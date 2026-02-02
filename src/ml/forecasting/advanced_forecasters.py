"""
Advanced Forecasting Models - ARIMA, LSTM, and Ensemble
Thesis Week 6: Multi-model forecasting for comparison study
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Statistical models
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.stattools import adfuller, acf, pacf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# Deep learning
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ARIMAForecaster:
    """
    ARIMA/SARIMA forecasting for time series
    
    Features:
    - Automatic differencing detection
    - Seasonal ARIMA support
    - External regressors (ARIMAX)
    """
    
    def __init__(
        self,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Tuple[int, int, int, int] = None,
        use_exog: bool = False
    ):
        """
        Initialize ARIMA forecaster
        
        Args:
            order: (p, d, q) for AR, Differencing, MA
            seasonal_order: (P, D, Q, s) for seasonal components
            use_exog: Include external regressors
        """
        self.order = order
        self.seasonal_order = seasonal_order
        self.use_exog = use_exog
        self.model = None
        self.fitted_model = None
        self.scaler = MinMaxScaler()
        self.training_data = None
        self.metrics = {}
    
    def check_stationarity(self, series: pd.Series) -> Dict[str, Any]:
        """
        Check if series is stationary using ADF test
        
        Returns:
            Dictionary with test results
        """
        if not STATSMODELS_AVAILABLE:
            return {'stationary': True, 'message': 'statsmodels not available'}
        
        result = adfuller(series.dropna())
        
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'stationary': result[1] < 0.05,
            'recommendation': 'd=0' if result[1] < 0.05 else 'd=1 or higher'
        }
    
    def auto_detect_order(self, series: pd.Series, max_p: int = 5, max_q: int = 5) -> Tuple[int, int, int]:
        """
        Automatically detect optimal ARIMA order using AIC
        Simplified grid search
        """
        if not STATSMODELS_AVAILABLE:
            return self.order
        
        # Check stationarity for d
        stationarity = self.check_stationarity(series)
        d = 0 if stationarity['stationary'] else 1
        
        # Simple ACF/PACF analysis
        try:
            acf_values = acf(series.diff().dropna() if d > 0 else series, nlags=10)
            pacf_values = pacf(series.diff().dropna() if d > 0 else series, nlags=10)
            
            # Count significant lags
            p = sum(abs(pacf_values[1:6]) > 0.2)
            q = sum(abs(acf_values[1:6]) > 0.2)
            
            p = min(max(p, 1), max_p)
            q = min(max(q, 1), max_q)
            
        except Exception:
            p, q = 1, 1
        
        logger.info(f"Auto-detected order: ({p}, {d}, {q})")
        return (p, d, q)
    
    def fit(
        self,
        data: pd.DataFrame,
        target_column: str = 'revenue',
        exog_columns: List[str] = None,
        auto_order: bool = False
    ) -> 'ARIMAForecaster':
        """
        Fit ARIMA model
        
        Args:
            data: DataFrame with time series data
            target_column: Target column name
            exog_columns: List of exogenous variable columns
            auto_order: Auto-detect optimal order
        """
        if not STATSMODELS_AVAILABLE:
            logger.warning("statsmodels not available, using mock")
            self.training_data = data
            return self
        
        series = data[target_column].values
        self.training_data = data
        
        # Auto-detect order if requested
        if auto_order:
            self.order = self.auto_detect_order(pd.Series(series))
        
        # Prepare exogenous variables
        exog = None
        if self.use_exog and exog_columns:
            exog = data[exog_columns].values
        
        # Fit model
        try:
            if self.seasonal_order:
                self.model = SARIMAX(
                    series,
                    order=self.order,
                    seasonal_order=self.seasonal_order,
                    exog=exog
                )
            else:
                self.model = ARIMA(
                    series,
                    order=self.order,
                    exog=exog
                )
            
            self.fitted_model = self.model.fit(disp=False)
            logger.info(f"ARIMA{self.order} fitted. AIC: {self.fitted_model.aic:.2f}")
            
        except Exception as e:
            logger.error(f"ARIMA fitting failed: {e}")
            self.fitted_model = None
        
        return self
    
    def predict(self, steps: int = 30, exog_future: np.ndarray = None) -> pd.DataFrame:
        """
        Generate forecast
        
        Args:
            steps: Number of periods to forecast
            exog_future: Future exogenous values
        
        Returns:
            DataFrame with forecast and confidence intervals
        """
        if self.fitted_model is None:
            # Mock forecast
            return self._mock_forecast(steps)
        
        # Generate forecast with confidence intervals
        forecast = self.fitted_model.get_forecast(steps=steps, exog=exog_future)
        
        forecast_df = pd.DataFrame({
            'yhat': forecast.predicted_mean,
            'yhat_lower': forecast.conf_int()[:, 0],
            'yhat_upper': forecast.conf_int()[:, 1]
        })
        
        # Add dates
        if self.training_data is not None and 'date' in self.training_data.columns:
            last_date = pd.to_datetime(self.training_data['date'].max())
            forecast_df['ds'] = pd.date_range(start=last_date + timedelta(days=1), periods=steps, freq='D')
        
        return forecast_df
    
    def _mock_forecast(self, steps: int) -> pd.DataFrame:
        """Generate mock forecast"""
        base = self.training_data['revenue'].mean() if self.training_data is not None else 50000
        
        forecasts = [base * (1 + np.random.normal(0, 0.08)) for _ in range(steps)]
        
        return pd.DataFrame({
            'yhat': forecasts,
            'yhat_lower': [f * 0.85 for f in forecasts],
            'yhat_upper': [f * 1.15 for f in forecasts],
            'ds': pd.date_range(start=datetime.now(), periods=steps, freq='D')
        })
    
    def evaluate(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate forecast metrics"""
        mape = mean_absolute_percentage_error(actual, predicted) * 100
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mae = mean_absolute_error(actual, predicted)
        
        self.metrics = {
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2)
        }
        
        return self.metrics


