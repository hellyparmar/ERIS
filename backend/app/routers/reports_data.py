"""
Reports and Data Router
Consolidated API Endpoints for Data Export, Reports, and Data Upload
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Sale, Product, Invoice, Customer
from app.services.reporting_service import ReportingService
from app.services.export_service import ExportService
from app.services.data_service import DataService
from app.api.auth.dependencies import get_current_active_user
from app.api.schemas import UploadResponse, DataSourcesResponse, DataSource

router = APIRouter(prefix="/reports", tags=["Reports & Data"])
data_service = DataService()

# ==================== REQUEST MODELS ====================

class ExportRequest(BaseModel):
    format: str = "pdf"  # pdf, excel, csv
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    filters: Optional[dict] = None

# ==================== REPORTS ====================

@router.get("/sales/download")
async def download_sales_report(
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download Sales Report"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    if format == "xlsx":
        report_buffer = ReportingService.generate_sales_report(start_date, end_date, db)
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            report_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "pdf":
        report_buffer = ReportingService.generate_pdf_report(
            [
                {"order_id": "ORD-001", "date": "2023-10-01", "customer": "John Doe", "amount": 1500.00, "status": "Completed"},
                {"order_id": "ORD-002", "date": "2023-10-02", "customer": "Jane Smith", "amount": 2300.50, "status": "Completed"},
                {"order_id": "ORD-003", "date": "2023-10-02", "customer": "Bob Brown", "amount": 450.00, "status": "Pending"},
            ],
            title=f"Sales Report ({start_date.date()} to {end_date.date()})"
        )
        filename = f"sales_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            report_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/inventory/download")
async def download_inventory_report(
    format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download Inventory/Stock Report"""
    if format == "xlsx":
        report_buffer = ReportingService.generate_inventory_report(db)
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            report_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    elif format == "pdf":
        report_buffer = ReportingService.generate_pdf_report(
            [
                {"product_name": "Premium T-Shirt", "sku": "TSH-001", "stock_qty": 45, "price": 499.00, "status": "In Stock"},
                {"product_name": "Slim Fit Jeans", "sku": "JNS-002", "stock_qty": 12, "price": 1299.00, "status": "Low Stock"},
                {"product_name": "Cotton Socks", "sku": "SOC-005", "stock_qty": 0, "price": 99.00, "status": "Out of Stock"},
            ],
            title="Inventory Status Report"
        )
        filename = f"inventory_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            report_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/purchase-order/download")
