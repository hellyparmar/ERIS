# Import all models to ensure they are registered with SQLAlchemy

from .base import Base
from .users import User, UserRoleEnum as UserRole, Role
from .organization import Store, Organization
from .outlet import Outlet
from .customers import Customer
from .product import Product
from .inventory import Inventory
from .sales import SaleTransaction
from .sale import Sale
from .employee_models import Employee
from .supplier import Supplier
from .purchase_order import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus
from .invoicing import Invoice
from .alert import Alert, AlertType, AlertSeverity
from .forecast import Forecast, ForecastType, ForecastResult
from .chat import ChatMessage
from .business_contact import BusinessContact
# Temporarily disabled - Phase 2 models have FK issues with current database schema
# from .phase2_models import Phase2Business, Phase2Customer, Phase2Product, Phase2Invoice, InvoiceLineItem, InvoicePayment, CustomerCredit, CreditTransaction, CreditReminder, GSTConfiguration
# from .models import (
#     BusinessContact, Sale, Employee, SalesFactor, 
#     AlertType as ModelsAlertType, AlertStatus, ContactType, 
#     InvoiceStatus, EmployeeShift, ForecastType as ModelsForecastType, MessageRole
# )

__all__ = [
    "Base",
    "User", "UserRole", "Role",
    "Outlet",
    "Customer",
    "Product",
    "Inventory",
    "SaleTransaction",
    "Sale",
    "Employee",
    "Supplier",
    "Store", "Organization",
    "PurchaseOrder", "PurchaseOrderItem", "PurchaseOrderStatus",
    "Invoice",
    "Alert", "AlertType", "AlertSeverity",
    "Forecast", "ForecastType", "ForecastResult",
    "ChatMessage",
    # Phase 2 models disabled
    # "Phase2Business", "Phase2Customer", "Phase2Product", "Phase2Invoice", "InvoiceLineItem", "InvoicePayment", "CustomerCredit", "CreditTransaction", "CreditReminder", "GSTConfiguration",
    "BusinessContact",
    # "Sale", "Employee", "SalesFactor",
    # "ModelsAlertType", "AlertStatus", "ContactType", "InvoiceStatus", "EmployeeShift", "ModelsForecastType", "MessageRole",
]
