"""SQLite index management for workspaces.

The index is regenerable -- it is derived from the filesystem state
and can be rebuilt with `pulse reindex`.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pulse.utils.paths import workspace_path

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
    ('nascent', 'emerging', 'hardening', 'established', 'peaking', 'declining', 'stale')),
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


def rebuild_index(workspace_id: str) -> int:
    """Rebuild the index from filesystem. Returns number of atoms indexed.

    Also indexes hypotheses, sources, and runs (everything the schema has a
    table for that lives on disk). Atoms are JSONL (append-only, monthly
    partition). Hypotheses, runs, and sources are YAML files.
    """
    import json
    import yaml

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
    atoms_dir = ws / "atoms"
    if atoms_dir.exists():
        for month_dir in sorted(atoms_dir.iterdir()):
            if not month_dir.is_dir() or month_dir.name.startswith("."):
                continue
            for jsonl_file in month_dir.glob("*.jsonl"):
                with open(jsonl_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            atom = json.loads(line)
                            _insert_atom_row(conn, atom, str(jsonl_file.relative_to(ws)))
                            atom_count += 1
                        except (json.JSONDecodeError, sqlite3.Error):
                            continue

    # Hypotheses (YAML, one file per hypothesis)
    hypotheses_dir = ws / "hypotheses"
    if hypotheses_dir.exists():
        for yf in sorted(hypotheses_dir.glob("*.yaml")):
            try:
                with open(yf) as f:
                    h = yaml.safe_load(f)
                if isinstance(h, dict):
                    _insert_hypothesis_row(conn, h, str(yf.relative_to(ws)))
            except (yaml.YAMLError, sqlite3.Error, KeyError):
                continue

    # Sources (YAML, single sources.yaml under sources/)
    sources_file = ws / "sources" / "sources.yaml"
    if sources_file.exists():
        try:
            with open(sources_file) as f:
                src_doc = yaml.safe_load(f) or {}
            for src in src_doc.get("sources", []):
                if isinstance(src, dict):
                    _insert_source_row(conn, src)
        except (yaml.YAMLError, sqlite3.Error):
            pass

    # Runs (YAML, one file per run, plus ad-hoc JSONL run logs)
    runs_dir = ws / "runs"
    if runs_dir.exists():
        for yf in sorted(runs_dir.glob("*.yaml")):
            try:
                with open(yf) as f:
                    r = yaml.safe_load(f)
                if isinstance(r, dict):
                    _insert_run_row(conn, r)
            except (yaml.YAMLError, sqlite3.Error, KeyError):
                continue

    conn.execute(
        "UPDATE schema_meta SET value = ? WHERE key = 'last_rebuilt'",
        (datetime.now(UTC).isoformat(),),
    )
    conn.commit()
    conn.close()

    return atom_count


def _insert_atom_row(conn: sqlite3.Connection, atom: dict[str, object], source_file: str) -> None:
    """Insert a single atom into the index."""
    import json

    conn.execute(
        """INSERT OR REPLACE INTO atoms
           (id, source_kind, source_adapter, source_ref, source_url, source_label,
            type, content, extracted_at, observed_at, entities,
            direction_ids, factor_ids, hypothesis_ids, workspace_entity_refs, source_file)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            atom["id"],
            atom["source_kind"],
            atom["source_adapter"],
            atom.get("source_ref"),
            atom.get("source_url"),
            atom.get("source_label"),
            atom["type"],
            atom["content"],
            atom["extracted_at"],
            atom.get("observed_at"),
            json.dumps(atom.get("entities", [])),
            json.dumps(atom.get("direction_ids", [])),
            json.dumps(atom.get("factor_ids", [])),
            json.dumps(atom.get("hypothesis_ids", [])),
            json.dumps(atom.get("workspace_entity_refs")) if atom.get("workspace_entity_refs") else None,
            source_file,
        ),
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
            float(h.get("confidence", 0.0)),
            int(h.get("age_days", 0)),
            _to_iso(h["created_at"]),
            _to_iso(h["last_updated"]),
            _to_iso(h["last_state_change"]),
            1 if h.get("auto_generated") else 0,
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
            int(src.get("atom_count_last_run", 0)),
            src.get("status", "active"),
        ),
    )


def _insert_run_row(conn: sqlite3.Connection, r: dict[str, object]) -> None:
    """Insert a single run into the index."""
    import json as _json

    output_files = r.get("output_files")
    if isinstance(output_files, list):
        output_files_json = _json.dumps(output_files)
    elif output_files:
        output_files_json = _json.dumps([output_files])
    else:
        output_files_json = None

    conn.execute(
        """INSERT OR REPLACE INTO runs
           (id, skill_name, playbook_name, started_at, ended_at, status,
            workspace_id, duration_ms, error_message, knowledge_versions,
            atoms_produced, output_files)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            r["id"],
            r.get("skill_name"),
            r.get("playbook_name"),
            _to_iso(r["started_at"]),
            _to_iso(r.get("ended_at")) if r.get("ended_at") else None,
            r["status"],
            r["workspace_id"],
            int(r["duration_ms"]) if r.get("duration_ms") is not None else None,
            r.get("error_message"),
            _json.dumps(r.get("knowledge_versions", {})),
            int(r.get("atoms_produced", 0)),
            output_files_json,
        ),
    )


def _to_iso(value: object) -> str:
    """Coerce datetimes / strings to ISO 8601 strings for SQLite."""
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[no-any-return]
    return str(value)


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
