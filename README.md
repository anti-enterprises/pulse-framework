# Pulse Skills Framework

A terminal-native business intelligence toolkit that turns six advisory frameworks into repeatable, composable CLI procedures — powered by LLMs, operated by humans.

Business intelligence work is usually unrepeatable. An advisor runs a competitive analysis, writes a positioning doc, gathers market signals — but the process lives in their head. Next quarter, next client, they start from scratch. Enterprise tools exist, but they are expensive, opaque, and built for teams of analysts, not solo operators.

Pulse solves this by encoding the methodologies of Hormozi, Abraham, Frasier, DemandCurve, Imperium, and Robbins into **skills** — atomic, numbered procedures with declared inputs, outputs, and LLM-augmented steps. Skills compose into **playbooks** that run on daily, weekly, monthly, and quarterly cadences. All state lives on your filesystem as human-readable YAML, JSONL, and Markdown. Nothing is hidden in a database you cannot inspect.

## What you get

**A structured intelligence process, not ad-hoc research.** Run `pulse weekly` and get a scored digest of market signals, emerging hypotheses, and direction momentum — not a Google Doc of links you will never revisit.

**Per-client workspaces with consistent methodology.** Every engagement follows the same framework. Onboard a client in 60 minutes. Produce weekly intelligence in 10. Each workspace is an isolated directory with its own identity, customer profile, sources, atoms, hypotheses, and deliverables.

**Six advisory frameworks operationalized, not summarized.** Hormozi's ecosystem mapping. Abraham's trust-network profiling. Frasier's acquisition wheel. DemandCurve's growth patterns. Imperium's positioning matrix. Robbins' strategic seasons. Each distilled into procedures with numbered steps and structured outputs.

**Everything version-controllable and human-readable.** All state is YAML, JSONL, and Markdown on your filesystem. SQLite indexes are regenerable, never the source of truth. You can `git init` a workspace and get full history of every intelligence decision.

**AI-agent native.** 50 Claude Code skills, an MCP server for Claude Desktop, and a setup script that registers Pulse with your agent in one command. Every `pulse <verb>` works identically whether you type it or your agent invokes it.

### Who this is for

- **Founders** who want a repeatable intelligence process instead of ad-hoc Googling
- **Advisors and fractional executives** managing multiple client engagements who need per-client workspaces with consistent methodology
- **AI-assisted operators** using Claude Code, Codex, or Cursor who want structured procedures their agent can follow
- **Framework hackers** who want to extend the skill library or wire in their own advisory methodology

## Get started

### Requirements

- Python 3.11+
- An Anthropic API key (set `ANTHROPIC_API_KEY` in your environment)

### Install

```bash
git clone https://github.com/your-org/pulse-skills-framework.git
cd pulse-skills-framework
pip install -e .

# One-time framework setup — creates ~/.pulse/
pulse init
```

### Create your first workspace

```bash
# Create a workspace
pulse workspace-new acme-corp

# Run the full kickoff (~90 min, interactive with checkpoints)
pulse onboard acme-corp

# Or run individual kickoff steps
pulse set-identity
pulse profile-customer
pulse articulate-offer
pulse set-goals
pulse set-position
```

The onboard playbook walks you through defining your business identity, building a deep customer profile, articulating your offer, setting goals, and establishing strategic positioning. It pauses at checkpoints so you can stop and resume later.

### Run your first intelligence pass

Once onboarded, add sources and run your first weekly pass:

```bash
pulse type-sources         # Classify and register intelligence sources
pulse weekly               # Extract, score, update directions, write digest
```

The weekly digest lands in `~/.pulse/workspaces/acme-corp/briefs/` as a structured Markdown file with scored signals, hypothesis updates, and recommended actions.

### Interactive mode

Running `pulse` with no arguments launches the **router** — an interactive decision tree that guides you to the right command based on what you are trying to do. The router checks workspace state and warns if prerequisites are missing before letting you run a command.

## Using Pulse with Claude Code and Codex

Pulse is designed to run inside AI coding agents. Every skill has declared inputs, numbered steps, and structured outputs that agents can follow without improvisation.

