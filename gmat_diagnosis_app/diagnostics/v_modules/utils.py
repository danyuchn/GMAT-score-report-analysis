"""
V診斷模塊的工具函數

此模塊包含用於V(Verbal)診斷的基礎工具函數，
用於格式化、難度分級以及相關計算。
"""

import pandas as pd
import numpy as np

def format_rate(rate_value):
    """Formats a rate value (0 to 1) as a percentage string, handling None/NaN."""
    if isinstance(rate_value, (int, float)) and not pd.isna(rate_value):
        return f"{rate_value:.1%}"
    else:
        return 'N/A'

def grade_difficulty_v(difficulty):
    """Grades the difficulty of a question based on V-Doc Chapter 2/7 rules."""
    # Ensure input is numeric before comparison
    difficulty_numeric = pd.to_numeric(difficulty, errors='coerce')
    if pd.isna(difficulty_numeric): return "Unknown Difficulty"

    if difficulty_numeric <= -1: return "Low / 505+"
    if -1 < difficulty_numeric <= 0: return "Mid / 555+"
    if 0 < difficulty_numeric <= 1: return "Mid / 605+"
    if 1 < difficulty_numeric <= 1.5: return "Mid / 655+"
    if 1.5 < difficulty_numeric <= 1.95: return "High / 705+"
    if 1.95 < difficulty_numeric <= 2: return "High / 805+"
    # 處理超出範圍的情況
    return "Unknown Difficulty" # Default for values outside expected range

def calculate_metrics_for_group(group):
    """Calculates basic metrics for a given group of data."""
    total = len(group)
    if total == 0:
        return {
            'total_questions': 0, 'errors': 0, 'error_rate': 0.0,
            'avg_time_spent': 0.0, 'avg_difficulty': None,
            'overtime_count': 0, 'overtime_rate': 0.0
        }

    errors = group['is_correct'].eq(False).sum()
    error_rate = errors / total
    avg_time_spent = group['question_time'].mean() if 'question_time' in group.columns and group['question_time'].notna().any() else 0.0
    avg_difficulty = group['question_difficulty'].mean() if 'question_difficulty' in group.columns and group['question_difficulty'].notna().any() else None
    overtime_count = group['overtime'].eq(True).sum() if 'overtime' in group.columns else 0
    overtime_rate = overtime_count / total
    return {
        'total_questions': total, 'errors': errors, 'error_rate': error_rate,
        'avg_time_spent': avg_time_spent, 'avg_difficulty': avg_difficulty,
        'overtime_count': overtime_count, 'overtime_rate': overtime_rate
    }

def analyze_dimension(df_filtered, dimension_col):
    """Analyzes performance metrics grouped by a specific dimension column."""
    if df_filtered.empty or dimension_col not in df_filtered.columns:
        return {}
    results = {}
    # Fill NaNs in the dimension column before grouping
    df_filtered[dimension_col] = df_filtered[dimension_col].fillna('Unknown')
    # Use observed=False if pandas version supports it, otherwise default
    try:
        grouped = df_filtered.groupby(dimension_col, observed=False)
    except TypeError:
        grouped = df_filtered.groupby(dimension_col)

    for name, group in grouped:
        # Skip if name is 'Unknown' unless it's the only group
        if name == 'Unknown' and len(grouped) > 1 and dimension_col != 'difficulty_grade': # Allow Unknown Difficulty
             if dimension_col != 'question_fundamental_skill' or name != 'Unknown Skill': # Allow Unknown Skill
                continue
        results[name] = calculate_metrics_for_group(group)
    return results

def calculate_skill_exemption_status(df_v):
    """Calculates the set of exempted skills based on V-Doc Chapter 6."""
    exempted_skills = set()
    # Check if df is empty or required columns are missing
    required_cols_exempt = ['question_fundamental_skill', 'is_correct', 'overtime']
    if df_v.empty or not all(col in df_v.columns for col in required_cols_exempt):
        return exempted_skills

    # Fill NaNs in skill column before grouping
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    try:
        skill_groups = df_v.groupby('question_fundamental_skill', observed=False)
    except TypeError:
        skill_groups = df_v.groupby('question_fundamental_skill')

    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue # Never exempt 'Unknown Skill'
        # 條件一：所有題目必須全部答對
        condition1 = group['is_correct'].all()
        # 條件二：所有題目必須全部無超時
        condition2 = not group['overtime'].any()
        # 兩個條件都滿足才豁免
        if condition1 and condition2:
            exempted_skills.add(skill)
    return exempted_skills

def calculate_skill_override(df_v):
    """Calculates the skill override trigger based on V-Doc Chapter 6."""
    analysis = {'skill_error_rates': {}, 'skill_override_triggered': {}}
    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        return analysis
    # Fill NaNs before grouping
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    try:
        skill_groups = df_v.groupby('question_fundamental_skill', observed=False)
    except TypeError:
        skill_groups = df_v.groupby('question_fundamental_skill')

    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue # Always skip Unknown Skill for override trigger
        total = len(group)
        # Ensure is_correct column exists before summing
        errors = group['is_correct'].eq(False).sum() if 'is_correct' in group.columns else 0
        error_rate = errors / total if total > 0 else 0.0
        analysis['skill_error_rates'][skill] = error_rate
        # 使用 V-Doc Ch6 中定義的 0.50 閾值判斷覆蓋規則
        analysis['skill_override_triggered'][skill] = error_rate > 0.50
    return analysis 