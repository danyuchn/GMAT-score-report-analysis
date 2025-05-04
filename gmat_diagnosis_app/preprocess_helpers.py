import pandas as pd
import numpy as np
import math

# --- Constants from Diagnostic Modules (Centralized) ---
# Quant
MAX_ALLOWED_TIME_Q = 45.0
TOTAL_QUESTIONS_Q = 21 # Assuming 21 based on test structure
Q_FAST_END_THRESHOLD_MINUTES = 1.0
Q_TIME_DIFF_PRESSURE_THRESHOLD = 3.0
LAST_THIRD_FRACTION_Q = 2/3 # Q uses last third check? (Verify this, DI uses it) - Assuming yes for now.

# DI
MAX_ALLOWED_TIME_DI = 45.0
TOTAL_QUESTIONS_DI = 20
DI_TIME_PRESSURE_THRESHOLD_MINUTES = 3.0
DI_INVALID_TIME_THRESHOLD_MINUTES = 1.0
LAST_THIRD_FRACTION_DI = 2/3

# Verbal
V_INVALID_TIME_HASTY_MIN = 1.0 # Main simple rule used here for initial suggestion
TOTAL_QUESTIONS_V = 23 # Assuming 23 based on test structure

# Tags
INVALID_DATA_TAG_Q = "數據無效：用時過短（受時間壓力影響）"
INVALID_DATA_TAG_DI = "數據無效：用時過短（受時間壓力影響）"
INVALID_DATA_TAG_V = "數據無效：用時過短（受時間壓力影響）"


def suggest_invalid_questions(df, time_pressure_status_map):
    """
    Suggests invalid questions based on predefined rules for Q, DI, and V sections.
    This function is intended for PREPROCESSING before user review.
    It prioritizes 'is_manually_invalid' and only suggests automatic invalidation
    if the question is not already manually marked invalid.

    Args:
        df (pd.DataFrame): Combined DataFrame with Q, DI, V data.
                           Requires columns: 'Subject', 'question_position', 'question_time',
                           and optionally 'is_manually_invalid'.
        time_pressure_status_map (dict): A dictionary mapping section ('Q', 'DI', 'V')
                                         to its time pressure status (True/False).

    Returns:
        pd.DataFrame: DataFrame with an 'is_invalid' column populated based on
                      manual flags and automatic suggestions.
                      The original 'is_manually_invalid' column is preserved.
                      A column 'is_auto_suggested_invalid' is added for clarity.
    """
    print("DEBUG: >>> Entering suggest_invalid_questions preprocess function >>>")
    df_processed = df.copy()

    # --- Initialize Columns ---
    if 'is_manually_invalid' not in df_processed.columns:
        print("DEBUG: 'is_manually_invalid' column not found. Initializing to False.")
        df_processed['is_manually_invalid'] = False
    else:
        df_processed['is_manually_invalid'] = df_processed['is_manually_invalid'].fillna(False).astype(bool)

    # Initialize suggestion column
    df_processed['is_auto_suggested_invalid'] = False
    
    # Ensure necessary columns for calculation exist
    if 'question_position' not in df_processed.columns or 'question_time' not in df_processed.columns:
        print(f"WARNING: Missing position or time columns in input DataFrame. Skipping auto-suggestion.")
        # Still ensure the 'is_invalid' column exists for the return value structure
        df_processed['is_invalid'] = df_processed['is_manually_invalid']
        return df_processed


    # --- Apply Rules Per Section ---
    for section, section_df_view in df_processed.groupby('Subject'):
        print(f"DEBUG: Processing section: {section}")
        indices = section_df_view.index # Get indices for this section
        eligible_for_auto_mask = ~df_processed.loc[indices, 'is_manually_invalid']
        auto_invalid_section_mask = pd.Series(False, index=indices) # Initialize mask for this section

        time_pressure = time_pressure_status_map.get(section, False)
        print(f"DEBUG: Time pressure for {section}: {time_pressure}")

        if section == 'Q':
            total_questions = TOTAL_QUESTIONS_Q
            threshold = Q_FAST_END_THRESHOLD_MINUTES
            last_third_start = math.ceil(total_questions * LAST_THIRD_FRACTION_Q) + 1 # Check Q rules, DI uses 2/3
            # Apply Q rule (Pressure & Last Third & Fast End)
            if time_pressure and total_questions > 0:
                is_last_third = df_processed.loc[indices, 'question_position'] >= last_third_start
                is_fast_end = pd.to_numeric(df_processed.loc[indices, 'question_time'], errors='coerce') < threshold
                # Combine all conditions for this section's auto invalidation
                # Ensure to only apply where eligible (not manually invalid)
                auto_invalid_section_mask = is_last_third & is_fast_end & eligible_for_auto_mask
                print(f"DEBUG Q: Last third starts at {last_third_start}, Threshold < {threshold} min. Pressure={time_pressure}. Applying rule.")
            else:
                 print("DEBUG Q: Skipping auto-suggestion (no pressure or no questions).")

        elif section == 'DI':
            total_questions = TOTAL_QUESTIONS_DI
            threshold = DI_INVALID_TIME_THRESHOLD_MINUTES
            last_third_start = math.ceil(total_questions * LAST_THIRD_FRACTION_DI) + 1
            # Apply DI rule (Pressure & Last Third & Fast End)
            if time_pressure and total_questions > 0:
                is_last_third = df_processed.loc[indices, 'question_position'] >= last_third_start
                is_fast_end = pd.to_numeric(df_processed.loc[indices, 'question_time'], errors='coerce') < threshold
                # Combine all conditions for this section's auto invalidation
                auto_invalid_section_mask = is_last_third & is_fast_end & eligible_for_auto_mask
                print(f"DEBUG DI: Last third starts at {last_third_start}, Threshold < {threshold} min. Pressure={time_pressure}. Applying rule.")
            else:
                print("DEBUG DI: Skipping auto-suggestion (no pressure or no questions).")

        elif section == 'V':
            threshold = V_INVALID_TIME_HASTY_MIN
            # Apply V simple rule (Just < threshold, regardless of pressure/position for suggestion)
            # Note: The more complex pressure-based rule from v_diagnostic is NOT used here for simplicity.
            is_fast = pd.to_numeric(df_processed.loc[indices, 'question_time'], errors='coerce') < threshold
            # Combine all conditions for this section's auto invalidation
            auto_invalid_section_mask = is_fast & eligible_for_auto_mask
            print(f"DEBUG V: Threshold < {threshold} min. Applying simple rule.")

        # Update the main DataFrame's suggestion column for this section
        # Ensure the index alignment is correct when updating
        df_processed.loc[indices, 'is_auto_suggested_invalid'] = auto_invalid_section_mask[indices]


    # --- Create Final 'is_invalid' for Preview ---
    # This column reflects the initial state shown to the user for review.
    # It's True if manually flagged OR auto-suggested.
    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']

    num_manual = df_processed['is_manually_invalid'].sum()
    num_auto_suggested = df_processed['is_auto_suggested_invalid'].sum()
    num_final_initial = df_processed['is_invalid'].sum()

    print(f"DEBUG: Initial manual invalid: {num_manual}")
    print(f"DEBUG: Auto-suggested invalid (only if not manual): {num_auto_suggested}")
    print(f"DEBUG: Total initially marked invalid for preview: {num_final_initial}")
    print("DEBUG: <<< Exiting suggest_invalid_questions preprocess function <<<")

    # Return the DataFrame ready for preview.
    # The frontend should display 'is_invalid' as "是否草率做題？" and allow edits.
    return df_processed 