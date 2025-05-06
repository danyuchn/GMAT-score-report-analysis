# -*- coding: utf-8 -*-
"""Functions for preprocessing Verbal section data, especially RC groups."""
import pandas as pd
import numpy as np
import warnings
import logging

def _calculate_rc_times(df_v_grouped):
    """Calculate reading time and total group time for RC passages."""
    # Calculate reading time: time of the first question in the group.
    # Using transform to broadcast the first question's time to all questions in the group.
    # Ensure question_position is numeric and handle potential NaNs before idxmin
    df_v_grouped['q_pos_numeric'] = pd.to_numeric(df_v_grouped['question_position'], errors='coerce')
    
    # Get the index of the first question per group
    # Need to handle groups where all q_pos_numeric might be NaN
    first_q_indices = []
    for name, group in df_v_grouped.groupby('rc_group_id', dropna=False):
        if group['q_pos_numeric'].notna().any():
            first_q_indices.append(group['q_pos_numeric'].idxmin())
        # else: group has no valid question_position, reading time will be NaN/0 later

    # Create a boolean series for first questions
    is_first_q = pd.Series(False, index=df_v_grouped.index)
    if first_q_indices:
        is_first_q.loc[first_q_indices] = True

    # Assign reading time (time of first question) to all questions in the group
    # Using a map or join approach for clarity if transform is complex
    reading_time_map = {}
    if first_q_indices:
        reading_time_map = df_v_grouped.loc[is_first_q].set_index('rc_group_id')['question_time'].to_dict()
    
    df_v_grouped['rc_reading_time'] = df_v_grouped['rc_group_id'].map(reading_time_map)
    df_v_grouped['rc_reading_time'] = pd.to_numeric(df_v_grouped['rc_reading_time'], errors='coerce').fillna(0)

    # Calculate total time for each RC group.
    group_total_time_map = df_v_grouped.groupby('rc_group_id')['question_time'].sum().to_dict()
    df_v_grouped['rc_group_total_time'] = df_v_grouped['rc_group_id'].map(group_total_time_map)
    df_v_grouped['rc_group_total_time'] = pd.to_numeric(df_v_grouped['rc_group_total_time'], errors='coerce').fillna(0)

    # Calculate number of questions in each RC group
    group_num_questions_map = df_v_grouped.groupby('rc_group_id').size().to_dict()
    df_v_grouped['rc_group_num_questions'] = df_v_grouped['rc_group_id'].map(group_num_questions_map).fillna(0)
    
    df_v_grouped.drop(columns=['q_pos_numeric'], inplace=True, errors='ignore')
    return df_v_grouped

def _identify_rc_groups(df_v_subset):
    """Identifies RC groups based on 'Passage ID' or question contiguity."""
    if 'Passage ID' in df_v_subset.columns and df_v_subset['Passage ID'].notna().any():
        # Ensure Passage ID is treated as string to avoid float issues from pd.factorize if some are numeric
        df_v_subset['rc_group_id'] = 'P-' + df_v_subset['Passage ID'].astype(str)
    else:
        logging.debug("'Passage ID' column missing or empty for Verbal RC. Attempting to group by contiguity.")
        # Fallback: Group consecutive RC questions if no Passage ID
        # Sort by question_position first to ensure contiguity logic works
        df_v_subset = df_v_subset.sort_values(by='question_position')
        is_rc = (df_v_subset['question_type'] == 'Reading Comprehension')
        
        # Calculate group numbers (integer) for creating distinct group IDs
        group_markers = (~is_rc).cumsum()
        
        # Initialize 'rc_group_id' as object dtype to hold strings or NaN
        df_v_subset['rc_group_id'] = pd.Series(index=df_v_subset.index, dtype='object')
        
        # Assign string-based group IDs to RC questions
        df_v_subset.loc[is_rc, 'rc_group_id'] = 'RCG-' + group_markers[is_rc].astype(str)
        
        # Non-RC questions get NaN group_id (this is the default for an object series if not assigned)
        df_v_subset.loc[~is_rc, 'rc_group_id'] = np.nan 
    return df_v_subset

def preprocess_verbal_data(df):
    """Applies preprocessing specific to Verbal data: RC grouping and time calcs."""
    df_processed = df.copy()
    verbal_mask = (df_processed['Subject'] == 'V')
    if not verbal_mask.any():
        return df_processed # No verbal data to process

    df_v_subset = df_processed[verbal_mask].copy()

    # Ensure question_time is numeric before calculations
    df_v_subset['question_time'] = pd.to_numeric(df_v_subset['question_time'], errors='coerce')

    df_v_subset = _identify_rc_groups(df_v_subset)
    
    # Calculate RC times only if there are RC groups identified
    if 'rc_group_id' in df_v_subset.columns and df_v_subset['rc_group_id'].notna().any():
        # Apply calculations only to rows that are part of an RC group
        rc_rows_mask = df_v_subset['rc_group_id'].notna() & (df_v_subset['question_type'] == 'Reading Comprehension')
        if rc_rows_mask.any():
            df_v_rc_part = df_v_subset[rc_rows_mask].copy()
            df_v_rc_part = _calculate_rc_times(df_v_rc_part) # Pass only the relevant part
            # Update the subset with new/modified RC columns
            df_v_subset.update(df_v_rc_part)

    # Update the original DataFrame with the processed verbal subset
    df_processed.update(df_v_subset)
    
    # Ensure standard RC columns exist in the main df, even if no V data or no RC groups
    # These are used by overtime calculation, so good to have them with NaN/0 if not applicable
    for col in ['rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions']:
        if col not in df_processed.columns:
            if 'float' in str(df[col].dtype if col in df.columns else 'float'): # Preserve dtype if possible
                 df_processed[col] = pd.Series(dtype='float64')
            else:
                 df_processed[col] = pd.Series(dtype='object') # Default to object if unsure
        # Fill NaNs introduced if only a subset was processed by _calculate_rc_times
        # This happens if update() doesn't fill all rows correctly for new columns
        if col in df_processed.columns and df_processed[col].isna().any():
            if 'time' in col or 'num' in col: # Numeric columns fill with 0
                df_processed[col] = df_processed[col].fillna(0)
            # 'rc_group_id' can remain NaN if not applicable

    return df_processed 