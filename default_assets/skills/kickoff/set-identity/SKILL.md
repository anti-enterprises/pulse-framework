---
name: pulse set-identity
version: 1.0.0
description: >
  Set the identity block of a workspace: declared business description,
  real business question (what business are you really in?), and scope
  statement.
layer: kickoff
cadence: one_time
operator_time: "~5m"
aliases: []
triggers:
  required_by_playbooks:
    - pulse onboard
    - pulse reposition
knowledge: []
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity)"
writes:
  - "workspace.yaml (sections: identity)"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
outputs:
  identity:
    path: workspace.yaml
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 180
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 2000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml`. Check if `identity` section already exists.
If it does, show the current values and ask if the operator wants to
update them.

## 2. Gather declared business

Ask the operator (if interactive):
"Describe what your business does in 1-2 sentences. What do you sell
or provide, and to whom?"

If headless, infer from workspace name and industry.

## 3. Ask the real business question

Ask the operator:
"What business are you *really* in? Not what you sell — what transformation
or outcome do you deliver? Think beyond the product."

This is the Hormozi 'real business' question. The gap between declared
and real is often where the most powerful positioning insights live.

## 4. Compute the delta

If the declared and real business differ meaningfully, note the delta:
what's the gap between what they say they do and what they really do?

## 5. Draft scope statement

Based on the declared business, real business, and workspace industry,
draft a one-sentence scope statement that defines the boundaries of
this workspace's intelligence gathering.

## 6. Review with operator (interactive mode)

Show the drafted identity block:
- declared_business
- real_business
- real_business_delta
- scope_statement (from workspace level)

Let the operator edit any field. Confirm before writing.

## 7. Write to workspace.yaml

Update the `identity` section of workspace.yaml with the confirmed values.
Set `identity_last_reviewed` to now.

## 8. Return summary

Print: "Identity set for [workspace name]. Declared: [declared_business].
Real: [real_business]."
