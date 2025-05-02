import pandas as pd
import numpy as np
import math # For floor function

# --- V-Specific Constants (Add as needed) ---
# Example: Define time thresholds if needed later
# CR_AVG_TIME_THRESHOLD = 2.0 # minutes
# RC_AVG_TIME_THRESHOLD_PER_Q = 1.75 # minutes (assuming reading time is separate or amortized)

# Chapter 1 Constants (from V-Doc)
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
HASTY_GUESSING_THRESHOLD_MINUTES = 0.5 # minutes (Used for BEHAVIOR_GUESSING_HASTY tag)

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
    'DI_DATA_INTERPRETATION_ERROR': 'Unknown', # Should ideally not appear in V data
    'DI_LOGICAL_REASONING_ERROR': 'Unknown',
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'Unknown',
}

# Diagnostic Parameter Mapping (for direct use or later reference)
V_DIAGNOSTIC_PARAMS = {
    'CR': {
        'Reading/Understanding': 'V_CR_READING_COMPREHENSION_ERROR',
        'Logic/Reasoning': 'V_CR_LOGICAL_REASONING_ERROR',
        'SFE': 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'
    },
    'RC': {
        'Reading/Understanding': 'V_RC_READING_COMPREHENSION_ERROR',
        'Inference/Application': 'V_RC_INFERENCE_APPLICATION_ERROR',
        'SFE': 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'
    },
}

# Skills associated with carelessness for Chapter 5
CARELESSNESS_SKILLS = {
    'V_CARELESSNESS_DETAIL_OMISSION',
    'V_CARELESSNESS_OPTION_MISREAD'
}

# --- V-Specific Helper Functions (if any needed in future) ---
# ...

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
        sfe_errors = group[group['question_fundamental_skill'] == 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'].eq(False).sum() if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in group['question_fundamental_skill'].unique() else 0
        sfe_error_rate_within_skill_errors = sfe_errors / errors if errors > 0 else 0.0

        status = 'OK'
        is_y_sfe = False

        # Apply rules
        if skill in exempted_v_skills:
            status = 'X' # Exempted
            analysis['exempted_skills_x'].append(skill)
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
            if skill == 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' or sfe_error_rate_within_skill_errors > y_sfe_threshold:
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
            'sfe_error_count': sfe_errors,
            'is_y_sfe': is_y_sfe,
            'question_type': question_type # Store the type for context
        }

    # Apply Macro Override Rules (Y-agg / Z-agg)
    # Example: Trigger if >= 3 skills in a category are Y or Z
    macro_trigger_threshold = 3
    if len(reading_y_skills) + len(reading_z_skills) >= macro_trigger_threshold:
         analysis['macro_override_reading']['triggered'] = True
         analysis['macro_override_reading']['reason'] = f">= {macro_trigger_threshold} Reading/Understanding skills are Weak (Y) or Insufficiently Covered (Z)."
         analysis['macro_override_reading']['skills_involved'] = reading_y_skills + reading_z_skills

    if len(logic_etc_y_skills) + len(logic_etc_z_skills) >= macro_trigger_threshold:
        analysis['macro_override_logic_grammar_inference']['triggered'] = True
        analysis['macro_override_logic_grammar_inference']['reason'] = f">= {macro_trigger_threshold} Logic/Grammar/Inference skills are Weak (Y) or Insufficiently Covered (Z)."
        analysis['macro_override_logic_grammar_inference']['skills_involved'] = logic_etc_y_skills + logic_etc_z_skills

    # Ensure exempted list is unique
    analysis['exempted_skills_x'] = list(set(analysis['exempted_skills_x']))

    return analysis

def _observe_patterns(df_v, v_time_pressure_status):
    """Observes patterns and behavioral indicators for Chapter 5.
       Checks for early rushing (absolute time) and high fast-wrong rate (relative time from Ch3).
    """
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

    # 1. Early Rushing Risk (V-Doc Ch5, absolute time < 1.0 min)
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
            print(f"      Ch5 Pattern: Found {len(early_rushing_indices)} potentially rushed questions in first third. Triggered: BEHAVIOR_EARLY_RUSHING_FLAG_RISK")

    # 2. Carelessness Issue (V-Doc Ch5, uses Ch3 'Fast' definition: < 0.75 * avg)
    # Use the 'is_relatively_fast' column calculated in _apply_ch3_diagnostic_rules
    if 'is_relatively_fast' in df_v.columns and 'is_correct' in df_v.columns:
        fast_mask = df_v['is_relatively_fast'] == True # Use the correct flag name (0.75 threshold)
        num_relatively_fast_total = fast_mask.sum()
        num_relatively_fast_incorrect = (fast_mask & (df_v['is_correct'] == False)).sum()

        if num_relatively_fast_total > 0:
            fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
            analysis['fast_wrong_rate'] = fast_wrong_rate
            # MD threshold is 0.25
            if fast_wrong_rate > 0.25:
                analysis['carelessness_issue'] = True
                analysis['param_triggers'].append('BEHAVIOR_CARELESSNESS_ISSUE')
                print(f"      Ch5 Pattern: Carelessness issue flagged (Fast-Wrong Rate: {fast_wrong_rate:.1%} > 25%). Triggered: BEHAVIOR_CARELESSNESS_ISSUE")
            else:
                print(f"      Ch5 Pattern: Fast-Wrong Rate = {fast_wrong_rate:.1%}")
        else:
            print("      Ch5 Pattern: No 'relatively fast' questions found to calculate carelessness rate.")
    else:
        print("      Ch5 Pattern: Skipping carelessness rate calculation ('is_relatively_fast' or 'is_correct' column missing). Ensure _apply_ch3_diagnostic_rules runs first.")

    return analysis

def _analyze_correct_slow(df_correct, question_type):
    """Analyzes correct but slow questions for Chapter 4.
       'Slow' is defined by the 'overtime' flag calculated in Chapter 1/3.
    """
    analysis = {
        'total_correct': 0,
        'correct_slow_count': 0,
        'correct_slow_rate': 0.0,
        'avg_difficulty_slow': None,
        'avg_time_slow': 0.0,
        'dominant_bottleneck_type': 'N/A', # Reading vs. Logic/Grammar/Inference
        'skill_breakdown_slow': {}
    }
    if df_correct.empty or 'question_time' not in df_correct.columns:
        return analysis

    total_correct = len(df_correct)
    analysis['total_correct'] = total_correct

    # Filter for slow questions using the 'overtime' flag (calculated based on Ch1 rules)
    if 'overtime' not in df_correct.columns:
        print(f"    Warning: 'overtime' column missing for Chapter 4 analysis ({question_type}). Cannot identify slow questions.")
    return analysis

    slow_correct_df = df_correct[df_correct['overtime'] == True].copy() # Ensure it's a copy
    correct_slow_count = len(slow_correct_df)
    analysis['correct_slow_count'] = correct_slow_count

    if total_correct > 0:
        analysis['correct_slow_rate'] = correct_slow_count / total_correct

    if correct_slow_count > 0:
        # --- Reset index of the filtered slow subset ---
        slow_correct_df.reset_index(drop=True, inplace=True)
        # --- End Reset ---

        # Analyze characteristics of slow questions
        if 'question_difficulty' in slow_correct_df.columns:
            analysis['avg_difficulty_slow'] = slow_correct_df['question_difficulty'].mean()
        analysis['avg_time_slow'] = slow_correct_df['question_time'].mean() # Keep in original units (Minutes)

        if 'question_fundamental_skill' in slow_correct_df.columns:
            # Map skills to categories to find bottleneck type
            # Ensure 'Unknown' category exists for robustness
            skill_to_category = V_SKILL_TO_ERROR_CATEGORY.copy()
            skill_to_category['Unknown Skill'] = 'Unknown'
            # Now assign the mapped series; index should align after reset
            slow_correct_df['error_category'] = slow_correct_df['question_fundamental_skill'].map(skill_to_category).fillna('Unknown')
            category_counts_slow = slow_correct_df['error_category'].value_counts()

            reading_slow = category_counts_slow.get('Reading/Understanding', 0)
            # Only include CR/RC related categories here
            logic_grammar_inference_slow = (category_counts_slow.get('Logic/Reasoning', 0) +
                                             category_counts_slow.get('Inference/Application', 0))

            # Determine dominant bottleneck
            if reading_slow > logic_grammar_inference_slow and reading_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Reading/Understanding'
            elif logic_grammar_inference_slow > reading_slow and logic_grammar_inference_slow / correct_slow_count > 0.5:
                # Use the combined name matching the translation key
                analysis['dominant_bottleneck_type'] = 'Logic/Reasoning' # or 'Inference/Application' or 'Logic/Grammar/Inference' if defined
            else:
                analysis['dominant_bottleneck_type'] = 'Mixed/Unclear'

            analysis['skill_breakdown_slow'] = slow_correct_df['question_fundamental_skill'].value_counts().to_dict()
    else:
        analysis['dominant_bottleneck_type'] = 'Skill data missing'

    return analysis

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

def _calculate_diagnostic_metrics(df_subset, type_name):
    """Calculates common diagnostic metrics for a subset of data."""
    metrics = {
        'type': type_name,
        'total_questions': 0,
        'errors': 0,
        'error_rate': 0.0,
        'overtime_count': 0,
        'overtime_rate': 0.0,
        'avg_time_spent': 0.0, # in minutes
        'avg_difficulty_correct': None,
        'avg_difficulty_incorrect': None,
        'initial_diagnosis': "No data available."
    }
    if df_subset.empty:
        return metrics

    total = len(df_subset)
    metrics['total_questions'] = total

    # Basic Accuracy
    errors = df_subset['is_correct'].eq(False).sum() # Use 'is_correct'
    metrics['errors'] = errors
    metrics['error_rate'] = errors / total if total > 0 else 0.0

    # Time Analysis (ensure columns exist)
    if 'question_time' in df_subset.columns:
        metrics['avg_time_spent'] = df_subset['question_time'].mean() / 60.0 # Assuming seconds -> minutes

    if 'overtime' in df_subset.columns: # 'overtime' boolean column needs to be calculated upstream if needed
        overtime_count = df_subset['overtime'].eq(True).sum()
        metrics['overtime_count'] = overtime_count
        metrics['overtime_rate'] = overtime_count / total if total > 0 else 0.0

    # Difficulty Analysis (ensure column exists)
    if 'question_difficulty' in df_subset.columns:
        correct_subset = df_subset[df_subset['is_correct'] == True] # Use 'is_correct'
        incorrect_subset = df_subset[df_subset['is_correct'] == False] # Use 'is_correct'
        if not correct_subset.empty:
            metrics['avg_difficulty_correct'] = correct_subset['question_difficulty'].mean()
        if not incorrect_subset.empty:
            metrics['avg_difficulty_incorrect'] = incorrect_subset['question_difficulty'].mean()

    # Simple Initial Diagnosis (based on error rate and difficulty comparison)
    diagnosis_parts = []
    if metrics['error_rate'] > 0.5: # Example threshold
        diagnosis_parts.append("High error rate.")
    elif metrics['error_rate'] < 0.2: # Example threshold
         diagnosis_parts.append("Low error rate.")
    else:
        diagnosis_parts.append("Moderate error rate.")

    if metrics['avg_difficulty_correct'] is not None and metrics['avg_difficulty_incorrect'] is not None:
        if metrics['avg_difficulty_incorrect'] < metrics['avg_difficulty_correct']:
             diagnosis_parts.append("Incorrect questions were, on average, easier than correct ones - potential sign of missing easy points.")
        elif metrics['avg_difficulty_incorrect'] > metrics['avg_difficulty_correct'] + 0.5: # Example threshold
             diagnosis_parts.append("Incorrect questions were significantly harder.")

    # Add time insights if available
    # Example: if metrics['avg_time_spent'] > SOME_THRESHOLD: diagnosis_parts.append("High average time.")

    metrics['initial_diagnosis'] = " ".join(diagnosis_parts) if diagnosis_parts else "Basic performance calculated."


    return metrics


# --- V-Specific Diagnosis Functions ---

def _diagnose_cr(df_cr):
    """Placeholder diagnosis for Critical Reasoning (CR)."""
    print("      Diagnosing CR...")
    return _calculate_diagnostic_metrics(df_cr, "CR")


def _diagnose_rc(df_rc):
    """Placeholder diagnosis for Reading Comprehension (RC)."""
    # Note: RC might need more complex handling (grouping by passage, separating reading time)
    # This is a simplified version for now.
    print("      Diagnosing RC...")
    return _calculate_diagnostic_metrics(df_rc, "RC")

def _diagnose_verbal_overall(df_v):
     """Placeholder for overall Verbal section analysis (if needed beyond type breakdown)."""
     print("      Diagnosing Verbal Overall...")
     # Could calculate overall metrics or look for cross-type patterns
     # For now, just use the generic calculator on the whole V dataset
     return _calculate_diagnostic_metrics(df_v, "Verbal Overall")

