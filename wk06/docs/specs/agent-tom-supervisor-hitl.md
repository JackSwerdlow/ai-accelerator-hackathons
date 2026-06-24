# Supervisor and HITL Gate Spec — FOI Multi-Agent CLI

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft (agent-prefixed — not yet consolidated)

---

## 1. Supervisor Orchestration (`pipeline.py`)

The supervisor is a plain function, not an LLM agent. It sequences deterministic
calls to each agent and enforces the HITL gate.

### 1.1 Call sequence

```
process_request(request_file, request_text, llm_haiku, llm_sonnet, rag, tracker)
    │
    ├─ [1] triage_agent(request_text, llm_haiku, tracker)
    │       → TriageResult  OR  fallback TriageResult on failure
    │
    ├─ [2] rag.retrieve(request_text, triage.topic)
    │       → list[PolicyChunk]  OR  [] on failure (compliance gets empty context)
    │
    ├─ [3] compliance_agent(request_text, triage, chunks, llm_sonnet, tracker)
    │       → ComplianceResult  OR  fallback ComplianceResult on failure
    │
    ├─ [4] response_agent(request_text, triage, compliance, llm_sonnet, tracker)
    │       → DraftResult  OR  fallback DraftResult on failure
    │
    ├─ [5] hitl_gate(triage, chunks, compliance, draft, request_file)
    │       → AuditEntry  (mandatory — never skipped)
    │
    └─ [6] assemble RequestResult → write output/<id>-result.json
```

### 1.2 Error handling per step

Each step is wrapped in a `try/except` block. On failure the supervisor logs the
error and substitutes a structured fallback so the pipeline can continue:

| Step | Failure | Fallback |
|------|---------|----------|
| Triage | API error / parse error | `TriageResult(topic="unknown", complexity="high", summary="Classification failed — manual review required", confidence=0.0)` |
| RAG retrieve | ChromaDB not indexed / connection error | `[]` (empty list — compliance proceeds with no context) |
| Compliance | API error / parse error | `ComplianceResult(exemptions_found=[], reasoning="Compliance check failed — manual exemption review required", ..., recommendation="withhold")` |
| Response | API error / parse error | `DraftResult(draft_letter="[DRAFT GENERATION FAILED — officer must draft manually]", evidence_summary="See classification and compliance results above")` |
| HITL gate | `KeyboardInterrupt` or broken stdin | Re-raise — never auto-approve |

The HITL gate is never auto-approved or skipped. If stdin is unavailable, the process
exits rather than silently approving a draft.

### 1.3 Retry and circuit breaker

- **Rate limits (HTTP 429):** `tenacity` `@retry` with `wait_exponential(multiplier=2,
  min=1, max=60)`, max 5 attempts. Applied to each agent function.
- **Circuit breaker:** After 3 consecutive agent failures (across requests in one run),
  the supervisor marks that agent as "degraded" and skips it for subsequent requests,
  substituting the fallback and logging a WARNING.

---

## 2. HITL Gate (`hitl.py`)

### 2.1 Display format

The gate prints a structured review to stdout before prompting. The goal is that the
operator can make an informed decision without opening any other file.

```
══════════════════════════════════════════════════════════════════════
  FOI REVIEW: request-001.txt  [FOI-2025-001]
══════════════════════════════════════════════════════════════════════

CLASSIFICATION
  Topic:      procurement
  Complexity: HIGH
  Confidence: 0.94
  Summary:    Request for IT consultancy contract names, values, and
              descriptions for financial years 2022-23 and 2023-24.

POLICY EVIDENCE  (top 5 RAG chunks)
  ┌─ [1]  foi-exemptions-guide.txt  (similarity: 0.82)
  │       "Section 43 -- Commercial interests. Information is exempt
  │        if disclosure would prejudice the commercial interests..."
  ├─ [2]  data-handling-policy.txt  (similarity: 0.79)
  │       "Contract values and supplier names for awarded contracts are
  │        published proactively and can be released under FOI..."
  ├─ [3]  data-handling-policy.txt  (similarity: 0.74)
  │       "Bid evaluation scores and ranking of unsuccessful bidders..."
  ├─ [4]  foi-exemptions-guide.txt  (similarity: 0.71)
  │       "PARTIAL DISCLOSURE: Where some information in a document..."
  └─ [5]  foi-exemptions-guide.txt  (similarity: 0.68)
          "PUBLIC INTEREST TEST: For qualified exemptions (sections 36
           and 43), the department must weigh..."

COMPLIANCE ANALYSIS
  Recommendation: PARTIAL RELEASE
  Exemptions:     s43 (commercial interests)
  Reasoning:      Contract names, supplier names, and total contract
                  values are generally releasable (data-handling-policy
                  §3). Evaluation criteria and internal scoring are
                  protected under s43. No personal data identified
                  requiring s40 redaction.

DRAFT RESPONSE
──────────────────────────────────────────────────────────────────────
Dear Requester,

Thank you for your Freedom of Information request...
[full draft text]
──────────────────────────────────────────────────────────────────────

DECISION
  [A] Approve — send draft as shown
  [R] Reject  — request will not proceed
  [M] Modify  — edit the draft before approving

> 
```

### 2.2 Interaction flow

