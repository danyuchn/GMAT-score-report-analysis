# -*- coding: utf-8 -*- # Ensure UTF-8 encoding for comments/strings
"""
GMAT診斷應用主程序
整合各個模組以提供完整的GMAT診斷功能
"""

import sys
import os
import io
import pandas as pd
import streamlit as st
import numpy as np
import logging
import openai
import plotly.graph_objects as go

# --- Project Path Setup ---
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # Handle cases where __file__ is not defined (e.g., interactive environments)
    st.warning("Could not automatically determine project root. Assuming modules are available.", icon="⚠️")
    project_root = os.getcwd()  # Fallback

# --- Module Imports ---
try:
    # Import custom modules for core logic
    from gmat_diagnosis_app import preprocess_helpers # Ensure the module itself is imported for setup_input_tabs
    # from gmat_diagnosis_app import irt_module as irt # Moved to analysis_orchestrator
    # from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q # Moved
    
    # Import our modularized components
    from gmat_diagnosis_app.constants.config import (
        SUBJECTS, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, BANK_SIZE, RANDOM_SEED,
        SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS, BASE_RENAME_MAP,
        REQUIRED_ORIGINAL_COLS, EXCEL_COLUMN_MAP
    )
    # from gmat_diagnosis_app.utils.validation import validate_dataframe
    # from gmat_diagnosis_app.utils.data_processing import process_subject_tab
    # from gmat_diagnosis_app.utils.styling import apply_styles
    # from gmat_diagnosis_app.utils.excel_utils import to_excel
    from gmat_diagnosis_app.services.openai_service import (
        summarize_report_with_openai, generate_ai_consolidated_report,
        get_chat_context, get_openai_response
    )
    # from gmat_diagnosis_app.services.plotting_service import create_theta_plot
    from gmat_diagnosis_app.ui.results_display import display_results, display_subject_results
    from gmat_diagnosis_app.ui.chat_interface import display_chat_interface
    from gmat_diagnosis_app.ui.input_tabs import setup_input_tabs, combine_input_data, display_analysis_button
    from gmat_diagnosis_app.session_manager import init_session_state, reset_session_for_new_upload # Added import
    from gmat_diagnosis_app.analysis_orchestrator import run_analysis # Added import
    
except ImportError as e:
    st.error(f"導入模組時出錯: {e}. 請確保環境設定正確，且 gmat_diagnosis_app 在 Python 路徑中。")
    st.stop()

# --- Initialize Column Display Configuration ---
# COLUMN_DISPLAY_CONFIG moved to ui/results_display.py

# --- Session State Functions ---
# init_session_state and reset_session_for_new_upload moved to session_manager.py

# --- Analysis Functions ---
# run_analysis moved to analysis_orchestrator.py

# --- Display Results Function ---
# display_results moved to ui.results_display.py

