from types import SimpleNamespace

import anthropic
import pytest
from opentelemetry.sdk.metrics import MeterProvider

import analyse
import telemetry


@pytest.fixture(autouse=True)
def _configure_telemetry_metrics():
    """analyse_response() calls telemetry.record_*() functions that need the
    module's metric instruments bound to a MeterProvider first (Task 2's
    configure_metrics) — without this, they're still None from telemetry.py's
    module load and every call raises AttributeError."""
    telemetry.configure_metrics(MeterProvider())


class FakeMessages:
    def __init__(self, message=None, error=None):
        self._message = message
        self._error = error

    def create(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._message


class FakeClient:
    def __init__(self, message=None, error=None):
        self.messages = FakeMessages(message=message, error=error)


def _fake_message(text, input_tokens=10, output_tokens=20):
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def test_analyse_response_success_returns_parsed_analysis():
    message = _fake_message(
        '{"summary": "neutral", "themes": ["privacy"], "sentiment": "mixed"}'
    )
    client = FakeClient(message=message)

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-1", "some text")

    assert outcome == "success"
    assert analysis == {
        "summary": "neutral",
        "themes": ["privacy"],
        "sentiment": "mixed",
    }
    assert spend_gbp > 0


def test_analyse_response_bad_json_returns_parse_error_not_raise():
    message = _fake_message("not valid json at all")
    client = FakeClient(message=message)

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-2", "some text")

    assert outcome == "parse_error"
    assert analysis is None
    assert spend_gbp > 0  # tokens were still spent on this call


def test_analyse_response_api_error_returns_api_error_not_raise():
    client = FakeClient(error=anthropic.AnthropicError("rate limited"))

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-3", "some text")

    assert outcome == "api_error"
    assert analysis is None
    assert spend_gbp == 0.0
