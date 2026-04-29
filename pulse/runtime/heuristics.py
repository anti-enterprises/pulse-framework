"""Post-run heuristics that auto-generate refinement notes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pulse.runtime.refinement import has_similar_refinement

if TYPE_CHECKING:
    from pulse.runtime.runs import RunLogger
    from pulse.runtime.skill import Skill


def check_post_run_heuristics(
    skill: Skill,
    run_logger: RunLogger,
    result: dict[str, Any],
    workspace_id: str,
) -> list[str]:
    """Return refinement notes triggered by a successful run outcome.

    Called after skill execution completes successfully but before
    the run is marked complete. Returns an empty list if no issues found.
    """
    notes: list[str] = []

    notes.extend(_check_zero_atoms(skill, run_logger))
    notes.extend(_check_duration_exceeded(skill, run_logger))
    notes.extend(_check_missing_outputs(skill, result))

    # Deduplicate against existing refinements
    return [n for n in notes if not has_similar_refinement(skill.path, n)]


def check_failure_heuristics(
    skill: Skill,
    workspace_id: str,
    error_message: str,
) -> list[str]:
    """Return refinement notes triggered by failure patterns.

    Called after a skill execution fails. Only checks patterns that
    require failure context (e.g. consecutive failures).
    """
    notes: list[str] = []
    notes.extend(_check_consecutive_failures(skill, workspace_id, error_message))
    return [n for n in notes if not has_similar_refinement(skill.path, n)]


# ── Individual heuristics ──────────────────────────────────────


def _check_zero_atoms(skill: Skill, run_logger: RunLogger) -> list[str]:
    """Flag when a skill produces zero atoms but is expected to produce some."""
    # Only relevant if skill declares atom-related writes
    writes = skill.meta.writes
    has_atom_output = any("atom" in w.lower() for w in writes)
    if not has_atom_output:
        return []

    if run_logger.atoms_produced == 0:
        return [
            f"Auto: {skill.meta.name} produced zero atoms. "
            "Expected atom output — investigate source availability or extraction logic."
        ]
    return []


def _check_duration_exceeded(skill: Skill, run_logger: RunLogger) -> list[str]:
    """Flag when a run significantly exceeds declared max_duration_s."""
    max_duration_s = skill.meta.runtime.get("max_duration_s")
    if max_duration_s is None:
        return []

    max_duration_s = int(max_duration_s)
    actual_s = (datetime.now(UTC) - run_logger.started_at).total_seconds()
    threshold = max_duration_s * 1.5

    if actual_s > threshold:
        return [
            f"Auto: {skill.meta.name} took {int(actual_s)}s, "
            f"exceeding declared max of {max_duration_s}s by "
            f"{int((actual_s / max_duration_s - 1) * 100)}%."
        ]
    return []


def _check_missing_outputs(skill: Skill, result: dict[str, Any]) -> list[str]:
    """Flag when declared output fields are missing from the result."""
    if not skill.meta.outputs:
        return []

    notes: list[str] = []
    for field in skill.meta.outputs:
        if field not in result:
            notes.append(
                f"Auto: {skill.meta.name} did not produce expected output field '{field}'."
            )
    return notes


def _check_consecutive_failures(
    skill: Skill,
    workspace_id: str,
    error_message: str,
) -> list[str]:
    """Flag when a skill has failed N+ times consecutively."""
    try:
        from pulse.runtime.index import get_connection

        conn = get_connection(workspace_id)
        rows = conn.execute(
            "SELECT status, error_message FROM runs "
            "WHERE skill_name = ? ORDER BY started_at DESC LIMIT 5",
            (skill.meta.name,),
        ).fetchall()
        conn.close()
    except Exception:
        return []

    # Count consecutive failures (most recent first)
    consecutive = 0
    for row in rows:
        if row[0] == "failed":
            consecutive += 1
        else:
            break

    if consecutive >= 3:
        last_error = error_message[:120] if error_message else "unknown"
        return [
            f"Auto: {skill.meta.name} failed {consecutive} consecutive times. "
            f"Last error: {last_error}"
        ]
    return []
