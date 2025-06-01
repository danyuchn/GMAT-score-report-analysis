#!/usr/bin/env python3
"""
GMAT Route Tool 命令一致性檢查腳本
檢查 command_details 和 route_table 之間的命令名稱一致性
"""

import sys
import os
from typing import Set, List, Dict

# 添加路徑以便導入模組
sys.path.append('gmat_llm_diagnostic_tools')

def check_command_consistency():
    """檢查 GMAT Route Tool 中的命令一致性"""
    
    print("🔍 開始檢查 GMAT Route Tool 命令一致性...\n")
    
    try:
        # 導入 Tools 類 (從 gmat_llm_diagnostic_tools 目錄)
        from gmat_route_tool import Tools
        tools = Tools()
        
        # 獲取 command_details 中定義的所有命令
        defined_commands = set(tools.command_details.keys())
        print(f"📋 在 command_details 中定義的命令數量: {len(defined_commands)}")
        print("定義的命令:")
        for i, cmd in enumerate(sorted(defined_commands), 1):
            print(f"  {i:2d}. {cmd}")
        
        print("\n" + "="*60 + "\n")
        
        # 從 route_table 中收集所有被引用的命令
        referenced_commands = set()
        route_table_details = {}
        
        for category, error_mappings in tools.route_table.items():
            route_table_details[category] = {}
            for error_code, commands in error_mappings.items():
                route_table_details[category][error_code] = commands
                referenced_commands.update(commands)
        
        print(f"📋 在 route_table 中被引用的命令數量: {len(referenced_commands)}")
        print("被引用的命令:")
        for i, cmd in enumerate(sorted(referenced_commands), 1):
            print(f"  {i:2d}. {cmd}")
        
        print("\n" + "="*60 + "\n")
        
        # 檢查一致性
        # 1. 在 route_table 中被引用但在 command_details 中未定義的命令
        undefined_commands = referenced_commands - defined_commands
        
        # 2. 在 command_details 中定義但在 route_table 中未被引用的命令
        unused_commands = defined_commands - referenced_commands
        
        # 輸出檢查結果
        errors_found = False
        
        if undefined_commands:
            errors_found = True
            print("❌ 錯誤：在 route_table 中被引用但在 command_details 中未定義的命令:")
            for i, cmd in enumerate(sorted(undefined_commands), 1):
                print(f"  {i:2d}. '{cmd}'")
            
            # 詳細顯示這些命令在哪些地方被引用
            print("\n   詳細引用位置:")
            for category, error_mappings in route_table_details.items():
                for error_code, commands in error_mappings.items():
                    for cmd in commands:
                        if cmd in undefined_commands:
                            print(f"     - {category}.{error_code}: '{cmd}'")
            print()
        
        if unused_commands:
            print("⚠️  警告：在 command_details 中定義但在 route_table 中未被引用的命令:")
            for i, cmd in enumerate(sorted(unused_commands), 1):
                print(f"  {i:2d}. '{cmd}'")
            print()
        
        if not errors_found and not unused_commands:
            print("✅ 完美！所有命令名稱都一致，沒有發現任何問題。")
        elif not errors_found:
            print("✅ 命令定義完整！所有被引用的命令都已正確定義。")
            print("   （有一些定義的命令暫未在路由表中使用，這是正常的）")
        
        print("\n" + "="*60 + "\n")
        
        # 統計資訊
        print("📊 統計摘要:")
        print(f"   • 定義的命令總數: {len(defined_commands)}")
        print(f"   • 被引用的命令總數: {len(referenced_commands)}")
        print(f"   • 共同命令數: {len(defined_commands & referenced_commands)}")
        print(f"   • 未定義的引用: {len(undefined_commands)} {'❌' if undefined_commands else '✅'}")
        print(f"   • 未使用的定義: {len(unused_commands)} {'⚠️' if unused_commands else '✅'}")
        
        # 各科目命令使用統計
        print(f"\n📈 各科目命令使用統計:")
        for category in sorted(tools.route_table.keys()):
            category_commands = set()
            for commands in tools.route_table[category].values():
                category_commands.update(commands)
            print(f"   • {category}: {len(category_commands)} 個不同命令")
        
        return len(undefined_commands) == 0
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確保 gmat_llm_diagnostic_tools/gmat_route_tool.py 檔案存在且無語法錯誤。")
        return False
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {e}")
        return False

def check_json_python_consistency():
    """額外檢查：比對 JSON 檔案中的模型名稱"""
    
    print("\n🔍 額外檢查：與 JSON 檔案的一致性...\n")
    
    try:
        import json
        import re
        
        # 讀取 JSON 檔案中的模型名稱
        json_file_path = 'gmat_llm_diagnostic_tools/models-export-1748708390311.json'
        
        if not os.path.exists(json_file_path):
            print("⚠️  JSON 檔案不存在，跳過此檢查。")
            return True
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取所有模型名稱
        json_model_names = set()
        name_pattern = r'"name":\s*"([^"]*)"'
        matches = re.findall(name_pattern, content)
        
        for name in matches:
            # 過濾掉非命令的名稱（科目代碼、人名等）
            if name not in ['CR', 'DS', 'GT', 'MSR', 'PS', 'RC', 'TPA', 'Dustin Yuchen Teng', 'prompt-to-label.md']:
                json_model_names.add(name)
        
        print(f"📋 JSON 檔案中找到的模型名稱數量: {len(json_model_names)}")
        
        # 導入 Python 中定義的命令
        from gmat_route_tool import Tools
        tools = Tools()
        python_commands = set(tools.command_details.keys())
        
        # 比對
        json_only = json_model_names - python_commands
        python_only = python_commands - json_model_names
        common = python_commands & json_model_names
        
        print(f"\n📊 JSON-Python 比對結果:")
        print(f"   • 共同命令: {len(common)}")
        print(f"   • 僅在 JSON 中: {len(json_only)}")
        print(f"   • 僅在 Python 中: {len(python_only)}")
        
        if json_only:
            print(f"\n📄 僅在 JSON 中存在的模型:")
            for i, name in enumerate(sorted(json_only), 1):
                print(f"  {i:2d}. {name}")
        
        if python_only:
            print(f"\n🐍 僅在 Python 中存在的命令:")
            for i, name in enumerate(sorted(python_only), 1):
                print(f"  {i:2d}. {name}")
        
        print(f"\n✅ 成功匹配的命令數: {len(common)}")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON 比對檢查中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    print("🎯 GMAT Route Tool 一致性檢查工具")
    print("="*60)
    
    # 檢查內部一致性
    internal_ok = check_command_consistency()
    
    # 檢查與 JSON 的一致性
    json_ok = check_json_python_consistency()
    
    print("\n" + "="*60)
    
    if internal_ok:
        print("🎉 內部命令一致性檢查通過！")
    else:
        print("💥 內部命令一致性檢查失敗！")
    
    if json_ok:
        print("🎉 JSON-Python 比對檢查完成！")
    
    if internal_ok and json_ok:
        print("\n🏆 所有檢查都順利完成！系統應該可以正常運作。")
        sys.exit(0)
    else:
        print("\n⚠️  發現問題，請檢查上述錯誤訊息。")
        sys.exit(1) 