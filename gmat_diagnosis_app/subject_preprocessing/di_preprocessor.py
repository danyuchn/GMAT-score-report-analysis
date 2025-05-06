# -*- coding: utf-8 -*-
"""Functions for preprocessing Data Insights (DI) section data, especially MSR groups."""
import pandas as pd
import numpy as np
import warnings
import logging

def _identify_msr_groups(df_di_subset):
    """
    Identifies MSR groups based on 'MSR Set ID' or question contiguity.
    Adds 'msr_group_id' to the DataFrame.
    """
    if 'MSR Set ID' in df_di_subset.columns and df_di_subset['MSR Set ID'].notna().any():
        df_di_subset['msr_group_id'] = 'MSR-' + df_di_subset['MSR Set ID'].astype(str)
    else:
        logging.debug("'MSR Set ID' column missing or empty for DI. Attempting to group by contiguity.")
        df_di_subset = df_di_subset.sort_values(by='question_position')
        is_msr = (df_di_subset['question_type'] == 'Multi-source reasoning')
        
        group_markers = (~is_msr).cumsum()
        
        df_di_subset['msr_group_id'] = pd.Series(index=df_di_subset.index, dtype='object')
        
        df_di_subset.loc[is_msr, 'msr_group_id'] = 'MSRG-' + group_markers[is_msr].astype(str)
        
        df_di_subset.loc[~is_msr, 'msr_group_id'] = np.nan
    return df_di_subset

def preprocess_di_data(df):
    """Applies preprocessing specific to DI data, primarily MSR grouping."""
    df_processed = df.copy()
    di_mask = (df_processed['Subject'] == 'DI')
    if not di_mask.any():
        if 'msr_group_id' not in df_processed.columns: # Ensure column exists
            df_processed['msr_group_id'] = pd.Series(dtype='object') 
        return df_processed

    df_di_subset = df_processed[di_mask].copy() 
    df_di_subset = _identify_msr_groups(df_di_subset)
    df_processed.update(df_di_subset) 

    if 'msr_group_id' not in df_processed.columns: # Ensure column exists after update
         df_processed['msr_group_id'] = pd.Series(dtype='object')
    elif df_processed['msr_group_id'].isna().all() and not df_di_subset.empty:
        # If all are NaN after processing DI rows, it means no MSR groups were identified or DI was empty.
        # This is fine, just ensure the column type is consistent if it was all NaNs.
        pass 

    return df_processed 