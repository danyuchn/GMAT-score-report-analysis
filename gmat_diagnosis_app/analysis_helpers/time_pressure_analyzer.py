# -*- coding: utf-8 -*-
"""
Time pressure analysis functions for GMAT diagnosis app.
從analysis_orchestrator.py中分離出來的時間壓力計算邏輯。
"""

import pandas as pd
import numpy as np
import logging
import streamlit as st

from gmat_diagnosis_app.constants.thresholds import THRESHOLDS

def calculate_time_pressure(df_combined_input):
    """
    Calculate time pressure for each subject.
    
    Args:
        df_combined_input (pd.DataFrame): Combined dataframe with all subjects.
        
    Returns:
        dict: Dictionary mapping subjects to time pressure status.
        bool: Success status of the operation.
    """
    try:
        time_pressure_map = {}
        
        q_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'Q', 'question_time'], errors='coerce').sum()
        v_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'V', 'question_time'], errors='coerce').sum()
        di_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'DI', 'question_time'], errors='coerce').sum()

        # --- Q Time Pressure Calculation ---
        q_df = df_combined_input[df_combined_input['Subject'] == 'Q'].copy()
        q_df['question_time'] = pd.to_numeric(q_df['question_time'], errors='coerce')
        q_df['question_position'] = pd.to_numeric(q_df['question_position'], errors='coerce')
        q_df = q_df.sort_values('question_position').dropna(subset=['question_position'])

        time_diff_q = THRESHOLDS['Q']['MAX_ALLOWED_TIME'] - q_total_time
        time_diff_check = time_diff_q <= THRESHOLDS['Q']['TIME_DIFF_PRESSURE']

        fast_end_questions_exist_q = False
        if not q_df.empty:
            total_q_questions = len(q_df)
            last_third_start_index_q = int(total_q_questions * THRESHOLDS['Q']['LAST_THIRD_FRACTION'])
            last_third_q_df = q_df.iloc[last_third_start_index_q:]
            if not last_third_q_df.empty:
                comparison_series_q = (last_third_q_df['question_time'] < THRESHOLDS['Q']['INVALID_FAST_END_MIN'])
                if hasattr(comparison_series_q, 'any') and callable(comparison_series_q.any):
                    fast_end_questions_exist_q = comparison_series_q.any()

        time_pressure_q = time_diff_check and fast_end_questions_exist_q

        # --- V Time Pressure Calculation (Corrected Logic) ---
        v_df = df_combined_input[df_combined_input['Subject'] == 'V'].copy()
        v_df['question_time'] = pd.to_numeric(v_df['question_time'], errors='coerce')
        v_df['question_position'] = pd.to_numeric(v_df['question_position'], errors='coerce')
        v_df = v_df.sort_values('question_position').dropna(subset=['question_position'])
        
        time_diff_v = THRESHOLDS['V']['MAX_ALLOWED_TIME'] - v_total_time
        v_time_diff_pressure_threshold = THRESHOLDS['V'].get('TIME_DIFF_PRESSURE', THRESHOLDS['Q'].get('TIME_DIFF_PRESSURE', 3.0))
        v_last_third_fraction = THRESHOLDS['V'].get('LAST_THIRD_FRACTION', THRESHOLDS['Q'].get('LAST_THIRD_FRACTION', 2/3))
        v_invalid_fast_end_min = THRESHOLDS['V'].get('INVALID_FAST_END_MIN', THRESHOLDS['V'].get('INVALID_HASTY_MIN', 1.0))

        time_diff_check_v = time_diff_v <= v_time_diff_pressure_threshold
        fast_end_questions_exist_v = False
        if not v_df.empty:
            total_v_questions = len(v_df)
            if total_v_questions > 0:
                last_third_start_index_v = int(total_v_questions * v_last_third_fraction)
                last_third_v_df = v_df.iloc[last_third_start_index_v:]
                if not last_third_v_df.empty:
                    comparison_series_v = (last_third_v_df['question_time'] < v_invalid_fast_end_min)
                    if hasattr(comparison_series_v, 'any') and callable(comparison_series_v.any):
                        fast_end_questions_exist_v = comparison_series_v.any()

        time_pressure_v = time_diff_check_v and fast_end_questions_exist_v

        # --- DI Time Pressure Calculation (Corrected Logic - similar to Q/V) ---
        di_df = df_combined_input[df_combined_input['Subject'] == 'DI'].copy()
        di_df['question_time'] = pd.to_numeric(di_df['question_time'], errors='coerce')
        di_df['question_position'] = pd.to_numeric(di_df['question_position'], errors='coerce')
        di_df = di_df.sort_values('question_position').dropna(subset=['question_position'])

        time_diff_di = THRESHOLDS['DI']['MAX_ALLOWED_TIME'] - di_total_time
        di_time_diff_pressure_threshold = THRESHOLDS['DI'].get('TIME_DIFF_PRESSURE', THRESHOLDS['DI'].get('TIME_PRESSURE_DIFF_MIN', 3.0))
        di_last_third_fraction = THRESHOLDS['DI'].get('LAST_THIRD_FRACTION', THRESHOLDS['Q'].get('LAST_THIRD_FRACTION', 2/3))
        di_invalid_fast_end_min = THRESHOLDS['DI'].get('INVALID_FAST_END_MIN', 1.0)

        time_diff_check_di = time_diff_di <= di_time_diff_pressure_threshold
        fast_end_questions_exist_di = False
        if not di_df.empty:
            total_di_questions = len(di_df)
            if total_di_questions > 0:
                last_third_start_index_di = int(total_di_questions * di_last_third_fraction)
                last_third_di_df = di_df.iloc[last_third_start_index_di:]
                if not last_third_di_df.empty:
                    comparison_series_di = (last_third_di_df['question_time'] < di_invalid_fast_end_min)
                    if hasattr(comparison_series_di, 'any') and callable(comparison_series_di.any):
                        fast_end_questions_exist_di = comparison_series_di.any()

        time_pressure_di = time_diff_check_di and fast_end_questions_exist_di

        time_pressure_map = {'Q': time_pressure_q, 'V': time_pressure_v, 'DI': time_pressure_di}
        return time_pressure_map, True
        
    except Exception as e:
        logging.error(f"計算時間壓力時出錯: {e}", exc_info=True)
        if st:
            st.error(f"計算時間壓力時出錯: {e}")
        return {}, False

