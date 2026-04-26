"""Run logging for skill and playbook invocations.

Each run produces:
1. A JSONL file at runs/<timestamp>.jsonl with event entries
2. A row in the SQLite index runs table
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from pulse.runtime.schemas import RunStatus
from pulse.utils.atomic_write import atomic_append
from pulse.utils.paths import workspace_path


class RunLogger:
    """Logger for a single skill/playbook invocation."""

    def __init__(
        self,
        workspace_id: str,
        skill_name: str | None = None,
        playbook_name: str | None = None,
    ) -> None:
        self.run_id = str(uuid.uuid4())
        self.workspace_id = workspace_id
        self.skill_name = skill_name
        self.playbook_name = playbook_name
        self.started_at = datetime.now(UTC)
        self.atoms_produced = 0
        self.output_files: list[str] = []

        # Create run log file (filesystem-safe timestamp)
        ts = self.started_at.strftime("%Y-%m-%dT%H-%M-%S")
        ws = workspace_path(workspace_id)
        self.log_path = ws / "runs" / f"{ts}.jsonl"

        # Write start event
        self.log_event({
            "event": "run_start",
            "run_id": self.run_id,
            "skill_name": self.skill_name,
            "playbook_name": self.playbook_name,
            "workspace_id": self.workspace_id,
            "started_at": self.started_at.isoformat(),
        })

    def log_event(self, event: dict[str, object]) -> None:
        """Append an event to the run log."""
        event["timestamp"] = datetime.now(UTC).isoformat()
        atomic_append(self.log_path, json.dumps(event, default=str))

    def complete(
        self,
        status: RunStatus = RunStatus.SUCCEEDED,
        error_message: str | None = None,
    ) -> None:
        """Close the run log and update the index."""
        ended_at = datetime.now(UTC)
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)

        self.log_event({
            "event": "run_end",
            "run_id": self.run_id,
            "status": status.value,
            "duration_ms": duration_ms,
            "atoms_produced": self.atoms_produced,
            "output_files": self.output_files,
            "error_message": error_message,
        })

        # Update SQLite index
        try:
            from pulse.runtime.index import get_connection
            conn = get_connection(self.workspace_id)
            conn.execute(
                """INSERT OR REPLACE INTO runs
                   (id, skill_name, playbook_name, started_at, ended_at,
                    status, workspace_id, duration_ms, error_message,
                    atoms_produced, output_files)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.run_id,
                    self.skill_name,
                    self.playbook_name,
                    self.started_at.isoformat(),
                    ended_at.isoformat(),
                    status.value,
                    self.workspace_id,
                    duration_ms,
                    error_message,
                    self.atoms_produced,
                    json.dumps(self.output_files),
                ),
            )
            conn.commit()
            conn.close()
        except Exception:
            # Index update failure is non-fatal
            pass
