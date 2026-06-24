# Research Primer: langchain-anthropic — ChatAnthropic and Structured Output

**Source:** https://docs.langchain.com/oss/python/integrations/chat/anthropic  
**Retrieved:** 2026-06-24 via Context7 MCP  
**Relevance:** ChatAnthropic init, tool binding, structured output for FOI agents

---

## 1. Initialisation

```python
from langchain_anthropic import ChatAnthropic

# Triage agent (low cost, high volume)
llm_haiku = ChatAnthropic(model="claude-haiku-4-5-20251001")

# Compliance + response agents (complex reasoning)
llm_sonnet = ChatAnthropic(model="claude-sonnet-4-6")
```

`ANTHROPIC_API_KEY` is read automatically from the environment (via `python-dotenv` /
`load_dotenv()` in `main.py`).

---

## 2. Structured Output with Pydantic

`with_structured_output()` binds a Pydantic model and returns a chain that parses the
LLM response directly into a typed object. Under the hood it uses tool-calling for
Anthropic models (not JSON mode).

```python
from pydantic import BaseModel, Field
from typing import Literal
from langchain_anthropic import ChatAnthropic

class TriageResult(BaseModel):
    topic: str = Field(description="Primary subject area, e.g. 'procurement'")
    complexity: Literal["high", "medium", "low"]
    summary: str = Field(description="One-sentence summary of the request")
    confidence: float = Field(ge=0.0, le=1.0)

llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
structured_llm = llm.with_structured_output(TriageResult)

result: TriageResult = structured_llm.invoke(
    "Classify this FOI request: ..."
)
# result.topic, result.complexity, etc. are typed and validated
```

**Important:** The model sees the Pydantic field `description` strings as instructions —
write them clearly, as they guide the model's output.

---

## 3. Tool Binding (alternative to structured output)

For compliance/response agents that may call tools (e.g., RAG retrieval) as well as
return structured output, `bind_tools()` is available:

```python
model_with_tools = llm_sonnet.bind_tools([search_policy_tool])
response = model_with_tools.invoke(messages)
```

For this project, we pass RAG chunks directly in the prompt rather than as tool calls,
so `with_structured_output()` is the right choice for all three agents.

---

## 4. Token Usage Metadata

Token usage is available in two ways:

**From the response object directly:**
```python
result = llm.invoke("Hello")
print(result.usage_metadata)
# {"input_tokens": 8, "output_tokens": 21, "total_tokens": 29,
#  "input_token_details": {"cache_read": 0, "cache_creation": 0}}
```

**From streaming:**
```python
stream = llm.stream(messages)
full = next(stream)
for chunk in stream:
    full += chunk
print(full.usage_metadata)
# {"input_tokens": 25, "output_tokens": 11, "total_tokens": 36}
```

---

## 5. Cost Tracking Pattern (Updated)

LangChain provides `get_usage_metadata_callback` — a context manager that accumulates
token usage across all LLM calls within its scope, keyed by model name.

```python
from langchain_core.callbacks import get_usage_metadata_callback

with get_usage_metadata_callback() as cb:
    result = structured_llm.invoke(prompt)
# cb.usage_metadata:
# {"claude-haiku-4-5-20251001": {"input_tokens": 312, "output_tokens": 48, ...}}
```

**For per-agent cost tracking**, use a separate context manager per agent call and
compute cost immediately:

```python
TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

def compute_cost(usage_metadata: dict, model: str) -> float:
    rates = TOKEN_COSTS[model]
    usage = usage_metadata.get(model, {})
    return (
        usage.get("input_tokens", 0) / 1000 * rates["input"] +
        usage.get("output_tokens", 0) / 1000 * rates["output"]
    )

# In triage agent:
with get_usage_metadata_callback() as cb:
    triage_result = structured_llm.invoke(prompt)
triage_usage = cb.usage_metadata.get("claude-haiku-4-5-20251001", {})
triage_cost = compute_cost(cb.usage_metadata, "claude-haiku-4-5-20251001")
```

**Architecture note:** This replaces the `BaseCallbackHandler` subclass proposed in
`agent-tom-system-architecture.md`. The `cost_tracker.py` module should use
`get_usage_metadata_callback` instead. Update the architecture spec on consolidation.

---

## 6. Key Package

```
langchain-anthropic>=0.3.0
```

Install: `pip install langchain-anthropic`

No separate `anthropic` package install needed — `langchain-anthropic` pulls it in as a
dependency.
