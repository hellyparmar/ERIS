"""
Enterprise Retail Intelligence System v3.0
R-DIOS DATA SCHEMAS

Pandera schema definitions for data validation across all data sources.
Ensures data quality and consistency before feature engineering.

Author: R-DIOS Team
Version: 3.0.0
"""

import pandera as pa
from pandera import Column, DataFrameSchema, Check
import pandas as pd


# ============================================================================
# SALES DATA SCHEMA (Layer 1)
# ============================================================================

SalesDataSchema = DataFrameSchema(
    {
        "date": Column(
            pa.DateTime,
            checks=[
                Check.greater_than_or_equal_to(pd.Timestamp("2020-01-01")),
                Check.less_than_or_equal_to(pd.Timestamp("2026-12-31"))
            ],
            nullable=False,
            description="Transaction date"
        ),
        "store_id": Column(
            pa.String,
            checks=Check(lambda s: s.str.len() > 0),
            nullable=False,
            description="Unique store identifier"
        ),
        "product_id": Column(
            pa.String,
            checks=Check(lambda s: s.str.len() > 0),
            nullable=False,
            description="Unique product identifier"
        ),
        "quantity": Column(
            pa.Float,
            checks=Check.greater_than_or_equal_to(0),
            nullable=True,  # Some datasets may not have quantity
            description="Units sold"
        ),
        "revenue": Column(
            pa.Float,
            checks=Check.greater_than_or_equal_to(0),
            nullable=False,
            description="Sales revenue"
        )
    },
    strict=False,  # Allow additional columns (will be dropped later)
    coerce=True    # Attempt type coercion
)


# ============================================================================
# INVENTORY DATA SCHEMA (Layer 2)
# ============================================================================

InventoryDataSchema = DataFrameSchema(
    {
        "date": Column(
            pa.DateTime,
            checks=[
                Check.greater_than_or_equal_to(pd.Timestamp("2020-01-01")),
                Check.less_than_or_equal_to(pd.Timestamp("2026-12-31"))
            ],
            nullable=False,
            description="Inventory snapshot date"
        ),
        "store_id": Column(
            pa.String,
            checks=Check(lambda s: s.str.len() > 0),
            nullable=False,
            description="Unique store identifier"
        ),
        "product_id": Column(
            pa.String,
            checks=Check(lambda s: s.str.len() > 0),
            nullable=False,
            description="Unique product identifier"
        ),
        "stock_level": Column(
            pa.Float,
            checks=Check.greater_than_or_equal_to(0),
            nullable=False,
            description="Current inventory level"
        ),
        "reorder_point": Column(
            pa.Float,
            checks=Check.greater_than_or_equal_to(0),
            nullable=True,
            description="Minimum stock before reorder"
        )
    },
    strict=False,
    coerce=True
)


# ============================================================================
# MACROECONOMIC DATA SCHEMA (Layer 3)
# ============================================================================

MacroDataSchema = DataFrameSchema(
    {
        "date": Column(
            pa.DateTime,
            checks=[
                Check.greater_than_or_equal_to(pd.Timestamp("2020-01-01")),
                Check.less_than_or_equal_to(pd.Timestamp("2026-12-31"))
            ],
            nullable=False,
            description="Indicator measurement date"
        ),
        "indicator_name": Column(
            pa.String,
            checks=Check(lambda s: s.str.len() > 0),
            nullable=False,
            description="Name of economic indicator"
        ),
        "value": Column(
            pa.Float,
            nullable=False,
            description="Indicator value"
        ),
        "region": Column(
            pa.String,
            nullable=True,
            description="Geographic region (optional)"
        )
    },
    strict=False,
    coerce=True
)


# ============================================================================
# TRAINING DATA SCHEMA (Merged Layers)
# ============================================================================

TrainingDataSchema = DataFrameSchema(
    {
        "date": Column(pa.DateTime, nullable=False),
        "store_id": Column(pa.String, nullable=False),
        "product_id": Column(pa.String, nullable=False),
        "sales": Column(pa.Float, checks=Check.greater_than_or_equal_to(0), nullable=False),
        "quantity": Column(pa.Float, nullable=True),
        "stock_level": Column(pa.Float, nullable=True),
        # Macroeconomic features will be added during feature engineering
    },
    strict=False,
    coerce=True
)


# ============================================================================
# SCHEMA VALIDATION UTILITIES
# ============================================================================

def validate_dataframe(df, schema, dataset_name="Unknown"):
    """
    Validate a dataframe against a pandera schema.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        schema (DataFrameSchema): Pandera schema
        dataset_name (str): Name for error reporting
        
    Returns:
        pd.DataFrame: Validated and coerced dataframe
        
    Raises:
        pa.errors.SchemaError: If validation fails
    """
    try:
        validated_df = schema.validate(df, lazy=True)
        print(f"✅ {dataset_name}: Schema validation passed")
        return validated_df
    except pa.errors.SchemaError as e:
        print(f"❌ {dataset_name}: Schema validation failed")
        print(f"   Errors: {e.failure_cases}")
        raise


def get_schema_summary(schema):
    """
    Print a human-readable summary of a schema.
    
    Args:
        schema (DataFrameSchema): Pandera schema to summarize
    """
    print("\n" + "="*80)
    print(f"SCHEMA: {schema.name if hasattr(schema, 'name') else 'Unnamed'}")
    print("="*80)
    
    for col_name, col_schema in schema.columns.items():
        nullable = "nullable" if col_schema.nullable else "required"
        dtype = col_schema.dtype
        print(f"  • {col_name:20s} [{dtype}] ({nullable})")
        
        if col_schema.checks:
            for check in col_schema.checks:
                print(f"    ↳ Check: {check}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    print("R-DIOS Schema Validation Module v3.0")
    print("\nAvailable Schemas:")
    print("  1. SalesDataSchema (Layer 1)")
    print("  2. InventoryDataSchema (Layer 2)")
    print("  3. MacroDataSchema (Layer 3)")
    print("  4. TrainingDataSchema (Merged)")
    
    # Example usage
    print("\n" + "="*80)
    print("SALES DATA SCHEMA")
    print("="*80)
    get_schema_summary(SalesDataSchema)
