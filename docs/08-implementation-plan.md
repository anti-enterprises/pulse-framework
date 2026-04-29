# 08 — Implementation Plan

This document tells the build agent what to construct in what order, with acceptance criteria at each phase. It is opinionated about sequencing because the framework's layers depend on each other in specific ways — building out of order produces dead-end branches that need rework.

The plan is organized in seven phases. Each phase ends in something testable. By the end of phase 4, the framework runs end-to-end against a workspace; by the end of phase 6, the corpus is functional (if enabled); by the end of phase 7, the five core playbooks compose the full operator experience.

## Project structure

Recommended Python package layout:

```
pulse-skills-framework/
├── pyproject.toml
├── README.md
├── pulse/                            # the package
│   ├── __init__.py
│   ├── cli.py                        # entry point: the `pulse` command
│   ├── dispatcher.py                 # command resolution and dispatch
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── workspace.py              # Workspace class and loading
│   │   ├── skill.py                  # Skill class, frontmatter parsing
│   │   ├── playbook.py               # Playbook runner
│   │   ├── router.py                 # Tree walker for `pulse` (no verb)
│   │   ├── llm.py                    # Claude API wrapper with logging
│   │   ├── corpus.py                 # LanceDB + embedding wrapper (optional)
│   │   ├── knowledge.py              # Knowledge file loading
│   │   ├── atoms.py                  # Atom write/read primitives
│   │   ├── index.py                  # SQLite index management
│   │   ├── runs.py                   # Run logging
│   │   └── schemas.py                # JSON schema validation
│   ├── commands/                     # built-in commands not in skills/
│   │   ├── init.py
│   │   ├── workspace_new.py
│   │   ├── workspace_list.py
│   │   ├── workspace_status.py
│   │   ├── reindex.py
│   │   └── help.py
│   └── utils/
│       ├── __init__.py
│       ├── jinja_env.py
│       ├── prompts.py
│       └── paths.py
├── default_assets/                   # what `pulse init` installs to ~/.pulse/
│   ├── skills/
│   │   ├── meta/
│   │   ├── kickoff/
│   │   ├── knowledge/
│   │   ├── corpus/
│   │   ├── discovery/
│   │   ├── listen/
│   │   ├── synthesis/
│   │   ├── action/
│   │   └── reflect/
│   ├── playbooks/
│   │   ├── onboard.yaml
│   │   ├── reposition.yaml
│   │   ├── weekly.yaml
│   │   ├── monthly.yaml
│   │   └── quarterly.yaml
│   ├── knowledge/
│   │   ├── frameworks/
│   │   ├── taxonomies/
│   │   ├── questionnaires/
│   │   ├── playbook-recipes/
│   │   ├── examples/
│   │   ├── source-templates/
│   │   ├── prompts/
│   │   └── glossary.yaml
│   ├── router/
│   │   └── tree.yaml
│   └── config.template.yaml
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── scripts/
    ├── package_assets.py             # bundle default_assets for distribution
    └── dev_install.sh
```

The split between `pulse/` (the runtime) and `default_assets/` (what gets installed to `~/.pulse/` on first run) is critical. The runtime is code that ships with the package; the assets are user-editable and get copied to the user's filesystem at init.

## Tech stack

Concrete choices for v1:

- **Python 3.11+**
- **Click** for CLI argument parsing (mature, simple, good shell completion)
- **Pydantic v2** for typed data classes (Workspace, Atom, Direction, Hypothesis)
- **PyYAML** with `safe_load` for YAML
- **Jinja2** for template rendering and condition evaluation
- **SQLite via `sqlite3` stdlib** for the workspace index
- **`anthropic` SDK** for Claude API
- **LanceDB** for the corpus vector store (optional dependency)
- **`voyageai` / `openai` SDKs** for embeddings (optional, depending on corpus provider choice)
- **`unstructured`** for parsing PDFs, Word docs, etc. during ingestion (optional dependency, only if corpus enabled)
- **`jsonschema`** for I/O validation
- **`rich`** for terminal output (tables, progress bars, formatted text)
- **`pytest`** for testing

Optional dependencies are gated behind extras:

