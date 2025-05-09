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
    
    # 打印中間處理結果（特別是對DI科目）
    if subject == 'DI':
        print(f"\n----- DEBUG: Excel生成開始，科目={subject} -----")
        print(f"數據行數: {len(df_copy)}")
        if 'is_invalid' in df_copy.columns:
            invalid_count = (df_copy['is_invalid'] == 'True').sum()
            print(f"is_invalid='True'的行數: {invalid_count}")
            print(f"is_invalid數據類型: {df_copy['is_invalid'].dtype}")
            print(f"is_invalid值分佈: {df_copy['is_invalid'].value_counts().to_dict()}")
        if 'is_manually_invalid' in df_copy.columns:
            manual_invalid_count = (df_copy['is_manually_invalid'] == 'True').sum()
            print(f"is_manually_invalid='True'的行數: {manual_invalid_count}")
    
    # 調試信息：進入to_excel函數
    logging.info(f"【to_excel調試】進入to_excel函數，科目: {subject}，數據行數: {len(df_copy)}")
    
    # 檢查無效項數據
    if 'is_invalid' in df_copy.columns:
        invalid_type = df_copy['is_invalid'].dtype
        invalid_sum = 0
        try:
            if df_copy['is_invalid'].dtype == 'object' or df_copy['is_invalid'].dtype == 'str':
                invalid_sum = (df_copy['is_invalid'] == 'True').sum()
            else:
                invalid_sum = df_copy['is_invalid'].sum()
        except:
            invalid_sum = "無法計算"
        logging.info(f"【to_excel調試】{subject}科接收到的is_invalid數據類型: {invalid_type}，True的行數: {invalid_sum}")
    
    if 'is_manually_invalid' in df_copy.columns:
        manual_invalid_type = df_copy['is_manually_invalid'].dtype
        manual_invalid_sum = 0
        try:
            if df_copy['is_manually_invalid'].dtype == 'object' or df_copy['is_manually_invalid'].dtype == 'str':
                manual_invalid_sum = (df_copy['is_manually_invalid'] == 'True').sum()
            else:
                manual_invalid_sum = df_copy['is_manually_invalid'].sum()
        except:
            manual_invalid_sum = "無法計算"
        logging.info(f"【to_excel調試】{subject}科接收到的is_manually_invalid數據類型: {manual_invalid_type}，True的行數: {manual_invalid_sum}")
    
    # 處理DI科目（移除question_fundamental_skill欄位）
    if subject == 'DI' and 'question_fundamental_skill' in local_column_map:
        del local_column_map['question_fundamental_skill']
        logging.info(f"【to_excel調試】{subject}科特殊處理：移除question_fundamental_skill欄位")
    
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
        except:
            invalid_sum = "無法計算"
        logging.info(f"【to_excel調試】{subject}科列篩選後的is_invalid數據類型: {invalid_type}，True的行數: {invalid_sum}")
        
        # 打印篩選後的結果（特別是對DI科目）
        if subject == 'DI':
            print(f"\n----- DEBUG: 列篩選後，科目={subject} -----")
            print(f"is_invalid數據類型: {invalid_type}")
            print(f"is_invalid=True/True的行數: {invalid_sum}")
    
    # 根據題號排序
    if 'question_position' in df_excel.columns:
        df_excel = df_excel.sort_values(by='question_position').reset_index(drop=True)
    elif '題號' in df_excel.columns:
        df_excel = df_excel.sort_values(by='題號').reset_index(drop=True)
    
    # 轉換布爾值為字符串（更好的Excel兼容性）
    for col in ['is_correct', 'is_sfe', 'is_invalid', 'overtime', 'is_manually_invalid']:
        if col in df_excel.columns:
            pre_convert_value = None
            try:
                if col == 'is_invalid':
                    pre_convert_value = df_excel[col].sum() if hasattr(df_excel[col], 'sum') else "無法計算"
                    logging.info(f"【to_excel調試】{subject}科轉換{col}為字符串前，True的行數: {pre_convert_value}")
            except:
                pass
                
            df_excel[col] = df_excel[col].astype(str)
            
            post_convert_value = None
            try:
                if col == 'is_invalid':
                    post_convert_value = (df_excel[col] == 'True').sum()
                    logging.info(f"【to_excel調試】{subject}科轉換{col}為字符串後，'True'的行數: {post_convert_value}")
                    
                    # 打印轉換後的結果（特別是對DI科目）
                    if subject == 'DI':
                        print(f"\n----- DEBUG: 轉換{col}為字符串後，科目={subject} -----")
                        print(f"{col}='True'的行數: {post_convert_value}")
                        print(f"{col}值分佈: {df_excel[col].value_counts().to_dict()}")
                    
                    # 檢查每個被標記為True的行
                    if post_convert_value > 0:
                        true_rows = df_excel[df_excel[col] == 'True']
                        for idx, row in true_rows.iterrows():
                            q_pos = row['question_position'] if 'question_position' in row else "未知"
                            logging.info(f"【to_excel調試】{subject}科第{idx}行(題號{q_pos})的{col}為'True'")
                            
                            # 打印具體無效項（特別是對DI科目）
                            if subject == 'DI' and col == 'is_invalid':
                                print(f"題號{q_pos}被標記為{col}='True'")
            except:
                pass
    
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
    manually_invalid_col = None
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
        elif orig_col == 'is_manually_invalid' and disp_col in header_list:
            manually_invalid_col = get_col_index(disp_col)
        elif orig_col == 'overtime' and disp_col in header_list:
            overtime_col = get_col_index(disp_col)
        elif orig_col == 'question_difficulty' and disp_col in header_list:
            difficulty_col = get_col_index(disp_col)
    
    # 記錄欄位索引
    logging.info(f"【to_excel調試】{subject}科欄位索引 - is_invalid: {invalid_col}, is_manually_invalid: {manually_invalid_col}")
    
    # 打印欄位索引（特別是對DI科目）
    if subject == 'DI':
        print(f"\n----- DEBUG: 欄位索引，科目={subject} -----")
        print(f"is_invalid列索引: {invalid_col}")
        print(f"is_manually_invalid列索引: {manually_invalid_col}")
        print(f"列標題: {header_list}")
    
    # 查找特殊隱藏列（用於條件格式）
    overtime_marker_col = get_col_index('_overtime_marker') if '_overtime_marker' in header_list else None
    
    # 獲取列字母
    time_col_letter = get_column_letter(time_col)
    correct_col_letter = get_column_letter(correct_col)
    invalid_col_letter = get_column_letter(invalid_col)
    manually_invalid_col_letter = get_column_letter(manually_invalid_col)
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
        
        # 3. 以styling.py中的優先級順序處理樣式:
        
        # 3.1 首先處理超時單元格（藍色文字）- 第一優先級
        if time_col is not None and overtime_col_name is not None:
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
        
        # 3.2 接著處理錯誤答案（紅色文字）- 第二優先級
        if correct_col is not None:
            for row_idx in range(len(df_excel)):
                excel_row = row_idx + 2  # Excel從1開始 + 標題行
                try:
                    is_correct = str(df_excel.iloc[row_idx][header_list[correct_col]]).lower() == 'true'
                    if not is_correct:
                        # 為錯誤行的每個單元格應用紅色文字（除了超時列）
                        for col_idx, col_name in enumerate(header_list):
                            # 跳過超時的時間列
                            skip_col = (col_idx == time_col and 
                                      overtime_col_name is not None and 
                                      str(df_excel.iloc[row_idx][overtime_col_name]).lower() == 'true')
                            
                            if not skip_col:
                                col_letter = get_column_letter(col_idx)
                                cell_value = df_excel.iloc[row_idx][col_name]
                                
                                # 安全處理不同類型的值
                                try:
                                    # 處理列表類型
                                    if isinstance(cell_value, list):
                                        cell_value = str(cell_value)
                                    # 處理NaN/None值
                                    elif pd.isna(cell_value):
                                        cell_value = ""
                                    # 寫入單元格
                                    worksheet.write(f"{col_letter}{excel_row}", cell_value, incorrect_text_format)
                                except Exception as e:
                                    logging.debug(f"嘗試安全寫入錯誤單元格 ({col_name}, 行 {excel_row}), 值類型: {type(cell_value)}")
                                    try:
                                        # 嘗試處理特殊情況
                                        if isinstance(cell_value, (int, float)) and not pd.isna(cell_value):
                                            worksheet.write_number(f"{col_letter}{excel_row}", cell_value, incorrect_text_format)
                                        else:
                                            worksheet.write_string(f"{col_letter}{excel_row}", str(cell_value), incorrect_text_format)
                                    except:
                                        worksheet.write_string(f"{col_letter}{excel_row}", "[無法顯示]", incorrect_text_format)
                except Exception as e:
                    logging.error(f"應用錯誤項格式時出錯：{e}")
        
        # 3.3 最後處理無效項（灰色文字）- 第三優先級，會覆蓋前面的樣式
        # 首先檢查 is_invalid，如果存在且為 true，則顯示灰色；如果不存在，才考慮 is_manually_invalid
        invalid_rows_count = 0
        for row_idx in range(len(df_excel)):
            excel_row = row_idx + 2  # Excel從1開始 + 標題行
            try:
                # 首先檢查 is_invalid（results_display.py已經將手動標記轉移到這裡）
                is_row_invalid = False
                
                # 1. 首先檢查 is_invalid
                if invalid_col is not None:
                    is_inv_str = str(df_excel.iloc[row_idx][header_list[invalid_col]]).lower()
                    is_row_invalid = is_inv_str == 'true'
                    logging.debug(f"【to_excel調試】{subject}科第{row_idx}行，is_invalid值: '{is_inv_str}'，判定結果: {is_row_invalid}")
                    
                    # 打印每行的is_invalid值和判定結果（特別是對DI科目）
                    if subject == 'DI':
                        q_pos = df_excel.iloc[row_idx]['question_position'] if 'question_position' in df_excel.columns else row_idx
                        print(f"行{row_idx+1}(題號{q_pos}) - is_invalid值: '{is_inv_str}'，判定結果: {is_row_invalid}")
                
                # 2. 如果 is_invalid 不是 true，再檢查 is_manually_invalid
                if not is_row_invalid and manually_invalid_col is not None:
                    is_man_inv_str = str(df_excel.iloc[row_idx][header_list[manually_invalid_col]]).lower()
                    is_row_invalid = is_man_inv_str == 'true'
                    logging.debug(f"【to_excel調試】{subject}科第{row_idx}行，is_manually_invalid值: '{is_man_inv_str}'，判定結果: {is_row_invalid}")
                
                # 輸出調試信息，檢查哪些行被標記為無效
                if is_row_invalid:
                    invalid_rows_count += 1
                    q_pos = "未知"
                    if 'question_position' in df_excel.columns:
                        pos_col_idx = df_excel.columns.get_loc('question_position')
                        q_pos = df_excel.iloc[row_idx, pos_col_idx]
                    logging.info(f"【to_excel調試】{subject}科第 {row_idx+1} 行(題號{q_pos})被標記為無效項，將應用灰色文字")
                    
                    # 打印被標記為無效的行（特別是對DI科目）
                    if subject == 'DI':
                        print(f"⚠️ 第{row_idx+1}行(題號{q_pos})被標記為無效項，將應用灰色文字")
                
                if is_row_invalid:
                    # 為無效行的每個單元格應用灰色文字（除了超時列）
                    for col_idx, col_name in enumerate(header_list):
                        # 跳過超時的時間列
                        skip_col = (col_idx == time_col and 
                                  overtime_col_name is not None and 
                                  str(df_excel.iloc[row_idx][overtime_col_name]).lower() == 'true')
                        
                        if not skip_col:
                            col_letter = get_column_letter(col_idx)
                            cell_value = df_excel.iloc[row_idx][col_name]
                            
                            # 安全處理不同類型的值
                            try:
                                # 處理列表類型
                                if isinstance(cell_value, list):
                                    cell_value = str(cell_value)
                                # 處理NaN/None值
                                elif pd.isna(cell_value):
                                    cell_value = ""
                                # 寫入單元格
                                worksheet.write(f"{col_letter}{excel_row}", cell_value, invalid_format)
                            except Exception as e:
                                logging.debug(f"嘗試安全寫入無效單元格 ({col_name}, 行 {excel_row}), 值類型: {type(cell_value)}")
                                try:
                                    # 嘗試處理特殊情況
                                    if isinstance(cell_value, (int, float)) and not pd.isna(cell_value):
                                        worksheet.write_number(f"{col_letter}{excel_row}", cell_value, invalid_format)
                                    else:
                                        worksheet.write_string(f"{col_letter}{excel_row}", str(cell_value), invalid_format)
                                except:
                                    worksheet.write_string(f"{col_letter}{excel_row}", "[無法顯示]", invalid_format)
            except Exception as e:
                logging.error(f"應用無效項格式時出錯：{e}")
        
        logging.info(f"【to_excel調試】{subject}科總共發現並處理了 {invalid_rows_count} 個無效行")
        
        # 打印最終處理結果（特別是對DI科目）
        if subject == 'DI':
            print(f"\n----- DEBUG: 最終處理結果，科目={subject} -----")
            print(f"總共處理了 {invalid_rows_count} 個無效行")
        
        # 4. 添加自動篩選
        worksheet.autofilter(0, 0, len(df_excel), len(header_list) - 1)
        
        # 5. 調整列寬
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
        if subject == 'DI':
            print(f"⚠️ 應用Excel格式時出錯: {e}")
    
    # 關閉writer並返回字節流
    writer.close()
    logging.info(f"【to_excel調試】{subject}科Excel生成完成")
    if subject == 'DI':
        print("----- DEBUG: Excel生成完成 -----")
    return output.getvalue() 