import pandas as pd
import numpy as np
import math # For floor function
import logging # 添加日誌模塊

# --- DI-Specific Constants (from Markdown Chapter 0 & 1) ---
MAX_ALLOWED_TIME_DI = 45.0  # minutes
TOTAL_QUESTIONS_DI = 20
TIME_PRESSURE_THRESHOLD_DI = 3.0  # minutes difference
INVALID_TIME_THRESHOLD_MINUTES = 1.0  # 1.0 minute
INVALID_DATA_TAG_DI = "數據無效：用時過短（受時間壓力影響）" # Added invalid tag

# Overtime thresholds (minutes) based on time pressure
OVERTIME_THRESHOLDS = {
    True: {  # High Pressure
        'TPA': 3.0,
        'GT': 3.0,
        'DS': 2.0,
        'MSR_GROUP': 6.0,
        'MSR_READING': 1.5,
        'MSR_SINGLE_Q': 1.5
    },
    False: {  # Low Pressure
        'TPA': 3.5,
        'GT': 3.5,
        'DS': 2.5,
        'MSR_GROUP': 7.0,
        'MSR_READING': 1.5,  # Reading threshold often kept constant
        'MSR_SINGLE_Q': 1.5  # Single question threshold often kept constant
    }
}

# --- DI-Specific Helper Functions ---

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value) # Ensure it's a string

def _grade_difficulty_di(difficulty):
    """Maps DI difficulty score to a 6-level grade string based on documentation."""
    if pd.isna(difficulty):
        return "Unknown Difficulty"
    if difficulty <= -1:
        return "低難度 (Low) / 505+"
    elif difficulty <= 0:
        return "中難度 (Mid) / 555+"
    elif difficulty <= 1:
        return "中難度 (Mid) / 605+"
    elif difficulty <= 1.5:
        return "中難度 (Mid) / 655+"
    elif difficulty <= 1.95:
        return "高難度 (High) / 705+"
    else: # difficulty > 1.95
        return "高難度 (High) / 805+"

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
    if df.empty or 'msr_group_id' not in df.columns or 'question_time' not in df.columns:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column
        return df

    df_msr = df[df['question_type'] == 'Multi-source reasoning'].copy()
    if df_msr.empty:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column even if no MSR
        return df

    group_times = df_msr.groupby('msr_group_id')['question_time'].sum()
    df_msr['msr_group_total_time'] = df_msr['msr_group_id'].map(group_times)

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

    df_msr['msr_reading_time'] = df_msr.index.map(reading_times)
    df_msr['is_first_msr_q'] = df_msr.index.isin(first_q_indices)

    df = df.merge(df_msr[['msr_group_total_time', 'msr_reading_time', 'is_first_msr_q']], left_index=True, right_index=True, how='left')
    df['is_first_msr_q'].fillna(False, inplace=True)
    # Fill NaN for MSR times for robustness, although merge 'left' should handle non-MSR
    df['msr_group_total_time'].fillna(np.nan, inplace=True)
    df['msr_reading_time'].fillna(np.nan, inplace=True)
    return df


# --- Main DI Diagnosis Runner ---

