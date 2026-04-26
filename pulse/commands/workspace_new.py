"""The `pulse workspace-new` command."""

from __future__ import annotations

import getpass

from rich.console import Console

from pulse.runtime.index import create_index
from pulse.runtime.workspace import (
    create_workspace,
    set_active_workspace,
    validate_workspace_id,
)


def run_workspace_new(args: tuple[str, ...]) -> None:
    """Create a new workspace."""
    console = Console()

    if not args:
        console.print(
            "\n[red]Error:[/red] Missing workspace ID.\n"
            "Usage: pulse workspace-new <workspace-id> [--name NAME] [--industry INDUSTRY]\n"
        )
        raise SystemExit(2)

    workspace_id = args[0]

    # Parse optional flags from remaining args
    name = workspace_id
    industry = ""
    remaining = list(args[1:])
    while remaining:
        arg = remaining.pop(0)
        if arg == "--name" and remaining:
            name = remaining.pop(0)
        elif arg == "--industry" and remaining:
            industry = remaining.pop(0)
        else:
            console.print(f"[yellow]Ignoring unknown argument: {arg}[/yellow]")

    # Validate
    error = validate_workspace_id(workspace_id)
    if error:
        console.print(f"\n[red]Error:[/red] {error}\n")
        raise SystemExit(2)

    # Create
    try:
        workspace = create_workspace(
            workspace_id=workspace_id,
            name=name,
            industry=industry,
            created_by=getpass.getuser(),
        )
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}\n")
        raise SystemExit(1) from e

    # Create SQLite index
    create_index(workspace_id)

    # Set as active
    set_active_workspace(workspace_id)

    console.print(f"\n[green]Workspace '{workspace_id}' created and set as active.[/green]")
    console.print(f"  Path: {workspace.id}")
    console.print("  Next: run `pulse onboard` to start the kickoff process.\n")
