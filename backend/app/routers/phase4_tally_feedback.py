"""
Phase 4 - Tally Sync & Feedback Router
Automatic ledger synchronization with Tally Prime
Customer feedback and issue tracking
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tally", tags=["Tally & Feedback"])


# ==================== Tally Sync Models ====================

class TallySyncLog(BaseModel):
    id: int
    sync_type: str  # ledger, inventory, accounts, bills
    status: str  # pending, in_progress, completed, failed
    records_synced: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class TallyAccount(BaseModel):
    id: int
    name: str
    type: str  # assets, liabilities, income, expenses
    balance: float
    currency: str = "INR"
    last_sync: datetime


class TallyLedger(BaseModel):
    id: int
    account_name: str
    description: str
    amount: float
    transaction_date: datetime
    reference_number: str
    synced: bool


# ==================== Feedback Models ====================

class CustomerFeedback(BaseModel):
    id: int
    customer_name: str
    customer_email: EmailStr
    rating: int  # 1-5
    message: str
    category: str  # product, service, delivery, quality, other
    created_at: datetime
    response: Optional[str]
    status: str  # open, in_progress, resolved, closed


class FeedbackResponse(BaseModel):
    feedback_id: int
    response_message: str
    responded_by: str
    responded_at: datetime


# ==================== Tally Sync Endpoints ====================

@router.get("/sync/status")
async def get_sync_status():
    """Get current Tally sync status"""
    try:
        return {
            "last_sync": datetime.now() - timedelta(minutes=5),
            "next_sync": datetime.now() + timedelta(minutes=55),
            "sync_interval_minutes": 60,
            "status": "operational",
            "last_sync_records": {
                "ledgers": 1245,
                "accounts": 58,
                "bills": 234,
                "inventory": 5620
            },
            "connection_status": "connected"
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/trigger")
async def trigger_tally_sync(
    background_tasks: BackgroundTasks,
    sync_type: str = Query("all", regex="^(all|ledger|inventory|accounts|bills)$")
):
    """Trigger manual Tally sync"""
    try:
        sync_id = int(datetime.now().timestamp() * 1000)
        
        # Add background task
        background_tasks.add_task(perform_tally_sync, sync_id, sync_type)
        
        return {
            "sync_id": sync_id,
            "sync_type": sync_type,
            "status": "initiated",
            "message": f"Tally sync initiated for {sync_type}",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error triggering sync: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def perform_tally_sync(sync_id: int, sync_type: str):
    """Background task to perform Tally sync"""
    try:
        logger.info(f"Starting Tally sync (ID: {sync_id}, Type: {sync_type})")
        
        # Simulate sync process
        await asyncio.sleep(2)
        
        logger.info(f"Tally sync completed (ID: {sync_id})")
    except Exception as e:
        logger.error(f"Error in Tally sync: {str(e)}")


@router.get("/accounts", response_model=List[TallyAccount])
async def get_tally_accounts(limit: int = Query(50, ge=1, le=200)):
    """Get Tally chart of accounts"""
    try:
        accounts = [
            TallyAccount(
                id=i,
                name=f"Account {i}",
                type=["assets", "liabilities", "income", "expenses"][i % 4],
                balance=float(100000 * (i % 10)),
                last_sync=datetime.now() - timedelta(minutes=5)
            )
            for i in range(1, limit + 1)
        ]
        return accounts
    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ledger/{account_id}", response_model=List[TallyLedger])
async def get_account_ledger(
    account_id: int,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Get ledger entries for an account"""
    try:
        ledgers = [
            TallyLedger(
                id=i,
                account_name=f"Account {account_id}",
                description=f"Transaction {i}",
                amount=float(1000 * i),
                transaction_date=datetime.now() - timedelta(days=i),
                reference_number=f"TXN-{account_id}-{i:04d}",
                synced=True
            )
            for i in range(1, limit + 1)
        ]
        return ledgers
    except Exception as e:
        logger.error(f"Error fetching ledger: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-logs", response_model=List[TallySyncLog])
async def get_sync_logs(limit: int = Query(20, ge=1, le=100)):
    """Get recent Tally sync logs"""
    try:
        logs = [
            TallySyncLog(
                id=i,
                sync_type=["ledger", "inventory", "accounts", "bills"][i % 4],
                status=["completed", "failed"][i % 10] if i % 10 == 0 else "completed",
                records_synced=1000 + (i * 100),
                records_failed=0 if i % 10 != 0 else 5,
                started_at=datetime.now() - timedelta(hours=i),
                completed_at=datetime.now() - timedelta(hours=i-1),
                error_message="Database connection timeout" if i % 10 == 0 else None
            )
            for i in range(1, limit + 1)
        ]
        return logs
    except Exception as e:
        logger.error(f"Error fetching sync logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Feedback Endpoints ====================

@router.post("/feedback")
async def submit_feedback(feedback: CustomerFeedback):
    """Submit customer feedback"""
    try:
        feedback_id = int(datetime.now().timestamp() * 1000)
        
        # Store feedback (mock)
        logger.info(f"Feedback submitted: {feedback_id}")
        
        return {
            "id": feedback_id,
            "status": "received",
            "message": "Thank you for your feedback",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback", response_model=List[CustomerFeedback])
async def get_feedback(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get all customer feedback"""
    try:
        feedbacks = [
            CustomerFeedback(
                id=1000 + i,
                customer_name=f"Customer {i}",
                customer_email=f"customer{i}@example.com",
                rating=min(5, (i % 5) + 1),
                message=f"Feedback message {i}",
                category=["product", "service", "delivery", "quality", "other"][i % 5],
                created_at=datetime.now() - timedelta(days=i),
                response=f"Response to feedback {i}" if i % 3 == 0 else None,
                status=["open", "in_progress", "resolved", "closed"][i % 4]
            )
            for i in range(1, limit + 1)
        ]
        
        # Filter by status
        if status:
            feedbacks = [f for f in feedbacks if f.status == status]
        
        # Filter by category
        if category:
            feedbacks = [f for f in feedbacks if f.category == category]
        
        return feedbacks
    except Exception as e:
        logger.error(f"Error fetching feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: int,
    response: FeedbackResponse
):
    """Respond to customer feedback"""
    try:
        return {
            "feedback_id": feedback_id,
            "status": "responded",
            "message": "Response saved",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error responding to feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/analytics")
async def get_feedback_analytics():
    """Get feedback analytics"""
    try:
        return {
            "total_feedback": 5432,
            "average_rating": 4.2,
            "feedback_by_category": {
                "product": 1234,
                "service": 1567,
                "delivery": 890,
                "quality": 543,
                "other": 198
            },
            "feedback_by_status": {
                "open": 234,
                "in_progress": 120,
                "resolved": 4891,
                "closed": 187
            },
            "resolution_time_hours": 24.5,
            "satisfaction_trend": "improving"
        }
    except Exception as e:
        logger.error(f"Error getting feedback analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/summary")
async def get_feedback_summary():
    """Get feedback summary"""
    try:
        return {
            "total_feedback_this_week": 432,
            "average_rating_this_week": 4.3,
            "common_issues": [
                {"issue": "Delivery delays", "count": 45, "percentage": 10.4},
                {"issue": "Product quality", "count": 32, "percentage": 7.4},
                {"issue": "Service timing", "count": 28, "percentage": 6.5}
            ],
            "top_compliments": [
                {"comment": "Great service", "count": 78},
                {"comment": "Fast delivery", "count": 65},
                {"comment": "Quality products", "count": 52}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting feedback summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
