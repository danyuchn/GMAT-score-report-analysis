import pandas as pd
import numpy as np
import logging # 引入 logging 模組

# Import translation function
from gmat_diagnosis_app.i18n import translate as t

# Import subject-specific diagnosis runners
from gmat_diagnosis_app.diagnostics.q_diagnostic import run_q_diagnosis
from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis

# --- Constants from V-Doc Chapter 1 ---
V_MAX_ALLOWED_TIME = 45.0 # minutes
V_TIME_PRESSURE_THRESHOLD_DIFF = 1.0 # minutes difference
V_CR_OVERTIME_THRESHOLD_PRESSURE_TRUE = 2.0 # minutes
V_CR_OVERTIME_THRESHOLD_PRESSURE_FALSE = 2.5 # minutes
V_SUSPICIOUS_FAST_MULTIPLIER = 0.5

# --- Constants from DI-Doc Chapter 0 & 1 --- - Removed (保持移除狀態)

# --- Logging Configuration (Optional but recommended) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
               2. The processed DataFrame with additional diagnostic fields, or an empty DataFrame on failure.
    """

    # --- 0. Initial Validation ---
    required_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'Subject']
    if not isinstance(df, pd.DataFrame):
         logging.error("Invalid input: Input is not a pandas DataFrame.")
         return t("data_input_format_invalid"), pd.DataFrame()

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = t("data_input_missing_columns").format(', '.join(missing_cols))
        logging.error(f"Invalid input DataFrame. Missing required columns: {missing_cols}")
        return error_msg, pd.DataFrame()

    df_processed = df.copy()

    # --- Data Type Conversion and Cleaning ---
    try:
        df_processed['question_time'] = pd.to_numeric(df_processed['question_time'], errors='coerce')
        df_processed['question_position'] = pd.to_numeric(df_processed['question_position'], errors='coerce')
        df_processed['question_difficulty'] = pd.to_numeric(df_processed['question_difficulty'], errors='coerce')
        if df_processed['is_correct'].dtype == 'object':
            df_processed['is_correct'] = df_processed['is_correct'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False})
        df_processed['is_correct'] = df_processed['is_correct'].astype(bool)
    except Exception as e:
        logging.error(f"Error during data type conversion: {e}")
        return t("data_type_conversion_failed").format(e), pd.DataFrame()

    # --- Initialize internal columns ---
    df_processed['is_invalid'] = False
    df_processed['overtime'] = False
    df_processed['suspiciously_fast'] = False

    # --- 1. Overall Time Strategy & Data Validity (Chapter 1 Logic - Applied Per Subject) ---
    logging.info("Starting Chapter 1: Time Strategy & Validity Analysis...")
    subjects_present = df_processed['Subject'].unique()
    subject_time_pressure_status = {}
    subject_avg_time_per_type = {}

    subject_time_limits = {'Q': 45.0, 'V': V_MAX_ALLOWED_TIME, 'DI': 45.0} # DI max time defined here

    for subject in subjects_present:
        # logging.info(f"  Processing Subject: {subject}")
        if subject not in subject_time_limits:
            logging.warning(f"Unrecognized subject '{subject}'. Skipping time analysis for this subject.")
            subject_time_pressure_status[subject] = 'Unknown'
            continue

        df_subj = df_processed[df_processed['Subject'] == subject] # No copy needed here for calculations
        if df_subj.empty:
            # logging.info(f"    Subject {subject}: No data found.")
            subject_time_pressure_status[subject] = False
            continue

        # Check for NaN/NaT in critical columns after conversion
        if df_subj['question_time'].isnull().any() or df_subj['question_position'].isnull().any():
             logging.warning(f"Subject {subject} has missing/non-numeric time or position data. Skipping detailed time analysis.")
             subject_time_pressure_status[subject] = 'Unknown'
             continue

        total_number_of_questions = len(df_subj)
        max_allowed_time = subject_time_limits.get(subject, 45.0)
        total_test_time = df_subj['question_time'].sum()
        time_diff = max_allowed_time - total_test_time
        # logging.info(f"    Subject {subject}: Total Time = {total_test_time:.2f} min, Allowed = {max_allowed_time:.1f} min, Diff = {time_diff:.2f} min")

        # Determine time pressure
        time_pressure = False
        if subject == 'V':
            if time_diff < V_TIME_PRESSURE_THRESHOLD_DIFF:
                time_pressure = True
                # logging.info(f"    Subject {subject}: Time Pressure Detected (V Logic: Diff < {V_TIME_PRESSURE_THRESHOLD_DIFF} min).")
        elif subject == 'DI':
            # logging.info(f"    Subject {subject}: Time pressure and validity handled within DI module.")
            time_pressure = False # Placeholder, DI module calculates the true value
        else: # Apply original logic for Q
             last_third_start_position = np.ceil(total_number_of_questions * 2 / 3)
             last_third_questions = df_subj[df_subj['question_position'] >= last_third_start_position]
             # Ensure time is not NaN before comparing
             fast_end_questions = last_third_questions[last_third_questions['question_time'].notna() & (last_third_questions['question_time'] < 1.0)]
             if time_diff <= 3.0 and not fast_end_questions.empty:
                 time_pressure = True
                 # logging.info(f"    Subject {subject}: Time Pressure Detected (Q Logic: Diff <= 3 min AND fast end questions exist).")

        subject_time_pressure_status[subject] = time_pressure

        # Calculate and store average time per type for this subject
        if 'question_type' in df_subj.columns:
             subject_avg_time_per_type[subject] = df_subj.groupby('question_type')['question_time'].mean().to_dict()
             # logging.info(f"      Avg time per type (min) for {subject}: {subject_avg_time_per_type[subject]}")
        else:
             subject_avg_time_per_type[subject] = {}
             logging.warning(f"      'question_type' column missing for {subject}, cannot calculate average times.")

    # --- Global Rule Application: Overtime (CR only here), Suspiciously Fast ---
    # Mark overtime for Q rows
    if 'Q' in subject_time_pressure_status:
        q_pressure = subject_time_pressure_status['Q']
        q_overtime_threshold = 2.5 if q_pressure else 3.0
        q_overtime_mask = (df_processed['Subject'] == 'Q') & (df_processed['question_time'] > q_overtime_threshold) & (~df_processed['is_invalid'])
        df_processed.loc[q_overtime_mask, 'overtime'] = True
        # logging.info(f"Marked {q_overtime_mask.sum()} Q questions as overtime (threshold: {q_overtime_threshold:.1f} min).")

    # Mark overtime for V-CR rows
    if 'V' in subject_time_pressure_status:
        v_pressure = subject_time_pressure_status['V']
        v_cr_threshold = V_CR_OVERTIME_THRESHOLD_PRESSURE_TRUE if v_pressure else V_CR_OVERTIME_THRESHOLD_PRESSURE_FALSE
        cr_overtime_mask = (df_processed['Subject'] == 'V') & (df_processed['question_type'] == 'CR') & (df_processed['question_time'] > v_cr_threshold) & (~df_processed['is_invalid'])
        df_processed.loc[cr_overtime_mask, 'overtime'] = True
        # logging.info(f"Marked {cr_overtime_mask.sum()} CR questions as overtime (threshold: {v_cr_threshold:.1f} min).")

    # Mark suspiciously fast (Optimized approach using transform)
    # Ensure 'question_type' exists before grouping
    if 'question_type' in df_processed.columns:
        # Calculate average time per Subject-Type group; use transform to align with original index
        df_processed['avg_time_per_type'] = df_processed.groupby(['Subject', 'question_type'])['question_time'].transform('mean')
        
        suspicious_fast_mask = (
            df_processed['question_time'].notna() &
            df_processed['avg_time_per_type'].notna() &
            (df_processed['question_time'] < df_processed['avg_time_per_type'] * V_SUSPICIOUS_FAST_MULTIPLIER) &
            (~df_processed['is_invalid'])
        )
        df_processed.loc[suspicious_fast_mask, 'suspiciously_fast'] = True
        # logging.info(f"Marked {suspicious_fast_mask.sum()} questions as suspiciously fast.")

        # Remove the temporary average time column
        df_processed.drop(columns=['avg_time_per_type'], inplace=True)
    else:
        logging.warning("Cannot mark suspiciously fast questions: 'question_type' column missing.")


    # --- Dispatch to Subject-Specific Diagnosis (Simplified) ---
    logging.info("Dispatching data to subject-specific diagnosis modules...")
    subject_report_dict = {}
    processed_dfs_list = []

    # Define runners and their specific argument needs
    # Functions are expected to return (results, report_str, df_processed)
    # We capture report_str and df_processed
    diagnosis_runners = {
        'Q': {'func': run_q_diagnosis, 'needs': ['pressure']},
        'V': {'func': run_v_diagnosis, 'needs': ['pressure', 'avg_times']},
        'DI': {'func': run_di_diagnosis, 'needs': []}
    }

    for subject_code, runner_info in diagnosis_runners.items():
        if subject_code not in subjects_present:
            continue # Skip if subject not in the input data

        df_subj = df_processed[df_processed['Subject'] == subject_code].copy() # Copy needed before passing to external func
        if df_subj.empty:
            # logging.info(f"Skipping {subject_code} diagnosis: No data for this subject.")
            continue

        try:
            logging.info(f"Running {subject_code} Diagnosis...")
            diagnostic_func = runner_info['func']
            args_to_pass = [df_subj] # First argument is always the dataframe

            # Prepare additional arguments based on 'needs'
            if 'pressure' in runner_info['needs']:
                args_to_pass.append(subject_time_pressure_status.get(subject_code, False)) # Use calculated pressure
            if 'avg_times' in runner_info['needs']:
                 args_to_pass.append(subject_avg_time_per_type.get(subject_code, {})) # Use calculated avg times

            # Call the diagnostic function
            # Assuming the return signature is (results, report_str, df_processed_subj)
            _, report_str, df_subj_processed = diagnostic_func(*args_to_pass)

            subject_report_dict[subject_code] = report_str
            if not df_subj_processed.empty:
                 processed_dfs_list.append(df_subj_processed)
            else:
                 logging.warning(f"{subject_code} diagnosis returned an empty DataFrame.")
            # logging.info(f"{subject_code} diagnosis complete.")

        except Exception as e:
            logging.error(f"Error during {subject_code} diagnosis: {e}", exc_info=True) # Log traceback
            subject_report_dict[subject_code] = t("diagnosis_error").format(subject_code, e)

    # === Concatenate results ===
    df_final_processed = pd.DataFrame() # Initialize as empty DataFrame
    if processed_dfs_list:
        try:
            # Check for consistent columns before concatenating if needed, or handle potential errors
            # Basic concatenation:
            df_final_processed = pd.concat(processed_dfs_list, ignore_index=True, sort=False) # Use sort=False to maintain column order if possible
            logging.info("Successfully concatenated processed dataframes.")
            # Final check for essential columns if necessary
            # e.g., if 'overtime' must exist:
            if 'overtime' not in df_final_processed.columns:
                 logging.warning("'overtime' column missing after concatenation. Adding it with False.")
                 df_final_processed['overtime'] = False # Or handle based on requirements
            # Check if concatenation resulted in empty DataFrame unexpectedly
            if df_final_processed.empty and any(not df.empty for df in processed_dfs_list):
                logging.warning("Concatenation resulted in an empty DataFrame unexpectedly.")

        except Exception as e:
            logging.error(f"Error during concatenation of diagnosis results: {e}", exc_info=True)
            # Decide how to return: maybe reports generated so far + empty df
            return subject_report_dict, pd.DataFrame(t("concatenation_error").format(e))
    elif not subject_report_dict: # No dfs processed AND no reports (likely indicates no data passed initial checks)
        logging.warning("No data processed by any subject module and no reports generated.")
        return t("no_data_processed"), pd.DataFrame()
    else: # No dfs processed, but maybe reports (e.g., errors occurred) exist
        logging.warning("No processed dataframes available to concatenate. Check reports for errors.")
        # Return any reports generated (likely errors) and an empty DataFrame
        return subject_report_dict, pd.DataFrame()


    logging.info(f"Diagnosis finished. Returning reports for subjects: {list(subject_report_dict.keys())} and DataFrame with shape {df_final_processed.shape}.")
    return subject_report_dict, df_final_processed

# End of run_diagnosis function.