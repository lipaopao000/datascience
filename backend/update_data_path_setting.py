import os
import sys
from sqlalchemy.orm import Session
import logging

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.database_models import SessionLocal
from backend.crud import crud_system_setting
from backend.models import schemas # Import schemas for SystemSettingUpdate and SystemSettingCreate

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_data_save_path_setting():
    db: Session = SessionLocal()
    try:
        new_path_value = {"path": "backend/data/project_data"} # The correct base path

        # Check if the setting exists
        existing_setting = crud_system_setting.get_setting(db, key="data_save_path")

        if existing_setting:
            # Update existing setting
            setting_update = schemas.SystemSettingUpdate(value=new_path_value, description="Base path for project data storage")
            updated_setting = crud_system_setting.update_setting(db, key="data_save_path", setting_update=setting_update)
            if updated_setting:
                logger.info(f"Successfully updated 'data_save_path' to: {updated_setting.value['path']}")
            else:
                logger.error("Failed to update 'data_save_path' setting.")
        else:
            # Create new setting if it doesn't exist
            setting_create = schemas.SystemSettingCreate(
                key="data_save_path",
                value=new_path_value,
                description="Base path for project data storage"
            )
            created_setting = crud_system_setting.create_setting(db, setting=setting_create)
            if created_setting:
                logger.info(f"Successfully created 'data_save_path' with value: {created_setting.value['path']}")
            else:
                logger.error("Failed to create 'data_save_path' setting.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    update_data_save_path_setting()
