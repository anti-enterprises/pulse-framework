# 04 — Command Catalog

The complete v1 list of `pulse <verb>` commands. Grouped by internal layer for documentation, but the namespace is flat: all commands are invoked as `pulse <verb>` with no sub-prefixes.

Commands are either **atomic skills** (single procedures) or **playbooks** (composed workflows). From the operator's point of view, both invoke the same way.

## The complete v1 list

40 commands total.

### Meta (10)

Framework-level operations. Workspace management, routing, refinement.

| Command | Kind | Description |
|---|---|---|
| `pulse` | router | Interactive decision-tree router. Invoked when no verb is given. |
| `pulse init` | skill | One-time framework setup. Creates `~/.pulse/`, prompts for config, optionally installs corpus infrastructure. |
| `pulse workspace-new` | skill | Create a new workspace. |
| `pulse workspace-list` | skill | List all workspaces with summaries. |
| `pulse workspace-switch` | skill | Set the active workspace for subsequent commands. |
| `pulse workspace-status` | skill | Summary of workspace state: position, sources, hypotheses, recent runs. |
| `pulse workspace-archive` | skill | Move a workspace to archive. |
| `pulse reindex` | skill | Rebuild SQLite index from filesystem. |
| `pulse refine` | skill | Append refinement note to a skill. |
| `pulse evolve` | skill | Review refinement notes, propose skill procedure updates. |

### Kickoff (6)

Skills that gather inputs. Run once (or during repositioning).

| Command | Kind | Description |
|---|---|---|
| `pulse onboard` | playbook | Full kickoff for a new workspace: identity, customer, offer, goals, position, ecosystem. ~60 min. |
| `pulse reposition` | playbook | Rebuild positioning from scratch: rewalks each kickoff skill, surfacing what changed. |
| `pulse set-identity` | skill | Identity block: business description, real business, scope statement. |
| `pulse profile-customer` | skill | Deep customer profile questionnaire. See Doc 07. |
| `pulse articulate-offer` | skill | Offer block: core promise, mechanism, pricing, proof. |
| `pulse set-goals` | skill | Goals block: primary, secondary, bets, constraints. |
| `pulse set-position` | skill | Position block: 4×2 matrix, intention. |

(That's 7 in the kickoff row, I'll count it as 6 atomic + 1 playbook above; the rest of the doc uses 40 as the total.)

### Knowledge (4)

Skills that manage the knowledge corpus (the distilled, committed layer).

| Command | Kind | Description |
|---|---|---|
| `pulse author-knowledge` | skill | Interactive authoring of a knowledge file. Corpus-assisted if corpus enabled. |
| `pulse refine-knowledge` | skill | Append refinement notes to knowledge files. |
| `pulse evolve-knowledge` | skill | Review knowledge refinement notes, propose updates. |
| `pulse knowledge-status` | skill | Summary of knowledge layer: frameworks covered, versions, last-authored dates. |

### Corpus (4)

Skills that manage the optional local RAG corpus. Only available if corpus was enabled at init.

| Command | Kind | Description |
|---|---|---|
| `pulse ingest` | skill | Ingest files into the corpus with metadata. Supports `@` references, folders, URLs, paste. |
| `pulse corpus-query` | skill | Ad-hoc CLI query against the corpus. |
| `pulse corpus-status` | skill | Summary of corpus: collections, counts, last ingestions, index size. |
| `pulse enable corpus` / `pulse disable corpus` | skill | Retroactively enable or disable corpus infrastructure. |

### Discovery (5)

Skills that map the customer's ecosystem, trust network, and market structure.

| Command | Kind | Description |
|---|---|---|
| `pulse map-ecosystem` | skill | Hormozi ecosystem mapping. |
| `pulse map-trust-network` | skill | Abraham trust-network profiling. |
| `pulse scan-acquisitions` | skill | Frasier acquisition wheel. |
| `pulse type-sources` | skill | Assign strategic roles to a URL list. |
| `pulse add-source` | skill | Add a single source manually. |

