# -*- coding: utf-8 -*-
# Ensure UTF-8 encoding for comments/strings
"""
Orchestrates the GMAT analysis pipeline.
簡化後的協調器，負責協調各個分離出來的模組。
"""

import pandas as pd
import numpy as np
import streamlit as st
import logging
import plotly.graph_objects as go

# --- Custom Module Imports ---
from gmat_diagnosis_app import irt_module as irt
# from gmat_diagnosis_app.preprocess_helpers import calculate_overtime, THRESHOLDS, parse_adjusted_qns # Old import
from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_overtime # New import
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # New import
from gmat_diagnosis_app.utils.parsing_utils import parse_adjusted_qns # New import

from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.constants.config import (
    SUBJECTS, BANK_SIZE, RANDOM_SEED,
    SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS
)
from gmat_diagnosis_app.services.openai_service import (
    summarize_report_with_openai, generate_ai_consolidated_report
)
from gmat_diagnosis_app.services.plotting_service import create_theta_plot
from gmat_diagnosis_app.subject_preprocessing.verbal_preprocessor import preprocess_verbal_data # Added import
from gmat_diagnosis_app.subject_preprocessing.di_preprocessor import preprocess_di_data # Added import
# Note: utils.validation, utils.data_processing, utils.excel_utils are not directly used by run_analysis
# but by functions it calls or data it prepares for.
# If any direct utility from them is needed, they should be imported here.

# --- 從分拆出去的模組引入功能 ---
from gmat_diagnosis_app.analysis_helpers.time_pressure_analyzer import (
    calculate_time_pressure, 
    calculate_and_apply_invalid_logic
)
from gmat_diagnosis_app.analysis_helpers.simulation_manager import (
    run_simulation,
    prepare_dataframes_for_diagnosis
)
from gmat_diagnosis_app.analysis_helpers.diagnosis_manager import (
    run_diagnosis,
    update_session_state_after_analysis
)

def _calculate_and_apply_invalid_logic(df_input, time_pressure_map_param, subject_thresholds_param):
    df_output = df_input.copy()
    if 'is_invalid' not in df_output.columns:
        df_output['is_invalid'] = False
    else:
        df_output['is_invalid'] = df_output['is_invalid'].fillna(False).astype(bool)

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

    return df_output, calculated_avg_times, calculated_ft_avg_times

