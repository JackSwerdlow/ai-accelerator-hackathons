"""Tests for the HITL approval gate (Task 11).

All tests are offline — no network, no real API calls.
Input injection via _scripted_input; console capture via StringIO.
"""

from __future__ import annotations

import json
from io import StringIO

import pytest
from rich.console import Console

from foi_system.hitl import approval_gate
from foi_system.models import (
    CaseRecord,
    Citation,
    ComplianceResult,
    ExemptionFinding,
    RedactionResult,
    ResponseDraft,
    RetrievedChunk,
    TriageResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_full_case() -> CaseRecord:
    """Return a fully-populated CaseRecord for gate testing."""
    case = CaseRecord(
        request_id="req-hitl-01",
        request_file="request_01.txt",
        request_text="Please release all employee personal records.",
    )
    case.triage = TriageResult(
        topic="personal_data",
        complexity="medium",
        summary="Request for personal data about employees.",
        confidence=0.92,
    )
    case.retrieved = [
        RetrievedChunk(
            text="Section 40 provides an absolute exemption for personal data.",
            source="exemptions.txt",
            section="s40",
            chunk_index=0,
            distance=0.18,
        )
    ]
    case.compliance = ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s40",
                kind="absolute",
                applies=True,
                rationale="Third-party personal data — release would breach GDPR.",
                citations=[
                    Citation(
                        section="s40",
                        quote="absolute exemption for personal data",
                        source="exemptions.txt",
                        chunk_index=0,
                    )
                ],
                public_interest_test=None,
            )
        ],
        policy_sources=["exemptions.txt"],
        third_party_notification_required=False,
        grounded=True,
    )
    case.response = ResponseDraft(
        letter="Dear Requester, we are withholding the requested information under s40.",
        exemptions_cited=["s40"],
        evidence_summary="Personal data exemption applies.",
    )
    case.redaction = RedactionResult(
        redacted_draft="Dear Requester, [REDACTED-name] records withheld under s40.",
        schedule=[],
        redaction_complete=True,
        needs_mandatory_review=False,
    )
    return case


def _scripted_input(*responses: str):
    it = iter(responses)
    return lambda _prompt: next(it)


def _make_console() -> Console:
    return Console(file=StringIO(), force_terminal=False, width=120)


# ---------------------------------------------------------------------------
# Test 1: empty operator hard-fails before rendering
# ---------------------------------------------------------------------------


def test_empty_operator_raises():
    """Empty or whitespace-only operator raises ValueError before any output."""
    case = _make_full_case()
    con = _make_console()

    with pytest.raises(ValueError, match="operator"):
        approval_gate(case, operator="", console=con, input_fn=_scripted_input("a", ""))

    assert con.file.getvalue() == "", "Nothing must be rendered before the ValueError"

    con2 = _make_console()
    with pytest.raises(ValueError, match="operator"):
        approval_gate(case, operator="   ", console=con2, input_fn=_scripted_input("a", ""))

    assert con2.file.getvalue() == "", "Whitespace operator must also raise before rendering"


# ---------------------------------------------------------------------------
# Test 2: recommendation is the headline (appears before distance)
# ---------------------------------------------------------------------------


def test_recommendation_is_headline():
    """The recommendation value appears in the output BEFORE the first 'distance:' substring."""
    case = _make_full_case()
    con = _make_console()

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("a", ""),
    )

    buf = con.file.getvalue()
    assert case.compliance is not None
    rec_value = case.compliance.recommendation.upper()

    assert rec_value in buf, f"Recommendation '{rec_value}' not found in output"
    assert "distance:" in buf, "'distance:' not found in output"

    idx_rec = buf.index(rec_value)
    idx_dist = buf.index("distance:")

    assert idx_rec < idx_dist, (
        f"Recommendation appears at index {idx_rec} but distance: at {idx_dist} — "
        "headline must precede evidence"
    )


# ---------------------------------------------------------------------------
# Test 3: cost must not appear at gate
# ---------------------------------------------------------------------------


def test_cost_absent_at_gate():
    """None of '$', 'USD', 'cost', 'cost_usd' may appear in the gate output."""
    case = _make_full_case()
    con = _make_console()

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("a", ""),
    )

    buf = con.file.getvalue()
    assert "$" not in buf, "'$' must not appear in gate output"
    assert "USD" not in buf, "'USD' must not appear in gate output"
    assert "cost" not in buf, "'cost' must not appear in gate output"
    assert "cost_usd" not in buf, "'cost_usd' must not appear in gate output"


# ---------------------------------------------------------------------------
# Test 4: distance label, not similarity
# ---------------------------------------------------------------------------


