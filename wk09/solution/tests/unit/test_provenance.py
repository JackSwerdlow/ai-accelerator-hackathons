"""Closes checklist GOV3 (model version auditable) and GOV6 (results.json
retains enough provenance to answer "why was this response classified this
way" for an FOI request or audit, without needing to re-run the analysis).

GOV3 correction (2026-07-15, verified via a real, free `client.models.list()`
call - see AI_LOG.md): the original test here assumed a "pinned" model looks
like `claude-<family>-<version>-<YYYYMMDD>` and a bare name like
`claude-sonnet-5` is a risky floating alias. Checking the actual model list
showed every CURRENT-generation model (`claude-sonnet-5`, `claude-opus-4-8`,
`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-opus-4-6`, `claude-fable-5`)
has no separate dated-snapshot id at all - only OLDER models
(`claude-opus-4-5-20251101`, `claude-haiku-4-5-20251001`, ...) do. There is
no dated string to "pin" `claude-sonnet-5` to. The achievable version of
GOV3's underlying concern - being able to prove which model actually
produced a given result, regardless of whether the identifier itself can be
frozen - is what GOV6 already requires: recording `model` per row. The two
checks below verify that, not a nonexistent naming convention.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))


class FakeSyncClient:
    def __init__(self, responder):
        self.messages = SimpleNamespace(create=responder)


def test_model_actually_used_is_recorded_per_row(solution_module):
    """GOV3 (corrected scope): since claude-sonnet-5 cannot be pinned to a
    dated snapshot id (none exists for this model), the achievable
    mitigation is recording which model string actually produced each
    result - so a later change in what "claude-sonnet-5" means is at least
    visible in old results, even if it can't be prevented at request time."""

    def responder(**kwargs):
        content = [SimpleNamespace(type="text", text='{"summary": "s", "themes": ["trust"], "sentiment": "neutral"}')]
        usage = SimpleNamespace(
            input_tokens=10, output_tokens=5, cache_creation_input_tokens=0, cache_read_input_tokens=0
        )
        return SimpleNamespace(content=content, usage=usage, model="claude-sonnet-5")

    client = FakeSyncClient(responder)
    row = {"id": "1", "respondent_type": "individual", "response_text": "some response text"}
    merged, _usage = solution_module.call_single_sync(client, row, "claude-sonnet-5", 500)

    assert merged.get("model") == "claude-sonnet-5", (
        "expected the per-row result to record the exact model string used for that row"
    )


def test_results_retain_enough_provenance_to_answer_why_without_rerunning(solution_module):
    """GOV6: an FOI request or audit asking "why was response N classified
    this way" should be answerable from results.json alone - the raw model
    output and the model version used, not just the final parsed fields."""

    def responder(**kwargs):
        content = [SimpleNamespace(type="text", text='{"summary": "s", "themes": ["trust"], "sentiment": "neutral"}')]
        usage = SimpleNamespace(
            input_tokens=10, output_tokens=5, cache_creation_input_tokens=0, cache_read_input_tokens=0
        )
        return SimpleNamespace(content=content, usage=usage, model="claude-sonnet-5")

    client = FakeSyncClient(responder)
    row = {"id": "1", "respondent_type": "individual", "response_text": "some response text"}
    merged, _usage = solution_module.call_single_sync(client, row, "claude-sonnet-5", 500)

    assert "model" in merged or "model_version" in merged, (
        "expected the per-row result to record which model version produced it"
    )
    assert "raw_response" in merged or "raw_model_output" in merged, (
        "expected the per-row result to retain the raw model output for later audit, "
        "not just the parsed summary/themes/sentiment"
    )


def test_provenance_is_retained_even_on_a_parse_error(solution_module):
    """The raw model output is most valuable for auditing exactly the rows
    that DIDN'T parse cleanly - a PARSE_ERROR sentinel must not discard the
    raw text that caused it."""

    def responder(**kwargs):
        content = [SimpleNamespace(type="text", text="not json at all, sorry")]
        usage = SimpleNamespace(
            input_tokens=10, output_tokens=5, cache_creation_input_tokens=0, cache_read_input_tokens=0
        )
        return SimpleNamespace(content=content, usage=usage, model="claude-sonnet-5")

    client = FakeSyncClient(responder)
    row = {"id": "1", "respondent_type": "individual", "response_text": "some response text"}
    merged, _usage = solution_module.call_single_sync(client, row, "claude-sonnet-5", 500)

    assert merged["summary"] == "PARSE_ERROR"
    assert merged.get("model") == "claude-sonnet-5"
    raw = merged.get("raw_response") or merged.get("raw_model_output")
    assert raw and "not json at all" in raw, (
        "expected the raw (unparseable) model output to survive into the sentinel row, "
        "not just the fact that parsing failed"
    )
