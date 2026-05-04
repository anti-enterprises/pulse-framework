"""SQLite index management for workspaces.

The index is regenerable -- it is derived from the filesystem state
and can be rebuilt with `pulse reindex`.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from pulse.utils.paths import workspace_path


@dataclass(frozen=True)
class SkippedIndexRow:
    """A filesystem row that could not be inserted into the SQLite index."""

    table: str
    row_id: str
    source_file: str
    reason: str


@dataclass(frozen=True)
class RebuildIndexResult:
    """Summary of a workspace index rebuild."""

    atom_count: int
    skipped: list[SkippedIndexRow] = field(default_factory=list)


LEGACY_ATOM_SOURCE_KIND_MAP = {
    "rss": "extraction",
    "web_page": "extraction",
    "research": "authored",
    "internal": "db_query",
}

LEGACY_ATOM_TYPE_MAP = {
    "data": "stat",
    "observation": "claim",
    "signal": "claim",
}

# Canonical DDL from doc 11, section 3
SCHEMA_DDL = """\
CREATE TABLE IF NOT EXISTS atoms (
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

CREATE INDEX IF NOT EXISTS idx_atoms_extracted_at ON atoms(extracted_at);
CREATE INDEX IF NOT EXISTS idx_atoms_source_kind ON atoms(source_kind);
CREATE INDEX IF NOT EXISTS idx_atoms_type ON atoms(type);
CREATE INDEX IF NOT EXISTS idx_atoms_source_adapter ON atoms(source_adapter);

CREATE TABLE IF NOT EXISTS directions (
  id TEXT PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN
    ('active', 'nascent', 'emerging', 'hardening', 'established',
     'peaking', 'declining', 'stale')),
  momentum REAL CHECK(momentum >= -1.0 AND momentum <= 1.0),
  confidence REAL CHECK(confidence >= 0.0 AND confidence <= 1.0),
  atom_count INTEGER DEFAULT 0,
  age_days INTEGER DEFAULT 0,
  origin_date TEXT NOT NULL,
  last_updated TEXT NOT NULL,
  source_file TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_directions_state ON directions(state);
CREATE INDEX IF NOT EXISTS idx_directions_momentum ON directions(momentum);

CREATE TABLE IF NOT EXISTS hypotheses (
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

CREATE INDEX IF NOT EXISTS idx_hypotheses_state ON hypotheses(state);
CREATE INDEX IF NOT EXISTS idx_hypotheses_last_state_change ON hypotheses(last_state_change);

CREATE TABLE IF NOT EXISTS factors (
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

CREATE INDEX IF NOT EXISTS idx_factors_kind ON factors(kind);
CREATE INDEX IF NOT EXISTS idx_factors_status ON factors(status);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  label TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN
    ('web_page', 'rss', 'podcast', 'youtube', 'newsletter', 'reddit',
     'review_aggregator', 'ad_library', 'community_forum',
     'social_platform', 'other')),
  strategic_role TEXT NOT NULL CHECK(strategic_role IN
    ('direct_competitor', 'substitute', 'complementary', 'industry_signal',
     'partner_candidate', 'trust_network', 'community_forum',
     'review_aggregator', 'ad_library', 'adjacent_winner',
     'acquisition_target')),
  health TEXT NOT NULL DEFAULT 'healthy' CHECK(health IN
    ('healthy', 'unknown', 'warning', 'failing', 'degraded', 'broken')),
  last_run TEXT,
  atom_count_last_run INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN
    ('active', 'pending', 'paused', 'archived'))
);

CREATE INDEX IF NOT EXISTS idx_sources_strategic_role ON sources(strategic_role);
CREATE INDEX IF NOT EXISTS idx_sources_health ON sources(health);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);

CREATE TABLE IF NOT EXISTS runs (
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

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_skill_name ON runs(skill_name);
CREATE INDEX IF NOT EXISTS idx_runs_playbook_name ON runs(playbook_name);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


def create_index(workspace_id: str) -> Path:
    """Create a new SQLite index for a workspace."""
    ws = workspace_path(workspace_id)
    db_path = ws / ".index.sqlite"

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA_DDL)

    # Insert schema metadata
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
        ("version", "1"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
        ("last_rebuilt", datetime.now(UTC).isoformat()),
    )
    conn.commit()
    conn.close()

    return db_path