```
Decision prompt: A / R / M  (case-insensitive; re-prompts on invalid input)

If M (modify):
  "Enter the full revised response text below.
   Submit an empty line to finish."
  > [multiline input until blank line]
  "Preview your modified response? [Y/n]: "
  [show modified text]
  "Confirm modification? [Y/n]: "
  If Y → decision = "modified", record before/after
  If N → return to decision prompt

If R:
  "Enter rejection reason (optional, press Enter to skip): "
  [record in audit notes field]
```

### 2.3 Operator identity

`OPERATOR_ID` is read from the `.env` file. If not set, the gate prompts:
```
Operator ID not configured. Enter your name/email for the audit record: 
```
This ensures every audit entry is attributed, even in unconfigured environments.

---

## 3. Audit Trail Schema

Every HITL decision is appended to `output/audit_trail.jsonl` (one JSON object per
line — append-only, easy to grep and process).

```json
{
  "timestamp": "2026-06-24T14:32:07Z",
  "request_id": "FOI-2025-001",
  "request_file": "request-001.txt",
  "operator": "tom.farley@dept.gov.uk",
  "decision": "modified",
  "triage": {
    "topic": "procurement",
    "complexity": "high",
    "confidence": 0.94
  },
  "compliance_recommendation": "partial_release",
  "exemptions_applied": ["s43"],
  "evidence_refs": [
    "foi-exemptions-guide.txt:chunk-017",
    "data-handling-policy.txt:chunk-004",
    "data-handling-policy.txt:chunk-009",
    "foi-exemptions-guide.txt:chunk-023",
    "foi-exemptions-guide.txt:chunk-031"
  ],
  "modification": {
    "before": "...original draft letter text...",
    "after":  "...operator's revised text..."
  },
  "rejection_reason": null,
  "cost_usd": 0.0182
}
```

Fields when `decision == "approved"`: `modification` is `null`.  
Fields when `decision == "rejected"`: `modification` is `null`; `rejection_reason` is a
string (may be empty).  
Fields when `decision == "modified"`: both `before` and `after` are populated.

---

## 4. Per-Request JSON Output Schema

`output/<request_id>-result.json` contains the complete pipeline record:

```json
{
  "request_file": "request-001.txt",
  "request_id": "FOI-2025-001",
  "triage": {
    "topic": "procurement",
    "complexity": "high",
    "summary": "...",
    "confidence": 0.94
  },
  "retrieved_chunks": [
    {
      "text": "...",
      "source": "foi-exemptions-guide.txt",
      "chunk_id": "foi-exemptions-guide.txt:chunk-017",
      "similarity_score": 0.82
    }
  ],
  "compliance": {
    "exemptions_found": ["s43"],
    "reasoning": "...",
    "policy_sources": ["foi-exemptions-guide.txt", "data-handling-policy.txt"],
    "chunk_ids": ["foi-exemptions-guide.txt:chunk-017", "..."],
    "recommendation": "partial_release"
  },
  "draft": {
    "draft_letter": "...",
    "evidence_summary": "..."
  },
  "audit": {
    "timestamp": "2026-06-24T14:32:07Z",
    "request_id": "FOI-2025-001",
    "request_file": "request-001.txt",
    "operator": "tom.farley@dept.gov.uk",
    "decision": "approved",
    "evidence_refs": ["..."],
    "exemptions_applied": ["s43"],
    "compliance_recommendation": "partial_release",
    "modification": null
  },
  "cost": {
    "triage": {
      "model": "claude-haiku-4-5-20251001",
      "prompt_tokens": 312,
      "completion_tokens": 48,
      "estimated_cost_usd": 0.0001
    },
    "compliance": {
      "model": "claude-sonnet-4-6",
      "prompt_tokens": 1840,
      "completion_tokens": 215,
      "estimated_cost_usd": 0.0087
    },
    "response": {
      "model": "claude-sonnet-4-6",
      "prompt_tokens": 2100,
      "completion_tokens": 380,
      "estimated_cost_usd": 0.0120
    },
    "total_usd": 0.0208
  }
}
```

---

## 5. End-of-Run Cost Summary (stdout)

After all requests are processed:

```
══════════════════════════════════════════════════════════════════════
  COST SUMMARY — 3 requests processed
══════════════════════════════════════════════════════════════════════

  Agent         Model                       Calls  Tokens    Cost USD
  ─────────────────────────────────────────────────────────────────
  triage        claude-haiku-4-5-20251001      3    1,080    $0.0003
  compliance    claude-sonnet-4-6              3    6,165    $0.0261
  response      claude-sonnet-4-6              3    7,440    $0.0360
  ─────────────────────────────────────────────────────────────────
  TOTAL                                        9   14,685    $0.0624

  Results written to: output/
  Audit trail:        output/audit_trail.jsonl
══════════════════════════════════════════════════════════════════════
```

---

## 6. Open Questions

1. Should `output/audit_trail.jsonl` be append-only across runs (persistent log) or
   reset each run? Recommend append-only — audit records should never be deleted.
2. The `OPERATOR_ID` fallback prompt breaks non-interactive use (e.g. piped input).
   Add a `--operator` CLI flag as override?
3. Should rejected requests still write a result JSON? Recommend yes — rejection is
   a decision and should be on record.
