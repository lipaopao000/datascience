from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from backend.models import database_models as models
from backend.models import schemas
from backend.crud import crud_model_registry, crud_experiment # Import crud_experiment for linking to runs
from backend.core.storage_utils import get_project_data_save_path # For model storage paths
from backend.core.config import settings # For base storage path

class ModelRegistryService:
    def __init__(self, db: Session):
        self.db = db

    def create_registered_model(self, model_create: schemas.RegisteredModelCreate) -> Optional[models.RegisteredModel]:
        existing_model = crud_model_registry.get_registered_model_by_name(self.db, name=model_create.name)
        if existing_model:
            return None # Model with this name already exists
        return crud_model_registry.create_registered_model(self.db, model=model_create)

    def get_registered_model(self, model_id: int) -> Optional[models.RegisteredModel]:
        return crud_model_registry.get_registered_model(self.db, model_id)

    def get_registered_models(self, skip: int = 0, limit: int = 100, project_id: Optional[int] = None) -> List[models.RegisteredModel]:
        return crud_model_registry.get_registered_models(self.db, skip, limit, project_id)

    def create_model_version(
        self, 
        version_create: schemas.ModelVersionCreate,
        user_id: Optional[int] = None # User who is registering this version
    ) -> Optional[models.ModelVersion]:
        registered_model = crud_model_registry.get_registered_model(self.db, version_create.registered_model_id)
        if not registered_model:
            return None # Registered model not found

        # Ensure model_path is valid and potentially copy/move the model file
        # For now, assume model_path is a path to a file that needs to be managed
        # In a real system, this might involve moving from a temporary location
        # or directly referencing an artifact from an experiment run.

        # If model_path is an artifact from a run, we might want to copy it to a dedicated model registry storage
        # For simplicity, let's assume model_path is already the final path or a path to be copied from.
        # If it's from an experiment run, we should verify the run_id and artifact path.
        
        # Example: If model_path is a local path, copy it to a structured model registry directory
        # This is a simplified example. In production, you'd use cloud storage or a dedicated model store.
        model_registry_base_path = os.path.join(settings.STORAGE_BASE_PATH, "model_registry")
        os.makedirs(model_registry_base_path, exist_ok=True)

        # Determine the next version number (handled by CRUD)
        # Construct a unique path for this model version
        # e.g., backend/data/model_registry/model_name/version_number/model.pkl
        next_version = (crud_model_registry.get_latest_model_version(self.db, version_create.registered_model_id).version + 1) if crud_model_registry.get_latest_model_version(self.db, version_create.registered_model_id) else 1
        
        model_version_dir = os.path.join(model_registry_base_path, registered_model.name, f"v{next_version}")
        os.makedirs(model_version_dir, exist_ok=True)
        
        # Assuming version_create.model_path is a local path to the model file
        # In a real scenario, you'd copy the actual model file here.
        # For now, let's just use the provided model_path as the final path.
        # If the model is an artifact from a run, its path is already managed by ExperimentService.
        # We should ideally link to the artifact directly or copy it.
        
        # For now, let's assume model_path in ModelVersionCreate is the *final* storage path.
        # If it's an artifact from a run, we should retrieve its full path from ExperimentService
        # and then store that full path here.
        
        # If run_id is provided, we can try to get the artifact path from the run
        final_model_path = version_create.model_path # Default to provided path
        if version_create.run_id:
            # This would require an instance of ExperimentService
            # For simplicity, let's assume the model_path provided is already the artifact path
            # or a path that needs to be copied.
            # A more robust solution would involve:
            # from backend.services.experiment_service import ExperimentService
            # exp_service = ExperimentService(self.db)
            # artifact = exp_service.get_run_artifact_by_path(version_create.run_id, version_create.model_path)
            # if artifact:
            #    final_model_path = exp_service.get_artifact_full_path(version_create.run_id, artifact.path)
            pass # Placeholder for more complex artifact handling

        version_create.user_id = user_id # Assign user who registered
        
        return crud_model_registry.create_model_version(self.db, model_version=version_create)

    def get_model_version(self, version_id: int) -> Optional[models.ModelVersion]:
        return crud_model_registry.get_model_version(self.db, version_id)

    def get_model_version_by_name_and_version(self, model_name: str, version: int) -> Optional[models.ModelVersion]:
        registered_model = crud_model_registry.get_registered_model_by_name(self.db, name=model_name)
        if not registered_model:
            return None
        return crud_model_registry.get_model_version_by_registered_model_and_version(self.db, registered_model.id, version)

    def get_latest_model_version(self, registered_model_id: int) -> Optional[models.ModelVersion]:
        return crud_model_registry.get_latest_model_version(self.db, registered_model_id)

    def get_model_versions_by_registered_model(self, registered_model_id: int, skip: int = 0, limit: int = 100) -> List[models.ModelVersion]:
        return crud_model_registry.get_model_versions_by_registered_model(self.db, registered_model_id, skip, limit)

    def transition_model_version_stage(self, version_id: int, new_stage: str, user_id: Optional[int] = None) -> Optional[models.ModelVersion]:
        # Validate new_stage against allowed stages (e.g., "None", "Staging", "Production", "Archived")
        allowed_stages = ["None", "Staging", "Production", "Archived"]
        if new_stage not in allowed_stages:
            return None # Invalid stage

        version_update = schemas.ModelVersionUpdate(stage=new_stage, user_id=user_id)
        return crud_model_registry.update_model_version(self.db, version_id, version_update)

    def delete_model_version(self, version_id: int) -> Optional[models.ModelVersion]:
        # Before deleting, consider if the actual model file should also be deleted from storage.
        # This would require retrieving the model_path and using os.remove or a storage utility.
        db_model_version = crud_model_registry.get_model_version(self.db, version_id)
        if db_model_version and os.path.exists(db_model_version.model_path):
            try:
                os.remove(db_model_version.model_path)
                # Also remove empty parent directories if desired
                # os.removedirs(os.path.dirname(db_model_version.model_path))
            except Exception as e:
                print(f"Warning: Could not delete model file {db_model_version.model_path}: {e}")
        return crud_model_registry.delete_model_version(self.db, version_id)

    def delete_registered_model(self, model_id: int) -> Optional[models.RegisteredModel]:
        # When deleting a registered model, all its versions (and their files) should also be deleted.
        # The cascade="all, delete-orphan" in database_models.py handles DB deletion.
        # We need to manually delete files.
        db_registered_model = crud_model_registry.get_registered_model(self.db, model_id)
        if db_registered_model:
            for version in db_registered_model.versions:
                if version.model_path and os.path.exists(version.model_path):
                    try:
                        os.remove(version.model_path)
                    except Exception as e:
                        print(f"Warning: Could not delete model file {version.model_path} for version {version.id}: {e}")
            # Attempt to remove the base directory for this registered model if it exists and is empty
            model_registry_base_path = os.path.join(settings.STORAGE_BASE_PATH, "model_registry")
            model_dir = os.path.join(model_registry_base_path, db_registered_model.name)
            if os.path.exists(model_dir) and not os.listdir(model_dir): # Check if directory is empty
                try:
                    os.rmdir(model_dir)
                except OSError as e:
                    print(f"Warning: Could not remove empty model directory {model_dir}: {e}")

        return crud_model_registry.delete_registered_model(self.db, model_id)
