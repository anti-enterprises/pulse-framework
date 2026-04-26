"""The `pulse help` and `pulse help <verb>` commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from pulse.dispatcher import CommandRegistry

# Layer display order and labels
LAYER_ORDER = [
    ("meta", "Meta"),
    ("kickoff", "Kickoff"),
    ("knowledge", "Knowledge"),
    ("corpus", "Corpus"),
    ("discovery", "Discovery"),
    ("listen", "Listen"),
    ("synthesis", "Synthesis"),
    ("action", "Action"),
    ("reflect", "Reflect"),
    ("playbook", "Playbooks"),
]


def show_help(registry: CommandRegistry, verb: str | None = None) -> None:
    """Display help for a specific command or all commands."""
    console = Console()

    if verb:
        _show_command_help(console, registry, verb)
    else:
        _show_all_help(console, registry)


def _show_command_help(
    console: Console, registry: CommandRegistry, verb: str
) -> None:
    """Show help for a specific command."""
    target = registry.resolve(verb)
    if target is None:
        suggestions = registry.suggest(verb)
        console.print(f"[red]Unknown command:[/red] pulse {verb}")
        if suggestions:
            console.print(f"\nDid you mean: {', '.join(f'pulse {s}' for s in suggestions)}")
        raise SystemExit(2)

    console.print(f"\n[bold]pulse {target.name}[/bold]")
    console.print(f"  {target.description}")
    if target.aliases:
        aliases = ", ".join(f"pulse {a.removeprefix('pulse ')}" for a in target.aliases)
        console.print(f"  Aliases: {aliases}")
    if target.layer:
        console.print(f"  Layer: {target.layer}")
    console.print()


def _show_all_help(console: Console, registry: CommandRegistry) -> None:
    """Show help for all commands."""
    from pulse import __version__

    console.print(f"\n[bold]Pulse Skills Framework[/bold] v{__version__}")
    console.print("Business intelligence, operationalized.\n")

    from pulse.dispatcher import TargetKind

    by_layer = registry.targets_by_layer()

    for layer_key, layer_label in LAYER_ORDER:
        targets = [
            t for t in by_layer.get(layer_key, [])
            if t.kind != TargetKind.DEFERRED
        ]
        if not targets:
            continue

        table = Table(title=layer_label, show_header=False, padding=(0, 2))
        table.add_column("Command", style="cyan", min_width=25)
        table.add_column("Description")

        for t in sorted(targets, key=lambda t: t.name):
            table.add_row(f"pulse {t.name}", t.description)

        console.print(table)
        console.print()

    console.print("[dim]Run `pulse help <command>` for details on a specific command.[/dim]")
    console.print("[dim]Run `pulse` with no arguments to launch the interactive router.[/dim]\n")


