"""
sales.py - Sales Model
Re-exports canonical Sale model from app.models.models_v6 to avoid multiple Declarative Base registries.
"""
from app.models.models_v6 import Sale as SaleTransaction, SaleItem

__all__ = ["SaleTransaction", "SaleItem"]