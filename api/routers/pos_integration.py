"""
POS to Invoice Integration Endpoints
Handles conversion of POS transactions to formal invoices
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from api.db.database_postgres import get_db
from api.services.pos_invoice_service import POSInvoiceService, POSInvoiceAnalytics

router = APIRouter(prefix="/api/v1/invoicing", tags=["POS Integration"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class POSToInvoiceRequest(BaseModel):
    """Convert POS sales to invoice"""
    transaction_id: str
    customer_id: Optional[int] = None
    invoice_type: str = "sales_invoice"
    notes: Optional[str] = None


class BulkConvertRequest(BaseModel):
    """Bulk convert multiple POS transactions"""
    transaction_ids: List[str]
    group_by_customer: bool = True


class LinkSalesToInvoiceRequest(BaseModel):
    """Link existing sales to an invoice"""
    invoice_id: int
    transaction_ids: List[str]


class ConversionMetricsResponse(BaseModel):
    """Conversion metrics response"""
    period_days: int
    total_sales: int
    invoiced_sales: int
    uninvoiced_sales: int
    conversion_rate_percent: float
    total_revenue: float
    invoiced_revenue: float
    uninvoiced_revenue: float


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/sales-to-invoice")
async def convert_sales_to_invoice(
    request: POSToInvoiceRequest,
    db: Session = Depends(get_db)
):
    """
    Convert a POS transaction to a formal invoice
    
    Creates an invoice from all sales records with the same transaction_id.
    Automatically:
    - Groups all line items from the transaction
    - Calculates taxes and totals
    - Creates invoice line items
    - Links sales to invoice
    
    Args:
        request: Transaction ID and invoice details
        
    Returns:
        Created invoice with details
    """
    result = POSInvoiceService.convert_sales_to_invoice(
        transaction_id=request.transaction_id,
        db=db,
        customer_id=request.customer_id,
        invoice_type=request.invoice_type,
        notes=request.notes
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.post("/bulk-sales-to-invoices")
async def bulk_convert_sales(
    request: BulkConvertRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk convert multiple POS transactions to invoices
    
    Can optionally group items by customer into single invoices.
    
    Args:
        request: List of transaction IDs
        
    Returns:
        Batch conversion results with success/failure counts
    """
    result = POSInvoiceService.bulk_convert_sales_to_invoices(
        transaction_ids=request.transaction_ids,
        db=db,
        group_by_customer=request.group_by_customer
    )
    
    return {
        "success": True,
        "data": result
    }


@router.post("/link-sales-to-invoice")
async def link_sales_to_invoice(
    request: LinkSalesToInvoiceRequest,
    db: Session = Depends(get_db)
):
    """
    Link existing POS sales to an invoice
    
    Associates already-created sales records with an invoice without
    creating a new invoice. Useful for adding items to existing invoices.
    
    Args:
        request: Invoice ID and transaction IDs to link
        
    Returns:
        Link operation result
    """
    result = POSInvoiceService.link_existing_sales_to_invoices(
        invoice_id=request.invoice_id,
        transaction_ids=request.transaction_ids,
        db=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/uninvoiced-sales")
async def get_uninvoiced_sales(
    customer_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get sales that haven't been converted to invoices
    
    Returns transactions from the last N days that don't have
    an associated invoice yet.
    
    Args:
        customer_id: Optional filter by customer ID
        days: Look back this many days (1-365, default 30)
        
    Returns:
        List of uninvoiced transactions grouped
    """
    result = POSInvoiceService.get_uninvoiced_sales(
        db=db,
        customer_id=customer_id,
        days=days
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/conversion-metrics")
async def get_conversion_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get POS-to-Invoice conversion metrics
    
    Returns statistics on how many sales have been converted
    to invoices, conversion rates, and revenue tracking.
    
    Args:
        days: Analysis period in days (1-365, default 30)
        
    Returns:
        Conversion metrics and statistics
    """
    result = POSInvoiceAnalytics.get_conversion_metrics(db=db, days=days)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "data": result["data"]
    }


@router.get("/sales-pending-invoicing")
async def get_sales_pending_invoicing(
    customer_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of sales pending invoicing
    
    Returns uninvoiced sales in a paginated format for
    the invoicing workflow.
    
    Args:
        customer_id: Optional customer filter
        limit: Maximum number of records to return
        
    Returns:
        Paginated list of pending sales
    """
    result = POSInvoiceService.get_uninvoiced_sales(
        db=db,
        customer_id=customer_id,
        days=365  # Full year lookback
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Paginate results
    transactions = result["data"]["transactions"][:limit]
    
    return {
        "success": True,
        "data": {
            "total_available": result["data"]["total_transactions"],
            "returned": len(transactions),
            "limit": limit,
            "transactions": transactions
        }
    }


@router.post("/auto-invoice-pending-sales")
async def auto_invoice_pending_sales(
    days: int = Query(7, ge=1, le=30),
    group_by_customer: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Automatically create invoices for all pending sales
    
    Creates invoices for all uninvoiced sales from the last N days.
    Can optionally group by customer into single invoices.
    
    Args:
        days: Process sales from last N days
        group_by_customer: Group items by customer
        
    Returns:
        Auto-invoicing results
    """
    # Get pending sales
    pending_result = POSInvoiceService.get_uninvoiced_sales(
        db=db,
        customer_id=None,
        days=days
    )
    
    if not pending_result["success"]:
        raise HTTPException(status_code=400, detail=pending_result["error"])
    
    transaction_ids = [t["transaction_id"] for t in pending_result["data"]["transactions"]]
    
    if not transaction_ids:
        return {
            "success": True,
            "data": {
                "message": "No pending sales to invoice",
                "invoices_created": 0,
                "total_amount": 0
            }
        }
    
    # Bulk convert
    result = POSInvoiceService.bulk_convert_sales_to_invoices(
        transaction_ids=transaction_ids,
        db=db,
        group_by_customer=group_by_customer
    )
    
    total_amount = sum(inv["total_amount"] for inv in result["invoices"])
    
    return {
        "success": True,
        "data": {
            "message": f"Created {result['successful']} invoices",
            "invoices_created": result["successful"],
            "invoices_failed": result["failed"],
            "total_amount": total_amount,
            "invoices": result["invoices"],
            "errors": result["errors"] if result["errors"] else None
        }
    }
