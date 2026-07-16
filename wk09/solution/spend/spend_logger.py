import csv
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

AGENT_NAME = os.environ.get("AGENT_NAME", socket.gethostname())

# CSV written alongside this file in spend/
_LOG_DIR = Path(__file__).resolve().parent
_LOG_PATH = _LOG_DIR / f"ai-spend-log-{AGENT_NAME}.csv"

# Input-side tokens are split into three columns because they're priced
# differently (fresh input at the full rate, cache writes at 1.25x, cache
# reads at 0.1x) - a single combined total can't be re-priced or audited
# later if the rate table changes, only the fresh/write/read split can.
_HEADERS = [
    "Timestamp", "AgentName", "CallType", "Purpose", "Description", "Model",
    "FreshInputTokens", "CacheCreationTokens", "CacheReadTokens", "OutputTokens",
    "CostGBP",
]

# Separate from the general per-agent log above: this one is only for actual
# runs of analyse.py (the production tool), so "what did the tool cost" and
# "what did the AI assistance cost" can be read independently. Filename still
# matches the ai-spend-log-*.csv glob show_spend.py/plot_spend.py use, so team
# totals still include it - it's a separate file, not a separate ledger.
_ANALYSIS_LOG_PATH = _LOG_DIR / f"ai-spend-log-{AGENT_NAME}-analysis-runs.csv"
_ANALYSIS_HEADERS = [
    "Timestamp", "AgentName", "CallType", "Purpose", "Description", "Model", "RunMode",
    "FreshInputTokens", "CacheCreationTokens", "CacheReadTokens", "OutputTokens",
    "CostGBP",
]


def log_row(
    call_type: str,
    purpose: str,
    model: str,
    fresh_input_tokens: int,
    cache_creation_tokens: int,
    cache_read_tokens: int,
    output_tokens: int,
    cost_gbp: float,
    description: str = "",
) -> None:
    write_header = not _LOG_PATH.exists()
    with _LOG_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(_HEADERS)
        w.writerow([
            datetime.now(timezone.utc).isoformat(),
            AGENT_NAME,
            call_type,
            purpose,
            description,
            model,
            fresh_input_tokens,
            cache_creation_tokens,
            cache_read_tokens,
            output_tokens,
            cost_gbp,
        ])


def log_analysis_run(
    mode: str,
    purpose: str,
    model: str,
    fresh_input_tokens: int,
    cache_creation_tokens: int,
    cache_read_tokens: int,
    output_tokens: int,
    cost_gbp: float,
    description: str = "",
) -> None:
    """Log one completed analyse.py run (sequential/concurrent/batch)."""
    write_header = not _ANALYSIS_LOG_PATH.exists()
    with _ANALYSIS_LOG_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(_ANALYSIS_HEADERS)
        w.writerow([
            datetime.now(timezone.utc).isoformat(),
            AGENT_NAME,
            "Claude API",
            purpose,
            description,
            model,
            mode,
            fresh_input_tokens,
            cache_creation_tokens,
            cache_read_tokens,
            output_tokens,
            cost_gbp,
        ])
