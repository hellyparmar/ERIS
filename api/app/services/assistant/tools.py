"""Answer builders: each intent runs real analytics and returns a narrative plus structured blocks
(KPI tiles, charts and tables) that the UI renders."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.models import OPEN_PO_STATUSES, InventoryItem, Organization, Outlet, Product, PurchaseOrder, Supplier
from app.services import analytics as A
from app.services import forecasting as F
from app.services.alerts import compute_alerts
from app.services.assistant.nlu import Parsed
from app.services.holidays import upcoming_events
from app.services.inventory import stock_status

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------------------------------------------------------------------------------------ formatting
class Fmt:
    def __init__(self, symbol: str = "₹"):
        self.symbol = symbol

    def money(self, v: float) -> str:
        v = float(v or 0)
        sign = "-" if v < 0 else ""
        v = abs(v)
        if self.symbol == "₹":
            if v >= 1e7:
                return f"{sign}₹{v / 1e7:.2f} Cr"
            if v >= 1e5:
                return f"{sign}₹{v / 1e5:.2f} L"
            return f"{sign}₹{indian(v)}"
        return f"{sign}{self.symbol}{v:,.0f}"

    @staticmethod
    def num(v: float) -> str:
        v = float(v or 0)
        return indian(v) if abs(v) >= 1 or v == 0 else f"{v:.2f}"

    @staticmethod
    def pct(v: float | None, signed: bool = True) -> str:
        if v is None:
            return "n/a"
        return f"{v:+.1f}%" if signed else f"{v:.1f}%"


def indian(v: float) -> str:
    """1234567 -> 12,34,567 (Indian digit grouping)."""
    n = int(round(v))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + s


def trend_word(ch: float | None) -> str:
    if ch is None:
        return ""
    if ch >= 0.5:
        return f"up {ch:.1f}%"
    if ch <= -0.5:
        return f"down {abs(ch):.1f}%"
    return "flat"


class Ctx:
    def __init__(self, db: Session, user_outlet_ids: list[int] | None, parsed: Parsed):
        self.db = db
        self.parsed = parsed
        org = db.scalar(select(Organization))
        self.f = Fmt(org.currency_symbol if org else "₹")
        self.anchor = A.anchor_date(db)
        # Outlet scope: the user's allowed outlets narrowed by outlets mentioned in the question.
        mentioned = parsed.outlet_ids
        if user_outlet_ids:
            mentioned = [o for o in mentioned if o in user_outlet_ids] or user_outlet_ids
        self.outlet_ids = mentioned or None
        self.scope_label = ", ".join(parsed.outlet_names) if parsed.outlet_ids and self.outlet_ids == parsed.outlet_ids \
            else ("all outlets" if not self.outlet_ids else ", ".join(
                db.scalars(select(Outlet.name).where(Outlet.id.in_(self.outlet_ids))).all()))

        self.used_periods: list[tuple[A.DateRange, str]] = []
        self.fallback: tuple[str, str, date] | None = None  # (period asked for, period answered, last data day)

    def period(self, default_days: int = 30) -> tuple[A.DateRange, str]:
        if self.parsed.period:
            chosen = self.clip(*self.parsed.period)
        else:
            chosen = (A.DateRange(self.anchor - timedelta(days=default_days - 1), self.anchor),
                      f"the last {default_days} days")
        self.use(*chosen)
        return chosen

    def clip(self, rng: A.DateRange, label: str) -> tuple[A.DateRange, str]:
        """Periods that run past the last day with sales data (e.g. "this week" when today has no bills yet)
        end on that day instead, so partial or empty days do not distort comparisons. A period that lies entirely
        after the data (e.g. "this week" on a Monday morning, before any bill) becomes the latest period of the
        same length (at least a week, or the latest day for "today") - the answer says so (self.fallback)."""
        if rng.start <= self.anchor < rng.end:
            return A.DateRange(rng.start, self.anchor), label
        latest = A.latest_sale_date(self.db)
        if latest and rng.start > latest:
            days = 1 if label == "today" else max(rng.days, 7)
            new = A.DateRange(latest - timedelta(days=days - 1), latest)
            new_label = f"{latest:%a %d %b} (the latest day with data)" if days == 1 else \
                f"the latest {days} days ({new.start:%d %b} to {new.end:%d %b})"
            self.fallback = (label, new_label, latest)
            return new, new_label
        return rng, label

    def use(self, rng: A.DateRange, label: str) -> None:
        """Record a period an answer is based on (shown in the answer's provenance)."""
        if not any(r.start == rng.start and r.end == rng.end for r, _ in self.used_periods):
            self.used_periods.append((rng, label))


def result(answer: str, blocks: list | None = None, suggestions: list | None = None, meta: dict | None = None) -> dict:
    """meta (optional): model_version, notes (insufficient-data caveats), sources (documents), data_source."""
    return {"answer": answer, "blocks": blocks or [], "suggestions": suggestions or [], "meta": meta or {}}


def kpi(label: str, value, fmt: str = "number", change: float | None = None, hint: str | None = None) -> dict:
    return {"label": label, "value": value, "format": fmt, "change": change, "hint": hint}


def table(title: str, columns: list[tuple[str, str, str]], rows: list[dict]) -> dict:
    return {"type": "table", "title": title,
            "columns": [{"key": k, "label": label, "format": fmt} for k, label, fmt in columns], "rows": rows}


def chart(kind: str, title: str, data: list[dict], x: str, series: list[tuple[str, str]], fmt: str = "currency") -> dict:
    return {"type": "chart", "chart": kind, "title": title, "data": data, "x": x,
            "series": [{"key": k, "label": label} for k, label in series], "format": fmt}


# ------------------------------------------------------------------------------------------ intents
def business_overview(c: Ctx) -> dict:
    rng = A.DateRange(c.anchor - timedelta(days=6), c.anchor)
    c.use(rng, "last 7 days")
    k = A.kpis_with_comparison(c.db, rng, c.outlet_ids)
    cur, ch = k["current"], k["change_pct"]
    if not cur["orders"]:
        return result(f"No sales have been recorded at {c.scope_label} in the last 7 days. Record bills on the Sales "
                      "page or import your sales history (Data import) and I can summarise how business is going.",
                      [], ["How do I import sales?", "What should I reorder?"])
    outlets = A.outlet_performance(c.db, rng, c.outlet_ids)
    cats = A.category_breakdown(c.db, rng, c.outlet_ids)
    alerts = compute_alerts(c.db, c.outlet_ids)
    lines = [f"**Business snapshot for {c.scope_label} - last 7 days (to {c.anchor:%d %b %Y})**", ""]
    lines.append(f"- Revenue **{c.f.money(cur['revenue'])}** ({trend_word(ch['revenue'])} vs the previous week) "
                 f"from **{c.f.num(cur['orders'])}** bills, average bill **{c.f.money(cur['avg_basket'])}**.")
    lines.append(f"- Gross profit **{c.f.money(cur['gross_profit'])}** at a **{cur['margin_pct']:.1f}%** margin.")
    if len(outlets) > 1:
        best = outlets[0]
        movers = [o for o in outlets if o["change_pct"] is not None]
        worst = min(movers, key=lambda o: o["change_pct"]) if movers else None
        lines.append(f"- Top outlet: **{best['name']}** ({c.f.money(best['revenue'])}, {best['share_pct']:.0f}% of sales).")
        if worst and worst["change_pct"] < 0:
            lines.append(f"- Needs attention: **{worst['name']}** is {trend_word(worst['change_pct'])} week on week.")
    growing = [x for x in cats if (x["change_pct"] or 0) > 5]
    if growing:
        g = max(growing, key=lambda x: x["change_pct"])
        lines.append(f"- Fastest-growing category: **{g['category']}** ({trend_word(g['change_pct'])}).")
    try:
        spec = F.build_spec(c.db, "total", None, c.outlet_ids)
        fc = F.forecast_series(c.db, spec, horizon=7)
        lines.append(f"- Forecast for the next 7 days: **{c.f.money(fc['summary']['next_7_days'])}** "
                     f"({trend_word(fc['summary']['change_vs_last_7_pct'])} vs this week).")
    except Exception:
        pass
    important = [a for a in alerts if a["severity"] in ("critical", "warning")][:4]
    if important:
        lines += ["", "**What to focus on:**"] + [f"- {a['title']} - {a['message']}" for a in important]
    blocks = [{"type": "kpis", "items": [
        kpi("Revenue (7d)", cur["revenue"], "currency", ch["revenue"]),
        kpi("Bills", cur["orders"], "number", ch["orders"]),
        kpi("Avg bill", cur["avg_basket"], "currency", ch["avg_basket"]),
        kpi("Gross profit", cur["gross_profit"], "currency", ch["gross_profit"]),
    ]}]
    if len(outlets) > 1:
        blocks.append(chart("bar", "Revenue by outlet - last 7 days", outlets, "name", [("revenue", "Revenue")]))
    return result("\n".join(lines), blocks, ["What should I reorder?", "Forecast sales for next week",
                                             "Which products are growing fastest this month?"])


def sales_summary(c: Ctx) -> dict:
    rng, label = c.period(30)
    return _sales_summary(c, rng, label)


def _sales_summary(c: Ctx, rng: A.DateRange, label: str) -> dict:
    p = c.parsed
    if p.product_ids:
        return product_performance(c, rng, label)
    prev, prev_label = A.comparable_period(rng)
    c.use(prev, prev_label)
    k = A.kpis_with_comparison(c.db, rng, c.outlet_ids, prev) if not p.category_id else None
    if p.category_id:
        series = A.revenue_series(c.db, rng, c.outlet_ids, "day", category_id=p.category_id)
        prev_series = A.revenue_series(c.db, prev, c.outlet_ids, "day", category_id=p.category_id)
        rev, prev_rev = sum(s["revenue"] for s in series), sum(s["revenue"] for s in prev_series)
        units = sum(s["units"] for s in series)
        profit = sum(s["profit"] for s in series)
        ch = A.pct_change(rev, prev_rev)
        ans = (f"**{p.category_name}** sales at {c.scope_label} for {label}: **{c.f.money(rev)}** "
               f"({trend_word(ch)} vs {prev_label}), **{c.f.num(units)}** units sold, "
               f"gross profit **{c.f.money(profit)}**.")
        tops = A.top_products(c.db, rng, c.outlet_ids, 5, category_id=p.category_id)
        blocks = [{"type": "kpis", "items": [kpi("Revenue", rev, "currency", ch), kpi("Units", units),
                                             kpi("Gross profit", profit, "currency")]},
                  chart("area", f"{p.category_name} - daily revenue", series, "date", [("revenue", "Revenue")])]
        if tops:
            ans += f" Best seller: **{tops[0]['name']}** ({c.f.money(tops[0]['revenue'])})."
            blocks.append(table("Top products in category", [("name", "Product", "text"), ("units", "Units", "number"),
                                                              ("revenue", "Revenue", "currency")], tops))
        return result(ans, blocks, [f"Forecast {p.category_name} for next month", f"Slow moving {p.category_name} items"])

    cur, ch = k["current"], k["change_pct"]
    if cur["orders"] == 0:
        return result(f"No sales have been recorded for **{label}** at {c.scope_label} yet.", [],
                      ["How much did we sell yesterday?", "Sales in the last 7 days"])
    single_day = rng.days == 1
    ans = (f"For **{label}** at **{c.scope_label}**, revenue was **{c.f.money(cur['revenue'])}** from "
           f"**{c.f.num(cur['orders'])}** bills (average bill **{c.f.money(cur['avg_basket'])}**, "
           f"{cur['items_per_basket']:.1f} items per bill).")
    if ch["revenue"] is not None:
        ans += f" That is **{trend_word(ch['revenue'])}** compared with {prev_label} ({prev.start:%d %b}" + (
            f" to {prev.end:%d %b})." if not single_day else ").")
    ans += f" Gross profit was **{c.f.money(cur['gross_profit'])}** ({cur['margin_pct']:.1f}% margin)."
    blocks = [{"type": "kpis", "items": [
        kpi("Revenue", cur["revenue"], "currency", ch["revenue"]),
        kpi("Bills", cur["orders"], "number", ch["orders"]),
        kpi("Avg bill", cur["avg_basket"], "currency", ch["avg_basket"]),
        kpi("Gross profit", cur["gross_profit"], "currency", ch["gross_profit"]),
    ]}]
    if rng.days > 1:
        gran = "month" if rng.days > 120 else ("week" if rng.days > 45 else "day")
        series = A.revenue_series(c.db, rng, c.outlet_ids, gran)
        blocks.append(chart("area", f"Revenue by {gran}", series, "date", [("revenue", "Revenue"), ("profit", "Gross profit")]))
    if not c.outlet_ids or len(c.outlet_ids) > 1:
        outlets = A.outlet_performance(c.db, rng, c.outlet_ids)
        blocks.append(table("By outlet", [("name", "Outlet", "text"), ("revenue", "Revenue", "currency"),
                                          ("orders", "Bills", "number"), ("change_pct", "Change", "percent")], outlets))
    return result(ans, blocks, ["Which products sold the most?", "Compare this month with last month",
                                "Show the sales trend for the last 6 months"])


def product_performance(c: Ctx, rng: A.DateRange, label: str) -> dict:
    p = c.parsed
    rows = A.top_products(c.db, rng, c.outlet_ids, limit=10, product_ids=p.product_ids)
    prev = {r["product_id"]: r for r in A.top_products(c.db, rng.previous(), c.outlet_ids, limit=10,
                                                       product_ids=p.product_ids)}
    if not rows:
        return result(f"No sales of {', '.join(p.product_names)} at {c.scope_label} in {label}.", [],
                      [f"Stock of {p.product_names[0]}"])
    lines = []
    for r in rows:
        pr = prev.get(r["product_id"])
        ch = A.pct_change(r["units"], pr["units"]) if pr else None
        lines.append(f"- **{r['name']}**: {c.f.num(r['units'])} units, {c.f.money(r['revenue'])} revenue, "
                     f"{r['margin_pct']:.1f}% margin{f' ({trend_word(ch)} in units)' if ch is not None else ''}.")
    stock_rows = _stock_rows(c, product_ids=p.product_ids)
    total_stock = sum(s["quantity"] for s in stock_rows)
    ans = f"Sales at **{c.scope_label}** for **{label}**:\n" + "\n".join(lines)
    if stock_rows:
        n_outlets = len({s["outlet"] for s in stock_rows})
        ans += f"\n\nCurrent stock: **{c.f.num(total_stock)}** units across {n_outlets} outlet(s)."
    series = A.revenue_series(c.db, rng, c.outlet_ids, "day" if rng.days <= 60 else "week",
                              product_id=p.product_ids[0])
    blocks = [chart("bar", f"{rows[0]['name']} - units sold", series, "date", [("units", "Units")], "number")]
    if stock_rows:
        blocks.append(table("Stock by outlet", [("outlet", "Outlet", "text"), ("product", "Product", "text"),
                                                ("quantity", "In stock", "number"), ("days_of_cover", "Days of cover", "number"),
                                                ("status", "Status", "status")], stock_rows))
    return result(ans, blocks, [f"Forecast demand for {rows[0]['name']}", "What should I reorder?"])


def compare_periods(c: Ctx) -> dict:
    periods = c.parsed.periods
    if len(periods) >= 2:
        (r1, l1), (r2, l2) = periods[0], periods[1]
        if r1.start < r2.start:  # "March 2025 vs March 2026": describe the later period against the earlier one
            (r1, l1), (r2, l2) = (r2, l2), (r1, l1)
    else:
        r1, l1 = c.period(30)
        r2, l2 = r1.previous(), "the previous period"
        if c.parsed.period and "month" in l1 and r1.start.day == 1:
            prev_end = r1.start - timedelta(days=1)
            r2, l2 = A.DateRange(prev_end.replace(day=1), prev_end), f"{prev_end:%B %Y}"
    c.use(r1, l1)
    c.use(r2, l2)
    k1, k2 = A.kpis(c.db, r1, c.outlet_ids), A.kpis(c.db, r2, c.outlet_ids)
    metrics = [("revenue", "Revenue", "currency"), ("orders", "Bills", "number"), ("avg_basket", "Avg bill", "currency"),
               ("units", "Units", "number"), ("gross_profit", "Gross profit", "currency"), ("margin_pct", "Margin %", "percent_plain"),
               ("avg_daily_revenue", "Avg daily revenue", "currency")]
    rows = [{"metric": label, l1: k1[key], l2: k2[key], "change": A.pct_change(k1[key], k2[key]), "_format": fmt}
            for key, label, fmt in metrics]
    ch = A.pct_change(k1["revenue"], k2["revenue"])
    ch_daily = A.pct_change(k1["avg_daily_revenue"], k2["avg_daily_revenue"])
    ans = (f"**{l1}** vs **{l2}** at {c.scope_label}: revenue {c.f.money(k1['revenue'])} vs "
           f"{c.f.money(k2['revenue'])} (**{trend_word(ch)}**).")
    if r1.days != r2.days:
        ans += (f" The periods differ in length ({r1.days} vs {r2.days} days), so compare the average daily revenue: "
                f"**{trend_word(ch_daily)}**.")
    ans += f" Average bill moved from {c.f.money(k2['avg_basket'])} to {c.f.money(k1['avg_basket'])}."
    cols = [("metric", "Metric", "text"), (l1, l1, "auto"), (l2, l2, "auto"), ("change", "Change", "percent")]
    return result(ans, [table("Period comparison", cols, rows)], ["Show the sales trend", "Which outlet grew the most?"])


def sales_trend(c: Ctx) -> dict:
    if c.parsed.period:
        rng, label = c.parsed.period
    else:
        start = max(A.first_sale_date(c.db) or c.anchor, c.anchor - timedelta(days=364))
        rng, label = A.DateRange(start.replace(day=1), c.anchor), "the last 12 months"
    c.use(rng, label)
    gran = "month" if rng.days > 90 else ("week" if rng.days > 31 else "day")
    series = A.revenue_series(c.db, rng, c.outlet_ids, gran, category_id=c.parsed.category_id,
                              product_id=c.parsed.product_ids[0] if c.parsed.product_ids else None)
    if not series or not any(s["revenue"] for s in series):
        return result(f"There are no sales for {c.scope_label} in {label}.")
    first_sale = next((i for i, x in enumerate(series) if x["revenue"] > 0), 0)
    series = series[first_sale:]  # start the trend where the data starts
    complete = series[:-1] if gran == "month" and len(series) > 2 and c.anchor.day < 25 else series
    best = max(complete, key=lambda s: s["revenue"])
    worst = min([s for s in complete if s["revenue"] > 0] or complete, key=lambda s: s["revenue"])
    def lbl(d: str) -> str:
        dt = date.fromisoformat(d)
        return f"{dt:%b %Y}" if gran == "month" else (f"week of {dt:%d %b}" if gran == "week" else f"{dt:%d %b}")

    first, last = complete[0]["revenue"], complete[-1]["revenue"]
    what = c.parsed.product_names[0] if c.parsed.product_ids else (c.parsed.category_name or "Revenue")
    change = trend_word(A.pct_change(last, first))
    ans = (f"**{what}** trend for {c.scope_label} over {label} (by {gran}): from {c.f.money(first)} to "
           f"{c.f.money(last)}{f' (**{change}**)' if change else ''}. Best {gran}: **{lbl(best['date'])}** "
           f"({c.f.money(best['revenue'])}); weakest: **{lbl(worst['date'])}** ({c.f.money(worst['revenue'])}).")
    if gran == "month" and len(series) > 1 and complete is not series:
        ans += " (The current month is still in progress, so it is excluded from the comparison.)"
    return result(ans, [chart("line", f"{what} by {gran}", series, "date", [("revenue", "Revenue"), ("profit", "Gross profit")])],
                  ["Forecast the next 30 days", "Which categories are growing?"])


def top_products(c: Ctx, slow: bool = False) -> dict:
    rng, label = c.period(30)
    n = c.parsed.top_n or 10
    sort = c.parsed.sort
    rows = A.top_products(c.db, rng, c.outlet_ids, n, sort=sort, ascending=slow, category_id=c.parsed.category_id)
    if not rows:
        return result(f"No product sales found for {c.scope_label} in {label}.")
    measure = {"revenue": "revenue", "units": "units sold", "profit": "gross profit"}[sort]
    what = f"{c.parsed.category_name} products" if c.parsed.category_id else "products"
    head = f"{'Slowest' if slow else 'Top'} {len(rows)} {what} by {measure} at **{c.scope_label}** for **{label}**:"
    lines = [f"{i}. **{r['name']}** - {c.f.money(r['revenue'])}, {c.f.num(r['units'])} units, {r['margin_pct']:.0f}% margin"
             for i, r in enumerate(rows, 1)]
    ans = head + "\n" + "\n".join(lines[:10])
    if slow:
        abc = A.abc_analysis(c.db, rng, c.outlet_ids)
        if abc["not_sold"]:
            ans += f"\n\n{len(abc['not_sold'])} active product(s) had **no sales at all**: " + ", ".join(
                x["name"] for x in abc["not_sold"][:5]) + "."
        ans += "\n\nConsider promotions, smaller order quantities or delisting for items that keep appearing here."
    else:
        share = sum(r["share_pct"] for r in rows)
        ans += f"\n\nTogether they make up **{share:.0f}%** of sales."
    key = {"revenue": "revenue", "units": "units", "profit": "profit"}[sort]
    blocks = [chart("bar", f"{'Slowest' if slow else 'Top'} products by {measure}", rows, "name", [(key, measure.title())],
                    "number" if sort == "units" else "currency"),
              table("Products", [("name", "Product", "text"), ("category", "Category", "text"), ("units", "Units", "number"),
                                 ("revenue", "Revenue", "currency"), ("margin_pct", "Margin", "percent_plain")], rows)]
    return result(ans, blocks, ["Forecast demand for " + rows[0]["name"], "Show category performance",
                                "What should I reorder?"])


def outlet_ranking(c: Ctx) -> dict:
    rng, label = c.period(30)
    rows = A.outlet_performance(c.db, rng, c.outlet_ids if c.outlet_ids and len(c.outlet_ids) > 1 else
                                (None if not c.parsed.outlet_ids else c.outlet_ids))
    rows = [r for r in rows if r["orders"] > 0] or rows
    if not rows:
        return result("No outlet sales found for that period.")
    best, worst = rows[0], rows[-1]
    ans = f"Outlet performance for **{label}**:\n" + "\n".join(
        f"{i}. **{r['name']}** ({r['city']}) - {c.f.money(r['revenue'])}, {c.f.num(r['orders'])} bills, avg bill "
        f"{c.f.money(r['avg_basket'])}, {trend_word(r['change_pct']) or 'new'}" for i, r in enumerate(rows, 1))
    if len(rows) > 1:
        movers = [r for r in rows if r["change_pct"] is not None]
        if movers:
            up = max(movers, key=lambda r: r["change_pct"])
            down = min(movers, key=lambda r: r["change_pct"])
            ans += (f"\n\n**{best['name']}** leads with {best['share_pct']:.0f}% of revenue; **{worst['name']}** is lowest. "
                    f"Biggest improvement: **{up['name']}** ({trend_word(up['change_pct'])}).")
            if down["change_pct"] < 0:
                ans += f" Biggest decline: **{down['name']}** ({trend_word(down['change_pct'])})."
    blocks = [chart("bar", "Revenue by outlet", rows, "name", [("revenue", "Revenue"), ("previous_revenue", "Previous period")]),
              table("Outlets", [("name", "Outlet", "text"), ("revenue", "Revenue", "currency"), ("orders", "Bills", "number"),
                                ("avg_basket", "Avg bill", "currency"), ("margin_pct", "Margin", "percent_plain"),
                                ("change_pct", "Change", "percent")], rows)]
    return result(ans, blocks, [f"Why is {worst['name']} lower?", f"Top products at {best['name']}",
                                "Forecast revenue for each outlet"])


def category_mix(c: Ctx) -> dict:
    rng, label = c.period(30)
    rows = A.category_breakdown(c.db, rng, c.outlet_ids)
    if not rows:
        return result("No category sales found for that period.")
    ans = f"Category performance at **{c.scope_label}** for **{label}**:\n" + "\n".join(
        f"- **{r['category']}**: {c.f.money(r['revenue'])} ({r['share_pct']:.0f}% of sales, {r['margin_pct']:.0f}% margin"
        f"{', ' + trend_word(r['change_pct']) if r['change_pct'] is not None else ''})" for r in rows)
    growers = [r for r in rows if r["change_pct"] is not None]
    if growers:
        g = max(growers, key=lambda r: r["change_pct"])
        d = min(growers, key=lambda r: r["change_pct"])
        ans += (f"\n\nGrowing fastest: **{g['category']}** ({trend_word(g['change_pct'])}). "
                f"Weakest: **{d['category']}** ({trend_word(d['change_pct'])}).")
    return result(ans, [chart("pie", "Sales mix by category", rows, "category", [("revenue", "Revenue")]),
                        table("Categories", [("category", "Category", "text"), ("revenue", "Revenue", "currency"),
                                             ("share_pct", "Share", "percent_plain"), ("margin_pct", "Margin", "percent_plain"),
                                             ("change_pct", "Change", "percent")], rows)],
                  [f"Top products in {rows[0]['category']}", f"Forecast {rows[0]['category']} sales"])


def forecast(c: Ctx) -> dict:
    p = c.parsed
    horizon = p.horizon or 30
    try:
        if p.product_ids:
            spec = F.build_spec(c.db, "product", p.product_ids[0], c.outlet_ids)
        elif p.category_id:
            spec = F.build_spec(c.db, "category", p.category_id, c.outlet_ids)
        elif c.outlet_ids and len(c.outlet_ids) == 1:
            spec = F.build_spec(c.db, "outlet", c.outlet_ids[0], c.outlet_ids)
        else:
            spec = F.build_spec(c.db, "total", None, c.outlet_ids)
        fc = F.forecast_series(c.db, spec, horizon=horizon)
    except ValueError as exc:
        return result(f"I couldn't build a forecast: {exc}")
    s = fc["summary"]
    is_units = spec.target == "units"
    val = (lambda v: f"{c.f.num(v)} units") if is_units else c.f.money
    where = f" at {c.scope_label}" if spec.scope in ("category", "product") else ""
    ans = (f"**{spec.label}{where}** - forecast for the next **{horizon} days** (from {fc['forecast'][0]['date']}):\n\n"
           f"- Expected total: **{val(s['horizon_total'])}** (about {val(s['avg_daily'])} per day)\n"
           f"- Next 7 days: **{val(s['next_7_days'])}** ({trend_word(s['change_vs_last_7_pct'])} vs the last 7 days)\n")
    if s.get("next_30_days") is not None:
        ans += f"- Next 30 days vs last 30 days: **{trend_word(s['change_vs_last_30_pct'])}**\n"
    if s.get("same_period_last_year"):
        ans += f"- Same period last year: {val(s['same_period_last_year'])}\n"
    ans += f"- Peak day: **{s['peak_day']['date']}** ({val(s['peak_day']['yhat'])})\n"
    if fc["events"]:
        ans += "- Festivals in the window: " + ", ".join(f"{e['name']} ({e['date']})" for e in fc["events"]) + "\n"
    sel = next(e for e in fc["evaluation"] if e.get("selected"))
    ans += (f"\nModel: **{fc['model_label']}**, chosen automatically after back-testing {len(fc['evaluation'])} models on the "
            f"last {fc['test_days']} days (error {sel['wape']:.1f}% WAPE). The shaded band is the 80% range.")
    blocks = [{"type": "forecast", "title": spec.label, "history": fc["history"][-60:], "forecast": fc["forecast"],
               "format": "number" if is_units else "currency"}]
    if spec.scope == "product":
        plan = F.product_stock_plan(c.db, spec.product_id, fc, c.outlet_ids)
        cover = plan["days_of_cover"]
        ans += (f"\n\n**Stock check:** {c.f.num(plan['current_stock'])} {plan['unit']} in stock"
                f"{f' - about {cover:.0f} days of cover' if cover is not None else ''}.")
        if plan["projected_stockout"]:
            ans += f" At the forecast rate it runs out around **{plan['projected_stockout']}**."
        if plan["recommended_order_qty"] > 0:
            ans += (f" Recommended order: **{plan['recommended_order_qty']} {plan['unit']}** "
                    f"(covers lead time of {plan['lead_time_days']} days + 1 week, with safety stock).")
        else:
            ans += (f" No order needed yet - place one by **{plan['reorder_by']}** to avoid running out."
                    if plan["reorder_by"] else " No reorder needed right now.")
    blocks.append(table("Model back-test (lower error is better)",
                        [("label", "Model", "text"), ("wape", "WAPE %", "number"), ("mape", "MAPE %", "number"),
                         ("mae", "MAE", "number")], [e for e in fc["evaluation"] if e.get("wape") is not None]))
    hist_range = fc.get("data_range") or {}
    return result(ans, blocks, ["What should I reorder?", "Forecast each category for next month",
                                "Which outlet will sell the most next week?"],
                  {"model_version": fc.get("model_version"), "forecast_run_id": fc.get("run_id"),
                   "notes": [f"Trained on {hist_range.get('days')} days of history ({hist_range.get('start')} to "
                             f"{hist_range.get('end')})."] if hist_range else []})


def _stock_rows(c: Ctx, product_ids: list[int] | None = None, category_id: int | None = None) -> list[dict]:
    q = select(InventoryItem, Product, Outlet).join(Product, Product.id == InventoryItem.product_id).join(
        Outlet, Outlet.id == InventoryItem.outlet_id).where(Product.is_active.is_(True))
    if c.outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(c.outlet_ids))
    if product_ids:
        q = q.where(Product.id.in_(product_ids))
    if category_id:
        q = q.where(Product.category_id == category_id)
    demand = A.avg_daily_units_by_outlet_product(c.db, 28, c.anchor)
    rows = []
    for inv, p, o in c.db.execute(q).all():
        rate = demand.get((o.id, p.id), 0)
        rows.append({"outlet": o.name, "product": p.name, "sku": p.sku, "quantity": inv.quantity, "unit": p.unit,
                     "reorder_level": inv.reorder_level, "avg_daily_demand": round(rate, 2),
                     "days_of_cover": round(inv.quantity / rate, 1) if rate > 0 else None,
                     "status": stock_status(inv.quantity, inv.reorder_level)})
    return rows


