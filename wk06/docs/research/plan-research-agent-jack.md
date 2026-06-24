# Plan Research — grounding for `Agent-Jack-PLAN.md`

**Author:** Agent-Jack
**Date:** 2026-06-24
**Method:** 4-way parallel Sonnet research sweep (Context7 for library docs, WebSearch for current rankings). Run ID `wf_1ab7f47f-bf3`.
**Purpose:** Evidence base for the implementation plan. Decisions here are *inputs* to the plan, not the plan itself.

> Caveat carried from the sweep: commercial legal RAG still hallucinates **17–33%** even with retrieval (Magesh et al. 2025). RAG reduces, never eliminates, the problem — the plan must lean on verification, not trust.

---

## 1. Embedding model (resolves spec §13.1)

**Decision — PRIMARY: `nomic-ai/nomic-embed-text-v1.5`.** ~274 MB, 768 dims (Matryoshka → can truncate to 256), **8,192-token** context, Apache 2.0.
**FALLBACK: `Alibaba-NLP/gte-base-en-v1.5`.** ~547 MB, 768 dims, 8,192-token context, Apache 2.0 — *drop-in, no prefix needed*.

**The decisive criterion is max sequence length, not MTEB score.** FOI/ICO guidance paragraphs are dense and cross-referential; models capped at ≤512 tokens (incl. the common `all-MiniLM-L6-v2` baseline at 256) truncate context and degrade badly on legal text ("0.4–0.6 accuracy at 4K chars" — Milvus 2026 benchmark). So the *usual default is the wrong choice here.*

**Integration gotchas (important):**
- nomic **requires** `trust_remote_code=True` and task prefixes — `search_document: ` on chunks, `search_query: ` on queries. Forgetting the prefixes measurably hurts retrieval. Chroma's built-in `SentenceTransformerEmbeddingFunction` may not add prefixes → may need a thin custom embedding-function wrapper.
- **gte-base** needs neither prefix nor remote code → integrates cleanly with Chroma's EF out of the box. This is the main argument for the fallback if we want zero friction.
- Qwen3-Embedding-0.6B scores higher (64.33, 32K context) but BF16 weights are **1.19 GB — over the limit**; only an unaudited INT8 community quant fits. **Excluded** for the hackathon.
- Open item: MTEB scores are BEIR (web/academic), not legal — validate on a small FOI passage/query set before locking in.

## 2. Orchestration (resolves spec §13.5) — DECISION NEEDED

If we use LangChain: **LangGraph `StateGraph` is the current recommended approach** — `AgentExecutor` and most legacy chain/agent abstractions were **deprecated Oct 2024**. `create_tool_calling_agent` survives only as a thin leaf-node convenience.

**But** for a *fixed linear 5-stage pipeline*, LangGraph's graph machinery may be heavier than needed. The genuine fork for the plan:
- **(A) Lightweight:** direct `langchain-anthropic` `ChatAnthropic` + `with_structured_output(...)` per agent, sequenced by a plain Python supervisor. Fewer moving parts; maximal control over the audit trail; no graph framework.
- **(B) LangGraph `StateGraph`:** nodes per stage, conditional edges. More idiomatic for "multi-agent", but more framework surface for a linear flow.
- **(C) No LangChain at all:** raw Anthropic SDK + Pydantic. Most control, most boilerplate.

