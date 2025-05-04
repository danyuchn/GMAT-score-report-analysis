import pandas as pd
import numpy as np

# --- Q-Specific Constants ---
INVALID_DATA_TAG_Q = "數據無效：用時過短（受時間壓力影響）"

APPENDIX_A_TRANSLATION = {
    # ... (保持不變) ...
    'Q_READING_COMPREHENSION_ERROR': "Quant 閱讀理解: Real 題文字理解錯誤/障礙",
    'Q_PROBLEM_UNDERSTANDING_ERROR': "Quant 題目理解: 數學問題本身理解錯誤",
    'Q_CONCEPT_APPLICATION_ERROR': "Quant 概念應用: 數學觀念/公式應用錯誤/障礙",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Quant 基礎掌握: 應用不穩定 (Special Focus Error)",
    'Q_CALCULATION_ERROR': "Quant 計算: 計算錯誤/障礙",
    'Q_EFFICIENCY_BOTTLENECK_READING': "Quant 效率瓶頸: Real 題閱讀耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': "Quant 效率瓶頸: 概念/公式思考或導出耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': "Quant 效率瓶頸: 計算過程耗時過長/反覆計算",
    'Q_CARELESSNESS_DETAIL_OMISSION': "行為模式: 粗心 - 忽略細節/條件/陷阱",
    'Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'Q_BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 整體粗心問題 (快而錯比例高)",
    'poor_real': "比較表現: Real 題錯誤率顯著偏高",
    'poor_pure': "比較表現: Pure 題錯誤率顯著偏高",
    'slow_real': "比較表現: Real 題超時率顯著偏高",
    'slow_pure': "比較表現: Pure 題超時率顯著偏高",
    'skill_override_triggered': "技能覆蓋: 某核心技能整體表現需基礎鞏固 (錯誤率或超時率>50%)"
}

# --- Q-Specific Helper Functions ---

def _get_translation(param):
    """Helper to get Chinese description, returns param name if not found."""
    return APPENDIX_A_TRANSLATION.get(param, param)

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value)

def _map_difficulty_to_label(difficulty):
    """Maps numeric difficulty (b-value) to descriptive label based on Ch7 rules."""
    # ... (保持不變) ...
    if difficulty is None or pd.isna(difficulty):
        return "未知難度 (Unknown)"
    if difficulty <= -1: return "低難度 (Low) / 505+"
    elif -1 < difficulty <= 0: return "中難度 (Mid) / 555+"
    elif 0 < difficulty <= 1: return "中難度 (Mid) / 605+"
    elif 1 < difficulty <= 1.5: return "中難度 (Mid) / 655+"
    elif 1.5 < difficulty <= 1.95: return "高難度 (High) / 705+"
    elif 1.95 < difficulty <= 2: return "高難度 (High) / 805+"
    else: return f"極高難度 ({difficulty:.2f})"


def _calculate_practice_time_limit(item_time, is_overtime):
    """Calculates the starting practice time limit (Z) based on Ch7 rules."""
    # ... (保持不變) ...
    if item_time is None or pd.isna(item_time): return 2.0
    target_time = 2.0
    base_time = item_time - 0.5 if is_overtime else item_time
    z_raw = np.floor(base_time * 2) / 2
    z = max(z_raw, target_time)
    return z

# --- Q-Specific Root Cause Diagnosis ---