### Register skills

```bash
# Auto-detect Claude Code and/or Codex and register skills
./setup

# Target a specific agent
./setup --host claude
./setup --host codex

# Remove skills
./setup --uninstall
```

This symlinks Pulse skills into `~/.claude/skills/` or `~/.codex/skills/`. Once registered, Pulse commands are available as slash commands: `/pulse-weekly`, `/pulse-onboard`, `/pulse-extract`, etc.

### Schedule as a routine

Pulse playbooks are designed for recurring execution. In Claude Code, you can schedule them as routines:

```
# Run weekly intelligence every Monday at 9am
/schedule pulse weekly --cron "0 9 * * 1"

# Or use the loop skill for active research phases
/loop 6h pulse daily
```

In Codex, add Pulse commands to your automation scripts — the CLI is stateless and idempotent by design.

### MCP server

For Claude Desktop or other MCP-compatible clients, Pulse exposes an MCP server:

```json
{
  "mcpServers": {
    "pulse": {
      "command": "python",
      "args": ["-m", "pulse.mcp_server"],
      "cwd": "/path/to/pulse-skills-framework"
    }
  }
}
```

Exposed tools: `pulse_help`, `pulse_workspace_status`, `pulse_workspace_list`, `pulse_workspace_new`, `pulse_workspace_switch`, `pulse_reindex`, and `pulse_run` (generic runner for any command).

### Permissions

The included `.claude/settings.json` pre-configures `Bash(pulse *)` so the agent can run any Pulse command without per-invocation approval.

## How it works

### The intelligence flow

Pulse follows a six-phase cycle:

```
Kickoff → Discovery → Listen → Synthesis → Action → Reflect
  (once)    (once)    (ongoing)  (ongoing)  (ongoing)  (periodic)
```

**Kickoff** establishes the strategic foundation: who you are, who your customer is, what you offer, what you are trying to achieve, and where you stand. This is done once per workspace.

**Discovery** maps the competitive landscape: direct competitors, substitutes, trust networks, acquisition targets, and intelligence sources. Also done once, refreshed quarterly.

**Listen** extracts observations ("atoms") from curated sources on an ongoing basis. Atoms are the smallest unit of intelligence — a claim, statistic, quote, entity mention, or theme.

**Synthesis** detects patterns: clusters atoms into hypotheses, scores signals against active hypotheses, tracks direction momentum, identifies commodity patterns and market gaps.

**Action** produces deliverables: content briefs, positioning statements, JTBD surveys, outreach sequences — all grounded in accumulated intelligence rather than invented from scratch.

**Reflect** audits the system: detects when your actual activities are drifting from declared positioning, runs postmortems on confirmed or retired hypotheses, and captures transferable learnings.

### Architecture

Pulse has five structural layers:

```
┌─────────────────────────────────────────────────┐
│  Corpus          Optional RAG layer (LanceDB)   │
├─────────────────────────────────────────────────┤
│  Knowledge       Distilled framework files      │
├─────────────────────────────────────────────────┤
│  Playbooks       Composed workflows (YAML)      │
├─────────────────────────────────────────────────┤
│  Skills          Atomic procedures (Markdown)   │
├─────────────────────────────────────────────────┤
│  Workspaces      Per-client state (YAML/JSONL)  │
└─────────────────────────────────────────────────┘
```

**Workspaces** hold all per-client state: identity, customer profile, offer, goals, positioning, intelligence atoms, hypotheses, directions, and sources. Each workspace is a directory of human-editable files with a regenerable SQLite index.

**Skills** are Markdown files with YAML frontmatter declaring inputs, outputs, knowledge dependencies, and a numbered procedure. The runtime parses the frontmatter and executes the procedure step by step, delegating LLM-backed steps to the configured provider.

**Playbooks** compose skills into multi-step workflows with checkpoints (human-in-the-loop pauses), conditional steps, and idempotent re-runs.

**Knowledge** contains distilled, operator-vetted framework material — glossaries, taxonomies, customer profile questionnaires — that skills reference at runtime. Updated independently of skills.

