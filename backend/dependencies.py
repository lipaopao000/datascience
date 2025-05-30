from sqlalchemy.orm import Session
from backend.models.database_models import SessionLocal, _test_session_local # Import SessionLocal and _test_session_local

def get_db():
    """Dependency to get DB session."""
    if _test_session_local: # If running in test environment
        db = _test_session_local()
    else: # Production/development environment
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
