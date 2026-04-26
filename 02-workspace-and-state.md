# 02 — Workspace and State

The workspace is where per-client state lives. Every operator or engagement gets a workspace; skills read and write against it. This document defines the workspace structure, the `workspace.yaml` spine, the atom schema, the SQLite index, and how state flows through the framework.

## The workspace directory

```
~/.pulse/workspaces/<workspace_id>/
├── workspace.yaml                    # the spine
├── position/
│   ├── current.yaml
│   └── history/
│       ├── 2026-04-23.yaml
│       └── 2026-01-14.yaml
├── ecosystem/
│   ├── map.yaml                      # Hormozi ecosystem
│   ├── yellow-pages.yaml             # Abraham before/during/after
│   ├── trust-network.yaml            # Abraham trust network
│   ├── commodity-pattern.yaml
│   ├── gap-map.yaml
│   └── unique-mechanism.yaml
├── sources/
│   └── sources.yaml
├── pipelines/
│   └── pipelines.yaml
├── atoms/
│   └── 2026-04/                      # partitioned by month
│       └── atoms.jsonl
├── factors/
│   └── factors.yaml
├── directions/
│   ├── d-041.yaml
│   ├── d-017.yaml
│   └── [...]
├── hypotheses/
│   ├── h-0412.yaml
│   ├── h-0398.yaml
│   └── [...]
├── briefs/
│   ├── weekly/
│   │   └── 2026-04-23.md
│   ├── monthly/
│   └── quarterly/
├── surveys/
│   └── [...]
├── outreach/
│   └── [...]
├── field-notes/
│   └── [...]
├── runs/
│   └── 2026-04-23T14-22-00.jsonl
├── .credentials/                     # git-ignored
├── .index.sqlite                     # regenerable
└── .router-log.jsonl
```

Every subdirectory is optional and created on first use. A brand-new workspace after `pulse init --workspace <id>` has only `workspace.yaml` and empty subdirectories ready for population.

## The `workspace.yaml` spine

This is the single most load-bearing file in the framework. Every operational skill reads from it. Kickoff skills write to it. It is the complete declaration of who this workspace is, who it serves, what it's playing for, and how it operates.

