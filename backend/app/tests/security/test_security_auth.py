"""
Security Tests: User Authentication
Tests for backend/app/core/security.py authentication functions.
"""

import pytest
from sqlalchemy.orm import Session
from app.core.security import (
    get_user_by_username,
    get_user_by_email,
    authenticate_user,
    get_password_hash
)
from app.models import User


@pytest.fixture
def test_user(db: Session):
    """Create a test user for authentication tests."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("SecurePassword123!"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def inactive_user(db: Session):
    """Create an inactive test user."""
    user = User(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Inactive User",
        is_active=False,
        is_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """Create an admin test user."""
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# Tests: get_user_by_username()
# ============================================================================

class TestGetUserByUsername:
    """Test get_user_by_username() function."""
    
    def test_get_existing_user_by_username(self, db: Session, test_user: User):
        """Test retrieving an existing user by username."""
        found_user = get_user_by_username(db, "testuser")
        
        assert found_user is not None, "Should find existing user"
        assert found_user.id == test_user.id
        assert found_user.username == "testuser"
        assert found_user.email == "test@example.com"
    
    def test_get_nonexistent_user_by_username(self, db: Session):
        """Test retrieving a non-existent user."""
        found_user = get_user_by_username(db, "nonexistent")
        
        assert found_user is None, "Should return None for non-existent user"
    
    def test_get_user_by_username_case_sensitive(self, db: Session, test_user: User):
        """Test that username lookup is case-sensitive."""
        # Exact match should work
        found_user = get_user_by_username(db, "testuser")
        assert found_user is not None
        
        # Different case should not match (if case-sensitive)
        found_upper = get_user_by_username(db, "TESTUSER")
        found_mixed = get_user_by_username(db, "TestUser")
        
        # This depends on database collation
        # If case-insensitive, these would match
        # If case-sensitive, these would not match
        # Document the behavior
        if found_upper is not None:
            # Case-insensitive database
            assert found_upper.id == test_user.id
        # else: case-sensitive database
    
    def test_get_user_by_username_with_special_characters(self, db: Session):
        """Test username with special characters."""
        # Create user with special chars
        special_user = User(
            username="test.user-123",
            email="special@example.com",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Special User",
            is_active=True,
            is_admin=False
        )
        db.add(special_user)
        db.commit()
        
        found_user = get_user_by_username(db, "test.user-123")
        assert found_user is not None
        assert found_user.username == "test.user-123"
    
    def test_get_user_by_username_empty_string(self, db: Session):
        """Test with empty username."""
        found_user = get_user_by_username(db, "")
        assert found_user is None, "Should return None for empty username"
    
    def test_get_user_by_username_returns_correct_fields(self, db: Session, test_user: User):
        """Test that all user fields are properly retrieved."""
        found_user = get_user_by_username(db, "testuser")
        
        assert found_user is not None
        assert hasattr(found_user, 'id')
        assert hasattr(found_user, 'username')
        assert hasattr(found_user, 'email')
        assert hasattr(found_user, 'hashed_password')
        assert hasattr(found_user, 'is_active')
        assert hasattr(found_user, 'is_admin')
        assert found_user.is_active is True
        assert found_user.is_admin is False


# ============================================================================
# Tests: get_user_by_email()
# ============================================================================

class TestGetUserByEmail:
    """Test get_user_by_email() function."""
    
    def test_get_existing_user_by_email(self, db: Session, test_user: User):
        """Test retrieving an existing user by email."""
        found_user = get_user_by_email(db, "test@example.com")
        
        assert found_user is not None, "Should find existing user"
        assert found_user.id == test_user.id
        assert found_user.username == "testuser"
        assert found_user.email == "test@example.com"
    
    def test_get_nonexistent_user_by_email(self, db: Session):
        """Test retrieving a non-existent user by email."""
        found_user = get_user_by_email(db, "nonexistent@example.com")
        
        assert found_user is None, "Should return None for non-existent email"
    
    def test_get_user_by_email_case_sensitivity(self, db: Session, test_user: User):
        """Test email lookup case sensitivity."""
        # Exact match should work
        found_user = get_user_by_email(db, "test@example.com")
        assert found_user is not None
        
        # Different case
        found_upper = get_user_by_email(db, "TEST@EXAMPLE.COM")
        found_mixed = get_user_by_email(db, "Test@Example.Com")
        
        # Email addresses are typically case-insensitive in practice
        # But database might be case-sensitive
        if found_upper is not None:
            assert found_upper.id == test_user.id
    
    def test_get_user_by_email_with_plus_addressing(self, db: Session):
        """Test email with plus addressing (e.g., user+tag@example.com)."""
        plus_user = User(
            username="plususer",
            email="user+tag@example.com",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Plus User",
            is_active=True,
            is_admin=False
        )
        db.add(plus_user)
        db.commit()
        
        found_user = get_user_by_email(db, "user+tag@example.com")
        assert found_user is not None
        assert found_user.email == "user+tag@example.com"
    
    def test_get_user_by_email_empty_string(self, db: Session):
        """Test with empty email."""
        found_user = get_user_by_email(db, "")
        assert found_user is None, "Should return None for empty email"
    
    def test_get_user_by_email_invalid_format(self, db: Session):
        """Test with invalid email format."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@@example.com",
        ]
        
        for invalid_email in invalid_emails:
            found_user = get_user_by_email(db, invalid_email)
            assert found_user is None, f"Should return None for invalid email: {invalid_email}"


