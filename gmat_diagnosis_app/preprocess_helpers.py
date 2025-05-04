import pandas as pd
import numpy as np
import math
import warnings # Use warnings module instead of print

# --- Centralized Thresholds and Constants ---
THRESHOLDS = {
    'Q': {
        'TOTAL_QUESTIONS': 21,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_FAST_END_MIN': 1.0,
        'TIME_DIFF_PRESSURE': 3.0, # Kept for reference, not directly used in these functions
        'LAST_THIRD_FRACTION': 2/3, # Assuming Q uses last third like DI
        'OVERTIME_PRESSURE': 2.5,
        'OVERTIME_NO_PRESSURE': 3.0,
        'INVALID_TAG': "數據無效：用時過短（Q：受時間壓力影響，處於後段且用時短）" # More specific tag
    },
    'DI': {
        'TOTAL_QUESTIONS': 20,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_FAST_END_MIN': 1.0,
        'TIME_PRESSURE_DIFF_MIN': 3.0, # Threshold to determine pressure itself
        'LAST_THIRD_FRACTION': 2/3,
        'INVALID_TAG': "數據無效：用時過短（DI：受時間壓力影響，處於後段且用時短）",
        # Type-specific overtime thresholds
        'OVERTIME': {
            'TPA': {'pressure': 3.0, 'no_pressure': 3.5},
            'GT': {'pressure': 3.0, 'no_pressure': 3.5}, # Assuming same as TPA based on original code
            'DS': {'pressure': 2.0, 'no_pressure': 2.5},
            # MSR target times used as thresholds for group overtime check
            'MSR_TARGET': {'pressure': 6.0, 'no_pressure': 7.0}
        }
    },
    'V': {
        'TOTAL_QUESTIONS': 23,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_HASTY_MIN': 1.0, # Simple threshold for *suggestion*
        'INVALID_TAG': "數據無效：用時過短（V：用時低於下限）", # Simplified tag for suggestion stage
        # Type-specific overtime thresholds
        'OVERTIME': {
            'CR': {'pressure': 2.0, 'no_pressure': 2.5},
            'RC_INDIVIDUAL': 2.0,
            'RC_GROUP_TARGET': { # Target times for RC groups (check requires +1 min buffer in logic)
                '3Q': {'pressure': 6.0, 'no_pressure': 7.0},
                '4Q': {'pressure': 8.0, 'no_pressure': 9.0}
            }
        }
    }
}

# --- Invalid Question Suggestion ---

def _suggest_invalid_last_third(pos_series, time_series, total_q, fraction, threshold):
    """Helper to check for invalid questions in the last fraction."""
    if total_q <= 0:
        return pd.Series(False, index=pos_series.index) # No questions, nothing invalid
    last_part_start_pos = math.ceil(total_q * fraction) # Position number starts at 1
    # If question_position is 1-based, >= last_part_start_pos
    # If 0-based index used for position: >= last_part_start_pos - 1
    # Assuming question_position is 1-based from original code.
    is_last_part = pos_series >= last_part_start_pos
    is_too_fast = time_series < threshold
    return is_last_part & is_too_fast

