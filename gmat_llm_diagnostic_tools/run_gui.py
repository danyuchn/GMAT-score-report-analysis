#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Study Planner GUI Launcher
GMAT 學習規劃系統 GUI 啟動器

Simple launcher script for the Streamlit GUI application
"""

import subprocess
import sys
import os

def check_requirements():
    """檢查必要的套件是否已安裝"""
    required_packages = [
        'streamlit',
        'pandas', 
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少必要套件，請先安裝:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """主要啟動函數"""
    print("=" * 60)
    print("🚀 GMAT 學習規劃系統 GUI 啟動器")
    print("GMAT Study Planner GUI Launcher")
    print("=" * 60)
    
    # 檢查套件
    print("🔍 檢查系統環境...")
    if not check_requirements():
        print("\n💡 安裝建議:")
        print("pip install streamlit pandas plotly")
        return
    
    print("✅ 環境檢查通過")
    
    # 設定 Streamlit 參數
    streamlit_script = "gmat_study_planner_gui.py"
    
    # 檢查腳本是否存在
    if not os.path.exists(streamlit_script):
        print(f"❌ 找不到 GUI 腳本: {streamlit_script}")
        print("請確保在正確的目錄中運行此腳本")
        return
    
    print(f"📱 啟動 Streamlit 應用: {streamlit_script}")
    print("🌐 應用將在瀏覽器中自動開啟")
    print("🛑 按 Ctrl+C 停止應用")
    print("-" * 60)
    
    try:
        # 啟動 Streamlit 應用
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            streamlit_script,
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 應用已停止")
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        print("\n🔧 故障排除:")
        print("1. 確保 Streamlit 已安裝: pip install streamlit")
        print("2. 確保在正確目錄中運行")
        print("3. 檢查防火牆設定")

if __name__ == "__main__":
    main() 