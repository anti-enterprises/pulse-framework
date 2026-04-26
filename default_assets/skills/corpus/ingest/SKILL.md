---
name: pulse ingest
version: 1.0.0
description: Ingest files into the corpus with metadata tagging.
layer: corpus
cadence: ad_hoc
operator_time: "~5m"
knowledge: []
reads: []
writes: []
inputs:
  files:
    type: array
    required: true
    description: "File paths or URLs to ingest"
  collection:
    type: enum
    values: [frameworks, industry, case-studies, interviews, workspace-specific, misc]
    required: true
outputs: {}
runtime:
  confirms_before_commit: true
  type: llm_procedure
llm:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.1
  max_tokens: 2000
refinements: []
---

# Procedure

## 1. Detect input mode

Accept file paths, folder paths, URLs, or pasted text.

## 2. Parse files

For each input, detect file type (PDF, DOCX, MD, TXT, HTML) and
extract text content.

## 3. Prompt for metadata

For each file, prompt for required metadata fields based on the
selected collection (per corpus/schema.yaml).

## 4. Estimate cost

Calculate embedding cost based on total tokens and display prominently
if > $1.

## 5. Confirm

Show summary: N files, M total chunks, estimated cost. Ask [Y/n].

## 6. Chunk and embed

Split each document into chunks, embed via configured provider,
store in LanceDB.

## 7. Log ingestion

Append to corpus/ingestion-log.jsonl.
