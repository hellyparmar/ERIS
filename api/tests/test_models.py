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
