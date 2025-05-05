# -*- coding: utf-8 -*- # Ensure UTF-8 encoding for comments/strings
import sys
import os
import re # Import regex module
import io # Ensure io is imported
import pandas as pd # Ensure pandas is imported
import streamlit as st
from io import StringIO # Use io.StringIO directly
import traceback # For detailed error logging
import numpy as np
import logging
import openpyxl # Required by pandas for Excel export
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
import plotly.graph_objects as go # Add plotly import
import openai # Keep openai import

# --- Project Path Setup --- (Keep as is)
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # Handle cases where __file__ is not defined (e.g., interactive environments)
    st.warning("Could not automatically determine project root. Assuming modules are available.", icon="⚠️")
    project_root = os.getcwd() # Fallback

# --- Module Imports --- (Keep as is, consider try-except for robustness)
try:
    from gmat_diagnosis_app import irt_module as irt
    from gmat_diagnosis_app.preprocess_helpers import suggest_invalid_questions, calculate_overtime, THRESHOLDS
    from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
    from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed
    from gmat_diagnosis_app.diagnostics.q_diagnostic import run_q_diagnosis_processed
except ImportError as e:
    st.error(f"導入模組時出錯: {e}. 請確保環境設定正確，且 gmat_diagnosis_app 在 Python 路徑中。")
    st.stop()

# --- Constants ---
# Validation Rules (Case and space sensitive for allowed values)
ALLOWED_PERFORMANCE = ['Correct', 'Incorrect']
ALLOWED_CONTENT_DOMAIN = {
    'Q': ['Algebra', 'Arithmetic'],
    'V': ['N/A'],
    'DI': ['Math Related', 'Non-Math Related']
}
ALLOWED_QUESTION_TYPE = {
    'Q': ['REAL', 'PURE'],
    'V': ['Critical Reasoning', 'Reading Comprehension'],
    'DI': ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table', 'Graphs and Tables']
}
ALLOWED_FUNDAMENTAL_SKILLS = {
    'Q': ['Equal/Unequal/ALG', 'Rates/Ratio/Percent', 'Rates/Ratios/Percent', 'Value/Order/Factors', 'Counting/Sets/Series/Prob/Stats'],
    'V': ['Plan/Construct', 'Identify Stated Idea', 'Identify Inferred Idea', 'Analysis/Critique'],
    'DI': ['N/A']
}
ALL_CONTENT_DOMAINS = list(set(cd for subj_cds in ALLOWED_CONTENT_DOMAIN.values() for cd in subj_cds))
ALL_QUESTION_TYPES = list(set(qt for subj_qts in ALLOWED_QUESTION_TYPE.values() for qt in subj_qts))
ALL_FUNDAMENTAL_SKILLS = list(set(fs for subj_fss in ALLOWED_FUNDAMENTAL_SKILLS.values() for fs in subj_fss))

