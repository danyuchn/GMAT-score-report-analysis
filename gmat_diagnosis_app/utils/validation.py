"""
Data validation module
Provides data validation and processing functionality
"""

import re
import pandas as pd
from gmat_diagnosis_app.constants.validation_rules import (
    VALIDATION_RULES
)
from gmat_diagnosis_app.constants.config import REQUIRED_ORIGINAL_COLS
from thefuzz import process, fuzz # Changed from fuzzywuzzy to thefuzz
from gmat_diagnosis_app.i18n import translate as t

def preprocess_skill(skill):
    """Lowercase, strip, collapse spaces for skill matching."""
    return re.sub(r'\s+', ' ', str(skill).strip()).lower()

def validate_dataframe(df, subject):
    """Validates the DataFrame rows based on predefined rules for the subject."""
    errors = []
    warnings = []
    required_original = REQUIRED_ORIGINAL_COLS.get(subject, [])

    # Determine actual required columns considering potential BOM in 'Question'
    question_col_in_df = '\ufeffQuestion' if '\ufeffQuestion' in df.columns and 'Question' not in df.columns else 'Question'
    actual_required = [col if col != 'Question' else question_col_in_df for col in required_original]

    # 1. Check for missing required columns
    missing_cols = [col for col in actual_required if col not in df.columns]
    if 'Question' in missing_cols and question_col_in_df == '\ufeffQuestion':
        missing_cols.remove('Question') # Don't report 'Question' if BOM version is present and required

    if missing_cols:
        errors.append(t('validation_missing_required_columns').format(', '.join(missing_cols)))
        return errors, warnings # Stop if essential columns are missing

    # 2. Validate cell values row by row
    for index, row in df.iterrows():
        for original_col_name, rules in VALIDATION_RULES.items():
            # Determine the actual column name to check in the dataframe (handling BOM)
            current_col_name = original_col_name
            if original_col_name == 'Question' and question_col_in_df == '\ufeffQuestion':
                current_col_name = question_col_in_df

            if current_col_name not in df.columns:
                # Skip validation only if the column wasn't required for this subject
                if original_col_name not in required_original:
                     continue
                # If it was required but not found, the previous check caught it.

            # Proceed if column exists
            if current_col_name in df.columns:
                value = row[current_col_name]

                # Skip validation for empty/NaN cells
                if pd.isna(value) or str(value).strip() == '':
                    continue

                is_valid = True
                error_detail = rules['error']
                correct_value = None # To store potential auto-corrected value

                # --- Type Checks ---
                if 'type' in rules:
                    value_str = str(value).strip()
                    if rules['type'] == 'positive_float':
                        try:
                            num = float(value_str)
                            if num <= 0: is_valid = False
                        except (ValueError, TypeError): is_valid = False
                    elif rules['type'] == 'positive_integer':
                        try:
                            num_float = float(value_str)
                            if not (num_float > 0 and num_float == int(num_float)):
                                is_valid = False
                        except (ValueError, TypeError): is_valid = False
                    elif rules['type'] == 'number':
                        try: float(value_str)
                        except (ValueError, TypeError): is_valid = False

                # --- Allowed List Checks (with auto-correction) ---
                elif 'allowed' in rules:
                    allowed_values_list = rules['allowed']
                    # Use subject-specific list if available
                    if 'subject_specific' in rules and subject in rules['subject_specific']:
                        allowed_values_list = rules['subject_specific'][subject]

                    value_str_stripped = str(value).strip()
                    value_str_lower = value_str_stripped.lower()

                    # Specific Logic for Q: Question Type ('real contexts'/'pure contexts')
                    if original_col_name == 'Question Type' and subject == 'Q':
                        if value_str_lower == 'real contexts': correct_value = 'REAL'; is_valid = True
                        elif value_str_lower == 'pure contexts': correct_value = 'PURE'; is_valid = True
                        else: # Fallback to general check for 'REAL', 'PURE'
                            allowed_map = {str(v).lower(): v for v in allowed_values_list}
                            if value_str_lower in allowed_map:
                                correct_value = allowed_map[value_str_lower]
                                is_valid = True
                            else:
                                # Fuzzy match for Q's Question Type if exact fails
                                match, score = process.extractOne(value_str_stripped, allowed_values_list, scorer=fuzz.ratio) if allowed_values_list else (None, 0)
                                if score >= 85: # Fuzzy match threshold
                                    correct_value = match
                                    is_valid = True
                                    warnings.append(t('validation_fuzzy_match_correction').format(index + 1, current_col_name, value_str_stripped, correct_value))
                                else:
                                    is_valid = False

                    # Specific Logic for Fundamental Skills (Preprocessing + Exact Match, then Fuzzy)
                    elif original_col_name == 'Fundamental Skills':
                        processed_input = preprocess_skill(value_str_stripped)
                        is_valid = False # Assume invalid initially
                        skill_map = {}
                        # Prepare a list of preprocessed allowed skills for fuzzy matching
                        preprocessed_allowed_skills_for_fuzzy = []

                        for allowed_val in allowed_values_list:
                            processed_allowed = preprocess_skill(allowed_val)
                            # Canonical mapping for Rates/Ratio/Percent(s)
                            canonical_value = 'Rates/Ratio/Percent' if processed_allowed == 'rates/ratios/percent' else allowed_val
                            skill_map[processed_allowed] = canonical_value
                            preprocessed_allowed_skills_for_fuzzy.append(processed_allowed) # Store preprocessed version for fuzzy

                        if processed_input in skill_map:
                            correct_value = skill_map[processed_input]
                            is_valid = True
                        else:
                            # Fuzzy match against preprocessed allowed skills
                            # We use the original allowed_values_list to extract the *original* casing if a match is found
                            # The `process.extractOne` needs the original list to return the correctly cased value.
                            # We find the best match based on the preprocessed input against preprocessed allowed values.
                            
                            # To get the original cased value from a fuzzy match on preprocessed strings:
                            # 1. Fuzzy match `processed_input` against `preprocessed_allowed_skills_for_fuzzy`.
                            # 2. If a match is found, get the index of the matched preprocessed skill.
                            # 3. Use this index to get the original cased skill from `allowed_values_list`.
                            # OR, simpler: fuzzy match `value_str_stripped` (original input) directly against `allowed_values_list` (original allowed values)
                            
                            match, score = process.extractOne(value_str_stripped, allowed_values_list, scorer=fuzz.WRatio) if allowed_values_list else (None, 0)
                            if score >= 85: # Fuzzy match threshold (using WRatio for better results with mixed case/punctuation)
                                # Check if the matched value, after preprocessing, is a known skill
                                preprocessed_match = preprocess_skill(match)
                                if preprocessed_match in skill_map: # Ensure the fuzzy matched skill is valid after preprocessing
                                    correct_value = skill_map[preprocessed_match] # Use the canonical form
                                    is_valid = True
                                    warnings.append(t('validation_fuzzy_match_correction').format(index + 1, current_col_name, value_str_stripped, correct_value))
                                else:
                                    # This case is unlikely if skill_map is comprehensive but good for safety
                                    is_valid = False
                            else:
                                is_valid = False
                    
                    # Default Case-Insensitive Check (Handles 'Graphs and Tables' -> 'Graph and Table')
                    # And Fuzzy matching for Content Domain and general Question Types (non-Q)
                    else:
                        allowed_map = {}
                        # Special handling for 'Graphs and Tables' -> 'Graph and Table' for DI Question Type
                        # This canonical mapping should ideally be in validation_rules.py or handled more generically
                        for v in allowed_values_list:
                            key = str(v).lower()
                            canonical_value = v
                            if original_col_name == 'Question Type' and subject == 'DI' and key == 'graphs and tables':
                                canonical_value = 'Graph and Table' # Specific canonical mapping
                            allowed_map[key] = canonical_value
                        
                        if value_str_lower in allowed_map:
                            correct_value = allowed_map[value_str_lower]
                            is_valid = True
                        else:
                            # Fuzzy match for 'Content Domain' and other 'Question Type'
                            if original_col_name in ['Content Domain', 'Question Type']:
                                match, score = process.extractOne(value_str_stripped, allowed_values_list, scorer=fuzz.ratio) if allowed_values_list else (None, 0)
                                if score >= 85: # Fuzzy match threshold
                                    # If it was 'Graphs and Tables' and matched to 'Graph and Table', ensure canonical
                                    if original_col_name == 'Question Type' and subject == 'DI' and str(match).lower() == 'graph and table':
                                        correct_value = 'Graph and Table'
                                    else:
                                        correct_value = match
                                    is_valid = True
                                    warnings.append(t('validation_fuzzy_match_correction').format(index + 1, current_col_name, value_str_stripped, correct_value))
                                else:
                                    is_valid = False
                            else:
                                is_valid = False # Not one of the fuzzy matched fields, and no exact match

                    # --- Auto-Correction Application ---
                    if is_valid and correct_value is not None and value_str_stripped != correct_value:
                        try:
                            # Use .loc for safe assignment BACK into the original DataFrame
                            df.loc[index, current_col_name] = correct_value
                            # st.toast(f"Row {index+1}, Col '{current_col_name}': Auto-corrected '{value_str_stripped}' to '{correct_value}'") # Optional user feedback
                        except Exception as e:
                            errors.append(t('validation_auto_correction_error').format(index + 1, current_col_name, e))
                            is_valid = False # Mark invalid if correction fails

                    elif not is_valid:
                        # Improve error message for list failures
                        allowed_str = ", ".join(f"'{v}'" for v in allowed_values_list)
                        error_detail += t('validation_allowed_values_error').format(allowed_str)

                # --- Record Error ---
                if not is_valid:
                    errors.append(t('validation_invalid_value_error').format(index + 1, current_col_name, value, error_detail))

    return errors, warnings 