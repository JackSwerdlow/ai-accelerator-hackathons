#!/usr/bin/env python3
"""
Spend dashboard — graphs of AI cost over time, split by agent/model/purpose.

Usage:
    python spend/plot_spend.py              # full 4-panel dashboard
    python spend/plot_spend.py --by agent   # single breakdown (agent/model/purpose/calltype)
"""

import argparse
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

_ROOT = Path(__file__).resolve().parent


def _load():
    files = sorted(_ROOT.glob("ai-spend-log-*.csv"))
    if not files:
        raise SystemExit("No spend logs found. Run analyse.py or install the Stop hook first.")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], utc=True)
    df["CostGBP"] = pd.to_numeric(df["CostGBP"], errors="coerce").fillna(0)
    return df.sort_values("Timestamp").reset_index(drop=True)


def _bar(ax, df, col, title):
    totals = df.groupby(col)["CostGBP"].sum().sort_values()
    totals.plot.barh(ax=ax, color="steelblue", edgecolor="white")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("£")
    ax.set_ylabel("")
    for bar, val in zip(ax.patches, totals):
        ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2,
                f"£{val:.3f}", va="center", fontsize=8)


def _timeline(ax, df):
    for agent, grp in df.groupby("AgentName"):
        ts = grp.set_index("Timestamp")["CostGBP"].cumsum()
        ts.plot(ax=ax, label=agent, marker="o", markersize=4, linewidth=1.5)
    ax.set_title("Cumulative spend over time", fontsize=10)
    ax.set_ylabel("£ (cumulative)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%H:%M"))
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)


def main():
    parser = argparse.ArgumentParser(description="AI spend dashboard")
    parser.add_argument("--by", choices=["agent", "model", "purpose", "calltype"],
                        help="Show a single breakdown panel instead of the full dashboard")
    args = parser.parse_args()

    df = _load()
    total = df["CostGBP"].sum()
    col_map = {"agent": "AgentName", "model": "Model",
               "purpose": "Purpose", "calltype": "CallType"}

    if args.by:
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.suptitle(f"Spend by {args.by}  —  total £{total:.4f}", fontsize=13)
        _bar(ax, df, col_map[args.by], "")
    else:
        fig = plt.figure(figsize=(13, 8))
        fig.suptitle(f"AI Spend Dashboard  —  total £{total:.4f}", fontsize=14, y=0.98)
        gs = fig.add_gridspec(2, 3, hspace=0.45, wspace=0.4)
        _timeline(fig.add_subplot(gs[0, :]), df)
        _bar(fig.add_subplot(gs[1, 0]), df, "AgentName", "By agent")
        _bar(fig.add_subplot(gs[1, 1]), df, "Purpose",   "By purpose")
        _bar(fig.add_subplot(gs[1, 2]), df, "Model",     "By model")

    plt.show()


if __name__ == "__main__":
    main()
