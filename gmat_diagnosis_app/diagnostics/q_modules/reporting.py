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
    
    # 從診斷數據中提取基本信息，用於生成反思提示
    reflection_prompts = []
    
    # 確保有可用的數據
    if df_diagnosed is not None and not df_diagnosed.empty:
        # 只對有問題且有效的題目(錯誤或超時)進行分析以生成反思建議
        if 'is_manually_invalid' in df_diagnosed.columns:
            manual_invalid_mask = df_diagnosed['is_manually_invalid'].fillna(False).astype(bool)
            valid_df = df_diagnosed[~manual_invalid_mask].copy()
        elif 'is_invalid' in df_diagnosed.columns: # Fallback if is_manually_invalid is not present
            invalid_mask = df_diagnosed['is_invalid'].fillna(False).astype(bool)
            valid_df = df_diagnosed[~invalid_mask].copy()
        else: # No invalid column, assume all are valid
            valid_df = df_diagnosed.copy()
        
        problem_df = valid_df[(valid_df['is_correct'] == False)].copy()
        
        # 確保必要的列存在
        required_cols = ['question_type', 'question_fundamental_skill', 'time_performance_category', 'diagnostic_params_list']
        if all(col in problem_df.columns for col in required_cols) and not problem_df.empty:
            # 根據三個維度進行分組：時間表現、基本技能、題型(REAL/PURE)
            combined_groups = problem_df.groupby(['time_performance_category', 'question_fundamental_skill', 'question_type'])\
            
            # 對每個組合進行分析並生成獨立的反思提示
            for (time_perf, skill, q_type), group in combined_groups:
                # 跳過正確題目的組（如果有的話）
                if 'Correct' in time_perf:
                    continue
                
                # 翻譯時間表現、技能和題型
                time_perf_map = {
                    'Fast & Wrong': '快錯',
                    'Slow & Wrong': '慢錯',
                    'Normal Time & Wrong': '正常時間錯'
                }
                
                time_perf_zh = time_perf_map.get(time_perf, time_perf)
                q_type_zh = q_type  # 假設REAL/PURE不需要翻譯
                skill_zh = skill  # 技能名稱可能已經是中文或不需要翻譯
                
                # 獲取該組的所有診斷參數
                all_diagnostic_params = []
                for params_list in group['diagnostic_params_list']:
                    if isinstance(params_list, list):
                        all_diagnostic_params.extend(params_list)
                
                if all_diagnostic_params:
                    # 去除重複的診斷參數並過濾無效參數
                    unique_params = list(set([p for p in all_diagnostic_params if isinstance(p, str) and p.strip()]))
                    
                    # 按類別分組 (這裡需要根據Q模塊的分類實際情況進行調整)
                    # 暫時使用簡單分組，可以根據需要完善
                    params_by_category = {}
                    for param in unique_params:
                        # 這裡可以添加更複雜的分類邏輯
                        # 例如：根據參數前綴或特定關鍵字進行分類
                        category = "問題類型"  # 默認類別
                        
                        # 簡單分類邏輯示例 (實際應用中應更完善)
                        if "CARELESSNESS" in param:
                            category = "粗心問題"
                        elif "READING" in param or "COMPREHENSION" in param:
                            category = "閱讀理解問題"
                        elif "CALCULATION" in param:
                            category = "計算問題"
                        elif "CONCEPT" in param or "APPLICATION" in param:
                            category = "概念應用問題"
                        elif "EFFICIENCY" in param:
                            category = "效率問題"
                        
                        if category not in params_by_category:
                            params_by_category[category] = []
                        params_by_category[category].append(param)
                    
                    # 生成引導反思提示的各個行
                    current_prompt_lines = []
                    current_prompt_lines.append(f"- 找尋【{skill_zh}】【{q_type_zh}】的考前做題紀錄，找尋【{time_perf_zh}】的題目，檢討並反思自己是否有：")
                    current_prompt_lines.append("") # Blank line

                    for cat_name, cat_params in params_by_category.items():
                        # 翻譯參數
                        params_zh = []
                        for p_code in cat_params:
                            try:
                                translated = get_translation(p_code)
                                params_zh.append(translated)
                            except:
                                params_zh.append(p_code)
                        current_prompt_lines.append(f"  【{cat_name}：{', '.join(params_zh)}】")
                    
                    current_prompt_lines.append("") # Blank line
                    current_prompt_lines.append("  等問題。")
                    reflection_prompts.append(current_prompt_lines) # Add the list of lines
    
    # 如果沒有生成任何反思提示，添加默認提示
    if not reflection_prompts:
        reflection_prompts.append(["- 找尋考前做題紀錄中的錯題，按照【基礎技能】【題型】【時間表現】【診斷標籤】等維度進行分析和反思，找出系統性的問題和改進方向。"]) # Ensure it's a list of lines
    
    # 添加反思提示到報告中
    for prompt_line_list in reflection_prompts:
        for line_content in prompt_line_list:
            lines.append(line_content)
        lines.append("") # Add a blank line between different reflection prompt blocks

    # --- Second Evidence ---
    lines.append("- **二級證據參考建議（如考場回憶失效）：**")
    
    # 直接檢查是否有足夠診斷數據，作為二級證據參考建議的條件
    if df_diagnosed is not None and not df_diagnosed.empty:
        lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您按照上述引導反思查看近期的練習記錄，整理相關錯題或超時題目。")
        
        # 再次強調核心問題
        core_issue_text = []
        param_to_emphasize = ["Q_CARELESSNESS_DETAIL_OMISSION", "Q_CONCEPT_APPLICATION_ERROR", "Q_CALCULATION_ERROR", "Q_READING_COMPREHENSION_ERROR"]
        for param in param_to_emphasize:
            if get_translation(param) in triggered_params_translated:
                core_issue_text.append(get_translation(param))
        
        if sfe_skills_involved:
            core_issue_text.append(get_translation("Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE"))
        
        if core_issue_text:
            lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(core_issue_text)}】。")
        
        lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")

    # --- Qualitative Analysis Suggestion ---
    lines.append("")
    lines.append("- **質化分析建議：**")
    lines.append("  - 如果您對報告中指出的某些問題仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

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
    
    # 使用 is_manually_invalid 計算 manual_invalid_q 和 manual_valid_q
    if 'is_manually_invalid' in df_final.columns:
        manual_invalid_mask = df_final['is_manually_invalid'].fillna(False).astype(bool)
        manual_invalid_q = manual_invalid_mask.sum()
        manual_valid_q = total_q - manual_invalid_q
        df_for_stats = df_final[~manual_invalid_mask].copy() # 用於後續統計的數據框
    elif 'is_invalid' in df_final.columns: # Fallback to is_invalid if is_manually_invalid is missing
        invalid_mask_fallback = df_final['is_invalid'].fillna(False).astype(bool)
        manual_invalid_q = invalid_mask_fallback.sum() # 在這種情況下，它實際上是總無效
        manual_valid_q = total_q - manual_invalid_q
        df_for_stats = df_final[~invalid_mask_fallback].copy()
    else: # No invalid columns
        manual_invalid_q = 0
        manual_valid_q = total_q
        df_for_stats = df_final.copy()
    
    # 基於 df_for_stats (排除了手動無效題) 進行後續統計
    correct_valid_q = df_for_stats[(df_for_stats['is_correct'] == True)].shape[0] if 'is_correct' in df_for_stats.columns else 0
    incorrect_valid_q = df_for_stats[(df_for_stats['is_correct'] == False)].shape[0] if 'is_correct' in df_for_stats.columns else 0
    overtime_q_on_valid = df_for_stats[df_for_stats['overtime'] == True].shape[0] if 'overtime' in df_for_stats.columns else 0
    
    # 計算評分率
    valid_score_rate = round((correct_valid_q / manual_valid_q * 100) if manual_valid_q > 0 else 0, 1)
    
    
    # 2. 第一章：測試條件和有效性
    report_parts.append("**測試條件和資料有效性**")
    time_pressure = ch1_results.get('time_pressure_status', False)
    time_pressure_text = "有" if time_pressure else "無"
    overtime_threshold = ch1_results.get('overtime_threshold_used', 2.5)
    report_parts.append(f"* 時間壓力狀態：{time_pressure_text}")
    report_parts.append(f"* 使用的超時閾值：{overtime_threshold} 分鐘")
    if manual_invalid_q > 0:
        report_parts.append(f"* 手動標記無效數據題數：{manual_invalid_q} ({'{:.1f}'.format(manual_invalid_q / total_q * 100 if total_q > 0 else 0)}%)")
    report_parts.append(f"* 有效評分率（基於手動無效排除）：{valid_score_rate}% ({correct_valid_q}/{manual_valid_q})")
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
    if manual_invalid_q > 0:
        summary_items.append(f"測試中有 {manual_invalid_q} 題手動標記無效數據，可能影響部分診斷精確度")
    
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
    
    # 使用新的引導反思生成邏輯，根據各組合獨立生成反思提示
    reflection_prompts = []
    
    if df_final is not None and not df_final.empty:
        # 修改：使用 is_manually_invalid 進行過濾，如果不存在，則回退到 is_invalid，但優先考慮 is_manually_invalid
        if 'is_manually_invalid' in df_final.columns:
            manual_invalid_mask_final = df_final['is_manually_invalid'].fillna(False).astype(bool)
            valid_df_final_for_reflection = df_final[~manual_invalid_mask_final].copy()
        elif 'is_invalid' in df_final.columns: # Fallback if is_manually_invalid is not present
            invalid_mask_final_fallback = df_final['is_invalid'].fillna(False).astype(bool)
            valid_df_final_for_reflection = df_final[~invalid_mask_final_fallback].copy()
        else: # No invalid column, assume all are valid
            valid_df_final_for_reflection = df_final.copy()
        
        if not valid_df_final_for_reflection.empty and 'time_performance_category' in valid_df_final_for_reflection.columns:
            # 只針對有問題的題目生成反思提示
            target_reflection_time_perf_en = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong']
            reflection_relevant_df = valid_df_final_for_reflection[valid_df_final_for_reflection['time_performance_category'].isin(target_reflection_time_perf_en)]

            if not reflection_relevant_df.empty and all(col in reflection_relevant_df.columns for col in ['question_fundamental_skill', 'question_type', 'diagnostic_params_list']):
                # 按三個維度組合分組
                try:
                    combined_groups = reflection_relevant_df.groupby(['time_performance_category', 'question_fundamental_skill', 'question_type'])\
                    
                    # 對每個組合生成獨立的反思提示
                    for (time_perf, skill, q_type), group in combined_groups:
                        # 翻譯時間表現
                        time_perf_map = {
                            'Fast & Wrong': '快錯',
                            'Slow & Wrong': '慢錯',
                            'Normal Time & Wrong': '正常時間錯'
                        }
                        time_perf_zh = time_perf_map.get(time_perf, time_perf)
                        
                        # 獲取該組的所有診斷參數
                        all_diagnostic_params = []
                        for params_list in group['diagnostic_params_list']:
                            if isinstance(params_list, list):
                                all_diagnostic_params.extend(params_list)
                        
                        if all_diagnostic_params:
                            # 去除重複的診斷參數
                            unique_params = list(set([p for p in all_diagnostic_params if isinstance(p, str) and p.strip()]))\
                            
                            # 按類別分組
                            params_by_category = {}
                            for param in unique_params:
                                category = "問題類型"  # 默認類別
                                
                                # 簡單分類邏輯
                                if "CARELESSNESS" in param:
                                    category = "粗心問題"
                                elif "READING" in param or "COMPREHENSION" in param:
                                    category = "閱讀理解問題"
                                elif "CALCULATION" in param:
                                    category = "計算問題"
                                elif "CONCEPT" in param or "APPLICATION" in param:
                                    category = "概念應用問題"
                                elif "EFFICIENCY" in param:
                                    category = "效率問題"
                                
                                if category not in params_by_category:
                                    params_by_category[category] = []
                                params_by_category[category].append(param)
                            
                            # 生成引導反思提示的各個行
                            current_prompt_lines = []
                            current_prompt_lines.append(f"- 找尋【{skill}】【{q_type}】的考前做題紀錄，找尋【{time_perf_zh}】的題目，檢討並反思自己是否有：")
                            current_prompt_lines.append("") # Blank line

                            for cat_name, cat_params in params_by_category.items():
                                # 翻譯參數
                                params_zh = []
                                for p_code in cat_params:
                                    try:
                                        translated = get_translation(p_code)
                                        params_zh.append(translated)
                                    except:
                                        params_zh.append(p_code)
                                current_prompt_lines.append(f"  【{cat_name}：{', '.join(params_zh)}】")
                            
                            current_prompt_lines.append("") # Blank line
                            current_prompt_lines.append("  等問題。")
                            reflection_prompts.append(current_prompt_lines) # Add the list of lines

                except Exception as e:
                    # 錯誤處理
                    reflection_prompts.append([f"- 生成引導反思時發生錯誤：{str(e)}"]) # Ensure it's a list of lines
    
    # 如果沒有生成任何反思提示，添加默認提示
    if not reflection_prompts:
        reflection_prompts.append(["- 找尋考前做題紀錄中的錯題，按照【基礎技能】【題型】【時間表現】【診斷標籤】等維度進行分析和反思，找出系統性的問題和改進方向。"]) # Ensure it's a list of lines
    
    # 添加反思提示到報告中
    for prompt_line_list in reflection_prompts:
        for line_content in prompt_line_list:
            report_parts.append(line_content) # Add each line individually
        report_parts.append("") # Keep one blank line after each full prompt block

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