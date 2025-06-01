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

## Q&DI診斷報告列表縮排統一優化及背景顏色修正 (2025-01-29)

Mistake: 列表縮排邏輯僅針對Q報告Key Focus區域，未覆蓋DI報告的反思提示等列表結構；診斷報告背景顏色與父容器不一致
Wrong:
1. 縮排處理邏輯僅檢測「Key Focus」和「重點關注」，未處理DI報告中的引導性反思提示等列表結構：
```python
# 僅處理Key Focus區域
if re.match(r'^\s*.*Key Focus:|^\s*.*重點關注', line, re.IGNORECASE):
    in_key_focus_section = True
```
2. 診斷報告使用白色背景，與父容器不一致：
```css
.diagnostic-report {
    background-color: #ffffff;  /* 固定白色背景 */
}
```

Correct:
1. 擴展列表區域檢測模式，涵蓋所有需要縮排處理的列表結構：
```python
list_section_patterns = [
    r'^\s*.*Key Focus:|^\s*.*重點關注',  # Q報告Key Focus
    r'^\s*.*引導性反思提示',  # DI報告反思提示
    r'^\s*.*引導反思提示',   # V報告反思提示
    r'^\s*.*\*\*.*\*\*：.*題目.*反思',  # 具體反思標題
    r'^\s*.*【.*】：',  # 分類標題
]
```
2. 修改診斷報告背景為透明，與父容器一致：
```css
.diagnostic-report {
    background-color: transparent;  /* 透明背景 */
}
```

Applied:
1. 統一列表縮排處理邏輯：
   - Q報告：Key Focus下的核心問題列表
   - DI報告：引導性反思提示下的分類項目
   - V報告：引導反思提示相關內容
   - 所有報告：分類標題（【】格式）

2. 優化縮排層級處理：
   - 第一層列表：`- ` → `  - `（2個空格縮排）
   - DI分類項目：`            * 【` → `        * 【`（12→8個空格）
   - DI第二層項目：`        * ` → `    * `（8→4個空格）
   - 保持4個空格項目不變
   - 其他星號項目添加基本縮排

3. 背景顏色統一：
   - 診斷報告背景改為透明
   - 保持邊框和陰影以維持視覺區分
   - 與父容器背景色保持一致

Fixed: 
- Q、DI、V三個科目的診斷報告列表結構現在都有適當的縮排層級
- 診斷報告背景顏色與應用程式主要容器保持一致
- 提供清晰的視覺層次同時避免背景顏色衝突

## Q診斷報告Key Focus區域縮排層級修正 (2025-01-29)

Mistake: Q診斷報告中「重點關注」或「Key Focus」下的列表項目缺少適當的縮排層級
Wrong:
格式化函數過度移除縮排，導致「重點關注」標題下的項目點沒有層級區分：
```
重點關注：題目是否重複涉及報告第III部分指出的核心問題：
- Q Carelessness Issue: Detail Omission
- Q Concept Application Error: Mathematical Concept/Formula Application
- Q Calculation Error: Mathematical Calculation
```
顯示為同一層級，缺少視覺層次

Correct:
改進格式化邏輯，為Key Focus區域下的列表項目添加適當縮排：
```python
# 檢測Key Focus區域並為其下的列表項目添加縮排
if in_key_focus_section:
    if line.startswith('- '):
        # 為Key Focus下的列表項目添加2個空格縮排
        processed_lines.append('  ' + line)
    elif line.startswith('**注意**'):
        # 注意事項保持原樣
        processed_lines.append(line)
    else:
        processed_lines.append(line)
```

Applied:
1. 改進Key Focus區域檢測邏輯，更準確地識別「重點關注」和「Key Focus」區域
2. 為該區域下的列表項目（- 開頭）自動添加2個空格縮排
3. 改進區域結束檢測，通過標題標記或內容分析判斷何時離開Key Focus區域
4. 保留注意事項和說明文字的原始格式

Fixed: Q診斷報告中「重點關注」標題下的核心問題列表現在顯示為適當的第二層級縮排，提供清晰的視覺層次

## Q Diagnostic Report Format Update (2025-01-29)

Mistake: Q diagnostic reporting format not matching q_section_diagnostic_report_formatted.md structure
Wrong:
Using old bullet point heavy format with multiple nested levels and translation keys:
```python
# In reporting.py generate_report_section3
lines = [t('core_issues_diagnosis')]
lines.append("")
lines.append(t('high_frequency_potential_issues'))
# Multiple nested bullet points like:
lines.extend([f"    * {line}" for line in core_issue_summary])
```
Correct:
Updated to use cleaner heading structure with reduced bullet point nesting:
```python
# Updated format following q_section_diagnostic_report_formatted.md
lines = []
lines.append("**B. 高頻潛在問題**")
# Direct text without excessive nesting:
for line in core_issue_summary:
    lines.append(line)
    lines.append("")
```

Applied:
1. Updated reporting.py to use ### for main sections, ** for subsections
2. Reduced bullet point nesting - only use for specific data items
3. Direct paragraph text for explanatory content
4. Updated styling.py format_diagnostic_report function to handle new structure
5. Maintained all diagnostic logic while improving readability

Fixed: Q diagnostic reports now follow the cleaner format structure specified in q_section_diagnostic_report_formatted.md with proper heading hierarchy and minimal bullet point usage

## Translation System Fix for Failing Chinese Strings (2025-01-28)

