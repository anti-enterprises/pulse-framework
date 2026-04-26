# 01 — Knowledge and Corpus Layers

Two layers, one responsibility: making framework substance available to skills.

- **Knowledge** is distilled, committed, skill-ready. It's what skills load at runtime.
- **Corpus** is raw source material, indexed for retrieval. It's what you query during authoring.

Both are optional to a degree (the corpus is truly optional; the knowledge layer always exists but can be sparse at first). Both update on their own tempo. This document defines what goes in each, how they relate, how skills consume them, and how they get refined.

## The knowledge layer

### What it is

A directory of markdown files, YAML taxonomies, structured questionnaires, prompt templates, and reference examples — everything the framework needs to apply its substance consistently.

```
~/.pulse/knowledge/
├── frameworks/
│   ├── hormozi/
│   │   ├── ecosystem-mapping.md
│   │   ├── commodity-pattern.md
│   │   ├── review-mining.md
│   │   ├── category-of-one.md
│   │   ├── _quotes.yaml
│   │   └── meta.yaml
│   ├── abraham/
│   │   ├── yellow-pages.md
│   │   ├── cross-industry-intelligence.md
│   │   ├── trust-network-profiling.md
│   │   ├── _quotes.yaml
│   │   └── meta.yaml
│   ├── frasier/
│   │   ├── acquisition-wheel.md
│   │   ├── capability-audit.md
│   │   ├── 5-80-5-canvas.md
│   │   ├── _quotes.yaml
│   │   └── meta.yaml
│   ├── demandcurve/
│   │   ├── jtbd-interviews.md
│   │   ├── review-mining.md
│   │   ├── unique-mechanism.md
│   │   ├── dissatisfied-customers.md
│   │   ├── _quotes.yaml
│   │   └── meta.yaml
│   ├── imperium/
│   │   ├── niche-research-sop.md
│   │   ├── active-intelligence.md
│   │   ├── _quotes.yaml
│   │   └── meta.yaml
│   └── robbins/
│       ├── lifecycle-stages.md
│       ├── seasons.md
│       ├── what-business-really-in.md
│       ├── seven-step-seven-week.md          # stub in v1, flesh out as documented
│       ├── _quotes.yaml
│       └── meta.yaml
├── taxonomies/
│   ├── strategic-roles.yaml
│   ├── source-kinds.yaml
│   ├── atom-types.yaml
│   ├── atom-source-kinds.yaml
│   ├── factor-kinds.yaml
│   ├── hypothesis-states.yaml
│   ├── direction-states.yaml
│   ├── signal-scores.yaml
│   ├── seasons.yaml
│   ├── lifecycle-stages.yaml
│   └── intentions.yaml
├── questionnaires/
│   ├── customer-profile.yaml
│   ├── offer-articulation.yaml
│   ├── position-matrix.yaml
│   ├── real-business.yaml
│   └── goals-and-constraints.yaml
├── playbook-recipes/
│   ├── weekly-intel.md
│   ├── monthly-synthesis.md
│   ├── quarterly-review.md
│   ├── onboarding-checklist.md
│   └── reposition-checklist.md
├── examples/
│   ├── ecosystem-map/
│   │   ├── ai-tools-example.yaml
│   │   ├── dtc-beauty-example.yaml
│   │   └── service-b2b-example.yaml
│   ├── commodity-pattern/
│   ├── customer-profile/
│   └── [...]
├── source-templates/
│   ├── direct-competitor/
│   │   ├── saas-b2b.yaml
│   │   └── dtc-product.yaml
│   ├── community-forum/
│   │   ├── reddit-subreddits-by-vertical.yaml
│   │   └── x-search-patterns.yaml
│   └── [...]
├── prompts/
│   ├── extraction/
│   │   ├── news-article.md
│   │   ├── competitor-blog.md
│   │   ├── review-aggregator.md
│   │   ├── community-thread.md
│   │   └── ad-library.md
│   ├── synthesis/
│   │   ├── propose-hypothesis.md
│   │   ├── score-signal.md
│   │   ├── find-commodity-pattern.md
│   │   └── find-gaps.md
│   └── generation/
│       ├── content-brief.md
│       ├── positioning-statement.md
│       └── jtbd-survey.md
├── glossary.yaml
└── CHANGELOG.md
```

### The anatomy of a framework file

