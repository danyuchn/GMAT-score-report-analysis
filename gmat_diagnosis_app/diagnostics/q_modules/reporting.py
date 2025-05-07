"""
Q診斷模塊的報告生成功能

此模塊包含用於Q(Quantitative)診斷的報告生成函數，
用於將診斷結果組織為格式化報告。
"""

import pandas as pd
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation, APPENDIX_A_TRANSLATION
from gmat_diagnosis_app.diagnostics.q_modules.utils import format_rate, map_difficulty_to_label
from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS


def generate_report_section1(ch1_results):
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


def generate_report_section2(ch2_summary, ch2_flags, ch3_errors):
    """Generates Section 2: Performance Overview."""
    lines = ["**2. 表現概覽**"]
    real_stats_error = next((item for item in ch2_summary if item.get('Metric') == 'Error Rate'), None)
    real_stats_ot = next((item for item in ch2_summary if item.get('Metric') == 'Overtime Rate'), None)
    if real_stats_error and real_stats_ot:
        real_err_rate_str = format_rate(real_stats_error.get('Real_Value', 'N/A'))
        real_ot_rate_str = format_rate(real_stats_ot.get('Real_Value', 'N/A'))
        pure_err_rate_str = format_rate(real_stats_error.get('Pure_Value', 'N/A'))
        pure_ot_rate_str = format_rate(real_stats_ot.get('Pure_Value', 'N/A'))
        lines.append(f"- Real 題表現: 錯誤率 {real_err_rate_str}, 超時率 {real_ot_rate_str}")
        lines.append(f"- Pure 題表現: 錯誤率 {pure_err_rate_str}, 超時率 {pure_ot_rate_str}")

        triggered_ch2_flags_desc = []
        if ch2_flags.get('poor_real', False): triggered_ch2_flags_desc.append(get_translation('poor_real'))
        if ch2_flags.get('poor_pure', False): triggered_ch2_flags_desc.append(get_translation('poor_pure'))
        if ch2_flags.get('slow_real', False): triggered_ch2_flags_desc.append(get_translation('slow_real'))
        if ch2_flags.get('slow_pure', False): triggered_ch2_flags_desc.append(get_translation('slow_pure'))
        if triggered_ch2_flags_desc:
            lines.append(f"- 比較提示: {'; '.join(triggered_ch2_flags_desc)}")
    else:
        lines.append("- 未能進行 Real vs. Pure 題的詳細比較。")

    if ch3_errors:
        error_difficulties = [err.get('Difficulty') for err in ch3_errors if err.get('Difficulty') is not None and not pd.isna(err.get('Difficulty'))]
        if error_difficulties:
            difficulty_labels = [map_difficulty_to_label(d) for d in error_difficulties]
            label_counts = pd.Series(difficulty_labels).value_counts().sort_index()
            if not label_counts.empty:
                distribution_str = ", ".join([f"{label} ({count}題)" for label, count in label_counts.items()])
                lines.append(f"- **錯誤難度分佈:** {distribution_str}")
    return lines


def generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved):
    """Generates Section 3: Core Issue Diagnosis."""
    lines = ["**3. 核心問題診斷**"]
    sfe_param_translated = get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

    if sfe_triggered:
        sfe_note = f"尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤 ({sfe_param_translated})"
        if sfe_skills_involved:
            sfe_note += f"，涉及技能: {', '.join(sorted(list(sfe_skills_involved)))})"
        else:
            sfe_note += ")"
        lines.append(f"- {sfe_note}，這表明在這些知識點的應用上可能存在穩定性問題。")

    core_issue_summary = []
    param_careless_detail = get_translation('Q_CARELESSNESS_DETAIL_OMISSION')
    param_concept_app = get_translation('Q_CONCEPT_APPLICATION_ERROR')
    param_calculation = get_translation('Q_CALCULATION_ERROR')
    param_problem_under = get_translation('Q_PROBLEM_UNDERSTANDING_ERROR')
    param_reading_comp = get_translation('Q_READING_COMPREHENSION_ERROR')
    param_eff_reading = get_translation('Q_EFFICIENCY_BOTTLENECK_READING')
    param_eff_concept = get_translation('Q_EFFICIENCY_BOTTLENECK_CONCEPT')
    param_eff_calc = get_translation('Q_EFFICIENCY_BOTTLENECK_CALCULATION')

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


def generate_report_section4(ch5_patterns):
    """Generates Section 4: Pattern Observation."""
    lines = ["**4. 模式觀察**"]
    pattern_found = False
    param_early_rush = get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    param_careless_issue = get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')

    if ch5_patterns.get('early_rushing_flag', False):
        lines.append(f"- 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。 ({param_early_rush})")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        lines.append(f"- 分析顯示，「快而錯」的情況佔比較高 ({ch5_patterns.get('fast_wrong_rate', 0):.1%})，提示可能需要關注答題的仔細程度，減少粗心錯誤。 ({param_careless_issue})")
        pattern_found = True
    if not pattern_found:
        lines.append("- 未發現明顯的特殊作答模式。")
    return lines