**Corpus** is an optional local RAG backend (LanceDB + embeddings) for querying source material during knowledge authoring. Never queried during normal skill execution.

### Core concepts

**Atoms** are the smallest unit of intelligence — a single observation (claim, statistic, quote, entity, theme) extracted from a source and timestamped. Atoms accumulate in append-only JSONL files partitioned by month.

**Directions** are named market trends with a lifecycle: nascent, emerging, hardening, established, peaking, declining, stale. Momentum is computed from atom velocity and hypothesis confidence.

**Hypotheses** are testable beliefs about the market. They move through proposed, active, hardening, confirmed/contested, retired. Each carries a confidence score updated as new atoms are scored against it.

### Workspace structure

```
~/.pulse/workspaces/<id>/
├── workspace.yaml              # The spine: identity, customer, offer, goals, position
├── atoms/YYYY-MM/atoms.jsonl   # Observations (append-only, monthly partitions)
├── directions/                 # Named market directions with momentum scores
├── hypotheses/                 # Testable propositions being tracked
├── factors/                    # External forces (regulatory, tech, economic, etc.)
├── sources/sources.yaml        # Active intelligence sources
├── ecosystem/                  # Competitive maps, trust networks, gap analysis
├── briefs/                     # Generated digests and content briefs
├── positioning/                # Positioning statements
├── surveys/                    # Generated JTBD surveys
├── outreach/                   # Outreach sequences
├── runs/                       # Execution logs per invocation
└── .index.sqlite               # Regenerable index (never the source of truth)
```

## Skills reference

Pulse ships with 38 skills across 9 layers, plus meta commands for workspace and framework management.

### Kickoff

Run once per workspace to establish the strategic foundation. All outputs write to `workspace.yaml`.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse set-identity` | ~5m | Identity block: what the business does vs. what it is really in, plus a scope statement bounding the intelligence work |
| `pulse profile-customer` | ~30m | Deep customer profile across four tiers: demographics/firmographics, psychographics and decision-making, jobs-to-be-done and behavior, and trust environment |
| `pulse articulate-offer` | ~10m | Offer block: core promise, delivery mechanism, pricing model, and proof assets — grounded in identity and customer profile |
| `pulse set-goals` | ~10m | Goals block: primary goal, secondary goals, active bets, and constraints for the current 90-day period |
| `pulse set-position` | ~10m | Robbins 4x2 positioning matrix (person/business/industry/economy across season and lifecycle) plus a strategic intention statement |

### Discovery

Map the competitive landscape and curate intelligence sources. Outputs go to `ecosystem/` and `sources/`.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse map-ecosystem` | ~15m | Hormozi-style competitive map: direct competitors, substitutes, complements, adjacent winners — seeded from customer profile, optionally expanded via web research |
| `pulse map-trust-network` | ~10m | Abraham trust-network hierarchy (Tier 1-4): influencers, platforms, communities, and media that shape your customers' decisions |
| `pulse scan-acquisitions` | ~10m | Frasier acquisition wheel: candidates scored across capability, customer access, technology, talent, distribution, and competitive-blocking categories |
| `pulse type-sources` | ~10m | Classify URLs into 10 strategic roles (competitor, trust voice, community forum, etc.) with metadata for downstream monitoring |
| `pulse add-source` | ~1m | Register a single intelligence source with URL, label, kind, and strategic role |

### Listen

Extract intelligence from curated sources. All outputs are atoms written to `atoms/YYYY-MM/atoms.jsonl`.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse extract` | ~10m | Deep atom extraction: claims, statistics, quotes, entities, and themes from all active sources over a 7-day window, with relevance scoring and deduplication |
| `pulse daily-extract` | ~3m | Lightweight daily pass: high-signal claims and stats only, high relevance threshold, one LLM call per source |
| `pulse mine-reviews` | ~5m | Review aggregator mining: pain points, dissatisfactions, metrics, and recurring themes from review sites |
| `pulse scan-ads` | ~5m | Ad library intelligence: messaging themes, value propositions, positioning signals, and spend pattern shifts from competitor ads |

### Synthesis

Detect patterns, test hypotheses, and identify market opportunities.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse propose-hypothesis` | ~10m | Multi-pass clustering of unexplained atoms into thematic groups, then generation of falsifiable hypothesis statements with initial confidence scores |
| `pulse score-signals` | ~3m | Score recent atoms against active hypotheses, updating confidence levels based on supporting or contradicting evidence strength |
| `pulse update-directions` | ~3m | Recompute direction momentum from atom velocity, hypothesis confidence, and time decay; advance the state machine (nascent through stale) |
| `pulse find-commodity-pattern` | ~10m | Hormozi commodity detection: identify dimensions of convergence (pricing parity, feature sameness, messaging overlap) and score commoditization risk |
| `pulse find-gaps` | ~10m | Market white-space analysis: cross-reference the served landscape with your customer profile to find unserved jobs, underserved segments, and price gaps |

