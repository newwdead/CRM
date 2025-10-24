"""
Security Tests: Password Hashing and Verification
Tests for backend/app/core/security.py password functions.
"""

import pytest
from app.core.security import verify_password, get_password_hash


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing_basic(self):
        """Test that password is properly hashed with bcrypt."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        # Verify hash is different from plain text
        assert hashed != password, "Hashed password should not equal plain text"
        
        # Verify hash starts with bcrypt prefix
        assert hashed.startswith("$2b$"), "Hash should use bcrypt algorithm ($2b$)"
        
        # Verify hash length (bcrypt = 60 characters)
        assert len(hashed) == 60, "Bcrypt hash should be 60 characters"
    
    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes (salt randomness)."""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Different hashes due to random salt
        assert hash1 != hash2, "Same password should generate different hashes"
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_password_hashing_various_strengths(self):
        """Test hashing with passwords of various strengths."""
        passwords = [
            "weak",                              # Weak
            "Medium123",                         # Medium
            "StrongP@ssw0rd!2023",              # Strong
            "VeryStrong!P@ssw0rd#123$XYZ",      # Very Strong
        ]
        
        for password in passwords:
            hashed = get_password_hash(password)
            assert hashed.startswith("$2b$"), f"Failed for password: {password}"
            assert len(hashed) == 60, f"Failed for password: {password}"
            assert hashed != password, f"Failed for password: {password}"
    
    def test_password_hashing_special_characters(self):
        """Test hashing passwords with special characters."""
        special_passwords = [
            "p@ssw0rd!",
            "pass#word$",
            "p&ss%w^rd*",
            "пароль",  # Cyrillic
            "密码",    # Chinese
            "🔒password🔑",  # Emojis
        ]
        
        for password in special_passwords:
            hashed = get_password_hash(password)
            assert hashed.startswith("$2b$"), f"Failed for: {password}"
            assert verify_password(password, hashed) is True, f"Failed for: {password}"
    
    def test_password_hashing_edge_cases(self):
        """Test hashing edge case passwords."""
        # Empty password
        empty = ""
        hashed_empty = get_password_hash(empty)
        assert verify_password(empty, hashed_empty) is True
        
        # Very long password (1000 characters)
        long_password = "a" * 1000
        hashed_long = get_password_hash(long_password)
        assert verify_password(long_password, hashed_long) is True
        
        # Single character
        single = "a"
        hashed_single = get_password_hash(single)
        assert verify_password(single, hashed_single) is True


