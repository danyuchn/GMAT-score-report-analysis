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
    lines = []
    lines.append("**B. 高頻潛在問題**")
    sfe_param_translated = t('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

    if sfe_triggered:
        sfe_note = f"特別值得注意的是，在已掌握技能領域的基礎或中等難度題目上出現錯誤（**{sfe_param_translated}**），"
        if sfe_skills_involved:
            sfe_note += f"涉及技能：{', '.join(sorted(list(sfe_skills_involved)))}，顯示這些知識點應用存在穩定性問題。"
        else:
            sfe_note += "顯示基礎掌握存在穩定性問題。"
        lines.append(sfe_note)
        lines.append("")

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
        core_issue_summary.append(f"粗心傾向是失分原因（**{param_careless_detail}**）。")
    if (param_concept_app in triggered_params_translated or param_problem_under in triggered_params_translated) and not sfe_triggered:
         related_issues = []
         if param_concept_app in triggered_params_translated: related_issues.append(f"**{param_concept_app}**")
         if param_problem_under in triggered_params_translated: related_issues.append(f"**{param_problem_under}**")
         core_issue_summary.append(f"概念理解存在問題：{'或'.join(related_issues)}。")
    if param_calculation in triggered_params_translated:
        core_issue_summary.append(f"計算錯誤也是失分原因之一（**{param_calculation}**）。")
    if param_reading_comp in triggered_params_translated:
        core_issue_summary.append(f"Real題目的文字信息理解可能存在障礙（**{param_reading_comp}**）。")

    efficiency_params_triggered = {p for p in triggered_params_translated if p in [param_eff_reading, param_eff_concept, param_eff_calc]}
    if efficiency_params_triggered:
        efficiency_contexts = []
        if param_eff_reading in efficiency_params_triggered: efficiency_contexts.append("閱讀Real題目")
        if param_eff_concept in efficiency_params_triggered: efficiency_contexts.append("概念思考")
        if param_eff_calc in efficiency_params_triggered: efficiency_contexts.append("計算過程")
        core_issue_summary.append(f"在{'、'.join(efficiency_contexts)}環節耗時較多（{', '.join([f'**{p}**' for p in sorted(list(efficiency_params_triggered))])}）。")

    if core_issue_summary:
        for line in core_issue_summary:
            lines.append(line)
            lines.append("")
    elif not sfe_triggered:
        lines.append("未識別出明顯的核心問題模式。")
        lines.append("")
    return lines


def generate_report_section4(ch5_patterns):
    """Generates Section 4: Pattern Observation."""
    lines = []
    lines.append("**C. 特殊行為模式觀察**")
    pattern_found = False
    param_early_rush = t('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    param_careless_issue = t('Q_BEHAVIOR_CARELESSNESS_ISSUE')

    if ch5_patterns.get('early_rushing_flag', False):
        lines.append(f"考試初期部分題目答題節奏偏快，建議保持穩定的答題節奏以避免潛在的\"標記復查\"風險。（**{param_early_rush}**）")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        lines.append(f"快速答錯比例較高（{ch5_patterns.get('fast_wrong_rate', 0):.1%}），存在粗心傾向。（**{param_careless_issue}**）")
        pattern_found = True
    if not pattern_found:
        lines.append("未發現特殊行為模式。")
    lines.append("")
    return lines


def generate_report_section5(ch6_override):
    """Generates Section 5: Foundational Consolidation Hint."""
    lines = []
    lines.append("**A. 優先鞏固技能**")
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        skill_text = ', '.join(sorted(override_skills_list))
        lines.append(f"對於 {skill_text} 這些核心技能，由於整體表現顯示有明顯提升空間，建議優先進行系統性基礎鞏固，而非僅針對個別錯題。")
    else:
        lines.append("當前未發現需要優先全面基礎鞏固的技能領域。")
    lines.append("")
    return lines


def generate_report_section6(q_recommendations, sfe_triggered):
    """Generates Section 6: Practice Plan Presentation."""
    lines = []
    lines.append("**B. 整體練習方向**")
    if sfe_triggered:
        lines.append("（註：涉及\"Foundation Mastery Instability\"的建議以優先級列出）")
        lines.append("")
    
    if q_recommendations:
        for rec in q_recommendations: # Assumes q_recommendations is already formatted list of strings
            lines.append(rec)
    else:
        lines.append("暫無具體練習建議。")
    lines.append("")
    return lines


def generate_report_section7(triggered_params_translated, sfe_skills_involved, df_diagnosed):
    """Generates Section 7: Follow-up Action Guidance."""
    lines = []
    lines.append("**A. 練習記錄回顧（次要證據參考）**")
    
    # 確保有可用的數據
    if df_diagnosed is not None and not df_diagnosed.empty:
        lines.append("目的：當您無法準確回憶具體錯誤原因、涉及知識點，或需要更客觀數據確認問題模式時。")
        lines.append("")
        lines.append("方法：建議按照以下指導反思回顧近期練習記錄，整理相關錯題或超時題目。")
        lines.append("")
        
        # 重點關注核心問題
        lines.append("重點關注：題目是否重複涉及報告第III部分指出的核心問題：")
        core_issues = [t("Q_CARELESSNESS_DETAIL_OMISSION"), t("Q_CONCEPT_APPLICATION_ERROR"), t("Q_CALCULATION_ERROR"), t("Q_READING_COMPREHENSION_ERROR")]
        if sfe_skills_involved:
            core_issues.append(t("Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE"))
        
        for issue in core_issues:
            lines.append(f"- {issue}")
        lines.append("")
        lines.append("**注意**：如果樣本不足，請注意在接下來的練習中收集，以便更準確地識別問題。")
    else:
        lines.append("目前缺乏足夠的診斷數據進行次要證據分析。")
    
    lines.append("")
    
    # --- Reflection Prompts ---
    lines.append("**B. 引導反思提示（針對具體技能與表現）**")
    lines.append("")
    
    # 從診斷數據中提取基本信息，用於生成反思提示
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
                    'Fast & Wrong': 'Fast & Wrong',
                    'Slow & Wrong': 'Slow & Wrong', 
                    'Normal Time & Wrong': 'Normal Time & Wrong'
                }
                
                time_perf_zh = time_perf_map.get(time_perf, time_perf)
                
                # 獲取該組的所有診斷參數
                all_diagnostic_params = []
                for params_list in group['diagnostic_params_list']:
                    if isinstance(params_list, list):
                        all_diagnostic_params.extend(params_list)
                
                if all_diagnostic_params:
                    # 去除重複的診斷參數並過濾無效參數
                    unique_params = list(set([p for p in all_diagnostic_params if isinstance(p, str) and p.strip()]))
                    
                    if unique_params:
                        # 生成引導反思提示
                        lines.append(f"**{skill} {q_type} 練習記錄反思**")
                        lines.append(f"尋找考前練習記錄中的{time_perf_zh}題目，回顧並反思是否存在以下問題類型：")
                        params_display = ', '.join(unique_params[:3])  # 限制顯示數量避免過長
                        if len(unique_params) > 3:
                            params_display += " 等問題。"
                        else:
                            params_display += " 等問題。"
                        lines.append(params_display)
                        lines.append("")
    
    # 如果沒有生成任何反思提示，添加默認提示
    if not any("練習記錄反思" in line for line in lines[-10:]):
        lines.append("建議回顧近期練習記錄，特別關注錯題的共同特徵和問題類型。")
        lines.append("")

    return lines


def generate_q_summary_report(results, recommendations, df_final, triggered_params_english):
    """
    Generates the summary report for Q section, based on Chapter 8 guidelines.
    Combines all the diagnostics into a comprehensive yet readable report.
    """
    report_lines = []
    report_lines.append("# Q Section Diagnostic Report Details")
    report_lines.append("## Q部分診斷報告詳情（基於用戶數據與模擬難度分析）")
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
    report_lines.append("### I. 報告概覽與即時反饋")
    report_lines.append("")
    
    # A. 作答時間與策略評估
    report_lines.append("**A. 答題時間與策略評估**")
    time_pressure = ch1_results.get('time_pressure_status', False)
    time_pressure_text = "是" if time_pressure else "否"
    overtime_threshold = ch1_results.get('overtime_threshold_used', 2.5)
    report_lines.append(f"- 時間壓力狀態：{time_pressure_text}")
    report_lines.append(f"- 使用超時閾值：{overtime_threshold}分鐘")
    report_lines.append("")
    
    # B. 重要註記
    report_lines.append("**B. 重要提醒**")
    if manual_invalid_q > 0:
        report_lines.append(f"- 手動標記無效數據數量：{manual_invalid_q} ({'{:.1f}'.format(manual_invalid_q / total_q * 100 if total_q > 0 else 0)}%)")
    report_lines.append(f"- 有效答題正確率（基於手動無效排除）：{valid_score_rate}% ({correct_valid_q}/{manual_valid_q})")
    report_lines.append("")
    
    # 2. 核心表現分析
    report_lines.append("### II. 核心表現分析")
    report_lines.append("")
    
    # A. 內容領域表現概覽
    report_lines.append("**A. 內容領域表現概覽**")
    report_lines.append("按題目類型（Real vs Pure）分析：")
    
    if ch2_flags.get('poor_real', False):
        report_lines.append("Real題型表現較差")
    elif ch2_flags.get('poor_pure', False):
        report_lines.append("Pure題型表現較差")
    elif ch2_flags.get('slow_real', False):
        report_lines.append("Real題型速度較慢")
    elif ch2_flags.get('slow_pure', False):
        report_lines.append("Pure題型速度較慢")
    else:
        report_lines.append("Real題型與Pure題型表現無顯著差異")
    
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
    report_lines.extend(core_issue_lines)
    
    # C. 特殊行為模式觀察
    pattern_lines = generate_report_section4(ch5_results)
    report_lines.extend(pattern_lines)
    
    # 3. 練習建議與基礎鞏固
    report_lines.append("### III. 練習建議與基礎鞏固")
    report_lines.append("")
    
    consolidation_lines = generate_report_section5(ch6_override)
    report_lines.extend(consolidation_lines)
    
    # B. 整體練習方向
    practice_lines = generate_report_section6(recommendations, sfe_triggered)
    report_lines.extend(practice_lines)
    
    # 4. 後續行動與深度反思指引 - 暫時註解掉不顯示
    # report_lines.append("### IV. 後續行動與深度反思指導")
    # report_lines.append("")
    
    # 5. 尋求高級協助 - 暫時註解掉不顯示
    # report_lines.append("### V. 尋求高級協助（定性分析）")
    # report_lines.append("")
    # report_lines.append("如果您對報告中識別的某些問題仍感困惑，可嘗試提供2-3道相關錯題，並附上詳細解題過程和思考實例，供顧問進行更深入的案例分析。")
    # report_lines.append("")
    
    # --- Final cleanup and assembly ---
    # Ensure no leading/trailing empty lines in the final report sections
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