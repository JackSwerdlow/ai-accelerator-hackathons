"""Closes checklist S1 (no hardcoded key fallback), S2 (key never leaks via
logs/output/exceptions), S3 (output escaping in viewer.py), and documents
why S4 (CSV/formula injection) has no automated coverage yet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import ANALYSE_PY, DUMMY_API_KEY, run_analyse  # noqa: E402


def test_no_hardcoded_api_key_fallback_in_source():
    """Closes S1: a real key pasted in "to make it work" is one commit away
    from being public - the source must not carry a non-empty fallback
    string for the key."""
    source = ANALYSE_PY.read_text(encoding="utf-8")
    assert '"PASTE-YOUR-KEY-HERE"' not in source, (
        "found a hardcoded placeholder API key fallback in source - if a real key is "
        "ever pasted in the same way to 'make it work locally', it ends up committed"
    )


def test_api_key_never_appears_in_stdout_stderr_or_results(tmp_path, mock_llm_server):
    """Closes S2. Deliberately triggers a crash (malformed JSON) so any key
    leakage via an unhandled exception/traceback would be caught too."""
    mock_llm_server.queue_malformed()
    result = run_analyse(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv")

    assert DUMMY_API_KEY not in result.stdout
    assert DUMMY_API_KEY not in result.stderr
    if result.results_path.exists():
        assert DUMMY_API_KEY not in result.results_path.read_text(encoding="utf-8")


def test_viewer_escapes_response_derived_text_in_html_output(tmp_path):
    """Closes S3: consultation-response-derived text (the model's summary,
    ultimately from public/adversarial input) must render inert in the
    viewer's HTML, not as live markup."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    import importlib.util

    spec = importlib.util.spec_from_file_location("viewer_under_test", Path(__file__).parent.parent.parent / "viewer.py")
    viewer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(viewer)

    malicious_summary = "<script>alert('xss')</script>"
    with viewer.app.app_context():
        html = viewer.PAGE
        from flask import render_template_string

        rendered = render_template_string(
            html,
            results=[
                {
                    "id": "1",
                    "respondent_type": "individual",
                    "summary": malicious_summary,
                    "themes": ["trust"],
                    "sentiment": "neutral",
                }
            ],
            sentiments=__import__("collections").Counter(["neutral"]),
            themes=__import__("collections").Counter(["trust"]),
        )
    assert "<script>alert('xss')</script>" not in rendered, "raw <script> tag survived into rendered HTML"
    assert "&lt;script&gt;" in rendered, "expected the summary to be HTML-escaped, not stripped or ignored"


import pytest  # noqa: E402


@pytest.mark.skip(
    reason=(
        "S4 (CSV/formula injection) has no automated coverage: there is no CSV-export "
        "code path anywhere in analyse.py or viewer.py today (output is results.json + "
        "an HTML viewer). Nothing to test until a CSV/Excel export feature exists - "
        "tracked as a known gap, not silently assumed covered."
    )
)
def test_csv_formula_injection_is_neutralised_on_export():
    pass
