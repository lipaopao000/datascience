from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime # Import datetime for timestamp fields


class DataUploadResponse(BaseModel): # Keep the old one if it's still used elsewhere for generic upload
    success: bool
    message: str
    patient_count: int # For zip, or 1 for single csv
    file_info: Dict[str, Any]


class GenericDataResponse(BaseModel):
    data_id: str
    columns: List[str]
    data: List[Dict[str, Any]]
    shape: List[int]
    summary: Dict[str, Any]
    records: int


class FeatureExtractionRequest(BaseModel):
    data_id: str
    feature_config: Dict[str, List[str]]


class MLTrainRequest(BaseModel):
    data_id: str # Add data_id
    model_type: str
    features: List[str] # This will now be derived from the feature file for the data_id
    target: str
    model_params: Dict[str, Any] = {}


class MLPredictRequest(BaseModel):
    model_id: str
    features: Dict[str, Any]


class CleaningConfig(BaseModel):
    remove_outliers: bool = True
    outlier_method: str = "iqr"
    fill_missing: bool = True
    missing_method: str = "interpolate"
    smooth_data: bool = False
    smooth_window: int = 5


class ColumnDefinition(BaseModel):
    name: str
    type: str # e.g., "string", "number", "datetime", "boolean"
    # Add other properties like description, required, etc. if needed

class DataSchemaBase(BaseModel):
    project_id: int # Add project_id
    name: str
    description: Optional[str] = None
    schema_type: str = "standard" # "standard" or "high_frequency_wide"
    
    # For "standard" schema_type
    columns: Optional[List[ColumnDefinition]] = None 
    
    # For "high_frequency_wide" schema_type
    time_column_index: Optional[int] = None # e.g., 0
    data_start_column_index: Optional[int] = None # e.g., 1
    num_data_columns: Optional[int] = None # e.g., 50
    data_column_base_name: Optional[str] = None # e.g., "value"
    sampling_rate_hz: Optional[float] = None # e.g., 50.0

class DataSchemaCreate(DataSchemaBase):
    pass

class DataSchemaResponse(DataSchemaBase):
    id: str
    created_at: Optional[str] = None # Store as ISO string
    updated_at: Optional[str] = None # Store as ISO string

class DataSchemaUpdate(BaseModel): # Allow partial updates
    name: Optional[str] = None
    description: Optional[str] = None
    schema_type: Optional[str] = None
    columns: Optional[List[ColumnDefinition]] = None
    time_column_index: Optional[int] = None
    data_start_column_index: Optional[int] = None
    num_data_columns: Optional[int] = None
    data_column_base_name: Optional[str] = None
    sampling_rate_hz: Optional[float] = None

class DataConfirmRequest(BaseModel):
    data_ids: List[str]

class ConfirmedDataResponse(BaseModel):
    success: bool
    message: str
    confirmed_data_ids: List[str]

class DataFormatRequest(BaseModel):
    data_ids: List[str]
    convert_to_headered: bool = False
    schema_id: Optional[str] = None
    value_column_name: Optional[str] = None # For high_frequency_wide transformation

class DataFormatResponse(BaseModel):
    success: bool
    message: str
    formatted_data_ids: List[str]

class DataDeleteBatchRequest(BaseModel):
    data_ids: List[str]

class DataDeleteBatchResponse(BaseModel):
    success: bool
    message: str
    deleted_data_ids: List[str]


# Project Management
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = None # Allow partial updates

class ProjectResponse(ProjectBase):
    id: int # Assuming integer ID from database
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # For Pydantic v2, or orm_mode = True for v1

# User Management
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool = True
    is_superuser: bool = False
    # projects: List[ProjectResponse] = [] # Could be added if needed

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Version Control
class VersionHistoryBase(BaseModel):
    entity_type: str  # e.g., "data", "model", "parameters"
    entity_id: str    # ID of the data, model, or parameter set
    # version: int # Version will be auto-incremented by CRUD, not part of create normally
    notes: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None # For parameters, config, small data
    file_identifier: Optional[str] = None # e.g., "dataset.csv", "model.pkl", "params.json" - used to construct full path

class VersionHistoryCreate(BaseModel): # Create schema doesn't need version or id
    entity_type: str
    entity_id: str
    notes: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None
    file_identifier: Optional[str] = None
    # project_id will be from path or context

class VersionHistoryResponse(VersionHistoryBase):
    id: int
    version: int # Actual version number from DB
    project_id: int # Link to project
    created_at: Optional[datetime] = None

# FileUploadResponse needs to be after VersionHistoryResponse
class FileUploadResponse(BaseModel):
    message: str
    files: List[VersionHistoryResponse] # List of successfully uploaded file versions

# System Settings
class SystemSettingBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    value: Optional[Any] = None
    description: Optional[str] = None

