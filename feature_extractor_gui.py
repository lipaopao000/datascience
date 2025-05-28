import os
import pandas as pd
import numpy as np
from scipy.stats import iqr, linregress # iqr用于计算四分位距, linregress用于计算线性回归斜率
from tqdm import tqdm # 导入tqdm用于显示进度条
import glob

# --- 配置 ---
# PROCESSED_DATA_PATH: 存放 data_preprocessor_gui.py 输出的 .pkl 文件的文件夹路径
PROCESSED_DATA_PATH = "processed_patient_data"
# OUTPUT_FEATURES_FILE: 最终生成的特征表 (CSV格式) 文件名
OUTPUT_FEATURES_FILE = "patient_features_table.csv"

# 定义在进行衍生特征计算时，使用哪个PEEP列。
# MV_COLS 中有 "PEEP" 和 "peep(呼末正压)"。假设使用 "peep(呼末正压)" (清洗后为 "peep_呼末正压")。
# 如果实际应使用 "PEEP" 列，请修改此变量为 "PEEP" (清洗后的名称)。
PEEP_COL_FOR_CALC = "peep_呼末正压" # 列名已被清洗，原名 "peep(呼末正压)"

# --- 辅助函数 ---
def calculate_stats(series, prefix):
    """
    为给定的pandas Series计算基础统计特征。

    参数:
    - series (pd.Series): 输入的时间序列数据。
    - prefix (str): 生成的特征名前缀 (例如 "ECG_心率")。

    返回:
    - dict: 包含各项统计特征的字典。
    """
    # 如果Series为空或全是NaN，则所有特征都为NaN
    if series.empty or series.isnull().all():
        return {
            f'{prefix}_mean': np.nan, f'{prefix}_median': np.nan, f'{prefix}_std': np.nan,
            f'{prefix}_min': np.nan, f'{prefix}_max': np.nan, f'{prefix}_iqr': np.nan,
            f'{prefix}_slope': np.nan, f'{prefix}_count': 0  # 记录有效数据点数量
        }

    # 再次确保数据是数值类型，并移除NaN值，以便进行统计计算
    series_numeric = pd.to_numeric(series, errors='coerce').dropna()

    # 如果移除NaN后Series为空
    if series_numeric.empty:
        return {
            f'{prefix}_mean': np.nan, f'{prefix}_median': np.nan, f'{prefix}_std': np.nan,
            f'{prefix}_min': np.nan, f'{prefix}_max': np.nan, f'{prefix}_iqr': np.nan,
            f'{prefix}_slope': np.nan, f'{prefix}_count': 0
        }

    features = {
        f'{prefix}_mean': series_numeric.mean(),             # 平均值
        f'{prefix}_median': series_numeric.median(),           # 中位数
        f'{prefix}_std': series_numeric.std(),               # 标准差
        f'{prefix}_min': series_numeric.min(),               # 最小值
        f'{prefix}_max': series_numeric.max(),               # 最大值
        f'{prefix}_iqr': iqr(series_numeric),                # 四分位距
        f'{prefix}_count': series_numeric.count()            # 有效数据点计数
    }

    # 计算斜率 (趋势)
    if len(series_numeric) >= 2: # 至少需要两个点才能计算斜率
        y_values = series_numeric.values
        x_values = np.arange(len(y_values)) # x轴使用简单序列
        try:
            slope, _, _, _, _ = linregress(x_values, y_values)
            features[f'{prefix}_slope'] = slope
        except ValueError: # 如果y_values中所有值都相同，linregress可能报错或返回无意义的值
            # 如果所有值都相同，斜率为0；否则设为NaN
            features[f'{prefix}_slope'] = 0.0 if series_numeric.nunique() == 1 else np.nan
    else:
        features[f'{prefix}_slope'] = np.nan # 数据点不足，斜率设为NaN

    return features

