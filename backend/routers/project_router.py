import logging # Added logging
from fastapi import APIRouter, Depends, HTTPException, status, Query 
from sqlalchemy.orm import Session
from typing import List, Annotated, Optional, Dict, Any
import pandas as pd
from backend.models import database_models as models
from backend.models import schemas
from backend.models.schemas import PaginatedResponse
from backend.crud import crud_project, crud_version_history
from backend.core import security
from backend.dependencies import get_db
from backend.services.schema_service import SchemaService
from backend.routers.schema_router import get_schema_service

logger = logging.getLogger(__name__) # Added logger

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(security.get_current_active_user)],
)

@router.post("/", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: schemas.ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    return crud_project.create_project(db=db, project=project, owner_id=current_user.id)

@router.get("/", response_model=List[schemas.ProjectResponse])
def read_projects(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Users can only see their own projects unless they are superusers
    if current_user.is_superuser:
        projects = crud_project.get_all_projects(db, skip=skip, limit=limit)
    else:
        projects = crud_project.get_projects_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def read_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if the user is the owner or a superuser
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
        
    return db_project

@router.put("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
    project_id: int, 
    project_update: schemas.ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")

    updated_project = crud_project.update_project(db, project_id=project_id, project_update=project_update, owner_id=current_user.id) # owner_id passed for consistency, though check is above
    if updated_project is None: # Should not happen if checks above pass
        raise HTTPException(status_code=404, detail="Project not found or update failed")
    return updated_project

@router.delete("/{project_id}", response_model=schemas.ProjectResponse) # Or just status code 204
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")

    # Before deleting, consider related entities like VersionHistory.
    # If VersionHistory has a ForeignKey to Project with ondelete="CASCADE", DB handles it.
    # Otherwise, manual deletion or checks might be needed.
    # For now, assuming cascade or that it's handled by business logic if versions should be kept.

    deleted_project = crud_project.delete_project(db, project_id=project_id, owner_id=current_user.id) # owner_id for consistency
    if deleted_project is None: # Should not happen
        raise HTTPException(status_code=404, detail="Project not found or delete failed")
    return deleted_project # Or return a success message/status

# --- Project Data Management Endpoints ---
from fastapi import UploadFile, File, Form
from backend.services.project_data_service import ProjectDataService # Import the service

# Dependency to get ProjectDataService
def get_project_data_service(db: Session = Depends(get_db), schema_service: SchemaService = Depends(get_schema_service)) -> ProjectDataService:
    return ProjectDataService(db, schema_service_instance=schema_service)

@router.post("/{project_id}/data/upload", response_model=schemas.FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_project_data(
    project_id: int,
    files: List[UploadFile] = File(...), # Changed to List[UploadFile]
    notes: Optional[str] = Form(None),
    data_service: ProjectDataService = Depends(get_project_data_service), # Use the service dependency
    current_user: models.User = Depends(security.get_current_active_user) # Ensures user is active
):
    # Verify project exists and user has access (could be a separate dependency)
    db_project = crud_project.get_project(data_service.db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload data to this project")

    uploaded_versions = []
    for file in files: # Iterate over each uploaded file
        file_content = await file.read()
        
        new_version_entry = data_service.upload_and_version_data(
            project_id=project_id,
            file_content=file_content,
            original_filename=file.filename,
            user_id=current_user.id, # Pass the user ID
            notes=notes
        )
        
        if new_version_entry is None:
            # Handle individual file upload failure, or raise an exception for the whole batch
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file {file.filename} or create new version.")
        uploaded_versions.append(new_version_entry)
        
    # Return a list of VersionHistoryResponse for all uploaded files
    # Or a custom response model that includes a list of these
    # For simplicity, let's return a list of the responses.
    # If the frontend expects a single object, we might need a wrapper schema.
    # For now, let's assume the frontend can handle a list or we'll adjust the response_model.
    # Given the frontend expects `response.files` as an array, this should work.
    return {"message": f"Successfully uploaded {len(uploaded_versions)} files.", "files": uploaded_versions}

@router.get("/{project_id}/data/{data_entity_id}/versions/{version_number}/view", response_model=schemas.GenericDataResponse)
async def view_project_data_version(
    project_id: int,
    data_entity_id: str,
    version_number: int,
    page: int = Query(1, ge=1), 
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    logger.info(f"Attempting to view data version: project_id={project_id}, entity_id={data_entity_id}, version_number={version_number}")

    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        logger.warning(f"Project {project_id} not found for data view request.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        logger.warning(f"User {current_user.id} not authorized to access project {project_id} for data view.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this project's data")

    data_service = ProjectDataService(db=db)
    df = data_service.load_data_from_version(
        project_id=project_id,
        entity_id=data_entity_id,
        version_number=version_number
    )

    if df is None:
        logger.warning(f"Data for project {project_id}, entity {data_entity_id}, version {version_number} not found or failed to load by service.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data for the specified version not found or failed to load.")

    # Paginate data for preview
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    data_sample = df.iloc[start_idx:end_idx].to_dict(orient='records')
    
    # Basic summary (can be expanded)
    summary_stats = df.describe(include='all').to_dict()
    # Convert NaN to None for JSON compatibility in summary
    for col_summary in summary_stats.values():
        for k, v in col_summary.items():
            if pd.isna(v):
                col_summary[k] = None
                
    logger.info(f"Successfully loaded and prepared preview for project {project_id}, entity {data_entity_id}, version {version_number}. Shape: {df.shape}")
    return schemas.GenericDataResponse(
        data_id=f"{data_entity_id}_v{version_number}", # Composite ID for response
        columns=df.columns.tolist(),
        data=data_sample,
        shape=list(df.shape),
        summary=summary_stats,
        records=len(df)
    )

@router.post("/{project_id}/data/{data_entity_id}/versions/{version_number}/clean", response_model=schemas.VersionHistoryResponse)
async def clean_project_data_version(
    project_id: int,
    data_entity_id: str,
    version_number: int,
    cleaning_request: schemas.DataCleaningRequest, # Request body with config and notes
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to clean data in this project")

    data_service = ProjectDataService(db=db)
    
    new_version_entry = data_service.clean_and_version_data(
        project_id=project_id,
        data_entity_id=data_entity_id,
        source_version_number=version_number,
        cleaning_config=cleaning_request.cleaning_config,
        notes=cleaning_request.notes
    )

    if new_version_entry is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clean data or create new version.")
        
    return new_version_entry

@router.post("/{project_id}/features/extract", response_model=schemas.VersionHistoryResponse)
async def extract_project_features(
    project_id: int,
    feature_request: schemas.ProjectFeatureExtractionRequest, # Request body
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to extract features in this project")

    data_service = ProjectDataService(db=db)
    
    new_features_version_entry = data_service.extract_and_version_features(
        project_id=project_id,
        source_data_entity_id=feature_request.source_data_entity_id,
        source_data_version=feature_request.source_data_version,
        feature_config=feature_request.feature_config,
        notes=feature_request.notes
    )

    if new_features_version_entry is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to extract features or create new version.")
        
    return new_features_version_entry

from backend.services.project_model_service import ProjectModelService

@router.post("/{project_id}/models/train", response_model=schemas.VersionHistoryResponse)
async def train_project_model(
    project_id: int,
    train_request: schemas.ProjectModelTrainRequest, # Request body
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to train models in this project")

    model_service = ProjectModelService(db=db)
    
    new_model_version_entry = model_service.train_and_version_model(
        project_id=project_id,
        train_request=train_request
    )

    if new_model_version_entry is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to train model or create new version.")
        
    return new_model_version_entry

@router.post("/{project_id}/models/predict", response_model=Dict[str, Any]) # Adjust response_model as needed
async def predict_with_project_model(
    project_id: int,
    predict_request: schemas.ProjectModelPredictRequest, # Request body
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use models in this project")

    model_service = ProjectModelService(db=db)
    
    try:
        predictions = model_service.predict_with_versioned_model(
            project_id=project_id,
            predict_request=predict_request
        )
    except ValueError as ve: # Catch specific ValueErrors from service (e.g. feature mismatch)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    
    if predictions is None:
        # This could be due to model not found, file error, or other issues in service
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to make prediction.")
        
    return {
        "project_id": project_id,
        "model_entity_id": predict_request.model_entity_id,
        "model_version": predict_request.model_version,
        "input_features": predict_request.input_features,
        "predictions": predictions 
    }

# --- ML Pipeline Orchestration Endpoint ---
from backend.tasks import run_ml_pipeline # Import the pipeline task

class MLPipelineRunRequest(schemas.BaseModel):
    data_entity_id: str
    source_data_version: int
    cleaning_config: Dict[str, Any] = {}
    feature_config: Dict[str, Any] = {}
    train_request: schemas.ProjectModelTrainRequest # Use the existing training request schema

@router.post("/{project_id}/pipeline/run", response_model=schemas.TaskStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_ml_pipeline_endpoint(
    project_id: int,
    pipeline_request: MLPipelineRunRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Triggers a full ML pipeline (clean -> feature extract -> train) as an asynchronous task.
    """
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to run pipelines in this project")

    # Convert Pydantic models to dictionaries for Celery task parameters
    # This is important because Celery tasks should ideally receive JSON-serializable data
    # and reconstruct Pydantic models inside the task if needed.
    cleaning_config_dict = pipeline_request.cleaning_config
    feature_config_dict = pipeline_request.feature_config
    train_request_dict = pipeline_request.train_request.model_dump() # Convert to dict

    task = run_ml_pipeline.delay(
        project_id=project_id,
        data_entity_id=pipeline_request.data_entity_id,
        source_data_version=pipeline_request.source_data_version,
        cleaning_config=cleaning_config_dict,
        feature_config=feature_config_dict,
        train_request_dict=train_request_dict,
        user_id=current_user.id # Pass user_id to the task
    )
    
    return {"task_id": task.id, "status": "PENDING", "message": "ML pipeline task has been submitted."}


@router.post("/{project_id}/data/{data_entity_id}/versions/{source_version_number}/rollback", response_model=schemas.VersionHistoryResponse)
async def rollback_project_data_version(
    project_id: int,
    data_entity_id: str,
    source_version_number: int,
    request_body: Optional[schemas.RollbackRequest] = None, # Use schema from schemas.py
    data_service: ProjectDataService = Depends(get_project_data_service), # Use the service dependency
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to rollback data in this project")

    rollback_notes = request_body.notes if request_body else f"Rolled back to version {source_version_number}"
    
    new_version_entry = data_service.rollback_to_version(
        project_id=project_id,
        data_entity_id=data_entity_id,
        source_version_number=source_version_number,
        notes=rollback_notes
    )

    if new_version_entry is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to rollback data version.")
        
    return new_version_entry

@router.post("/{project_id}/data/delete-batch", response_model=Dict[str, bool]) # Response model changed to reflect success/failure per entity
async def batch_delete_project_data_entities( # Renamed function for clarity
    project_id: int,
    delete_request: schemas.ProjectDataDeleteRequest, # Request body with data_ids
    data_service: ProjectDataService = Depends(get_project_data_service), # Use the service dependency
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(data_service.db, project_id=project_id) # Use data_service.db
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete data in this project")

    results = data_service.batch_delete_data_entities(
        project_id=project_id,
        entity_ids=delete_request.data_ids # Use entity_ids as per service method
    )

    # Check if all deletions failed
    if not any(results.values()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data entities found for deletion or all deletions failed.")
        
    return results # Return the dictionary of results

@router.post("/{project_id}/data/format", response_model=List[schemas.VersionHistoryResponse]) # Changed response_model
async def format_project_data(
    project_id: int,
    format_request: schemas.ProjectDataFormatRequest, # Request body
    data_service: ProjectDataService = Depends(get_project_data_service), # Use the service dependency
    current_user: models.User = Depends(security.get_current_active_user)
):
    # Verify project exists and user has access
    db_project = crud_project.get_project(data_service.db, project_id=project_id) # Use data_service.db
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to format data in this project")

    # Call the refactored service function
    formatted_versions, errors = data_service.format_and_version_data(
        project_id=project_id,
        data_ids=format_request.data_ids,
        convert_to_headered=format_request.convert_to_headered,
        schema_id=format_request.schema_id,
        data_specific_value_columns=format_request.data_specific_value_columns,
        notes=format_request.notes
    )

    if errors:
        # If there are any errors, return a 400 Bad Request with details
        # This is more informative than a generic 500
        error_detail = "Data formatting failed for one or more entities. Details: " + "; ".join(errors)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    
    if not formatted_versions:
        # This case should ideally be covered by 'errors' check, but as a fallback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to format any data or create new versions without specific errors reported.")
        
    return formatted_versions # Return the list of responses

# --- Project Version History Endpoint ---
from backend.crud import crud_version_history # Already imported if other version endpoints exist, ensure it is
# from typing import List # Already imported if other list responses exist, ensure it is
# from backend.models import schemas # Already imported, ensure VersionHistoryResponse is available

@router.get("/{project_id}/versions", response_model=PaginatedResponse[schemas.VersionHistoryResponse])
def list_project_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project's versions")
    
    versions = crud_version_history.get_versions_by_project_id(db, project_id=project_id, skip=skip, limit=limit)
    total_versions = crud_version_history.get_versions_count_by_project_id(db, project_id=project_id)
    return PaginatedResponse(items=versions, total=total_versions)

@router.get("/{project_id}/data/{data_entity_id}/versions", response_model=List[schemas.VersionHistoryResponse])
def list_entity_versions_for_project(
    project_id: int,
    data_entity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project's data versions")
    
    versions = crud_version_history.get_versions_for_entity(
        db, 
        project_id=project_id, 
        entity_type="data", # Assuming "data" for now, can be made dynamic if needed
        entity_id=data_entity_id,
        skip=0, # Fetch all for rollback dialog
        limit=1000 # Fetch a large enough limit for now, or or remove limit for all
    )
    return versions

@router.patch("/{project_id}/versions/{version_id}/notes", response_model=schemas.VersionHistoryResponse)
def update_version_notes(
    project_id: int,
    version_id: int,
    notes_update: schemas.VersionHistoryUpdateNotes, # Define this schema in schemas.py
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this project's versions")
    
    updated_version = crud_version_history.update_version_notes(db, version_id=version_id, notes=notes_update.notes)
    if not updated_version:
        raise HTTPException(status_code=404, detail="Version history entry not found")
    return updated_version

@router.patch("/{project_id}/versions/{version_id}/display_name", response_model=schemas.VersionHistoryResponse) # Changed to PATCH and display_name
def update_version_display_name(
    project_id: int,
    version_id: int,
    display_name_update: schemas.VersionHistoryUpdateDisplayName, # Define this schema in schemas.py
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this project's versions")
    
    updated_version = crud_version_history.update_version_display_name(db, version_id=version_id, display_name=display_name_update.display_name)
    if not updated_version:
        raise HTTPException(status_code=404, detail="Version history entry not found")
    return updated_version

@router.get("/{project_id}/data/test-delete-batch", response_model=Dict[str, str])
async def test_delete_batch_endpoint(
    project_id: int,
    current_user: models.User = Depends(security.get_current_active_user)
):
    # This is a temporary endpoint for testing routing
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this project")
    return {"message": f"Test endpoint for project {project_id} is reachable."}
