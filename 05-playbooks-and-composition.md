# 05 — Playbooks and Composition

A playbook is a YAML file that composes multiple skills into a named operator workflow. Playbooks are how the framework bridges atomic skills (narrow, technical) to operator vernacular (natural, intent-based). They are indistinguishable from skills at the command layer — `pulse weekly` runs a playbook; `pulse extract` runs a skill; both invoke the same way.

This document defines the playbook file format, composition patterns, the five core v1 playbooks, and the runtime that executes them.

## The playbook file format

Playbooks live under `~/.pulse/playbooks/` as YAML files:

```
playbooks/
├── onboard.yaml
├── reposition.yaml
├── weekly.yaml
├── monthly.yaml
└── quarterly.yaml
```

Each playbook has frontmatter-like top-level fields followed by a `steps:` array. Here's the canonical structure:

```yaml
# playbooks/weekly.yaml

name: pulse weekly
version: 1.0.0
description: >
  Routine weekly intelligence pass. Extracts new content from active
  sources, scores signals against active hypotheses, updates direction
  momentum, and produces a weekly digest.
  
layer: operational
cadence: weekly
operator_time: ~10m
aliases:
  - pulse intel
  - pulse w

# Preconditions
requires:
  workspace_exists: true
  position_set: true
  sources_min: 10
  mode: any     # any | interactive | headless

# Default inputs (can be overridden at invocation)
defaults:
  window_days: 7
  max_atoms_per_source: 50
  
# The ordered step list
steps:
  - id: extract
    skill: pulse extract
    with:
      window: last_{{ defaults.window_days }}d
      max_per_source: "{{ defaults.max_atoms_per_source }}"
    on_failure: log_and_continue
    timeout_s: 600

  - id: link_atoms_to_directions
    skill: pulse update-directions
    with:
      atoms: "{{ steps.extract.outputs.new_atoms }}"
      link_only: true
    on_failure: log_and_continue

  - id: score_signals
    skill: pulse score-signals
    foreach:
      var: hypothesis
      source: workspace.hypotheses.where(state in [active, hardening, contested])
    with:
      new_atoms: "{{ steps.extract.outputs.new_atoms }}"
      hypothesis: "{{ foreach.hypothesis }}"
    on_failure: log_and_continue

  - id: propose_new
    skill: pulse propose-hypothesis
    when: "{{ steps.extract.outputs.unexplained_atom_clusters | length > 0 }}"
    with:
      clusters: "{{ steps.extract.outputs.unexplained_atom_clusters }}"
    on_failure: log_and_continue
    
  - id: recompute_momentum
    skill: pulse update-directions
    with:
      link_only: false
      recompute_momentum: true
    on_failure: halt

  - id: weekly_digest
    skill: pulse write-brief
    with:
      kind: weekly_digest
      since: "{{ (now - defaults.window_days.days).isoformat() }}"
    output: briefs/weekly/{{ today }}.md
    on_failure: log_and_continue

# Post-run
on_complete:
  print_summary: true
  notify: stdout
  
on_failure:
  preserve_partial: true
  summary_to: runs/<timestamp>.jsonl
```

## Composition patterns

Playbooks support six composition patterns that cover the full range of workflows needed in v1:

### 1. Sequential (default)

Steps run in order. Step N+1 waits for step N. Simplest pattern, used most often.

```yaml
steps:
  - id: one
    skill: pulse extract
  - id: two
    skill: pulse score-signals
  - id: three
    skill: pulse update-directions
```

### 2. Foreach

Run a skill across a collection. Collection can be workspace state (hypotheses, sources, directions) or output from a prior step.

```yaml
- id: score_each
  skill: pulse score-signals
  foreach:
    var: hypothesis
    source: workspace.hypotheses.where(state == 'active')
  with:
    hypothesis: "{{ foreach.hypothesis }}"
```

Foreach iterations run serially by default (safe under concurrency). Can be parallelized with `parallel: true` for skills declared as parallelizable in their frontmatter.

### 3. Conditional (when)

Run a step only if a condition holds. Condition can reference prior step outputs, workspace state, or defaults.

```yaml
- id: propose_new
  skill: pulse propose-hypothesis
  when: "{{ steps.extract.outputs.new_atoms | length > 20 }}"
```

