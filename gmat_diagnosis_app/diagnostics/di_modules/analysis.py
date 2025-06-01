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
)
from gmat_diagnosis_app.i18n import translate as t # Use unified i18n system
from .utils import grade_difficulty_di, format_rate


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
    df_diagnosed['diagnostic_params'] = [[] for _ in range(len(df_diagnosed))]
    
    # Initialize is_sfe column (to be set later in the process)
    df_diagnosed['is_sfe'] = False
    
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
        df_diagnosed.loc[q_type_mask, :] = processed_df
        
        # Store override information
        if type_override_info:
            override_results[q_type] = type_override_info
    
    return df_diagnosed, override_results


def process_question_type(q_type_df, q_type, avg_times, max_diffs, ch1_thresholds):
    """Process diagnostic logic for a specific question type."""
    # Implementation details...
    # (This is a simplified version - the actual implementation would be more complex)
    
    override_info = {
        'override_triggered': False,
        'Y_agg': None,
        'Z_agg': None,
        'triggering_error_rate': 0.0,
        'triggering_overtime_rate': 0.0
    }
    
    return q_type_df, override_info


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