# 參數分配規則字典
PARAM_ASSIGNMENT_RULES = {
    # (time_performance_category, question_type): [param_list]
    ('Fast & Wrong', 'REAL'): ['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_READING_COMPREHENSION_ERROR'],
    ('Fast & Wrong', 'PURE'): ['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR'],
    ('Slow & Wrong', 'REAL'): ['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_EFFICIENCY_BOTTLENECK_READING'],
    ('Slow & Wrong', 'PURE'): ['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR'],
    ('Normal Time & Wrong', 'REAL'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR', 'Q_READING_COMPREHENSION_ERROR'],
    ('Normal Time & Wrong', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR'],
    ('Slow & Correct', 'REAL'): ['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'Q_EFFICIENCY_BOTTLENECK_READING'],
    ('Slow & Correct', 'PURE'): ['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION'],
    # Handle 'Unknown' time category (assign general error types if incorrect)
    ('Unknown', 'REAL'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR', 'Q_READING_COMPREHENSION_ERROR'],
    ('Unknown', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR'],
    # Add entries for correct but unknown time if needed, currently assigns nothing
    ('Unknown', None): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR'], # Fallback if type is None (shouldn't happen)
}
# Default params if incorrect but category/type combo not found above
DEFAULT_INCORRECT_PARAMS = ['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR']

def _diagnose_q_root_causes(df, avg_times, max_diffs):
    """
    Analyzes root causes row-by-row. Adds 'is_sfe', 'time_performance_category',
    and 'diagnostic_params' (raw codes) columns using vectorized ops and dict lookup.
    Handles invalid data tagging.
    """
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = ''
        return df

    # --- Vectorized Calculations for is_sfe and time_performance_category ---
    df['avg_time_for_type'] = df['question_type'].map(avg_times).fillna(2.0)
    numeric_time = pd.to_numeric(df['question_time'], errors='coerce')
    df['is_relatively_fast'] = (numeric_time < (df['avg_time_for_type'] * 0.75)).fillna(False)
    df['is_slow'] = df['overtime'].fillna(False)

    conditions = [
        (df['is_correct'] == True) & (df['is_relatively_fast'] == True),
        (df['is_correct'] == True) & (df['is_slow'] == True),
        (df['is_correct'] == True) & (df['is_relatively_fast'] == False) & (df['is_slow'] == False),
        (df['is_correct'] == False) & (df['is_relatively_fast'] == True),
        (df['is_correct'] == False) & (df['is_slow'] == True),
        (df['is_correct'] == False) & (df['is_relatively_fast'] == False) & (df['is_slow'] == False)
    ]
    choices = [
        'Fast & Correct', 'Slow & Correct', 'Normal Time & Correct',
        'Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong'
    ]
    df['time_performance_category'] = np.select(conditions, choices, default='Unknown')
    df.loc[numeric_time.isna(), 'time_performance_category'] = 'Unknown'

    df['max_correct_diff_for_skill'] = df['question_fundamental_skill'].map(max_diffs).fillna(-np.inf)
    numeric_diff = pd.to_numeric(df['question_difficulty'], errors='coerce')
    df['is_sfe'] = (
        (df['is_correct'] == False) & (df['is_invalid'] == False) &
        (numeric_diff.notna()) & (numeric_diff < df['max_correct_diff_for_skill'])
    ).fillna(False)

    # --- Parameter Assignment using Dictionary Lookup (Loop still needed for combining logic) ---
    all_diagnostic_params = []
    for index, row in df.iterrows():
        current_params = []
        is_sfe = row['is_sfe']
        time_perf_cat = row['time_performance_category']
        q_type = row['question_type']
        is_correct = bool(row.get('is_correct', True))
        is_invalid = bool(row.get('is_invalid', False))

        # 1. Get base parameters from rules dictionary
        lookup_key = (time_perf_cat, q_type)
        # Only apply rules if incorrect or slow & correct
        if not is_correct:
            # Special handling for Unknown time category if incorrect
            if time_perf_cat == 'Unknown':
                 base_params = PARAM_ASSIGNMENT_RULES.get(('Unknown', q_type), DEFAULT_INCORRECT_PARAMS)
            else:
                 base_params = PARAM_ASSIGNMENT_RULES.get(lookup_key, DEFAULT_INCORRECT_PARAMS) # Fallback if combo missing
            current_params.extend(base_params)
        elif time_perf_cat == 'Slow & Correct':
            base_params = PARAM_ASSIGNMENT_RULES.get(lookup_key, []) # Get efficiency params
            current_params.extend(base_params)
        # Other correct categories ('Fast & Correct', 'Normal Time & Correct') get no params from dict

        # 2. Add SFE if applicable (regardless of time)
        if is_sfe:
            # Avoid adding SFE if already present from the rule dictionary (though unlikely)
            if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' not in current_params:
                current_params.append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 3. Remove duplicates and ensure SFE is first
        unique_params = list(dict.fromkeys(current_params)) # Preserve order somewhat
        if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
            unique_params.remove('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
            unique_params.insert(0, 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 4. Add invalid tag if needed
        if is_invalid:
            # Avoid adding duplicate invalid tags
            if INVALID_DATA_TAG_Q not in unique_params:
                 # Insert invalid tag at the end for clarity? Or beginning? Let's try end.
                 unique_params.append(INVALID_DATA_TAG_Q)

        all_diagnostic_params.append(unique_params)

    df['diagnostic_params'] = all_diagnostic_params

    # --- Cleanup and Return ---
    cols_to_drop = ['avg_time_for_type', 'is_relatively_fast', 'is_slow', 'max_correct_diff_for_skill']
    df_final = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

    return df_final


# --- Q-Specific Diagnosis Logic (Chapters 2-6) ---
# Remains largely the same as previous refactoring, focusing on data collection
def _diagnose_q_internal(df_q_valid_diagnosed):
    """Performs detailed Q diagnosis (Chapters 2-6).
       Assumes df_q_valid_diagnosed contains only valid Q data with pre-calculated
       'is_sfe', 'time_performance_category', and 'diagnostic_params_list' columns.
    """
    # ... (保持 _diagnose_q_internal 函數與上一版本精簡後一致) ...
    if df_q_valid_diagnosed.empty:
        return {"chapter2_flags": {}}

    # --- Chapter 2: Real vs Pure Analysis ---
    df_real = df_q_valid_diagnosed[df_q_valid_diagnosed['question_type'] == 'REAL'].copy()
    df_pure = df_q_valid_diagnosed[df_q_valid_diagnosed['question_type'] == 'PURE'].copy()
    num_total_real = len(df_real)
    num_total_pure = len(df_pure)
    num_real_errors = df_real['is_correct'].eq(False).sum()
    num_pure_errors = df_pure['is_correct'].eq(False).sum()
    num_real_overtime = df_real['overtime'].eq(True).sum() if 'overtime' in df_real.columns else 0
    num_pure_overtime = df_pure['overtime'].eq(True).sum() if 'overtime' in df_pure.columns else 0
    wrong_rate_real = num_real_errors / num_total_real if num_total_real > 0 else 0
    wrong_rate_pure = num_pure_errors / num_total_pure if num_total_pure > 0 else 0
    over_time_rate_real = num_real_overtime / num_total_real if num_total_real > 0 else 0
    over_time_rate_pure = num_pure_overtime / num_total_pure if num_total_pure > 0 else 0
    significant_error_diff = abs(num_real_errors - num_pure_errors) >= 2
    significant_overtime_diff = abs(num_real_overtime - num_pure_overtime) >= 2
    ch2_flags = {'poor_real': False, 'poor_pure': False, 'slow_real': False, 'slow_pure': False}
    if significant_error_diff:
        if wrong_rate_real > wrong_rate_pure: ch2_flags['poor_real'] = True
        elif wrong_rate_pure > wrong_rate_real: ch2_flags['poor_pure'] = True
    if significant_overtime_diff:
        if over_time_rate_real > over_time_rate_pure: ch2_flags['slow_real'] = True
        elif over_time_rate_pure > over_time_rate_real: ch2_flags['slow_pure'] = True
    results_ch2_summary = pd.DataFrame([
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Total Questions', 'Real_Value': num_total_real, 'Pure_Value': num_total_pure},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Count', 'Real_Value': num_real_errors, 'Pure_Value': num_pure_errors},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Rate', 'Real_Value': wrong_rate_real, 'Pure_Value': wrong_rate_pure},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Count', 'Real_Value': num_real_overtime, 'Pure_Value': num_pure_overtime},
        {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Rate', 'Real_Value': over_time_rate_real, 'Pure_Value': over_time_rate_pure}
    ])

    # --- Chapter 3: Error Cause Analysis (Simplified: Collect Pre-diagnosed Info) ---
    error_analysis_list = []
    df_errors = df_q_valid_diagnosed[df_q_valid_diagnosed['is_correct'] == False].copy()
    if not df_errors.empty:
        for index, row in df_errors.iterrows():
            error_analysis_list.append({
                'question_position': row['question_position'],
                'Skill': row.get('question_fundamental_skill', 'Unknown Skill'),
                'Type': row['question_type'],
                'Difficulty': row.get('question_difficulty', None),
                'Time': row.get('question_time', None),
                'Time_Performance': row.get('time_performance_category', 'Unknown'),
                'Is_SFE': row.get('is_sfe', False),
                'Possible_Params': row.get('diagnostic_params_list', [])
            })

    # --- Chapter 4: Correct but Slow Analysis ---
    correct_slow_analysis_list = []
    if 'overtime' in df_q_valid_diagnosed.columns:
        df_correct_slow = df_q_valid_diagnosed[(df_q_valid_diagnosed['is_correct'] == True) & (df_q_valid_diagnosed['overtime'] == True)].copy()
        if not df_correct_slow.empty:
            for index, row in df_correct_slow.iterrows():
                correct_slow_analysis_list.append({
                    'question_position': row['question_position'],
                    'Skill': row.get('question_fundamental_skill', 'Unknown Skill'),
                    'Type': row['question_type'],
                    'Time': row.get('question_time', None),
                    'Possible_Params': row.get('diagnostic_params_list', [])
                })

    # --- Chapter 5: Pattern Observation ---
    early_rushing_items = []
    early_rushing_flag = False
    carelessness_issue = False
    fast_wrong_rate = 0.0
    total_number_of_questions = len(df_q_valid_diagnosed)
    if 'question_position' in df_q_valid_diagnosed.columns and 'question_time' in df_q_valid_diagnosed.columns and pd.api.types.is_numeric_dtype(df_q_valid_diagnosed['question_position']) and pd.api.types.is_numeric_dtype(df_q_valid_diagnosed['question_time']):
        first_third_threshold = total_number_of_questions / 3
        df_early = df_q_valid_diagnosed[df_q_valid_diagnosed['question_time'].notna() & (df_q_valid_diagnosed['question_position'] <= first_third_threshold) & (df_q_valid_diagnosed['question_time'] < 1.0)]
        if not df_early.empty:
            early_rushing_flag = True
            rushing_param_translated = _get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
            for index, row in df_early.iterrows():
                early_rushing_items.append({'question_position': row['question_position'], 'Time': row['question_time'], 'Type': row['question_type'], 'Skill': row.get('question_fundamental_skill', 'Unknown Skill'), 'Params': [rushing_param_translated]})
    num_fast_wrong = df_q_valid_diagnosed[df_q_valid_diagnosed['time_performance_category'] == 'Fast & Wrong'].shape[0]
    num_relatively_fast_total = df_q_valid_diagnosed[(df_q_valid_diagnosed['time_performance_category'] == 'Fast & Wrong') | (df_q_valid_diagnosed['time_performance_category'] == 'Fast & Correct')].shape[0]
    if num_relatively_fast_total > 0:
        fast_wrong_rate = num_fast_wrong / num_relatively_fast_total
        if fast_wrong_rate > 0.25: carelessness_issue = True

    # --- Chapter 6: Skill Override Rule ---
    skill_override_flags = {}
    if 'question_fundamental_skill' in df_q_valid_diagnosed.columns and 'overtime' in df_q_valid_diagnosed.columns:
        grouped_by_skill = df_q_valid_diagnosed.groupby('question_fundamental_skill')
        for skill, group in grouped_by_skill:
            if skill == 'Unknown Skill': continue
            num_total_skill = len(group)
            if num_total_skill == 0: continue
            num_errors_skill = group['is_correct'].eq(False).sum()
            num_overtime_skill = group['overtime'].eq(True).sum()
            error_rate_skill = num_errors_skill / num_total_skill
            overtime_rate_skill = num_overtime_skill / num_total_skill
            triggered, min_diff_skill, y_agg, z_agg = False, None, None, 2.5
            if error_rate_skill > 0.5 or overtime_rate_skill > 0.5:
                triggered = True
                problem_items = group[(group['is_correct'] == False) | (group['overtime'] == True)]
                if not problem_items.empty and 'question_difficulty' in problem_items.columns:
                    difficulties = problem_items['question_difficulty'].dropna()
                    if not difficulties.empty:
                        min_diff_skill = difficulties.min()
                        y_agg = _map_difficulty_to_label(min_diff_skill)
            skill_override_flags[skill] = {'triggered': triggered, 'error_rate': error_rate_skill, 'overtime_rate': overtime_rate_skill, 'total_questions': num_total_skill, 'min_diff_skill': min_diff_skill, 'y_agg': y_agg, 'z_agg': z_agg if triggered else None}

    # --- Combine results ---
    final_q_results = {
        "chapter2_summary": results_ch2_summary.to_dict('records'),
        "chapter2_flags": ch2_flags,
        "chapter3_error_details": error_analysis_list,
        "chapter4_correct_slow_details": correct_slow_analysis_list,
        "chapter5_patterns": {"early_rushing_flag": early_rushing_flag, "early_rushing_items": early_rushing_items, "carelessness_issue_flag": carelessness_issue, "fast_wrong_rate": fast_wrong_rate},
        "chapter6_skill_override": skill_override_flags
    }
    return final_q_results


# --- Q-Specific Recommendation Generation (Chapter 7) ---
# Remains the same as previous refactoring
def _generate_q_recommendations(q_diagnosis_results):
    """Generates practice recommendations based on Q diagnosis results (Ch 2-6)."""
    # ... (保持 _generate_q_recommendations 函數與上一版本精簡後一致) ...
    recommendations_by_skill = {}
    processed_override_skills = set()
    all_skills_found = set()
    ch2_flags = q_diagnosis_results.get('chapter2_flags', {})
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})
    poor_real = ch2_flags.get('poor_real', False)
    slow_pure = ch2_flags.get('slow_pure', False)
    triggers = []
    for error in ch3_errors:
        skill = error.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
            triggers.append({'skill': skill, 'difficulty': error.get('Difficulty'), 'time': error.get('Time'), 'is_overtime': error.get('Time_Performance') == 'Slow & Wrong', 'is_sfe': error.get('Is_SFE', False), 'q_position': error.get('question_position'), 'q_type': error.get('Type'), 'trigger_type': 'error'})
            all_skills_found.add(skill)
    for slow in ch4_correct_slow:
        skill = slow.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
            triggers.append({'skill': skill, 'difficulty': None, 'time': slow.get('Time'), 'is_overtime': True, 'is_sfe': False, 'q_position': slow.get('question_position'), 'q_type': slow.get('Type'), 'trigger_type': 'correct_slow'})
            all_skills_found.add(skill)

    for skill in all_skills_found:
        skill_recs_list = []
        is_overridden = ch6_override.get(skill, {}).get('triggered', False)
        if is_overridden and skill not in processed_override_skills:
            override_info = ch6_override.get(skill, {})
            y_agg = override_info.get('y_agg')
            z_agg = override_info.get('z_agg', 2.5)
            if y_agg is None:
                trigger_difficulties = [t['difficulty'] for t in triggers if t['skill'] == skill and t['difficulty'] is not None and not pd.isna(t['difficulty'])]
                min_diff_skill = min(trigger_difficulties) if trigger_difficulties else 0
                y_agg = _map_difficulty_to_label(min_diff_skill)
            macro_rec_text = f"**優先全面鞏固基礎** (整體錯誤率或超時率 > 50%): 從 {y_agg} 難度開始, 建議限時 {z_agg} 分鐘。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_override_skills.add(skill)
        elif not is_overridden:
            skill_triggers = [t for t in triggers if t['skill'] == skill]
            has_real_trigger = any(t.get('q_type') == 'REAL' for t in skill_triggers)
            has_pure_trigger = any(t.get('q_type') == 'PURE' for t in skill_triggers)
            adjustment_text = ""
            for trigger in skill_triggers:
                difficulty = trigger.get('difficulty')
                time = trigger.get('time')
                is_overtime_trigger = trigger.get('is_overtime', False)
                q_position_trigger = trigger.get('q_position', 'N/A')
                trigger_type = trigger.get('trigger_type')
                is_sfe_trigger = trigger.get('is_sfe', False)
                if difficulty is not None and not pd.isna(difficulty):
                    y = _map_difficulty_to_label(difficulty)
                    z = _calculate_practice_time_limit(time, is_overtime_trigger)
                    priority = 1 if is_sfe_trigger else 2
                    trigger_context = f"第 {q_position_trigger} 題相關"
                    practice_details = f"練習 {y}, 限時 {z} 分鐘。"
                    case_rec_text = f"{trigger_context}: {practice_details}"
                    if is_sfe_trigger: case_rec_text = f"*基礎掌握不穩* {case_rec_text}"
                    skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
                elif trigger_type == 'correct_slow':
                    y = "中難度 (Mid) / 605+"
                    q_position_trigger = trigger.get('q_position', 'N/A')
                    time = trigger.get('time')
                    is_overtime_trigger = trigger.get('is_overtime', True)
                    z = _calculate_practice_time_limit(time, is_overtime_trigger)
                    priority = 3
                    trigger_context = f"第 {q_position_trigger} 題相關 (正確但慢)"
                    practice_details = f"練習 {y}, 限時 {z} 分鐘 (提升速度)。"
                    case_rec_text = f"{trigger_context}: {practice_details}"
                    skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
            if poor_real and has_real_trigger: adjustment_text += " **Real題比例建議佔總練習題量2/3。**"
            if slow_pure and has_pure_trigger: adjustment_text += " **建議此考點練習題量增加。**"
            if adjustment_text:
                adj_text = f"整體練習註記: {adjustment_text.strip()}"
                skill_recs_list.append({'type': 'adjustment', 'text': adj_text, 'priority': 4})
        if skill_recs_list:
            recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    final_recommendations = []
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_override_skills else 1, s))
    for skill in sorted_skills:
        recs = recommendations_by_skill[skill]
        final_recommendations.append(f"--- 技能: {skill} ---")
        for rec in recs: final_recommendations.append(f"* {rec['text']}")
        final_recommendations.append("")
    if not final_recommendations:
        final_recommendations.append("根據本次分析，未產生具體的量化練習建議。請參考整體診斷總結。")
    return final_recommendations


# --- Q-Specific Summary Report Generation (Chapter 8) ---
# Decomposed into smaller functions

def _generate_report_section1(ch1_results):
    """Generates Section 1: Opening Summary."""
    lines = ["**1. 開篇總結**"]
    time_pressure_q = ch1_results.get('time_pressure_status', False)
    num_invalid_q = ch1_results.get('invalid_questions_excluded', 0)
    if time_pressure_q:
        lines.append("- 根據分析，您在本輪測驗中可能感受到明顯的時間壓力。")
    else:
        lines.append("- 根據分析，您在本輪測驗中未處於明顯的時間壓力下。")
    if num_invalid_q > 0:
        lines.append(f"- 測驗末尾存在因時間壓力導致作答過快、可能影響數據有效性的跡象 ({num_invalid_q} 題被排除)。")
    else:
        lines.append("- 未發現因時間壓力導致數據無效的跡象。")
    return lines

def _generate_report_section2(ch2_summary, ch2_flags, ch3_errors):
    """Generates Section 2: Performance Overview."""
    lines = ["**2. 表現概覽**"]
    real_stats_error = next((item for item in ch2_summary if item.get('Metric') == 'Error Rate'), None)
    real_stats_ot = next((item for item in ch2_summary if item.get('Metric') == 'Overtime Rate'), None)
    if real_stats_error and real_stats_ot:
        real_err_rate_str = _format_rate(real_stats_error.get('Real_Value', 'N/A'))
        real_ot_rate_str = _format_rate(real_stats_ot.get('Real_Value', 'N/A'))
        pure_err_rate_str = _format_rate(real_stats_error.get('Pure_Value', 'N/A'))
        pure_ot_rate_str = _format_rate(real_stats_ot.get('Pure_Value', 'N/A'))
        lines.append(f"- Real 題表現: 錯誤率 {real_err_rate_str}, 超時率 {real_ot_rate_str}")
        lines.append(f"- Pure 題表現: 錯誤率 {pure_err_rate_str}, 超時率 {pure_ot_rate_str}")

        triggered_ch2_flags_desc = []
        if ch2_flags.get('poor_real', False): triggered_ch2_flags_desc.append(_get_translation('poor_real'))
        if ch2_flags.get('poor_pure', False): triggered_ch2_flags_desc.append(_get_translation('poor_pure'))
        if ch2_flags.get('slow_real', False): triggered_ch2_flags_desc.append(_get_translation('slow_real'))
        if ch2_flags.get('slow_pure', False): triggered_ch2_flags_desc.append(_get_translation('slow_pure'))
        if triggered_ch2_flags_desc:
            lines.append(f"- 比較提示: {'; '.join(triggered_ch2_flags_desc)}")
    else:
        lines.append("- 未能進行 Real vs. Pure 題的詳細比較。")

    if ch3_errors:
        error_difficulties = [err.get('Difficulty') for err in ch3_errors if err.get('Difficulty') is not None and not pd.isna(err.get('Difficulty'))]
        if error_difficulties:
            difficulty_labels = [_map_difficulty_to_label(d) for d in error_difficulties]
            label_counts = pd.Series(difficulty_labels).value_counts().sort_index()
            if not label_counts.empty:
                distribution_str = ", ".join([f"{label} ({count}題)" for label, count in label_counts.items()])
                lines.append(f"- **錯誤難度分佈:** {distribution_str}")
    return lines

def _generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved):
    """Generates Section 3: Core Issue Diagnosis."""
    lines = ["**3. 核心問題診斷**"]
    sfe_param_translated = _get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

    if sfe_triggered:
        sfe_note = f"尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤 ({sfe_param_translated})"
        if sfe_skills_involved:
            sfe_note += f"，涉及技能: {', '.join(sorted(list(sfe_skills_involved)))})"
        else:
            sfe_note += ")"
        lines.append(f"- {sfe_note}，這表明在這些知識點的應用上可能存在穩定性問題。")

    core_issue_summary = []
    param_careless_detail = _get_translation('Q_CARELESSNESS_DETAIL_OMISSION')
    param_concept_app = _get_translation('Q_CONCEPT_APPLICATION_ERROR')
    param_calculation = _get_translation('Q_CALCULATION_ERROR')
    param_problem_under = _get_translation('Q_PROBLEM_UNDERSTANDING_ERROR')
    param_reading_comp = _get_translation('Q_READING_COMPREHENSION_ERROR')
    param_eff_reading = _get_translation('Q_EFFICIENCY_BOTTLENECK_READING')
    param_eff_concept = _get_translation('Q_EFFICIENCY_BOTTLENECK_CONCEPT')
    param_eff_calc = _get_translation('Q_EFFICIENCY_BOTTLENECK_CALCULATION')

    if param_careless_detail in triggered_params_translated:
        core_issue_summary.append(f"傾向於快速作答但出錯，可能涉及{param_careless_detail}。")
    if (param_concept_app in triggered_params_translated or param_problem_under in triggered_params_translated) and not sfe_triggered:
         related_issues = []
         if param_concept_app in triggered_params_translated: related_issues.append(param_concept_app)
         if param_problem_under in triggered_params_translated: related_issues.append(param_problem_under)
         core_issue_summary.append(f"花費了較長時間但仍無法解決部分問題，或對問題理解存在偏差，可能涉及{ ' 或 '.join(related_issues)}。")
    if param_calculation in triggered_params_translated:
        core_issue_summary.append(f"計算錯誤也是失分原因 ({param_calculation})。")
    if param_reading_comp in triggered_params_translated:
        core_issue_summary.append(f"Real題的文字信息理解可能存在障礙 ({param_reading_comp})。")

    efficiency_params_triggered = {p for p in triggered_params_translated if p in [param_eff_reading, param_eff_concept, param_eff_calc]}
    if efficiency_params_triggered:
        efficiency_contexts = []
        if param_eff_reading in efficiency_params_triggered: efficiency_contexts.append("Real題閱讀")
        if param_eff_concept in efficiency_params_triggered: efficiency_contexts.append("概念思考")
        if param_eff_calc in efficiency_params_triggered: efficiency_contexts.append("計算過程")
        core_issue_summary.append("部分題目雖然做對，但在{}等環節耗時過長 ({})，反映了應用效率有待提升。".format(
            "、".join(efficiency_contexts), ", ".join(sorted(list(efficiency_params_triggered)))))

    if core_issue_summary:
        lines.extend([f"- {line}" for line in core_issue_summary])
    elif not sfe_triggered:
        lines.append("- 未識別出主要的核心問題模式。")
    return lines

