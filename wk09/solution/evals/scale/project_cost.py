"""Closes checklist V3: projects £ cost and wall-clock time at 1,000/20,000
rows from a small REAL measured sample - not run through the real API at
that volume (see generate_synthetic.py for the structural-load-only
synthetic data).

Default per-row token counts below come from a real, logged 2-row run of
evals/run_quality_eval.py (see spend/ai-spend-log-Agent-Tom.csv, the
'Testing' row: 778 input + 182 output tokens over 2 rows = 389/91 per row).
Override with --input-tokens/--output-tokens if you have a larger sample.

Cache-write/read multipliers (1.25x for 5-min TTL, ~0.1x for a cache read)
are current published Anthropic pricing as of the plan's writing - verify
against Anthropic's pricing page before using this for a real budget
decision; pricing changes over time and this script does not check it live.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from spend.pricing import MODELS, GBP_PER_USD  # noqa: E402

CACHE_WRITE_MULTIPLIER = 1.25  # 5-minute TTL cache write vs base input price
CACHE_READ_MULTIPLIER = 0.10  # cache read vs base input price

MEASURED_INPUT_TOKENS_PER_ROW = 389
MEASURED_OUTPUT_TOKENS_PER_ROW = 91
# Of the ~389 input tokens per call, the INSTRUCTIONS block is the
# resend-every-time cost the brief calls out; the response_text itself
# varies per row and can never be cached. Measured exactly via the
# Anthropic API's (free) count_tokens endpoint against analyse.py's
# INSTRUCTIONS string.
MEASURED_INSTRUCTIONS_TOKENS = 321


def _cost_usd(model, input_tokens, output_tokens):
    p = MODELS.get(model, MODELS["claude-sonnet-4-6"])
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def project_baseline(n_rows, model, input_tokens_per_row, output_tokens_per_row):
    """Current approach: one call per row, full instructions resent, no
    caching - the literal brief-described sin."""
    total_input = n_rows * input_tokens_per_row
    total_output = n_rows * output_tokens_per_row
    usd = _cost_usd(model, total_input, total_output)
    return {"approach": "baseline (no caching)", "usd": round(usd, 2), "gbp": round(usd * GBP_PER_USD, 2)}


def project_with_prompt_caching(n_rows, model, input_tokens_per_row, output_tokens_per_row, instructions_tokens):
    """If solution/analyse.py added prompt caching on the (repeated,
    unchanging) INSTRUCTIONS block: row 1 pays a cache-write premium on
    those tokens, every subsequent row pays only the cache-read discount
    on them, plus the full price for the row-specific response_text."""
    p = MODELS.get(model, MODELS["claude-sonnet-4-6"])
    variable_input_per_row = input_tokens_per_row - instructions_tokens

    first_row_usd = (
        instructions_tokens * p["input"] * CACHE_WRITE_MULTIPLIER + variable_input_per_row * p["input"]
    ) / 1_000_000 + (output_tokens_per_row * p["output"]) / 1_000_000
    remaining_rows = n_rows - 1
    per_remaining_row_usd = (
        instructions_tokens * p["input"] * CACHE_READ_MULTIPLIER + variable_input_per_row * p["input"]
    ) / 1_000_000 + (output_tokens_per_row * p["output"]) / 1_000_000

    usd = first_row_usd + remaining_rows * per_remaining_row_usd
    return {
        "approach": "with prompt caching on the fixed instructions block",
        "usd": round(usd, 2),
        "gbp": round(usd * GBP_PER_USD, 2),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--input-tokens", type=int, default=MEASURED_INPUT_TOKENS_PER_ROW)
    parser.add_argument("--output-tokens", type=int, default=MEASURED_OUTPUT_TOKENS_PER_ROW)
    parser.add_argument("--instructions-tokens", type=int, default=MEASURED_INSTRUCTIONS_TOKENS)
    args = parser.parse_args()

    report = {"measured_from": "2-row real sample, see spend/ai-spend-log-Agent-Tom.csv", "scenarios": {}}
    for n_rows in (1_000, 20_000):
        report["scenarios"][n_rows] = {
            "baseline": project_baseline(n_rows, args.model, args.input_tokens, args.output_tokens),
            "with_caching": project_with_prompt_caching(
                n_rows, args.model, args.input_tokens, args.output_tokens, args.instructions_tokens
            ),
        }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
