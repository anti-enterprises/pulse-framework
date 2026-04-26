"""Interactive decision-tree router.

Bare `pulse` (no verb) launches this. It walks a YAML decision tree,
presenting numbered options, evaluating state-aware guards, and
dispatching commands with confirmation.

Not LLM-based. Deterministic. Numbered options only.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from pulse.utils.jinja_env import evaluate_condition, render_template
from pulse.utils.paths import config_path, router_dir, runs_dir


class Router:
    """Interactive decision-tree walker."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.tree: dict[str, Any] = {}
        self.breadcrumbs: list[str] = []
        self.session_path: list[str] = []
        self.context: dict[str, Any] = {}
        self.started_at = datetime.now(UTC)
        self.dispatched_command: str | None = None

    def load_tree(self, tree_path: Path | None = None) -> None:
        """Load the router tree from YAML."""
        path = tree_path or (router_dir() / "tree.yaml")
        if not path.exists():
            raise FileNotFoundError(
                f"Router tree not found at {path}.\n"
                "Run `pulse init` to set up the framework."
            )
        with open(path) as f:
            self.tree = yaml.safe_load(f)

    def load_context(self) -> None:
        """Load workspace and config state for guard evaluation."""
        self.context = {
            "now": datetime.now(UTC),
            "today": datetime.now(UTC).date(),
            "workspace": _load_workspace_context(),
            "corpus": _load_corpus_context(),
            "config": _load_config_context(),
        }

    def walk(self) -> None:
        """Main router loop. Walks the tree until quit or command dispatch."""
        if not sys.stdin.isatty():
            self.console.print(
                "[red]Error:[/red] The pulse router requires an interactive terminal.\n"
                "Run `pulse help` for a list of commands you can invoke directly."
            )
            raise SystemExit(1)

        # First-run check
        if not config_path().exists():
            self._show_first_run()
            return

        # Load tree and context
        try:
            self.load_tree()
        except FileNotFoundError:
            self.console.print(
                "\n[dim]Router tree not found. Run `pulse help` for available commands.[/dim]\n"
            )
            return

        self.load_context()

        # Start walking
        start_node = self.tree.get("default_start", "start")
        self._walk_node(start_node)

        # Log the session
        self._log_traversal()

    def _walk_node(self, node_id: str) -> None:
        """Walk a single node and handle the result."""
        nodes = self.tree.get("nodes", {})
        if node_id not in nodes:
            self.console.print(f"[red]Router error:[/red] Unknown node '{node_id}'")
            return

        node = nodes[node_id]
        self.breadcrumbs.append(node_id)
        self.session_path.append(node_id)

        # Evaluate guards
        guards = node.get("guard", [])
        for guard in guards:
            condition = guard.get("condition", "")
            try:
                triggered = evaluate_condition(condition, self.context)
            except Exception:
                triggered = False

            if triggered:
                action = guard.get("action")
                hint = guard.get("hint")

                if action == "route_to":
                    target = guard.get("target", "start")
                    if hint:
                        self.console.print(f"\n[yellow]{render_template(hint, self.context).strip()}[/yellow]")
                    self._walk_node(target)
                    return
                elif action == "block":
                    if hint:
                        self.console.print(f"\n[red]{render_template(hint, self.context).strip()}[/red]")
                    return
                elif hint:
                    # Informational guard — show hint, continue
                    self.console.print(f"\n[dim]{render_template(hint, self.context).strip()}[/dim]")

        # Show prompt and options
        prompt = node.get("prompt", "Choose an option:")
        options = node.get("options", [])

        self.console.print(f"\n[bold]{prompt}[/bold]\n")

        for i, opt in enumerate(options, 1):
            label = opt.get("label", "")
            self.console.print(f"  [cyan]{i}[/cyan]  {label}")

        self.console.print("\n  [dim]0  Back  |  q  Quit  |  ?  Help[/dim]")

        # Get input
        while True:
            try:
                raw = input("\n> ").strip()
            except (KeyboardInterrupt, EOFError):
                if self._confirm_exit():
                    return
                continue

            action = self._parse_input(raw, options)
            if action is None:
                self.console.print("[dim]Invalid input. Enter a number, command name, or escape key.[/dim]")
                continue

            # Handle the action
            action_type = action.get("type")

            if action_type == "select_option":
                opt = action["option"]
                self._handle_option(opt)
                return

            elif action_type == "back":
                self.breadcrumbs.pop()  # remove current
                if self.breadcrumbs:
                    prev = self.breadcrumbs.pop()  # go to previous
                    self._walk_node(prev)
                else:
                    if self._confirm_exit():
                        return
                    self._walk_node(node_id)
                return

            elif action_type == "quit":
                return

            elif action_type == "help":
                self.console.print(
                    "\n[bold]Navigation:[/bold]\n"
                    "  Enter a number to select an option\n"
                    "  Type a command name directly (e.g., 'weekly')\n"
                    "  0  Go back\n"
                    "  q  Quit\n"
                    "  ?  This help\n"
                    "  <  Start over\n"
                )
                continue

            elif action_type == "start_over":
                self.breadcrumbs.clear()
                start = self.tree.get("default_start", "start")
                self._walk_node(start)
                return

            elif action_type == "direct_command":
                cmd = action["command"]
                self._dispatch_command(cmd)
                return

    def _parse_input(
        self, raw: str, options: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Parse raw input into an action dict."""
        if not raw:
            return None

        # Global escapes
        escapes = self.tree.get("short_circuit", {}).get("global_escapes", {})
        if raw in escapes:
            escape_action = escapes[raw]
            return {"type": escape_action}

        # Also support standard escapes
        if raw == "0":
            return {"type": "back"}
        if raw.lower() == "q":
            return {"type": "quit"}
        if raw == "?":
            return {"type": "help"}
        if raw == "<":
            return {"type": "start_over"}

        # Number selection
        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return {"type": "select_option", "option": options[idx - 1]}
            return None
        except ValueError:
            pass

        # Short-circuit: direct command name
        short_circuit = self.tree.get("short_circuit", {})
        if short_circuit.get("direct_command", True):
            # Strip "pulse " prefix if given
            cmd = raw.removeprefix("pulse ").strip()
            if cmd:
                return {"type": "direct_command", "command": f"pulse {cmd}"}

        return None

    def _handle_option(self, opt: dict[str, Any]) -> None:
        """Handle a selected option."""
        action = opt.get("action")
        next_node = opt.get("next")

        if next_node:
            self._walk_node(next_node)
        elif action == "run_command":
            command = opt.get("command", "")
            confirm_text = opt.get("confirm")
            if confirm_text:
                rendered = render_template(confirm_text, self.context).strip()
                self.console.print(f"\n{rendered}")
                try:
                    answer = input("\n[Y/n] ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    return
                if answer in ("n", "no"):
                    return
            self._dispatch_command(command)
        elif action == "back":
            self.breadcrumbs.pop()  # current
            if self.breadcrumbs:
                prev = self.breadcrumbs.pop()
                self._walk_node(prev)
        elif action == "quit":
            pass  # exit naturally
        elif action == "start_over":
            self.breadcrumbs.clear()
            self._walk_node(self.tree.get("default_start", "start"))

    def _dispatch_command(self, command: str) -> None:
        """Dispatch a command via the CLI."""
        self.dispatched_command = command
        self.session_path.append(command)
        self.console.print(f"\n[green]Running: {command}[/green]\n")

        # Invoke through the CLI dispatcher
        import subprocess
        verb = command.removeprefix("pulse ").strip()
        try:
            subprocess.run([sys.executable, "-m", "pulse.cli", verb], check=False)
        except Exception as e:
            self.console.print(f"[red]Error dispatching: {e}[/red]")

    def _confirm_exit(self) -> bool:
        """Prompt for exit confirmation."""
        try:
            answer = input("Exit? [y/N] ").strip().lower()
            return answer in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            return True

    def _show_first_run(self) -> None:
        """Show the first-run welcome message."""
        self.console.print(Panel(
            Text.from_markup(
                "[bold]Welcome to Pulse.[/bold]\n\n"
                "It looks like this is your first time. Before you can do anything,\n"
                "you'll need to set up the framework.\n\n"
                "Run [cyan]pulse init[/cyan] to get started.\n\n"
                "  [cyan]pulse init[/cyan]                 -- one-time framework setup\n"
                "  [cyan]pulse help[/cyan]                 -- see all commands\n"
                "  [cyan]pulse[/cyan]                      -- come back here after init"
            ),
            title="Pulse",
            border_style="blue",
        ))

        try:
            raw = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            return

        if raw:
            cmd = raw.removeprefix("pulse ").strip()
            if cmd == "q":
                return
            self._dispatch_command(f"pulse {cmd}")

    def _log_traversal(self) -> None:
        """Log the router session to the global router log."""
        log_path = runs_dir() / "router.log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        duration_s = int((datetime.now(UTC) - self.started_at).total_seconds())
        ws_ctx = self.context.get("workspace", {})

        entry = {
            "timestamp": self.started_at.isoformat(),
            "workspace": ws_ctx.get("id"),
            "path": self.session_path,
            "dispatched": self.dispatched_command,
            "confirmed": self.dispatched_command is not None,
            "completed": True,
            "duration_s": duration_s,
        }

        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


def _load_workspace_context() -> dict[str, Any]:
    """Load workspace state for guard evaluation."""
    from pulse.runtime.workspace import get_active_workspace, load_workspace

    ws_id = get_active_workspace()
    if not ws_id:
        return {"exists": False, "id": None}

    try:
        ws = load_workspace(ws_id)
        return {
            "exists": True,
            "id": ws.id,
            "name": ws.name,
            "position_set": ws.position is not None,
            "identity_set": ws.identity is not None,
            "customer_set": ws.customer is not None,
            "sources_count": 0,  # TODO: query index when available
            "active_hypotheses_count": 0,
        }
    except Exception:
        return {"exists": False, "id": ws_id}


def _load_corpus_context() -> dict[str, Any]:
    """Load corpus state for guard evaluation."""
    cfg = config_path()
    if not cfg.exists():
        return {"enabled": False}
    with open(cfg) as f:
        data = yaml.safe_load(f) or {}
    corpus = data.get("corpus", {})
    return {"enabled": corpus.get("enabled", False)}


def _load_config_context() -> dict[str, Any]:
    """Load config state for guard evaluation."""
    import os
    cfg = config_path()
    if not cfg.exists():
        return {}
    with open(cfg) as f:
        data = yaml.safe_load(f) or {}
    llm = data.get("llm", {})
    return {
        "claude_api_key_set": bool(os.environ.get(llm.get("api_key_env", ""), "")) or bool(llm.get("api_key")),
    }
