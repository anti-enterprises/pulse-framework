# Pulse Skills Framework

Filesystem-based business intelligence toolkit. Operationalizes six advisory frameworks (Hormozi, Abraham, Frasier, DemandCurve, Imperium, Robbins) into repeatable CLI procedures.

## Quick Reference

```
pulse                        # Interactive router (requires terminal)
pulse help                   # List all commands
pulse help <verb>            # Help for a specific command
pulse init                   # One-time setup → creates ~/.pulse/
pulse workspace-new <id>     # Create workspace
pulse onboard <id>           # Full kickoff (~60 min)
pulse weekly                 # Routine intelligence pass (~10 min)
pulse workspace-status       # Show workspace state
```

## Architecture

Five layers, bottom to top:

1. **Workspaces** — per-client state at `~/.pulse/workspaces/<id>/` (YAML + JSONL + SQLite index)
2. **Skills** — atomic procedures at `~/.pulse/skills/<layer>/<name>/SKILL.md`
3. **Playbooks** — composed workflows at `~/.pulse/playbooks/*.yaml`
4. **Knowledge** — framework files at `~/.pulse/knowledge/`
5. **Corpus** — optional RAG layer via LanceDB at `~/.pulse/corpus/`

## Rules for Agents

1. **Always check the active workspace** before running operational commands: `pulse workspace-status`
2. **Never modify workspace.yaml directly** — use the appropriate `pulse` command
3. **Filesystem is source of truth** — `.index.sqlite` is regenerable via `pulse reindex`
4. **Respect the confirmation flow** — commands that declare `confirms_before_commit: true` should not be bypassed
5. **Corpus is optional** — skills with `corpus_queries: optional: true` work without it
6. **Run `pulse init` before anything else** if `~/.pulse/` does not exist
7. **Skills are procedures, not wikis** — each has numbered steps, declared I/O, and explicit outputs

## Command Catalog (45 active + 3 deferred)

### Meta
| Command | Description |
|---------|-------------|
| `pulse init` | One-time framework setup |
| `pulse workspace-new <id>` | Create workspace |
| `pulse workspace-list` | List all workspaces |
| `pulse workspace-switch <id>` | Set active workspace |
| `pulse workspace-status [id]` | Workspace state summary |
| `pulse workspace-archive <id>` | Archive a workspace |
| `pulse reindex [id]` | Rebuild SQLite index from filesystem |
| `pulse refine <skill>` | Append refinement note to a skill |
| `pulse evolve <skill>` | Propose skill updates from refinement notes |
| `pulse refine-router` | Append refinement note to router tree |

### Kickoff (run once per workspace)
| Command | Description |
|---------|-------------|
| `pulse onboard <id>` | Full kickoff playbook (~60 min) |
| `pulse reposition <id>` | Rebuild positioning from scratch |
| `pulse set-identity` | Identity block: declared business, real business |
| `pulse profile-customer` | Deep customer profile (4-tier questionnaire) |
| `pulse articulate-offer` | Offer: promise, mechanism, pricing, proof |
| `pulse set-goals` | Goals: primary, secondary, bets, constraints |
| `pulse set-position` | Position: 4x2 matrix + intention |

### Discovery
| Command | Description |
|---------|-------------|
| `pulse map-ecosystem` | Hormozi ecosystem mapping |
| `pulse map-trust-network` | Abraham trust-network profiling |
| `pulse scan-acquisitions` | Frasier acquisition wheel |
| `pulse type-sources` | Assign strategic roles to URLs |
| `pulse add-source` | Add a single source manually |

### Listen
| Command | Description |
|---------|-------------|
| `pulse extract` | Extract atoms from curated sources |
| `pulse mine-reviews` | Mine review aggregators |
| `pulse scan-ads` | Scan ad libraries |

### Synthesis
| Command | Description |
|---------|-------------|
| `pulse propose-hypothesis` | Cluster atoms, propose hypotheses |
| `pulse score-signals` | Score atoms against hypotheses |
| `pulse update-directions` | Recompute direction momentum |
| `pulse find-commodity-pattern` | Hormozi commodity detection |
| `pulse find-gaps` | Gap-map synthesis |

### Action
| Command | Description |
|---------|-------------|
| `pulse write-brief` | Generate content briefs |
| `pulse write-positioning` | Draft positioning statement |
| `pulse draft-survey` | JTBD survey generation |
| `pulse draft-outreach` | Outreach sequence generation |

### Reflect
| Command | Description |
|---------|-------------|
| `pulse audit-drift` | Position drift analysis |
| `pulse postmortem` | Hypothesis postmortem |
| `pulse connect-source` | Register an external source |

### Playbooks (composed workflows)
| Command | Description |
|---------|-------------|
| `pulse weekly` | Weekly intelligence pass (~10 min). Aliases: `pulse intel`, `pulse w` |
| `pulse monthly` | Monthly synthesis (~25 min) |
| `pulse quarterly` | Quarterly review (~60 min) |

### Knowledge
| Command | Description |
|---------|-------------|
| `pulse author-knowledge` | Author a knowledge file |
| `pulse refine-knowledge` | Refine knowledge files |
| `pulse evolve-knowledge` | Evolve knowledge from notes |
| `pulse knowledge-status` | Knowledge layer summary |

### Corpus (optional)
| Command | Description |
|---------|-------------|
| `pulse ingest` | Ingest files into corpus |
| `pulse corpus-query` | Query the corpus |
| `pulse corpus-status` | Corpus summary |
| `pulse enable-corpus` | Enable corpus infrastructure |
| `pulse disable-corpus` | Disable corpus infrastructure |

## Operational Cadences

- **Daily/ad-hoc**: `pulse extract`, `pulse propose-hypothesis`
- **Weekly** (`pulse weekly`): extract → score → update directions → write digest. ~10 min.
- **Monthly** (`pulse monthly`): weekly + commodity patterns + gap map + monthly digest. ~25 min.
- **Quarterly** (`pulse quarterly`): monthly + drift audit + postmortems + ecosystem refresh. ~60 min.

## Workspace Structure

```
~/.pulse/workspaces/<id>/
├── workspace.yaml          # The spine: identity, customer, offer, goals, position
├── atoms/YYYY-MM/atoms.jsonl  # Observations (append-only)
├── directions/             # Named directions with momentum
├── hypotheses/             # Propositions being tested
├── factors/                # External factors being tracked
├── sources/sources.yaml    # Active intelligence sources
├── ecosystem/              # Maps, trust networks, gap analysis
├── briefs/                 # Generated digests and briefs
├── runs/                   # Execution logs per invocation
└── .index.sqlite           # Regenerable SQLite index
```

## Development

```bash
pip install -e ".[dev]"     # Install with dev dependencies
pytest                      # Run tests (83 tests)
ruff check pulse/ tests/    # Lint
mypy pulse/                 # Type check
```

## Key Files

- `pulse/manifest.py` — Single source of truth for all 48 commands
- `pulse/runtime/schemas.py` — All Pydantic v2 data models
- `pulse/runtime/skill.py` — Skill discovery and execution engine
- `pulse/runtime/playbook.py` — Playbook runner (6 composition patterns)
- `pulse/runtime/router.py` — Interactive decision tree
- `default_assets/` — Skills, playbooks, knowledge, router tree shipped with the package
