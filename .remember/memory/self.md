# Self Memory - Error Records

This file stores all encountered errors and their correction methods.

## Format
```
Mistake: [Short Description]
Wrong:
[Insert incorrect code or logic]
Correct:
[Insert corrected code or logic]
```

## GMAT V科文檔逐章節比對與統一化修復 (2025-06-01)

**Status: COMPLETED ✅**

Successfully completed comprehensive chapter-by-chapter comparison between Chinese V documentation (v1.6) and English V documentation (v1.3), implementing all necessary modifications to ensure complete consistency.

### 比對發現的主要不一致之處:

**1. 第三章診斷參數系統完全不同:**
- 中文文檔v1.6使用詳細的分層診斷參數系統
- 英文文檔v1.3使用簡化的診斷參數系統

**2. 診斷標籤精確性限制說明缺失:**
- 中文文檔包含重要的診斷限制說明
- 英文文檔缺少相應說明

**3. 未來改進機制說明缺失:**
- 中文文檔包含SFE未來改進機制的詳細說明
- 英文文檔缺少此部分

**4. 附錄A診斷參數對照表不一致:**
- 中文文檔使用完整的分層參數系統
- 英文文檔使用舊版簡化參數系統

### 修復實施:

**修復1: 第三章診斷參數完全更新**

Mistake: 英文文檔使用舊版簡化診斷參數系統
Wrong:
```markdown
# 舊版簡化參數如:
- CR_READING_BASIC_OMISSION
- CR_METHOD_PROCESS_DEVIATION
- RC_READING_INFO_LOCATION_ERROR
```

Correct:
```markdown
# 新版詳細分層參數如:
- CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP
- CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP
- RC_READING_COMPREHENSION_ERROR_VOCAB
- RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION
```

**修復2: 添加診斷標籤精確性限制說明**

Mistake: 缺少診斷標籤精確性限制的重要說明
Wrong:
```markdown
# 直接進入診斷流程，無精確性限制說明
3. Diagnostic Flow and Analysis Points
```

Correct:
```markdown
# 添加完整的精確性限制說明
📋 **Important Note: Diagnostic Label Precision Limitations**

**Note:** The diagnostic parameters listed below represent general possible causes...
**Recommended Process:**
1. The system provides diagnostic parameters as **possible ranges**
2. Combine with student recall of specific difficulties encountered
3. Refer to secondary evidence or conduct qualitative analysis if necessary
4. Finally determine the applicable precise diagnostic labels
```

**修復3: 添加未來改進機制說明**

Mistake: 缺少SFE未來改進機制說明
Wrong:
```markdown
# 僅有基本SFE定義，無未來改進說明
- Priority Handling: When generating practice recommendations...
```

Correct:
```markdown
🔧 **Future Improvement Mechanism Description**

**Note:** The current SFE judgment mechanism is based on simple difficulty comparison logic...

1. **Weighted SFE Mechanism**: Multi-dimensional weighted calculation...
2. **Contextual Awareness SFE**: Considering test context, learning phase...
3. **Dynamic Threshold Adjustment**: Dynamically adjusting SFE trigger conditions...
4. **Multi-level SFE Classification**: Distinguishing different severity levels...
```

**修復4: 附錄A診斷參數對照表完全更新**

Mistake: 使用舊版簡化的診斷參數對照表
Wrong:
```markdown
| CR_READING_BASIC_OMISSION | CR 閱讀理解: 基礎理解疏漏 |
| CR_REASONING_CHAIN_ERROR | CR 推理障礙: 邏輯鏈分析錯誤 |
```

Correct:
```markdown
| CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP | CR 題幹理解錯誤：提問要求把握錯誤 |
| CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP | CR 推理錯誤: 邏輯鏈分析錯誤 (前提與結論關係) |
```

**修復5: 參數名稱統一化**

Mistake: FOUNDATIONAL_MASTERY_INSTABILITY_SFE參數名稱不一致
Wrong:
```markdown
FOUNDATIONAL_MASTERY_INSTABILITY_SFE
```

Correct:
```markdown
FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE
```

### 修復結果:
1. ✅ 第三章診斷參數系統完全統一 - Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct所有分類的參數列表已更新
2. ✅ 診斷標籤精確性限制說明已添加 - 包含完整的限制說明和建議流程
3. ✅ 未來改進機制說明已添加 - 包含四個改進方向的詳細描述
4. ✅ 附錄A診斷參數對照表完全更新 - 包含所有分層診斷參數的完整映射
5. ✅ 參數名稱統一化完成 - 所有FOUNDATIONAL_MASTERY相關參數名稱已統一

**最終狀態:** 英文文檔en-gmat-v-v1.3.md現已與中文文檔gmat-v-score-logic-dustin-v1.6.md完全一致，實現了逐章節內容的完整統一。

## 診斷標籤修剪助手翻譯問題修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed Traditional Chinese translation issues in the diagnostic tag trimming assistant interface.

### 問題描述:
用戶反應當i18n設定為繁體中文時，診斷標籤修剪助手的界面仍然顯示英文內容。