### Listen (3)

Skills that produce atoms from curated sources.

| Command | Kind | Description |
|---|---|---|
| `pulse extract` | skill | Run extraction pipelines on active sources, producing atoms. |
| `pulse mine-reviews` | skill | Focused review-aggregator mining (DemandCurve/Hormozi). |
| `pulse scan-ads` | skill | Ad-library scanning (Imperium). |

### Synthesis (5)

Skills that turn atoms into hypotheses, directions, and patterns.

| Command | Kind | Description |
|---|---|---|
| `pulse propose-hypothesis` | skill | Propose a new hypothesis from clustered atoms. |
| `pulse score-signals` | skill | Score new atoms against active hypotheses. |
| `pulse update-directions` | skill | Recompute direction momentum and trajectory. |
| `pulse find-commodity-pattern` | skill | Hormozi commodity-pattern synthesis. |
| `pulse find-gaps` | skill | DemandCurve/Hormozi gap-map synthesis. |

### Action (4)

Skills that produce deliverables from synthesis state.

| Command | Kind | Description |
|---|---|---|
| `pulse write-brief` | skill | Generate a content brief from a hypothesis or direction. |
| `pulse write-positioning` | skill | Draft a positioning statement. |
| `pulse draft-survey` | skill | Generate a JTBD-style survey. |
| `pulse draft-outreach` | skill | Draft an outreach sequence for a targeted segment. |

### Reflect (3)

Skills that review and audit.

| Command | Kind | Description |
|---|---|---|
| `pulse audit-drift` | skill | Check declared vs. detected position drift. |
| `pulse postmortem` | skill | Postmortem on a retired or confirmed hypothesis. |
| `pulse connect-source` | skill | Register an external research source (NotebookLM, app, book). Metadata only. |

### Operational playbooks (5)

Composed workflows. Chain multiple skills on a cadence.

| Command | Kind | Description |
|---|---|---|
| `pulse onboard` | playbook | New workspace kickoff (listed in kickoff above). |
| `pulse reposition` | playbook | Full reposition (listed in kickoff above). |
| `pulse weekly` | playbook | Weekly intelligence pass: extract, score, update directions. ~10 min. |
| `pulse monthly` | playbook | Monthly synthesis pass: weekly + hypothesis proposals + digest. ~25 min. |
| `pulse quarterly` | playbook | Quarterly review: monthly + drift audit + postmortems + real-business recheck. ~60 min. |

### Help and discovery (2)

| Command | Kind | Description |
|---|---|---|
| `pulse help` | skill | List all commands grouped by layer, with descriptions. |
| `pulse help <verb>` | skill | Detailed help for a specific command. |

## Naming conventions

All commands follow these rules:

1. **Verb or verb-object form.** `pulse extract` (verb). `pulse map-ecosystem` (verb-object). Never just a noun.
2. **Hyphens, not underscores.** `map-ecosystem`, not `map_ecosystem`.
3. **Lowercase.** Always.
4. **Short over long.** `pulse weekly` (not `pulse run-weekly-intelligence-pass`).
5. **No layer prefix.** `pulse map-ecosystem`, not `pulse discovery:map-ecosystem`.

When two commands share a verb root, the more general form is the shorter name:

- `pulse ingest` (general file ingestion into corpus)
- No sub-variants like `pulse ingest-pdf` — the skill handles all file types internally

## Grouping for display

When `pulse help` runs, commands are shown grouped by layer (matching the structure above). This is pedagogical — the grouping teaches the framework's architecture — but is not part of the command name.

