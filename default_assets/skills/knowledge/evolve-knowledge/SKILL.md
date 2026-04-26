---
name: pulse evolve-knowledge
version: 1.0.0
description: Review refinement notes on a knowledge file and propose concrete updates.
layer: knowledge
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads:
  - "knowledge/ (target knowledge file with refinement notes)"
writes:
  - "knowledge/ (updated knowledge file)"
inputs:
  knowledge_path:
    type: string
    required: true
    description: "Path to the knowledge file to evolve"
outputs:
  changes_made:
    description: "Summary of changes applied to the knowledge file"
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

## 1. Load knowledge file

Read the knowledge file and extract the `## Refinement Notes` section.
If no refinement notes exist, exit early with a message.

## 2. Analyze refinement notes (single-call LLM)

Send the full knowledge file and its refinement notes to the LLM.
Ask it to:
- Group notes by theme (corrections, additions, clarifications, removals)
- Identify conflicting notes
- Prioritize changes by impact
- Propose specific edits to the knowledge content

## 3. Present proposed changes

Show the operator:
- Each proposed change with rationale
- Which refinement note(s) it addresses
- A diff-style preview of affected sections

Let operator accept, reject, or modify each change.

## 4. Apply accepted changes

Update the knowledge file content with accepted changes.
Remove addressed refinement notes from the `## Refinement Notes` section.
Bump the version in frontmatter.

## 5. Write file

Save the updated knowledge file.

## 6. Return summary

Print: N changes applied, M notes addressed, N notes remaining.
