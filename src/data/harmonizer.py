"""
Enterprise Retail Intelligence System v3.0
R-DIOS SCHEMA HARMONIZER

Transforms heterogeneous data sources into standardized schemas.
Handles column renaming, type casting, and missing value imputation.

Author: R-DIOS Team
Version: 3.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class SchemaHarmonizer:
    """
    Harmonizes data from multiple sources into a unified schema.
    
    Handles common retail data variations:
    - Different column names (SaleAmount vs revenue vs sales)
    - Different date formats (MM/DD/YYYY vs YYYY-MM-DD)
    - Different ID formats (store_001 vs STORE_1)
    - Missing columns (graceful degradation)
    """
    
    # ============================================================================
    # COLUMN MAPPING DICTIONARIES
    # ============================================================================
    
    # Sales column mappings (various sources → standard schema)
    SALES_COLUMN_MAP = {
        # Date columns
        'date': ['date', 'Date', 'transaction_date', 'sale_date', 'datetime', 'timestamp'],
        
        # Store ID columns
        'store_id': ['store_id', 'store', 'store_nbr', 'store_number', 'location_id', 'shop_id'],
        
        # Product ID columns
        'product_id': ['product_id', 'item_id', 'sku', 'product', 'item', 'article_id'],
        
        # Quantity columns
        'quantity': ['quantity', 'qty', 'units', 'units_sold', 'count', 'items'],
        
        # Revenue/Sales columns
        'revenue': ['revenue', 'sales', 'amount', 'sale_amount', 'turnover', 'total_sales', 'total']
    }
    
    # Inventory column mappings
    INVENTORY_COLUMN_MAP = {
        'date': ['date', 'Date', 'snapshot_date', 'inventory_date', 'timestamp'],
        'store_id': ['store_id', 'store', 'store_nbr', 'location_id', 'warehouse_id'],
        'product_id': ['product_id', 'item_id', 'sku', 'product', 'article_id'],
        'stock_level': ['stock_level', 'inventory', 'stock', 'quantity_on_hand', 'available'],
        'reorder_point': ['reorder_point', 'min_stock', 'safety_stock', 'threshold']
    }
    
    # Macro/External factors column mappings
    MACRO_COLUMN_MAP = {
        'date': ['date', 'Date', 'period', 'time_period', 'month', 'year'],
        'indicator_name': ['indicator', 'indicator_name', 'metric', 'variable', 'name'],
        'value': ['value', 'amount', 'measure', 'data_value', 'val'],
        'region': ['region', 'location', 'area', 'geography', 'state', 'country']
    }
    
    def __init__(self):
        """Initialize harmonizer with mapping dictionaries."""
        self.verbose = True
    
    # ============================================================================
    # CORE HARMONIZATION METHOD
    # ============================================================================
    
    def harmonize_schema(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """
        Harmonize dataframe to standard schema.
        
        Args:
            df (pd.DataFrame): Input dataframe
            source_type (str): One of 'sales', 'inventory', 'macro'
            
        Returns:
            pd.DataFrame: Harmonized dataframe
        """
        df = df.copy()
        
        if self.verbose:
            print(f"\n🔧 Harmonizing {source_type} data...")
            print(f"   Input shape: {df.shape}")
            print(f"   Input columns: {list(df.columns)}")
        
        # Select appropriate column map
        if source_type == 'sales':
            column_map = self.SALES_COLUMN_MAP
        elif source_type == 'inventory':
            column_map = self.INVENTORY_COLUMN_MAP
        elif source_type == 'macro':
            column_map = self.MACRO_COLUMN_MAP
        else:
            raise ValueError(f"Unknown source_type: {source_type}")
        
        # Step 1: Map columns
        df = self._map_columns(df, column_map)
        
        # Step 2: Parse dates
        if 'date' in df.columns:
            df = self._parse_dates(df)
        
        # Step 3: Standardize IDs
        if 'store_id' in df.columns:
            df['store_id'] = df['store_id'].astype(str)
        if 'product_id' in df.columns:
            df['product_id'] = df['product_id'].astype(str)
        
        # Step 4: Handle missing values
        df = self._handle_missing_values(df, source_type)
        
        # Step 5: Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        if self.verbose:
            print(f"   ✅ Output shape: {df.shape}")
            print(f"   ✅ Output columns: {list(df.columns)}")
        
        return df
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _map_columns(self, df: pd.DataFrame, column_map: Dict) -> pd.DataFrame:
        """
        Rename columns based on mapping dictionary.
        
        Args:
            df (pd.DataFrame): Input dataframe
            column_map (Dict): Mapping dictionary
            
        Returns:
            pd.DataFrame: DataFrame with renamed columns
        """
        df = df.copy()
        rename_dict = {}
        
        for standard_name, possible_names in column_map.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    rename_dict[possible_name] = standard_name
                    break
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
            if self.verbose:
                print(f"   📝 Renamed columns: {rename_dict}")
        
        return df
    
    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse date column with multiple format support.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: DataFrame with parsed dates
        """
        df = df.copy()
        
        if 'date' not in df.columns:
            return df
        
        # Try multiple date formats
        date_formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%m/%d/%Y',           # 01/15/2024
            '%d/%m/%Y',           # 15/01/2024
            '%Y/%m/%d',           # 2024/01/15
            '%Y%m%d',             # 20240115
            '%d-%m-%Y',           # 15-01-2024
        ]
        
        # First, try pandas automatic parsing
        try:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if df['date'].isna().sum() == 0:
                if self.verbose:
                    print(f"   📅 Parsed dates automatically")
                return df
        except:
            pass
        
        # Try each format manually
        for fmt in date_formats:
            try:
                df['date'] = pd.to_datetime(df['date'], format=fmt, errors='coerce')
                if df['date'].isna().sum() == 0:
                    if self.verbose:
                        print(f"   📅 Parsed dates with format: {fmt}")
                    return df
            except:
                continue
        
        # If still not parsed, raise warning
        if df['date'].isna().sum() > 0:
            pct_failed = (df['date'].isna().sum() / len(df)) * 100
            print(f"   ⚠️  Warning: {pct_failed:.1f}% of dates failed to parse")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """
        Handle missing values based on source type.
        
        Args:
            df (pd.DataFrame): Input dataframe
            source_type (str): Type of data source
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        df = df.copy()
        
        # Sales-specific handling
        if source_type == 'sales':
            # If quantity is missing but revenue exists, impute quantity = 1
            if 'quantity' in df.columns and 'revenue' in df.columns:
                missing_qty = df['quantity'].isna()
                if missing_qty.sum() > 0:
                    df.loc[missing_qty, 'quantity'] = 1.0
                    if self.verbose:
                        print(f"   🔧 Imputed {missing_qty.sum()} missing quantity values with 1.0")
            
            # If revenue is missing, drop rows (critical column)
            if 'revenue' in df.columns:
                missing_revenue = df['revenue'].isna()
                if missing_revenue.sum() > 0:
                    df = df[~missing_revenue]
                    if self.verbose:
                        print(f"   🗑️  Dropped {missing_revenue.sum()} rows with missing revenue")
        
        # Inventory-specific handling
        elif source_type == 'inventory':
            # If stock_level is missing, impute with 0
            if 'stock_level' in df.columns:
                missing_stock = df['stock_level'].isna()
                if missing_stock.sum() > 0:
                    df.loc[missing_stock, 'stock_level'] = 0.0
                    if self.verbose:
                        print(f"   🔧 Imputed {missing_stock.sum()} missing stock_level with 0.0")
        
        # Macro-specific handling
        elif source_type == 'macro':
            # If value is missing, drop rows
            if 'value' in df.columns:
                missing_value = df['value'].isna()
                if missing_value.sum() > 0:
                    df = df[~missing_value]
                    if self.verbose:
                        print(f"   🗑️  Dropped {missing_value.sum()} rows with missing value")
        
        return df
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def detect_source_type(self, df: pd.DataFrame) -> str:
        """
        Auto-detect source type based on columns.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            str: Detected source type ('sales', 'inventory', or 'macro')
        """
        cols_lower = [c.lower() for c in df.columns]
        
        # Check for sales indicators
        sales_indicators = ['revenue', 'sales', 'amount', 'sale_amount']
        if any(indicator in cols_lower for indicator in sales_indicators):
            return 'sales'
        
        # Check for inventory indicators
        inventory_indicators = ['stock', 'inventory', 'stock_level']
        if any(indicator in cols_lower for indicator in inventory_indicators):
            return 'inventory'
        
        # Check for macro indicators
        macro_indicators = ['indicator', 'metric', 'value', 'measure']
        if any(indicator in cols_lower for indicator in macro_indicators):
            return 'macro'
        
        # Default to sales
        return 'sales'
    
    def get_column_mapping(self, df: pd.DataFrame, source_type: str) -> Dict[str, str]:
        """
        Get the column mapping that would be applied.
        
        Args:
            df (pd.DataFrame): Input dataframe
            source_type (str): Source type
            
        Returns:
            Dict: Mapping of original → standard column names
        """
        if source_type == 'sales':
            column_map = self.SALES_COLUMN_MAP
        elif source_type == 'inventory':
            column_map = self.INVENTORY_COLUMN_MAP
        elif source_type == 'macro':
            column_map = self.MACRO_COLUMN_MAP
        else:
            return {}
        
        rename_dict = {}
        for standard_name, possible_names in column_map.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    rename_dict[possible_name] = standard_name
                    break
        
        return rename_dict


# ============================================================================
# STANDALONE USAGE
# ============================================================================

if __name__ == "__main__":
    print("R-DIOS Schema Harmonizer Module v3.0")
    
    # Example: Harmonize a sample sales dataset
    sample_data = {
        'transaction_date': ['2024-01-15', '2024-01-16'],
        'store_nbr': ['001', '001'],
        'item_id': ['PROD_A', 'PROD_B'],
        'units_sold': [10, 15],
        'sale_amount': [100.50, 225.75]
    }
    
    df = pd.DataFrame(sample_data)
    print("\nOriginal DataFrame:")
    print(df)
    
    harmonizer = SchemaHarmonizer()
    df_harmonized = harmonizer.harmonize_schema(df, 'sales')
    
    print("\nHarmonized DataFrame:")
    print(df_harmonized)
    print(f"\nColumn types:\n{df_harmonized.dtypes}")
