"""Answer builders for analytical questions (v3): growth, why-did-it-change, stockout risk, weekend comparison,
forecast-model performance, anomalies and documentation lookups. Each one calls a fixed analytics function -
no free-form SQL - and returns its caveats in `meta` so the engine can show them with the answer."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select

from app.models import ForecastRun, Product, Sale
from app.services import analytics as A
from app.services import anomalies as AN
from app.services import drivers as D
from app.services import forecasting as F
from app.services.assistant import knowledge, llm
from app.services.assistant import tools as T
from app.services.assistant.tools import Ctx, chart, kpi, result, table, trend_word


# ------------------------------------------------------------------------------------------ growth
def growth_products(c: Ctx) -> dict:
    rng, label = c.period(30)
    prev, prev_label = _comparison(rng, label)
    c.use(prev, prev_label)
    n = c.parsed.top_n or 5
    decline = "decline" in c.parsed.flags
    cur = {r["product_id"]: r for r in A.top_products(c.db, rng, c.outlet_ids, 10_000, category_id=c.parsed.category_id)}
    before = {r["product_id"]: r for r in A.top_products(c.db, prev, c.outlet_ids, 10_000,
                                                          category_id=c.parsed.category_id)}
    total_prev = sum(r["revenue"] for r in before.values())
    # ignore tiny bases: a product must have had at least 0.2% of revenue (and 10 units) before
    min_base = max(0.002 * total_prev, 1.0)
    rows = []
    for pid, r in cur.items():
        b = before.get(pid)
        if not b or b["revenue"] < min_base or b["units"] < 10:
            continue
        rows.append({"name": r["name"], "category": r["category"], "revenue": r["revenue"], "previous": b["revenue"],
                     "change": round(r["revenue"] - b["revenue"], 2), "change_pct": A.pct_change(r["revenue"], b["revenue"]),
                     "units": r["units"], "previous_units": b["units"]})
    notes = []
    skipped = len(cur) - len(rows)
    if skipped:
        notes.append(f"{skipped} product(s) with very small sales in the previous period were left out, because "
                     "percentage growth on a tiny base is misleading.")
    if not rows:
        return result(f"There is not enough sales history at {c.scope_label} to compare {label} with the period "
                      "before it.", meta={"notes": notes + ["Growth needs sales in both periods."]})
    rows.sort(key=lambda r: (r["change_pct"] or 0), reverse=not decline)
    rows = rows[:n]
    word = "declining" if decline else "growing"
    ans = (f"The **{len(rows)} fastest-{word} products** at **{c.scope_label}** - **{label}** "
           f"({rng.start:%d %b} to {rng.end:%d %b}) vs {prev_label} ({prev.start:%d %b} to {prev.end:%d %b}), "
           "by revenue:\n" + "\n".join(
               f"{i}. **{r['name']}** ({r['category']}): {c.f.money(r['revenue'])} vs {c.f.money(r['previous'])} "
               f"(**{trend_word(r['change_pct'])}**, {c.f.num(r['units'])} vs {c.f.num(r['previous_units'])} units)"
               for i, r in enumerate(rows, 1)))
    blocks = [chart("bar", f"Fastest-{word} products (revenue change %)", rows, "name", [("change_pct", "Change %")],
                    "percent"),
              table("Products", [("name", "Product", "text"), ("category", "Category", "text"),
                                 ("revenue", "Revenue", "currency"), ("previous", "Previous", "currency"),
                                 ("change_pct", "Change", "percent")], rows)]
    return result(ans, blocks, [f"Forecast demand for {rows[0]['name']}", "Show the slowest products",
                                "Which categories are growing?"], {"notes": notes})


# ------------------------------------------------------------------------------------------ why did it change
def _comparison(rng: A.DateRange, label: str) -> tuple[A.DateRange, str]:
    return A.comparable_period(rng)


def why_change(c: Ctx) -> dict:
    if c.parsed.period:
        rng, label = c.clip(*c.parsed.period)
    else:
        rng = A.DateRange(c.anchor - timedelta(days=c.anchor.weekday()), c.anchor)
        label = "this week"
        if rng.days < 3:  # too early in the week - use the last 7 days
            rng, label = A.DateRange(c.anchor - timedelta(days=6), c.anchor), "the last 7 days"
    cmp, cmp_label = _comparison(rng, label)
    c.use(rng, label)
    c.use(cmp, cmp_label)
    r = D.explain_change(c.db, rng.start, rng.end, cmp.start, cmp.end, c.outlet_ids)
    if r.get("insufficient_data"):
        return result(f"I can't explain the change for {c.scope_label}: " + " ".join(r["summary"]),
                      meta={"notes": r["summary"]})
    asked_lower = "decline" in c.parsed.flags
    went_down = r["change"] < 0
    lines = [f"**{c.scope_label} - {label}** ({rng.start:%d %b} to {rng.end:%d %b}) compared with {cmp_label} "
             f"({cmp.start:%d %b} to {cmp.end:%d %b}):", ""]
    if asked_lower and not went_down:
        lines.append(f"Revenue was actually **not lower**: it is {trend_word(r['change_pct'])} "
                     f"({c.f.money(r['revenue'][0])} vs {c.f.money(r['revenue'][1])}).")
    summary = D.summary_lines(r, lambda v: c.f.money(abs(v)))
    lines += [f"- {x}" for x in (summary[1:] if asked_lower and not went_down else summary)]
    context = [x for x in r["anomalies"]][:3]
    if context:
        lines += ["", "**Unusual days in this period:**"] + [
            f"- {a['day']} at {a['outlet']}: {c.f.money(a['actual'])} vs {c.f.money(a['expected'])} expected. "
            f"{a['explanation']}" for a in context]
    notes = ["Driver effects other than bills and average bill are estimates; weather is an association, not proof "
             "of cause."]
    if r.get("scaled"):
        notes.append("The comparison period has a different length, so it was scaled to the same number of days.")
    drivers = [{"driver": x["label"], "effect": x["effect"], "detail": x["detail"]} for x in r["drivers"]]
    blocks = [{"type": "kpis", "items": [kpi("Revenue", r["revenue"][0], "currency", r["change_pct"]),
                                         kpi("Bills", r["bills"][0], "number", A.pct_change(r["bills"][0], r["bills"][1])),
                                         kpi("Avg bill", r["avg_bill"][0], "currency",
                                             A.pct_change(r["avg_bill"][0], r["avg_bill"][1]))]},
              chart("bar", "Estimated contribution to the change", drivers, "driver", [("effect", "Effect")]),
              table("Drivers", [("driver", "Driver", "text"), ("effect", "Effect", "currency"),
                                ("detail", "Evidence", "text")], drivers)]
    if len(r["outlets"]) > 1:
        blocks.append(table("By outlet", [("outlet", "Outlet", "text"), ("current", "This period", "currency"),
                                          ("previous", "Comparison", "currency"), ("change_pct", "Change", "percent")],
                            r["outlets"]))
    blocks.append(table("By category", [("category", "Category", "text"), ("current", "This period", "currency"),
                                        ("previous", "Comparison", "currency"), ("change", "Change", "currency")],
                        r["categories"]))
    return result("\n".join(lines), blocks, ["Summarize the major anomalies this month",
                                             "Which items may go out of stock in the next 14 days?"],
                  {"notes": notes})


# ------------------------------------------------------------------------------------------ stockout risk
def _risk_line(c: Ctx, r: dict) -> str:
    on_order = f"; {c.f.num(r['on_order'])} on order" if r["on_order"] else ""
    if r["current_stock"] <= 0:
        return (f"- **{r['product']}** at {r['outlet']}: **out of stock now**, normally sells "
                f"~{r['avg_daily_demand']:.1f}/day{on_order}")
    return (f"- **{r['product']}** at {r['outlet']}: {c.f.num(r['current_stock'])} {r['unit']} left, selling "
            f"~{r['avg_daily_demand']:.1f}/day - runs out around **{r['runs_out_on']}**{on_order}")


def stockout_risk(c: Ctx) -> dict:
    asked = c.parsed.horizon or 14
    days = min(max(asked, 1), 60)
    c.parsed.horizon = days  # shown in the provenance filters
    rows = F.stockout_risk(c.db, days, c.outlet_ids)
    if c.parsed.category_id:
        ids = set(c.db.scalars(select(Product.id).where(Product.category_id == c.parsed.category_id)).all())
        rows = [r for r in rows if r["product_id"] in ids]
    if c.parsed.product_ids:
        rows = [r for r in rows if r["product_id"] in c.parsed.product_ids]
    notes = ["Demand is the average of the last 28 days adjusted for the recent trend; open purchase orders count "
             "as stock on their expected delivery date."]
    if asked > 60:
        notes.append(f"Stock-out risk is projected at most 60 days ahead (you asked for {asked}).")
    if not rows:
        return result(f"No items at {c.scope_label} are expected to run out in the next **{days} days** - current "
                      "stock plus open purchase orders covers the expected demand.", [],
                      ["What should I reorder?", "Show low stock items"], {"notes": notes})
    lost = sum(r["lost_revenue_estimate"] for r in rows)
    now = [r for r in rows if r["days_left"] <= 0]
    ans = (f"**{len(rows)} item(s)** at **{c.scope_label}** may run out of stock in the next **{days} days**"
           f"{f' ({len(now)} already out or running out today)' if now else ''}. If nothing is ordered, about "
           f"**{c.f.money(lost)}** of sales could be lost.\n\n" + "\n".join(_risk_line(c, r) for r in rows[:10]))
    return result(ans, [table(f"Items at risk of running out within {days} days",
                              [("outlet", "Outlet", "text"), ("product", "Product", "text"),
                               ("current_stock", "In stock", "number"), ("avg_daily_demand", "Daily demand", "number"),
                               ("on_order", "On order", "number"), ("runs_out_on", "Runs out", "date"),
                               ("lost_revenue_estimate", "Sales at risk", "currency")], rows[:60])],
                  ["What should I reorder?", "Show pending purchase orders"], {"notes": notes})


# ------------------------------------------------------------------------------------------ weekend vs weekday
def weekend_compare(c: Ctx) -> dict:
    rng, label = c.period(56)
    q = select(Sale.outlet_id, Sale.sale_date, func.sum(Sale.total), func.count(Sale.id)).where(
        *A._sale_filters(rng, c.outlet_ids)).group_by(Sale.outlet_id, Sale.sale_date)
    names = A.outlet_names(c.db)
    agg: dict[int, dict] = {}
    for oid, day, rev, bills in c.db.execute(q).all():
        a = agg.setdefault(oid, {"we": [], "wd": [], "we_bills": 0, "wd_bills": 0})
        key = "we" if day.weekday() >= 5 else "wd"
        a[key].append(float(rev))
        a[f"{key}_bills"] += bills
    rows, notes = [], []
    for oid, a in agg.items():
        if len(a["we"]) < 2 or len(a["wd"]) < 4:
            notes.append(f"{names.get(oid)} has too few trading days in this period for a fair comparison.")
            continue
        we, wd = sum(a["we"]) / len(a["we"]), sum(a["wd"]) / len(a["wd"])
        total = sum(a["we"]) + sum(a["wd"])
        rows.append({"outlet": names.get(oid, str(oid)), "weekend_avg": round(we, 2), "weekday_avg": round(wd, 2),
                     "uplift_pct": A.pct_change(we, wd), "weekend_share_pct": round(sum(a["we"]) / total * 100, 1),
                     "weekend_days": len(a["we"]), "weekend_avg_bill": round(sum(a["we"]) / a["we_bills"], 2)
                     if a["we_bills"] else 0,
                     "weekday_avg_bill": round(sum(a["wd"]) / a["wd_bills"], 2) if a["wd_bills"] else 0})
    if not rows:
        return result(f"There are not enough weekend and weekday sales at {c.scope_label} in {label} to compare.",
                      meta={"notes": notes})
    rows.sort(key=lambda r: -r["weekend_avg"])
    best_uplift = max(rows, key=lambda r: r["uplift_pct"] or 0)
    ans = (f"**Weekend vs weekday sales** at {c.scope_label} for **{label}** ({rng.start:%d %b} to {rng.end:%d %b}), "
           "average revenue per day:\n" + "\n".join(
               f"- **{r['outlet']}**: weekend {c.f.money(r['weekend_avg'])} vs weekday {c.f.money(r['weekday_avg'])} "
               f"(**{trend_word(r['uplift_pct'])}** on weekends; weekends are {r['weekend_share_pct']:.0f}% of sales)"
               for r in rows))
    if len(rows) > 1:
        ans += (f"\n\n**{rows[0]['outlet']}** sells the most on a weekend day; **{best_uplift['outlet']}** has the "
                f"biggest weekend lift ({trend_word(best_uplift['uplift_pct'])}). Plan staff and stock for Saturdays "
                "and Sundays accordingly.")
    return result(ans, [chart("bar", "Average revenue per day", rows, "outlet",
                              [("weekend_avg", "Weekend day"), ("weekday_avg", "Weekday")]),
                        table("Weekend vs weekday", [("outlet", "Outlet", "text"),
                                                     ("weekend_avg", "Weekend / day", "currency"),
                                                     ("weekday_avg", "Weekday / day", "currency"),
                                                     ("uplift_pct", "Weekend lift", "percent"),
                                                     ("weekend_avg_bill", "Weekend avg bill", "currency"),
                                                     ("weekday_avg_bill", "Weekday avg bill", "currency"),
                                                     ("weekend_share_pct", "Weekend share", "percent_plain")], rows)],
                  ["When are our busiest hours?", "Which outlet had the highest revenue last month?"],
                  {"notes": notes})


# ------------------------------------------------------------------------------------------ model performance
def model_performance(c: Ctx) -> dict:
    p = c.parsed
    if p.product_ids:
        spec = F.build_spec(c.db, "product", p.product_ids[0], c.outlet_ids)
    elif p.category_id:
        spec = F.build_spec(c.db, "category", p.category_id, c.outlet_ids)
    elif c.outlet_ids and len(c.outlet_ids) == 1:
        spec = F.build_spec(c.db, "outlet", c.outlet_ids[0], c.outlet_ids)
    else:
        spec = F.build_spec(c.db, "total", None, c.outlet_ids)
    try:
        fc = F.forecast_series(c.db, spec, horizon=14)
    except ValueError as exc:
        return result(f"I couldn't evaluate the models for {spec.label}: {exc}", meta={"notes": [str(exc)]})
    scored = sorted([e for e in fc["evaluation"] if e.get("wape") is not None], key=lambda e: e["wape"])
    best, sel = scored[0], next(e for e in scored if e.get("selected"))
    base = next((e for e in scored if e["model"] == "seasonal_naive"), None)
    folds = fc.get("folds") or 1
    ans = (f"**{spec.label}**{' at ' + c.scope_label if spec.scope in ('category', 'product') else ''} - back-test "
           f"on the last {fc['test_days']} days in {folds} fold(s), data to {fc['as_of']}:\n\n"
           f"- Lowest error: **{best['label']}** with **{best['wape']:.1f}% WAPE**\n")
    if base:
        ans += f"- The seasonal-naive baseline scored {base['wape']:.1f}% WAPE"
        if best["wape"] < base["wape"]:
            ans += f", so the best model cuts the error by {(base['wape'] - best['wape']) / base['wape'] * 100:.0f}%"
        ans += "\n"
    if sel["model"] != best["model"]:
        ans += (f"- In production ERIS kept **{sel['label']}** ({sel['wape']:.1f}% WAPE): a challenger must beat "
                "the incumbent Prophet model by more than 10% to replace it, which avoids switching on noise.\n")
    else:
        ans += "- This is also the model ERIS uses for this forecast.\n"
    if sel.get("interval_coverage") is not None:
        ans += f"- The 80% prediction band covered {sel['interval_coverage']:.0f}% of days in the latest fold.\n"
    sources = [f"forecast run #{fc['run_id']}" if fc.get("run_id") else "live back-test"]
    ev = c.db.scalar(select(ForecastRun).where(ForecastRun.run_type == "evaluation", ForecastRun.status == "ok")
                     .order_by(ForecastRun.id.desc()))
    per_series = ((ev.parameters or {}).get("wape_by_series") or {}).get(spec.label) if ev else None
    if per_series:
        ranked = sorted(((m, w) for m, w in per_series.items() if w is not None), key=lambda x: x[1])
        ans += ("\nIn the rolling-origin evaluation (run #{}, {} origins of {} days): ".format(
            ev.id, (ev.parameters or {}).get("origins"), ev.horizon) + ", ".join(
                f"{F.short_label(m) if m != 'auto' else 'ERIS auto'} {w:.1f}%" for m, w in ranked) + " WAPE.")
        sources.append(f"evaluation run #{ev.id}")
    rows = [{"model": e["label"], "wape": e["wape"], "smape": e.get("smape"), "mae": e.get("mae"),
             "rmse": e.get("rmse"), "coverage": e.get("interval_coverage"),
             "selected": "selected" if e.get("selected") else ""} for e in scored]
    notes = [] if per_series else ["No rolling-origin evaluation covers this series yet - run one from the Model "
                                   "Comparison page for a more robust comparison."]
    notes.append("Accuracy is measured on synthetic demo data.")
    return result(ans, [chart("bar", f"Back-test error by model - {spec.label}", rows, "model", [("wape", "WAPE %")],
                              "number"),
                        table("Model comparison (lower is better)",
                              [("model", "Model", "text"), ("wape", "WAPE %", "number"), ("smape", "sMAPE %", "number"),
                               ("mae", "MAE", "number"), ("rmse", "RMSE", "number"),
                               ("coverage", "80% band coverage %", "number"), ("selected", "", "text")], rows)],
                  [f"Forecast {spec.label} for the next 30 days", "What is WAPE?"],
                  {"model_version": fc.get("model_version"), "notes": notes, "sources": sources,
                   "forecast_run_id": fc.get("run_id")})


# ------------------------------------------------------------------------------------------ anomalies
def anomalies(c: Ctx) -> dict:
    rng, label = c.period(30)
    found = AN.detect(c.db, rng.start, rng.end, c.outlet_ids)
    incidents = [a for a in found if not a.get("explained_by")]
    context = [a for a in found if a.get("explained_by")]
    lines_ = AN.suspicious_lines(c.db, rng.start, rng.end, c.outlet_ids)
    notes = [f"Flagged when daily revenue is {AN.Z_THRESHOLD:g}+ robust standard deviations from the outlet's "
             "expected level for that weekday."]
    if rng.days < 7:
        notes.append(f"Only {rng.days} day(s) of {label} have data so far - ask about the last 30 days for a fuller "
                     "picture.")
    if not found and not lines_:
        return result(f"No unusual days or suspicious bills at **{c.scope_label}** in **{label}** "
                      f"({rng.start:%d %b} to {rng.end:%d %b}). Sales stayed within their normal range.", [],
                      ["Why was revenue lower this week?", "How is business this week?"], {"notes": notes})
    major = sorted(incidents, key=lambda a: -abs(a["impact"]))
    ans = [f"**Unusual activity at {c.scope_label} - {label}** ({rng.start:%d %b} to {rng.end:%d %b}): "
           f"{len(incidents)} unusual outlet-day(s), {len(lines_)} suspicious bill line(s)"
           f"{f', and {len(context)} explained dip(s)' if context else ''}.", ""]
    for a in major[:6]:
        ans.append(f"- **{a['day']} - {a['outlet']}**: {c.f.money(a['actual'])} vs ~{c.f.money(a['expected'])} "
                   f"expected ({a['change_pct']:+.0f}%, {a['severity']}). {AN.explain(c.db, a)}")
    for x in lines_[:4]:
        ans.append(f"- **Suspicious entry** {x['invoice_no']} ({x['day']}, {x['outlet']}): {c.f.num(x['quantity'])} x "
                   f"{x['product']} - typical is about {x['typical_quantity']:g}. Check for a typing error.")
    if context:
        ans += ["", "Explained by context: " + "; ".join(f"{a['day']} {a['outlet']} ({a['explained_by']})"
                                                         for a in context[:4]) + "."]
    score = AN.score_against_labels(c.db, found, rng.start, rng.end, c.outlet_ids)
    if score and score["labelled"]:
        notes.append(f"On this period the detector found {score['true_positives']} of {score['labelled']} anomalies "
                     f"injected into the synthetic data (precision {score['precision']}, recall {score['recall']}).")
    rows = [{**a, "explanation": AN.explain(c.db, a)} for a in major]
    blocks = []
    if rows:
        blocks.append(table("Unusual days", [("day", "Date", "date"), ("outlet", "Outlet", "text"),
                                             ("actual", "Actual", "currency"), ("expected", "Expected", "currency"),
                                             ("change_pct", "Change", "percent"), ("severity", "Severity", "status"),
                                             ("explanation", "Evidence", "text")], rows))
    if lines_:
        blocks.append(table("Suspicious bill lines", [("day", "Date", "date"), ("invoice_no", "Bill", "text"),
                                                      ("outlet", "Outlet", "text"), ("product", "Product", "text"),
                                                      ("quantity", "Qty", "number"),
                                                      ("typical_quantity", "Typical qty", "number"),
                                                      ("line_total", "Amount", "currency")], lines_))
    return result("\n".join(ans), blocks, ["Why was revenue lower this week?", "Show the five fastest-growing products"],
                  {"notes": notes})


# ------------------------------------------------------------------------------------------ documentation (RAG)
def knowledge_answer(c: Ctx) -> dict:
    hits = knowledge.best_match(c.db, c.parsed.text)
    if not hits:
        return result("I couldn't find that in the ERIS documentation. I can explain metrics (WAPE, RFM, lift...), "
                      "how forecasts, imports, anomaly detection and demo invoices work, and where the data comes from.",
                      [], ["What is WAPE?", "How do I import sales?", "Where does the data come from?"],
                      {"notes": ["No documentation section matched the question closely enough."]})
    text = None
    if llm.status()["available"]:
        text = llm.document_answer(c.parsed.text, hits)
    if not text:
        text = "\n\n".join(f"**{h['title']}**\n\n{h['text']}" for h in hits)
    sources = [f"{h['source']} - {h['title']}" for h in hits]
    return result(text, [], ["How is the forecast model chosen?", "What is interval coverage?",
                             "How are anomalies detected?"],
                  {"sources": sources, "data_source": "ERIS project documentation"})


# ------------------------------------------------------------------------------------------ suppliers
def suppliers(c: Ctx) -> dict:
    """Supplier reliability: on-time rate of completed orders, lead time, open orders and recent purchases."""
    from app.models import OPEN_PO_STATUSES, PurchaseOrder, PurchaseOrderItem, Supplier

    since = c.anchor - timedelta(days=89)
    c.use(A.DateRange(c.anchor - timedelta(days=179), c.anchor), "the last 6 months")
    q = select(PurchaseOrder).where(PurchaseOrder.order_date >= c.anchor - timedelta(days=180))
    if c.outlet_ids:
        q = q.where(PurchaseOrder.outlet_id.in_(c.outlet_ids))
    orders = c.db.scalars(q).all()
    spend_q = select(PurchaseOrder.supplier_id, func.sum(PurchaseOrderItem.received_quantity * PurchaseOrderItem.unit_cost)).join(
        PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id).where(PurchaseOrder.received_date >= since)
    if c.outlet_ids:
        spend_q = spend_q.where(PurchaseOrder.outlet_id.in_(c.outlet_ids))
    spend = dict(c.db.execute(spend_q.group_by(PurchaseOrder.supplier_id)).all())
    rows = []
    for s in c.db.scalars(select(Supplier).where(Supplier.is_active.is_(True)).order_by(Supplier.name)).all():
        mine = [o for o in orders if o.supplier_id == s.id]
        done = [o for o in mine if o.status in ("received", "closed") and o.received_date and o.expected_date]
        on_time = sum(1 for o in done if o.received_date <= o.expected_date)
        open_orders = [o for o in mine if o.status in OPEN_PO_STATUSES]
        rows.append({"supplier": s.name, "lead_time_days": s.lead_time_days, "deliveries": len(done),
                     "on_time_pct": round(on_time / len(done) * 100, 1) if done else None,
                     "open_orders": len(open_orders),
                     "late_open": sum(1 for o in open_orders if o.expected_date and o.expected_date < c.anchor),
                     "purchases_90d": round(float(spend.get(s.id) or 0), 2)})
    if not rows:
        return result("No suppliers are set up yet - add them on the Suppliers page.")
    lines = [f"**Suppliers serving {c.scope_label}** (orders in the last 6 months):"]
    for r in sorted(rows, key=lambda r: -r["purchases_90d"]):
        ot = (f"{r['on_time_pct']:.0f}% on time over {r['deliveries']} deliveries" if r["on_time_pct"] is not None
              else "no completed deliveries")
        lines.append(f"- **{r['supplier']}**: {ot}, lead time {r['lead_time_days']} days, purchases "
                     f"{c.f.money(r['purchases_90d'])} in 90 days, {r['open_orders']} open order(s)")
    rated = sorted([r for r in rows if r["on_time_pct"] is not None and r["deliveries"] >= 3],
                   key=lambda r: (-r["on_time_pct"], r["lead_time_days"]))
    if rated:
        best, worst = rated[0], rated[-1]
        lines.append(f"\nMost reliable: **{best['supplier']}** ({best['on_time_pct']:.0f}% on time, "
                     f"{best['lead_time_days']}-day lead time).")
        if worst is not best:
            lines[-1] += f" Least reliable: **{worst['supplier']}** ({worst['on_time_pct']:.0f}% on time)."
    late = [r for r in rows if r["late_open"]]
    if late:
        lines.append("Overdue deliveries: " + ", ".join(f"{r['supplier']} ({r['late_open']})" for r in late) + ".")
    cols = [("supplier", "Supplier", "text"), ("on_time_pct", "On time %", "number"), ("deliveries", "Deliveries", "number"),
            ("lead_time_days", "Lead time (days)", "number"), ("open_orders", "Open orders", "number"),
            ("purchases_90d", "Purchases (90 days)", "currency")]
    return result("\n".join(lines), [table("Suppliers", cols, rows)],
                  ["Show pending purchase orders", "What should I reorder?"],
                  {"notes": ["On-time rate = completed orders received on or before their expected date."]})


# ------------------------------------------------------------------------------------------ guard rails
PAGES_FOR = {"invoice": "Sales → open a bill → Issue GST invoice", "sale": "Sales → New sale (or Void on a bill)",
             "bill": "Sales", "product": "Products", "price": "Products", "stock": "Inventory → Adjust / Transfer",
             "inventory": "Inventory", "order": "Suppliers & orders or Inventory → Reorder",
             "purchase": "Suppliers & orders", "supplier": "Suppliers & orders", "customer": "Customers",
             "user": "Settings → Users & roles", "outlet": "Outlets", "password": "Settings → My profile",
             "import": "Data import", "data": "Data import or Settings → System & data"}


def action_request(c: Ctx) -> dict:
    import re as _re

    t = c.parsed.text.lower()
    where = next((page for word, page in PAGES_FOR.items() if _re.search(rf"\b{word}", t)), None)
    ans = ("I can only **read and analyse** your data - I never create, change or delete anything, so nothing has been "
           "changed. " + (f"You can do this yourself on **{where}**." if where else "Use the relevant page in the menu "
                                                                                 "to make changes."))
    return result(ans, [], ["How is business this week?", "What should I reorder?"],
                  {"data_source": "none - no data was read or changed"})


def smalltalk(c: Ctx) -> dict:
    t = c.parsed.text.lower()
    ans = "Goodbye - your data will be here when you're back." if "bye" in t or "night" in t else \
        "You're welcome! Ask me anything else about your sales, stock or forecasts."
    return result(ans, [], ["How is business this week?", "Summarize the major anomalies this month"],
                  {"data_source": "none"})


DISPATCH = {
    **T.DISPATCH,
    "growth_products": growth_products,
    "why_change": why_change,
    "stockout_risk": stockout_risk,
    "weekend_compare": weekend_compare,
    "model_performance": model_performance,
    "anomalies": anomalies,
    "knowledge": knowledge_answer,
    "suppliers": suppliers,
    "action_request": action_request,
    "smalltalk": smalltalk,
}
