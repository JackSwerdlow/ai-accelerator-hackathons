"""Shared fixtures for the Consultation Insights eval/test suite.

See plans/eval-test-plan-agent-tom.md for the architecture these fixtures
support, and EVAL_REPORT.md for why there are two different subprocess
runners below. In short: `solution/analyse.py` was substantially rewritten
by a teammate partway through this work (sequential/concurrent/batch modes,
prompt caching, checkpoint-and-resume, explicit --input/--output/--state-file
flags) - a big improvement, but a different CLI than the one this test
suite was originally built against. `run_solution`/`start_solution` target
today's real CLI; `run_analyse`/`start_analyse` remain for the frozen
baseline suite, which intentionally runs the *original* prototype's
cwd-relative-path interface (see FROZEN_STARTER_SNAPSHOT) and must not be
"fixed" to match the new one.

Both redirect the client to a local mock server via `ANTHROPIC_BASE_URL`
(confirmed supported by inspecting the installed `anthropic` package's
source directly - `Anthropic.__init__` reads
`os.environ.get("ANTHROPIC_BASE_URL")` when no explicit `base_url` is passed;
this holds for both the raw `anthropic` client the new analyse.py uses and
the `langchain_anthropic` wrapper the frozen snapshot uses, since both sit
on top of the same underlying SDK).
"""
import http.server
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

SOLUTION_DIR = Path(__file__).parent.parent
STARTER_DIR = SOLUTION_DIR.parent / "starter"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
ANALYSE_PY = SOLUTION_DIR / "analyse.py"
STARTER_ANALYSE_PY = STARTER_DIR / "analyse.py"
# starter/ was supposed to be a read-only, frozen reference of "the sin" but
# was patched out-of-band by another contributor (see AI_LOG.md) - so the
# baseline suite runs against this git-history snapshot of the *original*
# starter/analyse.py (commit f7a35f5, before that patch) instead of the live
# starter/ directory, which no longer reproduces the original crash.
FROZEN_STARTER_SNAPSHOT = FIXTURES_DIR / "starter_analyse_original_snapshot.py"
VIEWER_PY = SOLUTION_DIR / "viewer.py"
README_PATH = SOLUTION_DIR / "README.md"

DUMMY_API_KEY = "test-dummy-anthropic-key-not-real"


def _message_response(text, input_tokens=50, output_tokens=20):
    """A minimal, valid Anthropic Messages API response body."""
    return {
        "id": "msg_test_000",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-5",
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


class _Behavior:
    """One queued response for the mock server to hand back."""

    def __init__(self, status=200, body=None, delay=0.0):
        self.status = status
        self.body = body
        self.delay = delay


class MockAnthropicServer:
    """A local stand-in for api.anthropic.com's /v1/messages endpoint.

    Behaviors are queued in the order requests are expected to arrive -
    since analyse.py processes rows strictly in order, "the Nth request"
    maps predictably to "the Nth row of the fixture CSV".
    """

    def __init__(self):
        self._queue = []
        self._default_text = json.dumps(
            {"summary": "A generic response.", "themes": ["trust"], "sentiment": "neutral"}
        )
        self.request_count = 0
        self.request_bodies = []
        self._lock = threading.Lock()
        handler = self._make_handler()
        self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    @property
    def base_url(self):
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def queue_text(self, text, input_tokens=50, output_tokens=20):
        """Queue a successful response whose content is exactly `text`."""
        self._queue.append(
            _Behavior(status=200, body=_message_response(text, input_tokens, output_tokens))
        )

    def queue_json(self, summary="A response.", themes=None, sentiment="neutral", input_tokens=50, output_tokens=20):
        """Queue a successful, well-formed analysis JSON payload."""
        payload = {"summary": summary, "themes": themes or ["trust"], "sentiment": sentiment}
        self.queue_text(json.dumps(payload), input_tokens=input_tokens, output_tokens=output_tokens)

    def queue_malformed(self, text="Sure, here is my analysis: not actually JSON at all!"):
        """Queue a 200 response whose content is *not* valid JSON."""
        self._queue.append(_Behavior(status=200, body=_message_response(text)))

    def queue_error(self, status=429, message="rate limited"):
        """Queue an HTTP error response (e.g. 429 rate-limit, 500 server error)."""
        self._queue.append(
            _Behavior(
                status=status,
                body={"type": "error", "error": {"type": "overloaded_error", "message": message}},
            )
        )

    def queue_delay_then_json(self, delay_seconds, **kwargs):
        payload = json.dumps(
            {
                "summary": kwargs.get("summary", "Delayed response."),
                "themes": kwargs.get("themes", ["trust"]),
                "sentiment": kwargs.get("sentiment", "neutral"),
            }
        )
        self._queue.append(_Behavior(status=200, body=_message_response(payload), delay=delay_seconds))

    def _make_handler(self):
        server = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # keep test output clean

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                with server._lock:
                    server.request_count += 1
                    try:
                        server.request_bodies.append(json.loads(raw))
                    except json.JSONDecodeError:
                        server.request_bodies.append({"_raw": raw.decode("utf-8", "replace")})
                    behavior = server._queue.pop(0) if server._queue else None

                if behavior is None:
                    body = _message_response(server._default_text)
                    status = 200
                else:
                    if behavior.delay:
                        time.sleep(behavior.delay)
                    body = behavior.body
                    status = behavior.status

                encoded = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return Handler

    def shutdown(self):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)


@pytest.fixture
def mock_llm_server():
    server = MockAnthropicServer()
    yield server
    server.shutdown()


