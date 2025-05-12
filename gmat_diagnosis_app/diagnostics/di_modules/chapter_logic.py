import pandas as pd
import numpy as np
import math # Keep math for _check_foundation_override if it moves here later
import logging

# # Basic logging configuration to ensure INFO messages are displayed within this module # Removed by AI
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s') # Removed by AI

from .constants import (
    CARELESSNESS_THRESHOLD,
    TOTAL_QUESTIONS_DI, # Import TOTAL_QUESTIONS_DI
    EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES, # Import new constant
    INVALID_DATA_TAG_DI # Ensure this is imported
)
from .translation import _translate_di # Needed later for other functions
from .utils import _grade_difficulty_di, _format_rate


def _diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """
    Analyzes root causes row-by-row based on Chapter 3 logic from the MD document.
    Adds 'diagnostic_params' and 'is_sfe' columns.
    Relies on 'question_type', 'content_domain', 'question_difficulty', 'question_time',
    'is_correct', 'overtime', 'msr_reading_time', 'is_first_msr_q', and 'is_invalid'.
    MODIFIED: Calculates time_performance_category for ALL rows.
    MODIFIED: Applies SFE and detailed diagnostic_params only to VALID rows.
    """
    # NOTE: This function still uses iterrows() and could be further optimized,
    # but that involves more complex refactoring than requested. Keeping as is.
    if df.empty:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
        df['is_sfe'] = False
        df['time_performance_category'] = 'Unknown' # Added init
        return df

    all_diagnostic_params = []
    all_is_sfe = []
    all_time_performance_categories = []

    max_diff_dict = {}
    if isinstance(max_diffs, pd.DataFrame) and not max_diffs.empty:
        for q_type_col in max_diffs.columns:
            q_type = q_type_col
            for domain in max_diffs.index:
                 max_val = max_diffs.loc[domain, q_type]
                 if pd.notna(max_val) and max_val != -np.inf:
                     max_diff_dict[(q_type, domain)] = max_val

    msr_reading_threshold = ch1_thresholds.get('MSR_READING', 1.5)
    msr_single_q_threshold = ch1_thresholds.get('MSR_SINGLE_Q', 1.5)

    for index, row in df.iterrows():
        params = []
        sfe_triggered = False

        q_type = row.get('question_type', 'Unknown')
        q_domain = row.get('content_domain', 'Unknown')
        q_diff = row.get('question_difficulty', None)
        q_time = row.get('question_time', None)
        is_correct = bool(row.get('is_correct', True))
        is_overtime = bool(row.get('overtime', False))
        msr_reading_time = row.get('msr_reading_time', None)
        is_first_msr_q = bool(row.get('is_first_msr_q', False))
        is_invalid_row = bool(row.get('is_invalid', False)) # Get invalid status for the row

        is_relatively_fast = False
        is_slow = is_overtime # For time category, slow means overtime
        is_normal_time = False
        avg_time_for_type = avg_times.get(q_type, np.inf)

        if pd.notna(q_time) and avg_time_for_type != np.inf:
            if q_time < (avg_time_for_type * 0.75):
                is_relatively_fast = True
            if not is_relatively_fast and not is_slow:
                is_normal_time = True

        current_time_performance_category = 'Unknown'
        if is_correct:
            if is_relatively_fast: current_time_performance_category = 'Fast & Correct'
            elif is_slow: current_time_performance_category = 'Slow & Correct'
            else: current_time_performance_category = 'Normal Time & Correct'
        else:
            if is_relatively_fast: current_time_performance_category = 'Fast & Wrong'
            elif is_slow: current_time_performance_category = 'Slow & Wrong'
            else: current_time_performance_category = 'Normal Time & Wrong'

        # --- Detailed Diagnostic Logic ---
        # These detailed params and SFE should only be applied if the row is NOT invalid.
        if not is_invalid_row:
            # SFE check (only for non-invalid rows)
            if not is_correct and pd.notna(q_diff):
                max_correct_diff_key = (q_type, q_domain)
                max_correct_diff = max_diff_dict.get(max_correct_diff_key, -np.inf)
                if q_diff < max_correct_diff:
                    sfe_triggered = True
                    # Updated SFE tag
                    params.append('DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')

            # A. Data Sufficiency
            if q_type == 'Data Sufficiency':
                if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加數學相關的所有錯誤標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH'])
                        # 添加所有閱讀理解錯誤細分標籤
                        params.extend(['DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX', 
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH']) 
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤及閱讀理解錯誤細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
                elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
            
            # B. Two-Part Analysis
            elif q_type == 'Two-part analysis':
                 if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
                 elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
            
            # C. Graph & Table
            elif q_type == 'Graph and Table':
                 if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
                 elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
            
            # D. Multi-Source Reasoning
            elif q_type == 'Multi-source reasoning':
                if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
                elif q_domain == 'Non-Math Related':
                     if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                     elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH'])
                     elif (is_normal_time or is_relatively_fast) and not is_correct:
                         # 添加所有非數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                         params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN'])
                         if is_relatively_fast: params.append('DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION')
        # --- End Detailed Logic ---
        else: # This row IS invalid
            sfe_triggered = False # Invalid rows are not SFE by this logic
            # params list should be empty or contain only INVALID_DATA_TAG_DI
            # The INVALID_DATA_TAG_DI is usually added in main.py to the original 'diagnostic_params' column.
            # Here, we ensure that if this function is solely responsible for 'params', it reflects invalidity.
            existing_row_params = row.get('diagnostic_params', [])
            if isinstance(existing_row_params, list) and INVALID_DATA_TAG_DI in existing_row_params:
                params = [INVALID_DATA_TAG_DI]
            elif not params: # If no SFE was added (because it's invalid), and params is empty
                params = [INVALID_DATA_TAG_DI]
            # current_time_performance_category is already calculated for all rows and will be used.

        # Ensure INVALID_DATA_TAG_DI is handled correctly if added by main.py
        # and merge with params calculated here (which are empty if invalid_row is true and no SFE)
        original_input_row_params = row.get('diagnostic_params', [])
        if not isinstance(original_input_row_params, list): original_input_row_params = []

        final_params_for_row = []
        if is_invalid_row:
            # For invalid rows, the params list should primarily be [INVALID_DATA_TAG_DI].
            # If main.py already put it in original_input_row_params, use that.
            if INVALID_DATA_TAG_DI in original_input_row_params:
                final_params_for_row = [p for p in original_input_row_params if p == INVALID_DATA_TAG_DI] # Keep only this tag if others exist
                if not final_params_for_row: final_params_for_row = [INVALID_DATA_TAG_DI] # Ensure it's there
            else:
                final_params_for_row = [INVALID_DATA_TAG_DI]
            # sfe_triggered is already False for invalid rows at this point if it came from this function's logic
        else: # Valid row
            # Combine any params from earlier steps (e.g. behavioral from main) with SFE/detailed from here
            temp_combined = original_input_row_params + params
            final_params_for_row = list(dict.fromkeys(temp_combined)) # Remove duplicates
            # Ensure new SFE tag is handled correctly
            if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE' in final_params_for_row:
                final_params_for_row.remove('DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
                final_params_for_row.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
            elif 'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE' in final_params_for_row: # Handle if old tag somehow still present
                 final_params_for_row.remove('DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE')
                 if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE' not in final_params_for_row:
                    final_params_for_row.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
        
        all_diagnostic_params.append(final_params_for_row)
        all_is_sfe.append(sfe_triggered)
        all_time_performance_categories.append(current_time_performance_category) # Appends category for all rows

    # Update the dataframe with all the collected information
    df['diagnostic_params'] = all_diagnostic_params
    df['is_sfe'] = all_is_sfe
    df['time_performance_category'] = all_time_performance_categories

    return df


def _observe_di_patterns(df, avg_times):
    """
    Observes special patterns like carelessness or early rushing (Chapter 4).
    Combines averages with diagnostic output from Chapter 3.
    Uses 'question_type', 'question_time', 'is_correct', 'question_position'.
    """
    analysis = {
        'triggered_behavioral_params': [],
        'carelessness_issue_triggered': False,
        'fast_wrong_rate': 0.0,
        'early_rushing_risk_triggered': False,
        'early_rushing_questions': []
    }
    if df.empty: return analysis

    if 'diagnostic_params' not in df.columns:
        df['diagnostic_params'] = [[] for _ in range(len(df))]
    else:
        df['diagnostic_params'] = df['diagnostic_params'].apply(lambda x: list(x) if isinstance(x, (list, tuple, set)) else [])

    # 檢查並確保time_performance_category存在
    if 'time_performance_category' not in df.columns:
        df['time_performance_category'] = 'Unknown'
    else:
        # 確保沒有空值或空字串
        df['time_performance_category'] = df['time_performance_category'].fillna('Unknown')
        df.loc[df['time_performance_category'] == '', 'time_performance_category'] = 'Unknown'

    # 1. Carelessness Issue - 使用核心邏輯文件中的定義
    fast_wrong_count = 0
    fast_total_count = 0
    if 'time_performance_category' in df.columns:
        fast_wrong_count = df[df['time_performance_category'] == 'Fast & Wrong'].shape[0]
        fast_total_count = df[(df['time_performance_category'].str.startswith('Fast'))].shape[0]
    
    # 如果沒有time_performance_category或計數為0，使用原始邏輯計算fast_wrong_rate
    if fast_total_count == 0:
        # 原始邏輯使用is_relatively_fast的計算
        is_relatively_fast_mask = pd.Series(False, index=df.index)
        for q_type, group in df.groupby('question_type'):
            avg_time = avg_times.get(q_type, np.inf)
            if avg_time != np.inf:
                is_relatively_fast_mask.loc[group.index] = group['question_time'].notna() & (group['question_time'] < avg_time * 0.75)

        fast_total_count = is_relatively_fast_mask.sum()
        if fast_total_count > 0:
            fast_wrong_mask = is_relatively_fast_mask & (df['is_correct'] == False)
            fast_wrong_count = fast_wrong_mask.sum()

    # 計算快錯率並設置觸發條件
    if fast_total_count > 0:
        fast_wrong_rate = fast_wrong_count / fast_total_count
        analysis['fast_wrong_rate'] = fast_wrong_rate
        # 使用核心邏輯文件中定義的閾值判斷粗心問題
        if fast_wrong_rate > CARELESSNESS_THRESHOLD:
            analysis['carelessness_issue_triggered'] = True
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR__CARELESSNESS_ISSUE')
            # Mark these questions in diagnostic_params
            if 'time_performance_category' in df.columns:
                for idx, row in df[df['time_performance_category'] == 'Fast & Wrong'].iterrows():
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_CARELESSNESS_DETAIL_OMISSION']
            else:
                for idx in df.index[fast_wrong_mask]:
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_CARELESSNESS_DETAIL_OMISSION']

    # 2. Early Rushing Risk (遵循核心邏輯文件第四章)
    if 'question_position' in df.columns and 'question_time' in df.columns:
        # 定義前三分之一的題目位置
        # 使用 TOTAL_QUESTIONS_DI 作為總題數基數
        first_third_q_count = TOTAL_QUESTIONS_DI // 3
        # 篩選出實際在前三分之一位置的題目 (基於 1-indexed question_position)
        early_rushing_mask = (
            df['question_position'].notna() &
            (df['question_position'] <= first_third_q_count) &
            df['question_time'].notna() &
            (df['question_time'] < EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES) # 使用絕對閾值
        )
        early_rushing_questions = df.loc[early_rushing_mask].sort_values('question_position')
        
        if len(early_rushing_questions) > 0:
            analysis['early_rushing_risk_triggered'] = True
            analysis['early_rushing_questions'] = early_rushing_questions['question_position'].tolist()
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
            # Mark these questions in diagnostic_params
            for idx in early_rushing_questions.index:
                if 'diagnostic_params' in df.columns:
                    df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK']

    return analysis 

def _check_foundation_override(df, type_metrics):
    """Checks for foundation override rule for each question type."""
    override_results = {}
    if df.empty or 'question_type' not in df.columns: return override_results

    question_types_in_data = df['question_type'].unique()

    for q_type in question_types_in_data:
        if pd.isna(q_type): continue

        metrics = type_metrics.get(q_type, {})
        error_rate = metrics.get('error_rate', 0.0)
        overtime_rate = metrics.get('overtime_rate', 0.0)
        triggered = False
        y_agg = None
        z_agg = None

        # 使用 0.50（50%）作為閾值，與核心邏輯文件中的規定一致
        if error_rate > 0.50 or overtime_rate > 0.50:
            triggered = True
            # Check required columns exist before filtering
            req_cols = ['question_type', 'is_correct', 'overtime', 'question_difficulty']
            # Add msr_group_id and msr_group_total_time for MSR logic
            if q_type == 'Multi-source reasoning':
                req_cols.extend(['msr_group_id', 'msr_group_total_time'])
            else: # For other types, we need question_time
                req_cols.append('question_time')
                
            if all(c in df.columns for c in req_cols):
                triggering_mask = (
                    (df['question_type'] == q_type) &
                    ((df['is_correct'] == False) | (df['overtime'] == True))
                )
                triggering_df = df[triggering_mask]

                if not triggering_df.empty:
                    if 'question_difficulty' in triggering_df.columns and triggering_df['question_difficulty'].notna().any(): # Ensure column exists before accessing
                         min_difficulty = triggering_df['question_difficulty'].min()
                         y_agg = _grade_difficulty_di(min_difficulty)
                    else: y_agg = "未知難度"

                    # --- MODIFIED Z_agg Calculation ---
                    if q_type == 'Multi-source reasoning':
                        if 'msr_group_id' in triggering_df.columns and 'msr_group_total_time' in df.columns:
                            triggering_group_ids = triggering_df['msr_group_id'].unique()
                            # Filter original df for these groups and get max total time
                            group_times = df[df['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
                            if group_times.notna().any():
                                max_group_time_minutes = group_times.max()
                                if pd.notna(max_group_time_minutes):
                                    calculated_z_agg = math.floor(max_group_time_minutes * 2) / 2.0
                                    z_agg = max(calculated_z_agg, 6.0) # Apply 6.0 min floor
                                else: z_agg = 6.0 # Default to floor if max_group_time is NaN
                            else: z_agg = 6.0 # Default to floor if no valid group times found
                        else: z_agg = 6.0 # Default to floor if required MSR columns are missing
                    else: # Original logic for non-MSR types
                        if 'question_time' in triggering_df.columns and triggering_df['question_time'].notna().any(): # Ensure column exists
                             max_time_minutes = triggering_df['question_time'].max()
                             # Ensure max_time_minutes is not NaN before floor operation
                             if pd.notna(max_time_minutes):
                                 # 使用向下取整到 0.5 的倍數函數計算 Z 值
                                 z_agg = math.floor(max_time_minutes * 2) / 2.0
                             else: z_agg = None
                        else: z_agg = None
                else:
                     y_agg = "未知難度"
                     z_agg = None # Or z_agg = 6.0 if q_type == 'Multi-source reasoning' and default floor is desired even with empty triggering_df? Currently None.
            else: # Handle missing columns case
                logging.warning(f"[DI Override Check] Missing required columns for {q_type}: {req_cols}. Cannot calculate Y/Z.") # Added logging
                y_agg = "未知難度"
                z_agg = 6.0 if q_type == 'Multi-source reasoning' else None # Apply floor for MSR even if columns missing


        override_results[q_type] = {
            'override_triggered': triggered,
            'Y_agg': y_agg,
            'Z_agg': z_agg,
            'triggering_error_rate': error_rate,
            'triggering_overtime_rate': overtime_rate
        }
    return override_results


def _generate_di_recommendations(df_diagnosed, override_results, domain_tags, time_pressure):
    """Generates practice recommendations based on Chapters 3, 5, and 2 results."""
    if 'question_type' not in df_diagnosed.columns or 'content_domain' not in df_diagnosed.columns: # Ensure content_domain also exists
        logging.warning("[DI Reco Init] 'question_type' or 'content_domain' missing in df_diagnosed. Returning empty recommendations.")
        return []

    # Ensure 'is_sfe' column exists, defaulting to False if not present.
    # This addresses the issue where missing 'is_sfe' caused Case Recommendations to be skipped.
    if 'is_sfe' not in df_diagnosed.columns:
        logging.warning("[DI Reco Init] 'is_sfe' column was missing in df_diagnosed. Initializing with False.")
        df_diagnosed['is_sfe'] = False

    # Ensure 'diagnostic_params' column exists, defaulting to empty list if not present
    if 'diagnostic_params' not in df_diagnosed.columns:
        logging.warning("[DI Reco Init] 'diagnostic_params' column was missing in df_diagnosed. Initializing with empty lists.")
        df_diagnosed['diagnostic_params'] = [[] for _ in range(len(df_diagnosed))]
    else:
        # Ensure its content is list-like for consistent processing later
        df_diagnosed['diagnostic_params'] = df_diagnosed['diagnostic_params'].apply(
            lambda x: list(x) if isinstance(x, (list, tuple, set)) else ([] if pd.isna(x) else [x] if isinstance(x, str) else [])
        )

    # question_types_in_data = df_diagnosed['question_type'].unique()
    # question_types_valid = [qt for qt in question_types_in_data if pd.notna(qt)]
    # # Initialize recommendations_by_type properly for all valid types
    # recommendations_by_type = {q_type: [] for q_type in question_types_valid if q_type is not None}
    
    CORE_DI_QUESTION_TYPES = ["Data Sufficiency", "Two-part analysis", "Graph and Table", "Multi-source reasoning"]
    recommendations_by_type = {q_type: [] for q_type in CORE_DI_QUESTION_TYPES}
    
    processed_override_types = set()

    # Exemption Rule (per type + domain, as per DI Doc Chapter 5)
    exempted_type_domain_combinations = set()
    if 'is_correct' in df_diagnosed.columns and 'overtime' in df_diagnosed.columns:
        # Group by type and domain to check exemption status for each combination
        grouped_for_exemption = df_diagnosed.groupby(['question_type', 'content_domain'], observed=False, dropna=False)
        for name, group_df in grouped_for_exemption:
            q_type, domain = name
            if pd.isna(q_type) or pd.isna(domain): continue # Skip if type or domain is NaN

            # Check if all questions in this group are correct and not overtime
            if not group_df.empty and not ((group_df['is_correct'] == False) | (group_df['overtime'] == True)).any():
                exempted_type_domain_combinations.add((q_type, domain))

    # Macro Recommendations
    math_related_zh = _translate_di('Math Related') # Translate once
    non_math_related_zh = _translate_di('Non-Math Related') # Translate once
    for q_type, override_info in override_results.items():
        if q_type in recommendations_by_type and override_info.get('override_triggered'):
            # Check if all content domains for this q_type are exempted
            all_domains_for_this_q_type_in_data = df_diagnosed[df_diagnosed['question_type'] == q_type]['content_domain'].unique()
            all_domains_for_this_q_type_in_data = [d for d in all_domains_for_this_q_type_in_data if pd.notna(d)] # Filter out NaN domains

            if not all_domains_for_this_q_type_in_data: # If the q_type has no actual content domains in the data
                pass # Proceed to generate macro recommendation as we can't confirm full exemption
            else:
                all_sub_domains_exempted = True
                for domain_for_q_type in all_domains_for_this_q_type_in_data:
                    if (q_type, domain_for_q_type) not in exempted_type_domain_combinations:
                        all_sub_domains_exempted = False
                        break
                
                if all_sub_domains_exempted:
                    logging.info(f"[DI Reco Logic] SKIPPING Macro recommendation for q_type '{q_type}' because all its sub-domains are exempted (perfect performance).")
                    # We still add to processed_override_types because if an override was triggered,
                    # it implies a general issue, and we might not want case recommendations
                    # even if the macro one is suppressed due to perfect sub-domain performance.
                    # This aligns with the existing logic of adding to processed_override_types here.
                    processed_override_types.add(q_type) 
                    continue # Skip generating the macro recommendation for this q_type

            y_agg = override_info.get('Y_agg', '未知難度')
            z_agg = override_info.get('Z_agg')
            z_agg_text = f"{z_agg:.1f} 分鐘" if pd.notna(z_agg) else "未知限時"
            error_rate_str = _format_rate(override_info.get('triggering_error_rate', 0.0))
            overtime_rate_str = _format_rate(override_info.get('triggering_overtime_rate', 0.0))
            rec_text = f"**宏觀建議 ({q_type}):** 由於整體表現有較大提升空間 (錯誤率 {error_rate_str} 或 超時率 {overtime_rate_str}), "
            rec_text += f"建議全面鞏固 **{q_type}** 題型的基礎，可從 **{y_agg}** 難度題目開始系統性練習，掌握核心方法，建議限時 **{z_agg_text}**。"
            recommendations_by_type[q_type].append({'type': 'macro', 'text': rec_text, 'question_type': q_type})
            processed_override_types.add(q_type)

    # Case Recommendations
    target_times_minutes = {'Data Sufficiency': 2.0, 'Two-part analysis': 3.0, 'Graph and Table': 3.0, 'Multi-source reasoning': 1.5}
    required_cols = ['is_correct', 'overtime', 'question_type', 'content_domain', 'question_difficulty', 'question_time', 'is_sfe', 'diagnostic_params']
    
    # Logging to check columns in df_diagnosed and the condition for case recommendations - REMOVED by AI
    # logging.info(f"[DI Reco Pre-Check] df_diagnosed columns: {list(df_diagnosed.columns)}")
    missing_cols = [col for col in required_cols if col not in df_diagnosed.columns]
    if missing_cols:
        logging.warning(f"[DI Reco Pre-Check] Missing required columns in df_diagnosed for Case Recommendations: {missing_cols}") # Keep warning
    condition_met = all(col in df_diagnosed.columns for col in required_cols)
    # logging.info(f"[DI Reco Pre-Check] Condition 'all(col in df_diagnosed.columns for col in required_cols)' is {condition_met}.") # REMOVED by AI

    if condition_met:
        df_trigger = df_diagnosed[((df_diagnosed['is_correct'] == False) | (df_diagnosed['overtime'] == True))]
        # --- Added Log after creating df_trigger --- REMOVED by AI
        # logging.info(f"[DI Reco Logic] df_trigger created. Is empty: {df_trigger.empty}")
        # if not df_trigger.empty:
        #     logging.info(f"[DI Reco Logic] df_trigger head:\n{df_trigger.head().to_string()}")
        # --- End of Added Log --- REMOVED by AI
        
        if not df_trigger.empty:
            # logging.info(f"[DI Reco Logic] df_trigger is not empty. Row count: {len(df_trigger)}. Unique q_types in trigger: {df_trigger['question_type'].unique()}") # Existing Log - REMOVED by AI
            try:
                grouped_triggers = df_trigger.groupby(['question_type', 'content_domain'], observed=False, dropna=False) # Handle potential NaNs in grouping keys
                for name, group_df in grouped_triggers:
                    q_type, domain = name
                    # logging.info(f"[DI Reco Logic] Processing group: q_type='{q_type}', domain='{domain}'") # Existing Log - REMOVED by AI

                    if pd.isna(q_type) or pd.isna(domain):
                        # logging.info(f"[DI Reco Logic] SKIPPING group ('{q_type}', '{domain}') because q_type or domain is NaN.") # Existing Log - REMOVED by AI
                        continue

                    # --- Added Logging for Skip Conditions --- REMOVED by AI
                    
                    # Original skip logic (kept for completeness)
                    if q_type in processed_override_types:
                        # logging.info(f"[DI Reco Logic] SKIPPING group ('{q_type}', '{domain}') because q_type '{q_type}' is in processed_override_types: {processed_override_types}." ) # MODIFIED Log - REMOVED by AI
                        continue
                    if (q_type, domain) in exempted_type_domain_combinations:
                        # logging.info(f"[DI Reco Logic] SKIPPING group ('{q_type}', '{domain}') because it is in exempted_type_domain_combinations: {exempted_type_domain_combinations}." ) # MODIFIED Log - REMOVED by AI
                        continue
                    
                    # logging.info(f"[DI Reco Logic] PROCEEDING to generate case recommendation for group ('{q_type}', '{domain}'). Row count in group: {len(group_df)}.") # Existing Log - REMOVED by AI

                    min_difficulty_score = group_df['question_difficulty'].min()
                    y_grade = _grade_difficulty_di(min_difficulty_score)

                    # --- Calculate Target Time (MODIFIED FOR MSR) & Max Z ---
                    max_z_minutes = None # Initialize
                    target_time_minutes = None # Initialize
                    if q_type == 'Multi-source reasoning':
                        target_time_minutes = 6.0 if time_pressure else 7.0 # Use group target time based on pressure
                        # Calculate max_z_minutes for MSR using group logic
                        if 'msr_group_id' in group_df.columns and 'msr_group_total_time' in df_diagnosed.columns:
                            triggering_group_ids = group_df['msr_group_id'].unique()
                            group_times = df_diagnosed[df_diagnosed['msr_group_id'].isin(triggering_group_ids)]['msr_group_total_time']
                            if group_times.notna().any():
                                max_group_time_minutes = group_times.max()
                                if pd.notna(max_group_time_minutes):
                                    calculated_z_agg = math.floor(max_group_time_minutes * 2) / 2.0
                                    max_z_minutes = max(calculated_z_agg, 6.0) # Apply 6.0 min floor
                                else: max_z_minutes = 6.0
                            else: max_z_minutes = 6.0
                        else: 
                            logging.warning(f"[DI Case Reco MSR] Missing msr_group_id or msr_group_total_time for MSR ({q_type}, {domain}). Defaulting Z to 6.0 min.")
                            max_z_minutes = 6.0
                    else: # Original logic for non-MSR types
                        target_time_minutes = target_times_minutes.get(q_type, 2.0) # Use dict lookup for non-MSR target
                        # Calculate max_z_minutes for non-MSR using single-question logic
                        z_minutes_list = []
                        for _, row in group_df.iterrows():
                            q_time_minutes = row['question_time']
                            is_overtime = row['overtime']
                            if pd.notna(q_time_minutes):
                                base_time_minutes = max(0, q_time_minutes - 0.5 if is_overtime else q_time_minutes)
                                z_raw_minutes = math.floor(base_time_minutes * 2) / 2.0
                                z = max(z_raw_minutes, target_time_minutes) # Apply non-MSR target time floor
                                z_minutes_list.append(z)
                        max_z_minutes = max(z_minutes_list) if z_minutes_list else target_time_minutes
                    
                    # Ensure max_z_minutes has a value (fallback to target time)
                    if max_z_minutes is None:
                         max_z_minutes = target_time_minutes # Use the determined target time (MSR or other)
                         logging.warning(f"[DI Case Reco] max_z_minutes calculation resulted in None for ({q_type}, {domain}). Falling back to target_time: {target_time_minutes}")
                    
                    # Ensure target_time_minutes is defined before logging/text generation
                    if target_time_minutes is None: # Fallback if somehow target_time wasn't set
                         target_time_minutes = target_times_minutes.get(q_type, 2.0) # Default lookup
                         logging.warning(f"[DI Case Reco] target_time_minutes was None for ({q_type}, {domain}) before text generation. Falling back to default: {target_time_minutes}")
                    
                    # Log the calculated values just before text generation - REMOVED by AI

                    # --- Generate Recommendation Text ---                    
                    z_text = f"{max_z_minutes:.1f} 分鐘" # Initial suggested time text
                    target_time_text = f"{target_time_minutes:.1f} 分鐘" # Final target time text
                    group_sfe = group_df['is_sfe'].any()
                    diag_params_codes = set().union(*[s for s in group_df['diagnostic_params'] if isinstance(s, list)]) # More concise set union
                    translated_params_list = _translate_di(list(diag_params_codes)) # Translate here if needed for text, else done later

                    problem_desc = "錯誤或超時"
                    sfe_prefix = "*基礎掌握不穩* " if group_sfe else ""
                    translated_domain = _translate_di(domain) # Translate domain

                    rec_text = f"{sfe_prefix}針對 **{translated_domain}** 領域的 **{q_type}** 題目 ({problem_desc})，"
                    rec_text += f"建議練習 **{y_grade}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"
                    if max_z_minutes - target_time_minutes > 2.0:
                        rec_text += " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效。**"

                    if q_type in recommendations_by_type:
                         recommendations_by_type[q_type].append({
                             'type': 'case_aggregated', 
                             'is_sfe': group_sfe, 
                             'domain': domain, 
                             'difficulty_grade': y_grade, 
                             'time_limit_z': max_z_minutes, # Starting suggested time
                             'target_time_minutes': target_time_minutes, # <-- ADDED Final target time
                             'text': rec_text, 
                             'question_type': q_type
                             })
            except Exception as e: # Catch exceptions during the loop
                 logging.error(f"Error generating case recommendation for group: ('{q_type if 'q_type' in locals() else 'unknown'}', '{domain if 'domain' in locals() else 'unknown'}'): {e}", exc_info=True) # Ensure q_type/domain exist
        else: # df_trigger is empty
            # logging.info(f"[DI Reco Logic] df_trigger is EMPTY. No incorrect or overtime questions found in df_diagnosed to generate case recommendations.") # REMOVED by AI
            pass # No action needed if trigger df is empty

    # Final Assembly
    final_recommendations = []
    # 先定義題型排序順序
    type_order_final = ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table']
    
    # Add exemption notes based on type-domain combinations
    all_type_domain_combos_in_data = set(df_diagnosed.groupby(['question_type', 'content_domain'], observed=False, dropna=False).groups.keys())
    sorted_exemptions = sorted(list(exempted_type_domain_combinations), key=lambda x: (type_order_final.index(x[0]) if x[0] in type_order_final else 99, x[1]))

    for q_type, domain in sorted_exemptions:
        if pd.isna(q_type) or pd.isna(domain): continue
        exempt_type_zh = _translate_di(q_type)
        exempt_domain_zh = _translate_di(domain)
        final_recommendations.append({
            'type': 'exemption_note',
            'text': f"**{exempt_domain_zh}** 領域的 **{exempt_type_zh}** 題目表現完美，已豁免練習建議。",
            'question_type': q_type,
            'domain': domain
        })

    for q_type in CORE_DI_QUESTION_TYPES: # Iterate through valid types found in data
        # Check if all domain combinations for this q_type are exempted
        all_domains_for_type_exempted = True
        # Get all domains present in the data for this specific q_type
        domains_for_this_q_type = df_diagnosed[df_diagnosed['question_type'] == q_type]['content_domain'].unique()
        domains_for_this_q_type = [d for d in domains_for_this_q_type if pd.notna(d)]

        if not domains_for_this_q_type: # If no domains for this type (e.g. type only had NaN domains)
             all_domains_for_type_exempted = False # Treat as not fully exempted
        else:
            for domain_for_type in domains_for_this_q_type:
                if (q_type, domain_for_type) not in exempted_type_domain_combinations:
                    all_domains_for_type_exempted = False
                    break
        
        if all_domains_for_type_exempted and q_type not in processed_override_types: # If all type+domain are exempt, and no override, skip this type's case recs
            continue
            
        type_recs = recommendations_by_type.get(q_type, [])
        if not type_recs: continue
        type_recs.sort(key=lambda rec: 0 if rec['type'] == 'macro' else 1)

        focus_note = ""
        has_math_case_agg = any(r.get('domain') == 'Math Related' for r in type_recs if r['type'] == 'case_aggregated')
        has_non_math_case_agg = any(r.get('domain') == 'Non-Math Related' for r in type_recs if r['type'] == 'case_aggregated')

        # Use pre-translated domain names
        if (domain_tags.get('poor_math_related') or domain_tags.get('slow_math_related')) and has_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{math_related_zh}` 題目的練習比例。**"
        if (domain_tags.get('poor_non_math_related') or domain_tags.get('slow_non_math_related')) and has_non_math_case_agg:
            focus_note += f" **建議增加 {q_type} 題型下 `{non_math_related_zh}` 題目的練習比例。**"

        if focus_note and type_recs:
            # Find last non-macro index safely
            last_agg_rec_index = -1
            for i in range(len(type_recs) - 1, -1, -1):
                 if type_recs[i]['type'] != 'macro': # Attach to last non-macro/exemption
                     last_agg_rec_index = i
                     break
            if last_agg_rec_index != -1:
                 type_recs[last_agg_rec_index]['text'] += focus_note
            else: # Attach to the only rec (must be macro if list not empty)
                 type_recs[-1]['text'] += focus_note


        final_recommendations.extend(type_recs)

    # 多級排序：
    # 1. SFE 聚合建議 (is_sfe=True) 優先級最高 (0)
    # 2. 宏觀建議 (type='macro') 次之 (1)
    # 3. 非SFE聚合建議 (is_sfe=False) 再次之 (2)
    # 4. 豁免說明 (type='exemption_note') 最後 (3)
    # 在相同優先級內部，再按題型順序 (type_order_final) 排序
    def sort_key(rec):
        rec_type = rec.get('type')
        is_sfe = rec.get('is_sfe', False) # 聚合建議才有 is_sfe
        q_type = rec.get('question_type', 'zzzzz') # 給予一個較後的默認排序值
        type_priority = type_order_final.index(q_type) if q_type in type_order_final else 99

        if rec_type == 'case_aggregated' and is_sfe:
            return (0, type_priority)
        elif rec_type == 'macro':
            return (1, type_priority)
        elif rec_type == 'case_aggregated' and not is_sfe:
            return (2, type_priority)
        elif rec_type == 'exemption_note':
            # 豁免說明通常按題型排在前面或特定位置，這裡也按題型排
            return (3, type_priority) 
        return (4, type_priority) # 其他類型（如果有）

    final_recommendations.sort(key=sort_key)

    return final_recommendations 
