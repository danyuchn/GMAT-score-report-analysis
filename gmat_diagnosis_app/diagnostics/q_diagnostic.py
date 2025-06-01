"""
Q診斷主模塊

此模塊提供了Q(Quantitative)診斷的主要入口點。
實際邏輯已分拆到 q_modules 子包中的相關模塊實現。
"""

import pandas as pd

# 從 q_modules 子包導入主要功能
from gmat_diagnosis_app.diagnostics.q_modules import run_q_diagnosis

# 主要診斷函數，保留與原始函數相同的簽名
def diagnose_q(df, include_summaries=False, include_individual_errors=False, include_summary_report=True):
    """
    Q診斷主函數 - 通過調用 q_modules.run_q_diagnosis 實現核心功能
    
    Args:
        df (pd.DataFrame): Q科目數據
        include_summaries (bool): 是否包含詳細摘要
        include_individual_errors (bool): 是否包含個別錯誤詳情
        include_summary_report (bool): 是否生成摘要報告
        
    Returns:
        tuple: (診斷結果, 報告字串, 處理後的DataFrame)
    """
    # Calculate time pressure status from data
    time_pressure_status = False
    if not df.empty and 'question_time' in df.columns:
        total_time = pd.to_numeric(df['question_time'], errors='coerce').sum(skipna=True)
        # Q科目45分鐘限制，如果用時超過40分鐘則認為有時間壓力
        time_pressure_status = total_time > 40.0
    
    return run_q_diagnosis(
        df_processed=df,
        time_pressure_status=time_pressure_status,
        include_summaries=include_summaries,
        include_individual_errors=include_individual_errors,
        include_summary_report=include_summary_report
    )