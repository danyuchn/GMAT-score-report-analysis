"""
Q診斷模塊的建議生成功能

此模塊包含用於Q(Quantitative)診斷的建議生成函數，
用於根據診斷結果生成練習建議和改進方向。
"""

import pandas as pd
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation
from gmat_diagnosis_app.diagnostics.q_modules.utils import map_difficulty_to_label, calculate_practice_time_limit


def generate_q_recommendations(q_diagnosis_results):
    """
    Generates practice recommendations based on Q diagnosis results (Ch 2-6).
    
    實現核心邏輯文件第七章的建議生成步驟：
    1. 確定建議觸發點
    2. 生成與初步分類建議
    3. 整理與輸出建議列表
    """
    recommendations_by_skill = {}
    processed_override_skills = set()
    all_skills_found = set()
    
    # 獲取需要的診斷結果
    ch2_flags = q_diagnosis_results.get('chapter2_flags', {})
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})
    poor_real = ch2_flags.get('poor_real', False)
    slow_pure = ch2_flags.get('slow_pure', False)
    
    # 識別所有的建議觸發點
    triggers = []
    # 處理錯誤觸發點
    for error in ch3_errors:
        skill = error.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
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
            all_skills_found.add(skill)
    
    # 處理正確但超時觸發點
    for slow in ch4_correct_slow:
        skill = slow.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
            triggers.append({
                'skill': skill, 
                'difficulty': None, 
                'time': slow.get('Time'), 
                'is_overtime': True, 
                'is_sfe': False, 
                'q_position': slow.get('question_position'), 
                'q_type': slow.get('Type'), 
                'trigger_type': 'correct_slow'
            })
            all_skills_found.add(skill)

    # 檢查基礎能力豁免（第六章）
    # 假設我們沒有明確的豁免數據，但可以添加一個檢查邏輯來實現
    exempted_skills = set()
    # 這裡可以添加豁免技能識別邏輯，例如檢查某技能是否所有題目都正確且不超時

    # 處理每個技能的建議
    for skill in all_skills_found:
        # 檢查豁免
        if skill in exempted_skills:
            continue
            
        skill_recs_list = []
        is_overridden = ch6_override.get(skill, {}).get('triggered', False)
        
        # 處理技能覆蓋（第六章）
        if is_overridden and skill not in processed_override_skills:
            override_info = ch6_override.get(skill, {})
            y_agg = override_info.get('y_agg')
            z_agg = override_info.get('z_agg', 2.5)
            
            # 如果沒有指定 y_agg，就找該技能的最低難度
            if y_agg is None:
                trigger_difficulties = [t['difficulty'] for t in triggers if t['skill'] == skill and t['difficulty'] is not None and not pd.isna(t['difficulty'])]
                min_diff_skill = min(trigger_difficulties) if trigger_difficulties else 0
                y_agg = map_difficulty_to_label(min_diff_skill)
            
            # 生成宏觀建議
            macro_rec_text = f"**優先全面鞏固基礎** (整體錯誤率或超時率 > 50%): 從 {y_agg} 難度開始, 建議限時 {z_agg} 分鐘。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0})
            processed_override_skills.add(skill)
        
        # 處理個案建議
        elif not is_overridden:
            skill_triggers = [t for t in triggers if t['skill'] == skill]
            has_real_trigger = any(t.get('q_type') == 'REAL' for t in skill_triggers)
            has_pure_trigger = any(t.get('q_type') == 'PURE' for t in skill_triggers)
            
            # 處理每個觸發點
            for trigger in skill_triggers:
                difficulty = trigger.get('difficulty')
                time = trigger.get('time')
                is_overtime_trigger = trigger.get('is_overtime', False)
                q_position_trigger = trigger.get('q_position', 'N/A')
                trigger_type = trigger.get('trigger_type')
                is_sfe_trigger = trigger.get('is_sfe', False)
                
                # 處理有明確難度的觸發點（通常是錯誤）
                if difficulty is not None and not pd.isna(difficulty):
                    y = map_difficulty_to_label(difficulty)
                    z = calculate_practice_time_limit(time, is_overtime_trigger)
                    priority = 1 if is_sfe_trigger else 2
                    trigger_context = f"第 {q_position_trigger} 題相關"
                    practice_details = f"練習 {y}, 限時 {z} 分鐘。"
                    
                    case_rec_text = f"{trigger_context}: {practice_details}"
                    
                    # 為 SFE 添加特殊標記
                    if is_sfe_trigger: 
                        case_rec_text = f"*基礎掌握不穩* {case_rec_text}"
                    
                    # 為超長限時添加提醒
                    if z > 4.0:
                        case_rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效**"
                    
                    skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
                
                # 處理無明確難度的觸發點（如正確但超時）
                elif trigger_type == 'correct_slow':
                    y = "中難度 (Mid) / 605+"  # 默認使用中難度
                    q_position_trigger = trigger.get('q_position', 'N/A')
                    time = trigger.get('time')
                    is_overtime_trigger = trigger.get('is_overtime', True)
                    z = calculate_practice_time_limit(time, is_overtime_trigger)
                    priority = 3
                    trigger_context = f"第 {q_position_trigger} 題相關 (正確但慢)"
                    practice_details = f"練習 {y}, 限時 {z} 分鐘 (提升速度)。"
                    
                    case_rec_text = f"{trigger_context}: {practice_details}"
                    
                    # 為超長限時添加提醒
                    if z > 4.0:
                        case_rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效**"
                    
                    skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
            
            # 添加第二章的側重規則
            adjustment_text = ""
            if poor_real and has_real_trigger: 
                adjustment_text += " **Real題比例建議佔總練習題量2/3。**"
            if slow_pure and has_pure_trigger: 
                adjustment_text += " **建議此考點練習題量增加。**"
            
            if adjustment_text:
                adj_text = f"整體練習註記: {adjustment_text.strip()}"
                skill_recs_list.append({'type': 'adjustment', 'text': adj_text, 'priority': 4})
        
        # 如果有建議，添加到對應技能
        if skill_recs_list:
            recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # 生成最終建議列表
    final_recommendations = []
    
    # 添加豁免技能說明
    for skill in exempted_skills:
        final_recommendations.append(f"--- 技能: {skill} ---")
        final_recommendations.append(f"* 技能 {skill} 表現完美，已豁免練習建議。")
        final_recommendations.append("")
    
    # 優先列出覆蓋技能的建議，再列出其他技能的建議
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_override_skills else 1, s))
    
    for skill in sorted_skills:
        recs = recommendations_by_skill[skill]
        final_recommendations.append(f"--- 技能: {skill} ---")
        
        # 優先列出 SFE 相關的建議
        sfe_recs = [rec for rec in recs if '*基礎掌握不穩*' in rec['text']]
        non_sfe_recs = [rec for rec in recs if '*基礎掌握不穩*' not in rec['text']]
        
        # 先輸出 SFE 建議
        for rec in sfe_recs:
            final_recommendations.append(f"* {rec['text']}")
        
        # 再輸出其他建議
        for rec in non_sfe_recs:
            final_recommendations.append(f"* {rec['text']}")
        
        final_recommendations.append("")
    
    # 如果沒有任何建議，添加默認信息
    if not final_recommendations:
        final_recommendations.append("根據本次分析，未產生具體的量化練習建議。請參考整體診斷總結。")
    
    return final_recommendations 