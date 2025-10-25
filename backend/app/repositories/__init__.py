"""
Repository Layer
Handles all database operations.
"""

from .contact_repository import ContactRepository
from .user_repository import UserRepository
from .ocr_repository import OCRRepository
from .settings_repository import SettingsRepository
from .audit_repository import AuditRepository

__all__ = [
    'ContactRepository',
    'UserRepository',
    'OCRRepository',
    'SettingsRepository',
    'AuditRepository',
]

