"""
Audit log model for tracking changes.
"""
from .base import Base, Column, Integer, String, DateTime, ForeignKey, func


class AuditLog(Base):
    """Audit log for tracking all changes to contacts, tags, and groups."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = Column(String, nullable=True)  # Store username for records even if user is deleted
    action = Column(String, nullable=False)  # 'created', 'updated', 'deleted', 'tag_added', 'tag_removed', etc.
    entity_type = Column(String, nullable=False, default='contact')  # 'contact', 'tag', 'group'
    changes = Column(String, nullable=True)  # JSON string of changes
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)




