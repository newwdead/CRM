"""
Two-Factor Authentication (2FA) API Endpoints
Provides setup, verification, and management of 2FA for users
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..database import get_db
from ..models.user import User
from .. import auth_utils
from ..core.two_factor import (
    setup_2fa_for_user,
    enable_2fa_for_user,
    disable_2fa_for_user,
    is_2fa_enabled,
    get_unused_backup_codes_count,
    regenerate_backup_codes,
    verify_2fa_for_login
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Schemas
class TwoFactorSetupResponse(BaseModel):
    """Response for 2FA setup"""
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]
    message: str = "2FA setup initiated. Scan QR code with authenticator app and verify to enable."


class TwoFactorVerifyRequest(BaseModel):
    """Request for 2FA verification"""
    code: str  # 6-digit TOTP code or 8-character backup code


class TwoFactorStatusResponse(BaseModel):
    """Response for 2FA status"""
    is_enabled: bool
    backup_codes_remaining: int = 0
    last_used_at: Optional[str] = None


class TwoFactorRegenerateResponse(BaseModel):
    """Response for backup codes regeneration"""
    backup_codes: List[str]
    message: str = "New backup codes generated. Store them securely."


# API Endpoints

@router.post('/setup', response_model=TwoFactorSetupResponse)
def setup_2fa(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Initiate 2FA setup for the current user.
    Returns secret, QR code, and backup codes.
    2FA is not enabled until verification is complete.
    """
    try:
        # Check if user is admin (only admins can use 2FA for now)
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="2FA is currently only available for admin users"
            )
        
        secret, qr_code, backup_codes = setup_2fa_for_user(db, current_user)
        
        logger.info(f"2FA setup initiated for user {current_user.id}")
        
        return TwoFactorSetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
        
    except Exception as e:
        logger.error(f"2FA setup error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up 2FA: {str(e)}"
        )


@router.post('/enable')
def enable_2fa(
    request: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Enable 2FA after verifying the initial TOTP code.
    """
    try:
        success = enable_2fa_for_user(db, current_user, request.code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please try again."
            )
        
        logger.info(f"2FA enabled for user {current_user.id}")
        
        return {
            "message": "2FA enabled successfully",
            "is_enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA enable error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable 2FA: {str(e)}"
        )


@router.post('/disable')
def disable_2fa(
    request: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Disable 2FA after verifying TOTP code or backup code.
    """
    try:
        success = disable_2fa_for_user(db, current_user, request.code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code or 2FA not enabled"
            )
        
        logger.info(f"2FA disabled for user {current_user.id}")
        
        return {
            "message": "2FA disabled successfully",
            "is_enabled": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA disable error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}"
        )


@router.get('/status', response_model=TwoFactorStatusResponse)
def get_2fa_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get 2FA status for the current user.
    """
    try:
        enabled = is_2fa_enabled(db, current_user)
        backup_count = 0
        last_used = None
        
        if enabled:
            backup_count = get_unused_backup_codes_count(db, current_user)
            
            # Get last used timestamp from database
            from ..models.two_factor_auth import TwoFactorAuth
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == current_user.id
            ).first()
            
            if two_fa and two_fa.last_used_at:
                last_used = two_fa.last_used_at.isoformat()
        
        return TwoFactorStatusResponse(
            is_enabled=enabled,
            backup_codes_remaining=backup_count,
            last_used_at=last_used
        )
        
    except Exception as e:
        logger.error(f"2FA status error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get 2FA status: {str(e)}"
        )


@router.post('/regenerate-backup-codes', response_model=TwoFactorRegenerateResponse)
def regenerate_codes(
    request: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Regenerate backup codes after verifying TOTP code.
    All old backup codes will be invalidated.
    """
    try:
        backup_codes = regenerate_backup_codes(db, current_user, request.code)
        
        if backup_codes is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code or 2FA not enabled"
            )
        
        logger.info(f"Backup codes regenerated for user {current_user.id}")
        
        return TwoFactorRegenerateResponse(
            backup_codes=backup_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup code regeneration error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate backup codes: {str(e)}"
        )


@router.post('/verify')
def verify_2fa(
    request: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Verify 2FA code (for login or other purposes).
    This endpoint is used during the login flow.
    """
    try:
        success = verify_2fa_for_login(db, current_user, request.code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
        
        logger.info(f"2FA verified for user {current_user.id}")
        
        return {
            "message": "2FA verification successful",
            "verified": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}"
        )

