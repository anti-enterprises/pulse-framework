"""Tests for the playbook runner."""

from __future__ import annotations

from pathlib import Path

import yaml

from pulse.runtime.playbook import PlaybookRunner, discover_playbooks
from pulse.runtime.schemas import PlaybookMeta


def _minimal_playbook_data() -> dict:
    return {
        "name": "pulse test-playbook",
        "version": "1.0.0",
        "description": "Test playbook",
        "cadence": "ad_hoc",
        "requires": {"workspace_exists": True},
        "steps": [
            {
                "id": "step1",
                "skill": "pulse workspace-status",
                "on_failure": "log_and_continue",
            },
        ],
    }


def test_load_playbook_from_data() -> None:
    data = _minimal_playbook_data()
    pb = PlaybookMeta.model_validate(data)
    assert pb.name == "pulse test-playbook"
    assert len(pb.steps) == 1
    assert pb.steps[0].skill == "pulse workspace-status"


def test_load_playbook_from_file(pulse_home: Path) -> None:
    pdir = pulse_home / "playbooks"
    pdir.mkdir(parents=True, exist_ok=True)

    data = _minimal_playbook_data()
    (pdir / "test-playbook.yaml").write_text(yaml.dump(data))

    runner = PlaybookRunner()
    pb = runner.load_playbook("test-playbook")
    assert pb.name == "pulse test-playbook"


def test_playbook_conditional_step() -> None:
    data = {
        "name": "pulse cond-test",
        "version": "1.0.0",
        "description": "Conditional test",
        "cadence": "ad_hoc",
        "steps": [
            {
                "id": "always",
                "skill": "pulse workspace-status",
                "on_failure": "log_and_continue",
            },
            {
                "id": "conditional",
                "skill": "pulse extract",
                "when": "false",
                "on_failure": "log_and_continue",
            },
        ],
    }
    pb = PlaybookMeta.model_validate(data)
    assert len(pb.steps) == 2
    assert pb.steps[1].when == "false"


def test_playbook_with_include() -> None:
    data = {
        "name": "pulse inc-test",
        "version": "1.0.0",
        "description": "Include test",
        "cadence": "ad_hoc",
        "steps": [
            {"include": "weekly"},
            {"id": "extra", "skill": "pulse extract", "on_failure": "log_and_continue"},
        ],
    }
    pb = PlaybookMeta.model_validate(data)
    assert pb.steps[0].include == "weekly"


def test_discover_playbooks(pulse_home: Path) -> None:
    pdir = pulse_home / "playbooks"
    pdir.mkdir(parents=True, exist_ok=True)

    (pdir / "alpha.yaml").write_text(yaml.dump({
        "name": "pulse alpha",
        "version": "1.0.0",
        "description": "Alpha playbook",
        "cadence": "weekly",
        "steps": [{"id": "s1", "skill": "pulse extract", "on_failure": "log_and_continue"}],
    }))

    playbooks = discover_playbooks()
    assert "alpha" in playbooks


def test_default_playbooks_valid() -> None:
    """All shipped playbook YAMLs should parse correctly."""
    pkg_root = Path(__file__).parent.parent.parent
    pb_dir = pkg_root / "default_assets" / "playbooks"
    if not pb_dir.exists():
        return

    for yaml_file in pb_dir.glob("*.yaml"):
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        pb = PlaybookMeta.model_validate(data)
        assert pb.name.startswith("pulse ")
        assert len(pb.steps) > 0