def run_di_diagnosis_processed(df_di_processed, di_time_pressure_status):
    """
    Runs the diagnostic analysis for Data Insights using a preprocessed DataFrame.
    Assumes 'is_invalid' column reflects the final status after user review.

    Args:
        df_di_processed (pd.DataFrame): DataFrame with DI responses, preprocessed with 'is_invalid'.
        di_time_pressure_status (bool): Time pressure status for DI.

    Returns:
        dict: A dictionary containing the results of the DI diagnosis, structured by chapter.
        str: A string containing the summary report for the DI section.
        pd.DataFrame: The processed DI DataFrame with added diagnostic columns.
    """
    logging.info("開始DI診斷處理...")
    di_diagnosis_results = {}

    if df_di_processed.empty:
        empty_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type',
                      'question_fundamental_skill', 'content_domain', 'Subject', 'is_invalid',
                      'overtime', 'suspiciously_fast', 'msr_group_id', 'msr_group_total_time',
                      'msr_reading_time', 'is_first_msr_q', 'is_sfe',
                      'time_performance_category', 'diagnostic_params_list']
        df_to_return = pd.DataFrame(columns=empty_cols)
        if 'Subject' not in df_to_return.columns:
            df_to_return['Subject'] = 'DI'
        return {}, "Data Insights (DI) 部分無數據可供診斷。", df_to_return

    df_di = df_di_processed.copy()

    # --- Chapter 0: Derivative Data Calculation & Basic Prep ---
    df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
    if 'question_position' not in df_di.columns: df_di['question_position'] = range(len(df_di))
    else: df_di['question_position'] = pd.to_numeric(df_di['question_position'], errors='coerce')
    if 'is_correct' not in df_di.columns: df_di['is_correct'] = True
    else: df_di['is_correct'] = df_di['is_correct'].astype(bool)
    if 'question_type' not in df_di.columns: df_di['question_type'] = 'Unknown Type'
    if 'msr_group_id' not in df_di.columns: df_di['msr_group_id'] = np.nan
    if 'is_invalid' not in df_di.columns: df_di['is_invalid'] = False

    df_di = _calculate_msr_metrics(df_di)

    # --- Chapter 1: Time Strategy & Validity ---
    total_test_time_di = df_di['question_time'].sum(skipna=True) # Ensure NaNs are skipped
    time_diff = MAX_ALLOWED_TIME_DI - total_test_time_di

    num_invalid_questions_total = df_di['is_invalid'].sum()
    di_diagnosis_results['invalid_count'] = num_invalid_questions_total

    # Initialize diagnostic_params if needed
    if 'diagnostic_params' not in df_di.columns:
        df_di['diagnostic_params'] = [[] for _ in range(len(df_di))]
    else:
        # Ensure it's a mutable list
        df_di['diagnostic_params'] = df_di['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, set, tuple)) else [])

    # Add invalid tag
    final_invalid_mask_di = df_di['is_invalid']
    if final_invalid_mask_di.any():
        for idx in df_di.index[final_invalid_mask_di]:
            current_list = df_di.loc[idx, 'diagnostic_params']
            if not isinstance(current_list, list): current_list = []
            if INVALID_DATA_TAG_DI not in current_list:
                current_list.append(INVALID_DATA_TAG_DI)
            df_di.loc[idx, 'diagnostic_params'] = current_list

    # --- Mark Overtime (Vectorized Approach) ---
    df_di['overtime'] = False
    thresholds = OVERTIME_THRESHOLDS[di_time_pressure_status]
    
    # Define masks for non-invalid rows
    valid_mask = ~df_di['is_invalid']
    
    # --- Non-MSR Overtime ---
    # TPA
    tpa_mask = valid_mask & ((df_di['question_type'] == 'Two-part analysis') | (df_di['question_type'] == 'TPA'))
    tpa_over_mask = tpa_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['TPA'])
    
    # GT
    gt_mask = valid_mask & ((df_di['question_type'] == 'Graph and Table') | (df_di['question_type'] == 'GT'))
    gt_over_mask = gt_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['GT'])
    
    # DS
    ds_mask = valid_mask & ((df_di['question_type'] == 'Data Sufficiency') | (df_di['question_type'] == 'DS'))
    ds_over_mask = ds_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['DS'])

    # --- MSR Overtime ---
    msr_mask = valid_mask & ((df_di['question_type'] == 'Multi-source reasoning') | (df_di['question_type'] == 'MSR'))
    
    # 1. Group Overtime
    msr_group_over = msr_mask & df_di['msr_group_total_time'].notna() & \
                     (df_di['msr_group_total_time'] > thresholds['MSR_GROUP'])

    # 2. Reading Overtime (First Q, if Group not Overtime)
    msr_reading_over = msr_mask & (~msr_group_over) & \
                       df_di['is_first_msr_q'] & df_di['msr_reading_time'].notna() & \
                       (df_di['msr_reading_time'] > thresholds['MSR_READING'])

    # 3. Adjusted Single Q Overtime (First Q, if Group/Reading not Overtime)
    # Calculate adjusted time safely
    adj_time = df_di['question_time'] - df_di['msr_reading_time']
    msr_adj_first_over = msr_mask & (~msr_group_over) & (~msr_reading_over) & \
                         df_di['is_first_msr_q'] & \
                         df_di['msr_reading_time'].notna() & df_di['question_time'].notna() & \
                         adj_time.notna() & \
                         (adj_time > thresholds['MSR_SINGLE_Q'])

    # 4. Single Q Overtime (Non-First Q, if Group not Overtime)
    msr_non_first_over = msr_mask & (~msr_group_over) & \
                         (~df_di['is_first_msr_q']) & df_di['question_time'].notna() & \
                         (df_di['question_time'] > thresholds['MSR_SINGLE_Q'])

    # Combine all MSR overtime conditions
    msr_over_mask = msr_group_over | msr_reading_over | msr_adj_first_over | msr_non_first_over
    
    # --- Combine all Overtime conditions ---
    # Ensure only valid rows are considered by applying valid_mask implicitly through component masks
    overall_overtime_mask = tpa_over_mask | gt_over_mask | ds_over_mask | msr_over_mask
    
    # Apply the final mask to set the 'overtime' column
    df_di.loc[overall_overtime_mask, 'overtime'] = True
    
    # --- End Vectorized Overtime ---

    # Store Chapter 1 results
    di_diagnosis_results['chapter_1'] = {
        'total_test_time_minutes': total_test_time_di,
        'time_difference_minutes': time_diff,
        'time_pressure': di_time_pressure_status, # Store the status used
        'invalid_questions_excluded': num_invalid_questions_total,
        'overtime_thresholds_minutes': thresholds
    }

    # Create filtered dataset for subsequent chapters
    df_di_filtered = df_di[~df_di['is_invalid']].copy() # Use ~is_invalid

    # --- Chapter 2: Multidimensional Performance Analysis ---
    domain_analysis = {}
    type_analysis = {}
    difficulty_analysis = {}
    domain_comparison_tags = {
        'poor_math_related': False, 'slow_math_related': False,
        'poor_non_math_related': False, 'slow_non_math_related': False,
        'significant_diff_error': False, 'significant_diff_overtime': False
    }

    if not df_di_filtered.empty:
        if 'content_domain' in df_di_filtered.columns:
            domain_analysis = _analyze_dimension(df_di_filtered, 'content_domain')
            math_metrics = domain_analysis.get('Math Related', {})
            non_math_metrics = domain_analysis.get('Non-Math Related', {})
            math_errors = math_metrics.get('errors', 0)
            non_math_errors = non_math_metrics.get('errors', 0)
            math_overtime = math_metrics.get('overtime', 0)
            non_math_overtime = non_math_metrics.get('overtime', 0)

            if abs(math_errors - non_math_errors) >= 2:
                domain_comparison_tags['significant_diff_error'] = True
                domain_comparison_tags['poor_math_related'] = math_errors > non_math_errors
                domain_comparison_tags['poor_non_math_related'] = non_math_errors > math_errors

            if abs(math_overtime - non_math_overtime) >= 2:
                 domain_comparison_tags['significant_diff_overtime'] = True
                 domain_comparison_tags['slow_math_related'] = math_overtime > non_math_overtime
                 domain_comparison_tags['slow_non_math_related'] = non_math_overtime > math_overtime

        if 'question_type' in df_di_filtered.columns:
            type_analysis = _analyze_dimension(df_di_filtered, 'question_type')

        if 'question_difficulty' in df_di_filtered.columns:
            df_di_filtered['difficulty_grade'] = df_di_filtered['question_difficulty'].apply(_grade_difficulty_di)
            difficulty_analysis = _analyze_dimension(df_di_filtered, 'difficulty_grade')

    di_diagnosis_results['chapter_2'] = {
        'by_domain': domain_analysis,
        'by_type': type_analysis,
        'by_difficulty': difficulty_analysis,
        'domain_comparison_tags': domain_comparison_tags
    }

    # --- Chapter 3: Root Cause Diagnosis ---
    if not df_di_filtered.empty and 'question_type' in df_di_filtered.columns:
        avg_time_per_type = df_di_filtered.groupby('question_type')['question_time'].mean().to_dict()
        max_correct_difficulty_per_combination = pd.DataFrame() # Init empty
        if 'content_domain' in df_di_filtered.columns and 'question_difficulty' in df_di_filtered.columns:
             correct_rows = df_di_filtered['is_correct'] == True
             if correct_rows.any(): # Ensure there are correct rows before grouping
                 max_correct_difficulty_per_combination = df_di_filtered[correct_rows].groupby(
                     ['question_type', 'content_domain']
                 )['question_difficulty'].max().unstack(fill_value=-np.inf)

        # 確保time_performance_category列存在初始值
        if 'time_performance_category' not in df_di_filtered.columns:
            df_di_filtered['time_performance_category'] = 'Unknown'

        df_di_filtered = _diagnose_root_causes(df_di_filtered, avg_time_per_type, max_correct_difficulty_per_combination, thresholds)

        di_diagnosis_results['chapter_3'] = {
            'diagnosed_dataframe': df_di_filtered.copy(), # Store a copy
            'avg_time_per_type_minutes': avg_time_per_type,
            'max_correct_difficulty': max_correct_difficulty_per_combination.to_dict() if not max_correct_difficulty_per_combination.empty else {}
        }
    else:
        di_diagnosis_results['chapter_3'] = {
             'diagnosed_dataframe': pd.DataFrame(),
             'avg_time_per_type_minutes': {},
             'max_correct_difficulty': {}
         }

    # --- Chapter 4: Special Pattern Observation ---
    avg_times_ch3 = di_diagnosis_results.get('chapter_3', {}).get('avg_time_per_type_minutes', {})
    # Pass the potentially modified df from Ch3
    df_ch3_diagnosed = di_diagnosis_results['chapter_3']['diagnosed_dataframe']
    # Operate on a copy if _observe_di_patterns modifies in place, or ensure it returns modified df
    df_for_ch4 = df_ch3_diagnosed.copy()
    pattern_analysis_results = _observe_di_patterns(df_for_ch4, avg_times_ch3) # Assume modifies df_for_ch4
    di_diagnosis_results['chapter_4'] = pattern_analysis_results

    # --- Chapter 5: Foundation Ability Override Rule ---
    type_analysis_ch2 = di_diagnosis_results.get('chapter_2', {}).get('by_type', {})
    # Use the potentially modified df from Ch4
    override_analysis = _check_foundation_override(df_for_ch4, type_analysis_ch2)
    di_diagnosis_results['chapter_5'] = override_analysis

    # --- 記錄 Ch4/Ch5 後 df_for_ch4 (即將成為 diagnosed_df_ch4_ch5) 的狀態 ---
    if 'time_performance_category' in df_for_ch4.columns:
        ch4_unique_vals = df_for_ch4['time_performance_category'].unique()
        ch4_value_counts = df_for_ch4['time_performance_category'].value_counts().to_dict()
        logging.info(f"DI DEBUG: After Ch4/5 - df_for_ch4 time_perf unique: {ch4_unique_vals}")
        logging.info(f"DI DEBUG: After Ch4/5 - df_for_ch4 time_perf counts: {ch4_value_counts}")
    else:
        logging.warning("DI DEBUG: After Ch4/5 - df_for_ch4 MISSING time_performance_category!")
    # --- 結束記錄 ---

    # --- Chapter 6: Practice Planning & Recommendations ---
    # Use the potentially modified df from Ch4/Ch5
    diagnosed_df_ch4_ch5 = df_for_ch4
    domain_tags_ch2 = di_diagnosis_results.get('chapter_2', {}).get('domain_comparison_tags', {})
    override_analysis_ch5 = di_diagnosis_results.get('chapter_5', {})

    recommendations = []
    if not diagnosed_df_ch4_ch5.empty:
        recommendations = _generate_di_recommendations(diagnosed_df_ch4_ch5, override_analysis_ch5, domain_tags_ch2)
    di_diagnosis_results['chapter_6'] = {'recommendations_list': recommendations}

    # --- Chapter 7: Summary Report Generation ---
    # Ensure the latest df (after Ch4 modifications) is used for the report
    di_diagnosis_results['chapter_3']['diagnosed_dataframe'] = diagnosed_df_ch4_ch5.copy()
    report_str = _generate_di_summary_report(di_diagnosis_results)

    # --- Final DataFrame Preparation ---
    # Start with the original DataFrame containing all rows (including invalid)
    df_base = df_di.copy()
    # Select only the diagnostic columns we calculated on the filtered data
    diagnostic_cols_to_merge = [] 
    if diagnosed_df_ch4_ch5 is not None and not diagnosed_df_ch4_ch5.empty:
        potential_cols = ['diagnostic_params', 'is_sfe', 'time_performance_category']
        diagnostic_cols_to_merge = [col for col in potential_cols if col in diagnosed_df_ch4_ch5.columns]

    if diagnostic_cols_to_merge:
        # Merge diagnostic columns from the filtered/diagnosed df back to the base df
        # Merge on index, keep all rows from the base df ('left' merge)
        logging.info(f"DI DEBUG: Before merge - df_base columns: {df_base.columns.tolist()}")
        logging.info(f"DI DEBUG: Before merge - diagnosed_df_ch4_ch5 columns: {diagnosed_df_ch4_ch5.columns.tolist()}")
        logging.info(f"DI DEBUG: Before merge - Columns to merge: {diagnostic_cols_to_merge}")
        df_merged = pd.merge(
            df_base,
            diagnosed_df_ch4_ch5[diagnostic_cols_to_merge], # Only select the columns to merge
            left_index=True,
            right_index=True,
            how='left', # Keep all rows from df_base
            suffixes=('', '_diag') # Add suffix in case of potential name conflicts
        )
        # Check if merge created duplicate columns (e.g., time_performance_category_diag)
        # Prioritize the _diag version if it exists
        for col in diagnostic_cols_to_merge:
            diag_col = col + '_diag'
            if diag_col in df_merged.columns:
                # Use the merged value (_diag), potentially overwriting original or filling NaNs
                df_merged[col] = df_merged[diag_col]
                df_merged.drop(columns=[diag_col], inplace=True)
                logging.info(f"Prioritized merged column '{col}' from '{diag_col}'.")

        df_to_return = df_merged # Use the merged result
        logging.info(f"Merged diagnostic columns: {diagnostic_cols_to_merge}")
        if 'time_performance_category' in df_to_return.columns:
             logging.info(f"DI DEBUG: After merge - df_to_return time_perf unique: {df_to_return['time_performance_category'].unique()}")
             logging.info(f"DI DEBUG: After merge - df_to_return time_perf counts: {df_to_return['time_performance_category'].value_counts(dropna=False).to_dict()}") # include NaN counts
        else:
             logging.warning("DI DEBUG: After merge - df_to_return MISSING time_performance_category!")

    else:
        # If no diagnostic columns were calculated (e.g., filtered df was empty)
        df_to_return = df_base
        logging.warning("No diagnostic columns found to merge back.")

    # Translate params (now operating on the potentially merged df_to_return)
    if 'diagnostic_params' in df_to_return.columns:
        # Ensure list type after potential merge (NaNs might appear for rows not in diagnosed_df)
        df_to_return['diagnostic_params'] = df_to_return['diagnostic_params'].apply(
            lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x] if isinstance(x, str) else [])
        )
        df_to_return['diagnostic_params_list_chinese'] = df_to_return['diagnostic_params'].apply(
            lambda params_list: _translate_di(params_list)
        )
        # Safely drop and rename
        if 'diagnostic_params' in df_to_return.columns: df_to_return.drop(columns=['diagnostic_params'], inplace=True)
        if 'diagnostic_params_list_chinese' in df_to_return.columns: df_to_return.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'}, inplace=True)
    else:
        # Initialize if missing entirely
        df_to_return['diagnostic_params_list'] = [[] for _ in range(len(df_to_return))]

    # --- Refined fillna logic --- 
    # 1. Ensure the time_performance_category column exists, default to 'Unknown'
    if 'time_performance_category' not in df_to_return.columns:
        df_to_return['time_performance_category'] = 'Unknown'
        logging.info("Initialized 'time_performance_category' column as 'Unknown'.")
    
    # 2. Fill NaNs potentially introduced by the merge (for rows NOT diagnosed) with 'Unknown'
    # Also ensure empty strings are treated as 'Unknown'
    df_to_return['time_performance_category'] = df_to_return['time_performance_category'].fillna('Unknown').replace('', 'Unknown')
    logging.info(f"After fillna/replace('Unknown'): unique values: {df_to_return['time_performance_category'].unique()}")

    # 3. Specifically set 'Invalid/Excluded' for rows marked as invalid
    if 'is_invalid' in df_to_return.columns:
        invalid_mask = df_to_return['is_invalid'] == True
        if invalid_mask.any():
            df_to_return.loc[invalid_mask, 'time_performance_category'] = 'Invalid/Excluded'
            logging.info(f"Set 'Invalid/Excluded' for {invalid_mask.sum()} rows. Final unique values: {df_to_return['time_performance_category'].unique()}")

    # Handle potential NaNs in 'is_sfe' after merge
    if 'is_sfe' in df_to_return.columns:
        df_to_return['is_sfe'].fillna(False, inplace=True)
        df_to_return['is_sfe'] = df_to_return['is_sfe'].astype(bool)
    else:
        df_to_return['is_sfe'] = False # Initialize if missing
    
    # Ensure Subject column exists
    if 'Subject' not in df_to_return.columns:
        df_to_return['Subject'] = 'DI'
    else:
         df_to_return['Subject'] = 'DI' # Force correct value

    # Final check for overtime column existence (should be fine as we start with df_di)
    if 'overtime' not in df_to_return.columns:
         df_to_return['overtime'] = False # Should not happen now

    # Fill NaNs in diagnostic columns for invalid rows if introduced by update/merge
    cols_to_fill_na = ['is_sfe', 'time_performance_category'] # Add others if needed
    fill_values = {'is_sfe': False, 'time_performance_category': 'Invalid/Excluded'}
    for col in cols_to_fill_na:
        if col in df_to_return.columns:
            df_to_return[col].fillna(fill_values.get(col, 'Unknown'), inplace=True)

    # Ensure is_invalid column is boolean
    if 'is_invalid' in df_to_return.columns:
        df_to_return['is_invalid'] = df_to_return['is_invalid'].astype(bool)
    else:
        df_to_return['is_invalid'] = False # Should exist from input

    # --- Remove DEBUG START ---
    # print(f"DEBUG (DI): Before return - Invalid rows in df_to_return: {df_to_return['is_invalid'].sum()}")
    # if 'is_invalid' in df_to_return.columns and df_to_return['is_invalid'].sum() > 0:
    #     print(f"DEBUG (DI): Before return - Invalid rows index: {df_to_return[df_to_return['is_invalid']].index.tolist()}")
    # --- Remove DEBUG END ---

    # 在return前最後記錄狀態
    if 'time_performance_category' in df_to_return.columns:
        unique_values = df_to_return['time_performance_category'].unique()
        value_counts = df_to_return['time_performance_category'].value_counts().to_dict()
        logging.info(f"最終time_performance_category唯一值: {unique_values}")
        logging.info(f"最終time_performance_category計數: {value_counts}")
    else:
        logging.warning("最終df_to_return中缺少time_performance_category列!")
    
    logging.info("DI診斷處理完成。")
    return di_diagnosis_results, report_str, df_to_return