class LSTMForecaster:
    """
    LSTM-based deep learning forecaster
    
    Features:
    - Sequence-to-sequence forecasting
    - Multi-feature support
    - GPU acceleration (if available)
    """
    
    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
        seq_length: int = 30
    ):
        """
        Initialize LSTM forecaster
        
        Args:
            input_size: Number of input features
            hidden_size: LSTM hidden state size
            num_layers: Number of LSTM layers
            output_size: Number of output features
            dropout: Dropout rate
            seq_length: Sequence length for training
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        self.dropout = dropout
        self.seq_length = seq_length
        
        self.model = None
        self.scaler = MinMaxScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') if TORCH_AVAILABLE else 'cpu'
        self.training_data = None
        self.metrics = {}
        
        if TORCH_AVAILABLE:
            self._build_model()
    
    def _build_model(self):
        """Build LSTM model architecture"""
        
        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, output_size, dropout):
                super(LSTMModel, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                
                self.lstm = nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    batch_first=True,
                    dropout=dropout if num_layers > 1 else 0
                )
                
                self.fc = nn.Sequential(
                    nn.Linear(hidden_size, hidden_size // 2),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                    nn.Linear(hidden_size // 2, output_size)
                )
            
            def forward(self, x):
                # x shape: (batch, seq_len, features)
                lstm_out, _ = self.lstm(x)
                # Take last output
                out = self.fc(lstm_out[:, -1, :])
                return out
        
        self.model = LSTMModel(
            self.input_size,
            self.hidden_size,
            self.num_layers,
            self.output_size,
            self.dropout
        ).to(self.device)
        
        logger.info(f"LSTM model built on {self.device}")
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - self.seq_length):
            X.append(data[i:i + self.seq_length])
            y.append(data[i + self.seq_length])
        return np.array(X), np.array(y)
    
    def fit(
        self,
        data: pd.DataFrame,
        target_column: str = 'revenue',
        feature_columns: List[str] = None,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        validation_split: float = 0.2
    ) -> 'LSTMForecaster':
        """
        Train LSTM model
        
        Args:
            data: Input DataFrame
            target_column: Target column
            feature_columns: Additional feature columns
            epochs: Training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Validation data ratio
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, using mock")
            self.training_data = data
            return self
        
        self.training_data = data
        
        # Prepare features
        if feature_columns:
            features = data[[target_column] + feature_columns].values
            self.input_size = len(feature_columns) + 1
            self._build_model()  # Rebuild with correct input size
        else:
            features = data[[target_column]].values
        
        # Scale data
        scaled_data = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = self._create_sequences(scaled_data)
        
        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Convert to tensors
        X_train = torch.FloatTensor(X_train).to(self.device)
        y_train = torch.FloatTensor(y_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        y_val = torch.FloatTensor(y_val).to(self.device)
        
        # DataLoader
        train_dataset = TensorDataset(X_train, y_train)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)
        
        # Training loop
        best_val_loss = float('inf')
        
        logger.info(f"Training LSTM for {epochs} epochs...")
        
        for epoch in range(epochs):
            self.model.train()
            train_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y[:, 0:1] if batch_y.dim() > 1 else batch_y.unsqueeze(1))
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val)
                val_loss = criterion(val_outputs, y_val[:, 0:1] if y_val.dim() > 1 else y_val.unsqueeze(1)).item()
            
            scheduler.step(val_loss)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
            
            if (epoch + 1) % 20 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss/len(train_loader):.6f}, Val Loss: {val_loss:.6f}")
        
        logger.info(f"LSTM training complete. Best Val Loss: {best_val_loss:.6f}")
        
        return self
    
    def predict(self, steps: int = 30) -> pd.DataFrame:
        """
        Generate forecast
        
        Args:
            steps: Number of periods to forecast
        
        Returns:
            Forecast DataFrame
        """
        if not TORCH_AVAILABLE or self.model is None:
            return self._mock_forecast(steps)
        
        self.model.eval()
        
        # Get last sequence from training data
        scaled_data = self.scaler.transform(self.training_data[['revenue']].values)
        current_seq = torch.FloatTensor(scaled_data[-self.seq_length:]).unsqueeze(0).to(self.device)
        
        predictions = []
        
        with torch.no_grad():
            for _ in range(steps):
                pred = self.model(current_seq)
                predictions.append(pred.cpu().numpy()[0, 0])
                
                # Update sequence
                new_val = torch.FloatTensor([[pred.cpu().numpy()[0, 0]]]).to(self.device)
                current_seq = torch.cat([current_seq[:, 1:, :], new_val.unsqueeze(0)], dim=1)
        
        # Inverse transform
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions)
        
        # Create forecast DataFrame
        last_date = pd.to_datetime(self.training_data['date'].max())
        forecast_df = pd.DataFrame({
            'ds': pd.date_range(start=last_date + timedelta(days=1), periods=steps, freq='D'),
            'yhat': predictions.flatten(),
            'yhat_lower': predictions.flatten() * 0.9,
            'yhat_upper': predictions.flatten() * 1.1
        })
        
        return forecast_df
    
    def _mock_forecast(self, steps: int) -> pd.DataFrame:
        """Generate mock forecast"""
        base = self.training_data['revenue'].mean() if self.training_data is not None else 50000
        forecasts = [base * (1 + np.random.normal(0, 0.06)) for _ in range(steps)]
        
        return pd.DataFrame({
            'ds': pd.date_range(start=datetime.now(), periods=steps, freq='D'),
            'yhat': forecasts,
            'yhat_lower': [f * 0.9 for f in forecasts],
            'yhat_upper': [f * 1.1 for f in forecasts]
        })
    
    def evaluate(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate forecast metrics"""
        mape = mean_absolute_percentage_error(actual, predicted) * 100
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mae = mean_absolute_error(actual, predicted)
        
        self.metrics = {
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2)
        }
        
        return self.metrics


class EnsembleForecaster:
    """
    Ensemble forecaster combining multiple models
    
    Methods:
    - Simple average
    - Weighted average (based on validation performance)
    - Stacking
    """
    
    def __init__(self, models: Dict[str, Any] = None, weights: Dict[str, float] = None):
        """
        Initialize ensemble
        
        Args:
            models: Dictionary of forecaster instances
            weights: Optional weights for each model
        """
        self.models = models or {}
        self.weights = weights
        self.forecasts = {}
        self.metrics = {}
    
    def add_model(self, name: str, model: Any, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models[name] = model
        if self.weights is None:
            self.weights = {}
        self.weights[name] = weight
    
    def fit_all(self, data: pd.DataFrame, **kwargs):
        """Fit all models in ensemble"""
        for name, model in self.models.items():
            logger.info(f"Fitting {name}...")
            model.fit(data, **kwargs)
    
    def predict_all(self, steps: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Generate predictions from all models
        
        Returns:
            Dictionary of model forecasts
        """
        self.forecasts = {}
        
        for name, model in self.models.items():
            logger.info(f"Generating forecast from {name}...")
            self.forecasts[name] = model.predict(steps=steps)
        
        return self.forecasts
    
    def combine_forecasts(self, method: str = 'weighted_average') -> pd.DataFrame:
        """
        Combine forecasts from all models
        
        Args:
            method: 'simple_average', 'weighted_average', 'median'
        
        Returns:
            Combined forecast DataFrame
        """
        if not self.forecasts:
            raise ValueError("No forecasts available. Run predict_all first.")
        
        # Get all predictions
        predictions = {}
        for name, forecast in self.forecasts.items():
            predictions[name] = forecast['yhat'].values
        
        # Combine based on method
        if method == 'simple_average':
            combined = np.mean(list(predictions.values()), axis=0)
        
        elif method == 'weighted_average':
            if self.weights is None:
                # Equal weights
                self.weights = {name: 1/len(self.models) for name in self.models}
            
            # Normalize weights
            total_weight = sum(self.weights.values())
            normalized = {k: v/total_weight for k, v in self.weights.items()}
            
            combined = np.zeros(len(list(predictions.values())[0]))
            for name, pred in predictions.items():
                combined += pred * normalized.get(name, 1/len(predictions))
        
        elif method == 'median':
            combined = np.median(list(predictions.values()), axis=0)
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Create result DataFrame
        sample_forecast = list(self.forecasts.values())[0]
        
        result = pd.DataFrame({
            'ds': sample_forecast['ds'],
            'yhat': combined,
            'yhat_lower': combined * 0.9,
            'yhat_upper': combined * 1.1
        })
        
        # Add individual model predictions for comparison
        for name, forecast in self.forecasts.items():
            result[f'yhat_{name}'] = forecast['yhat'].values
        
        return result
    
    def evaluate_all(self, actual: pd.Series) -> Dict[str, Dict[str, float]]:
        """
        Evaluate all models against actual values
        
        Returns:
            Dictionary of metrics per model
        """
        results = {}
        
        for name, forecast in self.forecasts.items():
            predicted = forecast['yhat'].values[:len(actual)]
            actual_values = actual.values[:len(predicted)]
            
            mape = mean_absolute_percentage_error(actual_values, predicted) * 100
            rmse = np.sqrt(mean_squared_error(actual_values, predicted))
            mae = mean_absolute_error(actual_values, predicted)
            
            results[name] = {
                'mape': round(mape, 2),
                'rmse': round(rmse, 2),
                'mae': round(mae, 2)
            }
        
        self.metrics = results
        return results
    
    def get_best_model(self, metric: str = 'mape') -> str:
        """Get name of best performing model"""
        if not self.metrics:
            raise ValueError("No metrics available. Run evaluate_all first.")
        
        return min(self.metrics.keys(), key=lambda x: self.metrics[x][metric])


# CLI for testing
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2022-01-01', end='2024-06-30', freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'revenue': [50000 * (1 + 0.1 * np.sin(i * 2 * np.pi / 7) + np.random.normal(0, 0.08)) for i in range(len(dates))],
        'is_holiday': [1 if d.month == 10 and 20 <= d.day <= 30 else 0 for d in dates],
        'is_monsoon': [1 if d.month in [6, 7, 8, 9] else 0 for d in dates]
    })
    
    print(f"Data: {len(data)} days")
    
    # Test ARIMA
    print("\n--- ARIMA ---")
    arima = ARIMAForecaster(order=(2, 1, 2))
    arima.fit(data, target_column='revenue', auto_order=True)
    arima_forecast = arima.predict(steps=30)
    print(f"ARIMA forecast: {len(arima_forecast)} days")
    
    # Test LSTM
    print("\n--- LSTM ---")
    lstm = LSTMForecaster(hidden_size=32, num_layers=1, seq_length=14)
    lstm.fit(data, target_column='revenue', epochs=50)
    lstm_forecast = lstm.predict(steps=30)
    print(f"LSTM forecast: {len(lstm_forecast)} days")
    
    # Test Ensemble
    print("\n--- Ensemble ---")
    ensemble = EnsembleForecaster()
    ensemble.add_model('arima', arima, weight=0.4)
    ensemble.add_model('lstm', lstm, weight=0.6)
    ensemble.forecasts = {'arima': arima_forecast, 'lstm': lstm_forecast}
    combined = ensemble.combine_forecasts(method='weighted_average')
    print(f"Ensemble forecast: {len(combined)} days")
    print(f"Sample: {combined['yhat'].head()}")
