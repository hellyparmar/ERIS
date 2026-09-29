"""
sale.py - Sale and SaleItem Models
MSc Data Science Project - Enterprise Retail Intelligence System

Covers POS transactions with itemised lines, tax, discounts, and payment tracking.
"""

import enum
from sqlalchemy import (
    Column, String, ForeignKey,
    Integer, DateTime, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class SalePaymentStatus(enum.Enum):
    PAID     = "paid"
    PARTIAL  = "partial"
    PENDING  = "pending"
    REFUNDED = "refunded"
    VOID     = "void"


class PaymentMethod(enum.Enum):
    CASH    = "cash"
    CARD    = "card"
    UPI     = "upi"
    NEFT    = "neft"
    WALLET  = "wallet"


class SaleChannel(enum.Enum):
    POS      = "pos"
    ONLINE   = "online"
    PHONE    = "phone"
    MANUAL   = "manual"


# ── Sale ──────────────────────────────────────────────────────────────────────
