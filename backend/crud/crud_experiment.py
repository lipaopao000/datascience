from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models import database_models as models
from backend.models import schemas

# --- CRUD for Experiment ---

def create_experiment(db: Session, experiment: schemas.ExperimentCreate) -> models.Experiment:
    db_experiment = models.Experiment(
        name=experiment.name,
        description=experiment.description,
        project_id=experiment.project_id
    )
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment

def get_experiment(db: Session, experiment_id: int) -> Optional[models.Experiment]:
    return db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()

def get_experiment_by_name(db: Session, name: str) -> Optional[models.Experiment]:
    return db.query(models.Experiment).filter(models.Experiment.name == name).first()

def get_experiments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Experiment]:
    return db.query(models.Experiment).offset(skip).limit(limit).all()

def get_experiments_by_project(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[models.Experiment]:
    return db.query(models.Experiment).filter(models.Experiment.project_id == project_id).offset(skip).limit(limit).all()

def update_experiment(db: Session, experiment_id: int, experiment_update: schemas.ExperimentCreate) -> Optional[models.Experiment]:
    db_experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if db_experiment:
        update_data = experiment_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_experiment, key, value)
        db_experiment.updated_at = datetime.now() # Manually update timestamp
        db.add(db_experiment)
        db.commit()
        db.refresh(db_experiment)
    return db_experiment

def delete_experiment(db: Session, experiment_id: int) -> Optional[models.Experiment]:
    db_experiment = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if db_experiment:
        db.delete(db_experiment)
        db.commit()
    return db_experiment

# --- CRUD for Run ---

def create_run(db: Session, run: schemas.RunCreate) -> models.Run:
    db_run = models.Run(
        experiment_id=run.experiment_id,
        run_name=run.run_name,
        status=run.status,
        source_type=run.source_type,
        source_name=run.source_name,
        git_commit=run.git_commit,
        user_id=run.user_id,
        artifact_location=run.artifact_location
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

def get_run(db: Session, run_id: int) -> Optional[models.Run]:
    return db.query(models.Run).filter(models.Run.id == run_id).first()

def get_runs_by_experiment(db: Session, experiment_id: int, skip: int = 0, limit: int = 100) -> List[models.Run]:
    return db.query(models.Run).filter(models.Run.experiment_id == experiment_id).offset(skip).limit(limit).all()

def update_run(db: Session, run_id: int, run_update: schemas.RunUpdate) -> Optional[models.Run]:
    db_run = db.query(models.Run).filter(models.Run.id == run_id).first()
    if db_run:
        update_data = run_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_run, key, value)
        db_run.updated_at = datetime.now()
        db.add(db_run)
        db.commit()
        db.refresh(db_run)
    return db_run

def delete_run(db: Session, run_id: int) -> Optional[models.Run]:
    db_run = db.query(models.Run).filter(models.Run.id == run_id).first()
    if db_run:
        db.delete(db_run)
        db.commit()
    return db_run

# --- CRUD for Parameter ---

def create_parameter(db: Session, parameter: schemas.ParameterCreate) -> models.Parameter:
    db_parameter = models.Parameter(
        run_id=parameter.run_id,
        key=parameter.key,
        value=parameter.value
    )
    db.add(db_parameter)
    db.commit()
    db.refresh(db_parameter)
    return db_parameter

def get_parameter(db: Session, parameter_id: int) -> Optional[models.Parameter]:
    return db.query(models.Parameter).filter(models.Parameter.id == parameter_id).first()

def get_parameters_by_run(db: Session, run_id: int, skip: int = 0, limit: int = 100) -> List[models.Parameter]:
    return db.query(models.Parameter).filter(models.Parameter.run_id == run_id).offset(skip).limit(limit).all()

# No update for parameter, usually parameters are immutable for a run.
# If a parameter needs to change, it's often a new run or a new parameter entry.

def delete_parameter(db: Session, parameter_id: int) -> Optional[models.Parameter]:
    db_parameter = db.query(models.Parameter).filter(models.Parameter.id == parameter_id).first()
    if db_parameter:
        db.delete(db_parameter)
        db.commit()
    return db_parameter

# --- CRUD for Metric ---

def create_metric(db: Session, metric: schemas.MetricCreate) -> models.Metric:
    db_metric = models.Metric(
        run_id=metric.run_id,
        key=metric.key,
        value=metric.value,
        step=metric.step
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

def get_metric(db: Session, metric_id: int) -> Optional[models.Metric]:
    return db.query(models.Metric).filter(models.Metric.id == metric_id).first()

def get_metrics_by_run(db: Session, run_id: int, skip: int = 0, limit: int = 100) -> List[models.Metric]:
    return db.query(models.Metric).filter(models.Metric.run_id == run_id).offset(skip).limit(limit).all()

# Metrics are usually immutable once logged. No update function.

def delete_metric(db: Session, metric_id: int) -> Optional[models.Metric]:
    db_metric = db.query(models.Metric).filter(models.Metric.id == metric_id).first()
    if db_metric:
        db.delete(db_metric)
        db.commit()
    return db_metric

# --- CRUD for Artifact ---

def create_artifact(db: Session, artifact: schemas.ArtifactCreate) -> models.Artifact:
    db_artifact = models.Artifact(
        run_id=artifact.run_id,
        path=artifact.path,
        file_type=artifact.file_type,
        file_size=artifact.file_size,
        checksum=artifact.checksum
    )
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    return db_artifact

def get_artifact(db: Session, artifact_id: int) -> Optional[models.Artifact]:
    return db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()

def get_artifacts_by_run(db: Session, run_id: int, skip: int = 0, limit: int = 100) -> List[models.Artifact]:
    return db.query(models.Artifact).filter(models.Artifact.run_id == run_id).offset(skip).limit(limit).all()

# Artifacts are usually immutable once logged. No update function.

def delete_artifact(db: Session, artifact_id: int) -> Optional[models.Artifact]:
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact:
        db.delete(db_artifact)
        db.commit()
    return db_artifact
