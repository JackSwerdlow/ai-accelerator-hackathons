"""Section-aware chunking, nomic embeddings, and persistent ChromaDB indexing."""

import re
import time
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from foi_system.config import (
    CHROMA_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION,
    EMBED_MODEL,
    STALENESS_DAYS,
)

_MODEL: SentenceTransformer | None = None


def _model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(EMBED_MODEL, trust_remote_code=True)  # nomic needs remote code
    return _MODEL


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a list of document strings using nomic-embed encode_document."""
    return _model().encode_document(texts).tolist()  # type: ignore[union-attr]


def embed_query(text: str) -> list[float]:
    """Embed a single query string using nomic-embed encode_query."""
    return _model().encode_query([text])[0].tolist()  # type: ignore[union-attr]


# Heading patterns for section-aware chunking
_SECTION_RE = re.compile(r"^SECTION\s+(\d+)\b")
_STANDALONE_HEADING_RE = re.compile(
    r"^(PUBLIC INTEREST TEST|PARTIAL DISCLOSURE|RESPONSE TIMELINE)\s*$"
)
_NUMBERED_HEADING_RE = re.compile(r"^\d+\.\s+[A-Z]")


def _is_heading(line: str) -> tuple[bool, str | None]:
    """Return (is_heading, section_label_or_None) for a stripped line."""
    m = _SECTION_RE.match(line)
    if m:
        return True, f"s{m.group(1)}"
    if _STANDALONE_HEADING_RE.match(line):
        return True, None
    if _NUMBERED_HEADING_RE.match(line):
        return True, None
    return False, None


def chunk_text(doc: str, source: str) -> list[dict[str, Any]]:
    """Split document into section-aware chunks.

    One heading-delimited block == one chunk.  Each dict has keys:
      text (str), section (str | None), chunk_index (int).

    Fallback: if no headings are detected, size-based split using CHUNK_SIZE / CHUNK_OVERLAP.
    Leading content before the first heading becomes chunk 0 with section=None.
    """
    lines = doc.splitlines(keepends=True)

    # --- Identify heading positions ---
    heading_positions: list[tuple[int, str | None]] = []  # (line_index, section_label)
    for i, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        is_h, section_label = _is_heading(stripped)
        if is_h:
            heading_positions.append((i, section_label))

    # --- Fallback: no headings found ---
    if not heading_positions:
        chunks: list[dict[str, Any]] = []
        step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
        start = 0
        idx = 0
        while start < len(doc):
            end = start + CHUNK_SIZE
            text_chunk = doc[start:end]
            if text_chunk.strip():
                chunks.append({"text": text_chunk, "section": None, "chunk_index": idx})
                idx += 1
            start += step
        return chunks

    # --- Section-aware split ---
    # Build block boundaries: list of (start_line, end_line_exclusive, section_label)
    blocks: list[dict[str, Any]] = []

    # Content before the first heading
    first_heading_line = heading_positions[0][0]
    if first_heading_line > 0:
        pre_text = "".join(lines[:first_heading_line])
        if pre_text.strip():
            blocks.append({"text": pre_text, "section": None, "chunk_index": 0})

    for pos, (line_idx, section_label) in enumerate(heading_positions):
        if pos + 1 < len(heading_positions):
            next_line_idx = heading_positions[pos + 1][0]
        else:
            next_line_idx = len(lines)

        block_text = "".join(lines[line_idx:next_line_idx])
        if block_text.strip():
            blocks.append({"text": block_text, "section": section_label, "chunk_index": 0})

    # Assign chunk_index sequentially
    for idx, block in enumerate(blocks):
        block["chunk_index"] = idx

    return blocks


def get_collection(
    path: str = CHROMA_PATH, name: str = COLLECTION
) -> chromadb.api.models.Collection.Collection:  # type: ignore[name-defined]
    """Return (or create) a ChromaDB collection with cosine similarity.

    If an existing collection uses a different space, it is deleted and recreated.
    """
    client = chromadb.PersistentClient(path=path)

    # Check if collection exists with wrong space config
    try:
        existing = client.get_collection(name=name)
        space = existing.configuration_json.get("hnsw", {}).get("space", "")
        if space != "cosine":
            client.delete_collection(name=name)
            # Fall through to create with cosine
        else:
            return existing  # type: ignore[return-value]
    except Exception:
        pass  # Collection doesn't exist yet — create below

    collection = client.get_or_create_collection(
        name=name,
        configuration={"hnsw": {"space": "cosine"}},
    )
    return collection  # type: ignore[return-value]


def index_policies(
    policies_dir: str,
    path: str = CHROMA_PATH,
    name: str = COLLECTION,
    now: float | None = None,
) -> int:
    """Index all *.txt files in policies_dir into ChromaDB.

    Each file is chunked, embedded, and stored with metadata:
      source, section, chunk_index, last_indexed (int epoch).

    `now` allows tests to specify a controlled timestamp.
    Returns total number of chunks indexed.
    """
    col = get_collection(path=path, name=name)
    ts = int(now if now is not None else time.time())
    total = 0

    for txt_file in sorted(Path(policies_dir).glob("*.txt")):
        source = txt_file.name
        doc_text = txt_file.read_text(encoding="utf-8")
        chunks = chunk_text(doc_text, source)
        if not chunks:
            continue

        texts = [c["text"] for c in chunks]
        ids = [f"{source}#{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "source": source,
                "section": c["section"] if c["section"] is not None else "",
                "chunk_index": c["chunk_index"],
                "last_indexed": ts,
            }
            for c in chunks
        ]

        col.add(
            ids=ids,
            embeddings=embed_documents(texts),
            documents=texts,
            metadatas=metadatas,  # type: ignore[arg-type]
        )
        total += len(chunks)

    return total


def check_freshness(
    path: str = CHROMA_PATH,
    name: str = COLLECTION,
    max_age_days: int = STALENESS_DAYS,
    now: float | None = None,
) -> list[str]:
    """Return sorted unique list of source filenames whose last_indexed is stale.

    Stale means: last_indexed < (now - max_age_days * 86400).
    """
    col = get_collection(path=path, name=name)
    cutoff = int((now if now is not None else time.time()) - max_age_days * 86400)

    result = col.get(
        where={"last_indexed": {"$lt": cutoff}},
        include=["metadatas"],
    )
    metadatas = result.get("metadatas") or []

    stale_sources: set[str] = set()
    for meta in metadatas:
        if meta and "source" in meta:
            stale_sources.add(str(meta["source"]))

    return sorted(stale_sources)
