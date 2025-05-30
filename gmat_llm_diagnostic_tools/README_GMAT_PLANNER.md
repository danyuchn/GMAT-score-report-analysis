# GMAT 讀書計畫自動化規劃系統 使用說明
# GMAT Study Plan Automation System - User Guide

## 📋 系統概述 (System Overview)

本系統根據 `basic-helper.md` 技術文件規格實現，能夠自動化生成個性化的 GMAT 考試週期建議及讀書計畫學習策略。

**🆕 新功能**: 現在支援完全互動式輸入，您可以在終端機中逐步輸入資料！

This system implements the specifications from `basic-helper.md` to automatically generate personalized GMAT study plans and cycle recommendations.

**🆕 New Feature**: Now supports fully interactive input - you can enter data step by step in the terminal!

## 🚀 快速開始 (Quick Start)

### 方式一：互動式輸入 (推薦) - Interactive Input (Recommended)

```bash
# 確保已安裝 Python 3.7+
python --version

# 運行互動式系統
python gmat_study_planner.py
```

系統會逐步引導您輸入以下資訊：
1. 目標 GMAT 分數 (200-805)
2. 分數制度 (Old/New)
3. 目前最高 GMAT 分數
4. 申請截止日期 (YYYY-MM-DD)
5. 語言考試準備狀態
6. 申請資料完成度 (0-100%)
7. 備考身份 (全職考生/在職考生)
8. 平日每日學習時間
9. 假日每日學習時間
10. 各科目目前積分 (60-90)

### 方式二：程式化使用 - Programmatic Usage

```python
from gmat_study_planner import GMATStudyPlanner

# 創建規劃器實例
planner = GMATStudyPlanner()

# 準備輸入數據
input_data = {
    "target_gmat_score": 700,           # 目標GMAT分數
    "target_score_system": "Old",       # "Old" 或 "New" 
    "current_highest_gmat_score": 620,  # 目前最高分數
    "application_deadline": "2025-12-01", # 申請截止日期 (YYYY-MM-DD)
    "language_test_status": "準備中",    # "已完成" 或 "準備中"
    "application_materials_progress": 60, # 申請資料完成度 (0-100%)
    "study_status": "在職考生",          # "全職考生" 或 "在職考生"
    "weekday_study_hours": 3,           # 平日每日學習時數
    "weekend_study_hours": 6,           # 假日每日學習時數
    "current_section_scores": {         # 各科目目前積分 (60-90)
        "Quantitative": 75,
        "Verbal": 70,
        "Data Insights": 72
    }
}

# 生成學習計劃
recommendations = planner.generate_study_plan(input_data)

# 打印結果
planner.print_study_plan(recommendations)
```

### 方式三：演示測試 - Demo Testing

```bash
# 運行自動演示
python demo_interactive_input.py
```

選擇選項 1 進行自動演示，或選項 2 查看手動測試指南。

## 🎯 互動式輸入流程 (Interactive Input Process)

### 輸入步驟詳解

#### 1. 目標分數設定
```
📊 1. 目標 GMAT 分數 (Target GMAT Score)
   範圍: 200-805
   請輸入目標分數: 720
```

#### 2. 分數制度選擇
```
📋 2. 分數制度 (Score System)
   選項: Old (舊制) / New (新制)
   請輸入分數制度 [Old/New]: new
```

#### 3. 當前成績輸入
```
📈 3. 目前最高 GMAT 分數 (Current Highest GMAT Score)
   範圍: 200-805
   請輸入目前最高分數: 650
```

#### 4. 申請時程規劃
```
📅 4. 申請截止日期 (Application Deadline)
   格式: YYYY-MM-DD (例如: 2025-12-01)
   請輸入申請截止日期: 2025-12-01
```

#### 5. 準備狀態評估
```
🌐 5. 語言考試準備狀態 (Language Test Status)
   選項: 已完成 / 準備中
   請輸入語言考試狀態 [已完成/準備中]: 準備中
```

#### 6. 申請進度追蹤
```
📝 6. 申請資料完成度 (Application Materials Progress)
   範圍: 0-100%
   請輸入完成百分比 (0-100): 70
```

#### 7. 學習狀態分類
```
👨‍🎓 7. 備考身份 (Study Status)
   選項: 全職考生 / 在職考生
   請輸入備考身份 [全職考生/在職考生]: 在職考生
```

#### 8-9. 時間資源配置
```
⏰ 8. 平日每日學習時間 (Weekday Study Hours)
   單位: 小時/天
   請輸入平日每天可學習時數: 4

🏖️ 9. 假日每日學習時間 (Weekend Study Hours)
   單位: 小時/天
   請輸入假日每天可學習時數: 8
```

#### 10. 各科目現況評估
```
📚 10. 各科目目前積分 (Current Section Scores)
    範圍: 60-90 分

    10.1 數學 (Quantitative)
    請輸入 Quantitative 目前積分 (60-90): 75

    10.2 語文 (Verbal)
    請輸入 Verbal 目前積分 (60-90): 70

    10.3 數據洞察 (Data Insights)
    請輸入 Data Insights 目前積分 (60-90): 72
```

#### 11. 資料確認
```
============================================================
📋 輸入摘要確認 (Input Summary)
============================================================
目標分數: 720 (New)
目前分數: 650
申請截止: 2025-12-01
語言考試: 準備中
申請資料: 70.0%
備考身份: 在職考生
平日學習: 4.0 小時/天
假日學習: 8.0 小時/天
各科積分:
  Quantitative: 75
  Verbal: 70
  Data Insights: 72

✅ 確認以上資訊正確嗎？[Y/n]: y
```

## ✨ 系統特色功能 (System Features)

