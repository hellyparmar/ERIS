"""Demand & revenue forecasting (model version 3).

Candidates, all trained only on data before each validation fold:

* Seasonal naive  - mean of the same weekday over the last 4 weeks: the baseline every model must beat
* Holt-Winters    - exponential smoothing with damped trend and weekly seasonality (statsmodels)
* XGBoost         - recursive gradient-boosted trees on scale-free lags, rolling means, calendar, festival and
                    exogenous features (promotions, price index, weather, stockouts) - see services/features.py
* Prophet         - weekly/yearly seasonality, the festival calendar as holidays, promotions/price/weather as
                    extra regressors (Meta Prophet)
* Ensemble        - mean of the two best non-baseline models

Selection: every candidate is scored on two consecutive 28-day folds at the end of the history. Prophet is the
incumbent and is replaced only when a challenger's WAPE is more than 10% lower (rule chosen by the rolling-origin
study in docs/FORECAST_EVALUATION.md). The 80% interval comes from the chosen model's back-test errors; its
coverage on the most recent fold (using intervals estimated on the earlier fold) is reported honestly.
Every forecast is persisted as a ForecastRun with data range, features, parameters, metrics and the selection.
A failure is recorded and reported as an error - never replaced by made-up numbers.
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

from app import clock
from app.db import write_session
from app.models import (
    OPEN_PO_STATUSES,
    Category,
    ForecastResult,
    ForecastRun,
    InventoryItem,
    Outlet,
    Product,
    Sale,
    SaleItem,
    Supplier,
)
from app.services import analytics as A
from app.services.features import (
    CALENDAR_FEATURES,
    EXOG_FEATURES,
    FESTIVALS,
    calendar_features,
    exogenous_features,
    feature_names,
)
from app.services.holidays import holidays_frame, upcoming_events

log = logging.getLogger(__name__)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("prophet.plot").setLevel(logging.CRITICAL)

MODEL_VERSION = "3.0"
TEST_DAYS = 28
INCUMBENT = "prophet"
SWITCH_MARGIN = 0.10  # a challenger must cut back-test WAPE by >10% to replace the incumbent
MAX_HISTORY_DAYS = 730
XGB_PARAMS = {"n_estimators": 350, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.8,
              "colsample_bytree": 0.8, "min_child_weight": 3, "random_state": 0}
MODEL_LABELS = {
    "seasonal_naive": "Seasonal naive (baseline)",
    "holt_winters": "Holt-Winters exponential smoothing",
    "xgboost": "XGBoost (lags + calendar + promotions + weather)",
    "prophet": "Prophet (seasonality + holidays + regressors)",
    "ensemble": "Ensemble (average of the two best models)",
}


def available_models() -> list[str]:
    models = ["seasonal_naive"]
    for name, module in (("holt_winters", "statsmodels"), ("xgboost", "xgboost"), ("prophet", "prophet")):
        try:
            __import__(module)
            models.append(name)
        except ImportError:
            pass
    return models


def short_label(model: str) -> str:
    return MODEL_LABELS.get(model, model).split(" (")[0]


# ------------------------------------------------------------------------------------------ models
# Every model has the signature f(train: Series, horizon: int, exog: DataFrame | None) -> ndarray.
# `exog` (when given) is indexed from the first training day to the last forecast day.

def _seasonal_naive(train: pd.Series, horizon: int, exog=None) -> np.ndarray:
    vals = train.values
    out = []
    for h in range(1, horizon + 1):
        lags = [vals[-(7 * k) + ((h - 1) % 7)] for k in range(1, 5) if len(vals) >= 7 * k]
        out.append(np.mean(lags) if lags else vals[-1])
    return np.array(out)


def _holt_winters(train: pd.Series, horizon: int, exog=None) -> np.ndarray:
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


def _lag_row(y: np.ndarray, t: int) -> tuple[list[float], float]:
    """Weekly lags scaled by the 28-day level. (A lag-1 term was tested and dropped: in recursive multi-step
    forecasting it compounds errors - weekly lags were better on 4 of 6 benchmark series.)"""
    level = float(y[t - 28:t].mean()) or 1.0
    return [y[t - 7] / level, y[t - 14] / level, y[t - 21] / level, y[t - 28] / level], level


def _design(train: pd.Series, horizon: int, exog: pd.DataFrame | None) -> np.ndarray:
    idx = pd.date_range(train.index[0], periods=len(train) + horizon, freq="D")
    cal = calendar_features(idx)
    if exog is not None:
        cal = cal.join(exog.reindex(idx).ffill().fillna(0.0))
    else:
        for c in EXOG_FEATURES:
            cal[c] = 0.0
    return cal[CALENDAR_FEATURES + [f"fest_{n}" for n in FESTIVALS] + EXOG_FEATURES].values


def _xgboost(train: pd.Series, horizon: int, exog: pd.DataFrame | None = None) -> np.ndarray:
    """Recursive XGBoost on scale-free lags + calendar/festival + exogenous features (M5-style)."""
    import xgboost as xgb  # native API: same model as XGBRegressor without needing scikit-learn

    y = train.clip(lower=0).astype(float).values
    other = _design(train, horizon, exog)
    X, target = [], []
    for t in range(28, len(y)):
        lags, level = _lag_row(y, t)
        X.append(lags + list(other[t]))
        target.append(y[t] / level)
    params = {k: v for k, v in XGB_PARAMS.items() if k not in ("n_estimators", "random_state")}
    params.update(objective="reg:squarederror", seed=XGB_PARAMS["random_state"], nthread=2, verbosity=0)
    model = xgb.train(params, xgb.DMatrix(np.array(X), label=np.array(target)),
                      num_boost_round=XGB_PARAMS["n_estimators"])
    ext = np.concatenate([y, np.zeros(horizon)])
    for t in range(len(y), len(y) + horizon):
        lags, level = _lag_row(ext, t)
        ext[t] = max(0.0, float(model.inplace_predict(np.array([lags + list(other[t])]))[0]) * level)
    return ext[len(y):]


def _prophet(train: pd.Series, horizon: int, exog: pd.DataFrame | None = None) -> np.ndarray:
    from prophet import Prophet

    df = pd.DataFrame({"ds": train.index, "y": train.values.astype(float)})
    logging.getLogger("prophet").setLevel(logging.ERROR)
    if len(df) >= 730:
        yearly, cps = True, 0.05
    elif len(df) >= 365:
        yearly, cps = 4, 0.02  # smoother yearly term + stiffer trend with under two years of history
    else:
        yearly, cps = False, 0.05
    m = Prophet(weekly_seasonality=True, yearly_seasonality=yearly, daily_seasonality=False,
                holidays=holidays_frame(), seasonality_mode="multiplicative" if (df.y > 0).all() else "additive",
                changepoint_prior_scale=cps, uncertainty_samples=0)
    future = pd.DataFrame({"ds": pd.date_range(train.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")})
    regressors = []
    if exog is not None:
        for col in ("promo_depth", "price_index", "temp_max_c", "rain_mm"):
            hist = exog[col].reindex(train.index)
            if hist.std() > 1e-6:
                regressors.append(col)
                m.add_regressor(col, mode="additive" if col in ("temp_max_c", "rain_mm") else "multiplicative")
                df[col] = hist.values
                future[col] = exog[col].reindex(future["ds"]).ffill().fillna(float(hist.iloc[-1])).values
    m.fit(df)
    return np.clip(m.predict(future)["yhat"].values, 0, None)


MODEL_FUNCS = {"seasonal_naive": _seasonal_naive, "holt_winters": _holt_winters, "xgboost": _xgboost,
               "prophet": _prophet}


def _metrics(actual: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - actual
    total = np.abs(actual).sum()
    nz = actual > 0
    denom = np.abs(actual) + np.abs(pred)
    ok = denom > 0
    return {
        "mae": round(float(np.mean(np.abs(err))), 2),
        "rmse": round(float(np.sqrt(np.mean(err ** 2))), 2),
        "mape": round(float(np.mean(np.abs(err[nz] / actual[nz])) * 100), 2) if nz.any() else None,
        "smape": round(float(np.mean(2 * np.abs(err[ok]) / denom[ok]) * 100), 2) if ok.any() else None,
        "wape": round(float(np.abs(err).sum() / total * 100), 2) if total else None,
        "bias_pct": round(float(err.sum() / total * 100), 2) if total else None,
    }


def _interval(actual: np.ndarray, pred: np.ndarray, alpha: float = 0.2) -> tuple[float, float]:
    """Relative error bounds for an 80% band from back-test errors (split-conformal quantile levels).

    Plain 10th/90th percentiles of a few dozen errors give a band that is too narrow on new days; the conformal
    finite-sample correction uses the ceil((n + 1)(1 - alpha/2))-th smallest error instead."""
    rel = np.sort((actual - pred) / np.where(pred > 0, pred, 1))
    n = len(rel)
    k = min(n, int(np.ceil((n + 1) * (1 - alpha / 2))))
    return float(rel[n - k]), float(rel[k - 1])


def _coverage(actual: np.ndarray, pred: np.ndarray, lo_q: float, hi_q: float) -> float:
    lo, hi = pred * (1 + lo_q), np.maximum(pred, pred * (1 + hi_q))
    return round(float(np.mean((actual >= lo) & (actual <= hi)) * 100), 1)


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
        s = A.product_daily_units(db, spec.product_id, start, end, spec.outlet_ids)
    else:
        rows = A.revenue_series(db, rng, spec.outlet_ids, "day", category_id=spec.category_id)
        key = "units" if spec.target == "units" else "revenue"
        s = pd.Series([r[key] for r in rows], index=pd.to_datetime([r["date"] for r in rows]), dtype=float)
    nz = np.flatnonzero(s.values > 0)  # drop leading zeros (e.g. an outlet that opened recently)
    return s.iloc[nz[0]:] if len(nz) else s


def load_exog(db: Session, spec: SeriesSpec, series: pd.Series, horizon: int) -> pd.DataFrame | None:
    if series.empty:
        return None
    return exogenous_features(db, series.index[0].date(), series.index[-1].date() + timedelta(days=horizon),
                              spec.outlet_ids, spec.category_id, spec.product_id)


def run_forecast(series: pd.Series, horizon: int, model: str = "auto", exog: pd.DataFrame | None = None) -> dict:
    """Back-test the candidate models, choose one and forecast `horizon` days ahead."""
    models = available_models()
    if model != "auto":
        if model not in MODEL_FUNCS:
            raise ValueError(f"Unknown model '{model}'")
        if model not in models:
            raise ValueError(f"Model '{model}' is not installed on this server")
    n = len(series)
    if n < 21 or series.sum() <= 0:
        raise ValueError("Not enough sales history to forecast (need at least 3 weeks with sales)")

    test_days = min(TEST_DAYS, max(7, n // 5))
    n_folds = 2 if n - 2 * test_days >= 120 else 1
    folds = [(n - (k + 1) * test_days, n - k * test_days) for k in range(n_folds - 1, -1, -1)]
    if n < 120 and "prophet" in models:
        models.remove("prophet")  # Prophet needs a longer history to be reliable
    if n < 70 and "xgboost" in models:
        models.remove("xgboost")
    candidates = models if model == "auto" else sorted({model, "seasonal_naive"}, key=models.index)
    actual = np.concatenate([series.values[a:b] for a, b in folds])

    def fit(name: str, train: pd.Series, h: int) -> np.ndarray:
        ex = exog.loc[:train.index[-1] + pd.Timedelta(days=h)] if exog is not None else None
        return MODEL_FUNCS[name](train, h, ex)

    evaluation, test_preds = [], {}
    for name in candidates:
        t0 = time.time()
        try:
            parts = [fit(name, series.iloc[:a], b - a) for a, b in folds]
            pred = np.concatenate(parts)
            m = _metrics(actual, pred)
            if n_folds == 2:
                lo_q, hi_q = _interval(series.values[folds[0][0]:folds[0][1]], parts[0])
                m["interval_coverage"] = _coverage(series.values[folds[1][0]:folds[1][1]], parts[1], lo_q, hi_q)
            m.update(model=name, label=MODEL_LABELS[name], train_seconds=round(time.time() - t0, 2))
            evaluation.append(m)
            test_preds[name] = pred
        except Exception as exc:  # a failing model must not break forecasting
            log.warning("model %s failed: %s", name, exc)
            evaluation.append({"model": name, "label": MODEL_LABELS[name], "error": str(exc)[:200]})

    scored = [e for e in evaluation if e.get("wape") is not None]
    if not scored:
        raise ValueError("All forecasting models failed for this series")
    members = [e["model"] for e in sorted(scored, key=lambda e: e["wape"]) if e["model"] != "seasonal_naive"][:2]
    if model == "auto" and len(members) == 2:
        pred = (test_preds[members[0]] + test_preds[members[1]]) / 2
        m = _metrics(actual, pred)
        m.update(model="ensemble", label=f"Ensemble ({short_label(members[0])} + {short_label(members[1])})",
                 train_seconds=0.0)
        evaluation.append(m)
        scored.append(m)
        test_preds["ensemble"] = pred
    if model != "auto" and model in test_preds:
        best = model
    else:
        top = min(scored, key=lambda e: e["wape"])
        incumbent = next((e for e in scored if e["model"] == INCUMBENT), None)
        best = top["model"]
        if incumbent and top is not incumbent and top["wape"] > incumbent["wape"] * (1 - SWITCH_MARGIN):
            best = INCUMBENT
    for e in evaluation:
        e["selected"] = e["model"] == best

    pred = test_preds[best]
    lo_q, hi_q = _interval(actual, pred)
    test = series.iloc[folds[-1][0]:]
    last_pred = pred[-test_days:]

    t0 = time.time()
    if best == "ensemble":
        final = (fit(members[0], series, horizon) + fit(members[1], series, horizon)) / 2
    else:
        final = fit(best, series, horizon)
    inference_seconds = round(time.time() - t0, 2)
    idx = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    forecast = [
        {"date": d.date().isoformat(), "yhat": round(float(v), 2),
         "lower": round(float(max(0.0, v * (1 + lo_q))), 2), "upper": round(float(max(v, v * (1 + hi_q))), 2)}
        for d, v in zip(idx, final, strict=False)
    ]
    backtest = [
        {"date": d.date().isoformat(), "actual": round(float(a), 2), "predicted": round(float(p), 2)}
        for d, a, p in zip(test.index, test.values, last_pred, strict=False)
    ]
    label = next(e["label"] for e in evaluation if e["model"] == best)
    return {"model": best, "model_label": label, "evaluation": evaluation, "forecast": forecast,
            "backtest": backtest, "test_days": test_days * n_folds, "folds": n_folds,
            "ensemble_members": members if best == "ensemble" else None,
            "final_fit_seconds": inference_seconds}


def _persist(spec: SeriesSpec, series: pd.Series | None, horizon: int, result: dict | None,
             error: str | None, seconds: float, user_id: int | None, run_type: str = "forecast") -> int | None:
    try:
        run = ForecastRun(
            run_type=run_type, scope=spec.scope, target=spec.target, series_label=spec.label,
            outlet_ids=spec.outlet_ids, category_id=spec.category_id, product_id=spec.product_id, horizon=horizon,
            data_start=series.index[0].date() if series is not None and len(series) else None,
            data_end=series.index[-1].date() if series is not None and len(series) else None,
            selected_model=result["model"] if result else None, model_version=MODEL_VERSION,
            features=feature_names(),
            parameters={"selection": "two 28-day folds, Prophet incumbent, 10% switch margin",
                        "test_days": result["test_days"] if result else None, "xgboost": XGB_PARAMS,
                        "interval": "split-conformal 80% band from relative back-test errors",
                        "ensemble_members": result.get("ensemble_members") if result else None},
            metrics=result["evaluation"] if result else None, status="ok" if result else "failed",
            error=error, duration_seconds=round(seconds, 2), created_by=user_id)
        if result:
            run.results = [ForecastResult(day=date.fromisoformat(f["date"]), yhat=f["yhat"], lower=f["lower"],
                                          upper=f["upper"]) for f in result["forecast"]]
        with write_session() as wdb:
            wdb.add(run)
            wdb.commit()
            return run.id
    except Exception:  # persisting must never break forecasting
        log.exception("could not persist forecast run")
        return None


def forecast_series(db: Session, spec: SeriesSpec, horizon: int = 30, model: str = "auto",
                    history_days: int = 120, user_id: int | None = None, persist: bool = True) -> dict:
    horizon = max(7, min(int(horizon), 90))
    end = A.anchor_date(db)
    key = (spec.scope, spec.target, tuple(spec.outlet_ids or []), spec.category_id, spec.product_id, horizon, model,
           _data_version(db))
    with _cache_lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < CACHE_SECONDS:
            if isinstance(hit[1], ValueError):
                raise hit[1]  # the same data cannot be forecast: answer again without another failed run
            return hit[1]

    t0 = time.time()
    series = None
    try:
        series = load_series(db, spec, end)
        exog = load_exog(db, spec, series, horizon)
        result = run_forecast(series, horizon, model, exog)
    except ValueError as exc:
        if persist:
            _persist(spec, series, horizon, None, str(exc), time.time() - t0, user_id)
        with _cache_lock:
            _cache[key] = (time.time(), exc)
        raise
    result["run_id"] = _persist(spec, series, horizon, result, None, time.time() - t0, user_id) if persist else None
    result["model_version"] = MODEL_VERSION
    result["data_range"] = {"start": series.index[0].date().isoformat(), "end": series.index[-1].date().isoformat(),
                            "days": len(series)}
    result["features"] = feature_names()
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
        out.append(f"{sel['label']} was selected after back-testing on the last 8 weeks (WAPE {sel['wape']:.1f}%), "
                   f"{gain:.0f}% better than the naive baseline.")
    else:
        out.append(f"{sel['label']} was selected after back-testing (WAPE {sel['wape']:.1f}%).")
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

    outstanding = PurchaseOrderItem.quantity - func.coalesce(PurchaseOrderItem.received_quantity, 0)
    incoming_q = select(PurchaseOrder.outlet_id, PurchaseOrderItem.product_id, func.sum(outstanding)).join(
        PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id).where(
        PurchaseOrder.status.in_(OPEN_PO_STATUSES)).group_by(
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


def stockout_risk(db: Session, days: int = 14, outlet_ids: list[int] | None = None) -> list[dict]:
    """Items expected to run out within `days`: stock + open purchase orders vs trend-adjusted demand.

    Uses the same demand-rate estimate as the reorder planner (last 28 days, recent-trend adjusted).
    """
    from app.models import PurchaseOrder, PurchaseOrderItem

    as_of = A.anchor_date(db)
    start = as_of - timedelta(days=27)
    q = select(SaleItem.outlet_id, SaleItem.product_id, SaleItem.sale_date, func.sum(SaleItem.quantity)).join(
        Sale, Sale.id == SaleItem.sale_id).where(A.COMPLETED, SaleItem.sale_date >= start, SaleItem.sale_date <= as_of)
    if outlet_ids:
        q = q.where(SaleItem.outlet_id.in_(outlet_ids))
    df = pd.DataFrame(db.execute(q.group_by(SaleItem.outlet_id, SaleItem.product_id, SaleItem.sale_date)).all(),
                      columns=["outlet_id", "product_id", "d", "units"])
    if df.empty:
        return []
    df["d"] = pd.to_datetime(df["d"])
    full = pd.date_range(start, as_of, freq="D")
    rates = {}
    for (o, p), g in df.groupby(["outlet_id", "product_id"]):
        s = g.set_index("d")["units"].reindex(full, fill_value=0.0)
        recent, prior = s.iloc[-14:].mean(), s.iloc[:14].mean()
        trend = min(max(recent / prior, 0.7), 1.4) if prior > 0 else 1.0
        rates[(o, p)] = float(s.mean() * (0.5 + 0.5 * trend))
    incoming = {}
    for o, p, qty, exp in db.execute(select(
            PurchaseOrder.outlet_id, PurchaseOrderItem.product_id,
            PurchaseOrderItem.quantity - func.coalesce(PurchaseOrderItem.received_quantity, 0),
            PurchaseOrder.expected_date).join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id).where(
            PurchaseOrder.status.in_(OPEN_PO_STATUSES))):
        if qty > 0:
            incoming.setdefault((o, p), []).append((exp, float(qty)))
    inv_q = select(InventoryItem, Product, Outlet).join(Product, Product.id == InventoryItem.product_id).join(
        Outlet, Outlet.id == InventoryItem.outlet_id).where(Product.is_active.is_(True), Outlet.is_active.is_(True))
    if outlet_ids:
        inv_q = inv_q.where(InventoryItem.outlet_id.in_(outlet_ids))
    today = clock.today()
    out = []
    for inv, p, o in db.execute(inv_q).all():
        rate = rates.get((o.id, p.id), 0.0)
        if rate <= 0.05:
            continue
        stock, run_out = inv.quantity, None
        arrivals = sorted(incoming.get((o.id, p.id), []), key=lambda x: x[0] or today)
        for k in range(1, days + 1):
            day = today + timedelta(days=k - 1)
            stock += sum(q for exp, q in arrivals if exp and exp == day)
            stock -= rate
            if stock < 0:
                run_out = day
                break
        if run_out is None:
            continue
        out.append({"outlet_id": o.id, "outlet": o.name, "product_id": p.id, "product": p.name, "sku": p.sku,
                    "unit": p.unit, "current_stock": inv.quantity, "avg_daily_demand": round(rate, 2),
                    "on_order": round(sum(q for _, q in arrivals), 1), "runs_out_on": run_out.isoformat(),
                    "days_left": (run_out - today).days, "lost_revenue_estimate": round(
                        rate * max(0, days - (run_out - today).days) * p.selling_price, 2)})
    out.sort(key=lambda r: (r["days_left"], -r["lost_revenue_estimate"]))
    return out