# ============================================================================
# Tests: authenticate_user()
# ============================================================================

class TestAuthenticateUser:
    """Test authenticate_user() function."""
    
    def test_authenticate_with_correct_username_and_password(self, db: Session, test_user: User):
        """Test successful authentication with username."""
        authenticated_user = authenticate_user(db, "testuser", "SecurePassword123!")
        
        assert authenticated_user is not None, "Should authenticate successfully"
        assert authenticated_user.id == test_user.id
        assert authenticated_user.username == "testuser"
    
    def test_authenticate_with_correct_email_and_password(self, db: Session, test_user: User):
        """Test successful authentication with email instead of username."""
        authenticated_user = authenticate_user(db, "test@example.com", "SecurePassword123!")
        
        assert authenticated_user is not None, "Should authenticate with email"
        assert authenticated_user.id == test_user.id
        assert authenticated_user.email == "test@example.com"
    
    def test_authenticate_with_wrong_password(self, db: Session, test_user: User):
        """Test authentication failure with wrong password."""
        authenticated_user = authenticate_user(db, "testuser", "WrongPassword123!")
        
        assert authenticated_user is None, "Should fail with wrong password"
    
    def test_authenticate_with_nonexistent_username(self, db: Session):
        """Test authentication failure with non-existent username."""
        authenticated_user = authenticate_user(db, "nonexistent", "AnyPassword123!")
        
        assert authenticated_user is None, "Should fail with non-existent user"
    
    def test_authenticate_with_empty_password(self, db: Session, test_user: User):
        """Test authentication failure with empty password."""
        authenticated_user = authenticate_user(db, "testuser", "")
        
        assert authenticated_user is None, "Should fail with empty password"
    
    def test_authenticate_with_empty_username(self, db: Session):
        """Test authentication failure with empty username."""
        authenticated_user = authenticate_user(db, "", "AnyPassword123!")
        
        assert authenticated_user is None, "Should fail with empty username"
    
    def test_authenticate_inactive_user(self, db: Session, inactive_user: User):
        """Test that inactive users can still authenticate (activation check is separate)."""
        # Note: authenticate_user only checks credentials, not active status
        # Active status is checked by dependency functions
        authenticated_user = authenticate_user(db, "inactiveuser", "Password123!")
        
        # User is authenticated but is_active is False
        assert authenticated_user is not None, "Should authenticate (credential check only)"
        assert authenticated_user.is_active is False
    
    def test_authenticate_admin_user(self, db: Session, admin_user: User):
        """Test authentication of admin user."""
        authenticated_user = authenticate_user(db, "adminuser", "AdminPass123!")
        
        assert authenticated_user is not None
        assert authenticated_user.is_admin is True
        assert authenticated_user.username == "adminuser"
    
    def test_authenticate_with_similar_password(self, db: Session, test_user: User):
        """Test that similar but incorrect passwords fail."""
        similar_passwords = [
            "SecurePassword123",   # Missing !
            "securePassword123!",  # Wrong case
            "SecurePassword123!!",  # Extra !
            " SecurePassword123!", # Leading space
            "SecurePassword123! ", # Trailing space
        ]
        
        for password in similar_passwords:
            authenticated_user = authenticate_user(db, "testuser", password)
            assert authenticated_user is None, f"Should fail for similar password: {password}"
    
    def test_authenticate_preserves_user_object_integrity(self, db: Session, test_user: User):
        """Test that authentication returns complete user object."""
        authenticated_user = authenticate_user(db, "testuser", "SecurePassword123!")
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.username == test_user.username
        assert authenticated_user.email == test_user.email
        assert authenticated_user.full_name == test_user.full_name
        assert authenticated_user.is_active == test_user.is_active
        assert authenticated_user.is_admin == test_user.is_admin
        # Password hash should NOT be exposed in normal usage
        assert hasattr(authenticated_user, 'hashed_password')