def get_connection(workspace_id: str) -> sqlite3.Connection:
    """Get a SQLite connection for a workspace index."""
    ws = workspace_path(workspace_id)
    db_path = ws / ".index.sqlite"

    if not db_path.exists():
        raise IndexError(
            f"E015: Index not found for workspace '{workspace_id}'.\n"
            f"Run `pulse reindex` to rebuild it."
        )

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def rebuild_index(workspace_id: str) -> RebuildIndexResult:
    """Rebuild the index from filesystem.

    Also indexes hypotheses, sources, and runs (everything the schema has a
    table for that lives on disk). Atoms are JSONL (append-only, monthly
    partition). Hypotheses, runs, and sources are YAML files.
    """
    ws = workspace_path(workspace_id)
    db_path = ws / ".index.sqlite"

    # Backup existing
    if db_path.exists():
        backup = db_path.with_suffix(
            f".sqlite.bak.{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        )
        db_path.rename(backup)

    # Create fresh
    create_index(workspace_id)
    conn = get_connection(workspace_id)

    # Atoms (JSONL, monthly)
    atom_count = 0
    skipped: list[SkippedIndexRow] = []
    atoms_dir = ws / "atoms"
    if atoms_dir.exists():
        for month_dir in sorted(atoms_dir.iterdir()):
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl_file in month_dir.glob("*.jsonl"):
                source_file = str(jsonl_file.relative_to(ws))
                with open(jsonl_file) as f:
                    for line_number, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line:
                            continue
                        atom: object | None = None
                        try:
                            atom = json.loads(line)
                            if not isinstance(atom, dict):
                                raise TypeError("atom row must be a JSON object")
                            _insert_atom_row(conn, atom, source_file)
                            atom_count += 1
                        except Exception as exc:
                            skipped.append(
                                _skipped_row("atoms", atom, source_file, exc, line_number)
                            )

    # Directions (YAML, one file per direction)
    directions_dir = ws / "directions"
    if directions_dir.exists():
        for yf in sorted(directions_dir.glob("*.yaml")):
            source_file = str(yf.relative_to(ws))
            d: object | None = None
            try:
                with open(yf) as f:
                    d = yaml.safe_load(f)
                if isinstance(d, dict):
                    _insert_direction_row(conn, d, source_file)
            except Exception as exc:
                skipped.append(_skipped_row("directions", d, source_file, exc))

    # Hypotheses (YAML, one file per hypothesis)
    hypotheses_dir = ws / "hypotheses"
    if hypotheses_dir.exists():
        for yf in sorted(hypotheses_dir.glob("*.yaml")):
            source_file = str(yf.relative_to(ws))
            h: object | None = None
            try:
                with open(yf) as f:
                    h = yaml.safe_load(f)
                if isinstance(h, dict):
                    _insert_hypothesis_row(conn, h, source_file)
            except Exception as exc:
                skipped.append(_skipped_row("hypotheses", h, source_file, exc))

    # Sources (YAML, single sources.yaml under sources/)
    sources_file = ws / "sources" / "sources.yaml"
    if sources_file.exists():
        source_file = str(sources_file.relative_to(ws))
        try:
            with open(sources_file) as f:
                src_doc = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            skipped.append(_skipped_row("sources", None, source_file, exc))
            src_doc = {}
        for src in src_doc.get("sources", []):
            try:
                if isinstance(src, dict):
                    _insert_source_row(conn, src)
            except Exception as exc:
                skipped.append(_skipped_row("sources", src, source_file, exc))

    # Runs (YAML, one file per run, plus ad-hoc JSONL run logs)
    runs_dir = ws / "runs"
    if runs_dir.exists():
        for yf in sorted(runs_dir.glob("*.yaml")):
            source_file = str(yf.relative_to(ws))
            r: object | None = None
            try:
                with open(yf) as f:
                    r = yaml.safe_load(f)
                if isinstance(r, dict):
                    _insert_run_row(conn, r)
            except Exception as exc:
                skipped.append(_skipped_row("runs", r, source_file, exc))

    conn.execute(
        "UPDATE schema_meta SET value = ? WHERE key = 'last_rebuilt'",
        (datetime.now(UTC).isoformat(),),
    )
    conn.commit()
    conn.close()

    return RebuildIndexResult(atom_count=atom_count, skipped=skipped)


def _insert_atom_row(conn: sqlite3.Connection, atom: dict[str, object], source_file: str) -> None:
    """Insert a single atom into the index."""
    normalized_source_kind = LEGACY_ATOM_SOURCE_KIND_MAP.get(
        str(atom["source_kind"]),
        str(atom["source_kind"]),
    )
    normalized_type = LEGACY_ATOM_TYPE_MAP.get(str(atom["type"]), str(atom["type"]))

    conn.execute(
        """INSERT OR REPLACE INTO atoms
           (id, source_kind, source_adapter, source_ref, source_url, source_label,
            type, content, extracted_at, observed_at, entities,
            direction_ids, factor_ids, hypothesis_ids, workspace_entity_refs, source_file)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            atom["id"],
            normalized_source_kind,
            atom["source_adapter"],
            atom.get("source_ref"),
            atom.get("source_url"),
            atom.get("source_label"),
            normalized_type,
            atom["content"],
            atom["extracted_at"],
            atom.get("observed_at"),
            json.dumps(atom.get("entities", [])),
            json.dumps(atom.get("direction_ids", [])),
            json.dumps(atom.get("factor_ids", [])),
            json.dumps(atom.get("hypothesis_ids", [])),
            (
                json.dumps(atom.get("workspace_entity_refs"))
                if atom.get("workspace_entity_refs")
                else None
            ),
            source_file,
        ),
    )


def _skipped_row(
    table: str,
    row: object,
    source_file: str,
    exc: Exception,
    line_number: int | None = None,
) -> SkippedIndexRow:
    """Build a stable skip record for operator-facing reporting."""
    if isinstance(row, dict):
        row_id = str(row.get("id") or row.get("code") or "(unknown)")
    elif line_number is not None:
        row_id = f"line {line_number}"
    else:
        row_id = "(unknown)"

    return SkippedIndexRow(
        table=table,
        row_id=row_id,
        source_file=source_file,
        reason=str(exc),
    )


def _insert_hypothesis_row(conn: sqlite3.Connection, h: dict[str, object], source_file: str) -> None:
    """Insert a single hypothesis into the index."""
    conn.execute(
        """INSERT OR REPLACE INTO hypotheses
           (id, code, title, state, confidence, age_days,
            created_at, last_updated, last_state_change, auto_generated, source_file)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            h["id"],
            h["code"],
            h["title"],
            h["state"],
            _as_float(h.get("confidence"), default=0.0),
            _as_int(h.get("age_days"), default=0),
            _to_iso(h["created_at"]),
            _to_iso(h["last_updated"]),
            _to_iso(h["last_state_change"]),
            1 if h.get("auto_generated") else 0,
            source_file,
        ),
    )


