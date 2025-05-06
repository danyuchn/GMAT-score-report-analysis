# GMAT 診斷應用程式

## 2024年重要更新

### 代碼模組化重構

GMAT診斷應用已被重構為以下模組結構，以改善可維護性：

```
gmat_diagnosis_app/
├── app.py                      # 主應用入口(精簡版)
├── constants/                  # 常量和配置
│   ├── __init__.py
│   ├── config.py               # 應用配置和常量
│   └── validation_rules.py     # 數據驗證規則
├── utils/                      # 工具函數
│   ├── __init__.py
│   ├── data_processing.py      # 數據處理函數
│   ├── excel_utils.py          # Excel生成工具
│   ├── styling.py              # 表格樣式工具
│   └── validation.py           # 數據驗證工具
├── services/                   # 服務
│   ├── __init__.py
│   ├── openai_service.py       # OpenAI API服務
│   └── plotting_service.py     # 圖表生成服務
├── ui/                         # 用戶界面
│   ├── __init__.py
│   ├── chat_interface.py       # 聊天界面
│   ├── input_tabs.py           # 數據輸入標籤頁
│   └── results_display.py      # 結果顯示
└── ... (原有的診斷模組等)
```

### 應用功能

- 上傳或貼上各科成績單，進行數據驗證和清洗
- 模擬IRT計算能力估計和題目難度
- 執行診斷分析並生成詳細報告
- 使用OpenAI進行報告整理和匯總建議
- AI問答功能，基於診斷報告和數據

### 顯示順序更新

- 從診斷試算表輸出中移除了「科目」欄位
- 將特定欄位移到最右側：
  - 是否正確（答對?）
  - SFE?
  - 是否無效
  - 其他二元/布林值欄位
- 優化Excel顯示，確保排序時顏色渲染跟隨數據移動
  - 使用儲存格級別條件格式，避免跨行條件格式
  - 確保錯題整列渲染為紅色
  - 修改超時標記方法，使其與數據行綁定

### 特定科目優化

- 針對DI科目，移除「考察能力」欄位
- 確保所有數值欄位(難度、用時)都使用正確的數值格式
- 優化條件格式處理順序，確保多個條件的優先級正確