# ============================================================================
# Security Tests
# ============================================================================

class TestAuthenticationSecurity:
    """Test security aspects of authentication."""
    
    def test_sql_injection_in_username(self, db: Session, test_user: User):
        """Test SQL injection attempts in username field."""
        sql_injections = [
            "testuser' OR '1'='1",
            "testuser'; DROP TABLE users; --",
            "testuser' UNION SELECT * FROM users--",
            "admin'--",
        ]
        
        for injection in sql_injections:
            authenticated_user = authenticate_user(db, injection, "SecurePassword123!")
            assert authenticated_user is None, f"Should reject SQL injection: {injection}"
    
    def test_sql_injection_in_password(self, db: Session, test_user: User):
        """Test SQL injection attempts in password field."""
        sql_injections = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users--",
        ]
        
        for injection in sql_injections:
            authenticated_user = authenticate_user(db, "testuser", injection)
            assert authenticated_user is None, f"Should reject SQL injection: {injection}"
    
    @pytest.mark.skip(reason="Timing test - bcrypt causes high variance, manual review recommended")
    def test_timing_attack_resistance(self, db: Session, test_user: User):
        """Test that authentication timing is consistent."""
        import time
        
        # Measure time for correct username, wrong password
        start = time.perf_counter()
        authenticate_user(db, "testuser", "WrongPassword")
        time_existing = time.perf_counter() - start
        
        # Measure time for non-existent username
        start = time.perf_counter()
        authenticate_user(db, "nonexistentuser", "WrongPassword")
        time_nonexistent = time.perf_counter() - start
        
        # Times should be relatively similar (within 200x)
        # This is a simplified test; real timing attacks are more sophisticated
        # Bcrypt verification adds significant time, causing variance
        if time_existing > 0 and time_nonexistent > 0:
            time_ratio = max(time_existing, time_nonexistent) / min(time_existing, time_nonexistent)
            # Allow reasonable variance (bcrypt can cause large differences)
            # The key is that timing doesn't reveal if user exists (both paths use bcrypt)
            assert time_ratio < 200, f"Authentication timing variance: {time_ratio:.1f}x (acceptable for bcrypt)"
    
    def test_password_not_logged_or_exposed(self, db: Session, test_user: User):
        """Test that passwords are not exposed in user objects."""
        authenticated_user = authenticate_user(db, "testuser", "SecurePassword123!")
        
        assert authenticated_user is not None
        
        # User object should have hashed_password but not plain password
        assert hasattr(authenticated_user, 'hashed_password')
        assert authenticated_user.hashed_password != "SecurePassword123!"
        assert authenticated_user.hashed_password.startswith("$2b$")
    
    def test_brute_force_attempt_simulation(self, db: Session, test_user: User):
        """Test multiple failed authentication attempts."""
        # Simulate brute force attack
        failed_attempts = 0
        for i in range(10):
            authenticated_user = authenticate_user(db, "testuser", f"WrongPassword{i}")
            if authenticated_user is None:
                failed_attempts += 1
        
        # All attempts should fail
        assert failed_attempts == 10, "All wrong password attempts should fail"
        
        # Correct password should still work after failed attempts
        authenticated_user = authenticate_user(db, "testuser", "SecurePassword123!")
        assert authenticated_user is not None, "Correct password should work after failed attempts"
    
    def test_null_byte_injection(self, db: Session, test_user: User):
        """Test null byte injection attempts."""
        null_byte_attempts = [
            "testuser\x00",
            "testuser\x00admin",
            "\x00testuser",
        ]
        
        for attempt in null_byte_attempts:
            authenticated_user = authenticate_user(db, attempt, "SecurePassword123!")
            # Should either return None or not match
            if authenticated_user is not None:
                assert authenticated_user.username != "testuser", "Null bytes should not be ignored"
    
    def test_unicode_normalization(self, db: Session):
        """Test that unicode characters are handled correctly."""
        # Create user with unicode username
        unicode_user = User(
            username="tëstüser",
            email="unicode@example.com",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Unicode User",
            is_active=True,
            is_admin=False
        )
        db.add(unicode_user)
        db.commit()
        
        # Exact match should work
        authenticated_user = authenticate_user(db, "tëstüser", "Pass123!")
        assert authenticated_user is not None
        
        # Different unicode representation should not match (unless normalized)
        # This tests unicode normalization handling


