import pandas as pd
import numpy as np
# Removed: import math

# --- V-Specific Constants ---
# CR Overtime Thresholds (minutes) based on pressure
CR_OVERTIME_THRESHOLDS = {
    True: 2.0, # High Pressure
    False: 2.5 # Low Pressure
}
RC_INDIVIDUAL_Q_THRESHOLD_MINUTES = 2.0
RC_READING_TIME_THRESHOLD_3Q = 2.0 # minutes
RC_READING_TIME_THRESHOLD_4Q = 2.5 # minutes
RC_GROUP_TARGET_TIME_ADJUSTMENT = 1.0 # minutes (add to target before checking group_overtime)

# RC Group Target Times (minutes) based on pressure
RC_GROUP_TARGET_TIMES = {
    True: { # High Pressure
        3: 6.0,
        4: 8.0
    },
    False: { # Low Pressure
        3: 7.0,
        4: 9.0
    }
}

# Define Hasty/Abandoned Threshold for use in Chapter 1/3 logic
V_INVALID_TIME_ABANDONED = 0.5 # minutes (as per V-Doc Ch1 Invalid rule)
V_INVALID_TIME_HASTY_MIN = 1.0 # minutes (as per V-Doc Ch1 Invalid rule)
HASTY_GUESSING_THRESHOLD_MINUTES = 0.5 # minutes (Used for BEHAVIOR_GUESSING_HASTY tag in Ch3)
INVALID_DATA_TAG_V = "數據無效：用時過短（受時間壓力影響）"

# Map fundamental skills (expected in data) to broader error categories for Chapter 3
V_SKILL_TO_ERROR_CATEGORY = {
    # VDOC Defined Core Skills
    'Plan/Construct': 'Logic/Reasoning',
    'Identify Stated Idea': 'Reading/Understanding',
    'Identify Inferred Idea': 'Inference/Application',
    'Analysis/Critique': 'Logic/Reasoning',
    # Common - Foundational Mastery Instability
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    # Default/Unknown
    'Unknown Skill': 'Unknown',
    # Add other non-skill mappings if needed
    'DI_DATA_INTERPRETATION_ERROR': 'Unknown',
    'DI_LOGICAL_REASONING_ERROR': 'Unknown',
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'Unknown',
}

# REMOVED Unused V_DIAGNOSTIC_PARAMS constant
# REMOVED Unused CARELESSNESS_SKILLS constant

# --- 參數類別順序定義 ---
V_PARAM_CATEGORY_ORDER = [
    'SFE',                  # 基礎掌握
    'Reading',              # 閱讀理解
    'Reasoning',            # 邏輯推理
    'Timing',               # 時間管理
    'Process',              # 流程方法
    'AC_Analysis',          # 選項分析
    'Question_Understanding', # 問題理解
    'Behavioral',           # 行為模式
    'Unknown'               # 未分類
]

# --- 參數到類別的映射 ---
V_PARAM_TO_CATEGORY = {
    # SFE
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',

    # Reading
    'CR_READING_BASIC_OMISSION': 'Reading',
    'CR_READING_DIFFICULTY_STEM': 'Reading',
    'CR_READING_TIME_EXCESSIVE': 'Reading', # Also Timing
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': 'Reading', # Also Timing
    'RC_READING_COMPREHENSION_BARRIER': 'Reading',
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': 'Reading',
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': 'Reading',
    'RC_READING_VOCAB_BOTTLENECK': 'Reading',
    'RC_READING_PRECISION_INSUFFICIENT': 'Reading',
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': 'Reading',
    'RC_READING_INFO_LOCATION_ERROR': 'Reading', # ADDED
    'RC_READING_KEYWORD_LOGIC_OMISSION': 'Reading', # ADDED

    # Reasoning
    'CR_REASONING_CHAIN_ERROR': 'Reasoning',
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': 'Reasoning',
    'CR_REASONING_ABSTRACTION_DIFFICULTY': 'Reasoning',
    'CR_REASONING_PREDICTION_ERROR': 'Reasoning',
    'CR_REASONING_TIME_EXCESSIVE': 'Reasoning', # Also Timing
    'RC_REASONING_INFERENCE_WEAKNESS': 'Reasoning',
    'RC_REASONING_TIME_EXCESSIVE': 'Reasoning', # Also Timing - ADDED

    # Timing
    'CR_READING_TIME_EXCESSIVE': 'Timing', # Also Reading
    'CR_REASONING_TIME_EXCESSIVE': 'Timing', # Also Reasoning
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': 'Timing', # Also AC_Analysis
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': 'Timing', # Also Reading
    'RC_LOCATION_TIME_EXCESSIVE': 'Timing', # ADDED
    'RC_REASONING_TIME_EXCESSIVE': 'Timing', # Also Reasoning - ADDED
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': 'Timing', # Also AC_Analysis - ADDED
    'EFFICIENCY_BOTTLENECK_READING': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_REASONING': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_LOCATION': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': 'Timing', # ADDED

    # Process
    'CR_METHOD_TYPE_SPECIFIC_ERROR': 'Process',
    'CR_METHOD_PROCESS_DEVIATION': 'Process',
    'RC_METHOD_INEFFICIENT_READING': 'Process', # ADDED
    'RC_LOCATION_ERROR_INEFFICIENCY': 'Process', # ADDED
    'RC_METHOD_TYPE_SPECIFIC_ERROR': 'Process', # ADDED

    # AC_Analysis (Answer Choice Analysis)
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': 'AC_Analysis',
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': 'AC_Analysis',
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': 'AC_Analysis',
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': 'AC_Analysis', # Also Timing
    'RC_AC_ANALYSIS_DIFFICULTY': 'AC_Analysis',
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': 'AC_Analysis', # Also Timing - ADDED

    # Question_Understanding
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding',
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding', # ADDED

    # Behavioral
    'BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral',
    'BEHAVIOR_GUESSING_HASTY': 'Behavioral'
}

# --- V-Specific Helper Functions ---

