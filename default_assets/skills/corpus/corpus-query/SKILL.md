---
name: pulse corpus-query
version: 1.0.0
description: Ad-hoc CLI query against the corpus.
layer: corpus
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads: []
writes: []
inputs:
  query:
    type: string
    required: true
  collection:
    type: string
  top_k:
    type: integer
    default: 20
outputs: {}
runtime:
  type: deterministic
llm: {}
refinements: []
---

# Procedure

## 1. Accept query

Take query string from operator.

## 2. Execute search

Run vector search against corpus with optional collection filter.

## 3. Display results

Show top-K results with chunk text, metadata, and similarity score.