## 3. LLM integration specifics (if LangChain)
- Structured output: `model.with_structured_output(PydanticModel, method='json_schema')` — **requires `langchain-anthropic>=1.1.0`**; without `method='json_schema'` it silently falls back to tool-use mode.
- **Cost tracking (built-in, no custom subclass):** `from langchain_core.callbacks import get_usage_metadata_callback` (context manager) or `UsageMetadataCallbackHandler` (via `config={"callbacks":[cb]}`). Returns per-model `{input_tokens, output_tokens, total_tokens, input_token_details:{cache_read, cache_creation}}`. **Create a fresh handler per request** (it accumulates). *(Matches Agent-Tom's finding.)*
- Retry/backoff: `model.with_retry(stop_after_attempt=N, wait_exponential_jitter=True)` on any Runnable — simplest, no extra dep. (Newer `ModelRetryMiddleware` exists but is tied to the deep-agents API — avoid unless already on it.)
- Import path gotcha: callbacks are in `langchain_core.callbacks`, **not** `langchain.callbacks`.

## 4. ChromaDB / RAG
- **`chromadb.PersistentClient(path="./chroma_db")`** — persists automatically (no `.persist()` in current API; calling it errors). Same path across `index` and `process` invocations → index survives. *This kills the #1 in-memory-lost-between-runs failure mode.*
- **`client.get_or_create_collection(name=..., embedding_function=ef, configuration={"hnsw":{"space":"cosine"}})`** — idempotent; pass the EF on every run; cosine space suits sentence-transformers.
- Embedding path: **direct Chroma `SentenceTransformerEmbeddingFunction`** is one dependency vs three for the LangChain-Chroma path. Prefer direct for a standalone CLI; use langchain-chroma only if orchestration is LangChain-heavy. (Note the nomic-prefix wrinkle in §1.)
- **Metadata must be scalar** (str/int/float). Store `{"source": filename, "chunk_index": int, "last_indexed": int(epoch)}`. Epoch int enables staleness filters: `where={"last_indexed": {"$gt": cutoff}}`.
- Query: `collection.query(query_texts=[q], n_results=k, include=['documents','metadatas','distances'])`. **Distances, not similarities** (lower = closer) — don't show raw distances to users as "scores".
- Chunking baseline: `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64, add_start_index=True)`, `k=5` — **empirical starting point**, tune recall@5 at 256/32, 512/64, 1024/128.

## 5. Grounding & lightweight eval (strengthens spec §6.2, §11)
- **Force verbatim-quote citations during generation** via structured output: each claim emits `{claim, quote, section_id}`. Unsupported claims become detectable with zero extra API cost (Pleias-RAG, 2025).
- **3-level citation-verification ladder:**
  - L1 (free): every cited `section_id` ∈ retrieved chunk ids → catches 100% of fabricated IDs.
  - L2 (free): `difflib.SequenceMatcher(None, quote, chunk_text).ratio() > 0.85` → catches verbatim misquotes (~83% detection).
  - L3 (optional, 1 LLM/NLI call per claim): entailment check (e.g. MiniCheck / DeepEval `FaithfulnessMetric`) → catches **misgrounded** citations (real section, contradictory text) — the most dangerous class, *not* caught by L1/L2.
- **Compliance reasoning scaffold (IRAC-adapted, kept light):** (1) identify exemption + section → (2) copy verbatim evidence → (3) assess public-interest test with explicit factors → (4) conclude release/partial/withhold + confidence. Keep it light; over-rigid templates *hurt* (self-CoT beat scripted templates by ~34% — arXiv 2511.07979). Violation-first aggregation (one confirmed exemption → withhold) is reliable zero-shot.
- **Retrieval drives accuracy more than prompt tricks.** Consider **hybrid BM25 + dense** retrieval — legal text has exact identifiers ("s.40(2)") that pure dense retrieval misses. **Cap retrieved chunks at 3–5**: more context *degrades* grounding (42% accuracy drop from 2→150 results — arXiv 2605.06635).
- **Eval tooling:** plain Python assertions for L1/L2 gold-answer checks; add **DeepEval `FaithfulnessMetric`** only for the semantic L3 step; **skip Ragas and all observability platforms** (setup cost > hackathon value). Gold set: **20–30 FOI requests in JSONL** `{id, request, exemptions[], evidence_sections[], disclosure}`, **hold out ~30%**. Report exemption-classification accuracy, coverage recall, false-positive rate.
- Optional shortcut: **Anthropic Citations API** (Jan 2025) returns native citation blocks for Claude — less manual wiring, but couples us to that API; weigh vs the manual verbatim-quote approach (more auditable, framework-independent).

---

## Decisions the plan must make (carried forward)
1. **Orchestration:** lightweight direct-SDK supervisor vs LangGraph vs raw Anthropic SDK (§2).
2. **Embedding:** nomic (best quality, needs prefix/remote-code wrapper) vs gte-base (drop-in, slightly lower) (§1).
3. **Retrieval:** hybrid BM25+dense vs dense-only; final `k` (3–5) and chunk size (§4, §5).
4. **Eval depth:** L1/L2 assertions only, or add L3 entailment (DeepEval) (§5).
5. **Citations:** manual verbatim-quote schema vs Anthropic Citations API (§5).

## Sources
Embeddings: HuggingFace model cards (nomic-embed-text-v1.5, gte-base-en-v1.5, Qwen3-Embedding-0.6B); Milvus 2026 embedding benchmark. LangChain/Anthropic: docs.langchain.com (philosophy, models, anthropic integration, middleware). ChromaDB: chroma-core GitHub examples + cookbook.chromadb.dev. Grounding/eval: Magesh et al. 2025 (JELS); Pleias-RAG (arXiv 2504.18225); Princeton CITP 2026; arXiv 2511.07979, 2510.26309, 2509.21557, 2605.06635; deepeval.com.
