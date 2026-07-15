"""Closes checklist C2: idempotent resume. Unit-level (fast, no subprocess)
complement to tests/system/test_resilience.py's kill-and-resume test - this
checks main()'s row-skipping logic directly against an existing results.json,
without needing to actually kill a process.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))


def _mock_response(text):
    return SimpleNamespace(content=text)


def test_rerunning_after_a_full_success_makes_no_new_api_calls(solution_module, monkeypatch, tmp_path):
    call_count = {"n": 0}

    def fake_invoke(prompt):
        call_count["n"] += 1
        return _mock_response('{"summary": "ok", "themes": ["trust"], "sentiment": "neutral"}')

    monkeypatch.setattr(solution_module, "llm", SimpleNamespace(invoke=fake_invoke))

    data_dir = tmp_path / "data"
    run_dir = tmp_path / "solution"
    data_dir.mkdir()
    run_dir.mkdir()
    (data_dir / "responses_sample.csv").write_text(
        "id,respondent_type,response_text\n1,individual,first\n2,individual,second\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(run_dir)
    solution_module.main()
    assert call_count["n"] == 2, "expected exactly one API call per row on the first run"

    call_count["n"] = 0
    solution_module.main()
    assert call_count["n"] == 0, (
        f"expected zero new API calls on a re-run after a full success, but made "
        f"{call_count['n']} - re-running must not re-analyse rows already done"
    )


def test_checkpoint_file_survives_a_round_trip(solution_module, monkeypatch, tmp_path):
    """The on-disk checkpoint format must be exactly what gets read back in
    on resume - if main() writes one shape and expects to read another, a
    resume would silently re-do everything (defeating the point of C2)."""
    monkeypatch.setattr(
        solution_module,
        "llm",
        SimpleNamespace(invoke=lambda prompt: _mock_response('{"summary": "ok", "themes": ["trust"], "sentiment": "neutral"}')),
    )
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "solution"
    data_dir.mkdir()
    run_dir.mkdir()
    (data_dir / "responses_sample.csv").write_text(
        "id,respondent_type,response_text\n1,individual,only row\n", encoding="utf-8"
    )
    monkeypatch.chdir(run_dir)
    solution_module.main()

    results_path = run_dir / "results.json"
    assert results_path.exists()
    with open(results_path, encoding="utf-8") as f:
        saved = json.load(f)
    assert len(saved) == 1
    assert saved[0]["id"] == "1"
    assert saved[0]["summary"] == "ok"