Every framework doc has the same shape. Example:

```markdown
---
framework: abraham
topic: yellow-pages
version: 2026.04.23
last_authored: 2026-04-23
source:
  primary: "EPIC & Abraham NotebookLM"
  primary_url: "https://notebooklm.google.com/notebook/..."
  primary_account: joe@geniusscaleai.com
  extracted_excerpts_ref: _quotes.yaml
refined_by:
  - 2026-04-23: initial authoring
skill_consumers:
  - pulse map-ecosystem
  - pulse map-trust-network
  - pulse find-complementary-sources
---

# Before/During/After Yellow Pages Exercise

## The exercise in one paragraph

Take a telephone directory (or its modern equivalent) and list 10 
familiar types of businesses. For each, map what customers buy 
before, during, and after purchasing the main product or service. 
The output identifies complementary businesses — partners, referral 
sources, and overlooked customer-journey participants.

## When to apply

- During workspace onboarding, after customer profile is set
- When looking for partnership candidates
- When ecosystem mapping has surfaced competitors but few complements
- Every quarter as a refresh

## Procedure

1. Load customer profile from workspace.yaml — specifically the 
   `customer.primary_profile.buys_before`, `.buys_during`, 
   `.buys_after` fields if already populated, otherwise this 
   skill populates them

2. For each category, ask the operator (or propose candidates):
   - What did they buy or use right before our product came into 
     their life?
   - What do they buy or use alongside our product?
   - What do they buy or use after our product has done its work?

3. For each named business type, classify:
   - Is it a candidate partner (non-competitive, audience overlap)?
   - Is it a trust-network voice (customers admire it)?
   - Is it a complementary source worth extracting signal from?

4. Write results to workspace ecosystem/complementary.yaml

## Calibration examples

See examples/yellow-pages/*.yaml for reference outputs across 
three verticals.

## Common pitfalls

- Listing only obvious direct-adjacencies (e.g., "a CRM" before 
  "a marketing tool"). Push for deeper customer-journey context.
- Mixing substitutes with complements. A substitute replaces; 
  a complement accompanies.
- Forgetting the "after" column. Most exercises focus on before 
  and during; the after column often reveals the richest partners.

## Refinements

(empty — add notes via `pulse refine-knowledge`)
```

Frontmatter declares what skills consume this file. That back-reference becomes the knowledge graph — when you update `yellow-pages.md`, you know which skills are affected.

### The `_quotes.yaml` sibling

Every framework directory has a `_quotes.yaml` file holding attributed excerpts:

```yaml
- id: qa_yp_001
  source: "Getting Everything You Can Out of All You've Got"
  author: "Jay Abraham"
  chapter: 7
  page: 142
  text: "Take a directory and list 10 familiar types of businesses..."
  context: "Core statement of the yellow-pages exercise."
  framework_use: "Canonical statement; quoted in training skills."

- id: qa_yp_002
  source: "Abraham Protege Program, Module 4"
  timestamp: "23:14"
  text: "The real question isn't who competes with you..."
  context: "Extension of the yellow-pages idea into trust-network territory."
```

Quotes are cross-referenced by ID from the framework doc. This keeps the framework doc readable and the attribution rigorous. It also keeps you safe from copyright issues — you maintain attributed excerpts as citations, not reproductions of full chapters.

### The `meta.yaml` per framework

Tracks version, last authored, source, changelog:

```yaml
framework: abraham
version: 2026.04.23
last_authored: 2026-04-23
last_authored_by: joe
sources:
  - name: "EPIC & Abraham NotebookLM"
    kind: notebooklm
    url: "https://notebooklm.google.com/notebook/..."
    account: joe@geniusscaleai.com
  - name: "Jay Abraham Collected Works"
    kind: book_collection
    location: corpus:frameworks/abraham/
topics_covered:
  - yellow-pages
  - cross-industry-intelligence
  - trust-network-profiling
changes:
  - version: 2026.04.23
    notes: initial authoring; three foundational topics documented
```

### Taxonomies

Small YAML files holding structured enums. Skills import these as authoritative sources of truth. Example:

