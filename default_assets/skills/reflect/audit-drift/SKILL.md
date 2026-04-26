---
name: pulse audit-drift
version: 1.0.0
description: Analyze position drift between declared positioning and observed market signals.
layer: reflect
cadence: quarterly
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "positioning/ (current positioning)"
  - "atoms/ (recent atoms)"
  - "directions/ (active directions)"
  - "hypotheses/ (active hypotheses)"
writes:
  - "reports/ (drift report)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  drift_report_path:
    description: "Path to the drift analysis report"
runtime:
  confirms_before_commit: false
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

## 1. Load declared position

Read `workspace.yaml` for identity, position, and intention.
Load the most recent positioning statement from `positioning/`.

## 2. Gather observed signals

Load recent atoms, direction momentum changes, and hypothesis
confidence shifts. Build a picture of where the market is actually
pulling the workspace.

## 3. Detect drift (single-call LLM)

Compare declared positioning against observed signals to identify:
- **Message drift**: Are market signals contradicting the positioning?
- **Audience drift**: Are atoms showing traction with a different segment?
- **Value drift**: Is the market valuing different aspects than positioned?
- **Competitive drift**: Have competitors moved into the positioned space?
- **Intention drift**: Does current trajectory match the stated intention?

For each drift dimension, score severity (none, mild, moderate, severe).

## 4. Assess implications

For each detected drift, evaluate:
- Is this drift a threat or an opportunity?
- Should positioning be updated, or should execution be corrected?
- What evidence would confirm the drift is real vs. noise?

## 5. Write drift report

Write to `reports/drift-audit-{date}.md` with findings, severity
scores, and recommended actions.

## 6. Return summary

Print: Drift dimensions detected, overall severity, top recommendation.
