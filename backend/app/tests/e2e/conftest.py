"""
E2E Test Fixtures
Configuration and fixtures for end-to-end tests
"""
import pytest
import httpx
from typing import Dict, AsyncGenerator


@pytest.fixture(scope="session")
def e2e_test_user():
    """
    Create E2E test user directly in database
    Returns credentials dict
    """
    from app.database import SessionLocal
    from app.models import User
    from app.core.auth import get_password_hash
    
    db = SessionLocal()
    
    # E2E test user credentials
    username = "e2e_test_user"
    password = "E2ETestPass123!"
    
    # Check if user exists
    existing_user = db.query(User).filter(User.username == username).first()
    
    if not existing_user:
        # Create new E2E test user
        new_user = User(
            username=username,
            email="e2e_test@example.com",
            hashed_password=get_password_hash(password),
            full_name="E2E Test User",
            is_active=True,
            is_admin=False
        )
        db.add(new_user)
        db.commit()
        print(f"✅ Created E2E test user: {username}")
    else:
        # Update existing user to ensure correct password
        existing_user.hashed_password = get_password_hash(password)
        existing_user.is_active = True
        db.commit()
        print(f"✅ Updated E2E test user: {username}")
    
    db.close()
    
    return {
        "username": username,
        "password": password,
        "email": "e2e_test@example.com"
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

