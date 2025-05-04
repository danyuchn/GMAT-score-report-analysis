import pandas as pd
import numpy as np
import math # For floor function

# --- DI-Specific Constants (from Markdown Chapter 0 & 1) ---
MAX_ALLOWED_TIME_DI = 45.0  # minutes
TOTAL_QUESTIONS_DI = 20
TIME_PRESSURE_THRESHOLD_DI = 3.0  # minutes difference
INVALID_TIME_THRESHOLD_MINUTES = 1.0  # 1.0 minute
LAST_THIRD_FRACTION = 2/3
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
       Adds 'msr_group_total_time', 'msr_reading_time', and 'is_first_msr_q' columns. # Added is_first_msr_q
    """
    if df.empty or 'msr_group_id' not in df.columns or 'question_time' not in df.columns:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column
        return df

    # Use full type name
    # Corrected type name to match the rest of the file/md if needed, assuming 'Multi-source reasoning' is correct
    df_msr = df[df['question_type'] == 'Multi-source reasoning'].copy()
    if df_msr.empty:
        df['msr_group_total_time'] = np.nan
        df['msr_reading_time'] = np.nan
        df['is_first_msr_q'] = False # Initialize column even if no MSR
        return df

    # Calculate group total time
    group_times = df_msr.groupby('msr_group_id')['question_time'].sum()
    df_msr['msr_group_total_time'] = df_msr['msr_group_id'].map(group_times)

    # Calculate reading time and identify first question
    reading_times = {}
    first_q_indices = set() # Keep track of indices of first questions
    for group_id, group_df in df_msr.groupby('msr_group_id'):
        group_df_sorted = group_df.sort_values('question_position')
        first_q_index = group_df_sorted.index[0]
        first_q_indices.add(first_q_index) # Mark this index as a first question

        if len(group_df_sorted) >= 2:
            first_q_time = group_df_sorted['question_time'].iloc[0]
            # Applying the logic from .py (first q time - avg time of others) which user confirmed
            other_q_times_avg = group_df_sorted['question_time'].iloc[1:].mean()
            reading_time = first_q_time - other_q_times_avg
            reading_times[first_q_index] = reading_time
        elif len(group_df_sorted) == 1:
             reading_times[first_q_index] = np.nan # Keep as NaN for single MSR

    # Apply reading times only to the first question of each group
    df_msr['msr_reading_time'] = df_msr.index.map(reading_times)
    # Create the is_first_msr_q flag
    df_msr['is_first_msr_q'] = df_msr.index.isin(first_q_indices)

    # Merge back into the original dataframe
    # Ensure is_first_msr_q is included in the merge
    df = df.merge(df_msr[['msr_group_total_time', 'msr_reading_time', 'is_first_msr_q']], left_index=True, right_index=True, how='left')
    # Fill NaN for non-MSR questions in the new flag column
    df['is_first_msr_q'].fillna(False, inplace=True)
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

def run_di_diagnosis(df_di_raw):
    """
    Runs the diagnostic analysis specifically for the Data Insights section.
    PRIORITIZES the 'is_manually_invalid' flag.

    Args:
        df_di_raw (pd.DataFrame): DataFrame containing only DI response data.
                              Needs columns like 'question_time', 'is_correct', 'question_type',
                              'question_position' (acts as identifier), 'msr_group_id' (if MSR exists), etc.
                              'question_difficulty' (simulated) is expected.
                              May contain 'is_manually_invalid'.

    Returns:
        dict: A dictionary containing the results of the DI diagnosis, structured by chapter.
        str: A string containing the summary report for the DI section.
        pd.DataFrame: The processed DI DataFrame with added diagnostic columns.
    """
    print("DEBUG: >>>>>> Entering run_di_diagnosis >>>>>>") # DEBUG
    print("  Running Data Insights Diagnosis...")
    di_diagnosis_results = {}

    if df_di_raw.empty:
        print("    No DI data provided. Skipping DI diagnosis.")
        # Return empty df with expected columns for downstream consistency
        empty_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type',
                      'question_fundamental_skill', 'content_domain', 'Subject', 'is_invalid',
                      'overtime', 'suspiciously_fast', 'msr_group_id', 'msr_group_total_time',
                      'msr_reading_time', 'is_first_msr_q', 'is_sfe',
                      'time_performance_category', 'diagnostic_params_list']
        return {}, "Data Insights (DI) 部分無數據可供診斷。", pd.DataFrame(columns=empty_cols)

    df_di = df_di_raw.copy()

    # --- Chapter 0: Derivative Data Calculation & Basic Prep ---
    print("    Chapter 0: Calculating Derivative Metrics & Basic Prep...")
    # Ensure 'question_time' is numeric (minutes)
    df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
    # Ensure other critical columns exist and have basic types
    if 'question_position' not in df_di.columns: df_di['question_position'] = range(len(df_di))
    else: df_di['question_position'] = pd.to_numeric(df_di['question_position'], errors='coerce')
    if 'is_correct' not in df_di.columns: df_di['is_correct'] = True # Default if missing
    else: df_di['is_correct'] = df_di['is_correct'].astype(bool)
    if 'question_type' not in df_di.columns: df_di['question_type'] = 'Unknown Type'
    # Initialize potential MSR group id if missing
    if 'msr_group_id' not in df_di.columns: df_di['msr_group_id'] = np.nan

    df_di = _calculate_msr_metrics(df_di) # Now adds 'is_first_msr_q'

    # --- Chapter 1: Time Strategy & Validity ---
    print("    Chapter 1: Time Strategy & Validity Analysis (DI Specific)")
    total_test_time_di = df_di['question_time'].sum() # Already in minutes
    time_diff = MAX_ALLOWED_TIME_DI - total_test_time_di
    time_pressure = time_diff <= TIME_PRESSURE_THRESHOLD_DI
    print(f"      DI Total Time: {total_test_time_di:.2f} min, Allowed: {MAX_ALLOWED_TIME_DI:.1f} min, Diff: {time_diff:.2f} min, Pressure: {time_pressure}")

    # --- START: Apply Manual Invalid Flag First ---
    if 'is_manually_invalid' in df_di.columns:
        df_di['is_invalid'] = df_di['is_manually_invalid'].fillna(False).astype(bool)
        print(f"      Initialized 'is_invalid' based on manual flags. Count: {df_di['is_invalid'].sum()}")
    else:
        print("      Warning (DI Ch1): 'is_manually_invalid' column not found. Initializing 'is_invalid' to False.")
        df_di['is_invalid'] = False
    # --- END: Apply Manual Invalid Flag First ---

    # --- Apply Automatic Invalid Rules ONLY if time pressure AND not manually invalid ---
    num_auto_invalid = 0
    if time_pressure:
        eligible_for_auto_rules_mask = ~df_di['is_invalid'] # Rows not manually marked invalid
        last_third_pos_start = TOTAL_QUESTIONS_DI * LAST_THIRD_FRACTION
        auto_invalid_mask = (
            eligible_for_auto_rules_mask &
            (df_di['question_position'] > last_third_pos_start) &
            (df_di['question_time'] < INVALID_TIME_THRESHOLD_MINUTES)
        )
        num_auto_invalid = auto_invalid_mask.sum()
        if num_auto_invalid > 0:
            print(f"      Marking {num_auto_invalid} additional DI questions as invalid based on automatic Chapter 1 rules (Pressure & Fast End).")
            df_di.loc[auto_invalid_mask, 'is_invalid'] = True

    num_invalid_questions_total = df_di['is_invalid'].sum()
    di_diagnosis_results['invalid_count'] = num_invalid_questions_total
    print(f"      Finished DI invalid marking. Total invalid count: {num_invalid_questions_total}")

    # --- Initialize diagnostic_params and add tag --- 
    if 'diagnostic_params' not in df_di.columns:
        df_di['diagnostic_params'] = [[] for _ in range(len(df_di))]
    else:
        df_di['diagnostic_params'] = df_di['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, set, tuple)) else [])

    final_invalid_mask_di = df_di['is_invalid']
    if final_invalid_mask_di.any():
        print(f"      Adding/Ensuring '{INVALID_DATA_TAG_DI}' tag for {final_invalid_mask_di.sum()} invalid DI rows.")
        for idx in df_di.index[final_invalid_mask_di]:
            current_list = df_di.loc[idx, 'diagnostic_params']
            if not isinstance(current_list, list): current_list = []
            if INVALID_DATA_TAG_DI not in current_list:
                current_list.append(INVALID_DATA_TAG_DI)
            df_di.loc[idx, 'diagnostic_params'] = current_list
    # --- End Add Tag --- 

    # Mark Overtime (on non-invalid data)
    df_di['overtime'] = False
    thresholds = OVERTIME_THRESHOLDS[time_pressure]

    print("DEBUG (di_diagnostic.py): 開始標記超時 - DI數據包含以下題型:")
    print(df_di['question_type'].value_counts())
    print(f"DEBUG (di_diagnostic.py): 使用閾值: {thresholds}")
    
    overtime_count = 0

    for index, row in df_di[df_di['is_invalid'] == False].iterrows():
        q_type = row['question_type']
        q_time = row['question_time']
        
        # 調試單個行的處理
        if index % 5 == 0:  # 僅打印每5行，避免過多輸出
            print(f"DEBUG (di_diagnostic.py): 檢查行 {index}, 題型='{q_type}', 時間={q_time}")

        # 兼容可能的題型名稱差異
        overtime_threshold = None
        if q_type == 'Two-part analysis' or q_type == 'TPA':
            overtime_threshold = thresholds['TPA']
            if pd.notna(q_time) and q_time > overtime_threshold:
                df_di.loc[index, 'overtime'] = True
                overtime_count += 1
                print(f"DEBUG (di_diagnostic.py): 標記TPA超時 - 位置={row.get('question_position', index)}, 時間={q_time}, 閾值={overtime_threshold}")
                
        elif q_type == 'Graph and Table' or q_type == 'GT':
            overtime_threshold = thresholds['GT']
            if pd.notna(q_time) and q_time > overtime_threshold:
                df_di.loc[index, 'overtime'] = True
                overtime_count += 1
                print(f"DEBUG (di_diagnostic.py): 標記GT超時 - 位置={row.get('question_position', index)}, 時間={q_time}, 閾值={overtime_threshold}")
                
        elif q_type == 'Data Sufficiency' or q_type == 'DS':
            overtime_threshold = thresholds['DS']
            if pd.notna(q_time) and q_time > overtime_threshold:
                df_di.loc[index, 'overtime'] = True
                overtime_count += 1
                print(f"DEBUG (di_diagnostic.py): 標記DS超時 - 位置={row.get('question_position', index)}, 時間={q_time}, 閾值={overtime_threshold}")
                
        elif q_type == 'Multi-source reasoning' or q_type == 'MSR':
            # --- MSR Overtime Logic (Revised according to rules) ---
            group_time = row.get('msr_group_total_time')
            is_first = row.get('is_first_msr_q', False)
            reading_time = row.get('msr_reading_time')
            group_threshold = thresholds.get('MSR_GROUP', 7.0) # Default if not found
            reading_threshold = thresholds.get('MSR_READING', 1.5)
            single_q_threshold = thresholds.get('MSR_SINGLE_Q', 1.5)
            position = row.get('question_position', index) # Use position for logging

            # 1. Check Group Overtime First
            if pd.notna(group_time) and group_time > group_threshold:
                df_di.loc[index, 'overtime'] = True
                overtime_count += 1 # Increment count (Note: this might overcount if multiple rows in the same OT group are processed)
                # We need a way to mark the whole group based on one check, or adjust counting.
                # Current loop structure will mark each row individually if group time exceeds.
                print(f"DEBUG (di_diagnostic.py): 標記MSR超時 (組) - 位置={position}, 組時間={group_time:.2f}, 閾值={group_threshold:.1f}")
            else:
                # 2. If Group NOT Overtime, check Individual/Reading time
                if is_first:
                    # Check Reading Overtime
                    if pd.notna(reading_time) and reading_time > reading_threshold:
                        df_di.loc[index, 'overtime'] = True
                        overtime_count += 1
                        print(f"DEBUG (di_diagnostic.py): 標記MSR超時 (閱讀) - 位置={position}, 閱讀時間={reading_time:.2f}, 閾值={reading_threshold:.1f}")
                    # Check Adjusted Single Question Overtime for First Question
                    elif pd.notna(reading_time) and pd.notna(q_time):
                        adjusted_time = q_time - reading_time
                        if adjusted_time > single_q_threshold:
                             df_di.loc[index, 'overtime'] = True
                             overtime_count += 1
                             print(f"DEBUG (di_diagnostic.py): 標記MSR超時 (首題調整後) - 位置={position}, 調整時間={adjusted_time:.2f}, 閾值={single_q_threshold:.1f}")
                else:
                    # Check Single Question Overtime for Non-First Questions
                    if pd.notna(q_time) and q_time > single_q_threshold:
                        df_di.loc[index, 'overtime'] = True
                        overtime_count += 1
                        print(f"DEBUG (di_diagnostic.py): 標記MSR超時 (非首題單題) - 位置={position}, 時間={q_time:.2f}, 閾值={single_q_threshold:.1f}")
            # --- End MSR Overtime Logic ---
    
    # 總結標記結果 - Recalculate sum after the loop for accuracy
    final_overtime_sum = df_di['overtime'].sum()

    # 總結標記結果
    print(f"DEBUG (di_diagnostic.py): 總共標記了 {overtime_count} 個超時題目 (共 {len(df_di)} 題)")
    print(f"DEBUG (di_diagnostic.py): df_di['overtime'].sum() = {df_di['overtime'].sum()}")
    if overtime_count > 0:
        print("DEBUG (di_diagnostic.py): 超時題目分布:")
        if 'question_type' in df_di.columns and 'overtime' in df_di.columns:
            overtime_by_type = df_di[df_di['overtime'] == True]['question_type'].value_counts()
            print(overtime_by_type)

    # Create filtered dataset for subsequent chapters
    df_di_filtered = df_di[df_di['is_invalid'] == False].copy()
    print(f"      Filtered dataset size for Chapters 2-6: {len(df_di_filtered)} questions.")

    di_diagnosis_results['chapter_1'] = {
        'total_test_time_minutes': total_test_time_di,
        'time_difference_minutes': time_diff,
        'time_pressure': time_pressure,
        'invalid_questions_excluded': num_invalid_questions_total,
        'overtime_thresholds_minutes': thresholds
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
            # Ensure difficulty grade calculation happens before Ch3 uses it if needed
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
    print("    Chapter 3: Root Cause Diagnosis (Applying Detailed Logic)") # Updated print
    if not df_di_filtered.empty and 'question_type' in df_di_filtered.columns: # Added check for question_type
        # Calculate prerequisites for Chapter 3
        avg_time_per_type = df_di_filtered.groupby('question_type')['question_time'].mean().to_dict()
        print(f"      Avg Time Per Type (minutes): {avg_time_per_type}")

        # Use 'is_correct' here
        # Check if 'content_domain' exists before grouping
        if 'content_domain' in df_di_filtered.columns:
             max_correct_difficulty_per_combination = df_di_filtered[df_di_filtered['is_correct'] == True].groupby(
                 ['question_type', 'content_domain']
             )['question_difficulty'].max().unstack(fill_value=-np.inf) # Use -inf for missing combos
             print(f"      Max Correct Difficulty Per Combination:\n{max_correct_difficulty_per_combination}")
        else:
             print("      Skipping Max Correct Difficulty calculation: 'content_domain' missing.")
             max_correct_difficulty_per_combination = pd.DataFrame() # Empty df

        # Apply root cause diagnosis logic row by row (using the new detailed function)
        df_di_filtered = _diagnose_root_causes(df_di_filtered, avg_time_per_type, max_correct_difficulty_per_combination, thresholds)

        # Store the dataframe with added diagnostic info
        di_diagnosis_results['chapter_3'] = {
            'diagnosed_dataframe': df_di_filtered, # Contains 'diagnostic_params' and 'is_sfe' columns
            'avg_time_per_type_minutes': avg_time_per_type,
            'max_correct_difficulty': max_correct_difficulty_per_combination.to_dict() if not max_correct_difficulty_per_combination.empty else {}
        }
        # Optional: Print summary of triggered params from the updated df
        if 'diagnostic_params' in df_di_filtered.columns:
             all_params = [p for params_list in df_di_filtered['diagnostic_params'] if isinstance(params_list, list) for p in params_list]
             param_counts = pd.Series(all_params).value_counts()
             print(f"      Triggered Diagnostic Parameter Counts (New Logic):\n{param_counts}")
        else:
            print("      'diagnostic_params' column missing after detailed diagnosis.")

    else:
        print("      Skipping Chapter 3 due to empty filtered data or missing columns.")
        di_diagnosis_results['chapter_3'] = {
             'diagnosed_dataframe': pd.DataFrame(),
             'avg_time_per_type_minutes': {},
             'max_correct_difficulty': {}
         }

    # --- Chapter 4: Special Pattern Observation (Using df_di_filtered) ---
    print("    Chapter 4: Special Pattern Observation")
    # Need avg_time_per_type from Chapter 3 results
    avg_times_ch3 = di_diagnosis_results.get('chapter_3', {}).get('avg_time_per_type_minutes', {})
    # Pass the dataframe to be potentially modified by _observe_di_patterns
    pattern_analysis_results = _observe_di_patterns(df_di_filtered, avg_times_ch3)
    di_diagnosis_results['chapter_4'] = pattern_analysis_results # Store the dict returned
    # Optional: Print pattern results
    print(f"      Carelessness Issue Triggered: {pattern_analysis_results.get('carelessness_issue_triggered')}")
    print(f"      Early Rushing Risk Triggered: {pattern_analysis_results.get('early_rushing_risk_triggered')}")
    # Note: df_di_filtered might now have 'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK' added to some rows

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
    # Use the potentially modified df_di_filtered from Ch4 as input for Ch6
    diagnosed_df_ch3_ch4 = df_di_filtered # Use df_di_filtered as it contains Ch3+Ch4 results now
    # Get domain comparison tags from Chapter 2 results
    domain_tags_ch2 = di_diagnosis_results.get('chapter_2', {}).get('domain_comparison_tags', {})
    # Get override analysis from Chapter 5 results
    override_analysis_ch5 = di_diagnosis_results.get('chapter_5', {})

    recommendations = [] # Default to empty list
    if not diagnosed_df_ch3_ch4.empty:
        recommendations = _generate_di_recommendations(diagnosed_df_ch3_ch4, override_analysis_ch5, domain_tags_ch2)
        print(f"      Generated {len(recommendations)} final recommendation items/groups.")
    else:
        print("      Skipping Chapter 6 recommendation generation due to empty diagnosed data.")

    di_diagnosis_results['chapter_6'] = {
         'recommendations_list': recommendations
    }

    # --- Chapter 7: Summary Report Generation ---
    print("    Chapter 7: Summary Report Generation")
    # Need to pass the full results dict to generate the report
    # The diagnosed_df inside the dict might be the one before Ch4 modifications,
    # ensure report uses the latest df if necessary (e.g., for listing params)
    # Let's update the df in the results dict before generating the report
    di_diagnosis_results['chapter_3']['diagnosed_dataframe'] = diagnosed_df_ch3_ch4.copy()

    di_report_summary = _generate_di_summary_report(di_diagnosis_results)
    # Optional: Print report summary
    print(f"      Generated DI Report (first 100 chars): {di_report_summary[:100]}...")

    print("  Data Insights Diagnosis Complete.")

    # --- Generate Final Report String ---
    report_str = _generate_di_summary_report(di_diagnosis_results) # Regenerate with updated df if needed

    print("DEBUG: <<<<<< Exiting run_di_diagnosis <<<<<<") # DEBUG

    # --- Get the final dataframe to return (likely from Chapter 3 results, now updated post-Ch4) ---
    df_to_return = diagnosed_df_ch3_ch4.copy() # Use the latest df

    # --- Translate English diagnostic codes to Chinese ---
    if 'diagnostic_params' in df_to_return.columns:
        print("DEBUG (di_diagnostic.py): Translating 'diagnostic_params' to Chinese...")
        # Apply the translation function to each list in the column
        df_to_return['diagnostic_params_list_chinese'] = df_to_return['diagnostic_params'].apply(
            lambda params_list: _translate_di(params_list) if isinstance(params_list, list) else []
        )
    else:
        print("WARNING (di_diagnostic.py): 'diagnostic_params' column not found for translation.")
        # Initialize the chinese list column anyway to avoid errors later
        df_to_return['diagnostic_params_list_chinese'] = [[] for _ in range(len(df_to_return))]

    # --- Drop the original English params column ---
    if 'diagnostic_params' in df_to_return.columns:
        df_to_return.drop(columns=['diagnostic_params'], inplace=True)
        print("DEBUG (di_diagnostic.py): Dropped 'diagnostic_params' column.")

    # --- Rename column for consistency and Return all results ---
    if 'diagnostic_params_list_chinese' in df_to_return.columns:
        df_to_return.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'}, inplace=True)
        print("DEBUG (di_diagnostic.py): Renamed 'diagnostic_params_list_chinese' to 'diagnostic_params_list'")
    else:
        # Initialize the column if it wasn't created and couldn't be renamed from chinese list
        print("DEBUG (di_diagnostic.py): Target list column not found or renamed. Initializing 'diagnostic_params_list'.")
        df_to_return['diagnostic_params_list'] = np.empty((len(df_to_return),0)).tolist()

    # --- DEBUG PRINT ---
    print("DEBUG (di_diagnostic.py): Columns before return:", df_to_return.columns.tolist())
    
    # --- 關鍵檢查: 確認overtime列確實存在 ---
    if 'overtime' not in df_to_return.columns:
        print("錯誤: overtime列在返回前消失!")
        if 'overtime' in df_di.columns:
            print("正在重新添加overtime列...")
            df_to_return['overtime'] = df_di['overtime'].copy()
        else:
            print("df_di也不包含overtime列！")
    else:
        # 檢查overtime內容
        print("overtime列存在，值分布:")
        print(df_to_return['overtime'].value_counts())
    
    # --- 確保 Subject 欄位存在 ---
    if 'Subject' not in df_to_return.columns:
        print("警告: 'Subject' 欄位在 DI 返回前缺失，正在重新添加...")
        df_to_return['Subject'] = 'DI'
    elif df_to_return['Subject'].isnull().any() or (df_to_return['Subject'] != 'DI').any():
         print("警告: 'Subject' 欄位存在但包含空值或錯誤值，正在修正...")
         df_to_return['Subject'] = 'DI' # 強制修正
    
    # 返回原始函數簽名需要的三個值
    return di_diagnosis_results, report_str, df_to_return

# --- Root Cause Diagnosis Helper (Chapter 3 Logic) --- REWRITTEN ---

def _diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """
    Analyzes root causes row-by-row based on Chapter 3 logic from the MD document.
    Adds 'diagnostic_params' and 'is_sfe' columns.
    Relies on 'question_type', 'content_domain', 'question_difficulty', 'question_time',
    'is_correct', 'overtime', 'msr_reading_time', 'is_first_msr_q'.
    """
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        return df

    all_diagnostic_params = []
    all_is_sfe = []
    all_time_performance_categories = []

    # Prepare max_correct_difficulty mapping
    max_diff_dict = {}
    if isinstance(max_diffs, pd.DataFrame):
        for q_type_col in max_diffs.columns: # Iterate through columns (types)
            # Use full type names for matching if needed
            # Map potential abbreviated names from df to full names used in max_diffs if necessary
            # Assuming column names in max_diffs are full names like 'Data Sufficiency'
            q_type = q_type_col
            for domain in max_diffs.index:
                 max_val = max_diffs.loc[domain, q_type]
                 if pd.notna(max_val) and max_val != -np.inf:
                     max_diff_dict[(q_type, domain)] = max_val


    # Get MSR specific thresholds
    msr_reading_threshold = ch1_thresholds.get('MSR_READING', 1.5)
    msr_single_q_threshold = ch1_thresholds.get('MSR_SINGLE_Q', 1.5)

    for index, row in df.iterrows():
        params = []
        sfe_triggered = False

        # Extract data safely
        q_type = row.get('question_type', 'Unknown')
        q_domain = row.get('content_domain', 'Unknown')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime = bool(row.get('overtime', False)) # Individual overtime flag
        msr_reading_time = row.get('msr_reading_time', None)
        is_first_msr_q = bool(row.get('is_first_msr_q', False))

        # Determine Time Performance Flags
        is_relatively_fast = False
        is_slow = is_overtime # Use the row's overtime status (which includes MSR group logic from Ch1)
        is_normal_time = False
        # Need to handle potential KeyError if q_type from data isn't in avg_times dict
        avg_time_for_type = avg_times.get(q_type, np.inf) # Get avg time or infinity

        if pd.notna(q_time) and avg_time_for_type != np.inf: # Check q_time is not NaN
            if q_time < (avg_time_for_type * 0.75):
                is_relatively_fast = True
            if not is_relatively_fast and not is_slow:
                is_normal_time = True
        # If q_time is NaN, flags remain False

        # --- Check SFE ---
        if not is_correct and pd.notna(q_diff): # Check q_diff is not NaN
            # Ensure q_type and q_domain are valid keys for max_diff_dict
            max_correct_diff_key = (q_type, q_domain)
            max_correct_diff = max_diff_dict.get(max_correct_diff_key, -np.inf)
            if q_diff < max_correct_diff:
                sfe_triggered = True
                params.append('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # Determine time performance category
        current_time_performance_category = 'Unknown'
        if is_correct:
            if is_relatively_fast:
                current_time_performance_category = 'Fast & Correct'
            elif is_slow:
                current_time_performance_category = 'Slow & Correct'
            else:
                current_time_performance_category = 'Normal Time & Correct'
        else: # Incorrect
            if is_relatively_fast:
                current_time_performance_category = 'Fast & Wrong'
            elif is_slow:
                current_time_performance_category = 'Slow & Wrong'
            else:
                current_time_performance_category = 'Normal Time & Wrong'

        # --- Detailed Diagnostic Logic based on MD Chapter 3 ---
        # Use full names consistently for comparison if data uses them
        # Example: Assuming data has 'Data Sufficiency', 'Two-part analysis', etc.

        # A. Data Sufficiency
        if q_type == 'Data Sufficiency':
            if q_domain == 'Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        # B. Two-Part Analysis
        elif q_type == 'Two-part analysis':
             if q_domain == 'Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        # C. Graph & Table
        elif q_type == 'Graph and Table':
             if q_domain == 'Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_DATA_EXTRACTION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        # D. Multi-Source Reasoning
        elif q_type == 'Multi-source reasoning':
            # Independent MSR Time Checks (from MD)
            if is_first_msr_q and pd.notna(msr_reading_time) and msr_reading_time > msr_reading_threshold:
                params.append('DI_MSR_READING_COMPREHENSION_BARRIER')
            if not is_first_msr_q and pd.notna(q_time) and q_time > msr_single_q_threshold:
                 params.append('DI_MSR_SINGLE_Q_BOTTLENECK')

            # Logic based on slow/fast/normal and correct/incorrect
            if q_domain == 'Math Related':
                if is_slow and not is_correct:
                    params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                 if is_slow and not is_correct:
                    params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR'])
                 elif is_slow and is_correct:
                    params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')

        # --- Finalize Params for the row ---
        unique_params = sorted(list(set(params)))
        if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
            # Ensure SFE is at the front if present
            unique_params.remove('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            unique_params.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # --- DEBUG: Check calculated params per row ---
        if not unique_params: # Print only if the list is empty
            # Check index existence safely
            row_identifier = f"Index {index}" if df.index.is_unique else f"Row position {df.index.get_loc(index)}"
            print(f"DEBUG (_diagnose_root_causes): {row_identifier} - No diagnostic params triggered. Correct: {is_correct}, TimePerf: {current_time_performance_category}")
        # Print first few non-empty lists (e.g., first 5 based on original index)
        elif index < 5: # Check original index
             print(f"DEBUG (_diagnose_root_causes): Row {index} - Triggered params: {unique_params}")
        # --- END DEBUG ---

        all_diagnostic_params.append(unique_params)
        all_is_sfe.append(sfe_triggered)
        all_time_performance_categories.append(current_time_performance_category)

    # Assign lists back to DataFrame
    if len(all_diagnostic_params) == len(df) and len(all_is_sfe) == len(df):
        df['diagnostic_params'] = all_diagnostic_params
        df['is_sfe'] = all_is_sfe
        df['time_performance_category'] = all_time_performance_categories
    else:
        print(f"Error: Length mismatch during root cause diagnosis (detailed). Skipping assignment.")
        if 'diagnostic_params' not in df.columns:
            df['diagnostic_params'] = [[] for _ in range(len(df))]
        if 'is_sfe' not in df.columns:
            df['is_sfe'] = False
        if 'time_performance_category' not in df.columns:
            df['time_performance_category'] = 'Unknown'

    return df


# --- Special Pattern Observation Helper (Chapter 4 Logic) --- MODIFIED ---

def _observe_di_patterns(df, avg_times):
    """Observes special patterns for Chapter 4: Carelessness and Early Rushing.
       Adds 'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK' to diagnostic_params of relevant rows.
       Returns a dictionary containing carelessness flag/param and early rushing details.
       Modifies the input DataFrame (df) by adding early rushing param to specific rows.
    """
    analysis = {
        'carelessness_issue_triggered': False, # Keep the flag for overall reporting
        'triggered_behavioral_params': [], # Store global behavioral params here
        'fast_wrong_rate': 0.0,
        'early_rushing_risk_triggered': False, # Keep flag for reporting convenience
        'early_rushing_questions': []
    }
    if df.empty:
        return analysis

    # Ensure 'diagnostic_params' column exists and is list type for modification
    if 'diagnostic_params' not in df.columns:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
    else:
        # Ensure existing entries are mutable lists
        df['diagnostic_params'] = df['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else [])


    # 1. Carelessness Issue (Fast & Wrong Rate)
    # Use a temporary column for calculation to avoid permanent modification here
    df['_is_relatively_fast_temp'] = False
    for index, row in df.iterrows():
        q_type = row['question_type']
        q_time = row['question_time']
        avg_time = avg_times.get(q_type, np.inf) # Use passed-in avg_times
        if pd.notna(q_time) and q_time < avg_time * 0.75:
            df.loc[index, '_is_relatively_fast_temp'] = True

    fast_mask = df['_is_relatively_fast_temp'] == True
    fast_wrong_mask = fast_mask & (df['is_correct'] == False)

    num_relatively_fast_total = fast_mask.sum()
    num_relatively_fast_incorrect = fast_wrong_mask.sum()

    if num_relatively_fast_total > 0:
        fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
        analysis['fast_wrong_rate'] = fast_wrong_rate
        if fast_wrong_rate > 0.3:
            analysis['carelessness_issue_triggered'] = True
            # Add the global param to the analysis dict
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_CARELESSNESS_ISSUE')

    # Clean up temporary column
    df.drop(columns=['_is_relatively_fast_temp'], inplace=True)


    # 2. Early Rushing Risk
    early_pos_limit = TOTAL_QUESTIONS_DI / 3
    early_rush_mask = (
        (df['question_position'] <= early_pos_limit) &
        (pd.notna(df['question_time'])) & # Ensure time is not NaN
        (df['question_time'] < INVALID_TIME_THRESHOLD_MINUTES)
    )

    early_rushing_indices = df[early_rush_mask].index.tolist() # Get indices as list

    if early_rushing_indices: # Check if the list is not empty
        analysis['early_rushing_risk_triggered'] = True
        early_rush_param = 'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK'

        # Add the parameter to the specific rows and collect details
        for index in early_rushing_indices:
            # Ensure the diagnostic_params for this row is a list before appending
            current_params = df.loc[index, 'diagnostic_params']
            if not isinstance(current_params, list):
                current_params = [] # Initialize as empty list if not already

            # Append param only if not already present
            if early_rush_param not in current_params:
                 current_params.append(early_rush_param)
                 # Assign the modified list back to the DataFrame
                 df.loc[index, 'diagnostic_params'] = current_params


            # Get row data for reporting details
            row = df.loc[index]
            analysis['early_rushing_questions'].append({
                'id': row.get('Question ID', index), # Use index as fallback ID
                'type': row['question_type'],
                'domain': row.get('content_domain', 'Unknown'), # Handle missing domain
                'time': row['question_time']
            })

    return analysis # Returns dict, but modifies df in place for early rushing params


# --- Foundation Ability Override Helper (Chapter 5 Logic) ---

def _check_foundation_override(df, type_metrics):
    """Checks for foundation override rule for each question type."""
    override_results = {}
    # Use full type names or map if necessary from df['question_type'].unique()
    # Assuming df uses full names that match keys in type_metrics potentially
    question_types_in_data = df['question_type'].unique()


    for q_type in question_types_in_data:
        # Skip if type is unknown or NaN
        if pd.isna(q_type): continue

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
                ((df['is_correct'] == False) | (df['overtime'] == True))
            )
            triggering_df = df[triggering_mask]

            if not triggering_df.empty:
                # Calculate Y_agg (lowest difficulty grade among triggering questions)
                # Ensure 'question_difficulty' exists and has valid values
                if 'question_difficulty' in triggering_df.columns and triggering_df['question_difficulty'].notna().any():
                     min_difficulty = triggering_df['question_difficulty'].min()
                     y_agg = _grade_difficulty_di(min_difficulty)
                else:
                     y_agg = "Unknown Difficulty"


                # Calculate Z_agg (max time among triggering questions, floored to 0.5 min)
                # Ensure 'question_time' exists and has valid values
                if 'question_time' in triggering_df.columns and triggering_df['question_time'].notna().any():
                     max_time_minutes = triggering_df['question_time'].max()
                     # Floor to nearest 0.5 minute: floor(time * 2) / 2
                     z_agg = math.floor(max_time_minutes * 2) / 2.0
                else:
                     z_agg = None # Cannot calculate if time is missing

            else:
                 # Should not happen if error_rate or overtime_rate > 0.5, but handle defensively
                 y_agg = "Unknown Difficulty"
                 z_agg = None

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
    # Ensure 'question_type' exists before proceeding
    if 'question_type' not in df_diagnosed.columns:
         print("Warning: 'question_type' column missing in diagnosed data for recommendations. Skipping.")
         return []

    # Use type names present in the actual data
    question_types_in_data = df_diagnosed['question_type'].unique()
    # Filter out NaN types if any
    question_types_valid = [qt for qt in question_types_in_data if pd.notna(qt)]

    recommendations_by_type = {q_type: [] for q_type in question_types_valid}
    processed_override_types = set()

    # --- ADD Exemption Rule Calculation (Matches MD Ch6) ---
    exempted_types = set()
    if 'is_correct' in df_diagnosed.columns and 'overtime' in df_diagnosed.columns:
        for q_type in question_types_valid:
            type_df = df_diagnosed[df_diagnosed['question_type'] == q_type]
            # Check if NO questions are incorrect OR overtime for this type
            if not type_df.empty and not ((type_df['is_correct'] == False) | (type_df['overtime'] == True)).any():
                exempted_types.add(q_type)
        print(f"      Exempted types (perfect performance): {exempted_types}") # Debug print
    else:
        print("Warning: Cannot calculate exempted types due to missing 'is_correct' or 'overtime' columns.")
    # --- END Exemption Rule Calculation ---


    # 2. Generate Macro Recommendations (from Chapter 5 override)
    for q_type, override_info in override_results.items():
        # Check if this type exists in our current data's recommendations dict
        if q_type in recommendations_by_type and override_info.get('override_triggered'):
            # --- Skip Macro if type is Exempted --- #
            if q_type in exempted_types:
                print(f"Info: Skipping Macro recommendation for {q_type} because it is exempted.")
                continue
            # --- End Skip --- #
            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if pd.notna(z_agg) else "未知限時" # Check for NaN Z_agg
            error_rate_str = _format_rate(override_info.get('triggering_error_rate', 0.0))
            overtime_rate_str = _format_rate(override_info.get('triggering_overtime_rate', 0.0))
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {error_rate_str} 或 超時率 {overtime_rate_str}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({
                'type': 'macro',
                'text': rec_text,
                'question_type': q_type # Add type for potential later use/sorting
            })
            processed_override_types.add(q_type)

    # 3. Generate Case Recommendations (Using AGGREGATED logic)
    target_times_minutes = {
        'Data Sufficiency': 2.0,
        'Two-part analysis': 3.0,
        'Graph and Table': 3.0,
        'Multi-source reasoning': 2.0 # Target time per question for MSR
    }

    required_cols = ['is_correct', 'overtime', 'question_type', 'content_domain',
                     'question_difficulty', 'question_time', 'is_sfe', 'diagnostic_params']
    if not all(col in df_diagnosed.columns for col in required_cols):
        print("Warning: Missing required columns for aggregated recommendation generation. Skipping.")
    else:
        df_trigger = df_diagnosed[((df_diagnosed['is_correct'] == False) | (df_diagnosed['overtime'] == True))]

        if not df_trigger.empty:
            # Use try-except for groupby robustness
            try:
                grouped_triggers = df_trigger.groupby(['question_type', 'content_domain'], observed=False) # Use observed=False if using categorical

                for name, group_df in grouped_triggers:
                    q_type, domain = name
                    if pd.isna(q_type) or pd.isna(domain): continue

                    # Skip if covered by macro override or exemption
                    if q_type in processed_override_types or q_type in exempted_types:
                        continue

                    # --- Aggregate information within the group ---
                    min_difficulty_score = group_df['question_difficulty'].min()
                    y_grade = _grade_difficulty_di(min_difficulty_score)

                    z_minutes_list = []
                    target_time_minutes = target_times_minutes.get(q_type, 2.0)
                    for _, row in group_df.iterrows():
                        q_time_minutes = row['question_time']
                        is_overtime = row['overtime']
                        if pd.notna(q_time_minutes):
                            base_time_minutes = q_time_minutes
                            if is_overtime:
                                base_time_minutes = q_time_minutes - 0.5
                            base_time_minutes = max(0, base_time_minutes)
                            z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                            z = max(z_raw_minutes, target_time_minutes)
                            z_minutes_list.append(z)

                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{target_time_minutes:.1f} 分鐘"

                    group_sfe = group_df['is_sfe'].any()

                    diag_params_codes = set()
                    for params_list in group_df['diagnostic_params']:
                        if isinstance(params_list, list):
                            diag_params_codes.update(params_list)

                    translated_params_list = _translate_di(list(diag_params_codes))
                    param_text = f"(問題點可能涉及: {', '.join(translated_params_list)})" if translated_params_list else "(具體問題點需進一步分析)"

                    problem_desc = "錯誤或超時"
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    translated_domain = _translate_di(domain)

                    rec_text = f"{sfe_prefix}針對 **{translated_domain}** 領域的 **{q_type}** 題目 ({problem_desc}) {param_text}，"
                    rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"

                    if max_z_minutes - target_time_minutes > 2.0:
                        rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    # Add to the dict, key is q_type
                    if q_type in recommendations_by_type:
                         recommendations_by_type[q_type].append({
                             'type': 'case_aggregated',
                             'is_sfe': group_sfe,
                             'domain': domain,
                             'difficulty_grade': y_grade,
                             'time_limit_z': max_z_minutes,
                             'text': rec_text,
                             'question_type': q_type
                         })
                    else:
                         print(f"Warning: q_type '{q_type}' from groupby not in recommendations_by_type keys. Skipping recommendation.")

            except Exception as e:
                print(f"Error during recommendation grouping/aggregation: {e}")
                # Continue without aggregated recommendations if grouping fails

    # 4. Final Assembly and Domain Focus Rules
    final_recommendations = []

    # --- ADD Exemption Note Generation (Matches MD Ch6) ---
    for q_type in sorted(list(exempted_types)): # Sort for consistent order
         # Check if this q_type exists in our valid types
         if q_type in question_types_valid:
              exemption_note_text = f"您在 **{q_type}** 題型上表現穩定，所有題目均在時限內正確完成，無需針對性個案練習。"
              final_recommendations.append({
                  'type': 'exemption_note',
                  'text': exemption_note_text,
                  'question_type': q_type
              })
    # --- END Exemption Note Generation ---

    # Process recommendations by type, applying focus rules
    # Iterate through the original valid types to maintain order if needed
    for q_type in question_types_valid:
        # Skip exempted types here, they are already handled above
        if q_type in exempted_types:
            continue

        type_recs = recommendations_by_type.get(q_type, [])
        if not type_recs: continue

        # Sort recommendations: Macro first, then Aggregated cases
        def sort_key(rec):
            if rec['type'] == 'macro': return 0
            # Aggregated cases sorted (e.g., by SFE status if needed)
            # return 1 if rec.get('is_sfe') else 2 # Example SFE sort
            return 1 # All aggregated cases at same level for now
        type_recs.sort(key=sort_key)

        # Apply domain focus rules
        focus_note = ""
        has_math_case_agg = any(r.get('domain') == 'Math Related' for r in type_recs if r['type'] == 'case_aggregated')
        has_non_math_case_agg = any(r.get('domain') == 'Non-Math Related' for r in type_recs if r['type'] == 'case_aggregated')

        if domain_tags.get('poor_math_related') or domain_tags.get('slow_math_related'):
            if has_math_case_agg: focus_note += f" **建議增加 {q_type} 題型下 `{_translate_di('Math Related')}` 題目的練習比例。**"
        if domain_tags.get('poor_non_math_related') or domain_tags.get('slow_non_math_related'):
            if has_non_math_case_agg: focus_note += f" **建議增加 {q_type} 題型下 `{_translate_di('Non-Math Related')}` 題目的練習比例。**"

        # Add focus note to the last non-macro recommendation
        if focus_note:
            last_agg_rec_index = -1
            for i in range(len(type_recs) - 1, -1, -1):
                if type_recs[i]['type'] == 'case_aggregated':
                    last_agg_rec_index = i
                    break
            if last_agg_rec_index != -1:
                 type_recs[last_agg_rec_index]['text'] += focus_note
            elif type_recs: # Append to macro if only macro exists
                 type_recs[-1]['text'] += focus_note

        # Add the processed recommendations for this non-exempted type
        final_recommendations.extend(type_recs)


    # Final sort of all recommendations? (e.g., by type order) - Already done above implicitly by iterating `question_types_valid`
    # But let's re-sort explicitly including exemption notes
    type_order_final = ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table']
    final_recommendations.sort(key=lambda x: type_order_final.index(x['question_type']) if x.get('question_type') in type_order_final else 99)

    return final_recommendations

# --- DI Appendix A Translation ---
APPENDIX_A_TRANSLATION_DI = {
    # DI - Reading & Understanding
    'DI_READING_COMPREHENSION_ERROR': "DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math)",
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': "DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙",
    # 'DI_DATA_INTERPRETATION_ERROR': "DI 數據解讀: 數據/信息解讀錯誤", # Removed - Placeholder
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
    'DI_MSR_READING_COMPREHENSION_BARRIER': "DI MSR 閱讀障礙: 題組整體閱讀時間過長", # Matched MD
    'DI_MSR_SINGLE_Q_BOTTLENECK': "DI MSR 單題瓶頸: 題組內單題回答時間過長", # Matched MD
    # 'DI_MSR_READING_BOTTLENECK': "..." # Removed - Old py param
    # 'DI_MSR_GROUP_INEFFICIENCY': "..." # Removed - Old py param
    # DI - Question Type Specific
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': "DI 特定題型障礙 (例如 MSR Non-Math 子題型)",
    # DI - Foundational & Efficiency
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "DI 基礎掌握: 應用不穩定 (Special Focus Error)", # Using MD version
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
    'Unknown Domain': "未知領域", # Added for robustness
    # Time Pressure
    'High': "高",
    'Moderate': "中等",
    'Low': "低",
    'Unknown': "未知",
    # Question Types (if needed for translation anywhere)
    'Data Sufficiency': 'Data Sufficiency',
    'Two-part analysis': 'Two-part analysis',
    'Multi-source reasoning': 'Multi-source reasoning',
    'Graph and Table': 'Graph and Table',
    'Unknown Type': '未知類型', # Added for robustness
    # --- Time Performance Categories ---
    'Fast & Wrong': "快錯",
    'Slow & Wrong': "慢錯",
    'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對",
    'Fast & Correct': "快對",
    'Normal Time & Correct': "正常時間 & 對",
    # --- End Time Performance Categories ---
}

# --- DI Tool/Prompt Recommendations Map (Example Structure) ---
# Maps sets of diagnostic parameters to strings containing tool/prompt recommendations
DI_TOOL_RECOMMENDATIONS_MAP = {
    # Example: Non-Math DS Logic Issues
    frozenset(['DI_LOGICAL_REASONING_ERROR']): # Trigger based on parameter only
        "針對非數學 DS 邏輯問題，考慮使用工具 `Dustin_GMAT_DI_Non-math_DS_Simulator`。相關 AI 提示可能包括 `DI-related/ds_logic_patterns.md`。", # Tool and Prompt
    # Example: Calculation Errors or Efficiency Bottleneck
    frozenset(['DI_CALCULATION_ERROR', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION']):
        "計算錯誤或效率低下，可使用 AI 提示 `Quant-related/calculation_shortcuts.md` 或 `Quant-related/error_analysis_calculation.md`。", # Only Prompts
    # Example: Data Interpretation Errors (General - replaced placeholder with reading comp)
    frozenset(['DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR']):
        "數據或文本解讀錯誤，嘗試 AI 提示 `DI-related/interpret_complex_text.md` 或 `DI-related/common_interpretation_pitfalls.md`。", # Only Prompts
    # Example: MSR Integration Issues
    frozenset(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_EFFICIENCY_BOTTLENECK_INTEGRATION']):
        "MSR 信息整合困難或耗時，可考慮使用工具 `Dustin_GMAT_DI_MSR_Integrator`。AI 提示可嘗試 `DI-related/msr_integration_strategy.md`。", # Tool and Prompt
    # Example: Carelessness (using the global param)
    frozenset(['DI_BEHAVIOR_CARELESSNESS_ISSUE']):
        "粗心問題導致失誤，建議使用 AI 提示 `General/attention_to_detail_checklist.md` 或 `General/self_reflection_careless_errors.md`。", # Only Prompts
    # Example: Foundational Mastery (SFE)
    frozenset(['DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE']):
        "基礎掌握不穩定 (SFE)，建議優先使用 AI 提示 `Quant-related/01_basic_explanation.md` 或 `DI-related/basic_concept_review.md` 鞏固基礎。", # Only Prompts
    # Example: MSR Specific Barriers
    frozenset(['DI_MSR_READING_COMPREHENSION_BARRIER', 'DI_MSR_SINGLE_Q_BOTTLENECK']):
        "MSR 閱讀或單題作答耗時過長，可參考 AI 提示 `DI-related/msr_time_management.md` 或 `DI-related/msr_reading_strategy.md`。",
    # Add more mappings as needed based on DI parameters and available tools/prompts
}


# --- Parameter Categories for Report Grouping (DI) --- Updated ---
DI_PARAM_CATEGORY_ORDER = [
    'SFE',
    'Reading/Interpretation',
    'Concept/Application (Math)',
    'Logical Reasoning (Non-Math)',
    'Data Handling', # Includes Calculation, Extraction
    'MSR Specific',
    'Efficiency',
    'Behavioral',
    'Unknown' # Catch-all for unmapped params
]

DI_PARAM_TO_CATEGORY = {
    # SFE
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    # Reading/Interpretation
    'DI_READING_COMPREHENSION_ERROR': 'Reading/Interpretation',
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': 'Reading/Interpretation',
    # Concept/Application (Math)
    'DI_CONCEPT_APPLICATION_ERROR': 'Concept/Application (Math)',
    # Logical Reasoning (Non-Math)
    'DI_LOGICAL_REASONING_ERROR': 'Logical Reasoning (Non-Math)',
    # Data Handling
    'DI_DATA_EXTRACTION_ERROR': 'Data Handling',
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': 'Data Handling',
    'DI_CALCULATION_ERROR': 'Data Handling',
    # MSR Specific
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': 'MSR Specific',
    'DI_MSR_READING_COMPREHENSION_BARRIER': 'MSR Specific',
    'DI_MSR_SINGLE_Q_BOTTLENECK': 'MSR Specific',
    # Question Type Specific
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': 'Unknown',
    # Efficiency
    'DI_EFFICIENCY_BOTTLENECK_READING': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': 'Efficiency',
    # Behavioral
    'DI_CARELESSNESS_DETAIL_OMISSION': 'Behavioral',
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral',
}

def _translate_di(param):
    """Translates an internal DI param/skill name using APPENDIX_A_TRANSLATION_DI."""
    if isinstance(param, list):
        # Filter out None or non-string items before translation
        return [APPENDIX_A_TRANSLATION_DI.get(p, p) for p in param if isinstance(p, str)]
    elif isinstance(param, str):
         return APPENDIX_A_TRANSLATION_DI.get(param, param)
    else:
         return str(param) # Return string representation of other types


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

    # Get diagnosed dataframe and calculate triggered params from it
    diagnosed_df = ch3.get('diagnosed_dataframe') # This should be the latest df passed to Ch7
    all_triggered_params = []
    sfe_triggered = False
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
         # Ensure params are lists before iterating
         param_lists = diagnosed_df['diagnostic_params'][diagnosed_df['diagnostic_params'].apply(isinstance, args=(list,))].tolist()
         all_triggered_params = list(set(p for params_list in param_lists for p in params_list))
         sfe_triggered = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in all_triggered_params
         # Also consider global behavioral params from Ch4 results
         ch4_behavioral_params = ch4.get('triggered_behavioral_params', [])
         all_triggered_params.extend(ch4_behavioral_params)
         all_triggered_params = list(set(all_triggered_params)) # Update unique list


    # 1. 開篇總結 (基於第一章)
    report_lines.append("**1. 開篇總結 (時間策略與有效性)**")
    tp_status_key = ch1.get('time_pressure') # Get boolean or None
    # Translate boolean to High/Low or Unknown
    if tp_status_key is True: tp_status = _translate_di('High')
    elif tp_status_key is False: tp_status = _translate_di('Low')
    else: tp_status = _translate_di('Unknown')

    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體作答時間: {total_time:.2f} 分鐘 (允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘, 剩餘 {time_diff:.2f} 分鐘)")
    report_lines.append(f"- 時間壓力感知: **{tp_status}**") # Use translated status
    if invalid_count > 0:
        report_lines.append(f"- **警告:** 因時間壓力下末段作答過快，有 {invalid_count} 題被標記為無效數據，未納入後續分析。")
    report_lines.append("")

    # 2. 表現概覽 (基於第二章)
    report_lines.append("**2. 表現概覽 (內容領域對比)**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): report_lines.append(f"- **{_translate_di('Math Related')}** 領域的 **錯誤率** 明顯更高。") # Translate domain
        if domain_tags.get('poor_non_math_related'): report_lines.append(f"- **{_translate_di('Non-Math Related')}** 領域的 **錯誤率** 明顯更高。") # Translate domain
        if domain_tags.get('slow_math_related'): report_lines.append(f"- **{_translate_di('Math Related')}** 領域的 **超時率** 明顯更高。") # Translate domain
        if domain_tags.get('slow_non_math_related'): report_lines.append(f"- **{_translate_di('Non-Math Related')}** 領域的 **超時率** 明顯更高。") # Translate domain
    else:
        report_lines.append(f"- {_translate_di('Math Related')}與{_translate_di('Non-Math Related')}領域的表現在錯誤率和超時率上無顯著差異。")
    report_lines.append("")

    # 3. 核心問題分析 (基於第三章參數 + Ch4 global params)
    report_lines.append("**3. 核心問題分析**")
    core_issues = []
    sfe_domains_involved = set()
    sfe_types_involved = set()

    # --- SFE Summary Logic ---
    if sfe_triggered and diagnosed_df is not None and 'is_sfe' in diagnosed_df.columns:
        sfe_rows = diagnosed_df[diagnosed_df['is_sfe'] == True]
        if not sfe_rows.empty:
            # Ensure domain/type columns exist before accessing
            if 'content_domain' in sfe_rows.columns:
                 sfe_domains_involved = set(sfe_rows['content_domain'].dropna())
            if 'question_type' in sfe_rows.columns:
                 sfe_types_involved = set(sfe_rows['question_type'].dropna())

            sfe_label = _translate_di('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            sfe_domains_zh = ", ".join(sorted([_translate_di(d) for d in sfe_domains_involved]))
            # Use translated types if translation map includes them, else use raw names
            sfe_types_zh = ", ".join(sorted([_translate_di(t) for t in sfe_types_involved]))
            sfe_note = f"**尤其需要注意: {sfe_label}**"
            if sfe_domains_involved: sfe_note += f" (涉及領域: {sfe_domains_zh})"
            if sfe_types_involved: sfe_note += f" (涉及題型: {sfe_types_zh})"
            sfe_note += ". (註：SFE 指在已掌握難度範圍內題目失誤)"
            report_lines.append(f"- {sfe_note}")

    # --- Core Issue Summary ---
    # Get counts of all triggered params (including behavioral from Ch4)
    param_counts_all = pd.Series(all_triggered_params).value_counts()

    # Exclude SFE for "other" top params
    top_other_params_codes = param_counts_all[param_counts_all.index != 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'].head(2).index.tolist()

    if top_other_params_codes:
        report_lines.append("- **其他主要問題點:**")
        for param_code in top_other_params_codes:
            report_lines.append(f"  - {_translate_di(param_code)}")
    elif not sfe_triggered:
        report_lines.append("- 未識別出明顯的核心問題模式。")

    # Detailed Diagnostic List removed per user request

    # 4. 特殊模式觀察 (基於第四章結果)
    report_lines.append("**4. 特殊模式觀察**")
    # Use flags from Ch4 results dict
    careless_triggered_ch4 = ch4.get('carelessness_issue_triggered')
    rushing_triggered_ch4 = ch4.get('early_rushing_risk_triggered')
    patterns_found = False
    if careless_triggered_ch4:
        fast_wrong_rate_str = _format_rate(ch4.get('fast_wrong_rate', 0.0))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_CARELESSNESS_ISSUE')}**: 相對快速作答的題目中，錯誤比例偏高 ({fast_wrong_rate_str})，提示可能存在粗心問題。")
        patterns_found = True
    if rushing_triggered_ch4:
        num_rush = len(ch4.get('early_rushing_questions', []))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')}**: 測驗前期 ({num_rush} 題) 出現作答時間過短 (<1分鐘) 的情況，可能影響準確率。")
        patterns_found = True
    if not patterns_found:
        report_lines.append("- 未發現明顯的粗心或前期過快等負面行為模式。")
    report_lines.append("")

    # 5. 詳細診斷說明 (Skipped as per previous logic)

    # 6. 練習建議 (基於第六章)
    report_lines.append("**6. 練習建議**")
    recommendations = ch6.get('recommendations_list', [])
    if not recommendations:
        report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        # Keep simple numbered list for now
        for i, rec in enumerate(recommendations):
            rec_text = rec.get('text', '無建議內容')
            report_lines.append(f"{i+1}. {rec_text}")
        report_lines.append("") # Add space after the list


    # 7. 後續行動指引
    report_lines.append("**7. 後續行動指引**")
    # 7.1 Diagnosis Confirmation
    report_lines.append("  **診斷理解確認:**")
    report_lines.append("  - 請仔細閱讀報告，特別是核心問題分析部分。您是否認同報告指出的主要問題點？這與您考試時的感受是否一致？")
    if sfe_triggered:
        report_lines.append(f"  - 報告顯示您觸發了 '{_translate_di('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')}'。您認為這主要是粗心，還是某些基礎概念確實存在模糊地帶？")
    # Add generic prompt for efficiency bottlenecks if any were triggered
    efficiency_params_present = any(p.startswith('DI_EFFICIENCY_BOTTLENECK_') for p in all_triggered_params)
    if efficiency_params_present:
         report_lines.append(f"  - 報告指出您在某些答對的題目上耗時較長，請回憶效率瓶頸所在。")


    # 7.2 Qualitative Analysis Suggestion
    qual_needed = any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR'])
    if qual_needed:
        report_lines.append("  **質化分析建議:**")
        report_lines.append("  - 如果您對報告中指出的某些問題（尤其是非數學相關的邏輯或閱讀理解錯誤）仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

    # 7.3 Second Evidence Suggestion
    # --- Re-introduce variable preparation for this section --- 
    detailed_items = [] # Initialize list, even though we don't iterate it for output here
    avg_time_per_type = ch3.get('avg_time_per_type_minutes', {}) # Get avg times from ch3 results
    df_problem = pd.DataFrame() # Initialize empty df
    if diagnosed_df is not None and not diagnosed_df.empty and 'diagnostic_params' in diagnosed_df.columns:
        filter_cols = ['is_correct', 'overtime']
        if all(col in diagnosed_df.columns for col in filter_cols):
            df_problem = diagnosed_df[ (diagnosed_df['is_correct'] == False) | (diagnosed_df['overtime'] == True) ].copy()
            # Check if df_problem is actually populated after filtering
            if not df_problem.empty:
                 detailed_items = df_problem.to_dict('records') # Populate detailed_items minimally if needed by logic below
    # --- End variable preparation --- 
    
    report_lines.append("  **二級證據參考建議:**")
    # Check if detailed items were generated (based on df_problem being non-empty)
    # Use df_problem instead of detailed_items directly for the condition
    if not df_problem.empty: # Check if df_problem was successfully created and populated
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
        
        # --- START NEW LOGIC: Group by time_performance_category ---
        details_added_2nd_ev = False
        if 'time_performance_category' in df_problem.columns:
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
                        print(f"DEBUG (di_report): Skipping category '{perf_en}' as requested.") # DEBUG
                        continue # Skip to the next category
                    # --- END SKIP LOGIC ---
                    
                    group_df = grouped_by_performance.get_group(perf_en)
                    if not group_df.empty:
                        perf_zh = _translate_di(perf_en)
                        
                        # Extract unique types and domains from this group
                        types_in_group = group_df['question_type'].dropna().unique()
                        domains_in_group = group_df['content_domain'].dropna().unique()
                        
                        types_zh = sorted([_translate_di(t) for t in types_in_group])
                        domains_zh = sorted([_translate_di(d) for d in domains_in_group])

                        # --- START Extract Unique Labels (Revised) ---
                        all_labels_in_group = set()
                        target_label_col = None
                        # Check if the final Chinese list column exists
                        if 'diagnostic_params_list' in group_df.columns:
                             target_label_col = 'diagnostic_params_list'
                             print(f"DEBUG (di_report): Using existing 'diagnostic_params_list' column.") # DEBUG
                        # If not, check if the original English column exists
                        elif 'diagnostic_params' in group_df.columns:
                             target_label_col = 'diagnostic_params'
                             print(f"DEBUG (di_report): Found 'diagnostic_params' column, will translate internally.") # DEBUG
                        else:
                             print(f"DEBUG (di_report): Neither 'diagnostic_params_list' nor 'diagnostic_params' found for this group!") # DEBUG

                        if target_label_col:
                            print(f"DEBUG (di_report):   Processing labels from column: {target_label_col}") # DEBUG
                            labels_head = group_df[target_label_col].head().tolist() # Get first 5 lists
                            print(f"DEBUG (di_report):   Head of {target_label_col}: {labels_head}") # DEBUG
                            
                            for labels_list in group_df[target_label_col]:
                                if isinstance(labels_list, list): # Check if it's a list
                                     # If using original English codes, translate them now
                                     if target_label_col == 'diagnostic_params':
                                         translated_list = _translate_di(labels_list) # Translate the list
                                         all_labels_in_group.update(translated_list)
                                     else: # Already Chinese
                                         all_labels_in_group.update(labels_list)
                        
                        # Labels in all_labels_in_group should now be Chinese
                        sorted_labels_zh = sorted(list(all_labels_in_group))
                        print(f"DEBUG (di_report):   Sorted unique Chinese labels found: {sorted_labels_zh}") # DEBUG
                        # --- END Extract Unique Labels (Revised) ---

                        # --- Modify Report Line ---
                        report_line = f"  - **{perf_zh}:** 需關注題型：【{', '.join(types_zh)}】；涉及領域：【{', '.join(domains_zh)}】。"
                        if sorted_labels_zh:
                             report_line += f" 注意相關問題點：【{', '.join(sorted_labels_zh)}】。"
                        report_lines.append(report_line)
                        # --- End Modify Report Line ---
                        
                        details_added_2nd_ev = True
        else:
            report_lines.append("  - (警告：缺少 'time_performance_category' 欄位，無法按時間表現分類。)")
            # --- FALLBACK TO OLD LOGIC (optional, or just skip?) ---
            # Maybe skip fallback to avoid confusion
            pass
        # --- END NEW LOGIC ---

        # Report core issues again (Keep this part)
        core_issue_texts = []
        if sfe_triggered: core_issue_texts.append(_translate_di('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'))
        # Assuming top_other_params_codes is still calculated correctly earlier in the function
        if 'top_other_params_codes' in locals() and top_other_params_codes: 
             core_issue_texts.extend([_translate_di(p) for p in top_other_params_codes])

        if core_issue_texts:
             report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(core_issue_texts)}】。")
             details_added_2nd_ev = True

        if not details_added_2nd_ev:
             report_lines.append("  - (本次分析未聚焦到特定的問題類型或領域)")

        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")


    # 7.4 Tools and Prompts Recommendation
    report_lines.append("  **輔助工具與 AI 提示推薦建議:**")
    recommended_di_tools = set()
    recommended_di_prompts = set()
    processed_for_tools_di = set()
    recommendations_made_di = False

    # Use all_triggered_params calculated at the start of Ch7 generation
    unique_triggered_params = set(all_triggered_params) # Ensure uniqueness

    for params_set, tool_desc in DI_TOOL_RECOMMENDATIONS_MAP.items():
        # Check if the required set of params is a subset of triggered params
        # Or if ANY of the params in the set were triggered (depending on desired logic)
        # Let's use 'any' for broader matching based on the examples provided
        trigger_match = any(p in unique_triggered_params for p in params_set)

        if trigger_match and not params_set.issubset(processed_for_tools_di):
            import re
            all_backticked = re.findall(r'`([^`]+?)`', tool_desc)
            current_tools = {item for item in all_backticked if not item.endswith('.md') and item.strip()}
            current_prompts = {item for item in all_backticked if item.endswith('.md')}

            if current_tools:
                recommended_di_tools.update(current_tools)
                recommendations_made_di = True
            if current_prompts:
                recommended_di_prompts.update(current_prompts)
                recommendations_made_di = True

            processed_for_tools_di.update(params_set)

    # Output collected tools and prompts
    tools_were_recommended_di = bool(recommended_di_tools)
    prompts_were_recommended_di = bool(recommended_di_prompts)

    if tools_were_recommended_di:
        report_lines.append("  - *工具:*" + (" (請根據問題選用)" if len(recommended_di_tools)>1 else ""))
        for tool in sorted(list(recommended_di_tools)):
            report_lines.append(f"    - `{tool}`")

    if prompts_were_recommended_di:
        if tools_were_recommended_di:
             report_lines.append("")
        report_lines.append("  - *AI提示:*" + (" (請根據問題選用)" if len(recommended_di_prompts)>1 else ""))
        for prompt in sorted(list(recommended_di_prompts)):
            report_lines.append(f"    - `{prompt}`")

    if not recommendations_made_di:
        report_lines.append("  - 根據當前診斷，暫無特別推薦的輔助工具或 AI 提示。")


    # Use double newline for Markdown paragraph breaks
    return "\n\n".join(report_lines)