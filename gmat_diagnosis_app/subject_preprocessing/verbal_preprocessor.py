# -*- coding: utf-8 -*-
"""Functions for preprocessing Verbal section data, especially RC groups."""
import pandas as pd
import numpy as np
import logging

# Try importing the threshold from v_modules, handle potential ImportError
try:
    from gmat_diagnosis_app.diagnostics.v_modules.constants import RC_GROUP_SIMILARITY_THRESHOLD
except ImportError:
    RC_GROUP_SIMILARITY_THRESHOLD = 80 # Default fallback

# --- Helper Function for Time-Based Splitting ---
def _is_likely_new_group_start(df_block_subset, relative_check_idx):
    """
    Checks if the question at relative_check_idx within the block subset
    has a time significantly longer than the average of other questions (excluding the first).

    Args:
        df_block_subset (pd.DataFrame): DataFrame containing ONLY the questions
                                         in the current consecutive block being evaluated.
                                         Index should be the original DataFrame index.
        relative_check_idx (int): The 0-based index WITHIN the df_block_subset
                                  to check (e.g., 3 for the 4th question).

    Returns:
        bool: True if the time at relative_check_idx suggests a new group start.
    """
    if df_block_subset.empty or len(df_block_subset) <= relative_check_idx or len(df_block_subset) < 3:
        # Not enough data to compare or invalid index
        return False # Default to not splitting if ambiguous

    try:
        # Ensure question_time is numeric
        q_times = pd.to_numeric(df_block_subset['question_time'], errors='coerce')

        # Check if the specific question to check has a valid time
        time_at_check_point = q_times.iloc[relative_check_idx]
        if pd.isna(time_at_check_point):
             return False # Cannot determine if time is NaN

        # Calculate average time excluding the first question of the block
        # Need at least 2 other questions to calculate a meaningful average
        other_q_times = q_times.iloc[1:] # Exclude the first question
        if len(other_q_times.dropna()) < 1:
             return False # Cannot determine without avg

        avg_time_excl_first = other_q_times.mean() # NaNs are automatically skipped by mean()

        if pd.isna(avg_time_excl_first) or avg_time_excl_first <= 0:
             return False # Cannot determine if avg is invalid

        threshold = 2 * avg_time_excl_first
        is_longer = time_at_check_point > threshold

        return is_longer

    except Exception as e:
        logging.error(f"Error during time check for index {df_block_subset.index[relative_check_idx]}: {e}", exc_info=True)
        return False # Default to False on error

