from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"
    ANALYST = "ANALYST"

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[UUID] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserRegister(UserBase):
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    organization_name: str = Field(..., description="Name of the retail organization")
    role: UserRole = Field(UserRole.ANALYST, description="Requested user role")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@example.com",
                "full_name": "Admin User",
                "password": "securepassword123",
                "organization_name": "Mega Retail Corp",
                "role": "ADMIN"
            }
        }
    }

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered user email")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@example.com",
                "password": "securepassword123"
            }
        }
    }

class UserResponse(UserBase):
    id: int
    role: UserRole
    organization_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "admin@example.com",
                "full_name": "Admin User",
                "role": "ADMIN",
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "is_active": True,
                "created_at": "2024-03-24T10:00:00"
            }
        }
    }
