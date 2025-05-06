"""
V診斷模塊的主要診斷功能

此模塊包含V(Verbal)診斷的主要入口點函數，
用於組織和執行完整的診斷流程。
"""

import pandas as pd
import logging

from gmat_diagnosis_app.diagnostics.v_modules.constants import INVALID_DATA_TAG_V
from gmat_diagnosis_app.diagnostics.v_modules.translations import translate_v
from gmat_diagnosis_app.diagnostics.v_modules.utils import (
    grade_difficulty_v, 
    analyze_dimension, 
    calculate_skill_exemption_status, 
    calculate_skill_override
)
from gmat_diagnosis_app.diagnostics.v_modules.analysis import (
    observe_patterns, 
    analyze_correct_slow, 
    apply_ch3_diagnostic_rules
)
from gmat_diagnosis_app.diagnostics.v_modules.recommendations import generate_v_recommendations
from gmat_diagnosis_app.diagnostics.v_modules.reporting import generate_v_summary_report


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
    # === DEBUG START ===
    logging.info("[V Diag - Entry] Received data. Overtime count: %s", df_v_processed['overtime'].sum())
    logging.info("[V Diag - Entry] Input df overtime head:\n%s", df_v_processed[['question_position', 'question_time', 'overtime']].head().to_string())
    # === DEBUG END ===
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
    # Ensure fundamental skill exists, default to 'Unknown Skill'
    if 'question_fundamental_skill' not in df_v.columns:
        df_v['question_fundamental_skill'] = 'Unknown Skill'
    else:
        # Fill NaN in fundamental skill AFTER it's ensured to exist
        df_v['question_fundamental_skill'] = df_v['question_fundamental_skill'].fillna('Unknown Skill')

    if 'is_correct' not in df_v.columns: df_v['is_correct'] = True # Assume correct if missing

    df_v['question_time'] = pd.to_numeric(df_v['question_time'], errors='coerce')
    df_v['question_difficulty'] = pd.to_numeric(df_v['question_difficulty'], errors='coerce') # Ensure difficulty is numeric

    if 'question_position' not in df_v.columns:
         df_v['question_position'] = range(len(df_v))
    else:
         df_v['question_position'] = pd.to_numeric(df_v['question_position'], errors='coerce')

    df_v['is_correct'] = df_v['is_correct'].astype(bool)

    if 'is_invalid' not in df_v.columns: df_v['is_invalid'] = False

    # Initialize diagnostic columns safely
    if 'diagnostic_params' not in df_v.columns:
        df_v['diagnostic_params'] = [[] for _ in range(len(df_v))]
    else:
        # Ensure it's a mutable list, handle potential NaNs
        df_v['diagnostic_params'] = df_v['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x]))

    # Initialize potentially missing boolean flags needed later
    for col in ['overtime', 'suspiciously_fast', 'is_sfe', 'is_relatively_fast']:
        if col not in df_v.columns: df_v[col] = False
    if 'time_performance_category' not in df_v.columns: df_v['time_performance_category'] = ''


    # --- Add Tag based on FINAL 'is_invalid' status ---
    final_invalid_mask_v = df_v['is_invalid']
    if final_invalid_mask_v.any():
        for idx in df_v.index[final_invalid_mask_v]:
            current_list = df_v.loc[idx, 'diagnostic_params']
            # Ensure current_list is a list before appending
            if not isinstance(current_list, list): current_list = []
            if INVALID_DATA_TAG_V not in current_list: current_list.append(INVALID_DATA_TAG_V)
            df_v.loc[idx, 'diagnostic_params'] = current_list

    num_invalid_v_total = df_v['is_invalid'].sum()
    v_diagnosis_results['invalid_count'] = num_invalid_v_total

    # --- Filter out invalid data ---
    df_v_processed_full = df_v.copy() # Store potentially modified df before filtering valid
    df_v_valid = df_v[~df_v['is_invalid']].copy() # Use the latest df_v

    if df_v_valid.empty:
        print("    No V data remaining after excluding invalid entries. Skipping further V diagnosis.")
        minimal_report = generate_v_summary_report(v_diagnosis_results)
        # Ensure essential columns exist even for empty valid df scenario return
        essential_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time',
                          'question_type', 'question_fundamental_skill', 'Subject', 'is_invalid',
                          'overtime', 'suspiciously_fast', 'is_sfe',
                          'time_performance_category', 'diagnostic_params_list']
        for col in essential_cols:
            if col not in df_v_processed_full.columns:
                 # Add column appropriately (e.g., bool for flags, empty list for list cols)
                 if col == 'diagnostic_params_list':
                     df_v_processed_full[col] = [[] for _ in range(len(df_v_processed_full))]
                 elif col == 'Subject':
                     df_v_processed_full[col] = 'V'
                 elif col in ['overtime', 'suspiciously_fast', 'is_sfe']:
                     df_v_processed_full[col] = False
                 elif col == 'time_performance_category':
                     df_v_processed_full[col] = ''
                 else: # Default for others (like numeric/object)
                     df_v_processed_full[col] = None
        return v_diagnosis_results, minimal_report, df_v_processed_full # Return the df with invalid tags

    # --- Chapter 1 Global Rule: Mark Suspiciously Fast ---
    # Ensure suspicious_fast exists before modification
    if 'suspiciously_fast' not in df_v.columns: df_v['suspiciously_fast'] = False
    for q_type, avg_time in v_avg_time_per_type.items():
        # Check avg_time is valid before using
        if avg_time is not None and pd.notna(avg_time) and avg_time > 0 and 'question_time' in df_v.columns:
             valid_time_mask = df_v['question_time'].notna()
             not_invalid_mask = ~df_v['is_invalid'] # Use latest is_invalid status
             suspicious_mask = (df_v['question_type'] == q_type) & \
                               (df_v['question_time'] < (avg_time * 0.5)) & \
                               valid_time_mask & \
                               not_invalid_mask
             df_v.loc[suspicious_mask, 'suspiciously_fast'] = True


    # --- Apply Chapter 3 Diagnostic Rules ---
    # Calculate max correct difficulty on VALID data
    df_correct_valid_v = df_v_valid[df_v_valid['is_correct'] == True].copy()
    max_correct_difficulty_per_skill_v = {}
    if not df_correct_valid_v.empty and 'question_fundamental_skill' in df_correct_valid_v.columns and 'question_difficulty' in df_correct_valid_v.columns:
        # Ensure difficulty is numeric before calculating max
        numeric_diff_correct = pd.to_numeric(df_correct_valid_v['question_difficulty'], errors='coerce')
        if numeric_diff_correct.notna().any():
             df_correct_v_skill_valid = df_correct_valid_v.dropna(subset=['question_fundamental_skill', 'question_difficulty'])
             df_correct_v_skill_valid['question_difficulty'] = pd.to_numeric(df_correct_v_skill_valid['question_difficulty'], errors='coerce')
             df_correct_v_skill_valid = df_correct_v_skill_valid.dropna(subset=['question_difficulty']) # Drop rows where conversion failed
             if not df_correct_v_skill_valid.empty:
                 max_correct_difficulty_per_skill_v = df_correct_v_skill_valid.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # Apply rules - modifies df_v in place. Pass v_time_pressure_status here.
    # Overtime calculation is now embedded within this function.
    df_v = apply_ch3_diagnostic_rules(df_v, max_correct_difficulty_per_skill_v, v_avg_time_per_type, v_time_pressure_status)

    # === DEBUG START ===
    logging.info("[V Diag - After Ch3 Rules] Overtime count: %s", df_v['overtime'].sum())
    logging.info("[V Diag - After Ch3 Rules] Sample with time category:\n%s", df_v[['question_position', 'overtime', 'time_performance_category']].head().to_string())
    # === DEBUG END ===

    # --- Translate diagnostic codes ---
    if 'diagnostic_params' in df_v.columns:
        # Ensure the lambda handles non-list inputs gracefully
        df_v['diagnostic_params_list'] = df_v['diagnostic_params'].apply(
            lambda params: [translate_v(p) for p in params if isinstance(p, str)] if isinstance(params, list) else []
        )
    else:
        # Initialize if 'diagnostic_params' somehow got dropped
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

    v_diagnosis_results.setdefault('chapter_2', {})['overall_metrics'] = analyze_dimension(df_valid_v, None)
    v_diagnosis_results.setdefault('chapter_2', {})['by_type'] = analyze_dimension(df_valid_v, 'question_type')
    # Ensure difficulty grading happens on the valid data for Ch2 analysis
    df_valid_v['difficulty_grade'] = df_valid_v['question_difficulty'].apply(grade_difficulty_v)
    v_diagnosis_results.setdefault('chapter_2', {})['by_difficulty'] = analyze_dimension(df_valid_v, 'difficulty_grade')
    # >>> MODIFICATION: Add analysis by skill <<<
    v_diagnosis_results.setdefault('chapter_2', {})['by_skill'] = analyze_dimension(df_valid_v, 'question_fundamental_skill')
    print("    Finished Chapter 2 V metrics.")

    # --- Populate Chapter 3 Results ---
    print("  Structuring V Analysis Results (Chapter 3)...")
    # Store the dataframe WITH BOTH param columns for report generator
    # Store the df *after* Ch3 rules have been applied (initially)
    # We will update this df later after adding behavioral tags from Ch5
    df_after_ch3 = df_v.copy()
    v_diagnosis_results['chapter_3'] = {'diagnosed_dataframe': df_after_ch3} # Store initial Ch3 df
    print("    Finished Chapter 3 V result structuring.")

    # --- Populate Chapter 4 Results (Correct but Slow on VALID data) ---
    print("  Executing V Analysis (Chapter 4 - Correct Slow)...")
    # Use valid data derived from the df *after* Ch3 processing
    df_valid_v_post_ch3 = df_v[~df_v['is_invalid']].copy()
    df_correct_v = df_valid_v_post_ch3[df_valid_v_post_ch3['is_correct'] == True].copy() # Use valid data post Ch3
    # === DEBUG START - CH4 Input ===
    logging.info("[V Diag - Ch4] Input df_correct_v for analyze_correct_slow (shape: %s). Overtime counts:\n%s",
                 df_correct_v.shape, df_correct_v['overtime'].value_counts().to_string() if 'overtime' in df_correct_v else "Overtime col missing")
    # === ADDED DEBUG - Check Question Types in df_correct_v ===
    if not df_correct_v.empty and 'question_type' in df_correct_v:
        logging.info("[V Diag - Ch4] Question types present in df_correct_v:\n%s", df_correct_v['question_type'].value_counts().to_string())
    # === DEBUG END ===
    # === DEBUG END ===
    # === MODIFICATION: Use full question type names for filtering ===
    cr_correct_slow_result = analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'Critical Reasoning'], 'CR')
    rc_correct_slow_result = analyze_correct_slow(df_correct_v[df_correct_v['question_type'] == 'Reading Comprehension'], 'RC')
    # === END MODIFICATION ===
    # === DEBUG START - CH4 Results ===
    logging.info("[V Diag - Ch4] Result from analyze_correct_slow(CR): %s", cr_correct_slow_result)
    logging.info("[V Diag - Ch4] Result from analyze_correct_slow(RC): %s", rc_correct_slow_result)
    # === DEBUG END ===
    v_diagnosis_results['chapter_4'] = {
        'cr_correct_slow': cr_correct_slow_result,
        'rc_correct_slow': rc_correct_slow_result
    }
    print("    Finished Chapter 4 V correct slow analysis.")

    # --- Populate Chapter 5 Results (Behavioral Patterns on VALID data) ---
    print("  Executing V Analysis (Chapter 5 - Behavioral Patterns)...")
    # Use the valid data derived from the df *after* Ch3 processing for pattern observation
    df_valid_v_for_ch5 = df_v[~df_v['is_invalid']].copy() # Use df_v state AFTER Ch3
    ch5_behavioral_analysis = observe_patterns(df_valid_v_for_ch5, v_time_pressure_status)
    v_diagnosis_results['chapter_5'] = ch5_behavioral_analysis
    print("    Finished Chapter 5 V behavioral analysis.")

    # === NEW: Apply Behavioral Tags (e.g., Carelessness) BACK to DataFrame ===
    # We modify the main df_v dataframe, which contains all rows (incl. invalid)
    # but the indices come from analysis on valid data.
    carelessness_indices = ch5_behavioral_analysis.get('carelessness_question_indices', [])
    if carelessness_indices:
        print(f"    Applying BEHAVIOR_CARELESSNESS_ISSUE tag to indices: {carelessness_indices}")
        for index in carelessness_indices:
            if index in df_v.index: # Ensure index exists in the main df
                 current_params = df_v.loc[index, 'diagnostic_params']
                 # Ensure it's a list before appending
                 if not isinstance(current_params, list):
                     current_params = []
                 if 'BEHAVIOR_CARELESSNESS_ISSUE' not in current_params:
                     # Create a new list and assign it back
                     new_params = current_params + ['BEHAVIOR_CARELESSNESS_ISSUE']
                     # Use .at for scalar assignment
                     df_v.at[index, 'diagnostic_params'] = new_params
                     # Also update the translated list if it exists
                     if 'diagnostic_params_list' in df_v.columns:
                         current_translated = df_v.loc[index, 'diagnostic_params_list'] # Reading with .loc is fine
                         if not isinstance(current_translated, list):
                             current_translated = []
                         translated_tag = translate_v('BEHAVIOR_CARELESSNESS_ISSUE')
                         if translated_tag not in current_translated:
                             # Create a new list and assign it back
                             new_translated_list = current_translated + [translated_tag]
                             # Use .at for scalar assignment
                             df_v.at[index, 'diagnostic_params_list'] = new_translated_list
            else:
                 print(f"    Warning: Carelessness index {index} not found in main df_v.")

    # Update the dataframe in Chapter 3 results *after* adding behavioral tags
    v_diagnosis_results['chapter_3']['diagnosed_dataframe'] = df_v.copy()
    # =========================================================================

    # --- Populate Chapter 6 Results (Skill Override Check on VALID data) ---
    print("  Executing V Analysis (Chapter 6 - Skill Override)...")
    # Use valid data derived from the df *after* Ch3 processing
    exempted_skills = calculate_skill_exemption_status(df_valid_v_post_ch3)
    ch6_override_results = calculate_skill_override(df_valid_v_post_ch3)
    ch6_results = {**ch6_override_results, 'exempted_skills': exempted_skills}
    v_diagnosis_results['chapter_6'] = ch6_results
    print(f"    Finished Chapter 6 V skill override/exemption analysis. Exempted: {exempted_skills}")

    # --- Generate Recommendations & Summary Report (Chapter 7 & 8) --- #
    # Pass the df *after* Ch3 processing to recommendation generator
    v_recommendations = generate_v_recommendations(v_diagnosis_results, exempted_skills)
    v_diagnosis_results['chapter_7'] = v_recommendations

    # Generate report using results containing the df with both param columns
    # === DEBUG START - Report Input ===
    logging.info("[V Diag - Report Gen] Input v_diagnosis_results['chapter_4'] for report:\n%s", v_diagnosis_results.get('chapter_4'))
    # === DEBUG END ===
    v_report_content = generate_v_summary_report(v_diagnosis_results)

    # --- Prepare Final DataFrame for Return ---
    df_v_final = df_v.copy() # Start with the df that has Ch3 results

    # === DEBUG START ===
    logging.info("[V Diag - Before Return] Final df overtime count: %s", df_v_final['overtime'].sum())
    logging.info("[V Diag - Before Return] Final df overtime head:\n%s", df_v_final[['question_position', 'overtime']].head().to_string())
    # === DEBUG END ===

    # --- Drop English column AFTER report is generated ---
    if 'diagnostic_params' in df_v_final.columns:
        try:
            df_v_final.drop(columns=['diagnostic_params'], inplace=True)
        except KeyError:
            pass # Ignore if already dropped

    # --- Ensure Subject Column ---
    if 'Subject' not in df_v_final.columns or df_v_final['Subject'].isnull().any() or (df_v_final['Subject'] != 'V').any():
        df_v_final['Subject'] = 'V'

    print("  Verbal Diagnosis Complete.")

    # Return the final df AFTER dropping the English params col
    return v_diagnosis_results, v_report_content, df_v_final 