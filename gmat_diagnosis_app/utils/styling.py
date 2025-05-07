"""
樣式工具模組
提供資料顯示樣式的函數
"""

from gmat_diagnosis_app.constants.config import (
    ERROR_FONT_COLOR, 
    OVERTIME_FONT_COLOR
)

def apply_styles(row):
    """Applies styling for invalid rows, incorrect answers, and overtime."""
    styles = [''] * len(row)
    INVALID_FONT_COLOR = '#A9A9A9' # DarkGray
    
    try:
        # 首先優先檢查是否為無效行 (is_invalid 或 is_manually_invalid 為 True)
        is_invalid_row = False
        if 'is_invalid' in row.index and row['is_invalid']:
            is_invalid_row = True
        # 也檢查手動標記的無效項（如果存在）
        elif 'is_manually_invalid' in row.index and row['is_manually_invalid']:
            is_invalid_row = True
            
        # 整行灰色文字 - 無效行樣式
        if is_invalid_row:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # 即使是無效行，用時超時也應該顯示為藍色
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            return styles # 無效行優先返回
            
        # 紅色文字 - 錯題樣式（僅適用於非無效行）
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)

        # 藍色文字 - 超時單元格
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'

    except (KeyError, IndexError) as e:
        # 記錄更多調試信息但不中斷流程
        import logging
        logging.debug(f"樣式應用時出錯: {e} (row columns: {list(row.index)})")
        pass # 忽略列缺失導致的樣式錯誤
    return styles 