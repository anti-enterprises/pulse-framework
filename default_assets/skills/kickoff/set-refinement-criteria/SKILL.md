---
name: pulse set-refinement-criteria
version: 1.0.0
description: >
  Define refinement criteria for the workspace. Criteria guide automatic
  refinement heuristics and LLM-driven run analysis, telling Pulse what
  to watch for when skills execute.
layer: kickoff
cadence: one_time
operator_time: "~10m"
aliases: [refinement-criteria]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
    - pulse set-goals
knowledge:
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, goals)"
writes:
  - "refinement/criteria.yaml"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
outputs:
  criteria:
    path: refinement/criteria.yaml
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  type: llm_procedure
  idempotency_key: "refinement_criteria_set"
llm:
  model: anthropic/claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 3000
logs:
  collect_feedback: true
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml` and extract the `identity` and `goals` sections.
If either is empty, warn the operator but continue — criteria can be
generic until identity/goals are set.

## 2. Present default criteria templates

Show the operator four built-in categories with default criteria:

**Performance**
- Duration watchdog: Flag skills that exceed `max_duration_s` by > 50%
- Consecutive failure alert: Flag skills that fail 3+ times in a row

**Quality**
- Zero atom yield: Flag extraction skills that produce no atoms
- Missing output fields: Flag skills that omit declared output fields

**Coverage**
- Source freshness: Flag sources not scanned in 14+ days
- Ecosystem staleness: Flag if ecosystem map hasn't been refreshed in 30+ days

**Freshness**
- Direction momentum stale: Flag directions with no new atoms in 21+ days
- Hypothesis age: Flag hypotheses older than 60 days without state change

For each template, the operator can: enable (default), disable, or customize
the threshold/rule.

## 3. Collect custom criteria

Ask the operator if they have additional refinement criteria specific to
their business or workflow. Accept 0-5 custom criteria, each with:
- Name (short label)
- Description (what to watch for)
- Category: performance | quality | coverage | freshness | custom
- Target skills (empty = all skills)
- Rule (natural language description of when to fire)
- Severity: info | warning | critical

## 4. Confirm before writing

Display the full criteria list in a table and ask for confirmation.

## 5. Write criteria file

Create `refinement/criteria.yaml` in the workspace directory with the
confirmed criteria. Each criterion gets a generated ID in the format
`rc-<slugified-name>`.

## 6. Return summary

Print the number of criteria defined per category and the total.
