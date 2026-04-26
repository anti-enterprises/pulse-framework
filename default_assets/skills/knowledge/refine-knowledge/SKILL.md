---
name: pulse refine-knowledge
version: 1.0.0
description: Append a refinement note to a knowledge file for later evolution.
layer: knowledge
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - "knowledge/ (target knowledge file)"
writes:
  - "knowledge/ (updated knowledge file)"
inputs:
  knowledge_path:
    type: string
    required: true
    description: "Path to the knowledge file to refine"
  note:
    type: string
    required: true
    description: "Refinement note to append"
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

## 1. Load knowledge file

Read the knowledge file at the specified path.
Verify it exists and has valid frontmatter.

## 2. Append refinement note

Add the note to a `## Refinement Notes` section at the end of the file.
Each note is prefixed with the current date in ISO format.

Format:
```
## Refinement Notes

- [2026-04-24] <note text>
```

If the section already exists, append to it.

## 3. Update frontmatter

Increment the refinement count in the frontmatter if tracked.

## 4. Write file

Save the updated knowledge file.

## 5. Return confirmation

Print: "Refinement note appended to [knowledge_path]."
