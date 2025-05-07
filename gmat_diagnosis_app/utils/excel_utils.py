"""
Excel 工具模組
提供Excel檔案生成和樣式應用的功能
"""

import io
import pandas as pd
import logging
import numpy as np
import streamlit as st

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
    
    # 為V科添加調試信息 (只在日誌中記錄)
    if subject == 'V':
        # 調試：輸出原始無效項值（在任何處理之前）
        if 'is_invalid' in df_copy.columns:
            logging.debug(f"V科原始is_invalid列值：\n{df_copy['is_invalid'].head(5)}")
            logging.debug(f"V科is_invalid列類型: {df_copy['is_invalid'].dtype}")
            # 顯示原始值分布
            try:
                value_counts = df_copy['is_invalid'].value_counts().to_dict()
                logging.debug(f"V科is_invalid原始值分布: {value_counts}")
            except Exception as e:
                logging.error(f"計算is_invalid值分布時出錯: {e}")
                
        # 強制轉換is_invalid為布爾值（避免任何可能的類型問題）
        if 'is_invalid' in df_copy.columns:
            # 首先使用fillna確保沒有缺失值
            df_copy['is_invalid'] = df_copy['is_invalid'].fillna(False)
            # 然後強制轉換為布爾值
            df_copy['is_invalid'] = df_copy['is_invalid'].astype(bool)
            # 再次檢查轉換後的值 (只在日誌中記錄)
            logging.debug(f"V科轉換後is_invalid列值：\n{df_copy['is_invalid'].head(5)}")
            value_counts = df_copy['is_invalid'].value_counts().to_dict()
            logging.debug(f"V科is_invalid轉換後值分布: {value_counts}")
    
        # 檢查是否有is_manually_invalid列，並顯示調試信息
        has_manually_invalid = 'is_manually_invalid' in df_copy.columns
        has_invalid = 'is_invalid' in df_copy.columns
        
        # 添加調試信息 (只在日誌中記錄)
        debug_info = f"V科：is_manually_invalid存在: {has_manually_invalid}, is_invalid存在: {has_invalid}"
        logging.debug(debug_info)
        
        if has_manually_invalid:
            manual_invalid_count = df_copy['is_manually_invalid'].sum()
            logging.debug(f"V科手動標記無效項數量: {manual_invalid_count}")
            
            # 重要修改：確保is_invalid完全以手動標記為準（Excel處理階段）
            if has_invalid:
                # 顯示原始is_invalid的數量
                orig_invalid_count = df_copy['is_invalid'].sum()
                
                # 重置is_invalid列（全部設為False）
                df_copy['is_invalid'] = False
                
                # 僅將手動標記的項設為無效
                df_copy.loc[df_copy['is_manually_invalid'] == True, 'is_invalid'] = True
                
                # 檢查重置後的無效項數量 (只在日誌中記錄)
                new_invalid_count = df_copy['is_invalid'].sum()
                logging.debug(f"V科僅使用手動標記後，無效項數量從 {orig_invalid_count} 變為 {new_invalid_count}")
                
                # 顯示is_manually_invalid為True的所有行的題號
                manually_invalid_rows = df_copy[df_copy['is_manually_invalid'] == True]
                if not manually_invalid_rows.empty:
                    manually_invalid_positions = manually_invalid_rows['question_position'].tolist()
                    logging.info(f"Excel處理階段檢測到手動標記的無效項 (題號): {manually_invalid_positions}")
                    
                    # 確認這些行的is_invalid也是True
                    for idx, row in manually_invalid_rows.iterrows():
                        if not row['is_invalid']:
                            logging.error(f"題號 {row['question_position']} 被手動標記為無效，但is_invalid為False！立即修正。")
                            # 強制修正
                            df_copy.at[idx, 'is_invalid'] = True
    
    # 如果是DI科目，從column_map中移除question_fundamental_skill
    if subject == 'DI' and 'question_fundamental_skill' in local_column_map:
        del local_column_map['question_fundamental_skill']

    # 在導出前，直接在時間列上添加超時標記，而不是依賴旗標列
    if 'overtime' in df_copy.columns and 'question_time' in df_copy.columns:
        # 將超時列的數據直接添加到主表的一個隱藏列中，這樣排序時會一起移動
        df_copy['_overtime_for_time'] = df_copy['overtime']

    # 確保無論如何都會導出is_invalid欄位
    if 'is_invalid' in df_copy.columns and 'is_invalid' not in local_column_map:
        local_column_map['is_invalid'] = '題目無效?'

    # 最後確認一次：is_invalid完全以手動標記為準
    if 'is_manually_invalid' in df_copy.columns and 'is_invalid' in df_copy.columns:
        # 重置is_invalid後再次設置
        df_copy['is_invalid'] = False
        df_copy.loc[df_copy['is_manually_invalid'] == True, 'is_invalid'] = True
        
        # 為V科再次添加調試信息
        if subject == 'V':
            if 'is_invalid' in df_copy.columns:
                invalid_count = df_copy['is_invalid'].sum()
                manual_count = df_copy['is_manually_invalid'].sum()
                logging.info(f"V科Excel最終確認：無效項數量: {invalid_count}，手動標記數量: {manual_count}")
                if invalid_count != manual_count:
                    logging.error(f"V科Excel警告：無效項數量與手動標記數量不一致！")
    
    # 所有V科數據的無效項檢查
    if subject == 'V':
        if 'is_invalid' in df_copy.columns:
            invalid_count = df_copy['is_invalid'].sum()
            logging.info(f"V科無效項數量: {invalid_count}")
            
            # 顯示所有列名以進行調試
            logging.info(f"V科原始數據列: {list(df_copy.columns)}")
            
            # 顯示Excel導出前的無效項數量
            logging.info(f"V科Excel導出前無效項數量: {invalid_count}")
            
            # 將is_invalid列轉換為文本，並檢查其值分布
            value_counts = df_copy['is_invalid'].astype(str).value_counts().to_dict()
            logging.info(f"V科is_invalid列轉換為文本後值分布: {value_counts}")
    
    # 檢查是否有本地列名映射
    if not local_column_map:
        df_excel = df_copy
    else:
        # 在進行列名映射之前，先進行列篩選 (如果映射中未提及的列將被丟棄)
        columns_to_keep = list(local_column_map.keys())
        # 加入可能額外需要的列 (不在map中但可能需要用於條件格式等)
        extra_cols = ['is_invalid', 'overtime', 'is_manually_invalid']
        for col in extra_cols:
            if col in df_copy.columns and col not in columns_to_keep:
                columns_to_keep.append(col)
        
        df_filtered = df_copy[columns_to_keep].copy()
        df_excel = df_filtered.rename(columns=local_column_map)
    
        # 顯示將要導出到Excel的列
        if subject == 'V':
            logging.info(f"V科Excel導出數據列: {list(df_excel.columns)}")
    
    # 新增：在寫入Excel前按題號排序
    if 'question_position' in df_excel.columns:
        df_excel = df_excel.sort_values(by='question_position').reset_index(drop=True)
    elif '題號' in df_excel.columns:  # 如果列已經被重命名
        df_excel = df_excel.sort_values(by='題號').reset_index(drop=True)

    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    sheet_name = f"{subject}" if subject else "Data"
    df_excel.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # --- Apply conditional formatting ---
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    header_list = list(df_excel.columns)
    
    # Define Excel formats
    correct_format = workbook.add_format({'bg_color': '#E6F6E6'})  # Light green background
    incorrect_format = workbook.add_format({'bg_color': '#FFF0F0'})  # Light pink/red background
    incorrect_text_format = workbook.add_format({'color': ERROR_FONT_COLOR})  # 紅色文字，用於錯誤答案
    overtime_format = workbook.add_format({'color': OVERTIME_FONT_COLOR, 'bold': True})  # Blue text
    invalid_format = workbook.add_format({'color': INVALID_FONT_COLOR})  # Dark gray text
    
    try:
        # Find columns by *display* names (values in column_map)
        correct_col_disp = next(v for k, v in local_column_map.items() if k == 'is_correct')
        time_col_disp = next(v for k, v in local_column_map.items() if k == 'question_time')
        overtime_col_disp = next(v for k, v in local_column_map.items() if k == 'overtime') # Name of the overtime flag column
        invalid_col_disp = None
        
        # 嘗試獲取無效項列名
        try:
            invalid_col_disp = next(v for k, v in local_column_map.items() if k == 'is_invalid')
        except StopIteration:
            # 無效項列可能不在映射中，使用默認名稱
            if 'is_invalid' in df_excel.columns:
                invalid_col_disp = 'is_invalid'
            elif '題目無效?' in df_excel.columns:
                invalid_col_disp = '題目無效?'
        
        # 找到診斷標籤欄位的索引
        diagnostic_col_disp = next(v for k, v in local_column_map.items() if k == 'diagnostic_params_list')
        diagnostic_col_idx = header_list.index(diagnostic_col_disp)

        correct_col_idx = header_list.index(correct_col_disp)
        time_col_idx = header_list.index(time_col_disp)
        invalid_col_idx = header_list.index(invalid_col_disp) if invalid_col_disp in header_list else None
        
        # 為V科添加特殊調試 - 顯示無效列索引
        if subject == 'V' and invalid_col_idx is not None:
            logging.info(f"V科無效列索引: {invalid_col_idx}, 列名: {invalid_col_disp}")
        
        # Convert column index to Excel column letter
        def get_column_letter(col_idx):
            """Convert zero-based column index to Excel column letter."""
            result = ''
            while col_idx >= 0:
                result = chr(65 + (col_idx % 26)) + result
                col_idx = col_idx // 26 - 1
            return result
        
        correct_col_letter = get_column_letter(correct_col_idx)
        time_col_letter = get_column_letter(time_col_idx)
        invalid_col_letter = get_column_letter(invalid_col_idx) if invalid_col_idx is not None else None
        
        # 為V科添加特殊調試 - 列出所有數據的is_invalid值
        if subject == 'V' and invalid_col_idx is not None:
            # 檢查無效項數據
            try:
                # 直接從DataFrame中獲取無效項值
                if 'is_invalid' in df_copy.columns:
                    invalid_values = df_copy['is_invalid'].astype(str).tolist()
                    logging.info(f"V科DataFrame中的無效項值: {invalid_values}")
            except Exception as e:
                logging.error(f"獲取V科無效項值時出錯: {e}")
            
            # 添加額外調試信息以確認條件格式化邏輯
            logging.info(f"V科Excel設置條件格式化 - 無效項列索引: {invalid_col_idx}, 列字母: {invalid_col_letter}")
        
        # 添加條件格式 - 正確/錯誤背景顏色
        worksheet.conditional_format(1, correct_col_idx, len(df_excel)+1, correct_col_idx, 
                                   {'type': 'text',
                                    'criteria': 'containing',
                                    'value': 'True',
                                    'format': correct_format})
        
        worksheet.conditional_format(1, correct_col_idx, len(df_excel)+1, correct_col_idx, 
                                   {'type': 'text',
                                    'criteria': 'containing',
                                    'value': 'False',
                                    'format': incorrect_format})
        
        # 新增：為錯誤答案的每一行應用紅色文字格式
        # 對每一列應用條件格式化
        for col in range(len(header_list)):
            if col != correct_col_idx:  # 跳過正確/錯誤列本身（它已經有背景色）
                col_letter = get_column_letter(col)
                worksheet.conditional_format(1, col, len(df_excel)+1, col, 
                                          {'type': 'formula',
                                           'criteria': f'={correct_col_letter}2="False"',
                                           'format': incorrect_text_format})
        
        # 添加完整的無效項條件格式
        if invalid_col_letter:
            # 使用文本條件匹配以適應各種TRUE值表示
            # 這可能是布爾值在Excel中的表示形式
            for row in range(1, len(df_excel) + 1):
                # 為所有行設置條件格式
                worksheet.conditional_format(
                    f"{invalid_col_letter}{row+1}", # +1因為Excel從1開始計數且第1行是標題
                    {'type': 'formula',
                     'criteria': f'=OR({invalid_col_letter}{row+1}=TRUE, {invalid_col_letter}{row+1}="TRUE", {invalid_col_letter}{row+1}="True", {invalid_col_letter}{row+1}="true")',
                     'format': invalid_format})
            
            # 全行條件格式（如果任何單元格中的is_invalid為true，則將整行設置為灰色）
            for row in range(1, len(df_excel) + 1):
                for col in range(len(header_list)):
                    if col != invalid_col_idx:  # 跳過無效列本身
                        col_letter = get_column_letter(col)
                        worksheet.conditional_format(
                            f"{col_letter}{row+1}",
                            {'type': 'formula',
                             'criteria': f'=OR({invalid_col_letter}{row+1}=TRUE, {invalid_col_letter}{row+1}="TRUE", {invalid_col_letter}{row+1}="True", {invalid_col_letter}{row+1}="true")',
                             'format': invalid_format})
        
        # 首先，添加AutoFilter以啟用篩選
        worksheet.autofilter(0, 0, len(df_excel), len(header_list) - 1)
        
        # 調整列寬
        for i, col in enumerate(df_excel.columns):
            max_len = max(
                df_excel[col].astype(str).map(len).max(),  # Max length of data
                len(str(col))  # Length of column name
            ) + 2  # Adding buffer
            
            # Cap column width at 50 for readability
            max_len = min(max_len, 50)
            
            # Convert to Excel column width
            worksheet.set_column(i, i, max_len)
            
    except Exception as e:
        logging.warning(f"應用Excel格式時出錯 ({sheet_name} 工作表): {e}", icon="⚠️")
    
    writer.close()
    return output.getvalue() 