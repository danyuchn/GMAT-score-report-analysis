# -*- coding: utf-8 -*-
"""Functions for analyzing time usage and calculating overtime."""
import pandas as pd
import warnings
from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import THRESHOLDS

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

    msr_group_overtime_map = {}
    if 'msr_group_id' in df_di.columns:
        msr_groups = df_di[df_di['question_type'] == 'MSR'].groupby('msr_group_id', dropna=True)
        for group_id, group_df in msr_groups:
             group_total_time = group_df['q_time_numeric'].sum(skipna=True)
             target_time = msr_target_times['pressure'] if pressure else msr_target_times['no_pressure']
             msr_group_overtime_map[group_id] = group_total_time > target_time
    else:
        warnings.warn("DI overtime: Missing 'msr_group_id' column, cannot calculate MSR group overtime.", UserWarning, stacklevel=3)

    for q_type, type_thresholds in overtime_thresholds.items():
        if q_type == 'MSR_TARGET': continue
        type_mask = (df_di['question_type'] == q_type)
        if not type_mask.any(): continue
        threshold = type_thresholds['pressure'] if pressure else type_thresholds['no_pressure']
        is_type_overtime = (df_di['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[type_mask & is_type_overtime] = True

    msr_mask = (df_di['question_type'] == 'MSR')
    if msr_mask.any() and 'msr_group_id' in df_di.columns:
         is_msr_group_overtime = df_di['msr_group_id'].map(msr_group_overtime_map).fillna(False)
         overtime_mask.loc[msr_mask & is_msr_group_overtime] = True
    return overtime_mask

def _calculate_overtime_v(df_v, pressure, thresholds):
    """Calculates overtime mask for V section."""
    overtime_mask = pd.Series(False, index=df_v.index)
    overtime_thresholds = thresholds['OVERTIME']
    cr_thresholds = overtime_thresholds['CR']
    rc_ind_threshold = overtime_thresholds['RC_INDIVIDUAL']
    rc_group_targets = overtime_thresholds['RC_GROUP_TARGET']

    rc_cols_present = all(c in df_v.columns for c in ['rc_group_id', 'rc_group_total_time', 'rc_reading_time'])
    if not rc_cols_present:
        warnings.warn("Verbal overtime: Missing preprocessed RC columns. RC overtime calculation will be skipped.", UserWarning, stacklevel=3)

    cr_mask = (df_v['question_type'] == 'Critical Reasoning')
    if cr_mask.any():
        threshold = cr_thresholds['pressure'] if pressure else cr_thresholds['no_pressure']
        is_cr_overtime = (df_v['q_time_numeric'] > threshold).fillna(False)
        overtime_mask.loc[cr_mask & is_cr_overtime] = True

    rc_mask = (df_v['question_type'] == 'Reading Comprehension')
    if rc_mask.any() and rc_cols_present:
        # Individual RC Question Overtime (simple)
        is_rc_ind_overtime = (df_v['q_time_numeric'] > rc_ind_threshold).fillna(False)
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
    return overtime_mask

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

    df_with_overtime.drop(columns=['q_time_numeric'], inplace=True, errors='ignore')
    return df_with_overtime 