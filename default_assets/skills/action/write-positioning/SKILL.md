---
name: pulse write-positioning
version: 1.0.0
description: Draft a positioning statement grounded in workspace intelligence and market evidence.
layer: action
cadence: quarterly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "hypotheses/ (confirmed hypotheses)"
  - "directions/ (established directions)"
  - "ecosystem/ (gap map, commodity patterns)"
writes:
  - "positioning/ (positioning statement markdown)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  positioning_path:
    description: "Path to the generated positioning statement"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 180
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

## 1. Load workspace intelligence

Read `workspace.yaml` for identity, customer profile, offer, and position.
Load confirmed hypotheses, established directions, gap map, and
commodity pattern analysis.

## 2. Assess positioning inputs

Identify the key inputs for positioning:
- What the customer truly needs (from customer profile and hypotheses)
- Where the market is commoditizing (from commodity patterns)
- Where the white space exists (from gap map)
- What the workspace uniquely delivers (from identity and offer)

## 3. Draft positioning statement (single-call LLM)

Generate a positioning statement that includes:
- **For** [target customer segment]
- **Who** [key need or job-to-be-done]
- **We provide** [category or frame of reference]
- **That** [key differentiator]
- **Unlike** [competitive alternative]
- **We** [proof point or reason to believe]

Also generate:
- A one-sentence elevator pitch
- A one-paragraph positioning narrative
- Key proof points from evidence

## 4. Review with operator

Show the drafted positioning with supporting evidence.
Let operator edit any component before writing.

## 5. Write positioning

Write to `positioning/positioning-{date}.md` with YAML frontmatter.
Include evidence references and confidence notes.

## 6. Return summary

Print: Positioning summary, evidence strength, recommended next actions.