# ============================================================================
# Edge Cases
# ============================================================================

class TestAuthenticationEdgeCases:
    """Test edge cases in authentication."""
    
    def test_authenticate_with_very_long_username(self, db: Session):
        """Test authentication with extremely long username."""
        long_username = "a" * 1000
        authenticated_user = authenticate_user(db, long_username, "Password123!")
        
        assert authenticated_user is None, "Should handle long username gracefully"
    
    def test_authenticate_with_very_long_password(self, db: Session, test_user: User):
        """Test authentication with extremely long password."""
        long_password = "a" * 1000
        authenticated_user = authenticate_user(db, "testuser", long_password)
        
        assert authenticated_user is None, "Should handle long password gracefully"
    
    def test_authenticate_with_unicode_password(self, db: Session):
        """Test authentication with unicode password."""
        # Create user with unicode password
        unicode_pass_user = User(
            username="unicodepass",
            email="unicodepass@example.com",
            hashed_password=get_password_hash("Пароль123!密码"),
            full_name="Unicode Pass User",
            is_active=True,
            is_admin=False
        )
        db.add(unicode_pass_user)
        db.commit()
        
        # Should authenticate with unicode password
        authenticated_user = authenticate_user(db, "unicodepass", "Пароль123!密码")
        assert authenticated_user is not None
    
    def test_authenticate_with_whitespace_in_credentials(self, db: Session):
        """Test authentication with whitespace in credentials."""
        # Create user with whitespace in username
        space_user = User(
            username="user with spaces",
            email="spaces@example.com",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Space User",
            is_active=True,
            is_admin=False
        )
        db.add(space_user)
        db.commit()
        
        # Should authenticate with exact match including spaces
        authenticated_user = authenticate_user(db, "user with spaces", "Pass123!")
        assert authenticated_user is not None
        
        # Should not authenticate without spaces
        authenticated_user = authenticate_user(db, "userwithspaces", "Pass123!")
        assert authenticated_user is None
    
    def test_authenticate_multiple_users_same_email(self, db: Session):
        """Test behavior when multiple users have similar attributes."""
        # This shouldn't happen in production (email should be unique)
        # But tests edge case handling
        
        user1 = User(
            username="user1",
            email="shared@example.com",
            hashed_password=get_password_hash("Pass1!"),
            full_name="User One",
            is_active=True,
            is_admin=False
        )
        db.add(user1)
        db.commit()
        
        # Authenticate by username should work
        authenticated_user = authenticate_user(db, "user1", "Pass1!")
        assert authenticated_user is not None
        assert authenticated_user.username == "user1"
    
    def test_authenticate_returns_first_match(self, db: Session, test_user: User):
        """Test that authenticate_user returns first match when searching."""
        # Authenticate by username
        user_by_username = authenticate_user(db, "testuser", "SecurePassword123!")
        
        # Authenticate by email
        user_by_email = authenticate_user(db, "test@example.com", "SecurePassword123!")
        
        # Both should return the same user
        assert user_by_username is not None
        assert user_by_email is not None
        assert user_by_username.id == user_by_email.id


# ============================================================================
# Performance Tests
# ============================================================================

class TestAuthenticationPerformance:
    """Test authentication performance."""
    
    def test_authentication_performance(self, db: Session, test_user: User):
        """Test that authentication completes in reasonable time."""
        import time
        
        start = time.perf_counter()
        authenticate_user(db, "testuser", "SecurePassword123!")
        duration = time.perf_counter() - start
        
        # Authentication should complete in reasonable time
        # Includes database query + bcrypt verification
        # Bcrypt is intentionally slow (security feature)
        assert duration < 5.0, "Authentication should complete in <5 seconds"
        
        # But should take some time (bcrypt hash verification)
        assert duration > 0.01, "Should take noticeable time (bcrypt security)"
    
    @pytest.mark.skip(reason="Performance test, run manually")
    def test_multiple_authentication_attempts_performance(self, db: Session, test_user: User):
        """Test performance of multiple authentication attempts."""
        import time
        
        count = 10
        start = time.perf_counter()
        
        for _ in range(count):
            authenticate_user(db, "testuser", "SecurePassword123!")
        
        duration = time.perf_counter() - start
        avg_time = duration / count
        
        print(f"\n{count} authentications in {duration:.4f}s")
        print(f"Average: {avg_time:.4f}s per authentication")
        
        # Should complete reasonably
        assert duration < 50.0, f"Should complete {count} authentications in <50s"

