"""The `pulse export` command — emit workspace intelligence as JSON.

Outputs directions + hypotheses + briefs in a stable JSON shape for downstream consumers
(e.g. an external content/concepts mirror). The filesystem is the source of truth, so this
reads the per-entity YAML directly — no LLM, no SQLite-index dependency. JSON is the only
format; a trailing ``--json`` flag is accepted for explicitness and ignored otherwise.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from pulse.runtime.workspace import get_active_workspace
from pulse.utils.paths import workspace_path


def _iso(value: Any) -> Any:
    """Datetimes/dates → ISO 8601 (so consumers can parse them); pass other types through."""
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    return value


def _load_yaml_dir(directory: Path) -> list[dict[str, Any]]:
    """Load every ``*.yaml`` in a directory as a dict (best-effort; skips malformed files)."""
    out: list[dict[str, Any]] = []
    if not directory.exists():
        return out
    for yf in sorted(directory.glob("*.yaml")):
        try:
            with open(yf) as f:
                doc = yaml.safe_load(f)
            if isinstance(doc, dict):
                out.append(doc)
        except Exception:
            continue
    return out


def _brief_kind(path: Path) -> str:
    """``2024-01-15-weekly-digest.md`` → ``weekly_digest`` (drop date parts)."""
    parts = [p for p in path.stem.split("-") if not p.isdigit()]
    return "_".join(parts) if parts else path.stem


def build_export(workspace_id: str) -> dict[str, Any]:
    """Assemble the export payload for a workspace from its on-disk YAML/Markdown."""
    ws = workspace_path(workspace_id)
    raw_dirs = _load_yaml_dir(ws / "directions")
    raw_hyps = _load_yaml_dir(ws / "hypotheses")

    # direction id → code, to resolve hypothesis.direction_ids into codes
    id_to_code = {d["id"]: d["code"] for d in raw_dirs if d.get("id") and d.get("code")}

    directions = [
        {
            "code": d.get("code"),
            "title": d.get("title"),
            "state": d.get("state"),
            "momentum": d.get("momentum"),
            "confidence": d.get("confidence"),
            "last_updated": _iso(d.get("last_updated")),
            "atom_count": d.get("atom_count", 0),
            "topic_ids": [],  # Pulse directions carry no topic tags; consumers default to []
        }
        for d in raw_dirs
        if d.get("code") and d.get("title")
    ]

    hypotheses = [
        {
            "code": h.get("code"),
            "title": h.get("title"),
            "detail": h.get("statement"),  # Pulse `statement` → consumer `detail`/thesis
            "state": h.get("state"),
            "confidence": h.get("confidence"),
            "direction_codes": [
                id_to_code[i] for i in (h.get("direction_ids") or []) if i in id_to_code
            ],
        }
        for h in raw_hyps
        if h.get("code") and h.get("title")
    ]

    briefs: list[dict[str, Any]] = []
    briefs_dir = ws / "briefs"
    if briefs_dir.exists():
        for bf in sorted(briefs_dir.glob("*.md")):
            briefs.append({"kind": _brief_kind(bf), "key_findings": []})

    return {"directions": directions, "hypotheses": hypotheses, "briefs": briefs}


def run_export(args: tuple[str, ...] = ()) -> None:
    """`pulse export [workspace] [--json]` — print the export JSON to stdout."""
    positional = [a for a in args if not a.startswith("-")]
    workspace_id = positional[0] if positional else get_active_workspace()
    if not workspace_id:
        Console(stderr=True).print(
            "[red]Error:[/red] No active workspace. "
            "Run `pulse workspace-switch <id>` or pass the workspace ID."
        )
        raise SystemExit(1)
    try:
        payload = build_export(workspace_id)
    except Exception as e:  # surface any load error as a clean CLI failure
        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from e
    # plain stdout (not rich) so a headless runner can capture + json.loads it verbatim
    print(json.dumps(payload, default=str))
