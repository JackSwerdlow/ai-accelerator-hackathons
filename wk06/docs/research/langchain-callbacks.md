# Research Primer: LangChain Token Usage and Cost Tracking

**Source:** https://docs.langchain.com/oss/python/langchain/models  
**Retrieved:** 2026-06-24 via Context7 MCP  
**Relevance:** Per-agent cost tracking for the assessment rubric "Cost awareness" axis

---

## 1. Key Finding

LangChain now provides **built-in** token usage tracking via `UsageMetadataCallbackHandler`
and `get_usage_metadata_callback`. Writing a custom `BaseCallbackHandler` subclass is
no longer necessary for this use case.

**This supersedes the `cost_tracker.py` approach described in the starter scaffold.**
The architecture spec (`agent-tom-system-architecture.md`) should be updated on
consolidation to reflect this simpler pattern.

---

## 2. `get_usage_metadata_callback` (Context Manager)

The cleanest pattern for per-agent tracking:

```python
from langchain_core.callbacks import get_usage_metadata_callback

with get_usage_metadata_callback() as cb:
    result = llm.invoke(prompt)

# cb.usage_metadata is a dict keyed by model name:
# {
#   "claude-haiku-4-5-20251001": {
#       "input_tokens": 312,
#       "output_tokens": 48,
#       "total_tokens": 360,
#       "input_token_details": {"cache_read": 0, "cache_creation": 0}
#   }
# }
```

Because each call is wrapped in its own `with` block, usage is naturally scoped
per-agent — no cross-contamination.

---

## 3. `UsageMetadataCallbackHandler` (Handler Object)

When you need to accumulate across multiple calls before inspecting:

```python
from langchain.chat_models import init_chat_model
from langchain_core.callbacks import UsageMetadataCallbackHandler

llm = init_chat_model(model="claude-haiku-4-5-20251001")

callback = UsageMetadataCallbackHandler()
result_1 = llm.invoke("Hello", config={"callbacks": [callback]})
result_2 = llm.invoke("World", config={"callbacks": [callback]})

print(callback.usage_metadata)
# Accumulates across all calls, keyed by model name
```

---

## 4. Recommended Pattern for This Project

```python
# config.py — token cost rates
TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

# cost_tracker.py
from langchain_core.callbacks import get_usage_metadata_callback
from config import TOKEN_COSTS

class CostTracker:
    def __init__(self):
        self.records: list[dict] = []

    def track(self, agent_name: str, model: str, llm_call_fn, *args, **kwargs):
        """Wrap an LLM call and record its cost."""
        with get_usage_metadata_callback() as cb:
            result = llm_call_fn(*args, **kwargs)

        usage = cb.usage_metadata.get(model, {})
        rates = TOKEN_COSTS.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            usage.get("input_tokens", 0) / 1000 * rates["input"] +
            usage.get("output_tokens", 0) / 1000 * rates["output"]
        )
        record = {
            "agent": agent_name,
            "model": model,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": cost,
        }
        self.records.append(record)
        return result, record

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
        return {
            "by_agent": by_agent,
            "total_usd": sum(r["cost_usd"] for r in self.records),
        }
```

---

## 5. Claude-Specific Token Details

For Claude models, `input_token_details` includes:
- `cache_read` — tokens served from the prompt cache (cheaper)
- `cache_creation` — tokens written to the prompt cache

These are relevant if prompt caching is enabled. For this project's scope (no explicit
caching), they will typically be 0.

---

## 6. Logging Token Usage for Audit

Each agent call should also be logged as structured JSON for the audit trail:

```python
import logging
import json

logger = logging.getLogger(__name__)

def log_agent_call(agent: str, model: str, usage: dict, cost: float):
    logger.info(json.dumps({
        "event": "llm_call",
        "agent": agent,
        "model": model,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": cost,
    }))
```

Configure the root logger with a JSON formatter in `main.py` before any agent calls.
