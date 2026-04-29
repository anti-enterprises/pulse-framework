# 06 — Master Router

The `pulse` command, invoked alone with no verb, launches the master router. The router asks numbered questions, presents state-aware options, and lands the operator on the right skill or playbook — with confirmation before any expensive action runs.

This document defines the router's behavior, the decision tree file format, the short-circuit input pattern, state-aware guards, and the traversal-logging system that enables continuous refinement.

## What the router is (and isn't)

The router is an **interactive decision tree**. It's not an LLM classifier. It's not fuzzy NLP. It's numbered options that the operator chooses between. Every traversal is deterministic.

Why the discipline: LLM-based intent classification is inconsistent. A classifier that sometimes routes "fix my positioning" to `pulse reposition` and sometimes to `pulse set-position` is worse than no router at all. An operator loses trust the moment routing becomes unpredictable. Numbered options are boring, reliable, and fast.

The router supports **short-circuit input** (typing a command name directly instead of a number), so power users are never slowed down by the tree. But the tree is always the fallback when the operator isn't sure.

## The tree file

The complete decision tree lives in one file:

```
~/.pulse/router/tree.yaml
```

Editable. Version-controlled. Re-readable by operators who want to understand what paths exist.

A sketch of the structure:

```yaml
version: 1
default_start: start

# Input patterns
short_circuit:
  direct_command: true          # accept `pulse weekly` typed as response
  short_names: true             # accept command name fragments (e.g. "weekly" or "map-eco")
  global_escapes:
    "0": back
    "q": quit
    "?": help
    "<": start_over

# Global state-aware guards applied at every prompt
guards:
  - condition: "workspace.exists == false"
    action: route_to
    target: setup

nodes:

  start:
    prompt: "What are you trying to do right now?"
    options:
      - label: "Set up a new workspace or framework"
        next: setup
      - label: "Work on positioning or the real-business question"
        next: positioning
      - label: "Add or manage sources"
        next: sources
      - label: "Run routine intelligence work"
        next: routine
      - label: "Investigate a hypothesis or direction"
        next: investigate
      - label: "Produce a deliverable (brief, survey, positioning, outreach)"
        next: deliverable
      - label: "Review or audit my workspace"
        next: review
      - label: "Work with the knowledge corpus (ingest, query, author)"
        next: corpus
      - label: "Show me the full command list"
        action: run_command
        command: pulse help

  setup:
    prompt: "What kind of setup?"
    guard:
      - condition: "workspace.exists == false"
        hint: "No workspace yet. Recommending `pulse init` and `pulse onboard`."
    options:
      - label: "First-time framework setup (install, configure, corpus)"
        action: run_command
        command: pulse init
        confirm: >
          This will set up ~/.pulse/, install framework components, and
          optionally install the local RAG corpus. Proceed?
      - label: "Create a new workspace for a client or project"
        action: run_command
        command: pulse workspace-new
      - label: "Onboard a new workspace (full kickoff)"
        action: run_command
        command: pulse onboard
        confirm: >
          This runs the full kickoff playbook — identity, customer profile,
          offer, goals, position, ecosystem, and sources. ~60 minutes.
          Proceed?
      - label: "Back"
        action: back

  routine:
    prompt: "How deep a pass do you want to run?"
    guard:
      - condition: "workspace.position_set == false"
        action: route_to
        target: positioning
        hint: >
          This workspace needs positioning set before running routine work.
          Redirecting to positioning setup.
      - condition: "workspace.sources_count < 5"
        hint: >
          Note: only {{ workspace.sources_count }} sources are active.
          Routine passes work best with 10+. Consider adding sources first.
    options:
      - label: "Weekly — extract, score, update directions (~10 min)"
        action: run_command
        command: pulse weekly
        confirm: >
          Running pulse weekly on workspace `{{ workspace.id }}`:
            - Extract from {{ workspace.sources_count }} active sources (last 7d)
            - Score new atoms against {{ workspace.active_hypotheses_count }} active hypotheses
            - Update direction momentum
            - Write weekly digest
          Proceed?
      - label: "Monthly — weekly plus hypothesis proposals (~25 min)"
        action: run_command
        command: pulse monthly
        confirm: >
          Running pulse monthly. This extends the weekly pass with
          commodity-pattern synthesis, gap-map analysis, and monthly
          digest. ~25 minutes. Proceed?
      - label: "Quarterly — full review with drift audit (~60 min)"
        action: run_command
        command: pulse quarterly
        confirm: >
          Running pulse quarterly. Full review: monthly synthesis plus
          position drift audit, real-business recheck, hypothesis
          postmortems, ecosystem refresh, quarterly review brief.
          ~60 minutes. Proceed?
      - label: "Just one step — let me pick"
        next: routine_granular
      - label: "Back"
        action: back

  routine_granular:
    prompt: "Which step?"
    options:
      - label: "Extract from active sources"
        action: run_command
        command: pulse extract
      - label: "Score new signals against hypotheses"
        action: run_command
        command: pulse score-signals
      - label: "Update direction momentum"
        action: run_command
        command: pulse update-directions
      - label: "Propose new hypotheses from atom clusters"
        action: run_command
        command: pulse propose-hypothesis
      - label: "Back"
        action: back

  positioning:
    prompt: "What aspect of positioning?"
    options:
      - label: "Set or update the 4×2 matrix and intention"
        action: run_command
        command: pulse set-position
      - label: "Redo the real-business question"
        action: run_command
        command: pulse set-identity
        with:
          section: real_business
      - label: "Update customer profile"
        action: run_command
        command: pulse profile-customer
      - label: "Articulate or update the offer"
        action: run_command
        command: pulse articulate-offer
      - label: "Full reposition — rebuild everything"
        action: run_command
        command: pulse reposition
        confirm: >
          Full reposition rebuilds identity, customer, offer, goals, 
          position, and ecosystem. ~45 minutes. Existing answers are 
          shown and you choose which to rebuild. Proceed?
      - label: "Back"
        action: back

  sources:
    prompt: "What do you want to do with sources?"
    options:
      - label: "Add a new source (single URL)"
        action: run_command
        command: pulse add-source
      - label: "Add multiple sources (URL list, typed by strategic role)"
        action: run_command
        command: pulse type-sources
      - label: "Map the full ecosystem (Hormozi framework)"
        action: run_command
        command: pulse map-ecosystem
      - label: "Map the trust network (Abraham framework)"
        action: run_command
        command: pulse map-trust-network
      - label: "Scan for acquisition targets (Frasier framework)"
        action: run_command
        command: pulse scan-acquisitions
      - label: "Register an external research source (NotebookLM, app, book)"
        action: run_command
        command: pulse connect-source
      - label: "Back"
        action: back

  investigate:
    prompt: "What are you investigating?"
    options:
      - label: "A specific hypothesis (see its evidence, score new signals)"
        action: run_command
        command: pulse score-signals
        with:
          mode: interactive
      - label: "A specific direction (see its trajectory, related factors)"
        action: run_command
        command: pulse update-directions
        with:
          mode: interactive
      - label: "Commodity pattern across competitors"
        action: run_command
        command: pulse find-commodity-pattern
      - label: "Gaps in the market"
        action: run_command
        command: pulse find-gaps
      - label: "Back"
        action: back

  deliverable:
    prompt: "What kind of deliverable?"
    options:
      - label: "Content brief (from a hypothesis or direction)"
        action: run_command
        command: pulse write-brief
      - label: "Positioning statement"
        action: run_command
        command: pulse write-positioning
      - label: "JTBD-style customer survey"
        action: run_command
        command: pulse draft-survey
      - label: "Outreach sequence"
        action: run_command
        command: pulse draft-outreach
      - label: "Back"
        action: back

  review:
    prompt: "What kind of review?"
    options:
      - label: "Quick workspace status"
        action: run_command
        command: pulse workspace-status
      - label: "Position drift audit (declared vs detected)"
        action: run_command
        command: pulse audit-drift
      - label: "Hypothesis postmortem (for confirmed or retired hypothesis)"
        action: run_command
        command: pulse postmortem
      - label: "Full quarterly review"
        action: run_command
        command: pulse quarterly
      - label: "Back"
        action: back

  corpus:
    prompt: "What do you want to do with the knowledge corpus?"
    guard:
      - condition: "corpus.enabled == false"
        hint: >
          The corpus is not enabled. Enable it with `pulse enable corpus`
          to unlock ingestion, querying, and corpus-assisted authoring.
    options:
      - label: "Ingest files I've referenced (via @)"
        action: run_command
        command: pulse ingest
      - label: "Query the corpus directly"
        action: run_command
        command: pulse corpus-query
      - label: "Author or refine a knowledge file"
        action: run_command
        command: pulse author-knowledge
      - label: "Refine an existing knowledge file with a note"
        action: run_command
        command: pulse refine-knowledge
      - label: "See corpus status"
        action: run_command
        command: pulse corpus-status
      - label: "Back"
        action: back
```