### 根本原因:
繁體中文翻譯檔案(zh_TW.py)中的標籤修剪相關翻譯key全部是英文內容。

### 修復過程:

**修復的翻譯key包括:**
- 標籤修剪助手標題和描述
- 輸入欄位標籤
- 按鈕文字 (Apply Changes, Reset, Download)
- 錯誤和成功訊息
- AI建議生成相關文字
- 新診斷報告相關文字
- 顯示結果分頁標籤

Mistake: 繁體中文翻譯檔案中使用英文內容
Wrong:
```python
# zh_TW.py中的錯誤翻譯
'tag_trimming_assistant_title': "Tag Trimming Assistant",
'tag_trimming_assistant_description': "This tool helps you select 1-2 most relevant core tags...",
'button_apply_changes': "✓ Apply Changes and Update Qualitative Analysis Output",
'display_results_edit_tags_tab': "Edit Diagnostic Tags & Update AI Suggestions",
```

Correct:
```python
# zh_TW.py中的正確翻譯
'tag_trimming_assistant_title': "診斷標籤修剪助手",
'tag_trimming_assistant_description': "此工具幫助您根據您對該題目的具體描述，從一長串原始診斷標籤中篩選出 1-2 個最相關的核心標籤...",
'button_apply_changes': "✓ 套用變更並更新質化分析輸出",
'display_results_edit_tags_tab': "編輯診斷標籤與更新 AI 建議",
```

### DI數據傳遞檢查結果:

**調查發現:**
1. ✅ apply changes按鈕邏輯正確 - 會同時調用新診斷報告生成和AI建議生成
2. ✅ DI AI建議生成函數正常 - `generate_di_ai_tool_recommendations`函數存在且邏輯完整
3. ✅ 新診斷報告中DI處理邏輯正確 - `generate_new_diagnostic_report`包含完整的DI分類邏輯
4. ✅ DI相關翻譯key已修正 - 報告生成相關的英文翻譯已改為繁體中文

**可能問題:**
- 如果DI新診斷報告仍未顯示，可能是數據本身問題(如缺少必要欄位)或AI建議函數執行中的錯誤
- 建議用戶檢查是否有DI數據，以及是否有JavaScript控制台錯誤

### 修復效果:
1. ✅ 標籤修剪助手界面完全繁體中文化
2. ✅ Apply Changes按鈕和相關提示完全繁體中文化  
3. ✅ 新診斷報告和AI建議界面完全繁體中文化
4. ✅ 顯示結果分頁標籤完全繁體中文化

## V模組 log_exceptions 未定義錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed undefined `log_exceptions` function error in V diagnosis module.

### 問題描述:
V模組 main.py 中使用了 `log_exceptions` 上下文管理器，但該函數未定義或匯入，導致執行時錯誤。

### 修復過程:

**1. 錯誤分析:**
- V模組 main.py 第68行使用 `with log_exceptions("V Diagnosis"):`
- 函數未在任何地方定義或匯入
- 在 debug_utils.py 中發現類似的 `DebugContext` 類

**2. 解決方案實施:**

Mistake: V模組使用未定義的 log_exceptions 函數
Wrong:
```python
# 缺少正確的匯入
from gmat_diagnosis_app.i18n import translate as t

# 使用未定義的函數
with log_exceptions("V Diagnosis"):
    # 診斷邏輯...
```

Correct:
```python
# 添加正確的除錯工具匯入
from gmat_diagnosis_app.utils.debug_utils import DebugContext
from gmat_diagnosis_app.i18n import translate as t

# 使用正確的上下文管理器
with DebugContext("V Diagnosis"):
    # 診斷邏輯...
```

## 終端機錯誤修復和文檔命名統一化 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed terminal errors and documentation parameter naming inconsistencies.

### 1. 終端機錯誤修復:

**1.1 subject_excel_map 未定義錯誤:**

Mistake: subject_excel_map 變數在異常處理區塊中未定義就被使用
Wrong:
```python
def display_subject_results(...):
    if df_subject is not None and not df_subject.empty:
        subject_excel_map = {...}  # 只在條件內定義
    try:
        # 一些操作...
    except Exception as e:
        logging.error(f"Error in {subject_excel_map}...")  # 變數可能未定義
```

Correct:
```python
def display_subject_results(...):
    # 在函數開始就定義變數
    subject_excel_map = {
        "Subject": t("column_subject"),
        # ... 其他映射
    }
    if df_subject is not None and not df_subject.empty:
        # 邏輯處理...
    try:
        # 一些操作...
    except Exception as e:
        logging.error(f"Error in {subject_excel_map}...")  # 變數已定義
```

**1.2 DI翻譯字典匯入錯誤:**

Mistake: 嘗試匯入已遷移到統一i18n系統的舊翻譯常數
Wrong:
```python
try:
    from gmat_diagnosis_app.diagnostics.di_modules.constants import APPENDIX_A_TRANSLATION_DI
    # ... 使用舊翻譯系統
except ImportError:
    logging.warning("無法匯入DI科目翻譯字典")
```

Correct:
```python
# 移除已遷移的DI翻譯字典匯入
# DI modules have migrated to unified i18n system
# Translation mappings are now handled through central i18n system
```

