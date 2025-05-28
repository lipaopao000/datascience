import time
import os
import uuid
import json # For serializing model_params if needed for logging
from typing import Optional, Dict, Any # Import Optional, Dict, Any
from datetime import datetime # Import datetime

from backend.celery_worker import celery_app # Import the celery app instance
from backend.models.database_models import SessionLocal # For creating DB session in task
from backend.services.experiment_service import ExperimentService # For logging experiments
from backend.services.project_data_service import ProjectDataService # For data operations
from backend.services.project_model_service import ProjectModelService # For model training
from backend.models import schemas # For Pydantic schemas

@celery_app.task(name="example_task_add")
def add(x: int, y: int) -> int:
    """A simple task that adds two numbers."""
    time.sleep(5)  # Simulate some work
    result = x + y
    print(f"Task 'add': {x} + {y} = {result}")
    return result

@celery_app.task(bind=True, name="long_running_ml_task_placeholder")
def long_running_ml_task(self, experiment_id: int, data_path: str, model_params: dict, user_id: Optional[int] = None):
    """
    A placeholder for a long-running ML task, integrated with experiment tracking.
    `bind=True` gives access to `self`, which is the task instance.
    This allows updating task state for progress reporting.
    """
    db = None
    run = None
    try:
        db = SessionLocal()
        exp_service = ExperimentService(db)

        # 1. Start a new run
        run_name = f"ml-run-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}"
        run = exp_service.start_run(
            experiment_id=experiment_id,
            run_name=run_name,
            user_id=user_id,
            source_type="CODE",
            source_name="backend.tasks.long_running_ml_task",
            git_commit="simulated_commit_hash" # In a real app, get actual commit
        )
        if not run:
            raise ValueError(f"Failed to start run for experiment {experiment_id}. Experiment might not exist.")
        
        self.update_state(state='STARTED', meta={'run_id': run.id, 'status': 'ML task started'})
        print(f"Started ML run {run.id} for experiment {experiment_id}. Artifacts will be saved to: {run.artifact_location}")

        # 2. Log parameters
        for key, value in model_params.items():
            exp_service.log_parameter(run.id, key, value)
        print(f"Logged parameters for run {run.id}.")

        total_steps = 10
        for i in range(total_steps):
            # Simulate a step in the ML process
            time.sleep(2) 
            # Update task state for progress
            self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total_steps, 'status': f'Processing step {i+1} of {total_steps}', 'run_id': run.id})
            print(f"ML Task (Run {run.id}): Step {i+1}/{total_steps} completed.")
        
        # Simulate model training result
        simulated_accuracy = 0.95 + (0.05 * (i / total_steps)) # Example increasing accuracy
        simulated_loss = 0.1 - (0.05 * (i / total_steps)) # Example decreasing loss

        # 3. Log metrics
        exp_service.log_metric(run.id, "accuracy", simulated_accuracy, step=total_steps)
        exp_service.log_metric(run.id, "loss", simulated_loss, step=total_steps)
        print(f"Logged metrics for run {run.id}.")

        # 4. Simulate saving a model artifact and log it
        # Create a dummy model file
        model_filename = f"model_run_{run.id}.pkl"
        dummy_model_path = os.path.join(run.artifact_location, model_filename)
        with open(dummy_model_path, "w") as f:
            f.write(f"Simulated ML model content for run {run.id}\n")
            f.write(json.dumps(model_params)) # Save params in dummy model for example
        
        exp_service.log_artifact(run.id, dummy_model_path, model_filename, "model")
        print(f"Logged model artifact for run {run.id} at {dummy_model_path}.")

        # 5. End the run successfully
        exp_service.end_run(run.id, "COMPLETED")
        print(f"ML Run {run.id} completed successfully.")
        
        return {"run_id": run.id, "status": "COMPLETED", "accuracy": simulated_accuracy, "model_path": dummy_model_path}

    except Exception as e:
        # 6. End the run with FAILED status if an error occurs
        if run:
            exp_service.end_run(run.id, "FAILED")
            self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'ML Task failed', 'run_id': run.id})
            print(f"ML Run {run.id} FAILED. Error: {e}")
        else:
            self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'ML Task failed before run could be started'})
            print(f"ML Task FAILED before run could be started. Error: {e}")
        # Re-raise the exception to let Celery mark the task as failed
        raise

