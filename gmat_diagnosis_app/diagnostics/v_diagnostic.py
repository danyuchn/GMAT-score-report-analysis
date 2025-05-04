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
# V-Doc defines separate thresholds for abandoned and hasty
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

# --- Main V Diagnosis Entry Point ---

def run_v_diagnosis(df_v_raw, v_time_pressure_status, v_avg_time_per_type):
    """
    DEPRECATED - Logic moved to run_v_diagnosis_processed.
    Runs the diagnostic analysis specifically for the Verbal section.
    PRIORITIZES the 'is_manually_invalid' flag.

    Args:
        df_v_raw (pd.DataFrame): DataFrame with Verbal responses.
        v_time_pressure_status (bool): Time pressure status determined by the main module.
        v_avg_time_per_type (dict): Average times per type calculated by the main module.

    Returns:
        dict: Dictionary containing V diagnosis results.
        str: Summary report string for V.
        pd.DataFrame: Processed V DataFrame with diagnostic columns.
    """
    # This function's core logic is now in run_v_diagnosis_processed
    # It should ideally not be called directly anymore.
    print("WARNING: Calling deprecated run_v_diagnosis. Preprocessing should happen upstream.")

    # Simulate the preprocessing step here for compatibility, although it shouldn't be needed
    time_pressure_status_map = {'V': v_time_pressure_status} # Use passed-in pressure
    from gmat_diagnosis_app.preprocess_helpers import suggest_invalid_questions
    df_v_preprocessed = suggest_invalid_questions(df_v_raw, time_pressure_status_map)

    return run_v_diagnosis_processed(df_v_preprocessed, v_time_pressure_status, v_avg_time_per_type)


