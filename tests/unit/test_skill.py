"""Tests for skill discovery and loading."""

from __future__ import annotations

from pathlib import Path

from pulse.runtime.skill import discover_skills, load_skill


def _create_skill_dir(base: Path, layer: str, name: str, frontmatter: str, procedure: str) -> Path:
    """Helper to create a minimal skill directory for testing."""
    skill_dir = base / "skills" / layer / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    content = f"---\n{frontmatter}\n---\n\n{procedure}"
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def test_load_skill(pulse_home: Path) -> None:
    fm = """\
name: pulse test-skill
version: 1.0.0
description: A test skill.
layer: meta
cadence: ad_hoc"""
    procedure = "# Procedure\n\n## 1. Do something\n\nDo the thing."

    skill_dir = _create_skill_dir(pulse_home, "meta", "test-skill", fm, procedure)

    skill = load_skill(skill_dir)
    assert skill.meta.name == "pulse test-skill"
    assert skill.verb == "test-skill"
    assert skill.meta.version == "1.0.0"
    assert skill.meta.layer == "meta"
    assert "Do the thing" in skill.procedure


def test_load_skill_with_schemas(pulse_home: Path) -> None:
    fm = """\
name: pulse schema-test
version: 1.0.0
description: Skill with schemas.
layer: meta
cadence: ad_hoc
inputs:
  workspace_id:
    type: string
    required: true"""
    procedure = "# Procedure\n\n## 1. Test\n\nTest."

    skill_dir = _create_skill_dir(pulse_home, "meta", "schema-test", fm, procedure)

    # Add input schema
    (skill_dir / "schema.input.yaml").write_text(
        '$schema: "http://json-schema.org/draft-07/schema#"\n'
        "type: object\n"
        "required: [workspace_id]\n"
        "properties:\n"
        "  workspace_id:\n"
        '    type: string\n'
    )

    skill = load_skill(skill_dir)
    assert skill.input_schema is not None
    assert skill.input_schema["type"] == "object"


def test_discover_skills(pulse_home: Path) -> None:
    fm = """\
name: pulse discovered-one
version: 1.0.0
description: First discoverable skill.
layer: meta
cadence: ad_hoc"""
    _create_skill_dir(pulse_home, "meta", "discovered-one", fm, "# Procedure\n\n## 1. Go\n\nGo.")

    fm2 = """\
name: pulse discovered-two
version: 1.0.0
description: Second discoverable skill.
layer: listen
cadence: weekly"""
    _create_skill_dir(pulse_home, "listen", "discovered-two", fm2, "# Procedure\n\n## 1. Go\n\nGo.")

    skills = discover_skills()
    assert "discovered-one" in skills
    assert "discovered-two" in skills
    assert skills["discovered-one"].meta.layer == "meta"
    assert skills["discovered-two"].meta.layer == "listen"


def test_discover_skills_skips_malformed(pulse_home: Path) -> None:
    # Valid skill
    fm = """\
name: pulse good-skill
version: 1.0.0
description: Good skill.
layer: meta
cadence: ad_hoc"""
    _create_skill_dir(pulse_home, "meta", "good-skill", fm, "# Procedure\n\n## 1. Go\n\nGo.")

    # Malformed skill (missing required fields)
    bad_dir = pulse_home / "skills" / "meta" / "bad-skill"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / "SKILL.md").write_text("---\nname: bad\n---\n\nBroken.")

    skills = discover_skills()
    assert "good-skill" in skills
    assert "bad" not in skills  # Malformed, skipped


def test_load_default_asset_skill(tmp_path: Path) -> None:
    """Test loading the shipped workspace-status skill."""
    pkg_root = Path(__file__).parent.parent.parent
    ws_status = pkg_root / "default_assets" / "skills" / "meta" / "workspace-status"

    if not ws_status.exists():
        return  # Skip if default_assets not present

    skill = load_skill(ws_status)
    assert skill.meta.name == "pulse workspace-status"
    assert skill.meta.runtime.get("type") == "deterministic"


def test_load_default_asset_set_identity(tmp_path: Path) -> None:
    """Test loading the shipped set-identity skill."""
    pkg_root = Path(__file__).parent.parent.parent
    set_id = pkg_root / "default_assets" / "skills" / "kickoff" / "set-identity"

    if not set_id.exists():
        return

    skill = load_skill(set_id)
    assert skill.meta.name == "pulse set-identity"
    assert skill.meta.layer == "kickoff"
    assert "real business" in skill.procedure.lower()
