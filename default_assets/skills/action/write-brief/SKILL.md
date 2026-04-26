---
name: pulse write-brief
version: 1.0.0
description: Generate content briefs from workspace intelligence for various cadences.
layer: action
cadence: periodic
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (recent atoms)"
  - "hypotheses/ (active hypotheses)"
  - "directions/ (active directions)"
writes:
  - "briefs/ (brief markdown file)"
inputs:
  workspace_id:
    type: string
    required: true
  kind:
    type: enum
    values: [weekly_digest, monthly_digest, quarterly_review, hypothesis_brief, direction_brief]
    required: true
    description: "Type of brief to generate"
outputs:
  brief_path:
    description: "Path to the generated brief markdown file"
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

Read `workspace.yaml` for identity, position, and goals.
Load relevant data based on brief kind.

## 2. Gather intelligence for brief kind

- **weekly_digest**: Atoms from last 7 days, hypothesis score changes, direction momentum shifts.
- **monthly_digest**: All weekly data plus trend analysis, new hypotheses, retired hypotheses.
- **quarterly_review**: Full workspace health, direction lifecycle, strategic position assessment.
- **hypothesis_brief**: Deep dive on a single hypothesis with all supporting/contradicting evidence.
- **direction_brief**: Direction trajectory, related hypotheses, and implications.

## 3. Generate brief (single-call LLM)

Send gathered intelligence to the LLM with instructions to produce:
- Executive summary (2-3 sentences)
- Key findings (bulleted)
- What changed since last brief of this kind
- Recommended actions (if applicable)
- Open questions

Format as clean markdown with appropriate headers.

## 4. Write brief

Write the brief to `briefs/{kind}-{date}.md`.
Include YAML frontmatter with metadata (kind, date, workspace_id).

## 5. Return summary

Print: Brief type, word count, path to generated file.
