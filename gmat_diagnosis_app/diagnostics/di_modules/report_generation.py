import pandas as pd

from .translation import (
    _translate_di, APPENDIX_A_TRANSLATION_DI, 
    DI_PARAM_CATEGORY_ORDER, DI_PARAM_TO_CATEGORY
)
from .utils import _format_rate
from .constants import (
    MAX_ALLOWED_TIME_DI, INVALID_DATA_TAG_DI
)

def _generate_di_summary_report(di_results):
    """Generates the summary report string for the Data Insights section."""
    report_lines = ["---（基於用戶數據與模擬難度分析）---", ""]
    ch1 = di_results.get('chapter_1', {})
    ch2 = di_results.get('chapter_2', {})
    ch3 = di_results.get('chapter_3', {})
    ch4 = di_results.get('chapter_4', {})
    # ch5 = di_results.get('chapter_5', {}) # Ch5 results not directly used in report text
    ch6 = di_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe')

    # Pre-translate common terms
    math_related_zh = _translate_di('Math Related')
    non_math_related_zh = _translate_di('Non-Math Related')

    # Prepare data for reflection mapping and param counts
    all_triggered_params = set()
    param_to_positions = {}
    domain_to_positions = {}
    param_counts_all = pd.Series(dtype=int)

    if diagnosed_df is not None and not diagnosed_df.empty:
        param_col_eng = 'diagnostic_params' if 'diagnostic_params' in diagnosed_df.columns else None
        map_cols = ['content_domain', 'question_position']
        if param_col_eng and all(col in diagnosed_df.columns for col in map_cols):
            all_param_lists_for_count = []
            for index, row in diagnosed_df.iterrows(): # Iteration needed for detailed mapping
                 pos = row.get('question_position')
                 domain = row.get('content_domain', 'Unknown Domain')
                 params = row.get(param_col_eng, [])
                 if not isinstance(params, list): params = []
                 params = [p for p in params if isinstance(p, str)] # Ensure strings

                 all_triggered_params.update(params)
                 all_param_lists_for_count.extend(params) # For counting

                 if pos is not None and pos != 'N/A':
                     if domain != 'Unknown Domain':
                          domain_to_positions.setdefault(domain, set()).add(pos)
                     for p in params:
                         param_to_positions.setdefault(p, set()).add(pos)
            if all_param_lists_for_count:
                 param_counts_all = pd.Series(all_param_lists_for_count).value_counts()

        ch4_behavioral_params = [p for p in ch4.get('triggered_behavioral_params', []) if isinstance(p, str)]
        all_triggered_params.update(ch4_behavioral_params)
        # Add Ch4 params to counts if not already counted (assuming they aren't in df)
        # This might slightly inflate counts if they *are* also in df - depends on Ch4 logic
        param_counts_all = param_counts_all.add(pd.Series(ch4_behavioral_params).value_counts(), fill_value=0)


    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for domain in domain_to_positions: domain_to_positions[domain] = sorted(list(domain_to_positions[domain]))
    sfe_triggered = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in all_triggered_params
    sfe_code = 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'

    # 1. 開篇總結
    report_lines.append("**1. 開篇總結（時間策略與有效性）**")
    tp_status = _translate_di(ch1.get('time_pressure', 'Unknown')) # Use translated status directly
    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    invalid_count = ch1.get('invalid_questions_excluded', 0)
    report_lines.append(f"- 整體作答時間：{total_time:.2f} 分鐘（允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘，剩餘 {time_diff:.2f} 分鐘）")
    report_lines.append(f"- 時間壓力感知：**{tp_status}**")
    if invalid_count > 0: report_lines.append(f"- **警告：** 因時間壓力下末段作答過快，有 {invalid_count} 題被標記為無效數據，未納入後續分析。")
    report_lines.append("")

    # 2. 表現概覽
    report_lines.append("**2. 表現概覽（內容領域對比）**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('poor_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('slow_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **超時率** 明顯更高。")
        if domain_tags.get('slow_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **超時率** 明顯更高。")
    else: report_lines.append(f"- {math_related_zh}與{non_math_related_zh}領域的表現在錯誤率和超時率上無顯著差異。")
    report_lines.append("")

    # 3. 核心問題分析
    report_lines.append("**3. 核心問題分析**")
    if sfe_triggered and diagnosed_df is not None and 'is_sfe' in diagnosed_df.columns:
        sfe_rows = diagnosed_df[diagnosed_df['is_sfe'] == True]
        if not sfe_rows.empty:
            sfe_domains_involved = set(sfe_rows['content_domain'].dropna()) if 'content_domain' in sfe_rows else set()
            sfe_types_involved = set(sfe_rows['question_type'].dropna()) if 'question_type' in sfe_rows else set()
            sfe_label = _translate_di(sfe_code)
            sfe_domains_zh = "，".join(sorted([_translate_di(d) for d in sfe_domains_involved]))
            sfe_types_zh = "，".join(sorted([_translate_di(t) for t in sfe_types_involved]))
            sfe_note = f"**尤其需要注意：{sfe_label}**"
            if sfe_domains_involved: sfe_note += f"（涉及領域：{sfe_domains_zh}）"
            if sfe_types_involved: sfe_note += f"（涉及題型：{sfe_types_zh}）"
            sfe_note += "。（註：SFE 指在已掌握難度範圍內題目失誤）"
            report_lines.append(f"- {sfe_note}")

    top_other_params_codes = []
    if not param_counts_all.empty:
        top_other_params_codes = param_counts_all[param_counts_all.index != sfe_code].head(2).index.tolist()
    if top_other_params_codes:
        report_lines.append("- **其他主要問題點：**")
        for param_code in top_other_params_codes: report_lines.append(f"  - {_translate_di(param_code)}")
    elif not sfe_triggered: report_lines.append("- 未識別出明顯的核心問題模式。")
    report_lines.append("")

    # 4. 特殊模式觀察
    report_lines.append("**4. 特殊模式觀察**")
    careless_triggered_ch4 = ch4.get('carelessness_issue_triggered')
    rushing_triggered_ch4 = ch4.get('early_rushing_risk_triggered')
    patterns_found = False
    if careless_triggered_ch4:
        fast_wrong_rate_str = _format_rate(ch4.get('fast_wrong_rate', 0.0)) # Assume _format_rate is available or move it here
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_CARELESSNESS_ISSUE')}**：相對快速作答的題目中，錯誤比例偏高（{fast_wrong_rate_str}），提示可能存在粗心問題。")
        patterns_found = True
    if rushing_triggered_ch4:
        num_rush = len(ch4.get('early_rushing_questions', []))
        report_lines.append(f"- **{_translate_di('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')}**：測驗前期（{num_rush} 題）出現作答時間過短（<1分鐘）的情況，可能影響準確率。")
        patterns_found = True
    if not patterns_found: report_lines.append("- 未發現明顯的粗心或前期過快等負面行為模式。")
    report_lines.append("")

    # 6. 練習建議
    report_lines.append("**6. 練習建議**")
    recommendations = ch6.get('recommendations_list', [])
    if not recommendations: report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        for i, rec in enumerate(recommendations): report_lines.append(f"{i+1}. {rec.get('text', '無建議內容')}")
    report_lines.append("")

    # 7. 後續行動指引
    report_lines.append("**7. 後續行動指引**")
    report_lines.append("- **引導反思：**")
    reflection_prompts = []
    # Define Helper Functions Locally (can be moved outside if preferred)
    def get_pos_context_str_di(param_keys):
        positions = set().union(*[param_to_positions.get(key, set()) for key in param_keys if isinstance(key, str)])
        return f"（涉及題號：{sorted(list(positions))}）" if positions else ""
    def get_relevant_domains_di(param_keys):
        relevant_positions = set().union(*[param_to_positions.get(key, set()) for key in param_keys if isinstance(key, str)])
        relevant_domains_set = {_translate_di(domain) for domain, positions in domain_to_positions.items() if not relevant_positions.isdisjoint(positions)}
        return sorted(list(relevant_domains_set))
    # Define DI Reflection Parameter Lists (using English codes)
    reading_interpretation_params_di = ['DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR']
    concept_logic_params_di = ['DI_CONCEPT_APPLICATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR']
    data_handling_calc_params_di = ['DI_DATA_EXTRACTION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_CALCULATION_ERROR']
    msr_specific_params_di = ['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_MSR_READING_COMPREHENSION_BARRIER', 'DI_MSR_SINGLE_Q_BOTTLENECK']
    efficiency_params_di = ['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION', 'DI_EFFICIENCY_BOTTLENECK_LOGIC', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_INTEGRATION']
    carelessness_params_di = ['DI_CARELESSNESS_DETAIL_OMISSION', 'DI_BEHAVIOR_CARELESSNESS_ISSUE']
    # Generate Reflection Prompts
    active_concept_logic = [p for p in concept_logic_params_di if p in all_triggered_params]
    if active_concept_logic or sfe_triggered:
        keys = active_concept_logic + ([sfe_code] if sfe_triggered else [])
        domains = get_relevant_domains_di(keys)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 回想一下，在做錯的{ctx}題目時，具體是卡在哪個數學概念、邏輯關係或題目要求上？是完全沒思路，理解錯誤，還是知道方法但應用出錯？" + get_pos_context_str_di(keys))
    active_reading = [p for p in reading_interpretation_params_di if p in all_triggered_params]
    if active_reading:
        domains = get_relevant_domains_di(active_reading)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 對於做錯/慢的{ctx}題目，是文字資訊、圖表解讀有困難，還是無法準確理解問題要求？" + get_pos_context_str_di(active_reading))
    active_data = [p for p in data_handling_calc_params_di if p in all_triggered_params]
    if active_data:
        domains = get_relevant_domains_di(active_data)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 在處理{ctx}題目時，是提取數據、整合信息出錯，還是計算過程容易失誤？" + get_pos_context_str_di(active_data))
    active_msr = [p for p in msr_specific_params_di if p in all_triggered_params]
    if active_msr:
        reflection_prompts.append(f"  - 對於 MSR 題目，是多源資訊的整合理解有困難，還是閱讀材料或回答單題耗時過長？" + get_pos_context_str_di(active_msr))
    active_efficiency = [p for p in efficiency_params_di if p in all_triggered_params]
    if active_efficiency:
        domains = get_relevant_domains_di(active_efficiency)
        ctx = f" [`{'，'.join(domains)}`] " if domains else " "
        reflection_prompts.append(f"  - 回想耗時過長的{ctx}題目，主要瓶頸是在閱讀、理解、思考、整合還是計算？" + get_pos_context_str_di(active_efficiency))
    active_careless = [p for p in carelessness_params_di if p in all_triggered_params]
    if active_careless: reflection_prompts.append("  - 回想一下，是否存在因為看錯字、忽略細節、誤解圖表或計算粗心導致的失誤？" + get_pos_context_str_di(active_careless))
    if not reflection_prompts: reflection_prompts.append("  - （本次分析未觸發典型的反思問題，建議結合練習計劃進行）")
    report_lines.extend(reflection_prompts)

    # Qualitative Analysis Suggestion
    if any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR']):
        report_lines.append("- **質化分析建議：**")
        report_lines.append("  - 如果您對報告中指出的某些問題（尤其是非數學相關的邏輯或閱讀理解錯誤）仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

    # Second Evidence Suggestion
    report_lines.append("- **二級證據參考建議：**")
    df_problem = pd.DataFrame() # Re-init for safety
    if diagnosed_df is not None and not diagnosed_df.empty and 'is_correct' in diagnosed_df and 'overtime' in diagnosed_df:
        df_problem = diagnosed_df[(diagnosed_df['is_correct'] == False) | (diagnosed_df['overtime'] == True)].copy()

    if not df_problem.empty:
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
        details_added_2nd_ev = False
        if 'time_performance_category' in df_problem.columns and 'question_type' in df_problem.columns and 'content_domain' in df_problem.columns and 'diagnostic_params' in df_problem.columns:
            performance_order = ['Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 'Slow & Correct', 'Fast & Correct', 'Normal Time & Correct', 'Unknown']
            try: # Add try-except for robustness of groupby
                grouped_by_performance = df_problem.groupby('time_performance_category')
                for perf_en in performance_order:
                    if perf_en == 'Fast & Correct': continue # Skip Fast & Correct
                    if perf_en in grouped_by_performance.groups:
                        group_df = grouped_by_performance.get_group(perf_en)
                        if not group_df.empty:
                            perf_zh = _translate_di(perf_en)
                            types_zh = sorted([_translate_di(t) for t in group_df['question_type'].dropna().unique()])
                            domains_zh = sorted([_translate_di(d) for d in group_df['content_domain'].dropna().unique()])
                            report_lines.append(f"  - **{perf_zh}：** 需關注題型：【{', '.join(types_zh)}】；涉及領域：【{', '.join(domains_zh)}】。")

                            # Categorize parameters within the group
                            all_eng_codes_in_group = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)])
                            all_eng_codes_in_group.discard(INVALID_DATA_TAG_DI) # Remove invalid tag from categorization

                            labels_by_category = {category: [] for category in DI_PARAM_CATEGORY_ORDER}
                            for code_en in all_eng_codes_in_group:
                                category = DI_PARAM_TO_CATEGORY.get(code_en, 'Unknown')
                                labels_by_category[category].append(code_en)

                            label_parts_data = []
                            for category in DI_PARAM_CATEGORY_ORDER:
                                category_eng_codes = labels_by_category.get(category, [])
                                if category_eng_codes:
                                    category_zh = _translate_di(category)
                                    category_labels_zh = sorted([_translate_di(code) for code in category_eng_codes])
                                    label_parts_data.append((category_zh, category_labels_zh))

                            if label_parts_data:
                                report_lines.append("    注意相關問題點：")
                                for category_zh, sorted_labels_zh in label_parts_data:
                                    report_lines.append(f"      - 【{category_zh}：{'、'.join(sorted_labels_zh)}】")
                            details_added_2nd_ev = True
            except Exception:
                 # Log error if needed, prevent report generation from crashing
                 report_lines.append("  - （分組分析時出現內部錯誤）")
                 details_added_2nd_ev = True # Mark as detail attempted

        # Report core issues again
        core_issue_texts = []
        if sfe_triggered: core_issue_texts.append(_translate_di(sfe_code))
        if 'top_other_params_codes' in locals() and top_other_params_codes:
             core_issue_texts.extend([_translate_di(p) for p in top_other_params_codes])
        filtered_core_issues = [issue for issue in core_issue_texts if issue != _translate_di(INVALID_DATA_TAG_DI)]
        if filtered_core_issues:
             report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(filtered_core_issues)}】。")
             details_added_2nd_ev = True

        if not details_added_2nd_ev: report_lines.append("  - （本次分析未聚焦到特定的問題類型或領域）")
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else: report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")

    # Tool/Prompt section was removed earlier

    return "\n\n".join(report_lines) 