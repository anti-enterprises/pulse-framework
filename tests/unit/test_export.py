"""Tests for the `pulse export` command."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml

from pulse.commands.export import _iso, build_export, run_export
from pulse.runtime.workspace import create_workspace


def _seed(pulse_home: Path) -> Path:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    ws = pulse_home / "workspaces" / "test-ws"
    (ws / "directions").mkdir(parents=True, exist_ok=True)
    (ws / "hypotheses").mkdir(parents=True, exist_ok=True)
    (ws / "briefs").mkdir(parents=True, exist_ok=True)

    (ws / "directions" / "D-001.yaml").write_text(yaml.safe_dump({
        "id": "dir-1", "code": "D-001", "title": "AI eats tooling",
        "state": "peaking", "momentum": 0.8, "confidence": 0.7,
        "atom_count": 5, "last_updated": "2026-06-15T00:00:00+00:00",
    }))
    (ws / "hypotheses" / "H-001.yaml").write_text(yaml.safe_dump({
        "id": "hyp-1", "code": "H-001", "title": "Devs want agentic CLIs",
        "statement": "Agentic CLIs will dominate developer tooling.",
        "state": "active", "confidence": 0.6, "direction_ids": ["dir-1"],
    }))
    (ws / "briefs" / "2026-06-15-weekly-digest.md").write_text("# Weekly digest\n")
    return ws


def test_export_maps_directions(pulse_home: Path) -> None:
    _seed(pulse_home)
    out = build_export("test-ws")
    assert len(out["directions"]) == 1
    d = out["directions"][0]
    assert d["code"] == "D-001"
    assert d["state"] == "peaking"
    assert d["momentum"] == 0.8
    assert d["confidence"] == 0.7
    assert d["atom_count"] == 5
    assert d["last_updated"] == "2026-06-15T00:00:00+00:00"
    assert d["topic_ids"] == []  # Pulse directions carry no topics


def test_export_maps_hypotheses(pulse_home: Path) -> None:
    _seed(pulse_home)
    h = build_export("test-ws")["hypotheses"][0]
    assert h["code"] == "H-001"
    assert h["detail"] == "Agentic CLIs will dominate developer tooling."  # statement -> detail
    assert h["confidence"] == 0.6
    assert h["direction_codes"] == ["D-001"]  # direction_ids resolved to codes


def test_export_lists_briefs(pulse_home: Path) -> None:
    _seed(pulse_home)
    briefs = build_export("test-ws")["briefs"]
    assert briefs == [{"kind": "weekly_digest", "key_findings": []}]


def test_export_empty_workspace(pulse_home: Path) -> None:
    create_workspace("empty-ws", "Empty", "SaaS", "tester")
    assert build_export("empty-ws") == {"directions": [], "hypotheses": [], "briefs": []}


def test_export_skips_malformed_and_untitled(pulse_home: Path) -> None:
    ws = _seed(pulse_home)
    (ws / "directions" / "broken.yaml").write_text(": not valid yaml :\n  - [")
    (ws / "directions" / "no-title.yaml").write_text(yaml.safe_dump({"id": "x", "code": "D-9"}))
    out = build_export("test-ws")
    assert len(out["directions"]) == 1  # only the well-formed, titled one


def test_run_export_prints_parseable_json(pulse_home: Path, capsys) -> None:
    _seed(pulse_home)
    run_export(("test-ws", "--json"))
    payload = json.loads(capsys.readouterr().out)  # must be the ONLY thing on stdout
    assert payload["directions"][0]["code"] == "D-001"
    assert payload["hypotheses"][0]["code"] == "H-001"


def test_iso_normalizes_datetime() -> None:
    assert _iso(dt.datetime(2026, 6, 15, tzinfo=dt.UTC)) == "2026-06-15T00:00:00+00:00"
    assert _iso("already-a-string") == "already-a-string"
    assert _iso(0.8) == 0.8
