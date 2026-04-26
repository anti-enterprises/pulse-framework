# Pulse Skills Framework — Build Package

This package contains everything needed for an AI coding agent (Claude Code, Codex, Cursor) to build the **Pulse Skills Framework** — a filesystem-based system of atomic skills, composed playbooks, a master routing skill, an updatable knowledge corpus, and an optional local RAG backend, designed to operationalize the business-intelligence thinking of Hormozi, Abraham, Frasier, DemandCurve, Imperium, and Robbins into a coherent CLI toolkit.

## Read order

1. **`00-framework-vision.md`** — what this is, who it's for, the layer architecture, the curated-inputs principle
2. **`01-knowledge-corpus.md`** — the knowledge layer (distilled, committed) and the corpus layer (source material, queryable); their relationship and how skills consume each
3. **`02-workspace-and-state.md`** — the `workspace.yaml` spine, directory layout, atom schema, SQLite indexing
4. **`03-skill-anatomy.md`** — the shape of a skill, frontmatter, procedure patterns, I/O contract, knowledge and corpus dependencies
5. **`04-command-catalog.md`** — the full v1 catalog of `pulse <verb>` commands, grouped by internal layer
6. **`05-playbooks-and-composition.md`** — how playbooks compose skills, the kickoff vs. operational split, the five core playbooks
7. **`06-master-router.md`** — the `pulse` bare entry point, decision tree, state-aware guards, short-circuit input
8. **`07-customer-profile-questionnaire.md`** — the single highest-leverage artifact: the question bank that every downstream skill depends on
9. **`08-implementation-plan.md`** — phased build sequence, acceptance criteria, common pitfalls
10. **`09-future-architecture.md`** — v2 (curated business-intelligence database), v3+ (emitters layer), the long-term trajectory
11. **`10-corpus-setup-guide.md`** — operator-facing guide for setting up the local RAG corpus well
12. **`11-appendix-types-and-schemas.md`** — canonical TypeScript/Python types, YAML schemas, and database DDL

## What this is

A filesystem-first, CLI-invokable, Claude-Code-friendly framework for running repeatable business-intelligence work across one or many client workspaces. It operationalizes six business advisory frameworks into atomic procedures that compose into named operator workflows. It ships with an optional local RAG backend for querying source materials during knowledge authoring.

It is not the Pulse Engine product. It is the substrate the Pulse Engine product would eventually use as its runtime — and independently, it is a tool that an advisor, founder, or fractional executive can use directly against client engagements without a UI.

## The five-layer architecture

```
skills/      — HOW to do things (stable procedures)
knowledge/   — WHAT skills draw on at runtime (distilled, committed)
corpus/      — WHERE source material is indexed for authoring (optional)
workspaces/  — WHAT HAS BEEN done for each operator (per-client state)
intel/       — WHAT the system has curated about the world (v2, reserved)
```

Skills reference knowledge at runtime. Knowledge is authored from corpus content and manual input. Workspaces accumulate state. The corpus is queried only during authoring, never at skill execution time. Each layer updates on its own tempo.

## Tech stack

- **Python 3.11+** for the CLI runtime and dispatcher
- **YAML** for declarative data (workspace, playbooks, taxonomies, router tree)
- **Markdown** for skill procedures, framework docs, prompt templates
- **JSONL** for append-only logs
- **SQLite** for workspace index
- **LanceDB** (optional, v1) for the local corpus vector store
- **Voyage AI / OpenAI / Anthropic / local BGE-M3** (operator choice) for embeddings
- **Git** for versioning skills, knowledge, and workspaces
- **Claude API** for LLM-backed steps within skills

## Top-level directory layout

```
~/.pulse/
├── skills/                  # Atomic skill definitions
├── playbooks/               # Composed workflows
├── knowledge/               # Distilled, committed skill-ready knowledge
├── corpus/                  # Optional: raw source material + vector index
├── workspaces/              # Per-client state directories
├── router/                  # Decision tree for bare `pulse`
├── config.yaml              # Global config
└── runs/                    # Execution logs
```

## The non-negotiables

1. **Filesystem as source of truth.** Every piece of state is a human-editable file. Databases are regenerable indexes, never primary stores.
2. **Skills are procedures, not wikis.** Every skill has declared inputs, a numbered procedure, and declared outputs.
3. **Knowledge is updatable without touching skills.** Skills reference knowledge by path.
4. **Curated inputs only.** No automatic ingestion from operational systems. Everything in the reasoning layer is there because the operator (or a skill acting under explicit direction) put it there.
5. **Unified `pulse` namespace.** All commands are `pulse <verb>`. No nested prefixes.
6. **Bare `pulse` is the router.** Typed alone, `pulse` invokes the master routing skill.
7. **Playbooks and atomic skills are indistinguishable at the command layer.**
8. **Kickoff is separate from operations.** Inputs are gathered by dedicated kickoff skills, once.
9. **The customer profile is the center of gravity.** Every downstream skill depends on a rich customer profile.
10. **Corpus and runtime are separate.** The corpus is an authoring backend. Skills never query it during normal execution.

## What's in / out for v1

**In:**
- Full `pulse` CLI with dispatcher, router, playbook runner
- ~40 skills across kickoff, discovery, listen, synthesis, action, reflect, and meta layers
- Complete knowledge corpus with all six frameworks represented
- Five core playbooks: `pulse onboard`, `pulse weekly`, `pulse monthly`, `pulse quarterly`, `pulse reposition`
- Router decision tree with state-aware guards
- Workspace + SQLite index + run logs
- Optional local RAG corpus with `pulse ingest` and `pulse corpus-query` skills
- Six pre-structured corpus collections (frameworks, industry, case-studies, interviews, workspace-specific, plus a catch-all)

**Out:**
- A GUI (CLI-only in v1)
- Cloud backend (everything runs locally)
- Multi-user collaboration on a single workspace
- Real-time source polling daemons
- Operational data integrations (CRM, PM, support — these pollute reasoning; never coming)
- The Pulse Engine product itself (this is the framework, not the product)

## How to use this package

If you are the coding agent: start with `08-implementation-plan.md`. It tells you what to build in what order, with acceptance criteria. Read `00` through `06` first to understand the architecture, then `07` for the highest-leverage single deliverable (the customer profile questionnaire), then `08` for the build sequence, then `09`-`11` for reference material.

If you are Joe: start with `07-customer-profile-questionnaire.md` and `08-implementation-plan.md`. Those are where you'd want to push back if anything feels wrong. Everything else is architectural scaffolding that those two documents depend on.