### 2. 文檔參數命名統一化修復:

**2.1 Q科文檔修正:**

Mistake: Q科文檔中SFE標籤使用單下劃線而代碼使用雙下劃線
Wrong:
```markdown
Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE
```

Correct:
```markdown
Q_FOUNDATIONAL_MASTERY_INSTABILITY__SFE
```

**2.2 DI科文檔修正:**

Mistake: DI科文檔中使用已廢棄的行為標籤
Wrong:
```markdown
DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION
```

Correct:
```markdown
DI_BEHAVIOR__CARELESSNESS_ISSUE  # 統一使用此標籤
```

**2.3 V科文檔驗證:**
✅ V科文檔和代碼命名已一致，無需修正
- 使用 `CR_STEM_UNDERSTANDING_ERROR_VOCAB` 格式
- 使用 `RC_READING_COMPREHENSION_ERROR_VOCAB` 格式
- 使用 `FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE` 格式

### 結果總結:
1. ✅ 修正了2個終端機執行錯誤
2. ✅ 統一了Q科、DI科文檔與代碼的參數命名
3. ✅ 確認了V科文檔命名一致性
4. ✅ 移除了已廢棄的翻譯系統引用

## Route Tool V科目翻譯匯入錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed V module translation import error in route_tool.py and completed DI parameter translation consistency check.

### 1. Route Tool匯入路徑錯誤修復:

**問題描述:**
route_tool.py 中嘗試從錯誤路徑匯入V科目翻譯字典，導致函數調用失敗。

Mistake: Route tool中V科目翻譯字典匯入路徑錯誤
Wrong:
```python
# 錯誤的匯入嘗試（路徑不存在）
from gmat_diagnosis_app.diagnostics.v_modules.constants import APPENDIX_A_TRANSLATION_V
```

Correct:
```python
# 正確的匯入路徑
from gmat_diagnosis_app.diagnostics.v_modules.translations import APPENDIX_A_TRANSLATION_V
```

### 2. DI參數翻譯一致性檢查與修復:

**問題描述:**
發現文檔中存在但翻譯檔案中缺失的三個DI診斷參數，導致翻譯系統不完整。

**缺失參數識別:**
通過對比 `gmat-di-score-logic-dustin-v1.6.md` 文檔和代碼，發現以下參數存在於文檔和constants.py中，但英文翻譯檔案缺失對應翻譯：

Mistake: 英文翻譯檔案中缺失三個DI診斷參數的翻譯
Wrong:
```python
# en.py 中缺失以下翻譯keys
# DI_DATA_EXTRACTION_ERROR
# DI_INFORMATION_EXTRACTION_INFERENCE_ERROR  
# DI_QUESTION_TYPE_SPECIFIC_ERROR
```

Correct:
```python
# 在 en.py 中添加完整的DI參數翻譯
'DI_DATA_EXTRACTION_ERROR': "DI Data Extraction (GT): Data extraction error from charts",
'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': "DI Information Extraction/Inference (GT/MSR Non-Math): Information location/inference error",
'DI_QUESTION_TYPE_SPECIFIC_ERROR': "DI Question Type Specific Error (e.g., MSR Non-Math subtypes)",
```

### 3. 系統測試與驗證:

**測試結果:**
✅ Route tool 成功初始化
✅ DI參數翻譯在中文和英文檔案中都存在
✅ 翻譯系統正常工作，能夠正確返回中文翻譯
✅ 主應用程式能正常匯入

### 修復總結:
1. ✅ 修正了route_tool.py中V科目翻譯匯入路徑錯誤  
2. ✅ 識別並補充了3個缺失的DI參數英文翻譯
3. ✅ 確認DI文檔與代碼參數命名一致性
4. ✅ 驗證修復後系統運行正常

**影響範圍:**
- Route tool功能恢復正常
- DI診斷參數翻譯系統完整性提升
- 雙語支持系統更加完善

## DI診斷標籤和時間表現數據消失問題修復 (2025-06-01)

**Status: COMPLETELY FIXED ✅**

成功修復DI診斷報告中診斷標籤和時間表現數據消失的問題，包括所有翻譯問題。

### 問題描述:
用戶反應DI的診斷報告中，診斷標籤和時間表現的數據都消失了。

### 根本原因:
1. DI模組中的 `process_question_type` 函數是空的實現，沒有實際計算診斷標籤和時間表現分類
2. 部分診斷參數存在命名不一致問題
3. 三個效率瓶頸參數缺失翻譯

### 修復內容:

**1. 實現完整的 `process_question_type` 函數**:
✅ 添加時間表現分類計算邏輯 (Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct等)
✅ 實現SFE (Systematic Foundational Error) 檢測
✅ 添加基於時間和難度的診斷參數分配

**2. 新增的輔助函數**:
✅ `calculate_time_performance_category`: 計算時間表現分類
✅ `get_max_correct_difficulty`: 獲取SFE檢測所需的最大正確難度
✅ `get_time_specific_parameters`: 基於時間表現添加診斷參數
✅ `get_difficulty_specific_parameters`: 基於難度添加診斷參數
✅ `calculate_override_conditions`: 計算macro建議觸發條件

