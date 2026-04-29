"""Tests for auto-refinement heuristics."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from pulse.runtime.heuristics import (
    check_failure_heuristics,
    check_post_run_heuristics,
)


def _create_skill(base: Path, name: str, **extra_meta: object) -> MagicMock:
    """Create a mock Skill with a real SKILL.md on disk."""
    skill_dir = base / "skills" / "meta" / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    fm_data = {
        "name": f"pulse {name}",
        "version": "1.0.0",
        "description": f"Test skill {name}.",
        "layer": "meta",
        "cadence": "ad_hoc",
    }
    fm_data.update(extra_meta)
    content = "---\n"
    for k, v in fm_data.items():
        if isinstance(v, list):
            content += f"{k}:\n"
            for item in v:
                content += f"  - {item}\n"
        elif isinstance(v, dict):
            content += f"{k}:\n"
            for dk, dv in v.items():
                content += f"  {dk}: {dv}\n"
        else:
            content += f"{k}: {v}\n"
    content += "refinements: []\n"
    content += "---\n\n# Procedure\n\nStep 1."
    (skill_dir / "SKILL.md").write_text(content)

    skill = MagicMock()
    skill.path = skill_dir
    skill.meta.name = f"pulse {name}"
    skill.meta.writes = extra_meta.get("writes", [])
    skill.meta.outputs = extra_meta.get("outputs", {})
    skill.meta.runtime = extra_meta.get("runtime", {})
    skill.meta.refinements = []
    return skill


def _make_run_logger(atoms_produced: int = 0) -> MagicMock:
    """Create a mock RunLogger."""
    logger = MagicMock()
    logger.atoms_produced = atoms_produced
    logger.started_at = datetime.now(UTC) - timedelta(seconds=10)
    return logger


class TestZeroAtoms:
    def test_fires_when_atoms_expected_but_zero(self, pulse_home: Path) -> None:
        skill = _create_skill(pulse_home, "zero-atoms", writes=["atoms/2026-04/atoms.jsonl"])
        logger = _make_run_logger(atoms_produced=0)

        notes = check_post_run_heuristics(skill, logger, {}, "test-ws")
        assert any("zero atoms" in n.lower() for n in notes)

    def test_silent_when_atoms_produced(self, pulse_home: Path) -> None:
        skill = _create_skill(pulse_home, "has-atoms", writes=["atoms/2026-04/atoms.jsonl"])
        logger = _make_run_logger(atoms_produced=5)

        notes = check_post_run_heuristics(skill, logger, {}, "test-ws")
        assert not any("zero atoms" in n.lower() for n in notes)

    def test_silent_when_no_atom_writes(self, pulse_home: Path) -> None:
        skill = _create_skill(pulse_home, "no-atom-writes", writes=["workspace.yaml"])
        logger = _make_run_logger(atoms_produced=0)

        notes = check_post_run_heuristics(skill, logger, {}, "test-ws")
        assert not any("zero atoms" in n.lower() for n in notes)


class TestDurationExceeded:
    def test_fires_when_exceeded(self, pulse_home: Path) -> None:
        skill = _create_skill(pulse_home, "slow-skill", runtime={"max_duration_s": 5})
        logger = _make_run_logger()
        # Started 10s ago, max is 5s, threshold is 7.5s => should fire
        logger.started_at = datetime.now(UTC) - timedelta(seconds=10)

        notes = check_post_run_heuristics(skill, logger, {}, "test-ws")
        assert any("exceeding" in n.lower() for n in notes)

    def test_silent_when_within_threshold(self, pulse_home: Path) -> None:
        skill = _create_skill(pulse_home, "fast-skill", runtime={"max_duration_s": 60})
        logger = _make_run_logger()
        logger.started_at = datetime.now(UTC) - timedelta(seconds=10)

        notes = check_post_run_heuristics(skill, logger, {}, "test-ws")
        assert not any("exceeding" in n.lower() for n in notes)


class TestMissingOutputs:
    def test_fires_on_missing_field(self, pulse_home: Path) -> None:
        skill = _create_skill(
            pulse_home, "missing-out",
            outputs={"summary": {"type": "string"}, "count": {"type": "integer"}},
        )
        logger = _make_run_logger()
        result = {"summary": "done"}  # missing 'count'

        notes = check_post_run_heuristics(skill, logger, result, "test-ws")
        assert any("count" in n for n in notes)

    def test_silent_when_all_present(self, pulse_home: Path) -> None:
        skill = _create_skill(
            pulse_home, "all-out",
            outputs={"summary": {"type": "string"}},
        )
        logger = _make_run_logger()
        result = {"summary": "done"}

        notes = check_post_run_heuristics(skill, logger, result, "test-ws")
        assert not any("output field" in n.lower() for n in notes)


class TestConsecutiveFailures:
    def _setup_runs_db(self, pulse_home: Path, workspace_id: str, skill_name: str, statuses: list[str]) -> None:
        """Insert fake run rows into the workspace SQLite index."""
        ws_dir = pulse_home / "workspaces" / workspace_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        db_path = ws_dir / ".index.sqlite"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            skill_name TEXT,
            playbook_name TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            duration_ms INTEGER,
            error_message TEXT,
            knowledge_versions TEXT,
            atoms_produced INTEGER DEFAULT 0,
            output_files TEXT
        )""")
        base_time = datetime.now(UTC)
        for i, status in enumerate(statuses):
            ts = (base_time - timedelta(minutes=len(statuses) - i)).isoformat()
            conn.execute(
                "INSERT INTO runs (id, skill_name, started_at, status, workspace_id, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f"run-{i}", skill_name, ts, status, workspace_id, "test error" if status == "failed" else None),
            )
        conn.commit()
        conn.close()

    def test_fires_on_three_consecutive_failures(self, pulse_home: Path) -> None:
        workspace_id = "test-ws"
        skill_name = "pulse fail-skill"
        self._setup_runs_db(pulse_home, workspace_id, skill_name, ["failed", "failed", "failed"])

        skill = _create_skill(pulse_home, "fail-skill")
        notes = check_failure_heuristics(skill, workspace_id, "test error")
        assert any("3 consecutive" in n for n in notes)

    def test_silent_on_single_failure(self, pulse_home: Path) -> None:
        workspace_id = "test-ws2"
        skill_name = "pulse single-fail"
        self._setup_runs_db(pulse_home, workspace_id, skill_name, ["failed"])

        skill = _create_skill(pulse_home, "single-fail")
        notes = check_failure_heuristics(skill, workspace_id, "test error")
        assert not any("consecutive" in n for n in notes)

    def test_silent_when_success_breaks_streak(self, pulse_home: Path) -> None:
        workspace_id = "test-ws3"
        skill_name = "pulse mixed-fail"
        # Most recent first: fail, fail, success, fail => only 2 consecutive
        self._setup_runs_db(pulse_home, workspace_id, skill_name, ["failed", "succeeded", "failed", "failed"])

        skill = _create_skill(pulse_home, "mixed-fail")
        notes = check_failure_heuristics(skill, workspace_id, "test error")
        assert not any("consecutive" in n for n in notes)
