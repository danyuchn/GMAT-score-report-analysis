#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Route Tool GUI Module
GMAT 路由工具圖形化介面模組

A Streamlit-based GUI component for the GMAT Issue Router with diagnostic label multi-selection
使用 Streamlit 構建的 GMAT 議題路由器，支援診斷標籤多選功能
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import sys
import os

# Add current directory to path for importing gmat_route_tool
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from gmat_route_tool import Tools
from modern_gui_styles import (
    create_section_header, 
    create_status_card,
    create_metric_card,
    create_feature_grid
)

def show_route_tool():
    """顯示 GMAT 路由工具介面"""
    
    create_section_header("GMAT 診斷標籤路由工具", "🎯")
    
    # 初始化路由工具
    if 'route_tool' not in st.session_state:
        st.session_state.route_tool = Tools()
    
    # 創建分頁
    route_tabs = st.tabs(["📋 標籤選擇", "📊 結果分析", "💡 工具說明"])
    
    # 分頁 1: 標籤選擇
    with route_tabs[0]:
        show_label_selection()
    
    # 分頁 2: 結果分析  
    with route_tabs[1]:
        show_results_analysis()
        
    # 分頁 3: 工具說明
    with route_tabs[2]:
        show_tool_info()

def show_label_selection():
    """顯示診斷標籤選擇介面"""
    
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    
    st.markdown("### 📋 選擇 GMAT 科目和診斷標籤")
    
    # 科目選擇
    col1, col2 = st.columns([1, 2])
    
    with col1:
        available_categories = st.session_state.route_tool.get_available_categories()
        selected_category = st.selectbox(
            "🎯 選擇 GMAT 科目",
            available_categories,
            help="選擇要分析的 GMAT 科目類別"
        )
    
    with col2:
        # 顯示科目說明
        category_descriptions = {
            "CR": "Critical Reasoning - 批判性推理",
            "DS": "Data Sufficiency - 資料充分性", 
            "GT": "Geometry - 幾何",
            "MSR": "Multi-Source Reasoning - 多源推理",
            "PS": "Problem Solving - 問題解決",
            "RC": "Reading Comprehension - 閱讀理解",
            "TPA": "Two-Part Analysis - 雙部分分析"
        }
        create_status_card(
            f"**{selected_category}**: {category_descriptions.get(selected_category, '未知科目')}",
            "info",
            "📚"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if selected_category:
        # 獲取該科目的診斷標籤映射
        error_codes_mapping = st.session_state.route_tool.get_error_codes_mapping(selected_category)
        
        if error_codes_mapping:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown(f"### 🏷️ {selected_category} 科目診斷標籤")
            
            # 創建兩欄布局顯示標籤
            col1, col2 = st.columns(2)
            
            # 將標籤分成兩組
            labels = list(error_codes_mapping.keys())
            mid_point = len(labels) // 2
            
            selected_labels = []
            
            with col1:
                st.markdown("**錯誤類型標籤 (第一組)**")
                for label in labels[:mid_point]:
                    if st.checkbox(label, key=f"checkbox_{selected_category}_{label}_1"):
                        selected_labels.append(label)
            
            with col2:
                st.markdown("**困難類型標籤 (第二組)**")
                for label in labels[mid_point:]:
                    if st.checkbox(label, key=f"checkbox_{selected_category}_{label}_2"):
                        selected_labels.append(label)
            
            # 存儲選中的標籤到 session state
            st.session_state[f'selected_labels_{selected_category}'] = selected_labels
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 顯示已選擇的標籤數量
            if selected_labels:
                create_status_card(f"已選擇 {len(selected_labels)} 個診斷標籤", "success", "✅")
                
                # 顯示選中的標籤
                with st.expander("🔍 查看已選擇的標籤", expanded=False):
                    st.markdown('<div class="modern-card-compact">', unsafe_allow_html=True)
                    for i, label in enumerate(selected_labels, 1):
                        error_code = error_codes_mapping[label]
                        st.write(f"{i}. **{label}** → `{error_code}`")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 分析按鈕
                if st.button("🔄 分析選中標籤", type="primary", key=f"analyze_{selected_category}"):
                    analyze_selected_labels(selected_category, selected_labels, error_codes_mapping)
            else:
                create_status_card("請至少選擇一個診斷標籤進行分析", "warning", "⚠️")
        else:
            create_status_card(f"無法找到 {selected_category} 科目的診斷標籤", "error", "❌")

def analyze_selected_labels(category: str, selected_labels: List[str], error_codes_mapping: Dict[str, str]):
    """分析選中的診斷標籤"""
    
    results = []
    
    for label in selected_labels:
        error_code = error_codes_mapping[label]
        
        # 獲取對應的訓練指令和描述
        commands_result = st.session_state.route_tool.get_commands_with_descriptions(category, error_code)
        
        if "error" not in commands_result:
            for cmd_detail in commands_result.get("commands_with_descriptions", []):
                results.append({
                    "診斷標籤": label,
                    "錯誤代碼": error_code,
                    "訓練指令": cmd_detail["command"],
                    "功能描述": cmd_detail["description"],
                    "使用時機": cmd_detail["usage_occasion"]
                })
        else:
            create_status_card(f"分析標籤 '{label}' 時發生錯誤: {commands_result['error']}", "error", "❌")
    
    # 存儲結果到 session state
    st.session_state[f'analysis_results_{category}'] = results
    
    # 顯示成功訊息
    if results:
        create_status_card(f"成功分析 {len(selected_labels)} 個診斷標籤，生成 {len(results)} 個訓練建議", "success", "✅")

def show_results_analysis():
    """顯示結果分析"""
    
    create_section_header("診斷標籤分析結果", "📊")
    
    # 檢查是否有分析結果
    has_results = False
    available_categories = st.session_state.route_tool.get_available_categories()
    
    for category in available_categories:
        results_key = f'analysis_results_{category}'
        if results_key in st.session_state and st.session_state[results_key]:
            has_results = True
            break
    
    if not has_results:
        create_status_card("請先在「標籤選擇」分頁中選擇診斷標籤並進行分析", "info", "📝")
        return
    
    # 選擇要查看的科目結果
    categories_with_results = []
    for category in available_categories:
        results_key = f'analysis_results_{category}'
        if results_key in st.session_state and st.session_state[results_key]:
            categories_with_results.append(category)
    
    if categories_with_results:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        selected_result_category = st.selectbox(
            "🎯 選擇要查看的科目結果",
            categories_with_results,
            help="選擇要查看分析結果的科目"
        )
        
        results = st.session_state[f'analysis_results_{selected_result_category}']
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 顯示統計資訊
        stats_features = [
            {"value": selected_result_category, "label": "科目", "icon": "📚"},
            {"value": str(len(set([r["診斷標籤"] for r in results]))), "label": "診斷標籤數", "icon": "🏷️"},
            {"value": str(len(results)), "label": "訓練指令數", "icon": "🎯"}
        ]
        create_feature_grid(stats_features)
        
        # 顯示詳細結果表格
        create_section_header("詳細分析結果", "📋")
        df = pd.DataFrame(results)
        
        # 使用可展開的方式顯示每個結果
        for i, row in df.iterrows():
            with st.expander(f"📌 {row['診斷標籤']} → {row['訓練指令']}", expanded=False):
                st.markdown('<div class="modern-card-compact">', unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**基本資訊**")
                    st.write(f"**診斷標籤**: {row['診斷標籤']}")
                    st.write(f"**錯誤代碼**: `{row['錯誤代碼']}`")
                    st.write(f"**訓練指令**: {row['訓練指令']}")
                
                with col2:
                    st.markdown("**詳細說明**")
                    st.markdown("**📝 功能描述**")
                    st.write(row['功能描述'])
                    
                    st.markdown("**⏰ 使用時機**")
                    st.write(row['使用時機'])
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # 匯出功能
        create_section_header("匯出分析結果", "💾")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV 匯出
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 下載 CSV 檔案",
                data=csv,
                file_name=f"gmat_route_analysis_{selected_result_category}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # JSON 匯出
            json_data = df.to_json(orient='records', force_ascii=False, indent=2)
            st.download_button(
                label="📋 下載 JSON 檔案", 
                data=json_data,
                file_name=f"gmat_route_analysis_{selected_result_category}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def show_tool_info():
    """顯示工具說明"""
    
    create_section_header("GMAT 診斷標籤路由工具說明", "💡")
    
    info_tabs = st.tabs(["🔧 功能介紹", "📖 使用指南", "🎯 科目說明"])
    
    with info_tabs[0]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 🎯 工具目標")
        create_status_card(
            "本工具旨在根據 GMAT 學習者的診斷標籤，自動推薦最適合的訓練指令和學習方法。",
            "info",
            "🎯"
        )
        
        st.markdown("### 🔧 核心功能")
        
        # 功能卡片
        function_features = [
            {"value": "✨", "label": "多選診斷標籤", "icon": "🏷️"},
            {"value": "🔄", "label": "自動路由分析", "icon": "⚙️"},
            {"value": "📊", "label": "結果視覺化", "icon": "📈"},
            {"value": "💾", "label": "匯出功能", "icon": "⬇️"}
        ]
        create_feature_grid(function_features)
        
        st.markdown("""
        #### 1. 多選診斷標籤
        - 支援同時選擇多個診斷標籤
        - 按科目分類組織標籤
        - 提供中英文對照的標籤說明
        
        #### 2. 自動路由分析
        - 根據選中標籤自動匹配訓練指令
        - 提供詳細的功能描述和使用時機
        - 支援批量分析多個標籤
        
        #### 3. 結果視覺化
        - 表格化展示分析結果
        - 可展開式詳細檢視
        - 支援 CSV 和 JSON 格式匯出
        
        ### 📊 分析邏輯
        
        1. **標籤映射**: 中文診斷標籤 → 英文錯誤代碼
        2. **指令匹配**: 錯誤代碼 → 對應訓練指令列表  
        3. **描述生成**: 訓練指令 → 功能描述 + 使用時機
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with info_tabs[1]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 📖 使用步驟")
        
        st.markdown("""
        #### 步驟 1: 選擇科目
        在「標籤選擇」分頁中，首先選擇要分析的 GMAT 科目 (CR, DS, GT, MSR, PS, RC, TPA)。
        
        #### 步驟 2: 多選診斷標籤
        根據學習者的實際困難情況，勾選相應的診斷標籤。可以同時選擇多個標籤。
        
        #### 步驟 3: 執行分析
        點擊「分析選中標籤」按鈕，系統會自動分析並生成對應的訓練建議。
        
        #### 步驟 4: 檢視結果
        在「結果分析」分頁中查看詳細的分析結果，包括：
        - 訓練指令名稱
        - 功能描述
        - 使用時機說明
        
        #### 步驟 5: 匯出結果
        可將分析結果匯出為 CSV 或 JSON 格式，便於後續使用。
        """)
        
        st.markdown("### 💡 使用建議")
        
        tips_features = [
            {"value": "🎯", "label": "精確選擇", "icon": "✅"},
            {"value": "📚", "label": "分科分析", "icon": "📖"},
            {"value": "🔄", "label": "結合實際", "icon": "💡"}
        ]
        create_feature_grid(tips_features)
        
        st.markdown("""
        - **精確選擇**: 根據實際診斷結果精確選擇標籤，避免過度泛化
        - **分科分析**: 建議按科目分別進行分析，以獲得更精準的建議
        - **結合實際**: 將系統建議與實際學習狀況結合，制定個性化學習計劃
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with info_tabs[2]:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        st.markdown("### 🎯 GMAT 科目說明")
        
        # 科目統計
        subject_features = [
            {"value": "7", "label": "總科目數", "icon": "📚"},
            {"value": "100+", "label": "診斷標籤", "icon": "🏷️"},
            {"value": "200+", "label": "訓練指令", "icon": "🎯"}
        ]
        create_feature_grid(subject_features)
        
        st.markdown("""
        #### CR (Critical Reasoning) - 批判性推理
        - 評估論證的邏輯結構
        - 識別假設、加強論證、削弱論證
        - 分析邏輯謬誤和推理錯誤
        
        #### DS (Data Sufficiency) - 資料充分性
        - 判斷給定條件是否足以解決問題
        - 數學概念與邏輯推理結合
        - 注重條件分析而非計算能力
        
        #### GT (Geometry) - 幾何
        - 平面幾何和立體幾何概念
        - 圖形分析和空間想像
        - 幾何定理的應用
        
        #### MSR (Multi-Source Reasoning) - 多源推理  
        - 整合多個資料來源
        - 圖表、表格、文字的綜合分析
        - 資訊整合與邏輯推理
        
        #### PS (Problem Solving) - 問題解決
        - 數學應用題解決
        - 涵蓋代數、幾何、統計等領域
        - 注重解題策略和計算準確性
        
        #### RC (Reading Comprehension) - 閱讀理解
        - 長篇文章理解與分析
        - 主旨、細節、推論題型
        - 提升閱讀速度和理解深度
        
        #### TPA (Two-Part Analysis) - 雙部分分析
        - 複合型問題解決
        - 同時考查邏輯和數學能力
        - 需要綜合性思考能力
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

def create_summary_report():
    """創建跨科目綜合分析報告"""
    
    available_categories = st.session_state.route_tool.get_available_categories()
    all_results = []
    
    # 收集所有科目的分析結果
    for category in available_categories:
        results_key = f'analysis_results_{category}'
        if results_key in st.session_state and st.session_state[results_key]:
            for result in st.session_state[results_key]:
                result['科目'] = category
                all_results.append(result)
    
    if not all_results:
        return None
    
    # 生成統計摘要
    df = pd.DataFrame(all_results)
    
    summary = {
        "總科目數": df['科目'].nunique(),
        "總診斷標籤數": df['診斷標籤'].nunique(), 
        "總訓練指令數": len(df),
        "科目分布": df['科目'].value_counts().to_dict(),
        "熱門訓練指令": df['訓練指令'].value_counts().head(5).to_dict()
    }
    
    return summary, df 