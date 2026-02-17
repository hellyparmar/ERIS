"""
GST Compliance API Routes
Endpoints for tax calculation, E-Invoice generation, and HSN summary
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from decimal import Decimal

from api.services.gst_calculator import GSTCalculator, LineItem, TaxType
from api.services.einvoice_service import EInvoicePreparationService
from api.dependencies import get_db, get_current_user
from api.middleware.tenant_context import require_organization

router = APIRouter(prefix="/api/v1/gst", tags=["GST Compliance"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class TaxCalculationRequest(BaseModel):
    """Request to calculate GST tax"""
    seller_state_code: str = Field(..., pattern=r'^\d{2}$')
    buyer_state_code: str = Field(..., pattern=r'^\d{2}$')
    reverse_charge: bool = False
    
    items: List[Dict] = Field(..., description="List of line items")
    
    class Config:
        schema_extra = {
            "example": {
                "seller_state_code": "29",
                "buyer_state_code": "29",
                "reverse_charge": False,
                "items": [
                    {
                        "product_id": "prod-123",
                        "name": "Laptop",
                        "hsn_code": "8471",
                        "quantity": 2,
                        "unit_price": 50000,
                        "discount_percentage": 10,
                        "cgst_rate": 9,
                        "sgst_rate": 9,
                        "igst_rate": 18,
                        "is_taxable": True
                    }
                ]
            }
        }


class TaxCalculationResponse(BaseModel):
    """Response with calculated tax"""
    transaction_type: str
    is_interstate: bool
    subtotal: float
    total_discount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    cess_amount: float
    total_tax: float
    round_off: float
    grand_total: float
    line_items: List[Dict]
    hsn_summary: List[Dict]


class EInvoiceGenerationRequest(BaseModel):
    """Request to generate E-Invoice"""
    invoice_id: UUID


class EInvoiceResponse(BaseModel):
    """E-Invoice generation response"""
    success: bool
    invoice_id: UUID
    irn: Optional[str] = None
    ack_number: Optional[str] = None
    ack_date: Optional[str] = None
    signed_qr_code: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# TAX CALCULATION ENDPOINTS
# ============================================================

@router.post("/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_gst_tax(
    request: TaxCalculationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate GST tax for given line items
    
    Automatically determines CGST+SGST (intra-state) or IGST (inter-state)
    """
    try:
        # Initialize calculator
        calculator = GSTCalculator(
            seller_state_code=request.seller_state_code,
            buyer_state_code=request.buyer_state_code,
            reverse_charge=request.reverse_charge
        )
        
        # Convert items to LineItem objects
        line_items = []
        for item_data in request.items:
            line_item = LineItem(
                product_id=item_data['product_id'],
                name=item_data['name'],
                hsn_code=item_data['hsn_code'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Decimal(str(item_data['unit_price'])),
                discount_percentage=Decimal(str(item_data.get('discount_percentage', 0))),
                cgst_rate=Decimal(str(item_data.get('cgst_rate', 0))),
                sgst_rate=Decimal(str(item_data.get('sgst_rate', 0))),
                igst_rate=Decimal(str(item_data.get('igst_rate', 0))),
                cess_rate=Decimal(str(item_data.get('cess_rate', 0))),
                is_taxable=item_data.get('is_taxable', True)
            )
            line_items.append(line_item)
        
        # Calculate tax
        result = calculator.calculate_invoice_tax(line_items)
        
        # Get HSN summary
        hsn_summary = calculator.get_hsn_summary(line_items)
        
        # Add HSN summary to result
        result['hsn_summary'] = hsn_summary
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Tax calculation failed: {str(e)}")


@router.get("/gst-rates/{hsn_code}")
async def get_gst_rate_for_hsn(
    hsn_code: str,
    db: Session = Depends(get_db)
):
    """Get current GST rate for HSN code"""
    from datetime import date
    
    # Query GST rates table
    query = """
        SELECT hsn_code, description, gst_rate, cess_rate, category
        FROM gst_rates
        WHERE hsn_code = :hsn_code
          AND is_active = true
          AND effective_from <= :today
          AND (effective_until IS NULL OR effective_until >= :today)
        ORDER BY effective_from DESC
        LIMIT 1
    """
    
    result = db.execute(query, {'hsn_code': hsn_code, 'today': date.today()}).fetchone()
    
    if not result:
        raise HTTPException(404, f"GST rate not found for HSN {hsn_code}")
    
    return {
        'hsn_code': result[0],
        'description': result[1],
        'gst_rate': float(result[2]),
        'cess_rate': float(result[3]),
        'category': result[4],
        'cgst_rate': float(result[2]) / 2,
        'sgst_rate': float(result[2]) / 2,
        'igst_rate': float(result[2])
    }


# ============================================================
# E-INVOICE ENDPOINTS
# ============================================================

@router.post("/e-invoice/prepare", response_model=Dict)
async def prepare_einvoice_json(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Prepare E-Invoice JSON (doesn't submit to GSP yet)
    
    Returns the JSON payload that would be sent to GSP
    """
    # Get invoice with items
    invoice = db.execute("""
        SELECT 
            i.*,
            o.gstin as seller_gstin,
            o.legal_name as seller_legal_name,
            o.name as seller_name,
            o.address as seller_address,
            o.contact_phone as seller_phone,
            o.contact_email as seller_email,
            c.gstin as buyer_gstin,
            c.name as buyer_name,
            c.address as buyer_address,
            c.phone as buyer_phone,
            c.email as buyer_email
        FROM invoices i
        LEFT JOIN organizations o ON i.organization_id = o.id
        LEFT JOIN customers c ON i.customer_id = c.id
        WHERE i.id = :invoice_id
          AND i.organization_id = :org_id
    """, {
        'invoice_id': str(invoice_id),
        'org_id': current_user['organization_id']
    }).fetchone()
    
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    
    # Get line items
    line_items = db.execute("""
        SELECT *
        FROM invoice_items
        WHERE invoice_id = :invoice_id
        ORDER BY id
    """, {'invoice_id': str(invoice_id)}).fetchall()
    
    if not line_items:
        raise HTTPException(400, "Invoice has no line items")
    
    # Prepare E-Invoice
    service = EInvoicePreparationService()
    
    invoice_data = dict(invoice)
    seller_data = {
        'gstin': invoice.seller_gstin,
        'legal_name': invoice.seller_legal_name,
        'name': invoice.seller_name,
        'address': invoice.seller_address,
        'contact_phone': invoice.seller_phone,
        'contact_email': invoice.seller_email
    }
    buyer_data = {
        'gstin': invoice.buyer_gstin,
        'name': invoice.buyer_name,
        'address': invoice.buyer_address,
        'phone': invoice.buyer_phone,
        'email': invoice.buyer_email
    }
    items_data = [dict(item) for item in line_items]
    
    einvoice = service.prepare_einvoice(invoice_data, seller_data, buyer_data, items_data)
    
    # Validate
    is_valid, error = service.validate_einvoice(einvoice)
    
    if not is_valid:
        raise HTTPException(400, f"E-Invoice validation failed: {error}")
    
    return {
        'invoice_id': str(invoice_id),
        'invoice_number': invoice.invoice_number,
        'einvoice_json': einvoice,
        'is_valid': True
    }


@router.post("/e-invoice/generate", response_model=EInvoiceResponse)
async def generate_einvoice(
    request: EInvoiceGenerationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate E-Invoice via GSP
    
    NOTE: This is a placeholder. Actual implementation requires:
    1. GSP provider account (ClearTax, Masters India, etc.)
    2. Digital signature certificate
    3. API credentials
    """
    # TODO: Implement actual GSP integration
    
    raise HTTPException(501, "E-Invoice generation not implemented. GSP integration required.")


# ============================================================
# HSN SUMMARY ENDPOINTS
# ============================================================

@router.get("/hsn-summary/{invoice_id}")
async def get_invoice_hsn_summary(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get HSN-wise summary for an invoice"""
    # Get line items
    items = db.execute("""
        SELECT 
            hsn_code,
            SUM(quantity) as total_quantity,
            SUM(taxable_amount) as total_taxable,
            SUM(cgst_amount) as total_cgst,
            SUM(sgst_amount) as total_sgst,
            SUM(igst_amount) as total_igst,
            SUM(cess_amount) as total_cess,
            cgst_rate + sgst_rate + igst_rate as gst_rate
        FROM invoice_items
        WHERE invoice_id = :invoice_id
        GROUP BY hsn_code, cgst_rate, sgst_rate, igst_rate
        ORDER BY hsn_code
    """, {'invoice_id': str(invoice_id)}).fetchall()
    
    summary = []
    for item in items:
        summary.append({
            'hsn_code': item[0],
            'total_quantity': float(item[1]),
            'taxable_amount': float(item[2]),
            'cgst_amount': float(item[3]),
            'sgst_amount': float(item[4]),
            'igst_amount': float(item[5]),
            'cess_amount': float(item[6]),
            'total_tax': float(item[3]) + float(item[4]) + float(item[5]) + float(item[6]),
            'gst_rate': float(item[7])
        })
    
    return {
        'invoice_id': str(invoice_id),
        'hsn_summary': summary
    }


# ============================================================
# STATE INFORMATION
# ============================================================

@router.get("/states")
async def list_indian_states(db: Session = Depends(get_db)):
    """List all Indian states with codes"""
    states = db.execute("""
        SELECT state_code, state_name, is_union_territory
        FROM indian_states
        ORDER BY state_name
    """).fetchall()
    
    return [
        {
            'state_code': s[0],
            'state_name': s[1],
            'is_union_territory': s[2]
        }
        for s in states
    ]


@router.get("/states/{state_code}")
async def get_state_info(
    state_code: str,
    db: Session = Depends(get_db)
):
    """Get state information by code"""
    state = db.execute("""
        SELECT state_code, state_name, is_union_territory
        FROM indian_states
        WHERE state_code = :code
    """, {'code': state_code}).fetchone()
    
    if not state:
        raise HTTPException(404, f"State not found for code {state_code}")
    
    return {
        'state_code': state[0],
        'state_name': state[1],
        'is_union_territory': state[2]
    }
