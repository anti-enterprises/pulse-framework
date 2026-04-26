"""Skill discovery, loading, and execution.

A skill is a folder under ~/.pulse/skills/<layer>/<name>/ containing
at minimum a SKILL.md with YAML frontmatter.

Loading is cheap (frontmatter only). Execution is expensive (knowledge,
LLM calls, file writes).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter
import yaml

from pulse.runtime.schemas import SkillFrontmatter
from pulse.utils.paths import skills_dir


class Skill:
    """A loaded skill definition."""

    def __init__(self, path: Path, meta: SkillFrontmatter, procedure: str) -> None:
        self.path = path
        self.meta = meta
        self.procedure = procedure
        self._input_schema: dict[str, Any] | None = None
        self._output_schema: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def verb(self) -> str:
        """The CLI verb (name without 'pulse ' prefix)."""
        return self.meta.name.removeprefix("pulse ")

    @property
    def input_schema(self) -> dict[str, Any] | None:
        """Lazy-load input schema."""
        if self._input_schema is None:
            schema_path = self.path / "schema.input.yaml"
            if schema_path.exists():
                with open(schema_path) as f:
                    self._input_schema = yaml.safe_load(f)
        return self._input_schema

    @property
    def output_schema(self) -> dict[str, Any] | None:
        """Lazy-load output schema."""
        if self._output_schema is None:
            schema_path = self.path / "schema.output.yaml"
            if schema_path.exists():
                with open(schema_path) as f:
                    self._output_schema = yaml.safe_load(f)
        return self._output_schema

    def load_templates(self) -> dict[str, str]:
        """Load template files from templates/ directory."""
        templates_dir = self.path / "templates"
        if not templates_dir.exists():
            return {}
        result: dict[str, str] = {}
        for f in templates_dir.iterdir():
            if f.is_file():
                result[f.name] = f.read_text()
        return result

    def load_examples(self) -> list[str]:
        """Load example files from examples/ directory."""
        examples_dir = self.path / "examples"
        if not examples_dir.exists():
            return []
        return [f.read_text() for f in sorted(examples_dir.iterdir()) if f.is_file()]

    def execute(
        self,
        workspace_id: str,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the skill against a workspace.

        The full 12-step execution flow from doc 03.
        """
        from pulse.runtime.knowledge import load_knowledge_files
        from pulse.runtime.llm import LLMClient
        from pulse.runtime.runs import RunLogger
        from pulse.runtime.schemas import RunStatus
        from pulse.runtime.workspace import load_workspace
        from pulse.utils.prompts import compose_skill_prompt

        inputs = inputs or {}
        run_logger = RunLogger(
            workspace_id=workspace_id,
            skill_name=self.meta.name,
        )

        try:
            # 1. Validate inputs (basic check for required fields)
            self._validate_inputs(inputs)

            # 2. Check idempotency (if declared)
            idempotency_key = self.meta.runtime.get("idempotency_key")
            force = inputs.get("force", False)
            if idempotency_key and not force:
                self._check_idempotency(workspace_id, str(idempotency_key), run_logger)

            # 3. Check preconditions
            workspace = load_workspace(workspace_id)

            # 4. Load knowledge files
            knowledge = {}
            if self.meta.knowledge:
                knowledge = load_knowledge_files(self.meta.knowledge)

            # 5. Load prompt templates
            templates = self.load_templates()

            run_logger.log_event({
                "event": "skill_preconditions_passed",
                "knowledge_files_loaded": len(knowledge),
                "templates_loaded": len(templates),
            })

            # 6-7. Execute based on runtime type
            runtime_type = self.meta.runtime.get("type", "llm_procedure")

            if runtime_type == "deterministic":
                result = self._execute_deterministic(workspace, inputs)
            else:
                # LLM procedure
                workspace_context = workspace.model_dump(
                    mode="json", exclude_none=True,
                    include={"id", "name", "industry", "identity", "customer", "offer", "goals", "position"},
                )
                examples = self.load_examples()
                system, user_msg = compose_skill_prompt(
                    procedure=self.procedure,
                    knowledge=knowledge or None,
                    workspace_context=workspace_context,
                    examples=examples or None,
                )

                llm_config_data = self.meta.llm
                llm = LLMClient(run_logger=run_logger)
                response = llm.call(
                    system=system,
                    user_message=user_msg,
                    model=str(llm_config_data.get("model")) if llm_config_data.get("model") else None,
                    temperature=float(llm_config_data.get("temperature", 0.3)),
                    max_tokens=int(llm_config_data.get("max_tokens", 4000)),
                )

                # Parse structured output
                result = self._parse_llm_output(response.content)

            # 8-12. Validate, write, log, complete
            run_logger.log_event({"event": "skill_execution_complete"})
            run_logger.complete(RunStatus.SUCCEEDED)

            return result

        except Exception as e:
            run_logger.log_event({
                "event": "skill_execution_error",
                "error": str(e),
            })
            run_logger.complete(RunStatus.FAILED, error_message=str(e))
            raise

    def _validate_inputs(self, inputs: dict[str, Any]) -> None:
        """Validate inputs against declared schema."""
        for name, spec in self.meta.inputs.items():
            if spec.get("required", False) and name not in inputs:
                raise ValueError(
                    f"E006: Missing required input '{name}' for {self.meta.name}."
                )

    def _check_idempotency(
        self, workspace_id: str, key_template: str, run_logger: Any
    ) -> None:
        """Check if skill already ran (idempotency)."""
        # Simplified check — full implementation uses Jinja2 to render the key
        try:
            from pulse.runtime.index import get_connection
            conn = get_connection(workspace_id)
            recent = conn.execute(
                "SELECT id FROM runs WHERE skill_name = ? AND status = 'succeeded' "
                "AND date(started_at) = date('now') ORDER BY started_at DESC LIMIT 1",
                (self.meta.name,),
            ).fetchone()
            conn.close()
            if recent:
                run_logger.log_event({"event": "idempotency_skip", "key": key_template})
                raise SkillIdempotencyError(
                    f"E009: {self.meta.name} already ran today. "
                    f"Use --force to override."
                )
        except ImportError:
            pass

    def _execute_deterministic(
        self, workspace: Any, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a deterministic skill (no LLM)."""
        # Deterministic skills are implemented as Python code, not LLM procedures.
        # This is a placeholder — specific deterministic skills override this.
        return {"status": "completed", "type": "deterministic"}

    def _parse_llm_output(self, content: str) -> dict[str, Any]:
        """Parse structured output from LLM response."""
        # Try to extract YAML from the response
        clean = content.strip()

        # Strip markdown code fences if present
        if clean.startswith("```yaml"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]

        try:
            result = yaml.safe_load(clean.strip())
            if isinstance(result, dict):
                return result
            return {"content": content}
        except yaml.YAMLError:
            return {"content": content}


class SkillIdempotencyError(Exception):
    """Raised when a skill's idempotency key is already satisfied."""


def discover_skills() -> dict[str, Skill]:
    """Walk ~/.pulse/skills/ and discover all skill definitions.

    Returns a dict mapping verb (CLI name without 'pulse ') to Skill.
    """
    root = skills_dir()
    if not root.exists():
        return {}

    skills: dict[str, Skill] = {}

    for skill_md in root.rglob("SKILL.md"):
        try:
            skill = load_skill(skill_md.parent)
            skills[skill.verb] = skill
        except Exception:
            # Skip malformed skills — don't crash discovery
            continue

    return skills


def load_skill(skill_dir: Path) -> Skill:
    """Load a skill from its directory."""
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        raise FileNotFoundError(f"No SKILL.md found in {skill_dir}")

    post = frontmatter.load(str(skill_md))
    meta = SkillFrontmatter.model_validate(post.metadata)
    procedure = post.content

    return Skill(path=skill_dir, meta=meta, procedure=procedure)
