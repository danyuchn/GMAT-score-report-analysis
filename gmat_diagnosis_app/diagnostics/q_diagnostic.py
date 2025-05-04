import pandas as pd
import numpy as np

# --- Q-Specific Constants ---
# Define max_allowed_time here as per MD Ch0
MAX_ALLOWED_TIME_Q = 45.0 # minutes
# Define fast end threshold here as per MD Ch1
FAST_END_THRESHOLD_MINUTES = 1.0
# Define time diff threshold for pressure as per MD Ch1
TIME_DIFF_PRESSURE_THRESHOLD = 3.0
# Tag for invalid data
INVALID_DATA_TAG_Q = "數據無效：用時過短（受時間壓力影響）"

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
    'skill_override_triggered': "技能覆蓋: 某核心技能整體表現需基礎鞏固 (錯誤率或超時率>50%)"
}

# --- Q-Specific Helper Functions ---

def _get_translation(param):
    """Helper to get Chinese description, returns param name if not found."""
    return APPENDIX_A_TRANSLATION.get(param, param)

def _format_rate(rate_value):
    """Formats a value as percentage if numeric, otherwise returns as string."""
    if isinstance(rate_value, (int, float)):
        return f"{rate_value:.1%}"
    else:
        return str(rate_value) # Ensure it's a string

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

