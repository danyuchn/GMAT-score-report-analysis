"""
輸入標籤頁模組
提供數據輸入和標籤頁界面的功能
"""

import streamlit as st
import pandas as pd
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

    tab_q, tab_v, tab_di, tab_total = st.tabs(["Quantitative (Q)", "Verbal (V)", "Data Insights (DI)", "Total"])
    tabs = {'Q': tab_q, 'V': tab_v, 'DI': tab_di, 'Total': tab_total}

    # 獲取驗證和建議無效題目的函數
    suggest_invalid_questions = preprocess_helpers_module.suggest_invalid_questions
    
    # Process each subject tab using the refactored function
    from gmat_diagnosis_app.utils.validation import validate_dataframe
    
    input_dfs = {}
    validation_errors = {}
    data_source_types = {}
    
    # 設置Total標籤頁
    with tab_total:
        st.subheader("使用滑竿選擇總分和各科級分")
        st.markdown("本功能可根據選擇的分數生成相應的百分位數和曲線圖")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 總分設定")
            total_score = st.slider(
                "GMAT總分 (205-805)",
                min_value=205,
                max_value=805,
                value=505,
                step=10,
                key="total_score_slider"
            )
            
            # 將選擇的分數存入session state
            if "total_score" not in st.session_state or st.session_state.total_score != total_score:
                st.session_state.total_score = total_score
        
        with col2:
            st.markdown("### 各科級分設定")
            q_score = st.slider(
                "Q科級分 (60-90)",
                min_value=60,
                max_value=90,
                value=75,
                step=1,
                key="q_score_slider"
            )
            
            v_score = st.slider(
                "V科級分 (60-90)",
                min_value=60,
                max_value=90,
                value=75,
                step=1,
                key="v_score_slider"
            )
            
            di_score = st.slider(
                "DI科級分 (60-90)",
                min_value=60,
                max_value=90,
                value=75,
                step=1,
                key="di_score_slider"
            )
            
            # 將各科級分存入session state
            if "q_score" not in st.session_state or st.session_state.q_score != q_score:
                st.session_state.q_score = q_score
            if "v_score" not in st.session_state or st.session_state.v_score != v_score:
                st.session_state.v_score = v_score
            if "di_score" not in st.session_state or st.session_state.di_score != di_score:
                st.session_state.di_score = di_score
        
        # 創建一個示例DataFrame以供顯示
        if st.button("確認分數設定", key="confirm_total_scores"):
            # 創建一個包含選定分數的DataFrame
            data = {
                'Score_Type': ['Total Score', 'Q Scaled Score', 'V Scaled Score', 'DI Scaled Score'],
                'Score': [total_score, q_score, v_score, di_score]
            }
            score_df = pd.DataFrame(data)
            
            # 將分數DataFrame存入session state
            st.session_state.score_df = score_df
            
            # 設置確認狀態標誌
            st.session_state.total_scores_confirmed = True
            
            # 顯示所選分數
            st.write("已選擇的分數:")
            st.dataframe(score_df, hide_index=True)
            
            # 存入input_dfs以供後續處理
            # 注意：這裡創建一個特殊格式的DataFrame，以便後續處理
            total_df = pd.DataFrame({
                'question_position': [1],  # 虛擬的題號
                'is_manually_invalid': [False],
                'Subject': ['Total'],
                'total_score': [total_score],
                'q_score': [q_score],
                'v_score': [v_score],
                'di_score': [di_score]
            })
            
            input_dfs['Total'] = total_df
            validation_errors['Total'] = []
            data_source_types['Total'] = "滑竿設定"
        
        # 如果之前已經確認過分數，重新創建Total的DataFrame
        elif st.session_state.get('total_scores_confirmed', False):
            total_df = pd.DataFrame({
                'question_position': [1],  # 虛擬的題號
                'is_manually_invalid': [False],
                'Subject': ['Total'],
                'total_score': [total_score],
                'q_score': [q_score],
                'v_score': [v_score],
                'di_score': [di_score]
            })
            
            input_dfs['Total'] = total_df
            validation_errors['Total'] = []
            data_source_types['Total'] = "滑竿設定"
            
            # 顯示確認狀態
            st.success("✅ 分數設定已確認")
            if 'score_df' in st.session_state:
                st.write("已選擇的分數:")
                st.dataframe(st.session_state.score_df, hide_index=True)
    
    # 處理其他主題標籤頁
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
    # 調試信息：打印輸入的數據框字典
    # st.write("調試：輸入的數據框") # Removed
    # for subj, df in input_dfs.items(): # Removed block
    #     if df is not None:
    #         st.write(f"科目 {subj}: 形狀 {df.shape}, 索引 {type(df.index)}, 索引範圍 {df.index.min()} - {df.index.max()}") # Removed
    #         if not df.index.is_unique:
    #             st.error(f"警告：科目 {subj} 的數據框有重複索引！") # Kept error as it might be useful
    #             st.write(f"重複索引值：{df.index[df.index.duplicated()].tolist()}") # Kept error detail
    
    # Filter out subjects where df is None (error, no data, or validation failed)
    valid_input_dfs = {subj: df for subj, df in input_dfs.items() if df is not None and subj in SUBJECTS}
    loaded_subjects = list(valid_input_dfs.keys())  # Subjects with valid dataframes
    
    # 調試信息：打印有效的數據框
    # st.write(f"有效科目: {loaded_subjects}") # Removed
    
    # 將Total頁籤的數據單獨存儲，不與其他科目合併
    if 'Total' in input_dfs and input_dfs['Total'] is not None:
        st.session_state.total_data = input_dfs['Total']
        # st.write("已保存Total數據到session state") # Removed

    df_combined_input = None
    if len(valid_input_dfs) == len(SUBJECTS):  # Only combine if ALL subjects are valid
        try:
            # 調試：更詳細地檢查每個數據框
            # st.write("準備合併的數據框詳情:") # Removed
            df_list = []
            
            for subj in SUBJECTS:
                if subj in valid_input_dfs:
                    df = valid_input_dfs[subj]
                    # st.write(f"科目 {subj} 詳情:") # Removed block
                    # st.write(f"  - 形狀: {df.shape}") # Removed
                    # st.write(f"  - 列名: {df.columns.tolist()}") # Removed
                    # st.write(f"  - 索引類型: {type(df.index)}") # Removed
                    # st.write(f"  - 索引是否唯一: {df.index.is_unique}") # Removed
                    
                    # 先重設索引，確保沒有重複索引
                    temp_df = df.copy()

                    # Check for and remove duplicate columns
                    if temp_df.columns.has_duplicates:
                        duplicated_cols = temp_df.columns[temp_df.columns.duplicated(keep=False)].unique().tolist()
                        st.warning(f"科目 {subj} 發現重複欄位名稱: {duplicated_cols}. 將只保留每個欄位的第一次出現。")
                        temp_df = temp_df.loc[:, ~temp_df.columns.duplicated(keep='first')]
                        # st.write(f"  - 去除重複欄位後列名: {temp_df.columns.tolist()}") # Removed
                        # st.write(f"  - 去除重複欄位後形狀: {temp_df.shape}") # Removed
                    
                    temp_df = temp_df.reset_index(drop=True)
                    # st.write(f"  - 重設索引後形狀: {temp_df.shape}") # Removed
                    
                    df_list.append(temp_df)
            
            # 使用重設過索引的DataFrame進行合併
            # st.write(f"開始合併 {len(df_list)} 個數據框...") # Removed
            
            # 嘗試使用不同的合併方法
            try:
                # 方法1：使用concat並顯式指定ignore_index
                df_combined_input = pd.concat(df_list, ignore_index=True)
                # st.write("合併方法1成功") # Removed
            except Exception as e1:
                st.error(f"合併方法1失敗: {e1}") # Kept error
                try:
                    # 方法2：逐個合併
                    df_combined_input = df_list[0].copy() if df_list else None
                    if len(df_list) > 1:
                        for i in range(1, len(df_list)):
                            df_combined_input = pd.concat([df_combined_input, df_list[i]], ignore_index=True)
                    # st.write("合併方法2成功") # Removed
                except Exception as e2:
                    st.error(f"合併方法2失敗: {e2}") # Kept error
                    # 方法3：使用空DataFrame作為基礎進行合併
                    try:
                        empty_df = pd.DataFrame()
                        df_combined_input = empty_df
                        for df in df_list:
                            df_combined_input = pd.concat([df_combined_input, df], ignore_index=True)
                        # st.write("合併方法3成功") # Removed
                    except Exception as e3:
                        st.error(f"所有合併方法都失敗了: {e3}") # Kept error
            
            # 顯示合併結果
            # if df_combined_input is not None: # Removed block
                # st.write(f"合併後的數據框形狀: {df_combined_input.shape}") # Removed
                # st.write(f"合併後的數據框列: {df_combined_input.columns.tolist()}") # Removed
            
            # Basic check after concat
            if df_combined_input is None or df_combined_input.empty:
                st.error("合併後的資料為空")
                df_combined_input = None  # Invalidate combination
            elif 'question_position' not in df_combined_input.columns:
                st.error("合併後的資料缺少 'question_position' 列")
                df_combined_input = None  # Invalidate combination
            elif df_combined_input['question_position'].isnull().any():
                st.error("合併後的資料中 'question_position' 有空值")
                df_combined_input = None  # Invalidate combination
        except Exception as e:
            st.error(f"合併已驗證的輸入資料時發生錯誤: {e}")
            # 顯示更詳細的錯誤信息
            import traceback
            st.code(traceback.format_exc())
            df_combined_input = None

    return df_combined_input, loaded_subjects, valid_input_dfs

