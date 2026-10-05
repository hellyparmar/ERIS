"""Every forecasting model runs in the installed environment.

The engine falls back to the remaining models when one fails, so a missing dependency would otherwise only show
up as a warning in the server log (this is how a missing scikit-learn once disabled XGBoost unnoticed)."""
import numpy as np
import pandas as pd
import pytest

from app.services import forecasting as F

EXPECTED = ["seasonal_naive", "holt_winters", "xgboost", "prophet"]


def _series(days: int = 200) -> pd.Series:
    rng = np.random.default_rng(0)
    t = np.arange(days)
    values = 1000 + 200 * np.sin(t * 2 * np.pi / 7) + rng.normal(0, 40, days)
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=days, freq="D"))


def test_all_models_are_installed():
    assert F.available_models() == EXPECTED


@pytest.mark.parametrize("name", EXPECTED)
def test_model_produces_a_forecast(name):
    pred = F.MODEL_FUNCS[name](_series(), 14)
    assert len(pred) == 14 and np.isfinite(pred).all() and (pred >= 0).all()
    assert 600 < float(np.mean(pred)) < 1400  # sensible level for a series around 1,000 a day


def test_auto_selection_uses_every_candidate():
    result = F.run_forecast(_series(), 14, "auto")
    evaluated = {e["model"] for e in result["evaluation"] if e.get("wape") is not None}
    assert set(EXPECTED) <= evaluated, result["evaluation"]


def test_saved_forecast_is_reused_without_refitting(client):
    from app.db import SessionLocal

    with SessionLocal() as db:
        spec = F.build_spec(db, "outlet", 2, None)
        fresh = F.forecast_series(db, spec, horizon=30, persist=False)
        assert not fresh.get("reused")
    F.clear_cache()
    with SessionLocal() as db:  # a later request (its own session) is served from the saved 30-day result
        week = F.forecast_series(db, spec, horizon=7, persist=False)
    assert week.get("reused") and week["model"] == fresh["model"]
    assert [f["yhat"] for f in week["forecast"]] == [f["yhat"] for f in fresh["forecast"][:7]]
    assert [f["date"] for f in week["forecast"]] == [f["date"] for f in fresh["forecast"][:7]]
    assert week["backtest"] == fresh["backtest"] and week["evaluation"] == fresh["evaluation"]


def test_forecast_page_records_a_reused_run_in_the_history(client, admin):
    from app.db import SessionLocal

    with SessionLocal() as db:  # a hidden pre-computed run, as the Docker build stores them
        F.forecast_series(db, F.build_spec(db, "outlet", 3, None), horizon=30, persist=False)
    r = client.get("/api/forecast?scope=outlet&target_id=3&horizon=14&model=auto", headers=admin).json()
    assert r["reused"] and r["run_id"]
    runs = client.get("/api/forecast/runs", headers=admin).json()["items"]
    assert r["run_id"] in [run["id"] for run in runs]
