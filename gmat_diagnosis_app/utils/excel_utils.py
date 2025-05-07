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
    
    # 處理DI科目（移除question_fundamental_skill欄位）
    if subject == 'DI' and 'question_fundamental_skill' in local_column_map:
        del local_column_map['question_fundamental_skill']
        
    # 處理無效項標記（確保一致性）
    if 'is_invalid' in df_copy.columns and 'is_manually_invalid' in df_copy.columns:
        # 以手動標記為準
        df_copy['is_invalid'] = df_copy['is_manually_invalid']
        logging.info(f"{subject}科：以手動標記為準設置無效項")
    
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
    
    # 根據題號排序
    if 'question_position' in df_excel.columns:
        df_excel = df_excel.sort_values(by='question_position').reset_index(drop=True)
    elif '題號' in df_excel.columns:
        df_excel = df_excel.sort_values(by='題號').reset_index(drop=True)
    
    # 轉換布爾值為字符串（更好的Excel兼容性）
    for col in ['is_correct', 'is_sfe', 'is_invalid', 'overtime']:
        if col in df_excel.columns:
            df_excel[col] = df_excel[col].astype(str)
    
    # 創建Excel writer
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    sheet_name = f"{subject}" if subject else "Data"
    
    # 預處理DataFrame中的NaN值
    for col in df_excel.columns:
        # 將NaN值替換為空字符串
        if df_excel[col].dtype != 'object' and pd.api.types.is_numeric_dtype(df_excel[col].dtype):
            df_excel[col] = df_excel[col].fillna(0)  # 數值列用0填充
        else:
            df_excel[col] = df_excel[col].fillna("")  # 其他列用空字符串填充
        
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
    time_col = None
    correct_col = None
    invalid_col = None
    overtime_col = None
    difficulty_col = None
    
    # 根據映射查找列名並獲取索引
    for orig_col, disp_col in local_column_map.items():
        if orig_col == 'question_time' and disp_col in header_list:
            time_col = get_col_index(disp_col)
        elif orig_col == 'is_correct' and disp_col in header_list:
            correct_col = get_col_index(disp_col)
        elif orig_col == 'is_invalid' and disp_col in header_list:
            invalid_col = get_col_index(disp_col)
        elif orig_col == 'overtime' and disp_col in header_list:
            overtime_col = get_col_index(disp_col)
        elif orig_col == 'question_difficulty' and disp_col in header_list:
            difficulty_col = get_col_index(disp_col)
    
    # 查找特殊隱藏列（用於條件格式）
    overtime_marker_col = get_col_index('_overtime_marker') if '_overtime_marker' in header_list else None
    
    # 獲取列字母
    time_col_letter = get_column_letter(time_col)
    correct_col_letter = get_column_letter(correct_col)
    invalid_col_letter = get_column_letter(invalid_col)
    overtime_col_letter = get_column_letter(overtime_col)
    overtime_marker_letter = get_column_letter(overtime_marker_col)
    
    # 查找超時列（優先使用_overtime_marker，其次是overtime）- 提前初始化以便在不同格式設定中使用
    overtime_col_name = None
    for col_name in header_list:
        if col_name == '_overtime_marker' or col_name == 'overtime':
            overtime_col_name = col_name
            break
    
    try:
        # 1. 設置難度列格式（兩位小數）
        if difficulty_col is not None:
            worksheet.set_column(difficulty_col, difficulty_col, None, difficulty_format)
        
        # 2. 應用正確/錯誤答案的背景色
        if correct_col is not None:
            # 正確答案（綠色背景）
            worksheet.conditional_format(1, correct_col, len(df_excel)+1, correct_col, 
                                       {'type': 'text',
                                        'criteria': 'containing',
                                        'value': 'True',
                                        'format': correct_format})
            
            # 錯誤答案（紅色背景）
            worksheet.conditional_format(1, correct_col, len(df_excel)+1, correct_col, 
                                       {'type': 'text',
                                        'criteria': 'containing',
                                        'value': 'False',
                                        'format': incorrect_format})
        
        # 3. 為無效項添加灰色文字（優先於錯誤的紅色文字）
        if invalid_col is not None:
            # 無效項列本身的格式
            worksheet.conditional_format(1, invalid_col, len(df_excel)+1, invalid_col, 
                                      {'type': 'text',
                                       'criteria': 'containing',
                                       'value': 'True',
                                       'format': invalid_format})
            
            # 直接為無效行應用格式（不使用條件格式）
            for row_idx in range(len(df_excel)):
                excel_row = row_idx + 2  # Excel從1開始 + 標題行
                # 檢查該行是否被標記為無效
                try:
                    is_invalid = str(df_excel.iloc[row_idx][header_list[invalid_col]]).lower() == 'true'
                    
                    if is_invalid:
                        # 為該行的每個單元格應用灰色文字格式（除了無效列本身）
                        for col_idx, col_name in enumerate(header_list):
                            # 跳過無效列本身以及時間列（如果已有超時標記）
                            skip_col = (col_idx == invalid_col) or (col_idx == time_col and 
                                       overtime_col_name is not None and 
                                       str(df_excel.iloc[row_idx][overtime_col_name]).lower() == 'true')
                            
                            if not skip_col:
                                col_letter = get_column_letter(col_idx)
                                cell_value = df_excel.iloc[row_idx][col_name]
                                
                                # 安全處理不同類型的值
                                try:
                                    # 處理列表類型（例如診斷參數列表）
                                    if isinstance(cell_value, list):
                                        cell_value = str(cell_value)
                                    # 處理NaN/None值
                                    elif pd.isna(cell_value):
                                        cell_value = ""
                                    # 寫入單元格
                                    worksheet.write(f"{col_letter}{excel_row}", cell_value, invalid_format)
                                except Exception as e:
                                    logging.debug(f"嘗試安全寫入單元格 ({col_name}, 行 {excel_row}), 值類型: {type(cell_value)}")
                                    try:
                                        # 如果原始值是數字但轉換失敗，嘗試寫入0
                                        if isinstance(cell_value, (int, float)) and not pd.isna(cell_value):
                                            worksheet.write_number(f"{col_letter}{excel_row}", 0, invalid_format)
                                        else:
                                            # 其他情況嘗試寫入空字符串
                                            worksheet.write_string(f"{col_letter}{excel_row}", "", invalid_format)
                                    except:
                                        worksheet.write_string(f"{col_letter}{excel_row}", "[無法顯示]", invalid_format)
                except Exception as e:
                    logging.error(f"應用無效項格式時出錯：{e}")
        
        # 4. 為錯誤答案行應用紅色文字（在無效項格式之後應用）
        if correct_col is not None:
            # 使用整行公式條件格式，對所有錯誤答案行應用紅色文字
            for row in range(1, len(df_excel) + 1):
                row_idx = row + 1  # 跳過標題行
                for col_idx in range(len(header_list)):
                    if col_idx != correct_col:  # 跳過正確/錯誤列本身
                        col_letter = get_column_letter(col_idx)
                        
                        # 檢查這個單元格是否屬於無效行，如果是就跳過紅色文字的應用
                        is_invalid_row = invalid_col is not None and row <= len(df_excel) and \
                                        str(df_excel.iloc[row-2][header_list[invalid_col]]).lower() == 'true'
                        
                        # 如果不是無效行，才應用紅色文字
                        if not is_invalid_row:
                            worksheet.conditional_format(
                                f"{col_letter}{row_idx}",
                                {'type': 'formula',
                                 'criteria': f'={correct_col_letter}{row_idx}="False"',
                                 'format': incorrect_text_format})
        
        # 5. 為超時項添加藍色文字（在時間列）
        if time_col is not None:
            if overtime_col_name is not None:
                # 為每一行單獨應用直接格式（不使用條件格式）
                for row_idx in range(len(df_excel)):
                    excel_row = row_idx + 2  # Excel從1開始 + 標題行
                    # 檢查該行是否超時
                    try:
                        is_overtime = str(df_excel.iloc[row_idx][overtime_col_name]).lower() == 'true'
                        if is_overtime:
                            # 獲取時間值
                            time_value = df_excel.iloc[row_idx][header_list[time_col]]
                            # 安全處理不同類型的值
                            try:
                                # 處理NaN/None值
                                if pd.isna(time_value):
                                    time_value = ""
                                # 寫入單元格
                                worksheet.write(f"{time_col_letter}{excel_row}", time_value, overtime_format)
                            except Exception as e:
                                logging.debug(f"嘗試安全寫入超時單元格 (行 {excel_row}), 值類型: {type(time_value)}")
                                try:
                                    # 如果原始值是數字但轉換失敗，嘗試寫入0
                                    if isinstance(time_value, (int, float)) and not pd.isna(time_value):
                                        worksheet.write_number(f"{time_col_letter}{excel_row}", 0, overtime_format)
                                    else:
                                        # 其他情況嘗試寫入空字符串
                                        worksheet.write_string(f"{time_col_letter}{excel_row}", "", overtime_format)
                                except:
                                    worksheet.write_string(f"{time_col_letter}{excel_row}", "[超時]", overtime_format)
                    except Exception as e:
                        logging.error(f"應用超時格式時出錯：{e}")
        
        # 6. 添加自動篩選
        worksheet.autofilter(0, 0, len(df_excel), len(header_list) - 1)
        
        # 7. 調整列寬
        for col_idx, col_name in enumerate(header_list):
            max_len = max(
                df_excel[col_name].astype(str).map(len).max() if not df_excel.empty else 0,
                len(str(col_name))
            ) + 2  # 添加緩衝
            
            # 限制最大寬度為50
            max_len = min(max_len, 50)
            worksheet.set_column(col_idx, col_idx, max_len)
    
    except Exception as e:
        logging.warning(f"應用Excel格式時出錯 ({sheet_name} 工作表): {e}")
    
    # 關閉writer並返回字節流
    writer.close()
    return output.getvalue() 