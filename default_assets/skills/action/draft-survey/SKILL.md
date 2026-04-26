---
name: pulse draft-survey
version: 1.0.0
description: Generate JTBD survey questions grounded in workspace hypotheses and customer profile.
layer: action
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "hypotheses/ (active hypotheses)"
  - "directions/ (active directions)"
writes:
  - "surveys/ (survey YAML file)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  survey_path:
    description: "Path to the generated survey YAML"
runtime:
  confirms_before_commit: true
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

## 1. Load workspace context

Read `workspace.yaml` for customer profile and jobs-to-be-done.
Load active hypotheses that need validation.
Load active directions to ground questions in real signals.

## 2. Identify survey objectives

Determine what the survey should validate:
- Unconfirmed hypotheses that need customer input
- Low-confidence aspects of the customer profile
- Jobs-to-be-done priority ranking
- Pain point severity assessment
- Switching friction factors

## 3. Generate survey questions (single-call LLM)

Produce a JTBD-style survey with:
- Screening questions (ensure respondent fits target profile)
- Situation questions (when did you last [job]?)
- Motivation questions (what triggered the search?)
- Outcome questions (what does success look like?)
- Constraint questions (what stopped you from switching?)
- Ranking questions (prioritize these pain points)

Each question includes: text, type (open/scale/multiple_choice/ranking),
options (if applicable), and which hypothesis it validates.

## 4. Review with operator

Show the survey with question-to-hypothesis mappings.
Let operator add, remove, or edit questions.

## 5. Write survey

Write to `surveys/survey-{date}.yaml` with metadata.

## 6. Return summary

Print: N questions generated, hypotheses targeted, estimated completion time.