# Validation Rules Dictionary (Original Column Name : { rules })
VALIDATION_RULES = {
    'Response Time (Minutes)': {'type': 'positive_float', 'error': "必須是正數 (例如 1.5, 2)。"},
    'Performance': {'allowed': ALLOWED_PERFORMANCE, 'error': f"必須是 {ALLOWED_PERFORMANCE} 其中之一 (大小寫/空格敏感)。"},
    'Content Domain': {'allowed': ALL_CONTENT_DOMAINS, 'subject_specific': ALLOWED_CONTENT_DOMAIN, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Question Type': {'allowed': ALL_QUESTION_TYPES, 'subject_specific': ALLOWED_QUESTION_TYPE, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Fundamental Skills': {'allowed': ALL_FUNDAMENTAL_SKILLS, 'subject_specific': ALLOWED_FUNDAMENTAL_SKILLS, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Question': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"},
    '\ufeffQuestion': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"}, # Handle BOM
}

# Base Column Rename Map (Original CSV Header -> Internal Name)
BASE_RENAME_MAP = {
    'Performance': 'is_correct', # Rename to is_correct early
    'Response Time (Minutes)': 'question_time',
    'Question Type': 'question_type',
    'Content Domain': 'content_domain',
    'Fundamental Skills': 'question_fundamental_skill'
    # 'Question' handled dynamically based on BOM
}

# Required Original Columns per Subject (Used by validation)
REQUIRED_ORIGINAL_COLS = {
    'Q': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type', 'Fundamental Skills'],
    'V': ['Question', 'Response Time (Minutes)', 'Performance', 'Question Type', 'Fundamental Skills'], # Removed Content Domain for V
    'DI': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type'] # Removed Fundamental Skills for DI
}

# Columns to keep for final diagnosis dataframe preparation
# Ensure all columns needed by diagnosis functions are listed here
FINAL_DIAGNOSIS_INPUT_COLS = [
    'Subject', 'question_position', 'is_correct', 'question_time',
    'question_type', 'content_domain', 'question_fundamental_skill',
    'is_invalid', 'overtime', 'is_manually_invalid', # Keep manual flag for reference if needed
    # Add simulation/calculated columns later:
    'question_difficulty', 'estimated_ability'
]

# IRT Simulation Constants
BANK_SIZE = 1000
RANDOM_SEED = 1000
SUBJECT_SIM_PARAMS = {
    'Q': {'initial_theta_key': 'initial_theta_q', 'total_questions': THRESHOLDS['Q']['TOTAL_QUESTIONS'], 'seed_offset': 0},
    'V': {'initial_theta_key': 'initial_theta_v', 'total_questions': THRESHOLDS['V']['TOTAL_QUESTIONS'], 'seed_offset': 1},
    'DI': {'initial_theta_key': 'initial_theta_di', 'total_questions': THRESHOLDS['DI']['TOTAL_QUESTIONS'], 'seed_offset': 2}
}

# Other Constants
MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
SUBJECTS = ['Q', 'V', 'DI'] # Define subjects for iteration

# --- Styling Constants & Helpers ---
ERROR_FONT_COLOR = '#D32F2F' # Red for errors
OVERTIME_FILL_COLOR = '#FFCDD2' # Light red fill for overtime

def apply_styles(row):
    """Applies styling for invalid rows, incorrect answers, and overtime."""
    styles = [''] * len(row)
    INVALID_FONT_COLOR = '#A9A9A9' # DarkGray
    ERROR_FONT_COLOR = '#D32F2F' # Red for errors
    OVERTIME_FILL_COLOR = '#FFCDD2' # Light red fill for overtime

    try:
        # Grey text for invalid rows (overrides other text styles)
        if 'is_invalid' in row.index and row['is_invalid']:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # Apply overtime background even if invalid
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'{styles[time_col_idx]}; background-color: {OVERTIME_FILL_COLOR}'.lstrip('; ')
            return styles # Return early if invalid

        # Red text for incorrect (only if not invalid)
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)

        # Red background for overtime time cell (applies to correct or incorrect, but not invalid text color)
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            current_style = styles[time_col_idx]
            # Add background without overriding potential error text color
            styles[time_col_idx] = f'{current_style}; background-color: {OVERTIME_FILL_COLOR}'.lstrip('; ')

    except (KeyError, IndexError):
        pass # Ignore styling errors if columns are missing
    return styles

def to_excel(df, column_map):
    """Converts DataFrame to styled Excel bytes, hiding overtime flag."""
    output = io.BytesIO()
    df_copy = df.copy()

    # Select only columns present in the map keys and rename them
    columns_to_keep = [col for col in column_map.keys() if col in df_copy.columns]
    df_renamed = df_copy[columns_to_keep].rename(columns=column_map)

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_renamed.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Define formats
        error_format = workbook.add_format({'font_color': ERROR_FONT_COLOR})
        overtime_format = workbook.add_format({'bg_color': OVERTIME_FILL_COLOR})
        invalid_format = workbook.add_format({'font_color': '#A9A9A9'})

        # --- Apply Conditional Formatting ---
        header_list = list(df_renamed.columns)
        max_row = len(df_renamed) + 1
        try:
            # Find columns by *display* names (values in column_map)
            correct_col_disp = next(v for k, v in column_map.items() if k == 'is_correct')
            time_col_disp = next(v for k, v in column_map.items() if k == 'question_time')
            overtime_col_disp = next(v for k, v in column_map.items() if k == 'overtime') # Name of the overtime flag column
            invalid_col_disp = next(v for k, v in column_map.items() if k == 'is_invalid') # Name of the invalid flag column

            correct_col_idx = header_list.index(correct_col_disp)
            time_col_idx = header_list.index(time_col_disp)
            overtime_col_idx = header_list.index(overtime_col_disp)
            invalid_col_idx = header_list.index(invalid_col_disp)

            correct_col_letter = chr(ord('A') + correct_col_idx)
            time_col_letter = chr(ord('A') + time_col_idx)
            overtime_col_letter = chr(ord('A') + overtime_col_idx)
            invalid_col_letter = chr(ord('A') + invalid_col_idx)

            data_range = f'A2:{chr(ord("A") + len(header_list)-1)}{max_row}'
            time_col_range = f'{time_col_letter}2:{time_col_letter}{max_row}'

            # Grey text for invalid rows (apply first or ensure it overrides)
            worksheet.conditional_format(data_range, {'type': 'formula',
                                                     'criteria': f'=${invalid_col_letter}2="True"', # Check text value
                                                     'format': invalid_format})

            # Red text for incorrect answers (whole row) - might be overridden by grey if invalid
            worksheet.conditional_format(data_range, {'type': 'formula',
                                                     'criteria': f'=${correct_col_letter}2="False"', # Check text value
                                                     'format': error_format})

            # Red background for overtime time cells
            worksheet.conditional_format(time_col_range, {'type': 'formula',
                                                          'criteria': f'=${overtime_col_letter}2=TRUE', # Check the flag column (still bool maybe?)
                                                          'format': overtime_format})

            # Hide the overtime flag column ONLY
            worksheet.set_column(overtime_col_idx, overtime_col_idx, None, None, {'hidden': True})
            # Do NOT hide the invalid column

        except (StopIteration, ValueError, IndexError) as e:
            st.warning(f"無法應用 Excel 樣式或隱藏欄位: {e}", icon="⚠️") # Use warning

    processed_data = output.getvalue()
    return processed_data

# --- Validation Helper Function ---
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
# --- End Validation Helper ---

# --- NEW Plotting Function ---
def create_theta_plot(theta_history_df, subject_name):
    """Creates a Plotly line chart of theta estimation history, starting from question 0 (initial theta)."""
    if theta_history_df is None or theta_history_df.empty:
        logging.warning(f"無法為 {subject_name} 生成 Theta 圖表，因為歷史數據為空。")
        return None

    # Check if we can get the initial theta from the 'before' column
    if 'theta_est_before_answer' in theta_history_df.columns and not theta_history_df['theta_est_before_answer'].empty:
        initial_theta = theta_history_df['theta_est_before_answer'].iloc[0]
        # Prepare data starting from question 0
        x_values = [0] + (theta_history_df.index + 1).tolist()
        y_values = [initial_theta] + theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [f"初始 Theta: {initial_theta:.3f}<extra></extra>"] + \
                     [f"題號 {i+1}<br>Theta: {theta:.3f}<extra></extra>" for i, theta in enumerate(theta_history_df['theta_est_after_answer'])]

    elif 'theta_est_after_answer' in theta_history_df.columns and not theta_history_df['theta_est_after_answer'].empty:
        # Fallback: Start from question 1 if 'before' data is missing
        logging.warning(f"在 {subject_name} 的歷史數據中找不到 'theta_est_before_answer'，圖表將從題號 1 開始。")
        x_values = (theta_history_df.index + 1).tolist()
        y_values = theta_history_df['theta_est_after_answer'].tolist()
        hover_text = [f"題號 {i+1}<br>Theta: {theta:.3f}<extra></extra>" for i, theta in enumerate(y_values)]
    else:
        logging.warning(f"無法為 {subject_name} 生成 Theta 圖表，因為歷史數據缺少必要的 Theta 列。")
        return None

    fig = go.Figure()
    # Add trace using the prepared x and y values
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name='Theta 估計值',
        line=dict(color='royalblue', width=2),
        marker=dict(color='royalblue', size=5),
        hovertemplate=hover_text # Use the combined hover text
    ))

    fig.update_layout(
        title=f"{subject_name} 科目能力 (Theta) 估計變化",
        xaxis_title="題號 (0=初始值)", # Update axis title
        yaxis_title="Theta (能力估計值)",
        xaxis=dict(
            showgrid=True,
            zeroline=False,
            # Adjust dtick for potentially starting from 0
            dtick=max(1, (len(x_values)-1) // 10 if len(x_values) > 1 else 1),
            tick0=0 # Ensure ticks start nicely from 0
        ),
        yaxis=dict(
            showgrid=True,
            zeroline=True,
            range=[-4, 4] # FIX: Set fixed y-axis range
        ),
        hovermode="x unified",
        legend_title_text='估計值類型'
    )
    return fig
# --- End NEW Plotting Function ---

# --- NEW OpenAI Summarization Helper ---
def summarize_report_with_openai(report_markdown, api_key):
    """Attempts to summarize/reformat a report using OpenAI API."""
    if not api_key:
        logging.warning("OpenAI API key is missing. Skipping summarization.")
        return report_markdown # Return original if no key

    try:
        # Ensure openai library is accessible here
        if 'openai' not in sys.modules:
             st.warning("OpenAI library not loaded correctly.", icon="⚠️")
             return report_markdown

        client = openai.OpenAI(api_key=api_key) # Initialize client
        system_prompt = """You are an assistant that reformats GMAT diagnostic reports. Use uniform heading levels: Level-2 headings for all major sections (## Section Title). Level-3 headings for subsections (### Subsection Title). Reformat content into clear Markdown tables where appropriate. Fix minor grammatical errors or awkward phrasing for readability. IMPORTANT: Do NOT add or remove any substantive information or conclusions. Only reformat and polish the existing text. Output strictly in Markdown format, without code blocks.  """

        response = client.chat.completions.create(
            model="gpt-4.1-nano", # Use the specified model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": report_markdown}
            ],
            # temperature=0.2 # Removed: o4-mini only supports default (1)
        )
        summarized_report = response.choices[0].message.content
        # Basic check if response seems valid (not empty)
        if summarized_report and summarized_report.strip():
             logging.info(f"OpenAI summarization successful for report starting with: {report_markdown[:50]}...")
             return summarized_report.strip()
        else:
             logging.warning("OpenAI returned empty response. Using original report.")
             st.warning("AI 整理報告時返回了空內容，將使用原始報告。", icon="⚠️")
             return report_markdown

    except openai.AuthenticationError:
        st.warning("OpenAI API Key 無效或權限不足，無法整理報告文字。請檢查側邊欄輸入或環境變數。", icon="🔑")
        logging.error("OpenAI AuthenticationError.")
        return report_markdown
    except openai.RateLimitError:
        st.warning("OpenAI API 請求頻率過高，請稍後再試。暫時使用原始報告文字。", icon="⏳")
        logging.error("OpenAI RateLimitError.")
        return report_markdown
    except openai.APIConnectionError as e:
        st.warning(f"無法連接至 OpenAI API ({e})，請檢查網路連線。暫時使用原始報告文字。", icon="🌐")
        logging.error(f"OpenAI APIConnectionError: {e}")
        return report_markdown
    except openai.APITimeoutError:
         st.warning("OpenAI API 請求超時。暫時使用原始報告文字。", icon="⏱️")
         logging.error("OpenAI APITimeoutError.")
         return report_markdown
    except openai.BadRequestError as e:
         # Often happens with context length issues or invalid requests
         st.warning(f"OpenAI API 請求無效 ({e})。可能是報告過長或格式問題。暫時使用原始報告文字。", icon="❗") # Use valid emoji
         logging.error(f"OpenAI BadRequestError: {e}")
         return report_markdown
    except Exception as e:
        st.warning(f"調用 OpenAI API 時發生未知錯誤：{e}。暫時使用原始報告文字。", icon="⚠️")
        logging.error(f"Unknown OpenAI API error: {e}", exc_info=True)
        return report_markdown
# --- End OpenAI Summarization Helper ---

# --- Helper functions for AI Chat ---
def _get_combined_report_context():
    """Combines markdown reports from all subjects."""
    full_report = ""
    if st.session_state.report_dict:
        for subject in SUBJECTS:
            report = st.session_state.report_dict.get(subject)
            if report:
                full_report += f"\n\n## {subject} 科診斷報告\n\n{report}"
    return full_report.strip()

def _get_dataframe_context(max_rows=50):
    """Converts the processed dataframe to a string format (markdown) for context."""
    if st.session_state.processed_df is not None and not st.session_state.processed_df.empty:
        df_context = st.session_state.processed_df.copy()
        # Optionally select/rename columns for clarity in context
        # For now, let's convert a sample to markdown
        try:
            # Convert boolean columns to Yes/No for better readability for the LLM
            bool_cols = df_context.select_dtypes(include=bool).columns
            for col in bool_cols:
                df_context[col] = df_context[col].map({True: 'Yes', False: 'No'})
                
            # Convert list column to string
            if 'diagnostic_params_list' in df_context.columns:
                df_context['diagnostic_params_list'] = df_context['diagnostic_params_list'].apply(
                    lambda x: ', '.join(map(str, x)) if isinstance(x, list) else str(x)
                )
                
            # Limit rows to avoid excessive context length
            if len(df_context) > max_rows:
                df_context_str = df_context.head(max_rows).to_markdown(index=False)
                df_context_str += f"\n... (只顯示前 {max_rows} 行)"
            else:
                df_context_str = df_context.to_markdown(index=False)
            return df_context_str
        except Exception as e:
            logging.error(f"Error converting dataframe to markdown context: {e}")
            return "(無法轉換詳細數據表格)"
    return "(無詳細數據表格)"

