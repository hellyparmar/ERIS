"""Demand & revenue forecasting.

Four models compete on every series; each is back-tested on a hold-out window (the most recent
`TEST_DAYS` days) and the model with the lowest WAPE wins ("auto"). Prediction intervals come from the
winning model's empirical back-test errors, so they reflect how accurate the model really was.

* Seasonal naive - "same weekday last weeks" baseline every model must beat
* Holt-Winters   - exponential smoothing with damped trend and weekly seasonality (statsmodels)
* Gradient boosting - recursive HistGradientBoosting on scale-free lags + calendar & festival features (scikit-learn)
* Prophet        - additive model with weekly/yearly seasonality and the retail festival calendar (Meta Prophet)
"""
from __future__ import annotations

import logging
import math
import threading
import time
import warnings
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, InventoryItem, Outlet, Product, Sale, SaleItem, Supplier
from app.services import analytics as A
from app.services.holidays import EVENTS, holidays_frame, upcoming_events

log = logging.getLogger(__name__)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("prophet.plot").setLevel(logging.CRITICAL)

TEST_DAYS = 28
MAX_HISTORY_DAYS = 730
MODEL_LABELS = {
    "seasonal_naive": "Seasonal naive (baseline)",
    "holt_winters": "Holt-Winters exponential smoothing",
    "gbm": "Gradient boosting (lags + calendar + festivals)",
    "prophet": "Prophet (seasonality + holidays)",
    "ensemble": "Ensemble (average of the two best models)",
}


def available_models() -> list[str]:
    models = ["seasonal_naive", "gbm"]
    try:
        import statsmodels  # noqa: F401

        models.insert(1, "holt_winters")
    except ImportError:
        pass
    try:
        import prophet  # noqa: F401

        models.append("prophet")
    except ImportError:
        pass
    return models


# ------------------------------------------------------------------------------------------ models
def _seasonal_naive(train: pd.Series, horizon: int) -> np.ndarray:
    """Average of the same weekday over the last 4 weeks."""
    vals = train.values
    out = []
    for h in range(1, horizon + 1):
        lags = [vals[-(7 * k) + ((h - 1) % 7)] for k in range(1, 5) if len(vals) >= 7 * k]
        out.append(np.mean(lags) if lags else vals[-1])
    return np.array(out)


def _holt_winters(train: pd.Series, horizon: int) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    y = train.iloc[-365:].astype(float)
    positive = (y > 0).all()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            y.values, trend="add", damped_trend=True, seasonal="mul" if positive else "add",
            seasonal_periods=7, initialization_method="estimated",
        ).fit(optimized=True)
    return np.clip(model.forecast(horizon), 0, None)


def _calendar_features(idx: pd.DatetimeIndex) -> pd.DataFrame:
    df = pd.DataFrame(index=idx)
    df["dow"] = idx.dayofweek
    df["weekend"] = (idx.dayofweek >= 5).astype(int)
    df["month"] = idx.month
    df["dom"] = idx.day
    doy = idx.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    names = sorted({e[0] for e in EVENTS})
    for n in names:
        df[f"ev_{n}"] = 0.0
    for name, day, before, after in EVENTS:
        ts = pd.Timestamp(day)
        for k in range(-after, before + 1):
            d = ts - pd.Timedelta(days=k)
            if d in df.index:
                # 1.0 on the day itself, fading with distance (captures build-up before festivals)
                df.loc[d, f"ev_{name}"] = max(df.loc[d, f"ev_{name}"], 1 - abs(k) / (before + after + 1))
                if k == 0:
                    df.loc[d, f"ev_{name}"] = 1.0
    return df


def _lag_features(y: np.ndarray, t: int, cal: np.ndarray) -> tuple[list[float], float]:
    level = float(y[t - 28:t].mean()) or 1.0
    return [y[t - 1] / level, y[t - 7] / level, y[t - 14] / level, y[t - 28] / level,
            y[t - 7:t].mean() / level, *cal[t]], level


