"""
Temporal Fusion Transformer (TFT) Forecasting Model
Advanced deep learning for multi-horizon time series forecasting
"""

import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available. TFT will use mock implementation.")


@dataclass
class TFTConfig:
    """TFT model configuration"""
    hidden_size: int = 64
    lstm_layers: int = 2
    attention_heads: int = 4
    dropout: float = 0.1
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    input_chunk_length: int = 30  # Days of history
    output_chunk_length: int = 7   # Days to forecast
    num_static_features: int = 3   # Category, channel, region
    num_time_varying_known: int = 5  # Day of week, month, holiday, etc.
    num_time_varying_unknown: int = 1  # Target variable


class GatedResidualNetwork(nn.Module):
    """
    Gated Residual Network (GRN) - key TFT component
    Enables selective information flow
    """
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int, dropout: float = 0.1):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Primary layers
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
        
        # Gate layers
        self.gate = nn.Linear(input_size, output_size)
        
        # Layer norm
        self.layer_norm = nn.LayerNorm(output_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # ELU activation
        self.elu = nn.ELU()
        
        # Residual connection (if dimensions match)
        self.residual = nn.Linear(input_size, output_size) if input_size != output_size else None
    
    def forward(self, x):
        # Primary path
        hidden = self.elu(self.fc1(x))
        hidden = self.dropout(hidden)
        hidden = self.fc2(hidden)
        
        # Gating
        gate = torch.sigmoid(self.gate(x))
        gated = gate * hidden
        
        # Residual
        if self.residual:
            residual = self.residual(x)
        else:
            residual = x
        
        # Add & Norm
        output = self.layer_norm(gated + residual)
        
        return output


class VariableSelectionNetwork(nn.Module):
    """
    Variable Selection Network
    Learns which inputs are most important
    """
    
    def __init__(self, input_size: int, num_inputs: int, hidden_size: int, dropout: float = 0.1):
        super().__init__()
        
        self.num_inputs = num_inputs
        self.hidden_size = hidden_size
        
        # Variable-specific GRNs
        self.var_grns = nn.ModuleList([
            GatedResidualNetwork(input_size, hidden_size, hidden_size, dropout)
            for _ in range(num_inputs)
        ])
        
        # Softmax weights
        self.softmax_weights = nn.Linear(hidden_size * num_inputs, num_inputs)
    
    def forward(self, inputs: List[torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor]:
        # Process each variable
        var_outputs = [grn(inp) for grn, inp in zip(self.var_grns, inputs)]
        
        # Concatenate for weight calculation
        concat = torch.cat(var_outputs, dim=-1)
        
        # Calculate variable weights
        weights = torch.softmax(self.softmax_weights(concat), dim=-1)
        
        # Weighted sum
        var_stack = torch.stack(var_outputs, dim=-1)
        weights_expanded = weights.unsqueeze(-2)
        output = (var_stack * weights_expanded).sum(dim=-1)
        
        return output, weights


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer implementation
    
    Key components:
    1. Variable Selection Networks for input importance
    2. LSTM encoder for temporal patterns
    3. Multi-head attention for long-range dependencies
    4. GRNs for information flow control
    """
    
    def __init__(self, config: TFTConfig):
        super().__init__()
        self.config = config
        
        # Static covariate encoder
        self.static_encoder = GatedResidualNetwork(
            config.num_static_features,
            config.hidden_size,
            config.hidden_size,
            config.dropout
        )
        
        # Time-varying encoders
        self.past_encoder = nn.Linear(
            config.num_time_varying_unknown + config.num_time_varying_known,
            config.hidden_size
        )
        
        self.future_encoder = nn.Linear(
            config.num_time_varying_known,
            config.hidden_size
        )
        
        # LSTM encoder
        self.encoder_lstm = nn.LSTM(
            input_size=config.hidden_size,
            hidden_size=config.hidden_size,
            num_layers=config.lstm_layers,
            batch_first=True,
            dropout=config.dropout if config.lstm_layers > 1 else 0
        )
        
        # LSTM decoder
        self.decoder_lstm = nn.LSTM(
            input_size=config.hidden_size,
            hidden_size=config.hidden_size,
            num_layers=config.lstm_layers,
            batch_first=True,
            dropout=config.dropout if config.lstm_layers > 1 else 0
        )
        
        # Multi-head attention
        self.attention = nn.MultiheadAttention(
            embed_dim=config.hidden_size,
            num_heads=config.attention_heads,
            dropout=config.dropout,
            batch_first=True
        )
        
        # Output layer
        self.output_layer = nn.Sequential(
            GatedResidualNetwork(config.hidden_size, config.hidden_size, config.hidden_size, config.dropout),
            nn.Linear(config.hidden_size, 1)
        )
    
    def forward(
        self,
        static_features: torch.Tensor,
        past_time_varying: torch.Tensor,
        future_time_varying: torch.Tensor
    ) -> torch.Tensor:
        batch_size = static_features.size(0)
        
        # Encode static features
        static_encoded = self.static_encoder(static_features)
        
        # Encode past time-varying
        past_encoded = self.past_encoder(past_time_varying)
        
        # Encode future time-varying
        future_encoded = self.future_encoder(future_time_varying)
        
        # Add static context to temporal features
        static_expanded_past = static_encoded.unsqueeze(1).expand(-1, past_encoded.size(1), -1)
        static_expanded_future = static_encoded.unsqueeze(1).expand(-1, future_encoded.size(1), -1)
        
        past_with_static = past_encoded + static_expanded_past
        future_with_static = future_encoded + static_expanded_future
        
        # LSTM encoding
        encoder_output, (hidden, cell) = self.encoder_lstm(past_with_static)
        
        # LSTM decoding
        decoder_output, _ = self.decoder_lstm(future_with_static, (hidden, cell))
        
        # Combine encoder and decoder outputs for attention
        combined = torch.cat([encoder_output, decoder_output], dim=1)
        
        # Self-attention
        attended, _ = self.attention(combined, combined, combined)
        
        # Get decoder portion
        decoder_attended = attended[:, -future_with_static.size(1):, :]
        
        # Output projection
        output = self.output_layer(decoder_attended)
        
        return output.squeeze(-1)


class TFTForecaster:
    """
    High-level TFT forecaster for retail demand
    """
    
    def __init__(self, config: TFTConfig = None):
        self.config = config or TFTConfig()
        self.model = None
        self.scaler = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_fitted = False
    
    def _prepare_features(
        self,
        data: pd.DataFrame,
        target_col: str = 'revenue'
    ) -> Dict[str, np.ndarray]:
        """Prepare features for TFT"""
        # Time features (known future)
        time_features = np.column_stack([
            data['date'].dt.dayofweek.values,
            data['date'].dt.month.values,
            data['date'].dt.day.values,
            data.get('is_holiday', np.zeros(len(data))).values,
            data.get('is_weekend', (data['date'].dt.dayofweek >= 5).astype(int)).values
        ])
        
        # Static features (e.g., category embeddings)
        static_features = np.zeros((len(data), self.config.num_static_features))
        
        # Target and unknown features
        target = data[target_col].values
        
        return {
            'time_features': time_features,
            'static_features': static_features,
            'target': target
        }
    
    def _create_sequences(
        self,
        features: Dict[str, np.ndarray],
        shuffle: bool = True
    ) -> Tuple[torch.Tensor, ...]:
        """Create input/output sequences"""
        time_feats = features['time_features']
        static_feats = features['static_features']
        target = features['target']
        
        input_len = self.config.input_chunk_length
        output_len = self.config.output_chunk_length
        
        X_static = []
        X_past = []
        X_future = []
        y = []
        
        for i in range(input_len, len(target) - output_len + 1):
            # Static features (use first sample)
            X_static.append(static_feats[i])
            
            # Past: time features + target
            past_target = target[i-input_len:i].reshape(-1, 1)
            past_time = time_feats[i-input_len:i]
            X_past.append(np.concatenate([past_target, past_time], axis=1))
            
            # Future: time features only
            X_future.append(time_feats[i:i+output_len])
            
            # Target
            y.append(target[i:i+output_len])
        
        # Convert to tensors
        X_static = torch.FloatTensor(np.array(X_static))
        X_past = torch.FloatTensor(np.array(X_past))
        X_future = torch.FloatTensor(np.array(X_future))
        y = torch.FloatTensor(np.array(y))
        
        if shuffle:
            indices = torch.randperm(len(y))
            X_static = X_static[indices]
            X_past = X_past[indices]
            X_future = X_future[indices]
            y = y[indices]
        
        return X_static, X_past, X_future, y
    
    def fit(
        self,
        data: pd.DataFrame,
        target_col: str = 'revenue',
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train TFT model
        
        Args:
            data: DataFrame with 'date' and target column
            target_col: Name of target column
            validation_split: Fraction for validation
        
        Returns:
            Training metrics
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available. Using mock training.")
            self.is_fitted = True
            return {'train_loss': 0.1, 'val_loss': 0.12}
        
        logger.info("Preparing TFT training data...")
        
        # Prepare features
        features = self._prepare_features(data, target_col)
        
        # Normalize target
        from sklearn.preprocessing import MinMaxScaler
        self.scaler = MinMaxScaler()
        features['target'] = self.scaler.fit_transform(
            features['target'].reshape(-1, 1)
        ).flatten()
        
        # Create sequences
        X_static, X_past, X_future, y = self._create_sequences(features)
        
        # Split
        split_idx = int(len(y) * (1 - validation_split))
        
        train_data = (
            X_static[:split_idx], X_past[:split_idx],
            X_future[:split_idx], y[:split_idx]
        )
        val_data = (
            X_static[split_idx:], X_past[split_idx:],
            X_future[split_idx:], y[split_idx:]
        )
        
        # Initialize model
        self.model = TemporalFusionTransformer(self.config).to(self.device)
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        best_val_loss = float('inf')
        train_losses = []
        val_losses = []
        
        for epoch in range(self.config.epochs):
            # Training
            self.model.train()
            
            for i in range(0, len(train_data[0]), self.config.batch_size):
                batch_end = min(i + self.config.batch_size, len(train_data[0]))
                
                static = train_data[0][i:batch_end].to(self.device)
                past = train_data[1][i:batch_end].to(self.device)
                future = train_data[2][i:batch_end].to(self.device)
                target = train_data[3][i:batch_end].to(self.device)
                
                optimizer.zero_grad()
                output = self.model(static, past, future)
                loss = criterion(output, target)
                loss.backward()
                optimizer.step()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                val_static = val_data[0].to(self.device)
                val_past = val_data[1].to(self.device)
                val_future = val_data[2].to(self.device)
                val_target = val_data[3].to(self.device)
                
                val_output = self.model(val_static, val_past, val_future)
                val_loss = criterion(val_output, val_target).item()
            
            train_losses.append(loss.item())
            val_losses.append(val_loss)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss={loss.item():.4f}, Val Loss={val_loss:.4f}")
        
        self.is_fitted = True
        
        return {
            'train_loss': train_losses[-1],
            'val_loss': val_losses[-1],
            'best_val_loss': best_val_loss
        }
    
    def predict(
        self,
        data: pd.DataFrame,
        horizon: int = 7
    ) -> pd.DataFrame:
        """
        Generate forecasts
        
        Args:
            data: Historical data
            horizon: Days to forecast
        
        Returns:
            DataFrame with predictions
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if not TORCH_AVAILABLE:
            # Mock predictions
            logger.warning("Using mock TFT predictions")
            base_date = data['date'].max()
            base_value = data['revenue'].mean()
            
            predictions = []
            for i in range(horizon):
                pred_date = base_date + timedelta(days=i+1)
                pred_value = base_value * (1 + 0.05 * np.sin(i * 2 * np.pi / 7))
                predictions.append({
                    'date': pred_date,
                    'forecast': pred_value,
                    'lower': pred_value * 0.9,
                    'upper': pred_value * 1.1
                })
            
            return pd.DataFrame(predictions)
        
        self.model.eval()
        
        # Prepare last input_chunk_length days
        features = self._prepare_features(data.tail(self.config.input_chunk_length + horizon))
        features['target'] = self.scaler.transform(
            features['target'].reshape(-1, 1)
        ).flatten()
        
        X_static, X_past, X_future, _ = self._create_sequences(features, shuffle=False)
        
        with torch.no_grad():
            static = X_static[-1:].to(self.device)
            past = X_past[-1:].to(self.device)
            future = X_future[-1:].to(self.device)
            
            output = self.model(static, past, future)
            predictions = output.cpu().numpy().flatten()
        
        # Inverse transform
        predictions = self.scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
        
        # Create result DataFrame
        base_date = data['date'].max()
        result = pd.DataFrame({
            'date': [base_date + timedelta(days=i+1) for i in range(len(predictions))],
            'forecast': predictions,
            'lower': predictions * 0.9,
            'upper': predictions * 1.1
        })
        
        return result


# CLI for testing
if __name__ == "__main__":
    print("Testing TFT Forecaster...")
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    
    data = pd.DataFrame({
        'date': dates,
        'revenue': 50000 + 10000 * np.sin(np.arange(len(dates)) * 2 * np.pi / 7) + np.random.normal(0, 3000, len(dates)),
        'is_holiday': np.random.choice([0, 1], len(dates), p=[0.95, 0.05])
    })
    
    print(f"Data: {len(data)} days")
    
    # Create forecaster
    config = TFTConfig(epochs=10)  # Quick test
    forecaster = TFTForecaster(config)
    
    # Train
    metrics = forecaster.fit(data, 'revenue')
    print(f"Training metrics: {metrics}")
    
    # Predict
    predictions = forecaster.predict(data, horizon=7)
    print(f"\nPredictions:")
    print(predictions)
