"""Tests for foi_system.models — all Pydantic v2 schemas."""

import pytest
from pydantic import ValidationError

from foi_system.models import (
    CaseRecord,
    ExemptionFinding,
    HumanDecision,
    RetrievedChunk,
    TriageResult,
)


def test_triageresult_rejects_unknown_topic() -> None:
    """TriageResult must reject topics not in the Literal."""
    with pytest.raises(ValidationError):
        TriageResult(
            topic="banana",  # type: ignore[arg-type]
            complexity="low",
            summary="test",
            confidence=0.9,
        )


def test_triage_confidence_bounds() -> None:
    """confidence must be in [0.0, 1.0]; values outside raise ValidationError."""
    with pytest.raises(ValidationError):
        TriageResult(
            topic="finance_spending",
            complexity="low",
            summary="test",
            confidence=1.5,
        )
    with pytest.raises(ValidationError):
        TriageResult(
            topic="finance_spending",
            complexity="low",
            summary="test",
            confidence=-0.1,
        )
    # Valid value should not raise
    result = TriageResult(
        topic="finance_spending",
        complexity="low",
        summary="test",
        confidence=0.8,
    )
    assert result.confidence == 0.8


def test_exemptionfinding_kind_required() -> None:
    """ExemptionFinding.kind is required and must be 'absolute' or 'qualified'."""
    # Missing kind raises
    with pytest.raises(ValidationError):
        ExemptionFinding(  # type: ignore[call-arg]
            section="s40",
            applies=True,
            rationale="personal data",
        )
    # Invalid kind raises
    with pytest.raises(ValidationError):
        ExemptionFinding(
            section="s40",
            kind="unknown",  # type: ignore[arg-type]
            applies=True,
            rationale="personal data",
        )
    # Both valid values are accepted
    ef_abs = ExemptionFinding(
        section="s40",
        kind="absolute",
        applies=True,
        rationale="personal data",
    )
    assert ef_abs.kind == "absolute"

    ef_qual = ExemptionFinding(
        section="s36",
        kind="qualified",
        applies=True,
        rationale="prejudice to effective conduct",
    )
    assert ef_qual.kind == "qualified"


def test_humandecision_requires_nonempty_operator() -> None:
    """HumanDecision.operator must be non-empty and non-whitespace-only."""
    with pytest.raises(ValidationError):
        HumanDecision(
            operator="",
            decision="approve",
            timestamp="2026-06-24T10:00:00Z",
            original_recommendation="release",
        )
    with pytest.raises(ValidationError):
        HumanDecision(
            operator="   ",
            decision="approve",
            timestamp="2026-06-24T10:00:00Z",
            original_recommendation="release",
        )
    # Valid operator is accepted
    hd = HumanDecision(
        operator="Alice Smith",
        decision="approve",
        timestamp="2026-06-24T10:00:00Z",
        original_recommendation="release",
    )
    assert hd.operator == "Alice Smith"


def test_caserecord_roundtrips_json() -> None:
    """CaseRecord with nested models round-trips through model_dump / model_validate."""
    triage = TriageResult(
        topic="procurement_commercial",
        complexity="medium",
        summary="Request about contract values",
        confidence=0.75,
    )
    chunk = RetrievedChunk(
        text="Section 43 exemption applies to commercial interests.",
        source="foi_policy.pdf",
        chunk_index=3,
        distance=0.12,
    )
    record = CaseRecord(
        request_id="r-001",
        request_file="request.txt",
        request_text="Please provide all contract values above £50k.",
        triage=triage,
        retrieved=[chunk],
    )
    dumped = record.model_dump()
    reconstructed = CaseRecord.model_validate(dumped)
    assert reconstructed == record
