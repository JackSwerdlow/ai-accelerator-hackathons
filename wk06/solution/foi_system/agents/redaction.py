"""Hybrid redaction agent for the FOI multi-agent system.

Two-pass redaction:
1. Deterministic regex pass — always applied, even if the model fails.
2. Haiku model pass — masks names/job-titles/contextual PII the regex can't catch.

On ANY model error → fail safe: keep regex redactions, flag needs_mandatory_review=True,
redaction_complete=False, prepend manual-review banner. Never return silently-unredacted text.
"""

import re
from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from foi_system.cost import CostTracker
from foi_system.llm import build_llm, structured
from foi_system.models import CaseRecord, RedactionItem, RedactionResult

# ---------------------------------------------------------------------------
# Verified regexes (confirmed against synthetic PII — do not modify)
# ---------------------------------------------------------------------------
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?:\+44\s?\d{1,4}|\b0\d{2,4})[\s-]?\d{3,4}[\s-]?\d{2,4}\b")
_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b")
_STAFF = re.compile(
    r"\b(?:(?:staff|employee|personnel)\s*(?:no\.?|number|id|#)?\s*[:#-]?\s*\d{4,})"
    r"|(?:SN|EMP)\d{4,}\b",
    re.IGNORECASE,
)

_PATTERNS = [
    ("email", _EMAIL),
    ("phone", _PHONE),
    ("postcode", _POSTCODE),
    ("staff_number", _STAFF),
]

_SYSTEM = (
    "You are an FOI redaction officer. The draft below has had emails, phone numbers, postcodes "
    "and staff numbers already masked as [REDACTED-...]. Mask any REMAINING personal data of "
    "identifiable individuals (names, job titles that identify a person, signatures, contextual "
    "identifiers) by replacing each with a [REDACTED-<category>] marker. Do NOT unmask existing "
    "[REDACTED-...] markers and do not alter non-personal content. Produce a redaction schedule "
    "(one item per redaction: category, exemption_section usually 's40', reason). If you are at "
    "all uncertain that you caught every piece of personal data, set needs_mandatory_review=true."
)


def redact_with_regex(text: str) -> tuple[str, list[RedactionItem]]:
    """Apply deterministic regex redactions and return (redacted_text, items).

    Uses the closure default-arg trick (_c=category) to avoid late-binding loop bug.
    """
    items: list[RedactionItem] = []
    redacted = text
    for category, pattern in _PATTERNS:

        def _sub(m: "re.Match[str]", _c: str = category) -> str:
            items.append(
                RedactionItem(
                    category=_c,
                    exemption_section="s40",
                    reason=f"personal data ({_c}) masked under s40",
                )
            )
            return f"[REDACTED-{_c}]"

        redacted = pattern.sub(_sub, redacted)
    return redacted, items


def redaction_agent(
    case: CaseRecord, cost: CostTracker, *, llm: Runnable | None = None
) -> RedactionResult:
    """Hybrid redaction: deterministic regex pass + Haiku model pass.

    Args:
        case: The FOI case record. Reads case.response.letter (empty string if None).
        cost: CostTracker to record LLM usage.
        llm: Optional structured Runnable returning RedactionResult.
             Defaults to structured(build_llm("redaction"), RedactionResult).
             Inject a RunnableLambda in tests to avoid network calls.

    Returns:
        RedactionResult with merged redacted_draft and schedule.
        On model failure: fail-safe result with regex redactions preserved,
        needs_mandatory_review=True, redaction_complete=False.
    """
    draft = case.response.letter if case.response is not None else ""
    redacted, regex_items = redact_with_regex(draft)

    runnable: Runnable = (
        llm if llm is not None else structured(build_llm("redaction"), RedactionResult)
    )
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"DRAFT (mask remaining personal data):\n{redacted}"),
    ]

    try:
        with cost.track("redaction"):
            model_result = cast(RedactionResult, runnable.invoke(messages))
    except Exception:
        # Fail safe: keep regex redactions, flag for mandatory review.
        # NEVER return silently-unredacted text.
        return RedactionResult(
            redacted_draft="[MANUAL REDACTION REQUIRED — automated redaction failed]\n" + redacted,
            schedule=regex_items,
            redaction_complete=False,
            needs_mandatory_review=True,
        )

    needs_review = model_result.needs_mandatory_review
    return RedactionResult(
        redacted_draft=model_result.redacted_draft,
        schedule=regex_items + model_result.schedule,
        redaction_complete=model_result.redaction_complete and not needs_review,
        needs_mandatory_review=needs_review,
    )
