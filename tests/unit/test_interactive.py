"""Tests for non-interactive (headless) mode."""

from __future__ import annotations

import pytest

from pulse.runtime.interactive import is_non_interactive, set_non_interactive
from pulse.runtime.playbook import PlaybookRunner


@pytest.fixture(autouse=True)
def _reset_flag():
    set_non_interactive(False)
    yield
    set_non_interactive(False)


def test_default_is_interactive() -> None:
    assert is_non_interactive() is False


def test_flag_enables_non_interactive() -> None:
    set_non_interactive(True)
    assert is_non_interactive() is True


def test_env_var_enables_non_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PULSE_NON_INTERACTIVE", "1")
    assert is_non_interactive() is True
    monkeypatch.setenv("PULSE_NON_INTERACTIVE", "false")
    assert is_non_interactive() is False


def test_checkpoint_auto_proceeds_when_non_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    # input() must NEVER be called in non-interactive mode (it would block / EOFError headless).
    monkeypatch.setattr("builtins.input", lambda *a, **k: pytest.fail("input() called in non-interactive mode"))
    set_non_interactive(True)
    runner = PlaybookRunner()
    # a proceed/halt checkpoint — auto-proceed returns None (continues the playbook), no raise
    assert runner._handle_checkpoint({"prompt": "Continue?", "options": [
        {"label": "Continue", "action": "proceed"},
        {"label": "Halt", "action": "halt_gracefully"},
    ]}, {}) is None
