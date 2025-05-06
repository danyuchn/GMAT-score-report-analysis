"""
V診斷模塊的報告生成功能

此模塊包含用於V(Verbal)診斷的報告生成函數，
用於將診斷結果組織為格式化報告。
"""

import pandas as pd
from gmat_diagnosis_app.diagnostics.v_modules.translations import translate_v, APPENDIX_A_TRANSLATION_V
from gmat_diagnosis_app.diagnostics.v_modules.utils import format_rate
from gmat_diagnosis_app.diagnostics.v_modules.constants import (
    V_PARAM_CATEGORY_ORDER, 
    V_PARAM_TO_CATEGORY,
    INVALID_DATA_TAG_V
)

def generate_v_summary_report(v_diagnosis_results):
    """Generates the summary report string for the Verbal section."""
    report_lines = []
    report_lines.append("---（基於用戶數據與模擬難度分析）---")
    report_lines.append("")

    # Extract chapters safely
    ch1 = v_diagnosis_results.get('chapter_1', {})
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    ch7 = v_diagnosis_results.get('chapter_7', [])

    # --- Section 1: 時間策略與有效性 ---
    report_lines.append("**1. 時間策略與有效性**")
    time_pressure_detected = ch1.get('time_pressure_status', False)
    invalid_count = ch1.get('invalid_count', 0) # Use invalid_count from results dict

    if time_pressure_detected:
        report_lines.append("- 根據分析，您在語文部分可能處於**時間壓力**下（測驗時間剩餘不多或末尾部分題目作答過快）。")
    else:
        report_lines.append("- 根據分析，您在語文部分未處於明顯的時間壓力下。")

    if invalid_count > 0:
        report_lines.append(f"- 已將 {invalid_count} 道可能因時間壓力影響有效性的題目從詳細分析中排除，以確保診斷準確性。")
        report_lines.append("- 請注意，這些被排除的題目將不會包含在後續的錯誤難度分佈統計和練習建議中。")
    else:
        report_lines.append("- 所有題目數據均被納入詳細分析。")
    report_lines.append("")

    # --- Section 2: 表現概覽 ---
    report_lines.append("**2. 表現概覽（CR vs RC vs Skills）**") # Modified Title
    chapter_2_results = v_diagnosis_results.get('chapter_2', {})
    v_metrics_by_type = chapter_2_results.get('by_type', {})
    v_metrics_by_skill = chapter_2_results.get('by_skill', {}) # Get skill metrics

    # CR vs RC Comparison
    cr_metrics = v_metrics_by_type.get('CR', v_metrics_by_type.get('Critical Reasoning', {})) # Allow both keys
    rc_metrics = v_metrics_by_type.get('RC', v_metrics_by_type.get('Reading Comprehension', {})) # Allow both keys

    cr_error_rate = cr_metrics.get('error_rate')
    cr_overtime_rate = cr_metrics.get('overtime_rate')
    rc_error_rate = rc_metrics.get('error_rate')
    rc_overtime_rate = rc_metrics.get('overtime_rate')

    cr_data_valid = cr_metrics and pd.notna(cr_error_rate) and pd.notna(cr_overtime_rate)
    rc_data_valid = rc_metrics and pd.notna(rc_error_rate) and pd.notna(rc_overtime_rate)

    report_lines.append("**按題型:**")
    if cr_data_valid and rc_data_valid:
        cr_total = cr_metrics.get('total_questions', 0)
        rc_total = rc_metrics.get('total_questions', 0)
        report_lines.append(f"- CR（{cr_total} 題）：錯誤率 {format_rate(cr_error_rate)}，超時率 {format_rate(cr_overtime_rate)}")
        report_lines.append(f"- RC（{rc_total} 題）：錯誤率 {format_rate(rc_error_rate)}，超時率 {format_rate(rc_overtime_rate)}")
        error_diff = abs(cr_error_rate - rc_error_rate)
        overtime_diff = abs(cr_overtime_rate - rc_overtime_rate)
        significant_error = error_diff >= 0.15
        significant_overtime = overtime_diff >= 0.15
        if significant_error or significant_overtime:
            if significant_error:
                report_lines.append(f"  - **錯誤率對比：** {'CR 更高' if cr_error_rate > rc_error_rate else 'RC 更高'}（差異 {format_rate(error_diff)}）")
            if significant_overtime:
                report_lines.append(f"  - **超時率對比：** {'CR 更高' if cr_overtime_rate > rc_overtime_rate else 'RC 更高'}（差異 {format_rate(overtime_diff)}）")
        else:
            report_lines.append("  - CR 與 RC 在錯誤率和超時率上表現相當，無顯著差異。")
    # Handle cases where one or both types are missing valid data
    elif not cr_data_valid and not rc_data_valid:
        report_lines.append("- 因缺乏有效的 CR 和 RC 數據，無法進行比較。")
    elif not cr_data_valid:
        report_lines.append("- 因缺乏有效的 CR 數據，無法進行比較。")
        if rc_data_valid:
             rc_total = rc_metrics.get('total_questions', 0)
             report_lines.append(f"  - （RC（{rc_total} 題）：錯誤率 {format_rate(rc_error_rate)}，超時率 {format_rate(rc_overtime_rate)}）")
    elif not rc_data_valid:
        report_lines.append("- 因缺乏有效的 RC 數據，無法進行比較。")
        if cr_data_valid:
             cr_total = cr_metrics.get('total_questions', 0)
             report_lines.append(f"  - （CR（{cr_total} 題）：錯誤率 {format_rate(cr_error_rate)}，超時率 {format_rate(cr_overtime_rate)}）")

    # >>> MODIFICATION: Add Skill Metrics <<<
    report_lines.append("**按核心技能:**")
    if v_metrics_by_skill and v_metrics_by_skill.get('Unknown Skill') is None and len(v_metrics_by_skill) > 1: # Check if skill data is meaningful
         sorted_skills = sorted([s for s in v_metrics_by_skill if s != 'Unknown Skill'])
         if not sorted_skills:
              report_lines.append("- 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
         else:
            for skill in sorted_skills:
                skill_metrics = v_metrics_by_skill.get(skill, {})
                skill_total = skill_metrics.get('total_questions', 0)
                skill_error_rate = skill_metrics.get('error_rate')
                skill_overtime_rate = skill_metrics.get('overtime_rate')
                skill_display_name = translate_v(skill) # Translate skill name
                report_lines.append(f"- {skill_display_name} ({skill_total} 題): 錯誤率 {format_rate(skill_error_rate)}, 超時率 {format_rate(skill_overtime_rate)}")
    else:
         report_lines.append("- 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
    report_lines.append("")


    # --- Section 3: 核心問題診斷 ---
    report_lines.append("**3. 核心問題診斷（基於觸發的診斷標籤）**")
    diagnosed_df_ch3_raw = ch3.get('diagnosed_dataframe') # Use the stored df
    sfe_triggered_overall = False
    sfe_skills_involved = set()
    triggered_params_all = set() # English codes
    qualitative_analysis_trigger = False
    secondary_evidence_trigger = False # Renamed from qualitative for clarity

    # Populate triggered_params_all from the stored English codes (before drop)
    # Ensure the column exists and iterate safely
    if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
        english_param_lists = diagnosed_df_ch3_raw['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])
        # Flatten the list of lists and filter non-string elements before creating the set
        flat_list = [p for sublist in english_param_lists for p in sublist if isinstance(p, str)]
        triggered_params_all.update(flat_list)
    # Add params from Ch5
    if ch5:
        # Ensure param_triggers contains only strings
        ch5_params = [p for p in ch5.get('param_triggers', []) if isinstance(p, str)]
        triggered_params_all.update(ch5_params)

    # Check for SFE and triggers using the potentially modified diagnosed_df_ch3_raw
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        # Ensure necessary columns exist before iterating
        check_cols_sfe = ['is_sfe', 'question_fundamental_skill', 'time_performance_category', 'diagnostic_params']
        if all(col in diagnosed_df_ch3_raw.columns for col in check_cols_sfe):
             for index, row in diagnosed_df_ch3_raw.iterrows():
                 is_sfe = row.get('is_sfe', False)
                 if is_sfe:
                     sfe_triggered_overall = True
                     skill = row.get('question_fundamental_skill', 'Unknown Skill')
                     if skill != 'Unknown Skill':
                         sfe_skills_involved.add(skill)
                     secondary_evidence_trigger = True # SFE warrants review

                 # Check for qualitative analysis trigger conditions
                 time_cat = row.get('time_performance_category', 'Unknown')
                 if time_cat in ['Normal Time & Wrong', 'Slow & Wrong', 'Slow & Correct']:
                     secondary_evidence_trigger = True # These also warrant review
                     # Safely get current params as a list
                     current_english_params_raw = row.get('diagnostic_params', [])
                     current_english_params = set(p for p in current_english_params_raw if isinstance(p, str)) if isinstance(current_english_params_raw, list) else set()

                     complex_params = {
                         'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
                         'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
                         'RC_REASONING_INFERENCE_WEAKNESS'
                     }
                     if any(p in complex_params for p in current_english_params):
                         qualitative_analysis_trigger = True # Specific trigger for qualitative
                     if time_cat == 'Slow & Correct':
                         qualitative_analysis_trigger = True # Also trigger qualitative

    # Report SFE Summary
    if sfe_triggered_overall:
        sfe_label = translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        sfe_skills_en = sorted(list(sfe_skills_involved))
        # Translate skill names for the report
        sfe_skills_zh = sorted([translate_v(s) for s in sfe_skills_en])
        sfe_note = f"{sfe_label}" + (f"（涉及技能：{', '.join(sfe_skills_zh)}）" if sfe_skills_zh else "")
        report_lines.append(f"- **尤其需要注意：** {sfe_note}。（註：SFE 指在已掌握技能範圍內的題目失誤）")

    # Summarize top other core issues based on frequency (optional enhancement, simple listing for now)
    core_issues_params = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE', INVALID_DATA_TAG_V} # Exclude SFE and Invalid Tag
    if core_issues_params:
        report_lines.append("- **主要問題點（根據觸發標籤推斷）：**")
        report_lines.append("請參考試算表中的診斷標籤") # Replace the detailed list generation
    elif not sfe_triggered_overall:
        report_lines.append("- 未識別出明顯的核心問題模式（基於錯誤及效率分析）。")
    report_lines.append("")


    # --- Section 4: 正確但低效分析 ---
    report_lines.append("**4. 正確但低效分析**")
    cr_slow_correct = ch4.get('cr_correct_slow', {})
    rc_slow_correct = ch4.get('rc_correct_slow', {})
    slow_correct_found = False
    for slow_data, type_name in [(cr_slow_correct, "CR"), (rc_slow_correct, "RC")]:
        if slow_data and slow_data.get('correct_slow_count', 0) > 0:
            count = slow_data['correct_slow_count']
            rate = format_rate(slow_data.get('correct_slow_rate', 'N/A'))
            avg_diff_val = slow_data.get('avg_difficulty_slow', None)
            avg_time_val = slow_data.get('avg_time_slow', None)
            avg_diff = f"{avg_diff_val:.2f}" if avg_diff_val is not None else 'N/A'
            avg_time = f"{avg_time_val:.2f}" if avg_time_val is not None else 'N/A'
            bottleneck = translate_v(slow_data.get('dominant_bottleneck_type', 'N/A'))
            report_lines.append(f"- {type_name}：{count} 題正確但慢（佔比 {rate}）。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。主要瓶頸：{bottleneck}。")
            slow_correct_found = True
    if not slow_correct_found:
        report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 作答模式觀察 ---
    report_lines.append("**5. 作答模式觀察**")
    early_rushing_flag = bool(ch5.get('early_rushing_flag_for_review', False))
    carelessness_issue = bool(ch5.get('carelessness_issue', False))
    fast_wrong_rate = ch5.get('fast_wrong_rate')
    pattern_found = False
    if early_rushing_flag:
         early_rush_param_translated = translate_v('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
         report_lines.append(f"- **提示：** {early_rush_param_translated} - 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏。")
         pattern_found = True
    if carelessness_issue:
        careless_param_translated = translate_v('BEHAVIOR_CARELESSNESS_ISSUE')
        fast_wrong_rate_str = format_rate(fast_wrong_rate) if fast_wrong_rate is not None else "N/A"
        report_lines.append(f"- **提示：** {careless_param_translated} - 分析顯示，「快而錯」的情況佔比較高（{fast_wrong_rate_str}），提示可能需關注答題仔細程度。")
        pattern_found = True
    if not pattern_found:
        report_lines.append("- 未發現明顯的特殊作答模式。")
    report_lines.append("")

    # --- Section 6: 基礎鞏固提示 ---
    report_lines.append("**6. 基礎鞏固提示**")
    override_triggered = ch6.get('skill_override_triggered', {})
    exempted_skills_ch6 = ch6.get('exempted_skills', set()) # Get exempted skills
    triggered_skills = [s for s, triggered in override_triggered.items() if bool(triggered)]

    # Filter out exempted skills from the triggered list for reporting override
    non_exempted_triggered_skills = [s for s in triggered_skills if s not in exempted_skills_ch6]

    if not override_triggered: # Check if dictionary itself exists/is populated
         report_lines.append("- 無法進行技能覆蓋分析（可能缺少數據或計算錯誤）。")
    elif non_exempted_triggered_skills: # Only report if there are non-exempted skills that triggered override
        triggered_skills_en = sorted(non_exempted_triggered_skills)
        # Translate skill names for the report
        triggered_skills_zh = sorted([translate_v(s) for s in triggered_skills_en])
        report_lines.append(f"- **以下核心技能整體表現顯示較大提升空間（錯誤率 > 50%），建議優先系統性鞏固：** {', '.join(triggered_skills_zh)}")
    else:
        report_lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則（或所有觸發的技能均已豁免）。")

    # Report Exempted Skills
    if exempted_skills_ch6:
         exempted_skills_zh = sorted([translate_v(s) for s in exempted_skills_ch6])
         report_lines.append(f"- **已掌握技能（豁免）：** 以下技能表現穩定（全對且無超時），無需特別練習：{', '.join(exempted_skills_zh)}")
    report_lines.append("")


    # --- Section 7: 練習計劃呈現 ---
    report_lines.append("**7. 練習計劃**")
    if ch7:
        for rec in ch7:
             rec_type = rec.get('type')
             rec_text = rec.get('text', '')
             if rec_type in ['skill_header', 'spacer']:
                 report_lines.append(rec_text)
             elif rec_type in ['macro', 'case', 'case_aggregated', 'behavioral']: # Include case_aggregated
                 report_lines.append(f"- {rec_text}")
    else:
        report_lines.append("- 無具體練習建議生成（可能因所有技能均豁免或無觸發項）。")
    report_lines.append("")

    # --- Section 8: 後續行動指引 ---
    report_lines.append("**8. 後續行動指引**")

    # Data Prep for Mapping (needs English codes)
    param_to_positions_v = {}
    skill_to_positions_v = {}
    v_translation_dict = APPENDIX_A_TRANSLATION_V

    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
         param_col_eng = 'diagnostic_params' # Use the English param column name
         if param_col_eng in diagnosed_df_ch3_raw.columns:
             # Ensure necessary mapping columns exist
             map_cols = ['question_position', 'question_fundamental_skill']
             if all(col in diagnosed_df_ch3_raw.columns for col in map_cols):
                 for index, row in diagnosed_df_ch3_raw.iterrows():
                     pos = row.get('question_position')
                     skill = row.get('question_fundamental_skill', 'Unknown Skill')
                     eng_params = row.get(param_col_eng, [])
                     # Ensure eng_params is a list and pos is valid number
                     if not isinstance(eng_params, list): eng_params = []
                     if pos is not None and pd.notna(pos):
                          try:
                              pos = int(pos) # Ensure positions are integers for sorting
                              if skill != 'Unknown Skill':
                                  skill_to_positions_v.setdefault(skill, set()).add(pos)
                              for p in eng_params:
                                  if isinstance(p, str): # Only map string params
                                      param_to_positions_v.setdefault(p, set()).add(pos)
                          except (ValueError, TypeError):
                              continue # Skip if position cannot be converted to int

                 # Convert sets to sorted lists
                 for param in param_to_positions_v: param_to_positions_v[param] = sorted(list(param_to_positions_v[param]))
                 for skill in skill_to_positions_v: skill_to_positions_v[skill] = sorted(list(skill_to_positions_v[skill]))

    # 8.1 Reflection Prompts
    report_lines.append("- **引導反思：**")
    reflection_prompts_v = []

    # Local helpers for context
    def get_pos_context_v(param_keys):
        # Use the param_to_positions_v dictionary defined above
        positions = set().union(*(param_to_positions_v.get(key, set()) for key in param_keys if isinstance(key, str)))
        return f"（涉及題號：{sorted(list(positions))}）" if positions else ""

    def get_relevant_skills_v(param_keys):
        # Use the param_to_positions_v and skill_to_positions_v dictionaries
        relevant_positions = set().union(*(param_to_positions_v.get(key, set()) for key in param_keys if isinstance(key, str)))
        relevant_skills_set = {skill for skill, positions in skill_to_positions_v.items() if not relevant_positions.isdisjoint(positions)}
        # Translate skills for display
        return sorted([translate_v(s) for s in relevant_skills_set])


    # Parameter Groups (using English codes)
    cr_reading_params = ['CR_READING_BASIC_OMISSION', 'CR_READING_DIFFICULTY_STEM', 'CR_READING_TIME_EXCESSIVE']
    cr_reasoning_params = ['CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY', 'CR_REASONING_ABSTRACTION_DIFFICULTY', 'CR_REASONING_PREDICTION_ERROR', 'CR_REASONING_TIME_EXCESSIVE']
    cr_ac_params = ['CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY', 'CR_AC_ANALYSIS_RELEVANCE_ERROR', 'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION', 'CR_AC_ANALYSIS_TIME_EXCESSIVE']
    cr_method_params = ['CR_METHOD_TYPE_SPECIFIC_ERROR', 'CR_METHOD_PROCESS_DEVIATION']
    rc_reading_params = ['RC_READING_SPEED_SLOW_FOUNDATIONAL', 'RC_READING_COMPREHENSION_BARRIER', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_DOMAIN_KNOWLEDGE_GAP', 'RC_READING_VOCAB_BOTTLENECK', 'RC_READING_PRECISION_INSUFFICIENT', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY', 'RC_READING_INFO_LOCATION_ERROR', 'RC_READING_KEYWORD_LOGIC_OMISSION']
    rc_location_params = ['RC_LOCATION_ERROR_INEFFICIENCY', 'RC_LOCATION_TIME_EXCESSIVE']
    rc_reasoning_params = ['RC_REASONING_INFERENCE_WEAKNESS', 'RC_REASONING_TIME_EXCESSIVE']
    rc_ac_params = ['RC_AC_ANALYSIS_DIFFICULTY', 'RC_AC_ANALYSIS_TIME_EXCESSIVE']
    rc_method_params = ['RC_METHOD_INEFFICIENT_READING', 'RC_METHOD_TYPE_SPECIFIC_ERROR']
    behavioral_params = ['BEHAVIOR_CARELESSNESS_ISSUE', 'BEHAVIOR_EARLY_RUSHING_FLAG_RISK', 'BEHAVIOR_GUESSING_HASTY']
    sfe_param = ['FOUNDATIONAL_MASTERY_INSTABILITY_SFE']

    # Generate prompts based on triggered parameters (using triggered_params_all set)
    prompt_groups = [
        (cr_reading_params, "回想 CR 題幹閱讀時，是耗時過長，還是對句子/詞彙理解有偏差？"),
        (cr_reasoning_params, "在 CR 邏輯推理時，是難以識別核心問題、理清論證鏈，還是預判方向錯誤？"),
        (cr_ac_params, "分析 CR 選項時，是難以理解選項本身，判斷相關性失誤，還是容易被強干擾項混淆？"),
        (cr_method_params, "做 CR 題時，是否遵循了標準流程？對於特定題型（如BF、Assumption）的方法是否清晰？"),
        (rc_reading_params, "閱讀 RC 文章時，是基礎速度慢、詞彙/長難句障礙，還是對篇章結構把握不清？"),
        (rc_location_params + rc_reasoning_params + rc_ac_params + rc_method_params, "回答 RC 問題時，是定位耗時/錯誤，推理能力不足，選項辨析困難，還是閱讀/解題方法不當？"),
        (sfe_param, "對於 SFE 問題，回想一下是哪個基礎知識點掌握不牢固導致的失誤？"),
        (behavioral_params, "是否存在因為倉促猜題、開頭搶時間或普遍粗心導致的失誤？")
    ]

    for params_group, prompt_text in prompt_groups:
        triggered_in_group = [p for p in params_group if p in triggered_params_all]
        if triggered_in_group:
            skills_zh = get_relevant_skills_v(triggered_in_group)
            skill_context = f" [`{'，'.join(skills_zh)}`] " if skills_zh else " "
            reflection_prompts_v.append(f"  - {prompt_text}{skill_context}" + get_pos_context_v(triggered_in_group))

    if not reflection_prompts_v:
        reflection_prompts_v.append("  - （本次分析未觸發典型的反思問題，建議結合練習計劃進行）")
    report_lines.extend(reflection_prompts_v)


    # 8.2 Second Evidence Suggestion
    report_lines.append("- **二級證據參考建議：**")
    df_problem = pd.DataFrame() # Re-initialize to ensure clean state
    # Use the potentially modified df from Ch3 results
    diagnosed_df_for_2nd_ev = ch3.get('diagnosed_dataframe')

    # Check necessary columns exist before filtering
    cols_for_2nd_ev_filter = ['is_correct', 'overtime', 'is_invalid'] # Ensure is_invalid exists
    if diagnosed_df_for_2nd_ev is not None and not diagnosed_df_for_2nd_ev.empty and \
       all(col in diagnosed_df_for_2nd_ev.columns for col in cols_for_2nd_ev_filter):
        # --- MODIFICATION START ---
        # Filter for rows that are incorrect OR overtime AND ARE NOT INVALID
        problem_mask = (
            ((diagnosed_df_for_2nd_ev['is_correct'] == False) | (diagnosed_df_for_2nd_ev.get('overtime', False) == True)) &
            (diagnosed_df_for_2nd_ev['is_invalid'] == False) # Explicitly exclude invalid rows
        )
        # --- MODIFICATION END ---
        df_problem = diagnosed_df_for_2nd_ev[problem_mask].copy()

    if not df_problem.empty:
        # This logic will now only operate on the filtered df_problem (valid data)
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
        details_added_2nd_ev = False
        # Check necessary columns for grouping and analysis exist
        cols_for_2nd_ev_analysis = ['time_performance_category', 'question_type', 'question_fundamental_skill', 'diagnostic_params']
        if all(col in df_problem.columns for col in cols_for_2nd_ev_analysis):
            performance_order_en = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct'] # Relevant categories for problems
            df_problem['time_performance_category'] = df_problem['time_performance_category'].fillna('Unknown')

            try:
                # Group by performance category
                grouped_by_performance = df_problem.groupby('time_performance_category') # Use observed=False if pandas allows

                for perf_en in performance_order_en:
                    if perf_en in grouped_by_performance.groups:
                        group_df = grouped_by_performance.get_group(perf_en)
                        if not group_df.empty:
                            perf_zh = translate_v(perf_en)
                            # Get unique types and skills, translate skills for display
                            types_in_group = sorted(group_df['question_type'].dropna().unique())
                            skills_in_group = sorted(group_df['question_fundamental_skill'].dropna().unique())
                            skills_display_zh = sorted([translate_v(s) for s in skills_in_group if s != 'Unknown Skill'])

                            # Get all unique English codes for this group from 'diagnostic_params'
                            all_eng_codes_in_group = set()
                            param_eng_col = 'diagnostic_params' # Use the English code column
                            for labels_list in group_df[param_eng_col]:
                                if isinstance(labels_list, list):
                                    # Add only string parameters, exclude invalid tag
                                    all_eng_codes_in_group.update(p for p in labels_list if isinstance(p, str) and p != INVALID_DATA_TAG_V)

                            # Categorize English codes and translate for display
                            labels_by_category = {category: [] for category in V_PARAM_CATEGORY_ORDER}
                            for code_en in all_eng_codes_in_group:
                                category = V_PARAM_TO_CATEGORY.get(code_en, 'Unknown')
                                labels_by_category[category].append(code_en)

                            label_parts_data = []
                            for category in V_PARAM_CATEGORY_ORDER:
                                category_eng_codes = labels_by_category.get(category, [])
                                if category_eng_codes:
                                    category_zh = translate_v(category)
                                    # Translate the English codes to Chinese for display
                                    category_labels_zh = sorted([translate_v(code) for code in category_eng_codes])
                                    label_parts_data.append((category_zh, category_labels_zh))

                            # Format Report Lines
                            report_lines.append(f"  - **{perf_zh}：** 需關注題型：【{', '.join(types_in_group)}】；涉及技能：【{', '.join(skills_display_zh)}】。")
                            if label_parts_data:
                                report_lines.append("    注意相關問題點：")
                                for category_zh, sorted_labels_zh in label_parts_data:
                                    report_lines.append(f"      - 【{category_zh}：{'、'.join(sorted_labels_zh)}】")
                            details_added_2nd_ev = True
            except Exception as e:
                 # Log error if needed, prevent report generation from crashing
                 print(f"Error during 2nd evidence grouping: {e}")
                 report_lines.append("  - （分組分析時出現內部錯誤）")
                 details_added_2nd_ev = True

        # Report core issues summary (using triggered_params_all calculated earlier)
        core_issue_codes_to_report = set()
        if 'FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params_all:
             core_issue_codes_to_report.add('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # Get top 2 other frequent params (optional enhancement, simplified for now)
        # For simplicity, just list all triggered params grouped by category
        if triggered_params_all:
             other_core_issues = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE', INVALID_DATA_TAG_V}
             if other_core_issues:
                 translated_core_issues = sorted([translate_v(code) for code in other_core_issues])
                 report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題，例如：【{', '.join(translated_core_issues[:5])}...】。") # Show top 5 for brevity
                 details_added_2nd_ev = True

        if not details_added_2nd_ev:
             report_lines.append("  - （本次分析未聚焦到特定的問題類型或技能以供二級證據分析）")
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        report_lines.append("  - (本次分析未發現需要二級證據深入探究的有效問題點)")


    # 8.3 Qualitative Analysis Suggestion
    report_lines.append("- **質化分析建議:**")
    if qualitative_analysis_trigger: # Use the flag set during SFE/Trigger analysis
         report_lines.append("  - *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時（尤其針對耗時過長或涉及複雜推理的題目）。")
         report_lines.append("  - *建議行動：* 可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")
    else:
         report_lines.append("  - (本次分析未觸發深入質化分析的特定建議，但若對任何問題點感到困惑，仍可採用此方法。)")

    report_lines.append("\n--- 報告結束 ---")

    # Final formatting for Chinese punctuation
    final_report_string = "\n".join(report_lines)
    final_report_string = final_report_string.replace(":", "：").replace("(", "（").replace(")", "）").replace("[", "【").replace("]", "】").replace(",", "，").replace(";", "；")
    final_report_string = final_report_string.replace("； ", "；")
    final_report_string = final_report_string.replace("： ", "：")
    final_report_string = final_report_string.replace("...", "…") # Ellipsis

    return final_report_string 