def _gbm(train: pd.Series, horizon: int) -> np.ndarray:
    """Recursive gradient boosting on scale-free lag features + calendar/festival features (M5-style)."""
    from sklearn.ensemble import HistGradientBoostingRegressor

    y = train.clip(lower=0).astype(float).values
    idx = pd.date_range(train.index[0], periods=len(y) + horizon, freq="D")
    cal = _calendar_features(idx).values
    X, target = [], []
    for t in range(28, len(y)):
        f, level = _lag_features(y, t, cal)
        X.append(f)
        target.append(y[t] / level)
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                          min_samples_leaf=10, random_state=0)
    model.fit(np.array(X), np.array(target))
    ext = np.concatenate([y, np.zeros(horizon)])
    for t in range(len(y), len(y) + horizon):
        f, level = _lag_features(ext, t, cal)
        ext[t] = max(0.0, float(model.predict([f])[0]) * level)
    return ext[len(y):]


def _prophet(train: pd.Series, horizon: int) -> np.ndarray:
    from prophet import Prophet

    df = pd.DataFrame({"ds": train.index, "y": train.values.astype(float)})
    logging.getLogger("prophet").setLevel(logging.ERROR)
    # With under two years of history a full yearly Fourier series over-fits one season's peaks,
    # so use a smoother yearly term and a stiffer trend.
    if len(df) >= 730:
        yearly, cps = True, 0.05
    elif len(df) >= 365:
        yearly, cps = 4, 0.02
    else:
        yearly, cps = False, 0.05
    m = Prophet(weekly_seasonality=True, yearly_seasonality=yearly, daily_seasonality=False,
                holidays=holidays_frame(), seasonality_mode="multiplicative" if (df.y > 0).all() else "additive",
                changepoint_prior_scale=cps, uncertainty_samples=0)
    m.fit(df)
    future = m.make_future_dataframe(periods=horizon, include_history=False)
    return np.clip(m.predict(future)["yhat"].values, 0, None)


MODEL_FUNCS = {"seasonal_naive": _seasonal_naive, "holt_winters": _holt_winters, "gbm": _gbm, "prophet": _prophet}


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - actual
    total = np.abs(actual).sum()
    nz = actual > 0
    return {
        "mae": round(float(np.mean(np.abs(err))), 2),
        "rmse": round(float(np.sqrt(np.mean(err ** 2))), 2),
        "mape": round(float(np.mean(np.abs(err[nz] / actual[nz])) * 100), 2) if nz.any() else None,
        "wape": round(float(np.abs(err).sum() / total * 100), 2) if total else None,
        "bias_pct": round(float(err.sum() / total * 100), 2) if total else None,
    }


# ------------------------------------------------------------------------------------------ engine
@dataclass
class SeriesSpec:
    scope: str  # total | outlet | category | product
    target: str  # revenue | units
    label: str
    outlet_ids: list[int] | None
    category_id: int | None = None
    product_id: int | None = None


_cache: dict[tuple, tuple[float, dict]] = {}
_cache_lock = threading.Lock()
CACHE_SECONDS = 900


def _data_version(db: Session) -> tuple:
    return tuple(db.execute(select(func.count(Sale.id), func.max(Sale.id), func.max(Sale.sale_date))).one())


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


def load_series(db: Session, spec: SeriesSpec, end: date) -> pd.Series:
    start = max(A.first_sale_date(db) or end, end - timedelta(days=MAX_HISTORY_DAYS - 1))
    rng = A.DateRange(start, end)
    if spec.scope == "product":
        return A.product_daily_units(db, spec.product_id, start, end, spec.outlet_ids)
    rows = A.revenue_series(db, rng, spec.outlet_ids, "day", category_id=spec.category_id)
    key = "units" if spec.target == "units" else "revenue"
    s = pd.Series([r[key] for r in rows], index=pd.to_datetime([r["date"] for r in rows]), dtype=float)
    # Drop leading zeros (e.g. an outlet that opened recently).
    nz = np.flatnonzero(s.values > 0)
    return s.iloc[nz[0]:] if len(nz) else s


