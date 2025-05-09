import pandas as pd
import logging
import re  # 添加 re 模塊導入

from .translation import (
    _translate_di, APPENDIX_A_TRANSLATION_DI, 
    DI_PARAM_CATEGORY_ORDER, DI_PARAM_TO_CATEGORY
)
from .utils import _format_rate
from .constants import (
    MAX_ALLOWED_TIME_DI, INVALID_DATA_TAG_DI,
    DI_TOOL_AI_RECOMMENDATIONS
)

def _generate_di_summary_report(di_results, with_details=True):
    """Generates the summary report string for the Data Insights section."""
    report_lines = ["---（基於用戶數據與模擬難度分析）---", ""]
    ch1 = di_results.get('chapter_1', {})
    ch2 = di_results.get('chapter_2', {})
    ch3 = di_results.get('chapter_3', {})
    ch4 = di_results.get('chapter_4', {})
    # ch5 = di_results.get('chapter_5', {}) # Ch5 results not directly used in report text
    ch6 = di_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe')

    # 添加調試信息：報告使用的數據框統計
    if diagnosed_df is not None:
        total_rows = len(diagnosed_df)
        invalid_rows = diagnosed_df.get('is_invalid', pd.Series(False, index=diagnosed_df.index)).sum()
        manual_invalid_rows = diagnosed_df.get('is_manually_invalid', pd.Series(False, index=diagnosed_df.index)).sum()
        valid_rows = total_rows - invalid_rows
        logging.info(f"[DI報告] 數據行統計：總數 {total_rows}, 有效 {valid_rows}, 無效 {invalid_rows}, 手動標記無效 {manual_invalid_rows}")
        
        # 按維度統計
        if 'content_domain' in diagnosed_df.columns:
            domains = diagnosed_df['content_domain'].unique()
            for domain in domains:
                domain_df = diagnosed_df[diagnosed_df['content_domain'] == domain]
                domain_total = len(domain_df)
                domain_wrong = domain_df['is_correct'].eq(False).sum()
                logging.info(f"[DI報告追蹤] 領域 {domain} - 總題數: {domain_total}, 錯誤數: {domain_wrong}")
        
        if 'question_type' in diagnosed_df.columns:
            types = diagnosed_df['question_type'].unique()
            for q_type in types:
                type_df = diagnosed_df[diagnosed_df['question_type'] == q_type]
                type_total = len(type_df)
                type_wrong = type_df['is_correct'].eq(False).sum()
                logging.info(f"[DI報告追蹤] 題型 {q_type} - 總題數: {type_total}, 錯誤數: {type_wrong}")
    else:
        logging.warning("[DI報告追蹤] 報告生成時 diagnosed_df 為空")

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
    report_lines.append("**開篇總結（時間策略與有效性）**")
    tp_status = _translate_di(ch1.get('time_pressure', 'Unknown')) # Use translated status directly
    total_time = ch1.get('total_test_time_minutes', 0)
    time_diff = ch1.get('time_difference_minutes', 0)
    # invalid_count_total_effective = ch1.get('invalid_questions_excluded', 0) # This is the total count of effective invalid questions

    manual_invalid_count = 0
    if diagnosed_df is not None and 'is_manually_invalid' in diagnosed_df.columns:
        manual_invalid_count = diagnosed_df['is_manually_invalid'].astype(bool).sum()

    report_lines.append(f"- 整體作答時間：{total_time:.2f} 分鐘（允許 {MAX_ALLOWED_TIME_DI:.1f} 分鐘，剩餘 {time_diff:.2f} 分鐘）")
    report_lines.append(f"- 時間壓力感知：**{tp_status}**")
    
    # 修改警告信息，使其針對手動標記的無效題目
    if manual_invalid_count > 0: 
        report_lines.append(f"- **註記：** 您手動標記了 {manual_invalid_count} 題為無效，這些題目已從部分細化分析中排除。")
    
    # 可選：如果仍需報告自動規則導致的無效，可以額外添加邏輯。
    # 例如，可以計算 total_effective_invalid - manual_invalid_count 來得到大致的自動無效數量，
    # 但需要注意 manual 和 auto 可能有重疊。
    # 目前根據用戶要求，主要調整上述手動無效的報告。
    report_lines.append("")

    # 2. 表現概覽
    report_lines.append("**表現概覽（內容領域對比）**")
    domain_tags = ch2.get('domain_comparison_tags', {})
    if domain_tags.get('significant_diff_error') or domain_tags.get('significant_diff_overtime'):
        if domain_tags.get('poor_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('poor_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **錯誤率** 明顯更高。")
        if domain_tags.get('slow_math_related'): report_lines.append(f"- **{math_related_zh}** 領域的 **超時率** 明顯更高。")
        if domain_tags.get('slow_non_math_related'): report_lines.append(f"- **{non_math_related_zh}** 領域的 **超時率** 明顯更高。")
    else: report_lines.append(f"- {math_related_zh}與{non_math_related_zh}領域的表現在錯誤率和超時率上無顯著差異。")
    report_lines.append("")

    # 3. 核心問題分析
    report_lines.append("**核心問題分析**")
    if sfe_triggered and diagnosed_df is not None and 'is_sfe' in diagnosed_df.columns:
        # 過濾無效題目
        valid_df = diagnosed_df[~diagnosed_df.get('is_invalid', False)].copy()
        sfe_rows = valid_df[valid_df['is_sfe'] == True]
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
        # 確保SFE代碼存在才過濾，否則獲取前2個參數
        if sfe_code in param_counts_all.index:
            top_other_params_codes = param_counts_all[param_counts_all.index != sfe_code].head(2).index.tolist()
        else:
            top_other_params_codes = param_counts_all.head(2).index.tolist()
    if top_other_params_codes:
        report_lines.append("- **高頻潛在問題點：**")
        for param_code in top_other_params_codes: report_lines.append(f"  - {_translate_di(param_code)}")
    elif not sfe_triggered: report_lines.append("- 未識別出明顯的核心問題模式。")
    
    # DI 科詳細數據預覽表（從報告末尾移動到這裡）
    report_lines.append("")
    if diagnosed_df is not None and not diagnosed_df.empty and 'is_correct' in diagnosed_df and 'overtime' in diagnosed_df:
        # 只考慮有效題目
        valid_df = diagnosed_df[~diagnosed_df.get('is_invalid', False)].copy()
        df_problem = valid_df[(valid_df['is_correct'] == False) | (valid_df['overtime'] == True)].copy()
        
        # 添加調試信息：問題數據統計
        problem_total = len(df_problem)
        problem_wrong = df_problem['is_correct'].eq(False).sum() if 'is_correct' in df_problem.columns else 0
        problem_overtime = df_problem['overtime'].sum() if 'overtime' in df_problem.columns else 0
        logging.info(f"[DI報告追蹤] 問題數據統計 - 總題數: {problem_total}, 錯誤數: {problem_wrong}, 超時數: {problem_overtime}")
    else:
        report_lines.append("- (無問題數據可供分析)")
    
    report_lines.append("")

    # 4. 特殊模式觀察
    report_lines.append("**特殊模式觀察**")
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
    report_lines.append("**練習建議**")
    recommendations = ch6.get('recommendations_list', [])
    if not recommendations: 
        report_lines.append("- 根據當前分析，暫無特別的練習建議。請保持全面複習。")
    else:
        # 改回條列式呈現，不使用表格
        for i, rec in enumerate(recommendations): 
            report_lines.append(f"- {rec.get('text', '無建議內容')}")
    report_lines.append("")

    # 7. 後續行動指引
    report_lines.append("**後續行動指引**")
    report_lines.append("- **二級證據參考建議（如考場回憶失效）：**")

        # Second Evidence Suggestion
    if diagnosed_df is not None and not diagnosed_df.empty and 'is_correct' in diagnosed_df and 'overtime' in diagnosed_df:
        report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您按照以上指引查看近期的練習記錄，整理相關錯題或超時題目。")
        
        # Report core issues again
        core_issue_texts = []
        if sfe_triggered: core_issue_texts.append(_translate_di(sfe_code))
        if 'top_other_params_codes' in locals() and top_other_params_codes:
             core_issue_texts.extend([_translate_di(p) for p in top_other_params_codes])
        filtered_core_issues = [issue for issue in core_issue_texts if issue != _translate_di(INVALID_DATA_TAG_DI)]
        if filtered_core_issues:
             report_lines.append(f"  - 請特別留意題目是否反覆涉及報告第三章指出的核心問題：【{', '.join(filtered_core_issues)}】。")
        report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
    else: 
        report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")
    
    # 基於數據動態生成引導反思
    reflection_prompts = []
    
    # 確保有可用的數據
    if diagnosed_df is not None and not diagnosed_df.empty:
        # 只對有問題且有效的題目(錯誤或超時)進行分析以生成反思建議
        valid_df = diagnosed_df[~diagnosed_df.get('is_invalid', False)].copy()
        problem_df = valid_df[(valid_df['is_correct'] == False) | (valid_df['overtime'] == True)].copy()
        
        # 確保必要的列存在
        required_cols = ['question_type', 'content_domain', 'time_performance_category', 'diagnostic_params']
        if all(col in problem_df.columns for col in required_cols) and not problem_df.empty:
            # 根據三個維度進行分組：時間表現、內容領域、題型
            combined_groups = problem_df.groupby(['time_performance_category', 'content_domain', 'question_type'])\
            
            # 對每個組合進行分析並生成獨立的反思提示
            for (time_perf, domain, q_type), group in combined_groups:
                # 跳過正確且正常用時的組（如果有的話）
                if time_perf in ['Normal Time & Correct', 'Fast & Correct']:
                    continue
                
                # 翻譯時間表現、題型和領域
                time_perf_zh = _translate_di(time_perf)
                q_type_zh = _translate_di(q_type)
                domain_zh = _translate_di(domain)
                
                # 獲取該組的所有診斷參數
                all_diagnostic_params = []
                for params_list in group['diagnostic_params']:
                    if isinstance(params_list, list):
                        all_diagnostic_params.extend(params_list)
                
                if all_diagnostic_params:
                    # 去除重複的診斷參數
                    unique_params = list(set(all_diagnostic_params))
                    
                    # 按類別分組
                    params_by_category = {}
                    for param in unique_params:
                        category = DI_PARAM_TO_CATEGORY.get(param, 'Unknown')
                        if category not in params_by_category:
                            params_by_category[category] = []
                        params_by_category[category].append(param)
                    
                    # 生成引導反思提示
                    prompt = f"找尋【{domain_zh}】【{q_type_zh}】的考前做題紀錄，找尋【{time_perf_zh}】的題目，檢討並反思自己是否有：\\n"\
                    
                    # 為每個類別生成標籤文本
                    for category, params in params_by_category.items():
                        # 翻譯類別和參數
                        category_zh = _translate_di(category)
                        params_zh = [_translate_di(p) for p in params]
                        
                        # 按照要求的格式添加
                        prompt += f"\\n【{category_zh}：{', '.join(params_zh)}】"\
                    
                    # 添加結尾
                    prompt += "\\n\\n等問題。"\
                    
                    # 將提示添加到列表中
                    reflection_prompts.append(prompt)
        
    # 如果沒有生成任何反思提示，添加默認提示
    if not reflection_prompts:
        reflection_prompts.append("未發現需要特別反思的問題模式。請繼續保持良好表現。")
    
    # 添加反思提示到報告中
    report_lines.append("\\n**引導反思提示**\\n")
    for prompt in reflection_prompts:
        report_lines.append(f"- {prompt}")
        report_lines.append("")

    # Qualitative Analysis Suggestion (移動到二級證據後面)
    if any(p in all_triggered_params for p in ['DI_LOGICAL_REASONING_ERROR', 'DI_READING_COMPREHENSION_ERROR']):
        report_lines.append("")  
        report_lines.append("- **質化分析建議：**")
        report_lines.append("  - 如果您對報告中指出的某些問題仍感困惑，可以嘗試**提供 2-3 題相關錯題的詳細解題流程跟思路範例**，供顧問進行更深入的個案分析。")

    # Add Tool/AI Prompt Recommendations (使用代碼註釋方式隱藏)
    """
    report_lines.append("- **輔助工具與 AI 提示推薦建議：**")
    report_lines.append("  - 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些可能適用的輔助工具和 AI 提示。系統會根據您觸發的診斷參數組合，推薦相關的資源。請根據您的具體診斷結果選用。")
    recommended_tools_added = False
    # Use all_triggered_params which is a set of unique English codes from Ch3 and Ch4
    # Ensure it exists and is a set
    current_triggered_params = all_triggered_params if isinstance(all_triggered_params, set) else set()

    for param_code in current_triggered_params: # Iterate over unique triggered English param codes
        if param_code in DI_TOOL_AI_RECOMMENDATIONS:
            param_zh = _translate_di(param_code)
            report_lines.append(f"  - **若診斷涉及【{param_zh}】:**")
            for rec_item in DI_TOOL_AI_RECOMMENDATIONS[param_code]:
                report_lines.append(f"    - {rec_item}")
            recommended_tools_added = True
    if not recommended_tools_added:
        report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議。)")
    report_lines.append("")
    """

    # 完成報告，添加調試信息：最終報告內容
    report_text = "\n\n".join(report_lines)  # 使用雙換行符以保持原有格式
    
    # 嘗試從報告文本中提取關鍵數據
    try:
        # 查找所有可能包含題數的行
        total_qs_match = re.search(r'共(\d+)題', report_text)
        if total_qs_match:
            total_qs = int(total_qs_match.group(1))
            logging.info(f"[DI報告追蹤] 從報告中提取的總題數: {total_qs}")
        
        # 查找錯誤數
        error_qs_match = re.search(r'(\d+)題作答錯誤', report_text)
        if error_qs_match:
            error_qs = int(error_qs_match.group(1))
            logging.info(f"[DI報告追蹤] 從報告中提取的錯誤題數: {error_qs}")
            
        # 查找無效題數
        invalid_qs_match = re.search(r'有\s*(\d+)\s*題被標記為無效數據', report_text)
        if invalid_qs_match:
            invalid_qs = int(invalid_qs_match.group(1))
            logging.info(f"[DI報告追蹤] 從報告中提取的無效題數: {invalid_qs}")
    except Exception as e:
        logging.error(f"[DI報告追蹤] 從報告中提取數據時出錯: {e}")
    
    return report_text 
