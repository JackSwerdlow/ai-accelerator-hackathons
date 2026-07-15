"""Regression coverage for evals/scale/, written test-after (both scripts
were run and manually sanity-checked before this test was added).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from evals.scale.generate_synthetic import generate  # noqa: E402
from evals.scale.project_cost import project_baseline, project_with_prompt_caching  # noqa: E402


def test_generate_synthetic_produces_the_requested_row_count():
    rows = generate(1000)
    assert len(rows) == 1000
    assert {r["id"] for r in rows} == {str(i) for i in range(1, 1001)}
    assert all(r["response_text"] for r in rows)


def test_caching_projection_is_always_cheaper_than_baseline_at_scale():
    baseline = project_baseline(20_000, "claude-sonnet-5", 389, 91)
    cached = project_with_prompt_caching(20_000, "claude-sonnet-5", 389, 91, 321)
    assert cached["gbp"] < baseline["gbp"], (
        "prompt caching on a large, unchanging instructions block should reduce cost "
        "at scale, not increase it"
    )
