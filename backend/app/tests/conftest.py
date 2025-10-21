"""
Pytest configuration and fixtures
"""
import os
# Set TESTING env var BEFORE importing app modules
os.environ["TESTING"] = "true"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from ..main import app
from ..database import Base, get_db

# Test database URL (SQLite in memory for speed)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_contact_data():
    """Sample contact data for testing"""
    return {
        "full_name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+79001234567",
        "company": "Test Corp",
        "position": "Manager"
    }


@pytest.fixture
def db_session(test_db):
    """Alias for test_db for compatibility"""
    return test_db


@pytest.fixture
def auth_token(client, test_db, test_user_data):
    """Create a regular user and return auth token"""
    from ..models import User
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Create regular user directly in database (to bypass approval requirement)
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=pwd_context.hash(test_user_data["password"]),
        full_name=test_user_data.get("full_name", "Test User"),
        is_active=True,  # Set active to bypass admin approval
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Login and get token (OAuth2PasswordRequestForm expects form data)
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def admin_auth_token(client, test_db):
    """Create an admin user and return auth token"""
    from ..models import User
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Check if admin user already exists
    admin_user = test_db.query(User).filter(User.username == "admin").first()
    
    if not admin_user:
        # Create admin user directly in database
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_context.hash("adminpass123"),
            full_name="Admin User",
            is_active=True,
            is_admin=True
        )
        test_db.add(admin_user)
        test_db.commit()
        test_db.refresh(admin_user)
    
    # Login and get token (OAuth2PasswordRequestForm expects form data)
    login_data = {
        "username": "admin",
        "password": "adminpass123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]

