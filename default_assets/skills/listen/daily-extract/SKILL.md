---
name: pulse daily-extract
version: 1.0.0
description: Lightweight daily atom extraction — high-signal claims and stats only.
layer: listen
cadence: daily
operator_time: "~3m"
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
outputs:
  atoms_created:
    description: "Count of new atoms written to atoms/"
  sources_processed:
    description: "Count of sources successfully processed"
runtime:
  confirms_before_commit: true
  concurrency: parallel
  max_duration_s: 300
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
Load `sources.yaml` and filter to active sources only.

## 2. Determine extraction window

Parse the `window` parameter (default `last_24h`) into a concrete date range.
Skip sources whose `last_run` is more recent than the window start — nothing
new to fetch.

## 3. Fetch source content

For each active source, fetch new content since last extraction.
Respect rate limits and retry on transient failures.
Log fetch errors per source without aborting the batch.

## 4. Extract atoms (single-call LLM per source)

For each source with new content, make a **single LLM call** to:
- Extract only the atom types specified in `types` (default: claims and stats)
- Apply a **high relevance threshold** — keep only atoms with clear signal
- Tag each atom with type, entities, and relevant direction_ids
- Cap at `max_per_source` atoms per source

Unlike full `extract`, this uses one call per source (not multi-call) and
skips lower-signal atom types (quotes, entities, themes) by default.

## 5. Deduplicate (exact match, last 48h)

Compare new atoms against atoms extracted in the last 48 hours only.
Use exact content match (no fuzzy matching) for speed.
Drop duplicates silently.

## 6. Confirm, write, and return

Show summary: N sources processed, M atoms extracted, top signals.
Ask [Y/n] before writing.

On confirmation:
- Append each atom as one JSON line to `atoms/YYYY-MM/atoms.jsonl`
- Update source `last_run` timestamps in `sources.yaml`
- Run `pulse reindex` to make new atoms queryable
- Print extraction summary: sources processed, atoms created, any errors
