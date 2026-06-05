"""
LSTM/GRU-based Sales Forecasting Module

Implements recurrent neural network (RNN) architectures for multi-step time series
forecasting of retail sales. Supports transfer learning across outlets and products.
Uses PyTorch for model training and inference.
"""

import os
import pickle
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class LSTMNet(nn.Module):
    """LSTM-based sequence-to-sequence model for time series forecasting."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 7,
    ):
        """
        Initialize LSTM model.
        
        Args:
            input_size: Number of input features
            hidden_size: Size of LSTM hidden state
            num_layers: Number of LSTM layers
            dropout: Dropout probability
            output_size: Number of output timesteps (forecast horizon)
        """
        super(LSTMNet, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through LSTM.
        
        Args:
            x: Input tensor (batch_size, seq_length, input_size)
            
        Returns:
            Output tensor (batch_size, output_size)
        """
        lstm_out, _ = self.lstm(x)
        last_out = lstm_out[:, -1, :]  # Take last timestep
        last_out = self.dropout(last_out)
        output = self.fc(last_out)
        return output


class GRUNet(nn.Module):
    """GRU-based sequence-to-sequence model for time series forecasting."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 7,
    ):
        """
        Initialize GRU model.
        
        Args:
            input_size: Number of input features
            hidden_size: Size of GRU hidden state
            num_layers: Number of GRU layers
            dropout: Dropout probability
            output_size: Number of output timesteps (forecast horizon)
        """
        super(GRUNet, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size
        
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through GRU.
        
        Args:
            x: Input tensor (batch_size, seq_length, input_size)
            
        Returns:
            Output tensor (batch_size, output_size)
        """
        gru_out, _ = self.gru(x)
        last_out = gru_out[:, -1, :]  # Take last timestep
        last_out = self.dropout(last_out)
        output = self.fc(last_out)
        return output