def _generate_report_section4(ch5_patterns):
    """Generates Section 4: Pattern Observation."""
    lines = ["**4. 模式觀察**"]
    pattern_found = False
    param_early_rush = _get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    param_careless_issue = _get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')

    if ch5_patterns.get('early_rushing_flag', False):
        lines.append(f"- 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。 ({param_early_rush})")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        lines.append(f"- 分析顯示，「快而錯」的情況佔比較高 ({ch5_patterns.get('fast_wrong_rate', 0):.1%})，提示可能需要關注答題的仔細程度，減少粗心錯誤。 ({param_careless_issue})")
        pattern_found = True
    if not pattern_found:
        lines.append("- 未發現明顯的特殊作答模式。")
    return lines

def _generate_report_section5(ch6_override):
    """Generates Section 5: Foundational Consolidation Hint."""
    lines = ["**5. 基礎鞏固提示**"]
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        lines.append(f"- 對於 [{', '.join(sorted(override_skills_list))}] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。")
    else:
        lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    return lines

def _generate_report_section6(q_recommendations, sfe_triggered):
    """Generates Section 6: Practice Plan Presentation."""
    lines = ["**6. 練習計劃呈現**"]
    if q_recommendations:
        if sfe_triggered:
            lines.append("- (注意：涉及「基礎掌握不穩」的建議已優先列出)")
        lines.extend(q_recommendations) # Assumes q_recommendations is already formatted list of strings
    else:
        lines.append("- 無具體練習建議生成。")
    return lines

