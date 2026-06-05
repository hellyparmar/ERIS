"""
Data module for ML pipeline.
"""

from .generate_sales_data import SalesDataGenerator, generate_sales_data

__all__ = ["SalesDataGenerator", "generate_sales_data"]
