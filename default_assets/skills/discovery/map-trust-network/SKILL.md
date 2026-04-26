---
name: pulse map-trust-network
version: 1.0.0
description: "Abraham trust-network profiling: map the voices, platforms, and authorities your customers trust."
layer: discovery
cadence: quarterly
operator_time: "~10m"
knowledge: []
reads:
  - workspace.yaml
  - "atoms/ (trust-related atoms)"
  - "sources.yaml (trust_network sources)"
writes:
  - "ecosystem/trust-network.yaml"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  trust_network_path:
    description: "Path to the trust network YAML"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 900
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 6000
logs:
  include_prompts: true
  include_responses: true
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml` for customer profile, especially:
- trust_voices from customer profile
- publications_read, podcasts_listened, events_attended
- hangouts_online, hangouts_offline

Load trust_network sources from `sources.yaml`.

## 2. Gather trust signals (multi-call LLM, pass 1)

From atoms and source data, identify:
- Influencers and thought leaders mentioned or cited
- Platforms where target customers congregate
- Publications and media they consume
- Events and communities they participate in
- Peer voices they reference in decisions

## 3. Map trust hierarchy (multi-call LLM, pass 2)

Organize trust voices into tiers:
- **Tier 1 (Inner Circle)**: Direct advisors, close peers, personal network
- **Tier 2 (Trusted Authorities)**: Industry experts, analysts, known brands
- **Tier 3 (Community)**: Forums, groups, social platforms
- **Tier 4 (Ambient)**: Media, content creators, general industry noise

For each voice/platform, assess:
- Reach (how many of target customers it touches)
- Influence strength (how much it sways decisions)
- Accessibility (how easy to get featured or referenced)

## 4. Identify strategic opportunities

Flag trust network nodes where the workspace could:
- Build relationships (guest appearances, co-creation)
- Earn mentions (through proof assets or case studies)
- Monitor for early signals (add as listen sources)

## 5. Write trust network

Write to `ecosystem/trust-network.yaml` with the full map.

## 6. Return summary

Print: N trust voices mapped, tier distribution, top opportunities.
