# 07 — Customer Profile Questionnaire

This is the single highest-leverage artifact in the entire framework. Every downstream skill depends on a rich customer profile. Ecosystem mapping needs it. Commodity-pattern detection needs it. Gap-map synthesis needs it. Content briefs need it. Positioning statements need it. Survey generation needs it.

A workspace with a thin customer profile produces thin outputs. A workspace with a deep, specific, well-authored profile produces outputs that feel startlingly grounded.

This document defines the full questionnaire: what it captures, how it's structured, how the `pulse profile-customer` skill walks the operator through it, and how the resulting data flows into every other skill.

## The questionnaire's role

When `pulse profile-customer <workspace_id>` runs, it walks the operator through a structured interview that takes 20-35 minutes. The output is the `customer:` block in `workspace.yaml` — a rich, multi-dimensional profile of the target customer synthesized from the frameworks (Abraham's prospect profiling, DemandCurve's JTBD, Imperium's niche research, Hormozi's ecosystem thinking).

Ideally, the operator has already:

- Talked to real customers (even informally)
- Read 10-20 reviews of competitors
- Observed where their customers hang out

If they haven't, the skill can still run — it'll produce a reasoned best-guess profile — but the skill marks fields as `confidence: low` where the operator is guessing, and recommends specific research actions (`pulse mine-reviews` on particular aggregators, JTBD interviews with existing customers) to firm up low-confidence fields over the following weeks.

## The four tiers

The questionnaire is organized in four tiers of depth. Each tier stands alone as a usable profile; each subsequent tier deepens the prior.

**Tier 1: Identity (5 min)** — demographic and firmographic basics. The minimum needed for other skills to function. If time pressure demands it, an operator could stop here and still use the framework, with reduced output quality.

**Tier 2: Psychology (8 min)** — worldview, anxieties, aspirations, decision style, status signals. This is where the profile starts to produce actually-specific outputs downstream.

**Tier 3: Jobs and pain (8 min)** — JTBD, pain points, current solutions, switching costs. DemandCurve-heavy. This is where content briefs and surveys gain real teeth.

**Tier 4: Trust network and ecosystem (10 min)** — who they admire, where they hang out, what they buy before/during/after. Abraham and Hormozi combined. This is what lets `pulse map-ecosystem` and `pulse map-trust-network` produce rich output without starting from zero.

Total: 20-35 minutes of deliberate questioning. One of the highest-ROI hours an operator can invest in the framework.

## The full question bank

Canonical form as `knowledge/questionnaires/customer-profile.yaml`:

