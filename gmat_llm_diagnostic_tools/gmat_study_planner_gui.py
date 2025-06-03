#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Study Planner GUI Application
GMAT 讀書計畫圖形化介面應用

A Streamlit-based GUI for the GMAT Study Planning System
使用 Streamlit 構建的 GMAT 學習規劃系統圖形化介面
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
from gmat_study_planner import GMATStudyPlanner
from gmat_route_tool_gui import show_route_tool
from modern_gui_styles import (
    apply_modern_css, 
    create_modern_header, 
    create_section_header, 
    create_status_card,
    create_metric_card,
    create_feature_grid,
    create_progress_bar
)

# 設定頁面配置
st.set_page_config(
    page_title="GMAT 學習規劃系統",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 應用現代化 CSS 樣式
apply_modern_css()

# 初始化 session state
if 'planner' not in st.session_state:
    st.session_state.planner = GMATStudyPlanner()
if 'study_plan_generated' not in st.session_state:
    st.session_state.study_plan_generated = False
if 'last_recommendations' not in st.session_state:
    st.session_state.last_recommendations = None

def main():
    """主要應用程序函數"""
    
    # 現代化標題和介紹
    create_modern_header(
        title="GMAT 學習規劃系統",
        subtitle="根據您的個人情況，生成個性化的 GMAT 學習計劃 | Generate personalized GMAT study plans based on your individual situation",
        icon="🎯"
    )
    
    # 側邊欄導航
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <h2 style="color: var(--primary-color); margin: 0;">📋 系統功能</h2>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "選擇功能頁面",
            ["🎯 學習計劃生成", "📊 分析工具", "🏷️ 診斷標籤路由", "ℹ️ 系統說明"],
            index=0
        )
        
        # 側邊欄功能介紹
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.9rem; color: var(--neutral-600); line-height: 1.5;">
        <strong>🔧 核心功能</strong><br>
        • 個性化學習計劃<br>
        • 科目分析工具<br>
        • 診斷標籤路由<br>
        • 智能時間分配<br>
        </div>
        """, unsafe_allow_html=True)
    
    # 根據選擇顯示相應頁面
    if page == "🎯 學習計劃生成":
        show_study_plan_generator()
    elif page == "📊 分析工具":
        show_analysis_tools()
    elif page == "🏷️ 診斷標籤路由":
        show_route_tool()
    elif page == "ℹ️ 系統說明":
        show_system_info()

def show_study_plan_generator():
    """顯示學習計劃生成器"""
    
    create_section_header("個性化學習計劃生成", "🎯")
    
    # 創建分頁收集資訊
    tabs = st.tabs(["📝 基本資訊", "⏰ 時程安排", "📚 學習狀況", "🚀 生成計劃"])
    
    # 分頁 1: 基本資訊
    with tabs[0]:
        with st.container():
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 目標設定")
                target_score = st.number_input(
                    "目標 GMAT 分數",
                    min_value=200,
                    max_value=805,
                    value=700,
                    step=10,
                    help="您希望達到的 GMAT 分數 (200-805)"
                )
                
                score_system = st.selectbox(
                    "分數制度",
                    ["New", "Old"],
                    index=0,
                    help="New: 新制 (Focus Edition), Old: 舊制 (10th Edition)"
                )
                
                current_score = st.number_input(
                    "目前最高 GMAT 分數",
                    min_value=200,
                    max_value=805,
                    value=600,
                    step=10,
                    help="您目前的最高 GMAT 分數"
                )
            
            with col2:
                st.markdown("### 📊 各科目目前積分 (60-90)")
                
                quant_score = st.slider(
                    "🧮 數學 Quantitative",
                    min_value=60,
                    max_value=90,
                    value=75,
                    help="數學科目目前積分"
                )
                
                verbal_score = st.slider(
                    "📖 語文 Verbal",
                    min_value=60,
                    max_value=90,
                    value=70,
                    help="語文科目目前積分"
                )
                
                di_score = st.slider(
                    "📈 數據洞察 Data Insights",
                    min_value=60,
                    max_value=90,
                    value=72,
                    help="數據洞察科目目前積分"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 顯示目前差距
            score_gap = target_score - current_score
            if score_gap > 0:
                create_status_card(
                    f"目標分數差距: {score_gap} 分 ({'大幅提升' if score_gap > 50 else '適度提升'})",
                    "info",
                    "📊"
                )
            elif score_gap == 0:
                create_status_card("您已達到目標分數！", "success", "🎉")
            else:
                create_status_card("目前分數已超過目標分數", "warning", "⚠️")
    
    # 分頁 2: 時程安排
    with tabs[1]:
        with st.container():
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📅 重要日期")
                deadline = st.date_input(
                    "申請截止日期",
                    value=datetime.now() + timedelta(days=365),
                    min_value=datetime.now(),
                    help="您的申請截止日期"
                )
                
                language_status = st.selectbox(
                    "語言考試狀態",
                    ["已完成", "未完成"],
                    help="托福/雅思等語言考試是否已完成"
                )
            
            with col2:
                st.markdown("### 📋 準備狀況")
                app_progress = st.slider(
                    "申請資料完成度 (%)",
                    min_value=0,
                    max_value=100,
                    value=50,
                    help="申請資料(推薦信、個人陳述等)的完成百分比"
                )
                
                study_status = st.selectbox(
                    "備考身份",
                    ["全職考生", "在職考生"],
                    help="您目前的備考身份"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 顯示可用時間分析
            days_to_deadline = (deadline - datetime.now().date()).days
            create_progress_bar(
                min(100, (days_to_deadline / 365) * 100),
                f"距離申請截止還有 {days_to_deadline} 天"
            )
    
    # 分頁 3: 學習狀況
    with tabs[2]:
        with st.container():
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ⏰ 平日安排")
                weekday_hours = st.number_input(
                    "平日每日學習時數",
                    min_value=0.0,
                    max_value=24.0,
                    value=3.0,
                    step=0.5,
                    help="週一到週五每天可以學習的小時數"
                )
            
            with col2:
                st.markdown("### 🎯 假日安排")
                weekend_hours = st.number_input(
                    "假日每日學習時數",
                    min_value=0.0,
                    max_value=24.0,
                    value=8.0,
                    step=0.5,
                    help="週六、週日每天可以學習的小時數"
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 計算每週總時數
            weekly_total = (weekday_hours * 5) + (weekend_hours * 2)
            
            # 使用現代化指標卡顯示時間統計
            features = [
                {"value": f"{weekday_hours * 5:.1f}h", "label": "平日總時數", "icon": "📚"},
                {"value": f"{weekend_hours * 2:.1f}h", "label": "假日總時數", "icon": "📖"},
                {"value": f"{weekly_total:.1f}h", "label": "每週總時數", "icon": "⏰"}
            ]
            create_feature_grid(features)
            
            # 時間充裕度分析
            if study_status == "全職考生":
                create_status_card("全職考生：時間安排靈活", "success", "✅")
            else:
                if weekday_hours >= 4 and weekend_hours >= 8:
                    create_status_card("在職考生：時間安排充裕", "success", "✅")
                else:
                    create_status_card("在職考生：建議平日 ≥ 4小時，假日 ≥ 8小時", "warning", "⚠️")
    
    # 分頁 4: 生成計劃
    with tabs[3]:
        # 收集所有數據
        input_data = {
            "target_gmat_score": int(target_score),
            "target_score_system": score_system,
            "current_highest_gmat_score": int(current_score),
            "application_deadline": deadline.strftime("%Y-%m-%d"),
            "language_test_status": language_status,
            "application_materials_progress": float(app_progress),
            "study_status": study_status,
            "weekday_study_hours": float(weekday_hours),
            "weekend_study_hours": float(weekend_hours),
            "current_section_scores": {
                "Quantitative": int(quant_score),
                "Verbal": int(verbal_score),
                "Data Insights": int(di_score)
            }
        }
        
        # 顯示輸入摘要
        with st.expander("📋 輸入資料摘要", expanded=True):
            st.markdown('<div class="modern-card-compact">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🎯 目標與現況:**")
                st.write(f"• 目標分數: {target_score} ({score_system})")
                st.write(f"• 目前分數: {current_score}")
                st.write(f"• 分數差距: {target_score - current_score}")
                st.write(f"• 申請截止: {deadline}")
                
            with col2:
                st.markdown("**📚 學習安排:**")
                st.write(f"• 備考身份: {study_status}")
                st.write(f"• 平日學習: {weekday_hours} 小時/天")
                st.write(f"• 假日學習: {weekend_hours} 小時/天")
                st.write(f"• 每週總計: {weekly_total:.1f} 小時")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 生成計劃按鈕
        if st.button("🚀 生成個性化學習計劃", type="primary", use_container_width=True):
            with st.spinner("🔄 正在分析您的情況並生成學習計劃..."):
                try:
                    recommendations = st.session_state.planner.generate_study_plan(input_data)
                    st.session_state.last_recommendations = recommendations
                    st.session_state.study_plan_generated = True
                    
                    # 顯示結果
                    display_study_plan_results(recommendations)
                    
                except Exception as e:
                    create_status_card(f"計劃生成失敗: {str(e)}", "error", "❌")
        
        # 如果之前已經生成過計劃，顯示結果
        if st.session_state.study_plan_generated and st.session_state.last_recommendations:
            st.divider()
            create_section_header("最近生成的學習計劃", "📊")
            display_study_plan_results(st.session_state.last_recommendations, key_suffix="_recent")

def display_study_plan_results(recommendations: Dict[str, Any], key_suffix: str = ""):
    """顯示學習計劃結果"""
    
    if "error" in recommendations:
        create_status_card(
            f"<strong>錯誤</strong><br>{recommendations['error']}<br><strong>建議:</strong> {recommendations.get('recommendations', '請聯繫教學顧問獲得幫助')}",
            "error",
            "❌"
        )
        return
    
    # 成功生成計劃
    create_status_card("學習計劃生成成功！", "success", "✅")
    
    # 核心分析結果
    create_section_header("核心分析", "📊")
    
    # 使用現代化指標卡顯示核心指標
    analysis_features = []
    
    if 'score_gap_analysis' in recommendations and ':' in recommendations['score_gap_analysis']:
        analysis_features.append({
            "value": recommendations['score_gap_analysis'].split(':')[1].strip(),
            "label": "目標差距",
            "icon": "🎯"
        })
    
    if 'schedule_analysis' in recommendations and ':' in recommendations['schedule_analysis']:
        analysis_features.append({
            "value": recommendations['schedule_analysis'].split(':')[1].strip(),
            "label": "時程寬裕度",
            "icon": "📅"
        })
    
    if 'time_sufficiency_analysis' in recommendations and ':' in recommendations['time_sufficiency_analysis']:
        analysis_features.append({
            "value": recommendations['time_sufficiency_analysis'].split(':')[1].strip(),
            "label": "時間充裕度",
            "icon": "⏰"
        })
    
    if analysis_features:
        create_feature_grid(analysis_features)
    
    # 建議考試週期
    create_section_header("建議考試週期", "📅")
    cycle = recommendations.get('recommended_exam_cycle', '未定')
    st.markdown(f"""
    <div class="modern-card" style="text-align: center;">
        <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.5rem;">
            📚 {cycle}
        </div>
        <div style="font-size: 1rem; color: var(--neutral-600);">
            推薦的考試準備週期
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 學習策略
    create_section_header("學習策略建議", "📚")
    strategy = recommendations.get('recommended_study_strategy', '')
    if strategy:
        st.markdown(f"""
        <div class="modern-card">
            <div style="line-height: 1.6; font-size: 1rem;">
                {strategy.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 時間分配
    col1, col2 = st.columns(2)
    
    with col1:
        create_section_header("科目時間分配比例", "⏰")
        allocation_text = recommendations.get('recommended_section_time_allocation', '')
        if allocation_text:
            # 解析時間分配數據創建圖表
            allocation_data = parse_time_allocation(allocation_text)
            if allocation_data:
                fig = px.pie(
                    values=list(allocation_data.values()),
                    names=list(allocation_data.keys()),
                    title="科目時間分配比例",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    font=dict(size=14),
                    showlegend=True,
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                st.plotly_chart(fig, use_container_width=True, key=f"time_allocation_pie_chart{key_suffix}")
            
            st.markdown(f"""
            <div class="modern-card-compact">
                <div style="line-height: 1.6;">
                    {allocation_text.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        create_section_header("實際學習時間安排", "🕐")
        actual_time = recommendations.get('actual_study_time_allocation', '')
        if actual_time and actual_time != "未提供學習時間資訊":
            st.markdown(f"""
            <div class="modern-card-compact">
                <div style="line-height: 1.6;">
                    {actual_time.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            create_status_card("未提供詳細時間安排", "info", "ℹ️")
    
    # 詳細分析
    with st.expander("📈 詳細分析數據", expanded=False):
        st.markdown('<div class="modern-card-compact">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 提升需求:**")
            st.write(recommendations.get('required_score_improvement', 'N/A'))
            st.markdown("**📅 可用天數:**")
            st.write(recommendations.get('available_preparation_days', 'N/A'))
            
        with col2:
            st.markdown("**⏰ 每週學習:**")
            st.write(recommendations.get('weekly_study_hours', 'N/A'))
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 下載結果
    create_section_header("匯出結果", "💾")
    result_json = json.dumps(recommendations, ensure_ascii=False, indent=2)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 下載 JSON 格式",
            data=result_json,
            file_name=f"gmat_study_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key=f"download_json{key_suffix}"
        )
    
    with col2:
        # 創建簡化的文字版本
        text_report = generate_text_report(recommendations)
        st.download_button(
            label="📝 下載文字報告",
            data=text_report,
            file_name=f"gmat_study_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key=f"download_txt{key_suffix}"
        )

def parse_time_allocation(allocation_text: str) -> Dict[str, float]:
    """解析時間分配文字為數據"""
    allocation_data = {}
    lines = allocation_text.split('\n')
    
    for line in lines:
        if ':' in line and '%' in line:
            parts = line.split(':')
            if len(parts) == 2:
                subject = parts[0].strip()
                percentage_str = parts[1].strip().replace('%', '')
                try:
                    percentage = float(percentage_str)
                    allocation_data[subject] = percentage
                except ValueError:
                    continue
    
    return allocation_data

def generate_text_report(recommendations: Dict[str, Any]) -> str:
    """生成文字格式的報告"""
    report = []
    report.append("GMAT 學習計劃報告")
    report.append("=" * 50)
    report.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    if "error" not in recommendations:
        report.append(f"建議考試週期: {recommendations.get('recommended_exam_cycle', '未定')}")
        report.append("")
        
        report.append("學習策略:")
        report.append(recommendations.get('recommended_study_strategy', ''))
        report.append("")
        
        report.append("科目時間分配:")
        report.append(recommendations.get('recommended_section_time_allocation', ''))
        report.append("")
        
        report.append("實際時間安排:")
        report.append(recommendations.get('actual_study_time_allocation', ''))
        report.append("")
        
        report.append("詳細分析:")
        report.append(f"- {recommendations.get('score_gap_analysis', '')}")
        report.append(f"- {recommendations.get('schedule_analysis', '')}")
        report.append(f"- {recommendations.get('time_sufficiency_analysis', '')}")
        report.append(f"- 所需積分提升: {recommendations.get('required_score_improvement', '')}")
        report.append(f"- 可用準備天數: {recommendations.get('available_preparation_days', '')}")
        report.append(f"- 每週學習時數: {recommendations.get('weekly_study_hours', '')}")
    else:
        report.append(f"錯誤: {recommendations['error']}")
        report.append(f"建議: {recommendations.get('recommendations', '')}")
    
    return '\n'.join(report)

def show_analysis_tools():
    """顯示分析工具"""
    create_section_header("GMAT 分析工具", "📊")
    
    tool_tabs = st.tabs(["🔄 分數轉換", "📈 科目分析", "⏰ 時間規劃"])
    
    # 分數轉換工具
    with tool_tabs[0]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 🔄 GMAT 分數轉換工具")
        create_status_card("將舊制 GMAT 分數轉換為新制分數", "info", "ℹ️")
        
        old_score = st.number_input(
            "輸入舊制 GMAT 分數",
            min_value=200,
            max_value=800,
            value=650,
            help="10th Edition GMAT 分數"
        )
        
        if st.button("轉換分數", key="convert_score_btn"):
            new_score = st.session_state.planner.convert_old_to_new_gmat_score(old_score, "Old")
            
            # 使用現代化指標卡顯示轉換結果
            conversion_features = [
                {"value": str(old_score), "label": "舊制分數", "icon": "📊"},
                {"value": "→", "label": "轉換", "icon": "🔄"},
                {"value": str(new_score), "label": "新制分數", "icon": "🎯"}
            ]
            create_feature_grid(conversion_features)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 科目分析工具
    with tool_tabs[1]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 📈 科目投報率分析")
        create_status_card("分析各科目的投資報酬率和時間分配建議", "info", "ℹ️")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            q_score = st.slider("數學 Quantitative", 60, 90, 75)
        with col2:
            v_score = st.slider("語文 Verbal", 60, 90, 70)
        with col3:
            di_score = st.slider("數據洞察 Data Insights", 60, 90, 72)
        
        section_scores = {
            "Quantitative": q_score,
            "Verbal": v_score,
            "Data Insights": di_score
        }
        
        if st.button("分析科目投報率", key="analyze_section_roi_btn"):
            time_allocation, _ = st.session_state.planner.analyze_section_roi_and_time_allocation(section_scores)
            
            # 創建現代化的條形圖
            subjects = list(time_allocation.keys())
            percentages = list(time_allocation.values())
            
            fig = go.Figure(data=[
                go.Bar(
                    x=subjects, 
                    y=percentages, 
                    text=[f"{p:.1f}%" for p in percentages], 
                    textposition='auto',
                    marker=dict(
                        color=percentages,
                        colorscale='Viridis',
                        showscale=True
                    )
                )
            ])
            fig.update_layout(
                title=dict(
                    text="科目時間分配建議",
                    font=dict(size=18, color='var(--neutral-800)')
                ),
                xaxis_title="科目",
                yaxis_title="建議時間分配 (%)",
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True, key="subject_roi_bar_chart")
            
            # 顯示詳細數據
            df = pd.DataFrame({
                '科目': subjects,
                '目前積分': [section_scores[s] for s in subjects],
                '建議時間分配': [f"{p:.1f}%" for p in percentages]
            })
            st.dataframe(df, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 時間規劃工具
    with tool_tabs[2]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### ⏰ 學習時間規劃分析")
        
        deadline_date = st.date_input("申請截止日期", datetime.now() + timedelta(days=180))
        lang_status = st.selectbox("語言考試狀態", ["已完成", "未完成"])
        app_prog = st.slider("申請資料完成度 (%)", 0, 100, 30)
        study_stat = st.selectbox("備考身份", ["全職考生", "在職考生"])
        
        if st.button("分析時程規劃", key="analyze_schedule_btn"):
            schedule_sufficient, prep_days = st.session_state.planner.assess_gmat_preparation_schedule(
                deadline_date.strftime("%Y-%m-%d"),
                lang_status,
                app_prog,
                study_stat
            )
            
            # 使用現代化指標卡顯示結果
            schedule_features = [
                {"value": f"{prep_days}", "label": "可用準備天數", "icon": "📅"},
                {"value": schedule_sufficient, "label": "時程狀況", "icon": "⏰"}
            ]
            create_feature_grid(schedule_features)
            
            # 時間線圖
            today = datetime.now()
            deadline = datetime.strptime(deadline_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[today, deadline],
                y=[1, 1],
                mode='markers+lines',
                marker=dict(size=15, color='var(--primary-color)'),
                line=dict(width=5, color='var(--primary-color)'),
                name="準備時程"
            ))
            fig.update_layout(
                title="GMAT 準備時程規劃",
                xaxis_title="日期",
                yaxis=dict(showticklabels=False),
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, key="schedule_timeline_chart")
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_system_info():
    """顯示系統說明"""
    create_section_header("系統說明與使用指南", "ℹ️")
    
    info_tabs = st.tabs(["📖 使用指南", "🔧 系統功能", "📞 聯繫資訊"])
    
    with info_tabs[0]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 📖 使用指南")
        
        st.markdown("""
        #### 🚀 快速開始
        
        1. **基本資訊設定**: 輸入您的目標分數、目前分數和各科積分
        2. **時程安排**: 設定申請截止日期和準備狀況
        3. **學習狀況**: 輸入每日可用學習時間
        4. **生成計劃**: 點擊生成按鈕獲得個性化建議
        
        #### 📊 理解結果
        
        - **考試週期**: 建議的考試間隔時間
            - 基本方案 (16天): 快速衝刺
            - 進階方案 (30天): 系統複習
            - 頂級方案 (45天): 全面提升
            - 待定方案: 需要個別討論
        
        - **時間分配**: 根據各科投報率計算的最佳時間分配
        - **學習策略**: 針對您情況的具體建議
        
        #### 💡 使用建議
        
        - 誠實填寫所有資訊以獲得最準確的建議
        - 定期重新評估並調整計劃
        - 結合模考結果更新積分數據
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with info_tabs[1]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 🔧 系統功能")
        
        # 功能卡片網格
        feature_cards = [
            {"value": "🎯", "label": "學習計劃生成", "icon": "📚"},
            {"value": "📊", "label": "分析工具", "icon": "🔧"},
            {"value": "🏷️", "label": "診斷標籤路由", "icon": "🎯"},
            {"value": "💾", "label": "匯出功能", "icon": "⬇️"}
        ]
        create_feature_grid(feature_cards)
        
        st.markdown("""
        #### 核心功能詳解
        
        ##### 🎯 學習計劃生成
        - 個性化 GMAT 學習計劃
        - 考試週期建議
        - 科目時間分配
        - 學習策略建議
        
        ##### 📊 分析工具
        - **分數轉換**: 舊制 ↔ 新制分數轉換
        - **科目分析**: 投資報酬率計算
        - **時間規劃**: 準備時程評估
        
        ##### 🏷️ 診斷標籤路由
        - 多選 GMAT 診斷標籤
        - 自動匹配訓練指令和方法
        - 詳細的功能描述和使用時機說明
        
        ##### 💾 匯出功能
        - JSON 格式 (完整數據)
        - 文字報告 (簡化版本)
        - CSV 格式 (路由工具結果)
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with info_tabs[2]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 📞 聯繫資訊")
        
        contact_features = [
            {"value": "v2.1.0", "label": "系統版本", "icon": "🔧"},
            {"value": "🟢", "label": "系統狀態", "icon": "💚"},
            {"value": "最新", "label": "數據版本", "icon": "📊"}
        ]
        create_feature_grid(contact_features)
        
        st.markdown("""
        #### 技術支援
        
        如果您在使用過程中遇到任何問題，請聯繫：
        
        - **Email**: support@gmat-planner.com
        - **電話**: +886-2-1234-5678
        - **線上客服**: 週一至週五 9:00-18:00
        
        #### 數據隱私
        
        - 所有輸入的個人資料僅用於計劃生成
        - 不會儲存或傳輸您的個人資訊
        - 建議下載結果後自行保存
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 