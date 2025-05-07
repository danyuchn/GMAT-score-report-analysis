"""
常量和配置模組
包含應用程式中使用的各種常量和配置項
"""

# --- Constants ---
# Subjects definition
SUBJECTS = ['Q', 'V', 'DI']  # Define subjects for iteration

# File size limits
MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# IRT Simulation Constants
BANK_SIZE = 1000
RANDOM_SEED = 1000
SUBJECT_SIM_PARAMS = {
    'Q': {'initial_theta_key': 'initial_theta_q', 'total_questions': 31, 'seed_offset': 0},
    'V': {'initial_theta_key': 'initial_theta_v', 'total_questions': 36, 'seed_offset': 1},
    'DI': {'initial_theta_key': 'initial_theta_di', 'total_questions': 12, 'seed_offset': 2}
}

# Styling Constants
ERROR_FONT_COLOR = '#D32F2F'  # Red for errors
OVERTIME_FONT_COLOR = '#0000FF'  # Blue for overtime
INVALID_FONT_COLOR = '#A9A9A9'  # Dark Gray for invalid rows

# Base Column Rename Map (Original CSV Header -> Internal Name)
BASE_RENAME_MAP = {
    'Performance': 'is_correct',  # Rename to is_correct early
    'Response Time (Minutes)': 'question_time',
    'Question Type': 'question_type',
    'Content Domain': 'content_domain',
    'Fundamental Skills': 'question_fundamental_skill'
    # 'Question' handled dynamically based on BOM
}

# Required Original Columns per Subject (Used by validation)
REQUIRED_ORIGINAL_COLS = {
    'Q': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type', 'Fundamental Skills'],
    'V': ['Question', 'Response Time (Minutes)', 'Performance', 'Question Type', 'Fundamental Skills'],  # Removed Content Domain for V
    'DI': ['Question', 'Response Time (Minutes)', 'Performance', 'Content Domain', 'Question Type']  # Removed Fundamental Skills for DI
}

# Columns to keep for final diagnosis dataframe preparation
# Ensure all columns needed by diagnosis functions are listed here
FINAL_DIAGNOSIS_INPUT_COLS = [
    'Subject', 'question_position', 'is_correct', 'question_time',
    'question_type', 'content_domain', 'question_fundamental_skill',
    'is_invalid', 'overtime', 'is_manually_invalid',  # Keep manual flag for reference if needed
    # Add simulation/calculated columns later:
    'question_difficulty', 'estimated_ability',
    # Added for V and DI diagnosis and overtime calculation needs
    'rc_group_id', 'rc_reading_time', 'rc_group_total_time', 'rc_group_num_questions', # For Verbal
    'msr_group_id', 'msr_group_total_time', 'msr_reading_time', 'msr_group_num_questions', 'is_first_msr_q' # For DI
]

# --- Column Display Configuration ---
COLUMN_DISPLAY_CONFIG = {
    "question_position": None,  # Will be replaced in app.py
    "question_type": None,
    "question_fundamental_skill": None,
    "question_difficulty": None,
    "question_time": None,
    "time_performance_category": None,
    "content_domain": None, 
    "diagnostic_params_list": None,
    "is_correct": None,
    "is_sfe": None,
    "is_invalid": None,
    "overtime": None,
    "is_manually_invalid": None,
}

# --- Excel Column Mapping ---
EXCEL_COLUMN_MAP = {
    "question_position": "題號",
    "question_type": "題型",
    "question_fundamental_skill": "考察能力",
    "question_difficulty": "難度(模擬)",
    "question_time": "用時(分)",
    "time_performance_category": "時間表現",
    "content_domain": "內容領域",
    "diagnostic_params_list": "診斷標籤",
    "is_correct": "答對",  # Use text TRUE/FALSE
    "is_sfe": "SFE",  # Use text TRUE/FALSE
    "is_invalid": "是否無效",  # Use text TRUE/FALSE
    "overtime": "overtime_flag",  # Internal flag for Excel styling, will be hidden by to_excel
} 