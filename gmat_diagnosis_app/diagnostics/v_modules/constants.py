"""
V診斷模塊的常量

此模塊包含V(Verbal)診斷所需的所有常量、閾值和參數映射。
"""

# 從統一常數檔案匯入共通常數
from gmat_diagnosis_app.i18n import t
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS

# --- V-Specific Constants ---
# 使用統一常數
V_SUSPICIOUS_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['SUSPICIOUS_FAST_MULTIPLIER']
CARELESSNESS_THRESHOLD = COMMON_TIME_CONSTANTS['CARELESSNESS_THRESHOLD']

# V特定的常數
MAX_ALLOWED_TIME_V = 45  # 測驗上限時間（分鐘）
TOTAL_QUESTIONS_V = 23  # 題目總數
TIME_PRESSURE_THRESHOLD_V = 3.0  # 時間差閾值（分鐘）

# CR Overtime Thresholds (minutes) based on pressure
CR_OVERTIME_THRESHOLDS = {
    True: 2.0, # High Pressure
    False: 2.5 # Low Pressure
}
RC_INDIVIDUAL_Q_THRESHOLD_MINUTES = 2.0  # 用於判斷排除閱讀時間後的單題解答是否過長 (MD文檔標準)
                                        # 與 MD 文件中的 rc_individual_q_threshold 對應
                                        # 在 MD 文件中定義：用於判斷排除第一道題的閱讀時間後，單題解答時間若超過此閾值，則標記為 individual_overtime
RC_READING_TIME_THRESHOLD_3Q = 2.0 # minutes
RC_READING_TIME_THRESHOLD_4Q = 2.5 # minutes
RC_GROUP_TARGET_TIME_ADJUSTMENT = 1.0 # minutes (add to target before checking group_overtime)

# 方案四：RC整組表現分類和單題寬容度
RC_INDIVIDUAL_TOLERANCE_WHEN_GROUP_GOOD = 0.5  # 整組表現良好時的單題寬容度（分鐘）
RC_GROUP_PERFORMANCE_CATEGORIES = {
    'GOOD': '良好',      # 總時間 ≤ 目標時間
    'ACCEPTABLE': '尚可', # 目標時間 < 總時間 ≤ 目標時間 + 1分鐘
    'POOR': '不佳'       # 總時間 > 目標時間 + 1分鐘
}

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
INVALID_DATA_TAG_V = t("v_invalid_data_tag")

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
    
    # 方案四：新增RC整組表現相關診斷參數
    'RC_READING_SPEED_GOOD_GROUP_PERFORMANCE': 'Reading',
    'RC_READING_SPEED_ACCEPTABLE_GROUP_PERFORMANCE': 'Reading',
    'RC_READING_SPEED_POOR_GROUP_PERFORMANCE': 'Reading',

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
    
    # 方案四：新增效率相關診斷參數
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MINOR_ISSUE': 'Timing',
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MODERATE_ISSUE': 'Timing',
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MAJOR_ISSUE': 'Timing',
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_SEVERE_ISSUE': 'Timing',
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MINOR_ISSUE': 'Timing',
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MODERATE_ISSUE': 'Timing',

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
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MINOR_ISSUE': 'AC_Analysis', # 方案四：跨類別參數
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MODERATE_ISSUE': 'AC_Analysis', # 方案四：跨類別參數

    # Question_Understanding
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding',
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': 'Question_Understanding', # ADDED

    # Behavioral
    'BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral',
    'BEHAVIOR_GUESSING_HASTY': 'Behavioral'
}

