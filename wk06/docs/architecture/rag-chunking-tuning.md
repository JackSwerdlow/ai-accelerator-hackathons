# RAG chunking / k spot-tune (Task 4b)

**Author:** Agent-Jack · **Date:** 2026-06-24 · **Status:** validated — constants ratified unchanged

Timeboxed recall@k validation of the section-aware chunker + nomic retrieval against the
**real starter policy corpus** (`starter/documents/policies/`: `foi-exemptions-guide.txt`,
`data-handling-policy.txt`), copied into a tmp ChromaDB and queried with the production
`search_policies`.

## Chunk structure (section-aware)
- `foi-exemptions-guide.txt` → **10 chunks**: `[None, s12, s21, s36, s40, s41, s43, None, None, None]`
  (one citable chunk per statutory section; the `None` chunks are the title/intro and the
  PUBLIC INTEREST TEST / PARTIAL DISCLOSURE / RESPONSE TIMELINE blocks).
- `data-handling-policy.txt` → **7 chunks** (numbered headings `1.`–`6.` + title), all `section=None`.
- **17 chunks total.** Section-aware splitting means chunk size is driven by the section
  boundaries, not by `CHUNK_SIZE` — the latter only governs the size-based **fallback** path for
  unstructured documents with no detectable headings.

## recall@k over 6 representative requests (one per exemption)
| Request gist | Expected | got @k=5 (sections, nearest-first) | hit |
|---|---|---|---|
| internal policy deliberation, emails/meeting notes | s36 | None, None, None, s43, None | content-yes / label-no |
| cost / 18-hour limit | s12 | **s12**, None, None, s21, None | ✅ |
| already published on website | s21 | **s21**, s41, None, None, None | ✅ |
| names, staff numbers, personal details | s40 | None, **s40**, None, None, None | ✅ |
| tender scores, pricing, supplier margins | s43 | None, **s43**, None, None, None | ✅ |
| provided in confidence by a third party | s41 | **s41**, s40, None, None, None | ✅ |

**recall@5 = 5/6 on exact section label; effectively 6/6 on relevant content.** The s36 case is
not a true miss: the nearest hit (cosine distance 0.311) is the data-handling policy's
`4. INTERNAL DELIBERATIONS` block, which *is* the on-point s36 guidance (it names Section 36 and
the public interest test) — it simply carries `section=None` because its heading is a numbered
clause, not a `SECTION 36` heading. The compliance agent reads chunk **text** (and cites verbatim
quotes), so the s36 finding remains fully groundable; `section` metadata is a convenience label,
not the sole signal. Top-hit cosine distances cluster in 0.21–0.39 — comfortably discriminative.

## Decision — constants unchanged (ratified baseline holds)
- `CHUNK_SIZE = 512`, `CHUNK_OVERLAP = 64` — unchanged. They only affect the unstructured
  fallback; the structured policies chunk cleanly on headings.
- `RAG_TOP_K = 5` — unchanged. Over a ~17-chunk corpus, k=5 reliably surfaces the relevant
  exemption content for every request type while keeping the compliance prompt (and its token
  cost) tight. Raising k would mostly add `None`-section noise for marginal exact-label gain.

No code change required; this note is the Task 4b deliverable.
