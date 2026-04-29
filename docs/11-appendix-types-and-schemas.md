# 11 — Appendix: Types and Schemas

Canonical reference for every type, schema, and DDL the framework defines. Build agents implement against this; operators and contributors read it to understand the data model precisely.

This document is reference material — read sections as you need them, not front to back.

## Section 1 — Python type definitions

Pydantic v2 models for every first-class entity in the framework. These are the source of truth for Python code.

### Workspace

```python
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class CompanyStage(str, Enum):
    PRE_REVENUE = "pre_revenue"
    EARLY_REVENUE = "early_revenue"
    EARLY_GROWTH = "early_growth"
    SCALE = "scale"
    MID_MARKET = "mid_market"
    ENTERPRISE = "enterprise"


class DecisionStyle(str, Enum):
    FAST_INFORMED_SKEPTICAL = "fast_informed_skeptical"
    SLOW_CONSENSUS = "slow_consensus"
    EXPERIMENTAL_ITERATIVE = "experimental_iterative"
    RECOMMENDATION_DRIVEN = "recommendation_driven"
    ANALYSIS_PARALYSIS = "analysis_paralysis"


class JobToBeDone(BaseModel):
    job: str
    when_trigger: str | None = None
    so_that: str | None = None
    urgency: Literal["critical", "high", "medium", "low", "background"]
    frequency: Literal["continuous", "weekly", "monthly", "quarterly", "annually", "one_time"]


class TrustVoice(BaseModel):
    name: str
    why: str
    platform: str | None = None


class CustomerDemographics(BaseModel):
    role_titles: list[str]
    company_stage: CompanyStage
    revenue_range_usd: str
    employee_range: str
    industries_served: list[str]
    geography_primary: str
    geography_secondary: list[str] = Field(default_factory=list)
    tech_stack_signals: str | None = None


class CustomerPsychographics(BaseModel):
    worldview: str
    anxieties: list[str]
    aspirations: list[str]
    decision_style: DecisionStyle
    buying_triggers: list[str] = Field(default_factory=list)
    status_signals: list[str] = Field(default_factory=list)
    self_narrative: str | None = None
    language: str | None = None


class CustomerProfile(BaseModel):
    descriptor: str
    demographics: CustomerDemographics
    psychographics: CustomerPsychographics
    jobs_to_be_done: list[JobToBeDone]
    pain_points: list[str]
    current_solutions: list[str]
    switching_friction: str | None = None
    wins_they_want: list[str] = Field(default_factory=list)
    wish_list_items: list[str] = Field(default_factory=list)
    dissatisfactions_with_alternatives: str | None = None
    trust_voices: list[TrustVoice]
    publications_read: list[str] = Field(default_factory=list)
    podcasts_listened: list[str] = Field(default_factory=list)
    events_attended: list[str] = Field(default_factory=list)
    hangouts_online: list[str] = Field(default_factory=list)
    hangouts_offline: list[str] = Field(default_factory=list)
    buys_before: list[str] = Field(default_factory=list)
    buys_during: list[str] = Field(default_factory=list)
    buys_after: list[str] = Field(default_factory=list)
    direct_competitors_known: list[str] = Field(default_factory=list)
    adjacent_winners_inspiration: list[str] = Field(default_factory=list)
    
    # Meta fields prefixed with underscore
    _low_confidence_fields: list[str] = Field(default_factory=list)
    _research_queue: list[str] = Field(default_factory=list)


class Customer(BaseModel):
    primary_profile: CustomerProfile


class Identity(BaseModel):
    declared_business: str
    real_business: str | None = None
    real_business_delta: str | None = None
    identity_last_reviewed: datetime | None = None


class Offer(BaseModel):
    core_promise: str
    mechanism: str
    pricing_model: dict[str, str | None]    # structure, range_usd, notes
    proof_assets: list[str] = Field(default_factory=list)


class Goals(BaseModel):
    primary: str
    secondary: list[str] = Field(default_factory=list)
    active_bets: list[str] = Field(default_factory=list)
    constraints: dict[str, str] = Field(default_factory=dict)


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class PositionLayer(BaseModel):
    season: Season
    lifecycle_stage: int = Field(ge=1, le=7)


class PositionMatrix(BaseModel):
    person: PositionLayer
    business: PositionLayer
    industry: PositionLayer
    economy: PositionLayer


class Intention(str, Enum):
    PUSH_INTO_GROWTH = "push_into_growth"
    HARDEN_FOUNDATIONS = "harden_foundations"
    PREPARE_FOR_TRANSITION = "prepare_for_transition"
    EXPERIMENT_AGGRESSIVELY = "experiment_aggressively"
    HARVEST = "harvest"
    PIVOT = "pivot"
    HOLD = "hold"


class Position(BaseModel):
    declared: PositionMatrix
    detected: PositionMatrix | None = None
    intention: Intention
    position_last_reviewed: datetime | None = None


class Cadence(BaseModel):
    weekly_day: str | None = None
    weekly_time: str | None = None
    monthly_day: int | None = None
    quarterly_months: list[int] = Field(default_factory=list)


class Notifications(BaseModel):
    run_summaries_to: str = "stdout"
    quarterly_review_reminders: bool = True


class WorkspaceConfig(BaseModel):
    active_playbooks: list[str] = Field(default_factory=list)
    signal_scoring_weights: dict[str, float] = Field(default_factory=dict)
    cadence: Cadence | None = None
    notifications: Notifications = Field(default_factory=Notifications)


class ExternalSource(BaseModel):
    name: str
    kind: Literal["notebooklm", "external_app", "book_collection", "podcast", "course", "other"]
    url: str | None = None
    account: str | None = None
    covers_frameworks: list[str] = Field(default_factory=list)


class Workspace(BaseModel):
    # Identity
    id: str
    name: str
    industry: str
    created: datetime
    created_by: str
    last_touched: datetime

    # Scope
    scope_statement: str | None = None

    # Sections (all optional at workspace creation; populated by kickoff skills)
    identity: Identity | None = None
    customer: Customer | None = None
    offer: Offer | None = None
    goals: Goals | None = None
    position: Position | None = None

    # Operational
    config: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    external_sources: list[ExternalSource] = Field(default_factory=list)

    # Metadata
    schema_version: int = 1
```

### Atom

```python
class AtomSourceKind(str, Enum):
    EXTRACTION = "extraction"
    AUTHORED = "authored"
    FIELD_NOTE = "field_note"
    CORPUS_QUERY = "corpus_query"
    DB_QUERY = "db_query"           # reserved for v2; not produced in v1


class AtomType(str, Enum):
    CLAIM = "claim"
    STAT = "stat"
    QUOTE = "quote"
    ENTITY = "entity"
    THEME = "theme"


class WorkspaceEntityRefs(BaseModel):
    customer_id: str | None = None
    deal_id: str | None = None
    project_id: str | None = None
    
    class Config:
        extra = "allow"   # forward-compat for v2 entity types


class Atom(BaseModel):
    # Identity
    id: str
    workspace_id: str

    # Source provenance
    source_kind: AtomSourceKind
    source_adapter: str
    source_ref: str | None = None
    source_url: str | None = None
    source_label: str | None = None

    # Content
    type: AtomType
    content: str
    entities: list[str] = Field(default_factory=list)

    # Links
    direction_ids: list[str] = Field(default_factory=list)
    factor_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)

    # Timing
    observed_at: datetime | None = None
    extracted_at: datetime

    # Reserved for v2
    workspace_entity_refs: WorkspaceEntityRefs | None = None
```

### Direction

```python
class DirectionState(str, Enum):
    NASCENT = "nascent"
    EMERGING = "emerging"
    HARDENING = "hardening"
    ESTABLISHED = "established"
    PEAKING = "peaking"
    DECLINING = "declining"
    STALE = "stale"


class Direction(BaseModel):
    id: str
    code: str                           # e.g., "d-041"
    title: str
    state: DirectionState
    momentum: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    atom_count: int = 0
    age_days: int = 0
    origin_date: datetime
    last_updated: datetime
    related_directions: list[str] = Field(default_factory=list)
    related_factors: list[str] = Field(default_factory=list)
    description: str | None = None
```

### Hypothesis

```python
class HypothesisState(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    HARDENING = "hardening"
    CONFIRMED = "confirmed"
    CONTESTED = "contested"
    RETIRED = "retired"


class Hypothesis(BaseModel):
    id: str
    code: str                           # e.g., "h-0412"
    title: str
    statement: str
    state: HypothesisState
    confidence: float = Field(ge=0.0, le=1.0)
    age_days: int = 0
    auto_generated: bool = False
    created_at: datetime
    last_updated: datetime
    last_state_change: datetime
    direction_ids: list[str] = Field(default_factory=list)
    supporting_atom_ids: list[str] = Field(default_factory=list)
    contradicting_atom_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
```

### Factor

```python
class FactorKind(str, Enum):
    REGULATORY = "regulatory"
    TECHNOLOGICAL = "technological"
    ECONOMIC = "economic"
    CULTURAL = "cultural"
    DEMOGRAPHIC = "demographic"
    COMPETITIVE = "competitive"
    SUPPLY_CHAIN = "supply_chain"
    CHANNEL = "channel"
    OTHER = "other"


class FactorStatus(str, Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"


class Factor(BaseModel):
    id: str
    kind: FactorKind
    name: str
    description: str | None = None
    weight: int = Field(ge=0, le=10)
    status: FactorStatus
    last_updated: datetime
    related_directions: list[str] = Field(default_factory=list)
```

### Source

```python
class SourceKind(str, Enum):
    WEB_PAGE = "web_page"
    RSS = "rss"
    PODCAST = "podcast"
    YOUTUBE = "youtube"
    REVIEW_AGGREGATOR = "review_aggregator"
    AD_LIBRARY = "ad_library"
    COMMUNITY_FORUM = "community_forum"
    SOCIAL_PLATFORM = "social_platform"
    OTHER = "other"


class StrategicRole(str, Enum):
    DIRECT_COMPETITOR = "direct_competitor"
    SUBSTITUTE = "substitute"
    COMPLEMENTARY = "complementary"
    PARTNER_CANDIDATE = "partner_candidate"
    TRUST_NETWORK = "trust_network"
    COMMUNITY_FORUM = "community_forum"
    REVIEW_AGGREGATOR = "review_aggregator"
    AD_LIBRARY = "ad_library"
    ADJACENT_WINNER = "adjacent_winner"
    ACQUISITION_TARGET = "acquisition_target"


class SourceHealth(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    BROKEN = "broken"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Source(BaseModel):
    id: str
    url: str
    label: str
    kind: SourceKind
    strategic_role: StrategicRole
    health: SourceHealth = SourceHealth.HEALTHY
    last_run: datetime | None = None
    atom_count_last_run: int = 0
    status: SourceStatus = SourceStatus.ACTIVE
    notes: str | None = None
```

