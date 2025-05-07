# -*- coding: utf-8 -*-
"""Functions for suggesting invalid questions based on rules."""
import pandas as pd
import math
import warnings
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import THRESHOLDS

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
        df_processed['is_manually_invalid'] = df_processed['is_manually_invalid'].fillna(False).astype(bool)
        
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
                ).reindex(indices).fillna(False)
        elif section == 'V':
             if time_pressure:
                 threshold = section_thresholds['INVALID_HASTY_MIN']
                 is_fast = q_time_series < threshold
                 auto_invalid_section_mask = is_fast.fillna(False)

        df_processed.loc[indices[eligible_for_auto], 'is_auto_suggested_invalid'] = auto_invalid_section_mask[eligible_for_auto]

    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']
    
    # 再次添加調試信息，確認最終的is_invalid狀態
    try:
        import streamlit as st
        final_invalid_count = df_processed['is_invalid'].sum()
        if final_invalid_count > 0:
            st.info(f"最終標記為無效的項目總數: {final_invalid_count}")
    except Exception as e:
        print(f"顯示最終無效項調試信息時出錯: {e}")
        
    df_processed.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')
    return df_processed 