# Note: Kept unused function as requested in previous prompt refinement.
def _analyze_skill_coverage(df_v, chapter2_metrics, exempted_v_skills):
    """Analyzes skill coverage and blind spots for Chapter 6."""
    analysis = {
        'skill_details': {}, # Dict mapping skill -> {total, errors, error_rate, status (Y/Z/X/OK), sfe_error_count, is_y_sfe}
        'weak_skills_y': [],
        'insufficient_coverage_z': [],
        'exempted_skills_x': list(exempted_v_skills),
        'macro_override_reading': {'triggered': False, 'reason': 'N/A', 'skills_involved': []}, # Y-agg/Z-agg Reading
        'macro_override_logic_grammar_inference': {'triggered': False, 'reason': 'N/A', 'skills_involved': []} # Y-agg/Z-agg Other
    }
    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        return analysis

    # Get average error rates from Chapter 2 (handle potential missing keys)
    cr_avg_error_rate = chapter2_metrics.get('cr_metrics', {}).get('error_rate', 0.0)
    rc_avg_error_rate = chapter2_metrics.get('rc_metrics', {}).get('error_rate', 0.0)

    # Map question types to their average error rates
    type_to_avg_error_rate = {
        'CR': cr_avg_error_rate,
        'RC': rc_avg_error_rate,
    }

    # Minimum occurrences for Z rule
    min_occurrences_for_z = 3
    # Error rate threshold multiplier for Y rule (e.g., 1.5x the average)
    y_rule_multiplier = 1.5
    # Minimum error rate for Y rule (e.g., must be at least 30%)
    y_rule_min_error_rate = 0.30
    # SFE rate threshold for Y-SFE rule (e.g., > 30% of errors are SFE)
    y_sfe_threshold = 0.30

    skill_groups = df_v.groupby('question_fundamental_skill')

    reading_y_skills = []
    reading_z_skills = []
    logic_etc_y_skills = []
    logic_etc_z_skills = []

    for skill, group in skill_groups:
        if skill == 'Unknown Skill' or skill not in V_SKILL_TO_ERROR_CATEGORY: continue # Skip unknown

        total = len(group)
        errors = group['is_correct'].eq(False).sum()
        error_rate = errors / total if total > 0 else 0.0
        question_type = group['question_type'].iloc[0] # Assume skill maps to one type
        avg_error_rate_for_type = type_to_avg_error_rate.get(question_type, 0.0)
        # Correctly calculate SFE errors within the group for this skill
        sfe_errors = group[group['is_sfe'] == True].shape[0] if 'is_sfe' in group.columns else 0 # Count SFE flags directly
        sfe_error_rate_within_skill_errors = sfe_errors / errors if errors > 0 else 0.0

        status = 'OK'
        is_y_sfe = False

        # Apply rules
        if skill in exempted_v_skills:
            status = 'X' # Exempted
            # No need to append here, exempted_skills_x is initialized with the list
        elif total < min_occurrences_for_z:
            status = 'Z' # Insufficient coverage
            analysis['insufficient_coverage_z'].append(skill)
            # Add to macro lists
            category = V_SKILL_TO_ERROR_CATEGORY.get(skill)
            if category == 'Reading/Understanding': reading_z_skills.append(skill)
            elif category in ['Logic/Reasoning', 'Inference/Application']: logic_etc_z_skills.append(skill)
        elif error_rate > max(avg_error_rate_for_type * y_rule_multiplier, y_rule_min_error_rate) and total >= min_occurrences_for_z:
            status = 'Y' # Weak skill
            analysis['weak_skills_y'].append(skill)
            # Check for Y-SFE
            # SFE is considered high if SFE flags account for > threshold % of the errors for this skill
            if sfe_error_rate_within_skill_errors > y_sfe_threshold:
                 is_y_sfe = True
                 status = 'Y-SFE' # Weak skill with high SFE component
            # Add to macro lists
            category = V_SKILL_TO_ERROR_CATEGORY.get(skill)
            if category == 'Reading/Understanding': reading_y_skills.append(skill)
            elif category in ['Logic/Reasoning', 'Inference/Application']: logic_etc_y_skills.append(skill)

        analysis['skill_details'][skill] = {
            'total': total,
            'errors': errors,
            'error_rate': error_rate,
            'status': status,
            'sfe_error_count': sfe_errors, # Count of questions flagged as SFE within this skill group
            'is_y_sfe': is_y_sfe,
            'question_type': question_type # Store the type for context
        }

    # Apply Macro Override Rules (Y-agg / Z-agg)
    macro_trigger_threshold = 3
    if len(reading_y_skills) + len(reading_z_skills) >= macro_trigger_threshold:
         analysis['macro_override_reading']['triggered'] = True
         analysis['macro_override_reading']['reason'] = f">= {macro_trigger_threshold} Reading/Understanding skills are Weak (Y) or Insufficiently Covered (Z)."
         analysis['macro_override_reading']['skills_involved'] = reading_y_skills + reading_z_skills

    if len(logic_etc_y_skills) + len(logic_etc_z_skills) >= macro_trigger_threshold:
        analysis['macro_override_logic_grammar_inference']['triggered'] = True
        analysis['macro_override_logic_grammar_inference']['reason'] = f">= {macro_trigger_threshold} Logic/Grammar/Inference skills are Weak (Y) or Insufficiently Covered (Z)."
        analysis['macro_override_logic_grammar_inference']['skills_involved'] = logic_etc_y_skills + logic_etc_z_skills

    # Ensure exempted list is unique (already passed in, ensure it's a set internally?)
    # analysis['exempted_skills_x'] = list(set(analysis['exempted_skills_x'])) # Already unique list

    return analysis


def _observe_patterns(df_v, v_time_pressure_status):
    """Observes patterns and behavioral indicators for Chapter 5."""
    analysis = {
        'early_rushing_questions_indices': [],
        'early_rushing_flag_for_review': False,
        'fast_wrong_rate': None, # Based on is_relatively_fast (0.75*avg)
        'carelessness_issue': False, # Based on fast_wrong_rate > 0.25
        'param_triggers': [] # To store triggered behavioral params
    }
    if df_v.empty:
        return analysis

    total_questions = len(df_v)
    analysis['early_rushing_questions_indices'] = []

    # 1. Early Rushing Risk
    if 'question_position' in df_v.columns and 'question_time' in df_v.columns:
        early_pos_limit = total_questions / 3 if total_questions > 0 else 0
        early_rush_mask = (
            (df_v['question_position'] <= early_pos_limit) &
            (df_v['question_time'] < 1.0)
        )
        early_rushing_indices = df_v[early_rush_mask].index.tolist()
        if early_rushing_indices:
            analysis['early_rushing_questions_indices'] = early_rushing_indices
            analysis['early_rushing_flag_for_review'] = True
            analysis['param_triggers'].append('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')

    # 2. Carelessness Issue
    if 'is_relatively_fast' in df_v.columns and 'is_correct' in df_v.columns:
        fast_mask = df_v['is_relatively_fast'] == True
        num_relatively_fast_total = fast_mask.sum()
        num_relatively_fast_incorrect = (fast_mask & (df_v['is_correct'] == False)).sum()

        if num_relatively_fast_total > 0:
            fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
            analysis['fast_wrong_rate'] = fast_wrong_rate
            if fast_wrong_rate > 0.25:
                analysis['carelessness_issue'] = True
                analysis['param_triggers'].append('BEHAVIOR_CARELESSNESS_ISSUE')

    return analysis

def _analyze_correct_slow(df_correct, question_type):
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
        return analysis

    slow_correct_df = df_correct[df_correct['overtime'] == True].copy()
    correct_slow_count = len(slow_correct_df)
    analysis['correct_slow_count'] = correct_slow_count

    if total_correct > 0:
        analysis['correct_slow_rate'] = correct_slow_count / total_correct

    if correct_slow_count > 0:
        slow_correct_df.reset_index(drop=True, inplace=True)

        if 'question_difficulty' in slow_correct_df.columns:
            analysis['avg_difficulty_slow'] = slow_correct_df['question_difficulty'].mean()
        analysis['avg_time_slow'] = slow_correct_df['question_time'].mean()

        if 'question_fundamental_skill' in slow_correct_df.columns:
            skill_to_category = V_SKILL_TO_ERROR_CATEGORY.copy()
            skill_to_category['Unknown Skill'] = 'Unknown'
            slow_correct_df['error_category'] = slow_correct_df['question_fundamental_skill'].map(skill_to_category).fillna('Unknown')
            category_counts_slow = slow_correct_df['error_category'].value_counts()

            reading_slow = category_counts_slow.get('Reading/Understanding', 0)
            logic_grammar_inference_slow = (category_counts_slow.get('Logic/Reasoning', 0) +
                                            category_counts_slow.get('Inference/Application', 0))

            if reading_slow > logic_grammar_inference_slow and reading_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Reading/Understanding'
            elif logic_grammar_inference_slow > reading_slow and logic_grammar_inference_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Logic/Reasoning'
            else:
                analysis['dominant_bottleneck_type'] = 'Mixed/Unclear'

            analysis['skill_breakdown_slow'] = slow_correct_df['question_fundamental_skill'].value_counts().to_dict()
        else:
            analysis['dominant_bottleneck_type'] = 'Skill data missing'

    return analysis

# Note: Kept unused function as requested in previous prompt refinement.
def _analyze_error_types(df_errors, question_type):
    """Analyzes error types for V questions of a specific type."""
    results = {
        'total_errors': len(df_errors),
        'error_records': [],
        'error_type_counts': {}
    }
    if df_errors.empty:
        return results

    error_records = []
    for index, row in df_errors.iterrows():
        q_position = row['question_position']
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        is_overtime = row.get('overtime', False)
        is_suspicious_fast = row.get('suspiciously_fast', False)

        # Determine time performance category
        if is_overtime:
            time_perf = 'Slow & Wrong'
        elif is_suspicious_fast:
            time_perf = 'Fast & Wrong'
        else:
            time_perf = 'Normal Time & Wrong'

        # Map skill to broader category using V_SKILL_TO_ERROR_CATEGORY mapping
        error_category = V_SKILL_TO_ERROR_CATEGORY.get(q_skill, 'Unknown')

        error_record = {
            'question_position': q_position,
            'question_skill': q_skill,
            'question_difficulty': q_diff,
            'time': q_time,
            'is_overtime': is_overtime,
            'time_performance': time_perf,
            'error_category': error_category
        }
        error_records.append(error_record)

        # Count errors by category
        results['error_type_counts'][error_category] = results['error_type_counts'].get(error_category, 0) + 1

    results['error_records'] = error_records
    return results


