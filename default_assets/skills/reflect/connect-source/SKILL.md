---
name: pulse connect-source
version: 1.0.0
description: Register an external knowledge source in the workspace configuration.
layer: reflect
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - workspace.yaml
writes:
  - "workspace.yaml (sections: external_sources)"
inputs:
  workspace_id:
    type: string
    required: true
  name:
    type: string
    required: true
    description: "Human-readable source name"
  kind:
    type: enum
    values: [notebooklm, external_app, book_collection, podcast, course, other]
    required: true
  url:
    type: string
    required: false
    description: "URL of the external source"
outputs:
  source_added:
    description: "Confirmation of the added source"
runtime:
  confirms_before_commit: true
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

## 1. Load workspace

Read `workspace.yaml` and locate the `external_sources` list.

## 2. Validate inputs

Check that:
- The source name is not already registered
- The kind is a valid value
- The URL (if provided) is well-formed

## 3. Append source

Add a new entry to `external_sources`:
```yaml
- name: <name>
  kind: <kind>
  url: <url>
  covers_frameworks: []
```

## 4. Write workspace.yaml

Save the updated workspace configuration.

## 5. Return confirmation

Print: "Source '[name]' ([kind]) registered in workspace [workspace_id]."
