import pandas as pd
import numpy as np
import logging

# Import from sibling modules within di_modules
from .constants import (
    MAX_ALLOWED_TIME_DI, TIME_PRESSURE_THRESHOLD_DI, INVALID_DATA_TAG_DI,
    INVALID_TIME_THRESHOLD_MINUTES, OVERTIME_THRESHOLDS, SUSPICIOUS_FAST_MULTIPLIER
)
from .utils import (
    # _calculate_msr_metrics, # Removed import
    _analyze_dimension, _grade_difficulty_di
)
from .translation import (
    _translate_di # Only translation function needed directly in main logic?
)
from .chapter_logic import (
    _diagnose_root_causes, _observe_di_patterns, _check_foundation_override, _generate_di_recommendations
)
from .report_generation import _generate_di_summary_report

# Rename the main processing function for clarity within the module
def run_di_diagnosis_logic(df_di_processed, di_time_pressure_status):
    """
    Core diagnostic logic for Data Insights, moved from di_diagnostic.py.
    Assumes 'is_invalid' column reflects the final status after user review.

    Args:
        df_di_processed (pd.DataFrame): DataFrame with DI responses, preprocessed with 'is_invalid'.
        di_time_pressure_status (bool): Time pressure status for DI.

    Returns:
        dict: A dictionary containing the results of the DI diagnosis, structured by chapter.
        str: A string containing the summary report for the DI section.
        pd.DataFrame: The processed DI DataFrame with added diagnostic columns.
    """
    di_diagnosis_results = {}
    report_str = "Data Insights (DI) 診斷過程中發生錯誤。"
    df_to_return = pd.DataFrame() # Default empty DataFrame
    empty_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type',
                  'question_fundamental_skill', 'content_domain', 'Subject', 'is_invalid',
                  'overtime', 'suspiciously_fast', 'msr_group_id', 'msr_group_total_time',
                  'msr_reading_time', 'is_first_msr_q', 'is_sfe',
                  'time_performance_category', 'diagnostic_params_list']

    try: # --- Start Main Try Block ---
        if df_di_processed.empty:
            report_str = "Data Insights (DI) 部分無數據可供診斷。"
            df_to_return = pd.DataFrame(columns=empty_cols)
            if 'Subject' not in df_to_return.columns:
                df_to_return['Subject'] = 'DI'
            logging.info("[run_di_diagnosis_logic] Input DataFrame is empty.")
            return {}, report_str, df_to_return

        df_di = df_di_processed.copy()
        
        # 添加調試日誌：記錄原始數據
        total_questions = len(df_di)
        logging.info(f"[DI數據追蹤] 原始數據總題數: {total_questions}")
        if 'is_correct' in df_di.columns:
            correct_count = df_di['is_correct'].sum()
            wrong_count = total_questions - correct_count
            logging.info(f"[DI數據追蹤] 原始數據答對題數: {correct_count}, 答錯題數: {wrong_count}")
        if 'is_invalid' in df_di.columns:
            invalid_count = df_di['is_invalid'].sum()
            valid_count = total_questions - invalid_count
            logging.info(f"[DI數據追蹤] 原始數據有效題數: {valid_count}, 無效題數: {invalid_count}")
            
        logging.debug(f"[run_di_diagnosis_logic] Starting diagnosis. Input df shape: {df_di.shape}")

        # --- Chapter 0: Derivative Data Calculation & Basic Prep ---
        logging.debug("[run_di_diagnosis_logic] Chapter 0: Basic Prep")
        df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
        if 'question_position' not in df_di.columns: df_di['question_position'] = range(len(df_di))
        else: df_di['question_position'] = pd.to_numeric(df_di['question_position'], errors='coerce')
        if 'is_correct' not in df_di.columns: df_di['is_correct'] = True
        else: df_di['is_correct'] = df_di['is_correct'].astype(bool)
        if 'question_type' not in df_di.columns: df_di['question_type'] = 'Unknown Type'
        if 'msr_group_id' not in df_di.columns:
            logging.warning("[run_di_diagnosis_logic] 'msr_group_id' column missing. MSR metrics will be NaN.")
            df_di['msr_group_id'] = np.nan # Ensure column exists even if empty
        if 'is_invalid' not in df_di.columns:
            df_di['is_invalid'] = False
            
        # 添加調試日誌：數據類型轉換後的狀態
        logging.info(f"[DI數據追蹤] 數據類型轉換後 - 總題數: {len(df_di)}, 答對題數: {df_di['is_correct'].sum()}, 答錯題數: {(~df_di['is_correct']).sum()}, 無效題數: {df_di['is_invalid'].sum()}")

        # df_di = _calculate_msr_metrics(df_di) # Removed call, MSR metrics are now expected from preprocessor
        # logging.debug(f"[run_di_diagnosis_logic] After _calculate_msr_metrics, df shape: {df_di.shape}") # Updated name

        # --- Chapter 1: Time Strategy & Validity ---
        logging.debug("[run_di_diagnosis_logic] Chapter 1: Time Strategy & Validity")
        total_test_time_di = df_di['question_time'].sum(skipna=True) # Ensure NaNs are skipped
        time_diff = MAX_ALLOWED_TIME_DI - total_test_time_di

        # --- 添加識別異常快速作答的邏輯（核心邏輯文件第一章）---
        # 初始化 suspiciously_fast 列
        df_di['suspiciously_fast'] = False # This column might be redundant after full invalid logic
        
        # 計算考試前三分之一各題型平均時間 (first_third_average_time_per_type)
        first_third_average_time_per_type = {}
        if 'question_position' in df_di.columns and 'question_time' in df_di.columns and 'question_type' in df_di.columns:
            positions = df_di['question_position'].sort_values().unique()
            if len(positions) > 0: # Ensure positions is not empty
                first_third_q_count = max(1, len(positions) // 3)
                first_third_positions = positions[:first_third_q_count]
                
                first_third_df = df_di[df_di['question_position'].isin(first_third_positions)].copy() # Use .copy() to avoid SettingWithCopyWarning
                if not first_third_df.empty:
                    first_third_average_time_per_type = first_third_df.groupby('question_type')['question_time'].mean().to_dict()

        # 舊的 suspiciously_fast 邏輯 (基於全局平均) 可以被新的 is_invalid 邏輯覆蓋或移除
        # For now, we comment it out as the new invalid logic is more comprehensive
        # if 'question_position' in df_di.columns and 'question_time' in df_di.columns:
        #     positions = df_di['question_position'].sort_values().unique()
        #     first_third_positions = positions[:max(1, len(positions) // 3)]
        #     first_third_mask = df_di['question_position'].isin(first_third_positions)
        #     first_third_avg_time = df_di.loc[first_third_mask, 'question_time'].mean()
        #     suspicious_fast_threshold = first_third_avg_time * SUSPICIOUS_FAST_MULTIPLIER
        #     suspiciously_fast_mask = df_di['question_time'].notna() & (df_di['question_time'] < suspicious_fast_threshold)
        #     df_di.loc[suspiciously_fast_mask, 'suspiciously_fast'] = True
            
        # 核心邏輯：標記無效數據 (is_invalid)
        if di_time_pressure_status: # 文檔標準：僅在 time_pressure == True 時執行
            # 獲取所有題目位置
            all_positions_sorted = sorted(df_di['question_position'].unique())
            if len(all_positions_sorted) > 0: # Ensure all_positions_sorted is not empty
                # 確定題目總數的後三分之一起始位置
                num_total_questions = len(all_positions_sorted)
                last_third_start_index = num_total_questions - (num_total_questions // 3)
                # 獲取後三分之一的題目位置列表 (0-indexed for iloc, but positions themselves are values)
                last_third_positions_values = all_positions_sorted[last_third_start_index:]

                # 篩選出位於後三分之一的題目
                last_third_questions_df = df_di[df_di['question_position'].isin(last_third_positions_values)].copy() # Use .copy()

                if not last_third_questions_df.empty:
                    for index, row in last_third_questions_df.iterrows():
                        if df_di.loc[index, 'is_invalid']: # Skip if already marked as invalid by preprocessor
                            continue

                        q_time = row['question_time']
                        q_type = row['question_type']
                        
                        abnormally_fast = False

                        # 標準 1 (疑似放棄)
                        if pd.notna(q_time) and q_time < INVALID_TIME_THRESHOLD_MINUTES: # 0.5 minutes
                            abnormally_fast = True

                        # 標準 2 (絕對倉促)
                        if not abnormally_fast and pd.notna(q_time) and q_time < 1.0: # 1.0 minutes (use EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES)
                            abnormally_fast = True
                        
                        # 標準 3-5 (相對單題倉促 - DS, TPA, GT)
                        if not abnormally_fast and q_type in ['DS', 'TPA', 'GT', 'Data Sufficiency', 'Two-part analysis', 'Graph and Table']: # Handle variations in q_type names
                            # Map variations to standard names for lookup
                            standard_q_type = q_type
                            if q_type == 'Data Sufficiency': standard_q_type = 'DS'
                            elif q_type == 'Two-part analysis': standard_q_type = 'TPA'
                            elif q_type == 'Graph and Table': standard_q_type = 'GT'
                                
                            avg_time = first_third_average_time_per_type.get(standard_q_type)
                            if avg_time is not None and pd.notna(avg_time) and pd.notna(q_time) and q_time < (avg_time * SUSPICIOUS_FAST_MULTIPLIER):
                                abnormally_fast = True
                        
                        # 標準 6 (相對題組倉促 - MSR)
                        if not abnormally_fast and q_type in ['MSR', 'Multi-source reasoning']:
                            standard_q_type_msr = 'MSR' # Standardize for lookup
                            avg_time_msr = first_third_average_time_per_type.get(standard_q_type_msr)
                            group_total_time = row.get('msr_group_total_time')
                            num_q_in_group = row.get('msr_group_num_questions')

                            if avg_time_msr is not None and pd.notna(avg_time_msr) and \
                               pd.notna(group_total_time) and pd.notna(num_q_in_group) and num_q_in_group > 0 and \
                               group_total_time < (avg_time_msr * num_q_in_group * SUSPICIOUS_FAST_MULTIPLIER):
                                abnormally_fast = True

                        if abnormally_fast:
                            df_di.loc[index, 'is_invalid'] = True
                            # logging.debug(f"Marked question pos {row['question_position']} as invalid due to abnormal fast response.")
        
        num_invalid_questions_total = df_di['is_invalid'].sum()
        di_diagnosis_results['invalid_count'] = num_invalid_questions_total

        # Initialize diagnostic_params if needed
        if 'diagnostic_params' not in df_di.columns:
            try:
                logging.debug(f"[run_di_diagnosis_logic] Initializing 'diagnostic_params'. df_di shape: {df_di.shape}, length of list: {len(df_di)}")
                df_di['diagnostic_params'] = [[] for _ in range(len(df_di))]
            except Exception as e:
                logging.error(f"[run_di_diagnosis_logic] Error initializing 'diagnostic_params': {e}", exc_info=True)
                raise e
        else:
            try:
                logging.debug(f"[run_di_diagnosis_logic] Ensuring 'diagnostic_params' is list. df_di shape: {df_di.shape}")
                df_di['diagnostic_params'] = df_di['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, set, tuple)) else [])
            except Exception as e:
                logging.error(f"[run_di_diagnosis_logic] Error ensuring 'diagnostic_params' is list: {e}", exc_info=True)
                raise e

        # Add invalid tag
        final_invalid_mask_di = df_di['is_invalid']
        if final_invalid_mask_di.any():
            logging.debug(f"[run_di_diagnosis_logic] Updating 'diagnostic_params' for invalid rows. df_di shape: {df_di.shape}, number invalid: {final_invalid_mask_di.sum()}")
            for idx in df_di.index[final_invalid_mask_di]:
                try:
                    current_list = df_di.loc[idx, 'diagnostic_params']
                    if not isinstance(current_list, list): current_list = []
                    if INVALID_DATA_TAG_DI not in current_list:
                        current_list.append(INVALID_DATA_TAG_DI)
                    df_di.loc[idx, 'diagnostic_params'] = current_list
                except Exception as e:
                    logging.error(f"[run_di_diagnosis_logic] Error updating 'diagnostic_params' for invalid row index {idx}: {e}", exc_info=True)
                    continue

        # --- Mark Overtime (Vectorized Approach) ---
        try:
            logging.debug(f"[run_di_diagnosis_logic] Initializing 'overtime' column. df_di shape: {df_di.shape}")
            df_di['overtime'] = False
        except Exception as e:
            logging.error(f"[run_di_diagnosis_logic] Error initializing 'overtime': {e}", exc_info=True)
            raise e

        thresholds = OVERTIME_THRESHOLDS[di_time_pressure_status]
        valid_mask = ~df_di['is_invalid']
        
        # Non-MSR Overtime
        tpa_mask = valid_mask & ((df_di['question_type'] == 'Two-part analysis') | (df_di['question_type'] == 'TPA'))
        tpa_over_mask = tpa_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['TPA'])
        gt_mask = valid_mask & ((df_di['question_type'] == 'Graph and Table') | (df_di['question_type'] == 'GT'))
        gt_over_mask = gt_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['GT'])
        ds_mask = valid_mask & ((df_di['question_type'] == 'Data Sufficiency') | (df_di['question_type'] == 'DS'))
        ds_over_mask = ds_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['DS'])

        # MSR Overtime
        msr_mask = valid_mask & ((df_di['question_type'] == 'Multi-source reasoning') | (df_di['question_type'] == 'MSR'))
        msr_group_over = msr_mask & df_di['msr_group_total_time'].notna() & (df_di['msr_group_total_time'] > thresholds['MSR_GROUP'])
        msr_reading_over = msr_mask & (~msr_group_over) & df_di['is_first_msr_q'] & df_di['msr_reading_time'].notna() & (df_di['msr_reading_time'] > thresholds['MSR_READING'])
        adj_time = df_di['question_time'] - df_di['msr_reading_time']
        msr_adj_first_over = msr_mask & (~msr_group_over) & (~msr_reading_over) & df_di['is_first_msr_q'] & df_di['msr_reading_time'].notna() & df_di['question_time'].notna() & adj_time.notna() & (adj_time > thresholds['MSR_SINGLE_Q'])
        msr_non_first_over = msr_mask & (~msr_group_over) & (~df_di['is_first_msr_q']) & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['MSR_SINGLE_Q'])
        msr_over_mask = msr_group_over | msr_reading_over | msr_adj_first_over | msr_non_first_over
        
        overall_overtime_mask = tpa_over_mask | gt_over_mask | ds_over_mask | msr_over_mask
        df_di.loc[overall_overtime_mask, 'overtime'] = True
        logging.debug(f"[run_di_diagnosis_logic] Overtime calculated. Count: {df_di['overtime'].sum()}")

        # Store Chapter 1 results
        di_diagnosis_results['chapter_1'] = {
            'total_test_time_minutes': total_test_time_di,
            'time_difference_minutes': time_diff,
            'time_pressure': di_time_pressure_status,
            'invalid_questions_excluded': num_invalid_questions_total,
            'overtime_thresholds_minutes': thresholds
        }

        # Create filtered dataset
        df_di_filtered = df_di[~df_di['is_invalid']].copy()
        
        # 添加調試日誌：篩選有效數據後的狀態
        valid_total = len(df_di_filtered)
        valid_correct = df_di_filtered['is_correct'].sum()
        valid_wrong = valid_total - valid_correct
        logging.info(f"[DI數據追蹤] 篩選有效數據後 - 有效題數: {valid_total}, 答對題數: {valid_correct}, 答錯題數: {valid_wrong}")
        logging.info(f"[DI數據追蹤] 這些數據將用於生成報告")
        
        logging.debug(f"[run_di_diagnosis_logic] Created df_di_filtered. Shape: {df_di_filtered.shape}")

        # --- Chapter 2: Multidimensional Performance Analysis ---
        logging.debug("[run_di_diagnosis_logic] Chapter 2: Performance Analysis")
        domain_analysis = {}
        type_analysis = {}
        difficulty_analysis = {}
        domain_comparison_tags = {
            'poor_math_related': False, 'slow_math_related': False,
            'poor_non_math_related': False, 'slow_non_math_related': False,
            'significant_diff_error': False, 'significant_diff_overtime': False
        }

        if not df_di_filtered.empty:
            if 'content_domain' in df_di_filtered.columns:
                domain_analysis = _analyze_dimension(df_di_filtered, 'content_domain')
                math_metrics = domain_analysis.get('Math Related', {})
                non_math_metrics = domain_analysis.get('Non-Math Related', {})
                math_errors = math_metrics.get('errors', 0)
                non_math_errors = non_math_metrics.get('errors', 0)
                math_overtime = math_metrics.get('overtime', 0)
                non_math_overtime = non_math_metrics.get('overtime', 0)

                if abs(math_errors - non_math_errors) >= 2:
                    domain_comparison_tags['significant_diff_error'] = True
                    domain_comparison_tags['poor_math_related'] = math_errors > non_math_errors
                    domain_comparison_tags['poor_non_math_related'] = non_math_errors > math_errors

                if abs(math_overtime - non_math_overtime) >= 2:
                     domain_comparison_tags['significant_diff_overtime'] = True
                     domain_comparison_tags['slow_math_related'] = math_overtime > non_math_overtime
                     domain_comparison_tags['slow_non_math_related'] = non_math_overtime > math_overtime

            if 'question_type' in df_di_filtered.columns:
                type_analysis = _analyze_dimension(df_di_filtered, 'question_type')

            if 'question_difficulty' in df_di_filtered.columns:
                df_di_filtered['difficulty_grade'] = df_di_filtered['question_difficulty'].apply(_grade_difficulty_di)
                difficulty_analysis = _analyze_dimension(df_di_filtered, 'difficulty_grade')

        di_diagnosis_results['chapter_2'] = {
            'by_domain': domain_analysis,
            'by_type': type_analysis,
            'by_difficulty': difficulty_analysis,
            'domain_comparison_tags': domain_comparison_tags
        }
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 2.")

        # --- Chapter 3: Root Cause Diagnosis ---
        logging.debug("[run_di_diagnosis_logic] Chapter 3: Root Cause Diagnosis")
        if not df_di_filtered.empty and 'question_type' in df_di_filtered.columns:
            avg_time_per_type = df_di_filtered.groupby('question_type')['question_time'].mean().to_dict()
            max_correct_difficulty_per_combination = pd.DataFrame()
            if 'content_domain' in df_di_filtered.columns and 'question_difficulty' in df_di_filtered.columns:
                 correct_rows = df_di_filtered['is_correct'] == True
                 if correct_rows.any():
                     max_correct_difficulty_per_combination = df_di_filtered[correct_rows].groupby(
                         ['question_type', 'content_domain']
                     )['question_difficulty'].max().unstack(fill_value=-np.inf)

            if 'time_performance_category' not in df_di_filtered.columns:
                df_di_filtered['time_performance_category'] = 'Unknown'

            df_di_filtered = _diagnose_root_causes(df_di_filtered, avg_time_per_type, max_correct_difficulty_per_combination, thresholds)

            di_diagnosis_results['chapter_3'] = {
                'diagnosed_dataframe': df_di_filtered.copy(),
                'avg_time_per_type_minutes': avg_time_per_type,
                'max_correct_difficulty': max_correct_difficulty_per_combination.to_dict() if not max_correct_difficulty_per_combination.empty else {}
            }
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 3.")

        # --- Chapter 4: Special Pattern Observation ---
        logging.debug("[run_di_diagnosis_logic] Chapter 4: Special Patterns")
        avg_times_ch3 = di_diagnosis_results.get('chapter_3', {}).get('avg_time_per_type_minutes', {})
        df_ch3_diagnosed = di_diagnosis_results['chapter_3']['diagnosed_dataframe']
        df_for_ch4 = df_ch3_diagnosed.copy()
        pattern_analysis_results = _observe_di_patterns(df_for_ch4, avg_times_ch3)
        di_diagnosis_results['chapter_4'] = pattern_analysis_results
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 4.")

        # --- Chapter 5: Foundation Ability Override Rule ---
        logging.debug("[run_di_diagnosis_logic] Chapter 5: Override Rule")
        type_analysis_ch2 = di_diagnosis_results.get('chapter_2', {}).get('by_type', {})
        override_analysis = _check_foundation_override(df_for_ch4, type_analysis_ch2)
        di_diagnosis_results['chapter_5'] = override_analysis
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 5.")

        # --- Chapter 6: Practice Planning & Recommendations ---
        logging.debug("[run_di_diagnosis_logic] Chapter 6: Recommendations")
        diagnosed_df_ch4_ch5 = df_for_ch4
        domain_tags_ch2 = di_diagnosis_results.get('chapter_2', {}).get('domain_comparison_tags', {})
        override_analysis_ch5 = di_diagnosis_results.get('chapter_5', {})

        recommendations = []
        if not diagnosed_df_ch4_ch5.empty:
            recommendations = _generate_di_recommendations(diagnosed_df_ch4_ch5, override_analysis_ch5, domain_tags_ch2)
        di_diagnosis_results['chapter_6'] = {'recommendations_list': recommendations}
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 6.")

        # --- Chapter 7: Summary Report Generation ---
        logging.debug("[run_di_diagnosis_logic] Chapter 7: Summary Report")
        di_diagnosis_results['chapter_3']['diagnosed_dataframe'] = diagnosed_df_ch4_ch5.copy()
        report_str = _generate_di_summary_report(di_diagnosis_results)
        logging.debug("[run_di_diagnosis_logic] Completed Chapter 7.")
        
        # 添加調試日誌：最終返回的數據統計
        if df_to_return.empty:
            df_to_return = df_di.copy()
        final_total = len(df_to_return)
        final_valid = len(df_to_return[~df_to_return['is_invalid']])
        final_correct = df_to_return[df_to_return['is_correct']].shape[0]
        final_valid_correct = df_to_return[(df_to_return['is_correct']) & (~df_to_return['is_invalid'])].shape[0]
        final_valid_wrong = final_valid - final_valid_correct
        logging.info(f"[DI數據追蹤] 最終返回數據 - 總題數: {final_total}, 有效題數: {final_valid}, 有效題中答對: {final_valid_correct}, 有效題中答錯: {final_valid_wrong}")

        # --- Final DataFrame Preparation ---
        logging.debug("[run_di_diagnosis_logic] Final DataFrame Preparation")
        df_base = df_di.copy()
        diagnostic_cols_to_merge = [] 
        if diagnosed_df_ch4_ch5 is not None and not diagnosed_df_ch4_ch5.empty:
            potential_cols = ['diagnostic_params', 'is_sfe', 'time_performance_category']
            diagnostic_cols_to_merge = [col for col in potential_cols if col in diagnosed_df_ch4_ch5.columns]

        if diagnostic_cols_to_merge:
            df_merged = pd.merge(
                df_base,
                diagnosed_df_ch4_ch5[diagnostic_cols_to_merge],
                left_index=True,
                right_index=True,
                how='left',
                suffixes=('', '_diag')
            )
            for col in diagnostic_cols_to_merge:
                diag_col = col + '_diag'
                if diag_col in df_merged.columns:
                    df_merged[col] = df_merged[diag_col]
                    df_merged.drop(columns=[diag_col], inplace=True)
            df_to_return = df_merged
        else:
            df_to_return = df_base

        if 'diagnostic_params' in df_to_return.columns:
            df_to_return['diagnostic_params'] = df_to_return['diagnostic_params'].apply(
                lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x] if isinstance(x, str) else [])
            )
            df_to_return['diagnostic_params_list_chinese'] = df_to_return['diagnostic_params'].apply(
                lambda params_list: _translate_di(params_list)
            )
            if 'diagnostic_params' in df_to_return.columns: df_to_return = df_to_return.drop(columns=['diagnostic_params'])
            if 'diagnostic_params_list_chinese' in df_to_return.columns: df_to_return = df_to_return.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'})
        else:
            df_to_return['diagnostic_params_list'] = [[] for _ in range(len(df_to_return))]

        if 'time_performance_category' not in df_to_return.columns:
            df_to_return['time_performance_category'] = 'Unknown'
        # 使用with context避免FutureWarning
        with pd.option_context('future.no_silent_downcasting', True):
            df_to_return['time_performance_category'] = df_to_return['time_performance_category'].replace({pd.NA: 'Unknown', None: 'Unknown', np.nan: 'Unknown', '': 'Unknown'})
            df_to_return['time_performance_category'] = df_to_return['time_performance_category'].infer_objects(copy=False)  # 允許推斷更合適的類型
        
        if 'is_invalid' in df_to_return.columns:
            invalid_mask = df_to_return['is_invalid'] == True
            if invalid_mask.any():
                df_to_return.loc[invalid_mask, 'time_performance_category'] = 'Invalid/Excluded'

        if 'is_sfe' in df_to_return.columns:
            # 使用with context避免FutureWarning
            with pd.option_context('future.no_silent_downcasting', True):
                df_to_return['is_sfe'] = df_to_return['is_sfe'].replace({pd.NA: False, None: False, np.nan: False})
                df_to_return['is_sfe'] = df_to_return['is_sfe'].infer_objects(copy=False)  # 允許推斷更合適的類型
            df_to_return['is_sfe'] = df_to_return['is_sfe'].astype(bool)
        else:
            df_to_return['is_sfe'] = False
        
        if 'Subject' not in df_to_return.columns:
            df_to_return['Subject'] = 'DI'
        else:
             df_to_return['Subject'] = 'DI'

        if 'overtime' not in df_to_return.columns:
            logging.warning("[run_di_diagnosis_logic] 'overtime' column missing before return. Initializing to False.")
            df_to_return['overtime'] = False

        cols_to_fill_na = ['is_sfe', 'time_performance_category']
        fill_values = {'is_sfe': False, 'time_performance_category': 'Invalid/Excluded'}
        # 使用with context避免FutureWarning
        with pd.option_context('future.no_silent_downcasting', True):
            for col in cols_to_fill_na:
                if col in df_to_return.columns:
                    fill_value = fill_values.get(col, 'Unknown')
                    # 使用替代方法避免FutureWarning
                    if fill_value == False:
                        df_to_return[col] = df_to_return[col].replace({pd.NA: False, None: False, np.nan: False})
                    else:
                        df_to_return[col] = df_to_return[col].replace({pd.NA: fill_value, None: fill_value, np.nan: fill_value, '': fill_value})
                    # 允許推斷更合適的類型
                    df_to_return[col] = df_to_return[col].infer_objects(copy=False)

        if 'is_invalid' in df_to_return.columns:
            df_to_return['is_invalid'] = df_to_return['is_invalid'].astype(bool)
        else:
            df_to_return['is_invalid'] = False

        logging.debug(f"[run_di_diagnosis_logic] Final df_di shape before return: {df_to_return.shape}")
        logging.debug(f"[run_di_diagnosis_logic] Columns: {df_to_return.columns.tolist()}")
        if 'diagnostic_params_list' in df_to_return.columns:
             logging.debug(f"[run_di_diagnosis_logic] diagnostic_params_list head:\n{df_to_return['diagnostic_params_list'].head().to_string()}")
        else:
             logging.debug("[run_di_diagnosis_logic] 'diagnostic_params_list' column not found before return.")

        logging.debug(f"[run_di_diagnosis_logic] Diagnosis successful. Returning df shape: {df_to_return.shape}")
        return di_diagnosis_results, report_str, df_to_return

    except Exception as e: # --- Catch All Exceptions ---
        logging.error(f"[run_di_diagnosis_logic] Unhandled exception during DI diagnosis: {e}", exc_info=True)
        df_to_return = pd.DataFrame(columns=empty_cols)
        if 'Subject' not in df_to_return.columns:
            df_to_return['Subject'] = 'DI'
        return {}, f"DI 診斷過程中發生未預期錯誤: {e}", df_to_return 