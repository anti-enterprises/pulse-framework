---
name: pulse refine
version: 1.0.0
description: Append a refinement note to a skill's SKILL.md for later evolution.
layer: meta
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - "skills/ (target skill SKILL.md)"
writes:
  - "skills/ (updated SKILL.md)"
inputs:
  skill_name:
    type: string
    required: true
    description: "Name of the skill to refine (e.g., listen/extract)"
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

## 1. Locate skill

Find the SKILL.md file for the named skill.
Verify it exists and has valid frontmatter.

## 2. Parse frontmatter

Extract the `refinements` list from the YAML frontmatter.

## 3. Append refinement

Add a new entry to the `refinements` list:
```yaml
- date: 2026-04-24T00:00:00
  note: "<note text>"
  action: none
```

## 4. Write SKILL.md

Save the updated SKILL.md with the new refinement entry.

## 5. Return confirmation

Print: "Refinement note appended to skill [skill_name]."
