import pandas as pd
import numpy as np

# --- Q-Specific Constants ---

APPENDIX_A_TRANSLATION = {
    # Quant - Reading & Understanding
    'Q_READING_COMPREHENSION_ERROR': "Quant 閱讀理解: Real 題文字理解錯誤/障礙",
    'Q_PROBLEM_UNDERSTANDING_ERROR': "Quant 題目理解: 數學問題本身理解錯誤",
    # Quant - Concept & Application
    'Q_CONCEPT_APPLICATION_ERROR': "Quant 概念應用: 數學觀念/公式應用錯誤/障礙",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Quant 基礎掌握: 應用不穩定 (Special Focus Error)",
    # Quant - Calculation
    'Q_CALCULATION_ERROR': "Quant 計算: 計算錯誤/障礙",
    # Quant - Efficiency Bottlenecks
    'Q_EFFICIENCY_BOTTLENECK_READING': "Quant 效率瓶頸: Real 題閱讀耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': "Quant 效率瓶頸: 概念/公式思考或導出耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': "Quant 效率瓶頸: 計算過程耗時過長/反覆計算",
    # Behavioral Patterns & Carelessness
    'Q_CARELESSNESS_DETAIL_OMISSION': "行為模式: 粗心 - 忽略細節/條件/陷阱",
    'Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'Q_BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 整體粗心問題 (快而錯比例高)",
    # Comparative Performance (Real vs Pure) - Flags from Ch2
    'poor_real': "比較表現: Real 題錯誤率顯著偏高",
    'poor_pure': "比較表現: Pure 題錯誤率顯著偏高",
    'slow_real': "比較表現: Real 題超時率顯著偏高",
    'slow_pure': "比較表現: Pure 題超時率顯著偏高",
    # Skill Level Override
    # 'skill_override_triggered': "技能覆蓋: 某核心技能整體表現需基礎鞏固" # Handled separately with skill name
}

# --- Q-Specific Helper Functions ---

def _get_translation(param):
    """Helper to get Chinese description, returns param name if not found."""
    return APPENDIX_A_TRANSLATION.get(param, param)

def _map_difficulty_to_label(difficulty):
    """Maps numeric difficulty (b-value) to descriptive label based on Ch7 rules."""
    if difficulty is None or pd.isna(difficulty): # Handle None or NaN difficulty
         return "未知難度 (Unknown)" 
    if difficulty <= -1:
        return "低難度 (Low) / 505+"
    elif -1 < difficulty <= 0:
        return "中難度 (Mid) / 555+"
    elif 0 < difficulty <= 1:
        return "中難度 (Mid) / 605+"
    elif 1 < difficulty <= 1.5:
        return "中難度 (Mid) / 655+"
    elif 1.5 < difficulty <= 1.95:
        return "高難度 (High) / 705+"
    elif 1.95 < difficulty <= 2:
        return "高難度 (High) / 805+"
    else: # Handle values outside the defined ranges
        return f"極高難度 ({difficulty:.2f})"

def _calculate_practice_time_limit(item_time, is_overtime):
    """Calculates the starting practice time limit (Z) based on Ch7 rules."""
    if item_time is None or pd.isna(item_time): # Handle None or NaN time
        return 2.0 # Default target time if original time is missing

    target_time = 2.0
    base_time = item_time - 0.5 if is_overtime else item_time
    # Floor to nearest 0.5
    z_raw = np.floor(base_time * 2) / 2
    # Ensure minimum is target_time
    z = max(z_raw, target_time)
    return z

# --- Q-Specific Diagnosis Logic (Chapters 2-6) ---

