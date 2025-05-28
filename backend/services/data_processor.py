import os
import pandas as pd
import numpy as np
import glob
import zipfile
from tqdm import tqdm
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import re # Import re module
# Removed: from services.schema_service import SchemaService # Import SchemaService

logger = logging.getLogger(__name__)
# Removed: schema_service = SchemaService() # Instantiate SchemaService


class DataProcessor:
    def __init__(self, schema_service_instance=None): # Accept SchemaService instance
        self.processed_data_path = "data/processed"
        os.makedirs(self.processed_data_path, exist_ok=True)
        self.schema_service = schema_service_instance # Store SchemaService instance

    def clean_col_names(self, df):
        """清洗DataFrame的列名"""
        df.columns = ["_".join(col.split()) for col in df.columns]
        return df

    async def process_zip_file(self, zip_path: str, group_name: Optional[str] = None) -> Dict[str, Any]:
        """处理ZIP文件"""
        extract_to_folder = "temp_extracted_patient_data"
        os.makedirs(extract_to_folder, exist_ok=True)

        extracted_count = 0
        patient_count = 0

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                member_list = zip_ref.namelist()
                for member_name in tqdm(member_list, desc="解压ZIP文件"):
                    base_filename = os.path.basename(member_name)
                    if base_filename.endswith(".csv") and not member_name.endswith('/'):
                        try:
                            zip_ref.extract(member_name, extract_to_folder)
                            extracted_count += 1
                        except Exception as e:
                            print(f"解压文件 {member_name} 时出错: {e}")

            # 处理解压后的数据
            patient_count = await self._process_extracted_data(extract_to_folder, group_name=group_name)

            return {
                "patient_count": patient_count,
                "file_info": {
                    "extracted_files": extracted_count,
                    "source": "zip"
                }
            }

        except Exception as e:
            raise Exception(f"处理ZIP文件失败: {e}")
        finally:
            # 清理临时文件夹
            if os.path.exists(extract_to_folder):
                import shutil
                shutil.rmtree(extract_to_folder)


    async def process_csv_file(self, csv_path: str, group_name: Optional[str] = None) -> Dict[str, Any]:
        """处理单个CSV文件"""
        try:
            data_id = Path(csv_path).stem
            df = pd.read_csv(csv_path, on_bad_lines='skip')
            
            if df is None:
                raise ValueError("DataFrame could not be loaded.")

            print(f"DEBUG: DataFrame columns before clean_col_names for {data_id}: {df.columns.tolist()}")
            df = self.clean_col_names(df)
            print(f"DEBUG: DataFrame columns after clean_col_names for {data_id}: {df.columns.tolist()}")
            
            output_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
            metadata = {
                "data_id": data_id,
                "source_file": Path(csv_path).name,
                "upload_time": datetime.now().isoformat(),
                "group_name": group_name,
                "rows": len(df),
                "columns": df.columns.tolist(),
                "shape": list(df.shape)
            }
            data_to_save = {'df': df, 'metadata': metadata}

            print(f"DEBUG: Attempting to save processed CSV data to: {output_path}")
            pd.to_pickle(data_to_save, output_path)
            print(f"DEBUG: Successfully saved processed CSV data to: {output_path}")

            return {
                "patient_count": 1,
                "file_info": metadata
            }

        except Exception as e:
            raise Exception(f"处理CSV文件失败: {e}")

    async def _process_extracted_data(self, data_path: str, group_name: Optional[str] = None) -> int:
        """处理解压后的数据"""
        try:
            patient_ids = [pid for pid in os.listdir(data_path)
                           if os.path.isdir(os.path.join(data_path, pid))]

            for patient_id in tqdm(patient_ids, desc="处理患者数据"):
                patient_folder_path = os.path.join(data_path, patient_id)
                all_csv_files = []

                # 查找时间范围文件夹
                time_range_folders = []
                if os.path.isdir(patient_folder_path):
                    time_range_folders = sorted([
                        os.path.join(patient_folder_path, trf)
                        for trf in os.listdir(patient_folder_path)
                        if os.path.isdir(os.path.join(patient_folder_path, trf))
                    ])

                for time_folder_path in time_range_folders:
                    csv_files = glob.glob(os.path.join(time_folder_path, "*.csv"))
                    all_csv_files.extend(sorted(csv_files))

                # 如果在子文件夹中没找到，直接在患者目录下查找
                if not all_csv_files:
                    csv_files = glob.glob(os.path.join(patient_folder_path, "*.csv"))
                    all_csv_files.extend(sorted(csv_files))

                # 合并所有CSV数据
                patient_dfs = []
                for f_path in all_csv_files:
                    try:
                        df = pd.read_csv(f_path, on_bad_lines='skip')
                        df = self.clean_col_names(df)
                        patient_dfs.append(df)
                    except Exception as e:
                        print(f"处理文件 {f_path} 时出错: {e}")
                        continue

                if patient_dfs:
                    combined_df = pd.concat(patient_dfs, ignore_index=True)
                    # 保存处理后的数据
                    output_file_path = os.path.join(self.processed_data_path, f"{patient_id}_data.pkl")
                    
                    metadata = {
                        "data_id": patient_id,
                        "source_files": [Path(f).name for f in all_csv_files],
                        "upload_time": datetime.now().isoformat(),
                        "group_name": group_name,
                        "rows": len(combined_df),
                        "columns": combined_df.columns.tolist(),
                        "shape": list(combined_df.shape)
                    }
                    data_to_save = {'df': combined_df, 'metadata': metadata}

                    logger.info(f"Attempting to save processed ZIP data to: {output_file_path}")
                    pd.to_pickle(data_to_save, output_file_path)
                    logger.info(f"Successfully saved processed ZIP data to: {output_file_path}")

            return len(patient_ids)

        except Exception as e:
            raise Exception(f"处理解压数据失败: {e}")

    def get_patient_list(self) -> List[Dict[str, Any]]:
        """获取数据列表 (现在返回包含元数据的列表)"""
        try:
            pkl_files = glob.glob(os.path.join(self.processed_data_path, "*.pkl"))
            data_summaries = []
            for pkl_file in sorted(pkl_files): # Sort for consistent order
                data_id = os.path.basename(pkl_file).replace("_data.pkl", "")
                try:
                    loaded_data = pd.read_pickle(pkl_file)
                    metadata = {}
                    if isinstance(loaded_data, dict) and 'metadata' in loaded_data:
                        metadata = loaded_data['metadata']
                    elif isinstance(loaded_data, pd.DataFrame):
                        # For old format, create basic metadata
                        df = loaded_data
                        metadata = {
                            "data_id": data_id,
                            "source_file": f"{data_id}.csv", # Placeholder
                            "upload_time": datetime.now().isoformat(),
                            "group_name": None,
                            "rows": len(df),
                            "columns": df.columns.tolist(),
                            "shape": list(df.shape)
                        }
                    
                    # Ensure essential fields are present
                    summary = {
                        "data_id": data_id,
                        "records": metadata.get("rows", 0),
                        "columns_count": len(metadata.get("columns", [])),
                        "group_name": metadata.get("group_name"),
                        "upload_time": metadata.get("upload_time"),
                        "confirmed": metadata.get("confirmed", False),
                        "schema_applied": metadata.get("schema_applied", None),
                        "version": metadata.get("version", 1), # Add version
                        "last_modified_at": metadata.get("last_modified_at", metadata.get("upload_time")) # Add last_modified_at
                    }
                    data_summaries.append(summary)
                except Exception as e:
                    logger.error(f"处理PKL文件 {pkl_file} 失败: {e}")
                    data_summaries.append({
                        "data_id": data_id,
                        "records": 0,
                        "columns_count": 0,
                        "group_name": "Error",
                        "upload_time": None,
                        "confirmed": False,
                        "schema_applied": None,
                        "version": 1,
                        "last_modified_at": None
                    })
            return data_summaries
        except Exception as e:
            raise Exception(f"获取数据列表失败: {e}")

    def load_patient_data(self, data_id: str) -> Optional[pd.DataFrame]:
        """加载数据用于清洗 (现在是通用数据加载)"""
        try:
            pkl_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
            if os.path.exists(pkl_path):
                loaded_data = pd.read_pickle(pkl_path)
                if isinstance(loaded_data, dict) and 'df' in loaded_data:
                    return loaded_data['df'] # New format
                else:
                    return loaded_data # Old format (DataFrame directly)
            return None
        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
            return None

    def get_patient_data(self, data_id: str) -> Optional[Dict[str, Any]]:
        """获取特定数据 (现在是通用数据获取)"""
        try:
            pkl_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
            if not os.path.exists(pkl_path):
                return None

            loaded_data = pd.read_pickle(pkl_path)
            
            df = None
            metadata = {}

            if isinstance(loaded_data, dict) and 'df' in loaded_data:
                df = loaded_data['df']
                metadata = loaded_data.get('metadata', {})
            else:
                df = loaded_data # Old format: DataFrame directly
                # Create default metadata for old format
                metadata = {
                    "data_id": data_id,
                    "source_file": f"{data_id}.csv", # Placeholder
                    "upload_time": datetime.now().isoformat(),
                    "group_name": None,
                    "rows": len(df),
                    "columns": df.columns.tolist(),
                    "shape": list(df.shape)
                }

            if df is None:
                return None

            # 转换为JSON可序列化的格式
            result = {
                "columns": df.columns.tolist(),
                "data": df.to_dict('records'),
                "shape": list(df.shape), # Ensure shape is a list
                "summary": df.describe().to_dict(),
                "data_id": data_id,
                "records": len(df),
                "metadata": metadata # Include all metadata
            }
            return result

        except Exception as e:
            raise Exception(f"获取数据失败: {e}")

    def get_visualization_data(self, data_id: str, limit_rows: int = 1000) -> Dict[str, Any]:
        """获取可视化数据 (现在是通用可视化数据)"""
        try:
            data = self.get_patient_data(data_id)
            if not data:
                return {}

            # 限制数据量
            limited_data = data["data"][:limit_rows]

            return {
                "data_id": data_id,
                "data": limited_data,
                "columns": data["columns"]
            }

        except Exception as e:
            raise Exception(f"获取可视化数据失败: {e}")

    def update_data_metadata(self, data_id: str, new_metadata: Dict[str, Any]) -> bool:
        """更新特定数据ID的元数据"""
        try:
            pkl_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
            if not os.path.exists(pkl_path):
                logger.warning(f"无法更新元数据: 数据文件 {pkl_path} 未找到。")
                return False

            loaded_data = pd.read_pickle(pkl_path)
            df = None
            metadata = {}

            if isinstance(loaded_data, dict) and 'df' in loaded_data:
                df = loaded_data['df']
                metadata = loaded_data.get('metadata', {})
            else:
                df = loaded_data # Old format: DataFrame directly
                metadata = { # Create default metadata for old format
                    "data_id": data_id,
                    "source_file": f"{data_id}.csv",
                    "upload_time": datetime.now().isoformat(),
                    "group_name": None,
                    "rows": len(df),
                    "columns": df.columns.tolist(),
                    "shape": list(df.shape)
                }
            
            # Update existing metadata with new values
            metadata.update(new_metadata)

            data_to_save = {'df': df, 'metadata': metadata}
            pd.to_pickle(data_to_save, pkl_path)
            logger.info(f"成功更新数据 {data_id} 的元数据。")
            return True
        except Exception as e:
            logger.error(f"更新数据 {data_id} 元数据失败: {str(e)}")
            return False

    def mark_data_as_confirmed(self, data_ids: List[str]) -> bool:
        """将指定数据ID的数据标记为已确认"""
        all_successful = True
        for data_id in data_ids:
            success = self.update_data_metadata(data_id, {"confirmed": True})
            if not success:
                all_successful = False
                logger.error(f"标记数据 {data_id} 为已确认失败。")
        return all_successful

    async def format_data(
        self,
        data_ids: List[str],
        convert_to_headered: bool,
        schema_id: Optional[str],
        value_column_name: Optional[str] = "value" # Add new parameter with default
    ) -> List[str]:
        """
        格式化数据，包括转换为有表头数据、应用模式和保存新版本。
        """
        formatted_data_ids = []
        for data_id in data_ids:
            try:
                # 1. Load original data and its metadata
                loaded_data = pd.read_pickle(os.path.join(self.processed_data_path, f"{data_id}_data.pkl"))
                original_df = loaded_data['df']
                original_metadata = loaded_data['metadata']

                df_to_format = original_df.copy()
                schema_applied_name = original_metadata.get("schema_applied")

                # 2. Apply schema if convert_to_headered is true and schema_id is provided
                if convert_to_headered and schema_id and self.schema_service:
                    schema = self.schema_service.get_schema(schema_id)
                    if not schema:
                        raise ValueError(f"Schema with ID {schema_id} not found.")
                    
                    schema_applied_name = schema.name

                    if schema.schema_type == "high_frequency_wide":
                        # This logic is similar to process_csv_file for high_frequency_wide
                        # It assumes the original_df is headerless and needs transformation
                        # For simplicity, we'll assume original_df is already in a raw format
                        # and needs to be converted to long format based on the schema.
                        # This part might need more robust implementation based on actual raw data structure.
                        
                        # For now, let's assume original_df is the raw data (no headers)
                        # and we need to apply the high_frequency_wide schema to it.
                        # This is a placeholder and needs actual implementation based on how
                        # raw headerless data is stored.
                        
                        # If original_df is already a processed DataFrame, this conversion
                        # might be complex. A simpler approach for now is to re-read the
                        # original raw CSV if available, or assume original_df is the raw data.
                        # High-frequency wide schema: transform from wide to long format
                        time_col_idx = schema.time_column_index
                        data_start_idx = schema.data_start_column_index
                        num_data_cols = schema.num_data_columns
                        base_name = schema.data_column_base_name
                        sampling_rate = schema.sampling_rate_hz

                        if original_df.shape[1] < data_start_idx + num_data_cols:
                            raise ValueError(f"Original data for {data_id} has fewer columns ({original_df.shape[1]}) than expected by high-frequency wide schema {schema.name} (expected at least {data_start_idx + num_data_cols}).")

                        # Extract time column and data columns
                        time_data = original_df.iloc[:, time_col_idx]
                        data_cols = original_df.iloc[:, data_start_idx : data_start_idx + num_data_cols]

                        long_format_records = []
                        for i, row_time in enumerate(time_data):
                            try:
                                # Attempt to parse time, assuming it might be numeric (seconds) or string
                                base_timestamp = pd.to_datetime(row_time, unit='s', errors='coerce')
                                if pd.isna(base_timestamp):
                                    base_timestamp = pd.to_datetime(row_time, errors='coerce')
                                if pd.isna(base_timestamp):
                                    logger.warning(f"Could not parse time value {row_time} at row {i} in data {data_id}, skipping row. Attempting next row.")
                                    continue
                            except Exception as e_time:
                                logger.warning(f"Error parsing time value {row_time} at row {i} in data {data_id}, skipping row. Error: {e_time}")
                                continue

                            for j in range(num_data_cols):
                                value = data_cols.iloc[i, j]
                                # Calculate precise timestamp for each sample in milliseconds
                                # 1 second / sampling_rate = duration of one sample
                                # j * (1.0 / sampling_rate) = time offset in seconds
                                # Convert to milliseconds: * 1000
                                sample_timestamp_ms = base_timestamp + pd.to_timedelta(j * (1000.0 / sampling_rate), unit='ms')
                                long_format_records.append({
                                    'timestamp': sample_timestamp_ms,
                                    value_column_name: value # Use custom value column name
                                })
                        
                        if not long_format_records:
                            logger.warning(f"No data could be transformed for {data_id} using schema {schema.name}. Resulting DataFrame will be empty.")
                            df_to_format = pd.DataFrame(columns=['timestamp', value_column_name]) # Use custom value column name
                        else:
                            df_to_format = pd.DataFrame(long_format_records)
                            df_to_format['timestamp'] = pd.to_datetime(df_to_format['timestamp'])
                        
                        # Clean column names after transformation (e.g., if 'value' had spaces)
                        df_to_format = self.clean_col_names(df_to_format)
                        logger.info(f"DEBUG: Transformed high_frequency_wide data head for {data_id}:\n{df_to_format.head()}")
                        logger.info(f"DEBUG: Transformed high_frequency_wide data dtypes for {data_id}:\n{df_to_format.dtypes}")

                    elif schema.schema_type == "standard":
                        # Apply standard schema: re-index columns and rename
                        col_names = [col.name for col in schema.columns]
                        if len(col_names) == df_to_format.shape[1]:
                            df_to_format.columns = col_names
                        else:
                            logger.warning(f"Schema column count mismatch for {data_id}, cannot apply standard schema names. Expected {len(col_names)}, got {df_to_format.shape[1]}. Attempting to use existing columns.")
                            # If column count mismatches, try to map by name if possible, or just keep existing
                            # For now, if mismatch, we keep existing columns and just clean names.
                            pass # No change to df_to_format.columns if mismatch
                        df_to_format = self.clean_col_names(df_to_format) # Ensure names are clean
                
                # 3. Update metadata for in-place formatting
                current_version = original_metadata.get("version", 1)
                new_version = current_version + 1
                
                updated_metadata = original_metadata.copy()
                updated_metadata["version"] = new_version
                updated_metadata["last_modified_at"] = datetime.now().isoformat()
                updated_metadata["rows"] = len(df_to_format)
                updated_metadata["columns"] = df_to_format.columns.tolist()
                updated_metadata["shape"] = list(df_to_format.shape)
                updated_metadata["schema_applied"] = schema_applied_name
                
                # Remove fields related to new file creation if they exist
                updated_metadata.pop("original_data_id", None)
                updated_metadata.pop("formatted_from_version", None)

                data_to_save = {'df': df_to_format, 'metadata': updated_metadata}
                
                # Save back to the original file path
                output_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
                pd.to_pickle(data_to_save, output_path)
                logger.info(f"成功格式化数据 {data_id} (版本 {new_version})。")
                formatted_data_ids.append(data_id) # Return original data_id as it's an update

            except Exception as e:
                logger.error(f"格式化数据 {data_id} 失败: {str(e)}")
                # Continue to next data_id even if one fails
        
        return formatted_data_ids

    def delete_data_batch(self, data_ids: List[str]) -> List[str]:
        """批量删除数据文件"""
        deleted_ids = []
        for data_id in data_ids:
            pkl_path = os.path.join(self.processed_data_path, f"{data_id}_data.pkl")
            try:
                if os.path.exists(pkl_path):
                    os.remove(pkl_path)
                    deleted_ids.append(data_id)
                    logger.info(f"成功删除数据文件: {pkl_path}")
                else:
                    logger.warning(f"尝试删除数据文件 {pkl_path} 失败: 文件不存在。")
            except Exception as e:
                logger.error(f"删除数据文件 {pkl_path} 失败: {str(e)}")
        return deleted_ids
