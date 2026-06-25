"""Human-in-the-loop (HITL) approval gate for the FOI multi-agent CLI.

No FOI response is released without an operator's approve / reject / modify
decision.  The gate renders the case to a Rich console, prompts the operator,
mutates ``case.decision`` / ``case.status``, writes one audit entry, and
returns the ``HumanDecision``.

Usage::

    from foi_system.hitl import approval_gate
    decision = approval_gate(case, operator="Officer Smith")
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import foi_system.audit as audit
from foi_system.audit import DEFAULT_JSONL_PATH, DEFAULT_TXT_PATH
from foi_system.models import (
    CaseRecord,
    HumanDecision,
    Modification,
)

__all__ = ["approval_gate"]


# ---------------------------------------------------------------------------
# Internal rendering helper
# ---------------------------------------------------------------------------


def _render_gate(
    case: CaseRecord,
    console: Console,
    low_confidence_threshold: float,
) -> None:
    """Render all case panels to *console* in decision-centred order.

    Order:
    1. RECOMMENDATION headline (MUST be first so idx < first distance:)
    2. Triage block (with optional LOW CONFIDENCE and CLARIFICATION banners)
    3. Third-party notification banner (when flagged)
    4. Exemption findings table
    5. Retrieved evidence chunks (up to 5)
    6. AI-GENERATED DRAFT panel
    """

    # ── 1. RECOMMENDATION HEADLINE ─────────────────────────────────────────
    rec_value = (
        case.compliance.recommendation.upper() if case.compliance is not None else "WITHHOLD"
    )
    console.print(
        Panel(
            f"[bold]RECOMMENDATION: {rec_value}[/bold]",
            title="[bold yellow]OPERATOR DECISION REQUIRED[/bold yellow]",
            border_style="yellow",
        )
    )

    # ── 2. TRIAGE ──────────────────────────────────────────────────────────
    if case.triage is not None:
        triage = case.triage
        triage_lines: list[str] = [
            f"topic: {triage.topic}",
            f"complexity: {triage.complexity}",
            f"confidence: {triage.confidence:.2f}",
        ]
        triage_text = "\n".join(triage_lines)

        if triage.confidence < low_confidence_threshold:
            triage_text += (
                "\n\n[bold red]LOW CONFIDENCE — manual review strongly advised[/bold red]"
            )

        if triage.clarification_recommended:
            reason = triage.clarification_reason or "ambiguous request"
            triage_text += f"\n\n[bold orange3]CLARIFICATION RECOMMENDED: {reason}[/bold orange3]"

        console.print(Panel(triage_text, title="Triage", border_style="blue"))

    # ── 3. THIRD-PARTY NOTIFICATION BANNER ────────────────────────────────
    if case.compliance is not None and case.compliance.third_party_notification_required:
        console.print(
            Panel(
                "[bold red]THIRD-PARTY NOTIFICATION MAY BE REQUIRED (s41 / s40(2))[/bold red]",
                border_style="red",
            )
        )

    # ── 4. EXEMPTION FINDINGS ──────────────────────────────────────────────
    if case.compliance is not None and case.compliance.exemptions:
        table = Table(title="Exemption Findings", show_lines=True)
        table.add_column("Section", style="cyan")
        table.add_column("Kind")
        table.add_column("Rationale")
        table.add_column("Quote")
        table.add_column("Public Interest Test")

        for finding in case.compliance.exemptions:
            quote_text = ""
            if finding.citations:
                quote_text = finding.citations[0].quote
            pit = finding.public_interest_test or ""
            table.add_row(
                finding.section,
                finding.kind,
                finding.rationale,
                quote_text,
                pit,
            )

        console.print(table)

    # ── 5. RETRIEVED CHUNKS (up to 5) ─────────────────────────────────────
    chunks = case.retrieved[:5]
    if chunks:
        chunk_lines: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            dist_label = f"distance: {chunk.distance:.2f} (lower = closer)"
            chunk_lines.append(f"[{i}] {chunk.source} §{chunk.section or '?'} — {dist_label}")
            chunk_lines.append(f"    {chunk.text[:200]}")

        console.print(
            Panel(
                "\n".join(chunk_lines),
                title="Retrieved Evidence",
                border_style="green",
            )
        )

    # ── 6. AI-GENERATED DRAFT ──────────────────────────────────────────────
    if case.redaction is not None:
        draft_text = case.redaction.redacted_draft
    elif case.response is not None:
        draft_text = case.response.letter
    else:
        draft_text = "[no draft available]"

    console.print(Panel(draft_text, title="AI-GENERATED DRAFT", border_style="magenta"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def approval_gate(
    case: CaseRecord,
    operator: str,
    *,
    console: Optional[Console] = None,
    input_fn: Callable[[str], str] = input,
    audit_jsonl_path: str | Path = DEFAULT_JSONL_PATH,
    audit_txt_path: str | Path = DEFAULT_TXT_PATH,
    low_confidence_threshold: float = 0.5,
) -> HumanDecision:
    """Decision-centred terminal gate.

    Renders the case, prompts the operator, mutates ``case.decision``/
    ``case.status``, writes one audit entry, returns the ``HumanDecision``.

    Args:
        case:                    The ``CaseRecord`` being reviewed.
        operator:                Non-empty string identifying the human operator.
                                 Hard-fails with ``ValueError`` if empty/whitespace.
        console:                 Rich ``Console`` to render to. Defaults to a new
                                 console writing to stdout.
        input_fn:                Callable used for all operator prompts. Defaults
                                 to the built-in ``input``.
        audit_jsonl_path:        Path for the JSONL audit file.
        audit_txt_path:          Path for the human-readable audit file.
        low_confidence_threshold: Triage confidence below this value triggers a
                                 LOW CONFIDENCE banner.

    Returns:
        The completed ``HumanDecision`` (also stored on ``case.decision``).

    Raises:
        ValueError: If *operator* is empty or whitespace-only.
    """

    # ── Hard-fail on empty operator BEFORE any rendering ──────────────────
    if not operator.strip():
        raise ValueError("operator identity is required")

    # ── Use a default console when none is injected ────────────────────────
    if console is None:
        console = Console()

    # ── Render the case ────────────────────────────────────────────────────
    _render_gate(case, console, low_confidence_threshold)

    # ── Determine the displayed draft (needed for 'modify') ────────────────
    if case.redaction is not None:
        displayed_draft = case.redaction.redacted_draft
    elif case.response is not None:
        displayed_draft = case.response.letter
    else:
        displayed_draft = "[no draft available]"

    # ── Prompt loop ────────────────────────────────────────────────────────
    decision_str: Optional[Literal["approve", "reject", "modify"]] = None
    notes: str = ""
    rejection_reason: Optional[str] = None
    modification: Optional[Modification] = None

    while True:
        raw = input_fn("[a]pprove / [r]eject / [m]odify: ").strip().lower()
        if not raw:
            continue
        first = raw[0]
        if first == "a":
            decision_str = "approve"
            notes = input_fn("Notes (optional): ")
            break
        elif first == "r":
            decision_str = "reject"
            while True:
                reason = input_fn("Reason: ").strip()
                if reason:
                    rejection_reason = reason
                    break
            break
        elif first == "m":
            decision_str = "modify"
            after = input_fn("Enter the revised letter (single line for tests): ")
            modification = Modification(before=displayed_draft, after=after)
            break
        # Any other input → re-prompt

    assert decision_str is not None  # loop only exits via break with a valid value

    # ── Compute evidence_refs ──────────────────────────────────────────────
    evidence_refs = [f"{c.source}#{c.chunk_index}" for c in case.retrieved]

    # ── Determine original_recommendation ─────────────────────────────────
    original_recommendation = (
        case.compliance.recommendation if case.compliance is not None else "withhold"
    )

    # ── Build the timestamp (same format as audit.make_entry) ─────────────
    timestamp = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    # ── Build the HumanDecision ────────────────────────────────────────────
    human_decision = HumanDecision(
        decision=decision_str,
        operator=operator,
        timestamp=timestamp,
        notes=notes,
        original_recommendation=original_recommendation,
        modification=modification,
        rejection_reason=rejection_reason,
        evidence_refs=evidence_refs,
    )

    # ── Mutate the case ────────────────────────────────────────────────────
    case.decision = human_decision
    if decision_str == "reject":
        case.status = "rejected"
    # approve / modify: leave case.status for the supervisor

    # ── Audit: exactly ONE decision entry ─────────────────────────────────
    payload: dict = {
        "decision": decision_str,
        "original_recommendation": original_recommendation,
        "evidence_refs": evidence_refs,
    }
    if notes:
        payload["notes"] = notes
    if rejection_reason is not None:
        payload["rejection_reason"] = rejection_reason
    if modification is not None:
        payload["modification"] = {
            "before": modification.before,
            "after": modification.after,
        }

    audit.log_event(
        audit.make_entry(
            "decision",
            case.request_id,
            agent=None,
            operator=operator,
            payload=payload,
        ),
        jsonl_path=audit_jsonl_path,
        txt_path=audit_txt_path,
    )

    return human_decision
