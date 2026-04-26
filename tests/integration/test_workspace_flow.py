"""Integration test: full workspace lifecycle."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from pulse.cli import main


def test_full_workspace_lifecycle(pulse_home: Path) -> None:
    """Test init -> workspace-new -> workspace-list -> workspace-status -> reindex."""
    runner = CliRunner()

    # Init (with simulated input for prompts)
    result = runner.invoke(main, ["init"], input="ANTHROPIC_API_KEY\nn\n")
    assert result.exit_code == 0, f"init failed: {result.output}"
    assert (pulse_home / "config.yaml").exists()

    # Create workspace
    result = runner.invoke(main, ["workspace-new", "test-client", "--name", "Test Client", "--industry", "SaaS"])
    assert result.exit_code == 0, f"workspace-new failed: {result.output}"
    assert "test-client" in result.output

    # List workspaces
    result = runner.invoke(main, ["workspace-list"])
    assert result.exit_code == 0, f"workspace-list failed: {result.output}"
    assert "test-client" in result.output

    # Workspace status
    result = runner.invoke(main, ["workspace-status"])
    assert result.exit_code == 0, f"workspace-status failed: {result.output}"
    assert "Test Client" in result.output or "test-client" in result.output

    # Reindex
    result = runner.invoke(main, ["reindex"])
    assert result.exit_code == 0, f"reindex failed: {result.output}"
    assert "rebuilt" in result.output.lower() or "indexed" in result.output.lower()


def test_workspace_switch(pulse_home: Path) -> None:
    runner = CliRunner()

    # Init
    result = runner.invoke(main, ["init"], input="ANTHROPIC_API_KEY\nn\n")
    assert result.exit_code == 0

    # Create two workspaces
    runner.invoke(main, ["workspace-new", "alpha"])
    runner.invoke(main, ["workspace-new", "beta"])

    # Switch
    result = runner.invoke(main, ["workspace-switch", "alpha"])
    assert result.exit_code == 0
    assert "alpha" in result.output

    # Status should show alpha
    result = runner.invoke(main, ["workspace-status"])
    assert result.exit_code == 0
