import pandas as pd
import numpy as np
import plotly.express as px
from scipy.signal import medfilt

# 1. 加载一个病人的 .pkl 文件 (这包含了预处理后的时间序列)
try:
    # 假设这是您 `data_preprocessor_gui.py` 生成的其中一个文件
    patient_data_dict = pd.read_pickle("processed_patient_data/2412739_data.pkl") 
    ecg_df = patient_data_dict.get('ecg_data')
    mv_df = patient_data_dict.get('mv_data')
except FileNotFoundError:
    print("错误：指定的PKL文件未找到。请确保路径和文件名正确。")
    exit()
except Exception as e:
    print(f"加载PKL文件时出错：{e}")
    exit()


# 2. 可视化原始信号 (以ECG的心率和血压为例)
if ecg_df is not None and not ecg_df.empty:
    # 确保列名是清洗后的，与.pkl中存储的一致
    heart_rate_col = "_".join("心率".split())
    systolic_bp_col = "_".join("收缩压".split())
    
    if heart_rate_col in ecg_df.columns:
        fig_hr = px.line(ecg_df, y=heart_rate_col, title=f'病人 {getattr(patient_data_dict, "patient_id", "未知ID")} - 心率')
        fig_hr.show() # 这会打开一个交互式图表

    if systolic_bp_col in ecg_df.columns:
        #fig_sbp = px.line(ecg_df, y=systolic_bp_col, title=f'病人 {getattr(patient_data_dict, "patient_id", "未知ID")} - 收缩压')
        #fig_sbp.show()
        
        # 3. 识别问题 (例如，负的血压值)
        negative_sbp_count = (ecg_df[systolic_bp_col] < 0).sum()
        if negative_sbp_count >= 0:
            print(f"发现 {negative_sbp_count} 个负的收缩压值。")

            # 4. 清洗操作 (示例：将负值替换为NaN，应用中值滤波)
            ecg_df_cleaned = ecg_df.copy()
            ecg_df_cleaned.loc[ecg_df_cleaned[systolic_bp_col] < 0, systolic_bp_col] = np.nan
            
            # 应用中值滤波平滑数据 (窗口大小可以调整)
            if not ecg_df_cleaned[systolic_bp_col].isnull().all(): # 确保不是所有值都为NaN
                 ecg_df_cleaned[systolic_bp_col + '_filtered'] = medfilt(ecg_df_cleaned[systolic_bp_col].fillna(method='ffill').fillna(method='bfill'), kernel_size=5) # 填充NaN以便滤波

            # 5. 可视化清洗后的信号
            fig_sbp_cleaned = px.line(ecg_df_cleaned, y=[systolic_bp_col, systolic_bp_col + '_filtered'], title=f'病人 {getattr(patient_data_dict, "patient_id", "未知ID")} - 清洗和滤波后的收缩压')
            fig_sbp_cleaned.show()
else:
    print("未能加载ECG数据或数据为空。")

# 对MV数据也可以进行类似操作