# --- Main RC Grouping Function (Rewritten) ---
def _identify_rc_groups(df_v_subset):
    """
    Identifies groups of consecutive Reading Comprehension (RC) questions based on
    block length and time heuristics (only for 7-question blocks).
    RC groups must be 3 or 4 questions long.

    Args:
        df_v_subset (pd.DataFrame): DataFrame containing Verbal questions.
                                     Requires 'question_type' and 'question_time'.
                                     Index should be preserved from the original DataFrame.

    Returns:
        pd.Series: Contains the group ID (integer starting from 0) for RC questions,
                   and NaN for non-RC or invalidly grouped RC questions.
                   Index matches df_v_subset.
    """
    rc_group_ids = pd.Series(np.nan, index=df_v_subset.index, dtype='Int64') # Use nullable Int64
    global_group_counter = 0

    if 'question_type' not in df_v_subset.columns:
        logging.error("Missing 'question_type' column.")
        return rc_group_ids
    if 'question_time' not in df_v_subset.columns:
        logging.error("Missing 'question_time' column.")
        return rc_group_ids

    # Ensure question_time is numeric
    df_v_subset['question_time_numeric'] = pd.to_numeric(df_v_subset['question_time'], errors='coerce')


    # 1. Identify consecutive RC blocks
    is_rc = df_v_subset['question_type'] == 'Reading Comprehension'
    # Create groups based on consecutive RC questions
    rc_blocks = is_rc.ne(is_rc.shift()).cumsum()[is_rc]

    if rc_blocks.empty:
        df_v_subset.drop(columns=['question_time_numeric'], inplace=True, errors='ignore') # Clean up temp column
        return rc_group_ids

    # 2. Process each block
    for block_id, block_indices in rc_blocks.groupby(rc_blocks).groups.items():
        block_length = len(block_indices)
        block_start_idx = block_indices[0]
        block_end_idx = block_indices[-1]

        # Get subset for time analysis if needed (only for length 7)
        block_subset_df = df_v_subset.loc[block_indices]

        current_idx_position = 0 # Position within the current block indices list
        while current_idx_position < block_length:
            remaining_length = block_length - current_idx_position
            group_size_to_assign = 0

            if remaining_length <= 2:
                break # Stop processing this block

            elif remaining_length == 3: group_size_to_assign = 3
            elif remaining_length == 4: group_size_to_assign = 4
            elif remaining_length == 5:
                break
            elif remaining_length == 6: group_size_to_assign = 3 # First part of 3+3
            elif remaining_length == 7:
                # Time heuristic needed for 3+4 vs 4+3
                # Check the 4th question in the remaining 7 (relative index 3)
                is_new_group = _is_likely_new_group_start(block_subset_df.iloc[current_idx_position : current_idx_position + 7], 3)
                if is_new_group:
                    group_size_to_assign = 3 # Split is 3 + 4
                else:
                    group_size_to_assign = 4 # Split is 4 + 3
            elif remaining_length == 8: group_size_to_assign = 4 # First part of 4+4
            elif remaining_length == 9: group_size_to_assign = 3 # First part of 3+3+3
            elif remaining_length == 10: group_size_to_assign = 3 # First part of 3+3+4
            elif remaining_length == 11: group_size_to_assign = 3 # First part of 3+4+4
            elif remaining_length == 12: group_size_to_assign = 4 # First part of 4+4+4
            else: # remaining_length > 12
                group_size_to_assign = 4

            # Assign Group ID
            if group_size_to_assign > 0:
                start_assign_block_pos = current_idx_position
                end_assign_block_pos = current_idx_position + group_size_to_assign -1
                # Get original indices from the block_indices Series
                original_indices_to_assign = block_indices[start_assign_block_pos : end_assign_block_pos + 1]

                rc_group_ids.loc[original_indices_to_assign] = global_group_counter

                current_idx_position += group_size_to_assign
                global_group_counter += 1
            else:
                 # Should not happen unless remaining_length <= 2 initially or 5
                 logging.error("Internal error: group_size_to_assign became 0 unexpectedly.")
                 break # Safety break

    # Clean up temporary column
    df_v_subset.drop(columns=['question_time_numeric'], inplace=True, errors='ignore')

    return rc_group_ids

def _calculate_rc_times(df_v_grouped):
    """Calculate reading time and total group time for RC passages."""
    # Ensure necessary columns exist, handle potential NaNs or missing groups
    if 'rc_group_id' not in df_v_grouped.columns or df_v_grouped['rc_group_id'].isna().all():
        # Ensure columns exist with default values even if skipped
        df_v_grouped['rc_reading_time'] = 0.0
        df_v_grouped['rc_group_total_time'] = 0.0
        df_v_grouped['rc_group_num_questions'] = 0
        return df_v_grouped

    # Convert relevant columns to numeric, coercing errors
    df_v_grouped['question_position'] = pd.to_numeric(df_v_grouped['question_position'], errors='coerce')
    df_v_grouped['question_time'] = pd.to_numeric(df_v_grouped['question_time'], errors='coerce')

    # --- Calculate Reading Time ---
    df_v_grouped['rc_reading_time'] = 0.0 # Initialize
    # Group by the potentially nullable Int64 rc_group_id
    # Need to handle groups where rc_group_id is NaN - these should not be processed
    valid_groups = df_v_grouped.dropna(subset=['rc_group_id']).groupby('rc_group_id')

    group_data_for_reading_time = {}
    first_q_indices_map = {} # Store first q index per group

    for name, group in valid_groups:
        if group['question_position'].notna().any():
            first_q_idx = group['question_position'].idxmin()
            first_q_time = group.loc[first_q_idx, 'question_time']
            other_qs_time = group.loc[group.index != first_q_idx, 'question_time']

            calculated_rc_reading_time = first_q_time
            if not other_qs_time.dropna().empty:
                avg_other_qs_time = other_qs_time.mean() # mean() handles NaNs
                if pd.notna(avg_other_qs_time):
                    calculated_rc_reading_time = first_q_time - avg_other_qs_time

            # Assign reading time only to the first question
            if pd.notna(calculated_rc_reading_time):
                 df_v_grouped.loc[first_q_idx, 'rc_reading_time'] = calculated_rc_reading_time
            else:
                 df_v_grouped.loc[first_q_idx, 'rc_reading_time'] = 0.0 # Default if calc failed


    # --- Calculate Total Time and Num Questions per Group ---
    df_v_grouped['rc_group_total_time'] = 0.0 # Initialize
    df_v_grouped['rc_group_num_questions'] = 0 # Initialize

    group_stats = valid_groups['question_time'].agg(['sum', 'size'])
    group_stats.columns = ['rc_group_total_time', 'rc_group_num_questions']

    # Map the results back to the DataFrame using the group_id
    # Need to handle if rc_group_id is not in group_stats.index (shouldn't happen with valid_groups)
    df_v_grouped['rc_group_total_time'] = df_v_grouped['rc_group_id'].map(group_stats['rc_group_total_time']).fillna(0)
    df_v_grouped['rc_group_num_questions'] = df_v_grouped['rc_group_id'].map(group_stats['rc_group_num_questions']).fillna(0).astype(int)


    # Final cleanup / default values
    df_v_grouped['rc_reading_time'] = df_v_grouped['rc_reading_time'].fillna(0)

    return df_v_grouped

