import pandas as pd
import logging
import re
import os

from .translation import (
    _translate_di,
    DI_PARAM_CATEGORY_ORDER, DI_PARAM_TO_CATEGORY
)
from .utils import _format_rate
from .constants import (
    MAX_ALLOWED_TIME_DI, INVALID_DATA_TAG_DI
)

def _generate_di_summary_report(di_results):
    """Generates the summary report string for the Data Insights section based on the new structure."""
    report_lines = ["DI 科診斷報告詳情", "---（基於用戶數據與模擬難度分析）---", ""] # Added main title

    ch1 = di_results.get('chapter_1', {})
    ch2 = di_results.get('chapter_2', {})
    ch3 = di_results.get('chapter_3', {})
    ch4 = di_results.get('chapter_4', {})
    # ch5 = di_results.get('chapter_5', {})
    ch6 = di_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe')

    # Pre-translate common terms
    math_related_zh = _translate_di('Math Related')
    non_math_related_zh = _translate_di('Non-Math Related')

    # Prepare data for reflection mapping and param counts
    all_triggered_params = set()
    param_to_positions = {} # Not directly used in new report structure, but keep for internal logic
    domain_to_positions = {} # Not directly used, keep for internal logic
    param_counts_all = pd.Series(dtype=int)

    if diagnosed_df is not None and not diagnosed_df.empty:
        param_col_eng = 'diagnostic_params' if 'diagnostic_params' in diagnosed_df.columns else None
        map_cols = ['content_domain', 'question_position']
        if param_col_eng and all(col in diagnosed_df.columns for col in map_cols):
            all_param_lists_for_count = []
            for index, row in diagnosed_df.iterrows():
                 pos = row.get('question_position')
                 domain = row.get('content_domain', 'Unknown Domain')
                 params = row.get(param_col_eng, [])
                 if not isinstance(params, list): params = []
                 params = [p for p in params if isinstance(p, str)]

                 all_triggered_params.update(params)
                 all_param_lists_for_count.extend(params)

                 if pos is not None and pos != 'N/A':
                     if domain != 'Unknown Domain':
                          domain_to_positions.setdefault(domain, set()).add(pos)
                     for p in params:
                         param_to_positions.setdefault(p, set()).add(pos)
            if all_param_lists_for_count:
                 param_counts_all = pd.Series(all_param_lists_for_count).value_counts()

        ch4_behavioral_params = [p for p in ch4.get('triggered_behavioral_params', []) if isinstance(p, str)]
        all_triggered_params.update(ch4_behavioral_params)
        param_counts_all = param_counts_all.add(pd.Series(ch4_behavioral_params).value_counts(), fill_value=0)

    sfe_triggered = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in all_triggered_params
    sfe_code = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'

    # --- I. 報告總覽與即時反饋 ---
    report_lines.append("**一、 報告總覽與即時反饋**")
    report_lines.append("") # Add spacing

    # A. 作答時間與策略評估
    report_lines.append("* **A. 作答時間與策略評估**")
    tp_status = _translate_di(ch1.get('time_pressure', 'Unknown'))
    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    report_lines.append(f"    * **整體作答時間：** {total_time:.2f} 分鐘 (允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘，剩餘 {time_diff:.2f} 分鐘)")
    report_lines.append(f"    * **時間壓力感知：** {tp_status}") # Removed bold from value as per new format

    # B. 重要註記
    report_lines.append("* **B. 重要註記**")
    manual_invalid_count = 0
    if diagnosed_df is not None and 'is_manually_invalid' in diagnosed_df.columns:
        manual_invalid_count = diagnosed_df['is_manually_invalid'].astype(bool).sum()
    if manual_invalid_count > 0:
        report_lines.append(f"    * 您手動標記了 {manual_invalid_count} 題為無效，這些題目已從部分細化分析中排除。")
    else:
        report_lines.append("    * 無手動標記為無效的題目。")
    report_lines.append("")

    # --- II. 核心表現分析 ---
    report_lines.append("**二、 核心表現分析**")
    report_lines.append("")

    # A. 內容領域表現概覽
    report_lines.append("* **A. 內容領域表現概覽**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    domain_comparison_lines = []
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): domain_comparison_lines.append(f"    * {math_related_zh}領域的錯誤率明顯更高。") # Removed bold from math_related_zh for content
        if domain_tags.get('poor_non_math_related'): domain_comparison_lines.append(f"    * {non_math_related_zh}領域的錯誤率明顯更高。")
        if domain_tags.get('slow_math_related'): domain_comparison_lines.append(f"    * {math_related_zh}領域的超時率明顯更高。")
        if domain_tags.get('slow_non_math_related'): domain_comparison_lines.append(f"    * {non_math_related_zh}領域的超時率明顯更高。")
    else:
        domain_comparison_lines.append(f"    * {math_related_zh}與{non_math_related_zh}領域的表現在錯誤率和超時率上無顯著差異。")
    if not domain_comparison_lines: # Fallback if no specific tags but differences were expected
        domain_comparison_lines.append(f"    * 請參考詳細數據分析各領域表現。") # Generic fallback
    report_lines.extend(domain_comparison_lines)


    # B. 高頻潛在問題點
    report_lines.append("* **B. 高頻潛在問題點**")
    potential_problem_lines = []
    if sfe_triggered and diagnosed_df is not None and 'is_sfe' in diagnosed_df.columns:
        valid_df_sfe = diagnosed_df[~diagnosed_df.get('is_invalid', False)].copy() # Renamed to avoid conflict
        sfe_rows = valid_df_sfe[valid_df_sfe['is_sfe'] == True]
        if not sfe_rows.empty:
            sfe_label = _translate_di(sfe_code)
            potential_problem_lines.append(f"    * {sfe_label} (註：SFE 指在已掌握難度範圍內題目失誤)")


    top_other_params_codes = []
    if not param_counts_all.empty:
        filtered_param_counts = param_counts_all[~param_counts_all.index.isin([sfe_code, INVALID_DATA_TAG_DI])]
        top_other_params_codes = filtered_param_counts.head(2).index.tolist()

    if top_other_params_codes:
        for param_code in top_other_params_codes:
            potential_problem_lines.append(f"    * {_translate_di(param_code)}")
    
    if not potential_problem_lines:
        potential_problem_lines.append("    * 未識別出明顯的核心問題模式。")
    report_lines.extend(potential_problem_lines)

    # C. 特殊行為模式觀察
    report_lines.append("* **C. 特殊行為模式觀察**")
    careless_triggered_ch4 = ch4.get('carelessness_issue_triggered')
    rushing_triggered_ch4 = ch4.get('early_rushing_risk_triggered')
    patterns_found = False
    behavior_pattern_lines = []
    if careless_triggered_ch4:
        fast_wrong_rate_str = _format_rate(ch4.get('fast_wrong_rate', 0.0))
        behavior_pattern_lines.append(f"    * {_translate_di('DI_BEHAVIOR_CARELESSNESS_ISSUE')}：相對快速作答的題目中，錯誤比例偏高（{fast_wrong_rate_str}），提示可能存在粗心問題。")
        patterns_found = True
    if rushing_triggered_ch4:
        num_rush = len(ch4.get('early_rushing_questions', []))
        behavior_pattern_lines.append(f"    * {_translate_di('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')}：測驗前期（{num_rush} 題）出現作答時間過短（<1分鐘）的情況，可能影響準確率。")
        patterns_found = True
    if not patterns_found:
        behavior_pattern_lines.append("    * 未發現明顯的粗心或前期過快等負面行為模式。")
    report_lines.extend(behavior_pattern_lines)
    report_lines.append("")


    # --- III. 宏觀練習建議 (按題型) ---
    report_lines.append("**三、 宏觀練習建議 (按題型)**")
    report_lines.append("")
    recommendations = ch6.get('recommendations_list', [])
    
    if not recommendations:
        report_lines.append("* 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        q_type_map = {
            "Data Sufficiency": "A", "Two-part analysis": "B", # Corrected "Two-part analysis" to "Two-part analysis"
            "Multi-source reasoning": "C", "Graph and Table": "D"
        }
        # Sort recommendations to match A, B, C, D if possible based on typical GMAT order
        # This requires knowing the question type within the rec text or structure
        
        # Attempt to parse recommendation text for structured output
        for idx, rec_original in enumerate(recommendations):
            rec_text = rec_original.get('text', '')
            rec_type = rec_original.get('type', 'unknown')
            original_q_type_field = rec_original.get('question_type', 'Unknown Type')

            q_type_eng = ""
            q_type_eng_stripped = ""
            q_type_zh = _translate_di(original_q_type_field)

            # Default texts, primarily for macro or as fallback
            challenge_text = _translate_di("整體表現有較大提升空間") # Generic default
            direction_text = _translate_di("建議全面鞏固基礎")     # Generic default
            time_limit_text = "N/A"

            if rec_type == 'macro':
                q_type_match_macro = re.search(r"宏觀建議 \((.*?)\):", rec_text)
                if q_type_match_macro:
                    q_type_eng = q_type_match_macro.group(1).strip()
                    q_type_zh = _translate_di(q_type_eng)

                challenge_match_macro = re.search(r"由於(整體表現有較大提升空間 \(錯誤率 .*?% 或 超時率 .*?%\))", rec_text)
                if challenge_match_macro:
                    challenge_text = challenge_match_macro.group(1).strip()

                direction_match_macro = re.search(r"(建議全面鞏固.*?題型的基礎，可從.*?開始系統性練習，掌握核心方法)", rec_text)
                if direction_match_macro:
                    full_direction_text = direction_match_macro.group(1).strip()
                    direction_text = full_direction_text[len("建議"):].strip() if full_direction_text.startswith("建議") else full_direction_text
                
                time_limit_match_macro = re.search(r"建議限時 \*\*(.*?分鐘)\*\*", rec_text)
                if time_limit_match_macro:
                    time_limit_text = time_limit_match_macro.group(1).strip()

            elif rec_type == 'case_aggregated':
                q_type_eng = original_q_type_field # Use type from the recommendation object

                # Construct challenge_text from structured fields or parse rec_text
                sfe_prefix = "*基礎掌握不穩* " if rec_original.get('is_sfe') else ""
                domain_in_rec = _translate_di(rec_original.get('domain', '未知領域'))
                # q_type_in_rec_zh = _translate_di(rec_original.get('question_type', '未知題型')) # q_type_zh is already this
                problem_desc_in_rec = _translate_di("錯誤或超時")
                challenge_text = f"{sfe_prefix}針對 **{domain_in_rec}** 領域的 **{q_type_zh}** 題目 ({problem_desc_in_rec})"
                
                # Construct direction_text
                difficulty_grade_in_rec = rec_original.get('difficulty_grade', '未知難度')
                # Target times map (consider making this a global constant or passing it if it varies)
                target_times_map_for_report = {'Data Sufficiency': 2.0, 'Two-part analysis': 3.0, 'Graph and Table': 3.0, 'Multi-source reasoning': 1.5}
                target_time_val = target_times_map_for_report.get(q_type_eng, 2.0) # Default to 2.0 if q_type_eng not found
                target_time_str = f"{target_time_val:.1f} 分鐘"
                
                # Try to get the specific part from rec_text first for direction
                direction_pattern_case = r"建議練習 \*\*(.*?)\*\* 難度題目,.*?\(最終目標時間: (.*?)\)"
                direction_match_case = re.search(direction_pattern_case, rec_text)
                if direction_match_case:
                    direction_text = f"建議練習 **{direction_match_case.group(1)}** 難度題目 (最終目標時間: {direction_match_case.group(2)})"
                else: # Fallback to structured data
                    direction_text = f"建議練習 **{difficulty_grade_in_rec}** 難度題目 (最終目標時間: {target_time_str})"

                # Append focus note if present in rec_text (usually at the end)
                focus_note_match = re.search(r"(\s\*\*建議增加.*?比例。\*\*)", rec_text) # Matches the bolded focus note
                if focus_note_match:
                    direction_text += focus_note_match.group(1)


                # Construct time_limit_text
                time_val_z = rec_original.get('time_limit_z')
                if pd.notna(time_val_z):
                    time_limit_text = f"{time_val_z:.1f} 分鐘"
                else:
                    # Fallback regex if field not present, though direct field is better
                    time_limit_pattern_case = r"起始練習限時建議為 \*\*(.*?)\*\*"
                    time_limit_match_case = re.search(time_limit_pattern_case, rec_text)
                    if time_limit_match_case:
                        time_limit_text = time_limit_match_case.group(1).strip()
                    else:
                        time_limit_text = "N/A"
            
            # Common post-processing for time_limit_text
            if time_limit_text != "N/A":
                if q_type_eng == "Multi-source reasoning":
                    time_limit_text += "/題組"
                else:
                    time_limit_text += "/題"
            
            section_letter = ""
            title_line_content_for_type = q_type_zh # Default to translated type

            if q_type_eng:
                q_type_eng_stripped = q_type_eng.strip()

                if q_type_eng_stripped in q_type_map:
                    section_letter = q_type_map[q_type_eng_stripped] + "."
                else: # Fallback for section letter if direct map fails (should be rare now)
                    for key_eng_map, letter_map in q_type_map.items():
                        if _translate_di(key_eng_map) in q_type_zh : 
                            section_letter = letter_map + "."
                            break
                    if not section_letter:
                        pass
            
            if rec_type == 'case_aggregated' and rec_original.get('is_sfe'):
                title_line_content_for_type += " (*基礎掌握不穩*)"

            title_line = f"* **{section_letter} {title_line_content_for_type}**"
            
            report_lines.append(title_line)
            report_lines.append(f"    * **當前挑戰：** {challenge_text}")
            report_lines.append(f"    * **建議方向：** {direction_text}")
            report_lines.append(f"    * **建議限時：** {time_limit_text}")
            report_lines.append("")

    report_lines.append("")


    # --- IV. 後續行動與深度反思指引 ---
    report_lines.append("**四、 後續行動與深度反思指引**")
    report_lines.append("")

    # A. 檢視練習記錄 (二級證據參考)
    report_lines.append("* **A. 檢視練習記錄 (二級證據參考)**")
    if diagnosed_df is not None and not diagnosed_df.empty and 'is_correct' in diagnosed_df and 'overtime' in diagnosed_df:
        report_lines.append("    * **目的：** 當無法準確回憶具體的錯誤原因、涉及知識點，或需更客觀數據確認問題模式時。")
        report_lines.append("    * **方法：** 按照以上指引查看近期練習記錄，整理相關錯題或超時題目。")

        core_issue_texts_for_review = []
        if sfe_triggered: core_issue_texts_for_review.append(_translate_di(sfe_code))
        if 'top_other_params_codes' in locals() and top_other_params_codes: # Use already defined list
             core_issue_texts_for_review.extend([_translate_di(p) for p in top_other_params_codes])
        
        # Filter out any INVALID_DATA_TAG if it accidentally got included
        filtered_core_issues_for_review = [issue for issue in core_issue_texts_for_review if issue != _translate_di(INVALID_DATA_TAG_DI)]

        if filtered_core_issues_for_review:
             report_lines.append(f"    * **重點關注：** 題目是否反覆涉及報告第二部分（核心表現分析）指出的核心問題：")
             for issue in filtered_core_issues_for_review:
                 report_lines.append(f"        * {issue}")
        else:
            report_lines.append(f"    * **重點關注：** 根據核心表現分析，留意常見錯誤類型。")

        report_lines.append("    * **注意：** 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else:
        report_lines.append("    * (本次分析未發現需要二級證據深入探究的問題點，或數據不足)")
    report_lines.append("")


    # B. 引導性反思提示 (針對特定題型與表現)
    report_lines.append("* **B. 引導性反思提示 (針對特定題型與表現)**")
    reflection_prompts_data = [] # Store tuples of (time_perf, domain, q_type, params_by_category)

    if diagnosed_df is not None and not diagnosed_df.empty:
        valid_df_reflection = diagnosed_df[~diagnosed_df.get('is_invalid', False)].copy() # Renamed
        problem_df_reflection = valid_df_reflection[
            (valid_df_reflection['is_correct'] == False) | (valid_df_reflection['overtime'] == True)
        ].copy() # Renamed

        required_cols = ['question_type', 'content_domain', 'time_performance_category', 'diagnostic_params']
        if all(col in problem_df_reflection.columns for col in required_cols) and not problem_df_reflection.empty:
            # Ensure consistent sorting for reproducibility if needed, though order might not matter for final output
            # sorted_problem_df = problem_df_reflection.sort_values(by=['content_domain', 'question_type', 'time_performance_category'])
            # combined_groups = sorted_problem_df.groupby(['time_performance_category', 'content_domain', 'question_type'], sort=False)
            combined_groups = problem_df_reflection.groupby(['time_performance_category', 'content_domain', 'question_type'])


            for (time_perf, domain, q_type), group in combined_groups:
                if time_perf in ['Normal Time & Correct', 'Fast & Correct', _translate_di('Normal Time & Correct'), _translate_di('Fast & Correct')]: # Check both Eng and Zh
                    continue

                all_diagnostic_params_group = [] # Renamed
                for params_list in group['diagnostic_params']:
                    if isinstance(params_list, list):
                        all_diagnostic_params_group.extend(p for p in params_list if p != INVALID_DATA_TAG_DI) # Filter invalid tag

                if all_diagnostic_params_group:
                    unique_params = sorted(list(set(all_diagnostic_params_group))) # Sort for consistent order
                    params_by_category = {}
                    # Use DI_PARAM_CATEGORY_ORDER for sorting categories
                    for category_eng in DI_PARAM_CATEGORY_ORDER:
                        params_in_cat = []
                        for param in unique_params:
                            if DI_PARAM_TO_CATEGORY.get(param) == category_eng:
                                params_in_cat.append(param)
                        if params_in_cat:
                             # Ensure params within a category are also sorted if desired
                            params_by_category[_translate_di(category_eng)] = sorted([_translate_di(p) for p in params_in_cat])


                    if params_by_category: # Only add if there are categorized params
                         reflection_prompts_data.append({
                            "time_perf_zh": _translate_di(time_perf),
                            "domain_zh": _translate_di(domain),
                            "q_type_zh": _translate_di(q_type),
                            "categories": params_by_category
                        })
    
    if not reflection_prompts_data:
        report_lines.append("    * 未發現需要特別反思的問題模式。請繼續保持良好表現。")
    else:
        for idx, prompt_data in enumerate(reflection_prompts_data):
            report_lines.append(f"    * **{idx + 1}. {prompt_data['domain_zh']} {prompt_data['q_type_zh']} ({prompt_data['time_perf_zh']})**")
            report_lines.append(f"        * **檢討方向：**")
            for category_zh, params_zh_list in prompt_data['categories'].items():
                report_lines.append(f"            * 【{category_zh}】：{', '.join(params_zh_list)}")
            report_lines.append("") # Space after each reflection item block
    report_lines.append("")


    # --- V. 尋求進階協助 (質化分析) ---
    report_lines.append("**五、 尋求進階協助 (質化分析)**")
    report_lines.append("")
    # Condition for showing this suggestion (can be adjusted)
    # Using a simplified condition based on existence of any core issues previously identified
    # or specific complex params.
    show_qualitative_suggestion = False
    if sfe_triggered or top_other_params_codes: # If any core issues were listed
        show_qualitative_suggestion = True
    elif any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_MULTI_SOURCE_INTEGRATION_ERROR_MSR']):
        show_qualitative_suggestion = True
        
    if show_qualitative_suggestion:
        report_lines.append("* **建議：** 如果您對報告中指出的某些問題仍感困惑，可以嘗試提供 2-3 題相關錯題的詳細解題流程跟思路範例，供顧問進行更深入的個案分析。")
    else:
        report_lines.append("* 目前分析結果較為清晰，若仍有疑問可隨時提出。")
    report_lines.append("")


    # Tool/AI Prompt Recommendations (remains commented out as per original logic)
    """
    report_lines.append("- **輔助工具與 AI 提示推薦建議：**")
    # ... (rest of the commented code)
    """

    report_text = "\n".join(report_lines) # Using single newline for tighter list formatting, can be \n\n if more space is needed

    # The try-except block for extracting stats from report_text is not part of the report content generation itself.
    # It can remain as is if used for logging/tracking.
    try:
        total_qs_match = re.search(r'共(\d+)題', report_text) # This regex might not match new report format
        # ... other stat extractions
    except Exception as e:
        logging.error(f"[DI報告追蹤] 從報告中提取數據時出錯: {e}")

    return report_text