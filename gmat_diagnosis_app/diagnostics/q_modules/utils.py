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


def calculate_time_limit_from_avg(question_time, is_overtime=False):
    """
    根據MD文檔第七章統一計算規則計算建議的限時。
    
    Args:
        question_time: 原始題目作答時間 (T)
        is_overtime: 是否為超時題目
    
    Returns:
        建議的練習限時 (Z)
    """
    target_time = 2.0  # 目標時間
    
    # 計算base_time：如果是超時（is_slow），則T - 0.5，否則T
    base_time = question_time - 0.5 if is_overtime else question_time
    
    # 向下取整到最近的0.5倍數
    z_raw = math.floor(base_time * 2) / 2
    
    # 確保不低於目標時間
    time_limit = max(z_raw, target_time)
    
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