# --- Root Cause Diagnosis Helper (Chapter 3 Logic) --- REWRITTEN ---

def _diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """
    Analyzes root causes row-by-row based on Chapter 3 logic from the MD document.
    Adds 'diagnostic_params' and 'is_sfe' columns.
    Relies on 'question_type', 'content_domain', 'question_difficulty', 'question_time',
    'is_correct', 'overtime', 'msr_reading_time', 'is_first_msr_q'.
    """
    # NOTE: This function still uses iterrows() and could be further optimized,
    # but that involves more complex refactoring than requested. Keeping as is.
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = 'Unknown' # Added init
        return df

    all_diagnostic_params = []
    all_is_sfe = []
    all_time_performance_categories = []

    max_diff_dict = {}
    if isinstance(max_diffs, pd.DataFrame) and not max_diffs.empty:
        for q_type_col in max_diffs.columns:
            q_type = q_type_col
            for domain in max_diffs.index:
                 max_val = max_diffs.loc[domain, q_type]
                 if pd.notna(max_val) and max_val != -np.inf:
                     max_diff_dict[(q_type, domain)] = max_val

    msr_reading_threshold = ch1_thresholds.get('MSR_READING', 1.5)
    msr_single_q_threshold = ch1_thresholds.get('MSR_SINGLE_Q', 1.5)

    for index, row in df.iterrows():
        params = []
        sfe_triggered = False

        q_type = row.get('question_type', 'Unknown')
        q_domain = row.get('content_domain', 'Unknown')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime = bool(row.get('overtime', False))
        msr_reading_time = row.get('msr_reading_time', None)
        is_first_msr_q = bool(row.get('is_first_msr_q', False))

        is_relatively_fast = False
        is_slow = is_overtime
        is_normal_time = False
        avg_time_for_type = avg_times.get(q_type, np.inf)

        if pd.notna(q_time) and avg_time_for_type != np.inf:
            if q_time < (avg_time_for_type * 0.75):
                is_relatively_fast = True
            if not is_relatively_fast and not is_slow:
                is_normal_time = True

        if not is_correct and pd.notna(q_diff):
            max_correct_diff_key = (q_type, q_domain)
            max_correct_diff = max_diff_dict.get(max_correct_diff_key, -np.inf)
            if q_diff < max_correct_diff:
                sfe_triggered = True
                params.append('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        current_time_performance_category = 'Unknown'
        if is_correct:
            if is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif is_slow: current_time_performance_category = 'Slow & Correct'
            else: current_time_performance_category = 'Normal Time & Correct'
        else:
            if is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif is_slow: current_time_performance_category = 'Slow & Wrong'
            else: current_time_performance_category = 'Normal Time & Wrong'

        # --- Detailed Diagnostic Logic ---
        # A. Data Sufficiency
        if q_type == 'Data Sufficiency':
            if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # B. Two-Part Analysis
        elif q_type == 'Two-part analysis':
             if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # C. Graph & Table
        elif q_type == 'Graph and Table':
             if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_DATA_EXTRACTION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # D. Multi-Source Reasoning
        elif q_type == 'Multi-source reasoning':
            if is_first_msr_q and pd.notna(msr_reading_time) and msr_reading_time > msr_reading_threshold: params.append('DI_MSR_READING_COMPREHENSION_BARRIER')
            if not is_first_msr_q and pd.notna(q_time) and q_time > msr_single_q_threshold: params.append('DI_MSR_SINGLE_Q_BOTTLENECK')
            if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                 if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # --- End Detailed Logic ---

        # Add the results to our lists
        all_diagnostic_params.append(params)
        all_is_sfe.append(sfe_triggered)
        all_time_performance_categories.append(current_time_performance_category)

    # Update the dataframe with all the collected information
    df['diagnostic_params'] = all_diagnostic_params
    df['is_sfe'] = all_is_sfe
    df['time_performance_category'] = all_time_performance_categories

    return df


# --- Special Pattern Observation Helper (Chapter 4 Logic) --- MODIFIED ---

def _observe_di_patterns(df, avg_times):
    """
    Observes special patterns like carelessness or early rushing (Chapter 4).
    Combines averages with diagnostic output from Chapter 3.
    Uses 'question_type', 'question_time', 'is_correct', 'question_position'.
    """
    analysis = {
        'triggered_behavioral_params': [],
        'carelessness_issue_triggered': False,
        'fast_wrong_rate': 0.0,
        'early_rushing_risk_triggered': False,
        'early_rushing_questions': []
    }
    if df.empty: return analysis

    if 'diagnostic_params' not in df.columns:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
    else:
        df['diagnostic_params'] = df['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else [])

    # 檢查並確保time_performance_category存在
    if 'time_performance_category' not in df.columns:
        df['time_performance_category'] = 'Unknown'
    else:
        # 確保沒有空值或空字串
        df['time_performance_category'] = df['time_performance_category'].fillna('Unknown')
        df.loc[df['time_performance_category'] == '', 'time_performance_category'] = 'Unknown'

    # 1. Carelessness Issue - 現在我們可以使用time_performance_category列
    fast_wrong_count = 0
    fast_total_count = 0
    if 'time_performance_category' in df.columns:
        fast_wrong_count = df[df['time_performance_category'] == 'Fast & Wrong'].shape[0]
        fast_total_count = df[(df['time_performance_category'].str.startswith('Fast'))].shape[0]
    
    # 如果沒有time_performance_category或計數為0，使用原始邏輯計算fast_wrong_rate
    if fast_total_count == 0:
        # 原始邏輯使用is_relatively_fast的計算
        is_relatively_fast_mask = pd.Series(False, index=df.index)
        for q_type, group in df.groupby('question_type'):
            avg_time = avg_times.get(q_type, np.inf)
            if avg_time != np.inf:
                is_relatively_fast_mask.loc[group.index] = group['question_time'].notna() & (group['question_time'] < avg_time * 0.75)

        fast_total_count = is_relatively_fast_mask.sum()
        if fast_total_count > 0:
            fast_wrong_mask = is_relatively_fast_mask & (df['is_correct'] == False)
            fast_wrong_count = fast_wrong_mask.sum()

    # 計算快錯率並設置觸發條件
    if fast_total_count > 0:
        fast_wrong_rate = fast_wrong_count / fast_total_count
        analysis['fast_wrong_rate'] = fast_wrong_rate
        if fast_wrong_rate > 0.3:
            analysis['carelessness_issue_triggered'] = True
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_CARELESSNESS_ISSUE')

    # 2. Early Rushing Risk
    # Ensure necessary columns exist before masking
    if 'question_position' in df.columns and 'question_time' in df.columns:
        early_pos_limit = TOTAL_QUESTIONS_DI / 3
        early_rush_mask = (
            (df['question_position'] <= early_pos_limit) &
            (df['question_time'].notna()) &
            (df['question_time'] < INVALID_TIME_THRESHOLD_MINUTES)
        )
        early_rushing_indices = df.index[early_rush_mask].tolist()

        if early_rushing_indices:
            analysis['early_rushing_risk_triggered'] = True
            early_rush_param = 'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK'
            for index in early_rushing_indices:
                # Safely access and modify the list
                current_params = df.loc[index, 'diagnostic_params']
                if not isinstance(current_params, list): current_params = []
                if early_rush_param not in current_params:
                     current_params.append(early_rush_param)
                     df.loc[index, 'diagnostic_params'] = current_params # Assign back

                # Collect details safely using .get()
                row = df.loc[index]
                analysis['early_rushing_questions'].append({
                    'id': row.get('Question ID', index),
                    'type': row.get('question_type', 'Unknown'),
                    'domain': row.get('content_domain', 'Unknown'),
                    'time': row.get('question_time', np.nan)
                })
    else:
        # Handle missing columns needed for early rush check if necessary
        pass

    return analysis


# --- Foundation Ability Override Helper (Chapter 5 Logic) ---

def _check_foundation_override(df, type_metrics):
    """Checks for foundation override rule for each question type."""
    override_results = {}
    if df.empty or 'question_type' not in df.columns: return override_results

    question_types_in_data = df['question_type'].unique()

    for q_type in question_types_in_data:
        if pd.isna(q_type): continue

        metrics = type_metrics.get(q_type, {})
        error_rate = metrics.get('error_rate', 0.0)
        overtime_rate = metrics.get('overtime_rate', 0.0)
        triggered = False
        y_agg = None
        z_agg = None

        if error_rate > 0.5 or overtime_rate > 0.5:
            triggered = True
            # Check required columns exist before filtering
            req_cols = ['question_type', 'is_correct', 'overtime', 'question_difficulty', 'question_time']
            if all(c in df.columns for c in req_cols):
                triggering_mask = (
                    (df['question_type'] == q_type) &
                    ((df['is_correct'] == False) | (df['overtime'] == True))
                )
                triggering_df = df[triggering_mask]

                if not triggering_df.empty:
                    if triggering_df['question_difficulty'].notna().any():
                         min_difficulty = triggering_df['question_difficulty'].min()
                         y_agg = _grade_difficulty_di(min_difficulty)
                    else: y_agg = "Unknown Difficulty"

                    if triggering_df['question_time'].notna().any():
                         max_time_minutes = triggering_df['question_time'].max()
                         # Ensure max_time_minutes is not NaN before floor operation
                         if pd.notna(max_time_minutes):
                             z_agg = math.floor(max_time_minutes * 2) / 2.0
                         else: z_agg = None
                    else: z_agg = None
                else:
                     y_agg = "Unknown Difficulty"
                     z_agg = None
            else: # Handle missing columns case
                y_agg = "Unknown Difficulty"
                z_agg = None


        override_results[q_type] = {
            'override_triggered': triggered,
            'Y_agg': y_agg,
            'Z_agg': z_agg,
            'triggering_error_rate': error_rate,
            'triggering_overtime_rate': overtime_rate
        }
    return override_results


# --- Recommendation Generation Helper (Chapter 6 Logic) ---

def _generate_di_recommendations(df_diagnosed, override_results, domain_tags):
    """Generates practice recommendations based on Chapters 3, 5, and 2 results."""
    if 'question_type' not in df_diagnosed.columns: return []

    question_types_in_data = df_diagnosed['question_type'].unique()
    question_types_valid = [qt for qt in question_types_in_data if pd.notna(qt)]
    recommendations_by_type = {q_type: [] for q_type in question_types_valid}
    processed_override_types = set()

    # Exemption Rule
    exempted_types = set()
    if 'is_correct' in df_diagnosed.columns and 'overtime' in df_diagnosed.columns:
        for q_type in question_types_valid:
            type_df = df_diagnosed[df_diagnosed['question_type'] == q_type]
            if not type_df.empty and not ((type_df['is_correct'] == False) | (type_df['overtime'] == True)).any():
                exempted_types.add(q_type)

    # Macro Recommendations
    math_related_zh = _translate_di('Math Related') # Translate once
    non_math_related_zh = _translate_di('Non-Math Related') # Translate once
    for q_type, override_info in override_results.items():
        if q_type in recommendations_by_type and override_info.get('override_triggered'):
            if q_type in exempted_types: continue
            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if pd.notna(z_agg) else "未知限時"
            error_rate_str = _format_rate(override_info.get('triggering_error_rate', 0.0))
            overtime_rate_str = _format_rate(override_info.get('triggering_overtime_rate', 0.0))
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {error_rate_str} 或 超時率 {overtime_rate_str}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({'type': 'macro', 'text': rec_text, 'question_type': q_type})
            processed_override_types.add(q_type)

    # Case Recommendations
    target_times_minutes = {'Data Sufficiency': 2.0, 'Two-part analysis': 3.0, 'Graph and Table': 3.0, 'Multi-source reasoning': 2.0}
    required_cols = ['is_correct', 'overtime', 'question_type', 'content_domain', 'question_difficulty', 'question_time', 'is_sfe', 'diagnostic_params']
    if all(col in df_diagnosed.columns for col in required_cols):
        df_trigger = df_diagnosed[((df_diagnosed['is_correct'] == False) | (df_diagnosed['overtime'] == True))]
        if not df_trigger.empty:
            try:
                grouped_triggers = df_trigger.groupby(['question_type', 'content_domain'], observed=False, dropna=False) # Handle potential NaNs in grouping keys
                for name, group_df in grouped_triggers:
                    q_type, domain = name
                    if pd.isna(q_type) or pd.isna(domain): continue
                    if q_type in processed_override_types or q_type in exempted_types: continue

                    min_difficulty_score = group_df['question_difficulty'].min()
                    y_grade = _grade_difficulty_di(min_difficulty_score)

                    z_minutes_list = []
                    target_time_minutes = target_times_minutes.get(q_type, 2.0)
                    for _, row in group_df.iterrows():
                        q_time_minutes = row['question_time']
                        is_overtime = row['overtime']
                        if pd.notna(q_time_minutes):
                            base_time_minutes = max(0, q_time_minutes - 0.5 if is_overtime else q_time_minutes)
                            z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                            z = max(z_raw_minutes, target_time_minutes)
                            z_minutes_list.append(z)

                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{target_time_minutes:.1f} 分鐘"
                    group_sfe = group_df['is_sfe'].any()
                    diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)]) # More concise set union
                    translated_params_list = _translate_di(list(diag_params_codes)) # Translate here if needed for text, else done later

                    problem_desc = "錯誤或超時"
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    translated_domain = _translate_di(domain) # Translate domain

                    rec_text = f"{sfe_prefix}針對 **{translated_domain}** 領域的 **{q_type}** 題目 ({problem_desc})，"
                    rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"
                    if max_z_minutes - target_time_minutes > 2.0:
                        rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    if q_type in recommendations_by_type:
                         recommendations_by_type[q_type].append({'type': 'case_aggregated', 'is_sfe': group_sfe, 'domain': domain, 'difficulty_grade': y_grade, 'time_limit_z': max_z_minutes, 'text': rec_text, 'question_type': q_type})
            except Exception:
                 # Error handling or logging can be added here
                 pass

    # Final Assembly
    final_recommendations = []
    for q_type in sorted(list(exempted_types)):
         if q_type in question_types_valid:
              final_recommendations.append({'type': 'exemption_note', 'text': f"您在 **{q_type}** 題型上表現穩定，所有題目均在時限內正確完成，無需針對性個案練習。", 'question_type': q_type})

    for q_type in question_types_valid:
        if q_type in exempted_types: continue
        type_recs = recommendations_by_type.get(q_type, [])
        if not type_recs: continue
        type_recs.sort(key=lambda rec: 0 if rec['type'] == 'macro' else 1)

        focus_note = ""
        has_math_case_agg = any(r.get('domain') == 'Math Related' for r in type_recs if r['type'] == 'case_aggregated')
        has_non_math_case_agg = any(r.get('domain') == 'Non-Math Related' for r in type_recs if r['type'] == 'case_aggregated')

        # Use pre-translated domain names
        if (domain_tags.get('poor_math_related') or domain_tags.get('slow_math_related')) and has_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{math_related_zh}` 題目的練習比例。**"
        if (domain_tags.get('poor_non_math_related') or domain_tags.get('slow_non_math_related')) and has_non_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{non_math_related_zh}` 題目的練習比例。**"

        if focus_note and type_recs:
            # Find last non-macro index safely
            last_agg_rec_index = -1
            for i in range(len(type_recs) - 1, -1, -1):
                 if type_recs[i]['type'] != 'macro': # Attach to last non-macro/exemption
                     last_agg_rec_index = i
                     break
            if last_agg_rec_index != -1:
                 type_recs[last_agg_rec_index]['text'] += focus_note
            else: # Attach to the only rec (must be macro if list not empty)
                 type_recs[-1]['text'] += focus_note


        final_recommendations.extend(type_recs)

    type_order_final = ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table']
    final_recommendations.sort(key=lambda x: type_order_final.index(x['question_type']) if x.get('question_type') in type_order_final else 99)

    return final_recommendations

