# 03 — Skill Anatomy

A skill is a folder. This document defines the folder structure, the `SKILL.md` frontmatter schema, the procedure pattern, the I/O contract, and how the skill runtime loads and executes a skill.

## The folder layout

A skill is a directory under `~/.pulse/skills/<layer>/<name>/` containing at minimum:

```
skills/
└── discovery/
    └── map-ecosystem/
        ├── SKILL.md
        ├── schema.input.yaml
        ├── schema.output.yaml
        ├── templates/
        │   ├── output.md
        │   └── prompt.md           # optional, but common
        ├── examples/
        │   └── good-example.yaml
        └── hooks/
            └── post-run.py         # optional
```

- `SKILL.md` is the declaration and procedure. Required.
- `schema.input.yaml` and `schema.output.yaml` declare what the skill consumes and produces. Both required.
- `templates/` holds output structure templates and any skill-specific prompt templates. Cross-skill prompts live in `knowledge/prompts/`.
- `examples/` holds reference outputs used for calibration.
- `hooks/` holds post-run actions (index updates, notifications, etc.).

## The `SKILL.md` frontmatter

Every `SKILL.md` starts with YAML frontmatter declaring everything about the skill the runtime needs:

```yaml
---
# Identity
name: pulse map-ecosystem
version: 1.0.0
description: >
  Apply Hormozi's Ecosystem Mapping exercise to a workspace. Produces
  a structured list of 10-20 businesses the workspace's customers
  already buy from or attend to — including direct competitors,
  substitutes, complementaries, trust-network voices, and adjacent
  winners.

# Categorization (pedagogical only — the command is still `pulse map-ecosystem`)
layer: discovery
cadence: periodic          # once at kickoff; refreshed quarterly
operator_time: ~15m        # typical operator time when running interactively

# What invokes this skill
aliases: []                # alternate names (e.g., `pulse ecosystem`)
triggers:
  router_nodes:            # which router tree nodes land on this skill
    - discovery_ecosystem
  required_by_playbooks:
    - pulse onboard
    - pulse reposition

# Knowledge dependencies (loaded by runtime at execution time)
knowledge:
  - frameworks/hormozi/ecosystem-mapping.md
  - frameworks/abraham/yellow-pages.md
  - taxonomies/strategic-roles.yaml
  - questionnaires/customer-profile.yaml
  - examples/ecosystem-map/

# Corpus queries (v1 feature when corpus enabled; skill falls back gracefully if not)
corpus_queries:
  - collection: frameworks
    filters:
      framework: hormozi
      topic_tags: [ecosystem, commodity_pattern]
    optional: true         # skill runs fine without corpus

# Prompt templates
uses_prompts:
  - synthesis/ecosystem-prompt.md

# Workspace state dependencies (what the skill reads)
reads:
  - workspace.yaml (sections: identity, customer, offer)
  - ecosystem/map.yaml (optional; extends rather than replaces if present)

# Workspace state products (what the skill writes)
writes:
  - ecosystem/map.yaml
  - atoms/<current-month>/atoms.jsonl (appends new atoms)

# Input schema
inputs:
  workspace_id:
    type: string
    required: true
    description: "Target workspace"
  mode:
    type: enum
    values: [interactive, headless]
    default: interactive
    description: "Interactive asks operator for additions; headless infers from existing context only"

# Output schema
outputs:
  ecosystem_map:
    path: ecosystem/map.yaml
    schema: schema.output.yaml
    
# Runtime behavior
runtime:
  confirms_before_commit: true
  idempotency_key: "<workspace_id>:ecosystem_map:<YYYY-MM>"   # won't re-run same month unless --force
  concurrency: serial      # one at a time per workspace
  max_duration_s: 900
  
# Model
llm:
  provider: anthropic
  model: claude-opus-4-7
  temperature: 0.3
  max_tokens: 4000

# Observability
logs:
  include_prompts: true
  include_responses: false    # content of responses goes in output files, not logs

# Refinement notes (appended by pulse refine-knowledge)
refinements: []
---

# Procedure

[the skill procedure follows, as markdown]
```

Every field has a specific purpose. The runtime uses frontmatter to: load dependencies, check preconditions, enforce idempotency, provide observability, validate I/O.

## The procedure