# --- Helper Function to Calculate First Third Averages ---
def _calculate_first_third_averages(df):
    """Calculates the average time per type for the first 1/3 of questions."""
    first_third_avg_time = {}
    if df.empty or 'question_position' not in df.columns or 'question_type' not in df.columns or 'question_time' not in df.columns:
        return first_third_avg_time

    total_questions = df['question_position'].max() # Assuming position is 1-based and consecutive
    if pd.isna(total_questions) or total_questions == 0: return first_third_avg_time

    first_third_limit = total_questions / 3
    df_first_third = df[df['question_position'] <= first_third_limit]

    if not df_first_third.empty:
        first_third_avg_time = df_first_third.groupby('question_type')['question_time'].mean().to_dict()
        print(f"DEBUG: Calculated first_third_average_time_per_type: {first_third_avg_time}") # DEBUG

    return first_third_avg_time

# --- Main V Diagnosis Runner ---

def run_v_diagnosis(df_v, v_time_pressure_status, v_avg_time_per_type, v_invalid_count=0): # Added v_invalid_count parameter
    """
    Runs the diagnostic analysis specifically for the Verbal section.

    Args:
        df_v (pd.DataFrame): DataFrame containing V response data (can include invalid).
        v_time_pressure_status (bool): Whether time pressure was detected for V.
        v_avg_time_per_type (dict): Dictionary mapping V question types to average times (overall).
        v_invalid_count (int): Number of invalid V questions already identified.

    Returns:
        dict: A dictionary containing the results of the V diagnosis.
        str: A string containing the summary report for the V section.
        pd.DataFrame: The processed V DataFrame with added diagnostic columns
                      (including 'is_invalid', diagnostic_params_list, etc.).
    """
    print("  Running Verbal Diagnosis...")
    v_diagnosis_results = {}

    if df_v.empty or 'question_position' not in df_v.columns: # Need position early
        print("    No V data or question_position provided. Skipping V diagnosis.")
        # Return empty dataframe with expected columns for consistency downstream
        empty_df = pd.DataFrame(columns=['question_position', 'question_time', 'is_correct', 'question_type',
                                          'question_difficulty', 'question_fundamental_skill', 'is_invalid',
                                          'overtime', 'rc_group_id', 'rc_group_size', 'rc_reading_time',
                                          'rc_group_total_time', 'rc_reading_overtime', 'rc_single_q_overtime',
                                          'reading_comprehension_barrier_inquiry', 'is_sfe',
                                          'is_relatively_fast', 'time_performance_category',
                                          'diagnostic_params_list'])
        return {}, "Verbal (V) 部分無有效數據或題目順序信息，無法進行診斷。", empty_df

    # Make a copy to avoid modifying the original slice
    df_v = df_v.copy()

    # --- Ensure basic required columns exist early ---
    required_cols = ['question_position', 'question_time', 'is_correct', 'question_type']
    for col in required_cols:
        if col not in df_v.columns:
            print(f"    ERROR: Required column '{col}' missing. Cannot proceed with V diagnosis.")
            # Return empty dataframe with expected columns
            empty_df = pd.DataFrame(columns=['question_position', 'question_time', 'is_correct', 'question_type',
                                          'question_difficulty', 'question_fundamental_skill', 'is_invalid',
                                          'overtime', 'rc_group_id', 'rc_group_size', 'rc_reading_time',
                                          'rc_group_total_time', 'rc_reading_overtime', 'rc_single_q_overtime',
                                          'reading_comprehension_barrier_inquiry', 'is_sfe',
                                          'is_relatively_fast', 'time_performance_category',
                                          'diagnostic_params_list'])
            return {}, f"Verbal (V) 部分缺少必需欄位 '{col}'，無法進行診斷。", empty_df


    # --- Calculate Prerequisites for Invalid Data Marking (Chapter 1) ---
    total_number_of_questions = 0
    if 'question_position' in df_v.columns and not df_v['question_position'].empty:
         # Use max() safely, handle potential non-numeric or all-NaN cases
         if pd.api.types.is_numeric_dtype(df_v['question_position']) and df_v['question_position'].notna().any():
             total_number_of_questions = df_v['question_position'].max()
         else:
             print("    Warning: 'question_position' column contains non-numeric or all NaN values. Cannot determine total question count accurately.")

    print(f"DEBUG: Total number of V questions based on position: {total_number_of_questions}")

    first_third_avg_time_per_type = _calculate_first_third_averages(df_v) # Needs pos, type, time

    # Calculate RC group info needed for hasty check and later overtime checks
    df_v = _identify_rc_groups(df_v) # Needs pos, type. Adds 'rc_group_id'
    # Add group size after identifying groups
    if 'rc_group_id' in df_v.columns:
        group_sizes_map = df_v.dropna(subset=['rc_group_id']).groupby('rc_group_id').size()
        df_v['rc_group_size'] = df_v['rc_group_id'].map(group_sizes_map)
    else:
        df_v['rc_group_size'] = np.nan

    df_v = _calculate_rc_times(df_v) # Needs group_id, pos, time. Adds 'rc_group_total_time', 'rc_reading_time'

    # --- Chapter 1: Implement Invalid Data Marking Logic ---
    df_v['is_invalid'] = False # Initialize column
    num_invalid_v_questions = 0 # Initialize counter

    if total_number_of_questions > 0 and v_time_pressure_status: # Only mark invalid if time pressure is TRUE
        last_third_start_pos = math.ceil(total_number_of_questions * 2 / 3) + 1 # Start of the last third
        print(f"DEBUG: Checking for invalid questions from position {last_third_start_pos} onwards (Time Pressure is TRUE).")

        # Create masks for conditions within the last third
        last_third_mask = df_v['question_position'] >= last_third_start_pos

        # Abandoned condition
        abandoned_mask = (df_v['question_time'] < 0.5) & last_third_mask

        # Hasty condition 1: time < 1.0 min
        hasty_time_mask = (df_v['question_time'] < 1.0) & last_third_mask

        # Hasty condition 2 (CR): time < 0.5 * first_third_avg
        hasty_cr_mask = pd.Series(False, index=df_v.index) # Initialize with False
        first_third_cr_avg = first_third_avg_time_per_type.get('CR', None)
        if first_third_cr_avg is not None and first_third_cr_avg > 0:
            hasty_cr_mask = (
                (df_v['question_type'] == 'CR') & \
                (df_v['question_time'] < first_third_cr_avg * 0.5) & \
                last_third_mask
            )
        else:
            print("DEBUG: First third CR average time not available or zero, skipping hasty CR check.")


        # Hasty condition 3 (RC): group_time < 0.5 * (first_third_avg * group_size)
        hasty_rc_mask = pd.Series(False, index=df_v.index) # Initialize with False
        first_third_rc_avg = first_third_avg_time_per_type.get('RC', None)
        if (first_third_rc_avg is not None and 
            first_third_rc_avg > 0 and 
            'rc_group_total_time' in df_v.columns and 
            'rc_group_size' in df_v.columns):
            # Apply only where rc_group_total_time and rc_group_size are valid
            # Create mask for valid RC group data
            valid_rc_check_mask = (
                df_v['rc_group_total_time'].notna() & 
                df_v['rc_group_size'].notna() & 
                (df_v['rc_group_size'] > 0)
            )
            
            # Create mask for hasty RC questions
            hasty_rc_mask = (
                (df_v['question_type'] == 'RC') & \
                (df_v['rc_group_total_time'] < (first_third_rc_avg * df_v['rc_group_size'] * 0.5)) & \
                valid_rc_check_mask & \
                last_third_mask
            )
        else:
            print("DEBUG: First third RC average time, group time, or group size not available/valid, skipping hasty RC check.")

        # Combine Hasty conditions
        hasty_combined_mask = hasty_time_mask | hasty_cr_mask | hasty_rc_mask

        # Final Invalid Mask: (Abandoned OR Hasty) AND in last third AND time pressure is True
        invalid_mask = (abandoned_mask | hasty_combined_mask) & last_third_mask

        # Apply the mask to set 'is_invalid' column
        df_v.loc[invalid_mask, 'is_invalid'] = True

        # Count the number of invalid questions marked
        num_invalid_v_questions = df_v['is_invalid'].sum()
        if num_invalid_v_questions > 0:
             print(f"    Marked {num_invalid_v_questions} questions as invalid due to haste/abandonment under time pressure.")
             # Optional: Print indices of invalid questions for debugging
             # print(f"    Invalid question indices: {df_v[df_v['is_invalid']].index.tolist()}")
    elif not v_time_pressure_status:
        print("DEBUG: Time pressure is FALSE, skipping invalid data marking based on haste/abandonment.")
    else: # total_number_of_questions is 0
        print("DEBUG: Total number of questions is 0, skipping invalid data marking.")


    # --- Chapter 1 Logic Adjustments: CR Overtime & RC flags (Continue after invalid marking) ---
    # RC group info and times already calculated above

    # Initialize/Reset 'overtime' column
    df_v['overtime'] = False
    df_v['rc_reading_overtime'] = False # Initialize RC flags
    df_v['rc_single_q_overtime'] = False
    df_v['reading_comprehension_barrier_inquiry'] = False # Initialize Barrier flag

    # Determine CR Overtime Threshold based on pressure
    cr_overtime_threshold = CR_OVERTIME_THRESHOLDS[v_time_pressure_status]
    print(f"DEBUG: CR Overtime Threshold set to {cr_overtime_threshold} min based on pressure={v_time_pressure_status}")

    # Apply Overtime Logic (CR and RC)
    rc_target_times = RC_GROUP_TARGET_TIMES[v_time_pressure_status]
    if 'rc_group_id' in df_v.columns: # Ensure column exists
        for index, row in df_v.iterrows():
            # Skip overtime calculation for invalid rows
            if row['is_invalid']:
                continue

            q_type = row['question_type']
            q_time = row.get('question_time', None)

            if q_type == 'Critical Reasoning':
                if q_time is not None and q_time > cr_overtime_threshold:
                    df_v.loc[index, 'overtime'] = True
            elif q_type == 'Reading Comprehension':
                group_size = row.get('rc_group_size')
                # Ensure group_size is valid before using it as key
                if pd.isna(group_size) or group_size not in rc_target_times:
                    # print(f"DEBUG RC OT Skip: Index {index}, Invalid group size: {group_size}")
                    continue # Skip RC OT calculation if group size is invalid

                target_group_time = rc_target_times.get(group_size)

                # Check Group Overtime
                group_total_time = row.get('rc_group_total_time')
                is_group_ot = False
                # Ensure target_group_time is valid before comparison
                if target_group_time is not None and pd.notna(group_total_time) and group_total_time > (target_group_time + RC_GROUP_TARGET_TIME_ADJUSTMENT):
                     is_group_ot = True
                     # print(f"DEBUG RC Group OT: Index {index}, Group {row.get('rc_group_id')}, Total {group_total_time:.2f} > Target {target_group_time:.1f}")

                # Check Reading Overtime (reading_time vs threshold)
                reading_time = row.get('rc_reading_time')
                reading_threshold = RC_READING_TIME_THRESHOLD_3Q if group_size == 3 else RC_READING_TIME_THRESHOLD_4Q
                is_reading_ot = pd.notna(reading_time) and reading_time > reading_threshold
                df_v.loc[index, 'rc_reading_overtime'] = is_reading_ot # Store flag
                # if is_reading_ot: print(f"DEBUG RC Reading OT: Index {index}, Time {reading_time:.2f} > Threshold {reading_threshold:.1f}")

                # Check Reading Comprehension Barrier Inquiry flag (MD Ch1)
                if is_reading_ot:
                    df_v.loc[index, 'reading_comprehension_barrier_inquiry'] = True
                    # print(f"      Ch1 Barrier Flag Triggered: RC Q {row['question_position']} (Reading time {reading_time:.2f} > {reading_threshold:.1f})")

                # Check Single Question Overtime (adjusted_rc_time > 2.0 min - MD Ch1)
                adjusted_rc_time = q_time # Default for non-first q or if reading time is missing
                # Determine if it's the first question in its group
                is_first_rc_q = False
                if pd.notna(row['rc_group_id']):
                    group_min_pos = df_v[df_v['rc_group_id'] == row['rc_group_id']]['question_position'].min()
                    is_first_rc_q = row['question_position'] == group_min_pos

                if is_first_rc_q and pd.notna(reading_time) and pd.notna(q_time):
                    # Calculate adjusted time only for the first question if reading time is valid
                     adjusted_rc_time = q_time - reading_time
                elif not is_first_rc_q:
                     # For non-first questions, adjusted_rc_time is just q_time
                     pass # Already set by default
                else: # First question but reading time invalid, or q_time invalid
                     adjusted_rc_time = None # Cannot calculate adjusted time reliably

                is_individual_ot = False
                if pd.notna(adjusted_rc_time):
                    is_individual_ot = adjusted_rc_time > RC_INDIVIDUAL_Q_THRESHOLD_MINUTES

                df_v.loc[index, 'rc_single_q_overtime'] = is_individual_ot # Store flag (This corresponds to individual_overtime)
                # if is_individual_ot: print(f"DEBUG RC Individual OT: Index {index}, Adj Time {adjusted_rc_time:.2f} > Threshold {RC_INDIVIDUAL_Q_THRESHOLD_MINUTES:.1f}")

                # Final RC Overtime (Per V-Doc Ch1 "用於第三章 Slow 分類"): Group OT OR Individual OT
                if is_group_ot or is_individual_ot:
                    df_v.loc[index, 'overtime'] = True # Set the main 'overtime' flag for RC

    else:
        print("Warning: 'rc_group_id' not found or other RC prerequisite missing, cannot calculate detailed RC overtime.")

    # --- Chapter 1 Global Rule: Mark Suspiciously Fast --- 
    df_v['suspiciously_fast'] = False # Initialize column
    print(f"DEBUG: Calculating 'suspiciously_fast' flag using overall avg times: {v_avg_time_per_type}")
    for q_type, avg_time in v_avg_time_per_type.items():
        if avg_time is not None and avg_time > 0 and 'question_time' in df_v.columns:
             # Ensure we only compare valid, non-NaN question times
             valid_time_mask = df_v['question_time'].notna()
             suspicious_mask = (df_v['question_type'] == q_type) & \
                               (df_v['question_time'] < (avg_time * 0.5)) & \
                               valid_time_mask
             df_v.loc[suspicious_mask, 'suspiciously_fast'] = True
             # Debug print count for this type
             # print(f"DEBUG: Marked {suspicious_mask.sum()} questions as suspiciously_fast for type {q_type} (Threshold < {avg_time * 0.5:.2f})")
        else:
             print(f"DEBUG: Skipping suspiciously_fast calculation for type {q_type} due to missing/invalid avg_time ({avg_time}) or missing 'question_time' column.")

    # --- Apply Chapter 3 Diagnostic Rules (Uses calculated 'overtime') ---
    # Calculate max correct difficulty per skill (needed for SFE check)
    # IMPORTANT: Use only VALID data for calculating max correct difficulty
    df_correct_v = df_v[(df_v['is_correct'] == True) & (df_v['is_invalid'] == False)].copy()
    max_correct_difficulty_per_skill_v = {}
    if not df_correct_v.empty and 'question_fundamental_skill' in df_correct_v.columns and 'question_difficulty' in df_correct_v.columns:
        # Ensure difficulty column is numeric before grouping
        if pd.api.types.is_numeric_dtype(df_correct_v['question_difficulty']):
            # Filter out NaNs in skill before grouping
            df_correct_v_skill_valid = df_correct_v.dropna(subset=['question_fundamental_skill'])
            if not df_correct_v_skill_valid.empty:
                 max_correct_difficulty_per_skill_v = df_correct_v_skill_valid.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # --- DEBUG: Print columns before applying rules ---
    print("DEBUG (run_v_diagnosis): Columns in df_v BEFORE _apply_ch3_diagnostic_rules:")
    print(df_v.columns.tolist())
    # print("DEBUG (run_v_diagnosis): Input df_v head BEFORE _apply_ch3_diagnostic_rules:")
    # print(df_v.head().to_string())
    print(f"DEBUG (run_v_diagnosis): max_correct_difficulty_per_skill_v (from valid data): {max_correct_difficulty_per_skill_v}")
    print(f"DEBUG (run_v_diagnosis): v_avg_time_per_type (overall): {v_avg_time_per_type}")
    # --- END DEBUG ---

    # Apply the rules - this function modifies df_v in place
    df_v = _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill_v, v_avg_time_per_type)

    # --- DEBUG: Print columns AFTER applying rules ---
    print("DEBUG (run_v_diagnosis): Columns in df_v AFTER _apply_ch3_diagnostic_rules:")
    print(df_v.columns.tolist())
    # Check if the key column was added
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (run_v_diagnosis): 'diagnostic_params' column head AFTER rules:")
        # Print head safely, handle potential errors if column is somehow empty list etc.
        try:
            print(df_v['diagnostic_params'].head())
        except Exception as e:
            print(f"Error printing diagnostic_params head: {e}")
            print(df_v['diagnostic_params']) # Print the whole series if head fails
    else:
        print("ERROR (run_v_diagnosis): 'diagnostic_params' column MISSING AFTER rules!")
    # --- END DEBUG ---

    # --- Translate diagnostic codes ---
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (v_diagnostic.py): Translating 'diagnostic_params' to Chinese...")
        # Apply the translation function (already handles lists)
        # Ensure the lambda handles non-list elements gracefully if they sneak in
        df_v['diagnostic_params_list_chinese'] = df_v['diagnostic_params'].apply(
            lambda params: [_translate_v(p) for p in params] if isinstance(params, list) else []
        )
    else:
        print("WARNING (v_diagnostic.py): 'diagnostic_params' column not found for translation.")
        # Initialize with empty lists if column doesn't exist
        # Ensure correct initialization syntax and apply it to the dataframe
        num_rows = len(df_v)
        df_v['diagnostic_params_list_chinese'] = pd.Series([[] for _ in range(num_rows)], index=df_v.index)


    # --- Drop original English codes column --- 
    if 'diagnostic_params' in df_v.columns:
        try:
             df_v.drop(columns=['diagnostic_params'], inplace=True)
             print("DEBUG (v_diagnostic.py): Dropped 'diagnostic_params' column.")
        except KeyError: # Handle case where column might have already been dropped or renamed
             print("DEBUG (v_diagnostic.py): 'diagnostic_params' column not found during drop (might be already handled).")

    # --- Rename translated column --- 
    if 'diagnostic_params_list_chinese' in df_v.columns:
        try:
            df_v.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'}, inplace=True)
            print("DEBUG (v_diagnostic.py): Renamed 'diagnostic_params_list_chinese' to 'diagnostic_params_list'")
        except Exception as e: # Catch potential errors during rename
             print(f"ERROR renaming column: {e}")
             # If rename fails, ensure the target column still exists or is created
             if 'diagnostic_params_list' not in df_v.columns:
                 print("Initializing 'diagnostic_params_list' after rename failed.")
                 num_rows = len(df_v)
                 df_v['diagnostic_params_list'] = pd.Series([[] for _ in range(num_rows)], index=df_v.index)
    else:
        # If rename source doesn't exist, still ensure target 'diagnostic_params_list' exists
        print("DEBUG (v_diagnostic.py): Source column ('diagnostic_params_list_chinese') not found for rename. Ensuring 'diagnostic_params_list' exists.")
        if 'diagnostic_params_list' not in df_v.columns:
            num_rows = len(df_v)
            df_v['diagnostic_params_list'] = pd.Series([[] for _ in range(num_rows)], index=df_v.index)

    # --- Initialize results dictionary --- 
    v_diagnosis_results = {}

    # --- Populate Chapter 1 Results --- 
    v_diagnosis_results['chapter_1'] = {
        'time_pressure_status': v_time_pressure_status,
        'invalid_questions_excluded': num_invalid_v_questions
        # Add other relevant Ch1 metrics if calculated (e.g., total time, avg time)
    }
    
    # Use provided v_invalid_count if it's greater than the calculated value
    if v_invalid_count > num_invalid_v_questions:
        print(f"    Using provided invalid question count ({v_invalid_count}) for reporting instead of calculated value ({num_invalid_v_questions}).")
        v_diagnosis_results['chapter_1']['invalid_questions_excluded'] = v_invalid_count
        
    print("  Populated Chapter 1 V results.")

    # --- Populate Chapter 2 Results (Basic Metrics) --- 
    print("  Executing V Analysis (Chapter 2 - Metrics)...")
    df_valid_v = df_v[df_v['is_invalid'] == False].copy() if 'is_invalid' in df_v.columns else df_v.copy()
    # Overall metrics
    v_diagnosis_results.setdefault('chapter_2', {})['overall_metrics'] = _calculate_metrics_for_group(df_valid_v) # Use helper
    # Metrics by type (CR vs RC)
    v_diagnosis_results.setdefault('chapter_2', {})['by_type'] = _analyze_dimension(df_valid_v, 'question_type') # Use helper
    # Metrics by difficulty (Requires grading first)
    # TODO: Add difficulty grading column before this step if needed for Ch2 report
    df_valid_v['difficulty_grade'] = df_valid_v['question_difficulty'].apply(_grade_difficulty_v)
    v_diagnosis_results.setdefault('chapter_2', {})['by_difficulty'] = _analyze_dimension(df_valid_v, 'difficulty_grade')
    print("    Finished Chapter 2 V metrics.")

    # --- Populate Chapter 3 Results (Error Analysis from diagnosed df) ---
    print("  Extracting V Analysis (Chapter 3 - Errors)...")
    # The actual diagnosis happened in _apply_ch3_diagnostic_rules, now we structure the result.
    v_diagnosis_results['chapter_3'] = {
        # Store the dataframe itself for report generation to access params/sfe/time_perf
        'diagnosed_dataframe': df_v.copy(), 
        # Optionally, extract summary stats like error counts per type/skill if needed
        # 'cr_error_analysis': _analyze_error_types_from_params(df_v[df_v['question_type'] == 'CR'], 'CR'),
        # 'rc_error_analysis': _analyze_error_types_from_params(df_v[df_v['question_type'] == 'RC'], 'RC'),
    }
    print("    Finished Chapter 3 V error structuring.")

    # --- Populate Chapter 4 Results (Correct but Slow) ---
    print("  Executing V Analysis (Chapter 4 - Correct Slow)...")
    df_correct_v = df_valid_v[df_valid_v['is_correct'] == True]
    v_diagnosis_results['chapter_4'] = {
        'cr_correct_slow': _analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'CR'], 'CR'),
        'rc_correct_slow': _analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'RC'], 'RC')
    }
    print("    Finished Chapter 4 V correct slow analysis.")

    # --- Populate Chapter 5 Results (Patterns) ---
    print("  Executing V Analysis (Chapter 5 - Patterns)...")
    v_diagnosis_results['chapter_5'] = _observe_patterns(df_valid_v, v_time_pressure_status)
    print("    Finished Chapter 5 V pattern observation.")

    # --- Populate Chapter 6 Results (Skill Override & Exemption) --- #
    print("  Executing V Analysis (Chapter 6 - Skill Exemption & Override)...")
    # Calculate Exemption Status FIRST (Based on MD Ch6)
    exempted_skills = _calculate_skill_exemption_status(df_valid_v)
    # Calculate Override Rule (Based on MD Ch6 - independent of exemption)
    ch6_override_results = _calculate_skill_override(df_valid_v)
    # Combine results for Chapter 6 dictionary
    ch6_results = {
        **ch6_override_results, # Includes skill_error_rates, skill_override_triggered, dataframe_for_ch6
        'exempted_skills': exempted_skills # Add the calculated exempted skills set
    }
    v_diagnosis_results['chapter_6'] = ch6_results
    print(f"    Finished Chapter 6 V skill override/exemption analysis. Exempted: {exempted_skills}")

    # --- Generate Recommendations & Summary Report (Chapter 7 & 8) --- #
    # Pass exempted skills to recommendation generator
    v_recommendations = _generate_v_recommendations(v_diagnosis_results, exempted_skills)
    v_diagnosis_results['chapter_7'] = v_recommendations # Store recommendations

    v_report_content = _generate_v_summary_report(v_diagnosis_results) # Generate the report

    # --- DEBUG PRINT --- 
    print("DEBUG (v_diagnostic.py): Columns before return:", df_v.columns.tolist())
    if 'diagnostic_params_list' in df_v.columns:
        print("DEBUG (v_diagnostic.py): 'diagnostic_params_list' head:")
        print(df_v['diagnostic_params_list'].head())
    else:
        print("DEBUG (v_diagnostic.py): 'diagnostic_params_list' column MISSING before return!")
    # --- END DEBUG PRINT ---

    # --- 確保 Subject 欄位存在 ---
    if 'Subject' not in df_v.columns:
        print("警告: 'Subject' 欄位在 V 返回前缺失，正在重新添加...")
        df_v['Subject'] = 'V'
    elif df_v['Subject'].isnull().any() or (df_v['Subject'] != 'V').any():
        print("警告: 'Subject' 欄位存在但包含空值或錯誤值，正在修正...")
        df_v['Subject'] = 'V' # 強制修正

    print("  Verbal Diagnosis Complete.")
    # Return results dictionary, report string, and the diagnosed dataframe
    return v_diagnosis_results, v_report_content, df_v # Return the generated report


