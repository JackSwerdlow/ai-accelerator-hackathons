"""Tests for the supervisor pipeline (Task 12).

All tests are offline — no network, no ChromaDB, no real LLM calls.
LLMs injected via DI kwargs; search_policies monkeypatched to return [].
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from langchain_core.runnables import RunnableLambda

import foi_system.retrieval as _retrieval_mod
from foi_system.cost import CostTracker
from foi_system.models import (
    CaseRecord,
    ComplianceResult,
    HumanDecision,
    Modification,
    RedactionResult,
    ResponseDraft,
    TriageResult,
)
from foi_system.supervisor import CircuitBreaker, process_folder, process_request

# ---------------------------------------------------------------------------
# Monkeypatch helpers
# ---------------------------------------------------------------------------


def _patch_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch search_policies to return [] (no ChromaDB required)."""
    monkeypatch.setattr(_retrieval_mod, "search_policies", lambda *a, **kw: [])


# ---------------------------------------------------------------------------
# Fake LLMs
# ---------------------------------------------------------------------------


def _triage_llm() -> RunnableLambda:
    return RunnableLambda(
        lambda _: TriageResult(
            topic="staffing_hr",
            complexity="medium",
            summary="Staffing records request.",
            confidence=0.85,
        )
    )


def _compliance_llm() -> RunnableLambda:
    return RunnableLambda(
        lambda _: ComplianceResult(
            recommendation="withhold",
            exemptions=[],
            grounded=True,
            notes="",
        )
    )


def _response_llm() -> RunnableLambda:
    return RunnableLambda(
        lambda _: ResponseDraft(
            letter="Dear Requester, your request is withheld.",
            exemptions_cited=[],
            evidence_summary="withheld on compliance grounds",
        )
    )


def _redaction_llm() -> RunnableLambda:
    return RunnableLambda(
        lambda _: RedactionResult(
            redacted_draft="Dear Requester [REDACTED], your request is withheld.",
            redaction_complete=True,
            needs_mandatory_review=False,
        )
    )


def _raising_llm() -> RunnableLambda:
    """LLM that always raises RuntimeError."""
    return RunnableLambda(lambda _: (_ for _ in ()).throw(RuntimeError("boom")))


# ---------------------------------------------------------------------------
# Gate helper
# ---------------------------------------------------------------------------


