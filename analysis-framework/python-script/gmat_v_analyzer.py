import pandas as pd
import math
import numpy as np # For handling potential NaN/division by zero
import argparse
import sys
from collections import defaultdict

# --- Configuration --- (Based on gmat-v-score-logic-dustin-v1.1.md)
MAX_ALLOWED_TIME_V = 45.0
TIME_PRESSURE_THRESHOLD_V = 1.0 # time_diff < 1.0 min means pressure
OVERTIME_THRESHOLD_CR_PRESSURE = 2.0
OVERTIME_THRESHOLD_CR_NO_PRESSURE = 2.5
RC_GROUP_TARGET_TIME_3Q_PRESSURE = 6.0
RC_GROUP_TARGET_TIME_4Q_PRESSURE = 8.0
RC_GROUP_TARGET_TIME_3Q_NO_PRESSURE = 7.0
RC_GROUP_TARGET_TIME_4Q_NO_PRESSURE = 9.0
RC_INDIVIDUAL_Q_THRESHOLD = 2.0
RC_READING_TIME_THRESHOLD_3Q = 2.0
RC_READING_TIME_THRESHOLD_4Q = 2.5
LAST_THIRD_FRACTION = 1/3
INVALID_TIME_THRESHOLD_HASTY = 1.0
INVALID_TIME_THRESHOLD_ABANDONED = 0.5
RELATIVE_SPEED_FACTOR_HASTY = 0.5 # For hasty check against first_third_avg
RELATIVE_SPEED_FACTOR_SUSPICIOUS = 0.5 # For suspiciously_fast check against overall avg
RELATIVELY_FAST_FACTOR_ERROR_CLASSIFICATION = 0.75 # For Fast & Wrong etc. classification
EARLY_FAST_TIME_THRESHOLD = 1.0 # Absolute time for early fast warning
EARLY_FRACTION = 1/3
CARELESSNESS_RATE_THRESHOLD_V = 0.25
SKILL_OVERRIDE_ERROR_RATE_THRESHOLD_V = 0.50
EXEMPTION_THRESHOLD_V = 2 # num_correct_not_overtime > threshold
TARGET_PRACTICE_TIME_CR = 2.0
TARGET_PRACTICE_TIME_RC = 1.5
PRACTICE_TIME_SLOW_REDUCTION_V = 0.5
Z_TIME_INCREASE_WARNING_THRESHOLD = 2.0 # If Z - target_time > threshold


# --- Helper Functions ---

def map_difficulty_to_label(d):
    # Replicates the 6-level difficulty mapping (assuming same as Q)
    if d is None or pd.isna(d):
        return "未知難度"
    if d <= -1: return "低難度 (Low) / 505+"
    if -1 < d <= 0: return "中難度 (Mid) / 555+"
    if 0 < d <= 1: return "中難度 (Mid) / 605+"
    if 1 < d <= 1.5: return "中難度 (Mid) / 655+"
    if 1.5 < d <= 1.95: return "高難度 (High) / 705+"
    if 1.95 < d <= 2: return "高難度 (High) / 805+"
    if d > 2: return "極高難度 (Very High) / 805+" # Handle potential higher values
    return "未知難度" # Default fallback

def floor_to_nearest_0_5(value):
    # Rounds a number down to the nearest multiple of 0.5.
    if value is None or pd.isna(value):
        return None
    return math.floor(value * 2) / 2

def safe_divide(numerator, denominator):
    # Prevents division by zero errors when calculating rates.
    if denominator is None or denominator == 0:
        return 0.0
    if numerator is None:
        return 0.0
    try:
        num = pd.to_numeric(numerator, errors='coerce')
        den = pd.to_numeric(denominator, errors='coerce')
        if pd.isna(num) or pd.isna(den) or den == 0:
            return 0.0
        return num / den
    except (ZeroDivisionError, TypeError, ValueError):
        return 0.0

def calculate_practice_time_v(question_time, is_slow, question_type):
    # Replicates Chapter 7 logic for calculating recommended practice time limit (Z) for Verbal.
    target_time = TARGET_PRACTICE_TIME_CR if question_type == 'CR' else TARGET_PRACTICE_TIME_RC
    base_time = question_time - PRACTICE_TIME_SLOW_REDUCTION_V if is_slow else question_time
    z_raw = floor_to_nearest_0_5(base_time)
    # Ensure z_raw is not None before comparing
    if z_raw is None:
        return target_time # Or handle as an error/default?
    z = max(z_raw, target_time)
    return z

