"""
DI診斷常數模塊

此模塊包含所有用於DI(Data Insights)診斷的常量、閾值和參數映射。
"""

# 從統一常數檔案匯入共通常數
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS

# DI基本常數
MAX_ALLOWED_TIME_DI = 45  # 測驗上限時間（分鐘）
TOTAL_QUESTIONS_DI = 20  # 題目總數
TIME_PRESSURE_THRESHOLD_DI = 3.0  # 時間差閾值（分鐘）

# 使用統一常數
INVALID_TIME_THRESHOLD_MINUTES = COMMON_TIME_CONSTANTS['INVALID_TIME_THRESHOLD_MINUTES']
SUSPICIOUS_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['SUSPICIOUS_FAST_MULTIPLIER']
RELATIVELY_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['RELATIVELY_FAST_MULTIPLIER']
CARELESSNESS_THRESHOLD = COMMON_TIME_CONSTANTS['CARELESSNESS_THRESHOLD']

# INVALID_DATA_TAG_DI is now retrieved from i18n translations using 'di_invalid_data_tag' key

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

# 添加前期過快題目絕對時間閾值 (核心邏輯文件第四章)
EARLY_RUSHING_ABSOLUTE_THRESHOLD_MINUTES = 1.0 # 分鐘 

# --- DI Tool and AI Prompt Recommendations (from DI Doc Chapter 7) ---
DI_TOOL_AI_RECOMMENDATIONS = {
    'DI_READING_COMPREHENSION_ERROR': [
        "Tool: Dustin_GMAT_Core_Sentence_Cracker.md", 
        "Tool: Dustin_GMAT_Close_Reading_Coach.md", 
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Verbal-related/01_basic_explanation.md", 
        "AI Prompt: Verbal-related/03_quick_rc_tricks.md", 
        "AI Prompt: Verbal-related/09_complex_sentence_rewrite.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md", 
        "AI Prompt: DI-related/04_custom_SOP.md"
    ],
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/04_problem_pattern.md", 
        "AI Prompt: DI-related/02_quick_g&t_tricks.md"
    ],
    'DI_DATA_EXTRACTION_ERROR': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: DI-related/02_quick_g&t_tricks.md"
    ],
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': [
        "AI Prompt: Verbal-related/01_basic_explanation.md", 
        "AI Prompt: Verbal-related/03_quick_rc_tricks.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md"
    ],
    'DI_CONCEPT_APPLICATION_ERROR': [
        "Tool: Dustin_GMAT_Textbook_Explainer.md", 
        "Tool: Dustin_GMAT_Q_Question_Classifier.md",
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/03_test_math_concepts.md", 
        "AI Prompt: Quant-related/05_variant_questions.md"
    ],
    'DI_LOGICAL_REASONING_ERROR': [
        "Tool: Dustin_GMAT_DI_Non-math_DS_Simulator.md",
        "Tool: Dustin_GMAT_Textbook_Explainer.md",
        "AI Prompt: Verbal-related/01_basic_explanation.md", 
        "AI Prompt: Verbal-related/02_quick_cr_tpa_tricks.md", 
        "AI Prompt: Verbal-related/05_evaluate_explanation.md", 
        "AI Prompt: Verbal-related/07_logical_term_explained.md"
    ],
    'DI_CALCULATION_ERROR': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/02_quick_math_tricks.md"
    ],
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': [
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Verbal-related/04_mindmap_passage.md", 
        "AI Prompt: Verbal-related/01_basic_explanation.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md", 
        "AI Prompt: DI-related/04_custom_SOP.md"
    ],
    'DI_MSR_READING_COMPREHENSION_BARRIER': [
        "Tool: Dustin_GMAT_Core_Sentence_Cracker.md", 
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Verbal-related/03_quick_rc_tricks.md", 
        "AI Prompt: Verbal-related/01_basic_explanation.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md", 
        "AI Prompt: Verbal-related/09_complex_sentence_rewrite.md"
    ],
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': [
        "Tool: Dustin_GMAT_DI_Non-math_DS_Simulator.md",
        "AI Prompt: (Select based on specific type, e.g., DI-related/02_quick_g&t_tricks.md (GT), DI-related/03_msr_info_flow.md (MSR))"
    ],
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': [
        "Tool: Dustin_GMAT_Textbook_Explainer.md",
        "AI Prompt: Quant-related/01_basic_explanation.md",
        "AI Prompt: Quant-related/03_test_math_concepts.md",
        "AI Prompt: Quant-related/05_variant_questions.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_READING': [
        "Tool: Dustin_GMAT_Core_Sentence_Cracker.md", 
        "Tool: Dustin_GMAT_Close_Reading_Coach.md", 
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Verbal-related/03_quick_rc_tricks.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md", 
        "AI Prompt: DI-related/04_custom_SOP.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md", 
        "AI Prompt: Quant-related/04_problem_pattern.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': [
        "AI Prompt: Verbal-related/02_quick_cr_tpa_tricks.md", 
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': [
        "Tool: GMAT_Terminator_DI_Review.md",
        "AI Prompt: Quant-related/02_quick_math_tricks.md", 
        "AI Prompt: DI-related/02_quick_g&t_tricks.md"
    ],
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': [
        "Tool: GMAT_Terminator_DI_Review.md",
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Verbal-related/03_quick_rc_tricks.md", 
        "AI Prompt: Verbal-related/04_mindmap_passage.md", 
        "AI Prompt: DI-related/03_msr_info_flow.md", 
        "AI Prompt: DI-related/04_custom_SOP.md"
    ],
    'BEHAVIOR_CARELESSNESS_ISSUE': [
        "AI Prompt: Quant-related/01_basic_explanation.md",
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ],
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md",
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ],
    'DI_CARELESSNESS_DETAIL_OMISSION': [
        "AI Prompt: Quant-related/01_basic_explanation.md",
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ]
}

