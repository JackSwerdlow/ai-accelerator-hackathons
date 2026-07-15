"""Regression tests for the spend-tracking Stop hook's double-counting bug.

Root cause (see AI_LOG.md for the full diagnosis): ~/.claude/spend_tracking_state.json
is shared across every concurrent Claude Code session/worktree in this
environment, and the old code did a non-atomic, unlocked read-modify-write
on it. A lost update reverted a session's line cursor, causing a huge
already-billed swath of the transcript to be reprocessed and re-billed -
one real session logged 73.5M and 118.2M "upload tokens" for two ordinary
turns as a result.

These tests NEVER touch the real ~/.claude/spend_tracking_state.json or a
real ai-spend-log CSV - every path is monkeypatched to tmp_path first.
"""
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).parent.parent.parent / "spend" / "log_claude_code_session.py"


@pytest.fixture
def hook(tmp_path, monkeypatch):
    """Import log_claude_code_session.py fresh, with all persistent paths
    redirected under tmp_path - never the real ~/.claude state or CSV."""
    monkeypatch.setenv("AGENT_NAME", "test-agent")
    spec = importlib.util.spec_from_file_location("log_claude_code_session_under_test", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    module.STATE_FILE = tmp_path / "spend_tracking_state.json"
    module.LOCK_FILE = tmp_path / "spend_tracking_state.lock"
    module.LOG_PATH = tmp_path / "ai-spend-log-test.csv"

    yield module
    sys.modules.pop(spec.name, None)


def _fake_assistant_entry(msg_id, input_tokens=0, output_tokens=0, cache_creation=0, cache_read=0):
    return {
        "type": "assistant",
        "message": {
            "id": msg_id,
            "model": "claude-sonnet-5",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_creation_input_tokens": cache_creation,
                "cache_read_input_tokens": cache_read,
            },
        },
    }


def test_parse_usage_skips_ids_already_billed_in_a_prior_invocation(hook):
    """The core fix: even if a stale line cursor causes an already-billed
    message to reappear in a "new" batch, it must not be billed twice."""
    entries = [
        _fake_assistant_entry("msg_1", input_tokens=10, cache_read=1000),
        _fake_assistant_entry("msg_2", input_tokens=20, cache_read=2000),
    ]
    # msg_1 was already billed in a previous invocation (simulating a stale
    # from_line that re-included its line in this batch).
    already_billed = {"msg_1"}

    inp, out, cache_creation, cache_read, model, newly_billed = hook._parse_usage(entries, already_billed)

    assert cache_read == 2000, "msg_1's tokens must not be re-billed"
    assert newly_billed == {"msg_2"}


def test_full_reprocessing_after_a_lost_state_update_does_not_double_bill(hook, tmp_path):
    """End-to-end reproduction of the actual incident: build a transcript,
    run the hook once, then simulate a lost state update (from_line
    reverted to 0, as a losing writer in the old race would cause) and run
    it again - the total billed across both runs must equal the true total,
    not double it."""
    transcript = tmp_path / "transcript.jsonl"
    entries = [
        _fake_assistant_entry(f"msg_{i}", input_tokens=5, cache_read=10_000 + i)
        for i in range(5)
    ]
    transcript.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    state = {}
    from_line, already_billed = hook._session_state(state, "session-1")
    new_entries, total_lines = hook._read_new_entries(str(transcript), from_line)
    inp1, out1, cc1, cr1, model, newly_billed1 = hook._parse_usage(new_entries, already_billed)
    state["session-1"] = {
        "from_line": total_lines,
        "billed_ids": list(already_billed | newly_billed1),
    }

    # Simulate the old bug: a concurrent writer's lost update reverts the
    # cursor to 0 (but - critically, this is the fix - NOT the billed_ids,
    # which the real hook always merges forward from what it read under
    # the lock, so a reverted cursor alone can no longer cause double
    # billing).
    state["session-1"]["from_line"] = 0

    from_line2, already_billed2 = hook._session_state(state, "session-1")
    new_entries2, total_lines2 = hook._read_new_entries(str(transcript), from_line2)
    inp2, out2, cc2, cr2, model2, newly_billed2 = hook._parse_usage(new_entries2, already_billed2)

    true_total_cache_read = sum(10_000 + i for i in range(5))
    assert cr1 + cr2 == true_total_cache_read, (
        f"expected the true total ({true_total_cache_read}) even after a reverted cursor, "
        f"got {cr1} + {cr2} = {cr1 + cr2}"
    )
    assert cr2 == 0, "the second run should have found nothing new to bill at all"


def test_state_migrates_old_line_cursor_only_format(hook):
    """Existing ~/.claude/spend_tracking_state.json entries are plain ints
    (line cursor only, no billed_ids) - must not crash or reset to 0."""
    state = {"old-session": 459}
    from_line, billed_ids = hook._session_state(state, "old-session")
    assert from_line == 459
    assert billed_ids == set()


def test_state_lock_serialises_concurrent_invocations(hook, tmp_path):
    """Proves the lock actually excludes concurrent critical sections,
    rather than just existing unused."""
    order = []
    barrier_entered = threading.Event()

    def critical_section(label, hold_seconds):
        with hook._StateLock():
            order.append(f"{label}-enter")
            if label == "first":
                barrier_entered.set()
                time.sleep(hold_seconds)
            order.append(f"{label}-exit")

    t1 = threading.Thread(target=critical_section, args=("first", 0.3))
    t1.start()
    barrier_entered.wait(timeout=2)
    t2 = threading.Thread(target=critical_section, args=("second", 0))
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert order == ["first-enter", "first-exit", "second-enter", "second-exit"], (
        f"expected the lock to fully serialise the two critical sections, got {order}"
    )
