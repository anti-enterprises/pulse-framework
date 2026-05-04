"""Pydantic v2 models for all Pulse entities.

Canonical source: doc 11 (11-appendix-types-and-schemas.md).
When this file and other docs disagree, this file wins.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────


class CompanyStage(StrEnum):
    PRE_REVENUE = "pre_revenue"
    EARLY_REVENUE = "early_revenue"
    EARLY_GROWTH = "early_growth"
    SCALE = "scale"
    MID_MARKET = "mid_market"
    ENTERPRISE = "enterprise"


class DecisionStyle(StrEnum):
    FAST_INFORMED_SKEPTICAL = "fast_informed_skeptical"
    SLOW_CONSENSUS = "slow_consensus"
    EXPERIMENTAL_ITERATIVE = "experimental_iterative"
    RECOMMENDATION_DRIVEN = "recommendation_driven"
    ANALYSIS_PARALYSIS = "analysis_paralysis"


class Season(StrEnum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class Intention(StrEnum):
    PUSH_INTO_GROWTH = "push_into_growth"
    HARDEN_FOUNDATIONS = "harden_foundations"
    PREPARE_FOR_TRANSITION = "prepare_for_transition"
    EXPERIMENT_AGGRESSIVELY = "experiment_aggressively"
    HARVEST = "harvest"
    PIVOT = "pivot"
    HOLD = "hold"


class AtomSourceKind(StrEnum):
    EXTRACTION = "extraction"
    AUTHORED = "authored"
    FIELD_NOTE = "field_note"
    CORPUS_QUERY = "corpus_query"
    DB_QUERY = "db_query"  # reserved for v2


class AtomType(StrEnum):
    CLAIM = "claim"
    STAT = "stat"
    QUOTE = "quote"
    ENTITY = "entity"
    THEME = "theme"


class DirectionState(StrEnum):
    ACTIVE = "active"
    NASCENT = "nascent"
    EMERGING = "emerging"
    HARDENING = "hardening"
    ESTABLISHED = "established"
    PEAKING = "peaking"
    DECLINING = "declining"
    STALE = "stale"


class HypothesisState(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    HARDENING = "hardening"
    CONFIRMED = "confirmed"
    CONTESTED = "contested"
    RETIRED = "retired"


class FactorKind(StrEnum):
    REGULATORY = "regulatory"
    TECHNOLOGICAL = "technological"
    ECONOMIC = "economic"
    CULTURAL = "cultural"
    DEMOGRAPHIC = "demographic"
    COMPETITIVE = "competitive"
    SUPPLY_CHAIN = "supply_chain"
    CHANNEL = "channel"
    OTHER = "other"


class FactorStatus(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"


class SourceKind(StrEnum):
    WEB_PAGE = "web_page"
    RSS = "rss"
    PODCAST = "podcast"
    YOUTUBE = "youtube"
    NEWSLETTER = "newsletter"
    REDDIT = "reddit"
    REVIEW_AGGREGATOR = "review_aggregator"
    AD_LIBRARY = "ad_library"
    COMMUNITY_FORUM = "community_forum"
    SOCIAL_PLATFORM = "social_platform"
    OTHER = "other"


class StrategicRole(StrEnum):
    DIRECT_COMPETITOR = "direct_competitor"
    SUBSTITUTE = "substitute"
    COMPLEMENTARY = "complementary"
    INDUSTRY_SIGNAL = "industry_signal"
    PARTNER_CANDIDATE = "partner_candidate"
    TRUST_NETWORK = "trust_network"
    COMMUNITY_FORUM = "community_forum"
    REVIEW_AGGREGATOR = "review_aggregator"
    AD_LIBRARY = "ad_library"
    ADJACENT_WINNER = "adjacent_winner"
    ACQUISITION_TARGET = "acquisition_target"


class SourceHealth(StrEnum):
    HEALTHY = "healthy"
    UNKNOWN = "unknown"
    WARNING = "warning"
    FAILING = "failing"
    DEGRADED = "degraded"
    BROKEN = "broken"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    PAUSED = "paused"
    ARCHIVED = "archived"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class SkillCadence(StrEnum):
    AD_HOC = "ad_hoc"
    PERIODIC = "periodic"
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class SkillLayer(StrEnum):
    META = "meta"
    KICKOFF = "kickoff"
    KNOWLEDGE = "knowledge"
    CORPUS = "corpus"
    DISCOVERY = "discovery"
    LISTEN = "listen"
    SYNTHESIS = "synthesis"
    ACTION = "action"
    REFLECT = "reflect"


# ──────────────────────────────────────────────────────────────
# Customer Profile models
# ──────────────────────────────────────────────────────────────


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
    current_solutions: list[str] = Field(default_factory=list)
    switching_friction: str | None = None
    wins_they_want: list[str] = Field(default_factory=list)
    wish_list_items: list[str] = Field(default_factory=list)
    dissatisfactions_with_alternatives: str | None = None
    trust_voices: list[TrustVoice] = Field(default_factory=list)
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
    low_confidence_fields: list[str] = Field(default_factory=list)
    research_queue: list[str] = Field(default_factory=list)


class Customer(BaseModel):
    primary_profile: CustomerProfile


# ──────────────────────────────────────────────────────────────
# Workspace spine models
# ──────────────────────────────────────────────────────────────


class Identity(BaseModel):
    declared_business: str
    real_business: str | None = None
    real_business_delta: str | None = None
    identity_last_reviewed: datetime | None = None


class Offer(BaseModel):
    core_promise: str
    mechanism: str
    pricing_model: dict[str, str | None]
    proof_assets: list[str] = Field(default_factory=list)


class Goals(BaseModel):
    primary: str
    secondary: list[str] = Field(default_factory=list)
    active_bets: list[str] = Field(default_factory=list)
    constraints: dict[str, str] = Field(default_factory=dict)


class PositionLayer(BaseModel):
    season: Season
    lifecycle_stage: int = Field(ge=1, le=7)


class PositionMatrix(BaseModel):
    person: PositionLayer
    business: PositionLayer
    industry: PositionLayer
    economy: PositionLayer


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
    id: str
    name: str
    industry: str
    created: datetime
    created_by: str
    last_touched: datetime
    scope_statement: str | None = None
    identity: Identity | None = None
    customer: Customer | None = None
    offer: Offer | None = None
    goals: Goals | None = None
    position: Position | None = None
    config: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    external_sources: list[ExternalSource] = Field(default_factory=list)
    schema_version: int = 1


# ──────────────────────────────────────────────────────────────
# Atom
# ──────────────────────────────────────────────────────────────


class WorkspaceEntityRefs(BaseModel):
    model_config = {"extra": "allow"}  # forward-compat for v2
    customer_id: str | None = None
    deal_id: str | None = None
    project_id: str | None = None


class Atom(BaseModel):
    id: str
    workspace_id: str
    source_kind: AtomSourceKind
    source_adapter: str
    source_ref: str | None = None
    source_url: str | None = None
    source_label: str | None = None
    type: AtomType
    content: str
    entities: list[str] = Field(default_factory=list)
    direction_ids: list[str] = Field(default_factory=list)
    factor_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None
    extracted_at: datetime
    workspace_entity_refs: WorkspaceEntityRefs | None = None


# ──────────────────────────────────────────────────────────────
# Direction, Hypothesis, Factor, Source
# ──────────────────────────────────────────────────────────────


class Direction(BaseModel):
    id: str
    code: str
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


class Hypothesis(BaseModel):
    id: str
    code: str
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


class Factor(BaseModel):
    id: str
    kind: FactorKind
    name: str
    description: str | None = None
    weight: int = Field(ge=0, le=10)
    status: FactorStatus
    last_updated: datetime
    related_directions: list[str] = Field(default_factory=list)


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


# ──────────────────────────────────────────────────────────────
# Refinement Criteria
# ──────────────────────────────────────────────────────────────


class RefinementCriterion(BaseModel):
    id: str
    name: str
    description: str
    category: Literal["performance", "quality", "coverage", "freshness", "custom"]
    target_skills: list[str] = Field(default_factory=list)
    rule: str
    severity: Literal["info", "warning", "critical"] = "warning"
    enabled: bool = True
    created_at: datetime


# ──────────────────────────────────────────────────────────────
# Pipeline, Run
# ──────────────────────────────────────────────────────────────


class PipelineStep(BaseModel):
    name: str
    type: Literal["fetch", "extract", "transform", "score", "write"]
    config: dict[str, str | int | float | bool] = Field(default_factory=dict)


class Pipeline(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: list[PipelineStep]
    triggers: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    enabled: bool = True


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


# ──────────────────────────────────────────────────────────────
# Skill & Playbook metadata
# ──────────────────────────────────────────────────────────────


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
    inputs: dict[str, dict[str, object]] = Field(default_factory=dict)
    outputs: dict[str, dict[str, object]] = Field(default_factory=dict)
    runtime: dict[str, str | int | bool] = Field(default_factory=dict)
    llm: dict[str, str | int | float] = Field(default_factory=dict)
    logs: dict[str, bool] = Field(default_factory=dict)
    refinements: list[SkillRefinement] = Field(default_factory=list)


class PlaybookStep(BaseModel):
    model_config = {"populate_by_name": True}

    id: str | None = None
    skill: str | None = None
    include: str | None = None
    checkpoint: dict[str, object] | None = None
    switch: str | None = None
    cases: list[dict[str, object]] | None = None
    when: str | None = None
    foreach: dict[str, object] | None = None
    with_params: dict[str, object] = Field(default_factory=dict, alias="with")
    on_failure: Literal["halt", "log_and_continue", "retry", "checkpoint"] = "log_and_continue"
    timeout_s: int | None = None
    idempotency: dict[str, object] | None = None
    output: str | None = None


class PlaybookRequires(BaseModel):
    workspace_exists: bool = True
    position_set: bool = False
    sources_min: int | None = None
    mode: Literal["any", "interactive", "headless"] = "any"


class PlaybookMeta(BaseModel):
    name: str
    version: str
    description: str
    layer: Literal["operational", "kickoff"] = "operational"
    cadence: SkillCadence
    operator_time: str | None = None
    aliases: list[str] = Field(default_factory=list)
    requires: PlaybookRequires = Field(default_factory=PlaybookRequires)
    defaults: dict[str, object] = Field(default_factory=dict)
    steps: list[PlaybookStep]
    on_complete: dict[str, object] = Field(default_factory=dict)
    on_failure: dict[str, object] = Field(default_factory=dict)
