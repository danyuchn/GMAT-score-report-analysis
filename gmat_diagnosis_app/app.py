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
    # Import custom modules
    from gmat_diagnosis_app import irt_module as irt
    from gmat_diagnosis_app.preprocess_helpers import suggest_invalid_questions, calculate_overtime, THRESHOLDS, parse_adjusted_qns
    from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
    from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
    from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
    # from gmat_diagnosis_app.diagnostics.ir_diagnostic import run_ir_diagnosis_processed
    
    # Import our modularized components
    from gmat_diagnosis_app.constants.config import (
        SUBJECTS, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, BANK_SIZE, RANDOM_SEED,
        SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS, BASE_RENAME_MAP,
        REQUIRED_ORIGINAL_COLS, EXCEL_COLUMN_MAP
    )
    from gmat_diagnosis_app.utils.validation import validate_dataframe
    from gmat_diagnosis_app.utils.data_processing import process_subject_tab
    from gmat_diagnosis_app.utils.styling import apply_styles
    from gmat_diagnosis_app.utils.excel_utils import to_excel
    from gmat_diagnosis_app.services.openai_service import (
        summarize_report_with_openai, generate_ai_consolidated_report,
        get_chat_context, get_openai_response
    )
    from gmat_diagnosis_app.services.plotting_service import create_theta_plot
    from gmat_diagnosis_app.ui.results_display import display_subject_results
    from gmat_diagnosis_app.ui.chat_interface import display_chat_interface
    from gmat_diagnosis_app.ui.input_tabs import setup_input_tabs, combine_input_data, display_analysis_button
    
except ImportError as e:
    st.error(f"導入模組時出錯: {e}. 請確保環境設定正確，且 gmat_diagnosis_app 在 Python 路徑中。")
    st.stop()

# --- Initialize Column Display Configuration ---
COLUMN_DISPLAY_CONFIG = {
    "question_position": st.column_config.NumberColumn("題號", help="題目順序"),
    # 拿掉科目欄位
    "question_type": st.column_config.TextColumn("題型"),
    "question_fundamental_skill": st.column_config.TextColumn("考察能力"),
    "question_difficulty": st.column_config.NumberColumn("難度(模擬)", help="系統模擬的題目難度 (有效題目)", format="%.2f", width="small"),
    "question_time": st.column_config.NumberColumn("用時(分)", format="%.2f", width="small"),
    "time_performance_category": st.column_config.TextColumn("時間表現"),
    "content_domain": st.column_config.TextColumn("內容領域"),
    "diagnostic_params_list": st.column_config.ListColumn("診斷標籤", help="初步診斷標籤", width="medium"),
    # 移到最右側的欄位
    "is_correct": st.column_config.CheckboxColumn("答對?", help="是否回答正確"),
    "is_sfe": st.column_config.CheckboxColumn("SFE?", help="是否為Special Focus Error", width="small"),
    "is_invalid": st.column_config.CheckboxColumn("標記無效?", help="此題是否被標記為無效 (手動優先)", width="small"),
    # Internal columns for styling, set config to None to hide in st.dataframe
    "overtime": None,
    "is_manually_invalid": None, # Hide the intermediate manual flag
}

# --- Session State Functions ---
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

