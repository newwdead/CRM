from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey
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
    
    # Name fields (ФИО)
    full_name = Column(String, nullable=True)  # Полное имя (для обратной совместимости)
    last_name = Column(String, nullable=True)  # Фамилия
    first_name = Column(String, nullable=True)  # Имя
    middle_name = Column(String, nullable=True)  # Отчество
    
    # Contact info
    company = Column(String, nullable=True, index=True)  # Added index for grouping
    position = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Additional CRM fields
    phone_mobile = Column(String, nullable=True)  # Мобильный телефон
    phone_work = Column(String, nullable=True)  # Рабочий телефон
    fax = Column(String, nullable=True)  # Факс
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
