from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.sql import func
import os

from backend.core.config import settings # Import settings

# Use SQLALCHEMY_DATABASE_URL from settings
DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Global variable to hold the test session local, if set by conftest
_test_session_local = None

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="projects")
    versions = relationship("VersionHistory", back_populates="project")
    # Add relationships to data, models, parameters if they become separate tables linked to projects

class VersionHistory(Base):
    __tablename__ = "version_history"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # e.g., "data", "model", "parameters"
    entity_id = Column(String, nullable=False)    # ID of the data, model, or parameter set
    version = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    version_metadata = Column(JSON, nullable=True) # Stores parameters, config, small data. Can be null if only file.
    file_identifier = Column(String, nullable=True) # e.g., "dataset_v1.csv", "model_v3.pkl"
    display_name = Column(String, nullable=True) # User-editable name for the versioned entity
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # user_id = Column(Integer, ForeignKey("users.id")) # Optional: who made the version

    project = relationship("Project", back_populates="versions")
    # user = relationship("User") # Optional

    __table_args__ = (UniqueConstraint('project_id', 'entity_type', 'entity_id', 'version', name='_project_entity_version_uc'),)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False) # Store value as JSON to accommodate various types
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# --- Experiment Tracking Models ---

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True) # Link to a project
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="experiments")
    runs = relationship("Run", back_populates="experiment", cascade="all, delete-orphan")

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    run_name = Column(String, index=True, nullable=True) # e.g., "run-2023-10-27-10-30"
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="RUNNING") # e.g., "RUNNING", "COMPLETED", "FAILED", "KILLED"
    source_type = Column(String, nullable=True) # e.g., "CODE", "NOTEBOOK", "DOCKER"
    source_name = Column(String, nullable=True) # e.g., "train_script.py", "my_notebook.ipynb"
    git_commit = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Who initiated the run
    artifact_location = Column(String, nullable=True) # Base path for artifacts for this run
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    experiment = relationship("Experiment", back_populates="runs")
    user = relationship("User", backref="runs")
    parameters = relationship("Parameter", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

class Parameter(Base):
    __tablename__ = "parameters"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False) # Store as Text to accommodate various types (e.g., JSON string)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    run = relationship("Run", back_populates="parameters")

    __table_args__ = (UniqueConstraint('run_id', 'key', name='_run_parameter_uc'),)

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False) # Use JSON to store float, int, or even list/dict if needed
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) # When the metric was logged
    step = Column(Integer, nullable=True) # For metrics logged over training steps (e.g., epoch, batch)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    run = relationship("Run", back_populates="metrics")

    __table_args__ = (UniqueConstraint('run_id', 'key', 'step', name='_run_metric_step_uc'),) # Unique per run, key, and step

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    path = Column(String, nullable=False) # Relative path within the run's artifact_location
    file_type = Column(String, nullable=False) # e.g., "model", "plot", "data", "log", "checkpoint"
    file_size = Column(Integer, nullable=True) # Size in bytes
    checksum = Column(String, nullable=True) # MD5 or SHA256 hash of the file
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    run = relationship("Run", back_populates="artifacts")

    __table_args__ = (UniqueConstraint('run_id', 'path', name='_run_artifact_path_uc'),)


# --- Model Registry Models ---

class RegisteredModel(Base):
    __tablename__ = "registered_models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True) # Link to a project
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", backref="registered_models")
    versions = relationship("ModelVersion", back_populates="registered_model", cascade="all, delete-orphan")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(Integer, primary_key=True, index=True)
    registered_model_id = Column(Integer, ForeignKey("registered_models.id"), nullable=False)
    version = Column(Integer, nullable=False) # Auto-incrementing version within a registered model
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=True) # Link to the experiment run that produced this model
    model_path = Column(String, nullable=False) # Path to the actual model file (e.g., S3 URI or local path)
    model_framework = Column(String, nullable=True) # e.g., "scikit-learn", "tensorflow", "pytorch"
    model_signature = Column(JSON, nullable=True) # Input/output schema of the model
    model_metadata = Column(JSON, nullable=True) # Any other relevant metadata
    stage = Column(String, nullable=False, default="None") # e.g., "None", "Staging", "Production", "Archived"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Who registered this version
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    registered_model = relationship("RegisteredModel", back_populates="versions")
    run = relationship("Run", backref="model_versions")
    user = relationship("User", backref="model_versions")

    __table_args__ = (UniqueConstraint('registered_model_id', 'version', name='_registered_model_version_uc'),)


def create_db_and_tables():
    # This function is typically used for initial setup or testing, not for production schema management.
    # In a production environment, Alembic migrations should be used to manage the database schema.
    Base.metadata.create_all(bind=engine)
