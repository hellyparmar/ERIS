"""Assistant orchestration: understand -> (optionally refine with LLM) -> run analytics -> answer."""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.models import ChatMessage, Organization, User
from app.security import scoped_outlet_ids
from app.services import analytics as A
from app.services.assistant import llm
from app.services.assistant.nlu import EntityIndex, Parsed, parse, parse_horizon, parse_periods
from app.services.assistant.tools import DISPATCH, HELP_TEXT, Ctx, Fmt, result

log = logging.getLogger(__name__)
FOLLOWUP = re.compile(r"^\s*(what about|how about|and|same for|now|also|for|in|at|what of|ok and|okay and)\b", re.I)


def _previous_context(db: Session, user: User) -> dict | None:
    msg = db.scalar(select(ChatMessage).where(ChatMessage.user_id == user.id, ChatMessage.role == "assistant")
                    .order_by(ChatMessage.id.desc()).limit(1))
    return (msg.payload or {}).get("context") if msg and msg.payload else None


def _apply_followup(p: Parsed, prev: dict, anchor: date) -> None:
    """'What about Bandra?' -> repeat the previous question with the new outlet."""
    p.intent = prev.get("intent", p.intent)
    p.confidence = max(p.confidence, 0.6)
    if not p.periods and prev.get("periods"):
        p.periods = [(A.DateRange(date.fromisoformat(x["start"]), date.fromisoformat(x["end"])), x["label"])
                     for x in prev["periods"]]
    mentioned_entity = p.outlet_ids or p.category_id or p.product_ids
    if not p.outlet_ids and not mentioned_entity:
        p.outlet_ids, p.outlet_names = prev.get("outlet_ids", []), prev.get("outlet_names", [])
    if not (p.category_id or p.product_ids) and not (p.outlet_ids and p.outlet_ids != prev.get("outlet_ids")):
        p.category_id, p.category_name = prev.get("category_id"), prev.get("category_name")
        p.product_ids, p.product_names = prev.get("product_ids", []), prev.get("product_names", [])
    if p.horizon is None:
        p.horizon = prev.get("horizon")
    if p.top_n is None:
        p.top_n = prev.get("top_n")


def _apply_llm(p: Parsed, data: dict, index: EntityIndex, anchor: date) -> None:
    intent = data.get("intent")
    if intent in DISPATCH or intent == "general":
        p.intent = intent
        p.confidence = 0.7
    if not p.periods and isinstance(data.get("period"), str):
        p.periods = parse_periods(data["period"], anchor)
    if not p.outlet_ids and isinstance(data.get("outlets"), list):
        outlets = index.match_outlets(" ".join(str(x) for x in data["outlets"]))
        p.outlet_ids, p.outlet_names = [o.id for o in outlets], [o.name for o in outlets]
    if not p.category_id and not p.product_ids and data.get("product"):
        prods = index.match_products(str(data["product"]))
        if 0 < len(prods) <= 3:
            p.product_ids, p.product_names = [x.id for x in prods], [x.name for x in prods]
    if not p.category_id and not p.product_ids and data.get("category"):
        cat = index.match_category(str(data["category"]))
        if cat:
            p.category_id, p.category_name = cat.id, cat.name
    if p.top_n is None and isinstance(data.get("top_n"), int):
        p.top_n = max(1, min(50, data["top_n"]))
    if p.horizon is None and isinstance(data.get("horizon_days"), int):
        p.horizon = max(7, min(90, data["horizon_days"]))


