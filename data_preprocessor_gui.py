import os
import pandas as pd
import glob
import zipfile
from tqdm import tqdm  # 导入tqdm用于显示进度条
import tkinter as tk
from tkinter import filedialog, simpledialog

# --- 配置 ---
# OUTPUT_PROCESSED_DATA_PATH: 处理后的病人数据（.pkl文件）将存储在此文件夹
OUTPUT_PROCESSED_DATA_PATH = "processed_patient_data" # 处理后的.pkl文件存放目录

# 定义ECG和MV文件需要保留的列名
ECG_COLS = ["体温", "心率", "收缩压", "舒张压"]
MV_COLS = [
    "FiO2", "频率", "目标容量", "目标压力", "PEEP", "吸气时间", "呼出潮气量",
    "分钟通气量", "总呼吸频率", "Ppeak(气道峰压)", "Pmean(气道平均压)",
    "pplat(平台压)", "peep(呼末正压)", "动态顺应性", "静态顺应性", "呼吸功",
    "呼气时间", "最大吸气流速", "最大呼气流速"
]

# --- 辅助函数 ---
def clean_col_names(df):
    """
    清洗DataFrame的列名，去除多余空格，并将多个空格替换为单个下划线。
    """
    df.columns = ["_".join(col.split()) for col in df.columns]
    return df

def process_csv_files(file_paths, required_cols):
    """
    读取并合并多个CSV文件，只选择所需的列。

    参数:
    - file_paths (list): CSV文件路径列表。
    - required_cols (list): 需要从CSV中提取的原始列名列表。

    返回:
    - pandas.DataFrame: 合并后的数据，只包含所需的、经过清洗和数值转换的列。
    """
    dfs = []  # 用于存储从每个CSV读取的DataFrame
    cleaned_required_cols = ["_".join(col.split()) for col in required_cols] # 预先清洗目标列名

    for f_path in sorted(file_paths):  # 对文件路径排序，尽量保证时序性
        try:
            df = pd.read_csv(f_path, on_bad_lines='skip') # 读取CSV，跳过损坏的行
            df = clean_col_names(df)  # 清洗列名

            # 筛选出实际存在于文件中的目标列
            current_cols_to_select = [col for col in cleaned_required_cols if col in df.columns]

            if not current_cols_to_select:
                # print(f"警告: 文件 {f_path} 中未找到任何目标列。已跳过此文件。") # 在tqdm中频繁打印不太好
                continue

            df_selected = df[current_cols_to_select].copy() # 使用 .copy() 避免 SettingWithCopyWarning

            # 将所有选中的列转换为数值类型，无法转换的变为NaN
            for col in df_selected.columns:
                df_selected.loc[:, col] = pd.to_numeric(df_selected[col], errors='coerce')

            dfs.append(df_selected)
        except pd.errors.EmptyDataError:
            # print(f"警告: 文件为空: {f_path}")
            pass # 在tqdm中不打印
        except Exception as e:
            # print(f"处理文件 {f_path} 时出错: {e}")
            pass # 在tqdm中不打印

    if not dfs:
        # 如果没有成功读取任何文件，返回一个带有清洗后目标列名的空DataFrame
        return pd.DataFrame(columns=cleaned_required_cols)

    # 合并所有DataFrames
    # 假设数据是1Hz的，合并后的索引如果文件是连续的，则代表秒数
    full_df = pd.concat(dfs, ignore_index=True)
    return full_df