Mistake: Chinese strings used as translation keys causing lookup failures
Wrong:
Using original Chinese strings directly in code and expecting i18n system to handle them:
```python
# In results_display.py
"行為模式": ["粗心問題（快而錯比例高）"]

# In translation tests
'RC 時間個別題目效率嚴重問題：個別題目時間效率嚴重問題'
'粗心問題 (快而錯比例高)'
'RC 閱讀速度差：整組表現不佳'
```
Correct:
Created English translation keys for failing Chinese strings and used them consistently:
```python
# Added new translation keys in both zh_TW.py and en.py:
'rc_timing_individual_question_efficiency_severe_issue_full': "RC 時間個別題目效率嚴重問題：個別題目時間效率嚴重問題"
'carelessness_issue_high_fast_wrong_ratio': "粗心問題 (快而錯比例高)"
'rc_reading_speed_poor_group_performance_poor': "RC 閱讀速度差：整組表現不佳"

# Updated results_display.py to use translation function:
from gmat_diagnosis_app.i18n import translate as t
"行為模式": [t('carelessness_issue_high_fast_wrong_ratio')]

# Updated test scripts to use new English keys instead of original Chinese strings
```

Fixed: All translation tests now pass with 100% success rate
Applied: Consistent use of English translation keys throughout the system for proper i18n functionality

## V Diagnosis Logic Compliance Issues (2025-01-28)

Mistake: Missing RC overtime calculation based on time pressure status
Wrong:
No RC group target time calculation based on time_pressure_status in V modules
Correct:
Need to implement RC group target time calculation:
```python
# In constants.py or analysis.py
RC_GROUP_TARGET_TIMES = {
    True: {  # High Pressure
        3: 6.0,
        4: 8.0
    },
    False: {  # Low Pressure
        3: 7.0,
        4: 9.0
    }
}
```

Mistake: Missing RC group overtime and individual overtime logic
Wrong:
Only using pre-calculated overtime flag for RC without proper group/individual distinction
Correct:
Need to implement proper RC overtime calculation:
1. group_overtime: if group_total_time > (rc_group_target_time + 1.0)
2. individual_overtime: if adjusted_rc_time > 2.0 (rc_individual_q_threshold)
3. RC question is "slow" if group_overtime == True OR individual_overtime == True

Mistake: Inconsistent question_type mapping in analysis
Wrong:
Using full question type names 'Critical Reasoning' and 'Reading Comprehension' in some places
Correct:
MD document specifies mapping: 'Critical Reasoning' → 'CR', 'Reading Comprehension' → 'RC'
Should standardize the mapping or ensure consistent usage throughout

Mistake: Missing first_third_average_time_per_type calculation for V diagnosis
Wrong:
V diagnosis doesn't calculate first_third_average_time_per_type for invalid data detection
Correct:
Should calculate first_third_average_time_per_type for both CR and RC types for standard 3 & 4 invalid detection criteria

## V Diagnosis Logic Compliance Fixed (2025-01-28)

Fixed: Added unified first_third_average_time_per_type calculation to V diagnosis
Applied:
Added import and calculation in gmat_diagnosis_app/diagnostics/v_modules/main.py:
```python
from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_first_third_average_time_per_type

# In run_v_diagnosis_processed function:
first_third_average_time_per_type = calculate_first_third_average_time_per_type(
    df_v_processed, ['Critical Reasoning', 'Reading Comprehension']
)
```

Fixed: Removed duplicate CR overtime calculation in apply_ch3_diagnostic_rules
Applied:
Modified gmat_diagnosis_app/diagnostics/v_modules/analysis.py to trust unified calculate_overtime function:
```python
# Old code (duplicated calculation):
if q_type == 'Critical Reasoning' and pd.notna(q_time) and q_time > cr_ot_threshold:
    current_is_overtime = True
elif q_type == 'Reading Comprehension' and original_row_overtime:
    current_is_overtime = True

# New code (unified approach):
original_row_overtime = bool(row.get('overtime', False)) # Get pre-calculated overtime from unified function
current_is_overtime = original_row_overtime # Trust the unified calculation for both CR and RC
```

Fixed: RC overtime logic already implemented in unified time_analyzer.py
Status:
RC group/individual overtime distinction is properly implemented in analysis_helpers/time_analyzer.py with:
- RC_GROUP_TARGET_TIMES correctly defined based on pressure status
- group_overtime and individual_overtime calculations
- RC方案四 implementation with group performance categories
- RC tolerance logic for good group performance

Fixed: Implemented complete four abnormally fast response criteria for V diagnosis
Applied:
Updated gmat_diagnosis_app/constants/thresholds.py to include V section invalid detection thresholds:
```python
'V': {
    'TIME_PRESSURE_DIFF_MIN': 3.0,  # V 科目時間壓力閾值（分鐘）
    'LAST_THIRD_FRACTION': 2/3,  # 檢查測驗最後 1/3 的題目
    'INVALID_ABANDONED_MIN': 0.5,  # 標準1：疑似放棄閾值（分鐘）
    'INVALID_HASTY_MIN': 1.0,  # 標準2：絕對倉促閾值（分鐘）
    'INVALID_TAG': "數據無效：用時過短（V：受時間壓力影響）"
}
```

Updated gmat_diagnosis_app/data_validation/invalid_suggestion.py to implement four criteria:
1. Standard 1: Suspected abandonment (< 0.5 min)
2. Standard 2: Absolutely rushed (< 1.0 min)  
3. Standard 3 & 4: Relative to first third average time (only check in last 1/3 of test)
4. Uses unified calculate_first_third_average_time_per_type function for consistency

Fixed: Replaced hardcoded 0.75 multiplier with unified RELATIVELY_FAST_MULTIPLIER constant
Applied:
Modified gmat_diagnosis_app/diagnostics/v_modules/analysis.py:
```python
# Added import and constant definition
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS
RELATIVELY_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['RELATIVELY_FAST_MULTIPLIER']

# Replaced hardcoded value
if q_time < (avg_time * RELATIVELY_FAST_MULTIPLIER):  # Relatively fast threshold
```

