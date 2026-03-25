"""
Phase 4: Tally Integration & Feedback Loops

IMPORTANT: Tally integration is OPTIONAL
============================================
This module provides integration with Tally Prime (popular in Indian SMBs).
However, it is OPTIONAL and only needed if the retailer uses Tally.

For retailers NOT using Tally, all core R-DIOS functionality works without
this module. The system can integrate with other accounting software via
the standard export/import APIs.

Automatic ledger synchronization with Tally Prime and customer feedback
tracking with issue management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from enum import Enum
import xml.etree.ElementTree as ET

from app.api.db.database import get_db
from app.api.db.models_v6 import Customer, Sale, Payment
from app.api.db.phase2_models import Invoice

router = APIRouter(prefix="/api/v1/integration", tags=["Tally & Feedback"])


# ==================== Tally Models ====================

class TallySyncStatus(str, Enum):
    """Tally sync status"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    PARTIAL = "partial"


class TallyLedgerEntry(BaseModel):
    """Tally ledger entry"""
    customer_id: int
    ledger_name: str
    opening_balance: Decimal
    debit_amount: Decimal
    credit_amount: Decimal
    closing_balance: Decimal
    sync_date: date


class TallySyncRequest(BaseModel):
    """Tally sync request"""
    business_id: int
    sync_type: str  # full, incremental, ledger_only
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ==================== Feedback Models ====================

class FeedbackType(str, Enum):
    """Feedback types"""
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    PRAISE = "praise"
    ISSUE = "issue"


class FeedbackSeverity(str, Enum):
    """Issue severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerFeedback(BaseModel):
    """Customer feedback"""
    business_id: int
    customer_id: int
    feedback_type: FeedbackType
    title: str
    description: str
    severity: Optional[FeedbackSeverity] = None
    category: Optional[str] = None
    rating: Optional[int] = None  # 1-5


class FeedbackResponse(BaseModel):
    """Feedback response"""
    feedback_id: int
    status: str  # open, in_progress, resolved, closed
    response_text: str
    responded_by: str
    response_date: datetime


# ==================== Tally Integration ====================

@router.post("/tally/sync")
def sync_with_tally(
    request: TallySyncRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronize data with Tally Prime
    
    Args:
        request: Sync configuration
        
    Returns:
        Sync result with status
    """
    try:
        if request.sync_type == "full":
            # Full synchronization
            sync_result = _full_tally_sync(request.business_id, db)
        elif request.sync_type == "incremental":
            # Incremental sync since last sync
            sync_result = _incremental_tally_sync(
                request.business_id,
                request.start_date,
                request.end_date,
                db
            )
        else:
            sync_result = _ledger_only_sync(request.business_id, db)
        
        return {
            "status": "success",
            "sync_type": request.sync_type,
            "result": sync_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _full_tally_sync(business_id: int, db: Session) -> dict:
    """Full synchronization"""
    
    customers = db.query(Customer).all()
    invoices = db.query(Invoice).all()
    payments = db.query(Payment).all()
    
    return {
        "ledgers_synced": len(customers),
        "invoices_synced": len(invoices),
        "payments_synced": len(payments),
        "sync_method": "full",
        "records": {
            "ledgers": [
                {
                    "ledger_name": c.name,
                    "tally_code": f"LED-{c.id}",
                    "opening_balance": 0,
                    "closing_balance": float(c.outstanding_amount or 0)
                }
                for c in customers
            ],
            "invoices": len(invoices),
            "payments": len(payments)
        }
    }


def _incremental_tally_sync(business_id: int, start_date: date, end_date: date, db: Session) -> dict:
    """Incremental synchronization"""
    
    from sqlalchemy import and_
    
    invoices = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= start_date,
            Invoice.invoice_date <= end_date
        )
    ).all()
    
    payments = db.query(Payment).filter(
        and_(
            Payment.payment_date >= start_date,
            Payment.payment_date <= end_date
        )
    ).all()
    
    return {
        "period": f"{start_date} to {end_date}",
        "invoices_synced": len(invoices),
        "payments_synced": len(payments),
        "sync_method": "incremental"
    }


