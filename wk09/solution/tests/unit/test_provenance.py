"""Closes checklist GOV3 (model version pinned, not a floating alias) and
GOV6 (results.json retains enough provenance to answer "why was this
response classified this way" for an FOI request or audit, without
needing to re-run the analysis).
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
    model_match = re.search(r'model\s*=\s*"([^"]+)"', source)
    assert model_match, "could not find a model= string in analyse.py to check"
    model_value = model_match.group(1)
    assert PINNED_MODEL_RE.match(model_value), (
        f"model={model_value!r} looks like a floating alias, not a pinned dated "
        f"snapshot - if the provider repoints this alias later, a published "
        f"government summary's classifications could shift silently with no "
        f"code change and no record of why"
    )


def _mock_response(text):
    return SimpleNamespace(content=text)


def test_results_retain_enough_provenance_to_answer_why_without_rerunning(solution_module, monkeypatch):
    """GOV6: an FOI request or audit asking "why was response N classified
    this way" should be answerable from results.json alone - the raw model
    output and the model version used, not just the final parsed fields."""
    monkeypatch.setattr(
        solution_module,
        "llm",
        SimpleNamespace(invoke=lambda prompt: _mock_response('{"summary": "s", "themes": ["trust"], "sentiment": "neutral"}')),
    )
    result = solution_module.analyse_response("some response text")
    assert "model" in result or "model_version" in result, (
        "expected the per-row result to record which model version produced it"
    )
    assert "raw_response" in result or "raw_model_output" in result, (
        "expected the per-row result to retain the raw model output for later audit, "
        "not just the parsed summary/themes/sentiment"
    )
