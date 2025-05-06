"""
輸入標籤頁模組
提供數據輸入和標籤頁界面的功能
"""

import streamlit as st
from gmat_diagnosis_app.utils.data_processing import process_subject_tab
from gmat_diagnosis_app.constants.config import (
    SUBJECTS,
    BASE_RENAME_MAP,
    MAX_FILE_SIZE_BYTES, 
    REQUIRED_ORIGINAL_COLS
)

def setup_input_tabs(preprocess_helpers_module):
    """設置輸入標籤頁，處理數據輸入和驗證"""
    st.header("1. 上傳或貼上各科成績單")
    st.info(f"提示：上傳的 CSV 檔案大小請勿超過 {MAX_FILE_SIZE_BYTES // (1024*1024)}MB。貼上的資料沒有此限制。")

    tab_q, tab_v, tab_di = st.tabs(["Quantitative (Q)", "Verbal (V)", "Data Insights (DI)"])
    tabs = {'Q': tab_q, 'V': tab_v, 'DI': tab_di}

    # 獲取驗證和建議無效題目的函數
    suggest_invalid_questions = preprocess_helpers_module.suggest_invalid_questions
    
    # Process each subject tab using the refactored function
    from gmat_diagnosis_app.utils.validation import validate_dataframe
    
    input_dfs = {}
    validation_errors = {}
    data_source_types = {}
    
    for subject in SUBJECTS:
        tab_container = tabs[subject]
        with tab_container:
            processed_df, source_type, warnings = process_subject_tab(
                subject, 
                tab_container, 
                BASE_RENAME_MAP, 
                MAX_FILE_SIZE_BYTES, 
                suggest_invalid_questions, 
                validate_dataframe,
                REQUIRED_ORIGINAL_COLS
            )
            
            # Store results in session state immediately after processing each tab
            input_dfs[subject] = processed_df  # Will be None if error/no data
            validation_errors[subject] = warnings
            if source_type:
                data_source_types[subject] = source_type
    
    return input_dfs, validation_errors, data_source_types

def combine_input_data(input_dfs, SUBJECTS):
    """Combine valid input DataFrames from all subjects"""
    # Filter out subjects where df is None (error, no data, or validation failed)
    valid_input_dfs = {subj: df for subj, df in input_dfs.items() if df is not None}
    loaded_subjects = list(valid_input_dfs.keys())  # Subjects with valid dataframes

    df_combined_input = None
    if len(valid_input_dfs) == len(SUBJECTS):  # Only combine if ALL subjects are valid
        try:
            import pandas as pd
            df_list = [valid_input_dfs[subj] for subj in SUBJECTS]  # Ensure consistent order
            df_combined_input = pd.concat(df_list, ignore_index=True)
            # Basic check after concat
            if df_combined_input.empty or 'question_position' not in df_combined_input.columns or df_combined_input['question_position'].isnull().any():
                st.error("合併後的資料為空或缺少有效的 'question_position'，無法繼續。")
                df_combined_input = None  # Invalidate combination
        except Exception as e:
            st.error(f"合併已驗證的輸入資料時發生錯誤: {e}")
            df_combined_input = None

    return df_combined_input, loaded_subjects, valid_input_dfs

def display_analysis_button(df_combined_input, any_validation_errors, input_dfs, SUBJECTS):
    """Display the analysis trigger button and determine its state"""
    st.divider()
    
    all_subjects_loaded_and_valid = (len([subj for subj, df in input_dfs.items() if df is not None]) == len(SUBJECTS)) and (df_combined_input is not None)

    # Determine button state
    button_disabled = True
    button_message = ""

    if all_subjects_loaded_and_valid:
        button_disabled = False  # Enable button
    elif any_validation_errors:
        button_message = "部分科目數據驗證失敗，請修正上方標示的錯誤後再試。"
        st.error(button_message)
    else:  # Not all subjects loaded or combined DF failed
        subjects_actually_loaded = [subj for subj, df in input_dfs.items() if df is not None]
        missing_subjects = [subj for subj in SUBJECTS if subj not in subjects_actually_loaded]
        if missing_subjects:
            button_message = f"請確保已為 {'、'.join(missing_subjects)} 科目提供有效數據。"
            st.warning(button_message, icon="⚠️")
        elif not input_dfs:  # No data attempted at all
            button_message = "請在上方分頁中為 Q, V, DI 三個科目上傳或貼上資料。"
            st.info(button_message)
        else:  # All attempted, but maybe combination failed or validation error cleared?
            button_message = "請檢查所有科目的數據是否已成功加載且無誤。"
            st.warning(button_message, icon="⚠️")
    
    return st.button("🔍 開始分析", type="primary", disabled=button_disabled, key="analyze_button"), button_disabled, button_message 