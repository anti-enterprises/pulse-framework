"""Machine-readable command manifest.

Single source of truth for all v1 commands. Docs, help, router, and
dispatcher all derive from this. Per Codex architecture review:
canonical name, aliases, kind, phase, status.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandEntry:
    name: str
    kind: str  # "builtin" | "skill" | "playbook" | "deferred"
    layer: str
    description: str
    phase: int  # implementation phase (1-7)
    status: str = "planned"  # "implemented" | "planned" | "deferred"
    aliases: tuple[str, ...] = ()


# Canonical v1 command manifest — 56 entries
# (53 active + 3 deferred)
MANIFEST: tuple[CommandEntry, ...] = (
    # ── Meta (12) ──
    CommandEntry("init", "builtin", "meta", "One-time framework setup.", 2, "implemented"),
    CommandEntry("workspace-new", "builtin", "meta", "Create a new workspace.", 2, "implemented"),
    CommandEntry("workspace-list", "builtin", "meta", "List all workspaces.", 2, "implemented"),
    CommandEntry("workspace-switch", "builtin", "meta", "Set active workspace.", 2, "implemented"),
    CommandEntry("workspace-status", "builtin", "meta", "Workspace state summary.", 2, "implemented"),
    CommandEntry("workspace-archive", "builtin", "meta", "Archive a workspace.", 7),
    CommandEntry("reindex", "builtin", "meta", "Rebuild SQLite index.", 2, "implemented"),
    CommandEntry("export", "builtin", "meta", "Export directions/hypotheses/briefs as JSON.", 2, "implemented"),
    CommandEntry("refine", "builtin", "meta", "Append refinement note to a skill.", 7, "implemented"),
    CommandEntry("evolve", "builtin", "meta", "Propose skill updates from refinement notes.", 7),
    CommandEntry("evolve-all", "builtin", "meta", "Evolve all skills with pending refinement notes.", 7, "implemented"),
    CommandEntry("refine-from-runs", "builtin", "meta", "Propose refinements from run history.", 7, "implemented"),
    CommandEntry("import-refinements", "builtin", "meta", "Import refinement notes from a YAML file.", 7, "implemented"),
    CommandEntry("refine-router", "builtin", "meta", "Append refinement note to router tree.", 7),
    CommandEntry("help", "builtin", "meta", "Show help.", 1, "implemented"),
    # ── Kickoff (7) ──
    CommandEntry("onboard", "playbook", "kickoff", "Full kickoff playbook. ~60 min.", 6, aliases=("pulse kickoff",)),
    CommandEntry("reposition", "playbook", "kickoff", "Rebuild positioning.", 7),
    CommandEntry("set-identity", "skill", "kickoff", "Identity block.", 3),
    CommandEntry("profile-customer", "skill", "kickoff", "Customer profile questionnaire.", 6),
    CommandEntry("articulate-offer", "skill", "kickoff", "Offer block.", 6),
    CommandEntry("set-goals", "skill", "kickoff", "Goals block.", 6),
    CommandEntry("set-position", "skill", "kickoff", "Position block.", 6),
    CommandEntry("set-refinement-criteria", "skill", "kickoff", "Define refinement criteria for the workspace.", 7),
    # ── Knowledge (4) ──
    CommandEntry("author-knowledge", "skill", "knowledge", "Author a knowledge file.", 7),
    CommandEntry("refine-knowledge", "skill", "knowledge", "Refine knowledge files.", 7),
    CommandEntry("evolve-knowledge", "skill", "knowledge", "Evolve knowledge from notes.", 7),
    CommandEntry("knowledge-status", "skill", "knowledge", "Knowledge layer summary.", 7),
    # ── Corpus (5) ──
    CommandEntry("ingest", "skill", "corpus", "Ingest files into corpus.", 5),
    CommandEntry("corpus-query", "skill", "corpus", "Query the corpus.", 5),
    CommandEntry("corpus-status", "skill", "corpus", "Corpus summary.", 5),
    CommandEntry("enable-corpus", "builtin", "corpus", "Enable corpus infrastructure.", 5, aliases=("pulse enable corpus",)),
    CommandEntry("disable-corpus", "builtin", "corpus", "Disable corpus infrastructure.", 5, aliases=("pulse disable corpus",)),
    # ── Discovery (5) ──
    CommandEntry("map-ecosystem", "skill", "discovery", "Hormozi ecosystem mapping.", 6),
    CommandEntry("map-trust-network", "skill", "discovery", "Abraham trust-network profiling.", 7),
    CommandEntry("scan-acquisitions", "skill", "discovery", "Frasier acquisition wheel.", 7),
    CommandEntry("type-sources", "skill", "discovery", "Assign strategic roles to URLs.", 6),
    CommandEntry("add-source", "skill", "discovery", "Add a source manually.", 7),
    # ── Listen (4) ──
    CommandEntry("extract", "skill", "listen", "Extract atoms from sources.", 7),
    CommandEntry("daily-extract", "skill", "listen", "Lightweight daily atom extraction.", 7),
    CommandEntry("mine-reviews", "skill", "listen", "Mine review aggregators.", 7),
    CommandEntry("scan-ads", "skill", "listen", "Scan ad libraries.", 7),
    # ── Synthesis (5) ──
    CommandEntry("propose-hypothesis", "skill", "synthesis", "Propose hypotheses from atoms.", 7),
    CommandEntry("score-signals", "skill", "synthesis", "Score atoms against hypotheses.", 7),
    CommandEntry("update-directions", "skill", "synthesis", "Update direction momentum.", 7),
    CommandEntry("find-commodity-pattern", "skill", "synthesis", "Commodity pattern detection.", 7),
    CommandEntry("find-gaps", "skill", "synthesis", "Gap-map synthesis.", 7),
    # ── Action (4) ──
    CommandEntry("write-brief", "skill", "action", "Generate content briefs.", 7),
    CommandEntry("write-positioning", "skill", "action", "Draft positioning statement.", 7),
    CommandEntry("draft-survey", "skill", "action", "JTBD survey generation.", 7),
    CommandEntry("draft-outreach", "skill", "action", "Outreach sequence generation.", 7),
    # ── Reflect (3) ──
    CommandEntry("audit-drift", "skill", "reflect", "Position drift analysis.", 7),
    CommandEntry("postmortem", "skill", "reflect", "Hypothesis postmortem.", 7),
    CommandEntry("connect-source", "skill", "reflect", "Register an external source.", 7),
    # ── Playbooks (3) ──
    CommandEntry("daily", "playbook", "playbook", "Daily source scan. ~3 min.", 7, aliases=("pulse d",)),
    CommandEntry("weekly", "playbook", "playbook", "Weekly intelligence pass. ~10 min.", 7, aliases=("pulse intel", "pulse w")),
    CommandEntry("monthly", "playbook", "playbook", "Monthly synthesis. ~25 min.", 7),
    CommandEntry("quarterly", "playbook", "playbook", "Quarterly review. ~60 min.", 7),
    # ── Deferred (3) ──
    CommandEntry("intel-query", "deferred", "", "Reserved for v2.", 0, "deferred"),
    CommandEntry("emit", "deferred", "", "Reserved for v3.", 0, "deferred"),
    CommandEntry("portfolio-scan", "deferred", "", "Reserved for v4.", 0, "deferred"),
)


def active_commands() -> list[CommandEntry]:
    """Return only non-deferred commands."""
    return [c for c in MANIFEST if c.status != "deferred"]


def implemented_commands() -> list[CommandEntry]:
    """Return only implemented commands."""
    return [c for c in MANIFEST if c.status == "implemented"]


def commands_by_phase(phase: int) -> list[CommandEntry]:
    """Return commands belonging to a specific implementation phase."""
    return [c for c in MANIFEST if c.phase == phase]
