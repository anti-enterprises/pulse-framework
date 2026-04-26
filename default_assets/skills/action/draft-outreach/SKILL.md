---
name: pulse draft-outreach
version: 1.0.0
description: Generate outreach sequences informed by positioning, customer profile, and market intelligence.
layer: action
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads:
  - workspace.yaml
  - "positioning/ (current positioning)"
  - "hypotheses/ (confirmed hypotheses)"
writes:
  - "outreach/ (outreach sequence files)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  outreach_path:
    description: "Path to the generated outreach sequence"
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
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml` for identity, customer profile, and offer.
Load current positioning statement.
Load confirmed hypotheses for evidence-backed messaging.

## 2. Determine outreach parameters

From customer profile, extract:
- Target persona and role
- Communication preferences and channels
- Key pain points and triggers
- Language and tone markers

## 3. Generate outreach sequence (single-call LLM)

Produce a multi-touch outreach sequence with:
- **Touch 1**: Cold open -- lead with a relevant insight or pain point
- **Touch 2**: Value demonstration -- share a specific result or proof point
- **Touch 3**: Social proof -- reference trust voices or case evidence
- **Touch 4**: Direct ask -- clear CTA with low friction
- **Touch 5**: Breakup -- final value-add before closing the loop

Each touch includes: subject line, body, timing (days after previous),
channel, and the hypothesis/evidence backing the messaging.

## 4. Review with operator

Show the sequence with evidence annotations.
Let operator edit copy, adjust timing, or remove touches.

## 5. Write outreach sequence

Write to `outreach/sequence-{date}.yaml` with metadata.

## 6. Return summary

Print: N touches generated, target persona, key messaging angles.
