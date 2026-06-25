"""CLI entry point for the FOI multi-agent system.

Commands:
  foi index [--policies <dir>]
  foi process <path> --operator <id>
  foi eval [--gold <file>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import foi_system.indexing as _indexing
import foi_system.supervisor as _supervisor
from foi_system.config import CHROMA_PATH, COLLECTION, get_operator_id

_DEFAULT_POLICIES_DIR = "corpus/policies"
_DEFAULT_GOLD_FILE = "corpus/gold/gold_answers.jsonl"


# ---------------------------------------------------------------------------
# Subcommand functions — called directly by tests
# ---------------------------------------------------------------------------


def index_cmd(args: argparse.Namespace) -> None:
    """Handle `foi index`."""
    policies_dir = args.policies
    try:
        n = _indexing.index_policies(policies_dir)
        print(f"Indexed {n} chunks from {policies_dir}.")
    except Exception as exc:  # noqa: BLE001
        print(str(exc))
        sys.exit(1)


def process_cmd(args: argparse.Namespace) -> None:
    """Handle `foi process`."""
    # Resolve operator — may be pre-filled from env var
    operator = args.operator or get_operator_id()
    if not operator:
        print("Error: --operator is required (or set the OPERATOR_ID environment variable).")
        sys.exit(1)

    policies_dir = getattr(args, "policies", _DEFAULT_POLICIES_DIR)

    # Auto-index when collection is empty
    col = _indexing.get_collection(CHROMA_PATH, COLLECTION)
    if col.count() == 0:
        n = _indexing.index_policies(policies_dir)
        print(f"[auto-index] Indexed {n} chunks from {policies_dir}")

    # Warn on stale documents
    stale = _indexing.check_freshness(CHROMA_PATH, COLLECTION)
    if stale:
        print(f"Warning: stale policy documents: {stale}. Re-run `foi index` to refresh.")

    path = Path(args.path)
    if path.is_dir():
        _supervisor.process_folder(str(path), operator)
    else:
        from foi_system.cost import CostTracker
        from foi_system.supervisor import CircuitBreaker

        _supervisor.process_request(str(path), operator, CostTracker(), CircuitBreaker())


def eval_cmd(args: argparse.Namespace) -> None:
    """Handle `foi eval`."""
    from eval.eval_harness import run_eval

    run_eval(args.gold)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foi",
        description="UK FOI multi-agent CLI",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- index ---
    p_index = sub.add_parser("index", help="Index policy documents into ChromaDB.")
    p_index.add_argument(
        "--policies",
        default=_DEFAULT_POLICIES_DIR,
        metavar="DIR",
        help=f"Directory containing policy .txt files (default: {_DEFAULT_POLICIES_DIR})",
    )

    # --- process ---
    p_process = sub.add_parser("process", help="Process a FOI request file or folder.")
    p_process.add_argument("path", metavar="FILE_OR_FOLDER", help="Request file or folder.")
    p_process.add_argument(
        "--operator",
        default="",
        metavar="ID",
        help="Operator identifier (or set OPERATOR_ID env var).",
    )
    p_process.add_argument(
        "--policies",
        default=_DEFAULT_POLICIES_DIR,
        metavar="DIR",
        help=f"Policy directory for auto-index (default: {_DEFAULT_POLICIES_DIR})",
    )

    # --- eval ---
    p_eval = sub.add_parser("eval", help="Run the evaluation harness.")
    p_eval.add_argument(
        "--gold",
        default=_DEFAULT_GOLD_FILE,
        metavar="FILE",
        help=f"Gold-answer JSONL file (default: {_DEFAULT_GOLD_FILE})",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the appropriate subcommand function."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "index":
        index_cmd(args)
    elif args.command == "process":
        process_cmd(args)
    elif args.command == "eval":
        eval_cmd(args)
    else:
        parser.print_help()
        sys.exit(1)
