"""Handler for ``pulse import-refinements <file>``."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from rich.console import Console

from pulse.runtime.refinement import write_refinement
from pulse.runtime.skill import discover_skills

console = Console()


def run_import_refinements(args: tuple[str, ...]) -> None:
    """Import refinement notes from a YAML file."""
    if not args:
        console.print("[yellow]Usage:[/yellow] pulse import-refinements <file.yaml> [--dry-run]")
        sys.exit(1)

    file_path = Path(args[0])
    dry_run = "--dry-run" in args

    if not file_path.exists():
        console.print(f"[red]File not found:[/red] {file_path}")
        sys.exit(1)

    with open(file_path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "refinements" not in data:
        console.print("[red]Invalid format.[/red] Expected YAML with a 'refinements' list.")
        sys.exit(1)

    entries: list[dict] = data["refinements"]
    if not entries:
        console.print("[yellow]No refinements found in file.[/yellow]")
        return

    skills = discover_skills()
    if not skills:
        console.print("[red]No skills discovered.[/red] Run `pulse init` first.")
        sys.exit(1)

    imported = 0
    skipped = 0
    skill_names: set[str] = set()

    for entry in entries:
        verb = entry.get("skill", "")
        note = entry.get("note", "")

        if not verb or not note:
            console.print(f"  [yellow]Skipping entry with missing skill or note:[/yellow] {entry}")
            skipped += 1
            continue

        skill = skills.get(verb)
        if skill is None:
            console.print(f"  [yellow]Unknown skill '{verb}' — skipped.[/yellow]")
            skipped += 1
            continue

        if dry_run:
            console.print(f"  [dim]Would add to {verb}:[/dim] {note}")
        else:
            write_refinement(skill.path, note)
            console.print(f"  [green]Added to {verb}:[/green] {note}")

        imported += 1
        skill_names.add(verb)

    action = "Would import" if dry_run else "Imported"
    console.print(
        f"\n[bold]{action} {imported} refinement(s) across {len(skill_names)} skill(s).[/bold]"
    )
    if skipped:
        console.print(f"[yellow]Skipped {skipped} entry(ies).[/yellow]")