### Pipeline

```python
class PipelineStep(BaseModel):
    name: str
    type: Literal["fetch", "extract", "transform", "score", "write"]
    config: dict[str, str | int | float | bool] = Field(default_factory=dict)


class Pipeline(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: list[PipelineStep]
    triggers: list[str] = Field(default_factory=list)   # e.g., ["weekly", "manual"]
    sources: list[str] = Field(default_factory=list)     # source IDs this pipeline operates on
    enabled: bool = True
```

### Run

```python
class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class Run(BaseModel):
    id: str
    skill_name: str | None = None
    playbook_name: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    status: RunStatus
    workspace_id: str
    duration_ms: int | None = None
    error_message: str | None = None
    knowledge_versions: dict[str, str] = Field(default_factory=dict)
    atoms_produced: int = 0
    output_files: list[str] = Field(default_factory=list)
```

### Skill metadata

```python
class SkillCadence(str, Enum):
    AD_HOC = "ad_hoc"
    PERIODIC = "periodic"
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class SkillLayer(str, Enum):
    META = "meta"
    KICKOFF = "kickoff"
    KNOWLEDGE = "knowledge"
    CORPUS = "corpus"
    DISCOVERY = "discovery"
    LISTEN = "listen"
    SYNTHESIS = "synthesis"
    ACTION = "action"
    REFLECT = "reflect"


class CorpusQuery(BaseModel):
    collection: str
    filters: dict[str, str | list[str]] = Field(default_factory=dict)
    optional: bool = False


class SkillRefinement(BaseModel):
    date: datetime
    note: str
    action: Literal["none", "taxonomy_updated", "prompt_updated", "procedure_updated"] = "none"
    version_bumped: str | None = None


class SkillFrontmatter(BaseModel):
    name: str
    version: str
    description: str
    layer: SkillLayer
    cadence: SkillCadence
    operator_time: str | None = None
    aliases: list[str] = Field(default_factory=list)
    triggers: dict[str, list[str]] = Field(default_factory=dict)
    knowledge: list[str] = Field(default_factory=list)
    corpus_queries: list[CorpusQuery] = Field(default_factory=list)
    uses_prompts: list[str] = Field(default_factory=list)
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)
    inputs: dict[str, dict] = Field(default_factory=dict)
    outputs: dict[str, dict] = Field(default_factory=dict)
    runtime: dict[str, str | int | bool] = Field(default_factory=dict)
    llm: dict[str, str | int | float] = Field(default_factory=dict)
    logs: dict[str, bool] = Field(default_factory=dict)
    refinements: list[SkillRefinement] = Field(default_factory=list)
```

### Playbook metadata

```python
class PlaybookStep(BaseModel):
    id: str | None = None
    skill: str | None = None             # name of skill to invoke (mutually exclusive with include/checkpoint/switch)
    include: str | None = None           # name of playbook to include
    checkpoint: dict | None = None
    switch: str | None = None
    cases: list[dict] | None = None
    when: str | None = None              # Jinja2 condition
    foreach: dict | None = None
    with_: dict = Field(default_factory=dict, alias="with")
    on_failure: Literal["halt", "log_and_continue", "retry", "checkpoint"] = "log_and_continue"
    timeout_s: int | None = None
    idempotency: dict | None = None
    output: str | None = None


class PlaybookRequires(BaseModel):
    workspace_exists: bool = True
    position_set: bool = False
    sources_min: int | None = None
    mode: Literal["any", "interactive", "headless"] = "any"


class Playbook(BaseModel):
    name: str
    version: str
    description: str
    layer: Literal["operational", "kickoff"] = "operational"
    cadence: SkillCadence
    operator_time: str | None = None
    aliases: list[str] = Field(default_factory=list)
    requires: PlaybookRequires = Field(default_factory=PlaybookRequires)
    defaults: dict = Field(default_factory=dict)
    steps: list[PlaybookStep]
    on_complete: dict = Field(default_factory=dict)
    on_failure: dict = Field(default_factory=dict)
```

## Section 2 — YAML schemas

JSON Schema (draft-07) definitions for the YAML files the framework consumes. These are referenced by skills via `schema:` declarations and validated at load time.

### `workspace.yaml` schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
$id: "pulse://schemas/workspace.yaml"
title: Workspace
type: object
required:
  - id
  - name
  - industry
  - created
  - created_by
  - last_touched
  - schema_version
properties:
  id:
    type: string
    pattern: "^[a-z][a-z0-9-]*$"
  name:
    type: string
  industry:
    type: string
  created:
    type: string
    format: date-time
  created_by:
    type: string
  last_touched:
    type: string
    format: date-time
  scope_statement:
    type: string
  identity:
    $ref: "#/definitions/Identity"
  customer:
    $ref: "#/definitions/Customer"
  offer:
    $ref: "#/definitions/Offer"
  goals:
    $ref: "#/definitions/Goals"
  position:
    $ref: "#/definitions/Position"
  config:
    $ref: "#/definitions/WorkspaceConfig"
  external_sources:
    type: array
    items:
      $ref: "#/definitions/ExternalSource"
  schema_version:
    type: integer
    const: 1

