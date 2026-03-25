"""
P5-T1: Sales Forecasting Service — ARIMA Engine
================================================
Data source  : invoices.total_amount (aggregated by DATE(invoice_date))
               Falls back to sales.total_amount when invoices < 14 days
Model        : ARIMA(7,1,1) — weekly lag, one differencing, one MA term
Fallback     : Naive flat-line average when history < 14 days (NO 500 errors)
Response     : { dates, historical, forecast, lower_band, upper_band }

Usage:
    from app.api.services.forecasting import build_forecast
    result = build_forecast(db, store_id=None, horizon=30)
"""

from __future__ import annotations

import logging
import warnings
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

warnings.filterwarnings("ignore")          # suppress statsmodels convergence noise
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

MIN_DAYS_FOR_ARIMA = 14          # Strict minimum before ARIMA is attempted
ARIMA_ORDER       = (7, 1, 1)   # (p, d, q) — weekly seasonality
FORECAST_HORIZON  = 30           # default forecast days
LOOKBACK_DAYS     = 180          # how far back to pull history


# ── Step 1: Data Extraction via SQLAlchemy ────────────────────────────────────

def _fetch_invoice_series(
    db: Session,
    store_id: Optional[int],
    lookback_days: int,
) -> pd.Series:
    """
    Query invoices.total_amount grouped by DATE(invoice_date).
    Falls back to sales.total_amount if invoices table has < 14 days of data.
    Returns a Pandas Series indexed by date, resampled to daily 'D' frequency,
    with missing days filled with 0.0.
    """
    start = date.today() - timedelta(days=lookback_days)
    end   = date.today()

    store_clause = "AND store_id = :store_id" if store_id else ""

    # ── Primary: invoices table ────────────────────────────────────────────
    inv_query = text(f"""
        SELECT
            DATE(COALESCE(invoice_date, created_at))  AS sale_date,
            SUM(total_amount)                          AS daily_revenue
        FROM invoices
        WHERE COALESCE(invoice_date, created_at) BETWEEN :start AND :end
          {store_clause}
        GROUP BY sale_date
        ORDER BY sale_date
    """)
    params: Dict[str, Any] = {"start": str(start), "end": str(end)}
    if store_id:
        params["store_id"] = store_id

    rows = db.execute(inv_query, params).fetchall()
    invoice_days = len([r for r in rows if float(r[1] or 0) > 0])

    # ── Fallback: sales table (more populated) ─────────────────────────────
    if invoice_days < MIN_DAYS_FOR_ARIMA:
        logger.info(
            f"Invoices only has {invoice_days} active days — "
            "merging with sales table for better ARIMA performance."
        )
        sales_query = text(f"""
            SELECT
                DATE(COALESCE(transaction_date, created_at)) AS sale_date,
                SUM(total_amount)                             AS daily_revenue
            FROM sales
            WHERE COALESCE(transaction_date, created_at) BETWEEN :start AND :end
              {store_clause}
            GROUP BY sale_date
            ORDER BY sale_date
        """)
        sales_rows = db.execute(sales_query, params).fetchall()

        # Merge both datasets by date, summing revenue
        combined: Dict[Any, float] = {}
        for row in rows:
            combined[row[0]] = float(row[1] or 0)
        for row in sales_rows:
            d_key = row[0]
            combined[d_key] = combined.get(d_key, 0.0) + float(row[1] or 0)

        if not combined:
            return pd.Series(dtype=float)

        raw = pd.Series(combined)
        raw.index = pd.to_datetime(raw.index)
    else:
        if not rows:
            return pd.Series(dtype=float)
        raw = pd.Series({r[0]: float(r[1] or 0) for r in rows})
        raw.index = pd.to_datetime(raw.index)

    # Reindex to a continuous daily range, fill missing days with 0.0
    full_index = pd.date_range(start=pd.Timestamp(start), end=pd.Timestamp(end), freq="D")
    series = raw.reindex(full_index, fill_value=0.0)
    return series


# ── Step 2a: Naive Forecast (< 14 days fallback) ──────────────────────────────

def _naive_forecast(series: pd.Series, horizon: int) -> Dict[str, Any]:
    """
    Flat-line naive forecast = rolling mean of available data.
    Returns ±std as confidence bands. Never crashes.
    """
    logger.warning(
        f"Naive forecast triggered — only {len(series)} days of data "
        f"(need {MIN_DAYS_FOR_ARIMA})."
    )
    mean_rev = float(series[series > 0].mean()) if (series > 0).any() else 0.0
    std_rev  = float(series[series > 0].std())  if (series > 0).any() else mean_rev * 0.15
    if np.isnan(std_rev):
        std_rev = mean_rev * 0.15

    last_date      = series.index[-1] if len(series) > 0 else pd.Timestamp.today()
    forecast_dates = [last_date + timedelta(days=i + 1) for i in range(horizon)]

    predicted  = [round(mean_rev, 2)]             * horizon
    lower_band = [round(max(0.0, mean_rev - std_rev), 2)] * horizon
    upper_band = [round(mean_rev + std_rev, 2)]    * horizon

    return {
        "model":            "naive_average",
        "warning":          f"Insufficient data ({(series > 0).sum()} active days). "
                            f"Need {MIN_DAYS_FOR_ARIMA}+ days for ARIMA. Showing average-based flat forecast.",
        "history_days":     int((series > 0).sum()),
        "forecast_dates":   [d.strftime("%Y-%m-%d") for d in forecast_dates],
        "forecast_values":  predicted,
        "lower_band":       lower_band,
        "upper_band":       upper_band,
    }


