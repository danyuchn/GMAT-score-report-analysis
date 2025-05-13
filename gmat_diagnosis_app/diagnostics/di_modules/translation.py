# --- DI Appendix A Translation ---
APPENDIX_A_TRANSLATION_DI = {
    # Fast & Wrong / Normal Time & Wrong (Error-based)
    'DI_READING_COMPREHENSION_ERROR__VOCABULARY': "DI 閱讀理解錯誤: 詞彙理解",
    'DI_READING_COMPREHENSION_ERROR__SYNTAX': "DI 閱讀理解錯誤: 句式理解",
    'DI_READING_COMPREHENSION_ERROR__LOGIC': "DI 閱讀理解錯誤: 邏輯理解",
    'DI_READING_COMPREHENSION_ERROR__DOMAIN': "DI 閱讀理解錯誤: 領域理解",
    'DI_GRAPH_INTERPRETATION_ERROR__GRAPH': "DI 圖表解讀錯誤: 圖形信息解讀",
    'DI_GRAPH_INTERPRETATION_ERROR__TABLE': "DI 圖表解讀錯誤: 表格信息解讀",
    'DI_CONCEPT_APPLICATION_ERROR__MATH': "DI 概念應用 (數學) 錯誤: 數學觀念/公式應用",
    'DI_LOGICAL_REASONING_ERROR__NON_MATH': "DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷",
    'DI_CALCULATION_ERROR__MATH': "DI 計算錯誤 (數學): 數學計算",
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': "DI 多源整合 (MSR): 跨分頁/來源信息整合障礙", # Primarily for Normal Time & Wrong and Slow & Wrong
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE': "DI 基礎掌握: 應用不穩定 (Special Focus Error)",
    'DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION': "DI 行為: 粗心 - 細節忽略/看錯",
    'DI_BEHAVIOR__CARELESSNESS_ISSUE': "DI 行為: 粗心 - 整體快錯率偏高",
    'DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK': "DI 行為: 測驗前期作答過快風險",

    # Slow & Wrong / Slow & Correct (Difficulty/Barrier-based)
    'DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION': "DI 閱讀理解障礙: 跨分頁/來源信息整合困難",
    'DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY': "DI 閱讀理解障礙: 詞彙理解困難",
    'DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX': "DI 閱讀理解障礙: 句式理解困難",
    'DI_READING_COMPREHENSION_DIFFICULTY__LOGIC': "DI 閱讀理解障礙: 邏輯理解困難",
    'DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN': "DI 閱讀理解障礙: 領域理解困難",
    'DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH': "DI 圖表解讀障礙: 圖形信息解讀困難",
    'DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE': "DI 圖表解讀障礙: 表格信息解讀困難",
    'DI_CONCEPT_APPLICATION_DIFFICULTY__MATH': "DI 概念應用 (數學) 障礙: 數學觀念/公式應用困難",
    'DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH': "DI 邏輯推理 (非數學) 障礙: 題目內在邏輯推理/判斷困難",
    'DI_CALCULATION_DIFFICULTY__MATH': "DI 計算 (數學) 障礙: 數學計算困難",
    'DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED': "DI 閱讀理解障礙: 心態失常讀不進去",

    # Domains, Time Pressure, Question Types, Time Performance Categories, Parameter Categories
    'Math Related': "數學相關",
    'Non-Math Related': "非數學相關",
    'Unknown Domain': "未知領域",
    'High': "高", 'Low': "低", 'Unknown': "未知",
    'True': "有時間壓力", 'False': "無時間壓力",
    'Data Sufficiency': 'Data Sufficiency', 'Two-part analysis': 'Two-part analysis',
    'Multi-source reasoning': 'Multi-source reasoning', 'Graph and Table': 'Graph and Table',
    'Unknown Type': '未知類型',
    'Fast & Wrong': "快錯", 'Slow & Wrong': "慢錯", 'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對", 'Fast & Correct': "快對", 'Normal Time & Correct': "正常時間 & 對",
    'Unknown': "未知", 'Invalid/Excluded': "已排除/無效",
    'SFE': '基礎掌握', 'Reading/Interpretation': '閱讀/解讀', 'Concept/Application': '概念/應用',
    'Data/Calculation': '數據/計算', 'Logic/Reasoning': '邏輯/推理', 'Multi-Source': '多源整合',
    'Efficiency': '效率問題', 'Carelessness': '粗心問題', 'Behavioral': '行為模式', 'Unknown': '未分類',
}

# --- Parameter Categories for Report Grouping (DI) --- Updated ---
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
    'DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION': 'Carelessness',
    'DI_BEHAVIOR__CARELESSNESS_ISSUE': 'Behavioral',
    'DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK': 'Behavioral'
}

def _translate_di(param):
    """Translates an internal DI param/skill name using APPENDIX_A_TRANSLATION_DI."""
    result = ""
    if isinstance(param, list):
        result = [APPENDIX_A_TRANSLATION_DI.get(p, str(p)) for p in param if isinstance(p, str)]
    elif isinstance(param, str):
         result = APPENDIX_A_TRANSLATION_DI.get(param, param)
    elif isinstance(param, bool):
         result = APPENDIX_A_TRANSLATION_DI.get(str(param), str(param))
    else:
         result = str(param)
         
    return result 