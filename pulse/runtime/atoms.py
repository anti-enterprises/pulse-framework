"""Atom read/write primitives.

Atoms are stored as append-only JSONL files, partitioned by month:
  atoms/YYYY-MM/atoms.jsonl
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pulse.runtime.schemas import Atom
from pulse.utils.atomic_write import atomic_append
from pulse.utils.paths import workspace_path


def write_atom(workspace_id: str, atom: Atom) -> Path:
    """Append an atom to the correct month-partitioned JSONL file."""
    month = atom.extracted_at.strftime("%Y-%m")
    ws = workspace_path(workspace_id)
    atoms_file = ws / "atoms" / month / "atoms.jsonl"

    line = atom.model_dump_json()
    atomic_append(atoms_file, line)
    return atoms_file


def read_atoms(
    workspace_id: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[Atom]:
    """Read atoms from the workspace, optionally filtered by date range."""
    ws = workspace_path(workspace_id)
    atoms_dir = ws / "atoms"

    if not atoms_dir.exists():
        return []

    atoms: list[Atom] = []
    for month_dir in sorted(atoms_dir.iterdir()):
        if not month_dir.is_dir():
            continue
        for jsonl_file in month_dir.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        atom = Atom.model_validate(data)
                        if since and atom.extracted_at < since:
                            continue
                        if until and atom.extracted_at > until:
                            continue
                        atoms.append(atom)
                    except (json.JSONDecodeError, Exception):
                        continue

    return atoms
