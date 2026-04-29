# Pulse Skills Framework — Agent Instructions

> For Codex, OpenCode, and any agent that reads AGENTS.md.

## What This Is

A Python CLI (`pulse <verb>`) that operationalizes six business advisory frameworks into repeatable procedures. 52 commands across 9 layers: meta, kickoff, knowledge, corpus, discovery, listen, synthesis, action, reflect.

## Setup

```bash
pip install -e .              # Core install
pip install -e ".[dev]"       # With dev tools
pip install -e ".[corpus]"    # With optional RAG corpus
pulse init                    # One-time setup (creates ~/.pulse/)
```

## How to Use

Every operation is `pulse <verb>`. The verb resolves through a registry that supports exact match, aliases, prefix match, and fuzzy matching.

```bash
pulse help                    # List all commands
pulse help <verb>             # Help for one command
pulse workspace-new <id>      # Create a workspace
pulse onboard <id>            # Full kickoff (~60 min interactive)
pulse daily                   # Daily source scan (~3 min)
pulse weekly                  # Routine intelligence pass
pulse workspace-status        # Show workspace state
```

Bare `pulse` (no verb) launches an interactive decision-tree router. Requires a terminal.

## Agent Rules

1. Run `pulse init` first if `~/.pulse/` does not exist.
2. Check `pulse workspace-status` before running operational commands.
3. Do not edit `workspace.yaml` directly — use the corresponding `pulse` command.
4. The SQLite index (`.index.sqlite`) is regenerable: `pulse reindex`.
5. Corpus is optional. Commands work without it unless they explicitly require it.
6. Skills that declare `confirms_before_commit: true` need operator confirmation before writing.
7. Playbooks compose skills sequentially with checkpoints — don't skip checkpoints.

## Command Reference

### Lifecycle
```
pulse init                     # Framework setup
pulse workspace-new <id>       # Create workspace
pulse onboard <id>             # Full kickoff (playbook)
pulse daily                    # Daily source scan (playbook)
pulse weekly                   # Weekly pass (playbook)
pulse monthly                  # Monthly synthesis (playbook)
pulse quarterly                # Quarterly review (playbook)
```

### Workspace Management
```
pulse workspace-list           # List workspaces
pulse workspace-switch <id>    # Set active workspace
pulse workspace-status [id]    # Status summary
pulse workspace-archive <id>   # Archive workspace
pulse reindex [id]             # Rebuild index
```

### Kickoff Skills
```
pulse set-identity             # Business identity
pulse profile-customer         # Customer profile (4-tier questionnaire)
pulse articulate-offer         # Offer articulation
pulse set-goals                # Goals and constraints
pulse set-position             # 4x2 position matrix + intention
pulse reposition               # Full reposition (playbook)
```

### Discovery
```
pulse map-ecosystem            # Hormozi ecosystem mapping
pulse map-trust-network        # Abraham trust network
pulse scan-acquisitions        # Frasier acquisition wheel
pulse type-sources             # Classify URLs by strategic role
pulse add-source               # Add one source
```

### Intelligence
```
pulse extract                  # Extract atoms from sources
pulse daily-extract            # Lightweight daily extraction (claims+stats)
pulse mine-reviews             # Mine review sites
pulse scan-ads                 # Scan ad libraries
pulse propose-hypothesis       # Propose hypotheses from atoms
pulse score-signals            # Score atoms against hypotheses
pulse update-directions        # Update direction momentum
pulse find-commodity-pattern   # Detect commodity patterns
pulse find-gaps                # Gap-map synthesis
```

### Deliverables
```
pulse write-brief              # Content briefs
pulse write-positioning        # Positioning statement
pulse draft-survey             # JTBD survey
pulse draft-outreach           # Outreach sequences
```

### Review
```
pulse audit-drift              # Position drift analysis
pulse postmortem               # Hypothesis postmortem
pulse connect-source           # Register external source
```

### Knowledge & Corpus
```
pulse author-knowledge         # Author knowledge file
pulse refine-knowledge         # Add refinement notes
pulse evolve-knowledge         # Evolve from notes
pulse knowledge-status         # Knowledge summary
pulse ingest                   # Ingest into corpus
pulse corpus-query             # Query corpus
pulse corpus-status            # Corpus summary
pulse enable-corpus            # Enable corpus
pulse disable-corpus           # Disable corpus
```

### Meta
```
pulse refine <skill>           # Note on a skill
pulse evolve <skill>           # Evolve skill from notes
pulse evolve-all               # Evolve all skills with pending notes
pulse refine-router            # Note on router tree
```

## Architecture

```
~/.pulse/
├── config.yaml                # Global config (API keys, active workspace)
├── workspaces/<id>/           # Per-client state
│   ├── workspace.yaml         # Spine: identity, customer, offer, goals, position
│   ├── atoms/YYYY-MM/*.jsonl  # Observations (append-only)
│   ├── directions/            # Tracked directions
│   ├── hypotheses/            # Active hypotheses
│   ├── sources/sources.yaml   # Intelligence sources
│   └── .index.sqlite          # Regenerable index
├── skills/<layer>/<name>/     # Skill definitions (SKILL.md + schemas)
├── playbooks/*.yaml           # Composed workflows
├── knowledge/                 # Framework knowledge files
├── corpus/                    # Optional RAG (LanceDB)
└── router/tree.yaml           # Decision tree for bare `pulse`
```

## Development

- Python 3.11+, Click, Pydantic v2, PyYAML, Jinja2, Rich, anthropic SDK
- Tests: `pytest` (83 tests)
- Lint: `ruff check pulse/ tests/`
- Types: `mypy pulse/ --ignore-missing-imports`
- Manifest (source of truth): `pulse/manifest.py`
