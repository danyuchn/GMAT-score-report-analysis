"""
Results display module
Diagnostic results display functionality
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from gmat_diagnosis_app.utils.styling import apply_styles
from gmat_diagnosis_app.utils.excel_utils import to_excel
from gmat_diagnosis_app.constants.config import SUBJECTS, EXCEL_COLUMN_MAP
from gmat_diagnosis_app.ui.chat_interface import display_chat_interface
from gmat_diagnosis_app.services.openai_service import trim_diagnostic_tags_with_openai
from gmat_diagnosis_app.i18n import translate as t
import logging
import traceback # Added for more detailed error logging in download

# --- Force Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s') # UNCOMMENTED

# --- Column Display Configuration (Moved from app.py) ---
COLUMN_DISPLAY_CONFIG = {
    "question_position": st.column_config.NumberColumn(t("column_question_number"), help=t("column_question_number_help")),
    "question_type": st.column_config.TextColumn(t("column_question_type")),
    "question_fundamental_skill": st.column_config.TextColumn(t("column_tested_ability")),
    "question_difficulty": st.column_config.NumberColumn(t("column_simulated_difficulty"), help=t("column_simulated_difficulty_help"), format="%.2f", width="small"),
    "question_time": st.column_config.NumberColumn(t("column_response_time_minutes"), format="%.2f", width="small"),
    "time_performance_category": st.column_config.TextColumn(t("column_time_performance")),
    "content_domain": st.column_config.TextColumn(t("column_content_domain")),
    "diagnostic_params_list": st.column_config.ListColumn(t("column_diagnostic_tags"), help=t("column_diagnostic_tags_help"), width="medium"),
    "is_correct": st.column_config.CheckboxColumn(t("column_is_correct"), help=t("column_is_correct_help")),
    "is_sfe": st.column_config.CheckboxColumn(t("column_is_sfe"), help=t("column_is_sfe_help"), width="small"),
    "is_invalid": st.column_config.CheckboxColumn(t("column_is_invalid"), help=t("column_is_invalid_help"), width="small"),
    "overtime": None, # Internal column for styling
    "is_manually_invalid": None, # Hide the intermediate manual flag
}

def display_subject_results(subject, tab_container, report_md, df_subject, col_config, excel_map):
    """Displays the diagnosis report, styled DataFrame, and download button for a subject."""
    tab_container.subheader(t("subject_diagnostic_report").format(subject))
    
    try:
        if df_subject is not None and not df_subject.empty and 'diagnostic_params_list' in df_subject.columns and 'question_type' in df_subject.columns:
            rc_data_session = df_subject[df_subject['question_type'] == 'Reading Comprehension'][['question_position', 'diagnostic_params_list']]
            if not rc_data_session.empty:
                pass
            else:
                pass
        elif df_subject is None or df_subject.empty:
             pass
        else:
            pass
    except Exception as log_e_session:
         logging.error(t("session_state_rc_tags_error").format(log_e_session))
    
    # Prepare data table (common for all subjects)
    styled_df = None
    df_to_display = None
    columns_for_st_display_order = []
    
    if df_subject is not None and not df_subject.empty:
        # Data preprocessing before table display
        subject_col_config = col_config.copy()
        subject_excel_map = excel_map.copy()
        
        # Copy dataframe to avoid modifying original data
        df_display = df_subject.copy()
        
        # Ensure sorted by question number
        if 'question_position' in df_display.columns:
            df_display = df_display.sort_values(by='question_position').reset_index(drop=True)
        
        # Subject-specific processing
        if subject == 'DI':
            # Remove 'Tested Ability' field for DI section
            if 'question_fundamental_skill' in subject_col_config:
                del subject_col_config['question_fundamental_skill']
            if 'question_fundamental_skill' in subject_excel_map:
                del subject_excel_map['question_fundamental_skill']
        
        # Check invalid data type and values
        if 'is_invalid' in df_display.columns:
            try:
                with pd.option_context('future.no_silent_downcasting', True):
                    df_display['is_invalid'] = df_display['is_invalid'].replace({pd.NA: False, None: False})
                    df_display['is_invalid'] = df_display['is_invalid'].infer_objects(copy=False)
                df_display['is_invalid'] = df_display['is_invalid'].astype(bool)
            except Exception as e:
                tab_container.error(t("invalid_data_conversion_error").format(e))
        
        # Important modification: Ensure is_invalid completely follows manual marking
        if 'is_manually_invalid' in df_display.columns:
            if 'is_invalid' in df_display.columns:
                df_display['is_invalid'] = False
                df_display.loc[df_display['is_manually_invalid'] == True, 'is_invalid'] = True

        # Prepare dataframe display
        cols_available = [k for k in subject_col_config.keys() if k in df_display.columns]
        df_to_display = df_display[cols_available].copy()
        columns_for_st_display_order = [k for k in cols_available if subject_col_config.get(k) is not None]

        # Ensure necessary columns exist
        if 'overtime' not in df_to_display.columns: df_to_display['overtime'] = False
        if 'is_correct' not in df_to_display.columns: df_to_display['is_correct'] = True
        if 'is_invalid' not in df_to_display.columns: df_to_display['is_invalid'] = False
        
        # Again ensure is_invalid follows manual marking
        if 'is_manually_invalid' in df_to_display.columns:
            df_to_display['is_invalid'] = False
            df_to_display.loc[df_to_display['is_manually_invalid'] == True, 'is_invalid'] = True
            
        # Ensure is_invalid is boolean
        df_to_display['is_invalid'] = df_to_display['is_invalid'].astype(bool)
        
        try:
            styled_df = df_to_display.style.set_properties(**{'text-align': 'left'}) \
                                   .set_table_styles([dict(selector='th', props=[('text-align', 'left')])]) \
                                   .apply(apply_styles, axis=1)
        except Exception as e:
            logging.error(t("styling_application_error").format(e))
            styled_df = None
    
    # 1. First display data table (all subjects)
    tab_container.subheader(t("subject_detailed_data").format(subject))
    if styled_df is not None:
        try:
            if 'diagnostic_params_list' in df_to_display.columns and 'question_type' in df_to_display.columns:
                rc_data_to_log = df_to_display[df_to_display['question_type'] == 'Reading Comprehension'][['question_position', 'diagnostic_params_list']]
                if not rc_data_to_log.empty:
                    pass
                else:
                    pass
            else:
                 pass
        except Exception as log_e:
             logging.error(t("rc_tags_logging_error").format(log_e))
        
        try:
            tab_container.dataframe(
                styled_df,
                column_config=subject_col_config,
                column_order=columns_for_st_display_order,
                hide_index=True,
                use_container_width=True
            )
        except Exception as e:
            tab_container.error(t("table_display_error").format(e))
            tab_container.info(t("data_table_processing_error"))
    else:
        tab_container.info(t("data_table_empty_error"))
    
    # 2. Display theta chart (if exists)
    if 'theta_plots' in st.session_state and subject in st.session_state.theta_plots:
        tab_container.subheader(t("subject_theta_chart").format(subject))
        tab_container.plotly_chart(st.session_state.theta_plots[subject], use_container_width=True)
    
    # 3. Finally display diagnostic report
    if report_md:
        tab_container.subheader(t("subject_diagnostic_report_details").format(subject))
        from gmat_diagnosis_app.utils.styling import create_report_container
        create_report_container(report_md)
    else:
        tab_container.info(t("report_not_found").format(subject))

    # 4. Download Button (same for all subjects)
    try:
        # Prepare a copy specifically for Excel export using excel_map
        df_for_excel = df_subject.copy() # First copy complete df_subject

        # Important: Ensure is_invalid in df_for_excel also follows is_manually_invalid
        if 'is_manually_invalid' in df_for_excel.columns:
            if 'is_invalid' in df_for_excel.columns:
                df_for_excel['is_invalid'] = False
                df_for_excel.loc[df_for_excel['is_manually_invalid'] == True, 'is_invalid'] = True
            else:
                df_for_excel['is_invalid'] = df_for_excel['is_manually_invalid']
        
        # Ensure is_invalid column is boolean for subsequent processing
        if 'is_invalid' in df_for_excel.columns:
            df_for_excel['is_invalid'] = df_for_excel['is_invalid'].astype(bool)
            
        # Filter columns by excel_map (after is_invalid update)
        df_for_excel = df_for_excel[[k for k in excel_map.keys() if k in df_for_excel.columns]].copy()
        
        # Ensure sorted by question number
        if 'question_position' in df_for_excel.columns:
            df_for_excel = df_for_excel.sort_values(by='question_position').reset_index(drop=True)

        if 'is_invalid' not in df_for_excel.columns:
            df_for_excel['is_invalid'] = False
            
        if 'question_difficulty' in df_for_excel.columns:
            df_for_excel['question_difficulty'] = pd.to_numeric(df_for_excel['question_difficulty'], errors='coerce')
        if 'question_time' in df_for_excel.columns:
            df_for_excel['question_time'] = pd.to_numeric(df_for_excel['question_time'], errors='coerce')
            
        if 'is_correct' in df_for_excel.columns:
            df_for_excel['is_correct'] = df_for_excel['is_correct'].astype(str)
        if 'is_sfe' in df_for_excel.columns:
            df_for_excel['is_sfe'] = df_for_excel['is_sfe'].astype(str)
            
        if 'is_invalid' in df_for_excel.columns:
            df_for_excel['is_invalid'] = df_for_excel['is_invalid'].astype(str)

        try:
            value_counts = df_for_excel['is_invalid'].value_counts().to_dict()
        except Exception as e:
            pass
            
        invalid_count = (df_for_excel['is_invalid'] == 'True').sum() if 'is_invalid' in df_for_excel.columns else 0
                
        excel_bytes = to_excel(df_for_excel, excel_map)
        
        today_str = pd.Timestamp.now().strftime('%Y%m%d')
        tab_container.download_button(
            t("download_subject_detailed_data").format(subject),
            data=excel_bytes,
            file_name=f"{today_str}_GMAT_{subject}_detailed_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        tab_container.error(t("excel_download_error").format(e))
        logging.error(t("detailed_error").format(traceback.format_exc()))
        tab_container.info(t("contact_admin_error"))

def display_total_results(tab_container):
    """Display Total score percentiles and chart analysis"""
    total_data_df = st.session_state.get('total_data')
    if total_data_df is None or not isinstance(total_data_df, pd.DataFrame) or total_data_df.empty:
        tab_container.info(t("total_score_not_set"))
        return
    
    total_score = st.session_state.total_score
    q_score = st.session_state.q_score
    v_score = st.session_state.v_score
    di_score = st.session_state.di_score
    
    datasets = {
        'Quantitative': {
            'color': 'red',
            'scale': np.array([
                90, 89, 88, 87, 86, 85, 84, 83, 82, 81,
                80, 79, 78, 77, 76, 75, 74, 73, 72, 71,
                70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60
            ]),
            'percentile': np.array([
                100, 97, 95, 94, 91, 88, 85, 81, 76, 70,
                64, 57, 50, 43, 37, 32, 26, 22, 19, 15,
                12, 10, 8, 6, 4, 3, 2, 2, 1, 1, 1
            ])
        },
        'Verbal': {
            'color': 'blue',
            'scale': np.array([
                90, 89, 88, 87, 86, 85, 84, 83, 82, 81,
                80, 79, 78, 77, 76, 75, 74, 73, 72, 71,
                70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60
            ]),
            'percentile': np.array([
                100, 99, 99, 98, 97, 94, 90, 84, 76, 67,
                57, 48, 39, 31, 23, 18, 13, 10, 7, 5,
                4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1
            ])
        },
        'Data Insights': {
            'color': 'black',
            'scale': np.array([
                90, 89, 88, 87, 86, 85, 84, 83, 82, 81,
                80, 79, 78, 77, 76, 75, 74, 73, 72, 71,
                70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60
            ]),
            'percentile': np.array([
                100, 100, 99, 99, 99, 98, 97, 96, 93, 89,
                84, 77, 70, 63, 54, 48, 42, 36, 31, 26,
                21, 18, 15, 12, 10, 8, 7, 6, 5, 4, 4
            ])
        }
    }
    
    def find_percentile(scale_score, dataset):
        scale = dataset['scale'][::-1]
        percentile = dataset['percentile'][::-1]
    
        if scale_score < scale[0]:
            return percentile[0]
        elif scale_score > scale[-1]:
            return percentile[-1]
        else:
            return np.interp(scale_score, scale, percentile)
    
    q_percentile = find_percentile(q_score, datasets['Quantitative'])
    v_percentile = find_percentile(v_score, datasets['Verbal'])
    di_percentile = find_percentile(di_score, datasets['Data Insights'])
    
    total_scores = np.array([800, 770, 740, 710, 680, 650, 620, 590, 560, 530, 500, 450, 400, 350, 300, 250, 200])
    total_percentiles = np.array([99.9, 99, 97, 92, 85, 75, 65, 51, 38, 28, 18, 8, 4, 2, 1, 0.5, 0.1])
    
    total_percentile = np.interp(total_score, total_scores[::-1], total_percentiles[::-1])
    
    tab_container.subheader(t("three_subjects_score_percentile_chart"))
    
    candidate_scores = {
        'Quantitative': q_score,
        'Verbal': v_score,
        'Data Insights': di_score
    }
    
    fig_combined = go.Figure()
    
    colors = {
        'Quantitative': 'red',
        'Verbal': 'blue',
        'Data Insights': 'black'
    }
    
    for name, dataset in datasets.items():
        fig_combined.add_trace(
            go.Scatter(
                x=dataset['scale'],
                y=dataset['percentile'],
                mode='lines+markers',
                name=name,
                line=dict(color=colors[name], width=2),
                marker=dict(size=6, color=colors[name])
            )
        )
        
        score = candidate_scores[name]
        percentile = find_percentile(score, dataset)
        
        sorted_scale = dataset['scale'][::-1]
        sorted_percentile = dataset['percentile'][::-1]
        
        from scipy.interpolate import interp1d
        
        idx = np.searchsorted(sorted_scale, score)
        if idx > 0 and idx < len(sorted_scale):
            x_left = sorted_scale[idx-1]
            y_left = sorted_percentile[idx-1]
            x_right = sorted_scale[idx+1] if idx+1 < len(sorted_scale) else sorted_scale[idx]
            y_right = sorted_percentile[idx+1] if idx+1 < len(sorted_percentile) else sorted_percentile[idx]
            
            slope = (y_right - y_left) / (x_right - x_left)
            
            tangent_range = 5
            x_min = max(score - tangent_range, sorted_scale[0])
            x_max = min(score + tangent_range, sorted_scale[-1])
            x_tangent = np.linspace(x_min, x_max, 50)
            
            y_tangent = percentile + slope * (x_tangent - score)
            
            fig_combined.add_trace(
                go.Scatter(
                    x=x_tangent,
                    y=y_tangent,
                    mode='lines',
                    line=dict(color=colors[name], dash='dash', width=2),
                    name=t("score_tangent_line").format(name),
                    showlegend=False
                )
            )
        
        fig_combined.add_trace(
            go.Scatter(
                x=[score],
                y=[percentile],
                mode='markers',
                name=t("score_point").format(name),
                marker=dict(
                    color=colors[name],
                    size=15,
                    symbol='x',
                    line=dict(color='white', width=2)
                )
            )
        )
    
    fig_combined.update_layout(
        title=t("gmat_score_percentile_relationship"),
        xaxis_title=t("scale_score_axis"),
        yaxis_title=t("percentile_axis"),
        xaxis=dict(range=[60, 90], tickmode='linear', tick0=60, dtick=5),
        yaxis=dict(range=[0, 100], tickmode='linear', tick0=0, dtick=10),
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        grid=dict(rows=1, columns=1),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", size=12)
    )
    
    fig_combined.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig_combined.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    
    tab_container.plotly_chart(fig_combined, use_container_width=True)
    
    tab_container.subheader(t("scale_percentile_relationship"))
    tab_container.markdown("""
    <iframe width="560" height="315" src="https://www.youtube.com/embed/MLVT-zxaBkE?si=9SJ68LSrvvii35p-" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    """, unsafe_allow_html=True)

# --- Function to generate new diagnostic report based on edited tags ---
def generate_new_diagnostic_report(df: pd.DataFrame) -> str:
    """
    Generate a new diagnostic report based on the provided DataFrame.
    
    Args:
        df: DataFrame containing diagnostic data
        
    Returns:
        A markdown string representing the new diagnostic report.
    """
    report_parts = [f"### {t('new_diagnostic_report')}"]

    if df is None or df.empty:
        report_parts.append(f"* {t('no_analysis_data')}")
        return "\n".join(report_parts)

    V_SKILL_CATEGORIES_TAGS = {
        "Analysis/Critique": {
            t('v_skill_cr_reasoning_barriers'): [t('v_tag_abstract_logic_terminology_difficulty'), t('v_tag_core_issue_identification_difficulty'), t('v_tag_logical_thinking_time_consuming'), t('v_tag_logical_chain_analysis_error'), t('v_tag_prediction_direction_error_missing')],
            t('v_skill_cr_method_application'): [t('v_tag_specific_question_type_method_error')],
            t('v_skill_cr_option_analysis'): [t('v_tag_strong_interference_option_confusion'), t('v_tag_option_understanding_difficulty'), t('v_tag_option_relevance_judgment_error'), t('v_tag_option_screening_time_consuming')],
            t('v_skill_cr_reading_comprehension'): [t('v_tag_reading_time_consuming'), t('v_tag_stem_understanding_barrier')],
            t('v_skill_cr_question_understanding'): [t('v_tag_question_requirement_grasp_error')],
            t('v_skill_other'): [t('v_tag_data_invalid_time_pressure')]
        },
        "Identify Inferred Idea": {
            t('v_skill_rc_positioning_ability'): [t('v_tag_positioning_efficiency_low_repeated'), t('v_tag_positioning_error_efficiency_low')],
            t('v_skill_rc_reasoning_barriers'): [t('v_tag_reasoning_ability_insufficient'), t('v_tag_deep_thinking_time_consuming')],
            t('v_skill_rc_option_analysis'): [t('v_tag_option_understanding_analysis_difficulty'), t('v_tag_option_screening_time_consuming')],
            t('v_skill_rc_reading_method'): [t('v_tag_reading_method_efficiency_low')],
            t('v_skill_rc_reading_comprehension'): [t('v_tag_ignore_keywords_logic'), t('v_tag_specific_domain_background_knowledge_lack'), t('v_tag_passage_structure_grasp_unclear'), t('v_tag_vocabulary_bottleneck'), t('v_tag_long_difficult_sentence_analysis_difficulty'), t('v_tag_reading_speed_slow_basic_problem'), t('v_tag_key_information_positioning_understanding_error'), t('v_tag_reading_accuracy_insufficient')],
            t('v_skill_rc_question_understanding'): [t('v_tag_question_focus_grasp_error')],
            t('v_skill_rc_method_application'): [t('v_tag_specific_question_type_recall_secondary_evidence')],
            t('v_skill_foundational_mastery'): [t('v_tag_application_unstable_sfe')],
            t('v_skill_efficiency_issues'): [t('v_tag_information_positioning_efficiency_low'), t('v_tag_reasoning_analysis_efficiency_low'), t('v_tag_option_analysis_efficiency_low'), t('v_tag_reading_comprehension_efficiency_low')],
            t('v_skill_behavioral_patterns'): [t('carelessness_issue_high_fast_wrong_ratio')]
        },
        "Identify Stated Idea": {
            t('v_skill_efficiency_issues'): [t('v_tag_information_positioning_efficiency_low'), t('v_tag_reasoning_analysis_efficiency_low'), t('v_tag_option_analysis_efficiency_low'), t('v_tag_reading_comprehension_efficiency_low')],
            t('v_skill_other'): [t('v_tag_data_invalid_time_pressure')]
        },
        "Plan/Construct": {
            t('v_skill_cr_reasoning_barriers'): [t('v_tag_abstract_logic_terminology_difficulty'), t('v_tag_core_issue_identification_difficulty'), t('v_tag_logical_thinking_time_consuming'), t('v_tag_logical_chain_analysis_error'), t('v_tag_prediction_direction_error_missing')],
            t('v_skill_cr_method_application'): [t('v_tag_not_follow_standard_process'), t('v_tag_specific_question_type_method_error')],
            t('v_skill_cr_option_analysis'): [t('v_tag_strong_interference_option_confusion'), t('v_tag_option_understanding_difficulty'), t('v_tag_option_relevance_judgment_error'), t('v_tag_option_screening_time_consuming')],
            t('v_skill_cr_reading_comprehension'): [t('v_tag_basic_understanding_omission'), t('v_tag_reading_time_consuming'), t('v_tag_stem_understanding_barrier')],
            t('v_skill_cr_question_understanding'): [t('v_tag_question_requirement_grasp_error')],
            t('v_skill_foundational_mastery'): [t('v_tag_application_unstable_sfe')],
            t('v_skill_efficiency_issues'): [t('v_tag_reasoning_analysis_efficiency_low'), t('v_tag_option_analysis_efficiency_low'), t('v_tag_reading_comprehension_efficiency_low')],
            t('v_skill_behavioral_patterns'): [t('carelessness_issue_high_fast_wrong_ratio')]
        }
    }

    required_cols_q = ["Subject", "question_position", "question_type", "question_fundamental_skill", "diagnostic_params_list"]
    required_cols_v = ["Subject", "question_position", "question_fundamental_skill", "diagnostic_params_list"]
    required_cols_di = ["Subject", "question_position", "content_domain", "question_type", "diagnostic_params_list"]

    for subject in ["Q", "V", "DI"]:
        subject_df = df[df["Subject"] == subject].copy()
        if subject_df.empty:
            continue

        report_parts.append(t('report_subject_classification_results').format(subject))
        missing_columns = []

        if subject == "Q":
            missing_columns = [col for col in required_cols_q if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**{t('report_q_subject_missing_columns').format(', '.join(missing_columns))}**")
                continue
            grouped = subject_df.groupby(["question_type", "question_fundamental_skill"], dropna=False)
            if not any(grouped):
                report_parts.append(f"**{t('report_q_subject_no_classification_data')}**")
            for (q_type, f_skill), group_data in grouped:
                q_type_str = str(q_type) if pd.notna(q_type) else t('report_unknown_question_type')
                f_skill_str = str(f_skill) if pd.notna(f_skill) else t('report_unknown_skill')
                report_parts.append(f"\n##### {t('report_q_subject_classification')}")
                report_parts.append(f"**{t('report_question_type_label')}** {q_type_str} | **{t('report_skill_label')}** {f_skill_str}")
                report_parts.append("")
                
                all_tags_in_group = []
                if not group_data.empty:
                    for _, row in group_data.iterrows():
                        tags_for_question = row.get("diagnostic_params_list", [])
                        if isinstance(tags_for_question, list):
                            all_tags_in_group.extend(tags_for_question)
                        elif isinstance(tags_for_question, str) and tags_for_question.strip():
                            all_tags_in_group.extend([t.strip() for t in tags_for_question.split(',') if t.strip()])
                
                unique_tags = sorted(list(set(str(tag).strip() for tag in all_tags_in_group if tag and str(tag).strip())))
                if unique_tags:
                    report_parts.append(f"| {t('report_category_label')} | {t('report_diagnostic_tags_label')} |")
                    report_parts.append("|------|----------|")
                    tags_display_str = "<br>".join(unique_tags)
                    report_parts.append(f"| {t('report_diagnostic_findings_label')} | {tags_display_str} |")
                else:
                    report_parts.append(f"**{t('report_diagnostic_result_no_common_tags')}**")
                report_parts.append("")
        
        elif subject == "V":
            missing_columns = [col for col in required_cols_v if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**{t('report_v_subject_missing_columns').format(', '.join(missing_columns))}**")
                continue
            grouped = subject_df.groupby(["question_fundamental_skill"], dropna=False)
            if not any(grouped):
                report_parts.append(f"**{t('report_v_subject_no_classification_data')}**")
            for f_skill, group_data in grouped:
                f_skill_str = str(f_skill) if pd.notna(f_skill) else t('report_unknown_skill')
                report_parts.append(f"\n##### {t('report_v_subject_skill_classification')}")
                report_parts.append(f"**{t('report_skill_domain_label')}** {f_skill_str}")
                report_parts.append("")

                student_unique_tags_for_skill = set()
                if not group_data.empty:
                    for _, row in group_data.iterrows():
                        tags_for_question = row.get("diagnostic_params_list", [])
                        if isinstance(tags_for_question, list):
                            for tag in tags_for_question:
                                if tag and str(tag).strip():
                                    student_unique_tags_for_skill.add(str(tag).strip())
                        elif isinstance(tags_for_question, str) and tags_for_question.strip():
                            for t_tag in tags_for_question.split(','):
                                if t_tag and t_tag.strip():
                                    student_unique_tags_for_skill.add(t_tag.strip())
                
                if f_skill_str in V_SKILL_CATEGORIES_TAGS:
                    report_parts.append(f"| {t('report_category_label')} | {t('report_diagnostic_findings_category')} |")
                    report_parts.append("|------|----------|")
                    skill_map = V_SKILL_CATEGORIES_TAGS[f_skill_str]
                    has_content_for_skill = False
                    for category, predefined_tags in skill_map.items():
                        tags_to_display_for_category = sorted([tag for tag in predefined_tags if tag in student_unique_tags_for_skill])
                        if tags_to_display_for_category:
                            has_content_for_skill = True
                            joined_tags = "<br>".join(tags_to_display_for_category)
                            report_parts.append(f"| {category} | {joined_tags} |")
                    if not has_content_for_skill:
                         report_parts.append(f"| {t('report_no_corresponding_classification')} | {t('report_no_matching_predefined_tags')} |")
                else:
                    sorted_unique_student_tags = sorted(list(student_unique_tags_for_skill))
                    if sorted_unique_student_tags:
                        report_parts.append(f"| {t('report_category_label')} | {t('report_diagnostic_tags_label')} |")
                        report_parts.append("|------|----------|")
                        tags_display_str = "<br>".join(sorted_unique_student_tags)
                        report_parts.append(f"| {t('report_diagnostic_findings_label')} | {tags_display_str} |")
                    else:
                        report_parts.append(f"**{t('report_diagnostic_result_no_common_tags')}**")
                report_parts.append("")

        elif subject == "DI":
            missing_columns = [col for col in required_cols_di if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**{t('report_di_subject_missing_columns').format(', '.join(missing_columns))}**")
                continue
            grouped = subject_df.groupby(["content_domain", "question_type"], dropna=False)
            if not any(grouped):
                report_parts.append(f"**{t('report_di_subject_no_classification_data')}**")
            for (c_domain, q_type), group_data in grouped:
                c_domain_str = str(c_domain) if pd.notna(c_domain) else t('report_unknown_content_domain')
                q_type_str = str(q_type) if pd.notna(q_type) else t('report_unknown_question_type')
                report_parts.append(f"\n##### {t('report_di_subject_classification')}")
                report_parts.append(f"**{t('report_content_domain_label')}** {c_domain_str} | **{t('report_question_type_label')}** {q_type_str}")
                report_parts.append("")

                all_tags_in_group = []
                if not group_data.empty:
                    for _, row in group_data.iterrows():
                        tags_for_question = row.get("diagnostic_params_list", [])
                        if isinstance(tags_for_question, list):
                            all_tags_in_group.extend(tags_for_question)
                        elif isinstance(tags_for_question, str) and tags_for_question.strip():
                            all_tags_in_group.extend([t.strip() for t in tags_for_question.split(',') if t.strip()])
                
                unique_tags = sorted(list(set(str(tag).strip() for tag in all_tags_in_group if tag and str(tag).strip())))
                if unique_tags:
                    report_parts.append(f"| {t('report_category_label')} | {t('report_diagnostic_tags_label')} |")
                    report_parts.append("|------|----------|")
                    tags_display_str = "<br>".join(unique_tags)
                    report_parts.append(f"| {t('report_diagnostic_findings_label')} | {tags_display_str} |")
                else:
                    report_parts.append(f"**{t('report_diagnostic_result_no_common_tags')}**")
                report_parts.append("")

    return "\n".join(report_parts)

# --- Display Results Function (Moved from app.py) ---
def display_results():
    """Displays all diagnostic results in separate tabs."""
    if not st.session_state.get("diagnosis_complete", False) and not st.session_state.get("original_processed_df") :
        st.info(t('display_results_no_analysis'))
        return

    tab_titles = [t('display_results_total_tab')]
    if st.session_state.get("consolidated_report_text"):
        tab_titles.append(t('display_results_ai_summary_tab'))
    
    tab_titles.extend([t('display_results_subject_results_tab').format(subject) for subject in SUBJECTS])
    tab_titles.append(t('display_results_edit_tags_tab'))
    tab_titles.append(t('display_results_ai_chat_tab'))

    tabs = st.tabs(tab_titles)
    
    current_tab_index = 0

    with tabs[current_tab_index]:
        display_total_results(tabs[current_tab_index])
    current_tab_index += 1
    
    if t('display_results_ai_summary_tab') in tab_titles:
        with tabs[current_tab_index]:
            tabs[current_tab_index].subheader(t('display_results_ai_summary_title'))
            report_text_to_display = st.session_state.get("consolidated_report_text", t('display_results_ai_summary_generating'))
            from gmat_diagnosis_app.utils.styling import create_report_container
            create_report_container(report_text_to_display)
        current_tab_index += 1

    for subject in SUBJECTS: 
        report_md = st.session_state.report_dict.get(subject, t('display_results_subject_report_not_found').format(subject))
        df_for_subject_display = st.session_state.processed_df if st.session_state.processed_df is not None else st.session_state.original_processed_df
        
        df_subject = pd.DataFrame()
        if df_for_subject_display is not None and not df_for_subject_display.empty:
            df_subject = df_for_subject_display[df_for_subject_display['Subject'] == subject]
        
        subject_tab_title = t('display_results_subject_results_tab').format(subject)
        try:
            actual_tab_index_for_subject = tab_titles.index(subject_tab_title)
            with tabs[actual_tab_index_for_subject]:
                display_subject_results(subject, tabs[actual_tab_index_for_subject], report_md, df_subject, COLUMN_DISPLAY_CONFIG, EXCEL_COLUMN_MAP)
        except ValueError:
            st.error(t('display_results_tab_not_found_error').format(subject_tab_title, tab_titles))

    edit_tab_title = t('display_results_edit_tags_tab')
    try:
        edit_tab_index = tab_titles.index(edit_tab_title)
        with tabs[edit_tab_index]:
            tabs[edit_tab_index].subheader(t('edit_tags_title'))
            
            if st.session_state.original_processed_df is None:
                tabs[edit_tab_index].info(t('edit_tags_no_data'))
            else:
                if "reset_editable_df_requested" in st.session_state and st.session_state.reset_editable_df_requested:
                    st.session_state.editable_diagnostic_df = st.session_state.original_processed_df.copy(deep=True)
                    st.session_state._editable_df_source = st.session_state.original_processed_df
                    tabs[edit_tab_index].success(t('edit_tags_reset_success'))
                    if 'generated_ai_prompts_for_edit_tab' in st.session_state:
                        del st.session_state['generated_ai_prompts_for_edit_tab']
                    st.session_state.reset_editable_df_requested = False
                
                if 'editable_diagnostic_df' not in st.session_state or st.session_state.original_processed_df is not st.session_state.get('_editable_df_source'):
                    st.session_state.editable_diagnostic_df = st.session_state.original_processed_df.copy()
                    st.session_state._editable_df_source = st.session_state.original_processed_df

                user_requested_internal_names = [
                    "Subject", "question_position", "is_correct", "question_time",
                    "question_type", "content_domain", "question_fundamental_skill",
                    "is_invalid", "time_performance_category", "diagnostic_params_list"
                ]
                
                cols_to_display = [col for col in user_requested_internal_names if col in st.session_state.editable_diagnostic_df.columns]
                df_for_editor = st.session_state.editable_diagnostic_df[cols_to_display].copy()

                if 'diagnostic_params_list' in df_for_editor.columns:
                    def format_tags_for_text_editor(tags_list):
                        if isinstance(tags_list, list):
                            return ", ".join(str(tag).strip() for tag in tags_list if tag and str(tag).strip())
                        if pd.isna(tags_list) or tags_list is None:
                            return ""
                        return str(tags_list).strip()
                    df_for_editor['diagnostic_params_list'] = df_for_editor['diagnostic_params_list'].apply(format_tags_for_text_editor)

                editor_column_config = {
                    "Subject": st.column_config.TextColumn(t('edit_column_subject'), disabled=True),
                    "question_position": st.column_config.NumberColumn(t('edit_column_question_position'), help=t('edit_column_question_position_help'), disabled=True),
                    "is_correct": st.column_config.CheckboxColumn(t('edit_column_is_correct'), help=t('edit_column_is_correct_help'), disabled=True),
                    "question_time": st.column_config.NumberColumn(t('edit_column_question_time'), help=t('edit_column_question_time_help'), format="%.2f", disabled=True),
                    "question_type": st.column_config.TextColumn(t('edit_column_question_type'), disabled=True),
                    "content_domain": st.column_config.TextColumn(t('edit_column_content_domain'), disabled=True),
                    "question_fundamental_skill": st.column_config.TextColumn(t('edit_column_question_fundamental_skill'), disabled=True),
                    "is_invalid": st.column_config.CheckboxColumn(t('edit_column_is_invalid'), help=t('edit_column_is_invalid_help'), disabled=True),
                    "time_performance_category": st.column_config.SelectboxColumn(
                        t('edit_column_time_performance_category'),
                        help=t('edit_column_time_performance_help'),
                        options=["Slow & Wrong", "Slow & Correct", "Normal Time & Wrong", "Normal Time & Correct", "Fast & Wrong", "Fast & Correct", "N/A"],
                        required=True
                    ),
                    "diagnostic_params_list": st.column_config.TextColumn(
                        t('edit_column_diagnostic_params_list'),
                        help=t('edit_column_diagnostic_params_help'),
                        width="large"
                    )
                }
                
                final_editor_column_config = {k: v for k, v in editor_column_config.items() if k in df_for_editor.columns}

                tabs[edit_tab_index].markdown(f"**{t('edit_tags_description')}**")
                
                tag_trimming_expander = tabs[edit_tab_index].expander(t('tag_trimming_assistant_title'), expanded=False)
                tag_trimming_expander.markdown(t('tag_trimming_assistant_description'), unsafe_allow_html=True)

                original_tags_input = tag_trimming_expander.text_area(
                    t('tag_trimming_original_tags_label'), 
                    key="trim_original_tags",
                    height=100
                )
                user_description_input = tag_trimming_expander.text_area(
                    t('tag_trimming_user_description_label'), 
                    key="trim_user_description",
                    height=100
                )

                if tag_trimming_expander.button(t('tag_trimming_request_button'), key="trim_tags_button"):
                    if not original_tags_input.strip() or not user_description_input.strip():
                        tag_trimming_expander.warning(t('tag_trimming_input_required'))
                    elif not st.session_state.get('master_key'):
                        tag_trimming_expander.error(t('tag_trimming_master_key_error'))
                    else:
                        with st.spinner(t('tag_trimming_ai_processing')):
                            master_key = st.session_state.master_key
                            try:
                                trimmed_suggestion = trim_diagnostic_tags_with_openai(
                                    original_tags_input,
                                    user_description_input,
                                    master_key
                                )
                                st.session_state.trimmed_tags_suggestion = trimmed_suggestion
                            except Exception as e:
                                st.session_state.trimmed_tags_suggestion = t('tag_trimming_ai_error').format(str(e))
                                logging.error(f"Error calling trim_diagnostic_tags_with_openai: {e}", exc_info=True)
                
                if "trimmed_tags_suggestion" in st.session_state:
                    tag_trimming_expander.markdown(f"##### {t('tag_trimming_result_title')}")
                    suggestion_to_display = st.session_state.trimmed_tags_suggestion
                    if suggestion_to_display.startswith(t('tag_trimming_error_prefix')) or suggestion_to_display.startswith(t('tag_trimming_ai_failed_prefix')):
                        tag_trimming_expander.error(suggestion_to_display)
                    elif suggestion_to_display == t('tag_trimming_no_match'):
                        tag_trimming_expander.info(suggestion_to_display)
                    else:
                        tag_trimming_expander.success(t('tag_trimming_suggested_tags').format(suggestion_to_display))
                        tag_trimming_expander.markdown(t('tag_trimming_usage_instruction'))
                # --- End of Tag Trimming Assistant ---

                # 添加一個保存編輯器內容的callback函數
                def save_editor_content():
                    # 當data_editor內容變更時，此函數將被調用
                    if "diagnosis_label_editor" in st.session_state:
                        edited_content = st.session_state["diagnosis_label_editor"]
                        logging.info(f"[save_editor_content] Received editor content of type: {type(edited_content)}")
                        
                        if edited_content is not None:
                            updated_full_df = st.session_state.editable_diagnostic_df.copy()
                            
                            # 處理編輯的內容（在session_state中可能是字典格式）
                            if isinstance(edited_content, dict):
                                logging.info(f"[save_editor_content] Handling dictionary content with keys: {edited_content.keys()}")
                                
                                # 嘗試檢查其他可能的編輯數據結構
                                if 'edited_rows' in edited_content:
                                    edited_rows = edited_content.get('edited_rows', {})
                                    logging.info(f"[save_editor_content] Found {len(edited_rows)} edited rows")
                                    
                                    if not edited_rows:
                                        logging.info("[save_editor_content] No rows were edited")
                                    
                                    # 處理編輯的行
                                    for idx_str, row_edits in edited_rows.items():
                                        try:
                                            # 嘗試將索引轉換為整數，用於定位DataFrame的行
                                            idx = int(idx_str)
                                            logging.info(f"[save_editor_content] Processing edits for row {idx}: {row_edits}")
                                            
                                            # 確保索引在DataFrame的有效範圍內
                                            if 0 <= idx < len(updated_full_df):
                                                for col_name, new_value in row_edits.items():
                                                    if col_name in updated_full_df.columns:
                                                        if col_name == 'diagnostic_params_list':
                                                            if pd.isna(new_value) or not isinstance(new_value, str) or not new_value.strip():
                                                                updated_full_df.at[idx, col_name] = []
                                                            else:
                                                                tags = [tag.strip() for tag in new_value.split(',') if tag.strip()]
                                                                updated_full_df.at[idx, col_name] = tags
                                                                logging.info(f"[save_editor_content] Updated tags for row {idx}: {tags}")
                                                        else:
                                                            updated_full_df.at[idx, col_name] = new_value
                                                            logging.info(f"[save_editor_content] Updated {col_name} for row {idx} to: {new_value}")
                                            else:
                                                logging.warning(f"[save_editor_content] Index {idx} is out of range for DataFrame with length {len(updated_full_df)}")
                                        except (ValueError, IndexError) as e:
                                            logging.error(f"[save_editor_content] Error processing row with idx {idx_str}: {e}")
                                            # 如果索引不是整數，嘗試使用DataFrame的iloc或loc進行更新
                                            try:
                                                if hasattr(updated_full_df, 'iloc'):
                                                    # 嘗試使用iloc
                                                    idx = int(idx_str)
                                                    if 0 <= idx < len(updated_full_df):
                                                        for col_name, new_value in row_edits.items():
                                                            if col_name in updated_full_df.columns:
                                                                if col_name == 'diagnostic_params_list':
                                                                    if pd.isna(new_value) or not isinstance(new_value, str) or not new_value.strip():
                                                                        updated_full_df.iloc[idx, updated_full_df.columns.get_loc(col_name)] = []
                                                                    else:
                                                                        tags = [tag.strip() for tag in new_value.split(',') if tag.strip()]
                                                                        updated_full_df.iloc[idx, updated_full_df.columns.get_loc(col_name)] = tags
                                                                else:
                                                                    updated_full_df.iloc[idx, updated_full_df.columns.get_loc(col_name)] = new_value
                                            except Exception as inner_e:
                                                logging.error(f"[save_editor_content] Failed to update row using iloc: {inner_e}")
                                elif 'added_rows' in edited_content:
                                    # 處理新增的行
                                    added_rows = edited_content.get('added_rows', [])
                                    logging.info(f"[save_editor_content] Found {len(added_rows)} added rows")
                                    # 這裡可以處理新增行的邏輯，但當前版本似乎不需要
                                elif 'deleted_rows' in edited_content:
                                    # 處理刪除的行
                                    deleted_rows = edited_content.get('deleted_rows', [])
                                    logging.info(f"[save_editor_content] Found {len(deleted_rows)} deleted rows")
                                    # 這裡可以處理刪除行的邏輯，但當前版本似乎不需要
                                else:
                                    # 嘗試直接使用字典的值作為更新
                                    logging.info(f"[save_editor_content] No standard edit data found. Available keys: {edited_content.keys()}")
                                    
                                    # 嘗試獲取數據
                                    if hasattr(edited_content, 'values'):
                                        # 檢查值的類型
                                        values = edited_content.values()
                                        if any(isinstance(value, dict) for value in values):
                                            # 如果有字典值，嘗試搜尋診斷標籤
                                            for key, value in edited_content.items():
                                                if isinstance(value, dict) and 'diagnostic_params_list' in value:
                                                    logging.info(f"[save_editor_content] Found diagnostic_params_list in edited_content[{key}]")
                                                    # 處理診斷標籤
                                        else:
                                            logging.warning(f"[save_editor_content] No dictionary values found in edited_content")
                                    else:
                                        logging.warning(f"[save_editor_content] edited_content does not have values attribute")
                            elif hasattr(edited_content, 'columns'):  # 如果是DataFrame格式
                                logging.info(f"[save_editor_content] Handling DataFrame content with columns: {edited_content.columns.tolist()}")
                                for col_name in edited_content.columns:
                                    if col_name in updated_full_df.columns:
                                        if col_name == 'diagnostic_params_list':
                                            def parse_tags_from_text_editor(tags_str):
                                                if pd.isna(tags_str) or not isinstance(tags_str, str) or not tags_str.strip():
                                                    return []
                                                return [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                                            
                                            updated_full_df[col_name] = edited_content[col_name].apply(parse_tags_from_text_editor)
                                            logging.info(f"[save_editor_content] Updated all tags in column {col_name}")
                                        else:
                                            updated_full_df[col_name] = edited_content[col_name]
                                            logging.info(f"[save_editor_content] Updated entire column {col_name}")
                            elif isinstance(edited_content, pd.DataFrame):  # 另一種檢查DataFrame的方式
                                logging.info(f"[save_editor_content] Handling DataFrame content (instance check) with shape: {edited_content.shape}")
                                for col_name in edited_content.columns:
                                    if col_name in updated_full_df.columns:
                                        if col_name == 'diagnostic_params_list':
                                            def parse_tags_from_text_editor(tags_str):
                                                if pd.isna(tags_str) or not isinstance(tags_str, str) or not tags_str.strip():
                                                    return []
                                                return [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                                            
                                            updated_full_df[col_name] = edited_content[col_name].apply(parse_tags_from_text_editor)
                                            logging.info(f"[save_editor_content] Updated all tags in column {col_name}")
                                        else:
                                            updated_full_df[col_name] = edited_content[col_name]
                                            logging.info(f"[save_editor_content] Updated entire column {col_name}")
                            else:
                                logging.error(f"[save_editor_content] Unsupported content type: {type(edited_content)}")
                            
                            # 立即保存更新後的數據框到session_state
                            st.session_state.editable_diagnostic_df = updated_full_df
                            # 設置一個標誌表示有未保存的變更
                            st.session_state.has_unsaved_changes = True
                            logging.info(f"[save_editor_content] Successfully saved changes and updated session state")
                        else:
                            logging.warning("[save_editor_content] Received None as editor content")

                edited_df_subset_from_editor = tabs[edit_tab_index].data_editor(
                    df_for_editor,
                    column_config=final_editor_column_config,
                    use_container_width=True,
                    num_rows="fixed", 
                    key="diagnosis_label_editor",
                    on_change=save_editor_content  # 使用我們的callback函數來立即保存變更
                )
                
                # 當有未保存的變更時顯示提示
                if st.session_state.get('has_unsaved_changes', False):
                    tabs[edit_tab_index].info(t('edit_tags_unsaved_changes'))

                if 'changes_saved' not in st.session_state:
                    st.session_state.changes_saved = False
                if 'has_unsaved_changes' not in st.session_state:
                    st.session_state.has_unsaved_changes = False

                col1, col2, col3 = tabs[edit_tab_index].columns(3)

                with col1:
                    if st.button(t('edit_tags_reset_button'), key="reset_button_col", use_container_width=True):
                        st.session_state.reset_editable_df_requested = True
                        st.session_state.ai_prompts_need_regeneration = False
                        st.session_state.changes_saved = False
                        st.session_state.has_unsaved_changes = False
                        st.rerun()

                with col2:
                    if st.button(t('edit_tags_apply_button'), key="apply_editable_df_col", type="primary", use_container_width=True):
                        # 如果已有未保存的變更，確保已保存到editable_diagnostic_df
                        st.session_state.has_unsaved_changes = False
                        st.session_state.ai_prompts_need_regeneration = True
                        st.session_state.changes_saved = True
                        tabs[edit_tab_index].success(t('edit_tags_apply_success'))
                        if st.session_state.get("editable_diagnostic_df") is not None:
                            new_report_content = generate_new_diagnostic_report(st.session_state.editable_diagnostic_df)
                            st.session_state.generated_new_diagnostic_report = new_report_content
                            with tabs[edit_tab_index].expander(t('new_diagnostic_report_title'), expanded=False):
                                st.markdown(new_report_content, unsafe_allow_html=True)
                        else:
                            with tabs[edit_tab_index].expander(t('new_diagnostic_report_title'), expanded=False):
                                st.warning(t('edit_tags_no_data_error'))
                
                with col3:
                    if st.button(t('edit_tags_download_button'), key="download_edited_file_trigger_col", use_container_width=True):
                        if st.session_state.get('has_unsaved_changes', False):
                            tabs[edit_tab_index].warning(t('edit_tags_unsaved_warning'), icon="⚠️")
                        elif st.session_state.get('changes_saved', False):
                            try:
                                df_to_export = st.session_state.editable_diagnostic_df.copy() # Start with internal names
                                logging.info(f"[Download Edited] Initial columns: {df_to_export.columns.tolist()}")

                                # --- Merge Logic (Operates on internal names) ---
                                if 'question_difficulty' not in df_to_export.columns and 'all_subjects_df_for_diagnosis' in st.session_state and not st.session_state.all_subjects_df_for_diagnosis.empty:
                                    source_df = st.session_state.all_subjects_df_for_diagnosis
                                    merge_keys = ['Subject', 'question_position']
                                    logging.info(f"[Download Edited] Attempting merge. Source df columns: {source_df.columns.tolist()}")
                                    
                                    source_has_keys = all(key in source_df.columns for key in merge_keys)
                                    target_has_keys = all(key in df_to_export.columns for key in merge_keys)
                                    source_has_difficulty = 'question_difficulty' in source_df.columns
                                    
                                    logging.info(f"[Download Edited] Merge Check: source_has_keys={source_has_keys}, target_has_keys={target_has_keys}, source_has_difficulty={source_has_difficulty}")

                                    if source_has_keys and target_has_keys and source_has_difficulty:
                                        try:
                                            if 'question_position' in merge_keys:
                                                if df_to_export['question_position'].dtype != source_df['question_position'].dtype:
                                                    logging.warning(f"[Download Edited] Type mismatch for 'question_position': {df_to_export['question_position'].dtype} vs {source_df['question_position'].dtype}. Attempting coercion.")
                                                    try:
                                                        df_to_export['question_position'] = pd.to_numeric(df_to_export['question_position'], errors='coerce').astype('Int64')
                                                        source_df_temp = source_df.copy()
                                                        source_df_temp['question_position'] = pd.to_numeric(source_df_temp['question_position'], errors='coerce').astype('Int64')
                                                        source_df_for_merge = source_df_temp
                                                        logging.info("[Download Edited] Coerced 'question_position' to Int64 for merge.")
                                                    except Exception as e:
                                                        logging.error(f"[Download Edited] Failed to coerce 'question_position' to a common type: {e}")
                                                        source_df_for_merge = source_df
                                                else:
                                                    source_df_for_merge = source_df
                                            else: 
                                                 source_df_for_merge = source_df

                                            difficulty_to_merge = source_df_for_merge[merge_keys + ['question_difficulty']].drop_duplicates(subset=merge_keys)
                                            df_to_export = pd.merge(df_to_export, difficulty_to_merge, on=merge_keys, how='left')
                                            logging.info(f"[Download Edited] Successfully merged 'question_difficulty'. Columns after merge: {df_to_export.columns.tolist()}")
                                        except Exception as e:
                                            logging.error(f"[Download Edited] Failed to merge 'question_difficulty': {e}")
                                    else:
                                        logging.warning("[Download Edited] Merge prerequisites not met. 'question_difficulty' or merge keys missing.")
                                else:
                                    logging.info("[Download Edited] Merge not needed or not possible.")

                                # --- Prepare final map and select columns based on internal names AFTER merge ---
                                final_internal_columns_to_export = [
                                    internal_name
                                    for internal_name in EXCEL_COLUMN_MAP.keys() # Use defined export order/keys
                                    if internal_name in df_to_export.columns # Check if column exists after merge
                                ]
                                df_to_export_final = df_to_export[final_internal_columns_to_export].copy() # Select final columns with internal names

                                # Create the map only for the selected columns
                                excel_column_map_for_export_final = {
                                    internal_name: EXCEL_COLUMN_MAP[internal_name]
                                    for internal_name in final_internal_columns_to_export
                                }
                                logging.info(f"[Download Edited] Final internal columns selected: {final_internal_columns_to_export}")
                                logging.info(f"[Download Edited] Final map for to_excel: {excel_column_map_for_export_final}")

                                # --- Data Type Conversion / Formatting (before to_excel) ---
                                # Convert lists to strings
                                if 'diagnostic_params_list' in df_to_export_final.columns:
                                    df_to_export_final['diagnostic_params_list'] = df_to_export_final['diagnostic_params_list'].apply(
                                        lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
                                    )
                                # Ensure boolean-like columns are strings if needed by to_excel formatting logic
                                for bool_col in ['is_correct', 'is_sfe', 'is_invalid']:
                                     if bool_col in df_to_export_final.columns:
                                          df_to_export_final[bool_col] = df_to_export_final[bool_col].astype(str)
                                # NOTE: Numeric formatting (e.g., difficulty, time) is handled within to_excel based on the map

                                # --- Call to_excel with internal names and the map ---
                                excel_bytes = to_excel(df_to_export_final, excel_column_map_for_export_final)

                                # Trigger download
                                today_str = pd.Timestamp.now().strftime('%Y%m%d')
                                st.download_button(
                                    label=t('edit_tags_download_button_label'), # This label appears AFTER the initial button click
                                    data=excel_bytes,
                                    file_name=f"{today_str}_GMAT_edited_diagnostic_data.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="actual_download_excel_button_col3_rerun", # Use a different key if needed
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(t('download_excel_error').format(e))
                                logging.error(t('download_excel_error_details').format(traceback.format_exc()))
                        else:
                            st.warning(t('changes_not_saved_download_warning'), icon="⚠️")

                if st.session_state.get('ai_prompts_need_regeneration', False) and st.session_state.changes_saved:
                    with st.spinner(t('ai_prompts_generating')):
                        q_prompts = ""
                        v_prompts = ""
                        di_prompts = ""

                        df_to_generate_prompts = st.session_state.editable_diagnostic_df

                        from gmat_diagnosis_app.diagnostics import generate_q_ai_tool_recommendations
                        q_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'Q']
                        if not q_df_subject.empty: 
                            q_prompts = generate_q_ai_tool_recommendations(q_df_subject)
                        
                        from gmat_diagnosis_app.diagnostics import generate_v_ai_tool_recommendations
                        v_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'V']
                        if not v_df_subject.empty: 
                            v_prompts = generate_v_ai_tool_recommendations(v_df_subject)

                        from gmat_diagnosis_app.diagnostics import generate_di_ai_tool_recommendations
                        di_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'DI']
                        if not di_df_subject.empty: 
                            di_prompts = generate_di_ai_tool_recommendations(di_df_subject)

                        all_prompts = f"### {t('ai_tools_recommendations_title')}\n\n**{t('ai_tools_q_subject')}**\n{q_prompts if q_prompts else t('ai_tools_no_specific_recommendations')}\n\n**{t('ai_tools_v_subject')}**\n{v_prompts if v_prompts else t('ai_tools_no_specific_recommendations')}\n\n**{t('ai_tools_di_subject')}**\n{di_prompts if di_prompts else t('ai_tools_no_specific_recommendations')}"
                        
                        st.session_state.generated_ai_prompts_for_edit_tab = all_prompts
                        st.session_state.ai_prompts_need_regeneration = False
                    
                if 'generated_ai_prompts_for_edit_tab' in st.session_state and st.session_state.changes_saved:
                    with tabs[edit_tab_index].expander(t('ai_tools_recommendations_title'), expanded=False):
                        st.markdown(st.session_state.generated_ai_prompts_for_edit_tab)
                elif not st.session_state.changes_saved and 'generated_ai_prompts_for_edit_tab' in st.session_state:
                    with tabs[edit_tab_index].expander(t('ai_tools_previous_results'), expanded=False):
                        st.info(t('ai_tools_previous_results_info'))
                        st.markdown(st.session_state.generated_ai_prompts_for_edit_tab)

    except ValueError:
        st.error(t('display_results_tab_not_found_error').format(edit_tab_title, tab_titles))
        

    ai_chat_tab_title = t('display_results_ai_chat_tab')
    try:
        ai_chat_tab_index = tab_titles.index(ai_chat_tab_title)
        with tabs[ai_chat_tab_index]:
            tabs[ai_chat_tab_index].subheader(t('ai_chat_title'))
            if st.session_state.get('master_key'):
                display_chat_interface(st.session_state)
            else:
                tabs[ai_chat_tab_index].info(t('ai_chat_master_key_required'))
    except ValueError:
        st.error(t('ai_chat_tab_not_found').format(ai_chat_tab_title)) 