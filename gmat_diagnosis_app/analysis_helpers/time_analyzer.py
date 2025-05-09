# -*- coding: utf-8 -*-
"""Functions for analyzing time usage and calculating overtime."""
import pandas as pd
import warnings
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import THRESHOLDS

def _calculate_overtime_q(df_q, pressure, thresholds):
    """Calculates overtime mask for Q section."""
    threshold = thresholds['OVERTIME_PRESSURE'] if pressure else thresholds['OVERTIME_NO_PRESSURE']
    # Only calculate overtime for valid questions
    valid_rows_mask = df_q.get('is_invalid', pd.Series(False, index=df_q.index)) == False
    is_overtime = pd.Series(False, index=df_q.index) # Initialize with False
    # Apply overtime logic only to valid rows
    is_overtime.loc[valid_rows_mask] = (df_q.loc[valid_rows_mask, 'q_time_numeric'] > threshold)
    return is_overtime.fillna(False)

def _calculate_overtime_di(df_di, pressure, thresholds):
    """Calculates overtime mask for DI section."""
    overtime_mask = pd.Series(False, index=df_di.index)
    # Ensure q_time_numeric exists, if not, create it from question_time
    if 'q_time_numeric' not in df_di.columns:
        df_di['q_time_numeric'] = pd.to_numeric(df_di['question_time'], errors='coerce')

    overtime_thresholds_config = thresholds['OVERTIME'] # This is THRESHOLDS['DI']['OVERTIME']
    msr_target_times = overtime_thresholds_config.get('MSR_TARGET', {})
    msr_individual_threshold = overtime_thresholds_config.get('MSR_INDIVIDUAL_THRESHOLD', 1.5) # Default from DI Doc if not in JSON

    # --- MSR Group Overtime --- 
    msr_group_overtime = pd.Series(False, index=df_di.index)
    if 'msr_group_id' in df_di.columns and 'msr_group_total_time' in df_di.columns:
        # Iterate over unique group_ids for MSR questions to apply group logic once per group
        unique_msr_groups = df_di.loc[(df_di['question_type'] == 'MSR') & (df_di['msr_group_id'].notna()), 'msr_group_id'].unique()
        for group_id in unique_msr_groups:
            group_data = df_di[(df_di['msr_group_id'] == group_id) & (df_di['question_type'] == 'MSR')]
            if group_data.empty: continue

            actual_group_total_time = group_data['msr_group_total_time'].iloc[0] # Assuming consistent within group post-preprocessing
            target_time_for_group = msr_target_times.get('pressure' if pressure else 'no_pressure', 6.0 if pressure else 7.0) # Default from DI Doc

            if actual_group_total_time > target_time_for_group:
                msr_group_overtime.loc[group_data.index] = True
    else:
        warnings.warn("DI overtime: Missing 'msr_group_id' or 'msr_group_total_time' column. Cannot calculate MSR group overtime.", UserWarning, stacklevel=3)

    # --- MSR Individual Question Overtime ---
    msr_individual_overtime = pd.Series(False, index=df_di.index)
    msr_mask_for_individual = (df_di['question_type'] == 'MSR')
    if msr_mask_for_individual.any() and 'msr_reading_time' in df_di.columns and 'msr_group_id' in df_di.columns:
        df_di['adjusted_msr_time'] = df_di['q_time_numeric']
        # msr_reading_time is non-zero ONLY for the first question of each group (from di_preprocessor)
        first_q_msr_mask = msr_mask_for_individual & df_di['msr_group_id'].notna() & (df_di['msr_reading_time'] != 0)
        df_di.loc[first_q_msr_mask, 'adjusted_msr_time'] = df_di.loc[first_q_msr_mask, 'q_time_numeric'] - df_di.loc[first_q_msr_mask, 'msr_reading_time']
        
        is_msr_ind_overtime = (df_di['adjusted_msr_time'] > msr_individual_threshold).fillna(False)
        msr_individual_overtime.loc[msr_mask_for_individual & is_msr_ind_overtime] = True
    # else: warnings.warn for missing msr_reading_time could be added if strict notification is needed.

    # --- Combine MSR Overtime flags ---
    final_msr_overtime = msr_group_overtime | msr_individual_overtime
    overtime_mask.loc[df_di['question_type'] == 'MSR'] = final_msr_overtime[df_di['question_type'] == 'MSR']

    # --- Non-MSR Question Types Overtime (DS, TPA, GT) ---
    for q_type, type_thresholds_map in overtime_thresholds_config.items():
        if q_type in ['MSR_TARGET', 'MSR_INDIVIDUAL_THRESHOLD']: continue # Skip MSR specific config keys handled above
        
        type_mask = (df_di['question_type'] == q_type)
        if not type_mask.any(): continue
        
        # Ensure type_thresholds_map is a dict (e.g., {'pressure': 2.0, 'no_pressure': 2.5})
        if isinstance(type_thresholds_map, dict):
            threshold_value = type_thresholds_map.get('pressure' if pressure else 'no_pressure')
            if threshold_value is not None:
                is_type_overtime = (df_di['q_time_numeric'] > threshold_value).fillna(False)
                overtime_mask.loc[type_mask & is_type_overtime] = True
            # else: warnings.warn for missing pressure/no_pressure key in threshold_value
        # else: warnings.warn for type_thresholds_map not being a dict for a given q_type

    if 'adjusted_msr_time' in df_di.columns: # Clean up temp column from df_di (which is a copy)
        df_di.drop(columns=['adjusted_msr_time'], inplace=True, errors='ignore')
        
    return overtime_mask

