"""The `pulse reindex` command."""

from __future__ import annotations

from rich.console import Console

from pulse.runtime.index import rebuild_index
from pulse.runtime.workspace import get_active_workspace


def run_reindex(args: tuple[str, ...] = ()) -> None:
    """Rebuild the SQLite index from filesystem."""
    console = Console()

    workspace_id = args[0] if args else get_active_workspace()
    if not workspace_id:
        console.print(
            "\n[red]Error:[/red] No active workspace.\n"
            "Run `pulse workspace-switch <id>` or pass workspace ID as argument.\n"
        )
        raise SystemExit(1)

    console.print(f"\n[bold]Rebuilding index for '{workspace_id}'...[/bold]")

    try:
        atom_count = rebuild_index(workspace_id)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        raise SystemExit(1) from e

    console.print(f"[green]Index rebuilt. {atom_count} atoms indexed.[/green]\n")
