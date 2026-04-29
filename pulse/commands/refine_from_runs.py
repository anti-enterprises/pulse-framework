"""Handler for ``pulse refine-from-runs [--days N] [--skill VERB]``."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from pulse.runtime.refinement import write_refinement
from pulse.runtime.skill import discover_skills
from pulse.runtime.workspace import get_active_workspace

console = Console()


def _parse_args(args: tuple[str, ...]) -> dict[str, str]:
    """Parse --key value pairs from args tuple."""
    parsed: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            parsed[args[i][2:]] = args[i + 1]
            i += 2
        else:
            i += 1
    return parsed


def _load_run_events(log_path: Path) -> list[dict]:
    """Load events from a JSONL run log file."""
    events: list[dict] = []
    if not log_path.exists():
        return events
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def run_refine_from_runs(args: tuple[str, ...]) -> None:
    """LLM-scan recent runs and propose refinement notes."""
    parsed = _parse_args(args)
    days = int(parsed.get("days", "7"))
    skill_filter = parsed.get("skill")

    workspace_id = get_active_workspace()
    if not workspace_id:
        console.print("[red]No active workspace.[/red] Run `pulse workspace-switch <id>` first.")
        sys.exit(1)

    # Import here to avoid circular imports and allow graceful failure
    from pulse.runtime.index import get_connection
    from pulse.runtime.llm import LLMClient

    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()

    # Query runs from SQLite
    try:
        conn = get_connection(workspace_id)
        query = "SELECT * FROM runs WHERE started_at >= ? ORDER BY started_at DESC"
        params: list[str] = [cutoff]
        if skill_filter:
            query = "SELECT * FROM runs WHERE started_at >= ? AND skill_name = ? ORDER BY started_at DESC"
            params.append(skill_filter)
        rows = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.execute(query, params).description] if rows else []
        conn.close()
    except Exception as exc:
        console.print(f"[red]Could not query runs:[/red] {exc}")
        sys.exit(1)

    if not rows:
        console.print(f"[yellow]No runs found in the last {days} day(s).[/yellow]")
        return

    # Group runs by skill
    runs_by_skill: dict[str, list[dict]] = {}
    for row in rows:
        run = dict(zip(columns, row, strict=False))
        skill_name = run.get("skill_name")
        if not skill_name:
            continue
        runs_by_skill.setdefault(skill_name, []).append(run)

    # Build per-skill summaries
    skills = discover_skills()
    summaries: list[dict] = []

    for skill_name, runs in sorted(runs_by_skill.items()):
        total = len(runs)
        succeeded = sum(1 for r in runs if r.get("status") == "succeeded")
        failed = sum(1 for r in runs if r.get("status") == "failed")
        durations = [r["duration_ms"] for r in runs if r.get("duration_ms")]
        avg_duration = sum(durations) / len(durations) if durations else 0
        atoms = sum(r.get("atoms_produced", 0) or 0 for r in runs)
        errors = list({r["error_message"] for r in runs if r.get("error_message")})

        # Extract verb from skill name (e.g. "pulse extract" -> "extract")
        verb = skill_name.replace("pulse ", "") if skill_name.startswith("pulse ") else skill_name
        skill = skills.get(verb)
        existing_refinements = []
        if skill:
            existing_refinements = [
                {"note": r.note, "action": r.action}
                for r in skill.meta.refinements
            ]

        summaries.append({
            "skill_name": skill_name,
            "verb": verb,
            "total_runs": total,
            "succeeded": succeeded,
            "failed": failed,
            "avg_duration_ms": round(avg_duration),
            "total_atoms": atoms,
            "unique_errors": errors[:5],
            "existing_refinements": existing_refinements,
        })

    # Display summary table
    table = Table(title=f"Run Summary (last {days} days)")
    table.add_column("Skill", style="cyan")
    table.add_column("Runs", justify="right")
    table.add_column("Pass", justify="right", style="green")
    table.add_column("Fail", justify="right", style="red")
    table.add_column("Avg Duration", justify="right")
    table.add_column("Atoms", justify="right")

    for s in summaries:
        table.add_row(
            s["verb"],
            str(s["total_runs"]),
            str(s["succeeded"]),
            str(s["failed"]),
            f"{s['avg_duration_ms']}ms",
            str(s["total_atoms"]),
        )
    console.print(table)
    console.print()

    # Send to LLM for analysis
    system_prompt = """\
You are a Pulse Skills Framework analyst. Given run summaries for skills,
propose 0-5 concise, actionable refinement notes per skill.

Focus on:
- Skills with high failure rates
- Skills producing zero atoms when atoms are expected
- Duration anomalies
- Recurring error patterns
- Gaps not covered by existing refinement notes

Output YAML:
```yaml
proposals:
  - skill: <verb>
    note: "<actionable observation>"
  - skill: <verb>
    note: "<actionable observation>"
```

If no refinements are warranted, output an empty list."""

    user_msg = yaml.dump({"summaries": summaries}, default_flow_style=False)

    console.print("[bold]Analyzing runs with LLM...[/bold]")
    try:
        llm = LLMClient()
        response = llm.call(
            system=system_prompt,
            user_message=user_msg,
            temperature=0.3,
            max_tokens=2000,
        )
    except Exception as exc:
        console.print(f"[red]LLM call failed:[/red] {exc}")
        sys.exit(1)

    # Parse LLM response
    content = response.content
    # Strip markdown code fences if present
    if "```yaml" in content:
        content = content.split("```yaml", 1)[1]
        content = content.split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1]
        content = content.split("```", 1)[0]

    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        console.print("[red]Could not parse LLM response as YAML.[/red]")
        console.print(response.content)
        return

    proposals = parsed.get("proposals", []) if isinstance(parsed, dict) else []
    if not proposals:
        console.print("[green]No refinements proposed — runs look healthy.[/green]")
        return

    # Interactive accept/reject
    console.print(f"\n[bold]{len(proposals)} refinement(s) proposed:[/bold]\n")
    accepted = 0

    for i, proposal in enumerate(proposals, 1):
        verb = proposal.get("skill", "")
        note = proposal.get("note", "")
        skill = skills.get(verb)

        console.print(f"  [{i}/{len(proposals)}] [cyan]{verb}[/cyan]: {note}")

        if not skill:
            console.print(f"    [yellow]Skill '{verb}' not found — skipping.[/yellow]")
            continue

        if not sys.stdin.isatty():
            # Non-interactive: skip
            console.print("    [dim]Non-interactive mode — skipping.[/dim]")
            continue

        choice = console.input("    [A]ccept / [R]eject / [E]dit / [S]kip all: ").strip().lower()

        if choice == "s":
            console.print("    [yellow]Skipping remaining proposals.[/yellow]")
            break
        elif choice == "a":
            write_refinement(skill.path, note)
            console.print("    [green]Accepted.[/green]")
            accepted += 1
        elif choice == "e":
            edited = console.input("    Edited note: ").strip()
            if edited:
                write_refinement(skill.path, edited)
                console.print("    [green]Accepted (edited).[/green]")
                accepted += 1
            else:
                console.print("    [yellow]Empty — rejected.[/yellow]")
        else:
            console.print("    [dim]Rejected.[/dim]")

    console.print(f"\n[bold]Accepted {accepted} of {len(proposals)} proposed refinement(s).[/bold]")