definitions:
  Identity:
    type: object
    required: [declared_business]
    properties:
      declared_business: { type: string }
      real_business: { type: string }
      real_business_delta: { type: string }
      identity_last_reviewed: { type: string, format: date-time }

  Customer:
    type: object
    required: [primary_profile]
    properties:
      primary_profile:
        $ref: "#/definitions/CustomerProfile"

  CustomerProfile:
    type: object
    required: [descriptor, demographics, psychographics, jobs_to_be_done, pain_points]
    properties:
      descriptor: { type: string }
      demographics: { $ref: "#/definitions/CustomerDemographics" }
      psychographics: { $ref: "#/definitions/CustomerPsychographics" }
      jobs_to_be_done:
        type: array
        items: { $ref: "#/definitions/JobToBeDone" }
      pain_points:
        type: array
        items: { type: string }
      current_solutions:
        type: array
        items: { type: string }
      switching_friction: { type: string }
      wins_they_want:
        type: array
        items: { type: string }
      wish_list_items:
        type: array
        items: { type: string }
      dissatisfactions_with_alternatives: { type: string }
      trust_voices:
        type: array
        items: { $ref: "#/definitions/TrustVoice" }
      publications_read: { type: array, items: { type: string } }
      podcasts_listened: { type: array, items: { type: string } }
      events_attended: { type: array, items: { type: string } }
      hangouts_online: { type: array, items: { type: string } }
      hangouts_offline: { type: array, items: { type: string } }
      buys_before: { type: array, items: { type: string } }
      buys_during: { type: array, items: { type: string } }
      buys_after: { type: array, items: { type: string } }
      direct_competitors_known: { type: array, items: { type: string } }
      adjacent_winners_inspiration: { type: array, items: { type: string } }

  CustomerDemographics:
    type: object
    required: [role_titles, company_stage, revenue_range_usd, employee_range, industries_served, geography_primary]
    properties:
      role_titles: { type: array, items: { type: string } }
      company_stage:
        type: string
        enum: [pre_revenue, early_revenue, early_growth, scale, mid_market, enterprise]
      revenue_range_usd: { type: string }
      employee_range: { type: string }
      industries_served: { type: array, items: { type: string } }
      geography_primary: { type: string }
      geography_secondary: { type: array, items: { type: string } }
      tech_stack_signals: { type: string }

  CustomerPsychographics:
    type: object
    required: [worldview, anxieties, aspirations, decision_style]
    properties:
      worldview: { type: string }
      anxieties: { type: array, items: { type: string } }
      aspirations: { type: array, items: { type: string } }
      decision_style:
        type: string
        enum:
          - fast_informed_skeptical
          - slow_consensus
          - experimental_iterative
          - recommendation_driven
          - analysis_paralysis
      buying_triggers: { type: array, items: { type: string } }
      status_signals: { type: array, items: { type: string } }
      self_narrative: { type: string }
      language: { type: string }

  JobToBeDone:
    type: object
    required: [job, urgency, frequency]
    properties:
      job: { type: string }
      when_trigger: { type: string }
      so_that: { type: string }
      urgency:
        type: string
        enum: [critical, high, medium, low, background]
      frequency:
        type: string
        enum: [continuous, weekly, monthly, quarterly, annually, one_time]

  TrustVoice:
    type: object
    required: [name, why]
    properties:
      name: { type: string }
      why: { type: string }
      platform: { type: string }

  Offer:
    type: object
    required: [core_promise, mechanism, pricing_model]
    properties:
      core_promise: { type: string }
      mechanism: { type: string }
      pricing_model:
        type: object
        properties:
          structure: { type: string }
          range_usd: { type: string }
          notes: { type: string }
      proof_assets: { type: array, items: { type: string } }

  Goals:
    type: object
    required: [primary]
    properties:
      primary: { type: string }
      secondary: { type: array, items: { type: string } }
      active_bets: { type: array, items: { type: string } }
      constraints:
        type: object
        additionalProperties: { type: string }

  Position:
    type: object
    required: [declared, intention]
    properties:
      declared: { $ref: "#/definitions/PositionMatrix" }
      detected: { $ref: "#/definitions/PositionMatrix" }
      intention:
        type: string
        enum:
          - push_into_growth
          - harden_foundations
          - prepare_for_transition
          - experiment_aggressively
          - harvest
          - pivot
          - hold
      position_last_reviewed: { type: string, format: date-time }

  PositionMatrix:
    type: object
    required: [person, business, industry, economy]
    properties:
      person: { $ref: "#/definitions/PositionLayer" }
      business: { $ref: "#/definitions/PositionLayer" }
      industry: { $ref: "#/definitions/PositionLayer" }
      economy: { $ref: "#/definitions/PositionLayer" }

  PositionLayer:
    type: object
    required: [season, lifecycle_stage]
    properties:
      season:
        type: string
        enum: [spring, summer, autumn, winter]
      lifecycle_stage:
        type: integer
        minimum: 1
        maximum: 7

  WorkspaceConfig:
    type: object
    properties:
      active_playbooks: { type: array, items: { type: string } }
      signal_scoring_weights:
        type: object
        additionalProperties: { type: number }
      cadence:
        type: object
        properties:
          weekly_day: { type: string }
          weekly_time: { type: string }
          monthly_day: { type: integer }
          quarterly_months:
            type: array
            items: { type: integer, minimum: 1, maximum: 12 }
      notifications:
        type: object
        properties:
          run_summaries_to: { type: string }
          quarterly_review_reminders: { type: boolean }

  ExternalSource:
    type: object
    required: [name, kind]
    properties:
      name: { type: string }
      kind:
        type: string
        enum: [notebooklm, external_app, book_collection, podcast, course, other]
      url: { type: string, format: uri }
      account: { type: string }
      covers_frameworks: { type: array, items: { type: string } }
