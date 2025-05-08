"""
結果顯示模組
顯示診斷結果的功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from gmat_diagnosis_app.utils.styling import apply_styles
from gmat_diagnosis_app.utils.excel_utils import to_excel
from gmat_diagnosis_app.constants.config import SUBJECTS, EXCEL_COLUMN_MAP
from gmat_diagnosis_app.ui.chat_interface import display_chat_interface
from gmat_diagnosis_app.diagnostics.q_modules.reporting import generate_q_summary_report # Placeholder for actual Q AI prompt function
from gmat_diagnosis_app.diagnostics.di_modules.report_generation import _generate_di_summary_report # Placeholder
from gmat_diagnosis_app.diagnostics.v_modules.reporting import generate_v_summary_report # Placeholder
import logging

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
    
    # 準備數據表格 (對所有科目通用)
    styled_df = None
    df_to_display = None
    columns_for_st_display_order = []
    
    if df_subject is not None and not df_subject.empty:
        # 準備表格顯示前的數據處理
        subject_col_config = col_config.copy()
        subject_excel_map = excel_map.copy()
        
        # 複製數據框以避免修改原始數據
        df_display = df_subject.copy()
        
        # 確保按題號排序
        if 'question_position' in df_display.columns:
            df_display = df_display.sort_values(by='question_position').reset_index(drop=True)
        
        # 科目特殊處理
        if subject == 'DI':
            # 針對DI科目移除「考察能力」欄位
            if 'question_fundamental_skill' in subject_col_config:
                del subject_col_config['question_fundamental_skill']
            if 'question_fundamental_skill' in subject_excel_map:
                del subject_excel_map['question_fundamental_skill']
        
        # 檢查無效項數據的類型和值
        if 'is_invalid' in df_display.columns:
            invalid_type = df_display['is_invalid'].dtype
            logging.debug(f"{subject}科無效項數據類型: {invalid_type}")
            
            # 確保無效項是布爾值
            try:
                df_display['is_invalid'] = df_display['is_invalid'].fillna(False).astype(bool)
            except Exception as e:
                tab_container.error(f"轉換無效項時出錯: {e}")
        
        # 重要修改：確保is_invalid完全以手動標記為準
        if 'is_manually_invalid' in df_display.columns:
            if 'is_invalid' in df_display.columns:
                # 先全部設為False
                df_display['is_invalid'] = False
                # 只將手動標記的項設為True
                df_display.loc[df_display['is_manually_invalid'] == True, 'is_invalid'] = True

        # 準備數據框顯示
        cols_available = [k for k in subject_col_config.keys() if k in df_display.columns]
        df_to_display = df_display[cols_available].copy()
        columns_for_st_display_order = [k for k in cols_available if subject_col_config.get(k) is not None]

        # 確保必要的列存在
        if 'overtime' not in df_to_display.columns: df_to_display['overtime'] = False
        if 'is_correct' not in df_to_display.columns: df_to_display['is_correct'] = True
        if 'is_invalid' not in df_to_display.columns: df_to_display['is_invalid'] = False
        
        # 再次確保is_invalid以手動標記為準
        if 'is_manually_invalid' in df_to_display.columns:
            df_to_display['is_invalid'] = False
            df_to_display.loc[df_to_display['is_manually_invalid'] == True, 'is_invalid'] = True
            
        # 確保is_invalid為布林值
        df_to_display['is_invalid'] = df_to_display['is_invalid'].astype(bool)
        
        try:
            styled_df = df_to_display.style.set_properties(**{'text-align': 'left'}) \
                                   .set_table_styles([dict(selector='th', props=[('text-align', 'left')])]) \
                                   .apply(apply_styles, axis=1)
        except Exception as e:
            logging.error(f"應用樣式時出錯: {e}")
            styled_df = None
    
    # 1. 首先顯示數據表格 (所有科目)
    tab_container.subheader(f"{subject} 科詳細數據 (含診斷標籤)")
    if styled_df is not None:
        try:
            tab_container.dataframe(
                styled_df,
                column_config=subject_col_config,
                column_order=columns_for_st_display_order,
                hide_index=True,
                use_container_width=True
            )
        except Exception as e:
            tab_container.error(f"顯示表格時出錯: {e}")
            tab_container.info("無法顯示數據表格：數據處理過程中出錯。")
    else:
        tab_container.info("無法顯示數據表格：數據為空或處理過程中出錯。")
    
    # 2. 顯示theta折線圖（如果存在）
    if 'theta_plots' in st.session_state and subject in st.session_state.theta_plots:
        tab_container.subheader(f"{subject} 科能力值 (Theta) 變化圖")
        tab_container.plotly_chart(st.session_state.theta_plots[subject], use_container_width=True)
    
    # 3. 最後顯示診斷報告
    if report_md:
        tab_container.subheader(f"{subject} 科診斷報告詳情")
        tab_container.markdown(report_md, unsafe_allow_html=True)
    else:
        tab_container.info(f"未找到 {subject} 科的診斷報告。")

    # 4. Download Button (一樣為所有科目顯示下載按鈕)
    try:
        # Prepare a copy specifically for Excel export using excel_map
        df_for_excel = df_subject[[k for k in subject_excel_map.keys() if k in df_subject.columns]].copy()
        
        # 確保按題號排序
        if 'question_position' in df_for_excel.columns:
            df_for_excel = df_for_excel.sort_values(by='question_position').reset_index(drop=True)

        # 所有科目的Excel處理邏輯統一（不再區分V/DI/Q）
        logging.debug(f"{subject}科Excel導出數據列: {list(df_for_excel.columns)}")
        
        # 確保is_invalid列一定存在，如果不存在則創建
        if 'is_invalid' not in df_for_excel.columns:
            df_for_excel['is_invalid'] = False
            logging.info(f"{subject}科原本沒有is_invalid列，已創建")
            
        # 記錄原始無效項數量
        orig_invalid_sum = df_for_excel['is_invalid'].sum()
        logging.debug(f"{subject}科Excel導出前無效項數量: {orig_invalid_sum}")
        
        # 重要：確保is_invalid完全以手動標記為準（Excel導出前）
        if 'is_manually_invalid' in df_for_excel.columns:
            # 重置is_invalid列
            df_for_excel['is_invalid'] = False
            # 僅將手動標記的項設為無效
            df_for_excel.loc[df_for_excel['is_manually_invalid'] == True, 'is_invalid'] = True
            
            logging.debug(f"{subject}科僅使用手動標記後，Excel導出無效項數量: {df_for_excel['is_invalid'].sum()}")
            
            # 驗證手動標記項被正確設置 (僅記錄到日誌)
            manual_invalid_count = df_for_excel['is_manually_invalid'].sum()
            invalid_count = df_for_excel['is_invalid'].sum()
            if manual_invalid_count != invalid_count:
                logging.error(f"錯誤：{subject}科Excel導出前，無效項數量 ({invalid_count}) 與手動標記數量 ({manual_invalid_count}) 不一致！")
        
        # Apply number formatting *before* calling to_excel if needed
        if 'question_difficulty' in df_for_excel.columns:
            df_for_excel['question_difficulty'] = pd.to_numeric(df_for_excel['question_difficulty'], errors='coerce')
        if 'question_time' in df_for_excel.columns:
            df_for_excel['question_time'] = pd.to_numeric(df_for_excel['question_time'], errors='coerce')
            
        # Convert boolean columns to strings for Excel export
        if 'is_correct' in df_for_excel.columns:
            df_for_excel['is_correct'] = df_for_excel['is_correct'].astype(str) # Convert TRUE/FALSE to text
        if 'is_sfe' in df_for_excel.columns:
            df_for_excel['is_sfe'] = df_for_excel['is_sfe'].astype(str)
            
        # Handle is_invalid specifically since we *just* processed it
        if 'is_invalid' in df_for_excel.columns:
            df_for_excel['is_invalid'] = df_for_excel['is_invalid'].astype(str) # Convert TRUE/FALSE to text
            
        # Final validation just to be sure we're exporting valid data
        # Ensures consistent, expectable log output for is_invalid
        try:
            value_counts = df_for_excel['is_invalid'].value_counts().to_dict()
            logging.debug(f"{subject}科Excel導出直前，is_invalid值分佈: {value_counts}")
        except Exception as e:
            logging.warning(f"計算{subject}科is_invalid分佈時出錯: {e}")
            
        # Calculate & display final invalid count in log
        invalid_count = (df_for_excel['is_invalid'] == 'True').sum() if 'is_invalid' in df_for_excel.columns else 0
        logging.info(f"{subject}科Excel導出包含 {invalid_count} 個無效題目")
        
        # Generate Excel and offer for download - Use function from excel_utils
        excel_bytes = to_excel(df_for_excel, subject_excel_map) # 使用科目特定的excel_map
        
        # Offer download button for Excel file - provide bytes to streamlit
        today_str = pd.Timestamp.now().strftime('%Y%m%d')
        tab_container.download_button(
            f"下載 {subject} 科詳細數據 (Excel)",
            data=excel_bytes,
            file_name=f"{today_str}_GMAT_{subject}_detailed_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        tab_container.error(f"準備Excel下載時出錯: {e}")
        import traceback
        logging.error(f"詳細錯誤: {traceback.format_exc()}")
        tab_container.info(f"如有需要，請聯繫管理員並提供以上錯誤信息。")

def display_total_results(tab_container):
    """顯示Total分數的百分位數和圖表分析"""
    total_data_df = st.session_state.get('total_data')
    # Correctly check if the DataFrame is None, not a DataFrame, or empty
    if total_data_df is None or not isinstance(total_data_df, pd.DataFrame) or total_data_df.empty:
        tab_container.info("尚未設定總分數據。請在「數據輸入與分析」標籤中的「Total」頁籤設定分數。")
        return
    
    # 獲取分數數據
    total_score = st.session_state.total_score
    q_score = st.session_state.q_score
    v_score = st.session_state.v_score
    di_score = st.session_state.di_score
    
    # 使用 scale-percentile-simulation.ipynb 中更準確的數據集
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
    
    # 函數：根據級分找對應百分位
    def find_percentile(scale_score, dataset):
        scale = dataset['scale'][::-1]  # 反轉為升序
        percentile = dataset['percentile'][::-1]
    
        if scale_score < scale[0]:
            return percentile[0]
        elif scale_score > scale[-1]:
            return percentile[-1]
        else:
            return np.interp(scale_score, scale, percentile)
    
    # 計算百分位數
    q_percentile = find_percentile(q_score, datasets['Quantitative'])
    v_percentile = find_percentile(v_score, datasets['Verbal'])
    di_percentile = find_percentile(di_score, datasets['Data Insights'])
    
    # 總分百分位數近似對應關係 (保留原有總分映射)
    total_scores = np.array([800, 770, 740, 710, 680, 650, 620, 590, 560, 530, 500, 450, 400, 350, 300, 250, 200])
    total_percentiles = np.array([99.9, 99, 97, 92, 85, 75, 65, 51, 38, 28, 18, 8, 4, 2, 1, 0.5, 0.1])
    
    # 插值計算總分百分位數
    total_percentile = np.interp(total_score, total_scores[::-1], total_percentiles[::-1])
    
    # 組合圖 - 單一圖表顯示所有科目數據
    tab_container.subheader("三科分數與百分位對應圖")
    
    candidate_scores = {
        'Quantitative': q_score,
        'Verbal': v_score,
        'Data Insights': di_score
    }
    
    # 創建Plotly圖表
    fig_combined = go.Figure()
    
    # 不同科目的顏色映射
    colors = {
        'Quantitative': 'red',
        'Verbal': 'blue',
        'Data Insights': 'black'
    }
    
    # 繪製所有科目的百分位曲線
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
        
        # 添加當前分數點
        score = candidate_scores[name]
        percentile = find_percentile(score, dataset)
        
        # 在 plotly 中生成切線
        # 首先準備數據用於插值
        sorted_scale = dataset['scale'][::-1]  # 反轉為升序
        sorted_percentile = dataset['percentile'][::-1]
        
        # 使用 scipy.interpolate.interp1d 代替 UnivariateSpline，因為我們只需要簡單的插值
        from scipy.interpolate import interp1d
        
        # 計算切線所需的點
        # 為了計算斜率，我們取點左右的數據點
        idx = np.searchsorted(sorted_scale, score)
        if idx > 0 and idx < len(sorted_scale):
            # 計算相鄰點的斜率來近似切線斜率
            x_left = sorted_scale[idx-1]
            y_left = sorted_percentile[idx-1]
            x_right = sorted_scale[idx+1] if idx+1 < len(sorted_scale) else sorted_scale[idx]
            y_right = sorted_percentile[idx+1] if idx+1 < len(sorted_percentile) else sorted_percentile[idx]
            
            # 計算斜率
            slope = (y_right - y_left) / (x_right - x_left)
            
            # 定義切線範圍 (score ± 5)
            tangent_range = 5
            x_min = max(score - tangent_range, sorted_scale[0])
            x_max = min(score + tangent_range, sorted_scale[-1])
            x_tangent = np.linspace(x_min, x_max, 50)
            
            # 計算切線上的點
            y_tangent = percentile + slope * (x_tangent - score)
            
            # 繪製切線
            fig_combined.add_trace(
                go.Scatter(
                    x=x_tangent,
                    y=y_tangent,
                    mode='lines',
                    line=dict(color=colors[name], dash='dash', width=2),
                    name=f"{name} 切線",
                    showlegend=False
                )
            )
        
        # 添加突出顯示的分數點
        fig_combined.add_trace(
            go.Scatter(
                x=[score],
                y=[percentile],
                mode='markers',
                name=f"{name} 分數",
                marker=dict(
                    color=colors[name],
                    size=15,
                    symbol='x',
                    line=dict(color='white', width=2)
                )
            )
        )
    
    # 更新圖表布局
    fig_combined.update_layout(
        title="GMAT分數與百分位對應關係",
        xaxis_title="級分",
        yaxis_title="百分位",
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
    
    # 添加網格線
    fig_combined.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig_combined.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    
    # 顯示組合圖
    tab_container.plotly_chart(fig_combined, use_container_width=True)
    
    # 新增加的部分：嵌入YouTube視頻
    tab_container.subheader("了解級分跟百分位之間的關係")
    tab_container.markdown("""
    <iframe width="560" height="315" src="https://www.youtube.com/embed/MLVT-zxaBkE?si=9SJ68LSrvvii35p-" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    """, unsafe_allow_html=True)

# --- Display Results Function (Moved from app.py) ---
def display_results():
    """Displays all diagnostic results in separate tabs."""
    if not st.session_state.get("diagnosis_complete", False) and not st.session_state.get("original_processed_df") :
        st.info("尚未執行分析或分析未成功完成。請先上傳數據並執行分析。")
        return

    tab_titles = ["Total (總分與百分位)"]
    if st.session_state.get("consolidated_report_text"):
        tab_titles.append("✨ AI 總結建議")
    
    # Add subject result tabs
    tab_titles.extend([f"{subject} 科結果" for subject in SUBJECTS])
    
    # Add the new Edit tab
    tab_titles.append("🔧 編輯診斷標籤 & 更新AI建議")
    
    # Add AI Chat tab last
    tab_titles.append("💬 AI 即時問答")

    tabs = st.tabs(tab_titles)
    
    current_tab_index = 0

    # Tab 1: Total Score Analysis
    with tabs[current_tab_index]:
        display_total_results(tabs[current_tab_index])
    current_tab_index += 1
    
    # Tab (Optional): AI Consolidated Report
    if "✨ AI 總結建議" in tab_titles:
        with tabs[current_tab_index]:
            tabs[current_tab_index].subheader("AI 智能匯總與建議行動")
            # Make sure to use consolidated_report_text, which is set by set_analysis_results
            report_text_to_display = st.session_state.get("consolidated_report_text", "AI總結報告生成中或不可用。")
            tabs[current_tab_index].markdown(report_text_to_display)
        current_tab_index += 1

    # Tabs for Q, V, DI
    for subject in SUBJECTS: 
        report_md = st.session_state.report_dict.get(subject, f"未找到 {subject} 科的診斷報告。")
        # Use original_processed_df if processed_df is None (e.g. after an error)
        df_for_subject_display = st.session_state.processed_df if st.session_state.processed_df is not None else st.session_state.original_processed_df
        
        df_subject = pd.DataFrame()
        if df_for_subject_display is not None and not df_for_subject_display.empty:
            df_subject = df_for_subject_display[df_for_subject_display['Subject'] == subject]
        
        subject_tab_title = f"{subject} 科結果"
        # Find the correct index for the subject tab
        try:
            actual_tab_index_for_subject = tab_titles.index(subject_tab_title)
            with tabs[actual_tab_index_for_subject]:
                display_subject_results(subject, tabs[actual_tab_index_for_subject], report_md, df_subject, COLUMN_DISPLAY_CONFIG, EXCEL_COLUMN_MAP)
        except ValueError:
            # This case should ideally not be reached if tab_titles is constructed correctly
            st.error(f"無法找到分頁 '{subject_tab_title}'。Tab配置: {tab_titles}")
            # Do not increment current_tab_index here, as it might mess up subsequent tab indexing if used linearly.
            # Instead, rely on finding index directly.

    # Tab for Editing Diagnostic Labels
    edit_tab_title = "🔧 編輯診斷標籤 & 更新AI建議"
    try:
        edit_tab_index = tab_titles.index(edit_tab_title)
        with tabs[edit_tab_index]:
            tabs[edit_tab_index].subheader("編輯診斷標籤並更新AI工具/提示建議")
            
            if st.session_state.original_processed_df is None:
                tabs[edit_tab_index].info("沒有可供編輯的診斷數據。請先成功執行一次分析。")
            else:
                # Initialize edited_df in session_state if it doesn't exist or if we need to reset
                if 'editable_diagnostic_df' not in st.session_state or st.session_state.original_processed_df is not st.session_state.get('_editable_df_source'):
                    st.session_state.editable_diagnostic_df = st.session_state.original_processed_df.copy()
                    st.session_state._editable_df_source = st.session_state.original_processed_df # Track source to detect reset needs

                # Define user-requested columns and their display order
                user_requested_internal_names = [
                    "Subject", "question_position", "is_correct", "question_time",
                    "question_type", "content_domain", "question_fundamental_skill",
                    "is_invalid", "time_performance_category", "diagnostic_params_list"
                ]
                
                # Create a DataFrame view for the editor with only these columns, in this order.
                # Make sure all these columns actually exist in the editable_diagnostic_df.
                # If a column is missing, this will raise a KeyError, which is good for debugging.
                # Alternatively, one could filter `user_requested_internal_names` to only include
                # columns that are actually present in `st.session_state.editable_diagnostic_df.columns`.
                cols_to_display = [col for col in user_requested_internal_names if col in st.session_state.editable_diagnostic_df.columns]
                df_for_editor = st.session_state.editable_diagnostic_df[cols_to_display].copy()

                # Prepare 'diagnostic_params_list' for TextColumn: convert list to comma-separated string
                if 'diagnostic_params_list' in df_for_editor.columns:
                    def format_tags_for_text_editor(tags_list):
                        if isinstance(tags_list, list):
                            # Filter out None or empty strings from list before joining
                            return ", ".join(str(tag).strip() for tag in tags_list if tag and str(tag).strip())
                        if pd.isna(tags_list) or tags_list is None:
                            return "" # Return empty string for NaN/None
                        # If it's already a string (e.g., from previous edit), just return it after stripping
                        return str(tags_list).strip()
                    df_for_editor['diagnostic_params_list'] = df_for_editor['diagnostic_params_list'].apply(format_tags_for_text_editor)

                # Define column configurations for the data_editor, tailored to the new view
                editor_column_config = {
                    "Subject": st.column_config.TextColumn("科目", disabled=True),
                    "question_position": st.column_config.NumberColumn("題號", help="題目在該科目中的順序", disabled=True),
                    "is_correct": st.column_config.CheckboxColumn("答對", help="該題是否回答正確", disabled=True),
                    "question_time": st.column_config.NumberColumn("用時", help="該題作答用時(分鐘)", format="%.2f", disabled=True),
                    "question_type": st.column_config.TextColumn("題型", disabled=True),
                    "content_domain": st.column_config.TextColumn("內容領域", disabled=True),
                    "question_fundamental_skill": st.column_config.TextColumn("考察能力", disabled=True),
                    "is_invalid": st.column_config.CheckboxColumn("標記無效", help="該題是否被標記為無效", disabled=True),
                    "time_performance_category": st.column_config.SelectboxColumn(
                        "時間表現",
                        help="點擊編輯以選擇時間表現分類",
                        options=["Slow & Wrong", "Slow & Right", "Normal & Wrong", "Normal & Right", "Fast & Wrong", "Fast & Right", "N/A"],
                        required=True
                    ),
                    "diagnostic_params_list": st.column_config.TextColumn(
                        "診斷標籤 (逗號分隔)",
                        help="請用逗號 (,) 分隔多個標籤。例如：標籤1,標籤2,標籤3",
                        width="large"
                    )
                }
                
                final_editor_column_config = {k: v for k, v in editor_column_config.items() if k in df_for_editor.columns}

                tabs[edit_tab_index].markdown("**說明:** 在下方表格中修改「診斷標籤」或「時間表現」。對於「診斷標籤」，請用逗號分隔多個標籤。完成後點擊「套用變更」按鈕。")
                
                edited_df_subset_from_editor = tabs[edit_tab_index].data_editor(
                    df_for_editor,
                    column_config=final_editor_column_config,
                    use_container_width=True,
                    num_rows="fixed", 
                    key="diagnosis_label_editor" 
                )

                if edited_df_subset_from_editor is not None:
                    updated_full_df = st.session_state.editable_diagnostic_df.copy()
                    
                    for col_name in edited_df_subset_from_editor.columns:
                        if col_name in updated_full_df.columns:
                            if col_name == 'diagnostic_params_list':
                                # Convert comma-separated string back to list of strings
                                def parse_tags_from_text_editor(tags_str):
                                    if pd.isna(tags_str) or not isinstance(tags_str, str) or not tags_str.strip():
                                        return []
                                    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                                
                                updated_full_df[col_name] = edited_df_subset_from_editor[col_name].apply(parse_tags_from_text_editor)
                            else:
                                updated_full_df[col_name] = edited_df_subset_from_editor[col_name]
                    
                    st.session_state.editable_diagnostic_df = updated_full_df
                    st.session_state.ai_prompts_need_regeneration = True

                col1, col2 = tabs[edit_tab_index].columns(2)
                if col1.button("↺ 重設為原始標籤", key="reset_editable_df"):
                    st.session_state.editable_diagnostic_df = st.session_state.original_processed_df.copy()
                    st.session_state.ai_prompts_need_regeneration = False # No need to regenerate if reset
                    if 'generated_ai_prompts_for_edit_tab' in st.session_state:
                        del st.session_state['generated_ai_prompts_for_edit_tab'] # Clear previous prompts
                    st.experimental_rerun()

                if col2.button("✓ 套用變更並更新AI建議", key="apply_editable_df", type="primary"):
                    # The editor already updated st.session_state.editable_diagnostic_df
                    # So, we just need to flag for regeneration
                    st.session_state.ai_prompts_need_regeneration = True
                    tabs[edit_tab_index].success("變更已套用！AI建議將在下方更新。")
                    # We will handle regeneration and display below
                
                # Display AI Prompts if regeneration is needed or already generated
                if st.session_state.get('ai_prompts_need_regeneration', False) or 'generated_ai_prompts_for_edit_tab' in st.session_state:
                    with st.spinner("正在根據您的編輯生成AI建議..."):
                        # --- TODO: Call new AI prompt generation functions here --- 
                        # These functions will take st.session_state.editable_diagnostic_df as input
                        # For now, using placeholders. These need to be implemented in respective diagnostic modules.
                        
                        q_prompts = ""
                        v_prompts = ""
                        di_prompts = ""

                        df_to_generate_prompts = st.session_state.editable_diagnostic_df

                        # Placeholder: Simulate calling the actual functions when they are ready
                        # Q Prompts
                        # from gmat_diagnosis_app.diagnostics.q_modules.ai_prompts import generate_q_ai_tool_recommendations 
                        # q_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'Q']
                        # if not q_df_subject.empty: q_prompts = generate_q_ai_tool_recommendations(q_df_subject)
                        
                        # V Prompts - similar structure
                        # from gmat_diagnosis_app.diagnostics.v_modules.ai_prompts import generate_v_ai_tool_recommendations
                        # v_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'V']
                        # if not v_df_subject.empty: v_prompts = generate_v_ai_tool_recommendations(v_df_subject)

                        # DI Prompts - similar structure
                        # from gmat_diagnosis_app.diagnostics.di_modules.ai_prompts import generate_di_ai_tool_recommendations
                        # di_df_subject = df_to_generate_prompts[df_to_generate_prompts['Subject'] == 'DI']
                        # if not di_df_subject.empty: di_prompts = generate_di_ai_tool_recommendations(di_df_subject)

                        # For demonstration, using mock data
                        q_prompts = "Q科AI建議 (基於編輯):\n- 工具A: ...\n- 提示B: ..."
                        v_prompts = "V科AI建議 (基於編輯):\n- 工具C: ...\n- 提示D: ..."
                        di_prompts = "DI科AI建議 (基於編輯):\n- 工具E: ...\n- 提示F: ..."

                        all_prompts = f"### AI 工具與提示建議 (基於您的編輯)\n\n**Quantitative (Q) 科目:**\n{q_prompts if q_prompts else '(無特定建議)'}\n\n**Verbal (V) 科目:**\n{v_prompts if v_prompts else '(無特定建議)'}\n\n**Data Insights (DI) 科目:**\n{di_prompts if di_prompts else '(無特定建議)'}"
                        
                        st.session_state.generated_ai_prompts_for_edit_tab = all_prompts
                        st.session_state.ai_prompts_need_regeneration = False # Reset flag after generation
                    
                if 'generated_ai_prompts_for_edit_tab' in st.session_state:
                    tabs[edit_tab_index].markdown(st.session_state.generated_ai_prompts_for_edit_tab)

    except ValueError:
        # This case should ideally not be reached if tab_titles is constructed correctly
        st.error(f"無法找到分頁 '{edit_tab_title}'。Tab配置: {tab_titles}")
        

    # Tab for AI Chat - find its index
    ai_chat_tab_title = "💬 AI 即時問答"
    try:
        ai_chat_tab_index = tab_titles.index(ai_chat_tab_title)
        with tabs[ai_chat_tab_index]:
            tabs[ai_chat_tab_index].subheader("與 AI 即時問答")
            if st.session_state.get('openai_api_key'):
                display_chat_interface(st.session_state)
            else:
                tabs[ai_chat_tab_index].info("請在側邊欄輸入 OpenAI API Key 以啟用 AI 問答功能。")
    except ValueError:
        # This should not happen if it's in tab_titles
        st.error(f"無法找到分頁 '{ai_chat_tab_title}'.") 