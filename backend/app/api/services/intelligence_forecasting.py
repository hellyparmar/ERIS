"""
Phase 5 — Intelligence: ARIMA Sales Forecasting Service
Provides 30-day revenue forecasts with confidence bands from historical sales data.

Design decisions:
- Uses statsmodels ARIMA with auto-fallback for insufficient data
- For < 14 days of history: returns simple moving average trend instead of crashing
- For < 30 days: uses simpler ARIMA(1,1,0) instead of auto_arima
- Handles missing days by forward-filling with 0 revenue
- Returns ISO datetime strings for JSON serialization safety
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

MIN_DAYS_FOR_ARIMA = 14          # Minimum history to run full ARIMA
MIN_DAYS_FOR_SIMPLE_ARIMA = 7   # Minimum to run any model at all
FORECAST_HORIZON = 30            # Default forecast days
FALLBACK_CONFIDENCE_PCT = 0.20  # ±20% bands for trend fallback


# ── Data Fetching ─────────────────────────────────────────────────────────────

def fetch_daily_revenue(
    db: Session,
    store_id: Optional[int] = None,
    lookback_days: int = 180,
) -> pd.Series:
    """
    Fetch daily total revenue from the sales table.
    Returns a Pandas Series indexed by date, sorted ascending.
    Missing dates are filled with 0.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)

    store_filter = "AND store_id = :store_id" if store_id else ""
    query = text(f"""
        SELECT
            DATE(COALESCE(transaction_date, created_at)) AS sale_date,
            SUM(total_amount) AS daily_revenue
        FROM sales
        WHERE COALESCE(transaction_date, created_at) >= :start_date
          AND COALESCE(transaction_date, created_at) <= :end_date
          {store_filter}
        GROUP BY sale_date
        ORDER BY sale_date ASC
    """)

    params: Dict[str, Any] = {"start_date": str(start_date), "end_date": str(end_date)}
    if store_id:
        params["store_id"] = store_id

    rows = db.execute(query, params).fetchall()

    if not rows:
        logger.warning("No sales data found for forecasting")
        return pd.Series(dtype=float)

    # Build a full date range and fill missing days with 0
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    series_raw = pd.Series(
        {row[0]: float(row[1]) for row in rows}
    )
    series_raw.index = pd.to_datetime(series_raw.index)
    series = series_raw.reindex(dates, fill_value=0.0)

    return series


# ── Forecasting Logic ─────────────────────────────────────────────────────────

def _simple_trend_forecast(series: pd.Series, horizon: int) -> Dict[str, Any]:
    """
    Fallback linear trend forecast for < MIN_DAYS_FOR_ARIMA days.
    Uses the rolling mean of all available data for prediction.
    Returns confidence bands at ±FALLBACK_CONFIDENCE_PCT.
    """
    logger.info(f"Using simple trend forecast ({len(series)} days history)")
    avg = float(series.mean())
    last_date = series.index[-1] if len(series) > 0 else pd.Timestamp.today()

    # Apply a mild linear trend from slope of available data
    x = np.arange(len(series))
    coeffs = np.polyfit(x, series.values, 1)
    slope, intercept = float(coeffs[0]), float(coeffs[1])

    forecast_dates = [last_date + timedelta(days=i + 1) for i in range(horizon)]
    forecast_vals, upper_vals, lower_vals = [], [], []

    for i, dt in enumerate(forecast_dates):
        predicted = max(0.0, slope * (len(series) + i) + intercept)
        band = predicted * FALLBACK_CONFIDENCE_PCT
        forecast_vals.append(round(predicted, 2))
        upper_vals.append(round(predicted + band, 2))
        lower_vals.append(round(max(0.0, predicted - band), 2))

    return {
        "model": "linear_trend_fallback",
        "history_days": len(series),
        "mean_daily_revenue": round(avg, 2),
        "forecast": {
            "dates": [dt.strftime("%Y-%m-%d") for dt in forecast_dates],
            "predicted": forecast_vals,
            "upper_bound": upper_vals,
            "lower_bound": lower_vals,
        },
        "accuracy_note": "Insufficient history for ARIMA — using linear trend extrapolation.",
    }


