#!/usr/bin/env python3
"""Aggregate all per-agent spend CSVs and print a summary.

Run from anywhere:
    python solution/spend/show_spend.py
"""

import csv
from collections import defaultdict
from pathlib import Path

# CSVs live at solution/ level
_ROOT = Path(__file__).resolve().parent


def load_rows():
    rows = []
    for path in sorted(_ROOT.glob("ai-spend-log-*.csv")):
        with open(path, newline="") as f:
            rows.extend(list(csv.DictReader(f)))
    return rows


def summarise(rows):
    by_agent = defaultdict(float)
    by_model = defaultdict(float)
    by_type = defaultdict(float)
    total = 0.0
    for r in rows:
        cost = float(r.get("CostGBP") or 0)
        by_agent[r["AgentName"]] += cost
        by_model[r["Model"]] += cost
        by_type[r["CallType"]] += cost
        total += cost
    return by_agent, by_model, by_type, total


def _table(title, data):
    print(f"\n{title:=<45}")
    for k, v in sorted(data.items()):
        print(f"  {k:<30} £{v:.4f}")


def main():
    rows = load_rows()
    if not rows:
        print("No spend logs found. Run analyse.py or add a manual entry first.")
        return

    by_agent, by_model, by_type, total = summarise(rows)
    _table("BY AGENT", by_agent)
    _table("BY MODEL", by_model)
    _table("BY CALL TYPE", by_type)
    print(f"\n{'TOTAL':=<45}")
    print(f"  {'Grand total':<30} £{total:.4f}")
    print(f"  {len(rows)} rows from {len(by_agent)} agent(s)\n")


if __name__ == "__main__":
    main()
