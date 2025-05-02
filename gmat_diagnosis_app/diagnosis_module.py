import pandas as pd
import numpy as np

# Import subject-specific diagnosis runners
from gmat_diagnosis_app.diagnostics.q_diagnostic import run_q_diagnosis
from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis

# --- Constants from V-Doc Chapter 1 ---
V_MAX_ALLOWED_TIME = 45.0 # minutes
V_TIME_PRESSURE_THRESHOLD_DIFF = 1.0 # minutes difference
V_INVALID_TIME_ABANDONED = 0.5 # minutes
V_INVALID_TIME_HASTY_MIN = 1.0 # minutes
V_CR_OVERTIME_THRESHOLD_PRESSURE_TRUE = 2.0 # minutes
V_CR_OVERTIME_THRESHOLD_PRESSURE_FALSE = 2.5 # minutes
V_SUSPICIOUS_FAST_MULTIPLIER = 0.5

# --- Constants from DI-Doc Chapter 0 & 1 --- - Removed
# DI_MAX_ALLOWED_TIME = 45.0 # minutes
# DI_TIME_PRESSURE_THRESHOLD = 3.0 # minutes difference
# DI_INVALID_TIME_THRESHOLD = 1.0 # minutes
# DI_LAST_THIRD_FRACTION = 2/3

# Note: Q and DI constants should be defined or imported if needed

# --- Main Diagnosis Orchestration Function ---