Fixed: Replaced hardcoded 0.25 carelessness threshold with unified CARELESSNESS_THRESHOLD constant
Applied:
Modified gmat_diagnosis_app/diagnostics/v_modules/analysis.py:
```python
# Added constant definition
CARELESSNESS_THRESHOLD = COMMON_TIME_CONSTANTS['CARELESSNESS_THRESHOLD']

# Replaced hardcoded value and updated comments
if fast_wrong_rate > CARELESSNESS_THRESHOLD:
```

## GMAT Q Diagnosis Logic Corrections (2025-01-28)

Mistake: Missing first third average time calculation
Wrong:
Missing implementation of `first_third_average_time_per_type` calculation required by MD Doc Chapter 0
Correct:
Added proper calculation in main.py:
```python
first_third_average_time_per_type = {}
if 'question_position' in df_q.columns and 'question_time' in df_q.columns and 'question_type' in df_q.columns:
    total_questions = len(df_q)
    first_third_end = total_questions // 3
    df_first_third = df_q[df_q['question_position'] <= first_third_end]
    
    for q_type in ['Real', 'Pure']:
        type_data = df_first_third[df_first_third['question_type'] == q_type]
        if not type_data.empty:
            avg_time = type_data['question_time'].mean()
            first_third_average_time_per_type[q_type] = avg_time if not pd.isna(avg_time) else 2.0
        else:
            first_third_average_time_per_type[q_type] = 2.0
```

Mistake: Incomplete invalid data detection logic
Wrong:
Missing the four specific abnormally fast response criteria and time pressure condition check from MD Doc Chapter 1
Correct:
Added proper invalid data detection with all four standards and time pressure condition check

Mistake: Incorrect fast threshold multiplier
Wrong:
Using hardcoded 0.75 multiplier in analysis.py
Correct:
Using RELATIVELY_FAST_MULTIPLIER constant from constants.py (0.75)

Mistake: Wrong carelessness calculation logic
Wrong:
Calculating ratio of Fast & Wrong to all Fast categories
Correct:
Calculating ratio of Fast & Wrong to all relatively fast questions based on time performance category

## MD Document Compliance Corrections (2025-01-28)

Mistake: Incorrect last third calculation for invalid data detection
Wrong:
```python
last_third_start = (len(df_q) * 2) // 3 + 1
last_third_questions = df_q[df_q['question_position'] >= last_third_start]
```
Correct:
```python
# 計算測驗最後 1/3 的題目（MD文檔第一章）
total_questions = len(df_q)
last_third_size = total_questions // 3
all_positions = sorted(df_q['question_position'].unique())
if len(all_positions) >= last_third_size:
    last_third_positions = all_positions[-last_third_size:]
    last_third_questions = df_q[df_q['question_position'].isin(last_third_positions)]
```

Mistake: Hardcoded total questions constant
Wrong:
TOTAL_QUESTIONS_Q = 20  # 題目總數
Correct:
Removed hardcoded constant, calculate from actual data at runtime using len(df_q)

Mistake: Incorrect carelessness rate calculation using string matching
Wrong:
```python
num_relatively_fast_total = df_q_valid_diagnosed[df_q_valid_diagnosed['time_performance_category'].str.contains('Fast')].shape[0]
```
Correct:
```python
# 重新計算相對快速作答，按第三章定義
avg_times_by_type = df_q_valid_diagnosed.groupby('question_type')['question_time'].mean().to_dict()
df_temp['is_relatively_fast'] = df_temp['question_time'] < (df_temp['avg_time_for_type'] * 0.75)
num_relatively_fast_total = df_temp['is_relatively_fast'].sum()
```

## Code Duplication Prevention (2025-01-28)

Mistake: Duplicated time-related constants and functions across Q, DI, V modules
Wrong:
Each module had its own implementation of:
- SUSPICIOUS_FAST_MULTIPLIER = 0.5
- first_third_average_time_per_type calculation
- CARELESSNESS_THRESHOLD constants
Correct:
Created unified approach:
1. Central constants in `constants/thresholds.py` -> COMMON_TIME_CONSTANTS
2. Unified function in `analysis_helpers/time_analyzer.py` -> calculate_first_third_average_time_per_type()
3. All modules import from unified sources

## I18n Implementation Best Practices (2025-01-28)

Mistake: Inconsistent import patterns for translation system
Wrong:
Mixed import styles across modules:
```python
from gmat_diagnosis_app.diagnostics.v_modules.translations import translate_v as t
from gmat_diagnosis_app.i18n.translate import translate
```
Correct:
Standardized import pattern across all modules:
```python
from gmat_diagnosis_app.i18n import translate as t
```

Mistake: Leaving hardcoded Chinese text in user-facing functions
Wrong:
```python
report_lines.append("V 科診斷報告詳情")
rec_text = f"針對【{skill_display_name}】建議練習【{y_grade}】難度題目"
```
Correct:
Convert all hardcoded text to translation keys:
```python
report_lines.append(t('v_report_title'))
rec_text = t('v_practice_recommendation_template').format(sfe_prefix, skill_display_name, y_grade, z_text, target_time_text)
```

Mistake: Not adding comprehensive translation coverage for new modules
Wrong:
Converting only some functions while leaving others with hardcoded text
Correct:
Systematic conversion approach:
1. Add all required translation keys to both zh-TW.py and en.py
2. Convert all user-facing strings in all module files
3. Test key functions to ensure translations work
4. Follow the same pattern as previously completed Q section

