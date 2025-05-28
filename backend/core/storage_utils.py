import os
from pathlib import Path
from sqlalchemy.orm import Session
from backend.crud import crud_system_setting
# Removed crud_project and Project as they are not used in this file after refactor
from backend.core.config import settings # Import settings

def get_project_data_save_path(db: Session, project_id: int) -> Path:
    """
    Determines the data storage path for a given project.
    It primarily uses the system-wide 'data_save_path' setting from the database.
    The fallback default for this setting is derived from settings.STORAGE_BASE_PATH.
    """
    # Construct the default path using settings.STORAGE_BASE_PATH
    # This default is used if the "data_save_path" key is not found in system settings.
    default_project_data_dir = os.path.join(settings.STORAGE_BASE_PATH, "project_data")
    fallback_default_setting_value = {"path": default_project_data_dir}

    base_path_setting = crud_system_setting.get_setting_value(
        db, 
        "data_save_path", 
        fallback_default_setting_value
    )
    
    # The value from DB (or fallback) should be a dict like {"path": "/actual/path"}
    base_storage_path_str = base_path_setting.get("path", default_project_data_dir)
    base_path = Path(base_storage_path_str)
    
    project_path = base_path / f"project_{project_id}"
    os.makedirs(project_path, exist_ok=True)
    return project_path

def get_versioned_data_path(
    db: Session, 
    project_id: int, 
    entity_type: str, # e.g., "data", "models", "features"
    entity_id: str,   # Unique ID for the data entity (e.g., a dataset UUID)
    version: int,
    filename: str      # Original or desired filename for this version (e.g., "raw_ecg.csv", "trained_model.pkl")
) -> Path:
    """
    Constructs a versioned file path for a data entity within a project.
    Example: /base_path/project_123/data/entity_abc/v1/raw_ecg.csv
    """
    project_base_path = get_project_data_save_path(db, project_id)
    
    # Sanitize entity_id and filename to be safe for path components
    safe_entity_id = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in entity_id)
    safe_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in filename)

    versioned_path = project_base_path / entity_type / safe_entity_id / f"v{version}"
    os.makedirs(versioned_path, exist_ok=True)
    
    return versioned_path / safe_filename

def get_entity_base_path(
    db: Session,
    project_id: int,
    entity_type: str,
    entity_id: str
) -> Path:
    """
    Gets the base path for a specific entity, where all its versions would be stored.
    Example: /base_path/project_123/data/entity_abc/
    """
    project_base_path = get_project_data_save_path(db, project_id)
    safe_entity_id = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in entity_id)
    entity_path = project_base_path / entity_type / safe_entity_id
    os.makedirs(entity_path, exist_ok=True)
    return entity_path
