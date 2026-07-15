"""Closes checklist V1 (per-run cost visible) and MON2 (cost guardrail).

Neither capability exists in solution/analyse.py yet, so both tests are
expected to fail right now - this is the TDD spec for adding them.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import run_solution  # noqa: E402

COST_LINE_RE = re.compile(r"(tokens?|£|cost)", re.IGNORECASE)


def test_run_reports_its_own_total_cost(tmp_path, mock_llm_server):
    """Distinct from evals/scale/project_cost.py's projection-from-a-sample:
    this asserts the pipeline reports what a *specific real run* actually
    cost, in its own stdout/output - "numbers, not vibes" for the run you
    just did, not just a forecast of a future one."""
    for _ in range(4):
        mock_llm_server.queue_json(
            summary="ok", themes=["trust"], sentiment="neutral", input_tokens=120, output_tokens=40
        )
    result = run_solution(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv")

    assert result.returncode == 0
    cost_lines = [line for line in result.stdout.splitlines() if COST_LINE_RE.search(line)]
    assert cost_lines, (
        "expected analyse.py's stdout to include a total token/cost summary for "
        "this run; got no matching lines in:\n" + result.stdout
    )
    assert any(re.search(r"\d", line) for line in cost_lines), (
        "expected the cost summary to include an actual number, not just the word "
        "'cost'/'tokens'"
    )


def test_run_stops_once_a_spend_cap_is_exceeded(tmp_path, mock_llm_server):
    """A hard cap that stops and warns rather than continuing silently to
    the end of a large, expensive batch - guards against a runaway retry
    loop or an accidental full re-run burning real shared budget."""
    for _ in range(4):
        mock_llm_server.queue_json(
            summary="ok", themes=["trust"], sentiment="neutral", input_tokens=100_000, output_tokens=50_000
        )
    result = run_solution(
        tmp_path,
        mock_llm_server,
        fixture_name="responses_tiny.csv",
        extra_env={"MAX_SPEND_GBP": "0.01"},
    )

    assert mock_llm_server.request_count < 4, (
        "expected the run to stop before processing all 4 rows once the configured "
        "spend cap was exceeded, but it made all 4 calls anyway"
    )
    stop_lines = [line for line in result.stdout.splitlines() if "spend" in line.lower() or "cap" in line.lower()]
    assert stop_lines, (
        "expected a clear message explaining the run stopped because of the spend "
        "cap, got no matching lines in:\n" + result.stdout
    )
