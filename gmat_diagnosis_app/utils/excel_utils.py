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
    """Converts DataFrame to styled Excel bytes, hiding overtime flag."""
    output = io.BytesIO()
    df_copy = df.copy()
    
    # 根據Subject判斷是否需要移除question_fundamental_skill欄位（針對DI科目）
    subject = df_copy['Subject'].iloc[0] if 'Subject' in df_copy.columns and not df_copy.empty else None
    local_column_map = column_map.copy()
    
    # 如果是DI科目，從column_map中移除question_fundamental_skill
    if subject == 'DI' and 'question_fundamental_skill' in local_column_map:
        del local_column_map['question_fundamental_skill']

    # 在導出前，直接在時間列上添加超時標記，而不是依賴旗標列
    if 'overtime' in df_copy.columns and 'question_time' in df_copy.columns:
        # 將超時列的數據直接添加到主表的一個隱藏列中，這樣排序時會一起移動
        df_copy['_overtime_for_time'] = df_copy['overtime']

    # Select only columns present in the map keys and rename them
    columns_to_keep = [col for col in local_column_map.keys() if col in df_copy.columns]
    # 添加臨時超時標記列
    if '_overtime_for_time' in df_copy.columns:
        columns_to_keep.append('_overtime_for_time')

    df_renamed = df_copy[columns_to_keep].rename(columns=local_column_map)

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_renamed.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Define formats (Using global color constants here)
        error_format = workbook.add_format({'font_color': ERROR_FONT_COLOR})
        overtime_format = workbook.add_format({'font_color': OVERTIME_FONT_COLOR})
        invalid_format = workbook.add_format({'font_color': INVALID_FONT_COLOR})

        # 定義數值格式
        number_format = workbook.add_format({'num_format': '0.00'})

        # --- Apply Conditional Formatting ---
        header_list = list(df_renamed.columns)
        max_row = len(df_renamed) + 1
        try:
            # Find columns by *display* names (values in column_map)
            correct_col_disp = next(v for k, v in local_column_map.items() if k == 'is_correct')
            time_col_disp = next(v for k, v in local_column_map.items() if k == 'question_time')
            overtime_col_disp = next(v for k, v in local_column_map.items() if k == 'overtime') # Name of the overtime flag column
            invalid_col_disp = next(v for k, v in local_column_map.items() if k == 'is_invalid') # Name of the invalid flag column

            # 找到診斷標籤欄位的索引
            diagnostic_col_disp = next(v for k, v in local_column_map.items() if k == 'diagnostic_params_list')
            diagnostic_col_idx = header_list.index(diagnostic_col_disp)

            correct_col_idx = header_list.index(correct_col_disp)
            time_col_idx = header_list.index(time_col_disp)
            overtime_col_idx = header_list.index(overtime_col_disp)
            invalid_col_idx = header_list.index(invalid_col_disp)

            # 找到臨時超時標記列的索引
            _overtime_for_time_idx = header_list.index('_overtime_for_time') if '_overtime_for_time' in header_list else -1

            correct_col_letter = chr(ord('A') + correct_col_idx)
            time_col_letter = chr(ord('A') + time_col_idx)
            overtime_col_letter = chr(ord('A') + overtime_col_idx)
            invalid_col_letter = chr(ord('A') + invalid_col_idx)
            _overtime_for_time_letter = chr(ord('A') + _overtime_for_time_idx) if _overtime_for_time_idx >= 0 else None

            # 尋找難度欄位索引並設定數值格式
            try:
                difficulty_col_disp = next(v for k, v in local_column_map.items() if k == 'question_difficulty')
                difficulty_col_idx = header_list.index(difficulty_col_disp)
                # 設定難度欄位為數值格式
                worksheet.set_column(difficulty_col_idx, difficulty_col_idx, None, number_format)
            except (StopIteration, ValueError):
                pass  # 如果找不到難度欄位，跳過

            # 設定用時欄位為數值格式
            worksheet.set_column(time_col_idx, time_col_idx, None, number_format)

            # 確保每一行都有獨立的條件格式，並使用cell方式
            # 按指定優先順序處理條件格式（1.無效項灰色，2.錯題紅色，3.超時藍色）

            # 獨立處理每一行
            for row in range(2, max_row):
                # 計算當前行的範圍（整行）
                row_range = f'A{row}:{chr(ord("A") + len(header_list) - 1)}{row}'

                # 1. 當行的無效項標記為灰色（最高優先順序）
                worksheet.conditional_format(row_range, {
                    'type': 'formula',
                    'criteria': f'=${invalid_col_letter}{row}="True"',
                    'format': invalid_format
                })

                # 2. 當行的錯題標記為紅色（第二優先順序，僅當不是無效項時）
                worksheet.conditional_format(row_range, {
                    'type': 'formula',
                    'criteria': f'=AND(${correct_col_letter}{row}="False",${invalid_col_letter}{row}<>"True")',
                    'format': error_format
                })

                # 3. 直接使用與行綁定的超時標記，而不依賴overtime列
                if _overtime_for_time_letter:
                    worksheet.conditional_format(f'{time_col_letter}{row}', {
                        'type': 'formula',
                        'criteria': f'=${_overtime_for_time_letter}{row}=TRUE',
                        'format': overtime_format
                    })

            # Hide the overtime flag column and temporary overtime column
            worksheet.set_column(overtime_col_idx, overtime_col_idx, None, None, {'hidden': True})
            if _overtime_for_time_idx >= 0:
                worksheet.set_column(_overtime_for_time_idx, _overtime_for_time_idx, None, None, {'hidden': True})

            # 隱藏診斷標籤右側的所有欄位
            # 找出所有在診斷標籤右側的欄位並隱藏
            for col_idx in range(len(header_list)):
                # 診斷標籤右側的欄位
                if col_idx > diagnostic_col_idx:
                    # 跳過已經隱藏的列
                    if col_idx == overtime_col_idx or col_idx == _overtime_for_time_idx:
                        continue
                    worksheet.set_column(col_idx, col_idx, None, None, {'hidden': True})

        except (StopIteration, ValueError, IndexError) as e:
            import streamlit as st
            st.warning(f"無法應用 Excel 樣式或隱藏欄位: {e}", icon="⚠️") # Use warning

    processed_data = output.getvalue()
    return processed_data 