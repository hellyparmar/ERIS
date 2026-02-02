"""
Reports Router
Endpoints for downloading Excel/PDF reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.db.database_postgres import get_db
from api.services.reporting_service import ReportingService
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

@router.get("/sales/download")
async def download_sales_report(
    format: str = Query("xlsx", regex="^(xlsx|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Download Sales Report
    """
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
            # Mock Data Logic duplicated from service (TEMPORARY - should move data fetch to separate method)
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
    format: str = Query("xlsx", regex="^(xlsx|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Download Inventory/Stock Report
    """
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
             # Mock Data Logic duplicated from service
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
    db: Session = Depends(get_db)
):
    """
    Generate and download a Purchase Order PDF
    """
    # Mock PO Data
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