Conditions are Jinja2 expressions evaluated against the playbook runtime context.

### 4. Branch

Choose between paths based on a value.

```yaml
- id: quarterly_branch
  switch: "{{ workspace.intention }}"
  cases:
    - value: preparing_for_transition
      steps:
        - skill: pulse scan-acquisitions
    - value: push_into_growth
      steps:
        - skill: pulse find-gaps
    - default:
      steps: []   # no-op for other intentions
```

Each case is a sub-list of steps. Branches are used sparingly — they can make playbooks hard to read. When used, they should reflect genuinely distinct operational paths.

### 5. Checkpoint

Human-in-the-loop pause for operator review before continuing.

```yaml
- id: review_proposed_hypotheses
  checkpoint:
    prompt: >
      {{ steps.propose_new.outputs.hypotheses | length }} new hypotheses 
      were proposed. Review in `hypotheses/proposed/` before continuing.
    options:
      - label: continue
        action: proceed
      - label: pause_and_exit
        action: halt_gracefully
      - label: skip_remaining
        action: skip_to_end
```

Checkpoints are critical in kickoff playbooks where you want the operator to validate intermediate state before committing to downstream work.

### 6. Idempotency markers

Steps that know whether they've already succeeded today and skip if so.

```yaml
- id: extract
  skill: pulse extract
  idempotency:
    key: "extract:{{ workspace_id }}:{{ today }}"
    on_duplicate: skip    # skip | force_rerun | prompt
```

Critical for `pulse weekly` which might accidentally get triggered twice on the same day — the dispatcher sees the idempotency key satisfied and skips the expensive extraction step.

## The playbook runtime

The runtime that executes playbooks (`pulse.runtime.playbook`) does the following:

1. **Load and validate**. Parse YAML. Validate against playbook schema. Resolve all `skill:` references — every named skill must exist in the skills directory.

2. **Check preconditions**. Verify workspace exists, position is set, sources count meets minimum, etc. Halt with clear error if unmet.

3. **Build execution context**. Initialize Jinja2 environment with `workspace`, `now`, `today`, `defaults`, and `steps` (which accumulates outputs as steps complete).

4. **Begin run log**. Open `workspaces/<id>/runs/<timestamp>.jsonl`. Insert runs row in SQLite with status=running and playbook_name=<name>.

5. **Execute steps in order**. For each step:
   - Evaluate `when` condition if present. If false, skip and log.
   - Evaluate idempotency key if present. If satisfied per policy, skip and log.
   - Resolve foreach source if present. For each item: invoke the skill with resolved inputs.
   - For non-foreach: invoke the skill once with resolved inputs.
   - Capture outputs into `steps.<id>.outputs` for later steps.
   - Handle failure per `on_failure` policy.

6. **Checkpoints pause the runtime**. On a checkpoint, save state to `runs/<timestamp>.checkpoint.yaml` and surface the prompt to the operator. On operator response, resume or halt.

7. **Run on_complete hooks**. Print summary, trigger notifications, etc.

8. **Close run log**. Update status=succeeded or status=failed with partial-success indicator. Write final summary.

## Context variables available in playbooks

```yaml
workspace:       # resolved workspace.yaml as a Jinja2-accessible object
  id: anti-enterprise
  identity: { ... }
  customer: { ... }
  position: { ... }
  hypotheses: [ ... ]   # loaded from hypotheses/ and index
  directions: [ ... ]
  sources: [ ... ]
  # [...]

defaults:        # from the playbook's defaults block, or overridden at invocation
  window_days: 7

steps:           # step outputs as they complete
  extract:
    outputs: { ... }
  score_signals:
    outputs: { ... }

now: 2026-04-23T14:22:00Z    # current timestamp
today: 2026-04-23             # current date

foreach:         # set during foreach iterations
  hypothesis: { ... }
  index: 2        # iteration index
```

## The five core v1 playbooks

Sketches of each. Full definitions live in the build output.

### 1. `pulse onboard` — Kickoff playbook

The one-hour investment that makes everything downstream work. A new operator or new client gets this done once.

