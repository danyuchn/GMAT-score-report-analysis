import pandas as pd
import numpy as np
import math # For floor function

# --- V-Specific Constants (Add as needed) ---
# Example: Define time thresholds if needed later
# CR_AVG_TIME_THRESHOLD = 2.0 # minutes
# RC_AVG_TIME_THRESHOLD_PER_Q = 1.75 # minutes (assuming reading time is separate or amortized)

# Chapter 1 Constants (from V-Doc)
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

# Define V_INVALID_TIME_ABANDONED for use in Chapter 3
V_INVALID_TIME_ABANDONED = 0.5 # minutes

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
       Specifically checks for early rushing and high fast-wrong rate.
    """
    analysis = {
        'early_rushing_questions_indices': [],
        'early_rushing_flag_for_review': False,
        'fast_wrong_rate': None, # Based on is_relatively_fast
        'carelessness_issue': False, # Based on fast_wrong_rate > 0.25
    }
    if df_v.empty:
        return analysis

    total_questions = len(df_v)

    # 1. Early Rushing Risk (V-Doc Ch5)
    # Ensure necessary columns exist
    if 'question_position' in df_v.columns and 'question_time' in df_v.columns:
        early_pos_limit = total_questions / 3
        # Use 1.0 min threshold as per V-Doc
        early_rush_mask = (
            (df_v['question_position'] <= early_pos_limit) &
            (df_v['question_time'] < 1.0)
        )
        early_rushing_indices = df_v[early_rush_mask].index.tolist()
        if early_rushing_indices:
            analysis['early_rushing_questions_indices'] = early_rushing_indices
            analysis['early_rushing_flag_for_review'] = True
            print(f"      Ch5 Pattern: Found {len(early_rushing_indices)} potentially rushed questions in first third.")

    # 2. Carelessness Issue (V-Doc Ch5)
    # Requires is_relatively_fast calculation (based on avg time * 0.75)
    # This calculation should ideally happen in Chapter 3 rule application.
    # Assuming 'is_relatively_fast_ch3' column exists from _apply_ch3_diagnostic_rules
    if 'is_relatively_fast_ch3' in df_v.columns and 'is_correct' in df_v.columns: # Use 'is_correct'
        fast_mask = df_v['is_relatively_fast_ch3'] == True
        num_relatively_fast_total = fast_mask.sum()
        num_relatively_fast_incorrect = (fast_mask & (df_v['is_correct'] == False)).sum() # Use 'is_correct'

        if num_relatively_fast_total > 0:
            fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
            analysis['fast_wrong_rate'] = fast_wrong_rate
            # V-Doc threshold is 0.25
            if fast_wrong_rate > 0.25:
                analysis['carelessness_issue'] = True
                print(f"      Ch5 Pattern: Carelessness issue flagged (Fast-Wrong Rate: {fast_wrong_rate:.1%} > 25%)")
            else:
                print(f"      Ch5 Pattern: Fast-Wrong Rate = {fast_wrong_rate:.1%}")
        else:
            print("      Ch5 Pattern: No 'relatively fast' questions found to calculate carelessness rate.")
    else:
        print("      Ch5 Pattern: Skipping carelessness rate calculation ('is_relatively_fast_ch3' or 'is_correct' column missing).")

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


# --- Main V Diagnosis Runner ---

def run_v_diagnosis(df_v, v_time_pressure_status, num_invalid_v_questions, v_avg_time_per_type):
    """
    Runs the diagnostic analysis specifically for the Verbal section.

    Args:
        df_v (pd.DataFrame): DataFrame containing only VALID Verbal response data.
                             Processed by the main diagnosis module (invalid filtered out).
                             Includes simulated 'question_difficulty'.
                             Expected columns added by main module: 'overtime' (for CR), 'suspiciously_fast'.
                             Assumes 'question_time' is in MINUTES.
        v_time_pressure_status (bool): The calculated time pressure status for Verbal (True=High, False=Low).
        num_invalid_v_questions (int): Number of invalid questions excluded for Verbal.
        v_avg_time_per_type (dict): Dictionary mapping question type to average time (minutes).

    Returns:
        dict: A dictionary containing the results of the Verbal diagnosis, structured by chapter.
               Example: {'chapter_1': {...}, 'chapter_2': {...}, ...}
        str: A string containing the summary report for the Verbal section.
    """
    print("--- Entering run_v_diagnosis ---") # 添加標記
    print(f"  Received df_v shape: {df_v.shape}") # 打印形狀
    if 'is_correct' in df_v.columns:
        print(f"  Value counts for 'is_correct' at entry:\n{df_v['is_correct'].value_counts()}") # 打印 is_correct 值分佈
    else:
        print("  'is_correct' column NOT FOUND at entry!")
        print(f"  Available columns: {df_v.columns.tolist()}") # 列出可用欄位
    # --- End Debug Print ---

    print("  Running Verbal Diagnosis...")
    v_diagnosis_results = {}

    # --- Chapter 1: Applying RC Specific Logic & Global Rules ---
    print("    Chapter 1: Applying RC Specific Logic & Global Rules")
    v_diagnosis_results['chapter_1'] = {
        'time_pressure_status': v_time_pressure_status,
        'invalid_questions_excluded': num_invalid_v_questions,
        'reading_comprehension_barrier_inquiry': False,
        'rc_group_details': {} # Store num_q, target_time, reading_time per group
    }
    # Potentially add more detailed V-specific time analysis here if needed, beyond the main module's overall check

    # --- Chapter 1.1: RC Group Identification and Time Calculation ---
    df_v = _identify_rc_groups(df_v)
    df_v = _calculate_rc_times(df_v)

    # --- Chapter 1.2: RC Reading Time Barrier & Overtime Rules ---
    df_v['reading_comprehension_barrier_inquiry'] = False
    df_v['group_overtime'] = False
    df_v['individual_overtime'] = False

    # Calculate group target times based on pressure
    target_times = RC_GROUP_TARGET_TIMES.get(v_time_pressure_status, RC_GROUP_TARGET_TIMES[False]) # Default to low pressure if status unknown

    rc_groups = df_v[df_v['question_type'] == 'RC'].groupby('rc_group_id')
    for group_id, group_df in rc_groups:
        num_q_in_group = len(group_df)
        group_total_time = group_df['rc_group_total_time'].iloc[0]
        group_target_time = target_times.get(num_q_in_group)

        # Check reading time barrier (on first question)
        first_q = group_df.sort_values('question_position').iloc[0]
        reading_time = first_q['rc_reading_time']
        reading_barrier = False
        if pd.notna(reading_time):
            if num_q_in_group == 3 and reading_time > RC_READING_TIME_THRESHOLD_3Q:
                reading_barrier = True
            elif num_q_in_group >= 4 and reading_time > RC_READING_TIME_THRESHOLD_4Q:
                reading_barrier = True
            if reading_barrier:
                df_v.loc[first_q.name, 'reading_comprehension_barrier_inquiry'] = True
                v_diagnosis_results['chapter_1']['reading_comprehension_barrier_inquiry'] = True # Set global flag if triggered anywhere

        # Check group overtime
        is_group_overtime = False
        if pd.notna(group_total_time) and group_target_time is not None:
            if group_total_time > (group_target_time + RC_GROUP_TARGET_TIME_ADJUSTMENT):
                 is_group_overtime = True
                 df_v.loc[group_df.index, 'group_overtime'] = True

        # Check individual RC overtime
        for index, row in group_df.iterrows():
            q_time = row['question_time']
            is_first_q = index == first_q.name
            reading_time_val = reading_time if pd.notna(reading_time) else 0

            adjusted_rc_time = q_time - reading_time_val if is_first_q else q_time

            if adjusted_rc_time > RC_INDIVIDUAL_Q_THRESHOLD_MINUTES:
                df_v.loc[index, 'individual_overtime'] = True

        # Store group details for reporting
        v_diagnosis_results['chapter_1']['rc_group_details'][group_id] = {
            'num_questions': num_q_in_group,
            'total_time': group_total_time,
            'target_time': group_target_time,
            'reading_time': reading_time,
            'is_group_overtime': is_group_overtime,
            'has_reading_barrier': reading_barrier
        }

    # --- Initialize 'overtime' column before assigning RC True values ---
    if 'overtime' not in df_v.columns:
        df_v['overtime'] = False # Initialize CR rows (and default RC) to False
    else:
        # If main module added CR overtime, ensure RC rows default to False before specific RC rules apply
        df_v.loc[df_v['question_type'] == 'RC', 'overtime'] = df_v.loc[df_v['question_type'] == 'RC', 'overtime'].fillna(False)
    # --- End Initialization ---

    # Final RC overtime status (for Ch3 'is_slow')
    # Combine the specific RC overtime conditions
    rc_overtime_mask = (df_v['question_type'] == 'RC') & (df_v['group_overtime'] | df_v['individual_overtime'])
    # Assign True only where the RC mask is True, keeping existing CR flags
    df_v.loc[rc_overtime_mask, 'overtime'] = True

    # --- Reset index after complex Chapter 1 manipulations ---
    df_v.reset_index(drop=True, inplace=True)
    # --- End Reset ---

    # --- Chapter 1.3: Store modified dataframe for subsequent chapters ---
    # This df_v now contains rc_group_id, times, and overtime flags

    # --- Add Difficulty Grade Column (for Ch2 analysis) ---
    if 'question_difficulty' in df_v.columns:
         df_v['difficulty_grade'] = df_v['question_difficulty'].apply(_grade_difficulty_v)
    else:
         df_v['difficulty_grade'] = 'Unknown Difficulty'

    # --- Chapter 2: CR/RC Performance Overview ---
    print("    Chapter 2: CR/RC Performance Overview")
    if df_v.empty or 'question_type' not in df_v.columns:
        print("      Skipping Chapter 2 due to missing data or 'question_type' column.")
        v_diagnosis_results['chapter_2'] = {
            'by_type': {},
            'by_difficulty': {},
            'by_type_difficulty': {}
        }
    else:
        type_analysis = _analyze_dimension(df_v, 'question_type')
        difficulty_analysis = _analyze_dimension(df_v, 'difficulty_grade')

        # Analyze by Type and Difficulty combined
        type_difficulty_analysis = {}
        if 'question_type' in df_v.columns and 'difficulty_grade' in df_v.columns:
            grouped = df_v.groupby(['question_type', 'difficulty_grade'])
            for name, group in grouped:
                q_type, diff_grade = name
                if q_type not in type_difficulty_analysis:
                    type_difficulty_analysis[q_type] = {}
                type_difficulty_analysis[q_type][diff_grade] = _calculate_metrics_for_group(group)

        v_diagnosis_results['chapter_2'] = {
            'by_type': type_analysis,
            'by_difficulty': difficulty_analysis,
            'by_type_difficulty': type_difficulty_analysis
        }
        print(f"      Type Analysis: {type_analysis}")
        print(f"      Difficulty Analysis: {difficulty_analysis}")
        # print(f"      Type x Difficulty Analysis: {type_difficulty_analysis}") # Too verbose

    # --- Chapter 3: Deep Dive into Errors ---
    print("    Chapter 3: Deep Dive into Errors")
    # ...

    # --- Chapter 3.1: Pre-computation (Max Correct Difficulty) ---
    max_correct_difficulty_per_skill = {}
    if 'question_fundamental_skill' in df_v.columns and 'question_difficulty' in df_v.columns:
        # --- Debug Print Before Calculation ---
        print("    DEBUG: Before calculating Max Correct Difficulty:")
        if 'is_correct' in df_v.columns:
             print(f"      Value counts for 'is_correct':\n{df_v['is_correct'].value_counts()}")
        else:
             print("      'is_correct' column missing!")
        # --- End Debug Print ---

        correct_df = df_v[df_v['is_correct'] == True].copy() # Use 'is_correct'
        if not correct_df.empty:
             max_correct_difficulty_per_skill = correct_df.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()
        print(f"      Calculated Max Correct Difficulty per Skill: {max_correct_difficulty_per_skill}")
    else:
        print("      Skipping Max Correct Difficulty calculation (missing skill or difficulty data).")
    # ...

    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        print("      Skipping Chapter 3 due to missing data or 'question_fundamental_skill' column.")
        cr_error_analysis = _analyze_error_types(pd.DataFrame(), 'CR')
        rc_error_analysis = _analyze_error_types(pd.DataFrame(), 'RC')
    else:
        # --- Add Debug Print for Question Types ---
        print("    DEBUG: Before creating df_cr/df_rc:")
        if 'question_type' in df_v.columns:
             print(f"      df_v 'question_type' counts:\n{df_v['question_type'].value_counts()}")
             print(f"      df_v 'is_correct' counts (again):\n{df_v['is_correct'].value_counts()}")
        else:
             print("      'question_type' column missing in df_v!")
        # --- End Debug Print ---

        # --- CORRECTED: Always define df_cr and df_rc here from current df_v ---
        # Use expected type names exactly
        df_cr = df_v[df_v['question_type'] == 'Critical Reasoning'].copy()
        df_rc = df_v[df_v['question_type'] == 'Reading Comprehension'].copy()
        # --- END CORRECTION ---

        # --- Add Debug Print for df_cr/df_rc shapes and correctness ---
        print(f"    DEBUG: After filtering by type:")
        print(f"      df_cr shape: {df_cr.shape}")
        if not df_cr.empty: print(f"      df_cr 'is_correct' counts:\n{df_cr['is_correct'].value_counts()}")
        print(f"      df_rc shape: {df_rc.shape}")
        if not df_rc.empty: print(f"      df_rc 'is_correct' counts:\n{df_rc['is_correct'].value_counts()}")
        # --- End Debug Print ---

        # Analyze errors for each type
        cr_errors = df_cr[df_cr['is_correct'] == False] # Use 'is_correct'
        rc_errors = df_rc[df_rc['is_correct'] == False] # Use 'is_correct'

        print(f"      Analyzing {len(cr_errors)} CR errors...") # Should now be non-zero if CR errors exist
        cr_error_analysis = _analyze_error_types(cr_errors, 'CR')
        print(f"      Analyzing {len(rc_errors)} RC errors...")
        rc_error_analysis = _analyze_error_types(rc_errors, 'RC')

    v_diagnosis_results['chapter_3'] = {
        'cr_error_analysis': cr_error_analysis,
        'rc_error_analysis': rc_error_analysis,
        'diagnosed_dataframe': df_v # Store the dataframe with params
    }
    # Optional: Print summary of dominant error types
    # Need to recalculate dominant error type based on the new analysis structure
    # print(f"        CR Dominant Error Type: {cr_error_analysis.get('dominant_error_type', 'N/A')}")
    # For now, just acknowledge the analysis was done
    print(f"        CR error analysis complete. Found {len(cr_errors)} errors.")
    print(f"        RC error analysis complete. Found {len(rc_errors)} errors.")


    # --- Chapter 3.2: Applying Diagnostic Rules ---
    # Reset index BEFORE applying rules to ensure unique index for .loc assignments inside the function
    df_v.reset_index(drop=True, inplace=True) # Add this line
    df_v = _apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill, v_avg_time_per_type)


    # --- Chapter 4: Correct but Slow Analysis ---
    print("    Chapter 4: Correct but Slow Analysis")
    cr_correct_slow_analysis = {}
    rc_correct_slow_analysis = {}

    # Need the original DFs (before filtering for errors)
    if df_v.empty or 'question_time' not in df_v.columns:
         print("      Skipping Chapter 4 due to missing data or 'question_time' column.")
         cr_correct_slow_analysis = _analyze_correct_slow(pd.DataFrame(), 'CR')
         rc_correct_slow_analysis = _analyze_correct_slow(pd.DataFrame(), 'RC')
    else:
        # Ensure dfs are defined even if previous chapters were skipped
        if 'df_cr' not in locals(): df_cr = df_v[df_v['question_type'] == 'CR'].copy()
        if 'df_rc' not in locals(): df_rc = df_v[df_v['question_type'] == 'RC'].copy()

        cr_correct = df_cr[df_cr['is_correct'] == True].copy() # Use 'is_correct', explicitly copy
        rc_correct = df_rc[df_rc['is_correct'] == True].copy() # Use 'is_correct', explicitly copy

        # Reset index before passing to the analysis function
        cr_correct.reset_index(drop=True, inplace=True)
        rc_correct.reset_index(drop=True, inplace=True)

        print(f"      Analyzing {len(cr_correct)} correct CR questions for slowness...")
        cr_correct_slow_analysis = _analyze_correct_slow(cr_correct, 'CR')
        print(f"      Analyzing {len(rc_correct)} correct RC questions for slowness...")
        rc_correct_slow_analysis = _analyze_correct_slow(rc_correct, 'RC')

    v_diagnosis_results['chapter_4'] = {
        'cr_correct_slow': cr_correct_slow_analysis,
        'rc_correct_slow': rc_correct_slow_analysis
    }
    # Optional: Print summary
    print(f"        CR Correct but Slow Rate: {cr_correct_slow_analysis.get('correct_slow_rate', 0.0):.1%}")
    print(f"        RC Correct but Slow Rate: {rc_correct_slow_analysis.get('correct_slow_rate', 0.0):.1%}")


    # --- Chapter 5: Pattern Observation ---
    print("    Chapter 5: Pattern Observation")
    pattern_analysis = _observe_patterns(df_v, v_time_pressure_status)
    v_diagnosis_results['chapter_5'] = pattern_analysis
    # Optional: Print summary of key findings
    print(f"        Early Rushing Risk: {len(pattern_analysis.get('early_rushing_questions_indices', []))} potentially rushed questions in first third.")
    print(f"        Fast-Wrong Rate: {pattern_analysis.get('fast_wrong_rate', 'N/A')}")
    print(f"        Carelessness Issue: {pattern_analysis.get('carelessness_issue', False)}")

    # --- Chapter 6: Skill Override Rule (V-Doc Definition) ---
    print("    Chapter 6: Skill Override Rule")
    skill_override_analysis = _calculate_skill_override(df_v)
    v_diagnosis_results['chapter_6'] = skill_override_analysis
    # Optional: Print summary
    triggered_overrides = {k: v for k, v in skill_override_analysis.get('skill_override_triggered', {}).items() if v}
    print(f"        Skill Override Triggered (>50% error rate): {triggered_overrides}")

    # --- Chapter 7: Recommendations ---
    print("    Chapter 7: Recommendations")
    # Pass override results to recommendation generator
    # Removed exempted_v_skills argument
    print("DEBUG: --- Calling _generate_v_recommendations ---") # DEBUG
    recommendations = _generate_v_recommendations(v_diagnosis_results)
    v_diagnosis_results['chapter_7'] = recommendations
    # Optional: Print summary of recommendations generated - Keep this line
    print(f"        Generated {len(recommendations)} recommendation items.") # Keep original print
    print("DEBUG: --- Returned from _generate_v_recommendations ---") # DEBUG

    # --- Chapter 8: Summary Report Generation ---
    print("    Chapter 8: Summary Report Generation")
    print("DEBUG: --- Calling _generate_v_summary_report ---") # DEBUG
    v_report_summary = _generate_v_summary_report(v_diagnosis_results)
    # Optional: Print first few lines of the report - Keep this line
    print(f"        Generated Report (first 100 chars): {v_report_summary[:100]}...") # Keep original print
    print("DEBUG: --- Returned from _generate_v_summary_report ---") # DEBUG

    print("  Verbal Diagnosis Complete.")
    # Return the results dict and the generated report string.
    return v_diagnosis_results, v_report_summary


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
    'EFFICIENCY_BOTTLENECK_CR_READING': "效率問題: CR 閱讀理解環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_CR_LOGIC': "效率問題: CR 邏輯分析環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_RC_READING': "效率問題: RC 閱讀理解環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_RC_ANALYSIS': "效率問題: RC 推理分析環節導致效率低下",
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
}

def _translate_v(param):
    """Translates an internal V param/skill name using APPENDIX_A_TRANSLATION_V."""
    return APPENDIX_A_TRANSLATION_V.get(param, param)

# --- V Summary Report Generation Helper ---

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value) # Ensure it's a string

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
    report_lines.append("**1. 時間策略與有效性 (摘要)**")
    tp_status = _translate_v(ch1.get('time_pressure_status', 'Unknown'))
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體時間壓力感知: {tp_status}")
    if invalid_count > 0:
        report_lines.append(f"- 因時間過短/過長被排除的無效題目數: {invalid_count}")
    report_lines.append("")

    # --- Section 2: CR/RC 表現概覽 --- # Title updated
    report_lines.append("**2. CR/RC 表現概覽**") 
    type_metrics = ch2.get('by_type', {})
    difficulty_metrics = ch2.get('by_difficulty', {})
    type_difficulty_metrics = ch2.get('by_type_difficulty', {})

    # Overall by Type (Filter for CR/RC)
    report_lines.append("  *按題型匯總:*")
    for q_type in ['CR', 'RC']:
        if q_type in type_metrics:
            metrics = type_metrics[q_type]
            # Format rates before f-string
            error_rate_str = _format_rate(metrics.get('error_rate', 0.0))
            report_lines.append(f"    - **{q_type}:** {metrics.get('total_questions')} 題, 錯誤率 {error_rate_str}, 平均耗時 {metrics.get('avg_time_spent', 0.0):.2f} 分鐘")

    # Overall by Difficulty
    report_lines.append("  *按難度匯總:*")
    sorted_grades = sorted(difficulty_metrics.keys(), key=lambda g: ('Unknown' in g, 'Low' in g, 'Mid' in g, 'High' in g, g))
    for grade in sorted_grades:
        metrics = difficulty_metrics[grade]
        # Format rate before f-string
        error_rate_str = _format_rate(metrics.get('error_rate', 0.0))
        report_lines.append(f"    - **{_translate_v(grade)}:** {metrics.get('total_questions')} 題, 錯誤率 {error_rate_str}")

    # Detailed by Type and Difficulty (Filter for CR/RC)
    report_lines.append("  *分題型與難度交叉分析 (錯誤率):*")
    for q_type in ['CR', 'RC']:
        if q_type in type_difficulty_metrics:
            line = f"    - **{q_type}:**"
            grade_parts = []
            type_grades = type_difficulty_metrics[q_type]
            sorted_type_grades = sorted(type_grades.keys(), key=lambda g: ('Unknown' in g, 'Low' in g, 'Mid' in g, 'High' in g, g))
            for grade in sorted_type_grades:
                metrics = type_grades[grade]
                # Format rate before f-string (note: .0% formatting)
                error_rate_str = "N/A"
                rate_val = metrics.get('error_rate', None)
                if isinstance(rate_val, (int, float)):
                    error_rate_str = f"{rate_val:.0%}" # Use .0% here as per original code
                grade_parts.append(f"{_translate_v(grade)} [{error_rate_str}]")
            line += " | ".join(grade_parts)
            report_lines.append(line)

    report_lines.append("")

    # --- Section 3: 錯誤深入分析 --- 
    report_lines.append("**3. 錯誤深入分析 (基於 Fundamental Skill)**")
    has_ch3_data = False
    for q_type in ['CR', 'RC']: # Filter for CR/RC
        analysis = ch3.get(f'{q_type.lower()}_error_analysis', {}) 
        if analysis.get('total_errors', 0) > 0:
            has_ch3_data = True
            report_lines.append(f"- **{q_type} ({analysis.get('total_errors')} 處錯誤):**")
            dom_error = _translate_v(analysis.get('dominant_error_type', 'N/A'))
            # Format rates before f-string
            read_rate_str = _format_rate(analysis.get('reading_understanding_rate', 0.0))
            logic_rate_str = _format_rate(analysis.get('logic_grammar_inference_rate', 0.0))
            sfe_rate_str = _format_rate(analysis.get('sfe_rate', 0.0))
            report_lines.append(f"  - 主要錯誤類型歸因: **{dom_error}**")
            report_lines.append(f"    - {_translate_v('Reading/Understanding')} 佔比: {read_rate_str}")
            report_lines.append(f"    - {_translate_v('Logic/Grammar/Inference')} 佔比: {logic_rate_str}")
            if analysis.get('sfe_rate', 0.0) > 0:
                 report_lines.append(f"    - {_translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')} 佔比: {sfe_rate_str}")
            # Optional: List top N error skills
            top_skills = sorted(analysis.get('skill_breakdown', {}).items(), key=lambda item: item[1], reverse=True)[:3]
            if top_skills:
                report_lines.append(f"  - 最常見錯誤技能: {', '.join([f'{_translate_v(s)} ({c})' for s, c in top_skills])}")
    if not has_ch3_data:
         report_lines.append("- 無法進行錯誤類型分析 (可能缺少 Fundamental Skill 數據)。")
    report_lines.append("")

    # --- Section 4: 正確但低效分析 --- 
    report_lines.append("**4. 正確但低效分析**")
    has_ch4_data = False
    for q_type in ['CR', 'RC']: # Filter for CR/RC
        analysis = ch4.get(f'{q_type.lower()}_correct_slow', {})
        if analysis.get('total_correct', 0) > 0:
            has_ch4_data = True
            slow_rate = analysis.get('correct_slow_rate', 0.0)
            if slow_rate > 0.1: # Only report if significant
                slow_rate_str = _format_rate(slow_rate) # Format rate
                report_lines.append(f"- **{q_type}:**")
                report_lines.append(f"  - 正確題目中耗時過長比例: {slow_rate_str}")
                bottleneck = _translate_v(analysis.get('dominant_bottleneck_type', 'N/A'))
                report_lines.append(f"  - 主要效率瓶頸歸因: **{bottleneck}**")
                avg_time = analysis.get('avg_time_slow', 0.0)
                report_lines.append(f"  - 慢題平均耗時: {avg_time:.2f} 分鐘")
    if not has_ch4_data:
         report_lines.append("- 無法進行低效分析 (可能缺少時間數據或無正確題目)。")
    elif not any(ch4.get(f'{qt.lower()}_correct_slow', {}).get('correct_slow_rate', 0.0) > 0.1 for qt in ['CR', 'RC']): # Filter check
         report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 模式觀察與行為分析 --- (This section is generally applicable)
    report_lines.append("**5. 模式觀察與行為分析**")
    # Ensure flags are Python bools
    early_rushing_flag = bool(ch5.get('early_rushing_flag_for_review', False))
    carelessness_issue = bool(ch5.get('carelessness_issue', False))
    fast_wrong_rate = ch5.get('fast_wrong_rate') # Can be None

    pattern_found = False
    if early_rushing_flag:
         report_lines.append("- **注意前期節奏**: 測驗前期出現作答時間過短 (<'1分鐘') 的情況，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。")
         pattern_found = True
    if carelessness_issue:
        fast_wrong_rate_str = _format_rate(fast_wrong_rate) if fast_wrong_rate is not None else ""
        fast_wrong_rate_text = f" ({fast_wrong_rate_str})" if fast_wrong_rate_str else ""
        report_lines.append(f"- **注意粗心問題**: 數據顯示「快而錯」的比例偏高{fast_wrong_rate_text}，提示可能存在粗心問題。建議放慢審題速度，仔細閱讀題目和選項，核對關鍵信息。")
        pattern_found = True

    if not pattern_found:
        report_lines.append("- 未發現明顯的負面行為模式 (前期過快、粗心)。")
    report_lines.append("")

    # --- Section 6: 基礎能力覆蓋規則 --- 
    report_lines.append("**6. 基礎能力覆蓋規則**")
    override_triggered = ch6.get('skill_override_triggered', {})
    # Ensure boolean conversion when checking triggered status
    triggered_skills = [s for s, triggered in override_triggered.items() if bool(triggered)]

    # Check if the original dictionary was empty or None before checking the list
    if not override_triggered:
         report_lines.append("- 無法進行技能覆蓋分析 (可能缺少 Fundamental Skill 數據或計算錯誤)。")
    elif triggered_skills:
        translated_skills = [_translate_v(s) for s in triggered_skills]
        report_lines.append(f"- **觸發基礎鞏固建議的技能 (錯誤率 > 50%):** {', '.join(translated_skills)}")
    else:
        report_lines.append("- 所有核心技能的整體錯誤率均未超過 50%，未觸發基礎能力覆蓋規則。")
    report_lines.append("")

    # --- Section 7: 練習建議 ---
    report_lines.append("**7. 練習建議**")
    if not ch7:
        report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        for i, rec in enumerate(ch7):
            report_lines.append(f"{i+1}. {rec.get('text', '無建議內容')}") # Assuming rec['text'] contains formatted recommendation
            report_lines.append("") # Add space between recommendations

    report_lines.append("\n**7. 後續行動指引**")

    # Core Constraint (Implicit in using _translate_v)
    # Report must use natural language via Appendix A translation.

    # Guide Reflection
    report_lines.append("  *引導反思:*")
    report_lines.append("    - **CR 相關：** 回想做錯的 CR 題，是沒看懂題幹的邏輯關係，還是選項難以排除？是哪種題型（削弱、加強、假設等）更容易出錯？")
    report_lines.append("    - **RC 相關：** 回想做錯的 RC 題，是文章沒讀懂，題目問啥沒理解，還是定位到了但理解有偏差？是否存在特定主題或文章結構的閱讀困難？基礎閱讀（詞彙、長難句）是否存在明顯瓶頸？")

    # Secondary Evidence Suggestion (Generic trigger for now)
    report_lines.append("  *二級證據參考建議:*")
    report_lines.append("    - **觸發時機：** 當您無法準確回憶具體的錯誤原因、涉及的技能弱點或題型，或需要更客觀的數據來確認問題模式時。")
    report_lines.append("    - **建議行動：** 『為了更精確地定位您在 [某技能/題型] 上的具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些技能點、題型或錯誤類型（參考 **附錄 A** 中的描述）反覆出現問題。』")

    # Qualitative Analysis Suggestion (Generic trigger for now)
    report_lines.append("  *質化分析建議:*")
    report_lines.append("    - **觸發時機：** 當您對診斷報告指出的錯誤原因感到困惑，特別是涉及複雜的邏輯推理或閱讀理解過程時，或者上述方法仍無法幫您釐清根本問題時。")
    report_lines.append("    - **建議行動：** 『如果您對 [某類問題，例如 CR 邏輯鏈分析或 RC 推理過程] 的錯誤原因仍感困惑，可以嘗試 **提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。』")

    # Tool Recommendations (Based on triggered parameters)
    report_lines.append("  *輔助工具/提示推薦:*")
    triggered_params_all = set()
    if ch3:
        # Consolidate all unique diagnostic params triggered across all questions
        diagnosed_df = ch3.get('diagnosed_dataframe')
        if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
             all_param_lists = diagnosed_df['diagnostic_params'].tolist()
             triggered_params_all = set(p for sublist in all_param_lists for p in sublist)

    # Add behavioral params if triggered (ensure bool conversion)
    if bool(ch5.get('early_rushing_flag_for_review', False)):
         triggered_params_all.add('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    if bool(ch5.get('carelessness_issue', False)):
         triggered_params_all.add('BEHAVIOR_CARELESSNESS_ISSUE')
    # Assuming BEHAVIOR_GUESSING_HASTY might be added in Ch3 rules if needed

    recommended_tools_desc = []
    # Map triggered params to tool recommendations based on V-Doc Ch 8.7 logic
    tool_recommendations_map = {
        # CR Reasoning/Type Specific
        frozenset(['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']):
            "可能適用外部工具 `Dustin_GMAT_CR_Core_Issue_Identifier` 或 `Dustin_GMAT_CR_Chain_Argument_Evaluation`，或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_METHOD_TYPE_SPECIFIC_ERROR']): # Needs specification for Boldface/Argument Construction
            "特定 CR 題型（如 Boldface, Argument Construction）困難，可能適用外部工具如 `Dustin's GMAT CR: Boldface Interactive Tutor` 或 `Dustin_GMAT_CR_Role_Argument_Construction`，或使用 AI 提示 `Verbal-related/01_basic_explanation.md`, `Verbal-related/05_evaluate_explanation.md`, `Verbal-related/06_boldface_SOP.md`。",
        frozenset(['CR_REASONING_ABSTRACTION_DIFFICULTY']):
            "CR 抽象邏輯或術語理解困難，可能適用外部工具 `Dustin's GMAT Tool: Textbook Explainer` 或 AI 提示 `Verbal-related/07_logical_term_explained.md`, `Verbal-related/09_complex_sentence_rewrite.md`。",
        # ... (Add mappings for all params listed in V-Doc Ch 8.7) ...

        # RC Reading Comprehension
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

    # Generate tool recommendations based on triggered params
    processed_for_tools = set()
    for params_set, tool_desc in tool_recommendations_map.items():
        # The any() and issubset() check should be robust against this error
        if any(p in triggered_params_all for p in params_set) and not params_set.issubset(processed_for_tools):
            trigger_reasons = [_translate_v(p) for p in params_set if p in triggered_params_all]
            if trigger_reasons:
                 report_lines.append(f"    - **基於診斷發現 ({', '.join(trigger_reasons)}):** {tool_desc}")
                 processed_for_tools.update(params_set)

    # Check processed_for_tools (set) emptiness correctly
    if not processed_for_tools and len(triggered_params_all) <= 5:
         report_lines.append("    - 根據當前診斷結果，暫無特別推薦的輔助工具。")

    report_lines.append("\n--- 報告結束 ---")
    print("DEBUG: --- Exiting _generate_v_summary_report ---") # DEBUG
    # Use double newline for Markdown paragraph breaks
    return "\n\n".join(report_lines)

# --- V Recommendation Generation Helper ---

def _generate_v_recommendations(v_diagnosis_results):
    """Generates practice recommendations based on V diagnosis results."""
    print("DEBUG: +++ Entering _generate_v_recommendations +++") # DEBUG
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
        skill_recs_list = []
        is_overridden = skill_override_triggered.get(skill, False)
        print(f"      Processing Skill: {skill}, Overridden: {is_overridden}")

        if is_overridden and skill not in processed_macro_skills:
            # Generate Macro Recommendation (V-Doc Ch7)
            macro_rec_text = f"針對【{_translate_v(skill)}】技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
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
                    is_slow = row.get('overtime', False)
                    is_sfe = row.get('is_sfe', False)
                    q_pos = row['question_position']
                    difficulty = row.get('question_difficulty')
                    time = row.get('question_time')
                    q_type = row['question_type']

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
                        case_rec_text = f"針對【{_translate_v(skill)}】下的問題 (Position {q_pos}, {trigger_desc})：建議練習【{y}】難度題目，起始練習限時建議為【{z:.1f}】分鐘。(目標時間：{'CR 2.0 / RC 1.5'}分鐘)。"
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
        final_recommendations.append({'type': 'skill_header', 'text': f"--- 技能: {_translate_v(skill)} ---"}) # Add header as dict item
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
    """Applies Chapter 3 diagnostic rules row-by-row."""
    if 'question_type' not in df_v.columns:
         print("      Cannot apply Chapter 3 rules: 'question_type' missing.")
         # Return original df and indicate failure? Or add empty columns?
         df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
         df_v['is_sfe'] = False
         df_v['is_relatively_fast_ch3'] = False
         return df_v

    # Initialize lists to store results
    all_diagnostic_params = []
    all_is_sfe = []
    all_is_relatively_fast_ch3 = []

    # Use average times passed from the main module
    if not avg_time_per_type:
        print("      Warning: Average time per type data not available for Chapter 3 rule application.")
        # Fallback: recalculate locally, but might differ from main module's calculation
        avg_time_per_type = df_v.groupby('question_type')['question_time'].mean().to_dict()

    # Make sure index is sequential if iterating with it (though we use iterrows)
    df_v_reset = df_v.reset_index(drop=True)

    for index, row in df_v_reset.iterrows(): # Iterate over the reset index df
        params = []
        q_type = row['question_type']
        q_time = row['question_time']
        is_correct = row['is_correct'] # Use 'is_correct'
        difficulty = row.get('question_difficulty')
        skill = row.get('question_fundamental_skill', 'Unknown Skill')
        # Use combined RC overtime flag calculated in Ch1
        is_overtime = row.get('overtime', False)
        # is_suspiciously_fast_flag = row.get('suspiciously_fast', False) # This flag is from main module, might not be needed directly here

        # 1. Time Performance Classification (Simplified - use suspicious_fast flag, rely on overtime flag)
        avg_time = avg_time_per_type.get(q_type, np.inf)
        # is_relatively_fast check from V-doc Ch3 uses 0.75 multiplier, differs from suspicious_fast (0.5)
        current_is_relatively_fast_ch3 = q_time < avg_time * 0.75
        is_slow = is_overtime # Slow uses the flag set based on CR/RC rules
        is_normal_time = not current_is_relatively_fast_ch3 and not is_slow

        # 2. Special Focus Error (SFE)
        current_is_sfe = False
        if not is_correct and difficulty is not None and skill != 'Unknown Skill' and skill in max_correct_difficulty_per_skill:
            max_diff = max_correct_difficulty_per_skill[skill]
            # Check if difficulty is strictly less than max correct difficulty for that skill
            if difficulty < max_diff:
                 current_is_sfe = True
                 params.append('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 3. Apply Rules based on Time/Correctness/Type (Based on V-Doc Ch3)
        # --- (Keep the existing rule logic here) ---
        if q_type == 'Critical Reasoning': # Use full name
            if current_is_relatively_fast_ch3 and not is_correct:
                # Fast & Wrong CR (V-Doc Ch3)
                params.extend([
                    'CR_METHOD_PROCESS_DEVIATION',
                    'CR_METHOD_TYPE_SPECIFIC_ERROR',
                    'CR_READING_BASIC_OMISSION'
                ])
                if q_time < V_INVALID_TIME_ABANDONED:
                    params.append('BEHAVIOR_GUESSING_HASTY')
            elif is_slow and not is_correct:
                # Slow & Wrong CR (V-Doc Ch3)
                params.extend([
                    'CR_READING_TIME_EXCESSIVE',
                    'CR_REASONING_TIME_EXCESSIVE',
                    'CR_AC_ANALYSIS_TIME_EXCESSIVE'
                ])
                # Include possible root causes also from "Normal Time & Wrong"
                params.extend([
                    'CR_REASONING_CHAIN_ERROR',
                    'CR_REASONING_ABSTRACTION_DIFFICULTY'
                ])
            elif is_normal_time and not is_correct:
                # Normal Time & Wrong CR (V-Doc Ch3)
                params.extend([
                    'CR_READING_DIFFICULTY_STEM',
                    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'CR_REASONING_CHAIN_ERROR',
                    'CR_REASONING_ABSTRACTION_DIFFICULTY',
                    'CR_REASONING_PREDICTION_ERROR',
                    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY',
                    'CR_AC_ANALYSIS_RELEVANCE_ERROR',
                    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION',
                    'CR_METHOD_TYPE_SPECIFIC_ERROR'
                ])
            elif is_slow and is_correct:
                # Slow & Correct CR (V-Doc Ch3)
                params.extend([
                    'EFFICIENCY_BOTTLENECK_READING',
                    'EFFICIENCY_BOTTLENECK_REASONING'
                ])

        elif q_type == 'Reading Comprehension': # Use full name
            if current_is_relatively_fast_ch3 and not is_correct:
                # Fast & Wrong RC (V-Doc Ch3)
                params.extend([
                    'RC_READING_INFO_LOCATION_ERROR',
                    'RC_READING_KEYWORD_LOGIC_OMISSION',
                    'RC_METHOD_TYPE_SPECIFIC_ERROR' # V-Doc doesn't list a specific RC method error param, using CR one as placeholder?
                ])
                if q_time < V_INVALID_TIME_ABANDONED:
                    params.append('BEHAVIOR_GUESSING_HASTY')
            elif is_slow and not is_correct:
                # Slow & Wrong RC (V-Doc Ch3)
                params.extend([
                    'RC_READING_SPEED_SLOW_FOUNDATIONAL',
                    'RC_METHOD_INEFFICIENT_READING',
                    'RC_LOCATION_TIME_EXCESSIVE',
                    'RC_REASONING_TIME_EXCESSIVE',
                    'RC_AC_ANALYSIS_TIME_EXCESSIVE'
                ])
                # Include possible root causes also from "Normal Time & Wrong"
                params.extend([
                    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                    'RC_REASONING_INFERENCE_WEAKNESS'
                ])
            elif is_normal_time and not is_correct:
                # Normal Time & Wrong RC (V-Doc Ch3)
                params.extend([
                    'RC_READING_VOCAB_BOTTLENECK',
                    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY',
                    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                    'RC_READING_DOMAIN_KNOWLEDGE_GAP',
                    'RC_READING_PRECISION_INSUFFICIENT',
                    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION',
                    'RC_LOCATION_ERROR_INEFFICIENCY',
                    'RC_REASONING_INFERENCE_WEAKNESS',
                    'RC_AC_ANALYSIS_DIFFICULTY',
                    # 'RC_METHOD_TYPE_SPECIFIC_ERROR' # V-Doc doesn't define this for RC normal/wrong
                ])
            elif is_slow and is_correct:
                # Slow & Correct RC (V-Doc Ch3)
                params.extend([
                    'EFFICIENCY_BOTTLENECK_READING',
                    'EFFICIENCY_BOTTLENECK_LOCATION',
                    'EFFICIENCY_BOTTLENECK_REASONING',
                    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS'
                ])

        # Add reading comprehension barrier if triggered for this RC group (info should be in row)
        if q_type == 'Reading Comprehension' and row.get('reading_comprehension_barrier_inquiry', False):
            params.append('RC_READING_COMPREHENSION_BARRIER') # Parameter needs to be defined in Appendix A

        # Store unique params, ensuring SFE is first
        unique_params = list(set(params))
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
            unique_params.remove('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            unique_params.insert(0, 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # Append results to lists instead of assigning to df_v.loc
        all_diagnostic_params.append(unique_params)
        all_is_sfe.append(current_is_sfe)
        all_is_relatively_fast_ch3.append(current_is_relatively_fast_ch3)

    # After loop, assign collected lists to the original DataFrame
    # Ensure lengths match before assignment (should match df_v_reset length)
    if len(all_diagnostic_params) == len(df_v):
        df_v['diagnostic_params'] = all_diagnostic_params
        df_v['is_sfe'] = all_is_sfe
        df_v['is_relatively_fast_ch3'] = all_is_relatively_fast_ch3
    else:
        # This case indicates an unexpected issue during iteration
        print(f"      Error: Length mismatch after loop in _apply_ch3_diagnostic_rules. Expected {len(df_v)}, got {len(all_diagnostic_params)}. Skipping assignment.")
        # Add empty columns to prevent downstream errors if possible
        if 'diagnostic_params' not in df_v.columns:
             df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
        if 'is_sfe' not in df_v.columns:
             df_v['is_sfe'] = False
        if 'is_relatively_fast_ch3' not in df_v.columns:
            df_v['is_relatively_fast_ch3'] = False

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