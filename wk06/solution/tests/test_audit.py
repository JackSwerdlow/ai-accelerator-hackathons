"""Tests for the audit log module (Task 10).

All tests are offline — no network, no real API calls.
Tests use tmp_path for all file-writing cases.
"""

import importlib
import json
import re

import foi_system.audit as audit
from foi_system.audit import log_event, make_entry  # noqa: E402

# ---------------------------------------------------------------------------
# Test 1: JSONL file is append-only; both entries are present in order
# ---------------------------------------------------------------------------


def test_append_only_jsonl(tmp_path):
    """Two log_event calls to the same paths produce exactly 2 JSONL lines in order."""
    jsonl_path = tmp_path / "audit.jsonl"
    txt_path = tmp_path / "audit.txt"

    entry_a = make_entry("triage", "req-001", agent="triage", payload={"topic": "finance"})
    entry_b = make_entry("compliance", "req-002", agent="compliance", payload={"result": "ok"})

    log_event(entry_a, jsonl_path=jsonl_path, txt_path=txt_path)
    log_event(entry_b, jsonl_path=jsonl_path, txt_path=txt_path)

    lines = jsonl_path.read_text().strip().split("\n")
    assert len(lines) == 2, f"Expected 2 JSONL lines, got {len(lines)}"

    obj_a = json.loads(lines[0])
    obj_b = json.loads(lines[1])

    assert obj_a["request_id"] == "req-001"
    assert obj_b["request_id"] == "req-002"


# ---------------------------------------------------------------------------
# Test 2: Human-readable .txt file is written
# ---------------------------------------------------------------------------


def test_human_readable_txt_written(tmp_path):
    """log_event writes a .txt line containing timestamp, event_type, and request_id."""
    jsonl_path = tmp_path / "audit.jsonl"
    txt_path = tmp_path / "audit.txt"

    entry = make_entry("triage", "req-txt-42", agent="triage", payload={"topic": "staffing"})
    log_event(entry, jsonl_path=jsonl_path, txt_path=txt_path)

    txt_content = txt_path.read_text()
    assert entry.timestamp in txt_content
    assert entry.event_type in txt_content
    assert f"request={entry.request_id}" in txt_content


# ---------------------------------------------------------------------------
# Test 3: make_entry produces a valid ISO-8601-Z timestamp and correct request_id
# ---------------------------------------------------------------------------


def test_entry_has_timestamp_and_request_id():
    """make_entry returns AuditEntry with ISO-8601-Z timestamp and the given request_id."""
    entry = make_entry("triage", "req-xyz")

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", entry.timestamp), (
        f"Timestamp {entry.timestamp!r} does not match ISO-8601-Z pattern"
    )
    assert entry.request_id == "req-xyz"


# ---------------------------------------------------------------------------
# Test 4: Secrets are scrubbed from both JSONL and .txt outputs
# ---------------------------------------------------------------------------


def test_no_secrets_in_entry(tmp_path):
    """Secrets in nested payload are redacted; non-secret fields are preserved."""
    jsonl_path = tmp_path / "audit.jsonl"
    txt_path = tmp_path / "audit.txt"

    entry = make_entry(
        "decision",
        "req-1",
        payload={
            "api_key": "sk-abc-XYZ-leak",
            "result": "ok",
            "nested": {"token": "t-leak", "fine": 1},
        },
    )
    log_event(entry, jsonl_path=jsonl_path, txt_path=txt_path)

    jsonl_text = jsonl_path.read_text()
    txt_text = txt_path.read_text()

    # Secrets must not appear
    assert "sk-abc-XYZ-leak" not in jsonl_text
    assert "sk-abc-XYZ-leak" not in txt_text
    assert "t-leak" not in jsonl_text
    assert "t-leak" not in txt_text

    # Redaction marker must appear
    assert "[REDACTED]" in jsonl_text
    assert "[REDACTED]" in txt_text

    # Non-secret values must be preserved
    assert "ok" in jsonl_text  # result: "ok"
    assert "1" in jsonl_text  # fine: 1


# ---------------------------------------------------------------------------
# Test 5: Append-only across simulated runs (second call must not truncate)
# ---------------------------------------------------------------------------


def test_append_only_across_runs(tmp_path):
    """Files opened in 'a' mode: second log_event call appends, never truncates."""
    jsonl_path = tmp_path / "audit.jsonl"
    txt_path = tmp_path / "audit.txt"

    entry_a = make_entry("triage", "req-run-a", agent="triage")
    entry_b = make_entry("response", "req-run-b", operator="officer1")

    log_event(entry_a, jsonl_path=jsonl_path, txt_path=txt_path)

    # Simulate a "fresh run" by reloading the module (state is reset, but files persist)
    importlib.reload(audit)

    log_event(entry_b, jsonl_path=jsonl_path, txt_path=txt_path)

    jsonl_lines = jsonl_path.read_text().strip().split("\n")
    txt_lines = txt_path.read_text().strip().split("\n")

    assert len(jsonl_lines) == 2, f"Expected 2 JSONL lines after two runs, got {len(jsonl_lines)}"
    assert len(txt_lines) == 2, f"Expected 2 txt lines after two runs, got {len(txt_lines)}"

    # Line 1 belongs to entry_a, line 2 to entry_b
    assert "req-run-a" in jsonl_lines[0]
    assert "req-run-b" in jsonl_lines[1]
    assert "req-run-a" in txt_lines[0]
    assert "req-run-b" in txt_lines[1]
