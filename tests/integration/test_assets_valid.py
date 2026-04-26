"""Validate all shipped default assets parse correctly."""

from __future__ import annotations

from pathlib import Path

import yaml

from pulse.runtime.schemas import PlaybookMeta, SkillFrontmatter


def _assets_dir() -> Path:
    return Path(__file__).parent.parent.parent / "default_assets"


def test_all_skill_frontmatter_valid() -> None:
    """Every SKILL.md in default_assets should have valid frontmatter."""
    import frontmatter

    assets = _assets_dir()
    if not assets.exists():
        return

    skills_dir = assets / "skills"
    skill_files = list(skills_dir.rglob("SKILL.md"))
    assert len(skill_files) > 0, "No skills found in default_assets"

    errors: list[str] = []
    for skill_md in sorted(skill_files):
        try:
            post = frontmatter.load(str(skill_md))
            SkillFrontmatter.model_validate(post.metadata)
        except Exception as e:
            rel = skill_md.relative_to(assets)
            errors.append(f"{rel}: {e}")

    assert not errors, "Invalid skill frontmatter:\n" + "\n".join(errors)


def test_all_playbooks_valid() -> None:
    """Every playbook YAML in default_assets should parse correctly."""
    assets = _assets_dir()
    if not assets.exists():
        return

    pb_dir = assets / "playbooks"
    pb_files = list(pb_dir.glob("*.yaml"))
    assert len(pb_files) > 0, "No playbooks found"

    errors: list[str] = []
    for pb_file in sorted(pb_files):
        try:
            with open(pb_file) as f:
                data = yaml.safe_load(f)
            PlaybookMeta.model_validate(data)
        except Exception as e:
            errors.append(f"{pb_file.name}: {e}")

    assert not errors, "Invalid playbooks:\n" + "\n".join(errors)


def test_all_skill_schemas_valid_yaml() -> None:
    """Every schema.input.yaml and schema.output.yaml should be valid YAML."""
    assets = _assets_dir()
    if not assets.exists():
        return

    errors: list[str] = []
    for schema_file in sorted(assets.rglob("schema.*.yaml")):
        try:
            with open(schema_file) as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Schema is not a dict: {schema_file}"
        except Exception as e:
            rel = schema_file.relative_to(assets)
            errors.append(f"{rel}: {e}")

    assert not errors, "Invalid schemas:\n" + "\n".join(errors)


def test_router_tree_valid() -> None:
    """Router tree.yaml should parse and have valid node references."""
    assets = _assets_dir()
    tree_path = assets / "router" / "tree.yaml"
    if not tree_path.exists():
        return

    with open(tree_path) as f:
        tree = yaml.safe_load(f)

    assert tree["version"] == 1
    nodes = tree["nodes"]

    for node_id, node in nodes.items():
        for opt in node.get("options", []):
            next_ref = opt.get("next")
            if next_ref:
                assert next_ref in nodes, f"'{node_id}' references unknown node '{next_ref}'"


def test_questionnaire_valid() -> None:
    """Customer profile questionnaire should parse as valid YAML."""
    assets = _assets_dir()
    q_path = assets / "knowledge" / "questionnaires" / "customer-profile.yaml"
    if not q_path.exists():
        return

    with open(q_path) as f:
        data = yaml.safe_load(f)

    assert "tiers" in data or "name" in data
