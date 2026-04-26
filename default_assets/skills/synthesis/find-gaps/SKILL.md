---
name: pulse find-gaps
version: 1.0.0
description: Gap-map synthesis identifying unserved needs and market white space.
layer: synthesis
cadence: monthly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (all atoms)"
  - "directions/ (active directions)"
  - "hypotheses/ (active hypotheses)"
  - "ecosystem/ (existing analyses)"
writes:
  - "ecosystem/ (gap map analysis)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  gap_map:
    description: "Gap map written to ecosystem/"
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

Read `workspace.yaml` for identity, customer profile, and offer.
Load all atoms, active directions, and hypotheses for context.
Load existing ecosystem analyses.

## 2. Map the served landscape (multi-call LLM, pass 1)

From competitive atoms and direction data, build a map of:
- What needs are currently well-served by competitors
- Which customer segments are actively targeted
- What solutions exist for each major job-to-be-done
- Which channels are saturated

## 3. Identify gaps (multi-call LLM, pass 2)

Cross-reference the served landscape with customer profile data:
- Unserved jobs-to-be-done
- Underserved customer segments
- Poorly solved pain points (high dissatisfaction in reviews)
- Missing integrations or workflows
- Price gaps (no offering at a price point customers want)
- Geographic or demographic gaps

## 4. Score gap attractiveness

For each gap, evaluate:
- Market size estimate (small, medium, large)
- Difficulty to serve (low, medium, high)
- Alignment with workspace identity and position
- Time to exploit (immediate, 3-6 months, 6-12 months)

## 5. Write gap map

Write the gap map analysis to `ecosystem/gap-map.yaml` with
gaps ranked by attractiveness score.

## 6. Return summary

Print: N gaps identified, top 3 opportunities, alignment with current direction.
