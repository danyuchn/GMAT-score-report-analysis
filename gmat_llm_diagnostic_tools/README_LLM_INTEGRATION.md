# GMAT 學習計劃 LLM 整合系統

這個系統將原有的 GMAT 學習規劃器與 LLM 模型整合，透過 Function Calling 提供智能化的 GMAT 學習諮詢服務。

## 系統架構

```
用戶輸入 → LLM 對話收集資料 → JSON 格式轉換 → Function Calling → 
GMAT 規劃器處理 → JSON 格式輸出 → LLM 自然語言解釋 → 用戶接收建議
```

## 檔案結構

```
gmat_study_planner.py          # 原始 GMAT 學習規劃器
gmat_llm_function_handler.py   # LLM Function Calling 處理器
gmat_llm_prompt.md             # LLM 提示詞與使用指南  
gmat_llm_integration_example.py # 整合範例與測試腳本
README_LLM_INTEGRATION.md      # 本說明文件
```

## 核心功能

### 1. Function Calling 處理器 (`gmat_llm_function_handler.py`)

這個模組提供三個主要函數供 LLM 調用：

#### `get_input_schema()`
- **功能**: 獲取輸入資料格式說明
- **參數**: 無
- **返回**: JSON 字串，包含完整的輸入格式說明和範例

#### `validate_user_input(user_data)`
- **功能**: 驗證用戶輸入資料的格式和內容
- **參數**: `user_data` (JSON 字串) - 需要驗證的用戶資料
- **返回**: JSON 字串，包含驗證結果和錯誤訊息

#### `generate_gmat_study_plan(user_data)`
- **功能**: 生成完整的 GMAT 學習計劃
- **參數**: `user_data` (JSON 字串) - 完整的用戶資料
- **返回**: JSON 字串，包含詳細的學習計劃和建議

### 2. 輸入資料格式

系統需要收集以下完整資料：

```json
{
  "target_gmat_score": 700,           // 目標分數 (200-805)
  "target_score_system": "New",       // 分數制度 ("Old"/"New")
  "current_highest_gmat_score": 600,  // 目前最高分數 (200-805)
  "application_deadline": "2025-12-01", // 申請截止日期 (YYYY-MM-DD)
  "language_test_status": "已完成",   // 語言考試狀態
  "application_materials_progress": 50, // 申請資料完成度 (0-100)
  "study_status": "在職考生",         // 備考身份
  "weekday_study_hours": 3,           // 平日每日學習時數
  "weekend_study_hours": 8,           // 假日每日學習時數
  "current_section_scores": {         // 各科目積分 (60-90)
    "Quantitative": 75,
    "Verbal": 70,
    "Data Insights": 72
  }
}
```

### 3. 輸出格式

成功生成學習計劃時，系統返回以下結構：

```json
{
  "success": true,
  "study_plan": {
    "exam_cycle": "每30天",
    "study_strategy": "詳細的學習策略說明...",
    "section_time_allocation": "各科目時間分配百分比...",
    "actual_time_allocation": "實際學習時間分配...",
    "analysis": {
      "score_gap": "分數差距分析",
      "schedule_sufficiency": "時程寬裕度",
      "time_sufficiency": "時間充裕度",
      "required_improvement": "所需積分提升",
      "available_days": "可用準備天數",
      "weekly_hours": "每週學習時數"
    },
    "input_summary": { /* 輸入摘要 */ }
  },
  "timestamp": "2025-01-XX...",
  "system_version": "1.0"
}
```

## 安裝與設置

### 1. 安裝依賴套件

```bash
pip install openai
```

### 2. 設置 OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

或在 Python 中直接設置：

```python
import openai
openai.api_key = "your-api-key-here"
```

## 使用方式

### 方式一：直接使用 Function Handler

```python
from gmat_llm_function_handler import generate_gmat_study_plan
import json

# 準備用戶資料
user_data = {
    "target_gmat_score": 700,
    "target_score_system": "New",
    # ... 其他完整資料
}

# 生成學習計劃
result = generate_gmat_study_plan(json.dumps(user_data, ensure_ascii=False))
print(result)
```

### 方式二：透過 LLM 對話系統

```python
from gmat_llm_integration_example import GMATLLMAdvisor

# 初始化顧問
advisor = GMATLLMAdvisor()

# 開始對話
response = advisor.chat("我想制定一個 GMAT 學習計劃")
print(response)
```

### 方式三：運行整合範例

```bash
python gmat_llm_integration_example.py
```

