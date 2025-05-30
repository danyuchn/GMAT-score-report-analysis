# GMAT LLM 診斷工具 (GMAT LLM Diagnostic Tools)

這個資料夾包含了專門用於LLM整合的GMAT初步診斷建議腳本和工具。

## 📁 檔案結構

### 核心腳本
- **`gmat_study_planner.py`** - GMAT學習規劃主程式
- **`gmat_llm_function_handler.py`** - LLM功能調用處理器
- **`gmat_route_tool.py`** - GMAT路由工具
- **`gmat_llm_integration_example.py`** - LLM整合範例

### 提示與配置
- **`gmat_llm_prompt.md`** - LLM提示詞模板

### 說明文件
- **`README_GMAT_PLANNER.md`** - GMAT規劃器詳細說明
- **`README_LLM_INTEGRATION.md`** - LLM整合指南

## 🚀 快速開始

### 1. 基本使用
```bash
# 進入工具目錄
cd gmat_llm_diagnostic_tools

# 執行學習規劃器
python gmat_study_planner.py

# 執行LLM整合範例
python gmat_llm_integration_example.py
```

### 2. LLM功能調用
```python
from gmat_llm_function_handler import GMATLLMFunctionHandler

handler = GMATLLMFunctionHandler()
result = handler.generate_gmat_study_plan(user_data_json)
```

## 🎯 主要功能

- **個性化學習計劃生成** - 基於學生現況生成客製化讀書計劃
- **LLM整合介面** - 提供與語言模型整合的標準化接口
- **智能診斷建議** - 自動分析並提供學習策略建議
- **多維度評估** - 涵蓋時間、分數、科目等多個維度的分析

## 📋 使用前提

- Python 3.7+
- 無外部依賴（僅使用標準庫）

## 🔧 與主應用分離

此工具包獨立於 `gmat_diagnosis_app` 主應用程式，可以：
- 獨立部署和使用
- 作為微服務提供API
- 整合到其他LLM系統中

## 📖 詳細說明

請參閱各個檔案的相關README文件以獲得更詳細的使用說明：
- [GMAT規劃器說明](./README_GMAT_PLANNER.md)
- [LLM整合指南](./README_LLM_INTEGRATION.md)

---

**維護者**: GMAT診斷分析團隊  
**版本**: 1.0  
**最後更新**: 2025年1月 