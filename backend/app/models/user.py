"""
User model for authentication and authorization.
"""
from sqlalchemy.orm import relationship
from .base import Base, Column, Integer, String, Boolean, DateTime, func


class User(Base):
    """User account with authentication and role management."""
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
    
    # Relationships
    two_factor_auth = relationship("TwoFactorAuth", back_populates="user", uselist=False, cascade="all, delete-orphan")
    backup_codes = relationship("TwoFactorBackupCode", back_populates="user", cascade="all, delete-orphan")




