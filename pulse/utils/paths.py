"""Central path resolution for Pulse. Never hardcode ~/.pulse/ — use these helpers."""

from __future__ import annotations

import os
from pathlib import Path


def pulse_home() -> Path:
    """Return the Pulse home directory. Respects PULSE_HOME env var."""
    env = os.environ.get("PULSE_HOME")
    if env:
        return Path(env)
    return Path.home() / ".pulse"


def config_path() -> Path:
    """Global config.yaml path."""
    return pulse_home() / "config.yaml"


def workspaces_dir() -> Path:
    """Root directory for all workspaces."""
    return pulse_home() / "workspaces"


def skills_dir() -> Path:
    """Root directory for skills."""
    return pulse_home() / "skills"


def playbooks_dir() -> Path:
    """Root directory for playbooks."""
    return pulse_home() / "playbooks"


def knowledge_dir() -> Path:
    """Root directory for knowledge files."""
    return pulse_home() / "knowledge"


def corpus_dir() -> Path:
    """Root directory for corpus storage."""
    return pulse_home() / "corpus"


def router_dir() -> Path:
    """Root directory for router tree."""
    return pulse_home() / "router"


def runs_dir() -> Path:
    """Root directory for global run logs (e.g., router log)."""
    return pulse_home() / "runs"


def workspace_path(workspace_id: str) -> Path:
    """Path to a specific workspace directory."""
    return workspaces_dir() / workspace_id
