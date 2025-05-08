"""
Q診斷模塊的報告生成功能

此模塊包含用於Q(Quantitative)診斷的報告生成函數，
用於將診斷結果組織為格式化報告。
"""

import pandas as pd
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation, APPENDIX_A_TRANSLATION
from gmat_diagnosis_app.diagnostics.q_modules.utils import format_rate, map_difficulty_to_label, grade_difficulty_q, calculate_practice_time_limit
from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS, INVALID_DATA_TAG_Q
import re


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
            lines.append(f"- **比較提示**: {'; '.join(triggered_ch2_flags_desc)}")
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
        sfe_note = f"尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤 (**{sfe_param_translated}**)"
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
        core_issue_summary.append(f"傾向於快速作答但出錯，可能涉及**{param_careless_detail}**。")
    if (param_concept_app in triggered_params_translated or param_problem_under in triggered_params_translated) and not sfe_triggered:
         related_issues = []
         if param_concept_app in triggered_params_translated: related_issues.append(f"**{param_concept_app}**")
         if param_problem_under in triggered_params_translated: related_issues.append(f"**{param_problem_under}**")
         core_issue_summary.append(f"花費了較長時間但仍無法解決部分問題，或對問題理解存在偏差，可能涉及{ ' 或 '.join(related_issues)}。")
    if param_calculation in triggered_params_translated:
        core_issue_summary.append(f"計算錯誤也是失分原因 (**{param_calculation}**)。")
    if param_reading_comp in triggered_params_translated:
        core_issue_summary.append(f"Real題的文字信息理解可能存在障礙 (**{param_reading_comp}**)。")

    efficiency_params_triggered = {p for p in triggered_params_translated if p in [param_eff_reading, param_eff_concept, param_eff_calc]}
    if efficiency_params_triggered:
        efficiency_contexts = []
        if param_eff_reading in efficiency_params_triggered: efficiency_contexts.append("Real題閱讀")
        if param_eff_concept in efficiency_params_triggered: efficiency_contexts.append("概念思考")
        if param_eff_calc in efficiency_params_triggered: efficiency_contexts.append("計算過程")
        core_issue_summary.append("部分題目雖然做對，但在{}等環節耗時過長 ({})，反映了應用效率有待提升。".format(
            "、".join(efficiency_contexts), ", ".join([f"**{p}**" for p in sorted(list(efficiency_params_triggered))])))

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
        lines.append(f"- 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。 (**{param_early_rush}**)")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        lines.append(f"- 分析顯示，「快而錯」的情況佔比較高 ({ch5_patterns.get('fast_wrong_rate', 0):.1%})，提示可能需要關注答題的仔細程度，減少粗心錯誤。 (**{param_careless_issue}**)")
        pattern_found = True
    if not pattern_found:
        lines.append("- 未發現明顯的特殊作答模式。")
    return lines


def generate_report_section5(ch6_override):
    """Generates Section 5: Foundational Consolidation Hint."""
    lines = ["**5. 基礎鞏固提示**"]
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        lines.append(f"- 對於 [**{', '.join(sorted(override_skills_list))}**] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。")
    else:
        lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    return lines


