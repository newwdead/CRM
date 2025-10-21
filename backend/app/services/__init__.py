"""
Service Layer Package

This package contains business logic services that separate concerns between
API endpoints and database operations. Services handle:
- Business logic and validation
- Complex operations involving multiple models
- Transaction management
- Reusable operations across different endpoints
"""

from .base import BaseService
from .contact_service import ContactService
from .duplicate_service import DuplicateService
from .settings_service import SettingsService
from .ocr_service import OCRService

__all__ = [
    'BaseService',
    'ContactService',
    'DuplicateService',
    'SettingsService',
    'OCRService',
]

