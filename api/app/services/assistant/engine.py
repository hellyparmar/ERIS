"""Assistant orchestration: understand -> (optionally refine with LLM) -> run analytics -> answer."""
from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.db import write_session
from app.models import ChatMessage, DatasetInfo, Organization, Outlet, Sale, User
from app.security import scoped_outlet_ids
from app.services import analytics as A
from app.services.assistant import knowledge, llm
from app.services.assistant.insight_tools import DISPATCH
from app.services.assistant.nlu import EntityIndex, Parsed, parse, parse_horizon, parse_periods
from app.services.assistant.tools import HELP_TEXT, Ctx, Fmt, result

log = logging.getLogger(__name__)
FOLLOWUP = re.compile(r"^\s*(what about|how about|and|same for|now|also|for|in|at|what of|ok and|okay and)\b", re.I)


def _previous_context(db: Session, user: User) -> dict | None:
    msg = db.scalar(select(ChatMessage).where(ChatMessage.user_id == user.id, ChatMessage.role == "assistant")
                    .order_by(ChatMessage.id.desc()).limit(1))
    return (msg.payload or {}).get("context") if msg and msg.payload else None


def _apply_followup(p: Parsed, prev: dict, anchor: date) -> None:
    """'What about Pune?' -> repeat the previous question with the new outlet."""
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


SOURCE_LABELS = {"synthetic": "synthetic demo data", "manual": "manually entered sales", "import": "imported sales"}