def extract_features_for_patient(patient_id, data_dict):
    """
    为单个病人提取所有指定特征。

    参数:
    - patient_id (str): 病人ID。
    - data_dict (dict): 包含 'ecg_data' 和 'mv_data' 两个DataFrame的字典。

    返回:
    - dict: 包含该病人所有特征的字典。
    """
    all_patient_features = {'patient_id': patient_id} # 初始化特征字典，首先放入病人ID

    # --- 提取ECG特征 ---
    ecg_df = data_dict.get('ecg_data') # 获取ECG数据
    # 预期的ECG列名（已清洗）
    expected_ecg_cols_cleaned = ["_".join(c.split()) for c in ["体温", "心率", "收缩压", "舒张压"]]

    if ecg_df is not None and not ecg_df.empty:
        for col_name in ecg_df.columns: # col_name 已经是清洗后的
            feature_prefix = f'ECG_{col_name}'
            all_patient_features.update(calculate_stats(ecg_df[col_name], feature_prefix))
    else: # 如果没有ECG数据或数据为空，为预期的ECG特征填充NaN
        for col_cleaned_name in expected_ecg_cols_cleaned:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), f'ECG_{col_cleaned_name}'))


    # --- 提取MV特征 ---
    mv_df = data_dict.get('mv_data') # 获取MV数据
    # 预期的MV原始列名（已清洗）
    expected_mv_cols_orig_cleaned = ["_".join(c.split()) for c in [
        "FiO2", "频率", "目标容量", "目标压力", "PEEP", "吸气时间", "呼出潮气量",
        "分钟通气量", "总呼吸频率", "Ppeak(气道峰压)", "Pmean(气道平均压)",
        "pplat(平台压)", "peep(呼末正压)", "动态顺应性", "静态顺应性", "呼吸功",
        "呼气时间", "最大吸气流速", "最大呼气流速"
    ]]
    # 预期的MV衍生特征的基础名
    derived_mv_feature_base_names = [
        'MV_Derived_RSBI', 'MV_Derived_DrivingPressure', 'MV_Derived_Cstat',
        'MV_Derived_Cdyn', 'MV_Derived_IERatio'
    ]

    if mv_df is not None and not mv_df.empty:
        # 1. 为MV数据中的原始列计算基础统计特征
        for col_name in mv_df.columns: # col_name 已经是清洗后的
            feature_prefix = f'MV_{col_name}'
            all_patient_features.update(calculate_stats(mv_df[col_name], feature_prefix))

        # 2. 计算并提取MV的衍生特征
        # 清洗列名，用于在mv_df中查找
        ftotal_col_cleaned = "_".join("总呼吸频率".split())
        vte_col_cleaned = "_".join("呼出潮气量".split())
        pplat_col_cleaned = "_".join("pplat(平台压)".split())
        ppeak_col_cleaned = "_".join("Ppeak(气道峰压)".split())
        ti_col_cleaned = "_".join("吸气时间".split())
        te_col_cleaned = "_".join("呼气时间".split())
        # PEEP_COL_FOR_CALC 已经是清洗后的名称

        # 2a. RSBI (浅快呼吸指数) = 总呼吸频率 / 呼出潮气量 (L)
        # 注意: 假设'呼出潮气量'单位是mL, 转为L。如果已经是L, 则移除 '/ 1000.0'
        if ftotal_col_cleaned in mv_df.columns and vte_col_cleaned in mv_df.columns:
            vte_liters = pd.to_numeric(mv_df[vte_col_cleaned], errors='coerce') / 1000.0
            ftotal = pd.to_numeric(mv_df[ftotal_col_cleaned], errors='coerce')
            rsbi_series = ftotal / (vte_liters + 1e-9) # 加微小量避免除以零
            rsbi_series = rsbi_series.replace([np.inf, -np.inf], np.nan) # 处理无穷大值
            all_patient_features.update(calculate_stats(rsbi_series, 'MV_Derived_RSBI'))
        else:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), 'MV_Derived_RSBI'))

        # 2b. Driving Pressure (驱动压) = Pplat - PEEP
        if pplat_col_cleaned in mv_df.columns and PEEP_COL_FOR_CALC in mv_df.columns:
            pplat_values = pd.to_numeric(mv_df[pplat_col_cleaned], errors='coerce')
            peep_values = pd.to_numeric(mv_df[PEEP_COL_FOR_CALC], errors='coerce')
            driving_pressure_series = pplat_values - peep_values
            all_patient_features.update(calculate_stats(driving_pressure_series, 'MV_Derived_DrivingPressure'))
        else:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), 'MV_Derived_DrivingPressure'))

        # 2c. Static Compliance (Cstat, 静态顺应性) = VTe(L) / (Pplat - PEEP)
        if vte_col_cleaned in mv_df.columns and pplat_col_cleaned in mv_df.columns and PEEP_COL_FOR_CALC in mv_df.columns:
            vte_liters = pd.to_numeric(mv_df[vte_col_cleaned], errors='coerce') / 1000.0 # 确保使用L为单位
            driving_pressure_for_cstat = (pd.to_numeric(mv_df[pplat_col_cleaned], errors='coerce') -
                                          pd.to_numeric(mv_df[PEEP_COL_FOR_CALC], errors='coerce'))
            cstat_series = vte_liters / (driving_pressure_for_cstat + 1e-9)
            cstat_series = cstat_series.replace([np.inf, -np.inf], np.nan)
            all_patient_features.update(calculate_stats(cstat_series, 'MV_Derived_Cstat'))
        else:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), 'MV_Derived_Cstat'))

        # 2d. Dynamic Compliance (Cdyn, 动态顺应性) = VTe(L) / (Ppeak - PEEP)
        if vte_col_cleaned in mv_df.columns and ppeak_col_cleaned in mv_df.columns and PEEP_COL_FOR_CALC in mv_df.columns:
            vte_liters = pd.to_numeric(mv_df[vte_col_cleaned], errors='coerce') / 1000.0 # 确保使用L为单位
            pressure_diff_cdyn = (pd.to_numeric(mv_df[ppeak_col_cleaned], errors='coerce') -
                                  pd.to_numeric(mv_df[PEEP_COL_FOR_CALC], errors='coerce'))
            cdyn_series = vte_liters / (pressure_diff_cdyn + 1e-9)
            cdyn_series = cdyn_series.replace([np.inf, -np.inf], np.nan)
            all_patient_features.update(calculate_stats(cdyn_series, 'MV_Derived_Cdyn'))
        else:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), 'MV_Derived_Cdyn'))

        # 2e. I:E Ratio (吸呼比) = 吸气时间 / 呼气时间
        if ti_col_cleaned in mv_df.columns and te_col_cleaned in mv_df.columns:
            ti_values = pd.to_numeric(mv_df[ti_col_cleaned], errors='coerce')
            te_values = pd.to_numeric(mv_df[te_col_cleaned], errors='coerce')
            ie_ratio_series = ti_values / (te_values + 1e-9) # 加微小量避免除以零
            ie_ratio_series = ie_ratio_series.replace([np.inf, -np.inf], np.nan)
            all_patient_features.update(calculate_stats(ie_ratio_series, 'MV_Derived_IERatio'))
        else:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), 'MV_Derived_IERatio'))
    else: # 如果没有MV数据或数据为空
        # 为预期的MV原始列特征填充NaN
        for col_cleaned_name in expected_mv_cols_orig_cleaned:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), f'MV_{col_cleaned_name}'))
        # 为预期的MV衍生特征填充NaN
        for derived_feature_base_name in derived_mv_feature_base_names:
            all_patient_features.update(calculate_stats(pd.Series(dtype=float), derived_feature_base_name))

    return all_patient_features

