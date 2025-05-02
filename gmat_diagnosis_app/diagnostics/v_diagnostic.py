import pandas as pd
import numpy as np

# --- V-Specific Constants (Add as needed) ---
# Example: Define time thresholds if needed later
# SC_AVG_TIME_THRESHOLD = 1.25 # minutes
# CR_AVG_TIME_THRESHOLD = 2.0 # minutes
# RC_AVG_TIME_THRESHOLD_PER_Q = 1.75 # minutes (assuming reading time is separate or amortized)

# Time thresholds (in seconds) - Adjust based on data/expert input
SC_TIME_THRESHOLD_SECONDS = 90   # 1.5 minutes
CR_TIME_THRESHOLD_SECONDS = 135  # 2.25 minutes
RC_TIME_THRESHOLD_SECONDS = 120  # 2.0 minutes per question (excluding passage reading? Needs refinement)
# Consider using percentile-based thresholds instead of fixed values if data varies widely.

# Map fundamental skills (expected in data) to broader error categories for Chapter 3
V_SKILL_TO_ERROR_CATEGORY = {
    # SC Reading/Understanding
    'V_SC_Meaning_Clarity': 'Reading/Understanding',
    'V_SC_Sentence_Structure': 'Reading/Understanding',
    # SC Grammar/Application
    'V_SC_Verb_Form_Tense': 'Grammar/Application',
    'V_SC_Pronoun_Reference_Agreement': 'Grammar/Application',
    'V_SC_Subject_Verb_Agreement': 'Grammar/Application',
    'V_SC_Modification_Placement': 'Grammar/Application',
    'V_SC_Parallelism_Structure': 'Grammar/Application',
    'V_SC_Comparison_Structure': 'Grammar/Application',
    'V_SC_Idiom_Usage_Diction': 'Grammar/Application',
    # CR Reading/Understanding
    'V_CR_Argument_Deconstruction': 'Reading/Understanding',
    'V_CR_Option_Interpretation': 'Reading/Understanding',
    # CR Logic/Reasoning
    'V_CR_Assumption_Identification': 'Logic/Reasoning',
    'V_CR_Strengthen_Weaken_Argument': 'Logic/Reasoning',
    'V_CR_Inference_Conclusion_Drawing': 'Logic/Reasoning',
    'V_CR_Evaluate_Argument_Method': 'Logic/Reasoning',
    'V_CR_Flaw_Identification': 'Logic/Reasoning',
    'V_CR_Explain_Resolve_Paradox': 'Logic/Reasoning',
    'V_CR_Boldface_Reasoning': 'Logic/Reasoning',
    # RC Reading/Understanding
    'V_RC_Passage_Comprehension': 'Reading/Understanding',
    'V_RC_Question_Stem_Analysis': 'Reading/Understanding',
    'V_RC_Option_Analysis': 'Reading/Understanding',
    # RC Inference/Application
    'V_RC_Main_Idea_Primary_Purpose': 'Inference/Application',
    'V_RC_Specific_Detail_Retrieval': 'Inference/Application',
    'V_RC_Inference_Implication': 'Inference/Application',
    'V_RC_Logical_Structure_Organization': 'Inference/Application',
    'V_RC_Application_Extrapolation': 'Inference/Application',
    'V_RC_Author_Tone_Attitude': 'Inference/Application',
    # Common - Foundational Mastery Instability
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    # Default/Unknown
    'Unknown Skill': 'Unknown',
    'DI_DATA_INTERPRETATION_ERROR': 'Unknown', # Should ideally not appear in V data
    'DI_LOGICAL_REASONING_ERROR': 'Unknown',
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'Unknown',
}