def suggest_invalid_questions(df, time_pressure_status_map):
    """
    Suggests invalid questions based on simplified rules for PREPROCESSING.
    Prioritizes 'is_manually_invalid' flag if present. Adds 'is_auto_suggested_invalid'.
    The final 'is_invalid' is manual OR auto_suggested (for preview).

    Args:
        df (pd.DataFrame): Combined DataFrame. Requires 'Subject', 'question_position',
                           'question_time'. Optional: 'is_manually_invalid'.
        time_pressure_status_map (dict): {'Q': bool, 'DI': bool, 'V': bool}

    Returns:
        pd.DataFrame: DataFrame with 'is_invalid', 'is_manually_invalid' (preserved or added),
                      and 'is_auto_suggested_invalid' columns.
    """
    # warnings.warn("Entering suggest_invalid_questions", stacklevel=2) # Optional: Use warnings for debug/info
    df_processed = df.copy()

    # --- Initialize Columns Safely ---
    if 'is_manually_invalid' not in df_processed.columns:
        df_processed['is_manually_invalid'] = False
    else:
        df_processed['is_manually_invalid'] = df_processed['is_manually_invalid'].fillna(False).astype(bool)

    df_processed['is_auto_suggested_invalid'] = False

    # --- Check Required Input Columns ---
    required_cols = ['Subject', 'question_position', 'question_time']
    missing_cols = [col for col in required_cols if col not in df_processed.columns]
    if missing_cols:
        warnings.warn(f"Missing required columns for invalid suggestion: {missing_cols}. Skipping suggestion.", UserWarning, stacklevel=2)
        df_processed['is_invalid'] = df_processed['is_manually_invalid'] # Ensure is_invalid exists
        return df_processed

    # Ensure time and position are numeric for calculations
    df_processed['q_time_numeric'] = pd.to_numeric(df_processed['question_time'], errors='coerce')
    df_processed['q_pos_numeric'] = pd.to_numeric(df_processed['question_position'], errors='coerce')

    # --- Apply Rules Per Section using Boolean Masking ---
    for section, section_thresholds in THRESHOLDS.items():
        section_mask = (df_processed['Subject'] == section)
        if not section_mask.any():
            continue # Skip if no data for this section

        indices = df_processed[section_mask].index
        eligible_for_auto = ~df_processed.loc[indices, 'is_manually_invalid'] # Mask where not manually invalid
        time_pressure = time_pressure_status_map.get(section, False)

        auto_invalid_section_mask = pd.Series(False, index=indices) # Initialize

        q_time_series = df_processed.loc[indices, 'q_time_numeric']
        q_pos_series = df_processed.loc[indices, 'q_pos_numeric']

        # Handle sections with "last third" rule (Q, DI)
        if section in ['Q', 'DI']:
            if time_pressure:
                threshold = section_thresholds['INVALID_FAST_END_MIN']
                total_q = section_thresholds['TOTAL_QUESTIONS']
                fraction = section_thresholds['LAST_THIRD_FRACTION']
                # Apply helper, ensuring NaNs in time/pos don't cause errors
                auto_invalid_section_mask = _suggest_invalid_last_third(
                    q_pos_series.dropna(), q_time_series.dropna(), total_q, fraction, threshold
                ).reindex(indices).fillna(False) # Reindex to match original section indices and fill NaN results as False
            # else: No auto-suggestion if no pressure for Q/DI

        # Handle Verbal section (simple haste check, only if pressure=True for V)
        elif section == 'V':
             if time_pressure: # V simple rule requires pressure for suggestion
                 threshold = section_thresholds['INVALID_HASTY_MIN']
                 is_fast = q_time_series < threshold
                 # Combine with eligibility mask, handle NaNs resulting from comparison
                 auto_invalid_section_mask = is_fast.fillna(False) & eligible_for_auto
             # else: No auto-suggestion if no pressure for V

        # Update the main dataframe
        df_processed.loc[indices, 'is_auto_suggested_invalid'] = auto_invalid_section_mask & eligible_for_auto

    # --- Create Final 'is_invalid' for Preview ---
    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']

    # Clean up temporary columns
    df_processed.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')

    # Optional: Log summary
    # num_manual = df_processed['is_manually_invalid'].sum()
    # num_auto = df_processed['is_auto_suggested_invalid'].sum()
    # num_final = df_processed['is_invalid'].sum()
    # print(f"Suggest Invalid Summary: Manual={num_manual}, Auto={num_auto}, Final Preview={num_final}")

    return df_processed

# --- Overtime Calculation ---

def _calculate_overtime_q(df_q, pressure, thresholds):
    """Calculates overtime mask for Q section."""
    threshold = thresholds['OVERTIME_PRESSURE'] if pressure else thresholds['OVERTIME_NO_PRESSURE']
    is_overtime = df_q['q_time_numeric'] > threshold
    return is_overtime.fillna(False)

