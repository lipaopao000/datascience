import pandas as pd
import numpy as np
from scipy.stats import iqr, linregress, skew, kurtosis
from scipy.signal import find_peaks
from typing import Dict, List, Any, Optional
import os
from tqdm import tqdm
import logging

# Assuming DataProcessor is available or can be instantiated
from services.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class FeatureExtractor:
    def __init__(self):
        self.processed_data_path = "data/processed"
        self.features_path = "data/features"
        os.makedirs(self.features_path, exist_ok=True)
        self.data_processor = DataProcessor() # Instantiate DataProcessor

    async def extract_features(self, data_id: str, feature_config: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        提取通用时序数据的特征。
        feature_config 示例:
        {
            "column_name_1": ["basic_stats", "time_domain"],
            "column_name_2": ["basic_stats", "frequency_domain"]
        }
        """
        try:
            # 加载数据
            df = self.data_processor.load_patient_data(data_id) # Renamed from load_patient_data to load_data
            if df is None or df.empty:
                raise Exception(f"未找到或数据为空: {data_id}")

            all_extracted_features = {'data_id': data_id}

            for col_name, types_to_extract in feature_config.items():
                if col_name not in df.columns:
                    logger.warning(f"列 '{col_name}' 不存在于数据中，跳过特征提取。")
                    continue

                series = df[col_name]
                extracted_col_features = self._extract_features_from_series(series, col_name, types_to_extract)
                all_extracted_features.update(extracted_col_features)

            # 保存特征
            # 考虑到可能有很多data_id，每个data_id的特征单独保存
            output_file = os.path.join(self.features_path, f"{data_id}_features.pkl")
            pd.to_pickle(all_extracted_features, output_file)

            # Convert numpy types to standard Python types for JSON serialization
            serializable_features = {}
            for key, value in all_extracted_features.items():
                if isinstance(value, np.int64):
                    serializable_features[key] = int(value)
                elif isinstance(value, np.float64):
                    serializable_features[key] = float(value)
                elif isinstance(value, np.bool_):
                    serializable_features[key] = bool(value)
                elif isinstance(value, pd.Timestamp):
                    serializable_features[key] = value.isoformat()
                else:
                    serializable_features[key] = value
            
            return {
                "data_id": data_id,
                "features_count": len(serializable_features) - 1, # Exclude data_id itself
                "features_file": output_file,
                "extracted_features": serializable_features # Return serializable features
            }

        except Exception as e:
            raise Exception(f"特征提取失败: {e}")

    def _extract_features_from_series(self, series: pd.Series, col_prefix: str, feature_types: List[str]) -> Dict[str, Any]:
        """
        从单个时序数据列中提取指定类型的特征。
        """
        features = {}
        series_numeric = pd.to_numeric(series, errors='coerce').dropna()

        if series_numeric.empty:
            return self._get_empty_stats(col_prefix) # Return empty stats if series is empty after cleaning

        if "basic_stats" in feature_types:
            features.update(self._calculate_basic_stats(series_numeric, col_prefix))
        if "time_domain" in feature_types:
            features.update(self._extract_time_domain_features(series_numeric, col_prefix))
        if "frequency_domain" in feature_types:
            features.update(self._extract_frequency_domain_features(series_numeric, col_prefix))
        # Add more generic feature types here as needed

        return features

    def _calculate_basic_stats(self, series: pd.Series, prefix: str) -> Dict[str, Any]:
        """计算基础统计特征"""
        if series.empty or series.isnull().all():
            return self._get_empty_stats(prefix)

        series_numeric = pd.to_numeric(series, errors='coerce').dropna()

        if series_numeric.empty:
            return self._get_empty_stats(prefix)

        features = {
            f'{prefix}_mean': series_numeric.mean(),
            f'{prefix}_median': series_numeric.median(),
            f'{prefix}_std': series_numeric.std(),
            f'{prefix}_min': series_numeric.min(),
            f'{prefix}_max': series_numeric.max(),
            f'{prefix}_iqr': iqr(series_numeric),
            f'{prefix}_count': series_numeric.count(),
            f'{prefix}_range': series_numeric.max() - series_numeric.min()
        }

        # 计算趋势（斜率）
        if len(series_numeric) >= 2:
            x_values = np.arange(len(series_numeric))
            y_values = series_numeric.values
            try:
                slope, _, r_value, _, _ = linregress(x_values, y_values)
                features[f'{prefix}_slope'] = slope
                features[f'{prefix}_r_squared'] = r_value**2
            except Exception:
                features[f'{prefix}_slope'] = np.nan
                features[f'{prefix}_r_squared'] = np.nan
        else:
            features[f'{prefix}_slope'] = np.nan
            features[f'{prefix}_r_squared'] = np.nan

        return features

    def _get_empty_stats(self, prefix: str) -> Dict[str, Any]:
        """返回空的统计特征"""
        return {
            f'{prefix}_mean': np.nan,
            f'{prefix}_median': np.nan,
            f'{prefix}_std': np.nan,
            f'{prefix}_min': np.nan,
            f'{prefix}_max': np.nan,
            f'{prefix}_iqr': np.nan,
            f'{prefix}_count': 0,
            f'{prefix}_range': np.nan,
            f'{prefix}_slope': np.nan,
            f'{prefix}_r_squared': np.nan
        }

    def _extract_time_domain_features(self, series: pd.Series, prefix: str) -> Dict[str, Any]:
        """提取时域特征"""
        features = {}
        if len(series) > 1:
            # 变异性特征
            features[f'{prefix}_RMS'] = np.sqrt(np.mean(series**2))
            features[f'{prefix}_Variance'] = np.var(series)
            features[f'{prefix}_CV'] = np.std(series) / np.mean(series) \
                if np.mean(series) != 0 else np.nan

            # 形状特征
            features[f'{prefix}_Skewness'] = skew(series)
            features[f'{prefix}_Kurtosis'] = kurtosis(series)

            # 峰值特征
            peaks, _ = find_peaks(series)
            features[f'{prefix}_PeakCount'] = len(peaks)
            features[f'{prefix}_PeakRate'] = len(peaks) / len(series) \
                if len(series) > 0 else 0
        else:
            features.update({
                f'{prefix}_RMS': np.nan,
                f'{prefix}_Variance': np.nan,
                f'{prefix}_CV': np.nan,
                f'{prefix}_Skewness': np.nan,
                f'{prefix}_Kurtosis': np.nan,
                f'{prefix}_PeakCount': 0,
                f'{prefix}_PeakRate': np.nan
            })
        return features

    def _extract_frequency_domain_features(self, series: pd.Series, prefix: str) -> Dict[str, Any]:
        """提取频域特征"""
        features = {}
        if len(series) > 10:  # 需要足够的数据点进行FFT
            fft_values = np.fft.fft(series)
            fft_magnitude = np.abs(fft_values)

            # 避免除以零
            sum_magnitude = np.sum(fft_magnitude)
            if sum_magnitude == 0:
                return self._get_empty_freq_stats(prefix)

            # 频域特征
            features[f'{prefix}_SpectralCentroid'] = np.sum(np.arange(len(fft_magnitude)) * fft_magnitude) / sum_magnitude
            features[f'{prefix}_SpectralSpread'] = np.sqrt(np.sum(((np.arange(len(fft_magnitude)) - features[f'{prefix}_SpectralCentroid'])**2) * fft_magnitude) / sum_magnitude)
            
            # 避免log2(0)
            normalized_magnitude = fft_magnitude / sum_magnitude
            features[f'{prefix}_SpectralEntropy'] = -np.sum(normalized_magnitude * np.log2(normalized_magnitude + 1e-10))

            # 主频率成分
            dominant_freq_idx = np.argmax(fft_magnitude[1:len(fft_magnitude)//2]) + 1
            features[f'{prefix}_DominantFreq'] = dominant_freq_idx
            features[f'{prefix}_DominantFreqPower'] = fft_magnitude[dominant_freq_idx]
        else:
            features.update(self._get_empty_freq_stats(prefix))
        return features

    def _get_empty_freq_stats(self, prefix: str) -> Dict[str, Any]:
        """返回空的频域统计特征"""
        return {
            f'{prefix}_SpectralCentroid': np.nan,
            f'{prefix}_SpectralSpread': np.nan,
            f'{prefix}_SpectralEntropy': np.nan,
            f'{prefix}_DominantFreq': np.nan,
            f'{prefix}_DominantFreqPower': np.nan
        }

    def get_feature_table(self, data_id: Optional[str] = None) -> Dict[str, Any]:
        """获取特征表，可指定data_id或获取所有"""
        try:
            if data_id:
                features_file = os.path.join(self.features_path, f"{data_id}_features.pkl")
                if os.path.exists(features_file):
                    features_dict = pd.read_pickle(features_file)
                    # Convert to DataFrame for consistent output structure
                    df = pd.DataFrame([features_dict])
                    return {
                        "shape": df.shape,
                        "columns": df.columns.tolist(),
                        "data": df.to_dict('records'),
                        "summary": df.describe().to_dict()
                    }
                else:
                    return {"message": f"没有找到 {data_id} 的特征文件"}
            else:
                all_features_dfs = []
                for filename in os.listdir(self.features_path):
                    if filename.endswith('_features.pkl'):
                        file_path = os.path.join(self.features_path, filename)
                        features_dict = pd.read_pickle(file_path)
                        all_features_dfs.append(pd.DataFrame([features_dict])) # Each dict becomes a row

                if all_features_dfs:
                    combined_df = pd.concat(all_features_dfs, ignore_index=True)
                    return {
                        "shape": combined_df.shape,
                        "columns": combined_df.columns.tolist(),
                        "data": combined_df.to_dict('records'),
                        "summary": combined_df.describe().to_dict()
                    }
                else:
                    return {"message": "没有找到任何特征文件"}
        except Exception as e:
            raise Exception(f"获取特征表失败: {e}")
