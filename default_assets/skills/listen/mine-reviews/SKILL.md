---
name: pulse mine-reviews
version: 1.0.0
description: Mine review aggregators for customer insights and competitive intelligence.
layer: listen
cadence: periodic
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "sources.yaml (review_aggregator sources)"
writes:
  - "atoms/ (new atom YAML files)"
inputs:
  workspace_id:
    type: string
    required: true
  source_ids:
    type: array
    required: false
    description: "Specific source IDs to mine; defaults to all review_aggregator sources"
outputs:
  atoms_created:
    description: "Count of new atoms extracted from reviews"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 180
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

## 1. Load workspace and review sources

Read `workspace.yaml` for identity and customer profile context.
Filter `sources.yaml` to `kind: review_aggregator` sources.
If `source_ids` provided, further filter to those specific sources.

## 2. Fetch recent reviews

For each review source, fetch reviews since last extraction.
Capture review text, rating, date, and reviewer metadata where available.

## 3. Extract insights (single-call LLM)

Send the batch of reviews to the LLM with workspace context. Extract:
- Pain points and dissatisfactions (atom type: claim)
- Specific metrics or ratings mentioned (atom type: stat)
- Notable customer quotes (atom type: quote)
- Recurring themes across reviews (atom type: theme)
- Competitor mentions (atom type: entity)

Tag each atom with relevant direction_ids and hypothesis_ids.

## 4. Score and filter

Score each atom for relevance to workspace scope.
Drop atoms below the relevance threshold.

## 5. Write atoms

Write passing atoms to `atoms/` directory.
Update source `last_run` timestamps.

## 6. Return summary

Print: N reviews processed, M atoms created, top themes found.
