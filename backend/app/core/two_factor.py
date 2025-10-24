"""
Two-Factor Authentication (2FA) Utilities
Provides TOTP generation, verification, QR code generation, and backup codes
"""
import pyotp
import qrcode
import secrets
import hashlib
import io
import base64
from typing import Tuple, List, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from ..models.user import User
from ..models.two_factor_auth import TwoFactorAuth, TwoFactorBackupCode
from ..core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


def generate_totp_secret() -> str:
    """
    Generate a random TOTP secret (Base32 encoded).
    
    Returns:
        Base32 encoded secret string
    """
    return pyotp.random_base32()


def generate_totp_uri(secret: str, user_email: str, issuer: str = "BizCard CRM") -> str:
    """
    Generate TOTP provisioning URI for authenticator apps.
    
    Args:
        secret: Base32 encoded TOTP secret
        user_email: User's email address
        issuer: Application name
        
    Returns:
        otpauth:// URI string
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer)


def generate_qr_code(uri: str) -> str:
    """
    Generate QR code image from TOTP URI.
    
    Args:
        uri: TOTP provisioning URI
        
    Returns:
        Base64 encoded PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify TOTP code against secret.
    
    Args:
        secret: Base32 encoded TOTP secret
        code: 6-digit code from authenticator app
        window: Number of time windows to check (default: 1 = ±30 seconds)
        
    Returns:
        True if code is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate backup codes for 2FA recovery.
    
    Args:
        count: Number of backup codes to generate (default: 10)
        
    Returns:
        List of backup codes (8 characters each, alphanumeric)
    """
    codes = []
    for _ in range(count):
        # Generate 8-character code (easier to type than UUID)
        code = secrets.token_hex(4).upper()  # 8 hex chars
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """
    Hash a backup code for storage.
    
    Args:
        code: Plain text backup code
        
    Returns:
        SHA256 hash of the code
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(code: str, code_hash: str) -> bool:
    """
    Verify backup code against hash.
    
    Args:
        code: Plain text backup code
        code_hash: SHA256 hash of the code
        
    Returns:
        True if code matches hash, False otherwise
    """
    return hash_backup_code(code) == code_hash


def setup_2fa_for_user(db: Session, user: User) -> Tuple[str, str, List[str]]:
    """
    Set up 2FA for a user (but don't enable it yet).
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        Tuple of (secret, qr_code_data_uri, backup_codes)
    """
    # Check if 2FA already exists
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    
    if two_fa:
        # Re-setup: generate new secret and codes
        logger.info(f"Re-setting up 2FA for user {user.id}")
        secret = generate_totp_secret()
        two_fa.secret = secret
        two_fa.is_enabled = False  # Require re-verification
        
        # Delete old backup codes
        db.query(TwoFactorBackupCode).filter(TwoFactorBackupCode.user_id == user.id).delete()
    else:
        # New setup
        logger.info(f"Setting up 2FA for user {user.id}")
        secret = generate_totp_secret()
        two_fa = TwoFactorAuth(
            user_id=user.id,
            secret=secret,
            is_enabled=False
        )
        db.add(two_fa)
    
    # Generate QR code
    uri = generate_totp_uri(secret, user.email)
    qr_code = generate_qr_code(uri)
    
    # Generate backup codes
    backup_codes = generate_backup_codes(10)
    
    # Store hashed backup codes
    for code in backup_codes:
        backup_code_obj = TwoFactorBackupCode(
            user_id=user.id,
            code_hash=hash_backup_code(code),
            is_used=False
        )
        db.add(backup_code_obj)
    
    db.commit()
    db.refresh(two_fa)
    
    logger.info(f"2FA setup complete for user {user.id}, not yet enabled")
    
    return secret, qr_code, backup_codes


def enable_2fa_for_user(db: Session, user: User, verification_code: str) -> bool:
    """
    Enable 2FA for a user after verifying the initial code.
    
    Args:
        db: Database session
        user: User object
        verification_code: 6-digit TOTP code to verify
        
    Returns:
        True if enabled successfully, False otherwise
    """
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    
    if not two_fa:
        logger.error(f"2FA not set up for user {user.id}")
        return False
    
    # Verify the code
    if not verify_totp_code(two_fa.secret, verification_code):
        logger.warning(f"Invalid 2FA verification code for user {user.id}")
        return False
    
    # Enable 2FA
    two_fa.is_enabled = True
    two_fa.enabled_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"2FA enabled for user {user.id}")
    return True


