import pandas as pd
import numpy as np
import logging

# --- DI-Specific Helper Functions ---

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value) # Ensure it's a string

def _grade_difficulty_di(difficulty):
    """Grades difficulty based on DI-Doc Chapter 2/6 rules."""
    # Ensure input is numeric before comparison
    difficulty_numeric = pd.to_numeric(difficulty, errors='coerce')
    if pd.isna(difficulty_numeric): return "未知難度"
    
    # 難度分級邏輯，與核心邏輯文件第二章保持一致
    if difficulty_numeric <= -1: return "低難度 (Low) / 505+"
    if -1 < difficulty_numeric <= 0: return "中難度 (Mid) / 555+"
    if 0 < difficulty_numeric <= 1: return "中難度 (Mid) / 605+"
    if 1 < difficulty_numeric <= 1.5: return "中難度 (Mid) / 655+"
    if 1.5 < difficulty_numeric <= 1.95: return "高難度 (High) / 705+"
    if 1.95 < difficulty_numeric <= 2: return "高難度 (High) / 805+"
    
    # 處理超出範圍的情況
    return "未知難度"

def _analyze_dimension(df_filtered, dimension_col):
    """Analyzes performance metrics grouped by a specific dimension column."""
    if df_filtered.empty or dimension_col not in df_filtered.columns:
        return {}

    results = {}
    grouped = df_filtered.groupby(dimension_col)

    for name, group in grouped:
        total = len(group)
        errors = group['is_correct'].eq(False).sum()
        overtime = group['overtime'].eq(True).sum()
        error_rate = errors / total if total > 0 else 0.0
        overtime_rate = overtime / total if total > 0 else 0.0
        avg_difficulty = group['question_difficulty'].mean() if 'question_difficulty' in group.columns else None

        results[name] = {
            'total_questions': total,
            'errors': errors,
            'overtime': overtime,
            'error_rate': error_rate,
            'overtime_rate': overtime_rate,
            'avg_difficulty': avg_difficulty
        }
    return results 