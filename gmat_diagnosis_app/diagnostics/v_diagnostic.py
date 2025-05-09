"""
V診斷主模塊

此模塊提供了V(Verbal)診斷的主要入口點。
實際邏輯已分拆到 v_modules 子包中的相關模塊實現。
"""

# import pandas as pd # Removed, as pd is not directly used in this forwarding module.

# 從 v_modules 子包導入主要功能
# 確保 main 模塊中定義了 run_v_diagnosis_processed
from gmat_diagnosis_app.diagnostics.v_modules.main import run_v_diagnosis_processed as run_v_diag_processed_from_module

# 主要診斷函數，保留與原始函數相同的簽名
def run_v_diagnosis_processed(df_v_processed, v_time_pressure_status, v_avg_time_per_type):
    """
    V診斷主函數 - 通過調用 v_modules.main.run_v_diagnosis_processed 實現核心功能
    
    Args:
        df_v_processed (pd.DataFrame): 預處理過的Verbal題目數據
        v_time_pressure_status (bool): Verbal部分的時間壓力狀態
        v_avg_time_per_type (dict): Verbal部分各題型的平均時間

    Returns:
        dict: 診斷結果。
        str: 摘要報告。
        pd.DataFrame: 包含診斷標籤的處理後數據框。
    """
    # 直接委託給模塊化的實現
    return run_v_diag_processed_from_module(
        df_v_processed,
        v_time_pressure_status,
        v_avg_time_per_type
    )

# --- 原始文件中的其他代碼已被移除，因為邏輯已移至 v_modules ---
# (例如：常數、輔助函數、各章節的詳細診斷邏輯等)