"""
V診斷模塊的常量和參數映射

此模塊包含所有用於V(Verbal)診斷的常量、閾值和參數映射，
用於診斷報告生成和分析。
"""

# --- V-Specific Constants ---
# CR Overtime Thresholds (minutes) based on pressure
CR_OVERTIME_THRESHOLDS = {
    True: 2.0, # High Pressure
    False: 2.5 # Low Pressure
}
RC_INDIVIDUAL_Q_THRESHOLD_MINUTES = 2.0  # 用於判斷排除閱讀時間後的單題解答是否過長
RC_READING_TIME_THRESHOLD_3Q = 2.0 # minutes
RC_READING_TIME_THRESHOLD_4Q = 2.5 # minutes
RC_GROUP_TARGET_TIME_ADJUSTMENT = 1.0 # minutes (add to target before checking group_overtime)

# RC Group Target Times (minutes) based on pressure
RC_GROUP_TARGET_TIMES = {
    True: { # High Pressure
        3: 6.0,
        4: 8.0
    },
    False: { # Low Pressure
        3: 7.0,
        4: 9.0
    }
}

# Define Hasty/Abandoned Threshold for use in Chapter 1/3 logic
V_INVALID_TIME_ABANDONED = 0.5 # minutes (as per V-Doc Ch1 Invalid rule)
V_INVALID_TIME_HASTY_MIN = 1.0 # minutes (as per V-Doc Ch1 Invalid rule)
HASTY_GUESSING_THRESHOLD_MINUTES = 0.5 # minutes (Used for BEHAVIOR_GUESSING_HASTY tag in Ch3)
INVALID_DATA_TAG_V = "數據無效：用時過短（受時間壓力影響）"
V_SUSPICIOUS_FAST_MULTIPLIER = 0.5 # 標記過快可疑題目的乘數

# Map fundamental skills (expected in data) to broader error categories for Chapter 3
V_SKILL_TO_ERROR_CATEGORY = {
    # VDOC Defined Core Skills
    'Plan/Construct': 'Logic/Reasoning',
    'Identify Stated Idea': 'Reading/Understanding',
    'Identify Inferred Idea': 'Inference/Application',
    'Analysis/Critique': 'Logic/Reasoning',
    # Common - Foundational Mastery Instability
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    # Default/Unknown
    'Unknown Skill': 'Unknown',
    # Add other non-skill mappings if needed
    'DI_DATA_INTERPRETATION_ERROR': 'Unknown',
    'DI_LOGICAL_REASONING_ERROR': 'Unknown',
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'Unknown',
}

# --- 參數類別順序定義 ---
V_PARAM_CATEGORY_ORDER = [
    'SFE',                  # 基礎掌握
    'Reading',              # 閱讀理解
    'Reasoning',            # 邏輯推理
    'Timing',               # 時間管理
    'Process',              # 流程方法
    'AC_Analysis',          # 選項分析
    'Question_Understanding', # 問題理解
    'Behavioral',           # 行為模式
    'Unknown'               # 未分類
]

# --- 參數到類別的映射 ---
V_PARAM_TO_CATEGORY = {
    # SFE
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',

    # Reading
    'CR_READING_BASIC_OMISSION': 'Reading',
    'CR_READING_DIFFICULTY_STEM': 'Reading',
    'CR_READING_TIME_EXCESSIVE': 'Reading', # Also Timing
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': 'Reading', # Also Timing
    'RC_READING_COMPREHENSION_BARRIER': 'Reading',
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': 'Reading',
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': 'Reading',
    'RC_READING_VOCAB_BOTTLENECK': 'Reading',
    'RC_READING_PRECISION_INSUFFICIENT': 'Reading',
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': 'Reading',
    'RC_READING_INFO_LOCATION_ERROR': 'Reading', # ADDED
    'RC_READING_KEYWORD_LOGIC_OMISSION': 'Reading', # ADDED

    # Reasoning
    'CR_REASONING_CHAIN_ERROR': 'Reasoning',
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': 'Reasoning',
    'CR_REASONING_ABSTRACTION_DIFFICULTY': 'Reasoning',
    'CR_REASONING_PREDICTION_ERROR': 'Reasoning',
    'CR_REASONING_TIME_EXCESSIVE': 'Reasoning', # Also Timing
    'RC_REASONING_INFERENCE_WEAKNESS': 'Reasoning',
    'RC_REASONING_TIME_EXCESSIVE': 'Reasoning', # Also Timing - ADDED

    # Timing
    'CR_READING_TIME_EXCESSIVE': 'Timing', # Also Reading
    'CR_REASONING_TIME_EXCESSIVE': 'Timing', # Also Reasoning
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': 'Timing', # Also AC_Analysis
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': 'Timing', # Also Reading
    'RC_LOCATION_TIME_EXCESSIVE': 'Timing', # ADDED
    'RC_REASONING_TIME_EXCESSIVE': 'Timing', # Also Reasoning - ADDED
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': 'Timing', # Also AC_Analysis - ADDED
    'EFFICIENCY_BOTTLENECK_READING': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_REASONING': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_LOCATION': 'Timing', # ADDED
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': 'Timing', # ADDED

    # Process
    'CR_METHOD_TYPE_SPECIFIC_ERROR': 'Process',
    'CR_METHOD_PROCESS_DEVIATION': 'Process',
    'RC_METHOD_INEFFICIENT_READING': 'Process', # ADDED
    'RC_LOCATION_ERROR_INEFFICIENCY': 'Process', # ADDED
    'RC_METHOD_TYPE_SPECIFIC_ERROR': 'Process', # ADDED

    # AC_Analysis (Answer Choice Analysis)
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': 'AC_Analysis',
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': 'AC_Analysis',
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': 'AC_Analysis',
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': 'AC_Analysis', # Also Timing
    'RC_AC_ANALYSIS_DIFFICULTY': 'AC_Analysis',
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': 'AC_Analysis', # Also Timing - ADDED

    # Question_Understanding
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding',
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding', # ADDED

    # Behavioral
    'BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral',
    'BEHAVIOR_GUESSING_HASTY': 'Behavioral'
} 