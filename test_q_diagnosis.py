from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.i18n import translate as t
import pandas as pd

# 創建一個簡單的測試數據
test_data = {
    'Subject': ['Q'] * 5,
    'question_position': [1, 2, 3, 4, 5],
    'question_type': ['Real', 'Pure', 'Real', 'Pure', 'Real'],
    'question_fundamental_skill': ['Counting/Sets/Series/Prob/Stats', 'Equal/Unequal/ALG', 'Value/Order/Factors', 'Rates/Ratio/Percent', 'Counting/Sets/Series/Prob/Stats'],
    'question_difficulty': [1.6, 1.2, 1.8, 0.8, 1.7],
    'question_time': [1.5, 2.5, 3.3, 2.0, 1.3],  # 使用question_time而不是time_seconds
    'is_correct': [False, True, False, True, False],
    'diagnostic_params_list': [
        ['Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE', 'Q_CALCULATION_ERROR'],
        [],
        ['Q_READING_COMPREHENSION_ERROR'],
        [],
        ['Q_CONCEPT_APPLICATION_ERROR', 'Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE']
    ],
    'is_manually_invalid': [False] * 5  # 添加這個列
}

df = pd.DataFrame(test_data)
print("Q診斷測試開始...")
try:
    results, report, df_diagnosed = diagnose_q(df, include_summary_report=True)
    print('測試完成，診斷報告生成成功')
    print('報告長度:', len(report) if report else 0)
    print("\n=== 診斷報告前500字 ===")
    print(report[:500] if report else "無報告內容")
    
    if "練習建議" in report:
        print("\n報告包含練習建議 ✓")
    else:
        print("\n報告缺少練習建議 ✗")
        
    if "行為模式觀察" in report:
        print("報告包含行為模式觀察 ✓")
    else:
        print("報告缺少行為模式觀察 ✗")
        
except Exception as e:
    print(f"測試失敗: {e}")
    import traceback
    traceback.print_exc() 