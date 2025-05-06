import pandas as pd
import numpy as np
import math
import warnings # Use warnings module instead of print
# import re # No longer needed here if parse_adjusted_qns is moved

from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Import from new location
# from gmat_diagnosis_app.utils.parsing_utils import parse_adjusted_qns # Will be imported where needed

# --- Centralized Thresholds and Constants ---
# THRESHOLDS moved to constants/thresholds.py

# --- Helper function for parsing adjusted question numbers ---
# parse_adjusted_qns moved to utils/parsing_utils.py

# --- Invalid Question Suggestion ---
# _suggest_invalid_last_third and suggest_invalid_questions moved to data_validation/invalid_suggestion.py

# --- Overtime Calculation ---
# _calculate_overtime_q, _calculate_overtime_di, _calculate_overtime_v, and calculate_overtime
# moved to analysis_helpers/time_analyzer.py

# --- Verbal Data Preprocessing ---
# preprocess_verbal_data, _identify_rc_groups, _calculate_rc_times
# moved to subject_preprocessing/verbal_preprocessor.py

# --- DI Data Preprocessing ---
# preprocess_di_data and _identify_msr_groups
# moved to subject_preprocessing/di_preprocessor.py

# Any remaining small helper functions specific to preprocess_helpers can stay here,
# or this file can become a facade that imports and re-exports from the new modules
# if app.py or other places rely on preprocess_helpers.specific_function() calls.

# For example, if app.py -> setup_input_tabs() -> preprocess_helpers.do_everything():
# This file might look like:
# from .data_validation.invalid_suggestion import suggest_invalid_questions
# from .analysis_helpers.time_analyzer import calculate_overtime
# from .subject_preprocessing.verbal_preprocessor import preprocess_verbal_data
# from .subject_preprocessing.di_preprocessor import preprocess_di_data
# etc.

# If setup_input_tabs directly calls these specific preprocessors, then preprocess_helpers.py
# might become very lean or even be refactored out.
# Current app.py passes the preprocess_helpers *module* to setup_input_tabs.
# So, preprocess_helpers.py should re-export them.

from gmat_diagnosis_app.data_validation.invalid_suggestion import suggest_invalid_questions
from gmat_diagnosis_app.analysis_helpers.time_analyzer import calculate_overtime
from gmat_diagnosis_app.subject_preprocessing.verbal_preprocessor import preprocess_verbal_data
from gmat_diagnosis_app.subject_preprocessing.di_preprocessor import preprocess_di_data
from gmat_diagnosis_app.utils.parsing_utils import parse_adjusted_qns

# THRESHOLDS is also used by analysis_orchestrator, so it's imported there from constants.thresholds
# parse_adjusted_qns is also used by analysis_orchestrator, so it's imported there from utils.parsing_utils

# It seems like the main functions that app.py (via setup_input_tabs) or analysis_orchestrator.py
# were calling from preprocess_helpers are now moved. 
# The `app.py` passes `preprocess_helpers` module to `setup_input_tabs`.
# `setup_input_tabs` then might be calling `preprocess_helpers.suggest_invalid_questions(...)` etc.
# So, this file (preprocess_helpers.py) should re-export them.

__all__ = [
    'suggest_invalid_questions',
    'calculate_overtime',
    'preprocess_verbal_data',
    'preprocess_di_data',
    'parse_adjusted_qns',
    'THRESHOLDS' # Also re-export THRESHOLDS if setup_input_tabs needs it from here
]