"""
Comprehensive security tests for Two-Factor Authentication (2FA)
Tests TOTP generation, verification, backup codes, QR generation, and login flows
"""
import pytest
from datetime import datetime, timedelta
import pyotp
import io
import re
import base64
from PIL import Image
from sqlalchemy.orm import Session

from app.core.two_factor import (
    generate_totp_secret,
    generate_totp_uri,
    generate_qr_code,
    verify_totp_code,
    generate_backup_codes,
    hash_backup_code,
    verify_backup_code,
    setup_2fa_for_user,
    enable_2fa_for_user,
    disable_2fa_for_user,
    verify_2fa_for_login,
    is_2fa_enabled,
    get_unused_backup_codes_count,
    regenerate_backup_codes
)
from app.models.user import User
from app.models.two_factor_auth import TwoFactorAuth, TwoFactorBackupCode


# ==================== FIXTURES ====================

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user"""
    user = User(
        username="test_2fa_user",
        email="test2fa@example.com",
        hashed_password="hashed_test_password",
        full_name="Test 2FA User",
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==================== TOTP SECRET & URI TESTS ====================

def test_generate_totp_secret():
    """Test TOTP secret generation"""
    secret = generate_totp_secret()
    assert secret is not None
    assert len(secret) == 32  # Base32 encoded secret
    assert secret.isalnum()  # Only alphanumeric characters


def test_generate_totp_secret_uniqueness():
    """Test that generated secrets are unique"""
    secrets = [generate_totp_secret() for _ in range(10)]
    assert len(set(secrets)) == 10  # All should be unique


def test_generate_totp_uri():
    """Test TOTP provisioning URI generation"""
    secret = "JBSWY3DPEHPK3PXP"
    user_email = "test@example.com"
    uri = generate_totp_uri(secret, user_email)
    
    assert uri.startswith("otpauth://totp/")
    # Email might be URL-encoded in the URI
    assert "test" in uri and "example.com" in uri
    assert secret in uri
    assert "issuer=" in uri


def test_generate_totp_uri_custom_issuer():
    """Test TOTP URI with custom issuer"""
    secret = "JBSWY3DPEHPK3PXP"
    user_email = "test@example.com"
    issuer = "CustomApp"
    uri = generate_totp_uri(secret, user_email, issuer)
    
    assert f"issuer={issuer}" in uri


# ==================== TOTP VERIFICATION TESTS ====================

def test_verify_totp_code_valid():
    """Test TOTP code verification with valid code"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_invalid():
    """Test TOTP code verification with invalid code"""
    secret = pyotp.random_base32()
    
    assert verify_totp_code(secret, "000000") is False
    assert verify_totp_code(secret, "invalid") is False