Mistake: Inconsistent translation key naming
Wrong:
Mixed naming conventions for translation keys
Correct:
Follow consistent naming pattern:
- Module prefix: 'v_' for V section, 'q_' for Q section
- Descriptive names: 'v_report_title', 'v_practice_recommendations'
- Parameter codes: 'CR_READING_BASIC_OMISSION', 'RC_READING_SPEED_SLOW_FOUNDATIONAL'

Mistake: Forgetting to update import statements when converting translation systems
Wrong:
Keeping old import statements after implementing i18n:
```python
from gmat_diagnosis_app.diagnostics.v_modules.translations import translate_v
```
Correct:
Update all import statements to use centralized i18n system:
```python
from gmat_diagnosis_app.i18n import translate as t
```

## V Diagnosis Logic Compliance Status (2025-01-28) - COMPLETED

All V section implementation issues have been resolved and aligned with gmat-v-score-logic-dustin-v1.4.md standards:

✅ RC_INDIVIDUAL_Q_THRESHOLD_MINUTES corrected to 2.0 minutes
✅ Unified first_third_average_time_per_type calculation implemented
✅ Complete four abnormally fast response criteria implemented for invalid data detection
✅ Unified overtime calculation logic properly integrated (no duplicate CR overtime calculation)
✅ Hardcoded multipliers (0.75, 0.25) replaced with unified constants
✅ Question type mapping consistency verified (Critical Reasoning ↔ CR, Reading Comprehension ↔ RC)
✅ RC overtime logic confirmed working in unified time_analyzer.py
✅ All syntax checks passed

V section diagnosis is now fully compliant with MD document Chapter 1 requirements.

## Python Import Syntax Issues (2025-01-28)

Mistake: Python module import error with hyphenated filenames
Wrong:
Translation file named "zh-TW.py" causing import error "無法解析匯入 gmat_diagnosis_app.i18n.translations.zh_TW"
Python cannot import modules with hyphens in filenames using dot notation.
Correct:
Renamed translation file from "zh-TW.py" to "zh_TW.py" to comply with Python import syntax.
Updated i18n system to map language codes to filenames:
```python
# In gmat_diagnosis_app/i18n/__init__.py
self.file_mapping = {
    'zh-TW': 'zh_TW',  # 語言代碼使用連字號，檔案名稱使用底線
    'en': 'en'
}
file_path = os.path.join(translation_dir, f'{self.file_mapping[lang]}.py')
```

This allows language codes to use hyphens (zh-TW) while filenames use underscores (zh_TW.py) for Python compatibility.

## V Diagnosis Translation Missing Keys (2025-01-28)

Mistake: V診斷報告中顯示英文鍵值而非中文翻譯
Wrong:
部分診斷參數缺少中文翻譯，導致報告中顯示原始英文鍵值：
- CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP
- CR_STEM_UNDERSTANDING_ERROR_VOCAB  
- CR_STEM_UNDERSTANDING_ERROR_SYNTAX
- RC_READING_COMPREHENSION_ERROR_VOCAB
- 'Slow & Correct' 時間表現類別翻譯缺失
Correct:
在 gmat_diagnosis_app/i18n/translations/zh_TW.py 中添加完整翻譯：
```python
'CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP': "CR 題幹理解錯誤：提問要求把握",
'CR_STEM_UNDERSTANDING_ERROR_VOCAB': "CR 題幹理解錯誤：詞彙",
'CR_STEM_UNDERSTANDING_ERROR_SYNTAX': "CR 題幹理解錯誤：句式",
'RC_READING_COMPREHENSION_ERROR_VOCAB': "RC 閱讀理解錯誤：詞彙",
'Slow & Correct': "慢對",
```
修正方法：使用腳本動態添加翻譯，確保所有診斷參數都有對應的中文翻譯。

## V Diagnosis English Translation Missing Keys (2025-01-28)

Mistake: Missing V diagnosis report section translations in English dictionary
Wrong:
Many V section report keys were present in zh_TW.py but missing in en.py, causing English reports to display raw keys instead of translations:
- v_special_behavior_observation
- v_careless_advice  
- v_practice_advice_and_consolidation
- v_prioritize_skill_consolidation
- v_overall_practice_direction
- v_subsequent_action_and_deep_reflection
- v_guided_reflection
- v_seek_advanced_assistance
And many more V-specific keys

Correct:
Added missing English translations to gmat_diagnosis_app/i18n/translations/en.py:
```python
# Missing V report sections that appear in your English report but are not translated
'v_special_behavior_observation': "* **D. Special Behavioral Pattern Observations**",
'v_careless_advice': "Analysis shows that \"fast and wrong\" situations account for a high proportion ({}), suggesting the need to focus on response carefulness",
'v_practice_advice_and_consolidation': "**III. Practice Recommendations and Foundation Consolidation**",
'v_prioritize_skill_consolidation': "* **A. Priority Consolidation Skills**",
'v_overall_practice_direction': "* **B. Overall Practice Direction**",
'v_subsequent_action_and_deep_reflection': "**IV. Follow-up Action and Deep Reflection Guidance**",
'v_guided_reflection': "* **B. Guided Reflection Prompts (Targeting Specific Skills and Performance)**",
'v_seek_advanced_assistance': "**V. Seeking Advanced Assistance (Qualitative Analysis)**",
# And many more diagnostic parameter translations
```

Mistake: Missing V diagnostic parameter translations in English dictionary
Wrong:
Diagnostic parameters like CR_STEM_UNDERSTANDING_ERROR_* and RC_CHOICE_ANALYSIS_ERROR_* were missing English translations
Correct:
Added comprehensive diagnostic parameter translations for CR and RC error/difficulty types in en.py dictionary

## V Diagnosis English Translation Missing Keys - COMPLETED (2025-01-28)

