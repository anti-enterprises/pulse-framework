"""Tests for the SQLite index."""

from __future__ import annotations

from pathlib import Path

from pulse.runtime.index import create_index, get_connection, query_counts, rebuild_index
from pulse.runtime.workspace import create_workspace


def test_create_index(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    db_path = create_index("test-ws")
    assert db_path.exists()

    # Verify tables exist
    conn = get_connection("test-ws")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t["name"] for t in tables]
    assert "atoms" in table_names
    assert "directions" in table_names
    assert "hypotheses" in table_names
    assert "factors" in table_names
    assert "sources" in table_names
    assert "runs" in table_names
    assert "schema_meta" in table_names
    conn.close()


def test_query_counts_empty(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    create_index("test-ws")
    counts = query_counts("test-ws")
    assert counts["atoms"] == 0
    assert counts["runs"] == 0


def test_rebuild_index(pulse_home: Path) -> None:
    create_workspace("test-ws", "Test", "SaaS", "tester")
    create_index("test-ws")
    atom_count = rebuild_index("test-ws")
    assert atom_count == 0  # empty workspace
