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
Q_OVERTIME_THRESHOLD_PRESSURE = 2.5 # Added: Q overtime threshold under pressure
Q_OVERTIME_THRESHOLD_NO_PRESSURE = 3.0 # Added: Q overtime threshold without pressure

# DI
MAX_ALLOWED_TIME_DI = 45.0
TOTAL_QUESTIONS_DI = 20
DI_TIME_PRESSURE_THRESHOLD_MINUTES = 3.0
DI_INVALID_TIME_THRESHOLD_MINUTES = 1.0
LAST_THIRD_FRACTION_DI = 2/3
# Added: DI overtime thresholds (values from di_diagnostic logic or docs)
DI_OVERTIME_THRESHOLD_TPA_PRESSURE = 3.0
DI_OVERTIME_THRESHOLD_TPA_NO_PRESSURE = 3.5
DI_OVERTIME_THRESHOLD_GT_PRESSURE = 3.0
DI_OVERTIME_THRESHOLD_GT_NO_PRESSURE = 3.5
DI_OVERTIME_THRESHOLD_DS_PRESSURE = 2.0
DI_OVERTIME_THRESHOLD_DS_NO_PRESSURE = 2.5
DI_MSR_TARGET_TIME_PRESSURE = 6.0
DI_MSR_TARGET_TIME_NO_PRESSURE = 7.0

# Verbal
V_INVALID_TIME_HASTY_MIN = 1.0 # Main simple rule used here for initial suggestion
TOTAL_QUESTIONS_V = 23 # Assuming 23 based on test structure
MAX_ALLOWED_TIME_V = 45.0 # Added: Max allowed time for Verbal
# Added: V overtime thresholds (values from v_diagnostic logic or docs)
V_OVERTIME_THRESHOLD_CR_PRESSURE = 2.0
V_OVERTIME_THRESHOLD_CR_NO_PRESSURE = 2.5
V_RC_TARGET_TIME_3Q_PRESSURE = 6.0
V_RC_TARGET_TIME_4Q_PRESSURE = 8.0
V_RC_TARGET_TIME_3Q_NO_PRESSURE = 7.0
V_RC_TARGET_TIME_4Q_NO_PRESSURE = 9.0
V_RC_INDIVIDUAL_Q_THRESHOLD = 2.0


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
        # Ensure boolean type and handle potential NaNs introduced by editor
        df_processed['is_manually_invalid'] = df_processed['is_manually_invalid'].fillna(False).astype(bool)


    # Initialize suggestion column
    df_processed['is_auto_suggested_invalid'] = False
    
    # Ensure necessary columns for calculation exist
    if 'question_position' not in df_processed.columns or 'question_time' not in df_processed.columns:
        print(f"WARNING: Missing position or time columns in input DataFrame for invalid suggestion. Skipping.")
        # Still ensure the 'is_invalid' column exists for the return value structure
        df_processed['is_invalid'] = df_processed['is_manually_invalid']
        return df_processed


    # --- Apply Rules Per Section ---
    for section, section_df_view in df_processed.groupby('Subject'):
        print(f"DEBUG: Suggesting invalid for section: {section}")
        indices = section_df_view.index # Get indices for this section
        eligible_for_auto_mask = ~df_processed.loc[indices, 'is_manually_invalid']
        auto_invalid_section_mask = pd.Series(False, index=indices) # Initialize mask for this section

        time_pressure = time_pressure_status_map.get(section, False)
        print(f"DEBUG: Time pressure for {section}: {time_pressure}")
        
        # Ensure question_time is numeric for comparisons
        q_time_numeric = pd.to_numeric(df_processed.loc[indices, 'question_time'], errors='coerce')

        if section == 'Q':
            total_questions = TOTAL_QUESTIONS_Q
            threshold = Q_FAST_END_THRESHOLD_MINUTES
            last_third_start = math.ceil(total_questions * LAST_THIRD_FRACTION_Q) + 1 # Check Q rules, DI uses 2/3
            # Apply Q rule (Pressure & Last Third & Fast End)
            if time_pressure and total_questions > 0:
                is_last_third = df_processed.loc[indices, 'question_position'] >= last_third_start
                is_fast_end = q_time_numeric < threshold
                # Combine all conditions for this section's auto invalidation
                # Ensure to only apply where eligible (not manually invalid)
                auto_invalid_section_mask = is_last_third & is_fast_end & eligible_for_auto_mask
                print(f"DEBUG Q: Last third starts at {last_third_start}, Threshold < {threshold} min. Pressure={time_pressure}. Applying rule.")
            else:
                 print("DEBUG Q: Skipping invalid auto-suggestion (no pressure or no questions).")

        elif section == 'DI':
            total_questions = TOTAL_QUESTIONS_DI
            threshold = DI_INVALID_TIME_THRESHOLD_MINUTES
            last_third_start = math.ceil(total_questions * LAST_THIRD_FRACTION_DI) + 1
            # Apply DI rule (Pressure & Last Third & Fast End)
            if time_pressure and total_questions > 0:
                is_last_third = df_processed.loc[indices, 'question_position'] >= last_third_start
                is_fast_end = q_time_numeric < threshold
                # Combine all conditions for this section's auto invalidation
                auto_invalid_section_mask = is_last_third & is_fast_end & eligible_for_auto_mask
                print(f"DEBUG DI: Last third starts at {last_third_start}, Threshold < {threshold} min. Pressure={time_pressure}. Applying rule.")
            else:
                print("DEBUG DI: Skipping invalid auto-suggestion (no pressure or no questions).")

        elif section == 'V':
            threshold = V_INVALID_TIME_HASTY_MIN
            # Apply V simple rule (Just < threshold, regardless of pressure/position for suggestion)
            # This is the 'hasty' check from the V doc (1.0 min OR < 50% of avg first third)
            # We only implement the 1.0 min part here for simplicity in preprocessing suggestion
            # The complex V invalid logic involving first third avg is complex for this stage
            is_fast = q_time_numeric < threshold
            # V invalid logic requires time_pressure=True
            if time_pressure:
                auto_invalid_section_mask = is_fast & eligible_for_auto_mask
                print(f"DEBUG V: Pressure=True. Threshold < {threshold} min. Applying simple invalid rule.")
            else:
                 print("DEBUG V: Skipping invalid auto-suggestion (no pressure).")


        # Update the main DataFrame's suggestion column for this section
        # Ensure the index alignment is correct when updating
        # Use .loc with the boolean mask directly for potentially safer assignment
        df_processed.loc[indices[auto_invalid_section_mask], 'is_auto_suggested_invalid'] = True


    # --- Create Final 'is_invalid' for Preview ---\
    # This column reflects the initial state shown to the user for review.
    # It's True if manually flagged OR auto-suggested.
    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']

    num_manual = df_processed['is_manually_invalid'].sum()
    num_auto_suggested = df_processed['is_auto_suggested_invalid'].sum()
    num_final_initial = df_processed['is_invalid'].sum()

    print(f"DEBUG: Initial manual invalid: {num_manual}")
    print(f"DEBUG: Auto-suggested invalid (only if not manual): {num_auto_suggested}")
    print(f"DEBUG: Total initially marked invalid for preview: {num_final_initial}")
    print("DEBUG: <<< Exiting suggest_invalid_questions preprocess function <<<\n")

    # Return the DataFrame ready for preview.
    # The frontend should display 'is_invalid' as "是否草率做題？" and allow edits.
    # The diagnostic modules will use this 'is_invalid' column (final state after user edit)
    return df_processed