def _get_openai_response(current_chat_history, report_context, dataframe_context):
    """Gets response from OpenAI using the responses endpoint and handles conversation history.
    
    Args:
        current_chat_history (list): The current chat history list.
        report_context (str): The combined markdown report context.
        dataframe_context (str): The dataframe context string.

    Returns:
        tuple: (ai_response_text, response_id) or raises an exception.
    """
    if not st.session_state.openai_api_key:
        raise ValueError("OpenAI API Key is missing.")
        
    client = openai.OpenAI(api_key=st.session_state.openai_api_key)
    
    # Find the last user prompt
    last_user_prompt = ""
    if current_chat_history and current_chat_history[-1]["role"] == "user":
        last_user_prompt = current_chat_history[-1]["content"]
    else:
        raise ValueError("Could not find the last user prompt in history.")
        
    # Find the previous response ID from the last assistant message
    previous_response_id = None
    if len(current_chat_history) > 1:
        for i in range(len(current_chat_history) - 2, -1, -1):
            if current_chat_history[i]["role"] == "assistant":
                previous_response_id = current_chat_history[i].get("response_id")
                break
                
    # Construct the input for the API using standard multi-line string and .format()
    input_template = '''You are a GMAT diagnostic assistant. Analyze the provided report summary and detailed data table (excerpt) to answer the user's question accurately and concisely. If the information is not present in the provided context, say so.

REPORT SUMMARY:
{report}

DETAILED DATA EXCERPT:
{data}

USER QUESTION:
{prompt}
'''
    api_input = input_template.format(
        report=report_context,
        data=dataframe_context,
        prompt=last_user_prompt
    )
    
    try:
        logging.info(f"Calling OpenAI responses.create with model gpt-4.1-mini. Previous ID: {previous_response_id}")
        response = client.responses.create(
            model="o4-mini", # Using the model from user's example
            input=api_input,
            previous_response_id=previous_response_id,
            # Add other parameters if needed, e.g., temperature, max_tokens based on API docs
            # max_output_tokens=500, # Example: limit output tokens
        )
        logging.info(f"OpenAI response received. Status: {response.status}")

        if response.status == 'completed' and response.output:
            # Extract text from the first output message content
            response_text = ""
            # Iterate through the output list to find the message block
            message_block = None
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    message_block = item
                    break # Found the message block
            
            if message_block and hasattr(message_block, 'content') and message_block.content:
                for content_block in message_block.content:
                    # Ensure the content_block itself has a type attribute before checking
                    if hasattr(content_block, 'type') and content_block.type == 'output_text':
                        response_text += content_block.text
            
            if not response_text:
                 # --- Log the output structure before raising error ---
                 logging.error(f"OpenAI response completed but no text found after iterating. Response output structure: {response.output}")
                 # --- End Log ---
                 raise ValueError("OpenAI response completed but contained no text output after iterating.")
                 
            return response_text.strip(), response.id
        elif response.status == 'error':
             error_details = response.error if response.error else "Unknown error"
             raise Exception(f"OpenAI API error: {error_details}")
        else:
             # --- Log the output structure before raising error ---
             logging.error(f"OpenAI response status not completed or output empty. Status: {response.status}. Response output structure: {response.output}")
             # --- End Log ---
             raise Exception(f"OpenAI response status was not 'completed' or output was empty. Status: {response.status}")

    except Exception as e:
        logging.error(f"Error calling OpenAI responses API: {e}", exc_info=True)
        # Re-raise the exception to be caught by the sidebar UI
        raise e
# Place this function near the other helper functions
# ... existing code ...