```yaml
name: pulse onboard
cadence: one_time
operator_time: ~60m

requires:
  workspace_exists: true
  position_set: false      # this playbook sets it

steps:
  - skill: pulse set-identity
  - checkpoint:
      prompt: "Identity captured. Continue to customer profile? [Y/n]"
  - skill: pulse profile-customer       # the big one — see Doc 07
  - checkpoint:
      prompt: "Customer profile captured. Continue to offer articulation? [Y/n]"
  - skill: pulse articulate-offer
  - skill: pulse set-goals
  - skill: pulse set-position
  - skill: pulse map-ecosystem
  - skill: pulse type-sources
  - checkpoint:
      prompt: >
        Workspace is set up. Review workspace.yaml and sources.yaml 
        before continuing. Ready to run first weekly pass? [Y/n]
```

The checkpoints are deliberate. Onboarding is a deliberate act. The operator should see and approve each section before the next begins.

### 2. `pulse reposition` — Rebuild positioning

Same shape as `pulse onboard` but reads existing workspace first and only regenerates sections the operator marks as changed. Used when a business meaningfully pivots.

```yaml
name: pulse reposition
cadence: occasional
operator_time: ~45m

requires:
  workspace_exists: true
  position_set: true       # reposition assumes an existing position

steps:
  - id: review_current
    skill: pulse workspace-status
    with:
      sections: [identity, customer, offer, goals, position]
  - checkpoint:
      prompt: "Which sections do you want to rebuild?"
      options:
        - identity
        - customer
        - offer
        - goals
        - position
        - ecosystem
        - sources
      multi_select: true
      store_as: sections_to_rebuild
  - foreach:
      var: section
      source: "{{ checkpoint.sections_to_rebuild }}"
    switch: "{{ foreach.section }}"
    cases:
      - value: identity
        steps: [{ skill: pulse set-identity }]
      - value: customer
        steps: [{ skill: pulse profile-customer }]
      - value: offer
        steps: [{ skill: pulse articulate-offer }]
      - value: goals
        steps: [{ skill: pulse set-goals }]
      - value: position
        steps: [{ skill: pulse set-position }]
      - value: ecosystem
        steps: [{ skill: pulse map-ecosystem }]
      - value: sources
        steps: [{ skill: pulse type-sources }]
```

### 3. `pulse weekly` — Weekly intelligence pass

Routine operations. Runs in 10 minutes or less. Produces a weekly digest.

```yaml
name: pulse weekly
cadence: weekly
operator_time: ~10m

requires:
  workspace_exists: true
  position_set: true
  sources_min: 5

defaults:
  window_days: 7

steps:
  - id: extract
    skill: pulse extract
    with:
      window: last_{{ defaults.window_days }}d
      
  - id: link_atoms
    skill: pulse update-directions
    with:
      atoms: "{{ steps.extract.outputs.new_atoms }}"
      link_only: true
      
  - id: score_each
    skill: pulse score-signals
    foreach:
      var: hypothesis
      source: workspace.hypotheses.where(state in ['active', 'hardening', 'contested'])
    with:
      new_atoms: "{{ steps.extract.outputs.new_atoms }}"
      hypothesis: "{{ foreach.hypothesis }}"
      
  - id: propose_new
    skill: pulse propose-hypothesis
    when: "{{ steps.extract.outputs.unexplained_atom_clusters | length > 0 }}"
    with:
      clusters: "{{ steps.extract.outputs.unexplained_atom_clusters }}"
      
  - id: momentum
    skill: pulse update-directions
    with:
      link_only: false
      recompute_momentum: true
      
  - id: digest
    skill: pulse write-brief
    with:
      kind: weekly_digest
      since_days: "{{ defaults.window_days }}"
    output: briefs/weekly/{{ today }}.md
```

### 4. `pulse monthly` — Monthly synthesis

Deeper than weekly. Adds richer synthesis and a monthly trajectory update.

```yaml
name: pulse monthly
cadence: monthly
operator_time: ~25m

defaults:
  window_days: 30

steps:
  # Start with the full weekly flow
  - include: weekly
    with:
      window_days: "{{ defaults.window_days }}"
      
  # Add commodity-pattern check
  - id: commodity_pattern
    skill: pulse find-commodity-pattern
    
  # Add gap-map synthesis
  - id: gaps
    skill: pulse find-gaps
    
  # Produce monthly digest
  - id: monthly_digest
    skill: pulse write-brief
    with:
      kind: monthly_digest
      since_days: "{{ defaults.window_days }}"
    output: briefs/monthly/{{ today }}.md
```

