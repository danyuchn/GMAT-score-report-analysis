"""
驗證模組
提供數據驗證和處理的功能
"""

import re
import pandas as pd
from gmat_diagnosis_app.constants.validation_rules import (
    VALIDATION_RULES,
    ALL_CONTENT_DOMAINS,
    ALL_QUESTION_TYPES,
    ALL_FUNDAMENTAL_SKILLS
)
from gmat_diagnosis_app.constants.config import REQUIRED_ORIGINAL_COLS

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
        errors.append(f"資料缺少必要欄位: {', '.join(missing_cols)}。請檢查欄位標頭。")
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
                            else: is_valid = False

                    # Specific Logic for Fundamental Skills (Fuzzy Match + Canonical Mapping)
                    elif original_col_name == 'Fundamental Skills':
                        processed_input = preprocess_skill(value_str_stripped)
                        is_valid = False # Assume invalid initially
                        skill_map = {}
                        for allowed_val in allowed_values_list:
                            processed_allowed = preprocess_skill(allowed_val)
                            # Canonical mapping for Rates/Ratio/Percent(s)
                            canonical_value = 'Rates/Ratio/Percent' if processed_allowed == 'rates/ratios/percent' else allowed_val
                            skill_map[processed_allowed] = canonical_value
                        if processed_input in skill_map:
                            correct_value = skill_map[processed_input]
                            is_valid = True

                    # Default Case-Insensitive Check (Handles 'Graphs and Tables' -> 'Graph and Table')
                    else:
                        allowed_map = {}
                        for v in allowed_values_list:
                            key = str(v).lower()
                            canonical_value = 'Graph and Table' if key == 'graphs and tables' else v
                            allowed_map[key] = canonical_value
                        if value_str_lower in allowed_map:
                            correct_value = allowed_map[value_str_lower]
                            is_valid = True
                        else: is_valid = False

                    # --- Auto-Correction Application ---
                    if is_valid and correct_value is not None and value_str_stripped != correct_value:
                        try:
                            # Use .loc for safe assignment BACK into the original DataFrame
                            df.loc[index, current_col_name] = correct_value
                            # st.toast(f"Row {index+1}, Col '{current_col_name}': Auto-corrected '{value_str_stripped}' to '{correct_value}'") # Optional user feedback
                        except Exception as e:
                            errors.append(f"第 {index + 1} 行, 欄位 '{current_col_name}': 自動修正時出錯 ({e})。")
                            is_valid = False # Mark invalid if correction fails

                    elif not is_valid:
                        # Improve error message for list failures
                        allowed_str = ", ".join(f"'{v}'" for v in allowed_values_list)
                        error_detail += f" 允許的值: {allowed_str} (大小寫/格式可能不符)。"

                # --- Record Error ---
                if not is_valid:
                    errors.append(f"第 {index + 1} 行, 欄位 '{current_col_name}': 值 '{value}' 無效。{error_detail}")

    return errors, warnings 