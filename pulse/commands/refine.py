"""Handler for ``pulse refine <skill> [note]``."""

from __future__ import annotations

import sys

from rich.console import Console

from pulse.runtime.refinement import write_refinement
from pulse.runtime.skill import discover_skills

console = Console()


def run_refine(args: tuple[str, ...]) -> None:
    """Append a refinement note to a skill's SKILL.md."""
    if not args:
        console.print("[yellow]Usage:[/yellow] pulse refine <skill> [note ...]")
        console.print("  If note is omitted, you will be prompted interactively.")
        sys.exit(1)

    skill_verb = args[0]
    note_parts = args[1:]

    skills = discover_skills()
    if not skills:
        console.print("[red]No skills discovered.[/red] Run `pulse init` first.")
        sys.exit(1)

    skill = skills.get(skill_verb)
    if skill is None:
        available = ", ".join(sorted(skills.keys()))
        console.print(f"[red]Unknown skill:[/red] {skill_verb}")
        console.print(f"  Available: {available}")
        sys.exit(1)

    # Build note from args or prompt interactively
    if note_parts:
        note = " ".join(note_parts)
    elif sys.stdin.isatty():
        console.print(f"[bold]Adding refinement to:[/bold] {skill.meta.name}")
        note = console.input("[dim]Note:[/dim] ").strip()
        if not note:
            console.print("[yellow]Empty note — skipped.[/yellow]")
            return
    else:
        console.print("[red]No note provided and stdin is not interactive.[/red]")
        sys.exit(1)

    refinement = write_refinement(skill.path, note)
    console.print(
        f"[green]Refinement added[/green] to {skill.meta.name} "
        f"(date={refinement.date:%Y-%m-%d}, action={refinement.action})"
    )