def _arima_forecast(series: pd.Series, horizon: int, auto: bool) -> Dict[str, Any]:
    """
    ARIMA forecast using statsmodels.
    If auto=True uses pmdarima.auto_arima to find best (p,d,q).
    If auto=False uses a conservative ARIMA(1,1,1) for speed.
    """
    from statsmodels.tsa.arima.model import ARIMA

    # Smooth out zero-inflation with a tiny floor to help ARIMA converge
    ts = series.copy().clip(lower=0.01)

    if auto:
        try:
            import pmdarima as pm
            logger.info("Running auto_arima to select best ARIMA parameters…")
            auto_model = pm.auto_arima(
                ts,
                seasonal=True,
                m=7,          # Weekly seasonality
                max_p=3, max_q=3, max_d=2,
                stepwise=True,
                suppress_warnings=True,
                error_action="ignore",
                information_criterion="aic",
                with_intercept=True,
            )
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order
            logger.info(f"auto_arima selected order={order}, seasonal_order={seasonal_order}")
        except Exception as e:
            logger.warning(f"auto_arima failed ({e}), falling back to ARIMA(1,1,1)")
            order = (1, 1, 1)
            seasonal_order = (0, 0, 0, 0)
    else:
        order = (1, 1, 1)
        seasonal_order = (0, 0, 0, 0)

    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        if any(s != 0 for s in seasonal_order[:3]):
            model = SARIMAX(ts, order=order, seasonal_order=seasonal_order,
                            enforce_stationarity=False, enforce_invertibility=False)
        else:
            model = ARIMA(ts, order=order)

        fit = model.fit(disp=False)
        forecast_res = fit.get_forecast(steps=horizon)
        pred_mean = forecast_res.predicted_mean
        conf_int = forecast_res.conf_int(alpha=0.20)  # 80% confidence interval

    except Exception as e:
        logger.error(f"ARIMA model fit/forecast failed: {e}", exc_info=True)
        raise RuntimeError(f"ARIMA fit failed: {e}")

    last_date = series.index[-1]
    forecast_dates = [last_date + timedelta(days=i + 1) for i in range(horizon)]

    predicted = [round(max(0.0, float(v)), 2) for v in pred_mean]
    lower = [round(max(0.0, float(conf_int.iloc[i, 0])), 2) for i in range(horizon)]
    upper = [round(max(0.0, float(conf_int.iloc[i, 1])), 2) for i in range(horizon)]

    # Summary stats
    hist_avg = round(float(series.tail(30).mean()), 2)
    forecast_avg = round(float(np.mean(predicted)), 2)
    trend_pct = round(((forecast_avg - hist_avg) / max(hist_avg, 1)) * 100, 1)

    return {
        "model": f"ARIMA{order}" if not any(s != 0 for s in seasonal_order[:3]) else f"SARIMA{order}x{seasonal_order}",
        "history_days": len(series),
        "mean_daily_revenue": hist_avg,
        "forecast_avg_daily": forecast_avg,
        "trend_vs_last30d_pct": trend_pct,
        "forecast": {
            "dates": [dt.strftime("%Y-%m-%d") for dt in forecast_dates],
            "predicted": predicted,
            "upper_bound": upper,
            "lower_bound": lower,
        },
    }


# ── Main Entry Point ──────────────────────────────────────────────────────────

def generate_sales_forecast(
    db: Session,
    store_id: Optional[int] = None,
    horizon: int = FORECAST_HORIZON,
    lookback_days: int = 180,
    use_auto_arima: bool = True,
) -> Dict[str, Any]:
    """
    Generate a sales revenue forecast for the next `horizon` days.

    Edge cases handled:
    - 0 days of data  → raises ValueError with a user-friendly message
    - 1–6 days        → raises ValueError asking for more data
    - 7–13 days       → simple linear trend fallback (no ARIMA)
    - 14+ days        → ARIMA with optional auto parameter selection

    Returns a dict with:
    - model: model type used
    - history_days: number of days of training data
    - forecast.dates: list of ISO date strings (YYYY-MM-DD)
    - forecast.predicted: list of predicted revenue values
    - forecast.upper_bound / lower_bound: 80% confidence interval
    """
    series = fetch_daily_revenue(db, store_id=store_id, lookback_days=lookback_days)

    if len(series) == 0:
        raise ValueError(
            "No sales data found. Cannot generate forecast. "
            "Complete at least one sale to enable forecasting."
        )

    # Drop leading zero days to get effective history
    non_zero_count = int((series > 0).sum())
    if non_zero_count < MIN_DAYS_FOR_SIMPLE_ARIMA:
        raise ValueError(
            f"Only {non_zero_count} days with sales found. "
            f"Need at least {MIN_DAYS_FOR_SIMPLE_ARIMA} days to forecast. "
            "Keep selling and try again!"
        )

    # Choose model complexity based on available data
    if len(series) < MIN_DAYS_FOR_ARIMA:
        result = _simple_trend_forecast(series, horizon)
    else:
        try:
            result = _arima_forecast(series, horizon, auto=use_auto_arima)
        except RuntimeError as e:
            logger.warning(f"ARIMA failed, falling back to trend: {e}")
            result = _simple_trend_forecast(series, horizon)

    # Add historical data summary for chart context
    result["historical_summary"] = {
        "start_date": series.index[0].strftime("%Y-%m-%d"),
        "end_date": series.index[-1].strftime("%Y-%m-%d"),
        "total_revenue": round(float(series.sum()), 2),
        "peak_day": {
            "date": series.idxmax().strftime("%Y-%m-%d"),
            "revenue": round(float(series.max()), 2),
        },
        "days_with_sales": non_zero_count,
    }
    result["generated_at"] = datetime.utcnow().isoformat() + "Z"
    result["horizon_days"] = horizon
    result["store_id"] = store_id

    return result
