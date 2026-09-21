"""
Consolidated GST / Billing / Invoicing router.

Replaces:
  - app/routers/gst.py, gst_config.py, gstr1.py
  - app/api/routers/invoicing_v2.py, bill_management.py
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.core.security import get_current_user
from app.api.deps import get_outlet_scope
from app.core.data_isolation import require_outlet_access
from app.models.users import User
from app.models import Invoice as InvoiceModel, Bill

from app.services.gst_calculator import (
    GSTCalculator, calculate_forward_tax, calculate_reverse_tax,
    is_same_state, get_rate_for_category, get_rate_for_hsn,
    calculate_line_item, calculate_line_items, CATEGORY_GST_RATES,
)
from app.services.invoice_pdf_service import generate_invoice_pdf
from app.services.invoice_service import BillService
from app.services import gstr1_service

router = APIRouter(prefix="/gst", tags=["GST / Billing"])

logger = __import__("logging").getLogger(__name__)

# ──────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────

MOCK_COMPANY = {
    "name": "Enterprise Retail Store",
    "address": "Enterprise Park, Bangalore, Karnataka - 560001",
    "gstin": "29ABCDE1234F1Z5",
    "state_code": "29",
    "bank_name": "HDFC Bank",
    "bank_ac": "12345678901234",
    "bank_ifsc": "HDFC0001234",
}

GST_SLABS = {
    "0": {"rate": 0, "description": "Exempt", "examples": ["fresh food", "books", "vegetables"]},
    "5": {"rate": 5, "description": "Reduced Rate", "examples": ["edible oils", "tea", "coffee", "coal"]},
    "12": {"rate": 12, "description": "Standard Rate (Lower)", "examples": ["processed food", "mobile phones"]},
    "18": {"rate": 18, "description": "Standard Rate", "examples": ["electronics", "furniture", "computers"]},
    "28": {"rate": 28, "description": "Luxury / Demerit Rate", "examples": ["automobiles", "tobacco", "luxury goods"]},
}

BUSINESS_TYPES = {
    "grocery": {"name": "Grocery / Kirana Store", "default_category": "groceries", "typical_gst": 0},
    "restaurant": {"name": "Restaurant / Food Service", "default_category": "food", "typical_gst": 5},
    "pharmacy": {"name": "Pharmacy / Medical", "default_category": "pharma", "typical_gst": 12},
    "electronics": {"name": "Electronics / Mobile Shop", "default_category": "electronics", "typical_gst": 18},
    "clothing": {"name": "Clothing / Apparel", "default_category": "clothing", "typical_gst": 12},
    "general": {"name": "General Merchandise", "default_category": "default", "typical_gst": 18},
}

# ════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ════════════════════════════════════════════

class TaxCalculationRequest(BaseModel):
    seller_state_code: str = Field(..., pattern=r'^\d{2}$')
    buyer_state_code: str = Field(..., pattern=r'^\d{2}$')
    reverse_charge: bool = False
    items: List[Dict] = Field(..., description="Line items with product_id, name, hsn_code, quantity, unit_price, discount_percentage, gst_rate")

class SimpleGSTRequest(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(...)
    is_interstate: bool = False

class GSTRateUpdate(BaseModel):
    category: str
    gst_rate: float
    hsn_code: Optional[str] = None
    description: Optional[str] = None

class BusinessTypeConfig(BaseModel):
    business_type: str
    store_id: Optional[int] = 1

class CreateInvoiceRequest(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: str
    line_items: List[Dict]
    gst_rate: float = 18.0
    tds_rate: float = 0
    notes: Optional[str] = None
    due_days: int = 30

class InvoicePaymentRequest(BaseModel):
    amount: float
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None

class CreateBillRequest(BaseModel):
    bill_number: str
    vendor_name: str
    bill_date: datetime
    subtotal: float
    gst_amount: float
    total_amount: float
    vendor_gst: Optional[str] = None
    vendor_phone: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    description: Optional[str] = None

class BillPaymentRequest(BaseModel):
    amount: float
    payment_date: datetime
    payment_method: str

class EInvoiceRequest(BaseModel):
    invoice_id: UUID

# ════════════════════════════════════════════
# TAX CALCULATION
# ════════════════════════════════════════════

@router.post("/calculate")
async def calculate_gst(
    req: SimpleGSTRequest,
    current_user: User = Depends(get_current_user),
):
    rate = get_rate_for_category(req.category)
    result = GSTCalculator.calculate_forward_tax(
        taxable_value=req.amount,
        gst_rate=rate,
        is_interstate=req.is_interstate,
    )
    return {
        "base_amount": float(result.taxable_value),
        "gst_rate_percent": f"{rate}%",
        "cgst_amount": float(result.cgst_amount),
        "sgst_amount": float(result.sgst_amount),
        "igst_amount": float(result.igst_amount),
        "total_gst": float(result.total_tax_amount),
        "total_with_gst": float(result.grand_total),
    }

@router.post("/calculate-tax")
async def calculate_gst_tax(req: TaxCalculationRequest):
    try:
        is_interstate = req.seller_state_code != req.buyer_state_code
        breakdowns, totals = calculate_line_items(
            [dict(i) for i in req.items], is_interstate=is_interstate,
        )
        return {
            "transaction_type": "interstate" if is_interstate else "intrastate",
            "is_interstate": is_interstate,
            "subtotal": float(totals["subtotal"]),
            "total_discount": float(totals["discount"]),
            "taxable_amount": float(totals["taxable"]),
            "cgst_amount": float(totals["cgst"]),
            "sgst_amount": float(totals["sgst"]),
            "igst_amount": float(totals["igst"]),
            "cess_amount": float(totals["cess"]),
            "total_tax": float(totals["total_tax"]),
            "grand_total": float(totals["grand_total"]),
            "line_items": [b.model_dump() for b in breakdowns],
            "hsn_summary": list({b.hsn_code: {"hsn_code": b.hsn_code, "quantity": float(b.quantity), "taxable_amount": float(b.taxable_amount), "total_tax": float(b.total_tax)} for b in breakdowns}.values()),
        }
    except Exception as e:
        raise HTTPException(500, f"Tax calculation failed: {str(e)}")

# ════════════════════════════════════════════
# RATES & CONFIGURATION
# ════════════════════════════════════════════

@router.get("/rates")
async def get_all_rates():
    return {
        "category_rates": {k: {"rate": v} for k, v in CATEGORY_GST_RATES.items()},
        "slabs": GST_SLABS,
    }

@router.get("/rates/hsn/{hsn_code}")
async def get_hsn_rate(hsn_code: str, db: Session = Depends(get_db)):
    rate = get_rate_for_hsn(hsn_code)
    result = db.execute(text("""
        SELECT hsn_code, description, gst_rate, cess_rate, category
        FROM gst_rates WHERE hsn_code = :hsn AND is_active = true
        ORDER BY effective_from DESC LIMIT 1
    """), {"hsn": hsn_code}).fetchone()
    if result:
        r = float(result[2])
        return {"hsn_code": result[0], "description": result[1], "gst_rate": r, "cgst_rate": r / 2, "sgst_rate": r / 2, "igst_rate": r}
    return {"hsn_code": hsn_code, "gst_rate": rate, "cgst_rate": rate / 2, "sgst_rate": rate / 2, "igst_rate": rate}

@router.get("/slabs")
async def get_gst_slabs():
    return {"slabs": GST_SLABS}

@router.get("/config/business-types")
async def get_business_types():
    return {"business_types": [{"id": k, "name": v["name"], "typical_gst_rate": v["typical_gst"], "default_category": v["default_category"]} for k, v in BUSINESS_TYPES.items()]}

@router.get("/config/product-gst/{product_id}")
async def get_product_gst(product_id: int, db: Session = Depends(get_db)):
    product = db.execute(text("""
        SELECT id, name, category, gst_rate, hsn_code FROM products WHERE id = :pid
    """), {"pid": product_id}).fetchone()
    if not product:
        raise HTTPException(404, "Product not found")
    effective = float(product[3] or 18)
    return {
        "product_id": product[0], "product_name": product[1],
        "category": product[2], "hsn_code": product[4] or "9999",
        "effective_gst_rate": effective,
        "cgst": effective / 2, "sgst": effective / 2,
    }

@router.get("/config/category-rates")
async def get_category_rates(db: Session = Depends(get_db)):
    overrides = {}
    try:
        rows = db.execute(text("""
            SELECT category, gst_rate, hsn_code, description, updated_at
            FROM gst_category_rates ORDER BY category
        """)).fetchall()
        overrides = {r[0]: {"rate": float(r[1]), "hsn": r[2], "description": r[3], "source": "custom", "updated": r[4].isoformat() if r[4] else None} for r in rows}
    except Exception:
        pass
    result = {}
    for cat, rate in CATEGORY_GST_RATES.items():
        if cat in overrides:
            result[cat] = overrides[cat]
        else:
            result[cat] = {"rate": rate, "hsn": "", "description": cat.title(), "source": "default", "updated": None}
    return {"category_rates": result}

@router.post("/config/category-rates")
async def set_category_rate(req: GSTRateUpdate, db: Session = Depends(get_db)):
    if req.gst_rate not in [0, 5, 12, 18, 28]:
        raise HTTPException(400, "Rate must be one of: 0, 5, 12, 18, 28")
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS gst_category_rates (
                id SERIAL PRIMARY KEY, category VARCHAR(100) UNIQUE NOT NULL,
                gst_rate DECIMAL(5,2) NOT NULL, hsn_code VARCHAR(20),
                description TEXT, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        db.execute(text("""
            INSERT INTO gst_category_rates (category, gst_rate, hsn_code, description)
            VALUES (:c, :r, :h, :d) ON CONFLICT (category) DO UPDATE
            SET gst_rate = EXCLUDED.gst_rate, hsn_code = EXCLUDED.hsn_code,
                description = EXCLUDED.description, updated_at = NOW()
        """), {"c": req.category.lower(), "r": req.gst_rate, "h": req.hsn_code or "", "d": req.description or req.category.title()})
        db.commit()
        return {"success": True, "message": f"Rate for '{req.category}' set to {req.gst_rate}%"}
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.post("/config/apply-business-type")
async def apply_business_type(req: BusinessTypeConfig, db: Session = Depends(get_db)):
    if req.business_type not in BUSINESS_TYPES:
        raise HTTPException(400, f"Unknown type. Valid: {list(BUSINESS_TYPES.keys())}")
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS gst_category_rates (
            id SERIAL PRIMARY KEY, category VARCHAR(100) UNIQUE NOT NULL,
            gst_rate DECIMAL(5,2) NOT NULL, hsn_code VARCHAR(20),
            description TEXT, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
        )
    """))
    applied = 0
    for cat, rate in CATEGORY_GST_RATES.items():
        if cat == "default":
            continue
        db.execute(text("""
            INSERT INTO gst_category_rates (category, gst_rate, description)
            VALUES (:c, :r, :d) ON CONFLICT (category) DO UPDATE
            SET gst_rate = EXCLUDED.gst_rate, updated_at = NOW()
        """), {"c": cat, "r": rate, "d": f"{cat.title()} - {req.business_type} profile"})
        applied += 1
    db.commit()
    return {"success": True, "business_type": req.business_type, "rates_applied": applied}

