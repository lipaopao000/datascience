import logging
from sqlalchemy.orm import Session
from typing import Optional, List, Any, Dict

from backend.models import database_models as models
from backend.models import schemas

# Set up logger
logger = logging.getLogger(__name__)

def get_version_history_entry(db: Session, version_id: int) -> Optional[models.VersionHistory]:
    return db.query(models.VersionHistory).filter(models.VersionHistory.id == version_id).first()

def get_versions_for_entity(
    db: Session, 
    project_id: int, 
    entity_type: str, 
    entity_id: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.VersionHistory]:
    """
    Get all versions for a specific entity (e.g., a dataset or model) within a project, ordered by version descending.
    """
    return (
        db.query(models.VersionHistory)
        .filter(
            models.VersionHistory.project_id == project_id,
            models.VersionHistory.entity_type == entity_type,
            models.VersionHistory.entity_id == entity_id,
        )
        .order_by(models.VersionHistory.version.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_version_notes(db: Session, version_id: int, notes: Optional[str]) -> Optional[models.VersionHistory]:
    """
    Update the notes for a specific version history entry.
    """
    db_version = db.query(models.VersionHistory).filter(models.VersionHistory.id == version_id).first()
    if db_version:
        db_version.notes = notes
        db.commit()
        db.refresh(db_version)
    return db_version

def update_version_display_name(db: Session, version_id: int, display_name: Optional[str]) -> Optional[models.VersionHistory]:
    """
    Update the display name for a specific version history entry.
    """
    db_version = db.query(models.VersionHistory).filter(models.VersionHistory.id == version_id).first()
    if db_version:
        db_version.display_name = display_name
        db.commit()
        db.refresh(db_version)
    return db_version

def get_versions_count_by_project_id(db: Session, project_id: int) -> int:
    """
    Get the total count of versions for a specific project.
    """
    return db.query(models.VersionHistory).filter(models.VersionHistory.project_id == project_id).count()

def get_latest_version_for_entity(
    db: Session, 
    project_id: int, 
    entity_type: str, 
    entity_id: str
) -> Optional[models.VersionHistory]:
    """
    Get the latest version for a specific entity within a project.
    """
    return (
        db.query(models.VersionHistory)
        .filter(
            models.VersionHistory.project_id == project_id,
            models.VersionHistory.entity_type == entity_type,
            models.VersionHistory.entity_id == entity_id,
        )
        .order_by(models.VersionHistory.version.desc())
        .first()
    )

def create_version_history(
    db: Session,
    project_id: int,
    version_create_data: schemas.VersionHistoryCreate # Use the Pydantic model
    # user_id: Optional[int] = None # If tracking which user created the version
) -> models.VersionHistory:
    """
    Creates a new version for an entity. It automatically increments the version number.
    """
    latest_version_entry = get_latest_version_for_entity(
        db, 
        project_id, 
        version_create_data.entity_type, 
        version_create_data.entity_id
    )
    
    current_version_number = 0
    if latest_version_entry:
        current_version_number = latest_version_entry.version
        
    new_version_number = current_version_number + 1
    
    db_version = models.VersionHistory(
        project_id=project_id,
        entity_type=version_create_data.entity_type,
        entity_id=version_create_data.entity_id,
        version=new_version_number,
        version_metadata=version_create_data.version_metadata,
        file_identifier=version_create_data.file_identifier,
        notes=version_create_data.notes,
        display_name=version_create_data.display_name, # Added display_name
        # user_id=user_id 
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def get_specific_version(
    db: Session,
    project_id: int,
    entity_type: str,
    entity_id: str,
    version: int
) -> Optional[models.VersionHistory]:
    """
    Retrieves a specific version of an entity.
    """
    return (
        db.query(models.VersionHistory)
        .filter(
            models.VersionHistory.project_id == project_id,
            models.VersionHistory.entity_type == entity_type,
            models.VersionHistory.entity_id == entity_id,
            models.VersionHistory.version == version,
        )
        .first()
    )

# Deleting version history entries is generally not recommended for auditability.
# If needed, it should be a privileged operation.
# def delete_version_history(db: Session, version_id: int) -> Optional[models.VersionHistory]:
#     db_version = get_version_history_entry(db, version_id)
#     if db_version:
#         db.delete(db_version)
#         db.commit()
#     return db_version

def get_versions_by_project_id(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[models.VersionHistory]:
    """
    Get all versions for a specific project, ordered by creation date descending.
    """
    return (
        db.query(models.VersionHistory)
        .filter(models.VersionHistory.project_id == project_id)
        .order_by(models.VersionHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_versions_for_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[models.VersionHistory]:
    """Alias for get_versions_by_project_id for API consistency"""
    return get_versions_by_project_id(db, project_id, skip, limit)
