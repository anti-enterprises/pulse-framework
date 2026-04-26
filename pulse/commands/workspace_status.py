"""The `pulse workspace-status` command."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from pulse.runtime.index import query_counts
from pulse.runtime.workspace import get_active_workspace, load_workspace


def run_workspace_status(args: tuple[str, ...] = ()) -> None:
    """Show workspace status summary."""
    console = Console()

    workspace_id = args[0] if args else get_active_workspace()
    if not workspace_id:
        console.print(
            "\n[red]Error:[/red] No active workspace.\n"
            "Run `pulse workspace-switch <id>` or pass workspace ID as argument.\n"
        )
        raise SystemExit(1)

    try:
        ws = load_workspace(workspace_id)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        raise SystemExit(1) from e

    console.print(f"\n[bold]Workspace: {ws.name}[/bold] ({ws.id})")
    console.print(f"  Industry: {ws.industry or '(not set)'}")
    console.print(f"  Created: {ws.created.strftime('%Y-%m-%d')}")
    console.print(f"  Last touched: {ws.last_touched.strftime('%Y-%m-%d %H:%M')}")

    # Sections status
    sections = Table(title="Sections", show_header=False)
    sections.add_column("Section", style="cyan", width=20)
    sections.add_column("Status")

    sections.add_row("Identity", "[green]set[/green]" if ws.identity else "[dim]not set[/dim]")
    sections.add_row("Customer", "[green]set[/green]" if ws.customer else "[dim]not set[/dim]")
    sections.add_row("Offer", "[green]set[/green]" if ws.offer else "[dim]not set[/dim]")
    sections.add_row("Goals", "[green]set[/green]" if ws.goals else "[dim]not set[/dim]")
    sections.add_row("Position", "[green]set[/green]" if ws.position else "[dim]not set[/dim]")

    console.print()
    console.print(sections)

    # Index counts
    counts = query_counts(workspace_id)
    if counts:
        idx = Table(title="Index", show_header=False)
        idx.add_column("Entity", style="cyan", width=20)
        idx.add_column("Count", justify="right")

        for entity in ["atoms", "directions", "hypotheses", "factors", "sources", "runs"]:
            idx.add_row(entity.title(), str(counts.get(entity, 0)))

        console.print()
        console.print(idx)

    # Position summary
    if ws.position:
        console.print(f"\n  Intention: {ws.position.intention.value}")

    console.print()
