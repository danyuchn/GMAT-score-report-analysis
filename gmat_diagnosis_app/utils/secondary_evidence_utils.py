"""
Secondary Evidence Utils
根據診斷參數動態生成二級證據查找重點提示
"""

from gmat_diagnosis_app.i18n import translate as t
import logging

def get_diagnostic_param_mapping():
    """
    Get mapping of diagnostic parameters to their focus areas and search strategies.
    Returns a dictionary mapping parameter codes to their analysis focus points.
    """
    return {
        # Q科診斷參數映射
        'Q_CARELESSNESS_DETAIL_OMISSION': {
            'subject': 'Q',
            'focus': '細節忽略和看錯',
            'search_strategy': '查找相同基礎技能下的快錯題目，特別關注計算錯誤和題目理解錯誤'
        },
        'Q_CONCEPT_APPLICATION_ERROR': {
            'subject': 'Q',
            'focus': '概念應用錯誤', 
            'search_strategy': '查找相同基礎技能（如代數、幾何等）的錯題，分析是否重複出現相同概念混淆'
        },
        'Q_CALCULATION_ERROR': {
            'subject': 'Q',
            'focus': '計算錯誤',
            'search_strategy': '查找相同基礎技能下的計算錯誤模式，確認是步驟錯誤還是運算錯誤'
        },
        'Q_READING_COMPREHENSION_ERROR': {
            'subject': 'Q',
            'focus': '文字理解問題',
            'search_strategy': '查找REAL題型的錯題記錄，分析是文字理解問題還是數學概念問題'
        },
        'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': {
            'subject': 'Q',
            'focus': t('v_foundation_instability_short'),
            'search_strategy': '查找涉及的基礎技能領域，分析基礎概念的掌握穩定性'
        },

        # V科診斷參數映射
        'CR_REASONING_CHAIN_ERROR': {
            'subject': 'V',
            'focus': 'CR邏輯鏈分析錯誤',
            'search_strategy': '查找相同CR題型（如削弱、加強、假設等）的錯誤模式，分析邏輯推理問題'
        },
        'CR_REASONING_CORE_ISSUE_ID_DIFFICULTY': {
            'subject': 'V',
            'focus': 'CR核心問題識別困難',
            'search_strategy': '查找CR題目的核心問題識別錯誤，分析題幹理解和論證結構分析能力'
        },
        'RC_READING_COMPREHENSION_ERROR_VOCAB': {
            'subject': 'V',
            'focus': 'RC詞彙理解錯誤',
            'search_strategy': '查找RC題目中的詞彙理解困難，確認是詞彙量問題還是語境理解問題'
        },
        'RC_READING_SENTENCE_STRUCTURE_DIFFICULTY': {
            'subject': 'V',
            'focus': 'RC句式理解困難',
            'search_strategy': '查找RC題目的長難句分析錯誤，分析句式結構理解能力'
        },
        'RC_REASONING_ERROR_INFERENCE': {
            'subject': 'V',
            'focus': 'RC推理錯誤',
            'search_strategy': '查找RC推理題的錯誤模式，分析是閱讀理解障礙還是邏輯推理問題'
        },
        'FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE': {
            'subject': 'V',
            'focus': '基礎掌握應用不穩定',
            'search_strategy': '查找涉及的核心技能領域，分析基礎能力的應用穩定性'
        },

        # DI科診斷參數映射
        'DI_READING_COMPREHENSION_ERROR__VOCABULARY': {
            'subject': 'DI',
            'focus': '文字理解 - 詞彙困難',
            'search_strategy': '查找相同內容領域（數學相關/非數學相關）的詞彙理解錯誤'
        },
        'DI_READING_COMPREHENSION_ERROR__SYNTAX': {
            'subject': 'DI',
            'focus': '文字理解 - 句式困難',
            'search_strategy': '查找相同題型的句式理解錯誤，分析長難句解析能力'
        },
        'DI_READING_COMPREHENSION_ERROR__LOGIC': {
            'subject': 'DI',
            'focus': '文字理解 - 邏輯困難',
            'search_strategy': '查找相同題型的邏輯理解錯誤，分析推理過程理解能力'
        },
        'DI_GRAPH_INTERPRETATION_ERROR__GRAPH': {
            'subject': 'DI',
            'focus': '圖表解讀 - 圖形信息',
            'search_strategy': '查找GT和MSR題型的圖形解讀錯誤，分析圖表信息提取能力'
        },
        'DI_GRAPH_INTERPRETATION_ERROR__TABLE': {
            'subject': 'DI',
            'focus': '圖表解讀 - 表格信息',
            'search_strategy': '查找GT和MSR題型的表格解讀錯誤，分析數據信息整合能力'
        },
        'DI_CONCEPT_APPLICATION_ERROR__MATH': {
            'subject': 'DI',
            'focus': '數學概念應用錯誤',
            'search_strategy': '查找數學相關領域的概念應用錯誤，分析數學觀念運用能力'
        },
        'DI_LOGICAL_REASONING_ERROR__NON_MATH': {
            'subject': 'DI',
            'focus': '非數學邏輯推理錯誤',
            'search_strategy': '查找非數學相關領域的邏輯推理錯誤，分析推理判斷能力'
        },
        'DI_MSR_READING_COMPREHENSION_BARRIER': {
            'subject': 'DI',
            'focus': 'MSR閱讀效率問題',
            'search_strategy': '查找MSR題組的閱讀時間分配問題，分析資料吸收和整合效率'
        },
        'DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE': {
            'subject': 'DI',
            'focus': t('v_foundation_instability_short'),
            'search_strategy': '查找相同題型和內容領域的基礎能力應用錯誤'
        },
        'DI_BEHAVIOR__CARELESSNESS_ISSUE': {
            'subject': 'DI',
            'focus': '粗心問題',
            'search_strategy': '查找快錯題目的模式，分析細節忽略和看錯問題'
        },
    }