# --- Detailed Diagnosis Function (NEW) ---
def get_detailed_diagnosis_v(question_data):
    """
    Generates detailed diagnosis, action, reflection, and evidence prompts for a single Verbal question.
    Based on Chapter 3 logic from gmat-v-score-logic-dustin-v1.1.md.
    Input: A dictionary or Series containing question details (id, type, is_correct, is_slow, etc.)
    Output: A dictionary with detailed diagnostic strings.
    """
    q_id = question_data['question_id']
    is_correct = question_data['is_correct']
    is_slow = question_data.get('is_slow', False) # Use .get for safety
    error_class = question_data.get('error_classification', 'N/A')
    is_sfe = question_data.get('special_focus_error', False)
    is_suspiciously_fast_correct = question_data.get('suspiciously_fast_correct', False)
    q_type = question_data['question_type']
    rc_group_id = question_data.get('rc_group_id') # Get RC group info if available
    skill = question_data.get('question_fundamental_skill', '未知技能')


    diagnosis = ""
    action = ""
    reflection = ""
    evidence = ""
    is_problematic = False # Flag if any diagnosis is generated

    if not is_correct:
        is_problematic = True
        if error_class == 'Fast & Wrong':
            diagnosis = "快且錯：作答速度相對平均水平明顯偏快，但結果錯誤。"
            action = "回憶：當時是時間壓力下搶答，還是對題目/選項理解有偏差？"
            reflection = f"Q{q_id} ({q_type}): 這題的快速錯誤是因為審題不清、忽略關鍵詞/邏輯，還是方法應用不熟練導致的？是否有固定類型的快錯模式？"
            evidence = f"查找 {skill} 相關錯題：檢查是否有其他題目也因速度過快而出錯，尤其是涉及相似邏輯鏈/閱讀結構的題目。確認是普遍的速度問題還是特定知識點掌握不牢。"
        elif error_class == 'Slow & Wrong':
            diagnosis = "慢且錯：作答時間偏長，但結果錯誤。"
            action = "回憶：當時的主要困難點在哪？是閱讀理解（長難句/詞彙）、邏詞推理卡住，還是選項辨析困難？"
            reflection = f"Q{q_id} ({q_type}): 這題耗時較長且錯誤，是哪個環節最耗時？是文章/題幹理解困難，邏輯鏈推導不清，還是選項比較難以排除？"
            evidence = f"查找 {skill} 相關錯題：檢查是否存在其他耗時較長且出錯的題目。分析這些題目共性，判斷是閱讀速度/理解問題，還是特定邏輯類型/選項干擾的處理問題。"
            if q_type == 'RC' and rc_group_id:
                 reflection += f" (RC組{rc_group_id}) 這次錯誤與文章本身理解關係大，還是題目/選項難度高？"
                 evidence += f" (RC組{rc_group_id}) 結合文章內容，分析是閱讀定位錯誤、細節理解偏差，還是主旨/推斷題的思路問題。"
        elif error_class == 'Normal Time & Wrong':
            diagnosis = "正常時間但錯誤：作答時間在正常範圍，但結果錯誤。"
            action = "回憶：當時的思考路徑是什麼？哪個環節出現了偏差？"
            reflection = f"Q{q_id} ({q_type}): 這題在正常時間內出錯，是哪個具體的知識點/技巧掌握不牢？是 CR 的特定邏輯錯誤類型（如无关比較、範圍擴大），還是 SC 的語法點/句意理解，或是 RC 的細節定位/推斷失誤？"
            evidence = f"查找 {skill} 相關錯題：整理類似題型或考點的錯誤，看是否存在系統性的理解偏差或方法缺陷。"
            if q_type == 'RC' and rc_group_id:
                 reflection += f" (RC組{rc_group_id}) 這個錯誤是獨立的題目理解問題，還是與文章段落/主旨理解有關？"
                 evidence += f" (RC組{rc_group_id}) 參照文章，確認是哪個選項的迷惑性強，或者自己對文章某部分的理解是否存在偏差。"

        if is_sfe:
            diagnosis += " **(基礎不穩)**"
            action += " **必須**優先複習鞏固相關基礎知識點/解題方法。"
            reflection += " **反思：** 為何在相對基礎的題目上會失誤？是概念不清、方法遺忘，還是應用不熟？"
            evidence += " **重點查找：** 整理所有被標記為 SFE 的錯題，找出共通的薄弱基礎環節。"

    elif is_correct:
        if is_slow: # Correct but slow
            is_problematic = True
            diagnosis = "正確但慢：結果正確，但用時顯著偏長。"
            action = "回憶：哪個環節耗時最長？是閱讀/審題，思考/推理，還是選項排除？"
            reflection = f"Q{q_id} ({q_type}): 這題雖然做對了，但為什麼花了這麼長時間？是閱讀速度慢，邏輯思考猶豫不決，選項比較耗時，還是對解題方法不夠自信/熟練？"
            evidence = f"查找 {skill} 相關題目：找出其他耗時較長的題目（不論對錯），分析是否存在普遍的效率瓶頸。"
            if q_type == 'RC' and rc_group_id:
                 reflection += f" (RC組{rc_group_id}) 耗時長是因為文章難讀，題目難，還是定位/回讀次數過多？"
                 evidence += f" (RC組{rc_group_id}) 分析閱讀和解題過程，是閱讀策略問題還是解題技巧效率問題？"
        elif is_suspiciously_fast_correct: # Correct and suspiciously fast
             is_problematic = True
             diagnosis = "正確但過快：結果正確，但用時異常短。"
             action = "回憶：是題目確實簡單，還是可能存在跳過步驟/僥倖蒙對的情況？"
             reflection = f"Q{q_id} ({q_type}): 這題做得又快又對，是真的掌握得很好，還是有可能因為過於自信而簡化了思考過程？確認自己是否完全理解了所有邏輯/語義細節？"
             evidence = f"查找 {skill} 相關題目：檢查是否存在其他作答異常快的題目，評估是否存在潛在的風險（如依賴直覺而非嚴謹分析）。"

    return {
        'question_id': q_id,
        'is_problematic': is_problematic,
        'diagnosis_text': diagnosis,
        'action_text': action,
        'reflection_prompt': reflection,
        'second_level_evidence_prompt': evidence,
        'error_classification': error_class, # Keep for potential filtering
        'is_sfe': is_sfe,
        'is_correct': is_correct,
        'is_slow': is_slow,
        'rc_group_id': rc_group_id,
        'question_type': q_type,
        'question_fundamental_skill': skill
    }

# --- RC Group Processing Function ---
def identify_and_process_rc_groups(df):
    """Identifies RC groups, calculates group time, estimates reading time."""
    rc_groups = []
    current_group = []
    group_id_counter = 1
    df['rc_group_id'] = None
    df['group_total_time'] = None
    df['rc_reading_time_est'] = None # Estimated reading time for the group (stored on first Q)
    df['num_questions_in_group'] = None

    for index, row in df.iterrows():
        if row['question_type'] == 'RC':
            current_group.append(index)
        else:
            if current_group:
                # Process the completed group
                rc_groups.append(list(current_group)) # Store indices
                df.loc[current_group, 'rc_group_id'] = group_id_counter
                group_id_counter += 1
                current_group = [] # Reset for next group
    # Process the last group if the test ends with RC questions
    if current_group:
        rc_groups.append(list(current_group))
        df.loc[current_group, 'rc_group_id'] = group_id_counter

    # Calculate group times and reading times
    rc_group_details = {} # Store details per group_id
    for group_indices in rc_groups:
        if not group_indices: continue
        group_df = df.loc[group_indices]
        group_id = group_df['rc_group_id'].iloc[0]
        group_total_time = group_df['question_time'].sum()
        num_questions = len(group_indices)
        df.loc[group_indices, 'group_total_time'] = group_total_time
        df.loc[group_indices, 'num_questions_in_group'] = num_questions

        # Estimate reading time (stored on the first question of the group)
        reading_time_est = None
        if num_questions > 1:
            first_q_time = group_df['question_time'].iloc[0]
            other_q_avg_time = group_df['question_time'].iloc[1:].mean()
            # Ensure other_q_avg_time is not NaN before calculation
            if pd.notna(first_q_time) and pd.notna(other_q_avg_time):
                 # Reading time cannot be negative, cap at first question time if avg is higher
                reading_time_est = max(0, first_q_time - other_q_avg_time)
                df.loc[group_indices[0], 'rc_reading_time_est'] = reading_time_est
            else:
                # Handle cases where calculation isn't possible (e.g., only 1 other question is NaN)
                 df.loc[group_indices[0], 'rc_reading_time_est'] = None # Or some default/indicator
        elif num_questions == 1:
             df.loc[group_indices[0], 'rc_reading_time_est'] = None # Cannot estimate for single Q group

        rc_group_details[group_id] = {
            'total_time': group_total_time,
            'num_questions': num_questions,
            'reading_time_est': reading_time_est,
            'indices': group_indices
        }

    return df, rc_group_details

# --- Main Analysis Function ---