# ════════════════════════════════════════════
# INDIAN STATES
# ════════════════════════════════════════════

@router.get("/states")
async def list_states(db: Session = Depends(get_db)):
    states = db.execute(text("""
        SELECT state_code, state_name, is_union_territory FROM indian_states ORDER BY state_name
    """)).fetchall()
    return [{"state_code": s[0], "state_name": s[1], "is_union_territory": s[2]} for s in states]

@router.get("/states/{state_code}")
async def get_state(state_code: str, db: Session = Depends(get_db)):
    state = db.execute(text("""
        SELECT state_code, state_name, is_union_territory FROM indian_states WHERE state_code = :c
    """), {"c": state_code}).fetchone()
    if not state:
        raise HTTPException(404, f"State not found: {state_code}")
    return {"state_code": state[0], "state_name": state[1], "is_union_territory": state[2]}

# ════════════════════════════════════════════
# GST RETURNS (GSTR-1 / GSTR-3B)
# ════════════════════════════════════════════

@router.get("/gstr1")
async def get_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
):
    data = gstr1_service.generate_gstr1_report(db, month, year)
    return {"success": True, "data": data}

@router.get("/gstr1/validate")
async def validate_gstr1(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
):
    data = gstr1_service.validate_gstr1(db, month, year)
    return {"success": True, "data": data}

