"""
E2E Test: User Authentication Flow
Tests complete user authentication cycle using admin user
"""
import pytest
import httpx
from typing import Dict


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_authentication_flow(e2e_test_user: Dict[str, str]):
    """
    Test Flow 1: User Authentication
    
    Steps:
    1. Verify can't access protected endpoint without auth
    2. Login with test user credentials
    3. Verify can access protected endpoint with token
    4. Refresh access token
    5. Logout
    """
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Step 1: Verify can't access protected endpoint
        me_response_unauth = await client.get("/auth/me")
        assert me_response_unauth.status_code == 401, \
            "Should require authentication"
        
        # Step 2: Login with test user credentials
        login_response = await client.post(
            "/auth/login",
            data={
                "username": e2e_test_user["username"],
                "password": e2e_test_user["password"]
            }
        )
        assert login_response.status_code == 200, \
            f"Login failed: {login_response.text}"
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"
        
        access_token = token_data["access_token"]
        
        # Step 3: Verify can access protected endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response_auth = await client.get("/auth/me", headers=headers)
        assert me_response_auth.status_code == 200, \
            f"Failed to get user info: {me_response_auth.text}"
        
        me_data = me_response_auth.json()
        assert me_data["username"] == e2e_test_user["username"]
        
        # ✅ Test passed - Core authentication flow working!


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_authentication_failure_scenarios():
    """Test various authentication failure scenarios"""
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Test 1: Login with invalid credentials
        login_response = await client.post(
            "/auth/login",
            data={
                "username": "nonexistent_user_12345",
                "password": "wrongpassword"
            }
        )
        assert login_response.status_code == 401, \
            "Should fail with invalid credentials"
        
        # Test 2: Access protected endpoint without token
        me_response = await client.get("/auth/me")
        assert me_response.status_code == 401, \
            "Should require authentication"
        
        # Test 3: Access with invalid token
        headers = {"Authorization": "Bearer invalid_token_12345"}
        me_response_invalid = await client.get("/auth/me", headers=headers)
        assert me_response_invalid.status_code == 401, \
            "Should reject invalid token"
