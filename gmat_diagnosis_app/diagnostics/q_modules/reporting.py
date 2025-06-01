"""
Q診斷模塊的報告生成功能

此模塊包含用於Q(Quantitative)診斷的報告生成函數，
用於將診斷結果組織為格式化報告。
"""

import pandas as pd
# Use i18n system instead of the old translation function
from gmat_diagnosis_app.i18n import translate as t
from gmat_diagnosis_app.diagnostics.q_modules.utils import format_rate, map_difficulty_to_label
from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS


def generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved):
    """Generates Section 3: Core Issue Diagnosis."""
    lines = [t('core_issues_diagnosis')]
    lines.append("")
    lines.append(t('high_frequency_potential_issues'))
    sfe_param_translated = t('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

    if sfe_triggered:
        sfe_note = f"{t('sfe_attention_note')} (**{sfe_param_translated}**)"
        if sfe_skills_involved:
            sfe_note += f"{t('sfe_skills_involved')} {', '.join(sorted(list(sfe_skills_involved)))}"
        else:
            sfe_note += ")"
        lines.append(f"    * {sfe_note}{t('sfe_stability_problem')}")

    core_issue_summary = []
    param_careless_detail = t('Q_CARELESSNESS_DETAIL_OMISSION')
    param_concept_app = t('Q_CONCEPT_APPLICATION_ERROR')
    param_calculation = t('Q_CALCULATION_ERROR')
    param_problem_under = t('Q_PROBLEM_UNDERSTANDING_ERROR')
    param_reading_comp = t('Q_READING_COMPREHENSION_ERROR')
    param_eff_reading = t('Q_EFFICIENCY_BOTTLENECK_READING')
    param_eff_concept = t('Q_EFFICIENCY_BOTTLENECK_CONCEPT')
    param_eff_calc = t('Q_EFFICIENCY_BOTTLENECK_CALCULATION')

    if param_careless_detail in triggered_params_translated:
        core_issue_summary.append(f"{t('careless_tendency')}**{param_careless_detail}**。")
    if (param_concept_app in triggered_params_translated or param_problem_under in triggered_params_translated) and not sfe_triggered:
         related_issues = []
         if param_concept_app in triggered_params_translated: related_issues.append(f"**{param_concept_app}**")
         if param_problem_under in triggered_params_translated: related_issues.append(f"**{param_problem_under}**")
         core_issue_summary.append(f"{t('concept_understanding_issue')}{t('or').join(related_issues)}。")
    if param_calculation in triggered_params_translated:
        core_issue_summary.append(f"{t('calculation_error_cause')} (**{param_calculation}**)。")
    if param_reading_comp in triggered_params_translated:
        core_issue_summary.append(f"{t('reading_comprehension_barrier')} (**{param_reading_comp}**)。")

    efficiency_params_triggered = {p for p in triggered_params_translated if p in [param_eff_reading, param_eff_concept, param_eff_calc]}
    if efficiency_params_triggered:
        efficiency_contexts = []
        if param_eff_reading in efficiency_params_triggered: efficiency_contexts.append(t('reading_real_questions'))
        if param_eff_concept in efficiency_params_triggered: efficiency_contexts.append(t('concept_thinking'))
        if param_eff_calc in efficiency_params_triggered: efficiency_contexts.append(t('calculation_process'))
        core_issue_summary.append(t('efficiency_time_consumption').format(
            "、".join(efficiency_contexts), ", ".join([f"**{p}**" for p in sorted(list(efficiency_params_triggered))])))

    if core_issue_summary:
        lines.extend([f"    * {line}" for line in core_issue_summary])
    elif not sfe_triggered:
        lines.append(f"    * {t('no_core_issues_identified')}")
    return lines


def generate_report_section4(ch5_patterns):
    """Generates Section 4: Pattern Observation."""
    lines = []
    lines.append(t('special_behavioral_patterns'))
    pattern_found = False
    param_early_rush = t('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    param_careless_issue = t('Q_BEHAVIOR_CARELESSNESS_ISSUE')

    if ch5_patterns.get('early_rushing_flag', False):
        lines.append(f"    * {t('early_rushing_warning')} (**{param_early_rush}**)")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        lines.append(f"    * {t('carelessness_analysis').format(ch5_patterns.get('fast_wrong_rate', 0))} (**{param_careless_issue}**)")
        pattern_found = True
    if not pattern_found:
        lines.append(f"    * {t('no_special_patterns')}")
    return lines


def generate_report_section5(ch6_override):
    """Generates Section 5: Foundational Consolidation Hint."""
    lines = []
    lines.append(t('practice_consolidation'))
    lines.append("")
    lines.append(t('priority_consolidation_skills'))
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        lines.append(f"    * {t('core_skills_consolidation').format(', '.join(sorted(override_skills_list)))}")
    else:
        lines.append(f"    * {t('no_skill_override_triggered')}")
    return lines


def generate_report_section6(q_recommendations, sfe_triggered):
    """Generates Section 6: Practice Plan Presentation."""
    lines = []
    lines.append(t('overall_practice_direction'))
    lines.append("")
    if q_recommendations:
        if sfe_triggered:
            lines.append(f"    * {t('sfe_priority_note')}")
            lines.append("")
        for rec in q_recommendations: # Assumes q_recommendations is already formatted list of strings
            lines.append(f"    {rec}")
    else:
        lines.append(f"    * {t('no_specific_practice_recommendations')}")
    return lines


def generate_report_section7(triggered_params_translated, sfe_skills_involved, df_diagnosed):
    """Generates Section 7: Follow-up Action Guidance."""
    lines = []
    lines.append(t('follow_up_action_guidance'))
    lines.append("")

    # --- Reflection Prompts ---
    lines.append(t('guided_reflection_prompts'))
    
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
            combined_groups = problem_df.groupby(['time_performance_category', 'question_fundamental_skill', 'question_type'])
            
            # 對每個組合進行分析並生成獨立的反思提示
            for (time_perf, skill, q_type), group in combined_groups:
                # 跳過正確題目的組（如果有的話）
                if 'Correct' in time_perf:
                    continue
                
                # 翻譯時間表現、技能和題型
                time_perf_map = {
                    'Fast & Wrong': t('fast_wrong'),
                    'Slow & Wrong': t('slow_wrong'),
                    'Normal Time & Wrong': t('normal_time_wrong')
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
                    
                    # 按類別分組
                    params_by_category = {}
                    for param in unique_params:
                        # 根據參數前綴或特定關鍵字進行分類
                        category = t('problem_types')  # 默認類別
                        
                        # 簡單分類邏輯
                        if "CARELESSNESS" in param:
                            category = t('carelessness_problems')
                        elif "READING" in param or "COMPREHENSION" in param:
                            category = t('reading_comprehension_problems')
                        elif "CALCULATION" in param:
                            category = t('calculation_problems')
                        elif "CONCEPT" in param or "APPLICATION" in param:
                            category = t('concept_application_problems')
                        elif "EFFICIENCY" in param:
                            category = t('efficiency_problems')
                        
                        if category not in params_by_category:
                            params_by_category[category] = []
                        params_by_category[category].append(param)
                    
                    # 生成引導反思提示
                    current_prompt_lines = []
                    current_prompt_lines.append(f"    * {t('reflection_instruction').format(skill_zh, q_type_zh, time_perf_zh)}")
                    
                    for cat_name, cat_params in params_by_category.items():
                        # 翻譯參數
                        params_zh = []
                        for p_code in cat_params:
                            try:
                                translated = t(p_code)
                                params_zh.append(translated)
                            except:
                                params_zh.append(p_code)
                        current_prompt_lines.append(f"        - {cat_name}：{', '.join(params_zh)}")
                    
                    current_prompt_lines.append(f"        {t('problems_category')}")
                    reflection_prompts.append(current_prompt_lines)
    
    # 如果沒有生成任何反思提示，添加默認提示
    if not reflection_prompts:
        reflection_prompts.append([f"    * {t('default_reflection_prompt')}"])
    
    # 添加反思提示到報告中
    for prompt_line_list in reflection_prompts:
        for line_content in prompt_line_list:
            lines.append(line_content)
        lines.append("")  # Add a blank line between different reflection prompt blocks

    # --- Second Evidence ---
    lines.append(t('practice_record_review'))
    
    # 直接檢查是否有足夠診斷數據，作為二級證據參考建議的條件
    if df_diagnosed is not None and not df_diagnosed.empty:
        lines.append(f"    * {t('review_purpose')}")
        lines.append(f"    * {t('review_method')}")
        
        # 再次強調核心問題
        core_issue_text = []
        param_to_emphasize = ["Q_CARELESSNESS_DETAIL_OMISSION", "Q_CONCEPT_APPLICATION_ERROR", "Q_CALCULATION_ERROR", "Q_READING_COMPREHENSION_ERROR"]
        for param in param_to_emphasize:
            if t(param):
                core_issue_text.append(t(param))
        
        if sfe_skills_involved:
            core_issue_text.append(t("Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE"))
        
        if core_issue_text:
            lines.append(f"    * {t('key_focus')}")
            for issue in core_issue_text:
                lines.append(f"        - {issue}")
        else:
            lines.append(f"    * {t('key_focus_general')}")
        
        lines.append(f"    * {t('sample_insufficient_note')}")
    else:
        lines.append(f"    * {t('no_secondary_evidence_needed')}")

    # --- Qualitative Analysis Suggestion ---
    lines.append("")
    lines.append(t('advanced_assistance'))
    lines.append("")
    lines.append(f"    * {t('qualitative_analysis_suggestion')}")
    lines.append("")
    return lines


def generate_q_summary_report(results, recommendations, df_final, triggered_params_english):
    """
    Generates the summary report for Q section, based on Chapter 8 guidelines.
    Combines all the diagnostics into a comprehensive yet readable report.
    """
    report_lines = [t('q_report_title')]
    report_lines.append(t('q_report_subtitle'))
    report_lines.append("")
    
    # 獲取各章節的診斷結果
    ch1_results = results.get('chapter1_results', {})
    ch2_flags = results.get('chapter2_flags', {})
    ch5_results = results.get('chapter5_patterns', {})
    ch2_summary = results.get('chapter2_summary', [])
    ch3_errors = results.get('chapter3_error_analysis', [])
    ch6_override = results.get('chapter6_skill_override', {})
    
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
    
    # 1. 報告總覽與即時反饋
    report_lines.append(t('report_overview_feedback'))
    report_lines.append("")
    
    # A. 作答時間與策略評估
    report_lines.append(t('time_strategy_assessment'))
    time_pressure = ch1_results.get('time_pressure_status', False)
    time_pressure_text = t('yes') if time_pressure else t('no')
    overtime_threshold = ch1_results.get('overtime_threshold_used', 2.5)
    report_lines.append(f"    * {t('time_pressure_status_label')}{time_pressure_text}")
    report_lines.append(f"    * {t('overtime_threshold_used')}{overtime_threshold} {t('minutes')}")
    
    # B. 重要註記
    report_lines.append(t('important_notes'))
    if manual_invalid_q > 0:
        report_lines.append(f"    * {t('manual_invalid_data_count')}{manual_invalid_q} ({'{:.1f}'.format(manual_invalid_q / total_q * 100 if total_q > 0 else 0)}%)")
    report_lines.append(f"    * {t('valid_score_rate')}{valid_score_rate}% ({correct_valid_q}/{manual_valid_q})")
    report_lines.append("")
    
    # 2. 核心表現分析
    report_lines.append(t('core_performance_analysis'))
    report_lines.append("")
    
    # A. 內容領域表現概覽
    report_lines.append(t('content_domain_overview'))
    report_lines.append(f"    {t('by_question_type')}")
    if ch2_flags.get('poor_real', False):
        report_lines.append(f"        * {t('real_performance_poor')}")
    if ch2_flags.get('poor_pure', False):
        report_lines.append(f"        * {t('pure_performance_poor')}")
    if ch2_flags.get('slow_real', False):
        report_lines.append(f"        * {t('real_slower')}")
    if ch2_flags.get('slow_pure', False):
        report_lines.append(f"        * {t('pure_slower')}")
    
    if not any(ch2_flags.values()):
        report_lines.append(f"        * {t('no_significant_difference')}")
    
    # 獲取錯誤分佈信息（如果有）
    if ch3_errors:
        error_difficulties = [err.get('Difficulty') for err in ch3_errors if err.get('Difficulty') is not None and not pd.isna(err.get('Difficulty'))]
        if error_difficulties:
            difficulty_labels = [map_difficulty_to_label(d) for d in error_difficulties]
            label_counts = pd.Series(difficulty_labels).value_counts().sort_index()
            if not label_counts.empty:
                distribution_str = ", ".join([f"{label} ({count}{t('questions_count')})" for label, count in label_counts.items()])
                report_lines.append(f"    {t('error_difficulty_distribution')} {distribution_str}")
    report_lines.append("")
    
    # B. 高頻潛在問題點
    # 解析triggered_params_english找出最頻繁的問題
    triggered_params_translated = []
    if triggered_params_english:
        for param_code in triggered_params_english:
            try:
                translated = t(param_code)
                triggered_params_translated.append(translated)
            except:
                triggered_params_translated.append(param_code)
                
    sfe_triggered = False
    sfe_skills_involved = set()
    if df_final is not None and 'is_sfe' in df_final.columns:
        sfe_mask = df_final['is_sfe'].fillna(False).astype(bool)
        sfe_triggered = sfe_mask.any()
        if sfe_triggered and 'question_fundamental_skill' in df_final.columns:
            sfe_skills = df_final.loc[sfe_mask, 'question_fundamental_skill'].dropna().unique()
            for skill in sfe_skills:
                if isinstance(skill, str) and skill.strip(): 
                    sfe_skills_involved.add(skill)
    
    core_issue_lines = generate_report_section3(triggered_params_translated, sfe_triggered, sfe_skills_involved)
    report_lines.extend(core_issue_lines[1:]) # Skip the title
    
    # C. 特殊行為模式觀察
    pattern_lines = generate_report_section4(ch5_results)
    report_lines.extend(pattern_lines)
    report_lines.append("")
    
    # 3. 練習建議與基礎鞏固
    consolidation_lines = generate_report_section5(ch6_override)
    report_lines.extend(consolidation_lines)
    
    # B. 整體練習方向
    practice_lines = generate_report_section6(recommendations, sfe_triggered)
    report_lines.extend(practice_lines)
    report_lines.append("")
    
    # 4 & 5. 後續行動與深度反思指引 & 尋求進階協助
    action_lines = generate_report_section7(triggered_params_translated, sfe_skills_involved, df_final)
    report_lines.extend(action_lines)
    report_lines.append("")
    
    # AI Tool Recommendation Section (Chapter 9)
    # Placeholder - this should be generated by a new function if needed
    # For now, let's assume it might come from 'recommendations' or be a static text.
    # Example: ai_tool_recs = generate_q_ai_tool_recommendations(df_final) # You'd need to create this
    # report_lines.extend(ai_tool_recs)
    
    # --- Final cleanup and assembly ---
    # Ensure no leading/trailing empty lines in the final report sections
    # (This is a basic example, more sophisticated cleanup might be needed)
    final_report_lines = []
    for line in report_lines:
        if final_report_lines or line.strip(): # Add line if it's not a leading empty line
            final_report_lines.append(line)
    
    # Remove trailing empty lines
    while final_report_lines and not final_report_lines[-1].strip():
        final_report_lines.pop()
        
    return "\n".join(final_report_lines) # Ensure this returns a joined string for the UI


def generate_q_ai_tool_recommendations(diagnosed_df_q_subject):
    """Generates AI tool and prompt recommendations based on edited Q diagnostic data."""
    recommendation_lines = []
    
    if diagnosed_df_q_subject is None or diagnosed_df_q_subject.empty:
        return f"  - {t('q_no_data_for_ai')}"

    # Ensure 'diagnostic_params_list' column exists
    if 'diagnostic_params_list' not in diagnosed_df_q_subject.columns:
        return f"  - {t('q_missing_diagnostic_params')}"

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
        recommendation_lines.append(f"  - {t('q_no_specific_ai_recommendations')}")
        return "\n".join(recommendation_lines)

    # Ensure Q_TOOL_AI_RECOMMENDATIONS is available
    # (Should be imported or defined in constants.py for q_modules)
    try:
        # from .constants import Q_TOOL_AI_RECOMMENDATIONS # Ensure this exists and is populated
        # from .translations import get_translation # To translate codes to Chinese for display
        pass # Assuming Q_TOOL_AI_RECOMMENDATIONS is already in scope via import
    except ImportError:
        return f"  - {t('q_ai_missing_config')}"
    
    # For translating codes to display names if needed (assuming get_translation exists)
    # from .translations import get_translation
    # This function might not be available or suitable if diagnostic_params_list contains free text.
    # We will display the code/text as is from the list if translation is complex.

    recommendation_lines.append(f"  {t('q_ai_tool_recommendations')}")
    # recommendation_lines.append("  - 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些基於您編輯後診斷標籤的建議：")
    
    recommended_tools_added_for_q = False
    # Sort for consistent output order
    for param_code_or_text in sorted(list(all_triggered_param_codes)):
        # If param_code_or_text is a known code in Q_TOOL_AI_RECOMMENDATIONS
        if param_code_or_text in Q_TOOL_AI_RECOMMENDATIONS:
            # display_name = get_translation(param_code_or_text) # If param is a code
            display_name = param_code_or_text # If it's already a descriptive text or no translation needed for keys
            recommendation_lines.append(f"  - {t('ai_diagnosis_involves').format(display_name)}")
            for rec_item in Q_TOOL_AI_RECOMMENDATIONS[param_code_or_text]:
                recommendation_lines.append(f"    - {rec_item}")
            recommended_tools_added_for_q = True
        # else: # Handle case where param_text is user-added and not in Q_TOOL_AI_RECOMMENDATIONS
            # This could be a place to add a generic prompt for user-added tags, e.g.
            # recommendation_lines.append(f"  - **關於您標記的【{param_code_or_text}】:** 建議您使用此標籤搜索相關學習資源或與AI討論此問題。")
            # recommended_tools_added_for_q = True
            
    if not recommended_tools_added_for_q:
        recommendation_lines.append(f"  - {t('q_no_specific_ai_recommendations')}")
    
    return "\n".join(recommendation_lines) 