# Diagnostic Parameter Mapping (for direct use or later reference)
V_DIAGNOSTIC_PARAMS = {
    'SC': {
        'Reading/Understanding': 'V_SC_READING_COMPREHENSION_ERROR',
        'Grammar/Application': 'V_SC_GRAMMAR_APPLICATION_ERROR',
        'SFE': 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE'
    },
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
    sc_avg_error_rate = chapter2_metrics.get('sc_metrics', {}).get('error_rate', 0.0)
    cr_avg_error_rate = chapter2_metrics.get('cr_metrics', {}).get('error_rate', 0.0)
    rc_avg_error_rate = chapter2_metrics.get('rc_metrics', {}).get('error_rate', 0.0)

    # Map question types to their average error rates
    type_to_avg_error_rate = {
        'SC': sc_avg_error_rate,
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
        errors = group['Correct'].eq(False).sum()
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
            elif category in ['Logic/Reasoning', 'Grammar/Application', 'Inference/Application']: logic_etc_z_skills.append(skill)
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
            elif category in ['Logic/Reasoning', 'Grammar/Application', 'Inference/Application']: logic_etc_y_skills.append(skill)

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
    """Observes patterns and behavioral indicators for Chapter 5."""
    analysis = {
        'carelessness_error_count': 0,
        'carelessness_error_rate_overall': 0.0, # Rate relative to all questions
        'consecutive_errors_streaks': [], # List of (start_index, length)
        'consecutive_correct_streaks': [], # List of (start_index, length)
        'errors_in_last_third': 0,
        'error_rate_last_third': 0.0,
        'performance_under_pressure_notes': "N/A", # Qualitative note
        'difficulty_collapse_notes': "N/A" # Note if errors spike at higher difficulty
    }
    if df_v.empty:
        return analysis

    total_questions = len(df_v)
    df_v_sorted = df_v.sort_values(by='question_position').reset_index()

    # 1. Carelessness Errors
    if 'question_fundamental_skill' in df_v_sorted.columns:
        careless_mask = df_v_sorted['question_fundamental_skill'].isin(CARELESSNESS_SKILLS) & (df_v_sorted['Correct'] == False)
        analysis['carelessness_error_count'] = careless_mask.sum()
        if total_questions > 0:
             analysis['carelessness_error_rate_overall'] = analysis['carelessness_error_count'] / total_questions

    # 2. Consecutive Errors/Corrects (Streak length >= 3)
    min_streak_len = 3
    current_error_streak = 0
    current_correct_streak = 0
    error_streak_start = -1
    correct_streak_start = -1

    for i, row in df_v_sorted.iterrows():
        is_correct = row['Correct']
        if not is_correct:
            if current_error_streak == 0:
                error_streak_start = i
            current_error_streak += 1
            # End correct streak if running
            if current_correct_streak >= min_streak_len:
                analysis['consecutive_correct_streaks'].append((correct_streak_start, current_correct_streak))
            current_correct_streak = 0
            correct_streak_start = -1
        else: # is_correct
            if current_correct_streak == 0:
                correct_streak_start = i
            current_correct_streak += 1
            # End error streak if running
            if current_error_streak >= min_streak_len:
                analysis['consecutive_errors_streaks'].append((error_streak_start, current_error_streak))
            current_error_streak = 0
            error_streak_start = -1

    # Check for streaks ending at the last question
    if current_error_streak >= min_streak_len:
        analysis['consecutive_errors_streaks'].append((error_streak_start, current_error_streak))
    if current_correct_streak >= min_streak_len:
        analysis['consecutive_correct_streaks'].append((correct_streak_start, current_correct_streak))

    # 3. Performance in Last Third
    last_third_start_index = total_questions * 2 // 3
    if last_third_start_index < total_questions:
        last_third_df = df_v_sorted.iloc[last_third_start_index:]
        analysis['errors_in_last_third'] = last_third_df['Correct'].eq(False).sum()
        if len(last_third_df) > 0:
            analysis['error_rate_last_third'] = analysis['errors_in_last_third'] / len(last_third_df)

    # 4. Performance under pressure (Simple check)
    if v_time_pressure_status == 'High':
        # Compare last third error rate to overall error rate
        overall_error_rate = df_v_sorted['Correct'].eq(False).sum() / total_questions if total_questions > 0 else 0
        if analysis['error_rate_last_third'] > overall_error_rate * 1.5: # e.g., 50% higher error rate
            analysis['performance_under_pressure_notes'] = "Evidence suggests performance (accuracy) significantly dropped in the later stages, potentially due to time pressure."
        else:
            analysis['performance_under_pressure_notes'] = "Time pressure was high, but no clear drop in accuracy in later stages detected from this simple check."
    elif v_time_pressure_status in ['Moderate', 'Low']:
         analysis['performance_under_pressure_notes'] = "Time pressure was not identified as high. Performance fluctuations likely due to other factors."
    else: # Unknown
         analysis['performance_under_pressure_notes'] = "Time pressure status unknown, cannot assess its impact."

    # 5. Difficulty Collapse (Simple check: error rate in hardest quartile)
    if 'question_difficulty' in df_v_sorted.columns:
        try:
            difficulty_quartiles = pd.qcut(df_v_sorted['question_difficulty'], 4, labels=False, duplicates='drop')
            hardest_quartile_df = df_v_sorted[difficulty_quartiles == 3] # Highest quartile (index 3)
            if not hardest_quartile_df.empty:
                error_rate_hardest = hardest_quartile_df['Correct'].eq(False).sum() / len(hardest_quartile_df)
                overall_error_rate = df_v_sorted['Correct'].eq(False).sum() / total_questions if total_questions > 0 else 0
                # Check if error rate in hardest quartile is disproportionately high
                if error_rate_hardest > 0.75 and error_rate_hardest > overall_error_rate * 2:
                    analysis['difficulty_collapse_notes'] = f"Error rate ({error_rate_hardest:.1%}) in the hardest 25% of questions is significantly high, suggesting a potential collapse when facing difficult V items."
                else:
                     analysis['difficulty_collapse_notes'] = "No clear evidence of disproportionately high error rate specifically on the hardest questions found."
            else:
                analysis['difficulty_collapse_notes'] = "Could not analyze hardest quartile (possibly too few questions or uniform difficulty)."
        except Exception as e:
             print(f"      Warning: Could not calculate difficulty quartiles: {e}")
             analysis['difficulty_collapse_notes'] = "Difficulty collapse analysis failed (error during quartile calculation)."
    else:
        analysis['difficulty_collapse_notes'] = "Difficulty data missing, cannot assess difficulty collapse."

    return analysis

def _analyze_correct_slow(df_correct, question_type):
    """Analyzes correct but slow questions for Chapter 4."""
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

    # Determine time threshold based on question type
    if question_type == 'SC':
        time_threshold = SC_TIME_THRESHOLD_SECONDS
    elif question_type == 'CR':
        time_threshold = CR_TIME_THRESHOLD_SECONDS
    elif question_type == 'RC':
        time_threshold = RC_TIME_THRESHOLD_SECONDS
    else:
        # Use a default or average if type is unknown/overall? Risky.
        time_threshold = (SC_TIME_THRESHOLD_SECONDS + CR_TIME_THRESHOLD_SECONDS + RC_TIME_THRESHOLD_SECONDS) / 3

    # Filter for slow questions
    slow_correct_df = df_correct[df_correct['question_time'] > time_threshold]
    correct_slow_count = len(slow_correct_df)
    analysis['correct_slow_count'] = correct_slow_count

    if total_correct > 0:
        analysis['correct_slow_rate'] = correct_slow_count / total_correct

    if correct_slow_count > 0:
        # Analyze characteristics of slow questions
        if 'question_difficulty' in slow_correct_df.columns:
            analysis['avg_difficulty_slow'] = slow_correct_df['question_difficulty'].mean()
        analysis['avg_time_slow'] = slow_correct_df['question_time'].mean() / 60.0 # seconds to minutes

        if 'question_fundamental_skill' in slow_correct_df.columns:
            # Map skills to categories to find bottleneck type
            slow_correct_df['error_category'] = slow_correct_df['question_fundamental_skill'].map(V_SKILL_TO_ERROR_CATEGORY).fillna('Unknown')
            category_counts_slow = slow_correct_df['error_category'].value_counts()

            reading_slow = category_counts_slow.get('Reading/Understanding', 0)
            logic_grammar_inference_slow = (category_counts_slow.get('Logic/Reasoning', 0) +
                                             category_counts_slow.get('Grammar/Application', 0) +
                                             category_counts_slow.get('Inference/Application', 0))

            # Determine dominant bottleneck
            if reading_slow > logic_grammar_inference_slow and reading_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Reading/Understanding'
            elif logic_grammar_inference_slow > reading_slow and logic_grammar_inference_slow / correct_slow_count > 0.5:
                analysis['dominant_bottleneck_type'] = 'Logic/Grammar/Inference'
            else:
                analysis['dominant_bottleneck_type'] = 'Mixed/Unclear'

            analysis['skill_breakdown_slow'] = slow_correct_df['question_fundamental_skill'].value_counts().to_dict()
        else:
             analysis['dominant_bottleneck_type'] = 'Skill data missing'

    return analysis

def _analyze_error_types(df_errors, question_type):
    """Analyzes error distribution based on fundamental skills for Chapter 3."""
    analysis = {
        'total_errors': 0,
        'reading_understanding_errors': 0,
        'logic_grammar_inference_errors': 0, # Combined category name for brevity
        'sfe_errors': 0,
        'unknown_skill_errors': 0,
        'reading_understanding_rate': 0.0,
        'logic_grammar_inference_rate': 0.0,
        'sfe_rate': 0.0,
        'dominant_error_type': 'N/A',
        'skill_breakdown': {}
    }
    if df_errors.empty or 'question_fundamental_skill' not in df_errors.columns:
        return analysis

    total_errors = len(df_errors)
    analysis['total_errors'] = total_errors

    # Map skills to categories
    df_errors['error_category'] = df_errors['question_fundamental_skill'].map(V_SKILL_TO_ERROR_CATEGORY).fillna('Unknown')

    # Count errors per category
    category_counts = df_errors['error_category'].value_counts()

    analysis['reading_understanding_errors'] = category_counts.get('Reading/Understanding', 0)
    # Combine Logic/Reasoning, Grammar/Application, Inference/Application into one metric
    analysis['logic_grammar_inference_errors'] = (category_counts.get('Logic/Reasoning', 0) +
                                                category_counts.get('Grammar/Application', 0) +
                                                category_counts.get('Inference/Application', 0))
    analysis['sfe_errors'] = category_counts.get('SFE', 0)
    analysis['unknown_skill_errors'] = category_counts.get('Unknown', 0)

    # Calculate rates
    if total_errors > 0:
        analysis['reading_understanding_rate'] = analysis['reading_understanding_errors'] / total_errors
        analysis['logic_grammar_inference_rate'] = analysis['logic_grammar_inference_errors'] / total_errors
        analysis['sfe_rate'] = analysis['sfe_errors'] / total_errors

    # Determine dominant error type (simple version)
    max_errors = 0
    dominant_type = 'N/A'
    if analysis['reading_understanding_errors'] > max_errors:
        max_errors = analysis['reading_understanding_errors']
        dominant_type = 'Reading/Understanding'
    if analysis['logic_grammar_inference_errors'] > max_errors:
        max_errors = analysis['logic_grammar_inference_errors']
        dominant_type = 'Logic/Grammar/Inference'
    if analysis['sfe_errors'] > max_errors:
        #max_errors = analysis['sfe_errors'] # Don't let SFE be dominant on its own usually
        pass # SFE is noted separately

    # Check if dominant type is significant enough (e.g., > 50% or significantly higher than others)
    is_dominant_clear = False
    if total_errors > 0 and max_errors / total_errors > 0.5: # Example threshold
        is_dominant_clear = True

    analysis['dominant_error_type'] = dominant_type if is_dominant_clear else 'Mixed/Unclear'
    if analysis['sfe_rate'] > 0.3: # Highlight if SFE is high
         analysis['dominant_error_type'] += " (High SFE Anteil)"

    # Detailed breakdown by fundamental skill
    analysis['skill_breakdown'] = df_errors['question_fundamental_skill'].value_counts().to_dict()

    return analysis

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
    errors = df_subset['Correct'].eq(False).sum()
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
        correct_subset = df_subset[df_subset['Correct'] == True]
        incorrect_subset = df_subset[df_subset['Correct'] == False]
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

def _diagnose_sc(df_sc):
    """Placeholder diagnosis for Sentence Correction (SC)."""
    print("      Diagnosing SC...")
    return _calculate_diagnostic_metrics(df_sc, "SC")


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

def run_v_diagnosis(df_v, v_time_pressure_status, num_invalid_v_questions):
    """
    Runs the diagnostic analysis specifically for the Verbal section.

    Args:
        df_v (pd.DataFrame): DataFrame containing only Verbal response data,
                             pre-validated and processed by the main diagnosis module.
                             Includes simulated 'question_difficulty'.
        v_time_pressure_status (str): The calculated time pressure status for Verbal ('High', 'Moderate', 'Low', 'Unknown').
        num_invalid_v_questions (int): Number of invalid questions excluded for Verbal.

    Returns:
        dict: A dictionary containing the results of the Verbal diagnosis, structured by chapter.
              Example: {'chapter_1': {...}, 'chapter_2': {...}, ...}
        str: A string containing the summary report for the Verbal section. (To be implemented later)
    """
    print("  Running Verbal Diagnosis...")
    v_diagnosis_results = {}

    # --- Chapter 1: Time Strategy & Validity (Handled by main module, results passed in) ---
    print("    Chapter 1: Time Strategy & Validity (Results from main module)")
    v_diagnosis_results['chapter_1'] = {
        'time_pressure_status': v_time_pressure_status,
        'invalid_questions_excluded': num_invalid_v_questions
    }
    # Potentially add more detailed V-specific time analysis here if needed, beyond the main module's overall check

    # --- Chapter 2: SC/CR/RC Performance Overview ---
    print("    Chapter 2: SC/CR/RC Performance Overview")
    if df_v.empty or 'question_type' not in df_v.columns:
        print("      Skipping Chapter 2 due to missing data or 'question_type' column.")
        v_diagnosis_results['chapter_2'] = {
            'sc_metrics': _calculate_diagnostic_metrics(pd.DataFrame(), "SC"),
            'cr_metrics': _calculate_diagnostic_metrics(pd.DataFrame(), "CR"),
            'rc_metrics': _calculate_diagnostic_metrics(pd.DataFrame(), "RC"),
            'overall_metrics': _calculate_diagnostic_metrics(pd.DataFrame(), "Verbal Overall")
        }
    else:
        df_sc = df_v[df_v['question_type'] == 'SC'].copy()
        df_cr = df_v[df_v['question_type'] == 'CR'].copy()
        df_rc = df_v[df_v['question_type'] == 'RC'].copy()

        sc_metrics = _diagnose_sc(df_sc)
        cr_metrics = _diagnose_cr(df_cr)
        rc_metrics = _diagnose_rc(df_rc) # Simple version for now
        overall_metrics = _diagnose_verbal_overall(df_v) # Overall V metrics

        v_diagnosis_results['chapter_2'] = {
            'sc_metrics': sc_metrics,
            'cr_metrics': cr_metrics,
            'rc_metrics': rc_metrics,
            'overall_metrics': overall_metrics # Adding overall section metrics
        }
        print(f"      SC Metrics: {sc_metrics['total_questions']} Qs, {sc_metrics['error_rate']:.2%} Error")
        print(f"      CR Metrics: {cr_metrics['total_questions']} Qs, {cr_metrics['error_rate']:.2%} Error")
        print(f"      RC Metrics: {rc_metrics['total_questions']} Qs, {rc_metrics['error_rate']:.2%} Error")
        print(f"      Overall V Metrics: {overall_metrics['total_questions']} Qs, {overall_metrics['error_rate']:.2%} Error")


    # --- Chapter 3: Deep Dive into Errors ---
    print("    Chapter 3: Deep Dive into Errors")
    sc_error_analysis = {}
    cr_error_analysis = {}
    rc_error_analysis = {}

    if df_v.empty or 'question_fundamental_skill' not in df_v.columns:
        print("      Skipping Chapter 3 due to missing data or 'question_fundamental_skill' column.")
        sc_error_analysis = _analyze_error_types(pd.DataFrame(), 'SC')
        cr_error_analysis = _analyze_error_types(pd.DataFrame(), 'CR')
        rc_error_analysis = _analyze_error_types(pd.DataFrame(), 'RC')
    else:
        # Ensure dfs are defined even if Chapter 2 was skipped but fundamental skills exist
        if 'df_sc' not in locals(): df_sc = df_v[df_v['question_type'] == 'SC'].copy()
        if 'df_cr' not in locals(): df_cr = df_v[df_v['question_type'] == 'CR'].copy()
        if 'df_rc' not in locals(): df_rc = df_v[df_v['question_type'] == 'RC'].copy()

        # Analyze errors for each type
        sc_errors = df_sc[df_sc['Correct'] == False]
        cr_errors = df_cr[df_cr['Correct'] == False]
        rc_errors = df_rc[df_rc['Correct'] == False]

        print(f"      Analyzing {len(sc_errors)} SC errors...")
        sc_error_analysis = _analyze_error_types(sc_errors, 'SC')
        print(f"      Analyzing {len(cr_errors)} CR errors...")
        cr_error_analysis = _analyze_error_types(cr_errors, 'CR')
        print(f"      Analyzing {len(rc_errors)} RC errors...")
        rc_error_analysis = _analyze_error_types(rc_errors, 'RC')

    v_diagnosis_results['chapter_3'] = {
        'sc_error_analysis': sc_error_analysis,
        'cr_error_analysis': cr_error_analysis,
        'rc_error_analysis': rc_error_analysis
    }
    # Optional: Print summary of dominant error types
    print(f"        SC Dominant Error Type: {sc_error_analysis.get('dominant_error_type', 'N/A')}")
    print(f"        CR Dominant Error Type: {cr_error_analysis.get('dominant_error_type', 'N/A')}")
    print(f"        RC Dominant Error Type: {rc_error_analysis.get('dominant_error_type', 'N/A')}")

    # --- Chapter 4: Correct but Slow Analysis ---
    print("    Chapter 4: Correct but Slow Analysis")
    sc_correct_slow_analysis = {}
    cr_correct_slow_analysis = {}
    rc_correct_slow_analysis = {}

    # Need the original DFs (before filtering for errors)
    if df_v.empty or 'question_time' not in df_v.columns:
         print("      Skipping Chapter 4 due to missing data or 'question_time' column.")
         sc_correct_slow_analysis = _analyze_correct_slow(pd.DataFrame(), 'SC')
         cr_correct_slow_analysis = _analyze_correct_slow(pd.DataFrame(), 'CR')
         rc_correct_slow_analysis = _analyze_correct_slow(pd.DataFrame(), 'RC')
    else:
        # Ensure dfs are defined even if previous chapters were skipped
        if 'df_sc' not in locals(): df_sc = df_v[df_v['question_type'] == 'SC'].copy()
        if 'df_cr' not in locals(): df_cr = df_v[df_v['question_type'] == 'CR'].copy()
        if 'df_rc' not in locals(): df_rc = df_v[df_v['question_type'] == 'RC'].copy()

        sc_correct = df_sc[df_sc['Correct'] == True]
        cr_correct = df_cr[df_cr['Correct'] == True]
        rc_correct = df_rc[df_rc['Correct'] == True]

        print(f"      Analyzing {len(sc_correct)} correct SC questions for slowness...")
        sc_correct_slow_analysis = _analyze_correct_slow(sc_correct, 'SC')
        print(f"      Analyzing {len(cr_correct)} correct CR questions for slowness...")
        cr_correct_slow_analysis = _analyze_correct_slow(cr_correct, 'CR')
        print(f"      Analyzing {len(rc_correct)} correct RC questions for slowness...")
        rc_correct_slow_analysis = _analyze_correct_slow(rc_correct, 'RC')

    v_diagnosis_results['chapter_4'] = {
        'sc_correct_slow': sc_correct_slow_analysis,
        'cr_correct_slow': cr_correct_slow_analysis,
        'rc_correct_slow': rc_correct_slow_analysis
    }
    # Optional: Print summary
    print(f"        SC Correct but Slow Rate: {sc_correct_slow_analysis.get('correct_slow_rate', 0.0):.1%}")
    print(f"        CR Correct but Slow Rate: {cr_correct_slow_analysis.get('correct_slow_rate', 0.0):.1%}")
    print(f"        RC Correct but Slow Rate: {rc_correct_slow_analysis.get('correct_slow_rate', 0.0):.1%}")


    # --- Chapter 5: Pattern Observation ---
    print("    Chapter 5: Pattern Observation")
    pattern_analysis = _observe_patterns(df_v, v_time_pressure_status)
    v_diagnosis_results['chapter_5'] = pattern_analysis
    # Optional: Print summary of key findings
    print(f"        Carelessness Errors: {pattern_analysis.get('carelessness_error_count', 0)}")
    print(f"        Consecutive Error Streaks (>=3): {len(pattern_analysis.get('consecutive_errors_streaks', []))}")
    print(f"        Error Rate Last Third: {pattern_analysis.get('error_rate_last_third', 0.0):.1%}")
    print(f"        Pressure Notes: {pattern_analysis.get('performance_under_pressure_notes', 'N/A')[:50]}...") # Truncate long notes
    print(f"        Difficulty Notes: {pattern_analysis.get('difficulty_collapse_notes', 'N/A')[:50]}...")

    # --- Chapter 6: Skill Coverage & Blind Spots ---
    print("    Chapter 6: Skill Coverage & Blind Spots")
    # Placeholder for exempted skills - this should be calculated in diagnosis_module.py and passed in
    # For now, using an empty set
    placeholder_exempted_v_skills = set()
    skill_analysis = _analyze_skill_coverage(df_v, v_diagnosis_results.get('chapter_2', {}), placeholder_exempted_v_skills)
    v_diagnosis_results['chapter_6'] = skill_analysis
    # Optional: Print summary
    print(f"        Weak Skills (Y): {len(skill_analysis.get('weak_skills_y', []))}")
    print(f"        Insufficient Coverage (Z): {len(skill_analysis.get('insufficient_coverage_z', []))}")
    print(f"        Exempted Skills (X): {len(skill_analysis.get('exempted_skills_x', []))}")
    print(f"        Macro Reading Override Triggered: {skill_analysis.get('macro_override_reading', {}).get('triggered')}")
    print(f"        Macro Logic/Etc Override Triggered: {skill_analysis.get('macro_override_logic_grammar_inference', {}).get('triggered')}")


    # --- Chapter 7: Recommendations ---
    print("    Chapter 7: Recommendations")
    recommendations = _generate_v_recommendations(v_diagnosis_results)
    v_diagnosis_results['chapter_7'] = recommendations
    # Optional: Print summary of recommendations generated
    print(f"        Generated {len(recommendations)} recommendation items.")

    # --- Chapter 8: Summary Report Generation ---
    print("    Chapter 8: Summary Report Generation")
    v_report_summary = _generate_v_summary_report(v_diagnosis_results)
    # Optional: Print first few lines of the report
    print(f"        Generated Report (first 100 chars): {v_report_summary[:100]}...")

    print("  Verbal Diagnosis Complete.")
    # Return the results dict and the generated report string.
    return v_diagnosis_results, v_report_summary


# --- V Appendix A Translation ---
# Maps internal skill/param names to user-friendly Chinese descriptions
APPENDIX_A_TRANSLATION_V = {
    # SC Skills
    'V_SC_Meaning_Clarity': "SC 語義清晰度",
    'V_SC_Sentence_Structure': "SC 句子結構",
    'V_SC_Verb_Form_Tense': "SC 動詞形式/時態",
    'V_SC_Pronoun_Reference_Agreement': "SC 代詞指代/一致",
    'V_SC_Subject_Verb_Agreement': "SC 主謂一致",
    'V_SC_Modification_Placement': "SC 修飾語放置",
    'V_SC_Parallelism_Structure': "SC 平行結構",
    'V_SC_Comparison_Structure': "SC 比較結構",
    'V_SC_Idiom_Usage_Diction': "SC 慣用法/措辭",
    # CR Skills
    'V_CR_Argument_Deconstruction': "CR 論證解構",
    'V_CR_Option_Interpretation': "CR 選項解讀",
    'V_CR_Assumption_Identification': "CR 假設識別",
    'V_CR_Strengthen_Weaken_Argument': "CR 加強/削弱論證",
    'V_CR_Inference_Conclusion_Drawing': "CR 推理/結論",
    'V_CR_Evaluate_Argument_Method': "CR 評估論證/方法",
    'V_CR_Flaw_Identification': "CR 缺陷識別",
    'V_CR_Explain_Resolve_Paradox': "CR 解釋/解決矛盾",
    'V_CR_Boldface_Reasoning': "CR 黑臉題推理",
    # RC Skills
    'V_RC_Passage_Comprehension': "RC 文章理解",
    'V_RC_Question_Stem_Analysis': "RC 問題分析",
    'V_RC_Option_Analysis': "RC 選項分析",
    'V_RC_Main_Idea_Primary_Purpose': "RC 主旨/目的",
    'V_RC_Specific_Detail_Retrieval': "RC 細節定位",
    'V_RC_Inference_Implication': "RC 推理/暗示",
    'V_RC_Logical_Structure_Organization': "RC 邏輯結構/組織",
    'V_RC_Application_Extrapolation': "RC 應用/外推",
    'V_RC_Author_Tone_Attitude': "RC 作者語氣/態度",
    # Common/Behavioral
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "基礎掌握不穩定 (SFE)",
    'V_CARELESSNESS_DETAIL_OMISSION': "粗心：忽略細節",
    'V_CARELESSNESS_OPTION_MISREAD': "粗心：選項看錯",
    'Unknown Skill': "未知技能",
    # Error Categories (used in report)
    'Reading/Understanding': "閱讀理解",
    'Logic/Reasoning': "邏輯推理",
    'Grammar/Application': "語法應用",
    'Inference/Application': "推理應用",
    'Logic/Grammar/Inference': "邏輯/語法/應用",
    # Statuses
    'Y': "薄弱技能",
    'Y-SFE': "薄弱技能 (高 SFE)",
    'Z': "考察不足",
    'X': "基本掌握 (豁免)",
    'OK': "表現正常",
    # Time Pressure
    'High': "高",
    'Moderate': "中等",
    'Low': "低",
    'Unknown': "未知",
}

def _translate_v(param):
    """Translates an internal V param/skill name using APPENDIX_A_TRANSLATION_V."""
    return APPENDIX_A_TRANSLATION_V.get(param, param)

# --- V Summary Report Generation Helper ---

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
    report_lines.append("**1. 時間策略與有效性 (摘要)**")
    tp_status = _translate_v(ch1.get('time_pressure_status', 'Unknown'))
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體時間壓力感知: {tp_status}")
    if invalid_count > 0:
        report_lines.append(f"- 因時間過短/過長被排除的無效題目數: {invalid_count}")
    report_lines.append("")

    # --- Section 2: SC/CR/RC 表現概覽 ---
    report_lines.append("**2. SC/CR/RC 表現概覽**")
    for q_type in ['SC', 'CR', 'RC']:
        metrics = ch2.get(f'{q_type.lower()}_metrics', {})
        if metrics.get('total_questions', 0) > 0:
            report_lines.append(f"- **{q_type}:**")
            report_lines.append(f"  - 總題數: {metrics.get('total_questions')}")
            report_lines.append(f"  - 錯誤率: {metrics.get('error_rate', 0.0):.1%}")
            report_lines.append(f"  - 平均耗時: {metrics.get('avg_time_spent', 0.0):.2f} 分鐘/題")
            avg_diff_correct = metrics.get('avg_difficulty_correct')
            avg_diff_incorrect = metrics.get('avg_difficulty_incorrect')
            if avg_diff_correct is not None and avg_diff_incorrect is not None:
                diff_comparison = "相當" if abs(avg_diff_correct - avg_diff_incorrect) < 0.2 else ("更低" if avg_diff_incorrect < avg_diff_correct else "更高")
                report_lines.append(f"  - 錯誤題目平均難度 ({avg_diff_incorrect:.2f}) 相較於正確題目 ({avg_diff_correct:.2f}) **{diff_comparison}**")
            else:
                 report_lines.append(f"  - 難度分析: (數據不足)")
            report_lines.append(f"  - 初步診斷: {metrics.get('initial_diagnosis', 'N/A')}")
        else:
            report_lines.append(f"- **{q_type}:** 無數據")
    report_lines.append("")

    # --- Section 3: 錯誤深入分析 ---
    report_lines.append("**3. 錯誤深入分析 (基於 Fundamental Skill)**")
    has_ch3_data = False
    for q_type in ['SC', 'CR', 'RC']:
        analysis = ch3.get(f'{q_type.lower()}_error_analysis', {})
        if analysis.get('total_errors', 0) > 0:
            has_ch3_data = True
            report_lines.append(f"- **{q_type} ({analysis.get('total_errors')} 處錯誤):**")
            dom_error = _translate_v(analysis.get('dominant_error_type', 'N/A'))
            read_rate = analysis.get('reading_understanding_rate', 0.0)
            logic_rate = analysis.get('logic_grammar_inference_rate', 0.0)
            sfe_rate = analysis.get('sfe_rate', 0.0)
            report_lines.append(f"  - 主要錯誤類型歸因: **{dom_error}**")
            report_lines.append(f"    - {_translate_v('Reading/Understanding')} 佔比: {read_rate:.1%}")
            report_lines.append(f"    - {_translate_v('Logic/Grammar/Inference')} 佔比: {logic_rate:.1%}")
            if sfe_rate > 0:
                 report_lines.append(f"    - {_translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')} 佔比: {sfe_rate:.1%}")
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
    for q_type in ['SC', 'CR', 'RC']:
        analysis = ch4.get(f'{q_type.lower()}_correct_slow', {})
        if analysis.get('total_correct', 0) > 0:
            has_ch4_data = True
            slow_rate = analysis.get('correct_slow_rate', 0.0)
            if slow_rate > 0.1: # Only report if significant
                report_lines.append(f"- **{q_type}:**")
                report_lines.append(f"  - 正確題目中耗時過長比例: {slow_rate:.1%}")
                bottleneck = _translate_v(analysis.get('dominant_bottleneck_type', 'N/A'))
                report_lines.append(f"  - 主要效率瓶頸歸因: **{bottleneck}**")
                avg_time = analysis.get('avg_time_slow', 0.0)
                report_lines.append(f"  - 慢題平均耗時: {avg_time:.2f} 分鐘")
    if not has_ch4_data:
         report_lines.append("- 無法進行低效分析 (可能缺少時間數據或無正確題目)。")
    elif not any(ch4.get(f'{qt.lower()}_correct_slow', {}).get('correct_slow_rate', 0.0) > 0.1 for qt in ['SC', 'CR', 'RC']):
         report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 模式觀察與行為分析 ---
    report_lines.append("**5. 模式觀察與行為分析**")
    careless_count = ch5.get('carelessness_error_count', 0)
    consecutive_errors_count = len(ch5.get('consecutive_errors_streaks', []))
    error_rate_last_third = ch5.get('error_rate_last_third', 0.0)
    pressure_notes = ch5.get('performance_under_pressure_notes', '')
    difficulty_notes = ch5.get('difficulty_collapse_notes', '')
    report_lines.append(f"- 歸因於粗心的錯誤數量: {careless_count}")
    report_lines.append(f"- 出現連錯 (>=3題) 的次數: {consecutive_errors_count}")
    report_lines.append(f"- 考試後段 (後1/3) 錯誤率: {error_rate_last_third:.1%}")
    if "significantly dropped" in pressure_notes:
        report_lines.append(f"- 時間壓力影響: {pressure_notes}")
    if "significantly high" in difficulty_notes:
         report_lines.append(f"- 高難度題目反應: {difficulty_notes}")
    if careless_count == 0 and consecutive_errors_count == 0 and "significantly" not in pressure_notes and "significantly" not in difficulty_notes:
        report_lines.append("- 未發現明顯的負面行為模式。")
    report_lines.append("")

    # --- Section 6: 技能覆蓋與知識盲區 ---
    report_lines.append("**6. 技能覆蓋與知識盲區 (基於 Fundamental Skill)**")
    weak_skills = ch6.get('weak_skills_y', [])
    insufficient_coverage = ch6.get('insufficient_coverage_z', [])
    exempted = ch6.get('exempted_skills_x', [])
    skill_details_dict = ch6.get('skill_details', {})

    if not skill_details_dict:
         report_lines.append("- 無法進行技能覆蓋分析 (可能缺少 Fundamental Skill 數據)。")
    else:
        if weak_skills:
             report_lines.append(f"- **主要薄弱技能 (Y/Y-SFE):**")
             for skill in weak_skills:
                 details = skill_details_dict.get(skill, {})
                 status = _translate_v(details.get('status', 'Y'))
                 q_type = details.get('question_type', '?')
                 rate = details.get('error_rate', 0)
                 report_lines.append(f"  - {_translate_v(skill)} ({q_type}) - {status} (錯誤率: {rate:.1%})")
        else:
            report_lines.append("- 未發現明顯的薄弱技能 (Y 規則未觸發)。")

        if insufficient_coverage:
             report_lines.append(f"- **考察不足的技能 (Z):**")
             for skill in insufficient_coverage:
                 details = skill_details_dict.get(skill, {})
                 q_type = details.get('question_type', '?')
                 total = details.get('total', 0)
                 report_lines.append(f"  - {_translate_v(skill)} ({q_type}) - {status} (僅考察 {total} 次)")
        else:
             report_lines.append("- 未發現考察嚴重不足的技能 (Z 規則未觸發)。")

        if exempted:
            report_lines.append(f"- **基本掌握的技能 (X - 豁免):**")
            report_lines.append(f"  - {', '.join([_translate_v(s) for s in exempted])}")

        # Macro Overrides
        if ch6.get('macro_override_reading', {}).get('triggered'):
            report_lines.append(f"- **宏觀提示:** {ch6['macro_override_reading'].get('reason')}")
        if ch6.get('macro_override_logic_grammar_inference', {}).get('triggered'):
             report_lines.append(f"- **宏觀提示:** {ch6['macro_override_logic_grammar_inference'].get('reason')}")
    report_lines.append("")

    # --- Section 7: 練習建議 ---
    report_lines.append("**7. 練習建議**")
    if not ch7:
        report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        for i, rec in enumerate(ch7):
            report_lines.append(f"{i+1}. {rec.get('text', '無建議內容')}") # Assuming rec['text'] contains formatted recommendation
            report_lines.append("") # Add space between recommendations

    return "\n".join(report_lines)

# --- V Recommendation Generation Helper ---

def _generate_v_recommendations(v_diagnosis_results):
    """Generates practice recommendations based on V diagnosis results."""
    recommendations = []
    processed_macro_skills = set() # Keep track of skills covered by macro recs

    # Extract relevant results safely
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})

    skill_details = ch6.get('skill_details', {})
    macro_reading = ch6.get('macro_override_reading', {})
    macro_logic_etc = ch6.get('macro_override_logic_grammar_inference', {})

    # 1. Macro Recommendations (Highest Priority)
    if macro_reading.get('triggered'):
        rec_text = f"**宏觀問題：整體閱讀理解能力需加強 (涉及技能: {', '.join(macro_reading.get('skills_involved', []))})**\n"
        rec_text += "- 原因：多個與閱讀理解相關的技能表現出弱點(Y)或考察不足(Z)。\n"
        rec_text += "- 建議：系統性提升 Verbal 文本的閱讀速度和理解深度，特別是長難句分析、段落結構把握、選項細微差別辨析能力。專項練習 SC 句子結構、CR 論證結構、RC 篇章結構。"
        recommendations.append({'type': 'macro_reading', 'text': rec_text})
        processed_macro_skills.update(macro_reading.get('skills_involved', []))

    if macro_logic_etc.get('triggered'):
        rec_text = f"**宏觀問題：整體邏輯推理/語法/應用能力需加強 (涉及技能: {', '.join(macro_logic_etc.get('skills_involved', []))})**\n"
        rec_text += "- 原因：多個與邏輯、語法或應用相關的技能表現出弱點(Y)或考察不足(Z)。\n"
        rec_text += "- 建議：系統性複習和鞏固相關 GMAT 語法規則、CR 邏輯鏈分析方法、RC 題型解題策略。針對性地練習涉及的具體技能點，提高應用準確性和速度。"
        recommendations.append({'type': 'macro_logic_etc', 'text': rec_text})
        processed_macro_skills.update(macro_logic_etc.get('skills_involved', []))

    # 2. Specific Skill Recommendations (Y, Y-SFE, Z) - Skip if covered by macro
    for skill, details in skill_details.items():
        if skill in processed_macro_skills: continue # Skip skills already covered

        status = details.get('status')
        q_type = details.get('question_type', 'Unknown Type')
        error_rate = details.get('error_rate', 0)

        rec_text = ""
        rec_type = 'skill'

        if status in ['Y', 'Y-SFE']:
            rec_type = 'weak_skill'
            rec_text = f"""**薄弱技能 ({status}): {skill} ({q_type})**
- 表現：錯誤率 ({error_rate:.1%}) 顯著偏高。{' (高 SFE 比例，基礎不穩固)' if status == 'Y-SFE' else ''}
"""
            # Add insights from Ch3 (Error type) and Ch4 (Slowdown)
            error_analysis = ch3.get(f"{q_type.lower()}_error_analysis", {})
            slow_analysis = ch4.get(f"{q_type.lower()}_correct_slow", {})
            dominant_error = error_analysis.get('dominant_error_type', 'N/A')
            is_slow = slow_analysis.get('correct_slow_rate', 0) > 0.2 # Example threshold for slow

            if "Reading/Understanding" in dominant_error:
                rec_text += "- 主要瓶頸：可能在於對此類問題的文本**閱讀理解**。\n"
            elif "Logic/Grammar/Inference" in dominant_error or "Grammar/Application" in dominant_error:
                rec_text += "- 主要瓶頸：可能在於相關**邏輯/語法/應用**規則的掌握或應用。\n"
            if is_slow:
                 rec_text += "- 同時注意：即使做對，此技能相關題目也存在**耗時過長**的情況。\n"

            rec_text += f"- 建議：針對 '{skill}' 進行專項練習，重點{'鞏固基礎並減少 SFE 錯誤' if status == 'Y-SFE' else '提升理解或應用準確性'}。{'同時注意提升解題速度。' if is_slow else ''}"

        elif status == 'Z':
            rec_type = 'insufficient_coverage'
            rec_text = f"""**考察不足 (Z): {skill} ({q_type})**
- 表現：練習數據中此技能考察次數過少 (僅 {details.get('total', 0)} 次)，無法準確評估掌握程度，存在潛在風險。
- 建議：補充 '{skill}' 相關知識點的學習和練習，確保全面覆蓋。"""

        elif status == 'X':
            rec_type = 'exempted'
            rec_text = f"""**基本掌握 (X - 豁免): {skill} ({q_type})**
- 表現：雖然可能存在少量錯誤，但整體正確率和效率達到標準，判斷為基本掌握。
- 建議：保持練習，注意維持穩定性，偶爾複習即可。"""

        if rec_text:
            recommendations.append({'type': rec_type, 'skill': skill, 'text': rec_text})

    # 3. Pattern/Behavioral Recommendations (from Ch5)
    carelessness_rate = ch5.get('carelessness_error_rate_overall', 0.0)
    consecutive_errors = ch5.get('consecutive_errors_streaks', [])
    pressure_notes = ch5.get('performance_under_pressure_notes', '')
    difficulty_notes = ch5.get('difficulty_collapse_notes', '')

    if carelessness_rate > 0.1: # Example threshold
        rec_text = f"""**行為建議：注意粗心錯誤**
- 表現：數據顯示存在一定比例 ({carelessness_rate:.1%}) 的錯誤歸因於細節忽略或選項看錯。
- 建議：放慢審題速度，仔細閱讀題目和選項的每一個詞，特別注意否定詞、限定詞、絕對詞。標記關鍵信息，核對筆記，做完題後快速檢查。"""
        recommendations.append({'type': 'behavior_carelessness', 'text': rec_text})

    if len(consecutive_errors) > 0:
        rec_text = f"""**行為建議：打斷連錯趨勢**
- 表現：測試中出現了 {len(consecutive_errors)} 次連續答錯 3 題或以上的情況。
- 建議：感知到連續遇到困難或連續不確定時，嘗試深呼吸、短暫休息（幾秒鐘），或者跳過當前難題（如果策略允許），調整心態後再繼續，避免負面情緒累積影響後續發揮。"""
        recommendations.append({'type': 'behavior_streaks', 'text': rec_text})

    if "significantly dropped" in pressure_notes:
        rec_text = f"""**行為建議：提升壓力下的表現穩定性**
- 表現：數據提示在測試後半段或時間壓力下，做題正確率有明顯下降。
- 建議：加強模擬計時訓練，練習在壓力下保持清晰的思路和穩定的做題節奏。學習並應用時間管理策略，例如為不同題型設定目標時間，遇到難題及時判斷是否暫時跳過。"""
        recommendations.append({'type': 'behavior_pressure', 'text': rec_text})

    if "significantly high" in difficulty_notes:
        rec_text = f"""**行為建議：應對高難度題目策略**
- 表現：數據提示在面對難度較高的 Verbal 題目時，錯誤率急劇上升。
- 建議：提升在高難度題目上的攻堅能力，但同時也要學會判斷和取捨。對於明顯超出能力範圍或預計耗時過長的難題，考慮戰略性放棄，確保在中低難度題目上的得分率。"""
        recommendations.append({'type': 'behavior_difficulty', 'text': rec_text})

    return recommendations 