"""
Q診斷模塊的建議生成功能

此模塊包含用於Q(Quantitative)診斷的建議生成函數，
用於根據診斷結果生成練習建議和改進方向。
"""

import pandas as pd
# Use i18n system instead of the old translation function
from gmat_diagnosis_app.i18n import translate as t
from gmat_diagnosis_app.diagnostics.q_modules.utils import (
    grade_difficulty_q, 
    calculate_time_limit_from_avg,
    map_difficulty_to_label
)


def generate_q_recommendations(q_diagnosis_results, df_valid_diagnosed_q_data):
    """
    Generates practice recommendations based on Q diagnosis results (Ch 2-6)
    and the provided valid diagnosed Q data for exemption calculation.
    """
    recommendations_by_skill = {}
    processed_override_skills = set()
    
    # --- Chapter 6: Fundamental Skill Exemption Rule ---
    exempted_skills = set()
    all_skills_in_valid_data = set()

    if df_valid_diagnosed_q_data is not None and not df_valid_diagnosed_q_data.empty and \
       'question_fundamental_skill' in df_valid_diagnosed_q_data.columns and \
       'is_correct' in df_valid_diagnosed_q_data.columns and \
       'overtime' in df_valid_diagnosed_q_data.columns:
        
        all_skills_in_valid_data = set(df_valid_diagnosed_q_data['question_fundamental_skill'].dropna().unique()) 
        all_skills_in_valid_data.discard('Unknown Skill')

        for skill_name, group_df in df_valid_diagnosed_q_data.groupby('question_fundamental_skill'):
            if pd.isna(skill_name) or skill_name == 'Unknown Skill':
                continue
            if not group_df.empty:
                # Ensure all questions for this skill are valid (already true due to input df)
                all_correct_in_skill = group_df['is_correct'].all()
                # Ensure 'overtime' column exists and is boolean before .any()
                none_overtime_in_skill = not group_df['overtime'].astype(bool).any() 
                if all_correct_in_skill and none_overtime_in_skill:
                    exempted_skills.add(skill_name)
    
    # 獲取需要的診斷結果
    ch2_flags = q_diagnosis_results.get('chapter2_flags', {})
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})
    poor_real = ch2_flags.get('poor_real', False)
    slow_pure = ch2_flags.get('slow_pure', False)
    
    # 識別建議觸發點 (errors and correct_slow)
    triggers = []
    for error in ch3_errors:
        skill = error.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill': # Add skill to all_skills_in_valid_data here if not done above
            triggers.append({
                'skill': skill, 
                'difficulty': error.get('Difficulty'), 
                'time': error.get('Time'), 
                'is_overtime': error.get('Time_Performance') == 'Slow & Wrong', 
                'is_sfe': error.get('Is_SFE', False), 
                'q_position': error.get('question_position'), 
                'q_type': error.get('Type'), 
                'trigger_type': 'error'
            })
    for slow in ch4_correct_slow:
        skill = slow.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill': # Add skill to all_skills_in_valid_data here if not done above
            triggers.append({
                'skill': skill, 
                'difficulty': slow.get('Difficulty'),
                'time': slow.get('Time'), 
                'is_overtime': True, 
                'is_sfe': False, 
                'q_position': slow.get('question_position'), 
                'q_type': slow.get('Type'), 
                'trigger_type': 'correct_slow'
            })

    # 處理每個技能的建議
    # Iterate over all skills found in valid data to ensure exempted skills are processed for exemption notes
    for skill in all_skills_in_valid_data: 
        if skill in exempted_skills:
            # For exempted skills, we will add a note later. No further processing needed here.
            continue
            
        skill_recs_list = []
        is_overridden = ch6_override.get(skill, {}).get('triggered', False)
        
        if is_overridden and skill not in processed_override_skills:
            override_info = ch6_override.get(skill, {})
            y_agg = override_info.get('y_agg')
            z_agg = override_info.get('z_agg', 2.5)
            
            if y_agg is None: # Fallback if y_agg was None from behavioral.py
                # First, try to find the minimum difficulty from 'error' triggers for this skill
                error_trigger_difficulties = [
                    t['difficulty'] for t in triggers
                    if t['skill'] == skill and t['trigger_type'] == 'error' and
                    t['difficulty'] is not None and not pd.isna(t['difficulty'])
                ]

                if error_trigger_difficulties:
                    min_relevant_difficulty = min(error_trigger_difficulties)
                    y_agg = grade_difficulty_q(min_relevant_difficulty)
                else:
                    # If no 'error' triggers have valid difficulty, try 'correct_slow' triggers
                    slow_trigger_difficulties = [
                        t['difficulty'] for t in triggers
                        if t['skill'] == skill and t['trigger_type'] == 'correct_slow' and
                        t['difficulty'] is not None and not pd.isna(t['difficulty'])
                    ]
                    if slow_trigger_difficulties:
                        min_relevant_difficulty = min(slow_trigger_difficulties)
                        y_agg = grade_difficulty_q(min_relevant_difficulty)
                    else:
                        # If neither 'error' nor 'correct_slow' triggers provide valid difficulty
                        y_agg = t('start_from_basic_difficulty')
            
            macro_rec_text = t('macro_comprehensive_foundation').format(y_agg, z_agg)
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_override_skills.add(skill)
        
        elif not is_overridden: # Only process case recommendations if not overridden
            skill_triggers = [t for t in triggers if t['skill'] == skill]
            has_real_trigger = any(t.get('q_type') == 'Real' for t in skill_triggers)
            has_pure_trigger = any(t.get('q_type') == 'Pure' for t in skill_triggers)
            
            for trigger in skill_triggers:
                difficulty = trigger.get('difficulty')
                time = trigger.get('time')
                is_overtime_trigger = trigger.get('is_overtime', False)
                q_position_trigger = trigger.get('q_position', 'N/A')
                is_sfe_trigger = trigger.get('is_sfe', False)
                
                y = "中難度 (Mid) / 605+" # Default for correct_slow or if difficulty missing
                if difficulty is not None and not pd.isna(difficulty):
                    y = grade_difficulty_q(difficulty)
                
                z = calculate_time_limit_from_avg(time, is_overtime_trigger)
                priority = 1 if is_sfe_trigger else (2 if trigger.get('trigger_type') == 'error' else 3)
                trigger_context = t('question_related_trigger').format(q_position_trigger)
                if trigger.get('trigger_type') == 'correct_slow': 
                    trigger_context += t('correct_but_slow_marker')

                practice_details = t('practice_details').format(y, z)
                if trigger.get('trigger_type') == 'correct_slow': 
                    practice_details = t('practice_details_speed').format(y, z)
                
                case_rec_text = f"{trigger_context}: {practice_details}"
                if is_sfe_trigger: 
                    case_rec_text = t('foundation_instability_marker').format(case_rec_text)
                if z > 4.0: 
                    case_rec_text += t('practice_volume_warning')
                
                skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
            
            if skill_recs_list: # Only add adjustment if there are case recommendations
                adjustment_text = ""
                if poor_real and has_real_trigger: 
                    adjustment_text += t('real_questions_ratio_note')
                if slow_pure and has_pure_trigger: 
                    adjustment_text += t('increase_practice_volume_note')
                
                if adjustment_text.strip():
                    adj_text_full = t('overall_practice_notes').format(adjustment_text.strip())
                    # Find the last case recommendation to append this note to, or add as separate
                    if skill_recs_list and skill_recs_list[-1]['type'] == 'case':
                        skill_recs_list[-1]['text'] += adjustment_text
                    else:
                        skill_recs_list.append({'type': 'adjustment_note', 'text': adj_text_full, 'priority': 4})
        
        if skill_recs_list:
            recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    final_recommendations = []
    # Ensure consistent order for skills in the final report
    report_skill_order = sorted(list(all_skills_in_valid_data.union(set(recommendations_by_skill.keys()))), key=lambda s: (0 if s in processed_override_skills else 1, 0 if s in exempted_skills else 1, s))

    for skill in report_skill_order:
        skill_title = t(skill) if skill != 'Unknown Skill' else t('Unknown Skill')
        final_recommendations.append(t('skill_label').format(skill_title))
        if skill in exempted_skills:
            final_recommendations.append(t('skill_perfect_exemption').format(skill_title))
        elif skill in recommendations_by_skill and recommendations_by_skill[skill]:
            for rec in recommendations_by_skill[skill]:
                final_recommendations.append(f"* {rec['text']}")
        elif skill not in processed_override_skills: # Not exempted, no specific recs, not overridden -> should not happen if logic is correct
            final_recommendations.append(t('no_specific_skill_recommendation').format(skill_title))
        final_recommendations.append("")
    
    if not final_recommendations:
        final_recommendations.append(t('no_quantitative_recommendations'))
    
    return final_recommendations 