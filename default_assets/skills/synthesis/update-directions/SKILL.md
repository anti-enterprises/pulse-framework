---
name: pulse update-directions
version: 1.0.0
description: Recompute direction momentum, trajectory, and state transitions.
layer: synthesis
cadence: weekly
operator_time: "~3m"
knowledge: []
reads:
  - workspace.yaml
  - "directions/ (all direction files)"
  - "atoms/ (recent atoms)"
  - "hypotheses/ (active hypotheses)"
writes:
  - "directions/ (updated direction files)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  directions_updated:
    description: "Count of directions with changed momentum or state"
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
  include_prompts: false
  include_responses: false
refinements: []
---

# Procedure

## 1. Load directions and recent atoms

Read all direction YAML files from `directions/`.
Load atoms created since the last direction update.

## 2. Count new evidence per direction

For each direction, count atoms linked to it since last update.
Compute the atom velocity (atoms per day) for each direction.

## 3. Compute momentum (deterministic)

Calculate momentum as a weighted average of:
- Recent atom velocity vs historical average
- Hypothesis confidence for linked hypotheses
- Time since last new atom (decay factor)

Momentum ranges from -1.0 (declining) to 1.0 (accelerating).

## 4. Determine state transitions (LLM-assisted)

For directions near state boundaries, use the LLM to evaluate:
- Should a nascent direction be promoted to emerging?
- Is an established direction showing signs of peaking?
- Has a direction gone stale (no new atoms in configured window)?

Apply the standard state machine: nascent -> emerging -> hardening ->
established -> peaking -> declining -> stale.

## 5. Update direction files

Write updated momentum, confidence, atom_count, and state to each
direction YAML file. Set `last_updated` to now.

## 6. Return summary

Print: N directions updated, state transitions, top movers.
