import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Tuple

# # Basic logging configuration to ensure INFO messages are displayed # Removed by AI
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s') # Removed by AI

# Import from sibling modules within di_modules
from .constants import (
    MAX_ALLOWED_TIME_DI, TIME_PRESSURE_THRESHOLD_DI,
    OVERTIME_THRESHOLDS, 
    EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES,
    SUSPICIOUS_FAST_MULTIPLIER,
    INVALID_TIME_THRESHOLD_MINUTES
)
from .utils import (
    # _calculate_msr_metrics, # Removed import
    analyze_dimension, grade_difficulty_di
)
# Import only needed items from translation.py, or keep for backward compatibility
# from .translation import (
#     _translate_di # Only translation function needed directly in main logic?
# )
from .analysis import (
    diagnose_root_causes, observe_di_patterns, check_foundation_override_detailed
)
from .recommendations import generate_di_recommendations
from .reporting import generate_di_summary_report
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS
from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_first_third_average_time_per_type
# Add unified i18n system import
from gmat_diagnosis_app.i18n import translate as t

# Rename the main processing function for clarity within the module
def run_di_diagnosis(
    df_processed: pd.DataFrame,
    time_pressure_status: bool,
    avg_time_per_type: Optional[Dict[str, float]] = None,
    include_summaries: bool = False,
    include_individual_errors: bool = False,
    include_summary_report: bool = True
) -> Tuple[Dict, str, pd.DataFrame]:
    # --- FORCE LOGGING CHECK --- REMOVED by AI
    # logging.info("!!!!!! [DI Main Entry] Entering run_di_diagnosis_logic !!!!!")
    # try:
    #     logging.basicConfig(level=logging.INFO,
    #                         format='>>>> FORCE LOG CHECK %(asctime)s - %(levelname)s - %(message)s',
    #                         force=True)
    #     logging.info(">>>> [DI Main Entry] Forced basicConfig attempt executed.")
    # except TypeError:
    #      logging.basicConfig(level=logging.INFO,
    #                         format='>>>> FORCE LOG CHECK (noforce) %(asctime)s - %(levelname)s - %(message)s')
    #      logging.info(">>>> [DI Main Entry] Forced basicConfig (no-force) attempt executed.")
    # logging.info(f">>>> [DI Main Entry] run_di_diagnosis_logic called with di_time_pressure_status: {di_time_pressure_status}")
    # --- End FORCE LOGGING CHECK --- REMOVED by AI
    """
    DI診斷主入口函數
    
    Args:
        df_processed: 預處理後的DataFrame，包含is_invalid標記
        time_pressure_status: 時間壓力狀態布林值
        avg_time_per_type: 各題型平均時間字典，可選
        include_summaries: 是否包含詳細摘要數據
        include_individual_errors: 是否包含個別錯誤詳情
        include_summary_report: 是否生成文字摘要報告
        
    Returns:
        tuple: (診斷結果字典, 報告字串, 帶診斷標記的DataFrame)
    """
    di_diagnosis_results = {}
    report_str = t('report_generation_disabled')  # Use translation for error message
    df_to_return = pd.DataFrame() # Default empty DataFrame
    empty_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type',
                  'question_fundamental_skill', 'content_domain', 'Subject', 'is_invalid',
                  'overtime', 'suspiciously_fast', 'msr_group_id', 'msr_group_total_time',
                  'msr_reading_time', 'is_first_msr_q', 'is_sfe',
                  'time_performance_category', 'diagnostic_params_list']

    try: # --- Start Main Try Block ---
        if df_processed.empty:
            report_str = t('di_ai_analysis_unavailable')  # Use translation for no data message
            df_to_return = pd.DataFrame(columns=empty_cols)
            if 'Subject' not in df_to_return.columns:
                df_to_return['Subject'] = 'DI'
            # logging.info("[run_di_diagnosis_logic] Input DataFrame is empty.") # Removed by AI
            return {}, report_str, df_to_return

        df_di = df_processed.copy()
        
        # Initialize time_performance_category early on df_di
        if 'time_performance_category' not in df_di.columns:
            df_di['time_performance_category'] = t('Unknown') # Default, will be calculated
        else: # Ensure it handles empty strings if already present
            df_di['time_performance_category'] = df_di['time_performance_category'].replace({'': t('Unknown'), pd.NA: t('Unknown'), None: t('Unknown'), np.nan: t('Unknown')})

        # 添加調試日誌：記錄原始數據
        total_questions = len(df_di)
        # logging.info(f"[DI數據追蹤] 原始數據總題數: {total_questions}")
        if 'is_correct' in df_di.columns:
            correct_count = df_di['is_correct'].sum()
            wrong_count = total_questions - correct_count
            # logging.info(f"[DI數據追蹤] 原始數據答對題數: {correct_count}, 答錯題數: {wrong_count}")
        if 'is_invalid' in df_di.columns:
            invalid_count = df_di['is_invalid'].sum()
            valid_count = total_questions - invalid_count
            # logging.info(f"[DI數據追蹤] 原始數據有效題數: {valid_count}, 無效題數: {invalid_count}")
            
        # logging.debug(f"[run_di_diagnosis_logic] Starting diagnosis. Input df shape: {df_di.shape}")

        # --- Chapter 0: Derivative Data Calculation & Basic Prep ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 0: Basic Prep")
        df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
        if 'question_position' not in df_di.columns: df_di['question_position'] = range(len(df_di))
        else: df_di['question_position'] = pd.to_numeric(df_di['question_position'], errors='coerce')
        if 'is_correct' not in df_di.columns: df_di['is_correct'] = True
        else: df_di['is_correct'] = df_di['is_correct'].astype(bool)
        if 'question_type' not in df_di.columns: df_di['question_type'] = 'Unknown Type'
        if 'msr_group_id' not in df_di.columns:
            logging.warning("'msr_group_id' column missing. MSR metrics will be NaN.")
            df_di['msr_group_id'] = np.nan # Ensure column exists even if empty
        if 'is_invalid' not in df_di.columns:
            df_di['is_invalid'] = False
            
        # 添加調試日誌：數據類型轉換後的狀態
        # logging.info(f"[DI數據追蹤] 數據類型轉換後 - 總題數: {len(df_di)}, 答對題數: {df_di['is_correct'].sum()}, 答錯題數: {(~df_di['is_correct']).sum()}, 無效題數: {df_di['is_invalid'].sum()}")

        # df_di = _calculate_msr_metrics(df_di) # Removed call, MSR metrics are now expected from preprocessor
        # logging.debug(f"[run_di_diagnosis_logic] After _calculate_msr_metrics, df shape: {df_di.shape}") # Updated name

        # --- Chapter 1: Time Strategy & Validity ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 1: Time Strategy & Validity")
        total_test_time_di = df_di['question_time'].sum(skipna=True) # Ensure NaNs are skipped
        time_diff = MAX_ALLOWED_TIME_DI - total_test_time_di

        # --- 添加識別異常快速作答的邏輯（核心邏輯文件第一章）---
        # 初始化 suspiciously_fast 列
        df_di['suspiciously_fast'] = False # This column might be redundant after full invalid logic
        
        # 計算考試前三分之一各題型平均時間 (first_third_average_time_per_type)
        first_third_average_time_per_type = calculate_first_third_average_time_per_type(
            df_di, ['DS', 'TPA', 'MSR', 'GT', 'Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table']
        )

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
        if time_pressure_status: # 文檔標準：僅在 time_pressure == True 時執行
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

                        # 標準 1 (疑似放棄) - Independent check
                        if pd.notna(q_time) and q_time < INVALID_TIME_THRESHOLD_MINUTES: # 0.5 minutes
                            abnormally_fast = True

                        # 標準 2 (絕對倉促) - Independent check  
                        if pd.notna(q_time) and q_time < 1.0: # 1.0 minutes (use EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES)
                            abnormally_fast = True
                        
                        # 標準 3-5 (相對單題倉促 - DS, TPA, GT) - Independent check
                        if q_type in ['DS', 'TPA', 'GT', 'Data Sufficiency', 'Two-part analysis', 'Graph and Table']: # Handle variations in q_type names
                            # Map variations to standard names for lookup
                            standard_q_type = q_type
                            if q_type == 'Data Sufficiency': standard_q_type = 'DS'
                            elif q_type == 'Two-part analysis': standard_q_type = 'TPA'
                            elif q_type == 'Graph and Table': standard_q_type = 'GT'
                                
                            avg_time = first_third_average_time_per_type.get(standard_q_type)
                            if avg_time is not None and pd.notna(avg_time) and pd.notna(q_time) and q_time < (avg_time * SUSPICIOUS_FAST_MULTIPLIER):
                                abnormally_fast = True
                        
                        # 標準 6 (相對題組倉促 - MSR) - Independent check
                        if q_type in ['MSR', 'Multi-source reasoning']:
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
                # logging.debug(f"[run_di_diagnosis_logic] Initializing 'diagnostic_params'. df_di shape: {df_di.shape}, length of list: {len(df_di)}")
                df_di['diagnostic_params'] = [[] for _ in range(len(df_di))]
            except Exception as e:
                logging.error(f"Error initializing 'diagnostic_params': {e}", exc_info=True)
                raise e
        else:
            try:
                # logging.debug(f"[run_di_diagnosis_logic] Ensuring 'diagnostic_params' is list. df_di shape: {df_di.shape}")
                df_di['diagnostic_params'] = df_di['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, set, tuple)) else [])
            except Exception as e:
                logging.error(f"Error ensuring 'diagnostic_params' is list: {e}", exc_info=True)
                raise e

        # Add invalid tag
        final_invalid_mask_di = df_di['is_invalid']
        if final_invalid_mask_di.any():
            # logging.debug(f"[run_di_diagnosis_logic] Updating 'diagnostic_params' for invalid rows in df_di. df_di shape: {df_di.shape}, number invalid: {final_invalid_mask_di.sum()}")
            for idx in df_di.index[final_invalid_mask_di]:
                try:
                    current_list = df_di.loc[idx, 'diagnostic_params']
                    if t('di_invalid_data_tag') not in current_list:
                        current_list.append(t('di_invalid_data_tag'))
                        df_di.loc[idx, 'diagnostic_params'] = current_list
                except Exception as e:
                    logging.error(f"Error updating diagnostic_params for invalid row at index {idx}: {e}", exc_info=True)

        # --- Mark Overtime (Vectorized Approach) on df_di ---
        try:
            # logging.debug(f"[run_di_diagnosis_logic] Initializing 'overtime' column in df_di. df_di shape: {df_di.shape}")
            df_di['overtime'] = False
        except Exception as e:
            logging.error(f"Error initializing 'overtime': {e}", exc_info=True)
            raise e

        thresholds = OVERTIME_THRESHOLDS[time_pressure_status]
        valid_mask = ~df_di['is_invalid']
        
        # Non-MSR Overtime
        tpa_mask = valid_mask & ((df_di['question_type'] == 'Two-part analysis') | (df_di['question_type'] == 'TPA'))
        tpa_over_mask = tpa_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['TPA'])
        gt_mask = valid_mask & ((df_di['question_type'] == 'Graph and Table') | (df_di['question_type'] == 'GT'))
        gt_over_mask = gt_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['GT'])
        ds_mask = valid_mask & ((df_di['question_type'] == 'Data Sufficiency') | (df_di['question_type'] == 'DS'))
        ds_over_mask = ds_mask & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['DS'])

        # MSR Overtime - Add safety checks for MSR columns
        msr_mask = valid_mask & ((df_di['question_type'] == 'Multi-source reasoning') | (df_di['question_type'] == 'MSR'))
        
        # Check if MSR columns exist before using them
        msr_group_over = pd.Series(False, index=df_di.index)
        msr_reading_over = pd.Series(False, index=df_di.index)
        msr_adj_first_over = pd.Series(False, index=df_di.index)
        msr_non_first_over = pd.Series(False, index=df_di.index)
        
        if 'msr_group_total_time' in df_di.columns and msr_mask.any():
            msr_group_over = msr_mask & df_di['msr_group_total_time'].notna() & (df_di['msr_group_total_time'] > thresholds['MSR_GROUP'])
        
        if 'msr_reading_time' in df_di.columns and 'is_first_msr_q' in df_di.columns and msr_mask.any():
            msr_reading_over = msr_mask & (~msr_group_over) & df_di['is_first_msr_q'] & df_di['msr_reading_time'].notna() & (df_di['msr_reading_time'] > thresholds['MSR_READING'])
            adj_time = df_di['question_time'] - df_di['msr_reading_time']
            # Fix the NoneType error by ensuring is_first_msr_q is boolean before using ~
            is_first_msr_q_bool = df_di['is_first_msr_q'].fillna(False).infer_objects(copy=False).astype(bool)
            msr_reading_over = msr_mask & (~msr_group_over) & is_first_msr_q_bool & df_di['msr_reading_time'].notna() & (df_di['msr_reading_time'] > thresholds['MSR_READING'])
            msr_adj_first_over = msr_mask & (~msr_group_over) & (~msr_reading_over) & is_first_msr_q_bool & df_di['msr_reading_time'].notna() & df_di['question_time'].notna() & adj_time.notna() & (adj_time > thresholds['MSR_SINGLE_Q'])
            msr_non_first_over = msr_mask & (~msr_group_over) & (~is_first_msr_q_bool) & df_di['question_time'].notna() & (df_di['question_time'] > thresholds['MSR_SINGLE_Q'])
        
        msr_over_mask = msr_group_over | msr_reading_over | msr_adj_first_over | msr_non_first_over
        
        overall_overtime_mask = tpa_over_mask | gt_over_mask | ds_over_mask | msr_over_mask
        df_di.loc[overall_overtime_mask, 'overtime'] = True
        # logging.debug(f"[run_di_diagnosis_logic] Overtime calculated. Count: {df_di['overtime'].sum()}")

        # Store Chapter 1 results
        di_diagnosis_results['chapter_1'] = {
            'total_test_time_minutes': total_test_time_di,
            'time_difference_minutes': time_diff,
            'time_pressure': time_pressure_status,
            'invalid_questions_excluded': num_invalid_questions_total,
            'overtime_thresholds_minutes': thresholds
        }

        # Use provided avg_time_per_type if available, otherwise calculate from data
        if avg_time_per_type and isinstance(avg_time_per_type, dict):
            avg_time_per_type_for_rules = avg_time_per_type.copy()
        else:
            # Calculate avg_time_per_type using filtered data as fallback
            avg_time_per_type_for_rules = {}
            if not df_di.empty and 'question_type' in df_di.columns:
                # Use valid data for calculation
                df_valid_calc = df_di[~df_di['is_invalid']]
                if not df_valid_calc.empty:
                    avg_time_per_type_for_rules = df_valid_calc.groupby('question_type')['question_time'].mean().to_dict()
        
        # Calculate max_correct_difficulty using VALID data
        max_correct_difficulty_per_combination_for_rules = pd.DataFrame()
        if not df_di.empty:
            if 'content_domain' in df_di.columns and 'question_difficulty' in df_di.columns:
                # Use valid data for calculation
                df_valid_calc = df_di[~df_di['is_invalid']]
                correct_rows_valid = df_valid_calc['is_correct'] == True
                if correct_rows_valid.any():
                    max_correct_difficulty_per_combination_for_rules = df_valid_calc[correct_rows_valid].groupby(
                        ['question_type', 'content_domain']
                    )['question_difficulty'].max().unstack(fill_value=-np.inf)

        # 添加時間壓力檢測標記（對所有數據進行檢測，不僅限於無效數據）
        # diagnose_root_causes will be called on the full df_di.
        # logging.debug("[run_di_diagnosis_logic] Chapter 3: Diagnose Root Causes")
        # Call the actual Chapter 3 logic first (always diagnose all rows)
        # df_di = _diagnose_root_causes(
        df_di, override_results = diagnose_root_causes(
            df_di, 
            avg_time_per_type_for_rules, 
            max_correct_difficulty_per_combination_for_rules, 
            OVERTIME_THRESHOLDS[time_pressure_status]
        )

        di_diagnosis_results['chapter_3'] = {
            'diagnosed_dataframe': df_di.copy(), # This df_di now has time_category for all and conditional SFE/params
            'avg_time_per_type_minutes': avg_time_per_type_for_rules, # Based on valid data
            'max_correct_difficulty': max_correct_difficulty_per_combination_for_rules.to_dict() if not max_correct_difficulty_per_combination_for_rules.empty else {} # Based on valid data
        }
        # logging.debug("[run_di_diagnosis_logic] Completed Chapter 3.")

        # --- Prepare df_di_filtered_for_analysis (used for summary and recommendations) ---
        df_di_filtered_for_analysis = df_di[~df_di['is_invalid']].copy()
        # 添加調試日誌：記錄篩選後用於分析的數據
        valid_count_filtered = len(df_di_filtered_for_analysis)
        correct_count_filtered = df_di_filtered_for_analysis['is_correct'].sum()
        wrong_count_filtered = valid_count_filtered - correct_count_filtered
        # logging.info(f"[DI數據追蹤] 篩選出的有效數據 (df_di_filtered_for_analysis created AFTER Ch3) - 有效題數: {valid_count_filtered}, 答對題數: {correct_count_filtered}, 答錯題數: {wrong_count_filtered}")
        # logging.info(f"[DI數據追蹤] 此df_di_filtered_for_analysis將用於生成部分匯總報告指標以及傳遞給建議生成器。")
        
        # Calculate overall metrics from the filtered data
        total_correct = df_di_filtered_for_analysis['is_correct'].sum()

        # --- Chapter 4: Special Pattern Observation (uses df_di_filtered_for_analysis or df_di as appropriate) ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 4: Special Patterns")
        # avg_times_ch3_for_ch4 was originally from diagnosed_dataframe.groupby. Now use avg_time_per_type_for_rules
        pattern_analysis_results = observe_di_patterns(df_di_filtered_for_analysis, avg_time_per_type_for_rules)
        di_diagnosis_results['chapter_4'] = pattern_analysis_results
        # logging.debug("[run_di_diagnosis_logic] Completed Chapter 4.")

        # --- Chapter 5: Special Foundation Override Check ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 5: Foundation Override Check")
        # Pass type_analysis to Chapter 5 for override decision
        type_analysis_ch2_for_ch5 = di_diagnosis_results.get('chapter_2', {}).get('by_type', {})
        override_analysis = check_foundation_override_detailed(df_di_filtered_for_analysis, type_analysis_ch2_for_ch5)
        di_diagnosis_results['chapter_5'] = override_analysis
        # logging.debug("[run_di_diagnosis_logic] Completed Chapter 5.")

        # --- Chapter 6: Recommendations ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 6: Recommendations")
        # Pass results from Chapters 2, 3, 5 to Chapter 6
        domain_tags_ch2_for_ch6 = di_diagnosis_results.get('chapter_2', {}).get('domain_comparison_tags', {})
        override_analysis_ch5_for_ch6 = di_diagnosis_results.get('chapter_5', {})

        recommendations = generate_di_recommendations(df_di_filtered_for_analysis, override_analysis_ch5_for_ch6, domain_tags_ch2_for_ch6, time_pressure=time_pressure_status)
        di_diagnosis_results['chapter_6'] = {'recommendations_list': recommendations}
        # logging.debug("[run_di_diagnosis_logic] Completed Chapter 6.")

        # --- Chapter 7: Summary Report Generation ---
        # logging.debug("[run_di_diagnosis_logic] Chapter 7: Summary Report")
        # Update chapter 3's dataframe in results for the report generator, ensuring it's the full df_di
        di_diagnosis_results['chapter_3']['diagnosed_dataframe'] = df_di.copy()

        # Generate summary report based on include_summary_report parameter
        if include_summary_report:
            report_str = generate_di_summary_report(di_diagnosis_results)
        else:
            report_str = t('report_generation_disabled')  # Use translation for disabled message
        # logging.debug("[run_di_diagnosis_logic] Completed Chapter 7.")
        
        # Logging for final returned data (df_di will be the base for df_to_return)
        if df_to_return.empty:
            df_to_return = df_di.copy()
        final_total = len(df_to_return)
        final_valid = len(df_to_return[~df_to_return['is_invalid']])
        final_correct = df_to_return[df_to_return['is_correct']].shape[0]
        final_valid_correct = df_to_return[(df_to_return['is_correct']) & (~df_to_return['is_invalid'])].shape[0]
        final_valid_wrong = final_valid - final_valid_correct
        # logging.info(f"[DI數據追蹤] 最終返回數據 - 總題數: {final_total}, 有效題數: {final_valid}, 有效題中答對: {final_valid_correct}, 有效題中答錯: {final_valid_wrong}")

        # --- Final DataFrame Preparation ---
        # logging.debug("[run_di_diagnosis_logic] Final DataFrame Preparation")
        # df_to_return starts as a copy of the fully processed df_di
        df_to_return = df_di.copy()

        # No complex merge needed if diagnostic_params, is_sfe, time_performance_category were correctly set on df_di by diagnose_root_causes

        if 'diagnostic_params' in df_to_return.columns:
            df_to_return['diagnostic_params'] = df_to_return['diagnostic_params'].apply(
                lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x] if isinstance(x, str) else [])
            )
            df_to_return['diagnostic_params_list_chinese'] = df_to_return['diagnostic_params'].apply(
                lambda params_list: [t(param) for param in params_list] if isinstance(params_list, list) else []
            )
            if 'diagnostic_params' in df_to_return.columns: df_to_return = df_to_return.drop(columns=['diagnostic_params'])
            if 'diagnostic_params_list_chinese' in df_to_return.columns: df_to_return = df_to_return.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'})
        else:
            df_to_return['diagnostic_params_list'] = [[] for _ in range(len(df_to_return))]

        if 'time_performance_category' not in df_to_return.columns:
            df_to_return['time_performance_category'] = t('Unknown')
        
        # Ensure `time_performance_category` for invalid rows is NOT overwritten to 'Invalid/Excluded' here.
        # It should retain the value calculated by diagnose_root_causes.
        # Fill NA or empty strings with 'Unknown' if diagnose_root_causes didn't assign a category.
        with pd.option_context('future.no_silent_downcasting', True):
            df_to_return['time_performance_category'] = df_to_return['time_performance_category'].replace({pd.NA: t('Unknown'), None: t('Unknown'), np.nan: t('Unknown'), '': t('Unknown')})
            df_to_return['time_performance_category'] = df_to_return['time_performance_category'].infer_objects(copy=False)
        
        if 'is_sfe' in df_to_return.columns:
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
        # Adjust fill_values for time_performance_category
        fill_values = {'is_sfe': False, 'time_performance_category': t('Unknown')} # Changed from 'Invalid/Excluded'
        with pd.option_context('future.no_silent_downcasting', True):
            for col in cols_to_fill_na:
                if col in df_to_return.columns:
                    fill_value = fill_values.get(col, t('Unknown'))
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

        # logging.debug(f"[run_di_diagnosis_logic] Final df_di shape before return: {df_to_return.shape}")
        # logging.debug(f"[run_di_diagnosis_logic] Columns: {df_to_return.columns.tolist()}")
        if 'diagnostic_params_list' in df_to_return.columns:
             # logging.debug(f"[run_di_diagnosis_logic] diagnostic_params_list head:\n{df_to_return['diagnostic_params_list'].head().to_string()}")
             pass
        else:
             # logging.debug("[run_di_diagnosis_logic] 'diagnostic_params_list' column not found before return.")
             pass

        # logging.debug(f"[run_di_diagnosis_logic] Diagnosis successful. Returning df shape: {df_to_return.shape}")
        return di_diagnosis_results, report_str, df_to_return

    except Exception as e: # --- Catch All Exceptions ---
        logging.error(f"Unhandled exception during DI diagnosis: {e}", exc_info=True)
        df_to_return = pd.DataFrame(columns=empty_cols)
        if 'Subject' not in df_to_return.columns:
            df_to_return['Subject'] = 'DI'
        return {}, t('di_diagnosis_error_message'), df_to_return 