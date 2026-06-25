"""Tests for the redaction agent (Task 8).

All tests are offline — the regex pass is tested directly; the model pass
is tested via injected RunnableLambda (no network, API key, or real model call).
"""

from langchain_core.runnables import Runnable, RunnableLambda

from foi_system.agents.redaction import redact_with_regex, redaction_agent
from foi_system.cost import CostTracker
from foi_system.models import CaseRecord, RedactionItem, RedactionResult, ResponseDraft


def _make_case(letter: str) -> CaseRecord:
    return CaseRecord(
        request_id="r1",
        request_file="f1.txt",
        request_text="test request",
        response=ResponseDraft(
            letter=letter,
            exemptions_cited=[],
            evidence_summary="",
        ),
    )


def test_regex_masks_email_phone_postcode() -> None:
    """redact_with_regex masks emails, phones, postcodes, and staff numbers directly."""
    draft = (
        "Contact jane.doe@dept.gov.uk or call 020 7946 0958. "
        "Our office is at SW1A 2AA. Staff number 84213 handled this."
    )
    redacted, items = redact_with_regex(draft)

    # Markers present
    assert "[REDACTED-email]" in redacted
    assert "[REDACTED-phone]" in redacted
    assert "[REDACTED-postcode]" in redacted
    assert "[REDACTED-staff_number]" in redacted

    # Originals absent
    assert "jane.doe@dept.gov.uk" not in redacted
    assert "020 7946 0958" not in redacted
    assert "SW1A 2AA" not in redacted
    assert "84213" not in redacted

    # Schedule carries s40 for all categories
    categories = {item.category for item in items}
    assert "email" in categories
    assert "phone" in categories
    assert "postcode" in categories
    assert "staff_number" in categories
    for item in items:
        assert item.exemption_section == "s40"


def test_model_pass_masks_named_individual() -> None:
    """Model pass (injected) masks a named individual; schedule gains a name item."""
    letter = "Dear Sir, caseworker John Smith handled your request. Regards."
    case = _make_case(letter)
    cost = CostTracker()

    model_result = RedactionResult(
        redacted_draft="Dear Sir, caseworker [REDACTED-name] handled your request. Regards.",
        schedule=[
            RedactionItem(
                category="name",
                exemption_section="s40",
                reason="named individual",
            )
        ],
        redaction_complete=True,
        needs_mandatory_review=False,
    )
    fake: Runnable = RunnableLambda(lambda _: model_result)

    result = redaction_agent(case, cost, llm=fake)

    assert "[REDACTED-name]" in result.redacted_draft
    assert "John Smith" not in result.redacted_draft
    categories = {item.category for item in result.schedule}
    assert "name" in categories


def test_produces_schedule_with_exemption() -> None:
    """Every item in the merged schedule has category, reason, and exemption_section set."""
    letter = (
        "Contact jane.doe@dept.gov.uk. Caseworker John Smith (staff number 84213) "
        "at SW1A 2AA handled this."
    )
    case = _make_case(letter)
    cost = CostTracker()

    model_result = RedactionResult(
        redacted_draft="Contact [REDACTED-email]. Caseworker [REDACTED-name] "
        "([REDACTED-staff_number]) at [REDACTED-postcode] handled this.",
        schedule=[
            RedactionItem(
                category="name",
                exemption_section="s40",
                reason="named individual",
            )
        ],
        redaction_complete=True,
        needs_mandatory_review=False,
    )
    fake: Runnable = RunnableLambda(lambda _: model_result)

    result = redaction_agent(case, cost, llm=fake)

    assert len(result.schedule) > 0
    for item in result.schedule:
        assert item.category != ""
        assert item.reason != ""
        assert item.exemption_section != ""
        assert item.exemption_section == "s40"


def test_failure_sets_needs_mandatory_review() -> None:
    """On model exception: needs_mandatory_review=True, redaction_complete=False,
    banner prepended, and regex redactions are still present (fail-safe)."""
    letter = (
        "Contact jane.doe@dept.gov.uk or call 020 7946 0958. Postcode SW1A 2AA. Staff number 84213."
    )
    case = _make_case(letter)
    cost = CostTracker()

    def _raise(_: object) -> RedactionResult:
        raise RuntimeError("model unavailable")

    fake = RunnableLambda(_raise)

    result = redaction_agent(case, cost, llm=fake)

    assert result.needs_mandatory_review is True
    assert result.redaction_complete is False
    assert result.redacted_draft.startswith("[MANUAL REDACTION REQUIRED")

    # Regex redactions are preserved even though model failed
    assert "[REDACTED-email]" in result.redacted_draft
    assert "[REDACTED-phone]" in result.redacted_draft
    assert "[REDACTED-postcode]" in result.redacted_draft
    assert "[REDACTED-staff_number]" in result.redacted_draft

    # Originals absent — PII is NOT silently unredacted
    assert "jane.doe@dept.gov.uk" not in result.redacted_draft
    assert "020 7946 0958" not in result.redacted_draft
    assert "SW1A 2AA" not in result.redacted_draft
    assert "84213" not in result.redacted_draft
