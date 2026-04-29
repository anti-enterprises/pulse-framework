"""Entry point for the `pulse` CLI.

Uses Click with a single command that accepts an optional verb and
dispatches through the CommandRegistry for alias/prefix/fuzzy resolution.

Architecture: built-ins + skill bridge (per Codex architecture review).
The static catalog derives from the manifest; Phase 3 adds dynamic
skill/playbook discovery that merges into the same registry.
"""

from __future__ import annotations

import sys

import click
from rich.console import Console

from pulse import __version__
from pulse.commands.help import show_help
from pulse.dispatcher import CommandRegistry, DispatchTarget, TargetKind
from pulse.manifest import MANIFEST


def _catalog_from_manifest() -> list[DispatchTarget]:
    """Derive the dispatcher catalog from the canonical manifest."""
    kind_map = {
        "builtin": TargetKind.BUILTIN,
        "skill": TargetKind.SKILL,
        "playbook": TargetKind.PLAYBOOK,
        "deferred": TargetKind.DEFERRED,
    }
    targets: list[DispatchTarget] = []
    for entry in MANIFEST:
        # "help" is handled specially in dispatch, not via the registry
        if entry.name == "help":
            continue
        targets.append(DispatchTarget(
            name=entry.name,
            kind=kind_map[entry.kind],
            description=entry.description,
            layer=entry.layer,
            aliases=list(entry.aliases),
        ))
    return targets


def build_registry() -> CommandRegistry:
    """Build the command registry.

    Phase 1-2: static catalog from manifest.
    Phase 3+: also scans ~/.pulse/skills/ and ~/.pulse/playbooks/.
    """
    from pulse.commands.corpus import run_corpus_status, run_disable_corpus, run_enable_corpus
    from pulse.commands.evolve_all import run_evolve_all
    from pulse.commands.import_refinements import run_import_refinements
    from pulse.commands.init import run_init
    from pulse.commands.refine import run_refine
    from pulse.commands.refine_from_runs import run_refine_from_runs
    from pulse.commands.reindex import run_reindex
    from pulse.commands.workspace_list import run_workspace_list
    from pulse.commands.workspace_new import run_workspace_new
    from pulse.commands.workspace_status import run_workspace_status
    from pulse.commands.workspace_switch import run_workspace_switch

    handlers: dict[str, object] = {
        "init": lambda args: run_init(),
        "workspace-new": run_workspace_new,
        "workspace-list": lambda args: run_workspace_list(),
        "workspace-switch": run_workspace_switch,
        "workspace-status": run_workspace_status,
        "reindex": run_reindex,
        "enable-corpus": run_enable_corpus,
        "disable-corpus": run_disable_corpus,
        "corpus-status": run_corpus_status,
        "evolve-all": run_evolve_all,
        "refine": run_refine,
        "refine-from-runs": run_refine_from_runs,
        "import-refinements": run_import_refinements,
    }

    registry = CommandRegistry()
    for target in _catalog_from_manifest():
        if target.name in handlers:
            target.handler = handlers[target.name]
        registry.register(target)

    # Phase 3: discover skills from ~/.pulse/skills/ and merge into registry.
    # If a manifest entry already exists (handler-less), attach the discovered
    # skill as its handler so dispatch reaches the runtime instead of the
    # "registered but not yet implemented" stub message.
    try:
        from pulse.runtime.skill import discover_skills
        from pulse.runtime.workspace import get_active_workspace
        skills = discover_skills()
        for verb, skill in skills.items():
            def _make_skill_handler(s=skill):
                def _handler(args: tuple[str, ...]) -> None:
                    workspace_id = args[0] if args else (get_active_workspace() or "")
                    if not workspace_id:
                        from rich.console import Console
                        Console().print(
                            "\n[red]Error:[/red] No active workspace. "
                            "Run `pulse workspace-switch <id>` or pass the workspace ID positionally.\n"
                        )
                        raise SystemExit(2)
                    runtime_type = s.meta.runtime.get("type", "llm_procedure")
                    delegated = _delegated_runtime()
                    if delegated and runtime_type == "llm_procedure":
                        _print_delegate_redirect(delegated, s.verb, kind="skill")
                        return
                    s.execute(workspace_id=workspace_id, inputs={"workspace_id": workspace_id})
                return _handler

            existing = registry.resolve(verb)
            if existing is None:
                registry.register(DispatchTarget(
                    name=verb,
                    kind=TargetKind.SKILL,
                    description=skill.meta.description,
                    layer=skill.meta.layer,
                    aliases=skill.meta.aliases,
                    handler=_make_skill_handler(),
                ))
            elif existing.handler is None:
                existing.handler = _make_skill_handler()
    except Exception:
        pass  # Skill discovery failure is non-fatal

    # Phase 3: discover playbooks from ~/.pulse/playbooks/ and attach
    # PlaybookRunner handlers to matching manifest entries.
    try:
        from pulse.runtime.playbook import PlaybookRunner
        from pulse.runtime.workspace import get_active_workspace
        from pulse.utils.paths import playbooks_dir as _playbooks_dir
        pb_dir = _playbooks_dir()
        if pb_dir.exists():
            for pb_file in sorted(pb_dir.glob("*.yaml")):
                # Verb is the filename stem (e.g., weekly.yaml -> "weekly").
                verb = pb_file.stem

                def _make_playbook_handler(path=pb_file, _verb=verb):
                    def _handler(args: tuple[str, ...]) -> None:
                        workspace_id = args[0] if args else (get_active_workspace() or "")
                        if not workspace_id:
                            from rich.console import Console
                            Console().print(
                                "\n[red]Error:[/red] No active workspace. "
                                "Run `pulse workspace-switch <id>` or pass the workspace ID positionally.\n"
                            )
                            raise SystemExit(2)
                        delegated = _delegated_runtime()
                        if delegated:
                            # Playbooks compose llm_procedure skills; redirect
                            # the entire playbook in delegated mode rather than
                            # iterating and printing N redirects.
                            _print_delegate_redirect(delegated, _verb, kind="playbook")
                            return
                        runner = PlaybookRunner()
                        playbook = runner.load_playbook(str(path))
                        runner.execute(playbook=playbook, workspace_id=workspace_id)
                    return _handler

                existing = registry.resolve(verb)
                if existing is None:
                    registry.register(DispatchTarget(
                        name=verb,
                        kind=TargetKind.PLAYBOOK,
                        description=f"Playbook from {pb_file.name}",
                        layer="playbook",
                        handler=_make_playbook_handler(),
                    ))
                elif existing.handler is None:
                    existing.handler = _make_playbook_handler()
    except Exception:
        pass  # Playbook discovery failure is non-fatal

    return registry


