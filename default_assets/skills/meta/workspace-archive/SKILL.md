---
name: pulse workspace-archive
version: 1.0.0
description: Move a workspace to the archive directory, preserving all data.
layer: meta
cadence: ad_hoc
operator_time: "~1m"
knowledge: []
reads:
  - workspace.yaml
writes:
  - "archive/ (moved workspace)"
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  archive_path:
    description: "Path to the archived workspace"
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

Read `workspace.yaml` to verify the workspace exists and get its name.

## 2. Validate preconditions

Check that:
- No playbooks are currently running for this workspace
- The workspace is not already archived

## 3. Confirm with operator

Show workspace summary (name, age, atom count, hypothesis count).
Ask: "Archive workspace [name]? This moves all data to archive/. [Y/n]"

## 4. Move workspace

Move the entire workspace directory to `archive/{workspace_id}/`.
Preserve directory structure and all files.

## 5. Update index

Remove the workspace from the active workspace index (`.index.sqlite`
or equivalent).

## 6. Return confirmation

Print: "Workspace [name] archived to [archive_path]."
