import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.config import settings
from backend.models.database_models import Base, SessionLocal
from backend.services.project_data_service import ProjectDataService
from backend.crud import crud_version_history, crud_system_setting
from backend.core.storage_utils import get_versioned_data_path # Import the utility function

# Configure logging for this script
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("backend").setLevel(logging.DEBUG)
logging.getLogger("backend.services.project_data_service").setLevel(logging.DEBUG)
logging.getLogger("backend.crud.crud_version_history").setLevel(logging.DEBUG)
logging.getLogger("backend.core.storage_utils").setLevel(logging.DEBUG) # Add logging for storage_utils

def debug_load_data():
    db = SessionLocal()
    try:
        project_id = 1
        data_entity_id = "dc8b10a6-13d6-4b18-84f4-dc449ad75539"
        version_number = 1

        logger.info(f"Attempting to debug load for project_id={project_id}, entity_id={data_entity_id}, version_number={version_number}")

        data_service = ProjectDataService(db=db)
        
        # First, try to get the version entry directly
        version_entry = crud_version_history.get_specific_version(
            db,
            project_id=project_id,
            entity_type="data",
            entity_id=data_entity_id,
            version=version_number
        )

        if not version_entry:
            logger.error(f"Version entry not found in DB for project {project_id}, entity {data_entity_id}, version {version_number}.")
            # Try to list all versions for this entity to see what's available
            all_versions = crud_version_history.get_versions_for_entity(db, project_id, "data", data_entity_id)
            if all_versions:
                logger.info(f"Found existing versions for entity {data_entity_id}: {[v.version for v in all_versions]}")
            else:
                logger.info(f"No versions found for entity {data_entity_id} in project {project_id}.")
            return

        logger.info(f"Found version entry in DB: {version_entry.file_identifier}, created_at={version_entry.created_at}")

        # Use the official utility function to get the expected file path
        expected_file_path = get_versioned_data_path(
            db,
            project_id=project_id,
            entity_type="data",
            entity_id=data_entity_id,
            version=version_number,
            filename=version_entry.file_identifier
        )
        logger.info(f"Expected file path (using get_versioned_data_path): {expected_file_path}")

        if not os.path.exists(expected_file_path):
            logger.error(f"File DOES NOT EXIST at expected path: {expected_file_path}")
            # List directory contents to help diagnose
            version_dir = os.path.dirname(expected_file_path)
            if os.path.exists(version_dir):
                logger.info(f"Contents of directory {version_dir}: {os.listdir(version_dir)}")
            else:
                logger.error(f"Version directory DOES NOT EXIST: {version_dir}")
            return

        logger.info(f"File EXISTS at expected path: {expected_file_path}")

        df = data_service.load_data_from_version(
            project_id=project_id,
            entity_id=data_entity_id,
            version_number=version_number
        )

        if df is None:
            logger.error("DataFrame is None after calling load_data_from_version. Check service logs for details.")
        else:
            logger.info(f"Successfully loaded DataFrame. Shape: {df.shape}")
            logger.info(f"First 5 rows:\n{df.head()}")

    except Exception as e:
        logger.error(f"An unexpected error occurred during debug_load_data: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    debug_load_data()
