"""Corpus management commands: enable-corpus, disable-corpus, corpus-status."""

from __future__ import annotations

import yaml
from rich.console import Console

from pulse.utils.atomic_write import atomic_write
from pulse.utils.paths import config_path


def run_enable_corpus(args: tuple[str, ...] = ()) -> None:
    """Enable corpus infrastructure."""
    console = Console()

    cfg = config_path()
    if not cfg.exists():
        console.print("\n[red]Error:[/red] Run `pulse init` first.\n")
        raise SystemExit(1)

    with open(cfg) as f:
        config = yaml.safe_load(f) or {}

    if config.get("corpus", {}).get("enabled"):
        console.print("\n[dim]Corpus is already enabled.[/dim]\n")
        return

    try:
        from pulse.runtime.corpus import CorpusManager
        mgr = CorpusManager()
        mgr.initialize()
        console.print("\n[green]Corpus enabled and initialized.[/green]\n")
    except Exception as e:
        console.print(f"\n[red]Error enabling corpus:[/red] {e}\n")
        console.print("[dim]Corpus requires: pip install pulse-skills[corpus][/dim]\n")
        raise SystemExit(1) from e


def run_disable_corpus(args: tuple[str, ...] = ()) -> None:
    """Disable corpus infrastructure."""
    console = Console()

    cfg = config_path()
    if not cfg.exists():
        console.print("\n[red]Error:[/red] Run `pulse init` first.\n")
        raise SystemExit(1)

    with open(cfg) as f:
        config = yaml.safe_load(f) or {}

    config.setdefault("corpus", {})
    config["corpus"]["enabled"] = False
    atomic_write(cfg, yaml.dump(config, default_flow_style=False))

    console.print("\n[green]Corpus disabled.[/green]\n")


def run_corpus_status(args: tuple[str, ...] = ()) -> None:
    """Show corpus status."""
    console = Console()

    from pulse.runtime.corpus import CorpusManager
    mgr = CorpusManager()
    status = mgr.status()

    if not status.get("enabled"):
        console.print(
            "\n[dim]Corpus is not enabled.[/dim]\n"
            "Run `pulse enable-corpus` to enable it.\n"
        )
        return

    console.print("\n[bold]Corpus Status[/bold]\n")
    console.print("  Enabled: [green]yes[/green]")
    console.print(f"  Embedding provider: {status.get('embedding_provider', 'unknown')}")
    console.print(f"  Collections: {', '.join(status.get('collections', []))}")
    console.print(f"  Total ingestions: {status.get('total_ingestions', 0)}")
    if "index_size_mb" in status:
        console.print(f"  Index size: {status['index_size_mb']} MB")
    console.print()
