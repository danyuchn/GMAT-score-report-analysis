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
                 auto_invalid_section_mask = is_fast.fillna(False) # No need for eligible_for_auto here, applied later
             # else: No auto-suggestion if no pressure for V

        # Update the main dataframe where eligible
        df_processed.loc[indices[eligible_for_auto], 'is_auto_suggested_invalid'] = auto_invalid_section_mask[eligible_for_auto]


    # --- Create Final 'is_invalid' for Preview ---
    df_processed['is_invalid'] = df_processed['is_manually_invalid'] | df_processed['is_auto_suggested_invalid']

    # Clean up temporary columns
    df_processed.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')

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
        msr_groups = df_di[df_di['question_type'] == 'MSR'].groupby('msr_group_id', dropna=True) # dropna=True is default
        for group_id, group_df in msr_groups:
             # if pd.isna(group_id): continue # Covered by dropna=True
             group_total_time = group_df['q_time_numeric'].sum(skipna=True) # Sum ignoring NaNs within group
             target_time = msr_target_times['pressure'] if pressure else msr_target_times['no_pressure']
             msr_group_overtime_map[group_id] = group_total_time > target_time
    else:
        warnings.warn("DI overtime: Missing 'msr_group_id' column, cannot calculate MSR group overtime.", UserWarning, stacklevel=3)

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
        # Find first question in each group using index from idxmin()
        df_rc['q_pos_numeric'] = pd.to_numeric(df_rc['question_position'], errors='coerce')
        first_q_indices = df_rc.loc[df_rc.dropna(subset=['q_pos_numeric']).groupby('rc_group_id')['q_pos_numeric'].idxmin()].index
        df_rc['is_first_q'] = df_rc.index.isin(first_q_indices)

        reading_time = df_rc['rc_reading_time'].fillna(0) # Use 0 if reading time calculation failed
        # Use numeric time directly, np.where handles types correctly if one branch is float
        adjusted_time = np.where(df_rc['is_first_q'], df_rc['q_time_numeric'] - reading_time, df_rc['q_time_numeric'])
        adjusted_time = np.maximum(0, adjusted_time) # Ensure non-negative adjusted time

        is_individual_overtime = (adjusted_time > rc_ind_threshold)

        # -- Group RC Check --
        # Map group sizes first
        group_sizes = df_rc.groupby('rc_group_id').size()
        df_rc['rc_group_size'] = df_rc['rc_group_id'].map(group_sizes)

        # Determine target time based on group size and pressure using np.select
        target_time = np.select(
             [
                 (df_rc['rc_group_size'] == 3) & pressure,
                 (df_rc['rc_group_size'] == 4) & pressure,
                 (df_rc['rc_group_size'] == 3) & ~pressure,
                 (df_rc['rc_group_size'] == 4) & ~pressure,
             ],
             [
                 rc_group_targets['3Q']['pressure'],
                 rc_group_targets['4Q']['pressure'],
                 rc_group_targets['3Q']['no_pressure'],
                 rc_group_targets['4Q']['no_pressure'],
             ],
             default=0 # No target for other sizes or if pressure condition is false
         )

        # Check group total time against target (+1 min buffer like original logic)
        # Fill NaN total times with 0 to avoid errors in comparison
        group_total_time = df_rc['rc_group_total_time'].fillna(0)
        is_group_overtime = (target_time > 0) & (group_total_time > (target_time + 1.0)) # Only True if target is valid

        # Combine individual and group overtime for RC questions
        # Handle potential NaNs from comparisons
        # Ensure fillna is called on pandas Series
        is_individual_overtime_series = pd.Series(is_individual_overtime, index=df_rc.index)
        is_group_overtime_series = pd.Series(is_group_overtime, index=df_rc.index)
        is_rc_overtime = is_individual_overtime_series.fillna(False) | is_group_overtime_series.fillna(False)

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
    df_processed = df.copy()

    # --- 1. Preprocess Verbal Data FIRST to get RC info ---
    try:
        df_processed = preprocess_verbal_data(df_processed)
    except Exception as e:
         warnings.warn(f"Error during verbal preprocessing: {e}. Overtime calculation may be affected.", RuntimeWarning, stacklevel=2)
         for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
              if col not in df_processed.columns: df_processed[col] = np.nan

    # --- 1b. Preprocess DI Data to get MSR info ---
    try:
        df_processed = preprocess_di_data(df_processed)
    except Exception as e:
        warnings.warn(f"Error during DI preprocessing: {e}. MSR overtime calculation may be affected.", RuntimeWarning, stacklevel=2)
        if 'msr_group_id' not in df_processed.columns:
            df_processed['msr_group_id'] = pd.Series(index=df_processed.index, dtype='object') # Ensure col exists even on error

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
    processed_indices = set() # Use set for efficient membership checking

    for section, section_thresholds in THRESHOLDS.items():
        section_mask_bool = (df_processed['Subject'] == section)
        if not section_mask_bool.any():
            continue # Skip if no data for this section

        indices = df_processed.index[section_mask_bool]
        processed_indices.update(indices) # Add processed indices to set
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
         # Assign to the 'overtime' column, ensuring index alignment and filling potential NaNs
         df_processed['overtime'] = combined_mask.reindex(df_processed.index).fillna(False)
    else:
         # Handle case where no subjects were processed (e.g., empty input df)
         df_processed['overtime'] = False

    # Check if all original rows were processed (more robust check)
    unprocessed_indices = df_processed.index.difference(list(processed_indices))
    if not unprocessed_indices.empty:
        warnings.warn(f"Overtime calculation: {len(unprocessed_indices)} rows were not processed (likely due to missing Subject). Defaulting overtime to False for these rows.", RuntimeWarning, stacklevel=2)
        df_processed.loc[unprocessed_indices, 'overtime'] = False # Ensure default

    df_processed.drop(columns=['q_time_numeric'], inplace=True, errors='ignore')

    return df_processed