# Note: Kept unused function as requested in previous prompt refinement.
def _calculate_first_third_averages(df):
    """Calculates the average time per type for the first 1/3 of questions."""
    first_third_avg_time = {}
    if df.empty or 'question_position' not in df.columns or 'question_type' not in df.columns or 'question_time' not in df.columns:
        return first_third_avg_time

    total_questions = df['question_position'].max()
    if pd.isna(total_questions) or total_questions == 0: return first_third_avg_time

    first_third_limit = total_questions / 3
    df_first_third = df[df['question_position'] <= first_third_limit]

    if not df_first_third.empty:
        first_third_avg_time = df_first_third.groupby('question_type')['question_time'].mean().to_dict()

    return first_third_avg_time

# --- Main V Diagnosis Entry Point ---

# Note: Kept unused function as requested in previous prompt refinement.
def run_v_diagnosis(df_v_raw, v_time_pressure_status, v_avg_time_per_type):
    """
    DEPRECATED - Logic moved to run_v_diagnosis_processed.
    """
    time_pressure_status_map = {'V': v_time_pressure_status}
    # Assuming this import works in the actual environment
    from gmat_diagnosis_app.preprocess_helpers import suggest_invalid_questions
    df_v_preprocessed = suggest_invalid_questions(df_v_raw, time_pressure_status_map)
    return run_v_diagnosis_processed(df_v_preprocessed, v_time_pressure_status, v_avg_time_per_type)


def run_v_diagnosis_processed(df_v_processed, v_time_pressure_status, v_avg_time_per_type):
    """
    Runs the diagnostic analysis for Verbal using a preprocessed DataFrame.
    """
    print("  Running Verbal Diagnosis...")
    v_diagnosis_results = {}

    if df_v_processed.empty:
        print("    No V data provided. Skipping V diagnosis.")
        return {}, "Verbal (V) 部分無數據可供診斷。", pd.DataFrame()

    df_v = df_v_processed.copy()

    # --- Initialize/Prepare Columns ---
    required_cols = ['question_position', 'question_time', 'is_correct', 'question_type', 'question_fundamental_skill']
    if 'question_fundamental_skill' not in df_v.columns: df_v['question_fundamental_skill'] = 'Unknown Skill'
    if 'is_correct' not in df_v.columns: df_v['is_correct'] = True # Assume correct if missing

    df_v['question_time'] = pd.to_numeric(df_v['question_time'], errors='coerce')
    df_v['question_position'] = pd.to_numeric(df_v['question_position'], errors='coerce')
    df_v['is_correct'] = df_v['is_correct'].astype(bool)

    if 'is_invalid' not in df_v.columns: df_v['is_invalid'] = False

    # Initialize diagnostic columns
    if 'diagnostic_params' not in df_v.columns:
        df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    else:
        df_v['diagnostic_params'] = df_v['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x]))

    for col in ['overtime', 'suspiciously_fast', 'is_sfe', 'is_relatively_fast']:
        if col not in df_v.columns: df_v[col] = False
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''


    # --- Add Tag based on FINAL 'is_invalid' status ---
    final_invalid_mask_v = df_v['is_invalid']
    if final_invalid_mask_v.any():
        for idx in df_v.index[final_invalid_mask_v]:
            current_list = df_v.loc[idx, 'diagnostic_params']
            if not isinstance(current_list, list): current_list = []
            if INVALID_DATA_TAG_V not in current_list: current_list.append(INVALID_DATA_TAG_V)
            df_v.loc[idx, 'diagnostic_params'] = current_list

    num_invalid_v_total = df_v['is_invalid'].sum()
    v_diagnosis_results['invalid_count'] = num_invalid_v_total

    # --- Filter out invalid data ---
    df_v_processed_full = df_v.copy() # Store potentially modified df before filtering valid
    df_v_valid = df_v[~df_v['is_invalid']].copy()

    if df_v_valid.empty:
        print("    No V data remaining after excluding invalid entries. Skipping further V diagnosis.")
        minimal_report = _generate_v_summary_report(v_diagnosis_results)
        return v_diagnosis_results, minimal_report, df_v_processed_full # Return the df with invalid tags

    # --- Chapter 1 Global Rule: Mark Suspiciously Fast ---
    if 'suspiciously_fast' not in df_v.columns: df_v['suspiciously_fast'] = False
    for q_type, avg_time in v_avg_time_per_type.items():
        if avg_time is not None and avg_time > 0 and 'question_time' in df_v.columns:
             valid_time_mask = df_v['question_time'].notna()
             not_invalid_mask = ~df_v['is_invalid']
             suspicious_mask = (df_v['question_type'] == q_type) & \
                               (df_v['question_time'] < (avg_time * 0.5)) & \
                               valid_time_mask & \
                               not_invalid_mask
             df_v.loc[suspicious_mask, 'suspiciously_fast'] = True


    # --- Apply Chapter 3 Diagnostic Rules ---
    df_correct_v = df_v_valid[df_v_valid['is_correct'] == True].copy()
    max_correct_difficulty_per_skill_v = {}
    if not df_correct_v.empty and 'question_fundamental_skill' in df_correct_v.columns and 'question_difficulty' in df_correct_v.columns:
        if pd.api.types.is_numeric_dtype(df_correct_v['question_difficulty']):
            df_correct_v_skill_valid = df_correct_v.dropna(subset=['question_fundamental_skill'])
            if not df_correct_v_skill_valid.empty:
                 max_correct_difficulty_per_skill_v = df_correct_v_skill_valid.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # Apply rules - modifies df_v in place
    df_v = _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill_v, v_avg_time_per_type)

    # --- Translate diagnostic codes ---
    if 'diagnostic_params' in df_v.columns:
        df_v['diagnostic_params_list'] = df_v['diagnostic_params'].apply(
            lambda params: [_translate_v(p) for p in params] if isinstance(params, list) else []
        )
    else:
        num_rows = len(df_v)
        df_v['diagnostic_params_list'] = pd.Series([[] for _ in range(num_rows)], index=df_v.index)

    # --- Initialize results dictionary ---
    v_diagnosis_results = {} # Reset results based on valid data processing

    # --- Populate Chapter 1 Results ---
    v_diagnosis_results['chapter_1'] = {
        'time_pressure_status': v_time_pressure_status,
        'invalid_questions_excluded': num_invalid_v_total
    }
    print("  Populated Chapter 1 V results.")

    # --- Populate Chapter 2 Results (Basic Metrics on VALID data) ---
    print("  Executing V Analysis (Chapter 2 - Metrics)...")
    # Recalculate valid df based on potentially modified df_v's is_invalid column
    df_valid_v = df_v[~df_v['is_invalid']].copy() # Use the latest df_v

    v_diagnosis_results.setdefault('chapter_2', {})['overall_metrics'] = _calculate_metrics_for_group(df_valid_v)
    v_diagnosis_results.setdefault('chapter_2', {})['by_type'] = _analyze_dimension(df_valid_v, 'question_type')
    # Ensure difficulty grading happens on the valid data for Ch2 analysis
    df_valid_v['difficulty_grade'] = df_valid_v['question_difficulty'].apply(_grade_difficulty_v)
    v_diagnosis_results.setdefault('chapter_2', {})['by_difficulty'] = _analyze_dimension(df_valid_v, 'difficulty_grade')
    print("    Finished Chapter 2 V metrics.")

    # --- Populate Chapter 3 Results ---
    print("  Structuring V Analysis Results (Chapter 3)...")
    # Store the dataframe WITH BOTH param columns for report generator
    v_diagnosis_results['chapter_3'] = {'diagnosed_dataframe': df_v.copy()}
    print("    Finished Chapter 3 V result structuring.")

    # --- Populate Chapter 4 Results (Correct but Slow on VALID data) ---
    print("  Executing V Analysis (Chapter 4 - Correct Slow)...")
    df_correct_v = df_valid_v[df_valid_v['is_correct'] == True].copy() # Use valid data
    v_diagnosis_results['chapter_4'] = {
        'cr_correct_slow': _analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'CR'], 'CR'),
        'rc_correct_slow': _analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'RC'], 'RC')
    }
    print("    Finished Chapter 4 V correct slow analysis.")

    # --- Populate Chapter 5 Results (Patterns on VALID data) ---
    print("  Executing V Analysis (Chapter 5 - Patterns)...")
    v_diagnosis_results['chapter_5'] = _observe_patterns(df_valid_v, v_time_pressure_status)
    print("    Finished Chapter 5 V pattern observation.")

    # --- Populate Chapter 6 Results (Skill Override & Exemption on VALID data) --- #
    print("  Executing V Analysis (Chapter 6 - Skill Exemption & Override)...")
    exempted_skills = _calculate_skill_exemption_status(df_valid_v)
    ch6_override_results = _calculate_skill_override(df_valid_v)
    ch6_results = {**ch6_override_results, 'exempted_skills': exempted_skills}
    v_diagnosis_results['chapter_6'] = ch6_results
    print(f"    Finished Chapter 6 V skill override/exemption analysis. Exempted: {exempted_skills}")

    # --- Generate Recommendations & Summary Report (Chapter 7 & 8) --- #
    v_recommendations = _generate_v_recommendations(v_diagnosis_results, exempted_skills)
    v_diagnosis_results['chapter_7'] = v_recommendations

    # Generate report using results containing the df with both param columns
    v_report_content = _generate_v_summary_report(v_diagnosis_results)

    # --- Drop English column AFTER report is generated ---
    if 'diagnostic_params' in df_v.columns:
        try:
            df_v.drop(columns=['diagnostic_params'], inplace=True)
        except KeyError:
            pass

    # --- Ensure Subject Column ---
    if 'Subject' not in df_v.columns or df_v['Subject'].isnull().any() or (df_v['Subject'] != 'V').any():
        df_v['Subject'] = 'V'

    print("  Verbal Diagnosis Complete.")

    return v_diagnosis_results, v_report_content, df_v