def stock_status_intent(c: Ctx) -> dict:
    p = c.parsed
    rows = _stock_rows(c, p.product_ids or None, p.category_id)
    if p.product_ids:
        total = sum(r["quantity"] for r in rows)
        lines = []
        for r in rows:
            cover = f" (~{r['days_of_cover']:.0f} days of cover)" if r["days_of_cover"] and r["quantity"] > 0 else ""
            flag = f" - **{r['status'].replace('_', ' ')}**" if r["status"] != "ok" else ""
            lines.append(f"- **{r['outlet']}**: {c.f.num(r['quantity'])} {r['unit']}{cover}{flag}")
        ans = f"Stock of **{', '.join(p.product_names)}** - total **{c.f.num(total)}**:\n" + "\n".join(lines)
        return result(ans, [table("Stock", [("outlet", "Outlet", "text"), ("product", "Product", "text"),
                                            ("quantity", "In stock", "number"), ("days_of_cover", "Days of cover", "number"),
                                            ("status", "Status", "status")], rows)],
                      [f"Forecast demand for {p.product_names[0]}", "What should I reorder?"])
    out = [r for r in rows if r["status"] == "out_of_stock"]
    low = [r for r in rows if r["status"] == "low"]
    if "out_only" in p.flags:
        focus, title = out, "Out of stock"
    elif "low_only" in p.flags:
        focus, title = low, "Below reorder level"
    else:
        focus, title = out + low, "Out of stock or low"
    focus.sort(key=lambda r: (r["days_of_cover"] if r["days_of_cover"] is not None else 0))
    value_q = select(func.sum(InventoryItem.quantity * Product.cost_price)).join(Product, Product.id == InventoryItem.product_id)
    if c.outlet_ids:
        value_q = value_q.where(InventoryItem.outlet_id.in_(c.outlet_ids))
    value = c.db.scalar(value_q) or 0
    ans = (f"Inventory at **{c.scope_label}**{' in ' + p.category_name if p.category_name else ''}: "
           f"**{len(rows)}** stock lines worth **{c.f.money(value)}** at cost. **{len(out)}** out of stock, "
           f"**{len(low)}** below reorder level.")
    if focus:
        urgent = []
        for r in focus[:8]:
            cover = f", ~{r['days_of_cover']:.1f} days of cover" if r["days_of_cover"] and r["quantity"] > 0 else ""
            urgent.append(f"- **{r['product']}** at {r['outlet']}: {c.f.num(r['quantity'])} left{cover}")
        ans += "\n\nMost urgent:\n" + "\n".join(urgent)
    else:
        ans += " Everything is above its reorder level."
    blocks = [{"type": "kpis", "items": [kpi("Stock value (cost)", value, "currency"), kpi("Out of stock", len(out)),
                                         kpi("Low stock", len(low))]}]
    if focus:
        blocks.append(table(title, [("outlet", "Outlet", "text"), ("product", "Product", "text"),
                                    ("quantity", "In stock", "number"), ("reorder_level", "Reorder level", "number"),
                                    ("days_of_cover", "Days of cover", "number"), ("status", "Status", "status")], focus[:50]))
    return result(ans, blocks, ["What should I reorder?", "Show pending purchase orders"])


