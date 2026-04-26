"""Tests for the interactive router."""

from __future__ import annotations

from pathlib import Path

import yaml

from pulse.runtime.router import Router


def _minimal_tree() -> dict:
    """A minimal tree for testing."""
    return {
        "version": 1,
        "default_start": "start",
        "short_circuit": {
            "direct_command": True,
            "short_names": True,
            "global_escapes": {
                "0": "back",
                "q": "quit",
                "?": "help",
                "<": "start_over",
            },
        },
        "guards": [],
        "nodes": {
            "start": {
                "prompt": "What do you want?",
                "options": [
                    {"label": "Go to setup", "next": "setup"},
                    {"label": "Run weekly", "action": "run_command", "command": "pulse weekly"},
                    {"label": "Help", "action": "run_command", "command": "pulse help"},
                ],
            },
            "setup": {
                "prompt": "Setup options",
                "options": [
                    {"label": "Init", "action": "run_command", "command": "pulse init",
                     "confirm": "Run pulse init?"},
                    {"label": "Back", "action": "back"},
                ],
            },
        },
    }


def _write_tree(pulse_home: Path, tree: dict | None = None) -> Path:
    """Write a tree.yaml to the test pulse home."""
    tree = tree or _minimal_tree()
    router_dir = pulse_home / "router"
    router_dir.mkdir(parents=True, exist_ok=True)
    tree_path = router_dir / "tree.yaml"
    tree_path.write_text(yaml.dump(tree, default_flow_style=False))
    return tree_path


def test_load_tree(pulse_home: Path) -> None:
    tree_path = _write_tree(pulse_home)
    router = Router()
    router.load_tree(tree_path)
    assert router.tree["version"] == 1
    assert "start" in router.tree["nodes"]
    assert "setup" in router.tree["nodes"]


def test_parse_input_number() -> None:
    router = Router()
    router.tree = _minimal_tree()
    options = router.tree["nodes"]["start"]["options"]

    result = router._parse_input("1", options)
    assert result is not None
    assert result["type"] == "select_option"
    assert result["option"]["label"] == "Go to setup"


def test_parse_input_out_of_range() -> None:
    router = Router()
    router.tree = _minimal_tree()
    options = router.tree["nodes"]["start"]["options"]

    result = router._parse_input("99", options)
    assert result is None


def test_parse_input_back() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("0", [])
    assert result is not None
    assert result["type"] == "back"


def test_parse_input_quit() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("q", [])
    assert result is not None
    assert result["type"] == "quit"


def test_parse_input_help() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("?", [])
    assert result is not None
    assert result["type"] == "help"


def test_parse_input_start_over() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("<", [])
    assert result is not None
    assert result["type"] == "start_over"


def test_parse_input_direct_command() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("weekly", [])
    assert result is not None
    assert result["type"] == "direct_command"
    assert result["command"] == "pulse weekly"


def test_parse_input_with_pulse_prefix() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("pulse weekly", [])
    assert result is not None
    assert result["type"] == "direct_command"
    assert result["command"] == "pulse weekly"


def test_parse_input_empty() -> None:
    router = Router()
    router.tree = _minimal_tree()
    result = router._parse_input("", [])
    assert result is None


def test_load_context(pulse_home: Path) -> None:
    """Context loads without a workspace (first-run scenario)."""
    # Write a config.yaml
    config = {"schema_version": 1, "corpus": {"enabled": False}, "llm": {}}
    (pulse_home / "config.yaml").write_text(yaml.dump(config))

    router = Router()
    router.load_context()
    assert "workspace" in router.context
    assert "corpus" in router.context
    assert router.context["corpus"]["enabled"] is False


def test_first_run_detection(pulse_home: Path) -> None:
    """When no config exists, router shows first-run message."""
    # No config.yaml — first run
    _write_tree(pulse_home)
    Router()  # should not crash even without config

    # Verify first-run condition: no config.yaml
    from pulse.utils.paths import config_path
    assert not config_path().exists()


def test_traversal_logging(pulse_home: Path) -> None:
    """Traversal log writes to global router.log.jsonl."""
    import json

    _write_tree(pulse_home)
    router = Router()
    router.tree = _minimal_tree()
    router.context = {"workspace": {"id": "test"}}
    router.session_path = ["start", "setup"]
    router.dispatched_command = "pulse init"

    router._log_traversal()

    log_path = pulse_home / "runs" / "router.log.jsonl"
    assert log_path.exists()

    with open(log_path) as f:
        entry = json.loads(f.readline())

    assert entry["workspace"] == "test"
    assert entry["path"] == ["start", "setup"]
    assert entry["dispatched"] == "pulse init"
    assert entry["confirmed"] is True


def test_tree_yaml_valid(pulse_home: Path) -> None:
    """Validate the shipped default tree.yaml loads correctly."""
    pkg_root = Path(__file__).parent.parent.parent
    tree_path = pkg_root / "default_assets" / "router" / "tree.yaml"
    if not tree_path.exists():
        return

    router = Router()
    router.load_tree(tree_path)
    assert router.tree["version"] == 1
    assert "start" in router.tree["nodes"]

    # Verify all node references are valid
    nodes = router.tree["nodes"]
    for node_id, node in nodes.items():
        for opt in node.get("options", []):
            next_ref = opt.get("next")
            if next_ref:
                assert next_ref in nodes, f"Node '{node_id}' references unknown node '{next_ref}'"


def test_tree_yaml_all_commands_exist() -> None:
    """Every command in tree.yaml should exist in the manifest."""
    from pulse.manifest import MANIFEST

    pkg_root = Path(__file__).parent.parent.parent
    tree_path = pkg_root / "default_assets" / "router" / "tree.yaml"
    if not tree_path.exists():
        return

    with open(tree_path) as f:
        tree = yaml.safe_load(f)

    manifest_names = {f"pulse {c.name}" for c in MANIFEST}
    manifest_names.add("pulse help")  # special case

    for node_id, node in tree.get("nodes", {}).items():
        for opt in node.get("options", []):
            cmd = opt.get("command")
            if cmd:
                assert cmd in manifest_names, (
                    f"Router node '{node_id}' references unknown command '{cmd}'"
                )