def _generate_report_section7(triggered_params_translated, param_to_positions, skill_to_positions, sfe_skills_involved, df_diagnosed):
    """Generates Section 7: Follow-up Action Guidance."""
    lines = ["**7. 後續行動指引**"]

    # --- Reflection Prompts ---
    lines.append("- **引導反思:**")
    reflection_prompts = []
    sfe_param_translated = _get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
    param_concept_app = _get_translation('Q_CONCEPT_APPLICATION_ERROR')
    param_problem_under = _get_translation('Q_PROBLEM_UNDERSTANDING_ERROR')
    param_calculation = _get_translation('Q_CALCULATION_ERROR')
    param_eff_calc = _get_translation('Q_EFFICIENCY_BOTTLENECK_CALCULATION')
    param_reading_comp = _get_translation('Q_READING_COMPREHENSION_ERROR')
    param_careless_detail = _get_translation('Q_CARELESSNESS_DETAIL_OMISSION')
    param_careless_issue = _get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')

    def get_pos_context_str_translated(param_keys_translated):
        positions = set().union(*(set(param_to_positions.get(key, [])) for key in param_keys_translated))
        return f" (涉及題號: {sorted(list(positions))})" if positions else ""

    if param_concept_app in triggered_params_translated or sfe_param_translated in triggered_params_translated:
        prompt_skills = set()
        for skill, poses in skill_to_positions.items():
             if any(pos in param_to_positions.get(param_concept_app, []) for pos in poses): prompt_skills.add(skill)
        if sfe_param_translated in triggered_params_translated: prompt_skills.update(sfe_skills_involved)
        skill_context = f" [`{', '.join(sorted(list(prompt_skills)))}`] " if prompt_skills else " "
        reflection_prompts.append(f"  - 回想一下，在做錯的{skill_context}題目時，具體是卡在哪個數學知識點或公式上？是完全沒思路，還是知道方法但用錯了？" + get_pos_context_str_translated([param_concept_app, sfe_param_translated]))
    if param_calculation in triggered_params_translated or param_eff_calc in triggered_params_translated:
        reflection_prompts.append("  - 是計算過程中容易出錯，還是計算速度偏慢？" + get_pos_context_str_translated([param_calculation, param_eff_calc]))
    if param_reading_comp in triggered_params_translated or _get_translation('poor_real') in triggered_params_translated:
        reflection_prompts.append("  - 對於做錯的文字題，是題目本身的陳述讀不懂，還是能讀懂但無法轉化成數學問題？是否存在特定主題或長句子的閱讀困難？" + get_pos_context_str_translated([param_reading_comp]))
    if param_careless_detail in triggered_params_translated or param_careless_issue in triggered_params_translated:
        reflection_prompts.append("  - 回想一下，是否經常因為看錯數字、漏掉條件或誤解題意而失分？" + get_pos_context_str_translated([param_careless_detail]))
    if not reflection_prompts: reflection_prompts.append("  - (本次分析未觸發典型的反思問題，建議結合練習計劃進行)")
    lines.extend(reflection_prompts)

    # --- Secondary Evidence ---
    lines.append("- **二級證據參考建議:**")
    if df_diagnosed is not None and not df_diagnosed.empty and 'time_performance_category' in df_diagnosed.columns and 'is_correct' in df_diagnosed.columns:
        # Filter out invalid data upfront for this section's analysis
        df_problem = df_diagnosed[
            (df_diagnosed['is_invalid'] == False) &
            ((df_diagnosed['is_correct'] == False) | (df_diagnosed.get('overtime', False) == True))
        ].copy()

        if not df_problem.empty:
            lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
            details_added_2nd_ev = False
            performance_order_en = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct', 'Unknown']
            # Group by performance category ONLY on the filtered (valid) problem data
            grouped_by_performance = df_problem.groupby('time_performance_category')

            for perf_en in performance_order_en:
                if perf_en in grouped_by_performance.groups:
                    group_df = grouped_by_performance.get_group(perf_en)
                    if not group_df.empty:
                        perf_zh = perf_en
                        if perf_en == 'Fast & Wrong': perf_zh = "快錯"
                        elif perf_en == 'Slow & Wrong': perf_zh = "慢錯"
                        elif perf_en == 'Normal Time & Wrong': perf_zh = "正常時間錯"
                        elif perf_en == 'Slow & Correct': perf_zh = "慢對"
                        elif perf_en == 'Unknown': perf_zh = "未知時間表現錯題"
                        types_in_group = sorted(list(group_df['question_type'].dropna().unique()))
                        skills_in_group = sorted(list(group_df['question_fundamental_skill'].dropna().unique()))
                        all_labels_in_group = set()
                        if 'diagnostic_params_list' in group_df.columns:
                            for labels_list in group_df['diagnostic_params_list']:
                                if isinstance(labels_list, list):
                                    # Exclude invalid tag if somehow present (should not be due to filter)
                                    valid_labels = {label for label in labels_list if label != _get_translation(INVALID_DATA_TAG_Q.split("：")[0])}
                                    all_labels_in_group.update(valid_labels)
                        sorted_labels_zh = sorted(list(all_labels_in_group))
                        report_line = f"  - **{perf_zh}:** 需關注題型：【{', '.join(types_in_group)}】；涉及技能：【{', '.join(skills_in_group)}】。"
                        if sorted_labels_zh: report_line += f" 注意相關問題點：【{', '.join(sorted_labels_zh)}】。"
                        lines.append(report_line)
                        details_added_2nd_ev = True

            if not details_added_2nd_ev: lines.append("  - (本次分析未聚焦到特定的有效問題類型或技能)")
            lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
        else: lines.append("  - (本次分析未發現需要二級證據深入探究的有效問題點)")
    else:
        lines.append("  - *觸發時機：* 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。")
        lines.append("  - *建議行動：* 為了更精確地定位具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些知識點或題型反覆出現問題。如果樣本不足，請在接下來的做題中注意收集，累積到足夠樣本後再進行分析。")

    # --- Qualitative Analysis ---
    lines.append("- **質化分析建議:**")
    lines.append("  - *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時。")
    qualitative_focus_skills = set()
    if param_concept_app in triggered_params_translated: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get(param_concept_app, []) for pos in poses))
    if param_problem_under in triggered_params_translated: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get(param_problem_under, []) for pos in poses))
    qualitative_focus_area_skills = f"涉及 {', '.join(sorted(list(qualitative_focus_skills)))} 的題目" if qualitative_focus_skills else "某些類型的題目"
    lines.append(f"  - *建議行動：* 如果您對 {qualitative_focus_area_skills} 的錯誤原因仍感困惑，可以嘗試**提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")

    return lines


