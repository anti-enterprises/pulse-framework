"""Tests for the pulse refine CLI command."""

from __future__ import annotations

from pathlib import Path

import frontmatter

from pulse.commands.refine import run_refine


def _create_skill_dir(base: Path, layer: str, name: str) -> Path:
    """Create a minimal skill directory."""
    skill_dir = base / "skills" / layer / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"""\
---
name: pulse {name}
version: 1.0.0
description: Test skill.
layer: {layer}
cadence: ad_hoc
refinements: []
---

# Procedure

Step 1.
"""
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


class TestRunRefine:
    def test_writes_note_from_args(self, pulse_home: Path) -> None:
        _create_skill_dir(pulse_home, "meta", "test-refine")

        run_refine(("test-refine", "This step needs clarification."))

        post = frontmatter.load(str(pulse_home / "skills" / "meta" / "test-refine" / "SKILL.md"))
        refinements = post.metadata.get("refinements", [])
        assert len(refinements) == 1
        assert refinements[0]["note"] == "This step needs clarification."

    def test_joins_multiple_args_as_note(self, pulse_home: Path) -> None:
        _create_skill_dir(pulse_home, "meta", "multi-arg")

        run_refine(("multi-arg", "word1", "word2", "word3"))

        post = frontmatter.load(str(pulse_home / "skills" / "meta" / "multi-arg" / "SKILL.md"))
        refinements = post.metadata.get("refinements", [])
        assert refinements[0]["note"] == "word1 word2 word3"

    def test_unknown_skill_exits(self, pulse_home: Path) -> None:
        _create_skill_dir(pulse_home, "meta", "exists")

        import pytest

        with pytest.raises(SystemExit):
            run_refine(("nonexistent-skill", "some note"))

    def test_no_args_exits(self, pulse_home: Path) -> None:
        import pytest

        with pytest.raises(SystemExit):
            run_refine(())
