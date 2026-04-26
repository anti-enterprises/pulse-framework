"""Paragraph-aware document chunking for corpus ingestion.

Splits on paragraph boundaries, falls back to sentences, then tokens.
Configurable target size and overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    start_offset: int
    end_offset: int
    token_count: int


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token for English)."""
    return max(1, len(text) // 4)


def chunk_document(
    text: str,
    target_tokens: int = 1000,
    overlap_tokens: int = 200,
) -> list[Chunk]:
    """Split text into chunks at paragraph boundaries.

    Falls back to sentence boundaries if paragraphs are too large,
    and to raw character splitting as last resort.
    """
    if not text.strip():
        return []

    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    # Split into paragraphs
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[Chunk] = []
    current_text = ""
    current_start = 0

    for para in paragraphs:
        if len(current_text) + len(para) + 2 <= target_chars:
            if current_text:
                current_text += "\n\n" + para
            else:
                current_text = para
                current_start = text.find(para, current_start)
        else:
            if current_text:
                end = current_start + len(current_text)
                chunks.append(Chunk(
                    text=current_text,
                    start_offset=current_start,
                    end_offset=end,
                    token_count=estimate_tokens(current_text),
                ))

            # If single paragraph exceeds target, split by sentences
            if len(para) > target_chars:
                sub_chunks = _split_by_sentences(para, target_chars, text, current_start)
                chunks.extend(sub_chunks)
                current_text = ""
                current_start = text.find(para, current_start) + len(para)
            else:
                # Start new chunk with overlap from previous
                if chunks and overlap_chars > 0:
                    overlap_text = chunks[-1].text[-overlap_chars:]
                    current_text = overlap_text + "\n\n" + para
                else:
                    current_text = para
                current_start = text.find(para, current_start if not chunks else chunks[-1].end_offset)

    # Flush remaining
    if current_text:
        end = current_start + len(current_text)
        chunks.append(Chunk(
            text=current_text,
            start_offset=current_start,
            end_offset=min(end, len(text)),
            token_count=estimate_tokens(current_text),
        ))

    return chunks


def _split_by_sentences(
    text: str, target_chars: int, full_text: str, search_start: int
) -> list[Chunk]:
    """Split a large paragraph by sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[Chunk] = []
    current = ""
    offset = full_text.find(text, search_start)

    for sent in sentences:
        if len(current) + len(sent) + 1 <= target_chars:
            current = (current + " " + sent).strip() if current else sent
        else:
            if current:
                chunks.append(Chunk(
                    text=current,
                    start_offset=offset,
                    end_offset=offset + len(current),
                    token_count=estimate_tokens(current),
                ))
                offset += len(current)
            current = sent

    if current:
        chunks.append(Chunk(
            text=current,
            start_offset=offset,
            end_offset=offset + len(current),
            token_count=estimate_tokens(current),
        ))

    return chunks