The body of `SKILL.md` is a numbered procedure. Each step is a short paragraph describing what happens. Steps can be imperative (what the skill does) or interactive (what the skill asks the operator).

Example from `map-ecosystem`:

```markdown
# Procedure

## 1. Load workspace context

Read `workspace.yaml`. Verify `identity`, `customer.primary_profile`, 
and `offer` sections are populated. If any are missing, halt with 
message: "Cannot map ecosystem without customer profile. Run 
`pulse profile-customer <workspace_id>` first."

## 2. Load existing ecosystem (if any)

If `ecosystem/map.yaml` exists, load it. This skill extends rather 
than replaces — previous entries stay unless explicitly removed.

## 3. Apply Hormozi's three framing questions

Using the customer profile, ask (if interactive) or infer (if headless):

a. What do they buy — before, during, and after our product?
   Load Abraham's yellow-pages framework for the extension.

b. Where do they go — online and offline hangouts, communities, 
   publications, events?

c. Who else serves them — direct competitors, substitutes, anyone 
   with audience overlap?

In interactive mode, ask each question separately. Let the operator 
add as many candidates as they want per question. In headless mode, 
generate candidates from the customer profile and any available 
workspace atoms.

## 4. Classify strategic role for each candidate

For each candidate business/voice/publication/community, apply the 
strategic_roles taxonomy. Each candidate gets exactly one role. 
Pick the most useful lens.

The 10 roles are defined in `taxonomies/strategic-roles.yaml` and 
summarized here: direct_competitor, substitute, complementary, 
partner_candidate, trust_network, community_forum, review_aggregator, 
ad_library, adjacent_winner, acquisition_target.

## 5. Draft the map

Compose the output YAML per `schema.output.yaml`. For each entry:
name, optional URL, strategic_role, one-sentence rationale, 
discovered_on, discovered_via (which question surfaced it).

## 6. Review with operator (interactive mode only)

Show the drafted map. Let the operator:
- Edit any entry
- Remove entries
- Add entries manually
- Confirm the whole map

In headless mode, skip this step and commit the draft directly, 
logging that human review was bypassed.

## 7. Write ecosystem/map.yaml

Overwrite the existing file. Back up the previous version to 
`ecosystem/map.yaml.bak.<timestamp>`.

## 8. Write atoms

For each candidate that has a URL, write an atom of type `entity` 
with that URL in `source_url` and the rationale in `content`. 
Link each atom to the ecosystem map via an `ecosystem_entry_id` 
field in the atom's extended metadata.

## 9. Run post-run hook

Execute `hooks/post-run.py` which updates the SQLite index and 
logs the run.

## 10. Return summary to operator

Print: "Ecosystem map updated: N entries across K strategic roles. 
M new atoms written. Map saved to ecosystem/map.yaml."
```

Steps are deliberately narrative — the skill runtime is smart enough to parse numbered headings and follow them. This is not code; it's a procedure that the LLM executing the skill reads and enacts. The frontmatter gives the runtime what it needs programmatically; the procedure gives the LLM what it needs semantically.

## The I/O schemas

### `schema.input.yaml`

Formal schema of inputs. Used by the runtime to validate before execution.

```yaml
# Input schema for pulse map-ecosystem

$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
  - workspace_id
properties:
  workspace_id:
    type: string
    description: "Target workspace ID (must exist)"
  mode:
    type: string
    enum: [interactive, headless]
    default: interactive
  force:
    type: boolean
    default: false
    description: "Bypass idempotency key check"
```

### `schema.output.yaml`

Formal schema of outputs. Used to validate what the skill writes.

```yaml
# Output schema for ecosystem/map.yaml

$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
  - workspace_id
  - generated_at
  - entries
properties:
  workspace_id:
    type: string
  generated_at:
    type: string
    format: date-time
  generated_by_skill_version:
    type: string
  entries:
    type: array
    minItems: 1
    items:
      type: object
      required:
        - id
        - name
        - strategic_role
        - rationale
      properties:
        id:
          type: string
        name:
          type: string
        url:
          type: string
          format: uri
        strategic_role:
          type: string
          enum:
            - direct_competitor
            - substitute
            - complementary
            - partner_candidate
            - trust_network
            - community_forum
            - review_aggregator
            - ad_library
            - adjacent_winner
            - acquisition_target
        rationale:
          type: string
        discovered_on:
          type: string
          format: date
        discovered_via:
          type: string
          enum: [before, during, after, hangout, competitor, substitute, adjacent]
        framework_attribution:
          type: string
```

