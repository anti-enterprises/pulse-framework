"""Command resolution and dispatch for the pulse CLI.

Resolution precedence (from doc 04):
1. Exact built-in command match
2. Exact skill name match
3. Exact playbook name match
4. Alias match (skills and playbooks)
5. Unique prefix match
6. Fuzzy match with disambiguation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import get_close_matches
from enum import StrEnum
from typing import Any


class TargetKind(StrEnum):
    BUILTIN = "builtin"
    SKILL = "skill"
    PLAYBOOK = "playbook"
    DEFERRED = "deferred"


@dataclass
class DispatchTarget:
    name: str
    kind: TargetKind
    description: str
    layer: str = ""
    aliases: list[str] = field(default_factory=list)
    handler: Any = None  # Click command or skill/playbook object


# Reserved verbs that cannot be used by user-defined skills
RESERVED_VERBS = frozenset({
    "init", "help", "version", "intel-query", "emit",
    "portfolio-scan", "upgrade-to-v2", "validate", "migrate",
})

# Deferred commands (reserved for future versions)
DEFERRED_COMMANDS: dict[str, str] = {
    "intel-query": "Reserved for v2 — curated business-intelligence queries.",
    "emit": "Reserved for v3 — outbound action integrations.",
    "portfolio-scan": "Reserved for v4 — cross-workspace pattern detection.",
}


class CommandRegistry:
    """Registry of all dispatchable commands."""

    def __init__(self) -> None:
        self._targets: dict[str, DispatchTarget] = {}
        self._aliases: dict[str, str] = {}

        # Register deferred commands
        for verb, desc in DEFERRED_COMMANDS.items():
            self.register(DispatchTarget(
                name=verb,
                kind=TargetKind.DEFERRED,
                description=desc,
            ))

    def register(self, target: DispatchTarget) -> None:
        """Register a dispatch target."""
        self._targets[target.name] = target
        for alias in target.aliases:
            # Strip "pulse " prefix from aliases for lookup
            clean = alias.removeprefix("pulse ")
            self._aliases[clean] = target.name

    def resolve(self, verb: str) -> DispatchTarget | None:
        """Resolve a verb to a dispatch target.

        Returns None if no match found. Raises AmbiguousCommandError
        if multiple candidates match.
        """
        # 1. Exact match
        if verb in self._targets:
            return self._targets[verb]

        # 2. Alias match
        if verb in self._aliases:
            return self._targets[self._aliases[verb]]

        # 3. Unique prefix match
        prefix_matches = [
            name for name in self._targets
            if name.startswith(verb) and self._targets[name].kind != TargetKind.DEFERRED
        ]
        if len(prefix_matches) == 1:
            return self._targets[prefix_matches[0]]

        # 4. Fuzzy match (edit distance)
        all_names = list(self._targets.keys()) + list(self._aliases.keys())
        close = get_close_matches(verb, all_names, n=3, cutoff=0.6)
        if close:
            # If exactly one close match, return it
            # Resolve aliases to targets
            resolved = set()
            for c in close:
                if c in self._aliases:
                    resolved.add(self._aliases[c])
                elif c in self._targets:
                    resolved.add(c)
            if len(resolved) == 1:
                return self._targets[resolved.pop()]

        return None

    def suggest(self, verb: str) -> list[str]:
        """Get suggestions for an unknown verb."""
        all_names = list(self._targets.keys()) + list(self._aliases.keys())
        return get_close_matches(verb, all_names, n=3, cutoff=0.5)

    def all_targets(self) -> dict[str, DispatchTarget]:
        """Return all registered targets."""
        return dict(self._targets)

    def targets_by_layer(self) -> dict[str, list[DispatchTarget]]:
        """Group targets by layer for help display."""
        groups: dict[str, list[DispatchTarget]] = {}
        for target in self._targets.values():
            layer = target.layer or "meta"
            groups.setdefault(layer, []).append(target)
        return groups
