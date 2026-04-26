---
name: pulse add-source
version: 1.0.0
description: Add a single source manually to the workspace.
layer: discovery
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - sources/sources.yaml
writes:
  - sources/sources.yaml
inputs:
  workspace_id:
    type: string
    required: true
  url:
    type: string
    required: true
  label:
    type: string
    required: true
  kind:
    type: enum
    values: [web_page, rss, podcast, youtube, review_aggregator, ad_library, community_forum, social_platform, other]
    required: true
  strategic_role:
    type: enum
    values: [direct_competitor, substitute, complementary, partner_candidate, trust_network, community_forum, review_aggregator, ad_library, adjacent_winner, acquisition_target]
    required: true
outputs:
  source:
    path: sources/sources.yaml
    schema: schema.output.yaml
runtime:
  confirms_before_commit: false
  type: deterministic
  max_duration_s: 60
llm: {}
refinements: []
---

# Procedure

## 1. Validate inputs

Check URL format, verify source kind and strategic role are valid enum values.

## 2. Load existing sources

Read `sources/sources.yaml` if it exists.

## 3. Check for duplicates

If a source with the same URL already exists, warn and offer to update.

## 4. Create source entry

Generate a UUID, create the source record with provided fields,
set health to "healthy" and status to "active".

## 5. Write sources.yaml

Append the new source to sources/sources.yaml.

## 6. Update index

Insert the source into the SQLite index.

## 7. Print confirmation

"Source added: [label] ([strategic_role]) at [url]"
