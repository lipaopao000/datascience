from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataScience Project Management"
    API_V1_STR: str = "/api/v1"
    # This default is for local development only if .env is not present.
    # It MUST be overridden by a strong, random key in .env or environment variables for production.
    SECRET_KEY: str = "super_secret_development_key_do_not_use_in_production"
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./datascience_project_management.db"
    # Use in-memory SQLite for tests for speed and to avoid file permission issues
    TEST_SQLALCHEMY_DATABASE_URL: str = "sqlite:///:memory:" 

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[AnyHttpUrl], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Celery (example, adjust as needed)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Storage (example, adjust based on storage_utils.py)
    STORAGE_BASE_PATH: str = "backend/data" # Default base path for local storage
    # If using cloud storage, add relevant configs here e.g.
    # S3_BUCKET_NAME: Optional[str] = None
    # AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