def _data_source(db: Session, outlet_ids: list[int] | None) -> str:
    q = select(Sale.source, func.count(Sale.id)).where(Sale.status == "completed")
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    counts = dict(db.execute(q.group_by(Sale.source)).all())
    if not counts:
        return "No sales recorded yet"
    parts = [f"{SOURCE_LABELS.get(s, s)} ({n:,} bills)" for s, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    text = "Sales database: " + ", ".join(parts)
    ds = db.scalar(select(DatasetInfo).order_by(DatasetInfo.id.desc())) if "synthetic" in counts else None
    if ds:
        text += f"; synthetic data from generator v{ds.generator_version}, seed {ds.random_seed}"
    return text


def _coverage_notes(db: Session, ctx: Ctx | None) -> list[str]:
    """Caveats when a period reaches outside the data, or an outlet was not open for all of it."""
    if ctx is None or not ctx.used_periods:
        return []
    notes = []
    today = clock.today()
    for rng, _label in ctx.used_periods:
        if rng.start <= today <= rng.end:
            notes.append(f"Today ({today:%d %b}) is still in progress - its figures include only the sales recorded so far.")
            break
    first_period = ctx.used_periods[0][0]
    if first_period.days <= 3 and ctx.parsed.intent in ("growth_products", "compare_periods", "category_mix", "why_change"):
        notes.append(f"The period is only {first_period.days} day(s) long, so percentage changes are noisy.")
    first, last = A.first_sale_date(db), A.latest_sale_date(db)
    outlets = db.scalars(select(Outlet).where(Outlet.id.in_(ctx.outlet_ids))).all() if ctx.outlet_ids else \
        db.scalars(select(Outlet)).all()
    for rng, label in ctx.used_periods:
        if first is None:
            notes.append("There is no sales data yet.")
            break
        if last and rng.start > last and rng.start <= clock.today():
            notes.append(f"No sales have been recorded after {last} yet.")
        elif rng.end < first or (last and rng.start > last):
            notes.append(f"{label} ({rng.start} to {rng.end}) is outside the recorded data ({first} to {last}).")
        elif rng.start < first:
            notes.append(f"Data starts on {first}, so {label} is only partly covered.")
        for o in outlets:
            if o.opened_on and rng.start < o.opened_on <= rng.end:
                notes.append(f"{o.name} opened on {o.opened_on}, part-way through {label}.")
    return list(dict.fromkeys(notes))


def _provenance(db: Session, parsed: Parsed, ctx: Ctx | None, out: dict, ms: float, engine: str) -> dict:
    meta = out.get("meta") or {}
    filters: dict = {}
    if ctx is not None and parsed.intent != "knowledge":
        filters["outlets"] = ctx.scope_label
        if ctx.used_periods:
            filters["periods"] = [f"{label}: {r.start.isoformat()} to {r.end.isoformat()}"
                                  for r, label in ctx.used_periods]
    if parsed.category_name:
        filters["category"] = parsed.category_name
    if parsed.product_names:
        filters["products"] = parsed.product_names
    if parsed.intent in ("forecast", "stockout_risk") and parsed.horizon:
        filters["horizon_days"] = parsed.horizon
    data_source = meta.get("data_source")
    if data_source is None and parsed.intent not in ("help", "general", "knowledge"):
        data_source = _data_source(db, ctx.outlet_ids if ctx else None)
    return {
        "data_source": data_source,
        "filters": filters,
        "query_ms": round(ms),
        "model_version": meta.get("model_version"),
        "forecast_run_id": meta.get("forecast_run_id"),
        "sources": meta.get("sources", []),
        "notes": list(dict.fromkeys((meta.get("notes") or []) + _coverage_notes(db, ctx))),
        "engine": engine,
        "method": "intent template (no free-form SQL)" if parsed.intent not in ("general",) else
        ("local LLM over summary facts" if engine == "llm" else "fallback"),
    }


def _ensure_table(out: dict) -> None:
    """Asked for a spreadsheet or table: when the answer has a chart but no table, add the chart's data as one."""
    blocks = out.get("blocks") or []
    if any(b.get("type") == "table" for b in blocks):
        return
    chart = next((b for b in blocks if b.get("type") == "chart" and b.get("data")), None)
    if chart is None:
        return
    fmt = chart.get("format") or "number"
    columns = [{"key": chart["x"], "label": chart["x"].replace("_", " ").capitalize()}]
    columns += [{"key": s["key"], "label": s.get("label") or s["key"], "format": s.get("format") or fmt} for s in chart["series"]]
    blocks.append({"type": "table", "title": chart.get("title") or "Data", "columns": columns,
                   "rows": [{c["key"]: row.get(c["key"]) for c in columns} for row in chart["data"]]})
    out["blocks"] = blocks


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
    ctx = None
    t0 = time.perf_counter()
    if parsed.intent == "general" and message and knowledge.best_match(db, message):
        parsed.intent = "knowledge"  # a documentation question the patterns did not recognise
    if parsed.unknown_outlets and parsed.intent not in ("knowledge", "help", "smalltalk", "action_request", "general"):
        # never silently widen "Outlet 7" to all outlets
        all_outlets = index.outlets
        visible = [(i, o) for i, o in enumerate(all_outlets, 1) if user_outlets is None or o.id in user_outlets]
        listing = ", ".join(f"Outlet {i} = {o.name}" for i, o in visible)
        out = result(f"There is no {', '.join(parsed.unknown_outlets)} - ERIS has {len(all_outlets)} outlet(s). "
                     f"Your outlets: {listing}. Please ask again with one of these.", [],
                     [f"Revenue at {visible[0][1].name} last month"] if visible else [],
                     {"data_source": "outlet list", "notes": ["The question named an outlet that does not exist."]})
        parsed.intent = "clarify"
    elif parsed.intent == "general" or parsed.intent not in DISPATCH:
        if not message:
            out = result(HELP_TEXT)
        elif llm_status["available"]:
            text = llm.general_answer(message, _facts(db, user_outlets, Fmt(org.currency_symbol if org else "₹")),
                                      org.name if org else "the business")
            out = result(text or HELP_TEXT, [], ["How is business this week?", "What should I reorder?"],
                         {"notes": ["Worded by the local language model from a summary of the last 30 days."]}
                         if text else None)
            engine = "llm" if text else engine
        else:
            out = result(
                "I'm not sure I understood that. I answer questions about your sales, products, outlets, stock, "
                "customers and forecasts using your live data.\n\n" + HELP_TEXT.split("\n\n", 1)[1],
                [], ["How is business this week?", "Top 5 products this month", "What should I reorder?"])
        parsed.intent = "general"
    else:
        try:
            ctx = Ctx(db, user_outlets, parsed)
            out = DISPATCH[parsed.intent](ctx)
        except Exception:
            log.exception("assistant tool %s failed", parsed.intent)
            out = result("Sorry - something went wrong while analysing that. Please try rephrasing the question.")
    if "as_table" in parsed.flags:
        _ensure_table(out)
    if ctx is not None and ctx.fallback:  # the period asked for has no data yet: say which one was answered
        asked, answered, latest = ctx.fallback
        out["answer"] = (f"No sales are recorded for **{asked}** yet - the data runs to **{latest:%a %d %b}**, so this "
                         f"answer covers **{answered}**.\n\n") + out["answer"]
    ms = (time.perf_counter() - t0) * 1000
    provenance = _provenance(db, parsed, ctx, out, ms, engine)

    response = {
        "answer": out["answer"],
        "blocks": out["blocks"],
        "suggestions": out["suggestions"],
        "intent": parsed.intent,
        "engine": engine,
        "context": parsed.to_context(),
        "data_as_of": anchor.isoformat(),
        "provenance": provenance,
    }
    with write_session() as wdb:  # short write transaction: the answer itself only reads
        wdb.add(ChatMessage(user_id=user.id, role="user", content=message))
        wdb.add(ChatMessage(user_id=user.id, role="assistant", content=out["answer"],
                            payload={k: response[k] for k in ("blocks", "suggestions", "intent", "engine", "context",
                                                              "provenance")}))
        wdb.commit()
    return response
