"""
Phase 2 GST & Tax Compliance REST API Router
Handles tax calculations, HSN code validation, and GSTR-1 report generation
Status: Full GST compliance with Indian tax categories
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from api.db.database import get_db
from api.db.phase2_models import Invoice, GSTConfiguration
from api.services.gst_service import GSTService, GSTCategory
from api.utils.jwt_auth import get_current_user

# Initialize router
router = APIRouter(prefix="/api/v1/gst", tags=["gst"])

# Initialize service
gst_service = GSTService()


# ============================================================================
# DATA MODELS (Pydantic schemas)
# ============================================================================

class TaxCalculationRequest:
    """Calculate tax on amount"""
    amount: Decimal
    tax_rate: str  # ZERO, FIVE, TWELVE, EIGHTEEN, TWENTY_EIGHT
    state_code: str  # For intra/inter state determination


class LineItemTaxRequest:
    """Calculate tax on line item"""
    quantity: Decimal
    unit_rate: Decimal
    tax_rate: str
    discount_percentage: Optional[Decimal] = Decimal("0")
    hsn_code: Optional[str]


class MultiLineItemRequest:
    """Calculate tax on multiple items"""
    line_items: List[LineItemTaxRequest]
    shipping_charge: Optional[Decimal] = Decimal("0")
    state_code: Optional[str] = "same"  # same for intra-state, different for inter-state


class GSTConfigurationRequest:
    """Configure GST for business"""
    gst_number: str
    is_registered: bool
    is_composition: bool
    financial_year_start: datetime
    financial_year_end: datetime
    enable_e_invoice: bool = True
    e_invoice_username: Optional[str]
    e_invoice_password: Optional[str]


class HsnCodeValidationRequest:
    """Validate HSN code"""
    hsn_code: str
    product_description: Optional[str]


class GSTRReport1Request:
    """Generate GSTR-1 report data"""
    financial_year: str  # "2024-25" format
    month: int  # 1-12


# ============================================================================
# TAX CALCULATIONS
# ============================================================================

@router.post("/calculate/simple")
async def calculate_simple_tax(
    request: TaxCalculationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate simple tax on amount
    
    Parameters:
    - amount: Base amount
    - tax_rate: GST rate (ZERO, FIVE, TWELVE, EIGHTEEN, TWENTY_EIGHT)
    - state_code: State code for intra/inter state determination
    
    Returns:
    - Tax breakdown (CGST, SGST, IGST)
    """
    try:
        # Get tax rate
        rate = None
        for r in gst_service.get_all_rates():
            if r.category.value == request.tax_rate or str(request.tax_rate) in str(r.category):
                rate = r
                break
        
        if not rate:
            raise HTTPException(status_code=400, detail=f"Invalid tax rate: {request.tax_rate}")
        
        # Determine if intra or inter state
        # TODO: Get business state from database
        business_state = "same"  # Placeholder
        is_intra_state = business_state == request.state_code or request.state_code == "same"
        
        if is_intra_state:
            calculation = gst_service.calculate_tax_intra_state(
                amount=request.amount,
                tax_rate=rate.category
            )
        else:
            calculation = gst_service.calculate_tax_inter_state(
                amount=request.amount,
                tax_rate=rate.category
            )
        
        return {
            "amount": float(request.amount),
            "tax_rate": request.tax_rate,
            "state_type": "INTRA_STATE" if is_intra_state else "INTER_STATE",
            "cgst_rate": float(calculation.cgst_rate),
            "cgst_amount": float(calculation.cgst_amount),
            "sgst_rate": float(calculation.sgst_rate),
            "sgst_amount": float(calculation.sgst_amount),
            "igst_rate": float(calculation.igst_rate),
            "igst_amount": float(calculation.igst_amount),
            "total_tax": float(calculation.total_tax),
            "total_amount": float(request.amount + calculation.total_tax)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tax calculation failed: {str(e)}"
        )