# --- V Appendix A Translation ---
# Maps internal skill/param names to user-friendly Chinese descriptions
APPENDIX_A_TRANSLATION_V = {
    # --- V-Doc Appendix A Parameters (Strictly Matched) ---
    # CR - Reading Comprehension
    'CR_READING_BASIC_OMISSION': "CR 閱讀理解: 基礎理解疏漏",
    'CR_READING_DIFFICULTY_STEM': "CR 閱讀理解: 題幹理解障礙 (關鍵詞/句式/邏輯/領域)",
    'CR_READING_TIME_EXCESSIVE': "CR 閱讀理解: 閱讀耗時過長",
    # CR - Question Understanding
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': "CR 題目理解: 提問要求把握錯誤",
    # CR - Reasoning Deficiencies
    'CR_REASONING_CHAIN_ERROR': "CR 推理障礙: 邏輯鏈分析錯誤 (前提/結論/關係)",
    'CR_REASONING_ABSTRACTION_DIFFICULTY': "CR 推理障礙: 抽象邏輯/術語理解困難",
    'CR_REASONING_PREDICTION_ERROR': "CR 推理障礙: 預判方向錯誤或缺失",
    'CR_REASONING_TIME_EXCESSIVE': "CR 推理障礙: 邏輯思考耗時過長",
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': "CR 推理障礙: 核心議題識別困難",
    # CR - Answer Choice Analysis
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': "CR 選項辨析: 選項本身理解困難",
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': "CR 選項辨析: 選項相關性判斷錯誤",
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': "CR 選項辨析: 強干擾選項混淆",
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': "CR 選項辨析: 選項篩選耗時過長",
    # CR - Method Application
    'CR_METHOD_PROCESS_DEVIATION': "CR 方法應用: 未遵循標準流程",
    'CR_METHOD_TYPE_SPECIFIC_ERROR': "CR 方法應用: 特定題型方法錯誤/不熟 (需註明題型)",
    # RC - Reading Comprehension
    'RC_READING_INFO_LOCATION_ERROR': "RC 閱讀理解: 關鍵信息定位/理解錯誤",
    'RC_READING_KEYWORD_LOGIC_OMISSION': "RC 閱讀理解: 忽略關鍵詞/邏輯",
    'RC_READING_VOCAB_BOTTLENECK': "RC 閱讀理解: 詞彙量瓶頸",
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': "RC 閱讀理解: 長難句解析困難",
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': "RC 閱讀理解: 篇章結構把握不清",
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': "RC 閱讀理解: 特定領域背景知識缺乏",
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': "RC 閱讀理解: 閱讀速度慢 (基礎問題)",
    'RC_READING_PRECISION_INSUFFICIENT': "RC 閱讀精度不足 (精讀/定位問題)",
    'RC_READING_COMPREHENSION_BARRIER': "RC 閱讀理解: 閱讀理解障礙 (耗時過長觸發)",
    # RC - Reading Method
    'RC_METHOD_INEFFICIENT_READING': "RC 閱讀方法: 閱讀方法效率低 (過度精讀)",
    # RC - Question Understanding
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': "RC 題目理解: 提問焦點把握錯誤",
    # RC - Location Skills
    'RC_LOCATION_ERROR_INEFFICIENCY': "RC 定位能力: 定位錯誤/效率低下",
    'RC_LOCATION_TIME_EXCESSIVE': "RC 定位能力: 定位效率低下 (反覆定位)",
    # RC - Reasoning Deficiencies
    'RC_REASONING_INFERENCE_WEAKNESS': "RC 推理障礙: 推理能力不足 (預判/細節/語氣)",
    'RC_REASONING_TIME_EXCESSIVE': "RC 推理障礙: 深度思考耗時過長",
    # RC - Answer Choice Analysis
    'RC_AC_ANALYSIS_DIFFICULTY': "RC 選項辨析: 選項理解/辨析困難 (含義/對應)",
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': "RC 選項辨析: 選項篩選耗時過長",
    # Foundational Mastery (CR & RC)
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "基礎掌握: 應用不穩定 (Special Focus Error)",
    # Efficiency Issues (CR & RC)
    'EFFICIENCY_BOTTLENECK_READING': "效率問題: 閱讀理解環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_REASONING': "效率問題: 推理分析環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_LOCATION': "效率問題: 信息定位環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': "效率問題: 選項辨析環節導致效率低下",
    # Behavioral Patterns
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    'BEHAVIOR_GUESSING_HASTY': "行為模式: 過快疑似猜題/倉促",

    # --- VDOC Defined Core Fundamental Skills ---
    'Plan/Construct': "計劃/構建",
    'Identify Stated Idea': "識別陳述信息",
    'Identify Inferred Idea': "識別推斷信息",
    'Analysis/Critique': "分析/批判",

    # --- Internal Codes (Not from V-Doc Appendix A, used for Reporting) ---
    # Difficulty Grades (from V-Doc Ch2/Ch7 definition)
    "Low / 505+": "低難度 (Low) / 505+",
    "Mid / 555+": "中難度 (Mid) / 555+",
    "Mid / 605+": "中難度 (Mid) / 605+",
    "Mid / 655+": "中難度 (Mid) / 655+",
    "High / 705+": "高難度 (High) / 705+",
    "High / 805+": "高難度 (High) / 805+",
    "Unknown Difficulty": "未知難度",

    # General/Status Codes (Not from V-Doc Appendix A)
    'Unknown Skill': "未知技能",
    'Y': "薄弱技能",
    'Y-SFE': "薄弱技能 (高 SFE)",
    'Z': "考察不足",
    'X': "基本掌握 (豁免)",
    'OK': "表現正常",
    'High': "高",
    'Low': "低",
    'Unknown': "未知",

    # Report Helper Categories (Not from V-Doc Appendix A)
    'Reading/Understanding': "閱讀理解",
    'Logic/Reasoning': "邏輯推理",
    'Inference/Application': "推理應用",
    'Method/Process': "方法/流程",
    'Behavioral': "行為模式",
    'Mixed/Other': "混合/其他",
    'N/A': '不適用',

    # Performance Labels (Not from V-Doc Appendix A)
    'Fast & Wrong': "快錯",
    'Slow & Wrong': "慢錯",
    'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對",
    'Fast & Correct': "快對",
    'Normal Time & Correct': "正常時間 & 對",
}