```

### Skill frontmatter schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
$id: "pulse://schemas/skill-frontmatter.yaml"
title: SkillFrontmatter
type: object
required: [name, version, description, layer, cadence]
properties:
  name:
    type: string
    pattern: "^pulse [a-z][a-z0-9-]*$"
  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
  description:
    type: string
  layer:
    type: string
    enum: [meta, kickoff, knowledge, corpus, discovery, listen, synthesis, action, reflect]
  cadence:
    type: string
    enum: [ad_hoc, periodic, one_time, weekly, monthly, quarterly]
  operator_time:
    type: string
  aliases:
    type: array
    items: { type: string }
  triggers:
    type: object
    properties:
      router_nodes: { type: array, items: { type: string } }
      required_by_playbooks: { type: array, items: { type: string } }
  knowledge:
    type: array
    items: { type: string }
  corpus_queries:
    type: array
    items:
      type: object
      required: [collection]
      properties:
        collection: { type: string }
        filters: { type: object }
        optional: { type: boolean, default: false }
  uses_prompts:
    type: array
    items: { type: string }
  reads:
    type: array
    items: { type: string }
  writes:
    type: array
    items: { type: string }
  inputs:
    type: object
    additionalProperties:
      type: object
      required: [type]
      properties:
        type:
          type: string
          enum: [string, integer, number, boolean, enum, array, object]
        required: { type: boolean, default: false }
        default: {}
        description: { type: string }
        values:
          type: array
          description: "For enum type"
  outputs:
    type: object
    additionalProperties:
      type: object
      properties:
        path: { type: string }
        schema: { type: string }
        description: { type: string }
  runtime:
    type: object
    properties:
      confirms_before_commit: { type: boolean }
      idempotency_key: { type: string }
      concurrency:
        type: string
        enum: [serial, parallel]
      max_duration_s: { type: integer, minimum: 1 }
      type:
        type: string
        enum: [llm_procedure, tree_walker, deterministic]
        default: llm_procedure
  llm:
    type: object
    properties:
      provider: { type: string }
      model: { type: string }
      temperature: { type: number, minimum: 0, maximum: 2 }
      max_tokens: { type: integer, minimum: 1 }
  logs:
    type: object
    properties:
      include_prompts: { type: boolean }
      include_responses: { type: boolean }
  refinements:
    type: array
    items:
      type: object
      required: [date, note]
      properties:
        date: { type: string, format: date }
        note: { type: string }
        action:
          type: string
          enum: [none, taxonomy_updated, prompt_updated, procedure_updated]
        version_bumped: { type: string }
```

### Playbook schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
$id: "pulse://schemas/playbook.yaml"
title: Playbook
type: object
required: [name, version, description, cadence, steps]
properties:
  name:
    type: string
    pattern: "^pulse [a-z][a-z0-9-]*$"
  version:
    type: string
  description:
    type: string
  layer:
    type: string
    enum: [operational, kickoff]
    default: operational
  cadence:
    type: string
    enum: [ad_hoc, periodic, one_time, weekly, monthly, quarterly]
  operator_time:
    type: string
  aliases:
    type: array
    items: { type: string }
  requires:
    type: object
    properties:
      workspace_exists: { type: boolean, default: true }
      position_set: { type: boolean, default: false }
      sources_min: { type: integer, minimum: 0 }
      mode:
        type: string
        enum: [any, interactive, headless]
        default: any
  defaults:
    type: object
  steps:
    type: array
    minItems: 1
    items:
      $ref: "#/definitions/Step"
  on_complete:
    type: object
    properties:
      print_summary: { type: boolean }
      notify: { type: string }
  on_failure:
    type: object
    properties:
      preserve_partial: { type: boolean }
      summary_to: { type: string }

definitions:
  Step:
    type: object
    properties:
      id: { type: string }
      skill: { type: string }
      include: { type: string }
      checkpoint:
        type: object
        properties:
          prompt: { type: string }
          options:
            type: array
            items:
              type: object
              required: [label, action]
              properties:
                label: { type: string }
                action:
                  type: string
                  enum: [proceed, halt_gracefully, skip_to_end, route_to]
                target: { type: string }
      switch: { type: string }
      cases:
        type: array
        items:
          type: object
          properties:
            value: {}
            default: { type: boolean }
            steps:
              type: array
              items: { $ref: "#/definitions/Step" }
      when: { type: string }
      foreach:
        type: object
        required: [var, source]
        properties:
          var: { type: string }
          source: { type: string }
          parallel: { type: boolean, default: false }
      with:
        type: object
      on_failure:
        type: string
        enum: [halt, log_and_continue, retry, checkpoint]
        default: log_and_continue
      timeout_s: { type: integer, minimum: 1 }
      idempotency:
        type: object
        required: [key]
        properties:
          key: { type: string }
          on_duplicate:
            type: string
            enum: [skip, force_rerun, prompt]
            default: skip
      output: { type: string }
    oneOf:
      - required: [skill]
      - required: [include]
      - required: [checkpoint]
      - required: [switch, cases]
