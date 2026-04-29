# 10 — Corpus Setup Guide

This is the operator-facing guide to setting up the local RAG corpus well. The corpus is optional, but if you enable it, the quality of corpus-assisted authoring depends entirely on how thoughtfully you set it up. This guide covers embedding provider tradeoffs, chunking defaults, metadata discipline, what to ingest first per framework, and the work estimates for getting to a useful baseline.

The audience here is the operator (you, Joe — or any human running this framework), not the build agent. Read this when you're standing in front of `pulse init` deciding whether to enable corpus and how to populate it.

## When to enable corpus

Enable corpus if any of these are true:

- You have framework source documents (books, PDFs, course materials, transcripts) you want queryable
- You want corpus-assisted authoring of knowledge files (`pulse author-knowledge` becomes meaningfully better with corpus)
- You expect to ingest 20+ documents over the framework's lifetime
- You're running this for client work and want to build accumulated reference material across engagements

Skip corpus if any of these are true:

- You're trying the framework out for the first time and want to see if it's useful before investing in setup
- You don't have source documents handy
- You're working in a constrained environment where adding ~280MB of dependencies is friction
- You'd rather author knowledge manually for now and enable corpus later (you can always run `pulse enable corpus` after the fact)

The framework works well in either mode. Corpus accelerates authoring; it doesn't change runtime behavior.

## Embedding provider tradeoffs

The most consequential setup choice. Four options:

### Voyage AI (recommended default)

- **Model**: `voyage-3` (1024 dimensions)
- **Cost**: ~$0.06 per million tokens at the time of writing
- **Quality**: Best-in-class retrieval quality for English-language technical and business content
- **Reranker**: `voyage-rerank-2` available (highly recommended; bumps top-k results from "decent" to "uncannily good")
- **Privacy**: API call; embeddings sent to Voyage servers
- **Setup**: API key from voyageai.com; paid

This is the recommended default. The retrieval quality difference vs OpenAI on framework-style queries is large enough to matter. The cost is negligible for the volumes a single advisor will produce.

### OpenAI

