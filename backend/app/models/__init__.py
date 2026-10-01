# Import all models to ensure they are registered with SQLAlchemy

from .base import Base
from .users import User, UserRoleEnum as UserRole, Role, UserOutletAccess
from .organization import Organization
from .outlet import Outlet
from .customers import Customer
from .commerce import Product
from .inventory import Inventory
from .commerce import Sale, Sale as SaleTransaction, SaleItem
from .commerce import Supplier
from .invoicing import Invoice, InvoiceLineItem, InvoiceTax, Payment
from .alert import Alert, AlertType, AlertSeverity
from .forecast import ForecastResult
from .chat import ChatMessage
from .audit import AuditLogEntry

__all__ = [
    "Base",
    "User",
    "UserRole",
    "Role",
    "UserOutletAccess",
    "Outlet",
    "Customer",
    "Product",
    "Inventory",
    "SaleTransaction",
    "Sale",
    "SaleItem",
    "Supplier",
    "Organization",
    "Invoice",
    "Alert",
    "AlertType",
    "AlertSeverity",
    "ForecastResult",
    "ChatMessage",
    "InvoiceLineItem",
    "InvoiceTax",
    "Payment",
    "AuditLogEntry",
]