### Action

Produce deliverables grounded in accumulated intelligence. Outputs go to `briefs/`, `positioning/`, `surveys/`, and `outreach/`.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse write-brief` | ~5m | Cadenced digest (daily, weekly, monthly, or quarterly) with executive summary, key findings, what changed, and recommended actions |
| `pulse write-positioning` | ~10m | Positioning statement (For/Who/We provide/That/Unlike/We) with elevator pitch, narrative, and proof points — all tied to scored evidence |
| `pulse draft-survey` | ~5m | JTBD customer survey: screening, situation, motivation, outcome, constraint, and ranking questions mapped to unconfirmed hypotheses |
| `pulse draft-outreach` | ~5m | Five-touch outreach sequence (cold open, value demo, social proof, direct ask, breakup) grounded in customer pain points and proven hypotheses |

### Reflect

Audit positioning, capture learnings, and maintain the intelligence system.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse audit-drift` | ~5m | Position drift detection across five dimensions (message, audience, value, competitive, intention) with severity scores and recommended corrections |
| `pulse postmortem` | ~5m | Hypothesis lifecycle review: evidence timeline reconstruction, outcome analysis (confirmed/retired/contested), and transferable learnings |
| `pulse connect-source` | ~1m | Register an external research source (NotebookLM, book, podcast, course) in the workspace for reference during intelligence work |

### Knowledge

