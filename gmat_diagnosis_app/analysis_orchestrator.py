# -*- coding: utf-8 -*-
# Ensure UTF-8 encoding for comments/strings
"""
Orchestrates the GMAT analysis pipeline.
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

                user_df_subj['estimated_ability'] = final_theta
                user_df_subj_sorted = user_df_subj.sort_values(by='question_position').reset_index(drop=True)

                sim_b_values = []
                if not sim_history_df.attrs.get('simulation_skipped', False):
                    sim_b_values = sim_history_df['b'].tolist()

                if len(sim_b_values) == len(user_df_subj_sorted):
                    user_df_subj_sorted['question_difficulty'] = sim_b_values
                elif not sim_history_df.attrs.get('simulation_skipped', False):
                    st.warning(f"{subject}: 模擬難度數量 ({len(sim_b_values)}) 與實際題目數量 ({len(user_df_subj_sorted)}) 不符。無法分配模擬難度。", icon="⚠️")
                    user_df_subj_sorted['question_difficulty'] = np.nan
                else: 
                    user_df_subj_sorted['question_difficulty'] = np.nan

                if subject == 'V':
                    try:
                        user_df_subj_sorted = preprocess_verbal_data(user_df_subj_sorted)
                        if not all(col in user_df_subj_sorted.columns for col in ['rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']):
                             st.warning(f"V科：preprocess_verbal_data 執行後，部分RC欄位仍缺失。RC 超時計算可能不準確或跳過。", icon="⚠️")
                    except Exception as e_verb_prep:
                        st.warning(f"V科：執行 verbal data preprocessing 時發生錯誤: {e_verb_prep}。RC 超時計算可能受影響。", icon="🔥")
                        for rc_col in ['rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']:
                            if rc_col not in user_df_subj_sorted.columns:
                                user_df_subj_sorted[rc_col] = np.nan if 'id' in rc_col else 0
                elif subject == 'DI':
                    try:
                        user_df_subj_sorted = preprocess_di_data(user_df_subj_sorted)
                        if 'msr_group_id' not in user_df_subj_sorted.columns:
                            st.warning(f"DI科：preprocess_di_data 執行後，'msr_group_id' 欄位仍缺失。MSR 相關計算可能不準確或跳過。", icon="⚠️")
                    except Exception as e_di_prep:
                        st.warning(f"DI科：執行 DI data preprocessing 時發生錯誤: {e_di_prep}。MSR 相關計算可能受影響。", icon="🔥")
                        if 'msr_group_id' not in user_df_subj_sorted.columns:
                            user_df_subj_sorted['msr_group_id'] = pd.NA

                # --- Calculate Overtime for the subject AFTER its specific preprocessing ---
                time_pressure_subj = time_pressure_map.get(subject, False)
                current_subj_pressure_map = {subject: time_pressure_subj}
                try:
                    # calculate_overtime adds the 'overtime' column to the DataFrame
                    user_df_subj_sorted = calculate_overtime(user_df_subj_sorted, current_subj_pressure_map)
                except Exception as overtime_calc_err:
                    st.warning(f"  {subject}: 計算 Overtime 時出錯 (在數據準備階段): {overtime_calc_err}。 'overtime' 欄位可能缺失或不正確。", icon="🔥")
                    if 'overtime' not in user_df_subj_sorted.columns:
                        user_df_subj_sorted['overtime'] = False # Default to False if calculation failed
                # --- End Overtime Calculation ---

                if 'content_domain' not in user_df_subj_sorted.columns:
                    user_df_subj_sorted['content_domain'] = 'Unknown Domain'
                if 'question_fundamental_skill' not in user_df_subj_sorted.columns:
                    user_df_subj_sorted['question_fundamental_skill'] = 'Unknown Skill'

                cols_to_keep = [col for col in FINAL_DIAGNOSIS_INPUT_COLS if col in user_df_subj_sorted.columns]
                # Ensure 'overtime' column is kept if it exists, as it's crucial for diagnosis.
                if 'overtime' in user_df_subj_sorted.columns and 'overtime' not in cols_to_keep:
                    cols_to_keep.append('overtime')
                
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
                    temp_report_dict[subject] = f"**{subject} 科診斷報告**\\n\\n* 診斷未成功執行或未返回結果。*\\n"

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