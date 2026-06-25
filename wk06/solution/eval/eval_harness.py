"""Eval harness for the FOI multi-agent system — Task 15.

Runs triage + compliance ONLY (no gate, no response, no redaction) over a
gold JSONL file and reports accuracy, recall, false-positive rate,
citation-grounding pass-rate, and n_requests.
"""

from __future__ import annotations

import json
from typing import Callable

import foi_system.agents.compliance as _compliance_mod
import foi_system.agents.triage as _triage_mod
import foi_system.retrieval as _retrieval
from foi_system.cost import CostTracker
from foi_system.models import CaseRecord, RetrievedChunk
from foi_system.verification import verify_citations


def _do_retrieve(
    text: str, fn: Callable[[str], list[RetrievedChunk]] | None = None
) -> list[RetrievedChunk]:
    """Retrieve policy chunks, falling back to search_policies when fn is None."""
    if fn is not None:
        return fn(text)
    try:
        return _retrieval.search_policies(text)
    except Exception:
        return []


def run_eval(
    gold_path: str,
    *,
    triage_llm=None,
    compliance_llm=None,
    retrieval_fn: Callable[[str], list[RetrievedChunk]] | None = None,
) -> dict:
    """Run triage + compliance over every item in the gold JSONL file.

    NO gate, NO response, NO redaction. The pipeline is:
      request_text -> triage_agent -> retrieve (or retrieval_fn) -> compliance_agent

    Returns a dict with these keys (all float unless noted):
      "accuracy"                 : fraction of items where predicted exemption sections
                                   match gold exactly (as sets, applies=True)
      "recall"                   : mean per-item recall = |predicted ∩ gold| / |gold|
                                   (skips items where gold exemption_sections is empty)
      "false_positive_rate"      : mean per-item FP rate = |predicted - gold| / |predicted|
                                   (skips items where predicted is empty)
      "citation_grounding_passrate" : fraction of items where verify_citations passes
      "n_requests"               : int, number of items processed
    """
    accuracy_hits = 0
    recall_items: list[float] = []
    fp_items: list[float] = []
    grounded_ok = 0
    n = 0

    with open(gold_path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue

            item = json.loads(line)
            n += 1

            case = CaseRecord(
                request_id=item["id"],
                request_file=item["id"],
                request_text=item["request"],
            )
            cost = CostTracker()

            # --- triage ---
            triage_result = _triage_mod.triage_agent(case, cost, llm=triage_llm)
            case.triage = triage_result

            # --- retrieval ---
            case.retrieved = _do_retrieve(case.request_text, retrieval_fn)

            # --- compliance ---
            result = _compliance_mod.compliance_agent(case, cost, llm=compliance_llm)

            # --- per-item metrics ---
            predicted_sections = {f.section for f in result.exemptions if f.applies}
            gold_sections = set(item.get("exemption_sections", []))

            # accuracy: exact set match
            if predicted_sections == gold_sections:
                accuracy_hits += 1

            # recall: only when gold is non-empty
            if gold_sections:
                recall_items.append(len(predicted_sections & gold_sections) / len(gold_sections))

            # false-positive rate: only when predicted is non-empty
            if predicted_sections:
                fp_items.append(len(predicted_sections - gold_sections) / len(predicted_sections))

            # citation grounding
            grounded, _problems = verify_citations(result, case.retrieved)
            if grounded:
                grounded_ok += 1

    if n == 0:
        return {
            "accuracy": 0.0,
            "recall": 0.0,
            "false_positive_rate": 0.0,
            "citation_grounding_passrate": 0.0,
            "n_requests": 0,
        }

    return {
        "accuracy": accuracy_hits / n,
        "recall": sum(recall_items) / len(recall_items) if recall_items else 0.0,
        "false_positive_rate": sum(fp_items) / len(fp_items) if fp_items else 0.0,
        "citation_grounding_passrate": grounded_ok / n,
        "n_requests": n,
    }