Manage the reusable framework material that skills reference at runtime. Outputs go to `~/.pulse/knowledge/`.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse author-knowledge` | ~15m | Multi-pass authoring of a new knowledge file from a chosen framework or topic, with outline, sections, examples, and cross-references |
| `pulse refine-knowledge` | ~1m | Queue a refinement note on a knowledge file for later structured evolution |
| `pulse evolve-knowledge` | ~5m | Synthesize accumulated refinement notes into proposed edits, apply accepted changes, clear addressed notes |
| `pulse knowledge-status` | ~30s | Summary of the knowledge layer: file counts, frameworks covered, pending refinements, total word count |

### Corpus

Optional RAG backend for querying source material during knowledge authoring.

| Command | Time | What you get |
|---------|------|-------------|
| `pulse ingest` | ~5m | Embed files into LanceDB (PDF, DOCX, MD, TXT, HTML) with collection tagging, cost estimation, and ingestion logging |
| `pulse corpus-query` | ~1m | Semantic search over ingested material returning top-K results with chunk text, metadata, and similarity scores |
| `pulse corpus-status` | ~10s | Collection counts, document and chunk totals, index size, and embedding provider details |
| `pulse enable-corpus` | — | Enable the corpus infrastructure (creates LanceDB store) |
| `pulse disable-corpus` | — | Disable and remove corpus infrastructure |

### Meta

Workspace lifecycle, framework evolution, and help.

| Command | What it does |
|---------|-------------|
| `pulse init` | One-time framework setup — creates `~/.pulse/` with skills, playbooks, knowledge, and config |
| `pulse workspace-new <id>` | Create a new workspace directory with empty structure |
| `pulse workspace-list` | List all workspaces with status indicators |
| `pulse workspace-switch <id>` | Set the active workspace |
| `pulse workspace-status [id]` | Workspace state summary: position matrix, hypothesis/direction counts, source health, recent runs |
| `pulse workspace-archive <id>` | Move a completed workspace to archive, preserving all data |
| `pulse reindex [id]` | Rebuild the SQLite index from filesystem state |
| `pulse refine <skill>` | Append a refinement note to any skill's procedure |
| `pulse evolve <skill>` | Synthesize accumulated refinement notes into proposed skill updates with version bumping |
| `pulse refine-router` | Append a refinement note to the interactive router decision tree |
| `pulse help [command]` | Show help for all commands or a specific command |

## Playbooks

Playbooks compose skills into cadenced workflows. They are invoked identically to individual skills — `pulse weekly` and `pulse extract` both run as `pulse <verb>`. Playbooks add checkpoints where the operator can pause and resume, conditional steps, and idempotent re-runs that skip already-completed steps.

### `pulse onboard` — Full kickoff

**Time:** ~90 minutes (interactive, with checkpoints)
**Run:** Once per workspace
**Aliases:** `pulse kickoff`

Sets up the complete strategic foundation for a workspace:

1. `pulse set-identity` — define identity block
2. **Checkpoint** — review identity before continuing
3. `pulse profile-customer` — walk the 4-tier customer questionnaire
4. **Checkpoint** — review customer profile before continuing
5. `pulse articulate-offer` — define offer block
6. `pulse set-goals` — set goals block
7. `pulse set-position` — establish positioning
8. **Checkpoint** — core kickoff complete, optionally continue to ecosystem
9. `pulse map-ecosystem` — Hormozi competitive mapping
10. `pulse type-sources` — classify and register intelligence sources

**Output:** A fully initialized `workspace.yaml` ready for operational intelligence work.

### `pulse reposition` — Rebuild positioning

**Time:** ~45 minutes (interactive)
**Run:** Ad-hoc, when strategy pivots

Re-walks the kickoff skills with change detection, surfacing what has shifted:

1. `pulse set-identity` — re-examine identity
2. **Checkpoint** — confirm before updating profile
3. `pulse profile-customer` — refresh customer understanding
4. `pulse articulate-offer` — re-articulate offer
5. `pulse set-goals` — update goals
6. `pulse set-position` — establish new positioning
7. **Checkpoint** — optionally refresh ecosystem
8. `pulse map-ecosystem` — refresh competitive map

### `pulse daily` — Daily source scan

**Time:** ~3 minutes
**Run:** Daily
**Aliases:** `pulse d`

Lightweight daily intelligence extraction:

1. `pulse daily-extract` — extract high-signal claims and stats from sources (last 24 hours)
2. `pulse update-directions` — link new atoms to existing directions (link-only mode, no momentum recompute)

**Output:** New atoms for the day, linked to existing directions.

### `pulse weekly` — Weekly intelligence pass

**Time:** ~10 minutes
**Run:** Weekly
**Aliases:** `pulse intel`, `pulse w`

The core operational cadence:

1. `pulse extract` — deep atom extraction from all sources (last 7 days)
2. `pulse update-directions` — link new atoms to directions
3. `pulse score-signals` — score atoms against active hypotheses
4. `pulse propose-hypothesis` — propose new hypotheses from unexplained atom clusters
5. `pulse write-brief` — generate weekly digest

**Output:** Scored atoms, updated hypotheses, direction momentum, and a weekly brief in `briefs/`.

### `pulse monthly` — Monthly synthesis

**Time:** ~25 minutes
**Run:** Monthly

Includes the full weekly pass, then adds deeper analysis:

1. **[weekly pass]** — extract, score, update, propose, digest (30-day window)
2. `pulse find-commodity-pattern` — detect commoditization dimensions and risk
3. `pulse find-gaps` — identify unserved needs and market white-space
4. `pulse write-brief` — generate monthly digest

**Output:** Everything from the weekly pass, plus commodity pattern analysis, gap map, and a monthly brief.

### `pulse quarterly` — Quarterly review

**Time:** ~60 minutes
**Run:** Quarterly

Includes the full monthly pass, then adds strategic review:

1. **[monthly pass]** — weekly + commodity patterns + gap map (90-day window)
2. `pulse audit-drift` — detect position drift across five dimensions
3. `pulse postmortem` — review lifecycle of confirmed/retired hypotheses
4. `pulse map-ecosystem` — refresh competitive map
5. **Checkpoint** — review synthesis before generating brief
6. `pulse write-brief` — generate quarterly review

**Output:** Everything from the monthly pass, plus drift audit, hypothesis postmortems, refreshed ecosystem map, and a quarterly brief.

## Optional: local RAG corpus

Pulse includes an optional local vector store for querying source material during knowledge authoring. It supports three embedding backends:

```bash
# Voyage AI (recommended)
pip install -e ".[corpus]"