# --- Refactored Data Input Tab Function ---
def process_subject_tab(subject, tab_container, base_rename_map):
    """Handles data input, cleaning, validation, and standardization for a subject tab."""
    st.subheader(f"{subject} 資料輸入")
    subject_key = subject.lower()

    uploaded_file = tab_container.file_uploader(
        f"上傳 {subject} 科目 CSV 檔案",
        type="csv",
        key=f"{subject_key}_uploader",
        help=f"檔案大小限制為 {MAX_FILE_SIZE_MB}MB。"
    )
    pasted_data = tab_container.text_area(
        f"或將 {subject} 科目 Excel 資料貼在此處：",
        height=150,
        key=f"{subject_key}_paster"
    )

    # Display required headers
    req_cols_str = ", ".join(f"'{c}'" for c in REQUIRED_ORIGINAL_COLS.get(subject, []))
    tab_container.caption(f"請確保資料包含以下欄位標題 (大小寫/空格敏感): {req_cols_str}")

    temp_df = None
    source = None
    data_source_type = None
    validation_errors = []

    # Determine data source
    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE_BYTES:
            tab_container.error(f"檔案大小 ({uploaded_file.size / (1024*1024):.2f} MB) 超過 {MAX_FILE_SIZE_MB}MB 限制。")
            return None, 'File Upload', [] # Return error state
        else:
            source = uploaded_file
            data_source_type = 'File Upload'
    elif pasted_data:
        source = StringIO(pasted_data)
        data_source_type = 'Pasted Data'

    if source is not None:
        try:
            # Read data, attempt flexible separator detection
            temp_df = pd.read_csv(source, sep=None, engine='python', skip_blank_lines=True)

            # --- Initial Cleaning & Prep ---
            initial_rows, initial_cols = temp_df.shape
            # Drop *_b columns silently
            cols_to_drop = [col for col in temp_df.columns if str(col).endswith('_b')]
            if cols_to_drop:
                temp_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

            # Drop fully empty rows/columns
            temp_df.dropna(how='all', axis=0, inplace=True)
            temp_df.dropna(how='all', axis=1, inplace=True)
            temp_df.reset_index(drop=True, inplace=True)
            cleaned_rows, cleaned_cols = temp_df.shape
            if initial_rows > cleaned_rows or initial_cols > cleaned_cols:
                 tab_container.caption(f"已自動移除 {initial_rows - cleaned_rows} 個空行和 {initial_cols - cleaned_cols} 個空列。")

            if temp_df.empty:
                 tab_container.warning("讀取的資料在清理空行/空列後為空。")
                 return None, data_source_type, []

            # Add manual invalid column *before* editor
            temp_df['is_manually_invalid'] = False # Default to False

            # --- Preprocessing for Invalid Suggestion (for default checkbox state) ---
            try:
                # Create a temporary structure for suggestion function
                temp_suggest_df = temp_df.copy()
                temp_suggest_df['Subject'] = subject
                # Basic time pressure guess for suggestion (actual pressure calculated later)
                time_col_name = 'Response Time (Minutes)'
                pressure_guess = False
                if time_col_name in temp_suggest_df.columns:
                    times = pd.to_numeric(temp_suggest_df[time_col_name], errors='coerce').dropna()
                    if len(times) > 1:
                         # Use a simple threshold diff for the *guess*
                         diff_threshold = THRESHOLDS['Q']['TIME_DIFF_PRESSURE'] if subject == 'Q' else (THRESHOLDS['DI']['TIME_PRESSURE_DIFF_MIN'] if subject == 'DI' else 3.0) # Guess for V
                         pressure_guess = (times.max() - times.min()) > diff_threshold

                temp_pressure_map = {subject: pressure_guess}

                # Rename required columns for suggestion function
                temp_rename_map = {}
                if time_col_name in temp_suggest_df.columns: temp_rename_map[time_col_name] = 'question_time'
                question_col = '\ufeffQuestion' if '\ufeffQuestion' in temp_suggest_df.columns else 'Question'
                if question_col in temp_suggest_df.columns: temp_rename_map[question_col] = 'question_position'
                if 'Performance' in temp_suggest_df.columns: temp_rename_map['Performance'] = 'is_correct' # Need correct format for suggest

                # Apply temporary renames if needed
                if temp_rename_map:
                    temp_suggest_df.rename(columns=temp_rename_map, inplace=True)
                    # Convert 'is_correct' column format if it exists after renaming
                    if 'is_correct' in temp_suggest_df.columns:
                       temp_suggest_df['is_correct'] = temp_suggest_df['is_correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)


                # Call suggestion function IF necessary columns are present
                suggest_cols_present = all(c in temp_suggest_df.columns for c in ['question_time', 'question_position', 'is_correct'])
                if suggest_cols_present:
                    processed_suggest_df = suggest_invalid_questions(temp_suggest_df, temp_pressure_map)
                    # Update the manual invalid flag based on suggestion
                    if 'is_auto_suggested_invalid' in processed_suggest_df.columns:
                        # Align indices before assigning
                        temp_df['is_manually_invalid'] = processed_suggest_df['is_auto_suggested_invalid'].reindex(temp_df.index).fillna(False)
                else:
                     tab_container.caption("無法自動建議無效題目，缺少必要欄位(時間, 題號, 正確性)。請手動勾選。")


            except Exception as suggest_err:
                tab_container.warning(f"自動檢測無效題目時出錯，請手動檢查: {suggest_err}", icon="⚠️")

            # --- Editable Preview ---
            tab_container.write("預覽與編輯資料 (修改後請確保欄位符合要求)：")
            column_order = ['is_manually_invalid'] + [col for col in temp_df.columns if col != 'is_manually_invalid']

            # Ensure the checkbox column uses boolean type before editor
            temp_df['is_manually_invalid'] = temp_df['is_manually_invalid'].astype(bool)

            edited_df = tab_container.data_editor(
                temp_df,
                key=f"editor_{subject_key}",
                num_rows="dynamic",
                use_container_width=True,
                column_order=column_order,
                column_config={
                    "is_manually_invalid": st.column_config.CheckboxColumn(
                        "是否草率做題？ (手動標記)",
                        help="勾選此框表示您手動判斷此題為無效（例如因倉促/慌亂）。此標記將優先於系統自動建議。",
                        default=False,
                    )
                    # Add other specific configs here if needed (e.g., number formats)
                }
            )

            # --- Post-Edit Validation ---
            # Create a fresh copy for validation to avoid modifying editor's state directly if validation fails mid-way
            df_to_validate = edited_df.copy()
            validation_errors, warnings = validate_dataframe(df_to_validate, subject) # validate_dataframe now modifies df_to_validate in place for corrections

            if validation_errors:
                tab_container.error(f"{subject} 科目: 發現以下輸入錯誤，請修正：")
                for error in validation_errors:
                    tab_container.error(f"- {error}")
                return None, data_source_type, validation_errors # Indicate validation failure

            # --- Final Standardization (using the validated and potentially auto-corrected df_to_validate) ---
            final_df = df_to_validate
            # Handle 'Question' column naming for standardization
            question_col_name = '\ufeffQuestion' if '\ufeffQuestion' in final_df.columns else 'Question'
            current_rename_map = base_rename_map.copy()
            if question_col_name in final_df.columns: # Ensure the correct one is mapped
                current_rename_map[question_col_name] = 'question_position'

            # Apply renames for columns that exist
            cols_to_rename = {k: v for k, v in current_rename_map.items() if k in final_df.columns}
            if cols_to_rename:
                final_df.rename(columns=cols_to_rename, inplace=True)

            # Subject-specific standardization AFTER renaming
            if 'question_type' in final_df.columns:
                final_df['question_type'] = final_df['question_type'].astype(str).str.strip()
                if subject == 'Q':
                    final_df['question_type'] = final_df['question_type'].str.upper() # Uppercase only for Q

            # Convert performance ('is_correct') to boolean (if it exists)
            if 'is_correct' in final_df.columns:
                 # Validation already ensured 'Correct'/'Incorrect', so simple check is fine
                 final_df['is_correct'] = final_df['is_correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            else:
                 # This case should be caught by validation, but as a safeguard:
                 tab_container.error(f"{subject}: 編輯/驗證後仍缺少 'Performance'/'is_correct' 欄位。", icon="🚨")
                 return None, data_source_type, ["Missing 'Performance' column after edits."]

            # Ensure question_position is numeric and sequential if missing/invalid
            if 'question_position' not in final_df.columns or pd.to_numeric(final_df['question_position'], errors='coerce').isnull().any():
                tab_container.warning(f"{subject}: 'Question'/'question_position' 缺失或無效，將根據當前順序重新生成題號。", icon="⚠️")
                final_df = final_df.reset_index(drop=True) # Ensure index is clean before assigning
                final_df['question_position'] = final_df.index + 1
            else:
                # Convert valid ones to integer
                final_df['question_position'] = pd.to_numeric(final_df['question_position'], errors='coerce').astype('Int64')

            # Ensure 'is_manually_invalid' is boolean and set final 'is_invalid'
            if 'is_manually_invalid' not in final_df.columns: # Should exist from editor
                final_df['is_manually_invalid'] = False
            final_df['is_manually_invalid'] = final_df['is_manually_invalid'].fillna(False).astype(bool)
            final_df['is_invalid'] = final_df['is_manually_invalid'] # Final invalid status based on user edit

            # Add Subject identifier
            final_df['Subject'] = subject

            tab_container.success(f"{subject} 科目資料讀取與驗證成功 ({data_source_type})！")
            return final_df, data_source_type, warnings

        except pd.errors.ParserError as pe:
             tab_container.error(f"無法解析 {subject} 資料。請檢查是否為有效的 CSV 或 Tab 分隔格式，且標頭正確。錯誤: {pe}")
             return None, data_source_type, [f"ParserError: {pe}"]
        except Exception as e:
            tab_container.error(f"處理 {subject} 科目資料時發生未預期錯誤：{e}")
            # tab_container.code(traceback.format_exc()) # Optional: show full traceback for debugging
            return None, data_source_type, [f"Unexpected error: {e}"]

    return None, None, [] # No data source provided
# --- End Data Input Function ---

# --- Refactored Results Display Function ---
def display_subject_results(subject, tab_container, report_md, df_subject, col_config, excel_map):
    """Displays the diagnosis report, styled DataFrame, and download button for a subject."""
    tab_container.subheader(f"{subject} 科診斷報告")
    # This line renders the markdown report with wrapping
    tab_container.markdown(report_md if report_md else f"未找到 {subject} 科的診斷報告。", unsafe_allow_html=True) # Added unsafe_allow_html=True just in case AI uses basic HTML

    tab_container.subheader(f"{subject} 科詳細數據 (含診斷標籤)")

    if df_subject is None or df_subject.empty:
        tab_container.write(f"沒有找到 {subject} 科的詳細數據可供顯示。")
        return

    # Prepare DataFrame for Display
    # 1. Select columns based on keys in col_config that exist in the data
    cols_available = [k for k in col_config.keys() if k in df_subject.columns]
    df_to_display = df_subject[cols_available].copy()

    # 2. Define column order for st.dataframe (exclude those with None config value, like 'overtime')
    columns_for_st_display_order = [k for k in cols_available if col_config.get(k) is not None]

    # 3. Display styled DataFrame
    try:
        # Ensure necessary columns for styling exist with defaults
        if 'overtime' not in df_to_display.columns: df_to_display['overtime'] = False
        if 'is_correct' not in df_to_display.columns: df_to_display['is_correct'] = True # Assume correct if missing for styling

        styled_df = df_to_display.style.set_properties(**{'text-align': 'left'}) \
                                       .set_table_styles([dict(selector='th', props=[('text-align', 'left')])]) \
                                       .apply(apply_styles, axis=1)

        tab_container.dataframe(
            styled_df,
            column_config=col_config,
            column_order=columns_for_st_display_order,
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        tab_container.error(f"無法應用樣式或顯示 {subject} 科數據: {e}")
        # Fallback: Display without styling, only showing configured columns
        try:
             tab_container.dataframe(
                 df_to_display[columns_for_st_display_order], # Use only displayable columns
                 column_config=col_config,
                 hide_index=True,
                 use_container_width=True
             )
        except Exception as fallback_e:
             tab_container.error(f"顯示回退數據時也發生錯誤: {fallback_e}")


    # 4. Download Button
    try:
        # Prepare a copy specifically for Excel export using excel_map
        df_for_excel = df_subject[[k for k in excel_map.keys() if k in df_subject.columns]].copy()

        # Apply number formatting *before* calling to_excel if needed
        if 'question_difficulty' in df_for_excel.columns:
             df_for_excel['question_difficulty'] = pd.to_numeric(df_for_excel['question_difficulty'], errors='coerce').map('{:.2f}'.format)
        if 'question_time' in df_for_excel.columns:
             df_for_excel['question_time'] = pd.to_numeric(df_for_excel['question_time'], errors='coerce').map('{:.2f}'.format)
        # Convert bools to string representation if desired for Excel output clarity
        if 'is_correct' in df_for_excel.columns:
             df_for_excel['is_correct'] = df_for_excel['is_correct'].astype(str) # Convert TRUE/FALSE to text
        if 'is_sfe' in df_for_excel.columns:
             df_for_excel['is_sfe'] = df_for_excel['is_sfe'].astype(str)


        excel_bytes = to_excel(df_for_excel, excel_map) # Pass the df subset and the map

        tab_container.download_button(
            label=f"下載 {subject} 科詳細數據 (Excel)",
            data=excel_bytes,
            file_name=f"gmat_diag_{subject}_detailed_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_excel_{subject}"
        )
    except Exception as e:
        tab_container.error(f"無法生成 {subject} 科的 Excel 下載文件: {e}")
        # tab_container.code(traceback.format_exc()) # Optional debug info
# --- End Results Display Function ---


# ==============================================================================
# --- Streamlit App Main Logic ---
# ==============================================================================

# --- Initialize Session State ---
# Use functions to avoid repeating keys
def init_session_state():
    defaults = {
        'analysis_run': False,
        'diagnosis_complete': False, # Track if diagnosis step finished
        'report_dict': {},
        # 'ai_summary': None, # Removing old AI summary state if not used elsewhere
        'final_thetas': {},
        'processed_df': None, # Store the final DataFrame after processing+diagnosis
        'error_message': None,
        'analysis_error': False, # Initialize analysis_error flag
        'input_dfs': {}, # Store loaded & validated DFs from tabs
        'validation_errors': {}, # Store validation errors per subject
        'data_source_types': {}, # Store how data was loaded ('File Upload' or 'Pasted Data')
        'theta_plots': {}, # NEW: Initialize dict for plots
        # --- AI Chat State ---
        'openai_api_key': None,
        'show_chat': False,
        'chat_history': [] # List of dicts: {"role": "user/assistant", "content": "..."}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state() # Call it once at the start

# Function to reset state for new upload or analysis start
def reset_session_for_new_upload():
    st.session_state.analysis_run = False # Reset run flag too
    st.session_state.diagnosis_complete = False
    st.session_state.report_dict = {}
    # st.session_state.ai_summary = None # Removed
    st.session_state.final_thetas = {}
    st.session_state.processed_df = None
    st.session_state.error_message = None
    st.session_state.analysis_error = False # Reset error flag
    # Keep input_dfs, validation_errors, data_source_types as they are related to input
    st.session_state.theta_plots = {} # Reset plots
    # --- Reset AI Chat State ---
    # Keep the API key entered by user unless they clear it?
    # st.session_state.openai_api_key = None
    st.session_state.show_chat = False
    st.session_state.chat_history = []

# --- Sidebar Settings --- (Remove Chat Interface part) ---
st.sidebar.subheader("OpenAI 設定 (選用)")
api_key_input = st.sidebar.text_input(
    "輸入您的 OpenAI API Key 啟用 AI 問答：",
    type="password",
    key="openai_api_key_input", # Use a dedicated key
    value=st.session_state.get('openai_api_key', ''), # Load from state if exists
    help="輸入有效金鑰並成功完成分析後，下方將出現 AI 對話框。"
)

# Update session state when input changes
if api_key_input:
    st.session_state.openai_api_key = api_key_input
else:
    # Optionally clear the key if the input is cleared
    st.session_state.openai_api_key = None
    st.session_state.show_chat = False # Hide chat if key is removed
    st.session_state.chat_history = [] # Clear history if key is removed

# --- Activate Chat Logic (place this logically after analysis completion check) ---
# This check should ideally happen within the main app logic where diagnosis_complete is set
# Moved the activation logic to where diagnosis_complete is set

# --- (Removed Chat Display from Sidebar) ---

st.sidebar.divider() # Keep divider maybe?

# --- IRT Simulation Settings --- 
st.sidebar.subheader("IRT 模擬設定")
# Store initial thetas in session state to persist them
if 'initial_theta_q' not in st.session_state: st.session_state.initial_theta_q = 0.0
if 'initial_theta_v' not in st.session_state: st.session_state.initial_theta_v = 0.0
if 'initial_theta_di' not in st.session_state: st.session_state.initial_theta_di = 0.0

st.session_state.initial_theta_q = st.sidebar.number_input("Q 科目初始 Theta 估計", value=st.session_state.initial_theta_q, step=0.1, key="theta_q_input")
st.session_state.initial_theta_v = st.sidebar.number_input("V 科目初始 Theta 估計", value=st.session_state.initial_theta_v, step=0.1, key="theta_v_input")
st.session_state.initial_theta_di = st.sidebar.number_input("DI 科目初始 Theta 估計", value=st.session_state.initial_theta_di, step=0.1, key="theta_di_input")


# --- Main Page ---
st.title('GMAT 成績診斷平台')

# --- Data Input Section (Using Tabs and Refactored Function) ---
st.header("1. 上傳或貼上各科成績單")
st.info(f"提示：上傳的 CSV 檔案大小請勿超過 {MAX_FILE_SIZE_MB}MB。貼上的資料沒有此限制。")

tab_q, tab_v, tab_di = st.tabs(["Quantitative (Q)", "Verbal (V)", "Data Insights (DI)"])
tabs = {'Q': tab_q, 'V': tab_v, 'DI': tab_di}

# Process each subject tab using the refactored function
for subject in SUBJECTS:
    tab_container = tabs[subject]
    with tab_container:
        processed_df, source_type, warnings = process_subject_tab(subject, tab_container, BASE_RENAME_MAP)
        # Store results in session state immediately after processing each tab
        st.session_state.input_dfs[subject] = processed_df # Will be None if error/no data
        st.session_state.validation_errors[subject] = warnings
        if source_type:
             st.session_state.data_source_types[subject] = source_type


# --- Combine Input Data (After Tabs) ---
# Retrieve potentially updated DFs and errors from session state
input_dfs = st.session_state.input_dfs
validation_errors = st.session_state.validation_errors

# Filter out subjects where df is None (error, no data, or validation failed)
valid_input_dfs = {subj: df for subj, df in input_dfs.items() if df is not None}
loaded_subjects = list(valid_input_dfs.keys()) # Subjects with valid dataframes

df_combined_input = None
if len(valid_input_dfs) == len(SUBJECTS): # Only combine if ALL subjects are valid
    try:
        df_list = [valid_input_dfs[subj] for subj in SUBJECTS] # Ensure consistent order if needed
        df_combined_input = pd.concat(df_list, ignore_index=True)
        # Basic check after concat
        if df_combined_input.empty or 'question_position' not in df_combined_input.columns or df_combined_input['question_position'].isnull().any():
             st.error("合併後的資料為空或缺少有效的 'question_position'，無法繼續。")
             df_combined_input = None # Invalidate combination
    except Exception as e:
        st.error(f"合併已驗證的輸入資料時發生錯誤: {e}")
        df_combined_input = None

# --- Analysis Trigger Button ---
st.divider()

# Check if *any* validation errors occurred across all tabs
any_validation_errors = any(bool(warnings) for warnings in validation_errors.values())
all_subjects_loaded_and_valid = (len(valid_input_dfs) == len(SUBJECTS)) and (df_combined_input is not None)

# Determine button state
button_disabled = True
button_message = ""

if all_subjects_loaded_and_valid:
    button_disabled = False # Enable button
elif any_validation_errors:
    button_message = "部分科目數據驗證失敗，請修正上方標示的錯誤後再試。"
    st.error(button_message)
else: # Not all subjects loaded or combined DF failed
    subjects_actually_loaded = [subj for subj, df in input_dfs.items() if df is not None]
    missing_subjects = [subj for subj in SUBJECTS if subj not in subjects_actually_loaded]
    if missing_subjects:
         button_message = f"請確保已為 {'、'.join(missing_subjects)} 科目提供有效數據。"
         st.warning(button_message, icon="⚠️")
    elif not input_dfs: # No data attempted at all
         button_message = "請在上方分頁中為 Q, V, DI 三個科目上傳或貼上資料。"
         st.info(button_message)
    else: # All attempted, but maybe combination failed or validation error cleared?
         button_message = "請檢查所有科目的數據是否已成功加載且無誤。"
         st.warning(button_message, icon="⚠️")


# Display the button
if st.button("🔍 開始分析", type="primary", disabled=button_disabled, key="analyze_button"):
    if not button_disabled: # Extra check
        st.session_state.analysis_run = True
        # Reset previous analysis outputs
        st.session_state.diagnosis_complete = False
        st.session_state.report_dict = {}
        st.session_state.ai_summary = None
        st.session_state.final_thetas = {}
        st.session_state.processed_df = None # Clear previous processed data
        st.session_state.error_message = None
        st.rerun() # Rerun to enter the analysis block immediately
    # No 'else' needed, button is disabled if conditions aren't met

# --- Analysis Execution Block ---
# Use df_combined_input which is only non-None if all subjects were valid and combined successfully
if st.session_state.analysis_run and df_combined_input is not None and not st.session_state.diagnosis_complete:
    st.header("2. 執行 IRT 模擬與診斷")
    analysis_success = True # Flag to track overall success
    df_final_for_diagnosis = None # Initialize
    total_steps = 5 # Define the total number of major steps for the progress bar
    current_step = 0

    # Initialize progress bar and status text placeholder
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"步驟 {current_step}/{total_steps}: 準備開始分析...")

    # --- 1. Calculate Time Pressure ---
    time_pressure_map = {}
    try:
        current_step = 1
        status_text.text(f"步驟 {current_step}/{total_steps}: 計算時間壓力...")
        # Use helper constants directly by accessing the THRESHOLDS dictionary
        q_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'Q', 'question_time'], errors='coerce').sum()
        v_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'V', 'question_time'], errors='coerce').sum()
        di_total_time = pd.to_numeric(df_combined_input.loc[df_combined_input['Subject'] == 'DI', 'question_time'], errors='coerce').sum()

        # --- Q Time Pressure Calculation (Modified) ---
        q_df = df_combined_input[df_combined_input['Subject'] == 'Q'].copy()
        q_df['question_time'] = pd.to_numeric(q_df['question_time'], errors='coerce')
        q_df['question_position'] = pd.to_numeric(q_df['question_position'], errors='coerce') # Ensure numeric for sorting
        q_df = q_df.sort_values('question_position').dropna(subset=['question_position']) # Sort and remove NaNs

        time_diff_q = THRESHOLDS['Q']['MAX_ALLOWED_TIME'] - q_total_time
        time_diff_check = time_diff_q <= THRESHOLDS['Q']['TIME_DIFF_PRESSURE'] # Check time diff <= 3

        fast_end_questions_exist = False
        if not q_df.empty:
            total_q_questions = len(q_df)
            last_third_start_index = int(total_q_questions * 2 / 3) # Start index for last third
            # Select last third based on sorted position index
            last_third_q_df = q_df.iloc[last_third_start_index:]
            if not last_third_q_df.empty:
                # Check if any question time in the last third is < 1.0
                fast_end_questions_exist = (last_third_q_df['question_time'] < 1.0).any()

        # Combine conditions as per markdown
        time_pressure_q = time_diff_check and fast_end_questions_exist
        # --- End Q Time Pressure Modification ---

        time_pressure_v = (THRESHOLDS['V']['MAX_ALLOWED_TIME'] - v_total_time) < 1.0 # Keep V logic as is for now, might need its own threshold in THRESHOLDS
        time_pressure_di = (THRESHOLDS['DI']['MAX_ALLOWED_TIME'] - di_total_time) <= THRESHOLDS['DI']['TIME_PRESSURE_DIFF_MIN'] # Using DI pressure diff

        time_pressure_map = {'Q': time_pressure_q, 'V': time_pressure_v, 'DI': time_pressure_di}
        # st.write(f"時間壓力狀態: {time_pressure_map}") # Removed detailed write
        progress_bar.progress(current_step / total_steps)
    except Exception as e:
        st.error(f"計算時間壓力時出錯: {e}")
        analysis_success = False
        status_text.text(f"步驟 {current_step}/{total_steps}: 計算時間壓力時出錯。") # Update status on error

    # --- 2. Calculate Overtime ---
    df_with_overtime = None
    if analysis_success:
        try:
            current_step = 2
            status_text.text(f"步驟 {current_step}/{total_steps}: 計算超時狀態...")
            # Ensure df_combined_input has necessary columns ('question_time', 'question_type', 'Subject')
            # These should exist due to validation and standardization steps.
            # df_with_overtime = calculate_overtime(df_combined_input, time_pressure_map) # REMOVED CALL
            df_final_input_for_sim = df_combined_input # Use the combined input directly for simulation
            # st.write("超時狀態計算完成。") # Removed detailed write
            # Use this dataframe going forward, it includes the user-confirmed 'is_invalid' flag
            # df_final_input_for_sim = df_with_overtime # This line is no longer needed
            progress_bar.progress(current_step / total_steps)

        except Exception as e:
            st.error(f"計算 overtime 時出錯: {e}")
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 計算超時狀態時出錯。") # Update status on error

    # --- 3. IRT Simulation ---
    all_simulation_histories = {}
    final_thetas_local = {}
    all_theta_plots = {} # NEW: Store plots locally first
    question_banks = {} # Define banks here
    if analysis_success:
        # st.write("執行 IRT 模擬...") # Removed detailed write
        current_step = 3
        status_text.text(f"步驟 {current_step}/{total_steps}: 執行 IRT 模擬...")
        try:
            # Initialize banks
            # st.write("  初始化模擬題庫...") # Removed detailed write
            for subject in SUBJECTS:
                seed = RANDOM_SEED + SUBJECT_SIM_PARAMS[subject]['seed_offset']
                question_banks[subject] = irt.initialize_question_bank(BANK_SIZE, seed=seed)
                if question_banks[subject] is None:
                     raise ValueError(f"Failed to initialize question bank for {subject}")
            # st.write("  模擬題庫創建完成。") # Removed detailed write

            # Run simulation per subject
            for subject in SUBJECTS:
                # st.write(f"  執行 {subject} 科目模擬...") # Removed detailed write
                params = SUBJECT_SIM_PARAMS[subject]
                initial_theta = st.session_state[params['initial_theta_key']]
                bank = question_banks[subject]

                # Get user data for the subject, sorted by position
                user_df_subj = df_final_input_for_sim[df_final_input_for_sim['Subject'] == subject].sort_values(by='question_position')

                # --- Calculate total questions and wrong positions from user_df_subj --- #
                if user_df_subj.empty:
                    st.warning(f"  {subject}: 沒有找到該科目的作答數據，無法執行模擬。", icon="⚠️")
                    final_thetas_local[subject] = initial_theta
                    all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                    all_simulation_histories[subject].attrs['simulation_skipped'] = True
                    continue

                try:
                    total_questions_attempted = len(user_df_subj) # Correctly use the subject-specific dataframe length
                    if total_questions_attempted <= 0:
                        raise ValueError("Number of rows is not positive.")

                    # Calculate wrong positions from the subject-specific dataframe
                    if 'is_correct' not in user_df_subj.columns:
                        raise ValueError(f"{subject}: 缺少 'is_correct' 欄位。")
                    user_df_subj['is_correct'] = user_df_subj['is_correct'].astype(bool)
                    user_df_subj['question_position'] = pd.to_numeric(user_df_subj['question_position'], errors='coerce')
                    wrong_positions = user_df_subj.loc[(user_df_subj['is_correct'] == False) & user_df_subj['question_position'].notna(), 'question_position'].astype(int).tolist()

                    # st.write(f"    {subject}: 模擬全部 {total_questions_attempted} 個作答題目，其中錯誤位置: {wrong_positions}") # Removed detailed write

                except (KeyError, ValueError, TypeError) as e:
                     st.error(f"  {subject}: 無法確定總作答題數或錯誤位置: {e}。跳過模擬。", icon="🚨")
                     final_thetas_local[subject] = initial_theta
                     all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                     all_simulation_histories[subject].attrs['simulation_skipped'] = True
                     continue # Skip to next subject
                # --- End Calculation --- #

                # --- Filter valid responses for later difficulty assignment --- #
                valid_responses = user_df_subj[~user_df_subj['is_invalid']].copy()
                if valid_responses.empty:
                    st.warning(f"  {subject}: 所有題目均被標記為無效，Theta 模擬仍基於完整序列。", icon="⚠️")
                # --- End Filtering --- #

                # --- Run simulation using the calculated total and wrong list --- #
                history_df = irt.simulate_cat_exam(
                    question_bank=bank,
                    wrong_question_positions=wrong_positions,
                    initial_theta=initial_theta,
                    total_questions=total_questions_attempted # Pass the correct total number
                )
                # --- End Simulation Call --- #

                if history_df is not None and not history_df.empty:
                    # Store results only if simulation ran
                    all_simulation_histories[subject] = history_df
                    final_theta_subj = history_df['theta_est_after_answer'].iloc[-1]
                    final_thetas_local[subject] = final_theta_subj
                    # st.write(f"    {subject}: 模擬完成。最後 Theta 估計: {final_theta_subj:.3f}") # Removed detailed write

                    # --- Generate and store plot ---
                    try:
                        theta_plot = create_theta_plot(history_df, subject)
                        if theta_plot:
                            all_theta_plots[subject] = theta_plot
                            # st.write(f"    {subject}: Theta 歷史圖表已生成。") # Removed detailed write
                        else:
                            st.warning(f"    {subject}: 未能生成 Theta 圖表 (create_theta_plot 返回 None)。", icon="📊") # More specific warning
                    except Exception as plot_err:
                        st.warning(f"    {subject}: 生成 Theta 圖表時出錯: {plot_err}", icon="📊")
                    # --- End plot generation ---
                elif history_df is not None and history_df.empty: # Succeeded but empty
                    st.warning(f"  {subject}: 模擬執行但未產生歷史記錄。將使用初始 Theta。")
                    final_thetas_local[subject] = initial_theta
                    all_simulation_histories[subject] = pd.DataFrame(columns=['question_number', 'question_id', 'a', 'b', 'c', 'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'])
                    all_simulation_histories[subject].attrs['simulation_skipped'] = True # Mark skipped
                else: # Failed (returned None)
                     raise ValueError(f"IRT simulation failed for subject {subject}")
            # After loop completes successfully
            progress_bar.progress(current_step / total_steps)

        except Exception as e:
            st.error(f"執行 IRT 模擬時出錯: {e}")
            # st.code(traceback.format_exc()) # Optional debug
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: IRT 模擬時出錯。") # Update status on error

    # --- 4. Prepare Data for Diagnosis ---
    if analysis_success:
        # st.write("準備診斷數據...") # Removed detailed write
        current_step = 4
        status_text.text(f"步驟 {current_step}/{total_steps}: 準備診斷數據...")
        df_final_for_diagnosis_list = []
        try:
            for subject in SUBJECTS:
                # st.write(f"  處理 {subject} 科目...") # Removed detailed write
                user_df_subj = df_final_input_for_sim[df_final_input_for_sim['Subject'] == subject].copy()
                sim_history_df = all_simulation_histories.get(subject)
                final_theta = final_thetas_local.get(subject)

                if sim_history_df is None: # Should not happen if simulation ran/skipped correctly
                    st.error(f"找不到 {subject} 的模擬歷史，無法準備數據。")
                    analysis_success = False; break

                # Add final theta estimate to all rows for context
                user_df_subj['estimated_ability'] = final_theta

                # --- Assign Difficulty ---
                # Sort user data by position *before* filtering invalid
                user_df_subj_sorted = user_df_subj.sort_values(by='question_position').reset_index(drop=True)

                # Get simulated difficulties IF simulation was not skipped
                sim_b_values = []
                if not sim_history_df.attrs.get('simulation_skipped', False):
                      sim_b_values = sim_history_df['b'].tolist()

                # Create a mapping from valid question original position to its sim difficulty
                valid_indices = user_df_subj_sorted[~user_df_subj_sorted['is_invalid']].index
                if len(valid_indices) != len(sim_b_values):
                     st.warning(f"{subject}: 有效題目數量 ({len(valid_indices)}) 與模擬難度值數量 ({len(sim_b_values)}) 不符。難度可能分配不準確。", icon="⚠️")
                     # Truncate to minimum? Or assign NaN? Assign NaN for safety.
                     min_len = min(len(valid_indices), len(sim_b_values))
                     difficulty_map = {user_df_subj_sorted.loc[idx, 'question_position']: sim_b_values[i]
                                       for i, idx in enumerate(valid_indices[:min_len])}
                else:
                     difficulty_map = {user_df_subj_sorted.loc[idx, 'question_position']: sim_b_values[i]
                                       for i, idx in enumerate(valid_indices)}


                # Assign difficulty based on the map, assign NaN to invalid or unmapped questions
                user_df_subj_sorted['question_difficulty'] = user_df_subj_sorted['question_position'].map(difficulty_map)

                # Fill missing essential columns (content_domain, fundamental_skill) if they don't exist
                if 'content_domain' not in user_df_subj_sorted.columns:
                     user_df_subj_sorted['content_domain'] = 'Unknown Domain'
                if 'question_fundamental_skill' not in user_df_subj_sorted.columns:
                     user_df_subj_sorted['question_fundamental_skill'] = 'Unknown Skill'

                # Select and reorder columns needed for diagnosis functions
                cols_to_keep = [col for col in FINAL_DIAGNOSIS_INPUT_COLS if col in user_df_subj_sorted.columns]
                df_final_for_diagnosis_list.append(user_df_subj_sorted[cols_to_keep])

            if analysis_success and df_final_for_diagnosis_list: # Check again after loop
                 df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
                 # st.write("診斷數據準備完成。") # Removed detailed write
                 progress_bar.progress(current_step / total_steps)
            elif analysis_success: # List is empty but no error flagged?
                 st.warning("未能準備任何科目的診斷數據。")
                 analysis_success = False # Mark as failure if no data to diagnose
                 status_text.text(f"步驟 {current_step}/{total_steps}: 數據準備完成，但無數據可診斷。")


        except Exception as e:
            st.error(f"準備診斷數據時發生錯誤: {e}")
            # st.code(traceback.format_exc()) # Optional debug
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 準備診斷數據時出錯。") # Update status on error

    # --- 5. Run Diagnosis ---
    all_diagnosed_dfs = []
    if analysis_success and df_final_for_diagnosis is not None:
        # st.write("執行診斷分析...") # Removed detailed write
        current_step = 5
        status_text.text(f"步驟 {current_step}/{total_steps}: 執行診斷分析...")
        temp_report_dict = {} # Use temporary dict during run
        try:
             # Pre-calculate V average times if V is present
             v_avg_time_per_type = {}
             if 'V' in SUBJECTS:
                 df_v_temp = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == 'V']
                 if not df_v_temp.empty and 'question_time' in df_v_temp.columns and 'question_type' in df_v_temp.columns:
                      # Ensure time is numeric for calculation
                      df_v_temp['question_time'] = pd.to_numeric(df_v_temp['question_time'], errors='coerce')
                      # Filter out rows where time is NaN after conversion
                      v_avg_time_per_type = df_v_temp.dropna(subset=['question_time']).groupby('question_type')['question_time'].mean().to_dict()


             for subject in SUBJECTS:
                 # st.write(f"  診斷 {subject} 科...") # Removed detailed write
                 df_subj = df_final_for_diagnosis[df_final_for_diagnosis['Subject'] == subject].copy()
                 # --- Calculate Overtime for the subject AFTER potential filtering (assuming filtering happens before/in diagnosis funcs) ---
                 time_pressure_subj = time_pressure_map.get(subject, False)
                 try:
                     # Pass only the subject's data and its pressure status
                     # Need to pass df_subj which might be filtered by subsequent steps
                     # Let's assume run_q_diagnosis_processed etc. handle filtering *or* operate on non-filtered data where invalid is just a flag
                     # calculate_overtime needs the DataFrame for the specific subject.
                     # Create a mini-map for the current subject
                     current_subj_pressure_map = {subject: time_pressure_subj}
                     df_subj_with_overtime = calculate_overtime(df_subj, current_subj_pressure_map)
                     df_subj = df_subj_with_overtime # Replace df_subj

                     # === START DEBUG LOGGING ===
                     logging.info(f"[{subject}] Overtime calculated. Overtime count: {df_subj['overtime'].sum()}")
                     logging.info(f"[{subject}] df_subj head with overtime before diagnosis:\n{df_subj[['Subject', 'question_position', 'question_type', 'question_time', 'overtime']].head().to_string()}")
                     # === END DEBUG LOGGING ===

                 except Exception as overtime_calc_err:
                      st.error(f"  {subject}: 計算 Overtime 時出錯: {overtime_calc_err}")
                      # Decide how to proceed: skip subject? continue without overtime?
                      # Let's add a placeholder report and continue without diagnosis for this subject
                      temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n* 計算超時狀態時出錯: {overtime_calc_err}*\n"
                      all_diagnosed_dfs.append(df_subj) # Append original df without overtime/diagnosis
                      continue # Skip diagnosis for this subject
                 # --- End Overtime Calculation ---

                 # Fill NaN difficulties with a default (e.g., average ability) before diagnosis? Or handle in diagnostic funcs.
                 # Let's assume diagnostic functions can handle potential NaNs in difficulty for invalid items.
                 # If not, fill here:
                 # final_theta = final_thetas_local.get(subject, 0) # Get final theta
                 # df_subj['question_difficulty'].fillna(final_theta, inplace=True)

                 time_pressure = time_pressure_map.get(subject, False)
                 subj_results, subj_report, df_subj_diagnosed = None, None, None

                 try:
                     if subject == 'Q':
                         # Pass the df_subj which now includes the calculated 'overtime' column
                         subj_results, subj_report, df_subj_diagnosed = run_q_diagnosis_processed(df_subj, time_pressure)
                     elif subject == 'DI':
                         subj_results, subj_report, df_subj_diagnosed = run_di_diagnosis_processed(df_subj, time_pressure)
                     elif subject == 'V':
                         subj_results, subj_report, df_subj_diagnosed = run_v_diagnosis_processed(df_subj, time_pressure, v_avg_time_per_type)
                 except Exception as diag_err:
                      st.error(f"  {subject} 科診斷函數執行時出錯: {diag_err}")


                 if subj_report is not None and df_subj_diagnosed is not None:
                     # --- Attempt OpenAI Summarization --- #
                     final_report_for_subject = subj_report # Start with the original
                     # Retrieve api key (it's loaded near the top)
                     if st.session_state.openai_api_key and subj_report and "發生錯誤" not in subj_report and "未成功執行" not in subj_report:
                         # st.write(f"    嘗試使用 OpenAI 整理 {subject} 科報告...") # Removed detailed write
                         summarized_report = summarize_report_with_openai(subj_report, st.session_state.openai_api_key)
                         if summarized_report != subj_report: # Check if summarization actually changed something
                             # st.write(f"      -> {subject} 科報告已由 AI 整理。") # Removed detailed write
                             final_report_for_subject = summarized_report
                         # else: # No need to write anything if no change
                             # st.write(f"      -> {subject} 科報告整理失敗或無需整理。")
                     # elif not st.session_state.openai_api_key:
                          # st.info(f"    未提供 OpenAI API Key，跳過 {subject} 科報告整理。") # Removed, less verbose

                     temp_report_dict[subject] = final_report_for_subject # Store the final version
                     all_diagnosed_dfs.append(df_subj_diagnosed) # Append the diagnosed dataframe
                     # st.write(f"    {subject} 科診斷處理完成。") # Removed detailed write

                 else:
                     st.error(f"  {subject} 科診斷未返回預期結果。")
                     temp_report_dict[subject] = f"**{subject} 科診斷報告**\n\n* 診斷未成功執行或未返回結果。*\n"


             # Combine results *after* loop
             valid_diagnosed_dfs = [df for df in all_diagnosed_dfs if df is not None and not df.empty]
             if valid_diagnosed_dfs:
                  st.session_state.processed_df = pd.concat(valid_diagnosed_dfs, ignore_index=True)

                  # === START DEBUG LOGGING ===
                  logging.info("Concatenated diagnosed dfs. Final processed_df info:")
                  logging.info(f"Shape: {st.session_state.processed_df.shape}")
                  logging.info(f"Columns: {st.session_state.processed_df.columns.tolist()}")
                  if 'overtime' in st.session_state.processed_df.columns:
                      logging.info("Overtime counts per subject in final df:")
                      logging.info(st.session_state.processed_df.groupby('Subject')['overtime'].sum())
                      logging.info(f"Final df head with overtime:\n{st.session_state.processed_df[['Subject', 'question_position', 'question_type', 'question_time', 'overtime', 'time_performance_category', 'diagnostic_params_list']].head().to_string()}") # Added related columns
                  else:
                      logging.warning("Final processed_df is missing 'overtime' column after concatenation.")
                  # === END DEBUG LOGGING ===

                  st.session_state.report_dict = temp_report_dict
                  st.session_state.final_thetas = final_thetas_local # Store thetas from sim
                  st.session_state.theta_plots = all_theta_plots # NEW: Store the plots in session state
                  # st.write("所有科目診斷完成。") # Removed detailed write
                  progress_bar.progress(current_step / total_steps) # Mark final step complete
             else:
                  st.error("所有科目均未能成功診斷或無數據。")
                  st.session_state.processed_df = None # Ensure no stale data
                  st.session_state.report_dict = temp_report_dict # Still show error reports
                  st.session_state.theta_plots = {} # Clear plots
                  analysis_success = False
                  status_text.text(f"步驟 {current_step}/{total_steps}: 診斷完成，但無有效結果。")


        except Exception as e:
            st.error(f"診斷過程中發生未預期錯誤: {e}")
            # st.code(traceback.format_exc()) # Optional debug
            analysis_success = False
            status_text.text(f"步驟 {current_step}/{total_steps}: 執行診斷時出錯。") # Update status on error

    # --- Final Status Update ---
    # Use st.session_state.processed_df existence check directly
    if analysis_success and st.session_state.processed_df is not None:
         # analysis_status.update(label="分析成功完成！", state="complete", expanded=False) # Removed status block update
         status_text.text("分析成功完成！") # Update final status text
         st.session_state.diagnosis_complete = True # Mark diagnosis as done
         st.session_state.error_message = None
         st.balloons() # Celebrate success
    else:
         # analysis_status.update(label="分析過程中斷或失敗。", state="error", expanded=True) # Removed status block update
         # Error message already set in status_text during the step failure
         if analysis_success and st.session_state.processed_df is None:
             # Handle the case where analysis technically succeeded but produced no df
             status_text.error("分析完成但未產生有效數據，請檢查輸入或診斷邏輯。")
         elif not analysis_success:
              # If analysis failed earlier, the status_text should already reflect the error step
              # Optionally add a generic error message if it's still the default text
              if "準備開始分析" in status_text.text("") : # Check if it's still initial text
                  status_text.error("分析過程中斷或失敗，請檢查上方錯誤訊息。")

         st.session_state.diagnosis_complete = False # Ensure it's False on error
         st.session_state.error_message = "分析未能成功完成，請檢查上方錯誤訊息。"
         st.session_state.theta_plots = {} # Clear plots on error

    # Explicitly clear the progress bar maybe? Or leave it at 100% / error state.
    # Leaving it might be fine.


