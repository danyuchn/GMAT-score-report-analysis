# -*- coding: utf-8 -*-
"""Manages session state for the GMAT Diagnosis App."""
import streamlit as st

def init_session_state():
    """Initialize session state variables with default values"""
    defaults = {
        'analysis_run': False,
        'diagnosis_complete': False, # Track if diagnosis step finished
        'report_dict': {},
        'ai_consolidated_report': None, # NEW: For consolidated AI report
        'final_thetas': {},
        'processed_df': None, # Store the final DataFrame after processing+diagnosis
        'error_message': None,
        'analysis_error': False, # Initialize analysis_error flag
        'input_dfs': {}, # Store loaded & validated DFs from tabs
        'validation_errors': {}, # Store validation errors per subject
        'data_source_types': {}, # Store how data was loaded ('File Upload' or 'Pasted Data')
        'theta_plots': {}, # Store plots for display
        # --- Total Score State ---
        'total_score': 505, # 默認總分505
        'q_score': 75, # 默認Q科級分75
        'v_score': 75, # 默認V科級分75
        'di_score': 75, # 默認DI科級分75
        'score_df': None, # 存儲分數DataFrame
        'total_data': None, # 存儲Total頁籤的數據
        'total_plot': None, # 存儲Total頁籤的圖表
        # --- AI Chat State ---
        'openai_api_key': None,
        'show_chat': False,
        'chat_history': [], # List of dicts: {"role": "user/assistant", "content": "..."}
        # --- Manual IRT Adjustment Inputs ---
        'q_incorrect_to_correct_qns': '',
        'q_correct_to_incorrect_qns': '',
        'v_incorrect_to_correct_qns': '',
        'v_correct_to_incorrect_qns': '',
        'di_incorrect_to_correct_qns': '',
        'di_correct_to_incorrect_qns': ''
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Store initial thetas in session state to persist them
    if 'initial_theta_q' not in st.session_state: st.session_state.initial_theta_q = 0.0
    if 'initial_theta_v' not in st.session_state: st.session_state.initial_theta_v = 0.0
    if 'initial_theta_di' not in st.session_state: st.session_state.initial_theta_di = 0.0

def reset_session_for_new_upload():
    """Reset session state for new data upload or analysis start"""
    # st.session_state.analysis_run = False # DO NOT reset this here. It's controlled by the main flow.
    st.session_state.diagnosis_complete = False
    st.session_state.report_dict = {}
    st.session_state.ai_consolidated_report = None
    st.session_state.final_thetas = {}
    st.session_state.processed_df = None
    st.session_state.error_message = None
    st.session_state.analysis_error = False
    st.session_state.theta_plots = {}
    st.session_state.show_chat = False
    st.session_state.chat_history = []
    # 不重置分數相關設定
    # st.session_state.total_score
    # st.session_state.q_score
    # st.session_state.v_score
    # st.session_state.di_score
    # 但重置圖表
    st.session_state.total_plot = None 