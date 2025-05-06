# --- DI-Specific Constants (from Markdown Chapter 0 & 1) ---
MAX_ALLOWED_TIME_DI = 45.0  # minutes
TOTAL_QUESTIONS_DI = 20
TIME_PRESSURE_THRESHOLD_DI = 3.0  # minutes difference
INVALID_TIME_THRESHOLD_MINUTES = 0.5  # 修改為 0.5 分鐘，與核心邏輯文件第一章疑似放棄的標準一致
INVALID_DATA_TAG_DI = "數據無效：用時過短（受時間壓力影響）" # Added invalid tag

# Overtime thresholds (minutes) based on time pressure
OVERTIME_THRESHOLDS = {
    True: {  # High Pressure
        'TPA': 3.0,
        'GT': 3.0,
        'DS': 2.0,
        'MSR_GROUP': 6.0,
        'MSR_READING': 1.5,
        'MSR_SINGLE_Q': 1.5
    },
    False: {  # Low Pressure
        'TPA': 3.5,
        'GT': 3.5,
        'DS': 2.5,
        'MSR_GROUP': 7.0,
        'MSR_READING': 1.5,  # Reading threshold often kept constant
        'MSR_SINGLE_Q': 1.5  # Single question threshold often kept constant
    }
}

# 添加用於判斷異常快速作答的標準（核心邏輯文件第一章）
SUSPICIOUS_FAST_MULTIPLIER = 0.5  # 用於計算相對於前三分之一平均的閾值

# 添加粗心閾值（核心邏輯文件第四章）
CARELESSNESS_THRESHOLD = 0.25  # 快錯率超過25%判定為粗心 