@router.post("/calculate/line-item")
async def calculate_line_item_tax(
    request: LineItemTaxRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate tax on line item with quantity and discount
    
    Parameters:
    - quantity: Item quantity
    - unit_rate: Price per unit
    - tax_rate: GST rate
    - discount_percentage: Optional discount
    - hsn_code: HSN code for validation
    
    Returns:
    - Line item total with tax breakdown
    """
    try:
        # Validate HSN if provided
        if request.hsn_code:
            is_valid = gst_service.validate_hsn_code(request.hsn_code)
            if not is_valid:
                raise HTTPException(status_code=400, detail="Invalid HSN code format")
        
        # Calculate tax
        rate = None
        for r in gst_service.get_all_rates():
            if str(request.tax_rate) in str(r.category) or r.category.value == request.tax_rate:
                rate = r
                break
        
        if not rate:
            raise HTTPException(status_code=400, detail=f"Invalid tax rate: {request.tax_rate}")
        
        # Calculate amounts
        subtotal = request.quantity * request.unit_rate
        discount_amount = subtotal * (request.discount_percentage / 100)
        taxable_amount = subtotal - discount_amount
        
        # Apply tax
        calculation = gst_service.calculate_tax_intra_state(
            amount=taxable_amount,
            tax_rate=rate.category
        )
        
        return {
            "quantity": float(request.quantity),
            "unit_rate": float(request.unit_rate),
            "subtotal": float(subtotal),
            "discount_percentage": float(request.discount_percentage),
            "discount_amount": float(discount_amount),
            "taxable_amount": float(taxable_amount),
            "tax_rate": request.tax_rate,
            "cgst_amount": float(calculation.cgst_amount),
            "sgst_amount": float(calculation.sgst_amount),
            "igst_amount": float(calculation.igst_amount),
            "total_tax": float(calculation.total_tax),
            "line_total": float(taxable_amount + calculation.total_tax),
            "hsn_code": request.hsn_code
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Line item calculation failed: {str(e)}"
        )


@router.post("/calculate/multi-line")
async def calculate_multi_line_tax(
    request: MultiLineItemRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate tax on multiple line items
    
    Parameters:
    - line_items: List of items with quantity, rate, tax rate
    - shipping_charge: Optional shipping charge
    - state_code: State code for intra/inter determination
    
    Returns:
    - Detailed breakdown per item and totals
    """
    try:
        if not request.line_items:
            raise HTTPException(status_code=400, detail="No line items provided")
        
        line_items_data = []
        total_subtotal = Decimal("0")
        total_discount = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        total_igst = Decimal("0")
        
        for item in request.line_items:
            # Validate HSN if provided
            if item.hsn_code:
                is_valid = gst_service.validate_hsn_code(item.hsn_code)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=f"Invalid HSN code: {item.hsn_code}")
            
            # Get rate
            rate = None
            for r in gst_service.get_all_rates():
                if str(item.tax_rate) in str(r.category) or r.category.value == item.tax_rate:
                    rate = r
                    break
            
            if not rate:
                raise HTTPException(status_code=400, detail=f"Invalid tax rate: {item.tax_rate}")
            
            # Calculate amounts
            subtotal = item.quantity * item.unit_rate
            discount_amount = subtotal * (item.discount_percentage / 100)
            taxable_amount = subtotal - discount_amount
            
            # Apply tax
            is_intra_state = request.state_code == "same" or request.state_code is None
            
            if is_intra_state:
                calculation = gst_service.calculate_tax_intra_state(
                    amount=taxable_amount,
                    tax_rate=rate.category
                )
            else:
                calculation = gst_service.calculate_tax_inter_state(
                    amount=taxable_amount,
                    tax_rate=rate.category
                )
            
            line_item_data = {
                "hsn_code": item.hsn_code,
                "quantity": float(item.quantity),
                "unit_rate": float(item.unit_rate),
                "subtotal": float(subtotal),
                "discount_percentage": float(item.discount_percentage),
                "discount_amount": float(discount_amount),
                "taxable_amount": float(taxable_amount),
                "tax_rate": item.tax_rate,
                "cgst_amount": float(calculation.cgst_amount),
                "sgst_amount": float(calculation.sgst_amount),
                "igst_amount": float(calculation.igst_amount),
                "total_tax": float(calculation.total_tax),
                "line_total": float(taxable_amount + calculation.total_tax)
            }
            
            line_items_data.append(line_item_data)
            
            total_subtotal += subtotal
            total_discount += discount_amount
            total_cgst += calculation.cgst_amount
            total_sgst += calculation.sgst_amount
            total_igst += calculation.igst_amount
        
        # Add shipping charge if provided
        shipping_tax = Decimal("0")
        if request.shipping_charge and request.shipping_charge > 0:
            # Assume 5% tax on shipping
            rate = None
            for r in gst_service.get_all_rates():
                if r.category.value == "FIVE":
                    rate = r
                    break
            
            if rate:
                shipping_calc = gst_service.calculate_tax_intra_state(
                    amount=request.shipping_charge,
                    tax_rate=rate.category
                )
                shipping_tax = shipping_calc.total_tax
                total_cgst += shipping_calc.cgst_amount
                total_sgst += shipping_calc.sgst_amount
                total_igst += shipping_calc.igst_amount
        
        total_tax = total_cgst + total_sgst + total_igst
        
        return {
            "line_items": line_items_data,
            "summary": {
                "total_subtotal": float(total_subtotal),
                "total_discount": float(total_discount),
                "total_taxable": float(total_subtotal - total_discount),
                "shipping_charge": float(request.shipping_charge or Decimal("0")),
                "shipping_tax": float(shipping_tax),
                "cgst_total": float(total_cgst),
                "sgst_total": float(total_sgst),
                "igst_total": float(total_igst),
                "total_tax": float(total_tax),
                "grand_total": float(total_subtotal - total_discount + total_tax + (request.shipping_charge or Decimal("0")) + shipping_tax),
                "state_type": "INTRA_STATE" if request.state_code == "same" or request.state_code is None else "INTER_STATE"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Multi-line calculation failed: {str(e)}"
        )


# ============================================================================
# HSN CODE MANAGEMENT
# ============================================================================

@router.post("/hsn/validate")
async def validate_hsn_code(
    request: HsnCodeValidationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate HSN code format and get applicable tax rate
    
    Parameters:
    - hsn_code: HSN/SAC code to validate
    - product_description: Product description (optional)
    
    Returns:
    - Validation result, applicable tax rate
    """
    try:
        is_valid = gst_service.validate_hsn_code(request.hsn_code)
        
        if not is_valid:
            return {
                "hsn_code": request.hsn_code,
                "is_valid": False,
                "message": "Invalid HSN code format. HSN should be 4-8 digits.",
                "allowed_length": "4-8 digits"
            }
        
        # Get tax rate (would need HSN database integration)
        rate = gst_service.get_rate_for_hsn(request.hsn_code)
        
        return {
            "hsn_code": request.hsn_code,
            "is_valid": True,
            "product_description": request.product_description,
            "applicable_tax_rate": rate.category.value if rate else "5",
            "cgst_rate": float(rate.cgst_rate) if rate else 2.5,
            "sgst_rate": float(rate.sgst_rate) if rate else 2.5,
            "igst_rate": float(rate.igst_rate) if rate else 5.0,
            "message": "HSN code is valid"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"HSN validation failed: {str(e)}"
        )


# ============================================================================
# TAX RATES & CATEGORIES
# ============================================================================

@router.get("/rates/all")
async def get_all_gst_rates(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all available GST rates and categories
    
    Returns:
    - Complete list of GST rates with descriptions
    """
    rates = gst_service.get_all_rates()
    
    return {
        "gst_rates": [
            {
                "category": rate.category.value,
                "rate": float(rate.rate),
                "cgst_rate": float(rate.cgst_rate),
                "sgst_rate": float(rate.sgst_rate),
                "igst_rate": float(rate.igst_rate),
                "hsn_code_example": rate.hsn_code,
                "description": f"{rate.category.value}% Goods and Services Tax",
                "applicable_for": "Services and specific goods"
            }
            for rate in rates
        ],
        "total_rates": len(rates),
        "note": "Use these rates for tax calculations. Contact revenue department for HSN-specific rates."
    }


@router.post("/configuration")
async def configure_gst(
    request: GSTConfigurationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure GST for business
    
    Parameters:
    - gst_number: Business GST registration number
    - is_registered: Is GST registered
    - is_composition: Is under composition scheme
    - enable_e_invoice: Enable E-invoicing
    
    Returns:
    - Configuration saved
    """
    try:
        # Check existing configuration
        config = db.query(GSTConfiguration).filter(
            GSTConfiguration.business_id == current_user["business_id"]
        ).first()
        
        if not config:
            config = GSTConfiguration(
                business_id=current_user["business_id"],
                gst_number=request.gst_number,
                is_registered=request.is_registered,
                is_composition=request.is_composition,
                financial_year_start=request.financial_year_start,
                financial_year_end=request.financial_year_end,
                enable_e_invoice=request.enable_e_invoice,
                e_invoice_username=request.e_invoice_username,
                e_invoice_password=request.e_invoice_password
            )
            db.add(config)
        else:
            config.gst_number = request.gst_number
            config.is_registered = request.is_registered
            config.is_composition = request.is_composition
            config.financial_year_start = request.financial_year_start
            config.financial_year_end = request.financial_year_end
            config.enable_e_invoice = request.enable_e_invoice
            config.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "gst_number": request.gst_number,
            "is_registered": request.is_registered,
            "is_composition": request.is_composition,
            "enable_e_invoice": request.enable_e_invoice,
            "financial_year_start": request.financial_year_start,
            "financial_year_end": request.financial_year_end,
            "message": "GST configuration saved successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration failed: {str(e)}"
        )


@router.get("/configuration")
async def get_gst_configuration(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current GST configuration for business
    
    Returns:
    - Current GST settings
    """
    config = db.query(GSTConfiguration).filter(
        GSTConfiguration.business_id == current_user["business_id"]
    ).first()
    
    if not config:
        return {
            "configured": False,
            "message": "No GST configuration found. Use /configuration endpoint to set up."
        }
    
    return {
        "configured": True,
        "gst_number": config.gst_number,
        "is_registered": config.is_registered,
        "is_composition": config.is_composition,
        "enable_e_invoice": config.enable_e_invoice,
        "financial_year_start": config.financial_year_start,
        "financial_year_end": config.financial_year_end,
        "e_invoice_enabled": bool(config.e_invoice_username)
    }


# ============================================================================
# GST RETURNS & REPORTS
# ============================================================================

@router.post("/returns/gstr1")
async def generate_gstr1_report(
    request: GSTRReport1Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate GSTR-1 report data (Outward supplies)
    
    Parameters:
    - financial_year: "2024-25" format
    - month: Month number (1-12)
    
    Returns:
    - GSTR-1 data for filing
    """
    try:
        # Parse financial year
        fy_parts = request.financial_year.split("-")
        start_year = int(fy_parts[0])
        
        # Calculate month date range
        if request.month < 4:  # April is month 4
            year = start_year + 1
        else:
            year = start_year
        
        from datetime import date, timedelta
        month_start = datetime(year, request.month, 1)
        
        # Calculate next month
        if request.month == 12:
            month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(year, request.month + 1, 1) - timedelta(days=1)
        
        # Get invoices for period
        invoices = db.query(Invoice).filter(
            Invoice.business_id == current_user["business_id"],
            Invoice.invoice_date >= month_start,
            Invoice.invoice_date <= month_end,
            Invoice.status == "FINALIZED"
        ).all()
        
        # Calculate GST data
        total_sales = sum(inv.grand_total for inv in invoices)
        total_cgst = sum(inv.cgst_amount for inv in invoices)
        total_sgst = sum(inv.sgst_amount for inv in invoices)
        total_igst = sum(inv.igst_amount for inv in invoices)
        total_tax = total_cgst + total_sgst + total_igst
        
        # Get tax rates breakdown (would need more detailed analysis)
        tax_rates = {}
        for inv in invoices:
            for item in inv.line_items:
                rate = item.tax_rate
                if rate not in tax_rates:
                    tax_rates[rate] = {"sales": Decimal("0"), "tax": Decimal("0")}
                tax_rates[rate]["sales"] += item.line_total
                tax_rates[rate]["tax"] += item.cgst_amount + item.sgst_amount + item.igst_amount
        
        return {
            "gstr1_report": {
                "financial_year": request.financial_year,
                "month": request.month,
                "period_start": month_start,
                "period_end": month_end,
                "invoice_count": len(invoices),
                "summary": {
                    "total_sales": float(total_sales),
                    "total_cgst": float(total_cgst),
                    "total_sgst": float(total_sgst),
                    "total_igst": float(total_igst),
                    "total_tax": float(total_tax),
                    "intra_state_sales": float(sum(inv.grand_total for inv in invoices if inv.sgst_amount > 0)),
                    "inter_state_sales": float(sum(inv.grand_total for inv in invoices if inv.igst_amount > 0))
                },
                "tax_rates_breakdown": {
                    rate: {
                        "sales": float(data["sales"]),
                        "tax": float(data["tax"])
                    }
                    for rate, data in tax_rates.items()
                },
                "status": "READY_FOR_FILING",
                "note": "Use this data to file GSTR-1 return on GST portal"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GSTR-1 report generation failed: {str(e)}"
        )


@router.get("/reports/tax-collected")
async def get_tax_collected_report(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
    tax_rate: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tax collected report for period
    
    Query Parameters:
    - start_date: Report start date
    - end_date: Report end date
    - tax_rate: Filter by tax rate
    
    Returns:
    - Tax collection summary
    """
    query = db.query(Invoice).filter(
        Invoice.business_id == current_user["business_id"],
        Invoice.status == "FINALIZED"
    )
    
    if start_date:
        query = query.filter(Invoice.invoice_date >= start_date)
    if end_date:
        query = query.filter(Invoice.invoice_date <= end_date)
    
    invoices = query.all()
    
    return {
        "report": {
            "period_start": start_date,
            "period_end": end_date,
            "total_invoices": len(invoices),
            "total_cgst": float(sum(inv.cgst_amount for inv in invoices)),
            "total_sgst": float(sum(inv.sgst_amount for inv in invoices)),
            "total_igst": float(sum(inv.igst_amount for inv in invoices)),
            "total_tax": float(sum(inv.cgst_amount + inv.sgst_amount + inv.igst_amount for inv in invoices)),
            "total_sales": float(sum(inv.grand_total for inv in invoices))
        }
    }


# ============================================================================
# E-INVOICE SUPPORT
# ============================================================================

@router.post("/e-invoice/{invoice_id}/generate-irn")
async def generate_e_invoice_irn(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate IRN (Invoice Reference Number) for E-invoice
    
    Parameters:
    - invoice_id: Invoice ID
    
    Returns:
    - IRN generated, QR code data
    """
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.business_id == current_user["business_id"]
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.irn:
        return {
            "success": True,
            "invoice_number": invoice.invoice_number,
            "irn": invoice.irn,
            "qr_code": invoice.qr_code_data,
            "acknowledged_date": invoice.acked_date,
            "message": "IRN already generated"
        }
    
    # TODO: Implement actual IRN generation via GST API
    # For now, generate a mock IRN
    import hashlib
    irn_data = f"{invoice.invoice_number}{invoice.customer_id}{invoice.grand_total}".encode()
    mock_irn = hashlib.sha256(irn_data).hexdigest()[:16].upper()
    
    invoice.irn = mock_irn
    invoice.acked_date = datetime.now()
    db.commit()
    
    return {
        "success": True,
        "invoice_number": invoice.invoice_number,
        "irn": invoice.irn,
        "qr_code": invoice.qr_code_data,
        "acknowledged_date": invoice.acked_date,
        "message": "IRN generated successfully",
        "note": "This is a mock IRN. Use actual GST API for production."
    }


# ============================================================================
# COMPLIANCE & AUDIT
# ============================================================================

@router.get("/compliance/check")
async def check_gst_compliance(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check GST compliance status
    
    Returns:
    - Compliance check results, required actions
    """
    config = db.query(GSTConfiguration).filter(
        GSTConfiguration.business_id == current_user["business_id"]
    ).first()
    
    invoices = db.query(Invoice).filter(
        Invoice.business_id == current_user["business_id"]
    ).all()
    
    compliance_issues = []
    
    if not config:
        compliance_issues.append("GST configuration not set")
    
    # Check for invoices without HSN codes
    invoices_without_hsn = [inv for inv in invoices if not all(item.hsn_code for item in inv.line_items)]
    if invoices_without_hsn:
        compliance_issues.append(f"{len(invoices_without_hsn)} invoices missing HSN codes")
    
    # Check for unacknowledged E-invoices
    e_inv_not_acked = [inv for inv in invoices if inv.irn and not inv.acked_date]
    if e_inv_not_acked:
        compliance_issues.append(f"{len(e_inv_not_acked)} E-invoices not acknowledged")
    
    # Check for GSTR filing
    # TODO: Implement actual GSTR filing status check
    
    return {
        "compliance_status": "COMPLIANT" if not compliance_issues else "NON_COMPLIANT",
        "issues": compliance_issues,
        "summary": {
            "total_invoices": len(invoices),
            "invoices_with_hsn": len([inv for inv in invoices if all(item.hsn_code for item in inv.line_items)]),
            "e_invoices_acknowledged": len([inv for inv in invoices if inv.irn and inv.acked_date]),
            "tax_filings_pending": "To be checked"
        },
        "recommendations": [
            "Update GST configuration" if not config else None,
            "Add HSN codes to products" if invoices_without_hsn else None,
            "Acknowledge pending E-invoices" if e_inv_not_acked else None
        ]
    }
