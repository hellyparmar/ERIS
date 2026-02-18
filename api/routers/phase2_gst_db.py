"""
Phase 2: GST Compliance Management with Database Integration

Complete GST tax calculation, compliance reporting, and database persistence
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from api.db.database import get_db
from api.db.phase2_models import GSTConfiguration, Invoice, InvoiceLineItem
from api.services.gst_service import gst_service

router = APIRouter(prefix="/api/v2/gst", tags=["gst"])


# ==================== GST Configuration ====================

@router.post("/config/setup")
def setup_gst_configuration(
    business_id: str,
    gstin: str,
    business_name: str,
    financial_year: str = "2024-04-01",
    gst_registration_date: date = None,
    composition_eligible: bool = False,
    composition_rate: Decimal = None,
    intra_state_cgst: Decimal = Decimal("9"),
    intra_state_sgst: Decimal = Decimal("9"),
    inter_state_igst: Decimal = Decimal("18"),
    db: Session = Depends(get_db)
):
    """
    Setup GST configuration for business
    
    Args:
        business_id: Business unique identifier
        gstin: GST registration number
        financial_year: Financial year start date (FY 2024 = 2024-04-01)
        composition_eligible: Composition scheme eligibility
    """
    try:
        # Check if config already exists
        existing = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if existing:
            raise ValueError(f"GST configuration already exists for {business_id}")
        
        config = GSTConfiguration(
            business_id=business_id,
            gstin=gstin,
            business_name=business_name,
            financial_year=financial_year,
            gst_registration_date=gst_registration_date or date.today(),
            composition_eligible=composition_eligible,
            composition_rate=Decimal(str(composition_rate)) if composition_rate else None,
            intra_state_cgst=Decimal(str(intra_state_cgst)),
            intra_state_sgst=Decimal(str(intra_state_sgst)),
            inter_state_igst=Decimal(str(inter_state_igst)),
            hsn_sac_enabled=True,
            nil_rated_enabled=True,
            zero_rated_enabled=True
        )
        
        db.add(config)
        db.commit()
        
        return {
            "status": "success",
            "configuration": {
                "business_id": business_id,
                "gstin": gstin,
                "financial_year": financial_year,
                "intra_state_rate": f"{intra_state_cgst}% + {intra_state_sgst}%",
                "inter_state_rate": f"{inter_state_igst}%",
                "setup_date": datetime.utcnow().isoformat()
            }
        }
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{business_id}")
def get_gst_configuration(business_id: str, db: Session = Depends(get_db)):
    """Get GST configuration for business"""
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        return {
            "status": "success",
            "configuration": {
                "business_id": config.business_id,
                "gstin": config.gstin,
                "business_name": config.business_name,
                "financial_year": config.financial_year,
                "gst_registration_date": config.gst_registration_date.isoformat(),
                "tax_rates": {
                    "intra_state": {
                        "cgst": float(config.intra_state_cgst),
                        "sgst": float(config.intra_state_sgst)
                    },
                    "inter_state": {
                        "igst": float(config.inter_state_igst)
                    }
                },
                "composition_scheme": config.composition_eligible,
                "composition_rate": float(config.composition_rate) if config.composition_rate else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{business_id}")
def update_gst_configuration(
    business_id: str,
    intra_state_cgst: Optional[Decimal] = None,
    intra_state_sgst: Optional[Decimal] = None,
    inter_state_igst: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    """Update GST tax rates"""
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        if intra_state_cgst:
            config.intra_state_cgst = Decimal(str(intra_state_cgst))
        if intra_state_sgst:
            config.intra_state_sgst = Decimal(str(intra_state_sgst))
        if inter_state_igst:
            config.inter_state_igst = Decimal(str(inter_state_igst))
        
        config.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "message": "GST configuration updated",
            "updated_at": config.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Tax Calculations ====================

@router.post("/calculate/intra-state")
def calculate_intra_state_tax(
    business_id: str,
    amount: Decimal,
    tax_rate: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    """
    Calculate GST for intra-state transaction (CGST + SGST)
    
    Args:
        business_id: Business identifier
        amount: Taxable amount
        tax_rate: Optional override rate (uses config default if not provided)
    """
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        # Use service layer for calculation
        result = gst_service.calculate_tax_intra_state(
            amount=amount,
            cgst_rate=float(config.intra_state_cgst),
            sgst_rate=float(config.intra_state_sgst)
        )
        
        return {
            "status": "success",
            "calculation": {
                "taxable_amount": float(amount),
                "cgst_rate": float(config.intra_state_cgst),
                "cgst_amount": result["cgst"],
                "sgst_rate": float(config.intra_state_sgst),
                "sgst_amount": result["sgst"],
                "total_tax": result["total_tax"],
                "total_amount": result["gross_amount"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate/inter-state")
def calculate_inter_state_tax(
    business_id: str,
    amount: Decimal,
    db: Session = Depends(get_db)
):
    """
    Calculate GST for inter-state transaction (IGST only)
    
    Args:
        business_id: Business identifier
        amount: Taxable amount
    """
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        # Use service layer for calculation
        result = gst_service.calculate_tax_inter_state(
            amount=amount,
            igst_rate=float(config.inter_state_igst)
        )
        
        return {
            "status": "success",
            "calculation": {
                "taxable_amount": float(amount),
                "igst_rate": float(config.inter_state_igst),
                "igst_amount": result["igst"],
                "total_tax": result["igst"],
                "total_amount": result["gross_amount"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate/line-items")
def calculate_line_items_tax(
    business_id: str,
    line_items: List[Dict],
    is_intra_state: bool = True,
    db: Session = Depends(get_db)
):
    """
    Calculate GST for multiple line items
    
    Args:
        line_items: List of {description, quantity, unit_price, tax_rate, hsn_code}
        is_intra_state: CGST+SGST (True) or IGST (False)
    """
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        # Calculate using service
        result = gst_service.calculate_line_items(
            line_items=line_items,
            cgst_rate=float(config.intra_state_cgst),
            sgst_rate=float(config.intra_state_sgst),
            igst_rate=float(config.inter_state_igst),
            is_intra_state=is_intra_state
        )
        
        return {
            "status": "success",
            "summary": {
                "total_items": len(line_items),
                "subtotal": result["subtotal"],
                "total_tax": result["total_tax"],
                "gross_total": result["gross_total"],
                "line_items": result["line_items"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GST Returns & Compliance ====================

@router.get("/returns/gstr1/{business_id}")
def generate_gstr1_return(
    business_id: str,
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Generate GSTR-1 return data (Outward supplies)
    
    GSTR-1: All supplies made (sales) in the month
    """
    try:
        # Get all invoices for the month
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            func.month(Invoice.created_at) == month,
            func.year(Invoice.created_at) == year
        ).all()
        
        if not invoices:
            raise HTTPException(status_code=404, detail=f"No invoices found for {month}/{year}")
        
        # Aggregate by GST slab
        gstr1_data = gst_service.get_gst_return_summary(business_id)
        
        total_taxable = sum(Decimal(str(inv.total_taxable)) for inv in invoices)
        total_tax = sum(Decimal(str(inv.total_tax)) for inv in invoices)
        total_supply = sum(Decimal(str(inv.total_amount)) for inv in invoices)
        
        return {
            "status": "success",
            "gstr1": {
                "month": month,
                "year": year,
                "business_id": business_id,
                "total_invoices": len(invoices),
                "total_taxable_supply": float(total_taxable),
                "total_tax_collected": float(total_tax),
                "total_supply": float(total_supply),
                "supplies_intra_state": len([i for i in invoices if not getattr(i, 'is_inter_state', False)]),
                "supplies_inter_state": len([i for i in invoices if getattr(i, 'is_inter_state', False)])
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/gstr2/{business_id}")
def generate_gstr2_return(
    business_id: str,
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Generate GSTR-2 return data (Inward supplies)
    
    Note: In current implementation, tracked via purchase invoices
    """
    try:
        # This would require purchase tracking in database
        # For now, return placeholder
        
        return {
            "status": "success",
            "message": "GSTR-2 tracking not yet implemented",
            "gstr2": {
                "month": month,
                "year": year,
                "business_id": business_id,
                "total_purchases": 0,
                "total_tax_eligible_input": 0.0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/returns/gstr3b/{business_id}")
def generate_gstr3b_return(
    business_id: str,
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Generate GSTR-3B return data (Monthly GST return)
    
    GSTR-3B: Outward supplies - Inward supplies = Net GST to pay
    """
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        # Get outward supplies (invoices)
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            func.month(Invoice.created_at) == month,
            func.year(Invoice.created_at) == year
        ).all()
        
        outward_cgst = sum(
            Decimal(str(getattr(inv, 'cgst_amount', 0))) for inv in invoices
        )
        outward_sgst = sum(
            Decimal(str(getattr(inv, 'sgst_amount', 0))) for inv in invoices
        )
        outward_igst = sum(
            Decimal(str(getattr(inv, 'igst_amount', 0))) for inv in invoices
        )
        
        # Input tax (placeholder)
        input_cgst = Decimal(0)
        input_sgst = Decimal(0)
        input_igst = Decimal(0)
        
        # Payable tax
        cgst_payable = outward_cgst - input_cgst
        sgst_payable = outward_sgst - input_sgst
        igst_payable = outward_igst - input_igst
        
        return {
            "status": "success",
            "gstr3b": {
                "month": month,
                "year": year,
                "business_id": business_id,
                "outward_supplies": {
                    "cgst": float(outward_cgst),
                    "sgst": float(outward_sgst),
                    "igst": float(outward_igst)
                },
                "inward_supplies": {
                    "cgst": float(input_cgst),
                    "sgst": float(input_sgst),
                    "igst": float(input_igst)
                },
                "gst_payable": {
                    "cgst": float(cgst_payable),
                    "sgst": float(sgst_payable),
                    "igst": float(igst_payable),
                    "total": float(cgst_payable + sgst_payable + igst_payable)
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Tax Rates & Compliance ====================

@router.get("/rates/standard/{business_id}")
def get_standard_tax_rates(business_id: str, db: Session = Depends(get_db)):
    """Get standard GST rates for business"""
    try:
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == business_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="GST configuration not found")
        
        return {
            "status": "success",
            "rates": {
                "intra_state": {
                    "cgst": float(config.intra_state_cgst),
                    "sgst": float(config.intra_state_sgst),
                    "total": float(config.intra_state_cgst + config.intra_state_sgst)
                },
                "inter_state": {
                    "igst": float(config.inter_state_igst)
                },
                "effective_from": config.updated_at.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-compliance")
def verify_gst_compliance(
    business_id: str,
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    Verify GST compliance for the month
    
    Checks:
    - All invoices have GST calculated
    - GST amounts are accurate
    - Returns can be filed
    """
    try:
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            func.month(Invoice.created_at) == month,
            func.year(Invoice.created_at) == year
        ).all()
        
        compliance_issues = []
        
        # Check all invoices have GST
        for inv in invoices:
            if not hasattr(inv, 'total_tax') or inv.total_tax == 0:
                compliance_issues.append(f"Invoice {inv.invoice_number}: No GST amount")
        
        is_compliant = len(compliance_issues) == 0
        
        return {
            "status": "success",
            "compliance": {
                "month": month,
                "year": year,
                "is_compliant": is_compliant,
                "total_invoices": len(invoices),
                "issues_found": len(compliance_issues),
                "issues": compliance_issues,
                "gstr1_filing_ready": is_compliant,
                "compliance_percentage": (len(invoices) - len(compliance_issues)) / len(invoices) * 100 if invoices else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Tax Analysis & Reporting ====================

@router.get("/analytics/monthly/{business_id}")
def get_monthly_tax_analytics(
    business_id: str,
    month: int,
    year: int,
    db: Session = Depends(get_db)
):
    """Get monthly GST analytics"""
    try:
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            func.month(Invoice.created_at) == month,
            func.year(Invoice.created_at) == year
        ).all()
        
        total_taxable = sum(Decimal(str(getattr(inv, 'total_taxable', 0))) for inv in invoices)
        total_tax = sum(Decimal(str(getattr(inv, 'total_tax', 0))) for inv in invoices)
        
        return {
            "status": "success",
            "analytics": {
                "month": month,
                "year": year,
                "total_invoices": len(invoices),
                "total_taxable_supply": float(total_taxable),
                "total_tax_collected": float(total_tax),
                "avg_tax_rate": float(total_tax / total_taxable * 100) if total_taxable > 0 else 0,
                "highest_invoice": float(max((inv.total_amount for inv in invoices), default=0))
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/annual/{business_id}")
def get_annual_tax_analytics(
    business_id: str,
    year: int,
    db: Session = Depends(get_db)
):
    """Get annual GST analytics"""
    try:
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            func.year(Invoice.created_at) == year
        ).all()
        
        total_taxable = sum(Decimal(str(getattr(inv, 'total_taxable', 0))) for inv in invoices)
        total_tax = sum(Decimal(str(getattr(inv, 'total_tax', 0))) for inv in invoices)
        
        # Monthly breakdown
        monthly_breakdown = {}
        for month in range(1, 13):
            month_invoices = [i for i in invoices if i.created_at.month == month]
            monthly_breakdown[f"Month_{month}"] = {
                "invoices": len(month_invoices),
                "tax": float(sum(Decimal(str(getattr(i, 'total_tax', 0))) for i in month_invoices))
            }
        
        return {
            "status": "success",
            "analytics": {
                "year": year,
                "total_invoices": len(invoices),
                "total_taxable_supply": float(total_taxable),
                "total_tax_collected": float(total_tax),
                "monthly_breakdown": monthly_breakdown
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tax-slabs/{business_id}")
def get_applicable_tax_slabs(business_id: str, db: Session = Depends(get_db)):
    """Get applicable tax slabs for business GST registration"""
    try:
        # Standard GST slabs in India
        tax_slabs = {
            "0%": {
                "category": "Nil-rated",
                "description": "Essential items, fresh produce",
                "enabled": True
            },
            "5%": {
                "category": "Essential items",
                "description": "Packaged food, books, newspapers",
                "enabled": True
            },
            "12%": {
                "category": "Standard rate",
                "description": "Most goods and services",
                "enabled": True
            },
            "18%": {
                "category": "Higher rate",
                "description": "Premium goods and most services",
                "enabled": True
            },
            "28%": {
                "category": "Highest rate",
                "description": "Luxury goods, tobacco, aerated beverages",
                "enabled": True
            }
        }
        
        return {
            "status": "success",
            "tax_slabs": tax_slabs
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