# --- Display Results Section ---
st.divider()
if st.session_state.analysis_run: # Only show results area if analysis was at least started
    st.header("📊 診斷結果")

    # --- Define Column Configuration and Excel Map ---
    # (Moved near the top as constants/config)
    COLUMN_DISPLAY_CONFIG = {
        "question_position": st.column_config.NumberColumn("題號", help="題目順序"),
        # "Subject": st.column_config.TextColumn("科目"), # Usually known from tab context
        "question_type": st.column_config.TextColumn("題型"),
        "content_domain": st.column_config.TextColumn("內容領域"), # Added back
        "question_fundamental_skill": st.column_config.TextColumn("考察能力"),
        "is_correct": st.column_config.CheckboxColumn("答對?", help="是否回答正確"),
        "question_difficulty": st.column_config.NumberColumn("難度(模擬)", help="系統模擬的題目難度 (有效題目)", format="%.2f", width="small"),
        # "estimated_ability": st.column_config.NumberColumn("能力估計", help="本科目最終能力估計值", format="%.2f", width="small"), # Add overall ability back (Removed)
        "question_time": st.column_config.NumberColumn("用時(分)", format="%.2f", width="small"),
        "time_performance_category": st.column_config.TextColumn("時間表現"),
        "is_sfe": st.column_config.CheckboxColumn("SFE?", help="是否為Special Focus Error", width="small"),
        "diagnostic_params_list": st.column_config.ListColumn("診斷標籤", help="初步診斷標籤", width="medium"),
        "is_invalid": st.column_config.CheckboxColumn("標記無效?", help="此題是否被標記為無效 (手動優先)", width="small"), # Show the final invalid flag
        # Internal columns for styling, set config to None to hide in st.dataframe
        "overtime": None,
        "is_manually_invalid": None, # Hide the intermediate manual flag
    }

    EXCEL_COLUMN_MAP = {
        "question_position": "題號",
        "Subject": "科目", # Keep subject in Excel export
        "question_type": "題型",
        "content_domain": "內容領域",
        "question_fundamental_skill": "考察能力",
        "is_correct": "答對", # Use text TRUE/FALSE (converted in display_subject_results)
        "question_difficulty": "難度(模擬)",
        # "estimated_ability": "能力估計", # Removed as per user request
        "question_time": "用時(分)",
        "time_performance_category": "時間表現",
        "is_sfe": "SFE", # Use text TRUE/FALSE
        "diagnostic_params_list": "診斷標籤",
        "is_invalid": "是否無效", # Use text TRUE/FALSE
        "overtime": "overtime_flag", # Internal flag for Excel styling, will be hidden by to_excel
    }

    if st.session_state.analysis_error:
        st.error(st.session_state.error_message)
    elif not st.session_state.diagnosis_complete:
        st.info("分析正在進行中或尚未完成。")
    elif st.session_state.processed_df is None or st.session_state.processed_df.empty:
        st.warning("診斷完成，但沒有可顯示的數據。")
        # Display any report messages even if df is empty (e.g., all invalid)
        if st.session_state.report_dict:
            st.subheader("診斷摘要")
            for subject, report_md in st.session_state.report_dict.items():
                st.markdown(f"### {subject} 科:")
                st.markdown(report_md, unsafe_allow_html=True)
    else:
        st.success("診斷分析已完成！")
        # --- Results Display Tabs --- #
        subjects_with_data = [subj for subj in SUBJECTS if subj in st.session_state.processed_df['Subject'].unique()]
        if not subjects_with_data:
            st.warning("處理後的數據中未找到任何有效科目。")
        else:
            # Create tabs for each subject with data
            result_tabs = st.tabs([f"{subj} 科結果" for subj in subjects_with_data])

            for i, subject in enumerate(subjects_with_data):
                subject_tab = result_tabs[i]
                with subject_tab:
                    df_subject = st.session_state.processed_df[st.session_state.processed_df['Subject'] == subject]
                    report_md = st.session_state.report_dict.get(subject, f"*未找到 {subject} 科的報告。*")
                    subject_excel_map = EXCEL_COLUMN_MAP
                    subject_col_config = COLUMN_DISPLAY_CONFIG

                    # --- 添加日誌調試 ---
                    # Removed logging block here
                    # --- 結束日誌調試 ---

                    # --- NEW: Display Theta Plot --- #
                    st.subheader(f"{subject} 科能力估計 (Theta) 走勢")
                    theta_plot = st.session_state.theta_plots.get(subject)
                    if theta_plot:
                        st.plotly_chart(theta_plot, use_container_width=True)
                    else:
                        # Access the original simulation history from run_analysis output if needed
                        # This might require passing all_simulation_histories to session state too,
                        # or recalculating the skipped status here.
                        # For simplicity, let's just check if the plot exists.
                        st.info(f"{subject} 科目的 Theta 估計圖表不可用。")
                    st.divider() # Add a separator
                    # --- End NEW --- #

                    display_subject_results(subject, subject_tab, report_md, df_subject, subject_col_config, subject_excel_map)

