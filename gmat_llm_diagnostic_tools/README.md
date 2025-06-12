# GMAT LLM 診斷工具 (GMAT LLM Diagnostic Tools)

這個資料夾包含了專門用於LLM整合的GMAT初步診斷建議腳本和工具，提供完整的GMAT備考解決方案。

## 📁 檔案結構

### 核心腳本
- **`gmat_study_planner.py`** - GMAT學習規劃主程式
- **`gmat_study_planner_gui.py`** - 主要 GUI 介面（整合版）
- **`gmat_route_tool.py`** - GMAT路由工具核心邏輯
- **`gmat_route_tool_gui.py`** - 路由工具 GUI 模組
- **`gmat_llm_function_handler.py`** - LLM功能調用處理器
- **`gmat_llm_integration_example.py`** - LLM整合範例
- **`modern_gui_styles.py`** - 現代化GUI樣式模組

### 啟動腳本
- **`run_integrated_gui.py`** - 整合系統啟動腳本

### 提示與配置
- **`gmat_llm_prompt.md`** - LLM提示詞模板
- **`gmat_route_prompt.md`** - 路由工具prompt
- **`prompt-to-label.md`** - 診斷標籤相關prompt

### 說明文件
- **`README_GMAT_PLANNER.md`** - GMAT規劃器詳細說明
- **`README_LLM_INTEGRATION.md`** - LLM整合指南
- **`MODERN_GUI_UPGRADE_GUIDE.md`** - GUI現代化升級指南

### 測試文件
- **`test_integration.py`** - 系統整合測試

## 🚀 快速開始

### 1. 安裝必要套件
```bash
pip install streamlit pandas plotly
```

### 2. 啟動整合系統

#### 使用啟動器（推薦）
```bash
python run_integrated_gui.py
```

#### 直接啟動 Streamlit
```bash
streamlit run gmat_study_planner_gui.py
```

### 3. 訪問系統
應用啟動後會自動在瀏覽器中開啟：
- **本地訪問**: http://localhost:8501

## 🎯 整合功能

### 📋 學習計劃生成
- **分步式資料收集**: 透過直觀的分頁介面收集用戶資訊
- **即時驗證與提示**: 輸入時提供即時反饋和建議
- **個性化分析**: 根據個人情況生成專屬學習計劃
- **視覺化結果**: 使用圖表展示時間分配和分析結果

### 🎯 診斷標籤路由 ⭐ **核心功能**
- **多選 GMAT 診斷標籤**: 支援同時選擇多個診斷標籤
- **自動匹配訓練指令**: 將中文診斷標籤映射到英文錯誤代碼
- **詳細功能描述**: 每個訓練指令都有詳細的功能說明和使用時機
- **支援7大GMAT科目**: CR, DS, GT, MSR, PS, RC, TPA
- **結果匯出**: 支援 CSV/JSON 格式匯出

### 📊 分析工具
- **分數轉換器**: 舊制 ↔ 新制 GMAT 分數轉換
- **科目投報率分析**: 計算各科目的學習投資報酬率
- **時間規劃分析**: 評估申請時程和準備充裕度

### 💾 結果匯出
- **JSON 格式**: 完整的分析數據
- **文字報告**: 簡化的可讀版本
- **CSV 匯出**: 診斷標籤分析結果

## 🎨 GUI特色

### 🎯 現代化設計
- **日夜主題切換**: 白天模式（白底黑字）和夜晚模式（黑底白字）
- **響應式布局**: 適配不同螢幕尺寸
- **清晰視覺層次**: 使用卡片式設計和一致的間距
- **豐富圖標**: 提升使用體驗

### 📊 視覺化展示
- **圓餅圖**: 科目時間分配比例
- **長條圖**: 科目投報率分析
- **時間線**: 準備時程規劃
- **指標卡**: 關鍵數據展示

## 🔧 診斷標籤路由使用指南