```yaml
# Identity
id: anti-enterprise
name: Anti-Enterprise
industry: AI software and developer infrastructure
created: 2026-04-23T10:00:00Z
created_by: joe@geniusscaleai.com
last_touched: 2026-04-23T14:22:00Z

# Scope
scope_statement: >
  Anti-Enterprise is Joe's AI consulting and development MSP, serving
  AI-curious SMB founders (10-50 employees, $1M-$20M revenue) who
  want practical AI capability without enterprise overhead.

# What business are we really in
identity:
  declared_business: "AI consulting and development for SMBs"
  real_business: "Operator leverage and decision-making capacity for small-team founders"
  real_business_delta: >
    Customers describe value in terms of outcomes (decisions made, hours back),
    not methods (consulting, AI). Worth revisiting positioning next quarter.
  identity_last_reviewed: 2026-04-23

# Customer (from pulse profile-customer — this is the deep structure)
customer:
  primary_profile:
    descriptor: "AI-curious SMB founders, 10-50 employees, $1M-$20M revenue"
    
    demographics:
      role_titles: [Founder, CEO, Co-founder]
      company_stage: early_growth
      revenue_range_usd: "1M-20M"
      employee_range: "10-50"
      industries_served:
        - professional_services
        - e-commerce
        - b2b_saas
      geography_primary: US_Canada
      geography_secondary: [UK, AU]

    psychographics:
      worldview: >
        Skeptical of enterprise SaaS. Values operator leverage over team
        growth. Reads The Information, Stratechery, Hormozi.
      anxieties:
        - falling behind on AI
        - hiring mistakes
        - vendor lock-in
      aspirations:
        - build something durable
        - stay lean while growing revenue
        - avoid becoming "another SaaS"
      decision_style: fast_informed_skeptical
      status_signals:
        - subscribes to paid newsletters
        - attends ShopTalk / SaaStr / similar
        - active on X

    jobs_to_be_done:
      - job: "figure out which AI tools are worth adopting without wasting weeks evaluating"
        urgency: high
        frequency: monthly
      - job: "ship an AI-powered feature customers actually want"
        urgency: medium
        frequency: quarterly
      - job: "make sure our team doesn't fall behind"
        urgency: background
        frequency: continuous

    pain_points:
      - "can't evaluate AI vendor claims"
      - "tools don't integrate with our stack"
      - "team resistance or skepticism"
      - "budget pressure from leadership"

    current_solutions:
      - "ChatGPT Team subscriptions"
      - "internal scripts"
      - "hired ad-hoc consultants"
      - "trying tools from YC batches"

    trust_voices:
      - name: "Alex Hormozi"
        why: "pragmatic, operator-framed, anti-enterprise"
      - name: "Ben Thompson (Stratechery)"
        why: "strategic framing they trust"
      - name: "Marc Andreessen"
        why: "forward-looking, AI-optimistic"
      - name: "Patrick McKenzie (Patio11)"
        why: "SMB software intuition"

    hangouts:
      - "r/ExperiencedDevs"
      - "r/EntrepreneurRideAlong"
      - "SaaStr community"
      - "Lenny's Newsletter community"
      - "specific X accounts (@patio11, @sama, @sama)"
      - "Hormozi's Acquisition.com community"

    buys_before:
      - "CRM (Hubspot / Pipedrive)"
      - "analytics tools (Segment / Amplitude)"
      - "productivity (Notion / Slack / Linear)"

    buys_during:
      - "OpenAI / Anthropic API credits"
      - "vertical SaaS tools"
      - "outsourced bookkeeping / legal"

    buys_after:
      - "custom development contractors"
      - "AI infrastructure (Pinecone / Replicate)"
      - "more sophisticated observability tools"

# Offer (from pulse articulate-offer)
offer:
  core_promise: >
    AI-powered decision-making capacity in 30 days, or we keep working
    until it works.
  mechanism: >
    A 3-phase engagement: Audit (understand current leverage gaps),
    Architect (design AI-native workflows), Activate (build and hand off).
    Uses Claude as the primary reasoning substrate.
  pricing_model:
    structure: flat_fee_with_equity_option
    range_usd: "25000-75000"
    notes: "Typically flat fee. Equity option for the right aligned client."
  proof_assets:
    - "Case study: Turner Marketing System (publishing)"
    - "Case study: Faith Bridge AI revenue strategy"
    - "Code: Pulse Engine open-source framework"

# Goals and constraints (from pulse set-goals)
goals:
  primary: "Reach $2M ARR by Q4 2026"
  secondary:
    - "Ship Pulse Engine public beta by Q2"
    - "Close 3 anchor clients for framework distribution"
    - "Establish Anti-Enterprise brand as category-defining"
  active_bets:
    - "launch Pulse Engine beta"
    - "publish Anti-Enterprise manifesto"
    - "establish advisory / MSP hybrid positioning"
  constraints:
    team: "solo founder + 2 contractors"
    capital: "no outside capital in scope"
    time: "advisory hours capped at 25/week"

# Position (from pulse set-position — the Robbins matrix)
position:
  declared:
    person:
      season: summer
      lifecycle_stage: 4
    business:
      season: spring
      lifecycle_stage: 3
    industry:
      season: summer
      lifecycle_stage: 4
    economy:
      season: autumn
      lifecycle_stage: 7
  detected: null                       # populated by detection skills, may be null in v1
  intention: push_into_growth
  position_last_reviewed: 2026-04-23

# Operational configuration
config:
  active_playbooks:
    - pulse weekly
    - pulse monthly
    - pulse quarterly
  signal_scoring_weights:
    trust_network: 1.0
    direct_competitor: 1.2
    community_forum: 0.7
    ad_library: 0.8
  cadence:
    weekly_day: Monday
    weekly_time: "08:00"
    monthly_day: 1
    quarterly_months: [1, 4, 7, 10]
  notifications:
    run_summaries_to: stdout
    quarterly_review_reminders: true

# Integration references (corpus-local, v1 just metadata)
external_sources:
  - name: "EPIC & Abraham NotebookLM"
    kind: notebooklm
    url: "https://notebooklm.google.com/notebook/..."
    covers_frameworks: [abraham, frasier]
  - name: "Hormozi's App"
    kind: external_app
    covers_frameworks: [hormozi]
  - name: "DemandCurve NotebookLM"
    kind: notebooklm
    url: "https://notebooklm.google.com/notebook/..."
    covers_frameworks: [demandcurve]
  - name: "Imperium NotebookLM"
    kind: notebooklm
    url: "https://notebooklm.google.com/notebook/..."
    covers_frameworks: [imperium]

# Metadata
schema_version: 1
```