def generate_report_section5(ch6_override):
    """Generates Section 5: Foundational Consolidation Hint."""
    lines = ["**5. 基礎鞏固提示**"]
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        lines.append(f"- 對於 [{', '.join(sorted(override_skills_list))}] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。")
    else:
        lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    return lines


def generate_report_section6(q_recommendations, sfe_triggered):
    """Generates Section 6: Practice Plan Presentation."""
    lines = ["**6. 練習計劃呈現**"]
    if q_recommendations:
        if sfe_triggered:
            lines.append("- (注意：涉及「基礎掌握不穩」的建議已優先列出)")
        lines.extend(q_recommendations) # Assumes q_recommendations is already formatted list of strings
    else:
        lines.append("- 無具體練習建議生成。")
    return lines


def generate_report_section7(triggered_params_translated, param_to_positions, skill_to_positions, sfe_skills_involved, df_diagnosed):
    """Generates Section 7: Follow-up Action Guidance."""
    lines = ["**7. 後續行動指引**"]

    # --- Reflection Prompts ---
    lines.append("- **引導反思:**")
    reflection_prompts = []
    sfe_param_translated = get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
    param_concept_app = get_translation('Q_CONCEPT_APPLICATION_ERROR')
    param_problem_under = get_translation('Q_PROBLEM_UNDERSTANDING_ERROR')
    param_calculation = get_translation('Q_CALCULATION_ERROR')
    param_eff_calc = get_translation('Q_EFFICIENCY_BOTTLENECK_CALCULATION')
    param_careless_detail = get_translation('Q_CARELESSNESS_DETAIL_OMISSION')
    param_careless_issue = get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')
    param_reading_comp = get_translation('Q_READING_COMPREHENSION_ERROR')

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
    if param_reading_comp in triggered_params_translated or get_translation('poor_real') in triggered_params_translated:
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
                                    from gmat_diagnosis_app.diagnostics.q_modules.constants import INVALID_DATA_TAG_Q
                                    valid_labels = {label for label in labels_list if label != get_translation(INVALID_DATA_TAG_Q.split("：")[0])}
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