```yaml
version: 1
tier_1_time_min: 5
tier_2_time_min: 8
tier_3_time_min: 8
tier_4_time_min: 10
total_time_min: "20-35"

intro: >
  This questionnaire builds the foundational customer profile every 
  downstream Pulse skill draws on. It's organized in four tiers of 
  depth. You can stop after any tier and come back — each tier 
  stands alone as a usable profile.

  Answer as specifically as you can. If you don't know, say so 
  explicitly ("I don't know yet — need to research") and we'll 
  flag those fields for later firming up.

sections:

  # ────────────────────────────────────────────────────────────
  # TIER 1: IDENTITY
  # ────────────────────────────────────────────────────────────

  - id: tier_1
    tier: 1
    title: "Who they are (identity)"
    description: "Demographic and firmographic basics."
    
    questions:
      
      - id: descriptor
        type: free_text
        prompt: >
          In one sentence, who is your primary target customer? 
          (Imagine describing them to a new hire in 10 seconds.)
        example: >
          "AI-curious SMB founders, 10-50 employees, $1M-$20M revenue, 
          running professional services or early-stage software businesses."
        writes_to: customer.primary_profile.descriptor

      - id: role_titles
        type: multi_value
        prompt: >
          What specific titles or roles do they hold? 
          (List 3-5.)
        example: "[Founder, CEO, Co-founder, Chief of Staff]"
        writes_to: customer.primary_profile.demographics.role_titles

      - id: company_stage
        type: enum
        prompt: "What stage company do they typically run?"
        options:
          - pre_revenue
          - early_revenue          # <$500K ARR
          - early_growth           # $500K-$5M
          - scale                  # $5M-$50M
          - mid_market             # $50M-$500M
          - enterprise             # $500M+
        writes_to: customer.primary_profile.demographics.company_stage

      - id: revenue_range_usd
        type: free_text
        prompt: "Revenue range (USD)?"
        example: "1M-20M"
        writes_to: customer.primary_profile.demographics.revenue_range_usd
        
      - id: employee_range
        type: free_text
        prompt: "Team size range?"
        example: "10-50"
        writes_to: customer.primary_profile.demographics.employee_range

      - id: industries_served
        type: multi_value
        prompt: >
          What industries are they primarily in? 
          (List 2-5 — or say "industry-agnostic" if that's the positioning.)
        example: "[professional_services, e-commerce, b2b_saas]"
        writes_to: customer.primary_profile.demographics.industries_served

      - id: geography
        type: structured
        prompt: "Primary and secondary geographies?"
        fields:
          - name: primary
            type: free_text
            example: "US_Canada"
          - name: secondary
            type: multi_value
            example: "[UK, AU]"
        writes_to: customer.primary_profile.demographics.geography_primary
                   customer.primary_profile.demographics.geography_secondary

      - id: tech_stack_signals
        type: free_text
        prompt: >
          What technology do they typically use? Any telltale stack signals 
          (e.g., uses Notion, not Confluence; uses Linear, not Jira)?
        example: >
          Notion, Slack, Linear, Vercel, Supabase, Stripe. Modern stack,
          avoids enterprise incumbents.
        writes_to: customer.primary_profile.demographics.tech_stack_signals

  # ────────────────────────────────────────────────────────────
  # TIER 2: PSYCHOLOGY
  # ────────────────────────────────────────────────────────────

  - id: tier_2
    tier: 2
    title: "How they think (psychology)"
    description: "Worldview, anxieties, aspirations, decision style."
    
    questions:
      
      - id: worldview
        type: long_text
        prompt: >
          Describe their worldview in 2-3 sentences. What's their 
          stance toward their industry? What do they believe about 
          how business should work? What are they skeptical of?
        example: >
          Skeptical of enterprise SaaS and its complexity. Values operator 
          leverage over team growth. Admires first-principles thinkers and 
          anti-establishment voices. Reads The Information and Stratechery.
          Suspicious of hype cycles but trusts peer recommendations.
        writes_to: customer.primary_profile.psychographics.worldview

      - id: anxieties
        type: multi_value
        prompt: >
          What anxieties keep them up at night? What are they afraid of?
          (3-7 specific items.)
        example: |
          - falling behind on AI while competitors catch up
          - hiring mistakes that slow the team
          - vendor lock-in to tools that will outgrow their usefulness
          - missing a category shift that reshapes their market
          - running out of runway before product-market fit hardens
        writes_to: customer.primary_profile.psychographics.anxieties

      - id: aspirations
        type: multi_value
        prompt: >
          What do they aspire to? What does "winning" look like for them?
          (3-5 specific items.)
        example: |
          - build something durable that outlasts fashion cycles
          - stay lean while growing revenue 3x/year
          - be cited as an authority in their space
          - avoid becoming "just another SaaS"
          - have real leverage (time, capital, attention)
        writes_to: customer.primary_profile.psychographics.aspirations

      - id: decision_style
        type: enum
        prompt: "How do they make buying decisions?"
        options:
          - fast_informed_skeptical       # research then decide quickly
          - slow_consensus                # committee-based, multiple stakeholders
          - experimental_iterative        # try small, expand
          - recommendation_driven         # buy what trusted voices buy
          - analysis_paralysis            # research endlessly
        writes_to: customer.primary_profile.psychographics.decision_style

      - id: buying_triggers
        type: multi_value
        prompt: >
          What events or feelings trigger buying behavior for them? 
          (3-5 specific triggers.)
        example: |
          - a trusted voice publicly endorses a tool or approach
          - a visible competitor adopts something
          - a specific failure or near-miss creates urgency
          - a pricing change makes a previously-deferred tool accessible
          - a team member advocates strongly for something
        writes_to: customer.primary_profile.psychographics.buying_triggers

      - id: status_signals
        type: multi_value
        prompt: >
          What do they do or own that signals status within their peer 
          group? (Helps identify hangout venues and publication preferences.)
        example: |
          - subscribes to paid newsletters (The Information, Stratechery)
          - attends SaaStr / ShopTalk / Y Combinator events
          - active on X, follows specific accounts
          - has a personal domain with a thoughtful blog
          - podcast guest appearances
        writes_to: customer.primary_profile.psychographics.status_signals

      - id: self_narrative
        type: long_text
        prompt: >
          How do they describe themselves when they introduce themselves?
          What story do they tell about what they do? (This reveals their 
          real identity — often different from their LinkedIn title.)
        example: >
          "I'm building a company that combines AI with <domain expertise> 
          to solve <specific problem>." Often avoids "founder" or "CEO" 
          in favor of "operator" or "builder." Emphasizes the work, not 
          the title.
        writes_to: customer.primary_profile.psychographics.self_narrative

      - id: language_they_use
        type: long_text
        prompt: >
          What specific words, phrases, or jargon do they use frequently? 
          What words do they avoid? This language becomes input for 
          positioning, content, and outreach drafts.
        example: >
          Uses: "leverage," "operator," "compounding," "durable," "build," 
          "ship," "first principles." Avoids: "synergy," "solution" (as 
          marketing word), "enterprise-grade," "transformation," "scale" 
          (as a verb).
        writes_to: customer.primary_profile.psychographics.language

  # ────────────────────────────────────────────────────────────
  # TIER 3: JOBS AND PAIN
  # ────────────────────────────────────────────────────────────

  - id: tier_3
    tier: 3
    title: "What they hire for (jobs to be done)"
    description: "JTBD, pain points, current solutions, switching costs."
    
    questions:

      - id: jobs_to_be_done
        type: structured_list
        prompt: >
          What jobs are they hiring your product or service to do? 
          (DemandCurve-style JTBD statements: "when ___, I want to ___, 
          so I can ___".) List 3-5 distinct jobs, in order of 
          importance.
        fields:
          - name: job
            type: free_text
            example: >
              "figure out which AI tools are worth adopting without 
              wasting weeks evaluating"
          - name: when_trigger
            type: free_text
            example: "quarterly planning, when budget is on the table"
          - name: so_that
            type: free_text
            example: "my team doesn't fall behind on capability curves"
          - name: urgency
            type: enum
            options: [critical, high, medium, low, background]
          - name: frequency
            type: enum
            options: [continuous, weekly, monthly, quarterly, annually, one_time]
        writes_to: customer.primary_profile.jobs_to_be_done

      - id: pain_points
        type: multi_value
        prompt: >
          What specific pains do they feel in their current state? 
          (Use their language. 5-10 items ideally.)
        example: |
          - "can't evaluate AI vendor claims"
          - "tools don't integrate with our stack"
          - "team resistance or skepticism toward AI"
          - "budget pressure from leadership"
          - "analysis paralysis — too many options"
          - "vendor noise makes it hard to find real signal"
          - "no clear ROI story for AI experiments"
        writes_to: customer.primary_profile.pain_points

      - id: current_solutions
        type: multi_value
        prompt: >
          What are they doing today to solve these jobs? (Even if 
          badly. Current solutions reveal switching dynamics and 
          competitive moats.)
        example: |
          - "ChatGPT Team subscriptions for the team"
          - "internal scripts hacked together by engineers"
          - "ad-hoc consulting engagements"
          - "trying tools from YC batches"
          - "reading newsletters and hoping to absorb"
        writes_to: customer.primary_profile.current_solutions

      - id: switching_friction
        type: long_text
        prompt: >
          What makes it hard for them to switch from their current 
          solutions to yours? (Time, money, habit, org politics, 
          sunk cost, learning curve, etc.)
        example: >
          Moderate switching friction. Most haven't committed deeply 
          to any AI stack, so there's low sunk cost. But there's 
          analysis paralysis: having tried 3-4 tools and been 
          disappointed, they're skeptical of yet another claim. 
          Trust barrier is higher than tool barrier.
        writes_to: customer.primary_profile.switching_friction

      - id: wins_they_want
        type: multi_value
        prompt: >
          What specific wins or outcomes would make them say "this 
          was worth it"? (This is the real success criterion for 
          your offer.)
        example: |
          - "saved 10+ hours a week on research and decision-making"
          - "shipped 2-3 AI features customers actually use"
          - "my team stopped asking me 'what about AI?' constantly"
          - "I can point to specific revenue from AI initiatives"
          - "I feel caught up, not behind"
        writes_to: customer.primary_profile.wins_they_want

      - id: wish_list_items
        type: multi_value
        prompt: >
          What are the "I wish..." statements you've heard from them?
          (Direct quotes from reviews, sales calls, customer interviews. 
          Gold for gap-map synthesis.)
        example: |
          - "I wish I had one person who could just tell me what's real 
             and what's hype"
          - "I wish these tools worked together"
          - "I wish I could pay for outcomes, not software seats"
          - "I wish someone would just build this the right way"
        writes_to: customer.primary_profile.wish_list_items

      - id: dissatisfactions_with_alternatives
        type: long_text
        prompt: >
          What do they complain about regarding your competitors or 
          alternatives? (Pulled from reviews, forums, word-of-mouth. 
          Source material for positioning.)
        example: >
          Complaints about consulting firms: too slow, too generic, 
          won't commit to delivery. Complaints about SaaS tools: 
          don't actually work out of the box, require lots of setup, 
          integrations are janky. Complaints about AI products 
          specifically: hype ratio too high, "it fails on my real 
          use cases."
        writes_to: customer.primary_profile.dissatisfactions_with_alternatives

  # ────────────────────────────────────────────────────────────
  # TIER 4: TRUST NETWORK AND ECOSYSTEM
  # ────────────────────────────────────────────────────────────

  - id: tier_4
    tier: 4
    title: "Who they trust and where they go (trust network + ecosystem)"
    description: >
      Abraham's prospect profiling combined with Hormozi's ecosystem 
      mapping. Who do they admire? What do they read? Where do they 
      hang out? What do they buy before, during, and after?
    
    questions:

      - id: trust_voices
        type: structured_list
        prompt: >
          Who are the specific voices, experts, or authorities they 
          admire or follow? (Abraham's trust-network question. List 
          5-10 with rationale.)
        fields:
          - name: name
            type: free_text
            example: "Alex Hormozi"
          - name: why
            type: free_text
            example: "pragmatic, operator-framed, anti-enterprise"
          - name: platform
            type: free_text
            example: "YouTube / X / Acquisition.com"
        writes_to: customer.primary_profile.trust_voices

      - id: publications_read
        type: multi_value
        prompt: >
          What publications, newsletters, or blogs do they read regularly?
        example: |
          - "The Information (paid)"
          - "Stratechery (paid)"
          - "Lenny's Newsletter"
          - "Not Boring"
          - "specific Substacks: Dan Shipper's Every, Packy McCormick"
        writes_to: customer.primary_profile.publications_read

      - id: podcasts_listened
        type: multi_value
        prompt: >
          What podcasts do they listen to?
        example: |
          - "Acquired"
          - "All-In"
          - "The Diary of a CEO"
          - "Lenny's Podcast"
          - "First Million"
        writes_to: customer.primary_profile.podcasts_listened

      - id: events_attended
        type: multi_value
        prompt: >
          What events or conferences do they attend (or wish they could)?
        example: |
          - "SaaStr Annual"
          - "YC Demo Days (as observer)"
          - "AI Engineer Summit"
          - "local founder dinners"
        writes_to: customer.primary_profile.events_attended

      - id: hangouts_online
        type: multi_value
        prompt: >
          Where do they hang out online? Communities, subreddits, 
          Discords, Slacks, forums, specific X searches?
        example: |
          - "r/ExperiencedDevs"
          - "r/EntrepreneurRideAlong"
          - "SaaStr Slack"
          - "Lenny's Newsletter community"
          - "Hormozi's Skool community"
          - "specific X followers of @sama, @patio11, @karpathy"
        writes_to: customer.primary_profile.hangouts_online

      - id: hangouts_offline
        type: multi_value
        prompt: >
          Where do they hang out offline? Cities, coworking spaces, 
          meetups, bars, sports, coffee shops?
        example: |
          - "NYC, SF, Austin, Miami for founder community"
          - "local founder dinners"
          - "specific coworking spaces (WeWork Brooklyn, South Park)"
          - "Whoop / Peloton / running communities"
        writes_to: customer.primary_profile.hangouts_offline

      - id: buys_before
        type: multi_value
        prompt: >
          What do they buy or use BEFORE your product comes into 
          their life? (Hormozi/Abraham before-during-after. Reveals 
          complementary partners and customer-journey entry points.)
        example: |
          - "CRM (Hubspot, Pipedrive)"
          - "analytics (Segment, Amplitude)"
          - "project management (Linear, Notion)"
          - "basic AI tools (ChatGPT Team, GitHub Copilot)"
        writes_to: customer.primary_profile.buys_before

      - id: buys_during
        type: multi_value
        prompt: >
          What do they buy or use ALONGSIDE your product?
        example: |
          - "OpenAI / Anthropic API credits"
          - "vertical SaaS for their specific industry"
          - "bookkeeping / legal services"
          - "performance marketing tools"
          - "customer support tools"
        writes_to: customer.primary_profile.buys_during

      - id: buys_after
        type: multi_value
        prompt: >
          What do they buy or use AFTER your product has done its 
          work — or as they mature?
        example: |
          - "custom development contractors"
          - "AI infrastructure (Pinecone, Replicate, Modal)"
          - "more sophisticated observability (Datadog, Sentry)"
          - "growth marketing consultancies"
          - "advisory board / fractional execs"
        writes_to: customer.primary_profile.buys_after

      - id: direct_competitors_named
        type: multi_value
        prompt: >
          Name 5-10 direct competitors they're aware of or have 
          considered. (Hormozi ecosystem starting point.)
        example: |
          - "Gradient AI"
          - "Scale AI (enterprise arm)"
          - "Anyscale"
          - "Consulting firms: Slalom, Accenture AI practice"
          - "Freelancer marketplaces (Toptal AI specialty)"
        writes_to: customer.primary_profile.direct_competitors_known

      - id: adjacent_winners
        type: multi_value
        prompt: >
          What businesses in completely different industries would 
          serve as models or inspirations for your positioning? 
          (Abraham cross-industry intelligence. Often the most 
          surprising and useful answers here.)
        example: |
          - "Shopify — opinionated platform for a specific operator type"
          - "Linear — tool that won by being opinionated against 
             enterprise defaults"
          - "Stripe — premium pricing defended by quality positioning"
          - "Basecamp — bootstrapped longevity in a VC-heavy space"
        writes_to: customer.primary_profile.adjacent_winners_inspiration

  # ────────────────────────────────────────────────────────────
  # META: CONFIDENCE AND RESEARCH QUEUE
  # ────────────────────────────────────────────────────────────

  - id: meta
    tier: all
    title: "Confidence and research queue"
    description: "Mark any fields where you're guessing rather than knowing, and queue research actions."
    
    questions:
      
      - id: low_confidence_fields
        type: multi_select_from_prior
        prompt: >
          Which fields were you mostly guessing on? Marking them low 
          confidence means we'll flag them in future skill runs and 
          recommend specific research to firm them up.
        source: all_fields_above
        writes_to: customer.primary_profile._low_confidence_fields

      - id: research_queue
        type: multi_value
        prompt: >
          What specific research would most firm up your low-confidence 
          fields? (The framework will suggest these as separate skill 
          invocations you can run later.)
        suggestions_based_on_low_confidence:
          - hangouts_online: "pulse mine-reviews on the named competitor products"
          - jobs_to_be_done: "run 3-5 JTBD interviews with recent customers"
          - trust_voices: "observe posts in the named communities for 2 weeks"
          - wish_list_items: "pulse scan-ads on competitor categories"
        writes_to: customer.primary_profile._research_queue
```

