import pandas as pd
import math
import numpy as np # For handling potential NaN/division by zero
import argparse
import sys

# --- Configuration ---
# These constants are based on gmat-q-score-logic-dustin-v1.1.md
MAX_ALLOWED_TIME = 45.0
TIME_PRESSURE_DIFF_THRESHOLD = 3.0
TIME_PRESSURE_FAST_TIME_THRESHOLD = 1.0
FAST_END_FRACTION = 1/3
OVERTIME_THRESHOLD_PRESSURE = 2.5
OVERTIME_THRESHOLD_NO_PRESSURE = 3.0
RELATIVELY_FAST_FACTOR = 0.75
CARELESSNESS_RATE_THRESHOLD = 0.25
SKILL_OVERRIDE_RATE_THRESHOLD = 0.5
MACRO_REC_TIME_LIMIT = 2.5
TARGET_PRACTICE_TIME = 2.0
PRACTICE_TIME_SLOW_REDUCTION = 0.5
EXEMPTION_THRESHOLD = 2 # num_correct_not_overtime > EXEMPTION_THRESHOLD

# --- Helper Functions ---

def map_difficulty_to_label(d):
    # Replicates the 6-level difficulty mapping from Chapter 2 & 7
    # Maps question difficulty (Q_b) to a descriptive label.
    if d is None or pd.isna(d):
        return "未知難度"
    if d <= -1: return "低難度 (Low) / 505+"
    if -1 < d <= 0: return "中難度 (Mid) / 555+"
    if 0 < d <= 1: return "中難度 (Mid) / 605+"
    if 1 < d <= 1.5: return "中難度 (Mid) / 655+"
    if 1.5 < d <= 1.95: return "高難度 (High) / 705+"
    if 1.95 < d <= 2: return "高難度 (High) / 805+"
    # Handle cases slightly above 2, potentially typos or edge cases
    if d > 2: return "極高難度 (Very High) / 805+"
    return "未知難度" # Default fallback

def calculate_practice_time(question_time, is_overtime):
    # Replicates Chapter 7 logic for calculating recommended practice time limit (Z)
    # Based on actual time taken and whether it was considered overtime.
    target_time = TARGET_PRACTICE_TIME
    # Reduce base time slightly if the question was slow, otherwise use actual time
    base_time = question_time - PRACTICE_TIME_SLOW_REDUCTION if is_overtime else question_time
    # Round down to the nearest 0.5 minute
    z_raw = math.floor(base_time * 2) / 2
    # Ensure the recommended time is at least the target time
    z = max(z_raw, target_time)
    return z

def safe_divide(numerator, denominator):
    # Prevents division by zero errors when calculating rates.
    if denominator is None or denominator == 0:
        return 0.0 # Return 0 rate if denominator is zero
    if numerator is None:
        return 0.0
    try:
        # Ensure inputs are numeric before division
        num = pd.to_numeric(numerator, errors='coerce')
        den = pd.to_numeric(denominator, errors='coerce')
        if pd.isna(num) or pd.isna(den) or den == 0:
            return 0.0
        return num / den
    except (ZeroDivisionError, TypeError, ValueError):
        return 0.0

# --- NEW: Detailed Diagnosis Function for Quant (Based on Ch3 structure) ---
def get_detailed_diagnosis_q(q_type, skill, is_correct, is_slow, is_relatively_fast):
    """
    Generates detailed diagnosis text and suggested actions for Quant questions,
    following the implied logic structure of Chapter 3.
    Note: Specific causes might differ from DI/V and need refinement based on Q logic doc if available.
    """
    diagnosis = "N/A"
    action = "N/A"
    generic_recall_action = "請學生回憶卡關點/錯誤原因/效率瓶頸。"
    # Assuming Q also benefits from secondary evidence and qualitative analysis
    generic_qualitative_analysis = "若仍困惑，提供2-3個解題思路範例(文字/錄音)進行個案分析。"

    # --- Determine the specific time/correctness category description ---
    time_correctness_category_desc = ""
    if is_correct:
        if is_slow: time_correctness_category_desc = "正確但慢"
        elif is_relatively_fast: time_correctness_category_desc = "快且正確"
        else: time_correctness_category_desc = "正常時間正確"
    else: # Incorrect
        if is_slow: time_correctness_category_desc = "慢且錯"
        elif is_relatively_fast: time_correctness_category_desc = "快且錯"
        else: time_correctness_category_desc = "正常時間錯誤"

    # --- Specific Secondary Evidence Prompt ---
    # Assuming skill is the relevant grouping dimension like domain in DI
    specific_secondary_evidence = f"若無法回憶/確認，查看近期(2-4週) **{time_correctness_category_desc}** 的 **{skill} ({q_type})** 題目記錄(樣本>5-10題)。歸納模式/障礙/考點。"

    # --- General Diagnosis based on Time/Correctness ---
    if is_correct:
        if is_slow:
            diagnosis = "效率瓶頸可能點："
            action = generic_recall_action + " " + specific_secondary_evidence
            if q_type == 'REAL': diagnosis += " 問題理解與轉化 / 解題步驟規劃 / 計算執行。"
            else: diagnosis += " 概念提取 / 公式選擇 / 計算執行。"
        elif is_relatively_fast:
            diagnosis = "作答相對較快且正確。"
            action = "提醒：注意避免潛在粗心或跳步。若在測驗後段，確認是否倉促。"
        else: # Normal time and correct
            diagnosis = "正常時間完成且正確。"
            action = "無需特別行動。"
    else: # Incorrect
        if is_slow:
            diagnosis = "慢而錯可能原因："
            action = generic_recall_action + " " + specific_secondary_evidence
            if q_type == 'REAL': diagnosis += " 1. 問題理解/轉化障礙; 2. 核心概念/公式遺忘或混淆; 3. 計算障礙; 4. 解題步驟錯誤。"
            else: diagnosis += " 1. 核心數學概念/公式掌握不牢; 2. 計算錯誤; 3. 方法選擇錯誤。"
            action += " 請識別具體考點/概念盲區。"
        else: # Normal or Fast & Wrong
            prefix = "快而錯" if is_relatively_fast else "正常時間做錯"
            diagnosis = f"{prefix} 可能原因："
            action = generic_recall_action # Start with recall
            if q_type == 'REAL': diagnosis += " 1. 題目理解偏差/條件遺漏; 2. 概念應用錯誤; 3. 計算粗心。"
            else: diagnosis += " 1. 相關數學概念應用錯誤; 2. 計算粗心; 3. 方法選擇不當。"
            # Recommend secondary evidence + potentially qualitative for these errors
            action += " " + specific_secondary_evidence + " " + generic_qualitative_analysis + " 請識別具體考點/概念盲區。"

    return diagnosis.strip(), action.strip()

