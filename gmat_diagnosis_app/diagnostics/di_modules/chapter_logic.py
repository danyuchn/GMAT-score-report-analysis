import pandas as pd
import numpy as np
import math # Keep math for _check_foundation_override if it moves here later

from .constants import SUSPICIOUS_FAST_MULTIPLIER, CARELESSNESS_THRESHOLD
from .translation import _translate_di # Needed later for other functions
from .utils import _grade_difficulty_di, _format_rate


def _diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """
    Analyzes root causes row-by-row based on Chapter 3 logic from the MD document.
    Adds 'diagnostic_params' and 'is_sfe' columns.
    Relies on 'question_type', 'content_domain', 'question_difficulty', 'question_time',
    'is_correct', 'overtime', 'msr_reading_time', 'is_first_msr_q'.
    """
    # NOTE: This function still uses iterrows() and could be further optimized,
    # but that involves more complex refactoring than requested. Keeping as is.
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = 'Unknown' # Added init
        return df

    all_diagnostic_params = []
    all_is_sfe = []
    all_time_performance_categories = []

    max_diff_dict = {}
    if isinstance(max_diffs, pd.DataFrame) and not max_diffs.empty:
        for q_type_col in max_diffs.columns:
            q_type = q_type_col
            for domain in max_diffs.index:
                 max_val = max_diffs.loc[domain, q_type]
                 if pd.notna(max_val) and max_val != -np.inf:
                     max_diff_dict[(q_type, domain)] = max_val

    msr_reading_threshold = ch1_thresholds.get('MSR_READING', 1.5)
    msr_single_q_threshold = ch1_thresholds.get('MSR_SINGLE_Q', 1.5)

    for index, row in df.iterrows():
        params = []
        sfe_triggered = False

        q_type = row.get('question_type', 'Unknown')
        q_domain = row.get('content_domain', 'Unknown')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime = bool(row.get('overtime', False))
        msr_reading_time = row.get('msr_reading_time', None)
        is_first_msr_q = bool(row.get('is_first_msr_q', False))

        is_relatively_fast = False
        is_slow = is_overtime
        is_normal_time = False
        avg_time_for_type = avg_times.get(q_type, np.inf)

        if pd.notna(q_time) and avg_time_for_type != np.inf:
            if q_time < (avg_time_for_type * 0.75):
                is_relatively_fast = True
            if not is_relatively_fast and not is_slow:
                is_normal_time = True

        if not is_correct and pd.notna(q_diff):
            max_correct_diff_key = (q_type, q_domain)
            max_correct_diff = max_diff_dict.get(max_correct_diff_key, -np.inf)
            if q_diff < max_correct_diff:
                sfe_triggered = True
                params.append('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        current_time_performance_category = 'Unknown'
        if is_correct:
            if is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif is_slow: current_time_performance_category = 'Slow & Correct'
            else: current_time_performance_category = 'Normal Time & Correct'
        else:
            if is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif is_slow: current_time_performance_category = 'Slow & Wrong'
            else: current_time_performance_category = 'Normal Time & Wrong'

        # --- Detailed Diagnostic Logic ---
        # A. Data Sufficiency
        if q_type == 'Data Sufficiency':
            if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # B. Two-Part Analysis
        elif q_type == 'Two-part analysis':
             if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # C. Graph & Table
        elif q_type == 'Graph and Table':
             if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_DATA_EXTRACTION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
             elif q_domain == 'Non-Math Related':
                if is_slow and not is_correct: params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.extend(['DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # D. Multi-Source Reasoning
        elif q_type == 'Multi-source reasoning':
            if is_first_msr_q and pd.notna(msr_reading_time) and msr_reading_time > msr_reading_threshold: params.append('DI_MSR_READING_COMPREHENSION_BARRIER')
            if not is_first_msr_q and pd.notna(q_time) and q_time > msr_single_q_threshold: params.append('DI_MSR_SINGLE_Q_BOTTLENECK')
            if q_domain == 'Math Related':
                if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR', 'DI_CALCULATION_ERROR'])
                elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_CONCEPT', 'DI_EFFICIENCY_BOTTLENECK_CALCULATION'])
                elif (is_normal_time or is_relatively_fast) and not is_correct:
                    params.append('DI_CONCEPT_APPLICATION_ERROR')
                    if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
            elif q_domain == 'Non-Math Related':
                 if is_slow and not is_correct: params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_READING_COMPREHENSION_ERROR', 'DI_GRAPH_TABLE_INTERPRETATION_ERROR', 'DI_LOGICAL_REASONING_ERROR', 'DI_QUESTION_TYPE_SPECIFIC_ERROR'])
                 elif is_slow and is_correct: params.extend(['DI_EFFICIENCY_BOTTLENECK_INTEGRATION', 'DI_EFFICIENCY_BOTTLENECK_READING', 'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE', 'DI_EFFICIENCY_BOTTLENECK_LOGIC'])
                 elif (is_normal_time or is_relatively_fast) and not is_correct:
                     params.extend(['DI_READING_COMPREHENSION_ERROR', 'DI_LOGICAL_REASONING_ERROR'])
                     if is_relatively_fast: params.append('DI_CARELESSNESS_DETAIL_OMISSION')
        # --- End Detailed Logic ---

        # Add the results to our lists
        all_diagnostic_params.append(params)
        all_is_sfe.append(sfe_triggered)
        all_time_performance_categories.append(current_time_performance_category)

    # Update the dataframe with all the collected information
    df['diagnostic_params'] = all_diagnostic_params
    df['is_sfe'] = all_is_sfe
    df['time_performance_category'] = all_time_performance_categories

    return df


def _observe_di_patterns(df, avg_times):
    """
    Observes special patterns like carelessness or early rushing (Chapter 4).
    Combines averages with diagnostic output from Chapter 3.
    Uses 'question_type', 'question_time', 'is_correct', 'question_position'.
    """
    analysis = {
        'triggered_behavioral_params': [],
        'carelessness_issue_triggered': False,
        'fast_wrong_rate': 0.0,
        'early_rushing_risk_triggered': False,
        'early_rushing_questions': []
    }
    if df.empty: return analysis

    if 'diagnostic_params' not in df.columns:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
    else:
        df['diagnostic_params'] = df['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else [])

    # 檢查並確保time_performance_category存在
    if 'time_performance_category' not in df.columns:
        df['time_performance_category'] = 'Unknown'
    else:
        # 確保沒有空值或空字串
        df['time_performance_category'] = df['time_performance_category'].fillna('Unknown')
        df.loc[df['time_performance_category'] == '', 'time_performance_category'] = 'Unknown'

    # 1. Carelessness Issue - 使用核心邏輯文件中的定義
    fast_wrong_count = 0
    fast_total_count = 0
    if 'time_performance_category' in df.columns:
        fast_wrong_count = df[df['time_performance_category'] == 'Fast & Wrong'].shape[0]
        fast_total_count = df[(df['time_performance_category'].str.startswith('Fast'))].shape[0]
    
    # 如果沒有time_performance_category或計數為0，使用原始邏輯計算fast_wrong_rate
    if fast_total_count == 0:
        # 原始邏輯使用is_relatively_fast的計算
        is_relatively_fast_mask = pd.Series(False, index=df.index)
        for q_type, group in df.groupby('question_type'):
            avg_time = avg_times.get(q_type, np.inf)
            if avg_time != np.inf:
                is_relatively_fast_mask.loc[group.index] = group['question_time'].notna() & (group['question_time'] < avg_time * 0.75)

        fast_total_count = is_relatively_fast_mask.sum()
        if fast_total_count > 0:
            fast_wrong_mask = is_relatively_fast_mask & (df['is_correct'] == False)
            fast_wrong_count = fast_wrong_mask.sum()

    # 計算快錯率並設置觸發條件
    if fast_total_count > 0:
        fast_wrong_rate = fast_wrong_count / fast_total_count
        analysis['fast_wrong_rate'] = fast_wrong_rate
        # 使用核心邏輯文件中定義的閾值判斷粗心問題
        if fast_wrong_rate > CARELESSNESS_THRESHOLD:
            analysis['carelessness_issue_triggered'] = True
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_CARELESSNESS_ISSUE')
            # Mark these questions in diagnostic_params
            if 'time_performance_category' in df.columns:
                for idx, row in df[df['time_performance_category'] == 'Fast & Wrong'].iterrows():
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_CARELESSNESS_DETAIL_OMISSION']
            else:
                for idx in df.index[fast_wrong_mask]:
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_CARELESSNESS_DETAIL_OMISSION']

    # 2. Early Rushing Risk (遵循核心邏輯文件第四章)
    if 'question_position' in df.columns and 'question_time' in df.columns:
        # 定義前三分之一的題目位置
        positions = df['question_position'].sort_values().unique()
        first_third_positions = positions[:max(1, len(positions) // 3)]
        
        # 獲取前三分之一題目的平均時間
        first_third_mask = df['question_position'].isin(first_third_positions)
        first_third_avg_time = df.loc[first_third_mask, 'question_time'].mean()
        
        # 使用 SUSPICIOUS_FAST_MULTIPLIER 判斷過快題目，而非硬編碼的 1.0 分鐘
        suspicious_fast_threshold = first_third_avg_time * SUSPICIOUS_FAST_MULTIPLIER
        early_rushing_mask = first_third_mask & df['question_time'].notna() & (df['question_time'] < suspicious_fast_threshold)
        early_rushing_questions = df.loc[early_rushing_mask].sort_values('question_position')
        
        if len(early_rushing_questions) > 0:
            analysis['early_rushing_risk_triggered'] = True
            analysis['early_rushing_questions'] = early_rushing_questions['question_position'].tolist()
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
            # Mark these questions in diagnostic_params
            for idx in early_rushing_questions.index:
                if 'diagnostic_params' in df.columns:
                    df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK']

    return analysis 

def _check_foundation_override(df, type_metrics):
    """Checks for foundation override rule for each question type."""
    override_results = {}
    if df.empty or 'question_type' not in df.columns: return override_results

    question_types_in_data = df['question_type'].unique()

    for q_type in question_types_in_data:
        if pd.isna(q_type): continue

        metrics = type_metrics.get(q_type, {})
        error_rate = metrics.get('error_rate', 0.0)
        overtime_rate = metrics.get('overtime_rate', 0.0)
        triggered = False
        y_agg = None
        z_agg = None

        # 使用 0.50（50%）作為閾值，與核心邏輯文件中的規定一致
        if error_rate > 0.50 or overtime_rate > 0.50:
            triggered = True
            # Check required columns exist before filtering
            req_cols = ['question_type', 'is_correct', 'overtime', 'question_difficulty', 'question_time']
            if all(c in df.columns for c in req_cols):
                triggering_mask = (
                    (df['question_type'] == q_type) &
                    ((df['is_correct'] == False) | (df['overtime'] == True))
                )
                triggering_df = df[triggering_mask]

                if not triggering_df.empty:
                    if triggering_df['question_difficulty'].notna().any():
                         min_difficulty = triggering_df['question_difficulty'].min()
                         y_agg = _grade_difficulty_di(min_difficulty)
                    else: y_agg = "未知難度"

                    if triggering_df['question_time'].notna().any():
                         max_time_minutes = triggering_df['question_time'].max()
                         # Ensure max_time_minutes is not NaN before floor operation
                         if pd.notna(max_time_minutes):
                             # 使用向下取整到 0.5 的倍數函數計算 Z 值
                             z_agg = math.floor(max_time_minutes * 2) / 2.0
                         else: z_agg = None
                    else: z_agg = None
                else:
                     y_agg = "未知難度"
                     z_agg = None
            else: # Handle missing columns case
                y_agg = "未知難度"
                z_agg = None


        override_results[q_type] = {
            'override_triggered': triggered,
            'Y_agg': y_agg,
            'Z_agg': z_agg,
            'triggering_error_rate': error_rate,
            'triggering_overtime_rate': overtime_rate
        }
    return override_results


def _generate_di_recommendations(df_diagnosed, override_results, domain_tags):
    """Generates practice recommendations based on Chapters 3, 5, and 2 results."""
    if 'question_type' not in df_diagnosed.columns: return []

    question_types_in_data = df_diagnosed['question_type'].unique()
    question_types_valid = [qt for qt in question_types_in_data if pd.notna(qt)]
    recommendations_by_type = {q_type: [] for q_type in question_types_valid}
    processed_override_types = set()

    # Exemption Rule
    exempted_types = set()
    if 'is_correct' in df_diagnosed.columns and 'overtime' in df_diagnosed.columns:
        for q_type in question_types_valid:
            type_df = df_diagnosed[df_diagnosed['question_type'] == q_type]
            if not type_df.empty and not ((type_df['is_correct'] == False) | (type_df['overtime'] == True)).any():
                exempted_types.add(q_type)

    # Macro Recommendations
    math_related_zh = _translate_di('Math Related') # Translate once
    non_math_related_zh = _translate_di('Non-Math Related') # Translate once
    for q_type, override_info in override_results.items():
        if q_type in recommendations_by_type and override_info.get('override_triggered'):
            if q_type in exempted_types: continue
            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if pd.notna(z_agg) else "未知限時"
            error_rate_str = _format_rate(override_info.get('triggering_error_rate', 0.0))
            overtime_rate_str = _format_rate(override_info.get('triggering_overtime_rate', 0.0))
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {error_rate_str} 或 超時率 {overtime_rate_str}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({'type': 'macro', 'text': rec_text, 'question_type': q_type})
            processed_override_types.add(q_type)

    # Case Recommendations
    target_times_minutes = {'Data Sufficiency': 2.0, 'Two-part analysis': 3.0, 'Graph and Table': 3.0, 'Multi-source reasoning': 2.0}
    required_cols = ['is_correct', 'overtime', 'question_type', 'content_domain', 'question_difficulty', 'question_time', 'is_sfe', 'diagnostic_params']
    if all(col in df_diagnosed.columns for col in required_cols):
        df_trigger = df_diagnosed[((df_diagnosed['is_correct'] == False) | (df_diagnosed['overtime'] == True))]
        if not df_trigger.empty:
            try:
                grouped_triggers = df_trigger.groupby(['question_type', 'content_domain'], observed=False, dropna=False) # Handle potential NaNs in grouping keys
                for name, group_df in grouped_triggers:
                    q_type, domain = name
                    if pd.isna(q_type) or pd.isna(domain): continue
                    if q_type in processed_override_types or q_type in exempted_types: continue

                    min_difficulty_score = group_df['question_difficulty'].min()
                    y_grade = _grade_difficulty_di(min_difficulty_score)

                    z_minutes_list = []
                    target_time_minutes = target_times_minutes.get(q_type, 2.0)
                    for _, row in group_df.iterrows():
                        q_time_minutes = row['question_time']
                        is_overtime = row['overtime']
                        if pd.notna(q_time_minutes):
                            base_time_minutes = max(0, q_time_minutes - 0.5 if is_overtime else q_time_minutes)
                            z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                            z = max(z_raw_minutes, target_time_minutes)
                            z_minutes_list.append(z)

                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{target_time_minutes:.1f} 分鐘"
                    group_sfe = group_df['is_sfe'].any()
                    diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)]) # More concise set union
                    translated_params_list = _translate_di(list(diag_params_codes)) # Translate here if needed for text, else done later

                    problem_desc = "錯誤或超時"
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    translated_domain = _translate_di(domain) # Translate domain

                    rec_text = f"{sfe_prefix}針對 **{translated_domain}** 領域的 **{q_type}** 題目 ({problem_desc})，"
                    rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"
                    if max_z_minutes - target_time_minutes > 2.0:
                        rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    if q_type in recommendations_by_type:
                         recommendations_by_type[q_type].append({'type': 'case_aggregated', 'is_sfe': group_sfe, 'domain': domain, 'difficulty_grade': y_grade, 'time_limit_z': max_z_minutes, 'text': rec_text, 'question_type': q_type})
            except Exception:
                 # Error handling or logging can be added here
                 pass

    # Final Assembly
    final_recommendations = []
    for q_type in sorted(list(exempted_types)):
         if q_type in question_types_valid:
              final_recommendations.append({'type': 'exemption_note', 'text': f"您在 **{q_type}** 題型上表現穩定，所有題目均在時限內正確完成，無需針對性個案練習。", 'question_type': q_type})

    for q_type in question_types_valid:
        if q_type in exempted_types: continue
        type_recs = recommendations_by_type.get(q_type, [])
        if not type_recs: continue
        type_recs.sort(key=lambda rec: 0 if rec['type'] == 'macro' else 1)

        focus_note = ""
        has_math_case_agg = any(r.get('domain') == 'Math Related' for r in type_recs if r['type'] == 'case_aggregated')
        has_non_math_case_agg = any(r.get('domain') == 'Non-Math Related' for r in type_recs if r['type'] == 'case_aggregated')

        # Use pre-translated domain names
        if (domain_tags.get('poor_math_related') or domain_tags.get('slow_math_related')) and has_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{math_related_zh}` 題目的練習比例。**"
        if (domain_tags.get('poor_non_math_related') or domain_tags.get('slow_non_math_related')) and has_non_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{non_math_related_zh}` 題目的練習比例。**"

        if focus_note and type_recs:
            # Find last non-macro index safely
            last_agg_rec_index = -1
            for i in range(len(type_recs) - 1, -1, -1):
                 if type_recs[i]['type'] != 'macro': # Attach to last non-macro/exemption
                     last_agg_rec_index = i
                     break
            if last_agg_rec_index != -1:
                 type_recs[last_agg_rec_index]['text'] += focus_note
            else: # Attach to the only rec (must be macro if list not empty)
                 type_recs[-1]['text'] += focus_note


        final_recommendations.extend(type_recs)

    type_order_final = ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table']
    final_recommendations.sort(key=lambda x: type_order_final.index(x['question_type']) if x.get('question_type') in type_order_final else 99)

    return final_recommendations 