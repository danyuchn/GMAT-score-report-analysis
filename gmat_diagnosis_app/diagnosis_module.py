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
        tuple: A tuple containing two elements:
               1. A dictionary where keys are subject names ('Q', 'V', 'DI')
                  and values are the corresponding Markdown report strings.
                  Returns an empty dictionary or dictionary with error messages if input is invalid
                  or no valid data remains after filtering.
               2. The processed DataFrame with additional diagnostic fields:
                  - time_performance_category: Classification based on time and correctness
                  - is_sfe: Boolean indicating if question is a Special Focus Error
                  - diagnostic_params_list: List of Chinese diagnostic labels
    """

    # --- 0. Initial Validation ---
    # Define the required columns, including 'Subject'
    required_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'Subject']
    if not isinstance(df, pd.DataFrame):
         print("Invalid input: Input is not a pandas DataFrame.")
         return "錯誤：輸入數據格式無效。", pd.DataFrame()

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Invalid input DataFrame. Missing required columns: {missing_cols}")
        # Provide a more informative error message
        return f"錯誤：輸入數據缺少必要的欄位：{', '.join(missing_cols)}。請檢查上傳的 Excel 文件。", pd.DataFrame()

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

        # Invalid marking logic for V and Q is moved to their respective submodules.
        # DI invalid logic is already handled in di_diagnostic.py.

    # --- Global Rule Application: Overtime (CR only here), Suspiciously Fast ---
    # Note: Invalid marking is now done within subject-specific modules.
    # We apply Overtime and Suspiciously Fast flags here *before* passing to submodules.
    # Submodules might later overwrite/ignore these flags based on their own invalid logic.
    
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
        return "診斷終止：在時間有效性過濾後，沒有剩餘的有效數據可供分析。", pd.DataFrame()

    # --- Dispatch to Subject-Specific Diagnosis ---
    print("\nDispatching data to subject-specific diagnosis modules...")
    subject_report_dict = {} # Initialize dictionary to store reports by subject

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

    # List to collect processed dataframes from subject modules
    processed_dfs_list = []

    # Run Q diagnosis if data exists
    if not df_q.empty:
        try:
            print("DEBUG (diagnosis_module): Running Q Diagnosis...")
            q_results, q_report_str, df_q_processed = run_q_diagnosis(df_q, subject_time_pressure_status.get('Q', False))
            subject_report_dict['Q'] = q_report_str
            # --- DEBUG: Check Q columns before adding --- 
            print(f"DEBUG (diagnosis_module): Columns returned from run_q_diagnosis: {df_q_processed.columns.tolist()}")
            if 'overtime' not in df_q_processed.columns:
                print("ERROR: 'overtime' column MISSING in df_q_processed!")
            # --- DEBUG: Check if Q DataFrame is empty --- 
            print(f"DEBUG (diagnosis_module): Is df_q_processed empty? {df_q_processed.empty}")
            # --- END DEBUG --- 
            processed_dfs_list.append(df_q_processed)
        except Exception as e:
            print(f"Error during Q diagnosis: {e}")
            subject_report_dict['Q'] = f"Q 科目診斷出錯: {e}"

    # Run V diagnosis if data exists
    if not df_v.empty:
        try:
            print("DEBUG (diagnosis_module): Running V Diagnosis...")
            v_results, v_report_str, df_v_processed = run_v_diagnosis(df_v, subject_time_pressure_status.get('V', False), subject_avg_time_per_type.get('V', {}))
            subject_report_dict['V'] = v_report_str
            # --- DEBUG: Check V columns before adding --- 
            print(f"DEBUG (diagnosis_module): Columns returned from run_v_diagnosis: {df_v_processed.columns.tolist()}")
            if 'overtime' not in df_v_processed.columns:
                print("ERROR: 'overtime' column MISSING in df_v_processed!")
            # --- END DEBUG --- 
            processed_dfs_list.append(df_v_processed)
        except Exception as e:
            print(f"Error during V diagnosis: {e}")
            subject_report_dict['V'] = f"V 科目診斷出錯: {e}"

    # Run DI diagnosis if data exists
    if not df_di.empty:
        try:
            print("DEBUG (diagnosis_module): Running DI Diagnosis...")
            # Pass the DI specific dataframe to run_di_diagnosis
            di_results, di_report_str, df_di_processed = run_di_diagnosis(df_di) # df_di is already filtered
            subject_report_dict['DI'] = di_report_str
            # --- DEBUG: Check DI columns before adding --- 
            print(f"DEBUG (diagnosis_module): Columns returned from run_di_diagnosis: {df_di_processed.columns.tolist()}")
            if 'overtime' not in df_di_processed.columns:
                print("ERROR: 'overtime' column MISSING in df_di_processed!")
            # --- END DEBUG --- 
            processed_dfs_list.append(df_di_processed)
        except Exception as e:
            print(f"Error during DI diagnosis: {e}")
            subject_report_dict['DI'] = f"DI 科目診斷出錯: {e}"

    # === Concatenate results ===
    df_final_for_diagnosis = None
    if processed_dfs_list:
        try:
            print("DEBUG (diagnosis_module): Concatenating processed dataframes...")
            df_final_for_diagnosis = pd.concat(processed_dfs_list, ignore_index=True)
            # --- DEBUG: Check columns AFTER concatenation --- 
            print(f"DEBUG (diagnosis_module): Columns after concat: {df_final_for_diagnosis.columns.tolist()}")
            if 'overtime' not in df_final_for_diagnosis.columns:
                print("ERROR: 'overtime' column MISSING after concatenation!")
            # --- Check Subjects After Concat --- 
            if df_final_for_diagnosis is not None and 'Subject' in df_final_for_diagnosis.columns:
                 print(f"DEBUG (diagnosis_module): Subjects AFTER concat: {df_final_for_diagnosis['Subject'].unique()}")
            # --- END DEBUG --- 
            elif df_final_for_diagnosis['overtime'].isnull().any():
                 print("WARNING: 'overtime' column contains NULL values after concatenation!")
            # --- END DEBUG --- 
        except Exception as e:
            print(f"Error during concatenation of diagnosis results: {e}")
            return f"錯誤：合併診斷結果時出錯: {e}", pd.DataFrame() # Return error and empty df
    else:
        print("No processed dataframes available to concatenate.")
        # Return message indicating no valid data could be processed
        # Check if any reports were generated (e.g., due to errors)
        if subject_report_dict:
             # Return the reports generated so far, likely error messages
             return subject_report_dict, pd.DataFrame()
        else:
             return "錯誤：沒有任何科目數據能夠成功處理。", pd.DataFrame()

    # Ensure the final dataframe is not None before returning
    if df_final_for_diagnosis is None:
         df_final_for_diagnosis = pd.DataFrame()
         print("WARNING: df_final_for_diagnosis ended up being None, returning empty DataFrame.")

    # Final check of columns before returning
    print(f"DEBUG (diagnosis_module): Columns in df_final_for_diagnosis before return: {df_final_for_diagnosis.columns.tolist()}")
    # --- Add Subject Check Before Return --- 
    if df_final_for_diagnosis is not None and 'Subject' in df_final_for_diagnosis.columns:
        print(f"DEBUG (diagnosis_module): Subjects BEFORE return: {df_final_for_diagnosis['Subject'].unique()}")
    # --- End Subject Check --- 
    
    return subject_report_dict, df_final_for_diagnosis

# End of run_diagnosis function. No other code should follow.