# --- DI Appendix A Translation ---
APPENDIX_A_TRANSLATION_DI = {
    # DI - Reading & Understanding
    'DI_READING_COMPREHENSION_ERROR': "DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math)",
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': "DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙",
    # DI - Concept & Application (Math)
    'DI_CONCEPT_APPLICATION_ERROR': "DI 概念應用 (Math): 數學觀念/公式應用錯誤/障礙",
    # DI - Logical Reasoning (Non-Math)
    'DI_LOGICAL_REASONING_ERROR': "DI 邏輯推理 (Non-Math): 題目內在邏輯推理/判斷錯誤",
    # DI - Data Handling & Calculation
    'DI_DATA_EXTRACTION_ERROR': "DI 數據提取 (GT): 從圖表中提取數據錯誤",
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': "DI 信息提取/推斷 (GT/MSR Non-Math): 信息定位/推斷錯誤",
    'DI_CALCULATION_ERROR': "DI 計算: 數學計算錯誤/障礙",
    # DI - MSR Specific
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': "DI 多源整合 (MSR): 跨分頁/來源信息整合錯誤/障礙",
    'DI_MSR_READING_COMPREHENSION_BARRIER': "DI MSR 閱讀障礙: 題組整體閱讀時間過長",
    'DI_MSR_SINGLE_Q_BOTTLENECK': "DI MSR 單題瓶頸: 題組內單題回答時間過長",
    # DI - Question Type Specific
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': "DI 特定題型障礙 (例如 MSR Non-Math 子題型)",
    # DI - Foundational & Efficiency
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "DI 基礎掌握: 應用不穩定 (Special Focus Error)",
    'DI_EFFICIENCY_BOTTLENECK_READING': "DI 效率瓶頸: 閱讀理解耗時 (Math/Non-Math)",
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': "DI 效率瓶頸: 概念/公式應用耗時 (Math)",
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': "DI 效率瓶頸: 計算耗時",
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': "DI 效率瓶頸: 邏輯推理耗時 (Non-Math)",
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': "DI 效率瓶頸: 圖表解讀耗時",
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': "DI 效率瓶頸: 多源信息整合耗時 (MSR)",
    # DI - Behavior
    'DI_CARELESSNESS_DETAIL_OMISSION': "DI 行為: 粗心 - 細節忽略/看錯 (快錯時隱含)",
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': "DI 行為: 粗心 - 整體快錯率偏高",
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "DI 行為: 測驗前期作答過快風險",
    # Domains
    'Math Related': "數學相關",
    'Non-Math Related': "非數學相關",
    'Unknown Domain': "未知領域",
    # Time Pressure
    'High': "高", 'Low': "低", 'Unknown': "未知",
    # Question Types
    'Data Sufficiency': 'Data Sufficiency', 'Two-part analysis': 'Two-part analysis',
    'Multi-source reasoning': 'Multi-source reasoning', 'Graph and Table': 'Graph and Table',
    'Unknown Type': '未知類型',
    # Time Performance Categories
    'Fast & Wrong': "快錯", 'Slow & Wrong': "慢錯", 'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對", 'Fast & Correct': "快對", 'Normal Time & Correct': "正常時間 & 對",
    'Unknown': "未知", 'Invalid/Excluded': "已排除/無效",
    # Parameter Categories
    'SFE': '基礎掌握', 'Reading/Interpretation': '閱讀/解讀', 'Concept/Application': '概念/應用',
    'Data/Calculation': '數據/計算', 'Logic/Reasoning': '邏輯/推理', 'Multi-Source': '多源整合',
    'Efficiency': '效率問題', 'Carelessness': '粗心問題', 'Behavioral': '行為模式', 'Unknown': '未分類',
}

