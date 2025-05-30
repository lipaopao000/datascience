from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os

from backend.models import schemas, database_models as models
from backend.crud import crud_experiment
from backend.services.experiment_service import ExperimentService
from backend.dependencies import get_db
from backend.core.security import get_current_active_user # For securing endpoints
from backend.core.config import settings # For artifact storage path

router = APIRouter()

# Dependency to get ExperimentService
def get_experiment_service(db: Session = Depends(get_db)) -> ExperimentService:
    return ExperimentService(db)

# --- Experiment Endpoints ---

@router.post("/experiments/", response_model=schemas.ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment_endpoint(
    experiment_create: schemas.ExperimentCreate,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new experiment.
    """
    # Ensure the project exists and current_user has access if project_id is provided
    if experiment_create.project_id:
        # This would require a crud_project import and check
        # For now, assuming project_id is valid or optional
        pass

    db_experiment = exp_service.create_experiment(experiment_create)
    if not db_experiment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment with this name already exists.")
    return db_experiment

@router.get("/experiments/", response_model=List[schemas.ExperimentResponse])
async def read_experiments_endpoint(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a list of experiments. Can filter by project_id.
    """
    experiments = exp_service.get_experiments(skip=skip, limit=limit, project_id=project_id)
    return experiments

@router.get("/experiments/{experiment_id}", response_model=schemas.ExperimentResponse)
async def read_experiment_endpoint(
    experiment_id: int,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a single experiment by ID.
    """
    experiment = exp_service.get_experiment(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiment

# --- Run Endpoints ---

@router.post("/experiments/{experiment_id}/runs/", response_model=schemas.RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run_endpoint(
    experiment_id: int,
    run_create: schemas.RunCreate, # Use RunCreate for request body
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Start a new run within an experiment.
    """
    # Override experiment_id from path
    run_create.experiment_id = experiment_id
    run_create.user_id = current_user.id # Associate run with current user

    db_run = exp_service.start_run(
        experiment_id=run_create.experiment_id,
        run_name=run_create.run_name,
        user_id=run_create.user_id,
        source_type=run_create.source_type,
        source_name=run_create.source_name,
        git_commit=run_create.git_commit
    )
    if not db_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found or run creation failed.")
    return db_run

@router.put("/runs/{run_id}/end", response_model=schemas.RunResponse)
async def end_run_endpoint(
    run_id: int,
    status: str = "COMPLETED", # Can be "COMPLETED", "FAILED", "KILLED"
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    End a run and update its status.
    """
    db_run = exp_service.end_run(run_id, status)
    if not db_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return db_run

@router.get("/runs/{run_id}", response_model=schemas.RunResponse)
async def read_run_endpoint(
    run_id: int,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve a single run by ID.
    """
    run = exp_service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run

@router.get("/experiments/{experiment_id}/runs", response_model=List[schemas.RunResponse])
async def read_runs_by_experiment_endpoint(
    experiment_id: int,
    skip: int = 0,
    limit: int = 100,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all runs for a specific experiment.
    """
    runs = exp_service.get_runs_by_experiment(experiment_id, skip, limit)
    return runs

# --- Parameter Endpoints ---

@router.post("/runs/{run_id}/parameters", response_model=schemas.ParameterResponse, status_code=status.HTTP_201_CREATED)
async def log_parameter_endpoint(
    run_id: int,
    parameter_create: schemas.ParameterBase, # Use ParameterBase for request body
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Log a parameter for a specific run.
    """
    db_parameter = exp_service.log_parameter(run_id, parameter_create.key, parameter_create.value)
    if not db_parameter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found or parameter logging failed.")
    return db_parameter

@router.get("/runs/{run_id}/parameters", response_model=List[schemas.ParameterResponse])
async def read_run_parameters_endpoint(
    run_id: int,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all parameters for a specific run.
    """
    parameters = exp_service.get_run_parameters(run_id)
    return parameters

# --- Metric Endpoints ---

@router.post("/runs/{run_id}/metrics", response_model=schemas.MetricResponse, status_code=status.HTTP_201_CREATED)
async def log_metric_endpoint(
    run_id: int,
    metric_create: schemas.MetricBase, # Use MetricBase for request body
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Log a metric for a specific run.
    """
    db_metric = exp_service.log_metric(run_id, metric_create.key, metric_create.value, metric_create.step)
    if not db_metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found or metric logging failed.")
    return db_metric

@router.get("/runs/{run_id}/metrics", response_model=List[schemas.MetricResponse])
async def read_run_metrics_endpoint(
    run_id: int,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all metrics for a specific run.
    """
    metrics = exp_service.get_run_metrics(run_id)
    return metrics

# --- Artifact Endpoints ---

@router.post("/runs/{run_id}/artifacts", response_model=schemas.ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def log_artifact_endpoint(
    run_id: int,
    file: UploadFile = File(...),
    artifact_path: str = "", # Relative path within the run's artifact_location
    file_type: str = "other",
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Log an artifact (file) for a specific run.
    The file will be stored in the run's artifact_location.
    `artifact_path` specifies the relative path within that location.
    """
    db_run = crud_experiment.get_run(exp_service.db, run_id)
    if not db_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    # Save the uploaded file temporarily
    temp_upload_dir = os.path.join(settings.STORAGE_BASE_PATH, "temp_uploads")
    os.makedirs(temp_upload_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_upload_dir, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save uploaded file: {e}")

    # Log the artifact using the service
    db_artifact = exp_service.log_artifact(
        run_id=run_id,
        local_path=temp_file_path,
        artifact_path=os.path.join(artifact_path, file.filename), # Ensure filename is part of the path
        file_type=file_type
    )
    
    # Clean up temporary file
    os.remove(temp_file_path)

    if not db_artifact:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Artifact logging failed.")
    return db_artifact

@router.get("/runs/{run_id}/artifacts", response_model=List[schemas.ArtifactResponse])
async def read_run_artifacts_endpoint(
    run_id: int,
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all artifacts for a specific run.
    """
    artifacts = exp_service.get_run_artifacts(run_id)
    return artifacts

@router.get("/runs/{run_id}/artifacts/download")
async def download_artifact_endpoint(
    run_id: int,
    artifact_path: str, # Relative path of the artifact within the run's artifact_location
    exp_service: ExperimentService = Depends(get_experiment_service),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Download a specific artifact from a run.
    """
    full_path = exp_service.get_artifact_full_path(run_id, artifact_path)
    if not full_path or not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found or path invalid.")
    
    from fastapi.responses import FileResponse
    return FileResponse(path=full_path, filename=os.path.basename(full_path), media_type="application/octet-stream")