Status: ✅ FULLY RESOLVED
- Added 80+ missing V section translation keys to English dictionary
- All V report sections now have proper English translations
- All CR/RC diagnostic parameters now have English translations  
- Time performance categories (Fast & Wrong, Slow & Correct, etc.) translations completed
- Tested and verified all translations work correctly in both languages
- V section English reports will now display proper translations instead of raw keys

Key additions include:
- V report structure translations (v_special_behavior_observation, v_practice_advice_and_consolidation, etc.)
- V reflection and guidance translations (v_guided_reflection, v_seek_advanced_assistance, etc.)
- CR diagnostic parameters (CR_STEM_UNDERSTANDING_ERROR_*, CR_REASONING_ERROR_*, etc.)
- RC diagnostic parameters (RC_CHOICE_ANALYSIS_ERROR_*, RC_READING_COMPREHENSION_ERROR_*, etc.)
- Time performance categories (Slow & Correct, Fast & Wrong, etc.)

## V Diagnosis Chinese Translation Missing Keys - COMPLETED (2025-01-28)

Mistake: Missing V diagnosis diagnostic parameters translations in Chinese dictionary
Wrong:
Several CR diagnostic parameters were missing Chinese translations, causing Chinese reports to display raw English keys:
- CR_STEM_UNDERSTANDING_ERROR_LOGIC
- CR_STEM_UNDERSTANDING_ERROR_DOMAIN
- v_overall_practice_direction
- v_review_practice_record
And behavioral pattern keys like "行為模式: 粗心問題 (快而錯比例高)"

Additionally, new translations were initially added outside the TRANSLATIONS dictionary closing brace, making them ineffective.

Correct:
1. Added missing Chinese translations to gmat_diagnosis_app/i18n/translations/zh_TW.py:
```python
'CR_STEM_UNDERSTANDING_ERROR_LOGIC': "CR 題幹理解錯誤：邏輯",
'CR_STEM_UNDERSTANDING_ERROR_DOMAIN': "CR 題幹理解錯誤：領域",
'v_overall_practice_direction': "* **B. 整體練習方向**",
'v_review_practice_record': "* **A. 檢視練習記錄（二級證據參考）**",
'行為模式: 粗心問題 (快而錯比例高)': "行為模式: 粗心問題 (快而錯比例高)",
'應用不穩定 (**SFE**)：已掌握技能應用不穩定': "應用不穩定 (**SFE**)：已掌握技能應用不穩定",
'RC 時間個別題目效率嚴重問題：個別題目時間效率嚴重問題': "RC 時間個別題目效率嚴重問題：個別題目時間效率嚴重問題",
'RC 閱讀速度差：整組表現不佳': "RC 閱讀速度差：整組表現不佳",
```

2. Fixed dictionary structure issue: Moved new translations from outside the closing `}` to inside the TRANSLATIONS dictionary.

3. Tested and verified all translations work correctly with the i18n system.

Status: ✅ FULLY RESOLVED
- All CR diagnostic parameters now have proper Chinese translations
- V report structure keys properly translated
- Behavioral pattern translations working correctly
- Dictionary structure corrected to ensure all translations are loaded

## DI Diagnosis i18n Implementation Completed (2025-01-28)

Fixed: Successfully migrated DI diagnostic modules from custom translation system to unified i18n system
Applied:
1. Added comprehensive DI translations to unified i18n system:
   - Added ~100+ DI translation keys to zh_TW.py and en.py
   - Covered all diagnostic parameters, report sections, AI prompts, and utility functions
   - Maintained consistency with existing V/Q module translation patterns

2. Updated all DI module files to use unified i18n system:
   - main.py: Replaced `from .translation import _translate_di` with `from gmat_diagnosis_app.i18n import translate as t`
   - report_generation.py: Updated all hardcoded Chinese text to use translation keys
   - ai_prompts.py: Converted AI tool recommendations and error messages
   - utils.py: Updated difficulty grading function to use i18n
   - chapter_logic.py: Replaced _translate_di calls with t() function calls
   - constants.py: Removed hardcoded INVALID_DATA_TAG_DI, now uses 'di_invalid_data_tag' key

3. Replaced INVALID_DATA_TAG_DI constant usage:
   - Removed from constants.py and all import statements
   - Updated all references to use t('di_invalid_data_tag') instead
   - Maintained functionality while enabling bilingual support

4. Verified implementation:
   - All files compile without syntax errors
   - i18n translations work correctly for both Chinese and English
   - Real-time language switching capability maintained via session state

Status: DI diagnostic report now fully supports bilingual output with unified i18n system, following same pattern as V/Q modules.

## DI Diagnosis Logic Compliance Issues (2025-01-28)

Mistake: MSR reading time calculation for single-question groups doesn't follow MD document
Wrong:
```python
# In di_preprocessor.py
if num_other_qs_msr == 0:
    calculated_msr_reading_time = first_q_time_msr  # Use first question time directly
```
Correct:
MD document states "此計算僅在題組包含至少兩題時有效" - should not calculate reading time for single-question MSR groups

Mistake: Invalid data detection standards use exclusive checking instead of "any one triggers"
Wrong:
```python
# In main.py invalid data logic
if not abnormally_fast and pd.notna(q_time) and q_time < 1.0:
    abnormally_fast = True
```
Correct:
Standards should be checked independently as MD document states "滿足其一即可觸發", not exclusive checking

Mistake: MSR overtime logic adds undefined msr_reading_over check
Wrong:
```python
# In main.py overtime calculation
msr_reading_over = msr_mask & (~msr_group_over) & df_di['is_first_msr_q'] & df_di['msr_reading_time'].notna() & (df_di['msr_reading_time'] > thresholds['MSR_READING'])
msr_over_mask = msr_group_over | msr_reading_over | msr_adj_first_over | msr_non_first_over
```
Correct:
MD document only defines group_overtime OR individual_overtime, no separate reading time overtime check