# --- Parameter Categories for Report Grouping ---
V_PARAM_CATEGORY_ORDER = [
    'SFE',
    'CR Reading', 'CR Question Understanding', 'CR Reasoning', 'CR AC Analysis', 'CR Method',
    'RC Reading', 'RC Question Understanding', 'RC Location', 'RC Reasoning', 'RC AC Analysis', 'RC Method',
    'Efficiency',
    'Behavioral',
    'Unknown' # Catch-all for unmapped params
]

V_PARAM_TO_CATEGORY = {
    # SFE
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    # CR
    'CR_READING_BASIC_OMISSION': 'CR Reading',
    'CR_READING_DIFFICULTY_STEM': 'CR Reading',
    'CR_READING_TIME_EXCESSIVE': 'Efficiency',
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'CR Question Understanding',
    'CR_REASONING_CHAIN_ERROR': 'CR Reasoning',
    'CR_REASONING_ABSTRACTION_DIFFICULTY': 'CR Reasoning',
    'CR_REASONING_PREDICTION_ERROR': 'CR Reasoning',
    'CR_REASONING_TIME_EXCESSIVE': 'Efficiency',
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': 'CR Reasoning',
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': 'CR AC Analysis',
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': 'CR AC Analysis',
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': 'CR AC Analysis',
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': 'Efficiency',
    'CR_METHOD_PROCESS_DEVIATION': 'CR Method',
    'CR_METHOD_TYPE_SPECIFIC_ERROR': 'CR Method',
    # RC
    'RC_READING_INFO_LOCATION_ERROR': 'RC Reading',
    'RC_READING_KEYWORD_LOGIC_OMISSION': 'RC Reading',
    'RC_READING_VOCAB_BOTTLENECK': 'RC Reading',
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': 'RC Reading',
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': 'RC Reading',
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': 'RC Reading',
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': 'Efficiency',
    'RC_READING_PRECISION_INSUFFICIENT': 'RC Reading',
    'RC_READING_COMPREHENSION_BARRIER': 'RC Reading',
    'RC_METHOD_INEFFICIENT_READING': 'RC Method',
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'RC Question Understanding',
    'RC_LOCATION_ERROR_INEFFICIENCY': 'RC Location',
    'RC_LOCATION_TIME_EXCESSIVE': 'Efficiency',
    'RC_REASONING_INFERENCE_WEAKNESS': 'RC Reasoning',
    'RC_REASONING_TIME_EXCESSIVE': 'Efficiency',
    'RC_AC_ANALYSIS_DIFFICULTY': 'RC AC Analysis',
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': 'Efficiency',
    # Efficiency (explicit)
    'EFFICIENCY_BOTTLENECK_READING': 'Efficiency',
    'EFFICIENCY_BOTTLENECK_REASONING': 'Efficiency',
    'EFFICIENCY_BOTTLENECK_LOCATION': 'Efficiency',
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': 'Efficiency',
    # Behavioral
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral',
    'BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'BEHAVIOR_GUESSING_HASTY': 'Behavioral',
}

def _translate_v(param):
    """Translates an internal V param/skill name using APPENDIX_A_TRANSLATION_V."""
    return APPENDIX_A_TRANSLATION_V.get(param, param)

# --- V Summary Report Generation Helper ---

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)) and not pd.isna(rate_value):
        return f"{rate_value:.1%}"
    else:
        return 'N/A' # Return N/A for non-numeric or NaN

