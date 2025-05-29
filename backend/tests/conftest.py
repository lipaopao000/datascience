import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import application components
from backend.main import app # For client and dependency overrides
from backend.models.database_models import Base, get_db # For table management and dependency override
from backend.core.config import settings
from backend.core import security # Ensure security is imported for overrides
from backend.models.database_models import User # For creating test user
from backend.models import database_models as main_db_models # For patching engine and SessionLocal

# Use a separate test database URL
TEST_DATABASE_URL = settings.TEST_SQLALCHEMY_DATABASE_URL

# 1. test_engine and TestingSessionLocal:
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# 2. patch_engine_for_lifespan (Session-Scoped, Autouse Fixture):
# Ensures the app's global engine and SessionLocal are pointed to the test DB setup for the whole session.
@pytest.fixture(scope="session", autouse=True)
def patch_engine_for_lifespan():
    original_engine = main_db_models.engine
    main_db_models.engine = test_engine
    
    original_session_local_module = main_db_models.SessionLocal
    main_db_models.SessionLocal = TestingSessionLocal
    yield
    main_db_models.engine = original_engine
    main_db_models.SessionLocal = original_session_local_module

# 3. db_session (Function-Scoped Fixture):
# Manages per-test table creation/dropping and provides a DB session.
# Also handles overriding the app's get_db dependency for the duration of the test.
@pytest.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=test_engine)  # Create tables for each test
    db = TestingSessionLocal()
    
    # Store original get_db to restore it later, ensuring other overrides are not affected.
    original_get_db = app.dependency_overrides.get(get_db) 
    app.dependency_overrides[get_db] = lambda: db

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)  # Drop tables after each test
        # Restore the original get_db override if it existed, otherwise remove it.
        if original_get_db:
            app.dependency_overrides[get_db] = original_get_db
        else:
            app.dependency_overrides.pop(get_db, None)


# 4. client (Function-Scoped Fixture - for unauthenticated requests):
@pytest.fixture(name="client")
def client_fixture(db_session): # Depends on db_session to ensure DB is set up
    from backend.main import app # Ensure app is imported
    # This client is for unauthenticated requests or when overrides are managed by other fixtures
    with TestClient(app) as test_client:
        yield test_client
    # General cleanup for any overrides that might have been set if this client was used directly
    # and an override was manually placed. This also ensures auth overrides are cleared if specific
    # auth client fixtures didn't properly clean up their specific override.
    app.dependency_overrides.clear()

# 5. User Fixtures (`test_user`, `test_superuser`):
@pytest.fixture(name="test_user")
def test_user_fixture(db_session): # Depends on db_session
    from backend.core.security import get_password_hash
    
    user = db_session.query(User).filter(User.username == "testuser").first()
    if not user:
        hashed_password = get_password_hash("testpassword")
        user = User(username="testuser", email="test@example.com", hashed_password=hashed_password, is_active=True, is_superuser=False)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture(name="test_superuser")
def test_superuser_fixture(db_session): # Depends on db_session
    from backend.core.security import get_password_hash
    
    superuser = db_session.query(User).filter(User.username == "superuser").first()
    if not superuser:
        hashed_password = get_password_hash("superpassword")
        superuser = User(username="superuser", email="super@example.com", hashed_password=hashed_password, is_active=True, is_superuser=True)
        db_session.add(superuser)
        db_session.commit()
        db_session.refresh(superuser)
    return superuser

# Modified Authenticated Client Fixtures
@pytest.fixture(name="authorized_client")
def authorized_client_fixture(db_session, test_user): # Depends on db_session
    from backend.main import app # Ensure app is imported
    from backend.core import security # Ensure security is imported
    
    app.dependency_overrides[security.get_current_active_user] = lambda: test_user
    with TestClient(app) as c:
        yield c
    # Clear only the specific override after use
    app.dependency_overrides.pop(security.get_current_active_user, None)

@pytest.fixture(name="superuser_client")
def superuser_client_fixture(db_session, test_superuser): # Depends on db_session
    from backend.main import app # Ensure app is imported
    from backend.core import security # Ensure security is imported

    app.dependency_overrides[security.get_current_active_user] = lambda: test_superuser
    with TestClient(app) as c:
        yield c
    # Clear only the specific override after use
    app.dependency_overrides.pop(security.get_current_active_user, None)
