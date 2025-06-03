"""
Q診斷模塊的常量和參數映射

此模塊包含所有用於Q(Quantitative)診斷的常量、閾值和參數映射，
用於診斷報告生成和分析。
"""

# 從統一常數檔案匯入共通常數
from gmat_diagnosis_app.i18n import t
from gmat_diagnosis_app.constants.thresholds import COMMON_TIME_CONSTANTS

# --- Q-Specific Constants ---
# 第零章與第一章的常數
MAX_ALLOWED_TIME_Q = 45.0  # 測驗上限時間（分鐘）
# TOTAL_QUESTIONS_Q = 21  # 移除硬編碼，改為運行時從數據計算
TIME_PRESSURE_THRESHOLD_Q = 3.0  # 時間差閾值（分鐘）

# 使用統一常數
INVALID_TIME_THRESHOLD_MINUTES = COMMON_TIME_CONSTANTS['INVALID_TIME_THRESHOLD_MINUTES']
ABSOLUTE_FAST_THRESHOLD_MINUTES = COMMON_TIME_CONSTANTS['ABSOLUTE_FAST_THRESHOLD_MINUTES']
SUSPICIOUS_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['SUSPICIOUS_FAST_MULTIPLIER']
RELATIVELY_FAST_MULTIPLIER = COMMON_TIME_CONSTANTS['RELATIVELY_FAST_MULTIPLIER']
CARELESSNESS_THRESHOLD = COMMON_TIME_CONSTANTS['CARELESSNESS_THRESHOLD']

# 超時閾值（分鐘）基於時間壓力狀態
OVERTIME_THRESHOLDS = {
    True: 2.5,  # 高壓力
    False: 3.0  # 低壓力
}

INVALID_DATA_TAG_Q = t("q_invalid_data_tag")

# 參數分配規則字典
PARAM_ASSIGNMENT_RULES = {
    # (time_performance_category, question_type): [param_list]
    # Fast & Wrong
    ('Fast & Wrong', 'REAL'): ['Q_READING_COMPREHENSION_ERROR', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'],
    ('Fast & Wrong', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'],
    # Slow & Wrong
    ('Slow & Wrong', 'REAL'): ['Q_READING_COMPREHENSION_ERROR', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 'Q_READING_COMPREHENSION_DIFFICULTY', 'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED', 'Q_CONCEPT_APPLICATION_DIFFICULTY', 'Q_CALCULATION_DIFFICULTY'],
    ('Slow & Wrong', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 'Q_CONCEPT_APPLICATION_DIFFICULTY', 'Q_CALCULATION_DIFFICULTY'],
    # Normal Time & Wrong
    ('Normal Time & Wrong', 'REAL'): ['Q_READING_COMPREHENSION_ERROR', 'Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'],
    ('Normal Time & Wrong', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE'],
    # Slow & Correct
    ('Slow & Correct', 'REAL'): ['Q_READING_COMPREHENSION_DIFFICULTY', 'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED', 'Q_CONCEPT_APPLICATION_DIFFICULTY', 'Q_CALCULATION_DIFFICULTY'],
    ('Slow & Correct', 'PURE'): ['Q_CONCEPT_APPLICATION_DIFFICULTY', 'Q_CALCULATION_DIFFICULTY'],
    # Unknown cases - retain a generic set, adjusted for new tags
    ('Unknown', 'REAL'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR', 'Q_READING_COMPREHENSION_ERROR'],
    ('Unknown', 'PURE'): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR'],
    ('Unknown', None): ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR'],
}

# Default params if incorrect but category/type combo not found above
DEFAULT_INCORRECT_PARAMS = ['Q_CONCEPT_APPLICATION_ERROR', 'Q_CALCULATION_ERROR']

# --- Q Tool and AI Prompt Recommendations (from Q-Doc Chapter 8) ---
Q_TOOL_AI_RECOMMENDATIONS = {
    'Q_READING_COMPREHENSION_ERROR': [
        "Tool: Dustin_GMAT_Q_Real-Context_Converter.md", 
        "Tool: Dustin_GMAT_Core_Sentence_Cracker.md", 
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Verbal-related/09_complex_sentence_rewrite.md"
    ],
    'Q_PROBLEM_UNDERSTANDING_ERROR': [
        "Tool: Dustin_GMAT_Q_Question_Classifier.md", 
        "Tool: Dustin_GMAT_Textbook_Explainer.md",
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/03_test_math_concepts.md", 
        "AI Prompt: Verbal-related/07_logical_term_explained.md (for DS)"
    ],
    'Q_CONCEPT_APPLICATION_ERROR': [
        "Tool: Dustin_GMAT_Q_Question_Classifier.md", 
        "Tool: Dustin_GMAT_Textbook_Explainer.md",
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/03_test_math_concepts.md", 
        "AI Prompt: Quant-related/04_problem_pattern.md", 
        "AI Prompt: Quant-related/05_variant_questions.md"
    ],
    'Q_CALCULATION_ERROR': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/02_quick_math_tricks.md"
    ],
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': [
        "Tool: Dustin_GMAT_Textbook_Explainer.md",
        "AI Prompt: Quant-related/01_basic_explanation.md (Priority)", 
        "AI Prompt: Quant-related/03_test_math_concepts.md (Auxiliary)", 
        "AI Prompt: Quant-related/05_variant_questions.md (Auxiliary)"
    ],
    'Q_EFFICIENCY_BOTTLENECK_READING': [
        "Tool: Dustin_GMAT_Chunk_Reading_Coach.md",
        "AI Prompt: Quant-related/02_quick_math_tricks.md"
    ],
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md", 
        "AI Prompt: Quant-related/04_problem_pattern.md"
    ],
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md"
    ],
    'BEHAVIOR_CARELESSNESS_ISSUE': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ],
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': [
        "AI Prompt: Quant-related/02_quick_math_tricks.md", 
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ],
    'Q_CARELESSNESS_DETAIL_OMISSION': [
        "AI Prompt: Quant-related/01_basic_explanation.md", 
        "AI Prompt: Quant-related/02_quick_math_tricks.md", 
        "AI Prompt: Verbal-related/05_evaluate_explanation.md"
    ]
    # Generic Q practice/classification/understanding could be added as a default if needed
} 