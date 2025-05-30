from pydantic import BaseModel
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime


class DataUploadResponse(BaseModel):
    success: bool
    message: str
    patient_count: int
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
    data_id: str
    model_type: str
    features: List[str]
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
    type: str


class DataSchemaBase(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    schema_type: str = "standard"
    
    columns: Optional[List[ColumnDefinition]] = None
    
    time_column_index: Optional[int] = None
    data_start_column_index: Optional[int] = None
    num_data_columns: Optional[int] = None
    data_column_base_name: Optional[str] = None
    sampling_rate_hz: Optional[float] = None

class DataSchemaCreate(DataSchemaBase):
    pass

class DataSchemaResponse(DataSchemaBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DataSchemaUpdate(BaseModel):
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

class DataValueColumnMapping(BaseModel):
    data_id: str
    value_column_name: str

class ProjectDataFormatRequest(BaseModel):
    data_ids: List[str]
    convert_to_headered: bool = False
    schema_id: Optional[str] = None
    data_specific_value_columns: Optional[List[DataValueColumnMapping]] = None
    notes: Optional[str] = None # Added notes field

class ProjectDataFormatResponse(BaseModel):
    success: bool
    message: str
    formatted_data_ids: List[str]

class ProjectDataDeleteRequest(BaseModel):
    data_ids: List[str]

class ProjectDataDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_data_ids: List[str]


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    name: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

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

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None # Added refresh_token

class TokenData(BaseModel):
    username: Optional[str] = None

class VersionHistoryBase(BaseModel):
    entity_type: str
    entity_id: str
    notes: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None
    file_identifier: Optional[str] = None
    display_name: Optional[str] = None # Added display_name

class VersionHistoryCreate(BaseModel):
    entity_type: str
    entity_id: str
    notes: Optional[str] = None
    version_metadata: Optional[Dict[str, Any]] = None
    file_identifier: Optional[str] = None
    display_name: Optional[str] = None # Added display_name

class VersionHistoryResponse(VersionHistoryBase):
    id: int
    version: int
    project_id: int
    created_at: Optional[datetime] = None
    rows: Optional[int] = None
    columns: Optional[int] = None
    size_bytes: Optional[int] = None
    display_name: Optional[str] = None # Added display_name

class VersionHistoryUpdateDisplayName(BaseModel):
    display_name: Optional[str] = None

class FileUploadResponse(BaseModel):
    message: str
    files: List[VersionHistoryResponse]

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

class DataCleaningRequest(BaseModel):
    cleaning_config: Dict[str, Any]
    notes: Optional[str] = "Cleaned data version"

class ProjectFeatureExtractionRequest(BaseModel):
    source_data_entity_id: str
    source_data_version: int
    feature_config: Dict[str, List[str]]
    notes: Optional[str] = "Extracted features"

class GridSearchCVConfig(BaseModel):
    param_grid: Dict[str, List[Any]]
    cv: Optional[int] = 3
    scoring: Optional[str] = None

class ModelParams(BaseModel):
    hyperparameters: Optional[Dict[str, Any]] = {}
    grid_search_cv: Optional[GridSearchCVConfig] = None

class ProjectModelTrainRequest(BaseModel):
    source_features_entity_id: str
    source_features_version: int
    model_type: str
    target_column: str
    model_params: Optional[ModelParams] = ModelParams()
    notes: Optional[str] = "Trained model"

class ProjectModelPredictRequest(BaseModel):
    model_entity_id: str
    model_version: int
    input_features: Dict[str, Any]

class RollbackRequest(BaseModel):
    notes: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None
    result: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None


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
        from_attributes = True

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
    version: int
    run_id: Optional[int] = None
    model_path: str
    model_framework: Optional[str] = None
    model_signature: Optional[Dict[str, Any]] = None
    model_metadata: Optional[Dict[str, Any]] = None
    stage: str = "None"
    user_id: Optional[int] = None

class ModelVersionCreate(BaseModel):
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
    user_id: Optional[int] = None

class ModelVersionResponse(ModelVersionBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ParameterBase(BaseModel):
    key: str
    value: str

class ParameterCreate(ParameterBase):
    run_id: int

class ParameterResponse(ParameterBase):
    id: int
    run_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MetricBase(BaseModel):
    key: str
    value: Any
    step: Optional[int] = None

class MetricCreate(MetricBase):
    run_id: int

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
    run_id: int

class ArtifactResponse(ArtifactBase):
    id: int
    run_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int

class VersionHistoryUpdateNotes(BaseModel):
    notes: Optional[str] = None