def reorder(c: Ctx) -> dict:
    rows = F.reorder_suggestions(c.db, c.outlet_ids)
    if c.parsed.category_id:
        cat_products = set(c.db.scalars(select(Product.id).where(Product.category_id == c.parsed.category_id)).all())
        rows = [r for r in rows if r["product_id"] in cat_products]
    if c.parsed.product_ids:
        rows = [r for r in rows if r["product_id"] in c.parsed.product_ids]
    if not rows:
        return result(f"Good news - nothing needs reordering at {c.scope_label} right now. Stock covers expected demand "
                      "plus supplier lead times.", [], ["Show low stock items", "Forecast next week's sales"])
    total = sum(r["estimated_cost"] for r in rows)
    crit = [r for r in rows if r["urgency"] == "critical"]
    by_supplier: dict[str, float] = {}
    for r in rows:
        by_supplier[r["supplier"] or "No supplier"] = by_supplier.get(r["supplier"] or "No supplier", 0) + r["estimated_cost"]
    ans = (f"I recommend reordering **{len(rows)} items** at {c.scope_label} (estimated cost **{c.f.money(total)}**). "
           f"**{len(crit)}** are critical - already out of stock or running out before a new delivery can arrive.\n\n"
           + "\n".join(f"- **{r['product']}** ({r['outlet']}): order **{r['suggested_qty']} {r['unit']}** - "
                       f"{c.f.num(r['current_stock'])} left, selling ~{r['avg_daily_demand']:.1f}/day"
                       for r in rows[:8]))
    ans += "\n\nBy supplier: " + ", ".join(f"{k} {c.f.money(v)}" for k, v in sorted(by_supplier.items(), key=lambda kv: -kv[1]))
    ans += "\n\nYou can raise purchase orders for these in one click from **Inventory → Reorder**."
    return result(ans, [table("Reorder suggestions", [("outlet", "Outlet", "text"), ("product", "Product", "text"),
                                                      ("current_stock", "In stock", "number"),
                                                      ("avg_daily_demand", "Daily demand", "number"),
                                                      ("suggested_qty", "Order qty", "number"), ("estimated_cost", "Est. cost", "currency"),
                                                      ("supplier", "Supplier", "text"), ("urgency", "Urgency", "status")], rows[:60])],
                  ["Show pending purchase orders", "Which items are out of stock?"])