def run_v_diagnosis_processed(df_v_processed, v_time_pressure_status, v_avg_time_per_type):
    """
    Runs the diagnostic analysis for Verbal using a preprocessed DataFrame.
    Assumes 'is_invalid' column reflects the final status after user review.

    Args:
        df_v_processed (pd.DataFrame): DataFrame with Verbal responses, preprocessed with 'is_invalid'.
        v_time_pressure_status (bool): Time pressure status for V.
        v_avg_time_per_type (dict): Average times per type calculated by the main module.

    Returns:
        dict: Dictionary containing V diagnosis results.
        str: Summary report string for V.
        pd.DataFrame: Processed V DataFrame with diagnostic columns.
    """
    print("  Running Verbal Diagnosis...")
    v_diagnosis_results = {}

    if df_v_processed.empty:
        print("    No V data provided. Skipping V diagnosis.")
        return {}, "Verbal (V) 部分無數據可供診斷。", pd.DataFrame()

    df_v = df_v_processed.copy() # Use the processed dataframe

    # --- DEBUG: Check incoming overtime status ---
    if 'overtime' in df_v.columns:
        print(f"  DEBUG V Diag: Incoming df_v overtime counts:\n{df_v['overtime'].value_counts()}")
    else:
        print("  DEBUG V Diag: Incoming df_v MISSING 'overtime' column!")
    if 'is_invalid' in df_v.columns:
         print(f"  DEBUG V Diag: Incoming df_v is_invalid counts:\n{df_v['is_invalid'].value_counts()}")
    # --- END DEBUG ---

    # --- Initialize/Prepare Columns ---
    # Ensure necessary columns exist
    required_cols = ['question_position', 'question_time', 'is_correct', 'question_type', 'question_fundamental_skill']
    missing_cols = [col for col in required_cols if col not in df_v.columns]
    if missing_cols:
        print(f"    Warning (V Diagnosis): Missing required columns: {missing_cols}. Analysis may be incomplete.")
        if 'question_fundamental_skill' not in df_v.columns: df_v['question_fundamental_skill'] = 'Unknown Skill'

    # Convert types
    df_v['question_time'] = pd.to_numeric(df_v['question_time'], errors='coerce')
    df_v['question_position'] = pd.to_numeric(df_v['question_position'], errors='coerce')
    if 'is_correct' in df_v.columns:
        df_v['is_correct'] = df_v['is_correct'].astype(bool)
    else:
        print("    Warning (V Diagnosis): 'is_correct' column missing.")
        df_v['is_correct'] = True # Assume correct if missing?

    # --- Manual Invalid Flag is handled in preprocessing ---
    # Ensure 'is_invalid' exists from preprocessing
    if 'is_invalid' not in df_v.columns:
        print("ERROR: 'is_invalid' column missing in df_v_processed!")
        df_v['is_invalid'] = False # Add default if missing

    # --- Initialize other diagnostic columns ---
    # Ensure diagnostic_params is initialized correctly as list of lists
    if 'diagnostic_params' not in df_v.columns:
        df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    else:
        # Ensure existing values are lists
        df_v['diagnostic_params'] = df_v['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x]))
        
    # Initialize required columns if they might be missing after preprocessing
    if 'overtime' not in df_v.columns: df_v['overtime'] = False
    if 'suspiciously_fast' not in df_v.columns: df_v['suspiciously_fast'] = False
    if 'is_sfe' not in df_v.columns: df_v['is_sfe'] = False
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''
    # Ensure is_relatively_fast is initialized for Ch5
    if 'is_relatively_fast' not in df_v.columns: df_v['is_relatively_fast'] = False # Initialize needed for Ch5 check

    # --- REMOVED: Automatic invalid rule application is done in preprocessing ---

    # --- Add Tag based on FINAL 'is_invalid' status --- 
    final_invalid_mask_v = df_v['is_invalid']
    if final_invalid_mask_v.any(): # Use the calculated final mask
        print(f"    Adding/Ensuring '{INVALID_DATA_TAG_V}' tag for {final_invalid_mask_v.sum()} invalid V rows.")
        # Use .loc for safe access and modification
        for idx in df_v.index[final_invalid_mask_v]:
            current_list = df_v.loc[idx, 'diagnostic_params']
            # Ensure it's a list
            if not isinstance(current_list, list):
                current_list = []
            # Add tag if not present
            if INVALID_DATA_TAG_V not in current_list:
                current_list.append(INVALID_DATA_TAG_V)
            # Assign back using .loc
            df_v.loc[idx, 'diagnostic_params'] = current_list
            
    num_invalid_v_total = df_v['is_invalid'].sum() # Count from the final column
    print(f"    Finished V invalid marking. Total invalid count: {num_invalid_v_total}")
    v_diagnosis_results['invalid_count'] = num_invalid_v_total # Store invalid count

    # --- Filter out invalid data for subsequent analysis (Chapters 2-7) --- 
    # Store the full dataframe before filtering for final return
    df_v_processed_full = df_v.copy()
    df_v_valid = df_v[~df_v['is_invalid']].copy() # More robust filtering using boolean indexing
    
    # --- DEBUG: Check overtime status after filtering invalid ---
    if 'overtime' in df_v_valid.columns:
        print(f"  DEBUG V Diag: df_v_valid (valid data) overtime counts:\n{df_v_valid['overtime'].value_counts()}")
    else:
        print("  DEBUG V Diag: df_v_valid MISSING 'overtime' column after filtering!")
    # --- END DEBUG ---
    
    if df_v_valid.empty:
        print("    No V data remaining after excluding invalid entries. Skipping further V diagnosis.")
        # Generate minimal report
        minimal_report = _generate_v_summary_report(v_diagnosis_results) # Function should handle empty results
        return v_diagnosis_results, minimal_report, df_v_processed_full

    # --- Chapter 1 Global Rule: Mark Suspiciously Fast --- 
    if 'suspiciously_fast' not in df_v.columns: df_v['suspiciously_fast'] = False # Ensure column exists
    print(f"DEBUG: Calculating 'suspiciously_fast' flag using overall avg times: {v_avg_time_per_type}")
    for q_type, avg_time in v_avg_time_per_type.items():
        if avg_time is not None and avg_time > 0 and 'question_time' in df_v.columns:
             # Ensure we only compare valid, non-NaN question times (also exclude invalid)
             valid_time_mask = df_v['question_time'].notna()
             # Ensure we only mark valid questions as suspiciously fast
             not_invalid_mask = ~df_v['is_invalid'] 
             suspicious_mask = (df_v['question_type'] == q_type) & \
                               (df_v['question_time'] < (avg_time * 0.5)) & \
                               valid_time_mask & \
                               not_invalid_mask # Add this condition
             df_v.loc[suspicious_mask, 'suspiciously_fast'] = True
             # Debug print count for this type
             # print(f"DEBUG: Marked {suspicious_mask.sum()} questions as suspiciously_fast for type {q_type} (Threshold < {avg_time * 0.5:.2f})")
        else:
             print(f"DEBUG: Skipping suspiciously_fast calculation for type {q_type} due to missing/invalid avg_time ({avg_time}) or missing 'question_time' column.")

    # --- Apply Chapter 3 Diagnostic Rules (Uses calculated 'overtime' AND 'is_invalid') ---
    # Calculate max correct difficulty per skill (needed for SFE check)
    # IMPORTANT: Use only VALID data for calculating max correct difficulty
    # Use df_v_valid which is already filtered
    df_correct_v = df_v_valid[df_v_valid['is_correct'] == True].copy()
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
    # df_v = _apply_ch3_diagnostic_rules(df_v_processed_full, max_correct_difficulty_per_skill_v, v_avg_time_per_type) # Apply to the full df
    df_v = _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill_v, v_avg_time_per_type)

    # --- DEBUG PRINT 1: After applying rules ---
    print("DEBUG (run_v_diagnosis): >>> After _apply_ch3_diagnostic_rules <<<")
    print("DEBUG (run_v_diagnosis): Columns:", df_v.columns.tolist())
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (run_v_diagnosis): 'diagnostic_params' (English) head:")
        print(df_v['diagnostic_params'].head())
    else:
        print("ERROR (run_v_diagnosis): 'diagnostic_params' column MISSING AFTER rules!")
    # --- END DEBUG PRINT 1 ---

    # --- Translate diagnostic codes --- Create Chinese list, keep English column for now ---
    # --- DEBUG PRINT 2: Before Translation ---
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (v_diagnostic.py): >>> Before Translation <<<")
        print("DEBUG (v_diagnostic.py): 'diagnostic_params' (English) head:")
        print(df_v['diagnostic_params'].head())
    else:
        print("DEBUG (v_diagnostic.py): 'diagnostic_params' column MISSING before translation.")
    # --- END DEBUG PRINT 2 ---
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (v_diagnostic.py): Translating 'diagnostic_params' to Chinese into 'diagnostic_params_list'...")
        # Apply the translation function (already handles lists)
        # Ensure the lambda handles non-list elements gracefully if they sneak in
        # Store directly into the final column name 'diagnostic_params_list'
        df_v['diagnostic_params_list'] = df_v['diagnostic_params'].apply(
            lambda params: [_translate_v(p) for p in params] if isinstance(params, list) else []
        )
        print("DEBUG (v_diagnostic.py): Created 'diagnostic_params_list' (Chinese). Kept original 'diagnostic_params' (English).")
    else:
        print("WARNING (v_diagnostic.py): 'diagnostic_params' column not found for translation.")
        # Initialize the target column if source was missing
        num_rows = len(df_v)
        df_v['diagnostic_params_list'] = pd.Series([[] for _ in range(num_rows)], index=df_v.index)

    # --- *** DO NOT DROP OR RENAME ENGLISH COLUMN YET *** ---

    # --- DEBUG PRINT 3: After Translation (Before Report Generation) ---
    print("DEBUG (v_diagnostic.py): >>> After Translation (Before Report Generation) <<<")
    print("DEBUG (v_diagnostic.py): Columns:", df_v.columns.tolist())
    if 'diagnostic_params' in df_v.columns:
        print("DEBUG (v_diagnostic.py): 'diagnostic_params' (English) head:")
        print(df_v['diagnostic_params'].head())
    if 'diagnostic_params_list' in df_v.columns:
        print("DEBUG (v_diagnostic.py): 'diagnostic_params_list' (Chinese) head:")
        print(df_v['diagnostic_params_list'].head())
    # --- END DEBUG PRINT 3 ---

    # --- Initialize results dictionary --- 
    v_diagnosis_results = {}

    # --- Populate Chapter 1 Results ---
    v_diagnosis_results['chapter_1'] = {
        'time_pressure_status': v_time_pressure_status,
        'invalid_questions_excluded': num_invalid_v_total
        # Add other relevant Ch1 metrics if calculated (e.g., total time, avg time)
    }

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

    # --- Populate Chapter 3 Results (Store the df WITH BOTH English and Chinese columns) --- 
    print("  Structuring V Analysis Results (Chapter 3)...")
    v_diagnosis_results['chapter_3'] = {
        # Store the dataframe itself for report generation to access BOTH params columns
        'diagnosed_dataframe': df_v.copy()
    }
    print("    Finished Chapter 3 V result structuring.")

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

    # --- *** PASS v_diagnosis_results (containing df with BOTH param cols) TO REPORT GENERATOR *** ---
    v_report_content = _generate_v_summary_report(v_diagnosis_results) # Generate the report

    # --- *** NOW Drop the English column AFTER report is generated *** ---
    if 'diagnostic_params' in df_v.columns:
        try:
             df_v.drop(columns=['diagnostic_params'], inplace=True)
             print("DEBUG (v_diagnostic.py): Dropped 'diagnostic_params' column AFTER report generation.")
        except KeyError:
             print("DEBUG (v_diagnostic.py): 'diagnostic_params' column not found during final drop.")

    # --- DEBUG PRINT: Final Columns Before Return ---
    print("DEBUG (v_diagnostic.py): Final Columns before return:", df_v.columns.tolist())
    if 'diagnostic_params_list' in df_v.columns:
        print("DEBUG (v_diagnostic.py): Final 'diagnostic_params_list' head:")
        print(df_v['diagnostic_params_list'].head())
    else:
        print("ERROR (v_diagnostic.py): Final 'diagnostic_params_list' column MISSING before return!")
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
    report_lines.append("**2. 表現概覽 (CR vs RC)**")
    # --- Corrected Metrics Retrieval --- #
    chapter_2_results = v_diagnosis_results.get('chapter_2', {})
    v_metrics_by_type = chapter_2_results.get('by_type', {})
    # Use the actual keys found in the data, default to empty dict if key missing
    cr_metrics = v_metrics_by_type.get('Critical Reasoning', v_metrics_by_type.get('CR', {}))
    rc_metrics = v_metrics_by_type.get('Reading Comprehension', v_metrics_by_type.get('RC', {}))
    # --- End Corrected Metrics Retrieval ---

    # Check if metrics exist and contain necessary rates
    cr_error_rate = cr_metrics.get('error_rate')
    cr_overtime_rate = cr_metrics.get('overtime_rate')
    rc_error_rate = rc_metrics.get('error_rate')
    rc_overtime_rate = rc_metrics.get('overtime_rate')

    # Refined check for comparison possibility
    cr_data_valid = cr_metrics and pd.notna(cr_error_rate) and pd.notna(cr_overtime_rate)
    rc_data_valid = rc_metrics and pd.notna(rc_error_rate) and pd.notna(rc_overtime_rate)

    if cr_data_valid and rc_data_valid:
        cr_total = cr_metrics.get('total_questions', 0)
        rc_total = rc_metrics.get('total_questions', 0)
        report_lines.append(f"- CR ({cr_total} 題): 錯誤率 {_format_rate(cr_error_rate)}, 超時率 {_format_rate(cr_overtime_rate)}")
        report_lines.append(f"- RC ({rc_total} 題): 錯誤率 {_format_rate(rc_error_rate)}, 超時率 {_format_rate(rc_overtime_rate)}")
        # Comparison logic (significant difference)
        error_diff = abs(cr_error_rate - rc_error_rate)
        overtime_diff = abs(cr_overtime_rate - rc_overtime_rate)
        significant_error = error_diff >= 0.15 # 15% difference threshold
        significant_overtime = overtime_diff >= 0.15 # 15% difference threshold

        if significant_error or significant_overtime:
            comparison_notes = []
            if significant_error:
                comparison_notes.append(f"錯誤率差異{'顯著' if significant_error else '不顯著'}")
                report_lines.append(f"  - **錯誤率對比:** {'CR 更高' if cr_error_rate > rc_error_rate else 'RC 更高'} (差異 {_format_rate(error_diff)})")
            if significant_overtime:
                comparison_notes.append(f"超時率差異{'顯著' if significant_overtime else '不顯著'}")
                report_lines.append(f"  - **超時率對比:** {'CR 更高' if cr_overtime_rate > rc_overtime_rate else 'RC 更高'} (差異 {_format_rate(overtime_diff)})")
        else:
            report_lines.append("  - CR 與 RC 在錯誤率和超時率上表現相當，無顯著差異。")
    elif not cr_data_valid and not rc_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 CR 和 RC 數據，無法進行比較。")
    elif not cr_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 CR 數據，無法進行比較。")
        if rc_data_valid: # Still show RC data if available
             rc_total = rc_metrics.get('total_questions', 0)
             report_lines.append(f"  - (RC ({rc_total} 題): 錯誤率 {_format_rate(rc_error_rate)}, 超時率 {_format_rate(rc_overtime_rate)})")
    elif not rc_data_valid:
        report_lines.append("- **CR 與 RC 表現對比：** 因缺乏有效的 RC 數據，無法進行比較。")
        if cr_data_valid: # Still show CR data if available
             cr_total = cr_metrics.get('total_questions', 0)
             report_lines.append(f"  - (CR ({cr_total} 題): 錯誤率 {_format_rate(cr_error_rate)}, 超時率 {_format_rate(cr_overtime_rate)})")
    # --- End refined check ---

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

    # --- Define triggered_params_all HERE --- #
    triggered_params_all = set()
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params_list' in diagnosed_df.columns:
         all_param_lists = diagnosed_df['diagnostic_params_list'].apply(lambda x: x if isinstance(x, list) else [])
         # Translate Chinese list back to English codes if necessary or get English codes directly
         # Assuming ch3 diagnosed_df still holds English codes if translation happened later
         # OR, ideally, get English codes directly from Ch3 results before translation happened.
         # For now, assume we need to get *all* unique params triggered.
         # We need the *English* codes here to compare with the Tool Map keys later.
         # Re-retrieve the English params if possible, otherwise this step is difficult.
         # Let's assume the 'diagnostic_params' (English) might still be in ch3 results
         diagnosed_df_ch3_raw = ch3.get('diagnosed_dataframe') # Get the df again
         if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
             # This assumes the English codes were stored before being dropped/renamed.
             # If not, this needs rethinking based on where English codes are preserved.
             english_param_lists = diagnosed_df_ch3_raw['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])
             triggered_params_all.update(p for sublist in english_param_lists for p in sublist)
         else:
              print("WARNING (_generate_v_summary_report): Could not retrieve original English diagnostic_params for tool recommendation matching.")

    # Add behavioral params from Chapter 5
    if ch5:
        triggered_params_all.update(ch5.get('param_triggers', []))
    # --- End Defining triggered_params_all ---

    if diagnosed_df is not None and not diagnosed_df.empty:
        # Check if 'diagnostic_params_list' column exists before trying to iterate
        params_col_exists = 'diagnostic_params_list' in diagnosed_df.columns
        if not params_col_exists:
             print("WARNING (_generate_v_summary_report): 'diagnostic_params_list' column missing in diagnosed_df for Section 3 analysis.")

        for index, row in diagnosed_df.iterrows():
            is_error = not row['is_correct']
            is_slow_correct = row['is_correct'] and row.get('overtime', False)
            # Use diagnostic_params_list (Chinese) if it exists, otherwise use an empty list
            params_zh = row.get('diagnostic_params_list', []) if params_col_exists else []
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

                # Collect core issue params (using Chinese list - need to translate back for core_issues_params if needed)
                # core_issues_params.update(...) # This needs English params

                # Store details for the list (using Chinese params for display)
                all_problem_items.append({
                    'position': q_pos,
                    'skill': skill,
                    'performance': time_cat,
                    'params': params_zh, # Store Chinese params for display list
                    'question_type': row.get('question_type', 'Unknown Type'),
                    'is_sfe': is_sfe
                })

                # Check for qualitative analysis triggers (MD Ch3 logic)
                # This requires ENGLISH params. Need to get them.
                # Assuming we have triggered_params_all (English) defined above now.
                # Need to re-map row index to the English params for accurate check.
                current_english_params = set() # Placeholder - Requires proper mapping
                # Example mapping (needs actual implementation):
                # if index in diagnosed_df_ch3_raw.index:
                #     raw_params = diagnosed_df_ch3_raw.loc[index, 'diagnostic_params']
                #     if isinstance(raw_params, list): current_english_params = set(raw_params)

                if time_cat in ['Normal Time & Wrong', 'Slow & Wrong']:
                    secondary_evidence_trigger = True # These categories warrant review
                    # Check for complex params that might trigger qualitative
                    complex_params = {
                        'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                        'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                        'RC_REASONING_INFERENCE_WEAKNESS'
                    }
                    # Use current_english_params here
                    # if any(p in complex_params for p in current_english_params):
                    #     qualitative_analysis_trigger = True
                elif time_cat == 'Slow & Correct':
                     qualitative_analysis_trigger = True # Often needs qualitative check for bottleneck

    # --- Re-calculate core_issues_params using the collected English triggered_params_all --- #
    core_issues_params = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'}
    # --- End Re-calculation --- #

    # Report SFE Summary
    if sfe_triggered_overall:
        sfe_label = _translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        # Keep skill names in English
        sfe_skills_en = sorted(list(sfe_skills_involved))
        sfe_note = f"{sfe_label}"
        if sfe_skills_en:
            sfe_note += f" (涉及技能: {', '.join(sfe_skills_en)})"
        report_lines.append(f"- **尤其需要注意:** {sfe_note}。(註：SFE 指在已掌握技能範圍內的題目失誤)")

    # Report if no core issues AND no SFE
    if not core_issues_params and not sfe_triggered_overall:
        report_lines.append("- 未識別出明顯的核心問題模式 (基於錯誤及效率分析)。")

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
        # Keep skill names in English
        triggered_skills_en = sorted(triggered_skills)
        report_lines.append(f"- **以下核心技能整體表現顯示較大提升空間 (錯誤率 > 50%)，建議優先系統性鞏固:** {', '.join(triggered_skills_en)}")
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
             # --- Corrected Condition to include macro and case_aggregated --- #
             elif rec_type == 'macro' or rec_type == 'case' or rec_type == 'case_aggregated':
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
    
    # --- 重要修改: 直接使用 diagnosed_df 中的 'diagnostic_params' (英文標籤) ---
    # 這確保 param_to_positions 的鍵是英文參數，與 triggered_params_all 能夠正確匹配
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
        for index, row in diagnosed_df.iterrows():
            pos = row.get('question_position')
            # 使用英文參數列表填充 param_to_positions
            params_en = row.get('diagnostic_params', [])
            if isinstance(params_en, list) and pos is not None and pos != 'N/A':
                for p in params_en:
                    param_to_positions.setdefault(p, set()).add(pos)
    # --- 修改結束 ---
    
    if all_problem_items:
        for item in all_problem_items:
            pos = item.get('position')
            skill = item.get('skill')
            performance = item.get('performance')
            if pos is not None and pos != 'N/A':
                if skill and skill != 'Unknown Skill':
                    skill_to_positions.setdefault(skill, set()).add(pos)
                if performance in performance_to_skills and skill and skill != 'Unknown Skill':
                    performance_to_skills[performance].add(skill)
    
    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for skill in skill_to_positions: skill_to_positions[skill] = sorted(list(skill_to_positions[skill]))

    # Guide Reflection
    report_lines.append("- **引導反思:**")
    reflection_prompts = []

    # --- Helper Function to Get Relevant Skills ---
    def get_relevant_skills(param_keys, param_to_positions_map, skill_to_positions_map):
        # Find all positions related to the given parameters
        relevant_positions = set()
        for key in param_keys:
            relevant_positions.update(param_to_positions_map.get(key, set()))

        # Find skills associated with these positions
        relevant_skills_set = set()
        for skill, positions in skill_to_positions_map.items():
            if not relevant_positions.isdisjoint(positions): # Check if any position matches
                if skill != 'Unknown Skill': # Exclude 'Unknown Skill'
                    relevant_skills_set.add(skill)

        # Return sorted list of English skill names
        return sorted(list(relevant_skills_set))
    # --- End Helper Function ---

    def get_pos_context(param_keys): # Keep existing helper
        positions = set().union(*(param_to_positions.get(key, set()) for key in param_keys))
        return f" (涉及題號: {sorted(list(positions))})" if positions else ""

    # --- Define Parameter Groups (Use English Codes) ---
    # These groups should correspond to the specific reflection prompts
    logic_params_v = [
        'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_ABSTRACTION_DIFFICULTY',
        'CR_REASONING_PREDICTION_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
        'CR_AC_ANALYSIS_RELEVANCE_ERROR', 'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION',
        'RC_REASONING_INFERENCE_WEAKNESS', 'RC_AC_ANALYSIS_DIFFICULTY',
        'CR_METHOD_TYPE_SPECIFIC_ERROR', # Added based on V-Doc Ch3
        'RC_METHOD_TYPE_SPECIFIC_ERROR'  # Added based on V-Doc Ch3
    ]
    reading_params_v = [
        'CR_READING_BASIC_OMISSION', 'CR_READING_DIFFICULTY_STEM',
        'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION',
        'RC_READING_INFO_LOCATION_ERROR', 'RC_READING_KEYWORD_LOGIC_OMISSION',
        'RC_READING_VOCAB_BOTTLENECK', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY',
        'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP',
        'RC_READING_PRECISION_INSUFFICIENT', 'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION',
        'RC_LOCATION_ERROR_INEFFICIENCY', 'RC_READING_COMPREHENSION_BARRIER',
        'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY'
    ]
    efficiency_params_v = [
        'CR_READING_TIME_EXCESSIVE', 'CR_REASONING_TIME_EXCESSIVE', 'CR_AC_ANALYSIS_TIME_EXCESSIVE',
        'RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_METHOD_INEFFICIENT_READING',
        'RC_LOCATION_TIME_EXCESSIVE', 'RC_REASONING_TIME_EXCESSIVE', 'RC_AC_ANALYSIS_TIME_EXCESSIVE',
        'EFFICIENCY_BOTTLENECK_READING', 'EFFICIENCY_BOTTLENECK_REASONING',
        'EFFICIENCY_BOTTLENECK_LOCATION', 'EFFICIENCY_BOTTLENECK_AC_ANALYSIS'
    ]
    carelessness_params_v = [
        'BEHAVIOR_CARELESSNESS_ISSUE'
        # Add V-specific carelessness params if defined, e.g., from App A
        # 'V_CARELESSNESS_DETAIL_OMISSION',
        # 'V_CARELESSNESS_OPTION_MISREAD'
    ]

    # Logic Prompt Check
    logic_trigger_check = any(p in triggered_params_all for p in logic_params_v)
    if logic_trigger_check:
        skills_involved = get_relevant_skills(logic_params_v, param_to_positions, skill_to_positions)
        skill_context = f" [`{', '.join(skills_involved)}`] " if skills_involved else " "
        reflection_prompts.append(f"  - 回想一下，在做錯/慢的{skill_context}題目時，具體是卡在哪个推理步驟、邏輯關係或選項辨析上？是完全沒思路，還是思路有偏差？" + get_pos_context(logic_params_v))

    # Reading Prompt Check
    reading_trigger_check = any(p in triggered_params_all for p in reading_params_v)
    if reading_trigger_check:
        skills_involved = get_relevant_skills(reading_params_v, param_to_positions, skill_to_positions)
        skill_context = f" [`{', '.join(skills_involved)}`] " if skills_involved else " "
        reflection_prompts.append(f"  - 對於做錯/慢的{skill_context}題目，是文章/題幹的關鍵信息沒讀懂、讀漏，還是題目要求理解錯誤？定位信息是否存在困難？" + get_pos_context(reading_params_v))

    # Efficiency Prompt Check
    efficiency_trigger_check = any(p in triggered_params_all for p in efficiency_params_v)
    if efficiency_trigger_check:
        skills_involved = get_relevant_skills(efficiency_params_v, param_to_positions, skill_to_positions)
        skill_context = f" [`{', '.join(skills_involved)}`] " if skills_involved else " "
        reflection_prompts.append(f"  - 回想耗時過長的{skill_context}題目，是閱讀花了太長時間，邏輯分析卡住，還是選項比較難以排除？" + get_pos_context(efficiency_params_v))

    # Carelessness Prompt Check
    carelessness_trigger_check = any(p in triggered_params_all for p in carelessness_params_v) # Use list defined above
    if carelessness_trigger_check: # Check the specific list, not just the one flag 'BEHAVIOR_CARELESSNESS_ISSUE'
        careless_positions = param_to_positions.get('BEHAVIOR_CARELESSNESS_ISSUE', set())
        # If the main flag has no direct positions, maybe find positions linked to other detail omission params?
        # For now, stick to the main flag's linked positions if any.
        careless_context = f" (例如題號: {sorted(list(careless_positions))})" if careless_positions else ""
        reflection_prompts.append("  - 回想一下，是否存在因為看錯字、忽略細節或誤解選項導致的失誤？" + careless_context)

    if not reflection_prompts:
        reflection_prompts.append("  - (本次分析未觸發典型的反思問題，建議結合練習計劃進行)")
    report_lines.extend(reflection_prompts)

    # Secondary Evidence Suggestion
    report_lines.append("- **二級證據參考建議:**")
    review_prompt = ""
    if secondary_evidence_trigger:
        review_prompt = "  - 本次分析識別出部分問題可能需要您查看近期的練習記錄以深入了解。當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。"
        
        # --- START NEW LOGIC: Group by time_performance_category ---
        details_added_2nd_ev = False
        
        diagnosed_df = ch3.get('diagnosed_dataframe') # Re-get df
        if diagnosed_df is not None and not diagnosed_df.empty and 'time_performance_category' in diagnosed_df.columns:
            # Filter for problems (incorrect or overtime)
            df_problem = diagnosed_df[(diagnosed_df['is_correct'] == False) | (diagnosed_df.get('overtime', False) == True)].copy()
            
            if not df_problem.empty:
                # Define the desired order for performance categories
                performance_order_en = [
                    'Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 
                    'Slow & Correct', 'Fast & Correct', 'Normal Time & Correct',
                    'Unknown' # Include Unknown as a fallback
                ]
                
                grouped_by_performance = df_problem.groupby('time_performance_category')
                
                # Iterate in the desired order
                for perf_en in performance_order_en:
                    if perf_en in grouped_by_performance.groups: # Check if this group exists
                        # --- ADD SKIP LOGIC for 'Fast & Correct' ---
                        if perf_en == 'Fast & Correct':
                            print(f"DEBUG (v_report): Skipping category '{perf_en}' as requested.") # DEBUG
                            continue # Skip to the next category
                        # --- END SKIP LOGIC ---
                        
                        group_df = grouped_by_performance.get_group(perf_en)
                        if not group_df.empty:
                            perf_zh = perf_en  # Default if translation not available
                            # Translate performance category if needed
                            if perf_en == 'Fast & Wrong': perf_zh = "快錯"
                            elif perf_en == 'Slow & Wrong': perf_zh = "慢錯"
                            elif perf_en == 'Normal Time & Wrong': perf_zh = "正常時間錯"
                            elif perf_en == 'Slow & Correct': perf_zh = "慢對"
                            elif perf_en == 'Fast & Correct': perf_zh = "快對"
                            elif perf_en == 'Normal Time & Correct': perf_zh = "正常時間對"
                            
                            # Extract unique types and skills from this group
                            types_in_group = group_df['question_type'].dropna().unique()
                            skills_in_group = group_df['question_fundamental_skill'].dropna().unique()
                            
                            types_zh = sorted([t for t in types_in_group])
                            # Keep skill names in English
                            skills_en = sorted([s for s in skills_in_group])

                            # --- Extract Unique Labels ---
                            all_labels_in_group = set()
                            target_label_col = None
                            
                            # Check if the diagnostic_params column exists
                            if 'diagnostic_params' in group_df.columns:
                                target_label_col = 'diagnostic_params'
                                print(f"DEBUG (v_report): Found 'diagnostic_params' column, will translate internally.")
                            else:
                                print(f"DEBUG (v_report): No diagnostic params column found for this group!")

                            if target_label_col:
                                print(f"DEBUG (v_report): Processing labels from column: {target_label_col}")
                                
                                for labels_list in group_df[target_label_col]:
                                    if isinstance(labels_list, list): # Check if it's a list
                                        translated_list = [_translate_v(p) for p in labels_list]
                                        all_labels_in_group.update(translated_list)
                            
                            sorted_labels_zh = sorted(list(all_labels_in_group))
                            
                            # --- Modify Report Line ---
                            report_line = f"  - **{perf_zh}:** 需關注題型：【{', '.join(types_zh)}】；涉及技能：【{', '.join(skills_en)}】。"
                            if sorted_labels_zh:
                                report_line += f" 注意相關問題點：【{', '.join(sorted_labels_zh)}】。"
                            review_prompt += f"\n{report_line}"
                            # --- End Modify Report Line ---
                            
                            details_added_2nd_ev = True
                
                if not details_added_2nd_ev:
                    review_prompt += " (本次分析未聚焦到特定的問題類型或技能) "
            else:
                review_prompt += " (本次分析未發現需要分析的問題) "
        else:
            review_prompt += " (缺少必要診斷數據) "
        # --- END NEW LOGIC ---
            
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
    # report_lines.append("- **輔助工具與 AI 提示推薦 (基於本次診斷觸發的標籤):**")
    # --- Comprehensive Tool Recommendation Map (Based on MD Ch8.7) ---
    # tool_recommendations_map = {
    #     # CR Reasoning & Specific Types
    #     frozenset(['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']):
    #         "可能適用外部工具 `Dustin_GMAT_CR_Core_Issue_Identifier` 或 `Dustin_GMAT_CR_Chain_Argument_Evaluation`；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
    #     frozenset(['CR_METHOD_TYPE_SPECIFIC_ERROR']):
    #         "特定 CR 題型方法錯誤 (如 Boldface, Argument Construction)，可能適用外部工具 `Dustin\'s GMAT CR: Boldface Interactive Tutor` (Boldface) 或 `Dustin_GMAT_CR_Role_Argument_Construction` (Argument Construction)；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
    #     frozenset(['CR_REASONING_ABSTRACTION_DIFFICULTY']):
    #         "CR 抽象邏輯或術語理解困難，可能適用外部工具 `Dustin\'s GMAT Tool: Textbook Explainer`；或使用 AI 提示 `Verbal-related/07_logical_term_explained.md`, `Verbal-related/09_complex_sentence_rewrite.md`。",
    #     frozenset(['CR_READING_BASIC_OMISSION']):
    #         "CR 基礎理解疏漏，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`。",
    #     frozenset(['CR_READING_DIFFICULTY_STEM']):
    #         "CR 題幹理解障礙，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`, `Verbal-related/09_complex_sentence_rewrite.md`。",
    #     frozenset(['CR_READING_TIME_EXCESSIVE']):
    #         "CR 閱讀耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/03_quick_rc_tricks.md`。",
    #     frozenset(['CR_QUESTION_UNDERSTANDING_MISINTERPRETATION']):
    #         "CR 提問要求把握錯誤，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`。",
    #     frozenset(['CR_REASONING_PREDICTION_ERROR']):
    #         "CR 預判方向錯誤或缺失，可使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`。",
    #     frozenset(['CR_REASONING_TIME_EXCESSIVE']):
    #         "CR 邏輯思考耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/05_evaluate_explanation.md`。",
    #     frozenset(['CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY']):
    #         "CR 選項本身理解困難，可使用 AI 提示 `Verbal-related/07_logical_term_explained.md`, `Verbal-related/01_basic_explanation.md`。",
    #     frozenset(['CR_AC_ANALYSIS_RELEVANCE_ERROR']):
    #         "CR 選項相關性判斷錯誤，可使用 AI 提示 `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
    #     frozenset(['CR_AC_ANALYSIS_DISTRACTOR_CONFUSION']):
    #         "CR 強干擾選項混淆，可能適用外部工具 `Dustin_GMAT_Verbal_Distractor_Mocker`；或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/07_logical_term_explained.md`。",
    #     frozenset(['CR_AC_ANALYSIS_TIME_EXCESSIVE']):
    #         "CR 選項篩選耗時過長，可使用 AI 提示 `Verbal-related/02_quick_cr_tpa_tricks.md`, `Verbal-related/06_boldface_SOP.md`。",
    #     frozenset(['CR_METHOD_PROCESS_DEVIATION']):
    #         "CR 未遵循標準流程，可使用 AI 提示 `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",

    #     # RC Reading Comprehension
    #     frozenset(['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_READING_COMPREHENSION_BARRIER']):
    #         "RC 基礎閱讀速度慢或存在障礙，可能適用外部工具 `Dustin GMAT: Chunk Reading Coach`；或使用 AI 提示 `Verbal-related/03_quick_rc_tricks.md`。",
    #     frozenset(['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'reading_comprehension_barrier_inquiry']): # Example: Combine param with Ch1 flag
    #         "RC 基礎閱讀速度慢，可能適用外部工具 `Dustin GMAT: Chunk Reading Coach` 或 AI 提示 `Verbal-related/03_quick_rc_tricks.md`。",
    #     frozenset(['RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP', 'RC_READING_VOCAB_BOTTLENECK']): # Non-systemic vocab
    #         "RC 長難句/領域知識/非系統性詞彙瓶頸，可能適用外部工具 `Dustin's GMAT Terminator: Sentence Cracker` 或相關 AI 提示。",
    #     frozenset(['RC_READING_VOCAB_BOTTLENECK']): # Systemic vocab (needs logic to differentiate)
    #         "RC 詞彙量瓶頸 (需系統性學習)，可能適用外部工具 `Dustin's GMAT Core: Vocab Master`。",
    #     frozenset(['RC_READING_PRECISION_INSUFFICIENT']):
    #         "RC 閱讀精度不足，可能適用外部工具 `Dustin GMAT Close Reading Coach` 或 AI 提示。",
    #     frozenset(['RC_READING_PASSAGE_STRUCTURE_DIFFICULTY']):
    #         "RC 篇章結構把握不清，可能適用外部工具 `Dustin_GMAT_RC_Passage_Analyzer` 或 AI 提示。",

    #     # Distractors/Carelessness
    #     frozenset(['CR_AC_ANALYSIS_DISTRACTOR_CONFUSION', 'RC_AC_ANALYSIS_DIFFICULTY', 'BEHAVIOR_CARELESSNESS_ISSUE']):
    #         "選項辨析困難或粗心問題，可能適用外部工具 `Dustin_GMAT_Verbal_Distractor_Mocker` 或相關 AI 提示。",

    #     # Foundational Mastery
    #     frozenset(['FOUNDATIONAL_MASTERY_INSTABILITY_SFE']):
    #         "基礎掌握不穩定 (SFE)，建議優先使用 AI 提示 `Verbal-related/01_basic_explanation.md` 鞏固基礎。",

    #     # Behavioral
    #     frozenset(['BEHAVIOR_EARLY_RUSHING_FLAG_RISK']):
    #         "前期作答過快，建議使用 AI 提示 `Verbal-related/05_evaluate_explanation.md` 反思節奏。",
    #     frozenset(['BEHAVIOR_GUESSING_HASTY']):
    #         "疑似猜題/倉促，建議使用 AI 提示 `Verbal-related/01_basic_explanation.md` 學習完整步驟。",
    # }

    # Generate tool recommendations based on triggered params (Q-like format)
    # processed_for_tools = set()
    # recommendations_made = False
    # Split tools and prompts
    # recommended_tools = set() # Use sets to avoid duplicates initially
    # recommended_prompts_map = {} # Keep this as dict to store reasons

    # for params_set, tool_desc in tool_recommendations_map.items():
    #     if any(p in triggered_params_all for p in params_set) and not params_set.issubset(processed_for_tools):
    #         trigger_reasons_translated = [_translate_v(p) for p in params_set if p in triggered_params_all]
    #         if trigger_reasons_translated:
    #             # Extract tool names and prompt names using precise patterns
    #             import re
    #             # Step 1: Find all items within backticks
    #             all_backticked_items = re.findall(r'`([^`]+?)`', tool_desc)
                
    #             # Step 2: Filter into tools (not ending in .md) and prompts (ending in .md)
    #             current_tools = {item for item in all_backticked_items if not item.endswith('.md') and item.strip()}
    #             current_prompts = {item for item in all_backticked_items if item.endswith('.md')}
                
    #             if current_tools:
    #                 recommended_tools.update(current_tools) # Add to set
    #                 recommendations_made = True
    #             if current_prompts:
    #                 for prompt in current_prompts:
    #                     # Store reasons for each prompt
    #                     if prompt not in recommended_prompts_map:
    #                         recommended_prompts_map[prompt] = set()
    #                     recommended_prompts_map[prompt].update(trigger_reasons_translated)
    #                 recommendations_made = True

    #             processed_for_tools.update(params_set)

    # Report Tools
    # if recommended_tools:
    #      report_lines.append("  - 工具:")
    #      # Sort the set before reporting
    #      for tool in sorted(list(recommended_tools)):
    #          report_lines.append(f"    - `{tool}`")

    # Report Prompts
    # if recommended_prompts_map:
    #     report_lines.append("  - AI提示:")
    #     for prompt in sorted(recommended_prompts_map.keys()):
    #         # reasons = ", ".join(sorted(list(recommended_prompts_map[prompt])))
    #         # report_lines.append(f"    - `{prompt}` (基於: {reasons})") # Option to show reasons
    #         report_lines.append(f"    - `{prompt}`")

    # Fallback message
    # if not recommendations_made:
    #      report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議)")

    report_lines.append("\n--- 報告結束 ---")
    print("DEBUG: --- Exiting _generate_v_summary_report ---") # DEBUG
    # Use double newline for Markdown paragraph breaks
    return "\n\n".join(report_lines)

# --- V Recommendation Generation Helper ---

def _generate_v_recommendations(v_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on V diagnosis results,
       applying skill exemption rules.
    """
    # print(f"DEBUG: +++ Entering _generate_v_recommendations (Exempted: {exempted_skills}) +++") # REMOVED DEBUG
    recommendations = []
    processed_macro_skills = set() # Keep track of skills covered by macro recs

    # Extract relevant results safely
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {}) # Now contains skill_override_triggered

    # Get Ch6 override results
    skill_override_triggered = ch6.get('skill_override_triggered', {})

    # Get Ch3 diagnosed dataframe (needed for iterating problems)
    diagnosed_df = v_diagnosis_results.get('chapter_3', {}).get('diagnosed_dataframe')

    # Initialize recommendations structure
    recommendations_by_skill = {} # Store recommendations keyed by skill
    all_skills_found = set() # Keep track of all unique skills encountered in diagnostic data

    # 1. Identify all skills from diagnostic parameters in Ch3
    # --- CORRECTED SKILL IDENTIFICATION --- #
    if diagnosed_df is not None and not diagnosed_df.empty and \
       'is_correct' in diagnosed_df.columns and \
       'overtime' in diagnosed_df.columns and \
       'question_fundamental_skill' in diagnosed_df.columns:

        problem_mask = (diagnosed_df['is_correct'] == False) | \
                       ((diagnosed_df['is_correct'] == True) & (diagnosed_df['overtime'] == True))
        problem_skills = diagnosed_df.loc[problem_mask, 'question_fundamental_skill'].dropna().unique()
        all_skills_found = set(skill for skill in problem_skills if skill != 'Unknown Skill')
        # print(f"      DEBUG (_generate_v_recommendations): Identified skills with problems (Error or SlowCorrect): {all_skills_found}") # REMOVED DEBUG
    else:
        print("      WARNING (_generate_v_recommendations): Could not identify problem skills due to missing columns in diagnosed_df.")
    # --- END CORRECTED SKILL IDENTIFICATION --- #

    # 2. Generate Recommendations (Macro then Case)
    if not all_skills_found:
        # print("      DEBUG (_generate_v_recommendations): No problem skills found, skipping recommendation generation loop.") # REMOVED DEBUG
        pass # Keep the logic flow

    for skill in all_skills_found:
        # --- APPLY EXEMPTION RULE (Task 3) ---
        if skill in exempted_skills:
            # print(f"      DEBUG (_generate_v_recommendations): Skipping recommendations for exempted skill: {skill}") # REMOVED DEBUG
            continue # Skip generating any recommendation for this skill
        # --- END EXEMPTION RULE ---

        skill_recs_list = []
        # Check for override rule based on the results passed in v_diagnosis_results
        is_overridden = ch6.get('skill_override_triggered', {}).get(skill, False)
        # print(f"      DEBUG (_generate_v_recommendations): Processing Skill: {skill}, Overridden: {is_overridden}") # REMOVED DEBUG

        if is_overridden and skill not in processed_macro_skills:
            # Generate Macro Recommendation (V-Doc Ch7)
            # Keep skill name in English for the recommendation text source
            macro_rec_text = f"針對【{skill}】技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_macro_skills.add(skill)
            # print(f"      DEBUG (_generate_v_recommendations): Generated MACRO recommendation for Skill: {skill}") # REMOVED DEBUG

        elif not is_overridden:
            case_recs_generated_for_skill = False # DEBUG flag
            # Generate Case-Specific Recommendations for this skill
            # Find relevant rows in diagnosed_df for this skill
            if diagnosed_df is not None and not diagnosed_df.empty:
                # Filter for the current skill AND problems (Error or SlowCorrect)
                # Use the same problem_mask defined earlier for efficiency
                skill_problem_mask = (diagnosed_df['question_fundamental_skill'] == skill) & problem_mask
                skill_rows = diagnosed_df[skill_problem_mask]

                if not skill_rows.empty:
                    # --- AGGREGATED CASE RECOMMENDATION (Changed from row-by-row) ---
                    # print(f"        DEBUG (_generate_v_recommendations): Found {len(skill_rows)} problem rows for Case Rec (Skill: {skill}).") # REMOVED DEBUG
                    # Aggregate info for the skill
                    min_difficulty = skill_rows['question_difficulty'].min()
                    y_grade = _grade_difficulty_v(min_difficulty)

                    # Calculate Max Z Time (Similar to DI logic)
                    z_minutes_list = []
                    q_type_for_skill = skill_rows['question_type'].iloc[0] # Assume skill maps to one type
                    target_time_minutes = 2.0 if q_type_for_skill == 'Critical Reasoning' else 1.5 # Use 1.5 for RC

                    for _, row in skill_rows.iterrows():
                        q_time_minutes = row['question_time']
                        is_overtime = row['overtime']
                        if pd.notna(q_time_minutes):
                            base_time_minutes = q_time_minutes
                            # No adjustment needed here based on current V logic for Z
                            base_time_minutes = max(0, base_time_minutes) # Ensure non-negative
                            # Floor to nearest 0.5 minute
                            z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                            z = max(z_raw_minutes, target_time_minutes) # Ensure Z is at least the target
                            z_minutes_list.append(z)

                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{'CR 2.0 / RC 1.5'} 分鐘" # Clarify target time

                    group_sfe = skill_rows['is_sfe'].any()

                    # Get triggered params for this group (Use the CHINESE list now)
                    # Note: Param list is no longer included in the output string per user request
                    # diag_params_zh = set()
                    # chinese_params_available = False
                    # Use the correct column name 'diagnostic_params_list'
                    # if 'diagnostic_params_list' in diagnosed_df.columns:
                    #      chinese_params_available = True
                    #      for idx in skill_rows.index:
                    #         row_params_zh = diagnosed_df.loc[idx, 'diagnostic_params_list']
                    #         if isinstance(row_params_zh, list):
                    #              diag_params_zh.update(row_params_zh)
                    # translated_params_list = sorted(list(diag_params_zh)) if chinese_params_available else []
                    # param_text = f"(問題點可能涉及: {', '.join(translated_params_list)})" if translated_params_list else "(具體問題點需進一步分析)"

                    problem_desc = "錯誤或超時" # No longer used in output
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    # Keep skill name in English
                    # --- ADJUSTED FORMATTING --- #
                    case_rec_text = f"{sfe_prefix}針對【{skill}】建議練習【{y_grade}】難度題目，起始練習限時建議為【{z_text}】(最終目標時間: {target_time_text})。"
                    # Removed: ({problem_desc}) {param_text}
                    # --- END ADJUSTED FORMATTING --- #


                    if max_z_minutes - target_time_minutes > 2.0:
                        case_rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    priority = 1 if group_sfe else 2 # Prioritize SFE cases
                    skill_recs_list.append({
                        'type': 'case_aggregated',
                        'text': case_rec_text,
                        'priority': priority,
                        'is_sfe': group_sfe # Store for potential sorting/filtering
                    })
                    case_recs_generated_for_skill = True # DEBUG flag
                    # --- END AGGREGATED CASE RECOMMENDATION ---\
                else:
                     # print(f"        DEBUG (_generate_v_recommendations): No problem rows found for Skill {skill} after filtering.") # REMOVED DEBUG
                     pass
            else:
                 # print(f"        DEBUG (_generate_v_recommendations): diagnosed_df is None or empty, cannot generate Case Rec for Skill {skill}.") # REMOVED DEBUG
                 pass

            # DEBUG print if no case recs were generated for a non-overridden skill
            if not case_recs_generated_for_skill:
                 # print(f"      WARNING (_generate_v_recommendations): No Case recommendations generated for non-overridden Skill: {skill}") # REMOVED DEBUG
                 pass # Keep logic flow

        # --- *** RE-ADD MISSING ASSIGNMENT HERE *** --- #
        # Add recommendations for this skill to the main dict if any were generated
        if skill_recs_list:
             recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])
        # --- *** END RE-ADD *** --- #

    # 3. Assemble Final List (excluding behavioral for now)
    final_recommendations = []

    # --- DEBUG: Print recommendations_by_skill before assembly --- # REMOVED
    # print(f"      DEBUG (_generate_v_recommendations): recommendations_by_skill = {recommendations_by_skill}") # REMOVED
    # --- END DEBUG --- #

    # Sort skills: Macro skills first, then alphabetically
    # This uses recommendations_by_skill which SHOULD contain the generated recs now
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_macro_skills else 1, s))

    # print(f"      DEBUG (_generate_v_recommendations): Skills to assemble recommendations for: {sorted_skills}") # REMOVED DEBUG

    for skill in sorted_skills:
        # Check if skill exists in the dictionary before accessing
        if skill in recommendations_by_skill:
            recs = recommendations_by_skill[skill] # Get the list of recs for the skill
            # print(f"        DEBUG (_generate_v_recommendations): Assembling recommendations for Skill: {skill}, Count: {len(recs)}") # REMOVED DEBUG
            final_recommendations.append({'type': 'skill_header', 'text': f"--- 技能: {skill} ---"}) # Add header as dict item
            final_recommendations.extend(recs) # Add list of rec dicts
            final_recommendations.append({'type': 'spacer', 'text': ""}) # Add spacer as dict item
        else:
            # print(f"        WARNING (_generate_v_recommendations): Skill '{skill}' not found in recommendations_by_skill during assembly.") # REMOVED DEBUG
            pass # Keep logic flow


    # 4. Add Behavioral Recommendations (from Ch5)
    # Placeholder for future implementation if needed
    # if ch5:
    #     behavioral_params = ch5.get('param_triggers', [])
    #     if 'BEHAVIOR_EARLY_RUSHING_FLAG_RISK' in behavioral_params:
    #         final_recommendations.append({'type': 'behavioral', 'text': '行為建議: 注意前期答題節奏，避免因過快而影響準確率。'})
    #     if 'BEHAVIOR_CARELESSNESS_ISSUE' in behavioral_params:
    #          final_recommendations.append({'type': 'behavioral', 'text': '行為建議: 「快而錯」比例偏高，練習時注意檢查細節，避免粗心錯誤。'})

    # --- DEBUG: Print final recommendations before return --- # REMOVED
    # print(f"DEBUG (_generate_v_recommendations): Final recommendations list (length {len(final_recommendations)}): {final_recommendations}") # REMOVED
    # --- END DEBUG --- #

    # print("DEBUG: --- Exiting _generate_v_recommendations ---\") # REMOVED DEBUG
    return final_recommendations # Returns the list

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

    # --- DEBUG: Print overtime rate calculation details ---
    print(f"    DEBUG V Metric Calc: Group Shape={group.shape}, Overtime Count={overtime_count}, Total Valid={total}, Calculated OT Rate={overtime_rate:.3f}")
    # --- END DEBUG ---

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