# OpenAI embeddings
pip install -e ".[corpus-openai]"

# Local embeddings (no API key needed, slower)
pip install -e ".[corpus-local]"
```

Then:

```bash
pulse enable-corpus
pulse ingest --collection frameworks /path/to/books/*.pdf
pulse corpus-query "hormozi value equation"
```

The corpus is purely an authoring aid. Skills never query it during normal execution — this keeps the reasoning layer deterministic and operator-controlled.

## Extending Pulse

### Adding a skill

Create a folder under `~/.pulse/skills/<layer>/<your-skill>/` with a `SKILL.md`:

```yaml
---
name: pulse your-skill
version: 1.0.0
description: What this skill does
layer: synthesis
cadence: ad_hoc

reads:
  - "workspace.yaml"
writes:
  - "ecosystem/your-output.yaml"

inputs:
  workspace_id:
    type: string
    required: true

runtime:
  confirms_before_commit: true
  type: llm_procedure

llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.3
---

# Procedure

## 1. Load context
Read workspace.yaml...

## 2. Do the work
...

## 3. Write output
...
```

Register it in `pulse/manifest.py` to make it available as `pulse your-skill`.

### Adding a playbook

Create a YAML file under `~/.pulse/playbooks/`:

```yaml
name: pulse your-playbook
version: 1.0.0
description: What this playbook does
steps:
  - id: step_one
    skill: pulse extract
    on_failure: log_and_continue
  - id: checkpoint
    checkpoint:
      prompt: "Review extraction results. Continue?"
  - id: step_two
    skill: pulse your-skill
```

Playbooks support six composition patterns: sequential, foreach, conditional (`when`), branching (`switch/cases`), checkpointing (human-in-the-loop), and idempotent skip-if-done.

### Self-improving skills

Pulse has a built-in refinement loop. As you use skills and notice improvements, queue them:

```bash
# Add a note about how a skill could improve
pulse refine score-signals

# Later, generate a proposed update from accumulated notes
pulse evolve score-signals
```

Refinement notes accumulate in the skill's `refinements/` directory. `pulse evolve` synthesizes them into a proposed update with version bumping.

## Design principles

1. **Filesystem is source of truth.** Every piece of state is a human-editable file. SQLite indexes are regenerable, never primary stores.
2. **Skills are procedures, not wikis.** Declared inputs, numbered steps, declared outputs.
3. **Curated inputs only.** Nothing enters the reasoning layer automatically. The operator decides what the system sees.
4. **Knowledge and skills are decoupled.** Update framework knowledge without touching skill procedures.
5. **Corpus and runtime are separate.** The vector store is an authoring aid, never consulted during skill execution.
6. **The customer profile is the center of gravity.** Every downstream skill depends on a rich, structured customer profile gathered during kickoff.

## Roadmap

Pulse is versioned additively — each version adds capability without invalidating earlier work. A workspace built on v1 runs unchanged on v3.

- **v2** adds a curated business-intelligence database (the `intel/` layer) for structured market data alongside the unstructured corpus.
- **v3** adds outbound action capability (the `emitters/` layer) for drafting and sending emails, calendar blocks, and CRM updates — all human-approval gated.
- **v4+** adds cross-workspace pattern detection and Pulse Engine product integration.

See [ROADMAP.md](ROADMAP.md) for the full version plan and deliberate non-goals.

## Development

```bash
pip install -e ".[dev]"     # Install with dev dependencies
pytest                      # Run tests
ruff check pulse/ tests/    # Lint
mypy pulse/                 # Type check
```

## License

MIT
