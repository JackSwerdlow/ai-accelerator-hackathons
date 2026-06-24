"""Tests for foi_system.cost — CostTracker per-call granularity and math.

All tests are offline (no network, no real API key).
"""

import pytest

from foi_system.cost import CostTracker


def test_cost_computes_usd_from_tokens() -> None:
    """add_from_usage correctly converts token counts to USD using PRICES_USD_PER_MTOK."""
    tracker = CostTracker()

    # Haiku: input $1/MTok, output $5/MTok
    # 1_000_000 in + 1_000_000 out = $1.0 + $5.0 = $6.0
    entry_haiku = tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 1_000_000, "output_tokens": 1_000_000},
    )
    assert entry_haiku.cost_usd == pytest.approx(6.0)

    tracker2 = CostTracker()
    # Sonnet: input $3/MTok, output $15/MTok
    # 2_000_000 in + 1_000_000 out = $6.0 + $15.0 = $21.0
    entry_sonnet = tracker2.add_from_usage(
        "compliance",
        "claude-sonnet-4-6",
        {"input_tokens": 2_000_000, "output_tokens": 1_000_000},
    )
    assert entry_sonnet.cost_usd == pytest.approx(21.0)


def test_costentry_emitted_per_call_not_per_stage() -> None:
    """Each call to add_from_usage emits a separate CostEntry — no merging."""
    tracker = CostTracker()
    tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 100, "output_tokens": 50},
    )
    tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 200, "output_tokens": 80},
    )
    # Two separate calls → two separate entries, NOT one merged entry
    assert len(tracker.entries) == 2


def test_per_agent_breakdown() -> None:
    """per_agent() sums costs per agent; per_request_total() is the grand total."""
    tracker = CostTracker()

    # triage call 1: haiku 1M in + 1M out = $6.0
    tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 1_000_000, "output_tokens": 1_000_000},
    )
    # compliance call: sonnet 2M in + 1M out = $21.0
    tracker.add_from_usage(
        "compliance",
        "claude-sonnet-4-6",
        {"input_tokens": 2_000_000, "output_tokens": 1_000_000},
    )
    # triage call 2: haiku 500k in + 500k out = $0.5 + $2.5 = $3.0
    tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 500_000, "output_tokens": 500_000},
    )

    breakdown = tracker.per_agent()
    assert breakdown["triage"] == pytest.approx(6.0 + 3.0)  # $9.0
    assert breakdown["compliance"] == pytest.approx(21.0)
    assert tracker.per_request_total() == pytest.approx(9.0 + 21.0)  # $30.0


def test_summary_table_has_per_agent_and_total() -> None:
    """summary_table() string contains each agent name and 'TOTAL' and the total cost."""
    tracker = CostTracker()
    tracker.add_from_usage(
        "triage",
        "claude-haiku-4-5-20251001",
        {"input_tokens": 1_000_000, "output_tokens": 1_000_000},
    )
    tracker.add_from_usage(
        "compliance",
        "claude-sonnet-4-6",
        {"input_tokens": 2_000_000, "output_tokens": 1_000_000},
    )

    table_str = tracker.summary_table()

    assert "triage" in table_str
    assert "compliance" in table_str
    assert "TOTAL" in table_str

    total = tracker.per_request_total()  # $27.0
    # The table renders cost_usd figures; check the total cost appears in the output
    assert f"{total:.4f}" in table_str