def _calculate_overtime_v(df_v, pressure, thresholds):
    """Calculates overtime mask for V section."""
    overtime_mask = pd.Series(False, index=df_v.index)
    overtime_thresholds = thresholds['OVERTIME']
    cr_thresholds = overtime_thresholds['CR']
    rc_ind_threshold = overtime_thresholds['RC_INDIVIDUAL']
    rc_group_targets = overtime_thresholds['RC_GROUP_TARGET']

    # Ensure q_time_numeric exists, if not, create it from question_time
    if 'q_time_numeric' not in df_v.columns:
        df_v['q_time_numeric'] = pd.to_numeric(df_v['question_time'], errors='coerce')

    rc_cols_present = all(c in df_v.columns for c in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time', 'rc_group_num_questions']) # Added rc_group_num_questions for completeness
    if not rc_cols_present:
        warnings.warn("Verbal overtime: Missing preprocessed RC columns. RC overtime calculation will be skipped.", UserWarning, stacklevel=3)

    cr_mask = (df_v['question_type'] == 'Critical Reasoning')
    if cr_mask.any():
        threshold = cr_thresholds['pressure'] if pressure else cr_thresholds['no_pressure']
        is_cr_overtime = (df_v['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[cr_mask & is_cr_overtime] = True

    rc_mask = (df_v['question_type'] == 'Reading Comprehension')
    if rc_mask.any() and rc_cols_present:
        # Adjusted RC individual question time calculation
        # Initialize adjusted_rc_time with original question_time
        df_v['adjusted_rc_time'] = df_v['q_time_numeric']
        
        # Identify first questions in each RC group
        # Assuming rc_reading_time is non-zero only for the first question of a group as per prior correction
        # or that it holds the value to be subtracted for the first question.
        # A more robust way is to check question_position within the group if available and sorted.
        # For now, relying on rc_reading_time structure from verbal_preprocessor.py
        # A common approach for identifying first question of a group:
        # df_v['is_first_in_rc_group'] = df_v.groupby('rc_group_id')['question_position'].transform(lambda x: x == x.min())
        # However, question_position might not be globally unique or perfectly ordered if df_v is a slice.
        # The verbal_preprocessor.py stores rc_reading_time specifically on the first question.
        # So, if rc_reading_time > 0, it implies it is the first question and has the value to subtract.
        
        # To correctly identify the first question for subtraction based on our verbal_preprocessor logic for rc_reading_time:
        # rc_reading_time is non-zero ONLY for the first question of each group.
        first_q_rc_mask = (df_v['question_type'] == 'Reading Comprehension') & df_v['rc_group_id'].notna() & (df_v['rc_reading_time'] != 0)      
        
        df_v.loc[first_q_rc_mask, 'adjusted_rc_time'] = df_v.loc[first_q_rc_mask, 'q_time_numeric'] - df_v.loc[first_q_rc_mask, 'rc_reading_time']
        
        # Individual RC Question Overtime based on adjusted_rc_time
        is_rc_ind_overtime = (df_v['adjusted_rc_time'] > rc_ind_threshold).fillna(False) # rc_ind_threshold is 2.0 mins as per doc
        overtime_mask.loc[rc_mask & is_rc_ind_overtime] = True

        # RC Group Overtime (based on precalculated group times)
        # Iterate through unique group_ids for RC questions to apply group logic once per group
        unique_rc_groups = df_v.loc[rc_mask & df_v['rc_group_id'].notna(), 'rc_group_id'].unique()
        for group_id in unique_rc_groups:
            group_data = df_v[(df_v['rc_group_id'] == group_id) & rc_mask]
            if group_data.empty: continue

            num_questions_in_group = group_data['rc_group_num_questions'].iloc[0] # Assuming consistent within group
            group_total_time = group_data['rc_group_total_time'].iloc[0]
            
            target_key = f"{int(num_questions_in_group)}Q" if num_questions_in_group in [3,4] else None
            if target_key and target_key in rc_group_targets:
                group_target_times = rc_group_targets[target_key]
                target_time_for_group = group_target_times['pressure'] if pressure else group_target_times['no_pressure']
                
                # RC Group overtime is defined as actual total time > target + 1 min buffer
                if group_total_time > (target_time_for_group + 1.0):
                    overtime_mask.loc[group_data.index] = True # Mark all questions in this group as overtime

    # Clean up temp column from df_v (which is a copy)
    if 'adjusted_rc_time' in df_v.columns:
        df_v.drop(columns=['adjusted_rc_time'], inplace=True, errors='ignore')
    
    return overtime_mask # Ensure the function returns the calculated mask

def calculate_overtime(df, time_pressure_status_map):
    """
    Calculates 'overtime' status for each question based on section-specific rules
    and time pressure. This is typically run AFTER initial preprocessing like
    preprocess_verbal_data and preprocess_di_data which add group time info.

    Args:
        df (pd.DataFrame): Combined DataFrame. Requires 'Subject', 'question_time',
                           'question_type'. For V, requires 'rc_group_id', 
                           'rc_group_total_time', 'rc_group_num_questions'.
                           For DI, requires 'msr_group_id'.
        time_pressure_status_map (dict): {'Q': bool, 'DI': bool, 'V': bool}

    Returns:
        pd.DataFrame: DataFrame with an added boolean 'overtime' column.
    """
    if df.empty:
        warnings.warn("Input DataFrame is empty. Cannot calculate overtime.", UserWarning, stacklevel=2)
        df_copy = df.copy()
        df_copy['overtime'] = False
        return df_copy

    df_with_overtime = df.copy()
    df_with_overtime['overtime'] = False
    # Create q_time_numeric once on the main copy we are modifying
    if 'q_time_numeric' not in df_with_overtime.columns: # Add if not exists
      df_with_overtime['q_time_numeric'] = pd.to_numeric(df_with_overtime['question_time'], errors='coerce')

    for section, section_thresholds in THRESHOLDS.items():
        section_mask = (df_with_overtime['Subject'] == section)
        if not section_mask.any():
            continue

        df_section = df_with_overtime[section_mask].copy() # Work on a copy for this section
        pressure = time_pressure_status_map.get(section, False)
        section_overtime_mask = pd.Series(False, index=df_section.index)

        if section == 'Q':
            section_overtime_mask = _calculate_overtime_q(df_section, pressure, section_thresholds)
        elif section == 'DI':
            section_overtime_mask = _calculate_overtime_di(df_section, pressure, section_thresholds)
        elif section == 'V':
            section_overtime_mask = _calculate_overtime_v(df_section, pressure, section_thresholds)
        
        # Update the main dataframe's 'overtime' column for the current section
        df_with_overtime.loc[section_mask, 'overtime'] = section_overtime_mask

    # Clean up the temporary q_time_numeric column from the main df_with_overtime
    if 'q_time_numeric' in df_with_overtime.columns:
        df_with_overtime.drop(columns=['q_time_numeric'], inplace=True, errors='ignore')
        
    return df_with_overtime 