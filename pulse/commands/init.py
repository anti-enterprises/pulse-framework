"""The `pulse init` command — one-time framework setup."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console

from pulse.utils.atomic_write import atomic_write
from pulse.utils.paths import (
    config_path,
    corpus_dir,
    knowledge_dir,
    playbooks_dir,
    pulse_home,
    router_dir,
    runs_dir,
    skills_dir,
    workspaces_dir,
)


def run_init() -> None:
    """Execute the init command."""
    console = Console()
    home = pulse_home()

    if config_path().exists():
        console.print(f"\n[yellow]Pulse is already initialized at {home}[/yellow]")
        if not click.confirm("Reinitialize? This will overwrite config.yaml.", default=False):
            console.print("Aborted.")
            raise SystemExit(0)

    console.print(f"\n[bold]Initializing Pulse at {home}[/bold]\n")

    # Create directory structure
    dirs = [
        home,
        skills_dir(),
        playbooks_dir(),
        knowledge_dir(),
        corpus_dir(),
        router_dir(),
        runs_dir(),
        workspaces_dir(),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Create skill layer subdirs
    for layer in ["meta", "kickoff", "knowledge", "corpus", "discovery",
                  "listen", "synthesis", "action", "reflect"]:
        (skills_dir() / layer).mkdir(exist_ok=True)

    # Create knowledge subdirs
    for subdir in ["frameworks", "taxonomies", "questionnaires", "playbook-recipes",
                   "examples", "source-templates", "prompts"]:
        (knowledge_dir() / subdir).mkdir(exist_ok=True)

    # Create framework dirs
    for fw in ["hormozi", "abraham", "frasier", "demandcurve", "imperium", "robbins"]:
        (knowledge_dir() / "frameworks" / fw).mkdir(exist_ok=True)

    # Copy default_assets if available
    _copy_default_assets(home)

    # Collect config
    api_key_env = "ANTHROPIC_API_KEY"
    if os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[green]Found ANTHROPIC_API_KEY in environment.[/green]")
    else:
        console.print(
            "[dim]Set the ANTHROPIC_API_KEY environment variable for LLM features.[/dim]"
        )
        alt = click.prompt(
            "API key env var name (or press Enter for ANTHROPIC_API_KEY)",
            default="ANTHROPIC_API_KEY",
            show_default=False,
        )
        if alt:
            api_key_env = alt

    corpus_enabled = click.confirm("Enable corpus (local RAG)? Requires extra dependencies.", default=False)

    # Write config.yaml
    config: dict[str, object] = {
        "schema_version": 1,
        "llm": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key_env": api_key_env,
            "api_key": None,
        },
        "active_workspace": None,
        "corpus": {
            "enabled": corpus_enabled,
        },
        "defaults": {
            "workspace_directory": str(workspaces_dir()),
            "log_level": "info",
            "output_format": "text",
        },
        "telemetry": {"enabled": False},
        "permissions": {"emitters": {}},
    }

    content = yaml.dump(config, default_flow_style=False, sort_keys=False)
    atomic_write(config_path(), content)

    # Write .gitignore
    gitignore = _pulse_gitignore()
    (home / ".gitignore").write_text(gitignore)

    console.print(f"\n[green]Pulse initialized at {home}[/green]")
    console.print("Next: run `pulse workspace-new <id>` to create your first workspace.\n")


def _copy_default_assets(home: Path) -> None:
    """Copy default_assets into the Pulse home if they exist in the package."""
    # Look for default_assets relative to this file's package
    pkg_root = Path(__file__).parent.parent.parent
    assets_dir = pkg_root / "default_assets"

    if not assets_dir.exists():
        return

    # Copy non-destructively (don't overwrite existing files)
    for src in assets_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(assets_dir)
        dest = home / rel
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _pulse_gitignore() -> str:
    return """\
# Global credentials
config.yaml

# Corpus index (regenerable)
corpus/index/
corpus/index.bak/
corpus/ingestion-log.jsonl

# Global router log
runs/router.log.jsonl

# OS / editor noise
.DS_Store
*.swp
.vscode/
"""
