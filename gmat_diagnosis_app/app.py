import sys
import os
import re # Import regex module

# Get the directory containing app.py
app_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(app_dir)

# Add the project root to the beginning of sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
from io import StringIO # Use io.StringIO directly
from gmat_diagnosis_app import irt_module as irt # Import using absolute path
from gmat_diagnosis_app.diagnosis_module import run_diagnosis # Import using absolute path
import os # For environment variables
import openai # Import OpenAI library

# --- Validation Rules and Messages ---
# Based on provided testset CSVs, case and space sensitive

ALLOWED_PERFORMANCE = ['Correct', 'Incorrect']
ALLOWED_CONTENT_DOMAIN = {
    'Q': ['Algebra', 'Arithmetic'],
    'V': ['N/A'], # Assuming only N/A based on v.csv example
    'DI': ['Math Related', 'Non-Math Related']
}
# Combine all possible domains for easier checking if needed, or use subject-specific
ALL_CONTENT_DOMAINS = list(set(cd for subj_cds in ALLOWED_CONTENT_DOMAIN.values() for cd in subj_cds))

ALLOWED_QUESTION_TYPE = {
    'Q': ['REAL', 'PURE'],
    'V': ['Critical Reasoning', 'Reading Comprehension'],
    'DI': ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table', 'Graphs and Tables']
}
ALL_QUESTION_TYPES = list(set(qt for subj_qts in ALLOWED_QUESTION_TYPE.values() for qt in subj_qts))

ALLOWED_FUNDAMENTAL_SKILLS = {
    'Q': ['Equal/Unequal/ALG', 'Rates/Ratio/Percent', 'Rates/Ratios/Percent', 'Value/Order/Factors', 'Counting/Sets/Series/Prob/Stats'],
    'V': ['Plan/Construct', 'Identify Stated Idea', 'Identify Inferred Idea', 'Analysis/Critique'],
    'DI': ['N/A'] # Assuming only N/A based on di.csv example
}
ALL_FUNDAMENTAL_SKILLS = list(set(fs for subj_fss in ALLOWED_FUNDAMENTAL_SKILLS.values() for fs in subj_fss))


