# Tooling Plan — FOI Multi-Agent CLI

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft (agent-prefixed — not yet consolidated)  
**Based on:** `docs/prompts/kickoff_prompt.md` + research in `learning_materials/`

---

## 1. Package Dependencies (`solution/requirements.txt`)

```
# LLM integration
langchain-anthropic>=0.3.0
langchain-core>=0.3.0

# Vector store + RAG
langchain-chroma>=0.1.0
chromadb>=1.0.0

# Embeddings (local, no API cost)
langchain-huggingface>=0.1.0
sentence-transformers>=3.0.0

# Text splitting (built into langchain)
langchain-text-splitters>=0.3.0

# Structured I/O
pydantic>=2.0.0

# Retry / backoff
tenacity>=8.0.0

# Config
python-dotenv>=1.0.0
```

**OpenAI fallback** (only needed if `EMBEDDING_PROVIDER=openai`):
```
langchain-openai>=0.2.0  # optional; omit if not using OpenAI embeddings
```

> Note: Minimum versions above are based on API patterns confirmed in research.
> Pin exact versions in `requirements.txt` once the environment is set up
> (`pip freeze > requirements.txt` after install). Do not ship unpinned versions.

---

## 2. Model Choices Confirmed

| Agent | Model | Rationale |
|-------|-------|-----------|
| Triage | `claude-haiku-4-5-20251001` | Low cost; simple classification; high volume |
| Compliance | `claude-sonnet-4-6` | Complex reasoning; exemption analysis |
| Response | `claude-sonnet-4-6` | Drafting formal letter; accuracy matters |

Token cost rates for `config.py`:

```python
TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}
```

> Verify against https://www.anthropic.com/pricing before implementation.

---

## 3. Cost Tracking — Updated Approach

LangChain provides `get_usage_metadata_callback` in `langchain_core.callbacks` — a
built-in context manager that returns per-model token counts after any LLM call.

**Decision:** Use `get_usage_metadata_callback` per agent call instead of a custom
`BaseCallbackHandler` subclass. The `cost_tracker.py` module wraps this into a
`CostTracker` class that accumulates per-agent records:

```python
from langchain_core.callbacks import get_usage_metadata_callback
from config import TOKEN_COSTS

class CostTracker:
    def __init__(self):
        self.records: list[dict] = []

    def track(self, agent_name: str, model: str, llm_call_fn, *args, **kwargs):
        with get_usage_metadata_callback() as cb:
            result = llm_call_fn(*args, **kwargs)
        usage = cb.usage_metadata.get(model, {})
        rates = TOKEN_COSTS.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            usage.get("input_tokens", 0) / 1000 * rates["input"] +
            usage.get("output_tokens", 0) / 1000 * rates["output"]
        )
        self.records.append({
            "agent": agent_name,
            "model": model,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": cost,
        })
        return result

    def summary(self) -> dict:
        by_agent = {}
        for r in self.records:
            ag = r["agent"]
            if ag not in by_agent:
                by_agent[ag] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
            by_agent[ag]["calls"] += 1
            by_agent[ag]["input_tokens"] += r["input_tokens"]
            by_agent[ag]["output_tokens"] += r["output_tokens"]
            by_agent[ag]["cost_usd"] += r["cost_usd"]
        return {"by_agent": by_agent, "total_usd": sum(r["cost_usd"] for r in self.records)}
```

Full primer with token-detail notes in `learning_materials/langchain-callbacks.md`.

**Update to `agent-tom-system-architecture.md`:** The `cost_tracker.py` description
should reflect this on consolidation.

---

## 4. Embedding Provider

**Default:** `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface`
- Downloaded to `~/.cache/huggingface/` on first use (~90 MB)
- Subsequent runs fully offline
- No API key required

**Fallback:** Set `EMBEDDING_PROVIDER=openai` in `.env` and provide `OPENAI_API_KEY`
- Use `langchain_openai.OpenAIEmbeddings(model="text-embedding-3-small")`
- `rag.py` detects `EMBEDDING_PROVIDER` env var and switches accordingly

---

## 5. Resolving Open Questions from Kickoff Prompt

### Q1: Testing patterns for agents (cost-effective)

**Decision:** Two-tier testing strategy

**Unit tests (zero cost):** Use LangChain's `FakeListChatModel` (from
`langchain_core.language_models.fake`) to inject fixed responses. Test that each agent:
- Parses the LLM response correctly into the expected Pydantic model
- Returns the correct fallback on error
- Calls `cost_tracker.track()` exactly once

```python
from langchain_core.language_models.fake import FakeListChatModel

fake_llm = FakeListChatModel(responses=['{"topic":"procurement","complexity":"high",...}'])
result = triage_agent("...request text...", fake_llm, tracker)
assert result.topic == "procurement"
```

**Integration tests (low cost):** Run the full pipeline against real haiku
(`claude-haiku-4-5-20251001`) on the 3 sample requests in `documents/foi_requests/`.
Haiku is cheap enough that 3 requests cost < $0.01 total. Assert on broad correctness
(topic in expected set, exemption section numbers present in compliance output).

**Do not use `claude-sonnet-4-6` in automated tests** — run sonnet only in manual
end-to-end checks.

### Q2: HITL presentation

**Resolved in `agent-tom-supervisor-hitl.md`.** Display format, interaction flow, and
audit trail schema are specified there. The key design choices:
- Rich evidence display (classification confidence, top-k RAG chunks with scores,
  compliance reasoning, full draft)
- Three-way decision: approve / reject / modify
- Modify flow collects multiline replacement text with a confirmation step
- Operator identity from `OPERATOR_ID` env var with runtime fallback prompt

### Q3: Caching near-duplicate FOIs

**Decision:** Out of scope for MVP. Mark as a stretch goal.

Reasoning: Implementing a similarity-based cache (compare incoming request to past
requests via embedding distance) adds complexity, requires a cache invalidation policy,
and is not required for the assessment rubric. The three sample requests are all
distinct and this is not tested.

Stretch goal note: could be implemented as a pre-pipeline step in `pipeline.py` that
checks embedding similarity against past `output/*.json` files before calling agents.

---

## 6. Logging Configuration

Python stdlib `logging` with a JSON formatter, configured in `main.py`:

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
```

All agent LLM calls emit a structured `INFO` log with `event`, `agent`, `model`,
`input_tokens`, `output_tokens`, `cost_usd` fields (see
`learning_materials/langchain-callbacks.md`).

---

## 7. Project Initialisation Checklist

Before writing any implementation code:

- [ ] Copy sample documents from `starter/documents/` to `solution/documents/`
- [ ] Create `solution/.env` from a `.env.example` template
- [ ] Confirm `ANTHROPIC_API_KEY` is set
- [ ] Run `pip install -r requirements.txt` in a virtual environment
- [ ] Run `python main.py index` — verify ChromaDB is created and chunk count > 0
- [ ] Run `python main.py process documents/foi_requests/request-001.txt` — verify
       pipeline runs end-to-end (stubs are fine at this point; confirm no import errors)
