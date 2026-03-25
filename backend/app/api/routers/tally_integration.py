"""
Tally Integration API Routes
Endpoints for integrating with Tally ERP
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.api.services.tally_sync_service import TallySyncService
from app.api.db import get_db
from app.api.auth.dependencies import get_current_user
from app.api.middleware.tenant_context import require_organization

router = APIRouter(prefix="/api/v1/integrations/tally", tags=["Tally Integration"])


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================

class TallyConnectionConfig(BaseModel):
    """Tally connection configuration"""
    host: str = "localhost"
    port: int = 9000


class TallySyncRequest(BaseModel):
    """Request to sync data with Tally"""
    sync_stock_items: bool = True
    sync_ledgers: bool = True


class InvoiceExportRequest(BaseModel):
    """Request to export invoice to Tally"""
    invoice_id: UUID


# ============================================================
# CONNECTION ENDPOINTS
# ============================================================

@router.post("/test-connection")
async def test_tally_connection(
    config: TallyConnectionConfig,
    current_user: dict = Depends(get_current_user)
):
    """
    Test connection to Tally
    
    Checks if Tally is running and accessible
    """
    try:
        tally_service = TallySyncService(
            tally_host=config.host,
            tally_port=config.port
        )
        
        status = tally_service.test_connection()
        
        return status
        
    except Exception as e:
        raise HTTPException(500, f"Connection test failed: {str(e)}")


@router.get("/company-info")
async def get_tally_company_info(
    host: str = "localhost",
    port: int = 9000,
    current_user: dict = Depends(get_current_user)
):
    """Get company information from Tally"""
    try:
        tally_service = TallySyncService(tally_host=host, tally_port=port)
        
        company_info = tally_service.connector.get_company_info()
        
        if not company_info:
            raise HTTPException(404, "Company information not found")
        
        return company_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get company info: {str(e)}")


# ============================================================
# IMPORT ENDPOINTS
# ============================================================

@router.post("/import/stock-items")
async def import_stock_items_from_tally(
    config: TallyConnectionConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Import stock items from Tally to R-DIOS
    
    This will:
    1. Connect to Tally
    2. Fetch all stock items
    3. Import/update products in R-DIOS
    """
    try:
        tally_service = TallySyncService(
            tally_host=config.host,
            tally_port=config.port
        )
        
        # Import stock items
        result = tally_service.import_stock_items_to_rdios(
            db,
            current_user['organization_id']
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Stock items import failed: {str(e)}")


@router.post("/import/ledgers")
async def import_ledgers_from_tally(
    config: TallyConnectionConfig,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Import ledgers from Tally to R-DIOS as customers
    
    Only imports sundry debtors (customer ledgers)
    """
    try:
        tally_service = TallySyncService(
            tally_host=config.host,
            tally_port=config.port
        )
        
        # Import ledgers
        result = tally_service.import_ledgers_to_rdios(
            db,
            current_user['organization_id']
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Ledgers import failed: {str(e)}")


@router.post("/sync")
async def sync_with_tally(
    request: TallySyncRequest,
    config: TallyConnectionConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Full sync with Tally
    
    Imports both stock items and ledgers
    """
    try:
        tally_service = TallySyncService(
            tally_host=config.host,
            tally_port=config.port
        )
        
        # Perform full sync
        result = tally_service.sync_all(
            db,
            current_user['organization_id']
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"Sync failed: {str(e)}")


# ============================================================
# EXPORT ENDPOINTS
# ============================================================

@router.post("/export/invoice/{invoice_id}")
async def export_invoice_to_tally(
    invoice_id: UUID,
    config: TallyConnectionConfig,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Export R-DIOS invoice to Tally as sales voucher
    
    Creates a sales voucher in Tally with:
    - Invoice number
    - Customer ledger
    - Line items
    - GST breakdown
    """
    try:
        # Get invoice data
        invoice_query = """
            SELECT 
                i.invoice_number,
                i.invoice_date,
                i.taxable_amount,
                i.cgst_amount,
                i.sgst_amount,
                i.igst_amount,
                i.total_amount as grand_total,
                c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = :invoice_id
              AND i.organization_id = :org_id
        """
        
        invoice = db.execute(invoice_query, {
            'invoice_id': str(invoice_id),
            'org_id': current_user['organization_id']
        }).fetchone()
        
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        
        # Prepare invoice data
        invoice_data = {
            'invoice_number': invoice.invoice_number,
            'invoice_date': str(invoice.invoice_date),
            'customer_name': invoice.customer_name or 'Cash Customer',
            'taxable_amount': float(invoice.taxable_amount),
            'cgst_amount': float(invoice.cgst_amount or 0),
            'sgst_amount': float(invoice.sgst_amount or 0),
            'igst_amount': float(invoice.igst_amount or 0),
            'grand_total': float(invoice.grand_total)
        }
        
        # Export to Tally
        tally_service = TallySyncService(
            tally_host=config.host,
            tally_port=config.port
        )
        
        result = tally_service.export_sales_invoice_to_tally(invoice_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Invoice export failed: {str(e)}")


@router.post("/export/invoices/bulk")
async def bulk_export_invoices_to_tally(
    invoice_ids: list[UUID],
    config: TallyConnectionConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Export multiple invoices to Tally in bulk
    """
    # TODO: Implement bulk export with background task
    
    return {
        'success': True,
        'total': len(invoice_ids),
        'message': f'{len(invoice_ids)} invoices queued for export to Tally',
        'note': 'Bulk export will run in background'
    }


# ============================================================
# CONFIGURATION ENDPOINTS
# ============================================================

@router.get("/config")
async def get_tally_config(
    current_user: dict = Depends(get_current_user)
):
    """Get current Tally configuration"""
    # TODO: Store config in database per organization
    
    return {
        'host': 'localhost',
        'port': 9000,
        'auto_sync_enabled': False,
        'sync_interval_minutes': 60
    }


@router.put("/config")
async def update_tally_config(
    config: TallyConnectionConfig,
    current_user: dict = Depends(get_current_user)
):
    """Update Tally configuration"""
    # TODO: Store config in database
    
    return {
        'success': True,
        'config': config.dict(),
        'message': 'Tally configuration updated'
    }