@router.get("/gstr1/download")
async def download_gstr1_csv(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
):
    return {"success": True, "message": "CSV download not implemented in consolidation. Use /gst/gstr1 for JSON."}

@router.get("/gstr3b")
async def get_gstr3b(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
):
    return {"success": True, "message": "GSTR-3B via consolidated service - see GSTR-1 for details"}

# ════════════════════════════════════════════
# INVOICES (B2B invoicing module)
# ════════════════════════════════════════════

from app.services.audit_service import log_audit_action_sync

@router.post("/invoices")
async def create_invoice(
    req: CreateInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models import InvoiceLineItem, InvoiceTax

    inv_count = db.execute(text("SELECT COUNT(*) FROM invoices WHERE DATE(invoice_date) = DATE('now')")).scalar() or 0
    inv_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{inv_count + 1:04d}"

    subtotal = 0.0
    gst_total = 0.0
    line_data = []
    for item in req.line_items:
        line = item["quantity"] * item["unit_price"]
        gst = line * (item.get("gst_rate", req.gst_rate) / 100)
        subtotal += line
        gst_total += gst
        line_data.append({**item, "line_total": line, "gst_amount": gst})

    tds = (subtotal + gst_total) * (req.tds_rate / 100) if req.tds_rate > 0 else 0
    total = subtotal + gst_total - tds

    inv = InvoiceModel(
        invoice_number=inv_number, customer_id=req.customer_id,
        customer_name=req.customer_name, customer_email=req.customer_email,
        subtotal=subtotal, gst_amount=gst_total, gst_rate=req.gst_rate,
        tds_amount=tds, tds_rate=req.tds_rate, total_amount=total,
        balance_amount=total, status="draft", payment_status="unpaid",
        notes=req.notes, due_date=datetime.now() + timedelta(days=req.due_days),
    )
    db.add(inv)
    db.flush()

    for ld in line_data:
        db.add(InvoiceLineItem(
            invoice_id=inv.id, product_name=ld.get("product_name", ""),
            quantity=ld["quantity"], unit_price=ld["unit_price"],
            line_total=ld["line_total"], gst_rate=ld.get("gst_rate", req.gst_rate),
            gst_amount=ld["gst_amount"],
            line_total_with_tax=ld["line_total"] + ld["gst_amount"],
        ))

    if gst_total > 0:
        db.add(InvoiceTax(invoice_id=inv.id, tax_name="GST", tax_rate=req.gst_rate, tax_amount=gst_total, tax_type="gst"))
    if tds > 0:
        db.add(InvoiceTax(invoice_id=inv.id, tax_name="TDS", tax_rate=req.tds_rate, tax_amount=tds, tax_type="tds"))

    db.commit()
    db.refresh(inv)
    
    log_audit_action_sync(
        db=db,
        action="create_invoice",
        performed_by=current_user.id,
        context={"invoice_id": inv.id, "invoice_number": inv.invoice_number, "total_amount": float(inv.total_amount)}
    )
    
    return {"success": True, "data": {"invoice_id": inv.id, "invoice_number": inv.invoice_number, "status": inv.status, "total_amount": inv.total_amount}}

@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    outlet_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_outlets = get_outlet_scope(current_user, db)
    query = db.query(InvoiceModel)
    if allowed_outlets:
        if outlet_id:
            if not require_outlet_access(current_user, outlet_id):
                raise HTTPException(status_code=403, detail="Access denied to this outlet")
            query = query.filter(InvoiceModel.outlet_id == outlet_id)
        else:
            query = query.filter(InvoiceModel.outlet_id.in_(allowed_outlets))
    elif outlet_id:
        query = query.filter(InvoiceModel.outlet_id == outlet_id)

    if status:
        query = query.filter(InvoiceModel.status == status)
    if payment_status:
        query = query.filter(InvoiceModel.payment_status == payment_status)
    if customer_id:
        query = query.filter(InvoiceModel.customer_id == customer_id)
    total = query.count()
    invoices = query.order_by(InvoiceModel.invoice_date.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"success": True, "data": {
        "invoices": [{
            "invoice_id": i.id, "invoice_number": i.invoice_number,
            "customer_name": i.customer_name,
            "invoice_date": i.invoice_date.isoformat() if i.invoice_date else None,
            "total_amount": i.total_amount, "amount_paid": i.amount_paid,
            "balance_amount": i.balance_amount, "status": i.status,
            "payment_status": i.payment_status,
        } for i in invoices],
        "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page},
    }}

@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if getattr(inv, 'outlet_id', None) and not require_outlet_access(current_user, inv.outlet_id):
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    items = [{"product_name": li.product_name, "quantity": li.quantity, "unit_price": li.unit_price, "line_total": li.line_total, "gst_amount": li.gst_amount} for li in inv.line_items]
    payments = [{"payment_date": p.payment_date.isoformat() if p.payment_date else None, "amount": p.amount_paid, "method": p.payment_method} for p in inv.payments]
    taxes = [{"tax_name": t.tax_name, "tax_rate": t.tax_rate, "tax_amount": t.tax_amount} for t in inv.taxes]
    return {"success": True, "data": {
        "invoice_id": inv.id, "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "customer_name": inv.customer_name, "customer_email": inv.customer_email,
        "subtotal": inv.subtotal, "gst_amount": inv.gst_amount,
        "tds_amount": inv.tds_amount, "total_amount": inv.total_amount,
        "amount_paid": inv.amount_paid, "balance_amount": inv.balance_amount,
        "status": inv.status, "payment_status": inv.payment_status,
        "line_items": items, "payments": payments, "taxes": taxes,
        "notes": inv.notes,
    }}

@router.post("/invoices/{invoice_id}/pay")
async def record_invoice_payment(invoice_id: int, req: InvoicePaymentRequest, db: Session = Depends(get_db)):
    from app.models import Payment as PaymentModel
    inv = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    payment = PaymentModel(
        invoice_id=invoice_id, amount_paid=req.amount,
        payment_method=req.payment_method, reference_number=req.reference_number,
        notes=req.notes,
    )
    db.add(payment)
    inv.amount_paid = (inv.amount_paid or 0) + req.amount
    inv.balance_amount = inv.total_amount - inv.amount_paid
    if inv.balance_amount <= 0:
        inv.status = inv.payment_status = "paid"
    elif inv.amount_paid > 0:
        inv.payment_status = "partially_paid"
    db.commit()
    return {"success": True, "data": {"amount_paid": req.amount, "total_paid": inv.amount_paid, "balance": inv.balance_amount, "status": inv.payment_status}}

@router.patch("/invoices/{invoice_id}/cancel")
async def cancel_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Cancel an invoice (status set to cancelled)."""
    inv = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv.status = "cancelled"
    db.commit()
    return {"success": True, "message": f"Invoice {invoice_id} cancelled successfully."}


@router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    items = [{
        "name": li.product_name, "hsn": "", "qty": li.quantity,
        "rate": li.unit_price, "taxable": li.line_total - (li.gst_amount or 0),
        "gst_rate": li.gst_rate, "cgst": (li.gst_amount or 0) / 2,
        "sgst": (li.gst_amount or 0) / 2, "igst": 0, "total": li.line_total_with_tax or li.line_total,
    } for li in inv.line_items]
    pdf_data = {
        "invoice_number": inv.invoice_number,
        "invoice_date": inv.invoice_date.isoformat() if inv.invoice_date else "",
        "due_date": inv.due_date.isoformat() if inv.due_date else "",
        "customer": {"name": inv.customer_name, "address": inv.billed_to_address or "", "gstin": inv.billed_to_gstin or ""},
        "items": items,
        "totals": {"taxable": inv.subtotal, "cgst": inv.gst_amount / 2, "sgst": inv.gst_amount / 2, "igst": 0, "grand_total": inv.total_amount},
        "payment_status": inv.payment_status,
        "notes": inv.notes,
    }
    pdf_bytes = generate_invoice_pdf(pdf_data, MOCK_COMPANY)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="Invoice_{inv.invoice_number}.pdf"'})

@router.get("/invoices/{sale_id}/gst-detail")
async def get_sale_gst_invoice(
    sale_id: int,
    buyer_state_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    from app.services.invoice_service import InvoiceService
    svc = InvoiceService(db, None)
    try:
        data = svc.generate_invoice_for_sale(sale_id, buyer_state_code)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.get("/invoices/{invoice_id}/hsn-summary")
async def get_hsn_summary(invoice_id: UUID, db: Session = Depends(get_db)):
    items = db.execute(text("""
        SELECT hsn_code, SUM(quantity) as qty, SUM(taxable_amount) as taxable,
               SUM(cgst_amount) as cgst, SUM(sgst_amount) as sgst,
               SUM(igst_amount) as igst, SUM(cess_amount) as cess
        FROM invoice_items WHERE invoice_id = :id
        GROUP BY hsn_code ORDER BY hsn_code
    """), {"id": str(invoice_id)}).fetchall()
    return {"invoice_id": str(invoice_id), "hsn_summary": [{"hsn_code": i[0], "total_quantity": float(i[1]), "taxable_amount": float(i[2]), "cgst": float(i[3]), "sgst": float(i[4]), "igst": float(i[5]), "cess": float(i[6])} for i in items]}

# ════════════════════════════════════════════
# BILLS (vendor bills + GST input credit)
# ════════════════════════════════════════════

@router.post("/bills")
async def create_bill(
    req: CreateBillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = BillService.create_bill(
        bill_number=req.bill_number, vendor_name=req.vendor_name,
        bill_date=req.bill_date, subtotal=req.subtotal,
        gst_amount=req.gst_amount, total_amount=req.total_amount,
        vendor_gst=req.vendor_gst, vendor_phone=req.vendor_phone,
        due_date=req.due_date, notes=req.notes, description=req.description,
        db=db,
    )
    if not result["success"]:
        raise HTTPException(400, result["error"])
        
    log_audit_action_sync(
        db=db,
        action="create_bill",
        performed_by=current_user.id,
        context={"bill_id": result["data"]["bill_id"], "bill_number": req.bill_number, "total_amount": req.total_amount}
    )
    return result

@router.get("/bills")
async def list_bills(
    vendor_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return BillService.get_bills(db=db, vendor_name=vendor_name, status=status, days=days)

@router.get("/bills/{bill_id}")
async def get_bill(bill_id: int, db: Session = Depends(get_db)):
    return BillService.get_bill_details(bill_id, db)

@router.post("/bills/{bill_id}/payment")
async def record_bill_payment(bill_id: int, req: BillPaymentRequest, db: Session = Depends(get_db)):
    return BillService.record_bill_payment(bill_id=bill_id, amount=req.amount, payment_date=req.payment_date, payment_method=req.payment_method, db=db)

# ════════════════════════════════════════════
# E-INVOICE
# ════════════════════════════════════════════

@router.post("/e-invoice/prepare")
async def prepare_einvoice(req: EInvoiceRequest, db: Session = Depends(get_db)):
    return {"invoice_id": str(req.invoice_id), "message": "E-Invoice stub - requires GSP integration. Invoice data available via /gst/invoices/{id}."}

# ════════════════════════════════════════════
# ANALYTICS
# ════════════════════════════════════════════

@router.get("/analytics/gst-summary")
async def gst_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query_str = "SELECT CAST(STRFTIME('%Y-%m', i.invoice_date) AS TEXT) as month, SUM(i.gst_amount) as total_gst, COUNT(*) as inv_count, SUM(i.subtotal) as taxable FROM invoices i WHERE 1=1"
    params = {}
    if start_date:
        query_str += " AND i.invoice_date >= :sd"; params["sd"] = start_date
    if end_date:
        query_str += " AND i.invoice_date <= :ed"; params["ed"] = end_date
    query_str += " GROUP BY month ORDER BY month DESC"
    rows = db.execute(text(query_str), params).fetchall()
    data = [{"month": r[0], "total_gst": round(float(r[1] or 0), 2), "invoice_count": r[2], "taxable_amount": round(float(r[3] or 0), 2)} for r in rows]
    return {"success": True, "data": {"gst_summary": data, "total_gst_collected": sum(d["total_gst"] for d in data), "tax_compliance_ready": True}}

@router.get("/analytics/payment-summary")
async def payment_summary(days: int = Query(90, ge=7, le=365), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT payment_status, COUNT(*), SUM(total_amount), SUM(amount_paid), SUM(balance_amount)
        FROM invoices WHERE invoice_date >= datetime('now', '-' || :d || ' days')
        GROUP BY payment_status
    """), {"d": days}).fetchall()
    summary = {"unpaid": {"count": 0, "value": 0, "collected": 0, "pending": 0},
               "partially_paid": {"count": 0, "value": 0, "collected": 0, "pending": 0},
               "paid": {"count": 0, "value": 0, "collected": 0, "pending": 0}}
    for r in rows:
        s = r[0]
        if s in summary:
            summary[s] = {"count": r[1], "value": round(float(r[2] or 0), 2), "collected": round(float(r[3] or 0), 2), "pending": round(float(r[4] or 0), 2)}
    total_value = sum(v["value"] for v in summary.values())
    total_collected = sum(v["collected"] for v in summary.values())
    return {"success": True, "data": {"summary": summary, "total_invoiced": round(total_value, 2), "total_collected": round(total_collected, 2), "collection_rate": round(total_collected / total_value * 100, 2) if total_value > 0 else 0}}

