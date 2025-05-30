"""
Q診斷模塊的工具函數

此模塊包含用於Q(Quantitative)診斷的基礎工具函數，
用於格式化、難度分級以及相關計算。
"""

import pandas as pd
import numpy as np
import math
from gmat_diagnosis_app.i18n import translate as t


def format_rate(value):
    """Format a rate value as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def map_difficulty_to_label(difficulty):
    """Map numeric difficulty to descriptive label."""
    if pd.isna(difficulty):
        return t('unknown_difficulty')
    if difficulty <= -1: return t('low_difficulty')
    elif -1 < difficulty <= 0: return t('mid_difficulty_555')
    elif 0 < difficulty <= 1: return t('mid_difficulty_605')
    elif 1 < difficulty <= 1.5: return t('mid_difficulty_655')
    elif 1.5 < difficulty <= 1.95: return t('high_difficulty_705')
    elif 1.95 < difficulty <= 2: return t('high_difficulty_805')
    else: return t('unknown_difficulty')  # 處理超出預期範圍的難度值


def calculate_time_limit_from_avg(avg_time, is_overtime=False):
    """
    根據平均時間計算建議的限時。
    使用向下取整到最近的0.5倍數的函數計算起始限時，
    並設定目標時間為2.0分鐘。
    """
    target_time = 2.0
    
    # 計算基本時間：如果超時，則減少0.5分鐘
    base_time = avg_time - 0.5 if is_overtime else avg_time
    # 向下取整到最近的0.5倍數
    time_limit = math.floor(base_time * 2) / 2
    # 確保不低於目標時間
    time_limit = max(time_limit, target_time)
    
    return time_limit


def map_difficulty_to_label_short(difficulty_numeric):
    """Map numeric difficulty to short descriptive label."""
    if pd.isna(difficulty_numeric): return t('unknown_difficulty_short')
    
    if difficulty_numeric <= -1: return t('low_difficulty')
    if -1 < difficulty_numeric <= 0: return t('mid_difficulty_555')
    if 0 < difficulty_numeric <= 1: return t('mid_difficulty_605')
    if 1 < difficulty_numeric <= 1.5: return t('mid_difficulty_655')
    if 1.5 < difficulty_numeric <= 1.95: return t('high_difficulty_705')
    if 1.95 < difficulty_numeric <= 2: return t('high_difficulty_805')
    return t('unknown_difficulty_short') # Fallback for out of defined range but numeric


def grade_difficulty_q(difficulty):
    """Grades Q difficulty based on Q-Doc Chapter 2 rules."""
    difficulty_numeric = pd.to_numeric(difficulty, errors='coerce')
    if pd.isna(difficulty_numeric): return t('unknown_difficulty')
    
    if difficulty_numeric <= -1: return t('low_difficulty')
    if -1 < difficulty_numeric <= 0: return t('mid_difficulty_555')
    if 0 < difficulty_numeric <= 1: return t('mid_difficulty_605')
    if 1 < difficulty_numeric <= 1.5: return t('mid_difficulty_655')
    if 1.5 < difficulty_numeric <= 1.95: return t('high_difficulty_705')
    if 1.95 < difficulty_numeric <= 2: return t('high_difficulty_805')
    return t('unknown_difficulty') # Fallback for out of defined range but numeric 