# --- Parameter Categories for Report Grouping (DI) --- Updated ---
DI_PARAM_CATEGORY_ORDER = [
    'SFE', 'Reading/Interpretation', 'Concept/Application', 'Data/Calculation',
    'Logic/Reasoning', 'Multi-Source', 'Efficiency', 'Carelessness', 'Behavioral', 'Unknown'
]

DI_PARAM_TO_CATEGORY = {
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    'DI_READING_COMPREHENSION_ERROR': 'Reading/Interpretation',
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': 'Reading/Interpretation',
    'DI_CONCEPT_APPLICATION_ERROR': 'Concept/Application',
    'DI_DATA_EXTRACTION_ERROR': 'Data/Calculation',
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': 'Data/Calculation',
    'DI_CALCULATION_ERROR': 'Data/Calculation',
    'DI_LOGICAL_REASONING_ERROR': 'Logic/Reasoning',
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': 'Logic/Reasoning', # Or specific category?
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': 'Multi-Source',
    'DI_MSR_READING_COMPREHENSION_BARRIER': 'Multi-Source', # Or Efficiency? Let's keep Multi-Source
    'DI_MSR_SINGLE_Q_BOTTLENECK': 'Multi-Source', # Or Efficiency? Let's keep Multi-Source
    'DI_EFFICIENCY_BOTTLENECK_READING': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': 'Efficiency',
    'DI_CARELESSNESS_DETAIL_OMISSION': 'Carelessness',
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral'
}

