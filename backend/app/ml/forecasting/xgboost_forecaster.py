# Heavy ML libraries (sklearn, xgboost) are lazy-loaded inside methods to save startup RAM.
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np


class XGBoostForecaster:
    """XGBoost-based forecasting for retail sales time series."""

    def __init__(self):
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.product_id: Optional[str] = None

    @staticmethod
    def create_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create lag, rolling window, date and cyclical features."""
        data = df.copy().sort_values("ds")
        data["ds"] = pd.to_datetime(data["ds"])
        data["y"] = pd.to_numeric(data["y"], errors="coerce").fillna(0)

        data["day_of_week"] = data["ds"].dt.dayofweek
        data["month"] = data["ds"].dt.month
        data["quarter"] = data["ds"].dt.quarter
        data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)

        try:
            import holidays

            years = sorted(data["ds"].dt.year.unique().tolist())
            indian_holidays = holidays.country_holidays("IN", years=years)
            data["is_holiday"] = data["ds"].dt.date.isin(indian_holidays).astype(int)
        except Exception:
            data["is_holiday"] = 0

        # Lag features
        for lag in [1, 7, 14, 30]:
            data[f"lag_{lag}"] = data["y"].shift(lag)

        # Rolling features
        for window in [7, 14, 30]:
            data[f"roll_mean_{window}"] = data["y"].shift(1).rolling(window=window, min_periods=1).mean()
            data[f"roll_std_{window}"] = data["y"].shift(1).rolling(window=window, min_periods=1).std().fillna(0)
            data[f"roll_min_{window}"] = data["y"].shift(1).rolling(window=window, min_periods=1).min().fillna(0)
            data[f"roll_max_{window}"] = data["y"].shift(1).rolling(window=window, min_periods=1).max().fillna(0)

        # Cyclical features
        data["dow_sin"] = np.sin(2 * np.pi * data["day_of_week"] / 7)
        data["dow_cos"] = np.cos(2 * np.pi * data["day_of_week"] / 7)
        data["month_sin"] = np.sin(2 * np.pi * (data["month"] - 1) / 12)
        data["month_cos"] = np.cos(2 * np.pi * (data["month"] - 1) / 12)

        data = data.dropna().reset_index(drop=True)

        return data

    def train(
        self, X: pd.DataFrame, y: pd.Series, product_id: str = "default", params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Train XGBoost regression model."""
        self.product_id = product_id

        X = X.copy()
        y = y.copy()

        from sklearn.preprocessing import StandardScaler

        self.feature_names = list(X.columns)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        params = params or {
            "objective": "reg:squarederror",
            "learning_rate": 0.1,
            "max_depth": 6,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "tree_method": "auto",
        }

        import xgboost as xgb

        self.model = xgb.XGBRegressor(**params)
        self.model.fit(X_scaled, y)

        return {
            "status": "success",
            "product_id": product_id,
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict using trained XGBoost model."""
        if self.model is None or self.scaler is None:
            raise ValueError("Model is not trained. Call train() first.")

        X = X.copy()
        if hasattr(self, "feature_names") and self.feature_names:
            # Reorder columns to match train phase
            X = X[self.feature_names]

        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        preds = np.clip(preds, 0, None)
        return preds

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate model with RMSE, MAE, MAPE."""
        preds = self.predict(X_test)
        from sklearn.metrics import mean_squared_error, mean_absolute_error

        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae = mean_absolute_error(y_test, preds)

        mask = y_test != 0
        mape = np.mean(np.abs((y_test[mask] - preds[mask]) / y_test[mask])) * 100 if mask.sum() > 0 else 0.0

        return {
            "rmse": float(rmse),
            "mae": float(mae),
            "mape": float(mape),
            "n": len(y_test),
        }

    def forecast(self, history: pd.DataFrame, periods: int) -> np.ndarray:
        """Generate recursive forecasts so each future lag uses earlier predictions."""
        if periods < 1:
            return np.array([], dtype=float)
        working = history[["ds", "y"]].copy().sort_values("ds").reset_index(drop=True)
        predictions = []
        for _ in range(periods):
            next_date = working["ds"].max() + pd.Timedelta(days=1)
            candidate = pd.concat(
                [working, pd.DataFrame({"ds": [next_date], "y": [0.0]})],
                ignore_index=True,
            )
            features = self.create_features(candidate)
            if features.empty or features.iloc[-1]["ds"] != next_date:
                raise ValueError("At least 31 daily observations are required for XGBoost forecasting")
            next_x = features.tail(1).drop(columns=["ds", "y"])
            prediction = float(self.predict(next_x)[0])
            working = pd.concat(
                [working, pd.DataFrame({"ds": [next_date], "y": [prediction]})],
                ignore_index=True,
            )
            predictions.append(prediction)
        return np.asarray(predictions)
