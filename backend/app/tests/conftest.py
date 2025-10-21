"""
Pytest configuration and fixtures
"""
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
def auth_token(client, test_user_data):
    """Create a regular user and return auth token"""
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Login and get token
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]


@pytest.fixture
def admin_auth_token(client, test_db):
    """Create an admin user and return auth token"""
    from ..models import User
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
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
    
    # Login and get token
    login_data = {
        "username": "admin",
        "password": "adminpass123"
    }
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]

