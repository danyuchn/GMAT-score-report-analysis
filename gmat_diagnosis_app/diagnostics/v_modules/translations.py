"""
V診斷模塊的翻譯功能

此模塊包含用於V(Verbal)診斷的翻譯字典和相關函數，
用於在診斷過程中將英文術語翻譯為中文。
"""

from gmat_diagnosis_app.diagnostics.v_modules.constants import INVALID_DATA_TAG_V

# --- V Appendix A Translation ---
APPENDIX_A_TRANSLATION_V = {
    # --- Diagnostic Tags from verbal_diagnostic_tags_summary.md ---
    'FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE': "基礎掌握: 應用不穩定",
    'BEHAVIOR_PATTERN_FAST_GUESSING_HASTY': "行為模式: 過快疑似猜題/倉促",
    'DATA_INVALID_SHORT_TIME_PRESSURE_AFFECTED': "數據無效：用時過短",

    'CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP': "CR 題幹理解錯誤：提問要求把握錯誤",
    'CR_STEM_UNDERSTANDING_ERROR_VOCAB': "CR 題幹理解錯誤：詞彙",
    'CR_STEM_UNDERSTANDING_ERROR_SYNTAX': "CR 題幹理解錯誤：句式",
    'CR_STEM_UNDERSTANDING_ERROR_LOGIC': "CR 題幹理解錯誤：邏輯",
    'CR_STEM_UNDERSTANDING_ERROR_DOMAIN': "CR 題幹理解錯誤：領域",
    'CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP': "CR 推理錯誤: 邏輯鏈分析錯誤",
    'CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING': "CR 推理錯誤: 抽象邏輯/術語理解錯誤",
    'CR_REASONING_ERROR_PREDICTION_DIRECTION': "CR 推理錯誤: 預判方向錯誤",
    'CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION': "CR 推理錯誤: 核心議題識別錯誤",
    'CR_CHOICE_UNDERSTANDING_ERROR_VOCAB': "CR 選項理解錯誤: 選項詞彙理解錯誤",
    'CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX': "CR 選項理解錯誤: 選項句式理解錯誤",
    'CR_CHOICE_UNDERSTANDING_ERROR_LOGIC': "CR 選項理解錯誤: 選項邏輯理解錯誤",
    'CR_CHOICE_UNDERSTANDING_ERROR_DOMAIN': "CR 選項理解錯誤: 選項領域理解錯誤",
    'CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT': "CR 推理錯誤: 選項相關性判斷錯誤",
    'CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION': "CR 推理錯誤: 強干擾選項混淆",
    'CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE': "CR 特定題型弱點",

    'CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB': "CR 題幹理解障礙：詞彙",
    'CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX': "CR 題幹理解障礙：句式",
    'CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC': "CR 題幹理解障礙：邏輯",
    'CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN': "CR 題幹理解障礙：領域",
    'CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING': "CR 推理障礙: 抽象邏輯/術語理解困難",
    'CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING': "CR 推理障礙: 預判方向缺失",
    'CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION': "CR 推理障礙: 核心議題識別困難",
    'CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT': "CR 推理障礙: 選項相關性判斷困難",
    'CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS': "CR 推理障礙: 強干擾選項辨析困難",
    'CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB': "CR 選項理解障礙: 選項詞彙理解困難",
    'CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX': "CR 選項理解障礙: 選項句式理解困難",
    'CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC': "CR 選項理解障礙: 選項邏輯理解困難",
    'CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN': "CR 選項理解障礙: 選項領域理解困難",

    'RC_READING_COMPREHENSION_ERROR_VOCAB': "RC 閱讀理解錯誤: 詞彙理解錯誤",
    'RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS': "RC 閱讀理解錯誤: 長難句解析錯誤",
    'RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE': "RC 閱讀理解錯誤: 篇章結構理解錯誤",
    'RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING': "RC 閱讀理解錯誤: 關鍵信息定位/理解錯誤",
    'RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT': "RC 題目理解錯誤: 提問焦點理解錯誤",
    'RC_LOCATION_SKILL_ERROR_LOCATION': "RC 定位能力錯誤: 定位錯誤",
    'RC_REASONING_ERROR_INFERENCE': "RC 推理錯誤: 推理錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_VOCAB': "RC 選項辨析錯誤: 選項詞彙理解錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_SYNTAX': "RC 選項辨析錯誤: 選項句式理解錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_LOGIC': "RC 選項辨析錯誤: 選項邏輯理解錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_DOMAIN': "RC 選項辨析錯誤: 選項領域理解錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT': "RC 選項辨析錯誤: 選項相關性判斷錯誤",
    'RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION': "RC 選項辨析錯誤: 強干擾選項混淆",
    'RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING': "RC 方法錯誤: 特定題型處理錯誤",

    'RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK': "RC 閱讀理解障礙: 詞彙量瓶頸",
    'RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS': "RC 閱讀理解障礙: 長難句解析困難",
    'RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR': "RC 閱讀理解障礙: 篇章結構把握不清",
    'RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK': "RC 閱讀理解障礙: 特定領域背景知識缺乏",
    'RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP': "RC 題目理解障礙: 提問焦點把握困難",
    'RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY': "RC 定位能力障礙: 定位效率低下",
    'RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW': "RC 推理障礙: 推理速度緩慢",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB': "RC 選項辨析障礙: 選項詞彙理解困難",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX': "RC 選項辨析障礙: 選項句式理解困難",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC': "RC 選項辨析障礙: 選項邏輯理解困難",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN': "RC 選項辨析障礙: 選項領域理解困難",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT': "RC 選項辨析障礙: 選項相關性判斷困難",
    'RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS': "RC 選項辨析障礙: 強干擾選項辨析困難",
    'RC_METHOD_DIFFICULTY_SPECIFIC_QUESTION_TYPE_HANDLING': "RC 方法障礙: 特定題型處理困難",

    # --- Other existing V-Doc Appendix A Parameters (Potentially legacy or for other uses, preserved) ---
    'CR_READING_BASIC_OMISSION': "CR 閱讀理解: 基礎理解疏漏", # Kept from original if not in MD
    'CR_READING_TIME_EXCESSIVE': "CR 閱讀理解: 閱讀耗時過長", # Kept from original
    'CR_REASONING_TIME_EXCESSIVE': "CR 推理障礙: 邏輯思考耗時過長", # Kept from original
    'CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY': "CR 選項辨析: 選項本身理解困難", # Kept from original
    'CR_AC_ANALYSIS_RELEVANCE_ERROR': "CR 選項辨析: 選項相關性判斷錯誤", # Kept from original
    'CR_AC_ANALYSIS_DISTRACTOR_CONFUSION': "CR 選項辨析: 強干擾選項混淆", # Kept from original
    'CR_AC_ANALYSIS_TIME_EXCESSIVE': "CR 選項辨析: 選項篩選耗時過長", # Kept from original
    'CR_METHOD_PROCESS_DEVIATION': "CR 方法應用: 未遵循標準流程", # Kept from original
    'RC_READING_KEYWORD_LOGIC_OMISSION': "RC 閱讀理解: 忽略關鍵詞/邏輯", # Kept from original
    'RC_READING_SPEED_SLOW_FOUNDATIONAL': "RC 閱讀理解: 閱讀速度慢 (基礎問題)", # Kept from original
    'RC_READING_PRECISION_INSUFFICIENT': "RC 閱讀精度不足 (精讀/定位問題)", # Kept from original
    'RC_READING_COMPREHENSION_BARRIER': "RC 閱讀理解: 閱讀理解障礙 (耗時過長觸發)", # Kept from original
    'RC_METHOD_INEFFICIENT_READING': "RC 閱讀方法: 閱讀方法效率低 (過度精讀)", # Kept from original
    'RC_QUESTION_UNDERSTANDING_MISINTERPRETATION': "RC 題目理解: 提問焦點把握錯誤", # Kept from original
    'RC_LOCATION_TIME_EXCESSIVE': "RC 定位能力: 定位效率低下 (反覆定位)", # Kept from original
    'RC_REASONING_TIME_EXCESSIVE': "RC 推理障礙: 深度思考耗時過長", # Kept from original
    'RC_AC_ANALYSIS_DIFFICULTY': "RC 選項辨析: 選項理解/辨析困難 (含義/對應)", # Kept from original
    'RC_AC_ANALYSIS_TIME_EXCESSIVE': "RC 選項辨析: 選項篩選耗時過長", # Kept from original
    # 'RC_METHOD_TYPE_SPECIFIC_ERROR' was in MD, so it's updated above.
    'EFFICIENCY_BOTTLENECK_READING': "效率問題: 閱讀理解環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_REASONING': "效率問題: 推理分析環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_LOCATION': "效率問題: 信息定位環節導致效率低下",
    'EFFICIENCY_BOTTLENECK_AC_ANALYSIS': "效率問題: 選項辨析環節導致效率低下",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    # 'BEHAVIOR_GUESSING_HASTY' is updated from MD

    # --- RC整組表現相關診斷參數翻譯 ---
    'RC_READING_SPEED_GOOD_GROUP_PERFORMANCE': "RC 閱讀速度: 整組表現良好",
    'RC_READING_SPEED_ACCEPTABLE_GROUP_PERFORMANCE': "RC 閱讀速度: 整組表現尚可",
    'RC_READING_SPEED_POOR_GROUP_PERFORMANCE': "RC 閱讀速度: 整組表現不佳",
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MINOR_ISSUE': "RC 時間管理: 單題效率輕微問題",
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MODERATE_ISSUE': "RC 時間管理: 單題效率中度問題",
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_MAJOR_ISSUE': "RC 時間管理: 單題效率嚴重問題",
    'RC_TIMING_INDIVIDUAL_QUESTION_EFFICIENCY_SEVERE_ISSUE': "RC 時間管理: 單題效率極嚴重問題",
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MINOR_ISSUE': "RC 選項辨析: 效率輕微問題",
    'RC_CHOICE_ANALYSIS_EFFICIENCY_MODERATE_ISSUE': "RC 選項辨析: 效率中度問題",

    # --- VDOC Defined Core Fundamental Skills --- (Preserved)
    'Plan/Construct': "Plan/Construct",
    'Identify Stated Idea': "Identify Stated Idea",
    'Identify Inferred Idea': "Identify Inferred Idea",
    'Analysis/Critique': "Analysis/Critique",

    # --- Internal Codes --- (Preserved)
    "Low / 505+": "低難度 (Low) / 505+",
    "Mid / 555+": "中難度 (Mid) / 555+",
    "Mid / 605+": "中難度 (Mid) / 605+",
    "Mid / 655+": "中難度 (Mid) / 655+",
    "High / 705+": "高難度 (High) / 705+",
    "High / 805+": "高難度 (High) / 805+",
    "Unknown Difficulty": "未知難度",
    'Unknown Skill': "未知技能",
    'Y': "薄弱技能",
    'Y-SFE': "薄弱技能 (高 SFE)",
    'Z': "考察不足",
    'X': "基本掌握 (豁免)",
    'OK': "表現正常",
    'High': "高",
    'Low': "低",
    'Unknown': "未知",
    'Reading/Understanding': "閱讀理解",
    'Logic/Reasoning': "邏輯推理",
    'Inference/Application': "推理應用",
    'Method/Process': "方法/流程",
    'Behavioral': "行為模式",
    'Mixed/Other': "混合/其他",
    'N/A': '不適用',
    'Fast & Wrong': "快錯",
    'Slow & Wrong': "慢錯",
    'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對",
    'Fast & Correct': "快對",
    'Normal Time & Correct': "正常時間 & 對",
    'SFE': '基礎掌握',
    'Reading': '閱讀理解',
    'Reasoning': '邏輯推理',
    'Timing': '時間管理',
    'Process': '流程方法',
    'AC_Analysis': '選項分析',
    'Question_Understanding': '問題理解',
    INVALID_DATA_TAG_V: "數據無效：用時過短"
}

def translate_v(param):
    """Translates V diagnostic parameter/term to Chinese, returning original if not found or explicitly mapped to English."""
    # Removed special handling for skills_to_keep_english to ensure all translations come from APPENDIX_A_TRANSLATION_V
    return APPENDIX_A_TRANSLATION_V.get(param, param) # Default to original if not in map at all 