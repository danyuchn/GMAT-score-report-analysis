import pandas as pd
import math
import numpy as np
import argparse
import sys
from collections import defaultdict

# --- Configuration (Based on gmat-di-score-logic-dustin-v1.1.md) ---
MAX_ALLOWED_TIME_DI = 45.0
TOTAL_QUESTIONS_DI = 20 # Typical, but script will use actual count
TIME_PRESSURE_THRESHOLD_DI = 3.0 # time_diff <= 3 min means pressure

# Overtime thresholds (minutes)
OVERTIME_THRESHOLD_TPA_PRESSURE = 3.0
OVERTIME_THRESHOLD_TPA_NO_PRESSURE = 3.5
OVERTIME_THRESHOLD_GT_PRESSURE = 3.0
OVERTIME_THRESHOLD_GT_NO_PRESSURE = 3.5
OVERTIME_THRESHOLD_DS_PRESSURE = 2.0
OVERTIME_THRESHOLD_DS_NO_PRESSURE = 2.5

# MSR Group Target Time (minutes) - Assuming 3 questions per group default
MSR_GROUP_TARGET_TIME_PRESSURE = 6.0
MSR_GROUP_TARGET_TIME_NO_PRESSURE = 7.0

# MSR Individual Analysis Thresholds (minutes)
MSR_READING_THRESHOLD = 1.5
MSR_SINGLE_Q_THRESHOLD = 1.5

# Invalid Data Thresholds
INVALID_FRACTION = 1/3
INVALID_TIME_THRESHOLD = 1.0 # Less than 1.0 min in last third + pressure -> invalid

# Relative Speed Factors
RELATIVELY_FAST_FACTOR = 0.75 # For Fast & Wrong classification

# Pattern Observation Thresholds
EARLY_POSITION_LIMIT = 6
EARLY_FAST_TIME_THRESHOLD_ABS = 1.0
CARELESSNESS_RATE_THRESHOLD_DI = 0.25

# Override Rule Threshold
OVERRIDE_RATE_THRESHOLD = 0.50

# Recommendation Parameters
EXEMPTION_THRESHOLD_DI = 2 # num_correct_not_overtime > threshold
# Target times for Z calculation
TARGET_PRACTICE_TIME_DS = 2.0
TARGET_PRACTICE_TIME_TPA = 3.0
TARGET_PRACTICE_TIME_GT = 3.0
TARGET_PRACTICE_TIME_MSR = 2.0 # Single MSR question target
PRACTICE_TIME_SLOW_REDUCTION_DI = 0.5
Z_TIME_INCREASE_WARNING_THRESHOLD_DI = 2.0

# Math Related Keywords List (Chapter 3)
MATH_KEYWORDS = ["Rates", "Ratio", "Percent", "Equalities", "Inequalties", "Algebra", "Value", "Order", "Factor", "Counting", "Sets", "Probabilities", "Series", "Statistics"]

# --- Helper Functions ---

def map_difficulty_to_label_di(d):
    # Replicates the 6-level difficulty mapping from Chapter 2
    if d is None or pd.isna(d): return "未知難度"
    if d <= -1: return "低難度 (Low) / 505+"
    if -1 < d <= 0: return "中難度 (Mid) / 555+"
    if 0 < d <= 1: return "中難度 (Mid) / 605+"
    if 1 < d <= 1.5: return "中難度 (Mid) / 655+"
    if 1.5 < d <= 1.95: return "高難度 (High) / 705+"
    # Adjusted upper boundary based on DI doc example
    if 1.95 < d <= 2: return "高難度 (High) / 805+"
    if d > 2: return "極高難度 (Very High) / 805+"
    return "未知難度"

def floor_to_nearest_0_5_di(value):
    if value is None or pd.isna(value): return None
    return math.floor(value * 2) / 2

def safe_divide_di(numerator, denominator):
    if denominator is None or denominator == 0: return 0.0
    if numerator is None: return 0.0
    try:
        num = pd.to_numeric(numerator, errors='coerce')
        den = pd.to_numeric(denominator, errors='coerce')
        if pd.isna(num) or pd.isna(den) or den == 0: return 0.0
        return num / den
    except (ZeroDivisionError, TypeError, ValueError): return 0.0

def calculate_practice_time_di(question_time, is_slow, question_type):
    # Replicates Chapter 6 logic for calculating Z
    target_time_map = {
        'DS': TARGET_PRACTICE_TIME_DS,
        'TPA': TARGET_PRACTICE_TIME_TPA,
        'GT': TARGET_PRACTICE_TIME_GT,
        'MSR': TARGET_PRACTICE_TIME_MSR
    }
    target_time = target_time_map.get(question_type, 2.0) # Default target if type unknown
    base_time = question_time - PRACTICE_TIME_SLOW_REDUCTION_DI if is_slow else question_time
    z_raw = floor_to_nearest_0_5_di(base_time)
    if z_raw is None: return target_time
    z = max(z_raw, target_time)
    return z

# --- MSR Group Processing ---
def identify_and_process_msr_groups(df):
    """Identifies MSR groups, calculates group time and reading time."""
    msr_groups = []
    current_group_indices = []
    group_id_counter = 1
    df['msr_group_id'] = None
    df['group_total_time'] = None
    df['msr_reading_time'] = None # Calculated for the group, stored on first Q
    df['num_questions_in_group'] = None

    # Convert index to list to avoid potential issues with loc on non-unique indices if any
    df_indices = df.index.tolist()

    for i, index in enumerate(df_indices):
        # Use .loc for reliable access by index label
        row = df.loc[index]
        if row['question_type'] == 'MSR':
            current_group_indices.append(index)
        else:
            if current_group_indices:
                msr_groups.append(list(current_group_indices))
                group_id = group_id_counter
                df.loc[current_group_indices, 'msr_group_id'] = group_id
                df.loc[current_group_indices, 'num_questions_in_group'] = len(current_group_indices)
                group_id_counter += 1
                current_group_indices = []
    # Process the last group if the test ends with MSR
    if current_group_indices:
        msr_groups.append(list(current_group_indices))
        group_id = group_id_counter
        df.loc[current_group_indices, 'msr_group_id'] = group_id
        df.loc[current_group_indices, 'num_questions_in_group'] = len(current_group_indices)

    # Calculate group times and estimated reading times
    msr_group_details = {}
    for indices in msr_groups:
        if not indices: continue
        group_df = df.loc[indices]
        group_id = group_df['msr_group_id'].iloc[0]
        group_total_time = group_df['question_time'].sum()
        num_questions = len(indices)
        df.loc[indices, 'group_total_time'] = group_total_time

        # Calculate MSR reading time (Chapter 0 logic)
        reading_time = None
        if num_questions >= 3: # Only calculate if 3 or more questions
            # Ensure we access by position within the group_df (iloc)
            q1_time = group_df['question_time'].iloc[0]
            q2_time = group_df['question_time'].iloc[1]
            q3_time = group_df['question_time'].iloc[2]
            if pd.notna(q1_time) and pd.notna(q2_time) and pd.notna(q3_time):
                 reading_time = q1_time - (q2_time + q3_time) / 2
                 # Reading time cannot be negative conceptually, but calculation might yield it. Keep as is for checks.
        # Store on first question using its original index
        df.loc[indices[0], 'msr_reading_time'] = reading_time

        msr_group_details[group_id] = {
            'total_time': group_total_time,
            'num_questions': num_questions,
            'reading_time': reading_time,
            'indices': indices # Store original indices
        }

    return df, msr_group_details