def customers(c: Ctx) -> dict:
    p = c.parsed
    seg = A.customer_segments(c.db, c.outlet_ids)
    if "at_risk" in p.flags:
        df = A.customer_rfm(c.db, c.outlet_ids)
        if df.empty:
            return result("No identified customers found yet.")
        risk = df[df["segment"].isin(["At Risk", "Needs Attention"])].sort_values("monetary", ascending=False).head(15)
        from app.models import Customer
        names = dict(c.db.execute(select(Customer.id, Customer.name)).all())
        phones = dict(c.db.execute(select(Customer.id, Customer.phone)).all())
        rows = [{"name": names.get(int(r.customer_id)), "phone": phones.get(int(r.customer_id)),
                 "last_purchase_days": int(r.recency), "orders": int(r.frequency), "spend": round(float(r.monetary), 2),
                 "segment": r.segment} for r in risk.itertuples()]
        n_risk = int((df["segment"] == "At Risk").sum())
        if not rows:
            return result("No customers are at risk right now - every regular has visited recently. (At-risk customers "
                          "are those who used to buy often but have not come back for a while.)", [],
                          ["Show customer segments", "Who are my top customers?"],
                          {"notes": [f"{len(df)} identified customer(s) in the last 12 months."]})
        ans = (f"**{n_risk}** valuable customers are **at risk** - they used to buy often but haven't visited recently. "
               f"Here are the highest-spending ones to win back (a personal call or a targeted offer works best):")
        return result(ans, [table("Customers to win back", [("name", "Customer", "text"), ("phone", "Phone", "text"),
                                                            ("last_purchase_days", "Days since last visit", "number"),
                                                            ("orders", "Orders (12m)", "number"), ("spend", "Spend (12m)", "currency"),
                                                            ("segment", "Segment", "text")], rows)],
                      ["Show customer segments", "Who are my top customers?"])
    rng, label = c.period(90)
    top = A.top_customers(c.db, rng, c.outlet_ids, p.top_n or 10)
    rep = A.repeat_rate(c.db, rng, c.outlet_ids)
    ans = (f"For **{label}**, **{rep['customers']}** identified customers shopped at {c.scope_label}; "
           f"**{rep['repeat_rate_pct']:.0f}%** came back more than once, and loyalty-linked bills were "
           f"{rep['identified_order_share_pct']:.0f}% of all bills.")
    if top:
        ans += f"\n\nTop customer: **{top[0]['name']}** ({c.f.money(top[0]['spend'])} over {top[0]['orders']} visits)."
    if seg["segments"]:
        ans += "\n\n**Customer segments (RFM, last 12 months):**\n" + "\n".join(
            f"- **{s['segment']}** - {s['customers']} customers, {s['revenue_share_pct']:.0f}% of loyalty revenue. {s['description']}."
            for s in seg["segments"])
    blocks = []
    if seg["segments"]:
        blocks.append(chart("pie", "Customers by segment", seg["segments"], "segment", [("customers", "Customers")], "number"))
    if top:
        blocks.append(table("Top customers", [("name", "Customer", "text"), ("type", "Type", "text"), ("orders", "Visits", "number"),
                                              ("spend", "Spend", "currency"), ("last_purchase", "Last purchase", "date")], top))
    return result(ans, blocks, ["Which customers are at risk?", "What is the average bill value?"])


