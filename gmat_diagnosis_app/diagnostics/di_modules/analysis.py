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
)
from gmat_diagnosis_app.i18n import translate as t # Use unified i18n system
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
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤及閱讀理解錯誤細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
                elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
            
            # B. Two-Part Analysis
            elif q_type == 'Two-part analysis':
                 if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
                 elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
            
            # C. Graph & Table
            elif q_type == 'Graph and Table':
                 if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
                 elif q_domain == 'Non-Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif is_slow and is_correct: 
                        # 添加所有相關困難標籤
                        params.extend(['DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC', 'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN',
                                     'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有非數學相關錯誤標籤、圖表解讀錯誤和閱讀理解細分標籤
                        params.extend(['DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
            
            # D. Multi-Source Reasoning
            elif q_type == 'Multi-source reasoning':
                msr_passage_overtime = False # Initialize msr_passage_overtime flag
                if pd.notna(msr_reading_time) and msr_reading_time > msr_reading_threshold: # msr_reading_threshold is defined earlier
                    msr_passage_overtime = True

                if q_domain == 'Math Related':
                    if is_slow and not is_correct: 
                        # 添加所有數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加相關困難標籤 (MSR特定標籤除外，稍後根據msr_passage_overtime添加)
                        difficulty_tags_to_add = [
                            'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                            'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                            'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC',
                            'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                            'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED']
                        params.extend(difficulty_tags_to_add)
                        if msr_passage_overtime:
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION')
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN')

                    elif is_slow and is_correct: 
                        # 添加相關困難標籤 (MSR特定標籤除外，稍後根據msr_passage_overtime添加)
                        difficulty_tags_to_add = [
                            'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                            'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                            'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC',
                            'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH', 'DI_CALCULATION_DIFFICULTY__MATH',
                            'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED']
                        params.extend(difficulty_tags_to_add)
                        if msr_passage_overtime:
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION')
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN')

                    elif (is_normal_time or is_relatively_fast) and not is_correct:
                        # 添加所有數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_CONCEPT_APPLICATION_ERROR__MATH', 'DI_CALCULATION_ERROR__MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
                elif q_domain == 'Non-Math Related':
                     if is_slow and not is_correct: 
                        # 添加所有非數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                        params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                     'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                     'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                     'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                     'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                        # 添加相關困難標籤 (MSR特定標籤除外，稍後根據msr_passage_overtime添加)
                        difficulty_tags_to_add = [
                            'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                            'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                            'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC',
                            'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                            'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED']
                        params.extend(difficulty_tags_to_add)
                        if msr_passage_overtime:
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION')
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN')

                     elif is_slow and is_correct: 
                        # 添加相關困難標籤 (MSR特定標籤除外，稍後根據msr_passage_overtime添加)
                        difficulty_tags_to_add = [
                            'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH', 'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE',
                            'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY', 'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX',
                            'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC',
                            'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                            'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED']
                        params.extend(difficulty_tags_to_add)
                        if msr_passage_overtime:
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION')
                            params.append('DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN')

                     elif (is_normal_time or is_relatively_fast) and not is_correct:
                         # 添加所有非數學相關錯誤標籤、多源整合錯誤和閱讀理解細分標籤
                         params.extend(['DI_MULTI_SOURCE_INTEGRATION_ERROR', 'DI_LOGICAL_REASONING_ERROR__NON_MATH',
                                      'DI_GRAPH_INTERPRETATION_ERROR__GRAPH', 'DI_GRAPH_INTERPRETATION_ERROR__TABLE',
                                      'DI_READING_COMPREHENSION_ERROR__VOCABULARY', 'DI_READING_COMPREHENSION_ERROR__SYNTAX',
                                      'DI_READING_COMPREHENSION_ERROR__LOGIC', 'DI_READING_COMPREHENSION_ERROR__DOMAIN',
                                      'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED'])
                         if is_relatively_fast: params.append('DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION')
        # --- End Detailed Logic ---
        else: # This row IS invalid
            sfe_triggered = False # Invalid rows are not SFE by this logic
            # params list should be empty or contain only invalid tag
            # The invalid tag is usually added in main.py to the original 'diagnostic_params' column.
            # Here, we ensure that if this function is solely responsible for 'params', it reflects invalidity.
            existing_row_params = row.get('diagnostic_params', [])
            if isinstance(existing_row_params, list) and t('di_invalid_data_tag') in existing_row_params:
                params = [t('di_invalid_data_tag')]
            elif not params: # If no SFE was added (because it's invalid), and params is empty
                params = [t('di_invalid_data_tag')]
            # current_time_performance_category is already calculated for all rows and will be used.

        # Ensure invalid tag is handled correctly if added by main.py
        # and merge with params calculated here (which are empty if invalid_row is true and no SFE)
        original_input_row_params = row.get('diagnostic_params', [])
        if not isinstance(original_input_row_params, list): original_input_row_params = []

        final_params_for_row = []
        if is_invalid_row:
            # For invalid rows, the params list should primarily be [invalid_tag].
            # If main.py already put it in original_input_row_params, use that.
            if t('di_invalid_data_tag') in original_input_row_params:
                final_params_for_row = [p for p in original_input_row_params if p == t('di_invalid_data_tag')] # Keep only this tag if others exist
                if not final_params_for_row: final_params_for_row = [t('di_invalid_data_tag')] # Ensure it's there
            else:
                final_params_for_row = [t('di_invalid_data_tag')]
            # sfe_triggered is already False for invalid rows at this point if it came from this function's logic
        else: # Valid row
            # Combine any params from earlier steps (e.g. behavioral from main) with SFE/detailed from here
            temp_combined = original_input_row_params + params
            final_params_for_row = list(dict.fromkeys(temp_combined)) # Remove duplicates
            # Ensure new SFE tag is handled correctly
            if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE' in final_params_for_row:
                final_params_for_row.remove('DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
                final_params_for_row.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
            elif sfe_triggered:  # If SFE isn't in the list but should be
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
            analysis['triggered_behavioral_params'].append('DI_BEHAVIOR_CARELESSNESS_ISSUE')
            # Mark these questions in diagnostic_params
            if 'time_performance_category' in df.columns:
                for idx, row in df[df['time_performance_category'] == 'Fast & Wrong'].iterrows():
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION']
            else:
                for idx in df.index[fast_wrong_mask]:
                    if 'diagnostic_params' in df.columns:
                        df.at[idx, 'diagnostic_params'] = list(df.at[idx, 'diagnostic_params']) + ['DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION']

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
    """
    Chapter 5: Special Foundation Check Based on Questions Answered
    Override recommendations based on types with low question count and suboptimal performance.
    
    UPDATED: Enhanced triggering logic to catch more subtle underperformance patterns.
    """
    override_results = {}
    
    for q_type in type_metrics:
        metrics = type_metrics[q_type]
        if metrics.empty:
            override_results[q_type] = {'override_triggered': False}
            continue

        x_count = metrics.get('num_questions_valid', 0)
        min_diff = metrics.get('min_difficulty', None)
        max_diff = metrics.get('max_difficulty', None)
        error_rate = metrics.get('error_rate', 0.0)
        overtime_rate = metrics.get('overtime_rate', 0.0)

        override_triggered = False
        y_agg = "未知難度"
        z_agg = None
        
        triggering_error_rate = None
        triggering_overtime_rate = None

        # Check triggering conditions with flexible thresholds
        # if x_count >= 3:
        #     if error_rate >= 0.5 or overtime_rate >= 0.5:
        #         override_triggered = True
        #         triggering_error_rate = error_rate
        #         triggering_overtime_rate = overtime_rate
        # elif x_count == 2:
        #     if error_rate >= 0.5 or overtime_rate >= 0.5:
        #         override_triggered = True
        #         triggering_error_rate = error_rate
        #         triggering_overtime_rate = overtime_rate
        # elif x_count == 1:
        #     # For single question, high threshold OR/AND specific patterns
        #     if error_rate == 1.0 and overtime_rate >= 0.0:  # Wrong AND potentially slow
        #         override_triggered = True
        #         triggering_error_rate = error_rate
        #         triggering_overtime_rate = overtime_rate

        # UPDATED flexible threshold logic, prioritizing error_rate >= 0.5 but allowing overtime-only triggers
        if x_count >= 3:
            if error_rate >= 0.5:
                override_triggered = True
                triggering_error_rate = error_rate
                triggering_overtime_rate = overtime_rate  # Always capture both for reporting
            elif overtime_rate >= 0.7:  # Higher threshold for overtime-only when sufficient data
                override_triggered = True
                triggering_error_rate = error_rate
                triggering_overtime_rate = overtime_rate
        elif x_count == 2:
            if error_rate >= 0.5:
                override_triggered = True
                triggering_error_rate = error_rate
                triggering_overtime_rate = overtime_rate
            elif overtime_rate >= 0.5:  # Moderate threshold for medium data
                override_triggered = True
                triggering_error_rate = error_rate
                triggering_overtime_rate = overtime_rate
        elif x_count == 1:
            # For single question, focus on clear failure
            if error_rate == 1.0:  # Must be wrong to trigger
                override_triggered = True
                triggering_error_rate = error_rate
                triggering_overtime_rate = overtime_rate

        if override_triggered:
            # Generate Y_agg (difficulty grade for recommendations)
            if pd.notna(min_diff):
                y_agg = _grade_difficulty_di(min_diff)
            else:
                y_agg = "低難度"  # Default fallback

            # Generate Z_agg (time recommendation based on historical performance)
            if 'avg_time' in metrics and pd.notna(metrics['avg_time']):
                base_time = max(0, metrics['avg_time'] - 0.5)  # Subtract 0.5 min for faster practice
                z_agg = math.floor(base_time * 2) / 2.0  # Round down to nearest 0.5
                # Apply type-specific minimum time limits
                type_minimums = {'Data Sufficiency': 1.5, 'Two-part analysis': 2.5, 'Graph and Table': 2.5, 'Multi-source reasoning': 6.0}
                z_agg = max(z_agg, type_minimums.get(q_type, 1.5))
            else:
                z_agg = 2.0  # Default recommendation

        override_results[q_type] = {
            'override_triggered': override_triggered,
            'Y_agg': y_agg,
            'Z_agg': z_agg,
            'triggering_error_rate': triggering_error_rate,
            'triggering_overtime_rate': triggering_overtime_rate,
            'question_count': x_count,
            'min_difficulty': min_diff,
            'max_difficulty': max_diff
        }

    return override_results 
