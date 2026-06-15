"""Non-interactive (headless) mode.

When enabled, operator checkpoints auto-proceed instead of blocking on terminal input,
so cadence playbooks (`pulse weekly`, `pulse daily`) run end to end without a TTY. Enabled
by the global ``--non-interactive`` / ``-y`` flag or the ``PULSE_NON_INTERACTIVE`` env var
(the latter is how headless runners turn it on without touching argv).
"""

from __future__ import annotations

import os

_NON_INTERACTIVE = False
_TRUTHY = {"1", "true", "yes", "on"}


def set_non_interactive(value: bool) -> None:
    """Set the process-wide non-interactive flag (from the CLI option)."""
    global _NON_INTERACTIVE
    _NON_INTERACTIVE = value


def is_non_interactive() -> bool:
    """True if the CLI flag was set OR ``PULSE_NON_INTERACTIVE`` is truthy."""
    if _NON_INTERACTIVE:
        return True
    return os.environ.get("PULSE_NON_INTERACTIVE", "").strip().lower() in _TRUTHY