def preprocess_verbal_data(df):
    """Applies preprocessing specific to Verbal data: RC grouping and time calcs."""
    df_processed = df.copy()
    verbal_mask = (df_processed['Subject'] == 'V')
    if not verbal_mask.any():
        # Ensure standard RC columns exist even if no V data
        for col in ['rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']:
             if col not in df_processed.columns:
                  df_processed[col] = pd.Series(dtype='float64' if 'time' in col or 'num' in col else 'Int64' if 'id' in col else 'object') # Use Int64 for ID
                  if 'time' in col or 'num' in col: df_processed[col] = df_processed[col].fillna(0) # Fill numeric
        return df_processed

    # Creates a SUBSET for verbal data
    df_v_subset = df_processed.loc[verbal_mask].copy()

    # Calls the NEW _identify_rc_groups on the SUBSET
    rc_groups_series = _identify_rc_groups(df_v_subset) # Returns a Series
    df_v_subset['rc_group_id'] = rc_groups_series # Assign Series to the subset column

    # Calculate RC times using the NEW group IDs (operates on df_v_subset in place)
    rc_groups_found_in_subset = df_v_subset['rc_group_id'].notna().any() # Check if any groups were successfully assigned
    if rc_groups_found_in_subset:
        df_v_subset = _calculate_rc_times(df_v_subset) # Modifies df_v_subset
    else:
        # Ensure columns exist with defaults if skipped
        if 'rc_reading_time' not in df_v_subset.columns: df_v_subset['rc_reading_time'] = 0.0
        if 'rc_group_total_time' not in df_v_subset.columns: df_v_subset['rc_group_total_time'] = 0.0
        if 'rc_group_num_questions' not in df_v_subset.columns: df_v_subset['rc_group_num_questions'] = 0


    # --- Update df_processed using .loc assignment ---
    cols_to_update_from_subset = ['rc_group_id']
    # Add other RC cols only if they were potentially calculated
    if rc_groups_found_in_subset:
         calculated_rc_cols = ['rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']
         for col in calculated_rc_cols:
              if col in df_v_subset.columns:
                   cols_to_update_from_subset.append(col)
              else:
                   logging.warning(f"Column '{col}' missing in df_v_subset after _calculate_rc_times.")

    for col in cols_to_update_from_subset:
        if col not in df_processed.columns:
            # Add column with appropriate dtype
            dtype = 'Int64' if col == 'rc_group_id' else 'float64' if 'time' in col or 'num' in col else 'object'
            df_processed[col] = pd.Series(dtype=dtype)

        # Assign values using .loc
        if col in df_v_subset.columns:
            df_processed.loc[verbal_mask, col] = df_v_subset[col]
        else:
             logging.error(f"Column '{col}' missing in df_v_subset during .loc update.")

    # --- Log after update ---
    if 'rc_group_id' not in df_processed.columns:
        logging.warning("'rc_group_id' column NOT FOUND in df_processed AFTER .loc update.") # KEEP this warning


    # Ensure standard RC columns exist in the final df and fill NaNs appropriately for non-verbal rows
    for col in ['rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']:
        if col not in df_processed.columns:
            dtype = 'Int64' if col == 'rc_group_id' else 'float64' # Default others to float
            df_processed[col] = pd.Series(dtype=dtype)
        # Fill NaNs ONLY for non-verbal rows for numeric cols calculated by RC logic
        numeric_rc_cols = ['rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']
        if col in numeric_rc_cols:
            df_processed.loc[~verbal_mask, col] = df_processed.loc[~verbal_mask, col].fillna(0)
        # 'rc_group_id' should remain NaN (or <NA> for Int64) for non-verbal rows

    return df_processed 