## Short-circuit input

At any router prompt, the operator can respond in four ways:

1. **A number** (e.g., `3`) — selects that option
2. **A direct command name** (e.g., `pulse weekly` or `weekly`) — dispatches immediately, bypassing the tree
3. **A global escape** (`0` for back, `q` for quit, `?` for help, `<` for start over)
4. **A fuzzy match** (e.g., `map-eco`) — resolves to a specific command if unambiguous; prompts for disambiguation otherwise

This lets the router serve two populations simultaneously:

- **New operators** navigate the tree, learning the commands as they go.
- **Power users** short-circuit — type `pulse` just to save a context switch, then immediately type `weekly` without navigating the tree.

The fuzzy matching is intentionally narrow (prefix matching and simple edit distance). No LLM classification. No semantic matching. The goal is to handle typos and common abbreviations, not to guess intent.

## State-aware guards

Every node can declare guards that evaluate before the prompt is shown. Guards serve two purposes:

1. **Redirect**. If the operator is trying to do X but their workspace isn't ready, route them to the prerequisite. Example: trying to run `pulse weekly` without a position set → redirected to positioning setup.

2. **Inform**. Non-blocking hints about workspace state. Example: "only 3 sources active — consider adding more before running weekly."

Guards are evaluated top-to-bottom. First matching guard wins. Redirection guards short-circuit the prompt entirely; informational guards show their hint above the prompt and then display the options normally.

