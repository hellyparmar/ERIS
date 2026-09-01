"""
Backward-compatible re-export of the canonical Customer model.
Avoids duplicate class registration in the SQLAlchemy declarative base.
"""
from app.models.customers import Customer as _Customer

# Mypy / IDE hint: treat this module-level name as the class itself
Customer = _Customer
__all__ = ["Customer"]
