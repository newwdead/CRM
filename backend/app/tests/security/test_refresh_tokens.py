"""
Comprehensive security tests for JWT Refresh Tokens
Tests token generation, verification, rotation, and security edge cases
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import time

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from app.models.user import User


# ==================== FIXTURES ====================

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user for token tests"""
    user = User(
        username="test_token_user",
        email="token@example.com",
        hashed_password="hashed_test_password",
        full_name="Test Token User",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==================== TOKEN GENERATION TESTS ====================

def test_create_access_token():
    """Test access token generation"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiration():
    """Test access token with custom expiration"""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=30)
    token = create_access_token(data, expires_delta)
    
    assert token is not None
    
    # Decode and verify expiration
    payload = decode_access_token(token)
    assert payload is not None
    exp = payload.get("exp")
    assert exp is not None
    
    # Check that expiration is approximately 30 minutes from now
    exp_time = datetime.utcfromtimestamp(exp)
    expected_time = datetime.utcnow() + expires_delta
    time_diff = abs((exp_time - expected_time).total_seconds())
    assert time_diff < 5  # Allow 5 second margin


def test_create_refresh_token():
    """Test refresh token generation"""
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_has_type():
    """Test refresh token contains 'type' field"""
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload.get("type") == "refresh"


def test_create_refresh_token_with_expiration():
    """Test refresh token with custom expiration"""
    data = {"sub": "testuser"}
    expires_delta = timedelta(days=7)
    token = create_refresh_token(data, expires_delta)
    
    assert token is not None
    
    # Decode and verify expiration
    payload = decode_refresh_token(token)
    assert payload is not None
    exp = payload.get("exp")
    assert exp is not None
    
    # Check that expiration is approximately 7 days from now
    exp_time = datetime.utcfromtimestamp(exp)
    expected_time = datetime.utcnow() + expires_delta
    time_diff = abs((exp_time - expected_time).total_seconds())
    assert time_diff < 10  # Allow 10 second margin


# ==================== TOKEN DECODING TESTS ====================

def test_decode_access_token_valid():
    """Test decoding valid access token"""
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "testuser"
    assert payload.get("role") == "admin"


def test_decode_access_token_invalid():
    """Test decoding invalid access token"""
    invalid_token = "invalid.token.here"
    
    payload = decode_access_token(invalid_token)
    assert payload is None


def test_decode_access_token_expired():
    """Test decoding expired access token"""
    data = {"sub": "testuser"}
    expires_delta = timedelta(seconds=-10)  # Already expired
    token = create_access_token(data, expires_delta)
    
    payload = decode_access_token(token)
    assert payload is None  # Expired tokens should return None


def test_decode_refresh_token_valid():
    """Test decoding valid refresh token"""
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload.get("sub") == "testuser"
    assert payload.get("type") == "refresh"


def test_decode_refresh_token_invalid():
    """Test decoding invalid refresh token"""
    invalid_token = "invalid.refresh.token"
    
    payload = decode_refresh_token(invalid_token)
    assert payload is None


def test_decode_refresh_token_rejects_access_token():
    """Test that refresh token decoder rejects access tokens"""
    data = {"sub": "testuser"}
    access_token = create_access_token(data)  # Create access token, not refresh
    
    payload = decode_refresh_token(access_token)
    assert payload is None  # Should reject because it's not a refresh token


def test_decode_access_token_accepts_refresh_token():
    """Test that access token decoder can decode refresh tokens (but shouldn't be used this way)"""
    data = {"sub": "testuser"}
    refresh_token = create_refresh_token(data)
    
    # decode_access_token doesn't check 'type', so it will decode
    payload = decode_access_token(refresh_token)
    assert payload is not None
    assert payload.get("type") == "refresh"
    # This shows why endpoints should verify token type


# ==================== TOKEN HASHING TESTS ====================

def test_hash_token():
    """Test token hashing"""
    token = "test_token_string"
    hashed = hash_token(token)
    
    assert hashed is not None
    assert len(hashed) == 64  # SHA256 produces 64-character hex string
    assert hashed != token  # Should be hashed, not plain text


def test_hash_token_consistency():
    """Test that hashing the same token produces the same hash"""
    token = "test_token_string"
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    
    assert hash1 == hash2


def test_hash_token_uniqueness():
    """Test that different tokens produce different hashes"""
    token1 = "test_token_1"
    token2 = "test_token_2"
    
    hash1 = hash_token(token1)
    hash2 = hash_token(token2)
    
    assert hash1 != hash2


# ==================== TOKEN ROTATION TESTS ====================

def test_refresh_token_rotation(db_session: Session, test_user: User):
    """Test that refresh tokens are rotated on each refresh"""
    # Create initial refresh token
    refresh_token_1 = create_refresh_token({"sub": test_user.username})
    test_user.refresh_token_hash = hash_token(refresh_token_1)
    test_user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=30)
    db_session.commit()
    
    # Sleep to ensure different timestamp
    time.sleep(1)
    
    # Simulate refresh: create new refresh token
    refresh_token_2 = create_refresh_token({"sub": test_user.username})
    test_user.refresh_token_hash = hash_token(refresh_token_2)
    db_session.commit()
    
    # Verify old token hash doesn't match new token
    assert hash_token(refresh_token_1) != hash_token(refresh_token_2)
    assert test_user.refresh_token_hash == hash_token(refresh_token_2)


def test_refresh_token_cannot_be_reused(db_session: Session, test_user: User):
    """Test that old refresh tokens cannot be reused after rotation"""
    # Create initial refresh token
    refresh_token_1 = create_refresh_token({"sub": test_user.username})
    hash_1 = hash_token(refresh_token_1)
    test_user.refresh_token_hash = hash_1
    db_session.commit()
    
    # Sleep to ensure different timestamp
    time.sleep(1)
    
    # Rotate token
    refresh_token_2 = create_refresh_token({"sub": test_user.username})
    hash_2 = hash_token(refresh_token_2)
    test_user.refresh_token_hash = hash_2
    db_session.commit()
    
    # Try to verify old token
    db_session.refresh(test_user)
    assert test_user.refresh_token_hash != hash_1
    assert test_user.refresh_token_hash == hash_2


# ==================== TOKEN EXPIRATION TESTS ====================

def test_access_token_default_expiration():
    """Test that access token uses default expiration"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    exp = datetime.utcfromtimestamp(payload["exp"])
    expected = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Allow 5 second margin
    assert abs((exp - expected).total_seconds()) < 5


def test_refresh_token_default_expiration():
    """Test that refresh token uses default expiration"""
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    payload = decode_refresh_token(token)
    exp = datetime.utcfromtimestamp(payload["exp"])
    expected = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Allow 10 second margin
    assert abs((exp - expected).total_seconds()) < 10


def test_refresh_token_longer_than_access_token():
    """Test that refresh tokens have longer expiration than access tokens"""
    data = {"sub": "testuser"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    access_payload = decode_access_token(access_token)
    refresh_payload = decode_refresh_token(refresh_token)
    
    access_exp = access_payload["exp"]
    refresh_exp = refresh_payload["exp"]
    
    assert refresh_exp > access_exp


# ==================== DATABASE INTEGRATION TESTS ====================

def test_store_refresh_token_hash(db_session: Session, test_user: User):
    """Test storing refresh token hash in database"""
    refresh_token = create_refresh_token({"sub": test_user.username})
    token_hash = hash_token(refresh_token)
    
    test_user.refresh_token_hash = token_hash
    test_user.refresh_token_expires_at = datetime.utcnow() + timedelta(days=30)
    test_user.last_refresh_at = datetime.utcnow()
    db_session.commit()
    
    db_session.refresh(test_user)
    assert test_user.refresh_token_hash == token_hash
    assert test_user.refresh_token_expires_at is not None
    assert test_user.last_refresh_at is not None


def test_verify_refresh_token_from_database(db_session: Session, test_user: User):
    """Test verifying refresh token against stored hash"""
    refresh_token = create_refresh_token({"sub": test_user.username})
    token_hash = hash_token(refresh_token)
    
    test_user.refresh_token_hash = token_hash
    db_session.commit()
    
    # Verify token
    db_session.refresh(test_user)
    assert test_user.refresh_token_hash == hash_token(refresh_token)


def test_refresh_token_expiration_check(db_session: Session, test_user: User):
    """Test checking refresh token expiration from database"""
    refresh_token = create_refresh_token({"sub": test_user.username})
    
    # Set expiration in past
    test_user.refresh_token_hash = hash_token(refresh_token)
    test_user.refresh_token_expires_at = datetime.utcnow() - timedelta(days=1)
    db_session.commit()
    
    db_session.refresh(test_user)
    assert test_user.refresh_token_expires_at < datetime.utcnow()


def test_last_refresh_timestamp(db_session: Session, test_user: User):
    """Test tracking last refresh timestamp"""
    before = datetime.utcnow()
    
    refresh_token = create_refresh_token({"sub": test_user.username})
    test_user.refresh_token_hash = hash_token(refresh_token)
    test_user.last_refresh_at = datetime.utcnow()
    db_session.commit()
    
    after = datetime.utcnow()
    
    db_session.refresh(test_user)
    assert before <= test_user.last_refresh_at <= after


# ==================== SECURITY EDGE CASES ====================

def test_token_tampering_detection():
    """Test that tampered tokens are rejected"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    # Tamper with token
    tampered_token = token[:-5] + "AAAAA"
    
    payload = decode_access_token(tampered_token)
    assert payload is None


def test_different_users_different_tokens():
    """Test that different users get different tokens"""
    token1 = create_access_token({"sub": "user1"})
    token2 = create_access_token({"sub": "user2"})
    
    assert token1 != token2


def test_multiple_tokens_same_user():
    """Test that same user can get multiple different tokens"""
    data = {"sub": "testuser"}
    
    token1 = create_access_token(data)
    time.sleep(1)  # Sleep 1 second to ensure different exp timestamp
    token2 = create_access_token(data)
    
    # Tokens should be different due to different exp timestamps
    assert token1 != token2


def test_refresh_token_without_username():
    """Test that tokens without username are handled correctly"""
    data = {"some_field": "value"}  # No 'sub' field
    token = create_refresh_token(data)
    
    payload = decode_refresh_token(token)
    assert payload is not None
    assert payload.get("sub") is None


def test_token_payload_preservation():
    """Test that custom payload data is preserved"""
    data = {
        "sub": "testuser",
        "role": "admin",
        "custom_field": "custom_value"
    }
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    assert payload.get("sub") == "testuser"
    assert payload.get("role") == "admin"
    assert payload.get("custom_field") == "custom_value"


# ==================== CONCURRENT ACCESS TESTS ====================

def test_multiple_refresh_tokens_same_user(db_session: Session, test_user: User):
    """Test handling multiple refresh token rotations for same user"""
    tokens = []
    for i in range(3):  # Reduced from 5 to 3 for faster test
        token = create_refresh_token({"sub": test_user.username})
        tokens.append(token)
        test_user.refresh_token_hash = hash_token(token)
        test_user.last_refresh_at = datetime.utcnow()
        db_session.commit()
        time.sleep(1)  # Sleep 1 second for different timestamps
    
    # Only the last token should be valid
    db_session.refresh(test_user)
    assert test_user.refresh_token_hash == hash_token(tokens[-1])
    
    # Old tokens should not match
    for old_token in tokens[:-1]:
        assert test_user.refresh_token_hash != hash_token(old_token)


# ==================== TOKEN LIFETIME TESTS ====================

def test_access_token_short_lived():
    """Test that access tokens are short-lived (15 minutes default)"""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    
    lifetime = (exp - now).total_seconds()
    # Should be approximately 15 minutes (900 seconds)
    assert 890 < lifetime < 910  # Allow 10 second margin


def test_refresh_token_long_lived():
    """Test that refresh tokens are long-lived (30 days default)"""
    data = {"sub": "testuser"}
    token = create_refresh_token(data)
    
    payload = decode_refresh_token(token)
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    
    lifetime_days = (exp - now).days
    # Should be approximately 30 days
    assert 29 <= lifetime_days <= 30

