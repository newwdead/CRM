"""
E2E Test: User Authentication Flow
Tests complete user registration, login, and authentication cycle
"""
import pytest
import httpx
from typing import Dict


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_authentication_flow(
    async_client: httpx.AsyncClient,
    test_user_credentials: Dict[str, str]
):
    """
    Test Flow 1: User Registration & Authentication
    
    Steps:
    1. Register new user
    2. Verify can't access protected endpoint without auth
    3. Login with credentials
    4. Verify can access protected endpoint with token
    5. Refresh access token
    6. Logout
    """
    
    async with async_client as client:
        # Step 1: Register new user
        register_response = await client.post(
            "/auth/register",
            json=test_user_credentials
        )
        assert register_response.status_code in [201, 400], \
            f"Registration failed: {register_response.text}"
        
        if register_response.status_code == 201:
            user_data = register_response.json()
            assert user_data["username"] == test_user_credentials["username"]
            assert user_data["email"] == test_user_credentials["email"]
            assert "password" not in user_data, "Password should not be in response"
        
        # Step 2: Verify can't access protected endpoint
        me_response_unauth = await client.get("/auth/me")
    assert me_response_unauth.status_code == 401, \
        "Should require authentication"
    
    # Step 3: Login with credentials
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"]
        }
    )
    assert login_response.status_code == 200, \
        f"Login failed: {login_response.text}"
    
    token_data = login_response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    access_token = token_data["access_token"]
    
    # Step 4: Verify can access protected endpoint with token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response_auth = await async_client.get("/auth/me", headers=headers)
    assert me_response_auth.status_code == 200, \
        f"Failed to get user info: {me_response_auth.text}"
    
    me_data = me_response_auth.json()
    assert me_data["username"] == test_user_credentials["username"]
    assert me_data["email"] == test_user_credentials["email"]
    
    # Step 5: Refresh access token (if refresh token available)
    if "refresh_token" in token_data:
        refresh_response = await async_client.post(
            "/auth/refresh",
            json={"refresh_token": token_data["refresh_token"]}
        )
        
        if refresh_response.status_code == 200:
            new_token_data = refresh_response.json()
            assert "access_token" in new_token_data
            new_access_token = new_token_data["access_token"]
            assert new_access_token != access_token, \
                "New token should be different"
            
            # Verify new token works
            headers_new = {"Authorization": f"Bearer {new_access_token}"}
            me_response_new = await async_client.get("/auth/me", headers=headers_new)
            assert me_response_new.status_code == 200
    
    # Step 6: Logout
    logout_response = await async_client.post(
        "/auth/logout",
        headers=headers
    )
    assert logout_response.status_code in [200, 204], \
        f"Logout failed: {logout_response.text}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_authentication_failure_scenarios(
    async_client: httpx.AsyncClient
):
    """Test various authentication failure scenarios"""
    
    # Test 1: Login with non-existent user
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": "nonexistent_user_12345",
            "password": "wrongpassword"
        }
    )
    assert login_response.status_code == 401, \
        "Should fail with invalid credentials"
    
    # Test 2: Register with invalid email
    register_response = await async_client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
    )
    assert register_response.status_code == 422, \
        "Should fail with invalid email format"
    
    # Test 3: Access protected endpoint without token
    me_response = await async_client.get("/auth/me")
    assert me_response.status_code == 401, \
        "Should require authentication"
    
    # Test 4: Access with invalid token
    headers = {"Authorization": "Bearer invalid_token_12345"}
    me_response_invalid = await async_client.get("/auth/me", headers=headers)
    assert me_response_invalid.status_code == 401, \
        "Should reject invalid token"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_password_strength_validation(
    async_client: httpx.AsyncClient,
    test_user_credentials: Dict[str, str]
):
    """Test password strength requirements"""
    
    weak_passwords = [
        "123",  # Too short
        "12345",  # Still too short
    ]
    
    for weak_password in weak_passwords:
        register_response = await async_client.post(
            "/auth/register",
            json={
                "username": f"testuser_{weak_password}",
                "email": f"test_{weak_password}@example.com",
                "password": weak_password
            }
        )
        assert register_response.status_code == 422, \
            f"Should reject weak password: {weak_password}"