def analyze_gmat_verbal_data(input_csv_path, output_csv_path, user_override_time_pressure=None):
    """
    Analyzes GMAT Verbal performance data based on gmat-v-score-logic-dustin-v1.1.md.
    Outputs a CSV with diagnostics and a summary report.
    """
    # Define required original columns for Verbal
    required_original_cols_v = ['Question', 'Response Time (Minutes)', 'Performance',
                                'Question Type', 'Fundamental Skills', 'V_b']
    try:
        # Read CSV with error handling and usecols
        try:
            df = pd.read_csv(input_csv_path, encoding='utf-8', usecols=required_original_cols_v)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_csv_path, encoding='gbk', usecols=required_original_cols_v)
            except UnicodeDecodeError:
                 df = pd.read_csv(input_csv_path, encoding='cp950', usecols=required_original_cols_v)
        except FileNotFoundError:
            print(f"錯誤：找不到輸入文件 '{input_csv_path}'")
            sys.exit(1)
        except ValueError as ve:
             if "usecols" in str(ve) and "not in list of columns" in str(ve):
                 # Check specifically which columns are missing from the expected list
                 try:
                     temp_df_cols = pd.read_csv(input_csv_path, encoding='utf-8', nrows=0).columns
                 except Exception:
                     temp_df_cols = [] # Fallback if reading columns fails
                 missing_in_file = [col for col in required_original_cols_v if col not in temp_df_cols]
                 if missing_in_file:
                      print(f"錯誤：輸入 CSV 文件 '{input_csv_path}' 缺少必要的欄位: {', '.join(missing_in_file)}。請確保文件包含所有必需欄位。")
                 else:
                     # This case might mean a mismatch between required_original_cols_v and the actual logic's needs
                     print(f"錯誤：嘗試讀取指定欄位時出錯，可能欄位名稱不符或檔案問題. Error: {ve}")
                 sys.exit(1)
             else: raise ve
        except Exception as e:
            print(f"讀取CSV時發生未預期的錯誤: {e}")
            sys.exit(1)

        # Validate required columns are present after reading
        missing_cols = [col for col in required_original_cols_v if col not in df.columns]
        if missing_cols:
            print(f"錯誤：讀取後發現 CSV 缺少必要的欄位: {', '.join(missing_cols)}。")
            sys.exit(1)

    except Exception as e:
        print(f"讀取或驗證 CSV 時發生錯誤: {e}")
        sys.exit(1)

    # --- 0. Prepare Initial Data ---
    df.rename(columns={
        'Question': 'question_id',
        'Response Time (Minutes)': 'question_time',
        'Performance': 'performance',
        'Question Type': 'question_type_raw', # Keep raw type temporarily
        'Fundamental Skills': 'question_fundamental_skill',
        'V_b': 'question_difficulty' # Rename V_b to difficulty
    }, inplace=True)

    # Standardize Question Type: Map full names to abbreviations
    type_mapping = {
        'critical reasoning': 'CR',
        'reading comprehension': 'RC'
    }
    # Convert to lower case, strip whitespace, then map
    df['question_type'] = df['question_type_raw'].astype(str).str.strip().str.lower()
    df['question_type'] = df['question_type'].map(type_mapping).fillna(df['question_type_raw'].str.upper()) # Use mapped or original upper
    # Basic check if mapping resulted in only CR/RC or if other types exist
    valid_types = ['CR', 'RC']
    unknown_types = df[~df['question_type'].isin(valid_types)]['question_type_raw'].unique()
    if len(unknown_types) > 0:
        print(f"警告：輸入檔案包含未知的 Question Type: {list(unknown_types)}。這些題目可能無法正確分析。")

    df.drop(columns=['question_type_raw'], inplace=True) # Drop the temporary raw column

    # Clean other columns
    df['performance'] = df['performance'].astype(str).str.strip().str.lower()
    df['question_fundamental_skill'] = df['question_fundamental_skill'].astype(str).str.strip()

    # Convert numeric types, handle errors
    df['question_time'] = pd.to_numeric(df['question_time'], errors='coerce')
    df['question_difficulty'] = pd.to_numeric(df['question_difficulty'], errors='coerce')
    df['question_id'] = pd.to_numeric(df['question_id'], errors='coerce')

    # Drop rows with essential data missing
    essential_cols_numeric = ['question_time', 'question_difficulty', 'question_id']
    initial_rows = len(df)
    df.dropna(subset=essential_cols_numeric, inplace=True)
    # Convert question_id to int after dropping NaNs
    if not df.empty:
         df['question_id'] = df['question_id'].astype(int)
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        print(f"警告：移除了 {rows_dropped} 行，因為 time, difficulty, 或 id 包含無效值。")

    # Add basic derived columns
    df['is_correct'] = df['performance'] == 'correct'
    df['question_position'] = np.arange(1, len(df) + 1)
    # Add placeholder for detailed diagnosis text in main df (optional, could just use list)
    df['detailed_diagnosis'] = ''
    df['detailed_action'] = ''
    df['detailed_reflection'] = ''
    df['detailed_evidence'] = ''

    total_test_time = df['question_time'].sum()
    total_number_of_questions = len(df)

    if total_number_of_questions == 0:
        print("錯誤：數據清理後，無有效題目可供分析。")
        sys.exit(1)

    # Identify RC groups and estimate reading time
    df, rc_group_details = identify_and_process_rc_groups(df)

    # Calculate average time per type (overall - needed for suspiciously_fast later)
    avg_time_per_type = df.groupby('question_type')['question_time'].mean().to_dict()
    avg_time_cr = avg_time_per_type.get('CR', 2.0) # Default if no CR
    avg_time_rc = avg_time_per_type.get('RC', 1.5) # Default if no RC

    # --- 1. Time Strategy & Validity ---
    time_diff = MAX_ALLOWED_TIME_V - total_test_time
    time_pressure = time_diff < TIME_PRESSURE_THRESHOLD_V

    # Apply user override if provided
    if user_override_time_pressure is not None:
        time_pressure = user_override_time_pressure
        print(f"用戶強制設定 time_pressure = {time_pressure}")

    # Set CR overtime threshold
    overtime_threshold_cr = OVERTIME_THRESHOLD_CR_PRESSURE if time_pressure else OVERTIME_THRESHOLD_CR_NO_PRESSURE

    # Define RC group target time FUNCTION based on pressure
    def get_rc_group_target_time(num_questions):
        if num_questions <= 0: return 0
        if num_questions == 3:
            return RC_GROUP_TARGET_TIME_3Q_PRESSURE if time_pressure else RC_GROUP_TARGET_TIME_3Q_NO_PRESSURE
        elif num_questions == 4:
             return RC_GROUP_TARGET_TIME_4Q_PRESSURE if time_pressure else RC_GROUP_TARGET_TIME_4Q_NO_PRESSURE
        else: # Handle groups with other sizes (e.g., 2 or 5+) - proportional?
             # Using avg target time per question from 3/4 Q groups as estimate
             base_target_per_q = (RC_GROUP_TARGET_TIME_4Q_PRESSURE / 4) if time_pressure else (RC_GROUP_TARGET_TIME_4Q_NO_PRESSURE / 4)
             print(f"警告：RC 題組 ID {group_id} 有 {num_questions} 題，非標準 3 或 4 題，將按比例估算目標時間。")
             return base_target_per_q * num_questions

    # Check RC reading time barrier inquiry
    reading_comprehension_barrier_inquiry = False
    long_reading_time_groups = []
    for group_id, details in rc_group_details.items():
        num_q = details['num_questions']
        read_time = details['reading_time_est']
        if read_time is not None and pd.notna(read_time):
            if (num_q == 3 and read_time > RC_READING_TIME_THRESHOLD_3Q) or \
               (num_q == 4 and read_time > RC_READING_TIME_THRESHOLD_4Q):
                reading_comprehension_barrier_inquiry = True
                long_reading_time_groups.append(group_id)
                # Optionally mark the first question of the group?
                # df.loc[details['indices'][0], 'long_reading_time_flag'] = True

    # Calculate average time per type for the FIRST THIRD of the test
    first_third_pos_limit = math.ceil(total_number_of_questions * EARLY_FRACTION)
    df_first_third = df[df['question_position'] <= first_third_pos_limit]
    first_third_avg_time_per_type = df_first_third.groupby('question_type')['question_time'].mean().to_dict()
    first_third_avg_cr = first_third_avg_time_per_type.get('CR', avg_time_cr) # Fallback to overall avg
    first_third_avg_rc = first_third_avg_time_per_type.get('RC', avg_time_rc) # Fallback to overall avg

    # Identify Invalid Data
    invalid_question_ids = []
    last_third_start_pos = math.ceil(total_number_of_questions * (1 - LAST_THIRD_FRACTION))
    df_last_third = df[df['question_position'] > last_third_start_pos]

    if time_pressure:
        for index, row in df_last_third.iterrows():
            q_time = row['question_time']
            q_type = row['question_type']
            q_id = row['question_id']
            rc_group_id = row['rc_group_id']

            is_hasty = False
            is_abandoned = q_time < INVALID_TIME_THRESHOLD_ABANDONED

            if q_time < INVALID_TIME_THRESHOLD_HASTY:
                is_hasty = True
            elif q_type == 'CR' and q_time < (first_third_avg_cr * RELATIVE_SPEED_FACTOR_HASTY):
                 is_hasty = True
            elif q_type == 'RC' and pd.notna(rc_group_id):
                 # Check if the *group* time was relatively fast compared to first third RC avg
                 group_info = rc_group_details.get(rc_group_id)
                 if group_info:
                     group_time = group_info['total_time']
                     num_q_group = group_info['num_questions']
                     # Check if group time is less than half the expected time based on first third average
                     if group_time < (first_third_avg_rc * num_q_group * RELATIVE_SPEED_FACTOR_HASTY):
                         is_hasty = True # Mark the individual question as hasty if its group was fast

            if is_hasty or is_abandoned:
                invalid_question_ids.append(q_id)
                df.loc[index, 'is_invalid'] = True # Mark in main df

    # Initialize diagnostic columns
    df['is_invalid'] = df['is_invalid'].fillna(False).astype(bool)
    df['overtime'] = False # CR specific
    df['group_overtime'] = False # RC group level
    df['individual_overtime'] = False # RC individual analysis time
    df['is_slow'] = False # Combined slow flag for Chapter 3
    df['suspiciously_fast'] = False
    df['difficulty_label'] = df['question_difficulty'].apply(map_difficulty_to_label)
    df['error_classification'] = 'N/A'
    df['special_focus_error'] = False
    df['correct_but_slow'] = False
    df['suspiciously_fast_correct'] = False # For Ch3 Fast&Correct
    df['is_relatively_fast'] = False # For Ch3/Ch5 classifications

    # Mark Overtime (CR, RC Group, RC Individual) and Suspiciously Fast - BEFORE filtering
    for index, row in df.iterrows():
        if row['is_invalid']: continue # Skip invalid questions

        q_time = row['question_time']
        q_type = row['question_type']
        q_id = row['question_id']
        rc_group_id = row['rc_group_id']
        avg_time_for_type = avg_time_per_type.get(q_type, 0)

        # Suspiciously Fast Check (against overall average)
        if avg_time_for_type > 0 and q_time < (avg_time_for_type * RELATIVE_SPEED_FACTOR_SUSPICIOUS):
            df.loc[index, 'suspiciously_fast'] = True

        # CR Overtime
        if q_type == 'CR':
            if q_time > overtime_threshold_cr:
                df.loc[index, 'overtime'] = True
                df.loc[index, 'is_slow'] = True
        # RC Overtime (Group and Individual)
        elif q_type == 'RC' and pd.notna(rc_group_id):
            group_info = rc_group_details.get(rc_group_id)
            if group_info:
                target_group_time = get_rc_group_target_time(group_info['num_questions'])
                # Group Overtime Check
                if group_info['total_time'] > (target_group_time + 1.0):
                    df.loc[index, 'group_overtime'] = True

                # Individual Overtime Check
                adj_rc_time = q_time # Default for non-first questions
                # If it's the first question, adjust by reading time estimate
                if index == group_info['indices'][0] and pd.notna(group_info['reading_time_est']):
                     adj_rc_time = max(0, q_time - group_info['reading_time_est'])

                if adj_rc_time > RC_INDIVIDUAL_Q_THRESHOLD:
                     df.loc[index, 'individual_overtime'] = True

                # Set combined is_slow flag for RC
                if df.loc[index, 'group_overtime'] or df.loc[index, 'individual_overtime']:
                     df.loc[index, 'is_slow'] = True

    # Create Filtered Data (excluding invalid)
    df_filtered = df[~df['is_invalid']].copy()

    if df_filtered.empty:
        print("警告：所有題目都被標記為無效，無法進行後續深入分析。請檢查時間壓力和結尾作答情況。")
        # Output minimal report
        summary_lines = ["========== GMAT Verbal 診斷報告 ==========",
                         "\n**錯誤：** 所有題目均因時間壓力或結尾作答過快而被標記為無效，無法生成診斷報告。"]
        # ... (code to save minimal df and summary - similar to Q script)
        summary_df = pd.DataFrame({'診斷報告與建議': summary_lines})
        spacer_data = {col: [None] * 3 for col in df.columns}
        spacer_df = pd.DataFrame(spacer_data)
        summary_df_aligned = pd.DataFrame(columns=df.columns)
        if df.columns[0] in summary_df_aligned.columns: summary_df_aligned[df.columns[0]] = summary_df['診斷報告與建議']
        else: summary_df_aligned.insert(0, df.columns[0], summary_df['診斷報告與建議'])
        final_df = pd.concat([df, spacer_df, summary_df_aligned], ignore_index=True)
        try:
            final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            print(f"已將包含無效標記的數據儲存至 {output_csv_path}")
        except Exception as e: print(f"儲存部分結果至CSV時發生錯誤: {e}")
        sys.exit(0)

    # --- 2. Multi-dimensional Analysis (on filtered data) ---
    # Analyze error rates by difficulty level and fundamental skill
    # (Similar logic to Q script, can be adapted using difficulty_label and question_fundamental_skill)
    errors_by_difficulty_type = df_filtered[~df_filtered['is_correct']].groupby(['difficulty_label', 'question_type']).size().unstack(fill_value=0)
    total_by_difficulty_type = df_filtered.groupby(['difficulty_label', 'question_type']).size().unstack(fill_value=0)
    # New way: Perform element-wise DataFrame division, handling zeros
    denominator_safe = total_by_difficulty_type.replace(0, np.nan) # Replace 0 with NaN
    error_rate_by_difficulty_type = (errors_by_difficulty_type / denominator_safe).fillna(0) # Divide and fill resulting NaNs with 0

    errors_by_skill = df_filtered[~df_filtered['is_correct']].groupby('question_fundamental_skill').size()
    total_by_skill = df_filtered.groupby('question_fundamental_skill').size()
    # Perform element-wise Series division, handling zeros
    denominator_skill_safe = total_by_skill.replace(0, np.nan)
    error_rate_by_skill = (errors_by_skill / denominator_skill_safe).fillna(0).sort_values(ascending=False)

    # --- 3. Root Cause Diagnosis (on filtered data) ---
    # Find the maximum difficulty achieved correctly for each skill
    if 'question_fundamental_skill' in df_filtered.columns:
         max_correct_difficulty_per_skill = df_filtered[df_filtered['is_correct']].groupby('question_fundamental_skill')['question_difficulty'].max().to_dict()
    else:
        max_correct_difficulty_per_skill = {}

    detailed_diagnoses_list = [] # List to store detailed diagnoses for report

    # Iterate through all *filtered* questions for classification
    for index, question in df_filtered.iterrows():
        q_id = question['question_id']
        q_time = question['question_time']
        q_type = question['question_type']
        skill = question['question_fundamental_skill']
        difficulty = question['question_difficulty']
        is_correct_flag = question['is_correct']
        is_slow_flag = question['is_slow'] # Use the pre-calculated is_slow flag
        is_suspiciously_fast_flag = question['suspiciously_fast']

        # A. Check for Special Focus Error (only for incorrect questions)
        is_sfe = False
        if not is_correct_flag:
            max_diff_for_skill = max_correct_difficulty_per_skill.get(skill, -np.inf)
            is_sfe = difficulty < max_diff_for_skill
            # Update SFE flag in the *original* DataFrame
            df.loc[df['question_id'] == q_id, 'special_focus_error'] = is_sfe

        # B. Classify Time Performance (Relative Fastness for error classification)
        avg_time = avg_time_per_type.get(q_type, 0)
        is_relatively_fast_ec = (q_time < avg_time * RELATIVELY_FAST_FACTOR_ERROR_CLASSIFICATION) if avg_time > 0 else False
        # Update is_relatively_fast helper in *original* DataFrame
        df.loc[df['question_id'] == q_id, 'is_relatively_fast'] = is_relatively_fast_ec

        # C. Assign error classification or correctness flags
        classification = 'N/A'
        current_suspiciously_fast_correct = False
        current_correct_but_slow = False
        if not is_correct_flag:
            # Error Classification
            if is_relatively_fast_ec:
                classification = 'Fast & Wrong'
            elif is_slow_flag:
                classification = 'Slow & Wrong'
            else: # Normal time
                 classification = 'Normal Time & Wrong'
            # Update classification in the *original* DataFrame
            df.loc[df['question_id'] == q_id, 'error_classification'] = classification
        else:
            # Correctness Classification
            if is_suspiciously_fast_flag:
                 # Mark Fast & Correct (using suspicious threshold)
                 df.loc[df['question_id'] == q_id, 'suspiciously_fast_correct'] = True
                 current_suspiciously_fast_correct = True
            if is_slow_flag:
                 # Mark Slow & Correct
                 df.loc[df['question_id'] == q_id, 'correct_but_slow'] = True
                 current_correct_but_slow = True # For diagnosis function

        # D. Call Detailed Diagnosis Function for the current question (using flags from original df)
        # We need to pass the potentially updated flags to the diagnosis function
        # Re-fetch the row from the original df to ensure all flags are current
        try:
            current_question_data = df.loc[df['question_id'] == q_id].iloc[0].to_dict()
        except IndexError:
            # Should not happen if q_id came from df_filtered, but safety check
            print(f"警告: 無法在原始 df 中找到過濾後的題目 ID {q_id} 以生成詳細診斷。")
            continue

        # Add the explicitly calculated classification/flags for the diagnosis function
        # The flags might not have been updated in the original df row fetched above yet
        current_question_data['error_classification'] = classification # Use the one calculated in this loop iteration
        current_question_data['is_slow'] = is_slow_flag # Use pre-calculated flag
        current_question_data['special_focus_error'] = is_sfe # Use flag calculated here
        current_question_data['suspiciously_fast_correct'] = current_suspiciously_fast_correct # Use flag calculated here
        # Note: 'correct_but_slow' flag is already updated in df, so it should be correct in current_question_data

        detailed_diagnosis_result = get_detailed_diagnosis_v(current_question_data)

        # Store the detailed diagnosis if it's problematic
        if detailed_diagnosis_result['is_problematic']:
            detailed_diagnoses_list.append(detailed_diagnosis_result)
            # Optionally, store main diagnosis text back into the main df for quick view
            df.loc[df['question_id'] == q_id, 'detailed_diagnosis'] = detailed_diagnosis_result['diagnosis_text']
            df.loc[df['question_id'] == q_id, 'detailed_action'] = detailed_diagnosis_result['action_text']
            df.loc[df['question_id'] == q_id, 'detailed_reflection'] = detailed_diagnosis_result['reflection_prompt']
            df.loc[df['question_id'] == q_id, 'detailed_evidence'] = detailed_diagnosis_result['second_level_evidence_prompt']

    # --- 5. Pattern Observation & Carelessness --- (Note: Chapter 4 is reference only)
    # Identify early fast questions (absolute time < 1.0 min)
    early_fast_questions_df = df[
        (df['question_position'] <= first_third_pos_limit) &
        (df['question_time'] < EARLY_FAST_TIME_THRESHOLD) &
        (~df['is_invalid']) # Exclude invalid
    ]
    early_fast_q_ids = early_fast_questions_df['question_id'].tolist()

    # Calculate Carelessness Issue Rate (using is_relatively_fast from Ch3)
    # Count on filtered data using the flag updated in the main df
    filtered_q_ids = df_filtered['question_id'].tolist()
    num_relatively_fast_total_v = df.loc[df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'], 'is_relatively_fast'].sum()
    num_relatively_fast_incorrect_v = df.loc[df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'] & ~df['is_correct'], 'is_relatively_fast'].sum()
    fast_wrong_rate_v = safe_divide(num_relatively_fast_incorrect_v, num_relatively_fast_total_v)
    carelessness_issue_v = fast_wrong_rate_v > CARELESSNESS_RATE_THRESHOLD_V

    # Identify questions flagged as 'Fast & Wrong' for Carelessness report
    fast_wrong_q_ids_v = df.loc[
        df['question_id'].isin(filtered_q_ids) & # Must be a valid question
        (df['error_classification'] == 'Fast & Wrong'),
        'question_id'
    ].tolist()

    # --- 6. Foundational Skill Override (on filtered data) ---
    skill_override_details_v = {}
    exempted_skills_v = set()
    skill_stats_v = pd.DataFrame() # Initialize empty

    if 'question_fundamental_skill' in df_filtered.columns and not df_filtered['question_fundamental_skill'].isnull().all():
        skill_stats_agg = df_filtered.groupby('question_fundamental_skill').agg(
            num_total_skill=('question_id', 'count'),
            num_errors_skill=('is_correct', lambda x: (x == False).sum()),
            # Calculate correct & not slow based on 'is_slow' flag
            num_correct_not_slow=('question_id', lambda x: (
                (df_filtered.loc[x.index, 'is_correct'] == True) &
                (df_filtered.loc[x.index, 'is_slow'] == False)
                 ).sum())
        ).reset_index()

        skill_stats_agg['error_rate_skill'] = skill_stats_agg.apply(
             lambda row: safe_divide(row['num_errors_skill'], row['num_total_skill']), axis=1
        )
        skill_stats_agg['override_triggered'] = skill_stats_agg['error_rate_skill'] > SKILL_OVERRIDE_ERROR_RATE_THRESHOLD_V

        # Store override details
        for _, row in skill_stats_agg[skill_stats_agg['override_triggered']].iterrows():
            skill_override_details_v[row['question_fundamental_skill']] = True # Just mark as triggered

        # Determine exempted skills
        exempted_skills_v = set(skill_stats_agg[skill_stats_agg['num_correct_not_slow'] > EXEMPTION_THRESHOLD_V]['question_fundamental_skill'].tolist())
        skill_stats_v = skill_stats_agg # Assign for later use in summary
    else:
        print("警告：無法按技能分組進行覆蓋規則和豁免分析。")

    # --- 7. Practice Planning & Recommendations ---
    recommendations_by_skill = defaultdict(list)
    processed_override_skills_v = set()

    # Identify trigger questions (incorrect or correct_but_slow)
    trigger_indices_filtered = df_filtered[
        (~df_filtered['is_correct']) | df_filtered['correct_but_slow'] # Use correct_but_slow flag from Ch3
    ].index
    all_trigger_skills_v = set(df_filtered.loc[trigger_indices_filtered, 'question_fundamental_skill']) | set(skill_override_details_v.keys())

    for skill in all_trigger_skills_v:
        if not isinstance(skill, str) or not skill: continue # Skip invalid skills

        # Macro Recommendation Check
        if skill in skill_override_details_v and skill not in processed_override_skills_v:
            macro_rec = f"針對 [{skill}] 技能，由於整體錯誤率偏高 (>50%)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
            recommendations_by_skill[skill].append({'type': 'macro', 'text': macro_rec, 'priority': 1})
            processed_override_skills_v.add(skill)
            continue # Skip individual recs if macro applies

        # Exemption Check (only if no macro rec)
        if skill in exempted_skills_v:
            if not recommendations_by_skill.get(skill): # Add only if no other recs exist yet
                 recommendations_by_skill[skill].append({'type': 'exemption', 'text': f"技能 [{skill}] 表現穩定，可暫緩練習。", 'priority': 99})
            continue # Skip individual recs if exempted

        # Individual Recommendation Generation
        skill_trigger_indices_filtered = df_filtered[
            (df_filtered['question_fundamental_skill'] == skill) &
            ((~df_filtered['is_correct']) | df_filtered['correct_but_slow'])
        ].index

        processed_q_ids_for_skill = set()
        for idx in skill_trigger_indices_filtered:
            question = df_filtered.loc[idx]
            q_id = question['question_id']
            if q_id in processed_q_ids_for_skill: continue

            difficulty = question['question_difficulty']
            q_time = question['question_time']
            q_type = question['question_type']
            is_slow_flag = question['is_slow'] # Correct but slow OR Slow & Wrong
            is_correct_flag = question['is_correct']

            # Fetch diagnostics from original df
            try:
                 question_diagnostics = df.loc[df['question_id'] == q_id].iloc[0]
                 error_class = question_diagnostics['error_classification']
                 is_sfe_flag = question_diagnostics['special_focus_error']
            except IndexError: error_class, is_sfe_flag = "未知", False

            # Calculate Y and Z
            practice_difficulty_y = map_difficulty_to_label(difficulty)
            practice_time_z = calculate_practice_time_v(q_time, is_slow_flag, q_type)
            target_time_disp = TARGET_PRACTICE_TIME_CR if q_type == 'CR' else TARGET_PRACTICE_TIME_RC

            # Build recommendation text
            trigger_reason, priority = "", 5
            if not is_correct_flag:
                trigger_reason = f"基於錯誤題目 (ID: {q_id}, 分類: {error_class})"
                if is_sfe_flag: trigger_reason += " **基礎掌握不穩**"; priority = 2
                else: priority = 3
            else: # Must be correct_but_slow
                 trigger_reason = f"基於正確但超時題目 (ID: {q_id})"
                 priority = 4

            rec_text = f"{trigger_reason}: 建議練習 [{practice_difficulty_y}] 難度題目，起始練習限時建議為 [{practice_time_z:.1f}] 分鐘。(最終目標時間：{q_type} {target_time_disp:.1f}分鐘)。"
            if practice_time_z - target_time_disp > Z_TIME_INCREASE_WARNING_THRESHOLD:
                 rec_text += " **需加大練習量以確保逐步限時有效**"

            recommendations_by_skill[skill].append({
                'type': 'individual', 'text': rec_text, 'priority': priority,
                'is_sfe': is_sfe_flag, 'q_id': q_id
            })
            processed_q_ids_for_skill.add(q_id)

    # Final Assembly of Recommendations List
    final_recommendations_list_v = []
    processed_final_skills_v = set()

    # Add exemptions first
    for skill in exempted_skills_v:
        if not isinstance(skill, str) or not skill: continue
        if skill not in processed_override_skills_v and not any(r['type'] == 'individual' for r in recommendations_by_skill.get(skill, [])):
            exemption_rec = next((r for r in recommendations_by_skill.get(skill, []) if r['type'] == 'exemption'), None)
            if exemption_rec:
                final_recommendations_list_v.append({'skill': skill, 'text': exemption_rec['text'], 'priority': exemption_rec['priority']})
                processed_final_skills_v.add(skill)

    # Add active recommendations
    valid_skill_keys_v = [k for k in recommendations_by_skill.keys() if isinstance(k, str) and k]
    sorted_skills_v = sorted(valid_skill_keys_v)

    for skill in sorted_skills_v:
        if skill in processed_final_skills_v: continue
        active_recs = [rec for rec in recommendations_by_skill.get(skill, []) if rec['type'] != 'exemption']
        if not active_recs: continue

        active_recs.sort(key=lambda x: x.get('priority', 5))
        combined_skill_rec_text = f"--- 技能: {skill} ---"
        for rec in active_recs:
            combined_skill_rec_text += f"\n- {rec['text']}"

        overall_priority = min(rec.get('priority', 5) for rec in active_recs)
        final_recommendations_list_v.append({'skill': skill, 'text': combined_skill_rec_text, 'priority': overall_priority})
        processed_final_skills_v.add(skill)

    final_recommendations_list_v.sort(key=lambda x: x['priority'])

    # --- 8. Diagnostic Summary Generation ---
    def generate_report_v(df_full, df_filt, time_p, time_d, cr_thresh, get_rc_target, rc_details, inv_ids, err_rate_diff_type, err_rate_skl, reading_barrier, long_read_groups, early_fast_ids, careless_flg, fast_wrong_rate_val, fast_wrong_ids_list, override_details, final_recs, detailed_diagnoses):
        """Generates the full text report based on analysis results."""
        summary = []
        summary.append("========== GMAT Verbal 診斷報告 ==========")

        # Chapter 1: Overall Time Strategy
        summary.append("\n**1. 整體時間策略與作答節奏**")
        time_pressure_desc = "時間壓力顯著 (剩餘時間 < 1 分鐘)" if time_p else "時間相對充裕"
        summary.append(f"- **整體時間壓力:** {time_pressure_desc} (總時間差 {time_d:.1f} 分鐘)。")
        if inv_ids:
            invalid_ids_str = ', '.join(map(str, sorted(inv_ids)))
            summary.append(f"- **結尾作答分析:** 測驗末尾存在 {len(inv_ids)} 題作答過快或疑似放棄 (題目 ID: {invalid_ids_str})，已被標記為 **無效數據**。這可能影響了最終部分題目的有效性，建議檢查結尾時間分配策略。")
        else:
            summary.append("- **結尾作答分析:** 未檢測到明顯的因時間壓力導致的末尾搶答/無效作答現象。")
        summary.append(f"- **超時標準:** CR 單題超時閾值設為 {cr_thresh:.1f} 分鐘。RC 題組目標時間根據題數調整 (如 3 題目標 {get_rc_target(3):.0f} 分鐘, 4 題目標 {get_rc_target(4):.0f} 分鐘)。")
        summary.append("- **疲勞提醒:** Verbal 部分疲勞效應普遍，建議考慮考試策略安排（如將 Verbal 置前）或考前進行閱讀熱身。")

        # Chapter 2: Performance Overview
        summary.append("\n**2. 表現概覽 (基於有效數據)**")
        summary.append("- **難度區間表現:**")
        total_by_difficulty_type = df_filt.groupby(['difficulty_label', 'question_type']).size().unstack(fill_value=0)
        errors_by_difficulty_type = df_filt[~df_filt['is_correct']].groupby(['difficulty_label', 'question_type']).size().unstack(fill_value=0)
        if not err_rate_diff_type.empty:
            for level in ["低難度 (Low) / 505+", "中難度 (Mid) / 555+", "中難度 (Mid) / 605+", "中難度 (Mid) / 655+", "高難度 (High) / 705+", "高難度 (High) / 805+", "極高難度 (Very High) / 805+", "未知難度"]:
                if level in err_rate_diff_type.index:
                    rates = err_rate_diff_type.loc[level]
                    total_counts = total_by_difficulty_type.loc[level]
                    desc = f"  - {level}: "
                    type_descs = []
                    if 'CR' in rates.index and total_counts.get('CR', 0) > 0:
                        type_descs.append(f"CR {rates.get('CR', 0):.1%} ({errors_by_difficulty_type.loc[level].get('CR', 0)}/{total_counts.get('CR', 0)})")
                    if 'RC' in rates.index and total_counts.get('RC', 0) > 0:
                         type_descs.append(f"RC {rates.get('RC', 0):.1%} ({errors_by_difficulty_type.loc[level].get('RC', 0)}/{total_counts.get('RC', 0)})")
                    if type_descs: summary.append(desc + ", ".join(type_descs))
        else: summary.append("  - 未能按難度區間分析錯誤率 (數據不足)。")

        summary.append("- **相對弱項技能 (按錯誤率排序):**")
        total_by_skill = df_filt.groupby('question_fundamental_skill').size()
        errors_by_skill = df_filt[~df_filt['is_correct']].groupby('question_fundamental_skill').size()
        if not err_rate_skl.empty:
            shown_skills = 0
            for skill, rate in err_rate_skl.items():
                if shown_skills < 5 and rate > 0: # Show top 5 with errors
                     override_marker = " *(需優先鞏固)*" if skill in override_details else ""
                     total_q_skill = total_by_skill.get(skill, 0)
                     error_q_skill = errors_by_skill.get(skill, 0)
                     summary.append(f"  - {skill}: {rate:.1%} ({error_q_skill}/{total_q_skill}){override_marker}")
                     shown_skills += 1
                elif shown_skills == 0 and rate == 0: # If top skill has 0% error rate
                    summary.append("  - 整體技能錯誤率較低。")
                    break
            if shown_skills == 0 and not any(err_rate_skl > 0): # Handle case where all skills have 0 errors
                 summary.append("  - 所有技能均無錯誤記錄。")
        else: summary.append("  - 未能按技能分析錯誤率 (數據不足或技能信息缺失)。")

        if rc_details: # Only comment if RC groups exist
            if reading_barrier:
                 groups_str = ', '.join(map(str, sorted(long_read_groups)))
                 summary.append(f"- **RC 閱讀時間初步評估:** 檢測到部分 RC 題組 (ID: {groups_str}) 的估算閱讀時間 **偏長**。這可能提示在基礎閱讀理解（詞彙、長難句、篇章把握）或閱讀策略上存在提升空間，建議結合第三/七章的具體分析和練習建議。")
            else:
                 summary.append("- **RC 閱讀時間初步評估:** 未發現明顯的閱讀時間過長問題。個案分析請參考第三/七章。")

        # Chapter 3: Core Problem Diagnosis (REWRITTEN for detailed per-question output)
        summary.append("\n**3. 核心問題診斷 (逐題分析)**")
        if detailed_diagnoses:
            # Group by RC group ID for better readability
            rc_grouped_diagnoses = defaultdict(list)
            cr_diagnoses = []
            other_diagnoses = []

            for diag in detailed_diagnoses:
                if diag['question_type'] == 'RC' and diag['rc_group_id'] is not None and pd.notna(diag['rc_group_id']):
                    rc_grouped_diagnoses[int(diag['rc_group_id'])].append(diag)
                elif diag['question_type'] == 'CR':
                    cr_diagnoses.append(diag)
                else: # Should not happen with current types, but good fallback
                    other_diagnoses.append(diag)

            # Sort diagnoses within each category
            cr_diagnoses.sort(key=lambda x: x['question_id'])
            for group_id in rc_grouped_diagnoses:
                rc_grouped_diagnoses[group_id].sort(key=lambda x: x['question_id'])
            other_diagnoses.sort(key=lambda x: x['question_id'])

            if cr_diagnoses:
                 summary.append("\n*--- CR 題目診斷 ---*")
                 for diag in cr_diagnoses:
                      summary.append(f"  - **Q{diag['question_id']}:** {diag['diagnosis_text']}")
                      summary.append(f"    *建議行動:* {diag['action_text']}")

            # Sort RC groups by their first question ID for consistent order
            sorted_rc_group_ids = sorted(rc_grouped_diagnoses.keys(), key=lambda gid: min(d['question_id'] for d in rc_grouped_diagnoses[gid]))

            for group_id in sorted_rc_group_ids:
                summary.append(f"\n*--- RC 題組 {group_id} 診斷 ---*")
                for diag in rc_grouped_diagnoses[group_id]:
                     summary.append(f"  - **Q{diag['question_id']}:** {diag['diagnosis_text']}")
                     summary.append(f"    *建議行動:* {diag['action_text']}")

            if other_diagnoses:
                 summary.append("\n*--- 其他類型題目診斷 ---*")
                 for diag in other_diagnoses:
                      summary.append(f"  - **Q{diag['question_id']}:** {diag['diagnosis_text']}")
                      summary.append(f"    *建議行動:* {diag['action_text']}")

            summary.append("\n(詳細的反思指引和二級證據查找建議見第七章)")

        elif not df_filt.empty:
            summary.append("- 本次測驗未發現需要特別關注的核心問題（如錯題、慢題等）。")
        else:
             summary.append("- 無有效數據進行核心問題診斷。")

        # Chapter 4: Pattern Observation (REWRITTEN to include fast_wrong IDs)
        summary.append("\n**4. 特殊模式觀察**")
        if early_fast_ids:
            early_ids_str_v = ', '.join(map(str, sorted(early_fast_ids)))
            summary.append(f"- **測驗前期作答:** 開始階段存在 **{len(early_fast_ids)} 題** 作答速度 (<1分鐘) **明顯偏快** (ID: {early_ids_str_v})。建議注意 **保持穩定的答題節奏**，避免潛在 'flag for review' 風險。")
        else:
            summary.append("- **測驗前期作答:** 未發現在測驗初期作答明顯過快的情況。")

        # Use the passed fast_wrong_ids_list
        if careless_flg:
            fw_ids_str = f" (涉及題目 ID: {', '.join(map(str, sorted(fast_wrong_ids_list)))})" if fast_wrong_ids_list else ""
            summary.append(f"- **粗心問題評估:** 分析顯示，「相對快且錯」的比例 ({fast_wrong_rate_val:.1%}) **偏高** (>{CARELESSNESS_RATE_THRESHOLD_V:.0%}){fw_ids_str}。提示可能需 **關注答題仔細程度**，減少因追求速度導致的失誤。請重點回顧這些快錯題目的思考過程（見第七章反思指引）。")
        elif df_full['is_relatively_fast'].sum() > 0: # Check if any question was relatively fast
             summary.append(f"- **粗心問題評估:** 「相對快且錯」比例 ({fast_wrong_rate_val:.1%}) 在正常範圍內。")
        else:
             summary.append("- **粗心問題評估:** 未能評估（無作答相對較快的題目）。")

        # Chapter 5: Foundational Skill Consolidation
        summary.append("\n**5. 基礎鞏固提示**")
        triggered_override_skills_list_v = list(override_details.keys())
        if triggered_override_skills_list_v:
            skills_str_v = ', '.join(triggered_override_skills_list_v)
            summary.append(f"- **優先系統鞏固:** 對於 **[{skills_str_v}]** 這些核心技能，因整體錯誤率超過 50%，建議 **優先進行系統性基礎鞏固**，而非僅針對個別錯題練習。詳見練習計劃。")
        else:
            summary.append("- **優先系統鞏固:** 未發現錯誤率超過 50% 的核心技能。練習建議將主要基於個案分析。")

        # Chapter 6: Detailed Practice Plan
        summary.append("\n**6. 詳細練習計劃**")
        if final_recs:
            summary.append("根據以上分析，建議您針對以下技能進行練習：\n")
            for rec in final_recs:
                summary.append(f"\n{rec['text']}")
        elif not df_filt.empty:
            summary.append("- 本次分析未生成具體的練習建議（可能因表現穩定或均被豁免）。")
        else:
             summary.append("- 無有效數據生成練習建議。")

        # Chapter 7: Next Steps and Reflection Guidance (REWRITTEN for detailed per-question output)
        summary.append("\n\n**7. 後續行動與反思指引 (逐題)**")
        summary.append("針對第三章診斷出的問題，請結合以下具體指引進行反思和二級證據查找：")

        if detailed_diagnoses:
             # Use the same grouping and sorting as in Chapter 3
            rc_grouped_diagnoses_ch7 = defaultdict(list)
            cr_diagnoses_ch7 = []
            other_diagnoses_ch7 = []

            for diag in detailed_diagnoses:
                if diag['question_type'] == 'RC' and diag['rc_group_id'] is not None and pd.notna(diag['rc_group_id']):
                    rc_grouped_diagnoses_ch7[int(diag['rc_group_id'])].append(diag)
                elif diag['question_type'] == 'CR':
                    cr_diagnoses_ch7.append(diag)
                else:
                    other_diagnoses_ch7.append(diag)

            cr_diagnoses_ch7.sort(key=lambda x: x['question_id'])
            for group_id in rc_grouped_diagnoses_ch7:
                rc_grouped_diagnoses_ch7[group_id].sort(key=lambda x: x['question_id'])
            sorted_rc_group_ids_ch7 = sorted(rc_grouped_diagnoses_ch7.keys(), key=lambda gid: min(d['question_id'] for d in rc_grouped_diagnoses_ch7[gid]))
            other_diagnoses_ch7.sort(key=lambda x: x['question_id'])

            summary.append("\n*--- 引導反思 (逐題) ---*")
            if cr_diagnoses_ch7:
                 for diag in cr_diagnoses_ch7: summary.append(f"- {diag['reflection_prompt']}")
            for group_id in sorted_rc_group_ids_ch7:
                 for diag in rc_grouped_diagnoses_ch7[group_id]: summary.append(f"- {diag['reflection_prompt']}")
            if other_diagnoses_ch7:
                 for diag in other_diagnoses_ch7: summary.append(f"- {diag['reflection_prompt']}")

            summary.append("\n*--- 二級證據參考建議 (逐題) ---*")
            summary.append("  *觸發時機:* 無法準確回憶錯誤原因/技能弱點，或需客觀數據確認模式時。")
            summary.append("  *建議行動:* 查看近期（2-4週）練習記錄，結合以下針對性方向整理相關錯題，歸納問題：")
            if cr_diagnoses_ch7:
                 for diag in cr_diagnoses_ch7: summary.append(f"- {diag['second_level_evidence_prompt']}")
            for group_id in sorted_rc_group_ids_ch7:
                 for diag in rc_grouped_diagnoses_ch7[group_id]: summary.append(f"- {diag['second_level_evidence_prompt']}")
            if other_diagnoses_ch7:
                 for diag in other_diagnoses_ch7: summary.append(f"- {diag['second_level_evidence_prompt']}")

        else:
            summary.append("- 未發現需要詳細反思或查找二級證據的具體問題點。")

        # Qualitative Analysis Suggestion (Keep existing)
        summary.append("\n*--- 質化分析建議 ---*")
        summary.append("  - *觸發時機:* 對診斷報告指出的錯誤原因（特別是複雜邏輯/閱讀理解）感到困惑，或上述方法仍無法釐清根本問題時。")
        summary.append("  - *建議行動:* 提供 2-3 題相關類型題目的詳細解題思路（文字/錄音），以便與顧問深入分析癥結。")

        summary.append("\n========== 報告結束 ==========")
        return summary

    # --- Final Summary Generation and Saving ---
    # Prepare arguments for the new generate_report_v function
    summary_lines = generate_report_v(
        df_full=df,
        df_filt=df_filtered,
        time_p=time_pressure,
        time_d=time_diff,
        cr_thresh=overtime_threshold_cr,
        get_rc_target=get_rc_group_target_time,
        rc_details=rc_group_details,
        inv_ids=invalid_question_ids,
        err_rate_diff_type=error_rate_by_difficulty_type,
        err_rate_skl=error_rate_by_skill,
        reading_barrier=reading_comprehension_barrier_inquiry,
        long_read_groups=long_reading_time_groups,
        early_fast_ids=early_fast_q_ids,
        careless_flg=carelessness_issue_v,
        fast_wrong_rate_val=fast_wrong_rate_v,
        fast_wrong_ids_list=fast_wrong_q_ids_v, # Pass the list here
        override_details=skill_override_details_v,
        final_recs=final_recommendations_list_v,
        detailed_diagnoses=detailed_diagnoses_list # Pass the collected detailed diagnoses
    )

    # --- Combine DataFrame and Summary for Output ---
    summary_df_v = pd.DataFrame({'診斷報告與建議': summary_lines})
    spacer_data_v = {col: [None] * 3 for col in df.columns}
    spacer_df_v = pd.DataFrame(spacer_data_v)
    # Add new detailed columns to spacer if they exist in df
    for detail_col in ['detailed_diagnosis', 'detailed_action', 'detailed_reflection', 'detailed_evidence']:
        if detail_col in df.columns:
            spacer_data_v[detail_col] = [None] * 3
    spacer_df_v = pd.DataFrame(spacer_data_v)

    summary_df_aligned_v = pd.DataFrame(columns=df.columns)
    if df.columns[0] in summary_df_aligned_v.columns: summary_df_aligned_v[df.columns[0]] = summary_df_v['診斷報告與建議']
    else: summary_df_aligned_v.insert(0, df.columns[0], summary_df_v['診斷報告與建議'])
    final_df_v = pd.concat([df, spacer_df_v, summary_df_aligned_v], ignore_index=True)

    # --- Save Final Result ---
    try:
        final_df_v.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"\n分析完成，Verbal 診斷報告與建議已儲存至: {output_csv_path}")
    except Exception as e:
        print(f"\n錯誤：儲存 Verbal 結果至 CSV 檔案 '{output_csv_path}' 時發生錯誤: {e}")
        sys.exit(1)

# --- Command-Line Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='分析 GMAT Verbal 測驗數據並生成診斷報告 (基於 gmat-v-score-logic-dustin-v1.1.md)。',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'input_csv',
        help='輸入的 CSV 檔案路徑 (例如：testset-v.csv)。\n必須包含欄位: Question, Response Time (Minutes), Performance, Question Type, Fundamental Skills, V_b'
    )
    parser.add_argument(
        'output_csv',
        help='輸出的 CSV 檔案路徑 (例如：testset-v-analyzed.csv)。'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--force_time_pressure',
        action='store_true',
        help='強制將 time_pressure 設為 True。'
    )
    group.add_argument(
        '--force_no_time_pressure',
        action='store_true',
        help='強制將 time_pressure 設為 False。'
    )

    args = parser.parse_args()
    override_v = None
    if args.force_time_pressure: override_v = True
    elif args.force_no_time_pressure: override_v = False

    analyze_gmat_verbal_data(args.input_csv, args.output_csv, user_override_time_pressure=override_v) 