# --- Analysis Functions ---
def run_analysis(df_combined_input):
    """Run the complete analysis pipeline on the input data"""
    analysis_success = True
    df_final_for_diagnosis = None
    total_steps = 5
    current_step = 0

    # Initialize progress bar and status text placeholder
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"步驟 {current_step}/{total_steps}: 準備開始分析...")

    # --- 1. Calculate Time Pressure ---
    time_pressure_map = {}
    try:
        current_step = 1
        status_text.text(f"步驟 {current_step}/{total_steps}: 計算時間壓力...")
        
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

        fast_end_questions_exist = False
        if not q_df.empty:
            total_q_questions = len(q_df)
            last_third_start_index = int(total_q_questions * 2 / 3)
            last_third_q_df = q_df.iloc[last_third_start_index:]
            if not last_third_q_df.empty:
                fast_end_questions_exist = (last_third_q_df['question_time'] < 1.0).any()

        time_pressure_q = time_diff_check and fast_end_questions_exist
        time_pressure_v = (THRESHOLDS['V']['MAX_ALLOWED_TIME'] - v_total_time) < 1.0
        time_pressure_di = (THRESHOLDS['DI']['MAX_ALLOWED_TIME'] - di_total_time) <= THRESHOLDS['DI']['TIME_PRESSURE_DIFF_MIN']

        time_pressure_map = {'Q': time_pressure_q, 'V': time_pressure_v, 'DI': time_pressure_di}
        progress_bar.progress(current_step / total_steps)
    except Exception as e:
        st.error(f"計算時間壓力時出錯: {e}")
        analysis_success = False
        status_text.text(f"步驟 {current_step}/{total_steps}: 計算時間壓力時出錯。")

    # --- 2. Prepare Data for Simulation ---
    df_final_input_for_sim = None
    if analysis_success:
        try:
            current_step = 2
            status_text.text(f"步驟 {current_step}/{total_steps}: 準備模擬輸入...")
            df_final_input_for_sim = df_combined_input
            progress_bar.progress(current_step / total_steps)
        except Exception as e:
            st.error(f"準備模擬輸入時出錯: {e}")
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 準備模擬輸入時出錯。")

    # --- 3. IRT Simulation ---
    all_simulation_histories = {}
    final_thetas_local = {}
    all_theta_plots = {}
    question_banks = {}
    
    if analysis_success:
        current_step = 3
        status_text.text(f"步驟 {current_step}/{total_steps}: 執行 IRT 模擬...")
        try:
            # Initialize banks
            for subject in SUBJECTS:
                seed = RANDOM_SEED + SUBJECT_SIM_PARAMS[subject]['seed_offset']
                question_banks[subject] = irt.initialize_question_bank(BANK_SIZE, seed=seed)
                if question_banks[subject] is None:
                    raise ValueError(f"Failed to initialize question bank for {subject}")

            # Run simulation per subject
            for subject in SUBJECTS:
                params = SUBJECT_SIM_PARAMS[subject]
                initial_theta = st.session_state[params['initial_theta_key']]
                bank = question_banks[subject]

                # Get user data for the subject, sorted by position
                user_df_subj = df_final_input_for_sim[df_final_input_for_sim['Subject'] == subject].sort_values(by='question_position')

                # --- Parse Manually Adjusted Question Numbers for IRT ---
                incorrect_to_correct_str_key = f"{subject.lower()}_incorrect_to_correct_qns"
                correct_to_incorrect_str_key = f"{subject.lower()}_correct_to_incorrect_qns"
                
                i_to_c_qns_str = st.session_state.get(incorrect_to_correct_str_key, "")
                c_to_i_qns_str = st.session_state.get(correct_to_incorrect_str_key, "")
                
                i_to_c_qns_set = parse_adjusted_qns(i_to_c_qns_str)
                c_to_i_qns_set = parse_adjusted_qns(c_to_i_qns_str)
                # --- End Parsing ---

                # Calculate total questions and wrong positions
                if user_df_subj.empty:
                    st.warning(f"  {subject}: 沒有找到該科目的作答數據，無法執行模擬。", icon="⚠️")
                    final_thetas_local[subject] = initial_theta
                    all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                    all_simulation_histories[subject].attrs['simulation_skipped'] = True
                    continue

                try:
                    total_questions_attempted = len(user_df_subj)
                    if total_questions_attempted <= 0:
                        raise ValueError("Number of rows is not positive.")

                    # Calculate wrong positions from the subject-specific dataframe
                    if 'is_correct' not in user_df_subj.columns:
                        raise ValueError(f"{subject}: 缺少 'is_correct' 欄位。")
                    user_df_subj['is_correct'] = user_df_subj['is_correct'].astype(bool)
                    user_df_subj['question_position'] = pd.to_numeric(user_df_subj['question_position'], errors='coerce')
                    wrong_positions = user_df_subj.loc[(user_df_subj['is_correct'] == False) & user_df_subj['question_position'].notna(), 'question_position'].astype(int).tolist()

                except (KeyError, ValueError, TypeError) as e:
                    st.error(f"  {subject}: 無法確定總作答題數或錯誤位置: {e}。跳過模擬。", icon="🚨")
                    final_thetas_local[subject] = initial_theta
                    all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                    all_simulation_histories[subject].attrs['simulation_skipped'] = True
                    continue

                # Filter valid responses for later difficulty assignment
                valid_responses = user_df_subj[~user_df_subj['is_invalid']].copy()
                if valid_responses.empty:
                    st.warning(f"  {subject}: 所有題目均被標記為無效，Theta 模擬仍基於完整序列。", icon="⚠️")

                # Run simulation
                history_df = irt.simulate_cat_exam(
                    question_bank=bank,
                    wrong_question_positions=wrong_positions,
                    initial_theta=initial_theta,
                    total_questions=total_questions_attempted,
                    incorrect_to_correct_qns=i_to_c_qns_set,      # Pass the parsed set
                    correct_to_incorrect_qns=c_to_i_qns_set        # Pass the parsed set
                )

                if history_df is not None and not history_df.empty:
                    # Store results only if simulation ran
                    all_simulation_histories[subject] = history_df
                    final_theta_subj = history_df['theta_est_after_answer'].iloc[-1]
                    final_thetas_local[subject] = final_theta_subj

                    # Generate and store plot
                    try:
                        theta_plot = create_theta_plot(history_df, subject)
                        if theta_plot:
                            all_theta_plots[subject] = theta_plot
                        else:
                            st.warning(f"    {subject}: 未能生成 Theta 圖表 (create_theta_plot 返回 None)。", icon="📊")
                    except Exception as plot_err:
                        st.warning(f"    {subject}: 生成 Theta 圖表時出錯: {plot_err}", icon="📊")
                
                elif history_df is not None and history_df.empty:  # Succeeded but empty
                    st.warning(f"  {subject}: 模擬執行但未產生歷史記錄。將使用初始 Theta。")
                    final_thetas_local[subject] = initial_theta
                    all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                    all_simulation_histories[subject].attrs['simulation_skipped'] = True
                else:  # Failed (returned None)
                    raise ValueError(f"IRT simulation failed for subject {subject}")
            
            progress_bar.progress(current_step / total_steps)

        except Exception as e:
            st.error(f"執行 IRT 模擬時出錯: {e}")
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: IRT 模擬時出錯。")

    # --- 4. Prepare Data for Diagnosis ---
    if analysis_success:
        current_step = 4
        status_text.text(f"步驟 {current_step}/{total_steps}: 準備診斷數據...")
        df_final_for_diagnosis_list = []
        try:
            for subject in SUBJECTS:
                user_df_subj = df_final_input_for_sim[df_final_input_for_sim['Subject'] == subject].copy()
                sim_history_df = all_simulation_histories.get(subject)
                final_theta = final_thetas_local.get(subject)

                if sim_history_df is None:
                    st.error(f"找不到 {subject} 的模擬歷史，無法準備數據。")
                    analysis_success = False
                    break

                # Add final theta estimate to all rows for context
                user_df_subj['estimated_ability'] = final_theta

                # Assign Difficulty
                user_df_subj_sorted = user_df_subj.sort_values(by='question_position').reset_index(drop=True)

                # Get simulated difficulties IF simulation was not skipped
                sim_b_values = []
                if not sim_history_df.attrs.get('simulation_skipped', False):
                    sim_b_values = sim_history_df['b'].tolist()

                # Assign difficulty to ALL questions based on simulation order
                if len(sim_b_values) == len(user_df_subj_sorted):
                    user_df_subj_sorted['question_difficulty'] = sim_b_values
                elif not sim_history_df.attrs.get('simulation_skipped', False):
                    st.warning(f"{subject}: 模擬難度數量 ({len(sim_b_values)}) 與實際題目數量 ({len(user_df_subj_sorted)}) 不符。無法分配模擬難度。", icon="⚠️")
                    user_df_subj_sorted['question_difficulty'] = np.nan
                else:  # Simulation was skipped, assign NaN
                    user_df_subj_sorted['question_difficulty'] = np.nan

                # Fill missing essential columns
                if 'content_domain' not in user_df_subj_sorted.columns:
                    user_df_subj_sorted['content_domain'] = 'Unknown Domain'
                if 'question_fundamental_skill' not in user_df_subj_sorted.columns:
                    user_df_subj_sorted['question_fundamental_skill'] = 'Unknown Skill'

                # Select and reorder columns needed for diagnosis functions
                cols_to_keep = [col for col in FINAL_DIAGNOSIS_INPUT_COLS if col in user_df_subj_sorted.columns]
                df_final_for_diagnosis_list.append(user_df_subj_sorted[cols_to_keep])

            if analysis_success and df_final_for_diagnosis_list:
                df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
                progress_bar.progress(current_step / total_steps)
            elif analysis_success:
                st.warning("未能準備任何科目的診斷數據。")
                analysis_success = False
                status_text.text(f"步驟 {current_step}/{total_steps}: 數據準備完成，但無數據可診斷。")

        except Exception as e:
            st.error(f"準備診斷數據時發生錯誤: {e}")
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 準備診斷數據時出錯。")

    # --- 5. Run Diagnosis ---
    all_diagnosed_dfs = []
    if analysis_success and df_final_for_diagnosis is not None:
        current_step = 5
        status_text.text(f"步驟 {current_step}/{total_steps}: 執行診斷分析...")
        temp_report_dict = {}  # Use temporary dict during run
        try:
            # Pre-calculate V average times if V is present
            v_avg_time_per_type = {}
            if 'V' in SUBJECTS:
                df_v_temp = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == 'V'].copy()
                if not df_v_temp.empty and 'question_time' in df_v_temp.columns and 'question_type' in df_v_temp.columns:
                    df_v_temp.loc[:, 'question_time'] = pd.to_numeric(df_v_temp['question_time'], errors='coerce')
                    v_avg_time_per_type = df_v_temp.dropna(subset=['question_time']).groupby('question_type')['question_time'].mean().to_dict()

            for subject in SUBJECTS:
                df_subj = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == subject].copy()
                # Calculate Overtime for the subject *before* diagnosis
                time_pressure_subj = time_pressure_map.get(subject, False)
                try:
                    current_subj_pressure_map = {subject: time_pressure_subj}
                    df_subj_with_overtime = calculate_overtime(df_subj, current_subj_pressure_map)
                    df_subj = df_subj_with_overtime  # Replace df_subj
                except Exception as overtime_calc_err:
                    st.error(f"  {subject}: 計算 Overtime 時出錯: {overtime_calc_err}")
                    temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n* 計算超時狀態時出錯: {overtime_calc_err}*\n"
                    all_diagnosed_dfs.append(df_subj)  # Append original df without overtime/diagnosis
                    continue  # Skip diagnosis for this subject

                time_pressure = time_pressure_map.get(subject, False)
                subj_results, subj_report, df_subj_diagnosed = None, None, None

                try:
                    if subject == 'Q':
                        subj_results, subj_report, df_subj_diagnosed = diagnose_q(df_subj)
                    elif subject == 'DI':
                        subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_subj, time_pressure)
                    elif subject == 'V':
                        subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
                except Exception as diag_err:
                    st.error(f"  {subject} 科診斷函數執行時出錯: {diag_err}")

                if subj_report is not None and df_subj_diagnosed is not None:
                    # Attempt OpenAI Summarization
                    final_report_for_subject = subj_report  # Start with the original
                    # Retrieve api key
                    if st.session_state.openai_api_key and subj_report and "發生錯誤" not in subj_report and "未成功執行" not in subj_report:
                        summarized_report = summarize_report_with_openai(subj_report, st.session_state.openai_api_key)
                        if summarized_report != subj_report:  # Check if summarization actually changed something
                            final_report_for_subject = summarized_report

                    temp_report_dict[subject] = final_report_for_subject  # Store the final version
                    all_diagnosed_dfs.append(df_subj_diagnosed)  # Append the diagnosed dataframe

                else:
                    st.error(f"  {subject} 科診斷未返回預期結果。")
                    temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n* 診斷未成功執行或未返回結果。*\n"

            # Combine results *after* loop
            valid_diagnosed_dfs = [df for df in all_diagnosed_dfs if df is not None and not df.empty]
            if valid_diagnosed_dfs:
                st.session_state.processed_df = pd.concat(valid_diagnosed_dfs, ignore_index=True)
                st.session_state.report_dict = temp_report_dict
                st.session_state.final_thetas = final_thetas_local  # Store thetas from sim
                st.session_state.theta_plots = all_theta_plots  # Store the plots in session state
                progress_bar.progress(current_step / total_steps)  # Mark final step complete

                # Generate Consolidated AI Report
                if st.session_state.openai_api_key and st.session_state.report_dict:
                    status_text.text(f"步驟 {current_step}/{total_steps}: 生成 AI 匯總建議...")  # Update status
                    try:
                        consolidated_report = generate_ai_consolidated_report(
                            st.session_state.report_dict,
                            st.session_state.openai_api_key
                        )
                        st.session_state.ai_consolidated_report = consolidated_report
                        if consolidated_report:
                            logging.info("AI consolidated report generated successfully.")
                        else:
                            logging.warning("AI consolidated report generation returned None or empty.")
                    except Exception as ai_gen_err:
                        st.warning(f"生成 AI 匯總建議時發生錯誤: {ai_gen_err}", icon="⚠️")
                        logging.error(f"Error calling generate_ai_consolidated_report: {ai_gen_err}", exc_info=True)
                        st.session_state.ai_consolidated_report = None  # Ensure it's None on error
                else:
                    st.session_state.ai_consolidated_report = None  # Ensure None if no key/report

            else:
                st.error("所有科目均未能成功診斷或無數據。")
                st.session_state.processed_df = None  # Ensure no stale data
                st.session_state.report_dict = temp_report_dict  # Still show error reports
                st.session_state.theta_plots = {}  # Clear plots
                analysis_success = False
                status_text.text(f"步驟 {current_step}/{total_steps}: 診斷完成，但無有效結果。")

        except Exception as e:
            st.error(f"診斷過程中發生未預期錯誤: {e}")
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 執行診斷時出錯。")

    # --- Final Status Update ---
    if analysis_success and st.session_state.processed_df is not None:
        status_text.text("分析成功完成！")  # Update final status text
        st.session_state.diagnosis_complete = True
        st.session_state.error_message = None
        st.session_state.analysis_error = False # Explicitly set on success
        st.balloons()  # Celebrate success
    else:
        # This block handles cases where analysis_success is False OR processed_df is None
        if analysis_success and st.session_state.processed_df is None: # Succeeded but no data
            status_text.error("分析完成但未產生有效數據，請檢查輸入或診斷邏輯。")
        elif not analysis_success: # Explicitly failed
            # Check if status_text was ever updated beyond initial
            current_status_text_value = status_text.text("") # Get current value by re-calling with empty
            if "準備開始分析..." in current_status_text_value or not current_status_text_value.strip():
                 status_text.error("分析過程中斷或失敗，請檢查上方錯誤訊息。")
            # else: status_text already reflects the error step

        st.session_state.diagnosis_complete = False
        st.session_state.analysis_error = True # Set on failure
        st.session_state.error_message = st.session_state.error_message or "分析未能成功完成，請檢查上方錯誤訊息。" # Preserve specific error if set
        st.session_state.theta_plots = {}  # Clear plots on error

    return analysis_success

