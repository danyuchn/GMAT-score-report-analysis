#!/usr/bin/env python3
"""
測試AI工具推薦翻譯功能的專用腳本
主要驗證之前記憶檔案中提到的問題是否已修正
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmat_diagnosis_app.utils.route_tool import DiagnosisRouterTool

def test_ai_tool_recommendations():
    """測試AI工具推薦翻譯功能"""
    print("=== AI工具推薦翻譯功能測試 ===")
    
    # 初始化診斷路由工具
    router = DiagnosisRouterTool()
    
    # 測試案例：之前出現問題的英文標籤
    test_tags = [
        "Mathematical Concept/Formula Application Difficulty",
        "Mathematical Calculation Difficulty", 
        "CR Stem Understanding Error: Question Requirement Grasp",
        "DI Reading Comprehension Difficulty: Mental Block Unable to Read",
        "Q Concept Application Error: Mathematical Concept/Formula Application",
        "Q Calculation Error: Mathematical Calculation",
        "中文測試標籤",  # 測試中文標籤
        "Data Sufficiency"  # 測試一般英文標籤
    ]
    
    print("\n測試各種診斷標籤的翻譯結果：")
    print("-" * 60)
    
    for tag in test_tags:
        print(f"\n輸入標籤: {tag}")
        
        # 測試翻譯功能
        try:
            translated = router.translate_zh_to_en(tag)
            print(f"翻譯結果: {translated}")
            
            # 測試是否能找到對應的工具推薦
            from gmat_diagnosis_app.diagnostics.q_modules.constants import Q_TOOL_AI_RECOMMENDATIONS
            
            if translated in Q_TOOL_AI_RECOMMENDATIONS:
                recommendations = Q_TOOL_AI_RECOMMENDATIONS[translated]
                print(f"工具推薦: 找到 {len(recommendations)} 項推薦")
                for i, rec in enumerate(recommendations[:2], 1):  # 只顯示前2項
                    print(f"  {i}. {rec[:50]}{'...' if len(rec) > 50 else ''}")
            else:
                print("工具推薦: 暫無對應的工具推薦")
                
        except Exception as e:
            print(f"錯誤: {e}")
        
        print("-" * 40)
    
    print("\n=== 特殊映射測試 ===")
    # 測試特殊映射是否正常工作
    special_test_cases = [
        ("Mathematical Concept/Formula Application Difficulty", "Q_CONCEPT_APPLICATION_DIFFICULTY"),
        ("Mathematical Calculation Difficulty", "Q_CALCULATION_DIFFICULTY"),
        ("CR Stem Understanding Error: Question Requirement Grasp", "CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP")
    ]
    
    for input_tag, expected_output in special_test_cases:
        actual_output = router.translate_zh_to_en(input_tag)
        status = "✅ PASS" if actual_output == expected_output else "❌ FAIL"
        print(f"{status} - {input_tag} → {actual_output}")
        if actual_output != expected_output:
            print(f"      預期: {expected_output}")
    
    print("\n=== 模糊匹配限制測試 ===")
    # 測試模糊匹配是否正確限制在中文文本
    chinese_text = "數學概念應用困難"
    english_text = "Mathematical Concept Application"
    
    print(f"中文文本測試: {chinese_text}")
    chinese_result = router.translate_zh_to_en(chinese_text)
    print(f"結果: {chinese_result}")
    
    print(f"英文文本測試: {english_text}")
    english_result = router.translate_zh_to_en(english_text)
    print(f"結果: {english_result}")

if __name__ == "__main__":
    test_ai_tool_recommendations() 