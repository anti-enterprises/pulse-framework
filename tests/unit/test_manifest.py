"""Tests for the command manifest -- contract tests per Codex architecture review."""

from __future__ import annotations

from pulse.manifest import MANIFEST, active_commands, implemented_commands


def test_manifest_no_duplicate_names() -> None:
    names = [c.name for c in MANIFEST]
    assert len(names) == len(set(names)), f"Duplicate names: {[n for n in names if names.count(n) > 1]}"


def test_manifest_no_duplicate_aliases() -> None:
    all_aliases: list[str] = []
    for c in MANIFEST:
        all_aliases.extend(c.aliases)
    assert len(all_aliases) == len(set(all_aliases)), "Duplicate aliases"


def test_manifest_active_excludes_deferred() -> None:
    active = active_commands()
    for c in active:
        assert c.status != "deferred"


def test_manifest_implemented_subset() -> None:
    impl = implemented_commands()
    assert len(impl) > 0
    for c in impl:
        assert c.status == "implemented"


def test_manifest_all_have_layer_or_deferred() -> None:
    for c in MANIFEST:
        if c.status != "deferred":
            assert c.layer, f"Command {c.name} has no layer"


def test_manifest_deferred_have_no_layer() -> None:
    for c in MANIFEST:
        if c.status == "deferred":
            assert c.layer == "", f"Deferred command {c.name} should have empty layer"


def test_manifest_corpus_toggles_canonical() -> None:
    """enable-corpus and disable-corpus are canonical; legacy aliases exist."""
    names = {c.name for c in MANIFEST}
    assert "enable-corpus" in names
    assert "disable-corpus" in names

    enable = next(c for c in MANIFEST if c.name == "enable-corpus")
    assert "pulse enable corpus" in enable.aliases

    disable = next(c for c in MANIFEST if c.name == "disable-corpus")
    assert "pulse disable corpus" in disable.aliases


def test_manifest_refine_router_in_v1() -> None:
    """refine-router is in v1 scope per architecture review."""
    names = {c.name for c in MANIFEST}
    assert "refine-router" in names


def test_manifest_help_present() -> None:
    """help is in the manifest even though it's dispatched specially."""
    names = {c.name for c in MANIFEST}
    assert "help" in names
