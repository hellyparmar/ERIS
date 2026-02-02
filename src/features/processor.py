"""
Enterprise Retail Intelligence System v3.0
R-DIOS FEATURE STORE - FEATURE ENGINEERING PROCESSOR

This module implements vectorized feature transformations for retail time-series data.
Designed to create rich feature sets for demand forecasting and inventory optimization.

Author: R-DIOS Team
Version: 3.0.0
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')


class RetailFeatureEngineer:
    """
    Feature engineering pipeline for retail analytics with strict vectorization.
    
    This class transforms raw retail data into ML-ready features by:
    - Extracting temporal patterns (time-series features)
    - Creating statistical memory (lags and rolling windows)
    - Encoding categorical variables
    - Normalizing target distributions
    """
    
    def __init__(self):
        """Initialize feature engineer with label encoders."""
        self.store_encoder = LabelEncoder()
        self.product_encoder = LabelEncoder()
        self.fitted = False
    
    # ============================================================================
    # TIME-SERIES TRANSFORMATION
    # ============================================================================
    
    def create_time_features(self, df):
        """
        Extract temporal features from date column.
        
        Args:
            df (pd.DataFrame): Input dataframe with 'date' column
            
        Returns:
            pd.DataFrame: DataFrame with added time features
        """
        df = df.copy()
        
        # Ensure 'date' is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Extract temporal components
        df['day_of_week'] = df['date'].dt.dayofweek  # Monday=0, Sunday=6
        df['month'] = df['date'].dt.month  # 1-12
        df['quarter'] = df['date'].dt.quarter  # 1-4
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)  # Sat/Sun = 1
        df['day_of_month'] = df['date'].dt.day
        df['week_of_year'] = df['date'].dt.isocalendar().week
        
        return df
    
    def create_cyclical_features(self, df):
        """
        Create sin/cos transformations for cyclical continuity.
        
        This preserves the circular nature of time (e.g., December is close to January).
        Critical for neural networks and tree-based models.
        
        Args:
            df (pd.DataFrame): Input dataframe with temporal features
            
        Returns:
            pd.DataFrame: DataFrame with cyclical encodings
        """
        df = df.copy()
        
        # Month cyclical encoding (12 months)
        if 'month' in df.columns:
            df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Day of week cyclical encoding (7 days)
        if 'day_of_week' in df.columns:
            df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Day of month cyclical encoding (assume 30 days for normalization)
        if 'day_of_month' in df.columns:
            df['dom_sin'] = np.sin(2 * np.pi * df['day_of_month'] / 30)
            df['dom_cos'] = np.cos(2 * np.pi * df['day_of_month'] / 30)
        
        return df
    
    # ============================================================================
    # STATISTICAL FEATURES - "MEMORY" OF THE MODEL
    # ============================================================================
    
    def create_lag_features(self, df, lags=[1, 7, 30], target_col='sales'):
        """
        Create lagged features to capture historical patterns.
        
        Lag features allow the model to "remember" past values:
        - Lag 1: Yesterday's sales (short-term trend)
        - Lag 7: Last week same day (weekly seasonality)
        - Lag 30: Last month same day (monthly seasonality)
        
        Args:
            df (pd.DataFrame): Input dataframe sorted by date
            lags (list): List of lag periods
            target_col (str): Column name to create lags for
            
        Returns:
            pd.DataFrame: DataFrame with lag features
        """
        df = df.copy()
        
        # Sort by date and store/product to ensure correct lag calculation
        if all(col in df.columns for col in ['date', 'store_id', 'product_id']):
            df = df.sort_values(['store_id', 'product_id', 'date']).reset_index(drop=True)
            
            # Group by store and product for proper lagging
            for lag in lags:
                df[f'{target_col}_lag_{lag}'] = df.groupby(['store_id', 'product_id'])[target_col].shift(lag)
        else:
            # Simple lag if grouping columns not available
            for lag in lags:
                df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        return df
    
    def create_rolling_window(self, df, windows=[7, 30], target_col='sales'):
        """
        Create rolling window statistics to capture trends and volatility.
        
        Rolling windows provide:
        - Rolling Mean: Smoothed trend direction
        - Rolling Std: Volatility/uncertainty measure
        
        Args:
            df (pd.DataFrame): Input dataframe sorted by date
            windows (list): List of window sizes (in days)
            target_col (str): Column name to calculate rolling stats for
            
        Returns:
            pd.DataFrame: DataFrame with rolling window features
        """
        df = df.copy()
        
        # Sort by date
        if all(col in df.columns for col in ['date', 'store_id', 'product_id']):
            df = df.sort_values(['store_id', 'product_id', 'date']).reset_index(drop=True)
            
            # Group by store and product for proper rolling calculation
            for window in windows:
                # Rolling mean (trend)
                df[f'{target_col}_rolling_mean_{window}'] = (
                    df.groupby(['store_id', 'product_id'])[target_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
                )
                
                # Rolling standard deviation (volatility)
                df[f'{target_col}_rolling_std_{window}'] = (
                    df.groupby(['store_id', 'product_id'])[target_col]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).std())
                )
                
                # Fill NaN std with 0 (no volatility when insufficient data)
                df[f'{target_col}_rolling_std_{window}'].fillna(0, inplace=True)
        else:
            # Simple rolling if grouping not available
            for window in windows:
                df[f'{target_col}_rolling_mean_{window}'] = (
                    df[target_col].rolling(window=window, min_periods=1).mean()
                )
                df[f'{target_col}_rolling_std_{window}'] = (
                    df[target_col].rolling(window=window, min_periods=1).std().fillna(0)
                )
        
        return df
    
    # ============================================================================
    # ENCODING & SCALING
    # ============================================================================
    
    def encode_categoricals(self, df, fit=True):
        """
        Encode categorical variables using Label Encoding.
        
        Args:
            df (pd.DataFrame): Input dataframe with categorical columns
            fit (bool): Whether to fit encoders (True for training, False for inference)
            
        Returns:
            pd.DataFrame: DataFrame with encoded categoricals
        """
        df = df.copy()
        
        if 'store_id' in df.columns:
            if fit:
                df['store_id_encoded'] = self.store_encoder.fit_transform(df['store_id'].astype(str))
            else:
                # Handle unseen categories
                df['store_id_encoded'] = df['store_id'].astype(str).map(
                    lambda x: self.store_encoder.transform([x])[0] 
                    if x in self.store_encoder.classes_ else -1
                )
        
        if 'product_id' in df.columns:
            if fit:
                df['product_id_encoded'] = self.product_encoder.fit_transform(df['product_id'].astype(str))
            else:
                # Handle unseen categories
                df['product_id_encoded'] = df['product_id'].astype(str).map(
                    lambda x: self.product_encoder.transform([x])[0]
                    if x in self.product_encoder.classes_ else -1
                )
        
        if fit:
            self.fitted = True
        
        return df
    
    def scale_targets(self, df, target_col='sales'):
        """
        Apply log transformation to normalize target distribution.
        
        Retail sales data is often right-skewed with outliers.
        Log transformation (log1p) helps:
        - Reduce impact of extreme values
        - Stabilize variance
        - Improve model convergence
        
        Args:
            df (pd.DataFrame): Input dataframe with target column
            target_col (str): Column name to transform
            
        Returns:
            pd.DataFrame: DataFrame with log-transformed target
        """
        df = df.copy()
        
        if target_col in df.columns:
            # Use log1p to handle zero values: log(1 + x)
            df[f'{target_col}_log'] = np.log1p(df[target_col])
        
        return df
    
    def inverse_scale_targets(self, df, target_col='sales'):
        """
        Inverse log transformation to get predictions back to original scale.
        
        Args:
            df (pd.DataFrame): Input dataframe with log-transformed target
            target_col (str): Base column name
            
        Returns:
            pd.DataFrame: DataFrame with inverse-transformed predictions
        """
        df = df.copy()
        
        log_col = f'{target_col}_log'
        if log_col in df.columns:
            df[f'{target_col}_predicted'] = np.expm1(df[log_col])
        
        return df
    
    # ============================================================================
    # PIPELINE ORCHESTRATION
    # ============================================================================
    
    def transform(self, df, fit=True, include_lags=True, include_rolling=True):
        """
        Complete feature engineering pipeline.
        
        Args:
            df (pd.DataFrame): Raw input dataframe
            fit (bool): Whether to fit encoders
            include_lags (bool): Whether to create lag features
            include_rolling (bool): Whether to create rolling window features
            
        Returns:
            pd.DataFrame: Fully transformed dataframe ready for ML
        """
        print("🔧 Starting Feature Engineering Pipeline...")
        
        # Step 1: Time-series features
        print("  📅 Creating time features...")
        df = self.create_time_features(df)
        df = self.create_cyclical_features(df)
        
        # Step 2: Statistical features (optional, order-dependent)
        if include_lags:
            print("  ⏮️  Creating lag features...")
            df = self.create_lag_features(df)
        
        if include_rolling:
            print("  📊 Creating rolling window features...")
            df = self.create_rolling_window(df)
        
        # Step 3: Encoding
        print("  🔢 Encoding categorical variables...")
        df = self.encode_categoricals(df, fit=fit)
        
        # Step 4: Target scaling
        if 'sales' in df.columns:
            print("  📈 Scaling target variable...")
            df = self.scale_targets(df)
        
        print("✅ Feature engineering complete!")
        print(f"   Original features: {len(df.columns) - 20}")  # Approximate
        print(f"   Total features: {len(df.columns)}")
        
        return df
    
    def get_feature_names(self, df):
        """
        Get list of all engineered feature names.
        
        Args:
            df (pd.DataFrame): Transformed dataframe
            
        Returns:
            list: List of feature column names
        """
        # Exclude metadata columns
        exclude_cols = ['date', 'store_id', 'product_id', 'sales', 'sales_log']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        return feature_cols


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_feature_summary(df, original_df):
    """
    Print summary of feature engineering transformations.
    
    Args:
        df (pd.DataFrame): Transformed dataframe
        original_df (pd.DataFrame): Original dataframe
    """
    print("\n" + "="*80)
    print("FEATURE ENGINEERING SUMMARY")
    print("="*80)
    print(f"Original shape: {original_df.shape}")
    print(f"Transformed shape: {df.shape}")
    print(f"Features added: {df.shape[1] - original_df.shape[1]}")
    print(f"\nNew features:")
    
    new_features = [col for col in df.columns if col not in original_df.columns]
    for i, feat in enumerate(new_features, 1):
        print(f"  {i:2d}. {feat}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    print("R-DIOS Feature Engineering Module v3.0")
    print("Ready for integration with MultiDatasetLoader")
