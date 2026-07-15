"""Black-box, subprocess-driven resilience tests against solution/analyse.py.

Run the real script exactly as a user would (`python analyse.py` from
solution/), redirected to a local mock Anthropic server. These test the
*desired* behaviour per plans/eval-test-plan-agent-tom.md - solution/analyse.py
is currently an unrefined copy of the original starter/analyse.py, so most
of these are expected to FAIL right now. That's the correct starting state
(see the plan's "Baseline finding"), not a bug in the tests: this is the red
baseline these tests exist to turn green as solution/analyse.py is refined.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_analyse, start_analyse  # noqa: E402


def test_malformed_json_does_not_crash_the_batch(tmp_path, mock_llm_server):
    """Closes checklist R3/C1: one bad model response is flagged and
    skipped, not allowed to crash the whole run."""
    mock_llm_server.queue_json(summary="Row 1, fine.", themes=["trust"], sentiment="neutral")
    mock_llm_server.queue_malformed()
    mock_llm_server.queue_json(summary="Row 3, fine.", themes=["cost"], sentiment="neutral")

    result = run_analyse(tmp_path, mock_llm_server, fixture_name="responses_malformed.csv")

    assert result.returncode == 0, (
        f"expected the run to complete despite one bad row; "
        f"stderr:\n{result.stderr}"
    )
    assert result.results is not None, "expected results.json to exist even though one row failed"
    assert len(result.results) == 3, "expected all 3 rows present in the output, including the bad one"
    bad_row = next(r for r in result.results if r["id"] == "2")
    assert bad_row.get("summary") != "Row 3, fine.", "the bad row must not silently disappear"


def test_kill_mid_run_then_resume_recovers_completed_rows(tmp_path, mock_llm_server):
    """Closes checklist R1/R2: a crash partway through a run does not lose
    already-completed results, and restarting finishes the remainder
    without re-calling the API for rows already done."""
    fixture = "responses_tiny.csv"  # 4 rows
    mock_llm_server.queue_delay_then_json(0.3, summary="row 1")
    mock_llm_server.queue_delay_then_json(5.0, summary="row 2 - never gets here, we kill first")

    proc, run_dir = start_analyse(tmp_path, mock_llm_server, fixture_name=fixture)
    time.sleep(1.0)  # let row 1 complete, then kill mid-row-2
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        proc.wait(timeout=5)

    results_path = run_dir / "results.json"
    assert results_path.exists(), (
        "expected at least row 1's result to have been checkpointed to disk "
        "before the process was killed"
    )
    with open(results_path, encoding="utf-8") as f:
        partial_results = json.load(f)
    assert len(partial_results) >= 1, "expected row 1's result to survive the kill"

    calls_before_resume = mock_llm_server.request_count
    for _ in range(4):
        mock_llm_server.queue_json(summary="resumed", themes=["trust"], sentiment="neutral")

    import os
    import subprocess

    from conftest import ANALYSE_PY, DUMMY_API_KEY

    resumed = subprocess.run(
        [sys.executable, str(ANALYSE_PY.resolve())],
        cwd=run_dir,
        env={
            "ANTHROPIC_API_KEY": DUMMY_API_KEY,
            "ANTHROPIC_BASE_URL": mock_llm_server.base_url,
            "PATH": os.environ.get("PATH", ""),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert resumed.returncode == 0, f"expected the resumed run to complete cleanly:\n{resumed.stderr}"
    with open(results_path, encoding="utf-8") as f:
        final_results = json.load(f)
    assert len(final_results) == 4, "expected all 4 rows present after resuming"

    calls_during_resume = mock_llm_server.request_count - calls_before_resume
    assert calls_during_resume <= 3, (
        f"expected the resumed run to skip the row(s) already completed and only call "
        f"the API for the remainder, but it made {calls_during_resume} calls"
    )


def test_permanent_api_failure_is_reported_clearly_not_retried_forever(tmp_path, mock_llm_server):
    """Closes checklist R4/DEP2: a sustained failure is reported clearly and
    the process exits, rather than retrying indefinitely or hanging."""
    for _ in range(10):
        mock_llm_server.queue_error(status=429, message="rate limited - sustained outage")

    result = run_analyse(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv", timeout=60)

    assert result.returncode != 0, "expected a clear failure, not a hang or silent success"
    assert mock_llm_server.request_count <= 10, (
        "expected a bounded number of retries against a sustained failure, not an "
        "unbounded retry loop"
    )
