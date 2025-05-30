"""
Q科AI工具與提示建議生成模組

此模塊生成基於Q科標籤的AI工具和提示建議。
使用新的診斷路由工具進行標籤匹配和建議生成。
"""

import pandas as pd
from gmat_diagnosis_app.utils.route_tool import DiagnosisRouterTool
from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS
# Use i18n system instead of the old translation dictionary
from gmat_diagnosis_app.i18n import translate as t, get_available_languages
from collections import Counter


def translate_chinese_to_english_tag(zh_tag: str) -> str:
    """
    將中文標籤轉換為英文標籤 (保留作為模糊匹配的備選方案)
    
    Args:
        zh_tag (str): 中文標籤
    
    Returns:
        str: 對應的英文標籤，如果找不到則返回原標籤
    """
    # Build reverse mapping dictionary using i18n system
    # Get all available translations from i18n system
    from gmat_diagnosis_app.i18n.translations.zh_TW import TRANSLATIONS as ZH_TRANSLATIONS
    from gmat_diagnosis_app.i18n.translations.en import TRANSLATIONS as EN_TRANSLATIONS
    
    # Create reverse mapping (Chinese -> English key)
    reverse_translation = {}
    for key in ZH_TRANSLATIONS:
        if key in EN_TRANSLATIONS:
            zh_text = ZH_TRANSLATIONS[key]
            reverse_translation[zh_text] = key
    
    # Try to find exact match for Chinese tag
    if zh_tag in reverse_translation:
        return reverse_translation[zh_tag]
    
    # Try partial match (Chinese tag might be part of complete translation)
    for zh, en_key in reverse_translation.items():
        if zh_tag in zh:
            return en_key
    
    # If no match found, return original tag
    return zh_tag


def generate_q_ai_tool_recommendations_fallback(df_q):
    """
    使用原有方法生成建議 (作為備選方案)
    
    Args:
        df_q (pd.DataFrame): 包含Q科目診斷標籤的數據框
        
    Returns:
        str: 格式化的AI工具和提示建議文本
    """
    if df_q is None or df_q.empty:
        return t('no_data_for_analysis')
    
    # 收集所有診斷標籤
    all_tags = []
    if 'diagnostic_params_list' in df_q.columns:
        for tag_list in df_q['diagnostic_params_list']:
            if isinstance(tag_list, list):
                all_tags.extend(tag_list)
    
    # 如果沒有標籤，返回空
    if not all_tags:
        return t('no_diagnostic_tags_found')
    
    # 計算每個標籤的出現頻率
    tag_counts = Counter(all_tags)
    
    # 找出所有匹配常量中定義的診斷標籤
    matched_recommendations = []
    
    # 遍歷標籤，先翻譯再查找推薦
    for tag, count in tag_counts.items():
        # 將中文標籤轉換為英文標籤
        english_tag = translate_chinese_to_english_tag(tag)
        
        # 檢查英文標籤是否與Q_TOOL_AI_RECOMMENDATIONS中的鍵匹配
        if english_tag in Q_TOOL_AI_RECOMMENDATIONS:
            recommendations = Q_TOOL_AI_RECOMMENDATIONS[english_tag]
            # 保存匹配的標籤(保留中文顯示)、推薦工具和出現次數
            matched_recommendations.append((tag, recommendations, count))
    
    # 根據標籤出現頻率排序
    matched_recommendations.sort(key=lambda x: x[2], reverse=True)
    
    # 生成推薦文本
    already_recommended = set()  # 用於追踪已經推薦的工具，避免重複
    
    for tag, tools, count in matched_recommendations:
        recommendation_text = f"**{tag}** (出現{count}次):\n"
        
        tools_added = False
        for tool in tools:
            if tool not in already_recommended:
                if tool.startswith("Tool:"):
                    recommendation_text += f"- {tool}\n"
                elif tool.startswith("AI:") or tool.startswith("AI Prompt:"):
                    recommendation_text += f"- {tool}\n"
                else:
                    recommendation_text += f"- {tool}\n"
                already_recommended.add(tool)
                tools_added = True
        
        if tools_added:
            recommendations.append(recommendation_text)
    
    # 如果沒有匹配的推薦，提供一個通用建議
    if not recommendations:
        return t('general_gmat_q_tool_suggestion')
    
    # 將所有推薦組合為一個字符串
    return "\n".join(recommendations)


def generate_q_ai_tool_recommendations(df_q: pd.DataFrame) -> str:
    """
    根據Q科診斷標籤生成AI工具和提示建議
    使用新的診斷路由工具進行匹配
    
    Args:
        df_q (pd.DataFrame): 包含Q科目診斷標籤的數據框
    
    Returns:
        str: 格式化的AI工具和提示建議文本
    """
    # 初始化路由工具
    router = DiagnosisRouterTool()
    
    try:
        # 使用新的路由工具生成建議
        recommendations = router.generate_recommendations_from_dataframe(df_q, "Q")
        
        # 如果新方法沒有找到足夠的建議，嘗試舊方法作為備選
        if recommendations == "(未找到診斷標籤)" or recommendations.startswith("未找到特定匹配"):
            legacy_recommendations = generate_q_ai_tool_recommendations_fallback(df_q)
            if not legacy_recommendations.startswith("未找到特定匹配") and legacy_recommendations != "(未找到診斷標籤)":
                recommendations = f"**使用新路由系統生成的建議：**\n{recommendations}\n\n**補充建議（基於舊系統）：**\n{legacy_recommendations}"
        
        return recommendations
        
    except Exception as e:
        # 如果新系統出現錯誤，回退到舊系統
        import logging
        logging.warning(f"New route tool failed for Q subject: {str(e)}, falling back to legacy method")
        return generate_q_ai_tool_recommendations_fallback(df_q) 