Guard conditions can reference:

- Workspace state (`workspace.position_set`, `workspace.sources_count`, `workspace.active_hypotheses_count`)
- Corpus state (`corpus.enabled`, `corpus.last_ingestion_age_days`)
- Global state (`config.claude_api_key_set`, `config.voyage_api_key_set`)
- Time (`now`, `today.weekday`, `workspace.last_run_age_hours`)

## Confirmation screens

Any command that mutates state, takes more than 30 seconds, or has a non-trivial cost should land on a confirmation screen in the router. The confirmation:

- States what will happen in specific terms (not "run pulse weekly" but "extract from 28 sources, score against 6 hypotheses, write digest to briefs/weekly/2026-04-23.md")
- Shows the workspace being operated on
- Asks `[Y/n]` with Y as default

This is the trust-building layer. Operators need to know the router won't fire off an expensive playbook because they fat-fingered a number.

Confirmation text supports Jinja2 templating, so it can show live workspace state:

```yaml
confirm: >
  Running pulse weekly on workspace `{{ workspace.id }}`:
    - Extract from {{ workspace.sources_count }} active sources
    - Score new atoms against {{ workspace.active_hypotheses_count }} active hypotheses
    - Update direction momentum
    - Write weekly digest to briefs/weekly/{{ today }}.md
  Estimated runtime: ~10 minutes.
  Estimated cost: ~$0.15 in Claude API calls.
  Proceed?
```

When the operator sees real numbers — 28 sources, 6 hypotheses, $0.15 cost — they know exactly what they're authorizing.

## Breadcrumbs

The router maintains a traversal breadcrumb so `0` (back) can take the operator to the previous prompt. Breadcrumbs are per-session — quitting and restarting clears them.

Example traversal:

```
start > routine > routine_granular    (current)
```

Typing `0` goes back to `routine`. Typing `0` again goes to `start`. Typing `0` at `start` prompts "Exit? [y/N]".

## The router skill itself

The router is implemented as a skill — `pulse` (no verb) is the same dispatcher mechanism as any other skill, but with a `tree_walker` runtime instead of a `llm_procedure` runtime.