# --- V Appendix A Translation ---
APPENDIX_A_TRANSLATION_V = {
    # --- V-Doc Appendix A Parameters (Strictly Matched) ---
    'CR_READING_BASIC_OMISSION': "CR 閱讀理解: 基礎理解疏漏",
    'CR_READING_DIFFICULTY_STEM': "CR 閱讀理解: 題幹理解障礙 (關鍵詞/句式/邏輯/領域)",
    'CR_READING_TIME_EXCESSIVE': "CR 閱讀理解: 閱讀耗時過長",
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': "CR 題目理解: 提問要求把握錯誤",
    'CR_REASONING_CHAIN_ERROR': "CR 推理障礙: 邏輯鏈分析錯誤 (前提/結論/關係)",
    'CR_REASONING_ABSTRACTION_DIFFICULTY': "CR 推理障礙: 抽象邏輯/術語理解困難",
    'CR_REASONING_PREDICTION_ERROR': "CR 推理障礙: 預判方向錯誤或缺失",
    'CR_REASONING_TIME_EXCESSIVE': "CR 推理障礙: 邏輯思考耗時過長",
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': "CR 推理障礙: 核心議題識別困難",
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': "CR 選項辨析: 選項本身理解困難",
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': "CR 選項辨析: 選項相關性判斷錯誤",
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': "CR 選項辨析: 強干擾選項混淆",
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': "CR 選項辨析: 選項篩選耗時過長",
    'CR_METHOD_PROCESS_DEVIATION': "CR 方法應用: 未遵循標準流程",
    'CR_METHOD_TYPE_SPECIFIC_ERROR': "CR 方法應用: 特定題型方法錯誤/不熟 (需註明題型)",
    'RC_READING_INFO_LOCATION_ERROR': "RC 閱讀理解: 關鍵信息定位/理解錯誤",
    'RC_READING_KEYWORD_LOGIC_OMISSION': "RC 閱讀理解: 忽略關鍵詞/邏輯",
    'RC_READING_VOCAB_BOTTLENECK': "RC 閱讀理解: 詞彙量瓶頸",
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': "RC 閱讀理解: 長難句解析困難",
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': "RC 閱讀理解: 篇章結構把握不清",
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': "RC 閱讀理解: 特定領域背景知識缺乏",
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': "RC 閱讀理解: 閱讀速度慢 (基礎問題)",
    'RC_READING_PRECISION_INSUFFICIENT': "RC 閱讀精度不足 (精讀/定位問題)",
    'RC_READING_COMPREHENSION_BARRIER': "RC 閱讀理解: 閱讀理解障礙 (耗時過長觸發)",
    'RC_METHOD_INEFFICIENT_READING': "RC 閱讀方法: 閱讀方法效率低 (過度精讀)",
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': "RC 題目理解: 提問焦點把握錯誤",
    'RC_LOCATION_ERROR_INEFFICIENCY': "RC 定位能力: 定位錯誤/效率低下",
    'RC_LOCATION_TIME_EXCESSIVE': "RC 定位能力: 定位效率低下 (反覆定位)",
    'RC_REASONING_INFERENCE_WEAKNESS': "RC 推理障礙: 推理能力不足 (預判/細節/語氣)",
    'RC_REASONING_TIME_EXCESSIVE': "RC 推理障礙: 深度思考耗時過長",
    'RC_AC_ANALYSIS_DIFFICULTY': "RC 選項辨析: 選項理解/辨析困難 (含義/對應)",
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': "RC 選項辨析: 選項篩選耗時過長",
    'RC_METHOD_TYPE_SPECIFIC_ERROR': "RC方法：特定題型（需回憶或二級證據釐清）",
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "基礎掌握: 應用不穩定 (Special Focus Error)",
    'EFFICIENCY_BOTTLENECK_READING': "效率問題: 閱讀理解環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_REASONING': "效率問題: 推理分析環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_LOCATION': "效率問題: 信息定位環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': "效率問題: 選項辨析環節導致效率低下",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    'BEHAVIOR_GUESSING_HASTY': "行為模式: 過快疑似猜題/倉促",

    # --- VDOC Defined Core Fundamental Skills ---
    'Plan/Construct': "計劃/構建",
    'Identify Stated Idea': "識別陳述信息",
    'Identify Inferred Idea': "識別推斷信息",
    'Analysis/Critique': "分析/批判",

    # --- Internal Codes ---
    "Low / 505+": "低難度 (Low) / 505+",
    "Mid / 555+": "中難度 (Mid) / 555+",
    "Mid / 605+": "中難度 (Mid) / 605+",
    "Mid / 655+": "中難度 (Mid) / 655+",
    "High / 705+": "高難度 (High) / 705+",
    "High / 805+": "高難度 (High) / 805+",
    "Unknown Difficulty": "未知難度",
    'Unknown Skill': "未知技能",
    'Y': "薄弱技能",
    'Y-SFE': "薄弱技能 (高 SFE)",
    'Z': "考察不足",
    'X': "基本掌握 (豁免)",
    'OK': "表現正常",
    'High': "高",
    'Low': "低",
    'Unknown': "未知", # Also used as a Category name
    'Reading/Understanding': "閱讀理解",
    'Logic/Reasoning': "邏輯推理",
    'Inference/Application': "推理應用",
    'Method/Process': "方法/流程",
    'Behavioral': "行為模式", # Also used as a Category name
    'Mixed/Other': "混合/其他",
    'N/A': '不適用',
    'Fast & Wrong': "快錯",
    'Slow & Wrong': "慢錯",
    'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對",
    'Fast & Correct': "快對",
    'Normal Time & Correct': "正常時間 & 對",
    'SFE': '基礎掌握', # Category name
    'Reading': '閱讀理解', # Category name
    'Reasoning': '邏輯推理', # Category name
    'Timing': '時間管理', # Category name
    'Process': '流程方法', # Category name
    'AC_Analysis': '選項分析', # Category name
    'Question_Understanding': '問題理解', # Category name
    INVALID_DATA_TAG_V: INVALID_DATA_TAG_V # Map invalid tag to itself if needed
}