def generate_dynamic_secondary_evidence_suggestions(processed_df):
    """
    Generate dynamic secondary evidence suggestions based on actual diagnostic parameters.
    
    Args:
        processed_df (pd.DataFrame): The processed dataframe with diagnostic parameters
        
    Returns:
        dict: Subject-specific secondary evidence suggestions based on actual diagnostic parameters
    """
    if processed_df is None or processed_df.empty:
        return {}
    
    # Filter out invalid data
    valid_df = processed_df.copy()
    if 'is_invalid' in processed_df.columns:
        valid_df = processed_df[~processed_df['is_invalid'].fillna(False)]
    
    if valid_df.empty:
        return {}
    
    # Get diagnostic parameter mapping
    param_mapping = get_diagnostic_param_mapping()
    
    # Collect diagnostic parameters by subject
    subject_params = {}
    subjects_in_data = valid_df['Subject'].unique() if 'Subject' in valid_df.columns else []
    
    for subject in subjects_in_data:
        if subject not in ['Q', 'V', 'DI']:
            continue
            
        subject_df = valid_df[valid_df['Subject'] == subject]
        collected_params = set()
        
        # Extract diagnostic parameters from the dataframe
        if 'diagnostic_params_list' in subject_df.columns:
            for _, row in subject_df.iterrows():
                params = row.get('diagnostic_params_list', [])
                if isinstance(params, list):
                    collected_params.update([p for p in params if p and isinstance(p, str)])
                elif isinstance(params, str) and params.strip():
                    collected_params.update([p.strip() for p in params.split(',') if p.strip()])
        
        subject_params[subject] = collected_params
    
    # Generate suggestions for each subject
    suggestions = {}
    
    for subject, params in subject_params.items():
        if not params:
            continue
            
        # Group parameters by focus areas
        focus_areas = {}
        unmatched_params = []
        
        for param in params:
            if param in param_mapping:
                param_info = param_mapping[param]
                focus = param_info['focus']
                strategy = param_info['search_strategy']
                
                if focus not in focus_areas:
                    focus_areas[focus] = []
                focus_areas[focus].append(strategy)
            else:
                unmatched_params.append(param)
        
        # Build subject-specific suggestion text
        suggestion_lines = []
        suggestion_lines.append(f"**{subject}科二級證據重點（基於您的診斷結果）：**")
        
        if focus_areas:
            for focus, strategies in focus_areas.items():
                # Use the first strategy for each focus area (they should be similar)
                strategy = strategies[0]
                suggestion_lines.append(f"- **{focus}**: {strategy}")
        
        # Add general guidance based on subject
        if subject == 'Q':
            suggestion_lines.append("- 特別注意：對比REAL和PURE題型的表現差異")
        elif subject == 'V':
            suggestion_lines.append("- 特別注意：區分CR和RC題型的不同問題模式")
        elif subject == 'DI':
            suggestion_lines.append("- 特別注意：分析不同題型（DS、TPA、GT、MSR）的錯誤集中點")
            suggestion_lines.append("- MSR題組：重點關注閱讀效率與時間分配問題")
        
        # Add sample size reminder
        suggestion_lines.append("- 注意：樣本數量少於10題時，統計參考價值有限")
        
        suggestions[subject] = "\n".join(suggestion_lines)
    
    return suggestions