- **Model**: `text-embedding-3-large` (3072 dimensions, configurable down to 256)
- **Cost**: ~$0.13 per million tokens
- **Quality**: Excellent, slightly behind Voyage on technical content
- **Reranker**: not native (you'd add Cohere rerank or skip)
- **Privacy**: API call; embeddings sent to OpenAI servers; data not used for training per OpenAI's API terms
- **Setup**: API key from platform.openai.com; paid

Reasonable choice if you already have an OpenAI account and don't want another vendor relationship. Slightly more expensive, slightly worse retrieval, but mature and reliable.

### Anthropic (via Claude API)

- **Model**: Anthropic's embedding models (when generally available)
- **Cost**: TBD
- **Quality**: TBD; expected competitive with OpenAI
- **Privacy**: API call to Anthropic
- **Setup**: same Claude API key the framework already uses

Worth choosing if you want to consolidate to one vendor (Anthropic for both LLM and embeddings) and minimize the surface of API keys you manage.

### Local (BGE-M3 via sentence-transformers)

- **Model**: `BAAI/bge-m3` (1024 dimensions)
- **Cost**: $0 ongoing (no API)
- **Quality**: Surprisingly strong for an open-source model; near OpenAI on most retrieval benchmarks
- **Reranker**: `BAAI/bge-reranker-v2-m3` (also local)
- **Privacy**: Fully local; nothing leaves your machine
- **Setup**: `pip install sentence-transformers`; first run downloads the model (~2GB)
- **Hardware**: needs a GPU for reasonable embedding speed; CPU works but slow (~10x slower)

Choose this if privacy is non-negotiable (sensitive client work) or if you want zero ongoing API costs. The quality tradeoff is small; the setup friction is the main cost.

### How to choose

A simple decision tree:

- **Privacy is critical** (you're doing M&A diligence, sensitive client work, or you just don't want anything leaving your machine) → Local BGE-M3
- **You already have OpenAI for other things and don't want a new vendor** → OpenAI text-embedding-3-large
- **You want best-in-class quality at minimal cost** → Voyage voyage-3
- **You want minimum vendors** → Anthropic embeddings

If you have no strong preference, take the recommended default (Voyage voyage-3 with voyage-rerank-2). For a single advisor's typical volume — say, 200 ingested documents over a year — total embedding cost is under $5.

## Chunking defaults

The framework uses paragraph-aware chunking with these defaults:

- **Target chunk size**: 1000 tokens
- **Overlap**: 200 tokens
- **Strategy**: prefer splitting on paragraph boundaries; fall back to sentence boundaries; last resort token boundaries

These are good defaults for the kinds of documents you'll ingest (books, course transcripts, articles, notes). Reasoning:

**Why 1000 tokens.** Smaller chunks (200-400 tokens) give precise retrieval but lose surrounding context, making the LLM work harder to integrate them. Larger chunks (2000+) provide context but produce noisier matches and waste prompt budget. 1000 is the sweet spot for text-heavy framework documents.

**Why 200 token overlap.** A concept that spans a chunk boundary would otherwise be split awkwardly. 20% overlap means concepts at boundaries appear in both adjacent chunks, so retrieval doesn't miss them.

**Why paragraph-aware.** Splitting mid-paragraph or mid-sentence destroys the semantic units the embedding model is most sensitive to. A chunk that ends mid-sentence retrieves worse than one that ends at a paragraph break, even at the same token count.

You can override these per-collection in `corpus/schema.yaml`. Don't bother unless you have specific reasons; the defaults are well-tuned.

### When to deviate

A few legitimate cases for non-default chunking:

- **Code-heavy documents** (technical specs, code samples): smaller chunks (500 tokens) with no overlap. Code snippets are atomic; cross-snippet overlap doesn't help.
- **Highly structured reference material** (taxonomies, dictionaries, glossaries): one entry per chunk regardless of size.
- **Conversation transcripts**: chunk by speaker turn, not by token count.

Configure these in `schema.yaml` per collection if needed.

## Metadata discipline

The single most important discipline in corpus setup.

The temptation when ingesting a document is to skip the metadata prompts ("just put it in, I'll fix it later"). Don't. Every chunk is forever stamped with whatever metadata it had at ingestion time. Fixing it later means re-ingesting, which costs API calls and breaks any references that might exist.

### Required metadata, by collection

Refresher from Doc 01 — these are the non-skippable fields:

**frameworks/**
- `framework`: which of the six (hormozi, abraham, frasier, demandcurve, imperium, robbins)
- `source_title`: human-readable title (e.g., "$100M Offers")
- `source_type`: book, transcript, course, article, podcast, notes

**industry/**
- `vertical`: which industry vertical
- `source_title`
- `source_type`

**case-studies/**
- `framework`: which framework the case illustrates
- `business_model`: saas, ecom, services, marketplace, etc.

**interviews/**
- `interview_type`: jtbd, customer_call, expert, lost_deal
- `interviewee_role`: title or role descriptor

**workspace-specific/**
- `workspace_id`: which workspace this belongs to
- `content_type`: customer_note, competitor_intel, historical_context, etc.

**misc/**
- `title`
- `description`

### Optional but high-value

The optional fields make later querying dramatically more useful:

- **`topic_tags`**: comma-separated tags. Spend a moment on these. Good tags (`pricing`, `positioning`, `commodity_pattern`) make later filtered queries effortless. Generic tags (`business`, `strategy`) are useless.

- **`chapter` and `page`** for books: makes citations rigorous. Operator running `pulse author-knowledge` gets back chunks that say "Chapter 7, p. 142" rather than "somewhere in the corpus."

- **`timestamp`** for transcripts: same value for audio/video material.

- **`publication_date`**: helps detect when corpus content has aged out and needs refresh.

### A discipline that pays off

A simple rule: when ingesting a document, type three to five topic tags before moving on. Just three. They don't have to be perfect. They just have to exist.

```
Topic tags? > pricing, ladders, value_proposition, commodity_pattern
```

Five seconds. The payoff is that six months from now when you're querying "what does Hormozi say about pricing ladders," the top-5 results are exactly the right chunks rather than a vaguely-related grab bag.

Skipping topic tags is a false economy. The minutes you save during ingestion you pay back tenfold in retrieval frustration.

## What to ingest first, by framework

If you're starting with an empty corpus and want to bootstrap quickly, here's a recommended ingestion sequence by framework. Each list is roughly ordered by retrieval-impact-per-page-ingested.

### Hormozi

1. **`$100M Offers`** (book) — the foundational text on offer construction, pricing, value equations. ~250 pages.
2. **`$100M Leads`** (book) — companion volume on lead generation, four core methods, ladders. ~280 pages.
3. **Hormozi YouTube transcripts on positioning** — selected videos on commodity-pattern detection, category-of-one thinking. ~30-50 transcripts of 10-30 minutes each.
4. **Acquisition.com community materials** if you have access — case study breakdowns of portfolio companies.

Tags worth applying liberally: `offers`, `pricing`, `value_equation`, `lead_magnets`, `commodity_pattern`, `category_of_one`, `ecosystem_map`, `irresistible_offer`.

### Abraham

1. **`Getting Everything You Can Out of All You've Got`** (book) — core text. ~350 pages. Especially the chapters on yellow-pages exercise, cross-industry intelligence, host-beneficiary relationships.
2. **EPIC NotebookLM exports** if you have them — the Protege Program transcripts.
3. **Joint venture frameworks** — articles, podcast appearances on partnership construction.
4. **Direct response classics** — Halbert, Hopkins, Sugarman if available; Abraham's intellectual lineage.

Tags: `yellow_pages`, `cross_industry`, `joint_venture`, `host_beneficiary`, `prospect_profile`, `trust_network`, `lifetime_value`.

### Frasier

1. **Acquisition Wheel course materials** if available — the canonical operationalization of the framework.
2. **Capability audit templates and worked examples**.
3. **5-80-5 canvas materials** — the strategic framing tool.

Tags: `acquisition_wheel`, `capability_audit`, `5_80_5`, `roll_up`, `operating_partner`.

### DemandCurve

1. **JTBD playbook** (course or guide) — the canonical methodology.
2. **Review mining methodology** — articles, course modules on extracting insight from review aggregators.
3. **Unique mechanism framework** — DemandCurve's positioning approach.
4. **Selected case study breakdowns** — DemandCurve has published many; the ones in your specific verticals are gold.

Tags: `jtbd`, `interview_methodology`, `review_mining`, `unique_mechanism`, `dissatisfied_customer`, `positioning`.

### Imperium

1. **Niche research SOP** — the canonical document on systematic niche research.
2. **Active intelligence framework** — the methodology for ongoing competitive observation.
3. **Selected case studies** of niche operations.

Tags: `niche_research`, `active_intelligence`, `competitive_observation`, `vertical_specialization`.

### Robbins

This one's more bespoke since the canonical Robbins material is mostly your own notes:

1. **Your notes on Robbins lifecycle stages and seasons** — author these as knowledge files first, then optionally ingest the source notes.
2. **The 7-step / 7-week system** — when you document it, ingest your own write-up.
3. **Tony Robbins source material** if you have it (Business Mastery, Date with Destiny notes, etc.).
4. **The "what business are you really in?" question** — supporting material from any source.

Tags: `lifecycle_stages`, `seasons`, `position_matrix`, `real_business`, `7_step_7_week`.

## Cross-framework material

A few categories worth ingesting that don't fit neatly under one framework:

### Industry references

For each vertical you work in, ingest:

- **Industry analyst reports** (Gartner, Forrester, IDC, vertical-specific analysts)
- **Trade press summaries** of the year's major shifts
- **Regulatory texts** if your vertical is regulated
- **Annual State of X reports** (State of SaaS, State of Marketplace, etc.)

Tag with `vertical: <vertical>`, `authority_tier: industry_analyst | trade_press | primary_research | community`.

### Case studies

Cross-framework worked examples. A great Hormozi-style breakdown of a specific business goes here, tagged with both the business model and the framework being applied.

### Interviews

Whenever you do JTBD interviews, customer calls, or expert conversations, ingest the transcripts here. Tag with `interview_type` and `interviewee_role`. These often produce the highest-leverage retrieval results because they contain language directly from the customer.

## Reranker setup

If you chose Voyage as your embedding provider, also enable `voyage-rerank-2` in `schema.yaml`:

```yaml
retrieval:
  default_top_k: 20
  rerank: true
  rerank_model: voyage-rerank-2
  rerank_top_k: 5
```

How reranking works: initial vector search returns 20 candidates; the reranker scores them with a more expensive but more accurate model; top 5 are returned. The tradeoff is one extra API call per query for substantially better results.

For OpenAI embeddings, the equivalent is Cohere rerank (`rerank-english-v3.0`); enable similarly if you have a Cohere API key.

For local BGE-M3, use the local `BAAI/bge-reranker-v2-m3` (downloaded on first use).

Reranker on is the right default for almost all use cases. Disable only if you're optimizing for ingestion-time queries that need to be sub-100ms.

## Workspace-specific corpus

Each workspace can have its own corpus content under `corpus/raw/workspace-specific/<workspace_id>/`. This is for:

- **Customer interview transcripts** for that specific client
- **Competitor intelligence** specific to that workspace's market
- **Historical context documents** about the client's business
- **Internal documents** the client has shared (with appropriate confidentiality)

These are queried only when the active workspace matches. Cross-workspace leakage doesn't happen by default.

The discipline: when you're working with a client and they share materials, ingest them into their workspace-specific corpus rather than a global bucket. You'll thank yourself when you're working with multiple clients and don't want their materials cross-contaminating each other's reasoning.

## Corpus prep work estimates

Realistic effort to bootstrap a useful corpus:

- **Minimum useful** (one framework, foundational texts only): 1-2 hours setup, ~30 documents, ~$1 in embedding costs
- **Solid baseline** (all six frameworks at primary-text depth): 4-6 hours setup, ~100 documents, ~$3 in embedding costs
- **Mature corpus** (frameworks + industry references + 20+ interviews + case studies): 15-25 hours of cumulative ingestion over months, ~500-1000 documents, ~$15-30 in cumulative embedding costs

The mature state is reached over months, not weeks. Don't try to do it in one sitting. Ingest as you encounter material.

## Common mistakes to avoid

A short list of things people do wrong:

1. **Ingesting first, deciding metadata later.** Always do metadata at ingestion. Re-ingestion is more painful than it sounds.

2. **One mega-collection.** Resist putting everything under `misc/`. The collection structure is what makes filtered queries possible.

3. **Sloppy topic tags.** A tag like `business` matches everything and helps nothing. Tags like `pricing_ladder`, `commodity_detection`, `host_beneficiary_construction` are precise and powerful.

4. **Ignoring chapter/page metadata for books.** Citation rigor matters. Spend the extra 30 seconds to enter chapter and approximate page when ingesting a book.

5. **Cross-pollinating workspace-specific corpus.** When client A's materials go into the global frameworks bucket "because it's a good case study," you've broken confidentiality. Workspace-specific stays workspace-specific.

6. **Setting up the corpus then never querying it.** Run `pulse corpus-query` periodically just to verify retrieval works as expected. If you ingested badly, you'll notice fast and can re-ingest before the bad data accumulates.

7. **Not ingesting your own work.** Your own past briefs, positioning statements, customer interviews, and learnings are some of the highest-value corpus material. Treat them as first-class content, not an afterthought.

## A reasonable starting protocol

If you want a concrete first session for setting up corpus, here's a 90-minute protocol:

**Minutes 0-10**: Run `pulse init` with corpus enabled. Pick Voyage as embedding provider. Verify the install completed.

**Minutes 10-30**: Ingest one foundational text per framework you actively use. PDFs of `$100M Offers`, the Abraham core text, your DemandCurve playbook, etc. Type metadata carefully. Use 3-5 topic tags per document.

**Minutes 30-60**: Ingest your own existing knowledge — past notes, briefs, positioning documents you've written for your own business or clients you've worked with before. Tag them workspace-specific where appropriate; tag them as case-studies where they're generalizable.

**Minutes 60-75**: Run a few `pulse corpus-query` invocations to test retrieval. Try queries you'd expect to work well and queries you're less sure about. Note the quality.

**Minutes 75-90**: Run `pulse author-knowledge` against one stub knowledge file (say, `frameworks/hormozi/ecosystem-mapping.md`). See how the corpus-assisted authoring feels. Refine the file. Save.

After 90 minutes: corpus is bootstrapped. You have ~10-20 documents indexed, you've validated retrieval works, you've authored one knowledge file with corpus assistance. Future ingestion happens incrementally as you encounter new material.

That's the on-ramp. From here, the corpus deepens with use.
