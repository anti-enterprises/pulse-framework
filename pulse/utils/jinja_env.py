"""Sandboxed Jinja2 environment for template rendering.

Exposes a restricted set of context variables:
workspace, config, now, today, defaults, steps.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jinja2 import BaseLoader, ChainableUndefined
from jinja2.sandbox import SandboxedEnvironment


def create_jinja_env() -> SandboxedEnvironment:
    """Create a sandboxed Jinja2 environment."""
    env = SandboxedEnvironment(
        loader=BaseLoader(),
        undefined=_SilentUndefined,
    )
    return env


def render_template(
    template_str: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Render a Jinja2 template string with context."""
    env = create_jinja_env()
    template = env.from_string(template_str)

    ctx = {
        "now": datetime.now(UTC),
        "today": datetime.now(UTC).date(),
    }
    if context:
        ctx.update(context)

    result: str = template.render(**ctx)
    return result


def evaluate_condition(
    condition: str,
    context: dict[str, Any] | None = None,
) -> bool:
    """Evaluate a Jinja2 condition expression."""
    result = render_template("{{ " + condition + " }}", context)
    return result.strip().lower() not in ("", "false", "none", "0")


class _SilentUndefined(ChainableUndefined):
    """Undefined that renders as empty string and silently chains attribute access.

    Must subclass jinja2.Undefined (via ChainableUndefined) so the sandbox
    environment accepts it; otherwise jinja's _environment_config_check asserts.
    """

    def __str__(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return False
