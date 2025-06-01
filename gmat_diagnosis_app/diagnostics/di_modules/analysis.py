"""
DI診斷模組 - 分析邏輯
處理DI診斷的核心分析邏輯，原chapter_logic.py檔案
"""

import pandas as pd
import numpy as np
import math # Keep math for _check_foundation_override if it moves here later
import logging
from collections import defaultdict

# # Basic logging configuration to ensure INFO messages are displayed within this module # Removed by AI
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s') # Removed by AI

from .constants import (
    CARELESSNESS_THRESHOLD,
    TOTAL_QUESTIONS_DI, # Import TOTAL_QUESTIONS_DI
    EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES, # Import new constant
    RELATIVELY_FAST_MULTIPLIER
)
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS
from gmat_diagnosis_app.i18n import translate as t # Use unified i18n system
from .utils import grade_difficulty_di, format_rate

# Define threshold for hasty guessing
HASTY_GUESSING_THRESHOLD_MINUTES = 0.5


def diagnose_root_causes(df, avg_times, max_diffs, ch1_thresholds):
    """
    Core Chapter 3 logic: Diagnose root causes based on the provided algorithm.
    
    Args:
        df: The DataFrame with question data
        avg_times: Dictionary mapping question types to average times
        max_diffs: Dictionary with maximum difficulty values
        ch1_thresholds: Dictionary with time pressure thresholds from Chapter 1
        
    Returns:
        tuple: (diagnosed_dataframe, override_results)
    """
    # Make a copy to avoid modifying the original DataFrame
    df_diagnosed = df.copy()
    
    # Initialize diagnostic parameters column
    if 'diagnostic_params' not in df_diagnosed.columns:
        df_diagnosed['diagnostic_params'] = [[] for _ in range(len(df_diagnosed))]
    
    # Initialize is_sfe column (to be set later in the process)
    if 'is_sfe' not in df_diagnosed.columns:
        df_diagnosed['is_sfe'] = False
    
    # Initialize time_performance_category if not present
    if 'time_performance_category' not in df_diagnosed.columns:
        df_diagnosed['time_performance_category'] = t('Unknown')
    
    # Override results tracking
    override_results = {}
    
    # Group by question type for processing
    question_types = df_diagnosed['question_type'].unique()
    
    for q_type in question_types:
        if pd.isna(q_type):
            continue
            
        q_type_mask = df_diagnosed['question_type'] == q_type
        q_type_df = df_diagnosed[q_type_mask].copy()
        
        # Skip if no valid data for this question type
        if q_type_df.empty:
            continue
            
        # Process this question type
        processed_df, type_override_info = process_question_type(
            q_type_df, q_type, avg_times, max_diffs, ch1_thresholds
        )
        
        # Update the main dataframe with processed results
        df_diagnosed.loc[q_type_mask, 'diagnostic_params'] = processed_df['diagnostic_params'].values
        df_diagnosed.loc[q_type_mask, 'is_sfe'] = processed_df['is_sfe'].values
        df_diagnosed.loc[q_type_mask, 'time_performance_category'] = processed_df['time_performance_category'].values
        
        # Store override information
        if type_override_info:
            override_results[q_type] = type_override_info
    
    return df_diagnosed, override_results


