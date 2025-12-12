"""
Pydantic models for admin-related data structures.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AdminLogin(BaseModel):
    """Model for admin login request."""
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    """Model for admin output (excludes sensitive data)."""
    admin_id: str
    email: str
    organization_name: str
    org_collection: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut

