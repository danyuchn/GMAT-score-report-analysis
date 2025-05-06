"""
V診斷模塊的分析功能

此模塊包含用於V(Verbal)診斷的核心分析函數，
用於評估學生表現和識別問題模式。
"""

import pandas as pd
import numpy as np
import logging
from gmat_diagnosis_app.diagnostics.v_modules.constants import (
    HASTY_GUESSING_THRESHOLD_MINUTES, 
    INVALID_DATA_TAG_V,
    V_SKILL_TO_ERROR_CATEGORY
)
from gmat_diagnosis_app.diagnostics.v_modules.utils import grade_difficulty_v


def observe_patterns(df_v, v_time_pressure_status):
    """Observes patterns and behavioral indicators for Chapter 5."""
    analysis = {
        'early_rushing_questions_indices': [],
        'early_rushing_flag_for_review': False,
        'fast_wrong_rate': None, # Based on is_relatively_fast (0.75*avg)
        'carelessness_issue': False, # Based on fast_wrong_rate > 0.25
        'param_triggers': [], # To store triggered behavioral params
        'carelessness_question_indices': [] # NEW: Store indices of questions triggering carelessness
    }
    if df_v.empty:
        return analysis

    total_questions = len(df_v)
    analysis['early_rushing_questions_indices'] = []

    # 1. Early Rushing Risk (符合核心邏輯文件 Chapter 5)
    if 'question_position' in df_v.columns and 'question_time' in df_v.columns:
        # Ensure columns are numeric before comparison
        df_v['question_position'] = pd.to_numeric(df_v['question_position'], errors='coerce')
        df_v['question_time'] = pd.to_numeric(df_v['question_time'], errors='coerce')

        # Filter out NaN positions before calculating limit
        valid_positions = df_v['question_position'].dropna()
        if not valid_positions.empty:
            max_pos = valid_positions.max()
            early_pos_limit = max_pos / 3 if max_pos > 0 else 0

            early_rush_mask = (
                (df_v['question_position'] <= early_pos_limit) &
                (df_v['question_time'] < 1.0) &
                df_v['question_position'].notna() & # Ensure position is not NaN
                df_v['question_time'].notna()      # Ensure time is not NaN
            )
            early_rushing_indices = df_v[early_rush_mask].index.tolist()
            if early_rushing_indices:
                analysis['early_rushing_questions_indices'] = early_rushing_indices
                analysis['early_rushing_flag_for_review'] = True
                analysis['param_triggers'].append('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')

    # 2. Carelessness Issue (符合核心邏輯文件 Chapter 5)
    if 'is_relatively_fast' in df_v.columns and 'is_correct' in df_v.columns:
        # 計算 num_relatively_fast_total (快的題目總數)
        fast_mask = df_v['is_relatively_fast'] == True
        num_relatively_fast_total = fast_mask.sum()
        
        # 計算 num_relatively_fast_incorrect (快且錯的題目數)
        fast_wrong_mask = fast_mask & (df_v['is_correct'] == False)
        num_relatively_fast_incorrect = fast_wrong_mask.sum()

        # 計算 fast_wrong_rate
        if num_relatively_fast_total > 0:
            fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
            analysis['fast_wrong_rate'] = fast_wrong_rate
            
            # 使用核心邏輯文件中定義的 0.25 閾值判斷粗心問題
            if fast_wrong_rate > 0.25:
                analysis['carelessness_issue'] = True
                analysis['param_triggers'].append('BEHAVIOR_CARELESSNESS_ISSUE')
                # 儲存快且錯的題目索引
                analysis['carelessness_question_indices'] = df_v.index[fast_wrong_mask].tolist()

    return analysis


