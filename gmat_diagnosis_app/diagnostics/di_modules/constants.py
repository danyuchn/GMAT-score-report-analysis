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