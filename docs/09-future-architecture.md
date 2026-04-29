# 09 — Future Architecture

This document defines what's reserved for v2, v3, and v4+ — and equally important, what v1 does to preserve optionality so those versions can land additively rather than requiring a rewrite.

## The principle

Each version of Pulse adds capability without invalidating earlier versions. A workspace built on v1 should run unchanged on v3 with new capabilities available but not required. A skill written for v1 should still work in v4. A playbook composed in v1 should still compose in v2.

This is enforceable only because v1 is deliberately conservative about what it commits to. Some surfaces are extensible from day one; others are explicitly reserved as future-only.

## v2 — Curated business-intelligence database

The v2 addition is a structured, query-only database for curated business intelligence.

### What it adds

A new `intel/` layer in the framework hierarchy:

```
~/.pulse/
├── skills/
├── playbooks/
├── knowledge/
├── corpus/
├── workspaces/
└── intel/                            # new in v2
    ├── schema/
    │   ├── markets.sql
    │   ├── benchmarks.sql
    │   ├── competitors.sql
    │   └── factors.sql
    ├── data/
    │   └── intel.sqlite
    ├── queries/
    │   ├── market-share-by-vertical.sql
    │   ├── benchmark-by-segment.sql
    │   └── ...
    └── README.md
```

The intel layer is a small SQLite database (or Postgres for operators who want it) populated by deliberate data entry — the operator types in market sizes, benchmarks, competitive metrics, factor timelines. Skills can query it via named, parameterized queries.

This is not a CRM connection. This is not a data warehouse sync. This is the operator's curated business intelligence, structured for reuse.

### The new atom source kind

In v1, `taxonomies/atom-source-kinds.yaml` reserves `db_query`:

```yaml
db_query:
  description: "Retrieved from the curated business-intelligence database."
  v1: false        # reserved for v2
```

In v2, this becomes a first-class source kind. Atoms produced by intel queries get this kind. Workspace skills can produce atoms by querying intel and binding the result.

### The new skill: `pulse intel-query`

```
$ pulse intel-query market-share-by-vertical \
    --vertical "AI consulting" \
    --year 2025

Result:
  vertical: AI consulting
  year: 2025
  total_market_size_usd: 8.4B
  growth_yoy: 0.42
  top_5_share_pct: 0.18
  fragmentation_index: 0.71
  source: industry-analyst-report-2025-q4
  last_updated: 2026-01-14
```

Named queries live in `intel/queries/` as SQL files with declared parameters. The operator (or skills) invokes them by name. Free-form SQL is not exposed at the CLI — only named queries — to maintain auditability and prevent the database from becoming a misuse vector.

### How intel relates to corpus

Two complementary backends:

- **Corpus** is unstructured (text chunks with metadata, queried by semantic similarity)
- **Intel** is structured (rows with typed columns, queried by SQL)

A skill needing to answer "what's the average ACV for B2B SaaS in the $5-20M segment?" should query intel (structured fact). A skill needing to answer "what does Hormozi say about pricing ladders?" should query corpus (semantic recall over text).

Both are curated, both are queried at authoring time (not runtime in the operational sense — though intel queries can also feed runtime synthesis when explicitly invoked).

### What v1 reserves for v2

- The atom source kind `db_query` is in the taxonomy file but flagged `v1: false`. Skills can't produce these atoms in v1.
- The command name `pulse intel-query` is reserved (Doc 04).
- The directory `~/.pulse/intel/` is reserved by convention; v1 won't create it but won't conflict if a future-aware operator pre-creates it.
- Workspace YAML extension: a top-level `intel:` block is reserved for per-workspace intel configuration (which queries are relevant, default parameters).

### What v2 will require from v1

- A clean atom-write path that accepts new source kinds without changing the core schema (already done in v1)
- A clean way for skills to declare dependencies on intel queries (extension of the `corpus_queries:` pattern in skill frontmatter)
- A clean upgrade path: `pulse upgrade-to-v2` should be idempotent and additive, never destructive

## v2.5 — RAG-assisted authoring enhancements

A smaller v2-era addition: improved corpus authoring workflow.

