import pandas as pd
import numpy as np
from scipy import stats, signal
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)


class EnhancedDataCleaner:
    def __init__(self):
        self.scaler = None

    def clean_data(self, data: pd.DataFrame, config: dict) -> dict:
        """
        清洗数据
        """
        try:
            cleaned_data = data.copy()
            cleaning_steps = []
            cleaning_stats = {}

            # 记录原始数据统计
            original_stats = self._calculate_data_stats(data)

            # 处理缺失值
            if config.get('missing_value_strategy') == 'drop':
                before_rows = len(cleaned_data)
                cleaned_data = cleaned_data.dropna()
                removed_rows = before_rows - len(cleaned_data)
                cleaning_steps.append(f"删除缺失值: 移除了 {removed_rows} 行")
                cleaning_stats['missing_removed'] = removed_rows
            elif config.get('missing_value_strategy') == 'fill':
                fill_method = config.get('fill_method', 'ffill')
                missing_count = cleaned_data.isnull().sum().sum()
                cleaned_data = self._fill_missing_values(cleaned_data, fill_method)
                cleaning_steps.append(f"填充缺失值: 使用 {fill_method} 方法填充 {missing_count} 个缺失值")
                cleaning_stats['missing_filled'] = missing_count

            # 信号滤波
            if config.get('apply_filter', False):
                filter_type = config.get('filter_type', 'lowpass')
                cutoff_freq = config.get('cutoff_frequency', 0.5)
                cleaned_data = self._apply_signal_filter(cleaned_data, filter_type, cutoff_freq)
                cleaning_steps.append(f"应用{filter_type}滤波器: 截止频率 {cutoff_freq}")

            # 处理异常值
            outlier_methods = config.get('outlier_methods', [])
            outlier_stats = {}

            if 'iqr' in outlier_methods:
                before_rows = len(cleaned_data)
                cleaned_data = self._remove_outliers_iqr(cleaned_data, config.get('iqr_factor', 1.5))
                removed = before_rows - len(cleaned_data)
                outlier_stats['iqr_removed'] = removed
                cleaning_steps.append(f"IQR方法移除异常值: {removed} 行")

            if 'zscore' in outlier_methods:
                threshold = config.get('zscore_threshold', 3.0)
                before_rows = len(cleaned_data)
                cleaned_data = self._remove_outliers_zscore(cleaned_data, threshold)
                removed = before_rows - len(cleaned_data)
                outlier_stats['zscore_removed'] = removed
                cleaning_steps.append(f"Z-Score方法移除异常值: {removed} 行 (阈值: {threshold})")

            if 'isolation_forest' in outlier_methods:
                contamination = config.get('contamination', 0.1)
                before_rows = len(cleaned_data)
                cleaned_data = self._remove_outliers_isolation_forest(cleaned_data, contamination)
                removed = before_rows - len(cleaned_data)
                outlier_stats['isolation_removed'] = removed
                cleaning_steps.append(f"孤立森林移除异常值: {removed} 行 (污染率: {contamination})")

            if 'percentile' in outlier_methods:
                lower_pct = config.get('lower_percentile', 1)
                upper_pct = config.get('upper_percentile', 99)
                before_rows = len(cleaned_data)
                cleaned_data = self._remove_outliers_percentile(cleaned_data, lower_pct, upper_pct)
                removed = before_rows - len(cleaned_data)
                outlier_stats['percentile_removed'] = removed
                cleaning_steps.append(f"百分位数方法移除异常值: {removed} 行 ({lower_pct}%-{upper_pct}%)")

            # 平滑处理
            if config.get('apply_smoothing', False):
                smoothing_method = config.get('smoothing_method', 'rolling_mean')
                window_size = config.get('smoothing_window', 5)
                cleaned_data = self._apply_smoothing(cleaned_data, smoothing_method, window_size)
                cleaning_steps.append(f"应用平滑处理: {smoothing_method} (窗口: {window_size})")

            # 数据标准化
            normalization_method = config.get('normalization_method')
            if normalization_method:
                cleaned_data = self._normalize_data(cleaned_data, normalization_method)
                cleaning_steps.append(f"数据标准化: {normalization_method}")

            # 重采样
            resample_freq = config.get('resample_freq')
            if resample_freq and 'timestamp' in cleaned_data.columns:
                original_freq = self._estimate_sampling_frequency(cleaned_data)
                cleaned_data = self._resample_data(cleaned_data, resample_freq)
                cleaning_steps.append(f"重采样: {original_freq} -> {resample_freq}")

            # 计算清洗后统计
            cleaned_stats = self._calculate_data_stats(cleaned_data)

            return {
                'cleaned_data': {
                    'data': cleaned_data.to_dict('records'),
                    'columns': cleaned_data.columns.tolist(),
                    'shape': cleaned_data.shape
                },
                'report': {
                    'original_rows': len(data),
                    'cleaned_rows': len(cleaned_data),
                    'removed_rows': len(data) - len(cleaned_data),
                    'processing_time': 1.5,
                    'steps': cleaning_steps,
                    'original_stats': original_stats,
                    'cleaned_stats': cleaned_stats,
                    'outlier_stats': outlier_stats,
                    'cleaning_stats': cleaning_stats
                }
            }

        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            raise

    def preview_cleaning_effect(self, data: pd.DataFrame, config: dict, column: str) -> dict:
        """
        预览清洗效果，不实际修改数据
        """
        try:
            original_data = data[column].copy()
            preview_data = data.copy()

            # 应用清洗步骤
            if config.get('missing_value_strategy') == 'fill':
                fill_method = config.get('fill_method', 'ffill')
                preview_data = self._fill_missing_values(preview_data, fill_method)

            if config.get('apply_filter', False):
                filter_type = config.get('filter_type', 'lowpass')
                cutoff_freq = config.get('cutoff_frequency', 0.5)
                preview_data = self._apply_signal_filter(preview_data, filter_type, cutoff_freq)

            if config.get('apply_smoothing', False):
                smoothing_method = config.get('smoothing_method', 'rolling_mean')
                window_size = config.get('smoothing_window', 5)
                preview_data = self._apply_smoothing(preview_data, smoothing_method, window_size)

            cleaned_column = preview_data[column]

            # 计算统计对比
            original_stats = {
                'mean': float(original_data.mean()),
                'std': float(original_data.std()),
                'min': float(original_data.min()),
                'max': float(original_data.max()),
                'missing_count': int(original_data.isnull().sum()),
                'outlier_count': self._count_outliers_zscore(original_data, 3.0)
            }

            cleaned_stats = {
                'mean': float(cleaned_column.mean()),
                'std': float(cleaned_column.std()),
                'min': float(cleaned_column.min()),
                'max': float(cleaned_column.max()),
                'missing_count': int(cleaned_column.isnull().sum()),
                'outlier_count': self._count_outliers_zscore(cleaned_column, 3.0)
            }

            return {
                'original_data': original_data.tolist()[:1000],  # 限制数据量
                'cleaned_data': cleaned_column.tolist()[:1000],
                'original_stats': original_stats,
                'cleaned_stats': cleaned_stats,
                'improvement': {
                    'std_reduction': (original_stats['std'] - cleaned_stats['std']) / original_stats['std'] * 100 \
                        if original_stats['std'] > 0 else 0,
                    'outlier_reduction': original_stats['outlier_count'] - cleaned_stats['outlier_count'],
                    'missing_reduction': original_stats['missing_count'] - cleaned_stats['missing_count']
                }
            }

        except Exception as e:
            logger.error(f"预览清洗效果失败: {str(e)}")
            raise

    def analyze_data_quality(self, data: pd.DataFrame) -> dict:
        """
        分析数据质量
        """
        try:
            quality_report = {}
            numeric_columns = data.select_dtypes(include=[np.number]).columns

            for col in numeric_columns:
                series = data[col]

                # 基础统计
                basic_stats = {
                    'count': int(series.count()),
                    'missing_count': int(series.isnull().sum()),
                    'missing_rate': float(series.isnull().sum() / len(series)),
                    'mean': float(series.mean()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'range': float(series.max() - series.min())
                }

                # 异常值检测
                outlier_stats = {
                    'zscore_outliers': self._count_outliers_zscore(series, 3.0),
                    'iqr_outliers': self._count_outliers_iqr(series),
                    'extreme_values': self._count_extreme_values(series)
                }

                # 数据分布特征
                distribution_stats = {
                    'skewness': float(series.skew()),
                    'kurtosis': float(series.kurtosis()),
                    'variance': float(series.var()),
                    'coefficient_of_variation': float(series.std() / series.mean()) \
                        if series.mean() != 0 else 0
                }

                # 时序特征（如果有时间戳）
                temporal_stats = {}
                if len(series) > 1:
                    temporal_stats = {
                        'trend': self._calculate_trend(series),
                        'stationarity': self._test_stationarity(series),
                        'autocorrelation': self._calculate_autocorrelation(series)
                    }

                quality_report[col] = {
                    'basic_stats': basic_stats,
                    'outlier_stats': outlier_stats,
                    'distribution_stats': distribution_stats,
                    'temporal_stats': temporal_stats,
                    'quality_score': self._calculate_quality_score(basic_stats, outlier_stats, distribution_stats)
                }

            return quality_report

        except Exception as e:
            logger.error(f"数据质量分析失败: {str(e)}")
            raise

    def _fill_missing_values(self, data: pd.DataFrame, method: str) -> pd.DataFrame:
        """填充缺失值"""
        if method == 'ffill':
            return data.fillna(method='ffill')
        elif method == 'bfill':
            return data.fillna(method='bfill')
        elif method == 'mean':
            return data.fillna(data.mean())
        elif method == 'median':
            return data.fillna(data.median())
        elif method == 'zero':
            return data.fillna(0)
        elif method == 'interpolate':
            return data.interpolate(method='linear')
        elif method == 'spline':
            return data.interpolate(method='spline', order=3)
        return data

    def _apply_signal_filter(self, data: pd.DataFrame, filter_type: str, cutoff_freq: float) -> pd.DataFrame:
        """应用信号滤波"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            if data[col].notna().sum() > 10:  # 确保有足够的数据点
                try:
                    if filter_type == 'lowpass':
                        # 低通滤波
                        b, a = signal.butter(4, cutoff_freq, btype='low')
                        data[col] = signal.filtfilt(b, a, data[col].fillna(data[col].mean()))
                    elif filter_type == 'highpass':
                        # 高通滤波
                        b, a = signal.butter(4, cutoff_freq, btype='high')
                        data[col] = signal.filtfilt(b, a, data[col].fillna(data[col].mean()))
                    elif filter_type == 'bandpass':
                        # 带通滤波
                        low_freq = cutoff_freq * 0.5
                        high_freq = cutoff_freq * 2
                        b, a = signal.butter(4, [low_freq, high_freq], btype='band')
                        data[col] = signal.filtfilt(b, a, data[col].fillna(data[col].mean()))
                except Exception as e:
                    logger.warning(f"滤波失败 {col}: {str(e)}")

        return data

    def _apply_smoothing(self, data: pd.DataFrame, method: str, window_size: int) -> pd.DataFrame:
        """应用平滑处理"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            try:
                if method == 'rolling_mean':
                    data[col] = data[col].rolling(window=window_size, center=True).mean()
                elif method == 'rolling_median':
                    data[col] = data[col].rolling(window=window_size, center=True).median()
                elif method == 'savgol':
                    if len(data[col].dropna()) > window_size:
                        data[col] = signal.savgol_filter(data[col].fillna(data[col].mean()),
                                                       window_size, 3)
                elif method == 'exponential':
                    data[col] = data[col].ewm(span=window_size).mean()
            except Exception as e:
                logger.warning(f"平滑处理失败 {col}: {str(e)}")

        return data

    def _remove_outliers_iqr(self, data: pd.DataFrame, factor: float = 1.5) -> pd.DataFrame:
        """使用IQR方法移除异常值"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]

        return data

    def _remove_outliers_zscore(self, data: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """使用Z-Score方法移除异常值"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            z_scores = np.abs(stats.zscore(data[col].dropna()))
            valid_indices = data[col].dropna().index
            outlier_mask = pd.Series(False, index=data.index)
            outlier_mask.loc[valid_indices] = z_scores >= threshold
            data = data[~outlier_mask]

        return data

    def _remove_outliers_isolation_forest(self, data: pd.DataFrame, contamination: float = 0.1) -> pd.DataFrame:
        """使用孤立森林方法移除异常值"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        if len(numeric_columns) > 0:
            # 填充缺失值用于异常检测
            data_filled = data[numeric_columns].fillna(data[numeric_columns].mean())
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            outliers = iso_forest.fit_predict(data_filled)
            data = data[outliers == 1]

        return data

    def _remove_outliers_percentile(self, data: pd.DataFrame, lower_pct: float, upper_pct: float) -> pd.DataFrame:
        """使用百分位数方法移除异常值"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        for col in numeric_columns:
            lower_bound = data[col].quantile(lower_pct / 100)
            upper_bound = data[col].quantile(upper_pct / 100)
            data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]

        return data

    def _count_outliers_zscore(self, series: pd.Series, threshold: float) -> int:
        """计算Z-Score异常值数量"""
        if series.notna().sum() == 0:
            return 0
        z_scores = np.abs(stats.zscore(series.dropna()))
        return int((z_scores >= threshold).sum())

    def _count_outliers_iqr(self, series: pd.Series) -> int:
        """计算IQR异常值数量"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return int(((series < lower_bound) | (series > upper_bound)).sum())

    def _count_extreme_values(self, series: pd.Series) -> int:
        """计算极端值数量（超过5个标准差）"""
        if series.notna().sum() == 0:
            return 0
        mean = series.mean()
        std = series.std()
        return int(((series < mean - 5*std) | (series > mean + 5*std)).sum())

    def _calculate_trend(self, series: pd.Series) -> float:
        """计算趋势（斜率）"""
        if len(series) < 2:
            return 0.0
        x = np.arange(len(series))
        y = series.values
        valid_mask = ~np.isnan(y)
        if valid_mask.sum() < 2:
            return 0.0
        slope, _ = np.polyfit(x[valid_mask], y[valid_mask], 1)
        return float(slope)

    def _test_stationarity(self, series: pd.Series) -> bool:
        """简单的平稳性测试"""
        if len(series) < 10:
            return True
        # 简单的方差稳定性测试
        mid = len(series) // 2
        first_half_var = series[:mid].var()
        second_half_var = series[mid:].var()
        return abs(first_half_var - second_half_var) / max(first_half_var, second_half_var) < 0.5

    def _calculate_autocorrelation(self, series: pd.Series, lag: int = 1) -> float:
        """计算自相关系数"""
        if len(series) <= lag:
            return 0.0
        return float(series.autocorr(lag=lag))

    def _calculate_quality_score(self, basic_stats: dict, outlier_stats: dict, distribution_stats: dict) -> float:
        """计算数据质量评分（0-100）"""
        score = 100.0

        # 缺失值惩罚
        score -= basic_stats['missing_rate'] * 30

        # 异常值惩罚
        total_outliers = outlier_stats['zscore_outliers'] + outlier_stats['iqr_outliers']
        outlier_rate = total_outliers / basic_stats['count'] if basic_stats['count'] > 0 else 0
        score -= outlier_rate * 20

        # 分布异常惩罚
        if abs(distribution_stats['skewness']) > 2:
            score -= 10
        if abs(distribution_stats['kurtosis']) > 5:
            score -= 10

        # 变异系数惩罚
        if distribution_stats['coefficient_of_variation'] > 2:
            score -= 15

        return max(0.0, score)

    def _calculate_data_stats(self, data: pd.DataFrame) -> dict:
        """计算数据统计信息"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        stats_dict = {}

        for col in numeric_columns:
            stats_dict[col] = {
                'mean': float(data[col].mean()),
                'std': float(data[col].std()),
                'min': float(data[col].min()),
                'max': float(data[col].max()),
                'missing_count': int(data[col].isnull().sum()),
                'outlier_count': self._count_outliers_zscore(data[col], 3.0)
            }

        return stats_dict

    def _estimate_sampling_frequency(self, data: pd.DataFrame) -> str:
        """估算采样频率"""
        if 'timestamp' in data.columns and len(data) > 1:
            time_diff = pd.to_datetime(data['timestamp']).diff().median()
            if time_diff.total_seconds() < 1:
                return f"{int(1/time_diff.total_seconds())}Hz"
            else:
                return f"{time_diff.total_seconds()}s"
        return "未知"

    def _normalize_data(self, data: pd.DataFrame, method: str) -> pd.DataFrame:
        """数据标准化"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns

        if method == 'zscore':
            self.scaler = StandardScaler()
        elif method == 'minmax':
            self.scaler = MinMaxScaler()
        elif method == 'robust':
            self.scaler = RobustScaler()

        if self.scaler and len(numeric_columns) > 0:
            data[numeric_columns] = self.scaler.fit_transform(data[numeric_columns])

        return data

    def _resample_data(self, data: pd.DataFrame, freq: str) -> pd.DataFrame:
        """重采样数据"""
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.set_index('timestamp')
            data = data.resample(freq).mean()
            data = data.reset_index()

        return data