def get_input_path():
    """
    使用Tkinter弹出对话框让用户选择输入源 (ZIP文件或文件夹)。
    返回选择的路径和类型 ('zip' 或 'folder')。
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    input_type = simpledialog.askstring("输入类型", "选择输入类型:\n1. ZIP压缩包\n2. 已解压的文件夹\n请输入 1 或 2:", parent=root)

    path = ""
    source_type = ""

    if input_type == '1':
        path = filedialog.askopenfilename(title="选择ZIP压缩文件", filetypes=[("ZIP files", "*.zip")])
        source_type = 'zip'
    elif input_type == '2':
        path = filedialog.askdirectory(title="选择包含病人ID的根文件夹")
        source_type = 'folder'
    else:
        print("无效的输入类型选择。程序将退出。")
        return None, None

    if not path: # 如果用户取消选择
        print("未选择任何输入。程序将退出。")
        return None, None

    return path, source_type

# --- 主要处理逻辑 ---
def main():
    # 1. 获取用户选择的输入路径和类型
    input_path, source_type = get_input_path()

    if not input_path or not source_type:
        return # 用户取消或输入无效，退出程序

    actual_data_path = "" # 实际存放病人一级ID文件夹的路径

    if source_type == 'zip':
        # 解压ZIP文件到临时目录
        extract_to_folder = "temp_extracted_patient_data" # 定义解压目标文件夹
        if os.path.exists(extract_to_folder):
            print(f"警告: 临时解压目录 {extract_to_folder} 已存在，将尝试使用现有内容或选择性覆盖。")
        else:
            os.makedirs(extract_to_folder, exist_ok=True) # 创建目录，如果存在则不报错

        print(f"开始从 {input_path} 选择性解压 ECG*.csv 和 MV*.csv 文件到 {extract_to_folder}...")
        extracted_count = 0
        try:
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                # 获取zip文件中的所有成员名称列表
                member_list = zip_ref.namelist()
                for member_name in tqdm(member_list, desc="扫描ZIP包内容"):
                    # 获取成员的基本文件名（不含路径的部分）
                    base_filename = os.path.basename(member_name)
                    # 检查是否是我们要的文件类型，并且确保它不是一个目录
                    if (base_filename.startswith("ECG") or base_filename.startswith("MV")) and \
                       base_filename.endswith(".csv") and \
                       not member_name.endswith('/'): # 确保不是目录条目
                        try:
                            zip_ref.extract(member_name, extract_to_folder)
                            extracted_count += 1
                        except Exception as extract_err:
                            print(f"解压文件 {member_name} 时出错: {extract_err}")
            if extracted_count > 0:
                print(f"选择性解压完成。共解压 {extracted_count} 个相关CSV文件。")
            else:
                print("警告: 在ZIP文件中未找到符合条件的ECG*.csv或MV*.csv文件进行解压。")
            actual_data_path = extract_to_folder
        except zipfile.BadZipFile:
            print(f"错误: {input_path} 不是一个有效的ZIP文件或文件已损坏。")
            return
        except Exception as e:
            print(f"处理ZIP文件时出错: {e}")
            return
    elif source_type == 'folder':
        actual_data_path = input_path

    if not actual_data_path or not os.path.isdir(actual_data_path):
        print(f"错误: 无法访问数据路径 {actual_data_path}。请检查路径或ZIP文件结构。")
        return

    # 2. 创建输出目录 (如果不存在)
    if not os.path.exists(OUTPUT_PROCESSED_DATA_PATH):
        os.makedirs(OUTPUT_PROCESSED_DATA_PATH)

    # 3. 获取病人ID列表 (即actual_data_path下的第一层文件夹名)
    try:
        # 确保actual_data_path下的内容是病人ID文件夹
        # 有时解压后可能会多一层与zip同名的文件夹，需要用户注意或脚本进行调整
        # 例如，如果zip文件名是 data.zip, 解压后是 data/patient_id/...
        # 那么 actual_data_path 应该是 os.path.join(extract_to_folder, "data")
        # 为简化，当前脚本假设 actual_data_path 直接包含了病人ID文件夹
        
        # 检查 actual_data_path 是否真的包含了病人ID文件夹，还是需要再进入一层
        # 这是一个简单的检查，如果只有一个子目录，并且这个子目录名和解压的zip文件名相似，可能需要深入一层
        # 这个逻辑比较复杂，暂时保持现状，用户需要保证 actual_data_path 的正确性
        
        patient_ids = [pid for pid in os.listdir(actual_data_path) if os.path.isdir(os.path.join(actual_data_path, pid))]
    except FileNotFoundError:
        print(f"错误: 无法在路径 {actual_data_path} 中列出文件夹。请检查路径。")
        return

    if not patient_ids:
        print(f"在 {actual_data_path} 中未找到病人ID文件夹。请检查ZIP解压后的结构或选择的文件夹。")
        return

    print(f"找到 {len(patient_ids)} 个病人文件夹。开始数据预处理...")

    # 遍历每个病人ID
    for patient_id in tqdm(patient_ids, desc="正在处理病人数据"):
        patient_folder_path = os.path.join(actual_data_path, patient_id) # 单个病人的文件夹路径
        patient_ecg_files = []  # 存储该病人所有ECG文件路径
        patient_mv_files = []   # 存储该病人所有MV文件路径

        # 遍历病人文件夹下的时间范围子文件夹 (第二层)
        # 对时间范围文件夹进行排序，以期保证数据的时间顺序
        time_range_folders = []
        if os.path.isdir(patient_folder_path): # 确保病人文件夹存在
            time_range_folders = sorted([
                os.path.join(patient_folder_path, trf) for trf in os.listdir(patient_folder_path)
                if os.path.isdir(os.path.join(patient_folder_path, trf))
            ])
        else:
            print(f"警告: 病人文件夹 {patient_folder_path} 未找到或不是目录。跳过病人 {patient_id}")
            continue


        for time_folder_path in time_range_folders: # 第三层，具体数据文件
            # 查找ECG文件，文件名以ECG开头，.csv结尾
            ecg_files_in_folder = glob.glob(os.path.join(time_folder_path, "ECG*.csv"))
            patient_ecg_files.extend(sorted(ecg_files_in_folder)) # 排序后添加

            # 查找MV文件，文件名以MV开头，.csv结尾
            mv_files_in_folder = glob.glob(os.path.join(time_folder_path, "MV*.csv"))
            patient_mv_files.extend(sorted(mv_files_in_folder)) # 排序后添加
        
        # 如果选择性解压后，文件可能直接在 patient_id 目录下，而不是 time_range_folder 下
        # 添加一个逻辑来检查 patient_folder_path 根目录下的文件
        if not patient_ecg_files and not patient_mv_files : # 如果在时间子文件夹没找到
            # print(f"在病人 {patient_id} 的时间子文件夹中未找到ECG/MV文件，尝试直接在病人目录下查找...")
            ecg_files_in_patient_root = glob.glob(os.path.join(patient_folder_path, "ECG*.csv"))
            patient_ecg_files.extend(sorted(ecg_files_in_patient_root))

            mv_files_in_patient_root = glob.glob(os.path.join(patient_folder_path, "MV*.csv"))
            patient_mv_files.extend(sorted(mv_files_in_patient_root))


        # --- 为当前病人整合ECG数据 ---
        # 初始化一个空的DataFrame，列名使用预定义的ECG_COLS（清洗后）
        patient_ecg_df = pd.DataFrame(columns=["_".join(col.split()) for col in ECG_COLS])
        if patient_ecg_files:
            patient_ecg_df = process_csv_files(patient_ecg_files, ECG_COLS)
        # else: # 不再打印，因为tqdm会覆盖
            # print(f"病人 {patient_id} 未找到ECG文件。")

        # --- 为当前病人整合MV数据 ---
        patient_mv_df = pd.DataFrame(columns=["_".join(col.split()) for col in MV_COLS])
        if patient_mv_files:
            patient_mv_df = process_csv_files(patient_mv_files, MV_COLS)
        # else:
            # print(f"病人 {patient_id} 未找到MV文件。")

        # --- 存储处理好的数据 ---
        # 使用pickle格式保存一个字典，包含ECG和MV两个DataFrame
        if not patient_ecg_df.empty or not patient_mv_df.empty: # 只有当至少有一个df不为空时才保存
            output_file_path = os.path.join(OUTPUT_PROCESSED_DATA_PATH, f"{patient_id}_data.pkl")
            try:
                pd.to_pickle({
                    'ecg_data': patient_ecg_df,
                    'mv_data': patient_mv_df
                }, output_file_path)
            except Exception as e:
                print(f"为病人 {patient_id} 保存数据时出错: {e}")
        # else: # 不再打印
            # print(f"病人 {patient_id} 未找到任何ECG或MV数据，不保存空的pickle文件。")


    print("\n数据预处理完成！")
    print(f"处理后的数据 (.pkl 文件) 保存在: {OUTPUT_PROCESSED_DATA_PATH}")

if __name__ == "__main__":
    main()