import telemetry


def test_redact_snippet_leaves_short_text_untouched():
    assert telemetry._redact_snippet("short text") == "short text"


def test_redact_snippet_truncates_long_text():
    long_text = "x" * 500
    result = telemetry._redact_snippet(long_text, max_len=80)
    assert len(result) < 500
    assert result.startswith("x" * 80)
    assert "500 chars total" in result


def test_redact_snippet_never_returns_full_text_over_limit():
    long_text = "SECRET " * 50
    result = telemetry._redact_snippet(long_text, max_len=20)
    assert long_text not in result
