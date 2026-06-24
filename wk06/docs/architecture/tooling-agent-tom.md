# Tooling Architecture — FOI Multi-Agent CLI

**Author:** agent-tom
**Date:** 2026-06-24
**Status:** Active — technology choices and research findings. Companion to `system-design-agent-tom.md`.
**Draws on:** `specs/mvp-spec-agent-tom.md` §7, `plans/tooling-agent-tom.md` (pre-restructure), Context7 research in `learning_materials/`

This document records technology choices and their rationale. It answers *why* these tools
were selected — not *what* the system must do and not implementation detail such as
requirements.txt or code patterns (those are in `plans/implementation-agent-tom.md`).

---

## 1. Technology choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| LLM — triage | `claude-haiku-4-5-20251001` | Low cost; well-defined classification task; high volume |
| LLM — compliance, response | `claude-sonnet-4-6` | Complex legal reasoning; accuracy and nuance matter |
| LLM framework | `langchain-anthropic` (`ChatAnthropic`) | Structured output, built-in callbacks, retry abstraction |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface` | Local, no API cost; ~90 MB one-time download; adequate retrieval quality for policy doc similarity |
| Vector store | `langchain-chroma` (`Chroma`) | Embedded mode, no separate server; persistent on disk |
| Text splitting | `RecursiveCharacterTextSplitter` | Respects paragraph/sentence boundaries before character splitting |
| Cost tracking | `langchain_core.callbacks.get_usage_metadata_callback` | Built-in context manager, no custom handler needed — see §4 |
| Structured I/O | Pydantic v2 + `llm.with_structured_output(Model)` | Runtime validation of LLM responses; tool-calling under the hood |
| Retry | `tenacity` | Exponential backoff for rate limits; clean decorator API |
| Logging | Python `logging` + JSON formatter | Structured; zero cost; audit-compliant |
| Config | `python-dotenv` | Load `.env` secrets; no hardcoded keys |

---

## 2. LLM tiering rationale

**Haiku for triage:** The triage task is a classification problem — assigning topic,
complexity, and a one-sentence summary. It is well-defined, relatively low-stakes (triage
errors degrade the pipeline but are catchable at the HITL gate), and high-volume (every
request calls triage first). Haiku is significantly cheaper than Sonnet and more than
adequate for structured classification.

**Sonnet for compliance and response:** Exemption analysis requires reasoning about UK FOIA
sections, weighing evidence, applying the public interest test for qualified exemptions, and
constructing citations with verbatim quotes. This is complex legal reasoning where accuracy
matters — a wrong exemption recommendation has legal and governance implications. Drafting a
formal FOI response letter requires precision and proper structure. Sonnet's capability
justifies its higher cost for these stages.

**Cost implication:** Using Haiku for triage reduces per-request cost by ~30–40% compared
to using Sonnet for all stages, with minimal accuracy impact on the classification task.

---

## 3. LangChain decision

**Why a framework over direct Anthropic API calls:**

- **Structured output:** `ChatAnthropic.with_structured_output(PydanticModel)` validates
  LLM responses at runtime against a typed schema. Direct API calls would require manual
  parsing and validation.
- **Callbacks:** The built-in callback system, including `get_usage_metadata_callback`,
  provides per-call token usage without custom instrumentation.
- **Retry abstraction:** LangChain integrates with tenacity and handles rate-limit retries
  at the framework level, reducing boilerplate in agent code.
- **Ecosystem coherence:** `langchain-chroma`, `langchain-huggingface`, and
  `langchain-anthropic` share a consistent interface, reducing impedance mismatch between
  the RAG, embedding, and LLM components.

---

## 4. `with_structured_output()` research finding

**Key finding (confirmed via Context7 LangChain docs):** `with_structured_output()` uses
**tool-calling** under the hood for Anthropic models — not JSON mode or a JSON prompt
suffix.

**Implications for implementation:**
- The Pydantic field `description` strings are sent to the Claude model as tool parameter
  descriptions. These descriptions directly guide the quality of the model's structured
  output — a well-described field produces more accurate results than an undescribed one.
- Write `description` strings carefully and specifically for every field in every model.
  A field described as `"The topic"` will perform worse than one described as
  `"Primary subject area of the FOI request, e.g. 'procurement', 'staffing_hr'"`.
- Tool-calling is more reliable than JSON mode for complex schemas with multiple nested
  fields, which is why LangChain defaults to it for Anthropic.

---

## 5. `get_usage_metadata_callback` research finding

**Key finding (confirmed via Context7 LangChain docs):** LangChain ships a built-in
`get_usage_metadata_callback` context manager in `langchain_core.callbacks`. It supersedes
the previous pattern of writing a custom `BaseCallbackHandler` subclass to intercept
`on_llm_end`.

**How it works:** Wrap any LLM call in `with get_usage_metadata_callback() as cb:`. After
the block, `cb.usage_metadata` is a dict mapping model ID to `{input_tokens, output_tokens,
total_tokens}`.

**Why this matters:** The earlier architecture drafts (and the kickoff prompt) specified a
custom `BaseCallbackHandler` subclass. This was the conventional LangChain pattern from
training data but is no longer the recommended approach. Using the built-in context manager:
- Requires no subclassing
- Returns a clean per-model dict
- Is maintained by the LangChain team as the canonical usage tracking API

Full research notes and usage examples: `learning_materials/langchain-callbacks.md`.

---

## 6. Embedding model: `sentence-transformers/all-MiniLM-L6-v2`

**Why this model:**
- **Local, no API cost.** The only paid external dependency should be the Claude API. Routing
  every policy chunk and every query through an embedding API would add cost and a second
  vendor dependency.
- **Size.** ~90 MB — well under the spec constraint of < 1 GB. Downloads to
  `~/.cache/huggingface/` on first use; subsequent runs are fully offline.
- **Retrieval quality.** Adequate for policy document similarity at hackathon scale. MTEB
  benchmarks (as of 2026-06) rank it well for semantic similarity tasks in the <500 MB tier.
- **`sentence-transformers` compatibility.** The `langchain-huggingface` integration wraps
  it cleanly and uses the same interface as the rest of the LangChain stack.

---

## 7. ChromaDB: embedded mode

**Why embedded (no separate server):**
- A separate ChromaDB server would require starting and managing a background process, adding
  setup complexity for a CLI hackathon tool.
- Embedded mode is a one-line initialisation and persists to disk at a specified path.
- The tradeoffs (no concurrent access from multiple processes, no cross-machine sharing) are
  acceptable for a single-operator CLI tool with a single-writer pattern.

---

## 8. OpenAI embedding fallback

**When and why:** Some lab environments block outbound HTTP requests to HuggingFace model
repositories (`huggingface.co`). If the `sentence-transformers/all-MiniLM-L6-v2` model
cannot be downloaded on first use, the system falls back to OpenAI's
`text-embedding-3-small` embedding API.

**How it is selected:** The `EMBEDDING_PROVIDER` environment variable switches the embedding
implementation in `rag.py`. `EMBEDDING_PROVIDER=openai` uses `OpenAIEmbeddings`; the default
(`huggingface`) uses `HuggingFaceEmbeddings`. Both produce compatible vector representations
for ChromaDB.

**Dependency:** The OpenAI fallback requires `langchain-openai` and `OPENAI_API_KEY` in `.env`.
These are optional — not required for the default HuggingFace path.

---

## 9. Dependency version rationale

Minimum versions in `requirements.txt` are based on confirmed API patterns from Context7
research:

- `langchain-anthropic>=0.3.0` — minimum version confirming `ChatAnthropic` and
  `with_structured_output()` with the current Anthropic models.
- `langchain-core>=0.3.0` — minimum version providing `get_usage_metadata_callback` in
  `langchain_core.callbacks`.
- `chromadb>=1.0.0` — stable embedded mode API.
- `sentence-transformers>=3.0.0` — stable `encode()` interface for
  `langchain-huggingface`.

**Pin after install:** After `pip install -r requirements.txt` succeeds in the target
environment, run `pip freeze > requirements.txt` to pin exact versions. Do not ship
unpinned minimum versions in production.

---

## 10. Token cost reference table

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| `claude-haiku-4-5-20251001` | $0.00025 | $0.00125 |
| `claude-sonnet-4-6` | $0.003 | $0.015 |

**Verify at implementation:** Confirm against https://www.anthropic.com/pricing before
committing costs to `config.py`. Rough estimate per FOI request: ~$0.018–$0.025 depending
on request length and policy doc coverage.