def _translate_di(param):
    """Translates an internal DI param/skill name using APPENDIX_A_TRANSLATION_DI."""
    if isinstance(param, list):
        return [APPENDIX_A_TRANSLATION_DI.get(p, str(p)) for p in param if isinstance(p, str)]
    elif isinstance(param, str):
         return APPENDIX_A_TRANSLATION_DI.get(param, param)
    else:
         return str(param)


# --- DI Summary Report Generation Helper (Chapter 7 Logic) ---

def _generate_di_summary_report(di_results):
    """Generates the summary report string for the Data Insights section."""
    report_lines = ["---（基於用戶數據與模擬難度分析）---", ""]
    ch1 = di_results.get('chapter_1', {})
    ch2 = di_results.get('chapter_2', {})
    ch3 = di_results.get('chapter_3', {})
    ch4 = di_results.get('chapter_4', {})
    # ch5 = di_results.get('chapter_5', {}) # Ch5 results not directly used in report text
    ch6 = di_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe')

    # Pre-translate common terms
    math_related_zh = _translate_di('Math Related')
    non_math_related_zh = _translate_di('Non-Math Related')

    # Prepare data for reflection mapping and param counts
    all_triggered_params = set()
    param_to_positions = {}
    domain_to_positions = {}
    param_counts_all = pd.Series(dtype=int)

    if diagnosed_df is not None and not diagnosed_df.empty:
        param_col_eng = 'diagnostic_params' if 'diagnostic_params' in diagnosed_df.columns else None
        map_cols = ['content_domain', 'question_position']
        if param_col_eng and all(col in diagnosed_df.columns for col in map_cols):
            all_param_lists_for_count = []
            for index, row in diagnosed_df.iterrows(): # Iteration needed for detailed mapping
                 pos = row.get('question_position')
                 domain = row.get('content_domain', 'Unknown Domain')
                 params = row.get(param_col_eng, [])
                 if not isinstance(params, list): params = []
                 params = [p for p in params if isinstance(p, str)] # Ensure strings

                 all_triggered_params.update(params)
                 all_param_lists_for_count.extend(params) # For counting

                 if pos is not None and pos != 'N/A':
                     if domain != 'Unknown Domain':
                          domain_to_positions.setdefault(domain, set()).add(pos)
                     for p in params:
                         param_to_positions.setdefault(p, set()).add(pos)
            if all_param_lists_for_count:
                 param_counts_all = pd.Series(all_param_lists_for_count).value_counts()

        ch4_behavioral_params = [p for p in ch4.get('triggered_behavioral_params', []) if isinstance(p, str)]
        all_triggered_params.update(ch4_behavioral_params)
        # Add Ch4 params to counts if not already counted (assuming they aren't in df)
        # This might slightly inflate counts if they *are* also in df - depends on Ch4 logic
        param_counts_all = param_counts_all.add(pd.Series(ch4_behavioral_params).value_counts(), fill_value=0)


    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for domain in domain_to_positions: domain_to_positions[domain] = sorted(list(domain_to_positions[domain]))
    sfe_triggered = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in all_triggered_params
    sfe_code = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'

    # 1. 開篇總結
    report_lines.append("**1. 開篇總結（時間策略與有效性）**")
    tp_status = _translate_di(ch1.get('time_pressure', 'Unknown')) # Use translated status directly
    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體作答時間：{total_time:.2f} 分鐘（允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘，剩餘 {time_diff:.2f} 分鐘）")
    report_lines.append(f"- 時間壓力感知：**{tp_status}**")
    if invalid_count > 0: report_lines.append(f"- **警告：** 因時間壓力下末段作答過快，有 {invalid_count} 題被標記為無效數據，未納入後續分析。")
    report_lines.append("")

    # 2. 表現概覽
    report_lines.append("**2. 表現概覽（內容領域對比）**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('poor_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('slow_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **超時率** 明顯更高。")
        if domain_tags.get('slow_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **超時率** 明顯更高。")
    else: report_lines.append(f"- {math_related_zh}與{non_math_related_zh}領域的表現在錯誤率和超時率上無顯著差異。")
    report_lines.append("")

    # 3. 核心問題分析
    report_lines.append("**3. 核心問題分析**")
    if sfe_triggered and diagnosed_df is not None and 'is_sfe' in diagnosed_df.columns:
        sfe_rows = diagnosed_df[diagnosed_df['is_sfe'] == True]
        if not sfe_rows.empty:
            sfe_domains_involved = set(sfe_rows['content_domain'].dropna()) if 'content_domain' in sfe_rows else set()
            sfe_types_involved = set(sfe_rows['question_type'].dropna()) if 'question_type' in sfe_rows else set()
            sfe_label = _translate_di(sfe_code)
            sfe_domains_zh = "，".join(sorted([_translate_di(d) for d in sfe_domains_involved]))
            sfe_types_zh = "，".join(sorted([_translate_di(t) for t in sfe_types_involved]))
            sfe_note = f"**尤其需要注意：{sfe_label}**"
            if sfe_domains_involved: sfe_note += f"（涉及領域：{sfe_domains_zh}）"
            if sfe_types_involved: sfe_note += f"（涉及題型：{sfe_types_zh}）"
            sfe_note += "。（註：SFE 指在已掌握難度範圍內題目失誤）"
            report_lines.append(f"- {sfe_note}")

    top_other_params_codes = []
    if not param_counts_all.empty:
        top_other_params_codes = param_counts_all[param_counts_all.index != sfe_code].head(2).index.tolist()
    if top_other_params_codes:
        report_lines.append("- **其他主要問題點：**")
        for param_code in top_other_params_codes: report_lines.append(f"  - {_translate_di(param_code)}")
    elif not sfe_triggered: report_lines.append("- 未識別出明顯的核心問題模式。")
    report_lines.append("")

    # 4. 特殊模式觀察
    report_lines.append("**4. 特殊模式觀察**")
    careless_triggered_ch4 = ch4.get('carelessness_issue_triggered')
    rushing_triggered_ch4 = ch4.get('early_rushing_risk_triggered')
    patterns_found = False
    if careless_triggered_ch4:
        fast_wrong_rate_str = _format_rate(ch4.get('fast_wrong_rate', 0.0))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_CARELESSNESS_ISSUE')}**：相對快速作答的題目中，錯誤比例偏高（{fast_wrong_rate_str}），提示可能存在粗心問題。")
        patterns_found = True
    if rushing_triggered_ch4:
        num_rush = len(ch4.get('early_rushing_questions', []))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')}**：測驗前期（{num_rush} 題）出現作答時間過短（<1分鐘）的情況，可能影響準確率。")
        patterns_found = True
    if not patterns_found: report_lines.append("- 未發現明顯的粗心或前期過快等負面行為模式。")
    report_lines.append("")

    # 6. 練習建議
    report_lines.append("**6. 練習建議**")
    recommendations = ch6.get('recommendations_list', [])
    if not recommendations: report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        for i, rec in enumerate(recommendations): report_lines.append(f"{i+1}. {rec.get('text', '無建議內容')}")
    report_lines.append("")

    # 7. 後續行動指引
    report_lines.append("**7. 後續行動指引**")
    report_lines.append("- **引導反思：**")
    reflection_prompts = []
    # Define Helper Functions Locally (can be moved outside if preferred)
    def get_pos_context_str_di(param_keys):
        positions = set().union(*[param_to_positions.get(key, set()) for key in param_keys if isinstance(key, str)])
        return f"（涉及題號：{sorted(list(positions))}）" if positions else ""
    def get_relevant_domains_di(param_keys):
        relevant_positions = set().union(*[param_to_positions.get(key, set()) for key in param_keys if isinstance(key, str)])
        relevant_domains_set = {_translate_di(domain) for domain, positions in domain_to_positions.items() if not relevant_positions.isdisjoint(positions)}
        return sorted(list(relevant_domains_set))
    # Define DI Reflection Parameter Lists (using English codes)
    reading_interpretation_params_di = ['DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR']
    concept_logic_params_di = ['DI_CONCEPT_APPLICATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR']
    data_handling_calc_params_di = ['DI_DATA_EXTRACTION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_CALCULATION_ERROR']
    msr_specific_params_di = ['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_MSR_READING_COMPREHENSION_BARRIER', 'DI_MSR_SINGLE_Q_BOTTLENECK']
    efficiency_params_di = ['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION', 'DI_EFFICIENCY_BOTTLENECK_LOGIC', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_INTEGRATION']
    carelessness_params_di = ['DI_CARELESSNESS_DETAIL_OMISSION', 'DI_BEHAVIOR_CARELESSNESS_ISSUE']
    # Generate Reflection Prompts
    active_concept_logic = [p for p in concept_logic_params_di if p in all_triggered_params]
    if active_concept_logic or sfe_triggered:
        keys = active_concept_logic + ([sfe_code] if sfe_triggered else [])
        domains = get_relevant_domains_di(keys)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 回想一下，在做錯的{ctx}題目時，具體是卡在哪個數學概念、邏輯關係或題目要求上？是完全沒思路，理解錯誤，還是知道方法但應用出錯？" + get_pos_context_str_di(keys))
    active_reading = [p for p in reading_interpretation_params_di if p in all_triggered_params]
    if active_reading:
        domains = get_relevant_domains_di(active_reading)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 對於做錯/慢的{ctx}題目，是文字資訊、圖表解讀有困難，還是無法準確理解問題要求？" + get_pos_context_str_di(active_reading))
    active_data = [p for p in data_handling_calc_params_di if p in all_triggered_params]
    if active_data:
        domains = get_relevant_domains_di(active_data)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 在處理{ctx}題目時，是提取數據、整合信息出錯，還是計算過程容易失誤？" + get_pos_context_str_di(active_data))
    active_msr = [p for p in msr_specific_params_di if p in all_triggered_params]
    if active_msr:
        reflection_prompts.append(f"  - 對於 MSR 題目，是多源資訊的整合理解有困難，還是閱讀材料或回答單題耗時過長？" + get_pos_context_str_di(active_msr))
    active_efficiency = [p for p in efficiency_params_di if p in all_triggered_params]
    if active_efficiency:
        domains = get_relevant_domains_di(active_efficiency)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 回想耗時過長的{ctx}題目，主要瓶頸是在閱讀、理解、思考、整合還是計算？" + get_pos_context_str_di(active_efficiency))
    active_careless = [p for p in carelessness_params_di if p in all_triggered_params]
    if active_careless: reflection_prompts.append("  - 回想一下，是否存在因為看錯字、忽略細節、誤解圖表或計算粗心導致的失誤？" + get_pos_context_str_di(active_careless))
    if not reflection_prompts: reflection_prompts.append("  - （本次分析未觸發典型的反思問題，建議結合練習計劃進行）")
    report_lines.extend(reflection_prompts)

    # Qualitative Analysis Suggestion
    if any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR']):
        report_lines.append("- **質化分析建議：**")
        report_lines.append("  - 如果您對報告中指出的某些問題（尤其是非數學相關的邏輯或閱讀理解錯誤）仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

    # Second Evidence Suggestion
    report_lines.append("- **二級證據參考建議：**")
    df_problem = pd.DataFrame() # Re-init for safety
    if diagnosed_df is not None and not diagnosed_df.empty and 'is_correct' in diagnosed_df and 'overtime' in diagnosed_df:
        df_problem = diagnosed_df[(diagnosed_df['is_correct'] == False) | (diagnosed_df['overtime'] == True)].copy()

    if not df_problem.empty:
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
        details_added_2nd_ev = False
        if 'time_performance_category' in df_problem.columns and 'question_type' in df_problem.columns and 'content_domain' in df_problem.columns and 'diagnostic_params' in df_problem.columns:
            performance_order = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct', 'Fast & Correct', 'Normal Time & Correct', 'Unknown']
            try: # Add try-except for robustness of groupby
                grouped_by_performance = df_problem.groupby('time_performance_category')
                for perf_en in performance_order:
                    if perf_en == 'Fast & Correct': continue # Skip Fast & Correct
                    if perf_en in grouped_by_performance.groups:
                        group_df = grouped_by_performance.get_group(perf_en)
                        if not group_df.empty:
                            perf_zh = _translate_di(perf_en)
                            types_zh = sorted([_translate_di(t) for t in group_df['question_type'].dropna().unique()])
                            domains_zh = sorted([_translate_di(d) for d in group_df['content_domain'].dropna().unique()])
                            report_lines.append(f"  - **{perf_zh}：** 需關注題型：【{', '.join(types_zh)}】；涉及領域：【{', '.join(domains_zh)}】。")

                            # Categorize parameters within the group
                            all_eng_codes_in_group = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)])
                            all_eng_codes_in_group.discard(INVALID_DATA_TAG_DI) # Remove invalid tag from categorization

                            labels_by_category = {category: [] for category in DI_PARAM_CATEGORY_ORDER}
                            for code_en in all_eng_codes_in_group:
                                category = DI_PARAM_TO_CATEGORY.get(code_en, 'Unknown')
                                labels_by_category[category].append(code_en)

                            label_parts_data = []
                            for category in DI_PARAM_CATEGORY_ORDER:
                                category_eng_codes = labels_by_category.get(category, [])
                                if category_eng_codes:
                                    category_zh = _translate_di(category)
                                    category_labels_zh = sorted([_translate_di(code) for code in category_eng_codes])
                                    label_parts_data.append((category_zh, category_labels_zh))

                            if label_parts_data:
                                report_lines.append("    注意相關問題點：")
                                for category_zh, sorted_labels_zh in label_parts_data:
                                    report_lines.append(f"      - 【{category_zh}：{'、'.join(sorted_labels_zh)}】")
                            details_added_2nd_ev = True
            except Exception:
                 # Log error if needed, prevent report generation from crashing
                 report_lines.append("  - （分組分析時出現內部錯誤）")
                 details_added_2nd_ev = True # Mark as detail attempted

        # Report core issues again
        core_issue_texts = []
        if sfe_triggered: core_issue_texts.append(_translate_di(sfe_code))
        if 'top_other_params_codes' in locals() and top_other_params_codes:
             core_issue_texts.extend([_translate_di(p) for p in top_other_params_codes])
        filtered_core_issues = [issue for issue in core_issue_texts if issue != _translate_di(INVALID_DATA_TAG_DI)]
        if filtered_core_issues:
             report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(filtered_core_issues)}】。")
             details_added_2nd_ev = True

        if not details_added_2nd_ev: report_lines.append("  - （本次分析未聚焦到特定的問題類型或領域）")
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else: report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")

    # Tool/Prompt section was removed earlier

    return "\n\n".join(report_lines)

