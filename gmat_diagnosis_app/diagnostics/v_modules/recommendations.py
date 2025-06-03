"""
V診斷模塊的建議生成功能

此模塊包含用於V(Verbal)診斷的建議生成函數，
用於根據診斷結果生成練習建議和改進方向。
"""

import numpy as np
import pandas as pd
# Use i18n system instead of the old translation function
from gmat_diagnosis_app.i18n import t


def generate_v_recommendations(v_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on V diagnosis results."""
    output_recommendations = []
    exemption_recommendations = [] # Initialize here
    case_recommendations = []
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

    # --- Start: Add Exemption Notes --- 
    exemption_notes_added = False
    for skill in sorted(list(all_skills_found)): # Iterate over all skills found in data
        if skill in exempted_skills:
            skill_display_name = t(skill)
            exempt_text = f"{t('v_recommendation_targeting_skill')}【{skill_display_name}】{t('v_recommendation_skill_stable_performance')}。"
            exemption_recommendations.append({
                'type': 'exemption', 
                'text': exempt_text, 
                'skill': skill, 
                'priority': -1 # Highest priority for exemptions
            })
            exemption_notes_added = True
    if exemption_notes_added and exemption_recommendations: # Add a spacer if exemptions were added
        exemption_recommendations.append({'type': 'spacer', 'text': ""})
    # --- End: Add Exemption Notes ---

    recommendations_by_skill = {}
    for skill in all_skills_found:
        if skill in exempted_skills: continue # Skip exempted skills

        skill_recs_list = []
        is_overridden = skill_override_triggered.get(skill, False)

        # 1. Handle Override Rule
        if is_overridden and skill not in processed_macro_skills:
            skill_display_name = t(skill) # Translate skill name
            macro_rec_text = f"{t('v_recommendation_targeting_skill')}【{skill_display_name}】{t('v_recommendation_skill_consolidation')}。"
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
                    z_text = f"{max_z_minutes:.1f} {t('di_recommendation_minute')}"
                    target_time_text = f"{target_time_minutes:.1f} {t('di_recommendation_minute')}" # Use the calculated target time

                    # Check for SFE within the group
                    group_sfe = skill_rows['is_sfe'].any() if 'is_sfe' in skill_rows.columns else False
                    sfe_prefix = t("v_foundation_instability_marker") if group_sfe else ""
                    skill_display_name = t(skill) # Translate skill name

                    # Construct recommendation text
                    case_rec_text = f"{sfe_prefix}{t('v_recommendation_targeting_skill')}【{skill_display_name}】{t('v_recommendation_practice_suggestion')}【{y_grade}】{t('v_recommendation_difficulty_initial_time')}【{z_text}】({t('v_recommendation_final_target_time')}: {target_time_text})。"

                    # Add overlong alert if needed
                    if max_z_minutes - target_time_minutes > 2.0:
                        case_rec_text += f" **{t('v_recommendation_excessive_time_warning')}**"

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
    # The main 'recommendations' list already contains exemption notes if any.
    # Now, we add skill-specific recommendations (macro or case-aggregated)
    # and then sort everything together if needed, or just append.

    # We will sort skills to ensure SFE-related skills come first, then normal, then macro if not SFE.
    # However, the current structure adds to recommendations_by_skill then sorts.
    # Let's adapt to ensure exemptions are at the top, then SFE, then others.

    final_recommendations = []
    if exemption_recommendations: # Add exemption notes first if they exist
        final_recommendations.extend(sorted(exemption_recommendations, key=lambda x: x.get('skill', '')))
        # recommendations list currently holds only exemptions. We clear it to reuse for skill-specific recs or adapt the flow.
        # For clarity, let's rename the list holding exemption notes.
        exemption_recommendations = list(exemption_recommendations) # Keep a copy
        recommendations = [] # Clear for skill-specific processing

    # The rest of the function populates recommendations_by_skill
    # ... (existing logic for populating recommendations_by_skill) ...

    # Assemble Final List: Start with exemptions, then SFE skills, then normal skills
    # This part needs to be after recommendations_by_skill is populated.
    # The original code for assembling final_recommendations is okay, but needs exemptions at the top.
    
    # Re-think the final assembly part to integrate exemptions at the top.
    # The original code for assembling final_recommendations:
    # final_recommendations = []
    # all_skills_sorted = [] (sfe_skills + normal_skills)
    # for skill in all_skills_sorted: ... add header and recs ...
    # This means exemptions should be added before this loop.

    # Corrected Final Assembly Logic:
    output_recommendations.extend(exemption_recommendations) # Add sorted exemptions first

    all_skills_for_recs_sorted = []
    sfe_skills_for_recs = []
    normal_skills_for_recs = []

    # Use keys from recommendations_by_skill as these are the ones with actual recs
    skills_with_generated_recs = list(recommendations_by_skill.keys())

    for skill_key in skills_with_generated_recs:
        # Check if any recommendation for this skill is SFE
        is_sfe_skill_group = False
        if skill_key in recommendations_by_skill and recommendations_by_skill[skill_key]:
             is_sfe_skill_group = any(rec.get('is_sfe', False) for rec in recommendations_by_skill[skill_key])
        
        if is_sfe_skill_group:
            sfe_skills_for_recs.append(skill_key)
        else:
            normal_skills_for_recs.append(skill_key)
    
    all_skills_for_recs_sorted = sorted(sfe_skills_for_recs) + sorted(normal_skills_for_recs)
    
    if all_skills_for_recs_sorted and output_recommendations and output_recommendations[-1].get('type') != 'spacer':
        # Add a spacer if exemptions were added and we are about to add skill recs
        if exemption_notes_added:
             output_recommendations.append({'type': 'spacer', 'text': ""})

    for skill_item in all_skills_for_recs_sorted:
        recs_for_skill = recommendations_by_skill[skill_item]
        skill_display_name_item = t(skill_item) 
        output_recommendations.append({'type': 'skill_header', 'text': t('v_skill_header_format').format(skill_display_name_item)})
        output_recommendations.extend(recs_for_skill)
        output_recommendations.append({'type': 'spacer', 'text': ""})

    return output_recommendations 