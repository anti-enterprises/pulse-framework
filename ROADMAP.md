# Pulse Skills Framework — Roadmap

Each version of Pulse adds capability without invalidating earlier versions. A workspace built on v1 runs unchanged on v3 with new capabilities available but not required. A skill written for v1 works in v4. A playbook composed in v1 still composes in v2. This is enforceable because v1 is deliberately conservative about what it commits to — schema versions, reserved directories, and extension points are all in place from day one.

## v2 — Curated business-intelligence database

A new `intel/` layer: a small SQLite (or Postgres) database populated by deliberate data entry — the operator types in market sizes, benchmarks, competitive metrics, factor timelines. Skills can query it via named, parameterized SQL queries. This is not a CRM connection or a data warehouse sync. This is the operator's curated business intelligence, structured for reuse.

**What it adds:**

- `~/.pulse/intel/` directory with schema definitions, data, and named queries
- `pulse intel-query` command: invoke named SQL queries with typed parameters, producing atoms of source kind `db_query`
- Structured data entry for market benchmarks, competitive metrics, and factor timelines
- Per-workspace intel configuration (which queries are relevant, default parameters)
- `pulse upgrade --to v2` idempotent migration

**How intel relates to corpus:** Corpus is unstructured (text chunks queried by semantic similarity). Intel is structured (rows queried by SQL). A skill needing "what's the average ACV for B2B SaaS in the $5-20M segment?" queries intel. A skill needing "what does Hormozi say about pricing ladders?" queries corpus.

## v2.5 — RAG authoring enhancements

Improved corpus workflow for knowledge authoring:

- **Hybrid retrieval:** combine vector similarity with BM25 keyword search for better recall
- **Query expansion:** automatic expansion of authoring queries via LLM before retrieval
- **Citation extraction:** auto-populate `_quotes.yaml` with attributable excerpts during knowledge authoring
- **Cross-reference detection:** identify when a new corpus document references a concept already in another knowledge file, prompting the operator to update both

## v3 — Emitters layer

Outbound action capability. A new `emitters/` layer with adapters that know how to draft and (with explicit human approval) send outbound messages.

**What it adds:**

- `~/.pulse/emitters/` directory with adapters for email, calendar, CRM, Slack
- `pulse emit email` — draft an email from a brief, open for review, send on confirm
- `pulse emit calendar` — propose a calendar block for investigative work on a hypothesis
- `pulse emit crm-write` — append structured notes to a CRM record
- OS-keychain credential management (replacing v1's file-based approach)
- `permissions:` block in `config.yaml` controlling which emitters are enabled

**The hard rule:** Emitters are outbound-only and human-approval gated. They never poll for inbound data. They never contribute to the reasoning layer. They draft, the human approves, then they send. This preserves the curated-inputs principle.

**Why v3 and not v2:** The intel layer (v2) is read-only and operator-curated — bugs are localized. Emitters affect external systems — bugs can send wrong emails or write garbage to a CRM. Emitters need a more mature framework foundation.

## v4+ — Portfolio and platform

### Cross-workspace pattern detection

An operator running Pulse against many workspaces accumulates structured intelligence across all of them. v4 adds a `pulse portfolio` namespace with skills that observe across workspaces (read-only, never writing across boundaries):

- "Commodity pattern detected in 8 workspaces this quarter — likely a category-wide shift"
- "Hypothesis X has hardened in 4 workspaces in 6 months — high confidence"
- "Three retail-tech workspaces show similar trust-network reorganization — cross-pollinate the response"

### Pulse Engine product integration

The Pulse Engine product (position-aware industry listening with a UI) consumes this framework as its agent runtime:

- Stable Python API for the product frontend
- Dashboard consuming framework outputs as structured data
- Authoring updates from the product flowing back through framework ingestion paths
- Framework continues to work standalone as a CLI

### Long-running listeners

A future possibility — operator-curated webhooks that produce atoms when external events fire. Example: a webhook from a customer-success tool that fires on high-value churn, producing an atom typed `field_note` with operator-curated context. Only viable if the operator deliberately wires it up and curates the schema.

## Deliberate non-goals

These are categorically rejected, not deferred. The reasoning is architectural, not resource-constrained.

**No automatic CRM/PM/support sync.** The moment the framework ingests raw operational data, the reasoning layer gets polluted with noise: incomplete CRM fields, stale ticket statuses, ambiguous calendar events. The operator stops trusting outputs. If an operator wants signal from their CRM, they should write a periodic skill that pulls a specific, bounded, deliberately-shaped extract — not a sync.

**No web UI.** CLI only. The discipline of forcing every operation through a CLI keeps the framework composable, scriptable, and auditable. The Pulse Engine product is where the UI lives. The framework is the engine.

**No real-time daemons.** No background processes polling sources or listening for webhooks. Skills run when invoked. This keeps operator intent in the loop and avoids the runaway-cost failure mode of polling-based systems.

**No ML model training.** The framework uses Claude and embedding models but never fine-tunes on workspace data. Training requires data discipline the framework cannot enforce.
