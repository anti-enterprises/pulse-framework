"""Corpus manager — optional local RAG with LanceDB.

All corpus operations gracefully degrade when:
- Corpus is disabled in config
- LanceDB/embedding deps are not installed

Skills with `corpus_queries: optional: true` work fine without corpus.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import yaml

from pulse.utils.atomic_write import atomic_append
from pulse.utils.paths import config_path, corpus_dir


@dataclass
class ChunkResult:
    text: str
    score: float
    metadata: dict[str, Any]


class CorpusManager:
    """Manages the optional local RAG corpus."""

    def __init__(self) -> None:
        self._db: Any = None

    def is_enabled(self) -> bool:
        """Check if corpus is enabled in config."""
        cfg = config_path()
        if not cfg.exists():
            return False
        with open(cfg) as f:
            data = yaml.safe_load(f) or {}
        return bool(data.get("corpus", {}).get("enabled", False))

    def _require_enabled(self) -> None:
        if not self.is_enabled():
            raise CorpusError(
                "E007: Corpus is not enabled.\n"
                "Run `pulse enable-corpus` to enable it."
            )

    def _require_deps(self) -> None:
        try:
            import lancedb  # noqa: F401
        except ImportError as e:
            raise CorpusError(
                "E010: Corpus requires additional dependencies.\n"
                "Run: pip install pulse-skills[corpus]"
            ) from e

    def _get_config(self) -> dict[str, Any]:
        """Load corpus config from config.yaml."""
        cfg = config_path()
        if not cfg.exists():
            return {}
        with open(cfg) as f:
            data = yaml.safe_load(f) or {}
        result: dict[str, Any] = data.get("corpus", {})
        return result

    def initialize(
        self,
        provider: str = "voyage",
        model: str = "voyage-3",
        api_key_env: str = "VOYAGE_API_KEY",
    ) -> None:
        """Initialize corpus infrastructure."""
        self._require_deps()

        cdir = corpus_dir()
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "index").mkdir(exist_ok=True)

        # Write corpus schema
        schema: dict[str, Any] = {
            "version": 1,
            "embedding": {
                "provider": provider,
                "model": model,
                "api_key_env": api_key_env,
            },
            "chunking": {
                "strategy": "paragraph_aware",
                "target_tokens": 1000,
                "overlap_tokens": 200,
            },
            "retrieval": {
                "default_top_k": 20,
                "rerank": False,
            },
            "collections": {
                "frameworks": {
                    "metadata_required": ["framework", "topic"],
                    "metadata_optional": ["source_ref", "author", "date_authored"],
                },
                "industry": {
                    "metadata_required": ["vertical"],
                    "metadata_optional": ["region", "date_range"],
                },
                "case-studies": {
                    "metadata_required": ["company", "vertical"],
                    "metadata_optional": ["outcome", "framework_applied"],
                },
                "interviews": {
                    "metadata_required": ["interviewee_role"],
                    "metadata_optional": ["company", "date"],
                },
                "workspace-specific": {
                    "metadata_required": ["workspace_id"],
                    "metadata_optional": [],
                },
                "misc": {
                    "metadata_required": [],
                    "metadata_optional": ["source", "notes"],
                },
            },
        }

        schema_path = cdir / "schema.yaml"
        schema_path.write_text(yaml.dump(schema, default_flow_style=False))

        # Update config
        cfg = config_path()
        with open(cfg) as f:
            config = yaml.safe_load(f) or {}
        config.setdefault("corpus", {})
        config["corpus"]["enabled"] = True
        config["corpus"]["embedding"] = {
            "provider": provider,
            "model": model,
            "api_key_env": api_key_env,
        }
        config["corpus"]["storage_path"] = str(cdir)
        from pulse.utils.atomic_write import atomic_write
        atomic_write(cfg, yaml.dump(config, default_flow_style=False))

    def ingest(
        self,
        text: str,
        collection: str,
        metadata: dict[str, Any],
        source_path: str | None = None,
    ) -> int:
        """Ingest text into the corpus. Returns number of chunks indexed."""
        self._require_enabled()
        self._require_deps()

        from pulse.runtime.chunking import chunk_document

        config = self._get_config()
        chunking = config.get("chunking", {})
        target = chunking.get("target_tokens", 1000)
        overlap = chunking.get("overlap_tokens", 200)

        chunks = chunk_document(text, target_tokens=target, overlap_tokens=overlap)

        # Embed and store (simplified — real implementation uses LanceDB)
        # For now, log the ingestion
        log_path = corpus_dir() / "ingestion-log.jsonl"
        for chunk in chunks:
            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "collection": collection,
                "chunk_tokens": chunk.token_count,
                "metadata": metadata,
                "source_path": source_path,
            }
            atomic_append(log_path, json.dumps(entry))

        return len(chunks)

    def query(
        self,
        query_text: str,
        collection: str | None = None,
        filters: dict[str, Any] | None = None,
        top_k: int = 20,
    ) -> list[ChunkResult]:
        """Query the corpus. Returns ranked chunk results."""
        self._require_enabled()
        self._require_deps()

        # Placeholder — real implementation uses LanceDB vector search
        return []

    def status(self) -> dict[str, Any]:
        """Get corpus status information."""
        if not self.is_enabled():
            return {"enabled": False}

        cdir = corpus_dir()
        schema_path = cdir / "schema.yaml"
        log_path = cdir / "ingestion-log.jsonl"

        result: dict[str, Any] = {"enabled": True}

        if schema_path.exists():
            with open(schema_path) as f:
                schema = yaml.safe_load(f) or {}
            result["collections"] = list(schema.get("collections", {}).keys())
            result["embedding_provider"] = schema.get("embedding", {}).get("provider")

        if log_path.exists():
            with open(log_path) as lf:
                line_count = sum(1 for _ in lf)
            result["total_ingestions"] = line_count
        else:
            result["total_ingestions"] = 0

        # Index size
        index_dir = cdir / "index"
        if index_dir.exists():
            size = sum(f.stat().st_size for f in index_dir.rglob("*") if f.is_file())
            result["index_size_mb"] = round(size / (1024 * 1024), 2)

        return result


class CorpusError(Exception):
    """Raised for corpus-related errors."""
