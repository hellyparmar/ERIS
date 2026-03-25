"""
Pydantic schemas for RLS management API
"""

from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AccessTypeEnum(str, Enum):
    """Types of database access"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "ALL"


class RLSExceptionCreate(BaseModel):
    """Request to create RLS exception"""
    granted_to_user_id: UUID4 = Field(..., description="User receiving exception")
    target_org_id: UUID4 = Field(..., description="Organization they can access")
    table_name: str = Field(..., description="Table to grant access to")
    access_type: AccessTypeEnum = Field(..., description="Type of access (SELECT, INSERT, UPDATE, DELETE, ALL)")
    expires_hours: int = Field(..., ge=1, le=168, description="Hours until exception expires (max 7 days)")
    reason: str = Field(..., description="Audit trail reason for exception")
    
    class Config:
        json_schema_extra = {
            "example": {
                "granted_to_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "target_org_id": "550e8400-e29b-41d4-a716-446655440001",
                "table_name": "invoices",
                "access_type": "SELECT",
                "expires_hours": 24,
                "reason": "Executive audit of Q4 sales data"
            }
        }


class RLSExceptionResponse(BaseModel):
    """RLS exception details"""
    exception_id: int = Field(..., description="Unique exception ID")
    granted_to: str = Field(..., description="User ID receiving exception")
    target_org: str = Field(..., description="Organization ID")
    table: str = Field(..., description="Table with access granted")
    access_type: str = Field(..., description="Type of access granted")
    expires_in_hours: int = Field(..., description="Hours until expiry")
    reason: str = Field(..., description="Reason for exception")
    created_at: datetime = Field(..., description="When exception was created")


class RLSViolationEntry(BaseModel):
    """Single RLS violation record"""
    hour: datetime
    table_name: str
    violation_type: str
    violation_count: int
    unique_users: int
    unique_orgs: int


class RLSViolationReport(BaseModel):
    """RLS violation statistics"""
    timestamp: datetime = Field(..., description="Report generation time")
    report_hours: int = Field(..., description="Hours covered in report")
    total_violations: int = Field(..., description="Total violation attempts")
    by_table: Dict[str, int] = Field(..., description="Violations grouped by table")
    by_type: Dict[str, int] = Field(..., description="Violations grouped by type")


class RLSTableStatus(BaseModel):
    """Status of RLS on single table"""
    table: str = Field(..., description="Table name")
    rls_enabled: bool = Field(..., description="Is RLS enabled")
    policy_count: int = Field(..., description="Number of policies")


class RLSStatusReport(BaseModel):
    """Complete RLS status report"""
    timestamp: datetime = Field(..., description="Report generation time")
    verification: Dict[str, Any] = Field(..., description="RLS verification details")
    violations_24h: int = Field(..., description="Violations in last 24 hours")
    status: str = Field(..., description="Overall status: protected, warning, or critical")


class RLSContextInfo(BaseModel):
    """Current request's RLS context"""
    user_id: str = Field(..., description="Current user ID")
    org_id: str = Field(..., description="Current organization ID")
    user_role: str = Field(..., description="User's role")
    assigned_stores: List[str] = Field(..., description="Stores user has access to")
    timestamp: datetime = Field(..., description="When context was captured")


class RLSValidationResult(BaseModel):
    """Result of RLS access validation"""
    can_access: bool = Field(..., description="Whether access is allowed")
    user_org: str = Field(..., description="User's organization")
    requested_org: Optional[str] = Field(None, description="Requested organization")
    user_role: Optional[str] = Field(None, description="User's role")
    assigned_stores: Optional[List[str]] = Field(None, description="User's assigned stores")
    reason: str = Field(..., description="Human-readable reason for decision")


class RLSCleanupResult(BaseModel):
    """Result of RLS cleanup operation"""
    status: str = Field(..., description="Cleanup status")
    timestamp: datetime = Field(..., description="Cleanup completion time")
    expired_exceptions_deleted: int = Field(..., description="Expired exceptions removed")
    old_violations_deleted: int = Field(..., description="Old violation records archived")
    error: Optional[str] = Field(None, description="Error message if cleanup failed")