Every field in this file has a kickoff skill that populates it. The operator fills out sections in a sequence of skills, each writing to its section. After the kickoff playbook completes, `workspace.yaml` is fully populated and every operational skill can read what it needs.

## The atom schema

Atoms are the unit of observation in the framework. Every signal, every extracted claim, every field note, every corpus query result becomes an atom.

```typescript
interface Atom {
  // Identity
  id: string;                          // uuid
  workspace_id: string;
  
  // Source provenance
  source_kind: AtomSourceKind;         // enum, see below
  source_adapter: string;              // which module produced this (e.g., "extractor-news", "manual", "corpus-query")
  source_ref?: string;                 // ID in source system if applicable
  source_url?: string;                 // clickable link back to origin
  source_label?: string;               // display label (e.g., "acme.ai", "@sama · X")
  
  // Content
  type: AtomType;                      // enum: claim | stat | quote | entity | theme
  content: string;
  entities?: string[];                 // named entities referenced
  
  // Links to synthesis
  direction_ids?: string[];            // directions this atom contributes to
  factor_ids?: string[];               // factors this atom references
  hypothesis_ids?: string[];           // hypotheses this atom has been scored against
  
  // Timing
  observed_at?: string;                // when the content was originally observed (may differ from extracted_at)
  extracted_at: string;                // when this atom was created
  
  // Reserved for v2 curated internal-data atoms
  workspace_entity_refs?: {
    customer_id?: string;
    deal_id?: string;
    project_id?: string;
    [key: string]: string | undefined;
  };
}
```

### Atom source kinds (v1)

```yaml
# taxonomies/atom-source-kinds.yaml

extraction:
  description: "Produced by a listen skill from a scraped source."
  v1: true

authored:
  description: "Directly written into the workspace by the operator or a skill."
  v1: true

field_note:
  description: "Operator-pasted content: sales call transcripts, survey responses, JTBD interviews, customer emails."
  v1: true

corpus_query:
  description: "Retrieved from the local RAG corpus during authoring."
  v1: true

# Reserved for v2
db_query:
  description: "Retrieved from the curated business-intelligence database."
  v1: false
```

v1 only emits `extraction`, `authored`, `field_note`, and (when corpus is enabled) `corpus_query`. The `db_query` kind is reserved for v2. No other source kinds exist. There is no `crm_record`, no `support_ticket`, no `calendar_event`. This is deliberate — curated inputs only.

## The atoms directory

Atoms are written as append-only JSONL files, partitioned by month:

```
workspaces/<id>/atoms/
├── 2026-04/
│   └── atoms.jsonl
├── 2026-05/
│   └── atoms.jsonl
└── [...]
```

