"""Tests for citation verification ladder (L1 id membership, L2 verbatim match)."""

import pytest

from foi_system.models import (
    Citation,
    ComplianceResult,
    ExemptionFinding,
    RetrievedChunk,
)
from foi_system.verification import verify_citations


@pytest.fixture
def chunk_s40():
    """s40 chunk: Personal data about third parties and data protection principles."""
    return RetrievedChunk(
        text=(
            "Personal data about third parties is exempt if disclosure would "
            "breach the data protection principles."
        ),
        source="exemptions.txt",
        section="s40",
        chunk_index=4,
        distance=0.3,
    )


def test_fabricated_chunk_id_fails_L1(chunk_s40):
    """L1 fails: cited chunk ID (source, chunk_index) not in retrieved chunks."""
    # Citation references chunk_index=99, which does not exist in retrieved list
    result = ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s40",
                kind="absolute",
                applies=True,
                rationale="r",
                citations=[
                    Citation(
                        section="s40",
                        quote="some quote",
                        source="exemptions.txt",
                        chunk_index=99,
                    )
                ],
            )
        ],
    )
    grounded, problems = verify_citations(result, [chunk_s40])
    assert grounded is False
    assert len(problems) == 1
    assert "not retrieved" in problems[0]


def test_misquote_fails_L2(chunk_s40):
    """L2 fails: quote is fabricated, not found verbatim in chunk."""
    # Citation references correct chunk but with fabricated quote
    result = ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s40",
                kind="absolute",
                applies=True,
                rationale="r",
                citations=[
                    Citation(
                        section="s40",
                        quote="personal data is always fully releasable to anyone who asks",
                        source="exemptions.txt",
                        chunk_index=4,
                    )
                ],
            )
        ],
    )
    grounded, problems = verify_citations(result, [chunk_s40])
    assert grounded is False
    assert len(problems) == 1
    assert "verbatim" in problems[0] or "coverage" in problems[0]


def test_valid_verbatim_quote_passes(chunk_s40):
    """L2 passes: quote is a valid verbatim excerpt from the chunk."""
    # Citation with exact verbatim excerpt from chunk text
    result = ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s40",
                kind="absolute",
                applies=True,
                rationale="r",
                citations=[
                    Citation(
                        section="s40",
                        quote="Personal data about third parties is exempt",
                        source="exemptions.txt",
                        chunk_index=4,
                    )
                ],
            )
        ],
    )
    grounded, problems = verify_citations(result, [chunk_s40])
    assert grounded is True
    assert problems == []
