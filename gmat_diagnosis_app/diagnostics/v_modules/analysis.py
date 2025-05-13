"""
分析模塊：與V診斷相關的主要分析函數

此模塊包含用於分析文字科目(Verbal)作答數據的函數，
主要著重於識別行為模式和應用特定的診斷規則。
"""

import pandas as pd
import numpy as np
import logging
from gmat_diagnosis_app.diagnostics.v_modules.constants import (
    HASTY_GUESSING_THRESHOLD_MINUTES, 
    INVALID_DATA_TAG_V,
    V_SKILL_TO_ERROR_CATEGORY,
    RC_READING_TIME_THRESHOLD_3Q,
    RC_READING_TIME_THRESHOLD_4Q
)


def observe_patterns(df_v):
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

    return analysis


def apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill, avg_time_per_type, time_pressure_status):
    """
    Applies Chapter 3 diagnostic rules row-by-row.
    Calculates \'overtime\', \'is_sfe\', \'is_relatively_fast\', \'time_performance_category\', and \'diagnostic_params\'.
    MODIFIED: Includes overtime calculation based on time_pressure_status.
    MODIFIED: Calculates time_performance_category for ALL rows.
    MODIFIED: Applies SFE and detailed diagnostic_params only to VALID rows.
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

    all_params_list = [] # Renamed to avoid potential conflicts
    all_sfe_list = []
    all_fast_flags_list = []
    all_time_categories_list = []
    all_overtime_flags_list = []

    # Define parameter sets based on MD Ch3 rules
    # The individual cr_params_... and rc_params_... lists are now directly defined within param_assignment_map

    # Create a mapping for easier lookup
    param_assignment_map = {
        ('CR', 'Fast & Wrong'): [
            'CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP',
            'CR_STEM_UNDERSTANDING_ERROR_VOCAB',
            'CR_STEM_UNDERSTANDING_ERROR_SYNTAX',
            'CR_STEM_UNDERSTANDING_ERROR_LOGIC',
            'CR_STEM_UNDERSTANDING_ERROR_DOMAIN',
            'CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP',
            'CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING',
            'CR_REASONING_ERROR_PREDICTION_DIRECTION',
            'CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION',
            'CR_CHOICE_UNDERSTANDING_ERROR_VOCAB',
            'CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX',
            'CR_CHOICE_UNDERSTANDING_ERROR_LOGIC',
            'CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT',
            'CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION',
            'CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE'
        ],
        ('CR', 'Normal Time & Wrong'): [
            'CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP',
            'CR_STEM_UNDERSTANDING_ERROR_VOCAB',
            'CR_STEM_UNDERSTANDING_ERROR_SYNTAX',
            'CR_STEM_UNDERSTANDING_ERROR_LOGIC',
            'CR_STEM_UNDERSTANDING_ERROR_DOMAIN',
            'CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP',
            'CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING',
            'CR_REASONING_ERROR_PREDICTION_DIRECTION',
            'CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION',
            'CR_CHOICE_UNDERSTANDING_ERROR_VOCAB',
            'CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX',
            'CR_CHOICE_UNDERSTANDING_ERROR_LOGIC',
            'CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT',
            'CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION',
            'CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE'
        ],
        ('CR', 'Slow & Wrong'): [
            'CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN',
            'CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING',
            'CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING',
            'CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION',
            'CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT',
            'CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN',
            'CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP',
            'CR_STEM_UNDERSTANDING_ERROR_VOCAB',
            'CR_STEM_UNDERSTANDING_ERROR_SYNTAX',
            'CR_STEM_UNDERSTANDING_ERROR_LOGIC',
            'CR_STEM_UNDERSTANDING_ERROR_DOMAIN',
            'CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP',
            'CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING',
            'CR_REASONING_ERROR_PREDICTION_DIRECTION',
            'CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION',
            'CR_CHOICE_UNDERSTANDING_ERROR_VOCAB',
            'CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX',
            'CR_CHOICE_UNDERSTANDING_ERROR_LOGIC',
            'CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT',
            'CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION',
            'CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE'
        ],
        ('CR', 'Slow & Correct'): [
            'CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC',
            'CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN',
            'CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING',
            'CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING',
            'CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION',
            'CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT',
            'CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC',
            'CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN'
        ],
        ('RC', 'Fast & Wrong'): [
            'RC_READING_COMPREHENSION_ERROR_VOCAB',
            'RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS',
            'RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE',
            'RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING',
            'RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT',
            'RC_LOCATION_SKILL_ERROR_LOCATION',
            'RC_REASONING_ERROR_INFERENCE',
            'RC_CHOICE_ANALYSIS_ERROR_VOCAB',
            'RC_CHOICE_ANALYSIS_ERROR_SYNTAX',
            'RC_CHOICE_ANALYSIS_ERROR_LOGIC',
            'RC_CHOICE_ANALYSIS_ERROR_DOMAIN',
            'RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT',
            'RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION',
            'RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING'
        ],
        ('RC', 'Normal Time & Wrong'): [
            'RC_READING_COMPREHENSION_ERROR_VOCAB',
            'RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS',
            'RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE',
            'RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING',
            'RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT',
            'RC_LOCATION_SKILL_ERROR_LOCATION',
            'RC_REASONING_ERROR_INFERENCE',
            'RC_CHOICE_ANALYSIS_ERROR_VOCAB',
            'RC_CHOICE_ANALYSIS_ERROR_SYNTAX',
            'RC_CHOICE_ANALYSIS_ERROR_LOGIC',
            'RC_CHOICE_ANALYSIS_ERROR_DOMAIN',
            'RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT',
            'RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION',
            'RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING'
        ],
        ('RC', 'Slow & Wrong'): [
            'RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK',
            'RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS',
            'RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR',
            'RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK',
            'RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP',
            'RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY',
            'RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS',
            'RC_METHOD_DIFFICULTY_SPECIFIC_QUESTION_TYPE_HANDLING',
            'RC_READING_COMPREHENSION_ERROR_VOCAB',
            'RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS',
            'RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE',
            'RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING',
            'RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT',
            'RC_LOCATION_SKILL_ERROR_LOCATION',
            'RC_REASONING_ERROR_INFERENCE',
            'RC_CHOICE_ANALYSIS_ERROR_VOCAB',
            'RC_CHOICE_ANALYSIS_ERROR_SYNTAX',
            'RC_CHOICE_ANALYSIS_ERROR_LOGIC',
            'RC_CHOICE_ANALYSIS_ERROR_DOMAIN',
            'RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT',
            'RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION',
            'RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING'
        ],
        ('RC', 'Slow & Correct'): [
            'RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK',
            'RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS',
            'RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR',
            'RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK',
            'RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP',
            'RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY',
            'RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT',
            'RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS',
            'RC_METHOD_DIFFICULTY_SPECIFIC_QUESTION_TYPE_HANDLING'
        ],
    }

    # --- Determine CR overtime threshold based on input status ---
    # Import locally to avoid circular imports
    from gmat_diagnosis_app.diagnostics.v_modules.constants import CR_OVERTIME_THRESHOLDS
    cr_ot_threshold = CR_OVERTIME_THRESHOLDS.get(time_pressure_status, CR_OVERTIME_THRESHOLDS[False])

    # --- Iterate and apply rules ---
    for index, row in df_v.iterrows():
        # Initialize for each row
        current_params = [] # For detailed diagnostic tags
        current_is_sfe = False
        current_is_relatively_fast = False
        current_time_performance_category = 'Unknown' # Default, will be calculated for all
        current_is_overtime = False # Will be calculated for all

        # Get row data safely
        q_type = row.get('question_type')
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_invalid = bool(row.get('is_invalid', False))

        # 1. Calculate Overtime Status (for ALL rows)
        # This logic determines current_is_overtime based on q_type and thresholds.
        # It will be used for time_performance_category calculation for all rows.
        original_row_overtime = bool(row.get('overtime', False)) # Get pre-existing overtime if any

        if q_type == 'Critical Reasoning' and pd.notna(q_time) and q_time > cr_ot_threshold:
            current_is_overtime = True
        elif q_type == 'Reading Comprehension' and original_row_overtime: # Trust pre-calculated RC overtime
             current_is_overtime = True
        elif original_row_overtime: # If overtime was true from other sources (e.g. preprocessor for other types)
            current_is_overtime = True
        # If none of the above, current_is_overtime remains False (its initial value)
        
        # 2. Determine Time Flags (Fast/Normal) (for ALL rows)
        is_slow = current_is_overtime # 'Slow' is defined by being overtime for category assignment
        is_normal_time = False # Default
        avg_time = avg_time_per_type.get(q_type, np.inf) # Default to infinity if type not found

        if pd.notna(q_time) and avg_time != np.inf:
            if q_time < (avg_time * 0.75):  # Relatively fast threshold
                current_is_relatively_fast = True
            # Normal time is neither relatively fast nor slow (overtime)
            if not current_is_relatively_fast and not is_slow:
                 is_normal_time = True

        # 3. Assign Time Performance Category (for ALL rows)
        if is_correct:
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif is_slow: current_time_performance_category = 'Slow & Correct'
            else: current_time_performance_category = 'Normal Time & Correct'
        else: # Incorrect
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif is_slow: current_time_performance_category = 'Slow & Wrong'
            else: current_time_performance_category = 'Normal Time & Wrong'
        
        # Initialize diagnostic_params for current row processing
        # diagnostic_params from the input row (row.get('diagnostic_params')) are preserved if row is invalid and contains INVALID_DATA_TAG_V
        processed_diagnostic_params = [] 

        # 方案四：添加基於RC整組表現的診斷（僅對RC題型）
        if q_type == 'Reading Comprehension' and not is_invalid:
            # 獲取RC組表現分類
            rc_group_performance = row.get('rc_group_performance', None)
            rc_tolerance_applied = bool(row.get('rc_tolerance_applied', False))
            rc_overtime_culprit = bool(row.get('rc_overtime_culprit', False))
            rc_severe_overtime_culprit = bool(row.get('rc_severe_overtime_culprit', False))
            
            # 基於整組表現添加特定診斷參數
            if rc_group_performance == '良好' and rc_tolerance_applied:
                # 整組表現良好，但單題可能稍微超時（應用了寬容度）
                if current_is_overtime:
                    processed_diagnostic_params.append('RC_READING_SPEED_GOOD_GROUP_PERFORMANCE')
                    if is_correct:
                        # 如果是正確的，表明學生有良好的理解但需要提高單題效率
                        processed_diagnostic_params.append('RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MINOR_ISSUE')
                    else:
                        # 如果是錯誤的，可能是因為花了太多時間但仍未找到正確答案
                        processed_diagnostic_params.append('RC_CHOICE_ANALYSIS_EFFICIENCY_MINOR_ISSUE')
            
            elif rc_group_performance == '尚可':
                # 整組表現尚可，單題使用標準閾值判斷
                if current_is_overtime:
                    processed_diagnostic_params.append('RC_READING_SPEED_ACCEPTABLE_GROUP_PERFORMANCE')
                    if is_correct:
                        processed_diagnostic_params.append('RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MODERATE_ISSUE')
                    else:
                        processed_diagnostic_params.append('RC_CHOICE_ANALYSIS_EFFICIENCY_MODERATE_ISSUE')
            
            elif rc_group_performance == '不佳':
                # 整組表現不佳，整組都標記為超時
                processed_diagnostic_params.append('RC_READING_SPEED_POOR_GROUP_PERFORMANCE')
                
                # 如果是元兇，特別標記
                if rc_overtime_culprit:
                    if rc_severe_overtime_culprit:
                        processed_diagnostic_params.append('RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_SEVERE_ISSUE')
                    else:
                        processed_diagnostic_params.append('RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MAJOR_ISSUE')

        if not is_invalid: 
            # 4. Check SFE for VALID rows
            if not is_correct and pd.notna(q_diff):
                max_correct_diff = max_diff_dict.get(q_skill, -np.inf)
                q_diff_numeric = pd.to_numeric(q_diff, errors='coerce')
                if pd.notna(q_diff_numeric) and q_diff_numeric < max_correct_diff:
                     current_is_sfe = True
                     processed_diagnostic_params.append('FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE')

            # 5. Assign DETAILED Diagnostic Params for VALID rows
            # Hasty Guessing can apply to valid rows if they are very fast
            if pd.notna(q_time) and q_time < HASTY_GUESSING_THRESHOLD_MINUTES:
                 processed_diagnostic_params.append('BEHAVIOR_GUESSING_HASTY')

            valid_q_type_for_map = None
            if q_type == 'Critical Reasoning': valid_q_type_for_map = 'CR'
            elif q_type == 'Reading Comprehension': valid_q_type_for_map = 'RC'

            if valid_q_type_for_map:
                 # Use the time_performance_category calculated for all rows to find relevant detailed params
                 params_to_add = param_assignment_map.get((valid_q_type_for_map, current_time_performance_category), [])
                 
                 # RC特殊處理：根據MD檔邏輯，區分「閱讀文章超時」和「單題超時」的標籤
                 if valid_q_type_for_map == 'RC' and (current_time_performance_category == 'Slow & Wrong' or current_time_performance_category == 'Slow & Correct'):
                     # 不是全部添加，而是根據條件篩選
                     rc_reading_time = row.get('rc_reading_time', 0)
                     rc_reading_time_exists = pd.notna(rc_reading_time) and rc_reading_time > 0
                     rc_group_num_questions = row.get('rc_group_num_questions', 0)
                     rc_reading_time_threshold = RC_READING_TIME_THRESHOLD_3Q
                     if rc_group_num_questions == 4:
                         rc_reading_time_threshold = RC_READING_TIME_THRESHOLD_4Q
                     
                     # 判斷文章閱讀是否超時
                     is_reading_slow = False
                     if rc_reading_time_exists and pd.notna(rc_group_num_questions) and rc_group_num_questions > 0:
                         if (rc_group_num_questions == 3 and rc_reading_time > RC_READING_TIME_THRESHOLD_3Q) or \
                            (rc_group_num_questions == 4 and rc_reading_time > RC_READING_TIME_THRESHOLD_4Q):
                             is_reading_slow = True
                     
                     # 篩選適用的標籤
                     reading_time_related_tags = [
                         'RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK',
                         'RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS',
                         'RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR',
                         'RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK'
                     ]
                     
                     single_question_time_related_tags = [
                         'RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP',
                         'RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY',
                         'RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT',
                         'RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS',
                         'RC_METHOD_DIFFICULTY_SPECIFIC_QUESTION_TYPE_HANDLING'
                     ]
                     
                     # 只添加符合條件的標籤
                     filtered_params = []
                     for param in params_to_add:
                         # 如果是閱讀文章相關標籤，只在文章閱讀超時時添加
                         if param in reading_time_related_tags:
                             if is_reading_slow:
                                 filtered_params.append(param)
                         # 如果是單題處理相關標籤，只在單題超時時添加
                         elif param in single_question_time_related_tags:
                             if current_is_overtime:  # 單題超時
                                 filtered_params.append(param)
                         # 其他標籤（包括錯誤類標籤）直接添加
                         else:
                             filtered_params.append(param)
                     
                     # 使用篩選後的標籤列表代替原來的全部標籤
                     processed_diagnostic_params.extend(filtered_params)
                 else:
                     # CR和其他題型保持原有邏輯
                     processed_diagnostic_params.extend(params_to_add)
        else:
            # For INVALID rows: current_is_sfe remains False (or its value from row if we decide to preserve it)
            # diagnostic_params: Preserve existing if it's just the invalid tag, otherwise clear detailed ones.
            # The INVALID_DATA_TAG_V is typically added in main.py. Here, we ensure no other detailed tags are added for invalid rows.
            current_is_sfe = bool(row.get('is_sfe', False)) # Preserve SFE if it was somehow set for an invalid row before this
            existing_row_params = row.get('diagnostic_params', [])
            if isinstance(existing_row_params, list) and INVALID_DATA_TAG_V in existing_row_params:
                processed_diagnostic_params = [INVALID_DATA_TAG_V] # Keep only the invalid tag
            else:
                # If main.py didn't add it, or params were something else, ensure it has at least this for consistency
                processed_diagnostic_params = [INVALID_DATA_TAG_V] 
            # time_performance_category is ALREADY set correctly for invalid rows from step 3.

        # 6. Final Parameter List Cleanup and Ordering
        # For valid rows, this combines any pre-existing (e.g. from other behaviors) with newly diagnosed ones.
        # For invalid rows, it should ideally just be [INVALID_DATA_TAG_V].
        
        # Get original params from the input row to merge with processed_diagnostic_params
        # This is important if other parts of the code (e.g. behavioral analysis) already added tags to `diagnostic_params`
        original_input_row_params = row.get('diagnostic_params', [])
        if not isinstance(original_input_row_params, list): original_input_row_params = []

        # Combine: For valid rows, original_input_row_params might have behavioral tags, processed_diagnostic_params has SFE/Ch3 tags.
        # For invalid rows, original_input_row_params should have INVALID_DATA_TAG_V from main.py, processed_diagnostic_params also has it.
        temp_combined_params = []
        if is_invalid:
            # Ensure INVALID_DATA_TAG_V is present, and ideally only that for invalid rows from this function's perspective
            temp_combined_params = [INVALID_DATA_TAG_V] 
            # If original_input_row_params had other tags AND the invalid tag, this simplifies it.
            # If it only had other tags (undesired for invalid), this corrects it.
        else: # Valid row
            temp_combined_params = original_input_row_params + processed_diagnostic_params
            
        unique_params = list(dict.fromkeys(temp_combined_params)) # Remove duplicates, preserving order somewhat

        # Specific ordering for SFE and Invalid Tag
        if 'FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE' in unique_params:
             unique_params.remove('FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE')
             unique_params.insert(0, 'FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE')
        if INVALID_DATA_TAG_V in unique_params:
             unique_params.remove(INVALID_DATA_TAG_V)
             if is_invalid: # For invalid rows, Invalid tag should be the main/only tag from Ch3 perspective
                 unique_params = [INVALID_DATA_TAG_V]
             else: # For valid rows, if it somehow got there, put it at the end.
                 unique_params.append(INVALID_DATA_TAG_V)
        
        # Append calculated values for this row
        all_params_list.append(unique_params)
        all_sfe_list.append(current_is_sfe)
        all_fast_flags_list.append(current_is_relatively_fast)
        all_time_categories_list.append(current_time_performance_category) # This is the key: uses value calculated for all rows
        all_overtime_flags_list.append(current_is_overtime)

    # Assign lists back to DataFrame safely
    if len(all_params_list) == len(df_v):
        df_v['diagnostic_params'] = all_params_list
        df_v['is_sfe'] = all_sfe_list
        df_v['is_relatively_fast'] = all_fast_flags_list
        df_v['time_performance_category'] = all_time_categories_list # Assign the categories calculated for all rows
        df_v['overtime'] = all_overtime_flags_list
    else:
        logging.error("Error: Length mismatch during V Ch3 rule application. DataFrame not fully updated.")
        # Fallback to prevent crash, but data might be inconsistent
        if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''
        # Ensure other columns also exist to prevent downstream errors if update failed
        if 'diagnostic_params' not in df_v.columns: df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
        if 'is_sfe' not in df_v.columns: df_v['is_sfe'] = False
        if 'is_relatively_fast' not in df_v.columns: df_v['is_relatively_fast'] = False
        if 'overtime' not in df_v.columns: df_v['overtime'] = False

    return df_v 