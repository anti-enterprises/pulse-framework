---
name: pulse scan-acquisitions
version: 1.0.0
description: "Frasier acquisition wheel: identify and score potential acquisition targets in the ecosystem."
layer: discovery
cadence: quarterly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (competitive and market atoms)"
  - "ecosystem/ (gap map, commodity patterns)"
  - "sources.yaml (all sources)"
writes:
  - "ecosystem/acquisition-targets.yaml"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  acquisition_targets_path:
    description: "Path to the acquisition targets YAML"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 900
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 6000
logs:
  include_prompts: true
  include_responses: true
refinements: []
---

# Procedure

## 1. Load workspace intelligence

Read `workspace.yaml` for identity, offer, goals, and position.
Load gap map and commodity pattern analyses from `ecosystem/`.
Load all sources, especially those tagged as `acquisition_target`.

## 2. Identify candidate categories (multi-call LLM, pass 1)

Based on the workspace's strategic position, identify acquisition
categories:
- **Capability fill**: Tools or teams that fill a gap in current offering
- **Customer access**: Companies with access to target customer segments
- **Technology**: Products with defensible technology advantages
- **Talent**: Teams with scarce expertise
- **Distribution**: Channels or platforms with existing reach
- **Competitive block**: Prevent competitors from acquiring

## 3. Score candidates (multi-call LLM, pass 2)

For each identified candidate or category, evaluate:
- Strategic fit (alignment with identity and goals)
- Market position (strength in their niche)
- Integration complexity (cultural and technical fit)
- Estimated effort (acquisition difficulty)
- Time sensitivity (is there competitive pressure?)

## 4. Rank and prioritize

Produce a ranked list of acquisition targets with:
- Company/product name and description
- Category and strategic rationale
- Fit score (0-10)
- Recommended next action (research, approach, monitor)

## 5. Write acquisition targets

Write to `ecosystem/acquisition-targets.yaml`.

## 6. Return summary

Print: N targets identified across M categories, top 3 recommendations.
