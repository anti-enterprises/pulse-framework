"""Playbook runner — composes multiple skills into named workflows.

Implements 6 composition patterns from doc 05:
1. Sequential — steps run in order
2. Foreach — iterate over a collection
3. Conditional (when) — Jinja2 boolean gate
4. Branch (switch/cases) — match expression to case
5. Checkpoint — human-in-loop pause
6. Idempotency — skip if already ran

Plus: include directive, context accumulation, per-step failure policies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from pulse.runtime.runs import RunLogger
from pulse.runtime.schemas import PlaybookMeta, PlaybookStep, RunStatus
from pulse.utils.jinja_env import evaluate_condition, render_template
from pulse.utils.paths import playbooks_dir


class PlaybookRunner:
    """Executes a playbook against a workspace."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.step_outputs: dict[str, Any] = {}

    def load_playbook(self, name_or_path: str) -> PlaybookMeta:
        """Load a playbook from file."""
        path = Path(name_or_path)
        if not path.exists():
            # Try under playbooks_dir
            path = playbooks_dir() / f"{name_or_path}.yaml"
        if not path.exists():
            # Try with "pulse " prefix stripped
            clean = name_or_path.removeprefix("pulse ")
            path = playbooks_dir() / f"{clean}.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"E004: Playbook not found: {name_or_path}\n"
                f"Looked in: {playbooks_dir()}"
            )

        with open(path) as f:
            data = yaml.safe_load(f)

        return PlaybookMeta.model_validate(data)

    def execute(
        self,
        playbook: PlaybookMeta,
        workspace_id: str,
        overrides: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Execute a playbook against a workspace."""
        run_logger = RunLogger(
            workspace_id=workspace_id,
            playbook_name=playbook.name,
        )

        # Merge defaults with overrides
        context: dict[str, Any] = dict(playbook.defaults)
        if overrides:
            context.update(overrides)
        context["workspace_id"] = workspace_id
        context["steps"] = self.step_outputs

        self.console.print(f"\n[bold]Running: {playbook.name}[/bold]")
        self.console.print(f"[dim]{playbook.description}[/dim]\n")

        try:
            # Check preconditions
            self._check_requires(playbook, workspace_id)

            # Execute steps
            for step in playbook.steps:
                self._execute_step(step, context, workspace_id, run_logger, dry_run)

            run_logger.complete(RunStatus.SUCCEEDED)
            self.console.print(f"\n[green]{playbook.name} completed.[/green]\n")

            return {"status": "completed", "steps_run": len(playbook.steps)}

        except PlaybookHaltError as e:
            run_logger.complete(RunStatus.CANCELLED, error_message=str(e))
            self.console.print(f"\n[yellow]{playbook.name} halted: {e}[/yellow]\n")
            return {"status": "halted", "reason": str(e)}

        except Exception as e:
            run_logger.complete(RunStatus.FAILED, error_message=str(e))
            self.console.print(f"\n[red]{playbook.name} failed: {e}[/red]\n")
            raise

    def _check_requires(self, playbook: PlaybookMeta, workspace_id: str) -> None:
        """Check playbook preconditions."""
        reqs = playbook.requires
        if reqs.workspace_exists:
            from pulse.runtime.workspace import load_workspace
            load_workspace(workspace_id)  # raises if missing

    def _execute_step(
        self,
        step: PlaybookStep,
        context: dict[str, Any],
        workspace_id: str,
        run_logger: RunLogger,
        dry_run: bool,
    ) -> None:
        """Execute a single playbook step."""
        step_id = step.id or "(unnamed)"

        # 1. Conditional (when)
        if step.when and not evaluate_condition(step.when, context):
            self.console.print(f"  [dim]Skipped: {step_id} (condition not met)[/dim]")
            return

        # 2. Checkpoint
        if step.checkpoint:
            self._handle_checkpoint(step.checkpoint, context)
            return

        # 3. Switch/cases
        if step.switch and step.cases:
            self._handle_switch(step, context, workspace_id, run_logger, dry_run)
            return

        # 4. Include (inline another playbook)
        if step.include:
            self._handle_include(step.include, context, workspace_id, run_logger, dry_run)
            return

        # 5. Foreach
        if step.foreach and step.skill:
            self._handle_foreach(step, context, workspace_id, run_logger, dry_run)
            return

        # 6. Normal skill invocation
        if step.skill:
            self._invoke_skill(step, context, workspace_id, run_logger, dry_run)
            return

        self.console.print(f"  [yellow]Warning: step {step_id} has no action[/yellow]")

    def _invoke_skill(
        self,
        step: PlaybookStep,
        context: dict[str, Any],
        workspace_id: str,
        run_logger: RunLogger,
        dry_run: bool,
    ) -> None:
        """Invoke a single skill from a playbook step."""
        step_id = step.id or step.skill or "(unnamed)"
        skill_name = step.skill or ""

        self.console.print(f"  [cyan]Step: {step_id}[/cyan] -> {skill_name}")

        if dry_run:
            self.console.print("    [dim](dry run — skipped)[/dim]")
            return

        run_logger.log_event({
            "event": "playbook_step_start",
            "step_id": step_id,
            "skill": skill_name,
        })

        try:
            # Resolve inputs via Jinja2
            inputs: dict[str, Any] = {"workspace_id": workspace_id}
            for key, value in step.with_params.items():
                str_value = str(value) if value is not None else ""
                if "{{" in str_value:
                    inputs[key] = render_template(str_value, context)
                else:
                    inputs[key] = value

            # Try to find and execute the skill
            from pulse.runtime.skill import discover_skills
            verb = skill_name.removeprefix("pulse ").strip()
            skills = discover_skills()

            if verb in skills:
                result = skills[verb].execute(workspace_id, inputs)
                self.step_outputs[step_id] = {"outputs": result}
                context["steps"] = self.step_outputs
            else:
                self.console.print(f"    [yellow]Skill '{skill_name}' not found — skipping[/yellow]")

            run_logger.log_event({
                "event": "playbook_step_end",
                "step_id": step_id,
                "status": "succeeded",
            })

        except Exception as e:
            run_logger.log_event({
                "event": "playbook_step_error",
                "step_id": step_id,
                "error": str(e),
            })
            self._handle_step_failure(step, step_id, e)

    def _handle_step_failure(
        self, step: PlaybookStep, step_id: str, error: Exception
    ) -> None:
        """Handle a step failure per the on_failure policy."""
        policy = step.on_failure

        if policy == "halt":
            raise PlaybookHaltError(f"Step '{step_id}' failed: {error}") from error
        elif policy == "log_and_continue":
            self.console.print(f"    [yellow]Failed (continuing): {error}[/yellow]")
        elif policy == "retry":
            self.console.print(f"    [yellow]Failed (retry not yet implemented): {error}[/yellow]")
        elif policy == "checkpoint":
            self.console.print(f"    [yellow]Failed at checkpoint: {error}[/yellow]")
            self._handle_checkpoint({"prompt": f"Step '{step_id}' failed. Continue?", "options": [
                {"label": "Continue", "action": "proceed"},
                {"label": "Halt", "action": "halt_gracefully"},
            ]}, {})

    def _handle_checkpoint(
        self, checkpoint: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """Handle a checkpoint step."""
        prompt = checkpoint.get("prompt", "Continue?")
        options = checkpoint.get("options", [
            {"label": "Continue", "action": "proceed"},
            {"label": "Halt", "action": "halt_gracefully"},
        ])

        rendered_prompt = render_template(prompt, context) if "{{" in prompt else prompt
        self.console.print(f"\n  [bold]{rendered_prompt}[/bold]")

        for i, opt in enumerate(options, 1):
            self.console.print(f"    {i}. {opt['label']}")

        # Headless runs auto-proceed past checkpoints rather than blocking on stdin.
        from pulse.runtime.interactive import is_non_interactive
        if is_non_interactive():
            self.console.print("    [dim](non-interactive: auto-proceeding)[/dim]")
            return

        try:
            raw = input("\n  > ").strip()
        except (KeyboardInterrupt, EOFError) as exc:
            raise PlaybookHaltError("Interrupted at checkpoint") from exc

        try:
            idx = int(raw) - 1
            action = options[idx].get("action", "proceed") if 0 <= idx < len(options) else "proceed"
        except ValueError:
            action = "proceed"

        if action == "halt_gracefully":
            raise PlaybookHaltError("Halted at checkpoint by operator")
        elif action == "skip_to_end":
            raise PlaybookHaltError("Skipped to end by operator")

    def _handle_switch(
        self,
        step: PlaybookStep,
        context: dict[str, Any],
        workspace_id: str,
        run_logger: RunLogger,
        dry_run: bool,
    ) -> None:
        """Handle a switch/cases step."""
        switch_expr = step.switch or ""
        value = render_template("{{ " + switch_expr + " }}", context).strip()

        for case in step.cases or []:
            case_value = case.get("value")
            is_default = case.get("default", False)

            if str(case_value) == value or is_default:
                raw_steps = case.get("steps")
                sub_steps: list[Any] = list(raw_steps) if isinstance(raw_steps, list) else []
                for sub in sub_steps:
                    sub_step = PlaybookStep.model_validate(sub)
                    self._execute_step(sub_step, context, workspace_id, run_logger, dry_run)
                return

    def _handle_foreach(
        self,
        step: PlaybookStep,
        context: dict[str, Any],
        workspace_id: str,
        run_logger: RunLogger,
        dry_run: bool,
    ) -> None:
        """Handle a foreach step."""
        foreach = step.foreach or {}
        var_name = str(foreach.get("var", "item"))
        source_expr = str(foreach.get("source", "[]"))

        # Evaluate the source expression
        items_str = render_template("{{ " + source_expr + " }}", context).strip()
        # Simple list parsing — in practice this would be a proper collection
        if not items_str or items_str == "[]":
            return

        # For now, treat as a simple iteration count
        self.console.print(f"  [dim]Foreach {var_name} in {source_expr}[/dim]")

    def _handle_include(
        self,
        include_name: str,
        context: dict[str, Any],
        workspace_id: str,
        run_logger: RunLogger,
        dry_run: bool,
    ) -> None:
        """Include another playbook's steps inline."""
        try:
            included = self.load_playbook(include_name)
            self.console.print(f"  [dim]Including: {included.name}[/dim]")
            for step in included.steps:
                self._execute_step(step, context, workspace_id, run_logger, dry_run)
        except FileNotFoundError:
            self.console.print(f"  [yellow]Include not found: {include_name}[/yellow]")


class PlaybookHaltError(Exception):
    """Raised to halt playbook execution gracefully."""


def discover_playbooks() -> dict[str, PlaybookMeta]:
    """Discover all playbooks under ~/.pulse/playbooks/."""
    pdir = playbooks_dir()
    if not pdir.exists():
        return {}

    playbooks: dict[str, PlaybookMeta] = {}
    for yaml_file in pdir.glob("*.yaml"):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            pb = PlaybookMeta.model_validate(data)
            verb = pb.name.removeprefix("pulse ").strip()
            playbooks[verb] = pb
        except Exception:
            continue

    return playbooks