def _translate_v(param):
    """Translates an internal V param/skill name to a Mandarin display string."""
    if param is None:
        return "未知參數"
    if not isinstance(param, str):
        if isinstance(param, list):
            return [_translate_v(p) for p in param]
        return str(param)

    # Use the main APPENDIX_A_TRANSLATION_V dictionary directly
    return APPENDIX_A_TRANSLATION_V.get(param, param) # Return original if not found

# --- V Summary Report Generation Helper ---

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)) and not pd.isna(rate_value):
        return f"{rate_value:.1%}"
    else:
        return 'N/A'

def _generate_v_summary_report(v_diagnosis_results):
    """Generates the summary report string for the Verbal section."""
    report_lines = []
    report_lines.append("---（基於用戶數據與模擬難度分析）---")
    report_lines.append("")

    # Extract chapters safely
    ch1 = v_diagnosis_results.get('chapter_1', {})
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    ch7 = v_diagnosis_results.get('chapter_7', [])

    # --- Section 1: 時間策略與有效性 ---
    report_lines.append("**1. 時間策略與有效性**")
    time_pressure_detected = ch1.get('time_pressure_status', False)
    invalid_count = ch1.get('invalid_questions_excluded', 0)

    if time_pressure_detected:
        report_lines.append("- 根據分析，您在語文部分可能處於**時間壓力**下（測驗時間剩餘不多或末尾部分題目作答過快）。")
    else:
        report_lines.append("- 根據分析，您在語文部分未處於明顯的時間壓力下。")

    if invalid_count > 0:
        report_lines.append(f"- 已將 {invalid_count} 道可能因時間壓力影響有效性的題目從詳細分析中排除，以確保診斷準確性。")
        report_lines.append("- 請注意，這些被排除的題目將不會包含在後續的錯誤難度分佈統計和練習建議中。")
    else:
        report_lines.append("- 所有題目數據均被納入詳細分析。")
    report_lines.append("")

    # --- Section 2: 表現概覽 ---
    report_lines.append("**2. 表現概覽（CR vs RC）**")
    chapter_2_results = v_diagnosis_results.get('chapter_2', {})
    v_metrics_by_type = chapter_2_results.get('by_type', {})
    cr_metrics = v_metrics_by_type.get('Critical Reasoning', v_metrics_by_type.get('CR', {}))
    rc_metrics = v_metrics_by_type.get('Reading Comprehension', v_metrics_by_type.get('RC', {}))

    cr_error_rate = cr_metrics.get('error_rate')
    cr_overtime_rate = cr_metrics.get('overtime_rate')
    rc_error_rate = rc_metrics.get('error_rate')
    rc_overtime_rate = rc_metrics.get('overtime_rate')

    cr_data_valid = cr_metrics and pd.notna(cr_error_rate) and pd.notna(cr_overtime_rate)
    rc_data_valid = rc_metrics and pd.notna(rc_error_rate) and pd.notna(rc_overtime_rate)

    if cr_data_valid and rc_data_valid:
        cr_total = cr_metrics.get('total_questions', 0)
        rc_total = rc_metrics.get('total_questions', 0)
        report_lines.append(f"- CR（{cr_total} 題）：錯誤率 {_format_rate(cr_error_rate)}，超時率 {_format_rate(cr_overtime_rate)}")
        report_lines.append(f"- RC（{rc_total} 題）：錯誤率 {_format_rate(rc_error_rate)}，超時率 {_format_rate(rc_overtime_rate)}")
        error_diff = abs(cr_error_rate - rc_error_rate)
        overtime_diff = abs(cr_overtime_rate - rc_overtime_rate)
        significant_error = error_diff >= 0.15
        significant_overtime = overtime_diff >= 0.15
        if significant_error or significant_overtime:
            if significant_error:
                report_lines.append(f"  - **錯誤率對比：** {'CR 更高' if cr_error_rate > rc_error_rate else 'RC 更高'}（差異 {_format_rate(error_diff)}）")
            if significant_overtime:
                report_lines.append(f"  - **超時率對比：** {'CR 更高' if cr_overtime_rate > rc_overtime_rate else 'RC 更高'}（差異 {_format_rate(overtime_diff)}）")
        else:
            report_lines.append("  - CR 與 RC 在錯誤率和超時率上表現相當，無顯著差異。")
    elif not cr_data_valid and not rc_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 CR 和 RC 數據，無法進行比較。")
    elif not cr_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 CR 數據，無法進行比較。")
        if rc_data_valid:
             rc_total = rc_metrics.get('total_questions', 0)
             report_lines.append(f"  - （RC（{rc_total} 題）：錯誤率 {_format_rate(rc_error_rate)}，超時率 {_format_rate(rc_overtime_rate)}）")
    elif not rc_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 RC 數據，無法進行比較。")
        if cr_data_valid:
             cr_total = cr_metrics.get('total_questions', 0)
             report_lines.append(f"  - （CR（{cr_total} 題）：錯誤率 {_format_rate(cr_error_rate)}，超時率 {_format_rate(cr_overtime_rate)}）")
    report_lines.append("")

    # --- Section 3: 核心問題診斷 ---
    report_lines.append("**3. 核心問題診斷（基於觸發的診斷標籤）**")
    diagnosed_df_ch3_raw = ch3.get('diagnosed_dataframe') # Use the stored df
    sfe_triggered_overall = False
    sfe_skills_involved = set()
    triggered_params_all = set() # English codes
    qualitative_analysis_trigger = False
    secondary_evidence_trigger = False # Renamed from qualitative for clarity

    # Populate triggered_params_all from the stored English codes (before drop)
    if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
        english_param_lists = diagnosed_df_ch3_raw['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])
        triggered_params_all.update(p for sublist in english_param_lists for p in sublist if isinstance(p, str))
    if ch5:
        triggered_params_all.update(ch5.get('param_triggers', []))

    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        for index, row in diagnosed_df_ch3_raw.iterrows():
            is_sfe = row.get('is_sfe', False)
            if is_sfe:
                sfe_triggered_overall = True
                skill = row.get('question_fundamental_skill', 'Unknown Skill')
                if skill != 'Unknown Skill':
                    sfe_skills_involved.add(skill)
                secondary_evidence_trigger = True # SFE warrants review

            # Check for qualitative analysis trigger conditions
            time_cat = row.get('time_performance_category', 'Unknown')
            if time_cat in ['Normal Time & Wrong', 'Slow & Wrong', 'Slow & Correct']:
                secondary_evidence_trigger = True # These also warrant review
                current_english_params = set(row.get('diagnostic_params', [])) if isinstance(row.get('diagnostic_params', []), list) else set()
                complex_params = {
                    'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                    'RC_REASONING_INFERENCE_WEAKNESS'
                }
                if any(p in complex_params for p in current_english_params):
                    qualitative_analysis_trigger = True # Specific trigger for qualitative
                if time_cat == 'Slow & Correct':
                    qualitative_analysis_trigger = True # Also trigger qualitative

    # Report SFE Summary
    if sfe_triggered_overall:
        sfe_label = _translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        sfe_skills_en = sorted(list(sfe_skills_involved))
        sfe_note = f"{sfe_label}" + (f"（涉及技能：{', '.join(sfe_skills_en)}）" if sfe_skills_en else "")
        report_lines.append(f"- **尤其需要注意：** {sfe_note}。（註：SFE 指在已掌握技能範圍內的題目失誤）")

    core_issues_params = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'}
    if not core_issues_params and not sfe_triggered_overall:
        report_lines.append("- 未識別出明顯的核心問題模式（基於錯誤及效率分析）。")
    report_lines.append("")

    # --- Section 4: 正確但低效分析 ---
    report_lines.append("**4. 正確但低效分析**")
    cr_slow_correct = ch4.get('cr_correct_slow', {})
    rc_slow_correct = ch4.get('rc_correct_slow', {})
    slow_correct_found = False
    for slow_data, type_name in [(cr_slow_correct, "CR"), (rc_slow_correct, "RC")]:
        if slow_data and slow_data.get('correct_slow_count', 0) > 0:
            count = slow_data['correct_slow_count']
            rate = _format_rate(slow_data.get('correct_slow_rate', 'N/A'))
            avg_diff_val = slow_data.get('avg_difficulty_slow', None)
            avg_time_val = slow_data.get('avg_time_slow', None)
            avg_diff = f"{avg_diff_val:.2f}" if avg_diff_val is not None else 'N/A'
            avg_time = f"{avg_time_val:.2f}" if avg_time_val is not None else 'N/A'
            bottleneck = _translate_v(slow_data.get('dominant_bottleneck_type', 'N/A'))
            report_lines.append(f"- {type_name}：{count} 題正確但慢（佔比 {rate}）。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。主要瓶頸：{bottleneck}。")
            slow_correct_found = True
    if not slow_correct_found:
        report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 作答模式觀察 ---
    report_lines.append("**5. 作答模式觀察**")
    early_rushing_flag = bool(ch5.get('early_rushing_flag_for_review', False))
    carelessness_issue = bool(ch5.get('carelessness_issue', False))
    fast_wrong_rate = ch5.get('fast_wrong_rate')
    pattern_found = False
    if early_rushing_flag:
         early_rush_param_translated = _translate_v('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
         report_lines.append(f"- **提示：** {early_rush_param_translated} - 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏。")
         pattern_found = True
    if carelessness_issue:
        careless_param_translated = _translate_v('BEHAVIOR_CARELESSNESS_ISSUE')
        fast_wrong_rate_str = _format_rate(fast_wrong_rate) if fast_wrong_rate is not None else "N/A"
        report_lines.append(f"- **提示：** {careless_param_translated} - 分析顯示，「快而錯」的情況佔比較高（{fast_wrong_rate_str}），提示可能需關注答題仔細程度。")
        pattern_found = True
    if not pattern_found:
        report_lines.append("- 未發現明顯的特殊作答模式。")
    report_lines.append("")

    # --- Section 6: 基礎鞏固提示 ---
    report_lines.append("**6. 基礎鞏固提示**")
    override_triggered = ch6.get('skill_override_triggered', {})
    triggered_skills = [s for s, triggered in override_triggered.items() if bool(triggered)]
    if not override_triggered: # Check if dictionary itself exists/is populated
         report_lines.append("- 無法進行技能覆蓋分析（可能缺少數據或計算錯誤）。")
    elif triggered_skills:
        triggered_skills_en = sorted(triggered_skills)
        report_lines.append(f"- **以下核心技能整體表現顯示較大提升空間（錯誤率 > 50%），建議優先系統性鞏固：** {', '.join(triggered_skills_en)}")
    else:
        report_lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    report_lines.append("")

    # --- Section 7: 練習計劃呈現 ---
    report_lines.append("**7. 練習計劃**")
    if ch7:
        for rec in ch7:
             rec_type = rec.get('type')
             rec_text = rec.get('text', '')
             if rec_type in ['skill_header', 'spacer']:
                 report_lines.append(rec_text)
             elif rec_type in ['macro', 'case', 'case_aggregated', 'behavioral']:
                 report_lines.append(f"- {rec_text}")
    else:
        report_lines.append("- 無具體練習建議生成（可能因所有技能均豁免或無觸發項）。")
    report_lines.append("")

    # --- Section 8: 後續行動指引 ---
    report_lines.append("**8. 後續行動指引**")

    # Data Prep for Mapping (needs English codes)
    param_to_positions_v = {}
    skill_to_positions_v = {}
    v_translation_dict = APPENDIX_A_TRANSLATION_V

    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
         param_col_eng = 'diagnostic_params'
         if param_col_eng in diagnosed_df_ch3_raw.columns:
             for index, row in diagnosed_df_ch3_raw.iterrows():
                 pos = row.get('question_position')
                 skill = row.get('question_fundamental_skill', 'Unknown Skill')
                 eng_params = row.get(param_col_eng, [])
                 if not isinstance(eng_params, list): eng_params = []

                 if pos is not None and pos != 'N/A':
                     pos = int(pos) # Ensure positions are integers for sorting
                     if skill != 'Unknown Skill':
                         skill_to_positions_v.setdefault(skill, set()).add(pos)
                     for p in eng_params:
                         if isinstance(p, str):
                             param_to_positions_v.setdefault(p, set()).add(pos)
             # Convert sets to sorted lists
             for param in param_to_positions_v: param_to_positions_v[param] = sorted(list(param_to_positions_v[param]))
             for skill in skill_to_positions_v: skill_to_positions_v[skill] = sorted(list(skill_to_positions_v[skill]))

    # 8.1 Reflection Prompts
    report_lines.append("- **引導反思：**")
    reflection_prompts_v = []

    # Local helpers for context
    def get_pos_context_v(param_keys):
        positions = set().union(*(param_to_positions_v.get(key, set()) for key in param_keys if isinstance(key, str)))
        return f"（涉及題號：{sorted(list(positions))}）" if positions else ""

    def get_relevant_skills_v(param_keys):
        relevant_positions = set().union(*(param_to_positions_v.get(key, set()) for key in param_keys if isinstance(key, str)))
        relevant_skills_set = {skill for skill, positions in skill_to_positions_v.items() if not relevant_positions.isdisjoint(positions)}
        return sorted(list(relevant_skills_set))

    # Parameter Groups
    cr_reading_params = ['CR_READING_BASIC_OMISSION', 'CR_READING_DIFFICULTY_STEM', 'CR_READING_TIME_EXCESSIVE']
    cr_reasoning_params = ['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY', 'CR_REASONING_ABSTRACTION_DIFFICULTY', 'CR_REASONING_PREDICTION_ERROR', 'CR_REASONING_TIME_EXCESSIVE']
    cr_ac_params = ['CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY', 'CR_AC_ANALYSIS_RELEVANCE_ERROR', 'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION', 'CR_AC_ANALYSIS_TIME_EXCESSIVE']
    cr_method_params = ['CR_METHOD_TYPE_SPECIFIC_ERROR', 'CR_METHOD_PROCESS_DEVIATION']
    rc_reading_params = ['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_READING_COMPREHENSION_BARRIER', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP', 'RC_READING_VOCAB_BOTTLENECK', 'RC_READING_PRECISION_INSUFFICIENT', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY', 'RC_READING_INFO_LOCATION_ERROR', 'RC_READING_KEYWORD_LOGIC_OMISSION']
    rc_location_params = ['RC_LOCATION_ERROR_INEFFICIENCY', 'RC_LOCATION_TIME_EXCESSIVE']
    rc_reasoning_params = ['RC_REASONING_INFERENCE_WEAKNESS', 'RC_REASONING_TIME_EXCESSIVE']
    rc_ac_params = ['RC_AC_ANALYSIS_DIFFICULTY', 'RC_AC_ANALYSIS_TIME_EXCESSIVE']
    rc_method_params = ['RC_METHOD_INEFFICIENT_READING', 'RC_METHOD_TYPE_SPECIFIC_ERROR']
    behavioral_params = ['BEHAVIOR_CARELESSNESS_ISSUE', 'BEHAVIOR_EARLY_RUSHING_FLAG_RISK', 'BEHAVIOR_GUESSING_HASTY']
    sfe_param = ['FOUNDATIONAL_MASTERY_INSTABILITY_SFE']

    # Generate prompts based on triggered parameters
    prompt_groups = [
        (cr_reading_params, "回想 CR 題幹閱讀時，是耗時過長，還是對句子/詞彙理解有偏差？"),
        (cr_reasoning_params, "在 CR 邏輯推理時，是難以識別核心問題、理清論證鏈，還是預判方向錯誤？"),
        (cr_ac_params, "分析 CR 選項時，是難以理解選項本身，判斷相關性失誤，還是容易被強干擾項混淆？"),
        (cr_method_params, "做 CR 題時，是否遵循了標準流程？對於特定題型（如BF、Assumption）的方法是否清晰？"),
        (rc_reading_params, "閱讀 RC 文章時，是基礎速度慢、詞彙/長難句障礙，還是對篇章結構把握不清？"),
        (rc_location_params + rc_reasoning_params + rc_ac_params + rc_method_params, "回答 RC 問題時，是定位耗時/錯誤，推理能力不足，選項辨析困難，還是閱讀/解題方法不當？"),
        (sfe_param, "對於 SFE 問題，回想一下是哪個基礎知識點掌握不牢固導致的失誤？"),
        (behavioral_params, "是否存在因為倉促猜題、開頭搶時間或普遍粗心導致的失誤？")
    ]

    for params_group, prompt_text in prompt_groups:
        triggered_in_group = [p for p in params_group if p in triggered_params_all]
        if triggered_in_group:
            skills = get_relevant_skills_v(triggered_in_group)
            skill_context = f" [`{', '.join(skills)}`] " if skills else " "
            reflection_prompts_v.append(f"  - {prompt_text}{skill_context}" + get_pos_context_v(triggered_in_group))

    if not reflection_prompts_v:
        reflection_prompts_v.append("  - （本次分析未觸發典型的反思問題，建議結合練習計劃進行）")
    report_lines.extend(reflection_prompts_v)


    # 8.2 Second Evidence Suggestion
    report_lines.append("- **二級證據參考建議：**")
    df_problem = pd.DataFrame()
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        filter_cols = ['is_correct', 'overtime']
        if all(col in diagnosed_df_ch3_raw.columns for col in filter_cols):
            df_problem = diagnosed_df_ch3_raw[ (diagnosed_df_ch3_raw['is_correct'] == False) | (diagnosed_df_ch3_raw.get('overtime', False) == True) ].copy()

    if not df_problem.empty:
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
        details_added_2nd_ev = False
        if 'time_performance_category' in df_problem.columns:
            performance_order_en = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct'] # Relevant categories
            df_problem['time_performance_category'] = df_problem['time_performance_category'].fillna('Unknown')
            # Ensure the column is categorical for potential ordering (though groupby handles strings)
            # df_problem['time_performance_category'] = pd.Categorical(df_problem['time_performance_category'], categories=performance_order_en + ['Unknown'], ordered=True)

            try:
                # Use observed=False if Pandas version supports it, to avoid warnings with categorical
                 grouped_by_performance = df_problem.groupby('time_performance_category', observed=False)
            except TypeError:
                 grouped_by_performance = df_problem.groupby('time_performance_category')


            for perf_en in performance_order_en:
                if perf_en in grouped_by_performance.groups:
                    group_df = grouped_by_performance.get_group(perf_en)
                    if not group_df.empty:
                        perf_zh = _translate_v(perf_en)
                        types_in_group = sorted(group_df['question_type'].dropna().unique())
                        skills_in_group = sorted(group_df['question_fundamental_skill'].dropna().unique())
                        skills_display_zh = sorted([_translate_v(s) for s in skills_in_group if s != 'Unknown Skill'])

                        # Get all unique English codes for this group
                        all_eng_codes_in_group = set()
                        param_eng_col = 'diagnostic_params'
                        if param_eng_col in group_df.columns:
                            for labels_list in group_df[param_eng_col]:
                                if isinstance(labels_list, list):
                                    all_eng_codes_in_group.update(p for p in labels_list if isinstance(p, str) and p != INVALID_DATA_TAG_V)

                        # Categorize English codes and translate for display
                        labels_by_category = {category: [] for category in V_PARAM_CATEGORY_ORDER}
                        for code_en in all_eng_codes_in_group:
                            category = V_PARAM_TO_CATEGORY.get(code_en, 'Unknown')
                            labels_by_category[category].append(code_en)

                        label_parts_data = []
                        for category in V_PARAM_CATEGORY_ORDER:
                            category_eng_codes = labels_by_category.get(category, [])
                            if category_eng_codes:
                                category_zh = _translate_v(category)
                                category_labels_zh = sorted([_translate_v(code) for code in category_eng_codes])
                                label_parts_data.append((category_zh, category_labels_zh))

                        # Format Report Lines
                        report_lines.append(f"  - **{perf_zh}:** 需關注題型：【{', '.join(types_in_group)}】；涉及技能：【{', '.join(skills_display_zh)}】。")
                        if label_parts_data:
                            report_lines.append("    注意相關問題點：")
                            for category_zh, sorted_labels_zh in label_parts_data:
                                report_lines.append(f"      - 【{category_zh}: {'、'.join(sorted_labels_zh)}】")
                        details_added_2nd_ev = True

        # Report core issues summary
        core_issue_codes_to_report = set()
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params_all:
             core_issue_codes_to_report.add('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        param_counts_v = {}
        if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
             all_param_lists_eng = [p for sublist in diagnosed_df_ch3_raw['diagnostic_params'] if isinstance(sublist, list) for p in sublist if isinstance(p, str)]
             if all_param_lists_eng: # Check if list is not empty
                 param_counts_v = pd.Series(all_param_lists_eng).value_counts()

        top_other_params_codes_v = []
        if not param_counts_v.empty:
             # Exclude SFE before taking top 2
             non_sfe_counts = param_counts_v.drop('FOUNDATIONAL_MASTERY_INSTABILITY_SFE', errors='ignore')
             top_other_params_codes_v = non_sfe_counts.head(2).index.tolist()
        core_issue_codes_to_report.update(top_other_params_codes_v)

        if core_issue_codes_to_report:
             translated_core_issues = sorted([_translate_v(code) for code in core_issue_codes_to_report if code and _translate_v(code) != INVALID_DATA_TAG_V])
             if translated_core_issues:
                 report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(translated_core_issues)}】。")
                 details_added_2nd_ev = True

        if not details_added_2nd_ev:
             report_lines.append("  - (本次分析未聚焦到特定的問題類型或技能)")
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")

    # 8.3 Qualitative Analysis Suggestion
    report_lines.append("- **質化分析建議:**")
    if qualitative_analysis_trigger:
         report_lines.append("  - *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時（尤其針對耗時過長或涉及複雜推理的題目）。")
         report_lines.append("  - *建議行動：* 可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")
    else:
         report_lines.append("  - (本次分析未觸發深入質化分析的特定建議，但若對任何問題點感到困惑，仍可採用此方法。)")

    report_lines.append("\n--- 報告結束 ---")
    return "\n".join(report_lines)


# --- V Recommendation Generation Helper ---

def _generate_v_recommendations(v_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on V diagnosis results."""
    recommendations = []
    processed_macro_skills = set()

    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe')
    skill_override_triggered = ch6.get('skill_override_triggered', {})
    all_skills_found = set()

    # Identify problem skills
    if diagnosed_df is not None and not diagnosed_df.empty and \
       all(col in diagnosed_df.columns for col in ['is_correct', 'overtime', 'question_fundamental_skill']):
        problem_mask = (diagnosed_df['is_correct'] == False) | \
                       ((diagnosed_df['is_correct'] == True) & (diagnosed_df['overtime'] == True))
        problem_skills = diagnosed_df.loc[problem_mask, 'question_fundamental_skill'].fillna('Unknown Skill').unique()
        all_skills_found = set(skill for skill in problem_skills if skill != 'Unknown Skill')

    recommendations_by_skill = {}
    for skill in all_skills_found:
        if skill in exempted_skills: continue

        skill_recs_list = []
        is_overridden = skill_override_triggered.get(skill, False)

        if is_overridden and skill not in processed_macro_skills:
            macro_rec_text = f"針對【{skill}】技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_macro_skills.add(skill)
        elif not is_overridden:
            if diagnosed_df is not None and not diagnosed_df.empty:
                diagnosed_df['question_fundamental_skill'] = diagnosed_df['question_fundamental_skill'].fillna('Unknown Skill')
                skill_problem_mask = (diagnosed_df['question_fundamental_skill'] == skill) & problem_mask
                skill_rows = diagnosed_df[skill_problem_mask]

                if not skill_rows.empty:
                    min_difficulty = skill_rows['question_difficulty'].min()
                    y_grade = _grade_difficulty_v(min_difficulty)

                    z_minutes_list = []
                    q_type_for_skill = skill_rows['question_type'].iloc[0]
                    target_time_map = {'CR': 2.0, 'RC': 1.75}
                    target_time_minutes = target_time_map.get(q_type_for_skill, 1.8)

                    for _, row in skill_rows.iterrows():
                        q_time_minutes = row['question_time']
                        if pd.notna(q_time_minutes):
                            base_time_minutes = max(0, q_time_minutes)
                            # Use np.floor instead of math.floor
                            z_raw_minutes = np.floor(base_time_minutes * 2) / 2.0
                            z = max(z_raw_minutes, target_time_minutes)
                            z_minutes_list.append(z)

                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{target_time_minutes:.1f} 分鐘"
                    group_sfe = skill_rows['is_sfe'].any()
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    case_rec_text = f"{sfe_prefix}針對【{skill}】建議練習【{y_grade}】難度題目，起始練習限時建議為【{z_text}】(最終目標時間: {target_time_text})。"

                    if max_z_minutes - target_time_minutes > 2.0:
                        case_rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    priority = 1 if group_sfe else 2
                    skill_recs_list.append({
                        'type': 'case_aggregated', 'text': case_rec_text,
                        'priority': priority, 'is_sfe': group_sfe
                    })

        if skill_recs_list:
            recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # Assemble Final List
    final_recommendations = []
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_macro_skills else 1, s))
    for skill in sorted_skills:
        if skill in recommendations_by_skill:
            recs = recommendations_by_skill[skill]
            final_recommendations.append({'type': 'skill_header', 'text': f"--- 技能: {skill} ---"})
            final_recommendations.extend(recs)
            final_recommendations.append({'type': 'spacer', 'text': ""})

    return final_recommendations


# --- Helper for Applying Chapter 3 Rules ---

def _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill, avg_time_per_type):
    """Applies Chapter 3 diagnostic rules row-by-row."""
    if df_v.empty:
        for col in ['diagnostic_params', 'is_sfe', 'is_relatively_fast', 'time_performance_category']:
            if col == 'diagnostic_params':
                df_v[col] = [[] for _ in range(len(df_v))]
            elif col == 'time_performance_category':
                df_v[col] = ''
            else:
                df_v[col] = False
        return df_v

    # Initialize columns if they don't exist
    if 'diagnostic_params' not in df_v.columns: df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    if 'is_sfe' not in df_v.columns: df_v['is_sfe'] = False
    if 'is_relatively_fast' not in df_v.columns: df_v['is_relatively_fast'] = False
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''

    max_diff_dict = max_correct_difficulty_per_skill

    all_params = []
    all_sfe = []
    all_fast_flags = []
    all_time_categories = []

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
        ('Critical Reasoning', 'Fast & Wrong'): cr_params_fast_wrong,
        ('Critical Reasoning', 'Normal Time & Wrong'): cr_params_normal_wrong,
        ('Critical Reasoning', 'Slow & Wrong'): cr_params_slow_wrong_time + cr_params_normal_wrong,
        ('Critical Reasoning', 'Slow & Correct'): cr_params_slow_correct_eff,
        ('Reading Comprehension', 'Fast & Wrong'): rc_params_fast_wrong,
        ('Reading Comprehension', 'Normal Time & Wrong'): rc_params_normal_wrong,
        ('Reading Comprehension', 'Slow & Wrong'): rc_params_slow_wrong_time + rc_params_normal_wrong,
        ('Reading Comprehension', 'Slow & Correct'): rc_params_slow_correct_eff,
    }


    for index, row in df_v.iterrows():
        q_type = row['question_type']
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime_combined = bool(row.get('overtime', False))

        current_params = []
        current_is_sfe = False
        current_is_relatively_fast = False
        current_time_performance_category = 'Unknown'

        # 1. Check SFE
        if not is_correct and q_diff is not None and not pd.isna(q_diff):
            max_correct_diff = max_diff_dict.get(q_skill, -np.inf)
            if q_diff < max_correct_diff:
                current_is_sfe = True
                current_params.append('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 2. Determine Time Flags
        is_slow = is_overtime_combined
        avg_time = avg_time_per_type.get(q_type, 1.8)
        is_normal_time = False
        if q_time is not None and not pd.isna(q_time):
            if q_time < (avg_time * 0.75):
                current_is_relatively_fast = True
            if q_time < HASTY_GUESSING_THRESHOLD_MINUTES:
                 current_params.append('BEHAVIOR_GUESSING_HASTY')
            if not current_is_relatively_fast and not is_slow:
                 is_normal_time = True

        # 3. Assign Time Performance Category
        if is_correct:
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif is_slow: current_time_performance_category = 'Slow & Correct'
            else: current_time_performance_category = 'Normal Time & Correct'
        else:
            if current_is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif is_slow: current_time_performance_category = 'Slow & Wrong'
            else: current_time_performance_category = 'Normal Time & Wrong'

        # 4. Assign DETAILED Diagnostic Params using the map
        params_to_add = param_assignment_map.get((q_type, current_time_performance_category), [])
        current_params.extend(params_to_add)

        # 5. Final Parameter List Cleanup
        unique_params = list(dict.fromkeys(current_params))
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
             unique_params.remove('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
             unique_params.insert(0, 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        all_params.append(unique_params)
        all_sfe.append(current_is_sfe)
        all_fast_flags.append(current_is_relatively_fast)
        all_time_categories.append(current_time_performance_category)

    # Assign lists back to DataFrame
    if len(all_params) == len(df_v):
        df_v['diagnostic_params'] = all_params
        df_v['is_sfe'] = all_sfe
        df_v['is_relatively_fast'] = all_fast_flags
        df_v['time_performance_category'] = all_time_categories
    # else: # Error case handled by checking length before assignment

    return df_v

# --- Helper Functions needed by Chapter 2 ---
def _calculate_metrics_for_group(group):
    """Calculates basic metrics for a given group of data."""
    total = len(group)
    errors = group['is_correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0.0
    avg_time_spent = group['question_time'].mean() if 'question_time' in group.columns else 0.0
    avg_difficulty = group['question_difficulty'].mean() if 'question_difficulty' in group.columns else None
    overtime_count = group['overtime'].eq(True).sum() if 'overtime' in group.columns else 0
    overtime_rate = overtime_count / total if total > 0 else 0.0
    return {
        'total_questions': total, 'errors': errors, 'error_rate': error_rate,
        'avg_time_spent': avg_time_spent, 'avg_difficulty': avg_difficulty,
        'overtime_count': overtime_count, 'overtime_rate': overtime_rate
    }

def _analyze_dimension(df_filtered, dimension_col):
    """Analyzes performance metrics grouped by a specific dimension column."""
    if df_filtered.empty or dimension_col not in df_filtered.columns:
        return {}
    results = {}
    df_filtered[dimension_col] = df_filtered[dimension_col].fillna('Unknown')
    grouped = df_filtered.groupby(dimension_col)
    for name, group in grouped:
        results[name] = _calculate_metrics_for_group(group)
    return results

# --- Helper function for Chapter 6 Override Rule ---
def _calculate_skill_override(df_v):
    """Calculates the skill override trigger based on V-Doc Chapter 6."""
    analysis = {'skill_error_rates': {}, 'skill_override_triggered': {}}
    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        return analysis
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    skill_groups = df_v.groupby('question_fundamental_skill')
    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue
        total = len(group)
        errors = group['is_correct'].eq(False).sum()
        error_rate = errors / total if total > 0 else 0.0
        analysis['skill_error_rates'][skill] = error_rate
        analysis['skill_override_triggered'][skill] = error_rate > 0.50
    return analysis

def _grade_difficulty_v(difficulty):
    """Grades the difficulty of a question based on V-Doc Chapter 2/7 rules."""
    if difficulty is None or pd.isna(difficulty): return "Unknown Difficulty"
    if difficulty <= -1: return "Low / 505+"
    if -1 < difficulty <= 0: return "Mid / 555+"
    if 0 < difficulty <= 1: return "Mid / 605+"
    if 1 < difficulty <= 1.5: return "Mid / 655+"
    if 1.5 < difficulty <= 1.95: return "High / 705+"
    if 1.95 < difficulty <= 2: return "High / 805+"
    return "Unknown Difficulty" # Default for values outside expected range

# --- Helper function for Chapter 6 Exemption Rule ---
def _calculate_skill_exemption_status(df_v):
    """Calculates the set of exempted skills based on V-Doc Chapter 6."""
    exempted_skills = set()
    if df_v.empty or not all(col in df_v.columns for col in ['question_fundamental_skill', 'is_correct', 'overtime']):
        return exempted_skills
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    skill_groups = df_v.groupby('question_fundamental_skill')
    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue
        if group['is_correct'].all() and not group['overtime'].any():
            exempted_skills.add(skill)
    return exempted_skills