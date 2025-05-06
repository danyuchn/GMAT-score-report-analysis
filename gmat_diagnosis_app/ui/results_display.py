"""
結果顯示模組
顯示診斷結果的功能
"""

import streamlit as st
import pandas as pd
from gmat_diagnosis_app.utils.styling import apply_styles
from gmat_diagnosis_app.utils.excel_utils import to_excel
from gmat_diagnosis_app.constants.config import SUBJECTS, EXCEL_COLUMN_MAP

# --- Column Display Configuration (Moved from app.py) ---
COLUMN_DISPLAY_CONFIG = {
    "question_position": st.column_config.NumberColumn("題號", help="題目順序"),
    "question_type": st.column_config.TextColumn("題型"),
    "question_fundamental_skill": st.column_config.TextColumn("考察能力"),
    "question_difficulty": st.column_config.NumberColumn("難度(模擬)", help="系統模擬的題目難度 (有效題目)", format="%.2f", width="small"),
    "question_time": st.column_config.NumberColumn("用時(分)", format="%.2f", width="small"),
    "time_performance_category": st.column_config.TextColumn("時間表現"),
    "content_domain": st.column_config.TextColumn("內容領域"),
    "diagnostic_params_list": st.column_config.ListColumn("診斷標籤", help="初步診斷標籤", width="medium"),
    "is_correct": st.column_config.CheckboxColumn("答對?", help="是否回答正確"),
    "is_sfe": st.column_config.CheckboxColumn("SFE?", help="是否為Special Focus Error", width="small"),
    "is_invalid": st.column_config.CheckboxColumn("標記無效?", help="此題是否被標記為無效 (手動優先)", width="small"),
    "overtime": None, # Internal column for styling
    "is_manually_invalid": None, # Hide the intermediate manual flag
}

def display_subject_results(subject, tab_container, report_md, df_subject, col_config, excel_map):
    """Displays the diagnosis report, styled DataFrame, and download button for a subject."""
    tab_container.subheader(f"{subject} 科診斷報告")
    # This line renders the markdown report with wrapping
    tab_container.markdown(report_md if report_md else f"未找到 {subject} 科的診斷報告。", unsafe_allow_html=True) # Added unsafe_allow_html=True just in case AI uses basic HTML

    tab_container.subheader(f"{subject} 科詳細數據 (含診斷標籤)")

    if df_subject is None or df_subject.empty:
        tab_container.write(f"沒有找到 {subject} 科的詳細數據可供顯示。")
        return

    # 複製配置以進行科目特定調整
    subject_col_config = col_config.copy()
    subject_excel_map = excel_map.copy()
    
    # 針對DI科目移除「考察能力」欄位
    if subject == 'DI':
        if 'question_fundamental_skill' in subject_col_config:
            del subject_col_config['question_fundamental_skill']
        if 'question_fundamental_skill' in subject_excel_map:
            del subject_excel_map['question_fundamental_skill']

    # Prepare DataFrame for Display
    # 1. Select columns based on keys in col_config that exist in the data
    cols_available = [k for k in subject_col_config.keys() if k in df_subject.columns]
    df_to_display = df_subject[cols_available].copy()

    # 2. Define column order for st.dataframe (exclude those with None config value, like 'overtime')
    columns_for_st_display_order = [k for k in cols_available if subject_col_config.get(k) is not None]

    # 3. Display styled DataFrame
    try:
        # Ensure necessary columns for styling exist with defaults
        if 'overtime' not in df_to_display.columns: df_to_display['overtime'] = False
        if 'is_correct' not in df_to_display.columns: df_to_display['is_correct'] = True # Assume correct if missing for styling

        styled_df = df_to_display.style.set_properties(**{'text-align': 'left'}) \
                                       .set_table_styles([dict(selector='th', props=[('text-align', 'left')])]) \
                                       .apply(apply_styles, axis=1)

        tab_container.dataframe(
            styled_df,
            column_config=subject_col_config,
            column_order=columns_for_st_display_order,
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        tab_container.error(f"無法應用樣式或顯示 {subject} 科數據: {e}")
        # Fallback: Display without styling, only showing configured columns
        try:
             tab_container.dataframe(
                 df_to_display[columns_for_st_display_order], # Use only displayable columns
                 column_config=subject_col_config,
                 hide_index=True,
                 use_container_width=True
             )
        except Exception as fallback_e:
             tab_container.error(f"顯示回退數據時也發生錯誤: {fallback_e}")


    # 4. Download Button
    try:
        # Prepare a copy specifically for Excel export using excel_map
        df_for_excel = df_subject[[k for k in subject_excel_map.keys() if k in df_subject.columns]].copy()

        # Apply number formatting *before* calling to_excel if needed
        if 'question_difficulty' in df_for_excel.columns:
             df_for_excel['question_difficulty'] = pd.to_numeric(df_for_excel['question_difficulty'], errors='coerce')
        if 'question_time' in df_for_excel.columns:
             df_for_excel['question_time'] = pd.to_numeric(df_for_excel['question_time'], errors='coerce')
        # Convert bools to string representation if desired for Excel output clarity
        if 'is_correct' in df_for_excel.columns:
             df_for_excel['is_correct'] = df_for_excel['is_correct'].astype(str) # Convert TRUE/FALSE to text
        if 'is_sfe' in df_for_excel.columns:
             df_for_excel['is_sfe'] = df_for_excel['is_sfe'].astype(str)

        # Ensure 'is_invalid' is also string for conditional formatting in to_excel
        if 'is_invalid' in df_for_excel.columns:
             df_for_excel['is_invalid'] = df_for_excel['is_invalid'].astype(str) # Convert TRUE/FALSE to text


        excel_bytes = to_excel(df_for_excel, subject_excel_map) # 使用科目特定的excel_map

        tab_container.download_button(
            label=f"下載 {subject} 科詳細數據 (Excel)",
            data=excel_bytes,
            file_name=f"gmat_diag_{subject}_detailed_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_excel_{subject}"
        )
    except Exception as e:
        tab_container.error(f"無法生成 {subject} 科的 Excel 下載文件: {e}") 

# --- Display Results Function (Moved from app.py) ---
def display_results():
    """Display analysis results in tabs"""
    st.header("📊 診斷結果")

    if st.session_state.analysis_error:
        st.error(st.session_state.error_message or "分析過程中發生錯誤，請檢查。")
    elif not st.session_state.diagnosis_complete:
        st.info("分析正在進行中或尚未完成。請稍候或檢查是否有錯誤提示。")
    elif st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("診斷完成，但沒有可顯示的數據。")
        if st.session_state.report_dict:
            st.subheader("診斷摘要")
            for subject, report_md in st.session_state.report_dict.items():
                st.markdown(f"### {subject} 科:")
                st.markdown(report_md, unsafe_allow_html=True)
    else:
        st.success("診斷分析已完成！")
        subjects_with_data = [subj for subj in SUBJECTS if subj in st.session_state.processed_df['Subject'].unique()]
        if not subjects_with_data:
            st.warning("處理後的數據中未找到任何有效科目。")
        else:
            tab_titles = [f"{subj} 科結果" for subj in subjects_with_data]
            show_ai_consolidated_tab = (
                st.session_state.openai_api_key and
                st.session_state.diagnosis_complete and
                st.session_state.ai_consolidated_report
            )
            if show_ai_consolidated_tab:
                tab_titles.append("✨ AI 匯總建議")

            result_tabs = st.tabs(tab_titles)

            for i, subject in enumerate(subjects_with_data):
                subject_tab = result_tabs[i]
                with subject_tab:
                    df_subject = st.session_state.processed_df[st.session_state.processed_df['Subject'] == subject]
                    report_md = st.session_state.report_dict.get(subject, f"*未找到 {subject} 科的報告。*")

                    st.subheader(f"{subject} 科能力估計 (Theta) 走勢")
                    theta_plot = st.session_state.theta_plots.get(subject)
                    if theta_plot:
                        st.plotly_chart(theta_plot, use_container_width=True)
                    else:
                        st.info(f"{subject} 科目的 Theta 估計圖表不可用。")
                    st.divider()
                    
                    # Use the global COLUMN_DISPLAY_CONFIG and EXCEL_COLUMN_MAP from this module
                    display_subject_results(subject, subject_tab, report_md, df_subject, COLUMN_DISPLAY_CONFIG, EXCEL_COLUMN_MAP)

            if show_ai_consolidated_tab:
                ai_tab_index = len(subjects_with_data)
                ai_consolidated_tab = result_tabs[ai_tab_index]
                with ai_consolidated_tab:
                    st.subheader("AI 匯總練習建議與後續行動")
                    st.markdown(st.session_state.ai_consolidated_report)
                    st.caption("此內容由 OpenAI (o4-mini) 模型根據各科報告中的相關部分生成。請務必結合原始報告進行核對。") 