"""
Compatibility shim for legacy imports of multitenant models.

This module previously contained duplicate class definitions (Organization, Store, User, etc.)
which conflicted with the canonical models in app.models.organization, app.models.users etc.

Now it re-exports those classes to maintain existing import paths while avoiding
SQLAlchemy duplicate table registration errors.

For older models imported from app.models.models or app.models.models_v6, we also
re-export those here for backward compatibility.
"""

from app.models.organization import Organization, Store
from app.models.users import User, UserRoleEnum as UserRole, Role
Permission = None
UserStore = None
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.schema import Category
from app.models.customers import Customer
from app.models.invoicing import Invoice
from app.models.sale import Sale, SaleItem, Refund
from app.models.alert import Alert

# Aliasing for older imports that expect "Inventory"
# Inventory is already imported from inventory.py

# Re-export enums that might be imported from here
StoreType = None
from app.models.users import UserRoleEnum

# Legacy re-exports from app.models.models and app.models.models_v6
# These are imported to satisfy imports in app.models.models (line 44)
# which tries to import Supplier, PurchaseOrder, PurchaseOrderItem from here
try:
    from app.models.supplier import Supplier
    from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
except (ImportError, ModuleNotFoundError):
    Supplier = None
    PurchaseOrder = None
    PurchaseOrderItem = None

# PaymentStatus enum alias
try:
    # Try to import from schema.py where it's properly defined
    from app.models.schema import PaymentStatusEnum as PaymentStatus
except (ImportError, ModuleNotFoundError):
    # Fallback if PaymentStatus isn't defined
    from enum import Enum
    class PaymentStatus(Enum):
        PAID = "paid"
        PENDING = "pending"
        PARTIAL = "partial"
        FAILED = "failed"
        REFUNDED = "refunded"
        PARTIAL = "partial"
        PENDING = "pending"
        OVERDUE = "overdue"

__all__ = [
    "Organization", "Store",
    "User", "UserRole", "Role", "Permission", "UserStore",
    "Category", "Product", "StoreInventory", "Inventory",
    "Customer", "Invoice", "Sale", "SaleItem", "Refund", "Alert",
    "StoreType",
    "Supplier", "PurchaseOrder", "PurchaseOrderItem", "PaymentStatus",
]
