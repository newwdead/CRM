"""
API Routes
"""
from fastapi import APIRouter

# Import all routers
from .auth import router as auth_router
from .contacts import router as contacts_router
from .duplicates import router as duplicates_router
from .settings import router as settings_router
from .admin import router as admin_router
from .ocr import router as ocr_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(contacts_router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(duplicates_router, prefix="/api/duplicates", tags=["Duplicates"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(admin_router, prefix="", tags=["Admin"])  # No prefix for backward compatibility
api_router.include_router(ocr_router, prefix="/ocr", tags=["OCR"])

__all__ = ['api_router', 'auth_router', 'contacts_router', 'duplicates_router', 'settings_router', 'admin_router', 'ocr_router']


