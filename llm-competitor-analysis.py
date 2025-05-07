"""llm_competitor_analysis.py
────────────────────────────────────────────────────
Benchmark multiple LLM vendors on a single prompt and have an OpenAI model rank
their answers **strictly in JSON**. Robust against malformed JSON — tries a
regex extraction fallback and, if needed, re‑asks the judge at temp 0.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import List

from dotenv import load_dotenv

from openai_guard import gpt_call  # tracks cost & enforces £ cap
from providers import PROVIDERS

# ── CONFIG ───────────────────────────────────────────────────────────────────
MAX_TOKENS = 1_000  # parity for all competitors
JUDGE_MODEL = "o3-mini"  # use the reasoning model to rank
JUDGE_TEMP = 0.0  # deterministic for JSON
QUESTION_PROMPT = (
    "Please craft a challenging, nuanced question about music production "
    "that will test the reasoning abilities of different language models. "
    "Answer ONLY with the question—no explanations."
)
SYSTEM_JSON = "You respond ONLY in valid JSON. No markdown."

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("llm‑battle")

# ── Helpers ──────────────────────────────────────────────────────────────────


def preview_keys() -> None:
    for env, label, n in [
        ("OPENAI_API_KEY", "OpenAI", 8),
        ("ANTHROPIC_API_KEY", "Anthropic", 7),
        ("GOOGLE_API_KEY", "Google", 2),
        ("DEEPSEEK_API_KEY", "DeepSeek", 3),
        ("GROQ_API_KEY", "Groq", 4),
    ]:
        key = os.getenv(env)
        log.info(
            f"{label} key {'detected' if key else 'MISSING'}"
            + (f" (starts {key[:n]})" if key else "")
        )


def banner(msg: str) -> None:
    print("-" * 60)
    print(msg)
    print("-" * 60)


# ── Judge helpers ────────────────────────────────────────────────────────────


def ask_judge(judge_prompt: str) -> str:
    """Call the judge model with system JSON constraint."""
    return gpt_call(
        [
            {"role": "system", "content": SYSTEM_JSON},
            {"role": "user", "content": judge_prompt},
        ],
        model=JUDGE_MODEL,
        max_tokens=300,
        temperature=JUDGE_TEMP,
    )


def parse_json(raw: str) -> List[str] | None:
    """Safely parse the judge output, fallback to regex extraction."""
    try:
        return json.loads(raw)["results"]
    except Exception:
        match = re.search(r"\{[^{}]*\}\s*$", raw.strip())
        if match:
            try:
                return json.loads(match.group())["results"]
            except Exception:  # still bad
                return None
        return None


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    preview_keys()

    # 1️⃣ Generate challenge question
    question = gpt_call(
        [{"role": "user", "content": QUESTION_PROMPT}],
        model="gpt-4o-mini",
        max_tokens=200,
    )
    log.info("Question → %s", question)

    base_messages = [{"role": "user", "content": question}]
    competitors: List[str] = []
    answers: List[str] = []

    # 2️⃣ Query each provider
    for name, fn in PROVIDERS:
        log.info("→ Asking %s …", name)
        try:
            ans = fn(base_messages, max_tokens=MAX_TOKENS)
        except Exception as exc:
            log.error("%s failed: %s", name, exc)
            ans = f"ERROR: {exc}"
        competitors.append(name)
        answers.append(ans)
        banner(f"### {name} says:\n\n{ans}")

    # 3️⃣ Build judging prompt
    compiled = "".join(
        f"# Response from competitor {idx+1}\n\n{ans}\n\n"
        for idx, ans in enumerate(answers)
    )
    judge_prompt = (
        f"You are judging a competition between {len(competitors)} competitors.\n\n"
        f"Each model received this question:\n\n{question}\n\n"
        "Rank the responses for clarity and strength of argument. "
        "Return JSON ONLY like {\"results\":[\"1\",\"2\",…]}. Numbers refer to competitor order.\n\n"
        f"Responses:\n\n{compiled}\n"
        "Answer now with STRICT JSON."
    )

    raw = ask_judge(judge_prompt)
    log.info("Judge raw → %s", raw)
    ranks = parse_json(raw)

    # Retry once with GPT‑4o‑mini deterministic if still bad
    if ranks is None:
        log.warning("Judge JSON malformed. Retrying with GPT‑4o‑mini at temp 0…")
        global JUDGE_MODEL
        JUDGE_MODEL = "gpt-4o-mini"
        raw = ask_judge(judge_prompt)
        log.info("Backup judge raw → %s", raw)
        ranks = parse_json(raw)

    if ranks is None:
        log.error("Failed to parse judge output after retry. Aborting.")
        return

    print("\n🏆  FINAL RANKING\n" + "=" * 30)
    for idx, rank in enumerate(ranks, 1):
        print(f"{idx}. {competitors[int(rank)-1]}")


if __name__ == "__main__":
    main()
