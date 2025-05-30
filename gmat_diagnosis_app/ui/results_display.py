"""
結果顯示模組
顯示診斷結果的功能
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
         logging.error(f"記錄 Session State RC 標籤時發生錯誤: {log_e_session}")
    
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
            try:
                with pd.option_context('future.no_silent_downcasting', True):
                    df_display['is_invalid'] = df_display['is_invalid'].replace({pd.NA: False, None: False})
                    df_display['is_invalid'] = df_display['is_invalid'].infer_objects(copy=False)
                df_display['is_invalid'] = df_display['is_invalid'].astype(bool)
            except Exception as e:
                tab_container.error(f"轉換無效項時出錯: {e}")
        
        # 重要修改：確保is_invalid完全以手動標記為準
        if 'is_manually_invalid' in df_display.columns:
            if 'is_invalid' in df_display.columns:
                df_display['is_invalid'] = False
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
            if 'diagnostic_params_list' in df_to_display.columns and 'question_type' in df_to_display.columns:
                rc_data_to_log = df_to_display[df_to_display['question_type'] == 'Reading Comprehension'][['question_position', 'diagnostic_params_list']]
                if not rc_data_to_log.empty:
                    pass
                else:
                    pass
            else:
                 pass
        except Exception as log_e:
             logging.error(f"記錄 RC 標籤時發生錯誤: {log_e}")
        
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
        from gmat_diagnosis_app.utils.styling import create_report_container
        create_report_container(report_md)
    else:
        tab_container.info(f"未找到 {subject} 科的診斷報告。")

    # 4. Download Button (一樣為所有科目顯示下載按鈕)
    try:
        # Prepare a copy specifically for Excel export using excel_map
        df_for_excel = df_subject.copy() # 先完整複製一份 df_subject

        # 重要：確保 df_for_excel 中的 is_invalid 也以 is_manually_invalid 為準
        if 'is_manually_invalid' in df_for_excel.columns:
            if 'is_invalid' in df_for_excel.columns:
                df_for_excel['is_invalid'] = False
                df_for_excel.loc[df_for_excel['is_manually_invalid'] == True, 'is_invalid'] = True
            else:
                df_for_excel['is_invalid'] = df_for_excel['is_manually_invalid']
        
        # 確保 is_invalid 列是布爾型，以便後續處理
        if 'is_invalid' in df_for_excel.columns:
            df_for_excel['is_invalid'] = df_for_excel['is_invalid'].astype(bool)
            
        # 根據 excel_map 篩選列（在 is_invalid 更新之後）
        df_for_excel = df_for_excel[[k for k in excel_map.keys() if k in df_for_excel.columns]].copy()
        
        # 確保按題號排序
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
            f"下載 {subject} 科詳細數據 (Excel)",
            data=excel_bytes,
            file_name=f"{today_str}_GMAT_{subject}_detailed_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        tab_container.error(f"準備Excel下載時出錯: {e}")
        logging.error(f"詳細錯誤: {traceback.format_exc()}")
        tab_container.info(f"如有需要，請聯繫管理員並提供以上錯誤信息。")

def display_total_results(tab_container):
    """顯示Total分數的百分位數和圖表分析"""
    total_data_df = st.session_state.get('total_data')
    if total_data_df is None or not isinstance(total_data_df, pd.DataFrame) or total_data_df.empty:
        tab_container.info("尚未設定總分數據。請在「數據輸入與分析」標籤中的「Total」頁籤設定分數。")
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
    
    tab_container.subheader("三科分數與百分位對應圖")
    
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
                    name=f"{name} 切線",
                    showlegend=False
                )
            )
        
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
    
    fig_combined.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    fig_combined.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgrey')
    
    tab_container.plotly_chart(fig_combined, use_container_width=True)
    
    tab_container.subheader("了解級分跟百分位之間的關係")
    tab_container.markdown("""
    <iframe width="560" height="315" src="https://www.youtube.com/embed/MLVT-zxaBkE?si=9SJ68LSrvvii35p-" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    """, unsafe_allow_html=True)

# --- Function to generate new diagnostic report based on edited tags ---
def generate_new_diagnostic_report(df: pd.DataFrame) -> str:
    """
    Generates a new diagnostic report by classifying questions based on their
    edited diagnostic tags and predefined criteria for Q, V, and DI subjects.

    Args:
        df: DataFrame containing the diagnostic data, including a 'Subject' column,
            'question_position', 'question_type', 'question_fundamental_skill',
            'content_domain', and 'diagnostic_params_list'.

    Returns:
        A markdown string representing the new diagnostic report.
    """
    report_parts = ["### 新診斷報告 (根據已修剪標籤與標準分類)"]

    if df is None or df.empty:
        report_parts.append("* 沒有可供分析的數據。")
        return "\n".join(report_parts)

    V_SKILL_CATEGORIES_TAGS = {
        "Analysis/Critique": {
            "CR 推理障礙": ["抽象邏輯/術語理解困難", "核心議題識別困難", "邏輯思考耗時過長", "邏輯鏈分析錯誤（前提/結論/關係）", "預判方向錯誤或缺失"],
            "CR 方法應用": ["特定題型方法錯誤/不熟（需註明題型）"],
            "CR 選項辨析": ["強干擾選項混淆", "選項本身理解困難", "選項相關性判斷錯誤", "選項篩選耗時過長"],
            "CR 閱讀理解": ["閱讀耗時過長", "題幹理解障礙（關鍵詞/句式/邏輯/領域）"],
            "CR 題目理解": ["提問要求把握錯誤"],
            "其他": ["數據無效：用時過短（受時間壓力影響）"]
        },
        "Identify Inferred Idea": {
            "RC 定位能力": ["定位效率低下（反覆定位）", "定位錯誤/效率低下"],
            "RC 推理障礙": ["推理能力不足（預判/細節/語氣）", "深度思考耗時過長"],
            "RC 選項辨析": ["選項理解/辨析困難（含義/對應）", "選項篩選耗時過長"],
            "RC 閱讀方法": ["閱讀方法效率低（過度精讀）"],
            "RC 閱讀理解": ["忽略關鍵詞/邏輯", "特定領域背景知識缺乏", "篇章結構把握不清", "詞彙量瓶頸", "長難句解析困難", "閱讀速度慢（基礎問題）", "關鍵信息定位/理解錯誤", "閱讀精度不足（精讀/定位問題）"],
            "RC 題目理解": ["提問焦點把握錯誤"],
            "RC 方法應用": ["特定題型（需回憶或二級證據釐清）"],
            "基礎掌握": ["應用不穩定（Special Focus Error）"],
            "效率問題": ["信息定位環節導致效率低下", "推理分析環節導致效率低下", "選項辨析環節導致效率低下", "閱讀理解環節導致效率低下"],
            "行為模式": [t('carelessness_issue_high_fast_wrong_ratio')]
        },
        "Identify Stated Idea": {
            "效率問題": ["信息定位環節導致效率低下", "推理分析環節導致效率低下", "選項辨析環節導致效率低下", "閱讀理解環節導致效率低下"],
            "其他": ["數據無效：用時過短（受時間壓力影響）"]
        },
        "Plan/Construct": {
            "CR 推理障礙": ["抽象邏輯/術語理解困難", "核心議題識別困難", "邏輯思考耗時過長", "邏輯鏈分析錯誤（前提/結論/關係）", "預判方向錯誤或缺失"],
            "CR 方法應用": ["未遵循標準流程", "特定題型方法錯誤/不熟（需註明題型）"],
            "CR 選項辨析": ["強干擾選項混淆", "選項本身理解困難", "選項相關性判斷錯誤", "選項篩選耗時過長"],
            "CR 閱讀理解": ["基礎理解疏漏", "閱讀耗時過長", "題幹理解障礙（關鍵詞/句式/邏輯/領域）"],
            "CR 題目理解": ["提問要求把握錯誤"],
            "基礎掌握": ["應用不穩定（Special Focus Error）"],
            "效率問題": ["推理分析環節導致效率低下", "選項辨析環節導致效率低下", "閱讀理解環節導致效率低下"],
            "行為模式": [t('carelessness_issue_high_fast_wrong_ratio')]
        }
    }

    required_cols_q = ["Subject", "question_position", "question_type", "question_fundamental_skill", "diagnostic_params_list"]
    required_cols_v = ["Subject", "question_position", "question_fundamental_skill", "diagnostic_params_list"]
    required_cols_di = ["Subject", "question_position", "content_domain", "question_type", "diagnostic_params_list"]

    for subject in ["Q", "V", "DI"]:
        subject_df = df[df["Subject"] == subject].copy()
        if subject_df.empty:
            continue

        report_parts.append(f"#### {subject} 科目分類結果：")
        missing_columns = []

        if subject == "Q":
            missing_columns = [col for col in required_cols_q if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**Q科目缺少必要欄位進行分類:** {', '.join(missing_columns)}")
                continue
            grouped = subject_df.groupby(["question_type", "question_fundamental_skill"], dropna=False)
            if not any(grouped):
                report_parts.append("**Q科目:** 沒有可依據 '題型' 和 '技能' 分類的題目。")
            for (q_type, f_skill), group_data in grouped:
                q_type_str = str(q_type) if pd.notna(q_type) else "未知題型"
                f_skill_str = str(f_skill) if pd.notna(f_skill) else "未知技能"
                report_parts.append(f"\n##### Q 科目分類")
                report_parts.append(f"**題型:** {q_type_str} | **技能:** {f_skill_str}")
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
                    report_parts.append("| 類別 | 診斷標籤 |")
                    report_parts.append("|------|----------|")
                    tags_display_str = "<br>".join(unique_tags)
                    report_parts.append(f"| 診斷發現 | {tags_display_str} |")
                else:
                    report_parts.append("**診斷結果:** 無特定共同標籤")
                report_parts.append("")
        
        elif subject == "V":
            missing_columns = [col for col in required_cols_v if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**V科目缺少必要欄位進行分類:** {', '.join(missing_columns)}")
                continue
            grouped = subject_df.groupby(["question_fundamental_skill"], dropna=False)
            if not any(grouped):
                report_parts.append("**V科目:** 沒有可依據 '技能' 分類的題目。")
            for f_skill, group_data in grouped:
                f_skill_str = str(f_skill) if pd.notna(f_skill) else "未知技能"
                report_parts.append(f"\n##### V 科目技能分類")
                report_parts.append(f"**技能領域:** {f_skill_str}")
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
                            for t in tags_for_question.split(','):
                                if t and t.strip():
                                    student_unique_tags_for_skill.add(t.strip())
                
                if f_skill_str in V_SKILL_CATEGORIES_TAGS:
                    report_parts.append("| 類別 | 診斷發現 |")
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
                         report_parts.append(f"| 無對應分類 | 此技能下未發現可匹配預定義分類的標籤 |")
                else:
                    sorted_unique_student_tags = sorted(list(student_unique_tags_for_skill))
                    if sorted_unique_student_tags:
                        report_parts.append("| 類別 | 診斷標籤 |")
                        report_parts.append("|------|----------|")
                        tags_display_str = "<br>".join(sorted_unique_student_tags)
                        report_parts.append(f"| 診斷發現 | {tags_display_str} |")
                    else:
                        report_parts.append("**診斷結果:** 無特定共同標籤")
                report_parts.append("")

        elif subject == "DI":
            missing_columns = [col for col in required_cols_di if col not in subject_df.columns]
            if missing_columns:
                report_parts.append(f"**DI科目缺少必要欄位進行分類:** {', '.join(missing_columns)}")
                continue
            grouped = subject_df.groupby(["content_domain", "question_type"], dropna=False)
            if not any(grouped):
                report_parts.append("**DI科目:** 沒有可依據 '內容領域' 和 '題型' 分類的題目。")
            for (c_domain, q_type), group_data in grouped:
                c_domain_str = str(c_domain) if pd.notna(c_domain) else "未知內容領域"
                q_type_str = str(q_type) if pd.notna(q_type) else "未知題型"
                report_parts.append(f"\n##### DI 科目分類")
                report_parts.append(f"**內容領域:** {c_domain_str} | **題型:** {q_type_str}")
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
                    report_parts.append("| 類別 | 診斷標籤 |")
                    report_parts.append("|------|----------|")
                    tags_display_str = "<br>".join(unique_tags)
                    report_parts.append(f"| 診斷發現 | {tags_display_str} |")
                else:
                    report_parts.append("**診斷結果:** 無特定共同標籤")
                report_parts.append("")

    return "\n".join(report_parts)

# --- Display Results Function (Moved from app.py) ---
def display_results():
    """Displays all diagnostic results in separate tabs."""
    if not st.session_state.get("diagnosis_complete", False) and not st.session_state.get("original_processed_df") :
        st.info("尚未執行分析或分析未成功完成。請先上傳數據並執行分析。")
        return

    tab_titles = ["Total (總分與百分位)"]
    if st.session_state.get("consolidated_report_text"):
        tab_titles.append("✨ AI 總結建議")
    
    tab_titles.extend([f"{subject} 科結果" for subject in SUBJECTS])
    tab_titles.append("編輯診斷標籤 & 更新AI建議")
    tab_titles.append("AI 即時問答")

    tabs = st.tabs(tab_titles)
    
    current_tab_index = 0

    with tabs[current_tab_index]:
        display_total_results(tabs[current_tab_index])
    current_tab_index += 1
    
    if "✨ AI 總結建議" in tab_titles:
        with tabs[current_tab_index]:
            tabs[current_tab_index].subheader("AI 智能匯總與建議行動")
            report_text_to_display = st.session_state.get("consolidated_report_text", "AI總結報告生成中或不可用。")
            from gmat_diagnosis_app.utils.styling import create_report_container
            create_report_container(report_text_to_display)
        current_tab_index += 1

    for subject in SUBJECTS: 
        report_md = st.session_state.report_dict.get(subject, f"未找到 {subject} 科的診斷報告。")
        df_for_subject_display = st.session_state.processed_df if st.session_state.processed_df is not None else st.session_state.original_processed_df
        
        df_subject = pd.DataFrame()
        if df_for_subject_display is not None and not df_for_subject_display.empty:
            df_subject = df_for_subject_display[df_for_subject_display['Subject'] == subject]
        
        subject_tab_title = f"{subject} 科結果"
        try:
            actual_tab_index_for_subject = tab_titles.index(subject_tab_title)
            with tabs[actual_tab_index_for_subject]:
                display_subject_results(subject, tabs[actual_tab_index_for_subject], report_md, df_subject, COLUMN_DISPLAY_CONFIG, EXCEL_COLUMN_MAP)
        except ValueError:
            st.error(f"無法找到分頁 '{subject_tab_title}'。Tab配置: {tab_titles}")

    edit_tab_title = "編輯診斷標籤 & 更新AI建議"
    try:
        edit_tab_index = tab_titles.index(edit_tab_title)
        with tabs[edit_tab_index]:
            tabs[edit_tab_index].subheader("編輯診斷標籤並更新AI工具/提示建議")
            
            if st.session_state.original_processed_df is None:
                tabs[edit_tab_index].info("沒有可供編輯的診斷數據。請先成功執行一次分析。")
            else:
                if "reset_editable_df_requested" in st.session_state and st.session_state.reset_editable_df_requested:
                    st.session_state.editable_diagnostic_df = st.session_state.original_processed_df.copy(deep=True)
                    st.session_state._editable_df_source = st.session_state.original_processed_df
                    tabs[edit_tab_index].success("已重設為原始標籤。")
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
                        options=["Slow & Wrong", "Slow & Correct", "Normal Time & Wrong", "Normal Time & Correct", "Fast & Wrong", "Fast & Correct", "N/A"],
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
                
                tag_trimming_expander = tabs[edit_tab_index].expander("標籤修剪助手", expanded=False)
                tag_trimming_expander.markdown("""
                此工具幫助您根據對題目的具體描述，從一長串原始診斷標籤中篩選出1-2個最相關的核心標籤。
                請在下方貼上原始標籤，並簡述您在該題遇到的困難或考場回憶。
                """, unsafe_allow_html=True)

                original_tags_input = tag_trimming_expander.text_area(
                    "原始診斷標籤 (請直接貼上，例如：標籤A, 標籤B, 標籤C)", 
                    key="trim_original_tags",
                    height=100
                )
                user_description_input = tag_trimming_expander.text_area(
                    "您對該題的描述或遇到的困難 (例如：選項比較時猶豫不決、看不懂題目問什麼、定位花了很久)", 
                    key="trim_user_description",
                    height=100
                )

                if tag_trimming_expander.button("請求 AI 修剪建議", key="trim_tags_button"):
                    if not original_tags_input.strip() or not user_description_input.strip():
                        tag_trimming_expander.warning("請同時輸入原始診斷標籤和您的描述。")
                    elif not st.session_state.get('master_key'):
                        tag_trimming_expander.error("錯誤：管理金鑰未在側邊欄設定或驗證失敗。請先設定有效的管理金鑰。")
                    else:
                        with st.spinner("AI 正在分析並修剪標籤...請稍候...⏳"):
                            master_key = st.session_state.master_key
                            try:
                                trimmed_suggestion = trim_diagnostic_tags_with_openai(
                                    original_tags_input,
                                    user_description_input,
                                    master_key
                                )
                                st.session_state.trimmed_tags_suggestion = trimmed_suggestion
                            except Exception as e:
                                st.session_state.trimmed_tags_suggestion = f"調用AI時發生錯誤：{str(e)}"
                                logging.error(f"Error calling trim_diagnostic_tags_with_openai: {e}", exc_info=True)
                
                if "trimmed_tags_suggestion" in st.session_state:
                    tag_trimming_expander.markdown("##### AI 修剪建議結果:")
                    suggestion_to_display = st.session_state.trimmed_tags_suggestion
                    if suggestion_to_display.startswith("錯誤：") or suggestion_to_display.startswith("AI 未能提供修剪建議"):
                        tag_trimming_expander.error(suggestion_to_display)
                    elif suggestion_to_display == "根據您的描述，原始標籤中未找到直接對應的項目。":
                        tag_trimming_expander.info(suggestion_to_display)
                    else:
                        tag_trimming_expander.success(f"**建議標籤：** {suggestion_to_display}")
                        tag_trimming_expander.markdown(f"""
                        您可以將上方建議的標籤複製到本頁面上方的「診斷標籤 (逗號分隔)」欄位中，
                        並點擊「✓ 套用變更並更新質化分析輸出」來更新您的整體診斷。
                        """)
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
                    tabs[edit_tab_index].info("您有未套用的變更。點擊「✓ 套用變更並更新質化分析輸出」按鈕保存並生成報告。")

                if 'changes_saved' not in st.session_state:
                    st.session_state.changes_saved = False
                if 'has_unsaved_changes' not in st.session_state:
                    st.session_state.has_unsaved_changes = False

                col1, col2, col3 = tabs[edit_tab_index].columns(3)

                with col1:
                    if st.button("↺ 重設為原始標籤", key="reset_button_col", use_container_width=True):
                        st.session_state.reset_editable_df_requested = True
                        st.session_state.ai_prompts_need_regeneration = False
                        st.session_state.changes_saved = False
                        st.session_state.has_unsaved_changes = False
                        st.rerun()

                with col2:
                    if st.button("✓ 套用變更並更新質化分析輸出", key="apply_editable_df_col", type="primary", use_container_width=True):
                        # 如果已有未保存的變更，確保已保存到editable_diagnostic_df
                        st.session_state.has_unsaved_changes = False
                        st.session_state.ai_prompts_need_regeneration = True
                        st.session_state.changes_saved = True
                        tabs[edit_tab_index].success("變更已套用！AI建議將在下方更新。")
                        if st.session_state.get("editable_diagnostic_df") is not None:
                            new_report_content = generate_new_diagnostic_report(st.session_state.editable_diagnostic_df)
                            st.session_state.generated_new_diagnostic_report = new_report_content
                            with tabs[edit_tab_index].expander("新診斷報告 (根據已修剪標籤與標準分類)", expanded=False):
                                st.markdown(new_report_content, unsafe_allow_html=True)
                        else:
                            with tabs[edit_tab_index].expander("新診斷報告 (根據已修剪標籤與標準分類)", expanded=False):
                                st.warning("無法生成新診斷報告，因為沒有可編輯的數據。")
                
                with col3:
                    if st.button("下載修改後的試算表", key="download_edited_file_trigger_col", use_container_width=True):
                        if st.session_state.get('has_unsaved_changes', False):
                            tabs[edit_tab_index].warning("您有未套用的變更。請先點擊「✓ 套用變更並更新質化分析輸出」按鈕儲存變更，然後再下載試算表。", icon="⚠️")
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
                                    label="點擊下載Excel檔案", # This label appears AFTER the initial button click
                                    data=excel_bytes,
                                    file_name=f"{today_str}_GMAT_edited_diagnostic_data.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="actual_download_excel_button_col3_rerun", # Use a different key if needed
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"準備Excel下載時出錯: {e}")
                                logging.error(f"詳細錯誤: {traceback.format_exc()}")
                        else:
                            st.warning("請先點擊「✓ 套用變更並更新質化分析輸出」按鈕儲存變更，然後再下載試算表。", icon="⚠️")

                if st.session_state.get('ai_prompts_need_regeneration', False) and st.session_state.changes_saved:
                    with st.spinner("正在根據您的編輯生成AI建議..."):
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

                        all_prompts = f"### AI 工具與提示建議 (基於您的編輯)\n\n**Quantitative (Q) 科目:**\n{q_prompts if q_prompts else '(無特定建議)'}\n\n**Verbal (V) 科目:**\n{v_prompts if v_prompts else '(無特定建議)'}\n\n**Data Insights (DI) 科目:**\n{di_prompts if di_prompts else '(無特定建議)'}"
                        
                        st.session_state.generated_ai_prompts_for_edit_tab = all_prompts
                        st.session_state.ai_prompts_need_regeneration = False
                    
                if 'generated_ai_prompts_for_edit_tab' in st.session_state and st.session_state.changes_saved:
                    with tabs[edit_tab_index].expander("AI 工具與提示建議 (基於您的編輯)", expanded=False):
                        st.markdown(st.session_state.generated_ai_prompts_for_edit_tab)
                elif not st.session_state.changes_saved and 'generated_ai_prompts_for_edit_tab' in st.session_state:
                    with tabs[edit_tab_index].expander("AI 工具與提示建議 (顯示先前結果)", expanded=False):
                        st.info("這是基於先前套用變更時生成的建議。如需最新建議，請再次套用變更。")
                        st.markdown(st.session_state.generated_ai_prompts_for_edit_tab)

    except ValueError:
        st.error(f"無法找到分頁 '{edit_tab_title}'。Tab配置: {tab_titles}")
        

    ai_chat_tab_title = "AI 即時問答"
    try:
        ai_chat_tab_index = tab_titles.index(ai_chat_tab_title)
        with tabs[ai_chat_tab_index]:
            tabs[ai_chat_tab_index].subheader("與 AI 即時問答")
            if st.session_state.get('master_key'):
                display_chat_interface(st.session_state)
            else:
                tabs[ai_chat_tab_index].info("請在側邊欄輸入有效的管理金鑰以啟用 AI 問答功能。")
    except ValueError:
        st.error(f"無法找到分頁 '{ai_chat_tab_title}'.") 