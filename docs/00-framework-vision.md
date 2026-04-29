# 00 — Framework Vision

## The one-line description

> **Pulse Skills Framework** is a filesystem-based, CLI-invokable system of atomic skills, composed playbooks, and an updatable knowledge corpus that operationalizes six business advisory frameworks (Hormozi, Abraham, Frasier, DemandCurve, Imperium, Robbins) into repeatable procedures an advisor or operator can run across one or many client workspaces.

## The problem it solves

Business-intelligence work at the SMB and mid-market level suffers from three structural weaknesses:

1. **Framework knowledge is siloed.** Hormozi has a worldview. Abraham has a worldview. Frasier has a worldview. No one has synthesized them into a single operational toolkit, and each advisor ends up doing it ad-hoc from memory.

2. **The work is unrepeatable.** Ecosystem mapping, position review, review mining, hypothesis formation — these are all procedures, but they exist in the heads of advisors and get re-derived from scratch every engagement. No codification means no compounding quality.

3. **Software for this work is too heavy.** Bloomberg terminals, Brandwatch, enterprise listening tools — all overkill for a $5M revenue business. Smaller advisors and operators have no middleware between "read a book and do it in your head" and "enterprise platform."

The Pulse Skills Framework sits in the gap. It's not a platform, not a product, not a service — it's a local toolkit of named procedures that one person (an advisor, a founder, a fractional exec) can run against their workspace or their client's workspace, in a terminal, and get reliable output.

## Who it's for

- **Independent consultants and fractional execs** running advisory engagements across multiple clients, who want to scale their framework-based thinking without hiring analysts
- **Operators of their own businesses** who want to do structured position-aware intelligence work on themselves, with the discipline of a framework
- **Agencies** looking to standardize how their strategists approach positioning, source discovery, and synthesis
- **The Pulse Engine product itself** — eventually, this framework becomes the runtime substrate powering the product's agent backend

## What it is not

- **Not a SaaS.** Zero servers. Zero accounts. Runs entirely on your machine.
- **Not a framework library.** It does not ship with 200 abstract frameworks to browse. It ships with six deeply-integrated ones operationalized into procedures.
- **Not a LangChain / CrewAI replacement.** It is not a general-purpose agent framework. It is opinionated about business-intelligence work specifically.
- **Not a note-taking app.** Workspaces accumulate state, but the framework is procedural, not reflective.
- **Not an integration platform.** It does not sync CRM records, move data between systems, or subscribe to operational feeds. It reasons against curated inputs, nothing more.

## The five-layer architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Corpus (optional, v1)                                       │
│   Raw source documents + vector index                        │
│   Queried during authoring, never at runtime                 │
└─────────────────────────────────────────────────────────────┘
                           ↓  (pulse author-knowledge)
┌─────────────────────────────────────────────────────────────┐
│ Knowledge                                                   │
│   Distilled, committed framework files                       │
│   Loaded by skills at runtime                                │
└─────────────────────────────────────────────────────────────┘
                           ↓  (skills reference by path)
┌─────────────────────────────────────────────────────────────┐
│ Skills                                                       │
│   Atomic procedures · Declared I/O · Stable over time        │
└─────────────────────────────────────────────────────────────┘
                           ↓  (playbooks compose them)
┌─────────────────────────────────────────────────────────────┐
│ Playbooks & Router                                           │
│   Named workflows · Decision tree · Operator-facing          │
└─────────────────────────────────────────────────────────────┘
                           ↓  (read / write)
┌─────────────────────────────────────────────────────────────┐
│ Workspaces                                                   │
│   Per-client state · YAML + JSONL + SQLite index             │
└─────────────────────────────────────────────────────────────┘

