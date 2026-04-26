---
name: pulse refine-router
version: 1.0.0
description: Append a refinement note to the router tree configuration for later tuning.
layer: meta
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - "router/ (router tree and notes)"
writes:
  - "router/ (updated notes file)"
inputs:
  note:
    type: string
    required: true
    description: "Refinement note for the router tree"
outputs:
  updated:
    description: "Confirmation that the note was appended"
runtime:
  confirms_before_commit: false
  concurrency: serial
  max_duration_s: 60
  type: deterministic
llm: {}
logs:
  include_prompts: false
  include_responses: false
refinements: []
---

# Procedure

## 1. Load router notes

Read the router refinement notes file at `router/refinement-notes.yaml`.
Create it if it does not exist.

## 2. Append note

Add a new entry:
```yaml
- date: 2026-04-24T00:00:00
  note: "<note text>"
  applied: false
```

## 3. Write notes file

Save the updated `router/refinement-notes.yaml`.

## 4. Return confirmation

Print: "Router refinement note appended. Total pending notes: N."
