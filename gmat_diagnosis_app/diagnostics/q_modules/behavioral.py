"""
Q診斷模塊的行為模式分析功能

此模塊包含用於Q(Quantitative)診斷的行為模式分析函數，
用於識別學生的作答行為模式。
"""

import pandas as pd
import numpy as np
from gmat_diagnosis_app.diagnostics.q_modules.translations import get_translation
from gmat_diagnosis_app.diagnostics.q_modules.constants import CARELESSNESS_THRESHOLD


def analyze_behavioral_patterns(df_q_valid_diagnosed):
    """Analyzes behavioral patterns for Chapter 5."""
    
    # --- Chapter 5: Special Patterns ---
    # 初始化結果
    early_rushing_flag = False
    early_rushing_items = []
    carelessness_issue = False
    fast_wrong_rate = 0.0
    
    # 前期過快檢測
    if 'question_position' in df_q_valid_diagnosed.columns and 'question_time' in df_q_valid_diagnosed.columns:
        # 計算題目總數的前三分之一
        positions = sorted(df_q_valid_diagnosed['question_position'].unique())
        first_third_end = max(1, len(positions) // 3)
        first_third_positions = positions[:first_third_end]
        
        # 在前三分之一題目中找出作答時間 < 1.0 分鐘的題目
        first_third_mask = df_q_valid_diagnosed['question_position'].isin(first_third_positions)
        df_first_third = df_q_valid_diagnosed[first_third_mask]
        df_first_third_fast = df_first_third[df_first_third['question_time'] < 1.0]
        
        if not df_first_third_fast.empty:
            early_rushing_flag = True
            early_rushing_items = df_first_third_fast['question_position'].tolist()
    
    # 粗心問題評估
    # 獲取時間表現分類為"Fast & Wrong"的題目數量
    fast_wrong_count = df_q_valid_diagnosed[df_q_valid_diagnosed['time_performance_category'] == 'Fast & Wrong'].shape[0]
    
    # 獲取所有"Fast"相關分類的題目總數（Fast & Wrong + Fast & Correct）
    all_fast_count = df_q_valid_diagnosed[df_q_valid_diagnosed['time_performance_category'].str.startswith('Fast')].shape[0]
    
    # 計算快錯率：所有快速作答中錯誤的比例
    if all_fast_count > 0:
        fast_wrong_rate = fast_wrong_count / all_fast_count
        # 使用 CARELESSNESS_THRESHOLD 常數作為閾值
        if fast_wrong_rate > CARELESSNESS_THRESHOLD:
            carelessness_issue = True
            
    # 整理結果
    return {
        "early_rushing_flag": early_rushing_flag, 
        "early_rushing_items": early_rushing_items, 
        "carelessness_issue_flag": carelessness_issue, 
        "fast_wrong_rate": fast_wrong_rate
    }


def analyze_skill_override(df_q_valid_diagnosed):
    """Analyzes skill override for Chapter 6."""
    
    # --- Chapter 6: Skill Override Rule ---
    skill_override_flags = {}
    skills_in_data = df_q_valid_diagnosed['question_fundamental_skill'].unique()
    skills_in_data = [s for s in skills_in_data if pd.notna(s) and s != 'Unknown Skill']
    
    for skill in skills_in_data:
        skill_df = df_q_valid_diagnosed[df_q_valid_diagnosed['question_fundamental_skill'] == skill]
        if len(skill_df) == 0: 
            continue
        
        num_errors = (skill_df['is_correct'] == False).sum()
        num_overtimes = (skill_df['overtime'] == True).sum() if 'overtime' in skill_df.columns else 0
        total_skill_qs = len(skill_df)
        
        error_rate = num_errors / total_skill_qs if total_skill_qs > 0 else 0
        overtime_rate = num_overtimes / total_skill_qs if total_skill_qs > 0 else 0
        
        # 使用 0.5 (50%) 閾值判斷是否觸發覆蓋規則
        override_triggered = error_rate > 0.5 or overtime_rate > 0.5
        
        if override_triggered:
            # 如果觸發，則尋找最低難度值
            error_or_overtime_mask = (skill_df['is_correct'] == False) | (skill_df['overtime'] == True)
            triggering_df = skill_df[error_or_overtime_mask]
            min_difficulty = None
            if not triggering_df.empty and 'question_difficulty' in triggering_df.columns:
                valid_difficulties = triggering_df['question_difficulty'].dropna()
                if not valid_difficulties.empty:
                    min_difficulty = valid_difficulties.min()
            
            # 使用從utils導入的函數轉換難度
            from gmat_diagnosis_app.diagnostics.q_modules.utils import map_difficulty_to_label
            
            skill_override_flags[skill] = {
                'triggered': True,
                'error_rate': error_rate,
                'overtime_rate': overtime_rate,
                'min_difficulty': min_difficulty,
                'y_agg': map_difficulty_to_label(min_difficulty) if min_difficulty is not None else None,
                'z_agg': 2.5  # 固定的宏觀限時值
            }
        else:
            skill_override_flags[skill] = {'triggered': False}

    return skill_override_flags 