Future (v2, reserved):
┌─────────────────────────────────────────────────────────────┐
│ Intel (structured business-intelligence database)            │
│   Queried during authoring and by specific skills            │
│   Curated, not ingested from operational systems             │
└─────────────────────────────────────────────────────────────┘
```

Five layers in v1, one additional reserved for v2. Each updates on its own tempo. Skills are stable; knowledge is refined periodically; corpus grows with ingestion; workspaces accumulate continuously.

## The ten non-negotiables

These are the principles that govern every design decision. They survive all other priorities.

### 1. Filesystem is the source of truth

Every piece of state is a human-editable file. Databases are regenerable indexes over files, never primary stores. This makes the entire system portable, inspectable, git-friendly, and durable against tooling changes. If the SQLite index corrupts tomorrow, you rebuild it from the files. If LanceDB is deprecated in two years, you re-embed the corpus in whatever replaces it. The files are the asset.

### 2. Skills are procedures, not wikis

A skill with no explicit procedure is not a skill. Every `SKILL.md` has numbered steps, declared I/O, and a clear output artifact. A skill that just describes a concept belongs in `knowledge/`, not `skills/`. This discipline is what separates this framework from the countless "AI agent frameworks" that are really just prompt libraries with a dispatcher.

### 3. Knowledge is updatable without touching skills

Skills reference knowledge by path. When Hormozi publishes new material, you update the knowledge file; every skill that references that framework picks up the change on next run. The procedure stays stable; the substance gets refined over time.

### 4. Curated inputs only

This is the principle that makes Pulse different from every other "AI + your business" product. The reasoning layer only accepts inputs the operator has deliberately curated. No automatic ingestion from operational systems. No CRM feeds. No project-management syncs. No support-ticket firehoses. Every atom, every factor, every reference point is there because someone explicitly put it there.

The failure mode this avoids is reasoning pollution. Most "AI for your business" products trust the raw data, end up regurgitating confused noise, and the operator stops trusting the output within weeks. Pulse maintains quality by constraining what enters the reasoning layer. The cost is slightly more manual curation. The benefit is trustworthy output that stays trustworthy.

### 5. Unified `pulse` namespace

All user-facing commands are `pulse <verb>`. No nested prefixes. No sub-namespaces. The folder structure on disk may be layered (skills are organized by internal type: kickoff, discovery, listen, synthesis, action, reflect, meta), but at the command layer everything is flat.

Rationale: operators memorize one prefix. Recategorization doesn't break muscle memory. Playbook YAML stays readable. The layer taxonomy is pedagogical, not syntactic.

### 6. Bare `pulse` is the router

Typed alone, `pulse` invokes the master routing skill — an interactive decision tree that asks numbered questions and lands the operator on the right command. Typed with a verb, `pulse <verb>` dispatches directly.

The router is a friendly front door for new operators and infrequent workflows. The direct commands are the freight entrance for power users and scripted invocations. Both always work.

### 7. Playbooks and atomic skills are indistinguishable at the command layer

`pulse weekly` is a playbook. `pulse extract` is an atomic skill. Both get invoked the same way. The dispatcher figures out which is which. From the operator's point of view, there is no distinction.

### 8. Kickoff is separate from operations

Inputs are gathered by dedicated kickoff skills (`pulse onboard`, `pulse reposition`, the position and profile setters) — once, at the start, or during major repositioning moments. Operational skills read from the workspace; they don't ask the operator questions.

Rationale: if every operational skill had to gather its own context, the framework would be unusable. The split concentrates friction in one deliberate hour and eliminates it everywhere else.

### 9. The customer profile is the center of gravity

Every downstream skill depends on a rich customer profile. Ecosystem mapping needs it. Commodity-pattern detection needs it. Review mining needs it. Content briefs need it. Positioning statements need it.

A Pulse workspace with a thin customer profile produces thin outputs regardless of how good the skills are. Investing heavily in the customer profile questionnaire is the single highest-leverage act in framework design. See Doc 07.

### 10. Corpus and runtime are separate

The corpus is an authoring backend. Skills query it when helping you author or refine knowledge files. Skills do not query it during normal execution. This separation matters for three reasons:

- **Determinism.** Runtime RAG retrieval is stochastic. Cached distilled knowledge files are deterministic. Repeated skill invocations against the same workspace should produce similar outputs.
- **Latency.** RAG adds hundreds of milliseconds per call. Across a dozen-skill playbook, that compounds.
- **Quality.** Raw retrieved chunks are noisy. Distilled knowledge files are curated. Skills produce better output from the latter.

The corpus enriches the *authoring* of knowledge, which then feeds the runtime. The runtime stays lean.

## The four cadences

Different rooms of the framework breathe at different speeds:

- **Daily / ad-hoc**: direct atomic commands (`pulse extract`, `pulse propose-hypothesis`)
- **Weekly**: `pulse weekly` — routine intelligence pass, ~10 min, low operator time
- **Monthly**: `pulse monthly` — deeper synthesis including hypothesis proposals, ~25 min
- **Quarterly**: `pulse quarterly` — position drift audit, real-business recheck, postmortems, ~60 min, high operator time

Kickoff (`pulse onboard`, `pulse reposition`) is outside this cadence — a one-hour investment made once, or during major inflection moments.

## Why this framework deserves to exist

A fair challenge: why not use Claude directly with a long system prompt? The answer is that a long system prompt is not:

- Repeatable across sessions
- Version-controlled
- Composable
- Inspectable
- Refinable based on usage

A skills framework turns a set of good advisory habits into artifacts that improve over time. You don't re-explain the Hormozi ecosystem map to Claude every engagement — you run `pulse map-ecosystem` and the framework handles loading context, asking the right questions, applying the taxonomy, writing the output in a format downstream skills can consume.

The compounding comes from three places:
- Accumulated refinements to individual skills
- Accumulated knowledge-corpus updates that every skill benefits from
- Accumulated workspace state that deepens what any new skill invocation can draw on

One year in, a mature Pulse installation is meaningfully smarter about advisory work than any individual session with a general-purpose model, because it's been refined by real use against real clients.

## The voice of the system

A few notes on tone for CLI output, prompts, questionnaires, and error messages:

- **Direct.** Not chatty, not verbose, not apologetic. Confident and brief.
- **No emoji. No exclamation marks. No spinners with cute phrases.**
- **Numbered options for any choice.** Never ask open-ended questions when a list will do.
- **Confirmation for destructive or long-running actions.** With a summary of what's about to happen.
- **Errors state what failed and what to do next.** Not "something went wrong." Not "sorry!"

Test for tone: does this feel like a command-line tool built by someone who takes the work seriously, or does it feel like it was designed to be charming? The first is right.

## Future horizons

This framework is built to grow without rewrites. A brief sketch of what lands in later versions:

**v2** — A curated business-intelligence database (Postgres or SQLite) with named parameterized queries. Skills can query structured data you've deliberately entered: market benchmarks, competitive intelligence, factor timelines, cross-workspace patterns. Still no raw feeds. Still curated inputs only.

**v3** — The emitters layer. Outbound action integrations (draft into email, write a ticket, propose a calendar block). One-way, human-approval gated, never contributing to the reasoning layer.

**v4+** — Cross-workspace pattern detection, the Pulse Engine product, and whatever the framework reveals it needs as it matures in real use.

Each version adds capability without requiring earlier-version rewrites. v1 alone is a complete advisory tool; everything beyond is additive. See Doc 09 for the full future-architecture sketch.
