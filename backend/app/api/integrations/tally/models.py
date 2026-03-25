"""
Tally Integration — Pydantic models
Describes the data contracts between R-DIOS and Tally ERP.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


# ─── Export models (R-DIOS → Tally) ────────────────────────────────────────────

class TallyVoucherLineItem(BaseModel):
    """Single line item within a Tally sales voucher."""
    product_name: str
    stock_item_name: str          # Must match Tally stock item name exactly
    quantity: float = 1.0
    unit: str = "Nos"
    rate: Decimal                 # Price per unit (excl. GST)
    amount: Decimal               # = quantity × rate
    gst_rate: float = 0.0        # Total GST % (e.g. 18)
    hsn_code: str = ""
    # Computed tax splits (filled automatically)
    cgst_amount: Decimal = Decimal("0")
    sgst_amount: Decimal = Decimal("0")
    igst_amount: Decimal = Decimal("0")

    def compute_taxes(self, is_interstate: bool = False) -> None:
        """Populate tax amounts from gst_rate and amount."""
        gst_amount = self.amount * Decimal(str(self.gst_rate)) / 100
        if is_interstate:
            self.igst_amount = gst_amount
            self.cgst_amount = Decimal("0")
            self.sgst_amount = Decimal("0")
        else:
            self.cgst_amount = gst_amount / 2
            self.sgst_amount = gst_amount / 2
            self.igst_amount = Decimal("0")


class TallySaleVoucher(BaseModel):
    """Sales voucher to be pushed to Tally."""
    invoice_number: str
    invoice_date: date
    customer_ledger_name: str
    is_interstate: bool = False
    narration: str = ""
    items: List[TallyVoucherLineItem]
    # Totals (auto-populated from items if not provided)
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None

    def compute_totals(self) -> None:
        """Recompute all tax totals from line items."""
        for item in self.items:
            item.compute_taxes(self.is_interstate)
        self.taxable_amount = sum((i.amount for i in self.items), Decimal("0"))
        self.cgst_amount   = sum((i.cgst_amount for i in self.items), Decimal("0"))
        self.sgst_amount   = sum((i.sgst_amount for i in self.items), Decimal("0"))
        self.igst_amount   = sum((i.igst_amount for i in self.items), Decimal("0"))
        self.grand_total   = (
            (self.taxable_amount or Decimal("0"))
            + (self.cgst_amount or Decimal("0"))
            + (self.sgst_amount or Decimal("0"))
            + (self.igst_amount or Decimal("0"))
        )


# ─── Import models (Tally → R-DIOS) ────────────────────────────────────────────

class TallyLedger(BaseModel):
    """Ledger account imported from Tally."""
    name: str
    guid: str = ""
    group: str = ""                     # e.g. 'Sundry Debtors', 'Bank Accounts'
    gstin: str = ""
    gst_registration_type: str = ""    # Regular / Composition / Unregistered
    opening_balance: float = 0.0
    # Derived
    is_customer: bool = False
    is_supplier: bool = False

    def classify(self) -> None:
        """Classify ledger based on Tally group."""
        debtor_groups = {"Sundry Debtors", "Debtors"}
        creditor_groups = {"Sundry Creditors", "Creditors"}
        self.is_customer = self.group in debtor_groups
        self.is_supplier = self.group in creditor_groups


class TallyStockItem(BaseModel):
    """Stock item imported from Tally."""
    name: str
    guid: str = ""
    category: str = ""             # Tally parent group
    unit: str = "Nos"
    hsn_code: str = ""
    gst_applicable: bool = False
    gst_rate: float = 0.0          # Combined GST % (e.g. 18)


class TallyVoucher(BaseModel):
    """Generic Tally voucher returned on import."""
    voucher_number: str
    voucher_type: str             # Sales, Purchase, Receipt, Payment
    date: date
    party_ledger: str
    amount: float
    narration: str = ""
    guid: str = ""


# ─── Status / response models ───────────────────────────────────────────────────

class TallyConnectionStatus(BaseModel):
    """Result of a Tally connectivity check."""
    connected: bool
    host: str
    port: int
    company_name: Optional[str] = None
    company_guid: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None


class TallySyncResult(BaseModel):
    """Summary returned after a sync operation."""
    success: bool
    operation: str                  # 'sync-sales', 'sync-invoices', 'import-ledgers', etc.
    timestamp: datetime = Field(default_factory=datetime.now)
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: List[str] = []
    message: str = ""
