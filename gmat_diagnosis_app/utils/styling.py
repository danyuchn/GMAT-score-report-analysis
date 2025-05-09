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
        # 調試信息
        if 'Subject' in row.index:
            subject = row['Subject']
            q_pos = row['question_position'] if 'question_position' in row.index else "未知"
            logging.debug(f"【styling調試】{subject}科題號{q_pos}開始樣式處理")
            
            # 記錄無效項狀態
            if 'is_invalid' in row.index:
                logging.debug(f"【styling調試】{subject}科題號{q_pos} is_invalid值: {row['is_invalid']}")
            if 'is_manually_invalid' in row.index:
                logging.debug(f"【styling調試】{subject}科題號{q_pos} is_manually_invalid值: {row['is_manually_invalid']}")
        
        # 1. 藍色文字 - 超時單元格 (第一優先級)
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用超時樣式")

        # 2. 紅色文字 - 錯題樣式（第二優先級）
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)
            # 保留超時單元格的藍色文字
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用錯題樣式")
            
        # 3. 整行灰色文字 - 無效行樣式（最後優先級，會覆蓋前面的樣式）
        # 首先檢查 is_invalid，再檢查 is_manually_invalid
        is_invalid_row = False
        # 1. 先檢查 is_invalid
        if 'is_invalid' in row.index and row['is_invalid']:
            is_invalid_row = True
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos} 依據is_invalid={row['is_invalid']}標記為無效行")
        # 2. 如果 is_invalid 不是 true，再檢查 is_manually_invalid
        if not is_invalid_row and 'is_manually_invalid' in row.index and row['is_manually_invalid']:
            is_invalid_row = True
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos} 依據is_manually_invalid={row['is_manually_invalid']}標記為無效行")
            
        if is_invalid_row:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # 即使是無效行，用時超時也應該顯示為藍色
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
                
            if 'Subject' in row.index:
                subject = row['Subject']
                q_pos = row['question_position'] if 'question_position' in row.index else "未知"
                logging.debug(f"【styling調試】{subject}科題號{q_pos}應用無效項樣式")

    except (KeyError, IndexError) as e:
        # 記錄更多調試信息但不中斷流程
        logging.debug(f"樣式應用時出錯: {e} (row columns: {list(row.index)})")
        pass # 忽略列缺失導致的樣式錯誤
    return styles 