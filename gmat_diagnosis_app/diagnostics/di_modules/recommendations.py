"""
DI診斷模組 - 建議生成
處理練習建議的生成邏輯
"""

import pandas as pd
import numpy as np
import math
import logging

from gmat_diagnosis_app.i18n import translate as t
from .utils import grade_difficulty_di, format_rate


def generate_di_recommendations(df_diagnosed, override_results, domain_tags, time_pressure):
    """Generates practice recommendations based on Chapters 3, 5, and 2 results."""
    if 'question_type' not in df_diagnosed.columns or 'content_domain' not in df_diagnosed.columns: # Ensure content_domain also exists
        logging.warning("[DI Reco Init] 'question_type' or 'content_domain' missing in df_diagnosed. Returning empty recommendations.")
        return []

    # Ensure 'is_sfe' column exists, defaulting to False if not present.
    # This addresses the issue where missing 'is_sfe' caused Case Recommendations to be skipped.
    if 'is_sfe' not in df_diagnosed.columns:
        logging.warning("[DI Reco Init] 'is_sfe' column was missing in df_diagnosed. Initializing with False.")
        df_diagnosed['is_sfe'] = False

    # Ensure 'diagnostic_params' column exists, defaulting to empty list if not present
    if 'diagnostic_params' not in df_diagnosed.columns:
        logging.warning("[DI Reco Init] 'diagnostic_params' column was missing in df_diagnosed. Initializing with empty lists.")
        df_diagnosed['diagnostic_params'] = [[] for _ in range(len(df_diagnosed))]
    else:
        # Ensure its content is list-like for consistent processing later
        df_diagnosed['diagnostic_params'] = df_diagnosed['diagnostic_params'].apply(
            lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x] if isinstance(x, str) else [])
        )

    # question_types_in_data = df_diagnosed['question_type'].unique()
    # question_types_valid = [qt for qt in question_types_in_data if pd.notna(qt)]
    # # Initialize recommendations_by_type properly for all valid types
    # recommendations_by_type = {q_type: [] for q_type in question_types_valid if q_type is not None}
    
    CORE_DI_QUESTION_TYPES = ["Data Sufficiency", "Two-part analysis", "Graph and Table", "Multi-source reasoning"]
    recommendations_by_type = {q_type: [] for q_type in CORE_DI_QUESTION_TYPES}
    
    processed_override_types = set()

    # Exemption Rule (per type + domain, as per DI Doc Chapter 5)
    exempted_type_domain_combinations = set()
    if 'is_correct' in df_diagnosed.columns and 'overtime' in df_diagnosed.columns:
        # Group by type and domain to check exemption status for each combination
        grouped_for_exemption = df_diagnosed.groupby(['question_type', 'content_domain'], observed=False, dropna=False)
        for name, group_df in grouped_for_exemption:
            q_type, domain = name
            if pd.isna(q_type) or pd.isna(domain): continue # Skip if type or domain is NaN

            # 按照文檔第五章標準：首先篩選有效題目
            valid_questions = group_df[group_df.get('is_invalid', False) == False]
            if valid_questions.empty:
                continue  # 如果沒有有效題目，跳過此組合
            
            # 條件一：所有有效題目必須全部正確 
            condition1_all_correct = valid_questions['is_correct'].all()
            
            # 條件二：所有有效題目必須全部無超時
            condition2_no_overtime = ~valid_questions['overtime'].any()
            
            # 同時滿足兩個條件才豁免
            if condition1_all_correct and condition2_no_overtime:
                exempted_type_domain_combinations.add((q_type, domain))

    # Macro Recommendations
    math_related_zh = t('Math Related') # Translate once
    non_math_related_zh = t('Non-Math Related') # Translate once
    for q_type, override_info in override_results.items():
        if q_type in recommendations_by_type and override_info.get('override_triggered'):
            # Check if all content domains for this q_type are exempted
            all_domains_for_this_q_type_in_data = df_diagnosed[df_diagnosed['question_type'] == q_type]['content_domain'].unique()
            all_domains_for_this_q_type_in_data = [d for d in all_domains_for_this_q_type_in_data if pd.notna(d)] # Filter out NaN domains

            if not all_domains_for_this_q_type_in_data: # If the q_type has no actual content domains in the data
                pass # Proceed to generate macro recommendation as we can't confirm full exemption
            else:
                all_sub_domains_exempted = True
                for domain_for_q_type in all_domains_for_this_q_type_in_data:
                    if (q_type, domain_for_q_type) not in exempted_type_domain_combinations:
                        all_sub_domains_exempted = False
                        break
                
                if all_sub_domains_exempted:
                    logging.info(f"[DI Reco Logic] SKIPPING Macro recommendation for q_type '{q_type}' because all its sub-domains are exempted (perfect performance).")
                    # We still add to processed_override_types because if an override was triggered,
                    # it implies a general issue, and we might not want case recommendations
                    # even if the macro one is suppressed due to perfect sub-domain performance.
                    # This aligns with the existing logic of adding to processed_override_types here.
                    processed_override_types.add(q_type) 
                    continue # Skip generating the macro recommendation for this q_type

            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if pd.notna(z_agg) else "未知限時"
            error_rate_str = format_rate(override_info.get('triggering_error_rate', 0.0))
            overtime_rate_str = format_rate(override_info.get('triggering_overtime_rate', 0.0))
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {error_rate_str} 或 超時率 {overtime_rate_str}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({'type': 'macro', 'text': rec_text, 'question_type': q_type})
            processed_override_types.add(q_type)

    # Case Recommendations
    target_times_minutes = {'Data Sufficiency': 2.0, 'Two-part analysis': 3.0, 'Graph and Table': 3.0, 'Multi-source reasoning': 1.5}
    required_cols = ['is_correct', 'overtime', 'question_type', 'content_domain', 'question_difficulty', 'question_time', 'is_sfe', 'diagnostic_params']
    
    # Logging to check columns in df_diagnosed and the condition for case recommendations - REMOVED by AI
    # logging.info(f"[DI Reco Pre-Check] df_diagnosed columns: {list(df_diagnosed.columns)}")
    missing_cols = [col for col in required_cols if col not in df_diagnosed.columns]
    if missing_cols:
        logging.warning(f"[DI Reco Pre-Check] Missing required columns in df_diagnosed for Case Recommendations: {missing_cols}") # Keep warning
    condition_met = all(col in df_diagnosed.columns for col in required_cols)
    # logging.info(f"[DI Reco Pre-Check] Condition 'all(col in df_diagnosed.columns for col in required_cols)' is {condition_met}.") # REMOVED by AI

    if condition_met:
        df_trigger = df_diagnosed[((df_diagnosed['is_correct'] == False) | (df_diagnosed['overtime'] == True))]
        
        if not df_trigger.empty:
            try:
                grouped_triggers = df_trigger.groupby(['question_type', 'content_domain'], observed=False, dropna=False) # Handle potential NaNs in grouping keys
                for name, group_df in grouped_triggers:
                    q_type, domain = name

                    if pd.isna(q_type) or pd.isna(domain):
                        continue

                    # Original skip logic (kept for completeness)
                    if q_type in processed_override_types:
                        continue
                    if (q_type, domain) in exempted_type_domain_combinations:
                        continue

                    min_difficulty_score = group_df['question_difficulty'].min()
                    y_grade = grade_difficulty_di(min_difficulty_score)

                    # --- Calculate Target Time (MODIFIED FOR MSR) & Max Z ---
                    max_z_minutes = None # Initialize
                    target_time_minutes = None # Initialize
                    if q_type == 'Multi-source reasoning':
                        target_time_minutes = 6.0 if time_pressure else 7.0 # Use group target time based on pressure
                        # Calculate max_z_minutes for MSR using group logic
                        if 'msr_group_id' in group_df.columns and 'msr_group_total_time' in df_diagnosed.columns:
                            triggering_group_ids = group_df['msr_group_id'].unique()
                            # 過濾掉NaN的group_id
                            triggering_group_ids = [gid for gid in triggering_group_ids if pd.notna(gid)]
                            
                            if triggering_group_ids:
                                group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
                                valid_group_times = group_times.dropna()
                                
                                if len(valid_group_times) > 0:
                                    max_group_time_minutes = valid_group_times.max()
                                    if pd.notna(max_group_time_minutes) and max_group_time_minutes > 0:
                                        calculated_z_agg = math.floor(max_group_time_minutes * 2) / 2.0
                                        max_z_minutes = max(calculated_z_agg, 6.0) # Apply 6.0 min floor
                                    else: 
                                        logging.warning(f"[DI Case Reco MSR] Invalid max_group_time_minutes for MSR ({q_type}, {domain}). Defaulting Z to 6.0 min.")
                                        max_z_minutes = 6.0
                                else: 
                                    logging.warning(f"[DI Case Reco MSR] No valid group times found for MSR ({q_type}, {domain}). Defaulting Z to 6.0 min.")
                                    max_z_minutes = 6.0
                            else:
                                logging.warning(f"[DI Case Reco MSR] No valid group IDs found for MSR ({q_type}, {domain}). Defaulting Z to 6.0 min.")
                                max_z_minutes = 6.0
                        else: 
                            logging.warning(f"[DI Case Reco MSR] Missing msr_group_id or msr_group_total_time for MSR ({q_type}, {domain}). Defaulting Z to 6.0 min.")
                            max_z_minutes = 6.0
                    else: # Original logic for non-MSR types
                        target_time_minutes = target_times_minutes.get(q_type, 2.0) # Use dict lookup for non-MSR target
                        # Calculate max_z_minutes for non-MSR using single-question logic
                        z_minutes_list = []
                        for _, row in group_df.iterrows():
                            q_time_minutes = row['question_time']
                            is_overtime = row['overtime']
                            if pd.notna(q_time_minutes):
                                base_time_minutes = max(0, q_time_minutes - 0.5 if is_overtime else q_time_minutes)
                                z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                                z = max(z_raw_minutes, target_time_minutes) # Apply non-MSR target time floor
                                z_minutes_list.append(z)
                        max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    
                    # Ensure max_z_minutes has a value (fallback to target time)
                    if max_z_minutes is None:
                         max_z_minutes = target_time_minutes # Use the determined target time (MSR or other)
                         logging.warning(f"[DI Case Reco] max_z_minutes calculation resulted in None for ({q_type}, {domain}). Falling back to target_time: {target_time_minutes}")
                    
                    # Ensure target_time_minutes is defined before logging/text generation
                    if target_time_minutes is None: # Fallback if somehow target_time wasn't set
                         target_time_minutes = target_times_minutes.get(q_type, 2.0) # Default lookup
                         logging.warning(f"[DI Case Reco] target_time_minutes was None for ({q_type}, {domain}) before text generation. Falling back to default: {target_time_minutes}")

                    # --- Generate Recommendation Text ---                    
                    z_text = f"{max_z_minutes:.1f} 分鐘" # Initial suggested time text
                    target_time_text = f"{target_time_minutes:.1f} 分鐘" # Final target time text
                    group_sfe = group_df['is_sfe'].any()
                    diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)]) # More concise set union
                    # Note: diag_params_codes collected but not currently used in recommendation text

                    problem_desc = "錯誤或超時"
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    translated_domain = t(domain) # Translate domain

                    rec_text = f"{sfe_prefix}針對 **{translated_domain}** 領域的 **{q_type}** 題目 ({problem_desc})，"
                    rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"
                    if max_z_minutes - target_time_minutes > 2.0:
                        rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    if q_type in recommendations_by_type:
                         recommendations_by_type[q_type].append({
                             'type': 'case_aggregated', 
                             'is_sfe': group_sfe, 
                             'domain': domain, 
                             'difficulty_grade': y_grade, 
                             'time_limit_z': max_z_minutes, # Starting suggested time
                             'target_time_minutes': target_time_minutes, # <-- ADDED Final target time
                             'text': rec_text, 
                             'question_type': q_type
                         })

            except Exception as e:
                logging.error(f"[DI Reco Error] Case recommendations failed for df_trigger: {e}")

    # Flatten and sort recommendations
    all_recommendations = []
    for q_type, recs in recommendations_by_type.items():
        all_recommendations.extend(recs)

    # Sort by question type priority and then by type (macro first, then case recommendations)
    def sort_key(rec):
        type_priority = CORE_DI_QUESTION_TYPES.index(rec['question_type']) if rec['question_type'] in CORE_DI_QUESTION_TYPES else 999
        type_rank = 0 if rec['type'] == 'macro' else 1
        return (type_priority, type_rank)

    all_recommendations.sort(key=sort_key)
    return all_recommendations 