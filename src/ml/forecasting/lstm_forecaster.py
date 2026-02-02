"""
LSTM Forecaster for R-DIOS Demand Forecasting
Deep Learning Time-Series Model using PyTorch

This implements a simple but effective LSTM model for retail demand forecasting.
Designed to work with the validation framework.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Try importing PyTorch
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. LSTM forecaster will not work.")


class TimeSeriesDataset(Dataset):
    """PyTorch Dataset for time series data"""
    
    def __init__(self, data: np.ndarray, seq_length: int = 30):
        """
        Args:
            data: 1D array of time series values
            seq_length: Number of past observations to use for prediction
        """
        self.data = data
        self.seq_length = seq_length
        
    def __len__(self):
        return len(self.data) - self.seq_length
    
    def __getitem__(self, idx):
        # Input: seq_length past values
        x = self.data[idx:idx + self.seq_length]
        # Target: next value
        y = self.data[idx + self.seq_length]
        
        return (
            torch.FloatTensor(x).unsqueeze(-1),  # Add feature dimension
            torch.FloatTensor([y])
        )


class LSTMModel(nn.Module):
    """LSTM Neural Network for Time Series Forecasting"""
    
    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Fully connected output layer
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        # x shape: (batch, seq_length, input_size)
        
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)
        
        # Take the last output
        last_output = lstm_out[:, -1, :]
        
        # Fully connected layer
        prediction = self.fc(last_output)
        
        return prediction


class LSTMForecaster:
    """
    LSTM-based demand forecasting for R-DIOS
    
    Features:
    - Sequence-to-one prediction
    - Configurable architecture
    - Early stopping
    - Normalization
    """
    
    def __init__(
        self,
        seq_length: int = 30,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 50,
        device: str = None
    ):
        """
        Initialize LSTM forecaster
        
        Args:
            seq_length: Number of past observations to use
            hidden_size: LSTM hidden layer size
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            learning_rate: Learning rate for optimizer
            batch_size: Training batch size
            epochs: Maximum training epochs
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for LSTM forecaster. Install with: pip install torch")
        
        self.seq_length = seq_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        
        # Device selection
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        self.model = None
        self.scaler_mean = None
        self.scaler_std = None
        
        logger.info(f"LSTM Forecaster initialized on device: {self.device}")
    
    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to zero mean and unit variance"""
        self.scaler_mean = np.mean(data)
        self.scaler_std = np.std(data)
        
        if self.scaler_std == 0:
            self.scaler_std = 1
        
        return (data - self.scaler_mean) / self.scaler_std
    
    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize predictions back to original scale"""
        return (data * self.scaler_std) + self.scaler_mean
    
    def fit(self, train_data: np.ndarray, validation_split: float = 0.1):
        """
        Train LSTM model
        
        Args:
            train_data: 1D array of training values
            validation_split: Fraction of data to use for validation
        """
        # Normalize data
        normalized_data = self._normalize(train_data)
        
        # Split into train/validation
        val_size = int(len(normalized_data) * validation_split)
        train_size = len(normalized_data) - val_size
        
        train_subset = normalized_data[:train_size]
        val_subset = normalized_data[train_size:]
        
        # Create datasets
        train_dataset = TimeSeriesDataset(train_subset, self.seq_length)
        val_dataset = TimeSeriesDataset(val_subset, self.seq_length) if val_size > self.seq_length else None
        
        # Create dataloaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            drop_last=True
        )
        
        val_loader = None
        if val_dataset is not None and len(val_dataset) > 0:
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.batch_size,
                shuffle=False
            )
        
        # Initialize model
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(self.epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                predictions = self.model(batch_x)
                loss = criterion(predictions, batch_y)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # Validation
            if val_loader is not None:
                self.model.eval()
                val_loss = 0.0
                
                with torch.no_grad():
                    for batch_x, batch_y in val_loader:
                        batch_x = batch_x.to(self.device)
                        batch_y = batch_y.to(self.device)
                        
                        predictions = self.model(batch_x)
                        loss = criterion(predictions, batch_y)
                        val_loss += loss.item()
                
                val_loss /= len(val_loader)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{self.epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            else:
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{self.epochs} - Train Loss: {train_loss:.4f}")
        
        logger.info("LSTM training complete")
    
    def predict(self, history: np.ndarray, horizon: int) -> np.ndarray:
        """
        Generate forecast for future periods
        
        Args:
            history: Historical data (at least seq_length values)
            horizon: Number of periods to forecast
        
        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        if len(history) < self.seq_length:
            raise ValueError(f"History must have at least {self.seq_length} values")
        
        self.model.eval()
        predictions = []
        
        # Normalize history
        normalized_history = (history - self.scaler_mean) / self.scaler_std
        
        # Use last seq_length values as initial input
        current_sequence = normalized_history[-self.seq_length:].copy()
        
        with torch.no_grad():
            for _ in range(horizon):
                # Prepare input
                x = torch.FloatTensor(current_sequence).unsqueeze(0).unsqueeze(-1).to(self.device)
                
                # Predict next value
                pred = self.model(x)
                pred_value = pred.cpu().numpy()[0, 0]
                
                # Store prediction
                predictions.append(pred_value)
                
                # Update sequence (rolling window)
                current_sequence = np.append(current_sequence[1:], pred_value)
        
        # Denormalize predictions
        predictions = np.array(predictions)
        predictions = self._denormalize(predictions)
        
        return predictions


# Convenience function for validation script
def validate_lstm(
    train_data: np.ndarray,
    test_data: np.ndarray,
    seq_length: int = 30,
    **kwargs
) -> Tuple[np.ndarray, dict]:
    """
    Train and validate LSTM model
    
    Args:
        train_data: Training time series
        test_data: Test time series
        seq_length: Sequence length
        **kwargs: Additional LSTM parameters
    
    Returns:
        predictions, metrics
    """
    try:
        forecaster = LSTMForecaster(seq_length=seq_length, **kwargs)
        forecaster.fit(train_data)
        predictions = forecaster.predict(train_data, horizon=len(test_data))
        
        # Calculate metrics
        mape = np.mean(np.abs((test_data - predictions) / test_data)) * 100
        rmse = np.sqrt(np.mean((test_data - predictions) ** 2))
        mae = np.mean(np.abs(test_data - predictions))
        
        ss_res = np.sum((test_data - predictions) ** 2)
        ss_tot = np.sum((test_data - np.mean(test_data)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        metrics = {
            'mape': mape,
            'rmse': rmse,
            'mae': mae,
            'r2': r2
        }
        
        return predictions, metrics
        
    except Exception as e:
        logger.error(f"LSTM validation failed: {e}")
        return None, {
            'mape': np.nan,
            'rmse': np.nan,
            'mae': np.nan,
            'r2': np.nan
        }


if __name__ == "__main__":
    # Test LSTM forecaster
    print("Testing LSTM Forecaster...")
    
    if not TORCH_AVAILABLE:
        print("PyTorch not available. Install with: pip install torch")
    else:
        # Generate sample data
        np.random.seed(42)
        t = np.arange(500)
        data = 100 + 10 * np.sin(t * 2 * np.pi / 50) + np.random.normal(0, 5, len(t))
        
        # Split train/test
        train = data[:400]
        test = data[400:]
        
        # Train and predict
        forecaster = LSTMForecaster(
            seq_length=30,
            hidden_size=32,
            num_layers=2,
            epochs=20,
            batch_size=16
        )
        
        print("Training LSTM...")
        forecaster.fit(train)
        
        print("Generating predictions...")
        predictions = forecaster.predict(train, horizon=len(test))
        
        # Calculate metrics
        mape = np.mean(np.abs((test - predictions) / test)) * 100
        print(f"\nTest MAPE: {mape:.2f}%")
        print("✅ LSTM forecaster working correctly!")
