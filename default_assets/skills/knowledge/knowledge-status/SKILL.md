---
name: pulse knowledge-status
version: 1.0.0
description: Summary of the knowledge layer -- files, frameworks covered, pending refinements.
layer: knowledge
cadence: ad_hoc
operator_time: "~30s"
knowledge: []
reads:
  - "knowledge/ (all knowledge files)"
writes: []
inputs: {}
outputs:
  text_summary:
    description: "Printed to stdout"
runtime:
  confirms_before_commit: false
  concurrency: parallel
  max_duration_s: 60
  type: deterministic
llm: {}
logs:
  include_prompts: false
  include_responses: false
refinements: []
---

# Procedure

## 1. Scan knowledge directory

List all files in `knowledge/`. Parse frontmatter from each.

## 2. Compile summary

Build a summary containing:
- Total knowledge files
- Frameworks covered (grouped by framework name)
- Files with pending refinement notes (count of notes per file)
- Last modified dates
- Total word count across all files

## 3. Print to stdout

Write the summary. No files produced.
