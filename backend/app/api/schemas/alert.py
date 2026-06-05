"""
Alert API Schemas - Pydantic models for alert requests/responses
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field

from app.models import AlertType, AlertStatus


class AlertFilterParams(BaseModel):
    """Alert filter parameters"""
    alert_type: Optional[AlertType] = None
    severity: Optional[str] = None
    status: Optional[AlertStatus] = None
    outlet_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AlertResponse(BaseModel):
    """Single alert response"""
    alert_id: UUID
    outlet_id: UUID
    product_id: Optional[UUID] = None
    alert_type: AlertType
    status: AlertStatus
    severity: str
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """List of alerts with pagination"""
    total: int
    skip: int
    limit: int
    items: List[AlertResponse]


class AlertSummaryResponse(BaseModel):
    """Alert summary statistics"""
    total_active: int
    total_resolved: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    by_outlet: dict = {}
    by_type: dict = {}


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge an alert"""
    snooze_minutes: Optional[int] = Field(None, ge=5, le=1440)  # 5 min to 24 hours


class AlertStatsResponse(BaseModel):
    """Alert statistics for dashboard"""
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    resolved_today: int
    trending_types: List[dict] = []
