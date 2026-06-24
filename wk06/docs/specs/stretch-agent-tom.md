# Stretch Spec — FOI Multi-Agent CLI

**Status:** Reference — implement after MVP is complete and working  
**Date:** 2026-06-24  
**Prerequisite:** `mvp-agent-tom.md` must be fully implemented before any stretch goal is started  
**Source:** `docs/research/foi-landscape-synthesis.md` (S1–S9) plus review recommendations

These goals add meaningful value beyond the hackathon rubric's minimum. Tier 1 items are
architecturally close to the MVP and are realistic additions during the hackathon. Tier 2
items require more effort. Tier 3 items are significant enough to be their own work items.

---

## Tier 1 — High value, architecturally close

### S1. Citation Verification (Post-Compliance Check)

**Value:** The highest-risk gap in the MVP. LLMs hallucinate 13–21% of legal citations
even with RAG (arXiv 2606.00898). An incorrect exemption section number in a draft letter
is legally indefensible.

**What it does:** After `compliance.py` returns a `ComplianceResult`, run a lightweight
post-generation check before passing to `response.py`:

1. Extract all section references from `compliance_result.reasoning` — any string matching
   the pattern `s\.\d+` (e.g. `s.43`, `s.40`) using `re.findall(r's\.\d+', reasoning)`.
2. For each cited section, check whether the string appears in the verbatim text of at
   least one chunk in `compliance_result.chunk_ids` (looked up from the `PolicyChunk`
   list already in memory).
3. If a citation is not found in any retrieved chunk, log a `WARNING` and append the
   unverified citation to a new field: `ComplianceResult.unverified_citations: list[str]`.
4. Render unverified citations as a banner in the HITL display:

```
[⚠ UNVERIFIED CITATIONS: The following exemption references were not found
   verbatim in the retrieved policy chunks: s.47. Check these manually before
   approving.]
```

**Schema change:** Add to `ComplianceResult` in `models.py`:
```python
unverified_citations: list[str] = Field(
    default_factory=list,
    description="Citation references not found verbatim in retrieved chunks"
)
```

**Implementation notes:**
- This is pure Python string matching — no additional LLM call needed.
- `re.findall(r'\bs\.?\d+\b', text, re.IGNORECASE)` catches `s40`, `s.40`, `S.40`.
- A citation "found" means the pattern appears anywhere in the chunk text — exact subsection
  matching (e.g. `s.40(2)`) can be a later refinement.
- Do not block the pipeline on unverified citations — surface them and let the operator
  decide. The HITL gate already supports human override.

**Estimated effort:** ~50 lines of Python across `compliance.py`, `models.py`, `hitl.py`.

---

### S2. Triage Override with Pipeline Re-Run

**Value:** Triage errors cascade downstream (VIDIZMO finding: wrong topic → wrong RAG
query → wrong compliance analysis → wrong draft). Currently the HITL gate is review-only;
operators cannot correct a mis-classification without re-running the whole pipeline.

**What it does:**

