#!/usr/bin/env python3
"""
測試新的路由工具集成

此腳本測試 gmat_route_tool.py 功能是否成功集成到診斷應用中
"""

import pandas as pd
import sys
import traceback

def test_route_tool():
    """測試路由工具基本功能"""
    print("=== 測試路由工具基本功能 ===")
    try:
        from gmat_diagnosis_app.utils.route_tool import DiagnosisRouterTool
        
        router = DiagnosisRouterTool()
        
        # 測試可用類別
        categories = router.get_available_categories()
        print(f"可用類別: {categories}")
        
        # 測試一些典型標籤的路由
        test_cases = [
            ("Q_CONCEPT_APPLICATION_ERROR", "Q"),
            ("CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP", "V"),
            ("RC_READING_COMPREHENSION_ERROR_VOCAB", "V"),
            ("DI_READING_COMPREHENSION_ERROR__VOCABULARY", "DI"),
            ("DI_GRAPH_INTERPRETATION_ERROR__GRAPH", "DI"),
            ("DI_CONCEPT_APPLICATION_ERROR__MATH", "DI"),
        ]
        
        for tag, subject in test_cases:
            commands = router.route_diagnosis_tag(tag, subject)
            category = router.determine_category_from_tag(tag, subject)
            print(f"\n標籤: {tag}")
            print(f"分類: {category}")
            print(f"建議命令 (前3個): {commands[:3]}")
        
        print("\n✅ 路由工具基本功能測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 路由工具測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_q_module():
    """測試 Q 科目 AI 建議生成"""
    print("\n=== 測試 Q 科目 AI 建議生成 ===")
    try:
        from gmat_diagnosis_app.diagnostics.q_modules.ai_prompts import generate_q_ai_tool_recommendations
        
        # 創建測試數據
        test_df = pd.DataFrame({
            'diagnostic_params_list': [
                ['Q_CONCEPT_APPLICATION_ERROR'],
                ['Q_CALCULATION_ERROR'],
                ['Q_READING_COMPREHENSION_DIFFICULTY']
            ]
        })
        
        result = generate_q_ai_tool_recommendations(test_df)
        
        print("Q 科目建議結果 (前500字符):")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # 檢查是否包含預期的命令
        expected_commands = ["Questions you did wrong", "Learn math concepts"]
        found_commands = [cmd for cmd in expected_commands if cmd in result]
        
        if found_commands:
            print(f"\n✅ Q 科目測試通過，找到命令: {found_commands}")
            return True
        else:
            print(f"❌ Q 科目測試失敗，未找到預期命令: {expected_commands}")
            return False
            
    except Exception as e:
        print(f"❌ Q 科目測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_v_module():
    """測試 V 科目 AI 建議生成"""
    print("\n=== 測試 V 科目 AI 建議生成 ===")
    try:
        from gmat_diagnosis_app.diagnostics.v_modules.ai_prompts import generate_v_ai_tool_recommendations
        
        # 創建測試數據
        test_df = pd.DataFrame({
            'diagnostic_params_list': [
                ['CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP'],
                ['RC_READING_COMPREHENSION_ERROR_VOCAB'],
                ['CR_STEM_UNDERSTANDING_ERROR_VOCAB']
            ]
        })
        
        result = generate_v_ai_tool_recommendations(test_df)
        
        print("V 科目建議結果 (前500字符):")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # 檢查是否包含預期的命令
        expected_commands = ["Questions you did wrong", "Logical Chain Builder", "Memorizing Vocabularies"]
        found_commands = [cmd for cmd in expected_commands if cmd in result]
        
        if found_commands:
            print(f"\n✅ V 科目測試通過，找到命令: {found_commands}")
            return True
        else:
            print(f"❌ V 科目測試失敗，未找到預期命令: {expected_commands}")
            return False
            
    except Exception as e:
        print(f"❌ V 科目測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def test_di_module():
    """測試 DI 科目 AI 建議生成"""
    print("\n=== 測試 DI 科目 AI 建議生成 ===")
    try:
        from gmat_diagnosis_app.diagnostics.di_modules.ai_prompts import generate_di_ai_tool_recommendations
        
        # 創建測試數據
        test_df = pd.DataFrame({
            'diagnostic_params_list': [
                ['DI_READING_COMPREHENSION_ERROR__VOCABULARY'],
                ['DI_GRAPH_INTERPRETATION_ERROR__GRAPH'],
                ['DI_CONCEPT_APPLICATION_ERROR__MATH']
            ]
        })
        
        result = generate_di_ai_tool_recommendations(test_df)
        
        print("DI 科目建議結果 (前500字符):")
        print(result[:500] + "..." if len(result) > 500 else result)
        
        # 檢查是否包含預期的命令
        expected_commands = ["Questions you did wrong", "Learn Math Concept", "Sentence cracker"]
        found_commands = [cmd for cmd in expected_commands if cmd in result]
        
        if found_commands:
            print(f"\n✅ DI 科目測試通過，找到命令: {found_commands}")
            return True
        else:
            print(f"❌ DI 科目測試失敗，未找到預期命令: {expected_commands}")
            return False
            
    except Exception as e:
        print(f"❌ DI 科目測試失敗: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("開始測試 gmat_route_tool.py 集成...")
    
    tests = [
        test_route_tool,
        test_q_module,
        test_v_module,
        test_di_module
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 測試總結 ===")
    print(f"通過: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有測試通過！新的路由工具集成成功！")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查錯誤訊息")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 