def generate_q_summary_report(results, recommendations, df_final, triggered_params_english):
    """
    Generates the summary report for Q section, based on Chapter 8 guidelines.
    Combines all the diagnostics into a comprehensive yet readable report.
    """
    report_parts = []
    
    # 獲取各章節的診斷結果
    ch1_results = results.get('chapter1_results', {})
    ch2_flags = results.get('chapter2_flags', {})
    ch5_results = results.get('chapter5_patterns', {})
    
    # 計算基本統計信息
    total_q = len(df_final)
    valid_q = len(df_final[df_final['is_invalid'] == False]) if 'is_invalid' in df_final.columns else total_q
    invalid_q = total_q - valid_q
    
    correct_q = df_final[df_final['is_correct'] == True].shape[0] if 'is_correct' in df_final.columns else 0
    incorrect_q = df_final[df_final['is_correct'] == False].shape[0] if 'is_correct' in df_final.columns else 0
    
    correct_valid_q = df_final[(df_final['is_correct'] == True) & (df_final['is_invalid'] == False)].shape[0] if 'is_correct' in df_final.columns and 'is_invalid' in df_final.columns else 0
    incorrect_valid_q = df_final[(df_final['is_correct'] == False) & (df_final['is_invalid'] == False)].shape[0] if 'is_correct' in df_final.columns and 'is_invalid' in df_final.columns else 0
    
    overtime_q = df_final[df_final['overtime'] == True].shape[0] if 'overtime' in df_final.columns else 0
    
    # 計算評分率
    valid_score_rate = round((correct_valid_q / valid_q * 100) if valid_q > 0 else 0, 1)
    
    # 1. 報告標頭
    report_parts.append("=== Quantitative (Q) 部分診斷報告 ===")
    report_parts.append("")
    
    # 2. 第一章：測試條件和有效性
    report_parts.append("--- 第一章：測試條件和資料有效性 ---")
    time_pressure = ch1_results.get('time_pressure_status', False)
    time_pressure_text = "有" if time_pressure else "無"
    overtime_threshold = ch1_results.get('overtime_threshold_used', 2.5)
    report_parts.append(f"* 時間壓力狀態：{time_pressure_text}")
    report_parts.append(f"* 使用的超時閾值：{overtime_threshold} 分鐘")
    if invalid_q > 0:
        report_parts.append(f"* 無效數據題數：{invalid_q} ({invalid_q / total_q * 100:.1f}%)")
    report_parts.append(f"* 有效評分率：{valid_score_rate}% ({correct_valid_q}/{valid_q})")
    report_parts.append("")
    
    # 3. 第二章：Real vs Pure分析
    report_parts.append("--- 第二章：Real vs Pure 問題表現 ---")
    if ch2_flags.get('poor_real', False):
        report_parts.append("* Real 題目表現較差：錯誤率顯著高於 Pure 題目")
    if ch2_flags.get('poor_pure', False):
        report_parts.append("* Pure 題目表現較差：錯誤率顯著高於 Real 題目")
    if ch2_flags.get('slow_real', False):
        report_parts.append("* Real 題目較慢：超時率顯著高於 Pure 題目")
    if ch2_flags.get('slow_pure', False):
        report_parts.append("* Pure 題目較慢：超時率顯著高於 Real 題目")
    
    if not any(ch2_flags.values()):
        report_parts.append("* Real 和 Pure 題型表現無顯著差異")
    report_parts.append("")
    
    # 4. 第五章：特殊行為模式
    report_parts.append("--- 第五章：行為模式識別 ---")
    carelessness_issue = ch5_results.get('carelessness_issue_flag', False)
    fast_wrong_rate = ch5_results.get('fast_wrong_rate', 0.0)
    early_rushing = ch5_results.get('early_rushing_flag', False)
    
    if carelessness_issue:
        report_parts.append(f"* 存在粗心問題：快速作答的錯誤率為 {fast_wrong_rate:.1%}")
    else:
        report_parts.append(f"* 無明顯粗心問題（快錯率：{fast_wrong_rate:.1%}）")
    
    if early_rushing:
        early_rushing_items = ch5_results.get('early_rushing_items', [])
        items_str = ", ".join([str(item) for item in early_rushing_items[:3]])
        if len(early_rushing_items) > 3:
            items_str += f"...（等 {len(early_rushing_items)} 題）"
        report_parts.append(f"* 前期解題過快（題號：{items_str}）：可能影響對題組的熟悉度和準確率")
    else:
        report_parts.append("* 未發現前期過快解題問題")
    report_parts.append("")
    
    # 5. 練習建議
    if recommendations:
        report_parts.append("--- 第七章：練習建議 ---")
        report_parts.extend(recommendations)
        report_parts.append("")
    
    # 6. 最終建議綜述
    report_parts.append("--- 綜合診斷 ---")
    summary_items = []
    
    # 基於第一章
    if invalid_q > 0:
        summary_items.append(f"測試中有 {invalid_q} 題無效數據，可能影響部分診斷精確度")
    
    # 基於第二章
    if ch2_flags.get('poor_real', False):
        summary_items.append("需要加強文字題理解能力")
    if ch2_flags.get('poor_pure', False):
        summary_items.append("需要加強純數學計算能力")
    if ch2_flags.get('slow_real', False) or ch2_flags.get('slow_pure', False):
        summary_items.append("解題速度需要提升")
    
    # 基於第五章
    if carelessness_issue:
        summary_items.append("存在明顯的粗心問題，建議練習時注重細節檢查")
    if early_rushing:
        summary_items.append("測試初期解題過快，建議調整測試節奏，確保題意理解準確")
    
    # 如果沒有特殊問題
    if not summary_items:
        if valid_score_rate >= 80:
            summary_items.append("整體表現優秀")
        elif valid_score_rate >= 60:
            summary_items.append("整體表現良好，仍有改進空間")
        else:
            summary_items.append("整體表現有待提升，請參考具體練習建議")
    
    for item in summary_items:
        report_parts.append(f"* {item}")
    
    # --- Chapter 8: Tool and AI Prompt Recommendations (Added) ---
    report_parts.append("--- 第八章：輔助工具與 AI 提示推薦建議 ---")
    recommended_tools_added = False
    if triggered_params_english: # Check if set is not empty
        sorted_triggered_params = sorted(list(triggered_params_english))
        for param_code in sorted_triggered_params:
            if param_code in Q_TOOL_AI_RECOMMENDATIONS:
                param_translation = APPENDIX_A_TRANSLATION.get(param_code, param_code)
                tool_list_for_param = Q_TOOL_AI_RECOMMENDATIONS[param_code]
                if tool_list_for_param:
                    report_parts.append(f"* 針對問題「{param_translation}」建議:")
                    for tool_or_prompt in tool_list_for_param:
                        report_parts.append(f"  - {tool_or_prompt}")
                    recommended_tools_added = True
    
    if not recommended_tools_added:
        report_parts.append("* (暫無針對性的輔助工具或 AI 提示建議)")
    report_parts.append("")
    
    # 組合完整報告
    return "\n".join(report_parts) 