### What it adds

- **Hybrid retrieval**: combine vector similarity with BM25 keyword search for better recall
- **Query expansion**: automatic expansion of authoring queries via Claude before retrieval
- **Citation extraction**: when authoring a knowledge file from corpus chunks, automatically populate `_quotes.yaml` with attributable excerpts
- **Cross-reference detection**: identify when a new corpus document references a concept already in another knowledge file, prompting the operator to update both

### What v1 reserves

- `corpus/schema.yaml` declares `version: 1`. v2 schema can extend additively.
- The query interface in `pulse/runtime/corpus.py` exposes a single `query()` function with structured filters. v2 can add `query_hybrid()`, `expand_and_query()` without breaking v1 callers.
- The `_quotes.yaml` format already supports the metadata v2 will populate; v1 just doesn't auto-populate it.

## v3 — The emitters layer

The v3 addition is outbound action capability.

### What it adds

A new `emitters/` layer:

```
~/.pulse/
└── emitters/                         # new in v3
    ├── email/
    ├── calendar/
    ├── crm-write/
    ├── slack/
    └── README.md
```

Each emitter is a small adapter that knows how to draft and (with explicit human approval) send outbound messages. Examples:

- `pulse emit email --to <addr> --from-brief briefs/weekly/2026-04-23.md` — drafts an email from a weekly digest, opens it for review in `$EDITOR`, sends only on explicit confirm
- `pulse emit calendar --propose-block --based-on hypotheses/h-0412.yaml` — proposes a calendar block for investigative work on a hypothesis
- `pulse emit crm-write --update-deal <deal_id> --notes-from briefs/...` — appends structured notes to a CRM record

### The hard rule

Emitters are **outbound only and human-approval gated**.

- They never poll for inbound data
- They never contribute to the reasoning layer
- They draft, the human approves, then they send
- A failure to send is logged but never auto-retried with modified content

This preserves the curated-inputs principle. Emitters are how the framework affects the world; they are never a back door for the world to affect the framework.

### Why this is v3, not v2

The intel layer (v2) and the emitters layer (v3) are both important, but they have different risk profiles:

- Intel is read-only and operator-curated. Bugs are localized.
- Emitters affect external systems. Bugs can send wrong emails, double-book calendars, write garbage to CRM.

Emitters need a more mature framework foundation before being added. v2 hardens the intel pattern; v3 builds on that hardness to add the outbound capability.

### What v1 reserves

- The command name `pulse emit` and the namespace `pulse emit-*`
- The directory `~/.pulse/emitters/`
- A `permissions:` block in `config.yaml` reserved for v3 (controls which emitters are enabled)

### What v3 will require

- A robust skill-execution log (already in v1)
- A consistent confirmation pattern (already in v1, used by the router)
- A credential management layer better than v1's simple file-based approach (v3 will add OS-keychain integration)

## v4+ — Cross-workspace pattern detection and Pulse Engine integration

The v4 horizon is hazier. A few directions seem likely:

### Cross-workspace pattern detection

An operator running Pulse against many client workspaces accumulates structured intelligence across all of them. v4 adds skills that can observe across workspaces:

- "I've seen this commodity pattern in 8 different workspaces this quarter — likely a category-wide shift, not a per-client phenomenon"
- "The hypothesis 'X is becoming table-stakes' has hardened in 4 workspaces in 6 months — confidence is high; consider productizing the response"
- "Three workspaces in retail tech all show similar trust-network reorganization — cross-pollinate the response strategy"

Implementation: a `pulse portfolio` namespace with skills that query across workspaces (read-only, never writing across the boundary).

### Pulse Engine product integration

The Pulse Engine product (the position-aware industry listening platform with a UI) was always envisioned as eventually consuming this framework as its agent runtime. v4 formalizes that contract:

- The framework exposes a stable API (Python) that the product can call
- The product's frontend and dashboard consume framework outputs as structured data
- The framework continues to work standalone (CLI), but also serves as the engine for the product
- Authoring updates from the product flow back through the framework's ingestion paths

### Long-running listeners and webhooks

