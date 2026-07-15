"""Black-box, subprocess-driven resilience tests against today's real
solution/analyse.py (rewritten by a teammate mid-project - see EVAL_REPORT.md
for what changed and why these tests were rewritten to match). Run via the
real CLI (--input/--output/--state-file/--mode), redirected to a local mock
Anthropic server - never against the tracked solution/results.json.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_solution, start_solution  # noqa: E402


def test_malformed_json_produces_a_sentinel_row_not_a_crash(tmp_path, mock_llm_server):
    """R3/C1: one bad model response is turned into a PARSE_ERROR sentinel
    row and the run completes, rather than crashing the whole batch."""
    mock_llm_server.queue_json(summary="Row 1, fine.", themes=["trust"], sentiment="neutral")
    mock_llm_server.queue_malformed()
    mock_llm_server.queue_json(summary="Row 3, fine.", themes=["cost"], sentiment="neutral")

    result = run_solution(tmp_path, mock_llm_server, fixture_name="responses_malformed.csv")

    assert result.returncode == 0, f"expected the run to complete despite one bad row; stderr:\n{result.stderr}"
    assert result.results is not None and len(result.results) == 3
    bad_row = next(r for r in result.results if r["id"] == "2")
    assert bad_row["summary"] == "PARSE_ERROR"
    assert "parse_error" in bad_row
    good_row = next(r for r in result.results if r["id"] == "1")
    assert good_row["summary"] == "Row 1, fine."


def test_kill_mid_run_then_resume_recovers_completed_rows(tmp_path, mock_llm_server):
    """R1/R2: a crash partway through a sequential run does not lose
    already-completed results - they're checkpointed to the state file
    after every row - and restarting with the same input/model/mode
    resumes rather than re-analysing rows already done."""
    fixture = "responses_tiny.csv"  # 4 rows
    mock_llm_server.queue_delay_then_json(0.3, summary="row 1")
    mock_llm_server.queue_delay_then_json(10.0, summary="row 2 - never gets here, we kill first")

    proc, output_json, state_file = start_solution(tmp_path, mock_llm_server, fixture_name=fixture)
    time.sleep(1.2)  # let row 1 complete and checkpoint, then kill mid-row-2
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        proc.wait(timeout=5)

    assert state_file.exists(), "expected row 1's progress to be checkpointed to the state file before the kill"
    with open(state_file, encoding="utf-8") as f:
        state = json.load(f)
    assert len(state.get("progress", {})) >= 1, "expected at least row 1 in the checkpointed progress"
    assert not output_json.exists(), (
        "results.json is only written once, at the very end of a run - this is a "
        "sanity check that the kill really happened mid-run, not after completion"
    )

    calls_before_resume = mock_llm_server.request_count
    for _ in range(4):
        mock_llm_server.queue_json(summary="resumed", themes=["trust"], sentiment="neutral")

    # Same tmp_path + fixture_name -> _solution_args derives the identical
    # --input/--output/--state-file paths as the killed run used, so this
    # naturally resumes the same checkpoint rather than starting fresh.
    resumed = run_solution(tmp_path, mock_llm_server, fixture_name=fixture)
    assert resumed.returncode == 0, f"expected the resumed run to complete cleanly:\n{resumed.stderr}"
    assert resumed.results is not None and len(resumed.results) == 4

    calls_during_resume = mock_llm_server.request_count - calls_before_resume
    assert calls_during_resume <= 3, (
        f"expected the resumed run to skip the row(s) already completed and only call "
        f"the API for the remainder, but it made {calls_during_resume} calls"
    )


def test_sustained_api_failure_becomes_sentinel_rows_not_a_crash_or_hang(tmp_path, mock_llm_server):
    """R4: a sustained failure (mocked as a persistent 429) is caught per-row
    and turned into an API_ERROR sentinel rather than crashing the whole
    run or retrying forever - a stronger resilience posture than the
    original plan assumed (whole-batch failure), verified against what the
    rewrite actually does."""
    for _ in range(20):
        mock_llm_server.queue_error(status=429, message="rate limited - sustained outage")

    result = run_solution(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv", timeout=60)

    assert result.returncode == 0, f"expected the run to complete via sentinel rows, not crash:\n{result.stderr}"
    assert result.results is not None and len(result.results) == 4
    assert all(r["summary"] == "API_ERROR" for r in result.results), (
        "expected every row to fall back to an API_ERROR sentinel given a sustained failure"
    )
    assert mock_llm_server.request_count < 20, (
        "expected bounded retries per row against a sustained failure, not one that "
        "burns through every queued response"
    )
