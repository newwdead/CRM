"""
OCR Settings API endpoints
Manage OCR version (v1.0 vs v2.0) and configuration
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..database import get_db
from ..models import User
from ..core import auth as auth_utils
from ..core.utils import get_setting, set_setting

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/version')
async def get_ocr_version(
    db: Session = Depends(get_db)
):
    """
    Get current OCR version setting (public access)
    Returns: {"version": "v1.0" | "v2.0"}
    """
    ocr_version = get_setting(db, "ocr_version", "v2.0")
    
    return {
        "version": ocr_version,
        "available_versions": ["v1.0", "v2.0"],
        "v1": {
            "name": "OCR v1.0 (Tesseract)",
            "description": "Classic Tesseract OCR",
            "speed": "Fast (1-2s)",
            "accuracy": "60-70%",
            "features": ["Basic text recognition", "Multiple languages"]
        },
        "v2": {
            "name": "OCR v2.0 (PaddleOCR + LayoutLMv3)",
            "description": "AI-powered OCR with field classification",
            "speed": "Medium (3-5s)",
            "accuracy": "80-90%",
            "features": [
                "PaddleOCR text recognition",
                "LayoutLMv3 AI classification",
                "Auto-validation",
                "MinIO storage",
                "Graceful fallback to v1.0"
            ]
        }
    }


@router.post('/version')
async def set_ocr_version(
    version: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Set OCR version (admin only)
    Body: {"version": "v1.0" | "v2.0"}
    """
    if version not in ["v1.0", "v2.0"]:
        raise HTTPException(status_code=400, detail="Invalid OCR version. Must be 'v1.0' or 'v2.0'")
    
    set_setting(db, "ocr_version", version)
    
    logger.info(f"OCR version changed to {version} by user {current_user.email}")
    
    return {
        "success": True,
        "version": version,
        "message": f"OCR version set to {version}",
        "restart_required": False  # Changes apply immediately
    }


@router.get('/config')
async def get_ocr_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_admin_user)
):
    """
    Get detailed OCR configuration (admin only)
    """
    ocr_version = get_setting(db, "ocr_version", "v2.0")
    
    return {
        "version": ocr_version,
        "v1_config": {
            "provider": "Tesseract",
            "languages": get_setting(db, "TESSERACT_LANGS", "rus+eng"),
            "confidence_threshold": 0.6
        },
        "v2_config": {
            "primary_provider": "PaddleOCR",
            "ai_classifier": "LayoutLMv3",
            "validator_enabled": True,
            "minio_storage": True,
            "fallback_to_v1": True
        },
        "storage": {
            "local": True,
            "minio": True,
            "minio_buckets": ["business-cards", "ocr-results"]
        }
    }


