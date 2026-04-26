"""Register Pulse skills with Claude Code and/or Codex.

Usage (after pip install):
    pulse-install-skills             # auto-detect hosts, create symlinks
    pulse-install-skills --uninstall # remove symlinks
    pulse-install-skills --host claude
    pulse-install-skills --host codex
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import click


def _source_skills_dir() -> Path:
    """Return the .claude/skills/ directory shipped with this package."""
    # Walk up from this file: pulse/install_skills.py -> pulse/ -> repo root
    repo_root = Path(__file__).resolve().parent.parent
    skills = repo_root / ".claude" / "skills"
    if not skills.is_dir():
        click.echo(f"Error: skills directory not found at {skills}", err=True)
        sys.exit(1)
    return skills


def _detect_hosts(host: str) -> dict[str, Path]:
    """Return {name: skills_dir} for each host to install into."""
    home = Path.home()
    targets: dict[str, Path] = {}

    if host == "auto":
        if shutil.which("claude"):
            targets["Claude Code"] = home / ".claude" / "skills"
        if shutil.which("codex"):
            targets["Codex"] = home / ".codex" / "skills"
        # Default to Claude Code if nothing detected
        if not targets:
            targets["Claude Code"] = home / ".claude" / "skills"
    elif host == "claude":
        targets["Claude Code"] = home / ".claude" / "skills"
    elif host == "codex":
        targets["Codex"] = home / ".codex" / "skills"

    return targets


def _link_skills(source: Path, target_dir: Path) -> int:
    """Create symlinks for all skills. Returns count of linked skills."""
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for skill_dir in sorted(source.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        link = target_dir / skill_dir.name
        # Remove existing symlink to allow update
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            # Don't overwrite real directories
            continue
        link.symlink_to(skill_dir)
        count += 1
    return count


def _unlink_skills(source: Path, target_dir: Path) -> int:
    """Remove symlinks that point into the source skills directory. Returns count."""
    count = 0
    for link in sorted(target_dir.glob("pulse*")):
        if not link.is_symlink():
            continue
        try:
            dest = link.resolve()
            if str(dest).startswith(str(source)):
                link.unlink()
                count += 1
        except (OSError, ValueError):
            continue
    return count


@click.command()
@click.option("--host", type=click.Choice(["auto", "claude", "codex"]), default="auto",
              help="Which host to install for (default: auto-detect).")
@click.option("--uninstall", is_flag=True, help="Remove skill symlinks.")
def main(host: str, uninstall: bool) -> None:
    """Register Pulse skills with Claude Code and/or Codex."""
    source = _source_skills_dir()
    targets = _detect_hosts(host)

    if uninstall:
        for name, target_dir in targets.items():
            if not target_dir.exists():
                continue
            count = _unlink_skills(source, target_dir)
            click.echo(f"  {name}: removed {count} symlinks from {target_dir}")
        click.echo("Pulse skills uninstalled.")
        return

    click.echo("Installing Pulse skills...")
    for name, target_dir in targets.items():
        count = _link_skills(source, target_dir)
        click.echo(f"  {name}: linked {count} skills to {target_dir}")
    click.echo("Done.")