def run_forecast(series: pd.Series, horizon: int, model: str = "auto") -> dict:
    """Back-test all candidate models, choose the best and forecast `horizon` days ahead."""
    models = available_models()
    if model != "auto":
        if model not in MODEL_FUNCS:
            raise ValueError(f"Unknown model '{model}'")
        if model not in models:
            raise ValueError(f"Model '{model}' is not installed on this server")
    n = len(series)
    if n < 21 or series.sum() <= 0:
        raise ValueError("Not enough sales history to forecast (need at least 3 weeks of data)")

    test_days = min(TEST_DAYS, max(7, n // 5))
    train, test = series.iloc[:-test_days], series.iloc[-test_days:]
    if n < 120 and "prophet" in models:
        models.remove("prophet")  # Prophet needs a longer history to be reliable
    candidates = models if model == "auto" else sorted({model, "seasonal_naive"}, key=models.index)

    evaluation, test_preds = [], {}
    for name in candidates:
        t0 = time.time()
        try:
            pred = MODEL_FUNCS[name](train, test_days)
            m = _metrics(test.values, pred)
            m.update(model=name, label=MODEL_LABELS[name], seconds=round(time.time() - t0, 2))
            evaluation.append(m)
            test_preds[name] = pred
        except Exception as exc:  # a failing model must not break forecasting
            log.warning("model %s failed: %s", name, exc)
            evaluation.append({"model": name, "label": MODEL_LABELS[name], "error": str(exc)[:200]})

    scored = [e for e in evaluation if e.get("wape") is not None]
    if not scored:
        raise ValueError("All forecasting models failed for this series")
    # Ensemble candidate: averaging the two strongest models is usually more robust than either alone.
    members = [e["model"] for e in sorted(scored, key=lambda e: e["wape"]) if e["model"] != "seasonal_naive"][:2]
    if model == "auto" and len(members) == 2:
        pred = (test_preds[members[0]] + test_preds[members[1]]) / 2
        m = _metrics(test.values, pred)
        m.update(model="ensemble", label=f"Ensemble ({MODEL_LABELS[members[0]].split(' (')[0]} + "
                                         f"{MODEL_LABELS[members[1]].split(' (')[0]})", seconds=0.0)
        evaluation.append(m)
        scored.append(m)
        test_preds["ensemble"] = pred
    best = model if model != "auto" and model in test_preds else min(scored, key=lambda e: e["wape"])["model"]
    for e in evaluation:
        e["selected"] = e["model"] == best

    # Empirical 80% interval from back-test relative errors of the chosen model.
    actual, pred = test.values, test_preds[best]
    rel = (actual - pred) / np.where(pred > 0, pred, 1)
    lo_q, hi_q = np.quantile(rel, 0.1), np.quantile(rel, 0.9)

    if best == "ensemble":
        final = (MODEL_FUNCS[members[0]](series, horizon) + MODEL_FUNCS[members[1]](series, horizon)) / 2
    else:
        final = MODEL_FUNCS[best](series, horizon)
    idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    forecast = [
        {"date": d.date().isoformat(), "yhat": round(float(v), 2),
         "lower": round(float(max(0.0, v * (1 + lo_q))), 2), "upper": round(float(max(v, v * (1 + hi_q))), 2)}
        for d, v in zip(idx, final, strict=False)
    ]
    backtest = [
        {"date": d.date().isoformat(), "actual": round(float(a), 2), "predicted": round(float(p), 2)}
        for d, a, p in zip(test.index, actual, pred, strict=False)
    ]
    label = next(e["label"] for e in evaluation if e["model"] == best)
    return {"model": best, "model_label": label, "evaluation": evaluation,
            "forecast": forecast, "backtest": backtest, "test_days": test_days}


def forecast_series(db: Session, spec: SeriesSpec, horizon: int = 30, model: str = "auto",
                    history_days: int = 120) -> dict:
    horizon = max(7, min(int(horizon), 90))
    end = A.anchor_date(db)
    key = (spec.scope, spec.target, tuple(spec.outlet_ids or []), spec.category_id, spec.product_id, horizon, model,
           _data_version(db))
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < CACHE_SECONDS:
            return hit[1]

    series = load_series(db, spec, end)
    result = run_forecast(series, horizon, model)
    fc = result["forecast"]
    hist = series.iloc[-history_days:]
    last_30 = float(series.iloc[-30:].sum())
    next_30 = sum(f["yhat"] for f in fc[:30])
    next_7 = sum(f["yhat"] for f in fc[:7])
    last_7 = float(series.iloc[-7:].sum())
    same_period_last_year = None
    ly_start = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(days=364)
    ly = series.loc[ly_start: ly_start + pd.Timedelta(days=min(horizon, 30) - 1)]
    if len(ly) >= min(horizon, 30) * 0.8:
        same_period_last_year = round(float(ly.sum()), 2)
    peak = max(fc, key=lambda f: f["yhat"])
    weekday_profile = pd.Series([f["yhat"] for f in fc], index=pd.to_datetime([f["date"] for f in fc]))
    by_dow = weekday_profile.groupby(weekday_profile.index.dayofweek).mean()

    result.update({
        "series": {"scope": spec.scope, "target": spec.target, "label": spec.label},
        "as_of": end.isoformat(),
        "horizon": horizon,
        "history": [{"date": d.date().isoformat(), "actual": round(float(v), 2)} for d, v in hist.items()],
        "summary": {
            "next_7_days": round(next_7, 2),
            "next_30_days": round(next_30, 2) if horizon >= 30 else None,
            "horizon_total": round(sum(f["yhat"] for f in fc), 2),
            "avg_daily": round(sum(f["yhat"] for f in fc) / len(fc), 2),
            "last_7_days": round(last_7, 2),
            "last_30_days": round(last_30, 2),
            "change_vs_last_7_pct": A.pct_change(next_7, last_7),
            "change_vs_last_30_pct": A.pct_change(next_30, last_30) if horizon >= 30 else None,
            "same_period_last_year": same_period_last_year,
            "peak_day": peak,
            "busiest_weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][
                int(by_dow.idxmax())] if len(by_dow) else None,
        },
        "events": upcoming_events(end + timedelta(days=1), horizon),
    })
    result["insights"] = _insights(result, spec)
    with _cache_lock:
        _cache[key] = (time.time(), result)
    return result


def _insights(r: dict, spec: SeriesSpec) -> list[str]:
    s = r["summary"]
    unit = "units" if spec.target == "units" else "revenue"
    out = []
    ch = s.get("change_vs_last_30_pct") if s.get("change_vs_last_30_pct") is not None else s.get("change_vs_last_7_pct")
    window = "30" if s.get("change_vs_last_30_pct") is not None else "7"
    if ch is not None:
        direction = "higher" if ch >= 0 else "lower"
        out.append(f"Expected {unit} over the next {window} days is {abs(ch):.1f}% {direction} than the last {window} days.")
    if s.get("busiest_weekday"):
        out.append(f"{s['busiest_weekday']} is forecast to be the busiest day of the week.")
    for ev in r.get("events", [])[:2]:
        out.append(f"{ev['name']} is {ev['days_away']} days away - festival demand is built into the forecast.")
    sel = next(e for e in r["evaluation"] if e.get("selected"))
    base = next((e for e in r["evaluation"] if e["model"] == "seasonal_naive" and e.get("wape") is not None), None)
    if base and sel["model"] != "seasonal_naive" and base["wape"]:
        gain = (base["wape"] - sel["wape"]) / base["wape"] * 100
        out.append(f"{sel['label']} was most accurate in back-testing (WAPE {sel['wape']:.1f}%), "
                   f"{gain:.0f}% better than the naive baseline.")
    else:
        out.append(f"{sel['label']} was most accurate in back-testing (WAPE {sel['wape']:.1f}%).")
    return out


# ------------------------------------------------------------------------------------------ specs
def build_spec(db: Session, scope: str, target_id: int | None, outlet_ids: list[int] | None) -> SeriesSpec:
    if scope == "total":
        label = "All outlets" if not outlet_ids else ", ".join(
            db.scalars(select(Outlet.name).where(Outlet.id.in_(outlet_ids))).all())
        return SeriesSpec("total", "revenue", f"Revenue - {label}", outlet_ids)
    if scope == "outlet":
        outlet = db.get(Outlet, target_id) if target_id else None
        if not outlet:
            raise LookupError("Outlet not found")
        if outlet_ids and outlet.id not in outlet_ids:
            raise PermissionError("You can only forecast your own outlet")
        return SeriesSpec("outlet", "revenue", f"Revenue - {outlet.name}", [outlet.id])
    if scope == "category":
        cat = db.get(Category, target_id) if target_id else None
        if not cat:
            raise LookupError("Category not found")
        return SeriesSpec("category", "revenue", f"Revenue - {cat.name}", outlet_ids, category_id=cat.id)
    if scope == "product":
        p = db.get(Product, target_id) if target_id else None
        if not p:
            raise LookupError("Product not found")
        return SeriesSpec("product", "units", f"Units - {p.name}", outlet_ids, product_id=p.id)
    raise ValueError("scope must be one of total, outlet, category, product")


# ------------------------------------------------------------------------------------------ stock planning
def product_stock_plan(db: Session, product_id: int, forecast: dict, outlet_ids: list[int] | None) -> dict:
    """Days of cover, projected stock-out date and recommended order quantity for one product."""
    p = db.get(Product, product_id)
    q = select(func.coalesce(func.sum(InventoryItem.quantity), 0)).where(InventoryItem.product_id == product_id)
    if outlet_ids:
        q = q.where(InventoryItem.outlet_id.in_(outlet_ids))
    stock = float(db.scalar(q) or 0)
    lead = (db.get(Supplier, p.supplier_id).lead_time_days if p.supplier_id else 3) or 3
    fc = forecast["forecast"]
    cum, stockout = 0.0, None
    for f in fc:
        cum += f["yhat"]
        if stockout is None and cum >= stock:
            stockout = f["date"]
    hist = [h["actual"] for h in forecast["history"][-28:]]
    sigma = float(np.std(hist)) if hist else 0.0
    review = 7
    need = sum(f["yhat"] for f in fc[: lead + review])
    safety = 1.65 * sigma * math.sqrt(lead)  # ~95% service level
    recommended = max(0, math.ceil(need + safety - stock))
    avg = forecast["summary"]["avg_daily"]
    return {
        "current_stock": round(stock, 1),
        "avg_daily_demand": avg,
        "days_of_cover": round(stock / avg, 1) if avg > 0 else None,
        "projected_stockout": stockout,
        "lead_time_days": lead,
        "safety_stock": round(safety, 1),
        "recommended_order_qty": recommended,
        "reorder_by": (date.fromisoformat(stockout) - timedelta(days=lead + 1)).isoformat() if stockout else None,
        "unit": p.unit,
    }


def reorder_suggestions(db: Session, outlet_ids: list[int] | None = None, limit: int | None = None) -> list[dict]:
    """Fast demand-driven reorder list for every outlet x product.

    Uses the last 28 days of sales with a recent-trend adjustment (last 14 vs previous 14 days) for the
    demand rate, and day-to-day variability for safety stock. Pending purchase orders count as incoming stock.
    """
    from app.models import PurchaseOrder, PurchaseOrderItem

    as_of = A.anchor_date(db)
    start = as_of - timedelta(days=27)
    q = select(SaleItem.outlet_id, SaleItem.product_id, SaleItem.sale_date, func.sum(SaleItem.quantity)).join(
        Sale, Sale.id == SaleItem.sale_id).where(A.COMPLETED, SaleItem.sale_date >= start,
                                                 SaleItem.sale_date <= as_of)
    if outlet_ids:
        q = q.where(SaleItem.outlet_id.in_(outlet_ids))
    df = pd.DataFrame(db.execute(q.group_by(SaleItem.outlet_id, SaleItem.product_id, SaleItem.sale_date)).all(),
                      columns=["outlet_id", "product_id", "d", "units"])
    stats: dict[tuple[int, int], tuple[float, float]] = {}
    if not df.empty:
        df["d"] = pd.to_datetime(df["d"])
        days = pd.date_range(start, as_of, freq="D")
        for (o, p), g in df.groupby(["outlet_id", "product_id"]):
            s = g.set_index("d")["units"].reindex(days, fill_value=0.0)
            recent, prior = s.iloc[-14:].mean(), s.iloc[:14].mean()
            trend = min(max(recent / prior, 0.7), 1.4) if prior > 0 else 1.0
            stats[(o, p)] = (float(s.mean() * (0.5 + 0.5 * trend)), float(s.std()))

    incoming_q = select(PurchaseOrder.outlet_id, PurchaseOrderItem.product_id, func.sum(PurchaseOrderItem.quantity)).join(
        PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id).where(PurchaseOrder.status == "ordered").group_by(
        PurchaseOrder.outlet_id, PurchaseOrderItem.product_id)
    incoming = {(o, p): float(v) for o, p, v in db.execute(incoming_q).all()}

    inv_q = select(InventoryItem, Product, Outlet, Supplier).join(Product, Product.id == InventoryItem.product_id).join(
        Outlet, Outlet.id == InventoryItem.outlet_id).outerjoin(Supplier, Supplier.id == Product.supplier_id).where(
        Product.is_active.is_(True), Outlet.is_active.is_(True))
    if outlet_ids:
        inv_q = inv_q.where(InventoryItem.outlet_id.in_(outlet_ids))
    out = []
    for inv, p, o, s in db.execute(inv_q).all():
        rate, sigma = stats.get((o.id, p.id), (0.0, 0.0))
        lead = s.lead_time_days if s else 3
        on_order = incoming.get((o.id, p.id), 0.0)
        position = inv.quantity + on_order
        reorder_point = max(inv.reorder_level, rate * lead + 1.65 * sigma * math.sqrt(lead))
        if rate <= 0 and inv.quantity > inv.reorder_level:
            continue
        if position > reorder_point:
            continue
        target = rate * (lead + 7) + 1.65 * sigma * math.sqrt(lead)
        qty = max(math.ceil(target - position), math.ceil(inv.reorder_level - position), 0)
        if qty <= 0:
            continue
        out.append({
            "outlet_id": o.id, "outlet": o.name, "product_id": p.id, "sku": p.sku, "product": p.name,
            "unit": p.unit, "supplier_id": s.id if s else None, "supplier": s.name if s else None,
            "current_stock": inv.quantity, "on_order": on_order, "reorder_level": inv.reorder_level,
            "avg_daily_demand": round(rate, 2), "days_of_cover": round(inv.quantity / rate, 1) if rate > 0 else None,
            "lead_time_days": lead, "suggested_qty": qty, "unit_cost": p.cost_price,
            "estimated_cost": round(qty * p.cost_price, 2),
            "urgency": "critical" if inv.quantity <= 0 or (rate > 0 and inv.quantity / rate < lead) else "soon",
        })
    out.sort(key=lambda r: (r["urgency"] != "critical", r["days_of_cover"] if r["days_of_cover"] is not None else 0))
    return out[:limit] if limit else out
