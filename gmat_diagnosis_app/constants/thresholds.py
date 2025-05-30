# -*- coding: utf-8 -*-
"""Centralized Thresholds for GMAT Diagnosis App."""

# --- Common Time-related Constants ---
COMMON_TIME_CONSTANTS = {
    'SUSPICIOUS_FAST_MULTIPLIER': 0.5,  # 相對於前三分之一平均時間的倍數，判斷相對倉促
    'RELATIVELY_FAST_MULTIPLIER': 0.75,  # 相對於全體平均時間的倍數，判斷相對快速作答
    'INVALID_TIME_THRESHOLD_MINUTES': 0.5,  # 判斷為疑似放棄的閾值（分鐘）
    'ABSOLUTE_FAST_THRESHOLD_MINUTES': 1.0,  # 判斷為絕對倉促的閾值（分鐘）
    'CARELESSNESS_THRESHOLD': 0.25,  # 快錯率超過25%判定為粗心
    'SKILL_OVERRIDE_THRESHOLD': 0.5,  # 技能覆蓋規則閾值（50%）
    'TARGET_PRACTICE_TIME_MINUTES': 2.0,  # 練習建議的目標時間
    'MACRO_PRACTICE_TIME_MINUTES': 2.5   # 宏觀建議的固定限時
}

THRESHOLDS = {
    'Q': {
        'TOTAL_QUESTIONS': 21,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_FAST_END_MIN': 1.0,
        'TIME_DIFF_PRESSURE': 3.0, 
        'LAST_THIRD_FRACTION': 2/3, 
        'OVERTIME_PRESSURE': 2.5,
        'OVERTIME_NO_PRESSURE': 3.0,
        'INVALID_TAG': "數據無效：用時過短（Q：受時間壓力影響，處於後段且用時短）"
    },
    'DI': {
        'TOTAL_QUESTIONS': 20,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_FAST_END_MIN': 1.0,
        'TIME_PRESSURE_DIFF_MIN': 3.0, 
        'LAST_THIRD_FRACTION': 2/3,
        'INVALID_TAG': "數據無效：用時過短（DI：受時間壓力影響，處於後段且用時短）",
        'OVERTIME': {
            'TPA': {'pressure': 3.0, 'no_pressure': 3.5},
            'GT': {'pressure': 3.0, 'no_pressure': 3.5}, 
            'DS': {'pressure': 2.0, 'no_pressure': 2.5},
            'MSR_TARGET': {'pressure': 6.0, 'no_pressure': 7.0}
        }
    },
    'V': {
        'TOTAL_QUESTIONS': 23,
        'MAX_ALLOWED_TIME': 45.0,
        'INVALID_HASTY_MIN': 1.0, 
        'INVALID_TAG': "數據無效：用時過短（V：用時低於下限）", 
        'OVERTIME': {
            'CR': {'pressure': 2.0, 'no_pressure': 2.5},
            'RC_INDIVIDUAL': 2.0,
            'RC_GROUP_TARGET': { 
                '3Q': {'pressure': 6.0, 'no_pressure': 7.0},
                '4Q': {'pressure': 8.0, 'no_pressure': 9.0}
            }
        }
    }
} 