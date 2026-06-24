"""Tests for foi_system.indexing — section-aware chunking, nomic embeddings, ChromaDB.

All tests use real nomic embeddings (model already cached) and tmp_path for ChromaDB dirs.
"""

import time
from pathlib import Path

from foi_system.indexing import check_freshness, chunk_text, get_collection, index_policies

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_section_aware_chunk_is_one_exemption() -> None:
    """chunk_text splits exemptions.txt so each SECTION heading is its own chunk.

    - Exactly one chunk has section == "s40".
    - That s40 chunk's text contains "personal" (case-insensitive).
    - That s40 chunk's text does NOT contain "confidence" or "actionable" (s41 content).
    - A separate chunk has section == "s41".
    """
    text = (FIXTURES_DIR / "exemptions.txt").read_text()
    chunks = chunk_text(text, "exemptions.txt")

    s40_chunks = [c for c in chunks if c["section"] == "s40"]
    s41_chunks = [c for c in chunks if c["section"] == "s41"]

    assert len(s40_chunks) == 1, f"Expected exactly one s40 chunk; got {len(s40_chunks)}"
    s40_text = s40_chunks[0]["text"].lower()
    assert "personal" in s40_text, "s40 chunk must contain 'personal'"
    assert "confidence" not in s40_text, "s40 chunk must NOT contain s41 text ('confidence')"
    assert "actionable" not in s40_text, "s40 chunk must NOT contain s41 text ('actionable')"

    assert len(s41_chunks) >= 1, "Expected at least one s41 chunk"


def test_index_policies_returns_chunk_count(tmp_path: Path) -> None:
    """index_policies returns total chunk count == collection.count() after indexing."""
    tmp = str(tmp_path / "chroma")
    count = index_policies(str(FIXTURES_DIR), path=tmp)

    assert isinstance(count, int), "index_policies must return an int"
    assert count > 0, "chunk count must be positive"

    col = get_collection(tmp)
    assert col.count() == count, "collection.count() must equal returned chunk count"


def test_index_persists_across_new_client(tmp_path: Path) -> None:
    """Indexed chunks survive a fresh PersistentClient (true disk persistence)."""
    tmp = str(tmp_path / "chroma")
    count = index_policies(str(FIXTURES_DIR), path=tmp)

    # Open a brand-new collection handle (new PersistentClient internally)
    fresh_col = get_collection(tmp)
    assert fresh_col.count() > 0, "Collection should have documents after reopen"
    assert fresh_col.count() == count, "count must match across client instances"


def test_cosine_space_persists_on_reopen(tmp_path: Path) -> None:
    """After indexing, reopening the collection still shows cosine space in configuration_json."""
    tmp = str(tmp_path / "chroma")
    index_policies(str(FIXTURES_DIR), path=tmp)

    col = get_collection(tmp)
    space = col.configuration_json["hnsw"]["space"]
    assert space == "cosine", f"Expected cosine space, got: {space!r}"


def test_metadata_has_source_section_epoch(tmp_path: Path) -> None:
    """Every stored metadata dict has required keys; at least one record has section == 's40'."""
    tmp = str(tmp_path / "chroma")
    index_policies(str(FIXTURES_DIR), path=tmp)

    col = get_collection(tmp)
    result = col.get(include=["metadatas"])
    metadatas = result["metadatas"]

    assert metadatas, "Should have at least one metadata record"

    for meta in metadatas:
        assert "source" in meta, f"Missing 'source' key in metadata: {meta}"
        assert "section" in meta, f"Missing 'section' key in metadata: {meta}"
        assert "chunk_index" in meta, f"Missing 'chunk_index' key in metadata: {meta}"
        assert "last_indexed" in meta, f"Missing 'last_indexed' key in metadata: {meta}"
        assert isinstance(meta["last_indexed"], int), (
            f"last_indexed must be int, got {type(meta['last_indexed'])}"
        )

    s40_records = [m for m in metadatas if m["section"] == "s40"]
    assert len(s40_records) >= 1, "At least one record must have section == 's40'"


def test_check_freshness_flags_old_docs(tmp_path: Path) -> None:
    """check_freshness returns stale source filenames; fresh index returns []."""
    # Index with a timestamp 40 days in the past (stale)
    tmp = str(tmp_path / "chroma_stale")
    old_now = time.time() - 40 * 86400
    index_policies(str(FIXTURES_DIR), path=tmp, now=old_now)

    stale = check_freshness(tmp, max_age_days=30)
    assert isinstance(stale, list), "check_freshness must return a list"
    # Both fixture files should be flagged as stale
    assert "exemptions.txt" in stale, "exemptions.txt should be flagged stale"
    assert "handling.txt" in stale, "handling.txt should be flagged stale"

    # Index fresh (default now) into a separate tmp dir
    tmp2 = str(tmp_path / "chroma_fresh")
    index_policies(str(FIXTURES_DIR), path=tmp2)

    fresh = check_freshness(tmp2, max_age_days=30)
    assert fresh == [], f"Expected no stale docs after fresh index, got: {fresh}"
