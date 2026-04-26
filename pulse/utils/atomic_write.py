"""Atomic file writes to prevent corruption on crash.

Pattern: write to tempfile in same dir, fsync, os.replace.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically.

    Creates a tempfile in the same directory, writes, fsyncs,
    then atomically replaces the target.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd = None
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        os.write(fd, content.encode())
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if fd is not None:
            os.close(fd)
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)


def atomic_append(path: Path, line: str) -> None:
    """Append a line to a file atomically (via open + write + fsync).

    For append-only files like atoms.jsonl — not a full replace.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(line)
        if not line.endswith("\n"):
            f.write("\n")
        f.flush()
        os.fsync(f.fileno())
