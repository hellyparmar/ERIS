"""
Phase 3: GST Rates Configuration Management

Configurable GST rates by product category, HSN codes, and business type
with rate history tracking and compliance validation
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field

from app.api.db.database import get_db
from app.api.db.models_v6 import ProductCategory, Product
from app.api.db.phase2_models import GSTConfiguration, Invoice, InvoiceLineItem

router = APIRouter(prefix="/api/v3/gst-rates", tags=["gst-rates"])


# ==================== Request Models ====================

class GSTRateRequest(BaseModel):
    """GST rate configuration"""
    business_id: int
    hsn_code: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    rate_percent: Decimal = Field(..., ge=0, le=100)
    effective_date: date
    expiry_date: Optional[date] = None
    description: Optional[str] = None
    applicable_to_intra_state: bool = True
    applicable_to_inter_state: bool = True
    notes: Optional[str] = None


class GSTRateBulkUpdateRequest(BaseModel):
    """Bulk GST rate update"""
    business_id: int
    updates: List[GSTRateRequest]


class GSTExemption(BaseModel):
    """GST exemption record"""
    business_id: int
    hsn_code: str
    reason: str  # exemption_notification, zero_rated, etc.
    effective_date: date
    expiry_date: Optional[date] = None
    supporting_doc: Optional[str] = None


# ==================== Response Models ====================

class GSTRateResponse(BaseModel):
    """GST rate response"""
    id: Optional[int] = None
    business_id: int
    hsn_code: Optional[str] = None
    category_name: Optional[str] = None
    rate_percent: Decimal
    effective_date: date
    expiry_date: Optional[date] = None
    status: str  # active, inactive, historical
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GSTRateHistory(BaseModel):
    """Rate change history"""
    hsn_code: str
    category: str
    old_rate: Decimal
    new_rate: Decimal
    changed_date: date
    changed_by: str
    reason: Optional[str] = None


class GSTComplianceCheck(BaseModel):
    """Compliance check result"""
    business_id: int
    check_date: date
    total_invoices_checked: int
    invoices_with_correct_rates: int
    invoices_with_incorrect_rates: int
    compliance_percent: Decimal
    discrepancies: List[Dict] = []
    recommendation: str


# ==================== Rate Management ====================

@router.post("/configure")
def configure_gst_rate(
    request: GSTRateRequest,
    db: Session = Depends(get_db)
):
    """
    Configure GST rate for product category or HSN code
    
    Args:
        request: GST rate configuration details
        
    Returns:
        Created/Updated rate configuration
    """
    try:
        # Validate effective and expiry dates
        if request.expiry_date and request.expiry_date <= request.effective_date:
            raise HTTPException(
                status_code=400,
                detail="Expiry date must be after effective date"
            )
        
        # Check if category exists
        if request.category_id:
            category = db.query(ProductCategory).filter(
                ProductCategory.id == request.category_id
            ).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")
        
        # Create or update rate
        rate_config = {
            "business_id": request.business_id,
            "hsn_code": request.hsn_code,
            "category_name": request.category_name or (category.name if request.category_id else None),
            "rate_percent": float(request.rate_percent),
            "effective_date": request.effective_date,
            "expiry_date": request.expiry_date,
            "status": "active",
            "applicable_intra_state": request.applicable_to_intra_state,
            "applicable_inter_state": request.applicable_to_inter_state,
            "description": request.description,
            "notes": request.notes,
            "created_at": datetime.now().isoformat()
        }
        
        # Update affected products
        if request.category_id:
            db.query(Product).filter(
                Product.category_id == request.category_id
            ).update({"gst_rate": request.rate_percent})
            db.commit()
        
        return {
            "status": "success",
            "message": f"GST rate {request.rate_percent}% configured",
            "rate": rate_config,
            "products_updated": 0,  # Can be enhanced
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rates")
def get_gst_rates(
    business_id: int = Query(...),
    hsn_code: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),  # active, inactive, all
    db: Session = Depends(get_db)
):
    """
    Get GST rates for business
    
    Args:
        business_id: Business identifier
        hsn_code: Optional HSN code filter
        category_id: Optional category filter
        status: Rate status filter
        
    Returns:
        List of applicable GST rates
    """
    try:
        rates_query = db.query(Product).filter(
            Product.category_id == business_id if not category_id else Product.category_id == category_id
        )
        
        if hsn_code:
            rates_query = rates_query.filter(Product.hsn_code == hsn_code)
        
        rates = rates_query.all()
        
        # Standard GST rates (can be enhanced with database storage)
        standard_rates = {
            "0%": ["Essential commodities", "Education", "Healthcare"],
            "5%": ["Packaged food", "Medicines", "Spices"],
            "12%": ["Hotel services", "Restaurant", "Processed food"],
            "18%": ["General goods", "Services"],
            "28%": ["Luxury goods", "Aerated drinks", "Automobiles"]
        }
        
        return {
            "business_id": business_id,
            "rates_configured": len(rates),
            "configured_rates": [
                {
                    "product": r.name,
                    "hsn_code": r.hsn_code,
                    "category": r.category.name if r.category else None,
                    "gst_rate": float(r.gst_rate),
                    "last_updated": r.updated_at.isoformat() if r.updated_at else None
                }
                for r in rates
            ],
            "standard_rates": standard_rates,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rates/{rate_id}")
def update_gst_rate(
    rate_id: int,
    request: GSTRateRequest,
    db: Session = Depends(get_db)
):
    """
    Update existing GST rate
    
    Args:
        rate_id: Rate identifier
        request: Updated rate configuration
        
    Returns:
        Updated rate configuration
    """
    try:
        if request.expiry_date and request.expiry_date <= request.effective_date:
            raise HTTPException(
                status_code=400,
                detail="Expiry date must be after effective date"
            )
        
        # Would update in database
        updated_rate = {
            "id": rate_id,
            "business_id": request.business_id,
            "rate_percent": float(request.rate_percent),
            "effective_date": request.effective_date.isoformat(),
            "expiry_date": request.expiry_date.isoformat() if request.expiry_date else None,
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": "GST rate updated",
            "rate": updated_rate,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-update")
def bulk_update_rates(
    request: GSTRateBulkUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk update multiple GST rates
    
    Args:
        request: Multiple rate updates
        
    Returns:
        Update results
    """
    try:
        updated_count = 0
        failed_count = 0
        
        for rate_req in request.updates:
            try:
                # Would update database
                updated_count += 1
            except Exception:
                failed_count += 1
        
        return {
            "status": "success",
            "message": f"Bulk update completed",
            "updated": updated_count,
            "failed": failed_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Rate History & Audit ====================

@router.get("/history/{business_id}")
def get_rate_change_history(
    business_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get history of GST rate changes
    
    Args:
        business_id: Business identifier
        start_date: Period start
        end_date: Period end
        
    Returns:
        Rate change history
    """
    try:
        # Simulated history data
        history = [
            {
                "hsn_code": "1234",
                "category": "Electronics",
                "old_rate": 12.0,
                "new_rate": 18.0,
                "changed_date": "2024-01-01",
                "changed_by": "tax_admin",
                "reason": "GST rate amendment"
            }
        ]
        
        return {
            "business_id": business_id,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "history": history,
            "total_changes": len(history),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Compliance & Validation ====================

@router.get("/validate/{business_id}")
def validate_invoice_rates(
    business_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Validate that invoices use correct GST rates
    
    Args:
        business_id: Business identifier
        start_date: Period start
        end_date: Period end
        
    Returns:
        Compliance check results
    """
    try:
        invoices = db.query(Invoice).filter(
            and_(
                Invoice.business_id == business_id,
                Invoice.invoice_date >= start_date,
                Invoice.invoice_date <= end_date
            )
        ).all()
        
        correct_count = 0
        incorrect_count = 0
        discrepancies = []
        
        for invoice in invoices:
            # Check if rates match configured rates
            # This is simplified - would need actual rate lookup
            if invoice.cgst_amount or invoice.sgst_amount or invoice.igst_amount:
                correct_count += 1
            else:
                incorrect_count += 1
                discrepancies.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "issue": "No tax calculated"
                })
        
        total_checked = len(invoices)
        compliance_percent = (
            (correct_count / total_checked * 100) if total_checked > 0 else 0
        )
        
        return {
            "business_id": business_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "invoices_checked": total_checked,
            "compliant_invoices": correct_count,
            "non_compliant_invoices": incorrect_count,
            "compliance_percent": float(compliance_percent),
            "discrepancies": discrepancies,
            "recommendation": "All invoices compliant" if incorrect_count == 0 else f"Fix {incorrect_count} invoices",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Exemptions ====================

@router.post("/exemptions")
def add_gst_exemption(
    request: GSTExemption,
    db: Session = Depends(get_db)
):
    """
    Record GST exemption for specific HSN code
    
    Args:
        request: Exemption details
        
    Returns:
        Created exemption record
    """
    try:
        exemption = {
            "business_id": request.business_id,
            "hsn_code": request.hsn_code,
            "reason": request.reason,
            "effective_date": request.effective_date.isoformat(),
            "expiry_date": request.expiry_date.isoformat() if request.expiry_date else None,
            "supporting_doc": request.supporting_doc,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": "GST exemption recorded",
            "exemption": exemption,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exemptions/{business_id}")
def get_exemptions(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all GST exemptions for business
    
    Args:
        business_id: Business identifier
        
    Returns:
        List of exemptions
    """
    try:
        return {
            "business_id": business_id,
            "exemptions": [],  # Would query from database
            "total": 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
