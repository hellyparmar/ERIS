"""Feature engineering for forecasting (reproducible: everything is derived from database tables).

Calendar features    day of week, weekend, day of month, month, quarter, day-of-year (sin/cos), festival proximity
Lag features         y(t-7), y(t-14), y(t-21), y(t-28), scale-free: divided by the 28-day rolling mean
                     ("level"), so one model shape fits small and large series; the model predicts y / level
Exogenous drivers    promo_depth  - revenue-weighted average discount of the series' products on promotion
                     price_index  - revenue-weighted shelf price relative to the start of the series
                     temp_max_c, rain_mm - outlet-weighted daily weather (climatology for future days)
                     stockout_share - revenue share of the series' products that were out of stock

Promotions are planned in advance and future weather is climatology, so both are legitimately known for the
forecast horizon; future stockouts are unknown and set to 0 (no leakage).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.models import Outlet, PriceHistory, Product, Promotion, Sale, SaleItem, StockoutEvent, WeatherDaily
from app.services.holidays import EVENTS

CALENDAR_FEATURES = ["dow", "weekend", "dom", "month", "quarter", "doy_sin", "doy_cos"]
LAG_FEATURES = ["lag7", "lag14", "lag21", "lag28"]
EXOG_FEATURES = ["promo_depth", "price_index", "temp_max_c", "rain_mm", "stockout_share"]
FESTIVALS = sorted({e[0] for e in EVENTS})


def calendar_features(idx: pd.DatetimeIndex) -> pd.DataFrame:
    df = pd.DataFrame(index=idx)
    df["dow"] = idx.dayofweek
    df["weekend"] = (idx.dayofweek >= 5).astype(int)
    df["dom"] = idx.day
    df["month"] = idx.month
    df["quarter"] = idx.quarter
    doy = idx.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    for n in FESTIVALS:
        df[f"fest_{n}"] = 0.0
    for name, day, before, after in EVENTS:
        ts = pd.Timestamp(day)
        for k in range(-after, before + 1):
            d = ts - pd.Timedelta(days=k)
            if d in df.index:
                # 1.0 on the festival day, fading with distance (captures the build-up before festivals)
                v = 1.0 if k == 0 else 1 - abs(k) / (before + after + 1)
                df.loc[d, f"fest_{name}"] = max(df.loc[d, f"fest_{name}"], v)
    return df


def feature_names() -> list[str]:
    return LAG_FEATURES + CALENDAR_FEATURES + [f"fest_{n}" for n in FESTIVALS] + EXOG_FEATURES


def exogenous_features(db: Session, start: date, end: date, outlet_ids: list[int] | None,
                       category_id: int | None = None, product_id: int | None = None) -> pd.DataFrame:
    """Daily exogenous drivers for a series (outlets x products) from `start` to `end` (may include future days)."""
    idx = pd.date_range(start, end, freq="D")
    out = pd.DataFrame(0.0, index=idx, columns=EXOG_FEATURES)
    out["price_index"] = 1.0

    # product weights: revenue share over the last 180 days of history inside the series scope
    pq = select(Product.id).where(Product.is_active.is_(True))
    if product_id:
        pq = select(Product.id).where(Product.id == product_id)
    elif category_id:
        pq = pq.where(Product.category_id == category_id)
    product_ids = list(db.scalars(pq).all())
    if not product_ids:
        return out
    hist_end = min(end, clock.today())
    wq = select(SaleItem.product_id, func.sum(SaleItem.line_total)).join(Sale, Sale.id == SaleItem.sale_id).where(
        Sale.status == "completed", SaleItem.product_id.in_(product_ids),
        SaleItem.sale_date > hist_end - timedelta(days=180))
    if outlet_ids:
        wq = wq.where(SaleItem.outlet_id.in_(outlet_ids))
    rev = dict(db.execute(wq.group_by(SaleItem.product_id)).all())
    total = sum(rev.values()) or 1.0
    pw = {p: rev.get(p, 0.0) / total for p in product_ids}
    if not any(pw.values()):
        pw = {p: 1 / len(product_ids) for p in product_ids}

    oq = select(Outlet.id, Outlet.city)
    if outlet_ids:
        oq = oq.where(Outlet.id.in_(outlet_ids))
    outlets = db.execute(oq).all()
    ow = {o: 1 / len(outlets) for o, _ in outlets} if outlets else {}
    cats = dict(db.execute(select(Product.id, Product.category_id).where(Product.id.in_(product_ids))).all())

    # promotions (historic + planned)
    promos = db.scalars(select(Promotion).where(Promotion.end_date >= start, Promotion.start_date <= end)).all()
    for pr in promos:
        affected = [p for p in product_ids if (pr.product_id and p == pr.product_id) or
                    (pr.category_id and cats.get(p) == pr.category_id)]
        if not affected:
            continue
        share_o = 1.0 if pr.outlet_id is None else ow.get(pr.outlet_id, 0.0)
        if not share_o:
            continue
        depth = sum(pw[p] for p in affected) * share_o * pr.discount_pct / 100
        s, e = max(pr.start_date, start), min(pr.end_date, end)
        out.loc[pd.Timestamp(s):pd.Timestamp(e), "promo_depth"] += depth

    # price index from price history (step function per product)
    hist = db.execute(select(PriceHistory.product_id, PriceHistory.effective_from, PriceHistory.selling_price).where(
        PriceHistory.product_id.in_(product_ids)).order_by(PriceHistory.product_id, PriceHistory.effective_from)).all()
    if hist:
        dfp = pd.DataFrame(hist, columns=["product_id", "day", "price"])
        index = np.zeros(len(idx))
        for p, g in dfp.groupby("product_id"):
            s = pd.Series(g["price"].values, index=pd.to_datetime(g["day"])).sort_index()
            s = s[~s.index.duplicated(keep="last")]
            daily = s.reindex(s.index.union(idx)).ffill().bfill().reindex(idx)
            index += pw.get(p, 0.0) * (daily.values / float(daily.iloc[0]))
        if index.sum():
            out["price_index"] = index

    # weather (outlet-weighted)
    cities = {}
    for o, city in outlets:
        cities[city] = cities.get(city, 0.0) + ow[o]
    if cities:
        wrows = db.execute(select(WeatherDaily.city, WeatherDaily.day, WeatherDaily.temp_max_c, WeatherDaily.rain_mm).where(
            WeatherDaily.city.in_(list(cities)), WeatherDaily.day >= start, WeatherDaily.day <= end)).all()
        if wrows:
            w = pd.DataFrame(wrows, columns=["city", "day", "temp", "rain"])
            w["day"] = pd.to_datetime(w["day"])
            w["wt"] = w["city"].map(cities)
            agg = w.assign(t=w.temp * w.wt, r=w.rain * w.wt).groupby("day")[["t", "r", "wt"]].sum()
            out["temp_max_c"] = (agg["t"] / agg["wt"]).reindex(idx).interpolate().ffill().bfill().fillna(0.0)
            out["rain_mm"] = (agg["r"] / agg["wt"]).reindex(idx).fillna(0.0)

    # stockouts (history only)
    events = db.execute(select(StockoutEvent.outlet_id, StockoutEvent.product_id, StockoutEvent.start_date,
                               StockoutEvent.end_date).where(StockoutEvent.product_id.in_(product_ids),
                                                             StockoutEvent.end_date >= start,
                                                             StockoutEvent.start_date <= min(end, hist_end))).all()
    for o, p, s, e in events:
        if o in ow:
            out.loc[pd.Timestamp(max(s, start)):pd.Timestamp(min(e, end)), "stockout_share"] += pw.get(p, 0.0) * ow[o]
    return out.astype(float)
