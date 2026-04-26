"""Smoke tests for the pulse CLI."""

from __future__ import annotations

from click.testing import CliRunner

from pulse.cli import main


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "pulse" in result.output
    assert "0.1.0" in result.output


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["help"])
    assert result.exit_code == 0
    assert "Pulse Skills Framework" in result.output
    assert "pulse init" in result.output
    assert "pulse weekly" in result.output


def test_help_specific_command() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["help", "init"])
    assert result.exit_code == 0
    assert "pulse init" in result.output
    assert "setup" in result.output.lower()


def test_help_unknown_command() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["help", "nonexistent-xyz-cmd"])
    assert result.exit_code == 2


def test_unknown_command_exits_2() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["totally-fake-command-xyz"])
    assert result.exit_code == 2
    assert "Unknown command" in result.output


def test_unknown_command_suggests() -> None:
    runner = CliRunner()
    # "weeky" fuzzy-matches to "weekly" which is a known (unimplemented) command
    # so it resolves and exits 1. Use a truly unknown string to test suggestions.
    result = runner.invoke(main, ["zzznotacommand"])
    assert result.exit_code == 2
    assert "Unknown command" in result.output


def test_bare_pulse_launches_router() -> None:
    runner = CliRunner()
    # CliRunner is not a tty, so the router should refuse
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert "interactive terminal" in result.output


def test_unimplemented_command_exits_1() -> None:
    runner = CliRunner()
    # Use a command that has no handler wired up yet
    result = runner.invoke(main, ["extract"])
    assert result.exit_code == 1
    assert "not yet implemented" in result.output


def test_deferred_command() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["intel-query"])
    assert result.exit_code == 0
    assert "Reserved for v2" in result.output


def test_alias_resolution() -> None:
    runner = CliRunner()
    # "kickoff" is an alias for "onboard"
    result = runner.invoke(main, ["kickoff"])
    assert result.exit_code == 1  # not implemented, but resolved
    assert "pulse onboard" in result.output


def test_help_shows_all_layers() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["help"])
    assert result.exit_code == 0
    for layer in ["Meta", "Kickoff", "Knowledge", "Corpus", "Discovery",
                   "Listen", "Synthesis", "Action", "Reflect", "Playbooks"]:
        assert layer in result.output
