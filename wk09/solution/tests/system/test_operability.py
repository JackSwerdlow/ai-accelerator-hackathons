"""Black-box operability tests against today's real solution/analyse.py -
can someone who isn't the author run it from the README, and does it
survive two people running it at once? Always via explicit --input/
--output/--state-file paths under tmp_path - never against the tracked
solution/results.json (see EVAL_REPORT.md for why that matters here).
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import DUMMY_API_KEY, README_PATH, VIEWER_PY, run_solution  # noqa: E402


def test_readme_documents_the_real_current_cli(tmp_path, mock_llm_server):
    """O1/O2: the README's documented commands must still match what
    analyse.py actually accepts, and following them must produce results
    and a reachable viewer."""
    readme_text = README_PATH.read_text(encoding="utf-8")
    assert "python analyse.py" in readme_text
    assert "python viewer.py" in readme_text
    # sequential is the implicit default (bare "python analyse.py"), not
    # shown as an explicit flag - only concurrent/batch need "--mode X".
    for mode in ("concurrent", "batch"):
        assert f"--mode {mode}" in readme_text, f"README no longer documents --mode {mode}"

    for _ in range(4):
        mock_llm_server.queue_json(summary="ok", themes=["trust"], sentiment="neutral")
    result = run_solution(tmp_path, mock_llm_server, fixture_name="responses_tiny.csv")
    assert result.returncode == 0, f"README's documented analyse.py step failed:\n{result.stderr}"
    assert result.results is not None and len(result.results) == 4

    port_match = re.search(r"<host>:(\d+)", readme_text)
    assert port_match, "README no longer documents which port the viewer listens on"
    port = int(port_match.group(1))

    # viewer.py opens a bare "results.json" relative to its own cwd - point
    # cwd at tmp_path, where run_solution() just wrote the real output file.
    env = {"PATH": os.environ.get("PATH", "")}
    proc = subprocess.Popen(
        [sys.executable, str(VIEWER_PY.resolve())],
        cwd=tmp_path,
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


def test_two_concurrent_runs_against_the_same_files_do_not_corrupt_state(tmp_path, mock_llm_server):
    """S5: "The policy team asked if two people running it at once would
    cause problems. Haven't checked." This checks - and finds a real,
    intermittent bug (roughly 1 in 5-6 runs when reproduced manually, not a
    test-harness artifact): `_save_state`'s temp file
    (`state_file.with_suffix(".tmp")`) is the SAME path for both processes
    when they share a state file, so one process's write-then-rename can
    race the other's and crash with
    `FileNotFoundError: ... '.batch_state.tmp' -> '.batch_state.json'`
    (captured verbatim in EVAL_REPORT.md). This sharpens the README's own
    documented caveat ("the checkpoint is local... not shared") from
    "redundant work" to "can crash a run outright." Runs several trials
    since the race is timing-dependent, not deterministic every call."""
    from conftest import _write_fixture_csv

    analyse_py = Path(__file__).parent.parent.parent / "analyse.py"
    crashes = []

    for trial in range(6):
        input_csv = tmp_path / f"input_{trial}.csv"
        output_json = tmp_path / f"results_{trial}.json"
        state_file = tmp_path / f".batch_state_{trial}.json"
        _write_fixture_csv(input_csv, "responses_tiny.csv")

        for _ in range(8):  # up to 4 rows x 2 concurrent runs
            mock_llm_server.queue_json(summary="ok", themes=["trust"], sentiment="neutral")

        env = {
            "ANTHROPIC_API_KEY": DUMMY_API_KEY,
            "ANTHROPIC_BASE_URL": mock_llm_server.base_url,
            "PATH": os.environ.get("PATH", ""),
        }
        args = [
            sys.executable, str(analyse_py),
            "--input", str(input_csv), "--output", str(output_json), "--state-file", str(state_file),
            "--mode", "sequential",
        ]
        procs = [
            subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for _ in range(2)
        ]
        results = [(p.wait(timeout=30), p) for p in procs]
        for code, p in results:
            if code != 0:
                crashes.append((trial, code, p.stderr.read()[-1000:]))

    assert not crashes, (
        f"{len(crashes)} of 12 concurrent-run attempts crashed with a shared-state-file "
        f"race (checklist S5). First crash:\ntrial={crashes[0][0]} exit={crashes[0][1]}\n"
        f"{crashes[0][2]}"
    )
