"""Per-call cost tracker for the FOI multi-agent system.

Emits one CostEntry per model call (not per stage) so per-call / per-agent /
per-request / per-run granularity can all be reconstructed from the entry list.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

from langchain_core.callbacks import get_usage_metadata_callback
from rich.console import Console
from rich.table import Table

from foi_system.config import PRICES_USD_PER_MTOK
from foi_system.models import CostEntry


class CostTracker:
    def __init__(self) -> None:
        self.entries: list[CostEntry] = []

    @contextmanager
    def track(self, agent: str) -> Iterator[None]:
        """Context manager: any LLM .invoke() inside is captured as a CostEntry."""
        with get_usage_metadata_callback() as cb:
            yield
        # usage_metadata keyed by model name -> one CostEntry per model invoked
        for model, usage in cb.usage_metadata.items():
            self.add_from_usage(agent, model, usage)  # type: ignore[arg-type]

    def add_from_usage(self, agent: str, model: str, usage: dict) -> CostEntry:
        """Compute cost from a raw usage dict and append a CostEntry."""
        in_tok = int(usage.get("input_tokens", 0))
        out_tok = int(usage.get("output_tokens", 0))
        prices = PRICES_USD_PER_MTOK[model]
        cost = in_tok / 1_000_000 * prices["input"] + out_tok / 1_000_000 * prices["output"]
        entry = CostEntry(
            agent=agent,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )
        self.entries.append(entry)
        return entry

    def per_agent(self) -> dict[str, float]:
        """Return total cost_usd summed per agent name."""
        out: dict[str, float] = {}
        for e in self.entries:
            out[e.agent] = out.get(e.agent, 0.0) + e.cost_usd
        return out

    def per_request_total(self) -> float:
        """Return grand total cost_usd across all entries."""
        return sum(e.cost_usd for e in self.entries)

    def summary_table(self) -> str:
        """Render a Rich table: one row per agent (calls/tokens/cost) + TOTAL row."""
        table = Table(title="Cost Summary")
        table.add_column("Agent", style="cyan")
        table.add_column("Calls", justify="right")
        table.add_column("Input", justify="right")
        table.add_column("Output", justify="right")
        table.add_column("Cost (USD)", justify="right", style="green")

        # Aggregate per agent
        agent_data: dict[str, dict[str, int | float]] = {}
        for e in self.entries:
            if e.agent not in agent_data:
                agent_data[e.agent] = {"calls": 0, "input": 0, "output": 0, "cost": 0.0}
            agent_data[e.agent]["calls"] = int(agent_data[e.agent]["calls"]) + 1
            agent_data[e.agent]["input"] = int(agent_data[e.agent]["input"]) + e.input_tokens
            agent_data[e.agent]["output"] = int(agent_data[e.agent]["output"]) + e.output_tokens
            agent_data[e.agent]["cost"] = float(agent_data[e.agent]["cost"]) + e.cost_usd

        total_calls = 0
        total_input = 0
        total_output = 0
        total_cost = 0.0

        for agent, data in agent_data.items():
            calls = int(data["calls"])
            inp = int(data["input"])
            out = int(data["output"])
            cost = float(data["cost"])
            table.add_row(agent, str(calls), str(inp), str(out), f"{cost:.4f}")
            total_calls += calls
            total_input += inp
            total_output += out
            total_cost += cost

        table.add_section()
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_calls}[/bold]",
            f"[bold]{total_input}[/bold]",
            f"[bold]{total_output}[/bold]",
            f"[bold]{total_cost:.4f}[/bold]",
        )

        buf = StringIO()
        Console(file=buf, width=100).print(table)
        return buf.getvalue()
