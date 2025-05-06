# GMAT 診斷應用程式

## 2024年重要更新

### 代碼模組化重構

GMAT診斷應用已被重構為以下模組結構，以改善可維護性：

```
gmat_diagnosis_app/
├── __init__.py                 # 套件初始化檔案
├── app.py                      # 主應用程式進入點
├── analysis_orchestrator.py    # 分析協調器
├── diagnosis_module.py         # 診斷主模組
├── irt_module.py               # 項目反應理論模組
├── preprocess_helpers.py       # 預處理輔助函數
├── session_manager.py          # 會話管理器
├── README.md                   # 專案說明文件
│
├── analysis_helpers/           # 分析輔助工具
│   ├── __init__.py
│   └── time_analyzer.py        # 時間分析器
│
├── constants/                  # 常量和配置
│   ├── __init__.py
│   ├── config.py               # 應用配置和常量
│   ├── thresholds.py           # 閾值設定
│   └── validation_rules.py     # 數據驗證規則
│
├── data_validation/            # 數據驗證模組
│   ├── __init__.py
│   └── invalid_suggestion.py   # 無效建議處理
│
├── diagnostics/                # 核心診斷模組
│   ├── __init__.py
│   ├── di_diagnostic.py        # DI 診斷協調器
│   ├── q_diagnostic.py         # Quant 診斷協調器
│   ├── v_diagnostic.py         # Verbal 診斷協調器
│   │
│   ├── di_modules/             # DI 特定模組
│   │   ├── __init__.py
│   │   ├── chapter_logic.py
│   │   ├── constants.py
│   │   ├── main.py
│   │   ├── report_generation.py
│   │   ├── translation.py
│   │   └── utils.py
│   │
│   ├── q_modules/              # Quant 特定模組
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── behavioral.py
│   │   ├── constants.py
│   │   ├── main.py
│   │   ├── recommendations.py
│   │   ├── reporting.py
│   │   ├── translations.py
│   │   └── utils.py
│   │
│   └── v_modules/              # Verbal 特定模組
│       ├── __init__.py
│       ├── analysis.py
│       ├── constants.py
│       ├── main.py
│       ├── recommendations.py
│       ├── reporting.py
│       ├── translations.py
│       └── utils.py
│
├── services/                   # 外部服務接口
│   ├── __init__.py
│   ├── openai_service.py       # OpenAI API服務
│   └── plotting_service.py     # 圖表生成服務
│
├── subject_preprocessing/      # 各科目預處理
│   ├── __init__.py
│   ├── di_preprocessor.py      # DI 預處理器
│   └── verbal_preprocessor.py  # Verbal 預處理器
│
├── ui/                         # 使用者介面元件
│   ├── __init__.py
│   ├── chat_interface.py       # 聊天界面
│   ├── input_tabs.py           # 數據輸入標籤頁
│   └── results_display.py      # 結果顯示
│
└── utils/                      # 通用工具函數
    ├── __init__.py
    ├── data_processing.py      # 數據處理函數
    ├── excel_utils.py          # Excel生成工具
    ├── parsing_utils.py        # 解析工具
    ├── styling.py              # 表格樣式工具
    └── validation.py           # 數據驗證工具
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
