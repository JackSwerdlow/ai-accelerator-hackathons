"""Supervisor for the FOI multi-agent system.

Orchestrates the full pipeline for one FOI request:
  triage → retrieve → compliance → response → redaction → gate

Five-layer defence — each LLM stage is wrapped in try/except:
- Appends to case.errors
- Logs an audit error entry
- Applies a typed fallback
- Records the failure in the CircuitBreaker
- Continues (never re-raises, except KeyboardInterrupt at the gate)

DI seams: when a ``*_llm`` kwarg is provided (e.g. in tests), the supervisor
invokes that callable directly instead of calling the full agent function.
This allows injecting a RunnableLambda so errors propagate to the supervisor's
try/except layer.  When ``*_llm=None`` (production), the supervisor calls the
full agent function which has its own robust internal fallbacks.

The CircuitBreaker skips a stage entirely once it has reached the failure
threshold, using the typed fallback directly without invoking the agent.

``process_folder`` processes all *.txt files in a folder with per-request
isolation and a Rich live progress display.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from rich.live import Live

import foi_system.audit as audit
import foi_system.retrieval as retrieval
from foi_system.agents.compliance import compliance_agent
from foi_system.agents.redaction import redaction_agent
from foi_system.agents.response import response_agent
from foi_system.agents.triage import triage_agent
from foi_system.config import CIRCUIT_BREAKER_THRESHOLD
from foi_system.cost import CostTracker
from foi_system.hitl import approval_gate
from foi_system.models import (
    CaseRecord,
    ComplianceResult,
    HumanDecision,
    RedactionResult,
    ResponseDraft,
    TriageResult,
)

__all__ = ["CircuitBreaker", "process_request", "process_folder"]

# ---------------------------------------------------------------------------
# Typed fallbacks (PLAN §4 table — exact objects)
# ---------------------------------------------------------------------------


def _triage_fallback() -> TriageResult:
    return TriageResult(
        topic="other",
        complexity="high",
        summary="classification failed — manual review",
        confidence=0.0,
        clarification_recommended=True,
    )


def _compliance_fallback() -> ComplianceResult:
    return ComplianceResult(
        exemptions=[],
        recommendation="withhold",
        grounded=False,
        notes="compliance analysis failed — manual exemption review required",
    )


def _response_fallback() -> ResponseDraft:
    return ResponseDraft(
        letter="[DRAFT GENERATION FAILED — officer must draft manually]",
        evidence_summary="see classification + compliance",
        exemptions_cited=[],
    )


def _redaction_fallback(case: CaseRecord) -> RedactionResult:
    from foi_system.agents.redaction import redact_with_regex

    draft = case.response.letter if case.response is not None else ""
    redacted, items = redact_with_regex(draft)
    return RedactionResult(
        redacted_draft="[MANUAL REDACTION REQUIRED — automated redaction failed]\n" + redacted,
        schedule=items,
        redaction_complete=False,
        needs_mandatory_review=True,
    )


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """Counts post-retry failures per stage; marks a stage degraded at threshold."""

    def __init__(self, threshold: int = CIRCUIT_BREAKER_THRESHOLD) -> None:
        self._failures: dict[str, int] = {}
        self._degraded: set[str] = set()
        self.threshold = threshold

    def is_degraded(self, stage: str) -> bool:
        return stage in self._degraded

    def record_failure(self, stage: str) -> None:
        """Count ONE post-retry failure for this stage. Mark degraded at threshold."""
        self._failures[stage] = self._failures.get(stage, 0) + 1
        if self._failures[stage] >= self.threshold:
            self._degraded.add(stage)

    def reset(self, stage: str) -> None:
        self._failures.pop(stage, None)
        self._degraded.discard(stage)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _log_error(
    case: CaseRecord,
    stage: str,
    exc: Exception,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
) -> None:
    """Append error to case and write an audit error entry."""
    error_msg = f"{stage} failed: {exc!r}"
    case.errors.append(error_msg)
    entry = audit.make_entry(
        "error",
        case.request_id,
        payload={"stage": stage, "error": error_msg},
    )
    _log(entry, audit_jsonl_path, audit_txt_path)


def _log_degraded(
    case: CaseRecord,
    stage: str,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
) -> None:
    """Log a WARNING-level audit event when a stage is skipped due to circuit breaker."""
    entry = audit.make_entry(
        "degraded",
        case.request_id,
        payload={"stage": stage, "reason": "circuit breaker open"},
    )
    _log(entry, audit_jsonl_path, audit_txt_path)


def _log(
    entry: audit.AuditEntry,
    jsonl_path: Optional[str | Path],
    txt_path: Optional[str | Path],
) -> None:
    kwargs: dict = {}
    if jsonl_path is not None:
        kwargs["jsonl_path"] = jsonl_path
    if txt_path is not None:
        kwargs["txt_path"] = txt_path
    audit.log_event(entry, **kwargs)


def _write_result(case: CaseRecord, results_dir: str | Path) -> None:
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    (results_path / f"{case.request_id}.json").write_text(
        case.model_dump_json(indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Stage runners — invoke the LLM directly when the DI seam is provided,
# otherwise delegate to the full agent function (production path).
# ---------------------------------------------------------------------------


def _run_triage(
    case: CaseRecord,
    cost: CostTracker,
    llm: Any,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
    breaker: "CircuitBreaker",
) -> None:
    """Triage stage with five-layer defence."""
    ajp = audit_jsonl_path
    atp = audit_txt_path
    if breaker.is_degraded("triage"):
        _log_degraded(case, "triage", audit_jsonl_path=ajp, audit_txt_path=atp)
        case.triage = _triage_fallback()
        return

    if llm is not None:
        # DI path: invoke the llm directly so errors propagate here
        try:
            _messages = [
                SystemMessage(content="triage"),
                HumanMessage(content=case.request_text),
            ]
            with cost.track("triage"):
                result = llm.invoke(_messages)
            case.triage = result
            _log(
                audit.make_entry(
                    "triage",
                    case.request_id,
                    payload={
                        "topic": case.triage.topic,
                        "complexity": case.triage.complexity,
                        "confidence": case.triage.confidence,
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "triage", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.triage = _triage_fallback()
            breaker.record_failure("triage")
    else:
        # Production path: call the full agent (has its own robust fallbacks)
        try:
            case.triage = triage_agent(case, cost, llm=None)
            _log(
                audit.make_entry(
                    "triage",
                    case.request_id,
                    payload={
                        "topic": case.triage.topic,
                        "complexity": case.triage.complexity,
                        "confidence": case.triage.confidence,
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "triage", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.triage = _triage_fallback()
            breaker.record_failure("triage")


def _run_compliance(
    case: CaseRecord,
    cost: CostTracker,
    llm: Any,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
    breaker: "CircuitBreaker",
) -> None:
    """Compliance stage with five-layer defence."""
    ajp = audit_jsonl_path
    atp = audit_txt_path
    if breaker.is_degraded("compliance"):
        _log_degraded(case, "compliance", audit_jsonl_path=ajp, audit_txt_path=atp)
        case.compliance = _compliance_fallback()
        return

    if llm is not None:
        # DI path: invoke the llm directly so errors propagate here
        try:
            _messages = [
                SystemMessage(content="compliance"),
                HumanMessage(content=case.request_text),
            ]
            with cost.track("compliance"):
                result = llm.invoke(_messages)
            case.compliance = result
            _log(
                audit.make_entry(
                    "compliance",
                    case.request_id,
                    payload={
                        "recommendation": case.compliance.recommendation,
                        "grounded": case.compliance.grounded,
                        "exemption_count": len(case.compliance.exemptions),
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "compliance", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.compliance = _compliance_fallback()
            breaker.record_failure("compliance")
    else:
        # Production path: call the full agent
        try:
            case.compliance = compliance_agent(case, cost, llm=None)
            _log(
                audit.make_entry(
                    "compliance",
                    case.request_id,
                    payload={
                        "recommendation": case.compliance.recommendation,
                        "grounded": case.compliance.grounded,
                        "exemption_count": len(case.compliance.exemptions),
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "compliance", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.compliance = _compliance_fallback()
            breaker.record_failure("compliance")


def _run_response(
    case: CaseRecord,
    cost: CostTracker,
    llm: Any,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
    breaker: "CircuitBreaker",
) -> None:
    """Response stage with five-layer defence."""
    ajp = audit_jsonl_path
    atp = audit_txt_path
    if breaker.is_degraded("response"):
        _log_degraded(case, "response", audit_jsonl_path=ajp, audit_txt_path=atp)
        case.response = _response_fallback()
        return

    if llm is not None:
        # DI path: invoke the llm directly so errors propagate here
        try:
            _messages = [
                SystemMessage(content="response"),
                HumanMessage(content=case.request_text),
            ]
            with cost.track("response"):
                result = llm.invoke(_messages)
            case.response = result
            _log(
                audit.make_entry(
                    "response",
                    case.request_id,
                    payload={
                        "exemptions_cited": case.response.exemptions_cited,
                        "letter_length": len(case.response.letter),
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "response", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.response = _response_fallback()
            breaker.record_failure("response")
    else:
        # Production path: call the full agent
        try:
            case.response = response_agent(case, cost, llm=None)
            _log(
                audit.make_entry(
                    "response",
                    case.request_id,
                    payload={
                        "exemptions_cited": case.response.exemptions_cited,
                        "letter_length": len(case.response.letter),
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "response", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.response = _response_fallback()
            breaker.record_failure("response")


def _run_redaction(
    case: CaseRecord,
    cost: CostTracker,
    llm: Any,
    *,
    audit_jsonl_path: Optional[str | Path],
    audit_txt_path: Optional[str | Path],
    breaker: "CircuitBreaker",
) -> None:
    """Redaction stage with five-layer defence."""
    ajp = audit_jsonl_path
    atp = audit_txt_path
    if breaker.is_degraded("redaction"):
        _log_degraded(case, "redaction", audit_jsonl_path=ajp, audit_txt_path=atp)
        case.redaction = _redaction_fallback(case)
        return

    if llm is not None:
        # DI path: invoke the llm directly so errors propagate here
        try:
            _messages = [
                SystemMessage(content="redaction"),
                HumanMessage(content=case.request_text),
            ]
            with cost.track("redaction"):
                result = llm.invoke(_messages)
            case.redaction = result
            _log(
                audit.make_entry(
                    "redaction",
                    case.request_id,
                    payload={
                        "redaction_complete": case.redaction.redaction_complete,
                        "needs_mandatory_review": case.redaction.needs_mandatory_review,
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "redaction", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.redaction = _redaction_fallback(case)
            breaker.record_failure("redaction")
    else:
        # Production path: call the full agent
        try:
            case.redaction = redaction_agent(case, cost, llm=None)
            _log(
                audit.make_entry(
                    "redaction",
                    case.request_id,
                    payload={
                        "redaction_complete": case.redaction.redaction_complete,
                        "needs_mandatory_review": case.redaction.needs_mandatory_review,
                    },
                ),
                ajp,
                atp,
            )
        except Exception as exc:
            _log_error(case, "redaction", exc, audit_jsonl_path=ajp, audit_txt_path=atp)
            case.redaction = _redaction_fallback(case)
            breaker.record_failure("redaction")


# ---------------------------------------------------------------------------
# Public API: process_request
# ---------------------------------------------------------------------------


def process_request(
    request_path: str | Path,
    operator: str,
    cost: CostTracker,
    breaker: "CircuitBreaker",
    *,
    triage_llm: Any = None,
    compliance_llm: Any = None,
    response_llm: Any = None,
    redaction_llm: Any = None,
    gate_fn: Optional[Callable[[CaseRecord, str], HumanDecision]] = None,
    results_dir: str | Path = "./output/results",
    audit_jsonl_path: Optional[str | Path] = None,
    audit_txt_path: Optional[str | Path] = None,
) -> CaseRecord:
    """Run the full pipeline for one request file. Returns the final CaseRecord.

    Always writes output/results/<request_id>.json even on error/reject.
    Always returns a CaseRecord regardless of failures.
    """
    request_path = Path(request_path)
    request_id = request_path.stem

    # Wrap read so even an unreadable file produces a result JSON.
    try:
        request_text = request_path.read_text(encoding="utf-8")
    except Exception as exc:
        case = CaseRecord(
            request_id=request_id,
            request_file=request_path.name,
            request_text="",
            status="error",
            errors=[f"read failed: {exc!r}"],
        )
        _write_result(case, results_dir)
        return case

    case = CaseRecord(
        request_id=request_id,
        request_file=request_path.name,
        request_text=request_text,
    )

    _cost_start_idx = len(cost.entries)

    _log_kwargs = dict(audit_jsonl_path=audit_jsonl_path, audit_txt_path=audit_txt_path)

    # ── Stage 1: Triage ───────────────────────────────────────────────────
    _run_triage(case, cost, triage_llm, breaker=breaker, **_log_kwargs)  # type: ignore[arg-type]

    # ── Stage 2: Retrieve ─────────────────────────────────────────────────
    try:
        case.retrieved = retrieval.search_policies(case.request_text)
    except Exception:
        case.retrieved = []
        case.errors.append("retrieval failed: no policy context")

    # ── Stage 3: Compliance ───────────────────────────────────────────────
    _run_compliance(case, cost, compliance_llm, breaker=breaker, **_log_kwargs)  # type: ignore[arg-type]

    # ── Stage 4: Response ─────────────────────────────────────────────────
    _run_response(case, cost, response_llm, breaker=breaker, **_log_kwargs)  # type: ignore[arg-type]

    # ── Stage 5: Redaction ────────────────────────────────────────────────
    _run_redaction(case, cost, redaction_llm, breaker=breaker, **_log_kwargs)  # type: ignore[arg-type]

    # ── Stage 6: Gate ─────────────────────────────────────────────────────
    try:
        _gate = gate_fn if gate_fn is not None else approval_gate
        decision: HumanDecision = _gate(case, operator)
        case.decision = decision

        # Apply modification — update both response and the displayed redacted draft
        if decision.decision == "modify" and decision.modification is not None:
            if case.response is not None:
                case.response.letter = decision.modification.after
            if case.redaction is not None:
                case.redaction.redacted_draft = decision.modification.after

    except KeyboardInterrupt:
        # Must propagate
        _write_result(case, results_dir)
        raise
    except Exception as exc:
        error_msg = f"gate failed: {exc!r}"
        case.errors.append(error_msg)
        _log(
            audit.make_entry(
                "error",
                request_id,
                payload={"stage": "gate", "error": error_msg},
            ),
            audit_jsonl_path,
            audit_txt_path,
        )
        case.status = "error"
        _write_result(case, results_dir)
        return case

    # ── Finalise ──────────────────────────────────────────────────────────
    if case.status != "rejected":
        case.status = "processed"

    # ── Cost summary audit entry ──────────────────────────────────────────
    # Compute cost for THIS request only (not cumulative batch total)
    _request_entries = cost.entries[_cost_start_idx:]
    _request_total = sum(e.cost_usd for e in _request_entries)
    _request_per_agent: dict[str, float] = {}
    for e in _request_entries:
        _request_per_agent[e.agent] = _request_per_agent.get(e.agent, 0.0) + e.cost_usd

    _log(
        audit.make_entry(
            "cost_summary",
            request_id,
            payload={
                "total_usd": _request_total,
                "per_agent": _request_per_agent,
            },
        ),
        audit_jsonl_path,
        audit_txt_path,
    )

    # ── Write result JSON ─────────────────────────────────────────────────
    _write_result(case, results_dir)

    return case


# ---------------------------------------------------------------------------
# Public API: process_folder
# ---------------------------------------------------------------------------


def process_folder(
    folder: str | Path,
    operator: str,
    *,
    results_dir: str | Path = "./output/results",
    audit_jsonl_path: Optional[str | Path] = None,
    audit_txt_path: Optional[str | Path] = None,
) -> list[CaseRecord]:
    """Process all *.txt files in folder.

    Per-request isolation: one file's exception never aborts the rest.
    Rich live progress per request + end-of-run cost summary printed to stdout.
    """
    files = sorted(Path(folder).glob("*.txt"))
    tracker = CostTracker()
    breaker = CircuitBreaker()
    results: list[CaseRecord] = []

    with Live(refresh_per_second=4) as live:
        for i, path in enumerate(files, 1):
            live.update(f"[{i}/{len(files)}] Processing {path.name}…")
            try:
                case = process_request(
                    str(path),
                    operator,
                    tracker,
                    breaker,
                    results_dir=results_dir,
                    audit_jsonl_path=audit_jsonl_path,
                    audit_txt_path=audit_txt_path,
                )
            except Exception:
                # Per-request isolation: one bad file never stops the batch
                results.append(
                    CaseRecord(
                        request_id=path.stem,
                        request_file=path.name,
                        request_text="",
                        status="error",
                        errors=["process_request raised unexpected exception"],
                    )
                )
                continue
            results.append(case)

    print(tracker.summary_table())  # end-of-run cost summary to stdout
    return results
