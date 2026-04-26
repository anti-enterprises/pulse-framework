---
name: pulse set-position
version: 1.0.0
description: >
  Set the position block: Robbins 4x2 matrix (person / business /
  industry / economy x season / lifecycle_stage) plus intention
  selection. Determines the strategic posture for all downstream skills.
layer: kickoff
cadence: one_time
operator_time: "~10m"
aliases: [position]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
    - pulse profile-customer
    - pulse articulate-offer
    - pulse set-goals
knowledge:
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, customer, offer, goals)"
writes:
  - "workspace.yaml (sections: position)"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
outputs:
  position:
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

Read `workspace.yaml`. Load all prior sections (identity, customer, offer,
goals) for context.

## 2. Explain the position matrix

Show the operator a brief explanation:

> The position matrix captures where you are across four dimensions,
> each with a **season** (spring / summer / autumn / winter) and a
> **lifecycle stage** (1-7).
>
> | Dimension  | What it captures                                    |
> |------------|-----------------------------------------------------|
> | Person     | You as the operator — energy, skill growth, runway   |
> | Business   | The business itself — product-market fit, revenue     |
> | Industry   | Your industry — growth phase, disruption cycle        |
> | Economy    | The macro environment — funding, spending, sentiment  |
>
> **Seasons**: spring (planting), summer (growth), autumn (harvest),
> winter (conserving).
>
> **Lifecycle stages**: 1 (pre-launch) through 7 (decline/exit).

## 3. Collect position for each dimension

For each of the four dimensions (person, business, industry, economy), ask:

> "What season is [dimension] in? (spring / summer / autumn / winter)"
> "What lifecycle stage? (1-7)"

Show contextual hints:
- **Person**: "Think about your personal energy, learning curve, and runway."
- **Business**: "Think about product-market fit, revenue trajectory, team state."
- **Industry**: "Think about whether your industry is growing, maturing, or disrupted."
- **Economy**: "Think about funding environment, customer spending, and market sentiment."

## 4. Select intention

Present the seven intentions with descriptions:

| Intention                   | When to use                                          |
|-----------------------------|------------------------------------------------------|
| `push_into_growth`          | Strong position, time to accelerate                  |
| `harden_foundations`        | Growth is happening but foundations are shaky         |
| `prepare_for_transition`    | A major shift is coming — new market, pivot, exit     |
| `experiment_aggressively`   | Low downside, high optionality — try many things      |
| `harvest`                   | Mature position, extract maximum value                |
| `pivot`                     | Current direction isn't working, change course        |
| `hold`                      | Uncertain environment, preserve optionality           |

Ask: "Given your position matrix, which intention best describes your
strategic posture for the next quarter?"

## 5. Review with operator (interactive mode)

Show the complete position block as a formatted matrix:

```
              Season    Stage
  Person      summer    4
  Business    spring    3
  Industry    summer    5
  Economy     autumn    4

  Intention: push_into_growth
```

Let the operator adjust before confirming.

## 6. Write to workspace.yaml

Update the `position:` section of `workspace.yaml`:
- `declared`: the 4x2 matrix
- `detected`: null (populated later by detection skills)
- `intention`: the selected intention
- `position_last_reviewed`: current timestamp

Uses atomic writes.

## 7. Return summary

Print: "Position set for [workspace name]. Intention: [intention]."
Recommend next skill: `pulse map-ecosystem`.