# --- DI Diagnosis Wrapper (to match expected import signature in diagnosis_module.py) ---
def run_di_diagnosis(df_di):
    """
    Wrapper function that matches the expected signature in diagnosis_module.py.
    Calculates time pressure status and then calls run_di_diagnosis_processed.
    
    Args:
        df_di (pd.DataFrame): DataFrame containing DI responses.
        
    Returns:
        Tuple: (results_dict, report_str, processed_df) - Same as run_di_diagnosis_processed
    """
    # Calculate time pressure status for DI
    if df_di.empty:
        return {}, "Data Insights (DI) 部分無數據可供診斷。", pd.DataFrame()
        
    # Convert question_time to numeric if needed
    if 'question_time' not in df_di.columns:
        return {}, "Data Insights (DI) 資料缺少必要欄位：question_time。", pd.DataFrame()
    
    # Use same logic as in run_di_diagnosis_processed
    total_test_time = df_di['question_time'].sum(skipna=True)
    time_diff = MAX_ALLOWED_TIME_DI - total_test_time
    
    # Determine time pressure (simplified rule for wrapper)
    di_time_pressure_status = time_diff < TIME_PRESSURE_THRESHOLD_DI
    
    # Call the full processor with calculated pressure status
    return run_di_diagnosis_processed(df_di, di_time_pressure_status)