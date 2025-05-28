from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Annotated

from backend.models import database_models as models
from backend.models import schemas
from backend.crud import crud_version_history, crud_project
from backend.core import security
from backend.models.database_models import get_db

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/versions", # Nested under projects
    tags=["version-history"],
    dependencies=[Depends(security.get_current_active_user)],
)

# Helper dependency to check project access
async def get_project_and_check_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
) -> models.Project:
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project's versions")
    return db_project

@router.post("/{entity_type}/{entity_id}", response_model=schemas.VersionHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_version(
    project_id: int, # Comes from path
    entity_type: str, # Comes from path, e.g., "data", "model"
    entity_id: str,   # Comes from path, specific ID of the data/model
    version_create_payload: schemas.VersionHistoryCreate, # Request body
    db: Session = Depends(get_db),
    project: models.Project = Depends(get_project_and_check_access) # Ensures project exists and user has access
):
    # Ensure the payload's entity_type and entity_id match the path parameters
    if version_create_payload.entity_type != entity_type or version_create_payload.entity_id != entity_id:
        raise HTTPException(status_code=400, detail="Entity type or ID in request body does not match path parameters.")

    # The version number is auto-incremented by the CRUD function
    new_version = crud_version_history.create_version_history(
        db=db,
        project_id=project.id, # Use ID from validated project object
        version_create_data=version_create_payload
        # user_id=current_user.id # If tracking user, get current_user from Depends
    )
    return new_version

@router.get("/{entity_type}/{entity_id}", response_model=List[schemas.VersionHistoryResponse])
def read_versions_for_entity(
    project_id: int,
    entity_type: str,
    entity_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    project: models.Project = Depends(get_project_and_check_access)
):
    versions = crud_version_history.get_versions_for_entity(
        db, project_id=project.id, entity_type=entity_type, entity_id=entity_id, skip=skip, limit=limit
    )
    return versions

@router.get("/{entity_type}/{entity_id}/latest", response_model=schemas.VersionHistoryResponse)
def read_latest_version_for_entity(
    project_id: int,
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
    project: models.Project = Depends(get_project_and_check_access)
):
    latest_version = crud_version_history.get_latest_version_for_entity(
        db, project_id=project.id, entity_type=entity_type, entity_id=entity_id
    )
    if not latest_version:
        raise HTTPException(status_code=404, detail=f"No versions found for {entity_type} with id {entity_id} in this project.")
    return latest_version

@router.get("/{entity_type}/{entity_id}/{version_number}", response_model=schemas.VersionHistoryResponse)
def read_specific_version(
    project_id: int,
    entity_type: str,
    entity_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    project: models.Project = Depends(get_project_and_check_access)
):
    specific_version = crud_version_history.get_specific_version(
        db, project_id=project.id, entity_type=entity_type, entity_id=entity_id, version=version_number
    )
    if not specific_version:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found for {entity_type} with id {entity_id} in this project.")
    return specific_version

# To "revert" or "load" a previous version, the client would typically:
# 1. Fetch the `data_snapshot` from a specific `VersionHistoryResponse`.
# 2. Use that `data_snapshot` to update the current state of their application or data.
# Optionally, a new version could be created that is a copy of an older version's snapshot.

from fastapi.responses import FileResponse, JSONResponse
from backend.core.storage_utils import get_versioned_data_path
import os

@router.get("/{entity_type}/{entity_id}/{version_number}/download", response_class=FileResponse)
async def download_versioned_file(
    project_id: int,
    entity_type: str,
    entity_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    project: models.Project = Depends(get_project_and_check_access) # Ensures project access
):
    version_entry = crud_version_history.get_specific_version(
        db, project_id=project.id, entity_type=entity_type, entity_id=entity_id, version=version_number
    )

    if not version_entry:
        raise HTTPException(status_code=404, detail="Version entry not found.")

    if not version_entry.file_identifier:
        # If there's no file identifier, but there is metadata, return metadata.
        # Or, if the expectation is always a file, raise an error.
        if version_entry.version_metadata:
             # Returning JSONResponse instead of FileResponse if no file
            return JSONResponse(
                status_code=200, # Or 202 if it's just metadata and not the "download"
                content={
                    "message": "No direct file download for this version. Returning metadata.",
                    "version_metadata": version_entry.version_metadata,
                    "file_identifier": None
                }
            )
        raise HTTPException(status_code=404, detail="No file associated with this version entry.")

    file_path = get_versioned_data_path(
        db,
        project_id=project.id,
        entity_type=version_entry.entity_type, # Use type from entry for safety
        entity_id=version_entry.entity_id,   # Use ID from entry
        version=version_entry.version,
        filename=version_entry.file_identifier
    )

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"File not found at path: {file_path}. The version entry might be inconsistent.")

    # Use the original filename for download if available in metadata, else the file_identifier
    download_filename = version_entry.file_identifier
    if version_entry.version_metadata and "original_filename" in version_entry.version_metadata:
        download_filename = version_entry.version_metadata["original_filename"]
    
    return FileResponse(path=file_path, filename=download_filename, media_type='application/octet-stream')