```markdown
---
name: pulse
description: Interactive routing skill. Walks the decision tree in router/tree.yaml to land on the right command.
layer: meta
cadence: ad_hoc
operator_time: ~30s
knowledge: []
reads:
  - router/tree.yaml
  - workspace.yaml (current workspace if set)
  - config.yaml
writes:
  - .router-log.jsonl
inputs: {}
outputs: {}
runtime:
  type: tree_walker    # special runtime type
llm: {}
---

# Procedure

1. Load router/tree.yaml
2. Load active workspace state (if any)
3. Start at tree.default_start (usually "start")
4. For each node:
   a. Evaluate guards; redirect or show hints
   b. Render prompt and numbered options (plus global escapes)
   c. Wait for input
   d. Parse input: number, command name, escape, or fuzzy match
   e. Dispatch action: run_command, next, back, quit, or help
5. On run_command:
   - Show confirmation if declared
   - On confirm: dispatch to the actual command
   - On reject: return to the current node
6. Log the traversal to .router-log.jsonl
7. After dispatched command finishes: ask "Anything else? [start/quit]"
```

## Traversal logging

Every router session is logged to `~/.pulse/runs/router.log.jsonl`:

```jsonl
{"timestamp":"2026-04-23T10:14:00Z","workspace":"anti-enterprise","path":["start","routine","pulse weekly"],"dispatched":"pulse weekly","confirmed":true,"completed":true,"duration_s":28}
{"timestamp":"2026-04-23T14:22:00Z","workspace":"anti-enterprise","path":["start","investigate"],"dispatched":null,"abandoned_at":"investigate","duration_s":12}
```

Over weeks, this log reveals usage patterns:

- Which paths get traversed most (worth making more prominent or faster)
- Which paths get abandoned (confusing prompts, wrong options)
- Which commands get invoked directly vs through routing (candidates for simpler aliasing)
- Which nodes show guards that redirect frequently (operators routinely missing preconditions)

A dedicated skill `pulse refine-router` reads the log periodically and proposes tree edits:

```
$ pulse refine-router

Analyzing 124 router sessions from the past 30 days...

Observations:
  1. 47 sessions navigated to "routine" → "weekly" (38%). This is your 
     most-used path. Consider adding "weekly" as a top-level option in 
     start node (currently 2 clicks, could be 1).
     
  2. 14 sessions abandoned at "investigate" (31% of investigate entries). 
     The prompt "What are you investigating?" may be too abstract. 
     Suggested rewrite shown below.
     
  3. The "corpus" branch was never entered in 124 sessions. If corpus 
     is important to surface, consider moving it higher in the start 
     options or adding explanatory text.

Apply suggested changes? [Y/n/edit]
```

The router improves itself based on how it's used. This is the continuous-improvement loop at the routing layer.

## First-time-run special handling

The very first time `pulse` is invoked (no config file exists, no workspaces exist), the router skips the normal tree and shows a first-run prompt:

```
$ pulse

Welcome to Pulse.

It looks like this is your first time. Before you can do anything, 
you'll need to set up the framework.

Run `pulse init` to get started.

  pulse init                 — one-time framework setup
  pulse help                 — see all commands
  pulse                      — come back here after init

Type the command you want to run, or `q` to exit.

> 
```

This is the one place the router breaks its own pattern. The decision tree doesn't apply until `pulse init` has completed successfully.

## Interrupt handling

Ctrl-C at any router prompt:

- Shows "Exit? [y/N]"
- Y exits cleanly
- N returns to the current prompt

During a dispatched command (post-confirmation), Ctrl-C interrupts the command and returns to the router with a log entry noting the interruption.

## The router's only hard rule

The router must never dispatch a command that the operator didn't explicitly confirm. Numbered selection of an option is confirmation of navigating to that option. Confirmation screens are required for anything that runs code, mutates state, or costs money. The router's value proposition depends on the operator trusting that no action happens without their explicit Y.

## Invoking the router in non-interactive contexts

When `pulse` is invoked in a context where stdin isn't a terminal (scripts, CI, cron), the router refuses to run and prints:

```
$ pulse
The router requires an interactive terminal.

To invoke commands non-interactively, use `pulse <command>` directly:

  pulse weekly              — run the weekly playbook
  pulse extract             — extract atoms
  pulse help                — list all commands

Or use the --workspace flag to operate on a specific workspace:

  pulse weekly --workspace anti-enterprise
```

This prevents the router from hanging in automation contexts.
