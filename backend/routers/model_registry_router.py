from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from backend.models import schemas, database_models as models
from backend.services.model_registry_service import ModelRegistryService
from backend.dependencies import get_db
from backend.core.security import get_current_active_user # For securing endpoints

router = APIRouter()

# Dependency to get ModelRegistryService
def get_model_registry_service(db: Session = Depends(get_db)) -> ModelRegistryService:
    return ModelRegistryService(db)

# --- Registered Model Endpoints ---

@router.post("/registered-models/", response_model=schemas.RegisteredModelResponse, status_code=status.HTTP_201_CREATED)
async def create_registered_model_endpoint(
    model_create: schemas.RegisteredModelCreate,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Register a new model.
    """
    # Optional: Check if project_id is valid and user has access
    db_model = model_reg_service.create_registered_model(model_create)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model with this name already exists.")
    return db_model

@router.get("/registered-models/", response_model=List[schemas.RegisteredModelResponse])
async def read_registered_models_endpoint(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a list of registered models. Can filter by project_id.
    """
    models = model_reg_service.get_registered_models(skip=skip, limit=limit, project_id=project_id)
    return models

@router.get("/registered-models/{model_id}", response_model=schemas.RegisteredModelResponse)
async def read_registered_model_endpoint(
    model_id: int,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a single registered model by ID.
    """
    model = model_reg_service.get_registered_model(model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered model not found")
    return model

@router.put("/registered-models/{model_id}", response_model=schemas.RegisteredModelResponse)
async def update_registered_model_endpoint(
    model_id: int,
    model_update: schemas.RegisteredModelUpdate,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a registered model.
    """
    db_model = model_reg_service.update_registered_model(model_id, model_update)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered model not found.")
    return db_model

@router.delete("/registered-models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_registered_model_endpoint(
    model_id: int,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a registered model and all its versions.
    """
    db_model = model_reg_service.delete_registered_model(model_id)
    if not db_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered model not found.")
    return {"message": "Registered model and its versions deleted successfully."}

# --- Model Version Endpoints ---

@router.post("/registered-models/{registered_model_id}/versions/", response_model=schemas.ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_model_version_endpoint(
    registered_model_id: int,
    version_create: schemas.ModelVersionCreate,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new version for a registered model.
    """
    version_create.registered_model_id = registered_model_id
    version_create.user_id = current_user.id # Assign user who registered this version

    db_version = model_reg_service.create_model_version(version_create, user_id=current_user.id)
    if not db_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered model not found or version creation failed.")
    return db_version

@router.get("/registered-models/{registered_model_id}/versions/", response_model=List[schemas.ModelVersionResponse])
async def read_model_versions_endpoint(
    registered_model_id: int,
    skip: int = 0,
    limit: int = 100,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all versions for a specific registered model.
    """
    versions = model_reg_service.get_model_versions_by_registered_model(registered_model_id, skip, limit)
    return versions

@router.get("/model-versions/{version_id}", response_model=schemas.ModelVersionResponse)
async def read_model_version_endpoint(
    version_id: int,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a single model version by ID.
    """
    version = model_reg_service.get_model_version(version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")
    return version

@router.get("/registered-models/{model_name}/versions/latest", response_model=schemas.ModelVersionResponse)
async def read_latest_model_version_by_name_endpoint(
    model_name: str,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve the latest version of a registered model by its name.
    """
    registered_model = crud_model_registry.get_registered_model_by_name(model_reg_service.db, name=model_name)
    if not registered_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registered model not found.")
    
    latest_version = model_reg_service.get_latest_model_version(registered_model.id)
    if latest_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No versions found for this registered model.")
    return latest_version

@router.get("/registered-models/{model_name}/versions/{version_number}", response_model=schemas.ModelVersionResponse)
async def read_specific_model_version_by_name_endpoint(
    model_name: str,
    version_number: int,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a specific version of a registered model by its name and version number.
    """
    version = model_reg_service.get_model_version_by_name_and_version(model_name, version_number)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found.")
    return version

@router.put("/model-versions/{version_id}/stage", response_model=schemas.ModelVersionResponse)
async def transition_model_version_stage_endpoint(
    version_id: int,
    new_stage: str, # e.g., "None", "Staging", "Production", "Archived"
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Transition a model version to a new stage (e.g., "Staging", "Production").
    """
    db_version = model_reg_service.transition_model_version_stage(version_id, new_stage, user_id=current_user.id)
    if not db_version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model version not found or invalid stage.")
    return db_version

@router.delete("/model-versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_version_endpoint(
    version_id: int,
    model_reg_service: ModelRegistryService = Depends(get_model_registry_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a specific model version.
    """
    db_version = model_reg_service.delete_model_version(version_id)
    if not db_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found.")
    return {"message": "Model version deleted successfully."}
