# Import all models to ensure they are registered with SQLAlchemy

from .base import Base
from .users import User, UserRoleEnum as UserRole, Role, UserOutletAccess
from .organization import Organization
from .outlet import Outlet
from .customers import Customer
from .models_v6 import Product
from .inventory import Inventory
from .sales import SaleTransaction, SaleItem
from .models_v6 import Sale
from .employee_models import Employee
from .models_v6 import Supplier
from .models_v6 import PurchaseOrder, PurchaseOrderItem
from .purchase_order import PurchaseOrderStatus
from .invoicing import Invoice
from .invoicing_models import InvoiceTax, Payment, GSTRate, Bill, CreditNote, DebitNote
from .invoicing_models import InvoiceLineItem
from .payment_status import PaymentStatus
from .loyalty import LoyaltyAccount, LoyaltyPoints, LoyaltyBonus
from .odoo_config import OdooConfig
from .community import CommunityListing
from .alert import Alert, AlertType, AlertSeverity
from .forecast import Forecast, ForecastType, ForecastResult
from .chat import ChatMessage
from .business_contact import BusinessContact
from .communication import Message, MessageChannel
from .audit import AuditLogEntry

__all__ = [
    "Base",
    "User", "UserRole", "Role", "UserOutletAccess",
    "Outlet",
    "Customer",
    "Product",
    "Inventory",
    "SaleTransaction",
    "Sale",
    "SaleItem",
    "Employee",
    "Supplier",
    "Organization",
    "PurchaseOrder", "PurchaseOrderItem", "PurchaseOrderStatus",
    "Invoice",
    "Alert", "AlertType", "AlertSeverity",
    "Forecast", "ForecastType", "ForecastResult",
    "ChatMessage",
    "InvoiceLineItem", "InvoiceTax", "Payment", "PaymentStatus", "GSTRate", "Bill", "CreditNote", "DebitNote",
    "LoyaltyAccount", "LoyaltyPoints", "LoyaltyBonus",
    "OdooConfig",
    "CommunityListing",
    "BusinessContact",
    "Message", "MessageChannel", "AuditLogEntry",
]
