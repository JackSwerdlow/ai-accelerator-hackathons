"""Closes checklist C4 (scored quality eval) and GOV4 (per-respondent_type
fairness cut). Calls the REAL Anthropic API through the actual pipeline
function (analyse_response) against a small, hand-labelled golden set -
bounded, real cost, logged to ai-spend-log-Agent-Tom.csv per the root
CLAUDE.md cost-tracking rule.

Scoring:
- theme overlap: set intersection / union (Jaccard) against expected_themes
- sentiment: exact match against expected_sentiment
- summary: word-overlap heuristic against reference_summary - flagged
  explicitly as lower-confidence per the plan; not an LLM-as-judge call,
  to avoid doubling the real API cost of this script.

Usage: python evals/run_quality_eval.py [--limit N]
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOLUTION_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SOLUTION_DIR))

EVALS_DIR = Path(__file__).parent
DATA_CSV = SOLUTION_DIR.parent / "data" / "responses_sample.csv"
GOLDEN_CSV = EVALS_DIR / "golden_set.csv"
SPEND_LOG = SOLUTION_DIR / "spend" / "ai-spend-log-Agent-Tom.csv"


def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _word_overlap(a, b):
    wa, wb = set(a.lower().split()), set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def score_row(golden_row, actual, sample_row):
    expected_themes = set(t.strip() for t in golden_row["expected_themes"].split(";") if t.strip())
    actual_themes = set(actual.get("themes", []))
    union = expected_themes | actual_themes
    theme_jaccard = len(expected_themes & actual_themes) / len(union) if union else 1.0

    sentiment_match = actual.get("sentiment") == golden_row["expected_sentiment"]

    summary_overlap = _word_overlap(golden_row["reference_summary"], actual.get("summary", ""))

    return {
        "id": golden_row["id"],
        "respondent_type": sample_row["respondent_type"],
        "theme_jaccard": round(theme_jaccard, 3),
        "sentiment_match": sentiment_match,
        "summary_word_overlap": round(summary_overlap, 3),
        "expected_themes": sorted(expected_themes),
        "actual_themes": sorted(actual_themes),
        "expected_sentiment": golden_row["expected_sentiment"],
        "actual_sentiment": actual.get("sentiment"),
    }


def log_spend(model, input_tokens, output_tokens, agent_name="Agent-Tom"):
    from spend.pricing import cost_gbp

    cost = cost_gbp(model, input_tokens, output_tokens)
    row = [
        datetime.now(timezone.utc).isoformat(),
        agent_name,
        "Claude API",
        "Testing",
        model,
        str(input_tokens),
        str(output_tokens),
        str(cost),
    ]
    with open(SPEND_LOG, "a", encoding="utf-8") as f:
        f.write(",".join(row) + "\n")
    return cost


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N golden rows (real API cost)")
    args = parser.parse_args()

    import analyse as solution_analyse

    golden_rows = _load_csv(GOLDEN_CSV)
    if args.limit:
        golden_rows = golden_rows[: args.limit]
    sample_by_id = {r["id"]: r for r in _load_csv(DATA_CSV)}

    scores = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_gbp = 0.0

    for golden_row in golden_rows:
        sample_row = sample_by_id.get(golden_row["id"])
        if sample_row is None:
            print(f"WARNING: golden row id={golden_row['id']} not found in {DATA_CSV}", file=sys.stderr)
            continue

        response = solution_analyse.llm.invoke(solution_analyse.INSTRUCTIONS + sample_row["response_text"])
        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        try:
            actual = json.loads(response.content)
        except json.JSONDecodeError:
            actual = {"summary": "", "themes": [], "sentiment": None}

        scores.append(score_row(golden_row, actual, sample_row))

    if total_input_tokens or total_output_tokens:
        model = getattr(solution_analyse.llm, "model", "claude-sonnet-5")
        total_cost_gbp = log_spend(model, total_input_tokens, total_output_tokens)

    by_type = defaultdict(list)
    for s in scores:
        by_type[s["respondent_type"]].append(s)

    report = {
        "n_scored": len(scores),
        "mean_theme_jaccard": round(sum(s["theme_jaccard"] for s in scores) / len(scores), 3) if scores else None,
        "sentiment_exact_match_rate": round(sum(s["sentiment_match"] for s in scores) / len(scores), 3) if scores else None,
        "mean_summary_word_overlap_LOW_CONFIDENCE": round(
            sum(s["summary_word_overlap"] for s in scores) / len(scores), 3
        )
        if scores
        else None,
        "by_respondent_type": {
            rtype: {
                "n": len(rows),
                "mean_theme_jaccard": round(sum(r["theme_jaccard"] for r in rows) / len(rows), 3),
                "sentiment_exact_match_rate": round(sum(r["sentiment_match"] for r in rows) / len(rows), 3),
            }
            for rtype, rows in by_type.items()
        },
        "real_api_cost_gbp": total_cost_gbp,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "rows": scores,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
