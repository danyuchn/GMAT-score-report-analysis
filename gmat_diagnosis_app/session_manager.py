# -*- coding: utf-8 -*-
"""Manages session state for the GMAT Diagnosis App."""
import streamlit as st
from gmat_diagnosis_app.i18n import set_language, get_language

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
        'master_key': None,
        'show_chat': False,
        'chat_history': [], # List of dicts: {"role": "user/assistant", "content": "..."}
        'chat_history_backup': [], # 備份聊天歷史，確保持久化
        # --- Manual IRT Adjustment Inputs ---
        'q_incorrect_to_correct_qns': '',
        'q_correct_to_incorrect_qns': '',
        'v_incorrect_to_correct_qns': '',
        'v_correct_to_incorrect_qns': '',
        'di_incorrect_to_correct_qns': '',
        'di_correct_to_incorrect_qns': '',
        # --- Editable Diagnosis Labels State ---
        'original_processed_df': None, # Backup of the original processed_df
        'editable_diagnostic_df': None, # Editable copy for diagnosis label modification
        'ai_prompts_need_regeneration': False,
        # --- Language State ---
        'current_language': 'zh-TW', # Default to Traditional Chinese
        'language_changed': False # Track if language has been changed
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize the i18n system with the current language
    if 'current_language' in st.session_state:
        set_language(st.session_state.current_language)
    
    # 保持聊天歷史持久化
    if 'chat_history' in st.session_state and 'chat_history_backup' in st.session_state:
        # 如果備份中有更多消息，使用備份恢復
        if len(st.session_state.chat_history_backup) > len(st.session_state.chat_history):
            import logging
            logging.info(f"從備份恢復聊天歷史 (備份長度: {len(st.session_state.chat_history_backup)}, 當前長度: {len(st.session_state.chat_history)})")
            st.session_state.chat_history = st.session_state.chat_history_backup.copy()
    
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
    
    # Reset editable diagnosis states
    st.session_state.original_processed_df = None
    st.session_state.ai_prompts_need_regeneration = False
    
    # 備份當前聊天歷史
    if 'chat_history' in st.session_state and st.session_state.chat_history:
        st.session_state.chat_history_backup = st.session_state.chat_history.copy()
    # 重置聊天歷史
    st.session_state.chat_history = []
    
    # 不重置分數相關設定
    # st.session_state.total_score
    # st.session_state.q_score
    # st.session_state.v_score
    # st.session_state.di_score
    # 但重置圖表
    st.session_state.total_plot = None
    
# 添加新函數，專門用於確保聊天歷史持久化
def ensure_chat_history_persistence():
    """確保聊天歷史在會話間持久化"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    # 如果備份存在且比當前歷史更長，則恢復備份
    if 'chat_history_backup' in st.session_state and len(st.session_state.chat_history_backup) > len(st.session_state.chat_history):
        import logging
        logging.info(f"恢復聊天歷史: 從備份中恢復了 {len(st.session_state.chat_history_backup)} 條消息")
        st.session_state.chat_history = st.session_state.chat_history_backup.copy()
    
    # 每次調用時都更新備份
    st.session_state.chat_history_backup = st.session_state.chat_history.copy()

# Helper function to update session state after analysis (called from diagnosis_manager.py)
# This is not part of the original file, but it's a good place to ensure original_processed_df is set.
# We'll call this from diagnosis_manager.py instead of directly modifying session state there.
def set_analysis_results(processed_df, report_dict, final_thetas, theta_plots, consolidated_report):
    st.session_state.processed_df = processed_df
    if processed_df is not None:
        st.session_state.original_processed_df = processed_df.copy() # Save a copy for reset
    else:
        st.session_state.original_processed_df = None
    st.session_state.report_dict = report_dict
    st.session_state.final_thetas = final_thetas
    st.session_state.theta_plots = theta_plots
    st.session_state.consolidated_report_text = consolidated_report # Assuming this holds the text for display
    st.session_state.diagnosis_complete = True
    st.session_state.error_message = None
    st.session_state.analysis_error = False
    st.balloons()

def set_analysis_error(error_message, theta_plots=None):
    st.session_state.diagnosis_complete = False
    st.session_state.analysis_error = True
    st.session_state.error_message = error_message
    if theta_plots and isinstance(theta_plots, dict):
        st.session_state.theta_plots = theta_plots
    else:
        st.session_state.theta_plots = {}
    # Ensure processed_df related states are cleared on error
    st.session_state.processed_df = None
    st.session_state.original_processed_df = None 