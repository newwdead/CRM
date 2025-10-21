"""
Application and system settings models.
"""
from .base import Base, Column, Integer, String, DateTime, func


class AppSetting(Base):
    """Application-level settings (key-value store)."""
    __tablename__ = "app_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=True)


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




