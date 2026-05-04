"""Tests for LLM prompt composition."""

from __future__ import annotations

from pulse.utils.prompts import compose_skill_prompt


def test_compose_skill_prompt_includes_inputs() -> None:
    _system, user = compose_skill_prompt(
        procedure="# Procedure\n\nDo the thing.",
        inputs={
            "workspace_id": "anti-enterprises",
            "analysis_depth": "weekly",
            "source_scope": "eligible_active",
        },
    )

    assert "--- INPUTS ---" in user
    assert "analysis_depth: weekly" in user
    assert "source_scope: eligible_active" in user
    assert "--- PROCEDURE ---" in user