def run_diagnosis(df):
    """
    Runs the complete diagnostic analysis by orchestrating subject-specific modules.
    Performs initial data validation and Chapter 1 analysis (Time Strategy & Validity)
    before dispatching data to Q, V, and DI diagnostic runners.

    Args:
        df (pd.DataFrame): DataFrame containing response data.
                           Expected columns: 'question_position' (acts as identifier),
                           'is_correct', 'question_difficulty' (simulated),
                           'question_time', 'question_type', 'question_fundamental_skill',
                           'Subject' ('Q', 'V', or 'DI'),
                           'estimated_ability' (optional).

    Returns:
        str: A combined report string containing diagnostics for all available subjects (Q, V, DI),
             or an error message if input is invalid or no valid data remains after filtering.
    """

    # --- 0. Initial Validation ---
    # Define the required columns, including 'Subject'
    required_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'Subject']
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
    # V-Doc uses minutes, assuming input is already in minutes. If input is seconds, convert here.
    # Let's assume input 'question_time' is MINUTES for now, aligning with V-doc Chapter 1 examples.
    df_processed['question_time'] = pd.to_numeric(df_processed['question_time'], errors='coerce')
    df_processed['question_position'] = pd.to_numeric(df_processed['question_position'], errors='coerce')
    df_processed['question_difficulty'] = pd.to_numeric(df_processed['question_difficulty'], errors='coerce')
    # Convert Correct to boolean, handling potential string values ('True', 'False')
    if df_processed['is_correct'].dtype == 'object':
        df_processed['is_correct'] = df_processed['is_correct'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False})
    df_processed['is_correct'] = df_processed['is_correct'].astype(bool)

    # --- Initialize internal columns ---
    df_processed['is_invalid'] = False # Initialize is_invalid column
    df_processed['overtime'] = False # Initialize overtime column (generic flag, specific logic in V/DI)
    df_processed['suspiciously_fast'] = False # Initialize suspiciously_fast column

    # --- 1. Overall Time Strategy & Data Validity (Chapter 1 Logic - Applied Per Subject) ---
    print("Starting Chapter 1: Time Strategy & Validity Analysis...")
    subjects_present = df_processed['Subject'].unique()
    all_invalid_indices = []
    subject_time_pressure_status = {} # Dictionary to store time pressure status per subject
    subject_avg_time_per_type = {} # Store avg times for suspiciously_fast calc

    # Define subject-specific parameters (Use V constants for V)
    subject_time_limits = {'Q': 45.0, 'V': V_MAX_ALLOWED_TIME, 'DI': 45.0} # Define DI max time here or fetch from di_diagnostic

    for subject in subjects_present:
        print(f"  Processing Subject: {subject}")
        # Check if subject is recognized before proceeding
        if subject not in subject_time_limits: # DI will be skipped here initially if not in limits
            print(f"    Warning: Unrecognized subject '{subject}'. Skipping time analysis for this subject.")
            subject_time_pressure_status[subject] = 'Unknown' # Mark status as unknown
            continue

        df_subj = df_processed[df_processed['Subject'] == subject].copy()
        if df_subj.empty:
            print(f"    Subject {subject}: No data found.")
            subject_time_pressure_status[subject] = False # No pressure if no data
            continue

        # Check for NaN/NaT in critical columns after conversion
        if df_subj['question_time'].isnull().any() or df_subj['question_position'].isnull().any():
             print(f"    Warning: Subject {subject} has missing/non-numeric time or position data after conversion. Skipping detailed time analysis.")
             subject_time_pressure_status[subject] = 'Unknown' # Status unknown if data is bad
             continue

        total_number_of_questions = len(df_subj)
        max_allowed_time = subject_time_limits.get(subject, 45.0)
        total_test_time = df_subj['question_time'].sum()
        time_diff = max_allowed_time - total_test_time
        print(f"    Subject {subject}: Total Time = {total_test_time:.2f} min, Allowed = {max_allowed_time:.1f} min, Diff = {time_diff:.2f} min")

        # Determine time pressure (using V-doc logic for V subject)
        time_pressure = False
        if subject == 'V':
            if time_diff < V_TIME_PRESSURE_THRESHOLD_DIFF:
                time_pressure = True
                print(f"    Subject {subject}: Time Pressure Detected (V Logic: Diff < {V_TIME_PRESSURE_THRESHOLD_DIFF} min).")
            else:
                print(f"    Subject {subject}: No Time Pressure Detected (V Logic).")
            # --- User Override Logic Placeholder ---
            # if user_override_flags.get(subject, {}).get('no_pressure', False):
            #     time_pressure = False
            #     print(f"    Subject {subject}: User OVERRIDE - Time Pressure set to False.")
        elif subject == 'DI':
            # DI time pressure and invalid logic is handled within di_diagnostic.py
            # We still need to calculate avg times for suspicious check later if needed
            print(f"    Subject {subject}: Time pressure and validity handled within DI module.")
            # Store a default status or skip? Let's store False, as the DI module calculates the real one.
            time_pressure = False # Default placeholder, DI module calculates the true value
            # If suspicious fast logic is needed globally for DI, calculate avg times here.
            if 'question_type' in df_subj.columns:
                subject_avg_time_per_type[subject] = df_subj.groupby('question_type')['question_time'].mean().to_dict()
                print(f"      Avg time per type (min) for DI (for potential suspicious check): {subject_avg_time_per_type[subject]}")
            else:
                subject_avg_time_per_type[subject] = {}
                print("      Warning: 'question_type' column missing for DI, cannot calculate average times.")

        else: # Apply original logic for Q for now (needs review based on their docs)
             last_third_start_position = np.ceil(total_number_of_questions * 2 / 3)
             last_third_questions = df_subj[df_subj['question_position'] >= last_third_start_position]
             fast_end_questions = last_third_questions[last_third_questions['question_time'].notna() & (last_third_questions['question_time'] < 1.0)] # Assuming 1.0 min threshold still applies for Q's original logic check
             if time_diff <= 3.0 and not fast_end_questions.empty:
                 time_pressure = True
                 print(f"    Subject {subject}: Time Pressure Detected (Original Logic: Diff <= 3 min AND fast end questions exist).")
             else:
                  print(f"    Subject {subject}: No Time Pressure Detected (Original Logic).")

        subject_time_pressure_status[subject] = time_pressure # Store status

        # Calculate average time per type for this subject (needed for invalid & suspicious checks)
        # TODO: Add calculation for first_third_average_time_per_type if needed by invalid logic
        if 'question_type' in df_subj.columns:
             subject_avg_time_per_type[subject] = df_subj.groupby('question_type')['question_time'].mean().to_dict()
             print(f"      Avg time per type (min): {subject_avg_time_per_type[subject]}")
        else:
             subject_avg_time_per_type[subject] = {}
             print("      Warning: 'question_type' column missing, cannot calculate average times.")


        # Identify invalid indices (only if time pressure is true)
        if time_pressure:
            invalid_indices_subj = []
            
            if subject == 'V':
                last_third_start_position = np.ceil(total_number_of_questions * 2 / 3)
                last_third_df = df_subj[df_subj['question_position'] >= last_third_start_position]
                
                avg_times = subject_avg_time_per_type.get(subject, {})
                
                for index, row in last_third_df.iterrows():
                    q_time = row['question_time']
                    q_type = row['question_type']
                    
                    # Check for Abandoned
                    is_abandoned = q_time < V_INVALID_TIME_ABANDONED
                    
                    # Check for Hasty (V-doc logic needs avg times and RC group logic)
                    is_hasty = q_time < V_INVALID_TIME_HASTY_MIN
                    # Placeholder for more complex hasty check from V-doc (requires avg time and RC group handling)
                    # avg_time_for_type = avg_times.get(q_type)
                    # if avg_time_for_type is not None:
                    #     # Need first_third_average_time for comparison
                    #     # Need RC group logic here too
                    #     # Example placeholder for CR hasty check:
                    #     # if q_type == 'CR' and q_time < first_third_avg_time_cr * 0.5: is_hasty = True
                    #     pass # Implement full hasty logic when avg times and RC groups are handled
                    
                    if is_abandoned or is_hasty:
                        invalid_indices_subj.append(index)
            elif subject == 'DI':
                # DI invalid logic handled within di_diagnostic.py
                pass # Do nothing here for DI invalid marking
            else:  # 預設邏輯 (目前用於 Q)
                last_third_start_position = np.ceil(total_number_of_questions * 2 / 3)
                last_third_df = df_subj[df_subj['question_position'] >= last_third_start_position]
                invalid_mask = last_third_df['question_time'] < 1.0
                invalid_indices_subj = last_third_df[invalid_mask].index.tolist()

            if invalid_indices_subj:
                all_invalid_indices.extend(invalid_indices_subj)
                print(f"    Subject {subject}: Marked {len(invalid_indices_subj)} question(s) in last third as invalid due to time pressure and being hasty/abandoned.")

    # --- Global Rule Application: Mark Invalid, Overtime (CR only here), Suspiciously Fast ---
    if all_invalid_indices:
        df_processed.loc[all_invalid_indices, 'is_invalid'] = True
        print(f"Marked a total of {len(all_invalid_indices)} questions as invalid across all subjects.")

    # Mark overtime for Q rows based on Q subject's pressure
    if 'Q' in subject_time_pressure_status:
        q_pressure = subject_time_pressure_status['Q']
        q_overtime_threshold = 2.5 if q_pressure else 3.0  # Set threshold based on pressure
        q_overtime_mask = (
            (df_processed['Subject'] == 'Q') &
            (df_processed['question_time'].notna()) &
            (df_processed['question_time'] > q_overtime_threshold) &
            (~df_processed['is_invalid'])
        )
        df_processed.loc[q_overtime_mask, 'overtime'] = True
        print(f"Marked {q_overtime_mask.sum()} Q questions as overtime (threshold: {q_overtime_threshold:.1f} min).")

    # Mark overtime for non-invalid CR rows based on V subject's pressure
    # Overtime for RC and other subjects needs subject-specific logic
    if 'V' in subject_time_pressure_status:
        v_pressure = subject_time_pressure_status['V']
        v_cr_threshold = V_CR_OVERTIME_THRESHOLD_PRESSURE_TRUE if v_pressure else V_CR_OVERTIME_THRESHOLD_PRESSURE_FALSE
        cr_overtime_mask = (
            (df_processed['Subject'] == 'V') &
            (df_processed['question_type'] == 'CR') &
            (df_processed['question_time'].notna()) &
            (df_processed['question_time'] > v_cr_threshold) &
            (~df_processed['is_invalid'])
        )
        df_processed.loc[cr_overtime_mask, 'overtime'] = True
        print(f"Marked {cr_overtime_mask.sum()} CR questions as overtime (threshold: {v_cr_threshold:.1f} min).")
    # Note: Other subjects' overtime marking needs their specific logic/thresholds here or in their modules

    # Mark suspiciously fast for non-invalid rows
    for subject, avg_times in subject_avg_time_per_type.items():
         if not avg_times: continue # Skip if no avg times calculated
         subj_mask = df_processed['Subject'] == subject
         for q_type, avg_time in avg_times.items():
             if avg_time is None or pd.isna(avg_time): continue
             type_mask = df_processed['question_type'] == q_type
             fast_mask = (
                 subj_mask & type_mask &
                 df_processed['question_time'].notna() &
                 (df_processed['question_time'] < avg_time * V_SUSPICIOUS_FAST_MULTIPLIER) &
                 (~df_processed['is_invalid'])
             )
             df_processed.loc[fast_mask, 'suspiciously_fast'] = True
             num_fast = fast_mask.sum()
             if num_fast > 0: print(f"  Marked {num_fast} {subject}/{q_type} questions as suspiciously fast (< {avg_time * V_SUSPICIOUS_FAST_MULTIPLIER:.2f} min).")


    if df_processed.empty:
        print("No valid data remaining after filtering. Cannot perform diagnosis.")
        return "診斷終止：在時間有效性過濾後，沒有剩餘的有效數據可供分析。"

    # --- Dispatch to Subject-Specific Diagnosis ---
    print("\nDispatching data to subject-specific diagnosis modules...")
    subject_reports = []

    # Separate dataframes by Subject
    df_q = df_processed[df_processed['Subject'] == 'Q'].copy()
    df_v = df_processed[df_processed['Subject'] == 'V'].copy()
    df_di = df_processed[df_processed['Subject'] == 'DI'].copy()

    # === DEBUG START: Check df_q right after creation ===
    print(f"DEBUG: df_q shape after filtering by Subject: {df_q.shape}")
    if not df_q.empty and 'question_type' in df_q.columns:
        print(f"DEBUG: df_q['question_type'] value counts BEFORE run_q_diagnosis:\n{df_q['question_type'].value_counts(dropna=False)}")
    elif df_q.empty:
        print("DEBUG: df_q is EMPTY after filtering by Subject!")
    else:
        print("DEBUG: df_q is not empty but 'question_type' column is missing!")
    # === DEBUG END ===

    # Prepare data/results to pass to subject modules
    # Pass the filtered df, time pressure status, invalid count, average times per type
    # Note: exempted_skills is passed only to Q for now

    # Run Q Diagnosis if data exists
    if not df_q.empty:
        # Pass relevant info: df_q, time pressure for Q, num_invalid for Q
        q_invalid_count = df_processed[(df_processed['Subject'] == 'Q') & (df_processed['is_invalid'])].shape[0]
        q_report = run_q_diagnosis(df_q, subject_time_pressure_status.get('Q', False), q_invalid_count)
        subject_reports.append(q_report)
    else:
        print("No Q data found.")
        subject_reports.append("量化 (Quantitative) 部分無有效數據。")

    # Run V Diagnosis if data exists
    if not df_v.empty:
        # Pass relevant info: df_v, time pressure for V, num_invalid for V, avg times for V
        v_invalid_count = df_processed[(df_processed['Subject'] == 'V') & (df_processed['is_invalid'])].shape[0]
        v_avg_times = subject_avg_time_per_type.get('V', {})
        v_results, v_report = run_v_diagnosis(df_v, subject_time_pressure_status.get('V', False), v_invalid_count, v_avg_times)
        subject_reports.append(v_report)
    else:
        print("No V data found.")
        subject_reports.append("語文 (Verbal) 部分無有效數據。")

    # Run DI Diagnosis if data exists
    if not df_di.empty:
        # 根據 di_diagnostic.py 的函數簽名傳遞參數
        # 注意：run_di_diagnosis 只接受 df_di 一個參數，內部會自行處理時間壓力邏輯
        # 我們確保 df_di 包含所需的所有列和信息
        # Pass the unfiltered DI dataframe
        di_raw_df = df_processed[df_processed['Subject'] == 'DI'].copy() # Get raw DI data before global filtering
        if not di_raw_df.empty:
             print("DEBUG: >>>>>> Calling run_di_diagnosis with di_raw_df >>>>>>") # DEBUG
             di_results, di_report = run_di_diagnosis(di_raw_df)
             print("DEBUG: <<<<<< Returned from run_di_diagnosis <<<<<<") # DEBUG
             subject_reports.append(di_report)
        else:
             print("No DI data found after initial processing.")
             subject_reports.append("數據洞察 (Data Insights) 部分無數據。")
    else:
        print("No DI data found.")
        subject_reports.append("數據洞察 (Data Insights) 部分無數據。")

    # --- Calculate correct total invalid and valid counts AFTER all diagnoses ---
    q_invalid_count = df_processed[(df_processed['Subject'] == 'Q') & (df_processed['is_invalid'])].shape[0]
    v_invalid_count = df_processed[(df_processed['Subject'] == 'V') & (df_processed['is_invalid'])].shape[0]
    # Extract DI invalid count from results (handle potential absence)
    di_invalid_count = 0
    if 'di_results' in locals() and isinstance(di_results, dict):
        di_invalid_count = di_results.get('chapter_1', {}).get('invalid_questions_excluded', 0)
    
    correct_total_invalid = q_invalid_count + v_invalid_count + di_invalid_count
    correct_total_valid = len(df_processed) - correct_total_invalid
    print(f"\nFiltered out {correct_total_invalid} invalid questions ({q_invalid_count} Q, {v_invalid_count} V, {di_invalid_count} DI). Proceeding with {correct_total_valid} valid questions for detailed diagnosis.")

    # --- Combine Reports ---
    print("\nCombining subject reports...")
    final_report_str = "\n\n---\n\n".join(subject_reports) # Join reports with a separator

    print("Diagnosis process complete.")
    return final_report_str

# End of run_diagnosis function. No other code should follow.
