from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Table, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    color = Column(String, nullable=True, default='#2563eb')  # Default blue
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to contacts
    contacts = relationship('Contact', secondary=contact_tags, back_populates='tags')

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    color = Column(String, nullable=True, default='#10b981')  # Default green
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to contacts
    contacts = relationship('Contact', secondary=contact_groups, back_populates='groups')

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=True)
    sequence_number = Column(Integer, unique=True, index=True, nullable=True)  # Порядковый номер по мере добавления
    
    # Name fields (ФИО)
    full_name = Column(String, nullable=True)  # Полное имя (для обратной совместимости)
    last_name = Column(String, nullable=True)  # Фамилия
    first_name = Column(String, nullable=True)  # Имя
    middle_name = Column(String, nullable=True)  # Отчество
    
    # Contact info
    company = Column(String, nullable=True, index=True)  # Added index for grouping
    position = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)  # Основной телефон (для обратной совместимости)
    address = Column(String, nullable=True)  # Основной адрес
    website = Column(String, nullable=True)
    
    # Additional CRM fields
    phone_mobile = Column(String, nullable=True)  # Мобильный телефон
    phone_work = Column(String, nullable=True)  # Рабочий телефон
    phone_additional = Column(String, nullable=True)  # Дополнительный телефон
    fax = Column(String, nullable=True)  # Факс
    address_additional = Column(String, nullable=True)  # Дополнительный адрес
    department = Column(String, nullable=True)  # Отдел
    birthday = Column(String, nullable=True)  # День рождения
    source = Column(String, nullable=True)  # Источник контакта
    status = Column(String, nullable=True, default='active')  # Статус (active, inactive, lead, client)
    priority = Column(String, nullable=True)  # Приоритет (low, medium, high, vip)
    
    # Notes and files
    comment = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    ocr_raw = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tags = relationship('Tag', secondary=contact_tags, back_populates='contacts')
    groups = relationship('Group', secondary=contact_groups, back_populates='contacts')

class AppSetting(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    username = Column(String, nullable=True)  # Store username for records even if user is deleted
    action = Column(String, nullable=False)  # 'created', 'updated', 'deleted', 'tag_added', 'tag_removed', etc.
    entity_type = Column(String, nullable=False, default='contact')  # 'contact', 'tag', 'group'
    changes = Column(String, nullable=True)  # JSON string of changes
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class SystemSettings(Base):
    """System-wide settings and configuration."""
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String, nullable=True)
    description = Column(String, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DuplicateContact(Base):
    """Store detected duplicate contacts for review and merging."""
    __tablename__ = "duplicate_contacts"
    id = Column(Integer, primary_key=True, index=True)
    contact_id_1 = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    contact_id_2 = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False, index=True)  # 0.0 to 1.0
    match_fields = Column(JSON, nullable=True)  # JSON object: {"name": 0.95, "email": 1.0}
    status = Column(String(20), default='pending', index=True)  # pending, reviewed, merged, ignored
    auto_detected = Column(Boolean, default=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    merged_into = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    contact_1 = relationship('Contact', foreign_keys=[contact_id_1])
    contact_2 = relationship('Contact', foreign_keys=[contact_id_2])
    reviewer = relationship('User', foreign_keys=[reviewed_by])

class OCRCorrection(Base):
    """
    Store OCR corrections for training and improving recognition accuracy.
    Each record represents a manual correction of OCR text block.
    """
    __tablename__ = "ocr_corrections"
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Original OCR data
    original_text = Column(String, nullable=False)  # What OCR recognized
    original_box = Column(String, nullable=False)  # JSON: {x, y, width, height}
    original_confidence = Column(Integer, nullable=True)  # Confidence score (0-100)
    
    # Corrected data
    corrected_text = Column(String, nullable=False)  # What user corrected it to
    corrected_field = Column(String, nullable=False)  # Which field: 'first_name', 'company', etc.
    
    # Metadata for training
    image_path = Column(String, nullable=True)  # Path to original image
    ocr_provider = Column(String, nullable=True)  # 'tesseract', 'parsio', 'google'
    language = Column(String, nullable=True)  # 'rus', 'eng', 'rus+eng'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