```

### Router tree schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
$id: "pulse://schemas/router-tree.yaml"
title: RouterTree
type: object
required: [version, default_start, nodes]
properties:
  version:
    type: integer
    const: 1
  default_start:
    type: string
  short_circuit:
    type: object
    properties:
      direct_command: { type: boolean }
      short_names: { type: boolean }
      global_escapes:
        type: object
        additionalProperties: { type: string }
  guards:
    type: array
    items: { $ref: "#/definitions/Guard" }
  nodes:
    type: object
    additionalProperties:
      $ref: "#/definitions/Node"

definitions:
  Node:
    type: object
    required: [prompt, options]
    properties:
      prompt: { type: string }
      guard:
        type: array
        items: { $ref: "#/definitions/Guard" }
      options:
        type: array
        minItems: 1
        items: { $ref: "#/definitions/Option" }

  Guard:
    type: object
    required: [condition]
    properties:
      condition: { type: string }
      action:
        type: string
        enum: [route_to, hint, block]
      target: { type: string }
      hint: { type: string }

  Option:
    type: object
    required: [label]
    properties:
      label: { type: string }
      next: { type: string }
      action:
        type: string
        enum: [run_command, back, quit, route_to, start_over]
      command: { type: string }
      with: { type: object }
      target: { type: string }
      confirm: { type: string }
      multi_select: { type: boolean }
      store_as: { type: string }
```

### Corpus schema

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
$id: "pulse://schemas/corpus-schema.yaml"
title: CorpusSchema
type: object
required: [version, embedding, chunking, collections]
properties:
  version:
    type: integer
    const: 1
  embedding:
    type: object
    required: [provider, model]
    properties:
      provider:
        type: string
        enum: [voyage, openai, anthropic, local_bge]
      model: { type: string }
      dimensions: { type: integer, minimum: 64 }
  chunking:
    type: object
    properties:
      strategy:
        type: string
        enum: [paragraph_aware, sentence_aware, token_count]
        default: paragraph_aware
      target_tokens: { type: integer, minimum: 100, default: 1000 }
      overlap_tokens: { type: integer, minimum: 0, default: 200 }
  retrieval:
    type: object
    properties:
      default_top_k: { type: integer, minimum: 1, default: 20 }
      rerank: { type: boolean, default: false }
      rerank_model: { type: string }
      rerank_top_k: { type: integer, minimum: 1, default: 5 }
  collections:
    type: object
    additionalProperties:
      type: object
      properties:
        metadata_required:
          type: array
          items: { type: string }
        metadata_optional:
          type: array
          items: { type: string }
```

## Section 3 — SQLite DDL

Complete DDL for the workspace index. Reproduced from Doc 02 with full constraints and indexes.

```sql
-- ─────────────────────────────────────────────────────────────
-- Atoms
-- ─────────────────────────────────────────────────────────────

CREATE TABLE atoms (
  id TEXT PRIMARY KEY,
  source_kind TEXT NOT NULL CHECK(source_kind IN
    ('extraction', 'authored', 'field_note', 'corpus_query', 'db_query')),
  source_adapter TEXT NOT NULL,
  source_ref TEXT,
  source_url TEXT,
  source_label TEXT,
  type TEXT NOT NULL CHECK(type IN ('claim', 'stat', 'quote', 'entity', 'theme')),
  content TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  observed_at TEXT,
  entities TEXT,
  direction_ids TEXT,
  factor_ids TEXT,
  hypothesis_ids TEXT,
  workspace_entity_refs TEXT,
  source_file TEXT NOT NULL
);

CREATE INDEX idx_atoms_extracted_at ON atoms(extracted_at);
CREATE INDEX idx_atoms_source_kind ON atoms(source_kind);
CREATE INDEX idx_atoms_type ON atoms(type);
CREATE INDEX idx_atoms_source_adapter ON atoms(source_adapter);

-- ─────────────────────────────────────────────────────────────
-- Directions
-- ─────────────────────────────────────────────────────────────

CREATE TABLE directions (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN
    ('nascent', 'emerging', 'hardening', 'established', 'peaking', 'declining', 'stale')),
  momentum REAL CHECK(momentum >= -1.0 AND momentum <= 1.0),
  confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  atom_count INTEGER DEFAULT 0,
  age_days INTEGER DEFAULT 0,
  origin_date TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  source_file TEXT NOT NULL
);

CREATE INDEX idx_directions_state ON directions(state);
CREATE INDEX idx_directions_momentum ON directions(momentum);

-- ─────────────────────────────────────────────────────────────
-- Hypotheses
-- ─────────────────────────────────────────────────────────────

CREATE TABLE hypotheses (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN
    ('proposed', 'active', 'hardening', 'confirmed', 'contested', 'retired')),
  confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  age_days INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  last_state_change TEXT NOT NULL,
  auto_generated INTEGER NOT NULL DEFAULT 0 CHECK(auto_generated IN (0, 1)),
  source_file TEXT NOT NULL
);

CREATE INDEX idx_hypotheses_state ON hypotheses(state);
CREATE INDEX idx_hypotheses_last_state_change ON hypotheses(last_state_change);

-- ─────────────────────────────────────────────────────────────
-- Factors
-- ─────────────────────────────────────────────────────────────

CREATE TABLE factors (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN
    ('regulatory', 'technological', 'economic', 'cultural', 'demographic',
     'competitive', 'supply_chain', 'channel', 'other')),
  name TEXT NOT NULL,
  weight INTEGER CHECK(weight >= 0 AND weight <= 10),
  status TEXT NOT NULL CHECK(status IN ('active', 'dormant', 'archived')),
  last_updated TEXT NOT NULL,
  source_file TEXT NOT NULL
);

