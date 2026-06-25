"""Tests for the response agent (Task 9).

All tests are offline — a RunnableLambda is injected as the structured runnable
(the DI seam) so no network, API key, or real model call is made.
"""

from langchain_core.runnables import RunnableLambda

from foi_system.agents.response import response_agent
from foi_system.cost import CostTracker
from foi_system.models import (
    CaseRecord,
    ComplianceResult,
    ExemptionFinding,
    ResponseDraft,
    TriageResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_case(
    compliance: ComplianceResult | None = None,
    triage: TriageResult | None = None,
) -> CaseRecord:
    case = CaseRecord(
        request_id="r1",
        request_file="f1.txt",
        request_text="Please release information about staff salaries.",
    )
    if compliance is not None:
        case.compliance = compliance
    if triage is not None:
        case.triage = triage
    return case


def _make_triage() -> TriageResult:
    return TriageResult(
        topic="staffing_hr",
        complexity="medium",
        summary="Request for staff salary data.",
        confidence=0.9,
    )


def _make_compliance_s40_s43() -> ComplianceResult:
    """Two applicable exemptions: s40 (absolute) and s43 (qualified with PIT)."""
    return ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s40",
                kind="absolute",
                applies=True,
                rationale="third party personal data",
            ),
            ExemptionFinding(
                section="s43",
                kind="qualified",
                applies=True,
                rationale="commercial interests prejudiced",
                public_interest_test=(
                    "Public interest in transparency is outweighed by harm to third parties."
                ),
            ),
        ],
    )


def _make_compliance_s43_only() -> ComplianceResult:
    """One applicable exemption: s43 only (no s40)."""
    return ComplianceResult(
        recommendation="withhold",
        exemptions=[
            ExemptionFinding(
                section="s43",
                kind="qualified",
                applies=True,
                rationale="commercial interests prejudiced",
                public_interest_test="Transparency outweighed by commercial harm.",
            ),
        ],
    )


def _raise(_):
    raise RuntimeError("simulated LLM failure")


# ---------------------------------------------------------------------------
# Test 1: deterministic post-processing populates exemptions_cited
# ---------------------------------------------------------------------------


def test_letter_cites_exemption_sections():
    """Compliance has s40 + s43 applicable; fake LLM returns empty exemptions_cited.

    Post-processing must union the applicable sections into result.exemptions_cited
    even though the fake model returned [].
    """
    compliance = _make_compliance_s40_s43()
    case = _make_case(compliance=compliance, triage=_make_triage())

    fake_draft = ResponseDraft(
        letter="<letter body>",
        exemptions_cited=[],  # intentionally empty — post-processing must fill this
        evidence_summary="Staff salary data withheld under personal data exemption.",
    )

    result = response_agent(case, CostTracker(), llm=RunnableLambda(lambda _: fake_draft))

    assert "s40" in result.exemptions_cited
    assert "s43" in result.exemptions_cited


# ---------------------------------------------------------------------------
# Test 2: s40 instruction injected when s40 applies; absent when only s43 applies
# ---------------------------------------------------------------------------


def test_s40_instruction_no_named_individuals():
    """When s40 is applicable the S40_INSTRUCTION block must appear in the prompt.

    Also asserts it is ABSENT when the only applicable exemption is s43.
    """
    # --- part A: s40 applies → instruction must be present ---
    compliance_s40 = _make_compliance_s40_s43()
    case_s40 = _make_case(compliance=compliance_s40, triage=_make_triage())

    captured: dict = {}

    def _fake_capture(msgs: list) -> ResponseDraft:
        captured["m"] = msgs
        return ResponseDraft(
            letter="Dear applicant…",
            exemptions_cited=[],
            evidence_summary="withheld",
        )

    response_agent(case_s40, CostTracker(), llm=RunnableLambda(_fake_capture))

    prompt_text = " ".join(str(m.content) for m in captured["m"])
    assert "do not include names, job titles" in prompt_text.lower()
    assert "aggregate" in prompt_text.lower()

    # --- part B: only s43 applies → instruction must NOT be present ---
    compliance_s43 = _make_compliance_s43_only()
    case_s43 = _make_case(compliance=compliance_s43, triage=_make_triage())

    captured_s43: dict = {}

    def _fake_capture_s43(msgs: list) -> ResponseDraft:
        captured_s43["m"] = msgs
        return ResponseDraft(
            letter="Dear applicant…",
            exemptions_cited=[],
            evidence_summary="withheld",
        )

    response_agent(case_s43, CostTracker(), llm=RunnableLambda(_fake_capture_s43))

    prompt_text_s43 = " ".join(str(m.content) for m in captured_s43["m"])
    assert "do not include names, job titles" not in prompt_text_s43.lower()


# ---------------------------------------------------------------------------
# Test 3: fallback holding letter on LLM error
# ---------------------------------------------------------------------------


def test_fallback_holding_letter():
    """When the LLM raises, the agent must return the exact fallback holding letter.

    - letter is exactly the sentinel string
    - evidence_summary is "see classification + compliance"
    - exemptions_cited still lists the applicable sections (deterministic)
    """
    compliance = _make_compliance_s40_s43()
    case = _make_case(compliance=compliance, triage=_make_triage())

    result = response_agent(case, CostTracker(), llm=RunnableLambda(_raise))

    assert result.letter == "[DRAFT GENERATION FAILED — officer must draft manually]"
    assert result.evidence_summary == "see classification + compliance"
    assert "s40" in result.exemptions_cited
    assert "s43" in result.exemptions_cited


# ---------------------------------------------------------------------------
# Test 4: compliance is None → holding letter without LLM call
# ---------------------------------------------------------------------------


def test_no_compliance_returns_holding_letter():
    """When case.compliance is None, return a holding letter without calling the LLM."""
    call_count = {"n": 0}

    def _raise(_):
        call_count["n"] += 1
        raise AssertionError("LLM must not be called when compliance is None")

    case = CaseRecord(request_id="r1", request_file="f1.txt", request_text="Some request.")
    # compliance is None by default on a fresh CaseRecord

    result = response_agent(case, CostTracker(), llm=RunnableLambda(_raise))

    assert call_count["n"] == 0, "LLM should not be called when compliance is missing"
    assert "HOLDING" in result.letter or "pending" in result.letter.lower(), (
        "holding letter should indicate pending/incomplete status"
    )
    assert result.exemptions_cited == []