def _diagnose_q_internal(df_q):
     """Performs detailed Q diagnosis (Chapters 2-6).
        Assumes df_q contains only valid Q data ('Real' or 'Pure') and necessary columns
        ('question_type', 'Correct', 'overtime', 'question_time',
         'question_fundamental_skill', 'question_difficulty', 'Question ID', 'question_position').
     """
     if df_q.empty:
         # Return structure indicating analysis was skipped or empty
         # Return an empty dictionary to signify no results
         return {}

     # --- Chapter 2: Real vs Pure Analysis ---
     print("    Executing Q - Chapter 2: Real vs Pure Analysis...")
     df_real = df_q[df_q['question_type'] == 'Real'].copy()
     df_pure = df_q[df_q['question_type'] == 'Pure'].copy()

     # Counts
     num_total_real = len(df_real)
     num_total_pure = len(df_pure)
     num_real_errors = df_real['Correct'].eq(False).sum()
     num_pure_errors = df_pure['Correct'].eq(False).sum()
     # Ensure 'overtime' column exists and is boolean
     num_real_overtime = df_real['overtime'].eq(True).sum() if 'overtime' in df_real.columns else 0
     num_pure_overtime = df_pure['overtime'].eq(True).sum() if 'overtime' in df_pure.columns else 0


     # Rates (handle division by zero)
     wrong_rate_real = num_real_errors / num_total_real if num_total_real > 0 else 0
     wrong_rate_pure = num_pure_errors / num_total_pure if num_total_pure > 0 else 0
     over_time_rate_real = num_real_overtime / num_total_real if num_total_real > 0 else 0
     over_time_rate_pure = num_pure_overtime / num_total_pure if num_total_pure > 0 else 0

     print(f"      Real: Total={num_total_real}, Errors={num_real_errors}, Overtime={num_real_overtime}")
     print(f"      Pure: Total={num_total_pure}, Errors={num_pure_errors}, Overtime={num_pure_overtime}")
     print(f"      Rates: ErrReal={wrong_rate_real:.1%}, ErrPure={wrong_rate_pure:.1%}, OTReal={over_time_rate_real:.1%}, OTPure={over_time_rate_pure:.1%}")

     # Check for significant difference (abs difference >= 2)
     significant_error_diff = abs(num_real_errors - num_pure_errors) >= 2
     significant_overtime_diff = abs(num_real_overtime - num_pure_overtime) >= 2

     # Initialize flags
     poor_real = False
     poor_pure = False
     slow_real = False
     slow_pure = False

     if significant_error_diff:
         if wrong_rate_real > wrong_rate_pure: # Compare rates if counts differ sig.
             poor_real = True
             print("      Flag Triggered: poor_real")
         elif wrong_rate_pure > wrong_rate_real:
             poor_pure = True
             print("      Flag Triggered: poor_pure")

     if significant_overtime_diff:
         if over_time_rate_real > over_time_rate_pure:
             slow_real = True
             print("      Flag Triggered: slow_real")
         elif over_time_rate_pure > over_time_rate_real:
             slow_pure = True
             print("      Flag Triggered: slow_pure")

     # Store results
     results_ch2 = pd.DataFrame([
         {'Analysis_Section': 'Chapter 2', 'Metric': 'Total Questions', 'Real_Value': num_total_real, 'Pure_Value': num_total_pure, 'Flag': ''},
         {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Count', 'Real_Value': num_real_errors, 'Pure_Value': num_pure_errors, 'Flag': f'Significant Diff: {significant_error_diff}'},
         {'Analysis_Section': 'Chapter 2', 'Metric': 'Error Rate', 'Real_Value': wrong_rate_real, 'Pure_Value': wrong_rate_pure, 'Flag': f'poor_real={poor_real}, poor_pure={poor_pure}'},
         {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Count', 'Real_Value': num_real_overtime, 'Pure_Value': num_pure_overtime, 'Flag': f'Significant Diff: {significant_overtime_diff}'},
         {'Analysis_Section': 'Chapter 2', 'Metric': 'Overtime Rate', 'Real_Value': over_time_rate_real, 'Pure_Value': over_time_rate_pure, 'Flag': f'slow_real={slow_real}, slow_pure={slow_pure}'}
     ])

     # --- Chapter 3: Error Cause Analysis ---
     print("    Executing Q - Chapter 3: Error Cause Analysis...")
     error_analysis_list = []
     df_errors = df_q[df_q['Correct'] == False].copy()
     average_time_per_type = {} # Initialize

     if not df_errors.empty:
         # Calculate prerequisites
         # Ensure question_time is numeric before grouping
         if pd.api.types.is_numeric_dtype(df_q['question_time']):
             average_time_per_type = df_q.groupby('question_type')['question_time'].mean().to_dict()
             print(f"      Average Times per Type: {average_time_per_type}")
         else:
             print("      Warning: 'question_time' is not numeric. Cannot calculate average times.")
             # Use a default if calculation fails
             average_time_per_type = {'Real': 2.0, 'Pure': 2.0}


         df_correct = df_q[df_q['Correct'] == True]
         max_correct_difficulty_per_skill = {} # Initialize
         if not df_correct.empty and 'question_fundamental_skill' in df_correct.columns and 'question_difficulty' in df_correct.columns:
              # Ensure difficulty is numeric before grouping
              if pd.api.types.is_numeric_dtype(df_correct['question_difficulty']):
                   max_correct_difficulty_per_skill = df_correct.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()
                   print(f"      Max Correct Difficulty per Skill (Top 5): {dict(list(max_correct_difficulty_per_skill.items())[:5])}") # Print first 5 for brevity
              else:
                  print("      Warning: 'question_difficulty' is not numeric. Cannot calculate max correct difficulty.")
         else:
              print("      Warning: Cannot calculate max correct difficulty per skill (missing columns or no correct answers).")

         # Analyze each error
         for index, row in df_errors.iterrows():
             q_id = row['Question ID']
             q_type = row['question_type']
             q_skill = row.get('question_fundamental_skill', 'Unknown Skill') # Handle missing skill
             q_difficulty = row.get('question_difficulty', None) # Handle potentially missing difficulty
             q_time = row.get('question_time', None) # Handle potentially missing time
             is_overtime = row.get('overtime', False) # Default to False if missing

             analysis_result = {
                 'Question ID': q_id,
                 'Skill': q_skill,
                 'Type': q_type,
                 'Difficulty': q_difficulty,
                 'Time': q_time,
                 'Time_Performance': 'Normal Time',
                 'Is_SFE': False,
                 'Possible_Params': []
             }

             # 1. Check Special Focus Error (SFE)
             if q_difficulty is not None and not pd.isna(q_difficulty):
                 max_correct_diff = max_correct_difficulty_per_skill.get(q_skill, -np.inf) # Default to -inf if skill not seen before
                 if q_difficulty < max_correct_diff:
                     analysis_result['Is_SFE'] = True
                     analysis_result['Possible_Params'].append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
                     print(f"        SFE Detected: QID {q_id}, Skill '{q_skill}', Difficulty {q_difficulty:.2f} < Max Correct {max_correct_diff:.2f}")
             else:
                  print(f"        Skipping SFE check for QID {q_id}: Missing difficulty.")

             # 2. Classify Time Performance & Assign Params
             is_relatively_fast = False
             is_normal_time = True # Assume normal initially

             if q_time is not None and not pd.isna(q_time):
                 avg_time = average_time_per_type.get(q_type, 2.0) # Default avg time if type unknown or calc failed
                 is_relatively_fast = q_time < (avg_time * 0.75)
                 is_slow = is_overtime # Use pre-calculated overtime flag (based on Chapter 1)
                 is_normal_time = not is_relatively_fast and not is_slow
             else:
                 is_slow = False # Cannot determine fast/slow/normal without time
                 print(f"        Skipping time performance classification for QID {q_id}: Missing time.")


             possible_params = []
             if is_relatively_fast:
                 analysis_result['Time_Performance'] = 'Fast & Wrong'
                 possible_params.extend(['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR'])
                 if q_type == 'Real': possible_params.append('Q_READING_COMPREHENSION_ERROR')
             elif is_slow:
                 analysis_result['Time_Performance'] = 'Slow & Wrong'
                 possible_params.extend(['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR'])
                 if q_type == 'Real': possible_params.append('Q_READING_COMPREHENSION_ERROR')
                 if analysis_result['Is_SFE']: possible_params.append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE') # Re-add if slow SFE
             elif is_normal_time: # Only applies if time was available
                 analysis_result['Time_Performance'] = 'Normal Time & Wrong'
                 possible_params.extend(['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR'])
                 if q_type == 'Real': possible_params.append('Q_READING_COMPREHENSION_ERROR')
                 if analysis_result['Is_SFE']: possible_params.append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE') # Re-add if normal SFE
             # If time was missing, Time_Performance remains 'Normal Time' but no time-based params are added

             # Add unique params (excluding SFE if already added initially)
             existing_params = set(analysis_result['Possible_Params'])
             for p in possible_params:
                  if p not in existing_params:
                      analysis_result['Possible_Params'].append(p)

             print(f"        Analyzed Error: QID {q_id}, Time Perf: {analysis_result['Time_Performance']}, SFE: {analysis_result['Is_SFE']}, Params: {analysis_result['Possible_Params']}")
             error_analysis_list.append(analysis_result)
     else:
          print("    No errors found in Q section for Chapter 3 analysis.")

     # --- Chapter 4: Correct but Slow Analysis ---
     print("    Executing Q - Chapter 4: Correct but Slow Analysis...")
     correct_slow_analysis_list = []
     # Ensure 'overtime' column exists before filtering
     if 'overtime' in df_q.columns:
         df_correct_slow = df_q[(df_q['Correct'] == True) & (df_q['overtime'] == True)].copy()

         if not df_correct_slow.empty:
             print(f"      Found {len(df_correct_slow)} correct but slow questions.")
             for index, row in df_correct_slow.iterrows():
                 q_id = row['Question ID']
                 q_type = row['question_type']
                 q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
                 q_time = row.get('question_time', None)

                 analysis_result = {
                     'Question ID': q_id,
                     'Skill': q_skill,
                     'Type': q_type,
                     'Time': q_time,
                     'Possible_Params': []
                 }

                 # Assign potential bottleneck parameters
                 possible_params = ['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION']
                 if q_type == 'Real':
                     possible_params.append('Q_EFFICIENCY_BOTTLENECK_READING')

                 analysis_result['Possible_Params'] = possible_params
                 time_str = f"{q_time:.2f}" if q_time is not None else "N/A"
                 print(f"        Correct but Slow: QID {q_id}, Skill '{q_skill}', Type '{q_type}', Time {time_str}, Params: {possible_params}")
                 correct_slow_analysis_list.append(analysis_result)
         else:
             print("    No correct but slow questions found in Q section for Chapter 4 analysis.")
     else:
          print("    Skipping Chapter 4 analysis ('overtime' column missing).")


     # --- Chapter 5: Pattern Observation ---
     print("    Executing Q - Chapter 5: Pattern Observation...")
     early_rushing_items = []
     early_rushing_flag = False
     carelessness_issue = False
     fast_wrong_rate = 0.0

     total_number_of_questions = len(df_q)

     # 1. Early Rushing Check
     if 'question_position' in df_q.columns and 'question_time' in df_q.columns and pd.api.types.is_numeric_dtype(df_q['question_position']) and pd.api.types.is_numeric_dtype(df_q['question_time']):
         first_third_threshold = total_number_of_questions / 3
         # Filter out rows where time might be NaN before comparison
         df_early = df_q[df_q['question_time'].notna() & (df_q['question_position'] <= first_third_threshold) & (df_q['question_time'] < 1.0)]
         if not df_early.empty:
             early_rushing_flag = True
             print(f"      Flag Triggered: Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK ({len(df_early)} items < 1.0 min in first third)")
             for index, row in df_early.iterrows():
                 early_rushing_items.append({
                      'Question ID': row['Question ID'],
                      'Position': row['question_position'],
                      'Time': row['question_time'],
                      'Type': row['question_type'],
                      'Skill': row.get('question_fundamental_skill', 'Unknown Skill'),
                      'Params': ['Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK']
                 })
         else:
             print("      No early rushing (< 1.0 min in first third) detected.")
     else:
         print("      Skipping early rushing check (missing or non-numeric position or time data).")

     # 2. Carelessness Issue Check (Fast & Wrong Rate)
     # average_time_per_type was calculated in Ch3
     if average_time_per_type and 'question_time' in df_q.columns and pd.api.types.is_numeric_dtype(df_q['question_time']): # Ensure avg times were calculated and time is numeric
         # Create temporary column only on valid time rows
         temp_df_q = df_q[df_q['question_time'].notna()].copy()
         temp_df_q['is_relatively_fast'] = temp_df_q.apply(
             lambda row: row['question_time'] < (average_time_per_type.get(row['question_type'], 2.0) * 0.75),
             axis=1
         )
         num_relatively_fast_total = temp_df_q['is_relatively_fast'].sum()
         num_relatively_fast_incorrect = temp_df_q[(temp_df_q['is_relatively_fast'] == True) & (temp_df_q['Correct'] == False)].shape[0]

         if num_relatively_fast_total > 0:
             fast_wrong_rate = num_relatively_fast_incorrect / num_relatively_fast_total
             print(f"      Fast & Wrong Analysis: Total Fast={num_relatively_fast_total}, Incorrect Fast={num_relatively_fast_incorrect}, Rate={fast_wrong_rate:.1%}")
             if fast_wrong_rate > 0.25:
                 carelessness_issue = True
                 print("      Flag Triggered: Q_BEHAVIOR_CARELESSNESS_ISSUE (Fast & Wrong Rate > 25%)")
         else:
             print("      No relatively fast questions found to calculate carelessness rate.")
     else:
          print("      Skipping carelessness check (average times not available or time column missing/non-numeric).")

     # --- Chapter 6: Skill Override Rule ---
     print("    Executing Q - Chapter 6: Skill Override Rule...")
     skill_override_flags = {}
     # Check if skill column exists and overtime column exists
     if 'question_fundamental_skill' in df_q.columns and 'overtime' in df_q.columns:
         grouped_by_skill = df_q.groupby('question_fundamental_skill')
         for skill, group in grouped_by_skill:
             if skill == 'Unknown Skill': continue # Skip unknown skills
             num_total_skill = len(group)
             if num_total_skill == 0: continue

             num_errors_skill = group['Correct'].eq(False).sum()
             num_overtime_skill = group['overtime'].eq(True).sum()

             error_rate_skill = num_errors_skill / num_total_skill
             overtime_rate_skill = num_overtime_skill / num_total_skill

             triggered = False
             if error_rate_skill > 0.5 or overtime_rate_skill > 0.5:
                 triggered = True
                 print(f"      Skill Override Triggered: Skill='{skill}', ErrRate={error_rate_skill:.1%}, OTRate={overtime_rate_skill:.1%}")

             skill_override_flags[skill] = {
                 'triggered': triggered,
                 'error_rate': error_rate_skill,
                 'overtime_rate': overtime_rate_skill,
                 'total_questions': num_total_skill
             }
     else:
         print("      Skipping skill override check (missing 'question_fundamental_skill' or 'overtime' column).")

     # --- Combine results from Chapters 2, 3, 4, 5, and 6 ---
     final_q_results = {
         "chapter2_summary": results_ch2.to_dict('records'),
         "chapter3_error_details": error_analysis_list,
         "chapter4_correct_slow_details": correct_slow_analysis_list,
         "chapter5_patterns": {
             "early_rushing_flag": early_rushing_flag,
             "early_rushing_items": early_rushing_items,
             "carelessness_issue_flag": carelessness_issue,
             "fast_wrong_rate": fast_wrong_rate
         },
         "chapter6_skill_override": skill_override_flags # Added Chapter 6 results
     }

     # This dictionary now contains all the analysis results from Ch 2-6 for Q section.
     return final_q_results

# --- Q-Specific Recommendation Generation (Chapter 7) ---

def _generate_q_recommendations(q_diagnosis_results, exempted_skills):
    """Generates practice recommendations based on Q diagnosis results (Ch 2-6)."""
    print("    Generating Q - Chapter 7: Practice Recommendations...")
    recommendations_by_skill = {}
    processed_override_skills = set()
    all_skills_found = set() # Keep track of all skills encountered

    # Extract necessary data from results dictionary (handle potential missing keys)
    ch2_summary_list = q_diagnosis_results.get('chapter2_summary', [])
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})

    # Get flags from Ch2 summary
    ch2_flags = {}
    for item in ch2_summary_list:
         metric = item.get('Metric')
         flag_str = item.get('Flag', '')
         if metric == 'Error Rate' or metric == 'Overtime Rate':
              # Parse flags like 'poor_real=True, poor_pure=False'
              for flag_pair in flag_str.split(','):
                   if '=' in flag_pair:
                        try:
                            key, value = flag_pair.strip().split('=')
                            ch2_flags[key.strip()] = value.strip().lower() == 'true'
                        except ValueError:
                             print(f"      Warning: Could not parse flag pair: '{flag_pair}'")
    poor_real = ch2_flags.get('poor_real', False)
    slow_pure = ch2_flags.get('slow_pure', False)
    print(f"      Chapter 2 Flags: poor_real={poor_real}, slow_pure={slow_pure}")

    # Combine triggers from Ch3 and Ch4
    triggers = []
    for error in ch3_errors:
        # Only add trigger if skill is known
        skill = error.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
             triggers.append({
                 'skill': skill,
                 'difficulty': error.get('Difficulty'), # Use .get for safety
                 'time': error.get('Time'),
                 'is_overtime': error.get('Time_Performance') == 'Slow & Wrong',
                 'is_sfe': error.get('Is_SFE', False),
                 'q_id': error.get('Question ID'),
                 'q_type': error.get('Type'),
                 'trigger_type': 'error'
             })
             all_skills_found.add(skill)
        else:
            print(f"      Skipping trigger for error QID {error.get('Question ID')}: Unknown Skill")

    for slow in ch4_correct_slow:
        skill = slow.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
             triggers.append({
                 'skill': skill,
                 'difficulty': None, # Difficulty might not be directly relevant for correct-slow recs
                 'time': slow.get('Time'),
                 'is_overtime': True, # By definition of Ch4
                 'is_sfe': False,
                 'q_id': slow.get('Question ID'),
                 'q_type': slow.get('Type'),
                 'trigger_type': 'correct_slow'
             })
             all_skills_found.add(skill)
        else:
            print(f"      Skipping trigger for correct-slow QID {slow.get('Question ID')}: Unknown Skill")

    # --- Generate Recommendations per Skill ---
    for skill in all_skills_found:
        # if skill == 'Unknown Skill': continue # Already filtered out when creating triggers

        skill_recs_list = []
        is_overridden = ch6_override.get(skill, {}).get('triggered', False)
        is_exempted = skill in exempted_skills # Check against passed-in set
        print(f"      Processing Skill: {skill}, Overridden: {is_overridden}, Exempted: {is_exempted}")

        if is_overridden and skill not in processed_override_skills:
            # Generate Macro Recommendation
            trigger_difficulties = [t['difficulty'] for t in triggers if t['skill'] == skill and t['difficulty'] is not None and not pd.isna(t['difficulty'])]
            min_diff_skill = min(trigger_difficulties) if trigger_difficulties else 0 # Default Y_agg if no difficulty data
            y_agg = _map_difficulty_to_label(min_diff_skill)
            z_agg = 2.5 # Fixed Z_agg from markdown
            macro_rec = f"針對【{skill}】技能：由於整體表現有較大提升空間 (錯誤率或超時率 > 50%)，建議優先**全面鞏固基礎**。可從【{y_agg}】難度題目開始系統性練習，掌握核心方法，建議限時【{z_agg}】分鐘。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec, 'priority': 0}) # High priority
            processed_override_skills.add(skill)
            print(f"      Generated MACRO recommendation for Skill: {skill}")

        elif not is_exempted and not is_overridden:
             # Generate Case Recommendations
             skill_triggers = [t for t in triggers if t['skill'] == skill]
             has_real_trigger = any(t.get('q_type') == 'Real' for t in skill_triggers)
             has_pure_trigger = any(t.get('q_type') == 'Pure' for t in skill_triggers)

             for trigger in skill_triggers:
                 y = "未知難度" # Default
                 difficulty = trigger.get('difficulty')
                 time = trigger.get('time')
                 is_overtime_trigger = trigger.get('is_overtime', False)
                 q_id_trigger = trigger.get('q_id', 'N/A')
                 trigger_type = trigger.get('trigger_type')
                 is_sfe_trigger = trigger.get('is_sfe', False)

                 if difficulty is not None and not pd.isna(difficulty):
                     y = _map_difficulty_to_label(difficulty)
                     z = _calculate_practice_time_limit(time, is_overtime_trigger)
                     priority = 1 if is_sfe_trigger else 2 # Prioritize SFE related recs
                     trigger_desc = f"(來源: QID {q_id_trigger}, {trigger_type}, SFE={is_sfe_trigger})"
                     case_rec = f"針對【{skill}】技能下的問題 {trigger_desc}：建議練習【{y}】難度的題目，目標限時【{z}】分鐘。"
                     skill_recs_list.append({'type': 'case', 'text': case_rec, 'priority': priority})
                 elif trigger_type == 'correct_slow': # Handle correct_slow where difficulty might be None
                     # Use a default difficulty or base recommendation on skill average?
                     # For now, recommend practice at a medium level
                     y = "中難度 (Mid) / 605+" # Default practice level for slow-correct
                     z = _calculate_practice_time_limit(time, is_overtime_trigger)
                     priority = 3 # Lower priority than error-based
                     trigger_desc = f"(來源: QID {q_id_trigger}, 正確但慢)"
                     case_rec = f"針對【{skill}】技能下的效率問題 {trigger_desc}：建議練習【{y}】難度的題目，目標限時【{z}】分鐘，注重提升解題速度。"
                     skill_recs_list.append({'type': 'case', 'text': case_rec, 'priority': priority})
                 else:
                      print(f"      Skipping case recommendation for QID {q_id_trigger}: Missing difficulty for error trigger.")


             if skill_recs_list: # Add adjustments only if case recommendations were generated
                  # Apply Chapter 2 Adjustments
                  adjustment_text = ""
                  if poor_real and has_real_trigger:
                       adjustment_text += " **Real題比例建議佔總練習題量2/3。**"
                  if slow_pure and has_pure_trigger:
                       adjustment_text += " **建議此考點練習題量增加。**"
                  if adjustment_text:
                       # Append to the first case recommendation or add as a separate note?
                       # Let's add as a separate note for clarity
                       skill_recs_list.append({'type': 'adjustment', 'text': f"針對【{skill}】的整體練習：{adjustment_text.strip()}", 'priority': 4})
                  print(f"      Generated {len(skill_recs_list)} CASE recommendations/adjustments for Skill: {skill}")

        elif is_exempted:
            # Generate exemption note only if not overridden (macro rec takes precedence)
            if not is_overridden:
                 exemption_note = f"技能【{skill}】表現穩定 (正確且未超時 > 2)，可暫緩針對個別錯題/慢題的練習。"
                 skill_recs_list.append({'type': 'exemption', 'text': exemption_note, 'priority': 5})
                 print(f"      Generated EXEMPTION note for Skill: {skill}")
            else:
                 print(f"      Skill {skill} is Exempted but also Overridden, Macro Recommendation takes precedence.")

        if skill_recs_list:
             # Sort recommendations within the skill: Macro (0), SFE Case (1), Other Case (2), Slow-Correct Case (3), Adjustment (4), Exemption (5)
             recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # Flatten and format the final list
    final_recommendations = []
    # Sort skills based on priority: Overridden skills first, then others alphabetically?
    # For now, iterate dict order which is generally insertion order in Python 3.7+
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_override_skills else 1, s))

    for skill in sorted_skills:
         recs = recommendations_by_skill[skill]
         final_recommendations.append(f"--- 技能: {skill} ---")
         for rec in recs:
              final_recommendations.append(rec['text'])
         final_recommendations.append("") # Add blank line

    if not final_recommendations:
        final_recommendations.append("根據本次分析，未產生具體的量化練習建議。請參考整體診斷總結。")

    print(f"    Finished generating Q recommendations. Total lines: {len(final_recommendations)}")
    return final_recommendations # Return list of recommendation strings


