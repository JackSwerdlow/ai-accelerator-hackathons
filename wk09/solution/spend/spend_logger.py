import csv
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

AGENT_NAME = os.environ.get("AGENT_NAME", socket.gethostname())

# CSV written at solution/ level alongside analyse.py, not inside spend/
_LOG_DIR = Path(__file__).parent.parent
_LOG_PATH = _LOG_DIR / f"ai-spend-log-{AGENT_NAME}.csv"

_HEADERS = [
    "Timestamp", "AgentName", "CallType", "Purpose",
    "Model", "UploadTokens", "DownloadTokens", "CostGBP",
]


def log_row(
    call_type: str,
    purpose: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_gbp: float,
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
            model,
            input_tokens,
            output_tokens,
            cost_gbp,
        ])
