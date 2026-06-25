"""Tests for the FOI CLI entry point (Task 13).

Tests call subcommand functions directly (not subprocess.run).
All external I/O is monkeypatched.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

import foi_system.indexing as _indexing_mod
import foi_system.supervisor as _supervisor_mod

# ---------------------------------------------------------------------------
# Test 1: index command reports chunk count
# ---------------------------------------------------------------------------


def test_index_command_reports_chunk_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """index_cmd prints 'Indexed 7 ...' when index_policies returns 7."""
    monkeypatch.setattr(_indexing_mod, "index_policies", lambda *a, **kw: 7)

    from foi_system.cli import index_cmd

    args = argparse.Namespace(policies=str(tmp_path))
    index_cmd(args)

    out = capsys.readouterr().out
    assert "Indexed" in out
    assert "7" in out


# ---------------------------------------------------------------------------
# Test 2: process command requires operator
# ---------------------------------------------------------------------------


def test_process_requires_operator(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """process_cmd exits with code 1 when operator is empty and OPERATOR_ID env is unset."""
    # Ensure env var is absent

    monkeypatch.delenv("OPERATOR_ID", raising=False)

    from foi_system.cli import process_cmd

    args = argparse.Namespace(operator="", path=str(tmp_path), policies="corpus/policies")

    with pytest.raises(SystemExit) as exc_info:
        process_cmd(args)

    assert exc_info.value.code == 1
    out_err = capsys.readouterr()
    assert "operator" in (out_err.out + out_err.err).lower()


# ---------------------------------------------------------------------------
# Test 3: process auto-indexes when collection is empty
# ---------------------------------------------------------------------------


class _FakeCollection:
    """Minimal collection stub whose count() returns a configurable value."""

    def __init__(self, count_val: int) -> None:
        self._count_val = count_val

    def count(self) -> int:
        return self._count_val


def test_process_autoindexes_when_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """process_cmd calls index_policies and prints auto-index message when collection is empty."""
    # Write a minimal request file in tmp_path (so path is a directory with one .txt)
    (tmp_path / "request1.txt").write_text("Please provide records about X.", encoding="utf-8")

    index_call_counter: list[int] = [0]

    def _fake_index_policies(*args: Any, **kwargs: Any) -> int:
        index_call_counter[0] += 1
        return 5

    monkeypatch.setattr(_indexing_mod, "get_collection", lambda *a, **kw: _FakeCollection(0))
    monkeypatch.setattr(_indexing_mod, "index_policies", _fake_index_policies)
    monkeypatch.setattr(_indexing_mod, "check_freshness", lambda *a, **kw: [])
    monkeypatch.setattr(_supervisor_mod, "process_folder", lambda *a, **kw: [])

    from foi_system.cli import process_cmd

    args = argparse.Namespace(
        operator="officer-42",
        path=str(tmp_path),
        policies="corpus/policies",
    )
    process_cmd(args)

    assert index_call_counter[0] >= 1, "index_policies was not called during auto-index"

    out = capsys.readouterr().out
    assert "[auto-index]" in out or "Indexed" in out


# ---------------------------------------------------------------------------
# Test 4: eval command runs without raising
# ---------------------------------------------------------------------------


def test_eval_command_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """eval_cmd calls run_eval with the given gold path and does not raise."""
    import eval.eval_harness as _harness_mod

    called_with: list[str] = []

    monkeypatch.setattr(_harness_mod, "run_eval", lambda gold_path: called_with.append(gold_path))

    from foi_system.cli import eval_cmd

    gold_file = str(tmp_path / "gold.jsonl")
    args = argparse.Namespace(gold=gold_file)
    eval_cmd(args)

    assert called_with == [gold_file]
