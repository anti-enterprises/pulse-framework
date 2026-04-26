---
name: pulse propose-hypothesis
version: 1.0.0
description: Cluster unexplained atoms, name emerging patterns, and propose scored hypotheses.
layer: synthesis
cadence: weekly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (unlinked atoms)"
  - "hypotheses/ (existing hypotheses)"
  - "directions/ (active directions)"
writes:
  - "hypotheses/ (new hypothesis YAML files)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  hypotheses_proposed:
    description: "Count of new hypotheses created"
  clusters_found:
    description: "Count of atom clusters identified"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 900
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.4
  max_tokens: 4000
logs:
  include_prompts: true
  include_responses: true
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml` for identity, position, and active directions.
Load existing hypotheses to avoid re-proposing known patterns.

## 2. Gather unlinked atoms

Find atoms not yet linked to any hypothesis. These are the raw
signals that may contain emerging patterns.

## 3. Cluster atoms (multi-call LLM, pass 1)

Send batches of unlinked atoms to the LLM. Ask it to:
- Group atoms by thematic similarity
- Name each cluster with a short descriptive label
- Estimate cluster coherence (how tightly the atoms relate)

Drop clusters with fewer than 3 atoms or low coherence.

## 4. Generate hypothesis statements (multi-call LLM, pass 2)

For each viable cluster, call the LLM to:
- Draft a falsifiable hypothesis statement
- Identify which directions the hypothesis relates to
- Score initial confidence (0.0-1.0) based on evidence strength
- List what additional evidence would confirm or refute it

## 5. Deduplicate against existing hypotheses

Compare proposed hypotheses against existing ones.
Merge if a proposed hypothesis is substantially similar to an active one.

## 6. Review with operator

Show each proposed hypothesis with:
- Statement, confidence score, supporting atom count
- Related directions
- What would confirm/refute it

Let operator accept, reject, or edit each hypothesis.

## 7. Write hypothesis files

Write accepted hypotheses to `hypotheses/` as YAML files.
Link supporting atoms to the new hypothesis IDs.

## 8. Return summary

Print: N clusters found, M hypotheses proposed, K accepted.
