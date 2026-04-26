"""The `pulse workspace-list` command."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from pulse.runtime.workspace import get_active_workspace, list_workspaces


def run_workspace_list(args: tuple[str, ...] = ()) -> None:
    """List all workspaces."""
    console = Console()
    workspaces = list_workspaces()

    if not workspaces:
        console.print(
            "\n[dim]No workspaces found.[/dim]\n"
            "Run `pulse workspace-new <id>` to create one.\n"
        )
        return

    active = get_active_workspace()

    table = Table(title="Workspaces")
    table.add_column("", style="green", width=2)
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Industry")
    table.add_column("Last Touched")

    for ws in workspaces:
        marker = "*" if ws["id"] == active else ""
        table.add_row(
            marker,
            ws["id"],
            ws.get("name", ""),
            ws.get("industry", ""),
            ws.get("last_touched", "")[:10],
        )

    console.print()
    console.print(table)
    console.print()