# --- Main Analysis Function ---

def analyze_gmat_data(input_csv_path, output_csv_path, user_override_time_pressure=None):
    """
    Analyzes GMAT performance data based on the logic defined in
    gmat-q-score-logic-dustin-v1.1.md.

    Reads data from input_csv_path, performs analysis, and writes results
    (original data + diagnostic columns + summary report) to output_csv_path.

    Args:
        input_csv_path (str): Path to the input CSV file (e.g., testset-q.csv).
        output_csv_path (str): Path to save the output CSV file.
        user_override_time_pressure (bool, optional): Manually override time
                                                   pressure detection.
                                                   Defaults to None (use detection).
    """
    try:
        # Read CSV, attempting different encodings if default fails
        try:
            df = pd.read_csv(input_csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_csv_path, encoding='gbk') # Try GBK for some Chinese files
            except UnicodeDecodeError:
                 df = pd.read_csv(input_csv_path, encoding='cp950') # Try Big5
        except FileNotFoundError:
            print(f"錯誤：找不到輸入文件 '{input_csv_path}'")
            sys.exit(1) # Exit if input file not found
        except Exception as e:
            print(f"讀取CSV時發生未預期的錯誤: {e}")
            sys.exit(1) # Exit on other read errors

        # Basic validation - check for essential columns
        required_cols = ['Question', 'Response Time (Minutes)', 'Performance',
                         'Question Type', 'Fundamental Skills', 'Q_b']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"錯誤：輸入 CSV 缺少必要的欄位: {', '.join(missing_cols)}")
            sys.exit(1)

    except Exception as e: # Catch potential errors during validation itself
        print(f"讀取或驗證 CSV 時發生錯誤: {e}")
        sys.exit(1)


    # --- 0. Prepare Initial Data ---
    # Rename columns for internal consistency
    df.rename(columns={
        'Question': 'question_id',
        'Response Time (Minutes)': 'question_time',
        'Performance': 'performance',
        'Question Type': 'question_type',
        'Fundamental Skills': 'question_fundamental_skill',
        'Q_b': 'question_difficulty'
    }, inplace=True)

    # Clean up potential whitespace and ensure consistent case
    df['performance'] = df['performance'].astype(str).str.strip().str.lower()
    df['question_type'] = df['question_type'].astype(str).str.strip().str.upper()
    df['question_fundamental_skill'] = df['question_fundamental_skill'].astype(str).str.strip()

    # Convert data types, handling potential errors robustly
    df['question_time'] = pd.to_numeric(df['question_time'], errors='coerce')
    df['question_difficulty'] = pd.to_numeric(df['question_difficulty'], errors='coerce')
    # Try converting question_id, coercing errors, then filling NaNs and converting to Int64
    df['question_id'] = pd.to_numeric(df['question_id'], errors='coerce')


    # Drop rows where essential numeric data couldn't be parsed or are missing
    essential_cols_numeric = ['question_time', 'question_difficulty', 'question_id']
    initial_rows = len(df)
    df.dropna(subset=essential_cols_numeric, inplace=True)
    df['question_id'] = df['question_id'].astype(int) # Convert to int after dropping NaNs

    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        print(f"警告：移除了 {rows_dropped} 行，因為 'question_time', 'question_difficulty', 或 'question_id' 包含無效或缺失值。")


    # Add derived columns
    df['is_correct'] = df['performance'] == 'correct'
    df['question_position'] = np.arange(1, len(df) + 1)

    total_test_time = df['question_time'].sum()
    total_number_of_questions = len(df)
    max_allowed_time = MAX_ALLOWED_TIME

    if total_number_of_questions == 0:
        print("錯誤：輸入檔案中沒有有效的題目數據可供分析。")
        sys.exit(1)

    # Initialize new diagnostic columns in the main DataFrame
    df['is_invalid'] = False
    df['overtime'] = False
    df['difficulty_label'] = df['question_difficulty'].apply(map_difficulty_to_label)
    df['error_classification'] = 'N/A' # N/A for correct or invalid questions initially
    df['special_focus_error'] = False # Will be updated for incorrect questions
    df['correct_but_slow'] = False # Will be updated for correct questions
    df['is_relatively_fast'] = False # Helper column for Chapters 3/5 analysis
    df['diagnosis_text'] = "N/A" # NEW Column for detailed diagnosis
    df['suggested_action'] = "N/A" # NEW Column for suggested action

    # --- 1. Time Strategy & Validity ---\
    time_diff = max_allowed_time - total_test_time

    # Identify questions in the last third of the test
    last_third_start_pos = math.ceil(total_number_of_questions * (1 - FAST_END_FRACTION))
    last_third_q_indices = df[df['question_position'] > last_third_start_pos].index

    # Find questions in the last third that were answered too quickly
    fast_end_questions_df = df.loc[last_third_q_indices][
        df.loc[last_third_q_indices, 'question_time'] < TIME_PRESSURE_FAST_TIME_THRESHOLD
    ]
    fast_end_question_ids = fast_end_questions_df['question_id'].tolist()

    # Determine time pressure based on time difference and fast end questions
    time_pressure_detected = (time_diff <= TIME_PRESSURE_DIFF_THRESHOLD) and (not fast_end_questions_df.empty)

    # Apply user override if provided, otherwise use detected value
    if user_override_time_pressure is not None:
        time_pressure = user_override_time_pressure
        print(f"用戶強制設定 time_pressure = {time_pressure}")
    else:
        time_pressure = time_pressure_detected

    # Set the overtime threshold based on time pressure status
    overtime_threshold = OVERTIME_THRESHOLD_PRESSURE if time_pressure else OVERTIME_THRESHOLD_NO_PRESSURE

    # Identify invalid questions (only if time pressure exists)
    invalid_question_ids = []
    if time_pressure:
        invalid_question_ids = fast_end_question_ids
        # Mark these questions as invalid in the main DataFrame
        df.loc[df['question_id'].isin(invalid_question_ids), 'is_invalid'] = True

    # Mark questions as 'overtime' if their time exceeds the threshold AND they are not invalid
    # This marking happens *before* filtering
    df['overtime'] = (df['question_time'] > overtime_threshold) & (~df['is_invalid'])

    # Create the filtered dataset for Chapters 2-7 analysis (excluding invalid questions)
    df_filtered = df[~df['is_invalid']].copy() # Use .copy() to avoid warnings

    if df_filtered.empty:
        print("警告：所有題目都被標記為無效，無法進行後續深入分析。將僅輸出包含標記的原始數據。")
        # Prepare a minimal summary indicating the issue
        summary_lines = ["========== GMAT 量化診斷報告 ==========",
                         "\\n**錯誤：** 所有題目均因時間壓力下的快速作答而被標記為無效數據，無法生成有效的診斷報告和練習建議。"]
        summary_df = pd.DataFrame({'診斷報告與建議': summary_lines})
        spacer_df = pd.DataFrame(np.nan, index=range(3), columns=df.columns) # More robust way
        summary_df_aligned = pd.DataFrame(columns=df.columns)
        summary_df_aligned[df.columns[0]] = summary_df['診斷報告與建議']
        final_df = pd.concat([df, spacer_df, summary_df_aligned], ignore_index=True)

        try:
            final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            print(f"已將包含無效標記的數據儲存至 {output_csv_path}")
        except Exception as e:
            print(f"儲存部分結果至CSV時發生錯誤: {e}")
        sys.exit(0) # Exit normally after saving partial results

    # --- 2. Multi-dimensional Analysis (on filtered data) ---
    real_q = df_filtered[df_filtered['question_type'] == 'REAL']
    pure_q = df_filtered[df_filtered['question_type'] == 'PURE']

    num_total_real = len(real_q)
    num_total_pure = len(pure_q)
    num_real_errors = len(real_q[~real_q['is_correct']])
    num_pure_errors = len(pure_q[~pure_q['is_correct']])
    # Count overtime using the flag already set in Chapter 1
    num_real_overtime = len(real_q[real_q['overtime']])
    num_pure_overtime = len(pure_q[pure_q['overtime']])

    # Calculate performance rates, using safe_divide for protection
    wrong_rate_real = safe_divide(num_real_errors, num_total_real)
    wrong_rate_pure = safe_divide(num_pure_errors, num_total_pure)
    over_time_rate_real = safe_divide(num_real_overtime, num_total_real)
    over_time_rate_pure = safe_divide(num_pure_overtime, num_total_pure)

    # Initialize diagnostic flags
    poor_real = False
    poor_pure = False
    slow_real = False
    slow_pure = False

    # Store lists of IDs for Chapter 3/7 report
    fast_wrong_ids_q = []
    slow_wrong_ids_q = []
    normal_wrong_ids_q = []
    correct_slow_ids_q = []
    sfe_ids_q = []
    problematic_question_details_q = [] # NEW list for detailed report info

    # Determine significant differences based on absolute counts and rates
    error_diff_significant = abs(num_real_errors - num_pure_errors) >= 2
    overtime_diff_significant = abs(num_real_overtime - num_pure_overtime) >= 2

    # Set flags based on significant differences, using rates to determine direction
    if error_diff_significant:
        if wrong_rate_real > wrong_rate_pure: poor_real = True
        elif wrong_rate_pure > wrong_rate_real: poor_pure = True
        # If counts differ but rates are equal, no flag is set based on rate comparison

    if overtime_diff_significant:
        if over_time_rate_real > over_time_rate_pure: slow_real = True
        elif over_time_rate_pure > over_time_rate_real: slow_pure = True
        # If counts differ but rates are equal, no flag is set based on rate comparison

    # --- 3. Root Cause Diagnosis (on filtered data) ---
    # Calculate average time per question type
    avg_time_real = safe_divide(real_q['question_time'].sum(), num_total_real)
    avg_time_pure = safe_divide(pure_q['question_time'].sum(), num_total_pure)
    average_time_per_type = {'REAL': avg_time_real, 'PURE': avg_time_pure}

    # Find the maximum difficulty achieved correctly for each skill
    max_correct_difficulty_per_skill = df_filtered[df_filtered['is_correct']].groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()

    # Get indices of incorrect questions in the filtered dataset
    incorrect_q_indices_filtered = df_filtered[~df_filtered['is_correct']].index

    # Iterate through filtered questions to classify errors, check SFE, and get detailed diagnosis
    # We iterate through all filtered questions now to also catch correct_but_slow
    for idx in df_filtered.index:
        question = df_filtered.loc[idx]
        skill = question['question_fundamental_skill']
        difficulty = question['question_difficulty']
        q_time = question['question_time']
        q_type = question['question_type']
        q_id = question['question_id']
        is_correct_flag = question['is_correct']
        is_overtime_flag = question['overtime'] # Use overtime flag calculated earlier

        # 1. Check for Special Focus Error (SFE) if incorrect
        is_sfe = False
        if not is_correct_flag:
            max_diff_for_skill = max_correct_difficulty_per_skill.get(skill, -np.inf)
            if pd.notna(difficulty) and pd.notna(max_diff_for_skill) and difficulty < max_diff_for_skill:
                is_sfe = True
            # Update SFE flag in the *original* DataFrame
            df.loc[df['question_id'] == q_id, 'special_focus_error'] = is_sfe
            if is_sfe:
                 sfe_ids_q.append(q_id)

        # 2. Classify Time Performance (Relative Fastness)
        avg_time = average_time_per_type.get(q_type, 0)
        is_relatively_fast_flag = (q_time < avg_time * RELATIVELY_FAST_FACTOR) if avg_time > 0 else False
        is_slow_flag = is_overtime_flag # For Q, slow is defined by overtime
        is_normal_time_flag = not is_relatively_fast_flag and not is_slow_flag

        # Update helper flag in *original* DataFrame
        df.loc[df['question_id'] == q_id, 'is_relatively_fast'] = is_relatively_fast_flag

        # 3. Assign error classification string and collect IDs
        classification = 'N/A'
        if not is_correct_flag:
            if is_relatively_fast_flag: classification = 'Fast & Wrong'; fast_wrong_ids_q.append(q_id)
            elif is_slow_flag: classification = 'Slow & Wrong'; slow_wrong_ids_q.append(q_id)
            else: classification = 'Normal Time & Wrong'; normal_wrong_ids_q.append(q_id)
            df.loc[df['question_id'] == q_id, 'error_classification'] = classification
        elif is_slow_flag: # Correct but slow
             classification = 'Correct but Slow'
             df.loc[df['question_id'] == q_id, 'correct_but_slow'] = True
             correct_slow_ids_q.append(q_id)
        else: # Correct and not slow
             classification = 'Correct'
             # We might still want diagnosis if relatively fast, handled by get_detailed_diagnosis

        # 4. Get Detailed Diagnosis & Action (only if problematic or relatively fast & correct)
        diag_text, action_text = "N/A", "N/A"
        is_problematic = not is_correct_flag or is_slow_flag
        is_fast_correct = is_correct_flag and is_relatively_fast_flag

        if is_problematic or is_fast_correct:
             diag_text, action_text = get_detailed_diagnosis_q(
                 q_type, skill, is_correct_flag, is_slow_flag, is_relatively_fast_flag
             )
             df.loc[df['question_id'] == q_id, 'diagnosis_text'] = diag_text
             df.loc[df['question_id'] == q_id, 'suggested_action'] = action_text

             # Store details only for problematic questions for the report's focus
             if is_problematic:
                  problematic_question_details_q.append({
                     'id': q_id,
                     'type': q_type,
                     'skill': skill,
                     'time': q_time,
                     'correct': is_correct_flag,
                     'slow': is_slow_flag,
                     'fast': is_relatively_fast_flag,
                     'sfe': is_sfe,
                     'diagnosis': diag_text,
                     'action': action_text,
                     'classification': classification,
                     'difficulty_label': question['difficulty_label'], # Get label from filtered df
                     'correct_but_slow': is_correct_flag and is_slow_flag
                  })

    # --- 4. Correct Question Time Analysis (on filtered data) ---\
    # This logic is now integrated into the loop in Chapter 3.
    # The flag 'correct_but_slow' is set there.
    # The list correct_slow_ids_q contains the relevant IDs.

    # --- 5. Pattern Observation & Carelessness ---\
    # Identify questions in the first third answered too quickly (absolute time)
    early_q_threshold_pos = total_number_of_questions / 3
    # Check in the *original* df for position, but filter out any that were marked invalid
    early_fast_questions_df = df[
        (df['question_position'] <= early_q_threshold_pos) &
        (df['question_time'] < TIME_PRESSURE_FAST_TIME_THRESHOLD) &
        (~df['is_invalid']) # Exclude invalid questions from this warning
    ]
    early_fast_q_ids = early_fast_questions_df['question_id'].tolist()
    # This list is used for a warning in the summary report

    # Calculate Carelessness Issue Rate
    # Uses 'is_relatively_fast' (calculated in Ch3 based on filtered data averages)
    # Access this flag from the *updated original* df, but only count rows present in df_filtered
    filtered_q_ids = df_filtered['question_id'].tolist() # IDs of questions used in main analysis

    # Count total relatively fast questions among the valid ones
    num_relatively_fast_total = df.loc[
        df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'],
        'is_relatively_fast'
    ].sum()
    # Count relatively fast AND incorrect questions among the valid ones
    num_relatively_fast_incorrect = df.loc[
        df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'] & ~df['is_correct'],
        'is_relatively_fast'
    ].sum()

    fast_wrong_rate = safe_divide(num_relatively_fast_incorrect, num_relatively_fast_total)
    # Determine if the carelessness issue flag should be set
    carelessness_issue = fast_wrong_rate > CARELESSNESS_RATE_THRESHOLD

    # --- 6. Foundational Skill Override (on filtered data) ---\
    # Aggregate performance stats per fundamental skill using the filtered data
    # Ensure groupby column exists and is not empty before proceeding
    if 'question_fundamental_skill' in df_filtered.columns and not df_filtered['question_fundamental_skill'].isnull().all():
        skill_stats = df_filtered.groupby('question_fundamental_skill').agg(
            num_total_skill=('question_id', 'count'),
            num_errors_skill=('is_correct', lambda x: (x == False).sum()),
            num_overtime_skill=('overtime', lambda x: (x == True).sum()),
            # Calculate count of correct & not overtime for the exemption rule (Chapter 7)
            num_correct_not_overtime=('question_id', lambda x: (
                (df_filtered.loc[x.index, 'is_correct'] == True) &
                (df_filtered.loc[x.index, 'overtime'] == False)
            ).sum()),
            # Find the minimum difficulty among error or overtime questions within the skill
            min_difficulty_error_or_overtime=('question_difficulty', lambda x:
                df_filtered.loc[x.index][
                    (~df_filtered.loc[x.index, 'is_correct']) | (df_filtered.loc[x.index, 'overtime'])
                ]['question_difficulty'].min(skipna=True) # Use skipna=True with min()
            )
        ).reset_index()

        # Calculate error and overtime rates per skill
        skill_stats['error_rate_skill'] = skill_stats.apply(lambda row: safe_divide(row['num_errors_skill'], row['num_total_skill']), axis=1)
        skill_stats['overtime_rate_skill'] = skill_stats.apply(lambda row: safe_divide(row['num_overtime_skill'], row['num_total_skill']), axis=1)


        # Determine if the override rule is triggered for each skill
        skill_stats['override_triggered'] = (skill_stats['error_rate_skill'] > SKILL_OVERRIDE_RATE_THRESHOLD) | \
                                            (skill_stats['overtime_rate_skill'] > SKILL_OVERRIDE_RATE_THRESHOLD)

        # Store details for skills where the override is triggered
        skill_override_details = {}
        triggered_override_skills_df = skill_stats[skill_stats['override_triggered']]

        for _, row in triggered_override_skills_df.iterrows():
            skill = row['question_fundamental_skill']
            min_diff = row['min_difficulty_error_or_overtime']
            # Map the minimum difficulty to a label for the macro recommendation
            y_agg = map_difficulty_to_label(min_diff) if pd.notna(min_diff) else "基礎 (Foundation)"
            z_agg = MACRO_REC_TIME_LIMIT # Fixed time limit for macro recommendations
            skill_override_details[skill] = {'Y_agg': y_agg, 'Z_agg': z_agg}
    else:
        # Handle case where grouping column is missing or all null
        print("警告：無法按 'question_fundamental_skill' 分組進行技能分析（欄位不存在或全為空值）。")
        skill_stats = pd.DataFrame() # Empty DataFrame
        skill_override_details = {}


    # --- 7. Practice Planning & Recommendations (logic based on filtered data) ---\
    recommendations_by_skill = {} # Temp dict to hold recommendations per skill
    processed_override_skills = set() # Track skills handled by macro recommendation

    # Determine exempted skills based on sufficient correct & non-overtime performance
    exempted_skills = set()
    if not skill_stats.empty and 'num_correct_not_overtime' in skill_stats.columns:
         exempted_skills = set(skill_stats[skill_stats['num_correct_not_overtime'] > EXEMPTION_THRESHOLD]['question_fundamental_skill'].tolist())

    # Identify all questions that could trigger a recommendation (incorrect or correct-but-slow)
    trigger_indices_filtered = df_filtered[
        (~df_filtered['is_correct']) | # Any incorrect question
        (df_filtered['is_correct'] & df_filtered['overtime']) # Correct but slow questions
    ].index

    # Also consider skills with override triggered, even if they don't have specific trigger questions in the current set
    all_trigger_skills = set(df_filtered.loc[trigger_indices_filtered, 'question_fundamental_skill']) | set(skill_override_details.keys())

    # Process recommendations skill by skill
    for skill in all_trigger_skills:
        if not isinstance(skill, str) or not skill: continue # Skip if skill name is invalid

        if skill not in recommendations_by_skill:
            recommendations_by_skill[skill] = []

        # --- Macro Recommendation Check ---\
        # If override is triggered for this skill and hasn't been processed yet
        if skill in skill_override_details and skill not in processed_override_skills:
            override_info = skill_override_details[skill]
            # Generate the macro recommendation text
            macro_rec = (
                f"針對 [{skill}] 技能，由於整體表現有較大提升空間 (根據第六章分析)，"
                f"建議全面鞏固基礎，可從 [{override_info['Y_agg']}] 難度題目開始系統性練習，"
                f"掌握核心方法，建議限時 [{override_info['Z_agg']:.1f}] 分鐘。"
            )
            recommendations_by_skill[skill].append({
                'type': 'macro',
                'text': macro_rec,
                'priority': 1 # High priority for macro recommendations
            })
            processed_override_skills.add(skill) # Mark skill as handled by macro rec
            # Skip individual recommendations for this skill as per logic ("instead of")
            continue

        # --- Exemption Check ---\
        # If no macro recommendation, check if the skill is exempted
        if skill in exempted_skills:
            # Store exemption info only if no other recommendations exist for this skill yet
            if not recommendations_by_skill.get(skill):
                 recommendations_by_skill[skill].append({
                     'type': 'exemption',
                     'text': f"技能 [{skill}] 表現穩定，可暫緩練習。",
                     'priority': 99 # Low priority
                 })
            # Skip individual recommendations if exempted
            continue

        # --- Individual Recommendation Generation ---\
        # If not overridden and not exempted, generate recommendations based on trigger questions
        # Find indices of trigger questions *for this specific skill* in the filtered data
        skill_trigger_indices_filtered = df_filtered[
            (df_filtered['question_fundamental_skill'] == skill) &
            ( (~df_filtered['is_correct']) | (df_filtered['is_correct'] & df_filtered['overtime']) )
        ].index

        processed_q_ids_for_skill = set() # Avoid duplicate recs if a question triggers multiple ways?

        for idx in skill_trigger_indices_filtered:
            question = df_filtered.loc[idx]
            q_id = question['question_id']

            # Avoid processing the same question multiple times for the same skill if logic allows
            if q_id in processed_q_ids_for_skill:
                continue

            difficulty = question['question_difficulty']
            q_time = question['question_time']
            is_overtime_flag = question['overtime'] # Needed for calculating practice time
            is_correct_flag = question['is_correct']

            # Fetch diagnostic flags (SFE, error class) from the *original* DataFrame
            # Use try-except for safety in case q_id somehow not found in original df
            try:
                question_diagnostics = df.loc[df['question_id'] == q_id].iloc[0]
                error_class = question_diagnostics['error_classification']
                is_sfe_flag = question_diagnostics['special_focus_error']
            except IndexError:
                 print(f"警告：無法在原始數據中找到題目 ID {q_id} 的診斷信息。")
                 error_class = "未知"
                 is_sfe_flag = False


            # Calculate recommended practice difficulty (Y) and time limit (Z)
            practice_difficulty_y = map_difficulty_to_label(difficulty)
            practice_time_z = calculate_practice_time(q_time, is_overtime_flag)

            # Determine trigger reason and priority for the recommendation text
            trigger_reason = ""
            priority = 5 # Default priority
            if not is_correct_flag:
                # Triggered by an incorrect question
                trigger_reason = f"基於錯誤題目 (ID: {q_id}, 分類: {error_class})"
                if is_sfe_flag:
                    trigger_reason += " **基礎掌握不穩**"
                    priority = 2 # Higher priority for SFE errors
                else:
                    priority = 3 # Normal error priority
            elif is_correct_flag and is_overtime_flag:
                 # Triggered by a correct but slow question
                 trigger_reason = f"基於正確但超時題目 (ID: {q_id})"
                 priority = 4 # Priority lower than errors

            # Construct the individual recommendation text
            rec_text = f"{trigger_reason}: 建議練習 [{practice_difficulty_y}] 難度的題目，目標限時 [{practice_time_z:.1f}] 分鐘。"

            recommendations_by_skill[skill].append({
                'type': 'individual',
                'text': rec_text,
                'priority': priority,
                'is_sfe': is_sfe_flag, # Store SFE status for potential highlighting
                'q_id': q_id # Store original question ID
            })
            processed_q_ids_for_skill.add(q_id)

    # --- Final Assembly of Recommendations List ---\
    final_recommendations_list = []
    processed_final_skills = set() # Track skills added to the final list

    # Step 1: Add Exemption Notes for skills that are exempt AND have no other recommendations
    for skill in exempted_skills:
        if not isinstance(skill, str) or not skill: continue
        # Check if skill has no macro override and no individual recommendations were generated
        if skill not in processed_override_skills and not any(rec['type'] == 'individual' for rec in recommendations_by_skill.get(skill, [])):
             # Find the exemption message stored earlier (if any)
             exemption_rec = next((rec for rec in recommendations_by_skill.get(skill, []) if rec['type'] == 'exemption'), None)
             if exemption_rec:
                 final_recommendations_list.append({
                     'skill': skill,
                     'text': exemption_rec['text'],
                     'priority': exemption_rec['priority']
                 })
                 processed_final_skills.add(skill)

    # Step 2: Process skills with Macro or Individual recommendations
    # Sort skills alphabetically for consistent output order before applying priority
    valid_skill_keys = [k for k in recommendations_by_skill.keys() if isinstance(k, str) and k]
    sorted_skills = sorted(valid_skill_keys)


    for skill in sorted_skills:
        if skill in processed_final_skills: continue # Already handled (as exemption-only)

        skill_recs = recommendations_by_skill.get(skill, [])
        # Filter out pure exemption messages if other recommendations exist
        active_recs = [rec for rec in skill_recs if rec['type'] != 'exemption']

        if not active_recs: continue # Skip if only exemption messages remained or list was empty

        # Sort recommendations within the skill: macro first, then by priority (SFE higher)
        active_recs.sort(key=lambda x: x.get('priority', 5))

        # Start building the combined text for this skill's recommendations
        combined_skill_rec_text = f"--- 技能: {skill} ---"
        adjustment_text = "" # To hold Chapter 2 adjustments

        # Determine if Chapter 2 adjustments apply
        trigger_question_ids_for_skill = set()
        has_real_trigger = False
        has_pure_trigger = False

        # Collect relevant question IDs and check their types
        for rec in active_recs:
            if rec['type'] == 'individual' and 'q_id' in rec:
                trigger_question_ids_for_skill.add(rec.get('q_id'))
            elif rec['type'] == 'macro':
                # For macro, consider all questions of that skill in filtered data
                 skill_q_ids = df_filtered[df_filtered['question_fundamental_skill'] == skill]['question_id'].tolist()
                 trigger_question_ids_for_skill.update(skill_q_ids)

        if trigger_question_ids_for_skill:
            # Check the types of the trigger questions in the original DataFrame
            trigger_questions_df = df[df['question_id'].isin(trigger_question_ids_for_skill)]
            if not trigger_questions_df.empty:
                 unique_types = trigger_questions_df['question_type'].unique()
                 has_real_trigger = 'REAL' in unique_types
                 has_pure_trigger = 'PURE' in unique_types

        # Apply Chapter 2 adjustments based on flags and trigger types
        if poor_real and has_real_trigger:
            adjustment_text += " **Real題比例建議佔總練習題量2/3。**"
        if slow_pure and has_pure_trigger:
             adjustment_text += " **建議此考點練習題量增加。**"

        # Append individual/macro recommendation texts
        for rec in active_recs:
            rec_text = rec['text']
            combined_skill_rec_text += f"\n- {rec_text}" # Use newline for list format

        # Add adjustment text if applicable
        if adjustment_text:
            combined_skill_rec_text += f"\n{adjustment_text.strip()}"

        # Determine the highest priority (lowest number) for this skill block for sorting
        overall_priority = min(rec.get('priority', 5) for rec in active_recs)

        final_recommendations_list.append({
            'skill': skill,
            'text': combined_skill_rec_text.strip(), # Final text block for the skill
            'priority': overall_priority
        })
        processed_final_skills.add(skill) # Mark as added to final list

    # Step 3: Sort the final list of recommendation blocks by priority
    final_recommendations_list.sort(key=lambda x: x['priority'])

    # --- 8. Diagnostic Summary Generation ---\
    # Assemble the natural language report using calculated flags and data.
    summary_lines = []
    summary_lines.append("========== GMAT 量化診斷報告 ==========")

    # Section 1: Overall Time Strategy
    summary_lines.append("\n**1. 整體時間策略與作答節奏**")
    time_pressure_desc = "顯著" if time_pressure else "相對充裕"
    time_diff_desc = f"總時間差 {time_diff:.1f} 分鐘"
    summary_lines.append(f"- 本次測驗時間壓力 **{time_pressure_desc}** ({time_diff_desc})。")
    if time_pressure and invalid_question_ids:
        invalid_ids_str = ', '.join(map(str, sorted(invalid_question_ids)))
        summary_lines.append(f"- 測驗末尾存在 {len(invalid_question_ids)} 題作答時間少於 {TIME_PRESSURE_FAST_TIME_THRESHOLD:.1f} 分鐘 (題目ID: {invalid_ids_str}), 這些題目已被標記為 **無效數據**，未納入後續主要分析。")
    elif time_pressure:
         summary_lines.append("- 雖然偵測到時間壓力條件，但未發現末尾作答過快的無效題目。")
    else:
        summary_lines.append("- 未檢測到明顯的因時間壓力導致的末尾搶答現象。")
    summary_lines.append(f"- 基於時間壓力評估，單題作答 **超時閾值** 設定為 **{overtime_threshold:.1f} 分鐘**。")

    # Section 2: Performance Overview
    summary_lines.append("\n**2. 表現概覽**")
    summary_lines.append("- **題型表現 (基於有效數據):**")
    if num_total_real > 0 or num_total_pure > 0:
        if num_total_real > 0:
            summary_lines.append(f"  - **Real 題** ({num_total_real} 題): 錯誤率 {wrong_rate_real:.1%}, 超時率 {over_time_rate_real:.1%}")
        else:
            summary_lines.append("  - Real 題: 本次測驗無有效的 Real 題數據。")
        if num_total_pure > 0:
            summary_lines.append(f"  - **Pure 題** ({num_total_pure} 題): 錯誤率 {wrong_rate_pure:.1%}, 超時率 {over_time_rate_pure:.1%}")
        else:
             summary_lines.append("  - Pure 題: 本次測驗無有效的 Pure 題數據。")
        # Add diagnostic flags if triggered
        diag_flags = []
        if poor_real: diag_flags.append("Real 題錯誤數量顯著較多 (可能與閱讀理解/問題轉化有關)")
        if poor_pure: diag_flags.append("Pure 題錯誤數量顯著較多 (需關注數學概念/計算)")
        if slow_real: diag_flags.append("Real 題超時情況顯著較多 (可能與閱讀速度/策略有關)")
        if slow_pure: diag_flags.append("Pure 題超時情況顯著較多 (需關注概念提取/計算效率)")
        if diag_flags:
             summary_lines.append("    *初步診斷:*\n" + "\n".join([f"      - {flag_desc}" for flag_desc in diag_flags]))
    else:
         summary_lines.append("  - 未能分析 Real/Pure 題表現 (數據不足或均無效)。")

    # Error distribution by difficulty
    errors_by_difficulty = df_filtered[~df_filtered['is_correct']]['difficulty_label'].value_counts().sort_index()
    if not errors_by_difficulty.empty:
         summary_lines.append("- **錯誤主要難度區間:**")
         for level, count in errors_by_difficulty.items():
              summary_lines.append(f"  - {level}: {count} 題")
    elif not df_filtered.empty:
         summary_lines.append("- **錯誤主要難度區間:** 本次測驗有效數據中無錯誤記錄。")

    # Weakest skills based on combined rates
    if not skill_stats.empty:
        skill_stats_sorted = skill_stats.sort_values(by=['error_rate_skill', 'overtime_rate_skill'], ascending=[False, False])
        summary_lines.append("- **相對弱項技能 (基於錯誤率/超時率，最多顯示前 3 項或觸發覆蓋規則的技能):**")
        shown_count = 0
        weak_skills_found = False
        for _, row in skill_stats_sorted.iterrows():
            skill_name = row['question_fundamental_skill']
            if not isinstance(skill_name, str) or not skill_name: continue # Skip invalid skill names

            is_override = row['override_triggered']
            is_high_rate = row['error_rate_skill'] > 0.2 or row['overtime_rate_skill'] > 0.2
            has_issue = row['error_rate_skill'] > 0 or row['overtime_rate_skill'] > 0

            if (is_high_rate or shown_count < 3 or is_override) and has_issue:
                override_marker = " *(需優先鞏固)*" if is_override else ""
                summary_lines.append(f"  - {skill_name} (錯誤率: {row['error_rate_skill']:.1%}, 超時率: {row['overtime_rate_skill']:.1%}){override_marker}")
                shown_count += 1
                weak_skills_found = True
                if shown_count >= 3 and not is_override and not is_high_rate:
                    break # Stop after 3 unless override or high rate

        if not weak_skills_found:
             summary_lines.append("  - 未檢測到明顯弱項技能 (所有技能錯誤率與超時率均較低)。")
    else:
        summary_lines.append("- **相對弱項技能:** 未能分析技能表現 (數據不足或技能信息缺失)。")


    # Section 3: Core Problem Diagnosis
    summary_lines.append("\n**3. 核心問題診斷**")
    # --- NEW: Detailed Per-Question Diagnosis Section ---
    if problematic_question_details_q:
        # Sort by priority (SFE first), then by question position/ID
        problematic_question_details_q.sort(key=lambda x: (
            0 if x['sfe'] else 1, # SFE first
            df.loc[df['question_id'] == x['id'], 'question_position'].iloc[0] # Then by position
            ))

        summary_lines.append("**核心問題診斷 (逐題分析):**")
        for detail in problematic_question_details_q:
            q_id = detail['id']
            q_type = detail['type']
            q_skill = detail['skill']
            q_time_txt = f"{detail['time']:.1f}min"
            correct_txt = "正確" if detail['correct'] else "錯誤"
            sfe_marker = " **[基礎掌握不穩]**" if detail['sfe'] else ""
            diff_label = detail['difficulty_label']
            time_perf_desc = f"({detail['classification']})" # Use the stored classification

            summary_lines.append(f"\n- **題目 ID {q_id}:** [{q_type}, {q_skill}, {diff_label}, {q_time_txt}, {correct_txt}] {time_perf_desc}{sfe_marker}")
            if detail['diagnosis'] != "N/A":
                summary_lines.append(f"  - *診斷:* {detail['diagnosis']}")
            if detail['action'] != "N/A":
                summary_lines.append(f"  - *建議行動:* {detail['action']}")
    else:
        summary_lines.append("**核心問題診斷:** 本次測驗在有效題目中未發現明顯的核心問題（錯誤、超時等）。")


    # Section 4: Pattern Observation
    summary_lines.append("\n**4. 特殊模式觀察**")
    if early_fast_q_ids:
        early_ids_str = ', '.join(map(str, sorted(early_fast_q_ids)))
        summary_lines.append(f"- **測驗前期作答:** 測驗開始階段存在 **{len(early_fast_q_ids)} 題** 作答速度 **明顯偏快** (題目ID: {early_ids_str})。建議注意 **保持穩定的答題節奏**，確保充分理解題目，避免潛在的 \"flag for review\" 風險。")
    else:
        summary_lines.append("- **測驗前期作答:** 未發現在測驗初期（前1/3）作答明顯過快（<1分鐘）的情況。")

    # Carelessness Issue Assessment
    if carelessness_issue:
        fast_wrong_contributing_ids = df.loc[df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'] & ~df['is_correct'], 'question_id'].tolist()
        ids_str = f" (涉及題目 ID: {', '.join(map(str, sorted(fast_wrong_contributing_ids)))})" if fast_wrong_contributing_ids else ""
        summary_lines.append(f"- **粗心問題評估:** 「相對快且錯」的比例 ({fast_wrong_rate:.1%}) **偏高** (>{CARELESSNESS_RATE_THRESHOLD:.0%}){ids_str}。提示可能需 **關注答題仔細程度**。(建議結合第3部分這些題目的診斷，確認是粗心、跳步還是理解不充分導致)")
    elif num_relatively_fast_total > 0 : # Only report if there were fast questions to calculate rate from
         summary_lines.append(f"- **粗心問題評估:** 「相對快且錯」的比例 ({fast_wrong_rate:.1%}) 在閾值 ({CARELESSNESS_RATE_THRESHOLD:.0%}) 以下，未觸發普遍性粗心問題的警示。")
    else:
         summary_lines.append("- **粗心問題評估:** 未能評估粗心問題（沒有發現作答相對較快的題目）。")


    # Section 5: Foundational Skill Consolidation
    summary_lines.append("\n**5. 基礎鞏固提示**")
    triggered_override_skills_list = [s for s in skill_override_details.keys() if isinstance(s, str) and s] # Filter invalid keys

    if triggered_override_skills_list:
        skills_str = ', '.join(triggered_override_skills_list)
        summary_lines.append(f"- **優先系統鞏固:** 對於 **[{skills_str}]** 這些核心技能，由於整體錯誤率或超時率 **超過 50%**，表現顯示出較大的系統性提升空間。**強烈建議優先進行系統性的基礎概念學習和鞏固**，而非僅針對個別錯題進行練習。詳細的宏觀練習建議見下一節。")
    else:
        summary_lines.append("- **優先系統鞏固:** 未發現錯誤率或超時率超過 50% 的核心技能。練習建議將主要基於個別錯誤題目、正確但超時題目以及相對弱項技能的分析。")

    # Section 6: Detailed Practice Plan
    summary_lines.append("\n**6. 詳細練習計劃**")
    if final_recommendations_list:
        summary_lines.append("根據以上分析，建議您針對以下技能進行練習：\n")
        for rec in final_recommendations_list:
            # Add extra newline before each skill block for better separation
            summary_lines.append(f"\n{rec['text']}")
    elif not df_filtered.empty: # Only say no recommendations if analysis was actually run
        summary_lines.append("- 本次分析未生成具體的練習建議。可能原因包括：所有題目均正確且未超時，或所有存在問題的技能均因表現穩定而被豁免練習。")
    # If df_filtered was empty, the message is handled earlier

    # Section 7: Next Steps and Reflection Guidance
    summary_lines.append("\n\n**7. 後續行動與反思指引**")
    summary_lines.append("本報告旨在提供數據驅動的診斷方向，實際提升需結合個人學習體驗和針對性練習。請特別關注第 3 部分列出的逐題診斷與建議行動。")
    summary_lines.append("\n- **引導反思 (針對第3部分診斷的具體題目):**")

    if not problematic_question_details_q:
        summary_lines.append("  - 本次測驗表現穩定，未發現明顯錯誤或超時問題。可思考如何進一步提升效率或挑戰更高難度。")
    else:
        for detail in problematic_question_details_q:
            q_id = detail['id']
            q_type = detail['type']
            q_skill = detail['skill']
            classification = detail['classification']
            is_sfe = detail['sfe']
            correct = detail['correct']

            prompt = f"  - **題目 ID {q_id}** ({q_type}, {q_skill}, {classification}){': [基礎掌握不穩]' if is_sfe else ':'}"
            reflection_points = []

            if not correct:
                if '慢' in classification:
                    points = ["問題理解/轉化", "核心概念/公式", "計算執行", "解題步驟規劃"]
                    reflection_points.append(f"回憶卡點：是 {'、'.join(points)} 中的哪方面？")
                elif '快' in classification or '正常' in classification:
                    points = ["題目理解偏差/條件遺漏", "概念應用錯誤", "計算粗心", "方法選擇不當"]
                    reflection_points.append(f"回憶失誤點：是 {'、'.join(points)} 中的哪方面？")
                if is_sfe:
                    reflection_points.append("為何在已掌握難度範圍內失誤？")
            elif detail['correct_but_slow']:
                points = ["問題理解/轉化", "概念提取", "公式選擇", "計算執行", "步驟規劃", "反覆檢查"]
                reflection_points.append(f"回憶效率瓶頸：是哪個環節耗時最長？({'、'.join(points)} 等)")

            if reflection_points:
                prompt += " " + " ".join(reflection_points)
            else:
                 prompt += " 請回憶該題作答過程中的具體情況。"

            summary_lines.append(prompt)

    summary_lines.append("\n- **二級證據參考建議 (針對第3部分診斷的具體題目):**")
    if not problematic_question_details_q:
        summary_lines.append("  - 無需特別查找二級證據。")
    else:
        secondary_evidence_needed = False
        secondary_prompts = []
        for detail in problematic_question_details_q:
            if "二級證據" in detail['action'] or "查看近期" in detail['action']:
                secondary_evidence_needed = True
                q_id = detail['id']
                q_type = detail['type']
                q_skill = detail['skill']
                search_characteristic = detail['classification'] # Use the classification as the primary search characteristic
                # Refine based on specific issues if needed (though classification often covers it for Q)
                if detail['sfe']: search_characteristic += " (SFE)"
                elif detail['correct_but_slow']: search_characteristic = "正確但慢"

                secondary_prompts.append(f"  - **題目 ID {q_id}** ({q_type}, {q_skill}): 查找近期練習中其他 **'{search_characteristic}'** 的 **{q_skill} ({q_type})** 題目，歸納錯誤模式/考點/障礙類型 (參考第3部分診斷)。若樣本不足(<5-10題)，注意積累。")

        if not secondary_evidence_needed:
            summary_lines.append("  - 根據本次診斷，暫無需特別查找二級證據。")
        else:
            summary_lines.append("  - *觸發時機:* 當第 3 部分的建議行動提示需要查看二級證據時，或您無法準確回憶具體障礙點/錯誤原因時。")
            summary_lines.append("  - *建議行動 (請根據以下針對性建議執行):*")
            summary_lines.extend(secondary_prompts)

    summary_lines.append("\n========== 報告結束 ==========")


    # --- Combine DataFrame and Summary for Output ---\
    # Convert summary lines list into a DataFrame for concatenation
    summary_df = pd.DataFrame({'診斷報告與建議': summary_lines})

    # Create spacer rows (as DataFrame) with same columns as the main data df
    spacer_df = pd.DataFrame(np.nan, index=range(3), columns=df.columns) # More robust way

    # Align the summary DataFrame to have the first column named the same as df's first column
    # All summary text will go into this first column, others will be NaN
    summary_df_aligned = pd.DataFrame(columns=df.columns)
    # Ensure the target column exists before assigning
    if df.columns[0] in summary_df_aligned.columns:
        summary_df_aligned[df.columns[0]] = summary_df['診斷報告與建議']
    else:
        # Fallback: create the column if it doesn't exist (shouldn't happen with DataFrame init)
        summary_df_aligned.insert(0, df.columns[0], summary_df['診斷報告與建議'])


    # Concatenate the original data (with added columns), spacer, and aligned summary
    final_df = pd.concat([df, spacer_df, summary_df_aligned], ignore_index=True)


    # --- Save Final Result ---\
    try:
        # Save the combined DataFrame to the specified output CSV file
        # Use utf-8-sig encoding to ensure correct handling of BOM for Excel compatibility
        final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"\n分析完成，診斷報告與建議已儲存至: {output_csv_path}")
    except Exception as e:
        print(f"\n錯誤：儲存結果至 CSV 檔案 '{output_csv_path}' 時發生錯誤: {e}")
        sys.exit(1) # Exit with error status if saving fails

