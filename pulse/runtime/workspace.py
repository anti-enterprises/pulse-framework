"""Workspace loading, saving, and management."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import yaml

from pulse.runtime.schemas import Workspace, WorkspaceConfig
from pulse.utils.atomic_write import atomic_write
from pulse.utils.paths import config_path, workspace_path, workspaces_dir


def load_workspace(workspace_id: str) -> Workspace:
    """Load and validate a workspace from its workspace.yaml."""
    ws_path = workspace_path(workspace_id)
    yaml_path = ws_path / "workspace.yaml"

    if not yaml_path.exists():
        raise WorkspaceError(
            f"E001: Workspace '{workspace_id}' does not exist.\n"
            f"Expected workspace.yaml at: {yaml_path}\n"
            f"Run `pulse workspace-new {workspace_id}` to create it."
        )

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise WorkspaceError(
            f"E001: Workspace '{workspace_id}' has an empty workspace.yaml.\n"
            f"Run `pulse workspace-new {workspace_id}` to recreate it."
        )

    return Workspace.model_validate(data)


def save_workspace(workspace: Workspace) -> None:
    """Save a workspace atomically."""
    ws_path = workspace_path(workspace.id)
    yaml_path = ws_path / "workspace.yaml"

    # Update last_touched
    workspace.last_touched = datetime.now(UTC)

    data = workspace.model_dump(mode="json", exclude_none=True)
    content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    atomic_write(yaml_path, content)


def list_workspaces() -> list[dict[str, str]]:
    """List all workspaces with basic info."""
    ws_dir = workspaces_dir()
    if not ws_dir.exists():
        return []

    results = []
    for entry in sorted(ws_dir.iterdir()):
        if not entry.is_dir():
            continue
        yaml_path = entry / "workspace.yaml"
        if not yaml_path.exists():
            continue
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            results.append({
                "id": data.get("id", entry.name),
                "name": data.get("name", ""),
                "industry": data.get("industry", ""),
                "created": data.get("created", ""),
                "last_touched": data.get("last_touched", ""),
            })
        except Exception:
            results.append({"id": entry.name, "name": "(error reading)", "industry": ""})

    return results


def get_active_workspace() -> str | None:
    """Get the active workspace ID from config.yaml."""
    cfg = config_path()
    if not cfg.exists():
        return None
    with open(cfg) as f:
        data = yaml.safe_load(f)
    if data is None:
        return None
    result: str | None = data.get("active_workspace")
    return result


def set_active_workspace(workspace_id: str) -> None:
    """Set the active workspace in config.yaml."""
    cfg = config_path()
    data: dict[str, object] = {}
    if cfg.exists():
        with open(cfg) as f:
            data = yaml.safe_load(f) or {}

    data["active_workspace"] = workspace_id
    content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    atomic_write(cfg, content)


def create_workspace(workspace_id: str, name: str, industry: str, created_by: str) -> Workspace:
    """Create a new workspace directory and workspace.yaml."""
    ws_path = workspace_path(workspace_id)

    if ws_path.exists():
        raise WorkspaceError(
            f"Workspace '{workspace_id}' already exists at {ws_path}.\n"
            "Choose a different ID or delete the existing workspace first."
        )

    now = datetime.now(UTC)
    workspace = Workspace(
        id=workspace_id,
        name=name,
        industry=industry,
        created=now,
        created_by=created_by,
        last_touched=now,
        config=WorkspaceConfig(),
        schema_version=1,
    )

    # Create directory structure
    ws_path.mkdir(parents=True, exist_ok=True)
    for subdir in [
        "position", "position/history",
        "ecosystem",
        "sources",
        "atoms",
        "factors",
        "directions",
        "hypotheses",
        "briefs",
        "surveys",
        "outreach",
        "field-notes",
        "runs",
        ".credentials",
    ]:
        (ws_path / subdir).mkdir(parents=True, exist_ok=True)

    # Write workspace.yaml
    save_workspace(workspace)

    # Write .gitignore
    gitignore = _workspace_gitignore()
    (ws_path / ".gitignore").write_text(gitignore)

    return workspace


def _workspace_gitignore() -> str:
    return """\
# Credentials -- never commit
.credentials/
*.key
*.pem

# Local index -- regenerable, no need to commit
.index.sqlite
.index.sqlite.bak
.index.sqlite.bak.*

# Run logs -- local artifacts
runs/

# OS noise
.DS_Store
Thumbs.db

# Editor noise
*.swp
*.swo
.vscode/
.idea/
"""


# Workspace ID validation
WORKSPACE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
RESERVED_IDS = frozenset({"default", "template", "archive", "meta", "__test__"})


def validate_workspace_id(workspace_id: str) -> str | None:
    """Validate a workspace ID. Returns error message or None if valid."""
    if not WORKSPACE_ID_RE.match(workspace_id):
        return (
            f"Invalid workspace ID: '{workspace_id}'. "
            "Must be 3-64 chars, lowercase alphanumeric and hyphens, start with a letter."
        )
    if workspace_id in RESERVED_IDS:
        return f"Workspace ID '{workspace_id}' is reserved."
    return None


class WorkspaceError(Exception):
    """Raised for workspace-related errors."""
