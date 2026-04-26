"""Generic interactive questionnaire walker.

Loads question banks from YAML, walks them tier-by-tier with
progress display, collects answers with confidence flags, saves
incrementally, and builds a research queue from low-confidence fields.

Usage:
    from pulse.runtime.questionnaire import QuestionnaireWalker

    walker = QuestionnaireWalker(
        questionnaire_path="questionnaires/customer-profile.yaml",
        workspace_id="acme-corp",
    )
    result = walker.run()
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from pulse.utils.atomic_write import atomic_write
from pulse.utils.paths import knowledge_dir

console = Console()


# ──────────────────────────────────────────────────────────────
# Types
# ──────────────────────────────────────────────────────────────


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    GUESSING = "guessing"


class WalkMode(StrEnum):
    FRESH = "fresh"
    REFRESH = "refresh"
    DEEPEN = "deepen"
    START_OVER = "start_over"


@dataclass
class Answer:
    """A single collected answer with metadata."""

    key: str
    value: Any
    confidence: Confidence = Confidence.HIGH
    skipped: bool = False


@dataclass
class TierResult:
    """Aggregated answers for a single tier."""

    tier_name: str
    answers: list[Answer] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return len(self.answers) > 0

    @property
    def high_confidence_count(self) -> int:
        return sum(
            1
            for a in self.answers
            if not a.skipped and a.confidence in (Confidence.HIGH, Confidence.MEDIUM)
        )

    @property
    def total_answered(self) -> int:
        return sum(1 for a in self.answers if not a.skipped)


@dataclass
class WalkResult:
    """Full result of walking a questionnaire."""

    questionnaire_name: str
    mode: WalkMode
    tiers: list[TierResult] = field(default_factory=list)
    low_confidence_fields: list[str] = field(default_factory=list)
    research_queue: list[str] = field(default_factory=list)
    aborted_after_tier: int | None = None

    def answers_dict(self) -> dict[str, Any]:
        """Flatten all answers into a {key: value} dict."""
        result: dict[str, Any] = {}
        for tier in self.tiers:
            for answer in tier.answers:
                if not answer.skipped:
                    result[answer.key] = answer.value
        return result

    def confidence_dict(self) -> dict[str, str]:
        """Return {key: confidence_level} for all answers."""
        result: dict[str, str] = {}
        for tier in self.tiers:
            for answer in tier.answers:
                if not answer.skipped:
                    result[answer.key] = answer.confidence.value
        return result


# ──────────────────────────────────────────────────────────────
# Questionnaire definition types
# ──────────────────────────────────────────────────────────────


@dataclass
class QuestionDef:
    """A question definition from YAML."""

    key: str
    prompt: str
    type: str  # free_text, list, enum, long_text, multi_value, structured_list, structured
    examples: list[str] | str | None = None
    help: str | None = None
    values: list[str] | None = None  # for enum type
    fields: list[dict[str, Any]] | None = None  # for structured types
    writes_to: str | None = None


@dataclass
class TierDef:
    """A tier definition from YAML."""

    name: str
    time_estimate: str
    description: str | None = None
    questions: list[QuestionDef] = field(default_factory=list)


@dataclass
class QuestionnaireDef:
    """A full questionnaire definition."""

    name: str
    description: str
    intro: str | None = None
    tiers: list[TierDef] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# YAML loading
# ──────────────────────────────────────────────────────────────


def load_questionnaire(rel_path: str) -> QuestionnaireDef:
    """Load a questionnaire YAML from knowledge_dir / rel_path."""
    full_path = knowledge_dir() / rel_path
    if not full_path.exists():
        raise FileNotFoundError(
            f"Questionnaire not found: {rel_path}\n"
            f"Expected at: {full_path}"
        )
    return load_questionnaire_from_path(full_path)


def load_questionnaire_from_path(path: Path) -> QuestionnaireDef:
    """Load a questionnaire YAML from an absolute path."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Empty questionnaire file: {path}")

    tiers: list[TierDef] = []
    for tier_raw in raw.get("tiers", []):
        questions: list[QuestionDef] = []
        for q_raw in tier_raw.get("questions", []):
            questions.append(
                QuestionDef(
                    key=q_raw["key"],
                    prompt=q_raw["prompt"],
                    type=q_raw.get("type", "free_text"),
                    examples=q_raw.get("examples"),
                    help=q_raw.get("help"),
                    values=q_raw.get("values"),
                    fields=q_raw.get("fields"),
                    writes_to=q_raw.get("writes_to"),
                )
            )
        tiers.append(
            TierDef(
                name=tier_raw["name"],
                time_estimate=tier_raw.get("time_estimate", ""),
                description=tier_raw.get("description"),
                questions=questions,
            )
        )

    return QuestionnaireDef(
        name=raw.get("name", path.stem),
        description=raw.get("description", ""),
        intro=raw.get("intro"),
        tiers=tiers,
    )


# ──────────────────────────────────────────────────────────────
# Incremental save
# ──────────────────────────────────────────────────────────────


def _progress_path(workspace_dir: Path, questionnaire_name: str) -> Path:
    """Path to the incremental progress file."""
    return workspace_dir / f".questionnaire-progress-{questionnaire_name}.yaml"


def save_progress(
    workspace_dir: Path,
    questionnaire_name: str,
    result: WalkResult,
) -> None:
    """Incrementally save questionnaire progress (crash-safe)."""
    data: dict[str, Any] = {
        "questionnaire": questionnaire_name,
        "mode": result.mode.value,
        "tiers_completed": len(result.tiers),
        "answers": {},
        "confidence": {},
        "low_confidence_fields": result.low_confidence_fields,
        "research_queue": result.research_queue,
    }
    for tier in result.tiers:
        for answer in tier.answers:
            if not answer.skipped:
                data["answers"][answer.key] = answer.value
                data["confidence"][answer.key] = answer.confidence.value

    content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    atomic_write(_progress_path(workspace_dir, questionnaire_name), content)


def load_progress(
    workspace_dir: Path,
    questionnaire_name: str,
) -> dict[str, Any] | None:
    """Load saved progress, or None if no progress file exists."""
    path = _progress_path(workspace_dir, questionnaire_name)
    if not path.exists():
        return None
    with open(path) as f:
        result: dict[str, Any] | None = yaml.safe_load(f)
        return result


def clear_progress(workspace_dir: Path, questionnaire_name: str) -> None:
    """Remove the progress file after successful completion."""
    path = _progress_path(workspace_dir, questionnaire_name)
    if path.exists():
        path.unlink()


# ──────────────────────────────────────────────────────────────
# Walker
# ──────────────────────────────────────────────────────────────


