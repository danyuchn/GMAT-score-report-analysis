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
    
    # 模仿 scale-percentile-simulation.ipynb 中的圖表 - 使用兩種圖表方式
    
    # 1. 組合圖 - 單一圖表顯示所有科目數據
    tab_container.subheader("三科分數與百分位對應圖 (組合圖)")
    
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
    
    # 2. 子圖版本 - 保留原有子圖方式但使用更準確的數據
    tab_container.subheader("分數與百分位對應圖 (子圖)")
    
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
            x=datasets['Quantitative']['scale'], 
            y=datasets['Quantitative']['percentile'], 
            mode='lines+markers',
            name='Q科級分百分位',
            line=dict(color='red', width=2),
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
            x=datasets['Verbal']['scale'], 
            y=datasets['Verbal']['percentile'], 
            mode='lines+markers',
            name='V科級分百分位',
            line=dict(color='blue', width=2),
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
            marker=dict(color='blue', size=12, symbol='star')
        ),
        row=2, col=1
    )
    
    # 圖表4: DI科級分百分位
    fig.add_trace(
        go.Scatter(
            x=datasets['Data Insights']['scale'], 
            y=datasets['Data Insights']['percentile'], 
            mode='lines+markers',
            name='DI科級分百分位',
            line=dict(color='black', width=2),
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
            marker=dict(color='black', size=12, symbol='star')
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
    fig.update_xaxes(title_text="Q科級分", range=[60, 90], row=1, col=2)
    fig.update_xaxes(title_text="V科級分", range=[60, 90], row=2, col=1)
    fig.update_xaxes(title_text="DI科級分", range=[60, 90], row=2, col=2)
    
    # 更新Y軸範圍
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=1, col=1)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=1, col=2)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="百分位(%)", range=[0, 100], row=2, col=2)
    
    # 保存圖表到session state
    st.session_state.total_plot = fig
    
    # 顯示圖表
    tab_container.plotly_chart(fig, use_container_width=True)
    
    # 更新總分計算公式
    new_estimated_score = -1005.3296 + 6.7098 * q_score + 6.6404 * v_score + 6.7954 * di_score
    
    # 添加總分計算公式說明
    tab_container.info(f"根據公式計算的預估總分: {new_estimated_score:.2f}，實際總分: {total_score}")
    
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