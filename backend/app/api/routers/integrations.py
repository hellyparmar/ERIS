"""
Tally ERP Integration API Endpoints

Provides REST endpoints for:
- Connection status check
- Invoice synchronization to Tally
- Ledger balance retrieval
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.integrations.tally_integration import TallyIntegration
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integrations"]
)


# Pydantic models for request/response
class InvoiceData(BaseModel):
    """Invoice data to sync to Tally"""
    invoice_id: str = Field(..., description="Unique invoice identifier")
    supplier_name: str = Field(..., description="Supplier/Vendor name")
    invoice_date: str = Field(..., description="Invoice date (YYYY-MM-DD format)")
    amount: float = Field(..., description="Invoice amount")
    description: str = Field(default="", description="Optional description")


class SyncInvoicesRequest(BaseModel):
    """Request to sync invoices to Tally"""
    invoices: List[InvoiceData] = Field(..., description="List of invoices to sync")


class TallyStatusResponse(BaseModel):
    """Tally connection status response"""
    connected: bool = Field(..., description="Is Tally connected")
    message: str = Field(..., description="Status message")
    tally_host: str = Field(..., description="Tally host")
    tally_port: int = Field(..., description="Tally port")
    status_code: int = Field(default=None, description="HTTP status code if available")
    error: str = Field(default=None, description="Error message if any")


class SyncInvoicesResponse(BaseModel):
    """Response from invoice sync operation"""
    status: str = Field(..., description="'success', 'partial', or 'error'")
    message: str = Field(..., description="Detailed message")
    synced_count: int = Field(..., description="Number of successfully synced invoices")
    failed_count: int = Field(..., description="Number of failed invoices")
    details: List[Dict[str, Any]] = Field(..., description="Details of each sync attempt")


class LedgerBalanceResponse(BaseModel):
    """Ledger balance response"""
    status: str = Field(..., description="'success' or 'error'")
    ledger_name: str = Field(..., description="Name of the ledger")
    balance: float = Field(default=None, description="Current balance")
    message: str = Field(..., description="Status message")


# Dependency: Get Tally integration instance
def get_tally_integration() -> TallyIntegration:
    """Get Tally integration instance"""
    return TallyIntegration()


@router.get(
    "/tally/status",
    response_model=TallyStatusResponse,
    summary="Check Tally Connection Status",
    description="Ping Tally ERP server to verify it's running and reachable"
)
async def check_tally_status(
    tally: TallyIntegration = Depends(get_tally_integration),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if Tally ERP is connected and running.
    
    Returns connection status and details about where Tally should be running.
    This endpoint helps diagnose connection issues.
    """
    try:
        status_result = tally.is_connected()
        return status_result
    except Exception as e:
        logger.error(f"Error checking Tally status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking Tally status: {str(e)}"
        )


@router.post(
    "/tally/sync-invoices",
    response_model=SyncInvoicesResponse,
    summary="Sync Invoices to Tally",
    description="Convert and post invoices to Tally ERP as purchase vouchers"
)
async def sync_invoices_to_tally(
    request: SyncInvoicesRequest,
    tally: TallyIntegration = Depends(get_tally_integration),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sync invoices from ERIS to Tally ERP.
    
    Converts invoice data to Tally XML voucher format and posts to Tally's
    built-in web server. Each invoice is converted to a Purchase voucher.
    
    Request body:
    ```json
    {
        "invoices": [
            {
                "invoice_id": "INV001",
                "supplier_name": "ABC Supplies",
                "invoice_date": "2024-01-15",
                "amount": 5000.00,
                "description": "Monthly supplies"
            }
        ]
    }
    ```
    
    Returns sync status for each invoice with success/failure details.
    """
    try:
        if not request.invoices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No invoices provided"
            )
        
        # Convert Pydantic models to dicts for integration
        invoice_dicts = [inv.dict() for inv in request.invoices]
        
        result = tally.sync_vouchers_to_tally(invoice_dicts)
        return result
        
    except Exception as e:
        logger.error(f"Error syncing invoices to Tally: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing invoices to Tally: {str(e)}"
        )


@router.get(
    "/tally/ledger/{ledger_name}/balance",
    response_model=LedgerBalanceResponse,
    summary="Fetch Ledger Balance",
    description="Retrieve ledger balance from Tally for reconciliation"
)
async def fetch_ledger_balance(
    ledger_name: str,
    tally: TallyIntegration = Depends(get_tally_integration),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Fetch the current balance of a specific ledger from Tally.
    
    Used for reconciliation between ERIS and Tally accounting records.
    
    Args:
        ledger_name: Name of the ledger in Tally (e.g., "Sundry Creditors")
    
    Returns the ledger balance if successful.
    """
    try:
        if not ledger_name or not ledger_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ledger name cannot be empty"
            )
        
        result = tally.fetch_ledger_balance(ledger_name)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ledger balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ledger balance: {str(e)}"
        )