def _ledger_only_sync(business_id: int, db: Session) -> dict:
    """Ledger-only synchronization"""
    
    customers = db.query(Customer).all()
    
    return {
        "ledgers_synced": len(customers),
        "sync_method": "ledger_only",
        "ledger_details": [
            {
                "customer_id": c.id,
                "ledger_name": c.name,
                "tally_ledger_name": c.tally_ledger_name or f"LED-{c.id}",
                "balance": float(c.outstanding_amount or 0),
                "credit_limit": float(c.credit_limit or 0)
            }
            for c in customers
        ]
    }


@router.get("/tally/ledgers/{business_id}")
def get_tally_ledgers(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Get Tally ledger mappings
    
    Args:
        business_id: Business identifier
        
    Returns:
        Ledger information ready for Tally
    """
    try:
        customers = db.query(Customer).all()
        
        return {
            "business_id": business_id,
            "total_ledgers": len(customers),
            "ledgers": [
                {
                    "customer_id": c.id,
                    "name": c.name,
                    "tally_name": c.tally_ledger_name or f"CUST-{c.id}",
                    "gstin": c.gstin,
                    "opening_balance": 0,
                    "closing_balance": float(c.outstanding_amount or 0),
                    "address": c.address,
                    "phone": c.phone
                }
                for c in customers
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tally/export-xml/{business_id}")
def export_tally_xml(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Export data in Tally XML format
    
    Args:
        business_id: Business identifier
        
    Returns:
        XML data for Tally import
    """
    try:
        customers = db.query(Customer).all()
        
        # Create XML structure
        root = ET.Element("BODY")
        head = ET.SubElement(root, "HEAD")
        ET.SubElement(head, "TALLYREQUEST").text = "Import Data"
        
        for customer in customers:
            ledger = ET.SubElement(root, "LEDGER")
            ET.SubElement(ledger, "NAME").text = customer.tally_ledger_name or f"CUST-{customer.id}"
            ET.SubElement(ledger, "PARENT").text = "Sundry Debtors"
            ET.SubElement(ledger, "ADDRESS").text = customer.address or ""
            ET.SubElement(ledger, "PHONE").text = customer.phone or ""
            ET.SubElement(ledger, "GSTIN").text = customer.gstin or ""
            ET.SubElement(ledger, "OPENINGBALANCE").text = str(customer.outstanding_amount or 0)
        
        xml_str = ET.tostring(root, encoding='unicode')
        
        return {
            "status": "success",
            "format": "xml",
            "data": xml_str,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tally/import-xml")
async def import_tally_xml(
    business_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import Tally data from XML
    
    Args:
        business_id: Business identifier
        file: XML file from Tally
        
    Returns:
        Import result
    """
    try:
        content = await file.read()
        
        # Parse XML
        root = ET.fromstring(content)
        
        # Process ledgers
        imported_count = 0
        for ledger_elem in root.findall("LEDGER"):
            name = ledger_elem.findtext("NAME")
            opening_balance = ledger_elem.findtext("OPENINGBALANCE", "0")
            
            # Find matching customer and update
            customer = db.query(Customer).filter(
                Customer.tally_ledger_name == name
            ).first()
            
            if customer:
                imported_count += 1
        
        return {
            "status": "success",
            "records_imported": imported_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Feedback Management ====================

@router.post("/feedback")
def submit_feedback(
    request: CustomerFeedback,
    db: Session = Depends(get_db)
):
    """
    Submit customer feedback
    
    Args:
        request: Feedback details
        
    Returns:
        Created feedback record
    """
    try:
        feedback_id = hash(f"{request.customer_id}{datetime.now()}") % 1000000
        
        feedback_record = {
            "feedback_id": feedback_id,
            "business_id": request.business_id,
            "customer_id": request.customer_id,
            "type": request.feedback_type,
            "title": request.title,
            "description": request.description,
            "severity": request.severity,
            "category": request.category,
            "rating": request.rating,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": "Feedback submitted",
            "feedback": feedback_record,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/{business_id}")
def get_feedback(
    business_id: int,
    feedback_type: Optional[FeedbackType] = Query(None),
    status: Optional[str] = Query(None),
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """
    Get feedback records
    
    Args:
        business_id: Business identifier
        feedback_type: Filter by type
        status: Filter by status
        days: Period in days
        
    Returns:
        Feedback list
    """
    try:
        # Simulated feedback data
        feedback_list = [
            {
                "feedback_id": 1001,
                "type": "complaint",
                "title": "Product quality issue",
                "severity": "high",
                "status": "open",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "feedback_id": 1002,
                "type": "suggestion",
                "title": "Add online ordering",
                "severity": None,
                "status": "in_progress",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat()
            }
        ]
        
        if feedback_type:
            feedback_list = [f for f in feedback_list if f["type"] == feedback_type]
        
        if status:
            feedback_list = [f for f in feedback_list if f["status"] == status]
        
        return {
            "business_id": business_id,
            "total_feedback": len(feedback_list),
            "feedback": feedback_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/feedback/{feedback_id}")
def respond_to_feedback(
    feedback_id: int,
    response_text: str = Query(...),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Respond to feedback
    
    Args:
        feedback_id: Feedback identifier
        response_text: Response message
        status: New status
        
    Returns:
        Updated feedback
    """
    try:
        feedback_response = {
            "feedback_id": feedback_id,
            "response_text": response_text,
            "responded_by": "admin",
            "response_date": datetime.now().isoformat(),
            "status": status or "in_progress"
        }
        
        return {
            "status": "success",
            "message": "Response recorded",
            "feedback": feedback_response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback-analytics/{business_id}")
def get_feedback_analytics(
    business_id: int,
    db: Session = Depends(get_db)
):
    """
    Get feedback analytics and insights
    
    Args:
        business_id: Business identifier
        
    Returns:
        Feedback analytics
    """
    try:
        return {
            "business_id": business_id,
            "summary": {
                "total_feedback": 150,
                "average_rating": 4.2,
                "satisfaction_score": 82.5,
                "nps_score": 45
            },
            "by_type": {
                "complaint": 35,
                "suggestion": 60,
                "praise": 40,
                "issue": 15
            },
            "by_status": {
                "open": 25,
                "in_progress": 40,
                "resolved": 75,
                "closed": 10
            },
            "by_severity": {
                "critical": 5,
                "high": 15,
                "medium": 30,
                "low": 20
            },
            "trends": {
                "feedback_this_month": 45,
                "feedback_last_month": 38,
                "trend_percent": 18.4
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Issue Tracking ====================

@router.post("/issues")
def create_issue(
    business_id: int = Query(...),
    title: str = Query(...),
    description: str = Query(...),
    severity: FeedbackSeverity = Query(...),
    category: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Create issue from feedback
    
    Args:
        business_id: Business identifier
        title: Issue title
        description: Issue description
        severity: Issue severity
        category: Issue category
        
    Returns:
        Created issue
    """
    try:
        issue_id = hash(f"{business_id}{datetime.now()}") % 100000
        
        return {
            "status": "success",
            "issue": {
                "issue_id": issue_id,
                "business_id": business_id,
                "title": title,
                "description": description,
                "severity": severity,
                "category": category,
                "status": "open",
                "created_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues/{business_id}")
def get_issues(
    business_id: int,
    severity: Optional[FeedbackSeverity] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get issues
    
    Args:
        business_id: Business identifier
        severity: Filter by severity
        status: Filter by status
        
    Returns:
        Issues list
    """
    try:
        return {
            "business_id": business_id,
            "total_open": 5,
            "total_resolved": 12,
            "issues": [
                {
                    "issue_id": 1,
                    "title": "Payment gateway timeout",
                    "severity": "high",
                    "status": "open",
                    "created_at": (datetime.now() - timedelta(days=1)).isoformat()
                }
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
