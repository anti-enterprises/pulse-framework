#!/usr/bin/env python3
"""Generate Claude Code skills from the Pulse manifest and default_assets.

Reads the command manifest and SKILL.md / playbook YAML files, then writes
Claude Code-compatible skills to .claude/skills/pulse-<verb>/SKILL.md.

Usage:
    python scripts/generate_agent_skills.py          # generate all
    python scripts/generate_agent_skills.py --clean   # remove generated, then regenerate
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pulse.manifest import MANIFEST  # noqa: E402

SKILLS_OUT = ROOT / ".claude" / "skills"
ASSETS = ROOT / "default_assets"

# ── Description templates keyed by command name ──────────────────────────

DESCRIPTIONS: dict[str, str] = {
    # Meta
    "init": (
        "Use when setting up the Pulse framework for the first time or when "
        "~/.pulse/ does not exist. Creates directory structure and copies default assets."
    ),
    "workspace-new": (
        "Use when creating a new client or project workspace in Pulse. "
        "Sets up the workspace directory at ~/.pulse/workspaces/<id>/."
    ),
    "workspace-list": "Use when checking what Pulse workspaces exist.",
    "workspace-switch": "Use when changing the active Pulse workspace.",
    "workspace-status": (
        "Use when checking the state of a Pulse workspace — position, sources, "
        "hypotheses, recent runs. Run this before any operational command."
    ),
    "workspace-archive": "Use when archiving a completed or inactive Pulse workspace.",
    "reindex": (
        "Use when the Pulse SQLite index is out of sync with filesystem state. "
        "Rebuilds .index.sqlite from workspace files."
    ),
    "refine": "Use when adding a refinement note to an existing Pulse skill procedure.",
    "evolve": "Use when proposing updates to a Pulse skill from accumulated refinement notes.",
    "evolve-all": "Use when evolving all skills that have pending refinement notes at once.",
    "refine-from-runs": (
        "Use when analyzing recent run history to discover refinement opportunities. "
        "LLM-scans run logs and proposes actionable refinement notes interactively."
    ),
    "import-refinements": (
        "Use when bulk-importing refinement notes from a YAML file. "
        "Follows the same pattern as source upload — one file, multiple skills."
    ),
    "refine-router": "Use when adding a refinement note to the Pulse interactive router decision tree.",
    "help": "Use when listing available Pulse commands or getting help on a specific command.",
    # Kickoff
    "onboard": (
        "Use when onboarding a new client or starting a new business intelligence engagement. "
        "Full kickoff playbook (~60 min): identity, customer profiling, offer, goals, positioning, "
        "ecosystem mapping, and source typing."
    ),
    "reposition": (
        "Use when rebuilding a workspace's positioning from scratch after a strategic pivot. "
        "Re-walks each kickoff skill, surfacing what changed (~45 min)."
    ),
    "set-identity": (
        "Use when defining or updating a workspace's identity block — "
        "the declared business vs. the real business."
    ),
    "profile-customer": (
        "Use when building a deep customer profile. Walks a 4-tier questionnaire covering "
        "demographics, psychographics, behavior, and buying patterns (~30 min)."
    ),
    "articulate-offer": (
        "Use when defining or refining the workspace's offer — "
        "promise, mechanism, pricing, and proof."
    ),
    "set-goals": (
        "Use when setting or updating workspace goals — "
        "primary, secondary, bets, and constraints."
    ),
    "set-position": (
        "Use when defining the workspace's strategic position — "
        "4x2 matrix and intention statement."
    ),
    "set-refinement-criteria": (
        "Use when defining refinement criteria during onboarding — "
        "what to watch for when skills execute (performance, quality, coverage, freshness)."
    ),
    # Knowledge
    "author-knowledge": "Use when creating a new knowledge file for the Pulse framework.",
    "refine-knowledge": "Use when adding refinement notes to existing Pulse knowledge files.",
    "evolve-knowledge": "Use when evolving Pulse knowledge files from accumulated refinement notes.",
    "knowledge-status": (
        "Use when checking the status of the Pulse knowledge layer — "
        "file counts, freshness, coverage."
    ),
    # Corpus
    "ingest": "Use when adding files to the Pulse RAG corpus for semantic search and retrieval.",
    "corpus-query": "Use when searching the Pulse corpus for relevant documents or passages.",
    "corpus-status": "Use when checking the Pulse corpus status — document count, index health, storage.",
    "enable-corpus": "Use when enabling the optional Pulse RAG corpus infrastructure (LanceDB + embeddings).",
    "disable-corpus": "Use when disabling the Pulse corpus infrastructure.",
    # Discovery
    "map-ecosystem": (
        "Use when mapping the competitive ecosystem using the Hormozi framework — "
        "players, substitutes, and market dynamics."
    ),
    "map-trust-network": (
        "Use when profiling the trust network using the Abraham framework — "
        "referral partners, strategic alliances, and influence paths."
    ),
    "scan-acquisitions": (
        "Use when scanning acquisition opportunities using the Frasier acquisition wheel."
    ),
    "type-sources": (
        "Use when assigning strategic intelligence roles to URLs — "
        "categorizing sources by monitoring value."
    ),
    "add-source": "Use when manually adding a single intelligence source to the workspace.",
    # Listen
    "extract": (
        "Use when extracting intelligence atoms from curated sources. "
        "Reads sources.yaml, fetches content, produces structured observation atoms. "
        "Part of the weekly cadence."
    ),
    "daily-extract": (
        "Use when running a lightweight daily atom extraction. "
        "Single LLM call per source, claims and stats only, 24h window. "
        "Part of the daily cadence."
    ),
    "mine-reviews": (
        "Use when mining customer review aggregators for intelligence atoms — "
        "patterns from reviews, ratings, and feedback."
    ),
    "scan-ads": (
        "Use when scanning ad libraries for competitive intelligence — "
        "ad copy, targeting, and creative patterns."
    ),
    # Synthesis
    "propose-hypothesis": (
        "Use when clustering unexplained atoms into patterns and proposing scored hypotheses. "
        "Identifies emerging themes from collected intelligence."
    ),
    "score-signals": (
        "Use when scoring intelligence atoms against active hypotheses — "
        "measuring evidence strength and updating confidence."
    ),
    "update-directions": (
        "Use when recomputing strategic direction momentum based on "
        "recent signals and hypothesis changes."
    ),
    "find-commodity-pattern": (
        "Use when detecting commodity patterns using the Hormozi framework — "
        "identifying where the market is commoditizing."
    ),
    "find-gaps": (
        "Use when running gap-map synthesis to identify underserved market "
        "segments or unmet needs."
    ),
    # Action
    "write-brief": (
        "Use when generating content briefs from intelligence analysis — "
        "turning hypotheses and signals into actionable content plans."
    ),
    "write-positioning": (
        "Use when drafting a positioning statement — synthesizing identity, "
        "customer, offer, and market data into a positioning document."
    ),
    "draft-survey": (
        "Use when generating a JTBD (Jobs-to-be-Done) survey for customer "
        "research and validation."
    ),
    "draft-outreach": (
        "Use when generating outreach sequences — personalized messaging "
        "based on workspace intelligence and customer profiles."
    ),
    # Reflect
    "audit-drift": (
        "Use when analyzing position drift — measuring how actual activities "
        "diverge from declared positioning over time."
    ),
    "postmortem": (
        "Use when running a hypothesis postmortem — what was predicted, "
        "what happened, and what was learned."
    ),
    "connect-source": "Use when registering an external intelligence source for ongoing monitoring.",
    # Playbooks
    "daily": (
        "Use when running the daily source scan (~3 min). "
        "Lightweight extraction of high-signal atoms and direction linking. "
        "Alias: pulse d."
    ),
    "weekly": (
        "Use when running the weekly intelligence pass (~10 min). "
        "Extracts atoms, scores signals, updates directions, writes digest. "
        "Aliases: pulse intel, pulse w."
    ),
    "monthly": (
        "Use when running the monthly synthesis (~25 min). Weekly pass plus "
        "commodity pattern detection, gap mapping, and monthly digest."
    ),
    "quarterly": (
        "Use when running the quarterly review (~60 min). Monthly pass plus "
        "drift audit, postmortems, ecosystem refresh, and quarterly brief."
    ),
}

# ── Layer display names ──────────────────────────────────────────────────

LAYER_LABELS: dict[str, str] = {
    "meta": "Meta",
    "kickoff": "Kickoff",
    "knowledge": "Knowledge",
    "corpus": "Corpus",
    "discovery": "Discovery",
    "listen": "Listen",
    "synthesis": "Synthesis",
    "action": "Action",
    "reflect": "Reflect",
    "playbook": "Playbook",
    "operational": "Playbook",
    "": "—",
}


# ── Helpers ──────────────────────────────────────────────────────────────


def parse_skill_md(path: Path) -> tuple[dict, str]:
    """Parse a SKILL.md into (frontmatter_dict, procedure_body)."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return fm, body


