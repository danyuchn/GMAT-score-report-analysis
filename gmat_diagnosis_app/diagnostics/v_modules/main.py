"""
V診斷模塊的主要診斷功能

此模塊包含V(Verbal)診斷的主要入口點函數，
用於組織和執行完整的診斷流程。
"""

import pandas as pd
import logging
# import streamlit as st # Removed this unused top-level import

from gmat_diagnosis_app.diagnostics.v_modules.constants import INVALID_DATA_TAG_V, V_SUSPICIOUS_FAST_MULTIPLIER, RC_READING_TIME_THRESHOLD_3Q, RC_READING_TIME_THRESHOLD_4Q
# Use i18n system instead of the old translation function
from gmat_diagnosis_app.i18n import translate as t
from gmat_diagnosis_app.diagnostics.v_modules.utils import (
    grade_difficulty_v, 
    analyze_dimension, 
    calculate_skill_exemption_status, 
    calculate_skill_override,
    calculate_metrics_for_group
)
from gmat_diagnosis_app.diagnostics.v_modules.analysis import (
    observe_patterns, 
    analyze_correct_slow, 
    apply_ch3_diagnostic_rules
)
from gmat_diagnosis_app.diagnostics.v_modules.recommendations import generate_v_recommendations
from gmat_diagnosis_app.diagnostics.v_modules.reporting import generate_v_summary_report


# Removed deprecated function run_v_diagnosis
# def run_v_diagnosis(df_v_raw, v_time_pressure_status, v_avg_time_per_type):
#     """
#     DEPRECATED - Logic moved to run_v_diagnosis_processed.
#     """
#     time_pressure_status_map = {'V': v_time_pressure_status}
#     # Assuming this import works in the actual environment
#     from gmat_diagnosis_app.preprocess_helpers import suggest_invalid_questions
#     df_v_preprocessed = suggest_invalid_questions(df_v_raw, time_pressure_status_map)
#     return run_v_diagnosis_processed(df_v_preprocessed, v_time_pressure_status, v_avg_time_per_type)


def run_v_diagnosis_processed(df_v_processed, v_time_pressure_status, v_avg_time_per_type):
    try:
        # 添加調試日誌
        # import streamlit as st # Removed unused import from function scope
        import logging
        
        # 調試檢查手動標記的無效項
        if 'is_manually_invalid' in df_v_processed.columns:
            manual_invalid_count = df_v_processed['is_manually_invalid'].sum()
            if manual_invalid_count > 0:
                # logging.info(f"V科診斷: 檢測到 {manual_invalid_count} 個手動標記的無效項") # REMOVED by AI
                # logging.info(f"手動標記無效的題號: {manually_invalid_positions}") # REMOVED by AI
                pass # End of manually_invalid check
        
        # 重要修改：完全以手動標記為準，不合併自動標記的結果
        # 先檢查是否存在手動標記列
        if 'is_manually_invalid' in df_v_processed.columns:
            # 不管之前is_invalid的值如何，完全重設為False
            if 'is_invalid' in df_v_processed.columns:
                df_v_processed['is_invalid'] = False
            else:
                df_v_processed['is_invalid'] = False  # 如果不存在，創建一個全為False的列
            
            # 只將手動標記的項目設為無效
            df_v_processed.loc[df_v_processed['is_manually_invalid'] == True, 'is_invalid'] = True
            
            # 重新計算無效項數量 (僅記錄到日誌，不顯示在UI中)
            invalid_count = df_v_processed['is_invalid'].sum()
            # logging.info(f"V科診斷: 僅使用手動標記，無效項數量為 {invalid_count}") # REMOVED by AI
            
            # 調試信息：確認是否只有手動標記的項目被設為無效 (僅記錄到日誌)
            if invalid_count != manual_invalid_count:
                logging.warning(f"警告：無效項數量 ({invalid_count}) 與手動標記數量 ({manual_invalid_count}) 不一致！")
        
        # --- Chapter 0: Initial Setup and Basic Metrics ---
        logging.debug("[V Diag - Entry] Received data. Overtime count: %s", df_v_processed['overtime'].sum() if 'overtime' in df_v_processed.columns else 'N/A')
        logging.debug("[V Diag - Entry] Input df overtime head:\\n%s", df_v_processed[['question_position', 'question_time', 'overtime']].head().to_string() if 'overtime' in df_v_processed.columns else "Overtime col missing")

        # Convert time to numeric, fill NaNs
        df_v_processed['question_time'] = pd.to_numeric(df_v_processed['question_time'], errors='coerce')
        df_v_processed['question_difficulty'] = pd.to_numeric(df_v_processed['question_difficulty'], errors='coerce') # Ensure difficulty is numeric

        if 'question_position' not in df_v_processed.columns:
             df_v_processed['question_position'] = range(len(df_v_processed))
        else:
             df_v_processed['question_position'] = pd.to_numeric(df_v_processed['question_position'], errors='coerce')

        df_v_processed['is_correct'] = df_v_processed['is_correct'].astype(bool)

        if 'is_invalid' not in df_v_processed.columns: df_v_processed['is_invalid'] = False

        # Initialize diagnostic columns safely
        if 'diagnostic_params' not in df_v_processed.columns:
            df_v_processed['diagnostic_params'] = [[] for _ in range(len(df_v_processed))]
        else:
            # Ensure it's a mutable list, handle potential NaNs
            df_v_processed['diagnostic_params'] = df_v_processed['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x]))

        # Initialize potentially missing boolean flags needed later
        for col in ['overtime', 'suspiciously_fast', 'is_sfe', 'is_relatively_fast']:
            if col not in df_v_processed.columns: df_v_processed[col] = False
        if 'time_performance_category' not in df_v_processed.columns: df_v_processed['time_performance_category'] = ''


        # --- Add Tag based on FINAL 'is_invalid' status ---
        final_invalid_mask_v = df_v_processed['is_invalid']
        if final_invalid_mask_v.any():
            invalid_count = final_invalid_mask_v.sum()
            # 減少UI輸出
            # logging.info(f"V科診斷: 將為 {invalid_count} 個標記為無效的項目添加無效數據標籤") # REMOVED by AI
            
            for idx in df_v_processed.index[final_invalid_mask_v]:
                current_list = df_v_processed.loc[idx, 'diagnostic_params']
                # Ensure current_list is a list before appending
                if not isinstance(current_list, list): current_list = []
                if INVALID_DATA_TAG_V not in current_list: current_list.append(INVALID_DATA_TAG_V)
                df_v_processed.loc[idx, 'diagnostic_params'] = current_list

        num_invalid_v_total = df_v_processed['is_invalid'].sum()
        v_diagnosis_results = {}
        v_diagnosis_results['invalid_count'] = num_invalid_v_total
        
        # 僅在日誌中記錄
        # logging.info(f"V科診斷: 總共有 {num_invalid_v_total} 個項目被標記為無效") # REMOVED by AI

        # --- Create df_v_valid_for_analysis_only for specific analyses that ONLY need valid data ---
        # This df is for reading/analysis, not for modifying rows that go back to the main df_v_processed
        df_v_valid_for_analysis_only = df_v_processed[~df_v_processed['is_invalid']].copy()


        # --- Chapter 1: RC Reading Comprehension Barrier Inquiry (on df_v_valid_for_analysis_only) ---
        # This section calculates 'reading_comprehension_barrier_inquiry' as a summary metric.
        # It does not directly affect per-row time_performance_category for display.
        # Initialize the column in the analysis-only df first
        df_v_valid_for_analysis_only['reading_comprehension_barrier_inquiry'] = False
        if 'rc_reading_time' in df_v_valid_for_analysis_only.columns and \
           'rc_group_num_questions' in df_v_valid_for_analysis_only.columns and \
           'rc_group_id' in df_v_valid_for_analysis_only.columns:
            df_v_valid_for_analysis_only['rc_reading_time'] = pd.to_numeric(df_v_valid_for_analysis_only['rc_reading_time'], errors='coerce')
            df_v_valid_for_analysis_only['rc_group_num_questions'] = pd.to_numeric(df_v_valid_for_analysis_only['rc_group_num_questions'], errors='coerce')

            rc_barrier_triggered_groups = set()
            first_questions_in_groups = df_v_valid_for_analysis_only[df_v_valid_for_analysis_only['rc_reading_time'] != 0]
            
            for idx, row in first_questions_in_groups.iterrows():
                if row['question_type'] == 'Reading Comprehension':
                    group_id = row['rc_group_id']
                    num_q = row['rc_group_num_questions']
                    reading_time = row['rc_reading_time']
                    
                    barrier = False
                    if pd.notna(num_q) and pd.notna(reading_time):
                        if (num_q == 3 and reading_time > RC_READING_TIME_THRESHOLD_3Q) or \
                           (num_q == 4 and reading_time > RC_READING_TIME_THRESHOLD_4Q):
                            barrier = True
                    
                    if barrier and pd.notna(group_id):
                        rc_barrier_triggered_groups.add(group_id)
            
            if rc_barrier_triggered_groups:
                for group_id_to_mark in rc_barrier_triggered_groups:
                    # Mark in the analysis-only DataFrame
                    df_v_valid_for_analysis_only.loc[df_v_valid_for_analysis_only['rc_group_id'] == group_id_to_mark, 'reading_comprehension_barrier_inquiry'] = True
        # --- End RC Reading Comprehension Barrier Inquiry ---


        if df_v_valid_for_analysis_only.empty:
            logging.warning("No V data remaining after excluding invalid entries for specific analyses. Diagnosis will proceed on all data where applicable.")
            # Do not return early, proceed with df_v_processed

        # --- Chapter 1 Global Rule: Mark Suspiciously Fast (on df_v_processed) ---
        # This flag is used in observe_patterns, which itself runs on a valid data subset.
        # However, calculating it on df_v_processed and then filtering is fine.
        if 'suspiciously_fast' not in df_v_processed.columns: df_v_processed['suspiciously_fast'] = False
        for q_type, avg_time in v_avg_time_per_type.items():
            if avg_time is not None and pd.notna(avg_time) and avg_time > 0 and 'question_time' in df_v_processed.columns:
                 valid_time_mask = df_v_processed['question_time'].notna()
                 # Apply to non-invalid rows within df_v_processed
                 not_invalid_mask = ~df_v_processed['is_invalid']
                 suspicious_mask = (df_v_processed['question_type'] == q_type) & \
                                   (df_v_processed['question_time'] < (avg_time * V_SUSPICIOUS_FAST_MULTIPLIER)) & \
                                   valid_time_mask & \
                                   not_invalid_mask 
                 df_v_processed.loc[suspicious_mask, 'suspiciously_fast'] = True


        # --- Apply Chapter 3 Diagnostic Rules (on df_v_processed) ---
        # Calculate max correct difficulty on VALID data for SFE rule
        df_correct_valid_v_for_sfe = df_v_processed[(df_v_processed['is_correct'] == True) & (~df_v_processed['is_invalid'])].copy()
        max_correct_difficulty_per_skill_v = {}
        if not df_correct_valid_v_for_sfe.empty and 'question_fundamental_skill' in df_correct_valid_v_for_sfe.columns and 'question_difficulty' in df_correct_valid_v_for_sfe.columns:
            numeric_diff_correct = pd.to_numeric(df_correct_valid_v_for_sfe['question_difficulty'], errors='coerce')
            if numeric_diff_correct.notna().any():
                 df_correct_v_skill_valid_for_sfe = df_correct_valid_v_for_sfe.dropna(subset=['question_fundamental_skill', 'question_difficulty'])
                 df_correct_v_skill_valid_for_sfe['question_difficulty'] = pd.to_numeric(df_correct_v_skill_valid_for_sfe['question_difficulty'], errors='coerce')
                 df_correct_v_skill_valid_for_sfe = df_correct_v_skill_valid_for_sfe.dropna(subset=['question_difficulty']) 
                 if not df_correct_v_skill_valid_for_sfe.empty:
                     max_correct_difficulty_per_skill_v = df_correct_v_skill_valid_for_sfe.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

        # apply_ch3_diagnostic_rules will now operate on all rows of df_v_processed
        # It needs to internally handle 'is_invalid' for SFE and specific diagnostic_params.
        df_v_processed = apply_ch3_diagnostic_rules(df_v_processed, max_correct_difficulty_per_skill_v, v_avg_time_per_type, v_time_pressure_status)

        # === DEBUG START ===
        logging.debug("[V Diag - After Ch3 Rules on df_v_processed] Overtime count: %s", df_v_processed['overtime'].sum() if 'overtime' in df_v_processed.columns else 'N/A')
        logging.debug("[V Diag - After Ch3 Rules on df_v_processed] Sample with time category:\n%s", df_v_processed[['question_position', 'overtime', 'time_performance_category', 'is_invalid']].head().to_string() if 'time_performance_category' in df_v_processed.columns else "Time category col missing")
        # === DEBUG END ===

        # --- Translate diagnostic codes (on df_v_processed) ---
        if 'diagnostic_params' in df_v_processed.columns:
            # Ensure the lambda handles non-list inputs gracefully
            df_v_processed['diagnostic_params_list'] = df_v_processed['diagnostic_params'].apply(
                lambda params: [t(p) for p in params if isinstance(p, str)] if isinstance(params, list) else []
            )
        else:
            # Initialize if 'diagnostic_params' somehow got dropped
            num_rows = len(df_v_processed)
            df_v_processed['diagnostic_params_list'] = pd.Series([[] for _ in range(num_rows)], index=df_v_processed.index)

        # --- Populate Chapter 1 Results ---
        rc_barrier_triggered_metric = False
        if 'reading_comprehension_barrier_inquiry' in df_v_valid_for_analysis_only.columns:
             rc_barrier_triggered_metric = df_v_valid_for_analysis_only['reading_comprehension_barrier_inquiry'].any()

        v_diagnosis_results['chapter_1'] = {
            'time_pressure_status': v_time_pressure_status,
            'invalid_count': num_invalid_v_total,
            'reading_comprehension_barrier_inquiry_triggered': rc_barrier_triggered_metric
        }
        logging.debug("Populated Chapter 1 V results.")

        # --- Populate Chapter 2 Results (Basic Metrics on df_v_valid_for_analysis_only) ---
        logging.debug("Executing V Analysis (Chapter 2 - Metrics using df_v_valid_for_analysis_only)...")
        # Recalculate valid df based on potentially modified df_v's is_invalid column
        # df_valid_v = df_v_valid.copy() # Use the latest df_v # This line is redundant if df_v_valid_for_analysis_only is used

        v_diagnosis_results.setdefault('chapter_2', {})['overall_metrics'] = calculate_metrics_for_group(df_v_valid_for_analysis_only)
        v_diagnosis_results.setdefault('chapter_2', {})['by_type'] = analyze_dimension(df_v_valid_for_analysis_only, 'question_type')
        # Ensure difficulty grading happens on the valid data for Ch2 analysis
        if not df_v_valid_for_analysis_only.empty: # Check if df is not empty before applying functions
            df_v_valid_for_analysis_only['difficulty_grade'] = df_v_valid_for_analysis_only['question_difficulty'].apply(grade_difficulty_v)
            v_diagnosis_results.setdefault('chapter_2', {})['by_difficulty'] = analyze_dimension(df_v_valid_for_analysis_only, 'difficulty_grade')
            v_diagnosis_results.setdefault('chapter_2', {})['by_skill'] = analyze_dimension(df_v_valid_for_analysis_only, 'question_fundamental_skill')
        else: # Handle empty case for by_difficulty and by_skill
            v_diagnosis_results.setdefault('chapter_2', {})['by_difficulty'] = {}
            v_diagnosis_results.setdefault('chapter_2', {})['by_skill'] = {}
            
        logging.debug("Finished Chapter 2 V metrics.")

        # --- Populate Chapter 3 Results ---
        logging.debug("Structuring V Analysis Results (Chapter 3)...")
        # Store the dataframe WITH BOTH param columns for report generator
        # Store the df *after* Ch3 rules have been applied (initially)
        # We will update this df later after adding behavioral tags from Ch5
        v_diagnosis_results['chapter_3'] = {'diagnosed_dataframe': df_v_processed.copy()} # Store the full df_v_processed
        logging.debug("Finished Chapter 3 V result structuring.")

        # --- Populate Chapter 4 Results (Correct but Slow on a filtered version of df_v_processed) ---
        logging.debug("Executing V Analysis (Chapter 4 - Correct Slow)...")
        df_correct_v_for_ch4 = df_v_processed[(df_v_processed['is_correct'] == True) & (~df_v_processed['is_invalid'])].copy()
        # === DEBUG START - CH4 Input ===
        logging.debug("[V Diag - Ch4] Input df_correct_v_for_ch4 for analyze_correct_slow (shape: %s). Overtime counts:\n%s",
                     df_correct_v_for_ch4.shape, df_correct_v_for_ch4['overtime'].value_counts().to_string() if 'overtime' in df_correct_v_for_ch4 else "Overtime col missing")
        # === ADDED DEBUG - Check Question Types in df_correct_v_for_ch4 ===
        if not df_correct_v_for_ch4.empty and 'question_type' in df_correct_v_for_ch4:
            logging.debug("[V Diag - Ch4] Question types present in df_correct_v_for_ch4:\n%s", df_correct_v_for_ch4['question_type'].value_counts().to_string())
        # === DEBUG END ===
        # === MODIFICATION: Use full question type names for filtering ===
        cr_correct_slow_result = analyze_correct_slow(df_correct_v_for_ch4[df_correct_v_for_ch4['question_type'] == 'Critical Reasoning'], 'CR')
        rc_correct_slow_result = analyze_correct_slow(df_correct_v_for_ch4[df_correct_v_for_ch4['question_type'] == 'Reading Comprehension'], 'RC')
        # === END MODIFICATION ===
        # === DEBUG START - CH4 Results ===
        logging.debug("[V Diag - Ch4] Result from analyze_correct_slow(CR): %s", cr_correct_slow_result)
        logging.debug("[V Diag - Ch4] Result from analyze_correct_slow(RC): %s", rc_correct_slow_result)
        # === DEBUG END ===
        v_diagnosis_results['chapter_4'] = {
            'cr_correct_slow': cr_correct_slow_result,
            'rc_correct_slow': rc_correct_slow_result
        }
        logging.debug("Finished Chapter 4 V correct slow analysis.")

        # --- Populate Chapter 5 Results (Behavioral Patterns on a filtered version of df_v_processed) ---
        logging.debug("Executing V Analysis (Chapter 5 - Behavioral Patterns)...")
        # Use the valid data derived from the df *after* Ch3 processing for pattern observation
        df_valid_v_for_ch5_analysis = df_v_processed[~df_v_processed['is_invalid']].copy()
        ch5_behavioral_analysis = observe_patterns(df_valid_v_for_ch5_analysis) # Updated call to observe_patterns
        v_diagnosis_results['chapter_5'] = ch5_behavioral_analysis
        logging.debug("Finished Chapter 5 V behavioral analysis.")

        # === NEW: Apply Behavioral Tags (e.g., Carelessness) BACK to df_v_processed ===
        carelessness_indices = ch5_behavioral_analysis.get('carelessness_question_indices', [])
        if carelessness_indices:
            logging.debug(f"Applying BEHAVIOR_CARELESSNESS_ISSUE tag to indices: {carelessness_indices} in df_v_processed")
            for index in carelessness_indices:
                if index in df_v_processed.index: # Ensure index exists in df_v_processed
                     current_params = df_v_processed.loc[index, 'diagnostic_params']
                     if not isinstance(current_params, list):
                         current_params = []
                     if 'BEHAVIOR_CARELESSNESS_ISSUE' not in current_params:
                         new_params = current_params + ['BEHAVIOR_CARELESSNESS_ISSUE']
                         df_v_processed.at[index, 'diagnostic_params'] = new_params
                         if 'diagnostic_params_list' in df_v_processed.columns:
                             current_translated = df_v_processed.loc[index, 'diagnostic_params_list']
                             if not isinstance(current_translated, list):
                                 current_translated = []
                             translated_tag = t('BEHAVIOR_CARELESSNESS_ISSUE')
                             if translated_tag not in current_translated:
                                 new_translated_list = current_translated + [translated_tag]
                                 df_v_processed.at[index, 'diagnostic_params_list'] = new_translated_list
                else:
                     logging.warning(f"    Warning: Carelessness index {index} not found in df_v_processed.")

        # Update the dataframe in Chapter 3 results *after* adding behavioral tags
        v_diagnosis_results['chapter_3']['diagnosed_dataframe'] = df_v_processed.copy()
        # =========================================================================

        # --- Populate Chapter 6 Results (Skill Override Check on df_v_valid_for_analysis_only) ---
        logging.debug("Executing V Analysis (Chapter 6 - Skill Override)...")
        # Use df_v_valid_for_analysis_only for these summary calculations
        exempted_skills = calculate_skill_exemption_status(df_v_valid_for_analysis_only)
        ch6_override_results = calculate_skill_override(df_v_valid_for_analysis_only)
        ch6_results = {**ch6_override_results, 'exempted_skills': exempted_skills}
        v_diagnosis_results['chapter_6'] = ch6_results
        logging.debug(f"Finished Chapter 6 V skill override/exemption analysis. Exempted: {exempted_skills}")

        # --- Generate Recommendations & Summary Report (Chapter 7 & 8) --- #
        # Pass the df *after* Ch3 processing to recommendation generator
        # Recommendations might be based on analysis of valid data, or overall patterns.
        # For now, assume generate_v_recommendations uses v_diagnosis_results (which contains summaries from valid data)
        # and potentially the full df_v_processed if needed.
        v_recommendations = generate_v_recommendations(v_diagnosis_results, exempted_skills) # exempted_skills is from valid data
        v_diagnosis_results['chapter_7'] = v_recommendations

        # Generate report using results.
        # generate_v_summary_report uses v_diagnosis_results which now includes df_v_processed in chapter_3.
        v_report_content = generate_v_summary_report(v_diagnosis_results)

        # --- Prepare Final DataFrame for Return ---
        df_v_final = df_v_processed.copy() # Start with the fully processed df

        # === DEBUG START ===
        logging.debug("[V Diag - Before Return] Final df_v_final overtime count: %s", df_v_final['overtime'].sum() if 'overtime' in df_v_final.columns else 'N/A')
        logging.debug("[V Diag - Before Return] Final df_v_final overtime head:\n%s", df_v_final[['question_position', 'overtime', 'is_invalid', 'time_performance_category']].head().to_string() if 'overtime' in df_v_final.columns else "Overtime col missing")
        # === DEBUG END ===

        # --- Drop English column AFTER report is generated ---
        if 'diagnostic_params' in df_v_final.columns:
            try:
                df_v_final.drop(columns=['diagnostic_params'], inplace=True, errors='ignore')
            except KeyError:
                pass # Ignore if already dropped

        # --- Ensure Subject Column ---
        if 'Subject' not in df_v_final.columns or df_v_final['Subject'].isnull().any() or (df_v_final['Subject'] != 'V').any():
            df_v_final['Subject'] = 'V'
        else: # Ensure it's 'V' if column exists but has mixed/wrong values
            df_v_final['Subject'] = 'V'

        logging.debug("Verbal Diagnosis Complete.")

        # No longer need to merge 'is_invalid' or 'is_manually_invalid' back,
        # as df_v_processed (and thus df_v_final) always contained the correct 'is_invalid' status.
        # Ensure 'is_invalid' is bool type for consistency
        df_v_final['is_invalid'] = df_v_final['is_invalid'].astype(bool)
            
        # ------ Check if the count matches the expected (QA safety) ------
        final_invalid_count_in_df = df_v_final['is_invalid'].sum() if 'is_invalid' in df_v_final.columns else 0
        if final_invalid_count_in_df != num_invalid_v_total:
            # logging.warning(f"V科診斷: 最終返回數據集中無效項數量 ({final_invalid_count_in_df}) 與初始記錄 ({num_invalid_v_total}) 不符。") # REMOVED by AI
            pass # Keep count check but remove excessive logging
        else:
            # logging.info(f"V科診斷: 最終返回數據集中確認包含 {final_invalid_count_in_df} 個無效項。") # REMOVED by AI
            pass # Keep count check but remove excessive logging

        # Return the final df AFTER dropping the English params col
        return v_diagnosis_results, v_report_content, df_v_final
    except Exception as e:
        logging.error(f"Error in run_v_diagnosis_processed: {e}", exc_info=True)
        return {}, t('v_diagnosis_error_message'), pd.DataFrame() 