選擇模式：
- **Demo 模式**: 無需 API，展示完整功能流程
- **互動模式**: 需要 OpenAI API，真實對話體驗

## LLM 提示詞使用

### OpenAI Function Calling 設置

```python
functions = [
    {
        "name": "generate_gmat_study_plan",
        "description": "根據學生的個人情況生成完整的 GMAT 學習計劃",
        "parameters": {
            "type": "object",
            "properties": {
                "user_data": {
                    "type": "string",
                    "description": "包含學生完整資訊的 JSON 字串"
                }
            },
            "required": ["user_data"]
        }
    }
    # ... 其他函數定義
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=conversation_history,
    functions=functions,
    function_call="auto"
)
```

### 系統提示詞關鍵點

1. **角色定義**: 專業的 GMAT 學習規劃顧問
2. **任務說明**: 收集資料、生成計劃、解釋建議
3. **對話流程**: 逐步收集，友善引導
4. **Function Calling 時機**: 驗證資料、生成計劃

## 對話流程範例

### 1. 開場與目標確認
```
顧問: 您好！我是您的 GMAT 學習規劃顧問...
用戶: 我想準備 GMAT，目標分數 700
顧問: 請問這是新制還是舊制的分數？
```

### 2. 現況評估
```
顧問: 了解您的目標後，現在想了解您目前的程度...
用戶: 我目前最高分數 600，各科積分...
顧問: [調用 validate_user_input 驗證資料]
```

### 3. 時程規劃
```
顧問: 接下來了解您的申請時程...
用戶: 申請截止日期 2025-12-01...
```

### 4. 學習安排
```
顧問: 最後了解您的學習安排...
用戶: 我是在職考生，平日 3 小時...
```

### 5. 計劃生成
```
顧問: [調用 generate_gmat_study_plan]
顧問: 📊 您的學習計劃分析完成！[解釋結果]
```

## 自定義與擴展

### 1. 修改提示詞

編輯 `gmat_llm_prompt.md` 或 `gmat_llm_integration_example.py` 中的 `SYSTEM_PROMPT`

### 2. 增加新功能

在 `gmat_llm_function_handler.py` 中添加新的處理函數：

```python
def new_function(parameter: str) -> str:
    """新功能的處理邏輯"""
    # 實作邏輯
    return json.dumps(result, ensure_ascii=False)
```

### 3. 支援其他 LLM 模型

修改 `GMATLLMAdvisor` 類別以支援其他 API：

```python
# 例如：Claude、Gemini 等
class CustomLLMAdvisor:
    def __init__(self, model_provider="openai"):
        self.provider = model_provider
        # 實作不同模型的調用邏輯
```

## 測試與驗證

### 1. 功能測試

```bash
python gmat_llm_function_handler.py
```

### 2. 整合測試

```bash
python gmat_llm_integration_example.py
```

選擇 Demo 模式查看完整流程

### 3. 資料驗證測試

```python
from gmat_llm_function_handler import validate_user_input

# 測試不完整資料
incomplete_data = {"target_gmat_score": 700}
result = validate_user_input(json.dumps(incomplete_data))
print(result)  # 應該顯示缺少欄位的錯誤
```

## 常見問題

### Q1: Function Calling 沒有被觸發
**A**: 檢查 function 定義格式是否正確，確保 LLM 能理解何時需要調用函數

### Q2: JSON 格式錯誤
**A**: 確保所有輸入資料都符合預期格式，使用 `validate_user_input` 進行預先檢查

### Q3: API 調用失敗
**A**: 檢查 API Key 設置和網路連接，確認 openai 套件版本相容

### Q4: 中文顯示問題
**A**: 確保使用 `ensure_ascii=False` 參數處理 JSON，並檢查終端編碼設置

## 注意事項

1. **API 費用**: LLM 調用會產生費用，建議先使用 Demo 模式測試
2. **資料隱私**: 注意用戶資料的隱私保護
3. **錯誤處理**: 系統包含完整的錯誤處理機制，但仍需監控異常情況
4. **版本相容**: 確保 openai 套件版本與 API 版本相容

## 技術支援

如遇到問題，請檢查：
1. 日誌檔案 (`gmat_llm_handler.log`)
2. 函數調用的參數格式
3. API 回應內容
4. 系統相依性設置

## 授權與免責聲明

本系統僅供學習和研究使用，生成的學習計劃建議僅供參考，實際學習安排請結合個人情況和專業意見。 