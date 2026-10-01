"""Optional local LLM via Ollama (free & open source). Everything degrades gracefully without it."""
from __future__ import annotations

import json
import logging
import time

import httpx

from app.config import settings

log = logging.getLogger(__name__)
_status: dict = {"checked": 0.0, "available": False, "model": None, "error": None}


def status(force: bool = False) -> dict:
    """Is Ollama reachable and is the configured model pulled? (cached for 60 s)"""
    if not settings.LLM_ENABLED:
        return {"available": False, "model": None, "provider": "ollama", "error": "disabled (LLM_ENABLED=false)"}
    if not force and time.time() - _status["checked"] < 60:
        return {**{k: v for k, v in _status.items() if k != "checked"}, "provider": "ollama"}
    _status["checked"] = time.time()
    try:
        r = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=1.5)
        r.raise_for_status()
        names = [m.get("name", "") for m in r.json().get("models", [])]
        wanted = settings.OLLAMA_MODEL
        match = next((n for n in names if n == wanted or n.split(":")[0] == wanted.split(":")[0]), None)
        _status.update(available=match is not None, model=match,
                       error=None if match else f"model '{wanted}' not pulled (run: ollama pull {wanted})")
    except Exception as exc:  # not running / not installed
        _status.update(available=False, model=None, error=f"Ollama not reachable at {settings.OLLAMA_URL}")
        log.debug("ollama unavailable: %s", exc)
    return {**{k: v for k, v in _status.items() if k != "checked"}, "provider": "ollama"}


def _chat(messages: list[dict], json_mode: bool = False, max_tokens: int = 400) -> str | None:
    st = status()
    if not st["available"]:
        return None
    payload = {"model": st["model"], "messages": messages, "stream": False,
               "options": {"temperature": 0.1, "num_predict": max_tokens}}
    if json_mode:
        payload["format"] = "json"
    try:
        r = httpx.post(f"{settings.OLLAMA_URL}/api/chat", json=payload, timeout=settings.LLM_TIMEOUT_SECONDS)
        r.raise_for_status()
        return r.json().get("message", {}).get("content")
    except Exception as exc:
        log.warning("ollama call failed: %s", exc)
        _status["checked"] = 0.0
        return None


INTENT_DESCRIPTIONS = {
    "business_overview": "general health / summary / what to focus on",
    "sales_summary": "revenue, bills, average bill for a period (optionally an outlet, category or product)",
    "compare_periods": "compare two time periods",
    "sales_trend": "revenue trend over months/weeks, growth or decline",
    "top_products": "best selling products",
    "slow_products": "slow moving / worst selling products",
    "outlet_ranking": "compare or rank outlets/stores",
    "category_mix": "sales by category",
    "forecast": "predict future sales or demand",
    "stock_status": "current stock, low stock, out of stock",
    "reorder": "what to reorder / purchase suggestions",
    "customers": "top customers, loyalty, segments, customers at risk",
    "peak_hours": "busiest hours or days",
    "payment_mix": "payment methods (UPI, cash, card)",
    "profitability": "profit and margins",
    "purchase_orders": "open or overdue purchase orders",
    "general": "anything else (advice, explanations)",
}


def classify(question: str, outlets: list[str], categories: list[str]) -> dict | None:
    system = (
        "You convert a retail manager's question into JSON for an analytics engine. Reply with JSON only, keys: "
        "intent (one of: " + ", ".join(f"{k} = {v}" for k, v in INTENT_DESCRIPTIONS.items()) + "), "
        "period (a phrase like 'yesterday', 'last 7 days', 'last month', 'this year', 'March 2026', or null), "
        "outlets (list of outlet names from: " + ", ".join(outlets) + "), "
        "category (one of: " + ", ".join(categories) + ", or null), product (product words or null), "
        "top_n (integer or null), horizon_days (integer for forecasts or null)."
    )
    raw = _chat([{"role": "system", "content": system}, {"role": "user", "content": question}], json_mode=True, max_tokens=200)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def general_answer(question: str, facts: str, org_name: str) -> str | None:
    system = (
        f"You are ERIS, a friendly retail business assistant for {org_name}, a food & beverage retail chain. "
        "Answer briefly (under 150 words) in simple language for a non-technical shop owner. Use markdown. "
        "When you mention numbers, use ONLY the facts provided below - never invent figures. If the question "
        "needs data you don't have, say what the user can ask instead.\n\nFACTS:\n" + facts
    )
    return _chat([{"role": "system", "content": system}, {"role": "user", "content": question}], max_tokens=350)
