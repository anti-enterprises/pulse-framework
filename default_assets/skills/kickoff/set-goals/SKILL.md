---
name: pulse set-goals
version: 1.0.0
description: >
  Set the goals block: primary goal, secondary goals, active bets,
  and constraints. Grounds the workspace's strategic direction so
  downstream skills know what to optimize for.
layer: kickoff
cadence: one_time
operator_time: "~10m"
aliases: [goals]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
    - pulse profile-customer
    - pulse articulate-offer
knowledge:
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, customer, offer)"
writes:
  - "workspace.yaml (sections: goals)"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
outputs:
  goals:
    path: workspace.yaml
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 300
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

Read `workspace.yaml`. Load identity, customer profile, and offer sections
for context. These inform what goals are realistic and relevant.

## 2. Gather primary goal

Ask the operator (if interactive):

> "What is the single most important outcome you want from this
> workspace over the next 90 days? Be specific — not 'grow revenue'
> but 'increase MRR from $X to $Y' or 'close 3 enterprise pilots.'"

If headless, infer from the offer and customer profile.

## 3. Gather secondary goals

Ask for 2-4 secondary goals that support or complement the primary:

> "What other outcomes matter? These are goals you'd pursue if the
> primary goal is on track, but would sacrifice if forced to choose."

## 4. Gather active bets

Ask for 1-3 active bets — experiments or initiatives with uncertain outcomes:

> "What bets are you currently running? Things you're trying that might
> not work but have high upside if they do."

Active bets are tracked separately because they need different evaluation
criteria than goals.

## 5. Gather constraints

Ask for key constraints as key-value pairs:

> "What constraints bound your strategy? Budget limits, team size,
> regulatory requirements, timeline commitments, technical debt."

Common constraint keys: `budget`, `team_size`, `timeline`, `regulatory`,
`technical`, `partnerships`.

## 6. Review with operator (interactive mode)

Show the drafted goals block:
- **Primary**: the main goal (bold)
- **Secondary**: bulleted list
- **Active bets**: bulleted list with uncertainty acknowledged
- **Constraints**: key-value table

Let the operator edit any field before confirming.

## 7. Write to workspace.yaml

Update the `goals:` section of `workspace.yaml` with the confirmed values.
Uses atomic writes.

## 8. Return summary

Print: "Goals set for [workspace name]."
Show the primary goal.
Recommend next skill: `pulse set-position`.
