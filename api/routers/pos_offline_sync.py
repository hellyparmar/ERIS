"""
Offline Transaction Sync Endpoint
Receives batched transactions from offline queue
Processes and saves them to database
Returns sync status for each transaction
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from api.db import get_db
from api.utils.jwt_auth import verify_pos_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pos", tags=["Offline Sync"])

# ═══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════

class OfflineTransactionItem(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    total_price: float
    gst_amount: float = 0

class OfflineTransactionPayload(BaseModel):
    id: str  # Client-generated ID for deduplication
    timestamp: int  # Unix timestamp
    type: str  # sale, refund, adjustment
    items: List[OfflineTransactionItem]
    total_amount: float
    payment_method: str  # cash, upi, card, khata
    customer_id: Optional[int] = None
    notes: Optional[str] = None

class SyncRequest(BaseModel):
    transactions: List[OfflineTransactionPayload]

class SyncTransactionResponse(BaseModel):
    transaction_id: str
    status: str  # synced, failed
    error: Optional[str] = None
    server_id: Optional[int] = None  # Transaction ID from server

class SyncResponse(BaseModel):
    success: bool
    synced: List[SyncTransactionResponse]
    failed: List[SyncTransactionResponse]

# ═══════════════════════════════════════════════════════════════
# SYNC ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/sync-offline")
async def sync_offline_transactions(
    request: SyncRequest,
    cashier: Dict = Depends(verify_pos_token),
    db=Depends(get_db)
):
    """
    Sync offline transactions with backend
    Handles conflict detection and deduplication
    """
    
    synced = []
    failed = []
    
    try:
        # Import Sale model
        from api.db.models import Sale
        from sqlalchemy import func
        
        for offline_txn in request.transactions:
            try:
                # Check for duplicates (same client ID within last hour)
                # This prevents double-processing if sync retried
                from datetime import timedelta
                
                hour_ago = datetime.utcnow() - timedelta(hours=1)
                duplicate = db.query(Sale).filter(
                    Sale.transaction_id == offline_txn.id,
                    Sale.created_at >= hour_ago
                ).first()
                
                if duplicate:
                    logger.warning(f"Duplicate transaction detected: {offline_txn.id}")
                    synced.append(SyncTransactionResponse(
                        transaction_id=offline_txn.id,
                        status="synced",
                        server_id=duplicate.id,
                        error="Duplicate transaction (already processed)"
                    ))
                    continue
                
                # Create new sale record
                total_gst = sum(item.gst_amount for item in offline_txn.items)
                subtotal = offline_txn.total_amount - total_gst
                
                sale = Sale(
                    transaction_id=offline_txn.id,
                    cashier_id=cashier.get("user_id"),
                    customer_id=offline_txn.customer_id,
                    total_items=len(offline_txn.items),
                    subtotal=subtotal,
                    gst_amount=total_gst,
                    discount=0,
                    total_amount=offline_txn.total_amount,
                    payment_method=offline_txn.payment_method,
                    payment_status="completed" if offline_txn.payment_method != "khata" else "pending",
                    status="completed",
                    notes=offline_txn.notes or f"[Synced from offline] {offline_txn.type}",
                    created_at=datetime.fromtimestamp(offline_txn.timestamp / 1000),  # Convert ms to seconds
                )
                
                db.add(sale)
                db.flush()  # Get the ID without committing
                
                # Add sale items
                from api.db.models import SaleItem
                
                for item in offline_txn.items:
                    sale_item = SaleItem(
                        sale_id=sale.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        gst_percent=0,  # Already calculated
                        total_price=item.total_price,
                        created_at=datetime.utcnow()
                    )
                    db.add(sale_item)
                
                db.commit()
                
                logger.info(f"Synced offline transaction: {offline_txn.id} → Sale #{sale.id}")
                
                synced.append(SyncTransactionResponse(
                    transaction_id=offline_txn.id,
                    status="synced",
                    server_id=sale.id
                ))
            
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to sync transaction {offline_txn.id}: {e}")
                failed.append(SyncTransactionResponse(
                    transaction_id=offline_txn.id,
                    status="failed",
                    error=str(e)
                ))
        
        return SyncResponse(
            success=len(failed) == 0,
            synced=synced,
            failed=failed
        )
    
    except Exception as e:
        logger.error(f"Sync batch error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process offline sync"
        )

# ═══════════════════════════════════════════════════════════════
# CONFLICT DETECTION
# ═══════════════════════════════════════════════════════════════

@router.get("/sync-status/{transaction_id}")
async def get_sync_status(
    transaction_id: str,
    db=Depends(get_db)
):
    """
    Check if an offline transaction was synced
    Returns: {synced: bool, server_id: int}
    """
    
    try:
        from api.db.models import Sale
        
        sale = db.query(Sale).filter(
            Sale.transaction_id == transaction_id
        ).first()
        
        if sale:
            return {
                "synced": True,
                "server_id": sale.id,
                "created_at": sale.created_at
            }
        else:
            return {
                "synced": False,
                "server_id": None,
                "message": "Transaction not found in backend"
            }
    
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check sync status"
        )