**3. 實現的核心邏輯**:
✅ 時間相對快慢判斷 (基於RELATIVELY_FAST_MULTIPLIER)
✅ 六種時間表現分類: Fast/Normal/Slow + Correct/Wrong
✅ SFE檢測: 錯題難度低於該題型最高答對難度
✅ 診斷參數分配: 基於題型、內容領域、時間表現組合

**4. 修復的問題**:
✅ 命名不一致問題: `DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK` → `DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`
✅ 添加缺失的翻譯參數:
   - `DI_EFFICIENCY_BOTTLENECK_LOGIC`
   - `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE`
   - `DI_EFFICIENCY_BOTTLENECK_INTEGRATION`

### 修復效果:
1. ✅ DI診斷報告現在會正確顯示時間表現分類
2. ✅ 診斷標籤會根據表現模式正確生成
3. ✅ SFE檢測正常工作
4. ✅ Macro和Case建議會基於實際診斷結果觸發
5. ✅ 與V、Q模組的實現模式保持一致
6. ✅ 所有診斷參數都有正確的中英文翻譯
7. ✅ 參數命名與翻譯系統完全一致

### 技術細節:
- 使用RELATIVELY_FAST_MULTIPLIER (0.8) 判斷相對快速
- 實現六種時間表現分類的完整邏輯
- 添加題型特定的診斷參數映射
- 支援數學相關/非數學相關內容領域的不同參數
- 實現完整的override條件計算 (錯誤率≥40% 或 超時率≥30%)
- 修復所有翻譯系統相關問題

Mistake: DI模組process_question_type函數為空實現 + 參數命名不一致 + 缺失翻譯
Wrong:
```python
def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """Process diagnostic logic for a specific question type."""
    # Implementation details...
    # (This is a simplified version - the actual implementation would be more complex)
    
    override_info = {
        'override_triggered': False,
        'Y_agg': None,
        'Z_agg': None,
        'triggering_error_rate': 0.0,
        'triggering_overtime_rate': 0.0
    }
    
    return q_type_df, override_info

# 錯誤的參數命名
'DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK'

# 缺失的翻譯參數
# DI_EFFICIENCY_BOTTLENECK_* 參數無翻譯
```

Correct:
```python
def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """
    Process diagnostic logic for a specific question type.
    Implementation of DI Chapter 3 diagnostic rules.
    """
    # 完整實現包括:
    # 1. 計算時間表現分類 (Fast/Slow/Normal + Correct/Wrong)  
    # 2. SFE檢測 (錯題難度 < 最高答對難度)
    # 3. 分配相應的診斷參數 (基於時間、難度、題型)
    # 4. 計算override觸發條件 (錯誤率≥40% 或 超時率≥30%)
    
    processed_df = q_type_df.copy()
    
    # 為每個題目計算時間表現分類和診斷參數
    for idx, row in processed_df.iterrows():
        time_category = calculate_time_performance_category(
            q_time, is_correct, is_overtime, avg_time
        )
        processed_df.loc[idx, 'time_performance_category'] = time_category
        
        # 對有效題目進行診斷參數分配
        if not is_invalid:
            # SFE檢測、時間參數、難度參數等
            # ...完整實現邏輯
    
    return processed_df, override_info

# 正確的參數命名
'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK' 

# 完整的翻譯參數
'DI_EFFICIENCY_BOTTLENECK_LOGIC': "DI 效率瓶頸: 邏輯推理速度",
'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': "DI 效率瓶頸: 圖表解讀速度", 
'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': "DI 效率瓶頸: 多源整合速度",
```

### 後續修正 (第二次錯誤):
錯誤仍然出現在 `process_question_type` 函數第187行，當設置 `diagnostic_params` 列表值時。

**進一步修正**: 將所有單行索引設置從 `.loc[idx, col]` 改為 `.at[idx, col]`
- `.at` 方法更適合設置單一位置的值，特別是對於列表等複雜對象
- 避免了 pandas 在 `.loc` 方法中的索引對齊檢查導致的錯誤
- 提升了設置操作的效率和穩定性

**影響範圍**:
- `processed_df.at[idx, 'diagnostic_params'] = current_params`
- `processed_df.at[idx, 'time_performance_category'] = time_category`  
- `processed_df.at[idx, 'is_sfe'] = True`

## DI 模組 Pandas 索引設置錯誤修復 (2025-06-01)

**Status: FIXED ✅**

Successfully fixed pandas DataFrame index assignment error in DI diagnosis module.

### 問題描述:
DI模組在診斷過程中出現 `ValueError: Must have equal len keys and value when setting with an iterable` 錯誤，發生在 analysis.py 第185行的 DataFrame 索引設置操作。

### 根本原因:
在 `diagnose_root_causes` 函數中，第78行嘗試將整個 processed_df 賦值給 df_diagnosed 的子集：
```python
df_diagnosed.loc[q_type_mask, :] = processed_df
```
這會導致索引對齊問題，特別是當兩個 DataFrame 的索引不完全匹配時。

