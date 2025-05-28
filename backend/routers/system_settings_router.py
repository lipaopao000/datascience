from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from backend.models import database_models as models
from backend.models import schemas
from backend.crud import crud_system_setting
from backend.core import security
from backend.models.database_models import get_db

router = APIRouter(
    prefix="/api/v1/system-settings",
    tags=["system-settings"],
    dependencies=[Depends(security.get_current_active_superuser)], # All routes require superuser
)

@router.post("/", response_model=schemas.SystemSettingResponse, status_code=status.HTTP_201_CREATED)
def create_setting(
    setting: schemas.SystemSettingCreate, 
    db: Session = Depends(get_db)
):
    db_setting = crud_system_setting.get_setting(db, key=setting.key)
    if db_setting:
        raise HTTPException(status_code=400, detail=f"Setting with key '{setting.key}' already exists.")
    return crud_system_setting.create_setting(db=db, setting=setting)

@router.get("/", response_model=List[schemas.SystemSettingResponse])
def read_settings(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    settings = crud_system_setting.get_all_settings(db, skip=skip, limit=limit)
    return settings

@router.get("/{setting_key}", response_model=schemas.SystemSettingResponse)
def read_setting(
    setting_key: str, 
    db: Session = Depends(get_db)
):
    db_setting = crud_system_setting.get_setting(db, key=setting_key)
    if db_setting is None:
        raise HTTPException(status_code=404, detail=f"Setting with key '{setting_key}' not found.")
    return db_setting

@router.put("/{setting_key}", response_model=schemas.SystemSettingResponse)
def update_setting(
    setting_key: str, 
    setting_update: schemas.SystemSettingUpdate, 
    db: Session = Depends(get_db)
):
    updated_setting = crud_system_setting.update_setting(db, key=setting_key, setting_update=setting_update)
    if updated_setting is None:
        raise HTTPException(status_code=404, detail=f"Setting with key '{setting_key}' not found or update failed.")
    return updated_setting

@router.delete("/{setting_key}", response_model=schemas.SystemSettingResponse) # Or just status 204
def delete_setting(
    setting_key: str, 
    db: Session = Depends(get_db)
):
    # Be cautious with deleting settings, especially critical ones.
    # Consider adding checks or preventing deletion of certain keys.
    if setting_key == "data_save_path": # Example: prevent deletion of a critical key
         raise HTTPException(status_code=403, detail=f"Cannot delete critical system setting: '{setting_key}'. Please update it instead.")

    deleted_setting = crud_system_setting.delete_setting(db, key=setting_key)
    if deleted_setting is None:
        raise HTTPException(status_code=404, detail=f"Setting with key '{setting_key}' not found or delete failed.")
    return deleted_setting
