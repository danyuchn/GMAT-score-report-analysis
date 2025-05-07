"""
Q診斷模塊的主入口函數

此模塊包含用於Q(Quantitative)診斷的主入口點函數，
用於協調整個診斷流程。
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict

from gmat_diagnosis_app.diagnostics.q_modules.constants import (
    MAX_ALLOWED_TIME_Q,
    TOTAL_QUESTIONS_Q,
    TIME_PRESSURE_THRESHOLD_Q,
    INVALID_TIME_THRESHOLD_MINUTES,
    SUSPICIOUS_FAST_MULTIPLIER,
    OVERTIME_THRESHOLDS,
    INVALID_DATA_TAG_Q
)
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation
from gmat_diagnosis_app.diagnostics.q_modules.utils import format_rate
from gmat_diagnosis_app.diagnostics.q_modules.analysis import diagnose_q_root_causes, diagnose_q_internal
from gmat_diagnosis_app.diagnostics.q_modules.behavioral import analyze_behavioral_patterns, analyze_skill_override
from gmat_diagnosis_app.diagnostics.q_modules.recommendations import generate_q_recommendations
from gmat_diagnosis_app.diagnostics.q_modules.reporting import (
    generate_report_section1,
    generate_report_section2,
    generate_report_section3,
    generate_report_section4,
    generate_report_section5,
    generate_report_section6,
    generate_report_section7,
    generate_q_summary_report
)


def diagnose_q_main(df, include_summaries=False, include_individual_errors=False, include_summary_report=True):
    """
    Main entry point for Q diagnostics.
    
    This function orchestrates the entire Q diagnostic process by:
    1. Analyzing time pressure and data validity (Ch 1)
    2. Performing root cause analysis on each question
    3. Analyzing patterns across questions (Ch 2-6)
    4. Generating practice recommendations (Ch 7)
    5. Producing the final report (Ch 8)
    
    Args:
        df (DataFrame): Input dataframe with question data
        include_summaries (bool): Whether to include detailed summary data
        include_individual_errors (bool): Whether to include individual error details
        include_summary_report (bool): Whether to generate the text summary report
        
    Returns:
        dict: Diagnostic results, recommendations, and report
    """
    # Avoid modifying the input
    df_q = df.copy()
    
    # --- Chapter 1: Time Pressure & Data Validity Analysis ---
    # These are now expected to be pre-calculated and passed in or already on df_q
    # total_time = df_q['question_time'].sum() if 'question_time' in df_q.columns else None
    # time_pressure = False # This should be an input or derived from df_q if part of a larger pipeline
    # overtime_threshold = OVERTIME_THRESHOLDS[False] 
    
    # if total_time is not None:
    #     remaining_time = MAX_ALLOWED_TIME_Q - total_time
    #     if remaining_time < TIME_PRESSURE_THRESHOLD_Q:
    #         time_pressure = True
    #         overtime_threshold = OVERTIME_THRESHOLDS[True]
    
    # 'overtime' column is now expected to be pre-calculated by time_analyzer.py
    # if 'question_time' in df_q.columns:
    #     df_q['overtime'] = df_q['question_time'] > overtime_threshold
    
    # 'is_invalid' column is now expected to be pre-calculated by analysis_orchestrator.py
    # invalid_questions = []
    # if 'question_time' in df_q.columns and 'question_position' in df_q.columns:
    #     positions = df_q['question_position'].unique()
    #     if len(positions) >= 3:
    #         first_third = max(1, len(positions) // 3)
    #         first_positions = sorted(positions)[:first_third]
    #         first_third_times = df_q[df_q['question_position'].isin(first_positions)]['question_time']
    #         if not first_third_times.empty:
    #             avg_first_third_time = first_third_times.mean()
    #             suspicious_threshold = avg_first_third_time * SUSPICIOUS_FAST_MULTIPLIER
    #             for idx, row in df_q.iterrows():
    #                 time = row.get('question_time')
    #                 if pd.notna(time):
    #                     is_too_fast = time < INVALID_TIME_THRESHOLD_MINUTES
    #                     is_suspicious = time < suspicious_threshold
    #                     if is_too_fast or (is_suspicious and time_pressure): # Incorrect: time_pressure use for invalid marking
    #                         df_q.at[idx, 'is_invalid'] = True
    #                         invalid_questions.append(row['question_position'])
    
    # Ensure 'is_invalid' and 'overtime' columns exist as they are used downstream
    if 'is_invalid' not in df_q.columns:
        df_q['is_invalid'] = False # Default to False if not present
    else:
        df_q['is_invalid'] = df_q['is_invalid'].fillna(False)
        
    if 'overtime' not in df_q.columns:
        df_q['overtime'] = False # Default to False if not present
    else:
        df_q['overtime'] = df_q['overtime'].fillna(False)

    # This part needs to be adapted based on how time_pressure is passed or determined for Q
    # For now, assuming it might be part of st.session_state or a direct param if this func is called in isolation.
    # For robust integration, time_pressure for Q should be an input.
    # Let's assume a placeholder `q_time_pressure_status` is available for now for overtime_threshold selection if needed by other parts
    # However, the `overtime` column itself should already be correctly populated.
    q_time_pressure_status = df_q.attrs.get('time_pressure_q', False) # Example: get from df attributes if set by orchestrator
    # The invalid_questions list for chapter1_results also needs to be sourced differently if this logic is removed.
    # It should ideally come from where 'is_invalid' is determined.
    num_invalid_q = df_q['is_invalid'].sum()

    # --- Process the Valid Data ---
    df_valid = df_q[~df_q['is_invalid']].copy()
    
    # Calculate average times for each question type for later use
    avg_times_by_type = df_valid.groupby('question_type')['question_time'].mean().to_dict() if 'question_time' in df_valid.columns else {}
    
    # Calculate max correct difficulty by skill for SFE detection
    max_diffs_by_skill = {}
    if not df_valid.empty and 'question_difficulty' in df_valid.columns and 'question_fundamental_skill' in df_valid.columns:
        df_correct = df_valid[df_valid['is_correct'] == True]
        for skill, skill_df in df_correct.groupby('question_fundamental_skill'):
            if not skill_df.empty and not pd.isna(skill):
                max_diffs_by_skill[skill] = skill_df['question_difficulty'].max()
    
    # --- Root Cause Diagnosis ---
    # Add diagnosis params to each row
    df_diagnosed = diagnose_q_root_causes(df_q, avg_times_by_type, max_diffs_by_skill)
    
    # 首先處理所有數據的診斷參數翻譯（包括無效數據）
    if 'diagnostic_params' in df_diagnosed.columns:
        # 將所有診斷參數從英文代碼轉換為中文標籤
        df_diagnosed['diagnostic_params_list'] = df_diagnosed['diagnostic_params'].apply(
            lambda params_list: [get_translation(param) for param in (params_list if isinstance(params_list, list) else [])]
        )

    # For the rest of the analysis, focus on valid data with diagnosis
    df_valid_diagnosed = df_diagnosed[~df_diagnosed['is_invalid']].copy()
    
    # --- Chapters 2-6: Internal Diagnosis ---
    internal_diagnosis = diagnose_q_internal(df_valid_diagnosed)
    
    # Extract needed data from internal diagnosis
    ch2_flags = internal_diagnosis.get('chapter2_flags', {})
    ch2_summary = internal_diagnosis.get('chapter2_summary', [])
    ch3_errors = internal_diagnosis.get('chapter3_error_details', [])
    ch4_correct_slow = internal_diagnosis.get('chapter4_correct_slow_details', [])
    
    # --- Analyze Behavioral Patterns (Chapter 5) ---
    ch5_patterns = analyze_behavioral_patterns(df_valid_diagnosed)
    
    # --- Analyze Skill Override (Chapter 6) ---
    ch6_skill_override = analyze_skill_override(df_valid_diagnosed)
    
    # --- Consolidate Parameters for Report Generation ---
    # Extract all triggered diagnostic parameters
    triggered_params = set()
    param_to_positions = defaultdict(list)
    skill_to_positions = defaultdict(list)
    
    if 'diagnostic_params_list' in df_valid_diagnosed.columns:
        for _, row in df_valid_diagnosed.iterrows():
            position = row.get('question_position')
            skill = row.get('question_fundamental_skill')
            param_list = row.get('diagnostic_params_list', [])
            
            # Skip invalid data
            if row.get('is_invalid', False) or not param_list:
                continue
            
            for param in param_list:
                if param != INVALID_DATA_TAG_Q:  # Skip invalid tags
                    triggered_params.add(param)
                    param_to_positions[param].append(position)
                    
            if skill and not pd.isna(skill):
                skill_to_positions[skill].append(position)
    
    # Translate parameter codes to readable descriptions
    triggered_params_translated = {get_translation(code) for code in triggered_params}
    
    # Find if SFE is triggered and in which skills
    sfe_param_code = 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'
    sfe_triggered = sfe_param_code in triggered_params
    sfe_skills_involved = set()
    
    if sfe_triggered:
        for _, row in df_valid_diagnosed[df_valid_diagnosed['is_sfe'] == True].iterrows():
            skill = row.get('question_fundamental_skill')
            if skill and not pd.isna(skill):
                sfe_skills_involved.add(skill)
    
    # --- Chapter 7: Generate Recommendations ---
    q_diagnosis_results = {
        'chapter1_results': {
            'time_pressure_status': q_time_pressure_status, # This needs to be correctly sourced
            'overtime_threshold_used': OVERTIME_THRESHOLDS[q_time_pressure_status], # This also needs correct pressure status
            'invalid_questions_excluded': num_invalid_q
        },
        'chapter2_flags': ch2_flags,
        'chapter2_summary': ch2_summary,
        'chapter3_error_details': ch3_errors,
        'chapter4_correct_slow_details': ch4_correct_slow,
        'chapter5_patterns': ch5_patterns,
        'chapter6_skill_override': ch6_skill_override
    }
    
    # Pass df_valid_diagnosed to generate_q_recommendations for exemption logic
    recommendations = generate_q_recommendations(q_diagnosis_results, df_valid_diagnosed)
    
    # --- Chapter 8: Generate Report Sections --- 
    report_sections = []
    report_sections.extend(generate_report_section1(q_diagnosis_results['chapter1_results']))
    report_sections.append("")
    report_sections.extend(generate_report_section2(ch2_summary, ch2_flags, ch3_errors))
    report_sections.append("")
    report_sections.extend(generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved))
    report_sections.append("")
    report_sections.extend(generate_report_section4(ch5_patterns))
    report_sections.append("")
    report_sections.extend(generate_report_section5(ch6_skill_override))
    report_sections.append("")
    report_sections.extend(generate_report_section6(recommendations, sfe_triggered))
    report_sections.append("")
    report_sections.extend(generate_report_section7(triggered_params_translated, param_to_positions, skill_to_positions, sfe_skills_involved, df_valid_diagnosed))
    
    # Compile the main diagnostic report
    main_report = "\n".join(report_sections)
    
    # Generate summary report if requested
    summary_report = None
    if include_summary_report:
        summary_report = generate_q_summary_report(q_diagnosis_results, recommendations, df_diagnosed, triggered_params)
    
    # Prepare the results dictionary
    results = {
        'raw_results': q_diagnosis_results,
        'recommendations': recommendations,
        'main_report': main_report,
        'summary_report': summary_report
    }
    
    # Include additional data if requested
    if include_summaries:
        results['diagnostic_summary'] = {
            'triggered_params': list(triggered_params),
            'time_pressure_status': q_time_pressure_status,
            'overtime_threshold': OVERTIME_THRESHOLDS[q_time_pressure_status],
            'sfe_triggered': sfe_triggered,
            'sfe_skills': list(sfe_skills_involved) if sfe_skills_involved else [],
            'skill_override': ch6_skill_override
        }
    
    if include_individual_errors:
        results['individual_errors'] = ch3_errors
    
    # Determine the primary report string to be returned alongside results and df_diagnosed
    final_report_str = summary_report if include_summary_report and summary_report is not None else main_report
    
    return results, final_report_str, df_diagnosed 