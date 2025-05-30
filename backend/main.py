import sys # Add sys import
import os
# Add the project root to sys.path to allow running main.py directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager # Import asynccontextmanager

# Import settings
from backend.core.config import settings

# Database related imports
from backend.models.database_models import Base, engine, SessionLocal # Removed get_db
from backend.dependencies import get_db # Import get_db from dependencies
from backend.crud import crud_system_setting, crud_user
from backend.core import security

# Routers
from backend.routers import (
    user_router, 
    project_router, 
    version_history_router, 
    system_settings_router,
    schema_router,
    task_router,
    experiment_router,
    model_registry_router
)
# Import existing services if they are still needed for non-CRUD operations or specific logic
# For example, if schema_router still depends on schema_service directly
from backend.services.schema_service import SchemaService
from backend.services.data_processor import DataProcessor # If schema_service needs it

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Set logging level for uvicorn and backend modules
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("backend").setLevel(logging.INFO) # Set overall backend logging to INFO
logging.getLogger("backend.routers.project_router").setLevel(logging.INFO) # Explicitly set for project router
logging.getLogger("backend.services.project_data_service").setLevel(logging.INFO) # Explicitly set for data service

def create_default_superuser():
    db = SessionLocal()
    try:
        from backend.models import schemas # Local import to ensure scope
        # Check if any user exists
        if crud_user.get_users(db, skip=0, limit=1):
            logger.info("Users already exist. Skipping default superuser creation.")
            return

        # Create a default superuser if no users exist
        default_username = settings.FIRST_SUPERUSER_USERNAME
        default_password = settings.FIRST_SUPERUSER_PASSWORD
        default_email = settings.FIRST_SUPERUSER_EMAIL

        if not default_username or not default_password:
            logger.warning("Default superuser username or password not set in environment variables. Skipping default superuser creation.")
            return

        user_in = schemas.UserCreate(
            username=default_username,
            email=default_email,
            password=default_password,
            is_superuser=True,
            is_active=True
        )
        crud_user.create_user(db, user=user_in)
        logger.info(f"Default superuser '{default_username}' created successfully.")
    except Exception as e:
        logger.error(f"Error creating default superuser: {e}", exc_info=True)
    finally:
        if db:
            db.close()

# Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # In a production environment, database migrations should be handled externally (e.g., via Alembic CLI)
    # This ensures that the database schema is managed consistently and avoids conflicts with migrations.
    # For development, you might uncomment create_tables() if you're not using Alembic or need quick setup.
    # logger.info("Application startup: Creating database tables...")
    # create_tables() 
    logger.info("Application startup: Creating default superuser if none exists...")
    create_default_superuser()
    # Initialize any other services or configurations needed at startup
    # For schema_router, if it still needs direct service injection:
    if hasattr(schema_router, '_schema_service_instance'):
        # This is a bit of a hack due to the existing structure.
        # Ideally, dependencies are handled via FastAPI's Depends.
        temp_db_for_service = SessionLocal()
        try:
            # Instantiate services correctly based on their constructors
            # SchemaService(data_processor_instance)
            # DataProcessor(schema_service_instance=None)
            
            # Create instances of services that might have interdependencies
            # Initialize SchemaService and DataProcessor
            ss_instance = SchemaService(data_processor_instance=None) # DataProcessor instance will be set later
            dp_instance = DataProcessor(schema_service_instance=ss_instance) # Pass SchemaService to DataProcessor
            
            # Set circular dependency for SchemaService
            ss_instance.data_processor = dp_instance 
            
            # Initialize ProjectDataService with SchemaService
            from backend.services.project_data_service import ProjectDataService # Import here to avoid circular import at top level
            global project_data_service_instance # Declare global to make it accessible outside lifespan
            project_data_service_instance = ProjectDataService(db=None, schema_service_instance=ss_instance) # DB session will be injected per request
            
            # Assign instances to routers if they use global instances (less ideal, but matches existing pattern)
            # For schema_router, if it still uses _schema_service_instance directly:
            if hasattr(schema_router, '_schema_service_instance'):
                schema_router._schema_service_instance = ss_instance
            
            # For project_data_router, if it needs a global instance for its dependencies:
            # This is handled by FastAPI's Depends(get_project_data_service) which creates it per request.
            # No global assignment needed for project_data_router's dependencies.
            
            logger.info("Services (SchemaService, DataProcessor, ProjectDataService) initialized.")
        except Exception as e_service_init:
            logger.error(f"Error initializing services for schema_router: {e_service_init}", exc_info=True)
        finally:
            # temp_db_for_service is not used for these instantiations anymore
            pass
    yield # Application starts serving requests
    # Cleanup logic can go here if needed for shutdown
    logger.info("Application shutdown.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0", # Or move to settings: settings.APP_VERSION
    description="API for managing data science projects, users, data versions, and system settings.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json", # Standardize openapi url
    lifespan=lifespan, # Pass the lifespan context manager
    redirect_slashes=False # Disable automatic trailing slash redirects
)

# CORS Middleware
# CORS Middleware - Temporarily allow all origins for debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for debugging CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
# Original logic (commented out for debugging)
# if settings.BACKEND_CORS_ORIGINS:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
# else: # Default to allow all if not specified, for local development ease
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["*"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )


# Include new routers with API_V1_STR prefix
app.include_router(user_router.router, prefix=settings.API_V1_STR, tags=["Users"])
app.include_router(project_router.router, prefix=settings.API_V1_STR, tags=["Projects"])
app.include_router(version_history_router.router, prefix=settings.API_V1_STR, tags=["Version History"])
app.include_router(system_settings_router.router, prefix=settings.API_V1_STR, tags=["System Settings"])

# Include existing schema_router (if it's still being used and adapted)
# Ensure its dependencies are correctly handled (e.g., via Depends or updated injection)
# Standardize prefix for schema_router as well
app.include_router(schema_router.router, prefix=settings.API_V1_STR, tags=["Schemas"])
app.include_router(task_router.router, prefix=settings.API_V1_STR, tags=["Tasks"])
app.include_router(experiment_router.router, prefix=settings.API_V1_STR, tags=["Experiments"])
app.include_router(model_registry_router.router, prefix=settings.API_V1_STR, tags=["Model Registry"])

# Health check endpoint
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Docs at /docs or /redoc."}

# Removed old data-related endpoints as they are now handled by project_data_router
# or are no longer relevant in the new project-centric architecture.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app", 
        host="0.0.0.0",
        port=8000,
        reload=True
    )
