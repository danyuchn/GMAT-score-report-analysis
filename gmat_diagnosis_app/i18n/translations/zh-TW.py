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
    'type': "類型",
    
    # Q Diagnostic Reporting - Hardcoded Chinese text from reporting.py
    'q_report_title': "Q 科診斷報告詳情",
    'q_report_subtitle': "（基於用戶數據與模擬難度分析）",
    'report_overview_feedback': "**一、 報告總覽與即時反饋**",
    'time_strategy_assessment': "* **A. 作答時間與策略評估**",
    'time_pressure_status_label': "時間壓力狀態：",
    'overtime_threshold_used': "使用的超時閾值：",
    'minutes': "分鐘",
    'important_notes': "* **B. 重要註記**",
    'manual_invalid_data_count': "手動標記無效數據題數：",
    'valid_score_rate': "有效評分率（基於手動無效排除）：",
    'yes': "有",
    'no': "無",
    
    'core_performance_analysis': "**二、 核心表現分析**",
    'content_domain_overview': "* **A. 內容領域表現概覽**",
    'by_question_type': "* **按題型 (Real vs Pure):**",
    'real_performance_poor': "Real 題目表現較差：錯誤率顯著高於 Pure 題目",
    'pure_performance_poor': "Pure 題目表現較差：錯誤率顯著高於 Real 題目",
    'real_slower': "Real 題目較慢：超時率顯著高於 Pure 題目",
    'pure_slower': "Pure 題目較慢：超時率顯著高於 Pure 題目",
    'no_significant_difference': "Real 和 Pure 題型表現無顯著差異",
    'error_difficulty_distribution': "* **錯誤難度分佈:**",
    'questions_count': "題",
    
    'core_issues_diagnosis': "**三、 核心問題診斷**",
    'high_frequency_potential_issues': "* **B. 高頻潛在問題點**",
    'sfe_attention_note': "尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤",
    'sfe_skills_involved': "，涉及技能:",
    'sfe_stability_problem': "，這表明在這些知識點的應用上可能存在穩定性問題。",
    'careless_tendency': "傾向於快速作答但出錯，可能涉及",
    'concept_understanding_issue': "花費了較長時間但仍無法解決部分問題，或對問題理解存在偏差，可能涉及",
    'calculation_error_cause': "計算錯誤也是失分原因",
    'reading_comprehension_barrier': "Real題的文字信息理解可能存在障礙",
    'efficiency_time_consumption': "部分題目雖然做對，但在{}等環節耗時過長 ({})，反映了應用效率有待提升。",
    'no_core_issues_identified': "未識別出主要的核心問題模式。",
    'reading_real_questions': "Real題閱讀",
    'concept_thinking': "概念思考",
    'calculation_process': "計算過程",
    'or': " 或 ",
    
    'special_behavioral_patterns': "* **C. 特殊行為模式觀察**",
    'early_rushing_warning': "測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 \"flag for review\" 風險。",
    'carelessness_analysis': "分析顯示，「快而錯」的情況佔比較高 ({})，提示可能需要關注答題的仔細程度，減少粗心錯誤。",
    'no_special_patterns': "未發現明顯的特殊作答模式。",
    
    'practice_consolidation': "**三、 練習建議與基礎鞏固**",
    'priority_consolidation_skills': "* **A. 優先鞏固技能**",
    'core_skills_consolidation': "對於 [**{}**] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。",
    'no_skill_override_triggered': "未觸發需要優先進行基礎鞏固的技能覆蓋規則。",
    
    'overall_practice_direction': "* **B. 整體練習方向**",
    'sfe_priority_note': "(注意：涉及「**基礎掌握不穩**」的建議已優先列出)",
    'no_specific_practice_recommendations': "無具體練習建議生成。",
    
    'follow_up_action_guidance': "**四、 後續行動與深度反思指引**",
    'guided_reflection_prompts': "* **B. 引導性反思提示 (針對特定技能與表現)**",
    'reflection_instruction': "找尋【{}】【{}】的考前做題紀錄，找尋【{}】的題目，檢討並反思自己是否有：",
    'problems_category': "等問題。",
    'default_reflection_prompt': "找尋考前做題紀錄中的錯題，按照【基礎技能】【題型】【時間表現】【診斷標籤】等維度進行分析和反思，找出系統性的問題和改進方向。",
    
    'practice_record_review': "* **A. 檢視練習記錄 (二級證據參考)**",
    'review_purpose': "* **目的：** 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。",
    'review_method': "* **方法：** 建議您按照以上引導反思查看近期的練習記錄，整理相關錯題或超時題目。",
    'key_focus': "* **重點關注：** 題目是否反覆涉及報告第三部分指出的核心問題：",
    'key_focus_general': "* **重點關注：** 根據核心表現分析，留意常見錯誤類型。",
    'sample_insufficient_note': "* **注意：** 如果樣本不足，請在接下來的做題中注意收集，以便更準確地定位問題。",
    'no_secondary_evidence_needed': "(本次分析未發現需要二級證據深入探究的問題點，或數據不足)",
    
    'advanced_assistance': "**五、 尋求進階協助 (質化分析)**",
    'qualitative_analysis_suggestion': "* **建議：** 如果您對報告中指出的某些問題仍感困惑，可以嘗試 **提供 2-3 題相關錯題的詳細解題流程跟思路範例** ，供顧問進行更深入的個案分析。",
    
    # Utility functions translations
    'unknown_difficulty': "未知難度 (Unknown)",
    'low_difficulty': "低難度 (Low) / 505+",
    'mid_difficulty_555': "中難度 (Mid) / 555+",
    'mid_difficulty_605': "中難度 (Mid) / 605+",
    'mid_difficulty_655': "中難度 (Mid) / 655+",
    'high_difficulty_705': "高難度 (High) / 705+",
    'high_difficulty_805': "高難度 (High) / 805+",
    'unknown_difficulty_short': "未知難度",
    
    # Main diagnosis module translations
    'report_generation_disabled': "報告生成被禁用或遇到問題。",
    
    # AI prompts module translations
    'no_data_for_analysis': "(無數據可供分析)",
    'no_diagnostic_tags_found': "(未找到診斷標籤)",
    
    # Recommendations module translations
    'macro_comprehensive_foundation': "**優先全面鞏固基礎** (整體錯誤率或超時率 > 50%): 從 {} 難度開始, 建議限時 {} 分鐘。",
    'start_from_basic_difficulty': "建議從基礎難度開始 (具體難度未知)",
    'question_related_trigger': "第 {} 題相關",
    'correct_but_slow_marker': " (正確但慢)",
    'practice_details': "練習 {}, 限時 {} 分鐘。",
    'practice_details_speed': "練習 {}, 限時 {} 分鐘 (提升速度)。",
    'foundation_instability_marker': "*基礎掌握不穩* {}",
    'practice_volume_warning': " **注意：起始限時遠超目標，需加大練習量以確保逐步限時有效**",
    'real_questions_ratio_note': " **Real題比例建議佔總練習題量2/3。**",
    'increase_practice_volume_note': " **建議此考點練習題量增加。**",
    'overall_practice_notes': "整體練習註記: {}",
    'skill_label': "技能: {}",
    'skill_perfect_exemption': "* 技能 {} 表現完美，已豁免練習建議。",
    'no_specific_skill_recommendation': "* (關於技能 {} 無特定建議，請參考整體總結。)",
    'no_quantitative_recommendations': "根據本次分析，未產生具體的量化練習建議。請參考整體診斷總結。",
    
    # Time performance categories
    'fast_wrong': "快錯",
    'slow_wrong': "慢錯",
    'normal_time_wrong': "正常時間錯",
    
    # Problem categories for reflection
    'carelessness_problems': "粗心問題",
    'reading_comprehension_problems': "閱讀理解問題",
    'calculation_problems': "計算問題",
    'concept_application_problems': "概念應用問題",
    'efficiency_problems': "效率問題",
    'problem_types': "問題類型",
    
    # AI tool recommendations
    'q_ai_tool_recommendations': "Q 科目 AI 輔助建議",
    'q_no_data_for_ai': "(Q科無數據可生成AI建議。)",
    'q_missing_diagnostic_params': "(Q科數據缺少 'diagnostic_params_list' 欄位，無法生成AI建議。)",
    'q_no_specific_ai_recommendations': "(根據您的Q科編輯，未觸發特定的工具或 AI 提示建議。)",
    'q_ai_missing_config': "(AI建議配置缺失，無法生成Q科建議。)",
    'ai_diagnosis_involves': "**若診斷涉及【{}】:**",
    'general_gmat_q_tool_suggestion': "未找到特定匹配的工具建議。建議參考GMAT官方指南中的Q科相關練習和策略。"
} 