# --- Command-Line Execution ---\
if __name__ == '__main__':
    # Set up argument parser for command-line usage
    parser = argparse.ArgumentParser(
        description='分析 GMAT Quantitative 測驗數據並生成診斷報告 (基於 gmat-q-score-logic-dustin-v1.1.md)。',
        formatter_class=argparse.RawTextHelpFormatter # Preserve newline formatting in help messages
    )
    parser.add_argument(
        'input_csv',
        help='輸入的 CSV 檔案路徑 (例如：testset-q.csv)。\n必須包含欄位: Question, Response Time (Minutes), Performance, Question Type, Fundamental Skills, Q_b'
    )
    parser.add_argument(
        'output_csv',
        help='輸出的 CSV 檔案路徑 (例如：testset-q-analyzed.csv)。\n將包含原始數據、診斷欄位及報告摘要。'
    )
    # Optional arguments to override time pressure detection in a mutually exclusive group
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--force_time_pressure',
        action='store_true',
        help='強制將 time_pressure 設為 True，覆蓋自動檢測結果。'
    )
    group.add_argument(
        '--force_no_time_pressure',
        action='store_true',
        help='強制將 time_pressure 設為 False，覆蓋自動檢測結果。'
    )


    args = parser.parse_args()

    # Determine the override value based on arguments
    override = None
    if args.force_time_pressure:
        override = True
    elif args.force_no_time_pressure:
        override = False

    # Run the main analysis function with parsed arguments
    analyze_gmat_data(args.input_csv, args.output_csv, user_override_time_pressure=override)