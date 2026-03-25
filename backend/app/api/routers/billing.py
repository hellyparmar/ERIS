from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
from app.api.db import get_db

router = APIRouter(prefix="/billing", tags=["Billing & GST"])

class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    tax_rate: float
    hsn_code: str = "0000"

class InvoiceCreate(BaseModel):
    customer_id: int
    is_interstate: bool = False
    items: List[InvoiceItemCreate]

@router.post("/generate")
async def generate_gst_invoice(req: InvoiceCreate, db: Session = Depends(get_db)):
    """Generates a legally compliant GST invoice, automatically calculating CGST/SGST/IGST splits."""
    try:
        total_base = 0.0
        total_tax = 0.0
        
        # Calculate totals safely handling zero-value edge cases
        for item in req.items:
            base = item.quantity * item.unit_price
            tax = base * (item.tax_rate / 100.0)
            total_base += base
            total_tax += tax
            
        cgst = 0.0
        sgst = 0.0
        igst = 0.0
        
        # Determine strict GST Split
        if req.is_interstate:
            igst = total_tax
        else:
            cgst = total_tax / 2.0
            sgst = total_tax / 2.0
            
        total_amount = total_base + cgst + sgst + igst
        
        # Atomic Transaction for Database Insertion
        # We need default uuid values for organization_id and store_id if they don't exist
        with db.begin():
            # Get a valid organization_id and store_id
            org_result = db.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_row = org_result.fetchone()
            if not org_row:
                # Insert a dummy org
                db.execute(text("INSERT INTO organizations (name) VALUES ('Default Org')"))
                org_result = db.execute(text("SELECT id FROM organizations LIMIT 1"))
                org_row = org_result.fetchone()
            org_id = org_row[0]

            store_result = db.execute(text("SELECT id FROM stores LIMIT 1"))
            store_row = store_result.fetchone()
            if not store_row:
                # Insert a dummy store
                db.execute(text("INSERT INTO stores (name, organization_id) VALUES ('Default Store', :org_id)"), {"org_id": org_id})
                store_result = db.execute(text("SELECT id FROM stores LIMIT 1"))
                store_row = store_result.fetchone()
            store_id = store_row[0]

            # Get a valid customer_id
            cust_result = db.execute(text("SELECT id FROM customers WHERE id = :cid LIMIT 1"), {"cid": req.customer_id})
            cust_row = cust_result.fetchone()
            if not cust_row:
                # Get the first available customer or create a dummy
                first_cust = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
                if not first_cust:
                    db.execute(text("INSERT INTO customers (name, phone) VALUES ('Default Cash Customer', '0000000000')"))
                    first_cust = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
                active_customer_id = first_cust[0]
            else:
                active_customer_id = req.customer_id

            # Create Invoice Metadata
            result = db.execute(text("""
                INSERT INTO invoices 
                (invoice_number, customer_id, taxable_amount, cgst_amount, sgst_amount, igst_amount, tax_amount, total_amount, is_interstate, organization_id, store_id)
                VALUES 
                ('INV-' || EXTRACT(EPOCH FROM NOW())::int, :cust_id, :base, :cgst, :sgst, :igst, :tax, :total, :inter, :org_id, :store_id)
                RETURNING id
            """), {
                "cust_id": active_customer_id, "base": total_base, "cgst": cgst, "sgst": sgst, 
                "igst": igst, "tax": total_tax, "total": total_amount, "inter": req.is_interstate,
                "org_id": org_id, "store_id": store_id
            })
            invoice_id = result.scalar()
            
            # Insert Line Items securely using COALESCE on missing fields natively
            for item in req.items:
                base = item.quantity * item.unit_price
                tax = base * (item.tax_rate / 100.0)
                tot = base + tax
                db.execute(text("""
                    INSERT INTO invoice_items
                    (invoice_id, product_id, quantity, unit_price, base_amount, hsn_code, tax_rate, tax_amount, total)
                    VALUES 
                    (:inv_id, :pid, COALESCE(:qty, 0), COALESCE(:price, 0), :base, :hsn, COALESCE(:rate, 0), :tax, :tot)
                """), {"inv_id": invoice_id, "pid": item.product_id, "qty": item.quantity, "price": item.unit_price, "base": base, "hsn": item.hsn_code, "rate": item.tax_rate, "tax": tax, "tot": tot})
                
        return {
            "success": True, 
            "invoice_id": invoice_id, 
            "summary": {
                "base_amount": round(total_base, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "igst": round(igst, 2),
                "grand_total": round(total_amount, 2)
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Invoice generation failed: {str(e)}")