CREATE INDEX idx_factors_kind ON factors(kind);
CREATE INDEX idx_factors_status ON factors(status);

-- ─────────────────────────────────────────────────────────────
-- Sources
-- ─────────────────────────────────────────────────────────────

CREATE TABLE sources (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  label TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN
    ('web_page', 'rss', 'podcast', 'youtube', 'review_aggregator',
     'ad_library', 'community_forum', 'social_platform', 'other')),
  strategic_role TEXT NOT NULL CHECK(strategic_role IN
    ('direct_competitor', 'substitute', 'complementary', 'partner_candidate',
     'trust_network', 'community_forum', 'review_aggregator', 'ad_library',
     'adjacent_winner', 'acquisition_target')),
  health TEXT NOT NULL DEFAULT 'healthy' CHECK(health IN
    ('healthy', 'warning', 'degraded', 'broken')),
  last_run TEXT,
  atom_count_last_run INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN
    ('active', 'paused', 'archived'))
);

CREATE INDEX idx_sources_strategic_role ON sources(strategic_role);
CREATE INDEX idx_sources_health ON sources(health);
CREATE INDEX idx_sources_status ON sources(status);

-- ─────────────────────────────────────────────────────────────
-- Runs
-- ─────────────────────────────────────────────────────────────

CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  skill_name TEXT,
  playbook_name TEXT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL CHECK(status IN
    ('running', 'succeeded', 'failed', 'cancelled', 'partial_success')),
  workspace_id TEXT NOT NULL,
  duration_ms INTEGER,
  error_message TEXT,
  knowledge_versions TEXT,
  atoms_produced INTEGER DEFAULT 0,
  output_files TEXT,
  CHECK (skill_name IS NOT NULL OR playbook_name IS NOT NULL)
);

CREATE INDEX idx_runs_started_at ON runs(started_at);
CREATE INDEX idx_runs_skill_name ON runs(skill_name);
CREATE INDEX idx_runs_playbook_name ON runs(playbook_name);
CREATE INDEX idx_runs_status ON runs(status);

-- ─────────────────────────────────────────────────────────────
-- Schema metadata
-- ─────────────────────────────────────────────────────────────

CREATE TABLE schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT INTO schema_meta (key, value) VALUES ('version', '1');
INSERT INTO schema_meta (key, value) VALUES ('last_rebuilt', '');
```

## Section 4 — Validation rules

Cross-cutting rules that the runtime enforces beyond what schemas can express.

### Workspace ID format

- Lowercase alphanumeric and hyphens only
- Must start with a letter
- Length 3-64
- Reserved: `default`, `template`, `archive`, `meta`

Regex: `^[a-z][a-z0-9-]{2,63}$` and not in reserved list.

### Skill name format

- Must start with `pulse `
- Verb portion: lowercase alphanumeric and hyphens
- Verb portion length 2-32
- Reserved verbs (cannot be used by user-defined skills): `init`, `help`, `version`, `intel-query`, `emit`, `portfolio-scan`

Regex: `^pulse [a-z][a-z0-9-]{1,31}$`

### Playbook name format

Same as skill name format. Skills and playbooks share the namespace.

### Atom ID format

- UUID v4 (36 chars including hyphens)
- Generated by the runtime, never user-supplied

### Direction code format

- `d-NNN` where N is digit
- Sequential within a workspace
- Maximum 999 directions per workspace (raise warning at 800)

### Hypothesis code format

- `h-NNNN` where N is digit  
- Sequential within a workspace
- Maximum 9999 hypotheses per workspace

### File paths

- All paths in skill frontmatter `reads:` and `writes:` are relative to the workspace root
- Absolute paths are forbidden (security: prevents skills from reading/writing outside workspace)
- The runtime resolves relative paths against the active workspace

### Knowledge file paths

- Relative to `~/.pulse/knowledge/`
- Forward slashes only (cross-platform consistency)
- Must exist at skill load time (validation fails if a declared knowledge file is missing)

### Corpus collection names

- Must be one of: `frameworks`, `industry`, `case-studies`, `interviews`, `workspace-specific`, `misc`
- Custom collections require `corpus/schema.yaml` to declare them first

### Run log file format

- One JSONL file per run at `runs/<ISO-timestamp>.jsonl`
- ISO timestamp: `YYYY-MM-DDTHH-MM-SS` (filesystem-safe; no colons)
- Each line is a JSON object with `event` field

### Atom JSONL file format

- One file per workspace per month: `atoms/YYYY-MM/atoms.jsonl`
- Append-only writes
- Each line is one Atom serialized as JSON
- Maximum file size before warning: 50MB (~10K atoms; partition further if approaching)

## Section 5 — Configuration files

### `~/.pulse/config.yaml` (global)

```yaml
schema_version: 1

# LLM (required)
llm:
  provider: anthropic
  model: claude-opus-4-7
  api_key_env: ANTHROPIC_API_KEY     # name of env var holding the key
  api_key: null                       # alternatively, key inline (less secure)

# Active workspace
active_workspace: anti-enterprise     # set by `pulse workspace-switch`

# Corpus
corpus:
  enabled: true
  embedding:
    provider: voyage                  # voyage | openai | anthropic | local_bge
    model: voyage-3
    api_key_env: VOYAGE_API_KEY
  storage_path: ~/.pulse/corpus
  