def peak_hours(c: Ctx) -> dict:
    rng, label = c.period(90)
    hm = A.hourly_heatmap(c.db, rng, c.outlet_ids)
    if not hm["cells"]:
        return result("No sales in that period.")
    by_hour: dict[int, float] = {}
    by_day: dict[int, float] = {}
    for cell in hm["cells"]:
        by_hour[cell["hour"]] = by_hour.get(cell["hour"], 0) + cell["revenue"]
        by_day[cell["weekday"]] = by_day.get(cell["weekday"], 0) + cell["revenue"]
    top_hours = sorted(by_hour.items(), key=lambda kv: -kv[1])[:3]
    quiet = sorted(by_hour.items(), key=lambda kv: kv[1])[:2]
    best_day = max(by_day.items(), key=lambda kv: kv[1])
    worst_day = min(by_day.items(), key=lambda kv: kv[1])
    b = hm["busiest"]
    ans = (f"Based on **{label}** at {c.scope_label}:\n"
           f"- Busiest hours: " + ", ".join(f"**{h}:00-{h + 1}:00**" for h, _ in top_hours) + "\n"
           "- Quietest hours: " + ", ".join(f"{h}:00-{h + 1}:00" for h, _ in quiet) + "\n"
           f"- Busiest day: **{WEEKDAYS[best_day[0]]}**; quietest: **{WEEKDAYS[worst_day[0]]}** "
           f"({(best_day[1] / worst_day[1] - 1) * 100:.0f}% difference)\n"
           f"- Single busiest slot: **{WEEKDAYS[b['weekday']]} {b['hour']}:00** (~{c.f.money(b['revenue'])} per week)\n\n"
           f"Schedule more staff and keep shelves full before the peaks; use quiet hours for restocking.")
    hours = [{"hour": f"{h}:00", "revenue": round(v, 2)} for h, v in sorted(by_hour.items())]
    return result(ans, [chart("bar", "Average weekly revenue by hour", hours, "hour", [("revenue", "Revenue")]),
                        {"type": "heatmap", "title": "Revenue heatmap (weekday x hour)", "cells": hm["cells"]}],
                  ["Which day of the week sells the most?", "Forecast next week"])


