"""
providers.py — thin wrappers around each LLM vendor used in the
llm‑competitor‑analysis pipeline.

Each helper returns a plain **str** with the assistant content and is
responsible for vendor‑specific plumbing *only* — the calling script takes
care of retries / judging / printing.

All OpenAI traffic funnels through **gpt_call()** (from openai_guard.py) so
every token is logged and capped against the monthly budget.
"""

from __future__ import annotations

import os
import logging
from typing import List, Dict, Tuple, Callable

from openai_guard import gpt_call  # cost‑aware wrapper
from anthropic import Anthropic

# Optional OpenAI‑compatible client for the other clouds (Gemini, DeepSeek, Groq, Ollama)
try:
    from openai import OpenAI as OpenAIClient
except ImportError:  # pragma: no cover — library missing only in CI
    OpenAIClient = None  # type: ignore

logger = logging.getLogger(__name__)


# ─────────────────── OpenAI ────────────────────
def ask_openai(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    **kwargs,
) -> str:
    """Query OpenAI via gpt_call wrapper (budget & log built‑in)."""
    return gpt_call(messages, model=model, **kwargs)


# ─────────────────── Anthropic ─────────────────
def ask_claude(
    messages: List[Dict[str, str]],
    model: str = "claude-3-7-sonnet-latest",
    **kwargs,
) -> str:
    """Query Anthropic Claude."""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(model=model, messages=messages, **kwargs)
    return resp.content[0].text


# ─────────────────── Gemini (Google) ───────────
def ask_gemini(
    messages: List[Dict[str, str]],
    model: str = "gemini-2.0-flash",
    **kwargs,
) -> str:
    """Query Google Gemini via its OpenAI‑compatible beta endpoint."""
    api_key = os.getenv("GOOGLE_API_KEY")
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    client = OpenAIClient(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content


# ─────────────────── DeepSeek ──────────────────
def ask_deepseek(
    messages: List[Dict[str, str]],
    model: str = "deepseek-chat",
    **kwargs,
) -> str:
    """Query DeepSeek."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = OpenAIClient(api_key=api_key, base_url="https://api.deepseek.com/v1")
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content


# ─────────────────── Groq (Llama 3) ────────────
def ask_groq(
    messages: List[Dict[str, str]],
    model: str = "llama-3.3-70b-versatile",
    **kwargs,
) -> str:
    """Query Groq Cloud (Meta Llama‑3 models)."""
    api_key = os.getenv("GROQ_API_KEY")
    client = OpenAIClient(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content


# ─────────────────── Ollama (local) ────────────
def ask_ollama(
    messages: List[Dict[str, str]],
    model: str = "llama3.2",
    **kwargs,
) -> str:
    """Query a local Ollama server (http://localhost:11434)."""
    client = OpenAIClient(base_url="http://localhost:11434/v1", api_key="ollama")
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content


# ─────────────────── Registry — change here only ────────────────
ProviderFn = Callable[[List[Dict[str, str]], str], str]

PROVIDERS: List[Tuple[str, ProviderFn]] = [
    ("gpt-4o-mini", ask_openai),
    ("claude-3-sonnet-latest", ask_claude),
    ("gemini-2.0-flash", ask_gemini),
    ("deepseek-chat", ask_deepseek),
    ("llama-3.3-70b-versatile", ask_groq),
    ("llama3.2", ask_ollama),
]

__all__ = [
    "ask_openai",
    "ask_claude",
    "ask_gemini",
    "ask_deepseek",
    "ask_groq",
    "ask_ollama",
    "PROVIDERS",
]