def _insert_direction_row(conn: sqlite3.Connection, d: dict[str, object], source_file: str) -> None:
    """Insert a single direction into the index."""
    conn.execute(
        """INSERT OR REPLACE INTO directions
           (id, code, title, state, momentum, confidence, atom_count,
            age_days, origin_date, last_updated, source_file)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            d["id"],
            d["code"],
            d["title"],
            d["state"],
            _as_float(d.get("momentum"), default=0.0),
            _as_float(d.get("confidence"), default=0.0),
            _as_int(
                d.get("atom_count"),
                default=_len_if_list(d.get("supporting_atom_ids")),
            ),
            _as_int(d.get("age_days"), default=0),
            _to_iso(d.get("origin_date") or d.get("created_at")),
            _to_iso(d["last_updated"]),
            source_file,
        ),
    )


def _insert_source_row(conn: sqlite3.Connection, src: dict[str, object]) -> None:
    """Insert a single source into the index."""
    conn.execute(
        """INSERT OR REPLACE INTO sources
           (id, url, label, kind, strategic_role, health,
            last_run, atom_count_last_run, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            src["id"],
            src["url"] or "",
            src["label"],
            src["kind"],
            src["strategic_role"],
            src.get("health", "healthy"),
            _to_iso(src.get("last_run")) if src.get("last_run") else None,
            _as_int(src.get("atom_count_last_run"), default=0),
            src.get("status", "active"),
        ),
    )


