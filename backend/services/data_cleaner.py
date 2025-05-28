import pandas as pd
import numpy as np
from scipy.signal import medfilt
from scipy import stats
from typing import Dict, Any
import os

class DataCleaner:
    def __init__(self):
        self.processed_data_path = "data/processed"


    async def clean_patient_data(self, patient_id: str, cleaning_config: Dict[str, Any]) -> Dict[str, Any]:
        """清洗患者数据"""
        try:
            pkl_path = os.path.join(self.processed_data_path, f"{patient_id}_data.pkl")
            if not os.path.exists(pkl_path):
                raise Exception(f"患者 {patient_id} 的数据文件不存在")

            data_dict = pd.read_pickle(pkl_path)
            cleaned_data = {}
            cleaning_report = {}

            # 清洗ECG数据
            if 'ecg_data' in data_dict and not data_dict['ecg_data'].empty:
                ecg_cleaned, ecg_report = self._clean_dataframe(
                    data_dict['ecg_data'],
                    cleaning_config,
                    "ECG"
                )
                cleaned_data['ecg_data'] = ecg_cleaned
                cleaning_report['ecg'] = ecg_report

            # 清洗MV数据
            if 'mv_data' in data_dict and not data_dict['mv_data'].empty:
                mv_cleaned, mv_report = self._clean_dataframe(
                    data_dict['mv_data'],
                    cleaning_config,
                    "MV"
                )
                cleaned_data['mv_data'] = mv_cleaned
                cleaning_report['mv'] = mv_report

            # 保存清洗后的数据
            cleaned_pkl_path = os.path.join(self.processed_data_path, f"{patient_id}_cleaned_data.pkl")
            pd.to_pickle(cleaned_data, cleaned_pkl_path)

            return {
                "success": True,
                "cleaned_file": cleaned_pkl_path,
                "cleaning_report": cleaning_report
            }

        except Exception as e:
            raise Exception(f"清洗患者数据失败: {e}")


    def _clean_dataframe(self, df: pd.DataFrame, config: Dict[str, Any], data_type: str) -> tuple:
        """清洗DataFrame"""
        df_cleaned = df.copy()
        report = {
            "original_shape": df.shape,
            "operations": [],
            "final_shape": None,
            "missing_values_before": df.isnull().sum().to_dict(),
            "missing_values_after": None
        }

        # 1. 移除异常值
        if config.get("remove_outliers", True):
            outlier_method = config.get("outlier_method", "iqr")
            df_cleaned, outlier_report = self._remove_outliers(df_cleaned, outlier_method)
            report["operations"].append({
                "operation": "remove_outliers",
                "method": outlier_method,
                "details": outlier_report
            })

        # 2. 处理缺失值
        if config.get("fill_missing", True):
            missing_method = config.get("missing_method", "interpolate")
            df_cleaned, missing_report = self._handle_missing_values(df_cleaned, missing_method)
            report["operations"].append({
                "operation": "handle_missing",
                "method": missing_method,
                "details": missing_report
            })

        # 3. 数据平滑
        if config.get("smooth_data", False):
            smooth_window = config.get("smooth_window", 5)
            df_cleaned, smooth_report = self._smooth_data(df_cleaned, smooth_window)
            report["operations"].append({
                "operation": "smooth_data",
                "window": smooth_window,
                "details": smooth_report
            })

        # 4. 数据类型特定的清洗
        if data_type == "ECG":
            df_cleaned = self._clean_ecg_specific(df_cleaned)
        elif data_type == "MV":
            df_cleaned = self._clean_mv_specific(df_cleaned)

        report["final_shape"] = df_cleaned.shape
        report["missing_values_after"] = df_cleaned.isnull().sum().to_dict()

        return df_cleaned, report


    def _remove_outliers(self, df: pd.DataFrame, method: str = "iqr") -> tuple:
        """移除异常值"""
        df_cleaned = df.copy()
        outlier_report = {}

        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                original_count = len(df_cleaned)

                if method == "iqr":
                    Q1 = df_cleaned[col].quantile(0.25)
                    Q3 = df_cleaned[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    outliers_mask = (df_cleaned[col] < lower_bound) | \
                                    (df_cleaned[col] > upper_bound)
                    df_cleaned.loc[outliers_mask, col] = np.nan

                elif method == "zscore":
                    z_scores = np.abs(stats.zscore(df_cleaned[col].dropna()))
                    outliers_mask = z_scores > 3
                    df_cleaned.loc[df_cleaned[col].dropna().index[outliers_mask], col] = np.nan

                outliers_removed = outliers_mask.sum() if 'outliers_mask' in locals() else 0
                outlier_report[col] = {
                    "outliers_removed": int(outliers_removed),
                    "percentage": float(outliers_removed / original_count * 100) \
                        if original_count > 0 else 0
                }

        return df_cleaned, outlier_report


    def _handle_missing_values(self, df: pd.DataFrame, method: str = "interpolate") -> tuple:
        """处理缺失值"""
        df_cleaned = df.copy()
        missing_report = {}

        for col in df.columns:
            missing_before = df_cleaned[col].isnull().sum()

            if missing_before > 0:
                if method == "interpolate":
                    df_cleaned[col] = df_cleaned[col].interpolate(method='linear')
                elif method == "forward_fill":
                    df_cleaned[col] = df_cleaned[col].fillna(method='ffill')
                elif method == "backward_fill":
                    df_cleaned[col] = df_cleaned[col].fillna(method='bfill')
                elif method == "mean":
                    df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mean())
                elif method == "median":
                    df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
                elif method == "drop":
                    df_cleaned = df_cleaned.dropna(subset=[col])

                missing_after = df_cleaned[col].isnull().sum()
                missing_report[col] = {
                    "missing_before": int(missing_before),
                    "missing_after": int(missing_after),
                    "filled": int(missing_before - missing_after)
                }

        return df_cleaned, missing_report


    def _smooth_data(self, df: pd.DataFrame, window: int = 5) -> tuple:
        """数据平滑"""
        df_cleaned = df.copy()
        smooth_report = {}

        for col in df.columns:
            if df[col].dtype in ['float64', 'int64'] and len(df[col].dropna()) > window:
                original_std = df_cleaned[col].std()

                # 使用中值滤波进行平滑
                smoothed_values = medfilt(
                    df_cleaned[col].fillna(method='ffill').fillna(method='bfill'),
                    kernel_size=window
                )
                df_cleaned[col + '_smoothed'] = smoothed_values

                smoothed_std = df_cleaned[col + '_smoothed'].std()
                smooth_report[col] = {
                    "original_std": float(original_std) if not np.isnan(original_std) else None,
                    "smoothed_std": float(smoothed_std) if not np.isnan(smoothed_std) else None,
                    "noise_reduction": float((original_std - smoothed_std) / original_std * 100) \
                        if original_std > 0 else 0
                }

        return df_cleaned, smooth_report


    def _clean_ecg_specific(self, df: pd.DataFrame) -> pd.DataFrame:
        """ECG数据特定清洗"""
        df_cleaned = df.copy()

        # 心率范围检查 (正常范围: 40-200 bpm)
        if '心率' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['心率'] < 40) | (df_cleaned['心率'] > 200), '心率'] = np.nan

        # 血压范围检查
        if '收缩压' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['收缩压'] < 60) | (df_cleaned['收缩压'] > 250), '收缩压'] = np.nan

        if '舒张压' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['舒张压'] < 30) | (df_cleaned['舒张压'] > 150), '舒张压'] = np.nan

        # 体温范围检查 (正常范围: 35-42°C)
        if '体温' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['体温'] < 35) | (df_cleaned['体温'] > 42), '体温'] = np.nan

        return df_cleaned


    def _clean_mv_specific(self, df: pd.DataFrame) -> pd.DataFrame:
        """MV数据特定清洗"""
        df_cleaned = df.copy()

        # FiO2范围检查 (0.21-1.0)
        if 'FiO2' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['FiO2'] < 0.21) | (df_cleaned['FiO2'] > 1.0), 'FiO2'] = np.nan

        # PEEP范围检查 (0-30 cmH2O)
        if 'PEEP' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['PEEP'] < 0) | (df_cleaned['PEEP'] > 30), 'PEEP'] = np.nan

        # 呼吸频率范围检查 (5-60 breaths/min)
        if '频率' in df_cleaned.columns:
            df_cleaned.loc[(df_cleaned['频率'] < 5) | (df_cleaned['频率'] > 60), '频率'] = np.nan

        return df_cleaned


    def get_data_quality_report(self, patient_id: str) -> Dict[str, Any]:
        """生成数据质量报告"""
        try:
            pkl_path = os.path.join(self.processed_data_path, f"{patient_id}_data.pkl")
            if not os.path.exists(pkl_path):
                raise Exception(f"患者 {patient_id} 的数据文件不存在")

            data_dict = pd.read_pickle(pkl_path)
            quality_report = {}

            for data_type, df in data_dict.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    quality_report[data_type] = {
                        "shape": df.shape,
                        "missing_values": df.isnull().sum().to_dict(),
                        "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
                        "data_types": df.dtypes.astype(str).to_dict(),
                        "summary_stats": df.describe().to_dict()
                    }

            return quality_report

        except Exception as e:
            raise Exception(f"生成数据质量报告失败: {e}")