# --- Q-Specific Root Cause Diagnosis --- 
def _diagnose_q_root_causes(df, avg_times, max_diffs):
    """Analyzes root causes row-by-row and adds 'diagnostic_params', 'is_sfe', and 'time_performance_category' columns."""
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = ''
        return df

    all_diagnostic_params = []
    all_is_sfe = []
    all_time_performance_categories = []

    max_diff_dict = max_diffs # Assuming max_diffs is already the correct dict {skill: max_difficulty}

    for index, row in df.iterrows():
        q_type = row['question_type']
        q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime = bool(row.get('overtime', False))
        is_invalid = bool(row.get('is_invalid', False)) # Get invalid status

        current_params = []
        current_is_sfe = False
        current_time_performance_category = 'Unknown'

        # 1. Check SFE (only if incorrect AND NOT invalid)
        if not is_correct and not is_invalid and q_diff is not None and not pd.isna(q_diff):
            max_correct_diff = max_diff_dict.get(q_skill, -np.inf)
            if q_diff < max_correct_diff:
                current_is_sfe = True
                current_params.append('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # 2. Determine Time Flags
        is_relatively_fast = False
        is_slow = is_overtime
        avg_time_for_type = avg_times.get(q_type, 2.0) # Default 2.0 mins for Q

        if q_time is not None and not pd.isna(q_time):
            if q_time < (avg_time_for_type * 0.75):
                is_relatively_fast = True

        # 3. Assign Time Performance Category
        if is_correct:
            if is_relatively_fast:
                current_time_performance_category = 'Fast & Correct'
            elif is_slow:
                current_time_performance_category = 'Slow & Correct'
            else:
                current_time_performance_category = 'Normal Time & Correct'
        else: # Incorrect
            if is_relatively_fast:
                current_time_performance_category = 'Fast & Wrong'
            elif is_slow:
                current_time_performance_category = 'Slow & Wrong'
            else:
                current_time_performance_category = 'Normal Time & Wrong'

        # 4. Assign Diagnostic Params based on Time Performance & Correctness
        if not is_correct:
            if current_time_performance_category == 'Fast & Wrong':
                current_params.extend(['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR'])
                if q_type == 'REAL': current_params.append('Q_READING_COMPREHENSION_ERROR')
            elif current_time_performance_category == 'Slow & Wrong':
                current_params.extend(['Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR'])
                if q_type == 'REAL': current_params.append('Q_EFFICIENCY_BOTTLENECK_READING')
                # SFE already added if applicable
            else: # Normal Time & Wrong
                current_params.extend(['Q_CONCEPT_APPLICATION_ERROR', 'Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_CALCULATION_ERROR'])
                if q_type == 'REAL': current_params.append('Q_READING_COMPREHENSION_ERROR')
        elif current_time_performance_category == 'Slow & Correct': # Correct but Slow -> Efficiency issues
             current_params.append('Q_EFFICIENCY_BOTTLENECK_CONCEPT')
             current_params.append('Q_EFFICIENCY_BOTTLENECK_CALCULATION')
             if q_type == 'REAL': current_params.append('Q_EFFICIENCY_BOTTLENECK_READING')

        # Remove duplicates and ensure SFE is first if present
        unique_params = list(dict.fromkeys(current_params)) # Simpler way to remove duplicates while preserving order somewhat
        if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in unique_params:
             unique_params.remove('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
             unique_params.insert(0, 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')

        # Append the invalid tag if the row is marked as invalid
        if is_invalid:
            # Check if tag already exists to avoid duplicates if run multiple times
            if INVALID_DATA_TAG_Q not in unique_params:
                 unique_params.append(INVALID_DATA_TAG_Q)

        all_diagnostic_params.append(unique_params)
        all_is_sfe.append(current_is_sfe)
        all_time_performance_categories.append(current_time_performance_category)

    # Assign lists back to DataFrame
    if len(all_diagnostic_params) == len(df):
        df['diagnostic_params'] = all_diagnostic_params
        df['is_sfe'] = all_is_sfe
        df['time_performance_category'] = all_time_performance_categories
    else:
        print("ERROR: Length mismatch in _diagnose_q_root_causes. Skipping assignment.")
        if 'diagnostic_params' not in df.columns: df['diagnostic_params'] = [[] for _ in range(len(df))]
        if 'is_sfe' not in df.columns: df['is_sfe'] = False
        if 'time_performance_category' not in df.columns: df['time_performance_category'] = ''

    return df

# --- Q-Specific Diagnosis Logic (Chapters 2-6) ---

def _diagnose_q_internal(df_q):
     """Performs detailed Q diagnosis (Chapters 2-6).
        Assumes df_q contains only valid Q data ('Real' or 'Pure') with necessary columns
        including 'overtime' and 'is_invalid' (though 'is_invalid' should be False here).
     """
     if df_q.empty:
         # Return structure indicating analysis was skipped or empty
         # Return an empty dictionary to signify no results
         return {}

     # --- Chapter 2: Real vs Pure Analysis ---
     print("    Executing Q - Chapter 2: Real vs Pure Analysis...")
     # Use uppercase to match standardized data from app.py
     df_real = df_q[df_q['question_type'] == 'REAL'].copy()
     df_pure = df_q[df_q['question_type'] == 'PURE'].copy()

     # DEBUG: Print value counts for the relevant columns
     print(f"      DEBUG: df_real['is_correct'] counts:\n{df_real['is_correct'].value_counts(dropna=False)}")
     print(f"      DEBUG: df_real['overtime'] counts:\n{df_real['overtime'].value_counts(dropna=False)}")
     print(f"      DEBUG: df_pure['is_correct'] counts:\n{df_pure['is_correct'].value_counts(dropna=False)}")
     print(f"      DEBUG: df_pure['overtime'] counts:\n{df_pure['overtime'].value_counts(dropna=False)}")

     # Counts
     num_total_real = len(df_real)
     num_total_pure = len(df_pure)
     num_real_errors = df_real['is_correct'].eq(False).sum()
     num_pure_errors = df_pure['is_correct'].eq(False).sum()
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
     df_errors = df_q[df_q['is_correct'] == False].copy()
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


         df_correct = df_q[df_q['is_correct'] == True]
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
             q_position = row['question_position']
             q_type = row['question_type']
             q_skill = row.get('question_fundamental_skill', 'Unknown Skill') # Handle missing skill
             q_difficulty = row.get('question_difficulty', None) # Handle potentially missing difficulty
             q_time = row.get('question_time', None) # Handle potentially missing time
             is_overtime = row.get('overtime', False) # Default to False if missing

             analysis_result = {
                 'question_position': q_position,
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
                     print(f"        SFE Detected: Position {q_position}, Skill '{q_skill}', Difficulty {q_difficulty:.2f} < Max Correct {max_correct_diff:.2f}")
             else:
                  print(f"        Skipping SFE check for Position {q_position}: Missing difficulty.")

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
                 print(f"        Skipping time performance classification for Position {q_position}: Missing time.")


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

             print(f"        Analyzed Error: Position {q_position}, Time Perf: {analysis_result['Time_Performance']}, SFE: {analysis_result['Is_SFE']}, Params: {analysis_result['Possible_Params']}")
             error_analysis_list.append(analysis_result)
     else:
          print("    No errors found in Q section for Chapter 3 analysis.")

     # --- Chapter 4: Correct but Slow Analysis ---
     print("    Executing Q - Chapter 4: Correct but Slow Analysis...")
     correct_slow_analysis_list = []
     # Ensure 'overtime' column exists before filtering
     if 'overtime' in df_q.columns:
         df_correct_slow = df_q[(df_q['is_correct'] == True) & (df_q['overtime'] == True)].copy()

         if not df_correct_slow.empty:
             print(f"      Found {len(df_correct_slow)} correct but slow questions.")
             for index, row in df_correct_slow.iterrows():
                 q_position = row['question_position']
                 q_type = row['question_type']
                 q_skill = row.get('question_fundamental_skill', 'Unknown Skill')
                 q_time = row.get('question_time', None)

                 analysis_result = {
                     'question_position': q_position,
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
                 print(f"        Correct but Slow: Position {q_position}, Skill '{q_skill}', Type '{q_type}', Time {time_str}, Params: {possible_params}")
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
                      'question_position': row['question_position'],
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
         num_relatively_fast_incorrect = temp_df_q[(temp_df_q['is_relatively_fast'] == True) & (temp_df_q['is_correct'] == False)].shape[0]

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

             num_errors_skill = group['is_correct'].eq(False).sum()
             num_overtime_skill = group['overtime'].eq(True).sum()

             error_rate_skill = num_errors_skill / num_total_skill
             overtime_rate_skill = num_overtime_skill / num_total_skill

             triggered = False
             min_diff_skill = None
             y_agg = None
             z_agg = 2.5  # 文檔指定的固定值
             
             if error_rate_skill > 0.5 or overtime_rate_skill > 0.5:
                 triggered = True
                 # 找出該技能中錯誤或超時題目的最低難度
                 problem_items = group[(group['is_correct'] == False) | (group['overtime'] == True)]
                 if not problem_items.empty and 'question_difficulty' in problem_items.columns:
                     difficulties = problem_items['question_difficulty'].dropna()
                     if not difficulties.empty:
                         min_diff_skill = difficulties.min()
                         y_agg = _map_difficulty_to_label(min_diff_skill)
                 
                 print(f"      Skill Override Triggered: Skill='{skill}', ErrRate={error_rate_skill:.1%}, OTRate={overtime_rate_skill:.1%}, Y_agg={y_agg}")

             skill_override_flags[skill] = {
                 'triggered': triggered,
                 'error_rate': error_rate_skill,
                 'overtime_rate': overtime_rate_skill,
                 'total_questions': num_total_skill,
                 'min_diff_skill': min_diff_skill,  # 新增儲存最低難度
                 'y_agg': y_agg,  # 新增儲存映射難度標籤
                 'z_agg': z_agg if triggered else None  # 新增儲存限時
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

def _generate_q_recommendations(q_diagnosis_results):
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
                 'q_position': error.get('question_position'),
                 'q_type': error.get('Type'),
                 'trigger_type': 'error'
             })
             all_skills_found.add(skill)
        else:
            print(f"      Skipping trigger for error Position {error.get('question_position')}: Unknown Skill")

    for slow in ch4_correct_slow:
        skill = slow.get('Skill', 'Unknown Skill')
        if skill != 'Unknown Skill':
             triggers.append({
                 'skill': skill,
                 'difficulty': None, # Difficulty might not be directly relevant for correct-slow recs
                 'time': slow.get('Time'),
                 'is_overtime': True, # By definition of Ch4
                 'is_sfe': False,
                 'q_position': slow.get('question_position'),
                 'q_type': slow.get('Type'),
                 'trigger_type': 'correct_slow'
             })
             all_skills_found.add(skill)
        else:
            print(f"      Skipping trigger for correct-slow Position {slow.get('question_position')}: Unknown Skill")

    # --- Generate Recommendations per Skill ---
    for skill in all_skills_found:
        # if skill == 'Unknown Skill': continue # Already filtered out when creating triggers

        skill_recs_list = []
        is_overridden = ch6_override.get(skill, {}).get('triggered', False)
        print(f"      Processing Skill: {skill}, Overridden: {is_overridden}")

        if is_overridden and skill not in processed_override_skills:
            # Generate Macro Recommendation
            # 從第六章的結果取得y_agg和z_agg，而不是重新計算
            override_info = ch6_override.get(skill, {})
            y_agg = override_info.get('y_agg')
            z_agg = override_info.get('z_agg', 2.5)  # 如果沒有存儲，使用文檔默認值
            
            # 如果第六章沒有計算出y_agg（可能因為難度數據缺失），則使用觸發點難度
            if y_agg is None:
                trigger_difficulties = [t['difficulty'] for t in triggers if t['skill'] == skill and t['difficulty'] is not None and not pd.isna(t['difficulty'])]
                min_diff_skill = min(trigger_difficulties) if trigger_difficulties else 0 # Default Y_agg if no difficulty data
                y_agg = _map_difficulty_to_label(min_diff_skill)
            
            # Updated Macro Recommendation Text
            macro_rec_text = f"**優先全面鞏固基礎** (整體錯誤率或超時率 > 50%): 從 {y_agg} 難度開始, 建議限時 {z_agg} 分鐘。"
            skill_recs_list.append({'type': 'macro', 'text': macro_rec_text, 'priority': 0}) # High priority
            processed_override_skills.add(skill)
            print(f"      Generated MACRO recommendation for Skill: {skill}")

        elif not is_overridden:
             # Generate Case Recommendations
             skill_triggers = [t for t in triggers if t['skill'] == skill]
             has_real_trigger = any(t.get('q_type') == 'Real' for t in skill_triggers)
             has_pure_trigger = any(t.get('q_type') == 'Pure' for t in skill_triggers)

             adjustment_text = "" # Initialize adjustment text for this skill

             for trigger in skill_triggers:
                 y = "未知難度" # Default
                 difficulty = trigger.get('difficulty')
                 time = trigger.get('time')
                 is_overtime_trigger = trigger.get('is_overtime', False)
                 q_position_trigger = trigger.get('q_position', 'N/A')
                 trigger_type = trigger.get('trigger_type')
                 is_sfe_trigger = trigger.get('is_sfe', False)

                 if difficulty is not None and not pd.isna(difficulty):
                     y = _map_difficulty_to_label(difficulty)
                     z = _calculate_practice_time_limit(time, is_overtime_trigger)
                     priority = 1 if is_sfe_trigger else 2 # Prioritize SFE related recs

                     # Revised case_rec construction:
                     trigger_context = f"第 {q_position_trigger} 題相關"
                     practice_details = f"練習 {y}, 限時 {z} 分鐘。"
                     case_rec_text = f"{trigger_context}: {practice_details}"
                     if is_sfe_trigger:
                         case_rec_text = f"*基礎掌握不穩* {case_rec_text}"
                     skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})

                 elif trigger_type == 'correct_slow':
                     y = "中難度 (Mid) / 605+"
                     q_position_trigger = trigger.get('q_position', 'N/A')
                     time = trigger.get('time')
                     is_overtime_trigger = trigger.get('is_overtime', True)
                     z = _calculate_practice_time_limit(time, is_overtime_trigger)
                     priority = 3

                     # Revised case_rec construction:
                     trigger_context = f"第 {q_position_trigger} 題相關 (正確但慢)"
                     practice_details = f"練習 {y}, 限時 {z} 分鐘 (提升速度)。"
                     case_rec_text = f"{trigger_context}: {practice_details}"
                     skill_recs_list.append({'type': 'case', 'text': case_rec_text, 'priority': priority})
                 else:
                      print(f"      Skipping case recommendation for Position {q_position_trigger}: Missing difficulty for error trigger.")


             # Apply Chapter 2 Adjustments (after processing all triggers for the skill)
             if poor_real and has_real_trigger:
                  adjustment_text += " **Real題比例建議佔總練習題量2/3。**"
             if slow_pure and has_pure_trigger:
                  adjustment_text += " **建議此考點練習題量增加。**"

             # Update adjustment text format and add to list if needed
             if adjustment_text:
                 adj_text = f"整體練習註記: {adjustment_text.strip()}"
                 skill_recs_list.append({'type': 'adjustment', 'text': adj_text, 'priority': 4})
             print(f"      Generated {len([r for r in skill_recs_list if r['type'] == 'case'])} CASE recommendations and {len([r for r in skill_recs_list if r['type'] == 'adjustment'])} adjustments for Skill: {skill}")

        if skill_recs_list:
             # Sort recommendations within the skill: Macro (0), SFE Case (1), Other Case (2), Slow-Correct Case (3), Adjustment (4)
             recommendations_by_skill[skill] = sorted(skill_recs_list, key=lambda x: x['priority'])

    # Flatten and format the final list using concise list format
    final_recommendations = []
    sorted_skills = sorted(recommendations_by_skill.keys(), key=lambda s: (0 if s in processed_override_skills else 1, s))

    for skill in sorted_skills:
         recs = recommendations_by_skill[skill]
         final_recommendations.append(f"--- 技能: {skill} ---")
         for rec in recs:
             # Apply '* ' prefix to all lines under the skill
             final_recommendations.append(f"* {rec['text']}")
         final_recommendations.append("") # Add blank line

    if not final_recommendations:
        final_recommendations.append("根據本次分析，未產生具體的量化練習建議。請參考整體診斷總結。")

    print(f"    Finished generating Q recommendations. Total lines: {len(final_recommendations)}")
    return final_recommendations # Return list of recommendation strings


# --- Q-Specific Summary Report Generation (Chapter 8) ---

def _generate_q_summary_report(q_diagnosis_results, q_recommendations, subject_time_pressure_status_q, num_invalid_questions, df_diagnosed=None):
    """Generates the final summary report string based on Q diagnosis and recommendations.
       Aligns with Chapter 8 of gmat-q-score-logic-dustin-v1.2.md.
       
    Args:
        q_diagnosis_results (dict): Dictionary containing Q diagnosis results by chapter.
        q_recommendations (list): List of recommendation strings.
        subject_time_pressure_status_q (bool): Whether time pressure was detected for Q.
        num_invalid_questions (int): Number of invalid Q questions already identified.
        df_diagnosed (pd.DataFrame, optional): The processed Q DataFrame with diagnostic columns.
                                               Used for time_performance_category grouping.
    
    Returns:
        str: A formatted summary report string.
    """
    print("    Generating Q - Chapter 8: Summary Report...")
    report_lines = []

    # Check if diagnosis results exist at all
    # Use chapter1_results key which is added in run_q_diagnosis
    if not q_diagnosis_results or 'chapter1_results' not in q_diagnosis_results:
         print("      Core diagnosis results or Chapter 1 results missing. Generating minimal report.")
         ch1_res = q_diagnosis_results.get('chapter1_results', {})
         time_pressure_q = ch1_res.get('time_pressure_status', False)
         num_invalid_q = ch1_res.get('invalid_questions_excluded', 0)
         # Generate minimal report structure matching MD sections
         report_lines.append("## GMAT 量化 (Quantitative) 診斷報告")
         report_lines.append("--- (基於用戶數據與模擬難度分析) ---")
         report_lines.append("\n**1. 開篇總結**") # MD Ch8.1 Title
         if time_pressure_q: report_lines.append("- 根據分析，您在本輪測驗中可能感受到明顯的**時間壓力**。")
         else: report_lines.append("- 根據分析，您在本輪測驗中未處於明顯的時間壓力下。")
         if num_invalid_q > 0: report_lines.append(f"- 測驗末尾存在 {num_invalid_q} 道因時間壓力導致作答過快、可能影響數據有效性的跡象，已從後續詳細分析中排除。")
         else: report_lines.append("- 未發現因時間壓力導致數據無效的跡象，所有題目均納入分析。")
         report_lines.append("\n**2. 表現概覽**") # MD Ch8.2 Title
         report_lines.append("- 無充足的有效數據進行表現概覽分析。")
         report_lines.append("\n**3. 核心問題診斷**") # MD Ch8.3 Title
         report_lines.append("- 無充足的有效數據進行核心問題診斷。")
         report_lines.append("\n**4. 模式觀察**") # MD Ch8.4 Title
         report_lines.append("- 無充足的有效數據進行模式觀察。")
         report_lines.append("\n**5. 基礎鞏固提示**") # MD Ch8.5 Title
         report_lines.append("- 無充足的有效數據進行基礎鞏固分析。")
         report_lines.append("\n**6. 練習計劃呈現**") # MD Ch8.6 Title
         report_lines.append("- 無法生成練習建議。")
         report_lines.append("\n**7. 後續行動指引**") # MD Ch8.7 Title
         report_lines.append("- 無法提供後續行動指引。")
         report_lines.append("\n--- 報告結束 ---")
         return "\n\n".join(report_lines)

    # Extract data safely using .get()
    ch1_results = q_diagnosis_results.get('chapter1_results', {})
    ch2_summary = q_diagnosis_results.get('chapter2_summary', [])
    ch3_errors = q_diagnosis_results.get('chapter3_error_details', [])
    ch4_correct_slow = q_diagnosis_results.get('chapter4_correct_slow_details', [])
    ch5_patterns = q_diagnosis_results.get('chapter5_patterns', {})
    ch6_override = q_diagnosis_results.get('chapter6_skill_override', {})

    # Extract triggered params for logic checks
    triggered_params = set()
    for err in ch3_errors: triggered_params.update(err.get('Possible_Params', []))
    for cs in ch4_correct_slow: triggered_params.update(cs.get('Possible_Params', []))
    if ch5_patterns.get('early_rushing_flag', False): triggered_params.add('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    if ch5_patterns.get('carelessness_issue_flag', False): triggered_params.add('Q_BEHAVIOR_CARELESSNESS_ISSUE')
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
                        except ValueError: pass
    triggered_params.update({flag for flag, status in ch2_flags.items() if status})

    report_lines.append("## GMAT 量化 (Quantitative) 診斷報告")
    report_lines.append("--- (基於用戶數據與模擬難度分析) ---")
    report_lines.append("")

    # 1. 開篇總結 (From Ch1 Results - Aligned with MD Ch8.1)
    report_lines.append("**1. 開篇總結**")
    time_pressure_q = ch1_results.get('time_pressure_status', False)
    num_invalid_q = ch1_results.get('invalid_questions_excluded', 0)
    # Use exact phrasing from MD Ch8.1
    if time_pressure_q:
        report_lines.append("- 根據分析，您在本輪測驗中可能感受到明顯的時間壓力。")
    else:
        report_lines.append("- 根據分析，您在本輪測驗中未處於明顯的時間壓力下。")
    if num_invalid_q > 0:
        report_lines.append(f"- 測驗末尾存在因時間壓力導致作答過快、可能影響數據有效性的跡象 ({num_invalid_q} 題被排除)。")
    else:
        report_lines.append("- 未發現因時間壓力導致數據無效的跡象。")
    report_lines.append("")

    # 2. 表現概覽 (Aligned with MD Ch8.2)
    report_lines.append("**2. 表現概覽**")
    real_stats_error = next((item for item in ch2_summary if item.get('Metric') == 'Error Rate'), None)
    real_stats_ot = next((item for item in ch2_summary if item.get('Metric') == 'Overtime Rate'), None)
    if real_stats_error and real_stats_ot:
        real_err_rate_str = _format_rate(real_stats_error.get('Real_Value', 'N/A'))
        real_ot_rate_str = _format_rate(real_stats_ot.get('Real_Value', 'N/A'))
        pure_err_rate_str = _format_rate(real_stats_error.get('Pure_Value', 'N/A'))
        pure_ot_rate_str = _format_rate(real_stats_ot.get('Pure_Value', 'N/A'))
        report_lines.append(f"- Real 題表現: 錯誤率 {real_err_rate_str}, 超時率 {real_ot_rate_str}")
        report_lines.append(f"- Pure 題表現: 錯誤率 {pure_err_rate_str}, 超時率 {pure_ot_rate_str}")

        triggered_ch2_flags_desc = []
        # Correctly reference the flags dictionary derived earlier
        if ch2_flags.get('poor_real', False): triggered_ch2_flags_desc.append(_get_translation('poor_real'))
        if ch2_flags.get('poor_pure', False): triggered_ch2_flags_desc.append(_get_translation('poor_pure'))
        if ch2_flags.get('slow_real', False): triggered_ch2_flags_desc.append(_get_translation('slow_real'))
        if ch2_flags.get('slow_pure', False): triggered_ch2_flags_desc.append(_get_translation('slow_pure'))
        if triggered_ch2_flags_desc:
             report_lines.append(f"- 比較提示: {'; '.join(triggered_ch2_flags_desc)}")
    else:
        report_lines.append("- 未能進行 Real vs. Pure 題的詳細比較。")

    # Error Difficulty Distribution (Aligned with MD Ch8.2)
    if ch3_errors:
        error_difficulties = [err.get('Difficulty') for err in ch3_errors if err.get('Difficulty') is not None and not pd.isna(err.get('Difficulty'))]
        if error_difficulties:
            difficulty_labels = [_map_difficulty_to_label(d) for d in error_difficulties]
            label_counts = pd.Series(difficulty_labels).value_counts().sort_index()
            if not label_counts.empty:
                distribution_str = ", ".join([f"{label} ({count}題)" for label, count in label_counts.items()])
                report_lines.append(f"- **錯誤難度分佈:** {distribution_str}")
            # No 'else' needed per MD structure
        # No 'else' needed per MD structure
    # No 'else' needed per MD structure
    report_lines.append("")

    # 3. 核心問題診斷 (Aligned with MD Ch8.3)
    report_lines.append("**3. 核心問題診斷**")
    sfe_triggered = False
    sfe_skills_involved = set()
    for err in ch3_errors:
        if err.get('Is_SFE', False):
             sfe_triggered = True
             skill = err.get('Skill', 'Unknown Skill')
             if skill != 'Unknown Skill': sfe_skills_involved.add(skill)

    # Report SFE Summary first if triggered (as per MD phrasing)
    if sfe_triggered:
        sfe_label = _get_translation('Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
        sfe_note = f"尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤 ({sfe_label})"
        if sfe_skills_involved:
             sfe_note += f"，涉及技能: {', '.join(sorted(list(sfe_skills_involved)))})"
        else:
            sfe_note += ")"
        report_lines.append(f"- {sfe_note}，這表明在這些知識點的應用上可能存在穩定性問題。")

    # Summarize other core issues using natural language based on triggered params
    core_issue_summary = []
    # Logic based on MD Ch8.3 examples
    if 'Q_CARELESSNESS_DETAIL_OMISSION' in triggered_params:
        core_issue_summary.append("傾向於快速作答但出錯，可能涉及{}。".format(_get_translation('Q_CARELESSNESS_DETAIL_OMISSION')))
    if 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params and not sfe_triggered: # Avoid repeating if SFE mentioned it
        core_issue_summary.append("花費了較長時間但仍無法解決部分問題，可能涉及{}。".format(_get_translation('Q_CONCEPT_APPLICATION_ERROR')))
    if 'Q_CALCULATION_ERROR' in triggered_params:
        core_issue_summary.append("計算錯誤也是失分原因 ({})。".format(_get_translation('Q_CALCULATION_ERROR')))
    if 'Q_PROBLEM_UNDERSTANDING_ERROR' in triggered_params:
         core_issue_summary.append("對數學問題本身的理解可能存在偏差 ({})。".format(_get_translation('Q_PROBLEM_UNDERSTANDING_ERROR')))
    if 'Q_READING_COMPREHENSION_ERROR' in triggered_params:
        core_issue_summary.append("Real題的文字信息理解可能存在障礙 ({})。".format(_get_translation('Q_READING_COMPREHENSION_ERROR')))

    correct_slow_params = set()
    for cs in ch4_correct_slow: correct_slow_params.update(cs.get('Possible_Params', []))
    efficiency_issues = []
    if 'Q_EFFICIENCY_BOTTLENECK_READING' in correct_slow_params: efficiency_issues.append("Real題閱讀")
    if 'Q_EFFICIENCY_BOTTLENECK_CONCEPT' in correct_slow_params: efficiency_issues.append("概念思考")
    if 'Q_EFFICIENCY_BOTTLENECK_CALCULATION' in correct_slow_params: efficiency_issues.append("計算過程")
    if efficiency_issues:
         core_issue_summary.append("部分題目雖然做對，但在{}等環節耗時過長 ({})，反映了應用效率有待提升。".format(
             "、".join(efficiency_issues),
             ", ".join([_get_translation(p) for p in correct_slow_params if p.startswith('Q_EFFICIENCY')]) # Translate related params
             ))

    if core_issue_summary:
        for summary_line in core_issue_summary:
             report_lines.append(f"- {summary_line}")
    elif not sfe_triggered:
         report_lines.append("- 未識別出主要的核心問題模式。") # Show only if NO SFE and NO other issues

    # Remove detailed list per position as MD uses summary
    report_lines.append("")

    # 4. 模式觀察 (Aligned with MD Ch8.4)
    report_lines.append("**4. 模式觀察**")
    pattern_found = False
    if ch5_patterns.get('early_rushing_flag', False):
        # Use exact phrasing from MD Ch8.4
        report_lines.append(f"- 測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。 ({_get_translation('Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')})")
        pattern_found = True
    if ch5_patterns.get('carelessness_issue_flag', False):
        # Use exact phrasing from MD Ch8.4
        report_lines.append(f"- 分析顯示，「快而錯」的情況佔比較高 ({ch5_patterns.get('fast_wrong_rate', 0):.1%})，提示可能需要關注答題的仔細程度，減少粗心錯誤。 ({_get_translation('Q_BEHAVIOR_CARELESSNESS_ISSUE')})")
        pattern_found = True
    if not pattern_found:
        report_lines.append("- 未發現明顯的特殊作答模式。")
    report_lines.append("")

    # 5. 基礎鞏固提示 (Aligned with MD Ch8.5)
    report_lines.append("**5. 基礎鞏固提示**")
    override_skills_list = [skill for skill, data in ch6_override.items() if data.get('triggered', False)]
    if override_skills_list:
        # Use exact phrasing from MD Ch8.5
        report_lines.append(f"- 對於 [{', '.join(sorted(override_skills_list))}] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。")
    else:
        # Use adjusted phrasing aligned with MD's intent
        report_lines.append("- 未觸發需要優先進行基礎鞏固的技能覆蓋規則。")
    report_lines.append("")

    # 6. 練習計劃呈現 (Aligned with MD Ch8.6)
    report_lines.append("**6. 練習計劃呈現**")
    if q_recommendations:
        # Mention SFE prioritization as per MD Ch3 note
        if sfe_triggered:
             report_lines.append("- (注意：涉及「基礎掌握不穩」的建議已優先列出)")
        report_lines.extend(q_recommendations)
    else:
        report_lines.append("- 無具體練習建議生成。")
    report_lines.append("")

    # 7. 後續行動指引 (Aligned with MD Ch8.7)
    report_lines.append("**7. 後續行動指引**")
    # Core Constraint Reminder (Implicitly followed by using translations)

    # Prepare mappings again for accurate context
    param_to_positions = {}
    skill_to_positions = {}
    for err in ch3_errors:
        pos = err.get('question_position'); skill = err.get('Skill', 'UK'); params = err.get('Possible_Params', [])
        if skill != 'UK' and pos is not None: skill_to_positions.setdefault(skill, set()).add(pos)
        for p in params: param_to_positions.setdefault(p, set()).add(pos)
    for cs in ch4_correct_slow:
        pos = cs.get('question_position'); skill = cs.get('Skill', 'UK'); params = cs.get('Possible_Params', [])
        if skill != 'UK' and pos is not None: skill_to_positions.setdefault(skill, set()).add(pos)
        for p in params: param_to_positions.setdefault(p, set()).add(pos)
    for param in param_to_positions: param_to_positions[param] = sorted(list(param_to_positions[param]))
    for skill in skill_to_positions: skill_to_positions[skill] = sorted(list(skill_to_positions[skill]))

    report_lines.append("- **引導反思:**")
    reflection_prompts = []
    def get_pos_context_str(param_keys): # Helper to get position context string
        positions = set().union(*(set(param_to_positions.get(key, [])) for key in param_keys))
        return f" (涉及題號: {sorted(list(positions))})" if positions else ""

    # Align reflection prompts EXACTLY with MD Ch8.7 prompts and triggers
    if 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params or 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params:
        prompt_skills = set()
        if 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params: prompt_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get('Q_CONCEPT_APPLICATION_ERROR',[]) for pos in poses))
        if 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in triggered_params: prompt_skills.update(sfe_skills_involved)
        skill_context = f" [`{', '.join(sorted(list(prompt_skills)))}`] " if prompt_skills else " "
        reflection_prompts.append(f"  - 回想一下，在做錯的{skill_context}題目時，具體是卡在哪個數學知識點或公式上？是完全沒思路，還是知道方法但用錯了？" + get_pos_context_str(['Q_CONCEPT_APPLICATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE']))

    if 'Q_CALCULATION_ERROR' in triggered_params or 'Q_EFFICIENCY_BOTTLENECK_CALCULATION' in triggered_params:
        reflection_prompts.append("  - 是計算過程中容易出錯，還是計算速度偏慢？" + get_pos_context_str(['Q_CALCULATION_ERROR', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION']))

    if 'Q_READING_COMPREHENSION_ERROR' in triggered_params or ch2_flags.get('poor_real', False):
        reflection_prompts.append("  - 對於做錯的文字題，是題目本身的陳述讀不懂，還是能讀懂但無法轉化成數學問題？是否存在特定主題或長句子的閱讀困難？" + get_pos_context_str(['Q_READING_COMPREHENSION_ERROR']))

    if 'Q_CARELESSNESS_DETAIL_OMISSION' in triggered_params or ch5_patterns.get('carelessness_issue_flag', False):
        reflection_prompts.append("  - 回想一下，是否經常因為看錯數字、漏掉條件或誤解題意而失分？" + get_pos_context_str(['Q_CARELESSNESS_DETAIL_OMISSION']))

    if not reflection_prompts: reflection_prompts.append("  - (本次分析未觸發典型的反思問題，建議結合練習計劃進行)")
    report_lines.extend(reflection_prompts)

    report_lines.append("- **二級證據參考建議:**")
    # Check if we have diagnosed dataframe with time_performance_category
    if df_diagnosed is not None and not df_diagnosed.empty and 'time_performance_category' in df_diagnosed.columns:
        # Filter for problems (incorrect or overtime)
        df_problem = df_diagnosed[(df_diagnosed['is_correct'] == False) | (df_diagnosed.get('overtime', False) == True)].copy()
        
        if not df_problem.empty:
            report_lines.append("  - 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時，建議您查看近期的練習記錄，整理相關錯題或超時題目。")
            
            # --- START NEW LOGIC: Group by time_performance_category ---
            details_added_2nd_ev = False
            
            # Define the desired order for performance categories
            performance_order_en = [
                'Fast & Wrong', 'Slow & Wrong', 'Normal Time & Wrong', 
                'Slow & Correct', 'Fast & Correct', 'Normal Time & Correct',
                'Unknown' # Include Unknown as a fallback
            ]
            
            grouped_by_performance = df_problem.groupby('time_performance_category')
            
            # Iterate in the desired order
            for perf_en in performance_order_en:
                if perf_en in grouped_by_performance.groups: # Check if this group exists
                    # --- ADD SKIP LOGIC for 'Fast & Correct' ---
                    if perf_en == 'Fast & Correct':
                        print(f"DEBUG (q_report): Skipping category '{perf_en}' as requested.") # DEBUG
                        continue # Skip to the next category
                    # --- END SKIP LOGIC ---
                    
                    group_df = grouped_by_performance.get_group(perf_en)
                    if not group_df.empty:
                        perf_zh = perf_en  # Default if translation not available
                        # Translate performance category if needed
                        if perf_en == 'Fast & Wrong': perf_zh = "快錯"
                        elif perf_en == 'Slow & Wrong': perf_zh = "慢錯"
                        elif perf_en == 'Normal Time & Wrong': perf_zh = "正常時間錯"
                        elif perf_en == 'Slow & Correct': perf_zh = "慢對"
                        elif perf_en == 'Fast & Correct': perf_zh = "快對"
                        elif perf_en == 'Normal Time & Correct': perf_zh = "正常時間對"
                        
                        # Extract unique types and skills from this group
                        types_in_group = group_df['question_type'].dropna().unique()
                        skills_in_group = group_df['question_fundamental_skill'].dropna().unique()
                        
                        types_zh = sorted([t for t in types_in_group])  # Already in desired format
                        skills_zh = sorted([s for s in skills_in_group])  # Already in desired format

                        # --- Extract Unique Labels ---
                        all_labels_in_group = set()
                        target_label_col = None
                        
                        # Check if the diagnostic_params_list_chinese column exists (with translated labels)
                        if 'diagnostic_params_list_chinese' in group_df.columns:
                            target_label_col = 'diagnostic_params_list_chinese'
                            print(f"DEBUG (q_report): Using 'diagnostic_params_list_chinese' column.")
                        # If not, check if the original params column exists
                        elif 'diagnostic_params' in group_df.columns:
                            target_label_col = 'diagnostic_params'
                            print(f"DEBUG (q_report): Found 'diagnostic_params' column, will translate internally.")
                        else:
                            print(f"DEBUG (q_report): No diagnostic params column found for this group!")

                        if target_label_col:
                            print(f"DEBUG (q_report): Processing labels from column: {target_label_col}")
                            
                            for labels_list in group_df[target_label_col]:
                                if isinstance(labels_list, list): # Check if it's a list
                                    # If using original English codes, translate them now
                                    if target_label_col == 'diagnostic_params':
                                        translated_list = [_get_translation(p) for p in labels_list]
                                        all_labels_in_group.update(translated_list)
                                    else: # Already translated
                                        all_labels_in_group.update(labels_list)
                        
                        sorted_labels_zh = sorted(list(all_labels_in_group))
                        
                        # --- Modify Report Line ---
                        report_line = f"  - **{perf_zh}:** 需關注題型：【{', '.join(types_zh)}】；涉及技能：【{', '.join(skills_zh)}】。"
                        if sorted_labels_zh:
                            report_line += f" 注意相關問題點：【{', '.join(sorted_labels_zh)}】。"
                        report_lines.append(report_line)
                        # --- End Modify Report Line ---
                        
                        details_added_2nd_ev = True
                        
            if not details_added_2nd_ev:
                report_lines.append("  - (本次分析未聚焦到特定的問題類型或技能)")
                
            report_lines.append("  - 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。")
        else:
            report_lines.append("  - (本次分析未發現需要二級證據深入探究的問題點)")
    else:
        # Fallback to old recommendations if no diagnosed dataframe or missing column
        report_lines.append("  - *觸發時機：* 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。")
        secondary_evidence_skills = set().union(*performance_to_skills.values()) if 'performance_to_skills' in locals() else set()
        skill_context_for_secondary = f"在 [`{', '.join(sorted(list(secondary_evidence_skills)))}`/相關題型] " if secondary_evidence_skills else ""
        report_lines.append(f"  - *建議行動：* 為了更精確地定位您{skill_context_for_secondary}上的具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些知識點或題型（參考**附錄 A** 中的描述）反覆出現問題。如果樣本不足，請在接下來的做題中注意收集，累積到足夠樣本後再進行分析。")

    report_lines.append("- **質化分析建議:**")
    # Align Qualitative Analysis text and trigger EXACTLY with MD Ch8.7
    # Trigger: Confusion (implicit) or inability to clarify via other means
    report_lines.append("  - *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時。")
    # Determine focus area based on Concept/Problem Understanding errors
    qualitative_focus_skills = set()
    if 'Q_CONCEPT_APPLICATION_ERROR' in triggered_params: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get('Q_CONCEPT_APPLICATION_ERROR',[]) for pos in poses))
    if 'Q_PROBLEM_UNDERSTANDING_ERROR' in triggered_params: qualitative_focus_skills.update(skill for skill, poses in skill_to_positions.items() if any(pos in param_to_positions.get('Q_PROBLEM_UNDERSTANDING_ERROR',[]) for pos in poses))
    qualitative_focus_area = f" [`某類問題`，例如涉及{_get_translation('Q_CONCEPT_APPLICATION_ERROR')}的題目]" if qualitative_focus_skills else " [`某類問題`]" # Default if no specific focus
    report_lines.append(f"  - *建議行動：* 如果您對{qualitative_focus_area} 的錯誤原因仍感困惑，可以嘗試**提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。")


    report_lines.append("- **輔助工具推薦建議:**") # Changed title to match MD more closely
    # Align Tool/Prompt Recommendations EXACTLY with MD Ch8.7 list and triggers
    recommended_tools_list = []
    recommended_prompts_map = {} # Use map to store prompts and their triggers

    # Tool: Classifier (Trigger: errors, slow-correct, or override)
    if ch3_errors or ch4_correct_slow or override_skills_list:
         recommended_tools_list.append("`Dustin's GMAT Q: Question Classifier`")

    # Tool: Real-Context Converter (Trigger: poor_real or slow_real)
    if ch2_flags.get('poor_real', False) or ch2_flags.get('slow_real', False):
         recommended_tools_list.append("`Dustin_GMAT_Q_Real-Context_Converter`")

    # AI Prompts - Check each trigger parameter set from MD
    def add_prompt_recommendation(prompt_name, triggering_params):
         # Check if ANY of the triggering params were found in this run
         if any(p in triggered_params for p in triggering_params):
             # Store the prompt and the specific params that triggered it for potential context (though MD doesn't require showing context)
             recommended_prompts_map[prompt_name] = recommended_prompts_map.get(prompt_name, set()).union(p for p in triggering_params if p in triggered_params)

    # MD Prompt Triggers:
    add_prompt_recommendation('Quant-related/01_basic_explanation.md', ['Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 'Q_CONCEPT_APPLICATION_ERROR', 'skill_override_triggered']) # Note: skill_override is not in triggered_params directly, check override_skills_list
    if override_skills_list: recommended_prompts_map.setdefault('Quant-related/01_basic_explanation.md', set()).add('skill_override_triggered') # Manually add trigger if list is not empty
    add_prompt_recommendation('Quant-related/03_test_math_concepts.md', ['Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 'Q_CONCEPT_APPLICATION_ERROR', 'skill_override_triggered'])
    if override_skills_list: recommended_prompts_map.setdefault('Quant-related/03_test_math_concepts.md', set()).add('skill_override_triggered')
    add_prompt_recommendation('Quant-related/02_quick_math_tricks.md', ['Q_EFFICIENCY_BOTTLENECK_READING', 'Q_EFFICIENCY_BOTTLENECK_CONCEPT', 'Q_EFFICIENCY_BOTTLENECK_CALCULATION', 'slow_real', 'slow_pure'])
    add_prompt_recommendation('Quant-related/03_test_math_concepts.md', ['Q_PROBLEM_UNDERSTANDING_ERROR', 'Q_READING_COMPREHENSION_ERROR']) # Already potentially added, set handles duplicates
    add_prompt_recommendation('Quant-related/01_basic_explanation.md', ['Q_CARELESSNESS_DETAIL_OMISSION', 'Q_BEHAVIOR_CARELESSNESS_ISSUE']) # Already potentially added

    # Always recommend variant and similar questions prompts? MD lists them under "通用練習與鞏固"
    recommended_prompts_map['Quant-related/05_variant_questions.md'] = recommended_prompts_map.get('Quant-related/05_variant_questions.md', set()).union({'通用練習'})
    recommended_prompts_map['Quant-related/06_similar_questions.md'] = recommended_prompts_map.get('Quant-related/06_similar_questions.md', set()).union({'通用練習'})

    # Format Tool/Prompt output
    if recommended_tools_list:
         report_lines.append("  - *工具推薦:*")
         for tool in sorted(list(set(recommended_tools_list))): # Ensure uniqueness
             report_lines.append(f"    - {tool}")
    if recommended_prompts_map:
         report_lines.append("  - *AI 提示推薦:*")
         for prompt in sorted(recommended_prompts_map.keys()):
             # MD doesn't show trigger context, just lists prompts
             report_lines.append(f"    - `{prompt}`")

    if not recommended_tools_list and not recommended_prompts_map:
         report_lines.append("  - (本次分析未觸發特定的工具或 AI 提示建議)")


    report_lines.append("\n--- 報告結束 ---")
    return "\n\n".join(report_lines)

# --- Main Q Diagnosis Entry Point ---

def run_q_diagnosis(df_raw_q, q_time_pressure_status=False):
    """
    Runs the diagnostic analysis specifically for the Quantitative section.
    Applies Chapter 1 logic internally to determine invalid data.

    Args:
        df_raw_q (pd.DataFrame): Raw DataFrame with all Q responses.
                                 Requires columns: 'question_position', 'question_time', 
                                 'is_correct', 'question_type', 'question_difficulty', 
                                 'question_fundamental_skill'.
        q_time_pressure_status (bool): Whether time pressure was detected for Q by the main module.

    Returns:
        dict: Dictionary containing Q diagnosis results by chapter, including invalid_count.
        str: A string containing the summary report for the Q section.
        pd.DataFrame: The processed Q DataFrame with added diagnostic columns 
                      (diagnostic_params_list, is_sfe, time_performance_category, is_invalid).
    """
    print("  Running Quantitative Diagnosis...")
    q_diagnosis_results = {}

    if df_raw_q.empty:
        print("    No Q data provided. Skipping Q diagnosis.")
        return {}, "Quantitative (Q) 部分無數據可供診斷。", pd.DataFrame()

    # --- Apply Chapter 1 Rules --- 
    # This function now handles filtering and overtime marking
    # It calculates its own time pressure but we use the passed one
    # We need to call this to get the overtime threshold and mark invalid
    df_q_processed, calculated_time_pressure, num_invalid_q, overtime_threshold_q = _apply_ch1_rules_internal(df_raw_q, q_time_pressure_status)

    # Chapter 1 results for reporting
    chapter1_results = {
        'time_pressure_status': q_time_pressure_status, # Use the status passed from main module
        'invalid_questions_excluded': num_invalid_q,
        'overtime_threshold_used': overtime_threshold_q
    }

    # Store the invalid count in the main results dictionary
    q_diagnosis_results['invalid_count'] = num_invalid_q
    q_diagnosis_results['chapter1_results'] = chapter1_results # Also store detailed ch1 results

    # Exclude invalid data from further analysis (Ch2-6)?
    # Let's keep invalid data in the df, but internal functions should filter based on is_invalid
    df_q_for_analysis = df_q_processed.copy()

    if df_q_for_analysis.empty:
        print("    No Q data remaining (possibly all invalid). Skipping further Q diagnosis.")
        # Generate a minimal report indicating no valid data
        minimal_report = _generate_q_summary_report(
             q_diagnosis_results, # Pass results containing invalid count
             ["無有效題目可供分析。"],
             q_time_pressure_status,
             num_invalid_q,
             None
        )
        # Return the df *before* filtering for the frontend display
        return q_diagnosis_results, minimal_report, df_q_processed

    # --- Run Internal Diagnosis (Chapters 2-6) --- 
    # Calculate prerequisites needed for root cause analysis (use df_q_for_analysis which includes is_invalid)
    # Ensure filtering happens where needed, e.g., average time only on valid?
    df_valid_for_avg = df_q_for_analysis[df_q_for_analysis['is_invalid'] == False]
    avg_time_per_type_q = {}
    if not df_valid_for_avg.empty and pd.api.types.is_numeric_dtype(df_valid_for_avg['question_time']):
        avg_time_per_type_q = df_valid_for_avg.groupby('question_type')['question_time'].mean().to_dict()
    else:
        avg_time_per_type_q = {'REAL': 2.0, 'PURE': 2.0} # Default

    max_correct_difficulty_per_skill_q = {}
    # Calculate max difficulty based on correct AND valid questions
    df_correct_valid_q = df_q_for_analysis[(df_q_for_analysis['is_correct'] == True) & (df_q_for_analysis['is_invalid'] == False)]
    if not df_correct_valid_q.empty and 'question_fundamental_skill' in df_correct_valid_q.columns and 'question_difficulty' in df_correct_valid_q.columns:
        if pd.api.types.is_numeric_dtype(df_correct_valid_q['question_difficulty']):
            max_correct_difficulty_per_skill_q = df_correct_valid_q.groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # Apply root cause diagnosis (adds diagnostic_params_list, is_sfe, time_performance_category)
    # Pass the dataframe containing BOTH valid and invalid rows
    df_q_diagnosed = _diagnose_q_root_causes(df_q_for_analysis, avg_time_per_type_q, max_correct_difficulty_per_skill_q)

    # --- Execute Chapters 2-6 Logic --- 
    print("  Executing Internal Q Diagnosis (Chapters 2-6)...")
    # Internal logic needs to handle the is_invalid flag where appropriate
    # For example, Ch2 Real/Pure comparison might exclude invalid
    q_internal_results = _diagnose_q_internal(df_q_diagnosed) # Pass the full diagnosed df
    print("    Finished Internal Q Diagnosis.")

    # Combine Chapter 1 results with results from Chapters 2-6
    # q_diagnosis_results already contains chapter1_results and invalid_count
    q_diagnosis_results.update(q_internal_results) # Add results from Ch 2-6

    # --- Translate diagnostic codes --- 
    # Ensure the diagnosed dataframe is used for translation
    if 'diagnostic_params_list' in df_q_diagnosed.columns:
        print("DEBUG (q_diagnostic.py): Translating 'diagnostic_params' to Chinese...")
        def translate_q_list(params_list):
            return [_get_translation(p) for p in params_list] if isinstance(params_list, list) else []
        df_q_diagnosed['diagnostic_params_list_chinese'] = df_q_diagnosed['diagnostic_params'].apply(translate_q_list)
    else:
        print("WARNING (q_diagnostic.py): 'diagnostic_params' column not found for translation.")
        # Ensure column exists even if translation failed
        if 'diagnostic_params_list_chinese' not in df_q_diagnosed.columns:
             df_q_diagnosed['diagnostic_params_list_chinese'] = [[] for _ in range(len(df_q_diagnosed))]

    # --- Drop original English codes column --- 
    if 'diagnostic_params' in df_q_diagnosed.columns:
        df_q_diagnosed.drop(columns=['diagnostic_params'], inplace=True)
        print("DEBUG (q_diagnostic.py): Dropped 'diagnostic_params' column.")

    # --- Rename translated column --- 
    if 'diagnostic_params_list_chinese' in df_q_diagnosed.columns:
        df_q_diagnosed.rename(columns={'diagnostic_params_list_chinese': 'diagnostic_params_list'}, inplace=True)
        print("DEBUG (q_diagnostic.py): Renamed 'diagnostic_params_list_chinese' to 'diagnostic_params_list'")
    else:
        print("DEBUG (q_diagnostic.py): Target list column not found or renamed. Initializing 'diagnostic_params_list'.")
        # Ensure column exists even if rename failed
        if 'diagnostic_params_list' not in df_q_diagnosed.columns:
            df_q_diagnosed['diagnostic_params_list'] = [[] for _ in range(len(df_q_diagnosed))]

    # --- Generate Recommendations & Summary Report --- 
    # Step 4: Generate Recommendations (Chapter 7)
    print("  Generating Q Recommendations (Chapter 7)...")
    # Pass the combined diagnosis results (Ch1-6) to the recommendation generator
    q_recommendations = _generate_q_recommendations(q_diagnosis_results) # Returns a list of strings
    print(f"    Generated {len(q_recommendations)} recommendation lines.")

    # Step 5: Generate Summary Report (Chapter 8)
    print("  Generating Q Summary Report (Chapter 8)...")
    # Pass the combined diagnosis results (Ch1-6) and recommendations
    report_str = _generate_q_summary_report(
        q_diagnosis_results, 
        q_recommendations, 
        q_time_pressure_status, # Pass the status from Ch1 results
        num_invalid_q,          # Pass the count from Ch1 results
        df_q_diagnosed          # Pass the diagnosed DataFrame for time_performance_category grouping
    )
    print("    Finished generating Q summary report.")

    # --- Step 6: Final Return ---
    # (Remove redundant translation logic here as it's done above)

    # --- DEBUG PRINT --- 
    print("DEBUG (q_diagnostic.py): Columns before return:", df_q_diagnosed.columns.tolist())
    if 'diagnostic_params_list' in df_q_diagnosed.columns:
        print("DEBUG (q_diagnostic.py): 'diagnostic_params_list' head:")
        print(df_q_diagnosed['diagnostic_params_list'].head())
    else:
        print("DEBUG (q_diagnostic.py): 'diagnostic_params_list' column MISSING before return!")
    # --- END DEBUG PRINT ---

    # --- 確保 Subject 欄位存在 ---
    if 'Subject' not in df_q_diagnosed.columns:
        print("警告: 'Subject' 欄位在 Q 返回前缺失，正在重新添加...")
        df_q_diagnosed['Subject'] = 'Q'
    elif df_q_diagnosed['Subject'].isnull().any() or (df_q_diagnosed['Subject'] != 'Q').any():
        print("警告: 'Subject' 欄位存在但包含空值或錯誤值，正在修正...")
        df_q_diagnosed['Subject'] = 'Q' # 強制修正

    print("  Quantitative Diagnosis Complete.")
    # Return combined results dict, report string, and the final diagnosed dataframe
    return q_diagnosis_results, report_str, df_q_diagnosed

# --- Chapter 1 Logic Implementation ---

def _apply_ch1_rules_internal(df_raw_q, time_pressure_from_main):
    """Applies Chapter 1 time validity rules internally for Q.
       Marks invalid rows and adds the tag.
       PRIORITIZES the 'is_manually_invalid' flag if present.

    Args:
        df_raw_q (pd.DataFrame): The raw Q DataFrame.
        time_pressure_from_main (bool): Whether time pressure was detected globally.

    Returns:
        pd.DataFrame: DataFrame with 'is_invalid' column updated and potentially 'diagnostic_params' added/updated.
    """
    df = df_raw_q.copy()

    # --- Ensure required columns exist and initialize ---
    if 'question_time' not in df.columns or 'question_position' not in df.columns:
        print("    Warning (Q Ch1 Internal): Missing time or position columns. Skipping invalid data check.")
        if 'is_invalid' not in df.columns: df['is_invalid'] = False # Ensure column exists
        if 'diagnostic_params' not in df.columns: df['diagnostic_params'] = [[] for _ in range(len(df))]
        return df

    # --- START: Prioritize Manual Invalid Flag ---
    if 'is_manually_invalid' in df.columns:
        # Initialize 'is_invalid' directly from the manual flag
        df['is_invalid'] = df['is_manually_invalid'].fillna(False).astype(bool)
        # Corrected f-string syntax
        print(f"    Initialized 'is_invalid' based on manual flags. Count: {df['is_invalid'].sum()}")
    else:
        # If manual flag column doesn't exist, initialize is_invalid to False
        print("    Warning (Q Ch1 Internal): 'is_manually_invalid' column not found. Initializing 'is_invalid' to False.")
        df['is_invalid'] = False
    # --- END: Prioritize Manual Invalid Flag ---

    # --- Initialize diagnostic_params if it doesn't exist ---
    if 'diagnostic_params' not in df.columns:
         # Initialize with empty lists
        df['diagnostic_params'] = [[] for _ in range(len(df))]
    else:
        # Ensure existing values are lists (handle potential issues)
        df['diagnostic_params'] = df['diagnostic_params'].apply(lambda x: x if isinstance(x, list) else [])

    # --- Apply Automatic Rules ONLY where not manually marked invalid ---
    # Define the mask for rows where automatic rules *can* be applied
    eligible_for_auto_rules_mask = ~df['is_invalid']

    # Calculate conditions for automatic invalidation
    # Ensure len(df) > 0 to avoid issues with empty dataframes in ceil
    if len(df) > 0:
        last_third_start_position = np.ceil(len(df) * 2 / 3)
    else:
        last_third_start_position = 0 # Or handle empty df case appropriately

    is_last_third = df['question_position'] >= last_third_start_position
    is_fast_end = df['question_time'] < FAST_END_THRESHOLD_MINUTES

    # Determine which rows meet the automatic invalid criteria
    # Apply only to rows eligible for auto rules
    auto_invalid_mask = (
        time_pressure_from_main &
        is_last_third &
        is_fast_end &
        eligible_for_auto_rules_mask # Apply only where not manually invalid
    )

    num_auto_invalid = auto_invalid_mask.sum()
    if num_auto_invalid > 0:
        print(f"    Marking {num_auto_invalid} additional Q questions as invalid based on automatic Chapter 1 rules.")
        # Update the 'is_invalid' column for these rows
        df.loc[auto_invalid_mask, 'is_invalid'] = True

    # --- Add tag to ALL rows finally marked as invalid (manual or auto) ---
    final_invalid_mask = df['is_invalid']
    if final_invalid_mask.any():
        print(f"    Adding/Ensuring '{INVALID_DATA_TAG_Q}' tag for {final_invalid_mask.sum()} invalid rows.")
        for idx in df[final_invalid_mask].index:
            # Ensure the cell contains a list before appending
            current_list = df.loc[idx, 'diagnostic_params']
            if not isinstance(current_list, list):
                current_list = [] # Initialize as list if not

            if INVALID_DATA_TAG_Q not in current_list:
                current_list.append(INVALID_DATA_TAG_Q)

            # Assign the potentially modified list back
            df.loc[idx, 'diagnostic_params'] = current_list

    print(f"    Finished Q Chapter 1 Internal Rules. Total invalid count: {df['is_invalid'].sum()}")
    return df