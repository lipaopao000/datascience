from sqlalchemy.orm import Session
from typing import Optional, List

from backend.models import database_models as models
from backend.models import schemas

def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return db.query(models.Project).filter(models.Project.owner_id == owner_id).offset(skip).limit(limit).all()

def get_all_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    """
    Retrieve all projects, typically for admin users.
    """
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate, owner_id: int) -> models.Project:
    db_project = models.Project(
        **project.model_dump(),
        owner_id=owner_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: int, project_update: schemas.ProjectUpdate, owner_id: int) -> Optional[models.Project]:
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not db_project:
        return None
    
    # Optional: Check if the user attempting the update is the owner or an admin
    # For now, we assume this check is done at the router level or via permissions.
    # if db_project.owner_id != owner_id: # and not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not authorized to update this project")

    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
        
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int, owner_id: int) -> Optional[models.Project]:
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    
    if not db_project:
        return None

    # Optional: Check ownership before deletion
    # if db_project.owner_id != owner_id: # and not current_user.is_superuser:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this project")
        
    # Consider what to do with related entities (e.g., VersionHistory)
    # Cascading deletes can be set up in SQLAlchemy models, or handled here.
    # For now, we'll just delete the project.
    
    db.delete(db_project)
    db.commit()
    return db_project
