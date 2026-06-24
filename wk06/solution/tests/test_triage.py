"""Tests for the triage agent (Task 5).

All tests are offline — a RunnableLambda is injected as the structured runnable
(the DI seam) so no network, API key, or real model call is made.
"""

from langchain_core.runnables import Runnable, RunnableLambda

from foi_system.agents.triage import triage_agent
from foi_system.cost import CostTracker
from foi_system.models import CaseRecord, TriageResult


def _make_case(text: str) -> CaseRecord:
    return CaseRecord(request_id="r1", request_file="f1.txt", request_text=text)


def test_triage_returns_valid_result() -> None:
    """Happy-path: injected runnable returns a TriageResult; agent returns it unchanged."""
    expected = TriageResult(
        topic="procurement_commercial",
        complexity="medium",
        summary="tender records request",
        confidence=0.85,
    )
    fake: Runnable = RunnableLambda(lambda _: expected)
    case = _make_case("Please provide all tender records from 2024.")
    cost = CostTracker()

    result = triage_agent(case, cost, llm=fake)

    assert result.topic == "procurement_commercial"
    assert result.complexity == "medium"
    assert result.confidence == 0.85


def test_triage_fallback_on_error_is_other_high() -> None:
    """When the runnable raises, agent returns typed fallback: other/high/0.0/clarification."""

    def _raise(_: object) -> TriageResult:
        raise RuntimeError("api down")

    fake = RunnableLambda(_raise)
    case = _make_case("Please provide all contracts over £50,000 signed in 2023.")
    cost = CostTracker()

    result = triage_agent(case, cost, llm=fake)

    assert result.topic == "other"
    assert result.complexity == "high"
    assert result.confidence == 0.0
    assert result.clarification_recommended is True


def test_malformed_request_sets_clarification_recommended() -> None:
    """Empty/whitespace request fires the deterministic guard before any model call."""
    case = _make_case("   ")
    cost = CostTracker()

    # No injected llm — guard must fire before any runnable is built/called
    result = triage_agent(case, cost)

    assert result.clarification_recommended is True
    assert result.topic == "other"


def test_triage_emits_confidence() -> None:
    """Confidence field flows through the agent unchanged."""
    fake: Runnable = RunnableLambda(
        lambda _: TriageResult(
            topic="finance_spending",
            complexity="low",
            summary="budget request",
            confidence=0.42,
        )
    )
    case = _make_case("Please provide all budget reports for Q1 2025.")
    cost = CostTracker()

    result = triage_agent(case, cost, llm=fake)

    assert result.confidence == 0.42
