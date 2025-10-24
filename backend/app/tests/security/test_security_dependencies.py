"""
Security Tests: Dependency Functions
Tests for backend/app/core/security.py dependency functions.
These are async functions used in FastAPI endpoints.
"""

import pytest
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    create_access_token,
    get_password_hash
)
from app.models import User


@pytest.fixture
def test_user(db: Session):
    """Create a test user for dependency tests."""
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


@pytest.fixture
def inactive_admin(db: Session):
    """Create an inactive admin user."""
    user = User(
        username="inactiveadmin",
        email="inactiveadmin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Inactive Admin",
        is_active=False,
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# Tests: get_current_user()
# ============================================================================

class TestGetCurrentUser:
    """Test get_current_user() dependency function."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self, db: Session, test_user: User):
        """Test getting current user with valid token."""
        # Create valid token
        token = create_access_token({"sub": test_user.username})
        
        # Call dependency
        current_user = await get_current_user(token=token, db=db)
        
        assert current_user is not None
        assert current_user.id == test_user.id
        assert current_user.username == test_user.username
        assert current_user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_no_token(self, db: Session):
        """Test that missing token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail
        assert "WWW-Authenticate" in exc_info.value.headers
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_empty_token(self, db: Session):
        """Test that empty token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="", db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, db: Session):
        """Test that invalid token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid_token", db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token(self, db: Session, test_user: User):
        """Test that expired token raises 401."""
        import time
        
        # Create token that expires in 1 second
        token = create_access_token(
            {"sub": test_user.username},
            expires_delta=timedelta(seconds=1)
        )
        
        # Wait for expiration
        time.sleep(2)
        
        # Try to use expired token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_tampered_token(self, db: Session, test_user: User):
        """Test that tampered token raises 401."""
        # Create valid token
        token = create_access_token({"sub": test_user.username})
        
        # Tamper with token
        parts = token.split('.')
        tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=tampered_token, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_nonexistent_username(self, db: Session):
        """Test that token for non-existent user raises 401."""
        # Create token for non-existent user
        token = create_access_token({"sub": "nonexistentuser"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_token_missing_sub(self, db: Session):
        """Test that token without 'sub' claim raises 401."""
        # Create token without 'sub' field
        token = create_access_token({"user_id": "123", "email": "test@example.com"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_get_current_user_returns_full_user_object(self, db: Session, test_user: User):
        """Test that dependency returns complete user object."""
        token = create_access_token({"sub": test_user.username})
        current_user = await get_current_user(token=token, db=db)
        
        # Verify all important fields
        assert hasattr(current_user, 'id')
        assert hasattr(current_user, 'username')
        assert hasattr(current_user, 'email')
        assert hasattr(current_user, 'full_name')
        assert hasattr(current_user, 'is_active')
        assert hasattr(current_user, 'is_admin')
        
        assert current_user.username == test_user.username
        assert current_user.email == test_user.email
        assert current_user.is_active == test_user.is_active
        assert current_user.is_admin == test_user.is_admin
    
    @pytest.mark.asyncio
    async def test_get_current_user_with_inactive_user_token(self, db: Session, inactive_user: User):
        """Test that inactive user can be retrieved (activation check is in next dependency)."""
        token = create_access_token({"sub": inactive_user.username})
        current_user = await get_current_user(token=token, db=db)
        
        # Should succeed (activation check is in get_current_active_user)
        assert current_user is not None
        assert current_user.id == inactive_user.id
        assert current_user.is_active is False


# ============================================================================
# Tests: get_current_active_user()
# ============================================================================

class TestGetCurrentActiveUser:
    """Test get_current_active_user() dependency function."""
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_with_active_user(self, test_user: User):
        """Test that active user passes through successfully."""
        current_user = await get_current_active_user(current_user=test_user)
        
        assert current_user is not None
        assert current_user.id == test_user.id
        assert current_user.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_with_inactive_user(self, inactive_user: User):
        """Test that inactive user raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_with_active_admin(self, admin_user: User):
        """Test that active admin user passes through."""
        current_user = await get_current_active_user(current_user=admin_user)
        
        assert current_user is not None
        assert current_user.id == admin_user.id
        assert current_user.is_active is True
        assert current_user.is_admin is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_with_inactive_admin(self, inactive_admin: User):
        """Test that inactive admin also raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=inactive_admin)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Inactive user" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_preserves_user_data(self, test_user: User):
        """Test that user object is preserved through dependency."""
        current_user = await get_current_active_user(current_user=test_user)
        
        assert current_user.id == test_user.id
        assert current_user.username == test_user.username
        assert current_user.email == test_user.email
        assert current_user.full_name == test_user.full_name
        assert current_user.is_admin == test_user.is_admin
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_returns_same_object(self, test_user: User):
        """Test that dependency returns the same user object."""
        current_user = await get_current_active_user(current_user=test_user)
        
        # Should be the same object reference
        assert current_user is test_user


# ============================================================================
# Tests: get_current_admin_user()
# ============================================================================

class TestGetCurrentAdminUser:
    """Test get_current_admin_user() dependency function."""
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_with_admin(self, admin_user: User):
        """Test that admin user passes through successfully."""
        current_admin = await get_current_admin_user(current_user=admin_user)
        
        assert current_admin is not None
        assert current_admin.id == admin_user.id
        assert current_admin.is_admin is True
        assert current_admin.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_with_regular_user(self, test_user: User):
        """Test that non-admin user raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=test_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_with_inactive_admin(self, inactive_admin: User):
        """Test behavior of inactive admin at admin check level."""
        # Note: get_current_admin_user only checks is_admin flag
        # Active status check happens in get_current_active_user (earlier in chain)
        # This tests the case if active check is bypassed
        
        # get_current_admin_user only checks is_admin, not is_active
        result = await get_current_admin_user(current_user=inactive_admin)
        
        # Should pass admin check (is_admin=True)
        # Inactive status would be caught earlier in dependency chain
        assert result is not None
        assert result.is_admin is True
        assert result.is_active is False  # Documents that active check is elsewhere
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_preserves_user_data(self, admin_user: User):
        """Test that admin user object is preserved."""
        current_admin = await get_current_admin_user(current_user=admin_user)
        
        assert current_admin.id == admin_user.id
        assert current_admin.username == admin_user.username
        assert current_admin.email == admin_user.email
        assert current_admin.full_name == admin_user.full_name
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_returns_same_object(self, admin_user: User):
        """Test that dependency returns the same user object."""
        current_admin = await get_current_admin_user(current_user=admin_user)
        
        # Should be the same object reference
        assert current_admin is admin_user
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_with_inactive_regular_user(self, inactive_user: User):
        """Test that inactive non-admin raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=inactive_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        # Could be either "Admin access required" or from active check
        # Depends on dependency chain order


# ============================================================================
# Integration Tests: Full Dependency Chain
# ============================================================================

class TestDependencyChain:
    """Test the full dependency chain integration."""
    
    @pytest.mark.asyncio
    async def test_full_chain_active_user(self, db: Session, test_user: User):
        """Test full chain: token → current_user → active_user."""
        # Step 1: Create token
        token = create_access_token({"sub": test_user.username})
        
        # Step 2: Get current user
        current_user = await get_current_user(token=token, db=db)
        assert current_user is not None
        
        # Step 3: Verify active
        active_user = await get_current_active_user(current_user=current_user)
        assert active_user is not None
        assert active_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_full_chain_admin_user(self, db: Session, admin_user: User):
        """Test full chain: token → current_user → active_user → admin_user."""
        # Step 1: Create token
        token = create_access_token({"sub": admin_user.username})
        
        # Step 2: Get current user
        current_user = await get_current_user(token=token, db=db)
        assert current_user is not None
        
        # Step 3: Verify active
        active_user = await get_current_active_user(current_user=current_user)
        assert active_user is not None
        
        # Step 4: Verify admin
        admin = await get_current_admin_user(current_user=active_user)
        assert admin is not None
        assert admin.is_admin is True
    
    @pytest.mark.asyncio
    async def test_full_chain_inactive_user_fails_at_active_check(
        self, db: Session, inactive_user: User
    ):
        """Test that inactive user fails at active check."""
        # Step 1: Create token
        token = create_access_token({"sub": inactive_user.username})
        
        # Step 2: Get current user (succeeds)
        current_user = await get_current_user(token=token, db=db)
        assert current_user is not None
        
        # Step 3: Verify active (fails)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=current_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    
    @pytest.mark.asyncio
    async def test_full_chain_non_admin_fails_at_admin_check(
        self, db: Session, test_user: User
    ):
        """Test that non-admin fails at admin check."""
        # Step 1-2: Get active user
        token = create_access_token({"sub": test_user.username})
        current_user = await get_current_user(token=token, db=db)
        active_user = await get_current_active_user(current_user=current_user)
        
        # Step 3: Try admin check (fails)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=active_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_full_chain_no_token_fails_immediately(self, db: Session):
        """Test that missing token fails at first dependency."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_full_chain_invalid_token_fails_immediately(self, db: Session):
        """Test that invalid token fails at first dependency."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid", db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Security Tests
# ============================================================================

class TestDependencySecurity:
    """Test security aspects of dependency functions."""
    
    @pytest.mark.asyncio
    async def test_token_reuse_across_requests(self, db: Session, test_user: User):
        """Test that same token can be reused (until expiration)."""
        token = create_access_token({"sub": test_user.username})
        
        # Use token multiple times
        for _ in range(3):
            current_user = await get_current_user(token=token, db=db)
            assert current_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_different_tokens_same_user(self, db: Session, test_user: User):
        """Test that different tokens for same user both work."""
        token1 = create_access_token({"sub": test_user.username})
        token2 = create_access_token({"sub": test_user.username})
        
        # Both tokens should work
        user1 = await get_current_user(token=token1, db=db)
        user2 = await get_current_user(token=token2, db=db)
        
        assert user1.id == user2.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_token_for_different_users(self, db: Session, test_user: User, admin_user: User):
        """Test that tokens are user-specific."""
        token_user = create_access_token({"sub": test_user.username})
        token_admin = create_access_token({"sub": admin_user.username})
        
        # Each token should return correct user
        user = await get_current_user(token=token_user, db=db)
        admin = await get_current_user(token=token_admin, db=db)
        
        assert user.id == test_user.id
        assert admin.id == admin_user.id
        assert user.id != admin.id
    
    @pytest.mark.asyncio
    async def test_sql_injection_in_token_payload(self, db: Session):
        """Test SQL injection attempts in token payload."""
        sql_injection = "admin' OR '1'='1"
        token = create_access_token({"sub": sql_injection})
        
        # Should not find user (safe from SQL injection)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_http_exception_structure_401(self, db: Session):
        """Test that 401 HTTPException has correct structure."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None, db=db)
        
        exception = exc_info.value
        assert exception.status_code == 401
        assert isinstance(exception.detail, str)
        assert "headers" in dir(exception)
        assert "WWW-Authenticate" in exception.headers
    
    @pytest.mark.asyncio
    async def test_http_exception_structure_403(self, test_user: User):
        """Test that 403 HTTPException has correct structure."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(current_user=test_user)
        
        exception = exc_info.value
        assert exception.status_code == 403
        assert isinstance(exception.detail, str)


# ============================================================================
# Performance Tests
# ============================================================================

class TestDependencyPerformance:
    """Test dependency function performance."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_performance(self, db: Session, test_user: User):
        """Test that get_current_user is fast."""
        import time
        
        token = create_access_token({"sub": test_user.username})
        
        start = time.perf_counter()
        await get_current_user(token=token, db=db)
        duration = time.perf_counter() - start
        
        # Should be very fast (database query + JWT decode)
        assert duration < 0.5, "Dependency should be fast (<500ms)"
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_performance(self, test_user: User):
        """Test that get_current_active_user is fast."""
        import time
        
        start = time.perf_counter()
        await get_current_active_user(current_user=test_user)
        duration = time.perf_counter() - start
        
        # Should be instant (just attribute check)
        assert duration < 0.01, "Active check should be instant"
    
    @pytest.mark.asyncio
    async def test_get_current_admin_user_performance(self, admin_user: User):
        """Test that get_current_admin_user is fast."""
        import time
        
        start = time.perf_counter()
        await get_current_admin_user(current_user=admin_user)
        duration = time.perf_counter() - start
        
        # Should be instant (just attribute check)
        assert duration < 0.01, "Admin check should be instant"
    
    @pytest.mark.skip(reason="Performance test, run manually")
    @pytest.mark.asyncio
    async def test_dependency_chain_performance(self, db: Session, admin_user: User):
        """Test full dependency chain performance."""
        import time
        
        token = create_access_token({"sub": admin_user.username})
        
        count = 100
        start = time.perf_counter()
        
        for _ in range(count):
            current_user = await get_current_user(token=token, db=db)
            active_user = await get_current_active_user(current_user=current_user)
            await get_current_admin_user(current_user=active_user)
        
        duration = time.perf_counter() - start
        avg_time = duration / count
        
        print(f"\n{count} full dependency chains in {duration:.4f}s")
        print(f"Average: {avg_time*1000:.4f}ms per chain")
        
        # Should complete reasonably
        assert duration < 50.0, f"Should complete {count} chains in <50s"

