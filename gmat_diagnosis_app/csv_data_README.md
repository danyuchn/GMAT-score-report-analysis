# GMAT 診斷數據 CSV 數據服務

此模組提供了一個 Python 後端，用於管理 GMAT 診斷數據和學生主觀回饋，並將這些數據儲存在 CSV 檔案中。

## 主要功能

該服務處理兩種類型的數據：

1. **GMAT 表現數據**：存儲學生測試部分的詳細逐題表現數據。
2. **學生主觀回饋**：存儲學生對完成的測試部分的時間壓力主觀回報。

## CSV 檔案結構

### `gmat_performance_data.csv`

- `student_id` (字串)：學生唯一識別碼
- `test_instance_id` (字串)：每個測試的唯一識別碼
- `gmat_section` (字串)：'Q', 'DI', 或 'V'
- `test_date` (字串)：YYYY-MM-DD 格式
- `question_id` (字串或整數)：與原始數據中的 ID 一致
- `question_position` (整數)：題目在測試中的順序，從 1 開始
- `question_time_minutes` (浮點數)：答題時間，單位：分鐘
- `is_correct` (整數)：1 代表正確，0 代表錯誤
- `question_difficulty` (整數或浮點數)：題目難度值
- `question_type` (字串)：例如：'Real', 'DS', 'CR'
- `question_fundamental_skill` (字串)：Q/V 部分需要的核心技能/領域，DI 部分可為空
- `content_domain` (字串)：DI 部分需要的內容領域，例如：'Math Related'，Q/V 部分可為空
- `total_section_time_minutes` (浮點數)：學生在此部分所花費的總時間
- `max_allowed_section_time_minutes` (浮點數)：此部分的標準允許時間，通常為 45.0
- `total_questions_in_section` (整數)：此部分的總題數
- `record_timestamp` (字串)：ISO 8601 格式的時間戳記，表示此記錄添加到 CSV 的時間

### `student_subjective_reports.csv`

- `student_id` (字串)：外鍵，關聯到 `gmat_performance_data.csv`
- `test_instance_id` (字串)：外鍵，關聯到 `gmat_performance_data.csv` 中的特定測試
- `gmat_section` (字串)：'Q', 'DI', 或 'V'
- `subjective_time_pressure` (整數)：1 代表「是，感覺到壓力」，0 代表「否，未感覺到壓力」
- `report_collection_timestamp` (字串)：ISO 8601 格式的時間戳記，表示收集主觀回報的時間

## 使用指南

### 初始化 CSV 檔案

```python
from services.csv_data_service import initialize_csv_files

# 初始化 CSV 檔案（如果不存在）
initialize_csv_files()
```

### 添加 GMAT 表現記錄

```python
from services.csv_data_service import add_gmat_performance_record

# 創建一個包含多個題目記錄的列表
records = [
    {
        "student_id": "student_001",
        "test_instance_id": "student_001_Q_20250508_test1",
        "gmat_section": "Q",
        "test_date": "2025-05-08",
        "question_id": "Q_1_001",
        "question_position": 1,
        "question_time_minutes": 2.5,
        "is_correct": 1,
        "question_difficulty": 3.0,
        "question_type": "PS",
        "question_fundamental_skill": "Algebra",
        "content_domain": "",
        "total_section_time_minutes": 40.0,
        "max_allowed_section_time_minutes": 45.0,
        "total_questions_in_section": 15
    },
    # ... 其他題目記錄 ...
]

# 添加記錄
success = add_gmat_performance_record(records)
```

### 添加主觀回饋記錄

```python
from services.csv_data_service import add_subjective_report_record
import datetime

# 創建一個主觀回饋記錄
report = {
    "student_id": "student_001",
    "test_instance_id": "student_001_Q_20250508_test1",
    "gmat_section": "Q",
    "subjective_time_pressure": 1,  # 1 表示感覺到壓力
    "report_collection_timestamp": datetime.datetime.now().isoformat()
}

# 添加記錄
success = add_subjective_report_record(report)
```

### 查詢數據

```python
from services.csv_data_service import (
    get_all_gmat_performance_records,
    get_student_gmat_performance_records,
    get_test_instance_gmat_performance_records,
    get_student_section_performance_records
)

# 獲取所有表現記錄
all_records = get_all_gmat_performance_records()

# 獲取特定學生的記錄
student_records = get_student_gmat_performance_records("student_001")

# 獲取特定測試實例的記錄
test_records = get_test_instance_gmat_performance_records("student_001_Q_20250508_test1")

# 獲取特定學生在特定部分的記錄
section_records = get_student_section_performance_records("student_001", "Q")
```

### 更新和刪除數據

```python
from services.csv_data_service import (
    update_gmat_performance_records,
    update_subjective_report_record,
    delete_gmat_performance_records,
    delete_subjective_report_record
)

# 更新表現記錄
updates = {"question_difficulty": 3.5}
success = update_gmat_performance_records("student_001_Q_20250508_test1", updates)

# 更新主觀回饋記錄
updates = {"subjective_time_pressure": 0}
success = update_subjective_report_record("student_001_Q_20250508_test1", updates)

# 刪除表現記錄
success = delete_gmat_performance_records("student_001_Q_20250508_test1")

# 刪除主觀回饋記錄
success = delete_subjective_report_record("student_001_Q_20250508_test1")
```

## 數據分析功能

這個服務還提供了強大的數據分析功能，用於理解學生表現。

### 計算學生部分統計數據

```python
from services.csv_data_analysis import calculate_student_section_stats

# 計算特定學生在特定部分的統計數據
stats = calculate_student_section_stats("student_001", "Q")
```

### 分析時間壓力影響

```python
from services.csv_data_analysis import analyze_time_pressure_impact

# 分析時間壓力對學生表現的影響
analysis = analyze_time_pressure_impact("student_001")
```

### 識別學生優勢和弱點

```python
from services.csv_data_analysis import identify_student_strengths_weaknesses

# 識別學生在特定部分的優勢和弱點
analysis = identify_student_strengths_weaknesses("student_001", "Q")
```

### 追蹤隨時間的進步情況

```python
from services.csv_data_analysis import get_progress_over_time

# 追蹤學生在特定部分隨時間的進步情況
progress = get_progress_over_time("student_001", "Q")
```

## 批次處理和導出功能

服務還包括批次處理和數據導出功能。

### 導出學生數據

```python
from services.csv_batch_processor import export_student_data

# 導出特定學生的所有數據
result = export_student_data("student_001", "exports")
```

### 導出所有數據

```python
from services.csv_batch_processor import export_all_data

# 導出系統中的所有數據
result = export_all_data("exports")
```

### 生成綜合學生報告

```python
from services.csv_batch_processor import generate_consolidated_student_report

# 為特定學生生成綜合報告
result = generate_consolidated_student_report(
    "student_001", 
    "exports/student_001_report.json"
)
```

## 示例腳本

查看 `csv_data_example.py` 腳本，了解如何使用這些服務的完整示例。它展示了：

1. 生成樣本數據
2. 數據檢索和查詢
3. 數據分析
4. 數據導出

運行示例腳本：

```bash
python csv_data_example.py
```

## 數據驗證

所有服務都包含嚴格的數據驗證，以確保添加到 CSV 檔案的數據完整性和一致性。各種檢查會驗證：

- 必填欄位是否存在
- 數據類型和格式是否正確
- 值是否在有效範圍內
- 日期和時間格式是否有效 