# ── Step 2b: ARIMA(7,1,1) Forecast ───────────────────────────────────────────

def _arima_forecast(series: pd.Series, horizon: int) -> Dict[str, Any]:
    """
    Fit ARIMA(7,1,1) on the daily revenue series and produce a 30-day forecast
    with 95% confidence intervals.
    """
    from statsmodels.tsa.arima.model import ARIMA as StatsARIMA

    # Clip negative/zero to a tiny floor so ARIMA log-transforms stay stable
    ts = series.copy().clip(lower=0.01)

    logger.info(f"Fitting ARIMA{ARIMA_ORDER} on {len(ts)} days of data…")
    model = StatsARIMA(ts, order=ARIMA_ORDER, trend="n")
    fit   = model.fit(method_kwargs={"warn_convergence": False, "disp": False})

    fc_res    = fit.get_forecast(steps=horizon)
    fc_mean   = fc_res.predicted_mean
    conf_int  = fc_res.conf_int(alpha=0.05)   # 95% CI

    last_date      = series.index[-1]
    forecast_dates = [last_date + timedelta(days=i + 1) for i in range(horizon)]

    return {
        "model":            f"ARIMA{ARIMA_ORDER}",
        "warning":          None,
        "history_days":     len(series),
        "aic":              round(float(fit.aic), 2),
        "forecast_dates":   [d.strftime("%Y-%m-%d") for d in forecast_dates],
        "forecast_values":  [round(max(0.0, float(v)), 2) for v in fc_mean],
        "lower_band":       [round(max(0.0, float(conf_int.iloc[i, 0])), 2) for i in range(horizon)],
        "upper_band":       [round(max(0.0, float(conf_int.iloc[i, 1])), 2) for i in range(horizon)],
    }


# ── Step 3: Main Entry Point ──────────────────────────────────────────────────

def build_forecast(
    db: Session,
    store_id: Optional[int] = None,
    horizon: int = FORECAST_HORIZON,
    lookback_days: int = LOOKBACK_DAYS,
) -> Dict[str, Any]:
    """
    Build a sales revenue forecast.

    Returns a dict with the following guaranteed keys (never raises 500):
    {
      "dates"     : list[str]   — historical YYYY-MM-DD dates
      "historical": list[float] — daily revenue for each historical date
      "forecast"  : list[float] — predicted values for next `horizon` days
      "lower_band": list[float] — 95% CI lower bound
      "upper_band": list[float] — 95% CI upper bound
      "model"     : str         — "ARIMA(7,1,1)" or "naive_average"
      "warning"   : str | None  — set when naive fallback is used
      "meta"      : dict        — additional model metadata
    }
    """
    series = _fetch_invoice_series(db, store_id=store_id, lookback_days=lookback_days)

    # ── Historical arrays (dates + values) ────────────────────────────────
    hist_dates  = [d.strftime("%Y-%m-%d") for d in series.index]
    hist_values = [round(float(v), 2) for v in series.values]

    active_days = int((series > 0).sum())

    # ── Choose model ──────────────────────────────────────────────────────
    if active_days < MIN_DAYS_FOR_ARIMA:
        fc = _naive_forecast(series, horizon)
    else:
        try:
            fc = _arima_forecast(series, horizon)
        except Exception as e:
            logger.error(f"ARIMA fit failed ({e}) — falling back to naive forecast")
            fc = _naive_forecast(series, horizon)
            fc["warning"] = f"ARIMA failed ({e}). Using naive fallback."

    # ── Assemble final response ───────────────────────────────────────────
    return {
        "dates":      hist_dates,
        "historical": hist_values,
        "forecast":   fc["forecast_values"],
        "lower_band": fc["lower_band"],
        "upper_band": fc["upper_band"],
        "model":      fc["model"],
        "warning":    fc.get("warning"),
        "meta": {
            "forecast_dates":  fc["forecast_dates"],
            "history_days":    fc["history_days"],
            "active_sale_days":active_days,
            "aic":             fc.get("aic"),
            "horizon":         horizon,
            "store_id":        store_id,
            "generated_at":    datetime.utcnow().isoformat() + "Z",
        },
    }
