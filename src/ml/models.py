"""
Enterprise Retail Intelligence System v3.0
ML MODELS MODULE

Wrapper classes for baseline and advanced forecasting models.
Provides unified interface for training, prediction, and evaluation.

Author: R-DIOS Team
Version: 3.0.0
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from typing import Dict, List, Optional, Tuple
import joblib
from pathlib import Path


class BaselineModel:
    """
    Wrapper for baseline regression models (RandomForest, Gradient Boosting).
    
    Provides consistent interface for training, prediction, and evaluation
    across different sklearn-compatible models.
    """
    
    def __init__(self, model_type: str = 'random_forest', **model_params):
        """
        Initialize baseline model.
        
        Args:
            model_type (str): One of 'random_forest', 'gradient_boosting'
            **model_params: Model-specific hyperparameters
        """
        self.model_type = model_type
        self.model_params = model_params
        self.model = None
        self.feature_names = None
        self.is_fitted = False
        
        # Initialize model
        if model_type == 'random_forest':
            default_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42,
                'n_jobs': -1
            }
            default_params.update(model_params)
            self.model = RandomForestRegressor(**default_params)
            
        elif model_type == 'gradient_boosting':
            default_params = {
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'random_state': 42
            }
            default_params.update(model_params)
            self.model = GradientBoostingRegressor(**default_params)
            
        else:
            raise ValueError(f"Unknown model_type: {model_type}")
        
        print(f"✅ Initialized {model_type} model")
        print(f"   Parameters: {self.model.get_params()}")
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> Dict:
        """
        Train the model on training data.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training targets
            X_val (pd.DataFrame): Validation features (optional)
            y_val (pd.Series): Validation targets (optional)
            
        Returns:
            Dict: Training metrics
        """
        print(f"\n🎯 Training {self.model_type}...")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Features: {len(X_train.columns)}")
        
        # Store feature names
        self.feature_names = list(X_train.columns)
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        # Training metrics
        train_preds = self.model.predict(X_train)
        train_rmse = np.sqrt(mean_squared_error(y_train, train_preds))
        train_mae = mean_absolute_error(y_train, train_preds)
        
        metrics = {
            'train_rmse': train_rmse,
            'train_mae': train_mae
        }
        
        print(f"   ✅ Training RMSE: {train_rmse:.4f}")
        print(f"   ✅ Training MAE: {train_mae:.4f}")
        
        # Validation metrics (if provided)
        if X_val is not None and y_val is not None:
            val_preds = self.model.predict(X_val)
            val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
            val_mae = mean_absolute_error(y_val, val_preds)
            
            metrics['val_rmse'] = val_rmse
            metrics['val_mae'] = val_mae
            
            print(f"   ✅ Validation RMSE: {val_rmse:.4f}")
            print(f"   ✅ Validation MAE: {val_mae:.4f}")
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X (pd.DataFrame): Features for prediction
            
        Returns:
            np.ndarray: Predictions
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")
        
        # Ensure features match training
        if self.feature_names is not None:
            missing_features = set(self.feature_names) - set(X.columns)
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")
            
            X = X[self.feature_names]  # Reorder to match training
        
        return self.model.predict(X)
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get feature importance scores.
        
        Args:
            top_n (int): Number of top features to return
            
        Returns:
            pd.DataFrame: Feature importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")
        
        if not hasattr(self.model, 'feature_importances_'):
            raise ValueError("Model does not support feature importance")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)
        
        return importance_df
    
    def save(self, path: str):
        """
        Save model to disk.
        
        Args:
            path (str): File path for saving
        """
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'is_fitted': self.is_fitted
        }
        
        joblib.dump(model_data, path)
        print(f"✅ Model saved to: {path}")
    
    @classmethod
    def load(cls, path: str) -> 'BaselineModel':
        """
        Load model from disk.
        
        Args:
            path (str): File path to load from
            
        Returns:
            BaselineModel: Loaded model instance
        """
        model_data = joblib.load(path)
        
        instance = cls(model_type=model_data['model_type'])
        instance.model = model_data['model']
        instance.feature_names = model_data['feature_names']
        instance.is_fitted = model_data['is_fitted']
        
        print(f"✅ Model loaded from: {path}")
        return instance


# ============================================================================
# EVALUATION METRICS
# ============================================================================

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate comprehensive evaluation metrics.
    
    Args:
        y_true (np.ndarray): True values
        y_pred (np.ndarray): Predicted values
        
    Returns:
        Dict: Dictionary of metrics
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    # MAPE (Mean Absolute Percentage Error)
    # Avoid division by zero
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    # R² Score
    from sklearn.metrics import r2_score
    r2 = r2_score(y_true, y_pred)
    
    return {
        'RMSE': rmse,
        'MAE': mae,
        'MAPE': mape,
        'R2': r2
    }


def print_metrics(metrics: Dict[str, float], dataset_name: str = "Test"):
    """
    Print metrics in formatted table.
    
    Args:
        metrics (Dict): Metrics dictionary
        dataset_name (str): Name of dataset being evaluated
    """
    print(f"\n{'='*60}")
    print(f"{dataset_name} Set Metrics")
    print(f"{'='*60}")
    
    for metric_name, value in metrics.items():
        if metric_name in ['MAPE', 'R2']:
            print(f"  {metric_name:10s}: {value:8.2f}%")
        else:
            print(f"  {metric_name:10s}: {value:8.4f}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("R-DIOS ML Models Module v3.0")
    print("Available Models:")
    print("  1. BaselineModel (random_forest)")
    print("  2. BaselineModel (gradient_boosting)")
    print("\nReady for training pipeline integration")
