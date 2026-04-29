"""Refinement utilities for appending and querying skill refinement notes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import frontmatter

from pulse.runtime.schemas import SkillRefinement
from pulse.utils.atomic_write import atomic_write


def write_refinement(
    skill_path: Path,
    note: str,
    action: str = "none",
    version_bumped: str | None = None,
) -> SkillRefinement:
    """Append a refinement entry to a skill's SKILL.md frontmatter.

    Args:
        skill_path: Directory containing SKILL.md.
        note: The refinement observation text.
        action: Status of the refinement (default "none" = pending).
        version_bumped: Optional version bump string (e.g. "1.0.0 → 1.0.1").

    Returns:
        The constructed SkillRefinement.
    """
    skill_md = skill_path / "SKILL.md"
    post = frontmatter.load(str(skill_md))

    refinements: list[dict] = post.metadata.get("refinements", [])
    if refinements is None:
        refinements = []

    entry: dict[str, object] = {
        "date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "note": note,
        "action": action,
    }
    if version_bumped is not None:
        entry["version_bumped"] = version_bumped

    refinements.append(entry)
    post.metadata["refinements"] = refinements

    atomic_write(skill_md, frontmatter.dumps(post))

    return SkillRefinement(
        date=datetime.now(UTC),
        note=note,
        action=action,
        version_bumped=version_bumped,
    )


def has_similar_refinement(
    skill_path: Path,
    note: str,
    window_days: int = 7,
) -> bool:
    """Check if a similar refinement note already exists within the window.

    Uses substring matching on normalized text to detect duplicates.
    """
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False

    post = frontmatter.load(str(skill_md))
    refinements: list[dict] = post.metadata.get("refinements", []) or []

    cutoff = datetime.now(UTC) - timedelta(days=window_days)
    normalized_note = note.strip().lower()

    for ref in refinements:
        ref_date = ref.get("date")
        if ref_date is None:
            continue

        # Parse date — could be a date object or ISO string
        if isinstance(ref_date, str):
            try:
                parsed = datetime.fromisoformat(ref_date).replace(tzinfo=UTC)
            except ValueError:
                continue
        elif hasattr(ref_date, "year"):
            # datetime.date or datetime.datetime
            parsed = datetime(ref_date.year, ref_date.month, ref_date.day, tzinfo=UTC)
        else:
            continue

        if parsed < cutoff:
            continue

        existing = ref.get("note", "").strip().lower()
        # Substring match in either direction
        if normalized_note in existing or existing in normalized_note:
            return True

    return False
