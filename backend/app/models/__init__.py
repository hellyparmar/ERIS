"""
models/__init__.py
Registers all ORM models with the shared Base so that Alembic and init_db()
can discover them in one import.
"""

from .base import Base  # noqa: F401

# Order matters for FK resolution: parents before children
from .organization import Organization, Store             # noqa: F401
from .users        import Permission, Role, User, UserStore  # noqa: F401
from .product      import Category, Product, StoreInventory  # noqa: F401
from .sale         import Sale, SaleItem, Refund          # noqa: F401
from .alert        import Alert                           # noqa: F401

__all__ = [
    "Base",
    # Organization
    "Organization", "Store",
    # Users / RBAC
    "Permission", "Role", "User", "UserStore",
    # Products
    "Category", "Product", "StoreInventory",
    # Sales
    "Sale", "SaleItem", "Refund",
    # Alerts
    "Alert",
]
