"""The `pulse workspace-switch` command."""

from __future__ import annotations

from rich.console import Console

from pulse.runtime.workspace import set_active_workspace, validate_workspace_id
from pulse.utils.paths import workspace_path


def run_workspace_switch(args: tuple[str, ...]) -> None:
    """Switch the active workspace."""
    console = Console()

    if not args:
        console.print(
            "\n[red]Error:[/red] Missing workspace ID.\n"
            "Usage: pulse workspace-switch <workspace-id>\n"
        )
        raise SystemExit(2)

    workspace_id = args[0]
    error = validate_workspace_id(workspace_id)
    if error:
        console.print(f"\n[red]Error:[/red] {error}\n")
        raise SystemExit(2)

    ws = workspace_path(workspace_id)
    if not ws.exists():
        console.print(
            f"\n[red]Error E001:[/red] Workspace '{workspace_id}' does not exist.\n"
            f"Run `pulse workspace-new {workspace_id}` to create it.\n"
        )
        raise SystemExit(1)

    set_active_workspace(workspace_id)
    console.print(f"\n[green]Active workspace set to '{workspace_id}'.[/green]\n")
