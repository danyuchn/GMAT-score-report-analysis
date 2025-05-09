"""
Q診斷模塊的翻譯功能

此模塊包含用於Q(Quantitative)診斷的翻譯字典和相關函數，
用於在診斷過程中將英文術語翻譯為中文。
"""

# --- Q Appendix A Translation ---
APPENDIX_A_TRANSLATION = {
    'Q_READING_COMPREHENSION_ERROR': "Quant 閱讀理解: Real 題文字理解錯誤/障礙",
    'Q_PROBLEM_UNDERSTANDING_ERROR': "Quant 題目理解: 數學問題本身理解錯誤",
    'Q_CONCEPT_APPLICATION_ERROR': "Quant 概念應用: 數學觀念/公式應用錯誤/障礙",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Quant 基礎掌握: 應用不穩定 (Special Focus Error)",
    'Q_CALCULATION_ERROR': "Quant 計算: 計算錯誤/障礙",
    'Q_EFFICIENCY_BOTTLENECK_READING': "Quant 效率瓶頸: Real 題閱讀耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': "Quant 效率瓶頸: 概念/公式思考或導出耗時過長",
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': "Quant 效率瓶頸: 計算過程耗時過長/反覆計算",
    'Q_CARELESSNESS_DETAIL_OMISSION': "行為模式: 粗心 - 忽略細節/條件/陷阱",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 整體粗心問題 (快而錯比例高)",
    'poor_real': "比較表現: Real 題錯誤率顯著偏高",
    'poor_pure': "比較表現: Pure 題錯誤率顯著偏高",
    'slow_real': "比較表現: Real 題超時率顯著偏高",
    'slow_pure': "比較表現: Pure 題超時率顯著偏高",
    'skill_override_triggered': "技能覆蓋: 某核心技能整體表現需基礎鞏固 (錯誤率或超時率>50%)"
}

def get_translation(param):
    """Helper to get Chinese description, returns param name if not found."""
    return APPENDIX_A_TRANSLATION.get(param, param) 