VALIDATION_RULES = {
    # Original Column Name (before rename) : { rules }
    'Response Time (Minutes)': {'type': 'positive_float', 'error': "必須是正數 (例如 1.5, 2)。"},
    'Performance': {'allowed': ALLOWED_PERFORMANCE, 'error': f"必須是 {ALLOWED_PERFORMANCE} 其中之一 (大小寫/空格敏感)。"},
    'Content Domain': {'allowed': ALL_CONTENT_DOMAINS, 'subject_specific': ALLOWED_CONTENT_DOMAIN, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Question Type': {'allowed': ALL_QUESTION_TYPES, 'subject_specific': ALLOWED_QUESTION_TYPE, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Fundamental Skills': {'allowed': ALL_FUNDAMENTAL_SKILLS, 'subject_specific': ALLOWED_FUNDAMENTAL_SKILLS, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    # We will validate the 'Question' column after potential rename
    'Question': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"},
    '\ufeffQuestion': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"}, # Handle BOM
    # Removed validation for b-values as they are not expected user inputs
    # 'DI_b': {'type': 'number', 'error': "必須是數字。"},
    # 'Q_b': {'type': 'number', 'error': "必須是數字。"},
    # 'V_b': {'type': 'number', 'error': "必須是數字。"},
}

# --- End Validation Rules ---

# --- Validation Helper Function ---
def validate_dataframe(df, subject):
    """
    Validates the DataFrame rows based on predefined rules for the subject.

    Args:
        df (pd.DataFrame): The DataFrame to validate (potentially edited).
        subject (str): The subject ('Q', 'V', 'DI') to apply specific rules.

    Returns:
        list: A list of error message strings. Empty list if valid.
    """
    errors = []
    # Define required columns based on the *original* expected names from CSVs
    # We check these exist in the df passed *to* validation (which is the edited_df)
    required_original_columns = {
        'Q': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type', 'Fundamental Skills'],
        'V': ['Question', 'Response Time (Minutes)', 'Performance', 'Question Type', 'Fundamental Skills'], # REMOVE Content Domain for V
        'DI': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type'] # REMOVE Fundamental Skills for DI
    }
    # Adjust required based on BOM possibility for 'Question'
    actual_required = required_original_columns.get(subject, [])
    question_col_to_check = 'Question' # Default
    if '\ufeffQuestion' in df.columns and 'Question' not in df.columns:
         question_col_to_check = '\ufeffQuestion'
         actual_required = [col if col != 'Question' else '\ufeffQuestion' for col in actual_required]
    elif 'Question' not in df.columns and '\ufeffQuestion' not in df.columns:
         # If neither standard 'Question' nor BOM version exists, flag 'Question' as missing
         pass # Let the check below handle it

    # Helper function for preprocessing skill names (lowercase, strip, collapse spaces)
    def preprocess_skill(skill):
        return re.sub(r'\\s+', ' ', str(skill).strip()).lower()

    # 1. Check for missing required columns first (using the potentially BOM-adjusted list)
    missing_cols = [col for col in actual_required if col not in df.columns]
    if missing_cols:
        # If 'Question' is missing, but '\ufeffQuestion' was required and IS present, don't report 'Question' as missing.
        if 'Question' in missing_cols and question_col_to_check == '\ufeffQuestion':
             missing_cols.remove('Question') # Remove the standard one if BOM version is the one we check

        # Re-check if missing_cols is now empty
        if missing_cols:
             errors.append(f"資料缺少必要欄位: {', '.join(missing_cols)}。請檢查上傳/貼上的資料或編輯結果。")
             return errors # Stop further validation if essential columns are missing

    # 2. Validate cell values row by row
    for index, row in df.iterrows():
        for col_name, rules in VALIDATION_RULES.items():
            # Determine the actual column name to check in the dataframe (handling BOM)
            current_col_name = col_name
            if col_name == 'Question' and question_col_to_check == '\ufeffQuestion':
                 current_col_name = question_col_to_check # Use BOM version if that's what df has

            if current_col_name not in df.columns:
                # Only skip if the original column name (non-BOM) wasn't in the required list
                # This prevents skipping validation for a required column just because it wasn't found (e.g., 'Performance')
                if col_name not in actual_required:
                    continue # Skip validation if column doesn't exist AND wasn't required

            # If the column IS required but wasn't found above, it would have returned errors already.
            # If it's not required and not present, we skipped. Now, if it *is* present:
            if current_col_name in df.columns:
                value = row[current_col_name]

                # Skip validation for truly empty/NaN cells for now
                if pd.isna(value): # Check for NaN first
                     continue
                # Convert to string and check if empty *after* stripping whitespace
                value_str_for_empty_check = str(value).strip()
                if value_str_for_empty_check == '':
                     continue # Also skip visibly empty cells

                is_valid = True
                error_detail = rules['error']
                correct_value = None # To store the value we might correct to

                # Type checks (apply strip here for robustness)
                if 'type' in rules:
                    value_str = str(value).strip() # Use stripped value for validation
                    if rules['type'] == 'positive_float':
                        try:
                            num = float(value_str)
                            if num <= 0: is_valid = False
                        except (ValueError, TypeError):
                            is_valid = False
                    elif rules['type'] == 'positive_integer':
                        try:
                            # Convert to float first to handle inputs like '1.0'
                            num_float = float(value_str)
                            # Check if positive, is an integer (no fractional part), and matches int conversion
                            if num_float > 0 and num_float == int(num_float):
                                is_valid = True
                            else:
                                is_valid = False # Not positive or has fractional part
                        except (ValueError, TypeError):
                             # If conversion to float fails, it's not a valid representation of an integer
                            is_valid = False
                    elif rules['type'] == 'number':
                         try:
                             float(value_str) # Just check if convertible
                         except (ValueError, TypeError):
                             is_valid = False

                # Allowed list checks (case and space sensitive - use original value)
                elif 'allowed' in rules:
                    allowed_values = rules['allowed']
                    # Use subject-specific list if available
                    if 'subject_specific' in rules and subject in rules['subject_specific']:
                        allowed_values = rules['subject_specific'][subject]

                    value_str_stripped = str(value).strip() # Value after stripping whitespace
                    value_str_lower = value_str_stripped.lower() # Lowercase version for comparison

                    # --- Start Specific Logic for Q: Question Type ---
                    if col_name == 'Question Type' and subject == 'Q':
                        if value_str_lower == 'real contexts':
                            correct_value = 'REAL'
                            is_valid = True
                        elif value_str_lower == 'pure contexts':
                            correct_value = 'PURE'
                            is_valid = True
                        else:
                            # Fallback to standard check if not the special context values
                            allowed_values_map = {str(v).lower(): v for v in allowed_values}
                            if value_str_lower in allowed_values_map:
                                correct_value = allowed_values_map[value_str_lower]
                                is_valid = True
                            else:
                                is_valid = False
                    # --- End Specific Logic for Q: Question Type ---

                    # --- Start Specific Logic for Fundamental Skills (Fuzzy Match + Canonical Mapping) ---
                    elif col_name == 'Fundamental Skills':
                        processed_input = preprocess_skill(value_str_stripped)
                        is_valid = False # Assume invalid initially
                        correct_value = None

                        # Build a map from preprocessed key to canonical value
                        skill_map = {}
                        for allowed_val in allowed_values: # allowed_values is subject-specific list
                            processed_allowed = preprocess_skill(allowed_val)
                            # Define the canonical value
                            if processed_allowed == 'rates/ratios/percent':
                                canonical_value = 'Rates/Ratio/Percent' # Standard singular form
                            else:
                                canonical_value = allowed_val # Use the value itself as canonical
                            skill_map[processed_allowed] = canonical_value

                        # Check if the preprocessed input exists as a key
                        if processed_input in skill_map:
                            correct_value = skill_map[processed_input] # Get the canonical value
                            is_valid = True
                    # --- End Specific Logic for Fundamental Skills ---

                    # --- Default Case-Insensitive Check (Handles case and specific variations like Graphs/Graph) ---
                    else:
                        # Build a map from lowercase key to canonical value
                        allowed_values_map = {}
                        for v in allowed_values:
                            key = str(v).lower()
                            # Map specific variations to their canonical form
                            if key == 'graphs and tables':
                                canonical_value = 'Graph and Table' # Standard form
                            else:
                                canonical_value = v # Use the value itself as canonical
                            allowed_values_map[key] = canonical_value

                        # Check if the lowercased input exists as a key in the map
                        if value_str_lower in allowed_values_map:
                            correct_value = allowed_values_map[value_str_lower] # Get the canonical value
                            is_valid = True
                        else:
                            is_valid = False
                    # --- End Default Check ---

                    # --- Correction Logic (Applies if a match was found above and correct_value is set) ---
                    if is_valid and correct_value is not None:
                        # If the stripped original value differs from the correct capitalization/format, update the DataFrame
                        if value_str_stripped != correct_value:
                            try:
                                # Use .loc for safe assignment
                                df.loc[index, current_col_name] = correct_value
                                # Optionally, log the correction?
                                # print(f"Corrected row {index}, col '{current_col_name}': '{value}' -> '{correct_value}'")
                            except Exception as e:
                                errors.append(f"第 {index + 1} 行, 欄位 '{current_col_name}': 嘗試自動修正大小寫/格式時出錯 ({e})。")
                                is_valid = False # Mark as invalid if correction fails
                    elif not is_valid:
                        # Format allowed values clearly for the error message if validation failed
                        allowed_values_str = ", ".join(f"'{v}'" for v in allowed_values)
                        error_detail += f" 允許的值: {allowed_values_str} (大小寫/空格不敏感匹配失敗)。"
                    # --- End Correction Logic ---

                if not is_valid:
                    # Add 1 to index for user-friendly row numbering (Excel/CSV style)
                    # Use current_col_name in the error message as that's the column header the user sees
                    errors.append(f"第 {index + 1} 行, 欄位 '{current_col_name}': 值 '{value}' 無效。{error_detail}")

    return errors
# --- End Validation Helper ---


# --- Initialize Session State ---
# To track if analysis has been run and store results
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False
if 'report_dict' not in st.session_state:
    st.session_state.report_dict = {}
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'final_thetas' not in st.session_state:
     st.session_state.final_thetas = {}
# Remove state for validated dataframes
# if 'validated_df_q' not in st.session_state:
#     st.session_state.validated_df_q = None
# if 'validated_df_v' not in st.session_state:
#     st.session_state.validated_df_v = None
# if 'validated_df_di' not in st.session_state:
#     st.session_state.validated_df_di = None

# --- Sidebar Settings (Keep as is) ---
st.sidebar.subheader("OpenAI 設定 (選用)")
api_key_input = st.sidebar.text_input(
    "輸入您的 OpenAI API Key：", 
    type="password", 
    help="或者設定 OPENAI_API_KEY 環境變數。用於生成文字摘要。"
)
openai_api_key = api_key_input if api_key_input else os.getenv("OPENAI_API_KEY")

st.sidebar.subheader("IRT 模擬設定")
initial_theta_q = st.sidebar.number_input("Q 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_v = st.sidebar.number_input("V 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_di = st.sidebar.number_input("DI 科目初始 Theta 估計", value=0.0, step=0.1)

BANK_SIZE = 1000 
TOTAL_QUESTIONS_Q = 21
TOTAL_QUESTIONS_V = 23
TOTAL_QUESTIONS_DI = 20
RANDOM_SEED = 1000 
MAX_FILE_SIZE_MB = 1 # Define max file size in MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024 # Calculate size in bytes
# --- End Sidebar ---

st.title('GMAT 成績診斷平台')

# --- Data Input Section (Using Tabs) ---
st.header("1. 上傳或貼上各科成績單")

st.info(f"提示：上傳的 CSV 檔案大小請勿超過 {MAX_FILE_SIZE_MB}MB。貼上的資料沒有此限制。") # Add info message

# Initialize DataFrames
df_q = None
df_v = None
df_di = None
data_sources = {}

tab_q, tab_v, tab_di = st.tabs(["Quantitative (Q)", "Verbal (V)", "Data Insights (DI)"])

with tab_q:
    st.subheader("Quantitative (Q) 資料輸入")
    uploaded_file_q = st.file_uploader(
        "上傳 Q 科目 CSV 檔案", 
        type="csv", 
        key="q_uploader",
        help=f"檔案大小限制為 {MAX_FILE_SIZE_MB}MB。"
    )
    pasted_data_q = st.text_area("或將 Q 科目 Excel 資料貼在此處：", height=150, key="q_paster")
    
    # --- Add Header Requirement Info ---
    st.caption("請確保資料包含以下欄位標題 (大小寫/空格敏感): 'Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type', 'Fundamental Skills'")
    # --- End Header Requirement Info ---

    temp_df_q = None
    source_q = None
    data_source_type_q = None # Track source type

    if uploaded_file_q is not None:
        if uploaded_file_q.size > MAX_FILE_SIZE_BYTES:
            st.error(f"檔案大小 ({uploaded_file_q.size / (1024*1024):.2f} MB) 超過 {MAX_FILE_SIZE_MB}MB 限制。")
            # source_q remains None
        else:
            source_q = uploaded_file_q
            data_source_type_q = 'File Upload'
    elif pasted_data_q:
        source_q = StringIO(pasted_data_q)
        data_source_type_q = 'Pasted Data'

    if source_q is not None:
        try:
            temp_df_q = pd.read_csv(source_q, sep=None, engine='python')
            
            # --- Explicitly Remove *_b columns --- 
            cols_to_drop_q = [col for col in temp_df_q.columns if str(col).endswith('_b')]
            if cols_to_drop_q:
                temp_df_q.drop(columns=cols_to_drop_q, inplace=True)
                st.caption(f"已自動忽略以下欄位: {', '.join(cols_to_drop_q)}")
            # --- End Remove --- 
            
            # --- Initial Cleaning: Drop empty rows and columns --- 
            initial_rows_q, initial_cols_q = temp_df_q.shape
            temp_df_q.dropna(how='all', inplace=True) # Drop rows where ALL are NaN
            temp_df_q.dropna(axis=1, how='all', inplace=True) # Drop columns where ALL are NaN
            temp_df_q.reset_index(drop=True, inplace=True) # Reset index
            cleaned_rows_q, cleaned_cols_q = temp_df_q.shape
            if initial_rows_q > cleaned_rows_q or initial_cols_q > cleaned_cols_q:
                 st.caption(f"已自動移除 {initial_rows_q - cleaned_rows_q} 個空行和 {initial_cols_q - cleaned_cols_q} 個空列。")
            # --- End Initial Cleaning ---

            # --- Editable Preview --- 
            validation_errors_q = [] # Initialize error list for Q
            if not temp_df_q.empty:
                st.write("預覽與編輯資料 (修改後請確保欄位符合下方要求)：")
                try:
                    # Use data_editor for viewing all data and allowing edits
                    edited_temp_df_q = st.data_editor(
                        temp_df_q,
                        key="editor_q",
                        num_rows="dynamic", # Allow adding/deleting rows
                        use_container_width=True
                    )
                    # --- START VALIDATION ---
                    validation_errors_q = validate_dataframe(edited_temp_df_q, 'Q')
                    if validation_errors_q:
                        st.error("Q科目: 發現以下輸入錯誤，請修正：")
                        for error in validation_errors_q:
                            st.error(f"- {error}")
                        temp_df_q = None # Mark as invalid if errors found
                    else:
                        temp_df_q = edited_temp_df_q # Use the validated, edited dataframe
                    # --- END VALIDATION ---

                except Exception as editor_e:
                    st.error(f"編輯器載入或操作時發生錯誤：{editor_e}")
                    temp_df_q = None # Stop processing this tab on editor error
            else:
                st.warning("讀取的資料在清理空行/空列後為空。")
                temp_df_q = None # Set to None if empty after cleaning

            # Proceed with standardization ONLY if temp_df_q is not None (i.e., no validation errors)
            if temp_df_q is not None:
                # --- Standardize Columns (Handle potential 'Question' variations) --- 
                rename_map_q = {
                    # '﻿Question': 'question_position', # Old logic
                    'Performance': 'Correct',
                    'Response Time (Minutes)': 'question_time',
                    'Question Type': 'question_type',
                    'Content Domain': 'content_domain',
                    'Fundamental Skills': 'question_fundamental_skill'
                }
                # Dynamically add the position mapping based on columns found in the *edited* df
                if '\ufeffQuestion' in temp_df_q.columns: # Check for BOM + Question first
                    rename_map_q['\ufeffQuestion'] = 'question_position'
                elif 'Question' in temp_df_q.columns: # Check for plain 'Question'
                    rename_map_q['Question'] = 'question_position'

                # Apply only columns that exist in the edited dataframe
                cols_to_rename = {k: v for k, v in rename_map_q.items() if k in temp_df_q.columns}
                if cols_to_rename:
                     temp_df_q.rename(columns=cols_to_rename, inplace=True)

                # Standardize question_type AFTER renaming
                if 'question_type' in temp_df_q.columns:
                    temp_df_q['question_type'] = temp_df_q['question_type'].astype(str).str.strip().str.upper()
                else:
                     st.warning("Q: 編輯後的資料缺少 'question_type' (或原始對應) 欄位。", icon="⚠️")

                if 'Correct' in temp_df_q.columns:
                     # Convert to boolean consistently
                     temp_df_q['Correct'] = temp_df_q['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                     temp_df_q.rename(columns={'Correct': 'is_correct'}, inplace=True) # Rename to is_correct
                else:
                    st.error("Q: 編輯後的資料缺少 'Performance'/'Correct' 欄位，無法確定錯誤題目。", icon="🚨")
                    temp_df_q = None # Mark as invalid

                if temp_df_q is not None:
                    data_sources['Q'] = data_source_type_q
                    st.success(f"Q 科目資料讀取成功 ({data_sources['Q']})！")
                    temp_df_q['Subject'] = 'Q' # Add subject identifier

                    # --- Ensure independent question_position for Q --- 
                    # Check if position exists AND is usable after potential edits/renaming
                    if 'question_position' not in temp_df_q.columns or pd.to_numeric(temp_df_q['question_position'], errors='coerce').isnull().any():
                        st.warning("Q: 缺少 'Question'/'question_position' 欄位或包含無效值，正在根據當前順序重新生成題號。", icon="⚠️")
                        # Use reset_index again to ensure consecutive numbering after edits
                        temp_df_q = temp_df_q.reset_index(drop=True)
                        temp_df_q['question_position'] = temp_df_q.index + 1
                    else:
                        # Ensure it's integer type after validation
                        temp_df_q['question_position'] = pd.to_numeric(temp_df_q['question_position'], errors='coerce').astype('Int64')
                    # --- End Ensure --- 
                    df_q = temp_df_q # Assign the fully processed df to df_q

            # Reset df_q if temp_df_q ended up being None after standardization/validation
            if temp_df_q is None:
                df_q = None
        except Exception as e:
            st.error(f"處理 Q 科目資料時發生錯誤：{e}")
            df_q = None # Ensure df_q is None on error

with tab_v:
    st.subheader("Verbal (V) 資料輸入")
    uploaded_file_v = st.file_uploader(
        "上傳 V 科目 CSV 檔案", 
        type="csv", 
        key="v_uploader",
        help=f"檔案大小限制為 {MAX_FILE_SIZE_MB}MB。"
    )
    pasted_data_v = st.text_area("或將 V 科目 Excel 資料貼在此處：", height=150, key="v_paster")
    
    # --- Add Header Requirement Info ---
    st.caption("請確保資料包含以下欄位標題 (大小寫/空格敏感): 'Question', 'Response Time (Minutes)', 'Performance', 'Question Type', 'Fundamental Skills'") # Note: Content Domain is often N/A for Verbal but check if your specific source requires it.
    # --- End Header Requirement Info ---

    temp_df_v = None
    source_v = None
    data_source_type_v = None

    if uploaded_file_v is not None:
        if uploaded_file_v.size > MAX_FILE_SIZE_BYTES:
            st.error(f"檔案大小 ({uploaded_file_v.size / (1024*1024):.2f} MB) 超過 {MAX_FILE_SIZE_MB}MB 限制。")
        else:
            source_v = uploaded_file_v
            data_source_type_v = 'File Upload'
    elif pasted_data_v:
        source_v = StringIO(pasted_data_v)
        data_source_type_v = 'Pasted Data'

    if source_v is not None:
        try:
            temp_df_v = pd.read_csv(source_v, sep=None, engine='python')
            
            # --- Explicitly Remove *_b columns --- 
            cols_to_drop_v = [col for col in temp_df_v.columns if str(col).endswith('_b')]
            if cols_to_drop_v:
                temp_df_v.drop(columns=cols_to_drop_v, inplace=True)
                st.caption(f"已自動忽略以下欄位: {', '.join(cols_to_drop_v)}")
            # --- End Remove --- 
            
            # --- Initial Cleaning --- 
            initial_rows_v, initial_cols_v = temp_df_v.shape
            temp_df_v.dropna(how='all', inplace=True)
            temp_df_v.dropna(axis=1, how='all', inplace=True)
            temp_df_v.reset_index(drop=True, inplace=True)
            cleaned_rows_v, cleaned_cols_v = temp_df_v.shape
            if initial_rows_v > cleaned_rows_v or initial_cols_v > cleaned_cols_v:
                 st.caption(f"已自動移除 {initial_rows_v - cleaned_rows_v} 個空行和 {initial_cols_v - cleaned_cols_v} 個空列。")
            # --- End Initial Cleaning ---

            # --- Editable Preview --- 
            validation_errors_v = [] # Initialize error list for V
            if not temp_df_v.empty:
                 st.write("預覽與編輯資料 (修改後請確保欄位符合下方要求)：")
                 try:
                    edited_temp_df_v = st.data_editor(
                        temp_df_v, 
                        key="editor_v", 
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    # --- START VALIDATION --- 
                    validation_errors_v = validate_dataframe(edited_temp_df_v, 'V')
                    if validation_errors_v:
                        st.error("V科目: 發現以下輸入錯誤，請修正：")
                        for error in validation_errors_v:
                            st.error(f"- {error}")
                        temp_df_v = None # Mark as invalid
                    else:
                        temp_df_v = edited_temp_df_v # Use validated df
                    # --- END VALIDATION --- 
                 except Exception as editor_e:
                     st.error(f"編輯器載入或操作時發生錯誤：{editor_e}")
                     temp_df_v = None
            else:
                 st.warning("讀取的資料在清理空行/空列後為空。")
                 temp_df_v = None

            # Proceed with standardization ONLY if temp_df_v is not None
            if temp_df_v is not None:
                # --- Standardize Columns --- 
                rename_map_v = {
                    # '﻿Question': 'question_position',
                    'Performance': 'Correct',
                    'Response Time (Minutes)': 'question_time',
                    'Question Type': 'question_type',
                    'Fundamental Skills': 'question_fundamental_skill'
                }
                if '\ufeffQuestion' in temp_df_v.columns:
                    rename_map_v['\ufeffQuestion'] = 'question_position'
                elif 'Question' in temp_df_v.columns:
                    rename_map_v['Question'] = 'question_position'
                
                cols_to_rename = {k: v for k, v in rename_map_v.items() if k in temp_df_v.columns}
                if cols_to_rename:
                    temp_df_v.rename(columns=cols_to_rename, inplace=True)

                # Standardize question_type AFTER renaming (Remove .str.upper() for V)
                if 'question_type' in temp_df_v.columns:
                    temp_df_v['question_type'] = temp_df_v['question_type'].astype(str).str.strip() # Keep original case for V
                else:
                     st.warning("V: 編輯後的資料缺少 'question_type' (或原始對應) 欄位。", icon="⚠️")

                if 'Correct' in temp_df_v.columns:
                     temp_df_v['Correct'] = temp_df_v['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                     temp_df_v.rename(columns={'Correct': 'is_correct'}, inplace=True)
                else:
                     st.error("V: 編輯後的資料缺少 'Performance'/'Correct' 欄位，無法確定錯誤題目。", icon="🚨")
                     temp_df_v = None

                if temp_df_v is not None:
                    data_sources['V'] = data_source_type_v
                    st.success(f"V 科目資料讀取成功 ({data_sources['V']})！")
                    temp_df_v['Subject'] = 'V'

                    # --- Ensure independent question_position for V --- 
                    if 'question_position' not in temp_df_v.columns or pd.to_numeric(temp_df_v['question_position'], errors='coerce').isnull().any():
                        st.warning("V: 缺少 'Question'/'question_position' 欄位或包含無效值，正在根據當前順序重新生成題號。", icon="⚠️")
                        temp_df_v = temp_df_v.reset_index(drop=True)
                        temp_df_v['question_position'] = temp_df_v.index + 1
                    else:
                        temp_df_v['question_position'] = pd.to_numeric(temp_df_v['question_position'], errors='coerce').astype('Int64')
                    # --- End Ensure --- 
                    df_v = temp_df_v

            # Reset df_v if temp_df_v ended up being None after standardization/validation
            if temp_df_v is None:
                df_v = None
        except Exception as e:
            st.error(f"處理 V 科目資料時發生錯誤：{e}")
            df_v = None

with tab_di:
    st.subheader("Data Insights (DI) 資料輸入")
    uploaded_file_di = st.file_uploader(
        "上傳 DI 科目 CSV 檔案", 
        type="csv", 
        key="di_uploader",
        help=f"檔案大小限制為 {MAX_FILE_SIZE_MB}MB。"
    )
    pasted_data_di = st.text_area("或將 DI 科目 Excel 資料貼在此處：", height=150, key="di_paster")
    
    # --- Add Header Requirement Info ---
    st.caption("請確保資料包含以下欄位標題 (大小寫/空格敏感): 'Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type'") # Note: Fundamental Skills is often N/A for DI but check if your specific source requires it.
    # --- End Header Requirement Info ---
    
    temp_df_di = None
    source_di = None
    data_source_type_di = None

    if uploaded_file_di is not None:
        if uploaded_file_di.size > MAX_FILE_SIZE_BYTES:
            st.error(f"檔案大小 ({uploaded_file_di.size / (1024*1024):.2f} MB) 超過 {MAX_FILE_SIZE_MB}MB 限制。")
        else:
            source_di = uploaded_file_di
            data_source_type_di = 'File Upload'
    elif pasted_data_di:
        source_di = StringIO(pasted_data_di)
        data_source_type_di = 'Pasted Data'

    if source_di is not None:
        try:
            temp_df_di = pd.read_csv(source_di, sep=None, engine='python')
            
            # --- Explicitly Remove *_b columns --- 
            cols_to_drop_di = [col for col in temp_df_di.columns if str(col).endswith('_b')]
            if cols_to_drop_di:
                temp_df_di.drop(columns=cols_to_drop_di, inplace=True)
                st.caption(f"已自動忽略以下欄位: {', '.join(cols_to_drop_di)}")
            # --- End Remove --- 
            
            # --- Initial Cleaning --- 
            initial_rows_di, initial_cols_di = temp_df_di.shape
            temp_df_di.dropna(how='all', inplace=True)
            temp_df_di.dropna(axis=1, how='all', inplace=True)
            temp_df_di.reset_index(drop=True, inplace=True)
            cleaned_rows_di, cleaned_cols_di = temp_df_di.shape
            if initial_rows_di > cleaned_rows_di or initial_cols_di > cleaned_cols_di:
                 st.caption(f"已自動移除 {initial_rows_di - cleaned_rows_di} 個空行和 {initial_cols_di - cleaned_cols_di} 個空列。")
            # --- End Initial Cleaning ---

            # --- Editable Preview --- 
            validation_errors_di = [] # Initialize error list for DI
            if not temp_df_di.empty:
                 st.write("預覽與編輯資料 (修改後請確保欄位符合下方要求)：")
                 try:
                     edited_temp_df_di = st.data_editor(
                         temp_df_di, 
                         key="editor_di", 
                         num_rows="dynamic",
                         use_container_width=True
                     )
                     # --- START VALIDATION --- 
                     validation_errors_di = validate_dataframe(edited_temp_df_di, 'DI')
                     if validation_errors_di:
                         st.error("DI科目: 發現以下輸入錯誤，請修正：")
                         for error in validation_errors_di:
                             st.error(f"- {error}")
                         temp_df_di = None # Mark as invalid
                     else:
                         temp_df_di = edited_temp_df_di # Use validated df
                     # --- END VALIDATION --- 
                 except Exception as editor_e:
                     st.error(f"編輯器載入或操作時發生錯誤：{editor_e}")
                     temp_df_di = None
            else:
                 st.warning("讀取的資料在清理空行/空列後為空。")
                 temp_df_di = None

            # Proceed with standardization ONLY if temp_df_di is not None
            if temp_df_di is not None:
                # --- Standardize Columns --- 
                rename_map_di = {
                    # '﻿Question': 'question_position',
                    'Performance': 'Correct',
                    'Response Time (Minutes)': 'question_time',
                    'Question Type': 'question_type',
                    'Content Domain': 'content_domain'
                }
                if '\ufeffQuestion' in temp_df_di.columns:
                    rename_map_di['\ufeffQuestion'] = 'question_position'
                elif 'Question' in temp_df_di.columns:
                    rename_map_di['Question'] = 'question_position'

                cols_to_rename = {k: v for k, v in rename_map_di.items() if k in temp_df_di.columns}
                if cols_to_rename:
                    temp_df_di.rename(columns=cols_to_rename, inplace=True)
                
                # Standardize question_type AFTER renaming (Remove .str.upper() for DI)
                if 'question_type' in temp_df_di.columns:
                    temp_df_di['question_type'] = temp_df_di['question_type'].astype(str).str.strip() # Keep original case for DI
                else:
                    st.warning("DI: 編輯後的資料缺少 'question_type' (或原始對應) 欄位。", icon="⚠️")
                
                if 'Correct' in temp_df_di.columns:
                     temp_df_di['Correct'] = temp_df_di['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                     temp_df_di.rename(columns={'Correct': 'is_correct'}, inplace=True) # Rename to is_correct
                else:
                     st.error("DI: 編輯後的資料缺少 'Performance'/'Correct' 欄位，無法確定錯誤題目。", icon="🚨")
                     temp_df_di = None

                if temp_df_di is not None:
                    data_sources['DI'] = data_source_type_di
                    st.success(f"DI 科目資料讀取成功 ({data_sources['DI']})！")
                    temp_df_di['Subject'] = 'DI'

                    # --- Ensure independent question_position for DI --- 
                    if 'question_position' not in temp_df_di.columns or pd.to_numeric(temp_df_di['question_position'], errors='coerce').isnull().any():
                        st.warning("DI: 缺少 'Question'/'question_position' 欄位或包含無效值，正在根據當前順序重新生成題號。", icon="⚠️")
                        temp_df_di = temp_df_di.reset_index(drop=True)
                        temp_df_di['question_position'] = temp_df_di.index + 1
                    else:
                        temp_df_di['question_position'] = pd.to_numeric(temp_df_di['question_position'], errors='coerce').astype('Int64')
                    # --- End Ensure --- 
                    df_di = temp_df_di

            # Reset df_di if temp_df_di ended up being None after standardization/validation
            if temp_df_di is None:
                 df_di = None
        except Exception as e:
            st.error(f"處理 DI 科目資料時發生錯誤：{e}")
            df_di = None

# --- Combine Input Data (After Tabs) ---
# Use the potentially edited and VALIDATED dataframes (df_q, df_v, df_di)
input_dfs = {'Q': df_q, 'V': df_v, 'DI': df_di}
# Filter out subjects where df is None (either initially or due to validation error)
loaded_subjects = {subj for subj, df in input_dfs.items() if df is not None}
# Create list of valid dataframes only
df_combined_input_list = [df for df in [df_q, df_v, df_di] if df is not None]
df_combined_input = None # Initialize

# Check if *any* data was loaded initially, even if it failed validation later
any_data_attempted = bool(data_sources) # Check if any source was identified

if df_combined_input_list: # Only proceed if there's at least one *valid* df
     try:
         # Concatenate with ignore_index=True, but 'question_position' is already calculated per subject
         df_combined_input = pd.concat(df_combined_input_list, ignore_index=True)

         # Ensure 'question_position' column exists after concat (it should, unless all inputs failed processing)
         if 'question_position' not in df_combined_input.columns:
             st.error("合併後資料缺少 'question_position' 欄位，無法繼續。檢查各科數據處理。")
             df_combined_input = None
         elif df_combined_input['question_position'].isnull().any():
              st.error("合併後 'question_position' 欄位包含空值，無法繼續。檢查各科數據處理。")
              df_combined_input = None
         # else:
         #     # Optional: Sort for better viewing/debugging, though later logic sorts per subject
         #     df_combined_input.sort_values(by=['Subject', 'question_position'], inplace=True)

     except Exception as e:
         st.error(f"合併 *有效* 輸入資料時發生錯誤: {e}")
         df_combined_input = None
elif any_data_attempted: # Data was loaded/pasted but ALL failed validation or processing
     st.warning("所有輸入的科目數據均未能通過驗證或處理，請檢查上方各分頁的錯誤信息。分析無法進行。")
# else: No data was ever loaded or pasted, message handled below

# --- Analysis Trigger Button ---
st.divider() # Add a visual separator

# Display the button differently based on whether data is ready
if df_combined_input is not None:
    if st.button("🔍 開始分析", type="primary", key="analyze_button"):
        st.session_state.analysis_run = True
        # Reset previous results when starting new analysis
        st.session_state.report_dict = {}
        st.session_state.ai_summary = None
        st.session_state.final_thetas = {}
    else:
        # If button not clicked in this run, keep analysis_run as False unless it was already True
        # This prevents analysis from running just on widget interaction after first run
        # st.session_state.analysis_run = st.session_state.get('analysis_run', False) # Keep existing state if button not clicked
        pass # No need to explicitly set to false, just don't set to true

elif any_data_attempted: # Data attempted but failed validation/combination
    st.error("數據驗證失敗或無法合併，請修正上方標示的錯誤後再試。")
    st.button("🔍 開始分析", type="primary", disabled=True, key="analyze_button_disabled_invalid") # Disable button
else:
    st.info("請在上方分頁中為至少一個科目上傳或貼上資料。")
    st.button("🔍 開始分析", type="primary", disabled=True, key="analyze_button_disabled_no_data") # Disable button

# --- Simulation, Processing, Diagnosis, and Output Tabs (Conditional Execution) ---
if st.session_state.analysis_run and df_combined_input is not None:

    st.header("2. 執行 IRT 模擬與診斷") # Combine headers
    all_simulation_histories = {} # Store histories per subject
    final_thetas = {}           # Store final theta per subject locally for this run
    df_final_for_diagnosis = None # Initialize

    # --- IRT Simulation ---
    simulation_success = True
    # with st.spinner("正在執行 IRT 模擬..."): # Replace with st.status
    with st.status("執行 IRT 模擬...", expanded=True) as status:
        st.write("初始化模擬題庫...")
        question_banks = {}
        try:
            # Create banks only for loaded subjects
            if 'Q' in loaded_subjects: question_banks['Q'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED)
            if 'V' in loaded_subjects: question_banks['V'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 1)
            if 'DI' in loaded_subjects: question_banks['DI'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 2)
            # Check for failure after trying to create all needed banks
            if any(subj in loaded_subjects and question_banks.get(subj) is None for subj in loaded_subjects):
                 st.error("創建模擬題庫失敗。")
                 simulation_success = False
                 status.update(label="模擬題庫創建失敗", state="error", expanded=True)
            else:
                 st.write("模擬題庫創建完成。")
        except Exception as e:
            st.error(f"創建模擬題庫時出錯: {e}")
            simulation_success = False
            status.update(label=f"模擬題庫創建出錯: {e}", state="error", expanded=True)

        if simulation_success:
            subject_params = {
                'Q': {'initial_theta': initial_theta_q, 'total_questions': TOTAL_QUESTIONS_Q},
                'V': {'initial_theta': initial_theta_v, 'total_questions': TOTAL_QUESTIONS_V},
                'DI': {'initial_theta': initial_theta_di, 'total_questions': TOTAL_QUESTIONS_DI}
            }

            for subject in loaded_subjects:
                st.write(f"執行 {subject} 科目模擬...")
                # Get parameters for simulation
                params = subject_params[subject]
                initial_theta = params['initial_theta']
                total_sim_questions = params['total_questions'] # Number of questions IN SIMULATION
                bank = question_banks[subject]
                
                # Get WRONG indices from the *original* user data for this subject
                user_df_subj = df_combined_input[df_combined_input['Subject'] == subject]
                wrong_indices = [] # Keep variable name for now, but it holds positions
                # Check for the final column name 'is_correct'
                if 'is_correct' in user_df_subj.columns:
                    # Sort by position before getting indices
                    user_df_subj_sorted = user_df_subj.sort_values(by='question_position')
                    # Filter using the final column name 'is_correct'
                    # --- CORRECTED LOGIC HERE ---
                    # Directly get the 'question_position' values of incorrect answers
                    wrong_positions = user_df_subj_sorted[user_df_subj_sorted['is_correct'] == False]['question_position'].tolist()
                    wrong_indices = wrong_positions # Assign to the variable expected by the simulation function
                    # --- END CORRECTION ---
                    st.write(f"  {subject}: 從用戶數據提取 {len(wrong_indices)} 個錯誤題目位置: {wrong_indices}")
                else:
                    # This warning should now only appear if 'Performance' was truly missing initially
                    st.warning(f"  {subject}: 用戶數據缺少 'is_correct' 欄位 (源自 'Performance')，假設全部答對進行模擬。")
                    wrong_indices = []

                # Run the simulation
                try:
                    history_df = irt.simulate_cat_exam(
                        question_bank=bank,
                        wrong_question_indices=wrong_indices, # Pass the list of actual wrong positions
                        initial_theta=initial_theta,
                        total_questions=total_sim_questions # Use the simulation total questions
                    )
                    if history_df is not None and not history_df.empty:
                        all_simulation_histories[subject] = history_df
                        # Store final theta locally first
                        final_theta_subj = history_df['theta_est_after_answer'].iloc[-1]
                        final_thetas[subject] = final_theta_subj
                        st.write(f"  {subject}: 模擬完成。最後 Theta 估計: {final_theta_subj:.3f}")
                    elif history_df is not None and history_df.empty:
                        st.warning(f"  {subject}: 模擬執行了，但未產生歷史記錄。")
                        simulation_success = False # Treat empty history as failure for next steps
                    else:
                         st.error(f"  {subject}: 模擬執行失敗，返回 None。")
                         simulation_success = False
                         break # Stop simulation for other subjects if one fails
                except Exception as e:
                    st.error(f"  {subject}: 執行模擬時發生錯誤: {e}")
                    simulation_success = False
                    break # Stop simulation

        if simulation_success and all_simulation_histories:
            status.update(label="IRT 模擬完成！", state="complete", expanded=False)
            st.session_state.final_thetas = final_thetas # Store final thetas in session state
        elif simulation_success: # Banks created, but simulation failed for some reason
             status.update(label="IRT 模擬部分失敗或未產生結果", state="error", expanded=True)
             simulation_success = False # Ensure it's false
        # Else: Bank creation failed, status already set to error

    # --- Prepare Data for Diagnosis ---
    # st.header("2. 準備診斷數據 (結合用戶數據與模擬難度)") # Combined into header 2
    if simulation_success:
        # with st.spinner("準備診斷數據中..."): # Replace with st.status
        with st.status("準備診斷數據...", expanded=True) as status_prep:
            df_final_for_diagnosis_list = []
            processing_error = False
            for subject in loaded_subjects:
                st.write(f"處理 {subject} 科目...")
                user_df_subj = df_combined_input[df_combined_input['Subject'] == subject].copy()
                sim_history_df = all_simulation_histories.get(subject)
                final_theta = final_thetas.get(subject)

                if sim_history_df is None or sim_history_df.empty:
                    st.error(f"找不到 {subject} 科目的有效模擬結果，無法繼續。")
                    processing_error = True; status_prep.update(state="error"); break

                # Extract simulated b-values
                sim_b_values = sim_history_df['b'].tolist()
                
                # Sort user data by position
                user_df_subj_sorted = user_df_subj.sort_values(by='question_position')
                num_user_questions = len(user_df_subj_sorted)
                num_sim_b = len(sim_b_values)

                # Check for length mismatch between user data and simulation results
                if num_user_questions != num_sim_b:
                     st.warning(f"{subject}: 用戶數據題目數 ({num_user_questions}) 與模擬結果數 ({num_sim_b}) 不符。" 
                               f"將僅使用前 {min(num_user_questions, num_sim_b)} 個數據進行難度賦值。診斷可能不完整。")
                     # Truncate to the minimum length
                     min_len = min(num_user_questions, num_sim_b)
                     user_df_subj_sorted = user_df_subj_sorted.iloc[:min_len]
                     sim_b_values = sim_b_values[:min_len]
                
                if not sim_b_values: # Check if list became empty after truncation
                     st.error(f"{subject}: 無可用的模擬難度值，無法繼續處理。")
                     processing_error = True; status_prep.update(state="error"); break

                # Assign simulated b-values as 'question_difficulty'
                user_df_subj_sorted['question_difficulty'] = sim_b_values
                st.write(f"  {subject}: 已將模擬難度賦值給 {len(user_df_subj_sorted)} 道題目。")

                # Add final theta as context
                if final_theta is not None:
                     user_df_subj_sorted['estimated_ability'] = final_theta

                df_final_for_diagnosis_list.append(user_df_subj_sorted)
            
            if not processing_error and df_final_for_diagnosis_list:
                df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
                
                # st.subheader("診斷用數據預覽 (含模擬難度)") # Optional: Move preview here?
                # st.dataframe(df_final_for_diagnosis.head())
                st.write("所有科目數據準備完成。")
                status_prep.update(label="診斷數據準備完成！", state="complete", expanded=False)
            elif not processing_error: # List is empty but no specific error flagged?
                 st.warning("未能準備任何診斷數據。")
                 status_prep.update(label="未能準備診斷數據", state="warning", expanded=True)
            # Else: error occurred, status already set
    
    # --- Diagnosis Section --- (Now uses df_final_for_diagnosis)
    diagnosis_expander = st.expander('診斷過程', expanded=False)
    
    if df_final_for_diagnosis is not None: # Check if data prep was successful
        # Define required columns immediately after confirming df_final_for_diagnosis exists
        required_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'Subject']

        with diagnosis_expander:
            st.write("開始進行診斷分析...")
            progress_bar = st.progress(0, text="初始化診斷過程...")
            
            # --- Display Subject Distribution and Difficulty Column Type Check --- 
            subject_counts = df_final_for_diagnosis['Subject'].value_counts()
            
            if 'question_fundamental_skill' not in df_final_for_diagnosis.columns:
                st.warning(f"警告: 資料中缺少 'question_fundamental_skill' 欄位，將使用預設值。")
                df_final_for_diagnosis['question_fundamental_skill'] = 'Unknown Skill' # Add placeholder
            if 'content_domain' not in df_final_for_diagnosis.columns:
                st.warning(f"警告: 資料中缺少 'content_domain' 欄位，將使用預設值。")
                df_final_for_diagnosis['content_domain'] = 'Unknown Domain' # Add placeholder

            # Define required columns inside the 'with' block, right before use
            required_cols = ['question_position', 'is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'Subject']

            missing_cols = [col for col in required_cols if col not in df_final_for_diagnosis.columns]
            if missing_cols:
                st.error(f"缺少必須的欄位: {', '.join(missing_cols)}")
                st.info("請確保您的資料包含所有必要欄位。")
            else:
                # Run diagnosis if all required columns are present
                progress_bar.progress(25, text="正在執行診斷分析...")
                try:
                    # Update this line to handle the tuple return value
                    report_dict, df_processed = run_diagnosis(df_final_for_diagnosis) # Expect a tuple now
                    
                    # Update df_final_for_diagnosis with processed data containing new diagnostic fields
                    df_final_for_diagnosis = df_processed
                    
                    progress_bar.progress(100, text="診斷分析完成！")
                    # Store the report_dict in session state for later use
                    st.session_state.report_dict = report_dict
                    st.session_state.diagnosis_complete = True
                    st.success("診斷分析成功完成。請選擇下方選項卡查看結果或原始資料。")
                except Exception as e:
                    st.error(f"診斷過程中發生錯誤: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.session_state.diagnosis_complete = False

# --- Display Results Section (Uses Session State) ---
st.divider()
if st.session_state.analysis_run: # Only show results area if analysis was attempted
    st.header("診斷結果")

    # Display Final Thetas if available
    if st.session_state.final_thetas:
         theta_items = [f"{subj}: {theta:.3f}" for subj, theta in st.session_state.final_thetas.items()]
         st.success(f"最終能力估計 (Theta): {', '.join(theta_items)}")

    # Check if the report dictionary exists AND is actually a dictionary
    if isinstance(st.session_state.report_dict, dict):
        if st.session_state.report_dict: # Check if the dictionary is not None and not empty
            # Dynamically create tabs based on available reports and AI summary possibility
            report_subjects = sorted(st.session_state.report_dict.keys()) # Get subjects with reports (e.g., ['DI', 'Q', 'V'])
            tab_names = report_subjects # Start with subject tabs
            
            # Check if AI summary should be a tab
            ai_summary_available = st.session_state.ai_summary is not None
            should_show_ai_tab = ai_summary_available or openai_api_key # Show tab if summary exists or could be generated

            if should_show_ai_tab:
                tab_names.append("AI 文字摘要")

            if not tab_names:
                st.warning("沒有可顯示的診斷報告分頁。") # Should not happen if report_dict check passed, but for safety
            else:
                tabs = st.tabs(tab_names)
                
                # Create a dictionary to map tab names to tabs for easier access
                tab_map = dict(zip(tab_names, tabs))

                # Display subject reports in their respective tabs
                for subject in report_subjects:
                    if subject in tab_map: # Check if tab was created
                        with tab_map[subject]:
                            st.subheader(f"{subject} 科目詳細診斷報告") # Add subheader for clarity

                            # --- Display Input Data Table (using df_final_for_diagnosis) ---
                            df_to_display = None
                            # Check if the main diagnosis dataframe exists
                            if 'df_final_for_diagnosis' in locals() and df_final_for_diagnosis is not None:
                                try:
                                     # Filter the final diagnosis df for the current subject
                                     df_to_display = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == subject].copy()
                                     # Optional: Select or reorder columns for display if needed
                                     # display_cols = ['question_position', 'is_correct', 'question_time', 'question_difficulty', 'question_type', 'content_domain', 'question_fundamental_skill']
                                     # existing_display_cols = [col for col in display_cols if col in df_to_display.columns]
                                     # df_to_display = df_to_display[existing_display_cols]
                                except KeyError:
                                      st.warning(f"無法在最終數據中找到 {subject} 科目的 'Subject' 欄位進行過濾。")
                                      df_to_display = None # Reset if filtering fails
                                except Exception as filter_e:
                                      st.warning(f"過濾 {subject} 科目數據以供顯示時出錯: {filter_e}")
                                      df_to_display = None

                            # Display the filtered dataframe if it's valid and not empty
                            if df_to_display is not None and not df_to_display.empty:
                                st.subheader("診斷用數據 (含模擬難度)") # Changed subheader
                                # Define column configurations, assuming new columns exist from backend
                                column_config = {
                                    "question_position": st.column_config.NumberColumn("題號", format="%d", width="small"),
                                    "is_correct": st.column_config.CheckboxColumn("答對?", width="small"),
                                    "question_time": st.column_config.NumberColumn("用時(分)", format="%.1f", width="small"),
                                    "question_difficulty": st.column_config.NumberColumn("模擬難度(b)", format="%.2f", width="medium"),
                                    "question_type": st.column_config.TextColumn("題型", width="small"),
                                    "content_domain": st.column_config.TextColumn("內容領域", width="medium"),
                                    "question_fundamental_skill": st.column_config.TextColumn("核心技能", width="medium"),
                                    # --- New Columns Config --- 
                                    "time_performance_category": st.column_config.TextColumn(
                                        "時間表現分類", 
                                        help="綜合答題時間與正確性的分類 (快對/慢錯等)",
                                        width="medium"
                                    ),
                                    "is_sfe": st.column_config.CheckboxColumn(
                                        "基礎不穩(SFE)?", 
                                        help="是否為特殊關注錯誤 (Special Focus Error) - 在已掌握技能範圍內題目失誤",
                                        width="small"
                                    ),
                                     "diagnostic_params_list": st.column_config.ListColumn(
                                        "診斷標籤列表",
                                        help="該題目觸發的具體診斷標籤",
                                        width="large", # Adjust width as needed
                                    ),
                                     # Hide columns not typically needed for direct user view?
                                     "estimated_ability": None, # Hide estimated_ability
                                     "Subject": None, # Hide Subject column
                                } 
                                
                                # Filter config for columns that actually exist in the dataframe
                                existing_columns = df_to_display.columns
                                
                                # --- Start Subject-Specific Column Filtering ---
                                di_display_columns = ['question_position', 'question_time', 'content_domain', 'question_type', 'question_difficulty', 'time_performance_category', 'diagnostic_params_list', 'overtime']
                                q_display_columns = ['question_position', 'question_time', 'content_domain', 'question_type', 'question_fundamental_skill', 'question_difficulty', 'time_performance_category', 'diagnostic_params_list', 'overtime']
                                v_display_columns = ['question_position', 'question_time', 'question_type', 'question_fundamental_skill', 'question_difficulty', 'time_performance_category', 'diagnostic_params_list', 'overtime']
                                filtered_column_config = {}

                                if subject == 'DI':
                                    for col in existing_columns:
                                        if col in di_display_columns:
                                            # Get the config from base, default to simple text if not defined (though it should be)
                                            config_setting = column_config.get(col, st.column_config.TextColumn(col))
                                            # Do not add if the base config explicitly set it to None (hidden)
                                            if config_setting is not None:
                                                 filtered_column_config[col] = config_setting
                                        else:
                                            # Explicitly hide columns not in the desired list for DI
                                            filtered_column_config[col] = None
                                elif subject == 'Q':
                                     for col in existing_columns:
                                        if col in q_display_columns:
                                            config_setting = column_config.get(col, st.column_config.TextColumn(col))
                                            if config_setting is not None:
                                                 filtered_column_config[col] = config_setting
                                        else:
                                            filtered_column_config[col] = None
                                elif subject == 'V':
                                     for col in existing_columns:
                                        if col in v_display_columns:
                                            config_setting = column_config.get(col, st.column_config.TextColumn(col))
                                            if config_setting is not None:
                                                 filtered_column_config[col] = config_setting
                                        else:
                                            filtered_column_config[col] = None
                                else:
                                    # For non-DI subjects, use the original filtering logic
                                    filtered_column_config = {
                                        k: v for k, v in column_config.items() if k in existing_columns or v is None # Keep explicit None config
                                    }
                                # --- End Subject-Specific Column Filtering ---

                                # --- START APPLYING STYLES ---
                                # Define the style function inside the loop to access df_to_display columns
                                def apply_styles(row):
                                    # Default styles (no special styling)
                                    styles = [''] * len(row)
                                    # Apply red text to entire row if incorrect
                                    if 'is_correct' in row.index and not row['is_correct']:
                                        styles = ['color: #D32F2F'] * len(row) # Darker red text
                                    
                                    # Apply red background to time cell if overtime
                                    if 'overtime' in row.index:
                                        # 為除錯增加日誌輸出
                                        if row['overtime'] and 'question_time' in row.index:
                                            try:
                                                # Attempt to get the index of the 'question_time' column
                                                time_col_idx = row.index.get_loc('question_time')
                                                # Apply darker red background (ensure alpha isn't too strong)
                                                styles[time_col_idx] = 'background-color: rgba(244, 67, 54, 0.4)' # Darker red with transparency
                                            except KeyError:
                                                pass # Column not found, do nothing
                                            except IndexError:
                                                pass # Index out of bounds, do nothing
                                    
                                    return styles

                                # Check if necessary columns exist before applying styles
                                required_style_cols = ['is_correct', 'overtime']
                                if all(col in df_to_display.columns for col in required_style_cols):
                                     # Apply the styling function row-wise
                                     styler = df_to_display.style.apply(apply_styles, axis=1)
                                     # Display the styled DataFrame
                                     st.dataframe(
                                         styler, 
                                         use_container_width=True,
                                         column_config=filtered_column_config, # Use the filtered config
                                         hide_index=True 
                                     )
                                else:
                                     # Display the original DataFrame if styling columns are missing
                                     missing_style_cols = [col for col in required_style_cols if col not in df_to_display.columns]
                                     st.warning(f"部分樣式欄位缺失: {', '.join(missing_style_cols)}。無法應用樣式。")
                                     st.dataframe(
                                         df_to_display, 
                                         use_container_width=True,
                                         column_config=filtered_column_config, 
                                         hide_index=True 
                                     )
                                # --- END APPLYING STYLES --- 

                                st.divider() # Add separator before the text report
                            else:
                                # Show only if analysis was run but df is missing/empty for this subject
                                if st.session_state.analysis_run: 
                                    st.caption(f"未能加載用於顯示的 {subject} 科目診斷數據表格。") # Fallback message
                            # --- End Display Input Data Table ---

                            # Ensure the report content itself is a string before displaying
                            report_content = st.session_state.report_dict.get(subject, "")
                            if report_content: # Only display markdown if there is content
                                if isinstance(report_content, str):
                                    # --- START Replace Chapter 3 Content ---
                                    placeholder = "（請參考診斷表單中的標記）"
                                    # Regex pattern to find Chapter 3 title and content until Chapter 4 or end
                                    pattern = re.compile(r"(^\*\*3\.[^\n]*\*\*)(.*?)(?=^\*\*4\.|\Z)", re.DOTALL | re.MULTILINE)
                                    # Replacement function to keep the title (Group 1) and replace content
                                    replacement = rf'\1\n\n{placeholder}\n\n'
                                    modified_report_content = pattern.sub(replacement, report_content)
                                    # --- END Replace Chapter 3 Content ---

                                    # Display the modified content
                                    st.markdown(modified_report_content)
                                else:
                                    st.warning(f"{subject} 科目的報告內容不是有效的文字格式，無法顯示。")
                            elif st.session_state.analysis_run:
                                st.info(f"{subject} 科目沒有生成文字診斷報告。")

                # Display AI summary tab content
                if "AI 文字摘要" in tab_map:
                    with tab_map["AI 文字摘要"]:
                        st.subheader("AI 文字摘要")
                        if st.session_state.ai_summary:
                            st.markdown(st.session_state.ai_summary)
                        elif openai_api_key:
                            st.info("AI 摘要尚未生成或生成失敗。請檢查上方狀態。")
                        else:
                            st.info("請在側邊欄輸入 OpenAI API Key 並重新運行分析以生成 AI 文字摘要。")

    elif st.session_state.analysis_run:
        if not isinstance(st.session_state.report_dict, dict):
            st.error(f"診斷分析返回的結果類型錯誤。預期為字典 (dict)，但收到了類型：{type(st.session_state.report_dict).__name__}。請檢查 `diagnosis_module.run_diagnosis` 的返回值。")
        elif not st.session_state.report_dict:
            st.error("分析過程未成功生成診斷報告字典，或字典為空。請檢查上方的狀態信息和錯誤提示，並確認 `diagnosis_module.run_diagnosis` 是否返回了預期的字典格式且包含內容。")