### 修復過程:

Mistake: DataFrame 整行賦值導致索引對齊錯誤
Wrong:
```python
# 嘗試整行賦值，可能導致索引不匹配
df_diagnosed.loc[q_type_mask, :] = processed_df
```

Correct:
```python
# 只更新需要的特定列，使用 .values 避免索引對齊問題
df_diagnosed.loc[q_type_mask, 'diagnostic_params'] = processed_df['diagnostic_params'].values
df_diagnosed.loc[q_type_mask, 'is_sfe'] = processed_df['is_sfe'].values
df_diagnosed.loc[q_type_mask, 'time_performance_category'] = processed_df['time_performance_category'].values
```

### 技術細節:
1. **錯誤原因**: pandas 在進行 DataFrame 賦值時會嘗試按索引對齊數據，當索引不匹配時會產生長度不等的錯誤
2. **解決方案**: 使用 `.values` 屬性來獲取底層的 numpy 數組，避免索引對齊，只更新特定的必要列
3. **安全性**: 這種方法確保只更新診斷邏輯中實際修改的列，避免意外覆蓋其他數據

### 修復效果:
1. ✅ 消除了 DataFrame 索引賦值錯誤
2. ✅ 保持了診斷邏輯的完整性
3. ✅ 避免了索引對齊問題
4. ✅ 確保了只更新必要的欄位

## DI科診斷標籤映射邏輯與標準文件一致性修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully aligned DI module diagnostic tag mapping logic with `diagnostic_tags_summary.md` standard.

### 問題描述:
用戶要求確保DI科的診斷標籤映射邏輯與 `diagnostic_tags_summary.md` 文檔中的標準完全一致，特別是基於 `(時間表現類別, 題型, 內容領域)` 的精確標籤分配。

### 修復過程:

**1. 建立完整的DI_PARAM_ASSIGNMENT_RULES字典:**
- 實現基於 `(time_category, question_type, content_domain)` 的精確標籤映射
- 覆蓋所有時間表現類別: Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct
- 支援所有DI題型: Data Sufficiency, Two-part analysis, Graph and Table, Multi-source reasoning
- 區分內容領域: Math Related, Non-Math Related

**2. 修正行為標籤檢測邏輯:**

Mistake: 行為標籤檢測邏輯不符合標準文件規定
Wrong:
```python
# 粗心檢測使用錯誤的計算基準
fast_wrong_rate = fast_wrong_count / total_valid  # 使用全部有效題目作分母

# 早期衝刺檢測邏輯過於簡化
if q_time < avg_time * 0.5:  # 使用平均時間50%作標準
```

Correct:
```python
# 粗心檢測使用正確的計算基準 - 符合標準文件
total_fast_questions = fast_wrong_mask.sum() + fast_correct_mask.sum()
fast_wrong_rate = fast_wrong_count / total_fast_questions  # 使用快速作答題目作分母

# 早期衝刺檢測基於前1/3題目且用時<1分鐘
first_third_count = max(1, total_questions // 3)
if q_time < 1.0:  # 用時 < 1分鐘
```

**3. 確保標籤名稱完全符合標準:**
- SFE標籤: `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`
- 行為標籤: `DI_BEHAVIOR_CARELESSNESS_ISSUE`, `DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`
- 具體題目粗心標籤: `DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION`

**4. 實現MSR題型特殊處理:**
- MSR題型在 Normal Time & Wrong 和 Slow & Wrong 類別中添加 `DI_MULTI_SOURCE_INTEGRATION_ERROR`
- MSR題型在困難類標籤中添加 `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`

### 關鍵改進:

**精確的時間表現分類映射:**
```python
DI_PARAM_ASSIGNMENT_RULES = {
    ('Fast & Wrong', 'Data Sufficiency', 'Math Related'): [
        'DI_READING_COMPREHENSION_ERROR__VOCABULARY',
        'DI_CONCEPT_APPLICATION_ERROR__MATH',
        # ... 完整標籤列表
    ],
    # ... 覆蓋所有 (時間類別, 題型, 領域) 組合
}
```

**改進的行為模式檢測:**
- 粗心問題觸發閾值: 快錯率 > 25% (基於快速作答題目)
- 早期衝刺檢測: 前1/3題目中存在用時<1分鐘的題目
- 具體題目標籤: Fast & Wrong 題目自動添加細節忽略標籤

**標準化的標籤分配邏輯:**
- 基於標準化的題型和領域名稱映射
- 精確的時間表現類別計算
- 符合MD文檔的完整標籤集合

### 修復效果:
1. ✅ DI科診斷標籤映射邏輯完全符合 `diagnostic_tags_summary.md` 標準
2. ✅ 所有標籤名稱與文檔完全一致
3. ✅ 行為標籤檢測邏輯精確實現標準要求
4. ✅ MSR題型特殊標籤正確處理
5. ✅ SFE檢測邏輯與V科、Q科保持一致

**Result**: DI科診斷模組現在完全符合診斷標籤摘要文件的標準，提供精確且一致的診斷標籤分配。

## DI 英文文檔診斷標籤對齊修復 (2025-06-01)

