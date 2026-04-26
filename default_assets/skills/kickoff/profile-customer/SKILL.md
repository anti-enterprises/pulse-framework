---
name: pulse profile-customer
version: 1.0.0
description: >
  Walk the 4-tier customer profile questionnaire. Builds the foundational
  customer profile that every downstream Pulse skill draws on. Covers
  identity, psychology, jobs-to-be-done, and trust network.
layer: kickoff
cadence: one_time
operator_time: "~30m"
aliases: [customer-profile, profile]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
knowledge:
  - questionnaires/customer-profile.yaml
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: customer)"
writes:
  - "workspace.yaml (sections: customer)"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
  walk_mode:
    type: enum
    values: [fresh, refresh, deepen, start_over]
    default: auto
    description: "Override the walk mode. 'auto' detects from existing data."
  stop_after_tier:
    type: integer
    required: false
    description: "Stop after this tier number (1-4). Default is all tiers."
outputs:
  customer:
    path: workspace.yaml
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 1800
  type: questionnaire
  questionnaire_path: "questionnaires/customer-profile.yaml"
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

## 1. Preflight

Read `workspace.yaml`. Check if a `customer:` section already exists.

If it does, offer three modes:
- **Refresh**: walk all questions, showing current answers. Operator edits only what changed.
- **Deepen**: walk only questions where current answer is empty or low-confidence.
- **Start over**: blank slate, re-walk everything.

If the `walk_mode` input is set to something other than `auto`, use that mode directly.

## 2. Load questionnaire

Load `questionnaires/customer-profile.yaml` via the questionnaire walker
(`pulse.runtime.questionnaire.QuestionnaireWalker`).

Pass the existing customer profile answers (if any) as `existing_answers`.

## 3. Walk the questionnaire

The walker handles:
- Tier-by-tier progress display ("Tier 2 of 4, question 5 of 10")
- Confidence flags on every answer (high / medium / low / guessing)
- Incremental saves after every answer (crash-safe)
- Tier boundary checkpoints (summarize progress, offer to stop)
- Examples shown in dim style so operators don't anchor on them

If `stop_after_tier` is set, the walker stops after that tier.

## 4. Build the research queue

After the walk completes, collect all fields marked `low` or `guessing`
confidence. For each, generate a specific research suggestion:

| Low-confidence field             | Research suggestion                                          |
|----------------------------------|--------------------------------------------------------------|
| `hangouts_online`                | `pulse mine-reviews` on named competitor products            |
| `jobs_to_be_done`                | Run 3-5 JTBD interviews with recent customers               |
| `trust_voices`                   | Observe posts in named communities for 2 weeks               |
| `wish_list_items`                | `pulse scan-ads` on competitor categories                    |
| `pain_points`                    | Read 20 competitor reviews on G2 / Capterra                  |
| `direct_competitors_known`       | `pulse map-ecosystem` with web search                        |

## 5. Map answers to workspace schema

Flatten the questionnaire answers into the `CustomerProfile` Pydantic model:
- `descriptor` -> `customer.primary_profile.descriptor`
- `role_titles` -> `customer.primary_profile.demographics.role_titles`
- `company_stage` -> `customer.primary_profile.demographics.company_stage`
- ... (full mapping defined in customer-profile.yaml `writes_to` fields)

Set `low_confidence_fields` and `research_queue` on the profile.

## 6. Review with operator (interactive mode)

Show the complete profile in a formatted table. Let the operator
confirm before writing. In headless mode, write immediately.

## 7. Write to workspace.yaml

Update the `customer:` section of `workspace.yaml` with the new profile.
Uses atomic writes for crash safety.

## 8. Write research atoms

For each research-queue item, write an atom:
- `type: authored`
- `source_kind: authored`
- Content: the research suggestion text
- Tags: `research_to_do`, linked to the relevant field

## 9. Return summary

Print a completion summary with:
- Per-tier completeness bars
- Count of high-confidence vs low-confidence fields
- Research queue items
- Recommended next skill (`pulse articulate-offer`)
