"""Audit log module for the FOI multi-agent system.

Writes every pipeline event to two output files in append-only mode:
  - PRIMARY:   JSONL (one ``AuditEntry`` JSON object per line) for compliance queries.
  - SECONDARY: Human-readable ``.txt`` (one summarised line per entry) for on-call review.

No secrets are ever written — ``make_entry`` scrubs any payload key whose lowercased
name contains a substring listed in ``_SECRET_KEY_PATTERNS`` before the entry is stored
or serialised.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from foi_system.models import AuditEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_JSONL_PATH: Path = Path("./output/audit_trail.jsonl")
DEFAULT_TXT_PATH: Path = Path("./output/audit_trail.txt")

# Field-name patterns whose values must be redacted from any audit payload before writing.
# Case-insensitive substring match on the dict key. NEVER trust callers to scrub.
_SECRET_KEY_PATTERNS: tuple[str, ...] = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "passwd",
    "auth",
    "credential",
    "private_key",
)

_REDACTED_VALUE: str = "[REDACTED]"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scrub_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict with secret values replaced by ``_REDACTED_VALUE``.

    Walks recursively into nested dicts and lists of dicts.
    The original ``payload`` object is NOT mutated.
    """
    result: dict[str, Any] = {}
    for key, value in payload.items():
        if any(pattern in key.lower() for pattern in _SECRET_KEY_PATTERNS):
            result[key] = _REDACTED_VALUE
        elif isinstance(value, dict):
            result[key] = _scrub_payload(value)
        elif isinstance(value, list):
            result[key] = [
                _scrub_payload(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def make_entry(
    event_type: str,
    request_id: str,
    *,
    agent: str | None = None,
    operator: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEntry:
    """Build an ``AuditEntry`` with an ISO 8601 UTC timestamp and a scrubbed payload.

    Args:
        event_type: Stage or event label (e.g. "triage", "compliance", "decision").
        request_id: Unique identifier for the FOI request being processed.
        agent:      Name of the agent producing this event, or ``None``.
        operator:   Human operator identifier, or ``None``.
        payload:    Arbitrary metadata dict; secrets are scrubbed before storage.

    Returns:
        A fully populated ``AuditEntry`` ready for ``log_event``.
    """
    timestamp = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    scrubbed = _scrub_payload(payload) if payload else {}
    return AuditEntry(
        timestamp=timestamp,
        request_id=request_id,
        event_type=event_type,
        agent=agent,
        operator=operator,
        payload=scrubbed,
    )


def format_entry_human(entry: AuditEntry) -> str:
    """Return one human-readable single-line summary (no trailing newline).

    Format (single line, fields separated by two spaces)::

        <timestamp>  <event_type>  request=<request_id>  agent=<agent|->
        operator=<operator|->  <payload-summary>

    ``<payload-summary>`` is a compact ``key=value`` join of the (already-scrubbed) payload.
    Nested values are rendered via f-string interpolation (one-line ``str()``/``__repr__``).
    """
    agent_str = entry.agent if entry.agent is not None else "-"
    operator_str = entry.operator if entry.operator is not None else "-"
    payload_summary = " ".join(f"{k}={v}" for k, v in entry.payload.items())
    fixed = (
        f"{entry.timestamp}  {entry.event_type}  "
        f"request={entry.request_id}  agent={agent_str}  operator={operator_str}"
    )
    if payload_summary:
        return f"{fixed}  {payload_summary}"
    return fixed


def log_event(
    entry: AuditEntry,
    *,
    jsonl_path: str | Path = DEFAULT_JSONL_PATH,
    txt_path: str | Path = DEFAULT_TXT_PATH,
) -> None:
    """Append one JSONL line AND one human-readable line for ``entry``.

    - JSONL line: ``entry.model_dump_json()`` + ``"\\n"`` (PRIMARY).
    - Human line: a single rendered line (SECONDARY) — see ``format_entry_human``.
    - Files are opened in append mode (``"a"``) — NEVER truncated, NEVER reset across runs.
    - Parent directories are created if missing (``mkdir parents=True, exist_ok=True``).
    """
    jsonl_path = Path(jsonl_path)
    txt_path = Path(txt_path)

    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(entry.model_dump_json() + "\n")

    with txt_path.open("a", encoding="utf-8") as fh:
        fh.write(format_entry_human(entry) + "\n")
