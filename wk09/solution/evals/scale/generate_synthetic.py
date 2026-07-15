"""Generates a synthetic large CSV by perturbing the 40 real rows, for
structural load testing (memory, checkpoint-file growth, wall-clock scaling
of non-API code paths) at 1,000/20,000-row scale WITHOUT spending real API
budget on that many rows. Never sent through the real API at this volume -
see plans/eval-test-plan-agent-tom.md component 5.
"""
import argparse
import csv
import random
from pathlib import Path

REAL_SAMPLE = Path(__file__).parent.parent.parent.parent / "data" / "responses_sample.csv"

FILLER_CLAUSES = [
    "In addition, I would note that timelines matter as much as principles.",
    "This view is shared by several people I know in a similar position.",
    "I raise this because it directly affects how I would use the service.",
    "None of this should be read as opposition to the underlying goal.",
    "I would welcome a follow-up consultation once a draft design exists.",
]


def _perturb(text, rng):
    """Lightly reword a real response by shuffling sentence order and
    appending a filler clause - enough variation to avoid literal
    duplicates without needing another real model call."""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    rng.shuffle(sentences)
    reworded = ". ".join(sentences)
    if not reworded.endswith("."):
        reworded += "."
    return reworded + " " + rng.choice(FILLER_CLAUSES)


def generate(n_rows, seed=42):
    rng = random.Random(seed)
    with open(REAL_SAMPLE, newline="", encoding="utf-8") as f:
        real_rows = list(csv.DictReader(f))

    rows = []
    for i in range(1, n_rows + 1):
        base = real_rows[(i - 1) % len(real_rows)]
        rows.append(
            {
                "id": str(i),
                "respondent_type": base["respondent_type"],
                "response_text": _perturb(base["response_text"], rng) if i > len(real_rows) else base["response_text"],
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n_rows", type=int)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rows = generate(args.n_rows, seed=args.seed)
    with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "respondent_type", "response_text"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic rows to {args.output_csv}")


if __name__ == "__main__":
    main()
