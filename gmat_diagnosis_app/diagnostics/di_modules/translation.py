# --- DI Appendix A Translation ---
APPENDIX_A_TRANSLATION_DI = {
    # DI - Reading & Understanding
    'DI_READING_COMPREHENSION_ERROR': "DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math)",
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': "DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙",
    # DI - Concept & Application (Math)
    'DI_CONCEPT_APPLICATION_ERROR': "DI 概念應用 (Math): 數學觀念/公式應用錯誤/障礙",
    # DI - Logical Reasoning (Non-Math)
    'DI_LOGICAL_REASONING_ERROR': "DI 邏輯推理 (Non-Math): 題目內在邏輯推理/判斷錯誤",
    # DI - Data Handling & Calculation
    'DI_DATA_EXTRACTION_ERROR': "DI 數據提取 (GT): 從圖表中提取數據錯誤",
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': "DI 信息提取/推斷 (GT/MSR Non-Math): 信息定位/推斷錯誤",
    'DI_CALCULATION_ERROR': "DI 計算: 數學計算錯誤/障礙",
    # DI - MSR Specific
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': "DI 多源整合 (MSR): 跨分頁/來源信息整合錯誤/障礙",
    'DI_MSR_READING_COMPREHENSION_BARRIER': "DI MSR 閱讀障礙: 題組整體閱讀時間過長",
    'DI_MSR_SINGLE_Q_BOTTLENECK': "DI MSR 單題瓶頸: 題組內單題回答時間過長",
    # DI - Question Type Specific
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': "DI 特定題型障礙 (例如 MSR Non-Math 子題型)",
    # DI - Foundational & Efficiency
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "DI 基礎掌握: 應用不穩定 (Special Focus Error)",
    'DI_EFFICIENCY_BOTTLENECK_READING': "DI 效率瓶頸: 閱讀理解耗時 (Math/Non-Math)",
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': "DI 效率瓶頸: 概念/公式應用耗時 (Math)",
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': "DI 效率瓶頸: 計算耗時",
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': "DI 效率瓶頸: 邏輯推理耗時 (Non-Math)",
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': "DI 效率瓶頸: 圖表解讀耗時",
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': "DI 效率瓶頸: 多源信息整合耗時 (MSR)",
    # DI - Behavior
    'DI_CARELESSNESS_DETAIL_OMISSION': "DI 行為: 粗心 - 細節忽略/看錯 (快錯時隱含)",
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': "DI 行為: 粗心 - 整體快錯率偏高",
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "DI 行為: 測驗前期作答過快風險",
    # Domains
    'Math Related': "數學相關",
    'Non-Math Related': "非數學相關",
    'Unknown Domain': "未知領域",
    # Time Pressure
    'High': "高", 'Low': "低", 'Unknown': "未知",
    'True': "有時間壓力", 'False': "無時間壓力",
    # Question Types
    'Data Sufficiency': 'Data Sufficiency', 'Two-part analysis': 'Two-part analysis',
    'Multi-source reasoning': 'Multi-source reasoning', 'Graph and Table': 'Graph and Table',
    'Unknown Type': '未知類型',
    # Time Performance Categories
    'Fast & Wrong': "快錯", 'Slow & Wrong': "慢錯", 'Normal Time & Wrong': "正常時間 & 錯",
    'Slow & Correct': "慢對", 'Fast & Correct': "快對", 'Normal Time & Correct': "正常時間 & 對",
    'Unknown': "未知", 'Invalid/Excluded': "已排除/無效",
    # Parameter Categories
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
    'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': 'SFE',
    'DI_READING_COMPREHENSION_ERROR': 'Reading/Interpretation',
    'DI_GRAPH_TABLE_INTERPRETATION_ERROR': 'Reading/Interpretation',
    'DI_CONCEPT_APPLICATION_ERROR': 'Concept/Application',
    'DI_DATA_EXTRACTION_ERROR': 'Data/Calculation',
    'DI_INFORMATION_EXTRACTION_INFERENCE_ERROR': 'Data/Calculation',
    'DI_CALCULATION_ERROR': 'Data/Calculation',
    'DI_LOGICAL_REASONING_ERROR': 'Logic/Reasoning',
    'DI_QUESTION_TYPE_SPECIFIC_ERROR': 'Logic/Reasoning', # Or specific category?
    'DI_MULTI_SOURCE_INTEGRATION_ERROR': 'Multi-Source',
    'DI_MSR_READING_COMPREHENSION_BARRIER': 'Multi-Source', # Or Efficiency? Let's keep Multi-Source
    'DI_MSR_SINGLE_Q_BOTTLENECK': 'Multi-Source', # Or Efficiency? Let's keep Multi-Source
    'DI_EFFICIENCY_BOTTLENECK_READING': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CONCEPT': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_CALCULATION': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_LOGIC': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE': 'Efficiency',
    'DI_EFFICIENCY_BOTTLENECK_INTEGRATION': 'Efficiency',
    'DI_CARELESSNESS_DETAIL_OMISSION': 'Carelessness',
    'DI_BEHAVIOR_CARELESSNESS_ISSUE': 'Behavioral',
    'DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': 'Behavioral'
}

def _translate_di(param):
    """Translates an internal DI param/skill name using APPENDIX_A_TRANSLATION_DI."""
    if isinstance(param, list):
        return [APPENDIX_A_TRANSLATION_DI.get(p, str(p)) for p in param if isinstance(p, str)]
    elif isinstance(param, str):
         return APPENDIX_A_TRANSLATION_DI.get(param, param)
    elif isinstance(param, bool):
         return APPENDIX_A_TRANSLATION_DI.get(str(param), str(param))
    else:
         return str(param) 