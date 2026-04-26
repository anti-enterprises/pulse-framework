---
name: pulse extract
version: 1.0.0
description: Extract atoms from curated sources using multi-call LLM pipeline.
layer: listen
cadence: periodic
operator_time: "~10m"
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
outputs:
  atoms_created:
    description: "Count of new atoms written to atoms/"
  sources_processed:
    description: "Count of sources successfully processed"
runtime:
  confirms_before_commit: true
  concurrency: parallel
  max_duration_s: 900
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
Load `sources.yaml` and filter to active sources only.

## 2. Determine extraction window

Parse the `window` parameter (e.g., `last_7d`) into a concrete date range.
Skip sources whose `last_run` is more recent than the window start.

## 3. Fetch source content

For each active source, fetch new content since last extraction.
Respect rate limits and retry on transient failures.
Log fetch errors per source without aborting the batch.

## 4. Extract atoms per source (multi-call LLM)

For each source with new content, call the LLM to:
- Identify claims, stats, quotes, entities, and themes
- Tag each atom with type, entities, and relevant direction_ids
- Score relevance to workspace scope (drop below threshold)

Cap at `max_per_source` atoms per source.

## 5. Deduplicate

Compare new atoms against existing atoms in the workspace.
Drop exact or near-duplicate content (fuzzy match on content field).

## 6. Confirm with operator

Show summary: N sources processed, M atoms extracted, top themes.
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