# To call these tasks from your FastAPI app:
# from backend.tasks import add, long_running_ml_task, run_ml_pipeline
#
# In an endpoint:
# task_result = add.delay(4, 6)
# print(f"Task ID: {task_result.id}")
@celery_app.task(bind=True, name="run_ml_pipeline")
def run_ml_pipeline(
    self,
    project_id: int,
    data_entity_id: str,
    source_data_version: int,
    cleaning_config: Dict[str, Any],
    feature_config: Dict[str, Any],
    train_request_dict: Dict[str, Any], # Dictionary representation of ProjectModelTrainRequest
    user_id: Optional[int] = None
):
    """
    Orchestrates a full ML pipeline: data cleaning -> feature extraction -> model training.
    """
    db = None
    try:
        db = SessionLocal()
        data_service = ProjectDataService(db)
        model_service = ProjectModelService(db)

        self.update_state(state='PROGRESS', meta={'current': 1, 'total': 3, 'status': 'Starting data cleaning...'})
        print(f"Pipeline for project {project_id}, data {data_entity_id} v{source_data_version}: Starting data cleaning.")

        # Step 1: Data Cleaning
        cleaned_data_version_entry = data_service.clean_and_version_data(
            project_id=project_id,
            data_entity_id=data_entity_id,
            source_version_number=source_data_version,
            cleaning_config=cleaning_config,
            notes=f"Cleaned data from pipeline (task {self.request.id})"
        )
        if not cleaned_data_version_entry:
            raise ValueError("Data cleaning failed.")
        
        self.update_state(state='PROGRESS', meta={'current': 2, 'total': 3, 'status': 'Starting feature extraction...', 'cleaned_version_id': cleaned_data_version_entry.id})
        print(f"Pipeline for project {project_id}: Data cleaned to version {cleaned_data_version_entry.version}. Starting feature extraction.")

        # Step 2: Feature Extraction
        # Use the newly cleaned data as source for feature extraction
        features_version_entry = data_service.extract_and_version_features(
            project_id=project_id,
            source_data_entity_id=data_entity_id, # Still the same data entity ID
            source_data_version=cleaned_data_version_entry.version, # Use the cleaned version
            feature_config=feature_config,
            notes=f"Features extracted from pipeline (task {self.request.id})"
        )
        if not features_version_entry:
            raise ValueError("Feature extraction failed.")

        self.update_state(state='PROGRESS', meta={'current': 3, 'total': 3, 'status': 'Starting model training...', 'features_version_id': features_version_entry.id})
        print(f"Pipeline for project {project_id}: Features extracted to entity {features_version_entry.entity_id} v{features_version_entry.version}. Starting model training.")

        # Step 3: Model Training
        # Convert dict to Pydantic model for type checking in service
        train_request = schemas.ProjectModelTrainRequest(
            source_features_entity_id=features_version_entry.entity_id,
            source_features_version=features_version_entry.version,
            **train_request_dict
        )
        
        model_version_entry = model_service.train_and_version_model(
            project_id=project_id,
            train_request=train_request
        )
        if not model_version_entry:
            raise ValueError("Model training failed.")

        self.update_state(state='SUCCESS', meta={'status': 'Pipeline completed successfully', 'model_version_id': model_version_entry.id})
        print(f"Pipeline for project {project_id}: Model trained and versioned to entity {model_version_entry.entity_id} v{model_version_entry.version}.")

        return {
            "status": "COMPLETED",
            "cleaned_data_version_id": cleaned_data_version_entry.id,
            "features_version_id": features_version_entry.id,
            "model_version_id": model_version_entry.id,
            "model_entity_id": model_version_entry.entity_id,
            "model_version_number": model_version_entry.version
        }

    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e), 'status': 'ML Pipeline failed'})
        print(f"ML Pipeline for project {project_id} FAILED. Error: {e}")
        raise # Re-raise to let Celery mark the task as failed
    finally:
        if db:
            db.close()

# To call these tasks from your FastAPI app:
# from backend.tasks import add, long_running_ml_task, run_ml_pipeline
#
# In an endpoint:
# task_result = add.delay(4, 6)
# print(f"Task ID: {task_result.id}")
#
# ml_task_result = long_running_ml_task.delay(experiment_id=1, data_path="/path/to/data.csv", model_params={"lr": 0.01}, user_id=1)
# print(f"ML Task ID: {ml_task_result.id}")
#
# pipeline_task_result = run_ml_pipeline.delay(
#     project_id=1,
#     data_entity_id="some_uuid",
#     source_data_version=1,
#     cleaning_config={"drop_duplicates": {"subset": ["col1"]}},
#     feature_config={"numerical_passthrough": ["col2"]},
#     train_request_dict={"model_type": "logistic_regression", "target_column": "target", "model_params": {"hyperparameters": {"C": 0.1}}}
# )
# print(f"Pipeline Task ID: {pipeline_task_result.id}")