# --- 主要特征提取逻辑 ---
def main():
    # 检查预处理数据文件夹是否存在
    if not os.path.exists(PROCESSED_DATA_PATH):
        print(f"错误: 预处理数据文件夹 {PROCESSED_DATA_PATH} 不存在。请先运行 data_preprocessor_gui.py 脚本。")
        return

    # 获取所有已处理的病人数据文件 (.pkl文件)
    processed_patient_files = glob.glob(os.path.join(PROCESSED_DATA_PATH, "*.pkl"))
    if not processed_patient_files:
        print(f"在文件夹 {PROCESSED_DATA_PATH} 中未找到 .pkl 文件。")
        return

    all_extracted_features_list = [] # 用于存储每个病人的特征字典
    print(f"找到 {len(processed_patient_files)} 个已处理的病人数据文件。开始特征提取...")

    # 遍历每个病人的 .pkl 文件
    for pkl_file_path in tqdm(processed_patient_files, desc="正在提取特征"):
        patient_id = os.path.basename(pkl_file_path).replace("_data.pkl", "") # 从文件名获取病人ID
        try:
            patient_data_dict = pd.read_pickle(pkl_file_path) # 读取pickle文件
            features_for_this_patient = extract_features_for_patient(patient_id, patient_data_dict)
            all_extracted_features_list.append(features_for_this_patient)
        except Exception as e:
            print(f"处理文件 {pkl_file_path} (病人ID: {patient_id}) 时出错: {e}")
            # 可选: 如果某个病人出错，是否要添加一行全是NaN的特征？
            # 为简化，此处跳过有错误的病人。

    if not all_extracted_features_list:
        print("未能提取任何特征。将不会创建输出文件。")
        return

    # 将特征列表 (列表内每个元素是一个病人的特征字典) 转换为DataFrame
    final_features_df = pd.DataFrame(all_extracted_features_list)

    # 可选：对列进行排序，使 patient_id 在第一列，然后是ECG特征，然后是MV原始特征，最后是MV衍生特征
    if not final_features_df.empty:
        cols_ordered = ['patient_id']
        feature_keys_sample = [k for k in final_features_df.columns if k != 'patient_id']

        ecg_cols_sorted = sorted([k for k in feature_keys_sample if k.startswith('ECG_')])
        mv_original_cols_sorted = sorted([k for k in feature_keys_sample if k.startswith('MV_') and not k.startswith('MV_Derived_')])
        mv_derived_cols_sorted = sorted([k for k in feature_keys_sample if k.startswith('MV_Derived_')])

        cols_ordered.extend(ecg_cols_sorted)
        cols_ordered.extend(mv_original_cols_sorted)
        cols_ordered.extend(mv_derived_cols_sorted)

        # 添加任何可能遗漏的列 (以防万一)
        remaining_columns = [c for c in final_features_df.columns if c not in cols_ordered]
        cols_ordered.extend(remaining_columns)
        
        try:
            final_features_df = final_features_df[cols_ordered]
        except KeyError as e:
            # 如果排序过程中出现问题（例如某些类型的特征完全缺失），则使用默认的列顺序
            print(f"列重排序时发生键错误: {e}。将使用默认列顺序。")


    # 将最终的特征DataFrame保存到CSV文件
    try:
        final_features_df.to_csv(OUTPUT_FEATURES_FILE, index=False, encoding='utf-8-sig')
        # encoding='utf-8-sig' 确保在Excel中打开包含中文的CSV文件时能正确显示
        print(f"\n特征提取完成！最终特征表保存在: {OUTPUT_FEATURES_FILE}")
        print(f"最终特征表维度: {final_features_df.shape}")
    except Exception as e:
        print(f"保存特征到CSV文件时出错: {e}")

if __name__ == "__main__":
    main()