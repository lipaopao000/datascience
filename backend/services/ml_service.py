import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, silhouette_score
)
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import joblib
import os
import json
from typing import Dict, List, Any, Tuple, Optional # Import Optional
import uuid
from datetime import datetime


class MLService:
    def __init__(self):
        self.models_path = "data/models"
        self.features_path = "data/features"
        os.makedirs(self.models_path, exist_ok=True)

        self.classification_models = {
            'random_forest': RandomForestClassifier,
            'logistic_regression': LogisticRegression,
            'svm': SVC
        }
        self.regression_models = {
            'random_forest': RandomForestRegressor,
            'linear_regression': LinearRegression,
            'svm': SVR
        }
        self.clustering_models = {
            'kmeans': KMeans,
            'dbscan': DBSCAN
        }

    async def train_model(self, data_id: str, model_type: str, features: List[str], target: str, model_params: Dict[str, Any]) -> Dict[str, Any]:
        """训练机器学习模型"""
        try:
            # 加载特定data_id的特征数据
            features_file = os.path.join(self.features_path, f"{data_id}_features.pkl")
            if not os.path.exists(features_file):
                raise Exception(f"特征文件 {features_file} 不存在，请先为 {data_id} 提取特征")

            # 特征文件现在是一个包含单行特征的字典
            features_dict = pd.read_pickle(features_file)
            
            # 将字典转换为单行DataFrame
            # The 'data_id' key should be excluded from features for training
            df_features = pd.DataFrame([{k: v for k, v in features_dict.items() if k != 'data_id'}])

            # 准备数据
            # 'features' list from request now acts as a selector if needed,
            # or we can use all columns from df_features except target.
            # For simplicity, assume 'features' list from request is the list of feature keys to use.
            # If target is part of features_dict (e.g. for supervised learning from raw data), it needs handling.
            # Assuming target is NOT in features_dict and needs to be loaded separately or is part of original data.
            # This part needs careful re-evaluation based on how target variable is sourced.
            # For now, let's assume the target is also a column in the original data, and features are extracted from other columns.
            # This means the current `df_features` is only one row. This is not suitable for training.
            # The ML service should operate on a table where rows are samples and columns are features.
            # The current `extracted_features.csv` was a combined table.
            # We need to decide if ML trains on features of ONE data_id or a COMBINED feature table.
            # For now, let's assume we need a combined feature table.
            
            # --- REVISED LOGIC: Load all feature files and combine them ---
            all_features_data = []
            for filename in os.listdir(self.features_path):
                if filename.endswith('_features.pkl'):
                    file_path = os.path.join(self.features_path, filename)
                    feature_data_row = pd.read_pickle(file_path)
                    all_features_data.append(feature_data_row)
            
            if not all_features_data:
                raise Exception("没有找到任何特征文件用于训练")

            df = pd.DataFrame(all_features_data)
            print(f"DEBUG: Combined features DataFrame shape: {df.shape}")
            print(f"DEBUG: Combined features DataFrame columns: {df.columns.tolist()}")
            print(f"DEBUG: Combined features DataFrame data_ids: {df['data_id'].tolist() if 'data_id' in df.columns else 'data_id column not found'}")

            # Ensure data_id is not used as a feature if present as a column
            if 'data_id' in df.columns and 'data_id' in features:
                features.remove('data_id')
            if 'data_id' in df.columns and 'data_id' == target: # Target should not be data_id
                 raise Exception("data_id cannot be the target variable.")


            X, y, task_type = self._prepare_data(df, features, target) # df is df_features_combined
            model_class = self._get_model_class(model_type, task_type)

            training_history = [] # Initialize
            if task_type == 'clustering':
                model, metrics = self._train_clustering_model(model_class, X, model_params)
                y_pred = model.labels_ if hasattr(model, 'labels_') else model.predict(X)
            else:
                model, metrics, y_pred, training_history = self._train_supervised_model(
                    model_class, X, y, task_type, model_params
                )

            model_id = str(uuid.uuid4())
            model_info = {
                'model_id': model_id,
                'model_type': model_type,
                'task_type': task_type,
                'features': features, # List of feature names used
                'target': target,
                'model_params': model_params,
                'metrics': metrics,
                'created_at': datetime.now().isoformat(),
                'data_shape': X.shape,
                'training_history': training_history,
                'trained_on_data_ids': df['data_id'].tolist() if 'data_id' in df.columns else [data_id] # Track which data_ids were used
            }
            self._save_model(model, model_info, model_id)

            return {
                'model_id': model_id,
                'metrics': metrics,
                'predictions': y_pred.tolist() if hasattr(y_pred, 'tolist') else y_pred,
                'training_history': training_history
            }
        except Exception as e:
            raise Exception(f"模型训练失败: {e}")

    async def predict(self, model_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """使用模型进行预测"""
        try:
            model, model_info = self._load_model(model_id)
            feature_names = model_info['features']
            
            # Ensure all required features are present in the input, fill with 0 or mean if not.
            # This assumes 'features' is a flat dict for a single prediction.
            X_pred_list = []
            for fname in feature_names:
                X_pred_list.append(features.get(fname, 0)) # Default to 0 if feature missing

            X_pred = np.array([X_pred_list])


            scaler_path = os.path.join(self.models_path, f"{model_id}_scaler.pkl")
            if os.path.exists(scaler_path):
                scaler = joblib.load(scaler_path)
                X_pred = scaler.transform(X_pred)

            if model_info['task_type'] == 'classification':
                prediction = model.predict(X_pred)[0]
                probabilities = model.predict_proba(X_pred)[0].tolist() if hasattr(model, 'predict_proba') else None
                return {'prediction': int(prediction) if isinstance(prediction, np.integer) else prediction, 'probabilities': probabilities}
            elif model_info['task_type'] == 'regression':
                return {'prediction': float(model.predict(X_pred)[0])}
            elif model_info['task_type'] == 'clustering':
                return {'cluster': int(model.predict(X_pred)[0])}
        except Exception as e:
            raise Exception(f"预测失败: {e}")

    def _prepare_data(self, df_features_combined: pd.DataFrame, features_to_use: List[str], target_column_name: str) -> Tuple[np.ndarray, Optional[np.ndarray], str]:
        """
        准备训练数据.
        df_features_combined: DataFrame where each row is a data_id and columns are extracted features + 'data_id'.
        features_to_use: List of feature column names to select from df_features_combined.
        target_column_name: Name of the target column in the original raw data.
        """
        from services.data_processor import DataProcessor # Local import to avoid circular dependency at module level
        data_processor = DataProcessor()

        missing_features = [f for f in features_to_use if f not in df_features_combined.columns]
        if missing_features:
            raise Exception(f"以下特征不存在于提取的特征表中: {', '.join(missing_features)}")

        # Select only specified features and data_id for merging
        cols_for_X_df = features_to_use + ['data_id']
        # Ensure no duplicates if 'data_id' was accidentally in features_to_use
        cols_for_X_df = sorted(list(set(cols_for_X_df))) 
        
        X_df = df_features_combined[cols_for_X_df].copy()
        
        # Fill NaNs only in numeric feature columns
        numeric_feature_cols = X_df[features_to_use].select_dtypes(include=np.number).columns
        X_df[numeric_feature_cols] = X_df[numeric_feature_cols].fillna(X_df[numeric_feature_cols].mean())


        if target_column_name == 'clustering': # Special case for clustering
            # Return only the feature values, data_id is not needed for X in clustering
            return X_df[features_to_use].values, None, 'clustering'

        # --- Load and aggregate target variable from original data ---
        target_values = []
        processed_data_ids_for_target = []

        for data_id in df_features_combined['data_id']:
            raw_data_df = data_processor.load_patient_data(data_id)
            
            if raw_data_df is None:
                print(f"DEBUG: Raw data for data_id '{data_id}' could not be loaded. Skipping for target extraction.")
                continue

            print(f"DEBUG: Raw data columns for data_id '{data_id}': {raw_data_df.columns.tolist()}")
            
            # The target_column_name comes from the frontend, which sees cleaned column names from data_details.
            # The raw_data_df here has also had its column names cleaned by DataProcessor.
            if target_column_name not in raw_data_df.columns:
                print(f"警告: 目标列 '{target_column_name}' 在数据ID '{data_id}' 的原始数据中未找到 (可用列: {raw_data_df.columns.tolist()})。该样本将从训练中排除。")
                continue
            
            target_series = pd.to_numeric(raw_data_df[target_column_name], errors='coerce').dropna()
            if not target_series.empty:
                aggregated_target = target_series.mean()
                target_values.append(aggregated_target)
                processed_data_ids_for_target.append(data_id)
            else:
                print(f"警告: 目标列 '{target_column_name}' 在数据ID '{data_id}' 中没有有效的数值数据用于聚合。该样本将从训练中排除。")


        if not target_values:
            raise Exception(f"无法从任何数据集中提取有效的目标变量 '{target_column_name}'。")

        df_target = pd.DataFrame({'data_id': processed_data_ids_for_target, target_column_name: target_values})
        
        # Merge features with target
        # X_df already has data_id, df_target has data_id and the target
        final_df = pd.merge(X_df, df_target, on='data_id', how='inner')

        if final_df.empty:
            raise Exception("特征数据和目标数据合并后为空，请检查data_id是否匹配或目标数据是否有效。")
        
        print(f"DEBUG: final_df shape after merging features and target: {final_df.shape}")
        print(f"DEBUG: final_df columns: {final_df.columns.tolist()}")


        X_prepared = final_df[features_to_use].values
        y_series = final_df[target_column_name]
        
        if y_series.dtype == 'object' or len(y_series.unique()) < 10:
            task_type = 'classification'
            le = LabelEncoder()
            y_encoded = le.fit_transform(y_series)
            # Store label encoder mapping if needed for inverse transform later
        else:
            task_type = 'regression'
            y_encoded = y_series.values

        return X_prepared, y_encoded, task_type

    def _get_model_class(self, model_type: str, task_type: str):
        """获取模型类"""
        if task_type == 'classification':
            if model_type not in self.classification_models:
                raise Exception(f"不支持的分类模型: {model_type}")
            return self.classification_models[model_type]
        elif task_type == 'regression':
            if model_type not in self.regression_models:
                raise Exception(f"不支持的回归模型: {model_type}")
            return self.regression_models[model_type]
        elif task_type == 'clustering':
            if model_type not in self.clustering_models:
                raise Exception(f"不支持的聚类模型: {model_type}")
            return self.clustering_models[model_type]
        else:
            raise Exception(f"不支持的任务类型: {task_type}")

    def _train_supervised_model(self, model_class, X: np.ndarray, y: np.ndarray, task_type: str, model_params: Dict[str, Any]) -> Tuple[Any, Dict[str, Any], np.ndarray, List[Dict[str, Any]]]:
        if X.shape[0] <= 1:
            raise ValueError(f"训练样本数量不足 ({X.shape[0]})，无法进行训练/测试分割。请确保有足够的数据包含所选的目标变量。")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Adjust test_size if n_samples is small to avoid empty train set
        # For example, if n_samples is 2, test_size=0.2 (1 sample) would leave 1 for training.
        # If n_samples is 1, it's already caught above.
        # If n_samples is very small (e.g., < 5), train_test_split might still be problematic with stratification.
        # A common minimum is test_size=1 sample.
        current_test_size = 0.2
        if X.shape[0] * (1 - current_test_size) < 1 : # if training set would be less than 1
            # This case should be caught by X.shape[0] <=1, but as a safeguard
            raise ValueError(f"样本数量 ({X.shape[0]}) 过少，无法以测试集比例 {current_test_size} 进行分割。")

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=current_test_size, random_state=42, stratify=y if task_type == 'classification' and len(np.unique(y)) > 1 else None
        )
        
        if X_train.shape[0] == 0:
            raise ValueError(f"分割后的训练集为空。原始样本数: {X.shape[0]}, 测试集比例: {current_test_size}。请检查数据或调整分割比例。")


        model = model_class(**model_params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = {}
        if task_type == 'classification':
            metrics = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
            }
            if len(np.unique(y_test)) > 1 and hasattr(model, 'predict_proba'): # Ensure y_test has more than 1 class for AUC
                 try:
                    y_proba = model.predict_proba(X_test)[:, 1]
                    metrics['auc'] = float(roc_auc_score(y_test, y_proba))
                 except ValueError:
                    metrics['auc'] = None # Not applicable for single class in y_test
        else:  # regression
            metrics = {
                'mse': float(mean_squared_error(y_test, y_pred)),
                'mae': float(mean_absolute_error(y_test, y_pred)),
                'r2': float(r2_score(y_test, y_pred)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred)))
            }
        
        # Cross-validation might fail if y has only one class after split
        try:
            cv_scores = cross_val_score(model, X_scaled, y, cv=5)
            metrics['cv_mean'] = float(cv_scores.mean())
            metrics['cv_std'] = float(cv_scores.std())
        except ValueError: # Handle cases like single class in y for CV
            metrics['cv_mean'] = None
            metrics['cv_std'] = None


        training_history = []
        if hasattr(model, 'loss_curve_'): 
            training_history = [{'epoch': i+1, 'loss': float(loss_val)} for i, loss_val in enumerate(model.loss_curve_)]
        elif hasattr(model, 'history_') and isinstance(model.history_, dict) and 'loss' in model.history_: 
            training_history = [{'epoch': i+1, 'loss': float(loss_val)} for i, loss_val in enumerate(model.history_['loss'])]
        
        # Save scaler
        model_id_for_scaler = str(uuid.uuid4()) # Temporary ID for scaler, or link to actual model_id
        scaler_path = os.path.join(self.models_path, f"{model_id_for_scaler}_scaler.pkl") # This needs to be linked to the actual model_id
        # joblib.dump(scaler, scaler_path) # We need the actual model_id before saving scaler

        return model, metrics, y_pred, training_history

    def _train_clustering_model(self, model_class, X: np.ndarray, model_params: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = model_class(**model_params)
        labels = model.fit_predict(X_scaled) if hasattr(model, 'fit_predict') else model.fit(X_scaled).labels_
        metrics = {}
        if len(np.unique(labels)) > 1:
            metrics['silhouette_score'] = float(silhouette_score(X_scaled, labels))
        else:
            metrics['silhouette_score'] = -1.0 # Or None, or some other indicator
        metrics['n_clusters'] = int(len(np.unique(labels)))
        if hasattr(model, 'inertia_'):
            metrics['inertia'] = float(model.inertia_)
        return model, metrics

    def _save_model(self, model: Any, model_info: Dict[str, Any], model_id: str):
        model_path = os.path.join(self.models_path, f"{model_id}_model.pkl")
        joblib.dump(model, model_path)
        info_path = os.path.join(self.models_path, f"{model_id}_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
        
        # Save scaler if it was used (assuming it's passed or accessible)
        # This part needs refinement: scaler should be saved with the model
        # For now, this is a placeholder. The scaler should be part of the model pipeline or saved separately with a clear link.
        # if 'scaler' in model_info: # Hypothetical
        #     scaler_path = os.path.join(self.models_path, f"{model_id}_scaler.pkl")
        #     joblib.dump(model_info['scaler'], scaler_path)


    def _load_model(self, model_id: str) -> Tuple[Any, Dict[str, Any]]:
        model_path = os.path.join(self.models_path, f"{model_id}_model.pkl")
        info_path = os.path.join(self.models_path, f"{model_id}_info.json")
        if not os.path.exists(model_path) or not os.path.exists(info_path):
            raise Exception(f"模型 {model_id} 不存在")
        model = joblib.load(model_path)
        with open(info_path, 'r', encoding='utf-8') as f:
            model_info = json.load(f)
        return model, model_info

    def get_model_list(self) -> List[Dict[str, Any]]:
        models = []
        for filename in os.listdir(self.models_path):
            if filename.endswith('_info.json'):
                info_path = os.path.join(self.models_path, filename)
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        model_info = json.load(f)
                    models.append(model_info)
                except Exception as e:
                    print(f"Error loading model info {filename}: {e}")
        models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return models

    def delete_model(self, model_id: str) -> bool:
        try:
            model_path = os.path.join(self.models_path, f"{model_id}_model.pkl")
            info_path = os.path.join(self.models_path, f"{model_id}_info.json")
            scaler_path = os.path.join(self.models_path, f"{model_id}_scaler.pkl") # Also delete scaler
            files_to_delete = [model_path, info_path, scaler_path]
            deleted_count = 0
            for file_path in files_to_delete:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count +=1
            return deleted_count > 0 # Return true if at least model or info was deleted
        except Exception as e:
            raise Exception(f"删除模型失败: {e}")

    def get_training_history(self, model_id: str) -> List[Dict[str, Any]]:
        try:
            _, model_info = self._load_model(model_id)
            return model_info.get('training_history', [])
        except Exception as e:
            raise Exception(f"获取训练历史失败: {e}")

    async def evaluate_model(self, model_id: str) -> Dict[str, Any]:
        # This method needs to be re-evaluated based on how data for evaluation is sourced.
        # It currently re-loads "extracted_features.csv" which is no longer the primary way features are stored.
        raise NotImplementedError("Model evaluation needs to be updated for new feature storage.")

    async def get_feature_importance(self, model_id: str) -> Dict[str, Any]:
        try:
            model, model_info = self._load_model(model_id)
            feature_names = model_info['features']
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                importance_dict = {name: float(importance) for name, importance in zip(feature_names, importances)}
                return {'feature_importance': dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))}
            elif hasattr(model, 'coef_'):
                coefficients = model.coef_[0] if model.coef_.ndim > 1 else model.coef_
                coef_dict = {name: float(coef) for name, coef in zip(feature_names, coefficients)}
                return {'coefficients': dict(sorted(coef_dict.items(), key=lambda x: abs(x[1]), reverse=True))}
            else:
                return {'message': '该模型不支持特征重要性分析'}
        except Exception as e:
            raise Exception(f"获取特征重要性失败: {e}")

    async def perform_dimensionality_reduction(self, method: str = 'pca', n_components: int = 2) -> Dict[str, Any]:
        # This method also needs re-evaluation for feature data sourcing.
        raise NotImplementedError("Dimensionality reduction needs to be updated for new feature storage.")