Each line is one atom as JSON. Files are append-only in normal operation — atoms aren't mutated after creation. If a correction is needed, write a new atom marking the old one superseded (via a `supersedes: <atom_id>` field in an extended schema if desired).

Why JSONL partitioned by month, not a database table:

- **Append-only writes** are safe under concurrent skill invocations (same skill running twice, or two skills triggered in parallel by a playbook). No locking required.
- **Partitioning by month** keeps files manageable. A prolific workspace producing 200 atoms a day would have ~6,000 per month — one file, fast to read.
- **Files are portable.** Backup with rsync. Inspect with `less`. Grep across months.
- **The SQLite index makes them queryable** without needing a proper database engine.

## The SQLite index

A single-file SQLite database at `workspaces/<id>/.index.sqlite` indexes everything in the workspace for efficient querying. It is always regenerable from the filesystem; the filesystem is the source of truth.

Key tables:

```sql
-- Atoms (mirror of JSONL files for queryability)
CREATE TABLE atoms (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL,
  source_adapter TEXT NOT NULL,
  source_ref TEXT,
  source_url TEXT,
  source_label TEXT,
  type TEXT NOT NULL,
  content TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  observed_at TEXT,
  entities TEXT,              -- JSON array
  direction_ids TEXT,         -- JSON array
  factor_ids TEXT,            -- JSON array
  hypothesis_ids TEXT,        -- JSON array
  source_file TEXT NOT NULL   -- which jsonl file this came from
);
CREATE INDEX atoms_extracted_at ON atoms(extracted_at);
CREATE INDEX atoms_source_kind ON atoms(source_kind);
CREATE INDEX atoms_type ON atoms(type);

-- Direction state snapshots
CREATE TABLE directions (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  title TEXT NOT NULL,
  state TEXT NOT NULL,
  momentum REAL,
  confidence REAL,
  atom_count INTEGER,
  age_days INTEGER,
  origin_date TEXT,
  last_updated TEXT NOT NULL,
  source_file TEXT NOT NULL
);
CREATE INDEX directions_state ON directions(state);

-- Hypothesis state snapshots
CREATE TABLE hypotheses (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  title TEXT NOT NULL,
  state TEXT NOT NULL,
  confidence REAL,
  age_days INTEGER,
  created_at TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  auto_generated INTEGER,
  source_file TEXT NOT NULL
);
CREATE INDEX hypotheses_state ON hypotheses(state);

-- Factors
CREATE TABLE factors (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  weight INTEGER,
  status TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  source_file TEXT NOT NULL
);

-- Sources
CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  label TEXT NOT NULL,
  kind TEXT NOT NULL,
  strategic_role TEXT NOT NULL,
  health TEXT NOT NULL,
  last_run TEXT,
  atom_count_last_run INTEGER,
  status TEXT NOT NULL
);
CREATE INDEX sources_strategic_role ON sources(strategic_role);
CREATE INDEX sources_health ON sources(health);

-- Run log (for observability)
CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  skill_name TEXT NOT NULL,
  playbook_name TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,       -- running | succeeded | failed | cancelled
  workspace_id TEXT NOT NULL,
  duration_ms INTEGER,
  error_message TEXT,
  knowledge_versions TEXT,    -- JSON map of framework-topic to version
  atoms_produced INTEGER,
  output_files TEXT           -- JSON array of paths written
);
CREATE INDEX runs_started_at ON runs(started_at);
CREATE INDEX runs_skill_name ON runs(skill_name);

-- Schema metadata
CREATE TABLE schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
INSERT INTO schema_meta (key, value) VALUES ('version', '1');
INSERT INTO schema_meta (key, value) VALUES ('last_rebuilt', '<timestamp>');
```

### Index maintenance

Every skill that writes files runs a post-hook that updates the relevant index tables. If the index gets out of sync (manual edits, crashed run, etc.), `pulse reindex` reads the filesystem and rebuilds from scratch:

```
$ pulse reindex

Rebuilding index for workspace: anti-enterprise
  Atoms:        12,847 rows indexed (2m 14s)
  Directions:   7 rows indexed
  Hypotheses:   23 rows indexed
  Factors:      6 rows indexed
  Sources:      30 rows indexed
  Runs:         342 rows indexed

Index rebuild complete. Backed up previous index to .index.sqlite.bak
```

## Run logs

Every skill invocation is logged. Two complementary places:

**`workspaces/<id>/runs/<timestamp>.jsonl`** — per-run JSONL file capturing structured events from the skill's execution. One line per event: skill started, step completed, LLM call made, atom written, file produced, skill finished.

**`.index.sqlite#runs` table** — summary row per run for queryability: "show me all `pulse map-ecosystem` runs in the last 30 days" is a SQL query, not a grep.

The per-run JSONL is the detailed trace. The SQLite row is the summary.

## Credentials

Credentials (API keys, tokens — for v1 that's primarily Claude API, and Voyage if using the corpus) are stored in `workspaces/<id>/.credentials/` or `~/.pulse/config.yaml` depending on whether they're workspace-scoped or global. The `.credentials/` directory is git-ignored by default. A `.gitignore` template at workspace creation ensures this.

v1 credential scope:

- **Global (`~/.pulse/config.yaml`)**: Claude API key, Voyage API key (if corpus enabled), embedding model preference
- **Workspace (`.credentials/`)**: none in v1. Reserved for v2 when operational integrations arrive.

## Workspace operations

A set of meta operations on workspaces themselves:

### `pulse init`

One-time framework setup. Creates `~/.pulse/` top-level structure, prompts for global config (Claude API key, corpus enablement, embedding provider). Doc 04 and Doc 10 cover this in detail.

### `pulse workspace-new <id>`

Creates a new workspace at `~/.pulse/workspaces/<id>/`. Stubs out the directory structure and a minimal `workspace.yaml`. Does not run onboarding — that's a separate explicit step (`pulse onboard <id>`).

### `pulse workspace-list`

Lists all workspaces with a quick summary: name, creation date, last touched, active hypothesis count, intention setting.

### `pulse workspace-switch <id>`

Sets the active workspace for subsequent commands. Operator can override per-command via a `--workspace` flag.

### `pulse workspace-status [<id>]`

Summary of workspace state: position health, source health, active hypotheses, directions by momentum, recent run log. This is what operators run when they open a workspace after a week away.

### `pulse workspace-archive <id>`

Moves a workspace to `~/.pulse/archive/` when an engagement ends. Keeps everything intact but removes it from active listings.

### `pulse reindex [<id>]`

Rebuilds the SQLite index from the filesystem. Safe to run anytime.

## State flow across skills

The typical flow for an operational skill (e.g., `pulse score-signals`):

```
1. Load workspace.yaml for identity/customer/position context
2. Load relevant knowledge files declared in skill frontmatter  
3. Query the workspace for inputs (active hypotheses, recent atoms)
4. Run procedure (load prompts, call Claude API, compose output)
5. Write output files (atoms, updated hypotheses)
6. Update SQLite index with new rows
7. Append run entry to runs/<timestamp>.jsonl and runs table
8. Return summary to operator
```

Every skill follows this shape. The discipline is enforced by the skill runtime — a skill that doesn't log its run or doesn't update the index is a bug.

## Workspace portability

Because everything is in the filesystem, workspaces are portable:

- **Backup**: `rsync` or `tar` the workspace directory.
- **Migration**: copy the directory to a new machine, run `pulse reindex` to rebuild the local SQLite index.
- **Sharing**: with care, directories can be shared with collaborators (git, or direct copy). Credentials in `.credentials/` should be excluded.
- **Archival**: move to `archive/` or to cold storage; restore by moving back.

The SQLite index is deliberately always regenerable. No data lives only in the index. This is what makes the framework durable against any future tooling changes.