# --- AI Chat Interface (Moved to Main Page Bottom) ---
st.divider()

# Check conditions to show chat
if st.session_state.openai_api_key and st.session_state.diagnosis_complete:
    st.session_state.show_chat = True
else:
    st.session_state.show_chat = False
    
if st.session_state.show_chat:
    st.header("💬 與 AI 對話 (基於本次報告)")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input at the bottom of the main page
    if prompt := st.chat_input("針對報告和數據提問..."):
        # Add user message to history and display
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare context and call OpenAI
        with st.chat_message("assistant"):
            message_placeholder = st.empty() # Placeholder for streaming or waiting message
            message_placeholder.markdown("思考中...")
            try:
                # --- Prepare Context --- 
                report_context = _get_combined_report_context() 
                dataframe_context = _get_dataframe_context()
                # --- Call OpenAI --- 
                ai_response_text, response_id = _get_openai_response(
                    st.session_state.chat_history, 
                    report_context, 
                    dataframe_context
                )
                
                # Display AI response and add to history with response_id
                message_placeholder.markdown(ai_response_text)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": ai_response_text,
                    "response_id": response_id # Store the ID for the next turn
                })

            except Exception as e:
                error_message = f"呼叫 AI 時出錯: {e}"
                message_placeholder.error(error_message)
                # Add error message to history, without a response_id
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})

# --- End of Main Page --- 
# (Add any final footers or elements after the chat interface if needed)
