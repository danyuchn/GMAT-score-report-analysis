# -*- coding: utf-8 -*-
"""Functions for suggesting invalid questions based on rules."""
import pandas as pd
import math
import warnings
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import THRESHOLDS
from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_first_third_average_time_per_type
import numpy as np

def _suggest_invalid_last_third(pos_series, time_series, total_q, fraction, threshold):
    """Helper to check for invalid questions in the last fraction."""
    if total_q <= 0:
        return pd.Series(False, index=pos_series.index)
    last_part_start_pos = math.ceil(total_q * fraction)
    is_last_part = pos_series >= last_part_start_pos
    is_too_fast = time_series < threshold
    return is_last_part & is_too_fast

def suggest_invalid_questions(df, time_pressure_status_map):
    """
    Suggests invalid questions based on simplified rules for PREPROCESSING.
    Prioritizes 'is_manually_invalid' flag if present. Adds 'is_auto_suggested_invalid'.
    The final 'is_invalid' is manual OR auto_suggested (for preview).

    Args:
        df (pd.DataFrame): Combined DataFrame. Requires 'Subject', 'question_position',
                           'question_time'. Optional: 'is_manually_invalid'.
        time_pressure_status_map (dict): {'Q': bool, 'DI': bool, 'V': bool}

    Returns:
        pd.DataFrame: DataFrame with 'is_invalid', 'is_manually_invalid' (preserved or added),
                      and 'is_auto_suggested_invalid' columns.
    """
    df_processed = df.copy()

    if 'is_manually_invalid' not in df_processed.columns:
        df_processed['is_manually_invalid'] = False
    else:
        df_processed['is_manually_invalid'] = df_processed['is_manually_invalid'].replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False).astype(bool)
        
        # 添加調試信息 - 記錄任何手動標記的無效項
        manually_invalid_count = df_processed['is_manually_invalid'].sum()
        if manually_invalid_count > 0:
            import streamlit as st
            try:
                st.warning(f"檢測到 {manually_invalid_count} 個手動標記的無效項", icon="⚠️")
                # 顯示這些項的詳細信息
                manually_invalid_indices = df_processed[df_processed['is_manually_invalid']].index
                for idx in manually_invalid_indices:
                    q_pos = df_processed.loc[idx, 'question_position'] if 'question_position' in df_processed.columns else "未知"
                    subj = df_processed.loc[idx, 'Subject'] if 'Subject' in df_processed.columns else "未知"
                    st.info(f"手動標記無效: 科目={subj}, 題號={q_pos}")
            except Exception as e:
                print(f"顯示手動無效項調試信息時出錯: {e}")

    df_processed['is_auto_suggested_invalid'] = False

    required_cols = ['Subject', 'question_position', 'question_time']
    missing_cols = [col for col in required_cols if col not in df_processed.columns]
    if missing_cols:
        warnings.warn(f"Missing required columns for invalid suggestion: {missing_cols}. Skipping suggestion.", UserWarning, stacklevel=2)
        df_processed['is_invalid'] = df_processed['is_manually_invalid']
        return df_processed

    df_processed['q_time_numeric'] = pd.to_numeric(df_processed['question_time'], errors='coerce')
    df_processed['q_pos_numeric'] = pd.to_numeric(df_processed['question_position'], errors='coerce')

    for section, section_thresholds in THRESHOLDS.items():
        section_mask = (df_processed['Subject'] == section)
        if not section_mask.any():
            continue

        indices = df_processed[section_mask].index
        eligible_for_auto = ~df_processed.loc[indices, 'is_manually_invalid']
        time_pressure = time_pressure_status_map.get(section, False)
        auto_invalid_section_mask = pd.Series(False, index=indices)
        q_time_series = df_processed.loc[indices, 'q_time_numeric']
        q_pos_series = df_processed.loc[indices, 'q_pos_numeric']

        if section in ['Q', 'DI']:
            if time_pressure:
                threshold = section_thresholds['INVALID_FAST_END_MIN']
                total_q = section_thresholds['TOTAL_QUESTIONS']
                fraction = section_thresholds['LAST_THIRD_FRACTION']
                auto_invalid_section_mask = _suggest_invalid_last_third(
                    q_pos_series.dropna(), q_time_series.dropna(), total_q, fraction, threshold
                ).reindex(indices).replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False)
        elif section == 'V':
            if time_pressure:
                # V 科目四個異常快速回應檢測準則（MD 文檔第一章）
                auto_invalid_section_mask = pd.Series(False, index=indices)
                
                # 計算測驗最後 1/3 的題目
                total_q = section_thresholds['TOTAL_QUESTIONS']
                last_third_size = total_q // 3
                last_third_start_position = total_q - last_third_size + 1
                
                # 獲取實際的題目位置範圍
                all_positions = sorted(q_pos_series.dropna().unique())
                if len(all_positions) >= last_third_size:
                    last_third_positions = all_positions[-last_third_size:]
                    is_last_third = q_pos_series.isin(last_third_positions)
                else:
                    # 如果題目數少於計算的1/3，則檢查所有題目
                    is_last_third = pd.Series(True, index=indices)
                
                # 計算前三分之一各題型平均時間
                v_section_df = df_processed[section_mask].copy()
                first_third_avg_times = calculate_first_third_average_time_per_type(
                    v_section_df, ['Critical Reasoning', 'Reading Comprehension']
                )
                
                for idx in indices:
                    if idx not in eligible_for_auto.index or not eligible_for_auto[idx]:
                        continue
                        
                    q_time = q_time_series.loc[idx] if idx in q_time_series.index else None
                    q_type = df_processed.loc[idx, 'question_type'] if 'question_type' in df_processed.columns else None
                    
                    if pd.isna(q_time):
                        continue
                    
                    # 檢查四個異常快速回應準則
                    abnormally_fast = False
                    
                    # 標準1：疑似放棄（< 0.5 分鐘）
                    if q_time < section_thresholds['INVALID_ABANDONED_MIN']:
                        abnormally_fast = True
                    
                    # 標準2：絕對倉促（< 1.0 分鐘）
                    elif q_time < section_thresholds['INVALID_HASTY_MIN']:
                        abnormally_fast = True
                    
                    # 標準3 & 4：相對於前三分之一平均時間（僅在測驗最後1/3檢查）
                    elif is_last_third.loc[idx] and q_type in first_third_avg_times:
                        first_third_avg = first_third_avg_times[q_type]
                        # 使用統一常數中的 SUSPICIOUS_FAST_MULTIPLIER (0.5)
                        from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS
                        suspicious_threshold = first_third_avg * COMMON_TIME_CONSTANTS['SUSPICIOUS_FAST_MULTIPLIER']
                        if q_time < suspicious_threshold:
                            abnormally_fast = True
                    
                    if abnormally_fast:
                        auto_invalid_section_mask.loc[idx] = True

        df_processed.loc[indices[eligible_for_auto], 'is_auto_suggested_invalid'] = auto_invalid_section_mask[eligible_for_auto]

    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']
        
    df_processed.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')
    return df_processed 