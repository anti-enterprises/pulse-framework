---
name: pulse extract
version: 1.0.0
description: Extract atoms from eligible active sources using a cadence-depth LLM pipeline.
layer: listen
cadence: periodic
operator_time: "uncapped; varies by eligible source count"
knowledge: []
reads:
  - workspace.yaml
  - "sources.yaml (active sources)"
writes:
  - "atoms/YYYY-MM/atoms.jsonl (one JSON line per atom, append-only, monthly partition)"
inputs:
  workspace_id:
    type: string
    required: true
  window:
    type: string
    required: false
    default: last_7d
    description: "Time window for extraction (e.g., last_7d, last_30d)"
  max_per_source:
    type: integer
    required: false
    default: 50
    description: "Maximum atoms to extract per source"
  source_scope:
    type: string
    required: false
    default: eligible_active
    description: "Source scope to scan; eligible_active means all active sources except explicit exclusions"
  analysis_depth:
    type: enum
    values: [weekly, monthly, quarterly]
    required: false
    default: weekly
    description: "Cadence-specific extraction depth"
  include_cadences:
    type: string
    required: false
    default: weekly
    description: "Comma-separated cadence outputs to consider during synthesis"
  exclude_source_kinds:
    type: string
    required: false
    default: review_aggregator
    description: "Comma-separated source kinds to exclude"
  exclude_strategic_roles:
    type: string
    required: false
    default: review_aggregator
    description: "Comma-separated strategic roles to exclude"
  exclude_tags:
    type: string
    required: false
    default: software_reviews
    description: "Comma-separated tags to exclude"
  last_run_policy:
    type: enum
    values: [respect_last_run, ignore_lower_cadence]
    required: false
    default: respect_last_run
    description: "Whether lower-cadence runs should be allowed to suppress this cadence's window review"
outputs:
  atoms_created:
    description: "Count of new atoms written to atoms/"
  sources_processed:
    description: "Count of sources successfully processed"
runtime:
  confirms_before_commit: true
  concurrency: parallel
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.2
  max_tokens: 4000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace and sources

Read `workspace.yaml` to get identity, scope, and active directions.
Load `sources.yaml` and filter to the requested `source_scope`.

For `source_scope=eligible_active`, scan every active source except sources
matching the explicit review exclusions:
- `kind` in `exclude_source_kinds` (default: `review_aggregator`)
- `strategic_role` in `exclude_strategic_roles` (default: `review_aggregator`)
- any tag in `exclude_tags` (default: `software_reviews`)

Do not exclude forums, social platforms, newsletters, Reddit, YouTube, RSS, or
web pages merely because they contain sentiment. Forums remain eligible because
they reveal trending projects and trajectories. Treat `daily_slot` and `tier_0`
as priority metadata only, not inclusion gates.

There is no source-count or runtime cap: process all eligible sources, batching
only for rate limits and source-specific backoff.

## 2. Determine extraction window

Parse the `window` parameter (e.g., `last_7d`, `last_30d`, `last_90d`) into a
concrete date range.

For `last_run_policy=respect_last_run`, skip sources whose `last_run` is more
recent than the window start when there is no visible new content. For
`last_run_policy=ignore_lower_cadence`, do not skip a source merely because a
daily or weekly run updated `last_run`; review the cadence window and rely on
deduplication before writing atoms.

## 3. Fetch source content

For each active source, fetch new content since last extraction.
Respect rate limits and retry on transient failures.
Log fetch errors per source without aborting the batch.
Track coverage for every eligible source: processed, skipped as no-new-content,
excluded by review rule, or failed.

## 4. Extract atoms per source (multi-call LLM)

For each source with new content, call the LLM to:
- Identify claims, stats, quotes, entities, and themes
- Tag each atom with type, entities, and relevant direction_ids
- Score relevance to workspace scope (drop below threshold)

Cap at `max_per_source` atoms per source.

Apply cadence-specific depth:
- **weekly**: look for repeated/source-supported signals, week-over-week changes,
  strong single-source events, and clusters that can move hypothesis confidence.
- **monthly**: require stronger evidence. Prefer cross-source trends, meaningful
  contradiction/confirmation of hypotheses, pricing/category shifts, and changes
  that affect commodity/gap analysis.
- **quarterly**: keep only durable strategic signals, structural market movement,
  position drift evidence, hypothesis lifecycle evidence, and ecosystem changes.

Successively deeper cadences should produce fewer, stronger conclusions even
though they review all eligible sources.

## 5. Deduplicate

Compare new atoms against existing atoms in the workspace.
Drop exact or near-duplicate content (fuzzy match on content field).

## 6. Confirm with operator

Show summary: N sources processed, M atoms extracted, top themes.
Include lower-cadence inputs considered, excluded review/software-review source
counts, and source failures.
Ask [Y/n] before writing.

## 7. Write atoms

Append each atom as one JSON line to `atoms/YYYY-MM/atoms.jsonl` (where
`YYYY-MM` is the month of `extracted_at`). The file is append-only and
month-partitioned; a single monthly file accumulates many atoms across runs.
Each line must validate against the `Atom` schema in
`pulse/runtime/schemas.py`. Use `pulse.runtime.atoms.write_atom()` if calling
from Python; otherwise write the JSON directly with `model_dump_json()` form.

Update source `last_run` timestamps in `sources.yaml`.

After writing, run `pulse reindex` (or call `rebuild_index(workspace_id)`
directly) so the new atoms become queryable through the SQLite index.

## 8. Return summary

Print extraction summary: sources processed, atoms created, any errors.
