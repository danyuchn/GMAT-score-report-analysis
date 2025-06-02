# -*- coding: utf-8 -*-
"""Functions for preprocessing Data Insights (DI) section data, especially MSR groups."""
import pandas as pd
import numpy as np
import logging

def _identify_msr_groups(df_di_subset):
    """
    Identifies MSR groups based on 'MSR Set ID' or question contiguity.
    Adds 'msr_group_id' to the DataFrame.
    """
    if 'MSR Set ID' in df_di_subset.columns and df_di_subset['MSR Set ID'].notna().any():
        # 修復: 先初始化所有行為NaN，然後只為有MSR Set ID的行設置值
        df_di_subset['msr_group_id'] = pd.Series(index=df_di_subset.index, dtype='object')
        msr_set_mask = df_di_subset['MSR Set ID'].notna()
        df_di_subset.loc[msr_set_mask, 'msr_group_id'] = 'MSR-' + df_di_subset.loc[msr_set_mask, 'MSR Set ID'].astype(str)
        df_di_subset.loc[~msr_set_mask, 'msr_group_id'] = pd.NA
    else:
        logging.debug("'MSR Set ID' column missing or empty for DI. Attempting to group by contiguity.")
        df_di_subset = df_di_subset.sort_values(by='question_position')
        is_msr = (df_di_subset['question_type'] == 'Multi-source reasoning')
        
        group_markers = (~is_msr).cumsum()
        
        df_di_subset['msr_group_id'] = pd.Series(index=df_di_subset.index, dtype='object')
        
        df_di_subset.loc[is_msr, 'msr_group_id'] = 'MSRG-' + group_markers[is_msr].astype(str)
        
        df_di_subset.loc[~is_msr, 'msr_group_id'] = pd.NA
    return df_di_subset

def preprocess_di_data(df):
    """Applies preprocessing specific to DI data, primarily MSR grouping and time calculations."""
    df_processed = df.copy()
    di_mask = (df_processed['Subject'] == 'DI')
    if not di_mask.any():
        # Ensure MSR specific columns exist even if no DI data, similar to verbal_preprocessor
        for col in ['msr_group_id', 'msr_group_total_time', 'msr_group_num_questions', 'msr_reading_time', 'is_first_msr_q']:
            if col not in df_processed.columns:
                df_processed[col] = pd.Series(dtype='object' if col == 'msr_group_id' else 'float64')
        return df_processed

    df_di_subset = df_processed[di_mask].copy() 
    df_di_subset['question_time'] = pd.to_numeric(df_di_subset['question_time'], errors='coerce') # Ensure numeric for sum
    
    # 初始化MSR相關列
    df_di_subset['msr_group_total_time'] = 0.0
    df_di_subset['msr_group_num_questions'] = 0.0  
    df_di_subset['msr_reading_time'] = 0.0
    df_di_subset['is_first_msr_q'] = False
    
    df_di_subset = _identify_msr_groups(df_di_subset)

    # Calculate MSR group total time, number of questions, and reading time
    if 'msr_group_id' in df_di_subset.columns and df_di_subset['msr_group_id'].notna().any():
        msr_rows_mask = df_di_subset['msr_group_id'].notna() & (df_di_subset['question_type'] == 'Multi-source reasoning')
        if msr_rows_mask.any():
            df_msr_part = df_di_subset[msr_rows_mask].copy()
            df_msr_part['question_position'] = pd.to_numeric(df_msr_part['question_position'], errors='coerce') # Ensure numeric for idxmin
            
            # Group Total Time
            group_total_time_map = df_msr_part.groupby('msr_group_id')['question_time'].sum().to_dict()
            df_msr_part['msr_group_total_time'] = df_msr_part['msr_group_id'].map(group_total_time_map)
            
            # Group Num Questions
            group_num_questions_map = df_msr_part.groupby('msr_group_id').size().to_dict()
            df_msr_part['msr_group_num_questions'] = df_msr_part['msr_group_id'].map(group_num_questions_map)

            # MSR Reading Time
            df_msr_part['msr_reading_time'] = 0.0 # Initialize
            first_q_indices_msr = []
            group_data_for_reading_time_msr = {}

            for name, group in df_msr_part.groupby('msr_group_id', dropna=False):
                if group['question_position'].notna().any() and len(group) >= 2: # Only if group has at least 2 questions
                    first_q_idx_msr = group['question_position'].idxmin()
                    first_q_indices_msr.append(first_q_idx_msr)
                    first_q_time_msr = group.loc[first_q_idx_msr, 'question_time']
                    other_qs_time_msr = group.loc[group.index != first_q_idx_msr, 'question_time']
                    
                    # Calculate MSR reading time according to MD document: only for groups with at least 2 questions
                    if not other_qs_time_msr.empty:
                        avg_other_qs_time_msr = other_qs_time_msr.mean()
                        calculated_msr_reading_time = first_q_time_msr - avg_other_qs_time_msr
                        df_msr_part.loc[first_q_idx_msr, 'msr_reading_time'] = calculated_msr_reading_time
                    # Note: For single-question MSR groups, msr_reading_time remains 0.0 (MD document: "此計算僅在題組包含至少兩題時有效")

            df_msr_part['msr_reading_time'] = pd.to_numeric(df_msr_part['msr_reading_time'], errors='coerce')
            df_msr_part['msr_reading_time'] = df_msr_part['msr_reading_time'].replace({pd.NA: 0, None: 0, np.nan: 0}).infer_objects(copy=False)

            # Add is_first_msr_q flag
            df_msr_part['is_first_msr_q'] = False
            if first_q_indices_msr: # Check if list is not empty
                # Ensure indices are valid for df_msr_part before trying to loc
                valid_first_q_indices = [idx for idx in first_q_indices_msr if idx in df_msr_part.index]
                if valid_first_q_indices:
                    df_msr_part.loc[valid_first_q_indices, 'is_first_msr_q'] = True

            # 修復: 使用更精確的方式更新MSR相關列，避免覆蓋其他數據
            msr_cols_to_update = ['msr_group_total_time', 'msr_group_num_questions', 'msr_reading_time', 'is_first_msr_q']
            for col in msr_cols_to_update:
                if col in df_msr_part.columns:
                    df_di_subset.loc[msr_rows_mask, col] = df_msr_part[col].values

    # 修復: 先確保主DataFrame中有所有MSR欄位，然後才進行update
    msr_all_cols = ['msr_group_id', 'msr_group_total_time', 'msr_group_num_questions', 'msr_reading_time', 'is_first_msr_q']
    for col in msr_all_cols:
        if col not in df_processed.columns:
            if col == 'msr_group_id':
                df_processed[col] = pd.NA
            elif col == 'is_first_msr_q':
                df_processed[col] = False
            else:
                df_processed[col] = 0.0

    df_processed.update(df_di_subset)

    return df_processed 