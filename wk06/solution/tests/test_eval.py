"""Tests for the evaluation harness (Task 15).

All tests are offline — agents monkeypatched at module level, no network calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import foi_system.agents.compliance as _compliance_mod
import foi_system.agents.triage as _triage_mod
from eval.eval_harness import run_eval
from foi_system.models import (
    Citation,
    ComplianceResult,
    ExemptionFinding,
    RetrievedChunk,
    TriageResult,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_gold_file(tmp_path: Path, items: list[dict]) -> str:
    """Write items as JSONL to tmp_path/gold.jsonl and return the path string."""
    path = tmp_path / "gold.jsonl"
    path.write_text("\n".join(json.dumps(item) for item in items) + "\n", encoding="utf-8")
    return str(path)


_GOLD_TEMPLATE = {
    "id": "t1",
    "request": "Please release staff records.",
    "topic": "staffing_hr",
    "complexity": "low",
    "recommendation": "withhold",
    "exemption_sections": ["s40"],
}

_SIMPLE_TRIAGE = TriageResult(
    topic="staffing_hr",
    complexity="low",
    summary="staffing request",
    confidence=0.9,
)


# ---------------------------------------------------------------------------
# Test 1 — accuracy, recall, false-positive rate
# ---------------------------------------------------------------------------


def test_eval_reports_accuracy_recall_fp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        # item 1: gold={"s40"}, predicted={"s40"} → exact match
        {**_GOLD_TEMPLATE, "id": "t1", "exemption_sections": ["s40"]},
        # item 2: gold={"s43"}, predicted={"s40"} → wrong section (FP + FN)
        {**_GOLD_TEMPLATE, "id": "t2", "exemption_sections": ["s43"]},
    ]
    gold_path = _make_gold_file(tmp_path, items)

    results_q = iter(
        [
            ComplianceResult(
                recommendation="withhold",
                exemptions=[
                    ExemptionFinding(
                        section="s40",
                        kind="absolute",
                        applies=True,
                        rationale="personal data",
                        citations=[],
                    )
                ],
                grounded=False,
            ),  # item 1: s40 predicted, s40 gold → exact match
            ComplianceResult(
                recommendation="withhold",
                exemptions=[
                    ExemptionFinding(
                        section="s40",
                        kind="absolute",
                        applies=True,
                        rationale="personal data",
                        citations=[],
                    )
                ],
                grounded=False,
            ),  # item 2: s40 predicted, s43 gold → wrong
        ]
    )

    monkeypatch.setattr(
        _triage_mod,
        "triage_agent",
        lambda case, cost, **kw: _SIMPLE_TRIAGE,
    )
    monkeypatch.setattr(
        _compliance_mod,
        "compliance_agent",
        lambda case, cost, **kw: next(results_q),
    )

    metrics = run_eval(gold_path, retrieval_fn=lambda _: [])

    assert metrics["accuracy"] == 0.5, f"expected 0.5, got {metrics['accuracy']}"
    assert metrics["recall"] == 0.5, f"expected 0.5 (item1=1.0 item2=0.0), got {metrics['recall']}"
    assert metrics["false_positive_rate"] > 0.0, (
        f"expected false_positive_rate > 0.0, got {metrics['false_positive_rate']}"
    )
    assert metrics["n_requests"] == 2


# ---------------------------------------------------------------------------
# Test 2 — gate must NEVER be called
# ---------------------------------------------------------------------------


def test_eval_runs_without_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    items = [{**_GOLD_TEMPLATE, "id": "g1"}]
    gold_path = _make_gold_file(tmp_path, items)

    gate_called: dict[str, int] = {"n": 0}

    def _gate_spy(*a, **kw):  # type: ignore[no-untyped-def]
        gate_called["n"] += 1
        raise AssertionError("gate was called!")

    monkeypatch.setattr("foi_system.hitl.approval_gate", _gate_spy)

    monkeypatch.setattr(
        _triage_mod,
        "triage_agent",
        lambda case, cost, **kw: _SIMPLE_TRIAGE,
    )
    monkeypatch.setattr(
        _compliance_mod,
        "compliance_agent",
        lambda case, cost, **kw: ComplianceResult(
            recommendation="withhold",
            exemptions=[],
            grounded=True,
        ),
    )

    result = run_eval(gold_path, retrieval_fn=lambda _: [])

    assert gate_called["n"] == 0, "approval_gate must never be called by run_eval"
    required_keys = {
        "accuracy",
        "recall",
        "false_positive_rate",
        "citation_grounding_passrate",
        "n_requests",
    }
    assert required_keys == set(result.keys())


# ---------------------------------------------------------------------------
# Test 3 — citation grounding pass-rate
# ---------------------------------------------------------------------------


def test_citation_grounding_passrate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {**_GOLD_TEMPLATE, "id": "c1", "exemption_sections": ["s40"]},
        {**_GOLD_TEMPLATE, "id": "c2", "exemption_sections": ["s40"]},
    ]
    gold_path = _make_gold_file(tmp_path, items)

    # A retrieved chunk whose text contains the exact quote we'll use for item 1.
    chunk = RetrievedChunk(
        text="Personal data must not be released under section 40.",
        source="policy.txt",
        section="s40",
        chunk_index=0,
        distance=0.1,
    )

    results_q = iter(
        [
            # item 1: citation grounded — chunk IS in retrieved and quote is verbatim
            ComplianceResult(
                recommendation="withhold",
                exemptions=[
                    ExemptionFinding(
                        section="s40",
                        kind="absolute",
                        applies=True,
                        rationale="personal data",
                        citations=[
                            Citation(
                                section="s40",
                                quote="Personal data must not be released under section 40.",
                                source="policy.txt",
                                chunk_index=0,
                            )
                        ],
                    )
                ],
                grounded=True,
            ),
            # item 2: citation NOT grounded — references a chunk not in retrieved
            ComplianceResult(
                recommendation="withhold",
                exemptions=[
                    ExemptionFinding(
                        section="s40",
                        kind="absolute",
                        applies=True,
                        rationale="personal data",
                        citations=[
                            Citation(
                                section="s40",
                                quote="some quote",
                                source="missing_policy.txt",
                                chunk_index=99,
                            )
                        ],
                    )
                ],
                grounded=False,
            ),
        ]
    )

    monkeypatch.setattr(
        _triage_mod,
        "triage_agent",
        lambda case, cost, **kw: _SIMPLE_TRIAGE,
    )
    monkeypatch.setattr(
        _compliance_mod,
        "compliance_agent",
        lambda case, cost, **kw: next(results_q),
    )

    def _retrieval_fn(text: str) -> list[RetrievedChunk]:
        return [chunk]

    metrics = run_eval(gold_path, retrieval_fn=_retrieval_fn)

    assert metrics["citation_grounding_passrate"] == 0.5, (
        f"expected 0.5, got {metrics['citation_grounding_passrate']}"
    )


# ---------------------------------------------------------------------------
# Test 4 — held-out set processes end-to-end
# ---------------------------------------------------------------------------


def test_held_out_set_processes_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    items = [
        {
            "id": "h1",
            "request": "Please release the procurement contracts.",
            "topic": "procurement_commercial",
            "complexity": "medium",
            "recommendation": "withhold",
            "exemption_sections": ["s43"],
        },
        {
            "id": "h2",
            "request": "I want to see the staff performance reviews.",
            "topic": "staffing_hr",
            "complexity": "low",
            "recommendation": "withhold",
            "exemption_sections": ["s40"],
        },
        {
            "id": "h3",
            "request": "Can you share the budget breakdown?",
            "topic": "finance_spending",
            "complexity": "medium",
            "recommendation": "release",
            "exemption_sections": [],
        },
    ]
    held_out_path = tmp_path / "held_out_tmp.jsonl"
    held_out_path.write_text("\n".join(json.dumps(item) for item in items) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        _triage_mod,
        "triage_agent",
        lambda case, cost, **kw: TriageResult(
            topic="other",
            complexity="low",
            summary="test",
            confidence=0.8,
        ),
    )
    monkeypatch.setattr(
        _compliance_mod,
        "compliance_agent",
        lambda case, cost, **kw: ComplianceResult(
            recommendation="withhold",
            exemptions=[],
            grounded=True,
        ),
    )

    result = run_eval(str(held_out_path), retrieval_fn=lambda _: [])

    required_keys = {
        "accuracy",
        "recall",
        "false_positive_rate",
        "citation_grounding_passrate",
        "n_requests",
    }
    missing = required_keys - set(result.keys())
    assert required_keys == set(result.keys()), f"missing keys: {missing}"
    assert result["n_requests"] >= 2
