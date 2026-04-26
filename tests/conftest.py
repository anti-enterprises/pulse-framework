"""Shared test fixtures for Pulse Skills Framework."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def pulse_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set PULSE_HOME to a temporary directory for test isolation."""
    home = tmp_path / ".pulse"
    home.mkdir()
    monkeypatch.setenv("PULSE_HOME", str(home))
    return home