def display_analysis_button(df_combined_input, any_validation_errors, input_dfs, SUBJECTS):
    """Display the analysis trigger button and determine its state"""
    st.divider()
    
    all_subjects_loaded_and_valid = (len([subj for subj, df in input_dfs.items() if df is not None and subj in SUBJECTS]) == len(SUBJECTS)) and (df_combined_input is not None)
    
    # 檢查時間壓力評估是否已填寫
    time_pressure_keys_filled = True
    missing_time_pressure_subjects = []
    for subject in SUBJECTS:
        subject_key = subject.lower()
        time_pressure_key = f"{subject_key}_time_pressure"
        if time_pressure_key not in st.session_state:
            time_pressure_keys_filled = False
            missing_time_pressure_subjects.append(subject)

    # 檢查Total頁籤的「確認分數設定」是否已按下
    total_scores_confirmed = st.session_state.get('total_scores_confirmed', False)

    # Determine button state
    button_disabled = True
    button_message = ""

    if all_subjects_loaded_and_valid and time_pressure_keys_filled and total_scores_confirmed:
        button_disabled = False  # Enable button
    elif not total_scores_confirmed:
        button_message = "請先在「Total (總分與百分位)」頁籤中點擊「確認分數設定」按鈕。"
        st.warning(button_message, icon="⚠️")
    elif not time_pressure_keys_filled:
        button_message = f"請為 {'、'.join(missing_time_pressure_subjects)} 科目填寫時間壓力評估（必填）。"
        st.warning(button_message, icon="⚠️")
    elif any_validation_errors:
        button_message = "部分科目數據驗證失敗，請修正上方標示的錯誤後再試。"
        st.error(button_message)
    else:  # Not all subjects loaded or combined DF failed
        subjects_actually_loaded = [subj for subj, df in input_dfs.items() if df is not None and subj in SUBJECTS]
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
    
    return st.button("開始分析", type="primary", disabled=button_disabled, key="analyze_button"), button_disabled, button_message 