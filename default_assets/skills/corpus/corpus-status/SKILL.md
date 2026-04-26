---
name: pulse corpus-status
version: 1.0.0
description: Summary of corpus state.
layer: corpus
cadence: ad_hoc
operator_time: "~10s"
knowledge: []
reads: []
writes: []
inputs: {}
outputs: {}
runtime:
  type: deterministic
llm: {}
refinements: []
---

# Procedure

## 1. Check enablement

Report whether corpus is enabled.

## 2. Show collections

List collections with document/chunk counts.

## 3. Show index info

Display index size on disk, last ingestion time, embedding provider.
