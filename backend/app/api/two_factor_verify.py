"""
2FA Verification endpoint for login flow.
Separate from main two_factor.py to avoid circular imports.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from ..database import get_db
from ..auth_utils import decode_access_token, create_access_token
from ..models.user import User
from ..models.two_factor_auth import TwoFactorAuth, TwoFactorBackupCode
from ..core.two_factor import verify_2fa_token, verify_2fa_backup_code

logger = logging.getLogger(__name__)
router = APIRouter()


class TwoFactorVerifyRequest(BaseModel):
    """Request model for 2FA verification during login."""
    token: str
    is_backup_code: bool = False


@router.post("/verify")
async def verify_two_factor_login(
    request: TwoFactorVerifyRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA code during login flow.
    
    Requires temp token from initial login.
    Returns full access token on successful verification.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    temp_token = authorization.replace("Bearer ", "")
    
    # Decode temp token
    payload = decode_access_token(temp_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify this is a temp 2FA token
    if not payload.get("temp") or not payload.get("2fa_pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint requires a temporary 2FA token"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Get 2FA config
    two_fa = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == user.id,
        TwoFactorAuth.is_enabled == True
    ).first()
    
    if not two_fa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this user"
        )
    
    try:
        # Verify token
        if request.is_backup_code:
            # Verify backup code
            is_valid = verify_2fa_backup_code(
                db=db,
                user_id=user.id,
                code=request.token
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or already used backup code"
                )
            
            logger.info(f"User {user.username} logged in using backup code")
        else:
            # Verify TOTP
            is_valid = verify_2fa_token(
                secret=two_fa.secret,
                token=request.token
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid verification code"
                )
            
            logger.info(f"User {user.username} logged in with 2FA")
        
        # Create full access token
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )

