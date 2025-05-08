"""
Q科AI工具與提示建議生成模組

此模塊生成基於Q科標籤的AI工具和提示建議。
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS
from gmat_diagnosis_app.diagnostics.q_modules.translations import APPENDIX_A_TRANSLATION

def translate_zh_to_en(zh_tag: str) -> str:
    """
    將中文標籤轉換為英文標籤
    
    Args:
        zh_tag (str): 中文標籤
    
    Returns:
        str: 對應的英文標籤，如果找不到則返回原標籤
    """
    # 構建反向映射字典 (中文 -> 英文)
    reverse_translation = {v: k for k, v in APPENDIX_A_TRANSLATION.items()}
    
    # 嘗試查找完全匹配的中文標籤
    if zh_tag in reverse_translation:
        return reverse_translation[zh_tag]
    
    # 嘗試部分匹配 (中文標籤可能只是完整翻譯的一部分)
    for zh, en in reverse_translation.items():
        if zh_tag in zh:
            return en
    
    # 如果沒有匹配到，返回原始標籤
    return zh_tag

def generate_q_ai_tool_recommendations(df_q: pd.DataFrame) -> str:
    """
    根據Q科診斷標籤生成AI工具和提示建議
    
    Args:
        df_q (pd.DataFrame): 包含Q科目診斷標籤的數據框
    
    Returns:
        str: 格式化的AI工具和提示建議文本
    """
    if df_q.empty:
        return "(無數據可供分析)"
    
    # 收集所有診斷標籤
    all_tags = []
    for tags_list in df_q['diagnostic_params_list'].dropna():
        if isinstance(tags_list, list):
            all_tags.extend(tags_list)
    
    # 如果沒有標籤，返回空
    if not all_tags:
        return "(未找到診斷標籤)"
    
    # 計算每個標籤的出現頻率
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # 找出所有匹配常量中定義的診斷標籤
    recommendations = []
    matched_tags = []
    
    # 遍歷標籤，先翻譯再查找推薦
    for zh_tag, count in tag_counts.items():
        # 將中文標籤轉換為英文標籤
        en_tag = translate_zh_to_en(zh_tag)
        
        # 檢查英文標籤是否與Q_TOOL_AI_RECOMMENDATIONS中的鍵匹配
        for recommendation_key in Q_TOOL_AI_RECOMMENDATIONS:
            if en_tag.upper() == recommendation_key or en_tag in recommendation_key or recommendation_key in en_tag.upper():
                matched_tools = Q_TOOL_AI_RECOMMENDATIONS[recommendation_key]
                # 保存匹配的標籤(保留中文顯示)、推薦工具和出現次數
                matched_tags.append((zh_tag, matched_tools, count))
                break
    
    # 根據標籤出現頻率排序
    matched_tags.sort(key=lambda x: x[2], reverse=True)
    
    # 生成推薦文本
    already_recommended = set()  # 用於追踪已經推薦的工具，避免重複
    
    for tag, tools, count in matched_tags:
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
        return "未找到特定匹配的工具建議。建議參考GMAT官方指南中的Q科相關練習和策略。"
    
    # 將所有推薦組合為一個字符串
    return "\n".join(recommendations) 