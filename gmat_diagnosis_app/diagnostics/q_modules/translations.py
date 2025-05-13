"""
Q診斷模塊的翻譯功能

此模塊包含用於Q(Quantitative)診斷的翻譯字典和相關函數，
用於在診斷過程中將英文術語翻譯為中文。
"""

# --- Q Appendix A Translation ---
APPENDIX_A_TRANSLATION = {
    'Q_READING_COMPREHENSION_ERROR': "Q 閱讀理解錯誤：題目文字理解",
    'Q_CONCEPT_APPLICATION_ERROR': "Q 概念應用錯誤：數學觀念/公式應用",
    'Q_CALCULATION_ERROR': "Q 計算錯誤：數學計算",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Q 基礎掌握：應用不穩定（Special Focus Error）",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式：前期作答過快（Flag risk）",
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式：整體粗心問題（快而錯比例高）",
    'Q_READING_COMPREHENSION_DIFFICULTY': "Q 閱讀理解障礙：題目文字理解困難",
    'Q_CONCEPT_APPLICATION_DIFFICULTY': "Q 概念應用障礙：數學觀念/公式應用困難",
    'Q_CALCULATION_DIFFICULTY': "Q 計算障礙：數學計算困難",
    'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED': "Q 閱讀理解障礙：心態失常讀不進去",
}

def get_translation(param):
    """Helper to get Chinese description, returns param name if not found."""
    return APPENDIX_A_TRANSLATION.get(param, param) 