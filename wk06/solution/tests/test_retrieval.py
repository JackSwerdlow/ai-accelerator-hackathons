"""Tests for foi_system.retrieval — search_policies()."""

import pytest

from foi_system.indexing import index_policies
from foi_system.models import RetrievedChunk
from foi_system.retrieval import search_policies


@pytest.fixture(scope="module")
def indexed_store(tmp_path_factory):
    """Index both fixture files into a tmp ChromaDB; return the path."""
    tmp = str(tmp_path_factory.mktemp("chroma"))
    fixtures_dir = "tests/fixtures"
    index_policies(fixtures_dir, path=tmp)
    return tmp


def test_query_section40_returns_personal_data_chunk_first(indexed_store):
    """s40 (personal data) chunk must be nearest for a personal-data query."""
    results = search_policies(
        "What personal information about third parties is exempt from disclosure?",
        k=5,
        path=indexed_store,
    )
    assert len(results) >= 1
    assert results[0].section == "s40"


def test_results_carry_section_and_distance(indexed_store):
    """Every result is a RetrievedChunk with float distance, non-empty source,
    int chunk_index; at least one has a non-None section; distances non-decreasing."""
    results = search_policies(
        "What exemptions apply to commercial interests and confidential information?",
        k=5,
        path=indexed_store,
    )
    assert len(results) >= 1

    for r in results:
        assert isinstance(r, RetrievedChunk)
        assert isinstance(r.distance, float)
        assert r.source != ""
        assert isinstance(r.chunk_index, int)

    # At least one chunk should have a non-None section (s40, s41, s43, etc.)
    sections = [r.section for r in results]
    assert any(s is not None for s in sections)

    # Distances must be non-decreasing (nearest-first ordering)
    distances = [r.distance for r in results]
    assert distances == sorted(distances)
