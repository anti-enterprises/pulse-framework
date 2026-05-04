---
name: pulse daily-extract
version: 1.0.0
description: Daily eligible-source atom extraction — high-signal claims and stats only.
layer: listen
cadence: daily
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
    default: last_24h
    description: "Time window for extraction (e.g., last_24h, last_48h)"
  max_per_source:
    type: integer
    required: false
    default: 10
    description: "Maximum atoms to extract per source"
  types:
    type: string
    required: false
    default: "claim,stat"
    description: "Comma-separated atom types to extract (claim, stat, quote, entity, theme)"
  source_scope:
    type: string
    required: false
    default: eligible_active
    description: "Source scope to scan; eligible_active means all active sources except explicit exclusions"
  analysis_depth:
    type: enum
    values: [daily]
    required: false
    default: daily
    description: "Cadence-specific analysis depth"
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
  temperature: 0.1
  max_tokens: 2000
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
web pages merely because they contain sentiment. Forums remain part of the daily
review because they reveal trending projects and trajectories.

Treat `daily_slot` and `tier_0` as priority metadata only. They may influence
processing order, but they must not limit inclusion. There is no source-count or
runtime cap: process all eligible sources, batching only for rate limits.

## 2. Determine extraction window

Parse the `window` parameter (default `last_24h`) into a concrete date range.
Use last-24-hours/new-since-last-run content only. Skip a source only when its
`last_run` is more recent than the window start and there is no visible new item
to review. Do not perform historical backfill during daily runs.

## 3. Fetch source content

For each active source, fetch new content since last extraction.
For `kind: rss` sources with a non-empty `feed_url`, fetch `feed_url` with an
RSS/Atom parser and do not fetch the HTML `url` first. Only use HTML/Firecrawl
fallback for RSS sources that do not have `feed_url`.
Respect rate limits and retry on transient failures.
Log fetch errors per source without aborting the batch.
Track coverage for every eligible source: processed, skipped as no-new-content,
excluded by review rule, or failed.

## 4. Extract atoms (single-call LLM per source)

For each source with new content, make a **single LLM call** to:
- Extract only the atom types specified in `types` (default: claims and stats)
- Apply a **high relevance threshold** — keep only atoms with clear signal
- Tag each atom with type, entities, and relevant direction_ids
- Cap at `max_per_source` atoms per source

Unlike full `extract`, this uses one call per source (not multi-call) and
skips lower-signal atom types (quotes, entities, themes) by default. Daily
analysis should favor timely, directional signals over broad synthesis:
new launches, changed positioning, newly visible buyer pain, repeated forum
themes, strong stats, or source-corroborated shifts.

## 5. Deduplicate (exact match, last 48h)

Compare new atoms against atoms extracted in the last 48 hours only.
Use exact content match (no fuzzy matching) for speed.
Drop duplicates silently.

## 6. Confirm, write, and return

Show summary: N sources processed, M atoms extracted, top signals.
Include excluded review/software-review source counts separately from failures.
Ask [Y/n] before writing.

On confirmation:
- Append each atom as one JSON line to `atoms/YYYY-MM/atoms.jsonl`
- Use canonical atom `source_kind` values; RSS and web-page extractions write
  `source_kind: extraction`, with the specific adapter/source in
  `source_adapter` and `source_ref`
- Update source `last_run` timestamps in `sources.yaml`
- Run `pulse reindex` to make new atoms queryable
- Print extraction summary: sources processed, atoms created, any errors
