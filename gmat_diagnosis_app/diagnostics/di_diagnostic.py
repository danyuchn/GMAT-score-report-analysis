import pandas as pd
import numpy as np
import math # For floor function

# --- DI-Specific Constants (from Markdown Chapter 0 & 1) ---
MAX_ALLOWED_TIME_DI = 45.0
TOTAL_QUESTIONS_DI = 20
TIME_PRESSURE_THRESHOLD_DI = 3.0 # minutes difference
INVALID_TIME_THRESHOLD_SECONDS = 60.0 # 1.0 minute
LAST_THIRD_FRACTION = 2/3

# Overtime thresholds (seconds) based on time pressure
OVERTIME_THRESHOLDS_SECONDS = {
    True: { # High Pressure
        'TPA': 3.0 * 60,
        'GT': 3.0 * 60,
        'DS': 2.0 * 60,
        'MSR_GROUP': 6.0 * 60,
        'MSR_READING': 1.5 * 60,
        'MSR_SINGLE_Q': 1.5 * 60
    },
    False: { # Low Pressure
        'TPA': 3.5 * 60,
        'GT': 3.5 * 60,
        'DS': 2.5 * 60,
        'MSR_GROUP': 7.0 * 60,
        'MSR_READING': 1.5 * 60, # Reading threshold often kept constant
        'MSR_SINGLE_Q': 1.5 * 60 # Single question threshold often kept constant
    }
}

# --- DI-Specific Helper Functions ---

def _grade_difficulty_di(difficulty):
    """Maps DI difficulty score to a 6-level grade string."""
    if pd.isna(difficulty):
        return "Unknown Difficulty"
    if difficulty <= -1:
        return "Low / 505+"
    elif difficulty <= 0:
        return "Mid / 555+"
    elif difficulty <= 1:
        return "Mid / 605+"
    elif difficulty <= 1.5:
        return "Mid / 655+"
    elif difficulty <= 1.95:
        return "High / 705+"
    else: # difficulty > 1.95
        return "High / 805+"

