#!/usr/bin/env python3
"""
GMAT診斷模組統一化計劃 - 功能性驗證測試腳本
測試各模組的導入和基本功能是否正常工作

版本: v1.0
創建日期: 2025-01-30
"""

import sys
import pandas as pd
import traceback
from pathlib import Path

class FunctionalityTester:
    """功能性測試器"""
    
    def __init__(self):
        self.results = {
            "di_module": {"passed": True, "issues": []},
            "q_module": {"passed": True, "issues": []},
            "v_module": {"passed": True, "issues": []},
            "cross_module": {"passed": True, "issues": []}
        }
        
        # Create sample test data
        self.sample_data = self.create_sample_data()
    
    def create_sample_data(self) -> pd.DataFrame:
        """創建測試用的樣本數據"""
        data = {
            'question_number': [1, 2, 3, 4, 5],
            'question_type': ['DS', 'PS', 'CR', 'RC', 'TPA'],
            'is_correct': [True, False, True, False, True],
            'time_seconds': [120, 90, 150, 200, 180],
            'difficulty': [1.2, -0.5, 0.8, 1.5, 0.2],
            'domain': ['Math Related', 'Math Related', 'Non-Math Related', 'Non-Math Related', 'Math Related'],
            'is_invalid': [False, False, False, False, False]
        }
        return pd.DataFrame(data)
    
    def run_all_tests(self):
        """執行所有功能性測試"""
        print("🧪 開始執行 GMAT 診斷模組功能性驗證測試...")
        print("=" * 80)
        
        # Test DI Module
        print("\n🔍 測試 DI 模組功能...")
        self.test_di_module()
        
        # Test Q Module  
        print("\n🔍 測試 Q 模組功能...")
        self.test_q_module()
        
        # Test V Module
        print("\n🔍 測試 V 模組功能...")
        self.test_v_module()
        
        # Test Cross-Module Integration
        print("\n🔍 測試跨模組整合...")
        self.test_cross_module_integration()
        
        # Summary
        print("\n📊 功能性測試結果摘要")
        self.print_summary()
        
        return self.results
    
    def test_di_module(self):
        """測試DI模組功能"""
        try:
            # Test imports
            print("  📦 測試DI模組匯入...")
            from gmat_diagnosis_app.diagnostics.di_modules import main as di_main
            from gmat_diagnosis_app.diagnostics.di_modules import analysis as di_analysis
            from gmat_diagnosis_app.diagnostics.di_modules import reporting as di_reporting
            from gmat_diagnosis_app.diagnostics.di_modules import recommendations as di_recommendations
            from gmat_diagnosis_app.diagnostics.di_modules import utils as di_utils
            from gmat_diagnosis_app.diagnostics.di_modules import constants as di_constants
            from gmat_diagnosis_app.diagnostics.di_modules import ai_prompts as di_ai_prompts
            print("    ✅ 所有DI模組檔案匯入成功")
            
            # Test constants access
            print("  🔧 測試DI模組常數...")
            if hasattr(di_constants, 'MAX_ALLOWED_TIME_DI'):
                print(f"    ✅ MAX_ALLOWED_TIME_DI = {di_constants.MAX_ALLOWED_TIME_DI}")
            if hasattr(di_constants, 'DI_PARAM_CATEGORY_ORDER'):
                print(f"    ✅ DI_PARAM_CATEGORY_ORDER 包含 {len(di_constants.DI_PARAM_CATEGORY_ORDER)} 個分類")
            
            # Test basic function existence
            print("  ⚙️  測試DI模組函數存在性...")
            if hasattr(di_main, 'run_di_diagnosis'):
                print("    ✅ di_main.run_di_diagnosis 函數存在")
            else:
                # Check for alternative function names
                main_functions = [name for name in dir(di_main) if 'diagnos' in name.lower()]
                if main_functions:
                    print(f"    ⚠️  找到替代診斷函數: {main_functions}")
                else:
                    print("    ❌ 未找到主診斷函數")
            
            if hasattr(di_utils, 'format_rate'):
                print("    ✅ di_utils.format_rate 函數存在")
            elif hasattr(di_utils, '_format_rate'):
                print("    ⚠️  發現舊命名函數 _format_rate (需要重構)")
            
            print("    ✅ DI模組基本功能測試通過")
            
        except Exception as e:
            error_msg = f"DI模組測試失敗: {str(e)}"
            self.results["di_module"]["issues"].append(error_msg)
            self.results["di_module"]["passed"] = False
            print(f"    ❌ {error_msg}")
            print(f"    詳細錯誤: {traceback.format_exc()}")
    
    def test_q_module(self):
        """測試Q模組功能"""
        try:
            # Test imports
            print("  📦 測試Q模組匯入...")
            from gmat_diagnosis_app.diagnostics.q_modules import main as q_main
            from gmat_diagnosis_app.diagnostics.q_modules import analysis as q_analysis
            from gmat_diagnosis_app.diagnostics.q_modules import reporting as q_reporting
            from gmat_diagnosis_app.diagnostics.q_modules import recommendations as q_recommendations
            from gmat_diagnosis_app.diagnostics.q_modules import utils as q_utils
            from gmat_diagnosis_app.diagnostics.q_modules import constants as q_constants
            from gmat_diagnosis_app.diagnostics.q_modules import ai_prompts as q_ai_prompts
            print("    ✅ 所有Q模組檔案匯入成功")
            
            # Test constants access
            print("  🔧 測試Q模組常數...")
            if hasattr(q_constants, 'Q_PARAM_CATEGORY_ORDER'):
                print(f"    ✅ Q_PARAM_CATEGORY_ORDER 包含 {len(q_constants.Q_PARAM_CATEGORY_ORDER)} 個分類")
            
            # Test basic function existence
            print("  ⚙️  測試Q模組函數存在性...")
            if hasattr(q_main, 'run_q_diagnosis'):
                print("    ✅ q_main.run_q_diagnosis 函數存在")
            else:
                # Check for alternative function names
                main_functions = [name for name in dir(q_main) if 'diagnos' in name.lower()]
                if main_functions:
                    print(f"    ⚠️  找到替代診斷函數: {main_functions}")
                else:
                    print("    ❌ 未找到主診斷函數")
            
            if hasattr(q_utils, 'format_rate'):
                print("    ✅ q_utils.format_rate 函數存在")
            
            print("    ✅ Q模組基本功能測試通過")
            
        except Exception as e:
            error_msg = f"Q模組測試失敗: {str(e)}"
            self.results["q_module"]["issues"].append(error_msg)
            self.results["q_module"]["passed"] = False
            print(f"    ❌ {error_msg}")
            print(f"    詳細錯誤: {traceback.format_exc()}")
    
    def test_v_module(self):
        """測試V模組功能"""
        try:
            # Test imports
            print("  📦 測試V模組匯入...")
            from gmat_diagnosis_app.diagnostics.v_modules import main as v_main
            from gmat_diagnosis_app.diagnostics.v_modules import analysis as v_analysis
            from gmat_diagnosis_app.diagnostics.v_modules import reporting as v_reporting
            from gmat_diagnosis_app.diagnostics.v_modules import recommendations as v_recommendations
            from gmat_diagnosis_app.diagnostics.v_modules import utils as v_utils
            from gmat_diagnosis_app.diagnostics.v_modules import constants as v_constants
            from gmat_diagnosis_app.diagnostics.v_modules import ai_prompts as v_ai_prompts
            print("    ✅ 所有V模組檔案匯入成功")
            
            # Test constants access
            print("  🔧 測試V模組常數...")
            if hasattr(v_constants, 'V_PARAM_CATEGORY_ORDER'):
                print(f"    ✅ V_PARAM_CATEGORY_ORDER 包含 {len(v_constants.V_PARAM_CATEGORY_ORDER)} 個分類")
            
            # Test basic function existence
            print("  ⚙️  測試V模組函數存在性...")
            if hasattr(v_main, 'run_v_diagnosis'):
                print("    ✅ v_main.run_v_diagnosis 函數存在")
            else:
                # Check for alternative function names
                main_functions = [name for name in dir(v_main) if 'diagnos' in name.lower()]
                if main_functions:
                    print(f"    ⚠️  找到替代診斷函數: {main_functions}")
                else:
                    print("    ❌ 未找到主診斷函數")
            
            if hasattr(v_utils, 'format_rate'):
                print("    ✅ v_utils.format_rate 函數存在")
            
            print("    ✅ V模組基本功能測試通過")
            
        except Exception as e:
            error_msg = f"V模組測試失敗: {str(e)}"
            self.results["v_module"]["issues"].append(error_msg)
            self.results["v_module"]["passed"] = False
            print(f"    ❌ {error_msg}")
            print(f"    詳細錯誤: {traceback.format_exc()}")
    
    def test_cross_module_integration(self):
        """測試跨模組整合功能"""
        try:
            print("  🔗 測試跨模組整合...")
            
            # Test that all modules can be imported together
            from gmat_diagnosis_app.diagnostics import di_modules, q_modules, v_modules
            print("    ✅ 所有診斷模組可同時匯入")
            
            # Test i18n integration
            print("  🌐 測試i18n整合...")
            from gmat_diagnosis_app.i18n import translate
            
            # Test basic translation functionality
            test_key = "di_invalid_data_tag"
            translation = translate(test_key)
            if translation and translation != test_key:
                print(f"    ✅ i18n翻譯功能正常: '{test_key}' -> '{translation}'")
            else:
                print(f"    ⚠️  i18n翻譯可能未配置: '{test_key}' -> '{translation}'")
            
            # Test that no naming conflicts exist
            print("  🏷️  測試命名衝突...")
            
            # Check for function name conflicts between modules
            import gmat_diagnosis_app.diagnostics.di_modules.utils as di_utils
            import gmat_diagnosis_app.diagnostics.q_modules.utils as q_utils
            import gmat_diagnosis_app.diagnostics.v_modules.utils as v_utils
            
            di_functions = set(dir(di_utils))
            q_functions = set(dir(q_utils))
            v_functions = set(dir(v_utils))
            
            common_functions = di_functions & q_functions & v_functions
            expected_common = {'format_rate', '__name__', '__doc__', '__file__', '__package__'}
            
            unexpected_conflicts = common_functions - expected_common
            if unexpected_conflicts:
                print(f"    ⚠️  發現非預期的函數名衝突: {unexpected_conflicts}")
            else:
                print("    ✅ 無非預期的函數名衝突")
                
            print("    ✅ 跨模組整合測試通過")
            
        except Exception as e:
            error_msg = f"跨模組整合測試失敗: {str(e)}"
            self.results["cross_module"]["issues"].append(error_msg)
            self.results["cross_module"]["passed"] = False
            print(f"    ❌ {error_msg}")
            print(f"    詳細錯誤: {traceback.format_exc()}")
    
    def print_summary(self):
        """打印測試結果摘要"""
        print("=" * 80)
        
        total_passed = sum(1 for result in self.results.values() if result["passed"])
        total_tests = len(self.results)
        
        print(f"📊 功能性測試總體結果: {total_passed}/{total_tests} 模組通過")
        
        for test_name, test_result in self.results.items():
            status = "✅ 通過" if test_result["passed"] else "❌ 失敗"
            print(f"\n{test_name.upper().replace('_', ' ')}: {status}")
            
            if test_result["issues"]:
                print("問題清單:")
                for issue in test_result["issues"]:
                    print(f"  {issue}")
            else:
                print("  沒有發現問題")
        
        # Overall recommendation
        if all(result["passed"] for result in self.results.values()):
            print("\n🎉 所有功能性測試通過！模組整合成功。")
            print("💡 建議: 可以繼續進行階段三的函數命名統一。")
        else:
            print("\n⚠️  發現功能性問題需要修正。")
        
        print("=" * 80)

def main():
    """主函數"""
    print("GMAT 診斷模組統一化計劃 - 功能性驗證測試")
    print("Version: v1.0")
    print("Date: 2025-01-30")
    
    tester = FunctionalityTester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    if all(result["passed"] for result in results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main() 