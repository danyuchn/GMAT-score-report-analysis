"""
樣式工具模組
提供資料顯示樣式的函數
"""

from gmat_diagnosis_app.constants.config import (
    ERROR_FONT_COLOR, 
    OVERTIME_FONT_COLOR,
    INVALID_FONT_COLOR
)
import logging

def apply_styles(row):
    """Applies styling for invalid rows, incorrect answers, and overtime."""
    styles = [''] * len(row)
    
    try:
        # 1. 藍色文字 - 超時單元格 (第一優先級)
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'

        # 2. 紅色文字 - 錯題樣式（第二優先級）
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)
            # 保留超時單元格的藍色文字
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            
        # 3. 整行灰色文字 - 無效行樣式（最後優先級，會覆蓋前面的樣式）
        is_invalid_row = False
        if 'is_invalid' in row.index and row['is_invalid']:
            is_invalid_row = True
        # 也檢查手動標記的無效項（如果存在）
        elif 'is_manually_invalid' in row.index and row['is_manually_invalid']:
            is_invalid_row = True
            
        if is_invalid_row:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # 即使是無效行，用時超時也應該顯示為藍色
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'

    except (KeyError, IndexError) as e:
        # 記錄更多調試信息但不中斷流程
        logging.debug(f"樣式應用時出錯: {e} (row columns: {list(row.index)})")
        pass # 忽略列缺失導致的樣式錯誤
    return styles 