class AnalyseRun:
    """A completed (or crashed) invocation of analyse.py in an isolated cwd."""

    def __init__(self, returncode, stdout, stderr, run_dir):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.run_dir = run_dir  # <tmp>/solution - the cwd analyse.py ran in
        self.results_path = run_dir / "results.json"

    @property
    def results(self):
        if not self.results_path.exists():
            return None
        with open(self.results_path, encoding="utf-8") as f:
            return json.load(f)


def _write_fixture_csv(dest, fixture_name):
    shutil.copy(FIXTURES_DIR / fixture_name, dest)


def run_analyse(
    tmp_path,
    mock_server,
    fixture_name="responses_tiny.csv",
    extra_env=None,
    timeout=30,
    analyse_py=FROZEN_STARTER_SNAPSHOT,
):
    """Run the OLD cwd-relative-path CLI as a subprocess - only still valid
    for FROZEN_STARTER_SNAPSHOT (the frozen baseline suite). Today's real
    solution/analyse.py takes explicit --input/--output/--state-file flags
    instead; use run_solution() for that.

    Lays out `<tmp>/data/responses_sample.csv` and cwd=`<tmp>/solution` to
    match the original prototype's relative paths (`../data/...`,
    `results.json`) exactly as `python analyse.py` was invoked from
    `solution/` (or `starter/`) before the CLI was rewritten.
    """
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "solution"
    data_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_fixture_csv(data_dir / "responses_sample.csv", fixture_name)

    env = {
        "ANTHROPIC_API_KEY": DUMMY_API_KEY,
        "ANTHROPIC_BASE_URL": mock_server.base_url,
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    if extra_env:
        env.update(extra_env)

    proc = subprocess.run(
        [sys.executable, str(analyse_py.resolve())],
        cwd=run_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return AnalyseRun(proc.returncode, proc.stdout, proc.stderr, run_dir)


def start_analyse(
    tmp_path, mock_server, fixture_name="responses_tiny.csv", extra_env=None, analyse_py=FROZEN_STARTER_SNAPSHOT
):
    """Like run_analyse but returns a live Popen handle. Old cwd-relative-path
    CLI - only still valid for FROZEN_STARTER_SNAPSHOT; use start_solution()
    for today's real solution/analyse.py."""
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "solution"
    data_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_fixture_csv(data_dir / "responses_sample.csv", fixture_name)

    env = {
        "ANTHROPIC_API_KEY": DUMMY_API_KEY,
        "ANTHROPIC_BASE_URL": mock_server.base_url,
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    if extra_env:
        env.update(extra_env)

    proc = subprocess.Popen(
        [sys.executable, str(analyse_py.resolve())],
        cwd=run_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc, run_dir


class SolutionRun:
    """A completed (or crashed) invocation of today's real analyse.py CLI,
    against explicit --input/--output/--state-file paths under tmp_path -
    no cwd tricks needed, since the new CLI takes real path arguments."""

    def __init__(self, returncode, stdout, stderr, output_path, state_file):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.output_path = output_path
        self.state_file = state_file

    @property
    def results(self):
        if not self.output_path.exists():
            return None
        with open(self.output_path, encoding="utf-8") as f:
            return json.load(f)

    @property
    def state(self):
        if not self.state_file.exists():
            return None
        with open(self.state_file, encoding="utf-8") as f:
            return json.load(f)


def _solution_args(tmp_path, fixture_name, mode, extra_args):
    input_csv = tmp_path / "input.csv"
    output_json = tmp_path / "results.json"
    state_file = tmp_path / ".batch_state.json"
    _write_fixture_csv(input_csv, fixture_name)
    args = [
        sys.executable,
        str(ANALYSE_PY.resolve()),
        "--input", str(input_csv),
        "--output", str(output_json),
        "--state-file", str(state_file),
        "--mode", mode,
    ]
    if extra_args:
        args.extend(extra_args)
    return args, output_json, state_file


def run_solution(
    tmp_path, mock_server, fixture_name="responses_tiny.csv", extra_env=None,
    timeout=30, mode="sequential", extra_args=None,
):
    """Run today's real solution/analyse.py as a subprocess against the mock
    server, using its actual current CLI."""
    args, output_json, state_file = _solution_args(tmp_path, fixture_name, mode, extra_args)
    env = {
        "ANTHROPIC_API_KEY": DUMMY_API_KEY,
        "ANTHROPIC_BASE_URL": mock_server.base_url,
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    if extra_env:
        env.update(extra_env)
    proc = subprocess.run(args, env=env, capture_output=True, text=True, timeout=timeout)
    return SolutionRun(proc.returncode, proc.stdout, proc.stderr, output_json, state_file)


def start_solution(
    tmp_path, mock_server, fixture_name="responses_tiny.csv", extra_env=None,
    mode="sequential", extra_args=None,
):
    """Like run_solution but returns a live Popen handle, for kill/resume and
    concurrent-run tests that need to interact with the process while it's
    still running."""
    args, output_json, state_file = _solution_args(tmp_path, fixture_name, mode, extra_args)
    env = {
        "ANTHROPIC_API_KEY": DUMMY_API_KEY,
        "ANTHROPIC_BASE_URL": mock_server.base_url,
        "PATH": __import__("os").environ.get("PATH", ""),
    }
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc, output_json, state_file


@pytest.fixture
def solution_module(monkeypatch):
    """Import solution/analyse.py in-process for unit tests, with a dummy
    key so client construction (lazy, no network call at construction time
    - verified empirically against the installed SDK) doesn't need a real
    one."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", DUMMY_API_KEY)
    sys.path.insert(0, str(SOLUTION_DIR))
    sys.modules.pop("analyse", None)
    import analyse as solution_analyse

    yield solution_analyse
    sys.modules.pop("analyse", None)
    sys.path.remove(str(SOLUTION_DIR))
