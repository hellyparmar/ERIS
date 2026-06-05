import os
import pickle
from typing import Optional, Dict, Any
from datetime import timedelta, datetime

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except ImportError:
    xgb = None


class XGBoostForecaster:
    """XGBoost-based forecasting for retail sales time series."""

    def __init__(self, model_dir: str = "models"):
        if xgb is None:
            raise ImportError("xgboost is not installed. Install with: pip install xgboost")

        self.model: Optional[xgb.XGBRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.model_dir = model_dir
        self.product_id: Optional[str] = None
        os.makedirs(model_dir, exist_ok=True)

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

        # Holiday indicator placeholder; user should inject from external holiday table
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

    def train(self, X: pd.DataFrame, y: pd.Series, product_id: str = "default", params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Train XGBoost regression model."""
        self.product_id = product_id

        X = X.copy()
        y = y.copy()

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

        self.model = xgb.XGBRegressor(**params)
        self.model.fit(X_scaled, y)

        model_path = os.path.join(self.model_dir, f"xgb_{product_id}.pkl")
        with open(model_path, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

        return {
            "status": "success",
            "product_id": product_id,
            "model_path": model_path,
            "trained_at": datetime.utcnow().isoformat(),
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict using trained XGBoost model."""
        if self.model is None or self.scaler is None:
            raise ValueError("Model is not trained. Call train() first.")

        X_scaled = self.scaler.transform(X)
        preds = self.model.predict(X_scaled)
        preds = np.clip(preds, 0, None)
        return preds

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate model with RMSE, MAE, MAPE."""
        preds = self.predict(X_test)

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

    def load(self, product_id: str) -> None:
        """Load model from disk."""
        model_path = os.path.join(self.model_dir, f"xgb_{product_id}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        with open(model_path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.product_id = product_id

