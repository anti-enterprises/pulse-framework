---
name: pulse scan-ads
version: 1.0.0
description: Scan ad libraries for competitive intelligence and messaging patterns.
layer: listen
cadence: periodic
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "sources.yaml (ad_library sources)"
writes:
  - "atoms/ (new atom YAML files)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  atoms_created:
    description: "Count of new atoms from ad analysis"
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

## 1. Load workspace and ad sources

Read `workspace.yaml` for identity, customer profile, and competitive context.
Filter `sources.yaml` to `kind: ad_library` sources.

## 2. Fetch active ads

For each ad library source, fetch currently running ads.
Capture ad creative text, headlines, CTAs, landing page URLs, and run dates.

## 3. Analyze ad patterns (single-call LLM)

Send ad data with workspace context to the LLM. Extract:
- Messaging themes and value propositions (atom type: theme)
- Specific claims made in ads (atom type: claim)
- Competitor positioning signals (atom type: entity)
- New offers or pricing changes mentioned (atom type: stat)
- Notable copy or hooks worth tracking (atom type: quote)

Tag atoms with direction_ids based on messaging alignment.

## 4. Detect changes

Compare against previously extracted ad atoms to identify:
- New messaging angles not seen before
- Retired messaging (ads no longer running)
- Spend pattern shifts (if data available)

## 5. Write atoms

Write new atoms to `atoms/` directory.
Update source `last_run` timestamps.

## 6. Return summary

Print: N ad sources scanned, M ads analyzed, K atoms created, key messaging shifts.