def analyze_correct_slow(df_correct, question_type):
    """Analyzes correct but slow questions for Chapter 4."""
    # === DEBUG START - _analyze_correct_slow Entry ===
    logging.debug("[analyze_correct_slow - %s] Entry. Input df_correct shape: %s. Overtime counts:\n%s",
                 question_type, df_correct.shape, df_correct['overtime'].value_counts().to_string() if 'overtime' in df_correct else "Overtime col missing")
    # === DEBUG END ===
    analysis = {
        'total_correct': 0,
        'correct_slow_count': 0,
        'correct_slow_rate': 0.0,
        'avg_difficulty_slow': None,
        'avg_time_slow': 0.0,
        'dominant_bottleneck_type': 'N/A',
        'skill_breakdown_slow': {}
    }
    if df_correct.empty or 'question_time' not in df_correct.columns:
        return analysis

    total_correct = len(df_correct)
    analysis['total_correct'] = total_correct

    if 'overtime' not in df_correct.columns:
        return analysis # Cannot determine slowness without overtime flag

    slow_correct_df = df_correct[df_correct['overtime'] == True].copy()
    correct_slow_count = len(slow_correct_df)
    analysis['correct_slow_count'] = correct_slow_count
    # === DEBUG START - _analyze_correct_slow Count ===
    logging.debug("[analyze_correct_slow - %s] Filtered slow_correct_df shape: %s. Calculated correct_slow_count: %s",
                 question_type, slow_correct_df.shape, correct_slow_count)
    # === DEBUG END ===

    if total_correct > 0:
        analysis['correct_slow_rate'] = correct_slow_count / total_correct

    if correct_slow_count > 0:
        slow_correct_df.reset_index(drop=True, inplace=True)

        if 'question_difficulty' in slow_correct_df.columns:
            numeric_diff = pd.to_numeric(slow_correct_df['question_difficulty'], errors='coerce')
            if numeric_diff.notna().any():
                 analysis['avg_difficulty_slow'] = numeric_diff.mean()

        if 'question_time' in slow_correct_df.columns:
             numeric_time = pd.to_numeric(slow_correct_df['question_time'], errors='coerce')
             if numeric_time.notna().any():
                 analysis['avg_time_slow'] = numeric_time.mean()


        if 'question_fundamental_skill' in slow_correct_df.columns:
            skill_to_category = V_SKILL_TO_ERROR_CATEGORY.copy()
            skill_to_category['Unknown Skill'] = 'Unknown'
            slow_correct_df['error_category'] = slow_correct_df['question_fundamental_skill'].map(skill_to_category).fillna('Unknown')
            category_counts_slow = slow_correct_df['error_category'].value_counts()

            # Get counts safely using .get()
            reading_slow = category_counts_slow.get('Reading/Understanding', 0)
            logic_reasoning_slow = category_counts_slow.get('Logic/Reasoning', 0)
            inference_application_slow = category_counts_slow.get('Inference/Application', 0)
            logic_grammar_inference_slow = logic_reasoning_slow + inference_application_slow

            if reading_slow > logic_grammar_inference_slow and reading_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Reading/Understanding'
            elif logic_grammar_inference_slow > reading_slow and logic_grammar_inference_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Logic/Reasoning or Inference/Application' # Combine for clarity
            else:
                analysis['dominant_bottleneck_type'] = 'Mixed/Unclear'

            analysis['skill_breakdown_slow'] = slow_correct_df['question_fundamental_skill'].value_counts().to_dict()
        else:
            analysis['dominant_bottleneck_type'] = 'Skill data missing'

    # === DEBUG START - _analyze_correct_slow Return ===
    logging.debug("[analyze_correct_slow - %s] Returning analysis: %s", question_type, analysis)
    # === DEBUG END ===
    return analysis


def apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill, avg_time_per_type, time_pressure_status):
    """
    Applies Chapter 3 diagnostic rules row-by-row.
    Calculates \'overtime\', \'is_sfe\', \'is_relatively_fast\', \'time_performance_category\', and \'diagnostic_params\'.
    MODIFIED: Includes overtime calculation based on time_pressure_status.
    """
    if df_v.empty:
        # Initialize columns even for empty df to ensure consistency
        for col in ['diagnostic_params', 'is_sfe', 'is_relatively_fast', 'time_performance_category', 'overtime']:
            if col == 'diagnostic_params':
                df_v[col] = [[] for _ in range(len(df_v))]
            elif col == 'time_performance_category':
                df_v[col] = ''
            else: # Boolean flags
                df_v[col] = False
        return df_v

    # --- Initialize columns if they don't exist ---
    if 'diagnostic_params' not in df_v.columns: df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    else: df_v['diagnostic_params'] = df_v['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x]))
    if 'is_sfe' not in df_v.columns: df_v['is_sfe'] = False
    if 'is_relatively_fast' not in df_v.columns: df_v['is_relatively_fast'] = False
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''
    # >>> Initialize overtime <<<
    if 'overtime' not in df_v.columns: df_v['overtime'] = False

    max_diff_dict = max_correct_difficulty_per_skill

    all_params = []
    all_sfe = []
    all_fast_flags = []
    all_time_categories = []
    all_overtime_flags = [] # To store calculated overtime status

    # Define parameter sets based on MD Ch3 rules
    cr_params_fast_wrong = ['CR_METHOD_PROCESS_DEVIATION', 'CR_METHOD_TYPE_SPECIFIC_ERROR', 'CR_READING_BASIC_OMISSION']
    cr_params_normal_wrong = ['CR_READING_DIFFICULTY_STEM', 'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION', 'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_ABSTRACTION_DIFFICULTY', 'CR_REASONING_PREDICTION_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY', 'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY', 'CR_AC_ANALYSIS_RELEVANCE_ERROR', 'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION', 'CR_METHOD_TYPE_SPECIFIC_ERROR']
    cr_params_slow_wrong_time = ['CR_READING_TIME_EXCESSIVE', 'CR_REASONING_TIME_EXCESSIVE', 'CR_AC_ANALYSIS_TIME_EXCESSIVE']
    cr_params_slow_correct_eff = ['EFFICIENCY_BOTTLENECK_READING', 'EFFICIENCY_BOTTLENECK_REASONING', 'EFFICIENCY_BOTTLENECK_AC_ANALYSIS']
    rc_params_fast_wrong = ['RC_READING_INFO_LOCATION_ERROR', 'RC_READING_KEYWORD_LOGIC_OMISSION', 'RC_METHOD_TYPE_SPECIFIC_ERROR']
    rc_params_normal_wrong = ['RC_READING_VOCAB_BOTTLENECK', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP', 'RC_READING_PRECISION_INSUFFICIENT', 'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION', 'RC_LOCATION_ERROR_INEFFICIENCY', 'RC_REASONING_INFERENCE_WEAKNESS', 'RC_AC_ANALYSIS_DIFFICULTY', 'RC_METHOD_TYPE_SPECIFIC_ERROR']
    rc_params_slow_wrong_time = ['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_METHOD_INEFFICIENT_READING', 'RC_LOCATION_TIME_EXCESSIVE', 'RC_REASONING_TIME_EXCESSIVE', 'RC_AC_ANALYSIS_TIME_EXCESSIVE']
    rc_params_slow_correct_eff = ['EFFICIENCY_BOTTLENECK_READING', 'EFFICIENCY_BOTTLENECK_LOCATION', 'EFFICIENCY_BOTTLENECK_REASONING', 'EFFICIENCY_BOTTLENECK_AC_ANALYSIS']

    # Create a mapping for easier lookup
    param_assignment_map = {
        ('CR', 'Fast & Wrong'): cr_params_fast_wrong,
        ('CR', 'Normal Time & Wrong'): cr_params_normal_wrong,
        ('CR', 'Slow & Wrong'): cr_params_slow_wrong_time + cr_params_normal_wrong, # Combine time + root cause
        ('CR', 'Slow & Correct'): cr_params_slow_correct_eff,
        ('RC', 'Fast & Wrong'): rc_params_fast_wrong,
        ('RC', 'Normal Time & Wrong'): rc_params_normal_wrong,
        ('RC', 'Slow & Wrong'): rc_params_slow_wrong_time + rc_params_normal_wrong, # Combine time + root cause
        ('RC', 'Slow & Correct'): rc_params_slow_correct_eff,
    }

    # --- Determine CR overtime threshold based on input status ---
    # Import locally to avoid circular imports
    from gmat_diagnosis_app.diagnostics.v_modules.constants import CR_OVERTIME_THRESHOLDS
    cr_ot_threshold = CR_OVERTIME_THRESHOLDS.get(time_pressure_status, CR_OVERTIME_THRESHOLDS[False])

    # --- Iterate and apply rules ---
    for index, row in df_v.iterrows():
        # Initialize for each row
        current_params = []
        current_is_sfe = False
        current_is_relatively_fast = False
        current_time_performance_category = 'Unknown'
        current_is_overtime = False # Calculate overtime status here

        # Get row data safely
        q_type = row.get('question_type')
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_invalid = bool(row.get('is_invalid', False))
        # Assume RC group/individual overtime flags are PRE-CALCULATED and stored if needed,
        # or rely solely on single question time for CR. The code below ONLY handles CR overtime directly.
        # If RC metrics were calculated externally, 'overtime' column should reflect the combined status.
        # We will calculate CR overtime here and assume RC overtime is handled externally if needed.

        # 0. Skip processing for invalid rows, but keep their index for assignment
        if is_invalid:
            all_params.append(row.get('diagnostic_params', [])) # Keep existing params (might include invalid tag)
            all_sfe.append(row.get('is_sfe', False))
            all_fast_flags.append(row.get('is_relatively_fast', False))
            all_time_categories.append(row.get('time_performance_category', 'Invalid'))
            all_overtime_flags.append(row.get('overtime', False)) # Keep existing overtime status
            continue

        # 1. Calculate Overtime Status (Only for CR directly here)
        # --- MODIFICATION: Use full question type names ---
        if q_type == 'Critical Reasoning' and pd.notna(q_time) and q_time > cr_ot_threshold:
            current_is_overtime = True
        # >>> IMPORTANT: For RC, we assume 'overtime' flag is potentially pre-calculated <<<
        elif q_type == 'Reading Comprehension' and 'overtime' in row and bool(row['overtime']):
             current_is_overtime = True
        # --- END MODIFICATION ---

        # 2. Check SFE
        if not is_correct and pd.notna(q_diff):
            # Ensure skill exists in dict, otherwise default to -inf
            max_correct_diff = max_diff_dict.get(q_skill, -np.inf)
            # Ensure q_diff is numeric before comparison
            q_diff_numeric = pd.to_numeric(q_diff, errors='coerce')
            if pd.notna(q_diff_numeric) and q_diff_numeric < max_correct_diff:
                 current_is_sfe = True
                 current_params.append('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')


        # 3. Determine Time Flags (Fast/Normal)
        is_slow = current_is_overtime # 'Slow' is defined by being overtime
        is_normal_time = False
        avg_time = avg_time_per_type.get(q_type, np.inf) # Default to infinity if type not found

        if pd.notna(q_time) and avg_time != np.inf:
            if q_time < (avg_time * 0.75):  # 核心邏輯文件定義的相對快閾值
                current_is_relatively_fast = True
            # Check for guessing threshold
            if q_time < HASTY_GUESSING_THRESHOLD_MINUTES:
                 current_params.append('BEHAVIOR_GUESSING_HASTY')
            # Normal time is neither fast nor slow
            if not current_is_relatively_fast and not is_slow:
                 is_normal_time = True

        # 4. Assign Time Performance Category based on calculated flags
        if is_correct:
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif current_is_overtime: current_time_performance_category = 'Slow & Correct' # Use current_is_overtime directly
            else: current_time_performance_category = 'Normal Time & Correct'
        else: # Incorrect
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif current_is_overtime: current_time_performance_category = 'Slow & Wrong' # Use current_is_overtime directly
            else: current_time_performance_category = 'Normal Time & Wrong'

        # 5. Assign DETAILED Diagnostic Params using the map based on the category
        # Ensure q_type is valid before lookup
        # --- MODIFICATION: Handle full question type names ---
        if q_type == 'Critical Reasoning':
            valid_q_type = 'CR'
        elif q_type == 'Reading Comprehension':
            valid_q_type = 'RC'
        else:
            valid_q_type = None # Keep None for other types or invalid values
        # --- END MODIFICATION ---

        if valid_q_type:
             params_to_add = param_assignment_map.get((valid_q_type, current_time_performance_category), [])
             current_params.extend(params_to_add)

        # 6. Final Parameter List Cleanup
        # Use existing params if available and add new ones
        existing_params = row.get('diagnostic_params', [])
        if not isinstance(existing_params, list): existing_params = []
        combined_params = existing_params + current_params
        unique_params = list(dict.fromkeys(combined_params)) # Preserve order somewhat while removing duplicates

        # Ensure SFE is first if present
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
             unique_params.remove('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
             unique_params.insert(0, 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        # Ensure invalid tag is last if present
        if INVALID_DATA_TAG_V in unique_params:
             unique_params.remove(INVALID_DATA_TAG_V)
             unique_params.append(INVALID_DATA_TAG_V)

        # Append calculated values for this row
        all_params.append(unique_params)
        all_sfe.append(current_is_sfe)
        all_fast_flags.append(current_is_relatively_fast)
        all_time_categories.append(current_time_performance_category)
        all_overtime_flags.append(current_is_overtime) # Store calculated overtime

    # Assign lists back to DataFrame safely
    if len(all_params) == len(df_v):
        df_v['diagnostic_params'] = all_params
        df_v['is_sfe'] = all_sfe
        df_v['is_relatively_fast'] = all_fast_flags
        df_v['time_performance_category'] = all_time_categories
        df_v['overtime'] = all_overtime_flags # 更新 overtime 狀態以確保一致性
    else:
        print("Error: Length mismatch during Chapter 3 rule application. DataFrame not fully updated.")

    return df_v 