def generate_report_section6(q_recommendations, sfe_triggered):
    """Generates Section 6: Practice Plan Presentation."""
    lines = ["**6. 練習計劃呈現**"]
    if q_recommendations:
        if sfe_triggered:
            lines.append("- (注意：涉及「**基礎掌握不穩**」的建議已優先列出)")
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
    param_careless_interpretation = get_translation('Q_CARELESSNESS_INTERPRETATION_ERROR')
    param_strategy_selection = get_translation('Q_STRATEGY_SELECTION_ERROR')
    
    # 定義獲取位置上下文的輔助函數
    def get_pos_context_str_translated(positions):
        return f" (涉及題號: {sorted(list(positions))})" if positions else ""
    
    # 提取推薦的技能和時間表現（如果可用）
    recommended_skill = "Rates/Ratio/Percent"  # 預設值
    question_type = "Real"  # 預設值
    time_performance = "慢錯"  # 預設值
    diagnostic_label = "診斷標籤"  # 預設值
    
    # 從診斷數據中提取最常見的技能、問題類型和時間表現
    if df_diagnosed is not None and not df_diagnosed.empty:
        # 提取最常見的技能
        if 'question_fundamental_skill' in df_diagnosed.columns:
            skill_counts = df_diagnosed['question_fundamental_skill'].value_counts()
            if not skill_counts.empty:
                recommended_skill = skill_counts.index[0]
        
        # 提取最常見的問題類型
        if 'question_type' in df_diagnosed.columns:
            type_counts = df_diagnosed['question_type'].value_counts()
            if not type_counts.empty:
                question_type = type_counts.index[0]
        
        # 提取最常見的時間表現
        if 'time_performance_category' in df_diagnosed.columns:
            perf_counts = df_diagnosed['time_performance_category'].value_counts()
            if not perf_counts.empty and perf_counts.index[0] != 'Unknown':
                perf = perf_counts.index[0]
                if perf == 'Fast & Wrong': time_performance = "快錯"
                elif perf == 'Slow & Wrong': time_performance = "慢錯"
                elif perf == 'Normal Time & Wrong': time_performance = "正常時間錯"
                elif perf == 'Slow & Correct': time_performance = "慢對"
        
        # 提取最常見的診斷標籤
        if 'diagnostic_params_list' in df_diagnosed.columns:
            all_labels = []
            for labels_list in df_diagnosed['diagnostic_params_list']:
                if isinstance(labels_list, list):
                    all_labels.extend(labels_list)
            if all_labels:
                from collections import Counter
                label_counts = Counter(all_labels)
                if label_counts:
                    diagnostic_label = max(label_counts.items(), key=lambda x: x[1])[0]
    
    # 添加已有的反思提示
    if sfe_param_translated in triggered_params_translated:
        sfe_skills_str = ", ".join(sorted(sfe_skills_involved)) if sfe_skills_involved else "任何相關基礎技能"
        skill_context = f"**{sfe_skills_str}** 的基礎知識點" if sfe_skills_involved else "**相關基礎知識點**"
        reflection_prompts.append(f"  - **基礎掌握不穩定:** 請檢視{skill_context}。對於每個基礎知識點，問自己：我能否不看參考資料，流暢且無錯誤地複述其定義、公式、關鍵性質？能否在 30 秒內快速識別應用場景？")

    if param_concept_app in triggered_params_translated:
        pos_str = get_pos_context_str_translated(param_to_positions.get(param_concept_app, []))
        reflection_prompts.append(f"  - **概念應用錯誤:** 反思{pos_str}的錯誤，您是否了解題目要求的數學概念，但無法靈活應用？可能是知識點學習停留在理解階段，未達熟練應用階段。試著解釋：「我知道要用什麼概念，但卡在哪一步實際操作？」")

    if param_problem_under in triggered_params_translated:
        pos_str = get_pos_context_str_translated(param_to_positions.get(param_problem_under, []))
        reflection_prompts.append(f"  - **題意理解錯誤:** 分析{pos_str}的錯誤，問題是否出在誤解題目意圖、條件或限制？回顧這些題目時，找出您理解有誤的特定部分，並確認：「下次遇到類似表述時，我需要注意哪些關鍵字或關係？」")

    if param_calculation in triggered_params_translated:
        pos_str = get_pos_context_str_translated(param_to_positions.get(param_calculation, []))
        reflection_prompts.append(f"  - **計算錯誤:** 檢視{pos_str}的錯誤，確認計算過程中的具體問題點：是運算符號錯誤、數字抄寫錯誤、還是公式套用錯誤？對於每次發現的計算錯誤，記錄下具體錯誤類型，尋找個人計算模式中的弱點。")

    if param_eff_calc in triggered_params_translated:
        pos_str = get_pos_context_str_translated(param_to_positions.get(param_eff_calc, []))
        reflection_prompts.append(f"  - **計算效率瓶頸:** 針對{pos_str}的題目，您的計算過程是否過於冗長或繁瑣？嘗試拆解您的解題路徑：「我有沒有遺漏更簡潔的解法？是否有不必要的中間步驟？」考慮是否能通過代數技巧、數字特性或估算來簡化運算。")

    if param_careless_detail in triggered_params_translated or param_careless_interpretation in triggered_params_translated:
        pos_careless_detail = param_to_positions.get(param_careless_detail, [])
        pos_careless_interp = param_to_positions.get(param_careless_interpretation, [])
        all_careless_pos = list(set(pos_careless_detail + pos_careless_interp))
        pos_str = get_pos_context_str_translated(all_careless_pos)
        reflection_prompts.append(f"  - **粗心問題:** 回顧{pos_str}的錯誤，具體分析「粗心」的本質：是單純的符號抄錯、還是解題途中失去對題目核心的關注？對於每道粗心導致的錯題，找出您解題過程中的關鍵轉折點，並思考：「我在哪一步開始偏離正確方向？這種偏離有什麼特定模式或前兆？」")

    if param_strategy_selection in triggered_params_translated:
        pos_str = get_pos_context_str_translated(param_to_positions.get(param_strategy_selection, []))
        reflection_prompts.append(f"  - **策略選擇錯誤:** 針對{pos_str}的題目，回顧您當時選擇的解題路徑，與更優解法對比：「我是否陷入複雜計算而忽略了更直接的方法？我對某些常見解題策略的識別是否自動化？」思考您的策略選擇過程，確認是缺乏特定解法知識，還是未能迅速識別適用場景。")

    # 添加找尋特定技能和題型考前做題記錄的反思提示
    reflection_prompts.append(f"  - **考前做題記錄檢視:** 找尋【{recommended_skill}】＋【{question_type}】的考前做題紀錄，針對【{time_performance}】的題目，檢討並反思自己是否有【{diagnostic_label}】等問題並進一步細分確實考點。")

    if reflection_prompts:
        lines.extend(reflection_prompts)
    else:
        lines.append("  - (本次分析未觸發針對性反思提示)")
        lines.append("  - 建議您仍針對錯題和超時題，分析是否有知識點不熟、題意理解有誤、或解題策略不佳等問題。")

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
                        if perf_en == 'Fast & Wrong': perf_zh = "**快錯**"
                        elif perf_en == 'Slow & Wrong': perf_zh = "**慢錯**"
                        elif perf_en == 'Normal Time & Wrong': perf_zh = "**正常時間錯**"
                        elif perf_en == 'Slow & Correct': perf_zh = "**慢對**"
                        elif perf_en == 'Unknown': perf_zh = "**未知時間表現錯題**"
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
                        report_line = f"  - {perf_zh}: 需關注題型：【{', '.join(types_in_group)}】；涉及技能：【{', '.join(skills_in_group)}】。"
                        if sorted_labels_zh: report_line += f" 注意相關問題點：【{', '.join(sorted_labels_zh)}】。"
                        lines.append(report_line)
                        details_added_2nd_ev = True

            if not details_added_2nd_ev: lines.append("  - (本次分析未聚焦到特定的有效問題類型或技能)")
            lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
        else: lines.append("  - (本次分析未發現需要二級證據深入探究的有效問題點)")
    else:
        lines.append("  - **觸發時機:** 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。")
        lines.append("  - **建議行動:** 為了更精確地定位具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些知識點或題型反覆出現問題。如果樣本不足，請在接下來的做題中注意收集，累積到足夠樣本後再進行分析。")

    # --- Qualitative Analysis ---
    lines.append("- **質化分析建議:**")
    lines.append("  - **觸發時機:** 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時。")
    qualitative_focus_skills = set()
    if param_concept_app in triggered_params_translated: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get(param_concept_app, []) for pos in poses))
    if param_problem_under in triggered_params_translated: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get(param_problem_under, []) for pos in poses))
    qualitative_focus_area_skills = f"涉及 **{', '.join(sorted(list(qualitative_focus_skills)))}** 的題目" if qualitative_focus_skills else "某些類型的題目"
    lines.append(f"  - **建議行動:** 如果您對 {qualitative_focus_area_skills} 的錯誤原因仍感困惑，可以嘗試**提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")

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
    
    
    # 2. 第一章：測試條件和有效性
    report_parts.append("**測試條件和資料有效性**")
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
    report_parts.append("**Real vs Pure 問題表現**")
    if ch2_flags.get('poor_real', False):
        report_parts.append("* Real 題目表現較差：錯誤率顯著高於 Pure 題目")
    if ch2_flags.get('poor_pure', False):
        report_parts.append("* Pure 題目表現較差：錯誤率顯著高於 Real 題目")
    if ch2_flags.get('slow_real', False):
        report_parts.append("* Real 題目較慢：超時率顯著高於 Pure 題目")
    if ch2_flags.get('slow_pure', False):
        report_parts.append("* Pure 題目較慢：超時率顯著高於 Pure 題目")
    
    if not any(ch2_flags.values()):
        report_parts.append("* Real 和 Pure 題型表現無顯著差異")
    report_parts.append("")
    
    # 4. 第五章：特殊行為模式
    report_parts.append("**行為模式識別**")
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
        report_parts.append("**練習建議**")
        report_parts.extend(recommendations)
        report_parts.append("")
    
    # 6. 最終建議綜述
    report_parts.append("**綜合診斷**")
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
    report_parts.append("")
    
    # 7. 引導反思
    report_parts.append("**引導反思**")
    
    # 定義時間表現類型
    time_performances = [
        {'en': 'Slow & Wrong', 'zh': '慢錯'},
        {'en': 'Fast & Wrong', 'zh': '快錯'},
        {'en': 'Normal Time & Wrong', 'zh': '正常時間錯'},
        {'en': 'Slow & Correct', 'zh': '慢對'}
    ]
    
    # 獲取常見問題類型和診斷標籤
    common_skills = {}
    common_question_types = {}
    common_diagnostic_labels = {}
    existing_performances = set()  # 追蹤實際存在的時間表現類型
    
    # 從df_final提取數據
    if df_final is not None and not df_final.empty and 'time_performance_category' in df_final.columns:
        # 準備數據分析
        valid_df = df_final[df_final['is_invalid'] == False].copy() if 'is_invalid' in df_final.columns else df_final.copy()
        
        # 查找數據中存在的時間表現類型
        existing_performances = set(valid_df['time_performance_category'].unique())
        
        # 為每種時間表現類別找出最常見的技能和題型
        for perf in time_performances:
            perf_en = perf['en']
            if perf_en not in existing_performances:
                continue  # 跳過不存在的時間表現類型
                
            perf_df = valid_df[valid_df['time_performance_category'] == perf_en]
            
            # 提取最常見的技能
            if not perf_df.empty and 'question_fundamental_skill' in perf_df.columns:
                skill_counts = perf_df['question_fundamental_skill'].value_counts()
                if not skill_counts.empty:
                    common_skills[perf_en] = skill_counts.index[0]
                else:
                    common_skills[perf_en] = "Rates/Ratio/Percent"  # 預設值
            else:
                common_skills[perf_en] = "Rates/Ratio/Percent"  # 預設值
            
            # 提取最常見的問題類型
            if not perf_df.empty and 'question_type' in perf_df.columns:
                type_counts = perf_df['question_type'].value_counts()
                if not type_counts.empty:
                    common_question_types[perf_en] = type_counts.index[0]
                else:
                    common_question_types[perf_en] = "Real"  # 預設值
            else:
                common_question_types[perf_en] = "Real"  # 預設值
            
            # 提取最常見的診斷標籤
            if not perf_df.empty and 'diagnostic_params_list' in perf_df.columns:
                all_labels = []
                for labels_list in perf_df['diagnostic_params_list']:
                    if isinstance(labels_list, list):
                        all_labels.extend(labels_list)
                if all_labels:
                    from collections import Counter
                    label_counts = Counter(all_labels)
                    if label_counts:
                        # Exclude INVALID_DATA_TAG_Q if present
                        if INVALID_DATA_TAG_Q in label_counts:
                            del label_counts[INVALID_DATA_TAG_Q]
                        if label_counts: # Check if still non-empty
                            common_diagnostic_labels[perf_en] = label_counts.most_common(1)[0][0]
                        else:
                            common_diagnostic_labels[perf_en] = "無特定標籤" # Default if only invalid tags were present
                    else:
                        common_diagnostic_labels[perf_en] = "無特定標籤" # 預設值
                else:
                    common_diagnostic_labels[perf_en] = "無特定標籤" # 預設值
            else:
                common_diagnostic_labels[perf_en] = "無特定標籤" # 預設值
    
    # 生成引導反思問題
    for perf in time_performances:
        perf_en = perf['en']
        perf_zh = perf['zh']
        
        # 只為實際存在的時間表現類型生成問題
        if perf_en not in existing_performances:
            continue
            
        skill = common_skills.get(perf_en, "代數")
        q_type = common_question_types.get(perf_en, "文字題")
        label = common_diagnostic_labels.get(perf_en, "概念應用錯誤")
        
        report_parts.append(f"* 當出現 **{perf_zh}** 時，通常是 **{skill}** 方面的 **{q_type}** 題，診斷為 **{label}**，您認為可能的原因是什麼？")
    report_parts.append("")

    # 7. AI工具和提示建議（這部分將被新的獨立函數取代，但保留結構以便參考）
    # """
    # report_parts.append("**輔助工具與 AI 提示推薦建議：**")
    # report_parts.append("  - 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些可能適用的輔助工具和 AI 提示。系統会根据您触发的诊断参数组合，推荐相关的资源。请根据您的具体诊断结果选用。")
    # recommended_tools_added = False
    # if triggered_params_english:
    #     for param_code in triggered_params_english: # Iterate over unique triggered English param codes
    #         if param_code in Q_TOOL_AI_RECOMMENDATIONS:
    #             param_zh = get_translation(param_code)
    #             report_parts.append(f"  - **若診斷涉及【{param_zh}】:**")
    #             for rec_item in Q_TOOL_AI_RECOMMENDATIONS[param_code]:
    #                 report_parts.append(f"    - {rec_item}")
    #             recommended_tools_added = True
    # if not recommended_tools_added:
    #     report_parts.append("  - (本次分析未觸發特定的工具或 AI 提示建議。)")
    # report_parts.append("")
    # """
    
    return "\n".join(report_parts)


