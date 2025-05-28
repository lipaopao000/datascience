import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient # For async tests if needed, though TestClient is sync
import os

# Import application components
from backend.main import app # Only need app from main
from backend.models.database_models import Base, get_db, _test_session_local # Import _test_session_local
from backend.core.config import settings
from backend.core.security import get_current_active_user # For mocking auth
from backend.models.database_models import User # For creating test user
from backend.models import database_models # Import to ensure all models are registered with Base.metadata
# Removed unnecessary imports for previous mocking strategies
# import os # Not strictly needed if using in-memory db and not cleaning files manually
# from contextlib import asynccontextmanager
# from fastapi import FastAPI

# Use a separate test database URL
TEST_DATABASE_URL = settings.TEST_SQLALCHEMY_DATABASE_URL

# Create a test engine and session
# For in-memory SQLite, use "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine) # Bind to test_engine

@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    Provides a clean database session for each test.
    Creates tables, yields a session, then drops tables.
    For in-memory SQLite, this automatically handles cleanup.
    """
    # Set the global test session local for get_db in database_models.py
    global _test_session_local
    _test_session_local = TestingSessionLocal

    # Ensure all models are imported and registered with Base.metadata
    # This is handled by the `import database_models` above.
    Base.metadata.create_all(bind=test_engine) # Create tables using the test engine
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine) # Drop tables after test
        _test_session_local = None # Reset global for other tests/cleanup


@pytest.fixture(name="client")
def client_fixture(db_session):
    """
    Provides a FastAPI test client with overridden database dependency.
    The lifespan event in main.py will use the test database setup.
    """
    # No need to override get_db here, as it's handled by _test_session_local
    # No need to mock create_tables here, as lifespan in main.py will use the test_engine
    with TestClient(app) as test_client: # TestClient automatically handles lifespan if defined on app
        yield test_client
    
    # Clear any other overrides that might have been set during the test
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
def test_user_fixture(db_session):
    """
    Creates a test user for authenticated tests.
    """
    from backend.core.security import get_password_hash # Import here to avoid circular dependency if security imports models
    
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_password, is_active=True, is_superuser=False)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(name="test_superuser")
def test_superuser_fixture(db_session):
    """
    Creates a test superuser for authenticated tests requiring superuser privileges.
    """
    from backend.core.security import get_password_hash
    
    hashed_password = get_password_hash("superpassword")
    superuser = User(username="superuser", email="super@example.com", hashed_password=hashed_password, is_active=True, is_superuser=True)
    db_session.add(superuser)
    db_session.commit()
    db_session.refresh(superuser)
    return superuser

@pytest.fixture(name="authorized_client")
def authorized_client_fixture(client, test_user):
    """
    Provides a test client authenticated as a regular user.
    Mocks the get_current_active_user dependency.
    """
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="superuser_client")
def superuser_client_fixture(client, test_superuser):
    """
    Provides a test client authenticated as a superuser.
    Mocks the get_current_active_user dependency.
    """
    app.dependency_overrides[get_current_active_user] = lambda: test_superuser
    yield client
    app.dependency_overrides.clear()

# You might also want fixtures for:
# - Mocking external services (e.g., Celery tasks, external APIs)
# - Test data (e.g., pre-populated projects, experiments)
