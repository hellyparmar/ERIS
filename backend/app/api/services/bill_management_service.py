"""
Bill Management Service
Handles vendor bills, GST input credit tracking, and payment management
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.db.models import Supplier
from app.api.db.invoicing_models import Bill, Payment, GSTRate, InvoiceTax



class BillManagementService:
    """Service for vendor bill management"""
    
    @staticmethod
    def create_bill(
        bill_number: str,
        supplier_id: int,
        bill_date: datetime,
        items: List[Dict[str, Any]],
        db: Session,
        due_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new vendor bill
        
        Args:
            bill_number: Unique bill identifier
            supplier_id: Vendor/supplier ID
            bill_date: Date of the bill
            items: List of bill items with product_id, quantity, unit_price
            db: Database session
            due_date: Payment due date
            notes: Additional notes
            
        Returns:
            Bill creation result with ID and details
        """
        try:
            # Calculate totals
            subtotal = Decimal("0")
            total_gst = Decimal("0")
            items_data = []
            
            for item in items:
                line_subtotal = Decimal(str(item["unit_price"])) * Decimal(str(item["quantity"]))
                
                # Get GST rate (default 18%)
                gst_rate = BillManagementService._get_gst_rate(item.get("category", "General"), db)
                gst_amount = line_subtotal * Decimal(str(gst_rate)) / Decimal("100")
                
                line_total = line_subtotal + gst_amount
                
                subtotal += line_subtotal
                total_gst += gst_amount
                
                items_data.append({
                    "category": item.get("category", "General"),
                    "description": item.get("description", ""),
                    "quantity": item["quantity"],
                    "unit_price": Decimal(str(item["unit_price"])),
                    "gst_rate": gst_rate,
                    "gst_amount": gst_amount,
                    "line_total": line_total
                })
            
            total_amount = subtotal + total_gst
            
            # Create bill record
            bill = Bill(
                bill_number=bill_number,
                supplier_id=supplier_id,
                bill_date=bill_date,
                due_date=due_date or bill_date,
                subtotal_amount=float(subtotal),
                gst_amount=float(total_gst),
                total_amount=float(total_amount),
                status="draft",
                payment_status="pending",
                notes=notes or "",
                gst_input_available=float(total_gst),  # All GST is input credit
                gst_input_claimed=0.0
            )
            
            db.add(bill)
            db.flush()  # Get the ID
            
            # Create bill items
            # Note: BillItem model doesn't exist, Bill model stores summary only
            # for item in items_data:
            #     bill_item = BillItem(
            #         bill_id=bill.id,
            #         category=item["category"],
            #         description=item["description"],
            #         quantity=item["quantity"],
            #         unit_price=float(item["unit_price"]),
            #         gst_rate=item["gst_rate"],
            #         gst_amount=float(item["gst_amount"]),
            #         line_total=float(item["line_total"])
            #     )
            #     db.add(bill_item)
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "bill_id": bill.id,
                    "bill_number": bill_number,
                    "supplier_id": supplier_id,
                    "subtotal": float(subtotal),
                    "gst_total": float(total_gst),
                    "total_amount": float(total_amount),
                    "status": "draft",
                    "items_count": len(items_data),
                    "gst_input_available": float(total_gst)
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": f"Failed to create bill: {str(e)}"}
    
    @staticmethod
    def get_bills(
        db: Session,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        days: int = 90
    ) -> Dict[str, Any]:
        """Get bills with optional filters"""
        try:
            query = db.query(Bill).filter(
                Bill.bill_date >= func.datetime('now', f'-{days} days')
            )
            
            if supplier_id:
                query = query.filter(Bill.supplier_id == supplier_id)
            if status:
                query = query.filter(Bill.status == status)
            
            bills = query.all()
            
            return {
                "success": True,
                "data": {
                    "total": len(bills),
                    "bills": [
                        {
                            "id": bill.id,
                            "bill_number": bill.bill_number,
                            "supplier_id": bill.supplier_id,
                            "bill_date": bill.bill_date,
                            "due_date": bill.due_date,
                            "subtotal": bill.subtotal_amount,
                            "gst": bill.gst_amount,
                            "total": bill.total_amount,
                            "status": bill.status,
                            "payment_status": bill.payment_status,
                            "gst_input_available": bill.gst_input_available,
                            "gst_input_claimed": bill.gst_input_claimed
                        }
                        for bill in bills
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_bill_details(bill_id: int, db: Session) -> Dict[str, Any]:
        """Get detailed bill information with items"""
        try:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return {"success": False, "error": f"Bill {bill_id} not found"}
            
            # BillItem model doesn't exist
            items = []  # db.query(BillItem).filter(BillItem.bill_id == bill_id).all()
            
            return {
                "success": True,
                "data": {
                    "bill": {
                        "id": bill.id,
                        "bill_number": bill.bill_number,
                        "supplier_id": bill.supplier_id,
                        "bill_date": bill.bill_date,
                        "due_date": bill.due_date,
                        "subtotal": bill.subtotal_amount,
                        "gst": bill.gst_amount,
                        "total": bill.total_amount,
                        "status": bill.status,
                        "payment_status": bill.payment_status,
                        "notes": bill.notes,
                        "gst_input_available": bill.gst_input_available,
                        "gst_input_claimed": bill.gst_input_claimed,
                        "created_at": bill.created_at
                    },
                    "items": [
                        {
                            "id": item.id,
                            "category": item.category,
                            "description": item.description,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "gst_rate": item.gst_rate,
                            "gst_amount": item.gst_amount,
                            "line_total": item.line_total
                        }
                        for item in items
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def record_bill_payment(
        bill_id: int,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str,
        db: Session,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a payment against a bill"""
        try:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return {"success": False, "error": f"Bill {bill_id} not found"}
            
            if Decimal(str(amount)) > Decimal(str(bill.total_amount)):
                return {"success": False, "error": "Payment amount exceeds bill total"}
            
            # Create payment record
            payment = Payment(
                bill_id=bill_id,
                amount=float(amount),
                payment_date=payment_date,
                payment_method=payment_method,
                status="completed",
                notes=notes or ""
            )
            
            db.add(payment)
            
            # Update bill payment status
            total_paid = (bill.amount_paid or 0) + float(amount)
            bill.amount_paid = total_paid
            
            if total_paid >= bill.total_amount:
                bill.payment_status = "paid"
                bill.paid_date = payment_date
            elif total_paid > 0:
                bill.payment_status = "partial"
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "payment_id": payment.id,
                    "bill_id": bill_id,
                    "amount": float(amount),
                    "payment_date": payment_date,
                    "payment_method": payment_method,
                    "bill_status": bill.payment_status,
                    "total_paid": total_paid,
                    "remaining": bill.total_amount - total_paid
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def claim_gst_input(
        bill_id: int,
        amount: Optional[Decimal] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Claim GST input credit from bill"""
        try:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return {"success": False, "error": f"Bill {bill_id} not found"}
            
            claim_amount = amount or Decimal(str(bill.gst_input_available))
            
            if Decimal(str(claim_amount)) > Decimal(str(bill.gst_input_available)):
                return {"success": False, "error": "Claim amount exceeds available GST"}
            
            bill.gst_input_claimed = float(Decimal(str(bill.gst_input_claimed or 0)) + claim_amount)
            bill.gst_input_available = float(
                Decimal(str(bill.gst_input_available)) - claim_amount
            )
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "bill_id": bill_id,
                    "gst_claimed": float(claim_amount),
                    "gst_available": bill.gst_input_available,
                    "total_gst": bill.gst_amount
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_gst_input_summary(db: Session, days: int = 90) -> Dict[str, Any]:
        """Get GST input credit summary"""
        try:
            bills = db.query(Bill).filter(
                Bill.bill_date >= func.datetime('now', f'-{days} days')
            ).all()
            
            total_gst = Decimal("0")
            total_claimed = Decimal("0")
            total_available = Decimal("0")
            
            for bill in bills:
                total_gst += Decimal(str(bill.gst_amount or 0))
                total_claimed += Decimal(str(bill.gst_input_claimed or 0))
                total_available += Decimal(str(bill.gst_input_available or 0))
            
            return {
                "success": True,
                "data": {
                    "period_days": days,
                    "total_gst_in_bills": float(total_gst),
                    "total_gst_claimed": float(total_claimed),
                    "total_gst_available": float(total_available),
                    "claimed_percent": (float(total_claimed) / float(total_gst) * 100) if total_gst > 0 else 0,
                    "bill_count": len(bills)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_vendor_analytics(
        db: Session,
        supplier_id: Optional[int] = None,
        days: int = 90
    ) -> Dict[str, Any]:
        """Get analytics for vendor bills"""
        try:
            query = db.query(Bill).filter(
                Bill.bill_date >= func.datetime('now', f'-{days} days')
            )
            
            if supplier_id:
                query = query.filter(Bill.supplier_id == supplier_id)
            
            bills = query.all()
            
            total_amount = Decimal("0")
            total_paid = Decimal("0")
            pending_amount = Decimal("0")
            total_gst = Decimal("0")
            
            for bill in bills:
                total_amount += Decimal(str(bill.total_amount or 0))
                total_paid += Decimal(str(bill.amount_paid or 0))
                pending_amount += Decimal(str(bill.total_amount or 0)) - Decimal(str(bill.amount_paid or 0))
                total_gst += Decimal(str(bill.gst_amount or 0))
            
            return {
                "success": True,
                "data": {
                    "period_days": days,
                    "bill_count": len(bills),
                    "total_amount": float(total_amount),
                    "total_paid": float(total_paid),
                    "pending_amount": float(pending_amount),
                    "payment_rate_percent": (float(total_paid) / float(total_amount) * 100) if total_amount > 0 else 0,
                    "total_gst": float(total_gst),
                    "average_bill_value": float(total_amount / len(bills)) if bills else 0
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _get_gst_rate(category: str, db: Session) -> float:
        """Get GST rate for a category"""
        gst_rate = db.query(GSTRate).filter(GSTRate.category == category).first()
        return float(gst_rate.rate) if gst_rate else 18.0


class BillReconciliation:
    """Service for bill reconciliation and GST compliance"""
    
    @staticmethod
    def get_pending_bills(
        db: Session,
        days_overdue: int = 0
    ) -> Dict[str, Any]:
        """Get pending and overdue bills"""
        try:
            query = db.query(Bill).filter(
                Bill.payment_status.in_(["pending", "partial"])
            )
            
            if days_overdue > 0:
                overdue_date = func.datetime('now', f'-{days_overdue} days')
                query = query.filter(Bill.due_date < overdue_date)
            
            bills = query.all()
            
            return {
                "success": True,
                "data": {
                    "total_bills": len(bills),
                    "bills": [
                        {
                            "id": bill.id,
                            "bill_number": bill.bill_number,
                            "supplier_id": bill.supplier_id,
                            "bill_date": bill.bill_date,
                            "due_date": bill.due_date,
                            "total": bill.total_amount,
                            "paid": bill.amount_paid or 0,
                            "pending": bill.total_amount - (bill.amount_paid or 0),
                            "status": bill.payment_status
                        }
                        for bill in bills
                    ]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def reconcile_gst_for_period(
        db: Session,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Generate GST reconciliation report for a period"""
        try:
            sales_invoices = db.query(func.sum(InvoiceTax.tax_amount)).filter(
                InvoiceTax.created_at >= period_start,
                InvoiceTax.created_at <= period_end,
                InvoiceTax.tax_type.in_(["SGST", "CGST", "IGST", "GST"])
            ).scalar() or 0
            
            bills = db.query(Bill).filter(
                Bill.bill_date >= period_start,
                Bill.bill_date <= period_end
            ).all()
            
            purchase_gst = sum(bill.gst_amount or 0 for bill in bills)
            gst_input_claimed = sum(bill.gst_input_claimed or 0 for bill in bills)
            
            net_gst = float(sales_invoices) - gst_input_claimed
            
            return {
                "success": True,
                "data": {
                    "period": f"{period_start.date()} to {period_end.date()}",
                    "output_gst": float(sales_invoices),
                    "input_gst_available": float(purchase_gst),
                    "input_gst_claimed": float(gst_input_claimed),
                    "input_gst_available_unclaimed": float(purchase_gst - gst_input_claimed),
                    "net_gst_liability": max(0, net_gst),
                    "net_gst_refund": max(0, -net_gst)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# InvoiceTax already imported at top from app.api.db.invoicing_models
