# Re-export database utilities and models for backward compatibility
from app.database import get_db, engine
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

# For backward compatibility with code that imports specific models under different names
Sale = SaleTransaction
SaleItem = None  # Not in consolidated models
Customer = User  # Fallback
Message = ChatMessage
MessageChannel = None
PaymentStatus = None
LoyaltyPoints = None

__all__ = [
    "get_db",
    "engine",
    "Base",
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
    "ChatMessage", "Message", "MessageChannel",
    "PaymentStatus",
    "LoyaltyPoints",
]