```toml
[project.optional-dependencies]
corpus = ["lancedb", "voyageai", "unstructured[pdf,docx]"]
corpus-openai = ["lancedb", "openai", "unstructured[pdf,docx]"]
corpus-local = ["lancedb", "sentence-transformers", "unstructured[pdf,docx]"]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]
```

`pip install pulse-skills` installs core. `pip install pulse-skills[corpus]` adds the Voyage-based corpus. The runtime checks for these at corpus operations and prompts the operator if missing.

## Phase 1 — Foundation

**Goal**: A package that installs, has a CLI entry point, and can run `pulse help`.

### Tasks

1. Set up `pyproject.toml` with package metadata and Click as a dependency.
2. Create the package skeleton (directory structure above, empty `__init__.py` files).
3. Implement `pulse/cli.py` as the Click entry point. It should accept any verb as the first positional arg and dispatch to a stub.
4. Implement `pulse help` and `pulse help <command>` against a static command registry.
5. Implement the `pulse` (no verb) → router stub that just prints "Router not yet implemented."
6. Set up `pytest` and write smoke tests: `pulse help` exits 0; `pulse nonsense` exits 2 with helpful error; `pulse` with no args invokes the router stub.
7. Set up `ruff` and `mypy` configuration; pass both on the empty codebase.

### Done when

- `pip install -e .` succeeds in a clean venv.
- `pulse --version` prints the version.
- `pulse help` prints a help message (even if the command list is sparse).
- `pulse` with no args prints the router stub message.
- All tests pass; ruff and mypy are clean.

### Pitfalls

- **Don't try to make `pulse` shell out to a binary**. Click's group/command pattern handles the dispatch natively.
- **Resist the urge to start writing skills before the dispatcher is solid**. The dispatcher is the load-bearing piece; everything else plugs into it.

## Phase 2 — Workspace primitives and `pulse init`

**Goal**: An operator can run `pulse init`, get a working `~/.pulse/` directory, then `pulse workspace-new <id>` to create their first workspace.

### Tasks

1. Implement `pulse/runtime/workspace.py`:
   - Pydantic model for `Workspace` with all sections from Doc 02
   - Loading logic: read `workspace.yaml`, validate, cache
   - Path resolution helpers (atoms dir, runs dir, index path)
2. Implement `pulse/commands/init.py`:
   - Detect whether `~/.pulse/` exists; if so, prompt for clobber/abort
   - Create directory structure
   - Copy `default_assets/` contents to `~/.pulse/`
   - Prompt for global config: Claude API key, default workspace location
   - Prompt for corpus enablement (defer actual corpus install to phase 5)
   - Write `~/.pulse/config.yaml`
3. Implement `pulse/commands/workspace_new.py`:
   - Validate workspace ID format (lowercase, hyphens, no spaces)
   - Create workspace directory under `~/.pulse/workspaces/<id>/`
   - Stub out subdirectories (atoms, runs, position, ecosystem, etc.)
   - Write a minimal `workspace.yaml` with id, name, created timestamps
   - Initialize empty `.index.sqlite` with the schema from Doc 02
4. Implement `pulse/commands/workspace_list.py`, `workspace_switch.py`, `workspace_status.py` (basic version).
5. Implement `pulse/runtime/index.py`:
   - SQLite schema creation
   - Basic insert/query helpers for atoms, directions, hypotheses, factors, sources, runs
6. Implement `pulse/commands/reindex.py`:
   - Walk filesystem, rebuild index from scratch
   - Backup previous index before clobbering

### Done when