def display_results():
    """Display analysis results in tabs"""
    st.header("📊 診斷結果")

    if st.session_state.analysis_error:
        st.error(st.session_state.error_message or "分析過程中發生錯誤，請檢查。") # Fallback error message
    elif not st.session_state.diagnosis_complete:
        st.info("分析正在進行中或尚未完成。請稍候或檢查是否有錯誤提示。") # More informative message
    elif st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("診斷完成，但沒有可顯示的數據。")
        # Display any report messages even if df is empty (e.g., all invalid)
        if st.session_state.report_dict:
            st.subheader("診斷摘要")
            for subject, report_md in st.session_state.report_dict.items():
                st.markdown(f"### {subject} 科:")
                st.markdown(report_md, unsafe_allow_html=True)
    else:
        st.success("診斷分析已完成！")
        # Results Display Tabs
        subjects_with_data = [subj for subj in SUBJECTS if subj in st.session_state.processed_df['Subject'].unique()]
        if not subjects_with_data:
            st.warning("處理後的數據中未找到任何有效科目。")
        else:
            # Create tabs for each subject with data
            tab_titles = [f"{subj} 科結果" for subj in subjects_with_data]

            # Add AI Consolidated Report Tab if applicable
            show_ai_consolidated_tab = (
                st.session_state.openai_api_key and
                st.session_state.diagnosis_complete and
                st.session_state.ai_consolidated_report
            )
            if show_ai_consolidated_tab:
                tab_titles.append("✨ AI 匯總建議")

            result_tabs = st.tabs(tab_titles)

            # Display subject-specific results
            for i, subject in enumerate(subjects_with_data):
                subject_tab = result_tabs[i]
                with subject_tab:
                    df_subject = st.session_state.processed_df[st.session_state.processed_df['Subject'] == subject]
                    report_md = st.session_state.report_dict.get(subject, f"*未找到 {subject} 科的報告。*")

                    # Display Theta Plot
                    st.subheader(f"{subject} 科能力估計 (Theta) 走勢")
                    theta_plot = st.session_state.theta_plots.get(subject)
                    if theta_plot:
                        st.plotly_chart(theta_plot, use_container_width=True)
                    else:
                        st.info(f"{subject} 科目的 Theta 估計圖表不可用。")
                    st.divider()

                    display_subject_results(subject, subject_tab, report_md, df_subject, COLUMN_DISPLAY_CONFIG, EXCEL_COLUMN_MAP)

            # Display AI Consolidated Report in its Tab
            if show_ai_consolidated_tab:
                ai_tab_index = len(subjects_with_data)  # It's the last tab
                ai_consolidated_tab = result_tabs[ai_tab_index]
                with ai_consolidated_tab:
                    st.subheader("AI 匯總練習建議與後續行動")
                    st.markdown(st.session_state.ai_consolidated_report)
                    st.caption("此內容由 OpenAI (o4-mini) 模型根據各科報告中的相關部分生成。請務必結合原始報告進行核對。")

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
    from gmat_diagnosis_app import preprocess_helpers
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