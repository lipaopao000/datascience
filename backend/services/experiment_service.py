from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import uuid # For generating unique run IDs or artifact IDs
import hashlib # For checksums
from pathlib import Path # Import Path

from backend.models import database_models as models
from backend.models import schemas
from backend.crud import crud_experiment
from backend.core.storage_utils import get_project_data_save_path, get_versioned_data_path
from backend.core.config import settings

class ExperimentService:
    def __init__(self, db: Session):
        self.db = db

    def create_experiment(self, experiment_create: schemas.ExperimentCreate) -> models.Experiment:
        # Check if experiment with the same name already exists for the project
        existing_experiment = crud_experiment.get_experiment_by_name(self.db, name=experiment_create.name)
        if existing_experiment:
            # You might want to raise an HTTPException here in a router,
            # but services typically return None or raise custom exceptions.
            return None # Or raise ValueError("Experiment with this name already exists.")
        
        return crud_experiment.create_experiment(self.db, experiment=experiment_create)

    def get_experiment(self, experiment_id: int) -> Optional[models.Experiment]:
        return crud_experiment.get_experiment(self.db, experiment_id)

    def get_experiments(self, skip: int = 0, limit: int = 100, project_id: Optional[int] = None) -> List[models.Experiment]:
        if project_id:
            return crud_experiment.get_experiments_by_project(self.db, project_id, skip, limit)
        return crud_experiment.get_experiments(self.db, skip, limit)

    def start_run(
        self, 
        experiment_id: int, 
        run_name: Optional[str] = None, 
        user_id: Optional[int] = None,
        source_type: Optional[str] = None,
        source_name: Optional[str] = None,
        git_commit: Optional[str] = None
    ) -> Optional[models.Run]:
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None # Experiment not found

        if not run_name:
            run_name = f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # Determine artifact location for this run
        # This path should be unique per run and accessible for storing artifacts
        # Example: backend/data/artifacts/experiment_id/run_id/
        # For now, let's use a simple path based on project_id and run_id (which will be assigned after creation)
        # We'll need to update the run with the actual artifact_location after it's created and has an ID.
        
        # Create a temporary run object to get an ID, then update artifact_location
        # Or, generate a UUID for the run_id and use that for the path
        run_uuid = str(uuid.uuid4())
        artifact_base_path = os.path.join(settings.STORAGE_BASE_PATH, "artifacts", str(experiment_id), run_uuid)
        os.makedirs(artifact_base_path, exist_ok=True)

        run_create = schemas.RunCreate(
            experiment_id=experiment_id,
            run_name=run_name,
            status="RUNNING",
            source_type=source_type,
            source_name=source_name,
            git_commit=git_commit,
            user_id=user_id,
            artifact_location=artifact_base_path # Set the base path for artifacts
        )
        db_run = crud_experiment.create_run(self.db, run=run_create)
        return db_run

    def end_run(self, run_id: int, status: str = "COMPLETED") -> Optional[models.Run]:
        run_update = schemas.RunUpdate(end_time=datetime.now(), status=status)
        return crud_experiment.update_run(self.db, run_id, run_update)

    def log_parameter(self, run_id: int, key: str, value: Any) -> Optional[models.Parameter]:
        # Convert value to string for storage in Text column
        parameter_create = schemas.ParameterCreate(run_id=run_id, key=key, value=str(value))
        return crud_experiment.create_parameter(self.db, parameter=parameter_create)

    def log_metric(self, run_id: int, key: str, value: Any, step: Optional[int] = None) -> Optional[models.Metric]:
        # Value is stored as JSON, so pass directly
        metric_create = schemas.MetricCreate(run_id=run_id, key=key, value=value, step=step)
        return crud_experiment.create_metric(self.db, metric=metric_create)

    def log_artifact(self, run_id: int, local_path: str, artifact_path: str, file_type: str) -> Optional[models.Artifact]:
        db_run = crud_experiment.get_run(self.db, run_id)
        if not db_run or not db_run.artifact_location:
            return None # Run or artifact_location not found

        # Construct the full destination path
        full_artifact_dir = Path(db_run.artifact_location) / Path(artifact_path).parent
        os.makedirs(full_artifact_dir, exist_ok=True)
        
        full_destination_path = Path(db_run.artifact_location) / artifact_path
        
        # Copy the file
        try:
            import shutil
            shutil.copy(local_path, full_destination_path)
        except FileNotFoundError:
            print(f"Error: Local artifact file not found at {local_path}")
            return None
        except Exception as e:
            print(f"Error copying artifact: {e}")
            return None

        # Calculate file size and checksum
        file_size = os.path.getsize(full_destination_path)
        with open(full_destination_path, "rb") as f:
            checksum = hashlib.md5(f.read()).hexdigest() # Or SHA256 for stronger hash

        artifact_create = schemas.ArtifactCreate(
            run_id=run_id,
            path=artifact_path, # Store relative path
            file_type=file_type,
            file_size=file_size,
            checksum=checksum
        )
        return crud_experiment.create_artifact(self.db, artifact=artifact_create)

    def get_run_parameters(self, run_id: int) -> List[models.Parameter]:
        return crud_experiment.get_parameters_by_run(self.db, run_id)

    def get_run_metrics(self, run_id: int) -> List[models.Metric]:
        return crud_experiment.get_metrics_by_run(self.db, run_id)

    def get_run_artifacts(self, run_id: int) -> List[models.Artifact]:
        return crud_experiment.get_artifacts_by_run(self.db, run_id)

    def get_artifact_full_path(self, run_id: int, artifact_path: str) -> Optional[Path]:
        db_run = crud_experiment.get_run(self.db, run_id)
        if db_run and db_run.artifact_location:
            return Path(db_run.artifact_location) / artifact_path
        return None
