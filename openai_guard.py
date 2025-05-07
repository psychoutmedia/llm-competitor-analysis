"""openai_guard.py — cost‑aware wrapper for OpenAI chat calls
------------------------------------------------------------------
• Logs token usage to **usage_log.csv** (autocreates)
• Converts USD → GBP (configurable FX)
• Enforces a monthly budget cap (default £10 via env var)
• Adds model‑specific parameter shims (e.g., o3‑series uses
  `max_completion_tokens` instead of `max_tokens`)

Usage
-----
    from openai_guard import gpt_call

    messages = [{"role": "user", "content": "Hello!"}]
    answer = gpt_call(messages, model="gpt-4o-mini", max_tokens=200)

CSV columns
-----------
    timestamp,month,model,prompt_tokens,completion_tokens,total_tokens,cost_gbp
"""

from __future__ import annotations

import csv
import datetime as dt
import os
from pathlib import Path
from typing import Any, Dict, List

import openai
from dotenv import load_dotenv

# ── ENV & CONFIG ─────────────────────────────────────────────────────────────
load_dotenv(override=True)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Pricing ($ per 1K tokens) — update if OpenAI changes rates
MODEL_PRICING = {
    "gpt-4o-mini": {"in": 0.15 / 1000, "out": 0.60 / 1000},  # $0.15 / $0.60 per M
    "gpt-3.5-turbo-0125": {"in": 0.50 / 1000, "out": 1.50 / 1000},
    "o3-mini": {"in": 0.50 / 1000, "out": 1.50 / 1000},  # same as 3.5 for now
}

USD_TO_GBP = float(os.getenv("USD_TO_GBP", 0.80))
MONTHLY_BUDGET_GBP = float(os.getenv("MAX_BUDGET_GBP", 10))
LOG_FILE = Path("usage_log.csv")

# ── Internal helpers ─────────────────────────────────────────────────────────


def _estimate_cost(model: str, prompt_tok: int, comp_tok: int) -> float:
    if model not in MODEL_PRICING:
        raise ValueError(f"Pricing for model '{model}' not configured.")
    price = MODEL_PRICING[model]
    usd = prompt_tok * price["in"] + comp_tok * price["out"]
    return usd * USD_TO_GBP


def _current_month_spend() -> float:
    if not LOG_FILE.exists():
        return 0.0
    month = dt.datetime.utcnow().strftime("%Y-%m")
    with LOG_FILE.open() as f:
        reader = csv.DictReader(f)
        return sum(float(r["cost_gbp"]) for r in reader if r["month"] == month)


def _log_usage(
    timestamp: dt.datetime, model: str, p_tok: int, c_tok: int, cost: float
) -> None:
    new = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="") as f:
        fieldnames = [
            "timestamp",
            "month",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost_gbp",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": timestamp.isoformat(timespec="seconds"),
                "month": timestamp.strftime("%Y-%m"),
                "model": model,
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": p_tok + c_tok,
                "cost_gbp": f"{cost:.6f}",
            }
        )


# ── Public wrapper ───────────────────────────────────────────────────────────


def gpt_call(
    messages: List[Dict[str, Any]], *, model: str = "gpt-4o-mini", **kwargs
) -> str:
    """Call OpenAI chat completion with logging + budget cap.

    Parameters
    ----------
    messages : list[dict]
        Chat messages [{"role": "user", "content": "…"}, …]
    model : str, default "gpt-4o-mini"
    **kwargs : Any
        Extra parameters (e.g., temperature, max_tokens).

    Returns
    -------
    str
        Assistant message content.
    """

    # ── Model‑specific arg shim ──────────────────
    if model.startswith("o3-"):
        # token param rename
        if "max_tokens" in kwargs:
            kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
    # o3 does NOT accept temperature / top_p
    kwargs.pop("temperature", None)
    kwargs.pop("top_p", None)

    # Budget pre‑check
    spent = _current_month_spend()
    if spent >= MONTHLY_BUDGET_GBP:
        raise RuntimeError(
            f"💸 Monthly budget exhausted (£{spent:.2f} ≥ £{MONTHLY_BUDGET_GBP})"
        )

    # Live request
    response = openai.chat.completions.create(model=model, messages=messages, **kwargs)
    usage = response.usage

    # Cost calc & post‑check
    cost = _estimate_cost(model, usage.prompt_tokens, usage.completion_tokens)
    if spent + cost > MONTHLY_BUDGET_GBP:
        raise RuntimeError(
            f"⚠️ This call (£{cost:.4f}) would exceed the £{MONTHLY_BUDGET_GBP} cap "
            f"(current £{spent:.2f}). Aborted."
        )

    # Log & return content
    _log_usage(
        dt.datetime.utcnow(), model, usage.prompt_tokens, usage.completion_tokens, cost
    )
    return response.choices[0].message.content


__all__ = ["gpt_call"]
