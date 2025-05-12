"""
Excel 工具模組
提供Excel檔案生成和樣式應用的功能
"""

import io
import pandas as pd
import logging
import numpy as np

from gmat_diagnosis_app.constants.config import (
    ERROR_FONT_COLOR, 
    OVERTIME_FONT_COLOR, 
    INVALID_FONT_COLOR
)

def to_excel(df, column_map):
    """
    將DataFrame轉換為Excel字節流，應用樣式和條件格式
    
    Args:
        df: 包含數據的DataFrame
        column_map: 欄位名稱映射字典
        
    Returns:
        bytes: Excel文件的字節流
    """
    # 創建輸出緩衝區
    output = io.BytesIO()
    df_copy = df.copy()
    
    # 獲取科目
    subject = df_copy['Subject'].iloc[0] if 'Subject' in df_copy.columns and not df_copy.empty else None
    local_column_map = column_map.copy()
    
    # 處理數值格式
    if 'question_difficulty' in df_copy.columns:
        df_copy['question_difficulty'] = df_copy['question_difficulty'].apply(
            lambda x: round(float(x), 2) if pd.notnull(x) else x
        )
    
    # 確保overtime列被保留用於條件格式
    if 'overtime' in df_copy.columns:
        df_copy['_overtime_marker'] = df_copy['overtime']
    
    # 篩選和重命名列
    if local_column_map:
        # 選擇要保留的列
        columns_to_keep = list(local_column_map.keys())
        
        # 添加額外需要但不顯示的列（用於條件格式）
        extra_cols = ['is_invalid', 'overtime', 'is_manually_invalid', '_overtime_marker']
        for col in extra_cols:
            if col in df_copy.columns and col not in columns_to_keep:
                columns_to_keep.append(col)
        
        # 過濾和重命名列
        df_excel = df_copy[columns_to_keep].rename(columns=local_column_map)
    else:
        df_excel = df_copy
    
    # 記錄篩選後的無效項數據
    if 'is_invalid' in df_excel.columns:
        invalid_type = df_excel['is_invalid'].dtype
        invalid_sum = 0
        try:
            if df_excel['is_invalid'].dtype == 'object' or df_excel['is_invalid'].dtype == 'str':
                invalid_sum = (df_excel['is_invalid'] == 'True').sum()
            else:
                invalid_sum = df_excel['is_invalid'].sum()
        except Exception as e:
            invalid_sum = "無法計算"
    
    # 根據題號排序
    if 'question_position' in df_excel.columns:
        df_excel = df_excel.sort_values(by='question_position').reset_index(drop=True)
    elif '題號' in df_excel.columns:
        df_excel = df_excel.sort_values(by='題號').reset_index(drop=True)
    
    # 轉換布爾值為字符串（更好的Excel兼容性）
    boolean_cols_original_names = ['is_correct', 'is_sfe', 'is_invalid', 'overtime', 'is_manually_invalid']
    for original_name in boolean_cols_original_names:
        # Get the column name as it actually appears in df_excel (it might have been renamed)
        current_name_in_df_excel = local_column_map.get(original_name, original_name)
        
        if current_name_in_df_excel in df_excel.columns:
            # Original logging/debugging logic for 'is_invalid' can be kept, using current_name_in_df_excel for data access
            pre_convert_value = None
            try:
                if original_name == 'is_invalid': # Check based on the original intent of the column
                    # Access data using current_name_in_df_excel
                    pre_convert_value = df_excel[current_name_in_df_excel].sum() if hasattr(df_excel[current_name_in_df_excel], 'sum') else "無法計算"
            except Exception as e:
                pass # Original code had commented out logging here
                
            df_excel[current_name_in_df_excel] = df_excel[current_name_in_df_excel].astype(str)
            
            post_convert_value = None
            try:
                if original_name == 'is_invalid': # Check based on the original intent of the column
                    # Access data using current_name_in_df_excel
                    post_convert_value = (df_excel[current_name_in_df_excel] == 'True').sum()
            except Exception as e:
                pass # Original code had commented out logging here
    
    # 創建Excel writer
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    sheet_name = f"{subject}" if subject else "Data"
    
    # 預處理DataFrame中的NaN值
    with pd.option_context('future.no_silent_downcasting', True):
        for col in df_excel.columns:
            # 將NaN值替換為空字符串
            if df_excel[col].dtype != 'object' and pd.api.types.is_numeric_dtype(df_excel[col].dtype):
                # 使用with context方式避免FutureWarning
                df_excel[col] = df_excel[col].replace({pd.NA: 0, None: 0, np.nan: 0})
            else:
                # 使用with context方式避免FutureWarning
                df_excel[col] = df_excel[col].replace({pd.NA: "", None: "", np.nan: ""})
            
            # 允許推斷更合適的類型
            df_excel[col] = df_excel[col].infer_objects(copy=False)
            
            # 將列表類型的值轉換為字符串
            if any(isinstance(x, list) for x in df_excel[col].dropna()):
                df_excel[col] = df_excel[col].apply(lambda x: str(x) if isinstance(x, list) else x)
    
    # 寫入數據
    df_excel.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # 獲取workbook和worksheet對象
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    # 定義格式
    correct_format = workbook.add_format({'bg_color': '#E6F6E6'})  # 淺綠色背景（正確）
    incorrect_format = workbook.add_format({'bg_color': '#FFF0F0'})  # 淺紅色背景（錯誤）
    incorrect_text_format = workbook.add_format({'color': ERROR_FONT_COLOR})  # 紅色文字（錯誤）
    overtime_format = workbook.add_format({'color': OVERTIME_FONT_COLOR, 'bold': True})  # 藍色文字（超時）
    invalid_format = workbook.add_format({'color': INVALID_FONT_COLOR})  # 深灰色文字（無效項）
    difficulty_format = workbook.add_format({'num_format': '0.00'})  # 難度格式（兩位小數）
    time_format = workbook.add_format({'num_format': '0.00'})  # 用時格式（兩位小數）
    
    # 獲取列名列表和必要的欄位索引
    header_list = list(df_excel.columns)
    
    # 定義列索引映射函數
    def get_col_index(col_name):
        try:
            return header_list.index(col_name)
        except ValueError:
            return None
    
    # 定義列字母獲取函數
    def get_column_letter(col_idx):
        """將基於0的列索引轉換為Excel列字母。"""
        if col_idx is None:
            return None
        result = ''
        while col_idx >= 0:
            result = chr(65 + (col_idx % 26)) + result
            col_idx = col_idx // 26 - 1
        return result
    
    # 獲取各欄位的列索引
    time_col_idx = get_col_index(local_column_map.get('question_time'))
    correct_col_idx = get_col_index(local_column_map.get('is_correct'))
    invalid_col_idx = get_col_index(local_column_map.get('is_invalid'))
    manually_invalid_col_idx = get_col_index(local_column_map.get('is_manually_invalid'))
    overtime_col_idx = get_col_index(local_column_map.get('overtime'))
    difficulty_col_idx = get_col_index(local_column_map.get('question_difficulty'))
    
    # 應用條件格式
    for row_num in range(len(df_excel)):
        # 檢查是否為無效項（優先使用 is_manually_invalid）
        is_invalid_row = False
        if manually_invalid_col_idx is not None and df_excel.iloc[row_num, manually_invalid_col_idx] == 'True':
            is_invalid_row = True
        elif invalid_col_idx is not None and df_excel.iloc[row_num, invalid_col_idx] == 'True':
            is_invalid_row = True
        
        if is_invalid_row:
            q_pos_excel = df_excel.iloc[row_num, get_col_index(local_column_map.get('question_position', 'question_position'))] if get_col_index(local_column_map.get('question_position', 'question_position')) is not None else "未知"
            worksheet.set_row(row_num + 1, None, invalid_format) # +1 because Excel rows are 1-based and we skip the header
            continue # 無效項不再應用其他格式
        
        # 應用正確/錯誤格式
        if correct_col_idx is not None:
            is_correct_value = df_excel.iloc[row_num, correct_col_idx] == 'True'
            if is_correct_value:
                # worksheet.set_row(row_num + 1, None, correct_format) # +1 because Excel rows are 1-based # MODIFIED: Commented out to remove green background for correct answers
                pass # No background format needed for correct answers
            else:
                worksheet.set_row(row_num + 1, None, incorrect_format) # +1 because Excel rows are 1-based
                
                # 對錯誤題目應用紅色文字
                for col_idx in range(len(header_list)):
                    worksheet.write(row_num + 1, col_idx, df_excel.iloc[row_num, col_idx], incorrect_text_format)
        
        # 應用超時格式（僅應用於「用時」欄位）
        if time_col_idx is not None and overtime_col_idx is not None:
            is_overtime_value = df_excel.iloc[row_num, overtime_col_idx] == 'True'
            if is_overtime_value:
                worksheet.write(row_num + 1, time_col_idx, df_excel.iloc[row_num, time_col_idx], overtime_format)
    
    # 記錄處理的無效行數
    invalid_processed_count = 0
    if manually_invalid_col_idx is not None:
        invalid_processed_count = (df_excel.iloc[:, manually_invalid_col_idx] == 'True').sum()
    elif invalid_col_idx is not None:
         invalid_processed_count = (df_excel.iloc[:, invalid_col_idx] == 'True').sum()
    
    # 應用難度數字格式
    if difficulty_col_idx is not None:
        difficulty_col_letter = get_column_letter(difficulty_col_idx)
        if difficulty_col_letter:
            worksheet.set_column(f'{difficulty_col_letter}:{difficulty_col_letter}', None, difficulty_format)
            
    # 應用用時數字格式
    if time_col_idx is not None:
        time_col_letter = get_column_letter(time_col_idx)
        if time_col_letter:
            worksheet.set_column(f'{time_col_letter}:{time_col_letter}', None, time_format)
    
    # 調整列寬
    for i, col in enumerate(header_list):
        # 移除不希望用戶看到的內部標記列
        if col in ['is_invalid', 'overtime', 'is_manually_invalid', '_overtime_marker']:
            worksheet.set_column(i, i, None, None, {'hidden': True})
            continue
            
        column_len = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2 # 加2給予一些緩衝
        worksheet.set_column(i, i, column_len)
    
    # 保存Excel文件
    writer.close()
    output.seek(0)
    
    return output.getvalue() 