```yaml
# taxonomies/strategic-roles.yaml

strategic_roles:
  - id: direct_competitor
    label: "Direct competitor"
    definition: "A company directly serving your customers with a similar offer."
    framework_origin: hormozi
    extracts_emphasized:
      - positioning
      - pricing
      - offer_structure
      - messaging_shifts

  - id: substitute
    label: "Substitute"
    definition: "An alternative solution your customer might choose instead."
    framework_origin: hormozi
    extracts_emphasized:
      - alternative_solution_framing
      - when_to_use_signals

  - id: complementary
    label: "Complementary"
    definition: "Something bought before, during, or after your product."
    framework_origin: abraham
    extracts_emphasized:
      - adjacent_purchase_context
      - customer_journey_context

  # ... and so on for all 10 roles
```

### Questionnaires

Structured question banks that kickoff skills walk the operator through. The most important one is `customer-profile.yaml`, documented in full in Doc 07. Others include `offer-articulation.yaml` (mechanism, promise, pricing), `position-matrix.yaml` (Robbins 4×2), `real-business.yaml` (the question that changes everything), and `goals-and-constraints.yaml` (what you're playing for).

Each questionnaire is a YAML file with a list of sections, each section a list of questions, each question typed (free_text, multiple_choice, ranked_list, structured_fields). See Doc 07 for the canonical example.

### Examples

Reference outputs for each skill. When `pulse map-ecosystem` runs, it can load `examples/ecosystem-map/*.yaml` to show the model what a good output looks like. These are calibration assets — they shape output quality more than any prompt tweak.

Each example directory contains 2-4 reference files covering different verticals (SaaS B2B, DTC product, services, marketplace) so skills have breadth.

### Source templates

Pre-built source configurations by strategic role and platform. Example: `source-templates/direct-competitor/saas-b2b.yaml` contains a standard set of URL patterns, extraction prompts, and schedule recommendations for tracking a B2B SaaS direct competitor. When `pulse add-source` runs, it can offer to populate from a template.

### Prompts

LLM prompt templates used by skills. These are `.md` files — not inlined in `SKILL.md` — so they can be refined independently. A skill declares which prompt it uses:

```yaml
---
name: pulse propose-hypothesis
uses_prompts:
  - synthesis/propose-hypothesis.md
---
```

And the runtime loads that prompt, interpolates workspace context, sends to Claude.

### Glossary

One YAML file with canonical definitions for every term used across the framework:

```yaml
direction:
  definition: "A vector being tracked in a workspace, with origin, trajectory, velocity, momentum, and state."
  distinguished_from:
    topic: "A topic is a noun; a direction is a vector."
  appears_in:
    - product_copy
    - frameworks/hormozi/commodity-pattern.md
    - taxonomies/direction-states.yaml

commodity_pattern:
  definition: "The undifferentiated baseline of claims, features, or positions multiple direct competitors make identically."
  framework_origin: hormozi
  related_terms:
    - category_of_one
    - differentiation
    - ecosystem_map

# [...]
```

The glossary is the single most valuable onboarding artifact for any new person joining the framework. Read the glossary, understand the domain.

## The corpus layer (optional, v1)

### What it is

A local, schema-enforced vector store over your source documents — the books, transcripts, courses, and notes that underpin the framework's substance. Queried during authoring of knowledge files, not at skill runtime.

```
~/.pulse/corpus/
├── raw/                              # source documents by bucket
│   ├── frameworks/
│   │   ├── hormozi/
│   │   ├── abraham/
│   │   ├── frasier/
│   │   ├── demandcurve/
│   │   ├── imperium/
│   │   └── robbins/
│   ├── industry/
│   │   └── <vertical>/
│   ├── case-studies/
│   ├── interviews/
│   └── workspace-specific/
│       └── <workspace_id>/
├── index/
│   └── lancedb/
├── schema.yaml                       # canonical collection + metadata schema
├── ingestion-log.jsonl               # append-only log
└── README.md
```

### The six collections

Each bucket under `raw/` represents a collection in the vector index with distinct metadata requirements:

**frameworks/** — the six business advisory frameworks. Required metadata: `framework` (enum of six), `source_title`, `source_type`. Optional: `chapter`, `page`, `timestamp`, `publication_date`, `topic_tags`.

**industry/** — general industry references by vertical. Required: `vertical`, `source_title`, `source_type`. Optional: `publication_date`, `geography`, `authority_tier` (primary_research / industry_analyst / trade_press / community).

**case-studies/** — worked examples illustrating specific framework applications. Required: `framework` (which framework the case illustrates), `business_model`. Optional: `revenue_range`, `outcome` (success / failure / turnaround), `topic_tags`.

**interviews/** — transcripts. JTBD interviews, customer calls, expert conversations, lost-deal interviews. Required: `interview_type`, `interviewee_role`. Optional: `workspace_id` (null for cross-workspace applicable), `date`, `topic_tags`.

**workspace-specific/** — per-workspace private corpus. Required: `workspace_id`, `content_type` (customer_note / competitor_intel / historical_context / etc). Never cross-workspace queried.

**misc/** — a catch-all for material that doesn't fit elsewhere. Required: `title`, `description`. Deliberately unstructured; use sparingly.

### The schema file

Lives at `corpus/schema.yaml` and is the authoritative source for what metadata each collection requires. Ingestion enforces it; queries filter against it; operators edit it to evolve the corpus structure.

Full example:

```yaml
version: 1

embedding:
  provider: voyage        # voyage | openai | anthropic | local_bge
  model: voyage-3
  dimensions: 1024

chunking:
  strategy: paragraph_aware
  target_tokens: 1000
  overlap_tokens: 200

retrieval:
  default_top_k: 20
  rerank: true
  rerank_model: voyage-rerank-2
  rerank_top_k: 5

collections:
  frameworks:
    metadata_required:
      - framework         # enum: hormozi, abraham, frasier, demandcurve, imperium, robbins
      - source_title
      - source_type       # enum: book | transcript | course | article | podcast | notes
    metadata_optional:
      - chapter
      - page
      - timestamp
      - publication_date
      - topic_tags

  industry:
    metadata_required:
      - vertical
      - source_title
      - source_type
    metadata_optional:
      - publication_date
      - geography
      - authority_tier

  case-studies:
    metadata_required:
      - framework
      - business_model
    metadata_optional:
      - revenue_range
      - outcome
      - topic_tags

  interviews:
    metadata_required:
      - interview_type
      - interviewee_role
    metadata_optional:
      - workspace_id
      - date
      - topic_tags

  workspace-specific:
    metadata_required:
      - workspace_id
      - content_type

  misc:
    metadata_required:
      - title
      - description
```

### How corpus content is ingested

Via the `pulse ingest` skill, documented in full in Doc 04. The flow, briefly: operator references files (via `@` in Claude Code, or via CLI args), selects bucket, provides required metadata, confirms. The skill chunks, embeds, indexes, logs.

Every ingestion is logged to `ingestion-log.jsonl`:

```jsonl
{"timestamp":"2026-04-23T14:22:00Z","file":"/Users/joe/Documents/100m-offers.pdf","bucket":"frameworks/hormozi","metadata":{"framework":"hormozi","source_title":"$100M Offers","source_type":"book","topic_tags":["offers","pricing","positioning"]},"chunks":84,"embedding_cost_usd":0.04}
```

This log is invaluable when debugging retrieval, reingesting with a different embedding model, or auditing the corpus composition.

### How the corpus is queried

Two entry points:

**`pulse corpus-query`** — direct CLI query, useful for ad-hoc research:

```
$ pulse corpus-query --collection frameworks --framework hormozi \
    --topic-tags pricing "how does Hormozi think about pricing ladders?"

Top 5 results:
  1. [Hormozi · $100M Offers · Ch. 9 · p.187] 
     "Pricing ladders let you capture customers at multiple willingness..."
  2. [Hormozi · $100M Offers · Ch. 9 · p.191]
     ...
  [...]

Show full chunks? [y/N]
```

**During authoring via `pulse author-knowledge`** — the main author-time integration. When authoring a knowledge file, the skill queries the corpus for relevant material and shows retrieved chunks, letting the operator curate what goes into the distilled knowledge file.

No skill calls the corpus during normal operational execution. Always author-time only.

## How skills consume knowledge

A skill's `SKILL.md` declares knowledge dependencies in frontmatter:

```yaml
---
name: pulse map-ecosystem
description: Apply Hormozi's Ecosystem Mapping exercise to a workspace.
knowledge:
  - frameworks/hormozi/ecosystem-mapping.md
  - frameworks/abraham/yellow-pages.md    # for before/during/after extension
  - taxonomies/strategic-roles.yaml
  - questionnaires/customer-profile.yaml
  - examples/ecosystem-map/
  - prompts/synthesis/find-commodity-pattern.md
uses_prompts:
  - synthesis/ecosystem-prompt.md
inputs:
  workspace_id: string
outputs:
  writes: ecosystem/map.yaml
---
```

At runtime, the skill's dispatcher loads all declared knowledge files, composes them into the prompt context, and executes the procedure. Knowledge loading is lazy — a file declared in `knowledge:` is only actually read when the procedure step that references it is reached.

## How knowledge gets authored and refined

Four mechanisms, in order of increasing automation:

### 1. Manual authoring

Knowledge files are text. Edit them. Commit. Done. For stable frameworks this is often the right tempo — you're not updating Hormozi weekly.

### 2. Corpus-assisted authoring via `pulse author-knowledge`

The main workflow. The skill:

1. Asks what you're authoring or refining
2. Loads the target knowledge file (if it exists) so you can see current state
3. Queries the corpus for relevant material
4. Shows retrieved chunks ranked by relevance
5. Lets you select which chunks to incorporate
6. Drafts a proposed update to the knowledge file
7. You review, edit, accept or reject
8. On accept: writes the file, updates `meta.yaml`, appends to `CHANGELOG.md`, updates `_quotes.yaml` with any newly-attributed excerpts

This is the workflow that makes the knowledge layer improve over time without drudgery.

### 3. Refinement notes via `pulse refine-knowledge`

After running a skill whose output felt off, invoke `pulse refine-knowledge <framework-topic>` to append a dated note to the knowledge file's `## Refinements` section. Over time these notes accumulate:

> 2026-04-23: When run on service businesses, the "what do they buy during?" prompt consistently surfaces nothing useful. Consider replacing with "what tools do they use?" for service verticals.

Notes don't change the procedure; they record observations for later.

### 4. Knowledge evolution via `pulse evolve-knowledge`

Periodically (quarterly), invoke `pulse evolve-knowledge <framework-topic>` to have the framework:

1. Read accumulated refinement notes
2. Propose revisions to the procedure based on the notes
3. Present diff for review
4. On accept: write the update, move notes to an archive section

This is how the framework compounds. Notes aren't just backlog; they become the raw material for continuous refinement.

## The relationship between corpus and knowledge

Three important relationships worth making explicit:

**Corpus is upstream of knowledge.** Content flows from raw source material, through the vector index, through author-knowledge sessions, into distilled knowledge files. The knowledge files are the skill-runtime artifact; the corpus is the authoring substrate.

**Knowledge can exist without corpus.** An operator who doesn't want to set up RAG infrastructure can still have a full knowledge layer. They'd author files manually, incorporating material from memory, books, notes, or other source methods. The framework works. It just doesn't have the corpus-assisted authoring convenience.

**Corpus can exist without heavy knowledge.** An operator early in framework use might ingest corpus material but not yet have time to author distilled knowledge files. Skills fall back gracefully — they can run on stub knowledge files or on knowledge files that reference corpus material more heavily. Quality is lower until the knowledge layer is built out, but the framework doesn't crash.

The ideal mature state is both layers rich: a deep corpus of source material, regularly mined; and a well-maintained knowledge layer that distills the corpus into skill-ready form.

## Knowledge layer versioning

Each framework directory's `meta.yaml` tracks its own version. Skills can record which knowledge version they used when they ran — stored in the run log. This becomes auditable history:

> Two quarters ago, `pulse map-ecosystem` ran against version 2026.01.15 of the Hormozi framework. The current version is 2026.04.23, which added guidance on identifying zombie-brand acquisition targets. Rerunning today would incorporate that.

This matters for client work where output differences between engagements need explanation.

## What goes in knowledge vs. corpus — the clear line

A question that comes up: for a given piece of substance, does it belong in `knowledge/` or in `corpus/raw/`?

The rule: **if a skill consumes it at runtime, it's knowledge; if only authoring consumes it, it's corpus**.

Hormozi's full "$100M Offers" text → corpus/raw/frameworks/hormozi/ (too long for runtime, used during authoring).

The distilled ecosystem-mapping procedure derived from that book → knowledge/frameworks/hormozi/ecosystem-mapping.md (used by `pulse map-ecosystem` at runtime).

A sharp division. Anything ambiguous — a 20-page chapter summary, a condensed version of a framework — goes in knowledge *only if a skill will consume it at runtime*. If it's just reference material you want searchable, it goes in corpus.
