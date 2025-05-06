# -*- coding: utf-8 -*-
"""Centralized Thresholds for GMAT Diagnosis App."""

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