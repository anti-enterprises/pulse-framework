---
name: pulse map-ecosystem
version: 1.0.0
description: >
  Hormozi-style ecosystem mapping. Seeds the ecosystem from the customer
  profile (competitors, complementary products, trust voices, adjacent
  winners) and expands via web research. Produces a categorized list of
  ecosystem entities with strategic roles.
layer: discovery
cadence: one_time
operator_time: "~15m"
aliases: [ecosystem]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
    - pulse profile-customer
knowledge:
  - taxonomies/strategic-roles.yaml
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, customer)"
writes:
  - "workspace.yaml (sections: ecosystem)"
  - "ecosystem/*.yaml"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
  expand_via_web:
    type: boolean
    default: false
    description: "If true, use web search to expand the ecosystem beyond customer-profile seeds."
outputs:
  ecosystem:
    path: "ecosystem/"
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 600
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.4
  max_tokens: 6000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml`. Require `identity` and `customer` sections.
Extract seed data from the customer profile:

- `direct_competitors_known` -> seed `direct_competitor` entities
- `buys_before` / `buys_during` / `buys_after` -> seed `complementary` and `partner_candidate` entities
- `trust_voices` -> seed `trust_network` entities
- `adjacent_winners_inspiration` -> seed `adjacent_winner` entities
- `hangouts_online` / `hangouts_offline` -> seed `community_forum` entities
- `publications_read` / `podcasts_listened` -> seed `trust_network` entities

## 2. Load strategic roles taxonomy

Load `taxonomies/strategic-roles.yaml` to provide role definitions and
examples to the LLM.

## 3. Categorize seeds

For each seed entity from the customer profile, assign:
- **Name**: entity name
- **URL**: if known (many will be blank — operator fills in later)
- **Strategic role**: from the 10-role taxonomy
- **Notes**: why this entity matters to the ecosystem

Present the categorized list to the operator for review.

## 4. Expand (if requested)

If `expand_via_web` is true, use the LLM to suggest additional entities
the operator may have missed, based on:
- Industry analysis
- Competitor adjacency
- Common trust-network patterns

Present expansions separately, clearly marked as suggestions.

## 5. Operator review (interactive mode)

Show the full ecosystem map as a table grouped by strategic role:

```
Direct Competitors (4)
  - Gradient AI          [url pending]
  - Scale AI             https://scale.com
  ...

Trust Network (6)
  - Alex Hormozi         YouTube / Acquisition.com
  ...

Community Forums (3)
  - r/ExperiencedDevs    https://reddit.com/r/ExperiencedDevs
  ...
```

Let the operator add, remove, re-categorize, or add URLs.

## 6. Write ecosystem files

For each entity, write a YAML file to `ecosystem/<entity-slug>.yaml`:
```yaml
name: "Gradient AI"
url: "https://gradient.ai"
strategic_role: direct_competitor
source_kind: web_page
notes: "AI consulting competitor targeting SMBs"
discovered_via: customer_profile
added_at: 2024-01-15T10:00:00Z
```

## 7. Return summary

Print: "Ecosystem mapped for [workspace name]. [N] entities across [M] roles."
Show a role-count breakdown table.
Recommend next skill: `pulse type-sources`.
