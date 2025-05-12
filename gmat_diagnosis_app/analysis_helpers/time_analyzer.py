# -*- coding: utf-8 -*-
"""Functions for analyzing time usage and calculating overtime."""
import pandas as pd
import warnings
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import THRESHOLDS
import logging # Re-added import
from gmat_diagnosis_app.constants.config import RC_GROUP_TARGET_TIME_ADJUSTMENT # 修改為絕對導入路徑

def _calculate_overtime_q(df_q, pressure, thresholds):
    """Calculates overtime mask for Q section."""
    threshold = thresholds['OVERTIME_PRESSURE'] if pressure else thresholds['OVERTIME_NO_PRESSURE']
    # Only calculate overtime for valid questions
    valid_rows_mask = df_q.get('is_invalid', pd.Series(False, index=df_q.index)) == False
    is_overtime = pd.Series(False, index=df_q.index) # Initialize with False
    # Apply overtime logic only to valid rows
    is_overtime.loc[valid_rows_mask] = (df_q.loc[valid_rows_mask, 'q_time_numeric'] > threshold)
    return is_overtime.fillna(False)

def _calculate_overtime_di(df_di, pressure, thresholds):
    """Calculates overtime mask for DI section."""
    overtime_mask = pd.Series(False, index=df_di.index)
    # Ensure q_time_numeric exists, if not, create it from question_time
    if 'q_time_numeric' not in df_di.columns:
        df_di['q_time_numeric'] = pd.to_numeric(df_di['question_time'], errors='coerce')

    overtime_thresholds_config = thresholds['OVERTIME'] # This is THRESHOLDS['DI']['OVERTIME']
    msr_target_times = overtime_thresholds_config.get('MSR_TARGET', {})
    msr_individual_threshold = overtime_thresholds_config.get('MSR_INDIVIDUAL_THRESHOLD', 1.5) # Default from DI Doc if not in JSON

    # --- MSR Group Overtime --- 
    msr_group_overtime = pd.Series(False, index=df_di.index)
    if 'msr_group_id' in df_di.columns and 'msr_group_total_time' in df_di.columns:
        # Iterate over unique group_ids for MSR questions to apply group logic once per group
        unique_msr_groups = df_di.loc[(df_di['question_type'] == 'MSR') & (df_di['msr_group_id'].notna()), 'msr_group_id'].unique()
        for group_id in unique_msr_groups:
            group_data = df_di[(df_di['msr_group_id'] == group_id) & (df_di['question_type'] == 'MSR')]
            if group_data.empty: continue

            actual_group_total_time = group_data['msr_group_total_time'].iloc[0] # Assuming consistent within group post-preprocessing
            target_time_for_group = msr_target_times.get('pressure' if pressure else 'no_pressure', 6.0 if pressure else 7.0) # Default from DI Doc

            if actual_group_total_time > target_time_for_group:
                msr_group_overtime.loc[group_data.index] = True
    else:
        warnings.warn("DI overtime: Missing 'msr_group_id' or 'msr_group_total_time' column. Cannot calculate MSR group overtime.", UserWarning, stacklevel=3)

    # --- MSR Individual Question Overtime ---
    msr_individual_overtime = pd.Series(False, index=df_di.index)
    msr_mask_for_individual = (df_di['question_type'] == 'MSR')
    if msr_mask_for_individual.any() and 'msr_reading_time' in df_di.columns and 'msr_group_id' in df_di.columns:
        df_di['adjusted_msr_time'] = df_di['q_time_numeric']
        # msr_reading_time is non-zero ONLY for the first question of each group (from di_preprocessor)
        first_q_msr_mask = msr_mask_for_individual & df_di['msr_group_id'].notna() & (df_di['msr_reading_time'] != 0)
        df_di.loc[first_q_msr_mask, 'adjusted_msr_time'] = df_di.loc[first_q_msr_mask, 'q_time_numeric'] - df_di.loc[first_q_msr_mask, 'msr_reading_time']
        
        is_msr_ind_overtime = (df_di['adjusted_msr_time'] > msr_individual_threshold).fillna(False)
        msr_individual_overtime.loc[msr_mask_for_individual & is_msr_ind_overtime] = True
    # else: warnings.warn for missing msr_reading_time could be added if strict notification is needed.

    # --- Combine MSR Overtime flags ---
    final_msr_overtime = msr_group_overtime | msr_individual_overtime
    overtime_mask.loc[df_di['question_type'] == 'MSR'] = final_msr_overtime[df_di['question_type'] == 'MSR']

    # --- Non-MSR Question Types Overtime (DS, TPA, GT) ---
    for q_type, type_thresholds_map in overtime_thresholds_config.items():
        if q_type in ['MSR_TARGET', 'MSR_INDIVIDUAL_THRESHOLD']: continue # Skip MSR specific config keys handled above
        
        type_mask = (df_di['question_type'] == q_type)
        if not type_mask.any(): continue
        
        # Ensure type_thresholds_map is a dict (e.g., {'pressure': 2.0, 'no_pressure': 2.5})
        if isinstance(type_thresholds_map, dict):
            threshold_value = type_thresholds_map.get('pressure' if pressure else 'no_pressure')
            if threshold_value is not None:
                is_type_overtime = (df_di['q_time_numeric'] > threshold_value).fillna(False)
                overtime_mask.loc[type_mask & is_type_overtime] = True
            # else: warnings.warn for missing pressure/no_pressure key in threshold_value
        # else: warnings.warn for type_thresholds_map not being a dict for a given q_type

    if 'adjusted_msr_time' in df_di.columns: # Clean up temp column from df_di (which is a copy)
        df_di.drop(columns=['adjusted_msr_time'], inplace=True, errors='ignore')
        
    return overtime_mask