# --- Verbal Preprocessing & RC Helpers ---

def preprocess_verbal_data(df):
    """Applies preprocessing specific to Verbal data: RC grouping and time calcs."""
    df_processed = df.copy()
    v_mask = df_processed['Subject'] == 'V'
    if not v_mask.any():
        # Ensure columns exist even if no V data, filled with NaN
        for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
             if col not in df_processed.columns: df_processed[col] = np.nan
        return df_processed

    # Work on a view/copy of the verbal subset
    df_v_subset = df_processed[v_mask]

    # Check required columns for RC processing on the subset
    required_for_rc = ['question_type', 'question_position', 'question_time']
    if not all(col in df_v_subset.columns for col in required_for_rc):
        warnings.warn("Skipping RC preprocessing for Verbal (Missing required columns: time, position, type)", UserWarning, stacklevel=2)
        # Ensure expected columns exist anyway, filled with NaN
        for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
             if col not in df_processed.columns: df_processed[col] = np.nan
        return df_processed # Return original df if requirements not met

    # Apply RC grouping and time calculations
    df_v_processed = _identify_rc_groups(df_v_subset)
    df_v_processed = _calculate_rc_times(df_v_processed)

    # Update the main dataframe safely using .loc and the original index
    for col in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time']:
         if col not in df_processed.columns:
             # Ensure column exists in main df and is of object type for rc_group_id
             if col == 'rc_group_id':
                 df_processed[col] = pd.Series(index=df_processed.index, dtype='object')
             else: # For time columns, float is fine, but can be object too if mixed with NaN initially
                 df_processed[col] = np.nan 
         # Update using the index from the processed verbal subset
         df_processed.loc[df_v_processed.index, col] = df_v_processed[col]

    return df_processed


def _identify_rc_groups(df_v_subset):
    """Identifies RC passages groups based on consecutive question positions."""
    # Sort by position ensures continuity check works
    df_v = df_v_subset.sort_values('question_position').copy()
    # Initialize rc_group_id with object dtype to prevent FutureWarning
    df_v['rc_group_id'] = pd.Series(index=df_v.index, dtype='object')

    # Convert position to numeric ONCE
    df_v['q_pos_numeric'] = pd.to_numeric(df_v['question_position'], errors='coerce')

    rc_indices = df_v[df_v['question_type'] == 'Reading Comprehension'].index
    if rc_indices.empty: # More explicit check
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
                warnings.warn(f"Skipping RC Group ID for index {idx} due to invalid position '{row['question_position']}'.", RuntimeWarning, stacklevel=3)
                last_valid_pos = -2 # Reset continuity
                current_group_id = np.nan # Ensure no carry-over
                continue # Skip assignment for this row

            # Check for break in continuity (position must be exactly +1)
            if current_pos != last_valid_pos + 1:
                group_counter += 1
                current_group_id = f"RC_Group_{group_counter}"

            df_v.loc[idx, 'rc_group_id'] = current_group_id
            last_valid_pos = current_pos
        else:
            # Reset if not RC or if continuity broke on previous RC
            current_group_id = np.nan
            last_valid_pos = -2

    # Validate group sizes after assigning all IDs
    group_sizes = df_v.dropna(subset=['rc_group_id']).groupby('rc_group_id').size()
    oversized_groups = group_sizes[group_sizes > 4].index.tolist()
    if oversized_groups:
         warnings.warn(f"RC groups detected with > 4 questions: {oversized_groups}. Verify data continuity.", UserWarning, stacklevel=2)

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

    # Calculate group total time (sum numeric times per group) using transform
    df_v['rc_group_total_time'] = df_v.groupby('rc_group_id')['q_time_numeric'].transform('sum')

    # Calculate reading time (first q time - avg time of others in group)
    df_v['rc_reading_time'] = np.nan # Initialize

    # Group by rc_group_id, dropping groups where id is NaN
    for group_id, group_df in df_v.groupby('rc_group_id', dropna=True):
        # Ensure group has valid numeric positions and times, sort by position
        group_df_valid = group_df.dropna(subset=['q_pos_numeric', 'q_time_numeric']).sort_values('q_pos_numeric')

        if len(group_df_valid) <= 1:
            # Cannot calculate reading time with 0 or 1 valid questions
            # Reading time remains NaN for these rows (initialized above)
            continue

        first_q_index = group_df_valid.index[0]
        first_q_time = group_df_valid['q_time_numeric'].iloc[0]
        # Calculate mean of remaining valid times (iloc[1:])
        other_q_times_avg = group_df_valid['q_time_numeric'].iloc[1:].mean()

        # Calculate reading time, defaulting to 0 if avg calculation failed (e.g., only one question)
        # This case is already handled by len(group_df_valid) check, but robust check here:
        if pd.isna(other_q_times_avg):
            reading_time = 0
        else:
            reading_time = max(0, first_q_time - other_q_times_avg)

        # Assign reading time ONLY to the first question's index in the main working copy df_v
        df_v.loc[first_q_index, 'rc_reading_time'] = reading_time

    df_v.drop(columns=['q_time_numeric', 'q_pos_numeric'], inplace=True, errors='ignore')
    return df_v

