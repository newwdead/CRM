"""
Audit log schemas.
"""
from .base import BaseModel, Optional, datetime, ConfigDict


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
    
    model_config = ConfigDict(from_attributes=True)