- Fresh `pulse init` on a clean machine completes successfully and creates `~/.pulse/` with the expected structure.
- `pulse workspace-new test-client` creates a workspace.
- `pulse workspace-list` shows it.
- `pulse workspace-switch test-client` sets it active.
- `pulse workspace-status` prints a minimal summary.
- `pulse reindex` rebuilds the SQLite index without errors.
- All operations are idempotent (rerunning doesn't break things) and have clear error messages on failure.

### Pitfalls

- **Don't hardcode `~/.pulse/`**. Use `Path.home() / ".pulse"` and respect a `PULSE_HOME` env var override for testing.
- **Atomically write `workspace.yaml`** (write to tempfile, fsync, rename) to avoid corruption on crash.
- **The SQLite schema from Doc 02 is canonical**. Don't add fields ad-hoc; if a schema change is needed, bump `schema_meta.version` and write a migration.

## Phase 3 — Skill loader and dispatcher

**Goal**: Skills declared as folders with `SKILL.md` get discovered, loaded, validated, and dispatched. Invoking `pulse <skill-name>` runs the skill.

### Tasks

1. Implement `pulse/runtime/skill.py`:
   - Parse `SKILL.md` frontmatter (YAML frontmatter via `python-frontmatter`)
   - Pydantic model for skill metadata
   - Validate against a canonical skill-frontmatter schema
   - Lazy loaders for `schema.input.yaml`, `schema.output.yaml`, templates, examples
2. Implement skill discovery: walk `~/.pulse/skills/` recursively, find every `SKILL.md`, build a registry indexed by skill name.
3. Update `pulse/dispatcher.py`:
   - Resolve verb to skill (or playbook, or built-in command)
   - Apply alias matching
   - Apply fuzzy matching with disambiguation prompt
4. Implement `pulse/runtime/llm.py`:
   - Wrapper around `anthropic` SDK
   - Auto-loads API key from config
   - Logs every request/response to the active run log
   - Handles streaming, retries, rate limits
5. Implement the basic skill execution flow:
   - Load skill
   - Validate inputs against `schema.input.yaml`
   - Load knowledge files declared in frontmatter
   - Begin run log
   - Execute the procedure (for v1, this means: load the SKILL.md procedure section as a prompt, send to Claude with the loaded context, capture response)
   - Validate outputs against `schema.output.yaml`
   - Write outputs to declared paths
   - Update SQLite index
   - Close run log
   - Print summary
6. Build the first three deterministic skills as proof of concept:
   - `pulse workspace-status` (deterministic, no LLM)
   - `pulse reindex` (deterministic, no LLM, already partially built in phase 2)
   - `pulse help` (already built, formalize it as a skill)
7. Build the first LLM-backed skill: `pulse set-identity` (single LLM call, simple structured output).

### Done when

- `pulse <skill-name>` resolves and executes any skill defined under `~/.pulse/skills/`.
- Adding a new skill is a matter of dropping a `SKILL.md` and schemas into the right folder; no code change needed.
- Frontmatter validation catches malformed skills with clear errors.
- The first LLM-backed skill (`pulse set-identity`) actually calls Claude and writes structured output to `workspace.yaml`.
- Run logs are written for every invocation.

### Pitfalls

- **Don't conflate skill loading with skill execution**. Loading should be cheap (just frontmatter); execution is the expensive part. Lazy-load everything declared in `knowledge:` and `uses_prompts:`.
- **The procedure section of SKILL.md is markdown for the LLM, not for code**. The runtime sends it as part of the prompt. Don't try to parse the numbered steps into code.
- **Validate output schemas before writing files**. A skill that writes a malformed file is worse than one that fails cleanly.

## Phase 4 — The router

**Goal**: `pulse` (no verb) launches the interactive router and walks the operator through the decision tree.

### Tasks

1. Implement `pulse/runtime/router.py`:
   - Parse `~/.pulse/router/tree.yaml`
   - Pydantic model for router nodes, options, guards, actions
   - Validate tree on load (every `next:` references an existing node, every `command:` references an existing skill)
2. Implement the tree walker:
   - Render prompt with numbered options (use `rich` for nice formatting)
   - Accept input: number, command name, escape, or fuzzy match
   - Evaluate guards before each prompt (use Jinja2 environment with workspace context)
   - Handle `next:`, `action: run_command`, `action: back`, `action: route_to`, `action: quit`
   - Maintain breadcrumbs for back navigation
   - Show confirmation screens for `run_command` actions that declare `confirm:`
3. Implement traversal logging:
   - Write each session to `~/.pulse/runs/router.log.jsonl`
   - Include: timestamp, workspace, path traversed, dispatched command, abandoned-at point, duration
4. Wire `pulse` (no verb) to invoke the router.
5. Implement first-run special handling: if `config.yaml` doesn't exist, skip the tree and show the init prompt.
6. Implement non-interactive detection (`stdin.isatty()` check); refuse with helpful message if not a terminal.
7. Author the v1 `tree.yaml` (full tree from Doc 06).

### Done when

- `pulse` launches the router and walks the tree.
- Numbered options work; short-circuit input works; fuzzy matching works.
- Guards correctly redirect or inform.
- Confirmation screens display before any expensive action.
- Ctrl-C at any prompt cleanly exits with confirmation.
- Traversal log captures every session.
- First-run prompt appears when no config exists.

### Pitfalls

- **Don't let the router silently dispatch**. Every command run from the router must show a confirmation screen if the command declares one. Numbered selection navigates to the prompt, not past it.
- **The Jinja2 environment for guards needs to be sandboxed**. Don't expose arbitrary Python; expose only the workspace, config, corpus, now, and today objects.
- **Test with a workspace that doesn't exist, a workspace that's brand new, and a mature workspace**. Guards behave differently in each state.

## Phase 5 — Corpus infrastructure (conditional)

**Goal**: When the operator chooses to enable the corpus at init, the framework installs LanceDB, configures the schema, and provides `pulse ingest` and `pulse corpus-query`.

This phase is conditionally relevant: if the operator skips corpus at init, this phase delivers `pulse enable corpus` instead, deferring the rest until the operator opts in.

### Tasks

1. Implement `pulse/runtime/corpus.py`:
   - Detect whether corpus is enabled (presence of `~/.pulse/corpus/index/`)
   - Load and validate `corpus/schema.yaml`
   - LanceDB connection management
   - Embedding provider abstraction (Voyage, OpenAI, Anthropic, local BGE)
   - Chunking utilities (paragraph-aware, configurable token target/overlap)
   - Metadata enforcement at ingestion
   - Query interface with structured filters
2. Update `pulse init` to handle corpus setup:
   - Prompt for corpus enablement
   - If yes: prompt for embedding provider; collect API key if needed; install optional dependencies via `pip install --user 'pulse-skills[corpus]'`; create corpus directory structure; write `schema.yaml`; initialize LanceDB
   - Show progress during install (it can take a minute)
3. Implement `pulse enable corpus` and `pulse disable corpus` for retroactive changes.
4. Implement the `pulse ingest` skill (from Doc 04):
   - Mode detection (file references, folder, URL, paste)
   - File type handling (PDF, DOCX, MD, TXT, HTML, transcripts)
   - Bucket selection
   - Per-file metadata prompts (with required-field enforcement from `schema.yaml`)
   - Cost estimation before commit
   - Confirmation
   - Chunking + embedding + indexing
   - Append to `ingestion-log.jsonl`
5. Implement the `pulse corpus-query` skill:
   - Accept query string
   - Accept structured filters (collection, framework, vertical, etc.)
   - Execute query, optionally with reranking
   - Display top results with full chunk text and metadata
6. Implement `pulse corpus-status`:
   - Show collection counts
   - Show last ingestion times
   - Show index size on disk
   - Surface any schema validation issues

### Done when

- A fresh `pulse init` with corpus enabled installs cleanly and produces a working LanceDB at `~/.pulse/corpus/index/`.
- `pulse ingest` accepts files, prompts for metadata, embeds, indexes, logs.
- `pulse corpus-query "..." --collection frameworks --framework hormozi` returns relevant chunks.
- `pulse enable corpus` and `pulse disable corpus` work retroactively.
- All corpus operations gracefully handle the case where corpus is disabled.

### Pitfalls

- **Don't make corpus mandatory anywhere**. Skills that benefit from corpus must declare `corpus_queries: ... optional: true` and have manual-authoring fallback paths. Test that the framework works end-to-end with corpus disabled.
- **Embedding cost is real**. Show it prominently before any ingestion that exceeds (say) $1.
- **LanceDB has a schema discipline**. Once a collection is created with certain fields, changing them requires migration. Get the schema right before bulk ingestion.
- **Optional deps are tricky**. If the operator chose corpus at init but the install failed, the framework needs to detect that and offer a path to fix it (`pulse enable corpus` should be re-runnable).

## Phase 6 — Kickoff skills

**Goal**: An operator can run `pulse onboard <workspace_id>` end-to-end and have a fully populated workspace.

### Tasks

1. Author `default_assets/knowledge/questionnaires/customer-profile.yaml` (full bank from Doc 07).
2. Author the other questionnaires: `offer-articulation.yaml`, `position-matrix.yaml`, `real-business.yaml`, `goals-and-constraints.yaml`.
3. Implement `pulse profile-customer`:
   - Walk the questionnaire tier by tier
   - Capture answers with confidence flags
   - Save incrementally
   - Build research queue from low-confidence fields
   - Write to `workspace.yaml`
   - Write research-queue items as atoms
4. Implement the other kickoff skills: `pulse set-identity`, `pulse articulate-offer`, `pulse set-goals`, `pulse set-position`.
5. Author the `default_assets/knowledge/frameworks/` files for all six frameworks (start with stubs; full authoring is a separate ongoing effort).
6. Implement `pulse map-ecosystem` (the first major discovery skill, ties together customer profile + framework knowledge + corpus queries if available).
7. Implement `pulse type-sources` (assigns strategic roles to URLs the operator provides).
8. Author `default_assets/playbooks/onboard.yaml` and validate it composes the kickoff skills correctly.
9. Write integration tests: full onboard flow from `pulse workspace-new` to `pulse workspace-status` showing a populated workspace.

### Done when

- `pulse onboard test-workspace` runs end-to-end (with operator interaction) and produces a fully populated `workspace.yaml`.
- The customer profile is rich enough that downstream skill outputs visibly improve when the profile is rich vs sparse.
- All kickoff skills are individually invocable (don't have to run the whole onboard playbook).
- Re-running `pulse profile-customer` offers refresh/deepen/start-over modes correctly.

### Pitfalls

- **The customer profile questionnaire is long. Don't accidentally make it feel longer**. Use clear section headers, show progress (e.g., "Tier 2 of 4, question 5 of 10"), allow saving and resuming. The operator should always know how much is left.
- **Don't anchor too hard on examples**. Show them, but in a clearly-marked dim style. Operators copy examples literally if you let them.
- **`workspace.yaml` is the truth**. Skills should never cache it; always re-read on each invocation. Operators may edit it manually between skill runs.

## Phase 7 — Operational skills and playbooks

**Goal**: An operator with an onboarded workspace can run `pulse weekly`, `pulse monthly`, `pulse quarterly` on cadence and get useful output every time.

### Tasks

1. Implement listen-layer skills:
   - `pulse extract` (the workhorse — given a list of sources and a window, extract atoms)
   - `pulse mine-reviews`
   - `pulse scan-ads`
2. Implement synthesis-layer skills:
   - `pulse propose-hypothesis`
   - `pulse score-signals`
   - `pulse update-directions`
   - `pulse find-commodity-pattern`
   - `pulse find-gaps`
3. Implement action-layer skills:
   - `pulse write-brief`
   - `pulse write-positioning`
   - `pulse draft-survey`
   - `pulse draft-outreach`
4. Implement reflect-layer skills:
   - `pulse audit-drift`
   - `pulse postmortem`
   - `pulse connect-source`
5. Implement knowledge-management skills:
   - `pulse author-knowledge`
   - `pulse refine-knowledge`
   - `pulse evolve-knowledge`
   - `pulse knowledge-status`
6. Implement framework-meta skills:
   - `pulse refine` (skill refinement notes)
   - `pulse evolve` (skill evolution from notes)
7. Implement `pulse/runtime/playbook.py` (full playbook runtime per Doc 05):
   - Sequential, foreach, when, switch, checkpoint, idempotency patterns
   - Include directive
   - Failure handling per declared policy
   - Run-log integration
8. Author `default_assets/playbooks/weekly.yaml`, `monthly.yaml`, `quarterly.yaml`, `reposition.yaml`.
9. End-to-end integration tests:
   - Full lifecycle: init → workspace-new → onboard → weekly → monthly → quarterly
   - Test against a fixture workspace with seeded sources and atoms
10. CLI polish:
    - Shell completion (`pulse --install-completion`)
    - `--dry-run` flag on playbooks
    - `--verbose` flag for diagnostic logging
    - `--output-format` flag where relevant

### Done when

- All 40 commands from Doc 04 are implemented.
- All five core playbooks run end-to-end against a populated test workspace.
- Idempotency keys correctly skip duplicate work within a day.
- Checkpoints in playbooks correctly pause and resume.
- A full integration test runs from cold start to quarterly review without error.
- The framework feels like a usable tool, not a demo.

### Pitfalls

- **The biggest risk in this phase is scope creep on individual skills**. Each skill should do its declared job and stop. The temptation is to make `pulse propose-hypothesis` also score signals, also update directions, also write a brief. Resist. One skill, one job.
- **Test with realistic atom volumes**. A workspace with 50 atoms is different from one with 5,000. Make sure synthesis skills work at both scales.
- **The playbook runtime is the most complex piece of code in the framework**. Spend extra care on testing — every composition pattern should have unit and integration coverage.
- **Don't over-prompt-engineer**. The skills' value comes from the structured procedure and accumulated knowledge, not from clever prompts. Simple, clear prompts that compose well are better than baroque single-shot prompts.

## Cross-phase concerns

A few things that span every phase:

### Logging discipline

Every skill invocation, every LLM call, every file write, every SQLite change is logged. The run log is the audit trail. If something goes wrong, the operator should be able to read the run log and understand what happened. Build the logging primitives in phase 2 and use them everywhere.

### Error messages

Errors should always state:
1. What was attempted
2. Why it failed
3. What the operator can do next

Bad: `Error: validation failed`
Good: `Error: workspace.yaml is missing the customer.primary_profile.descriptor field. Run \`pulse profile-customer\` to complete the customer profile, then retry this command.`

### Atomic writes

Any file write that could leave the workspace in an inconsistent state on crash should be atomic: write to tempfile, fsync, rename. This includes `workspace.yaml`, all atoms files, the SQLite index.

### Idempotency

Skills should be designed so that running them twice in a row is safe. Most kickoff skills offer refresh modes; most operational skills check idempotency keys; deterministic skills are naturally idempotent.

### Performance budgets

- Skill cold start: < 500ms (under fast skill loading + lazy knowledge loading)
- Workspace status: < 100ms (cached SQLite query)
- Weekly playbook end-to-end on a workspace with 30 sources: < 15 minutes
- Quarterly playbook on the same: < 75 minutes

If anything blows these budgets, profile and fix before shipping.

## Suggested phase ordering for the build agent

If you're a coding agent reading this, here's the suggested cadence:

1. **Phase 1**: 1 day. Foundation, no external dependencies.
2. **Phase 2**: 2 days. Workspace primitives, init, basic SQLite.
3. **Phase 3**: 3 days. Skill loader, dispatcher, first LLM-backed skill.
4. **Phase 4**: 2 days. Router. Less code than it looks; well-structured.
5. **Phase 5**: 3 days (if corpus enabled in build, otherwise skip). LanceDB integration, ingestion skill, query skill.
6. **Phase 6**: 4 days. Kickoff skills + customer profile questionnaire authoring.
7. **Phase 7**: 7 days. The bulk of the operational skills, all five playbooks, full integration tests.

Total: ~22 days at a steady pace. Compressible to ~14 if working aggressively in parallel on independent skills in phase 7.

## Final acceptance test

The framework is ready for v1 release when:

```bash
# Clean machine
pip install pulse-skills[corpus]

# First-time setup
pulse init
# (corpus enabled, Voyage selected, API keys provided)

# Create and onboard a workspace
pulse workspace-new my-test
pulse onboard my-test
# (operator walks through customer profile, offer, position, ecosystem)

# Ingest a few framework documents
pulse ingest
# (operator references a few PDFs, assigns to frameworks/hormozi, etc.)

# Run a weekly pass
pulse weekly
# (extracts from sources set up during onboarding, scores against any active hypotheses, writes weekly digest)

# Check status
pulse workspace-status
```

If this sequence runs cleanly with reasonable output at each step, v1 ships. Anything less is a bug to fix before release.
