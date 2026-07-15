# USD per million tokens — update when Anthropic pricing changes.
# Source: Anthropic pricing page, checked 2026-07-15.
MODELS = {
    "claude-fable-5":    {"input": 10.00, "output": 50.00},
    "claude-opus-4-8":   {"input":  5.00, "output": 25.00},
    "claude-opus-4-7":   {"input":  5.00, "output": 25.00},
    "claude-opus-4-6":   {"input":  5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input":  1.00, "output":  5.00},
    # starter/analyse.py uses "claude-sonnet-5" which is not a valid model ID —
    # mapped here as a safe fallback; update analyse.py to claude-sonnet-4-6
    "claude-sonnet-5":   {"input":  3.00, "output": 15.00},
}

GBP_PER_USD = 0.79  # approximate; update as needed


def cost_gbp(model: str, input_tokens: int, output_tokens: int) -> float:
    p = MODELS.get(model, MODELS["claude-sonnet-4-6"])
    usd = (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000
    return round(usd * GBP_PER_USD, 4)