1. At the HITL gate, before the `A/R/M` decision, show an additional prompt:
```
  Classification correct? [Y/n]:
```
2. If `n`, prompt:
```
  Enter corrected topic (current: procurement):
  Enter corrected complexity — high / medium / low (current: high):
```
3. Accept the corrections; update `triage_result.topic` and `triage_result.complexity`
   in-memory (do not re-call the triage LLM — the operator's judgement supersedes it).
4. Re-run steps [2]–[4] of the pipeline (RAG retrieve, compliance, response) with the
   corrected triage classification.
5. Re-render the HITL display with the new compliance analysis and draft.
6. Record the original and corrected topic in `AuditEntry`:

**Schema change:** Add to `AuditEntry` in `models.py`:
```python
triage_overridden: bool = False
triage_original_topic: str | None = None
```

**Implementation notes:**
- Wrap the `[2]–[4]` pipeline steps in a helper function
  `run_compliance_and_response(request_text, triage, rag, llm_sonnet, tracker)` that
  `pipeline.py` can call both on first run and on triage override.
- The partial re-run adds ~2 Sonnet calls (compliance + response) at ~$0.01 per
  override. Log additional cost against the same `RequestCost`.
- Set `operator_overrode_triage: bool` in the audit entry — this field has direct value
  for monitoring classification accuracy over time (see `production-agent-tom.md`).

**Estimated effort:** ~80 lines across `pipeline.py`, `hitl.py`, `models.py`.

---

### S3. Policy Document Staleness Warning

**Value:** The RAG store is indexed once at startup. FOI exemption guidance changes.
The compliance agent reasoning from outdated policy documents could cite superseded
guidance. This is a medium risk in the MVP; a low-cost fix makes it visible.

**What it does:**

1. When indexing, write a metadata file to `chroma_db/index_metadata.json`:
   ```json
   { "indexed_at": "2026-06-24T14:00:00Z", "document_count": 4 }
   ```
2. In `main.py process`, read `index_metadata.json` and check the `indexed_at` age.
3. If age exceeds `STALE_INDEX_DAYS` (default: 30, configurable via env var), print
   a warning before processing:
   ```
   ⚠ WARNING: Policy documents were last indexed 45 days ago. Consider re-indexing
     before processing requests: python main.py index --source documents/policies/
   ```
4. Add to `config.py`:
   ```python
   STALE_INDEX_DAYS = int(os.getenv("STALE_INDEX_DAYS", "30"))
   ```

**Implementation notes:**
- Do not block processing — only warn. The operator decides whether to re-index.
- Add `main.py index --check-freshness` subcommand that reports age without re-indexing.
- `index_metadata.json` is inside `chroma_db/` which is gitignored; that is correct.

**Estimated effort:** ~30 lines across `rag.py`, `main.py`, `config.py`.

---

## Tier 2 — Meaningful additions, moderate effort

### S4. Duplicate / Similar Request Detection

**Value:** Real FOI teams waste significant effort re-processing requests that are nearly
identical to previously answered ones. Surfacing a past decision to the operator before
the pipeline runs saves processing cost and promotes consistent responses.

**What it does:**

1. Before running the triage → compliance → response pipeline, embed the incoming request
   text using the same embedding model as RAG.
2. Query a second ChromaDB collection (`foi_decisions`) against past audit entries.
3. If cosine similarity > `DUPLICATE_THRESHOLD` (default: 0.85), surface at HITL:
   ```
   ℹ SIMILAR PAST REQUEST DETECTED (similarity: 0.91)
     Reference:   FOI-2025-042 (2026-03-15)
     Decision:    approved
     Exemptions:  s43
     Stored at:   output/foi-2025-042-result.json
   ```
4. After an `approved` or `modified` decision, append the request embedding + audit
   reference to the `foi_decisions` collection.

**Schema change:** `config.py`:
```python
DUPLICATE_THRESHOLD = float(os.getenv("DUPLICATE_THRESHOLD", "0.85"))
DECISIONS_COLLECTION = "foi_decisions"
```

**Implementation notes:**
- Only seed the `foi_decisions` collection from `approved`/`modified` entries. Rejected
  requests are less useful as precedents.
- This does not skip the pipeline — it informs the operator. Full pipeline still runs so
  the compliance analysis is fresh.
- The embedding cost is negligible (~0 for HuggingFace local model).

**Estimated effort:** ~80 lines across `rag.py`, `pipeline.py`, `hitl.py`, `config.py`.

---

### S5. Extended Vexatious / Malformed Request Flagging

**Value:** The ICO's May 2026 guidance identifies AI-drafted requests that misquote
legislation as a rising operational problem. The MVP `clarification_recommended` flag is
a start; this stretch goal adds structured detection categories.

**What it does:**

The triage agent prompt is extended to detect and classify:

| Category | Flag | Example |
|----------|------|---------|
| Non-existent FOIA section | `malformed_legislation` | "Under s.99 of the FOIA..." |
| Ambiguous scope | `ambiguous_scope` | No time period, no subject area specified |
| Unreasonably broad | `overbroad` | "All internal communications ever sent" |
| Bulk/identical pattern | `bulk_identical` | Identical to recent requests |
| No public authority nexus | `wrong_body` | Request clearly addressed to a different body |

**Schema change:** Extend `TriageResult`:
```python
clarification_flags: list[Literal[
    "malformed_legislation",
    "ambiguous_scope",
    "overbroad",
    "bulk_identical",
    "wrong_body"
]] = Field(default_factory=list)
```

The existing `clarification_recommended: bool` remains as the top-level flag (set True
when `len(clarification_flags) > 0`). The flags add specificity for the operator.

**HITL display:** When flags are present, list them:
```
[⚠ CLARIFICATION RECOMMENDED
   Flags: ambiguous_scope — no time period specified; malformed_legislation — s.99
   does not exist in FOIA 2000. Consider seeking clarification before processing.]
```

**Implementation notes:**
- The detection is prompt-engineering, not a separate agent. Add a structured
  `clarification_flags` field to the triage tool definition.
- "bulk_identical" requires S4 (duplicate detection) to be meaningful — implement S4 first.
- FOIA 2000 sections run to s.88; the triage agent can flag anything citing s.89+ as
  `malformed_legislation` without needing a full section lookup.

**Estimated effort:** ~40 lines of prompt changes + schema extension + HITL display update.

---

### S6. ATRS Record Auto-Generation

**Value:** Any public authority deploying this system must publish an Algorithmic
Transparency Recording Standard (ATRS) record before going live (mandatory since
February 2024). Generating a pre-filled draft from system metadata turns a compliance
burden into a one-command artefact.

**What it does:**

Add `main.py atrs-record` subcommand that writes a partially-filled ATRS Tier 1 record
to `output/atrs-record.md` using known system metadata:

```markdown
# ATRS Tier 1 Record — FOI Multi-Agent Processing System

**Tool name:** FOI Multi-Agent CLI
**Version:** [populated from package metadata]
**Date prepared:** [today]
**Contact:** [OPERATOR_ID from .env]

## Description
Automated triage, compliance, and response drafting for FOI requests. No decision
is made without human approval (mandatory HITL gate).

## Scope of use
Processes incoming FOI requests against indexed policy documents. Recommends
exemptions and drafts response letters for operator review and approval.

## Significant influence on decisions?
Yes — the system produces compliance recommendations and draft responses that
directly inform the officer's decision on each FOI request.

## Human oversight
Every request is reviewed by a named operator at the HITL gate before any response
is sent. The operator can approve, reject, or modify the AI-generated draft.

## Third-party suppliers
- Anthropic Claude API (claude-haiku, claude-sonnet) — LLM inference
- HuggingFace sentence-transformers — local embedding model
- ChromaDB — local vector store (no external calls)

## Audit trail
Decisions are logged to output/audit_trail.jsonl with operator attribution and
AI-generated content preserved for review.

---
*Auto-generated by `main.py atrs-record`. Review and complete before submission.*
*ATRS Tier 2 fields (bias testing, performance metrics) require manual completion.*
*See: https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard*
```

**Implementation notes:**
- No LLM call — pure template substitution.
- Tier 2 fields (bias testing, performance metrics, training data description) must be
  completed manually; the auto-generated record notes this explicitly.
- For real deployment, this record must be submitted to the ATRS register before go-live.

**Estimated effort:** ~30 lines in `main.py` plus a template string.

---

## Tier 3 — Larger scope, plan as future work

### S7. Precedent Store

**What it does:** Persist approved audit entries to a third ChromaDB collection. Before
the compliance agent runs, retrieve semantically similar past decisions as few-shot
examples in the compliance prompt. This promotes consistency and lets the system learn
from operator corrections over time.

**Why it is Tier 3:** Requires careful prompt engineering to avoid "poisoning" the
compliance agent with past errors. The precedent retrieval logic (what to include, how
many, how to weigh recency vs similarity) needs empirical testing. Architecturally,
it adds a new data dependency between past and present requests, which complicates
testing.

**Dependency:** Builds on S4 (duplicate detection); the `foi_decisions` collection in
S4 is the seed for the precedent store.

---

### S8. Multi-Department Routing

**What it does:** Detect when an FOI request crosses departmental boundaries (e.g., a
request about a joint DfE/DHSC programme) and flag it for routing to the correct team
rather than processing immediately.

**Why it is Tier 3:** Requires a maintained taxonomy of departmental areas and
sub-authorities. Without that taxonomy, detection is speculative. Out of scope for a
single-department hackathon demo.

---

### S9. Proactive Disclosure Flagging

**What it does:** After a request is approved, check whether the response could be
pre-emptively published to a disclosure log (reducing future duplicate requests on the
same topic). Flag as `proactive_disclosure_candidate: bool` in the audit entry.

**Why it is Tier 3:** The decision to publish proactively requires legal and policy
judgement beyond what the compliance agent can provide. The flag would need to be
acted on by a separate publication workflow. Valuable but well beyond hackathon scope.

---

## Performance Monitoring Fields (build-in during MVP if time allows)

These two fields on `AuditEntry` have zero implementation cost at design time but
become essential for a real deployment's performance review:

```python
operator_overrode_triage: bool = False   # did operator correct the triage classification?
# operator_modified_draft is already captured via decision == "modified"
```

Add `operator_overrode_triage` to `AuditEntry` in `models.py` (set in S2 if
implemented; otherwise set based on whether S2 override was used). Even without
S2, this field can be set to `False` at MVP and flipped to `True` if S2 is added later.

---

## Stretch Goal Summary

| ID | Goal | Tier | Effort | Dependency |
|----|------|------|--------|------------|
| S1 | Citation verification | 1 | ~50 lines | None |
| S2 | Triage override + re-run | 1 | ~80 lines | None |
| S3 | Policy staleness warning | 1 | ~30 lines | None |
| S4 | Duplicate detection | 2 | ~80 lines | None |
| S5 | Extended vexatious/malformed flagging | 2 | ~40 lines | None (S4 for bulk_identical) |
| S6 | ATRS record auto-generation | 2 | ~30 lines | None |
| S7 | Precedent store | 3 | Significant | S4 |
| S8 | Multi-department routing | 3 | Significant | External taxonomy |
| S9 | Proactive disclosure flagging | 3 | Significant | External workflow |
