"""
Pydantic models for organization-related data structures.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class OrgCreate(BaseModel):
    """Model for creating a new organization."""
    organization_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    @field_validator('organization_name')
    @classmethod
    def validate_org_name(cls, v: str) -> str:
        """Validate organization name is not empty after trimming."""
        if not v.strip():
            raise ValueError("Organization name cannot be empty")
        return v.strip()


class OrgUpdate(BaseModel):
    """Model for updating an organization."""
    new_organization_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


class OrgOut(BaseModel):
    """Model for organization output (excludes sensitive data)."""
    organization_name: str
    collection_name: str
    admin_email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

