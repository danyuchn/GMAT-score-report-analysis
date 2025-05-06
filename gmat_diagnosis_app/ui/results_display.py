"""
結果顯示模組
顯示診斷結果的功能
"""

import streamlit as st
import pandas as pd
from gmat_diagnosis_app.utils.styling import apply_styles
from gmat_diagnosis_app.utils.excel_utils import to_excel

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