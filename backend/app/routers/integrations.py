"""
Integrations Router — Tally ERP sync endpoints
Routes: /integrations/tally/*
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from app.middleware.auth import get_current_user
from app.models.multitenant_models import User

from app.api.integrations.tally.sync_service import TallySyncService
from app.api.integrations.tally.models import TallyConnectionStatus, TallySyncResult

router = APIRouter(
    prefix="/api/v1/integrations/tally",
    tags=["Tally Integration"],
)

# ─── Helpers ─────────────────────────────────────────────────────────────────────

def _get_service(host: str, port: int) -> TallySyncService:
    """Instantiate sync service with given or env-default connection."""
    return TallySyncService(
        host=host or os.getenv("TALLY_HOST", "localhost"),
        port=port or int(os.getenv("TALLY_PORT", "9000")),
        company_name=os.getenv("TALLY_COMPANY_NAME", ""),
    )


# ─── Request schemas ─────────────────────────────────────────────────────────────

class TallyHost(BaseModel):
    host: str = "localhost"
    port: int = 9000

class SaleExportItem(BaseModel):
    name: str
    tally_item_name: Optional[str] = None
    qty: float = 1
    rate: float = 0
    amount: float = 0
    gst_rate: float = 0
    hsn_code: str = ""
    unit: str = "Nos"

class SaleExportRequest(BaseModel):
    invoice_number: str
    sale_date: Optional[str] = None         # ISO date string
    customer_name: Optional[str] = "Cash"
    is_interstate: bool = False
    items: List[SaleExportItem]

class InvoiceExportRequest(BaseModel):
    invoice_number: str
    invoice_date: Optional[str] = None
    customer_name: Optional[str] = "Cash"
    taxable_amount: float = 0
    cgst_amount: float = 0
    sgst_amount: float = 0
    igst_amount: float = 0
    grand_total: float = 0


# ─── Status ──────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=TallyConnectionStatus, summary="Get Tally connection status")
async def get_tally_status(
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
    current_user: User = Depends(get_current_user)
):
    """
    Ping the Tally server and return connection status + company details.
    Use this to verify that Tally is running before triggering a sync.
    """
    svc = _get_service(host, port)
    return svc.check_status()


# ─── Export: R-DIOS → Tally ──────────────────────────────────────────────────────

@router.post("/sync-sales", response_model=TallySyncResult, summary="Export POS sales to Tally")
async def sync_sales_to_tally(
    request: SaleExportRequest,
    background_tasks: BackgroundTasks,
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
    current_user: User = Depends(get_current_user)
):
    """
    Export a single POS sale from R-DIOS to Tally as a Sales Voucher.

    The voucher includes:
    - Party ledger entry (customer debit)
    - Sales ledger entry (credit)
    - CGST / SGST / IGST ledger splits
    - Inventory entries per line item
    """
    svc = _get_service(host, port)
    sale_dict = {
        "invoice_number": request.invoice_number,
        "sale_date": request.sale_date,
        "customer_name": request.customer_name,
        "is_interstate": request.is_interstate,
        "items": [item.dict() for item in request.items],
    }
    result = svc.export_sale(sale_dict)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.dict())
    return result


@router.post("/sync-invoices", response_model=TallySyncResult, summary="Export GST invoice to Tally")
async def sync_invoice_to_tally(
    request: InvoiceExportRequest,
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
    current_user: User = Depends(get_current_user)
):
    """
    Export a GST invoice from R-DIOS to Tally as a Sales Voucher.

    Use for formal B2B invoices where the full GST breakdown is known.
    """
    svc = _get_service(host, port)
    result = svc.export_invoice(request.dict())
    if not result.success:
        raise HTTPException(status_code=502, detail=result.dict())
    return result


# ─── Import: Tally → R-DIOS ──────────────────────────────────────────────────────

@router.post("/import-ledgers", response_model=TallySyncResult, summary="Import ledgers from Tally")
async def import_ledgers_from_tally(
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
):
    """
    Fetch all ledgers from Tally (sundry debtors, creditors, bank accounts, etc.).
    Returns a summary of how many were fetched.
    """
    svc = _get_service(host, port)
    return svc.import_ledgers()


@router.post("/import-stock-items", response_model=TallySyncResult, summary="Import stock items from Tally")
async def import_stock_items_from_tally(
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
):
    """
    Fetch all stock items (products) from Tally.
    Includes HSN code, GST applicability, and unit of measurement.
    """
    svc = _get_service(host, port)
    return svc.import_stock_items()


@router.post("/import-vouchers", response_model=TallySyncResult, summary="Import vouchers from Tally")
async def import_vouchers_from_tally(
    voucher_type: str = Query(default="Sales"),
    from_date: Optional[str] = Query(default=None, description="ISO date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(default=None),
    host: str = Query(default="localhost"),
    port: int = Query(default=9000),
):
    """
    Import vouchers from Tally for a given date range.
    Useful for reconciling R-DIOS and Tally books.
    """
    svc = _get_service(host, port)
    fd = datetime.fromisoformat(from_date).date() if from_date else None
    td = datetime.fromisoformat(to_date).date() if to_date else None
    return svc.import_vouchers(voucher_type=voucher_type, from_date=fd, to_date=td)
