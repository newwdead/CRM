"""
Contact, Tag, and Group models for CRM functionality.
"""
from .base import Base, Column, Integer, String, DateTime, Table, ForeignKey, relationship, func


# Association table for many-to-many relationship between contacts and tags
contact_tags = Table(
    'contact_tags',
    Base.metadata,
    Column('contact_id', Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for many-to-many relationship between contacts and groups
contact_groups = Table(
    'contact_groups',
    Base.metadata,
    Column('contact_id', Integer, ForeignKey('contacts.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True)
)


class Tag(Base):
    """Tag for categorizing contacts."""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, nullable=True, default='#2563eb')  # Default blue
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to contacts
    contacts = relationship('Contact', secondary=contact_tags, back_populates='tags')


class Group(Base):
    """Group for organizing contacts."""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    color = Column(String, nullable=True, default='#10b981')  # Default green
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to contacts
    contacts = relationship('Contact', secondary=contact_groups, back_populates='groups')


class Contact(Base):
    """Business contact with full CRM fields."""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=True)
    sequence_number = Column(Integer, unique=True, index=True, nullable=True)  # Sequential number
    
    # Name fields (Full Name breakdown)
    full_name = Column(String, nullable=True)  # Full name (for backward compatibility)
    last_name = Column(String, nullable=True)  # Last name / Фамилия
    first_name = Column(String, nullable=True)  # First name / Имя
    middle_name = Column(String, nullable=True)  # Middle name / Отчество
    
    # Contact info
    company = Column(String, nullable=True, index=True)  # Company name (indexed for grouping)
    position = Column(String, nullable=True)  # Job position
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # Primary phone (for backward compatibility)
    address = Column(String, nullable=True)  # Primary address
    website = Column(String, nullable=True)
    
    # Additional CRM fields
    phone_mobile = Column(String, nullable=True)  # Mobile phone
    phone_work = Column(String, nullable=True)  # Work phone
    phone_additional = Column(String, nullable=True)  # Additional phone
    fax = Column(String, nullable=True)  # Fax
    address_additional = Column(String, nullable=True)  # Additional address
    department = Column(String, nullable=True)  # Department
    birthday = Column(String, nullable=True)  # Birthday
    source = Column(String, nullable=True)  # Contact source
    status = Column(String, nullable=True, default='active')  # Status (active, inactive, lead, client)
    priority = Column(String, nullable=True)  # Priority (low, medium, high, vip)
    
    # Notes and files
    comment = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)  # Original photo path
    thumbnail_path = Column(String, nullable=True)  # Thumbnail path
    ocr_raw = Column(String, nullable=True)  # Raw OCR text
    
    # QR Code data
    has_qr_code = Column(Integer, nullable=True, default=0)  # 1 if QR code detected, 0 otherwise
    qr_data = Column(String, nullable=True)  # Raw QR code data (vCard, MeCard, URL, etc.)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tags = relationship('Tag', secondary=contact_tags, back_populates='contacts')
    groups = relationship('Group', secondary=contact_groups, back_populates='contacts')