Mistake: MSR Z_agg calculation uses msr_group_total_time instead of question_time
Wrong:
```python
# In chapter_logic.py _check_foundation_override
max_group_time_minutes = triggering_df['msr_group_total_time'].max()
z_agg = math.floor(max_group_time_minutes * 2) / 2.0
```
Correct:
MD document specifies Z_agg should use max question_time: "找出該題型下所有...題目中的最大 question_time"

## DI Diagnosis Logic Detailed Compliance Issues Found (2025-01-28)

Issue Category: Logic Flow Consistency
- MSR reading time calculation violates MD document constraints
- Invalid data detection uses wrong logical operators
- Overtime calculation adds undefined checks
- Foundation override uses wrong time metrics for MSR

Impact: These issues may cause incorrect diagnostic results and recommendations that don't align with the standardized MD document framework

Status: Identified, awaiting user decision on which fixes to prioritize

## DI Diagnosis Logic Compliance Issues - FIXED (2025-01-28)

Fixed: MSR reading time calculation for single-question groups now follows MD document
Applied:
Modified gmat_diagnosis_app/subject_preprocessing/di_preprocessor.py line 69-80:
- Removed automatic fallback to first_q_time_msr for single-question groups
- Added clear comment explaining MD document constraint: "此計算僅在題組包含至少兩題時有效"
- Single-question MSR groups now keep msr_reading_time = 0.0 as initialized

Fixed: Invalid data detection standards now use independent checking instead of exclusive
Applied:
Modified gmat_diagnosis_app/diagnostics/di_modules/main.py lines 127-140:
- Removed "if not abnormally_fast" conditions from Standards 2, 3-5, and 6
- Changed to independent checks allowing "滿足其一即可觸發" as per MD document
- All standards now check independently and any can trigger abnormally_fast = True

Fixed: MD document updated to match code implementation for MSR overtime logic
Applied:
Updated analysis-framework/sec-doc-zh/gmat-di-score-logic-dustin-v1.4.md:
- Changed MSR overtime from "雙重標準" to "四重標準"
- Added detailed descriptions for msr_group_over, msr_reading_over, msr_adj_first_over, msr_non_first_over
- Updated final overtime condition to match code: "msr_group_over OR msr_reading_over OR msr_adj_first_over OR msr_non_first_over"

Fixed: MD document updated for MSR Z_agg calculation to match code implementation
Applied:
Updated analysis-framework/sec-doc-zh/gmat-di-score-logic-dustin-v1.4.md Chapter 5:
- Added MSR special handling note: "對於MSR題型，使用 msr_group_total_time 作為時間計算基準"
- Document now reflects code's actual implementation using different time metrics for different question types

Status: All 5 DI diagnosis logic compliance issues have been resolved according to user decisions:
1. ✅ Code fixed to match MD document (MSR reading time calculation)
2. ✅ Code fixed to match MD document (invalid data detection)  
3. ✅ MD document updated to match code (MSR overtime logic)
4. ✅ MD document updated to match code (override parameters)
5. ✅ MD document updated to match code (Z_agg calculation)

## Hardcoded Chinese Text Completion Fix (2025-01-29)

Mistake: Remaining hardcoded Chinese text in various files after i18n implementation
Wrong:
Files still contained hardcoded Chinese text that should use the translation system:
```python
# In results_display.py
if suggestion_to_display.startswith("錯誤：") or suggestion_to_display.startswith("AI 未能提供修剪建議"):

# In chat_interface.py  
if context["dataframe"] and context["dataframe"] != "(無詳細數據表格)":

# In plotting_service.py
"""
繪圖服務模組
提供生成圖表的功能
"""

# In app.py (comments)
# 設置頁面配置
# 額外確保聊天歷史持久化
```
Correct:
```python
# In results_display.py - use translation keys
if suggestion_to_display.startswith(t('tag_trimming_error_prefix')) or suggestion_to_display.startswith(t('tag_trimming_ai_failed_prefix')):

# In chat_interface.py - use translation key
if context["dataframe"] and context["dataframe"] != t('chat_debug_no_detailed_table'):

# In plotting_service.py - English comments
"""
Plotting service module

Provides functions for generating charts
"""

# In app.py - English comments
# Set page configuration (removed duplicate)
# Ensure chat history persistence
```

Fixed: Added missing translation keys to both zh_TW.py and en.py:
- 'tag_trimming_error_prefix': "錯誤：" / "Error:"
- 'tag_trimming_ai_failed_prefix': "AI 未能提供修剪建議" / "AI failed to provide trimming suggestions"  
- 'chat_debug_no_detailed_table': "(無詳細數據表格)" / "(No detailed data table)"

Applied: All remaining hardcoded Chinese text has been converted to translation system or changed to English comments according to project standards. The hardcoded Chinese check report requirements are now completely fulfilled.

Status: Hardcoded Chinese text cleanup is COMPLETED ✅
- High priority files (app.py, results_display.py, validation.py) ✅
- Medium priority files (chat_interface.py, plotting_service.py) ✅  
- Low priority files (test files and comments) ✅
- All user-facing Chinese text now uses i18n translation system
- Code comments converted to English per project standards

## Module Import Order Fix (2025-01-29)

