"""
Contact, Tag, and Group schemas for CRM functionality.
"""
from .base import BaseModel, Optional, List, datetime


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
# Contact Schemas
# ============================================================================

class ContactBase(BaseModel):
    """Base contact schema."""
    uid: Optional[str] = None
    
    # Name fields
    full_name: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    
    # Contact info
    company: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    
    # Additional CRM fields
    phone_mobile: Optional[str] = None
    phone_work: Optional[str] = None
    phone_additional: Optional[str] = None
    fax: Optional[str] = None
    address_additional: Optional[str] = None
    department: Optional[str] = None
    birthday: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    
    # Notes and files
    comment: Optional[str] = None
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
    sequence_number: Optional[int] = None
    tags: List[TagResponse] = []
    groups: List[GroupResponse] = []
    thumbnail_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginatedContactsResponse(BaseModel):
    """Schema for paginated contacts response."""
    items: List[ContactResponse]
    total: int
    page: int
    limit: int
    pages: int
    
    class Config:
        from_attributes = True


# Update forward references for nested models
ContactResponse.model_rebuild()