def payment_mix(c: Ctx) -> dict:
    rng, label = c.period(30)
    rows = A.payment_mix(c.db, rng, c.outlet_ids)
    ch = A.channel_mix(c.db, rng, c.outlet_ids)
    ans = f"Payment mix at **{c.scope_label}** for **{label}**:\n" + "\n".join(
        f"- **{r['method'].upper()}**: {r['share_pct']:.0f}% of revenue ({c.f.num(r['orders'])} bills)" for r in rows)
    for x in ch:
        if x["channel"] == "delivery":
            ans += (f"\n\nDelivery orders were **{x['share_pct']:.0f}%** of revenue with an average bill of "
                    f"{c.f.money(x['avg_basket'])}.")
    return result(ans, [chart("pie", "Revenue by payment method", rows, "method", [("revenue", "Revenue")])],
                  ["What is the average bill value?", "Show sales by outlet"])


def profitability(c: Ctx) -> dict:
    rng, label = c.period(30)
    cats = A.category_breakdown(c.db, rng, c.outlet_ids)
    prods = A.top_products(c.db, rng, c.outlet_ids, 200, sort="revenue")
    k = A.kpis(c.db, rng, c.outlet_ids)
    if not prods:
        return result("No sales in that period.")
    best_profit = sorted(prods, key=lambda r: -r["profit"])[:5]
    low_margin = sorted([r for r in prods if r["revenue"] > 0], key=lambda r: r["margin_pct"])[:5]
    ans = (f"Gross profit at **{c.scope_label}** for **{label}**: **{c.f.money(k['gross_profit'])}** on "
           f"{c.f.money(k['revenue'])} revenue (**{k['margin_pct']:.1f}%** margin, after tax and cost of goods).\n\n"
           "**Biggest profit contributors:**\n" + "\n".join(
               f"- {r['name']}: {c.f.money(r['profit'])} ({r['margin_pct']:.0f}% margin)" for r in best_profit) +
           "\n\n**Lowest margins (review pricing or supplier cost):**\n" + "\n".join(
               f"- {r['name']}: {r['margin_pct']:.1f}% margin" for r in low_margin))
    return result(ans, [chart("bar", "Gross profit by category", cats, "category", [("profit", "Gross profit")]),
                        table("Category margins", [("category", "Category", "text"), ("revenue", "Revenue", "currency"),
                                                   ("profit", "Gross profit", "currency"),
                                                   ("margin_pct", "Margin", "percent_plain")], cats)],
                  ["Top products by profit", "Show category performance"])


def purchase_orders(c: Ctx) -> dict:
    q = select(PurchaseOrder, Supplier, Outlet).join(Supplier, Supplier.id == PurchaseOrder.supplier_id).join(
        Outlet, Outlet.id == PurchaseOrder.outlet_id).where(PurchaseOrder.status.in_(OPEN_PO_STATUSES))
    if c.outlet_ids:
        q = q.where(PurchaseOrder.outlet_id.in_(c.outlet_ids))
    rows = []
    for po, s, o in c.db.execute(q.order_by(PurchaseOrder.expected_date)).all():
        overdue = po.expected_date is not None and po.expected_date < clock.today()
        rows.append({"po_number": po.po_number, "supplier": s.name, "outlet": o.name, "order_date": po.order_date.isoformat(),
                     "expected_date": po.expected_date.isoformat() if po.expected_date else None,
                     "total_cost": po.total_cost, "status": "overdue" if overdue else po.status})
    if "overdue" in c.parsed.flags:
        rows = [r for r in rows if r["status"] == "overdue"]
    if not rows:
        return result("There are no open purchase orders" + (" that are overdue." if "overdue" in c.parsed.flags else "."),
                      [], ["What should I reorder?"])
    overdue = [r for r in rows if r["status"] == "overdue"]
    ans = (f"**{len(rows)}** open purchase orders worth **{c.f.money(sum(r['total_cost'] for r in rows))}**"
           f"{f', **{len(overdue)} overdue**' if overdue else ''}. Next expected: **{rows[0]['po_number']}** from "
           f"{rows[0]['supplier']} on {rows[0]['expected_date']}.")
    return result(ans, [table("Open purchase orders", [("po_number", "PO", "text"), ("supplier", "Supplier", "text"),
                                                       ("outlet", "Outlet", "text"), ("expected_date", "Expected", "date"),
                                                       ("total_cost", "Value", "currency"), ("status", "Status", "status")], rows)],
                  ["What should I reorder?", "Which items are out of stock?"])


def basket_analysis(c: Ctx) -> dict:
    rng, label = c.period(90)
    pairs = A.product_affinity(c.db, rng, c.outlet_ids, limit=12)
    if c.parsed.product_ids:
        ids = set(c.parsed.product_ids)
        pairs = [x for x in A.product_affinity(c.db, rng, c.outlet_ids, limit=200, min_pair_count=10)
                 if x["product_a_id"] in ids or x["product_b_id"] in ids][:10]
    if not pairs:
        return result(f"I couldn't find products that are bought together more than by chance for {label}.")
    ans = (f"**Frequently bought together** at {c.scope_label} ({label}, market-basket analysis). "
           "Lift shows how many times more likely the pair is bought together than by chance:\n" + "\n".join(
               f"- **{x['product_a']}** + **{x['product_b']}** - lift {x['lift']:.1f}x, "
               f"{x['bills_together']} bills, {x['confidence_pct']:.0f}% of buyers of one also buy the other"
               for x in pairs[:8]) +
           "\n\nUse these for shelf placement, combo offers and 'customers also bought' suggestions at billing.")
    return result(ans, [table("Product pairs", [("product_a", "Product", "text"), ("product_b", "Bought with", "text"),
                                                ("bills_together", "Bills", "number"), ("lift", "Lift", "number"),
                                                ("confidence_pct", "Confidence", "percent_plain")], pairs)],
                  ["How can I increase sales?", "Top products this month"])


