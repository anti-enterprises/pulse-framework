"""Tests for the command dispatcher."""

from __future__ import annotations

from pulse.dispatcher import CommandRegistry, DispatchTarget, TargetKind


def _make_registry() -> CommandRegistry:
    """Create a test registry with a few targets."""
    reg = CommandRegistry()
    reg.register(DispatchTarget("workspace-new", TargetKind.BUILTIN, "Create workspace.", "meta"))
    reg.register(DispatchTarget("workspace-list", TargetKind.BUILTIN, "List workspaces.", "meta"))
    reg.register(DispatchTarget("workspace-status", TargetKind.BUILTIN, "Workspace status.", "meta"))
    reg.register(DispatchTarget(
        "weekly", TargetKind.BUILTIN, "Weekly pass.", "playbook",
        aliases=["pulse intel", "pulse w"],
    ))
    reg.register(DispatchTarget("extract", TargetKind.BUILTIN, "Extract atoms.", "listen"))
    return reg


def test_exact_match() -> None:
    reg = _make_registry()
    target = reg.resolve("weekly")
    assert target is not None
    assert target.name == "weekly"


def test_alias_match() -> None:
    reg = _make_registry()
    target = reg.resolve("intel")
    assert target is not None
    assert target.name == "weekly"


def test_alias_match_single_char() -> None:
    reg = _make_registry()
    target = reg.resolve("w")
    assert target is not None
    assert target.name == "weekly"


def test_prefix_match_unique() -> None:
    reg = _make_registry()
    target = reg.resolve("extr")
    assert target is not None
    assert target.name == "extract"


def test_prefix_match_ambiguous_returns_none() -> None:
    reg = _make_registry()
    # "workspace-" matches multiple commands
    target = reg.resolve("workspace-")
    assert target is None


def test_no_match_returns_none() -> None:
    reg = _make_registry()
    target = reg.resolve("xyznonexistent")
    assert target is None


def test_suggest() -> None:
    reg = _make_registry()
    suggestions = reg.suggest("weeky")
    assert "weekly" in suggestions


def test_targets_by_layer() -> None:
    reg = _make_registry()
    by_layer = reg.targets_by_layer()
    assert "meta" in by_layer
    assert "playbook" in by_layer
    # 3 builtin meta targets + deferred commands (no layer) grouped as ""
    meta_builtins = [t for t in by_layer["meta"] if t.kind == TargetKind.BUILTIN]
    assert len(meta_builtins) == 3


def test_deferred_commands_registered() -> None:
    reg = CommandRegistry()  # fresh, has deferred commands
    target = reg.resolve("intel-query")
    assert target is not None
    assert target.kind == TargetKind.DEFERRED