def test_distance_label_not_similarity():
    """Gate output contains 'distance:' and 'lower = closer' and does NOT contain 'similarity'."""
    case = _make_full_case()
    con = _make_console()

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("a", ""),
    )

    buf = con.file.getvalue()
    assert "distance:" in buf, "'distance:' not found in gate output"
    assert "lower = closer" in buf, "'lower = closer' not found in gate output"
    assert "similarity" not in buf.lower(), "'similarity' must not appear in gate output"


# ---------------------------------------------------------------------------
# Test 5: approve finalises correctly
# ---------------------------------------------------------------------------


def test_approve_finalises():
    """Approve + empty notes: decision=='approve', case.status != 'rejected', original_rec set."""
    case = _make_full_case()
    con = _make_console()

    decision = approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("a", ""),
    )

    assert decision.decision == "approve"
    assert case.decision is not None
    assert case.decision.decision == "approve"
    assert case.status != "rejected"
    assert case.decision.original_recommendation == "withhold"


# ---------------------------------------------------------------------------
# Test 6: reject sets case.status == 'rejected'
# ---------------------------------------------------------------------------


def test_reject_sets_status_rejected_still_writes_result():
    """Reject path: case.status=='rejected', decision.rejection_reason captured."""
    case = _make_full_case()
    con = _make_console()

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("r", "out of scope"),
    )

    assert case.status == "rejected"
    assert case.decision is not None
    assert case.decision.decision == "reject"
    assert case.decision.rejection_reason == "out of scope"


# ---------------------------------------------------------------------------
# Test 7: modify records modification before/after
# ---------------------------------------------------------------------------


def test_modify_records_modification_before_after():
    """Modify path: modification.before == redacted_draft, modification.after == operator input."""
    case = _make_full_case()
    con = _make_console()

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("m", "Dear Requester, revised letter."),
    )

    assert case.decision is not None
    assert case.decision.decision == "modify"
    assert case.decision.modification is not None
    assert case.redaction is not None
    assert case.decision.modification.before == case.redaction.redacted_draft
    assert case.decision.modification.after == "Dear Requester, revised letter."


# ---------------------------------------------------------------------------
# Test 8: third-party banner shown when flagged
# ---------------------------------------------------------------------------


def test_third_party_banner_shown_when_flagged():
    """Banner 'THIRD-PARTY NOTIFICATION' appears iff third_party_notification_required=True."""
    # Case WITH the flag
    case_with = _make_full_case()
    assert case_with.compliance is not None
    case_with.compliance.third_party_notification_required = True
    con_with = _make_console()

    approval_gate(
        case_with,
        operator="officer1",
        console=con_with,
        input_fn=_scripted_input("a", ""),
    )

    buf_with = con_with.file.getvalue()
    assert "THIRD-PARTY NOTIFICATION" in buf_with, (
        "Third-party banner must appear when flag is True"
    )

    # Case WITHOUT the flag
    case_without = _make_full_case()
    assert case_without.compliance is not None
    assert case_without.compliance.third_party_notification_required is False
    con_without = _make_console()

    approval_gate(
        case_without,
        operator="officer1",
        console=con_without,
        input_fn=_scripted_input("a", ""),
    )

    buf_without = con_without.file.getvalue()
    assert "THIRD-PARTY NOTIFICATION" not in buf_without, (
        "Third-party banner must NOT appear when flag is False"
    )


# ---------------------------------------------------------------------------
# Test 9: decision logs evidence_refs in JSONL audit
# ---------------------------------------------------------------------------


def test_decision_logs_evidence_refs(tmp_path):
    """After approving, JSONL audit file has one decision entry with correct evidence_refs."""
    case = _make_full_case()
    con = _make_console()

    jsonl_path = tmp_path / "audit.jsonl"
    txt_path = tmp_path / "audit.txt"

    approval_gate(
        case,
        operator="officer1",
        console=con,
        input_fn=_scripted_input("a", ""),
        audit_jsonl_path=jsonl_path,
        audit_txt_path=txt_path,
    )

    lines = jsonl_path.read_text().strip().split("\n")
    assert len(lines) == 1, f"Expected exactly 1 audit line, got {len(lines)}"

    entry = json.loads(lines[0])
    assert entry["event_type"] == "decision"

    expected_refs = [f"{c.source}#{c.chunk_index}" for c in case.retrieved]
    assert isinstance(entry["payload"]["evidence_refs"], list)
    assert entry["payload"]["evidence_refs"] == expected_refs
    assert entry["payload"]["decision"] == "approve"
