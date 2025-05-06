"""
Q診斷主模塊

此模塊提供了Q(Quantitative)診斷的主要入口點。
實際邏輯已分拆到 q_modules 子包中的相關模塊實現。
"""

# 從 q_modules 子包導入主要功能
from gmat_diagnosis_app.diagnostics.q_modules import diagnose_q_main

# 主要診斷函數，保留與原始函數相同的簽名
def diagnose_q(df, include_summaries=False, include_individual_errors=False, include_summary_report=True):
    """
    Q診斷主函數 - 通過調用 q_modules.diagnose_q_main 實現核心功能
    
    Args:
        df (DataFrame): 輸入數據框，包含問題數據
        include_summaries (bool): 是否包含詳細摘要數據
        include_individual_errors (bool): 是否包含個別錯誤詳情
        include_summary_report (bool): 是否生成文本摘要報告
    
    Returns:
        dict: 診斷結果、建議和報告
    """
    # 直接委託給模塊化的實現
    return diagnose_q_main(df, include_summaries, include_individual_errors, include_summary_report)