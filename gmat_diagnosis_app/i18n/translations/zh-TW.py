"""
Traditional Chinese (zh-TW) translations for GMAT Diagnosis App

This file contains all Chinese translations based on the original translation dictionary.
"""

TRANSLATIONS = {
    # UI Interface Translations
    'analysis_settings': "分析設定",
    'language_selection': "語言 / Language",
    'select_language': "選擇語言 / Select Language:",
    'language_updated': "語言已更新！",
    'sample_data': "範例數據",
    'sample_data_import': "範例數據導入",
    'sample_data_description': "點擊下方按鈕導入範例做題數據，方便體驗系統功能",
    'load_sample_data': "一鍵導入範例數據",
    'sample_data_loaded_success': "範例數據已成功填入各科目的文本框！請檢查「數據輸入與分析」頁面。",
    'ai_settings': "AI功能設定",
    'master_key_prompt': "輸入管理員金鑰啟用 AI 問答功能：",
    'master_key_help': "輸入有效管理金鑰並成功完成分析後，下方將出現 AI 對話框。管理金鑰請向系統管理員索取。",
    'master_key_success': "管理金鑰驗證成功，AI功能已啟用！",
    'master_key_failed': "管理金鑰驗證失敗，無法啟用AI功能。",
    'irt_simulation_settings': "IRT模擬設定",
    'manual_adjustments': "手動調整題目",
    'manual_adjustments_description': "手動調整題目正確性",
    'manual_adjustments_note': "（僅影響IRT模擬）",
    'incorrect_to_correct': "由錯改對題號",
    'correct_to_incorrect': "由對改錯題號",
    'example_format': "例: 1,5,10",
    'main_title': "GMAT 成績診斷平台 by Dustin",
    'main_subtitle': "智能化個人化成績分析與學習建議系統",
    'data_input_tab': "數據輸入與分析",
    'results_view_tab': "結果查看",
    'quick_guide': "快速使用指南 👉",
    'footer_feedback': "有問題或建議？請前往",
    'footer_github': "GitHub Issues",
    'footer_submit': "提交反饋",
    
    # Q Diagnostic Parameters - Original translations
    'Q_READING_COMPREHENSION_ERROR': "Q 閱讀理解錯誤：題目文字理解",
    'Q_CONCEPT_APPLICATION_ERROR': "Q 概念應用錯誤：數學觀念/公式應用",
    'Q_CALCULATION_ERROR': "Q 計算錯誤：數學計算",
    'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': "Q 基礎掌握：應用不穩定（Special Focus Error）",
    'Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    'Q_BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    'Q_READING_COMPREHENSION_DIFFICULTY': "Q 閱讀理解障礙：題目文字理解困難",
    'Q_CONCEPT_APPLICATION_DIFFICULTY': "Q 概念應用障礙：數學觀念/公式應用困難",
    'Q_CALCULATION_DIFFICULTY': "Q 計算障礙：數學計算困難",
    'Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED': "Q 閱讀理解障礙：心態失常讀不進去",
    
    # Additional Q parameters found in code
    'Q_CARELESSNESS_DETAIL_OMISSION': "Q 粗心問題：細節遺漏",
    'Q_PROBLEM_UNDERSTANDING_ERROR': "Q 問題理解錯誤：題意理解",
    'Q_EFFICIENCY_BOTTLENECK_READING': "Q 效率瓶頸：閱讀速度",
    'Q_EFFICIENCY_BOTTLENECK_CONCEPT': "Q 效率瓶頸：概念應用",
    'Q_EFFICIENCY_BOTTLENECK_CALCULATION': "Q 效率瓶頸：計算速度",
    
    # Behavioral pattern variants (without Q_ prefix)
    'BEHAVIOR_CARELESSNESS_ISSUE': "行為模式: 粗心問題 (快而錯比例高)",
    'BEHAVIOR_EARLY_RUSHING_FLAG_RISK': "行為模式: 前期作答過快 (Flag risk)",
    
    # Skill names (if needed for translation)
    'Unknown Skill': "未知技能",
    
    # Common diagnostic terms
    'time_pressure_status': "時間壓力狀態",
    'overtime_threshold': "超時門檻",
    'invalid_questions_excluded': "已排除無效題目",
    'diagnostic_params': "診斷參數",
    'diagnostic_params_list': "診斷參數列表",
    'question_position': "題目位置",
    'question_fundamental_skill': "題目基礎技能",
    'is_correct': "答對",
    'is_invalid': "無效",
    'is_manually_invalid': "手動標記無效",
    'question_time': "答題時間",
    'question_difficulty': "題目難度",
    'question_type': "題目類型",
    'overtime': "超時",
    'is_sfe': "為SFE",
    
    # Report sections
    'chapter1_results': "第一章結果",
    'chapter2_flags': "第二章標記",
    'chapter2_summary': "第二章摘要",
    'chapter3_error_details': "第三章錯誤詳情",
    'chapter4_correct_slow_details': "第四章正確但慢詳情",
    'chapter5_patterns': "第五章模式",
    'chapter6_skill_override': "第六章技能覆蓋",
    
    # Behavioral patterns
    'behavioral_patterns': "行為模式",
    'early_rushing': "前期過快",
    'carelessness_issue': "粗心問題",
    'skill_override': "技能覆蓋",
    
    # General terms
    'recommendations': "建議",
    'analysis': "分析",
    'diagnosis': "診斷",
    'results': "結果",
    'summary': "摘要",
    'details': "詳情",
    'error': "錯誤",
    'correct': "正確",
    'slow': "慢",
    'fast': "快",
    'invalid': "無效",
    'valid': "有效",
    'threshold': "門檻",
    'time': "時間",
    'difficulty': "難度",
    'skill': "技能",
    'position': "位置",
    'type': "類型"
} 