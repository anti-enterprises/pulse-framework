"""Prompt composition for LLM-backed skills.

Composes the full prompt from:
- Skill procedure (markdown body of SKILL.md)
- Knowledge files (loaded by path)
- Workspace context (serialized workspace.yaml sections)
- Examples (if declared)
"""

from __future__ import annotations

from typing import Any

import yaml


def compose_skill_prompt(
    procedure: str,
    knowledge: dict[str, str] | None = None,
    workspace_context: dict[str, Any] | None = None,
    examples: list[str] | None = None,
) -> tuple[str, str]:
    """Compose system and user messages for a skill's LLM call.

    Returns (system_message, user_message).
    """
    # System message: role framing + knowledge
    system_parts = [
        "You are Pulse, a business intelligence assistant. You execute skill "
        "procedures precisely, producing structured output in the format specified.",
        "",
        "Follow the procedure below step by step. Produce output in YAML format "
        "unless the procedure specifies otherwise.",
    ]

    if knowledge:
        system_parts.append("\n--- KNOWLEDGE ---\n")
        for path, content in knowledge.items():
            system_parts.append(f"### {path}\n\n{content}\n")

    system = "\n".join(system_parts)

    # User message: workspace context + procedure + examples
    user_parts = []

    if workspace_context:
        user_parts.append("--- WORKSPACE CONTEXT ---\n")
        user_parts.append(yaml.dump(workspace_context, default_flow_style=False))
        user_parts.append("")

    user_parts.append("--- PROCEDURE ---\n")
    user_parts.append(procedure)

    if examples:
        user_parts.append("\n--- EXAMPLES ---\n")
        for i, example in enumerate(examples, 1):
            user_parts.append(f"### Example {i}\n\n{example}\n")

    user = "\n".join(user_parts)

    return system, user