# --- NEW: Detailed Diagnosis Function (Based on Chapter 3 of MD) ---
def get_detailed_diagnosis(q_type, domain, is_correct, is_slow, is_relatively_fast, is_msr_reading_long=False, is_msr_single_q_long=False):
    """
    Generates detailed diagnosis text and suggested actions based on question attributes,
    following the logic in gmat-di-score-logic-dustin-v1.1.md Chapter 3.
    """
    diagnosis = "N/A"
    action = "N/A"
    math_keywords_prompt = f"(參考考點列表: {', '.join(MATH_KEYWORDS)})"
    generic_recall_action = "請學生回憶卡關點/錯誤原因/效率瓶頸。"
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
    specific_secondary_evidence = f"若無法回憶/確認，查看近期(2-4週) **{time_correctness_category_desc}** 的 **{q_type} ({domain})** 題目記錄(樣本>5-10題)。歸納模式/障礙/考點。"
    if q_type == 'MSR':
         if is_msr_reading_long:
            specific_secondary_evidence += " (特別關注閱讀材料類型和整合障礙)"
         if is_msr_single_q_long:
            specific_secondary_evidence += " (特別關注讀題/定位/選項環節耗時)"


    # --- MSR Specific Time Checks (Handled first as they are independent) ---
    msr_diagnosis_parts = []
    msr_action_parts = []
    if q_type == 'MSR':
        if is_msr_reading_long:
            msr_diagnosis_parts.append("MSR 題組閱讀時間偏長。")
            msr_action_parts.append(f"請回憶源資料吸收障礙是（單字、句構、領域、圖表、跨分頁整合資訊）。{specific_secondary_evidence}")
        if is_msr_single_q_long:
            msr_diagnosis_parts.append("MSR 題組中該問題回答時間偏長。")
            msr_action_parts.append(f"請回憶障礙是（讀題、定位、選項）。{specific_secondary_evidence}")

    # --- General Diagnosis based on Time/Correctness ---
    time_correctness_diagnosis = "N/A"
    time_correctness_action = "N/A"

    if is_correct:
        if is_slow:
            time_correctness_diagnosis = "效率瓶頸可能點："
            time_correctness_action = generic_recall_action + " " + specific_secondary_evidence
            if domain == 'Math Related':
                if q_type in ['DS', 'TPA', 'GT']: time_correctness_diagnosis += " 文字理解 / 公式導出 / 計算 / 圖表解讀 / 數據截取。"
                elif q_type == 'MSR': time_correctness_diagnosis += " 跨分頁信息整合 / 文字理解 / 圖表解讀 / 公式 / 計算。"
            else: # Non-Math Related
                if q_type in ['DS', 'TPA']: time_correctness_diagnosis += " 文字理解 / 題目內在邏輯推理。"
                elif q_type == 'GT': time_correctness_diagnosis += " 圖表解讀 / 文字理解 / 信息提取。"
                elif q_type == 'MSR': time_correctness_diagnosis += " 跨分頁信息整合 / 文字理解 / 圖表解讀 / 邏輯推斷。"
                 # Slow & Correct Non-Math doesn't require specifying sub-types per MD
        elif is_relatively_fast:
            time_correctness_diagnosis = "作答相對較快且正確。"
            time_correctness_action = "提醒：注意避免潛在粗心或被標記 (flag for review)。若在測驗後段，確認是否因時間壓力倉促作答。"
        else: # Normal time and correct
            time_correctness_diagnosis = "正常時間完成且正確。"
            time_correctness_action = "無需特別行動。"
    else: # Incorrect
        if is_slow:
            time_correctness_diagnosis = "慢而錯可能原因："
            time_correctness_action = generic_recall_action + " " + specific_secondary_evidence
            if domain == 'Math Related':
                if q_type in ['DS', 'TPA', 'GT']: time_correctness_diagnosis += " 1. 文字理解障礙 (細分：單詞/句構/術語); 2. 公式導出障礙; 3. 計算障礙; 4. 圖表/數據障礙 (GT)。"
                elif q_type == 'MSR': time_correctness_diagnosis += " 跨分頁信息整合 / 文字理解 / 圖表解讀 / 公式 / 計算等。"
                time_correctness_action += f" 需學生識別數學相關考點 {math_keywords_prompt}。"
            else: # Non-Math Related
                if q_type in ['DS', 'TPA']: time_correctness_diagnosis += " 1. 文字理解障礙 (細分：單詞/句構/題意); 2. 題目內在邏輯推理障礙。"
                elif q_type == 'GT': time_correctness_diagnosis += " 圖表解讀 / 文字理解 / 信息提取/推斷錯誤。"
                elif q_type == 'MSR': time_correctness_diagnosis += " 跨分頁信息整合 / 文字理解 / 圖表解讀 / 邏輯推斷 / 題型考點障礙。"
                time_correctness_action += " 請學生回憶是文字理解還是邏輯判斷問題。"
                if q_type == 'MSR': time_correctness_action += " (邏輯推斷是否關聯 main idea/supporting idea/inference 等概念？)"
        else: # Normal or Fast & Wrong
            prefix = "快而錯" if is_relatively_fast else "正常時間做錯"
            time_correctness_diagnosis = f"{prefix} 可能原因："
            time_correctness_action = generic_recall_action # Start with recall
            if domain == 'Math Related':
                time_correctness_diagnosis += " 相關數學考點不熟或應用錯誤。"
                time_correctness_action += f" 需學生識別數學相關考點 {math_keywords_prompt}。" + " " + specific_secondary_evidence
            else: # Non-Math Related
                time_correctness_diagnosis += " 1. 文字理解疏漏/錯誤; 2. 題目內在邏輯應用錯誤。"
                # Strongly recommend secondary + qualitative for Non-Math Normal/Fast wrong
                time_correctness_action += " " + specific_secondary_evidence + " " + generic_qualitative_analysis
                if q_type == 'MSR': time_correctness_action += " (分析是否與 main idea/supporting idea/inference 相關？)"


    # --- Combine MSR-specific and general diagnosis ---
    final_diagnosis_parts = msr_diagnosis_parts
    # Only add general diagnosis if it's not 'N/A' or 'Normal time and correct' (unless MSR had issues)
    if time_correctness_diagnosis not in ["N/A", "正常時間完成且正確。"] or msr_diagnosis_parts:
        if time_correctness_diagnosis != "N/A":
             final_diagnosis_parts.append(time_correctness_diagnosis)

    final_action_parts = msr_action_parts
    if time_correctness_action not in ["N/A", "無需特別行動。"] or msr_action_parts:
        if time_correctness_action != "N/A":
             final_action_parts.append(time_correctness_action)

    diagnosis = " ".join(final_diagnosis_parts) if final_diagnosis_parts else "N/A"
    action = " ".join(final_action_parts) if final_action_parts else "N/A"

    # Handle the case where only MSR time issue occurred on a correctly answered question
    if is_correct and diagnosis == "N/A" and (is_msr_reading_long or is_msr_single_q_long):
         diagnosis = "作答正確，但存在 MSR 特定時間問題。" # Placeholder, actual issue described above
         # Action part is already captured in msr_action_parts

    # If no issues at all were found
    if not final_diagnosis_parts and not final_action_parts:
        diagnosis = "表現正常。"
        action = "無需特別行動。"


    return diagnosis.strip(), action.strip()


# --- Main Analysis Function ---

