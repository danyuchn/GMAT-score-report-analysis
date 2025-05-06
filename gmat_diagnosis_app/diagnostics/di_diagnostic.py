import pandas as pd
import logging

# Import constants needed for the wrapper function
from .di_modules.constants import MAX_ALLOWED_TIME_DI, TIME_PRESSURE_THRESHOLD_DI

# Import the main logic function from the sub-module
from .di_modules.main import run_di_diagnosis_logic

# Keep the original signature for external calls
def run_di_diagnosis_processed(df_di_processed, di_time_pressure_status):
    """
    Wrapper for the main DI diagnosis logic housed in di_modules.main.

    Args:
        df_di_processed (pd.DataFrame): DataFrame with DI responses, preprocessed with 'is_invalid'.
        di_time_pressure_status (bool): Time pressure status for DI.

    Returns:
        dict: A dictionary containing the results of the DI diagnosis, structured by chapter.
        str: A string containing the summary report for the DI section.
        pd.DataFrame: The processed DI DataFrame with added diagnostic columns.
    """
    # Delegate to the actual implementation in main.py
    return run_di_diagnosis_logic(df_di_processed, di_time_pressure_status)

# --- DI Diagnosis Wrapper (to match expected import signature in diagnosis_module.py) ---
def run_di_diagnosis(df_di):
    """
    Wrapper function that matches the expected signature in diagnosis_module.py.
    Calculates time pressure status and then calls run_di_diagnosis_processed.
    
    Args:
        df_di (pd.DataFrame): DataFrame containing DI responses.
        
    Returns:
        Tuple: (results_dict, report_str, processed_df) - Same as run_di_diagnosis_processed
    """
    # Calculate time pressure status for DI
    if df_di.empty:
        # Return empty results consistent with the main logic's empty case
        empty_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type',
                      'question_fundamental_skill', 'content_domain', 'Subject', 'is_invalid',
                      'overtime', 'suspiciously_fast', 'msr_group_id', 'msr_group_total_time',
                      'msr_reading_time', 'is_first_msr_q', 'is_sfe',
                      'time_performance_category', 'diagnostic_params_list']
        df_empty_return = pd.DataFrame(columns=empty_cols)
        df_empty_return['Subject'] = 'DI'
        return {}, "Data Insights (DI) 部分無數據可供診斷。", df_empty_return
        
    # Convert question_time to numeric if needed
    if 'question_time' not in df_di.columns:
        logging.error("[run_di_diagnosis wrapper] Input DataFrame missing 'question_time'.")
        return {}, "Data Insights (DI) 資料缺少必要欄位：question_time。", pd.DataFrame(columns=['Subject']) # Minimal error return
    
    try:
        # Ensure numeric for calculation
        df_di['question_time'] = pd.to_numeric(df_di['question_time'], errors='coerce')
        total_test_time = df_di['question_time'].sum(skipna=True)
        time_diff = MAX_ALLOWED_TIME_DI - total_test_time
        
        # Determine time pressure (using imported constants)
        # Keeping the simple rule from the original wrapper for consistency
        di_time_pressure_status = time_diff < TIME_PRESSURE_THRESHOLD_DI
    except Exception as e:
        logging.error(f"[run_di_diagnosis wrapper] Error calculating time pressure: {e}", exc_info=True)
        # Handle error: maybe default pressure to False and proceed, or return error
        return {}, f"DI 診斷前計算時間壓力時出錯: {e}", pd.DataFrame(columns=['Subject'])
    
    # Call the main processor (which now calls the logic from main.py)
    return run_di_diagnosis_processed(df_di, di_time_pressure_status)