def get_question_type_specific_guidance(subject, question_type, content_domain=None):
    """
    Get specific guidance for question type and content domain combinations.
    
    Args:
        subject (str): Subject code (Q, V, DI)
        question_type (str): Question type
        content_domain (str, optional): Content domain
        
    Returns:
        str: Specific guidance text
    """
    guidance_map = {
        # Q科題型指導
        ('Q', 'REAL'): "查找REAL題型錯題，重點分析文字理解和數學概念應用問題",
        ('Q', 'PURE'): "查找PURE題型錯題，重點分析純數學概念和計算問題",
        
        # V科題型指導
        ('V', 'Critical Reasoning'): "查找CR題型錯題，按題型分類（削弱、加強、假設等）分析錯誤模式",
        ('V', 'Reading Comprehension'): "查找RC題型錯題，分析是閱讀理解障礙還是題目分析問題",
        
        # DI科題型指導
        ('DI', 'Data Sufficiency'): "查找DS題型錯題，分析充分性判斷和邏輯推理問題",
        ('DI', 'Two-part analysis'): "查找TPA題型錯題，分析兩部分關聯性和推理問題", 
        ('DI', 'Graph and Table'): "查找GT題型錯題，重點分析圖表信息解讀和數據提取問題",
        ('DI', 'Multi-source reasoning'): "查找MSR題型錯題，重點分析多源信息整合和閱讀效率問題",
    }
    
    # Add content domain specific guidance for DI
    if subject == 'DI' and content_domain:
        base_guidance = guidance_map.get((subject, question_type), "")
        if content_domain == 'Math Related':
            return f"{base_guidance}，特別關注數學概念應用和計算錯誤"
        elif content_domain == 'Non-Math Related':
            return f"{base_guidance}，特別關注文字理解和邏輯推理錯誤"
    
    return guidance_map.get((subject, question_type), "根據題型特點分析錯誤模式")

def get_time_performance_specific_guidance(time_performance):
    """
    Get specific guidance based on time performance category.
    
    Args:
        time_performance (str): Time performance category
        
    Returns:
        str: Time-specific guidance text
    """
    guidance_map = {
        'Fast & Wrong': "重點查找快錯題目，分析粗心、細節忽略和過度自信問題",
        'Normal Time & Wrong': "查找正常時間錯題，分析概念理解和方法應用問題", 
        'Slow & Wrong': "查找慢錯題目，分析效率瓶頸和理解障礙問題",
        'Slow & Correct': "查找慢而對題目，分析效率瓶頸和時間分配問題"
    }
    
    return guidance_map.get(time_performance, "根據時間表現分析相應問題") 