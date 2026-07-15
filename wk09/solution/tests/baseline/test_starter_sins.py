"""Frozen baseline: proves the original prototype's failure modes, once.

Runs against `FROZEN_STARTER_SNAPSHOT` (a git-history copy of the *original*
starter/analyse.py, commit f7a35f5) rather than the live `starter/` directory.
starter/ was supposed to be read-only, but was patched out-of-band by another
contributor part-way through this project (checkpointing + a JSON try/except
were added directly to starter/analyse.py - see AI_LOG.md) - so the live
directory no longer reproduces the sin these tests exist to document. These
tests are never meant to be "fixed": if they ever start passing, that means
the frozen snapshot changed, which should not happen.
"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from conftest import FROZEN_STARTER_SNAPSHOT  # noqa: E402


def test_malformed_json_crashes_the_whole_run(tmp_path, mock_llm_server):
    """The brief's headline inherited flaw: one bad model response crashes
    the entire batch and every result computed so far is lost, because
    results are only written once, at the very end."""
    from conftest import run_analyse

    mock_llm_server.queue_json(summary="Row 1, fine.", themes=["trust"], sentiment="neutral")
    mock_llm_server.queue_malformed()
    mock_llm_server.queue_json(summary="Row 3, never reached.", themes=["cost"], sentiment="neutral")

    result = run_analyse(
        tmp_path,
        mock_llm_server,
        fixture_name="responses_malformed.csv",
        analyse_py=FROZEN_STARTER_SNAPSHOT,
    )

    assert result.returncode != 0, "expected the original script to crash on non-JSON model output"
    assert "JSONDecodeError" in result.stderr
    assert not result.results_path.exists(), (
        "expected zero results saved - the original script only writes results.json "
        "once, at the very end, so a mid-run crash loses everything computed so far"
    )
    # Only 2 of 3 rows were ever attempted - row 3 was never reached, and its
    # (would-be) result is gone along with row 1's, which *did* succeed.
    assert mock_llm_server.request_count == 2


def test_rerun_after_full_success_makes_the_same_api_calls_again(tmp_path, mock_llm_server):
    """README: "Re-running re-analyses everything, including rows it has
    already done." Proves this is true of the original script - a full,
    successful run followed by a second run makes the same number of API
    calls again, wasting real budget on rows already analysed."""
    from conftest import run_analyse

    fixture = "responses_tiny.csv"  # 4 rows, all benign

    for _ in range(4):
        mock_llm_server.queue_json(summary="ok", themes=["trust"], sentiment="neutral")
    first = run_analyse(tmp_path, mock_llm_server, fixture_name=fixture, analyse_py=FROZEN_STARTER_SNAPSHOT)
    assert first.returncode == 0
    assert first.results is not None
    assert len(first.results) == 4
    calls_after_first_run = mock_llm_server.request_count
    assert calls_after_first_run == 4

    # Re-run against the *same* run_dir/results.json using run_analyse again
    # would reset the data dir via a fresh tmp_path - instead, invoke the
    # script a second time directly against the same run_dir to prove the
    # existing results.json is ignored entirely.
    import subprocess
    import sys as _sys

    for _ in range(4):
        mock_llm_server.queue_json(summary="ok again", themes=["trust"], sentiment="neutral")
    proc = subprocess.run(
        [_sys.executable, str(FROZEN_STARTER_SNAPSHOT.resolve())],
        cwd=first.run_dir,
        env={
            "ANTHROPIC_API_KEY": "test-dummy-anthropic-key-not-real",
            "ANTHROPIC_BASE_URL": mock_llm_server.base_url,
            "PATH": __import__("os").environ.get("PATH", ""),
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert mock_llm_server.request_count == calls_after_first_run + 4, (
        "the original script re-analysed all 4 rows again on the second run, "
        "despite results.json already containing a complete, successful result set"
    )