def _delegated_runtime() -> str | None:
    """Read llm.delegated_runtime from ~/.pulse/config.yaml.

    Returns the runtime name (e.g., "claude_code") if set, else None.
    Failure to read config is treated as None (use API directly).
    """
    try:
        import yaml
        from pulse.utils.paths import config_path
        cfg = config_path()
        if not cfg.exists():
            return None
        with open(cfg) as f:
            data = yaml.safe_load(f) or {}
        llm = data.get("llm") or {}
        value = llm.get("delegated_runtime")
        return str(value) if value else None
    except Exception:
        return None


def _print_delegate_redirect(runtime_name: str, verb: str, kind: str = "skill") -> None:
    """Print a redirect message when delegated_runtime intercepts dispatch."""
    from rich.console import Console
    pretty = {"claude_code": "Claude Code"}.get(runtime_name, runtime_name)
    invoke_form = {"claude_code": f"/pulse-{verb}"}.get(runtime_name, f"/{verb}")
    Console().print(
        f"\n[yellow]pulse {verb}[/yellow] is an LLM {kind}.\n"
        f"This Pulse install delegates LLM execution to [bold]{pretty}[/bold] "
        f"(llm.delegated_runtime in ~/.pulse/config.yaml).\n"
        f"Invoke [bold]{invoke_form}[/bold] in {pretty} instead, or unset "
        f"llm.delegated_runtime to call the API directly.\n"
    )


# Lazily-built singleton
_registry: CommandRegistry | None = None


def get_registry() -> CommandRegistry:
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry


@click.command(context_settings={"ignore_unknown_options": True})
@click.version_option(__version__, prog_name="pulse")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--workspace", "-w", default=None, help="Override active workspace.")
@click.argument("verb", required=False)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def main(
    verbose: bool,
    workspace: str | None,
    verb: str | None,
    args: tuple[str, ...],
) -> None:
    """Pulse Skills Framework -- business intelligence, operationalized."""
    registry = get_registry()
    console = Console()

    # No verb -- launch the router (built-in exception, dedicated runtime type)
    if verb is None:
        _launch_router()
        return

    # "help" is a built-in, not dispatched through registry
    if verb == "help":
        help_verb = args[0] if args else None
        show_help(registry, help_verb)
        return

    # Resolve through the registry
    target = registry.resolve(verb)

    if target is None:
        suggestions = registry.suggest(verb)
        console.print(f"\n[red]Error:[/red] Unknown command: pulse {verb}")
        if suggestions:
            console.print(
                f"Did you mean: {', '.join(f'pulse {s}' for s in suggestions)}"
            )
        console.print("\nRun `pulse help` for a list of available commands.\n")
        raise SystemExit(2)

    if target.kind == TargetKind.DEFERRED:
        console.print(f"\n[yellow]pulse {target.name}[/yellow]: {target.description}\n")
        return

    # Command exists but not yet implemented
    if target.handler is None:
        console.print(
            f"\n[yellow]pulse {target.name}[/yellow] is registered but not yet implemented.\n"
            "This command will be available in a future phase.\n"
        )
        raise SystemExit(1)

    # Invoke the handler
    target.handler(args)


def _launch_router() -> None:
    """Launch the interactive router.

    Per architecture: bare `pulse` is a built-in exception with
    dedicated runtime type, not forced through skill-name regex.
    """
    if not sys.stdin.isatty():
        console = Console()
        console.print(
            "[red]Error:[/red] The pulse router requires an interactive terminal.\n"
            "Run `pulse help` for a list of commands you can invoke directly."
        )
        raise SystemExit(1)

    from pulse.runtime.router import Router
    router = Router()
    router.walk()