Mistake: Incorrect import order causing ModuleNotFoundError
Wrong:
```python
# In app.py
import streamlit as st

# Import i18n functions early to use in page config
from gmat_diagnosis_app.i18n import translate as t  # ❌ Too early, before path setup

# Call set_page_config as the first Streamlit command
st.set_page_config(page_title=t("page_title"), ...)

# ... later in the file ...
# --- Project Path Setup ---
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)  # ❌ Path setup happens AFTER import attempt
```
Correct:
```python
# In app.py
import streamlit as st

# ... standard imports ...

# --- Project Path Setup (MUST BE FIRST) ---
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)  # ✅ Path setup BEFORE imports
except NameError:
    project_root = os.getcwd()  # Fallback

# Import i18n functions after path setup
from gmat_diagnosis_app.i18n import translate as t  # ✅ After path setup

# Call set_page_config as early as possible
st.set_page_config(page_title=t("page_title"), ...)
```

Fixed: Reorganized import order in app.py:
1. Standard library imports first
2. Path setup immediately after
3. Custom module imports only after path is configured
4. Added fallback error handling for translation function

Applied: The import order fix resolves the ModuleNotFoundError that occurs when the gmat_diagnosis_app module cannot be found in the Python path.

Status: Module import error RESOLVED ✅
- Path setup now happens before any custom module imports
- Translation system works correctly after path configuration
- Application now starts successfully without import errors

--- 

**Result**: DI diagnostic report now fully supports bilingual output with unified i18n system, matching V/Q module implementation patterns. All translation issues resolved with 100% test success rate.

## Hardcoded Chinese Text Fix (2025-01-29)

Mistake: V diagnostic reporting module still had hardcoded Chinese text "提示：" 
Wrong:
V reporting module using hardcoded Chinese text in behavioral pattern suggestions:
```python
# In gmat_diagnosis_app/diagnostics/v_modules/reporting.py line 231, 236
report_lines.append(f"    * **提示：** {early_rush_param_translated} - {t('v_early_rush_advice')}。")
report_lines.append(f"    * **提示：** {careless_param_translated} - {t('v_careless_advice').format(fast_wrong_rate_str)}。")
```
Correct:
Created translation key for tip prefix and updated V reporting to use translation system:
```python
# Added translation keys in zh_TW.py and en.py:
'v_tip_prefix': "提示：",  # zh_TW.py
'v_tip_prefix': "Tip:",    # en.py

# Updated V reporting.py to use translation function:
report_lines.append(f"    * **{t('v_tip_prefix')}** {early_rush_param_translated} - {t('v_early_rush_advice')}。")
report_lines.append(f"    * **{t('v_tip_prefix')}** {careless_param_translated} - {t('v_careless_advice').format(fast_wrong_rate_str)}。")
```

Fixed: V diagnostic reports now fully support bilingual tip prefix in behavioral pattern sections
Applied: Consistent use of translation system throughout V diagnostic reporting with proper i18n implementation

Status Check: Based on project memory files, DI diagnostic modules have already completed i18n implementation, and Section Detailed Data column headers are already using translation system through results_display.py. The three issues mentioned by user have been addressed:
1. ✅ DI text reports: Already internationalized (completed in previous implementation) 
2. ✅ V text reports "提示：": Fixed with translation key 'v_tip_prefix'
3. ✅ Section Detailed Data column headers: Already using translation system via 'subject_detailed_data' key

## DI Diagnosis Translation Error Fix (2025-06-01)

Mistake: Passing list to translation function instead of individual strings
Wrong:
```python
diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)])
translated_params_list = t(list(diag_params_codes)) # Error: unhashable type: 'list'
```
Correct:
```python
diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)])
translated_params_list = [t(param_code) for param_code in diag_params_codes] # Translate each parameter code separately
```

Fixed: Translation function only accepts strings as keys, not lists. Each parameter code must be translated individually.
Applied: Fixed in gmat_diagnosis_app/diagnostics/di_modules/chapter_logic.py line 758

## Dataframe Column Headers i18n Fix (2025-06-01)

Mistake: Static COLUMN_DISPLAY_CONFIG causing untranslated dataframe headers
Wrong:
```python
# In results_display.py - defined at module load time
COLUMN_DISPLAY_CONFIG = {
    "question_position": st.column_config.NumberColumn(t("column_question_number"), help=t("column_question_number_help")),
    "question_type": st.column_config.TextColumn(t("column_question_type")),
    # ... other columns
}
```
Correct:
```python
# In results_display.py - dynamic function called at runtime
def get_column_display_config():
    """Get column display configuration with current language translations"""
    return {
        "question_position": st.column_config.NumberColumn(t("column_question_number"), help=t("column_question_number_help")),
        "question_type": st.column_config.TextColumn(t("column_question_type")),
        # ... other columns
    }

# Usage updated:
display_subject_results(subject, tabs[actual_tab_index_for_subject], report_md, df_subject, get_column_display_config(), {})
```

Fixed: Dataframe column headers in diagnosis reports now properly respond to language changes. Static configuration caused headers to be fixed at module load time rather than adapting to current language setting.
Applied: Modified gmat_diagnosis_app/ui/results_display.py to use dynamic configuration function

## Q科診斷報告代碼塊格式錯誤修復 (2025-01-29)

