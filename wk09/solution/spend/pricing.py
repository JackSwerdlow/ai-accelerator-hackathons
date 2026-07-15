# USD per million tokens — update when Anthropic pricing changes.
# Source: Anthropic pricing page, checked 2026-07-15.
MODELS = {
    "claude-fable-5":    {"input": 10.00, "output": 50.00},
    "claude-opus-4-8":   {"input":  5.00, "output": 25.00},
    "claude-opus-4-7":   {"input":  5.00, "output": 25.00},
    "claude-opus-4-6":   {"input":  5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input":  1.00, "output":  5.00},
    # claude-sonnet-5 IS a valid, current model ID (the previous comment here
    # claiming otherwise was wrong). Its standard rate is $3.00/$15.00, but an
    # introductory rate of $2.00/$10.00 applies through 2026-08-31 (today is
    # 2026-07-15 - the introductory rate is in effect right now). Revert to
    # {"input": 3.00, "output": 15.00} after that date.
    "claude-sonnet-5":   {"input":  2.00, "output": 10.00},
}

GBP_PER_USD = 0.79  # approximate; update as needed

BATCH_DISCOUNT = 0.5          # Anthropic Message Batches API: 50% off standard token pricing
CACHE_WRITE_MULTIPLIER = 1.25  # ephemeral (5-min) cache writes cost 1.25x the standard input rate
CACHE_READ_MULTIPLIER = 0.1    # cache hits cost 0.1x the standard input rate


def cost_gbp(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    batch: bool = False,
) -> float:
    p = MODELS.get(model, MODELS["claude-sonnet-4-6"])
    usd = (
        input_tokens * p["input"]
        + cache_creation_tokens * p["input"] * CACHE_WRITE_MULTIPLIER
        + cache_read_tokens * p["input"] * CACHE_READ_MULTIPLIER
        + output_tokens * p["output"]
    ) / 1_000_000
    if batch:
        usd *= BATCH_DISCOUNT
    return round(usd * GBP_PER_USD, 4)