def advice(c: Ctx) -> dict:
    """Data-driven recommendations (works without any LLM)."""
    rng = A.DateRange(c.anchor - timedelta(days=29), c.anchor)
    recs: list[tuple[str, str]] = []
    lost = A.lost_sales_estimate(c.db, c.outlet_ids)
    if lost["items"]:
        recs.append(("Fix stock-outs first",
                     f"{len(lost['items'])} items that normally sell are out of stock ({', '.join(lost['items'][:3])}"
                     f"{'...' if len(lost['items']) > 3 else ''}), putting about **{c.f.money(lost['revenue_at_risk_per_day'])} "
                     "of sales per day** at risk. Raise purchase orders from Inventory → Reorder."))
    pairs = A.product_affinity(c.db, A.DateRange(c.anchor - timedelta(days=89), c.anchor), c.outlet_ids, limit=3)
    if pairs:
        recs.append(("Cross-sell items customers already pair",
                     "; ".join(f"{x['product_a']} + {x['product_b']} ({x['lift']:.1f}x lift)" for x in pairs) +
                     ". Shelve them together or create combo offers to lift the average bill "
                     f"(currently {c.f.money(A.kpis(c.db, rng, c.outlet_ids)['avg_basket'])})."))
    week = A.DateRange(c.anchor - timedelta(days=13), c.anchor)
    outlets = [o for o in A.outlet_performance(c.db, week, c.outlet_ids) if o["change_pct"] is not None]
    if len(outlets) > 1:
        weak = min(outlets, key=lambda o: o["change_pct"])
        if weak["change_pct"] < 0:
            recs.append((f"Investigate {weak['name']}",
                         f"Revenue is {trend_word(weak['change_pct'])} over the last 14 days. Compare its stock-outs, "
                         "staffing and local competition with the best outlet, and run a local promotion."))
    df = A.customer_rfm(c.db, c.outlet_ids)
    if not df.empty:
        at_risk = df[df["segment"] == "At Risk"]
        if len(at_risk):
            recs.append(("Win back lapsed regulars",
                         f"{len(at_risk)} customers who used to buy often haven't visited recently (worth "
                         f"{c.f.money(float(at_risk['monetary'].sum()))} in the last year). Send them a personal offer - "
                         "ask me \"which customers are at risk?\" for the list."))
    slow = A.top_products(c.db, rng, c.outlet_ids, 3, ascending=True)
    if slow:
        recs.append(("Clear slow movers", "Bundle or discount " + ", ".join(s["name"] for s in slow) +
                     " and order them in smaller quantities to free up cash."))
    hm = A.hourly_heatmap(c.db, A.DateRange(c.anchor - timedelta(days=55), c.anchor), c.outlet_ids)
    if hm["busiest"]:
        b = hm["busiest"]
        recs.append(("Staff for the peaks", f"The busiest slot is {WEEKDAYS[b['weekday']]} around {b['hour']}:00. "
                     "Add a cashier and restock fast movers before evening peaks to cut queues and missed sales."))
    for ev in upcoming_events(c.anchor, 30)[:1]:
        recs.append((f"Prepare for {ev['name']}",
                     f"{ev['name']} is {ev['days_away']} days away. Stock up on sweets, dry fruits and snacks; "
                     "check the category forecasts for expected demand."))
    cats = A.category_breakdown(c.db, rng, c.outlet_ids)
    if cats:
        hi = max(cats, key=lambda x: x["margin_pct"])
        recs.append(("Promote high-margin categories",
                     f"{hi['category']} earns a {hi['margin_pct']:.0f}% margin but is only {hi['share_pct']:.0f}% of sales - "
                     "give it better shelf space and sampling."))
    ans = "Here are data-driven actions to grow sales and profit, based on your latest numbers:\n\n" + "\n".join(
        f"{i}. **{t}** - {d}" for i, (t, d) in enumerate(recs, 1))
    blocks = []
    if pairs:
        blocks.append(table("Products bought together", [("product_a", "Product", "text"), ("product_b", "Bought with", "text"),
                                                         ("lift", "Lift", "number"), ("bills_together", "Bills", "number")], pairs))
    return result(ans, blocks, ["Which customers are at risk?", "What should I reorder?", "Which products are bought together?"])


HELP_TEXT = """I'm your ERIS business assistant. Ask me in plain English about your sales, stock and customers - \
I look up the live data and answer with numbers, charts and tables, and show where every number came from. For example:

- **Sales**: "How much did we sell yesterday?", "Revenue at Indiranagar last month", "Compare September with August"
- **Why it changed**: "Why was Outlet 3 revenue lower this week?", "What caused the drop at Andheri last month?"
- **Products**: "Top 5 products this week", "Show the five fastest-growing products", "How is paneer selling?"
- **Outlets**: "Which outlet had the highest revenue last month?", "Compare weekend sales between outlets"
- **Forecasts**: "Forecast sales for next week", "What forecast model performed best for beverages?"
- **Inventory**: "Which items may go out of stock in the next 14 days?", "What should I reorder?", "Stock of eggs"
- **Unusual activity**: "Summarize the major anomalies this month"
- **Customers**: "Who are my top customers?", "Which customers are at risk?"
- **Patterns & advice**: "When are our busiest hours?", "Which products are bought together?", "How can I increase sales?"
- **How ERIS works**: "What is WAPE?", "How do I import sales?", "Is the GSTIN real?"

You can name an outlet (Andheri, Indiranagar, "Outlet 2"...), a category (dairy, bakery...) or a product, \
and a time period (today, last week, March, last 90 days)."""


def help_intent(c: Ctx) -> dict:
    return result(HELP_TEXT, [], ["How is business this week?", "What should I reorder?", "Forecast sales for next month"])


DISPATCH = {
    "business_overview": business_overview,
    "sales_summary": sales_summary,
    "compare_periods": compare_periods,
    "sales_trend": sales_trend,
    "top_products": top_products,
    "slow_products": lambda c: top_products(c, slow=True),
    "outlet_ranking": outlet_ranking,
    "category_mix": category_mix,
    "forecast": forecast,
    "stock_status": stock_status_intent,
    "reorder": reorder,
    "customers": customers,
    "peak_hours": peak_hours,
    "payment_mix": payment_mix,
    "profitability": profitability,
    "purchase_orders": purchase_orders,
    "basket_analysis": basket_analysis,
    "advice": advice,
    "help": help_intent,
}