class LSTMForecaster:
    """
    LSTM/GRU-based time series forecaster for retail sales prediction.
    
    Features:
    - Sequence-based learning (30-day lookback window)
    - LSTM and GRU architecture support
    - Multi-step ahead forecasting
    - Transfer learning across outlets
    - Model persistence with PyTorch
    - Confidence intervals on predictions
    """
    
    # Hyperparameters
    SEQUENCE_LENGTH = 30  # 30-day lookback window
    HIDDEN_SIZE = 128
    NUM_LAYERS = 2
    DROPOUT = 0.2
    
    # Feature columns (9 features, specific order)
    FEATURE_COLUMNS = [
        'units_sold',
        'unit_price',
        'discount_percent',
        'temperature_max_celsius',
        'is_holiday',
        'is_weekend',
        'day_of_week_sin',
        'day_of_week_cos',
        'month_sin',
        'month_cos',
        'is_month_end',
    ]
    
    def __init__(
        self,
        outlet_id: int,
        product_id: int,
        db: Session,
        device: str = 'cpu',
        model_dir: str = 'models',
    ):
        """
        Initialize LSTM forecaster.
        
        Args:
            outlet_id: Outlet ID for outlet-specific forecasting
            product_id: Product ID for product-specific forecasting
            db: SQLAlchemy database session
            device: Computation device ('cpu' or 'cuda')
            model_dir: Directory to save/load models
        """
        self.outlet_id = outlet_id
        self.product_id = product_id
        self.db = db
        self.device = torch.device(device if torch.cuda.is_available() or device == 'cpu' else 'cpu')
        self.model_dir = model_dir
        
        os.makedirs(model_dir, exist_ok=True)
        
        self.model: Optional[nn.Module] = None
        self.scaler: Optional[MinMaxScaler] = None
        self.training_data: Optional[pd.DataFrame] = None
        self.feature_columns_actual = []
        
        logger.info(f"LSTMForecaster initialized for outlet {outlet_id}, product {product_id} on device {self.device}")
    
    def _fetch_data(self) -> pd.DataFrame:
        """
        Fetch historical sales and feature data from database.
        
        Returns:
            DataFrame with dates and feature columns
        """
        try:
            from app.models import SaleTransaction, Product, ExternalRegressor
            
            # Query sales transactions for this outlet and product
            stmt = select(SaleTransaction).where(
                and_(
                    SaleTransaction.outlet_id == self.outlet_id,
                    SaleTransaction.product_id == self.product_id,
                )
            ).order_by(SaleTransaction.transaction_date)
            
            transactions = self.db.execute(stmt).scalars().all()
            
            if not transactions:
                logger.warning(f"No transactions found for outlet {self.outlet_id}, product {self.product_id}")
                return pd.DataFrame()
            
            # Aggregate by date
            data = []
            for trans in transactions:
                data.append({
                    'date': trans.transaction_date.date() if hasattr(trans.transaction_date, 'date') else trans.transaction_date,
                    'units_sold': trans.quantity,
                    'unit_price': trans.unit_price,
                    'discount_percent': trans.discount or 0,
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Aggregate by date (sum units, avg price/discount)
            df = df.groupby('date').agg({
                'units_sold': 'sum',
                'unit_price': 'mean',
                'discount_percent': 'mean',
            }).reset_index()
            
            # Add external regressors
            stmt_reg = select(ExternalRegressor).where(
                ExternalRegressor.date >= df['date'].min()
            ).order_by(ExternalRegressor.date)
            
            regressors = self.db.execute(stmt_reg).scalars().all()
            reg_dict = {}
            for reg in regressors:
                reg_dict[reg.date] = {
                    'temperature_max_celsius': reg.temperature or 25.0,
                    'is_holiday': reg.is_holiday if hasattr(reg, 'is_holiday') else 0,
                }
            
            # Add regressor features
            df['temperature_max_celsius'] = df['date'].map(lambda x: reg_dict.get(x, {}).get('temperature_max_celsius', 25.0))
            df['is_holiday'] = df['date'].map(lambda x: reg_dict.get(x, {}).get('is_holiday', 0))
            
            # Add temporal features
            df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
            
            # Cyclical encoding for day of week
            df['day_of_week_sin'] = np.sin(2 * np.pi * df['date'].dt.dayofweek / 7)
            df['day_of_week_cos'] = np.cos(2 * np.pi * df['date'].dt.dayofweek / 7)
            
            # Cyclical encoding for month
            df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12)
            
            # Month end indicator
            df['is_month_end'] = (df['date'].dt.day == df['date'].dt.daysinmonth).astype(int)
            
            # Fill any missing values with forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"Fetched {len(df)} days of data for outlet {self.outlet_id}, product {self.product_id}")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data from database: {str(e)}")
            return pd.DataFrame()
    
    def prepare_sequences(
        self,
        df: pd.DataFrame,
        horizon_days: int = 7,
        fit_scaler: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training.
        
        Creates sliding windows of SEQUENCE_LENGTH with targets of horizon_days.
        Normalizes all features using MinMaxScaler.
        
        Args:
            df: DataFrame with feature columns
            horizon_days: Number of days to predict ahead
            fit_scaler: Whether to fit scaler on this data (False for inference)
            
        Returns:
            Tuple of (X, y, X_dates, y_dates) where:
            - X: shape (n_samples, SEQUENCE_LENGTH, n_features)
            - y: shape (n_samples, horizon_days)
            - X_dates: start dates of sequences
            - y_dates: end dates of targets
        """
        # Select feature columns that exist in DataFrame
        available_features = [col for col in self.FEATURE_COLUMNS if col in df.columns]
        self.feature_columns_actual = available_features
        
        feature_data = df[available_features].values
        dates = df['date'].values
        
        # Fit or use existing scaler
        if fit_scaler or self.scaler is None:
            self.scaler = MinMaxScaler(feature_range=(0, 1))
            feature_data_scaled = self.scaler.fit_transform(feature_data)
            logger.info(f"Fitted scaler on {len(feature_data)} samples with {len(available_features)} features")
        else:
            feature_data_scaled = self.scaler.transform(feature_data)
        
        # Create sequences
        X, y = [], []
        X_dates, y_dates = [], []
        
        for i in range(len(feature_data_scaled) - self.SEQUENCE_LENGTH - horizon_days + 1):
            X.append(feature_data_scaled[i:i + self.SEQUENCE_LENGTH])
            y.append(feature_data_scaled[i + self.SEQUENCE_LENGTH:i + self.SEQUENCE_LENGTH + horizon_days, 0])  # Only units_sold
            X_dates.append(dates[i])
            y_dates.append(dates[i + self.SEQUENCE_LENGTH + horizon_days - 1])
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"Created {len(X)} sequences (X shape: {X.shape}, y shape: {y.shape})")
        return X, y, np.array(X_dates), np.array(y_dates)
    
    def build_model(self, model_type: str = 'lstm', horizon_days: int = 7) -> nn.Module:
        """
        Build LSTM or GRU model.
        
        Args:
            model_type: 'lstm' or 'gru'
            horizon_days: Number of output timesteps
            
        Returns:
            PyTorch model instance
        """
        input_size = len(self.feature_columns_actual) if self.feature_columns_actual else len(self.FEATURE_COLUMNS)
        
        if model_type.lower() == 'lstm':
            model = LSTMNet(
                input_size=input_size,
                hidden_size=self.HIDDEN_SIZE,
                num_layers=self.NUM_LAYERS,
                dropout=self.DROPOUT,
                output_size=horizon_days,
            )
            logger.info(f"Built LSTM model: input_size={input_size}, hidden_size={self.HIDDEN_SIZE}, num_layers={self.NUM_LAYERS}")
        elif model_type.lower() == 'gru':
            model = GRUNet(
                input_size=input_size,
                hidden_size=self.HIDDEN_SIZE,
                num_layers=self.NUM_LAYERS,
                dropout=self.DROPOUT,
                output_size=horizon_days,
            )
            logger.info(f"Built GRU model: input_size={input_size}, hidden_size={self.HIDDEN_SIZE}, num_layers={self.NUM_LAYERS}")
        else:
            raise ValueError(f"Unknown model_type: {model_type}. Use 'lstm' or 'gru'.")
        
        return model.to(self.device)
    
    def train(
        self,
        horizon_days: int = 7,
        epochs: int = 100,
        model_type: str = 'lstm',
        batch_size: int = 64,
        learning_rate: float = 0.001,
        early_stopping_patience: int = 10,
    ) -> Dict:
        """
        Train LSTM/GRU model with chronological train/val/test split.
        
        Args:
            horizon_days: Number of days to forecast ahead
            epochs: Maximum number of training epochs
            model_type: 'lstm' or 'gru'
            batch_size: Training batch size
            learning_rate: Adam optimizer learning rate
            early_stopping_patience: Patience for early stopping
            
        Returns:
            Dictionary with training metrics:
            {
                'train_loss': list,
                'val_loss': list,
                'test_mape': float,
                'test_rmse': float,
                'test_mae': float,
                'epochs_trained': int,
                'model_path': str,
            }
        """
        # Fetch and prepare data
        df = self._fetch_data()
        if len(df) < self.SEQUENCE_LENGTH + horizon_days:
            raise ValueError(f"Insufficient data: {len(df)} rows, need at least {self.SEQUENCE_LENGTH + horizon_days}")
        
        self.training_data = df.copy()
        
        # Prepare sequences
        X, y, _, _ = self.prepare_sequences(df, horizon_days=horizon_days, fit_scaler=True)
        
        # Chronological split (80% train, 10% val, 10% test)
        n_samples = len(X)
        train_size = int(0.8 * n_samples)
        val_size = int(0.1 * n_samples)
        
        X_train, y_train = X[:train_size], y[:train_size]
        X_val, y_val = X[train_size:train_size + val_size], y[train_size:train_size + val_size]
        X_test, y_test = X[train_size + val_size:], y[train_size + val_size:]
        
        logger.info(f"Split: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")
        
        # Convert to PyTorch tensors
        X_train_t = torch.FloatTensor(X_train).to(self.device)
        y_train_t = torch.FloatTensor(y_train).to(self.device)
        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.FloatTensor(y_val).to(self.device)
        X_test_t = torch.FloatTensor(X_test).to(self.device)
        y_test_t = torch.FloatTensor(y_test).to(self.device)
        
        # Create data loaders
        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
        
        # Build model
        self.model = self.build_model(model_type=model_type, horizon_days=horizon_days)
        
        # Optimizer and loss
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')
        patience_counter = 0
        
        logger.info(f"Starting training: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0.0
            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            train_losses.append(train_loss)
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                y_val_pred = self.model(X_val_t)
                val_loss = criterion(y_val_pred, y_val_t).item()
                val_losses.append(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                model_path = os.path.join(
                    self.model_dir,
                    f"{model_type}_{self.outlet_id}_{self.product_id}_{horizon_days}.pth"
                )
                torch.save(self.model.state_dict(), model_path)
                logger.info(f"Epoch {epoch + 1}: New best val_loss={val_loss:.6f}, model saved")
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch + 1}")
                    break
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}: train_loss={train_loss:.6f}, val_loss={val_loss:.6f}")
        
        # Evaluate on test set
        self.model.eval()
        with torch.no_grad():
            y_test_pred = self.model(X_test_t).cpu().numpy()
            y_test_np = y_test_t.cpu().numpy()
        
        # Calculate metrics on scaled data
        mape = np.mean(np.abs((y_test_np - y_test_pred) / (y_test_np + 1e-8))) * 100
        rmse = np.sqrt(np.mean((y_test_np - y_test_pred) ** 2))
        mae = np.mean(np.abs(y_test_np - y_test_pred))
        
        logger.info(f"Test metrics: MAPE={mape:.2f}%, RMSE={rmse:.6f}, MAE={mae:.6f}")
        
        return {
            'train_loss': train_losses,
            'val_loss': val_losses,
            'test_mape': float(mape),
            'test_rmse': float(rmse),
            'test_mae': float(mae),
            'epochs_trained': epoch + 1,
            'model_path': model_path,
        }
    
    def forecast(
        self,
        horizon_days: int = 7,
        model_type: str = 'lstm',
    ) -> Dict:
        """
        Generate forecast on most recent data.
        
        Loads saved model or trains if not found. Runs inference on the most recent
        SEQUENCE_LENGTH days and returns forecasts with confidence intervals.
        
        Args:
            horizon_days: Number of days to forecast ahead
            model_type: 'lstm' or 'gru'
            
        Returns:
            Dictionary with:
            {
                'dates': list of forecast dates,
                'predicted_units': list of point forecasts,
                'confidence_lower': list of lower bounds (predicted * 0.85),
                'confidence_upper': list of upper bounds (predicted * 1.15),
            }
        """
        # Load or train model
        model_path = os.path.join(
            self.model_dir,
            f"{model_type}_{self.outlet_id}_{self.product_id}_{horizon_days}.pth"
        )
        
        if not os.path.exists(model_path):
            logger.info(f"Model not found at {model_path}, training...")
            self.train(horizon_days=horizon_days, model_type=model_type)
        else:
            logger.info(f"Loading model from {model_path}")
            # Fetch data to prepare sequences (get scaler)
            df = self._fetch_data()
            if len(df) < self.SEQUENCE_LENGTH + horizon_days:
                raise ValueError(f"Insufficient data for forecasting")
            self.training_data = df.copy()
            # Prepare sequences to fit scaler
            self.prepare_sequences(df, horizon_days=horizon_days, fit_scaler=True)
            
            # Load model weights
            self.model = self.build_model(model_type=model_type, horizon_days=horizon_days)
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
        
        # Get most recent SEQUENCE_LENGTH days
        df = self._fetch_data()
        if len(df) < self.SEQUENCE_LENGTH:
            raise ValueError(f"Insufficient recent data for inference")
        
        available_features = [col for col in self.FEATURE_COLUMNS if col in df.columns]
        recent_data = df[available_features].tail(self.SEQUENCE_LENGTH).values
        
        # Scale
        recent_data_scaled = self.scaler.transform(recent_data)
        X_inference = torch.FloatTensor(recent_data_scaled).unsqueeze(0).to(self.device)
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            y_pred_scaled = self.model(X_inference).cpu().numpy()[0]
        
        # Inverse transform (only units_sold, column 0)
        y_pred_full = np.zeros((len(y_pred_scaled), len(available_features)))
        y_pred_full[:, 0] = y_pred_scaled  # Put predictions in first column (units_sold)
        
        # Use dummy values for other features to inverse transform
        dummy_features = recent_data[-len(y_pred_scaled):]
        y_pred_full[:, 1:] = dummy_features[:, 1:]
        
        y_pred_original = self.scaler.inverse_transform(y_pred_full)[:, 0]
        y_pred_original = np.maximum(y_pred_original, 0)  # Clip to non-negative
        
        # Generate forecast dates
        last_date = pd.to_datetime(df['date'].iloc[-1])
        forecast_dates = [
            (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(1, horizon_days + 1)
        ]
        
        # Confidence intervals (±15%)
        confidence_lower = y_pred_original * 0.85
        confidence_upper = y_pred_original * 1.15
        
        logger.info(f"Generated {horizon_days}-day forecast for outlet {self.outlet_id}, product {self.product_id}")
        
        return {
            'dates': forecast_dates,
            'predicted_units': y_pred_original.tolist(),
            'confidence_lower': confidence_lower.tolist(),
            'confidence_upper': confidence_upper.tolist(),
        }
    
    def transfer_learn(
        self,
        source_outlet_id: int,
        fine_tune_epochs: int = 20,
        horizon_days: int = 7,
        model_type: str = 'lstm',
        learning_rate: float = 0.0001,
    ) -> Dict:
        """
        Transfer learning from another outlet's model.
        
        Loads weights from source outlet, freezes first LSTM/GRU layer, and
        fine-tunes on target outlet's data.
        
        Args:
            source_outlet_id: Outlet ID with pre-trained model
            fine_tune_epochs: Number of fine-tuning epochs
            horizon_days: Number of days to forecast
            model_type: 'lstm' or 'gru'
            learning_rate: Lower LR for fine-tuning
            
        Returns:
            Dictionary with fine-tuning metrics
        """
        # Load source model
        source_model_path = os.path.join(
            self.model_dir,
            f"{model_type}_{source_outlet_id}_{self.product_id}_{horizon_days}.pth"
        )
        
        if not os.path.exists(source_model_path):
            raise FileNotFoundError(f"Source model not found: {source_model_path}")
        
        logger.info(f"Loading source model from outlet {source_outlet_id}")
        
        # Build model and load source weights
        self.model = self.build_model(model_type=model_type, horizon_days=horizon_days)
        self.model.load_state_dict(torch.load(source_model_path, map_location=self.device))
        assert self.model is not None, "Model must be initialized before freezing layers"

        # Freeze first LSTM/GRU layer weights by parameter name
        if model_type.lower() == 'lstm':
            for name, param in self.model.lstm.named_parameters():
                if name.endswith('_l0'):
                    param.requires_grad = False
        elif model_type.lower() == 'gru':
            for name, param in self.model.gru.named_parameters():
                if name.endswith('_l0'):
                    param.requires_grad = False

        # Fetch target outlet data
        df_target = self._fetch_data()
        if len(df_target) < self.SEQUENCE_LENGTH + horizon_days:
            raise ValueError(f"Insufficient target data for fine-tuning")
        
        self.training_data = df_target.copy()
        
        # Prepare sequences (fit scaler on target data)
        X, y, _, _ = self.prepare_sequences(df_target, horizon_days=horizon_days, fit_scaler=True)
        
        # Use all data for fine-tuning (small learning rate)
        X_t = torch.FloatTensor(X).to(self.device)
        y_t = torch.FloatTensor(y).to(self.device)
        
        dataset = TensorDataset(X_t, y_t)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=False)
        
        # Fine-tune
        optimizer = optim.Adam(
            [p for p in self.model.parameters() if p.requires_grad],
            lr=learning_rate
        )
        criterion = nn.MSELoss()
        
        logger.info(f"Fine-tuning on target outlet {self.outlet_id} for {fine_tune_epochs} epochs")
        
        fine_tune_losses = []
        for epoch in range(fine_tune_epochs):
            self.model.train()
            epoch_loss = 0.0
            for X_batch, y_batch in dataloader:
                optimizer.zero_grad()
                y_pred = self.model(X_batch)
                loss = criterion(y_pred, y_batch)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            epoch_loss /= len(dataloader)
            fine_tune_losses.append(epoch_loss)
            
            if (epoch + 1) % 5 == 0:
                logger.info(f"Fine-tune epoch {epoch + 1}: loss={epoch_loss:.6f}")
        
        # Save fine-tuned model
        model_path = os.path.join(
            self.model_dir,
            f"{model_type}_{self.outlet_id}_{self.product_id}_{horizon_days}.pth"
        )
        torch.save(self.model.state_dict(), model_path)
        logger.info(f"Fine-tuned model saved to {model_path}")
        
        return {
            'source_outlet_id': source_outlet_id,
            'target_outlet_id': self.outlet_id,
            'fine_tune_losses': fine_tune_losses,
            'model_path': model_path,
        }