def calculate_overtime(df, time_pressure_status_map):
    """
    Calculates the 'overtime' status for each question based on subject-specific rules
    and the time pressure status.

    Args:
        df (pd.DataFrame): Combined DataFrame with Q, DI, V data.
                           Requires columns: 'Subject', 'question_time', 'question_type'.
                           For RC, requires 'rc_group_id' and 'question_position'.
                           For MSR, requires 'msr_group_id'.
        time_pressure_status_map (dict): A dictionary mapping section ('Q', 'DI', 'V')
                                         to its time pressure status (True/False).

    Returns:
        pd.DataFrame: DataFrame with an added boolean 'overtime' column.
                      Returns the original df with a warning if needed columns are missing.
    """
    print("DEBUG: >>> Entering calculate_overtime preprocess function >>>")
    df_processed = df.copy()
    df_processed['overtime'] = False # Initialize column

    # --- Preprocess Verbal Data FIRST to get RC info --- 
    df_processed = preprocess_verbal_data(df_processed)
    # --- End Verbal Preprocessing --- 

    # --- Check required columns ---
    required_cols = ['Subject', 'question_time', 'question_type']
    missing_cols = [col for col in required_cols if col not in df_processed.columns]
    if missing_cols:
        print(f"WARNING: Missing required columns for overtime calculation: {missing_cols}. Skipping.")
        return df_processed # Return original df without 'overtime' calculation

    # Ensure question_time is numeric, coercing errors
    df_processed['question_time_numeric'] = pd.to_numeric(df_processed['question_time'], errors='coerce')

    # --- Apply Rules Per Section ---
    for section, section_df_view in df_processed.groupby('Subject'):
        print(f"DEBUG: Calculating overtime for section: {section}")
        indices = section_df_view.index
        time_pressure = time_pressure_status_map.get(section, False)
        print(f"DEBUG: Time pressure for {section}: {time_pressure}")

        section_overtime_mask = pd.Series(False, index=indices) # Initialize mask for this section

        if section == 'Q':
            threshold = Q_OVERTIME_THRESHOLD_PRESSURE if time_pressure else Q_OVERTIME_THRESHOLD_NO_PRESSURE
            print(f"DEBUG Q: Overtime threshold: {threshold} min.")
            # Compare numeric time with threshold, handle NaN times as not overtime
            is_overtime = df_processed.loc[indices, 'question_time_numeric'] > threshold
            section_overtime_mask = is_overtime.fillna(False)

        elif section == 'DI':
            print(f"DEBUG DI: Processing overtime based on question_type...")
            # Check for MSR group ID
            has_msr_group_id = 'msr_group_id' in df_processed.columns
            if not has_msr_group_id:
                print("WARNING DI: Missing 'msr_group_id' column, MSR group overtime cannot be calculated.")

            # --- Pre-calculate MSR Group Times (if possible) ---
            msr_group_overtime_map = {}
            if has_msr_group_id:
                # Filter only DI rows for MSR grouping
                msr_groups = df_processed.loc[indices][df_processed.loc[indices, 'question_type'] == 'MSR'].groupby('msr_group_id')
                for group_id, group_df in msr_groups:
                    # Ensure group_id is not NaN or similar invalid values before proceeding
                    if pd.isna(group_id):
                         # print(f"  WARN MSR: Skipping group with invalid ID: {group_id}")
                         continue
                    group_total_time = group_df['question_time_numeric'].sum()
                    target_time = DI_MSR_TARGET_TIME_PRESSURE if time_pressure else DI_MSR_TARGET_TIME_NO_PRESSURE
                    is_group_overtime = group_total_time > target_time
                    msr_group_overtime_map[group_id] = is_group_overtime
                    # print(f"  DEBUG MSR Group {group_id}: Total Time={group_total_time:.2f}, Target={target_time:.2f}, Overtime={is_group_overtime}")
            # --- End MSR Pre-calculation ---

            di_overtime_conditions = []
            for idx in indices:
                q_type = df_processed.loc[idx, 'question_type']
                q_time = df_processed.loc[idx, 'question_time_numeric']
                overtime_flag = False
                if pd.isna(q_time): # Skip if time is NaN
                    continue

                if q_type == 'TPA':
                    threshold = DI_OVERTIME_THRESHOLD_TPA_PRESSURE if time_pressure else DI_OVERTIME_THRESHOLD_TPA_NO_PRESSURE
                    if q_time > threshold: overtime_flag = True
                elif q_type == 'GT':
                    threshold = DI_OVERTIME_THRESHOLD_GT_PRESSURE if time_pressure else DI_OVERTIME_THRESHOLD_GT_NO_PRESSURE
                    if q_time > threshold: overtime_flag = True
                elif q_type == 'DS':
                    threshold = DI_OVERTIME_THRESHOLD_DS_PRESSURE if time_pressure else DI_OVERTIME_THRESHOLD_DS_NO_PRESSURE
                    if q_time > threshold: overtime_flag = True
                elif q_type == 'MSR':
                    if has_msr_group_id:
                        group_id = df_processed.loc[idx, 'msr_group_id']
                        # Check if group_id is valid before looking up
                        if pd.notna(group_id) and group_id in msr_group_overtime_map:
                            overtime_flag = msr_group_overtime_map[group_id]
                        else:
                             # Handle cases where group_id might be NaN or unexpected
                             # print(f"  WARN MSR: Group ID {group_id} not found in map or invalid for index {idx}.")
                             pass # Keep overtime_flag as False
                    else:
                        # No group ID, cannot determine MSR group overtime
                        pass # Keep overtime_flag as False

                di_overtime_conditions.append(overtime_flag)
            
            # Assign the calculated overtime flags to the section mask
            # This assumes di_overtime_conditions list matches the order and length of valid indices
            valid_indices = df_processed.loc[indices, 'question_time_numeric'].dropna().index
            if len(di_overtime_conditions) == len(valid_indices):
                 section_overtime_mask.loc[valid_indices] = di_overtime_conditions
            else:
                 # This case should ideally not happen if NaN handling is correct
                 print(f"ERROR DI: Mismatch in length between overtime conditions ({len(di_overtime_conditions)}) and valid indices ({len(valid_indices)}). Overtime assignment may be incorrect.")
                 # Fallback: Try assigning based on the length of the conditions list, assuming order matches
                 if len(di_overtime_conditions) <= len(indices):
                      section_overtime_mask.iloc[:len(di_overtime_conditions)] = di_overtime_conditions
                 else:
                      section_overtime_mask = pd.Series(di_overtime_conditions[:len(indices)], index=indices) # Truncate conditions

            print(f"DEBUG DI: Calculated overtime flags (count True): {section_overtime_mask.sum()}")


        elif section == 'V':
            print(f"DEBUG V: Processing overtime based on question_type...")
            # Check if required RC columns were successfully added by preprocessing
            has_rc_cols = 'rc_group_id' in df_processed.columns and \
                          'rc_group_total_time' in df_processed.columns and \
                          'rc_reading_time' in df_processed.columns
            # REMOVED Warning about missing columns, should be handled by preprocess_verbal_data

            df_v_section = df_processed.loc[indices].copy() # Work on a copy for V section
            # Initialize columns specific to V overtime calculation within this scope
            df_v_section['group_overtime'] = False
            df_v_section['individual_overtime'] = False

            # --- Calculate RC Group Overtime --- 
            # This part is now implicitly handled by checking the precalculated group total time later
            # No need for a separate loop here just to set group_overtime flag
            # if has_rc_cols:
            #     rc_groups = df_v_section[df_v_section['question_type'] == 'RC'].groupby('rc_group_id')
            #     ...

            # --- Calculate RC Individual Overtime & CR Overtime --- 
            # No need to pre-calculate reading times, they are already in df_processed

            # --- Iterate through V questions --- 
            for idx in df_v_section.index:
                q_time = df_v_section.loc[idx, 'question_time']
                q_type = df_v_section.loc[idx, 'question_type'] # Get type for this row
                q_pos = df_v_section.loc[idx, 'question_position'] # Get position for debug

                if pd.isna(q_time) or pd.isna(q_type):
                    # print(f"  DEBUG V OT Skip: Index {idx}, Missing Time or Type") # Optional debug
                    continue # Skip if time or type is missing

                if q_type == 'Critical Reasoning':
                    threshold = V_OVERTIME_THRESHOLD_CR_PRESSURE if time_pressure else V_OVERTIME_THRESHOLD_CR_NO_PRESSURE
                    if q_time > threshold:
                         # Use .loc for direct assignment on the V section DataFrame copy
                         df_v_section.loc[idx, 'overtime'] = True
                         print(f"    DEBUG CR V OT: Idx={idx}, Pos={q_pos}, Time={q_time:.2f} > Threshold={threshold:.2f} -> OVERTIME")
                elif q_type == 'Reading Comprehension':
                     if not has_rc_cols:
                         continue # Skip RC individual if columns missing
                     
                     # Debug RC Row
                     group_id = df_v_section.loc[idx, 'rc_group_id']
                     q_pos = df_v_section.loc[idx, 'question_position']
                     print(f"    DEBUG RC V OT Check: Idx={idx}, Pos={q_pos}, Group={group_id}, Time={q_time:.2f}")
                     
                     # --- Individual Overtime Check --- 
                     reading_time = df_v_section.loc[idx, 'rc_reading_time']
                     if pd.isna(reading_time):
                         reading_time = 0 # Assume 0 if calculation failed
                     print(f"      RC V OT: ReadingTime={reading_time:.2f}")
                     
                     is_first_question = False
                     if pd.notna(group_id) and pd.notna(q_pos):
                         group_df = df_v_section[(df_v_section['rc_group_id'] == group_id) & (df_v_section['question_type'] == 'RC')]
                         if not group_df.empty:
                             min_pos_in_group = group_df['question_position'].min()
                             if pd.notna(min_pos_in_group) and q_pos == min_pos_in_group:
                                 is_first_question = True
                     print(f"      RC V OT: IsFirstQuestion={is_first_question}")
                                 
                     adjusted_rc_time = q_time - reading_time if is_first_question else q_time
                     print(f"      RC V OT: AdjustedTime={adjusted_rc_time:.2f}")
                     
                     individual_overtime_flag = adjusted_rc_time > V_RC_INDIVIDUAL_Q_THRESHOLD
                     df_v_section.loc[idx, 'individual_overtime'] = individual_overtime_flag
                     print(f"      RC V OT: IndividualOvertime={individual_overtime_flag} (Threshold={V_RC_INDIVIDUAL_Q_THRESHOLD:.2f})")

                     # --- Group Overtime Check --- 
                     group_overtime_flag = False
                     if pd.notna(group_id) and 'rc_group_total_time' in df_v_section.columns:
                         target_time = 0
                         num_q_in_group = len(df_v_section[df_v_section['rc_group_id'] == group_id])
                         print(f"      RC V OT: NumQInGroup={num_q_in_group}")
                         if num_q_in_group == 3:
                             target_time = V_RC_TARGET_TIME_3Q_PRESSURE if time_pressure else V_RC_TARGET_TIME_3Q_NO_PRESSURE
                         elif num_q_in_group == 4:
                             target_time = V_RC_TARGET_TIME_4Q_PRESSURE if time_pressure else V_RC_TARGET_TIME_4Q_NO_PRESSURE
                         else:
                             print(f"      RC V OT: WARNING - Unexpected NumQInGroup ({num_q_in_group}), cannot check group OT.")
                         
                         group_total_time_val = df_v_section.loc[idx, 'rc_group_total_time']
                         print(f"      RC V OT: GroupTotalTime={group_total_time_val:.2f}, TargetTime={target_time:.2f}")
                         if pd.notna(group_total_time_val) and target_time > 0:
                              group_overtime_flag = group_total_time_val > (target_time + 1.0)
                         print(f"      RC V OT: GroupOvertime={group_overtime_flag}")
                     else:
                          print(f"      RC V OT: Skipping group overtime check (Invalid group_id or missing rc_group_total_time)")
                     # Store group overtime flag (though maybe redundant if final flag is set)
                     df_v_section.loc[idx, 'group_overtime'] = group_overtime_flag 

                     # --- Final Overtime Decision --- 
                     final_overtime = group_overtime_flag or individual_overtime_flag
                     df_v_section.loc[idx, 'overtime'] = final_overtime
                     print(f"      RC V OT: Final Overtime = {final_overtime}")

            # Update the main overtime mask for the V section
            section_overtime_mask = df_v_section['overtime']
            print(f"DEBUG V: Finished processing V overtime. section_overtime_mask.sum() = {section_overtime_mask.sum()}")


        # Update the main DataFrame's 'overtime' column for this section
        df_processed.loc[indices, 'overtime'] = section_overtime_mask[indices]

    # Drop the temporary numeric time column
    df_processed.drop(columns=['question_time_numeric'], inplace=True)

    num_overtime = df_processed['overtime'].sum()
    print(f"DEBUG: Total overtime questions calculated: {num_overtime}")
    print("DEBUG: <<< Exiting calculate_overtime preprocess function <<<\n")

    return df_processed 


