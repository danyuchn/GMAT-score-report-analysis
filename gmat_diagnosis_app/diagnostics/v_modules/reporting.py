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
    INVALID_DATA_TAG_V,
    V_TOOL_AI_RECOMMENDATIONS # Import the new constant
)

def generate_v_summary_report(v_diagnosis_results):
    """Generates the summary report string for the Verbal section, structured similarly to DI report."""
    report_lines = []
    report_lines.append("V 科診斷報告詳情") # New overall title
    report_lines.append("---（基於用戶數據與模擬難度分析）---")
    report_lines.append("")

    # Extract chapters safely
    ch1 = v_diagnosis_results.get('chapter_1', {})
    ch2 = v_diagnosis_results.get('chapter_2', {})
    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch4 = v_diagnosis_results.get('chapter_4', {})
    ch5 = v_diagnosis_results.get('chapter_5', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    ch7 = v_diagnosis_results.get('chapter_7', []) # Practice recommendations

    # --- I. 報告總覽與即時反饋 ---
    report_lines.append("**一、 報告總覽與即時反饋**")
    report_lines.append("")

    # A. 作答時間與策略評估
    report_lines.append("* **A. 作答時間與策略評估**")
    time_pressure_detected = ch1.get('time_pressure_status', False)
    if time_pressure_detected:
        report_lines.append("    * 根據分析，您在語文部分可能處於**時間壓力**下（測驗時間剩餘不多或末尾部分題目作答過快）。")
    else:
        report_lines.append("    * 根據分析，您在語文部分未處於明顯的時間壓力下。")
    report_lines.append("") # Spacing after this sub-section content

    # B. 重要註記
    report_lines.append("* **B. 重要註記**")
    invalid_count = ch1.get('invalid_count', 0)
    if invalid_count > 0:
        report_lines.append(f"    * 已將 {invalid_count} 道可能因時間壓力影響有效性的題目從詳細分析中排除，以確保診斷準確性。")
        report_lines.append("    * 請注意，這些被排除的題目將不會包含在後續的錯誤難度分佈統計和練習建議中。")
    else:
        report_lines.append("    * 所有題目數據均被納入詳細分析。")
    report_lines.append("") # Spacing after major section I

    # --- II. 核心表現分析 ---
    report_lines.append("**二、 核心表現分析**")
    report_lines.append("")

    # A. 題型與技能表現概覽
    report_lines.append("* **A. 題型與技能表現概覽**")
    chapter_2_results = v_diagnosis_results.get('chapter_2', {})
    v_metrics_by_type = chapter_2_results.get('by_type', {})
    v_metrics_by_skill = chapter_2_results.get('by_skill', {})

    # CR vs RC Comparison
    cr_metrics = v_metrics_by_type.get('CR', v_metrics_by_type.get('Critical Reasoning', {}))
    rc_metrics = v_metrics_by_type.get('RC', v_metrics_by_type.get('Reading Comprehension', {}))
    cr_error_rate = cr_metrics.get('error_rate')
    cr_overtime_rate = cr_metrics.get('overtime_rate')
    rc_error_rate = rc_metrics.get('error_rate')
    rc_overtime_rate = rc_metrics.get('overtime_rate')
    cr_data_valid = cr_metrics and pd.notna(cr_error_rate) and pd.notna(cr_overtime_rate)
    rc_data_valid = rc_metrics and pd.notna(rc_error_rate) and pd.notna(rc_overtime_rate)

    report_lines.append("    * **按題型 (CR vs RC):**") # Sub-sub-heading
    if cr_data_valid and rc_data_valid:
        cr_total = cr_metrics.get('total_questions', 0)
        rc_total = rc_metrics.get('total_questions', 0)
        report_lines.append(f"        * CR（{cr_total} 題）") # Indented
        report_lines.append(f"        * RC（{rc_total} 題）") # Indented
        error_diff = abs(cr_error_rate - rc_error_rate)
        overtime_diff = abs(cr_overtime_rate - rc_overtime_rate)
        significant_error = error_diff >= 0.15
        significant_overtime = overtime_diff >= 0.15
        if significant_error or significant_overtime:
            report_lines.append("        * **異常情況：**") # Indented
            if significant_error:
                report_lines.append(f"            * 錯誤率：{'CR 顯著高於 RC' if cr_error_rate > rc_error_rate else 'RC 顯著高於 CR'}（差異 {format_rate(error_diff)}）")
            if significant_overtime:
                report_lines.append(f"            * 超時率：{'CR 顯著高於 RC' if cr_overtime_rate > rc_overtime_rate else 'RC 顯著高於 CR'}（差異 {format_rate(overtime_diff)}）")
        else:
            report_lines.append("        * CR 與 RC 在錯誤率和超時率上表現相當，無顯著差異。") # Indented
    elif not cr_data_valid and not rc_data_valid:
        report_lines.append("        * 因缺乏有效的 CR 和 RC 數據，無法進行比較。")
    elif not cr_data_valid:
        report_lines.append("        * 因缺乏有效的 CR 數據，無法進行完整比較。")
        if rc_data_valid:
             rc_total = rc_metrics.get('total_questions', 0)
             report_lines.append(f"            * RC（{rc_total} 題）")
    elif not rc_data_valid:
        report_lines.append("        * 因缺乏有效的 RC 數據，無法進行完整比較。")
        if cr_data_valid:
             cr_total = cr_metrics.get('total_questions', 0)
             report_lines.append(f"            * CR（{cr_total} 題）")
    report_lines.append("") # Space

    report_lines.append("    * **按核心技能:**") # Sub-sub-heading
    if v_metrics_by_skill and v_metrics_by_skill.get('Unknown Skill') is None and len(v_metrics_by_skill) > 1:
         sorted_skills = sorted([s for s in v_metrics_by_skill if s != 'Unknown Skill'])
         if not sorted_skills:
              report_lines.append("        * 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
         else:
            for skill in sorted_skills:
                skill_metrics = v_metrics_by_skill.get(skill, {})
                skill_total = skill_metrics.get('total_questions', 0)
                skill_error_rate = skill_metrics.get('error_rate')
                skill_overtime_rate = skill_metrics.get('overtime_rate')
                skill_display_name = skill
                report_lines.append(f"        * {skill_display_name} ({skill_total} 題)")
                high_error_threshold = 0.5
                high_overtime_threshold = 0.4
                if skill_error_rate > high_error_threshold or skill_overtime_rate > high_overtime_threshold:
                    report_lines.append("            * **異常：**")
                    if skill_error_rate > high_error_threshold:
                        report_lines.append(f"                * 此技能錯誤率偏高")
                    if skill_overtime_rate > high_overtime_threshold:
                        report_lines.append(f"                * 此技能超時率偏高")
    else:
         report_lines.append("        * 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
    report_lines.append("")

    # B. 高頻潛在問題點 (was "核心問題診斷（基於觸發的診斷標籤）")
    report_lines.append("* **B. 高頻潛在問題點**")
    diagnosed_df_ch3_raw = ch3.get('diagnosed_dataframe')
    sfe_triggered_overall = False
    sfe_skills_involved = set()
    triggered_params_all = set()
    # qualitative_analysis_trigger and secondary_evidence_trigger are for internal logic, not directly reported here in DI style.

    if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
        english_param_lists = diagnosed_df_ch3_raw['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])
        flat_list = [p for sublist in english_param_lists for p in sublist if isinstance(p, str)]
        triggered_params_all.update(flat_list)
    if ch5: # ch5 behavior params also contribute to "all_triggered_params"
        ch5_params = [p for p in ch5.get('param_triggers', []) if isinstance(p, str)]
        triggered_params_all.update(ch5_params)

    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        check_cols_sfe = ['is_sfe', 'question_fundamental_skill'] # Simplified check for SFE part
        if all(col in diagnosed_df_ch3_raw.columns for col in check_cols_sfe):
             for index, row in diagnosed_df_ch3_raw.iterrows():
                 if row.get('is_sfe', False):
                     sfe_triggered_overall = True
                     skill = row.get('question_fundamental_skill', 'Unknown Skill')
                     if skill != 'Unknown Skill':
                         sfe_skills_involved.add(skill)
    
    sfe_reported = False
    if sfe_triggered_overall:
        sfe_label = translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        sfe_skills_en = sorted(list(sfe_skills_involved))
        sfe_skills_display = sfe_skills_en
        sfe_note = f"{sfe_label}" + (f"（涉及技能：{', '.join(sfe_skills_display)}）" if sfe_skills_display else "")
        report_lines.append(f"    * {sfe_note}。（註：SFE 指在已掌握技能範圍內的題目失誤）") # DI style bullet
        sfe_reported = True

    core_issues_params_to_report = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE', INVALID_DATA_TAG_V, 'BEHAVIOR_EARLY_RUSHING_FLAG_RISK', 'BEHAVIOR_CARELESSNESS_ISSUE', 'BEHAVIOR_GUESSING_HASTY'}
    
    reported_other_params_count = 0
    if core_issues_params_to_report:
        param_counts = {}
        if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
            for params_list_for_row in diagnosed_df_ch3_raw['diagnostic_params']:
                actual_params_list = [p for p in params_list_for_row if isinstance(p, str)] if isinstance(params_list_for_row, list) else []
                for param_code in actual_params_list:
                    if param_code in core_issues_params_to_report:
                        param_counts[param_code] = param_counts.get(param_code, 0) + 1
        
        if param_counts:
            sorted_params = sorted(param_counts.items(), key=lambda item: -item[1])
            top_params = sorted_params[:5] # V report lists top 5
            for param_code, count in top_params:
                translated_param = translate_v(param_code)
                report_lines.append(f"    * {translated_param} (出現 {count} 次)") # DI style bullet
                reported_other_params_count +=1
            if not top_params and not sfe_reported: # No SFE and no other params from count
                 report_lines.append("    * 未識別出除SFE或行為模式外的特定核心問題模式。")
        elif not sfe_reported: # No SFE and param_counts was empty
             report_lines.append("    * 未識別出除SFE或行為模式外的特定核心問題模式。")
            
    elif not sfe_triggered_overall: # No core_issues_params_to_report AND no SFE
        report_lines.append("    * 未識別出明顯的核心問題模式（基於錯誤及效率分析）。")
    report_lines.append("")

    # C. 正確但低效分析 (V-specific, placed under Core Performance Analysis)
    report_lines.append("* **C. 正確但低效分析**")
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
            skill_breakdown = slow_data.get('skill_breakdown_slow', {})
            if skill_breakdown:
                fundamental_skill = max(skill_breakdown, key=skill_breakdown.get)
            else:
                fundamental_skill = 'Unknown Skill'
            report_lines.append(f"    * {type_name}：{count} 題正確但慢（佔比 {rate}）。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。相關技能：{fundamental_skill}。")
            slow_correct_found = True
    if not slow_correct_found:
        report_lines.append("    * 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # D. 特殊行為模式觀察 (was "作答模式觀察")
    report_lines.append("* **D. 特殊行為模式觀察**")
    early_rushing_flag = bool(ch5.get('early_rushing_flag_for_review', False))
    carelessness_issue = bool(ch5.get('carelessness_issue', False))
    fast_wrong_rate = ch5.get('fast_wrong_rate')
    pattern_found = False
    if early_rushing_flag:
         early_rush_param_translated = translate_v('BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
         report_lines.append(f"    * **提示：** {early_rush_param_translated} - 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏。")
         pattern_found = True
    if carelessness_issue:
        careless_param_translated = translate_v('BEHAVIOR_CARELESSNESS_ISSUE')
        fast_wrong_rate_str = format_rate(fast_wrong_rate) if fast_wrong_rate is not None else "N/A"
        report_lines.append(f"    * **提示：** {careless_param_translated} - 分析顯示，「快而錯」的情況佔比較高（{fast_wrong_rate_str}），提示可能需關注答題仔細程度。")
        pattern_found = True
    if not pattern_found:
        report_lines.append("    * 未發現明顯的特殊作答模式。")
    report_lines.append("") # Spacing after major section II

    # --- III. 練習建議與基礎鞏固 --- (Adapted from DI "宏觀練習建議")
    report_lines.append("**三、 練習建議與基礎鞏固**")
    report_lines.append("")

    # A. 優先鞏固技能 (from V's "基礎鞏固提示")
    report_lines.append("* **A. 優先鞏固技能**")
    override_triggered = ch6.get('skill_override_triggered', {})
    exempted_skills_ch6 = ch6.get('exempted_skills', set())
    triggered_skills = [s for s, triggered in override_triggered.items() if bool(triggered)]
    non_exempted_triggered_skills = [s for s in triggered_skills if s not in exempted_skills_ch6]

    found_consolidation_points = False
    if not override_triggered:
         report_lines.append("    * 無法進行技能覆蓋分析（可能缺少數據或計算錯誤）。")
         found_consolidation_points = True
    elif non_exempted_triggered_skills:
        triggered_skills_en = sorted(non_exempted_triggered_skills)
        triggered_skills_zh = sorted([translate_v(s) for s in triggered_skills_en])
        report_lines.append(f"    * **以下核心技能整體表現顯示較大提升空間（錯誤率 > 50%），建議優先系統性鞏固：** {', '.join(triggered_skills_zh)}")
        found_consolidation_points = True
    else: # This case means override_triggered exists, but non_exempted_triggered_skills is empty
        report_lines.append("    * 未觸發需要優先進行基礎鞏固的技能覆蓋規則（或所有觸發的技能均已豁免）。")
        found_consolidation_points = True # Still a statement was made

    if exempted_skills_ch6:
         exempted_skills_zh = sorted([translate_v(s) for s in exempted_skills_ch6])
         report_lines.append(f"    * **已掌握技能（豁免）：** 以下技能表現穩定（全對且無超時），無需特別練習：{', '.join(exempted_skills_zh)}")
         found_consolidation_points = True
    
    if not found_consolidation_points: # Should not happen if above logic is correct, but as a fallback
        report_lines.append("    * 關於基礎技能鞏固方面無特別提示。")
    report_lines.append("")

    # B. 整體練習方向 (from V's general "練習建議" part of "練習建議與後續行動")
    report_lines.append("")
    report_lines.append("* **B. 整體練習方向**")
    report_lines.append("")
    practice_recommendations = ch7
    if practice_recommendations:
        for rec in practice_recommendations:
            if isinstance(rec, dict):
                text_to_display = rec.get('text')
                rec_type = rec.get('type')
                if rec_type == 'spacer':
                    # For spacers, if their text is empty or None, add a blank line.
                    # Otherwise, format their text (though spacers usually have empty text).
                    if text_to_display:
                        # Check if this is a skill separator line
                        if text_to_display.strip().startswith("--- 技能:") and text_to_display.strip().endswith("---"):
                            report_lines.append(f"    {text_to_display.strip()}") # No bullet point, ensure stripped
                            report_lines.append("") # Add a new line after skill title
                        else:
                            report_lines.append(f"    {text_to_display.strip()}") # Adjusted to no bullet, ensure stripped
                    else: report_lines.append("") # Keep spacer as empty line if no text
                elif text_to_display is not None:
                    report_lines.append(f"    {text_to_display}") # Adjusted to no bullet
                else:
                    report_lines.append(f"    {str(rec)}") # Fallback, Adjusted to no bullet
            else:
                # Handle cases where rec is a string, potentially a skill separator
                if isinstance(rec, str) and rec.strip().startswith("--- 技能:") and rec.strip().endswith("---"):
                    report_lines.append(f"    {rec.strip()}") # No bullet point, ensure stripped
                    report_lines.append("") # Add a new line after skill title
                else:
                    report_lines.append(f"    {str(rec)}") # Adjusted to no bullet
    else:
        report_lines.append("    * 本次分析未產生具體的練習建議。請參考整體診斷和反思部分。")
    report_lines.append("") # Spacing after major section III

    # --- IV. 後續行動與深度反思指引 --- (Matches DI: IV)
    report_lines.append("**四、 後續行動與深度反思指引**")
    report_lines.append("")

    # A. 檢視練習記錄 (二級證據參考) (Matches DI: IV.A, from V's "二級證據參考建議")
    report_lines.append("* **A. 檢視練習記錄 (二級證據參考)**")
    # Extracting original pieces for this section from V's "後續行動建議"
    # Note: qualitative_analysis_trigger and secondary_evidence_trigger were set earlier
    # diagnosed_df_ch3_raw is available
    
    # Mimic DI structure: Purpose, Method, Focus, Note
    report_lines.append("    * **目的：** 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。") # Added Purpose like DI
    report_lines.append("    * **方法：** 建議您按照以下引導反思查看近期的練習記錄，整理相關錯題或超時題目。") # Adapted V's text

    # Focus (Core issues)
    core_issue_text_for_review = [] # Re-calculate for this section's focus
    # Based on V's original logic for "二級證據參考建議"
    # The original V code re-extracts diagnostic_labels for this. We maintain that by re-extracting relevant params.
    # The original V's "core_issue_text" for this part was:
    # for param_code in ['CR_REASONING_CHAIN_ERROR', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']:
    #     if translate_v(param_code) in diagnostic_labels: # diagnostic_labels was populated from all params in diagnosed_df_ch3_raw
    #         core_issue_text_for_review.append(translate_v(param_code))
    # if sfe_triggered_overall:
    #     core_issue_text_for_review.append(translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE'))
    # This requires `diagnostic_labels` to be defined. Let's define it as it was in V for this part.
    current_diagnostic_labels_for_review = set()
    if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
        all_params_temp = []
        for params_list_temp in diagnosed_df_ch3_raw['diagnostic_params']:
            if isinstance(params_list_temp, list): all_params_temp.extend(params_list_temp)
        for param_temp in all_params_temp:
            if isinstance(param_temp, str): current_diagnostic_labels_for_review.add(translate_v(param_temp))
    
    for param_code in ['CR_REASONING_CHAIN_ERROR', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']:
        if translate_v(param_code) in current_diagnostic_labels_for_review:
            core_issue_text_for_review.append(translate_v(param_code))
    if sfe_triggered_overall: # sfe_triggered_overall is already determined
         if translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE') not in core_issue_text_for_review: # Avoid duplicate
            core_issue_text_for_review.append(translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE'))

    if core_issue_text_for_review:
        report_lines.append(f"    * **重點關注：** 題目是否反覆涉及報告第二部分（核心表現分析）指出的核心問題：") # Adapted
        for issue_text in core_issue_text_for_review:
             report_lines.append(f"        * {issue_text}") # DI style list for issues
    else: # Fallback if no specific core issues identified for this section
        report_lines.append(f"    * **重點關注：** 根據核心表現分析，留意常見錯誤類型。")


    report_lines.append("    * **注意：** 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。") # Adapted V's text
    # Fallback from V if no data for this
    if diagnosed_df_ch3_raw is None or diagnosed_df_ch3_raw.empty: # Original V check for this part
        report_lines.clear() # Clear previous lines for this sub-section if no data
        report_lines.append("* **A. 檢視練習記錄 (二級證據參考)**") # Re-add title
        report_lines.append("    * (本次分析未發現需要二級證據深入探究的問題點，或數據不足)")
    report_lines.append("")

    # B. 引導性反思提示 (針對特定技能與表現) (Matches DI: IV.B, from V's "引導反思")
    report_lines.append("* **B. 引導性反思提示 (針對特定技能與表現)**") # Adjusted title slightly for V context (skill vs type)
    # This is V's "NEW LOGIC FOR GUIDED REFLECTION"
    # Replicating V's logic for extracting skills_list, time_performances_list, diagnostic_labels_list, categorized_labels
    fundamental_skills_reflect = set()
    time_performances_reflect = set()
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        if 'question_fundamental_skill' in diagnosed_df_ch3_raw.columns:
            valid_skills = diagnosed_df_ch3_raw['question_fundamental_skill'].dropna().unique()
            for skill in valid_skills:
                if isinstance(skill, str) and skill != 'Unknown Skill': fundamental_skills_reflect.add(skill)
        if 'time_performance_category' in diagnosed_df_ch3_raw.columns:
            valid_perfs = diagnosed_df_ch3_raw['time_performance_category'].dropna().unique()
            for perf in valid_perfs:
                if isinstance(perf, str) and perf != 'Unknown': time_performances_reflect.add(perf)
    
    skills_list_reflect = sorted(list(fundamental_skills_reflect))
    time_performances_list_reflect = sorted(list(time_performances_reflect))
    
    reflection_prompts_generated = False
    prompt_idx = 1 # Moved prompt_idx initialization outside the loops

    if skills_list_reflect and time_performances_list_reflect and diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        filtered_time_performances_reflect = [perf for perf in time_performances_list_reflect if perf not in ['Fast & Correct', 'Normal Time & Correct']]
        
        category_order_reflect = [
            "CR 推理障礙", "CR 方法應用", "CR 選項辨析", "CR 閱讀理解", "CR 題目理解",
            "RC 閱讀理解", "RC方法", "基礎掌握", "效率問題", "數據無效", "行為模式", "其他問題"
        ]
        
        for skill_reflect in skills_list_reflect:
            for time_perf_reflect in filtered_time_performances_reflect:
                # Filter dataframe for the current skill and time_performance combination
                current_combo_df = diagnosed_df_ch3_raw[
                    (diagnosed_df_ch3_raw['question_fundamental_skill'] == skill_reflect) &
                    (diagnosed_df_ch3_raw['time_performance_category'] == time_perf_reflect)
                ]

                if current_combo_df.empty: # Skip if no data for this specific combo
                    continue

                # Extract and translate diagnostic params specific to this combo
                combo_diagnostic_params_raw = []
                if 'diagnostic_params' in current_combo_df.columns:
                    for params_list in current_combo_df['diagnostic_params']:
                        if isinstance(params_list, list):
                            combo_diagnostic_params_raw.extend(p for p in params_list if p != INVALID_DATA_TAG_V and isinstance(p, str))
                
                if not combo_diagnostic_params_raw: # No specific (non-invalid) params for this combo
                    continue
                
                combo_diagnostic_labels_translated = {translate_v(p) for p in set(combo_diagnostic_params_raw)}

                # Categorize these specific translated labels
                categorized_labels_for_combo = {}
                for label_translated in combo_diagnostic_labels_translated:
                    category = None
                    if "CR 推理障礙" in label_translated: category = "CR 推理障礙"
                    elif "CR 方法應用" in label_translated: category = "CR 方法應用"
                    elif "CR 選項辨析" in label_translated: category = "CR 選項辨析"
                    elif "CR 閱讀理解" in label_translated: category = "CR 閱讀理解"
                    elif "CR 題目理解" in label_translated: category = "CR 題目理解"
                    elif "RC 閱讀理解" in label_translated: category = "RC 閱讀理解"
                    elif "RC方法" in label_translated: category = "RC方法"
                    elif "基礎掌握" in label_translated: category = "基礎掌握"
                    elif "效率問題" in label_translated: category = "效率問題"
                    # No need to check for INVALID_DATA_TAG_V here as it was filtered out from combo_diagnostic_params_raw
                    elif "行為模式" in label_translated: category = "行為模式"
                    else: category = "其他問題"
                    if category not in categorized_labels_for_combo: categorized_labels_for_combo[category] = []
                    categorized_labels_for_combo[category].append(label_translated)

                if not categorized_labels_for_combo: # If after categorization, no relevant labels found
                    continue

                # 將時間表現標籤翻譯成中文
                time_perf_translated = translate_v(time_perf_reflect)
                
                report_lines.append(f"    {prompt_idx}. {skill_reflect} ({time_perf_translated})")
                report_lines.append(f"        檢討方向： 找尋考前做題紀錄中此類題目，檢討並反思自己是否有：")
                
                # Add an empty line before categories to prevent Markdown from interpreting as code block
                report_lines.append("")
                
                # Create lines for each category separately (no longer using categories_for_this_prompt_text list)
                category_lines_added = False
                category_lines = []  # 用來收集所有類別行
                
                for category_reflect_key in category_order_reflect:
                    if category_reflect_key in categorized_labels_for_combo and categorized_labels_for_combo[category_reflect_key]:
                        # 針對此類別的標籤做排序
                        sorted_labels = sorted([
                            l.replace(f'{category_reflect_key}: ', '').replace(category_reflect_key, '').strip('【】')
                            for l in categorized_labels_for_combo[category_reflect_key]
                        ])
                        
                        # 將排序好的標籤以【】包圍並以、連接
                        labels_in_category_text = "、".join([f"【{label}】" for label in sorted_labels])
                        
                        if labels_in_category_text:
                            # 每個類別獨立成行，放入臨時列表
                            category_lines.append(f"        【{category_reflect_key}】：{labels_in_category_text}")
                            category_lines_added = True
                
                # 收集好所有類別行後，用兩個換行符加入報告
                if category_lines:
                    # 將所有類別行以雙換行符連接，確保每行在輸出中正確分開
                    joined_categories = "\n\n".join(category_lines)
                    report_lines.append(joined_categories)
                    reflection_prompts_generated = True
                    report_lines.append("")  # 確保與結尾「等問題」有一行空白
                    report_lines.append("        等問題。")
                    report_lines.append("") 
                    prompt_idx +=1
                # If no categories_for_this_prompt_text, this combo won't be added, handled by outer continue statements

    if not reflection_prompts_generated:
        report_lines.append("    * 找尋考前做題紀錄中的錯題和超時題，按照【題型】【內容領域】【時間表現】【診斷標籤】等維度進行分析和反思，找出系統性的問題和改進方向。")
    report_lines.append("") # Spacing after major section IV

    # --- V. 尋求進階協助 (質化分析) --- (Matches DI: V, from V's "質化分析建議")
    report_lines.append("**五、 尋求進階協助 (質化分析)**")
    report_lines.append("")
    # V's logic for qualitative_analysis_trigger
    # Re-evaluate based on original V logic:
    # qualitative_analysis_trigger was set if time_cat in ['Normal Time & Wrong', 'Slow & Wrong', 'Slow & Correct']
    # AND (complex_params were present OR time_cat == 'Slow & Correct')
    # This is complex to re-evaluate here without the full row-wise iteration.
    # For simplicity and to maintain original information, we can use the `qualitative_analysis_trigger`
    # that would have been set by the original logic flow if we were to run it.
    # However, `qualitative_analysis_trigger` was not directly passed into this function, it was calculated inside.
    # Let's use a simplified condition like DI, based on presence of certain complex issues or SFE.
    show_qualitative_suggestion_v = False
    complex_params_codes_v = {
        'CR_REASONING_CHAIN_ERROR', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY',
        'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY',
        'RC_REASONING_INFERENCE_WEAKNESS'
    }
    if sfe_triggered_overall or any(p in triggered_params_all for p in complex_params_codes_v):
        show_qualitative_suggestion_v = True
    # Additionally, V original logic also triggered qualitative for any 'Slow & Correct'
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty and 'time_performance_category' in diagnosed_df_ch3_raw.columns:
        if (diagnosed_df_ch3_raw['time_performance_category'] == 'Slow & Correct').any():
             show_qualitative_suggestion_v = True

    if show_qualitative_suggestion_v:
        report_lines.append("* **建議：** 如果您對報告中指出的某些問題仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")
    else:
        report_lines.append("* 目前分析結果較為清晰，若仍有疑問可隨時提出。")
    report_lines.append("")

    # --- Section for AI Tool Recommendations (Commented out to match DI's handling in summary) ---
    # This part is handled by generate_v_ai_tool_recommendations, which is usually called separately.
    # The original V summary report also had this commented out.
    # """
    # report_lines.append("- **輔助工具與 AI 提示推薦建議：**")
    # ... (rest of V's original commented out AI recommendations)
    # """
    
    return "\n\n".join(report_lines) # V used single newline, DI used single too for lists then \n\n between major sections. Let's try single for now.


# New function for AI tool recommendations based on edited data
# THIS FUNCTION IS NOT BEING MODIFIED, ONLY generate_v_summary_report IS.
def generate_v_ai_tool_recommendations(diagnosed_df_v_subject):
    """Generates AI tool and prompt recommendations based on edited V diagnostic data."""
    recommendation_lines = []
    
    if diagnosed_df_v_subject is None or diagnosed_df_v_subject.empty:
        return "  - (V科無數據可生成AI建議。)"

    if 'diagnostic_params_list' not in diagnosed_df_v_subject.columns:
        return "  - (V科數據缺少 'diagnostic_params_list' 欄位，無法生成AI建議。)"

    all_triggered_param_codes = set()
    if 'is_sfe' in diagnosed_df_v_subject.columns and diagnosed_df_v_subject['is_sfe'].any():
        all_triggered_param_codes.add("V_SFE_GENERAL_ADVICE_CODE") # Example SFE code for V

    for param_list in diagnosed_df_v_subject['diagnostic_params_list']:
        if isinstance(param_list, list):
            for param_text_or_code in param_list:
                all_triggered_param_codes.add(str(param_text_or_code))
    
    all_triggered_param_codes = {code for code in all_triggered_param_codes if code and str(code).strip()}

    if not all_triggered_param_codes:
        recommendation_lines.append("  - (根據您的V科編輯，未觸發特定的工具或 AI 提示建議。)")
        return "\n".join(recommendation_lines)

    try:
        # from .constants import V_TOOL_AI_RECOMMENDATIONS # Ensure this exists
        # from .translations import translate_v # For display name if codes are English
        pass # Assuming V_TOOL_AI_RECOMMENDATIONS is in scope
    except ImportError:
        return "  - (AI建議配置缺失，無法生成V科建議。)"

    recommendation_lines.append("  --- V 科目 AI 輔助建議 ---")
    
    recommended_tools_added_for_v = False
    for param_code_or_text in sorted(list(all_triggered_param_codes)):
        if param_code_or_text in V_TOOL_AI_RECOMMENDATIONS:
            # 判斷參數名稱，確保使用一致的命名風格
            # 如果是英文參數碼，則使用 translate_v 函數進行翻譯
            # 這使參數命名風格與 MD 文件保持一致
            is_english_code = param_code_or_text.isupper() and '_' in param_code_or_text
            display_name = translate_v(param_code_or_text) if is_english_code else param_code_or_text
            recommendation_lines.append(f"  - **若診斷涉及【{display_name}】:**")
            for rec_item in V_TOOL_AI_RECOMMENDATIONS[param_code_or_text]:
                recommendation_lines.append(f"    - {rec_item}")
            recommended_tools_added_for_v = True
            
    if not recommended_tools_added_for_v:
        recommendation_lines.append("  - (根據您的V科編輯，未觸發特定的工具或 AI 提示建議。)")
    
    return "\n".join(recommendation_lines)


# --- Helper function to group parameters by category for detailed table ---
# (This function seems to be related to detailed table generation, not summary report)

def _generate_detailed_diagnostic_table_v(diagnosed_df):
    # Filter for error/overtime questions
    # For each, list: Q#, Type, Skill, Time Perf, Translated Params (grouped by category)
    pass 