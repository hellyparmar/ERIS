"""
Backward-compatible re-exports for legacy app.api.db.models references.
Maps all model names to their canonical implementations under app.models.
"""
from app.models.models_v6 import SaleItem, Product, Sale, Supplier, PurchaseOrder, PurchaseOrderItem
from app.models.loyalty import LoyaltyAccount, LoyaltyPoints, LoyaltyBonus
from app.models.odoo_config import OdooConfig
from app.models.payment_status import PaymentStatus
from app.models.community import CommunityListing
from app.models.customers import Customer
from app.models.inventory import Inventory
from app.models.users import User, Role

__all__ = [
    "SaleItem",
    "LoyaltyAccount",
    "LoyaltyPoints",
    "LoyaltyBonus",
    "OdooConfig",
    "PaymentStatus",
    "CommunityListing",
    "Customer",
    "Product",
    "Sale",
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "Inventory",
    "User",
    "Role",
]