async def download_purchase_order(
    item_id: str = Query("GENERAL", min_length=1),
    quantity: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate and download a Purchase Order PDF"""
    po_items = [
        {"item_code": item_id, "description": f"Refill Stock for {item_id}", "quantity": quantity, "unit_price": 450.00, "total": quantity * 450.00},
        {"item_code": "SHIP-001", "description": "Express Shipping", "quantity": 1, "unit_price": 50.00, "total": 50.00},
    ]
    report_buffer = ReportingService.generate_purchase_order(
        po_items, 
        title=f"Purchase Order for {item_id}"
    )
    filename = f"PO_{item_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        report_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== DATA EXPORTS ====================

@router.post("/export/sales")
async def export_sales(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export sales data in specified format"""
    try:
        query = db.query(Sale)
        if request.start_date:
            start = datetime.fromisoformat(request.start_date)
            query = query.filter(Sale.sale_date >= start)
        if request.end_date:
            end = datetime.fromisoformat(request.end_date)
            query = query.filter(Sale.sale_date <= end)
        sales = query.all()
        
        sales_data = [{
            "id": sale.id,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d") if sale.sale_date else "",
            "customer_id": sale.customer_id or "",
            "product_id": sale.product_id or "",
            "quantity": sale.quantity or 0,
            "unit_price": float(sale.unit_price or 0),
            "total_amount": float(sale.total_amount or 0),
            "payment_method": sale.payment_method or "",
            "channel": sale.channel or ""
        } for sale in sales]
        
        export_service = ExportService()
        date_range = f"{request.start_date} to {request.end_date}" if request.start_date and request.end_date else None
        file_bytes = export_service.export_sales_report(sales_data, format=request.format, date_range=date_range)
        
        content_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        return Response(
            content=file_bytes,
            media_type=content_types.get(request.format.lower(), "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename=sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensions.get(request.format.lower(), 'bin')}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/export/inventory")
async def export_inventory(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export inventory data in specified format"""
    try:
        query = db.query(Product)
        if request.filters:
            if request.filters.get("category"):
                query = query.filter(Product.category == request.filters["category"])
            if request.filters.get("low_stock"):
                query = query.filter(Product.stock_level <= Product.reorder_point)
        
        products = query.all()
        inventory_data = [{
            "sku": product.sku or "",
            "name": product.name or "",
            "category": product.category or "",
            "stock_level": product.stock_level or 0,
            "reorder_point": product.reorder_point or 0,
            "cost_price": float(product.cost_price or 0),
            "selling_price": float(product.selling_price or 0),
            "hsn_code": product.hsn_code or "",
            "gst_rate": float(product.gst_rate or 0)
        } for product in products]
        
        export_service = ExportService()
        file_bytes = export_service.export_inventory_report(inventory_data, format=request.format)
        
        content_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        return Response(
            content=file_bytes,
            media_type=content_types.get(request.format.lower(), "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename=inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensions.get(request.format.lower(), 'bin')}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/export/invoices")
async def export_invoices(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export invoice data in specified format"""
    try:
        query = db.query(Invoice)
        if request.start_date:
            start = datetime.fromisoformat(request.start_date)
            query = query.filter(Invoice.invoice_date >= start)
        if request.end_date:
            end = datetime.fromisoformat(request.end_date)
            query = query.filter(Invoice.invoice_date <= end)
        
        invoices = query.all()
        invoice_data = [{
            "invoice_number": inv.invoice_number or "",
            "invoice_date": inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "",
            "customer_id": inv.customer_id or "",
            "total_amount": float(inv.total_amount or 0),
            "amount_paid": float(inv.amount_paid or 0),
            "amount_due": float(inv.amount_due or 0),
            "payment_status": inv.payment_status.value if inv.payment_status else "",
            "due_date": inv.due_date.strftime("%Y-%m-%d") if inv.due_date else ""
        } for inv in invoices]
        
        export_service = ExportService()
        file_bytes = export_service.export_invoice_report(invoice_data, format=request.format)
        
        content_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        return Response(
            content=file_bytes,
            media_type=content_types.get(request.format.lower(), "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename=invoices_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensions.get(request.format.lower(), 'bin')}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/export/customers")
async def export_customers(
    request: ExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export customer data in specified format"""
    try:
        result = await db.execute(select(Customer))
        customers = result.scalars().all()
        customer_data = [{
            "id": cust.id,
            "name": cust.name or "",
            "email": cust.email or "",
            "phone": cust.phone or "",
            "city": cust.city or "",
            "state": cust.state or "",
            "total_purchases": float(cust.total_purchases or 0)
        } for cust in customers]
        
        export_service = ExportService()
        if request.format.lower() == "pdf":
            file_bytes = export_service.export_to_pdf(customer_data, "Customer Report")
        elif request.format.lower() == "excel":
            file_bytes = export_service.export_to_excel(customer_data, "Customers", "Customer Report")
        else:
            file_bytes = export_service.export_to_csv(customer_data)
        
        content_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
        extensions = {"pdf": "pdf", "excel": "xlsx", "csv": "csv"}
        
        return Response(
            content=file_bytes,
            media_type=content_types.get(request.format.lower(), "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename=customers_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensions.get(request.format.lower(), 'bin')}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# ==================== DATA UPLOADS ====================

@router.post("/data/upload/sales", response_model=UploadResponse)
async def upload_sales_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload sales data from CSV file."""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        contents = await file.read()
        return await data_service.process_sales_upload(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/upload/inventory", response_model=UploadResponse)
async def upload_inventory_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload inventory data from CSV file."""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        contents = await file.read()
        return await data_service.process_inventory_upload(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/upload/economic", response_model=UploadResponse)
async def upload_economic_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload macroeconomic data from CSV file."""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be CSV format")
        contents = await file.read()
        return await data_service.process_economic_indicators_upload(contents, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/sources", response_model=DataSourcesResponse)
async def get_data_sources():
    """List all available data sources with metadata."""
    try:
        sources = [
            DataSource(name="Sales Data (Synthetic)", type="sales", last_updated=datetime.now(), row_count=18250),
            DataSource(name="Inventory Data (Synthetic)", type="inventory", last_updated=datetime.now(), row_count=20)
        ]
        return DataSourcesResponse(sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
