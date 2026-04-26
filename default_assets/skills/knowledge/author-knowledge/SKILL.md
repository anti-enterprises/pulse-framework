---
name: pulse author-knowledge
version: 1.0.0
description: Interactive authoring of a knowledge file from a chosen framework or topic.
layer: knowledge
cadence: ad_hoc
operator_time: "~15m"
knowledge: []
reads:
  - "knowledge/ (existing knowledge files)"
writes:
  - "knowledge/ (new knowledge markdown file)"
inputs:
  framework:
    type: string
    required: true
    description: "Framework or methodology name (e.g., hormozi-offer, jtbd, porter-five-forces)"
  topic:
    type: string
    required: true
    description: "Specific topic or angle within the framework"
outputs:
  knowledge_path:
    description: "Path to the authored knowledge file"
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

## 1. Check for existing knowledge

Scan `knowledge/` for existing files on the same framework/topic.
If found, show existing content and ask if operator wants to create
a new file or extend the existing one.

## 2. Outline the knowledge file (multi-call LLM, pass 1)

Generate a structured outline for the knowledge file:
- Core concepts and definitions
- Key principles or rules
- Application guidance (how Pulse skills use this knowledge)
- Common pitfalls
- References and further reading

Present the outline to the operator for approval or modification.

## 3. Draft content (multi-call LLM, pass 2)

For each section in the approved outline, generate content that:
- Is written for use by LLM prompts (clear, structured, unambiguous)
- Includes concrete examples where helpful
- Cross-references other knowledge files if relevant
- Stays within the framework's established terminology

## 4. Review with operator

Show the full draft. Let operator edit sections, request deeper
treatment of specific areas, or remove unnecessary content.

## 5. Write knowledge file

Write to `knowledge/{framework}-{topic}.md` with YAML frontmatter
containing framework, topic, version, and created date.

## 6. Return summary

Print: Knowledge file path, section count, word count.