def run_analysis(df_combined_input):
    """Run the complete analysis pipeline on the input data"""
    analysis_success = True
    df_final_for_diagnosis = None
    total_steps = 5
    current_step = 0

    # Initialize progress bar and status text placeholder
    progress_bar = st.progress(0)
    status_text_element = st.empty()
    
    # NEW: String variable to hold the actual status message
    current_status_message = f"步驟 {current_step}/{total_steps}: 準備開始分析..."
    status_text_element.text(current_status_message)

    # --- 1. Calculate Time Pressure ---
    try:
        current_step = 1
        current_status_message = f"步驟 {current_step}/{total_steps}: 計算時間壓力..."
        status_text_element.text(current_status_message)

        time_pressure_map, time_pressure_success = calculate_time_pressure(df_combined_input)
        
        if not time_pressure_success:
            analysis_success = False
            current_status_message = f"步驟 {current_step}/{total_steps}: 計算時間壓力時出錯。"
            status_text_element.text(current_status_message)
            return False
            
        progress_bar.progress(current_step / total_steps)

    except Exception as e:
        logging.error(f"計算時間壓力時出錯: {e}", exc_info=True)
        st.error(f"計算時間壓力時出錯: {e}")
        analysis_success = False
        current_status_message = f"步驟 {current_step}/{total_steps}: 計算時間壓力時出錯。"
        status_text_element.text(current_status_message)
        return False

    # --- 2. Prepare Data for Simulation ---
    df_final_input_for_sim = None
    if analysis_success:
        current_step = 2
        current_status_message = f"步驟 {current_step}/{total_steps}: 準備數據進行模擬..."
        status_text_element.text(current_status_message)
        try:
            df_final_input_for_sim = df_combined_input
            progress_bar.progress(current_step / total_steps)
        except Exception as e:
            st.error(f"準備模擬數據時出錯: {e}")
            analysis_success = False
            current_status_message = f"步驟 {current_step}/{total_steps}: 準備模擬數據時出錯。"
            status_text_element.text(current_status_message)
            return False

    # --- 3. IRT Simulation ---
    if analysis_success:
        current_step = 3
        current_status_message = f"步驟 {current_step}/{total_steps}: 執行 IRT 模擬獲取能力值 (Theta)..."
        status_text_element.text(current_status_message)
        
        try:
            all_simulation_histories, final_thetas_local, all_theta_plots, question_banks, sim_success = run_simulation(df_final_input_for_sim)
            
            if not sim_success:
                analysis_success = False
                current_status_message = f"步驟 {current_step}/{total_steps}: IRT 模擬過程中出錯。"
                status_text_element.text(current_status_message)
                return False
                
            progress_bar.progress(current_step / total_steps)
            
        except Exception as e:
            st.error(f"IRT 模擬過程中出錯: {e}")
            analysis_success = False
            current_status_message = f"步驟 {current_step}/{total_steps}: IRT 模擬過程中出錯。"
            status_text_element.text(current_status_message)
            return False

    # --- 4. Prepare Data for Diagnosis ---
    if analysis_success:
        current_step = 4
        current_status_message = f"步驟 {current_step}/{total_steps}: 執行科目診斷..."
        status_text_element.text(current_status_message)
        
        try:
            # --- Apply is_invalid logic and calculate average times BEFORE splitting by subject ---
            df_combined_input_with_invalids, all_subjects_avg_times, all_subjects_ft_avg_times = \
                calculate_and_apply_invalid_logic(df_final_input_for_sim, time_pressure_map, THRESHOLDS)
            
            df_final_for_diagnosis, diagnosis_prep_success = prepare_dataframes_for_diagnosis(
                df_combined_input, 
                all_simulation_histories, 
                final_thetas_local, 
                time_pressure_map, 
                THRESHOLDS, 
                df_combined_input_with_invalids
            )
            
            if not diagnosis_prep_success:
                analysis_success = False
                current_status_message = f"步驟 {current_step}/{total_steps}: 科目診斷數據準備失敗。"
                status_text_element.text(current_status_message)
                return False
                
            progress_bar.progress(current_step / total_steps)
            
        except Exception as e:
            st.error(f"科目診斷準備過程中出錯: {e}")
            analysis_success = False
            current_status_message = f"步驟 {current_step}/{total_steps}: 科目診斷準備過程中出錯。"
            status_text_element.text(current_status_message)
            return False

    # --- 5. Run Diagnosis ---
    if analysis_success and df_final_for_diagnosis is not None:
        current_step = 5
        current_status_message = f"步驟 {current_step}/{total_steps}: 執行綜合診斷..."
        status_text_element.text(current_status_message)
        
        try:
            processed_df, report_dict, consolidated_report, diagnosis_success = run_diagnosis(df_final_for_diagnosis, time_pressure_map)
            
            if not diagnosis_success:
                analysis_success = False
                current_status_message = f"步驟 {current_step}/{total_steps}: 診斷過程失敗。"
                status_text_element.text(current_status_message)
                
            # --- Final Status Update ---
            update_session_state_after_analysis(
                analysis_success, 
                processed_df, 
                report_dict, 
                final_thetas_local, 
                all_theta_plots, 
                consolidated_report, 
                error_message=current_status_message if not analysis_success else None
            )
            
            progress_bar.progress(1.0)
            
            if analysis_success:
                current_status_message = f"步驟 {current_step}/{total_steps}: 分析完成！"
                status_text_element.text(current_status_message)
            
        except Exception as e:
            st.error(f"診斷過程中發生未預期錯誤: {e}")
            analysis_success = False
            current_status_message = f"步驟 {current_step}/{total_steps}: 執行診斷時出錯。"
            status_text_element.text(current_status_message)
            return False

    return analysis_success 