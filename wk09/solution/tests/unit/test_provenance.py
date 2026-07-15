"""Closes checklist GOV3 (model version pinned, not a floating alias) and
checks GOV6 (results.json retains enough provenance to answer "why was this
response classified this way" for an FOI request or audit, without needing
to re-run the analysis) - still a real, confirmed gap in the rewrite.
"""
import re
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import ANALYSE_PY  # noqa: E402

# A dated/pinned Anthropic model id looks like claude-<family>-<version>-<YYYYMMDD>
# (e.g. claude-sonnet-5-20260115) or an explicit "-v" snapshot marker - a bare
# "claude-sonnet-5" with no date/snapshot suffix is a floating alias.
PINNED_MODEL_RE = re.compile(r"claude-[a-z0-9\-]+-\d{8}")


def test_model_string_is_a_pinned_dated_snapshot_not_a_floating_alias():
    source = ANALYSE_PY.read_text(encoding="utf-8")
    model_match = re.search(r'DEFAULT_MODEL\s*=\s*"([^"]+)"', source)
    assert model_match, "could not find a DEFAULT_MODEL = \"...\" string in analyse.py to check"
    model_value = model_match.group(1)
    assert PINNED_MODEL_RE.match(model_value), (
        f"DEFAULT_MODEL={model_value!r} looks like a floating alias, not a pinned "
        f"dated snapshot - if the provider repoints this alias later, a published "
        f"government summary's classifications could shift silently with no code "
        f"change and no record of why"
    )


class FakeSyncClient:
    def __init__(self, responder):
        self.messages = SimpleNamespace(create=responder)


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
