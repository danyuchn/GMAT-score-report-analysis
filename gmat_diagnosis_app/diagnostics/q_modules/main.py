"""
Q診斷模塊的主入口函數

此模塊包含用於Q(Quantitative)診斷的主入口點函數，
用於協調整個診斷流程。
"""

import pandas as pd
from collections import defaultdict

from gmat_diagnosis_app.diagnostics.q_modules.constants import (
    OVERTIME_THRESHOLDS,
    INVALID_DATA_TAG_Q
)
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation
from gmat_diagnosis_app.diagnostics.q_modules.analysis import diagnose_q_root_causes, diagnose_q_internal
from gmat_diagnosis_app.diagnostics.q_modules.behavioral import analyze_behavioral_patterns, analyze_skill_override
from gmat_diagnosis_app.diagnostics.q_modules.recommendations import generate_q_recommendations
from gmat_diagnosis_app.diagnostics.q_modules.reporting import (
    # generate_report_section1,
    # generate_report_section2,
    # generate_report_section3,
    # generate_report_section4,
    # generate_report_section5,
    # generate_report_section6,
    # generate_report_section7,
    generate_q_summary_report
)


def diagnose_q_main(df, include_summaries=False, include_individual_errors=False, include_summary_report=True):
    """
    Main entry point for Q diagnostics.
    
    This function orchestrates the entire Q diagnostic process by:
    1. Analyzing time pressure and data validity (Ch 1) - Note: Time pressure from attrs, invalid handling updated.
    2. Performing root cause analysis on each question
    3. Analyzing patterns across questions (Ch 2-6)
    4. Generating practice recommendations (Ch 7)
    5. Producing the final report (Ch 8)
    
    Args:
        df (DataFrame): Input dataframe with question data. Expected to have 'is_manually_invalid' if manual review is done,
                        otherwise 'is_invalid' will be used as a fallback for filtering.
        include_summaries (bool): Whether to include detailed summary data
        include_individual_errors (bool): Whether to include individual error details
        include_summary_report (bool): Whether to generate the text summary report
        
    Returns:
        dict: Diagnostic results, recommendations, and report
    """
    # Avoid modifying the input
    df_q = df.copy()
    
    # --- Chapter 1: Time Pressure & Data Validity Analysis ---
    # Time pressure status is expected to be in df_q.attrs.get('time_pressure_q', False)
    q_time_pressure_status = df_q.attrs.get('time_pressure_q', False)
    current_overtime_threshold = OVERTIME_THRESHOLDS[q_time_pressure_status]

    # Calculate 'overtime' column
    if 'question_time' in df_q.columns:
        # Ensure question_time is numeric for comparison
        df_q['question_time'] = pd.to_numeric(df_q['question_time'], errors='coerce')
        # Create the 'overtime' boolean column
        df_q['overtime'] = df_q['question_time'] > current_overtime_threshold
        # Handle potential NaNs from coercion or if question_time was missing for some rows
        df_q['overtime'] = df_q['overtime'].fillna(False)
    else:
        # If question_time column is not present, initialize 'overtime' column with False
        # This ensures the column exists for downstream processes
        df_q['overtime'] = pd.Series([False] * len(df_q), index=df_q.index)

    # Determine the mask for valid data, prioritizing 'is_manually_invalid'
    if 'is_manually_invalid' in df_q.columns:
        manual_invalid_mask = df_q['is_manually_invalid'].fillna(False).astype(bool)
        valid_data_mask = ~manual_invalid_mask
        num_manual_invalid_q = manual_invalid_mask.sum()
        # Ensure is_invalid column reflects the manual decision for subsequent logic if other parts rely on it
        # This is a critical step: if is_manually_invalid exists, it should be the source of truth for 'is_invalid' state.
        df_q['is_invalid'] = manual_invalid_mask 
    elif 'is_invalid' in df_q.columns:
        # Fallback to is_invalid if is_manually_invalid is not present
        # Logging a warning might be useful here in a real scenario
        print("Warning: 'is_manually_invalid' column not found. Falling back to 'is_invalid' for filtering Q data.")
        valid_data_mask = ~df_q['is_invalid'].fillna(False).astype(bool)
        num_manual_invalid_q = df_q['is_invalid'].sum() # In this case, it reflects total invalid based on the fallback
    else:
        # No invalid column, assume all are valid
        print("Warning: Neither 'is_manually_invalid' nor 'is_invalid' column found. Assuming all Q data is valid.")
        valid_data_mask = pd.Series([True] * len(df_q), index=df_q.index)
        num_manual_invalid_q = 0
        df_q['is_invalid'] = False # Ensure is_invalid column exists and is False

    # --- Process the Valid Data based on the determined mask ---
    df_valid_for_analysis = df_q[valid_data_mask].copy()
    
    # Calculate average times for each question type using the correctly filtered valid data
    avg_times_by_type = df_valid_for_analysis.groupby('question_type')['question_time'].mean().to_dict() if 'question_time' in df_valid_for_analysis.columns and not df_valid_for_analysis.empty else {}
    
    # Calculate max correct difficulty by skill for SFE detection using correctly filtered valid data
    max_diffs_by_skill = {}
    if not df_valid_for_analysis.empty and 'question_difficulty' in df_valid_for_analysis.columns and 'question_fundamental_skill' in df_valid_for_analysis.columns:
        df_correct_valid = df_valid_for_analysis[df_valid_for_analysis['is_correct'] == True]
        if not df_correct_valid.empty:
            for skill, skill_df in df_correct_valid.groupby('question_fundamental_skill'):
                if not skill_df.empty and not pd.isna(skill):
                    max_diffs_by_skill[skill] = skill_df['question_difficulty'].max()
    
    # --- Root Cause Diagnosis ---
    # Add diagnosis params to each row. df_diagnosed will be a modified copy of the original df_q,
    # with root causes applied. 'diagnose_q_root_causes' needs to correctly handle 'is_invalid' internally.
    df_diagnosed = diagnose_q_root_causes(df_q.copy(), avg_times_by_type, max_diffs_by_skill) # Pass a copy of df_q
    
    # 首先處理所有數據的診斷參數翻譯（包括無效數據）
    if 'diagnostic_params' in df_diagnosed.columns:
        # 將所有診斷參數從英文代碼轉換為中文標籤
        df_diagnosed['diagnostic_params_list'] = df_diagnosed['diagnostic_params'].apply(
            lambda params_list: [get_translation(param) for param in (params_list if isinstance(params_list, list) else [])]
        )

    # For the rest of the analysis, focus on valid data with diagnosis
    # This df_valid_diagnosed should now also correctly reflect manual invalid decisions
    # as df_diagnosed was based on df_q where 'is_invalid' was updated from 'is_manually_invalid'
    df_valid_diagnosed = df_diagnosed[valid_data_mask].copy()
    
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
            'time_pressure_status': q_time_pressure_status, 
            'overtime_threshold_used': OVERTIME_THRESHOLDS[q_time_pressure_status], 
            'invalid_questions_excluded': num_manual_invalid_q # Use the count of manually invalid questions
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
    # report_sections = [] # Commented out
    # report_sections.extend(generate_report_section1(q_diagnosis_results['chapter1_results'])) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section2(ch2_summary, ch2_flags, ch3_errors)) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved)) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section4(ch5_patterns)) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section5(ch6_skill_override)) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section6(recommendations, sfe_triggered)) # Commented out
    # report_sections.append("") # Commented out
    # report_sections.extend(generate_report_section7(triggered_params_translated, param_to_positions, skill_to_positions, sfe_skills_involved, df_valid_diagnosed)) # Commented out
    
    # Compile the main diagnostic report
    main_report = "" # Initialize main_report as empty or a placeholder
    # if report_sections: # This list is no longer populated
        # main_report = "\\n".join(report_sections) # Commented out
    
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
    # If summary_report is generated, it's preferred. Otherwise, main_report (which is now empty or placeholder).
    final_report_str = summary_report if include_summary_report and summary_report is not None else main_report
    if final_report_str is None: # Ensure final_report_str is never None
        final_report_str = "報告生成被禁用或遇到問題。" # Default message if no report is generated
    
    return results, final_report_str, df_diagnosed 