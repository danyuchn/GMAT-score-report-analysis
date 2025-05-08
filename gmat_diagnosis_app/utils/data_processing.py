"""
數據處理模組
提供數據處理的功能
"""

import io
import pandas as pd
import numpy as np
import re
import logging
import streamlit as st
from gmat_diagnosis_app.constants.config import BASE_RENAME_MAP

def process_subject_tab(subject, tab_container, base_rename_map, max_file_size_bytes, suggest_invalid_questions, validate_dataframe, required_original_cols):
    """Handles data input, cleaning, validation, and standardization for a subject tab."""
    subject_key = subject.lower()

    uploaded_file = tab_container.file_uploader(
        f"上傳 {subject} 科目 CSV 檔案",
        type="csv",
        key=f"{subject_key}_uploader",
        help=f"檔案大小限制為 {max_file_size_bytes // (1024*1024)}MB。"
    )
    pasted_data = tab_container.text_area(
        f"或將 {subject} 科目 Excel 資料貼在此處：",
        height=150,
        key=f"{subject_key}_paster"
    )

    # Display required headers
    req_cols_str = ", ".join(f"'{c}'" for c in required_original_cols.get(subject, []))
    tab_container.caption(f"請確保資料包含以下欄位標題 (大小寫/空格敏感): {req_cols_str}")

    temp_df = None
    source = None
    data_source_type = None
    validation_errors = []

    # Determine data source
    if uploaded_file is not None:
        if uploaded_file.size > max_file_size_bytes:
            tab_container.error(f"檔案大小 ({uploaded_file.size / (1024*1024):.2f} MB) 超過 {max_file_size_bytes // (1024*1024)}MB 限制。")
            return None, 'File Upload', [] # Return error state
        else:
            source = uploaded_file
            data_source_type = 'File Upload'
    elif pasted_data:
        source = io.StringIO(pasted_data) # Use io.StringIO
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
                         diff_threshold = 3.0 # Default threshold
                         if subject == 'Q': diff_threshold = 3.0
                         elif subject == 'DI': diff_threshold = 2.0
                         elif subject == 'V': diff_threshold = 3.0
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
                        # 使用替代方法處理NaN值，避免FutureWarning
                        temp_df['is_manually_invalid'] = processed_suggest_df['is_auto_suggested_invalid'].reindex(temp_df.index).replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False)
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
            final_df['is_manually_invalid'] = final_df['is_manually_invalid'].replace({pd.NA: False, None: False, np.nan: False}).infer_objects(copy=False).astype(bool)
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