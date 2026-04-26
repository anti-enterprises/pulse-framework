---
name: pulse find-commodity-pattern
version: 1.0.0
description: "Hormozi commodity pattern detection: identify where the market is converging on sameness."
layer: synthesis
cadence: monthly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (competitive atoms)"
  - "directions/ (active directions)"
  - "ecosystem/ (existing analyses)"
writes:
  - "ecosystem/ (commodity pattern analysis)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  commodity_patterns:
    description: "Commodity pattern analysis written to ecosystem/"
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

## 1. Load workspace and competitive intelligence

Read `workspace.yaml` for identity and offer context.
Load atoms tagged with competitive entities or directions.
Load existing ecosystem analyses for context.

## 2. Identify commodity dimensions (multi-call LLM, pass 1)

Analyze competitive atoms to find dimensions where competitors
are converging:
- Pricing models becoming similar
- Feature sets reaching parity
- Messaging using identical language
- Delivery mechanisms becoming interchangeable
- Customer experience becoming undifferentiated

## 3. Score commodity risk per dimension (multi-call LLM, pass 2)

For each commodity dimension, score:
- Convergence rate (how fast competitors are becoming similar)
- Customer perception (do customers see a difference?)
- Switching cost (how easy is it to switch between competitors?)
- Defensibility (what structural advantages exist?)

## 4. Identify differentiation opportunities

For each high-risk commodity dimension, propose:
- Where the workspace can zig while others zag
- Underserved segments within the commodity space
- Adjacent value that competitors are ignoring

## 5. Write analysis

Write the commodity pattern analysis to `ecosystem/commodity-pattern.yaml`
including dimensions, scores, and differentiation opportunities.

## 6. Return summary

Print: N commodity dimensions found, top risks, key opportunities.