## How `pulse profile-customer` walks the operator through

The skill's procedure, in brief:

1. **Preflight**. Read `workspace.yaml`. If a customer profile already exists, offer three modes:
   - *Refresh*: walk all questions, showing current answers, operator edits only what changed
   - *Deepen*: walk only questions where current answer is shallow
   - *Start over*: blank slate

2. **Tier gating**. Offer the operator a choice of completing all four tiers or stopping after a specific tier. Each tier is a checkpoint.

3. **For each question in each tier**:
   - Display the prompt
   - Show the example (but clearly marked — operators sometimes anchor too hard on examples)
   - Collect the answer
   - Ask: "How confident are you? [high / medium / low / guessing]"
   - If low or guessing: note it for the research queue
   - Save incrementally (every answer is persisted — if the skill crashes, progress isn't lost)

4. **Tier boundary checkpoints**. After each tier, summarize what's been captured and offer to continue or stop.

5. **Meta section**. Walk the low-confidence fields, build the research queue.

6. **Write outputs**:
   - `workspace.yaml` is updated with the new `customer:` block
   - A new atom is written for each research-queue item, typed `authored`, tagged `research_to_do`, linked to the relevant field

7. **Summary**:
   ```
   Customer profile captured for workspace anti-enterprise.
   
   Completeness:
     Tier 1 (identity):               ████████ 100%
     Tier 2 (psychology):             ██████▎▎  80% (8/10 high-confidence)
     Tier 3 (jobs and pain):          ████████ 100%
     Tier 4 (trust network):          █████▎▎▎  65% (some research needed)
   
   Research queue (4 items):
     - mine reviews on direct_competitors_known (→ pulse mine-reviews)
     - run JTBD interviews with 3 recent customers (manual)
     - observe r/ExperiencedDevs, r/EntrepreneurRideAlong for 2 weeks
     - scan ad libraries for direct competitors (→ pulse scan-ads)
   
   Run `pulse workspace-status` to see full state.
   Next recommended: `pulse articulate-offer` to build the offer block.
   ```

## How the profile flows into downstream skills

A sample of how richly the profile gets consumed:

### `pulse map-ecosystem`

Reads:
- `customer.primary_profile.direct_competitors_known` → seeds the competitor list
- `customer.primary_profile.buys_before/during/after` → seeds complementary candidates
- `customer.primary_profile.trust_voices` → seeds trust-network candidates
- `customer.primary_profile.adjacent_winners_inspiration` → seeds adjacent-winner candidates
- `customer.primary_profile.hangouts_online/offline` → seeds community-forum candidates

### `pulse find-gaps`

Reads:
- `customer.primary_profile.wish_list_items` → primary gap signals
- `customer.primary_profile.dissatisfactions_with_alternatives` → competitive gap signals
- `customer.primary_profile.pain_points` → latent need signals

### `pulse write-brief`

Reads:
- `customer.primary_profile.language` → voice calibration
- `customer.primary_profile.worldview` → framing alignment
- `customer.primary_profile.buying_triggers` → call-to-action structure
- `customer.primary_profile.trust_voices` → citations and social proof choice
- `customer.primary_profile.pain_points` → hook angles

### `pulse draft-survey`

Reads:
- `customer.primary_profile.jobs_to_be_done` → job-framing questions
- `customer.primary_profile.pain_points` → validation questions
- `customer.primary_profile.current_solutions` → switching questions
- `customer.primary_profile.language` → question wording

### `pulse propose-hypothesis`

Reads the entire customer profile as background context, plus specifically:
- `customer.primary_profile.buying_triggers` → hypothesis framing
- `customer.primary_profile.pain_points` → hypothesis substance
- `customer.primary_profile.wish_list_items` → opportunity hypotheses

Every skill gets better when the profile gets better. Investing the 30 minutes compounds across every subsequent skill invocation for the life of the workspace.

## Profile evolution over time

The profile isn't static. It should get sharper as the operator learns more. The framework supports evolution:

- **Weekly and monthly runs** surface language patterns from atoms. Over time, if atoms consistently show customers using language that doesn't match `customer.primary_profile.language`, `pulse audit-drift` flags it.

- **`pulse profile-customer --refresh`** walks all fields again, showing current values and asking whether they're still accurate. A quarterly habit.

- **Field-level updates**: `pulse profile-customer --section jobs_to_be_done` only walks that section, useful when a specific facet needs firming up.

- **Research queue items** naturally update fields as they complete. When `pulse mine-reviews` finds that customers complain about X more than Y, the pain_points field can be updated with higher confidence.

The goal is a profile that's richer two quarters from now than it is today.

## The profile as client deliverable

A secondary benefit worth flagging: the customer profile that comes out of `pulse profile-customer` is itself a deliverable. An advisor running this with a client produces a structured, specific, framework-informed customer profile as an artifact of the engagement. That's a valuable thing on its own — many clients don't have one, or have a vague one.

Exportable to a client-friendly document:

```
pulse export-profile --workspace turner-marketing --format markdown
```

Writes a clean, narrative markdown file from the structured YAML. Good for client deliverables, team onboarding, or external reference.

## The discipline this questionnaire enforces

The questionnaire is designed to enforce specific habits of thinking:

**Specificity over generality.** "SMBs" is not an answer. "AI-curious SMB founders, 10-50 employees, $1M-$20M revenue, running professional services or early-stage software" is an answer.

**Language fidelity.** The "what words do they use and avoid" question forces the operator to listen to their customers, not to themselves. This single field improves downstream copy generation more than any prompt engineering.

**Honest confidence.** The confidence-flagging system makes it impossible to hide guesses inside plausible-sounding answers. If you're guessing, say so, and put research on the queue.

**Cross-framework integration.** By organizing tiers so DemandCurve's JTBD, Imperium's niche research, Abraham's prospect profiling, and Hormozi's ecosystem question all get asked in one sitting, the operator does the synthesis naturally rather than running four separate exercises.

This is why the questionnaire is the highest-leverage artifact. It's not just data capture — it's a forcing function for a specific quality of thinking that downstream skills then amplify.
