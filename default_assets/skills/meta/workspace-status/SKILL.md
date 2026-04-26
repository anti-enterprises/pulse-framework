---
name: pulse workspace-status
version: 1.0.0
description: Summary of workspace state -- position, sources, active hypotheses, recent runs.
layer: meta
cadence: ad_hoc
operator_time: "~30s"
knowledge: []
reads:
  - workspace.yaml
  - .index.sqlite
writes: []
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  text_summary:
    description: "Printed to stdout"
runtime:
  confirms_before_commit: false
  concurrency: parallel
  type: deterministic
llm: {}
logs:
  include_prompts: false
  include_responses: false
refinements: []
---

# Procedure

## 1. Load workspace

Read `workspace.yaml` and open `.index.sqlite`.

## 2. Compose summary

Build a summary string containing:
- Workspace name, id, age
- Position summary (intention, Robbins matrix)
- Active hypothesis count by state
- Direction count by state
- Source health summary
- Last 5 runs with timing

## 3. Print to stdout

Write the summary. No files produced. No atoms written.
