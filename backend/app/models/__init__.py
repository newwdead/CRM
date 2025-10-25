"""
Database models package.

Import all models here to ensure they are registered with SQLAlchemy.
"""
from .base import Base
from .user import User
from .contact import Contact, Tag, Group, contact_tags, contact_groups
from .two_factor_auth import TwoFactorAuth, TwoFactorBackupCode
from .settings import AppSetting, SystemSettings
from .audit import AuditLog
from .ocr import OCRCorrection

__all__ = [
    'Base',
    'User',
    'Contact',
    'Tag',
    'Group',
    'contact_tags',
    'contact_groups',
    'AppSetting',
    'SystemSettings',
    'AuditLog',
    'OCRCorrection',
    'TwoFactorAuth',
    'TwoFactorBackupCode',
]




