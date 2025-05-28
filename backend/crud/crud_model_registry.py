from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models import database_models as models
from backend.models import schemas

# --- CRUD for RegisteredModel ---

def create_registered_model(db: Session, model: schemas.RegisteredModelCreate) -> models.RegisteredModel:
    db_model = models.RegisteredModel(
        name=model.name,
        description=model.description,
        project_id=model.project_id
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_registered_model(db: Session, model_id: int) -> Optional[models.RegisteredModel]:
    return db.query(models.RegisteredModel).filter(models.RegisteredModel.id == model_id).first()

def get_registered_model_by_name(db: Session, name: str) -> Optional[models.RegisteredModel]:
    return db.query(models.RegisteredModel).filter(models.RegisteredModel.name == name).first()

def get_registered_models(db: Session, skip: int = 0, limit: int = 100, project_id: Optional[int] = None) -> List[models.RegisteredModel]:
    query = db.query(models.RegisteredModel)
    if project_id:
        query = query.filter(models.RegisteredModel.project_id == project_id)
    return query.offset(skip).limit(limit).all()

def update_registered_model(db: Session, model_id: int, model_update: schemas.RegisteredModelUpdate) -> Optional[models.RegisteredModel]:
    db_model = db.query(models.RegisteredModel).filter(models.RegisteredModel.id == model_id).first()
    if db_model:
        update_data = model_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_model, key, value)
        db_model.updated_at = datetime.now()
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
    return db_model

def delete_registered_model(db: Session, model_id: int) -> Optional[models.RegisteredModel]:
    db_model = db.query(models.RegisteredModel).filter(models.RegisteredModel.id == model_id).first()
    if db_model:
        db.delete(db_model)
        db.commit()
    return db_model

# --- CRUD for ModelVersion ---

def create_model_version(db: Session, model_version: schemas.ModelVersionCreate) -> models.ModelVersion:
    # Determine the next version number for this registered model
    max_version = db.query(func.max(models.ModelVersion.version)).filter(
        models.ModelVersion.registered_model_id == model_version.registered_model_id
    ).scalar()
    new_version = (max_version or 0) + 1

    db_model_version = models.ModelVersion(
        registered_model_id=model_version.registered_model_id,
        version=new_version,
        run_id=model_version.run_id,
        model_path=model_version.model_path,
        model_framework=model_version.model_framework,
        model_signature=model_version.model_signature,
        model_metadata=model_version.model_metadata,
        stage=model_version.stage,
        user_id=model_version.user_id
    )
    db.add(db_model_version)
    db.commit()
    db.refresh(db_model_version)
    return db_model_version

def get_model_version(db: Session, version_id: int) -> Optional[models.ModelVersion]:
    return db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()

def get_model_version_by_registered_model_and_version(db: Session, registered_model_id: int, version: int) -> Optional[models.ModelVersion]:
    return db.query(models.ModelVersion).filter(
        models.ModelVersion.registered_model_id == registered_model_id,
        models.ModelVersion.version == version
    ).first()

def get_model_versions_by_registered_model(db: Session, registered_model_id: int, skip: int = 0, limit: int = 100) -> List[models.ModelVersion]:
    return db.query(models.ModelVersion).filter(models.ModelVersion.registered_model_id == registered_model_id).order_by(models.ModelVersion.version.desc()).offset(skip).limit(limit).all()

def get_latest_model_version(db: Session, registered_model_id: int) -> Optional[models.ModelVersion]:
    return db.query(models.ModelVersion).filter(
        models.ModelVersion.registered_model_id == registered_model_id
    ).order_by(models.ModelVersion.version.desc()).first()

def update_model_version(db: Session, version_id: int, version_update: schemas.ModelVersionUpdate) -> Optional[models.ModelVersion]:
    db_model_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()
    if db_model_version:
        update_data = version_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_model_version, key, value)
        db_model_version.updated_at = datetime.now()
        db.add(db_model_version)
        db.commit()
        db.refresh(db_model_version)
    return db_model_version

def delete_model_version(db: Session, version_id: int) -> Optional[models.ModelVersion]:
    db_model_version = db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()
    if db_model_version:
        db.delete(db_model_version)
        db.commit()
    return db_model_version