# --- V Tool and AI Prompt Recommendations ---
# Based on gmat-v-score-logic-dustin-v1.4.md Chapter 8
V_TOOL_AI_RECOMMENDATIONS = {
    # CR - Reasoning / Specific Type
    'CR_REASONING_CHAIN_ERROR': ["Tool: Dustin_GMAT_CR_Chain_Argument_Evaluation.md", "AI: Verbal-related/05_evaluate_explanation.md, Verbal-related/06_boldface_SOP.md"],
    'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': ["Tool: Dustin_GMAT_CR_Core_Issue_Identifier.md", "AI: Verbal-related/01_basic_explanation.md"],
    'CR_METHOD_TYPE_SPECIFIC_ERROR': [ # This is a general key; specific tool/AI might depend on the actual type mentioned in diagnosis.
        "Tool: (If Boldface) Dustin_GMAT_CR_Boldface_Interactive_Tutor.md",
        "Tool: (If Argument Construction) Dustin_GMAT_CR_Role_Argument_Construction.md",
        "AI: Verbal-related/01_basic_explanation.md, Verbal-related/05_evaluate_explanation.md, Verbal-related/06_boldface_SOP.md (If Boldface)"
    ],
    'CR_REASONING_ABSTRACTION_DIFFICULTY': ["Tool: Dustin_GMAT_Textbook_Explainer.md", "AI: Verbal-related/07_logical_term_explained.md, Verbal-related/09_complex_sentence_rewrite.md"],
    'CR_READING_BASIC_OMISSION': ["AI: Verbal-related/01_basic_explanation.md"],
    'CR_READING_DIFFICULTY_STEM': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/07_logical_term_explained.md, Verbal-related/09_complex_sentence_rewrite.md"],
    'CR_READING_TIME_EXCESSIVE': ["AI: Verbal-related/02_quick_cr_tpa_tricks.md, Verbal-related/03_quick_rc_tricks.md"],
    'CR_QUESTION_UNDERSTANDING_MISINTERPRETATION': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/07_logical_term_explained.md"],
    'CR_REASONING_PREDICTION_ERROR': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/05_evaluate_explanation.md"],
    'CR_REASONING_TIME_EXCESSIVE': ["AI: Verbal-related/02_quick_cr_tpa_tricks.md, Verbal-related/05_evaluate_explanation.md"],
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': ["AI: Verbal-related/07_logical_term_explained.md, Verbal-related/01_basic_explanation.md"],
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': ["AI: Verbal-related/05_evaluate_explanation.md, Verbal-related/06_boldface_SOP.md"],
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': ["Tool: Dustin_GMAT_Verbal_Distractor_Mocker.md", "AI: Verbal-related/01_basic_explanation.md, Verbal-related/07_logical_term_explained.md"],
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': ["AI: Verbal-related/02_quick_cr_tpa_tricks.md, Verbal-related/06_boldface_SOP.md"],
    'CR_METHOD_PROCESS_DEVIATION': ["AI: Verbal-related/05_evaluate_explanation.md, Verbal-related/06_boldface_SOP.md"],

    # RC - Reading Comprehension
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': ["Tool: Dustin_GMAT_Chunk_Reading_Coach.md", "AI: Verbal-related/03_quick_rc_tricks.md"],
    # Explicitly adding RC_READING_COMPREHENSION_BARRIER based on its inclusion in the reporting code and potential relation to reading speed
    'RC_READING_COMPREHENSION_BARRIER': ["Tool: Dustin_GMAT_Chunk_Reading_Coach.md", "AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': ["Tool: Dustin_GMAT_Sentence_Cracker.md", "AI: Verbal-related/09_complex_sentence_rewrite.md, Verbal-related/01_basic_explanation.md"],
    'RC_READING_DOMAIN_KNOWLEDGE_GAP': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/08_source_passage_rewrite.md"],
    'RC_READING_VOCAB_BOTTLENECK': ["Tool: Dustin_GMAT_Core_Vocab_Master.md", "AI: Verbal-related/09_complex_sentence_rewrite.md, Verbal-related/01_basic_explanation.md"],
    'RC_READING_PRECISION_INSUFFICIENT': ["Tool: Dustin_GMAT_Close_Reading_Coach.md", "AI: Verbal-related/01_basic_explanation.md, Verbal-related/03_quick_rc_tricks.md"],
    'RC_READING_PASSAGE_STRUCTURE_DIFFICULTY': ["Tool: Dustin_GMAT_RC_Passage_Analyzer.md", "AI: Verbal-related/04_mindmap_passage.md, Verbal-related/03_quick_rc_tricks.md"],
    'RC_READING_INFO_LOCATION_ERROR': ["AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/04_mindmap_passage.md"],
    'RC_READING_KEYWORD_LOGIC_OMISSION': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/03_quick_rc_tricks.md"],
    'RC_METHOD_INEFFICIENT_READING': ["AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/04_mindmap_passage.md"],
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/07_logical_term_explained.md"],
    'RC_LOCATION_ERROR_INEFFICIENCY': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_LOCATION_TIME_EXCESSIVE': ["AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/04_mindmap_passage.md"],
    'RC_REASONING_INFERENCE_WEAKNESS': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/05_evaluate_explanation.md"],
    'RC_REASONING_TIME_EXCESSIVE': ["AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/05_evaluate_explanation.md"],
    'RC_AC_ANALYSIS_DIFFICULTY': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/07_logical_term_explained.md"],
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_METHOD_TYPE_SPECIFIC_ERROR': ["AI: Verbal-related/01_basic_explanation.md (general), specific RC type tricks if available"],
    
    # 方案四：整組表現相關診斷
    'RC_READING_SPEED_GOOD_GROUP_PERFORMANCE': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_READING_SPEED_ACCEPTABLE_GROUP_PERFORMANCE': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_READING_SPEED_POOR_GROUP_PERFORMANCE': ["Tool: Dustin_GMAT_Chunk_Reading_Coach.md", "AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/04_mindmap_passage.md"],
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MINOR_ISSUE': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MODERATE_ISSUE': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MAJOR_ISSUE': ["AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/05_evaluate_explanation.md"],
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_SEVERE_ISSUE': ["Tool: Dustin_GMAT_RC_Passage_Analyzer.md", "AI: Verbal-related/03_quick_rc_tricks.md, Verbal-related/05_evaluate_explanation.md"],
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MINOR_ISSUE': ["AI: Verbal-related/01_basic_explanation.md"],
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MODERATE_ISSUE': ["AI: Verbal-related/01_basic_explanation.md, Verbal-related/05_evaluate_explanation.md"],

    # Foundational Mastery / Efficiency / Behavioral
    'FOUNDATIONAL_MASTERY_INSTABILITY_SFE': ["AI: Verbal-related/01_basic_explanation.md (priority)"],
    'EFFICIENCY_BOTTLENECK_READING': ["Tool: Dustin_GMAT_Chunk_Reading_Coach.md", "AI: Verbal-related/03_quick_rc_tricks.md"],
    'EFFICIENCY_BOTTLENECK_REASONING': ["AI: Verbal-related/02_quick_cr_tpa_tricks.md, Verbal-related/05_evaluate_explanation.md"],
    'EFFICIENCY_BOTTLENECK_LOCATION': ["AI: Verbal-related/03_quick_rc_tricks.md"],
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': ["AI: Verbal-related/02_quick_cr_tpa_tricks.md (CR), Verbal-related/03_quick_rc_tricks.md (RC)"],
    'BEHAVIOR_CARELESSNESS_ISSUE': ["Tool: Dustin_GMAT_Verbal_Distractor_Mocker.md", "AI: Verbal-related/05_evaluate_explanation.md, Verbal-related/01_basic_explanation.md"],
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': ["AI: Verbal-related/05_evaluate_explanation.md"],
    'BEHAVIOR_GUESSING_HASTY': ["AI: Verbal-related/01_basic_explanation.md"],

    # Generic/Fallback recommendations for broader categories if specific param not hit
    # These are conceptual and would require a different lookup logic if implemented.
    # For now, the mapping is direct parameter to recommendation.
} 