#!/usr/bin/env python3
"""
測試實際的i18n翻譯函數
"""

import sys
import random
import os

sys.path.append('/Users/danyuchn/GMAT-score-report-analysis')

# 模擬session state
class MockSessionState:
    def __init__(self, language='zh_TW'):
        self.language = language

# 設置模擬的session state
import streamlit as st
if not hasattr(st, 'session_state'):
    st.session_state = MockSessionState()

from gmat_diagnosis_app.i18n import translate as t
from gmat_diagnosis_app.i18n.translations.zh_TW import TRANSLATIONS as zh_trans

def test_i18n_function():
    """測試i18n translate函數"""
    print("=== i18n translate() 函數測試 ===\n")
    
    # 獲取所有翻譯鍵並抽樣
    all_keys = list(zh_trans.keys())
    sample_size = len(all_keys) 
    sampled_keys = random.sample(all_keys, sample_size)
    
    print(f"測試translate()函數，抽樣 {sample_size} 個翻譯鍵...\n")
    
    stats = {
        'zh_success': 0,
        'en_success': 0,
        'zh_errors': 0,
        'en_errors': 0
    }
    
    error_details = []
    
    # 測試中文翻譯
    print("🇹🇼 測試中文翻譯 (zh_TW)...")
    if hasattr(st.session_state, 'language'):
        st.session_state.language = 'zh_TW'
    
    for i, key in enumerate(sampled_keys):
        if i % 100 == 0:
            print(f"  進度: {i}/{sample_size}")
        
        try:
            translation = t(key)
            if translation and translation != key:  # 成功翻譯且不是原鍵值
                stats['zh_success'] += 1
                if i < 3:  # 顯示前3個示例
                    print(f"  ✅ {key} -> {translation[:50]}{'...' if len(translation) > 50 else ''}")
            else:
                stats['zh_errors'] += 1
                if len(error_details) < 5:
                    error_details.append(f"❌ 中文翻譯失敗: {key} -> {translation}")
        except Exception as e:
            stats['zh_errors'] += 1
            if len(error_details) < 5:
                error_details.append(f"💥 中文翻譯錯誤: {key} -> {str(e)}")
    
    print()
    
    # 測試英文翻譯
    print("🇺🇸 測試英文翻譯 (en)...")
    if hasattr(st.session_state, 'language'):
        st.session_state.language = 'en'
    
    for i, key in enumerate(sampled_keys):
        if i % 100 == 0:
            print(f"  進度: {i}/{sample_size}")
        
        try:
            translation = t(key)
            if translation and translation != key:  # 成功翻譯且不是原鍵值
                stats['en_success'] += 1
                if i < 3:  # 顯示前3個示例
                    print(f"  ✅ {key} -> {translation[:50]}{'...' if len(translation) > 50 else ''}")
            else:
                stats['en_errors'] += 1
                if len(error_details) < 10:
                    error_details.append(f"❌ 英文翻譯失敗: {key} -> {translation}")
        except Exception as e:
            stats['en_errors'] += 1
            if len(error_details) < 10:
                error_details.append(f"💥 英文翻譯錯誤: {key} -> {str(e)}")
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("📊 translate() 函數測試結果")
    print("="*60)
    print(f"🇹🇼 中文翻譯成功: {stats['zh_success']:4d}/{sample_size} ({stats['zh_success']/sample_size*100:.1f}%)")
    print(f"🇹🇼 中文翻譯錯誤: {stats['zh_errors']:4d}/{sample_size} ({stats['zh_errors']/sample_size*100:.1f}%)")
    print(f"🇺🇸 英文翻譯成功: {stats['en_success']:4d}/{sample_size} ({stats['en_success']/sample_size*100:.1f}%)")
    print(f"🇺🇸 英文翻譯錯誤: {stats['en_errors']:4d}/{sample_size} ({stats['en_errors']/sample_size*100:.1f}%)")
    
    if error_details:
        print(f"\n🔍 錯誤詳情:")
        for detail in error_details:
            print(f"  {detail}")
    
    overall_success = (stats['zh_success'] + stats['en_success']) / (sample_size * 2) * 100
    print(f"\n🎯 整體成功率: {overall_success:.1f}%")
    
    if overall_success >= 95:
        print("🟢 i18n函數狀態: 優秀")
    elif overall_success >= 85:
        print("🟡 i18n函數狀態: 良好")
    else:
        print("🔴 i18n函數狀態: 需要修復")

if __name__ == "__main__":
    random.seed(42)
    test_i18n_function() 