def preprocess_verbal_data(df):
    """Applies preprocessing specific to Verbal data, like RC grouping.
       To be called before calculate_overtime.
    """
    print("DEBUG: >>> Entering preprocess_verbal_data >>>")
    df_processed = df.copy()
    v_indices = df_processed[df_processed['Subject'] == 'V'].index
    
    if not v_indices.empty:
        df_v_subset = df_processed.loc[v_indices].copy()
        
        # Ensure necessary columns exist before calling helpers
        required_for_rc = ['question_type', 'question_position', 'question_time']
        if all(col in df_v_subset.columns for col in required_for_rc):
            print("  Preprocessing RC groups for Verbal data...")
            df_v_subset = _identify_rc_groups(df_v_subset)
            df_v_subset = _calculate_rc_times(df_v_subset)
            
            # Update the main dataframe with the processed V subset
            # Ensure columns added exist in the main df or add them
            for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
                if col not in df_processed.columns:
                     df_processed[col] = np.nan # Add column if missing
                df_processed.loc[v_indices, col] = df_v_subset[col]
        else:
            print(f"  Skipping RC preprocessing for Verbal data (Missing columns: {[col for col in required_for_rc if col not in df_v_subset.columns]})")

    print("DEBUG: <<< Exiting preprocess_verbal_data <<<")
    return df_processed


