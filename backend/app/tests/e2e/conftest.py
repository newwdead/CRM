"""
E2E Test Fixtures
Configuration and fixtures for end-to-end tests
"""
import pytest
import httpx
from typing import Dict, AsyncGenerator


@pytest.fixture
def async_client():
    """Create async HTTP client for E2E tests"""
    return httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=30.0,
        follow_redirects=True
    )


@pytest.fixture
def test_user_credentials() -> Dict[str, str]:
    """Test user credentials"""
    import time
    timestamp = int(time.time() * 1000)  # millisecond precision
    return {
        "username": f"testuser_e2e_{timestamp}",
        "email": f"testuser_e2e_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": "E2E Test User"
    }


@pytest.fixture
async def authenticated_client(
    async_client: httpx.AsyncClient,
    test_user_credentials: Dict[str, str]
) -> AsyncGenerator[tuple[httpx.AsyncClient, Dict], None]:
    """
    Create authenticated client with test user
    Returns: (client, user_data)
    """
    # Register user
    register_response = await async_client.post(
        "/auth/register",
        json=test_user_credentials
    )
    
    if register_response.status_code not in [201, 400]:  # 400 if user exists
        raise Exception(f"Registration failed: {register_response.text}")
    
    # Login
    login_response = await async_client.post(
        "/auth/login",
        data={
            "username": test_user_credentials["username"],
            "password": test_user_credentials["password"]
        }
    )
    
    if login_response.status_code != 200:
        raise Exception(f"Login failed: {login_response.text}")
    
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # Add token to client headers
    async_client.headers.update({
        "Authorization": f"Bearer {access_token}"
    })
    
    yield async_client, token_data
    
    # Cleanup: logout
    await async_client.post("/auth/logout")


# Add timestamp for unique usernames
@pytest.fixture(scope="session", autouse=True)
def setup_timestamp():
    """Generate unique timestamp for test run"""
    import time
    pytest.timestamp = int(time.time())

