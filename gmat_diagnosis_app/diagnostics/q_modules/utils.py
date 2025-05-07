"""
Q診斷模塊的工具函數

此模塊包含用於Q(Quantitative)診斷的基礎工具函數，
用於格式化、難度分級以及相關計算。
"""

import pandas as pd
import numpy as np


def format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value)


def map_difficulty_to_label(difficulty):
    """Maps numeric difficulty (b-value) to descriptive label based on Ch2 rules."""
    if difficulty is None or pd.isna(difficulty):
        return "未知難度 (Unknown)"
    if difficulty <= -1: return "低難度 (Low) / 505+"
    elif -1 < difficulty <= 0: return "中難度 (Mid) / 555+"
    elif 0 < difficulty <= 1: return "中難度 (Mid) / 605+"
    elif 1 < difficulty <= 1.5: return "中難度 (Mid) / 655+"
    elif 1.5 < difficulty <= 1.95: return "高難度 (High) / 705+"
    elif 1.95 < difficulty <= 2: return "高難度 (High) / 805+"
    else: return "未知難度 (Unknown)"  # 處理超出預期範圍的難度值


def calculate_practice_time_limit(item_time, is_overtime):
    """
    Calculates the starting practice time limit (Z) based on Ch7 rules.
    使用向下取整到最近的0.5倍數的函數計算起始限時，
    並設定目標時間為2.0分鐘。
    """
    if item_time is None or pd.isna(item_time): return 2.0
    target_time = 2.0
    # 計算基本時間：如果超時，則減少0.5分鐘
    base_time = item_time - 0.5 if is_overtime else item_time
    # 向下取整到最近的0.5倍數
    z_raw = np.floor(base_time * 2) / 2
    # 確保不低於目標時間
    z = max(z_raw, target_time)
    return z


def grade_difficulty_q(difficulty):
    """Grades Q difficulty based on Q-Doc Chapter 2 rules."""
    difficulty_numeric = pd.to_numeric(difficulty, errors='coerce')
    if pd.isna(difficulty_numeric): return "未知難度"
    
    if difficulty_numeric <= -1: return "低難度 (Low) / 505+"
    if -1 < difficulty_numeric <= 0: return "中難度 (Mid) / 555+"
    if 0 < difficulty_numeric <= 1: return "中難度 (Mid) / 605+"
    if 1 < difficulty_numeric <= 1.5: return "中難度 (Mid) / 655+"
    if 1.5 < difficulty_numeric <= 1.95: return "高難度 (High) / 705+"
    if 1.95 < difficulty_numeric <= 2: return "高難度 (High) / 805+"
    return "未知難度" # Fallback for out of defined range but numeric 