def generate_q_ai_tool_recommendations(diagnosed_df_q_subject):
    """Generates AI tool and prompt recommendations based on edited Q diagnostic data."""
    recommendation_lines = []
    
    if diagnosed_df_q_subject is None or diagnosed_df_q_subject.empty:
        return "  - (Q科無數據可生成AI建議。)"

    # Ensure 'diagnostic_params_list' column exists
    if 'diagnostic_params_list' not in diagnosed_df_q_subject.columns:
        return "  - (Q科數據缺少 'diagnostic_params_list' 欄位，無法生成AI建議。)"

    # Aggregate all unique diagnostic parameter codes (assuming they are English codes here)
    # And also check for SFE flags directly from the boolean column
    all_triggered_param_codes = set()
    sfe_is_present_in_edited_data = False
    if 'is_sfe' in diagnosed_df_q_subject.columns and diagnosed_df_q_subject['is_sfe'].any():
        sfe_is_present_in_edited_data = True
        # Add a generic SFE code if SFE is present, to trigger SFE-related general advice
        # This code needs to be a key in Q_TOOL_AI_RECOMMENDATIONS
        all_triggered_param_codes.add("Q_SFE_GENERAL_ADVICE_CODE") # Example SFE code

    for param_list in diagnosed_df_q_subject['diagnostic_params_list']:
        if isinstance(param_list, list):
            for param_text_or_code in param_list:
                # We need a robust way to get the English CODE if param_text_or_code is Chinese text.
                # For now, assuming param_text_or_code might be an English code or we adapt Q_TOOL_AI_RECOMMENDATIONS keys.
                # Let's assume for now that diagnostic_params_list contains codes that can be used as keys.
                # Or, if they are Chinese, Q_TOOL_AI_RECOMMENDATIONS should use Chinese keys.
                # To simplify, this placeholder will assume param_text_or_code is usable.
                # This is a CRITICAL part to get right based on actual data in diagnostic_params_list.
                # For now, let's assume `diagnostic_params_list` could contain English codes from the original diagnosis
                # or user-added text. We should prioritize codes if they match.
                all_triggered_param_codes.add(str(param_text_or_code)) 
    
    # Remove any None or empty string codes if they accidentally got in
    all_triggered_param_codes = {code for code in all_triggered_param_codes if code and str(code).strip()}

    if not all_triggered_param_codes:
        recommendation_lines.append("  - (根據您的Q科編輯，未觸發特定的工具或 AI 提示建議。)")
        return "\n".join(recommendation_lines)

    # Ensure Q_TOOL_AI_RECOMMENDATIONS is available
    # (Should be imported or defined in constants.py for q_modules)
    try:
        # from .constants import Q_TOOL_AI_RECOMMENDATIONS # Ensure this exists and is populated
        # from .translations import get_translation # To translate codes to Chinese for display
        pass # Assuming Q_TOOL_AI_RECOMMENDATIONS is already in scope via import
    except ImportError:
        return "  - (AI建議配置缺失，無法生成Q科建議。)"
    
    # For translating codes to display names if needed (assuming get_translation exists)
    # from .translations import get_translation
    # This function might not be available or suitable if diagnostic_params_list contains free text.
    # We will display the code/text as is from the list if translation is complex.

    recommendation_lines.append("  --- Q 科目 AI 輔助建議 ---")
    # recommendation_lines.append("  - 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些基於您編輯後診斷標籤的建議：")
    
    recommended_tools_added_for_q = False
    # Sort for consistent output order
    for param_code_or_text in sorted(list(all_triggered_param_codes)):
        # If param_code_or_text is a known code in Q_TOOL_AI_RECOMMENDATIONS
        if param_code_or_text in Q_TOOL_AI_RECOMMENDATIONS:
            # display_name = get_translation(param_code_or_text) # If param is a code
            display_name = param_code_or_text # If it's already a descriptive text or no translation needed for keys
            recommendation_lines.append(f"  - **若診斷涉及【{display_name}】:**")
            for rec_item in Q_TOOL_AI_RECOMMENDATIONS[param_code_or_text]:
                recommendation_lines.append(f"    - {rec_item}")
            recommended_tools_added_for_q = True
        # else: # Handle case where param_text is user-added and not in Q_TOOL_AI_RECOMMENDATIONS
            # This could be a place to add a generic prompt for user-added tags, e.g.
            # recommendation_lines.append(f"  - **關於您標記的【{param_code_or_text}】:** 建議您使用此標籤搜索相關學習資源或與AI討論此問題。")
            # recommended_tools_added_for_q = True
            
    if not recommended_tools_added_for_q:
        recommendation_lines.append("  - (根據您的Q科編輯，未觸發特定的工具或 AI 提示建議。)")
    
    return "\n".join(recommendation_lines) 