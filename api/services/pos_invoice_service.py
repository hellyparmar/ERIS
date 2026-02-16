"""
POS to Invoice Integration Service
Converts POS sales transactions to invoices with automatic line item creation
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.db.models import (
    Sale, SaleItem, Invoice, InvoiceLineItem, Product, 
    Customer, Inventory, InvoiceTax, GSTRate
)


class POSInvoiceService:
    """Service to convert POS sales to invoices"""
    
    @staticmethod
    def convert_sales_to_invoice(
        transaction_id: str,
        db: Session,
        customer_id: Optional[int] = None,
        invoice_type: str = "sales_invoice",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert a POS transaction (multiple sales records) into a formal invoice
        
        Args:
            transaction_id: POS transaction ID (groups multiple sales)
            db: Database session
            customer_id: Optional customer ID (overrides sales customer)
            invoice_type: Type of invoice (sales_invoice, estimate, etc)
            notes: Additional invoice notes
            
        Returns:
            Invoice creation response with ID, number, and items
        """
        try:
            # Fetch all sales for this transaction
            sales = db.query(Sale).filter(
                Sale.transaction_id == transaction_id
            ).all()
            
            if not sales:
                return {
                    "success": False,
                    "error": f"No sales found for transaction {transaction_id}"
                }
            
            # Determine customer from first sale or provided ID
            final_customer_id = customer_id or (sales[0].customer_id if sales else None)
            
            # Calculate totals from all sales
            subtotal = Decimal("0")
            tax_total = Decimal("0")
            items_data = []
            
            for sale in sales:
                product = db.query(Product).filter(Product.id == sale.product_id).first()
                
                line_subtotal = Decimal(str(sale.unit_price)) * Decimal(str(sale.quantity))
                line_tax = Decimal(str(sale.tax)) if sale.tax else Decimal("0")
                
                subtotal += line_subtotal
                tax_total += line_tax
                
                items_data.append({
                    "product_id": sale.product_id,
                    "product_name": product.name if product else f"Product {sale.product_id}",
                    "category": product.category if product else "Unknown",
                    "quantity": sale.quantity,
                    "unit_price": Decimal(str(sale.unit_price)),
                    "tax_rate": POSInvoiceService._get_tax_rate(product, db),
                    "discount": Decimal(str(sale.discount)) if sale.discount else Decimal("0"),
                    "tax_amount": line_tax,
                    "line_total": line_subtotal + line_tax
                })
            
            # Create invoice
            total_amount = subtotal + tax_total
            invoice = Invoice(
                invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                customer_id=final_customer_id,
                invoice_date=datetime.now(),
                due_date=datetime.now(),  # Can be customized
                subtotal_amount=float(subtotal),
                tax_amount=float(tax_total),
                total_amount=float(total_amount),
                status="draft",
                invoice_type=invoice_type,
                notes=notes or f"Created from POS transaction {transaction_id}",
                payment_status="pending"
            )
            
            db.add(invoice)
            db.flush()  # Get the ID without committing
            
            # Create invoice line items
            for item in items_data:
                line_item = InvoiceLineItem(
                    invoice_id=invoice.id,
                    product_id=item["product_id"],
                    description=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=float(item["unit_price"]),
                    discount=float(item["discount"]),
                    tax_rate=item["tax_rate"],
                    tax_amount=float(item["tax_amount"]),
                    line_total=float(item["line_total"])
                )
                db.add(line_item)
            
            # Add taxes to invoice
            tax_details = POSInvoiceService._extract_tax_breakdown(items_data)
            for tax_type, tax_amount in tax_details.items():
                if tax_amount > 0:
                    invoice_tax = InvoiceTax(
                        invoice_id=invoice.id,
                        tax_type=tax_type,
                        tax_amount=float(tax_amount),
                        rate=POSInvoiceService._get_tax_rate_for_type(tax_type)
                    )
                    db.add(invoice_tax)
            
            # Update sales with invoice reference
            for sale in sales:
                sale.invoice_id = invoice.id
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "transaction_id": transaction_id,
                    "customer_id": final_customer_id,
                    "subtotal": float(subtotal),
                    "tax_total": float(tax_total),
                    "total_amount": float(total_amount),
                    "items_count": len(items_data),
                    "status": "draft",
                    "items": items_data
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": f"Failed to convert sales to invoice: {str(e)}"
            }
    
    @staticmethod
    def bulk_convert_sales_to_invoices(
        transaction_ids: List[str],
        db: Session,
        group_by_customer: bool = True
    ) -> Dict[str, Any]:
        """
        Convert multiple POS transactions to invoices
        
        Args:
            transaction_ids: List of POS transaction IDs
            db: Database session
            group_by_customer: If True, group items by customer in one invoice
            
        Returns:
            Batch conversion results
        """
        results = {
            "total_requested": len(transaction_ids),
            "successful": 0,
            "failed": 0,
            "invoices": [],
            "errors": []
        }
        
        if group_by_customer:
            # Group sales by customer first
            customer_sales = {}
            
            for tid in transaction_ids:
                sales = db.query(Sale).filter(Sale.transaction_id == tid).all()
                for sale in sales:
                    cid = sale.customer_id or 0
                    if cid not in customer_sales:
                        customer_sales[cid] = []
                    customer_sales[cid].extend(sales)
            
            # Create one invoice per customer
            for cid, sales_list in customer_sales.items():
                result = POSInvoiceService.convert_sales_to_invoice(
                    transaction_id=transaction_ids[0],  # Use first for reference
                    db=db,
                    customer_id=cid if cid > 0 else None
                )
                
                if result["success"]:
                    results["successful"] += 1
                    results["invoices"].append(result["data"])
                else:
                    results["failed"] += 1
                    results["errors"].append(result["error"])
        else:
            # Create one invoice per transaction
            for tid in transaction_ids:
                result = POSInvoiceService.convert_sales_to_invoice(
                    transaction_id=tid,
                    db=db
                )
                
                if result["success"]:
                    results["successful"] += 1
                    results["invoices"].append(result["data"])
                else:
                    results["failed"] += 1
                    results["errors"].append(result["error"])
        
        return results
    
    @staticmethod
    def link_existing_sales_to_invoices(
        invoice_id: int,
        transaction_ids: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Link existing sales records to an invoice
        
        Args:
            invoice_id: Invoice ID to link to
            transaction_ids: POS transaction IDs to link
            db: Database session
            
        Returns:
            Link operation result
        """
        try:
            # Fetch invoice
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                return {"success": False, "error": f"Invoice {invoice_id} not found"}
            
            # Link all sales from transactions
            linked_count = 0
            for tid in transaction_ids:
                sales = db.query(Sale).filter(Sale.transaction_id == tid).all()
                for sale in sales:
                    if sale.invoice_id is None:
                        sale.invoice_id = invoice_id
                        linked_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "invoice_id": invoice_id,
                    "sales_linked": linked_count,
                    "transactions_processed": len(transaction_ids)
                }
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_uninvoiced_sales(
        db: Session,
        customer_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get sales that haven't been converted to invoices
        
        Args:
            db: Database session
            customer_id: Optional filter by customer
            days: Look back this many days (default 30)
            
        Returns:
            List of uninvoiced transactions
        """
        try:
            query = db.query(Sale).filter(
                Sale.invoice_id.is_(None),
                Sale.transaction_date >= func.datetime('now', f'-{days} days')
            )
            
            if customer_id:
                query = query.filter(Sale.customer_id == customer_id)
            
            sales = query.all()
            
            # Group by transaction
            transactions = {}
            for sale in sales:
                tid = sale.transaction_id
                if tid not in transactions:
                    transactions[tid] = {
                        "transaction_id": tid,
                        "customer_id": sale.customer_id,
                        "transaction_date": sale.transaction_date,
                        "items": [],
                        "total_amount": 0
                    }
                
                transactions[tid]["items"].append({
                    "product_id": sale.product_id,
                    "quantity": sale.quantity,
                    "unit_price": sale.unit_price,
                    "amount": sale.total_amount
                })
                transactions[tid]["total_amount"] += float(sale.total_amount)
            
            return {
                "success": True,
                "data": {
                    "total_transactions": len(transactions),
                    "total_amount": sum(t["total_amount"] for t in transactions.values()),
                    "transactions": list(transactions.values())
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _get_tax_rate(product: Optional[Any], db: Session) -> float:
        """Get applicable tax rate for a product"""
        if not product:
            return 18.0  # Default GST rate
        
        # Fetch GST rate from category
        gst_rate = db.query(GSTRate).filter(
            GSTRate.category == product.category
        ).first()
        
        return float(gst_rate.rate) if gst_rate else 18.0
    
    @staticmethod
    def _get_tax_rate_for_type(tax_type: str) -> float:
        """Get rate for a specific tax type"""
        tax_rates = {
            "SGST": 9.0,
            "CGST": 9.0,
            "IGST": 18.0,
            "GST": 18.0,
            "TDS": 2.0
        }
        return tax_rates.get(tax_type, 0.0)
    
    @staticmethod
    def _extract_tax_breakdown(items_data: List[Dict]) -> Dict[str, Decimal]:
        """Extract tax breakdown from line items"""
        tax_breakdown = {
            "GST": Decimal("0"),
            "TDS": Decimal("0"),
            "other": Decimal("0")
        }
        
        for item in items_data:
            tax_amount = Decimal(str(item["tax_amount"]))
            # Assume GST unless specified
            tax_breakdown["GST"] += tax_amount
        
        return tax_breakdown


class POSInvoiceAnalytics:
    """Analytics for POS-to-Invoice conversion"""
    
    @staticmethod
    def get_conversion_metrics(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get metrics on POS-to-Invoice conversion"""
        try:
            # Total sales in period
            total_sales = db.query(func.count(Sale.id)).filter(
                Sale.transaction_date >= func.datetime('now', f'-{days} days')
            ).scalar()
            
            # Invoiced sales
            invoiced_sales = db.query(func.count(Sale.id)).filter(
                Sale.transaction_date >= func.datetime('now', f'-{days} days'),
                Sale.invoice_id.isnot(None)
            ).scalar()
            
            # Uninvoiced sales
            uninvoiced_sales = total_sales - invoiced_sales
            
            # Revenue metrics
            total_revenue = db.query(func.sum(Sale.total_amount)).filter(
                Sale.transaction_date >= func.datetime('now', f'-{days} days')
            ).scalar() or 0
            
            invoiced_revenue = db.query(func.sum(Sale.total_amount)).filter(
                Sale.transaction_date >= func.datetime('now', f'-{days} days'),
                Sale.invoice_id.isnot(None)
            ).scalar() or 0
            
            uninvoiced_revenue = total_revenue - invoiced_revenue
            
            return {
                "success": True,
                "data": {
                    "period_days": days,
                    "total_sales": total_sales,
                    "invoiced_sales": invoiced_sales,
                    "uninvoiced_sales": uninvoiced_sales,
                    "conversion_rate_percent": (invoiced_sales / total_sales * 100) if total_sales > 0 else 0,
                    "total_revenue": float(total_revenue),
                    "invoiced_revenue": float(invoiced_revenue),
                    "uninvoiced_revenue": float(uninvoiced_revenue),
                    "uninvoiced_revenue_percent": (uninvoiced_revenue / total_revenue * 100) if total_revenue > 0 else 0
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
