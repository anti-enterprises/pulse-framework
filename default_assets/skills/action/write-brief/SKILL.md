---
name: pulse write-brief
version: 1.0.0
description: Generate content briefs from workspace intelligence for various cadences.
layer: action
cadence: periodic
operator_time: "uncapped; varies by cadence scope"
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
    values: [daily_result, weekly_digest, monthly_digest, quarterly_review, hypothesis_brief, direction_brief]
    required: true
    description: "Type of brief to generate"
  cadence_window:
    type: string
    required: false
    description: "Concrete cadence window to summarize, e.g. last_24h, last_7d, last_30d, last_90d"
  analysis_depth:
    type: enum
    values: [daily, weekly, monthly, quarterly]
    required: false
    description: "Cadence-specific analysis depth"
  source_scope:
    type: string
    required: false
    default: eligible_active
    description: "Source scope represented by the brief"
  include_cadences:
    type: string
    required: false
    description: "Comma-separated cadence artifacts to load before writing"
  exclude_source_kinds:
    type: string
    required: false
    default: review_aggregator
    description: "Comma-separated source kinds excluded from source review"
  exclude_strategic_roles:
    type: string
    required: false
    default: review_aggregator
    description: "Comma-separated strategic roles excluded from source review"
  exclude_tags:
    type: string
    required: false
    default: software_reviews
    description: "Comma-separated tags excluded from source review"
outputs:
  brief_path:
    description: "Path to the generated brief markdown file"
runtime:
  confirms_before_commit: true
  concurrency: serial
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
Load relevant data based on brief kind. Always include the active inputs block
so the brief reflects the requested `kind`, `cadence_window`, `analysis_depth`,
`source_scope`, and review exclusions.

## 2. Gather intelligence for brief kind

- **daily_result**: Daily extraction result, source coverage, excluded review/software-review sources, new atoms, top trajectories, direction links, and followups for the last 24 hours.
- **weekly_digest**: Daily results from the last 7 days, atoms from the last 7 days, weekly source-sweep results, hypothesis score changes, direction momentum shifts, and repeated/source-supported clusters.
- **monthly_digest**: Daily and weekly results from the last 30 days, atoms from the last 30 days, monthly source-sweep results, trend analysis, commodity/gap updates, new hypotheses, retired hypotheses, and confidence changes.
- **quarterly_review**: Daily, weekly, and monthly results from the last 90 days, atoms from the last 90 days, quarterly source-sweep results, workspace health, direction lifecycle, drift audit, hypothesis postmortems, ecosystem refresh, and strategic position assessment.
- **hypothesis_brief**: Deep dive on a single hypothesis with all supporting/contradicting evidence.
- **direction_brief**: Direction trajectory, related hypotheses, and implications.

For weekly/monthly/quarterly, load lower-cadence artifacts before generating the
brief:
- weekly loads `briefs/daily/` artifacts and daily run logs in the 7-day window.
- monthly loads `briefs/daily/`, `briefs/weekly/`, and run logs in the 30-day window.
- quarterly loads `briefs/daily/`, `briefs/weekly/`, `briefs/monthly/`, and run logs in the 90-day window.

Respect the review exclusion policy in coverage notes: public review/software
review sources are excluded; forums/social/newsletters remain eligible.

## 3. Generate brief (single-call LLM)

Send gathered intelligence to the LLM with instructions to produce:
- Executive summary (2-3 sentences)
- Key findings (bulleted)
- What changed since last brief of this kind
- Recommended actions (if applicable)
- Open questions

Use cadence-specific depth:
- daily: concise source coverage and immediate high-signal changes.
- weekly: stronger week-level patterns and hypothesis movement.
- monthly: trend strength, commodity/gap implications, and confidence changes.
- quarterly: durable strategic shifts, drift, lifecycle decisions, and position implications.

Format as clean markdown with appropriate headers.

## 4. Write brief

Write the brief to the cadence directory:
- `daily_result` -> `briefs/daily/{date}-daily-result.md`
- `weekly_digest` -> `briefs/weekly/{date}-weekly-digest.md`
- `monthly_digest` -> `briefs/monthly/{YYYY-MM}.md`
- `quarterly_review` -> `briefs/quarterly/{YYYY}-Q{quarter}.md`
- other kinds -> `briefs/{kind}-{date}.md`

Include YAML frontmatter with metadata (kind, date, workspace_id).

## 5. Return summary

Print: Brief type, word count, path to generated file.
