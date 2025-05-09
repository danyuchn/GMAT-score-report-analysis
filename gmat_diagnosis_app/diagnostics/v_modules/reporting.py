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
    report_lines.append("**時間策略與有效性**")
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
    report_lines.append("**表現概覽（CR vs RC vs Skills）**") # Modified Title
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
        
        # 不顯示錯誤率與超時率的詳細數值，只顯示總題數
        report_lines.append(f"- CR（{cr_total} 題）")
        report_lines.append(f"- RC（{rc_total} 題）")
        
        error_diff = abs(cr_error_rate - rc_error_rate)
        overtime_diff = abs(cr_overtime_rate - rc_overtime_rate)
        significant_error = error_diff >= 0.15
        significant_overtime = overtime_diff >= 0.15
        
        # 只顯示異常情況
        if significant_error or significant_overtime:
            report_lines.append("  - **異常情況：**")
            if significant_error:
                report_lines.append(f"    - 錯誤率：{'CR 顯著高於 RC' if cr_error_rate > rc_error_rate else 'RC 顯著高於 CR'}（差異 {format_rate(error_diff)}）")
            if significant_overtime:
                report_lines.append(f"    - 超時率：{'CR 顯著高於 RC' if cr_overtime_rate > rc_overtime_rate else 'RC 顯著高於 CR'}（差異 {format_rate(overtime_diff)}）")
        else:
            report_lines.append("  - CR 與 RC 在錯誤率和超時率上表現相當，無顯著差異。")
    # Handle cases where one or both types are missing valid data
    elif not cr_data_valid and not rc_data_valid:
        report_lines.append("- 因缺乏有效的 CR 和 RC 數據，無法進行比較。")
    elif not cr_data_valid:
        report_lines.append("- 因缺乏有效的 CR 數據，無法進行完整比較。")
        if rc_data_valid:
             rc_total = rc_metrics.get('total_questions', 0)
             report_lines.append(f"  - RC（{rc_total} 題）")
    elif not rc_data_valid:
        report_lines.append("- 因缺乏有效的 RC 數據，無法進行完整比較。")
        if cr_data_valid:
             cr_total = cr_metrics.get('total_questions', 0)
             report_lines.append(f"  - CR（{cr_total} 題）")

    # >>> MODIFICATION: Add Skill Metrics <<<
    report_lines.append("")
    report_lines.append("**按核心技能:**")
    if v_metrics_by_skill and v_metrics_by_skill.get('Unknown Skill') is None and len(v_metrics_by_skill) > 1: # Check if skill data is meaningful
         sorted_skills = sorted([s for s in v_metrics_by_skill if s != 'Unknown Skill'])
         if not sorted_skills:
              report_lines.append("- 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
         else:
            # 列出所有技能
            for skill in sorted_skills:
                skill_metrics = v_metrics_by_skill.get(skill, {})
                skill_total = skill_metrics.get('total_questions', 0)
                skill_error_rate = skill_metrics.get('error_rate')
                skill_overtime_rate = skill_metrics.get('overtime_rate')
                skill_display_name = skill  # 使用原始技能名，不翻譯
                
                # 只顯示總題數，不顯示錯誤率和超時率
                report_lines.append(f"- {skill_display_name} ({skill_total} 題)")
                
                # 只有當錯誤率或超時率顯著高於平均時才顯示異常
                high_error_threshold = 0.5  # 可調整的閾值
                high_overtime_threshold = 0.4  # 可調整的閾值
                
                if skill_error_rate > high_error_threshold or skill_overtime_rate > high_overtime_threshold:
                    report_lines.append("  - **異常：**")
                    if skill_error_rate > high_error_threshold:
                        report_lines.append(f"    - 此技能錯誤率偏高")
                    if skill_overtime_rate > high_overtime_threshold:
                        report_lines.append(f"    - 此技能超時率偏高")
    else:
         report_lines.append("- 未能分析按技能劃分的表現（可能缺少有效技能數據）。")
    report_lines.append("")


    # --- Section 3: 核心問題診斷 ---
    report_lines.append("**核心問題診斷（基於觸發的診斷標籤）**")
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
        # 保持技能名為英文
        sfe_skills_display = sfe_skills_en
        sfe_note = f"{sfe_label}" + (f"（涉及技能：{', '.join(sfe_skills_display)}）" if sfe_skills_display else "")
        report_lines.append(f"- **尤其需要注意：** {sfe_note}。（註：SFE 指在已掌握技能範圍內的題目失誤）")

    # 修改核心問題診斷部分，只列出最常出現的數個標籤
    core_issues_params_to_report = triggered_params_all - {'FOUNDATIONAL_MASTERY_INSTABILITY_SFE', INVALID_DATA_TAG_V, 'BEHAVIOR_EARLY_RUSHING_FLAG_RISK', 'BEHAVIOR_CARELESSNESS_ISSUE', 'BEHAVIOR_GUESSING_HASTY'}
    
    if core_issues_params_to_report: # Check if there are any core issues to report after filtering
        report_lines.append("- **主要潛在問題點：**")
        
        # Count frequency of each diagnostic parameter
        param_counts = {}
        if diagnosed_df_ch3_raw is not None and 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
            for params_list_for_row in diagnosed_df_ch3_raw['diagnostic_params']:
                # Ensure it's a list and filter out non-string params if any defensive coding needed
                actual_params_list = [p for p in params_list_for_row if isinstance(p, str)] if isinstance(params_list_for_row, list) else []
                for param_code in actual_params_list:
                    if param_code in core_issues_params_to_report: # Only count relevant core issues
                        param_counts[param_code] = param_counts.get(param_code, 0) + 1
        
        if param_counts: # If there are countable params
            # Sort params by frequency (descending)
            sorted_params = sorted(param_counts.items(), key=lambda item: -item[1])
            
            # 只列出出現頻率最高的5個標籤
            top_params = sorted_params[:5]
            
            for param_code, count in top_params:
                translated_param = translate_v(param_code)
                report_lines.append(f"  - {translated_param} (出現 {count} 次)")
        else: # No countable params found in the dataframe diagnostic_params lists
             report_lines.append("  - 未識別出除SFE或行為模式外的特定核心問題模式。")
            
    elif not sfe_triggered_overall: # No core issues and no SFE
        report_lines.append("- 未識別出明顯的核心問題模式（基於錯誤及效率分析）。")
    report_lines.append("")


    # --- Section 4: 正確但低效分析 ---
    report_lines.append("**正確但低效分析**")
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
            
            # 替換瓶頸為fundamental skill，保持英文
            # bottleneck = translate_v(slow_data.get('dominant_bottleneck_type', 'N/A'))
            fundamental_skill = slow_data.get('primary_skill', 'Unknown Skill')
            
            report_lines.append(f"- {type_name}：{count} 題正確但慢（佔比 {rate}）。平均難度 {avg_diff}，平均耗時 {avg_time} 分鐘。相關技能：{fundamental_skill}。")
            slow_correct_found = True
    if not slow_correct_found:
        report_lines.append("- 未發現明顯的正確但低效問題。")
    report_lines.append("")

    # --- Section 5: 作答模式觀察 ---
    report_lines.append("**作答模式觀察**")
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
    report_lines.append("**基礎鞏固提示**")
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


    # --- Section 7: 練習建議與後續行動 --- (練習建議部分已移至 recommendations.py)
    report_lines.append("**練習建議與後續行動**")
    
    # 練習建議 (從 chapter_7_recommendations 中獲取)
    practice_recommendations = v_diagnosis_results.get('chapter_7_recommendations', [])
    if practice_recommendations:
        for rec in practice_recommendations:
            report_lines.append(f"- {rec}")
    else:
        report_lines.append("- 本次分析未產生具體的練習建議。請參考整體診斷和反思部分。")
    report_lines.append("")

    # 後續行動 (二級證據收集與質化分析)
    report_lines.append("**後續行動建議**")
    
    # 提取基本信息用於引導反思格式模板
    fundamental_skills = set()
    time_performances = set()
    diagnostic_labels = set()
    
    # 從診斷數據中提取信息
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        # 提取技能
        if 'question_fundamental_skill' in diagnosed_df_ch3_raw.columns:
            valid_skills = diagnosed_df_ch3_raw['question_fundamental_skill'].dropna().unique()
            for skill in valid_skills:
                if isinstance(skill, str) and skill != 'Unknown Skill':
                    fundamental_skills.add(skill)
        
        # 提取時間表現
        if 'time_performance_category' in diagnosed_df_ch3_raw.columns:
            valid_perfs = diagnosed_df_ch3_raw['time_performance_category'].dropna().unique()
            for perf in valid_perfs:
                if isinstance(perf, str) and perf != 'Unknown':
                    time_performances.add(perf)
        
        # 提取診斷標籤
        all_diagnostic_params = []
        if 'diagnostic_params' in diagnosed_df_ch3_raw.columns:
            for params_list in diagnosed_df_ch3_raw['diagnostic_params']:
                if isinstance(params_list, list):
                    all_diagnostic_params.extend(params_list)
            
            # 將英文診斷標籤轉換為中文
            for param in all_diagnostic_params:
                if isinstance(param, str):
                    translated_param = translate_v(param)
                    diagnostic_labels.add(translated_param)
    
    # 將集合轉換為排序的列表
    skills_list = sorted(list(fundamental_skills))
    time_performances_list = sorted(list(time_performances))
    diagnostic_labels_list = sorted(list(diagnostic_labels))
    
    # 格式化時間表現
    time_perf_text = "，".join(time_performances_list) if time_performances_list else "各種時間表現"
    
    # 格式化診斷標籤
    labels_text = "，".join(diagnostic_labels_list) if diagnostic_labels_list else "診斷標籤"
    
    # 格式化技能
    skills_text = "，".join(skills_list) if skills_list else "基礎技能"
    
    # 添加引導反思
    report_lines.append("- **引導反思:**")
    
    # 添加單一統一格式的引導反思，與DI模組保持一致
    if skills_list:
        unified_reflection = f"  - 找尋【內容領域】【{skills_text}】的考前做題紀錄，找尋【{time_perf_text}】的題目，檢討並反思自己是否有：【{labels_text}】等問題。"
    else:
        unified_reflection = "  - 找尋考前做題紀錄中的錯題和超時題，按照【題型】【內容領域】【時間表現】【診斷標籤】等維度進行分析和反思，找出系統性的問題和改進方向。"
    
    report_lines.append(unified_reflection)
    
    # 添加二級證據參考建議
    report_lines.append("")
    report_lines.append("- **二級證據參考建議（如考場回憶失效）：**")
    
    if diagnosed_df_ch3_raw is not None and not diagnosed_df_ch3_raw.empty:
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您按照上述引導反思查看近期的練習記錄，整理相關錯題或超時題目。")
        
        # 再次強調核心問題
        core_issue_text = []
        for param_code in ['CR_REASONING_CHAIN_ERROR', 'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY', 'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY']:
            if translate_v(param_code) in diagnostic_labels:
                core_issue_text.append(translate_v(param_code))
        
        if sfe_triggered_overall:
            core_issue_text.append(translate_v('FOUNDATIONAL_MASTERY_INSTABILITY_SFE'))
        
        if core_issue_text:
            report_lines.append(f"  - 請特別留意題目是否反覆涉及報告核心問題診斷章節指出的問題：【{', '.join(core_issue_text)}】。")
        
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")
    
    # 質化分析建議
    report_lines.append("")
    report_lines.append("- **質化分析建議：**")
    report_lines.append("  - 如果您對報告中指出的某些問題仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")
    
    report_lines.append("")

    # --- Section 8: Tool and AI Prompt Recommendations (COMMENTED OUT - to be replaced by new function) ---
    # """
    # report_lines.append("- **輔助工具與 AI 提示推薦建議：**")
    # report_lines.append("  - 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些可能適用的輔助工具和 AI 提示。系統會根據您觸發的診斷參數組合，推薦相關的資源。請根據您的具體診斷結果選用。")
    # recommended_tools_added = False
    # # Use all_triggered_params_all which is a set of unique English codes from Ch3 and Ch5
    # # Ensure it exists and is a set
    # current_triggered_params_v = triggered_params_all if isinstance(triggered_params_all, set) else set()

    # for param_code in current_triggered_params_v:
    #     if param_code in V_TOOL_AI_RECOMMENDATIONS:
    #         param_zh = translate_v(param_code)
    #         report_lines.append(f"  - **若診斷涉及【{param_zh}】:**")
    #         for rec_item in V_TOOL_AI_RECOMMENDATIONS[param_code]:
    #             report_lines.append(f"    - {rec_item}")
    #         recommended_tools_added = True
            
    # if not recommended_tools_added:
    #     report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議。)")
    # report_lines.append("")
    # """
    
    return "\n".join(report_lines)

# New function for AI tool recommendations based on edited data
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