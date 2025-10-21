"""
Duplicate contact schemas.
"""
from .base import BaseModel, Optional, datetime
from .contact import ContactResponse
from typing import Dict


class DuplicateContactResponse(BaseModel):
    """Schema for duplicate contact in responses."""
    id: int
    contact_id_1: int
    contact_id_2: int
    similarity_score: float
    match_fields: Optional[Dict[str, float]] = None
    status: str
    auto_detected: bool
    detected_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    merged_into: Optional[int] = None
    
    # Nested contacts
    contact_1: Optional[ContactResponse] = None
    contact_2: Optional[ContactResponse] = None
    
    class Config:
        from_attributes = True