def find_skill_md(name: str, layer: str) -> Path | None:
    """Locate the default_assets SKILL.md for a command."""
    candidates = [
        ASSETS / "skills" / layer / name / "SKILL.md",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback: search all layer dirs
    for layer_dir in (ASSETS / "skills").iterdir():
        if not layer_dir.is_dir():
            continue
        p = layer_dir / name / "SKILL.md"
        if p.exists():
            return p
    return None


def find_playbook_yaml(name: str) -> Path | None:
    """Locate the playbook YAML for a command."""
    p = ASSETS / "playbooks" / f"{name}.yaml"
    return p if p.exists() else None


def format_playbook_steps(pb: dict) -> str:
    """Format playbook steps into readable markdown."""
    steps = pb.get("steps", [])
    lines = []
    for i, step in enumerate(steps, 1):
        if "skill" in step:
            skill_name = step["skill"].replace("pulse ", "")
            params = step.get("with", {})
            on_fail = step.get("on_failure", "halt")
            line = f"{i}. **{step.get('id', skill_name)}** — `pulse {skill_name}`"
            if params:
                # Strip Jinja2 template expressions, show resolved or simplified values
                cleaned = {}
                for k, v in params.items():
                    sv = str(v)
                    if "{{" in sv:
                        # Replace Jinja2 expression with a placeholder
                        sv = sv.replace("{{ defaults.mode }}", "interactive")
                        sv = sv.strip("{} ").strip()
                    cleaned[k] = sv
                param_str = ", ".join(f"{k}={v}" for k, v in cleaned.items())
                line += f" ({param_str})"
            if on_fail != "halt":
                line += f" [on failure: {on_fail}]"
            lines.append(line)
        elif "checkpoint" in step:
            cp = step["checkpoint"]
            lines.append(f"{i}. **checkpoint** — {cp.get('prompt', 'Pause for review')}")
        elif "include" in step:
            lines.append(f"{i}. **include** — runs the `pulse {step['include']}` playbook")
    return "\n".join(lines)


def format_inputs(inputs: dict) -> str:
    """Format skill inputs as a markdown table."""
    if not inputs:
        return ""
    lines = ["| Parameter | Type | Required | Description |", "|-----------|------|----------|-------------|"]
    for name, spec in inputs.items():
        typ = spec.get("type", "string")
        req = "yes" if spec.get("required", False) else "no"
        desc = spec.get("description", "")
        default = spec.get("default")
        if default is not None:
            desc += f" (default: `{default}`)"
        lines.append(f"| `{name}` | {typ} | {req} | {desc} |")
    return "\n".join(lines)


def format_outputs(outputs: dict) -> str:
    """Format skill outputs as a markdown list."""
    if not outputs:
        return ""
    lines = []
    for name, spec in outputs.items():
        desc = spec.get("description", "")
        lines.append(f"- **{name}** — {desc}")
    return "\n".join(lines)


# ── Generators ───────────────────────────────────────────────────────────


def generate_skill_type(entry, fm: dict, procedure: str) -> str:
    """Generate Claude Code SKILL.md for a skill-type command."""
    desc = DESCRIPTIONS.get(entry.name, f"Use when running pulse {entry.name}. {entry.description}")
    layer = LAYER_LABELS.get(entry.layer, entry.layer)
    cadence = fm.get("cadence", "ad_hoc")
    op_time = fm.get("operator_time", "varies")
    reads = fm.get("reads", [])
    writes = fm.get("writes", [])
    inputs = fm.get("inputs", {})
    outputs = fm.get("outputs", {})
    runtime_type = fm.get("runtime", {}).get("type", "llm_procedure")
    confirms = fm.get("runtime", {}).get("confirms_before_commit", False)

    sections = []

    # Header
    sections.append(f"# pulse {entry.name}\n")
    sections.append(f"{entry.description}\n")
    sections.append(f"**Layer:** {layer} | **Cadence:** {cadence} | **Time:** {op_time}")
    sections.append(f"**Runtime:** {runtime_type}" + (" | **Confirms before commit**" if confirms else ""))

    # Prerequisites
    prereqs = [
        "- Pulse framework installed (`pip install -e .` from pulse-skills-framework, or `pulse help` to verify)",
        "- Active workspace (`pulse workspace-status`)",
    ]
    if reads:
        prereqs.append(f"- Reads: {', '.join(f'`{r}`' for r in reads)}")
    sections.append("\n## Prerequisites\n")
    sections.append("\n".join(prereqs))

    # Quick run
    sections.append("\n## Quick Run\n")
    sections.append(f"```bash\npulse {entry.name}\n```")

    # Inputs
    if inputs:
        sections.append("\n## Inputs\n")
        sections.append(format_inputs(inputs))

    # Procedure
    if procedure:
        sections.append("\n## Procedure\n")
        # Strip the leading "# Procedure" header if present
        proc = procedure
        if proc.startswith("# Procedure"):
            proc = proc[len("# Procedure"):].strip()
        sections.append(proc)

    # Outputs
    if outputs:
        sections.append("\n## Outputs\n")
        sections.append(format_outputs(outputs))

    # Writes
    if writes:
        sections.append("\n## Files Written\n")
        for w in writes:
            sections.append(f"- `{w}`")

    body = "\n".join(sections)

    return (
        f"---\n"
        f"name: pulse:{entry.name}\n"
        f"description: \"{desc}\"\n"
        f"---\n\n"
        f"{body}\n"
    )


def generate_playbook_type(entry, pb: dict) -> str:
    """Generate Claude Code SKILL.md for a playbook-type command."""
    desc = DESCRIPTIONS.get(entry.name, f"Use when running pulse {entry.name}. {entry.description}")
    pb_desc = pb.get("description", entry.description).strip()
    op_time = pb.get("operator_time", "varies")
    aliases = pb.get("aliases", [])
    requires = pb.get("requires", {})
    steps_md = format_playbook_steps(pb)
    on_complete = pb.get("on_complete", {})
    on_failure = pb.get("on_failure", {})

    sections = []

    # Header
    sections.append(f"# pulse {entry.name}\n")
    sections.append(f"{pb_desc}\n")
    sections.append(f"**Time:** {op_time}")
    if aliases:
        sections.append(f"**Aliases:** {', '.join(f'`{a}`' for a in aliases)}")

    # Prerequisites
    sections.append("\n## Prerequisites\n")
    sections.append("- Pulse framework installed (`pulse help` to verify)")
    if requires.get("workspace_exists"):
        sections.append("- Active workspace (`pulse workspace-status`)")
    if requires.get("position_set"):
        sections.append("- Position must be set (run kickoff skills first)")
    if requires.get("sources_min"):
        sections.append(f"- At least {requires['sources_min']} source(s) configured")

    # Quick run
    sections.append("\n## Quick Run\n")
    sections.append(f"```bash\npulse {entry.name}\n```")

    # Steps
    sections.append("\n## Playbook Steps\n")
    sections.append(steps_md)

    # On complete
    if on_complete.get("message"):
        sections.append("\n## On Completion\n")
        sections.append(on_complete["message"].strip())

    # On failure
    if on_failure and on_failure.get("message"):
        sections.append("\n## On Failure\n")
        sections.append(on_failure["message"].strip())

    body = "\n".join(sections)

    return (
        f"---\n"
        f"name: pulse:{entry.name}\n"
        f"description: \"{desc}\"\n"
        f"---\n\n"
        f"{body}\n"
    )


def generate_builtin_type(entry) -> str:
    """Generate Claude Code SKILL.md for a builtin command."""
    desc = DESCRIPTIONS.get(entry.name, f"Use when running pulse {entry.name}. {entry.description}")

    sections = []
    sections.append(f"# pulse {entry.name}\n")
    sections.append(f"{entry.description}\n")
    sections.append(f"**Layer:** {LAYER_LABELS.get(entry.layer, entry.layer)} | **Type:** builtin")

    # Usage
    sections.append("\n## Usage\n")
    if entry.name in ("workspace-new", "workspace-switch", "workspace-archive"):
        sections.append(f"```bash\npulse {entry.name} <id>\n```")
    elif entry.name == "reindex":
        sections.append(f"```bash\npulse {entry.name} [id]\n```")
    elif entry.name == "refine":
        sections.append(f"```bash\npulse {entry.name} <skill> [note]\n```")
    elif entry.name == "evolve":
        sections.append(f"```bash\npulse {entry.name} <skill>\n```")
    elif entry.name == "refine-from-runs":
        sections.append(f"```bash\npulse {entry.name} [--days N] [--skill VERB]\n```")
    elif entry.name == "import-refinements":
        sections.append(f"```bash\npulse {entry.name} <file.yaml> [--dry-run]\n```")
    else:
        sections.append(f"```bash\npulse {entry.name}\n```")

    # Skill MD content if it exists
    skill_md = find_skill_md(entry.name, entry.layer)
    if skill_md:
        fm, procedure = parse_skill_md(skill_md)
        if procedure:
            proc = procedure
            if proc.startswith("# Procedure"):
                proc = proc[len("# Procedure"):].strip()
            sections.append("\n## Procedure\n")
            sections.append(proc)

    body = "\n".join(sections)

    return (
        f"---\n"
        f"name: pulse:{entry.name}\n"
        f"description: \"{desc}\"\n"
        f"---\n\n"
        f"{body}\n"
    )


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate Claude Code skills from Pulse manifest")
    parser.add_argument("--clean", action="store_true", help="Remove existing generated skills first")
    args = parser.parse_args()

    # Identify generated skill dirs (pulse-* but not the master pulse/)
    generated = [d for d in SKILLS_OUT.iterdir() if d.is_dir() and d.name.startswith("pulse-")] if SKILLS_OUT.exists() else []

    if args.clean and generated:
        print(f"Cleaning {len(generated)} existing pulse-* skill dirs...")
        for d in generated:
            shutil.rmtree(d)

    SKILLS_OUT.mkdir(parents=True, exist_ok=True)

    count = 0
    skipped = 0

    for entry in MANIFEST:
        if entry.status == "deferred":
            skipped += 1
            continue

        # Skip help — not useful as a standalone agent skill
        if entry.name == "help":
            skipped += 1
            continue

        out_dir = SKILLS_OUT / f"pulse-{entry.name}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "SKILL.md"

        if entry.kind == "skill":
            skill_md = find_skill_md(entry.name, entry.layer)
            if skill_md:
                fm, procedure = parse_skill_md(skill_md)
                content = generate_skill_type(entry, fm, procedure)
            else:
                # No SKILL.md in default_assets — generate from manifest only
                content = generate_skill_type(entry, {}, "")
        elif entry.kind == "playbook":
            pb_path = find_playbook_yaml(entry.name)
            if pb_path:
                pb = yaml.safe_load(pb_path.read_text())
                content = generate_playbook_type(entry, pb)
            else:
                content = generate_builtin_type(entry)
        elif entry.kind == "builtin":
            content = generate_builtin_type(entry)
        else:
            skipped += 1
            continue

        out_file.write_text(content)
        count += 1
        print(f"  {'updated' if out_file.exists() else 'created'}: pulse-{entry.name}/SKILL.md")

    print(f"\nDone: {count} skills generated, {skipped} skipped (deferred/help)")
    print(f"Output: {SKILLS_OUT}/pulse-*/SKILL.md")


if __name__ == "__main__":
    main()
