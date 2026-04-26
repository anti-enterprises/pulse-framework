"""Tests for corpus infrastructure."""

from __future__ import annotations

from pathlib import Path

import yaml

from pulse.runtime.chunking import chunk_document, estimate_tokens
from pulse.runtime.corpus import CorpusManager


def test_estimate_tokens() -> None:
    assert estimate_tokens("hello world") > 0
    assert estimate_tokens("a" * 400) == 100  # ~4 chars per token


def test_chunk_short_document() -> None:
    text = "This is a short document."
    chunks = chunk_document(text, target_tokens=100)
    assert len(chunks) == 1
    assert chunks[0].text == text


def test_chunk_long_document() -> None:
    # Create a document with many paragraphs
    paragraphs = [f"Paragraph {i}. " * 50 for i in range(10)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_document(text, target_tokens=200)
    assert len(chunks) > 1
    # Every chunk should have content
    for chunk in chunks:
        assert len(chunk.text) > 0
        assert chunk.token_count > 0


def test_chunk_empty_document() -> None:
    chunks = chunk_document("")
    assert chunks == []
    chunks = chunk_document("   ")
    assert chunks == []


def test_corpus_manager_disabled(pulse_home: Path) -> None:
    # Write config with corpus disabled
    cfg = pulse_home / "config.yaml"
    cfg.write_text(yaml.dump({"corpus": {"enabled": False}}))

    mgr = CorpusManager()
    assert mgr.is_enabled() is False


def test_corpus_manager_enabled(pulse_home: Path) -> None:
    cfg = pulse_home / "config.yaml"
    cfg.write_text(yaml.dump({"corpus": {"enabled": True}}))

    mgr = CorpusManager()
    assert mgr.is_enabled() is True


def test_corpus_status_disabled(pulse_home: Path) -> None:
    cfg = pulse_home / "config.yaml"
    cfg.write_text(yaml.dump({"corpus": {"enabled": False}}))

    mgr = CorpusManager()
    status = mgr.status()
    assert status["enabled"] is False


def test_corpus_status_enabled(pulse_home: Path) -> None:
    cfg = pulse_home / "config.yaml"
    cfg.write_text(yaml.dump({"corpus": {"enabled": True}}))

    # Create schema and index dir
    cdir = pulse_home / "corpus"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "index").mkdir(exist_ok=True)
    (cdir / "schema.yaml").write_text(yaml.dump({
        "version": 1,
        "embedding": {"provider": "voyage", "model": "voyage-3"},
        "collections": {"frameworks": {}, "industry": {}},
    }))

    mgr = CorpusManager()
    status = mgr.status()
    assert status["enabled"] is True
    assert "frameworks" in status["collections"]
    assert status["total_ingestions"] == 0
