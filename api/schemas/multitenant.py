"""
Pydantic schemas for multi-tenant architecture
Validation models for organizations and stores
"""

from pydantic import BaseModel, UUID4, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================
# ORGANIZATION SCHEMAS
# ============================================================

class OrganizationBase(BaseModel):
    """Base organization fields"""
    name: str = Field(..., min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    gstin: Optional[str] = Field(None, regex=r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$')
    pan: Optional[str] = Field(None, regex=r'^[A-Z]{5}\d{4}[A-Z]{1}$')
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=20)


class OrganizationCreate(OrganizationBase):
    """Schema for creating new organization"""
    address: Optional[Dict[str, Any]] = {
        'line1': '',
        'line2': '',
        'city': '',
        'state': '',
        'state_code': '',
        'pincode': '',
        'country': 'India'
    }
    subscription_plan: str = Field('free', regex=r'^(free|basic|pro|enterprise)$')


class OrganizationUpdate(BaseModel):
    """Schema for updating organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    upi_vpa: Optional[str] = Field(None, max_length=100)
    settings: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None


class Organization(OrganizationBase):
    """Complete organization model"""
    id: UUID4
    address: Dict[str, Any]
    subscription_plan: str
    subscription_status: str
    trial_ends_at: Optional[datetime]
    subscription_started_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Summary of organization (for listings)"""
    id: UUID4
    name: str
    gstin: Optional[str]
    subscription_plan: str
    subscription_status: str
    is_active: bool
    store_count: int = 0
    
    class Config:
        from_attributes = True


# ============================================================
# STORE SCHEMAS
# ============================================================

class StoreBase(BaseModel):
    """Base store fields"""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    store_type: str = Field('retail', regex=r'^(retail|warehouse|franchise|online)$')
    manager_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None


class StoreCreate(StoreBase):
    """Schema for creating new store"""
    address: Optional[Dict[str, Any]] = {
        'line1': '',
        'line2': '',
        'city': '',
        'state': '',
        'state_code': '',
        'pincode': '',
        'country': 'India'
    }
    operating_hours: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = {}


class StoreUpdate(BaseModel):
    """Schema for updating store"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = None
    store_type: Optional[str] = Field(None, regex=r'^(retail|warehouse|franchise|online)$')
    manager_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    address: Optional[Dict[str, Any]] = None
    operating_hours: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Store(StoreBase):
    """Complete store model"""
    id: UUID4
    organization_id: UUID4
    address: Dict[str, Any]
    operating_hours: Dict[str, Any]
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StoreSummary(BaseModel):
    """Summary of store (for listings)"""
    id: UUID4
    name: str
    code: Optional[str]
    store_type: str
    city: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


# ============================================================
# STATISTICS & ANALYTICS
# ============================================================

class OrganizationStats(BaseModel):
    """Organization statistics"""
    total_stores: int
    active_stores: int
    total_products: int
    total_customers: int
    total_invoices_this_month: int
    revenue_this_month: float
    storage_used_mb: float


class StoreStats(BaseModel):
    """Store statistics"""
    store_id: UUID4
    store_name: str
    total_products: int
    low_stock_items: int
    invoices_today: int
    revenue_today: float
    revenue_this_month: float


# ============================================================
# SUBSCRIPTION & BILLING
# ============================================================

class SubscriptionUpdate(BaseModel):
    """Update subscription plan"""
    plan: str = Field(..., regex=r'^(free|basic|pro|enterprise)$')
    billing_cycle: str = Field('monthly', regex=r'^(monthly|yearly)$')


class SubscriptionStatus(BaseModel):
    """Subscription status details"""
    organization_id: UUID4
    current_plan: str
    status: str
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    next_billing_date: Optional[datetime]
    amount_due: float
    features: Dict[str, bool]


# ============================================================
# MULTI-STORE OPERATIONS
# ============================================================

class StoreTransferRequest(BaseModel):
    """Transfer inventory between stores"""
    from_store_id: UUID4
    to_store_id: UUID4
    product_id: UUID4
    quantity: int = Field(..., gt=0)
    reason: str
    notes: Optional[str] = None


class BulkStoreUpdate(BaseModel):
    """Update multiple stores at once"""
    store_ids: List[UUID4]
    updates: StoreUpdate


# ============================================================
# USER STORE ACCESS
# ============================================================

class UserStoreAccess(BaseModel):
    """User's access to stores"""
    user_id: UUID4
    organization_id: UUID4
    assigned_stores: List[UUID4]
    can_access_all_stores: bool = False


class UpdateUserStoreAccess(BaseModel):
    """Update user's store access"""
    assigned_stores: List[UUID4]
    can_access_all_stores: Optional[bool] = False