Why formal schemas: downstream skills (playbooks, composed workflows) can validate that they're consuming well-formed data. A skill that writes a malformed output is caught at the contract boundary, not at the consuming skill's failure point.

## Templates

### `templates/output.md`

The expected shape of the skill's output artifact, filled in via LLM generation or deterministic composition:

```yaml
# ecosystem/map.yaml — produced by pulse map-ecosystem

workspace_id: {{ workspace_id }}
generated_at: {{ timestamp }}
generated_by_skill_version: "1.0.0"

entries:
{% for entry in entries %}
  - id: {{ entry.id }}
    name: "{{ entry.name }}"
    url: "{{ entry.url }}"
    strategic_role: {{ entry.strategic_role }}
    rationale: "{{ entry.rationale }}"
    discovered_on: {{ entry.discovered_on }}
    discovered_via: {{ entry.discovered_via }}
    framework_attribution: "{{ entry.framework_attribution }}"
{% endfor %}
```

### `templates/prompt.md`

Skill-specific prompts that are tightly coupled to this skill. Cross-skill prompts (e.g., generic extraction prompts) live in `~/.pulse/knowledge/prompts/` and are referenced from frontmatter. Skill-local templates here are for procedure-specific LLM calls.

## Examples

Reference outputs that calibrate what "good" looks like for this skill:

```
examples/
├── ai-tools-example.yaml
├── dtc-beauty-example.yaml
└── service-b2b-example.yaml
```

The skill runtime can include examples in the LLM context during execution, especially in the early steps of the procedure where setting the right mental model matters. Frontmatter can indicate whether examples should be included automatically or only when asked.

## Hooks

Post-run hooks execute after the main procedure completes. Typical hooks:

### `hooks/post-run.py`

```python
"""
Post-run hook for pulse map-ecosystem.
Updates the SQLite index, logs the run, triggers any downstream alerts.
"""

import sqlite3
from pathlib import Path
from pulse.runtime import load_workspace, log_run

def run(workspace_id: str, output_paths: list[str], run_metadata: dict):
    workspace = load_workspace(workspace_id)
    
    # Update source count in index  
    conn = sqlite3.connect(workspace.index_path)
    # [...index updates specific to what this skill writes...]
    conn.commit()
    conn.close()
    
    # Log the run
    log_run(
        workspace_id=workspace_id,
        skill_name="pulse map-ecosystem",
        output_paths=output_paths,
        metadata=run_metadata,
    )
```

Hooks are plain Python. The framework provides a `pulse.runtime` module with workspace loading, run logging, and common utilities.

## How the runtime executes a skill

When `pulse map-ecosystem <workspace_id>` is invoked:

1. **Dispatch**. CLI dispatcher finds the skill (or playbook) by name.
2. **Load skill definition**. Parse `SKILL.md` frontmatter, load schemas, templates, examples.
3. **Validate inputs**. Check against `schema.input.yaml`.
4. **Check idempotency**. If frontmatter declares an idempotency key and it's been satisfied recently, either skip or prompt (`--force` bypasses).
5. **Check preconditions**. Verify workspace exists. Verify required workspace.yaml sections exist.
6. **Load knowledge files**. Lazy-load the files declared in `knowledge:`. Only load those referenced in the procedure step currently executing (lazy pattern).
7. **Run corpus queries if enabled**. Execute any declared corpus queries. If corpus disabled and queries are marked optional, continue. If required and disabled, halt.
8. **Load prompts**. Load declared prompt templates.
9. **Begin run log**. Open `workspaces/<id>/runs/<timestamp>.jsonl`. Insert `runs` row in SQLite with status=running.
10. **Execute procedure**. Step by step. Each LLM call logged. Each file write logged.
11. **Validate outputs**. Check outputs against `schema.output.yaml`.
12. **Commit outputs**. Write files. Update SQLite index.
13. **Run post-run hook**. Execute `hooks/post-run.py` if present.
14. **Close run log**. Update `runs` row with status=succeeded and timing data.
15. **Return summary**. Print to stdout.

On failure at any step: run log status=failed with error. Partial outputs are either rolled back (if the skill declares transactional) or left as-is with a clear log entry.

## Skill versioning