# --- DI Preprocessing & MSR Helpers (NEW) ---

def _identify_msr_groups(df_di_subset):
    """
    Identifies MSR (Multi-source reasoning) groups in DI data.
    Consecutive MSR questions (by position) are grouped into sets of up to 3.
    A break in position continuity or a full group (3 questions) starts a new group.
    """
    # Ensure working on a copy, sort by position
    df_d = df_di_subset.sort_values('question_position').copy()
    
    # Initialize msr_group_id with object dtype to handle strings and NaN
    df_d['msr_group_id'] = pd.Series(index=df_d.index, dtype='object')

    # Convert question_position to numeric for comparison
    df_d['q_pos_numeric'] = pd.to_numeric(df_d['question_position'], errors='coerce')

    group_id_counter = 0
    current_msr_in_group_count = 0
    last_msr_pos = -2  # Ensures the first MSR question starts a new group
    current_group_name = None

    # Iterate through all rows of the sorted DI subset
    for idx in df_d.index:
        row = df_d.loc[idx]
        is_msr = (
            (row['question_type'] == 'Multi-source reasoning') or (row['question_type'] == 'MSR')
        ) and pd.notna(row['q_pos_numeric'])

        if is_msr:
            current_pos = row['q_pos_numeric']
            
            # Start a new group if:
            # 1. Continuity is broken (current_pos != last_msr_pos + 1)
            # 2. Current group is full (current_msr_in_group_count == 3)
            if current_pos != last_msr_pos + 1 or current_msr_in_group_count == 3:
                group_id_counter += 1
                current_group_name = f"MSR_Group_{group_id_counter}"
                current_msr_in_group_count = 0  # Reset count for the new group
            
            df_d.loc[idx, 'msr_group_id'] = current_group_name
            current_msr_in_group_count += 1
            last_msr_pos = current_pos
        else:
            # If not an MSR question, it doesn't belong to an MSR group.
            # Reset continuity trackers for MSRs to ensure next MSR starts a new group.
            last_msr_pos = -2 
            current_msr_in_group_count = 0
            current_group_name = None
            
    df_d.drop(columns=['q_pos_numeric'], inplace=True, errors='ignore')
    return df_d

def preprocess_di_data(df):
    """Applies preprocessing specific to DI data: MSR grouping."""
    df_processed = df.copy()
    di_mask = df_processed['Subject'] == 'DI'
    
    # Initialize msr_group_id in the main df if not present, ensuring object type
    if 'msr_group_id' not in df_processed.columns:
        df_processed['msr_group_id'] = pd.Series(index=df_processed.index, dtype='object')
    elif df_processed['msr_group_id'].dtype != 'object':
        df_processed['msr_group_id'] = df_processed['msr_group_id'].astype('object')

    if not di_mask.any():
        # No DI data, return with potentially initialized (empty) msr_group_id column
        return df_processed

    # Work on a copy of the DI subset
    df_di_subset = df_processed[di_mask].copy()

    required_for_msr = ['question_type', 'question_position']
    if not all(col in df_di_subset.columns for col in required_for_msr):
        warnings.warn(
            "Skipping MSR preprocessing for DI (Missing required columns: 'question_type', 'question_position'). 'msr_group_id' will be empty.", 
            UserWarning, 
            stacklevel=2
        )
        return df_processed # Return with existing (likely empty or all NaN) msr_group_id

    # Apply MSR grouping to the DI subset
    df_di_processed_subset = _identify_msr_groups(df_di_subset)

    # Update the 'msr_group_id' in the main dataframe using .loc and the original index
    # Only update for rows that were part of the DI subset and processed
    if 'msr_group_id' in df_di_processed_subset.columns:
        df_processed.loc[df_di_processed_subset.index, 'msr_group_id'] = df_di_processed_subset['msr_group_id']
    
    return df_processed