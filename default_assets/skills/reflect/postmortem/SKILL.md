---
name: pulse postmortem
version: 1.0.0
description: Conduct a hypothesis postmortem to capture learnings from confirmed or retired hypotheses.
layer: reflect
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "hypotheses/ (target hypothesis)"
  - "atoms/ (linked atoms)"
  - "directions/ (related directions)"
writes:
  - "reports/ (postmortem report)"
inputs:
  workspace_id:
    type: string
    required: true
  hypothesis_id:
    type: string
    required: true
    description: "ID of the hypothesis to review"
outputs:
  postmortem_path:
    description: "Path to the postmortem report"
runtime:
  confirms_before_commit: false
  concurrency: serial
  max_duration_s: 180
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 4000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load hypothesis and evidence

Read the target hypothesis from `hypotheses/`.
Load all supporting and contradicting atoms.
Load related directions and their trajectories.

## 2. Reconstruct the timeline

Build a chronological view of:
- When the hypothesis was proposed
- Key evidence that arrived over time
- Confidence score changes at each scoring run
- State transitions and when they occurred

## 3. Analyze outcome (single-call LLM)

Evaluate the hypothesis lifecycle:
- **If confirmed**: What was the strongest evidence? How long did confirmation take?
  Was the original statement accurate or did it evolve?
- **If retired**: Why was it retired? Was it wrong, or did conditions change?
  What early signals should have indicated the outcome sooner?
- **If contested**: What are the competing interpretations? What evidence
  would resolve the contest?

## 4. Extract learnings

Identify transferable insights:
- Source quality: Which sources provided the best evidence?
- Timing: How early could this have been detected?
- Blind spots: What was missed or underweighted?
- Process improvements: How could the synthesis pipeline improve?

## 5. Write postmortem

Write to `reports/postmortem-{hypothesis_code}-{date}.md`.

## 6. Return summary

Print: Hypothesis outcome, key learning, process recommendation.
