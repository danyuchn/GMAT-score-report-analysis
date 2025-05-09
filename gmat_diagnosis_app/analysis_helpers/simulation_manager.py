# -*- coding: utf-8 -*-
"""
Simulation manager for GMAT diagnosis app.
從analysis_orchestrator.py中分離出來的IRT模擬管理邏輯。
"""

import pandas as pd
import numpy as np
import logging
import streamlit as st
from gmat_diagnosis_app import irt_module as irt
from gmat_diagnosis_app.constants.config import BANK_SIZE, RANDOM_SEED, SUBJECT_SIM_PARAMS, SUBJECTS
from gmat_diagnosis_app.utils.parsing_utils import parse_adjusted_qns
from gmat_diagnosis_app.services.plotting_service import create_theta_plot

def run_simulation(df_input_for_sim):
    """
    Run IRT simulation for each subject in the input data.
    
    Args:
        df_input_for_sim (pd.DataFrame): DataFrame with preprocessed input data.
        
    Returns:
        tuple: (simulation_histories, final_thetas, theta_plots, question_banks, success_status)
    """
    all_simulation_histories = {}
    final_thetas_local = {}
    all_theta_plots = {}
    question_banks = {}
    analysis_success = True
    
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
            user_df_subj = df_input_for_sim[df_input_for_sim['Subject'] == subject].sort_values(by='question_position')

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
        
        return all_simulation_histories, final_thetas_local, all_theta_plots, question_banks, analysis_success

    except Exception as e:
        st.error(f"IRT 模擬過程中出錯: {e}")
        logging.error(f"IRT 模擬過程中出錯: {e}", exc_info=True)
        return {}, {}, {}, {}, False

def prepare_dataframes_for_diagnosis(all_simulation_histories, final_thetas, 
                                     time_pressure_map, df_combined_input_with_invalids):
    """
    Prepare final dataframes for diagnosis by combining simulation results with input data.
    
    Args:
        all_simulation_histories (dict): Simulation histories by subject.
        final_thetas (dict): Final theta values by subject.
        time_pressure_map (dict): Time pressure status by subject.
        df_combined_input_with_invalids (pd.DataFrame): Input dataframe with invalids marked.
        
    Returns:
        tuple: (DataFrame for diagnosis, success status)
    """
    from gmat_diagnosis_app.constants.config import FINAL_DIAGNOSIS_INPUT_COLS
    from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_overtime
    from gmat_diagnosis_app.subject_preprocessing.verbal_preprocessor import preprocess_verbal_data
    from gmat_diagnosis_app.subject_preprocessing.di_preprocessor import preprocess_di_data
    
    df_final_for_diagnosis_list = []
    analysis_success = True
    
    try:
        for subject in SUBJECTS:
            user_df_subj = df_combined_input_with_invalids[df_combined_input_with_invalids['Subject'] == subject].copy()
            sim_history_df = all_simulation_histories.get(subject)
            final_theta = final_thetas.get(subject)

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
                    if 'msr_group_total_time' not in user_df_subj_sorted.columns:
                        logging.warning("Orchestrator: DI: 'msr_group_total_time' NOT in user_df_subj_sorted.columns AFTER preprocess_di_data!")
                    if 'msr_group_id' not in user_df_subj_sorted.columns:
                        st.warning(f"DI科：preprocess_di_data 執行後，'msr_group_id' 欄位仍缺失。MSR 相關計算可能不準確或跳過。", icon="⚠️")
                except Exception as e_di_prep:
                    st.warning(f"DI科：執行 DI data preprocessing 時發生錯誤: {e_di_prep}。MSR 相關計算可能受影響。", icon="🔥")
                    # Ensure critical MSR columns exist even on error for downstream safety, though data might be wrong
                    for msr_col_critical in ['msr_group_id', 'msr_group_total_time', 'msr_reading_time', 'msr_group_num_questions', 'is_first_msr_q']:
                        if msr_col_critical not in user_df_subj_sorted.columns:
                            if 'id' in msr_col_critical: user_df_subj_sorted[msr_col_critical] = pd.NA
                            elif 'is_' in msr_col_critical: user_df_subj_sorted[msr_col_critical] = False
                            else: user_df_subj_sorted[msr_col_critical] = 0.0

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
            
            current_df_for_list = user_df_subj_sorted[cols_to_keep]
            df_final_for_diagnosis_list.append(current_df_for_list)

        if analysis_success and df_final_for_diagnosis_list:
            df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
            if 'msr_group_total_time' not in df_final_for_diagnosis.columns and 'DI' in df_final_for_diagnosis['Subject'].unique():
                logging.error("CRITICAL_ERROR: Orchestrator: 'msr_group_total_time' NOT in df_final_for_diagnosis columns AFTER concat (DI data present)!")
            return df_final_for_diagnosis, True
        elif analysis_success:
            st.warning("未能準備任何科目的診斷數據。")
            return pd.DataFrame(), False
            
    except Exception as e:
        st.error(f"準備科目診斷數據時出錯: {e}")
        logging.error(f"準備科目診斷數據時出錯: {e}", exc_info=True)
        return pd.DataFrame(), False 