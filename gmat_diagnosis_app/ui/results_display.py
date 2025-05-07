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
    
    tab_container.subheader("GMAT 分數分析")
    
    # 顯示所選分數
    if st.session_state.get('score_df') is not None:
        tab_container.dataframe(st.session_state.score_df, hide_index=True, use_container_width=True)
    else:
        score_data = {
            'Score_Type': ['Total Score', 'Q Scaled Score', 'V Scaled Score', 'DI Scaled Score'],
            'Score': [total_score, q_score, v_score, di_score]
        }
        tab_container.dataframe(pd.DataFrame(score_data), hide_index=True, use_container_width=True)
    
    # 生成百分位數分析
    tab_container.subheader("分數百分位分析")
    
    # 通過插值計算百分位數
    # 總分百分位數近似對應關係 (擬合數據)
    total_scores = np.array([800, 770, 740, 710, 680, 650, 620, 590, 560, 530, 500, 450, 400, 350, 300, 250, 200])
    total_percentiles = np.array([99.9, 99, 97, 92, 85, 75, 65, 51, 38, 28, 18, 8, 4, 2, 1, 0.5, 0.1])
    
    # 各科級分百分位數近似對應關係 (擬合數據)
    scaled_scores = np.array([90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40])
    scaled_percentiles = np.array([98, 92, 83, 70, 55, 40, 28, 18, 10, 5, 2])
    
    # 插值計算百分位數
    total_percentile = np.interp(total_score, total_scores[::-1], total_percentiles[::-1])
    q_percentile = np.interp(q_score, scaled_scores[::-1], scaled_percentiles[::-1])
    v_percentile = np.interp(v_score, scaled_scores[::-1], scaled_percentiles[::-1])
    di_percentile = np.interp(di_score, scaled_scores[::-1], scaled_percentiles[::-1])
    
    # 創建百分位數DataFrame
    percentile_data = {
        'Score_Type': ['Total Score', 'Q Scaled Score', 'V Scaled Score', 'DI Scaled Score'],
        'Score': [total_score, q_score, v_score, di_score],
        'Percentile': [
            f"{total_percentile:.1f}%", 
            f"{q_percentile:.1f}%", 
            f"{v_percentile:.1f}%", 
            f"{di_percentile:.1f}%"
        ]
    }
    percentile_df = pd.DataFrame(percentile_data)
    
    # 顯示百分位數表格
    tab_container.dataframe(percentile_df, hide_index=True, use_container_width=True)
    
    # 生成圖表
    tab_container.subheader("分數與百分位對應圖")
    
    # 創建一個包含四個子圖的圖表
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "GMAT 總分百分位分布", 
            "Q科級分百分位分布", 
            "V科級分百分位分布", 
            "DI科級分百分位分布"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # 圖表1: 總分百分位
    fig.add_trace(
        go.Scatter(
            x=total_scores, 
            y=total_percentiles, 
            mode='lines+markers',
            name='總分百分位',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    # 添加當前總分位置
    fig.add_trace(
        go.Scatter(
            x=[total_score], 
            y=[total_percentile], 
            mode='markers',
            name='當前總分',
            marker=dict(color='red', size=12, symbol='star')
        ),
        row=1, col=1
    )
    
    # 圖表2: Q科級分百分位
    fig.add_trace(
        go.Scatter(
            x=scaled_scores, 
            y=scaled_percentiles, 
            mode='lines+markers',
            name='Q科級分百分位',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ),
        row=1, col=2
    )
    # 添加當前Q科級分位置
    fig.add_trace(
        go.Scatter(
            x=[q_score], 
            y=[q_percentile], 
            mode='markers',
            name='當前Q科級分',
            marker=dict(color='red', size=12, symbol='star')
        ),
        row=1, col=2
    )
    
    # 圖表3: V科級分百分位
    fig.add_trace(
        go.Scatter(
            x=scaled_scores, 
            y=scaled_percentiles, 
            mode='lines+markers',
            name='V科級分百分位',
            line=dict(color='purple', width=2),
            marker=dict(size=6)
        ),
        row=2, col=1
    )
    # 添加當前V科級分位置
    fig.add_trace(
        go.Scatter(
            x=[v_score], 
            y=[v_percentile], 
            mode='markers',
            name='當前V科級分',
            marker=dict(color='red', size=12, symbol='star')
        ),
        row=2, col=1
    )
    
    # 圖表4: DI科級分百分位
    fig.add_trace(
        go.Scatter(
            x=scaled_scores, 
            y=scaled_percentiles, 
            mode='lines+markers',
            name='DI科級分百分位',
            line=dict(color='orange', width=2),
            marker=dict(size=6)
        ),
        row=2, col=2
    )
    # 添加當前DI科級分位置
    fig.add_trace(
        go.Scatter(
            x=[di_score], 
            y=[di_percentile], 
            mode='markers',
            name='當前DI科級分',
            marker=dict(color='red', size=12, symbol='star')
        ),
        row=2, col=2
    )
    
    # 更新圖表布局
    fig.update_layout(
        height=800,
        width=800,
        title_text="GMAT分數與百分位對應關係",
        showlegend=False,
        template="plotly_white"
    )
    
    # 更新X軸範圍
    fig.update_xaxes(title_text="總分", range=[200, 800], row=1, col=1)
    fig.update_xaxes(title_text="Q科級分", range=[40, 90], row=1, col=2)
    fig.update_xaxes(title_text="V科級分", range=[40, 90], row=2, col=1)
    fig.update_xaxes(title_text="DI科級分", range=[40, 90], row=2, col=2)
    
    # 更新Y軸範圍
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=1, col=1)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=1, col=2)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=2, col=2)
    
    # 保存圖表到session state
    st.session_state.total_plot = fig
    
    # 顯示圖表
    tab_container.plotly_chart(fig, use_container_width=True)
    
    # 添加解釋和分析
    tab_container.subheader("分數解釋")
    
    # 根據總分分析
    if total_score >= 750:
        score_analysis = "您的總分處於頂尖水平（99%以上），有競爭力申請全球任何商學院。"
    elif total_score >= 700:
        score_analysis = "您的總分非常優秀（90%以上），對大多數頂尖商學院有競爭力。"
    elif total_score >= 650:
        score_analysis = "您的總分良好（大約70-80%百分位），對許多優秀商學院具有競爭力。"
    elif total_score >= 600:
        score_analysis = "您的總分處於中等偏上水平（約50-60%百分位），對部分商學院有競爭力，可考慮提高。"
    elif total_score >= 550:
        score_analysis = "您的總分處於中等水平（約30-40%百分位），建議繼續提高以增加申請競爭力。"
    else:
        score_analysis = "您的總分有提升空間（低於30%百分位），建議加強備考策略。"
    
    tab_container.markdown(f"**總分分析**：{score_analysis}")
    
    # 分析各科表現平衡性
    scores = [q_percentile, v_percentile, di_percentile]
    max_diff = max(scores) - min(scores)
    
    if max_diff > 30:
        balance_analysis = "您的各科表現差異較大，建議重點提高較弱的科目以獲得更平衡的分數。"
    elif max_diff > 15:
        balance_analysis = "您的各科表現有一定差異，可考慮適當平衡各科備考時間。"
    else:
        balance_analysis = "您的各科表現相對平衡，這是一個很好的優勢。"
    
    tab_container.markdown(f"**平衡性分析**：{balance_analysis}")
    
    # 找出最強和最弱科目
    subject_names = ["Q科", "V科", "DI科"]
    strongest = subject_names[scores.index(max(scores))]
    weakest = subject_names[scores.index(min(scores))]
    
    tab_container.markdown(f"**優勢科目**：{strongest}（{max(scores):.1f}%百分位）")
    tab_container.markdown(f"**待提高科目**：{weakest}（{min(scores):.1f}%百分位）")
    
    # 提供改進建議
    tab_container.subheader("提升策略建議")
    
    if total_score < 650:
        tab_container.markdown("""
        **提升總分策略**:
        1. 制定全面的備考計劃，涵蓋所有科目
        2. 增加每周學習時間，確保系統性學習
        3. 使用官方資源進行練習並熟悉考試
        4. 考慮參加備考課程或尋求專業輔導
        """)
    
    if min(scores) < 70:
        tab_container.markdown(f"""
        **提升{weakest}建議**:
        1. 診斷具體弱點，找出知識或技能差距
        2. 專項練習薄弱環節並尋求專門指導
        3. 增加該科目的練習頻率和時間投入
        4. 定期評估進步並調整學習策略
        """)
    
    tab_container.markdown("""
    **平衡發展建議**:
    1. 持續練習強勢科目，保持已有優勢
    2. 適當分配時間，不忽視任何一個科目
    3. 定期進行模擬測試，確認整體進步
    4. 在考前保持沉著冷靜，合理安排複習
    """)

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
            # 添加Total標籤頁
            tab_titles = [f"{subj} 科結果" for subj in subjects_with_data]
            tab_titles.append("Total")  # 添加Total標籤頁
            
            show_ai_consolidated_tab = (
                st.session_state.openai_api_key and
                st.session_state.diagnosis_complete and
                st.session_state.ai_consolidated_report
            )
            if show_ai_consolidated_tab:
                tab_titles.append("✨ AI 匯總建議")

            result_tabs = st.tabs(tab_titles)

            # 顯示各科目結果
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
            
            # 顯示Total標籤頁結果
            total_tab_index = len(subjects_with_data)
            with result_tabs[total_tab_index]:
                display_total_results(result_tabs[total_tab_index])

            # 顯示AI匯總標籤頁結果
            if show_ai_consolidated_tab:
                ai_tab_index = len(subjects_with_data) + 1  # +1是因為Total標籤頁
                ai_consolidated_tab = result_tabs[ai_tab_index]
                with ai_consolidated_tab:
                    st.subheader("AI 匯總練習建議與後續行動")
                    st.markdown(st.session_state.ai_consolidated_report)
                    st.caption("此內容由 OpenAI (o4-mini) 模型根據各科報告中的相關部分生成。請務必結合原始報告進行核對。") 