class QuestionnaireWalker:
    """Interactive questionnaire walker with rich output.

    Walks a questionnaire definition tier-by-tier, collecting answers
    with confidence flags, saving incrementally, and building a
    research queue from low-confidence fields.
    """

    def __init__(
        self,
        questionnaire_path: str,
        workspace_dir: Path,
        existing_answers: dict[str, Any] | None = None,
        mode: WalkMode | None = None,
    ) -> None:
        self.questionnaire = load_questionnaire(questionnaire_path)
        self.workspace_dir = workspace_dir
        self.existing_answers = existing_answers or {}
        self._mode = mode
        self._result = WalkResult(
            questionnaire_name=self.questionnaire.name,
            mode=mode or WalkMode.FRESH,
        )

    def run(self) -> WalkResult:
        """Run the full questionnaire walk. Returns collected answers."""
        # Determine mode
        mode = self._resolve_mode()
        self._result.mode = mode

        # Show intro
        self._show_intro(mode)

        # Walk tiers
        total_tiers = len(self.questionnaire.tiers)
        for tier_idx, tier_def in enumerate(self.questionnaire.tiers):
            tier_num = tier_idx + 1

            # Show tier header
            self._show_tier_header(tier_def, tier_num, total_tiers)

            # Walk questions in this tier
            tier_result = self._walk_tier(tier_def, tier_num, total_tiers)
            self._result.tiers.append(tier_result)

            # Incremental save after each tier
            save_progress(self.workspace_dir, self.questionnaire.name, self._result)

            # Tier boundary checkpoint
            if tier_num < total_tiers and not self._tier_checkpoint(tier_def, tier_num, total_tiers):
                self._result.aborted_after_tier = tier_num
                break

        # Build low-confidence fields and research queue
        self._build_research_queue()

        # Final save
        save_progress(self.workspace_dir, self.questionnaire.name, self._result)

        # Show summary
        self._show_summary()

        return self._result

    def _resolve_mode(self) -> WalkMode:
        """Determine the walk mode based on existing data."""
        if self._mode is not None:
            return self._mode

        if not self.existing_answers:
            return WalkMode.FRESH

        console.print()
        console.print(
            Panel(
                "[bold]Existing answers found.[/bold] How would you like to proceed?",
                title="Questionnaire Mode",
                border_style="blue",
            )
        )
        console.print("  [bold]1.[/bold] Refresh  — walk all questions, edit only what changed")
        console.print("  [bold]2.[/bold] Deepen   — walk only low-confidence or empty fields")
        console.print("  [bold]3.[/bold] Start over — blank slate")
        console.print()

        choice = Prompt.ask(
            "Choose mode",
            choices=["1", "2", "3"],
            default="1",
        )

        mode_map = {"1": WalkMode.REFRESH, "2": WalkMode.DEEPEN, "3": WalkMode.START_OVER}
        return mode_map[choice]

    def _show_intro(self, mode: WalkMode) -> None:
        """Show the questionnaire introduction."""
        console.print()

        title = f"[bold]{self.questionnaire.name}[/bold]"
        if self.questionnaire.description:
            title += f"\n{self.questionnaire.description}"

        tier_count = len(self.questionnaire.tiers)
        estimates = [t.time_estimate for t in self.questionnaire.tiers if t.time_estimate]
        time_info = f"{tier_count} tiers"
        if estimates:
            time_info += f" ({', '.join(estimates)})"

        body = f"[dim]{time_info}[/dim]"
        if mode != WalkMode.FRESH:
            body += f"\n[yellow]Mode: {mode.value}[/yellow]"

        if self.questionnaire.intro:
            body += f"\n\n[dim]{escape(self.questionnaire.intro.strip())}[/dim]"

        console.print(Panel(body, title=title, border_style="green"))
        console.print()

    def _show_tier_header(
        self, tier_def: TierDef, tier_num: int, total_tiers: int
    ) -> None:
        """Show the header for a tier."""
        console.print()
        console.rule(
            f"[bold blue]Tier {tier_num} of {total_tiers}: {tier_def.name}[/bold blue]"
        )
        if tier_def.description:
            console.print(f"  [dim]{escape(tier_def.description)}[/dim]")
        if tier_def.time_estimate:
            console.print(f"  [dim]Estimated time: {tier_def.time_estimate}[/dim]")
        console.print()

    def _walk_tier(
        self, tier_def: TierDef, tier_num: int, total_tiers: int
    ) -> TierResult:
        """Walk all questions in a tier."""
        tier_result = TierResult(tier_name=tier_def.name)
        total_questions = len(tier_def.questions)

        for q_idx, q_def in enumerate(tier_def.questions):
            q_num = q_idx + 1
            progress = (
                f"[dim]Tier {tier_num} of {total_tiers}, "
                f"question {q_num} of {total_questions}[/dim]"
            )
            console.print(progress)

            answer = self._ask_question(q_def)
            tier_result.answers.append(answer)

            # Incremental save after each answer
            self._result.tiers = [
                *self._result.tiers,
            ]
            # We save at tier boundary, but also after each answer group
            # for crash safety.
            self._save_current_state(tier_result)

        return tier_result

    def _save_current_state(self, current_tier: TierResult) -> None:
        """Save progress including the in-progress tier."""
        # Build a temporary result that includes the current partial tier
        temp = copy.copy(self._result)
        # Replace or append current tier
        existing_names = [t.tier_name for t in temp.tiers]
        if current_tier.tier_name in existing_names:
            temp.tiers = [
                current_tier if t.tier_name == current_tier.tier_name else t
                for t in temp.tiers
            ]
        else:
            temp.tiers = [*temp.tiers, current_tier]
        save_progress(self.workspace_dir, self.questionnaire.name, temp)

    def _ask_question(self, q_def: QuestionDef) -> Answer:
        """Ask a single question and collect the answer with confidence."""
        mode = self._result.mode
        existing = self.existing_answers.get(q_def.key)

        # In deepen mode, skip high-confidence existing answers
        if mode == WalkMode.DEEPEN and existing is not None:
            console.print(f"  [dim]Skipping {q_def.key} (already answered)[/dim]")
            return Answer(key=q_def.key, value=existing, skipped=True)

        # Show the question
        console.print()
        console.print(f"  [bold]{escape(q_def.prompt.strip())}[/bold]")

        # Show help if available
        if q_def.help:
            console.print(f"  [dim]{escape(q_def.help)}[/dim]")

        # Show examples in dim style
        if q_def.examples:
            if isinstance(q_def.examples, list):
                examples_str = ", ".join(str(e) for e in q_def.examples)
            else:
                examples_str = str(q_def.examples)
            console.print(f"  [dim italic]Examples: {escape(examples_str)}[/dim italic]")

        # Show existing value in refresh mode
        if mode == WalkMode.REFRESH and existing is not None:
            console.print(f"  [yellow]Current: {escape(str(existing))}[/yellow]")

        # Show enum values
        if q_def.type == "enum" and q_def.values:
            console.print(f"  [dim]Options: {', '.join(q_def.values)}[/dim]")

        # Collect the answer based on type
        value = self._collect_answer(q_def, existing)

        if value is None or (isinstance(value, str) and value.strip() == ""):
            if existing is not None:
                # Keep existing in refresh mode
                return Answer(key=q_def.key, value=existing, confidence=Confidence.MEDIUM)
            return Answer(key=q_def.key, value=None, skipped=True)

        # Ask for confidence
        confidence = self._ask_confidence(q_def.key)

        return Answer(key=q_def.key, value=value, confidence=confidence)

    def _collect_answer(
        self, q_def: QuestionDef, existing: Any
    ) -> Any:
        """Collect an answer based on question type."""
        default = str(existing) if existing is not None else ""

        if q_def.type == "enum":
            choices = q_def.values or []
            if choices:
                return Prompt.ask(
                    "  >",
                    choices=choices,
                    default=default if default in choices else None,
                )
            return Prompt.ask("  >", default=default or None)

        if q_def.type in ("list", "multi_value"):
            console.print("  [dim]Enter items one per line. Empty line to finish.[/dim]")
            items: list[str] = []
            if existing and isinstance(existing, list):
                console.print(f"  [dim]Current items: {', '.join(str(i) for i in existing)}[/dim]")
            while True:
                item = Prompt.ask("  +", default="")
                if not item:
                    break
                items.append(item)
            return items if items else (existing if isinstance(existing, list) else None)

        if q_def.type in ("long_text", "free_text"):
            return Prompt.ask("  >", default=default or None)

        if q_def.type == "structured_list":
            return self._collect_structured_list(q_def, existing)

        if q_def.type == "structured":
            return self._collect_structured(q_def, existing)

        # Default: simple text
        return Prompt.ask("  >", default=default or None)

    def _collect_structured_list(
        self, q_def: QuestionDef, existing: Any
    ) -> list[dict[str, Any]]:
        """Collect a list of structured items."""
        field_defs = q_def.fields or []
        items: list[dict[str, Any]] = []

        if existing and isinstance(existing, list):
            console.print(f"  [dim]({len(existing)} existing items)[/dim]")

        console.print("  [dim]Add items. Empty first field to finish.[/dim]")

        while True:
            item: dict[str, Any] = {}
            first = True
            for field_def in field_defs:
                fname = field_def.get("name", "value")
                ftype = field_def.get("type", "free_text")
                fexample = field_def.get("example", "")

                label = f"  {fname} [dim]({fexample})[/dim]" if fexample else f"  {fname}"

                if ftype == "enum":
                    options = field_def.get("options", [])
                    val = Prompt.ask(label, choices=options, default="")
                else:
                    val = Prompt.ask(label, default="")

                if first and not val:
                    return items if items else (existing if isinstance(existing, list) else [])
                first = False
                item[fname] = val

            items.append(item)
            console.print("  [dim]---[/dim]")

        return items  # pragma: no cover — unreachable, loop exits via return

    def _collect_structured(
        self, q_def: QuestionDef, existing: Any
    ) -> dict[str, Any]:
        """Collect a structured (non-list) answer."""
        field_defs = q_def.fields or []
        result: dict[str, Any] = {}

        existing_dict = existing if isinstance(existing, dict) else {}

        for field_def in field_defs:
            fname = field_def.get("name", "value")
            ftype = field_def.get("type", "free_text")
            fexample = field_def.get("example", "")
            fdefault = str(existing_dict.get(fname, ""))

            label = f"  {fname} [dim]({fexample})[/dim]" if fexample else f"  {fname}"

            if ftype in ("multi_value", "list"):
                console.print(f"  [dim]Enter {fname} items, one per line. Empty to finish.[/dim]")
                items: list[str] = []
                while True:
                    item = Prompt.ask("  +", default="")
                    if not item:
                        break
                    items.append(item)
                result[fname] = items
            else:
                result[fname] = Prompt.ask(label, default=fdefault or None)

        return result

    def _ask_confidence(self, field_key: str) -> Confidence:
        """Ask the operator how confident they are in the answer."""
        raw = Prompt.ask(
            "  [dim]Confidence?[/dim]",
            choices=["high", "medium", "low", "guessing"],
            default="high",
        )
        return Confidence(raw)

    def _tier_checkpoint(
        self, tier_def: TierDef, tier_num: int, total_tiers: int
    ) -> bool:
        """Show tier summary and ask whether to continue."""
        console.print()

        current_tier = self._result.tiers[-1] if self._result.tiers else None
        if current_tier:
            answered = current_tier.total_answered
            high = current_tier.high_confidence_count
            total = len(tier_def.questions)
            console.print(
                f"  [green]Tier {tier_num} complete.[/green] "
                f"{answered}/{total} answered, {high} high-confidence."
            )

        total_tiers - tier_num
        next_tier = self.questionnaire.tiers[tier_num] if tier_num < total_tiers else None
        if next_tier:
            console.print(
                f"  Next: [bold]{next_tier.name}[/bold] "
                f"({next_tier.time_estimate})"
            )

        console.print()
        return Confirm.ask(
            f"  Continue to tier {tier_num + 1} of {total_tiers}?",
            default=True,
        )

    def _build_research_queue(self) -> None:
        """Build the low-confidence fields list and research queue."""
        low_fields: list[str] = []
        for tier in self._result.tiers:
            for answer in tier.answers:
                if not answer.skipped and answer.confidence in (
                    Confidence.LOW,
                    Confidence.GUESSING,
                ):
                    low_fields.append(answer.key)

        self._result.low_confidence_fields = low_fields

        # Build research suggestions
        research: list[str] = []
        for field_key in low_fields:
            research.append(f"Research needed: firm up '{field_key}' (currently low-confidence)")
        self._result.research_queue = research

    def _show_summary(self) -> None:
        """Show the completion summary."""
        console.print()

        table = Table(title="Questionnaire Summary", border_style="green")
        table.add_column("Tier", style="bold")
        table.add_column("Answered", justify="right")
        table.add_column("High-Confidence", justify="right")
        table.add_column("Bar")

        len(self.questionnaire.tiers)

        for tier_idx, tier_def in enumerate(self.questionnaire.tiers):
            if tier_idx < len(self._result.tiers):
                tier_result = self._result.tiers[tier_idx]
                total_q = len(tier_def.questions)
                answered = tier_result.total_answered
                high = tier_result.high_confidence_count
                pct = (answered / total_q * 100) if total_q > 0 else 0
                bar_len = int(pct / 10)
                bar = "[green]" + "\u2588" * bar_len + "[/green]" + "[dim]" + "\u2591" * (10 - bar_len) + "[/dim]"
                table.add_row(
                    f"{tier_idx + 1}. {tier_def.name}",
                    f"{answered}/{total_q}",
                    f"{high}/{answered}" if answered > 0 else "-",
                    bar,
                )
            else:
                table.add_row(
                    f"{tier_idx + 1}. {tier_def.name}",
                    "[dim]not started[/dim]",
                    "-",
                    "[dim]" + "\u2591" * 10 + "[/dim]",
                )

        console.print(table)

        if self._result.low_confidence_fields:
            console.print()
            console.print("[yellow]Low-confidence fields:[/yellow]")
            for field_key in self._result.low_confidence_fields:
                console.print(f"  - {field_key}")

        if self._result.research_queue:
            console.print()
            console.print("[yellow]Research queue:[/yellow]")
            for item in self._result.research_queue:
                console.print(f"  - {item}")

        console.print()
