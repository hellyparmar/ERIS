"""Reusable analytics queries shared by the dashboard, analytics pages, forecasting and the AI assistant.

All functions take an optional list of outlet ids (None = all outlets) and an inclusive date range.
Revenue is tax-inclusive amount paid; gross profit = revenue excluding tax - cost of goods.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import Select, case, distinct, extract, func, select
from sqlalchemy.orm import Session

from app import clock
from app.models import Category, Customer, Outlet, Product, Sale, SaleItem

COMPLETED = Sale.status == "completed"
_CACHE: dict[tuple, tuple[float, object]] = {}
_CACHE_TTL = 600


def _data_version(db: Session) -> tuple:
    return tuple(db.execute(select(func.count(Sale.id), func.max(Sale.id),
                                   func.sum(case((Sale.status == "void", 1), else_=0)))).one())


def cached(fn):
    """Memoise expensive analyses per (arguments, data version) for a few minutes."""
    import functools
    import time as _time

    @functools.wraps(fn)
    def wrapper(db: Session, *args, **kwargs):
        key = (fn.__name__, repr(args), repr(sorted(kwargs.items())), _data_version(db))
        hit = _CACHE.get(key)
        if hit and _time.time() - hit[0] < _CACHE_TTL:
            return copy.deepcopy(hit[1])
        value = fn(db, *args, **kwargs)
        if len(_CACHE) > 256:
            _CACHE.clear()
        _CACHE[key] = (_time.time(), value)
        return copy.deepcopy(value)

    return wrapper


@dataclass
class DateRange:
    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def previous(self) -> "DateRange":
        return DateRange(self.start - timedelta(days=self.days), self.start - timedelta(days=1))

    def as_dict(self) -> dict:
        return {"start": self.start.isoformat(), "end": self.end.isoformat(), "days": self.days}


def latest_sale_date(db: Session) -> date | None:
    return db.scalar(select(func.max(Sale.sale_date)).where(COMPLETED))


def anchor_date(db: Session) -> date:
    """The 'today' analytics are relative to: the last day with sales data, never in the future."""
    latest = latest_sale_date(db)
    today = clock.today()
    return min(latest, today) if latest else today


PERIODS = {"7d": 7, "14d": 14, "30d": 30, "90d": 90, "180d": 180, "365d": 365}


def resolve_period(db: Session, period: str | None = "30d", start: date | None = None,
                   end: date | None = None) -> DateRange:
    if start and end:
        if start > end:
            start, end = end, start
        return DateRange(start, end)
    anchor = end or anchor_date(db)
    period = period or "30d"
    if period == "mtd":
        return DateRange(anchor.replace(day=1), anchor)
    if period == "ytd":
        return DateRange(anchor.replace(month=1, day=1), anchor)
    days = PERIODS.get(period, 30)
    return DateRange(anchor - timedelta(days=days - 1), anchor)


def _sale_filters(rng: DateRange, outlet_ids: list[int] | None):
    conds = [COMPLETED, Sale.sale_date >= rng.start, Sale.sale_date <= rng.end]
    if outlet_ids:
        conds.append(Sale.outlet_id.in_(outlet_ids))
    return conds


def _item_query(rng: DateRange, outlet_ids: list[int] | None, *cols) -> Select:
    q = select(*cols).select_from(SaleItem).join(Sale, Sale.id == SaleItem.sale_id).where(
        COMPLETED, SaleItem.sale_date >= rng.start, SaleItem.sale_date <= rng.end)
    if outlet_ids:
        q = q.where(SaleItem.outlet_id.in_(outlet_ids))
    return q


def pct_change(current: float, previous: float) -> float | None:
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


# --------------------------------------------------------------------------------------------- KPIs
def kpis(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> dict:
    row = db.execute(
        select(
            func.coalesce(func.sum(Sale.total), 0),
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.items_count), 0),
            func.coalesce(func.sum(Sale.discount), 0),
            func.coalesce(func.sum(Sale.tax_amount), 0),
            func.count(distinct(Sale.customer_id)),
        ).where(*_sale_filters(rng, outlet_ids))
    ).one()
    revenue, orders, units, discount, tax, customers = row
    cost = db.scalar(_item_query(rng, outlet_ids, func.coalesce(func.sum(SaleItem.cost_amount), 0))) or 0
    net = revenue - tax
    gp = net - cost
    return {
        "revenue": round(revenue, 2),
        "orders": orders,
        "units": round(units, 1),
        "avg_basket": round(revenue / orders, 2) if orders else 0,
        "items_per_basket": round(units / orders, 2) if orders else 0,
        "discount": round(discount, 2),
        "tax": round(tax, 2),
        "gross_profit": round(gp, 2),
        "margin_pct": round(gp / net * 100, 1) if net else 0,
        "identified_customers": customers,
        "avg_daily_revenue": round(revenue / rng.days, 2),
    }


def comparable_period(rng: DateRange) -> tuple[DateRange, str]:
    """Like-for-like baseline: the same weekdays a week earlier for periods up to a week, the same days of the
    previous month for month-to-date / calendar months, otherwise the preceding period of equal length."""
    if rng.days <= 7:
        label = "the same day last week" if rng.days == 1 else "the same days a week earlier"
        return DateRange(rng.start - timedelta(days=7), rng.end - timedelta(days=7)), label
    if rng.start.day == 1 and rng.days <= 31:
        prev_end = rng.start - timedelta(days=1)
        start = prev_end.replace(day=1)
        return DateRange(start, min(start + timedelta(days=rng.days - 1), prev_end)), f"the same days of {start:%B %Y}"
    return rng.previous(), f"the previous {rng.days} days"


def kpis_with_comparison(db: Session, rng: DateRange, outlet_ids: list[int] | None = None,
                         previous: DateRange | None = None) -> dict:
    cur = kpis(db, rng, outlet_ids)
    prev = kpis(db, previous or rng.previous(), outlet_ids)
    return {
        "current": cur,
        "previous": prev,
        "change_pct": {k: pct_change(cur[k], prev[k]) for k in
                       ("revenue", "orders", "avg_basket", "gross_profit", "units", "identified_customers")},
    }


# --------------------------------------------------------------------------------------------- series
def revenue_series(db: Session, rng: DateRange, outlet_ids: list[int] | None = None, granularity: str = "day",
                   category_id: int | None = None, product_id: int | None = None) -> list[dict]:
    """Daily (or weekly/monthly) revenue, orders, units and profit. Missing days are filled with zero."""
    if category_id or product_id:
        q = _item_query(rng, outlet_ids, SaleItem.sale_date.label("d"),
                        func.sum(SaleItem.line_total).label("revenue"),
                        func.count(distinct(SaleItem.sale_id)).label("orders"),
                        func.sum(SaleItem.quantity).label("units"),
                        func.sum(SaleItem.line_total - SaleItem.tax_amount - SaleItem.cost_amount).label("profit"))
        if product_id:
            q = q.where(SaleItem.product_id == product_id)
        if category_id:
            q = q.join(Product, Product.id == SaleItem.product_id).where(Product.category_id == category_id)
        q = q.group_by(SaleItem.sale_date)
        df = pd.DataFrame(db.execute(q).all(), columns=["d", "revenue", "orders", "units", "profit"])
    else:
        q = select(Sale.sale_date, func.sum(Sale.total), func.count(Sale.id), func.sum(Sale.items_count)).where(
            *_sale_filters(rng, outlet_ids)).group_by(Sale.sale_date)
        df = pd.DataFrame(db.execute(q).all(), columns=["d", "revenue", "orders", "units"])
        cost = db.execute(_item_query(rng, outlet_ids, SaleItem.sale_date,
                                      func.sum(SaleItem.cost_amount + SaleItem.tax_amount)).group_by(SaleItem.sale_date)).all()
        cdf = pd.DataFrame(cost, columns=["d", "deduct"])
        df = df.merge(cdf, on="d", how="left") if len(df) else df.assign(deduct=[])
        df["profit"] = df["revenue"] - df["deduct"].fillna(0)
        df = df.drop(columns="deduct")

    full = pd.DataFrame({"d": pd.date_range(rng.start, rng.end, freq="D")})
    if len(df):
        df["d"] = pd.to_datetime(df["d"])
        df = full.merge(df, on="d", how="left").fillna(0)
    else:
        df = full.assign(revenue=0.0, orders=0, units=0.0, profit=0.0)

    if granularity in ("week", "month"):
        rule = "W-MON" if granularity == "week" else "MS"
        label = "left" if granularity == "week" else None
        counts = df.set_index("d").resample(rule, label=label or "left", closed="left")["revenue"].count()
        df = df.set_index("d").resample(rule, label=label or "left", closed="left").sum().reset_index()
        # Drop partial weeks at either edge (they look like false dips); keep a partial current month.
        full = 7 if granularity == "week" else None
        if full and len(df) > 2:
            keep = counts.values >= full
            keep[1:-1] = True
            df = df[keep]
    return [
        {"date": r.d.date().isoformat(), "revenue": round(float(r.revenue), 2), "orders": int(r.orders),
         "units": round(float(r.units), 1), "profit": round(float(r.profit), 2)}
        for r in df.itertuples()
    ]


# --------------------------------------------------------------------------------------------- breakdowns
def top_products(db: Session, rng: DateRange, outlet_ids: list[int] | None = None, limit: int = 10,
                 sort: str = "revenue", ascending: bool = False, category_id: int | None = None,
                 product_ids: list[int] | None = None) -> list[dict]:
    revenue = func.sum(SaleItem.line_total).label("revenue")
    units = func.sum(SaleItem.quantity).label("units")
    profit = func.sum(SaleItem.line_total - SaleItem.tax_amount - SaleItem.cost_amount).label("profit")
    q = _item_query(rng, outlet_ids, Product.id, Product.sku, Product.name, Category.name.label("category"),
                    revenue, units, profit).join(Product, Product.id == SaleItem.product_id).join(
        Category, Category.id == Product.category_id).group_by(Product.id, Product.sku, Product.name, Category.name)
    if category_id:
        q = q.where(Product.category_id == category_id)
    if product_ids:
        q = q.where(Product.id.in_(product_ids))
    key = {"revenue": revenue, "units": units, "profit": profit}.get(sort, revenue)
    q = q.order_by(key.asc() if ascending else key.desc()).limit(limit)
    rows = db.execute(q).all()
    total = db.scalar(_item_query(rng, outlet_ids, func.sum(SaleItem.line_total))) or 0
    return [
        {"product_id": r.id, "sku": r.sku, "name": r.name, "category": r.category, "revenue": round(r.revenue, 2),
         "units": round(r.units, 1), "profit": round(r.profit, 2),
         "margin_pct": round(r.profit / (r.revenue or 1) * 100, 1) if r.revenue else 0,
         "share_pct": round(r.revenue / total * 100, 1) if total else 0}
        for r in rows
    ]


def category_breakdown(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> list[dict]:
    prev = rng.previous()

    def run(r: DateRange):
        q = _item_query(r, outlet_ids, Category.id, Category.name, func.sum(SaleItem.line_total),
                        func.sum(SaleItem.quantity),
                        func.sum(SaleItem.line_total - SaleItem.tax_amount - SaleItem.cost_amount)).join(
            Product, Product.id == SaleItem.product_id).join(Category, Category.id == Product.category_id).group_by(
            Category.id, Category.name)
        return {row[0]: row for row in db.execute(q).all()}

    cur, before = run(rng), run(prev)
    total = sum(r[2] for r in cur.values()) or 1
    out = [
        {"category_id": cid, "category": r[1], "revenue": round(r[2], 2), "units": round(r[3], 1),
         "profit": round(r[4], 2), "share_pct": round(r[2] / total * 100, 1),
         "margin_pct": round(r[4] / r[2] * 100, 1) if r[2] else 0,
         "change_pct": pct_change(r[2], before[cid][2]) if cid in before else None}
        for cid, r in cur.items()
    ]
    return sorted(out, key=lambda x: -x["revenue"])


def outlet_performance(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> list[dict]:
    prev = rng.previous()

    def run(r: DateRange):
        q = select(Sale.outlet_id, func.sum(Sale.total), func.count(Sale.id), func.sum(Sale.items_count)).where(
            *_sale_filters(r, outlet_ids)).group_by(Sale.outlet_id)
        return {row[0]: row for row in db.execute(q).all()}

    cur, before = run(rng), run(prev)
    costs = dict(db.execute(_item_query(rng, outlet_ids, SaleItem.outlet_id,
                                        func.sum(SaleItem.cost_amount + SaleItem.tax_amount)).group_by(
        SaleItem.outlet_id)).all())
    oq = select(Outlet)
    if outlet_ids:
        oq = oq.where(Outlet.id.in_(outlet_ids))
    outlets = db.scalars(oq.order_by(Outlet.id)).all()
    total = sum(r[1] for r in cur.values()) or 1
    out = []
    for o in outlets:
        r = cur.get(o.id)
        revenue = r[1] if r else 0.0
        orders = r[2] if r else 0
        profit = revenue - costs.get(o.id, 0) if r else 0.0
        prev_rev = before[o.id][1] if o.id in before else 0
        out.append({
            "outlet_id": o.id, "code": o.code, "name": o.name, "city": o.city, "is_active": o.is_active,
            "revenue": round(revenue, 2), "orders": orders,
            "avg_basket": round(revenue / orders, 2) if orders else 0,
            "units": round(r[3], 1) if r else 0, "profit": round(profit, 2),
            "margin_pct": round(profit / (revenue - 0) * 100, 1) if revenue else 0,
            "share_pct": round(revenue / total * 100, 1),
            "previous_revenue": round(prev_rev, 2), "change_pct": pct_change(revenue, prev_rev),
            "avg_daily_revenue": round(revenue / rng.days, 2),
        })
    return sorted(out, key=lambda x: -x["revenue"])


def payment_mix(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> list[dict]:
    rows = db.execute(select(Sale.payment_method, func.count(Sale.id), func.sum(Sale.total)).where(
        *_sale_filters(rng, outlet_ids)).group_by(Sale.payment_method)).all()
    total = sum(r[2] for r in rows) or 1
    return sorted([{"method": m, "orders": c, "revenue": round(v, 2), "share_pct": round(v / total * 100, 1)}
                   for m, c, v in rows], key=lambda x: -x["revenue"])


def channel_mix(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> list[dict]:
    rows = db.execute(select(Sale.channel, func.count(Sale.id), func.sum(Sale.total)).where(
        *_sale_filters(rng, outlet_ids)).group_by(Sale.channel)).all()
    total = sum(r[2] for r in rows) or 1
    return [{"channel": ch, "orders": c, "revenue": round(v, 2), "avg_basket": round(v / c, 2) if c else 0,
             "share_pct": round(v / total * 100, 1)} for ch, c, v in rows]


def hourly_heatmap(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> dict:
    """Average revenue by weekday x hour (weekday 0 = Monday)."""
    dow = extract("dow", Sale.sold_at)
    hour = extract("hour", Sale.sold_at)
    rows = db.execute(select(dow, hour, func.sum(Sale.total), func.count(Sale.id)).where(
        *_sale_filters(rng, outlet_ids)).group_by(dow, hour)).all()
    weeks = max(rng.days / 7, 1)
    cells = [{"weekday": (int(d) + 6) % 7, "hour": int(h), "revenue": round(v / weeks, 2),
              "orders": round(c / weeks, 1)} for d, h, v, c in rows]
    busiest = max(cells, key=lambda c: c["revenue"]) if cells else None
    return {"cells": cells, "busiest": busiest}


def basket_distribution(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> list[dict]:
    bands = [(0, 100), (100, 250), (250, 500), (500, 1000), (1000, 2000), (2000, None)]
    out = []
    for lo, hi in bands:
        cond = [Sale.total >= lo] + ([Sale.total < hi] if hi else [])
        c, v = db.execute(select(func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0)).where(
            *_sale_filters(rng, outlet_ids), *cond)).one()
        out.append({"band": f"{lo}-{hi}" if hi else f"{lo}+", "orders": c, "revenue": round(v, 2)})
    return out


# --------------------------------------------------------------------------------------------- products
@cached
def abc_analysis(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> dict:
    """Classify products into A (top ~80% of revenue), B (next 15%) and C (last 5%)."""
    rows = top_products(db, rng, outlet_ids, limit=10_000)
    total = sum(r["revenue"] for r in rows) or 1
    cum = 0.0
    for r in rows:
        cum += r["revenue"]
        share = cum / total
        r["cumulative_pct"] = round(share * 100, 1)
        r["class"] = "A" if share <= 0.8 or r is rows[0] else ("B" if share <= 0.95 else "C")
    summary = {}
    for cls in "ABC":
        items = [r for r in rows if r["class"] == cls]
        summary[cls] = {"products": len(items), "revenue": round(sum(r["revenue"] for r in items), 2),
                        "share_pct": round(sum(r["revenue"] for r in items) / total * 100, 1)}
    sold_ids = {r["product_id"] for r in rows}
    unsold = db.execute(select(Product.id, Product.sku, Product.name).where(
        Product.is_active.is_(True), Product.id.not_in(sold_ids) if sold_ids else True)).all()
    return {"products": rows, "summary": summary,
            "not_sold": [{"product_id": u.id, "sku": u.sku, "name": u.name} for u in unsold]}


# --------------------------------------------------------------------------------------------- customers
SEGMENT_INFO = {
    "Champions": "Bought recently, buy often and spend the most",
    "Loyal": "Buy regularly with good spend",
    "Potential Loyalists": "Recent customers with growing frequency",
    "New": "First purchase very recently",
    "Needs Attention": "Above-average customers who have not bought lately",
    "At Risk": "Used to buy often, but not for a long time",
    "Lost": "Lowest recency, frequency and spend",
}


@cached
def customer_rfm(db: Session, outlet_ids: list[int] | None = None, as_of: date | None = None,
                 lookback_days: int = 365) -> pd.DataFrame:
    as_of = as_of or anchor_date(db)
    rng = DateRange(as_of - timedelta(days=lookback_days - 1), as_of)
    q = select(Sale.customer_id, func.max(Sale.sale_date), func.count(Sale.id), func.sum(Sale.total),
               func.min(Sale.sale_date)).where(*_sale_filters(rng, outlet_ids), Sale.customer_id.is_not(None)).group_by(
        Sale.customer_id)
    df = pd.DataFrame(db.execute(q).all(), columns=["customer_id", "last", "frequency", "monetary", "first"])
    if df.empty:
        return df
    df["recency"] = (pd.Timestamp(as_of) - pd.to_datetime(df["last"])).dt.days
    df["tenure"] = (pd.Timestamp(as_of) - pd.to_datetime(df["first"])).dt.days

    def score(s: pd.Series, reverse: bool = False) -> pd.Series:
        ranks = s.rank(method="first", ascending=not reverse)
        return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)

    df["R"] = score(df["recency"], reverse=True)
    df["F"] = score(df["frequency"])
    df["M"] = score(df["monetary"])

    def segment(r) -> str:
        if r.R >= 4 and r.F >= 4 and r.M >= 4:
            return "Champions"
        if r.R >= 4 and r.tenure <= 45 and r.frequency <= 2:
            return "New"
        if r.F >= 4 and r.R >= 3:
            return "Loyal"
        if r.R >= 4:
            return "Potential Loyalists"
        if r.R <= 2 and r.F >= 4:
            return "At Risk"
        if r.R <= 2 and r.F <= 2:
            return "Lost"
        return "Needs Attention"

    df["segment"] = df.apply(segment, axis=1)
    return df


def customer_segments(db: Session, outlet_ids: list[int] | None = None) -> dict:
    df = customer_rfm(db, outlet_ids)
    if df.empty:
        return {"segments": [], "total_customers": 0}
    g = df.groupby("segment").agg(customers=("customer_id", "count"), revenue=("monetary", "sum"),
                                  avg_recency=("recency", "mean"), avg_frequency=("frequency", "mean"),
                                  avg_spend=("monetary", "mean")).reset_index()
    total_rev = g["revenue"].sum() or 1
    segments = [
        {"segment": r.segment, "description": SEGMENT_INFO.get(r.segment, ""), "customers": int(r.customers),
         "revenue": round(float(r.revenue), 2), "revenue_share_pct": round(float(r.revenue) / float(total_rev) * 100, 1),
         "avg_recency_days": round(float(r.avg_recency), 1), "avg_orders": round(float(r.avg_frequency), 1),
         "avg_spend": round(float(r.avg_spend), 2)}
        for r in g.itertuples()
    ]
    order = list(SEGMENT_INFO)
    segments.sort(key=lambda s: order.index(s["segment"]))
    return {"segments": segments, "total_customers": int(len(df))}


def top_customers(db: Session, rng: DateRange, outlet_ids: list[int] | None = None, limit: int = 10) -> list[dict]:
    spend = func.sum(Sale.total).label("spend")
    q = select(Customer.id, Customer.name, Customer.phone, Customer.customer_type, spend,
               func.count(Sale.id).label("orders"), func.max(Sale.sale_date).label("last")).join(
        Sale, Sale.customer_id == Customer.id).where(*_sale_filters(rng, outlet_ids)).group_by(
        Customer.id, Customer.name, Customer.phone, Customer.customer_type).order_by(spend.desc()).limit(limit)
    return [{"customer_id": r.id, "name": r.name, "phone": r.phone, "type": r.customer_type,
             "spend": round(r.spend, 2), "orders": r.orders, "last_purchase": r.last.isoformat()}
            for r in db.execute(q).all()]


def repeat_rate(db: Session, rng: DateRange, outlet_ids: list[int] | None = None) -> dict:
    q = select(Sale.customer_id, func.count(Sale.id)).where(
        *_sale_filters(rng, outlet_ids), Sale.customer_id.is_not(None)).group_by(Sale.customer_id)
    counts = [c for _, c in db.execute(q).all()]
    total_orders = db.scalar(select(func.count(Sale.id)).where(*_sale_filters(rng, outlet_ids))) or 0
    identified = sum(counts)
    return {
        "customers": len(counts),
        "repeat_customers": sum(1 for c in counts if c > 1),
        "repeat_rate_pct": round(sum(1 for c in counts if c > 1) / len(counts) * 100, 1) if counts else 0,
        "identified_order_share_pct": round(identified / total_orders * 100, 1) if total_orders else 0,
    }


# --------------------------------------------------------------------------------------------- daily demand
def product_daily_units(db: Session, product_id: int, start: date, end: date,
                        outlet_ids: list[int] | None = None) -> pd.Series:
    q = select(SaleItem.sale_date, func.sum(SaleItem.quantity)).join(Sale, Sale.id == SaleItem.sale_id).where(
        COMPLETED, SaleItem.product_id == product_id, SaleItem.sale_date >= start, SaleItem.sale_date <= end)
    if outlet_ids:
        q = q.where(SaleItem.outlet_id.in_(outlet_ids))
    rows = db.execute(q.group_by(SaleItem.sale_date)).all()
    idx = pd.date_range(start, end, freq="D")
    s = pd.Series({pd.Timestamp(d): float(v) for d, v in rows}, dtype=float)
    return s.reindex(idx, fill_value=0.0)


def avg_daily_units_by_outlet_product(db: Session, days: int = 28, as_of: date | None = None) -> dict[tuple[int, int], float]:
    as_of = as_of or anchor_date(db)
    start = as_of - timedelta(days=days - 1)
    q = select(SaleItem.outlet_id, SaleItem.product_id, func.sum(SaleItem.quantity)).join(
        Sale, Sale.id == SaleItem.sale_id).where(COMPLETED, SaleItem.sale_date >= start,
                                                 SaleItem.sale_date <= as_of).group_by(SaleItem.outlet_id,
                                                                                       SaleItem.product_id)
    return {(o, p): float(q_) / days for o, p, q_ in db.execute(q).all()}


def outlet_names(db: Session) -> dict[int, str]:
    return dict(db.execute(select(Outlet.id, Outlet.name)).all())


def first_sale_date(db: Session) -> date | None:
    return db.scalar(select(func.min(Sale.sale_date)).where(COMPLETED))



# --------------------------------------------------------------------------------------------- market basket
@cached
def product_affinity(db: Session, rng: DateRange, outlet_ids: list[int] | None = None, limit: int = 15,
                     min_pair_count: int = 20) -> list[dict]:
    """Frequently-bought-together pairs (market basket analysis) ranked by lift.

    support = share of bills containing both, confidence = P(B | A), lift = P(A and B) / (P(A) P(B)).
    Lift > 1 means the products are bought together more often than chance.
    """
    from itertools import combinations

    q = _item_query(rng, outlet_ids, SaleItem.sale_id, SaleItem.product_id)
    df = pd.DataFrame(db.execute(q).all(), columns=["sale_id", "product_id"]).drop_duplicates()
    if df.empty:
        return []
    n_bills = df["sale_id"].nunique()
    item_counts = df["product_id"].value_counts()
    baskets = df.groupby("sale_id")["product_id"].apply(lambda s: sorted(s.tolist()))
    pair_counts: dict[tuple[int, int], int] = {}
    for items in baskets:
        if len(items) < 2:
            continue
        for a, b in combinations(items[:12], 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    names = dict(db.execute(select(Product.id, Product.name)).all())
    rows = []
    for (a, b), c in pair_counts.items():
        if c < min_pair_count:
            continue
        pa, pb = item_counts[a] / n_bills, item_counts[b] / n_bills
        support = c / n_bills
        lift = support / (pa * pb)
        if lift <= 1.05:
            continue
        conf_ab, conf_ba = c / item_counts[a], c / item_counts[b]
        rows.append({"product_a": names.get(a), "product_b": names.get(b), "product_a_id": int(a), "product_b_id": int(b),
                     "bills_together": int(c), "support_pct": round(float(support) * 100, 2), "lift": round(float(lift), 2),
                     "confidence_pct": round(float(max(conf_ab, conf_ba)) * 100, 1)})
    rows.sort(key=lambda r: (-r["lift"], -r["bills_together"]))
    return rows[:limit]


def lost_sales_estimate(db: Session, outlet_ids: list[int] | None = None) -> dict:
    """Revenue at risk per day from items that are out of stock but normally sell."""
    from app.models import InventoryItem

    demand = avg_daily_units_by_outlet_product(db, 28)
    q = select(InventoryItem.outlet_id, InventoryItem.product_id, Product.selling_price, Product.name).join(
        Product, Product.id == InventoryItem.product_id).where(InventoryItem.quantity <= 0, Product.is_active.is_(True))
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    items, total = [], 0.0
    for o, p, price, name in db.execute(q).all():
        rate = demand.get((o, p), 0)
        if rate > 0:
            total += rate * price
            items.append(name)
    return {"revenue_at_risk_per_day": round(total, 2), "items": items}
