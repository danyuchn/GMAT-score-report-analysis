"""
Q診斷模塊的翻譯功能 (已棄用)

此模塊包含用於Q(Quantitative)診斷的翻譯字典和相關函數。
已棄用：請使用新的i18n系統 (gmat_diagnosis_app.i18n)
"""

import warnings

# --- Q Appendix A Translation (DEPRECATED) ---
# 已棄用：請使用 gmat_diagnosis_app.i18n 系統
APPENDIX_A_TRANSLATION = {
    'Q_READING_COMPREHENSION_ERROR': "Q 閱讀理解錯誤：題目文字理解",
    'Q_CONCEPT_APPLICATION_ERROR': "Q 概念應用錯誤：數學觀念/公式應用",
    'Q_CALCULATION_ERROR': "Q 計算錯誤：數學計算",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Q 基礎掌握：應用不穩定（Special Focus Error）",
    'Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'Q_BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    'Q_READING_COMPREHENSION_DIFFICULTY': "Q 閱讀理解障礙：題目文字理解困難",
    'Q_CONCEPT_APPLICATION_DIFFICULTY': "Q 概念應用障礙：數學觀念/公式應用困難",
    'Q_CALCULATION_DIFFICULTY': "Q 計算障礙：數學計算困難",
    'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED': "Q 閱讀理解障礙：心態失常讀不進去",
}

def get_translation(param):
    """
    Helper to get Chinese description, returns param name if not found.
    
    DEPRECATED: This function is deprecated. Please use the new i18n system:
    
    from gmat_diagnosis_app.i18n import translate as t
    translated_text = t(param)
    
    Args:
        param (str): Parameter key to translate
        
    Returns:
        str: Translated text or original param if not found
    """
    warnings.warn(
        "get_translation() is deprecated. Use 'from gmat_diagnosis_app.i18n import translate as t' instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Fallback to old translation for backward compatibility
    return APPENDIX_A_TRANSLATION.get(param, param) 