def _insert_run_row(conn: sqlite3.Connection, r: dict[str, object]) -> None:
    """Insert a single run into the index."""
    normalized = _normalize_run_row(r)
    output_files = normalized.get("output_files")
    if isinstance(output_files, list):
        output_files_json = json.dumps(output_files)
    elif output_files:
        output_files_json = json.dumps([output_files])
    else:
        output_files_json = None

    conn.execute(
        """INSERT OR REPLACE INTO runs
           (id, skill_name, playbook_name, started_at, ended_at, status,
            workspace_id, duration_ms, error_message, knowledge_versions,
            atoms_produced, output_files)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            normalized["id"],
            normalized.get("skill_name"),
            normalized.get("playbook_name"),
            _to_iso(normalized["started_at"]),
            _to_iso(normalized.get("ended_at")) if normalized.get("ended_at") else None,
            normalized["status"],
            normalized["workspace_id"],
            (
                _as_int(normalized.get("duration_ms"))
                if normalized.get("duration_ms") is not None
                else None
            ),
            normalized.get("error_message"),
            json.dumps(normalized.get("knowledge_versions", {})),
            _as_int(normalized.get("atoms_produced"), default=0),
            output_files_json,
        ),
    )


def _normalize_run_row(r: dict[str, object]) -> dict[str, object]:
    """Normalize current and legacy run-log YAML shapes to the index schema."""
    normalized = dict(r)
    normalized["workspace_id"] = r.get("workspace_id") or r.get("workspace")
    normalized["started_at"] = r.get("started_at") or r.get("ran_at")
    normalized["ended_at"] = r.get("ended_at") or r.get("completed_at")
    normalized["status"] = r.get("status") or "succeeded"

    if not normalized.get("skill_name") and not normalized.get("playbook_name"):
        command_name = _legacy_run_command_name(r)
        if command_name:
            normalized["playbook_name"] = command_name

    if not normalized.get("atoms_produced"):
        normalized["atoms_produced"] = _legacy_run_atom_count(r)

    if not normalized.get("output_files"):
        output_files = _legacy_run_output_files(r)
        if output_files:
            normalized["output_files"] = output_files

    return normalized


def _legacy_run_command_name(r: dict[str, object]) -> str | None:
    """Infer playbook name from older `kind` / `skill` run-log fields."""
    value = r.get("kind") or r.get("skill")
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("pulse:"):
        return value.replace("pulse:", "pulse ", 1)
    if value.startswith("pulse "):
        return value
    return f"pulse {value}"


def _legacy_run_atom_count(r: dict[str, object]) -> int:
    """Infer atom count from older run-log fields."""
    for key in ("atoms_created", "new_atom_ids", "atoms"):
        value = r.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, list):
            return len(value)
    return 0


def _legacy_run_output_files(r: dict[str, object]) -> list[str]:
    """Collect output file paths from older run-log fields."""
    output_files: list[str] = []
    output = r.get("output")
    if isinstance(output, str):
        output_files.append(output)

    steps = r.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict) and isinstance(step.get("output"), str):
                output_files.append(step["output"])

    return output_files


def _to_iso(value: object) -> str:
    """Coerce datetimes / strings to ISO 8601 strings for SQLite."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[no-any-return]
    return str(value)


def _as_int(value: object, default: int = 0) -> int:
    """Coerce scalar index values to int."""
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str, bytes, bytearray)):
        return int(value)
    raise TypeError(f"cannot coerce {type(value).__name__} to int")


def _as_float(value: object, default: float = 0.0) -> float:
    """Coerce scalar index values to float."""
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, str, bytes, bytearray)):
        return float(value)
    raise TypeError(f"cannot coerce {type(value).__name__} to float")


def _len_if_list(value: object) -> int:
    """Return a list length for legacy count inference."""
    return len(value) if isinstance(value, list) else 0


def query_counts(workspace_id: str) -> dict[str, int]:
    """Get entity counts from the index."""
    try:
        conn = get_connection(workspace_id)
    except IndexError:
        return {}

    counts: dict[str, int] = {}
    for table in ["atoms", "directions", "hypotheses", "factors", "sources", "runs"]:
        row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        counts[table] = row[0] if row else 0

    conn.close()
    return counts


class IndexError(Exception):
    """Raised for index-related errors."""
