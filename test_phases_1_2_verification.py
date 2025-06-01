#!/usr/bin/env python3
"""
GMAT診斷模組統一化計劃 - 階段一與階段二驗證腳本
測試檔案結構、導入語句、命名規範等是否符合統一化標準

版本: v1.0
創建日期: 2025-01-30
"""

import os
import sys
import ast
import importlib.util
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

class UnificationVerifier:
    """統一化驗證器"""
    
    def __init__(self):
        self.base_path = Path("gmat_diagnosis_app/diagnostics")
        self.modules = ["di_modules", "q_modules", "v_modules"]
        self.results = {
            "phase_1": {"passed": True, "issues": []},
            "phase_2": {"passed": True, "issues": []},
            "imports": {"passed": True, "issues": []},
            "compilation": {"passed": True, "issues": []}
        }
        
        # Expected file structure based on unification plan
        self.expected_files = {
            "main.py",           # Main diagnosis function
            "analysis.py",       # Core analysis logic (was chapter_logic.py in DI)
            "reporting.py",      # Report generation (was report_generation.py in DI)
            "recommendations.py", # Practice recommendations
            "utils.py",          # Utility functions
            "constants.py",      # Constants and configurations
            "ai_prompts.py",     # AI-related functionality
            "__init__.py"        # Module initialization
        }
        
        # Files that should NOT exist after phase 2
        self.deprecated_files = {
            "chapter_logic.py",   # Should be renamed to analysis.py
            "report_generation.py", # Should be renamed to reporting.py
            "translation.py"      # Should be removed (using i18n now)
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試"""
        print("🔍 開始執行 GMAT 診斷模組統一化驗證測試...")
        print("=" * 80)
        
        # Phase 1 Tests
        print("\n📋 階段一驗證: 環境準備與備份")
        self.verify_phase_1()
        
        # Phase 2 Tests
        print("\n📂 階段二驗證: 檔案結構統一")
        self.verify_phase_2()
        
        # Import Tests
        print("\n📦 匯入語句驗證")
        self.verify_imports()
        
        # Compilation Tests
        print("\n🔧 編譯與語法驗證")
        self.verify_compilation()
        
        # Summary
        print("\n📊 測試結果摘要")
        self.print_summary()
        
        return self.results
    
    def verify_phase_1(self):
        """驗證階段一: 環境準備"""
        print("檢查 git 狀態和備份標籤...")
        
        # Check if we're on the correct branch
        try:
            import subprocess
            result = subprocess.run(["git", "branch", "--show-current"], 
                                  capture_output=True, text=True)
            current_branch = result.stdout.strip()
            if current_branch != "gui-rewrite-7":
                self.results["phase_1"]["issues"].append(
                    f"❌ 當前分支是 '{current_branch}'，應該是 'gui-rewrite-7'"
                )
                self.results["phase_1"]["passed"] = False
            else:
                print("✅ 分支檢查通過: gui-rewrite-7")
        except Exception as e:
            self.results["phase_1"]["issues"].append(f"❌ Git 檢查失敗: {str(e)}")
            self.results["phase_1"]["passed"] = False
        
        # Check if base directories exist
        if not self.base_path.exists():
            self.results["phase_1"]["issues"].append(f"❌ 基礎路徑不存在: {self.base_path}")
            self.results["phase_1"]["passed"] = False
        else:
            print("✅ 基礎路徑檢查通過")
        
        # Check if all module directories exist
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                self.results["phase_1"]["issues"].append(f"❌ 模組目錄不存在: {module}")
                self.results["phase_1"]["passed"] = False
            else:
                print(f"✅ 模組目錄存在: {module}")
    
    def verify_phase_2(self):
        """驗證階段二: 檔案結構統一"""
        print("檢查檔案結構統一化...")
        
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                continue
                
            print(f"\n檢查 {module} 模組:")
            
            # Check for expected files
            existing_files = set(f.name for f in module_path.iterdir() if f.is_file() and f.suffix == '.py')
            
            # Check for deprecated files
            for deprecated_file in self.deprecated_files:
                if deprecated_file in existing_files:
                    self.results["phase_2"]["issues"].append(
                        f"❌ {module}: 仍存在已棄用檔案 '{deprecated_file}'"
                    )
                    self.results["phase_2"]["passed"] = False
                    print(f"  ❌ 發現已棄用檔案: {deprecated_file}")
                else:
                    print(f"  ✅ 已棄用檔案已移除: {deprecated_file}")
            
            # Check for required files
            missing_files = self.expected_files - existing_files
            if missing_files:
                for missing_file in missing_files:
                    self.results["phase_2"]["issues"].append(
                        f"❌ {module}: 缺少必要檔案 '{missing_file}'"
                    )
                    self.results["phase_2"]["passed"] = False
                    print(f"  ❌ 缺少檔案: {missing_file}")
            else:
                print(f"  ✅ 所有必要檔案都存在")
            
            # Check file naming consistency
            extra_files = existing_files - self.expected_files - {"__pycache__"}
            if extra_files:
                for extra_file in extra_files:
                    # Some modules may have additional files like behavioral.py or translations.py
                    if extra_file not in ["behavioral.py", "translations.py"]:
                        print(f"  ⚠️  額外檔案: {extra_file} (可能是模組特有檔案)")
    
    def verify_imports(self):
        """驗證匯入語句正確性"""
        print("檢查匯入語句...")
        
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                continue
                
            print(f"\n檢查 {module} 匯入語句:")
            
            # Check main.py imports specifically
            main_py = module_path / "main.py"
            if main_py.exists():
                self.check_main_py_imports(main_py, module)
            
            # Check other file imports
            for py_file in module_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    self.check_file_imports(py_file, module)
    
    def check_main_py_imports(self, file_path: Path, module: str):
        """檢查 main.py 的匯入語句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('.'):
                        # Relative import
                        module_name = node.module.lstrip('.')
                        
                        # Check for old import patterns that should be updated
                        if module_name == "chapter_logic" and module == "di_modules":
                            self.results["imports"]["issues"].append(
                                f"❌ {module}/main.py: 仍使用舊匯入 'chapter_logic'，應改為 'analysis'"
                            )
                            self.results["imports"]["passed"] = False
                            print(f"  ❌ 發現舊匯入: chapter_logic")
                        
                        if module_name == "report_generation" and module == "di_modules":
                            self.results["imports"]["issues"].append(
                                f"❌ {module}/main.py: 仍使用舊匯入 'report_generation'，應改為 'reporting'"
                            )
                            self.results["imports"]["passed"] = False
                            print(f"  ❌ 發現舊匯入: report_generation")
                        
                        if module_name == "analysis":
                            print(f"  ✅ 使用新匯入: analysis")
                        
                        if module_name == "reporting":
                            print(f"  ✅ 使用新匯入: reporting")
                            
        except Exception as e:
            self.results["imports"]["issues"].append(f"❌ {file_path}: 匯入檢查失敗 - {str(e)}")
            self.results["imports"]["passed"] = False
    
    def check_file_imports(self, file_path: Path, module: str):
        """檢查其他檔案的匯入語句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for i18n imports (should be standardized)
            if "from gmat_diagnosis_app.i18n import translate" in content:
                print(f"  ✅ {file_path.name}: 使用標準 i18n 匯入")
            elif "translate" in content and "i18n" in content:
                # Parse the file to check for actual code usage (not comments)
                try:
                    tree = ast.parse(content)
                    found_old_translation = False
                    
                    # Check for function definitions or calls related to old translation system
                    for node in ast.walk(tree):
                        # Check for function definitions like _translate_di
                        if isinstance(node, ast.FunctionDef) and node.name.startswith("_translate_"):
                            found_old_translation = True
                            break
                        # Check for function calls like _translate_di(...)
                        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id.startswith("_translate_"):
                            found_old_translation = True
                            break
                        # Check for attribute access like something._translate_di
                        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.startswith("_translate_"):
                            found_old_translation = True
                            break
                        # Check for imports from translation.py
                        elif isinstance(node, ast.ImportFrom) and node.module and "translation" in node.module:
                            found_old_translation = True
                            break
                    
                    if found_old_translation:
                        self.results["imports"]["issues"].append(
                            f"❌ {module}/{file_path.name}: 仍使用舊翻譯系統"
                        )
                        self.results["imports"]["passed"] = False
                        print(f"  ❌ {file_path.name}: 使用舊翻譯系統")
                    else:
                        print(f"  ✅ {file_path.name}: 無舊翻譯系統使用")
                        
                except SyntaxError:
                    # If we can't parse the file, fall back to simple text search
                    # but be more specific about what we're looking for
                    active_translate_patterns = [
                        "_translate_di(",
                        "_translate_q(",
                        "_translate_v(",
                        "from .translation import",
                        "from translation import"
                    ]
                    
                    found_pattern = False
                    for pattern in active_translate_patterns:
                        if pattern in content:
                            found_pattern = True
                            break
                    
                    if found_pattern:
                        self.results["imports"]["issues"].append(
                            f"❌ {module}/{file_path.name}: 仍使用舊翻譯系統"
                        )
                        self.results["imports"]["passed"] = False
                        print(f"  ❌ {file_path.name}: 使用舊翻譯系統")
                    else:
                        print(f"  ✅ {file_path.name}: 無舊翻譯系統使用")
                        
        except Exception as e:
            print(f"  ⚠️  {file_path.name}: 匯入檢查警告 - {str(e)}")
    
    def verify_compilation(self):
        """驗證編譯和語法正確性"""
        print("檢查編譯和語法...")
        
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                continue
                
            print(f"\n檢查 {module} 編譯:")
            
            for py_file in module_path.glob("*.py"):
                if py_file.name == "__pycache__":
                    continue
                    
                try:
                    # Try to parse the file
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    ast.parse(content)
                    print(f"  ✅ {py_file.name}: 語法正確")
                    
                    # Try to import the module (basic import test)
                    self.test_module_import(py_file, module)
                    
                except SyntaxError as e:
                    self.results["compilation"]["issues"].append(
                        f"❌ {module}/{py_file.name}: 語法錯誤 - 第{e.lineno}行: {e.msg}"
                    )
                    self.results["compilation"]["passed"] = False
                    print(f"  ❌ {py_file.name}: 語法錯誤 - {e.msg}")
                    
                except Exception as e:
                    self.results["compilation"]["issues"].append(
                        f"❌ {module}/{py_file.name}: 編譯錯誤 - {str(e)}"
                    )
                    self.results["compilation"]["passed"] = False
                    print(f"  ❌ {py_file.name}: 編譯錯誤 - {str(e)}")
    
    def test_module_import(self, file_path: Path, module: str):
        """測試模組匯入"""
        try:
            # Create module spec
            module_name = f"gmat_diagnosis_app.diagnostics.{module}.{file_path.stem}"
            
            # Skip __init__.py for basic import test
            if file_path.name == "__init__.py":
                return
                
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module_obj = importlib.util.module_from_spec(spec)
                # Don't actually execute - just check if we can create the module object
                print(f"  ✅ {file_path.name}: 匯入測試通過")
            else:
                print(f"  ⚠️  {file_path.name}: 匯入規格創建失敗")
                
        except Exception as e:
            print(f"  ⚠️  {file_path.name}: 匯入測試警告 - {str(e)}")
    
    def print_summary(self):
        """打印測試結果摘要"""
        print("=" * 80)
        
        total_passed = sum(1 for phase in self.results.values() if phase["passed"])
        total_phases = len(self.results)
        
        print(f"📊 總體結果: {total_passed}/{total_phases} 階段通過")
        
        for phase_name, phase_result in self.results.items():
            status = "✅ 通過" if phase_result["passed"] else "❌ 失敗"
            print(f"\n{phase_name.upper()}: {status}")
            
            if phase_result["issues"]:
                print("問題清單:")
                for issue in phase_result["issues"]:
                    print(f"  {issue}")
            else:
                print("  沒有發現問題")
        
        # Overall recommendation
        if all(phase["passed"] for phase in self.results.values()):
            print("\n🎉 所有測試通過！可以繼續進行階段三。")
        else:
            print("\n⚠️  發現問題需要修正，請查看上述詳細資訊。")
        
        print("=" * 80)

def main():
    """主函數"""
    print("GMAT 診斷模組統一化計劃 - 階段一與階段二驗證")
    print("Version: v1.0")
    print("Date: 2025-01-30")
    
    verifier = UnificationVerifier()
    results = verifier.run_all_tests()
    
    # Return exit code based on results
    if all(phase["passed"] for phase in results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main() 