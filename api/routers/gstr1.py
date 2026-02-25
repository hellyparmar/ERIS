"""
GSTR-1 Export Router
Uses gstr1_service for report generation and validation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from api.db import get_db
from api.services import gstr1_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gst", tags=["GST Compliance"])


@router.get("/gstr1")
async def get_gstr1_export(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db)
):
    """
    Generate GSTR-1 report for a given month/year.
    Returns B2C summary, HSN breakdown, and total tax liability.
    """
    try:
        data = gstr1_service.generate_gstr1_report(db, month, year)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"GSTR-1 export error: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate GSTR-1: {str(e)}")


@router.get("/gstr1/validate")
async def validate_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db)
):
    """Pre-filing validation — check for missing GST amounts, HSN codes, etc."""
    try:
        data = gstr1_service.validate_gstr1(db, month, year)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"GSTR-1 validate error: {e}")
        raise HTTPException(500, "Validation failed")


@router.get("/invoice/{sale_id}")
async def get_gst_invoice(
    sale_id: int,
    buyer_state_code: str = Query(None, description="Buyer state code for IGST/CGST determination"),
    db: Session = Depends(get_db)
):
    """Generate GST invoice breakdown for a specific sale"""
    from api.services import gst_invoice_service
    try:
        data = gst_invoice_service.generate_invoice_for_sale(db, sale_id, buyer_state_code)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"GST invoice error: {e}", exc_info=True)
        raise HTTPException(500, "Failed to generate GST invoice")


@router.get("/invoices")
async def list_gst_invoices(
    start_date: str = Query(None),
    end_date: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Paginated list of GST invoices with CGST/SGST breakdown"""
    from api.services import gst_invoice_service
    try:
        result = gst_invoice_service.get_invoice_list(db, start_date, end_date, page, per_page)
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"Invoice list error: {e}")
        raise HTTPException(500, "Failed to fetch invoices")
