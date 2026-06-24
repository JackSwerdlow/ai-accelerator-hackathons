"""Configuration constants for the FOI multi-agent system."""

import os

from dotenv import load_dotenv

load_dotenv()

MODEL_TIERS: dict[str, str] = {
    "triage": "claude-haiku-4-5-20251001",
    "compliance": "claude-sonnet-4-6",
    "response": "claude-sonnet-4-6",
    "redaction": "claude-haiku-4-5-20251001",
}  # redaction tiered to Haiku

PRICES_USD_PER_MTOK: dict[str, dict[str, float]] = {
    # Claude ONLY — verified against current Anthropic pricing 2026-06-24
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}

# ratified; MiniLM fallback if Day-1 download fails
EMBED_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"
EMBED_FALLBACK: str = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PATH: str = "./output/chroma_db"
COLLECTION: str = "foi_policies"
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 64
RAG_TOP_K: int = 5
STALENESS_DAYS: int = 30
PER_CALL_COST_CAP_USD: float = 0.25  # cost-downgrade trigger (reliability layer 4)
CIRCUIT_BREAKER_THRESHOLD: int = 3  # consecutive post-retry failures -> degrade agent


def get_operator_id() -> str | None:
    """Return the OPERATOR_ID env var if set, else None.

    This is an optional pre-fill only — the CLI/HITL layer must enforce non-empty.
    """
    return os.environ.get("OPERATOR_ID") or None