def _analyze_dimension(df_filtered, dimension_col):
    """Analyzes performance metrics grouped by a specific dimension column."""
    if df_filtered.empty or dimension_col not in df_filtered.columns:
        return {}

    results = {}
    grouped = df_filtered.groupby(dimension_col)

    for name, group in grouped:
        total = len(group)
        errors = group['Correct'].eq(False).sum()
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
       Adds 'msr_group_total_time' and 'msr_reading_time' columns.
    """
    if df.empty or 'msr_group_id' not in df.columns or 'question_time' not in df.columns:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        return df

    df_msr = df[df['question_type'] == 'MSR'].copy()
    if df_msr.empty:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        return df

    # Calculate group total time
    group_times = df_msr.groupby('msr_group_id')['question_time'].sum()
    df_msr['msr_group_total_time'] = df_msr['msr_group_id'].map(group_times)

    # Calculate reading time (first question time - avg time of others in group)
    reading_times = {}
    for group_id, group_df in df_msr.groupby('msr_group_id'):
        group_df_sorted = group_df.sort_values('question_position')
        if len(group_df_sorted) >= 2:
            first_q_time = group_df_sorted['question_time'].iloc[0]
            other_q_times_avg = group_df_sorted['question_time'].iloc[1:].mean()
            reading_time = first_q_time - other_q_times_avg
            # Store reading time associated with the first question's index
            first_q_index = group_df_sorted.index[0]
            reading_times[first_q_index] = reading_time
        elif len(group_df_sorted) == 1:
             # If only one MSR question in group, reading time is effectively its time?
             # Or treat as undefined? Let's mark as NaN for now.
             first_q_index = group_df_sorted.index[0]
             reading_times[first_q_index] = np.nan

    # Apply reading times only to the first question of each group
    df_msr['msr_reading_time'] = df_msr.index.map(reading_times)

    # Merge back into the original dataframe
    df = df.merge(df_msr[['msr_group_total_time', 'msr_reading_time']], left_index=True, right_index=True, how='left')
    return df

# --- DI-Specific Placeholder Diagnosis Functions (will be replaced/used later) ---

def _diagnose_ds(df_ds):
    """Placeholder diagnosis for Data Sufficiency (DS)."""
    # ... (Logic for Ch2 onwards)
    return {}

def _diagnose_tpa(df_tpa):
    """Placeholder diagnosis for Two-Part Analysis (TPA)."""
    # ... (Logic for Ch2 onwards)
    return {}

def _diagnose_msr(df_msr):
    """Placeholder diagnosis for Multi-Source Reasoning (MSR)."""
    # ... (Logic for Ch2 onwards)
    return {}

def _diagnose_gt(df_gt):
    """Placeholder diagnosis for Graph & Table (GT)."""
    # ... (Logic for Ch2 onwards)
    return {}

# --- Main DI Diagnosis Runner ---

def run_di_diagnosis(df_di):
    """
    Runs the diagnostic analysis specifically for the Data Insights section.

    Args:
        df_di (pd.DataFrame): DataFrame containing only DI response data.
                              Needs columns like 'question_time', 'Correct', 'question_type',
                              'question_position', 'msr_group_id' (if MSR exists), etc.
                              'question_difficulty' (simulated) is expected.

    Returns:
        dict: A dictionary containing the results of the DI diagnosis, structured by chapter.
        str: A string containing the summary report for the DI section.
    """
    print("  Running Data Insights Diagnosis...")
    di_diagnosis_results = {}

    if df_di.empty:
        print("    No DI data provided. Skipping DI diagnosis.")
        return {}, "Data Insights (DI) 部分無數據可供診斷。"

    # --- Chapter 0: Derivative Data Calculation ---
    print("    Chapter 0: Calculating Derivative Metrics (MSR Times)...")
    # Ensure 'question_time' is numeric (seconds assumed based on thresholds)
    df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
    df_di = _calculate_msr_metrics(df_di)

    # --- Chapter 1: Time Strategy & Validity ---
    print("    Chapter 1: Time Strategy & Validity Analysis (DI Specific)")
    total_test_time_di = df_di['question_time'].sum() / 60.0 # Convert sum of seconds to minutes
    time_diff = MAX_ALLOWED_TIME_DI - total_test_time_di
    time_pressure = time_diff <= TIME_PRESSURE_THRESHOLD_DI
    print(f"      DI Total Time: {total_test_time_di:.2f} min, Allowed: {MAX_ALLOWED_TIME_DI:.1f} min, Diff: {time_diff:.2f} min, Pressure: {time_pressure}")

    # Set thresholds based on pressure
    thresholds = OVERTIME_THRESHOLDS_SECONDS[time_pressure]

    # Identify invalid questions (only if time_pressure is True)
    df_di['is_invalid'] = False
    num_invalid_questions = 0
    if time_pressure:
        last_third_pos_start = TOTAL_QUESTIONS_DI * LAST_THIRD_FRACTION
        invalid_mask = (
            (df_di['question_position'] > last_third_pos_start) &
            (df_di['question_time'] < INVALID_TIME_THRESHOLD_SECONDS)
        )
        df_di.loc[invalid_mask, 'is_invalid'] = True
        num_invalid_questions = invalid_mask.sum()
        print(f"      Identified {num_invalid_questions} potentially invalid questions due to high pressure & fast time in last third.")

    # Mark Overtime (on non-invalid data)
    df_di['overtime'] = False
    df_di['msr_group_overtime'] = False # Specific flag for MSR group OT

    for index, row in df_di[df_di['is_invalid'] == False].iterrows():
        q_type = row['question_type']
        q_time = row['question_time']

        if q_type == 'TPA' and q_time > thresholds['TPA']:
            df_di.loc[index, 'overtime'] = True
        elif q_type == 'GT' and q_time > thresholds['GT']:
            df_di.loc[index, 'overtime'] = True
        elif q_type == 'DS' and q_time > thresholds['DS']:
            df_di.loc[index, 'overtime'] = True
        elif q_type == 'MSR':
            group_time = row['msr_group_total_time']
            if pd.notna(group_time) and group_time > thresholds['MSR_GROUP']:
                df_di.loc[index, 'overtime'] = True # Mark individual MSR Q as overtime if group is overtime
                df_di.loc[index, 'msr_group_overtime'] = True # Also mark the group flag
            # Independent MSR checks from Ch3 (can be done here or later)
            # Reading time check (on first question of group)
            # if pd.notna(row['msr_reading_time']) and row['msr_reading_time'] > thresholds['MSR_READING']:
            #     # Mark specific reading bottleneck? (Handled in Ch3)
            #     pass
            # Single Q time check (on non-first questions?)
            # Let's keep MSR specific time param generation in Ch3 for clarity

    # Create filtered dataset for subsequent chapters
    df_di_filtered = df_di[df_di['is_invalid'] == False].copy()
    print(f"      Filtered dataset size for Chapters 2-6: {len(df_di_filtered)} questions.")

    di_diagnosis_results['chapter_1'] = {
        'total_test_time_minutes': total_test_time_di,
        'time_difference_minutes': time_diff,
        'time_pressure': time_pressure,
        'invalid_questions_excluded': num_invalid_questions,
        'overtime_thresholds_seconds': thresholds
    }

    # --- Chapter 2: Multidimensional Performance Analysis (Using df_di_filtered) ---
    print("    Chapter 2: Multidimensional Performance Analysis")
    domain_analysis = {}
    type_analysis = {}
    difficulty_analysis = {}
    domain_comparison_tags = {
        'poor_math_related': False, 'slow_math_related': False,
        'poor_non_math_related': False, 'slow_non_math_related': False,
        'significant_diff_error': False, 'significant_diff_overtime': False
    }

    if not df_di_filtered.empty:
        # Analyze by Content Domain
        if 'content_domain' in df_di_filtered.columns:
            domain_analysis = _analyze_dimension(df_di_filtered, 'content_domain')
            print(f"      Domain Analysis: {domain_analysis}")
            # Significant difference check for domain
            math_metrics = domain_analysis.get('Math Related', {})
            non_math_metrics = domain_analysis.get('Non-Math Related', {})
            math_errors = math_metrics.get('errors', 0)
            non_math_errors = non_math_metrics.get('errors', 0)
            math_overtime = math_metrics.get('overtime', 0)
            non_math_overtime = non_math_metrics.get('overtime', 0)

            if abs(math_errors - non_math_errors) >= 2:
                domain_comparison_tags['significant_diff_error'] = True
                if math_errors > non_math_errors:
                    domain_comparison_tags['poor_math_related'] = True
                else:
                    domain_comparison_tags['poor_non_math_related'] = True

            if abs(math_overtime - non_math_overtime) >= 2:
                 domain_comparison_tags['significant_diff_overtime'] = True
                 if math_overtime > non_math_overtime:
                     domain_comparison_tags['slow_math_related'] = True
                 else:
                     domain_comparison_tags['slow_non_math_related'] = True
            print(f"      Domain Comparison Tags: {domain_comparison_tags}")
        else:
            print("      Skipping Domain analysis: 'content_domain' column missing.")

        # Analyze by Question Type
        if 'question_type' in df_di_filtered.columns:
            type_analysis = _analyze_dimension(df_di_filtered, 'question_type')
            print(f"      Type Analysis: {type_analysis}")
        else:
            print("      Skipping Type analysis: 'question_type' column missing.")

        # Analyze by Difficulty Grade
        if 'question_difficulty' in df_di_filtered.columns:
            df_di_filtered['difficulty_grade'] = df_di_filtered['question_difficulty'].apply(_grade_difficulty_di)
            difficulty_analysis = _analyze_dimension(df_di_filtered, 'difficulty_grade')
            print(f"      Difficulty Analysis: {difficulty_analysis}")
        else:
            print("      Skipping Difficulty analysis: 'question_difficulty' column missing.")

    di_diagnosis_results['chapter_2'] = {
        'by_domain': domain_analysis,
        'by_type': type_analysis,
        'by_difficulty': difficulty_analysis,
        'domain_comparison_tags': domain_comparison_tags
    }

    # --- Chapter 3: Root Cause Diagnosis (Using df_di_filtered) ---
    print("    Chapter 3: Root Cause Diagnosis")
    if not df_di_filtered.empty:
        # Calculate prerequisites for Chapter 3
        avg_time_per_type = df_di_filtered.groupby('question_type')['question_time'].mean().to_dict()
        print(f"      Avg Time Per Type (seconds): {avg_time_per_type}")

        max_correct_difficulty_per_combination = df_di_filtered[df_di_filtered['Correct'] == True].groupby(
            ['question_type', 'content_domain']
        )['question_difficulty'].max().unstack(fill_value=-np.inf) # Use -inf for missing combos
        print(f"      Max Correct Difficulty Per Combination:\n{max_correct_difficulty_per_combination}")

        # Apply root cause diagnosis logic row by row
        df_di_filtered = _diagnose_root_causes(df_di_filtered, avg_time_per_type, max_correct_difficulty_per_combination, thresholds)

        # Store the dataframe with added diagnostic info (or just the params)
        # Storing the whole DF might be easier for subsequent chapters
        di_diagnosis_results['chapter_3'] = {
            'diagnosed_dataframe': df_di_filtered, # Contains 'diagnostic_params' and 'is_sfe' columns
            'avg_time_per_type_seconds': avg_time_per_type,
            'max_correct_difficulty': max_correct_difficulty_per_combination.to_dict()
        }
        # Optional: Print summary of triggered params
        all_params = [p for params_list in df_di_filtered['diagnostic_params'] for p in params_list]
        param_counts = pd.Series(all_params).value_counts()
        print(f"      Triggered Diagnostic Parameter Counts:\n{param_counts}")

    else:
        print("      Skipping Chapter 3 due to empty filtered data.")
        di_diagnosis_results['chapter_3'] = {
             'diagnosed_dataframe': pd.DataFrame(),
             'avg_time_per_type_seconds': {},
             'max_correct_difficulty': {}
         }

    # --- Chapter 4: Special Pattern Observation (Using df_di_filtered) ---
    print("    Chapter 4: Special Pattern Observation")
    # Need avg_time_per_type from Chapter 3 results
    avg_times_ch3 = di_diagnosis_results.get('chapter_3', {}).get('avg_time_per_type_seconds', {})
    pattern_analysis = _observe_di_patterns(df_di_filtered, avg_times_ch3)
    di_diagnosis_results['chapter_4'] = pattern_analysis
    # Optional: Print pattern results
    print(f"      Carelessness Issue Triggered: {pattern_analysis.get('carelessness_issue_triggered')}")
    print(f"      Early Rushing Risk Triggered: {pattern_analysis.get('early_rushing_risk_triggered')}")

    # --- Chapter 5: Foundation Ability Override Rule (Using df_di_filtered & Ch2 results) ---
    print("    Chapter 5: Foundation Ability Override Rule")
    type_analysis_ch2 = di_diagnosis_results.get('chapter_2', {}).get('by_type', {})
    override_analysis = _check_foundation_override(df_di_filtered, type_analysis_ch2)
    di_diagnosis_results['chapter_5'] = override_analysis
    # Optional: Print override results
    for q_type, results in override_analysis.items():
        if results.get('override_triggered'):
            print(f"      Override Triggered for {q_type}: Y_agg={results.get('Y_agg')}, Z_agg={results.get('Z_agg')}")

    # --- Chapter 6: Practice Planning & Recommendations (Using Ch3 diagnosed_dataframe, Ch5 override, Ch2 tags) ---
    print("    Chapter 6: Practice Planning & Recommendations")
    # Get the diagnosed dataframe from Chapter 3 results
    diagnosed_df_ch3 = di_diagnosis_results.get('chapter_3', {}).get('diagnosed_dataframe')
    # Get domain comparison tags from Chapter 2 results
    domain_tags_ch2 = di_diagnosis_results.get('chapter_2', {}).get('domain_comparison_tags', {})
    # Get override analysis from Chapter 5 results
    override_analysis_ch5 = di_diagnosis_results.get('chapter_5', {})

    recommendations = [] # Default to empty list
    if diagnosed_df_ch3 is not None and not diagnosed_df_ch3.empty:
        recommendations = _generate_di_recommendations(diagnosed_df_ch3, override_analysis_ch5, domain_tags_ch2)
        print(f"      Generated {len(recommendations)} final recommendation items/groups.")
    else:
        print("      Skipping Chapter 6 recommendation generation due to missing/empty diagnosed data from Ch3.")

    di_diagnosis_results['chapter_6'] = {
         'recommendations_list': recommendations
    }

    # --- Chapter 7: Summary Report Generation ---
    print("    Chapter 7: Summary Report Generation")
    # Need to pass the full results dict to generate the report
    di_report_summary = _generate_di_summary_report(di_diagnosis_results)
    # Optional: Print report summary
    print(f"      Generated DI Report (first 100 chars): {di_report_summary[:100]}...")

    print("  Data Insights Diagnosis Complete.")
    return di_diagnosis_results, di_report_summary

# --- Root Cause Diagnosis Helper (Chapter 3 Logic) ---

def _diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """Applies Chapter 3 root cause diagnosis logic row-by-row.
       Adds 'diagnostic_params' (list) and 'is_sfe' (bool) columns.
    """
    df['diagnostic_params'] = [[] for _ in range(len(df))]
    df['is_sfe'] = False

    for index, row in df.iterrows():
        params = []
        q_type = row['question_type']
        domain = row['content_domain']
        q_time = row['question_time']
        is_correct = row['Correct']
        difficulty = row['question_difficulty']
        is_overtime = row['overtime'] # From Chapter 1

        # Determine Time Performance
        avg_time = avg_times.get(q_type, np.inf) # Default to infinity if type unknown
        is_relatively_fast = q_time < avg_time * 0.75
        is_slow = is_overtime # Slow is defined by the overtime flag from Ch1
        is_normal_time = not is_relatively_fast and not is_slow

        # Determine Special Focus Error (SFE)
        max_correct_diff = max_diffs.get(domain, {}).get(q_type, -np.inf) # Get max correct diff for this combo
        is_sfe = (not is_correct) and (difficulty < max_correct_diff)
        df.loc[index, 'is_sfe'] = is_sfe
        if is_sfe:
            params.append('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # Apply MSR Specific Time Checks (Independent)
        if q_type == 'MSR':
            # Reading time check (only applies to first question, check if reading_time exists and is high)
            msr_reading_time = row.get('msr_reading_time') # Get calculated reading time
            msr_reading_threshold = ch1_thresholds.get('MSR_READING')
            if pd.notna(msr_reading_time) and msr_reading_threshold is not None and msr_reading_time > msr_reading_threshold:
                 params.append('DI_MSR_READING_COMPREHENSION_BARRIER')

            # Single Q time check (if not first question? Doc is a bit vague, let's apply to all MSR for simplicity if time > threshold)
            msr_single_q_threshold = ch1_thresholds.get('MSR_SINGLE_Q')
            if msr_single_q_threshold is not None and q_time > msr_single_q_threshold:
                # Avoid double-counting if group is already overtime? No, doc says independent.
                params.append('DI_MSR_SINGLE_Q_BOTTLENECK')

        # Apply Rules based on Type, Domain, Time, Correctness
        if q_type == 'DS':
            if domain == 'Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_CONCEPT_APPLICATION_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif domain == 'Non-Math Related':
                if is_slow and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct:
                     params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        elif q_type == 'TPA': # Similar logic to DS
             if domain == 'Math Related':
                 if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_CONCEPT_APPLICATION_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif domain == 'Non-Math Related':
                 if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        elif q_type == 'GT':
             if domain == 'Math Related':
                 if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_DATA_EXTRACTION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_DATA_EXTRACTION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif domain == 'Non-Math Related':
                 if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        elif q_type == 'MSR':
            # Note: is_slow here refers to individual question overtime based on group time
            if domain == 'Math Related':
                 if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_CONCEPT_APPLICATION_ERROR']) # Simplified, could be integration/reading too
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif domain == 'Non-Math Related':
                 if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR','DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        # Remove duplicates and store
        unique_params = list(set(params))
        # Ensure SFE is always first if present, for easier identification later
        if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
            unique_params.remove('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            unique_params.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        df.loc[index, 'diagnostic_params'] = unique_params

    return df 

# --- Special Pattern Observation Helper (Chapter 4 Logic) ---

def _observe_di_patterns(df, avg_times):
    """Observes special patterns for Chapter 4: Carelessness and Early Rushing."""
    analysis = {
        'carelessness_issue_triggered': False,
        'fast_wrong_rate': 0.0,
        'early_rushing_risk_triggered': False,
        'early_rushing_questions': [] # List of dicts {id, type, domain, time}
    }
    if df.empty:
        return analysis

    # 1. Carelessness Issue (Fast & Wrong Rate)
    # Re-calculate is_relatively_fast based on avg_times passed in
    df['is_relatively_fast'] = False
    for index, row in df.iterrows():
        q_type = row['question_type']
        q_time = row['question_time']
        avg_time = avg_times.get(q_type, np.inf)
        if q_time < avg_time * 0.75:
            df.loc[index, 'is_relatively_fast'] = True

    fast_mask = df['is_relatively_fast'] == True
    fast_wrong_mask = fast_mask & (df['Correct'] == False)

    num_relatively_fast_total = fast_mask.sum()
    num_relatively_fast_incorrect = fast_wrong_mask.sum()

    if num_relatively_fast_total > 0:
        fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
        analysis['fast_wrong_rate'] = fast_wrong_rate
        # Threshold from markdown example: 0.3
        if fast_wrong_rate > 0.3:
            analysis['carelessness_issue_triggered'] = True

    # 2. Early Rushing Risk
    early_pos_limit = TOTAL_QUESTIONS_DI / 3
    early_rush_mask = (
        (df['question_position'] <= early_pos_limit) &
        (df['question_time'] < INVALID_TIME_THRESHOLD_SECONDS) # Use 1.0 min threshold
    )

    early_rushing_df = df[early_rush_mask]
    if not early_rushing_df.empty:
        analysis['early_rushing_risk_triggered'] = True
        # Store details of rushing questions
        for _, row in early_rushing_df.iterrows():
            analysis['early_rushing_questions'].append({
                'id': row.get('Question ID', 'N/A'), # Assuming column name
                'type': row['question_type'],
                'domain': row['content_domain'],
                'time': row['question_time']
            })

    # Clean up temporary column
    if 'is_relatively_fast' in df.columns:
         df.drop(columns=['is_relatively_fast'], inplace=True)

    return analysis 

# --- Foundation Ability Override Helper (Chapter 5 Logic) ---

def _check_foundation_override(df, type_metrics):
    """Checks for foundation override rule for each question type."""
    override_results = {}
    question_types = ['DS', 'TPA', 'MSR', 'GT'] # All possible DI types

    for q_type in question_types:
        metrics = type_metrics.get(q_type, {})
        error_rate = metrics.get('error_rate', 0.0)
        overtime_rate = metrics.get('overtime_rate', 0.0)

        triggered = False
        y_agg = None
        z_agg = None

        # Check if override is triggered
        if error_rate > 0.5 or overtime_rate > 0.5:
            triggered = True

            # Find relevant questions if triggered
            triggering_mask = (
                (df['question_type'] == q_type) &
                ((df['Correct'] == False) | (df['overtime'] == True))
            )
            triggering_df = df[triggering_mask]

            if not triggering_df.empty:
                # Calculate Y_agg (lowest difficulty grade among triggering questions)
                min_difficulty = triggering_df['question_difficulty'].min()
                y_agg = _grade_difficulty_di(min_difficulty)

                # Calculate Z_agg (max time among triggering questions, floored to 0.5 min)
                max_time_seconds = triggering_df['question_time'].max()
                max_time_minutes = max_time_seconds / 60.0
                # Floor to nearest 0.5 minute: floor(time * 2) / 2
                z_agg = math.floor(max_time_minutes * 2) / 2.0
            else:
                 # Should not happen if error_rate or overtime_rate > 0.5, but handle defensively
                 y_agg = "Unknown Difficulty"
                 z_agg = None # Or a default?

        override_results[q_type] = {
            'override_triggered': triggered,
            'Y_agg': y_agg,
            'Z_agg': z_agg,
            'triggering_error_rate': error_rate, # Store for context
            'triggering_overtime_rate': overtime_rate # Store for context
        }

    return override_results 

# --- Recommendation Generation Helper (Chapter 6 Logic) ---

def _generate_di_recommendations(df_diagnosed, override_results, domain_tags):
    """Generates practice recommendations based on Chapters 3, 5, and 2 results."""
    recommendations_by_type = {q_type: [] for q_type in ['DS', 'TPA', 'MSR', 'GT']}
    processed_override_types = set()
    exempted_combinations = set()

    # 1. Calculate Exempted Combinations
    if not df_diagnosed.empty and 'content_domain' in df_diagnosed.columns and 'question_type' in df_diagnosed.columns:
        correct_not_overtime = df_diagnosed[(df_diagnosed['Correct'] == True) & (df_diagnosed['overtime'] == False)]
        combo_counts = correct_not_overtime.groupby(['question_type', 'content_domain']).size()
        exempted_combos_series = combo_counts[combo_counts > 2]
        exempted_combinations = set(exempted_combos_series.index)
        print(f"        Exempted Combinations (Qt, Dm): {exempted_combinations}")

    # 2. Generate Macro Recommendations (from Chapter 5 override)
    for q_type, override_info in override_results.items():
        if override_info.get('override_triggered'):
            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if z_agg is not None else "未知限時"
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {override_info.get('triggering_error_rate', 0.0):.1%} 或 超時率 {override_info.get('triggering_overtime_rate', 0.0):.1%}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({
                'type': 'macro',
                'text': rec_text
            })
            processed_override_types.add(q_type)

    # 3. Generate Case Recommendations (from Chapter 3 diagnosed data)
    # Define target times (seconds) for Z calculation
    target_times_seconds = {'DS': 2.0*60, 'TPA': 3.0*60, 'GT': 3.0*60, 'MSR': 2.0*60}

    df_trigger = df_diagnosed[((df_diagnosed['Correct'] == False) | (df_diagnosed['overtime'] == True))]

    for index, row in df_trigger.iterrows():
        q_type = row['question_type']
        domain = row['content_domain']
        difficulty_score = row['question_difficulty']
        q_time_seconds = row['question_time']
        is_correct = row['Correct']
        is_overtime = row['overtime']
        is_sfe = row['is_sfe']
        diag_params = row['diagnostic_params'] # List of english params

        # Skip if exempted or covered by macro
        if (q_type, domain) in exempted_combinations or q_type in processed_override_types:
            continue

        # Calculate Y (Difficulty Grade)
        y_grade = _grade_difficulty_di(difficulty_score)

        # Calculate Z (Starting Time Limit in minutes)
        target_time_sec = target_times_seconds.get(q_type, 120) # Default 2 mins
        base_time_sec = q_time_seconds - (0.5 * 60) if is_overtime else q_time_seconds
        z_raw_minutes = math.floor((base_time_sec / 60.0) * 2) / 2.0
        z_minutes = max(z_raw_minutes, target_time_sec / 60.0)
        z_text = f"{z_minutes:.1f} 分鐘"
        target_time_text = f"{target_time_sec / 60.0:.1f} 分鐘"

        # Build recommendation text
        # TODO: Translate diag_params before including?
        problem_desc = "錯誤" if not is_correct else "正確但超時"
        sfe_prefix = "*基礎掌握不穩* " if is_sfe else ""
        param_text = f"(問題點可能涉及: {', '.join(diag_params)})" if diag_params else "(具體問題點需進一步分析)"

        rec_text = f"{sfe_prefix}針對 **{domain}** 領域的 **{q_type}** 題目 ({problem_desc}) {param_text}，"
        rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"

        # Add overtime warning if Z is much higher than target
        if z_minutes - (target_time_sec / 60.0) > 2.0:
            rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

        recommendations_by_type[q_type].append({
            'type': 'case',
            'is_sfe': is_sfe,
            'domain': domain,
            'difficulty_grade': y_grade,
            'time_limit_z': z_minutes,
            'text': rec_text,
            'related_question_index': index # Optional: store index for traceability
        })

    # 4. Final Assembly and Domain Focus Rules
    final_recommendations = []

    # Add exemption notes first if type not overridden
    for qt, dm in exempted_combinations:
        if qt not in processed_override_types:
             final_recommendations.append({
                 'type': 'exemption_note',
                 'question_type': qt,
                 'text': f"**豁免說明 ({qt}):** {dm} 領域的 {qt} 題目表現穩定，可暫緩練習。"
             })

    # Process recommendations by type, applying focus rules
    for q_type, type_recs in recommendations_by_type.items():
        if not type_recs: continue # Skip if no recommendations for this type

        # Sort recommendations: Macro first, then SFE cases, then other cases
        def sort_key(rec):
            if rec['type'] == 'macro': return 0
            if rec.get('is_sfe'): return 1
            return 2
        type_recs.sort(key=sort_key)

        # Apply domain focus rules
        focus_note = ""
        has_math_case = any(r.get('domain') == 'Math Related' for r in type_recs if r['type'] == 'case')
        has_non_math_case = any(r.get('domain') == 'Non-Math Related' for r in type_recs if r['type'] == 'case')

        if domain_tags.get('poor_math_related') or domain_tags.get('slow_math_related'):
            if has_math_case: focus_note += f" **建議增加 {q_type} 題型下 `Math Related` 題目的練習比例。**"
        if domain_tags.get('poor_non_math_related') or domain_tags.get('slow_non_math_related'):
            if has_non_math_case: focus_note += f" **建議增加 {q_type} 題型下 `Non-Math Related` 題目的練習比例。**"

        # Add focus note to the last recommendation text of this type (if any case recs exist)
        if focus_note and any(r['type'] == 'case' for r in type_recs):
            for i in range(len(type_recs) - 1, -1, -1):
                if type_recs[i]['type'] != 'macro': # Add to first non-macro rec from end
                    type_recs[i]['text'] += focus_note
                    break
            else: # If only macro rec exists, append there? Or add as separate item?
                 type_recs[-1]['text'] += focus_note # Append to macro if only macro exists

        # Add the processed recommendations for this type to final list
        final_recommendations.extend(type_recs)

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
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "DI 基礎掌握不穩定 (SFE)",
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
    # Time Pressure
    'High': "高",
    'Moderate': "中等",
    'Low': "低",
    'Unknown': "未知",
}

def _translate_di(param):
    """Translates an internal DI param/skill name using APPENDIX_A_TRANSLATION_DI."""
    # Handle list of params if passed
    if isinstance(param, list):
        return [_translate_di(p) for p in param]
    return APPENDIX_A_TRANSLATION_DI.get(param, param)


# --- DI Summary Report Generation Helper (Chapter 7 Logic) ---

def _generate_di_summary_report(di_results):
    """Generates the summary report string for the Data Insights section."""
    report_lines = []
    report_lines.append("## GMAT 數據洞察 (Data Insights) 診斷報告")
    report_lines.append("--- (基於用戶數據與模擬難度分析) ---")
    report_lines.append("")

    # Extract chapters safely
    ch1 = di_results.get('chapter_1', {})
    ch2 = di_results.get('chapter_2', {})
    ch3 = di_results.get('chapter_3', {})
    ch4 = di_results.get('chapter_4', {})
    ch5 = di_results.get('chapter_5', {})
    ch6 = di_results.get('chapter_6', {})

    # Get diagnosed dataframe and triggered params from Ch3
    diagnosed_df = ch3.get('diagnosed_dataframe')
    all_triggered_params = []
    sfe_triggered = False
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
        all_triggered_params = list(set(p for params_list in diagnosed_df['diagnostic_params'] for p in params_list))
        sfe_triggered = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in all_triggered_params

    # 1. 開篇總結 (基於第一章)
    report_lines.append("**1. 開篇總結 (時間策略與有效性)**")
    tp_status = _translate_di(ch1.get('time_pressure', 'Unknown'))
    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體作答時間: {total_time:.2f} 分鐘 (允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘, 剩餘 {time_diff:.2f} 分鐘)")
    report_lines.append(f"- 時間壓力感知: **{tp_status}**")
    if invalid_count > 0:
        report_lines.append(f"- **警告:** 因時間壓力下末段作答過快，有 {invalid_count} 題被標記為無效數據，未納入後續分析。")
    report_lines.append("")

    # 2. 表現概覽 (基於第二章)
    report_lines.append("**2. 表現概覽 (內容領域對比)**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): report_lines.append("- **數學相關** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('poor_non_math_related'): report_lines.append("- **非數學相關** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('slow_math_related'): report_lines.append("- **數學相關** 領域的 **超時率** 明顯更高。")
        if domain_tags.get('slow_non_math_related'): report_lines.append("- **非數學相關** 領域的 **超時率** 明顯更高。")
    else:
        report_lines.append("- 數學相關與非數學相關領域的表現在錯誤率和超時率上無顯著差異。")
    # Optional: Add brief summary of type/difficulty performance if needed
    report_lines.append("")

    # 3. 核心問題分析 (基於第三章參數)
    report_lines.append("**3. 核心問題分析**")
    core_issues = []
    # Prioritize SFE
    if sfe_triggered:
        core_issues.append(f"**{_translate_di('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')}**: 在一些基礎或已掌握難度範圍內的題目上出現失誤，顯示基礎掌握不夠穩定。")
    # Add top 2-3 other frequent parameters (excluding SFE if already added)
    param_counts_ch3 = pd.Series([p for params_list in diagnosed_df['diagnostic_params'] for p in params_list if p != 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE']).value_counts()
    top_other_params = param_counts_ch3.head(2).index.tolist()
    for param in top_other_params:
        core_issues.append(f"**{_translate_di(param)}**: 這是導致錯誤或低效的另一個主要原因。")

    if not core_issues:
        report_lines.append("- 未識別出特別突出的核心問題參數。")
    else:
        report_lines.extend([f"- {issue}" for issue in core_issues])
    report_lines.append("")

    # 4. 特殊模式觀察 (基於第四章)
    report_lines.append("**4. 特殊模式觀察**")
    careless_triggered = ch4.get('carelessness_issue_triggered')
    rushing_triggered = ch4.get('early_rushing_risk_triggered')
    patterns_found = False
    if careless_triggered:
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_CARELESSNESS_ISSUE')}**: 相對快速作答的題目中，錯誤比例偏高 ({ch4.get('fast_wrong_rate', 0.0):.1%})，提示可能存在粗心問題。")
        patterns_found = True
    if rushing_triggered:
        num_rush = len(ch4.get('early_rushing_questions', []))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')}**: 測驗前期 ({num_rush} 題) 出現作答時間過短 (<1分鐘) 的情況，可能影響準確率。")
        patterns_found = True
    if not patterns_found:
        report_lines.append("- 未發現明顯的粗心或前期過快等負面行為模式。")
    report_lines.append("")

    # 5. 詳細診斷說明 (可選，基於第三章)
    # report_lines.append("**5. 詳細診斷參數列表 (供參考)**")
    # ... (Code to list triggered params per type/domain, using _translate_di)
    # report_lines.append("")

    # 6. 練習建議 (基於第六章)
    report_lines.append("**6. 練習建議**")
    recommendations = ch6.get('recommendations_list', [])
    if not recommendations:
        report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        # Group recommendations by type for better readability?
        current_q_type = None
        for i, rec in enumerate(recommendations):
            rec_text = rec.get('text', '無建議內容')
            q_type = rec.get('question_type') # Get type if available
            if q_type and q_type != current_q_type:
                # report_lines.append(f"\n--- {q_type} 建議 ---") # Optional heading
                current_q_type = q_type
            report_lines.append(f"{i+1}. {rec_text}")
            report_lines.append("") # Add space
    # Ensure final space if recommendations existed
    if recommendations: report_lines.append("")

    # 7. 後續行動指引
    report_lines.append("**7. 後續行動指引**")
    # 7.1 Diagnosis Confirmation
    report_lines.append("  **診斷理解確認:**")
    report_lines.append("  - 請仔細閱讀報告，特別是核心問題分析部分。您是否認同報告指出的主要問題點？這與您考試時的感受是否一致？")
    if sfe_triggered:
        report_lines.append(f"  - 報告顯示您觸發了 '{_translate_di('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')}'。您認為這主要是粗心，還是某些基礎概念確實存在模糊地帶？")
    # Add prompts for other core issues if needed
    # ...

    # 7.2 Qualitative Analysis Suggestion
    # Trigger if uncertain about core issues, esp. Non-Math logic/reading
    qual_needed = any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR'])
    if qual_needed:
        report_lines.append("  **質化分析建議:**")
        report_lines.append("  - 如果您對報告中指出的某些問題（尤其是非數學相關的邏輯或閱讀理解錯誤）仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

    # 7.3 Second Evidence Suggestion
    # Trigger if core issues identified
    if core_issues:
        report_lines.append("  **二級證據參考建議:**")
        report_lines.append("  - 為了更精確地定位您遇到的問題，建議您查看近期的練習記錄，尋找與報告中核心問題參數相關的類似錯誤或超時題目。如果能找到 5-10 題以上，嘗試歸納常見錯誤模式或涉及的具體考點/障礙類型。")

    # 7.4 Tools and Prompts Recommendation
    report_lines.append("  **輔助工具與 AI 提示推薦建議:**")
    tools_prompts_added = False
    # Tool recommendations
    if 'DI_LOGICAL_REASONING_ERROR' in all_triggered_params and diagnosed_df is not None and not diagnosed_df.empty and any(diagnosed_df[(diagnosed_df['diagnostic_params'].apply(lambda x: 'DI_LOGICAL_REASONING_ERROR' in x)) & (diagnosed_df['question_type'] == 'DS') & (diagnosed_df['content_domain'] == 'Non-Math Related')].any()):
        report_lines.append("  - *工具:* 考慮使用 `Dustin_GMAT_DI_Non-math_DS_Simulator` 針對性練習非數學 DS 邏輯。")
        tools_prompts_added = True
    # Add other tool triggers if applicable...

    # Prompt recommendations (simplified logic based on presence of param types)
    prompt_map = {
        'basic': ['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'],
        'efficiency': ['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION', 'DI_EFFICIENCY_BOTTLENECK_LOGIC', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_MSR_READING_COMPREHENSION_BARRIER', 'DI_MSR_SINGLE_Q_BOTTLENECK', 'DI_CALCULATION_ERROR'],
        'deep': ['DI_CONCEPT_APPLICATION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_MULTI_SOURCE_INTEGRATION_ERROR'],
        'behavior': ['DI_BEHAVIOR_CARELESSNESS_ISSUE'],
        'msr_specific': ['DI_QUESTION_TYPE_SPECIFIC_ERROR'],
        'consolidation': ['DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'] # Also for general consolidation
    }
    triggered_prompt_types = set()
    for p_type, params in prompt_map.items():
        if any(tp in all_triggered_params for tp in params):
            triggered_prompt_types.add(p_type)

    if triggered_prompt_types:
        report_lines.append("  - *AI提示 (可根據問題選用):*")
        if 'basic' in triggered_prompt_types: report_lines.append("    - 解釋基礎概念/步驟: `Verbal-related/01...` 或 `Quant-related/01...`")
        if 'efficiency' in triggered_prompt_types: report_lines.append("    - 提升解題效率/技巧: `Verbal-related/02...`, `Verbal-related/03...`, `Quant-related/02...`")
        if 'deep' in triggered_prompt_types: report_lines.append("    - 深化概念理解/模式識別: `Verbal-related/04...`, `Verbal-related/07...`, `Quant-related/03...`, `Quant-related/04...`")
        if 'behavior' in triggered_prompt_types: report_lines.append("    - 評估解題方法/思路: `Verbal-related/05...`")
        if 'consolidation' in triggered_prompt_types: report_lines.append("    - 生成變體題/相似題鞏固: `Quant-related/05...`, `Quant-related/06...`")
        if 'msr_specific' in triggered_prompt_types: report_lines.append("    - MSR 文本簡化/複雜化: `Verbal-related/08...`, `Verbal-related/09...`")
        tools_prompts_added = True

    if not tools_prompts_added:
        report_lines.append("  - 根據當前診斷，暫無特別推薦的輔助工具或 AI 提示。")

    return "\n".join(report_lines) 