# --- Q-Specific Summary Report Generation (Chapter 8) ---

def _generate_q_summary_report(q_diagnosis_results, q_recommendations, subject_time_pressure_status, num_invalid_questions):
    """Generates the final summary report string based on Q diagnosis and recommendations."""
    print("    Generating Q - Chapter 8: Summary Report...")
    report_lines = []

    # Check if diagnosis results exist
    if not q_diagnosis_results:
         print("      No Q diagnosis results provided. Returning empty report.")
         return "量化 (Quantitative) 部分無有效診斷結果可供報告。"


    # Extract data (safer access with .get)
    ch2_summary = q_diagnosis_results.get('chapter2_summary', [])
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch5_patterns = q_diagnosis_results.get('chapter5_patterns', {})
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})

    # --- Helper to extract triggered params ---
    triggered_params = set()
    for err in ch3_errors: triggered_params.update(err.get('Possible_Params', []))
    for cs in ch4_correct_slow: triggered_params.update(cs.get('Possible_Params', []))
    if ch5_patterns.get('early_rushing_flag', False): triggered_params.add('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    if ch5_patterns.get('carelessness_issue_flag', False): triggered_params.add('Q_BEHAVIOR_CARELESSNESS_ISSUE')
    # --- End Helper ---

    # Get Chapter 2 Flags again for reporting
    ch2_flags = {}
    for item in ch2_summary:
         metric = item.get('Metric')
         flag_str = item.get('Flag', '')
         if metric == 'Error Rate' or metric == 'Overtime Rate':
              for flag_pair in flag_str.split(','):
                   if '=' in flag_pair:
                        try:
                            key, value = flag_pair.strip().split('=')
                            ch2_flags[key.strip()] = value.strip().lower() == 'true'
                        except ValueError:
                             pass # Ignore parsing errors
    triggered_params.update({flag for flag, status in ch2_flags.items() if status})

    report_lines.append("## GMAT 量化 (Quantitative) 診斷報告")
    report_lines.append("--- (基於用戶數據與模擬難度分析) ---")
    report_lines.append("")

    # 1. 開篇總結 (時間)
    report_lines.append("**1. 時間策略與有效性 (摘要)**")
    # Add dynamic content based on passed parameters
    q_time_pressure = subject_time_pressure_status.get('Q', '未知') # Get Q status, default to unknown
    if q_time_pressure is True:
        report_lines.append("- 根據分析，您在量化部分可能處於**時間壓力**下 (測驗時間剩餘不多且末尾部分題目作答過快)。")
    elif q_time_pressure is False:
        report_lines.append("- 根據分析，您在量化部分未處於明顯的時間壓力下。")
    else:
        report_lines.append("- 未能明確判斷量化部分的時間壓力狀態。")

    if num_invalid_questions > 0:
        report_lines.append(f"- 已將 {num_invalid_questions} 道可能因時間壓力影響有效性的題目從詳細分析中排除，以確保診斷準確性。")
    else:
        report_lines.append("- 所有題目數據均被納入詳細分析。")
    report_lines.append("")

    # 2. 表現概覽
    report_lines.append("**2. 表現概覽**")
    real_stats_error = next((item for item in ch2_summary if item.get('Metric') == 'Error Rate'), None)
    pure_stats_error = real_stats_error # In the current structure, they are in the same dict item
    real_stats_ot = next((item for item in ch2_summary if item.get('Metric') == 'Overtime Rate'), None)
    pure_stats_ot = real_stats_ot

    if real_stats_error and real_stats_ot:
        report_lines.append(f"- **Real vs. Pure 題表現:**")
        # Use .get for safer access to values
        real_err_rate = real_stats_error.get('Real_Value', 'N/A')
        real_ot_rate = real_stats_ot.get('Real_Value', 'N/A')
        pure_err_rate = pure_stats_error.get('Pure_Value', 'N/A')
        pure_ot_rate = pure_stats_ot.get('Pure_Value', 'N/A')

        report_lines.append(f"  - Real 題: 錯誤率 {real_err_rate:.1% if isinstance(real_err_rate, (int, float)) else real_err_rate}, 超時率 {real_ot_rate:.1% if isinstance(real_ot_rate, (int, float)) else real_ot_rate}")
        report_lines.append(f"  - Pure 題: 錯誤率 {pure_err_rate:.1% if isinstance(pure_err_rate, (int, float)) else pure_err_rate}, 超時率 {pure_ot_rate:.1% if isinstance(pure_ot_rate, (int, float)) else pure_ot_rate}")

        # Report triggered comparison flags
        triggered_ch2_flags_desc = []
        for flag, status in ch2_flags.items():
             if status and flag in APPENDIX_A_TRANSLATION:
                  triggered_ch2_flags_desc.append(_get_translation(flag))
        if triggered_ch2_flags_desc:
             report_lines.append(f"  - **提示:** {'; '.join(triggered_ch2_flags_desc)}")
    else:
        report_lines.append("- 未能進行 Real vs. Pure 題的詳細比較 (數據不足或缺失)。")

    # Weakest Skills Summary
    # Sort skills by error rate (desc), then overtime rate (desc) if triggered
    weak_skills_triggered = {skill: data for skill, data in ch6_override.items() if data.get('triggered', False)}
    if weak_skills_triggered:
         sorted_weak_skills = sorted(weak_skills_triggered.keys(),
                                     key=lambda s: (weak_skills_triggered[s].get('error_rate', 0), weak_skills_triggered[s].get('overtime_rate', 0)),
                                     reverse=True)
         report_lines.append(f"- **相對弱項技能 (錯誤率或超時率 > 50%):** {', '.join(sorted_weak_skills)}")
    else:
         report_lines.append("- 未發現錯誤率或超時率超過 50% 的核心技能。")
    report_lines.append("") # Add blank line

    # 3. 核心問題診斷
    report_lines.append("**3. 核心問題診斷 (基於觸發的診斷標籤)**")
    core_issues = set()
    sfe_triggered = False
    sfe_skills_involved = set()

    for err in ch3_errors:
        params = err.get('Possible_Params', [])
        skill = err.get('Skill', 'Unknown Skill')
        is_sfe = err.get('Is_SFE', False)
        core_issues.update(p for p in params if p != 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        if is_sfe:
            sfe_triggered = True
            if skill != 'Unknown Skill':
                 sfe_skills_involved.add(skill)

    for cs in ch4_correct_slow:
         core_issues.update(cs.get('Possible_Params', []))

    if sfe_triggered:
        sfe_desc = _get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        if sfe_skills_involved:
             sfe_desc += f" (涉及技能: {', '.join(sorted(list(sfe_skills_involved)))})"
        report_lines.append(f"- **尤其需要注意:** {sfe_desc} - 在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤，表明在這些知識點的應用上可能存在穩定性問題。")

    if core_issues:
         report_lines.append("- **常見問題類型/效率瓶頸可能包括:**")
         # Sort issues alphabetically for consistent reporting
         for issue in sorted(list(core_issues)):
              if issue in APPENDIX_A_TRANSLATION:
                   report_lines.append(f"  - {_get_translation(issue)}")
         # Add SFE again if it wasn't the only issue
         if sfe_triggered and not core_issues: # If SFE was the *only* thing found
              report_lines.append(f"- **主要問題:** {_get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')} (詳見上文)")

    elif not sfe_triggered: # If no core issues and no SFE
        report_lines.append("- 未識別出明顯的核心問題模式 (基於錯誤及效率分析)。")
    report_lines.append("")

    # 4. 模式觀察
    report_lines.append("**4. 作答模式觀察**")
    pattern_found = False
    if ch5_patterns.get('early_rushing_flag', False):
        report_lines.append(f"- **提示:** {_get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')} - 測驗開始階段的部分題目作答速度較快 ({len(ch5_patterns.get('early_rushing_items', []))} 題)，建議注意保持穩定的答題節奏。")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        report_lines.append(f"- **提示:** {_get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')} - 分析顯示，「快而錯」的情況佔比較高 ({ch5_patterns.get('fast_wrong_rate', 0):.1%})，提示可能需關注答題仔細程度。")
        pattern_found = True
    if not pattern_found:
        report_lines.append("- 未發現明顯的特殊作答模式。")
    report_lines.append("")

    # 5. 基礎鞏固提示
    report_lines.append("**5. 基礎鞏固提示**")
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        report_lines.append(f"- **以下核心技能整體表現顯示較大提升空間 (錯誤率或超時率 > 50%)，建議優先系統性鞏固:** {', '.join(sorted(override_skills_list))}")
    else:
        report_lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    report_lines.append("")

    # 6. 練習計劃呈現
    report_lines.append("**6. 練習計劃建議**")
    if q_recommendations:
        report_lines.extend(q_recommendations) # Embed the generated list
    else:
        report_lines.append("- 未生成具體的量化練習建議。")
    report_lines.append("")

    # 7. 後續行動指引
    report_lines.append("**7. 後續行動指引**")
    report_lines.append("- **引導反思:**")
    # --- Dynamic Reflection Prompts ---
    reflection_prompts = []
    if 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params or 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params:
        reflection_prompts.append("  - 回想一下，在做錯的相關題目時，具體是卡在哪個數學知識點或公式上？是完全沒思路，還是知道方法但用錯了？")
    if 'Q_CALCULATION_ERROR' in triggered_params or 'Q_EFFICIENCY_BOTTLENECK_CALCULATION' in triggered_params:
        reflection_prompts.append("  - 是計算過程中容易出錯，還是計算速度偏慢？")
    if 'Q_READING_COMPREHENSION_ERROR' in triggered_params or ch2_flags.get('poor_real', False):
        reflection_prompts.append("  - 對於做錯的文字題，是題目陳述讀不懂，還是無法轉化成數學問題？")
    if 'Q_CARELESSNESS_DETAIL_OMISSION' in triggered_params or ch5_patterns.get('carelessness_issue_flag', False):
        reflection_prompts.append("  - 回想一下，是否經常因為看錯數字、漏掉條件或誤解題意而失分？")

    if not reflection_prompts: # Check if any specific prompts were added
         reflection_prompts.append("  - (本次分析未觸發典型的反思問題，建議結合練習計劃進行)")
    report_lines.extend(reflection_prompts) # Add the generated prompts
    # --- End Dynamic Reflection Prompts ---

    report_lines.append("- **二級證據參考建議:**")
    # --- Dynamic Secondary Evidence Prompt ---
    focus_areas_for_review = set()
    # Use override_skills_list calculated earlier
    sfe_skills = {err['Skill'] for err in ch3_errors if err.get('Is_SFE', False) and err['Skill'] != 'Unknown Skill'}
    slow_wrong_skills = {err['Skill'] for err in ch3_errors if err.get('Time_Performance') == 'Slow & Wrong' and err['Skill'] != 'Unknown Skill'}
    correct_slow_skills = {cs['Skill'] for cs in ch4_correct_slow if cs['Skill'] != 'Unknown Skill'}

    focus_areas_for_review.update(override_skills_list)
    focus_areas_for_review.update(sfe_skills)
    focus_areas_for_review.update(slow_wrong_skills)
    focus_areas_for_review.update(correct_slow_skills)

    review_prompt = "  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題。"
    if focus_areas_for_review:
        review_prompt += f" 請特別關注在以下領域/問題上反覆出現的情況：【{', '.join(sorted(list(focus_areas_for_review)))}】。歸納是哪些知識點或題型（參考報告中的描述）導致問題。"
    else:
        review_prompt += " 歸納是哪些知識點或題型（參考報告中的描述）反覆出現問題。"
    review_prompt += " 如果樣本不足，請在接下來的做題中注意收集。"
    report_lines.append(review_prompt)
    # --- End Dynamic Secondary Evidence Prompt ---

    report_lines.append("- **質化分析建議:**")
    # --- Dynamic Qualitative Analysis Prompt ---
    focus_areas_for_qualitative = set()
    concept_error_skills = {err['Skill'] for err in ch3_errors if 'Q_CONCEPT_APPLICATION_ERROR' in err.get('Possible_Params', []) and err['Skill'] != 'Unknown Skill'}
    problem_understanding_skills = {err['Skill'] for err in ch3_errors if 'Q_PROBLEM_UNDERSTANDING_ERROR' in err.get('Possible_Params', []) and err['Skill'] != 'Unknown Skill'}

    focus_areas_for_qualitative.update(override_skills_list) # Skills needing fundamental review are good candidates
    focus_areas_for_qualitative.update(sfe_skills)     # SFE suggests deeper issues
    focus_areas_for_qualitative.update(concept_error_skills)
    focus_areas_for_qualitative.update(problem_understanding_skills)

    qualitative_prompt = "  - 如果您對診斷指出的錯誤原因仍感困惑，或者上述方法仍無法幫您釐清根本問題"
    if focus_areas_for_qualitative:
         qualitative_prompt += f"，尤其是在【{', '.join(sorted(list(focus_areas_for_qualitative)))}】這些方面，"
    qualitative_prompt += "可提供 2-3 題該類型題目的詳細解題流程和思路，以便進行更深入的個案分析。"
    report_lines.append(qualitative_prompt)
    # --- End Dynamic Qualitative Analysis Prompt ---

    report_lines.append("- **輔助工具與 AI 提示推薦 (基於本次診斷觸發的標籤):**")
    tools_recommended = False
    if 'poor_real' in triggered_params or 'slow_real' in triggered_params or 'Q_EFFICIENCY_BOTTLENECK_READING' in triggered_params:
         report_lines.append("  - 工具: `Dustin_GMAT_Q_Real-Context_Converter` (將純數學題改寫為應用題練習)")
         tools_recommended = True
    # Always recommend classifier? Let's make it conditional based on having errors/slows/overrides
    if ch3_errors or ch4_correct_slow or override_skills_list:
        report_lines.append("  - 工具: `Dustin's GMAT Q: Question Classifier` (輔助整理錯題/效率瓶頸題)")
        tools_recommended = True

    prompts_recommended = False
    # Simplified prompt recommendation logic
    base_prompts = {'Quant-related/05_variant_questions.md', 'Quant-related/06_similar_questions.md'} # Always suggest these for practice
    if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params or 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params or override_skills_list:
        base_prompts.add('Quant-related/01_basic_explanation.md')
        base_prompts.add('Quant-related/03_test_math_concepts.md')
    if any(p in triggered_params for p in ['Q_EFFICIENCY_BOTTLENECK_READING', 'Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'slow_real', 'slow_pure']):
        base_prompts.add('Quant-related/02_quick_math_tricks.md')
    if any(p in triggered_params for p in ['Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_READING_COMPREHENSION_ERROR']):
        base_prompts.add('Quant-related/03_test_math_concepts.md') # Reuse for understanding
    if any(p in triggered_params for p in ['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_BEHAVIOR_CARELESSNESS_ISSUE']):
        base_prompts.add('Quant-related/01_basic_explanation.md') # Reuse for standard steps

    if base_prompts:
         prompts_recommended = True
         report_lines.append("  - AI提示:")
         for prompt in sorted(list(base_prompts)):
             # Add context based on trigger? Maybe too complex for now.
             report_lines.append(f"    - `{prompt}`")


    if not tools_recommended and not prompts_recommended:
         report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議)")

    return "\n".join(report_lines)


# --- Main Q Diagnosis Entry Point ---

def run_q_diagnosis(df_q, exempted_skills, subject_time_pressure_status, num_invalid_questions):
    """
    Runs the full diagnostic process for the Quantitative (Q) section.

    Args:
        df_q (pd.DataFrame): DataFrame containing *filtered* Q data.
        exempted_skills (set): Set of skills exempted from case recommendations.
        subject_time_pressure_status (dict): Dictionary mapping subject to time pressure boolean.
        num_invalid_questions (int): Total number of invalid questions filtered out earlier.

    Returns:
        str: The generated Q summary report string, or a message indicating no report could be generated.
    """
    print("--- Running Quantitative Diagnosis --- ")
    if df_q.empty:
        print("  No valid Q data provided. Skipping Q diagnosis.")
        return "量化 (Quantitative) 部分無有效數據可供診斷。"

    # Perform core diagnosis (Chapters 2-6)
    q_diagnosis_results = _diagnose_q_internal(df_q)

    if not q_diagnosis_results: # Check if internal diagnosis returned empty results
        print("  Q internal diagnosis yielded no results. Skipping recommendations and report.")
        return "量化 (Quantitative) 部分診斷未產生有效結果。"

    # Generate recommendations (Chapter 7)
    q_recommendations = _generate_q_recommendations(q_diagnosis_results, exempted_skills)

    # Generate summary report (Chapter 8)
    q_report = _generate_q_summary_report(q_diagnosis_results, q_recommendations, subject_time_pressure_status, num_invalid_questions)

    print("--- Finished Quantitative Diagnosis --- ")
    return q_report 