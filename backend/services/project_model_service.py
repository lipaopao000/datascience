import os
import pandas as pd
import joblib # For saving/loading scikit-learn models
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging

from backend.crud import crud_version_history, crud_system_setting
from backend.core.storage_utils import get_versioned_data_path
from backend.models import schemas as pydantic_schemas # Renamed to avoid conflict
from backend.services.project_data_service import ProjectDataService # To load features data

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
import numpy as np
from datetime import datetime # Import datetime for run names

logger = logging.getLogger(__name__)

from backend.services.experiment_service import ExperimentService # Import ExperimentService
from backend.services.model_registry_service import ModelRegistryService # Import ModelRegistryService

class ProjectModelService:
    def __init__(self, db: Session):
        self.db = db
        self.project_data_service = ProjectDataService(db) # Instantiate ProjectDataService
        self.experiment_service = ExperimentService(db) # Instantiate ExperimentService
        self.model_registry_service = ModelRegistryService(db) # Instantiate ModelRegistryService

    def load_features_data(
        self,
        project_id: int,
        features_entity_id: str,
        features_version: int
    ) -> Optional[pd.DataFrame]:
        """
        Loads a specific version of a features entity for a project.
        This is similar to ProjectDataService.load_data_from_version but specific for 'features'.
        """
        version_entry = crud_version_history.get_specific_version(
            self.db,
            project_id=project_id,
            entity_type="features", 
            entity_id=features_entity_id,
            version=features_version
        )

        if not version_entry or not version_entry.file_identifier:
            logger.warning(
                f"No version entry or file_identifier found for features: project {project_id}, "
                f"entity {features_entity_id}, version {features_version}."
            )
            return None

        file_path = get_versioned_data_path(
            self.db,
            project_id=project_id,
            entity_type="features",
            entity_id=features_entity_id,
            version=features_version,
            filename=version_entry.file_identifier
        )

        if not os.path.exists(file_path):
            logger.error(f"Features file not found at versioned path: {file_path}")
            return None
        try:
            # Assuming features are saved as PKL (DataFrame)
            df = pd.read_pickle(file_path)
            logger.info(f"Successfully loaded features from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading features from {file_path}: {e}", exc_info=True)
            return None


    def train_and_version_model(
        self,
        project_id: int,
        train_request: pydantic_schemas.ProjectModelTrainRequest
    ) -> Optional[pydantic_schemas.VersionHistoryResponse]:
        """
        Loads features, trains a model, saves the model, and creates a version history entry.
        Integrates with Experiment Tracking and Model Registry.
        """
        run = None
        try:
            # 1. Load the source features version
            features_df = self.load_features_data(
                project_id=project_id,
                features_entity_id=train_request.source_features_entity_id,
                features_version=train_request.source_features_version
            )
            if features_df is None:
                logger.error("Source features data for model training not found.")
                return None

            # Get user ID (assuming current_user is available or passed)
            # For now, let's use a placeholder or pass it from the router
            # user_id = current_user.id if current_user else None
            user_id = 1 # Placeholder for a default user or pass from router

            # 2. Start a new Experiment Run
            # Find or create an experiment for this project/model type
            experiment_name = f"{train_request.model_type.replace('_', ' ').title()} Training"
            experiment = self.experiment_service.get_experiment_by_name(self.db, name=experiment_name)
            if not experiment:
                experiment_create = pydantic_schemas.ExperimentCreate(
                    name=experiment_name,
                    description=f"Experiment for {train_request.model_type} model training in project {project_id}.",
                    project_id=project_id
                )
                experiment = self.experiment_service.create_experiment(experiment_create)
                if not experiment:
                    raise Exception(f"Failed to create experiment: {experiment_name}")

            run_name = f"run-{train_request.model_type}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            run = self.experiment_service.start_run(
                experiment_id=experiment.id,
                run_name=run_name,
                user_id=user_id,
                source_type="CODE",
                source_name="backend.services.project_model_service.train_and_version_model",
                git_commit="simulated_commit_hash" # Replace with actual git commit in production
            )
            if not run:
                raise Exception(f"Failed to start run for experiment {experiment.id}")
            logger.info(f"Started experiment run {run.id} for experiment {experiment.name}.")

            # 3. Log parameters to the run
            for key, value in train_request.model_params.hyperparameters.items():
                self.experiment_service.log_parameter(run.id, key, value)
            if train_request.model_params.grid_search_cv:
                self.experiment_service.log_parameter(run.id, "grid_search_cv_config", train_request.model_params.grid_search_cv.model_dump_json())
            self.experiment_service.log_parameter(run.id, "target_column", train_request.target_column)
            self.experiment_service.log_parameter(run.id, "source_features_entity_id", train_request.source_features_entity_id)
            self.experiment_service.log_parameter(run.id, "source_features_version", train_request.source_features_version)
            logger.info(f"Logged parameters to run {run.id}.")

            # 4. Perform Model Training
            model_object = None
            training_metrics = {}
            model_notes = train_request.notes
            
            if train_request.target_column not in features_df.columns:
                raise ValueError(f"Target column '{train_request.target_column}' not found in features data.")
            
            X = features_df.drop(columns=[train_request.target_column])
            y = features_df[train_request.target_column]

            stratify_param = y if pd.api.types.is_categorical_dtype(y) or (y.nunique() < 10 and len(y) > 20) else None
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify_param)

            model_params_config = train_request.model_params if train_request.model_params else pydantic_schemas.ModelParams()
            model_specific_params = model_params_config.hyperparameters if model_params_config.hyperparameters else {}
            grid_search_cv_config = model_params_config.grid_search_cv

            base_model = None
            is_classification_task = True

            if train_request.model_type == "random_forest_classifier":
                base_model = RandomForestClassifier(random_state=42, **model_specific_params)
            elif train_request.model_type == "gradient_boosting_classifier":
                base_model = GradientBoostingClassifier(random_state=42, **model_specific_params)
            elif train_request.model_type == "logistic_regression":
                base_model = LogisticRegression(random_state=42, solver='liblinear', **model_specific_params)
            elif train_request.model_type == "linear_regression":
                base_model = LinearRegression(**model_specific_params)
                is_classification_task = False
            elif train_request.model_type == "random_forest_regressor":
                base_model = RandomForestRegressor(random_state=42, **model_specific_params)
                is_classification_task = False
            else:
                raise ValueError(f"Unsupported model_type: {train_request.model_type}")

            training_metrics_raw = {
                "feature_columns": X.columns.tolist(),
                "test_set_shape": [X_test.shape[0], X_test.shape[1]],
                "train_set_shape": [X_train.shape[0], X_train.shape[1]]
            }

            if grid_search_cv_config and grid_search_cv_config.param_grid:
                logger.info(f"Performing GridSearchCV for {train_request.model_type} with param_grid: {grid_search_cv_config.param_grid}")
                
                default_scoring = 'accuracy' if is_classification_task else 'r2'
                scoring = grid_search_cv_config.scoring or default_scoring
                
                grid_search = GridSearchCV(
                    estimator=base_model,
                    param_grid=grid_search_cv_config.param_grid,
                    cv=grid_search_cv_config.cv,
                    scoring=scoring,
                    n_jobs=-1 # Use all available cores
                )
                grid_search.fit(X_train, y_train) # Fit on training data
                model_object = grid_search.best_estimator_
                training_metrics_raw["best_params_grid_search"] = grid_search.best_params_
                training_metrics_raw["best_score_grid_search"] = float(grid_search.best_score_)
                logger.info(f"GridSearchCV complete. Best params: {grid_search.best_params_}, Best score ({scoring}): {grid_search.best_score_}")
            else:
                model_object = base_model
                model_object.fit(X_train, y_train)
                logger.info(f"Standard model fitting for {train_request.model_type} (no GridSearchCV).")

            y_pred_test = model_object.predict(X_test)

            if is_classification_task:
                training_metrics_raw.update({
                    "accuracy_on_test": float(accuracy_score(y_test, y_pred_test)),
                    "precision_macro_on_test": float(precision_score(y_test, y_pred_test, average='macro', zero_division=0)),
                    "recall_macro_on_test": float(recall_score(y_test, y_pred_test, average='macro', zero_division=0)),
                    "f1_macro_on_test": float(f1_score(y_test, y_pred_test, average='macro', zero_division=0)),
                })
            else: # Regression task
                 training_metrics_raw.update({
                    "mse_on_test": float(mean_squared_error(y_test, y_pred_test)),
                    "rmse_on_test": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                    "r2_score_on_test": float(r2_score(y_test, y_pred_test)),
                })
            logger.info(f"Model '{train_request.model_type}' evaluation on test set complete. Metrics: {training_metrics_raw}")

            # 5. Log metrics to the run
            for key, value in training_metrics_raw.items():
                # Only log numeric/JSON-serializable metrics as actual metrics
                if isinstance(value, (int, float, bool, dict, list)):
                    self.experiment_service.log_metric(run.id, key, value)
                else:
                    # Store non-numeric metrics as parameters or part of artifact metadata
                    self.experiment_service.log_parameter(run.id, f"metric_info_{key}", str(value))
            logger.info(f"Logged metrics to run {run.id}.")

            # 6. Save the trained model to a new versioned file (using VersionHistory for storage)
            model_entity_id = str(uuid.uuid4()) # Unique ID for this specific model artifact
            new_version_number = 1 # This is the first version of this specific model artifact
            
            model_filename = f"{train_request.model_type.replace(' ','_')}_run_{run.id}_v{new_version_number}.pkl"
            
            # Use the run's artifact_location for storing the model file
            model_file_path_in_artifacts = Path(run.artifact_location) / model_filename
            
            joblib.dump(model_object, model_file_path_in_artifacts) # Using joblib for scikit-learn models
            logger.info(f"Saved trained model to {model_file_path_in_artifacts}")

            # 7. Log artifact (model file) to the run
            self.experiment_service.log_artifact(
                run.id, 
                str(model_file_path_in_artifacts), # Local path of the saved file
                model_filename, # Relative path within artifact_location
                "model"
            )
            logger.info(f"Logged model artifact for run {run.id}.")

            # 8. Register the model in the Model Registry
            registered_model = self.model_registry_service.get_registered_model_by_name(self.db, name=train_request.model_type)
            if not registered_model:
                registered_model_create = pydantic_schemas.RegisteredModelCreate(
                    name=train_request.model_type,
                    description=f"Registered model for {train_request.model_type} in project {project_id}.",
                    project_id=project_id
                )
                registered_model = self.model_registry_service.create_registered_model(registered_model_create)
                if not registered_model:
                    raise Exception(f"Failed to create registered model: {train_request.model_type}")
            
            model_version_create = pydantic_schemas.ModelVersionCreate(
                registered_model_id=registered_model.id,
                run_id=run.id, # Link to the experiment run
                model_path=str(model_file_path_in_artifacts), # Full path to the model file
                model_framework="scikit-learn", # Or derive dynamically
                model_signature={"inputs": X.columns.tolist(), "outputs": ["prediction"]}, # Basic signature
                model_metadata={
                    "target_column": train_request.target_column,
                    "training_metrics": training_metrics_raw,
                    "hyperparameters": train_request.model_params.hyperparameters,
                    "grid_search_cv_config": train_request.model_params.grid_search_cv.model_dump() if train_request.model_params.grid_search_cv else None
                },
                stage="None", # Initial stage
                user_id=user_id
            )
            model_version = self.model_registry_service.create_model_version(model_version_create, user_id=user_id)
            if not model_version:
                raise Exception(f"Failed to create model version for {train_request.model_type}")
            logger.info(f"Registered model version {model_version.version} for model {registered_model.name}.")

            # 9. End the experiment run successfully
            self.experiment_service.end_run(run.id, "COMPLETED")
            logger.info(f"Experiment run {run.id} completed successfully.")

            # 10. Create a VersionHistory entry for the model (linking to the model registry version)
            # This VersionHistory entry is for the *model artifact* itself, not the model registry entry.
            # It tracks the file in the project's version history.
            version_metadata = {
                "registered_model_id": registered_model.id,
                "registered_model_name": registered_model.name,
                "model_version_id": model_version.id,
                "model_version_number": model_version.version,
                "experiment_run_id": run.id,
                "model_type": train_request.model_type,
                "training_metrics": training_metrics_raw,
                "original_filename": model_filename,
                "content_type": "application/octet-stream", # For PKL
                "size_bytes": model_file_path_in_artifacts.stat().st_size,
            }
            
            version_create_payload = pydantic_schemas.VersionHistoryCreate(
                entity_type="model", 
                entity_id=model_entity_id, # This is the UUID of the model artifact
                notes=train_request.notes,
                version_metadata=version_metadata,
                file_identifier=model_filename 
            )
            
            new_db_entry = crud_version_history.create_version_history(
                self.db, project_id, version_create_payload
            )
            
            return pydantic_schemas.VersionHistoryResponse.model_validate(new_db_entry)

        except Exception as e:
            logger.error(f"Error during model training and versioning: {e}", exc_info=True)
            if run:
                self.experiment_service.end_run(run.id, "FAILED")
                logger.error(f"Experiment run {run.id} marked as FAILED.")
            # Re-raise the exception to be handled by the router
            raise

    # Future methods:
    # - predict_with_versioned_model
    # - evaluate_versioned_model

    def predict_with_versioned_model(
        self,
        project_id: int,
        predict_request: pydantic_schemas.ProjectModelPredictRequest
    ) -> Optional[Any]: # Return type can be more specific, e.g., List[Any] or np.ndarray
        """
        Loads a specific version of a trained model and makes predictions on input features.
        """
        # 1. Load the specified model version
        version_entry = crud_version_history.get_specific_version(
            self.db,
            project_id=project_id,
            entity_type="model",
            entity_id=predict_request.model_entity_id,
            version=predict_request.model_version
        )

        if not version_entry or not version_entry.file_identifier:
            logger.warning(
                f"No version entry or file_identifier found for model: project {project_id}, "
                f"entity {predict_request.model_entity_id}, version {predict_request.model_version}."
            )
            return None

        model_file_path = get_versioned_data_path(
            self.db,
            project_id=project_id,
            entity_type="model",
            entity_id=predict_request.model_entity_id,
            version=predict_request.model_version,
            filename=version_entry.file_identifier
        )

        if not os.path.exists(model_file_path):
            logger.error(f"Model file not found at versioned path: {model_file_path}")
            return None

        try:
            model_object = joblib.load(model_file_path)
            logger.info(f"Successfully loaded model from {model_file_path}")
        except Exception as e:
            logger.error(f"Error loading model from {model_file_path}: {e}", exc_info=True)
            return None

        # 2. Prepare input features for prediction
        # Assuming input_features is a single instance (dict)
        # For scikit-learn, model.predict usually expects a 2D array-like structure (e.g., DataFrame or list of lists)
        try:
            # Convert the input dict to a DataFrame with a single row.
            # The order of columns in this DataFrame must match the order expected by the model.
            # This information (expected feature order/names) should ideally be stored with the model
            # or derived from its training metadata.
            
            # Placeholder: Attempt to get feature names from model training metadata if stored
            feature_names = None
            if version_entry.version_metadata and \
               version_entry.version_metadata.get("training_metrics") and \
               version_entry.version_metadata["training_metrics"].get("feature_columns"):
                feature_names = version_entry.version_metadata["training_metrics"]["feature_columns"]
            
            if feature_names:
                # Ensure all required features are present in the input
                missing_input_features = [f_name for f_name in feature_names if f_name not in predict_request.input_features]
                if missing_input_features:
                    raise ValueError(f"Missing input features for prediction: {', '.join(missing_input_features)}")
                
                # Create DataFrame with columns in the correct order
                input_df = pd.DataFrame([predict_request.input_features])[feature_names]
            else:
                # Fallback if feature names are not stored: use keys from input_features.
                # This is less robust as order might not match.
                logger.warning("Feature names for model prediction not found in metadata. Using order from input_features. This might be unreliable.")
                input_df = pd.DataFrame([predict_request.input_features])

            # 3. Make prediction
            predictions = model_object.predict(input_df)
            
            # For a single instance prediction, result is often a single value or an array of one.
            # Convert to a Python native type if it's a numpy type.
            if hasattr(predictions, "tolist"):
                return predictions.tolist()
            return predictions

        except ValueError as ve: # E.g. feature mismatch
            logger.error(f"ValueError during prediction: {ve}", exc_info=True)
            raise ve # Re-raise to be caught by router and returned as 400
        except Exception as e:
            logger.error(f"Error during prediction: {e}", exc_info=True)
            # Return a more generic error or None, to be handled by the router
            return None
