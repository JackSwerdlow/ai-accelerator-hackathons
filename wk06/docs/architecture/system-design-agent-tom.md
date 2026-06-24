# System Design — FOI Multi-Agent CLI

**Author:** agent-tom
**Date:** 2026-06-24
**Status:** Active — supersedes `specs/system-architecture-agent-tom.md` and `specs/supervisor-hitl-agent-tom.md`
**Draws on:** `specs/Agent-Jack-SPEC.md` §5 (pipeline topology rationale), `specs/mvp-spec-agent-tom.md`

This document records design decisions and their rationale. It answers *why* the system
is shaped the way it is — not *what* it must do (that is in `specs/`) and not *how* to
build it (that is in `plans/`).

---

## 1. Pipeline topology: linear supervised pipeline over a shared case record

**Decision:** A linear, supervised pipeline where a single supervisor sequences four
deterministic agent calls over a shared case record that is enriched at each stage.

```
            ┌──────────────────────── supervisor ────────────────────────┐
 request →  │  triage → compliance(RAG) → response → HITL gate           │  → outputs
            └─────────────────────────────────────────────────────────────┘
                         (per-stage fallback · cost accumulation · audit)
```

**Rationale (from `Agent-Jack-SPEC.md` §5):** This is the most reliable, deterministic,
and auditable topology. The strongest fit for the Reliability and Governance rubric axes
and for a clean, repeatable demo.

**Dynamic routing rejected because:** it introduces non-determinism in the processing path,
makes the audit trail less uniform (different requests may have taken different routes), and
offers no benefit at this scale — all FOI requests follow the same four-stage process.

**Blackboard architecture rejected because:** shared mutable state across agents is harder
to reason about, test, and trace. A linear pipeline where each stage receives a typed
input and produces a typed output is fully traceable and independently testable.

**Shared case record:** A single data structure threaded through the pipeline so every
stage sees prior stages' findings and the final record is a complete, auditable account
of the request. The case record grows at each stage; nothing is discarded.

---

## 2. Supervisor design: plain Python function, not an LLM agent

**Decision:** The supervisor (`pipeline.py`) is implemented as a plain Python function
(`process_request()`), not as an LLM-powered agent.

**Rationale:** Sequencing deterministic calls is not an LLM task. An LLM supervisor would:
- Add latency and cost to an operation that needs no reasoning
- Introduce non-determinism into what must be a deterministic control path
- Make error handling harder (an LLM cannot reliably "decide" to invoke the fallback)
- Complicate auditing (reasoning trace vs deterministic call sequence)

The supervisor owns: sequencing, per-stage error handling and fallback, cost accumulation,
the HITL gate invocation, and output writing. All of these are purely deterministic.

---

## 3. Agent interface contract: Pydantic models only

**Decision:** Agents exchange only Pydantic v2 models. No agent imports from another agent.
The supervisor wires them together.

**Rationale:**
- **Independent testability:** each agent can be tested in isolation against a typed input
  and expected output — no shared state, no hidden dependencies.
- **Replaceability:** swapping one agent's implementation requires only that the new
  implementation accepts the same input model and returns the same output model.
- **Runtime validation:** Pydantic validates every exchange point at runtime; a malformed
  LLM response is caught at the model boundary, not silently propagated.
- **Single source of truth:** all schema definitions live in `models.py`; changes propagate
  automatically across agents that consume them.

---

## 4. HITL gate design principles

**Decision:** The gate implements an Approve / Reject / Modify (A/R/M) pattern with rich
evidence display, mandatory active choice, and never auto-approval.

**Rationale for three-way decision (not binary):**
- Binary approve/reject forces rejection of near-correct drafts. The Modify path allows
  the operator to fix a minor error without discarding the entire AI-generated draft.
- Both the AI's original and the operator's modification are preserved in the audit trail
  (AI recommendation alongside human decision), which is the key governance requirement.

**Rationale for never auto-approve:**
- The Robodebt scheme is the canonical cautionary example: an automated checkpoint that
  functioned as a rubber stamp amplified AI errors at scale rather than catching them.
  Passive or default approval is not a safeguard.
- The operator must actively choose. The system must not time out to a default, must not
  accept empty input as approval, and must not skip the gate for any reason including
  batch processing.

**Evidence display before decision:**
- The operator needs to see the full basis for the AI recommendation before acting. The
  gate displays: retrieved policy chunks (with source and similarity score), classification,
  exemption reasoning, and the draft response labelled "AI-generated draft".
- Warning banners for `clarification_recommended` and `third_party_notification_required`
  are shown before the decision prompt, not buried in the evidence.

**Operator identity:**
- Every decision is attributed to a named individual or role. An empty operator identity
  is an error. This satisfies the "human review of an AI-assisted decision" expectation
  under the Data (Use and Access) Act 2025.

---

## 5. Error handling strategy

**Decision:** Per-step fallbacks with conservative defaults, tenacity retry for transient
failures, and circuit breaker after repeated failures.