class SystemSettingResponse(SystemSettingBase):
    id: int
    updated_at: Optional[str] = None

# For project data operations
class DataCleaningRequest(BaseModel):
    cleaning_config: Dict[str, Any] # e.g., {"drop_na_rows": True, "fill_na_value": 0}
    notes: Optional[str] = "Cleaned data version"

class ProjectFeatureExtractionRequest(BaseModel):
    source_data_entity_id: str # UUID of the source data entity
    source_data_version: int   # Version of the source data to use
    feature_config: Dict[str, List[str]] # Same as old FeatureExtractionRequest
    notes: Optional[str] = "Extracted features"

class GridSearchCVConfig(BaseModel):
    param_grid: Dict[str, List[Any]]
    cv: Optional[int] = 3 # Default CV folds
    scoring: Optional[str] = None # e.g., 'accuracy', 'f1_macro', 'r2', 'neg_mean_squared_error'

class ModelParams(BaseModel):
    hyperparameters: Optional[Dict[str, Any]] = {}
    grid_search_cv: Optional[GridSearchCVConfig] = None

class ProjectModelTrainRequest(BaseModel):
    source_features_entity_id: str # UUID of the source features entity
    source_features_version: int   # Version of the source features to use
    model_type: str                # e.g., "logistic_regression", "random_forest"
    target_column: str             # Name of the target variable column in the features data
    model_params: Optional[ModelParams] = ModelParams() # Includes hyperparameters and optional GridSearchCV config
    notes: Optional[str] = "Trained model"

class ProjectModelPredictRequest(BaseModel):
    model_entity_id: str  # UUID of the model entity
    model_version: int    # Version of the model to use
    input_features: Dict[str, Any] # Single instance for prediction, or List[Dict[str,Any]] for batch

# For data rollback
class RollbackRequest(BaseModel):
    notes: Optional[str] = None

# Celery Task Status
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None # For progress info or other metadata


# --- Experiment Tracking Schemas ---

class ExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentResponse(ExperimentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # For Pydantic v2, or orm_mode = True for v1

class RunBase(BaseModel):
    experiment_id: int
    run_name: Optional[str] = None
    status: str = "RUNNING"
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    git_commit: Optional[str] = None
    user_id: Optional[int] = None
    artifact_location: Optional[str] = None

class RunCreate(RunBase):
    pass

class RunUpdate(BaseModel):
    run_name: Optional[str] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    artifact_location: Optional[str] = None

class RunResponse(RunBase):
    id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Model Registry Schemas ---

class RegisteredModelBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None

class RegisteredModelCreate(RegisteredModelBase):
    pass

class RegisteredModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None

class RegisteredModelResponse(RegisteredModelBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModelVersionBase(BaseModel):
    registered_model_id: int
    version: int # This will be auto-assigned by service, but useful for response/lookup
    run_id: Optional[int] = None # Link to the experiment run that produced this model
    model_path: str # Path to the actual model file (e.g., S3 URI or local path)
    model_framework: Optional[str] = None # e.g., "scikit-learn", "tensorflow", "pytorch"
    model_signature: Optional[Dict[str, Any]] = None # Input/output schema of the model
    model_metadata: Optional[Dict[str, Any]] = None # Any other relevant metadata
    stage: str = "None" # e.g., "None", "Staging", "Production", "Archived"
    user_id: Optional[int] = None

class ModelVersionCreate(BaseModel): # For creation, version is not provided by client
    registered_model_id: int
    run_id: Optional[int] = None
    model_path: str
    model_framework: Optional[str] = None
    model_signature: Optional[Dict[str, Any]] = None
    model_metadata: Optional[Dict[str, Any]] = None
    stage: str = "None"
    user_id: Optional[int] = None

class ModelVersionUpdate(BaseModel):
    model_path: Optional[str] = None
    model_framework: Optional[str] = None
    model_signature: Optional[Dict[str, Any]] = None
    model_metadata: Optional[Dict[str, Any]] = None
    stage: Optional[str] = None
    user_id: Optional[int] = None # If ownership can be transferred

class ModelVersionResponse(ModelVersionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ParameterBase(BaseModel):
    key: str
    value: str # Stored as Text in DB, so string here

class ParameterCreate(ParameterBase):
    run_id: int # Required for creation

class ParameterResponse(ParameterBase):
    id: int
    run_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MetricBase(BaseModel):
    key: str
    value: Any # Stored as JSON in DB, so Any here
    step: Optional[int] = None

class MetricCreate(MetricBase):
    run_id: int # Required for creation

class MetricResponse(MetricBase):
    id: int
    run_id: int
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArtifactBase(BaseModel):
    path: str
    file_type: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None

class ArtifactCreate(ArtifactBase):
    run_id: int # Required for creation

class ArtifactResponse(ArtifactBase):
    id: int
    run_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
