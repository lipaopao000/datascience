from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Annotated # Import Optional and Annotated
from sqlalchemy.orm import Session # Import Session
from backend.models.schemas import DataSchemaCreate, DataSchemaResponse, DataSchemaUpdate
from backend.services.schema_service import SchemaService
from backend.core import security # Import security for user dependency
from backend.crud import crud_project # Import crud_project for project authorization
from backend.models import database_models as models # Import models for User
from backend.models.database_models import get_db # Import get_db

router = APIRouter(
    prefix="/projects/{project_id}/schemas", # New project-scoped prefix
    tags=["Project Schemas"], # Updated tag
    dependencies=[Depends(security.get_current_active_user)], # All routes require active user
)

# This is a placeholder for the actual schema_service instance
# It will be overridden by the dependency override in main.py for testing/injection
_schema_service_instance: Optional[SchemaService] = None

def get_schema_service(db: Session = Depends(get_db)) -> SchemaService: # Pass db to service
    print(f"DEBUG: get_schema_service called. _schema_service_instance is: {_schema_service_instance}")
    if _schema_service_instance is None:
        # Re-instantiate if not set, though main.py should handle this
        from backend.services.data_processor import DataProcessor
        _schema_service_instance = SchemaService(data_processor_instance=DataProcessor(schema_service_instance=None))
        _schema_service_instance.data_processor.schema_service = _schema_service_instance
    return _schema_service_instance

# Dependency to check project access
def verify_project_access(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    db_project = crud_project.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_superuser and db_project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this project")
    return db_project # Return project for further use if needed

# Define common dependencies as variables to simplify endpoint signatures
active_user = Depends(security.get_current_active_user)
get_db_session = Depends(get_db)
get_schema_service_instance = Depends(get_schema_service)
verify_project_access_dependency = Depends(verify_project_access)


@router.post("/", response_model=DataSchemaResponse, status_code=status.HTTP_201_CREATED)
async def create_schema_endpoint(
    project_id: int,
    schema_data: DataSchemaCreate,
    current_user: Annotated[models.User, active_user], # Moved to be before other default args if it's a dependency
    db_project: models.Project = verify_project_access_dependency,
    schema_service: SchemaService = get_schema_service_instance,
):
    try:
        # Pass project_id to the service method
        return schema_service.create_schema(project_id=project_id, schema_data=schema_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建数据模式失败: {str(e)}")

@router.get("/", response_model=List[DataSchemaResponse])
async def get_schemas_endpoint(
    project_id: int,
    current_user: Annotated[models.User, active_user],
    db_project: models.Project = verify_project_access_dependency,
    schema_service: SchemaService = get_schema_service_instance,
):
    try:
        # Pass project_id to the service method
        return schema_service.get_schemas(project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据模式列表失败: {str(e)}")

@router.get("/{schema_id}", response_model=DataSchemaResponse)
async def get_schema_endpoint(
    project_id: int,
    schema_id: str,
    current_user: Annotated[models.User, active_user],
    db_project: models.Project = verify_project_access_dependency,
    schema_service: SchemaService = get_schema_service_instance,
):
    try:
        # Pass project_id to the service method
        schema = schema_service.get_schema(project_id=project_id, schema_id=schema_id)
        if not schema:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return schema
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据模式失败: {str(e)}")

@router.put("/{schema_id}", response_model=DataSchemaResponse)
async def update_schema_endpoint(
    project_id: int,
    schema_id: str,
    schema_data: DataSchemaUpdate,
    current_user: Annotated[models.User, active_user],
    db_project: models.Project = verify_project_access_dependency,
    schema_service: SchemaService = get_schema_service_instance,
):
    try:
        # Pass project_id to the service method
        updated_schema = schema_service.update_schema(project_id=project_id, schema_id=schema_id, schema_data=schema_data)
        if not updated_schema:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return updated_schema
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新数据模式失败: {str(e)}")

@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema_endpoint(
    project_id: int,
    schema_id: str,
    current_user: Annotated[models.User, active_user],
    db_project: models.Project = verify_project_access_dependency,
    schema_service: SchemaService = get_schema_service_instance,
):
    try:
        # Pass project_id to the service method
        if not schema_service.delete_schema(project_id=project_id, schema_id=schema_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除数据模式失败: {str(e)}")
