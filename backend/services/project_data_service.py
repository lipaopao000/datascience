import os
import shutil # Added shutil
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List # Added List
from sqlalchemy.orm import Session
import logging
import uuid 

from backend.crud import crud_version_history, crud_system_setting
from backend.core.storage_utils import get_versioned_data_path
from backend.models import schemas # Changed to import schemas directly for VersionHistoryCreate
from backend.models.schemas import VersionHistoryResponse 

from sklearn.feature_extraction.text import TfidfVectorizer # Added for TF-IDF

logger = logging.getLogger(__name__)

class ProjectDataService:
    def __init__(self, db: Session):
        self.db = db

    def load_data_from_version(
        self, 
        project_id: int, 
        entity_id: str, # This is the data_entity_id (UUID)
        version_number: int
    ) -> Optional[pd.DataFrame]:
        """
        Loads a specific version of a data entity (e.g., a CSV or PKL file) for a project.
        Returns a pandas DataFrame if successful, None otherwise.
        """
        version_entry = crud_version_history.get_specific_version(
            self.db,
            project_id=project_id,
            entity_type="data", # Assuming this service is for "data" entities
            entity_id=entity_id,
            version=version_number
        )

        if not version_entry or not version_entry.file_identifier:
            logger.warning(
                f"No version entry or file_identifier found for project {project_id}, "
                f"entity {entity_id}, version {version_number}."
            )
            return None

        file_path = get_versioned_data_path(
            self.db,
            project_id=project_id,
            entity_type="data",
            entity_id=entity_id,
            version=version_number,
            filename=version_entry.file_identifier
        )

        if not os.path.exists(file_path):
            logger.error(f"File not found at versioned path: {file_path}")
            return None

        try:
            if version_entry.file_identifier.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif version_entry.file_identifier.endswith(".pkl"):
                # Assuming .pkl files store DataFrames directly or in a known structure
                # This might need adjustment if .pkl structure varies (e.g. dict with 'df' key)
                loaded_content = pd.read_pickle(file_path)
                if isinstance(loaded_content, pd.DataFrame):
                    df = loaded_content
                elif isinstance(loaded_content, dict) and 'df' in loaded_content: # Common pattern
                    df = loaded_content['df']
                else:
                    logger.error(f"Unrecognized content in PKL file: {file_path}")
                    return None
            else:
                logger.error(f"Unsupported file type for loading: {version_entry.file_identifier}")
                return None
            
            logger.info(f"Successfully loaded data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}", exc_info=True)
            return None

    def upload_and_version_data(
        self,
        project_id: int,
        file_content: bytes,
        original_filename: str,
        user_id: Optional[int] = None,
        notes: Optional[str] = "Initial data upload"
    ) -> Optional[VersionHistoryResponse]:
        """
        Handles uploaded data, saves it to storage, and creates an initial version history entry.
        """
        # 1. Determine a unique entity_id for this new data asset
        data_entity_id = str(uuid.uuid4())
        
        # 2. Determine the initial version number (always 1 for a new entity)
        new_version_number = 1
        
        # 3. Determine the storage path for this initial version
        # Use the original filename for the stored file
        stored_filename = original_filename # Or sanitize/rename if needed
        versioned_file_path = get_versioned_data_path(
            self.db, project_id, "data", data_entity_id, new_version_number, stored_filename
        )
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(versioned_file_path), exist_ok=True)

        # 4. Save the file content to the determined path
        try:
            with open(versioned_file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"Saved uploaded file to {versioned_file_path}")
        except Exception as e:
            logger.error(f"Failed to save uploaded file to {versioned_file_path}: {e}", exc_info=True)
            return None

        # 5. Optionally, read the file to extract metadata (e.g., columns, shape)
        # This part can be expanded based on file type (CSV, Excel, etc.)
        file_metadata = {}
        try:
            if stored_filename.endswith(".csv"):
                df = pd.read_csv(versioned_file_path)
                file_metadata["columns"] = df.columns.tolist()
                file_metadata["shape"] = list(df.shape)
                file_metadata["records"] = len(df)
                file_metadata["content_type"] = "text/csv"
            elif stored_filename.endswith(".pkl"):
                # For PKL, we might not want to load the whole thing just for metadata
                # Or load it if it's small enough
                file_metadata["content_type"] = "application/octet-stream"
            # Add other file types as needed
        except Exception as e:
            logger.warning(f"Could not extract metadata from {stored_filename}: {e}")
            file_metadata["parsing_error"] = str(e)

        # 6. Create a VersionHistory entry
        version_metadata = {
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "size_bytes": versioned_file_path.stat().st_size,
            **file_metadata # Include extracted metadata
        }
        
        version_create_payload = schemas.VersionHistoryCreate(
            entity_type="data",
            entity_id=data_entity_id,
            notes=notes,
            version_metadata=version_metadata,
            file_identifier=stored_filename # The name of the file as stored
        )
        
        new_db_entry = crud_version_history.create_version_history(
            self.db, project_id, version_create_payload
        )
        
        if not new_db_entry:
            # If DB entry creation fails, consider cleaning up the saved file
            os.remove(versioned_file_path)
            logger.error(f"Failed to create version history entry for {original_filename}. File deleted.")
            return None

        return schemas.VersionHistoryResponse.model_validate(new_db_entry)


    def clean_and_version_data(
        self,
        project_id: int,
        data_entity_id: str,
        source_version_number: int,
        cleaning_config: Dict[str, Any], # Simplified config for now
        notes: Optional[str] = "Cleaned data"
    ) -> Optional[VersionHistoryResponse]:
        """
        Loads a specific version of data, applies cleaning, and saves it as a new version.
        """
        # 1. Load the source data version
        source_df = self.load_data_from_version(
            project_id=project_id,
            entity_id=data_entity_id,
            version_number=source_version_number
        )
        if source_df is None:
            logger.error(f"Source data version {source_version_number} for entity {data_entity_id} not found.")
            return None

        # 2. Perform Cleaning (Placeholder for actual cleaning logic)
        # In a real scenario, this would use a more sophisticated cleaning service/library.
        cleaned_df = source_df.copy()

        # 1. Duplicate Row Handling
        duplicate_config = cleaning_config.get("drop_duplicates")
        if isinstance(duplicate_config, dict):
            subset = duplicate_config.get("subset")
            keep = duplicate_config.get("keep", "first")
            if keep not in ['first', 'last', False]:
                keep = 'first' # Default to 'first' if invalid
            
            initial_rows = len(cleaned_df)
            cleaned_df.drop_duplicates(subset=subset, keep=keep, inplace=True)
            rows_removed = initial_rows - len(cleaned_df)
            if rows_removed > 0:
                logger.info(f"Removed {rows_removed} duplicate rows. Config: subset={subset}, keep={keep}")

        # 2. Data Type Conversion
        type_conversion_config = cleaning_config.get("type_conversions", {})
        for col_name, conv_config in type_conversion_config.items():
            if col_name in cleaned_df.columns:
                to_type = conv_config.get("to_type")
                errors = conv_config.get("errors", "coerce") # Default to coerce for numeric/datetime
                
                if to_type == "numeric":
                    cleaned_df[col_name] = pd.to_numeric(cleaned_df[col_name], errors=errors)
                    logger.info(f"Attempted numeric conversion for column '{col_name}' with errors='{errors}'.")
                elif to_type == "datetime":
                    dt_format = conv_config.get("format")
                    cleaned_df[col_name] = pd.to_datetime(cleaned_df[col_name], format=dt_format, errors=errors)
                    logger.info(f"Attempted datetime conversion for column '{col_name}' with format='{dt_format}', errors='{errors}'.")
                elif to_type == "string":
                    cleaned_df[col_name] = cleaned_df[col_name].astype(str)
                    logger.info(f"Converted column '{col_name}' to string type.")
                else:
                    logger.warning(f"Unsupported 'to_type': {to_type} for column '{col_name}'. Skipping conversion.")
            else:
                logger.warning(f"Column '{col_name}' for type conversion not found in DataFrame. Skipping.")


        # 3. Global NA handling (existing logic)
        if cleaning_config.get("drop_na_all_rows"): # Drop rows where ALL values are NA
            cleaned_df.dropna(how='all', inplace=True)
            logger.info(f"After drop_na_all_rows: {cleaned_df.shape}")

        if cleaning_config.get("drop_na_any_rows"): # Drop rows where ANY value is NA
            cleaned_df.dropna(how='any', inplace=True)
            logger.info(f"After drop_na_any_rows: {cleaned_df.shape}")
        
        global_fill_na_value = cleaning_config.get("fill_na_global_value")
        if global_fill_na_value is not None: # Check for None explicitly, as 0 is a valid fill value
            cleaned_df.fillna(global_fill_na_value, inplace=True)
            logger.info(f"After global_fill_na_value with {global_fill_na_value}: {cleaned_df.shape}")

        # Per-column NA handling
        column_specific_na_config = cleaning_config.get("column_na_handling", {})
        for col_name, col_config in column_specific_na_config.items():
            if col_name in cleaned_df.columns:
                fill_method = col_config.get("fill_method")
                fill_value = col_config.get("fill_value")
                
                if fill_method == "mean":
                    if pd.api.types.is_numeric_dtype(cleaned_df[col_name]):
                        cleaned_df[col_name].fillna(cleaned_df[col_name].mean(), inplace=True)
                    else:
                        logger.warning(f"Cannot fill with mean for non-numeric column '{col_name}'. Skipping.")
                elif fill_method == "median":
                    if pd.api.types.is_numeric_dtype(cleaned_df[col_name]):
                        cleaned_df[col_name].fillna(cleaned_df[col_name].median(), inplace=True)
                    else:
                        logger.warning(f"Cannot fill with median for non-numeric column '{col_name}'. Skipping.")
                elif fill_method == "mode":
                    cleaned_df[col_name].fillna(cleaned_df[col_name].mode().iloc[0] if not cleaned_df[col_name].mode().empty else None, inplace=True)
                elif fill_value is not None: # Explicit fill value for column
                    cleaned_df[col_name].fillna(fill_value, inplace=True)
                logger.info(f"Applied NA handling for column '{col_name}'.")

        # Outlier removal (IQR example)
        outlier_config = cleaning_config.get("remove_outliers_iqr")
        if outlier_config and isinstance(outlier_config, dict):
            columns_to_check = outlier_config.get("columns", [])
            multiplier = outlier_config.get("multiplier", 1.5)
            for col_name in columns_to_check:
                if col_name in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[col_name]):
                    Q1 = cleaned_df[col_name].quantile(0.25)
                    Q3 = cleaned_df[col_name].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - multiplier * IQR
                    upper_bound = Q3 + multiplier * IQR
                    
                    # Filter out outliers
                    initial_rows = len(cleaned_df)
                    cleaned_df = cleaned_df[
                        (cleaned_df[col_name] >= lower_bound) & (cleaned_df[col_name] <= upper_bound)
                    ]
                    rows_removed = initial_rows - len(cleaned_df)
                    if rows_removed > 0:
                        logger.info(f"Removed {rows_removed} outliers from column '{col_name}' using IQR method.")
                else:
                    logger.warning(f"Cannot apply IQR outlier removal to non-numeric or non-existent column '{col_name}'.")
        
        logger.info(f"Data cleaning applied. Original shape: {source_df.shape}, Cleaned shape: {cleaned_df.shape}")

        # 3. Determine new version number
        latest_version_entry = crud_version_history.get_latest_version_for_entity(
            self.db, project_id, "data", data_entity_id
        )
        new_version_number = (latest_version_entry.version + 1) if latest_version_entry else 1
        
        # 4. Save the cleaned DataFrame to a new versioned file
        # Assume cleaned data is saved in the same format (e.g., CSV) or decide on a standard (e.g., PKL)
        # For simplicity, let's assume we save as CSV.
        source_version_entry = crud_version_history.get_specific_version(
            self.db, project_id, "data", data_entity_id, source_version_number
        )
        original_filename = "cleaned_data.csv" # Default
        if source_version_entry and source_version_entry.file_identifier:
            base, ext = os.path.splitext(source_version_entry.file_identifier)
            original_filename = f"{base}_cleaned_v{new_version_number}{ext}"
        
        cleaned_file_path = get_versioned_data_path(
            self.db, project_id, "data", data_entity_id, new_version_number, original_filename
        )
        
        try:
            # Save based on assumed format or add logic for format choice
            if original_filename.endswith(".csv"):
                cleaned_df.to_csv(cleaned_file_path, index=False)
            elif original_filename.endswith(".pkl"):
                 pd.to_pickle(cleaned_df, cleaned_file_path) # Or save as {'df': cleaned_df, 'metadata': ...}
            else: # Default to CSV if extension is unknown or different
                temp_cleaned_filename = f"{Path(original_filename).stem}_cleaned_v{new_version_number}.csv"
                cleaned_file_path = get_versioned_data_path(
                    self.db, project_id, "data", data_entity_id, new_version_number, temp_cleaned_filename
                )
                cleaned_df.to_csv(cleaned_file_path, index=False)
                original_filename = temp_cleaned_filename # Update filename if changed

            logger.info(f"Saved cleaned data to {cleaned_file_path}")
        except Exception as e:
            logger.error(f"Failed to save cleaned data to {cleaned_file_path}: {e}", exc_info=True)
            return None

        # 5. Create a new VersionHistory entry for the cleaned data
        version_metadata = {
            "source_entity_id": data_entity_id,
            "source_version": source_version_number,
            "cleaning_config_applied": cleaning_config,
            "original_filename": original_filename, # The name of the saved cleaned file
            "content_type": "text/csv" if original_filename.endswith(".csv") else "application/octet-stream", # Adjust as needed
            "size_bytes": cleaned_file_path.stat().st_size,
        }
        
        version_create_payload = schemas.VersionHistoryCreate(
            entity_type="data",
            entity_id=data_entity_id, # Same entity, new version
            notes=notes,
            version_metadata=version_metadata,
            file_identifier=original_filename 
        )
        
        new_db_entry = crud_version_history.create_version_history(
            self.db, project_id, version_create_payload
        )
        
        # Convert SQLAlchemy model to Pydantic response model
        return VersionHistoryResponse.model_validate(new_db_entry)

    def rollback_to_version(
        self,
        project_id: int,
        data_entity_id: str,
        source_version_number: int,
        notes: Optional[str] = None
    ) -> Optional[VersionHistoryResponse]:
        """
        Creates a new version of a data entity by copying an existing version's file and metadata.
        Effectively "rolls back" to a previous state by making it the newest version.
        """
        # 1. Verify the source version exists and get its details
        source_version_entry = crud_version_history.get_specific_version(
            self.db, project_id, "data", data_entity_id, source_version_number
        )
        if not source_version_entry or not source_version_entry.file_identifier:
            logger.error(
                f"Source version {source_version_number} for entity {data_entity_id} (project {project_id}) "
                f"not found or has no associated file."
            )
            return None

        source_file_path = get_versioned_data_path(
            self.db,
            project_id,
            "data",
            data_entity_id,
            source_version_number,
            source_version_entry.file_identifier
        )
        if not os.path.exists(source_file_path):
            logger.error(f"Source file for rollback not found at {source_file_path}")
            return None

        # 2. Determine new version number
        latest_version_entry = crud_version_history.get_latest_version_for_entity(
            self.db, project_id, "data", data_entity_id
        )
        new_version_number = (latest_version_entry.version + 1) if latest_version_entry else 1
        
        # 3. Define path for the new version's file (same filename as source)
        new_version_file_path = get_versioned_data_path(
            self.db, project_id, "data", data_entity_id, new_version_number, source_version_entry.file_identifier
        )

        try:
            # 4. Copy the source file to the new version's path
            shutil.copy2(source_file_path, new_version_file_path) # copy2 preserves metadata
            logger.info(f"Copied data from {source_file_path} to {new_version_file_path} for rollback.")
        except Exception as e:
            logger.error(f"Failed to copy file for rollback: {e}", exc_info=True)
            return None

        # 5. Create a new VersionHistory entry for the rolled-back version
        rollback_notes = notes or f"Rolled back to version {source_version_number}"
        
        # Copy metadata from the source version, updating relevant fields
        new_version_metadata = source_version_entry.version_metadata.copy() if source_version_entry.version_metadata else {}
        new_version_metadata["rolled_back_from_version"] = source_version_number
        new_version_metadata["original_filename"] = source_version_entry.file_identifier # Keep original name
        if os.path.exists(new_version_file_path): # Update size if file exists
             new_version_metadata["size_bytes"] = new_version_file_path.stat().st_size


        version_create_payload = schemas.VersionHistoryCreate(
            entity_type="data",
            entity_id=data_entity_id,
            notes=rollback_notes,
            version_metadata=new_version_metadata,
            file_identifier=source_version_entry.file_identifier # Same file name
        )
        
        new_db_entry = crud_version_history.create_version_history(
            self.db, project_id, version_create_payload
        )
        
        return VersionHistoryResponse.model_validate(new_db_entry)

    def extract_and_version_features(
        self,
        project_id: int,
        source_data_entity_id: str,
        source_data_version: int,
        feature_config: Dict[str, List[str]], # From ProjectFeatureExtractionRequest
        notes: Optional[str] = "Extracted features"
    ) -> Optional[VersionHistoryResponse]:
        """
        Loads a specific version of data, extracts features, and saves features as a new entity and version.
        """
        # 1. Load the source data version
        source_df = self.load_data_from_version(
            project_id=project_id,
            entity_id=source_data_entity_id,
            version_number=source_data_version
        )
        if source_df is None:
            logger.error(
                f"Source data for feature extraction not found: project {project_id}, "
                f"entity {source_data_entity_id}, version {source_data_version}."
            )
            return None

        # 2. Perform Feature Extraction (Placeholder for actual feature extraction logic)
        # This would typically involve a dedicated FeatureExtractor class or library.
        # Implementing more concrete feature extraction based on config.
        processed_features_list = []
        final_feature_columns = []
        placeholder_notes = notes # Keep original notes, append errors if any

        try:
            # Numerical Passthrough
            numerical_cols = feature_config.get("numerical_passthrough", [])
            if numerical_cols:
                missing_numerical = [col for col in numerical_cols if col not in source_df.columns]
                if missing_numerical:
                    raise ValueError(f"Missing numerical columns for passthrough: {', '.join(missing_numerical)}")
                processed_features_list.append(source_df[numerical_cols].copy())
                final_feature_columns.extend(numerical_cols)
                logger.info(f"Processed numerical passthrough for columns: {numerical_cols}")

            # Categorical One-Hot Encoding
            onehot_cols = feature_config.get("categorical_onehot", [])
            if onehot_cols:
                missing_onehot = [col for col in onehot_cols if col not in source_df.columns]
                if missing_onehot:
                    raise ValueError(f"Missing categorical columns for one-hot encoding: {', '.join(missing_onehot)}")
                onehot_encoded_df = pd.get_dummies(source_df[onehot_cols], columns=onehot_cols, prefix=onehot_cols, dummy_na=False) # dummy_na=False by default
                processed_features_list.append(onehot_encoded_df)
                final_feature_columns.extend(onehot_encoded_df.columns.tolist())
                logger.info(f"Processed one-hot encoding for columns: {onehot_cols}")

            # Date/Time Feature Engineering
            datetime_cols_config = feature_config.get("datetime_features", {}) # Expects dict: {"col_name": ["year", "month", ...]} or just list of cols
            
            # Standardize to list of columns if not a dict
            datetime_cols_to_process = []
            if isinstance(datetime_cols_config, list): # Simple list of columns, extract all common features
                datetime_cols_to_process = datetime_cols_config
                default_dt_parts = ["year", "month", "day", "dayofweek", "hour"]
                datetime_cols_config = {col: default_dt_parts for col in datetime_cols_to_process}


            for col_name, parts_to_extract in datetime_cols_config.items():
                if col_name not in source_df.columns:
                    raise ValueError(f"Missing datetime column for feature engineering: {col_name}")
                
                # Ensure column is datetime
                datetime_series = pd.to_datetime(source_df[col_name], errors='coerce')
                if datetime_series.isnull().all(): # if all are NaT after conversion
                    logger.warning(f"Column '{col_name}' could not be converted to datetime or is all null. Skipping datetime feature extraction.")
                    continue

                temp_dt_features = pd.DataFrame()
                if "year" in parts_to_extract:
                    temp_dt_features[f"{col_name}_year"] = datetime_series.dt.year
                if "month" in parts_to_extract:
                    temp_dt_features[f"{col_name}_month"] = datetime_series.dt.month
                if "day" in parts_to_extract:
                    temp_dt_features[f"{col_name}_day"] = datetime_series.dt.day
                if "dayofweek" in parts_to_extract:
                    temp_dt_features[f"{col_name}_dayofweek"] = datetime_series.dt.dayofweek
                if "hour" in parts_to_extract:
                    temp_dt_features[f"{col_name}_hour"] = datetime_series.dt.hour
                # Add more parts as needed (e.g., weekofyear, quarter)
                
                if not temp_dt_features.empty:
                    processed_features_list.append(temp_dt_features)
                    final_feature_columns.extend(temp_dt_features.columns.tolist())
                    logger.info(f"Processed datetime features for column: {col_name}")
            
            if not processed_features_list:
                # If no features were specified or processed, this could be an issue or intended
                logger.warning("No features were processed based on the provided configuration.")
                features_df = pd.DataFrame(index=source_df.index) # Empty DataFrame with original index
            else:
                features_df = pd.concat(processed_features_list, axis=1)
            
            # Text Feature Engineering (TF-IDF)
            tfidf_config = feature_config.get("text_features_tfidf")
            if isinstance(tfidf_config, dict):
                text_col = tfidf_config.get("column")
                max_features = tfidf_config.get("max_features", 100) # Default max_features

                if text_col and text_col in source_df.columns:
                    if source_df[text_col].isnull().all():
                        logger.warning(f"Text column '{text_col}' for TF-IDF is all null. Skipping TF-IDF.")
                    else:
                        try:
                            # Ensure text column is string and fill NaNs with empty string for TfidfVectorizer
                            text_data = source_df[text_col].astype(str).fillna('') 
                            vectorizer = TfidfVectorizer(max_features=max_features)
                            tfidf_matrix = vectorizer.fit_transform(text_data)
                            feature_names = vectorizer.get_feature_names_out()
                            tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=[f"tfidf_{name}" for name in feature_names], index=source_df.index)
                            
                            # Concatenate with existing features_df
                            features_df = pd.concat([features_df, tfidf_df], axis=1)
                            final_feature_columns.extend(tfidf_df.columns.tolist())
                            logger.info(f"Processed TF-IDF for column: {text_col}. Added {len(tfidf_df.columns)} features. Shape after TF-IDF: {features_df.shape}")
                        except Exception as e_tfidf:
                             logger.error(f"Error during TF-IDF for column '{text_col}': {e_tfidf}", exc_info=True)
                             placeholder_notes = f"{placeholder_notes} (TF-IDF Error on '{text_col}': {str(e_tfidf)})"

                elif text_col:
                     logger.warning(f"Text column '{text_col}' for TF-IDF not found in DataFrame.")


            logger.info(f"Features extracted. Final shape: {features_df.shape}")

        except ValueError as ve: # Catch config errors specifically
            logger.error(f"Configuration error during feature extraction: {ve}", exc_info=True)
            placeholder_notes = f"{notes} (Configuration Error: {str(ve)})"
            features_df = pd.DataFrame() # Return empty DataFrame on config error
        except Exception as e:
            logger.error(f"Error during feature extraction: {e}", exc_info=True)
            placeholder_notes = f"{notes} (Extraction Error: {str(e)})"
            features_df = pd.DataFrame() # Empty DataFrame on other errors

        # 3. Create a new entity_id for these features
        features_entity_id = str(uuid.uuid4()) 

        # 4. Determine new version number for this new features entity (will be 1)
        # Since it's a new entity_id, version will always start at 1.
        new_version_number = 1
        
        # 5. Save the features DataFrame to a new versioned file
        # Features are often saved as PKL or CSV. Let's use PKL.
        features_filename = f"features_v{new_version_number}.pkl"
        features_file_path = get_versioned_data_path(
            self.db, project_id, "features", features_entity_id, new_version_number, features_filename
        )
        
        try:
            pd.to_pickle(features_df, features_file_path)
            logger.info(f"Saved features to {features_file_path}")
        except Exception as e:
            logger.error(f"Failed to save features to {features_file_path}: {e}", exc_info=True)
            return None

        # 6. Create a new VersionHistory entry for the features
        version_metadata = {
            "source_data_entity_id": source_data_entity_id,
            "source_data_version": source_data_version,
            "feature_extraction_config": feature_config,
            "original_filename": features_filename,
            "content_type": "application/octet-stream", # For PKL
            "size_bytes": features_file_path.stat().st_size,
            "features_shape": list(features_df.shape)
        }
        
        version_create_payload = schemas.VersionHistoryCreate( # Use the imported schemas
            entity_type="features", # New entity type
            entity_id=features_entity_id,
            notes=placeholder_notes,
            version_metadata=version_metadata,
            file_identifier=features_filename 
        )
        
        new_db_entry = crud_version_history.create_version_history(
            self.db, project_id, version_create_payload
        )
        
        return VersionHistoryResponse.model_validate(new_db_entry)