# --- RC Helper Functions (Moved from v_diagnostic.py) ---

def _identify_rc_groups(df_v):
    """Identifies RC passages groups based on consecutive question positions."""
    if 'question_type' not in df_v.columns or 'question_position' not in df_v.columns:
        return df_v

    df_v = df_v.sort_values('question_position').copy()
    df_v['rc_group_id'] = np.nan

    rc_indices = df_v[df_v['question_type'] == 'Reading Comprehension'].index # Match exact type name
    if not rc_indices.any():
        return df_v # No RC questions

    group_counter = 0
    current_group_id = np.nan
    last_pos = -2

    for idx in df_v.index:
        row = df_v.loc[idx]
        # Use exact name match
        if row['question_type'] == 'Reading Comprehension':
            # Ensure position is numeric before comparison
            current_pos = pd.to_numeric(row['question_position'], errors='coerce')
            if pd.isna(current_pos):
                 print(f"Warning (_identify_rc_groups): Skipping row index {idx} due to non-numeric position.")
                 last_pos = -2 # Reset continuity check
                 continue
                 
            if current_pos != last_pos + 1:
                # Start of a new group
                group_counter += 1
                current_group_id = f"RC_Group_{group_counter}"
            df_v.loc[idx, 'rc_group_id'] = current_group_id
            last_pos = current_pos # Update last valid position
        else:
            # Reset group logic if non-RC question encountered
            current_group_id = np.nan
            last_pos = -2

    # Validate group sizes (Warn if > 4)
    if 'rc_group_id' in df_v.columns:
        group_sizes = df_v.dropna(subset=['rc_group_id']).groupby('rc_group_id').size()
        oversized_groups = group_sizes[group_sizes > 4].index.tolist()
        if oversized_groups:
             print(f"    Warning: RC groups detected with > 4 questions, manual check recommended: {oversized_groups}")

    return df_v