### 支援科目
- **CR**: Critical Reasoning (批判性推理)
- **DS**: Data Sufficiency (資料充分性)  
- **GT**: Geometry (幾何)
- **MSR**: Multi-Source Reasoning (多源推理)
- **PS**: Problem Solving (問題解決)
- **RC**: Reading Comprehension (閱讀理解)
- **TPA**: Two-Part Analysis (雙部分分析)

### 使用步驟
1. **選擇科目**: 在側邊欄選擇「🎯 診斷標籤路由」
2. **多選標籤**: 根據學習困難選擇相應的診斷標籤
3. **執行分析**: 點擊「🔄 分析選中標籤」
4. **檢視結果**: 查看訓練指令、功能描述和使用時機
5. **匯出結果**: 支援 CSV 和 JSON 格式

### 標籤示例
#### CR (Critical Reasoning)
- 題幹詞彙理解錯誤
- 邏輯鏈分析前提結論關係錯誤
- 核心問題識別錯誤

#### RC (Reading Comprehension)  
- 閱讀理解詞彙錯誤
- 長難句分析錯誤
- 文章結構理解錯誤

## 💻 LLM整合使用

### 基本使用
```python
from gmat_llm_function_handler import GMATLLMFunctionHandler

handler = GMATLLMFunctionHandler()
result = handler.generate_gmat_study_plan(user_data_json)
```

### 路由工具整合
```python
# 進入工具目錄
cd gmat_llm_diagnostic_tools

# 執行學習規劃器
python gmat_study_planner.py

# 執行LLM整合範例
python gmat_llm_integration_example.py
```

## 🔧 故障排除

### 常見問題

#### Q: 無法啟動應用
```bash
# 檢查 Python 版本（需要 3.7+）
python --version

# 重新安裝套件
pip install --upgrade streamlit pandas plotly

# 清除快取
streamlit cache clear
```

#### Q: 診斷標籤不顯示
- 確認 `gmat_route_tool.py` 檔案存在
- 檢查檔案權限
- 重新啟動系統

#### Q: 瀏覽器無法開啟
1. 手動開啟瀏覽器
2. 訪問 http://localhost:8501
3. 檢查防火牆設定

### 效能優化
```python
# 在 ~/.streamlit/config.toml 中設定
[server]
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

## 🔒 隱私與安全

### 資料處理
- ✅ 所有計算均在本地進行
- ✅ 不會上傳個人資料到雲端
- ✅ Session 結束後自動清除資料

## 📋 使用前提

- Python 3.7+
- Streamlit, Pandas, Plotly 套件
- 瀏覽器支援（Chrome, Firefox, Safari）

## 🔧 與主應用分離

此工具包獨立於 `gmat_diagnosis_app` 主應用程式，可以：
- 獨立部署和使用
- 作為微服務提供API
- 整合到其他LLM系統中

## 📖 詳細說明

請參閱各個檔案的相關文件以獲得更詳細的使用說明：
- [GMAT規劃器說明](./README_GMAT_PLANNER.md)
- [LLM整合指南](./README_LLM_INTEGRATION.md)
- [GUI現代化指南](./MODERN_GUI_UPGRADE_GUIDE.md)

## 📱 部署選項

### 本地部署
適合個人使用，資料完全在本地處理

### Streamlit Cloud 部署
1. 上傳程式碼到 GitHub
2. 連接 Streamlit Cloud  
3. 一鍵部署到雲端

### Docker 部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "gmat_study_planner_gui.py"]
```

## 更新日誌

### Version 2.1.0 (最新版本)
- ✅ 整合診斷標籤路由工具
- ✅ 新增多選標籤功能  
- ✅ 支援批量分析和結果匯出
- ✅ 現代化GUI設計（日夜主題）
- ✅ 文檔整合優化

### Version 2.0.0
- ✅ 原有學習規劃功能
- ✅ 分析工具模組
- ✅ 基礎 GUI 框架

---

**維護者**: GMAT診斷分析團隊  
**版本**: 2.1.0  
**最後更新**: 2025年1月30日 