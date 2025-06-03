#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Integrated GMAT GUI System
執行整合後的 GMAT 圖形化系統

This script runs the integrated GMAT study planner GUI with the route tool functionality
執行整合了路由工具功能的 GMAT 學習規劃 GUI 系統
"""

import sys
import os
import subprocess

def run_integrated_gui():
    """Run the integrated GMAT GUI system"""
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the main GUI file
    gui_file = os.path.join(current_dir, "gmat_study_planner_gui.py")
    
    # Check if the GUI file exists
    if not os.path.exists(gui_file):
        print(f"❌ Error: GUI file not found at {gui_file}")
        return False
    
    # Check if required files exist
    required_files = [
        "gmat_route_tool.py",
        "gmat_route_tool_gui.py", 
        "gmat_study_planner.py"
    ]
    
    for file in required_files:
        file_path = os.path.join(current_dir, file)
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: Required file {file} not found at {file_path}")
    
    print("🚀 Starting Integrated GMAT GUI System...")
    print("📍 Access the application at: http://localhost:8501")
    print("💡 Use Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Run streamlit
        subprocess.run([
            sys.executable, 
            "-m", 
            "streamlit", 
            "run", 
            gui_file,
            "--server.port=8501",
            "--server.headless=false"
        ], cwd=current_dir, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Shutting down the GMAT GUI system...")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 GMAT Integrated GUI System Launcher")
    print("📚 GMAT 整合 GUI 系統啟動器")
    print("=" * 60)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed. Please install it with:")
        print("   pip install streamlit")
        sys.exit(1)
    
    # Check if required packages are available
    required_packages = ["pandas", "plotly", "datetime"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Please install them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    print("\n🎉 All dependencies are available!")
    print("Starting the integrated GUI system...")
    
    success = run_integrated_gui()
    
    if success:
        print("✅ GMAT GUI system shut down successfully.")
    else:
        print("❌ GMAT GUI system encountered an error.")
        sys.exit(1) 