def _generate_v_summary_report(v_diagnosis_results):
    """Generates the summary report string for the Verbal section."""
    print("DEBUG: +++ Entering _generate_v_summary_report +++") # DEBUG
    report_lines = []
    report_lines.append("## GMAT 語文 (Verbal) 診斷報告")
    report_lines.append("--- (基於用戶數據與模擬難度分析) ---")
    report_lines.append("")

    # Extract chapters safely
    ch1 = v_diagnosis_results.get('chapter_1', {})
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    ch7 = v_diagnosis_results.get('chapter_7', [])

    # --- Section 1: 時間策略與有效性 (來自總模塊) ---
    report_lines.append("**1. 時間策略與有效性**")
    time_pressure_detected = ch1.get('time_pressure_status', False)
    invalid_count = ch1.get('invalid_questions_excluded', 0)

    if time_pressure_detected:
        report_lines.append("- 根據分析，您在語文部分可能處於**時間壓力**下 (測驗時間剩餘不多或末尾部分題目作答過快)。")
    else:
        report_lines.append("- 根據分析，您在語文部分未處於明顯的時間壓力下。")

    if invalid_count > 0:
        report_lines.append(f"- 已將 {invalid_count} 道可能因時間壓力影響有效性的題目從詳細分析中排除，以確保診斷準確性。")
        report_lines.append("- 請注意，這些被排除的題目將不會包含在後續的錯誤難度分佈統計和練習建議中。")
    else:
        report_lines.append("- 所有題目數據均被納入詳細分析。")
    report_lines.append("")

    # --- Section 2: 表現概覽 --- #
    report_lines.append("**2. 表現概覽**")
    type_metrics = ch2.get('by_type', {})
    difficulty_metrics = ch2.get('by_difficulty', {})
    exempted_skills_ch6 = ch6.get('exempted_skills', set()) # Get exempted skills from Ch6 results

    # Overall by Type (CR vs RC)
    report_lines.append(f"- **CR vs. RC 題表現:**")
    for q_type_short in ['CR', 'RC']:
        # Map short type to full name if needed, assuming type_metrics uses short names
        q_type_full_name = 'Critical Reasoning' if q_type_short == 'CR' else 'Reading Comprehension'
        metrics = type_metrics.get(q_type_short) # Use short name to get metrics
        if metrics:
            error_rate_str = _format_rate(metrics.get('error_rate', 'N/A'))
            overtime_rate_str = _format_rate(metrics.get('overtime_rate', 'N/A'))
            avg_time_str = f"{metrics.get('avg_time_spent', 0.0):.2f}"
            report_lines.append(f"  - {q_type_full_name}: 錯誤率 {error_rate_str}, 超時率 {overtime_rate_str}, 平均耗時 {avg_time_str} 分鐘")
        else:
            report_lines.append(f"  - {q_type_full_name}: 無數據")

    # Difficulty Analysis Reporting
    if difficulty_metrics:
        report_lines.append(f"- **按難度水平表現:**")
        grade_order_en = ["Low / 505+", "Mid / 555+", "Mid / 605+", "Mid / 655+", "High / 705+", "High / 805+", "Unknown Difficulty"]
        for english_grade_key in grade_order_en:
            metrics = difficulty_metrics.get(english_grade_key)
            if metrics:
                grade_zh = _translate_v(english_grade_key)
                q_count = metrics.get('total_questions', 0)
                error_rate_str = _format_rate(metrics.get('error_rate', 'N/A'))
                avg_time_str = f"{metrics.get('avg_time_spent', 0.0):.2f}"
                report_lines.append(f"  - {grade_zh}: {q_count}題, 錯誤率 {error_rate_str}, 平均耗時 {avg_time_str} 分鐘")
    else:
        report_lines.append("- **按難度水平表現:** 無數據")

    # Error Difficulty Distribution
    all_error_records = []
    diagnosed_df_ch3 = ch3.get('diagnosed_dataframe')
    if diagnosed_df_ch3 is not None and not diagnosed_df_ch3.empty and 'is_correct' in diagnosed_df_ch3.columns:
        all_error_records = diagnosed_df_ch3[diagnosed_df_ch3['is_correct'] == False].to_dict('records')
    if all_error_records:
        error_difficulties = [err.get('question_difficulty') for err in all_error_records if err.get('question_difficulty') is not None and not pd.isna(err.get('question_difficulty'))]
        if error_difficulties:
            difficulty_labels = [_grade_difficulty_v(d) for d in error_difficulties]
            label_counts = pd.Series(difficulty_labels).value_counts()
            grade_order_en = ["Low / 505+", "Mid / 555+", "Mid / 605+", "Mid / 655+", "High / 705+", "High / 805+", "Unknown Difficulty"]
            label_counts = label_counts.reindex(grade_order_en).dropna()
            if not label_counts.empty:
                distribution_str = ", ".join([f"{_translate_v(label)} ({int(count)}題)" for label, count in label_counts.items()])
                report_lines.append(f"  - **錯誤難度分佈:** {distribution_str}")
            else:
                report_lines.append("  - **錯誤難度分佈:** 無有效難度數據可供分析。")
        else:
            report_lines.append("  - **錯誤難度分佈:** 錯誤題目無有效難度數據。")
    else:
        report_lines.append("  - **錯誤難度分佈:** 無錯誤題目可供分析難度分佈。")

    # Report Exempted Skills
    if exempted_skills_ch6:
        exempted_skills_zh = [_translate_v(s) for s in sorted(list(exempted_skills_ch6))]
        report_lines.append(f"- **已掌握技能 (豁免):** 以下技能表現良好 (全對且無超時)，無需針對性練習：{', '.join(exempted_skills_zh)}。")
    report_lines.append("")

    # --- Section 3: 核心問題診斷 --- #
    report_lines.append("**3. 核心問題診斷 (基於觸發的診斷標籤)**")
    diagnosed_df = ch3.get('diagnosed_dataframe')
    all_problem_items = []
    sfe_triggered_overall = False
    sfe_skills_involved = set()
    core_issues_params = set()
    secondary_evidence_trigger = False # Flag for Ch8 suggestion
    qualitative_analysis_trigger = False # Flag for Ch8 suggestion

    if diagnosed_df is not None and not diagnosed_df.empty:
        for index, row in diagnosed_df.iterrows():
            is_error = not row['is_correct']
            is_slow_correct = row['is_correct'] and row.get('overtime', False)
            params = row.get('diagnostic_params', []) # Use the detailed params from refactored Ch3
            is_sfe = row.get('is_sfe', False)
            skill = row.get('question_fundamental_skill', 'Unknown Skill')
            q_pos = row.get('question_position', 'N/A')
            time_cat = row.get('time_performance_category', 'Unknown') # Get time category

            if is_error or is_slow_correct:
                # Collect SFE info
                if is_sfe:
                    sfe_triggered_overall = True
                    if skill != 'Unknown Skill':
                        sfe_skills_involved.add(skill)
                        secondary_evidence_trigger = True # SFE often needs review

                # Collect core issue params (exclude SFE)
                current_core_params = {p for p in params if p != 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'}
                core_issues_params.update(current_core_params)

                # Store details for the list
                all_problem_items.append({
                    'position': q_pos,
                    'skill': skill,
                    'performance': time_cat,
                    'params': params, # Store original English params
                    'question_type': row.get('question_type', 'Unknown Type'),
                    'is_sfe': is_sfe
                })

                # Check for qualitative analysis triggers (MD Ch3 logic)
                if time_cat in ['Normal Time & Wrong', 'Slow & Wrong']:
                    secondary_evidence_trigger = True # These categories warrant review
                    # Check for complex params that might trigger qualitative
                    complex_params = {
                        'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                        'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                        'RC_REASONING_INFERENCE_WEAKNESS'
                    }
                    if any(p in complex_params for p in current_core_params):
                        qualitative_analysis_trigger = True
                elif time_cat == 'Slow & Correct':
                     qualitative_analysis_trigger = True # Often needs qualitative check for bottleneck

    # Report SFE Summary
    if sfe_triggered_overall:
        sfe_label = _translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        sfe_skills_zh = [_translate_v(s) for s in sorted(list(sfe_skills_involved))]
        sfe_note = f"{sfe_label}"
        if sfe_skills_zh:
            sfe_note += f" (涉及技能: {', '.join(sfe_skills_zh)})"
        report_lines.append(f"- **尤其需要注意:** {sfe_note}。(註：SFE 指在已掌握技能範圍內的題目失誤)")

    # Report if no core issues AND no SFE
    if not core_issues_params and not sfe_triggered_overall:
        report_lines.append("- 未識別出明顯的核心問題模式 (基於錯誤及效率分析)。")

    # Detailed Diagnostics List (REMOVED per user request - details in table)
    # if all_problem_items:
    #     report_lines.append("- **詳細診斷標籤 (含時間表現和技能):**")
    #     def sort_key(item):
    #         q_type = item.get('question_type', 'Unknown Type')
    #         skill_en = item.get('skill', 'zzzzz')
    #         skill_zh = _translate_v(skill_en)
    #         position = item.get('position', float('inf'))
    #         type_order = 0 if q_type == 'Critical Reasoning' else (1 if q_type == 'Reading Comprehension' else 2)
    #         sfe_order = 0 if item.get('is_sfe') else 1 # Prioritize SFE
    #         return (sfe_order, type_order, skill_zh, position)
    #     sorted_items = sorted(all_problem_items, key=sort_key)
    #
    #     for item in sorted_items:
    #         pos = item['position']
    #         skill_en = item['skill']
    #         skill_zh = _translate_v(skill_en)
    #         performance_en = item['performance']
    #         params_codes = item['params']
    #         performance_zh = _translate_v(performance_en)
    #         translated_params = [_translate_v(p) for p in params_codes]
    #         sfe_marker = "*" if item.get('is_sfe') else ""
    #
    #         line_parts = [f"  - {sfe_marker}題號 {pos}: [{performance_zh}, 技能: {skill_zh}] - 診斷:"]
    #         if translated_params:
    #             # Group params by category for readability
    #             params_by_category = {}
    #             for p_code, p_zh in zip(params_codes, translated_params):
    #                 category_en = V_PARAM_TO_CATEGORY.get(p_code, 'Unknown')
    #                 category_zh = _translate_v(category_en) if category_en != 'Unknown' else '其他'
    #                 if category_zh not in params_by_category:
    #                     params_by_category[category_zh] = []
    #                 params_by_category[category_zh].append(p_zh)
    #
    #             # Define order for categories (translate from V_PARAM_CATEGORY_ORDER)
    #             category_order_zh = [_translate_v(c) for c in V_PARAM_CATEGORY_ORDER if _translate_v(c) in params_by_category] + [c for c in params_by_category if c not in [_translate_v(cat) for cat in V_PARAM_CATEGORY_ORDER]]
    #
    #             for cat_zh in category_order_zh:
    #                  line_parts.append(f"    - [{cat_zh}] {', '.join(params_by_category[cat_zh])}")
    #         else:
    #             line_parts.append("    - [無特定診斷標籤]")
    #         report_lines.append("\n".join(line_parts))
    report_lines.append("")

    # --- Section 4: 正確但低效分析 --- #
    report_lines.append("**4. 正確但低效分析**")
    cr_slow_correct = ch4.get('cr_correct_slow', {})
    rc_slow_correct = ch4.get('rc_correct_slow', {})
    slow_correct_found = False
    if cr_slow_correct and cr_slow_correct.get('correct_slow_count', 0) > 0:
        count = cr_slow_correct['correct_slow_count']
        rate = _format_rate(cr_slow_correct.get('correct_slow_rate', 'N/A'))
        avg_diff_val = cr_slow_correct.get('avg_difficulty_slow', None)
        avg_time_val = cr_slow_correct.get('avg_time_slow', None)
        avg_diff = f"{avg_diff_val:.2f}" if avg_diff_val is not None else 'N/A'
        avg_time = f"{avg_time_val:.2f}" if avg_time_val is not None else 'N/A'
        bottleneck = _translate_v(cr_slow_correct.get('dominant_bottleneck_type', 'N/A'))
        report_lines.append(f"- CR: {count} 題正確但慢 (佔比 {rate})。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。主要瓶頸: {bottleneck}。")
        slow_correct_found = True
    if rc_slow_correct and rc_slow_correct.get('correct_slow_count', 0) > 0:
        count = rc_slow_correct['correct_slow_count']
        rate = _format_rate(rc_slow_correct.get('correct_slow_rate', 'N/A'))
        avg_diff_val = rc_slow_correct.get('avg_difficulty_slow', None)
        avg_time_val = rc_slow_correct.get('avg_time_slow', None)
        avg_diff = f"{avg_diff_val:.2f}" if avg_diff_val is not None else 'N/A'
        avg_time = f"{avg_time_val:.2f}" if avg_time_val is not None else 'N/A'
        bottleneck = _translate_v(rc_slow_correct.get('dominant_bottleneck_type', 'N/A'))
        report_lines.append(f"- RC: {count} 題正確但慢 (佔比 {rate})。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。主要瓶頸: {bottleneck}。")
        slow_correct_found = True
    if not slow_correct_found:
        report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 作答模式觀察 --- #
    report_lines.append("**5. 作答模式觀察**")
    early_rushing_flag = bool(ch5.get('early_rushing_flag_for_review', False))
    carelessness_issue = bool(ch5.get('carelessness_issue', False))
    fast_wrong_rate = ch5.get('fast_wrong_rate')
    pattern_found = False
    if early_rushing_flag:
         early_rush_param_translated = _translate_v('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
         report_lines.append(f"- **提示:** {early_rush_param_translated} - 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏。")
         pattern_found = True
    if carelessness_issue:
        careless_param_translated = _translate_v('BEHAVIOR_CARELESSNESS_ISSUE')
        fast_wrong_rate_str = _format_rate(fast_wrong_rate) if fast_wrong_rate is not None else "N/A"
        report_lines.append(f"- **提示:** {careless_param_translated} - 分析顯示，「快而錯」的情況佔比較高 ({fast_wrong_rate_str})，提示可能需關注答題仔細程度。")
        pattern_found = True
    if not pattern_found:
        report_lines.append("- 未發現明顯的特殊作答模式。")
    report_lines.append("")

    # --- Section 6: 基礎鞏固提示 --- #
    report_lines.append("**6. 基礎鞏固提示**")
    override_triggered = ch6.get('skill_override_triggered', {}) # Use result from _calculate_skill_override
    triggered_skills = [s for s, triggered in override_triggered.items() if bool(triggered)]
    if not override_triggered:
         report_lines.append("- 無法進行技能覆蓋分析 (可能缺少數據或計算錯誤)。")
    elif triggered_skills:
        triggered_skills_zh = [_translate_v(s) for s in sorted(triggered_skills)]
        report_lines.append(f"- **以下核心技能整體表現顯示較大提升空間 (錯誤率 > 50%)，建議優先系統性鞏固:** {', '.join(triggered_skills_zh)}")
    else:
        report_lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    report_lines.append("")

    # --- Section 7: 練習計劃呈現 --- #
    report_lines.append("**7. 練習計劃**")
    if ch7: # Check if recommendations exist
        for rec in ch7:
             rec_type = rec.get('type')
             rec_text = rec.get('text', '')
             if rec_type == 'skill_header' or rec_type == 'spacer':
                 report_lines.append(rec_text)
             elif rec_type == 'macro' or rec_type == 'case':
                 # Add indentation for list items
                 report_lines.append(f"- {rec_text}")
             # Add handling for behavioral if implemented
             elif rec_type == 'behavioral':
                 report_lines.append(f"- {rec_text}")
    else:
        report_lines.append("- 無具體練習建議生成 (可能因所有技能均豁免或無觸發項)。")
    report_lines.append("")

    # --- Section 8: 後續行動指引 --- #
    report_lines.append("**8. 後續行動指引**")
    param_to_positions = {}
    skill_to_positions = {}
    performance_to_skills = {
        'Fast & Wrong': set(), 'Slow & Wrong': set(),
        'Normal Time & Wrong': set(), 'Slow & Correct': set()
    }
    if all_problem_items:
        for item in all_problem_items:
            pos = item.get('position')
            skill = item.get('skill')
            params = item.get('params', [])
            performance = item.get('performance')
            if pos is not None and pos != 'N/A':
                if skill and skill != 'Unknown Skill':
                    skill_to_positions.setdefault(skill, set()).add(pos)
                for p in params:
                    param_to_positions.setdefault(p, set()).add(pos)
                if performance in performance_to_skills and skill and skill != 'Unknown Skill':
                    performance_to_skills[performance].add(skill)
    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for skill in skill_to_positions: skill_to_positions[skill] = sorted(list(skill_to_positions[skill]))

    triggered_params_all = set()
    diagnosed_df_ch3 = ch3.get('diagnosed_dataframe') # Re-get df
    if diagnosed_df_ch3 is not None and not diagnosed_df_ch3.empty and 'diagnostic_params' in diagnosed_df_ch3.columns:
         all_param_lists = diagnosed_df_ch3['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])
         triggered_params_all.update(p for sublist in all_param_lists for p in sublist)
    if bool(ch5.get('early_rushing_flag_for_review', False)): triggered_params_all.add('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    if bool(ch5.get('carelessness_issue', False)): triggered_params_all.add('BEHAVIOR_CARELESSNESS_ISSUE')

    # Guide Reflection
    report_lines.append("- **引導反思:**")
    reflection_prompts = []
    def get_pos_context(param_keys):
        positions = set().union(*(param_to_positions.get(key, set()) for key in param_keys))
        return f" (涉及題號: {sorted(list(positions))})" if positions else ""
    logic_params = [...] # Same as before
    reading_params = [...] # Same as before
    efficiency_params = [...] # Same as before
    if any(p in triggered_params_all for p in logic_params): reflection_prompts.append("  - 回想一下，在做錯的相關題目時，具體是卡在哪个推理步驟、邏輯關係或選項辨析上？是完全沒思路，還是思路有偏差？" + get_pos_context(logic_params))
    if any(p in triggered_params_all for p in reading_params): reflection_prompts.append("  - 對於做錯的題目，是文章/題幹的關鍵信息沒讀懂、讀漏，還是題目要求理解錯誤？定位信息是否存在困難？" + get_pos_context(reading_params))
    if any(p in triggered_params_all for p in efficiency_params): reflection_prompts.append("  - 回想耗時過長的題目，是閱讀花了太長時間，邏輯分析卡住，還是選項比較難以排除？" + get_pos_context(efficiency_params))
    if 'BEHAVIOR_CARELESSNESS_ISSUE' in triggered_params_all:
        fw_positions = set().union(*(param_to_positions.get(key, set()) for key in ['CR_READING_BASIC_OMISSION', 'BEHAVIOR_CARELESSNESS_ISSUE'])) # Link carelessness flag to positions
        fw_context = f" (例如題號: {sorted(list(fw_positions))})" if fw_positions else ""
        reflection_prompts.append("  - 回想一下，是否存在因為看錯字、忽略細節或誤解選項導致的失誤？" + fw_context)
    if not reflection_prompts: reflection_prompts.append("  - (本次分析未觸發典型的反思問題，建議結合練習計劃進行)")
    report_lines.extend(reflection_prompts)

    # Secondary Evidence Suggestion
    report_lines.append("- **二級證據參考建議:**")
    review_prompt = ""
    if secondary_evidence_trigger:
        review_prompt = "  - 本次分析識別出部分問題可能需要您查看近期的練習記錄以深入了解。當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題。"
        performance_order = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct']
        details_added = False
        for perf_key in performance_order:
            skills = performance_to_skills.get(perf_key)
            if skills:
                sorted_skills_zh = [_translate_v(s) for s in sorted(list(skills))]
                perf_zh = _translate_v(perf_key)
                review_prompt += f"\n  - **{perf_zh}:** 需關注技能：【{', '.join(sorted_skills_zh)}】。"
                details_added = True
        if not details_added:
            review_prompt += " (本次分析未聚焦到特定的問題技能分類) "
        review_prompt += " 歸納是哪些知識點或題型（參考報告中的描述）導致問題。 如果樣本不足，請在接下來的做題中注意收集。"
    else:
        review_prompt = "  - (本次分析未觸發需要參考二級證據的特定問題模式)"
    report_lines.append(review_prompt)

    # Qualitative Analysis Suggestion
    report_lines.append("- **質化分析建議:**")
    qual_trigger_text = ""
    if qualitative_analysis_trigger:
        qual_triggers = []
        logic_params_for_qual = ['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY', 'RC_REASONING_INFERENCE_WEAKNESS']
        reading_params_for_qual = ['RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY']
        if any(p in triggered_params_all for p in logic_params_for_qual): qual_triggers.append("複雜邏輯推理")
        if any(p in triggered_params_all for p in reading_params_for_qual): qual_triggers.append("複雜閱讀理解")
        if qual_triggers: qual_trigger_text = f"(特別是涉及{ ' 或 '.join(qual_triggers)}過程時) "
        report_lines.append(f"  - 如果您對診斷報告指出的錯誤原因感到困惑，{qual_trigger_text}或者當您無法準確回憶錯誤原因且二級證據幫助有限時，可以嘗試提供 2-3 題相關類型題目的詳細解題流程跟思路範例（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")
    else:
        report_lines.append("  - (本次分析未觸發需要進行質化分析的特定問題)")

    # Tool Recommendations
    report_lines.append("- **輔助工具與 AI 提示推薦 (基於本次診斷觸發的標籤):**")
    # --- Comprehensive Tool Recommendation Map (Based on MD Ch8.7) ---
    tool_recommendations_map = {
        # CR Reasoning & Specific Types
        frozenset(['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']):
            "可能適用外部工具 `Dustin_GMAT_CR_Core_Issue_Identifier` 或 `Dustin_GMAT_CR_Chain_Argument_Evaluation`；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_METHOD_TYPE_SPECIFIC_ERROR']):
            "特定 CR 題型方法錯誤 (如 Boldface, Argument Construction)，可能適用外部工具 `Dustin\'s GMAT CR: Boldface Interactive Tutor` (Boldface) 或 `Dustin_GMAT_CR_Role_Argument_Construction` (Argument Construction)；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_REASONING_ABSTRACTION_DIFFICULTY']):
            "CR 抽象邏輯或術語理解困難，可能適用外部工具 `Dustin\'s GMAT Tool: Textbook Explainer`；或使用 AI 提示 `Verbal-related/07_logical_term_explained.md`, `Verbal-related/09_complex_sentence_rewrite.md`。",
        frozenset(['CR_READING_BASIC_OMISSION']):
            "CR 基礎理解疏漏，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`。",
        frozenset(['CR_READING_DIFFICULTY_STEM']):
            "CR 題幹理解障礙，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`, `Verbal-related/09_complex_sentence_rewrite.md`。",
        frozenset(['CR_READING_TIME_EXCESSIVE']):
            "CR 閱讀耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/03_quick_rc_tricks.md`。",
        frozenset(['CR_QUESTION_UNDERSTANDING_MISINTERPRETATION']):
            "CR 提問要求把握錯誤，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`。",
        frozenset(['CR_REASONING_PREDICTION_ERROR']):
            "CR 預判方向錯誤或缺失，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`。",
        frozenset(['CR_REASONING_TIME_EXCESSIVE']):
            "CR 邏輯思考耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/05_evaluate_explanation.md`。",
        frozenset(['CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY']):
            "CR 選項本身理解困難，可使用 AI 提示 `Verbal-related/07_logical_term_explained.md`, `Verbal-related/01_basic_explanation.md`。",
        frozenset(['CR_AC_ANALYSIS_RELEVANCE_ERROR']):
            "CR 選項相關性判斷錯誤，可使用 AI 提示 `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_AC_ANALYSIS_DISTRACTOR_CONFUSION']):
            "CR 強干擾選項混淆，可能適用外部工具 `Dustin_GMAT_Verbal_Distractor_Mocker`；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`。",
        frozenset(['CR_AC_ANALYSIS_TIME_EXCESSIVE']):
            "CR 選項篩選耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_METHOD_PROCESS_DEVIATION']):
            "CR 未遵循標準流程，可使用 AI 提示 `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",

        # RC Reading Comprehension
        frozenset(['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_READING_COMPREHENSION_BARRIER']):
            "RC 基礎閱讀速度慢或存在障礙，可能適用外部工具 `Dustin GMAT: Chunk Reading Coach`；或使用 AI 提示 `Verbal-related/03_quick_rc_tricks.md`。",
        frozenset(['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'reading_comprehension_barrier_inquiry']): # Example: Combine param with Ch1 flag
            "RC 基礎閱讀速度慢，可能適用外部工具 `Dustin GMAT: Chunk Reading Coach` 或 AI 提示 `Verbal-related/03_quick_rc_tricks.md`。",
        frozenset(['RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP', 'RC_READING_VOCAB_BOTTLENECK']): # Non-systemic vocab
            "RC 長難句/領域知識/非系統性詞彙瓶頸，可能適用外部工具 `Dustin's GMAT Terminator: Sentence Cracker` 或相關 AI 提示。",
        frozenset(['RC_READING_VOCAB_BOTTLENECK']): # Systemic vocab (needs logic to differentiate)
            "RC 詞彙量瓶頸 (需系統性學習)，可能適用外部工具 `Dustin's GMAT Core: Vocab Master`。",
        frozenset(['RC_READING_PRECISION_INSUFFICIENT']):
            "RC 閱讀精度不足，可能適用外部工具 `Dustin GMAT Close Reading Coach` 或 AI 提示。",
        frozenset(['RC_READING_PASSAGE_STRUCTURE_DIFFICULTY']):
            "RC 篇章結構把握不清，可能適用外部工具 `Dustin_GMAT_RC_Passage_Analyzer` 或 AI 提示。",

        # Distractors/Carelessness
        frozenset(['CR_AC_ANALYSIS_DISTRACTOR_CONFUSION', 'RC_AC_ANALYSIS_DIFFICULTY', 'BEHAVIOR_CARELESSNESS_ISSUE']):
            "選項辨析困難或粗心問題，可能適用外部工具 `Dustin_GMAT_Verbal_Distractor_Mocker` 或相關 AI 提示。",

        # Foundational Mastery
        frozenset(['FOUNDATIONAL_MASTERY_INSTABILITY_SFE']):
            "基礎掌握不穩定 (SFE)，建議優先使用 AI 提示 `Verbal-related/01_basic_explanation.md` 鞏固基礎。",

        # Behavioral
        frozenset(['BEHAVIOR_EARLY_RUSHING_FLAG_RISK']):
            "前期作答過快，建議使用 AI 提示 `Verbal-related/05_evaluate_explanation.md` 反思節奏。",
        frozenset(['BEHAVIOR_GUESSING_HASTY']):
            "疑似猜題/倉促，建議使用 AI 提示 `Verbal-related/01_basic_explanation.md` 學習完整步驟。",
    }

    # Generate tool recommendations based on triggered params (Q-like format)
    processed_for_tools = set()
    recommendations_made = False
    # Split tools and prompts
    recommended_tools = set() # Use sets to avoid duplicates initially
    recommended_prompts_map = {} # Keep this as dict to store reasons

    for params_set, tool_desc in tool_recommendations_map.items():
        if any(p in triggered_params_all for p in params_set) and not params_set.issubset(processed_for_tools):
            trigger_reasons_translated = [_translate_v(p) for p in params_set if p in triggered_params_all]
            if trigger_reasons_translated:
                # Extract tool names and prompt names using precise patterns
                import re
                # Step 1: Find all items within backticks
                all_backticked_items = re.findall(r'`([^`]+?)`', tool_desc)
                
                # Step 2: Filter into tools (not ending in .md) and prompts (ending in .md)
                current_tools = {item for item in all_backticked_items if not item.endswith('.md') and item.strip()}
                current_prompts = {item for item in all_backticked_items if item.endswith('.md')}
                
                # # Match `Dustin...` or other potential tool names NOT ending in .md (OLD LOGIC)
                # tools = re.findall(r'`([^`]+?)(?<!\\.md)`', tool_desc)
                # # Match patterns like `Verbal-related/... .md` (OLD LOGIC)
                # prompts = re.findall(r'`((?:Verbal-related/|\\w+/)[^`]+\\.md)`', tool_desc) # Allow other potential paths ending in .md

                if current_tools:
                    recommended_tools.update(current_tools) # Add to set
                    recommendations_made = True
                if current_prompts:
                    for prompt in current_prompts:
                        # Store reasons for each prompt
                        if prompt not in recommended_prompts_map:
                            recommended_prompts_map[prompt] = set()
                        recommended_prompts_map[prompt].update(trigger_reasons_translated)
                    recommendations_made = True

                processed_for_tools.update(params_set)

    # Report Tools
    if recommended_tools:
         report_lines.append("  - 工具:")
         # Sort the set before reporting
         for tool in sorted(list(recommended_tools)):
             report_lines.append(f"    - `{tool}`")

    # Report Prompts
    if recommended_prompts_map:
        report_lines.append("  - AI提示:")
        for prompt in sorted(recommended_prompts_map.keys()):
            # reasons = ", ".join(sorted(list(recommended_prompts_map[prompt])))
            # report_lines.append(f"    - `{prompt}` (基於: {reasons})") # Option to show reasons
            report_lines.append(f"    - `{prompt}`")

    # Fallback message
    if not recommendations_made:
         report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議)")

    report_lines.append("\n--- 報告結束 ---")
    print("DEBUG: --- Exiting _generate_v_summary_report ---") # DEBUG
    # Use double newline for Markdown paragraph breaks
    return "\n\n".join(report_lines)

# --- V Recommendation Generation Helper ---

def _generate_v_recommendations(v_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on V diagnosis results,
       applying skill exemption rules.
    """
    print(f"DEBUG: +++ Entering _generate_v_recommendations (Exempted: {exempted_skills}) +++") # DEBUG
    recommendations = []
    processed_macro_skills = set() # Keep track of skills covered by macro recs

    # Extract relevant results safely
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {}) # Now contains skill_override_triggered
    # Removed: ch7 = v_diagnosis_results.get('chapter_7', []) # This should be the output, not input

    # Get Ch6 override results
    skill_override_triggered = ch6.get('skill_override_triggered', {})

    # Get Ch3 diagnosed dataframe (needed for iterating problems)
    diagnosed_df = v_diagnosis_results.get('chapter_3', {}).get('diagnosed_dataframe')

    # Initialize recommendations structure
    recommendations_by_skill = {} # Store recommendations keyed by skill
    all_skills_found = set() # Keep track of all unique skills encountered in diagnostic data

    # 1. Identify all skills from diagnostic parameters in Ch3
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
        # Also consider skills from correct-slow if needed for completeness (Ch4 data)
        # For now, primarily focus on skills associated with diagnostic triggers (errors/SFE/slow)
        # Extract unique skills from the 'diagnostic_params' which now holds the triggers
        for params_list in diagnosed_df['diagnostic_params']:
            # Need to associate params back to skill - iterate through df instead?
            pass # Placeholder - Need a better way to get all relevant skills

        # Iterate through the diagnosed dataframe to get skills associated with problems
        # This is complex because params are stored, not the original triggers. Rethink approach.

        # Alternative: Get skills from Ch3 error records and Ch4 correct-slow records
        if ch3:
            cr_errors = ch3.get('cr_error_analysis', {}).get('error_records', [])
            rc_errors = ch3.get('rc_error_analysis', {}).get('error_records', [])
            for err in cr_errors + rc_errors:
                 skill = err.get('question_skill')
                 if skill and skill != 'Unknown Skill': all_skills_found.add(skill)
        if ch4:
            cr_slow = ch4.get('cr_correct_slow', {}).get('skill_breakdown_slow', {})
            rc_slow = ch4.get('rc_correct_slow', {}).get('skill_breakdown_slow', {})
            all_skills_found.update(cr_slow.keys())
            all_skills_found.update(rc_slow.keys())
            # Filter out 'Unknown Skill' if it snuck in
            all_skills_found.discard('Unknown Skill')

    # 2. Generate Recommendations (Macro then Case)
    for skill in all_skills_found:
        # --- APPLY EXEMPTION RULE (Task 3) ---
        if skill in exempted_skills:
            print(f"      Skipping recommendations for exempted skill: {skill}")
            continue # Skip generating any recommendation for this skill
        # --- END EXEMPTION RULE ---

        skill_recs_list = []
        # Check for override rule based on the results passed in v_diagnosis_results
        is_overridden = ch6.get('skill_override_triggered', {}).get(skill, False)
        print(f"      Processing Skill: {skill}, Overridden: {is_overridden}")

        if is_overridden and skill not in processed_macro_skills:
            # Generate Macro Recommendation (V-Doc Ch7)
            macro_rec_text = f"針對【{skill}】技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_macro_skills.add(skill)
            print(f"      Generated MACRO recommendation for Skill: {skill}")

        elif not is_overridden:
            # Generate Case-Specific Recommendations for this skill
            # Find relevant rows in diagnosed_df for this skill
            if diagnosed_df is not None and not diagnosed_df.empty:
                skill_rows = diagnosed_df[diagnosed_df['question_fundamental_skill'] == skill]
                for index, row in skill_rows.iterrows():
                    # Check if this row triggered a recommendation (Error, SFE, Correct-Slow)
                    # Need logic to determine if *this specific row* was a trigger
                    # This requires linking back params to original triggers - difficult with current structure
                    # Simplified: Generate case rec if error or slow (overtime=True)
                    is_error = not row['is_correct']
                    q_type = row['question_type']
                    # 判斷是否慢 (is_slow): (CR: overtime == True; RC: group_overtime == True 或 individual_overtime == True)
                    if q_type == 'Critical Reasoning':
                        is_slow = row.get('overtime', False)
                    else:  # Reading Comprehension
                        is_slow = row.get('group_overtime', False) or row.get('individual_overtime', False)
                    is_sfe = row.get('is_sfe', False)
                    q_pos = row['question_position']
                    difficulty = row.get('question_difficulty')
                    time = row.get('question_time')

                    # Only generate case rec if it was an error or correct-slow
                    if is_error or (row['is_correct'] and is_slow):
                        # Determine Y and Z (V-Doc Ch7)
                        y = _grade_difficulty_v(difficulty)
                        target_time = 2.0 if q_type == 'Critical Reasoning' else 1.5
                        base_time = time - 0.5 if is_slow and time is not None else time
                        if base_time is not None and not pd.isna(base_time):
                             z_raw = math.floor(base_time * 2) / 2 # Floor to nearest 0.5
                             z = max(z_raw, target_time)
                        else:
                             z = target_time # Default if time is missing

                        # Build text
                        trigger_desc = "基礎掌握不穩" if is_sfe else ("慢" if is_slow else "錯")
                        case_rec_text = f"針對【{skill}】下的問題 (Position {q_pos}, {trigger_desc})：建議練習【{y}】難度題目，起始練習限時建議為【{z:.1f}】分鐘。(目標時間：{'CR 2.0 / RC 1.5'}分鐘)。"
                        priority = 1 if is_sfe else (2 if is_error else 3) # SFE > Error > Slow

                        # Add volume alert if Z is much higher than target
                        if (z - target_time) > 2.0:
                            case_rec_text += " **需加大練習量以確保逐步限時有效**。"

                        skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})

        # Add recommendations for this skill to the main dict
        if skill_recs_list:
             recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # 3. Assemble Final List (excluding behavioral for now)
    final_recommendations = []
    # Removed exemption logic

    # Sort skills: Macro skills first, then alphabetically
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_macro_skills else 1, s))

    for skill in sorted_skills:
        recs = recommendations_by_skill[skill]
        final_recommendations.append({'type': 'skill_header', 'text': f"--- 技能: {skill} ---"}) # Add header as dict item
        final_recommendations.extend(recs) # Add list of rec dicts
        final_recommendations.append({'type': 'spacer', 'text': ""}) # Add spacer as dict item

    # 4. Add Behavioral Recommendations (from Ch5)
    # ... (Keep existing behavioral recommendation logic) ...

    print("DEBUG: --- Exiting _generate_v_recommendations ---") # DEBUG
    return final_recommendations

# --- RC Helper Functions (for Chapter 1 logic) ---

def _identify_rc_groups(df_v):
    """Identifies RC passages groups based on consecutive question positions."""
    if 'question_type' not in df_v.columns or 'question_position' not in df_v.columns:
        return df_v

    df_v = df_v.sort_values('question_position').copy()
    df_v['rc_group_id'] = np.nan

    rc_indices = df_v[df_v['question_type'] == 'RC'].index
    if not rc_indices.any():
        return df_v # No RC questions

    group_counter = 0
    current_group_id = np.nan
    last_pos = -2

    for idx in df_v.index:
        row = df_v.loc[idx]
        if row['question_type'] == 'RC':
            if row['question_position'] != last_pos + 1:
                # Start of a new group
                group_counter += 1
                current_group_id = f"RC_Group_{group_counter}"
            df_v.loc[idx, 'rc_group_id'] = current_group_id
            last_pos = row['question_position']
        else:
            # Reset group logic if non-RC question encountered
            current_group_id = np.nan
            last_pos = -2

    # Validate group sizes (Warn if > 4)
    if 'rc_group_id' in df_v.columns:
        group_sizes = df_v.dropna(subset=['rc_group_id']).groupby('rc_group_id').size()
        oversized_groups = group_sizes[group_sizes > 4].index.tolist()
        if oversized_groups:
             print(f"    Warning: RC groups detected with > 4 questions, manual check recommended: {oversized_groups}")

    return df_v

def _calculate_rc_times(df_v):
    """Calculates RC group total time and estimated reading time."""
    if 'rc_group_id' not in df_v.columns or df_v['rc_group_id'].isnull().all():
        df_v['rc_group_total_time'] = np.nan
        df_v['rc_reading_time'] = np.nan
        return df_v

    # Calculate group total time
    group_times = df_v[df_v['question_type'] == 'RC'].groupby('rc_group_id')['question_time'].sum()
    df_v['rc_group_total_time'] = df_v['rc_group_id'].map(group_times)

    # Calculate reading time (first q time - avg time of others)
    df_v['rc_reading_time'] = np.nan
    df_rc_only = df_v[df_v['question_type'] == 'RC'].copy()

    for group_id, group_df in df_rc_only.groupby('rc_group_id'):
        group_df_sorted = group_df.sort_values('question_position')
        first_q_index = group_df_sorted.index[0]
        if len(group_df_sorted) > 1:
            first_q_time = group_df_sorted['question_time'].iloc[0]
            other_q_times_avg = group_df_sorted['question_time'].iloc[1:].mean()
            reading_time = first_q_time - other_q_times_avg
            # Assign reading time only to the first question of the group
            df_v.loc[first_q_index, 'rc_reading_time'] = reading_time
        # If only 1 question in group, reading_time remains NaN

    return df_v

# --- Helper for Applying Chapter 3 Rules ---

def _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill, avg_time_per_type):
    """Applies Chapter 3 diagnostic rules row-by-row based on gmat-v-score-logic-dustin-v1.2.md.
       Assigns detailed diagnostic parameters based on Verbal Doc Appendix A.
       Adds 'diagnostic_params', 'is_sfe', 'is_relatively_fast', and 'time_performance_category' columns.
       'is_relatively_fast' uses the 0.75 * avg time threshold.
    """
    if df_v.empty:
        df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
        df_v['is_sfe'] = False
        df_v['is_relatively_fast'] = False # Changed name
        df_v['time_performance_category'] = ''
        return df_v

    # Initialize columns first
    if 'diagnostic_params' not in df_v.columns: df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    if 'is_sfe' not in df_v.columns: df_v['is_sfe'] = False
    if 'is_relatively_fast' not in df_v.columns: df_v['is_relatively_fast'] = False # Changed name
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''

    max_diff_dict = max_correct_difficulty_per_skill

    all_params = []
    all_sfe = []
    all_fast_flags = []
    all_time_categories = []

    for index, row in df_v.iterrows():
        q_type = row['question_type'] # CR or RC
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime_combined = bool(row.get('overtime', False)) # This is the combined OT flag from Ch1
        # RC specific flags for detailed bottleneck analysis (Used in Ch1/upstream, may be relevant contextually)
        # is_rc_reading_overtime = bool(row.get('rc_reading_overtime', False))
        # is_rc_single_q_overtime = bool(row.get('rc_single_q_overtime', False))

        current_params = []
        current_is_sfe = False
        current_is_relatively_fast = False # Renamed
        current_time_performance_category = 'Unknown'

        # 1. Check SFE (only if incorrect)
        if not is_correct and q_diff is not None and not pd.isna(q_diff):
            max_correct_diff = max_diff_dict.get(q_skill, -np.inf)
            if q_diff < max_correct_diff:
                current_is_sfe = True
                # Add SFE param immediately if SFE is triggered
                current_params.append('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 2. Determine Time Flags (is_slow uses combined flag)
        is_slow = is_overtime_combined # Use the combined flag from Ch1
        avg_time = avg_time_per_type.get(q_type, 1.8) # Default V avg ~1.8 min? Default should be safe

        is_normal_time = False # Flag for normal time
        if q_time is not None and not pd.isna(q_time):
            # Check for relatively fast using the 0.75 threshold (MD Ch3)
            if q_time < (avg_time * 0.75):
                current_is_relatively_fast = True
            # Check for Hasty/Guessing using the absolute threshold (MD Ch3 & App A)
            if q_time < HASTY_GUESSING_THRESHOLD_MINUTES:
                 current_params.append('BEHAVIOR_GUESSING_HASTY') # Add param if hasty

            # Determine if normal time (not fast and not slow)
            if not current_is_relatively_fast and not is_slow:
                 is_normal_time = True

        # 3. Assign Time Performance Category (Based on MD Ch3 definitions)
        if is_correct:
            if current_is_relatively_fast:
                current_time_performance_category = 'Fast & Correct'
            elif is_slow:
                current_time_performance_category = 'Slow & Correct'
            else: # is_normal_time or (q_time is None) - default to normal if time is missing
                current_time_performance_category = 'Normal Time & Correct'
        else: # Incorrect
            if current_is_relatively_fast:
                current_time_performance_category = 'Fast & Wrong'
            elif is_slow:
                current_time_performance_category = 'Slow & Wrong'
            else: # is_normal_time or (q_time is None)
                current_time_performance_category = 'Normal Time & Wrong'

        # --- Start Refactored Parameter Assignment based on Markdown Ch3 ---
        # 4. Assign DETAILED Diagnostic Params based on MD Ch3 Time/Accuracy/Type categories
        if q_type == 'Critical Reasoning':
            if current_time_performance_category == 'Fast & Wrong':
                current_params.extend([
                    'CR_METHOD_PROCESS_DEVIATION',
                    'CR_METHOD_TYPE_SPECIFIC_ERROR', # Note: MD says "需註明題型" - code cannot do this directly
                    'CR_READING_BASIC_OMISSION'
                ])
                # BEHAVIOR_GUESSING_HASTY already added if applicable in step 2
            elif current_time_performance_category == 'Normal Time & Wrong':
                current_params.extend([
                    'CR_READING_DIFFICULTY_STEM',
                    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'CR_REASONING_CHAIN_ERROR',
                    'CR_REASONING_ABSTRACTION_DIFFICULTY',
                    'CR_REASONING_PREDICTION_ERROR',
                    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY',
                    'CR_AC_ANALYSIS_RELEVANCE_ERROR',
                    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION',
                    'CR_METHOD_TYPE_SPECIFIC_ERROR' # Note: MD says "需註明題型"
                ])
                # SFE param already added if applicable in step 1
            elif current_time_performance_category == 'Slow & Wrong':
                # Explicit time-related params for Slow & Wrong CR
                current_params.extend([
                    'CR_READING_TIME_EXCESSIVE',
                    'CR_REASONING_TIME_EXCESSIVE',
                    'CR_AC_ANALYSIS_TIME_EXCESSIVE'
                ])
                # Add potential underlying causes from 'Normal Time & Wrong' list (as per MD "同時可能包含...")
                current_params.extend([
                    'CR_READING_DIFFICULTY_STEM',
                    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'CR_REASONING_CHAIN_ERROR',
                    'CR_REASONING_ABSTRACTION_DIFFICULTY',
                    'CR_REASONING_PREDICTION_ERROR',
                    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY',
                    'CR_AC_ANALYSIS_RELEVANCE_ERROR',
                    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION',
                    'CR_METHOD_TYPE_SPECIFIC_ERROR' # Note: MD says "需註明題型"
                ])
                # SFE param already added if applicable in step 1
            elif current_time_performance_category == 'Slow & Correct':
                # Efficiency bottlenecks for Slow & Correct CR (MD Ch3)
                current_params.extend([
                    'EFFICIENCY_BOTTLENECK_READING',
                    'EFFICIENCY_BOTTLENECK_REASONING',
                    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS'
                ])
            # Cases 'Fast & Correct' and 'Normal Time & Correct' don't add specific params per MD Ch3

        elif q_type == 'Reading Comprehension':
            if current_time_performance_category == 'Fast & Wrong':
                current_params.extend([
                    'RC_READING_INFO_LOCATION_ERROR',
                    'RC_READING_KEYWORD_LOGIC_OMISSION',
                    'RC_METHOD_TYPE_SPECIFIC_ERROR' # Note: MD says "需註明題型"
                ])
                # BEHAVIOR_GUESSING_HASTY already added if applicable in step 2
            elif current_time_performance_category == 'Normal Time & Wrong':
                current_params.extend([
                    'RC_READING_VOCAB_BOTTLENECK',
                    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY',
                    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                    'RC_READING_DOMAIN_KNOWLEDGE_GAP',
                    'RC_READING_PRECISION_INSUFFICIENT',
                    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'RC_LOCATION_ERROR_INEFFICIENCY',
                    'RC_REASONING_INFERENCE_WEAKNESS',
                    'RC_AC_ANALYSIS_DIFFICULTY',
                    'RC_METHOD_TYPE_SPECIFIC_ERROR' # Note: MD says "需註明題型"
                ])
                # SFE param already added if applicable in step 1
            elif current_time_performance_category == 'Slow & Wrong':
                # Explicit time-related params for Slow & Wrong RC
                current_params.extend([
                    'RC_READING_SPEED_SLOW_FOUNDATIONAL',
                    'RC_METHOD_INEFFICIENT_READING',
                    'RC_LOCATION_TIME_EXCESSIVE',
                    'RC_REASONING_TIME_EXCESSIVE',
                    'RC_AC_ANALYSIS_TIME_EXCESSIVE'
                ])
                # Add potential underlying causes from 'Normal Time & Wrong' list (as per MD "同時可能包含...")
                current_params.extend([
                    'RC_READING_VOCAB_BOTTLENECK',
                    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY',
                    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                    'RC_READING_DOMAIN_KNOWLEDGE_GAP',
                    'RC_READING_PRECISION_INSUFFICIENT',
                    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'RC_LOCATION_ERROR_INEFFICIENCY',
                    'RC_REASONING_INFERENCE_WEAKNESS',
                    'RC_AC_ANALYSIS_DIFFICULTY',
                    'RC_METHOD_TYPE_SPECIFIC_ERROR' # Note: MD says "需註明題型"
                ])
                # SFE param already added if applicable in step 1
            elif current_time_performance_category == 'Slow & Correct':
                 # Efficiency bottlenecks for Slow & Correct RC (MD Ch3)
                 current_params.extend([
                    'EFFICIENCY_BOTTLENECK_READING',
                    'EFFICIENCY_BOTTLENECK_LOCATION',
                    'EFFICIENCY_BOTTLENECK_REASONING',
                    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS'
                 ])
            # Cases 'Fast & Correct' and 'Normal Time & Correct' don't add specific params per MD Ch3

        # --- End Refactored Parameter Assignment ---

        # 5. Final Parameter List Cleanup
        # Remove duplicates while preserving order (Python 3.7+) and prioritize SFE
        unique_params = list(dict.fromkeys(current_params))
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
             # Ensure SFE is at the front if present
             unique_params.remove('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
             unique_params.insert(0, 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        all_params.append(unique_params)
        all_sfe.append(current_is_sfe)
        all_fast_flags.append(current_is_relatively_fast) # Renamed list
        all_time_categories.append(current_time_performance_category)

    # Assign lists back to DataFrame
    if len(all_params) == len(df_v):
        df_v['diagnostic_params'] = all_params
        df_v['is_sfe'] = all_sfe
        df_v['is_relatively_fast'] = all_fast_flags # Renamed column
        df_v['time_performance_category'] = all_time_categories
    else:
        print("ERROR: Length mismatch in _apply_ch3_diagnostic_rules. Skipping assignment.")
        # Re-initialize columns on error to prevent downstream issues
        df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
        df_v['is_sfe'] = False
        df_v['is_relatively_fast'] = False
        df_v['time_performance_category'] = ''

    return df_v

# --- Helper to Recalculate Ch3 Error Analysis from Params ---

def _analyze_error_types_from_params(df_errors, question_type):
    """Analyzes error distribution based on Chapter 3 diagnostic parameters."""
    analysis = {
        'total_errors': 0,
        'param_counts': {},
        'dominant_error_type': 'N/A',
        # Add more detailed breakdown if needed based on param categories
    }
    if df_errors.empty or 'diagnostic_params' not in df_errors.columns:
        return analysis

    total_errors = len(df_errors)
    analysis['total_errors'] = total_errors

    all_params = [p for params_list in df_errors['diagnostic_params'] for p in params_list]
    param_counts = pd.Series(all_params).value_counts()
    analysis['param_counts'] = param_counts.to_dict()

    # Determine dominant error type (based on most frequent param, excluding SFE for dominance)
    dominant_param = param_counts.drop('FOUNDATIONAL_MASTERY_INSTABILITY_SFE', errors='ignore').idxmax() if not param_counts.drop('FOUNDATIONAL_MASTERY_INSTABILITY_SFE', errors='ignore').empty else 'N/A'

    # Map dominant param back to a category (Reading, Logic/Grammar, Method, Behavior...)
    # This mapping needs refinement based on the actual params used in _apply_ch3_diagnostic_rules
    if 'READING' in dominant_param:
         analysis['dominant_error_type'] = 'Reading/Understanding'
    elif 'LOGIC' in dominant_param or 'GRAMMAR' in dominant_param:
         analysis['dominant_error_type'] = 'Logic/Grammar/Inference'
    elif 'METHOD' in dominant_param:
         analysis['dominant_error_type'] = 'Method/Process'
    elif 'BEHAVIOR' in dominant_param:
        analysis['dominant_error_type'] = 'Behavioral'
    else:
        analysis['dominant_error_type'] = 'Mixed/Other'

    if analysis['param_counts'].get('FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 0) / total_errors > 0.3:
        analysis['dominant_error_type'] += " (High SFE Anteil)"

    return analysis 

# --- Add Helper Functions needed by Chapter 2 ---
# (Similar to DI's _analyze_dimension)

def _calculate_metrics_for_group(group):
    """Calculates basic metrics for a given group of data."""
    total = len(group)
    errors = group['is_correct'].eq(False).sum() # Use 'is_correct'
    error_rate = errors / total if total > 0 else 0.0
    avg_time_spent = group['question_time'].mean() if 'question_time' in group.columns else 0.0
    avg_difficulty = group['question_difficulty'].mean() if 'question_difficulty' in group.columns else None
    overtime_count = group['overtime'].eq(True).sum() if 'overtime' in group.columns else 0
    overtime_rate = overtime_count / total if total > 0 else 0.0

    return {
        'total_questions': total,
        'errors': errors,
        'error_rate': error_rate,
        'avg_time_spent': avg_time_spent, # minutes
        'avg_difficulty': avg_difficulty,
        'overtime_count': overtime_count,
        'overtime_rate': overtime_rate
    }

def _analyze_dimension(df_filtered, dimension_col):
    """Analyzes performance metrics grouped by a specific dimension column."""
    if df_filtered.empty or dimension_col not in df_filtered.columns:
        return {}

    results = {}
    # Ensure dimension column is suitable for grouping (handle potential NaNs)
    df_filtered[dimension_col] = df_filtered[dimension_col].fillna('Unknown')
    grouped = df_filtered.groupby(dimension_col)

    for name, group in grouped:
        results[name] = _calculate_metrics_for_group(group)
    return results

# --- Helper function for Chapter 6 Override Rule ---

def _calculate_skill_override(df_v):
    """Calculates the skill override trigger based on V-Doc Chapter 6.
       Triggers if a skill's error rate > 50%.
    """
    analysis = {
        'skill_error_rates': {},
        'skill_override_triggered': {}
    }
    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        return analysis

    # Ensure skill column is suitable for grouping
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    skill_groups = df_v.groupby('question_fundamental_skill')

    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue

        total = len(group)
        errors = group['is_correct'].eq(False).sum() # Use 'is_correct'
        error_rate = errors / total if total > 0 else 0.0

        analysis['skill_error_rates'][skill] = error_rate
        analysis['skill_override_triggered'][skill] = error_rate > 0.50

    return analysis

def _grade_difficulty_v(difficulty):
    """
    Grades the difficulty of a question based on V-Doc Chapter 2/7 rules.
    
    Args:
        difficulty (float): The question difficulty value (V_b)
        
    Returns:
        str: The difficulty grade string
    """
    if difficulty is None or pd.isna(difficulty):
        return "Unknown Difficulty"
    
    # V-Doc Ch2/Ch7 difficulty grading
    if difficulty <= -1:
        return "Low / 505+"
    elif -1 < difficulty <= 0:
        return "Mid / 555+"
    elif 0 < difficulty <= 1:
        return "Mid / 605+"
    elif 1 < difficulty <= 1.5:
        return "Mid / 655+"
    elif 1.5 < difficulty <= 1.95:
        return "High / 705+"
    elif 1.95 < difficulty <= 2:
        return "High / 805+"
    else:
        return "Unknown Difficulty"

# --- Helper function for Chapter 6 Exemption Rule ---

def _calculate_skill_exemption_status(df_v):
    """Calculates the set of exempted skills based on V-Doc Chapter 6 Exemption Rule.
       A skill is exempted if all questions under it are correct AND not overtime.
    """
    exempted_skills = set()
    if df_v.empty or 'question_fundamental_skill' not in df_v.columns or \
       'is_correct' not in df_v.columns or 'overtime' not in df_v.columns:
        print("    Warning: Cannot calculate skill exemption (missing required columns).")
        return exempted_skills

    # Ensure skill column is suitable for grouping
    df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')
    skill_groups = df_v.groupby('question_fundamental_skill')

    for skill, group in skill_groups:
        if skill == 'Unknown Skill': continue

        all_correct = group['is_correct'].all()
        no_overtime = not group['overtime'].any()

        if all_correct and no_overtime:
            exempted_skills.add(skill)
            print(f"      Ch6 Exemption: Skill '{skill}' meets exemption criteria (All correct, no overtime).")

    return exempted_skills