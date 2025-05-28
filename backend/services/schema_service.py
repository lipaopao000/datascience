import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.models.schemas import DataSchemaCreate, DataSchemaResponse, DataSchemaUpdate, ColumnDefinition
# Removed: from services.data_processor import DataProcessor # Import DataProcessor

SCHEMAS_DIR = "data/schemas"
os.makedirs(SCHEMAS_DIR, exist_ok=True)

class SchemaService:
    def __init__(self, data_processor_instance): # Accept DataProcessor instance
        self.data_processor = data_processor_instance

    def _get_schema_path(self, schema_id: str) -> str:
        return os.path.join(SCHEMAS_DIR, f"{schema_id}.json")

    def create_schema(self, schema_data: DataSchemaCreate) -> DataSchemaResponse:
        schema_id = str(uuid.uuid4())
        
        full_schema_data = schema_data.dict()
        full_schema_data["id"] = schema_id
        full_schema_data["created_at"] = datetime.now().isoformat()
        full_schema_data["updated_at"] = datetime.now().isoformat()

        if schema_data.schema_type == "standard":
            if not schema_data.columns: # Check if columns list exists and is not empty
                raise ValueError("Standard schema type requires column definitions.")
            # Basic validation for column names and types for standard schema
            for col in schema_data.columns:
                if not col.name or not col.type:
                    raise ValueError("Column name and type cannot be empty for standard schema.")
                if col.type not in ["string", "number", "datetime", "boolean"]:
                    raise ValueError(f"Invalid column type: {col.type}")
            full_schema_data["columns"] = [col.dict() for col in schema_data.columns]
        elif schema_data.schema_type == "high_frequency_wide":
            # Ensure columns is None for this type, as it's defined by other fields
            full_schema_data["columns"] = None 
            if not all([
                isinstance(schema_data.time_column_index, int),
                isinstance(schema_data.data_start_column_index, int),
                isinstance(schema_data.num_data_columns, int),
                schema_data.data_column_base_name,
                isinstance(schema_data.sampling_rate_hz, float)
            ]):
                raise ValueError("High-frequency wide schema requires time_column_index, data_start_column_index, num_data_columns, data_column_base_name, and sampling_rate_hz.")
            full_schema_data["columns"] = None # Explicitly set to None if not standard
        else:
            raise ValueError(f"Invalid schema_type: {schema_data.schema_type}")
        
        file_path = self._get_schema_path(schema_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_schema_data, f, ensure_ascii=False, indent=2)
        
        return DataSchemaResponse(**full_schema_data)

    def get_schemas(self) -> List[DataSchemaResponse]:
        schemas = []
        for filename in os.listdir(SCHEMAS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(SCHEMAS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                        schemas.append(DataSchemaResponse(**schema_data))
                except Exception as e:
                    print(f"Error loading schema file {filename}: {e}") # Or use logger
        schemas.sort(key=lambda s: s.name) # Sort by name
        return schemas

    def get_schema(self, schema_id: str) -> Optional[DataSchemaResponse]:
        file_path = self._get_schema_path(schema_id)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
                return DataSchemaResponse(**schema_data)
        except Exception as e:
            print(f"Error loading schema file {schema_id}.json: {e}") # Or use logger
            return None

    def update_schema(self, schema_id: str, schema_update_data: DataSchemaUpdate) -> Optional[DataSchemaResponse]:
        file_path = self._get_schema_path(schema_id)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            current_schema_data = json.load(f)

        update_data = schema_update_data.dict(exclude_unset=True) # Get only provided fields
        
        for key, value in update_data.items():
            if value is not None: # Only update if value is provided
                if key == "columns" and current_schema_data.get("schema_type", "standard") == "standard":
                    if not value: # Empty list for columns
                         current_schema_data[key] = []
                         continue
                    validated_columns = []
                    for col_data in value:
                        col_def = ColumnDefinition(**col_data)
                        if not col_def.name or not col_def.type:
                            raise ValueError("Column name and type cannot be empty for standard schema.")
                        if col_def.type not in ["string", "number", "datetime", "boolean"]:
                            raise ValueError(f"Invalid column type: {col_def.type}")
                        validated_columns.append(col_def.dict())
                    current_schema_data[key] = validated_columns
                elif key == "schema_type":
                    if value not in ["standard", "high_frequency_wide"]:
                        raise ValueError(f"Invalid schema_type: {value}")
                    current_schema_data[key] = value
                    # If changing to high_frequency_wide, ensure columns is None or empty
                    if value == "high_frequency_wide":
                        current_schema_data["columns"] = None
                    # If changing to standard, ensure high_freq fields are None or not present
                    elif value == "standard":
                        for hf_key in ["time_column_index", "data_start_column_index", "num_data_columns", "data_column_base_name", "sampling_rate_hz"]:
                            current_schema_data.pop(hf_key, None)


                else:
                    current_schema_data[key] = value
        
        # Validate high_frequency_wide fields if type is set or being set to it
        if current_schema_data.get("schema_type") == "high_frequency_wide":
            if not all([
                isinstance(current_schema_data.get("time_column_index"), int),
                isinstance(current_schema_data.get("data_start_column_index"), int),
                isinstance(current_schema_data.get("num_data_columns"), int),
                current_schema_data.get("data_column_base_name"),
                isinstance(current_schema_data.get("sampling_rate_hz"), float)
            ]):
                # Allow partial updates, so don't raise error if not all fields are present yet during update
                pass # raise ValueError("High-frequency wide schema requires all specific fields to be set.")
            current_schema_data["columns"] = None # Ensure columns is None for this type

        current_schema_data["updated_at"] = datetime.now().isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(current_schema_data, f, ensure_ascii=False, indent=2)
            
        return DataSchemaResponse(**current_schema_data)

    def delete_schema(self, schema_id: str) -> bool:
        file_path = self._get_schema_path(schema_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
