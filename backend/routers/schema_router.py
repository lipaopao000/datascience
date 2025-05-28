from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional # Import Optional
from backend.models.schemas import DataSchemaCreate, DataSchemaResponse, DataSchemaUpdate
from backend.services.schema_service import SchemaService

router = APIRouter()

# This is a placeholder for the actual schema_service instance
# It will be overridden by the dependency override in main.py for testing/injection
_schema_service_instance: Optional[SchemaService] = None

def get_schema_service() -> SchemaService:
    print(f"DEBUG: get_schema_service called. _schema_service_instance is: {_schema_service_instance}")
    if _schema_service_instance is None:
        raise RuntimeError("SchemaService not initialized. Ensure it's set up in main.py")
    return _schema_service_instance

@router.post("/", response_model=DataSchemaResponse, status_code=status.HTTP_201_CREATED)
async def create_schema_endpoint(schema_data: DataSchemaCreate, schema_service: SchemaService = Depends(get_schema_service)):
    try:
        return schema_service.create_schema(schema_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建数据模式失败: {str(e)}")

@router.get("/", response_model=List[DataSchemaResponse])
async def get_schemas_endpoint(schema_service: SchemaService = Depends(get_schema_service)):
    try:
        return schema_service.get_schemas()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据模式列表失败: {str(e)}")

@router.get("/{schema_id}", response_model=DataSchemaResponse)
async def get_schema_endpoint(schema_id: str, schema_service: SchemaService = Depends(get_schema_service)):
    try:
        schema = schema_service.get_schema(schema_id)
        if not schema:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return schema
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据模式失败: {str(e)}")

@router.put("/{schema_id}", response_model=DataSchemaResponse)
async def update_schema_endpoint(schema_id: str, schema_data: DataSchemaUpdate, schema_service: SchemaService = Depends(get_schema_service)):
    try:
        updated_schema = schema_service.update_schema(schema_id, schema_data)
        if not updated_schema:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return updated_schema
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新数据模式失败: {str(e)}")

@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema_endpoint(schema_id: str, schema_service: SchemaService = Depends(get_schema_service)):
    try:
        if not schema_service.delete_schema(schema_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据模式未找到")
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除数据模式失败: {str(e)}")