A future possibility — explicitly out of scope for v1-v3 — is operator-curated webhooks: declared endpoints the operator wires up that produce atoms when external events happen. Example: a webhook from a customer-success tool that fires when a high-value account churns, producing an atom typed `field_note` with operator-curated context.

This stays in the curated-inputs principle if and only if the operator deliberately wires it up and curates the schema. It's a v4+ consideration, not a near-term commitment.

## What v1 deliberately does NOT do (and why)

A list of things v1 could plausibly do but deliberately doesn't, with reasoning:

### No automatic CRM/PM/support sync

Operational data integrations are categorically rejected. The reason is the curated-inputs principle. The moment the framework starts ingesting raw operational data, the reasoning layer gets polluted with noise: incomplete CRM fields, stale ticket statuses, ambiguous calendar events. The operator stops trusting outputs because they reflect the noise.

The right architecture is curated inputs only. If an operator wants signal from their CRM, they should write a periodic skill that pulls a *specific*, *bounded*, *deliberately-shaped* extract — not a sync.

### No multi-user collaboration

v1 is single-operator. Workspaces are not designed for concurrent editing. Run logs assume one runner at a time. This dramatically simplifies the design.

A future v4+ could add multi-user support via locking, branching, or merge semantics. It's not impossible, just not in scope.

### No web UI

CLI only. The discipline of forcing every operation through a CLI keeps the framework composable, scriptable, and auditable. The Pulse Engine product is where the UI lives. The framework is the engine.

### No real-time daemons

No background processes polling sources, watching feeds, listening for webhooks. Skills run when invoked, period. This keeps operator intent in the loop and avoids the runaway-cost failure mode of polling-based systems.

### No ML model training

The framework doesn't train models on workspace data. It uses Claude (and possibly local embedding models) but never fine-tunes. This is deliberate: training requires data discipline the framework can't enforce.

If a v4+ wanted to add fine-tuning, it would need explicit, opt-in, per-workspace training with full data audit trails.

## Preservation-of-optionality checklist

For v1 implementation to preserve future-version optionality, these things must be true at v1 release:

1. **Atom schema** uses an enum for `source_kind` with a documented extension point. Adding `db_query` (v2), and other future kinds, requires only enum addition.

2. **Skill frontmatter** has a `version:` field and an `extensions:` reserved block for future fields without breaking v1 parsing.

3. **Playbook frontmatter** has the same `version:` and `extensions:` reservation.

4. **`workspace.yaml`** has `schema_version: 1` and a documented migration path. Adding sections (`intel:`, `emitters:`, etc.) doesn't break v1.

5. **`config.yaml`** is forward-compatible: unknown sections are preserved across writes, not stripped.

6. **The SQLite index** has `schema_meta` with `version` and `last_rebuilt`. Migrations are versioned and reversible.

7. **Run logs** include the framework version that produced them, for backward-compatible analysis.

8. **The router tree** has `version: 1` and supports unknown action types being parsed but flagged (so v2 nodes can sit in a v1 tree without crashing v1).

9. **The corpus schema** has `version: 1` and supports additive collection definitions.

10. **All filesystem paths** that v2/v3 will use (`intel/`, `emitters/`) are reserved by documentation, not by file creation. v1 doesn't create them; v1 doesn't conflict if they exist.

If all ten of these are true, v2 lands as `pulse upgrade --to v2` running additive migrations and dropping in new skills, with zero rewrites of v1 work.

## The trajectory in one paragraph

v1 ships a complete advisory tool: skills, knowledge, corpus, workspaces, playbooks, router. It's standalone-useful and commercially viable as an advisor's local toolkit. v2 adds curated business intelligence as a structured layer parallel to corpus, expanding what skills can ground in. v3 adds outbound action capability (emitters), letting the framework affect the world under human approval. v4+ adds cross-workspace observation, formal Pulse Engine product integration, and whatever the framework reveals it needs as it matures in real use. Each version is additive. Each version respects the curated-inputs principle. Each version preserves the operator's trust by never doing things they didn't deliberately authorize.

That's the long arc. v1 is the foundation that makes the whole arc possible.
