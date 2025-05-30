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

--- 