def _approve_gate(case: CaseRecord, op: str) -> HumanDecision:
    """Fake gate: approve with minimal valid HumanDecision."""
    decision = HumanDecision(
        decision="approve",
        operator=op,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        original_recommendation=case.compliance.recommendation if case.compliance else "withhold",
        evidence_refs=[f"{c.source}#{c.chunk_index}" for c in case.retrieved],
    )
    case.decision = decision
    return decision


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_single_request_writes_result_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")

    results_dir = tmp_path / "results"
    case = process_request(
        str(req_file),
        "op1",
        CostTracker(),
        CircuitBreaker(),
        triage_llm=_triage_llm(),
        compliance_llm=_compliance_llm(),
        response_llm=_response_llm(),
        redaction_llm=_redaction_llm(),
        gate_fn=_approve_gate,
        results_dir=results_dir,
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    assert case.status == "processed"
    result_file = results_dir / "request.json"
    assert result_file.exists()
    data = json.loads(result_file.read_text())
    assert data["request_id"] == "request"
    assert case.triage is not None
    assert case.compliance is not None
    assert case.response is not None
    assert case.redaction is not None
    assert case.decision is not None


def test_stage_error_uses_fallback_and_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")

    case = process_request(
        str(req_file),
        "op1",
        CostTracker(),
        CircuitBreaker(),
        triage_llm=_raising_llm(),
        compliance_llm=_compliance_llm(),
        response_llm=_response_llm(),
        redaction_llm=_redaction_llm(),
        gate_fn=_approve_gate,
        results_dir=tmp_path / "results",
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    # Typed fallback was applied for triage
    assert case.triage is not None
    assert case.triage.topic == "other"
    assert case.triage.confidence == 0.0
    # At least one error mentioning "triage"
    assert any("triage" in e for e in case.errors)
    # Pipeline continued
    assert case.compliance is not None
    # Final status — did not crash
    assert case.status in ("processed", "rejected")


def test_fault_injected_at_every_stage_completes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")

    results_dir = tmp_path / "results"
    case = process_request(
        str(req_file),
        "op1",
        CostTracker(),
        CircuitBreaker(),
        triage_llm=_raising_llm(),
        compliance_llm=_raising_llm(),
        response_llm=_raising_llm(),
        redaction_llm=_raising_llm(),
        gate_fn=_approve_gate,
        results_dir=results_dir,
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    result_file = results_dir / "request.json"
    assert result_file.exists()
    assert len(case.errors) >= 4
    assert case.status in ("processed", "rejected", "error")
    assert case.status != "pending"


def test_batch_one_failure_does_not_abort_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_search(monkeypatch)

    # Write two request files
    (tmp_path / "req1.txt").write_text("First request.")
    (tmp_path / "req2.txt").write_text("Second request.")

    call_count = 0

    def _fake_process_request(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("simulated failure on first request")
        # Second call: return a minimal CaseRecord
        path = args[0]
        stem = Path(path).stem
        return CaseRecord(
            request_id=stem,
            request_file=Path(path).name,
            request_text="Second request.",
            status="processed",
        )

    import foi_system.supervisor as _supervisor_mod

    monkeypatch.setattr(_supervisor_mod, "process_request", _fake_process_request)

    results = process_folder(
        str(tmp_path),
        "op1",
        results_dir=str(tmp_path / "results"),
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    assert len(results) == 2
    statuses = {r.status for r in results}
    assert "error" in statuses
    # The second succeeded
    assert any(r.status == "processed" for r in results)


def test_circuit_breaker_degrades_after_threshold(tmp_path: Path) -> None:
    breaker = CircuitBreaker()

    breaker.record_failure("triage")
    breaker.record_failure("triage")
    breaker.record_failure("triage")
    assert breaker.is_degraded("triage")

    breaker.record_failure("compliance")
    breaker.record_failure("compliance")
    assert not breaker.is_degraded("compliance")


def test_costs_accumulated_per_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")

    results_dir = tmp_path / "results"
    cost = CostTracker()

    case = process_request(
        str(req_file),
        "op1",
        cost,
        CircuitBreaker(),
        triage_llm=_triage_llm(),
        compliance_llm=_compliance_llm(),
        response_llm=_response_llm(),
        redaction_llm=_redaction_llm(),
        gate_fn=_approve_gate,
        results_dir=results_dir,
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    # Fake LLMs don't emit usage so cost should be 0.0
    assert cost.per_request_total() == 0.0
    assert cost.per_agent() == {}
    # CaseRecord has costs field
    assert case.costs == []
    # Result JSON includes costs field
    result_file = results_dir / "request.json"
    assert "costs" in json.loads(result_file.read_text())


def test_per_request_costs_embedded_in_result_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per-request cost entries must be embedded in case.costs and the result JSON
    (PLAN §3.3), sliced to THIS request only — not left empty, not the whole batch.

    Real LLM calls emit usage; fakes don't, so this test simulates a captured usage
    entry via a triage fake with a side effect, plus a pre-seeded prior-batch entry
    that must be excluded from this request's costs.
    """
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")
    results_dir = tmp_path / "results"

    cost = CostTracker()
    # Prior batch item's cost — must NOT appear in this request's case.costs.
    cost.add_from_usage(
        "triage", "claude-haiku-4-5-20251001", {"input_tokens": 1, "output_tokens": 1}
    )

    def _triage_with_usage(_msgs: object) -> TriageResult:
        # Simulate the usage the real structured+retry call would have captured.
        cost.add_from_usage(
            "triage", "claude-haiku-4-5-20251001", {"input_tokens": 100, "output_tokens": 20}
        )
        return TriageResult(
            topic="staffing_hr", complexity="medium", summary="Staff records.", confidence=0.8
        )

    case = process_request(
        str(req_file),
        "op1",
        cost,
        CircuitBreaker(),
        triage_llm=RunnableLambda(_triage_with_usage),
        compliance_llm=_compliance_llm(),
        response_llm=_response_llm(),
        redaction_llm=_redaction_llm(),
        gate_fn=_approve_gate,
        results_dir=results_dir,
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    # Exactly this request's one entry is embedded (prior-batch entry excluded).
    assert len(case.costs) == 1
    assert case.costs[0].input_tokens == 100
    assert case.costs[0].output_tokens == 20
    assert case.costs[0].cost_usd > 0.0
    # And it round-trips into the written result artefact.
    written = json.loads((results_dir / "request.json").read_text())
    assert len(written["costs"]) == 1
    assert written["costs"][0]["input_tokens"] == 100


def test_modify_uses_override_as_final_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_search(monkeypatch)
    req_file = tmp_path / "request.txt"
    req_file.write_text("Please release all staff records.")

    def _modify_gate(case: CaseRecord, op: str) -> HumanDecision:
        decision = HumanDecision(
            decision="modify",
            operator=op,
            timestamp=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            original_recommendation=(
                case.compliance.recommendation if case.compliance else "withhold"
            ),
            modification=Modification(before="Original.", after="Revised letter."),
            evidence_refs=[f"{c.source}#{c.chunk_index}" for c in case.retrieved],
        )
        case.decision = decision
        return decision

    results_dir = tmp_path / "results"
    case = process_request(
        str(req_file),
        "op1",
        CostTracker(),
        CircuitBreaker(),
        triage_llm=_triage_llm(),
        compliance_llm=_compliance_llm(),
        response_llm=_response_llm(),
        redaction_llm=_redaction_llm(),
        gate_fn=_modify_gate,
        results_dir=results_dir,
        audit_jsonl_path=str(tmp_path / "audit.jsonl"),
        audit_txt_path=str(tmp_path / "audit.txt"),
    )

    assert case.decision is not None
    assert case.decision.decision == "modify"
    assert case.response is not None
    assert case.response.letter == "Revised letter."
    assert case.status == "processed"

    result_file = results_dir / "request.json"
    assert result_file.exists()
    data = json.loads(result_file.read_text())
    assert data["decision"]["decision"] == "modify"
