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
from backend.models.database_models import Base, engine, get_db, SessionLocal # engine here will be updated later
from backend.crud import crud_system_setting, crud_user # For default settings and user creation
from backend.core import security # For password hashing

# Routers
from backend.routers import (
    user_router, 
    project_router, 
    version_history_router, 
    system_settings_router,
    schema_router, # Keep existing schema_router if still used
    task_router, # Import the new task_router
    experiment_router, # Import the new experiment_router
    model_registry_router # Import the new model_registry_router
)
# Import existing services if they are still needed for non-CRUD operations or specific logic
# For example, if schema_router still depends on schema_service directly
from backend.services.schema_service import SchemaService
from backend.services.data_processor import DataProcessor # If schema_service needs it

# Configure logging (basic setup)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create database tables on startup
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created or already exist.")
        
        # Add default system settings if they don't exist
        db = SessionLocal()
        default_data_path_key = "data_save_path"
        # Use path from settings, ensuring it's a sub-path of STORAGE_BASE_PATH if appropriate
        # For now, let's assume project_data is a subdirectory within STORAGE_BASE_PATH
        default_project_data_path = os.path.join(settings.STORAGE_BASE_PATH, "project_data")
        # Ensure the directory exists
        os.makedirs(default_project_data_path, exist_ok=True)
        default_data_path_value = {"path": default_project_data_path} # Store as JSON
        default_data_path_desc = "Default path for storing project-related data files."
        
        existing_setting = crud_system_setting.get_setting(db, key=default_data_path_key)
        if not existing_setting:
            from backend.models.schemas import SystemSettingCreate as PySystemSettingCreate # Pydantic schema
            setting_create = PySystemSettingCreate(
                key=default_data_path_key, 
                value=default_data_path_value, 
                description=default_data_path_desc
            )
            crud_system_setting.create_setting(db, setting=setting_create)
            logger.info(f"Added default system setting: {default_data_path_key}")

        # Add other default settings as needed (e.g., default admin user, JWT secret if not from env)

    except Exception as e:
        logger.error(f"Error creating database tables or default settings: {e}", exc_info=True)
    finally:
        if db:
            db.close()

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
    logger.info("Application startup: Creating database tables...")
    create_tables()
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
            
            # Create instances
            ss_instance = SchemaService(data_processor_instance=None) # Create SchemaService first
            dp_instance = DataProcessor(schema_service_instance=ss_instance) # Pass SchemaService to DataProcessor
            
            # Now set the circular dependency
            ss_instance.data_processor = dp_instance 
            
            # Assign to the router if the hack is still needed
            schema_router._schema_service_instance = ss_instance
            logger.info("SchemaService and DataProcessor instances configured for schema_router.")
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
# Temporarily allow all origins for debugging CORS issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
    expose_headers=["*"] # Expose all headers
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
app.include_router(task_router.router, prefix=settings.API_V1_STR, tags=["Tasks"]) # Add task router
app.include_router(experiment_router.router, prefix=settings.API_V1_STR, tags=["Experiments"]) # Add experiment router
app.include_router(model_registry_router.router, prefix=settings.API_V1_STR, tags=["Model Registry"]) # Add model registry router

# Health check endpoint (can be outside API_V1_STR or inside, depending on preference)
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.get("/", include_in_schema=False) # Root path redirect or info
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}. Docs at /docs or /redoc."}

# --- Old Endpoints (To be reviewed, refactored into routers, or removed) ---
# The existing endpoints for /api/upload, /api/data, /api/clean, /api/features, /api/ml, /api/visualize
# need to be refactored to align with the new project-based structure and user authentication.
# For now, they are effectively superseded or will need significant updates.
# It's recommended to create new versions of these endpoints within the respective routers (e.g., project_router)
# that are project-aware and use the new versioning system.

# Example of how an old endpoint might be refactored (conceptual)
# This would go into a new router, e.g., `data_management_router.py` under a project
# @project_router.post("/{project_id}/data/upload", ...)
# async def upload_project_data(project_id: int, file: UploadFile, ...):
#     # 1. Check project access (use dependency)
#     # 2. Process upload
#     # 3. Create a version history entry for this data within the project
#     pass

if __name__ == "__main__":
    import uvicorn
    # Ensure Uvicorn reloader works well with this structure if using `python backend/main.py`
    # For production, use `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
    # Consider loading host and port from settings as well for consistency
    uvicorn.run(
        "backend.main:app", 
        host="0.0.0.0", # Or settings.APP_HOST
        port=8000,      # Or settings.APP_PORT
        reload=True     # Or settings.APP_RELOAD
    )
