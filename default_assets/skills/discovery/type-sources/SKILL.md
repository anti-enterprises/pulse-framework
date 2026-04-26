---
name: pulse type-sources
version: 1.0.0
description: >
  Assign strategic roles to source URLs. Takes ecosystem entities or
  raw URLs and classifies them using the strategic-roles taxonomy.
  Enriches sources with metadata for downstream monitoring skills.
layer: discovery
cadence: ad_hoc
operator_time: "~10m"
aliases: [type-sources, classify-sources]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse map-ecosystem
knowledge:
  - taxonomies/strategic-roles.yaml
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, customer)"
  - "ecosystem/*.yaml"
writes:
  - "sources/*.yaml"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
  urls:
    type: array
    items:
      type: string
    required: false
    description: "Optional list of URLs to classify. If empty, processes ecosystem entities."
outputs:
  sources:
    path: "sources/"
    schema: schema.output.yaml
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 300
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.2
  max_tokens: 4000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace context and ecosystem

Read `workspace.yaml` for identity and customer context.
Read all files in `ecosystem/` to get the current ecosystem entities.

## 2. Identify sources to classify

If `urls` input is provided, use those. Otherwise, collect all ecosystem
entities that have URLs but haven't been classified as sources yet.

## 3. Load strategic roles taxonomy

Load `taxonomies/strategic-roles.yaml` for role definitions and examples.

## 4. Classify each source

For each URL/entity, determine:

- **Label**: human-readable name
- **Kind**: source kind (web_page, rss, podcast, youtube, review_aggregator,
  ad_library, community_forum, social_platform, other)
- **Strategic role**: from the 10-role taxonomy
- **Health**: initial health assessment (healthy / warning / degraded / broken)
- **Notes**: classification rationale

Classification uses the LLM with the strategic-roles taxonomy as context,
plus the workspace identity and customer profile to inform role assignment.

## 5. Operator review (interactive mode)

Show the classified sources as a table:

```
URL                          Label              Kind        Role               Health
https://gradient.ai          Gradient AI        web_page    direct_competitor   healthy
https://reddit.com/r/...     r/ExperiencedDevs  community   community_forum     healthy
https://g2.com/products/...  G2 - Category      web_page    review_aggregator   healthy
```

Let the operator adjust roles, labels, or skip entries.

## 6. Write source files

For each classified source, write a YAML file to `sources/<source-slug>.yaml`:
```yaml
id: "src-gradient-ai"
url: "https://gradient.ai"
label: "Gradient AI"
kind: web_page
strategic_role: direct_competitor
health: healthy
status: active
notes: "Direct competitor in AI consulting for SMBs"
```

## 7. Return summary

Print: "Typed [N] sources for [workspace name]."
Show a breakdown by strategic role and source kind.
