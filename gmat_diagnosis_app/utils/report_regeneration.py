# -*- coding: utf-8 -*-
"""
Report regeneration utilities for language switching.
語言切換時重新生成診斷報告的工具函數。
"""

import pandas as pd
import logging
import streamlit as st
from gmat_diagnosis_app.constants.config import SUBJECTS
from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.services.openai_service import summarize_report_with_openai, generate_ai_consolidated_report


def regenerate_reports_for_language_switch():
    """
    Regenerate diagnostic reports when language is switched.
    This function re-runs the diagnosis logic on existing processed data to get reports in the new language.
    """
    try:
        # Get existing processed data
        df_final = st.session_state.get("processed_df")
        if df_final is None or df_final.empty:
            logging.warning("No processed data found for report regeneration")
            return
        
        # Get time pressure map from existing session state
        time_pressure_map = {}
        for subject in SUBJECTS:
            time_pressure_key = f"{subject.lower()}_time_pressure"
            if time_pressure_key in st.session_state:
                # Convert to boolean if it's a string or int
                time_pressure_value = st.session_state[time_pressure_key]
                if isinstance(time_pressure_value, str):
                    time_pressure_map[subject] = time_pressure_value.lower() in ['true', 'high', '高']
                elif isinstance(time_pressure_value, (int, float)):
                    time_pressure_map[subject] = int(time_pressure_value) > 2  # Assuming 1-5 scale, >2 means high pressure
                else:
                    time_pressure_map[subject] = bool(time_pressure_value)
            else:
                time_pressure_map[subject] = False
        
        # Store original data to avoid modification
        original_processed_df = df_final.copy()
        
        # Re-generate reports for each subject with new language
        temp_report_dict = {}
        
        # Pre-calculate V average times if V is present (same as original logic)
        v_avg_time_per_type = {}
        if 'V' in SUBJECTS:
            df_v_temp = df_final[df_final['Subject'] == 'V'].copy()
            if not df_v_temp.empty and 'question_time' in df_v_temp.columns and 'question_type' in df_v_temp.columns:
                df_v_temp.loc[:, 'question_time'] = pd.to_numeric(df_v_temp['question_time'], errors='coerce')
                v_avg_time_per_type = df_v_temp.dropna(subset=['question_time']).groupby('question_type')['question_time'].mean().to_dict()

        for subject in SUBJECTS:
            df_subj = df_final[df_final['Subject'] == subject].copy()
            time_pressure = time_pressure_map.get(subject, False)
            
            if df_subj.empty:
                continue
                
            try:
                subj_results, subj_report, df_subj_diagnosed = None, None, None
                
                if subject == 'Q':
                    subj_results, subj_report, df_subj_diagnosed = diagnose_q(df_subj)
                elif subject == 'DI':
                    subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_subj, time_pressure)
                elif subject == 'V':
                    subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
                
                if subj_report is not None:
                    # Apply OpenAI summarization if available
                    final_report_for_subject = subj_report
                    if st.session_state.get('master_key') and subj_report and "發生錯誤" not in subj_report and "未成功執行" not in subj_report:
                        summarized_report = summarize_report_with_openai(subj_report, st.session_state.master_key)
                        if summarized_report != subj_report:
                            final_report_for_subject = summarized_report
                    
                    temp_report_dict[subject] = final_report_for_subject
                else:
                    temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n*診斷未成功執行或未返回結果。*\n"
                    
            except Exception as diag_err:
                logging.error(f"Error regenerating {subject} report: {diag_err}")
                temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n*重新生成報告時發生錯誤: {diag_err}*\n"
        
        # Update session state with new reports
        st.session_state.report_dict = temp_report_dict
        st.session_state.raw_reports_for_ai = temp_report_dict
        
        # Regenerate AI consolidated report if master key is available
        if st.session_state.get('master_key') and temp_report_dict:
            try:
                consolidated_report = generate_ai_consolidated_report(
                    temp_report_dict,
                    st.session_state.master_key
                )
                if consolidated_report:
                    st.session_state.consolidated_report = consolidated_report
                    st.session_state.consolidated_report_text = consolidated_report
                    logging.info("AI consolidated report regenerated successfully for new language.")
                else:
                    logging.warning("AI consolidated report regeneration returned None or empty.")
            except Exception as ai_gen_err:
                logging.error(f"Error regenerating AI consolidated report: {ai_gen_err}")
        
        logging.info(f"Successfully regenerated reports for language switch. Generated {len(temp_report_dict)} reports.")
        
    except Exception as e:
        logging.error(f"Error in regenerate_reports_for_language_switch: {e}", exc_info=True)
        # Don't raise the error to avoid breaking the app, just log it 