def disable_2fa_for_user(db: Session, user: User, verification_code: str) -> bool:
    """
    Disable 2FA for a user after verifying code.
    
    Args:
        db: Database session
        user: User object
        verification_code: 6-digit TOTP code or backup code to verify
        
    Returns:
        True if disabled successfully, False otherwise
    """
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    
    if not two_fa or not two_fa.is_enabled:
        logger.error(f"2FA not enabled for user {user.id}")
        return False
    
    # Verify code (TOTP or backup)
    is_valid = False
    
    # Try TOTP first
    if verify_totp_code(two_fa.secret, verification_code):
        is_valid = True
    else:
        # Try backup codes
        backup_codes = db.query(TwoFactorBackupCode).filter(
            TwoFactorBackupCode.user_id == user.id,
            TwoFactorBackupCode.is_used == False
        ).all()
        
        for backup_code in backup_codes:
            if verify_backup_code(verification_code, backup_code.code_hash):
                # Mark backup code as used
                backup_code.is_used = True
                backup_code.used_at = datetime.utcnow()
                is_valid = True
                break
    
    if not is_valid:
        logger.warning(f"Invalid 2FA code for disabling user {user.id}")
        return False
    
    # Disable 2FA
    two_fa.is_enabled = False
    db.commit()
    
    logger.info(f"2FA disabled for user {user.id}")
    return True


def verify_2fa_for_login(db: Session, user: User, code: str) -> bool:
    """
    Verify 2FA code during login.
    
    Args:
        db: Database session
        user: User object
        code: 6-digit TOTP code or 8-character backup code
        
    Returns:
        True if code is valid, False otherwise
    """
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    
    if not two_fa or not two_fa.is_enabled:
        # 2FA not enabled, shouldn't be here
        logger.warning(f"2FA verification requested but not enabled for user {user.id}")
        return False
    
    # Try TOTP first (6 digits)
    if len(code) == 6 and code.isdigit():
        if verify_totp_code(two_fa.secret, code):
            # Update last used timestamp
            two_fa.last_used_at = datetime.utcnow()
            db.commit()
            logger.info(f"2FA TOTP verified for user {user.id}")
            return True
    
    # Try backup code (8 characters)
    if len(code) == 8:
        backup_codes = db.query(TwoFactorBackupCode).filter(
            TwoFactorBackupCode.user_id == user.id,
            TwoFactorBackupCode.is_used == False
        ).all()
        
        for backup_code in backup_codes:
            if verify_backup_code(code.upper(), backup_code.code_hash):
                # Mark backup code as used
                backup_code.is_used = True
                backup_code.used_at = datetime.utcnow()
                two_fa.last_used_at = datetime.utcnow()
                db.commit()
                logger.info(f"2FA backup code verified for user {user.id}")
                return True
    
    logger.warning(f"Invalid 2FA code for user {user.id}")
    return False


def is_2fa_enabled(db: Session, user: User) -> bool:
    """
    Check if 2FA is enabled for a user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        True if 2FA is enabled, False otherwise
    """
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    return two_fa is not None and two_fa.is_enabled


def get_unused_backup_codes_count(db: Session, user: User) -> int:
    """
    Get count of unused backup codes for a user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        Number of unused backup codes
    """
    count = db.query(TwoFactorBackupCode).filter(
        TwoFactorBackupCode.user_id == user.id,
        TwoFactorBackupCode.is_used == False
    ).count()
    return count


def regenerate_backup_codes(db: Session, user: User, verification_code: str) -> Optional[List[str]]:
    """
    Regenerate backup codes for a user (after verification).
    
    Args:
        db: Database session
        user: User object
        verification_code: 6-digit TOTP code to verify
        
    Returns:
        List of new backup codes or None if verification fails
    """
    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    
    if not two_fa or not two_fa.is_enabled:
        logger.error(f"2FA not enabled for user {user.id}")
        return None
    
    # Verify the code
    if not verify_totp_code(two_fa.secret, verification_code):
        logger.warning(f"Invalid 2FA code for regenerating backup codes for user {user.id}")
        return None
    
    # Delete old backup codes
    db.query(TwoFactorBackupCode).filter(TwoFactorBackupCode.user_id == user.id).delete()
    
    # Generate new backup codes
    backup_codes = generate_backup_codes(10)
    
    # Store hashed backup codes
    for code in backup_codes:
        backup_code_obj = TwoFactorBackupCode(
            user_id=user.id,
            code_hash=hash_backup_code(code),
            is_used=False
        )
        db.add(backup_code_obj)
    
    db.commit()
    
    logger.info(f"Backup codes regenerated for user {user.id}")
    
    return backup_codes

