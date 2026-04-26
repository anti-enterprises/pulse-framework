---
name: pulse evolve
version: 1.0.0
description: Review refinement notes on a skill and propose updates to its procedure or frontmatter.
layer: meta
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads:
  - "skills/ (target skill SKILL.md)"
writes:
  - "skills/ (updated SKILL.md)"
inputs:
  skill_name:
    type: string
    required: true
    description: "Name of the skill to evolve (e.g., listen/extract)"
outputs:
  changes_made:
    description: "Summary of changes applied to the skill"
runtime:
  confirms_before_commit: true
  concurrency: serial
  max_duration_s: 180
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

## 1. Load skill

Read the SKILL.md for the named skill.
Extract the `refinements` list from frontmatter.
If no refinement notes exist, exit early with a message.

## 2. Analyze refinements (single-call LLM)

Send the full SKILL.md and its refinement notes to the LLM.
Ask it to:
- Categorize notes (procedure change, frontmatter tweak, prompt update, taxonomy update)
- Propose specific edits to the skill
- Identify notes that conflict with each other
- Suggest a version bump (patch, minor, or major)

## 3. Present proposed changes

Show the operator each proposed change with rationale.
Let operator accept, reject, or modify each change.

## 4. Apply accepted changes

Update the SKILL.md with accepted changes.
Mark addressed refinements with `action` set to the appropriate value.
Bump version in frontmatter per the accepted bump level.

## 5. Write SKILL.md

Save the updated skill file.

## 6. Return summary

Print: N changes applied, version bumped to X.Y.Z, M notes addressed.
