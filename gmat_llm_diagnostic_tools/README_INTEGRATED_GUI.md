# GMAT 整合 GUI 系統使用說明
# GMAT Integrated GUI System User Guide

## 系統概述 | System Overview

本系統整合了 GMAT 學習規劃工具和診斷標籤路由工具，提供完整的 GMAT 備考解決方案。
This system integrates the GMAT study planning tool and diagnostic label routing tool, providing a comprehensive GMAT preparation solution.

## 核心功能 | Core Features

### 1. 🎯 學習計劃生成 | Study Plan Generation
- 個性化 GMAT 學習計劃制定
- 基於目標分數和現有能力的時間分配建議
- 考試週期和策略建議

### 2. 📊 分析工具 | Analysis Tools
- GMAT 分數轉換（舊制 ↔ 新制）
- 科目投資報酬率分析
- 學習時程規劃評估

### 3. 🎯 診斷標籤路由 | Diagnostic Label Routing ⭐ **新功能**
- 多選 GMAT 診斷標籤
- 自動匹配訓練指令和方法
- 詳細的功能描述和使用時機說明
- 支援 CSV/JSON 結果匯出

### 4. ℹ️ 系統說明 | System Information
- 詳細的使用指南和功能說明
- 技術支援資訊

## 安裝需求 | Installation Requirements

### Python 套件 | Python Packages
```bash
pip install streamlit pandas plotly
```

### 必要檔案 | Required Files
確保以下檔案存在於同一目錄中：
- `gmat_study_planner_gui.py` - 主要 GUI 介面
- `gmat_route_tool_gui.py` - 路由工具 GUI 模組
- `gmat_route_tool.py` - 路由工具核心邏輯
- `gmat_study_planner.py` - 學習規劃核心邏輯
- `run_integrated_gui.py` - 系統啟動腳本

## 啟動系統 | Starting the System

### 方法 1: 使用啟動腳本 | Method 1: Using Launch Script
```bash
python run_integrated_gui.py
```

### 方法 2: 直接使用 Streamlit | Method 2: Direct Streamlit
```bash
streamlit run gmat_study_planner_gui.py
```

系統將在 http://localhost:8501 啟動

## 診斷標籤路由工具使用指南 | Diagnostic Label Routing Tool Guide

### 步驟 1: 選擇科目 | Step 1: Select Subject
1. 在側邊欄選擇「🎯 診斷標籤路由」
2. 在「📋 標籤選擇」分頁中選擇 GMAT 科目：
   - **CR**: Critical Reasoning (批判性推理)
   - **DS**: Data Sufficiency (資料充分性)
   - **GT**: Geometry (幾何)
   - **MSR**: Multi-Source Reasoning (多源推理)
   - **PS**: Problem Solving (問題解決)
   - **RC**: Reading Comprehension (閱讀理解)
   - **TPA**: Two-Part Analysis (雙部分分析)

### 步驟 2: 多選診斷標籤 | Step 2: Multi-Select Diagnostic Labels
1. 系統會顯示該科目的所有可用診斷標籤
2. 根據學習者的實際困難情況，勾選相應的標籤
3. 支援同時選擇多個標籤進行批量分析

### 步驟 3: 執行分析 | Step 3: Execute Analysis
1. 點擊「🔄 分析選中標籤」按鈕
2. 系統會自動：
   - 將中文診斷標籤映射到英文錯誤代碼
   - 匹配對應的訓練指令
   - 生成詳細的功能描述和使用時機說明

### 步驟 4: 檢視結果 | Step 4: View Results
1. 切換到「📊 結果分析」分頁
2. 查看分析結果，包括：
   - 訓練指令名稱
   - 功能描述
   - 使用時機說明
3. 使用可展開式介面檢視詳細內容

### 步驟 5: 匯出結果 | Step 5: Export Results
1. 支援 CSV 和 JSON 格式匯出
2. 檔案名稱自動包含科目和時間戳記
3. 便於後續分析和追蹤

## 診斷標籤示例 | Diagnostic Label Examples

### CR (Critical Reasoning) 示例標籤：
- 題幹詞彙理解錯誤
- 邏輯鏈分析前提結論關係錯誤
- 核心問題識別錯誤
- 強干擾選項混淆錯誤

### RC (Reading Comprehension) 示例標籤：
- 閱讀理解詞彙錯誤
- 長難句分析錯誤
- 文章結構理解錯誤
- 推理錯誤

### PS (Problem Solving) 示例標籤：
- 閱讀理解錯誤
- 概念應用錯誤
- 計算錯誤
- 基礎掌握不穩定

## 系統特色 | System Features

### 🔧 技術特色 | Technical Features
- **響應式設計**: 支援桌面和平板裝置
- **即時分析**: 快速診斷標籤分析
- **批量處理**: 支援多標籤同時分析
- **結果匯出**: 多格式檔案輸出

### 🎯 教學特色 | Educational Features
- **中英對照**: 提供中英文對照標籤說明
- **詳細描述**: 每個訓練指令都有詳細的功能描述
- **使用時機**: 明確說明何時使用特定訓練方法
- **學習路徑**: 根據診斷結果提供個性化學習建議

## 疑難排解 | Troubleshooting

### 常見問題 | Common Issues

**Q1: 系統無法啟動**
- 檢查 Python 版本 (建議 3.7+)
- 確認已安裝所有必要套件
- 檢查檔案完整性

**Q2: 診斷標籤不顯示**
- 確認 `gmat_route_tool.py` 檔案存在
- 檢查檔案權限
- 重新啟動系統

**Q3: 匯出功能異常**
- 檢查瀏覽器下載設定
- 確認有足夠的磁碟空間
- 檢查檔案權限

### 技術支援 | Technical Support
如遇到其他問題，請檢查：
1. 控制台錯誤訊息
2. Streamlit 日誌檔案
3. Python 環境設定

## 更新日誌 | Update Log

### Version 2.1.0 (最新版本)
- ✅ 整合診斷標籤路由工具
- ✅ 新增多選標籤功能
- ✅ 支援批量分析和結果匯出
- ✅ 增強使用者介面體驗
- ✅ 新增綜合說明文檔

### Version 2.0.0
- ✅ 原有學習規劃功能
- ✅ 分析工具模組
- ✅ 基礎 GUI 框架

## 未來規劃 | Future Plans

- 🔄 增加更多 GMAT 科目支援
- 📊 加入視覺化分析圖表
- 🤖 整合 AI 學習建議
- 🌐 多語言支援擴展
- 📱 行動裝置適配優化

---

**作者**: GMAT GPT Team  
**版本**: 2.1.0  
**最後更新**: 2025-01-30 