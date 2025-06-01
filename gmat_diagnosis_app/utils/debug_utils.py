"""
Debug utilities for GMAT Diagnosis App.

This module provides debugging tools and utilities to improve maintainability
and facilitate troubleshooting during development and production.
"""

import logging
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional, List
import traceback
import time
from functools import wraps
import json
import os
from datetime import datetime

# Configure debug logger
def setup_debug_logger(name: str = 'gmat_debug', level: int = logging.DEBUG) -> logging.Logger:
    """
    Set up a dedicated debug logger with proper formatting.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # File handler for debug logs
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        file_handler = logging.FileHandler(f'logs/debug_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# Performance monitoring decorator
def monitor_performance(logger: Optional[logging.Logger] = None):
    """
    Decorator to monitor function performance and log execution time.
    
    Args:
        logger: Optional logger instance
    """
    if logger is None:
        logger = setup_debug_logger()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            try:
                logger.debug(f"Starting execution: {func_name}")
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"Completed execution: {func_name} in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Error in {func_name} after {execution_time:.3f}s: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        return wrapper
    return decorator

# DataFrame debugging utilities
class DataFrameDebugger:
    """Utility class for debugging DataFrame operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_debug_logger()
    
    def log_dataframe_info(self, df: pd.DataFrame, name: str = "DataFrame") -> None:
        """
        Log comprehensive information about a DataFrame.
        
        Args:
            df: DataFrame to analyze
            name: Name/identifier for the DataFrame
        """
        self.logger.debug(f"=== {name} Info ===")
        self.logger.debug(f"Shape: {df.shape}")
        self.logger.debug(f"Columns: {list(df.columns)}")
        self.logger.debug(f"Index: {df.index.dtype}, {len(df.index)} entries")
        
        # Memory usage
        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        self.logger.debug(f"Memory usage: {memory_usage:.2f} MB")
        
        # Null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            self.logger.debug(f"Null values: {null_counts[null_counts > 0].to_dict()}")
        
        # Data types
        self.logger.debug(f"Data types: {df.dtypes.to_dict()}")
    
    def compare_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                          name1: str = "DF1", name2: str = "DF2") -> None:
        """
        Compare two DataFrames and log differences.
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            name1: Name for first DataFrame
            name2: Name for second DataFrame
        """
        self.logger.debug(f"=== Comparing {name1} vs {name2} ===")
        
        # Shape comparison
        if df1.shape != df2.shape:
            self.logger.warning(f"Shape mismatch: {name1} {df1.shape} vs {name2} {df2.shape}")
        
        # Column comparison
        cols1, cols2 = set(df1.columns), set(df2.columns)
        if cols1 != cols2:
            missing_in_2 = cols1 - cols2
            missing_in_1 = cols2 - cols1
            if missing_in_2:
                self.logger.warning(f"Columns in {name1} but not {name2}: {missing_in_2}")
            if missing_in_1:
                self.logger.warning(f"Columns in {name2} but not {name1}: {missing_in_1}")
        
        # Value comparison for common columns
        common_cols = cols1 & cols2
        if len(common_cols) > 0 and df1.shape[0] == df2.shape[0]:
            for col in common_cols:
                if not df1[col].equals(df2[col]):
                    diff_count = (df1[col] != df2[col]).sum()
                    self.logger.warning(f"Column '{col}' has {diff_count} different values")

# Session state debugging
class SessionStateDebugger:
    """Utility class for debugging Streamlit session state."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_debug_logger()
    
    def log_session_state(self, prefix: str = "") -> None:
        """
        Log current session state contents.
        
        Args:
            prefix: Optional prefix for log messages
        """
        if 'st' not in globals():
            self.logger.warning("Streamlit not available, cannot log session state")
            return
        
        self.logger.debug(f"{prefix}Session State Contents:")
        for key, value in st.session_state.items():
            value_type = type(value).__name__
            if isinstance(value, (str, int, float, bool)):
                self.logger.debug(f"  {key}: {value} ({value_type})")
            elif isinstance(value, (list, dict)):
                self.logger.debug(f"  {key}: {value_type} with {len(value)} items")
            elif isinstance(value, pd.DataFrame):
                self.logger.debug(f"  {key}: DataFrame {value.shape}")
            else:
                self.logger.debug(f"  {key}: {value_type}")

# Configuration debugging
class ConfigDebugger:
    """Utility class for debugging configuration and constants."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_debug_logger()
    
    def log_constants(self, module_name: str, constants_dict: Dict[str, Any]) -> None:
        """
        Log configuration constants for debugging.
        
        Args:
            module_name: Name of the module/section
            constants_dict: Dictionary of constants to log
        """
        self.logger.debug(f"=== {module_name} Constants ===")
        for key, value in constants_dict.items():
            self.logger.debug(f"  {key}: {value}")

