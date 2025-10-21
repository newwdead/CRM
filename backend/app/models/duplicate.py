"""
Duplicate contact detection models.
"""
from .base import Base, Column, Integer, Float, String, Boolean, DateTime, ForeignKey, JSON, relationship, func


class DuplicateContact(Base):
    """Store detected duplicate contacts for review and merging."""
    __tablename__ = "duplicate_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id_1 = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    contact_id_2 = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False, index=True)  # 0.0 to 1.0
    match_fields = Column(JSON, nullable=True)  # JSON object: {"name": 0.95, "email": 1.0}
    status = Column(String(20), default='pending', index=True)  # pending, reviewed, merged, ignored
    auto_detected = Column(Boolean, default=False)  # Auto-detected or manually flagged
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    merged_into = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    contact_1 = relationship('Contact', foreign_keys=[contact_id_1])
    contact_2 = relationship('Contact', foreign_keys=[contact_id_2])
    reviewer = relationship('User', foreign_keys=[reviewed_by])




