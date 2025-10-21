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
from .tags import router as tags_router
from .groups import router as groups_router
from .health import router as health_router
from .telegram import router as telegram_router
from .whatsapp import router as whatsapp_router
from .exports import router as exports_router

# Create main API router
api_router = APIRouter()

# Include sub-routers (order matters for path matching)
api_router.include_router(health_router, tags=["Health"])  # No prefix - /health, /version
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(contacts_router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(exports_router, prefix="/contacts/export", tags=["Export/Import"])  # Must be before /contacts prefix
api_router.include_router(duplicates_router, prefix="/api/duplicates", tags=["Duplicates"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(admin_router, prefix="", tags=["Admin"])  # No prefix for backward compatibility
api_router.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
api_router.include_router(tags_router, prefix="/tags", tags=["Tags"])
api_router.include_router(groups_router, prefix="/groups", tags=["Groups"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["Telegram"])
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"])

__all__ = [
    'api_router',
    'auth_router',
    'contacts_router',
    'duplicates_router',
    'settings_router',
    'admin_router',
    'ocr_router',
    'tags_router',
    'groups_router',
    'health_router',
    'telegram_router',
    'whatsapp_router',
    'exports_router'
]