# Error context manager
class DebugContext:
    """Context manager for debugging with automatic error handling."""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or setup_debug_logger()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.debug(f"Completed operation: {self.operation_name} in {duration:.3f}s")
        else:
            self.logger.error(f"Operation failed: {self.operation_name} after {duration:.3f}s")
            self.logger.error(f"Error: {exc_type.__name__}: {exc_val}")
            self.logger.error(f"Traceback: {''.join(traceback.format_tb(exc_tb))}")
        
        # Don't suppress exceptions
        return False

# Diagnosis debugging utilities
class DiagnosisDebugger:
    """Specialized debugging utilities for diagnosis modules."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_debug_logger()
        self.df_debugger = DataFrameDebugger(logger)
    
    def log_diagnosis_input(self, df: pd.DataFrame, subject: str, 
                           time_pressure: bool, avg_times: Optional[Dict] = None) -> None:
        """
        Log diagnosis function inputs for debugging.
        
        Args:
            df: Input DataFrame
            subject: Subject name (Q/V/DI)
            time_pressure: Time pressure status
            avg_times: Average times dictionary
        """
        self.logger.debug(f"=== {subject} Diagnosis Input ===")
        self.logger.debug(f"Time pressure: {time_pressure}")
        if avg_times:
            self.logger.debug(f"Average times: {avg_times}")
        
        self.df_debugger.log_dataframe_info(df, f"{subject} Input DataFrame")
        
        # Log key column statistics
        if 'is_correct' in df.columns:
            correct_rate = df['is_correct'].mean()
            self.logger.debug(f"Overall correct rate: {correct_rate:.3f}")
        
        if 'question_time' in df.columns:
            time_stats = df['question_time'].describe()
            self.logger.debug(f"Time statistics: {time_stats.to_dict()}")
        
        if 'is_invalid' in df.columns:
            invalid_count = df['is_invalid'].sum()
            self.logger.debug(f"Invalid questions: {invalid_count}/{len(df)}")
    
    def log_diagnosis_output(self, results: Dict, report: str, df: pd.DataFrame, subject: str) -> None:
        """
        Log diagnosis function outputs for debugging.
        
        Args:
            results: Diagnosis results dictionary
            report: Generated report text
            df: Output DataFrame
            subject: Subject name
        """
        self.logger.debug(f"=== {subject} Diagnosis Output ===")
        self.logger.debug(f"Results keys: {list(results.keys())}")
        self.logger.debug(f"Report length: {len(report)} characters")
        
        self.df_debugger.log_dataframe_info(df, f"{subject} Output DataFrame")
        
        # Log key results
        if 'invalid_count' in results:
            self.logger.debug(f"Invalid count: {results['invalid_count']}")

# Global debug configuration
DEBUG_MODE = os.getenv('GMAT_DEBUG_MODE', 'False').lower() == 'true'
DEBUG_LEVEL = getattr(logging, os.getenv('GMAT_DEBUG_LEVEL', 'DEBUG').upper())

# Initialize global debug logger
debug_logger = setup_debug_logger('gmat_global_debug', DEBUG_LEVEL)

# Convenience functions
def debug_log(message: str, level: int = logging.DEBUG) -> None:
    """Quick debug logging function."""
    debug_logger.log(level, message)

def debug_dataframe(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """Quick DataFrame debugging function."""
    if DEBUG_MODE:
        debugger = DataFrameDebugger(debug_logger)
        debugger.log_dataframe_info(df, name)

def debug_session_state(prefix: str = "") -> None:
    """Quick session state debugging function."""
    if DEBUG_MODE:
        debugger = SessionStateDebugger(debug_logger)
        debugger.log_session_state(prefix) 