Skills are versioned via `version:` in frontmatter (semver). The version is captured in every run log, so you can later ask "which version of `pulse map-ecosystem` produced this ecosystem map?"

Version bumps happen when:

- **Patch** (0.0.X): prompt tuning, template refinement, documentation edits
- **Minor** (0.X.0): new optional inputs, new optional outputs, new procedure steps
- **Major** (X.0.0): breaking changes to I/O schema, renaming, significant procedure changes

The skill registry tracks version history in `skills/<name>/VERSIONS.md` (optional but recommended for actively-refined skills).

## Refinement notes in the skill itself

The `refinements:` array in frontmatter accumulates dated observations about the skill's behavior in real use:

```yaml
refinements:
  - date: 2026-04-30
    note: "When running on service businesses, step 3a ('what do they buy before?') surfaces generic answers. Consider splitting to service-business variant."
    action: none
  - date: 2026-05-14
    note: "Strategic role classification too permissive — too many entries land as 'trust_network'. Tightened definition in taxonomies file."
    action: taxonomy_updated
    version_bumped: 1.0.0 → 1.0.1
```

These are added by `pulse refine <skill-name>` and periodically converted into actual procedure updates by `pulse evolve <skill-name>`.

## The skill runtime library

A Python package `pulse.runtime` provides the primitives skills use. Key exports:

```python
from pulse.runtime import (
    load_workspace,        # -> Workspace object
    load_skill,            # -> Skill object
    load_knowledge,        # load a knowledge file by path
    query_corpus,          # query the corpus with structured filters
    call_llm,              # unified LLM call with logging
    write_atom,            # append to atoms.jsonl + index
    write_yaml,            # write YAML file with schema validation
    update_index,          # SQLite index update
    log_run,               # run log entry
    workspace_ref,         # resolve workspace path
)
```

This is what skill authors import from. Skills don't do low-level filesystem or API work — they use the runtime library.

## A complete minimal skill example

For reference, the simplest possible skill — `pulse workspace-status`:

```
skills/meta/workspace-status/
├── SKILL.md
├── schema.input.yaml
└── schema.output.yaml
```

`SKILL.md`:

```markdown
---
name: pulse workspace-status
version: 1.0.0
description: Summary of workspace state — position, sources, active hypotheses, recent runs.
layer: meta
cadence: ad_hoc
operator_time: "~30s"
knowledge: []
reads:
  - workspace.yaml
  - .index.sqlite
writes: []
inputs:
  workspace_id:
    type: string
    required: true
outputs:
  text_summary:
    description: "Printed to stdout"
runtime:
  confirms_before_commit: false
  concurrency: parallel
llm: {}
---

# Procedure

## 1. Load workspace

Read `workspace.yaml` and open `.index.sqlite`.

## 2. Compose summary

Build a summary string containing:
- Workspace name, id, age
- Position summary (intention, Robbins matrix)
- Active hypothesis count by state
- Direction count by state
- Source health summary
- Last 5 runs with timing

## 3. Print to stdout

Write the summary. No files produced. No atoms written.
```

That's a complete skill. No LLM calls, no corpus queries, no templates. The runtime validates inputs, runs the procedure (using deterministic composition since there's no LLM call declared), logs the run, returns.

Compare that minimal skill to something like `pulse propose-hypothesis`, which will have extensive LLM usage, knowledge loading, corpus queries (if enabled), multi-step procedure, and output validation. Same shape; different scale.

## Skill types by LLM involvement

Three archetypes:

- **Deterministic skills**: no LLM calls. Pure procedure over workspace state. Examples: `pulse workspace-status`, `pulse reindex`, `pulse workspace-list`. Fast, cheap, reliable.

- **Single-call skills**: one LLM call in the middle of the procedure. Examples: `pulse write-brief` (brief generation from hypothesis), `pulse draft-survey` (JTBD survey from customer profile). The procedure sets up context and validates output; the LLM does the generation.

- **Multi-call skills**: several LLM calls composing a procedure. Examples: `pulse propose-hypothesis` (cluster atoms, name the pattern, score confidence), `pulse map-ecosystem` (generate candidates per question, classify each, synthesize). Most expensive and longest-running.

The frontmatter `runtime.max_duration_s` is set appropriately to the archetype — 60s for deterministic, 180s for single-call, 900s for multi-call.
