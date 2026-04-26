"""Tests for workspace management."""

from __future__ import annotations

from pathlib import Path

import pytest

from pulse.runtime.workspace import (
    WorkspaceError,
    create_workspace,
    list_workspaces,
    load_workspace,
    save_workspace,
    validate_workspace_id,
)


def test_validate_workspace_id_valid() -> None:
    assert validate_workspace_id("my-client") is None
    assert validate_workspace_id("abc") is None
    assert validate_workspace_id("test-workspace-123") is None


def test_validate_workspace_id_invalid() -> None:
    assert validate_workspace_id("AB") is not None  # too short + uppercase
    assert validate_workspace_id("a") is not None  # too short
    assert validate_workspace_id("ab") is not None  # too short
    assert validate_workspace_id("1bad") is not None  # starts with number
    assert validate_workspace_id("has spaces") is not None


def test_validate_workspace_id_reserved() -> None:
    assert validate_workspace_id("default") is not None
    assert validate_workspace_id("template") is not None
    assert validate_workspace_id("archive") is not None


def test_create_workspace(pulse_home: Path) -> None:
    ws = create_workspace("test-client", "Test Client", "SaaS", "tester")
    assert ws.id == "test-client"
    assert ws.name == "Test Client"
    assert ws.industry == "SaaS"

    # Directory structure created
    ws_path = pulse_home / "workspaces" / "test-client"
    assert ws_path.exists()
    assert (ws_path / "workspace.yaml").exists()
    assert (ws_path / "atoms").exists()
    assert (ws_path / "runs").exists()
    assert (ws_path / ".gitignore").exists()


def test_create_workspace_duplicate(pulse_home: Path) -> None:
    create_workspace("test-client", "Test", "SaaS", "tester")
    with pytest.raises(WorkspaceError):
        create_workspace("test-client", "Test", "SaaS", "tester")


def test_load_workspace(pulse_home: Path) -> None:
    create_workspace("test-client", "Test Client", "SaaS", "tester")
    ws = load_workspace("test-client")
    assert ws.id == "test-client"
    assert ws.name == "Test Client"
    assert ws.schema_version == 1


def test_load_workspace_nonexistent(pulse_home: Path) -> None:
    with pytest.raises(WorkspaceError):
        load_workspace("nonexistent")


def test_save_and_reload(pulse_home: Path) -> None:
    ws = create_workspace("test-client", "Test", "SaaS", "tester")
    ws.scope_statement = "Testing scope"
    save_workspace(ws)

    ws2 = load_workspace("test-client")
    assert ws2.scope_statement == "Testing scope"


def test_list_workspaces(pulse_home: Path) -> None:
    create_workspace("alpha", "Alpha", "Tech", "tester")
    create_workspace("beta", "Beta", "Finance", "tester")
    workspaces = list_workspaces()
    assert len(workspaces) == 2
    ids = [w["id"] for w in workspaces]
    assert "alpha" in ids
    assert "beta" in ids
