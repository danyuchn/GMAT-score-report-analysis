# -*- coding: utf-8 -*-
"""
Diagnosis manager for GMAT diagnosis app.
從analysis_orchestrator.py中分離出來的診斷管理邏輯。
"""

import pandas as pd
import logging
import streamlit as st
from gmat_diagnosis_app.constants.config import SUBJECTS
from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.services.openai_service import summarize_report_with_openai, generate_ai_consolidated_report
# Import the new helper functions from session_manager
from gmat_diagnosis_app.session_manager import set_analysis_results, set_analysis_error

def run_diagnosis(df_final_for_diagnosis, time_pressure_map):
    """
    Run diagnosis for each subject and generate reports.
    
    Args:
        df_final_for_diagnosis (pd.DataFrame): DataFrame prepared for diagnosis.
        time_pressure_map (dict): Time pressure status by subject.
        
    Returns:
        tuple: (diagnosed_dfs, report_dict, consolidated_report, success_status)
    """
    all_diagnosed_dfs = []
    temp_report_dict = {}  # Use temporary dict during run
    analysis_success = True
    consolidated_report = None
    
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
                    # Corrected: Filter df_subj from df_final_for_diagnosis, not st.session_state.processed_df for current run
                    if df_final_for_diagnosis is not None and 'DI' in df_final_for_diagnosis['Subject'].unique(): # Check if DI data exists in the current prepared data
                        df_di_for_diag = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == 'DI'].copy()
                        # Enhanced Debugging for df_di_for_diag before calling run_di_diagnosis_logic
                        if 'msr_group_total_time' not in df_di_for_diag.columns:
                            pass # Logged error, DI diagnosis might fail or produce incorrect results
                        subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_di_for_diag, time_pressure) # Use df_subj which is df_di_for_diag
                    else:
                        # logging.info("Orchestrator (Step 5): No DI data found in df_final_for_diagnosis. Skipping DI diagnosis.") # REMOVED by AI
                        subj_results, subj_report, df_subj_diagnosed = {}, "DI 科無數據可診斷。", pd.DataFrame()

                elif subject == 'V':
                    subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
            except Exception as diag_err:
                st.error(f"  {subject} 科診斷函數執行時出錯: {diag_err}")

            if subj_report is not None and df_subj_diagnosed is not None:
                # Attempt OpenAI Summarization
                final_report_for_subject = subj_report  # Start with the original
                # Retrieve api key
                if st.session_state.master_key and subj_report and "發生錯誤" not in subj_report and "未成功執行" not in subj_report:
                    summarized_report = summarize_report_with_openai(subj_report, st.session_state.master_key)
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
            # 確保在合併前篩選掉空的或全NA的列，以避免警告
            filtered_dfs = []
            for df in valid_diagnosed_dfs:
                # 移除全NA的列
                df_filtered = df.dropna(axis=1, how='all')
                # 確保所有列的數據類型相容
                filtered_dfs.append(df_filtered)
                
            st.session_state.processed_df = pd.concat(filtered_dfs, ignore_index=True)
            st.session_state.report_dict = temp_report_dict

            # Generate Consolidated AI Report
            if st.session_state.master_key and st.session_state.report_dict:
                try:
                    consolidated_report = generate_ai_consolidated_report(
                        st.session_state.report_dict,
                        st.session_state.master_key
                    )
                    st.session_state.consolidated_report = consolidated_report
                    st.session_state.raw_reports_for_ai = temp_report_dict # Save for potential re-summarization
                    if consolidated_report:
                        logging.info("AI consolidated report generated successfully.")
                    else:
                        logging.warning("AI consolidated report generation returned None or empty.")
                except Exception as ai_gen_err:
                    st.warning(f"生成 AI 匯總建議時發生錯誤: {ai_gen_err}", icon="⚠️")
                    logging.error(f"Error calling generate_ai_consolidated_report: {ai_gen_err}", exc_info=True)
                    consolidated_report = None  # Ensure it's None on error
            else:
                consolidated_report = None  # Ensure None if no key/report

        else:
            st.error("所有科目均未能成功診斷或無數據。")
            st.session_state.processed_df = None  # Ensure no stale data
            st.session_state.report_dict = temp_report_dict  # Still show error reports
            analysis_success = False
            
        # 修改第120行的pd.concat
        if valid_diagnosed_dfs:
            # 同樣確保在合併前篩選掉空的或全NA的列
            filtered_dfs = []
            for df in valid_diagnosed_dfs:
                df_filtered = df.dropna(axis=1, how='all')
                filtered_dfs.append(df_filtered)
            
            return pd.concat(filtered_dfs, ignore_index=True), temp_report_dict, consolidated_report, analysis_success
        else:
            return pd.DataFrame(), temp_report_dict, consolidated_report, analysis_success

    except Exception as e:
        st.error(f"診斷過程中發生未預期錯誤: {e}")
        logging.error(f"診斷過程中發生未預期錯誤: {e}", exc_info=True)
        return pd.DataFrame(), {}, None, False

def update_session_state_after_analysis(analysis_success, processed_df, report_dict, final_thetas, theta_plots, consolidated_report, error_message=None):
    """
    Update session state after analysis based on success status.
    
    Args:
        analysis_success (bool): Whether analysis was successful.
        processed_df (pd.DataFrame): Processed and diagnosed dataframe.
        report_dict (dict): Dictionary of reports by subject.
        final_thetas (dict): Final theta values by subject.
        theta_plots (dict): Theta plots by subject.
        consolidated_report (str): Consolidated AI report.
        error_message (str, optional): Error message if analysis failed.
        
    Returns:
        None
    """
    if analysis_success and processed_df is not None and not processed_df.empty:
        # Call the new helper function to set results
        set_analysis_results(
            processed_df=processed_df,
            report_dict=report_dict,
            final_thetas=final_thetas,
            theta_plots=theta_plots,
            consolidated_report=consolidated_report
        )
    else:
        error_msg_to_pass = error_message
        if analysis_success and (processed_df is None or processed_df.empty): # Succeeded but no data
            error_msg_to_pass = "分析完成但未產生有效數據，請檢查輸入或診斷邏輯。"
        elif not analysis_success: # Explicitly failed
            error_msg_to_pass = error_message or "分析未能成功完成，請檢查上方錯誤訊息。" # Preserve specific error if set
        
        # Call the new helper function to set error
        set_analysis_error(
            error_message=error_msg_to_pass,
            theta_plots=theta_plots # Pass theta_plots to preserve them if they exist
        ) 