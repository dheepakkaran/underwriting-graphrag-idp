"""Claude Haiku 5.5 client with a cost ledger and a hard $ cap.

Every call is appended to results/cost_ledger.jsonl (tokens in/out, cache reads, $). Before each call the running
total is checked; at or above HARD_CAP_USD the call raises BudgetExceeded instead of spending more.
Prices: Claude Haiku 5.5, $0.10 / 1M input, $0.50 / 1M output (prompts < 100K tokens); cache reads billed at 0.1x input.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, TypeVar

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6
HARD_CAP_USD = float(os.environ.get("HARD_CAP_USD", "0.50"))
LEDGER = ROOT / "results" / "cost_ledger.jsonl"

T = TypeVar("T", bound=BaseModel)


class BudgetExceeded(RuntimeError):
    pass


_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=4)
    return _client


def spent_usd() -> float:
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l)["usd"] for l in LEDGER.read_text().splitlines() if l.strip())


def _log(tag: str, usage: Any, seconds: float) -> float:
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    usd = (usage.input_tokens * PRICE_IN + cache_write * PRICE_IN * 1.25 + cache_read * PRICE_IN * 0.1
           + usage.output_tokens * PRICE_OUT)
    LEDGER.parent.mkdir(exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps({"tag": tag, "model": MODEL, "in": usage.input_tokens, "out": usage.output_tokens,
                            "cache_read": cache_read, "cache_write": cache_write, "usd": round(usd, 7),
                            "seconds": round(seconds, 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
    return usd


def _guard():
    s = spent_usd()
    if s >= HARD_CAP_USD:
        raise BudgetExceeded(f"spent ${s:.4f} >= hard cap ${HARD_CAP_USD:.2f}; stopping")


def parse(tag: str, system: str, user: str, schema: type[T], max_tokens: int = 4000) -> T:
    """One structured-output call: returns a validated Pydantic object."""
    _guard()
    t0 = time.time()
    r = client().messages.parse(
        model=MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema, output_config={"effort": "low"},
    )
    _log(tag, r.usage, time.time() - t0)
    if r.stop_reason == "refusal":
        raise RuntimeError(f"{tag}: model refused")
    if r.parsed_output is None:
        raise RuntimeError(f"{tag}: no parsed output (stop_reason={r.stop_reason})")
    return r.parsed_output


def create(tag: str, **kw) -> anthropic.types.Message:
    """Raw messages.create (used by the tool-using agent loop)."""
    _guard()
    t0 = time.time()
    r = client().messages.create(model=MODEL, **kw)
    _log(tag, r.usage, time.time() - t0)
    return r
