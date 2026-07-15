"""Black-box operability tests: can someone who isn't the author run this
from the README alone, and does it survive two people running it at once?
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import ANALYSE_PY, DUMMY_API_KEY, README_PATH, VIEWER_PY, run_analyse  # noqa: E402


def test_readme_running_it_steps_produce_results_and_a_reachable_viewer(tmp_path, mock_llm_server):
    """Closes checklist O2: the automated form of "someone who isn't you
    could run it, from your README, tomorrow." Extracts the commands from
    the README's "Running it" section and checks they still match what
    actually exists (`python analyse.py` then `python viewer.py`)."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    assert "python analyse.py" in readme_text, "README no longer documents how to run the analyser"
    assert "python viewer.py" in readme_text, "README no longer documents how to run the viewer"

    for _ in range(4):
        mock_llm_server.queue_json(summary="ok", themes=["trust"], sentiment="neutral")
    result = run_analyse(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv")
    assert result.returncode == 0, f"README's documented analyse.py step failed:\n{result.stderr}"
    assert result.results is not None and len(result.results) == 4

    port_match = re.search(r"localhost:(\d+)", readme_text)
    assert port_match, "README no longer documents which port the viewer listens on"
    port = int(port_match.group(1))

    env = {"PATH": os.environ.get("PATH", "")}
    proc = subprocess.Popen(
        [sys.executable, str(VIEWER_PY.resolve())],
        cwd=result.run_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        import urllib.error
        import urllib.request

        reachable = False
        for _ in range(20):
            time.sleep(0.25)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1)
                reachable = True
                break
            except (urllib.error.URLError, OSError):
                continue
        assert reachable, "viewer.py never became reachable on the README-documented port"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def test_two_concurrent_runs_do_not_corrupt_results(tmp_path, mock_llm_server):
    """Closes checklist S5: "The policy team asked if two people running it
    at once would cause problems. Haven't checked." - this checks."""
    from conftest import _write_fixture_csv

    data_dir = tmp_path / "data"
    run_dir = tmp_path / "solution"
    data_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_fixture_csv(data_dir / "responses_sample.csv", "responses_tiny.csv")

    for _ in range(8):  # 4 rows x 2 concurrent runs
        mock_llm_server.queue_json(summary="ok", themes=["trust"], sentiment="neutral")

    env = {
        "ANTHROPIC_API_KEY": DUMMY_API_KEY,
        "ANTHROPIC_BASE_URL": mock_llm_server.base_url,
        "PATH": os.environ.get("PATH", ""),
    }
    procs = [
        subprocess.Popen(
            [sys.executable, str(ANALYSE_PY.resolve())],
            cwd=run_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    outcomes = [p.wait(timeout=30) for p in procs]

    results_path = run_dir / "results.json"
    assert results_path.exists(), "expected results.json to exist after two concurrent runs"
    with open(results_path, encoding="utf-8") as f:
        raw = f.read()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    assert parsed is not None, (
        "results.json is not valid JSON after two concurrent runs wrote to it "
        "at the same time - the file was corrupted by the race"
    )
    assert all(o == 0 for o in outcomes), "expected both concurrent runs to exit cleanly"