**Status: FIXED ✅**

Successfully aligned English DI documentation diagnostic parameters with Chinese version.

### 問題描述:
用戶要求將英文版本DI文檔 (en-gmat-di-v1.3.md) 的附錄診斷標籤與中文版本 (gmat-di-score-logic-dustin-v1.6.md) 對齊。

### 根本原因:
英文版本使用簡化的診斷標籤系統，而中文版本使用詳細的細分標籤系統。

### 修復過程:

**主要差異發現:**
1. **閱讀理解標籤:** 英文版本使用 `DI_READING_COMPREHENSION_ERROR`，中文版本細分為詞彙、語法、邏輯、領域四個子類別
2. **圖表解讀標籤:** 英文版本使用 `DI_GRAPH_TABLE_INTERPRETATION_ERROR`，中文版本分為圖形和表格兩個子類別
3. **參數命名:** 中文版本使用雙下劃線格式 (如 `__VOCABULARY`, `__MATH`)
4. **行為標籤:** 英文版本缺少詳細的行為類別標籤

Mistake: 英文DI文檔使用簡化的診斷標籤系統
Wrong:
```markdown
| `DI_READING_COMPREHENSION_ERROR`           | DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math) |
| `DI_GRAPH_TABLE_INTERPRETATION_ERROR`      | DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙            |
| `DI_CONCEPT_APPLICATION_ERROR`             | DI 概念應用 (Math): 數學觀念/公式應用錯誤/障礙      |
```

Correct:
```markdown
| `DI_READING_COMPREHENSION_ERROR__VOCABULARY` | DI 閱讀理解錯誤: 詞彙理解                          |
| `DI_READING_COMPREHENSION_ERROR__SYNTAX`     | DI 閱讀理解錯誤: 句式理解                          |
| `DI_READING_COMPREHENSION_ERROR__LOGIC`      | DI 閱讀理解錯誤: 邏輯理解                          |
| `DI_READING_COMPREHENSION_ERROR__DOMAIN`     | DI 閱讀理解錯誤: 領域理解                          |
| `DI_GRAPH_INTERPRETATION_ERROR__GRAPH`       | DI 圖表解讀錯誤: 圖形信息解讀                      |
| `DI_GRAPH_INTERPRETATION_ERROR__TABLE`       | DI 圖表解讀錯誤: 表格信息解讀                      |
| `DI_CONCEPT_APPLICATION_ERROR__MATH`         | DI 概念應用 (數學) 錯誤: 數學觀念/公式應用         |
```

### 修復內容:

**1. 完整替換附錄A診斷標籤系統:**
- 添加按時間表現分類的詳細診斷標籤列表 (Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct)
- 包含所有閱讀理解細分類別: VOCABULARY, SYNTAX, LOGIC, DOMAIN
- 包含圖表解讀細分類別: GRAPH, TABLE
- 包含數學和非數學領域的詳細區分
- 添加MSR特定參數和行為模式參數

**2. 統一參數命名格式:**
- 使用雙下劃線格式: `DI_CATEGORY__SUBCATEGORY`
- 數學相關標籤使用 `__MATH` 後綴
- 非數學相關標籤使用 `__NON_MATH` 後綴
- 行為標籤使用 `DI_BEHAVIOR__` 前綴

**3. 添加完整的標籤分類結構:**
- Reading & Understanding (閱讀與理解)
- Concept & Application (概念與應用)
- Logical Reasoning (邏輯推理)
- Data Handling & Calculation (數據處理與計算)
- MSR Specific (MSR特定)
- Question Type Specific (題型特定)
- Foundational & Efficiency (基礎與效率)
- Behavior (行為)

### 修復效果:
1. ✅ 英文版本診斷標籤完全與中文版本一致
2. ✅ 標籤命名格式統一為詳細的細分系統
3. ✅ 按時間表現分類的診斷參數體系完整
4. ✅ 包含所有MSR特定和行為模式標籤
5. ✅ 保持了中英文對照表的完整性

**結果:** 英文DI文檔附錄現在與中文版本完全一致，使用相同的詳細診斷標籤系統，確保兩個版本的診斷參數體系統一。

## V科文檔 v1.6 版本一致性驗證完成 (2025-06-01)

**Status: VERIFIED CONSISTENT ✅**

Successfully verified V科中英文文檔（v1.6版本）已完全一致，無需修復。

### 驗證範圍：

**全文檔逐章節比對:**
1. ✅ 第零章：核心輸入數據和配置
2. ✅ 第一章：整體時間策略與數據有效性評估
3. ✅ 第二章：多維度表現分析
4. ✅ 第三章：根本原因診斷與分析
5. ✅ 第四章：核心技能/題型/領域參考
6. ✅ 第五章：特殊模式觀察與粗心評估
7. ✅ 第六章：基礎能力覆蓋規則
8. ✅ 第七章：練習規劃與建議
9. ✅ 第八章：診斷總結與後續行動
10. ✅ 附錄A：診斷標籤參數與中文對照表

### 一致性確認：