### 5. `pulse quarterly` — Quarterly review

The longest and deepest playbook. Checks position drift, rewalks real-business question, postmortems retired hypotheses.

```yaml
name: pulse quarterly
cadence: quarterly
operator_time: ~60m

defaults:
  window_days: 90

steps:
  # Include monthly synthesis
  - include: monthly
    with:
      window_days: "{{ defaults.window_days }}"
      
  # Drift audit (position declared vs detected)
  - id: drift
    skill: pulse audit-drift
    
  - checkpoint:
      prompt: >
        Drift audit surfaced {{ steps.drift.outputs.drift_count }} 
        areas. Review before continuing.
      options:
        - continue
        - reposition_now        # jumps to pulse reposition
        - pause
      
  # Real-business question revisit
  - id: real_business
    skill: pulse set-identity
    with:
      sections: [real_business]
      mode: revisit
      
  # Postmortems on closed hypotheses
  - id: postmortems
    skill: pulse postmortem
    foreach:
      var: hypothesis
      source: >
        workspace.hypotheses.where(
          state in ['confirmed', 'retired'] and
          last_state_change >= (now - 90.days)
        )
    with:
      hypothesis: "{{ foreach.hypothesis }}"
      
  # Ecosystem refresh
  - id: ecosystem_refresh
    skill: pulse map-ecosystem
    with:
      mode: refresh
      
  # Produce quarterly review brief
  - id: quarterly_brief
    skill: pulse write-brief
    with:
      kind: quarterly_review
      since_days: "{{ defaults.window_days }}"
    output: briefs/quarterly/{{ today }}.md
```

## Including playbooks within playbooks

The `include:` directive composes playbooks:

```yaml
steps:
  - include: weekly
    with:
      window_days: 30
```

Semantics: the included playbook's steps are inlined into the calling playbook. Defaults in the `with:` override the included playbook's defaults. Step IDs get namespaced (`weekly.extract` rather than just `extract`) to avoid collisions.

This is how `monthly` builds on `weekly` and `quarterly` builds on `monthly` without duplication.

## Failure handling

Each step declares an `on_failure:` policy:

- `halt`: stop the playbook. Remaining steps don't run. Run log captures the failure.
- `log_and_continue`: log the failure, continue with next step. Good for non-critical steps.
- `retry`: retry up to N times (default 2). Useful for transient network failures.
- `checkpoint`: pause and ask the operator how to proceed.

Default is `log_and_continue` unless declared. Critical steps (ones whose outputs other steps depend on) should usually be `halt`.

## Authoring a new playbook

Operators (not just framework authors) can write playbooks. The workflow:

1. Create `playbooks/my-workflow.yaml`.
2. Write the YAML following the schema.
3. Validate with `pulse validate-playbook my-workflow`.
4. Dry-run with `pulse my-workflow --dry-run` to see execution plan without executing.
5. Run normally.

Custom playbooks are first-class. They appear in `pulse help`, they get dispatched the same way, they can be used as `include:` targets by other playbooks.

This is how the framework grows organically. An operator builds a workflow that works for one client, generalizes it, commits it as a playbook. Over time the library of playbooks reflects accumulated wisdom about what compositions of skills actually work.

## The kickoff vs operational split, revisited

Worth re-emphasizing the principle from Doc 00, because it shapes every playbook design:

Kickoff playbooks (`onboard`, `reposition`) gather inputs. They ask the operator many questions. They take an hour. They run rarely.

Operational playbooks (`weekly`, `monthly`, `quarterly`) consume those inputs. They ask the operator almost nothing. They take minutes. They run on cadence.

Mixing the two destroys both. If `weekly` starts asking for customer profile clarifications, it's no longer a weekly pass — it's an unexpected hour-long interruption. If `onboard` tries to extract signals from sources before they're set up, it fails.

The test for playbook design: **operator-facing questions only belong in kickoff**. Operational playbooks execute against existing state and produce outputs; if they ever need input, they halt with a clear message pointing to which kickoff skill to run.