**Conservative defaults rationale:** The fallback for every stage fails *safe*, not *open*:
- Triage failure → `topic="unknown"`, `complexity="high"` (forces careful human review)
- Compliance failure → recommend `"withhold"` (never silently releases)
- Response failure → a templated holding response flagged for manual completion

These defaults are deliberately over-cautious: the cost of under-releasing (delayed response,
officer manual review) is far lower than the cost of incorrectly releasing exempt material.

**Tenacity retry:** Applied to LLM API calls for transient rate-limit errors (HTTP 429).
Exponential backoff prevents thundering herd on the API. Does not retry on persistent errors
(authentication failures, malformed requests).

**Circuit breaker:** After 3 consecutive failures for the same agent across requests in a
single run, the agent is marked "degraded" and the fallback is substituted for all remaining
requests. This prevents a broken agent from blocking batch processing indefinitely while
ensuring failures are visible in the log.

**Batch isolation:** One failing request must not abort the run. The supervisor catches
per-request exceptions, logs the failure, and continues with the next request.

---

## 6. RAG architecture decisions

**Embedded ChromaDB (no separate server):**
- For a hackathon CLI, requiring a running ChromaDB server would complicate setup
  significantly. Embedded mode is a one-line initialisation and persists to disk.
- The tradeoff (no concurrent access, no cross-machine sharing) is acceptable for a
  single-operator CLI tool.

**Local HuggingFace embeddings (no embedding API cost):**
- The only paid external dependency should be the Claude API. Routing every policy chunk
  and every query through an embedding API would add cost and a second external dependency.
- `sentence-transformers/all-MiniLM-L6-v2` is ~90 MB, downloaded once to
  `~/.cache/huggingface/`, and runs fully locally thereafter.
- Adequate retrieval quality for policy document similarity at hackathon scale.

**`RecursiveCharacterTextSplitter`:**
- Respects paragraph and sentence boundaries before falling back to character splitting.
  Policy documents contain reasoning that spans multiple sentences; splitting mid-sentence
  would degrade retrieval quality. Paragraph-aware splitting preserves context.

---

## 7. Audit trail design

**Append-only JSONL file:**
- Never overwritten across runs. Each run appends to the same file.
- Rationale: the audit trail is a governance asset. Overwriting it would destroy the record
  of past decisions. An append-only file can be ingested by any log aggregation tool and
  can be inspected with standard text tools.
- Rejected requests are also logged. Rejection is a decision on record, not an absence.

**Operator attribution required:**
- Every entry carries a non-empty operator string. An empty operator identity is an error.
- This satisfies the "human review of an AI-assisted decision" requirement under the Data
  (Use and Access) Act 2025.

**AI recommendation alongside human decision:**
- The entry captures `compliance_recommendation` (what the AI recommended) and `decision`
  (what the operator chose). Both are preserved.
- When the operator modifies the draft, both the original AI text and the operator's revised
  text are captured in the `modification` field.
- This gives auditors the ability to reconstruct exactly what the AI produced and what the
  human decided, independently.

---

## 8. Pipeline data flow diagram

```
FOI Request File (.txt)
       │
       │  read_text()
       ▼
 ┌─────────────┐
 │ triage.py   │  LLM: cheap, fast (classification task)
 │             │  In:  request_text: str
 │             │  Out: TriageResult
 └──────┬──────┘
        │
        │  TriageResult + request_text
        ▼
 ┌─────────────────┐
 │  rag.py         │  retrieve top-k chunks from ChromaDB
 │  (retrieval)    │  Query: request_text + triage.topic
 │                 │  Out: list[PolicyChunk]
 └────────┬────────┘
          │
          │  request_text + TriageResult + list[PolicyChunk]
          ▼
 ┌────────────────┐
 │ compliance.py  │  LLM: capable, complex reasoning
 │                │  In:  request_text, triage, chunks
 │                │  Out: ComplianceResult
 └───────┬────────┘
         │
         │  request_text + TriageResult + ComplianceResult
         ▼
 ┌───────────────┐
 │ response.py   │  LLM: capable, formal drafting
 │               │  In:  request_text, triage, compliance
 │               │  Out: DraftResult
 └──────┬────────┘
        │
        │  TriageResult + list[PolicyChunk] + ComplianceResult + DraftResult
        ▼
 ┌──────────────┐
 │  hitl.py     │  Display evidence; prompt operator; write audit entry
 │              │  In:  all above + request_file path
 │              │  Out: AuditEntry
 └──────┬───────┘
        │
        │  RequestResult (all stages + cost)
        ▼
  output/<request_id>-result.json
  output/audit_trail.jsonl        (appended)
```

Each agent call wraps its LLM invocation in a cost-tracking context manager. The
`CostTracker` in `cost_tracker.py` accumulates per-agent records; `pipeline.py` calls
`tracker.summary()` to populate `RequestResult.cost`.
