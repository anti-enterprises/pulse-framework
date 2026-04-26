---
name: pulse score-signals
version: 1.0.0
description: Score new atoms against active hypotheses to update confidence levels.
layer: synthesis
cadence: periodic
operator_time: "~3m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (recent unscored atoms)"
  - "hypotheses/ (active hypotheses)"
writes:
  - "hypotheses/ (updated confidence scores)"
inputs:
  workspace_id:
    type: string
    required: true
  hypothesis_id:
    type: string
    required: false
    description: "Score against a specific hypothesis; defaults to all active"
outputs:
  atoms_scored:
    description: "Count of atoms scored"
  hypotheses_updated:
    description: "Count of hypotheses with updated scores"
runtime:
  confirms_before_commit: false
  concurrency: serial
  max_duration_s: 180
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.1
  max_tokens: 3000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace and hypotheses

Read `workspace.yaml` for scoring weight configuration.
Load active hypotheses (or the specific `hypothesis_id` if provided).

## 2. Gather unscored atoms

Find atoms created since the last scoring run that are not yet
linked to any hypothesis as supporting or contradicting evidence.

## 3. Score atoms against hypotheses (single-call LLM)

For each hypothesis, send the hypothesis statement and unscored atoms
to the LLM. For each atom, determine:
- Relevance to the hypothesis (0.0-1.0)
- Direction: supporting, contradicting, or neutral
- Strength of evidence: weak, moderate, or strong

## 4. Update hypothesis confidence

Recalculate hypothesis confidence using:
- Existing supporting/contradicting atom counts
- New atom scores weighted by evidence strength
- Apply workspace signal_scoring_weights if configured

## 5. Update state transitions

If confidence crosses a threshold, update hypothesis state:
- Below 0.2: consider retiring
- Above 0.8: promote to hardening/confirmed
- Contradicting evidence > supporting: mark as contested

## 6. Write updates

Update hypothesis YAML files with new confidence scores and atom links.
Mark scored atoms with hypothesis_ids.

## 7. Return summary

Print: N atoms scored, M hypotheses updated, any state transitions.
