"""Run `pulse evolve` on every skill that has pending refinement notes."""

from __future__ import annotations

from rich.console import Console

from pulse.runtime.skill import discover_skills


def run_evolve_all(args: tuple[str, ...]) -> None:
    """Discover skills with unaddressed refinements and evolve each."""
    console = Console()

    skills = discover_skills()
    if not skills:
        console.print("\n[yellow]No skills discovered.[/yellow]\n")
        return

    # Find skills with at least one refinement where action == "none"
    pending: list[tuple[str, object]] = []
    for verb, skill in sorted(skills.items()):
        refinements = skill.meta.refinements
        unaddressed = [r for r in refinements if r.action == "none"]
        if unaddressed:
            pending.append((verb, skill))

    if not pending:
        console.print("\n[green]No skills have pending refinement notes.[/green]\n")
        return

    console.print(f"\n[bold]Found {len(pending)} skill(s) with pending refinements:[/bold]\n")
    for verb, skill in pending:
        unaddressed = [r for r in skill.meta.refinements if r.action == "none"]
        console.print(f"  - [cyan]pulse {verb}[/cyan] ({len(unaddressed)} note(s))")
    console.print()

    from pulse.runtime.workspace import get_active_workspace

    workspace_id = args[0] if args else (get_active_workspace() or "")
    if not workspace_id:
        console.print(
            "[red]Error:[/red] No active workspace. "
            "Run `pulse workspace-switch <id>` or pass the workspace ID positionally.\n"
        )
        raise SystemExit(2)

    evolved = 0
    for verb, skill in pending:
        console.rule(f"[bold]pulse evolve {verb}[/bold]")
        try:
            skill_to_evolve = skills.get("evolve")
            if skill_to_evolve is None:
                console.print("[red]Error:[/red] `pulse evolve` skill not found.\n")
                raise SystemExit(2)
            skill_to_evolve.execute(
                workspace_id=workspace_id,
                inputs={"workspace_id": workspace_id, "skill_name": verb},
            )
            evolved += 1
        except SystemExit:
            raise
        except Exception as exc:
            console.print(f"  [red]Error evolving {verb}:[/red] {exc}\n")

    console.print(f"\n[bold green]Done:[/bold green] evolved {evolved}/{len(pending)} skill(s).\n")
