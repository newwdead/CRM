"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username must be alphanumeric (can contain _ and -)')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be at most 50 characters')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str  # Can be username or email
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    username: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user data in responses (without sensitive data)."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


# ============================================================================
# Contact Schemas
# ============================================================================

class ContactBase(BaseModel):
    """Base contact schema."""
    uid: Optional[str] = None
    full_name: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    comment: Optional[str] = None
    website: Optional[str] = None
    photo_path: Optional[str] = None
    ocr_raw: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    pass


class ContactUpdate(ContactBase):
    """Schema for updating a contact."""
    pass


class ContactResponse(ContactBase):
    """Schema for contact in responses."""
    id: int
    tags: List['TagResponse'] = []
    groups: List['GroupResponse'] = []
    
    class Config:
        from_attributes = True


# ============================================================================
# Tag Schemas
# ============================================================================

class TagBase(BaseModel):
    """Base tag schema."""
    name: str
    color: Optional[str] = '#2563eb'


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = None
    color: Optional[str] = None


class TagResponse(TagBase):
    """Schema for tag in responses."""
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Group Schemas
# ============================================================================

class GroupBase(BaseModel):
    """Base group schema."""
    name: str
    description: Optional[str] = None
    color: Optional[str] = '#10b981'


class GroupCreate(GroupBase):
    """Schema for creating a group."""
    pass


class GroupUpdate(BaseModel):
    """Schema for updating a group."""
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class GroupResponse(GroupBase):
    """Schema for group in responses."""
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogResponse(BaseModel):
    """Schema for audit log in responses."""
    id: int
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    entity_type: str
    changes: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Need to update forward references
ContactResponse.model_rebuild()