def _calculate_overtime_v(df_v, pressure, thresholds):
    """Calculates overtime mask for V section with improved RC logic (方案四)."""
    overtime_mask = pd.Series(False, index=df_v.index)
    overtime_thresholds = thresholds['OVERTIME']
    cr_thresholds = overtime_thresholds['CR']
    rc_ind_threshold = overtime_thresholds['RC_INDIVIDUAL']
    rc_group_targets = overtime_thresholds['RC_GROUP_TARGET']

    # 從v_modules.constants導入方案四所需常量
    from gmat_diagnosis_app.diagnostics.v_modules.constants import (
        RC_INDIVIDUAL_TOLERANCE_WHEN_GROUP_GOOD,
        RC_GROUP_PERFORMANCE_CATEGORIES
    )
    
    # Ensure q_time_numeric exists, if not, create it from question_time
    if 'q_time_numeric' not in df_v.columns:
        df_v['q_time_numeric'] = pd.to_numeric(df_v['question_time'], errors='coerce')

    rc_cols_present = all(c in df_v.columns for c in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time', 'rc_group_num_questions']) # Added rc_group_num_questions for completeness
    if not rc_cols_present:
        warnings.warn("Verbal overtime: Missing preprocessed RC columns. RC overtime calculation will be skipped.", UserWarning, stacklevel=3)

    # 處理CR題型（邏輯不變）
    cr_mask = (df_v['question_type'] == 'Critical Reasoning')
    if cr_mask.any():
        threshold = cr_thresholds['pressure'] if pressure else cr_thresholds['no_pressure']
        is_cr_overtime = (df_v['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[cr_mask & is_cr_overtime] = True

    # 處理RC題型（方案四新邏輯）
    rc_mask = (df_v['question_type'] == 'Reading Comprehension')
    if rc_mask.any() and rc_cols_present:
        # 新增RC組表現分類列
        df_v['rc_group_performance'] = 'unknown'
        
        # 計算調整後時間（扣除閱讀時間）
        df_v['adjusted_rc_time'] = df_v['q_time_numeric']
        first_q_rc_mask = rc_mask & df_v['rc_group_id'].notna() & (df_v['rc_reading_time'] != 0)      
        df_v.loc[first_q_rc_mask, 'adjusted_rc_time'] = df_v.loc[first_q_rc_mask, 'q_time_numeric'] - df_v.loc[first_q_rc_mask, 'rc_reading_time']
        
        # 針對每個RC組進行評估
        unique_rc_groups = df_v.loc[rc_mask & df_v['rc_group_id'].notna(), 'rc_group_id'].unique()
        for group_id in unique_rc_groups:
            group_data = df_v[(df_v['rc_group_id'] == group_id) & rc_mask]
            if group_data.empty: continue

            num_questions_in_group = group_data['rc_group_num_questions'].iloc[0]
            group_total_time = group_data['rc_group_total_time'].iloc[0]
            
            target_key = f"{int(num_questions_in_group)}Q" if num_questions_in_group in [3,4] else None
            if target_key and target_key in rc_group_targets:
                group_target_times = rc_group_targets[target_key]
                target_time_for_group = group_target_times['pressure'] if pressure else group_target_times['no_pressure']
                
                # 方案四：根據整組表現分類
                if group_total_time <= target_time_for_group:
                    # 整組表現良好
                    df_v.loc[group_data.index, 'rc_group_performance'] = RC_GROUP_PERFORMANCE_CATEGORIES['GOOD']
                    
                    # 使用更寬容的單題標準
                    adjusted_ind_threshold = rc_ind_threshold + RC_INDIVIDUAL_TOLERANCE_WHEN_GROUP_GOOD
                    is_rc_ind_overtime = (df_v.loc[group_data.index, 'adjusted_rc_time'] > adjusted_ind_threshold).fillna(False)
                    overtime_mask.loc[group_data.index[is_rc_ind_overtime]] = True
                    
                    # 標記單題寬容度資訊
                    df_v.loc[group_data.index, 'rc_tolerance_applied'] = True
                    
                elif group_total_time <= (target_time_for_group + RC_GROUP_TARGET_TIME_ADJUSTMENT):
                    # 整組表現尚可
                    df_v.loc[group_data.index, 'rc_group_performance'] = RC_GROUP_PERFORMANCE_CATEGORIES['ACCEPTABLE']
                    
                    # 使用標準閾值判斷單題
                    is_rc_ind_overtime = (df_v.loc[group_data.index, 'adjusted_rc_time'] > rc_ind_threshold).fillna(False)
                    overtime_mask.loc[group_data.index[is_rc_ind_overtime]] = True
                    
                    # 標記未應用寬容度
                    df_v.loc[group_data.index, 'rc_tolerance_applied'] = False
                    
                else:
                    # 整組表現不佳
                    df_v.loc[group_data.index, 'rc_group_performance'] = RC_GROUP_PERFORMANCE_CATEGORIES['POOR']
                    
                    # 整組標記為overtime
                    overtime_mask.loc[group_data.index] = True
                    
                    # 標記未應用寬容度
                    df_v.loc[group_data.index, 'rc_tolerance_applied'] = False
                    
                    # 標識"元兇"（超時最嚴重的題目）
                    time_deviations = df_v.loc[group_data.index, 'adjusted_rc_time'] - rc_ind_threshold
                    time_deviations = time_deviations.fillna(0)
                    if not time_deviations.empty:
                        # 至少標記一個元兇（如果有超時的話）
                        culprits = time_deviations[time_deviations > 0]
                        if not culprits.empty:
                            worst_offenders = culprits.nlargest(min(2, len(culprits))).index
                            df_v.loc[worst_offenders, 'rc_overtime_culprit'] = True
                            
                            # 標記嚴重元兇（超時超過1分鐘）
                            severe_offenders = time_deviations[time_deviations > 1.0].index
                            df_v.loc[severe_offenders, 'rc_severe_overtime_culprit'] = True

    # 保留這些列以供診斷使用
    cols_to_keep = ['rc_group_performance', 'rc_tolerance_applied', 'rc_overtime_culprit', 'rc_severe_overtime_culprit', 'adjusted_rc_time']
    for col in cols_to_keep:
        if col in df_v.columns:
            # 將這些診斷列複製到原始df_v
            if col not in overtime_mask.index.names:  # 確保不是索引名稱，避免衝突
                overtime_mask = pd.concat([overtime_mask, df_v[col]], axis=1)
    
    # 清理臨時列
    if 'adjusted_rc_time' in df_v.columns:
        df_v.drop(columns=['adjusted_rc_time'], inplace=True, errors='ignore')
    
    return overtime_mask # 返回計算的mask和診斷列

def calculate_overtime(df, time_pressure_status_map):
    """
    Calculates 'overtime' status for each question based on section-specific rules
    and time pressure. This is typically run AFTER initial preprocessing like
    preprocess_verbal_data and preprocess_di_data which add group time info.

    Args:
        df (pd.DataFrame): Combined DataFrame. Requires 'Subject', 'question_time',
                           'question_type'. For V, requires 'rc_group_id', 
                           'rc_group_total_time', 'rc_group_num_questions'.
                           For DI, requires 'msr_group_id'.
        time_pressure_status_map (dict): {'Q': bool, 'DI': bool, 'V': bool}

    Returns:
        pd.DataFrame: DataFrame with an added boolean 'overtime' column and
                     additional diagnostic columns for RC questions.
    """
    if df.empty:
        return df

    # Add 'overtime' column if it doesn't exist, initialized to False
    if 'overtime' not in df.columns:
        df['overtime'] = False

    # Convert question_time to numeric once for efficiency
    if 'q_time_numeric' not in df.columns:
        df['q_time_numeric'] = pd.to_numeric(df['question_time'], errors='coerce')

    # Ensure required threshold structure exists
    if not isinstance(THRESHOLDS, dict):
        logging.error("THRESHOLDS configuration is invalid.")
        return df # Return unmodified df

    for subject in df['Subject'].unique():
        subject_mask = (df['Subject'] == subject)
        if not subject_mask.any():
            continue

        df_subj = df[subject_mask].copy() # Work on a copy for this section
        pressure = time_pressure_status_map.get(subject, False)
        subj_thresholds = THRESHOLDS.get(subject)

        if not subj_thresholds or not isinstance(subj_thresholds.get('OVERTIME'), dict):
            # warnings.warn(f"Invalid or missing OVERTIME thresholds for subject {subject}. Skipping overtime calculation.", UserWarning, stacklevel=2)
            continue

        overtime_mask = pd.Series(False, index=df_subj.index) # Default mask
        calculated_columns = {} # To store columns added by helper functions

        try:
            if subject == 'Q':
                overtime_mask = _calculate_overtime_q(df_subj, pressure, subj_thresholds)
            elif subject == 'DI':
                overtime_mask = _calculate_overtime_di(df_subj, pressure, subj_thresholds)
            elif subject == 'V':
                overtime_result = _calculate_overtime_v(df_subj, pressure, subj_thresholds)
                if isinstance(overtime_result, pd.DataFrame):
                    overtime_mask = overtime_result.iloc[:, 0]
                    calculated_columns = {col: overtime_result[col] for col in overtime_result.columns[1:]}
                else:
                    overtime_mask = overtime_result

            df.loc[subject_mask, 'overtime'] = overtime_mask
            for col, values in calculated_columns.items():
                df.loc[subject_mask, col] = values

        except KeyError as e:
            warnings.warn(f"Missing expected column during overtime calculation for {subject}: {e}. Skipping.", UserWarning, stacklevel=2)
        except Exception as e:
            logging.error(f"Error calculating overtime for {subject}: {e}", exc_info=True) # Keep this important error log
            warnings.warn(f"Error during overtime calculation for {subject}: {e}. Results may be incomplete.", RuntimeWarning, stacklevel=2)

    # Clean up the temporary numeric time column if we added it
    if 'q_time_numeric' in df.columns and not df.columns.duplicated().any(): # Avoid error if multiple q_time_numeric somehow exist
        df.drop(columns=['q_time_numeric'], inplace=True, errors='ignore')
        
    return df