def _generate_q_summary_report(q_diagnosis_results, q_recommendations, df_diagnosed=None):
    """Generates the final summary report string by calling section generators."""

    # --- Pre-calculate data needed by multiple sections ---
    ch1_results = q_diagnosis_results.get('chapter1_results', {})
    ch2_summary = q_diagnosis_results.get('chapter2_summary', [])
    ch2_flags = q_diagnosis_results.get('chapter2_flags', {})
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch5_patterns = q_diagnosis_results.get('chapter5_patterns', {})
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})

    # Check if core diagnosis results exist (Simplified check)
    core_data_exists = bool(ch1_results or ch2_summary or ch3_errors or ch4_correct_slow)

    if not core_data_exists:
        # Generate minimal report only if absolutely no data was processed
        time_pressure_q = ch1_results.get('time_pressure_status', False)
        num_invalid_q = ch1_results.get('invalid_questions_excluded', 0)
        report_lines = ["---（基於用戶數據與模擬難度分析）---"]
        report_lines.append("\n**1. 開篇總結**")
        if time_pressure_q: report_lines.append("- 根據分析，您在本輪測驗中可能感受到明顯的**時間壓力**。")
        else: report_lines.append("- 根據分析，您在本輪測驗中未處於明顯的時間壓力下。")
        if num_invalid_q > 0: report_lines.append(f"- 測驗末尾存在 {num_invalid_q} 道因時間壓力導致作答過快、可能影響數據有效性的跡象，已從後續詳細分析中排除。")
        else: report_lines.append("- 未發現因時間壓力導致數據無效的跡象，所有題目均納入分析。")
        report_lines.append("\n**2. 表現概覽**"); report_lines.append("- 無充足的有效數據進行表現概覽分析。")
        report_lines.append("\n**3. 核心問題診斷**"); report_lines.append("- 無充足的有效數據進行核心問題診斷。")
        report_lines.append("\n**4. 模式觀察**"); report_lines.append("- 無充足的有效數據進行模式觀察。")
        report_lines.append("\n**5. 基礎鞏固提示**"); report_lines.append("- 無充足的有效數據進行基礎鞏固分析。")
        report_lines.append("\n**6. 練習計劃呈現**"); report_lines.append("- 無法生成練習建議。")
        report_lines.append("\n**7. 後續行動指引**"); report_lines.append("- 無法提供後續行動指引。")
        report_lines.append("\n--- 報告結束 ---")
        final_report_string = "\n\n".join(report_lines)
        final_report_string = final_report_string.replace(":", "：").replace("(", "（").replace(")", "）").replace("[", "【").replace("]", "】").replace(",", "，").replace(";", "；")
        return final_report_string

    # --- Calculate Triggered Params and Mappings ---
    triggered_params_translated = set()
    param_to_positions = {}
    skill_to_positions = {}
    sfe_skills_involved = set()
    sfe_triggered = False

    for err in ch3_errors:
        pos = err.get('question_position'); skill = err.get('Skill', 'Unknown Skill'); params = err.get('Possible_Params', [])
        triggered_params_translated.update(params)
        if skill != 'UK' and pos is not None: skill_to_positions.setdefault(skill, set()).add(pos)
        for p in params: param_to_positions.setdefault(p, set()).add(pos)
        if err.get('Is_SFE', False):
             sfe_triggered = True
             if skill != 'UK': sfe_skills_involved.add(skill)

    for cs in ch4_correct_slow:
        pos = cs.get('question_position'); skill = cs.get('Skill', 'UK'); params = cs.get('Possible_Params', [])
        triggered_params_translated.update(params)
        if skill != 'UK' and pos is not None: skill_to_positions.setdefault(skill, set()).add(pos)
        for p in params: param_to_positions.setdefault(p, set()).add(pos)

    for flag, status in ch2_flags.items():
        if status: triggered_params_translated.add(_get_translation(flag))
    if ch5_patterns.get('early_rushing_flag', False): triggered_params_translated.add(_get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK'))
    if ch5_patterns.get('carelessness_issue_flag', False): triggered_params_translated.add(_get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE'))

    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for skill in skill_to_positions: skill_to_positions[skill] = sorted(list(skill_to_positions[skill]))

    # --- Generate Report Sections ---
    all_report_lines = ["---（基於用戶數據與模擬難度分析）---", ""]
    all_report_lines.extend(_generate_report_section1(ch1_results))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section2(ch2_summary, ch2_flags, ch3_errors))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section4(ch5_patterns))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section5(ch6_override))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section6(q_recommendations, sfe_triggered))
    all_report_lines.append("")
    all_report_lines.extend(_generate_report_section7(triggered_params_translated, param_to_positions, skill_to_positions, sfe_skills_involved, df_diagnosed))

    all_report_lines.append("\n--- 報告結束 ---")

    # --- Final Formatting ---
    final_report_string = "\n\n".join(all_report_lines)
    # Use Chinese punctuation
    final_report_string = final_report_string.replace(":", "：").replace("(", "（").replace(")", "）").replace("[", "【").replace("]", "】").replace(",", "，").replace(";", "；")

    # Specific fixes for generated punctuation if needed (example)
    final_report_string = final_report_string.replace("； ", "；") # Fix space after semicolon if happens
    final_report_string = final_report_string.replace("： ", "：") # Fix space after colon if happens

    return final_report_string


