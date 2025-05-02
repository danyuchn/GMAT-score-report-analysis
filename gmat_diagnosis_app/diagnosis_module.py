import pandas as pd
import numpy as np

# Import subject-specific diagnosis runners
from .diagnostics.q_diagnostic import run_q_diagnosis
from .diagnostics.v_diagnostic import run_v_diagnosis
from .diagnostics.di_diagnostic import run_di_diagnosis

# --- Main Diagnosis Orchestration Function ---

def run_diagnosis(df):
    """
    Runs the complete diagnostic analysis by orchestrating subject-specific modules.
    Performs initial data validation and Chapter 1 analysis (Time Strategy & Validity)
    before dispatching data to Q, V, and DI diagnostic runners.

    Args:
        df (pd.DataFrame): DataFrame containing response data.
                           Expected columns: 'Question ID', 'Correct', 'question_difficulty' (simulated),
                           'question_time', 'question_type', 'question_fundamental_skill',
                           'question_position', 'Subject' ('Q', 'V', or 'DI'),
                           'estimated_ability' (optional).

    Returns:
        str: A combined report string containing diagnostics for all available subjects (Q, V, DI),
             or an error message if input is invalid or no valid data remains after filtering.
    """

    # --- 0. Initial Validation ---
    # Define the required columns, including 'Subject'
    required_cols = ['Question ID', 'Correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'question_position', 'Subject']
    if not isinstance(df, pd.DataFrame):
         print("Invalid input: Input is not a pandas DataFrame.")
         return "錯誤：輸入數據格式無效。"

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Invalid input DataFrame. Missing required columns: {missing_cols}")
        # Provide a more informative error message
        return f"錯誤：輸入數據缺少必要的欄位：{', '.join(missing_cols)}。請檢查上傳的 Excel 文件。"

    # Subject column is checked above as part of required_cols

    df_processed = df.copy()

    # --- Data Type Conversion and Cleaning ---
    # Convert time and position to numeric, coercing errors
    df_processed['question_time'] = pd.to_numeric(df_processed['question_time'], errors='coerce')
    df_processed['question_position'] = pd.to_numeric(df_processed['question_position'], errors='coerce')
    df_processed['question_difficulty'] = pd.to_numeric(df_processed['question_difficulty'], errors='coerce')
    # Convert Correct to boolean, handling potential string values ('True', 'False')
    if df_processed['Correct'].dtype == 'object':
        df_processed['Correct'] = df_processed['Correct'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False})
    df_processed['Correct'] = df_processed['Correct'].astype(bool)

    # --- Initialize internal columns ---
    df_processed['is_invalid'] = False # Initialize is_invalid column
    df_processed['overtime'] = False # Initialize overtime column
    df_processed['overtime_threshold'] = 3.0 # Default threshold

    # --- 1. Overall Time Strategy & Data Validity (Chapter 1 Logic - Applied Per Subject) ---
    print("Starting Chapter 1: Time Strategy & Validity Analysis...")
    subjects_present = df_processed['Subject'].unique()
    all_invalid_indices = []
    subject_time_pressure_status = {} # Dictionary to store time pressure status per subject

    # Define subject-specific parameters (Adjust these as needed)
    subject_time_limits = {'Q': 45.0, 'V': 45.0, 'DI': 45.0}

    for subject in subjects_present:
        print(f"  Processing Subject: {subject}")
        # Check if subject is recognized before proceeding
        if subject not in subject_time_limits:
            print(f"    Warning: Unrecognized subject '{subject}'. Skipping time analysis for this subject.")
            subject_time_pressure_status[subject] = '未知' # Mark status as unknown
            continue

        df_subj = df_processed[df_processed['Subject'] == subject].copy()
        if df_subj.empty:
            print(f"    Subject {subject}: No data found.")
            subject_time_pressure_status[subject] = False # No pressure if no data
            continue

        # Check for NaN/NaT in critical columns after conversion
        if df_subj['question_time'].isnull().any() or df_subj['question_position'].isnull().any():
             print(f"    Warning: Subject {subject} has missing/non-numeric time or position data after conversion. Skipping detailed time analysis.")
             subject_time_pressure_status[subject] = '未知' # Status unknown if data is bad
             continue

        total_number_of_questions = len(df_subj)
        max_allowed_time = subject_time_limits.get(subject, 45.0) # Default to 45 if subject not defined
        total_test_time = df_subj['question_time'].sum()
        time_diff = max_allowed_time - total_test_time
        print(f"    Subject {subject}: Total Time = {total_test_time:.2f} min, Allowed = {max_allowed_time:.1f} min, Diff = {time_diff:.2f} min")

        # Find last third questions
        last_third_start_position = np.ceil(total_number_of_questions * 2 / 3)
        last_third_questions = df_subj[df_subj['question_position'] >= last_third_start_position]

        # Find fast questions at the end (ensure time is not NaN before comparing)
        fast_end_questions = last_third_questions[last_third_questions['question_time'].notna() & (last_third_questions['question_time'] < 1.0)]
        print(f"    Subject {subject}: Found {len(fast_end_questions)} questions < 1.0 min in last third.")

        # Determine time pressure
        time_pressure = False
        if time_diff <= 3.0 and not fast_end_questions.empty:
            time_pressure = True
            print(f"    Subject {subject}: Time Pressure Detected (Diff <= 3 min AND fast end questions exist).")
            # TODO: Implement user override logic if needed
        else:
             print(f"    Subject {subject}: No Time Pressure Detected.")

        subject_time_pressure_status[subject] = time_pressure # Store status

        # Set overtime threshold based on pressure
        overtime_threshold = 2.5 if time_pressure else 3.0
        print(f"    Subject {subject}: Overtime Threshold set to {overtime_threshold:.1f} min.")
        df_processed.loc[df_subj.index, 'overtime_threshold'] = overtime_threshold

        # Identify invalid indices (only if time pressure is true)
        if time_pressure:
            invalid_indices = fast_end_questions.index.tolist()
            all_invalid_indices.extend(invalid_indices)
            print(f"    Subject {subject}: Marked {len(invalid_indices)} question(s) as invalid due to time pressure.")

    # --- Global Rule Application: Mark Invalid and Overtime ---
    if all_invalid_indices:
        df_processed.loc[all_invalid_indices, 'is_invalid'] = True
        print(f"Marked a total of {len(all_invalid_indices)} questions as invalid across all subjects.")

    # Mark overtime for non-invalid rows based on their subject's threshold
    # Ensure time is not NaN before comparing with threshold
    df_processed['overtime'] = (
        df_processed['question_time'].notna() &
        (df_processed['question_time'] > df_processed['overtime_threshold']) &
        (~df_processed['is_invalid'])
    )
    num_overtime = df_processed['overtime'].sum()
    print(f"Marked {num_overtime} questions as overtime.")

    num_invalid_questions = len(all_invalid_indices) # Total invalid count

    # --- Filter out invalid data ---
    df_filtered = df_processed[df_processed['is_invalid'] == False].copy()
    num_filtered = len(df_processed) - len(df_filtered)
    print(f"Filtered out {num_filtered} invalid questions. Proceeding with {len(df_filtered)} valid questions for detailed diagnosis.")

    if df_filtered.empty:
        print("No valid data remaining after filtering. Cannot perform diagnosis.")
        return "診斷終止：在時間有效性過濾後，沒有剩餘的有效數據可供分析。"

    # --- Calculate Exempted Skills (for Q Chapter 7) ---
    print("Calculating exempted skills for Q Chapter 7...")
    exempted_skills = set()
    # Check if the skill column exists and has content before grouping
    if 'question_fundamental_skill' in df_filtered.columns and df_filtered['question_fundamental_skill'].notna().any():
        try:
            # Group by skill, handling potential NaN skills gracefully
            grouped_by_skill_valid = df_filtered.dropna(subset=['question_fundamental_skill']).groupby('question_fundamental_skill')
            for skill, group in grouped_by_skill_valid:
                # Ensure Correct and overtime columns are boolean before calculation
                if pd.api.types.is_bool_dtype(group['Correct']) and pd.api.types.is_bool_dtype(group['overtime']):
                    num_correct_not_overtime = group[(group['Correct'] == True) & (group['overtime'] == False)].shape[0]
                    if num_correct_not_overtime > 2:
                        exempted_skills.add(skill)
                        print(f"  Skill '{skill}' exempted for Q (Correct & Not Overtime: {num_correct_not_overtime} > 2)")
                else:
                     print(f"  Skipping exemption calculation for skill '{skill}': 'Correct' or 'overtime' column is not boolean.")
        except Exception as e:
            print(f"  Error during exemption calculation: {e}")
    else:
        print("  Skipping Q exemption calculation (missing 'question_fundamental_skill' column or column is empty).")

    # --- Dispatch to Subject-Specific Diagnosis ---
    print("\nDispatching data to subject-specific diagnosis modules...")
    subject_reports = []

    # Separate dataframes by Subject
    df_q = df_filtered[df_filtered['Subject'] == 'Q'].copy()
    df_v = df_filtered[df_filtered['Subject'] == 'V'].copy()
    df_di = df_filtered[df_filtered['Subject'] == 'DI'].copy()

    # Run Q Diagnosis if data exists
    if not df_q.empty:
        q_report = run_q_diagnosis(df_q, exempted_skills, subject_time_pressure_status, num_invalid_questions)
        subject_reports.append(q_report)
    else:
        print("No Q data found.")
        subject_reports.append("量化 (Quantitative) 部分無有效數據。")

    # Run V Diagnosis if data exists
    if not df_v.empty:
        v_report = run_v_diagnosis(df_v, subject_time_pressure_status, num_invalid_questions)
        subject_reports.append(v_report)
    else:
        print("No V data found.")
        subject_reports.append("語文 (Verbal) 部分無有效數據。")

    # Run DI Diagnosis if data exists
    if not df_di.empty:
        di_report = run_di_diagnosis(df_di, subject_time_pressure_status, num_invalid_questions)
        subject_reports.append(di_report)
    else:
        print("No DI data found.")
        subject_reports.append("數據洞察 (Data Insights) 部分無有效數據。")

    # --- Combine Reports ---
    print("\nCombining subject reports...")
    final_report_str = "\n\n---\n\n".join(subject_reports) # Join reports with a separator

    print("Diagnosis process complete.")
    return final_report_str

# End of run_diagnosis function. No other code should follow.