# --- Main Application ---
def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Set page title
    st.title('GMAT 成績診斷平台')
    
    # --- Sidebar Settings ---
    st.sidebar.subheader("OpenAI 設定 (選用)")
    api_key_input = st.sidebar.text_input(
        "輸入您的 OpenAI API Key 啟用 AI 問答：",
        type="password",
        key="openai_api_key_input",
        value=st.session_state.get('openai_api_key', ''),
        help="輸入有效金鑰並成功完成分析後，下方將出現 AI 對話框。"
    )

    # Update session state when input changes
    if api_key_input:
        st.session_state.openai_api_key = api_key_input
    else:
        st.session_state.openai_api_key = None
        st.session_state.show_chat = False
        st.session_state.chat_history = []

    st.sidebar.divider()

    # --- IRT Simulation Settings ---
    st.sidebar.subheader("IRT 模擬設定")
    st.session_state.initial_theta_q = st.sidebar.number_input(
        "Q 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_q, 
        step=0.1,
        key="theta_q_input"
    )
    st.session_state.initial_theta_v = st.sidebar.number_input(
        "V 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_v, 
        step=0.1,
        key="theta_v_input"
    )
    st.session_state.initial_theta_di = st.sidebar.number_input(
        "DI 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_di, 
        step=0.1,
        key="theta_di_input"
    )

    # --- Manual IRT Adjustment Inputs in Sidebar ---
    st.sidebar.markdown("#### 手動調整題目正確性 (僅影響IRT模擬)")
    
    # Quant
    st.sidebar.markdown("##### 計量 (Quant)")
    st.session_state.q_incorrect_to_correct_qns = st.sidebar.text_input(
        "Q 由錯改對題號", 
        value=st.session_state.q_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="q_i_to_c_input"
    )
    st.session_state.q_correct_to_incorrect_qns = st.sidebar.text_input(
        "Q 由對改錯題號", 
        value=st.session_state.q_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="q_c_to_i_input"
    )

    # Verbal
    st.sidebar.markdown("##### 語文 (Verbal)")
    st.session_state.v_incorrect_to_correct_qns = st.sidebar.text_input(
        "V 由錯改對題號", 
        value=st.session_state.v_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="v_i_to_c_input"
    )
    st.session_state.v_correct_to_incorrect_qns = st.sidebar.text_input(
        "V 由對改錯題號", 
        value=st.session_state.v_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="v_c_to_i_input"
    )

    # Data Insights (DI)
    st.sidebar.markdown("##### 資料洞察 (DI)")
    st.session_state.di_incorrect_to_correct_qns = st.sidebar.text_input(
        "DI 由錯改對題號", 
        value=st.session_state.di_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="di_i_to_c_input"
    )
    st.session_state.di_correct_to_incorrect_qns = st.sidebar.text_input(
        "DI 由對改錯題號", 
        value=st.session_state.di_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="di_c_to_i_input"
    )
    st.sidebar.divider() # Add a divider after these inputs
    
    # --- Data Input Section ---
    input_dfs, validation_errors, data_source_types = setup_input_tabs(preprocess_helpers)
    
    # Store in session state
    st.session_state.input_dfs = input_dfs
    st.session_state.validation_errors = validation_errors
    st.session_state.data_source_types = data_source_types
    
    # Combine Input Data
    df_combined_input, loaded_subjects, valid_input_dfs = combine_input_data(input_dfs, SUBJECTS)
    
    # Check if any validation errors occurred across all tabs
    any_validation_errors = any(bool(warnings) for warnings in validation_errors.values())
    
    # Display Analysis Button
    button_clicked, button_disabled, button_message = display_analysis_button(
        df_combined_input, 
        any_validation_errors, 
        input_dfs,
        SUBJECTS
    )
    
    # --- Analysis Execution Block ---
    if button_clicked and not button_disabled:
        # This is a new analysis request
        reset_session_for_new_upload() # Clear previous *results* and *completion status*
        st.session_state.analysis_run = True # Mark that analysis should run *now*
                                             # This flag will persist for the current script run
                                             # to ensure results are displayed.
        st.session_state.diagnosis_complete = False # Ensure it starts as not complete

        if df_combined_input is not None:
            st.header("2. 執行 IRT 模擬與診斷")
            run_analysis(df_combined_input) # This will update diagnosis_complete and analysis_error
        else:
            # If there's no data, then analysis didn't really "run" in a meaningful way.
            st.session_state.analysis_run = False 
            st.warning("沒有合併的數據可以分析，無法啟動分析。")
    
    # Note: The elif block that was here for `st.session_state.analysis_run and not st.session_state.diagnosis_complete`
    # has been removed as its primary utility was with st.rerun() for iterative display on slow steps.
    # With the current synchronous call to run_analysis, this simplified structure should be sufficient.
    
    # --- Results Display ---
    # Show results if analysis_run was set to True by the button click (meaning an analysis was attempted)
    if st.session_state.analysis_run:
        display_results()
    
    # --- Chat Interface ---
    display_chat_interface(st.session_state)

if __name__ == "__main__":
    main() 