# --- Main Q Diagnosis Entry Point ---
# Remains the same as previous refactoring
def run_q_diagnosis_processed(df_q_processed, q_time_pressure_status=False):
    """
    Runs the diagnostic analysis specifically for the Quantitative section.
    Assumes the input DataFrame has the final 'is_invalid' status after preprocessing and user review.
    """
    print("  Running Quantitative Diagnosis...")
    q_diagnosis_results = {}

    if df_q_processed.empty:
        print("    No Q data provided. Skipping Q diagnosis.")
        return {}, "Quantitative (Q) 部分無數據可供診斷。", pd.DataFrame()

    # --- Chapter 1 Summary Info ---
    num_invalid_q = df_q_processed['is_invalid'].sum() if 'is_invalid' in df_q_processed.columns else 0
    overtime_threshold_q = 2.5 if q_time_pressure_status else 3.0
    chapter1_results = {'time_pressure_status': q_time_pressure_status, 'invalid_questions_excluded': num_invalid_q, 'overtime_threshold_used': overtime_threshold_q}
    q_diagnosis_results['chapter1_results'] = chapter1_results
    q_diagnosis_results['invalid_count'] = num_invalid_q

    # --- Calculate Prerequisites ---
    df_q_valid_pre_diag = df_q_processed[df_q_processed['is_invalid'] == False].copy() if 'is_invalid' in df_q_processed.columns else df_q_processed.copy()
    avg_time_per_type_q = {}
    if not df_q_valid_pre_diag.empty and 'question_time' in df_q_valid_pre_diag.columns and pd.api.types.is_numeric_dtype(df_q_valid_pre_diag['question_time']):
        avg_time_per_type_q = df_q_valid_pre_diag.groupby('question_type')['question_time'].mean().to_dict()
    else: avg_time_per_type_q = {'REAL': 2.0, 'PURE': 2.0}
    max_correct_difficulty_per_skill_q = {}
    df_correct_valid_q = df_q_valid_pre_diag[(df_q_valid_pre_diag['is_correct'] == True)]
    if not df_correct_valid_q.empty and 'question_fundamental_skill' in df_correct_valid_q.columns and 'question_difficulty' in df_correct_valid_q.columns:
        if pd.api.types.is_numeric_dtype(df_correct_valid_q['question_difficulty']):
            max_correct_difficulty_per_skill_q = df_correct_valid_q.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # --- Step 1: Root Cause Diagnosis ---
    df_q_with_raw_diags = _diagnose_q_root_causes(df_q_processed.copy(), avg_time_per_type_q, max_correct_difficulty_per_skill_q)

    # --- Step 2: Translate Diagnostic Codes ---
    df_q_diagnosed = df_q_with_raw_diags
    if 'diagnostic_params' in df_q_diagnosed.columns:
        def translate_q_list(params_list): return [_get_translation(p) for p in params_list] if isinstance(params_list, list) else []
        df_q_diagnosed['diagnostic_params_list'] = df_q_diagnosed['diagnostic_params'].apply(translate_q_list)
        df_q_diagnosed.drop(columns=['diagnostic_params'], inplace=True)
    else:
        if 'diagnostic_params_list' not in df_q_diagnosed.columns: df_q_diagnosed['diagnostic_params_list'] = [[] for _ in range(len(df_q_diagnosed))]

    # --- Step 3: Filter Valid Data for Internal Analysis ---
    df_q_valid_diagnosed = df_q_diagnosed[df_q_diagnosed['is_invalid'] == False].copy()

    # --- Handle Case: No Valid Data Remaining ---
    if df_q_valid_diagnosed.empty:
        print("    No valid Q data remaining after filtering. Skipping detailed Q diagnosis.")
        minimal_report = _generate_q_summary_report(q_diagnosis_results, ["無有效題目可供分析。"], df_q_diagnosed)
        return q_diagnosis_results, minimal_report, df_q_diagnosed

    # --- Step 4: Internal Diagnosis (Chapters 2-6) ---
    q_internal_results = _diagnose_q_internal(df_q_valid_diagnosed)
    q_diagnosis_results.update(q_internal_results)

    # --- Step 5: Generate Recommendations (Chapter 7) ---
    q_recommendations = _generate_q_recommendations(q_diagnosis_results)

    # --- Step 6: Generate Summary Report (Chapter 8) ---
    report_str = _generate_q_summary_report(q_diagnosis_results, q_recommendations, df_q_diagnosed)

    # --- Step 7: Final Return ---
    if 'Subject' not in df_q_diagnosed.columns: df_q_diagnosed['Subject'] = 'Q'
    elif df_q_diagnosed['Subject'].isnull().any() or (df_q_diagnosed['Subject'] != 'Q').any(): df_q_diagnosed['Subject'] = 'Q'

    print("  Quantitative Diagnosis Complete.")
    return q_diagnosis_results, report_str, df_q_diagnosed