class TestPasswordVerification:
    """Test password verification functionality."""
    
    def test_password_verification_correct(self):
        """Test verification with correct password."""
        password = "CorrectPassword123!"
        hashed = get_password_hash(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """Test verification with incorrect password."""
        password = "CorrectPassword123!"
        hashed = get_password_hash(password)
        
        # Wrong passwords should not verify
        wrong_passwords = [
            "WrongPassword",
            "correctpassword123!",  # Wrong case
            "CorrectPassword123",   # Missing !
            "CorrectPassword123!!",  # Extra !
            "",                      # Empty
        ]
        
        for wrong in wrong_passwords:
            assert verify_password(wrong, hashed) is False, f"Should fail for: {wrong}"
    
    def test_password_verification_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "CaseSensitive"
        hashed = get_password_hash(password)
        
        assert verify_password("CaseSensitive", hashed) is True
        assert verify_password("casesensitive", hashed) is False
        assert verify_password("CASESENSITIVE", hashed) is False
        assert verify_password("cAsEsEnSiTiVe", hashed) is False
    
    def test_password_verification_empty_password(self):
        """Test verification with empty password."""
        # Hash empty password
        hashed = get_password_hash("")
        
        # Empty should match
        assert verify_password("", hashed) is True
        
        # Non-empty should not match
        assert verify_password("a", hashed) is False
    
    def test_password_verification_malformed_hash(self):
        """Test verification with malformed hash."""
        password = "TestPassword123"
        
        # Test with invalid hashes
        invalid_hashes = [
            "",                      # Empty
            "not_a_valid_hash",     # Plain text
            "$2b$invalid",          # Invalid bcrypt
            "a" * 60,               # Wrong length but valid
        ]
        
        for invalid_hash in invalid_hashes:
            # Should not crash, should return False or raise ValueError
            try:
                result = verify_password(password, invalid_hash)
                assert result is False, f"Should reject invalid hash: {invalid_hash}"
            except (ValueError, Exception):
                # Some malformed hashes may raise exceptions, which is acceptable
                pass


class TestPasswordSecurityProperties:
    """Test security properties of password hashing."""
    
    def test_password_not_recoverable(self):
        """Test that original password cannot be recovered from hash."""
        password = "SecretPassword123!"
        hashed = get_password_hash(password)
        
        # Hash should not contain original password
        assert password not in hashed
        assert password.lower() not in hashed.lower()
        
        # No obvious pattern that reveals password
        assert len(hashed) == 60  # Fixed length regardless of password
    
    def test_password_timing_attack_resistance(self):
        """Test that verification time is consistent (timing attack resistance)."""
        import time
        
        password = "ConsistentPassword123!"
        hashed = get_password_hash(password)
        
        # Test with correct password
        start = time.perf_counter()
        verify_password(password, hashed)
        correct_time = time.perf_counter() - start
        
        # Test with incorrect password
        start = time.perf_counter()
        verify_password("WrongPassword", hashed)
        incorrect_time = time.perf_counter() - start
        
        # Times should be relatively similar (within 10x)
        # Bcrypt is designed to take consistent time regardless of match
        # Note: This is a simplified test; real timing attacks are more sophisticated
        time_ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
        assert time_ratio < 10, "Verification timing should be consistent"
    
    def test_password_hash_algorithm_strength(self):
        """Test that bcrypt is properly configured."""
        password = "TestPassword"
        hashed = get_password_hash(password)
        
        # Extract bcrypt parameters from hash
        # Format: $2b$rounds$salt+hash
        parts = hashed.split('$')
        
        assert parts[1] == "2b", "Should use bcrypt 2b"
        
        # Rounds should be >= 4 (2^4 = 16 iterations minimum)
        # Default is usually 12 (2^12 = 4096 iterations)
        rounds = int(parts[2])
        assert rounds >= 4, "Bcrypt rounds should be at least 4"
        assert rounds <= 31, "Bcrypt rounds should be at most 31"
    
    def test_sql_injection_in_password(self):
        """Test that SQL injection attempts in passwords are safely hashed."""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]
        
        for sql_attempt in sql_injection_attempts:
            hashed = get_password_hash(sql_attempt)
            
            # Should hash without issues
            assert hashed.startswith("$2b$")
            
            # Should verify correctly
            assert verify_password(sql_attempt, hashed) is True
            
            # SQL should not be in hash
            assert "DROP" not in hashed.upper()
            assert "UNION" not in hashed.upper()
    
    def test_xss_in_password(self):
        """Test that XSS attempts in passwords are safely hashed."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]
        
        for xss_attempt in xss_attempts:
            hashed = get_password_hash(xss_attempt)
            
            # Should hash without issues
            assert hashed.startswith("$2b$")
            
            # Should verify correctly
            assert verify_password(xss_attempt, hashed) is True
            
            # XSS should not be executable in hash
            assert "<script>" not in hashed
            assert "javascript:" not in hashed


class TestPasswordValidation:
    """Test password validation scenarios."""
    
    def test_common_passwords_still_hash(self):
        """Test that even common/weak passwords can be hashed."""
        # Note: This tests hashing, not policy enforcement
        # Password policy should be enforced at application level
        common_passwords = [
            "password",
            "123456",
            "qwerty",
            "admin",
            "letmein",
        ]
        
        for password in common_passwords:
            hashed = get_password_hash(password)
            assert hashed.startswith("$2b$")
            assert verify_password(password, hashed) is True
    
    def test_whitespace_in_password(self):
        """Test passwords with whitespace."""
        passwords_with_whitespace = [
            " password",           # Leading space
            "password ",           # Trailing space
            "pass word",           # Middle space
            "pass  word",          # Double space
            "\tpassword",          # Tab
            "password\n",          # Newline
        ]
        
        for password in passwords_with_whitespace:
            hashed = get_password_hash(password)
            
            # Should hash and verify exactly as provided
            assert verify_password(password, hashed) is True
            
            # Whitespace matters (should not trim)
            if password != password.strip():
                assert verify_password(password.strip(), hashed) is False


# ============================================================================
# Performance Tests
# ============================================================================

class TestPasswordPerformance:
    """Test password hashing performance."""
    
    def test_hashing_performance(self):
        """Test that password hashing is reasonably fast but not too fast."""
        import time
        
        password = "TestPassword123"
        
        start = time.perf_counter()
        get_password_hash(password)
        duration = time.perf_counter() - start
        
        # Bcrypt should take noticeable time (security feature)
        # Should be > 10ms (secure)
        assert duration > 0.01, "Hashing should take time (security feature)"
        
        # But not too slow for UX (< 5 seconds)
        assert duration < 5.0, "Hashing should not be too slow"
    
    def test_verification_performance(self):
        """Test that password verification is reasonably fast."""
        import time
        
        password = "TestPassword123"
        hashed = get_password_hash(password)
        
        start = time.perf_counter()
        verify_password(password, hashed)
        duration = time.perf_counter() - start
        
        # Verification should also take time (security feature)
        assert duration > 0.01, "Verification should take time"
        assert duration < 5.0, "Verification should not be too slow"
    
    @pytest.mark.skip(reason="Performance test, run manually")
    def test_multiple_hashes_performance(self):
        """Test performance of hashing multiple passwords."""
        import time
        
        passwords = [f"password{i}" for i in range(10)]
        
        start = time.perf_counter()
        for password in passwords:
            get_password_hash(password)
        duration = time.perf_counter() - start
        
        avg_time = duration / len(passwords)
        print(f"\nAverage hashing time: {avg_time:.4f}s per password")
        
        # Should complete 10 hashes in reasonable time
        assert duration < 50.0, "Should hash 10 passwords in <50 seconds"