def _facts(db: Session, outlet_ids: list[int] | None, f: Fmt) -> str:
    anchor = A.anchor_date(db)
    rng = A.DateRange(anchor - timedelta(days=29), anchor)
    k = A.kpis_with_comparison(db, rng, outlet_ids)
    cur, ch = k["current"], k["change_pct"]
    outlets = A.outlet_performance(db, rng, outlet_ids)
    cats = A.category_breakdown(db, rng, outlet_ids)[:4]
    tops = A.top_products(db, rng, outlet_ids, 5)
    lines = [
        f"Data up to {anchor.isoformat()}. Last 30 days: revenue {f.money(cur['revenue'])} ({ch['revenue']}% vs previous 30 days), "
        f"{cur['orders']} bills, average bill {f.money(cur['avg_basket'])}, gross margin {cur['margin_pct']}%.",
        "Outlets by revenue: " + "; ".join(f"{o['name']} {f.money(o['revenue'])} ({o['change_pct']}%)" for o in outlets),
        "Top categories: " + "; ".join(f"{x['category']} {x['share_pct']}% share, {x['margin_pct']}% margin" for x in cats),
        "Top products: " + "; ".join(f"{x['name']} {f.money(x['revenue'])}" for x in tops),
    ]
    return "\n".join(lines)


def answer(db: Session, user: User, message: str) -> dict:
    message = (message or "").strip()[:500]
    anchor = A.anchor_date(db)
    # Relative dates ("today", "yesterday") follow the real calendar while data is current; with stale
    # data (e.g. an old demo database) they are relative to the last day that has sales.
    today = clock.today()
    ref = today if anchor >= today - timedelta(days=1) else anchor
    index = EntityIndex(db)
    parsed = parse(db, message, ref, index)
    engine = "rules"

    prev = _previous_context(db, user)
    is_followup = bool(FOLLOWUP.match(message)) and len(message.split()) <= 8
    if prev and prev.get("intent") in DISPATCH and prev.get("intent") != "help" and (
            (is_followup and parsed.confidence < 0.75) or
            (parsed.intent == "general" and (parsed.outlet_ids or parsed.category_id or parsed.product_ids or parsed.periods))):
        _apply_followup(parsed, prev, anchor)
        engine = "rules+context"

    llm_status = llm.status()
    if llm_status["available"] and parsed.confidence < 0.5 and parsed.intent != "help":
        data = llm.classify(message, [o.name for o in index.outlets], [c.name for c in index.categories])
        if data:
            _apply_llm(parsed, data, index, ref)
            engine = "rules+llm"
    if parsed.horizon is None:
        parsed.horizon = parse_horizon(message)

    user_outlets = scoped_outlet_ids(user)
    org = db.scalar(select(Organization))
    if parsed.intent == "general" or parsed.intent not in DISPATCH:
        if not message:
            out = result(HELP_TEXT)
        elif llm_status["available"]:
            text = llm.general_answer(message, _facts(db, user_outlets, Fmt(org.currency_symbol if org else "₹")),
                                      org.name if org else "the business")
            out = result(text or HELP_TEXT, [], ["How is business this week?", "What should I reorder?"])
            engine = "llm" if text else engine
        else:
            out = result(
                "I'm not sure I understood that. I answer questions about your sales, products, outlets, stock, "
                "customers and forecasts using your live data.\n\n" + HELP_TEXT.split("\n\n", 1)[1],
                [], ["How is business this week?", "Top 5 products this month", "What should I reorder?"])
        parsed.intent = "general"
    else:
        try:
            out = DISPATCH[parsed.intent](Ctx(db, user_outlets, parsed))
        except Exception:
            log.exception("assistant tool %s failed", parsed.intent)
            out = result("Sorry - something went wrong while analysing that. Please try rephrasing the question.")

    response = {
        "answer": out["answer"],
        "blocks": out["blocks"],
        "suggestions": out["suggestions"],
        "intent": parsed.intent,
        "engine": engine,
        "context": parsed.to_context(),
        "data_as_of": anchor.isoformat(),
    }
    db.add(ChatMessage(user_id=user.id, role="user", content=message))
    db.add(ChatMessage(user_id=user.id, role="assistant", content=out["answer"],
                       payload={k: response[k] for k in ("blocks", "suggestions", "intent", "engine", "context")}))
    db.commit()
    return response