# Parameter categories for report grouping (DI)
DI_PARAM_CATEGORY_ORDER = [
    'SFE', 'Reading/Interpretation', 'Concept/Application', 'Data/Calculation',
    'Logic/Reasoning', 'Multi-Source', 'Efficiency', 'Carelessness', 'Behavioral', 'Unknown'
]

DI_PARAM_TO_CATEGORY = {
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE': 'SFE',
    'DI_READING_COMPREHENSION_ERROR__VOCABULARY': 'Reading/Interpretation',
    'DI_READING_COMPREHENSION_ERROR__SYNTAX': 'Reading/Interpretation',
    'DI_READING_COMPREHENSION_ERROR__LOGIC': 'Reading/Interpretation',
    'DI_READING_COMPREHENSION_ERROR__DOMAIN': 'Reading/Interpretation',
    'DI_GRAPH_INTERPRETATION_ERROR__GRAPH': 'Reading/Interpretation',
    'DI_GRAPH_INTERPRETATION_ERROR__TABLE': 'Reading/Interpretation',
    'DI_CONCEPT_APPLICATION_ERROR__MATH': 'Concept/Application',
    'DI_LOGICAL_REASONING_ERROR__NON_MATH': 'Logic/Reasoning',
    'DI_CALCULATION_ERROR__MATH': 'Data/Calculation',
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': 'Multi-Source',
    'DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION': 'Multi-Source',
    'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY': 'Multi-Source',
    'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX': 'Multi-Source',
    'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC': 'Multi-Source',
    'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN': 'Multi-Source',
    'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH': 'Multi-Source',
    'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE': 'Multi-Source',
    'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH': 'Concept/Application',
    'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH': 'Logic/Reasoning',
    'DI_CALCULATION_DIFFICULTY__MATH': 'Data/Calculation',
    'DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION': 'Carelessness',
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral'
}

# NOTE: The previous APPENDIX_A_TRANSLATION_DI dictionary and _translate_di function 
# have been removed as they are now replaced by the unified i18n translation system.
# All parameter translations are now handled via the i18n system using translation keys.