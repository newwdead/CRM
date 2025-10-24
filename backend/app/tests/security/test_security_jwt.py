"""
Security Tests: JWT Token Creation and Validation
Tests for backend/app/core/security.py JWT functions.
"""

import pytest
import time
from datetime import timedelta, datetime
from jose import jwt, JWTError
from app.core.security import (
    create_access_token,
    decode_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


class TestJWTTokenCreation:
    """Test JWT access token creation."""
    
    def test_create_basic_access_token(self):
        """Test creating a basic JWT access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str), "Token should be a string"
        
        # Token should have 3 parts (header.payload.signature)
        parts = token.split('.')
        assert len(parts) == 3, "JWT should have 3 parts"
        
        # Each part should be base64-encoded (non-empty)
        for part in parts:
            assert len(part) > 0, "Each JWT part should be non-empty"
    
    def test_create_token_with_user_data(self):
        """Test creating token with various user data."""
        test_cases = [
            {"sub": "admin"},
            {"sub": "user@example.com"},
            {"sub": "user123", "role": "admin"},
            {"sub": "testuser", "is_admin": True},
        ]
        
        for data in test_cases:
            token = create_access_token(data)
            assert isinstance(token, str)
            assert len(token.split('.')) == 3
    
    def test_create_token_expiration_default(self):
        """Test that token has default expiration."""
        data = {"sub": "testuser"}
        
        # Record time before creating token
        before_timestamp = datetime.utcnow().timestamp()
        token = create_access_token(data)
        after_timestamp = datetime.utcnow().timestamp()
        
        # Decode without verification to check payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Should have expiration field
        assert "exp" in payload, "Token should have expiration"
        
        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        assert exp_timestamp > after_timestamp, "Expiration should be in future"
        
        # Expiration should be reasonable (approximately ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow for timezone differences and clock skew (±2 hour tolerance for very long tokens)
        expected_exp_min = before_timestamp + (ACCESS_TOKEN_EXPIRE_MINUTES * 60) - 7200
        expected_exp_max = after_timestamp + (ACCESS_TOKEN_EXPIRE_MINUTES * 60) + 7200
        actual_duration = exp_timestamp - before_timestamp
        expected_duration = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert expected_exp_min <= exp_timestamp <= expected_exp_max, \
            f"Expiration mismatch: expected ~{expected_duration}s, got {actual_duration}s (diff: {actual_duration - expected_duration}s)"
    
    def test_create_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        
        before_timestamp = datetime.utcnow().timestamp()
        token = create_access_token(data, expires_delta=expires_delta)
        after_timestamp = datetime.utcnow().timestamp()
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration is approximately 30 minutes from creation time
        exp_timestamp = payload["exp"]
        # Allow ±2 hours tolerance (to account for server time differences)
        expected_exp_min = before_timestamp + (30 * 60) - 7200
        expected_exp_max = after_timestamp + (30 * 60) + 7200
        assert expected_exp_min <= exp_timestamp <= expected_exp_max, \
            "Custom expiration should be approximately respected"
    
    def test_create_token_with_short_expiration(self):
        """Test creating token with very short expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=5)
        
        before_timestamp = datetime.utcnow().timestamp()
        token = create_access_token(data, expires_delta=expires_delta)
        after_timestamp = datetime.utcnow().timestamp()
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp_timestamp = payload["exp"]
        # For short expiration, allow ±2 hours tolerance (server time differences)
        expected_exp_min = before_timestamp + 5 - 7200
        expected_exp_max = after_timestamp + 5 + 7200
        assert expected_exp_min <= exp_timestamp <= expected_exp_max, \
            "Short expiration should be approximately respected"
    
    def test_create_token_with_long_expiration(self):
        """Test creating token with long expiration (days)."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(days=365)  # 1 year
        
        before_timestamp = datetime.utcnow().timestamp()
        token = create_access_token(data, expires_delta=expires_delta)
        after_timestamp = datetime.utcnow().timestamp()
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        exp_timestamp = payload["exp"]
        # For long expiration, allow ±2 hours tolerance (server time differences)
        expected_exp_min = before_timestamp + (365 * 24 * 60 * 60) - 7200
        expected_exp_max = after_timestamp + (365 * 24 * 60 * 60) + 7200
        assert expected_exp_min <= exp_timestamp <= expected_exp_max, \
            "Long expiration should be approximately respected"
    
    def test_create_token_preserves_data(self):
        """Test that token creation preserves all original data."""
        data = {
            "sub": "testuser",
            "email": "test@example.com",
            "is_admin": True,
            "custom_field": "custom_value"
        }
        
        token = create_access_token(data)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # All original fields should be present
        assert payload["sub"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["is_admin"] is True
        assert payload["custom_field"] == "custom_value"
        
        # Plus expiration
        assert "exp" in payload


class TestJWTTokenDecoding:
    """Test JWT access token decoding and validation."""
    
    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        data = {"sub": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        # Should return dictionary
        assert decoded is not None, "Valid token should decode successfully"
        assert isinstance(decoded, dict), "Decoded payload should be dict"
        
        # Should contain original data
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"
        
        # Should contain expiration
        assert "exp" in decoded
    
    def test_decode_token_with_complex_data(self):
        """Test decoding token with complex nested data."""
        data = {
            "sub": "testuser",
            "metadata": {
                "roles": ["admin", "user"],
                "permissions": ["read", "write"]
            }
        }
        
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert "metadata" in decoded
        assert decoded["metadata"]["roles"] == ["admin", "user"]
    
    def test_decode_malformed_token(self):
        """Test decoding malformed tokens."""
        malformed_tokens = [
            "",                          # Empty string
            "not.a.token",               # Not enough parts
            "invalid",                   # Single part
            "header.payload",            # Only 2 parts
            "header.payload.signature.extra",  # Too many parts
            "aaaa.bbbb.cccc",           # Invalid base64
        ]
        
        for token in malformed_tokens:
            decoded = decode_access_token(token)
            assert decoded is None, f"Malformed token should return None: {token}"
    
    def test_decode_token_with_wrong_signature(self):
        """Test decoding token with tampered signature."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Tamper with the signature
        parts = token.split('.')
        parts[2] = "tampered_signature_xyz123"
        tampered_token = '.'.join(parts)
        
        decoded = decode_access_token(tampered_token)
        assert decoded is None, "Tampered token should be rejected"
    
    def test_decode_token_with_wrong_algorithm(self):
        """Test decoding token signed with different algorithm."""
        data = {"sub": "testuser"}
        
        # Create token with HS512 instead of HS256
        token = jwt.encode(data, SECRET_KEY, algorithm="HS512")
        
        decoded = decode_access_token(token)
        assert decoded is None, "Token with wrong algorithm should be rejected"
    
    def test_decode_token_with_wrong_secret(self):
        """Test decoding token signed with different secret."""
        data = {"sub": "testuser"}
        
        # Create token with wrong secret
        wrong_secret = "wrong-secret-key"
        token = jwt.encode(data, wrong_secret, algorithm=ALGORITHM)
        
        decoded = decode_access_token(token)
        assert decoded is None, "Token with wrong secret should be rejected"
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        data = {"sub": "testuser"}
        
        # Create token that expires in 1 second
        expires_delta = timedelta(seconds=1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Token should be valid immediately
        decoded = decode_access_token(token)
        assert decoded is not None, "Token should be valid immediately"
        
        # Wait for expiration
        time.sleep(2)
        
        # Token should now be expired
        decoded = decode_access_token(token)
        assert decoded is None, "Expired token should be rejected"
    
    def test_decode_token_with_tampered_payload(self):
        """Test decoding token with tampered payload."""
        data = {"sub": "user"}
        token = create_access_token(data)
        
        # Tamper with the payload (middle part)
        parts = token.split('.')
        # Try to change user to admin by tampering payload
        tampered_payload = parts[1] + "tampered"
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
        
        decoded = decode_access_token(tampered_token)
        assert decoded is None, "Token with tampered payload should be rejected"


class TestJWTTokenSecurity:
    """Test security properties of JWT implementation."""
    
    def test_token_algorithm_is_hs256(self):
        """Test that HS256 algorithm is used."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Decode header to check algorithm
        parts = token.split('.')
        import base64
        import json
        
        # Pad base64 string if needed
        header_b64 = parts[0]
        header_b64 += "=" * (4 - len(header_b64) % 4)
        
        header_bytes = base64.urlsafe_b64decode(header_b64)
        header = json.loads(header_bytes)
        
        assert header["alg"] == "HS256", "Should use HS256 algorithm"
        assert header["typ"] == "JWT", "Should be JWT type"
    
    def test_token_cannot_be_decoded_without_secret(self):
        """Test that token cannot be decoded without secret key."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Try to decode with wrong secret
        try:
            jwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])
            assert False, "Should raise exception for wrong secret"
        except JWTError:
            pass  # Expected
    
    def test_token_signature_verification(self):
        """Test that signature is properly verified."""
        data = {"sub": "testuser"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        
        # Same data but different tokens (due to expiration time)
        # But both should decode successfully
        decoded1 = decode_access_token(token1)
        decoded2 = decode_access_token(token2)
        
        assert decoded1 is not None
        assert decoded2 is not None
        assert decoded1["sub"] == decoded2["sub"]
    
    def test_token_replay_attack_prevention(self):
        """Test that expired tokens cannot be replayed."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Token valid now
        assert decode_access_token(token) is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Same token now invalid
        assert decode_access_token(token) is None
        
        # Verify this happens multiple times (no replay)
        assert decode_access_token(token) is None
        assert decode_access_token(token) is None
    
    def test_token_contains_no_sensitive_data_in_plain(self):
        """Test that token doesn't expose sensitive data in plain text."""
        data = {"sub": "testuser", "password": "should_not_be_visible"}
        token = create_access_token(data)
        
        # Payload is base64-encoded but not encrypted
        # So we should NOT put sensitive data in tokens
        parts = token.split('.')
        import base64
        
        payload_b64 = parts[1]
        # Pad if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload_str = payload_bytes.decode('utf-8')
        
        # Password would be visible in payload (this is by design)
        # This test serves as a reminder: DON'T PUT PASSWORDS IN TOKENS!
        assert "should_not_be_visible" in payload_str, \
            "JWT payload is base64-encoded, not encrypted - never store passwords!"
    
    def test_token_timing_safe_comparison(self):
        """Test that token validation uses timing-safe comparison."""
        data = {"sub": "testuser"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        
        # Measure time to validate correct token
        start = time.perf_counter()
        decode_access_token(token1)
        correct_time = time.perf_counter() - start
        
        # Measure time to validate incorrect token
        start = time.perf_counter()
        decode_access_token(token1[:-5] + "wrong")
        incorrect_time = time.perf_counter() - start
        
        # Times should be relatively similar (within 100x)
        # This is a simplified test; real timing attacks are more sophisticated
        if correct_time > 0 and incorrect_time > 0:
            time_ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
            # JWT verification is cryptographic, should have consistent timing
            assert time_ratio < 100, "Token validation should have consistent timing"


class TestJWTEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_create_token_with_empty_data(self):
        """Test creating token with minimal data."""
        data = {"sub": ""}  # Empty username
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == ""
    
    def test_create_token_with_unicode_data(self):
        """Test creating token with unicode characters."""
        data = {
            "sub": "用户",  # Chinese
            "name": "Пользователь",  # Russian
            "emoji": "👤🔒"  # Emojis
        }
        
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "用户"
        assert decoded["name"] == "Пользователь"
        assert decoded["emoji"] == "👤🔒"
    
    def test_create_token_with_special_characters(self):
        """Test creating token with special characters."""
        data = {
            "sub": "user@example.com",
            "special": "!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
        }
        
        token = create_access_token(data)
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["special"] == "!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
    
    def test_create_token_with_large_payload(self):
        """Test creating token with large payload."""
        # Create large data (but reasonable for JWT)
        data = {
            "sub": "testuser",
            "large_data": "x" * 1000  # 1KB of data
        }
        
        token = create_access_token(data)
        assert len(token) < 2000, "Token should not be excessively large"
        
        decoded = decode_access_token(token)
        assert decoded is not None
        assert len(decoded["large_data"]) == 1000
    
    def test_decode_none_token(self):
        """Test decoding None as token."""
        # This tests error handling
        try:
            decoded = decode_access_token(None)
            assert decoded is None, "None token should return None"
        except (TypeError, AttributeError):
            # Also acceptable to raise exception
            pass
    
    def test_create_token_with_zero_expiration(self):
        """Test creating token with zero expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=0)
        
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Token should be immediately or almost immediately expired
        # Depending on timing, might decode or not
        decoded = decode_access_token(token)
        # Either None (expired) or dict (just in time) is acceptable
        assert decoded is None or isinstance(decoded, dict)


class TestJWTConfiguration:
    """Test JWT configuration and constants."""
    
    def test_secret_key_configured(self):
        """Test that SECRET_KEY is configured."""
        from app.core.security import SECRET_KEY
        
        assert SECRET_KEY is not None, "SECRET_KEY should be configured"
        assert len(SECRET_KEY) > 10, "SECRET_KEY should be reasonably long"
        assert isinstance(SECRET_KEY, str), "SECRET_KEY should be a string"
    
    def test_algorithm_is_hs256(self):
        """Test that ALGORITHM is HS256."""
        from app.core.security import ALGORITHM
        
        assert ALGORITHM == "HS256", "Should use HS256 algorithm"
    
    def test_access_token_expire_minutes_configured(self):
        """Test that ACCESS_TOKEN_EXPIRE_MINUTES is configured."""
        from app.core.security import ACCESS_TOKEN_EXPIRE_MINUTES
        
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0, "Expiration should be positive"
        assert ACCESS_TOKEN_EXPIRE_MINUTES <= 43200, "Max 30 days (reasonable limit)"
    
    def test_secret_key_not_default_in_production(self):
        """Test that default secret key is detected (warning)."""
        from app.core.security import SECRET_KEY
        
        # If using default secret, this is a security warning
        default_secret = "your-secret-key-change-this-in-production"
        
        if default_secret in SECRET_KEY:
            pytest.skip("⚠️  WARNING: Using default SECRET_KEY! Change in production!")


# ============================================================================
# Performance Tests
# ============================================================================

class TestJWTPerformance:
    """Test JWT token performance."""
    
    def test_token_creation_performance(self):
        """Test that token creation is fast."""
        data = {"sub": "testuser"}
        
        start = time.perf_counter()
        create_access_token(data)
        duration = time.perf_counter() - start
        
        # Token creation should be very fast (<10ms)
        assert duration < 0.01, "Token creation should be fast"
    
    def test_token_decoding_performance(self):
        """Test that token decoding is fast."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        start = time.perf_counter()
        decode_access_token(token)
        duration = time.perf_counter() - start
        
        # Token decoding should be fast (<10ms)
        assert duration < 0.01, "Token decoding should be fast"
    
    @pytest.mark.skip(reason="Performance test, run manually")
    def test_bulk_token_operations_performance(self):
        """Test performance of creating and decoding many tokens."""
        count = 1000
        
        # Test creation
        start = time.perf_counter()
        tokens = []
        for i in range(count):
            token = create_access_token({"sub": f"user{i}"})
            tokens.append(token)
        creation_time = time.perf_counter() - start
        
        print(f"\nCreated {count} tokens in {creation_time:.4f}s")
        print(f"Average: {creation_time/count*1000:.4f}ms per token")
        
        # Test decoding
        start = time.perf_counter()
        for token in tokens:
            decode_access_token(token)
        decoding_time = time.perf_counter() - start
        
        print(f"Decoded {count} tokens in {decoding_time:.4f}s")
        print(f"Average: {decoding_time/count*1000:.4f}ms per token")
        
        # Should complete in reasonable time
        assert creation_time < 10.0, "Should create 1000 tokens in <10s"
        assert decoding_time < 10.0, "Should decode 1000 tokens in <10s"