# Defaults
defaults:
  workspace_directory: ~/.pulse/workspaces
  log_level: info                     # debug | info | warn | error
  output_format: text                 # text | json | yaml
  
# Telemetry (off by default; reserved for future opt-in)
telemetry:
  enabled: false

# Permissions (reserved for v3)
permissions:
  emitters: {}
```

### Workspace `.gitignore` template

Created at workspace initialization:

```gitignore
# Credentials — never commit
.credentials/
*.key
*.pem

# Local index — regenerable, no need to commit
.index.sqlite
.index.sqlite.bak
.index.sqlite.bak.*

# Run logs — local artifacts
runs/

# Router log — local navigation history
.router-log.jsonl

# OS noise
.DS_Store
Thumbs.db

# Editor noise
*.swp
*.swo
.vscode/
.idea/
```

### `~/.pulse/.gitignore` template

For the framework directory itself, if the operator chooses to put `~/.pulse/` under version control:

```gitignore
# Per-workspace ignored items handled by workspace-level .gitignore

# Global credentials
config.yaml          # contains API keys; user can selectively commit a sanitized version

# Corpus index (regenerable)
corpus/index/
corpus/index.bak/

# Corpus ingestion log (workspace-local trace)
# Operators can choose to commit this; default ignored
corpus/ingestion-log.jsonl

# Global router log
runs/router.log.jsonl

# OS / editor noise
.DS_Store
*.swp
.vscode/
```

## Section 6 — Quick reference: file ↔ schema map

| File | Schema |
|---|---|
| `workspaces/<id>/workspace.yaml` | `pulse://schemas/workspace.yaml` |
| `workspaces/<id>/atoms/YYYY-MM/atoms.jsonl` | `pulse://schemas/atom.json` (per line) |
| `workspaces/<id>/directions/d-*.yaml` | `pulse://schemas/direction.yaml` |
| `workspaces/<id>/hypotheses/h-*.yaml` | `pulse://schemas/hypothesis.yaml` |
| `workspaces/<id>/factors/factors.yaml` | `pulse://schemas/factors.yaml` |
| `workspaces/<id>/sources/sources.yaml` | `pulse://schemas/sources.yaml` |
| `workspaces/<id>/runs/*.jsonl` | `pulse://schemas/run-event.json` (per line) |
| `skills/<layer>/<n>/SKILL.md` (frontmatter) | `pulse://schemas/skill-frontmatter.yaml` |
| `skills/<layer>/<n>/schema.input.yaml` | (skill-specific JSON Schema) |
| `skills/<layer>/<n>/schema.output.yaml` | (skill-specific JSON Schema) |
| `playbooks/*.yaml` | `pulse://schemas/playbook.yaml` |
| `router/tree.yaml` | `pulse://schemas/router-tree.yaml` |
| `corpus/schema.yaml` | `pulse://schemas/corpus-schema.yaml` |
| `corpus/ingestion-log.jsonl` | `pulse://schemas/ingestion-event.json` (per line) |
| `config.yaml` | `pulse://schemas/global-config.yaml` |

This map is the contract: every file the framework writes or reads is governed by exactly one schema. Skills validate I/O at the boundaries. Operators editing files manually can validate with `pulse validate <path>`.

## Section 7 — Reserved namespaces

A reference of names reserved by the framework to prevent user collisions:

### Reserved skill verbs

`init`, `help`, `version`, `intel-query` (v2), `emit` (v3), `portfolio-scan` (v4), `upgrade-to-v2` (v2), `validate`, `migrate`

### Reserved workspace IDs

`default`, `template`, `archive`, `meta`, `__test__`

### Reserved corpus collection names

`frameworks`, `industry`, `case-studies`, `interviews`, `workspace-specific`, `misc`, `__test__`

### Reserved playbook names

`onboard`, `reposition`, `weekly`, `monthly`, `quarterly`

(Operators can extend these but cannot redefine them.)

### Reserved atom source kinds

`extraction`, `authored`, `field_note`, `corpus_query`, `db_query` (v2)

### Reserved framework names

`hormozi`, `abraham`, `frasier`, `demandcurve`, `imperium`, `robbins`

## Section 8 — Error codes

Standardized error codes for tooling integration:

| Code | Meaning |
|---|---|
| `E001` | Workspace does not exist |
| `E002` | Workspace not initialized (missing required sections) |
| `E003` | Skill not found |
| `E004` | Playbook not found |
| `E005` | Knowledge file referenced but not present |
| `E006` | Schema validation failed |
| `E007` | Corpus not enabled but required by skill |
| `E008` | LLM API call failed |
| `E009` | Idempotency key satisfied; skill already ran |
| `E010` | Insufficient permissions or credentials |
| `E011` | Concurrent execution conflict |
| `E012` | Output file already exists; would clobber |
| `E013` | Router tree validation failed |
| `E014` | Playbook step failed; halting per on_failure policy |
| `E015` | Index out of sync; run `pulse reindex` |

Errors are surfaced with code, human message, and (when available) a suggested next action.

```
Error E002: Workspace 'anti-enterprise' is not initialized.
The workspace exists but is missing the customer profile section.

Run `pulse profile-customer anti-enterprise` to complete onboarding,
or `pulse onboard anti-enterprise` to run the full kickoff playbook.
```

## End of appendix

This document is the canonical source for every type, schema, and constraint. When implementations and other docs disagree with this appendix, this appendix wins. When the appendix is wrong, fix the appendix first, then propagate.