def _calculate_rc_times(df_v):
    """Calculates RC group total time and estimated reading time.
       Assumes _identify_rc_groups has been run.
       Ensures question_time is numeric.
    """
    if 'rc_group_id' not in df_v.columns or df_v['rc_group_id'].isnull().all():
        df_v['rc_group_total_time'] = np.nan
        df_v['rc_reading_time'] = np.nan
        return df_v
        
    # Ensure question_time is numeric
    df_v['question_time_numeric'] = pd.to_numeric(df_v['question_time'], errors='coerce')

    # Calculate group total time using the numeric column
    # Filter for RC questions only *before* grouping for total time
    rc_only_df = df_v[df_v['question_type'] == 'Reading Comprehension'].copy()
    if not rc_only_df.empty:
        group_times = rc_only_df.groupby('rc_group_id')['question_time_numeric'].sum()
        df_v['rc_group_total_time'] = df_v['rc_group_id'].map(group_times)
    else:
         df_v['rc_group_total_time'] = np.nan

    # Calculate reading time (first q time - avg time of others)
    df_v['rc_reading_time'] = np.nan
    # Use the pre-filtered rc_only_df for grouping here as well
    if not rc_only_df.empty:
        for group_id, group_df in rc_only_df.groupby('rc_group_id'):
            # Ensure positions are numeric for sorting
            group_df['question_position_numeric'] = pd.to_numeric(group_df['question_position'], errors='coerce')
            group_df_sorted = group_df.dropna(subset=['question_position_numeric']).sort_values('question_position_numeric')
            
            if group_df_sorted.empty:
                 continue # Skip group if positions are invalid
                 
            first_q_index = group_df_sorted.index[0]
            if len(group_df_sorted) > 1:
                first_q_time = group_df_sorted['question_time_numeric'].iloc[0]
                other_q_times_numeric = group_df_sorted['question_time_numeric'].iloc[1:].dropna()
                if pd.isna(first_q_time) or other_q_times_numeric.empty:
                    reading_time = 0 # Cannot calculate if first time is NaN or no other times exist
                else:
                    other_q_times_avg = other_q_times_numeric.mean()
                    reading_time = first_q_time - other_q_times_avg
                    reading_time = max(0, reading_time) # Ensure reading time is not negative
                # Assign reading time only to the first question of the group in the *original* df_v
                df_v.loc[first_q_index, 'rc_reading_time'] = reading_time
            else:
                 # If only 1 question in group, reading_time remains NaN (or set to 0? Let's keep NaN)
                 pass 
            # Drop temporary numeric position column from the group copy
            # group_df_sorted = group_df_sorted.drop(columns=['question_position_numeric'], errors='ignore')

    # Drop the temporary numeric time column from the main df
    df_v = df_v.drop(columns=['question_time_numeric'], errors='ignore')

    return df_v

# --- End RC Helper Functions --- 