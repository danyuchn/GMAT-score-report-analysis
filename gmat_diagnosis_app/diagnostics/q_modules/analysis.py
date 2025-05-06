"""
Q診斷模塊的分析功能

此模塊包含用於Q(Quantitative)診斷的核心分析函數，
用於評估學生表現和識別問題模式。
"""

import pandas as pd
import numpy as np
from gmat_diagnosis_app.diagnostics.q_modules.constants import (
    INVALID_DATA_TAG_Q,
    PARAM_ASSIGNMENT_RULES,
    DEFAULT_INCORRECT_PARAMS
)


def diagnose_q_root_causes(df, avg_times, max_diffs):
    """
    Analyzes root causes row-by-row. Adds 'is_sfe', 'time_performance_category',
    and 'diagnostic_params' (raw codes) columns using vectorized ops and dict lookup.
    Handles invalid data tagging.
    """
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = ''
        return df

    # --- Vectorized Calculations for is_sfe and time_performance_category ---
    # 計算每個題目對應題型的平均時間
    df['avg_time_for_type'] = df['question_type'].map(avg_times).fillna(2.0)
    numeric_time = pd.to_numeric(df['question_time'], errors='coerce')
    
    # 判斷是否相對快速（使用0.75乘數，與核心邏輯文件第三章一致）
    df['is_relatively_fast'] = (numeric_time < (df['avg_time_for_type'] * 0.75)).fillna(False)
    # 判斷是否超時
    df['is_slow'] = df['overtime'].fillna(False)

    # 設定時間表現分類
    conditions = [
        (df['is_correct'] == True) & (df['is_relatively_fast'] == True),
        (df['is_correct'] == True) & (df['is_slow'] == True),
        (df['is_correct'] == True) & (df['is_relatively_fast'] == False) & (df['is_slow'] == False),
        (df['is_correct'] == False) & (df['is_relatively_fast'] == True),
        (df['is_correct'] == False) & (df['is_slow'] == True),
        (df['is_correct'] == False) & (df['is_relatively_fast'] == False) & (df['is_slow'] == False)
    ]
    choices = [
        'Fast & Correct', 'Slow & Correct', 'Normal Time & Correct',
        'Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong'
    ]
    df['time_performance_category'] = np.select(conditions, choices, default='Unknown')
    df.loc[numeric_time.isna(), 'time_performance_category'] = 'Unknown'

    # 判斷是否特殊關注錯誤(SFE)：
    # 該題的難度低於該學生在該技能上已正確完成的最高難度
    df['max_correct_diff_for_skill'] = df['question_fundamental_skill'].map(max_diffs).fillna(-np.inf)
    numeric_diff = pd.to_numeric(df['question_difficulty'], errors='coerce')
    df['is_sfe'] = (
        (df['is_correct'] == False) & (df['is_invalid'] == False) &
        (numeric_diff.notna()) & (numeric_diff < df['max_correct_diff_for_skill'])
    ).fillna(False)

    # --- Parameter Assignment using Dictionary Lookup (Loop still needed for combining logic) ---
    all_diagnostic_params = []
    for index, row in df.iterrows():
        current_params = []
        is_sfe = row['is_sfe']
        time_perf_cat = row['time_performance_category']
        q_type = row['question_type']
        is_correct = bool(row.get('is_correct', True))
        is_invalid = bool(row.get('is_invalid', False))

        # 1. Get base parameters from rules dictionary
        lookup_key = (time_perf_cat, q_type)
        # Only apply rules if incorrect or slow & correct
        if not is_correct:
            # Special handling for Unknown time category if incorrect
            if time_perf_cat == 'Unknown':
                 base_params = PARAM_ASSIGNMENT_RULES.get(('Unknown', q_type), DEFAULT_INCORRECT_PARAMS)
            else:
                 base_params = PARAM_ASSIGNMENT_RULES.get(lookup_key, DEFAULT_INCORRECT_PARAMS) # Fallback if combo missing
            current_params.extend(base_params)
        elif time_perf_cat == 'Slow & Correct':
            base_params = PARAM_ASSIGNMENT_RULES.get(lookup_key, []) # Get efficiency params
            current_params.extend(base_params)
        # Other correct categories ('Fast & Correct', 'Normal Time & Correct') get no params from dict

        # 2. Add SFE if applicable (regardless of time)
        if is_sfe:
            # Avoid adding SFE if already present from the rule dictionary (though unlikely)
            if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' not in current_params:
                current_params.append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 3. Remove duplicates and ensure SFE is first
        unique_params = list(dict.fromkeys(current_params)) # Preserve order somewhat
        if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
            unique_params.remove('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            unique_params.insert(0, 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 4. Add invalid tag if needed
        if is_invalid:
            # Avoid adding duplicate invalid tags
            if INVALID_DATA_TAG_Q not in unique_params:
                 # Insert invalid tag at the end for clarity
                 unique_params.append(INVALID_DATA_TAG_Q)

        all_diagnostic_params.append(unique_params)

    df['diagnostic_params'] = all_diagnostic_params

    # --- Cleanup and Return ---
    cols_to_drop = ['avg_time_for_type', 'is_relatively_fast', 'is_slow', 'max_correct_diff_for_skill']
    df_final = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

    return df_final


def diagnose_q_internal(df_q_valid_diagnosed):
    """Performs detailed Q diagnosis (Chapters 2-6).
       Assumes df_q_valid_diagnosed contains only valid Q data with pre-calculated
       'is_sfe', 'time_performance_category', and 'diagnostic_params_list' columns.
    """
    if df_q_valid_diagnosed.empty:
        return {"chapter2_flags": {}}

    # --- Chapter 2: Real vs Pure Analysis ---
    df_real = df_q_valid_diagnosed[df_q_valid_diagnosed['question_type'] == 'REAL'].copy()
    df_pure = df_q_valid_diagnosed[df_q_valid_diagnosed['question_type'] == 'PURE'].copy()
    num_total_real = len(df_real)
    num_total_pure = len(df_pure)
    num_real_errors = df_real['is_correct'].eq(False).sum()
    num_pure_errors = df_pure['is_correct'].eq(False).sum()
    num_real_overtime = df_real['overtime'].eq(True).sum() if 'overtime' in df_real.columns else 0
    num_pure_overtime = df_pure['overtime'].eq(True).sum() if 'overtime' in df_pure.columns else 0
    wrong_rate_real = num_real_errors / num_total_real if num_total_real > 0 else 0
    wrong_rate_pure = num_pure_errors / num_total_pure if num_total_pure > 0 else 0
    over_time_rate_real = num_real_overtime / num_total_real if num_total_real > 0 else 0
    over_time_rate_pure = num_pure_overtime / num_total_pure if num_total_pure > 0 else 0
    significant_error_diff = abs(num_real_errors - num_pure_errors) >= 2
    significant_overtime_diff = abs(num_real_overtime - num_pure_overtime) >= 2
    ch2_flags = {'poor_real': False, 'poor_pure': False, 'slow_real': False, 'slow_pure': False}
    if significant_error_diff:
        if wrong_rate_real > wrong_rate_pure: ch2_flags['poor_real'] = True
        elif wrong_rate_pure > wrong_rate_real: ch2_flags['poor_pure'] = True
    if significant_overtime_diff:
        if over_time_rate_real > over_time_rate_pure: ch2_flags['slow_real'] = True
        elif over_time_rate_pure > over_time_rate_real: ch2_flags['slow_pure'] = True
    results_ch2_summary = pd.DataFrame([
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Total Questions', 'Real_Value': num_total_real, 'Pure_Value': num_total_pure},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Count', 'Real_Value': num_real_errors, 'Pure_Value': num_pure_errors},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Rate', 'Real_Value': wrong_rate_real, 'Pure_Value': wrong_rate_pure},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Count', 'Real_Value': num_real_overtime, 'Pure_Value': num_pure_overtime},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Rate', 'Real_Value': over_time_rate_real, 'Pure_Value': over_time_rate_pure}
    ])

    # --- Chapter 3: Error Cause Analysis (Simplified: Collect Pre-diagnosed Info) ---
    error_analysis_list = []
    df_errors = df_q_valid_diagnosed[df_q_valid_diagnosed['is_correct'] == False].copy()
    if not df_errors.empty:
        for index, row in df_errors.iterrows():
            error_analysis_list.append({
                'question_position': row['question_position'],
                'Skill': row.get('question_fundamental_skill', 'Unknown Skill'),
                'Type': row['question_type'],
                'Difficulty': row.get('question_difficulty', None),
                'Time': row.get('question_time', None),
                'Time_Performance': row.get('time_performance_category', 'Unknown'),
                'Is_SFE': row.get('is_sfe', False),
                'Possible_Params': row.get('diagnostic_params_list', [])
            })

    # --- Chapter 4: Correct but Slow Analysis ---
    correct_slow_analysis_list = []
    if 'overtime' in df_q_valid_diagnosed.columns:
        df_correct_slow = df_q_valid_diagnosed[(df_q_valid_diagnosed['is_correct'] == True) & (df_q_valid_diagnosed['overtime'] == True)].copy()
        if not df_correct_slow.empty:
            for index, row in df_correct_slow.iterrows():
                correct_slow_analysis_list.append({
                    'question_position': row['question_position'],
                    'Skill': row.get('question_fundamental_skill', 'Unknown Skill'),
                    'Type': row['question_type'],
                    'Time': row.get('question_time', None),
                    'Possible_Params': row.get('diagnostic_params_list', [])
                })

    return {
        "chapter2_flags": ch2_flags,
        "chapter2_summary": results_ch2_summary.to_dict('records'),
        "chapter3_error_details": error_analysis_list,
        "chapter4_correct_slow_details": correct_slow_analysis_list
    } 