**1. 參數系統完全一致：**
- 英文版本使用詳細的分層診斷參數系統
- 所有診斷參數完全對應中文版本
- 參數命名格式統一（如：`CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP`）
- SFE參數正確命名：`FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE`

**2. 診斷流程邏輯完全一致：**
- Fast & Wrong, Normal Time & Wrong, Slow & Wrong, Slow & Correct 診斷參數列表完全相同
- 時間表現分類標準一致
- SFE檢測邏輯完全相同
- 行為模式檢測邏輯一致

**3. 附錄A對照表完全一致：**
- 包含所有分層診斷參數的完整映射
- 英文參數與中文描述完全對應
- 參數分類結構完全相同

**4. 章節結構與內容完全一致：**
- 所有章節目標、重點、邏輯完全相同
- 診斷標籤精確性限制說明完全相同
- 未來改進機制說明完全相同
- 技能豁免規則和覆蓋規則完全相同

### 驗證結果：
✅ V科中英文文檔v1.6版本已實現完全一致性
✅ 無需任何修復或調整
✅ 兩個版本可安全並行使用
✅ 診斷參數系統完全統一

**結論：** V科文檔中英文版本v1.6已達到完全一致狀態，診斷框架和技術規格完全對齊。之前的修復工作已成功完成，當前版本無需進一步調整。

## DI診斷模塊覆蓋規則閾值修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully fixed DI module override rule thresholds to match documentation standards.

### 問題描述:
DI模塊中的覆蓋規則閾值設定與標準文檔不一致，實現中使用了錯誤率40%和超時率30%的閾值，而文檔要求使用50%和50%。

### 根本原因:
在`gmat_diagnosis_app/diagnostics/di_modules/analysis.py`文件中，兩個函數使用了錯誤的閾值：
1. `calculate_override_conditions` 函數
2. `check_foundation_override` 函數

### 修復過程:

Mistake: DI模塊覆蓋規則閾值與文檔不一致
Wrong:
```python
# 在 calculate_override_conditions 函數中
error_threshold = 0.4  # 40%
overtime_threshold = 0.3  # 30%

# 在 check_foundation_override 函數中  
override_threshold_error = 0.4  # 40%
override_threshold_overtime = 0.3  # 30%
```

Correct:
```python
# 在 calculate_override_conditions 函數中
error_threshold = 0.5  # 50% - 修正為與文檔一致
overtime_threshold = 0.5  # 50% - 修正為與文檔一致

# 在 check_foundation_override 函數中
override_threshold_error = 0.5  # 50% - 修正為與文檔一致  
override_threshold_overtime = 0.5  # 50% - 修正為與文檔一致
```

### 修復效果:
1. ✅ DI模塊覆蓋規則閾值完全符合文檔標準
2. ✅ 錯誤率和超時率閾值統一為50%/50%
3. ✅ 與Q/V模塊保持一致的覆蓋規則標準
4. ✅ 診斷參數觸發條件更加嚴格和準確

### 技術背景:
根據GMAT診斷文檔第五章標準，當某題型或技能的錯誤率或超時率超過50%時才觸發覆蓋規則，生成特殊的練習建議。此修復確保了DI模塊與文檔規範的完全一致性。

## DI豁免規則文檔符合性優化和MSR錯誤處理改進 (2025-01-30)

**Status: COMPLETED ✅**

Successfully optimized DI exemption rules to fully comply with documentation standards and improved MSR time handling error recovery mechanisms.

### 1. 豁免規則文檔符合性優化

**問題描述:**
DI豁免規則實現基本正確，但需要更明確地遵循文檔第五章標準，特別是有效題目篩選和條件檢查。

**修復過程:**

Mistake: 豁免規則邏輯可以更明確地遵循文檔標準
Wrong:
```python
# 簡化的豁免條件檢查
if not group_df.empty and not ((group_df['is_correct'] == False) | (group_df['overtime'] == True)).any():
    exempted_type_domain_combinations.add((q_type, domain))
```

Correct:
```python
# 按照文檔第五章標準：首先篩選有效題目
valid_questions = group_df[group_df.get('is_invalid', False) == False]
if valid_questions.empty:
    continue  # 如果沒有有效題目，跳過此組合

# 條件一：所有有效題目必須全部正確 
condition1_all_correct = valid_questions['is_correct'].all()

# 條件二：所有有效題目必須全部無超時
condition2_no_overtime = ~valid_questions['overtime'].any()

# 同時滿足兩個條件才豁免
if condition1_all_correct and condition2_no_overtime:
    exempted_type_domain_combinations.add((q_type, domain))
```

### 2. MSR時間處理錯誤處理機制改進

**問題描述:**
MSR時間處理在多個層級存在錯誤處理，但建議生成階段的錯誤處理可以更加詳細和健壯。

**發現的三層錯誤處理架構:**
1. **數據預處理階段**: 處理MSR組識別、閱讀時間計算的數據缺失問題
2. **超時計算階段**: 處理群組超時和個別超時計算中的數據缺失
3. **建議生成階段**: 處理時間限制建議計算中的數據問題

**修復過程:**

