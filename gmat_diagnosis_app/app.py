# -*- coding: utf-8 -*- # Ensure UTF-8 encoding for comments/strings
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

import sys
import os
import io
import pandas as pd
import numpy as np
import logging
import openai
import plotly.graph_objects as go
import datetime

# --- Project Path Setup (MUST BE FIRST) ---
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # Handle cases where __file__ is not defined (e.g., interactive environments)
    project_root = os.getcwd()  # Fallback

# Import i18n functions after path setup
from gmat_diagnosis_app.i18n import translate as t

# Call set_page_config as early as possible
st.set_page_config(
    page_title=t("page_title"),
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Module Imports ---
try:
    # Import custom modules for core logic
    from gmat_diagnosis_app import preprocess_helpers # Ensure the module itself is imported for setup_input_tabs
    # from gmat_diagnosis_app import irt_module as irt # Moved to analysis_orchestrator
    # from gmat_diagnosis_app.irt import probability_correct, item_information, estimate_theta, initialize_question_bank, simulate_cat_exam
    # from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q # Moved
    
    # Import our modularized components
    from gmat_diagnosis_app.constants.config import (
        SUBJECTS, # Retained: Used in main for iterating tabs and processing
        # MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, # Removed: Likely used within setup_input_tabs
        # BANK_SIZE, RANDOM_SEED, SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS, # Removed: Likely used in analysis_orchestrator or deeper
        BASE_RENAME_MAP # Retained: Used in main for sample data processing
        # REQUIRED_ORIGINAL_COLS, EXCEL_COLUMN_MAP # Removed: Likely used within setup_input_tabs or preprocess_helpers
    )
    # from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Removed: Likely used in analysis_orchestrator or deeper
    # from gmat_diagnosis_app.utils.validation import validate_dataframe
    # from gmat_diagnosis_app.utils.data_processing import process_subject_tab
    # from gmat_diagnosis_app.utils.styling import apply_styles
    # from gmat_diagnosis_app.utils.excel_utils import to_excel # Removed
    from gmat_diagnosis_app.services.openai_service import ( # Retained: get_chat_context, get_openai_response might be used by a chat interface if it were called
        # summarize_report_with_openai, generate_ai_consolidated_report, # Removed: Assumed handled by orchestrator/display
        get_chat_context, get_openai_response # Retained cautiously, though display_chat_interface is not called
    )
    # from gmat_diagnosis_app.services.plotting_service import create_theta_plot
    from gmat_diagnosis_app.ui.results_display import display_results # Removed display_subject_results
    # from gmat_diagnosis_app.ui.chat_interface import display_chat_interface # Removed: Not called
    from gmat_diagnosis_app.ui.input_tabs import setup_input_tabs, combine_input_data, display_analysis_button
    from gmat_diagnosis_app.session_manager import init_session_state, reset_session_for_new_upload, ensure_chat_history_persistence
    from gmat_diagnosis_app.analysis_orchestrator import run_analysis # Added import
    from gmat_diagnosis_app.services.csv_data_service import add_gmat_performance_record, GMAT_PERFORMANCE_HEADERS, add_subjective_report_record # Added for CSV export and new function
    
    # Import the new analysis helpers - These are likely used by analysis_orchestrator, not directly here.
    # from gmat_diagnosis_app.analysis_helpers.time_pressure_analyzer import calculate_time_pressure, calculate_and_apply_invalid_logic # Removed
    # from gmat_diagnosis_app.analysis_helpers.simulation_manager import run_simulation, prepare_dataframes_for_diagnosis # Removed
    # from gmat_diagnosis_app.analysis_helpers.diagnosis_manager import run_diagnosis, update_session_state_after_analysis # Removed
    
except ImportError as e:
    # Add fallback for when translation is not available
    try:
        st.error(t("import_error_message").format(e))
    except:
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

# Callback function for loading sample data
def load_sample_data_callback():
    """Sets session state for sample data to be pasted into text areas."""
    sample_q_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	2.3	Correct	Algebra	REAL	Equal/Unequal/ALG
2	4.8	Correct	Algebra	REAL	Rates/Ratio/Percent
3	1.3	Correct	Arithmetic	REAL	Equal/Unequal/ALG
4	2.2	Incorrect	Arithmetic	REAL	Value/Order/Factors
5	0.8	Correct	Arithmetic	REAL	Rates/Ratio/Percent
6	3.5	Correct	Algebra	REAL	Rates/Ratio/Percent
7	1.5	Correct	Algebra	REAL	Equal/Unequal/ALG
8	1.5	Correct	Arithmetic	REAL	Rates/Ratio/Percent
9	1.3	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
10	5.4	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
11	2.6	Incorrect	Algebra	PURE	Equal/Unequal/ALG
12	4.3	Correct	Arithmetic	PURE	Rates/Ratio/Percent
13	1.6	Incorrect	Arithmetic	PURE	Counting/Sets/Series/Prob/Stats
14	0.9	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
15	0.7	Correct	Algebra	PURE	Value/Order/Factors
16	4.6	Correct	Algebra	PURE	Value/Order/Factors
17	2.1	Correct	Algebra	PURE	Counting/Sets/Series/Prob/Stats
18	0.7	Correct	Arithmetic	PURE	Equal/Unequal/ALG
19	0.7	Correct	Arithmetic	PURE	Rates/Ratio/Percent
20	0.8	Incorrect	Arithmetic	PURE	Value/Order/Factors
21	0.9	Correct	Arithmetic	PURE	Value/Order/Factors"""

    sample_v_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	1.5	Correct	N/A	Critical Reasoning	Plan/Construct
2	3.6	Correct	N/A	Critical Reasoning	Plan/Construct
3	3	Correct	N/A	Reading Comprehension	Identify Stated Idea
4	1	Incorrect	N/A	Reading Comprehension	Identify Inferred Idea
5	3.7	Incorrect	N/A	Reading Comprehension	Identify Inferred Idea
6	1.7	Incorrect	N/A	Critical Reasoning	Analysis/Critique
7	2.7	Correct	N/A	Reading Comprehension	Identify Inferred Idea
8	1	Correct	N/A	Reading Comprehension	Identify Stated Idea
9	1.6	Correct	N/A	Reading Comprehension	Identify Inferred Idea
10	2.2	Correct	N/A	Critical Reasoning	Plan/Construct
11	4.4	Correct	N/A	Reading Comprehension	Identify Inferred Idea
12	0.6	Correct	N/A	Reading Comprehension	Identify Stated Idea
13	2.3	Correct	N/A	Reading Comprehension	Identify Inferred Idea
14	0.6	Correct	N/A	Reading Comprehension	Identify Stated Idea
15	2.4	Incorrect	N/A	Critical Reasoning	Analysis/Critique
16	2.3	Incorrect	N/A	Critical Reasoning	Analysis/Critique
17	2.8	Incorrect	N/A	Critical Reasoning	Plan/Construct
18	1.3	Correct	N/A	Critical Reasoning	Analysis/Critique
19	0.7	Correct	N/A	Critical Reasoning	Analysis/Critique
20	1.9	Incorrect	N/A	Critical Reasoning	Analysis/Critique
21	1.4	Incorrect	N/A	Critical Reasoning	Analysis/Critique
22	1	Correct	N/A	Critical Reasoning	Plan/Construct
23	1.2	Incorrect	N/A	Critical Reasoning	Plan/Construct"""

    sample_di_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	1.5	Correct	Math Related	Data Sufficiency	N/A
2	1.8	Correct	Math Related	Data Sufficiency	N/A
3	3.1	Correct	Non-Math Related	Two-part analysis	N/A
4	4.2	Correct	Math Related	Multi-source reasoning	N/A
5	1.9	Incorrect	Non-Math Related	Multi-source reasoning	N/A
6	1	Incorrect	Math Related	Multi-source reasoning	N/A
7	3.7	Incorrect	Non-Math Related	Data Sufficiency	N/A
8	2.5	Incorrect	Non-Math Related	Graph and Table	N/A
9	5.9	Correct	Non-Math Related	Two-part analysis	N/A
10	2.7	Incorrect	Math Related	Graph and Table	N/A
11	2.1	Incorrect	Math Related	Data Sufficiency	N/A
12	1.7	Incorrect	Math Related	Data Sufficiency	N/A
13	2.8	Correct	Non-Math Related	Graph and Table	N/A
14	1.5	Incorrect	Math Related	Data Sufficiency	N/A
15	2	Incorrect	Non-Math Related	Graph and Table	N/A
16	1.2	Incorrect	Non-Math Related	Data Sufficiency	N/A
17	0.4	Incorrect	Math Related	Two-part analysis	N/A
18	3.5	Incorrect	Math Related	Graph and Table	N/A
19	0.1	Incorrect	Math Related	Two-part analysis	N/A
20	1.2	Incorrect	Math Related	Graph and Table	N/A"""

    st.session_state.q_paster = sample_q_data
    st.session_state.v_paster = sample_v_data
    st.session_state.di_paster = sample_di_data
    
    if 'example_data_loaded' in st.session_state:
        del st.session_state['example_data_loaded']
    if 'example_data' in st.session_state:
        del st.session_state['example_data']
    
    st.session_state.sample_data_pasted_success = True

# --- Main Application ---
def main():
    """Main application entry point"""
    # Set page configuration (removed duplicate)
    # st.set_page_config( # This block will be removed
    #     page_title="GMAT Score Analysis Platform",
    #     page_icon="📊",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )
    
    # Initialize session state
    init_session_state()
    
    # Ensure chat history persistence
    ensure_chat_history_persistence()
    
    # Apply custom CSS styling
    from gmat_diagnosis_app.utils.styling import apply_custom_css
    apply_custom_css()

    # Import i18n functions
    from gmat_diagnosis_app.i18n import translate

    # Initialize the success message flag for sample data pasting if it doesn't exist
    if 'sample_data_pasted_success' not in st.session_state:
        st.session_state.sample_data_pasted_success = False
    
    # Page title and introduction area
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        # {translate('main_title')}
        ### {translate('main_subtitle')}
        """)
    
    # Create main navigation
    main_tabs = st.tabs([translate('data_input_tab'), translate('results_view_tab')])
    
    with main_tabs[0]:  # Data input and analysis tab
        # Brief usage guide (core steps)
        with st.expander(translate('quick_guide'), expanded=False):
            st.markdown(f"""
            1. {t('preparation_guide_step1')}
            2. {t('preparation_guide_step2')}
            3. {t('preparation_guide_step3')}
            4. {t('preparation_guide_step4')}
            5. {t('preparation_guide_step5')}
            """)
            
        # --- Disclaimer & Tutorial Links ---
        disclaimer_warning = st.expander(t('disclaimer_title'), expanded=False)
        with disclaimer_warning:
            st.markdown(f"""
            {t('disclaimer_content_1')}

            {t('disclaimer_content_2')}

            {t('disclaimer_item_1')}
            {t('disclaimer_item_2')}

            {t('disclaimer_recommendation')}

            {t('disclaimer_professional_advice')}

            ---

            {t('data_usage_title')}

            {t('data_collection_consent')}
            {t('deidentification_responsibility')}
            {t('feedback_instruction')}
            """)
            
        tutorial_help = st.expander(t('tutorial_title'), expanded=False)
        with tutorial_help:
            st.markdown(f"""
            {t('tutorial_welcome_title')}

            {t('tutorial_section1_title')}

            {t('tutorial_section1_intro')}

            {t('tutorial_section1_point1')}
            {t('tutorial_section1_point2')}
            {t('tutorial_section1_point3')}
            {t('tutorial_section1_point4')}

            {t('tutorial_section2_title')}

            {t('tutorial_section2_quality_note')}

            {t('tutorial_section2_data_source')}
            {t('tutorial_section2_format_requirements')}
                {t('tutorial_section2_format_point1')}
                {t('tutorial_section2_format_point2')}
            {t('tutorial_section2_required_fields')}
                {t('tutorial_section2_common_fields')}
                    {t('tutorial_section2_common_field1')}
                    {t('tutorial_section2_common_field2')}
                    {t('tutorial_section2_common_field3')}
                {t('tutorial_section2_subject_fields')}
                    {t('tutorial_section2_content_domain')}
                        {t('tutorial_section2_content_domain_q')}
                        {t('tutorial_section2_content_domain_di')}
                    {t('tutorial_section2_question_type')}
                        {t('tutorial_section2_question_type_q')}
                        {t('tutorial_section2_question_type_v')}
                        {t('tutorial_section2_question_type_di')}
                    {t('tutorial_section2_fundamental_skills')}
                        {t('tutorial_section2_fundamental_skills_q')}
                        {t('tutorial_section2_fundamental_skills_v')}
            {t('tutorial_section2_deidentification_title')}
                {t('tutorial_section2_deidentification_warning')}
                {t('tutorial_section2_deidentification_responsibility')}

            {t('tutorial_section3_title')}

            {t('tutorial_section3_step1_title')}
                {t('tutorial_section3_step1_point1')}
                {t('tutorial_section3_step1_point2')}
                {t('tutorial_section3_step1_point3')}
            {t('tutorial_section3_step2_title')}
                {t('tutorial_section3_step2_point1')}
                {t('tutorial_section3_step2_point2')}
                {t('tutorial_section3_step2_point3')}
            {t('tutorial_section3_step3_title')}
                {t('tutorial_section3_step3_point1')}
                {t('tutorial_section3_step3_point2')}
            {t('tutorial_section3_step4_title')}
                {t('tutorial_section3_step4_point1')}
                {t('tutorial_section3_step4_point2')}
                {t('tutorial_section3_step4_point3')}

            {t('tutorial_section4_title')}

            {t('tutorial_section4_intro')}

            {t('tutorial_section4_subject_results')}
                {t('tutorial_section4_theta_plot')}
                {t('tutorial_section4_diagnostic_report')}
                    {t('tutorial_section4_report_point1')}
                    {t('tutorial_section4_report_point2')}
                    {t('tutorial_section4_report_point3')}
                    {t('tutorial_section4_report_point4')}
                    {t('tutorial_section4_report_point5')}
                    {t('tutorial_section4_report_point6')}
                {t('tutorial_section4_detailed_data')}
                {t('tutorial_section4_download')}
            {t('tutorial_section4_ai_summary')}
                {t('tutorial_section4_ai_summary_point1')}
                {t('tutorial_section4_ai_summary_point2')}
                {t('tutorial_section4_ai_summary_note')}

            {t('tutorial_section5_title')}

            {t('tutorial_section5_point1')}
            {t('tutorial_section5_point2')}
                {t('tutorial_section5_example1')}
                {t('tutorial_section5_example2')}
                {t('tutorial_section5_example3')}
                {t('tutorial_section5_example4')}
            {t('tutorial_section5_limitation')}

            {t('tutorial_section6_title')}

            {t('tutorial_section6_q1')}
                {t('tutorial_section6_a1')}
            {t('tutorial_section6_q2')}
                {t('tutorial_section6_a2')}
            {t('tutorial_section6_q3')}
                {t('tutorial_section6_a3')}
            {t('tutorial_section6_q4')}
                {t('tutorial_section6_a4')}
            """)
        
        st.divider()
        
        # --- Data Input Section ---
        input_dfs, validation_errors, data_source_types = setup_input_tabs(preprocess_helpers)
        
        # 檢查是否需要顯示範例數據
        if st.session_state.get('example_data_loaded', False) and st.session_state.get('example_data'):
            # 注入範例數據到input_dfs
            for subject in SUBJECTS:
                if subject in st.session_state['example_data']:
                    if input_dfs.get(subject) is None:  # 只有在尚未輸入數據時才注入
                        example_df = st.session_state['example_data'][subject].copy()
                        # 添加必要的列
                        example_df['is_manually_invalid'] = False
                        example_df['Subject'] = subject
                        
                        # 重設索引以避免潛在的索引問題
                        example_df = example_df.reset_index(drop=True)
                        
                        # 將原始數據重命名為標準化列名
                        rename_map = BASE_RENAME_MAP.copy()
                        if 'Question' in example_df.columns:
                            rename_map['Question'] = 'question_position'
                        if 'Response Time (Minutes)' in example_df.columns:
                            rename_map['Response Time (Minutes)'] = 'question_time'
                        if 'Performance' in example_df.columns:
                            rename_map['Performance'] = 'is_correct'
                            # 轉換Performance列為is_correct
                            example_df['is_correct'] = example_df['Performance'].apply(
                                lambda x: x == 'Correct' if isinstance(x, str) else bool(x)
                            )
                        
                        example_df.rename(columns=rename_map, inplace=True)
                        
                        input_dfs[subject] = example_df
                        validation_errors[subject] = []
                        data_source_types[subject] = t('data_source_label')
            
            # 清除標誌，避免重複加載
            st.session_state['example_data_loaded'] = False
        
        # Store in session state
        st.session_state.input_dfs = input_dfs
        st.session_state.validation_errors = validation_errors
        st.session_state.data_source_types = data_source_types
        
        # Combine Input Data
        df_combined_input, loaded_subjects, valid_input_dfs = combine_input_data(input_dfs, SUBJECTS)
        
        # Check if any validation errors occurred across all tabs
        any_validation_errors = any(bool(warnings) for warnings in validation_errors.values())
        
        # Display Analysis Button with improved styling
        st.divider()
        st.subheader(t("start_analysis_section"))
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
                with st.spinner(t("analysis_in_progress")):
                    # --- Add to CSV ---
                    records_to_add = []
                    # Generate a unique student_id for this upload session if not available
                    # For simplicity, using a fixed student_id for now, or derive from session
                    student_id_for_batch = st.session_state.get("student_id_for_upload", f"student_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
                    st.session_state.student_id_for_upload = student_id_for_batch # Store for potential reuse in the session
                    
                    test_date_for_batch = datetime.date.today().isoformat()

                    # Calculate per-section totals first
                    section_stats = {}
                    if 'Subject' in df_combined_input.columns and 'question_time' in df_combined_input.columns:
                        for subject_name, group in df_combined_input.groupby('Subject'):
                            if subject_name in SUBJECTS: # Process only Q, V, DI
                                # Ensure question_time is numeric before summing
                                numeric_times = pd.to_numeric(group['question_time'], errors='coerce')
                                section_stats[subject_name] = {
                                    'total_questions': len(group),
                                    'total_time': numeric_times.sum()
                                }

                    for index, row in df_combined_input.iterrows():
                        record = {}
                        gmat_section = row.get("Subject")
                        
                        # Skip if not a main GMAT section (e.g. 'Total' if it exists in df_combined_input)
                        if gmat_section not in SUBJECTS:
                            continue
                            
                        record["student_id"] = student_id_for_batch
                        # Create a unique test_instance_id for each section within the batch
                        record["test_instance_id"] = f"{student_id_for_batch}_{gmat_section}_{test_date_for_batch.replace('-', '')}_upload"
                        record["gmat_section"] = gmat_section
                        record["test_date"] = test_date_for_batch
                        
                        question_pos = row.get("question_position", index + 1)
                        record["question_id"] = f"{gmat_section}_{question_pos}_{test_date_for_batch.replace('-', '')}"
                        record["question_position"] = int(question_pos) if pd.notnull(question_pos) else index + 1
                        # Ensure question_time is numeric before converting to float
                        question_time_val = row.get("question_time", 0.0)
                        if isinstance(question_time_val, str):
                            question_time_val = pd.to_numeric(question_time_val, errors='coerce')
                        record["question_time_minutes"] = float(question_time_val) if pd.notnull(question_time_val) else 0.0
                        
                        is_correct_val = row.get("is_correct")
                        if isinstance(is_correct_val, bool):
                            record["is_correct"] = 1 if is_correct_val else 0
                        elif isinstance(is_correct_val, str):
                            record["is_correct"] = 1 if is_correct_val.lower() == 'correct' else 0
                        else:
                            record["is_correct"] = 0 # Default if unknown format
                            
                        # question_difficulty might not be present in uploaded data, default to 0 or a placeholder
                        record["question_difficulty"] = float(row.get("question_difficulty", 0.0)) 
                        record["question_type"] = str(row.get("question_type", ""))
                        record["question_fundamental_skill"] = str(row.get("question_fundamental_skill", ""))
                        record["content_domain"] = str(row.get("content_domain", ""))
                        
                        if gmat_section in section_stats:
                            record["total_questions_in_section"] = int(section_stats[gmat_section]['total_questions'])
                            # Safely convert total_time to float, handle NaN values
                            total_time_val = section_stats[gmat_section]['total_time']
                            record["total_section_time_minutes"] = float(total_time_val) if pd.notnull(total_time_val) else 0.0
                        else:
                            record["total_questions_in_section"] = 0 # Should not happen if Subject is Q,V,DI
                            record["total_section_time_minutes"] = 0.0

                        record["max_allowed_section_time_minutes"] = 45.0 # Standard or from config
                        
                        # Ensure all GMAT_PERFORMANCE_HEADERS are present, even if with None or default values, except record_timestamp
                        for header in GMAT_PERFORMANCE_HEADERS:
                            if header not in record and header != "record_timestamp":
                                record[header] = None 
                        records_to_add.append(record)
                    
                    if records_to_add:
                        if add_gmat_performance_record(records_to_add):
                            # st.toast(f"已成功將 {len(records_to_add)} 筆資料附加到 gmat_performance_data.csv", icon="✅") # This line will be commented out
                            pass # Add pass if commenting out the toast makes the block empty
                        else:
                            st.toast(t("csv_append_error"), icon="⚠️")
                    else:
                        st.toast(t("csv_append_no_data"), icon="ℹ️")
                    # --- End Add to CSV ---
                    
                    # --- 添加主觀時間壓力報告到 CSV ---
                    subjective_reports_added = 0
                    
                    for subject in SUBJECTS:
                        subject_key = subject.lower()
                        time_pressure_key = f"{subject_key}_time_pressure"
                        
                        if time_pressure_key in st.session_state:
                            time_pressure_value = int(st.session_state[time_pressure_key])
                            test_instance_id = f"{student_id_for_batch}_{subject}_{test_date_for_batch.replace('-', '')}_upload"
                            
                            # 創建主觀報告記錄
                            subjective_report = {
                                "student_id": student_id_for_batch,
                                "test_instance_id": test_instance_id,
                                "gmat_section": subject,
                                "subjective_time_pressure": time_pressure_value,
                                "report_collection_timestamp": datetime.datetime.now().isoformat()
                            }
                            
                            # 將報告寫入 CSV
                            if add_subjective_report_record(subjective_report):
                                subjective_reports_added += 1
                            else:
                                st.toast(t("subjective_report_error").format(subject), icon="⚠️")
                    
                    if subjective_reports_added > 0:
                        pass # 成功添加報告
                    # --- 添加主觀時間壓力報告到 CSV 結束 ---

                    run_analysis(df_combined_input) # This will update diagnosis_complete and analysis_error
                
                if st.session_state.diagnosis_complete:
                    st.success(t("analysis_complete_message"))
            else:
                # If there's no data, then analysis didn't really "run" in a meaningful way.
                st.session_state.analysis_run = False 
                st.error(t("no_data_to_analyze"))
    
    with main_tabs[1]:  # 結果查看標籤頁
        if st.session_state.get("diagnosis_complete", False):
            display_results()
        else:
            # 顯示尚未分析的提示
            st.info(t("analysis_not_run_yet"))
            st.markdown(f"""
            {t('analysis_flow_title')}
            
            {t('analysis_flow_step1')}
            {t('analysis_flow_step2')}
            {t('analysis_flow_step3')}
            {t('analysis_flow_step4')}
            """)
            
    # --- Sidebar Settings ---
    st.sidebar.subheader(translate('analysis_settings'))
    
    # --- Language Selection ---
    with st.sidebar.expander(translate('language_selection'), expanded=True):
        # Language selection
        language_options = {
            'zh-TW': '繁體中文',
            'en': 'English'
        }
        
        current_lang = st.session_state.get('current_language', 'zh-TW')
        
        selected_language = st.selectbox(
            translate('select_language'),
            options=list(language_options.keys()),
            format_func=lambda x: language_options[x],
            index=list(language_options.keys()).index(current_lang),
            key="language_selector"
        )
        
        # Update language if changed
        if selected_language != current_lang:
            st.session_state.current_language = selected_language
            st.session_state.language_changed = True
            
            # Update the i18n system
            from gmat_diagnosis_app.i18n import set_language
            set_language(selected_language)
            
            success_msg = translate('language_updated') + " / Language updated!" if selected_language == 'zh-TW' else "Language updated! / " + translate('language_updated')
            st.success(success_msg)
            st.rerun()  # Trigger rerun to apply language changes
    
    # 添加範例數據導入功能
    with st.sidebar.expander(translate('sample_data'), expanded=True):
        st.markdown(f"### {translate('sample_data_import')}")
        st.markdown(translate('sample_data_description'))
        
        st.button(translate('load_sample_data'), 
                  key="load_sample_data_pasted", 
                  use_container_width=True,
                  on_click=load_sample_data_callback) # Use on_click callback

        if st.session_state.get('sample_data_pasted_success', False):
            st.success(translate('sample_data_loaded_success'))
            st.session_state.sample_data_pasted_success = False # Reset flag
            
    # OpenAI設定區塊（移到上方更明顯的位置）
    with st.sidebar.expander(translate('ai_settings'), expanded=False):
        master_key_input = st.text_input(
            translate('master_key_prompt'),
            type="password",
            key="master_key_input",
            value=st.session_state.get('master_key', ''),
            help=translate('master_key_help')
        )

        # Update session state when input changes
        if master_key_input:
            st.session_state.master_key = master_key_input
            # 使用新的方法基於master key初始化OpenAI客戶端
            from gmat_diagnosis_app.services.openai_service import initialize_openai_client_with_master_key
            if initialize_openai_client_with_master_key(master_key_input):
                st.session_state.show_chat = True
                st.session_state.chat_history = []
                st.success(translate('master_key_success'))
            else:
                st.session_state.show_chat = False
                st.session_state.chat_history = []
                st.error(translate('master_key_failed'))
        else:
            st.session_state.master_key = None
            st.session_state.show_chat = False
            st.session_state.chat_history = []

    # --- IRT Simulation Settings ---
    with st.sidebar.expander(translate('irt_simulation_settings'), expanded=False):
        st.session_state.initial_theta_q = st.number_input(
            t("q_initial_theta"), 
            value=st.session_state.initial_theta_q, 
            step=0.1,
            key="theta_q_input"
        )
        st.session_state.initial_theta_v = st.number_input(
            t("v_initial_theta"), 
            value=st.session_state.initial_theta_v, 
            step=0.1,
            key="theta_v_input"
        )
        st.session_state.initial_theta_di = st.number_input(
            t("di_initial_theta"), 
            value=st.session_state.initial_theta_di, 
            step=0.1,
            key="theta_di_input"
        )

    # --- Manual IRT Adjustment Inputs in Sidebar ---
    with st.sidebar.expander(translate('manual_adjustments'), expanded=False):
        st.markdown(f"#### {translate('manual_adjustments_description')}")
        st.markdown(translate('manual_adjustments_note'))
        
        # 使用標籤頁節省空間
        q_tab, v_tab, di_tab = st.tabs(["Q", "V", "DI"])
        
        with q_tab:
            st.session_state.q_incorrect_to_correct_qns = st.text_input(
                translate('incorrect_to_correct'), 
                value=st.session_state.q_incorrect_to_correct_qns,
                placeholder=translate('example_format'),
                key="q_i_to_c_input"
            )
            st.session_state.q_correct_to_incorrect_qns = st.text_input(
                translate('correct_to_incorrect'), 
                value=st.session_state.q_correct_to_incorrect_qns,
                placeholder=translate('example_format'),
                key="q_c_to_i_input"
            )
        
        with v_tab:
            st.session_state.v_incorrect_to_correct_qns = st.text_input(
                translate('incorrect_to_correct'), 
                value=st.session_state.v_incorrect_to_correct_qns,
                placeholder=translate('example_format'),
                key="v_i_to_c_input"
            )
            st.session_state.v_correct_to_incorrect_qns = st.text_input(
                translate('correct_to_incorrect'), 
                value=st.session_state.v_correct_to_incorrect_qns,
                placeholder=translate('example_format'),
                key="v_c_to_i_input"
            )
        
        with di_tab:
            st.session_state.di_incorrect_to_correct_qns = st.text_input(
                translate('incorrect_to_correct'), 
                value=st.session_state.di_incorrect_to_correct_qns,
                placeholder=translate('example_format'),
                key="di_i_to_c_input"
            )
            st.session_state.di_correct_to_incorrect_qns = st.text_input(
                translate('correct_to_incorrect'), 
                value=st.session_state.di_correct_to_incorrect_qns,
                placeholder=translate('example_format'),
                key="di_c_to_i_input"
            )
    
    # 頁尾信息
    st.markdown("---")
    st.caption(f"{translate('footer_feedback')} [{translate('footer_github')}](https://github.com/danyuchn/GMAT-score-report-analysis/issues) {translate('footer_submit')}")

if __name__ == "__main__":
    main() 