def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """
    Process diagnostic logic for a specific question type.
    Implementation of DI Chapter 3 diagnostic rules.
    """
    # Make a copy to avoid modifying input data
    processed_df = q_type_df.copy()
    
    # Initialize columns if they don't exist
    if 'diagnostic_params' not in processed_df.columns:
        processed_df['diagnostic_params'] = [[] for _ in range(len(processed_df))]
    if 'is_sfe' not in processed_df.columns:
        processed_df['is_sfe'] = False
    if 'time_performance_category' not in processed_df.columns:
        processed_df['time_performance_category'] = t('Unknown')
    
    # Get average time for this question type
    avg_time = avg_times.get(q_type, 2.0)  # Default 2 minutes if not found
    
    # Initialize override tracking
    override_info = {
        'override_triggered': False,
        'Y_agg': None,
        'Z_agg': None,
        'triggering_error_rate': 0.0,
        'triggering_overtime_rate': 0.0
    }
    
    # Process each question in this type
    for idx, row in processed_df.iterrows():
        q_time = row.get('question_time', 0)
        is_correct = row.get('is_correct', True)
        is_overtime = row.get('overtime', False) 
        is_invalid = row.get('is_invalid', False)
        q_difficulty = row.get('question_difficulty', 0)
        content_domain = row.get('content_domain', 'Unknown')
        
        # Initialize diagnostic params for this row
        current_params = row.get('diagnostic_params', [])
        if not isinstance(current_params, list):
            current_params = []
        current_params = current_params.copy()  # Avoid modifying original
        
        # Calculate time performance category for ALL rows (valid and invalid)
        time_category = calculate_time_performance_category(
            q_time, is_correct, is_overtime, avg_time
        )
        processed_df.at[idx, 'time_performance_category'] = time_category
        
        # Only process diagnostic logic for VALID rows
        if not is_invalid:
            # 1. Check for Systematic Foundational Error (SFE)
            if not is_correct and pd.notna(q_difficulty):
                # Get max correct difficulty for this question type and content domain
                max_correct_diff = get_max_correct_difficulty(
                    max_diffs, q_type, content_domain
                )
                
                if pd.notna(max_correct_diff) and q_difficulty < max_correct_diff:
                    processed_df.at[idx, 'is_sfe'] = True
                    if 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE' not in current_params:
                        current_params.insert(0, 'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE')
            
            # 2. Add time-based diagnostic parameters
            if pd.notna(q_time):
                # Hasty guessing detection
                if q_time < HASTY_GUESSING_THRESHOLD_MINUTES:
                    if 'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK' not in current_params:
                        current_params.append('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
                
                # Add specific diagnostic parameters based on time category and question type
                time_specific_params = get_time_specific_parameters(
                    q_type, time_category, content_domain, is_correct, is_overtime
                )
                
                for param in time_specific_params:
                    if param not in current_params:
                        current_params.append(param)
            
            # 3. Add difficulty-based parameters
            if pd.notna(q_difficulty):
                difficulty_params = get_difficulty_specific_parameters(
                    q_type, q_difficulty, is_correct, content_domain
                )
                
                for param in difficulty_params:
                    if param not in current_params:
                        current_params.append(param)
        
        else:
            # For invalid rows, ensure they have the invalid tag
            invalid_tag = t('di_invalid_data_tag')
            if invalid_tag not in current_params:
                current_params = [invalid_tag]
        
        # Update diagnostic params for this row
        processed_df.at[idx, 'diagnostic_params'] = current_params
    
    # Calculate override conditions for this question type
    override_info = calculate_override_conditions(processed_df, q_type)
    
    return processed_df, override_info


def calculate_time_performance_category(q_time, is_correct, is_overtime, avg_time):
    """Calculate time performance category based on time, correctness, and overtime status."""
    
    # Determine if relatively fast
    is_relatively_fast = False
    if pd.notna(q_time) and pd.notna(avg_time) and avg_time > 0:
        is_relatively_fast = q_time < (avg_time * RELATIVELY_FAST_MULTIPLIER)
    
    # Assign time performance category
    if is_correct:
        if is_relatively_fast:
            return 'Fast & Correct'
        elif is_overtime:
            return 'Slow & Correct'
        else:
            return 'Normal Time & Correct'
    else:  # Incorrect
        if is_relatively_fast:
            return 'Fast & Wrong'
        elif is_overtime:
            return 'Slow & Wrong'
        else:
            return 'Normal Time & Wrong'


def get_max_correct_difficulty(max_diffs, q_type, content_domain):
    """Get maximum correct difficulty for SFE detection."""
    if isinstance(max_diffs, dict):
        # Try to get from the max_diffs dictionary
        if q_type in max_diffs and content_domain in max_diffs[q_type]:
            return max_diffs[q_type][content_domain]
        elif q_type in max_diffs:
            # If specific domain not found, use any available domain for this question type
            domain_diffs = max_diffs[q_type]
            if isinstance(domain_diffs, dict) and domain_diffs:
                return max(domain_diffs.values())
    return -np.inf  # Default if not found


def get_time_specific_parameters(q_type, time_category, content_domain, is_correct, is_overtime):
    """Get diagnostic parameters based on time performance."""
    params = []
    
    # Map question type to standardized names
    q_type_map = {
        'Data Sufficiency': 'DS',
        'Two-part analysis': 'TPA', 
        'Graph and Table': 'GT',
        'Multi-source reasoning': 'MSR'
    }
    
    std_q_type = q_type_map.get(q_type, q_type)
    
    # Add time-specific parameters based on performance category
    if time_category in ['Fast & Wrong', 'Normal Time & Wrong']:
        # Error-related parameters
        if content_domain in ['Math Related', 'Math related']:
            params.extend([
                'DI_CONCEPT_APPLICATION_ERROR__MATH',
                'DI_CALCULATION_ERROR__MATH'
            ])
        else:
            params.extend([
                'DI_LOGICAL_REASONING_ERROR__NON_MATH',
                'DI_READING_COMPREHENSION_ERROR__LOGIC'
            ])
        
        # Add question type specific error parameters
        if std_q_type in ['TPA', 'GT']:
            params.append('DI_GRAPH_INTERPRETATION_ERROR__TABLE')
        elif std_q_type == 'MSR':
            params.append('DI_MULTI_SOURCE_INTEGRATION_ERROR')
    
    elif time_category in ['Slow & Wrong', 'Slow & Correct']:
        # Difficulty/efficiency parameters
        if content_domain in ['Math Related', 'Math related']:
            params.extend([
                'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH',
                'DI_CALCULATION_DIFFICULTY__MATH'
            ])
        else:
            params.extend([
                'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH',
                'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC'
            ])
        
        # Add efficiency bottleneck parameters
        if std_q_type == 'DS':
            params.append('DI_EFFICIENCY_BOTTLENECK_LOGIC')
        elif std_q_type in ['TPA', 'GT']:
            params.append('DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE')
        elif std_q_type == 'MSR':
            params.append('DI_EFFICIENCY_BOTTLENECK_INTEGRATION')
    
    return params


def get_difficulty_specific_parameters(q_type, q_difficulty, is_correct, content_domain):
    """Get diagnostic parameters based on question difficulty."""
    params = []
    
    # Only add difficulty parameters for incorrect answers
    if not is_correct and pd.notna(q_difficulty):
        difficulty_level = grade_difficulty_di(q_difficulty)
        
        # Add difficulty-specific parameters based on content domain
        if content_domain in ['Math Related', 'Math related']:
            if q_difficulty <= 0:  # Low to mid difficulty
                params.append('DI_CALCULATION_ERROR__MATH')
            else:  # Higher difficulty
                params.append('DI_CONCEPT_APPLICATION_ERROR__MATH')
        else:
            if q_difficulty <= 0:  # Low to mid difficulty
                params.append('DI_READING_COMPREHENSION_ERROR__DOMAIN')
            else:  # Higher difficulty
                params.append('DI_LOGICAL_REASONING_ERROR__NON_MATH')
    
    return params


def calculate_override_conditions(processed_df, q_type):
    """Calculate override conditions for macro recommendations."""
    override_info = {
        'override_triggered': False,
        'Y_agg': None,
        'Z_agg': None,
        'triggering_error_rate': 0.0,
        'triggering_overtime_rate': 0.0
    }
    
    # Filter to valid questions only
    valid_df = processed_df[~processed_df.get('is_invalid', False)]
    
    if valid_df.empty:
        return override_info
    
    # Calculate performance metrics
    total_valid = len(valid_df)
    errors = (valid_df['is_correct'] == False).sum()
    overtime_count = valid_df['overtime'].sum()
    
    error_rate = errors / total_valid if total_valid > 0 else 0.0
    overtime_rate = overtime_count / total_valid if total_valid > 0 else 0.0
    
    # Check override thresholds
    error_threshold = 0.4  # 40%
    overtime_threshold = 0.3  # 30%
    
    if error_rate >= error_threshold or overtime_rate >= overtime_threshold:
        override_info['override_triggered'] = True
        override_info['triggering_error_rate'] = error_rate
        override_info['triggering_overtime_rate'] = overtime_rate
        
        # Set difficulty grade for recommendations
        if 'question_difficulty' in valid_df.columns:
            min_difficulty = valid_df['question_difficulty'].min()
            if pd.notna(min_difficulty):
                override_info['Y_agg'] = grade_difficulty_di(min_difficulty)
            else:
                override_info['Y_agg'] = t('low_difficulty')
        else:
            override_info['Y_agg'] = t('low_difficulty')
        
        # Set time recommendation
        if 'question_time' in valid_df.columns:
            avg_time = valid_df['question_time'].mean()
            if pd.notna(avg_time):
                # Subtract 0.5 minutes for practice recommendation
                base_time = max(0, avg_time - 0.5)
                override_info['Z_agg'] = math.floor(base_time * 2) / 2.0
                
                # Apply minimum time limits by question type
                type_minimums = {
                    'Data Sufficiency': 1.5,
                    'Two-part analysis': 2.5, 
                    'Graph and Table': 2.5,
                    'Multi-source reasoning': 6.0
                }
                min_time = type_minimums.get(q_type, 1.5)
                override_info['Z_agg'] = max(override_info['Z_agg'], min_time)
            else:
                override_info['Z_agg'] = 2.0
        else:
            override_info['Z_agg'] = 2.0
    
    return override_info


def observe_di_patterns(df, avg_times):
    """
    Chapter 4 logic: Observe behavioral patterns in DI data.
    
    Args:
        df: The diagnosed DataFrame
        avg_times: Dictionary mapping question types to average times
        
    Returns:
        dict: Dictionary containing behavioral pattern analysis results
    """
    patterns = {
        'carelessness_issue_triggered': False,
        'early_rushing_risk_triggered': False,
        'fast_wrong_rate': 0.0,
        'early_rushing_questions': [],
        'triggered_behavioral_params': []
    }
    
    # Filter for valid questions only
    valid_df = df[~df.get('is_invalid', False)].copy()
    
    if valid_df.empty:
        return patterns
    
    # Carelessness detection
    fast_wrong_mask = (valid_df['is_correct'] == False) & (valid_df['overtime'] == False)
    fast_wrong_count = fast_wrong_mask.sum()
    total_valid = len(valid_df)
    
    if total_valid > 0:
        fast_wrong_rate = fast_wrong_count / total_valid
        patterns['fast_wrong_rate'] = fast_wrong_rate
        
        # Trigger carelessness if fast-wrong rate exceeds threshold
        if fast_wrong_rate >= 0.3:  # 30% threshold
            patterns['carelessness_issue_triggered'] = True
            patterns['triggered_behavioral_params'].append('DI_BEHAVIOR_CARELESSNESS_ISSUE')
    
    # Early rushing detection
    rushing_questions = []
    for idx, row in valid_df.iterrows():
        q_type = row.get('question_type')
        q_time = row.get('question_time', 0)
        avg_time = avg_times.get(q_type, 2.0)
        
        # Consider rushing if time < 50% of average time
        if q_time < avg_time * 0.5:
            rushing_questions.append(idx)
    
    if len(rushing_questions) >= 2:  # At least 2 rushing instances
        patterns['early_rushing_risk_triggered'] = True
        patterns['early_rushing_questions'] = rushing_questions
        patterns['triggered_behavioral_params'].append('DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK')
    
    return patterns


def check_foundation_override(df, type_metrics):
    """
    Chapter 5 logic: Check for foundation override conditions.
    
    Args:
        df: The diagnosed DataFrame
        type_metrics: Dictionary containing metrics by question type
        
    Returns:
        dict: Dictionary containing override decisions and SFE flags
    """
    override_decisions = {}
    
    # Calculate SFE (Systematic Foundational Error) flags
    df_copy = df.copy()
    df_copy['is_sfe'] = False
    
    # Group by question type and analyze
    for q_type in df['question_type'].unique():
        if pd.isna(q_type):
            continue
            
        q_type_mask = df['question_type'] == q_type
        q_type_df = df[q_type_mask]
        
        if q_type_df.empty:
            continue
        
        # Calculate error and overtime rates
        valid_mask = ~q_type_df.get('is_invalid', False)
        valid_df = q_type_df[valid_mask]
        
        if len(valid_df) == 0:
            continue
            
        error_rate = (valid_df['is_correct'] == False).mean()
        overtime_rate = valid_df['overtime'].mean()
        
        # Override threshold logic (simplified)
        override_threshold_error = 0.4  # 40%
        override_threshold_overtime = 0.3  # 30%
        
        override_triggered = (error_rate >= override_threshold_error or 
                            overtime_rate >= override_threshold_overtime)
        
        if override_triggered:
            # Mark questions as SFE if they meet certain criteria
            low_difficulty_mask = valid_df.get('question_difficulty', 0) <= 0
            error_mask = valid_df['is_correct'] == False
            sfe_mask = low_difficulty_mask & error_mask
            
            if sfe_mask.any():
                df_copy.loc[q_type_mask & valid_mask, 'is_sfe'] = sfe_mask
        
        override_decisions[q_type] = {
            'override_triggered': override_triggered,
            'error_rate': error_rate,
            'overtime_rate': overtime_rate
        }
    
    return override_decisions, df_copy


def check_foundation_override_detailed(df, type_metrics):
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
                y_agg = grade_difficulty_di(min_diff)
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