def analyze_gmat_di_data(input_csv_path, output_csv_path, user_override_time_pressure=None):
    """
    Analyzes GMAT DI performance data based on gmat-di-score-logic-dustin-v1.1.md.
    Outputs a CSV with diagnostics and a summary report.
    """
    # Define required original columns for DI based on the ACTUAL CSV header
    required_original_cols_di = [
        'Question', 'Response Time (Minutes)', 'Performance', 'Content Domain',
        'Question Type', 'DI_b'
        # 'Fundamental Skills' is ignored, 'question_position' is generated
    ]
    try:
        # Read CSV with error handling and potential encoding fallback
        # Read all columns first to validate presence, handling extra commas
        try:
             df_all_cols = pd.read_csv(input_csv_path, encoding='utf-8', dtype={'Question': str}) # Use actual ID col name
        except UnicodeDecodeError:
            try:
                df_all_cols = pd.read_csv(input_csv_path, encoding='gbk', dtype={'Question': str})
            except UnicodeDecodeError:
                 df_all_cols = pd.read_csv(input_csv_path, encoding='cp950', dtype={'Question': str})
        except FileNotFoundError:
            print(f"錯誤：找不到輸入文件 '{input_csv_path}'")
            sys.exit(1)
        except Exception as e:
            print(f"讀取CSV標頭時發生未預期的錯誤: {e}")
            sys.exit(1)

        # Check if all required columns exist in the file using ACTUAL names
        missing_cols_in_file = [col for col in required_original_cols_di if col not in df_all_cols.columns]
        if missing_cols_in_file:
             print(f"錯誤：輸入 CSV 文件 '{input_csv_path}' 缺少必要的欄位: {', '.join(missing_cols_in_file)}。請確保文件包含所有必需欄位。")
             sys.exit(1)

        # Now read ONLY the required columns using ACTUAL names
        try:
             df = pd.read_csv(input_csv_path, encoding='utf-8', usecols=required_original_cols_di, dtype={'Question': str})
        except UnicodeDecodeError:
             try:
                 df = pd.read_csv(input_csv_path, encoding='gbk', usecols=required_original_cols_di, dtype={'Question': str})
             except UnicodeDecodeError:
                  df = pd.read_csv(input_csv_path, encoding='cp950', usecols=required_original_cols_di, dtype={'Question': str})

    except ValueError as ve:
         print(f"讀取指定欄位時出錯，可能檔案格式不符或欄位問題. Error: {ve}")
         sys.exit(1)
    except Exception as e:
        print(f"讀取或驗證 CSV 時發生錯誤: {e}")
        sys.exit(1)

    # --- 0. Prepare Initial Data & Derived Metrics ---
    # Rename columns from CSV names to internal script names
    df.rename(columns={
        'Question': 'question_id',
        'Response Time (Minutes)': 'question_time',
        'Performance': 'performance_raw', # Temp name
        'Content Domain': 'content_domain',
        'Question Type': 'question_type_raw', # Temp name
        'DI_b': 'question_difficulty'
    }, inplace=True)

    # Generate question_position
    df['question_position'] = np.arange(1, len(df) + 1)


    # Basic Cleaning & Type Conversion (using renamed columns)
    df['question_time'] = pd.to_numeric(df['question_time'], errors='coerce')
    df['question_difficulty'] = pd.to_numeric(df['question_difficulty'], errors='coerce')
    # question_position is already numeric

    # Convert performance_raw to is_correct
    if df['performance_raw'].dtype == 'object':
        df['is_correct'] = df['performance_raw'].astype(str).str.strip().str.lower() == 'correct' # Changed from 'true' to 'correct'
    elif pd.api.types.is_numeric_dtype(df['performance_raw']):
         df['is_correct'] = df['performance_raw'].astype(int) == 1 # Assuming 1 means correct
    else: # Fallback
        print("警告：\'Performance\' 欄位類型未知，嘗試轉換為布林值。")
        df['is_correct'] = df['performance_raw'].astype(bool)
    df.drop(columns=['performance_raw'], inplace=True) # Drop the temporary column

    # Standardize question_type from question_type_raw
    # Define mapping based on DI types if needed, or just clean
    # Example assumes direct use after cleaning for DI (DS, TPA, MSR, GT)
    df['question_type'] = df['question_type_raw'].astype(str).str.strip()
    # Convert known types like 'Data Sufficiency' etc. to abbreviations if they appear
    type_mapping_di = {
         'data sufficiency': 'DS',
         'two-part analysis': 'TPA',
         'multi-source reasoning': 'MSR',
         'graph and table': 'GT'
         # Add other potential full names if necessary
    }
    # Apply mapping robustly
    df['question_type'] = df['question_type'].str.lower().map(type_mapping_di).fillna(df['question_type'].str.upper())
    df.drop(columns=['question_type_raw'], inplace=True) # Drop the temporary column


    # Standardize content_domain (using internal names now)
    df['content_domain'] = df['content_domain'].astype(str).str.strip()
    # Ensure specific casing 'Math Related' / 'Non-Math Related'
    content_domain_mapping = {
        'math related': 'Math Related',
        'non-math related': 'Non-Math Related'
    }
    df['content_domain'] = df['content_domain'].str.lower().map(content_domain_mapping).fillna(df['content_domain'])


    # Validate standardized values
    valid_types = ['DS', 'TPA', 'MSR', 'GT']
    valid_domains = ['Math Related', 'Non-Math Related']
    # Use internal column names for checking now
    unknown_types_found = df[~df['question_type'].isin(valid_types)]['question_type'].unique()
    unknown_domains_found = df[~df['content_domain'].isin(valid_domains)]['content_domain'].unique()
    if len(unknown_types_found) > 0: print(f"警告：發現未知 Question Type: {list(unknown_types_found)}")
    if len(unknown_domains_found) > 0: print(f"警告：發現未知 Content Domain: {list(unknown_domains_found)}")

    # Drop rows with essential data missing (using internal column names)
    essential_cols_check = ['question_time', 'question_difficulty', 'question_position',
                           'question_id', 'is_correct', 'question_type', 'content_domain']
    initial_rows = len(df)
    df.dropna(subset=essential_cols_check, inplace=True)
    if initial_rows > len(df):
         print(f"警告：移除了 {initial_rows - len(df)} 行，因為包含無效或缺失的基礎值。")

    if df.empty:
        print("錯誤：數據清理後，無有效題目可供分析。")
        sys.exit(1)

    # Convert types after cleaning (position already int, id kept as string default)
    # df['question_id'] = df['question_id'].astype(str) # Keep as string
    # df['question_position'] = df['question_position'].astype(int) # Already int
    df = df.sort_values('question_position') # Ensure order

    total_test_time = df['question_time'].sum()
    total_number_of_questions = len(df)

    # Process MSR Groups (calculates group_total_time, msr_reading_time)
    df, msr_group_details = identify_and_process_msr_groups(df)

    # Calculate initial overall average time per type (before filtering)
    avg_time_per_type_initial = df.groupby('question_type')['question_time'].mean().to_dict()

    # Calculate initial max correct difficulty per combination (before filtering)
    max_correct_difficulty_per_comb_initial = df[df['is_correct']].groupby(
        ['question_type', 'content_domain']
    )['question_difficulty'].max().unstack(fill_value=-np.inf) # Use unstack for easier lookup

    # --- 1. Time Strategy & Validity ---
    time_diff = MAX_ALLOWED_TIME_DI - total_test_time
    time_pressure = time_diff <= TIME_PRESSURE_THRESHOLD_DI

    # Apply user override
    if user_override_time_pressure is not None:
        time_pressure = user_override_time_pressure
        print(f"用戶強制設定 time_pressure = {time_pressure}")

    # Set Overtime Thresholds based on time_pressure
    overtime_thresholds = {
        'TPA': OVERTIME_THRESHOLD_TPA_PRESSURE if time_pressure else OVERTIME_THRESHOLD_TPA_NO_PRESSURE,
        'GT': OVERTIME_THRESHOLD_GT_PRESSURE if time_pressure else OVERTIME_THRESHOLD_GT_NO_PRESSURE,
        'DS': OVERTIME_THRESHOLD_DS_PRESSURE if time_pressure else OVERTIME_THRESHOLD_DS_NO_PRESSURE,
    }
    msr_group_target = MSR_GROUP_TARGET_TIME_PRESSURE if time_pressure else MSR_GROUP_TARGET_TIME_NO_PRESSURE

    # Identify Invalid Data (Only if time_pressure is True)
    df['is_invalid'] = False
    invalid_question_ids_di = []
    if time_pressure:
        last_third_start_pos = math.ceil(total_number_of_questions * (1 - INVALID_FRACTION))
        # Check index existence before slicing
        last_third_indices = df[df['question_position'] > last_third_start_pos].index
        if not last_third_indices.empty:
             invalid_flags = df.loc[last_third_indices, 'question_time'] < INVALID_TIME_THRESHOLD
             df.loc[last_third_indices[invalid_flags], 'is_invalid'] = True
             invalid_question_ids_di = df.loc[last_third_indices[invalid_flags], 'question_id'].tolist()

    # Initialize diagnostic columns
    df['overtime'] = False
    df['msr_group_overtime'] = False # Specific flag for MSR group overtime
    df['is_slow'] = False # Combined slow flag
    df['difficulty_label'] = df['question_difficulty'].apply(map_difficulty_to_label_di)
    df['is_relatively_fast'] = False
    df['error_classification'] = 'N/A' # e.g., 'Slow & Wrong', 'Fast & Wrong'
    df['special_focus_error'] = False
    df['correct_but_slow'] = False
    df['msr_reading_time_long'] = False
    df['msr_single_q_time_long'] = False
    df['diagnosis_text'] = "N/A" # NEW Column for detailed diagnosis
    df['suggested_action'] = "N/A" # NEW Column for suggested action

    # Mark Overtime (including MSR group) - BEFORE filtering
    for index, row in df.iterrows():
        q_type = row['question_type']
        q_time = row['question_time']
        msr_group_id = row['msr_group_id']

        if q_type in overtime_thresholds:
            if q_time > overtime_thresholds[q_type]:
                df.loc[index, 'overtime'] = True
                df.loc[index, 'is_slow'] = True
        elif q_type == 'MSR' and pd.notna(msr_group_id):
            group_info = msr_group_details.get(msr_group_id)
            if group_info and group_info['total_time'] > msr_group_target:
                df.loc[index, 'msr_group_overtime'] = True
                df.loc[index, 'is_slow'] = True # Mark individual MSR q as slow if group is overtime

    # Create Filtered Data (excluding invalid)
    df_filtered = df[~df['is_invalid']].copy()

    if df_filtered.empty:
        print("警告：所有題目都被標記為無效，無法進行後續深入分析。")
        # Output minimal report (similar logic as in Verbal script)
        summary_lines = ["========== GMAT DI 診斷報告 ==========",
                         "\n**錯誤：** 所有題目均因時間壓力或結尾作答過快而被標記為無效，無法生成診斷報告。"]
        summary_df = pd.DataFrame({'診斷報告與建議': summary_lines})
        # Create spacer dynamically based on actual columns in df
        spacer_data = {col: [None] * 3 for col in df.columns}
        spacer_df = pd.DataFrame(spacer_data)
        summary_df_aligned = pd.DataFrame(columns=df.columns)
        # Use the first column of df for alignment
        first_col_name = df.columns[0]
        summary_df_aligned[first_col_name] = summary_df['診斷報告與建議']
        final_df = pd.concat([df, spacer_df, summary_df_aligned], ignore_index=True)
        try:
            final_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            print(f"已將包含無效標記的數據儲存至 {output_csv_path}")
        except Exception as e: print(f"儲存部分結果至CSV時發生錯誤: {e}")
        sys.exit(0)

    # Recalculate average times and max difficulties based on FILTERED data for analysis
    avg_time_per_type_filtered = df_filtered.groupby('question_type')['question_time'].mean().to_dict()
    max_correct_difficulty_per_comb = df_filtered[df_filtered['is_correct']].groupby(
         ['question_type', 'content_domain']
    )['question_difficulty'].max().unstack(fill_value=-np.inf)

    # --- 2. Multi-dimensional Analysis (on filtered data) ---
    # By Content Domain
    domain_stats = df_filtered.groupby('content_domain').agg(
        num_total=('question_id', 'count'),
        num_errors=('is_correct', lambda x: (x == False).sum()),
        num_overtime=('is_slow', 'sum') # Use is_slow as the overtime indicator here
    ).reindex(['Math Related', 'Non-Math Related'], fill_value=0) # Ensure both domains exist

    domain_stats['error_rate'] = domain_stats.apply(lambda row: safe_divide_di(row['num_errors'], row['num_total']), axis=1)
    domain_stats['overtime_rate'] = domain_stats.apply(lambda row: safe_divide_di(row['num_overtime'], row['num_total']), axis=1)

    # Check significant differences between domains
    math_errors = domain_stats.loc['Math Related', 'num_errors']
    nonmath_errors = domain_stats.loc['Non-Math Related', 'num_errors']
    math_overtime = domain_stats.loc['Math Related', 'num_overtime']
    nonmath_overtime = domain_stats.loc['Non-Math Related', 'num_overtime']


    domain_diff_tags = []
    if abs(math_errors - nonmath_errors) >= 2:
        tag = 'poor_math_related' if math_errors > nonmath_errors else 'poor_non_math_related'
        domain_diff_tags.append(tag)
    if abs(math_overtime - nonmath_overtime) >= 2:
        tag = 'slow_math_related' if math_overtime > nonmath_overtime else 'slow_non_math_related'
        domain_diff_tags.append(tag)

    # By Question Type
    type_stats = df_filtered.groupby('question_type').agg(
        num_total=('question_id', 'count'),
        num_errors=('is_correct', lambda x: (x == False).sum()),
        num_overtime=('is_slow', 'sum')
    ).reindex(['DS', 'TPA', 'MSR', 'GT'], fill_value=0) # Ensure all types exist

    type_stats['error_rate'] = type_stats.apply(lambda row: safe_divide_di(row['num_errors'], row['num_total']), axis=1)
    type_stats['overtime_rate'] = type_stats.apply(lambda row: safe_divide_di(row['num_overtime'], row['num_total']), axis=1)

    # By Difficulty Level
    difficulty_stats = df_filtered.groupby('difficulty_label').agg(
        num_total=('question_id', 'count'),
        num_errors=('is_correct', lambda x: (x == False).sum())
    )
    difficulty_stats['error_rate'] = difficulty_stats.apply(lambda row: safe_divide_di(row['num_errors'], row['num_total']), axis=1)
    # Sort by a logical order if possible, or just index
    difficulty_order = ["低難度 (Low) / 505+", "中難度 (Mid) / 555+", "中難度 (Mid) / 605+", "中難度 (Mid) / 655+", "高難度 (High) / 705+", "高難度 (High) / 805+", "極高難度 (Very High) / 805+", "未知難度"]
    difficulty_stats = difficulty_stats.reindex(difficulty_order, fill_value=0)

    # --- 3. Root Cause Diagnosis (on filtered data, update original df) ---
    # Initialize lists to store IDs for summary report
    fast_wrong_ids = []
    slow_wrong_ids = []
    normal_wrong_ids = []
    correct_slow_ids = []
    sfe_ids = [] # Already have sfe_errors_df_di, but let's collect IDs here too for consistency
    msr_reading_long_ids = []
    msr_single_q_long_ids = []
    problematic_question_details = [] # NEW list to store detailed info for report

    # Iterate through filtered df to apply logic and collect IDs/Details
    for index, question in df_filtered.iterrows():
        q_id = question['question_id']
        q_type = question['question_type']
        q_time = question['question_time']
        q_domain = question['content_domain']
        difficulty = question['question_difficulty']
        is_correct_flag = question['is_correct']
        is_slow_flag = question['is_slow'] # Use the pre-calculated is_slow flag

        # A. Calculate Relative Speed
        avg_time = avg_time_per_type_filtered.get(q_type, 0)
        is_relatively_fast_flag = (q_time < avg_time * RELATIVELY_FAST_FACTOR) if avg_time > 0 else False
        # Apply back to original df using .loc
        df.loc[df['question_id'] == q_id, 'is_relatively_fast'] = is_relatively_fast_flag


        # B. Check for Special Focus Error
        is_sfe = False
        if not is_correct_flag:
             # Use .get() with default for both levels of the multi-index
            max_diff_for_type = max_correct_difficulty_per_comb.get(q_type, pd.Series(dtype=float)) # Get Series or empty Series
            max_diff = max_diff_for_type.get(q_domain, -np.inf) # Get value for domain


            if pd.notna(difficulty) and pd.notna(max_diff) and difficulty < max_diff:
                is_sfe = True
            # Apply back to original df using .loc
            df.loc[df['question_id'] == q_id, 'special_focus_error'] = is_sfe

            if is_sfe:
                 sfe_ids.append(q_id)

        # C. MSR Specific Time Checks (Get flags first)
        is_msr_reading_long_flag = False
        is_msr_single_q_long_flag = False
        if q_type == 'MSR':
            msr_group_id = question['msr_group_id']
            group_info = msr_group_details.get(msr_group_id)
            if group_info:
                # Reading time check (on first question)
                if index == group_info['indices'][0] and pd.notna(group_info['reading_time']) and group_info['reading_time'] > MSR_READING_THRESHOLD:
                     is_msr_reading_long_flag = True
                     # Apply back to original df using .loc
                     df.loc[df['question_id'] == q_id, 'msr_reading_time_long'] = True
                     if q_id not in msr_reading_long_ids: msr_reading_long_ids.append(q_id) # Collect ID
                # Single question time check (on non-first questions)
                elif index != group_info['indices'][0] and q_time > MSR_SINGLE_Q_THRESHOLD:
                     is_msr_single_q_long_flag = True
                     # Apply back to original df using .loc
                     df.loc[df['question_id'] == q_id, 'msr_single_q_time_long'] = True
                     if q_id not in msr_single_q_long_ids: msr_single_q_long_ids.append(q_id) # Collect ID

        # D. Assign Error Classification & Get Detailed Diagnosis/Action
        classification = 'N/A'
        diag_text, action_text = "N/A", "N/A"

        if not is_correct_flag:
            if is_relatively_fast_flag: classification = 'Fast & Wrong'; fast_wrong_ids.append(q_id)
            elif is_slow_flag: classification = 'Slow & Wrong'; slow_wrong_ids.append(q_id)
            else: classification = 'Normal Time & Wrong'; normal_wrong_ids.append(q_id)
            # Apply back to original df using .loc
            df.loc[df['question_id'] == q_id, 'error_classification'] = classification

        elif is_slow_flag: # Correct but slow
             # Apply back to original df using .loc
            df.loc[df['question_id'] == q_id, 'correct_but_slow'] = True

            correct_slow_ids.append(q_id)

        # Get detailed diagnosis regardless of correctness if there's an issue (slow, MSR time, or incorrect)
        if not is_correct_flag or is_slow_flag or is_msr_reading_long_flag or is_msr_single_q_long_flag:
             diag_text, action_text = get_detailed_diagnosis(
                 q_type, q_domain, is_correct_flag, is_slow_flag, is_relatively_fast_flag,
                 is_msr_reading_long_flag, is_msr_single_q_long_flag
             )
             # Apply back to original df using .loc
             df.loc[df['question_id'] == q_id, 'diagnosis_text'] = diag_text
             df.loc[df['question_id'] == q_id, 'suggested_action'] = action_text


             # Store details for the report
             problematic_question_details.append({
                 'id': q_id,
                 'type': q_type,
                 'domain': q_domain,
                 'time': q_time,
                 'correct': is_correct_flag,
                 'slow': is_slow_flag,
                 'fast': is_relatively_fast_flag,
                 'sfe': is_sfe,
                 'msr_read_long': is_msr_reading_long_flag,
                 'msr_single_long': is_msr_single_q_long_flag,
                 'diagnosis': diag_text,
                 'action': action_text,
                 'classification': classification if not is_correct_flag else ("Correct but Slow" if is_slow_flag else "Correct"),
                 'correct_but_slow': is_correct_flag and is_slow_flag, # Explicitly add the key
                 'difficulty_label': question['difficulty_label'] # Get label from filtered df
             })


    # --- 4. Pattern Observation (on filtered data) ---
    early_fast_questions = df_filtered[
        (df_filtered['question_position'] <= EARLY_POSITION_LIMIT) &
        (df_filtered['question_time'] < EARLY_FAST_TIME_THRESHOLD_ABS)
    ]
    early_fast_q_ids_di = early_fast_questions['question_id'].tolist()

    # Calculate Carelessness Issue Rate (using is_relatively_fast applied to original df for filtered items)
    filtered_q_ids = df_filtered['question_id'].tolist()
    # Access flags directly from the updated original DataFrame
    fast_flags_in_filtered = df.loc[df['question_id'].isin(filtered_q_ids), 'is_relatively_fast']
    correct_flags_in_filtered = df.loc[df['question_id'].isin(filtered_q_ids), 'is_correct']


    num_relatively_fast_total_di = fast_flags_in_filtered.sum()
    num_relatively_fast_incorrect_di = (fast_flags_in_filtered & ~correct_flags_in_filtered).sum()

    fast_wrong_rate_di = safe_divide_di(num_relatively_fast_incorrect_di, num_relatively_fast_total_di)
    carelessness_issue_di = fast_wrong_rate_di > CARELESSNESS_RATE_THRESHOLD_DI

    # --- 5. Foundational Skill Override (on filtered data) ---
    override_details_di = {}
    override_agg_params = {} # Store Y_agg and Z_agg

    # Use type_stats calculated in Chapter 2
    for q_type, stats in type_stats.iterrows():
        # Ensure stats is Series and has the required indices before checking
        if isinstance(stats, pd.Series) and 'error_rate' in stats.index and 'overtime_rate' in stats.index:
             if stats['error_rate'] > OVERRIDE_RATE_THRESHOLD or stats['overtime_rate'] > OVERRIDE_RATE_THRESHOLD:
                override_details_di[q_type] = True
                # Find min difficulty among error/overtime for this type
                override_trigger_questions = df_filtered[
                    (df_filtered['question_type'] == q_type) &
                    ((df_filtered['is_correct'] == False) | (df_filtered['is_slow'] == True))
                ]
                if not override_trigger_questions.empty:
                    min_diff = override_trigger_questions['question_difficulty'].min()
                    max_time = override_trigger_questions['question_time'].max()
                    y_agg = map_difficulty_to_label_di(min_diff)
                    # Fix Z_agg calculation: MD implies floor(max_time*2)/2
                    z_agg = floor_to_nearest_0_5_di(max_time) # floor(val*2)/2 is the same as floor_to_nearest_0_5
                    override_agg_params[q_type] = {'Y_agg': y_agg, 'Z_agg': z_agg}

                else:
                    # Should not happen if override triggered, but handle defensively
                    override_agg_params[q_type] = {'Y_agg': "未知難度", 'Z_agg': None}

    # --- 6. Practice Planning & Recommendations ---
    recommendations_by_type = defaultdict(list)
    processed_override_types_di = set()

    # Calculate exempted combinations
    exempted_combinations = set()
    # Check if columns exist before accessing
    if 'question_type' in df_filtered.columns and 'content_domain' in df_filtered.columns:
         correct_not_slow_df = df_filtered[
            (df_filtered['is_correct'] == True) & (df_filtered['is_slow'] == False)
         ]
         if not correct_not_slow_df.empty:
             correct_not_slow_counts = correct_not_slow_df.groupby(['question_type', 'content_domain']).size().unstack(fill_value=0)

             for q_type in correct_not_slow_counts.index:
                 for domain in correct_not_slow_counts.columns:
                      if correct_not_slow_counts.loc[q_type, domain] > EXEMPTION_THRESHOLD_DI:
                           exempted_combinations.add((q_type, domain))

    # Identify trigger questions (incorrect or correct_but_slow in filtered data)
    trigger_indices_filtered = df_filtered[
        (~df_filtered['is_correct']) | df_filtered['correct_but_slow']
    ].index
    # Ensure 'question_type' column exists before using .loc
    all_trigger_types = set()
    if 'question_type' in df_filtered.columns:
         all_trigger_types = set(df_filtered.loc[trigger_indices_filtered, 'question_type']) | set(override_details_di.keys())


    for q_type in all_trigger_types:
        if not isinstance(q_type, str) or not q_type: continue

        # Macro Recommendation Check
        if q_type in override_details_di and q_type not in processed_override_types_di:
            params = override_agg_params.get(q_type, {})
            y_agg = params.get('Y_agg', '未知難度')
            z_agg = params.get('Z_agg')
            z_agg_text = f"{z_agg:.1f}" if z_agg is not None else "N/A"
            macro_rec = f"針對 [{q_type}] 題型，由於整體表現有較大提升空間，建議全面鞏固基礎，可從 [{y_agg}] 難度題目開始系統性練習，掌握核心方法，建議限時 [{z_agg_text}] 分鐘。"
            recommendations_by_type[q_type].append({'type': 'macro', 'text': macro_rec, 'priority': 1})
            processed_override_types_di.add(q_type)
            continue # Skip individual recs if macro applies

        # Individual Recommendation Generation (Iterate through triggers for this type)
        # Check if 'question_type' column exists
        if 'question_type' not in df_filtered.columns: continue

        type_trigger_indices_filtered = df_filtered[
            (df_filtered['question_type'] == q_type) &
            ((~df_filtered['is_correct']) | df_filtered['correct_but_slow'])
        ].index

        processed_q_ids_for_type = set()
        for idx in type_trigger_indices_filtered:
            question = df_filtered.loc[idx]
            q_id = question['question_id']
            q_domain = question['content_domain']
            if q_id in processed_q_ids_for_type: continue

            # Check exemption and macro skip again for this specific combo
            if (q_type, q_domain) in exempted_combinations: continue
            if q_type in processed_override_types_di: continue # Should be caught above, but double-check

            difficulty = question['question_difficulty']
            q_time = question['question_time']
            is_slow_flag = question['is_slow']
            is_correct_flag = question['is_correct']

            # Fetch diagnostics from original df using .loc and checking existence
            error_class, is_sfe_flag = "未知", False
            diag_row = df[df['question_id'] == q_id]
            if not diag_row.empty:
                 question_diagnostics = diag_row.iloc[0]
                 error_class = question_diagnostics.get('error_classification', "未知")
                 is_sfe_flag = question_diagnostics.get('special_focus_error', False)


            # Calculate Y and Z
            practice_difficulty_y = map_difficulty_to_label_di(difficulty)
            practice_time_z = calculate_practice_time_di(q_time, is_slow_flag, q_type)
            target_map = {'DS': 2.0, 'TPA': 3.0, 'GT': 3.0, 'MSR': 2.0}
            target_time_disp = target_map.get(q_type, 2.0)

            # Build recommendation text
            trigger_reason, priority = "", 5
            if not is_correct_flag:
                trigger_reason = f"基於錯誤題目 (ID: {q_id}, 分類: {error_class})"
                if is_sfe_flag: trigger_reason += " **基礎掌握不穩**"; priority = 2
                else: priority = 3
            else: # Must be correct_but_slow
                 trigger_reason = f"基於正確但超時題目 (ID: {q_id})"
                 priority = 4

            rec_text = f"{trigger_reason} (領域: {q_domain}): 建議練習 [{practice_difficulty_y}] 難度題目，起始練習限時建議為 [{practice_time_z:.1f}] 分鐘。(最終目標時間: {q_type} {target_time_disp:.1f}分鐘)。"
            if practice_time_z is not None and target_time_disp is not None and \
               practice_time_z - target_time_disp > Z_TIME_INCREASE_WARNING_THRESHOLD_DI:
                 rec_text += " **需加大練習量以確保逐步限時有效**"


            recommendations_by_type[q_type].append({
                'type': 'individual', 'text': rec_text, 'priority': priority,
                'is_sfe': is_sfe_flag, 'q_id': q_id, 'domain': q_domain # Store domain for focus rule
            })
            processed_q_ids_for_type.add(q_id)

    # Final Assembly of Recommendations List
    final_recommendations_list_di = []
    processed_final_types_di = set()

    # Add exemptions first (only if no macro/individual recommendation exists for that type)
    exempted_types_added = set()
    for q_type, domain in exempted_combinations:
         if q_type not in processed_override_types_di and not any(r['type'] == 'individual' for r in recommendations_by_type.get(q_type, [])):
            if q_type not in exempted_types_added: # Avoid adding multiple exemption notes for same type
                 exemption_text = f"[{q_type}] 題型在部分領域表現穩定，若無其他建議可暫緩練習。" # Generic exemption note per type
                 # Find if any specific domain was exempted for this type
                 specific_exemptions = [d for qt, d in exempted_combinations if qt == q_type]
                 if specific_exemptions:
                      exemption_text = f"[{q_type}] 題型在 [{', '.join(specific_exemptions)}] 領域表現穩定，可暫緩練習。"

                 final_recommendations_list_di.append({'type': q_type, 'text': exemption_text, 'priority': 99})
                 processed_final_types_di.add(q_type)
                 exempted_types_added.add(q_type)


    # Add active recommendations (sorted by priority within type)
    valid_type_keys = [k for k in recommendations_by_type.keys() if isinstance(k, str) and k]
    sorted_types_di = sorted(valid_type_keys)

    for q_type in sorted_types_di:
        if q_type in processed_final_types_di: continue
        active_recs = [rec for rec in recommendations_by_type.get(q_type, [])] # Keep macro and individual
        if not active_recs: continue

        active_recs.sort(key=lambda x: x.get('priority', 5))

        # Build combined text, apply focus rules
        combined_type_rec_text = f"--- 題型: {q_type} ---"
        has_math_rec = False
        has_nonmath_rec = False
        for rec in active_recs:
            combined_type_rec_text += f"\n- {rec['text']}"
            if rec.get('type') == 'individual':
                if rec.get('domain') == 'Math Related': has_math_rec = True
                if rec.get('domain') == 'Non-Math Related': has_nonmath_rec = True

        # Apply Content Domain Focus Rules (based on Chapter 2 tags)
        focus_added = False
        if ('poor_math_related' in domain_diff_tags or 'slow_math_related' in domain_diff_tags) and has_math_rec:
            combined_type_rec_text += "\n  **建議增加該題型下 Math Related 題目的練習比例。**"
            focus_added = True
        if ('poor_non_math_related' in domain_diff_tags or 'slow_non_math_related' in domain_diff_tags) and has_nonmath_rec:
            combined_type_rec_text += "\n  **建議增加該題型下 Non-Math Related 題目的練習比例。**"
            focus_added = True

        overall_priority = min(rec.get('priority', 5) for rec in active_recs)
        final_recommendations_list_di.append({'type': q_type, 'text': combined_type_rec_text, 'priority': overall_priority})
        processed_final_types_di.add(q_type)

    final_recommendations_list_di.sort(key=lambda x: x['priority'])

    # --- 7. Diagnostic Summary Generation ---
    summary_lines = []
    summary_lines.append("========== GMAT DI 診斷報告 ==========")

    # 1. Overall Time Strategy
    summary_lines.append("\n**1. 整體時間策略與作答有效性**")
    time_pressure_desc = "時間壓力顯著 (總剩餘時間 <= 3 分鐘)" if time_pressure else "時間相對充裕"
    summary_lines.append(f"- **整體時間壓力:** {time_pressure_desc} (總時間差 {time_diff:.1f} 分鐘)。")
    if invalid_question_ids_di:
        invalid_ids_str = ', '.join(map(str, sorted(invalid_question_ids_di)))
        summary_lines.append(f"- **結尾作答分析:** 測驗末尾存在 {len(invalid_question_ids_di)} 題作答過快 (<1.0分鐘)，且處於時間壓力下，已被標記為 **無效數據** (題目 ID: {invalid_ids_str})。")
    else:
        summary_lines.append("- **結尾作答分析:** 未檢測到因時間壓力導致的末尾搶答/無效作答現象。")
    summary_lines.append(f"- **超時標準:** DS={overtime_thresholds.get('DS', 'N/A'):.1f}min, TPA={overtime_thresholds.get('TPA', 'N/A'):.1f}min, GT={overtime_thresholds.get('GT', 'N/A'):.1f}min, MSR題組目標={msr_group_target:.1f}min (基於壓力狀況)。")

    # 2. Performance Overview
    summary_lines.append("\n**2. 表現概覽 (基於有效數據)**")
    summary_lines.append("- **內容領域 (Content Domain) 表現:**")
    if not domain_stats.empty:
        for domain, stats in domain_stats.iterrows():
            diff_markers = [tag for tag in domain_diff_tags if domain.replace(" ","_").lower() in tag]
            marker_text = f" *({', '.join(diff_markers)})*" if diff_markers else ""
            # Check if stats is Series before accessing by index
            error_rate_txt = f"{stats['error_rate']:.1%}" if isinstance(stats, pd.Series) and 'error_rate' in stats.index else "N/A"
            overtime_rate_txt = f"{stats['overtime_rate']:.1%}" if isinstance(stats, pd.Series) and 'overtime_rate' in stats.index else "N/A"
            summary_lines.append(f"  - {domain}: 錯誤率 {error_rate_txt}, 超時率 {overtime_rate_txt}{marker_text}")

    else: summary_lines.append("  - 無法按內容領域分析。")

    summary_lines.append("- **題型 (Question Type) 表現:**")
    if not type_stats.empty:
        for q_type, stats in type_stats.iterrows():
             override_marker = " *(需優先鞏固)*" if q_type in override_details_di else ""
             # Check if stats is Series before accessing by index
             error_rate_txt = f"{stats['error_rate']:.1%}" if isinstance(stats, pd.Series) and 'error_rate' in stats.index else "N/A"
             overtime_rate_txt = f"{stats['overtime_rate']:.1%}" if isinstance(stats, pd.Series) and 'overtime_rate' in stats.index else "N/A"
             summary_lines.append(f"  - {q_type}: 錯誤率 {error_rate_txt}, 超時率 {overtime_rate_txt}{override_marker}")

    else: summary_lines.append("  - 無法按題型分析。")

    summary_lines.append("- **難度區間表現 (錯誤率):**")
    if not difficulty_stats.empty:
         for label, stats in difficulty_stats.iterrows():
              # Check if stats is Series and has num_total > 0
             if isinstance(stats, pd.Series) and stats.get('num_total', 0) > 0:
                 error_rate_txt = f"{stats['error_rate']:.1%}"
                 num_errors_txt = int(stats.get('num_errors', 0))
                 num_total_txt = int(stats.get('num_total', 0))
                 summary_lines.append(f"  - {label}: {error_rate_txt} ({num_errors_txt}/{num_total_txt})")

    else: summary_lines.append("  - 無法按難度區間分析。")

    # 3. Core Problem Diagnosis (Detailed Per Question)
    summary_lines.append("\n**3. 核心問題診斷 (逐題分析)**")
    if problematic_question_details:
        # Sort by priority (SFE first), then by question position/ID for consistency
        problematic_question_details.sort(key=lambda x: (0 if x['sfe'] else 1, df.loc[df['question_id'] == x['id'], 'question_position'].iloc[0]))

        for detail in problematic_question_details:
            q_id = detail['id']
            q_type = detail['type']
            q_domain = detail['domain']
            q_time_txt = f"{detail['time']:.1f}min"
            correct_txt = "正確" if detail['correct'] else "錯誤"
            sfe_marker = " **[基礎掌握不穩]**" if detail['sfe'] else ""
            diff_label = detail['difficulty_label']

            time_perf_desc = ""
            if detail['classification'] != 'N/A' and not detail['correct']:
                 time_perf_desc = f"({detail['classification']})"
            elif detail['correct_but_slow']:
                 time_perf_desc += "(正確但慢)"
            elif detail['msr_read_long']:
                 time_perf_desc += "(MSR閱讀長)"
            elif detail['msr_single_long']:
                 time_perf_desc += "(MSR單題長)"


            summary_lines.append(f"\n- **題目 ID {q_id}:** [{q_type}, {q_domain}, {diff_label}, {q_time_txt}, {correct_txt}] {time_perf_desc}{sfe_marker}")
            if detail['diagnosis'] != "N/A":
                summary_lines.append(f"  - *診斷:* {detail['diagnosis']}")
            if detail['action'] != "N/A":
                summary_lines.append(f"  - *建議行動:* {detail['action']}")
    else:
        summary_lines.append("- 本次測驗在有效題目中未發現明顯的核心問題（錯誤、超時等）。")


    # 4. Pattern Observation
    summary_lines.append("\n**4. 特殊模式觀察**")
    if early_fast_q_ids_di:
        early_ids_str_di = ', '.join(map(str, sorted(early_fast_q_ids_di)))
        summary_lines.append(f"- **測驗前期作答:** 開始階段存在 {len(early_fast_q_ids_di)} 題作答速度 (<1.0分鐘) **明顯偏快** (ID: {early_ids_str_di})。注意 `flag for review` 風險。")
    else:
        summary_lines.append("- **測驗前期作答:** 未發現在測驗初期作答明顯過快的情況。")

    if carelessness_issue_di:
        # List the IDs contributing to fast & wrong rate
        fast_wrong_contributing_ids = df.loc[df['question_id'].isin(filtered_q_ids) & df['is_relatively_fast'] & ~df['is_correct'], 'question_id'].tolist()
        ids_str = f" (涉及題目 ID: {', '.join(map(str, sorted(fast_wrong_contributing_ids)))})" if fast_wrong_contributing_ids else ""
        summary_lines.append(f"- **粗心問題評估:** 「相對快且錯」的比例 ({fast_wrong_rate_di:.1%}) **偏高** (>{CARELESSNESS_RATE_THRESHOLD_DI:.0%}){ids_str}。提示可能需 **關注答題仔細程度**。(建議結合第3部分這些題目的診斷，確認是流程簡化、閱讀疏漏還是方法不熟導致)")

    elif num_relatively_fast_total_di > 0:
         summary_lines.append(f"- **粗心問題評估:** 「相對快且錯」比例 ({fast_wrong_rate_di:.1%}) 在正常範圍內。")
    else:
         summary_lines.append("- **粗心問題評估:** 未能評估（無作答相對較快的題目）。")

    # 5. Foundational Consolidation
    summary_lines.append("\n**5. 基礎鞏固提示**")
    triggered_override_types_list = list(override_details_di.keys())
    if triggered_override_types_list:
        types_str = ', '.join(triggered_override_types_list)
        summary_lines.append(f"- **優先系統鞏固:** 對於 **[{types_str}]** 題型，因整體錯誤率或超時率超過 50%，建議 **優先進行系統性基礎鞏固**。詳見練習計劃。")
    else:
        summary_lines.append("- **優先系統鞏固:** 未發現需覆蓋式基礎鞏固的題型。")

    # 6. Detailed Practice Plan
    summary_lines.append("\n**6. 詳細練習計劃**")
    if final_recommendations_list_di:
        summary_lines.append("根據以上分析，建議您針對以下題型進行練習：\n")
        for rec in final_recommendations_list_di:
            summary_lines.append(f"\n{rec['text']}") # Already includes type header
    elif not df_filtered.empty:
        summary_lines.append("- 本次分析未生成具體的練習建議（可能因表現穩定或均被豁免）。")

    # 7. Next Steps and Reflection Guidance
    summary_lines.append("\n\n**7. 後續行動與反思指引**")
    summary_lines.append("本報告提供數據診斷，提升需結合反思和練習。請特別關注第 3 部分列出的逐題診斷與建議行動。")
    summary_lines.append("\n- **引導反思 (針對第3部分診斷的具體題目):**")

    # Gather all problematic IDs for reflection prompt
    problematic_ids_for_prompt = set(q['id'] for q in problematic_question_details) # Use IDs from detailed list
    # problematic_ids_str = ", ".join(map(str, sorted(list(problematic_ids_for_prompt)))) if problematic_ids_for_prompt else ""

    # --- REMOVE OLD GENERIC PROMPT ---
    # if problematic_ids_str:
    #     summary_lines.append(f"  - **針對第 3 部分診斷中提到的問題題目 (ID: {problematic_ids_str})**，請結合具體診斷和建議行動進行回憶：當時的卡點是什麼？是哪個環節導致了錯誤或耗時？診斷中提到的可能原因是否符合您的情況？")
    # else:
    #      summary_lines.append("  - 本次測驗表現穩定，未發現明顯錯誤或超時問題。可思考如何進一步提升效率或挑戰更高難度。")

    # --- ADD NEW PER-QUESTION PROMPTS --- 
    if not problematic_question_details:
         summary_lines.append("  - 本次測驗表現穩定，未發現明顯錯誤或超時問題。可思考如何進一步提升效率或挑戰更高難度。")
    else:
        # Iterate through problematic questions and generate specific reflection prompts
        for detail in problematic_question_details:
            q_id = detail['id']
            q_type = detail['type']
            q_domain = detail['domain']
            classification = detail['classification'] # e.g., "Slow & Wrong", "Correct but Slow"
            is_sfe = detail['sfe']
            msr_read_long = detail['msr_read_long']
            msr_single_long = detail['msr_single_long']
            correct = detail['correct']

            prompt = f"  - **題目 ID {q_id}** ({q_type}, {q_domain}, {classification}){': [基礎掌握不穩]' if is_sfe else ':'}" # Base prompt start

            # Add specific reflection question based on the issue
            reflection_points = []
            if not correct:
                if '慢' in classification:
                    points = ["文字理解", "公式/概念", "計算", "圖表解讀(GT)", "信息整合(MSR)", "邏輯推理步驟"]
                    reflection_points.append(f"回憶卡點：是 {'、'.join(points)} 中的哪方面？")
                elif '快' in classification or '正常' in classification:
                    points = ["相關知識點不熟", "方法應用錯誤", "文字理解疏漏/錯誤", "題目內在邏輯應用錯誤"]
                    reflection_points.append(f"回憶失誤點：是 {'、'.join(points)} 中的哪方面？")
                if is_sfe:
                    reflection_points.append("為何在已掌握難度範圍內失誤？")
            elif detail['correct_but_slow']: # Correct but slow
                points = ["文字理解", "計算", "定位信息", "整合信息", "選項排除"]
                reflection_points.append(f"回憶效率瓶頸：是哪個環節耗時最長？({'、'.join(points)} 等)")

            # MSR specific prompts
            if msr_read_long:
                reflection_points.append("（MSR閱讀）回憶是文字、圖表還是跨頁整合更耗時？")
            if msr_single_long:
                reflection_points.append("（MSR答題）回憶是讀題、定位信息還是比較選項更耗時？")

            if reflection_points:
                prompt += " " + " ".join(reflection_points)
            else: # Fallback if somehow marked problematic but no specific points match
                 prompt += " 請回憶該題作答過程中的具體情況。"

            summary_lines.append(prompt)

    summary_lines.append("\n- **二級證據參考建議 (針對第3部分診斷的具體題目):**")
    # --- Modify Secondary Evidence section --- 
    if not problematic_question_details:
        summary_lines.append("  - 無需特別查找二級證據。")
    else:
        secondary_evidence_needed = False
        secondary_prompts = [] # Collect prompts first
        for detail in problematic_question_details:
             # Check if the action text suggests secondary evidence
             if "二級證據" in detail['action'] or "查看近期" in detail['action']:
                 secondary_evidence_needed = True
                 q_id = detail['id']
                 q_type = detail['type']
                 q_domain = detail['domain']
                 # Determine the characteristic to search for based on the original problem
                 search_characteristic = detail['classification'] # Default to the classification
                 # Refine search characteristic based on specific issues
                 if detail['msr_read_long']: search_characteristic = "MSR閱讀慢"
                 elif detail['msr_single_long']: search_characteristic = "MSR單題慢"
                 elif detail['correct_but_slow'] and not detail['msr_read_long'] and not detail['msr_single_long']:
                      search_characteristic = "正確但慢"
                 elif not detail['correct']:
                      if '慢' in detail['classification']: search_characteristic = "慢且錯"
                      elif '快' in detail['classification']: search_characteristic = "快且錯"
                      else: search_characteristic = "正常時間錯誤"

                 secondary_prompts.append(f"  - **題目 ID {q_id}** ({q_type}, {q_domain}): 查找近期練習中其他 **'{search_characteristic}'** 的 **{q_type} ({q_domain})** 題目，歸納錯誤模式/考點/障礙類型 (參考第3部分診斷)。若樣本不足(<5-10題)，注意積累。")
     
        if not secondary_evidence_needed:
            summary_lines.append("  - 根據本次診斷，暫無需特別查找二級證據。")
        else:
            summary_lines.append("  - *觸發時機:* 當第 3 部分的建議行動提示需要查看二級證據時，或您無法準確回憶具體障礙點/錯誤原因時。")
            summary_lines.append("  - *建議行動 (請根據以下針對性建議執行):*")
            summary_lines.extend(secondary_prompts) # Add all collected prompts
 
    summary_lines.append("\n- **質化分析建議:**")
    summary_lines.append("  - *觸發時機:* 當第 3 部分的建議行動提示需要進行質化分析時，或您對診斷結果/建議行動感到困惑，且二級證據仍無法釐清根本原因時。")

    summary_lines.append("\n========== 報告結束 ==========")

    # --- Combine DataFrame and Summary for Output ---
    summary_df_di = pd.DataFrame({'診斷報告與建議': summary_lines})
    # Dynamically create spacer based on df columns
    spacer_data_di = {col: [None] * 3 for col in df.columns}
    spacer_df_di = pd.DataFrame(spacer_data_di)
    summary_df_aligned_di = pd.DataFrame(columns=df.columns)
    first_col_name = df.columns[0] # Use the first column for alignment
    summary_df_aligned_di[first_col_name] = summary_df_di['診斷報告與建議']
    # Ensure alignment works even if df is empty or has few columns
    for col in df.columns[1:]:
         if col not in summary_df_aligned_di.columns:
              summary_df_aligned_di[col] = None

    # Concatenate making sure indices are handled correctly
    final_df_di = pd.concat([df.reset_index(drop=True),
                            spacer_df_di.reset_index(drop=True),
                            summary_df_aligned_di.reset_index(drop=True)],
                           ignore_index=True)


    # --- Save Final Result ---
    try:
        final_df_di.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        print(f"\n分析完成，DI 診斷報告與建議已儲存至: {output_csv_path}")
    except Exception as e:
        print(f"\n錯誤：儲存 DI 結果至 CSV 檔案 '{output_csv_path}' 時發生錯誤: {e}")
        sys.exit(1)

# --- Command-Line Execution ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='分析 GMAT Data Insights (DI) 測驗數據並生成診斷報告 (基於 gmat-di-score-logic-dustin-v1.1.md)。',
        formatter_class=argparse.RawTextHelpFormatter # Preserve newline formatting in help
    )
    parser.add_argument(
        'input_csv',
        help='輸入的 CSV 檔案路徑 (例如：testset-di.csv)。\n必須包含欄位: Question, Response Time (Minutes), Performance, Content Domain, Question Type, DI_b' # Updated help text
    )
    parser.add_argument(
        'output_csv',
        help='輸出的 CSV 檔案路徑 (例如：testset-di-analyzed.csv)。'
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
    override_di = None
    if args.force_time_pressure: override_di = True
    elif args.force_no_time_pressure: override_di = False

    analyze_gmat_di_data(args.input_csv, args.output_csv, user_override_time_pressure=override_di) 