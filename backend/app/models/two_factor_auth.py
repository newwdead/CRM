"""
Two-Factor Authentication (2FA) Model
Stores TOTP secrets and backup codes for users
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class TwoFactorAuth(Base):
    """Two-Factor Authentication configuration for users"""
    __tablename__ = "two_factor_auth"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # TOTP Configuration
    secret = Column(String, nullable=False)  # Base32 encoded secret
    is_enabled = Column(Boolean, default=False)  # 2FA activation status
    
    # Backup codes (comma-separated, hashed)
    backup_codes = Column(String, nullable=True)  # 10 backup codes
    
    # Metadata
    enabled_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="two_factor_auth")
    
    def __repr__(self):
        return f"<TwoFactorAuth(user_id={self.user_id}, enabled={self.is_enabled})>"


class TwoFactorBackupCode(Base):
    """Individual backup codes for 2FA recovery"""
    __tablename__ = "two_factor_backup_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Backup code (hashed)
    code_hash = Column(String, nullable=False)
    
    # Usage tracking
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="backup_codes")
    
    def __repr__(self):
        return f"<TwoFactorBackupCode(user_id={self.user_id}, used={self.is_used})>"