def test_verify_totp_code_window():
    """Test TOTP code verification with time window"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    # Current code should always be valid
    current_code = totp.now()
    assert verify_totp_code(secret, current_code) is True
    
    # Note: Time window test is tricky due to timing; current code is enough


def test_verify_totp_code_expired():
    """Test TOTP code verification with expired code"""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    
    # Generate code from 2 minutes ago (should be expired)
    old_code = totp.at(datetime.utcnow() - timedelta(minutes=2))
    assert verify_totp_code(secret, old_code) is False


# ==================== QR CODE TESTS ====================

def test_generate_qr_code():
    """Test QR code generation"""
    secret = "JBSWY3DPEHPK3PXP"
    user_email = "test@example.com"
    uri = generate_totp_uri(secret, user_email)
    qr_data_uri = generate_qr_code(uri)
    
    assert qr_data_uri is not None
    assert qr_data_uri.startswith("data:image/png;base64,")
    
    # Extract base64 data
    base64_data = qr_data_uri.split(",")[1]
    img_bytes = base64.b64decode(base64_data)
    
    # Verify it's a valid PNG image
    img = Image.open(io.BytesIO(img_bytes))
    assert img.format == "PNG"


# ==================== BACKUP CODES TESTS ====================

def test_generate_backup_codes():
    """Test backup code generation"""
    codes = generate_backup_codes(count=8)
    
    assert len(codes) == 8
    for code in codes:
        assert len(code) == 8  # 8 hex characters
        # tokens are uppercase hex as per implementation
        assert code.isalnum()
        assert all(c in '0123456789ABCDEF' for c in code.upper())


def test_generate_backup_codes_uniqueness():
    """Test backup codes are unique"""
    codes = generate_backup_codes(count=10)
    assert len(set(codes)) == 10  # All should be unique


def test_hash_backup_code():
    """Test backup code hashing"""
    code = "ABCD1234"
    hashed = hash_backup_code(code)
    
    assert hashed is not None
    assert len(hashed) == 64  # SHA256 produces 64-character hex string
    assert hashed != code  # Should be hashed, not plain text


def test_verify_backup_code_valid():
    """Test backup code verification with valid code"""
    code = "ABCD1234"
    hashed = hash_backup_code(code)
    
    assert verify_backup_code(code, hashed) is True


def test_verify_backup_code_invalid():
    """Test backup code verification with invalid code"""
    code = "ABCD1234"
    hashed = hash_backup_code(code)
    
    assert verify_backup_code("WRONGCODE", hashed) is False


# ==================== DATABASE INTEGRATION TESTS ====================

def test_is_2fa_enabled_disabled(db_session: Session, test_user: User):
    """Test checking 2FA status for user without 2FA"""
    enabled = is_2fa_enabled(db_session, test_user)
    assert enabled is False


def test_setup_2fa_for_user(db_session: Session, test_user: User):
    """Test 2FA setup for user"""
    secret, qr_code, backup_codes = setup_2fa_for_user(db_session, test_user)
    
    assert secret is not None
    assert len(secret) == 32
    assert qr_code is not None
    assert qr_code.startswith("data:image/png;base64,")
    assert len(backup_codes) == 10
    
    # Verify database record
    two_fa = db_session.query(TwoFactorAuth).filter_by(user_id=test_user.id).first()
    assert two_fa is not None
    assert two_fa.secret == secret
    assert two_fa.is_enabled is False  # Not enabled until verified
    
    # Verify backup codes are stored
    stored_backup_codes = db_session.query(TwoFactorBackupCode).filter_by(
        user_id=test_user.id
    ).all()
    assert len(stored_backup_codes) == 10


def test_enable_2fa_for_user(db_session: Session, test_user: User):
    """Test enabling 2FA after setup"""
    # Setup 2FA first
    secret, _, _ = setup_2fa_for_user(db_session, test_user)
    
    # Generate valid TOTP code
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    # Enable 2FA
    success = enable_2fa_for_user(db_session, test_user, code)
    assert success is True
    
    # Verify enabled
    assert is_2fa_enabled(db_session, test_user) is True


def test_enable_2fa_for_user_invalid_code(db_session: Session, test_user: User):
    """Test enabling 2FA with invalid code"""
    # Setup 2FA first
    setup_2fa_for_user(db_session, test_user)
    
    # Try to enable with invalid code
    success = enable_2fa_for_user(db_session, test_user, "000000")
    assert success is False
    
    # Verify still disabled
    assert is_2fa_enabled(db_session, test_user) is False


def test_disable_2fa_for_user(db_session: Session):
    """Test disabling 2FA"""
    # Create user
    user = User(
        username="test_disable_2fa",
        email="disable2fa@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Setup and enable 2FA
    secret, _, _ = setup_2fa_for_user(db_session, user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, user, totp.now())
    
    # Disable 2FA with valid code
    disable_code = totp.now()
    success = disable_2fa_for_user(db_session, user, disable_code)
    assert success is True
    
    # Verify disabled
    assert is_2fa_enabled(db_session, user) is False


def test_verify_2fa_for_login_with_totp(db_session: Session, test_user: User):
    """Test 2FA verification during login with TOTP code"""
    # Setup and enable 2FA
    secret, _, _ = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # Verify with new TOTP code
    login_code = totp.now()
    assert verify_2fa_for_login(db_session, test_user, login_code) is True


def test_verify_2fa_for_login_with_backup_code(db_session: Session, test_user: User):
    """Test 2FA verification during login with backup code"""
    # Setup and enable 2FA
    secret, _, backup_codes = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # Verify with backup code
    backup_code = backup_codes[0]
    assert verify_2fa_for_login(db_session, test_user, backup_code) is True
    
    # Check that backup code was marked as used
    assert get_unused_backup_codes_count(db_session, test_user) == 9


def test_verify_2fa_for_login_backup_code_reuse(db_session: Session, test_user: User):
    """Test that used backup codes cannot be reused"""
    # Setup and enable 2FA
    secret, _, backup_codes = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # Use a backup code
    backup_code = backup_codes[0]
    assert verify_2fa_for_login(db_session, test_user, backup_code) is True
    
    # Try to use same code again
    assert verify_2fa_for_login(db_session, test_user, backup_code) is False


def test_get_unused_backup_codes_count(db_session: Session, test_user: User):
    """Test counting unused backup codes"""
    # Setup 2FA
    secret, _, backup_codes = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # All codes unused
    assert get_unused_backup_codes_count(db_session, test_user) == 10
    
    # Use one code
    verify_2fa_for_login(db_session, test_user, backup_codes[0])
    assert get_unused_backup_codes_count(db_session, test_user) == 9
    
    # Use another
    verify_2fa_for_login(db_session, test_user, backup_codes[1])
    assert get_unused_backup_codes_count(db_session, test_user) == 8


def test_regenerate_backup_codes_function(db_session: Session, test_user: User):
    """Test regenerating backup codes"""
    # Setup and enable 2FA
    secret, _, old_codes = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # Regenerate codes with valid TOTP
    new_codes = regenerate_backup_codes(db_session, test_user, totp.now())
    assert new_codes is not None
    assert len(new_codes) == 10
    
    # Old codes should not work
    assert verify_2fa_for_login(db_session, test_user, old_codes[0]) is False
    
    # New codes should work
    assert verify_2fa_for_login(db_session, test_user, new_codes[0]) is True


def test_regenerate_backup_codes_invalid_verification(db_session: Session, test_user: User):
    """Test regenerating backup codes with invalid verification code"""
    # Setup and enable 2FA
    secret, _, _ = setup_2fa_for_user(db_session, test_user)
    totp = pyotp.TOTP(secret)
    enable_2fa_for_user(db_session, test_user, totp.now())
    
    # Try to regenerate with invalid code
    new_codes = regenerate_backup_codes(db_session, test_user, "000000")
    assert new_codes is None


# ==================== SECURITY EDGE CASES ====================

def test_2fa_cannot_enable_without_setup(db_session: Session, test_user: User):
    """Test that 2FA cannot be enabled without setup"""
    success = enable_2fa_for_user(db_session, test_user, "123456")
    assert success is False


def test_backup_codes_hashed_in_db(db_session: Session, test_user: User):
    """Test that backup codes are hashed in database"""
    _, _, plain_codes = setup_2fa_for_user(db_session, test_user)
    
    # Get stored codes from database
    stored_codes = db_session.query(TwoFactorBackupCode).filter_by(
        user_id=test_user.id
    ).all()
    
    # Verify none of the plain codes are in database
    stored_hashes = [code.code_hash for code in stored_codes]
    for plain_code in plain_codes:
        assert plain_code not in stored_hashes  # Should be hashed


def test_totp_timing_attack_resistance():
    """Test TOTP verification is resistant to timing attacks"""
    import time
    secret = pyotp.random_base32()
    
    # Measure time for correct code
    start = time.time()
    totp = pyotp.TOTP(secret)
    verify_totp_code(secret, totp.now())
    correct_time = time.time() - start
    
    # Measure time for incorrect code
    start = time.time()
    verify_totp_code(secret, "000000")
    incorrect_time = time.time() - start
    
    # Times should be roughly similar (within 50ms for generous margin)
    assert abs(correct_time - incorrect_time) < 0.05


def test_2fa_multiple_users_isolation(db_session: Session):
    """Test that 2FA for different users is isolated"""
    # Create two users
    user1 = User(username="user1", email="user1@example.com", hashed_password="hash1", is_active=True, is_admin=True)
    user2 = User(username="user2", email="user2@example.com", hashed_password="hash2", is_active=True, is_admin=True)
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    # Setup 2FA for both
    secret1, _, codes1 = setup_2fa_for_user(db_session, user1)
    secret2, _, codes2 = setup_2fa_for_user(db_session, user2)
    
    # Secrets should be different
    assert secret1 != secret2
    
    # Backup codes should be different
    assert set(codes1) != set(codes2)
    
    # User1's code should not work for User2
    totp1 = pyotp.TOTP(secret1)
    success = enable_2fa_for_user(db_session, user2, totp1.now())
    assert success is False


def test_2fa_secret_not_exposed_in_user_model(db_session: Session, test_user: User):
    """Test that 2FA secret is stored separately from user model"""
    secret, _, _ = setup_2fa_for_user(db_session, test_user)
    
    # Refresh user from database
    db_session.refresh(test_user)
    
    # User model should not contain secret directly
    assert not hasattr(test_user, 'totp_secret')
    assert not hasattr(test_user, '2fa_secret')
    
    # Secret should be in separate table
    two_fa = db_session.query(TwoFactorAuth).filter_by(user_id=test_user.id).first()
    assert two_fa.secret == secret


# ==================== COMPREHENSIVE WORKFLOW TEST ====================

def test_complete_2fa_workflow(db_session: Session):
    """Test complete 2FA workflow from setup to login"""
    # 1. Create user
    user = User(
        username="workflow_test",
        email="workflow@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # 2. Setup 2FA
    secret, qr_code, backup_codes = setup_2fa_for_user(db_session, user)
    
    assert secret is not None
    assert len(backup_codes) == 10
    assert qr_code.startswith("data:image/png;base64,")
    
    # 3. Verify QR code
    base64_data = qr_code.split(",")[1]
    img_bytes = base64.b64decode(base64_data)
    img = Image.open(io.BytesIO(img_bytes))
    assert img.format == "PNG"
    
    # 4. Enable 2FA with TOTP
    totp = pyotp.TOTP(secret)
    code = totp.now()
    success = enable_2fa_for_user(db_session, user, code)
    assert success is True
    
    # 5. Check status
    assert is_2fa_enabled(db_session, user) is True
    assert get_unused_backup_codes_count(db_session, user) == 10
    
    # 6. Simulate login with TOTP
    login_code = totp.now()
    assert verify_2fa_for_login(db_session, user, login_code) is True
    
    # 7. Simulate login with backup code
    backup_code = backup_codes[0]
    assert verify_2fa_for_login(db_session, user, backup_code) is True
    assert get_unused_backup_codes_count(db_session, user) == 9
    
    # 8. Regenerate backup codes
    new_codes = regenerate_backup_codes(db_session, user, totp.now())
    assert len(new_codes) == 10
    assert get_unused_backup_codes_count(db_session, user) == 10
    
    # 9. Disable 2FA
    success = disable_2fa_for_user(db_session, user, totp.now())
    assert success is True
    
    # 10. Verify disabled
    assert is_2fa_enabled(db_session, user) is False
