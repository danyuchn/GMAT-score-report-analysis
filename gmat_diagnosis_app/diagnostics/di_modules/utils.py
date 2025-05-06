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

def _calculate_msr_metrics(df):
    """Calculates MSR group total time and reading time (for first question).
       Assumes MSR questions are grouped by a 'msr_group_id' column.
       Adds 'msr_group_total_time', 'msr_reading_time', and 'is_first_msr_q' columns.
    """
    # logging.debug(f"[_calculate_msr_metrics] Input df shape: {df.shape}")
    if df.empty or 'msr_group_id' not in df.columns or 'question_time' not in df.columns:
        # logging.debug("[_calculate_msr_metrics] Input df empty or missing required columns. Initializing MSR columns to NaN/False.")
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column
        return df

    df_msr = df[df['question_type'] == 'Multi-source reasoning'].copy()
    # logging.debug(f"[_calculate_msr_metrics] df_msr shape: {df_msr.shape}")
    if df_msr.empty:
        # logging.debug("[_calculate_msr_metrics] No MSR rows found. Initializing MSR columns to NaN/False.")
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column even if no MSR
        return df

    group_times = df_msr.groupby('msr_group_id')['question_time'].sum()
    # logging.debug(f"[_calculate_msr_metrics] Calculated group_times series (len: {len(group_times)}):\\n{group_times.head()}")
    # Assignment 1: Map group times
    try:
        # logging.debug(f"[_calculate_msr_metrics] Assigning 'msr_group_total_time'. df_msr shape: {df_msr.shape}, map series len: {len(df_msr['msr_group_id'].map(group_times))}")
        df_msr['msr_group_total_time'] = df_msr['msr_group_id'].map(group_times)
    except Exception as e:
        logging.error(f"[_calculate_msr_metrics] Error assigning 'msr_group_total_time': {e}", exc_info=True)
        raise e

    reading_times = {}
    first_q_indices = set()
    for group_id, group_df in df_msr.groupby('msr_group_id'):
        group_df_sorted = group_df.sort_values('question_position')
        first_q_index = group_df_sorted.index[0]
        first_q_indices.add(first_q_index)

        if len(group_df_sorted) >= 2:
            first_q_time = group_df_sorted['question_time'].iloc[0]
            other_q_times_avg = group_df_sorted['question_time'].iloc[1:].mean()
            # Handle potential NaN in average calculation if only 2 questions and one has NaN time
            if pd.notna(first_q_time) and pd.notna(other_q_times_avg):
                 reading_time = first_q_time - other_q_times_avg
                 reading_times[first_q_index] = reading_time
            else:
                 reading_times[first_q_index] = np.nan # Cannot calculate reading time if times are missing
        elif len(group_df_sorted) == 1:
             reading_times[first_q_index] = np.nan

    # Assignment 2: Map reading times
    try:
        reading_times_series = df_msr.index.map(reading_times)
        # logging.debug(f"[_calculate_msr_metrics] Assigning 'msr_reading_time'. df_msr shape: {df_msr.shape}, reading_times_series len: {len(reading_times_series)}")
        df_msr['msr_reading_time'] = reading_times_series
    except Exception as e:
        logging.error(f"[_calculate_msr_metrics] Error assigning 'msr_reading_time': {e}", exc_info=True)
        raise e

    # Assignment 3: Assign boolean for first MSR question
    try:
        is_first_q_series = df_msr.index.isin(first_q_indices)
        # logging.debug(f"[_calculate_msr_metrics] Assigning 'is_first_msr_q'. df_msr shape: {df_msr.shape}, is_first_q_series len: {len(is_first_q_series)}")
        df_msr['is_first_msr_q'] = is_first_q_series
    except Exception as e:
        logging.error(f"[_calculate_msr_metrics] Error assigning 'is_first_msr_q': {e}", exc_info=True)
        raise e

    # Assignment 4: Merge back into original df
    df_to_merge = df_msr[['msr_group_total_time', 'msr_reading_time', 'is_first_msr_q']]
    # logging.debug(f"[_calculate_msr_metrics] Merging MSR columns back. Original df shape: {df.shape}, df_to_merge shape: {df_to_merge.shape}")
    try:
        df = df.merge(df_to_merge, left_index=True, right_index=True, how='left')
    except Exception as e:
        logging.error(f"[_calculate_msr_metrics] Error merging MSR columns: {e}", exc_info=True)
        raise e
    # logging.debug(f"[_calculate_msr_metrics] df shape after merge: {df.shape}")

    # Fill NaNs added by merge
    try:
        # logging.debug("[_calculate_msr_metrics] Filling NaNs for 'is_first_msr_q' after merge.")
        # df['is_first_msr_q'].fillna(False, inplace=True)
        df['is_first_msr_q'] = df['is_first_msr_q'].fillna(False)
        # logging.debug("[_calculate_msr_metrics] Filling NaNs for 'msr_group_total_time' after merge.")
        # df['msr_group_total_time'].fillna(np.nan, inplace=True)
        df['msr_group_total_time'] = df['msr_group_total_time'].fillna(np.nan)
        # logging.debug("[_calculate_msr_metrics] Filling NaNs for 'msr_reading_time' after merge.")
        # df['msr_reading_time'].fillna(np.nan, inplace=True)
        df['msr_reading_time'] = df['msr_reading_time'].fillna(np.nan)
    except Exception as e:
        logging.error(f"[_calculate_msr_metrics] Error filling NaNs after merge: {e}", exc_info=True)
        raise e

    # logging.debug(f"[_calculate_msr_metrics] Returning df shape: {df.shape}")
    return df 