### 🔍 智能輸入驗證
- 自動檢查數值範圍
- 日期格式驗證
- 錯誤重新輸入機制
- 中英文輸入支援

### 📄 輸入摘要確認
- 完整參數回顧
- 一鍵確認或重新輸入
- 清晰的數據格式化顯示

### 💾 結果保存功能
- 自動生成時間戳文件名
- JSON 格式完整保存
- 可選擇是否保存

### 🔄 多學生分析
- 連續分析多個學生案例
- 保持程式運行狀態
- 高效批量處理

## 📊 輸入參數說明 (Input Parameters)

| 參數名稱 | 類型 | 範圍/選項 | 說明 |
|---------|------|----------|------|
| `target_gmat_score` | int | 200-805 | 目標GMAT分數 |
| `target_score_system` | str | "Old"/"New" | 目標分數制度 |
| `current_highest_gmat_score` | int | 200-805 | 目前最高GMAT分數 |
| `application_deadline` | str | YYYY-MM-DD | 申請截止日期 |
| `language_test_status` | str | "已完成"/"準備中" | 語言考試準備狀態 |
| `application_materials_progress` | float | 0-100 | 申請資料完成百分比 |
| `study_status` | str | "全職考生"/"在職考生" | 備考身份 |
| `weekday_study_hours` | float | ≥0 | 平日每日可用讀書時間 |
| `weekend_study_hours` | float | ≥0 | 假日每日可用讀書時間 |
| `current_section_scores` | dict | 60-90 | 各科目目前積分 |

## 🎯 核心功能 (Core Functions)

### 1. 分數轉換 (Score Conversion)
- 自動將GMAT舊制分數轉換為新制分數
- 支援完整的官方對照表

### 2. 目標差距分析 (Target Gap Analysis)
- 計算目標與現有分數差距
- 評估所需提升的總積分

### 3. 科目投報率分析 (Subject ROI Analysis)
- 基於百分位斜率計算各科目投報率
- 自動推薦最優時間分配比例

### 4. 時程寬裕度評估 (Schedule Assessment)
- 評估申請截止日期壓力
- 考慮語言考試和申請資料準備時間

### 5. 學習時間評估 (Study Time Assessment)
- 評估每日學習時間充裕度
- 根據全職/在職身份調整標準

### 6. 綜合策略建議 (Comprehensive Strategy)
- 基於多維度分析提供個性化策略
- 包含考試週期和學習方法建議

## 📈 輸出結果說明 (Output Description)

系統會生成包含以下內容的詳細分析報告：

### 分析結果 (Analysis Results)
- 🎯 分數差距分析
- ⏰ 時程寬裕度評估  
- ⏲️ 時間充裕度評估
- 📚 所需積分提升
- 📅 可用準備天數
- 🕒 每週學習時數

### 個性化建議 (Personalized Recommendations)
- 🎓 建議考試週期
- 📖 建議學習策略 
- ⚖️ 建議科目時間分配

## 🔧 進階使用 (Advanced Usage)

### 批量處理多個學生
如需分析多個學生，只需在完成一個分析後，選擇 "是" 繼續分析下一個學生：
```
🔄 是否要為其他學生生成計劃？[Y/n]: y
```

### 保存分析結果
系統會自動生成帶時間戳的文件名：
```
💾 是否要將結果保存到文件？[Y/n]: y
✅ 結果已保存到: gmat_study_plan_20250102_143052.json
```

### 錯誤處理與重新輸入
如果輸入有誤，可以在最終確認階段選擇重新輸入：
```
✅ 確認以上資訊正確嗎？[Y/n]: n
請重新開始輸入...
```

## ⚠️ 注意事項 (Important Notes)

1. **分數範圍**: 所有GMAT分數必須在合理範圍內 (200-805)
2. **日期格式**: 申請截止日期必須使用 YYYY-MM-DD 格式
3. **積分範圍**: 各科目積分必須在 60-90 之間
4. **時間單位**: 學習時間以小時為單位
5. **語言支援**: 系統同時支援中文和英文輸入
6. **中斷操作**: 使用 Ctrl+C 可隨時中斷程式

## 🛠️ 故障排除 (Troubleshooting)

### 常見錯誤 (Common Errors)

#### 1. 輸入驗證失敗
```
錯誤: target_gmat_score must be between 200 and 805
解決: 確保目標分數在有效範圍內
```

#### 2. 日期格式錯誤
```
錯誤: Invalid date format
解決: 使用 YYYY-MM-DD 格式，例如 "2025-12-01"
```

#### 3. 科目分數超範圍
```
錯誤: Invalid Quantitative score: 95. Must be between 60-90
解決: 確保所有科目積分在 60-90 範圍內
```

#### 4. 程式中斷
```
❌ 程序被用戶中斷
解決: 重新運行程式即可
```

### 系統限制 (System Limitations)

1. 本系統基於統計模型，不能替代個人化教學諮詢
2. 邊界情況（如分數下降、目標變更）需要人工介入
3. 建議定期更新個人進度並重新生成計劃

## 📞 技術支援 (Technical Support)

如需技術支援或功能擴展，請：
1. 檢查輸入參數是否符合規格
2. 查看錯誤訊息並對照故障排除指南
3. 使用演示腳本測試系統功能
4. 聯繫教學顧問進行個性化討論

## 📁 相關檔案 (Related Files)

- `gmat_study_planner.py` - 主程式 (互動式版本)
- `demo_interactive_input.py` - 演示測試腳本
- `test_gmat_scenarios.py` - 多情境測試腳本
- `IMPLEMENTATION_SUMMARY.md` - 完整實施總結

---

**版本**: 2.0 (Interactive Version)  
**最後更新**: 2025年1月  
**新增功能**: 完全互動式輸入界面  
**基於文件**: basic-helper.md 技術規格 