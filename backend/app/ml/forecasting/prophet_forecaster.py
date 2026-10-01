"""Prophet demand forecaster with real predictions and measured metrics."""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class ProphetForecaster:
    def __init__(
        self,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        holidays_df: Optional[pd.DataFrame] = None,
        include_holidays: bool = True,
        country_code: str = "IN",
        **_kwargs,
    ):
        try:
            from prophet import Prophet
        except ImportError as exc:
            raise RuntimeError("Prophet is required for ensemble forecasting") from exc

        self._prophet_class = Prophet
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.holidays_df = holidays_df
        self.include_holidays = include_holidays
        self.country_code = country_code
        self.model = None
        self.training_data: Optional[pd.DataFrame] = None
        self.active_regressors: List[str] = []

    def _holidays(self) -> Optional[pd.DataFrame]:
        if not self.include_holidays:
            return None
        if self.holidays_df is not None:
            return self.holidays_df
        try:
            import holidays

            calendar = holidays.country_holidays(self.country_code, years=range(2020, 2031))
            return pd.DataFrame(
                [
                    {"holiday": name, "ds": pd.Timestamp(day), "lower_window": -1, "upper_window": 1}
                    for day, name in calendar.items()
                ]
            )
        except Exception:
            return None

    def prepare_data(
        self,
        frame: pd.DataFrame,
        date_column: str = "date",
        target_column: str = "revenue",
        regressors: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        if date_column not in frame or target_column not in frame:
            raise ValueError(f"Forecast data requires '{date_column}' and '{target_column}' columns")
        prepared = pd.DataFrame(
            {
                "ds": pd.to_datetime(frame[date_column]),
                "y": pd.to_numeric(frame[target_column], errors="coerce"),
            }
        ).dropna()
        prepared = prepared.groupby("ds", as_index=False)["y"].sum().sort_values("ds")
        if len(prepared) < 30:
            raise ValueError("At least 30 daily observations are required for forecasting")
        self.active_regressors = []
        for regressor in regressors or []:
            if regressor in frame:
                prepared[regressor] = pd.to_numeric(frame[regressor], errors="coerce").fillna(0)
                self.active_regressors.append(regressor)
        self.training_data = prepared
        return prepared

    def fit(self, frame: pd.DataFrame, regressors: Optional[List[str]] = None) -> "ProphetForecaster":
        yearly_seasonality = self.yearly_seasonality and len(frame) >= 730
        self.model = self._prophet_class(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            holidays=self._holidays(),
        )
        self.model.add_seasonality(name="monthly", period=30.5, fourier_order=5)
        for regressor in regressors or []:
            if regressor in frame:
                self.model.add_regressor(regressor)
        self.model.fit(frame)
        return self

    def train(self, frame: pd.DataFrame, **_kwargs) -> str:
        date_column = "date" if "date" in frame else "ds"
        target_column = "sales" if "sales" in frame else "y"
        prepared = self.prepare_data(frame, date_column, target_column)
        self.fit(prepared)
        return "Model trained successfully"

    def predict(self, periods: int = 30, include_history: bool = True, **_kwargs) -> pd.DataFrame:
        if self.model is None:
            raise RuntimeError("Prophet model has not been trained")
        future = self.model.make_future_dataframe(periods=periods, freq="D", include_history=include_history)
        forecast = self.model.predict(future)
        forecast["date"] = forecast["ds"]
        return forecast

    def evaluate(self, frame: pd.DataFrame, **_kwargs) -> Dict[str, float]:
        if self.model is None:
            raise RuntimeError("Prophet model has not been trained")
        date_column = "date" if "date" in frame else "ds"
        target_column = "sales" if "sales" in frame else "y"
        test = pd.DataFrame(
            {
                "ds": pd.to_datetime(frame[date_column]),
                "y": pd.to_numeric(frame[target_column], errors="coerce"),
            }
        ).dropna()
        prediction = self.model.predict(test[["ds"]])
        actual = test["y"].to_numpy(dtype=float)
        predicted = prediction["yhat"].to_numpy(dtype=float)
        mae = float(np.mean(np.abs(actual - predicted)))
        rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
        nonzero = actual != 0
        mape = (
            float(np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])) * 100)
            if nonzero.any()
            else 0.0
        )
        direction = float(np.mean((np.diff(actual) >= 0) == (np.diff(predicted) >= 0))) if len(actual) > 1 else 1.0
        return {"mape": mape, "rmse": rmse, "mae": mae, "direction_accuracy": direction, "samples": len(actual)}