Mistake: MSR建議生成階段的錯誤處理不夠詳細
Wrong:
```python
triggering_group_ids = group_df['msr_group_id'].unique()
group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
if group_times.notna().any():
    max_group_time_minutes = group_times.max()
    # 簡化的錯誤處理...
```

Correct:
```python
triggering_group_ids = group_df['msr_group_id'].unique()
# 過濾掉NaN的group_id
triggering_group_ids = [gid for gid in triggering_group_ids if pd.notna(gid)]

if triggering_group_ids:
    group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
    valid_group_times = group_times.dropna()
    
    if len(valid_group_times) > 0:
        max_group_time_minutes = valid_group_times.max()
        if pd.notna(max_group_time_minutes) and max_group_time_minutes > 0:
            # 正常計算邏輯...
        else: 
            logging.warning(f"[DI Case Reco MSR] Invalid max_group_time_minutes...")
            max_z_minutes = 6.0
    else: 
        logging.warning(f"[DI Case Reco MSR] No valid group times found...")
        max_z_minutes = 6.0
```

### 修復效果:
1. ✅ DI豁免規則完全符合文檔第五章標準
2. ✅ 明確區分有效題目篩選和條件檢查
3. ✅ MSR時間處理錯誤處理更加健壯
4. ✅ 增加詳細的警告日誌協助調試
5. ✅ 多層級的錯誤回退機制確保系統穩定性

**技術改進:**
- 豁免規則按照文檔標準先篩選有效題目，再檢查兩個條件
- MSR錯誤處理增加NaN過濾、數據有效性檢查、詳細警告
- 保持6.0分鐘的默認回退值，確保MSR建議生成不會失敗

## 三科診斷報告語言切換即時更新修復 (2025-01-30)

**Status: COMPLETED ✅**

Successfully implemented real-time language switching for diagnostic reports in all three subjects (Q, V, DI).

### 問題描述:
用戶反映三個科目的文字診斷報告在i18n語言切換後沒有即時更新，需要重新生成報告才會顯示新語言。

### 根本原因:
診斷報告的內容在分析完成時生成為完整的文字字符串，並存儲在`st.session_state.report_dict`中。這些內容是固定字符串而非動態翻譯鍵，因此語言切換時不會自動更新。

### 修復過程:

**1. 創建報告重新生成機制**

在`gmat_diagnosis_app/utils/report_regeneration.py`中實現了完整的報告重新生成邏輯：

Mistake: 診斷報告使用固定文字存儲，語言切換時不會更新
Wrong:
```python
# 語言切換時只更新i18n系統，報告內容不變
if selected_language != current_lang:
    st.session_state.current_language = selected_language
    set_language(selected_language)
    st.rerun()
```

Correct:
```python
# 語言切換時重新生成診斷報告
if selected_language != current_lang:
    st.session_state.current_language = selected_language
    set_language(selected_language)
    
    # Re-generate diagnostic reports if analysis is complete
    if st.session_state.get("diagnosis_complete", False) and st.session_state.get("processed_df") is not None:
        from gmat_diagnosis_app.utils.report_regeneration import regenerate_reports_for_language_switch
        regenerate_reports_for_language_switch()
    
    st.rerun()
```

**2. 實現完整的重新生成函數**

```python
def regenerate_reports_for_language_switch():
    """
    Regenerate diagnostic reports when language is switched.
    Re-runs the diagnosis logic on existing processed data to get reports in the new language.
    """
    # 重新獲取處理過的數據
    df_final = st.session_state.get("processed_df")
    
    # 恢復時間壓力設定
    time_pressure_map = {}
    for subject in SUBJECTS:
        time_pressure_key = f"{subject.lower()}_time_pressure"
        # ... 恢復邏輯 ...
    
    # 重新生成每個科目的報告
    temp_report_dict = {}
    for subject in SUBJECTS:
        if subject == 'Q':
            subj_results, subj_report, df_subj_diagnosed = diagnose_q(df_subj)
        elif subject == 'DI':
            subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_subj, time_pressure)
        elif subject == 'V':
            subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
        
        temp_report_dict[subject] = final_report_for_subject
    
    # 更新session state
    st.session_state.report_dict = temp_report_dict
    
    # 重新生成AI綜合報告（如有）
    if st.session_state.get('master_key'):
        consolidated_report = generate_ai_consolidated_report(temp_report_dict, st.session_state.master_key)
        st.session_state.consolidated_report = consolidated_report
```

### 修復效果:
1. ✅ 三個科目診斷報告支持即時語言切換
2. ✅ 語言切換時自動重新生成報告內容
3. ✅ 保持原有診斷邏輯和數據完整性
4. ✅ AI綜合報告也會重新生成（如適用）
5. ✅ 用戶體驗改善：無需重新分析即可看到新語言報告

### 技術實現:
- 在語言切換邏輯中檢測是否已有診斷結果
- 如有結果則調用報告重新生成函數
- 重新生成過程復用原有診斷邏輯，確保一致性
- 保持時間壓力設定和其他分析參數
- 支持OpenAI報告總結功能的重新生成

**用戶影響:** 現在用戶可以在查看結果時隨時切換語言，診斷報告會立即以新語言顯示，大幅提升了多語言使用體驗。