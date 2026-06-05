# Re-export models from main models module
from app.models import (
    Base,
    User, UserRole,
    Outlet,
    Product,
    Inventory,
    SaleTransaction,
    Supplier,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus,
    Invoice,
    Alert, AlertType, AlertSeverity,
    Forecast, ForecastType, ForecastResult,
    ChatMessage,
)

# Aliases for backward compatibility
Sale = SaleTransaction
Message = ChatMessage

# Stub classes for models that don't exist in consolidated schema
class SaleItem:
    """Stub for SaleItem model not in consolidated schema"""
    pass

class MessageChannel:
    """Stub for MessageChannel model"""
    pass

class PaymentStatus:
    """Stub for PaymentStatus model"""
    pass

class LoyaltyPoints:
    """Stub for LoyaltyPoints model"""
    pass

__all__ = [
    "User", "UserRole", "Customer",
    "Outlet",
    "Product",
    "Inventory",
    "Sale", "SaleTransaction", "SaleItem",
    "Supplier",
    "PurchaseOrder", "PurchaseOrderItem", "PurchaseOrderStatus",
    "Invoice",
    "Alert", "AlertType", "AlertSeverity",
    "Forecast", "ForecastType", "ForecastResult",
    "Message", "ChatMessage", "MessageChannel",
    "PaymentStatus",
    "LoyaltyPoints",
]
