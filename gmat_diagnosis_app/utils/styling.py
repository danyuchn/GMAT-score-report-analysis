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
        # Grey text for invalid rows (overrides other text styles)
        if 'is_invalid' in row.index and row['is_invalid']:
            styles = [f'color: {INVALID_FONT_COLOR}'] * len(row)
            # Apply overtime text color even if invalid
            if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
                time_col_idx = row.index.get_loc('question_time')
                styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'
            return styles # Return early if invalid

        # Red text for incorrect (only if not invalid)
        if 'is_correct' in row.index and not row['is_correct']:
            styles = [f'color: {ERROR_FONT_COLOR}'] * len(row)

        # Blue text for overtime time cell
        if 'overtime' in row.index and row['overtime'] and 'question_time' in row.index:
            time_col_idx = row.index.get_loc('question_time')
            styles[time_col_idx] = f'color: {OVERTIME_FONT_COLOR}'

    except (KeyError, IndexError):
        pass # Ignore styling errors if columns are missing
    return styles 