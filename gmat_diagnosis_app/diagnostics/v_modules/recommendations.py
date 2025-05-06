"""
V診斷模塊的建議生成功能

此模塊包含用於V(Verbal)診斷的建議生成函數，
用於根據診斷結果生成練習建議和改進方向。
"""

import numpy as np
import pandas as pd
from gmat_diagnosis_app.diagnostics.v_modules.translations import translate_v


def generate_v_recommendations(v_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on V diagnosis results."""
    recommendations = []
    processed_macro_skills = set()

    ch3 = v_diagnosis_results.get('chapter_3', {})
    ch6 = v_diagnosis_results.get('chapter_6', {})
    diagnosed_df = ch3.get('diagnosed_dataframe') # Get the df processed by Ch3
    skill_override_triggered = ch6.get('skill_override_triggered', {})
    all_skills_found = set()

    # 向下取整到最近的 0.5 的倍數的輔助函數
    def floor_to_nearest_0_5(value):
        return np.floor(value * 2) / 2.0

    # Identify problem skills based on the diagnosed dataframe
    if diagnosed_df is not None and not diagnosed_df.empty:
        # Ensure necessary columns exist
        cols_needed = ['is_correct', 'overtime', 'question_fundamental_skill', 'is_invalid']
        if all(col in diagnosed_df.columns for col in cols_needed):
            # Identify rows that are either incorrect or overtime AND are *not* invalid
            problem_mask = ((diagnosed_df['is_correct'] == False) | (diagnosed_df['overtime'] == True)) & \
                           (diagnosed_df['is_invalid'] == False)
            problem_skills = diagnosed_df.loc[problem_mask, 'question_fundamental_skill'].fillna('Unknown Skill').unique()
            all_skills_found = set(skill for skill in problem_skills if skill != 'Unknown Skill')
        else:
             print("Warning: Missing columns needed for identifying problem skills in recommendations.")


    recommendations_by_skill = {}
    for skill in all_skills_found:
        if skill in exempted_skills: continue # Skip exempted skills

        skill_recs_list = []
        is_overridden = skill_override_triggered.get(skill, False)

        # 1. Handle Override Rule
        if is_overridden and skill not in processed_macro_skills:
            skill_display_name = translate_v(skill) # Translate skill name
            macro_rec_text = f"針對【{skill_display_name}】技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_macro_skills.add(skill)

        # 2. Handle Case Recommendations (if not overridden)
        elif not is_overridden:
            if diagnosed_df is not None and not diagnosed_df.empty:
                # Ensure fundamental skill column exists and handle NaNs
                diagnosed_df['question_fundamental_skill'] = diagnosed_df['question_fundamental_skill'].fillna('Unknown Skill')
                # Filter rows for the current skill that have problems AND are not invalid
                skill_problem_mask = (diagnosed_df['question_fundamental_skill'] == skill) & problem_mask
                skill_rows = diagnosed_df[skill_problem_mask]

                if not skill_rows.empty:
                    # Aggregate Difficulty (Y)
                    # Ensure difficulty column exists and is numeric
                    min_difficulty = None
                    if 'question_difficulty' in skill_rows.columns:
                         numeric_diff_skill = pd.to_numeric(skill_rows['question_difficulty'], errors='coerce')
                         if numeric_diff_skill.notna().any():
                             min_difficulty = numeric_diff_skill.min()
                    
                    # Import grade function locally to avoid circular imports
                    from gmat_diagnosis_app.diagnostics.v_modules.utils import grade_difficulty_v
                    y_grade = grade_difficulty_v(min_difficulty)

                    # Aggregate Time Limit (Z)
                    z_minutes_list = []
                    # Use the first valid question type for the skill group
                    q_type_full_name = skill_rows['question_type'].dropna().iloc[0] if not skill_rows['question_type'].dropna().empty else 'Critical Reasoning' # Default to full name
                    # Convert to abbreviation for map lookup
                    if q_type_full_name == 'Critical Reasoning':
                        q_type_abbr = 'CR'
                    elif q_type_full_name == 'Reading Comprehension':
                        q_type_abbr = 'RC'
                    else:
                        q_type_abbr = None # Handle unexpected types

                    # 使用核心邏輯文件中的目標時間
                    target_time_map = {'CR': 2.0, 'RC': 1.5}
                    target_time_minutes = target_time_map.get(q_type_abbr, 2.0) # 默認使用 CR 的目標時間

                    for _, row in skill_rows.iterrows():
                        q_time_minutes = row['question_time']
                        is_overtime_trigger = bool(row.get('overtime', False))
                        if pd.notna(q_time_minutes):
                            # 根據 V-Doc 計算 base_time
                            base_time_minutes = q_time_minutes - 0.5 if is_overtime_trigger else q_time_minutes
                            # 確保不為負數
                            base_time_minutes = max(0, base_time_minutes)
                            # 使用向下取整到最近 0.5 的倍數的函數計算 Z_raw
                            z_raw_minutes = floor_to_nearest_0_5(base_time_minutes)
                            # 確保不低於目標時間
                            z_individual = max(z_raw_minutes, target_time_minutes)
                            z_minutes_list.append(z_individual)

                    # 確定這項技能的最終聚合起始練習限時，取該技能下所有題目計算出的 Z_individual 中的最大值
                    max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    z_text = f"{max_z_minutes:.1f} 分鐘"
                    target_time_text = f"{target_time_minutes:.1f} 分鐘" # Use the calculated target time

                    # Check for SFE within the group
                    group_sfe = skill_rows['is_sfe'].any() if 'is_sfe' in skill_rows.columns else False
                    sfe_prefix = "**基礎掌握不穩** - " if group_sfe else ""
                    skill_display_name = translate_v(skill) # Translate skill name

                    # Construct recommendation text
                    case_rec_text = f"{sfe_prefix}針對【{skill_display_name}】建議練習【{y_grade}】難度題目，起始練習限時建議為【{z_text}】(最終目標時間: {target_time_text})。"

                    # Add overlong alert if needed
                    if max_z_minutes - target_time_minutes > 2.0:
                        case_rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效**"

                    # Determine priority
                    priority = 1 if group_sfe else 2
                    skill_recs_list.append({
                        'type': 'case_aggregated', 'text': case_rec_text,
                        'priority': priority, 'is_sfe': group_sfe
                    })

        # Add recommendations for the skill if any were generated
        if skill_recs_list:
            recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # Assemble Final List
    final_recommendations = []
    # 首先顯示標記為 SFE 的建議
    all_skills_sorted = []
    sfe_skills = []
    normal_skills = []
    
    for skill in recommendations_by_skill:
        if any(rec['is_sfe'] for rec in recommendations_by_skill[skill] if 'is_sfe' in rec):
            sfe_skills.append(skill)
        else:
            normal_skills.append(skill)
    
    # 優先顯示 SFE 標記的技能，之後是普通技能
    all_skills_sorted = sorted(sfe_skills) + sorted(normal_skills)
    
    for skill in all_skills_sorted:
        recs = recommendations_by_skill[skill]
        skill_display_name = translate_v(skill) # Translate skill name
        final_recommendations.append({'type': 'skill_header', 'text': f"--- 技能: {skill_display_name} ---"})
        final_recommendations.extend(recs)
        final_recommendations.append({'type': 'spacer', 'text': ""})

    return final_recommendations 