"""
Offline Transaction Sync Router
Batch process queued POS transactions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

from app.api.db import get_db
from app.api.services.offline_sync_service import sync_offline_transactions

router = APIRouter(prefix="/offline", tags=["Offline Sync"])

class OfflineTransaction(BaseModel):
    client_transaction_id: str
    cart: Dict
    payment: Dict
    cashier_id: int
    offline_timestamp: str

class SyncRequest(BaseModel):
    transactions: List[OfflineTransaction]

class SyncResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[Dict]
    synced_at: str

@router.post("/sync", response_model=SyncResponse)
async def sync_offline_transactions_endpoint(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """
    Batch process offline transactions
    
    Validates each transaction, checks for duplicates,
    and applies ACID guarantees per transaction
    """
    if not request.transactions:
        raise HTTPException(status_code=400, detail="No transactions to sync")
    
    # Convert Pydantic models to dicts
    transactions = [txn.dict() for txn in request.transactions]
    
    result = sync_offline_transactions(transactions, db)
    
    return SyncResponse(**result)

@router.get("/status")
async def get_sync_status(db: Session = Depends(get_db)):
    """
    Get offline sync status
    Returns last sync time and pending count
    """
    # TODO: Track sync status in database
    return {
        "online": True,
        "last_sync": datetime.now().isoformat(),
        "pending_count": 0
    }
