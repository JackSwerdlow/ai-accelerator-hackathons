"""Single LLM seam for the FOI multi-agent system.

All structured-output and retry logic lives here — nowhere else.
Model-fallback and cost-downgrade hooks attach here in later tasks (Task 12).
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from foi_system.config import MODEL_TIERS


def build_llm(agent: str, temperature: float = 0.0) -> ChatAnthropic:
    """Build a bare ChatAnthropic for the given agent tier.

    max_retries=0 disables the Anthropic SDK's own retry so .with_retry() in
    structured() is the SINGLE retry mechanism in the system.
    """
    return ChatAnthropic(model=MODEL_TIERS[agent], temperature=temperature, max_retries=0)  # type: ignore[call-arg]


def structured(llm: ChatAnthropic, schema: type[BaseModel]) -> Runnable:
    """Wrap llm with structured output (json_schema) then a single retry wrapper.

    Composition order is critical: with_structured_output FIRST (on the bare
    ChatAnthropic), THEN .with_retry() — reversing the order fails because
    RunnableRetry has no with_structured_output method.
    """
    return llm.with_structured_output(schema, method="json_schema").with_retry(
        stop_after_attempt=4, wait_exponential_jitter=True
    )