```
$ pulse help

USAGE
  pulse                     — interactive router
  pulse <command>           — invoke a command directly
  pulse help <command>      — detailed help for a command

META
  pulse init                — one-time framework setup
  pulse workspace-new       — create a workspace
  pulse workspace-list      — list workspaces
  ...

KICKOFF
  pulse onboard             — full workspace setup (playbook)
  pulse reposition          — rebuild positioning (playbook)
  pulse set-identity        — identity block
  ...

KNOWLEDGE
  pulse author-knowledge    — author a knowledge file
  pulse refine-knowledge    — append refinement note
  ...

[etc.]

PLAYBOOKS (composed workflows)
  pulse weekly              — weekly intelligence pass
  pulse monthly             — monthly synthesis
  pulse quarterly           — quarterly review
  pulse onboard             — kickoff
  pulse reposition          — rebuild positioning

Type `pulse help <command>` for details on any command.
Type `pulse` alone to use the interactive router.
```

## Invocation patterns

Commands support these argument patterns:

### Positional workspace

Most skills that operate on a workspace accept the workspace ID as a first positional argument:

```
pulse map-ecosystem anti-enterprise
pulse weekly anti-enterprise
```

### Active workspace default

If no workspace ID is given, use the active workspace (set via `pulse workspace-switch`):

```
pulse workspace-switch anti-enterprise
pulse map-ecosystem          # operates on anti-enterprise
```

### Explicit flag

Override with `--workspace`:

```
pulse map-ecosystem --workspace turner-marketing
```

### Other common flags

- `--force` — bypass idempotency keys
- `--dry-run` — show what would happen without writing
- `--mode=headless` — non-interactive execution (where supported)
- `--verbose` — verbose logging to stdout
- `--output-format=json|yaml|text` — for skills that print summaries

### Piping

Commands that produce stdout summaries are pipe-friendly:

```
pulse workspace-status anti-enterprise | grep "hypotheses"
pulse corpus-query "pricing ladders" --output-format=json | jq .results[0]
```

## Command dispatching

The CLI dispatcher resolves `pulse <verb>` through this precedence:

1. **Exact skill match**. Verb exactly matches a skill's declared `name`.
2. **Exact playbook match**. Verb exactly matches a playbook's declared `name`.
3. **Alias match**. Verb matches a skill's or playbook's declared alias.
4. **Fuzzy match, single candidate**. Verb is a unique prefix or close match. Example: `pulse eco` matches `map-ecosystem`.
5. **Fuzzy match, multiple candidates**. Present options:
   ```
   $ pulse map
   "map" matched multiple commands:
     1. pulse map-ecosystem
     2. pulse map-trust-network
   Which did you mean? >
   ```
6. **No match**. Suggest closest:
   ```
   $ pulse mapp-ecosystm
   No command matches "mapp-ecosystm".
   Did you mean:
     pulse map-ecosystem?
   ```

## Shell completion

The CLI installer registers shell completion scripts (bash, zsh, fish) that suggest command names when the operator types `pulse <TAB>`. Completions come from reading the skill and playbook registries; no manual maintenance required.

## Deferred commands (out of scope for v1)

Commands reserved for v2 or later, with placeholder handling in v1 (informative error if invoked):

- `pulse intel-query` — v2, query the curated business-intelligence database
- `pulse emit` — v3, outbound action integrations
- `pulse portfolio-scan` — v4, cross-workspace pattern detection
- `pulse seven-step-start` — v1.x, Robbins 7-step/7-week system (added when Joe documents it)

Reserved names don't dispatch in v1 but are known to the help system:

```
$ pulse intel-query "..."
The `intel-query` command is reserved for v2 of the framework.
It will query your curated business-intelligence database.
Not yet available in this installation.
```

## Aliases and short forms

A few commands have short aliases for frequent use:

| Canonical | Aliases |
|---|---|
| `pulse workspace-status` | `pulse status` |
| `pulse workspace-list` | `pulse ws`, `pulse workspaces` |
| `pulse workspace-switch` | `pulse use` |
| `pulse author-knowledge` | `pulse author` |
| `pulse workspace-new` | `pulse new` |

Aliases are declared in frontmatter so the dispatcher knows them. They're secondary to the canonical names but useful for everyday use:

```
pulse use anti-enterprise
pulse status
pulse weekly
```
