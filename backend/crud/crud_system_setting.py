from sqlalchemy.orm import Session
from typing import Optional, List, Any

from backend.models import database_models as models
from backend.models import schemas

def get_setting(db: Session, key: str) -> Optional[models.SystemSetting]:
    return db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()

def get_all_settings(db: Session, skip: int = 0, limit: int = 100) -> List[models.SystemSetting]:
    return db.query(models.SystemSetting).offset(skip).limit(limit).all()

def create_setting(db: Session, setting: schemas.SystemSettingCreate) -> models.SystemSetting:
    db_setting = models.SystemSetting(
        key=setting.key,
        value=setting.value,
        description=setting.description
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def update_setting(db: Session, key: str, setting_update: schemas.SystemSettingUpdate) -> Optional[models.SystemSetting]:
    db_setting = get_setting(db, key)
    if not db_setting:
        return None
    
    update_data = setting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_setting, field, value)
        
    db.commit()
    db.refresh(db_setting)
    return db_setting

def delete_setting(db: Session, key: str) -> Optional[models.SystemSetting]:
    db_setting = get_setting(db, key)
    if db_setting:
        db.delete(db_setting)
        db.commit()
    return db_setting

# Helper to get a specific setting's value directly
def get_setting_value(db: Session, key: str, default: Any = None) -> Any:
    setting = get_setting(db, key)
    if setting:
        return setting.value
    return default
