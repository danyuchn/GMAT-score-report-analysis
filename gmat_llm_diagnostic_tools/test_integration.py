#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Integration Test Script
GMAT 整合系統測試腳本

Tests all components of the integrated GMAT GUI system
測試整合 GMAT GUI 系統的所有組件
"""

import os
import sys

def test_integration():
    """Test the integration of GMAT GUI system components"""
    
    print('=' * 60)
    print('🧪 GMAT 整合系統測試')
    print('🧪 GMAT Integration System Test')
    print('=' * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Import verification
    print('\n📋 Test 1: 模組導入測試 (Module Import Test)')
    print('-' * 40)
    
    total_tests += 1
    try:
        from gmat_route_tool import Tools
        print('✅ gmat_route_tool.py import successful')
        success_count += 1
    except Exception as e:
        print(f'❌ gmat_route_tool.py import failed: {e}')
    
    total_tests += 1
    try:
        from gmat_route_tool_gui import show_route_tool
        print('✅ gmat_route_tool_gui.py import successful')
        success_count += 1
    except Exception as e:
        print(f'❌ gmat_route_tool_gui.py import failed: {e}')
    
    total_tests += 1
    try:
        from gmat_study_planner import GMATStudyPlanner
        print('✅ gmat_study_planner.py import successful')
        success_count += 1
    except Exception as e:
        print(f'❌ gmat_study_planner.py import failed: {e}')
    
    # Test 2: Route tool functionality
    print('\n🔧 Test 2: 路由工具功能測試 (Route Tool Functionality Test)')
    print('-' * 40)
    
    total_tests += 1
    try:
        tools = Tools()
        categories = tools.get_available_categories()
        print(f'✅ Route tool categories available: {categories}')
        success_count += 1
        
        # Test CR category
        if 'CR' in categories:
            total_tests += 1
            error_codes = tools.get_error_codes_for_category('CR')
            print(f'✅ CR category has {len(error_codes)} error codes')
            success_count += 1
            
            # Test a specific error code
            if error_codes:
                total_tests += 1
                result = tools.get_commands_with_descriptions('CR', error_codes[0])
                if 'commands_with_descriptions' in result:
                    print(f'✅ Command descriptions working, found {len(result["commands_with_descriptions"])} commands')
                    success_count += 1
                else:
                    print(f'❌ Command descriptions failed: {result}')
        
    except Exception as e:
        print(f'❌ Route tool functionality test failed: {e}')
    
    # Test 3: File existence check
    print('\n📁 Test 3: 檔案存在檢查 (File Existence Check)')
    print('-' * 40)
    
    required_files = [
        'gmat_route_tool.py',
        'gmat_route_tool_gui.py', 
        'gmat_study_planner_gui.py',
        'run_integrated_gui.py',
        'README_INTEGRATED_GUI.md'
    ]
    
    for file in required_files:
        total_tests += 1
        if os.path.exists(file):
            print(f'✅ {file} exists')
            success_count += 1
        else:
            print(f'❌ {file} missing')
    
    # Test 4: Package dependencies
    print('\n📦 Test 4: 套件依賴檢查 (Package Dependencies Check)')
    print('-' * 40)
    
    required_packages = ['streamlit', 'pandas', 'plotly']
    
    for package in required_packages:
        total_tests += 1
        try:
            __import__(package)
            print(f'✅ {package} is available')
            success_count += 1
        except ImportError:
            print(f'❌ {package} is missing - install with: pip install {package}')
    
    # Test Results Summary
    print('\n' + '=' * 60)
    print('📊 測試結果摘要 (Test Results Summary)')
    print('=' * 60)
    
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    
    print(f'✅ 成功測試: {success_count}/{total_tests} ({success_rate:.1f}%)')
    print(f'✅ Successful tests: {success_count}/{total_tests} ({success_rate:.1f}%)')
    
    if success_count == total_tests:
        print('\n🎉 所有測試通過！系統準備就緒')
        print('🎉 All tests passed! System is ready')
        print('💡 執行 python run_integrated_gui.py 啟動完整系統')
        print('💡 Run python run_integrated_gui.py to start the full system')
        return True
    else:
        failed_tests = total_tests - success_count
        print(f'\n⚠️ {failed_tests} 項測試失敗，請檢查上述錯誤')
        print(f'⚠️ {failed_tests} tests failed, please check the errors above')
        print('🔧 修復錯誤後重新執行測試')
        print('🔧 Fix the errors and re-run the test')
        return False

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1) 