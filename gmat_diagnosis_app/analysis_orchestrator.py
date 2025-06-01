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
import time

# --- Custom Module Imports ---
# from gmat_diagnosis_app import irt_module as irt
# from gmat_diagnosis_app.preprocess_helpers import calculate_overtime, THRESHOLDS, parse_adjusted_qns # Old import
# THRESHOLDS now imported from constants.thresholds later in the file
# from gmat_diagnosis_app.utils.parsing_utils import parse_adjusted_qns # New import

# from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
# from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
# from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.constants.config import (
    SUBJECTS, BANK_SIZE, RANDOM_SEED,
    SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS
)
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS
from gmat_diagnosis_app.services.openai_service import (
    summarize_report_with_openai, generate_ai_consolidated_report
)
# from gmat_diagnosis_app.services.plotting_service import create_theta_plot
# from gmat_diagnosis_app.subject_preprocessing.verbal_preprocessor import preprocess_verbal_data
# from gmat_diagnosis_app.subject_preprocessing.di_preprocessor import preprocess_di_data
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

# Import translation system
from gmat_diagnosis_app.i18n import translate as t

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
    current_status_message = t('analysis_initializing')
    status_text_element.text(current_status_message)

    # --- 1. Calculate Time Pressure ---
    try:
        current_step = 1
        current_status_message = t('analysis_step_time_pressure').format(current_step, total_steps)
        status_text_element.text(current_status_message)

        time_pressure_map, time_pressure_success = calculate_time_pressure(df_combined_input)
        
        if not time_pressure_success:
            analysis_success = False
            current_status_message = t('analysis_step_time_pressure_error').format(current_step, total_steps)
            status_text_element.text(current_status_message)
            return False
            
        progress_bar.progress(current_step / total_steps)

    except Exception as e:
        logging.error(f"Error occurred while calculating time pressure: {e}", exc_info=True)
        st.error(f"Error occurred while calculating time pressure: {e}")
        analysis_success = False
        current_status_message = t('analysis_step_time_pressure_error').format(current_step, total_steps)
        status_text_element.text(current_status_message)
        return False

    # --- 2. Prepare Data for Simulation ---
    df_final_input_for_sim = None
    if analysis_success:
        current_step = 2
        current_status_message = t('analysis_step_data_preparation').format(current_step, total_steps)
        status_text_element.text(current_status_message)
        try:
            df_final_input_for_sim = df_combined_input
            progress_bar.progress(current_step / total_steps)
        except Exception as e:
            st.error(f"Error occurred while preparing simulation data: {e}")
            analysis_success = False
            current_status_message = t('analysis_step_data_preparation_error').format(current_step, total_steps)
            status_text_element.text(current_status_message)
            return False

    # --- 3. IRT Simulation ---
    if analysis_success:
        current_step = 3
        current_status_message = t('analysis_step_irt_simulation').format(current_step, total_steps)
        status_text_element.text(current_status_message)
        
        try:
            # 將 run_simulation 拆分為兩個子步驟
            # 這裡可以添加進度更新
            status_text_element.text(t('analysis_step_irt_initialization').format(current_step, total_steps))
            
            all_simulation_histories, final_thetas_local, all_theta_plots, question_banks, sim_success = run_simulation(df_final_input_for_sim)
            
            status_text_element.text(t('analysis_step_theta_generation').format(current_step, total_steps))
            
            if not sim_success:
                analysis_success = False
                current_status_message = t('analysis_step_irt_error').format(current_step, total_steps)
                status_text_element.text(current_status_message)
                return False
                
            progress_bar.progress(current_step / total_steps)
            
        except Exception as e:
            st.error(f"Error occurred during IRT simulation process: {e}")
            analysis_success = False
            current_status_message = t('analysis_step_irt_error').format(current_step, total_steps)
            status_text_element.text(current_status_message)
            return False

    # --- 4. Prepare Data for Diagnosis ---
    if analysis_success:
        current_step = 4
        current_status_message = t('analysis_step_diagnosis_preparation').format(current_step, total_steps)
        status_text_element.text(current_status_message)
        
        try:
            # --- Apply is_invalid logic and calculate average times BEFORE splitting by subject ---
            status_text_element.text(t('analysis_step_invalid_marking').format(current_step, total_steps))
            
            df_combined_input_with_invalids, all_subjects_avg_times, all_subjects_ft_avg_times = \
                calculate_and_apply_invalid_logic(df_final_input_for_sim, time_pressure_map, THRESHOLDS)
            
            status_text_element.text(t('analysis_step_data_splitting').format(current_step, total_steps))
            
            df_final_for_diagnosis, diagnosis_prep_success = prepare_dataframes_for_diagnosis(
                all_simulation_histories, 
                final_thetas_local, 
                time_pressure_map, 
                df_combined_input_with_invalids
            )
            
            if not diagnosis_prep_success:
                analysis_success = False
                current_status_message = t('analysis_step_diagnosis_preparation_error').format(current_step, total_steps)
                status_text_element.text(current_status_message)
                return False
                
            progress_bar.progress(current_step / total_steps)
            
        except Exception as e:
            st.error(f"Error occurred during subject diagnosis preparation: {e}")
            analysis_success = False
            current_status_message = t('analysis_step_diagnosis_preparation_error').format(current_step, total_steps)
            status_text_element.text(current_status_message)
            return False

    # --- 5. Run Diagnosis ---
    if analysis_success and df_final_for_diagnosis is not None:
        current_step = 5
        current_status_message = t('analysis_step_diagnosis_execution').format(current_step, total_steps)
        status_text_element.text(current_status_message)
        
        try:
            # 細分顯示各科目診斷進度
            status_text_element.text(t('analysis_step_q_diagnosis').format(current_step, total_steps))
            
            # 這裡不實際修改代碼邏輯，僅添加進度顯示
            # 假設診斷邏輯按照Q、V、DI順序運行
            processed_df, report_dict, consolidated_report, diagnosis_success = run_diagnosis(df_final_for_diagnosis, time_pressure_map)
            
            # V科目診斷進度顯示 - 這只是UI顯示，不影響實際執行
            status_text_element.text(t('analysis_step_v_diagnosis').format(current_step, total_steps))
            
            # 短暫延遲確保用戶能看到進度變化
            time.sleep(0.5)
            
            # DI科目診斷進度顯示
            status_text_element.text(t('analysis_step_di_diagnosis').format(current_step, total_steps))
            
            time.sleep(0.5)
            
            # 報告生成與整合階段
            # status_text_element.text(f"步驟 {current_step}/{total_steps}: 生成診斷報告與整合診斷結果...")
            
            # AI匯總報告生成階段
            if st.session_state.master_key:
                status_text_element.text(t('analysis_step_ai_summary').format(current_step, total_steps))
            
            if not diagnosis_success:
                analysis_success = False
                current_status_message = t('analysis_step_diagnosis_error').format(current_step, total_steps)
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
                current_status_message = t('analysis_complete').format(total_steps)
                status_text_element.text(current_status_message)
            
        except Exception as e:
            st.error(f"Unexpected error occurred during diagnosis: {e}")
            analysis_success = False
            current_status_message = t('analysis_step_diagnosis_execution_error').format(current_step, total_steps)
            status_text_element.text(current_status_message)
            return False

    return analysis_success 