def _calculate_overtime_di(df_di, pressure, thresholds):
    """Calculates overtime mask for DI section."""
    overtime_mask = pd.Series(False, index=df_di.index)
    overtime_thresholds = thresholds['OVERTIME']
    msr_target_times = overtime_thresholds['MSR_TARGET']

    # --- Pre-calculate MSR Group Overtime ---
    msr_group_overtime_map = {}
    if 'msr_group_id' in df_di.columns:
        # Group by msr_group_id *within DI section*
        msr_groups = df_di[df_di['question_type'] == 'MSR'].groupby('msr_group_id', dropna=False) # include NaN groups? No, dropna=True default
        for group_id, group_df in msr_groups:
             if pd.isna(group_id): continue # Skip invalid group IDs
             group_total_time = group_df['q_time_numeric'].sum(skipna=True) # Sum ignoring NaNs within group
             target_time = msr_target_times['pressure'] if pressure else msr_target_times['no_pressure']
             msr_group_overtime_map[group_id] = group_total_time > target_time
    else:
        warnings.warn("DI overtime: Missing 'msr_group_id' column, cannot calculate MSR group overtime.", UserWarning, stacklevel=3) # Use stacklevel 3

    # --- Apply rules per type using vectorized operations where possible ---
    for q_type, type_thresholds in overtime_thresholds.items():
        if q_type == 'MSR_TARGET': continue # Skip MSR target entry

        type_mask = (df_di['question_type'] == q_type)
        if not type_mask.any(): continue # Skip if no questions of this type

        threshold = type_thresholds['pressure'] if pressure else type_thresholds['no_pressure']
        # Compare time, handle NaNs, update overall mask
        is_type_overtime = (df_di['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[type_mask & is_type_overtime] = True

    # --- Apply MSR group overtime ---
    msr_mask = (df_di['question_type'] == 'MSR')
    if msr_mask.any() and 'msr_group_id' in df_di.columns:
         # Map the pre-calculated group overtime status, default to False if group_id is NaN or not found
         is_msr_group_overtime = df_di['msr_group_id'].map(msr_group_overtime_map).fillna(False)
         overtime_mask.loc[msr_mask & is_msr_group_overtime] = True # Update if group is overtime

    return overtime_mask


def _calculate_overtime_v(df_v, pressure, thresholds):
    """Calculates overtime mask for V section."""
    overtime_mask = pd.Series(False, index=df_v.index)
    overtime_thresholds = thresholds['OVERTIME']
    cr_thresholds = overtime_thresholds['CR']
    rc_ind_threshold = overtime_thresholds['RC_INDIVIDUAL']
    rc_group_targets = overtime_thresholds['RC_GROUP_TARGET']

    # Check for essential RC columns added by preprocess_verbal_data
    rc_cols_present = all(c in df_v.columns for c in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time'])
    if not rc_cols_present:
        warnings.warn("Verbal overtime: Missing preprocessed RC columns. RC overtime calculation will be skipped.", UserWarning, stacklevel=3)

    # --- CR Overtime ---
    cr_mask = (df_v['question_type'] == 'Critical Reasoning')
    if cr_mask.any():
        threshold = cr_thresholds['pressure'] if pressure else cr_thresholds['no_pressure']
        is_cr_overtime = (df_v['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[cr_mask & is_cr_overtime] = True

    # --- RC Overtime ---
    rc_mask = (df_v['question_type'] == 'Reading Comprehension')
    if rc_mask.any() and rc_cols_present:
        df_rc = df_v.loc[rc_mask].copy() # Work on RC subset

        # -- Individual RC Check --
        # Find first question in each group
        df_rc['q_pos_numeric'] = pd.to_numeric(df_rc['question_position'], errors='coerce')
        # Avoid SettingWithCopyWarning by using .loc on the original df_rc index
        is_first_in_group = df_rc.loc[df_rc.groupby('rc_group_id')['q_pos_numeric'].idxmin(), 'question_position'].notna() # Series indicating first q per group
        # Map this back to df_rc based on index
        df_rc['is_first_q'] = df_rc.index.isin(is_first_in_group[is_first_in_group].index) # Map True/False based on index match


        reading_time = df_rc['rc_reading_time'].fillna(0) # Use 0 if reading time calculation failed
        adjusted_time = np.where(df_rc['is_first_q'], df_rc['q_time_numeric'] - reading_time, df_rc['q_time_numeric'])
        adjusted_time = np.maximum(0, adjusted_time) # Ensure non-negative adjusted time

        is_individual_overtime = (adjusted_time > rc_ind_threshold)

        # -- Group RC Check --
        # Map group sizes first
        group_sizes = df_rc.groupby('rc_group_id').size()
        df_rc['rc_group_size'] = df_rc['rc_group_id'].map(group_sizes)

        # Determine target time based on group size and pressure
        target_time = 0 # Default
        if pressure:
             target_time = np.select(
                 [df_rc['rc_group_size'] == 3, df_rc['rc_group_size'] == 4],
                 [rc_group_targets['3Q']['pressure'], rc_group_targets['4Q']['pressure']],
                 default=0 # No target for other sizes
             )
        else: # No pressure
             target_time = np.select(
                 [df_rc['rc_group_size'] == 3, df_rc['rc_group_size'] == 4],
                 [rc_group_targets['3Q']['no_pressure'], rc_group_targets['4Q']['no_pressure']],
                 default=0
             )

        # Check group total time against target (+1 min buffer like original logic)
        # Fill NaN total times with 0 to avoid errors in comparison
        group_total_time = df_rc['rc_group_total_time'].fillna(0)
        is_group_overtime = (target_time > 0) & (group_total_time > (target_time + 1.0)) # Only True if target is valid

        # Combine individual and group overtime for RC questions
        # Handle potential NaNs from comparisons
        is_rc_overtime = is_individual_overtime.fillna(False) | is_group_overtime.fillna(False)

        # Update the main overtime mask using the index from df_rc
        overtime_mask.loc[df_rc.index[is_rc_overtime]] = True # Update where is_rc_overtime is True

    return overtime_mask


def calculate_overtime(df, time_pressure_status_map):
    """
    Calculates the 'overtime' status for each question. Calls subject-specific helpers.

    Args:
        df (pd.DataFrame): Combined DataFrame. Requires 'Subject', 'question_time', 'question_type'.
                           Requires RC/MSR columns if V/DI are present.
        time_pressure_status_map (dict): {'Q': bool, 'DI': bool, 'V': bool}

    Returns:
        pd.DataFrame: DataFrame with added boolean 'overtime' column.
    """
    # warnings.warn("Entering calculate_overtime", stacklevel=2) # Optional info
    df_processed = df.copy()

    # --- 1. Preprocess Verbal Data FIRST to get RC info ---
    # This adds 'rc_group_id', 'rc_group_total_time', 'rc_reading_time'
    try:
        df_processed = preprocess_verbal_data(df_processed)
    except Exception as e:
         warnings.warn(f"Error during verbal preprocessing: {e}. Overtime calculation may be affected.", RuntimeWarning, stacklevel=2)
         # Add expected columns as NaN if they failed, to prevent KeyError later
         for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
              if col not in df_processed.columns: df_processed[col] = np.nan

    # --- 2. Check Base Required Columns ---
    required_cols = ['Subject', 'question_time', 'question_type']
    missing_cols = [col for col in required_cols if col not in df_processed.columns]
    if missing_cols:
        warnings.warn(f"Missing required columns for overtime calculation: {missing_cols}. Returning original DataFrame.", UserWarning, stacklevel=2)
        df_processed['overtime'] = False # Ensure column exists even if calculation skipped
        return df_processed

    # --- 3. Prepare Numeric Time Column ---
    df_processed['q_time_numeric'] = pd.to_numeric(df_processed['question_time'], errors='coerce')

    # --- 4. Calculate Overtime Per Subject using Helpers ---
    all_overtime_masks = []
    processed_indices = [] # Keep track of indices processed to ensure full coverage

    for section, section_thresholds in THRESHOLDS.items():
        section_mask_bool = (df_processed['Subject'] == section)
        if not section_mask_bool.any():
            continue # Skip if no data for this section

        indices = df_processed.index[section_mask_bool]
        processed_indices.extend(indices.tolist())
        df_section = df_processed.loc[indices]
        pressure = time_pressure_status_map.get(section, False)
        overtime_section_mask = pd.Series(False, index=indices) # Default

        try:
            if section == 'Q':
                overtime_section_mask = _calculate_overtime_q(df_section, pressure, section_thresholds)
            elif section == 'DI':
                overtime_section_mask = _calculate_overtime_di(df_section, pressure, section_thresholds)
            elif section == 'V':
                overtime_section_mask = _calculate_overtime_v(df_section, pressure, section_thresholds)

            all_overtime_masks.append(overtime_section_mask)
        except Exception as e:
            warnings.warn(f"Error calculating overtime for section {section}: {e}. Overtime for this section defaulted to False.", RuntimeWarning, stacklevel=2)
            # Append a False mask for this section to maintain structure
            all_overtime_masks.append(pd.Series(False, index=indices))


    # --- 5. Combine results and clean up ---
    if all_overtime_masks:
         # Concatenate all boolean Series masks
         combined_mask = pd.concat(all_overtime_masks)
         # Assign to the 'overtime' column, ensuring index alignment
         df_processed['overtime'] = combined_mask.reindex(df_processed.index).fillna(False)
    else:
         # Handle case where no subjects were processed (e.g., empty input df)
         df_processed['overtime'] = False

    # Check if all original rows were processed
    if len(processed_indices) != len(df_processed):
        warnings.warn(f"Overtime calculation: Not all rows were processed ({len(processed_indices)} vs {len(df_processed)}). Defaulting unprocessed rows to False.", RuntimeWarning, stacklevel=2)
        unprocessed_indices = df_processed.index.difference(processed_indices)
        df_processed.loc[unprocessed_indices, 'overtime'] = False # Ensure default


    df_processed.drop(columns=['q_time_numeric'], inplace=True, errors='ignore')

    # Optional: Log summary
    # num_overtime = df_processed['overtime'].sum()
    # print(f"Calculate Overtime Summary: Total Overtime={num_overtime}")

    return df_processed


# --- Verbal Preprocessing & RC Helpers (Keep logic largely the same) ---

def preprocess_verbal_data(df):
    """Applies preprocessing specific to Verbal data: RC grouping and time calcs."""
    df_processed = df.copy()
    v_mask = df_processed['Subject'] == 'V'
    if not v_mask.any():
        return df_processed # No verbal data

    # Work on a view/copy of the verbal subset
    df_v_subset = df_processed[v_mask]

    # Check required columns for RC processing on the subset
    required_for_rc = ['question_type', 'question_position', 'question_time']
    if not all(col in df_v_subset.columns for col in required_for_rc):
        warnings.warn("Skipping RC preprocessing for Verbal (Missing required columns: time, position, type)", UserWarning, stacklevel=2)
        # Ensure expected columns exist anyway, filled with NaN
        for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
             if col not in df_processed.columns: df_processed[col] = np.nan
        return df_processed

    # Apply RC grouping and time calculations
    df_v_processed = _identify_rc_groups(df_v_subset)
    df_v_processed = _calculate_rc_times(df_v_processed)

    # Update the main dataframe safely using .loc and the original index
    for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
         if col not in df_processed.columns: df_processed[col] = np.nan # Ensure column exists in main df
         # Update using the index from the processed verbal subset
         df_processed.loc[df_v_processed.index, col] = df_v_processed[col]

    return df_processed


def _identify_rc_groups(df_v_subset):
    """Identifies RC passages groups based on consecutive question positions."""
    # Ensure working with a copy if modifications are made (already handled by caller)
    df_v = df_v_subset.sort_values('question_position').copy() # Sort for continuity check
    df_v['rc_group_id'] = np.nan

    # Convert position to numeric ONCE
    df_v['q_pos_numeric'] = pd.to_numeric(df_v['question_position'], errors='coerce')

    rc_indices = df_v[df_v['question_type'] == 'Reading Comprehension'].index
    if not rc_indices.any():
        df_v.drop(columns=['q_pos_numeric'], inplace=True, errors='ignore')
        return df_v # No RC questions

    group_counter = 0
    current_group_id = np.nan
    last_valid_pos = -2 # Ensure first RC question starts a group

    # Iterate using index for safe assignment back
    for idx in df_v.index:
        row = df_v.loc[idx]
        if row['question_type'] == 'Reading Comprehension':
            current_pos = row['q_pos_numeric'] # Use pre-calculated numeric pos
            if pd.isna(current_pos):
                warnings.warn(f"Skipping RC Group ID for index {idx} due to invalid position.", RuntimeWarning, stacklevel=2)
                last_valid_pos = -2 # Reset continuity
                continue

            # Check for break in continuity
            if current_pos != last_valid_pos + 1:
                group_counter += 1
                current_group_id = f"RC_Group_{group_counter}"

            df_v.loc[idx, 'rc_group_id'] = current_group_id
            last_valid_pos = current_pos
        else:
            # Reset if not RC
            current_group_id = np.nan
            last_valid_pos = -2

    # Validate group sizes
    group_sizes = df_v.dropna(subset=['rc_group_id']).groupby('rc_group_id').size()
    oversized_groups = group_sizes[group_sizes > 4].index.tolist()
    if oversized_groups:
         warnings.warn(f"RC groups detected with > 4 questions: {oversized_groups}. Verify data.", UserWarning, stacklevel=2)

    df_v.drop(columns=['q_pos_numeric'], inplace=True, errors='ignore')
    return df_v


def _calculate_rc_times(df_v_grouped):
    """Calculates RC group total time and estimated reading time."""
    # Assume df_v_grouped already has 'rc_group_id'
    if 'rc_group_id' not in df_v_grouped.columns or df_v_grouped['rc_group_id'].isnull().all():
        df_v_grouped['rc_group_total_time'] = np.nan
        df_v_grouped['rc_reading_time'] = np.nan
        return df_v_grouped

    df_v = df_v_grouped.copy() # Work on a copy
    df_v['q_time_numeric'] = pd.to_numeric(df_v['question_time'], errors='coerce')
    df_v['q_pos_numeric'] = pd.to_numeric(df_v['question_position'], errors='coerce')

    # Calculate group total time (sum numeric times per group)
    # Important: Map this back to *all* rows belonging to the group
    group_total_times = df_v.groupby('rc_group_id')['q_time_numeric'].transform('sum')
    df_v['rc_group_total_time'] = group_total_times

    # Calculate reading time (first q time - avg time of others in group)
    df_v['rc_reading_time'] = np.nan # Initialize

    # Find the index of the first question in each group
    first_q_indices = df_v.loc[df_v.dropna(subset=['q_pos_numeric']).groupby('rc_group_id')['q_pos_numeric'].idxmin()].index

    for group_id, group_df in df_v.groupby('rc_group_id'):
        if pd.isna(group_id): continue # Skip if group_id is NaN

        group_df_sorted = group_df.dropna(subset=['q_pos_numeric', 'q_time_numeric']).sort_values('q_pos_numeric')
        if len(group_df_sorted) <= 1:
            continue # Cannot calculate reading time with 0 or 1 valid questions

        first_q_index = group_df_sorted.index[0]
        first_q_time = group_df_sorted['q_time_numeric'].iloc[0]
        other_q_times_avg = group_df_sorted['q_time_numeric'].iloc[1:].mean() # Mean of remaining valid times

        if pd.isna(first_q_time) or pd.isna(other_q_times_avg):
             reading_time = 0 # Default if calculation not possible
        else:
             reading_time = max(0, first_q_time - other_q_times_avg)

        # Assign reading time only to the first question's index in the main working copy df_v
        df_v.loc[first_q_index, 'rc_reading_time'] = reading_time


    df_v.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')
    return df_v