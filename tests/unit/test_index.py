"""Tests for the SQLite index."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from pulse.runtime.index import create_index, get_connection, query_counts, rebuild_index
from pulse.runtime.workspace import create_workspace


def test_create_index(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    db_path = create_index("test-ws")
    assert db_path.exists()

    # Verify tables exist
    conn = get_connection("test-ws")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t["name"] for t in tables]
    assert "atoms" in table_names
    assert "directions" in table_names
    assert "hypotheses" in table_names
    assert "factors" in table_names
    assert "sources" in table_names
    assert "runs" in table_names
    assert "schema_meta" in table_names
    conn.close()


def test_query_counts_empty(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    create_index("test-ws")
    counts = query_counts("test-ws")
    assert counts["atoms"] == 0
    assert counts["runs"] == 0


def test_rebuild_index(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    create_index("test-ws")
    result = rebuild_index("test-ws")
    assert result.atom_count == 0  # empty workspace


def test_rebuild_index_normalizes_legacy_atoms_and_indexes_workspace_sources(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    ws = pulse_home / "workspaces" / "test-ws"

    atoms_file = ws / "atoms" / "2026-04" / "atoms.jsonl"
    atoms_file.parent.mkdir(parents=True, exist_ok=True)
    atoms = [
        {
            "id": "atom-rss-data",
            "workspace_id": "test-ws",
            "source_kind": "rss",
            "source_adapter": "aws_ml_blog",
            "source_ref": "src-rss-aws-ml-blog",
            "source_url": "https://example.com/rss-post",
            "source_label": "AWS ML Blog",
            "type": "data",
            "content": "A legacy RSS data atom should index as extraction/stat.",
            "extracted_at": "2026-04-30T00:00:00+00:00",
        },
        {
            "id": "atom-research-signal",
            "workspace_id": "test-ws",
            "source_kind": "research",
            "source_adapter": "strategic_analysis",
            "source_ref": "report",
            "source_url": None,
            "source_label": "Research",
            "type": "signal",
            "content": "A legacy research signal should index as authored/claim.",
            "extracted_at": "2026-04-30T00:00:00+00:00",
        },
    ]
    atoms_file.write_text("\n".join(json.dumps(atom) for atom in atoms) + "\n")

    sources_file = ws / "sources" / "sources.yaml"
    sources_file.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1",
                "sources": [
                    {
                        "id": "src-rss-openai-news",
                        "url": "https://openai.com/news/",
                        "label": "OpenAI News",
                        "kind": "rss",
                        "strategic_role": "industry_signal",
                        "health": "unknown",
                        "status": "active",
                    },
                    {
                        "id": "src-newsletter-example",
                        "url": "https://example.com/newsletter",
                        "label": "Newsletter Example",
                        "kind": "newsletter",
                        "strategic_role": "industry_signal",
                        "health": "unknown",
                        "status": "pending",
                    },
                    {
                        "id": "src-reddit-example",
                        "url": "https://reddit.com/r/example",
                        "label": "Reddit Example",
                        "kind": "reddit",
                        "strategic_role": "community_forum",
                        "health": "unknown",
                        "status": "active",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    result = rebuild_index("test-ws")

    assert result.atom_count == 2
    assert result.skipped == []

    counts = query_counts("test-ws")
    assert counts["atoms"] == 2
    assert counts["sources"] == 3

    conn = get_connection("test-ws")
    indexed_atoms = conn.execute(
        "SELECT id, source_kind, type FROM atoms ORDER BY id"
    ).fetchall()
    indexed_sources = conn.execute(
        "SELECT id, kind, strategic_role, health, status FROM sources ORDER BY id"
    ).fetchall()
    conn.close()

    assert [dict(row) for row in indexed_atoms] == [
        {"id": "atom-research-signal", "source_kind": "authored", "type": "claim"},
        {"id": "atom-rss-data", "source_kind": "extraction", "type": "stat"},
    ]
    assert [dict(row) for row in indexed_sources] == [
        {
            "id": "src-newsletter-example",
            "kind": "newsletter",
            "strategic_role": "industry_signal",
            "health": "unknown",
            "status": "pending",
        },
        {
            "id": "src-reddit-example",
            "kind": "reddit",
            "strategic_role": "community_forum",
            "health": "unknown",
            "status": "active",
        },
        {
            "id": "src-rss-openai-news",
            "kind": "rss",
            "strategic_role": "industry_signal",
            "health": "unknown",
            "status": "active",
        },
    ]


def test_rebuild_index_reports_skipped_rows_and_continues_sources(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    ws = pulse_home / "workspaces" / "test-ws"

    sources_file = ws / "sources" / "sources.yaml"
    sources_file.write_text(
        yaml.safe_dump(
            {
                "schema_version": "1",
                "sources": [
                    {
                        "id": "src-valid",
                        "url": "https://example.com/valid",
                        "label": "Valid",
                        "kind": "rss",
                        "strategic_role": "industry_signal",
                        "health": "unknown",
                        "status": "active",
                    },
                    {
                        "id": "src-invalid",
                        "url": "https://example.com/invalid",
                        "label": "Invalid",
                        "kind": "bad_kind",
                        "strategic_role": "industry_signal",
                        "health": "unknown",
                        "status": "active",
                    },
                    {
                        "id": "src-valid-after-invalid",
                        "url": "https://example.com/after",
                        "label": "Valid After Invalid",
                        "kind": "reddit",
                        "strategic_role": "community_forum",
                        "health": "unknown",
                        "status": "pending",
                    },
                ],
            },
            sort_keys=False,
        )
    )

    result = rebuild_index("test-ws")

    counts = query_counts("test-ws")
    assert counts["sources"] == 2
    assert len(result.skipped) == 1
    assert result.skipped[0].table == "sources"
    assert result.skipped[0].row_id == "src-invalid"
    assert "CHECK constraint failed" in result.skipped[0].reason


def test_rebuild_index_normalizes_legacy_run_logs(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    ws = pulse_home / "workspaces" / "test-ws"

    weekly_run = {
        "id": "run-2026-04-26-weekly",
        "workspace": "test-ws",
        "kind": "weekly",
        "started_at": "2026-04-26T15:00:00Z",
        "completed_at": "2026-04-26T15:30:00Z",
        "steps": [
            {
                "step": "write_digest",
                "status": "completed",
                "output": "briefs/weekly/2026-04-26-weekly-digest.md",
            }
        ],
        "new_atom_ids": ["atom-one", "atom-two"],
    }
    daily_run = {
        "id": "2026-04-30-daily",
        "workspace_id": "test-ws",
        "skill": "pulse:daily",
        "ran_at": "2026-04-30T00:00:00Z",
        "atoms_created": 7,
        "atoms": ["atom-a", "atom-b"],
    }

    (ws / "runs" / "2026-04-26-weekly.yaml").write_text(
        yaml.safe_dump(weekly_run, sort_keys=False)
    )
    (ws / "runs" / "2026-04-30-daily.yaml").write_text(
        yaml.safe_dump(daily_run, sort_keys=False)
    )

    result = rebuild_index("test-ws")

    assert result.skipped == []
    assert query_counts("test-ws")["runs"] == 2

    conn = get_connection("test-ws")
    indexed_runs = conn.execute(
        """SELECT id, skill_name, playbook_name, started_at, ended_at, status,
                  workspace_id, atoms_produced, output_files
           FROM runs
           ORDER BY id"""
    ).fetchall()
    conn.close()

    assert [dict(row) for row in indexed_runs] == [
        {
            "id": "2026-04-30-daily",
            "skill_name": None,
            "playbook_name": "pulse daily",
            "started_at": "2026-04-30T00:00:00Z",
            "ended_at": None,
            "status": "succeeded",
            "workspace_id": "test-ws",
            "atoms_produced": 7,
            "output_files": None,
        },
        {
            "id": "run-2026-04-26-weekly",
            "skill_name": None,
            "playbook_name": "pulse weekly",
            "started_at": "2026-04-26T15:00:00Z",
            "ended_at": "2026-04-26T15:30:00Z",
            "status": "succeeded",
            "workspace_id": "test-ws",
            "atoms_produced": 2,
            "output_files": json.dumps(["briefs/weekly/2026-04-26-weekly-digest.md"]),
        },
    ]


def test_rebuild_index_indexes_workspace_directions(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    ws = pulse_home / "workspaces" / "test-ws"

    direction = {
        "id": "D001",
        "code": "D001",
        "title": "UpWork-First Acquisition",
        "state": "active",
        "confidence": 0.9,
        "created_at": "2026-04-28T00:00:00Z",
        "last_updated": "2026-05-01T00:00:00Z",
        "supporting_atom_ids": ["atom-one", "atom-two"],
    }
    (ws / "directions" / "D001-upwork-first.yaml").write_text(
        yaml.safe_dump(direction, sort_keys=False)
    )

    result = rebuild_index("test-ws")

    assert result.skipped == []
    assert query_counts("test-ws")["directions"] == 1

    conn = get_connection("test-ws")
    indexed_directions = conn.execute(
        """SELECT id, code, title, state, momentum, confidence, atom_count,
                  age_days, origin_date, last_updated, source_file
           FROM directions"""
    ).fetchall()
    conn.close()

    assert [dict(row) for row in indexed_directions] == [
        {
            "id": "D001",
            "code": "D001",
            "title": "UpWork-First Acquisition",
            "state": "active",
            "momentum": 0.0,
            "confidence": 0.9,
            "atom_count": 2,
            "age_days": 0,
            "origin_date": "2026-04-28T00:00:00Z",
            "last_updated": "2026-05-01T00:00:00Z",
            "source_file": "directions/D001-upwork-first.yaml",
        }
    ]
