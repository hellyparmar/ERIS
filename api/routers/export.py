"""
Export Router - API Endpoints for Data Export
Supports PDF, Excel, and CSV exports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.db.database import get_db
from api.db.models import User, Sale, Product, Invoice, Customer
from api.services.export_service import ExportService
from api.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/export", tags=["Export"])


# ==================== REQUEST MODELS ====================

class ExportRequest(BaseModel):
    format: str = "pdf"  # pdf, excel, csv
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    filters: Optional[dict] = None


# ==================== EXPORT ENDPOINTS ====================

@router.post("/sales")
async def export_sales(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export sales data in specified format
    
    - **format**: pdf, excel, or csv
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    try:
        # Query sales data
        query = db.query(Sale)
        
        # Apply date filters
        if request.start_date:
            start = datetime.fromisoformat(request.start_date)
            query = query.filter(Sale.sale_date >= start)
        
        if request.end_date:
            end = datetime.fromisoformat(request.end_date)
            query = query.filter(Sale.sale_date <= end)
        
        sales = query.all()
        
        # Convert to dict format
        sales_data = [
            {
                "id": sale.id,
                "sale_date": sale.sale_date.strftime("%Y-%m-%d") if sale.sale_date else "",
                "customer_id": sale.customer_id or "",
                "product_id": sale.product_id or "",
                "quantity": sale.quantity or 0,
                "unit_price": float(sale.unit_price or 0),
                "total_amount": float(sale.total_amount or 0),
                "payment_method": sale.payment_method or "",
                "channel": sale.channel or ""
            }
            for sale in sales
        ]
        
        # Generate export
        export_service = ExportService()
        date_range = None
        if request.start_date and request.end_date:
            date_range = f"{request.start_date} to {request.end_date}"
        
        file_bytes = export_service.export_sales_report(
            sales_data,
            format=request.format,
            date_range=date_range
        )
        
        # Determine content type and filename
        content_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        content_type = content_types.get(request.format.lower(), "application/octet-stream")
        extension = extensions.get(request.format.lower(), "bin")
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/inventory")
async def export_inventory(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export inventory data in specified format
    
    - **format**: pdf, excel, or csv
    - **filters**: Optional filters (category, stock_level, etc.)
    """
    try:
        # Query inventory data
        query = db.query(Product)
        
        # Apply filters if provided
        if request.filters:
            if request.filters.get("category"):
                query = query.filter(Product.category == request.filters["category"])
            if request.filters.get("low_stock"):
                query = query.filter(Product.stock_level <= Product.reorder_point)
        
        products = query.all()
        
        # Convert to dict format
        inventory_data = [
            {
                "sku": product.sku or "",
                "name": product.name or "",
                "category": product.category or "",
                "stock_level": product.stock_level or 0,
                "reorder_point": product.reorder_point or 0,
                "cost_price": float(product.cost_price or 0),
                "selling_price": float(product.selling_price or 0),
                "hsn_code": product.hsn_code or "",
                "gst_rate": float(product.gst_rate or 0)
            }
            for product in products
        ]
        
        # Generate export
        export_service = ExportService()
        file_bytes = export_service.export_inventory_report(
            inventory_data,
            format=request.format
        )
        
        # Determine content type and filename
        content_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        content_type = content_types.get(request.format.lower(), "application/octet-stream")
        extension = extensions.get(request.format.lower(), "bin")
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/invoices")
async def export_invoices(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export invoice data in specified format
    
    - **format**: pdf, excel, or csv
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    try:
        # Query invoice data
        query = db.query(Invoice)
        
        # Apply date filters
        if request.start_date:
            start = datetime.fromisoformat(request.start_date)
            query = query.filter(Invoice.invoice_date >= start)
        
        if request.end_date:
            end = datetime.fromisoformat(request.end_date)
            query = query.filter(Invoice.invoice_date <= end)
        
        invoices = query.all()
        
        # Convert to dict format
        invoice_data = [
            {
                "invoice_number": inv.invoice_number or "",
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "",
                "customer_id": inv.customer_id or "",
                "total_amount": float(inv.total_amount or 0),
                "amount_paid": float(inv.amount_paid or 0),
                "amount_due": float(inv.amount_due or 0),
                "payment_status": inv.payment_status.value if inv.payment_status else "",
                "due_date": inv.due_date.strftime("%Y-%m-%d") if inv.due_date else ""
            }
            for inv in invoices
        ]
        
        # Generate export
        export_service = ExportService()
        file_bytes = export_service.export_invoice_report(
            invoice_data,
            format=request.format
        )
        
        # Determine content type and filename
        content_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        content_type = content_types.get(request.format.lower(), "application/octet-stream")
        extension = extensions.get(request.format.lower(), "bin")
        filename = f"invoices_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/customers")
async def export_customers(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export customer data in specified format"""
    try:
        customers = db.query(Customer).all()
        
        customer_data = [
            {
                "id": cust.id,
                "name": cust.name or "",
                "email": cust.email or "",
                "phone": cust.phone or "",
                "city": cust.city or "",
                "state": cust.state or "",
                "loyalty_points": cust.loyalty_points or 0,
                "total_purchases": float(cust.total_purchases or 0)
            }
            for cust in customers
        ]
        
        export_service = ExportService()
        
        if request.format.lower() == "pdf":
            file_bytes = export_service.export_to_pdf(customer_data, "Customer Report")
        elif request.format.lower() == "excel":
            file_bytes = export_service.export_to_excel(customer_data, "Customers", "Customer Report")
        else:
            file_bytes = export_service.export_to_csv(customer_data)
        
        content_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        content_type = content_types.get(request.format.lower(), "application/octet-stream")
        extension = extensions.get(request.format.lower(), "bin")
        filename = f"customers_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        return Response(
            content=file_bytes,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
