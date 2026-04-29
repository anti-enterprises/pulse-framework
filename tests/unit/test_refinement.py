"""Tests for refinement utilities (write, dedup, import)."""

from __future__ import annotations

from pathlib import Path

import frontmatter

from pulse.runtime.refinement import has_similar_refinement, write_refinement


def _create_skill_dir(base: Path, layer: str, name: str, frontmatter_str: str, procedure: str) -> Path:
    """Helper to create a minimal skill directory for testing."""
    skill_dir = base / "skills" / layer / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    content = f"---\n{frontmatter_str}\n---\n\n{procedure}"
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


class TestWriteRefinement:
    def test_appends_note(self, pulse_home: Path) -> None:
        fm = """\
name: pulse test-skill
version: 1.0.0
description: A test skill.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "test-skill", fm, "# Procedure\n\nDo the thing.")

        ref = write_refinement(skill_dir, "Step 2 is unclear when input is empty.")

        assert ref.note == "Step 2 is unclear when input is empty."
        assert ref.action == "none"

        # Reload and verify
        post = frontmatter.load(str(skill_dir / "SKILL.md"))
        refinements = post.metadata.get("refinements", [])
        assert len(refinements) == 1
        assert refinements[0]["note"] == "Step 2 is unclear when input is empty."
        assert refinements[0]["action"] == "none"

    def test_preserves_procedure(self, pulse_home: Path) -> None:
        procedure = """\
# Procedure

## 1. Complex step

```python
x = {"key": "value"}
print(x)
```

---

Some text after a horizontal rule.

## 2. Another step

- bullet one
- bullet two"""
        fm = """\
name: pulse preserve-test
version: 1.0.0
description: Test procedure preservation.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "preserve-test", fm, procedure)

        write_refinement(skill_dir, "Test note.")

        post = frontmatter.load(str(skill_dir / "SKILL.md"))
        # Procedure content should be preserved
        assert "```python" in post.content
        assert 'x = {"key": "value"}' in post.content
        assert "Some text after a horizontal rule." in post.content
        assert "- bullet one" in post.content

    def test_creates_refinements_list(self, pulse_home: Path) -> None:
        """SKILL.md with no refinements key should get one created."""
        fm = """\
name: pulse no-refinements
version: 1.0.0
description: No refinements yet.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "no-ref", fm, "# Procedure\n\nStep 1.")

        write_refinement(skill_dir, "First refinement.")

        post = frontmatter.load(str(skill_dir / "SKILL.md"))
        assert len(post.metadata["refinements"]) == 1

    def test_multiple_refinements_append(self, pulse_home: Path) -> None:
        fm = """\
name: pulse multi-ref
version: 1.0.0
description: Multiple refinements.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "multi-ref", fm, "# Procedure\n\nStep 1.")

        write_refinement(skill_dir, "First note.")
        write_refinement(skill_dir, "Second note.")
        write_refinement(skill_dir, "Third note.")

        post = frontmatter.load(str(skill_dir / "SKILL.md"))
        refinements = post.metadata["refinements"]
        assert len(refinements) == 3
        assert refinements[0]["note"] == "First note."
        assert refinements[2]["note"] == "Third note."


class TestHasSimilarRefinement:
    def test_detects_exact_duplicate(self, pulse_home: Path) -> None:
        fm = """\
name: pulse dedup-test
version: 1.0.0
description: Dedup test.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "dedup", fm, "# Procedure\n\nStep 1.")

        write_refinement(skill_dir, "This is a test note.")
        assert has_similar_refinement(skill_dir, "This is a test note.") is True

    def test_detects_substring_match(self, pulse_home: Path) -> None:
        fm = """\
name: pulse substr-test
version: 1.0.0
description: Substring test.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "substr", fm, "# Procedure\n\nStep 1.")

        write_refinement(skill_dir, "Auto: pulse extract produced zero atoms.")
        assert has_similar_refinement(skill_dir, "zero atoms") is True

    def test_allows_different_note(self, pulse_home: Path) -> None:
        fm = """\
name: pulse diff-test
version: 1.0.0
description: Different note test.
layer: meta
cadence: ad_hoc"""
        skill_dir = _create_skill_dir(pulse_home, "meta", "diff", fm, "# Procedure\n\nStep 1.")

        write_refinement(skill_dir, "Duration exceeded by 200%.")
        assert has_similar_refinement(skill_dir, "Zero atoms produced.") is False

    def test_nonexistent_skill_returns_false(self, pulse_home: Path) -> None:
        fake_dir = pulse_home / "skills" / "meta" / "nonexistent"
        assert has_similar_refinement(fake_dir, "anything") is False