@router.get("/analytics/overdue-invoices")
async def overdue_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    today = datetime.now()
    base_query = db.query(InvoiceModel).filter(
        InvoiceModel.due_date < today,
        InvoiceModel.payment_status != "paid",
        InvoiceModel.status != "cancelled",
    )
    total_count = base_query.count()
    invoices = base_query.order_by(InvoiceModel.due_date.asc()).offset((page - 1) * per_page).limit(per_page).all()
    data = [{"invoice_number": i.invoice_number, "customer_name": i.customer_name, "due_date": i.due_date.isoformat() if i.due_date else None, "days_overdue": (today - i.due_date).days, "balance_amount": i.balance_amount, "total_amount": i.total_amount} for i in invoices]
    return {
        "success": True, 
        "data": {
            "overdue_invoices": data, 
            "count": len(data),
            "total": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_count + per_page - 1) // per_page,
            "total_overdue": round(sum(d["balance_amount"] for d in data), 2)
        }
    }

@router.get("/analytics/vendor-bills")
async def vendor_bills_analytics(days: int = Query(90, ge=1, le=365), db: Session = Depends(get_db)):
    return BillService.get_vendor_analytics(db=db, days=days)

@router.get("/analytics/pending-bills")
async def pending_bills(days_overdue: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return BillService.get_pending_bills(db=db, days_overdue=days_overdue)
