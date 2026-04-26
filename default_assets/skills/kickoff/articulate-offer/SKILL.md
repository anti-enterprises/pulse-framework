---
name: pulse articulate-offer
version: 1.0.0
description: >
  Build the offer block: core promise, mechanism, pricing model, and
  proof assets. Uses the customer profile and identity to draft a
  structured offer definition.
layer: kickoff
cadence: one_time
operator_time: "~10m"
aliases: [offer]
triggers:
  required_by_playbooks:
    - pulse onboard
  depends_on:
    - pulse set-identity
    - pulse profile-customer
knowledge:
  - glossary.yaml
corpus_queries: []
uses_prompts: []
reads:
  - "workspace.yaml (sections: identity, customer)"
writes:
  - "workspace.yaml (sections: offer)"
inputs:
  workspace_id:
    type: string
    required: true
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
outputs:
  offer:
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
  temperature: 0.4
  max_tokens: 3000
logs:
  include_prompts: true
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace context

Read `workspace.yaml`. Require that `identity` and `customer` sections exist.
If either is missing, abort with a message directing the operator to run
the prerequisite skill first.

## 2. Draft the offer block

Using the identity (declared business, real business) and customer profile
(pain points, JTBD, current solutions, switching friction), draft:

### Core Promise
One sentence: what transformation or outcome does the offer deliver?
Not what you sell — what the customer gets. Frame in the customer's language
(from `customer.primary_profile.psychographics.language`).

### Mechanism
How does the offer deliver on the promise? What's the system, method,
process, or technology? This is the "how it works" that builds credibility.

### Pricing Model
Structured as key-value pairs:
- `model`: how you charge (per_seat, per_project, retainer, usage_based, hybrid, etc.)
- `anchor_price`: the reference price or range
- `value_metric`: what the customer is really paying for (outcomes, hours, seats, etc.)
- `positioning`: premium, mid-market, value, or freemium

### Proof Assets
List of evidence that the promise is real:
- Case studies, testimonials, metrics, certifications, awards
- Even if sparse now — list what exists and what's needed

## 3. Review with operator (interactive mode)

Display the drafted offer block in a formatted panel:
- Core promise (bold)
- Mechanism (normal)
- Pricing model (table)
- Proof assets (bulleted list)

Let the operator edit any field. Flag fields where the LLM had to
guess (mark as low-confidence).

## 4. Write to workspace.yaml

Update the `offer:` section of `workspace.yaml` with the confirmed values.
Uses atomic writes.

## 5. Return summary

Print: "Offer articulated for [workspace name]."
Show the core promise and mechanism.
Recommend next skill: `pulse set-goals`.