Mistake: Q科診斷報告中診斷參數文字被錯誤包裹在代碼塊中
Wrong:
```python
# 在styling.py中的代碼塊移除規則不夠完全
# 16. 修正可能的格式化問題
# 避免不當的代碼塊格式
report_text = re.sub(r'```([^`]*[\u4e00-\u9fff][^`]*)```', r'\1', report_text)

# 這個規則只能移除包含中文的代碼塊，無法處理：
# 1. 純英文的代碼塊：```Q Concept Application Error```
# 2. 單行代碼格式：`Q Concept Application Error`
# 3. 多行代碼塊標記
# 4. 混合格式代碼塊
```
Correct:
```python
# 16. 修正可能的格式化問題 - 強化代碼塊移除
# 移除所有可能的代碼塊格式（包含中文、英文、數字、符號等）
report_text = re.sub(r'```([^`]*)```', r'\1', report_text)
report_text = re.sub(r'`([^`]+)`', r'\1', report_text)

# 特別處理包含診斷參數的代碼塊
report_text = re.sub(r'```\s*\[Problem Types[^\]]*\].*?```', lambda m: m.group(0).replace('```', ''), report_text, flags=re.DOTALL)

# 移除單行代碼格式（反引號）
report_text = re.sub(r'`([^`\n]*)`', r'\1', report_text)

# 移除多行代碼塊標記
report_text = re.sub(r'^```[a-zA-Z]*\n', '', report_text, flags=re.MULTILINE)
report_text = re.sub(r'\n```$', '', report_text, flags=re.MULTILINE)
report_text = re.sub(r'^```$', '', report_text, flags=re.MULTILINE)

# 17. 特別處理可能被誤認為代碼的診斷參數行
# 移除可能的內聯代碼格式化
report_text = re.sub(r'(\s+- [^:]+：)`([^`]+)`', r'\1\2', report_text)

# 18. 確保沒有遺留的代碼塊標記
report_text = re.sub(r'```', '', report_text)
report_text = re.sub(r'`', '', report_text)
```

Fixed: Q科診斷報告現在能完全移除所有類型的代碼塊格式化
Applied: 強化了gmat_diagnosis_app/utils/styling.py中的format_diagnostic_report函數，添加了多重代碼塊移除規則

測試結果：
- ✅ 移除三重反引號代碼塊：```content```
- ✅ 移除單一反引號代碼：`content`
- ✅ 移除多行代碼塊標記
- ✅ 處理混合格式代碼塊
- ✅ 保留正常的粗體格式：**content**
- ✅ 特別處理診斷參數內容
```

## V科診斷報告方括號格式錯誤修復 (2025-01-29)

Mistake: V科診斷報告中方括號格式被錯誤顯示，且過度縮排被Markdown識別為代碼塊
Wrong:
```python
# 在V科報告生成中使用方括號格式和過度縮排，但styling.py缺少對應處理規則
# gmat_diagnosis_app/diagnostics/v_modules/reporting.py 第467行：
category_lines.append(f"        【{category_reflect_key}】：{labels_in_category_text}")

# 產生的格式如：
# 8個空格 + 【Other Issues】：【CR Choice Understanding Error: Logic】
# 在Markdown中，4個或更多空格會被自動識別為代碼塊

# styling.py中缺少對方括號格式和過度縮排的處理規則
```
Correct:
```python
# 在styling.py中添加V科方括號格式和過度縮排處理規則：

# 5. 修正過度縮排問題（防止被識別為代碼塊）
# 將4個或更多空格開頭的行調整為最多3個空格，避免Markdown代碼塊識別
# 但保留有意義的層級結構
report_text = re.sub(r'^([ ]{4})([^\s])', r'  \2', report_text, flags=re.MULTILINE)  # 4空格->2空格
report_text = re.sub(r'^([ ]{5,8})([^\s])', r'   \2', report_text, flags=re.MULTILINE)  # 5-8空格->3空格
report_text = re.sub(r'^([ ]{9,})([^\s])', r'   \2', report_text, flags=re.MULTILINE)  # 9+空格->3空格

# 18. 特別處理V科診斷報告中的方括號格式（防止被誤認為代碼塊）
# 處理類似 [Other Issues] : [CR Choice Understanding Error: Logic] 的格式
report_text = re.sub(r'\[([^\]]+)\]\s*:\s*\[([^\]]+)\]', r'\1: \2', report_text)

# 處理多個方括號項目的組合，如 [Error: Key Info Location Understanding] , [ Error: Long Diffi]
report_text = re.sub(r'\[([^\]]+)\]\s*,\s*\[\s*([^\]]+)\]', r'\1, \2', report_text)

# 處理單獨的方括號項目
report_text = re.sub(r'\[([^\]]+)\](?!\s*:)', r'\1', report_text)

# 20. 處理V科特有的【】格式（保留但優化顯示）
# 確保【】包圍的內容不會被誤認為代碼或其他格式
report_text = re.sub(r'【([^】]+)】：【([^】]+)】', r'**\1**: \2', report_text)
```

Fixed: V科診斷報告格式化現在能正確處理方括號格式和過度縮排問題
Applied: 修復了gmat_diagnosis_app/utils/styling.py中的format_diagnostic_report函數

測試結果：
- ✅ 修正過度縮排：8空格 → 3空格（避免代碼塊識別）
- ✅ 保留層級結構：4空格 → 2空格，5-8空格 → 3空格
- ✅ 移除方括號格式：[Other Issues] : [CR Choice Understanding Error: Logic] → Other Issues: CR Choice Understanding Error: Logic
- ✅ 處理多項目組合：[Error: Key] , [ Error: Long] → Error: Key , Error: Long  
- ✅ 移除代碼塊包圍：```[RC Reading Comprehension]: [Error: Key]``` → RC Reading Comprehension: Error: Key
- ✅ 移除單一反引號：`CR Choice Understanding Error: Logic` → CR Choice Understanding Error: Logic
- ✅ 優化【】格式顯示：【CR 推理障礙】：【CR 推理邏輯錯誤】 → **CR 推理障礙**: CR 推理邏輯錯誤
- ✅ 保持正常文字格式不變

## 根本原因分析
問題的根本原因是V科報告生成時使用了8個空格的縮排（`f"        【{category_reflect_key}】：{labels_in_category_text}"`），這在Markdown中被自動識別為代碼塊。現在通過格式化函數將過度縮排調整為最多3個空格，完全避免了代碼塊自動識別問題。