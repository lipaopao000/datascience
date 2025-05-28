import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta


def create_sample_ecg_data():
    """创建示例ECG数据"""
    # 生成时间序列
    start_time = datetime.now() - timedelta(minutes=10)
    time_points = [
        start_time + timedelta(seconds=i * 0.01) for i in range(60000)
    ]  # 100Hz采样，10分钟

    # 生成基础ECG信号
    t = np.linspace(0, 600, 60000)  # 10分钟

    # 模拟ECG信号（简化版）
    heart_rate = 75  # 75 bpm
    ecg_base = np.sin(2 * np.pi * heart_rate / 60 * t)

    # 添加噪声和异常值
    noise = np.random.normal(0, 0.1, len(t))
    ecg_signal = ecg_base + noise

    # 添加一些异常值
    outlier_indices = np.random.choice(len(t), size=100, replace=False)
    ecg_signal[outlier_indices] += np.random.normal(0, 2, 100)

    # 添加一些缺失值
    missing_indices = np.random.choice(len(t), size=200, replace=False)
    ecg_signal[missing_indices] = np.nan

    # 创建多导联数据
    data = {
        'timestamp': time_points,
        'lead_I': ecg_signal,
        'lead_II': ecg_signal * 1.2 + np.random.normal(0, 0.05, len(t)),
        'lead_III': ecg_signal * 0.8 + np.random.normal(0, 0.05, len(t)),
        'aVR': -ecg_signal * 0.5 + np.random.normal(0, 0.05, len(t)),
        'aVL': ecg_signal * 0.6 + np.random.normal(0, 0.05, len(t)),
        'aVF': ecg_signal * 0.9 + np.random.normal(0, 0.05, len(t)),
        'V1': ecg_signal * 0.3 + np.random.normal(0, 0.05, len(t)),
        'V2': ecg_signal * 0.5 + np.random.normal(0, 0.05, len(t)),
        'V3': ecg_signal * 0.8 + np.random.normal(0, 0.05, len(t)),
        'V4': ecg_signal * 1.2 + np.random.normal(0, 0.05, len(t)),
        'V5': ecg_signal * 1.0 + np.random.normal(0, 0.05, len(t)),
        'V6': ecg_signal * 0.6 + np.random.normal(0, 0.05, len(t))
    }

    df = pd.DataFrame(data)
    return df


def create_sample_mv_data():
    """创建示例机械通气数据"""
    # 生成时间序列
    start_time = datetime.now() - timedelta(hours=2)
    time_points = [start_time + timedelta(seconds=i) for i in range(7200)]  # 1Hz采样，2小时

    t = np.linspace(0, 7200, 7200)

    # 模拟机械通气参数
    # 呼吸频率约12次/分钟
    resp_rate = 12
    breathing_cycle = np.sin(2 * np.pi * resp_rate / 60 * t)

    # 压力信号
    pressure_base = 15 + 5 * breathing_cycle + np.random.normal(0, 1, len(t))

    # 流量信号
    flow_base = 0.5 * np.cos(2 * np.pi * resp_rate / 60 * t) + np.random.normal(0, 0.1, len(t))

    # 添加异常值和缺失值
    outlier_indices = np.random.choice(len(t), size=50, replace=False)
    pressure_base[outlier_indices] += np.random.normal(0, 10, 50)

    missing_indices = np.random.choice(len(t), size=100, replace=False)
    pressure_base[missing_indices] = np.nan
    flow_base[missing_indices] = np.nan

    data = {
        'timestamp': time_points,
        'FiO2': np.random.normal(0.21, 0.02, len(t)),  # 氧浓度
        'frequency': np.random.normal(12, 1, len(t)),  # 呼吸频率
        'target_volume': np.random.normal(500, 50, len(t)),  # 目标潮气量
        'PEEP': np.random.normal(5, 0.5, len(t)),  # 呼气末正压
        'pressure': pressure_base,  # 气道压力
        'flow': flow_base  # 气流
    }

    df = pd.DataFrame(data)
    return df


def save_sample_data():
    """保存示例数据"""
    # 确保数据目录存在
    os.makedirs('data/processed', exist_ok=True)

    # 创建并保存ECG数据
    ecg_data = create_sample_ecg_data()
    ecg_data.to_csv('data/processed/patient_001_ecg.csv', index=False)
    print("ECG示例数据已保存到 data/processed/patient_001_ecg.csv")

    # 创建并保存MV数据
    mv_data = create_sample_mv_data()
    mv_data.to_csv('data/processed/patient_002_mv.csv', index=False)
    print("MV示例数据已保存到 data/processed/patient_002_mv.csv")

    # 创建患者信息文件
    patients_info = [
        {
            'id': 'patient_001',
            'name': '患者001 - ECG数据',
            'data_type': 'ecg',
            'file_path': 'data/processed/patient_001_ecg.csv',
            'upload_time': datetime.now().isoformat(),
            'description': '心电图数据，包含12导联，采样频率100Hz，包含噪声和异常值'
        },
        {
            'id': 'patient_002',
            'name': '患者002 - 机械通气数据',
            'data_type': 'mv',
            'file_path': 'data/processed/patient_002_mv.csv',
            'upload_time': datetime.now().isoformat(),
            'description': '机械通气数据，包含压力、流量等参数，采样频率1Hz'
        }
    ]

    import json
    with open('data/processed/patients_info.json', 'w', encoding='utf-8') as f:
        json.dump(patients_info, f, ensure_ascii=False, indent=2)
    print("患者信息已保存到 data/processed/patients_info.json")


if __name__ == "__main__":
    save_sample_data()