def calculate_and_apply_invalid_logic(df_input, time_pressure_map_param, subject_thresholds_param):
    """
    Calculate invalid markers for questions under time pressure.
    
    Args:
        df_input (pd.DataFrame): Input dataframe with all subjects.
        time_pressure_map_param (dict): Dictionary of time pressure by subject.
        subject_thresholds_param (dict): Dictionary of thresholds by subject.
        
    Returns:
        tuple: (DataFrame with invalids, avg times dict, first third avg times dict)
    """
    df_output = df_input.copy()
    if 'is_invalid' not in df_output.columns:
        df_output['is_invalid'] = False
    else:
        df_output['is_invalid'] = df_output['is_invalid'].replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False).astype(bool)

    calculated_avg_times = {}
    calculated_ft_avg_times = {}

    for subject_code, is_pressure in time_pressure_map_param.items():
        subj_df_mask = df_output['Subject'] == subject_code
        if not subj_df_mask.any():
            calculated_avg_times[subject_code] = {}
            calculated_ft_avg_times[subject_code] = {}
            continue

        current_subj_df = df_output[subj_df_mask].copy()
        current_subj_df['question_time'] = pd.to_numeric(current_subj_df['question_time'], errors='coerce')
        current_subj_df['question_position'] = pd.to_numeric(current_subj_df['question_position'], errors='coerce')
        current_subj_df = current_subj_df.sort_values('question_position').reset_index(drop=True)

        avg_time_per_type = {}
        if not current_subj_df.empty:
            avg_time_per_type = current_subj_df.groupby('question_type')['question_time'].mean().to_dict()
        calculated_avg_times[subject_code] = avg_time_per_type

        total_questions_subj = len(current_subj_df)
        first_third_q_count = 0
        if total_questions_subj > 0:
            first_third_q_count = int(total_questions_subj / 3)
        
        first_third_df = current_subj_df.head(first_third_q_count) 
        ft_avg_time = {}
        if not first_third_df.empty:
            ft_avg_time = first_third_df.groupby('question_type')['question_time'].mean().to_dict()
        calculated_ft_avg_times[subject_code] = ft_avg_time

        if is_pressure and total_questions_subj > 0:
            last_third_fraction = subject_thresholds_param.get(subject_code, {}).get('LAST_THIRD_FRACTION', subject_thresholds_param['Q']['LAST_THIRD_FRACTION'])
            last_third_start_index = int(total_questions_subj * last_third_fraction)
            
            original_indices_to_check = df_output[subj_df_mask].iloc[last_third_start_index:].index

            for original_idx in original_indices_to_check:
                row = df_output.loc[original_idx]
                q_time = pd.to_numeric(row['question_time'], errors='coerce')
                q_type = row['question_type']
                
                ft_avg_time_for_q_type = ft_avg_time.get(q_type, np.nan)
                is_abnormally_fast = False
                if pd.notna(q_time) and q_time < 0.5: 
                    is_abnormally_fast = True
                
                if not is_abnormally_fast and pd.notna(q_time) and q_time < 1.0: 
                    is_abnormally_fast = True
                
                if not is_abnormally_fast and pd.notna(q_time) and pd.notna(ft_avg_time_for_q_type) and ft_avg_time_for_q_type > 0:
                    if q_time < (ft_avg_time_for_q_type * 0.5):
                        is_abnormally_fast = True
                
                if not is_abnormally_fast and subject_code == 'V' and q_type == 'Reading Comprehension':
                    rc_group_id_val = row.get('rc_group_id')
                    if pd.notna(rc_group_id_val):
                        current_rc_group_df = df_output[df_output['rc_group_id'] == rc_group_id_val]
                        group_total_time = pd.to_numeric(current_rc_group_df['question_time'], errors='coerce').sum()
                        num_q_in_group = len(current_rc_group_df)
                        ft_avg_rc_time_v = ft_avg_time.get('Reading Comprehension', np.nan)

                        if pd.notna(ft_avg_rc_time_v) and ft_avg_rc_time_v > 0 and num_q_in_group > 0:
                            if group_total_time < (ft_avg_rc_time_v * num_q_in_group * 0.5):
                                for g_idx in current_rc_group_df.index:
                                    if g_idx in original_indices_to_check:
                                        df_output.loc[g_idx, 'is_invalid'] = True
                                is_abnormally_fast = True
                
                elif not is_abnormally_fast and subject_code == 'DI' and q_type == 'MSR':
                    msr_group_id_val = row.get('msr_group_id')
                    if pd.notna(msr_group_id_val):
                        current_msr_group_df = df_output[df_output['msr_group_id'] == msr_group_id_val]
                        group_total_time_msr = pd.to_numeric(current_msr_group_df['question_time'], errors='coerce').sum()
                        num_q_in_msr_group = len(current_msr_group_df)
                        ft_avg_msr_time_di = ft_avg_time.get('MSR', np.nan)
                        
                        if pd.notna(ft_avg_msr_time_di) and ft_avg_msr_time_di > 0 and num_q_in_msr_group > 0:
                            if group_total_time_msr < (ft_avg_msr_time_di * num_q_in_msr_group * 0.5):
                                for g_idx in current_msr_group_df.index:
                                    if g_idx in original_indices_to_check:
                                        df_output.loc[g_idx, 'is_invalid'] = True
                                is_abnormally_fast = True 

                if is_abnormally_fast and not df_output.loc[original_idx, 'is_invalid']:
                    df_output.loc[original_idx, 'is_invalid'] = True

    # After all automatic invalid logic, merge manual invalid flags
    if 'is_manually_invalid' in df_output.columns:
        df_output['is_manually_invalid'] = df_output['is_manually_invalid'].replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False).astype(bool)
        df_output['is_invalid'] = df_output['is_invalid'] | df_output['is_manually_invalid']

    return df_output, calculated_avg_times, calculated_ft_avg_times 