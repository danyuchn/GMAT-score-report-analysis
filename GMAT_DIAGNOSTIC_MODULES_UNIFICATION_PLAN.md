# GMAT 診斷模組結構統一化實施計劃

**版本**: v1.0  
**分支**: gui-rewrite-7  
**創建日期**: 2025-01-30  
**目標**: 統一 di_modules、q_modules、v_modules 三個診斷模組的結構、命名和介面，提升可維護性

---

## 📋 **目錄**

1. [現狀分析](#現狀分析)
2. [統一化目標](#統一化目標)
3. [實施階段規劃](#實施階段規劃)
4. [詳細實施步驟](#詳細實施步驟)
5. [命名標準規範](#命名標準規範)
6. [測試驗證計劃](#測試驗證計劃)
7. [風險評估與回滾策略](#風險評估與回滾策略)

---

## 🔍 **現狀分析**

### **檔案結構差異**

| 模組 | 檔案列表 | 特有檔案 |
|------|----------|----------|
| **di_modules** | `main.py`, `chapter_logic.py`, `report_generation.py`, `utils.py`, `constants.py`, `ai_prompts.py`, `translation.py`, `__init__.py` | `chapter_logic.py`, `report_generation.py`, `translation.py` |
| **q_modules** | `main.py`, `analysis.py`, `reporting.py`, `behavioral.py`, `utils.py`, `constants.py`, `ai_prompts.py`, `recommendations.py`, `translations.py`, `__init__.py` | `analysis.py`, `behavioral.py`, `translations.py` |
| **v_modules** | `main.py`, `analysis.py`, `reporting.py`, `recommendations.py`, `utils.py`, `constants.py`, `ai_prompts.py`, `translations.py`, `__init__.py` | `analysis.py`, `translations.py` |

### **主要問題識別**

1. **檔案命名不一致**: `chapter_logic.py` vs `analysis.py`, `report_generation.py` vs `reporting.py`
2. **函數命名模式差異**: DI模組使用底線前綴，Q/V模組不使用
3. **主入口函數不統一**: 函數名、參數列表、返回值格式不一致
4. **參數命名約定混亂**: DataFrame 參數命名不統一
5. **模組結構差異**: 缺少統一的檔案組織邏輯

---

## 🎯 **統一化目標**

### **核心目標**
1. **結構統一**: 建立標準化的檔案結構和命名規範
2. **介面統一**: 標準化主入口函數的參數和返回值
3. **命名統一**: 統一函數、參數、變數的命名約定
4. **可維護性提升**: 減少重複代碼，提高代碼可讀性
5. **擴展性增強**: 建立清晰的模組擴展範本

### **保持差異的部分**
- 各科目特有的計算邏輯
- 診斷參數標籤內容
- 報告格式的科目特異性
- 業務邏輯的科目差異

---

## 📅 **實施階段規劃**

### **階段一: 準備階段** (1-2天) ✅ 已完成
- [x] 代碼備份與分支管理
- [x] 依賴關係分析
- [x] 測試案例準備

### **階段二: 檔案結構統一** (2-3天) ✅ 已完成
- [x] 檔案重新命名
- [x] 匯入語句更新
- [x] 結構調整驗證

### **階段三: 函數命名統一** (2-3天) ✅ 已完成
- [x] DI模組底線前綴移除
- [x] 工具函數命名標準化
- [x] 函數調用更新

### **階段四: 介面標準化** (3-4天) 🔄 進行中
- [ ] 主入口函數統一
- [ ] 參數命名標準化
- [ ] 返回值格式統一

### **階段五: 測試與驗證** (2-3天)
- [ ] 單元測試執行
- [ ] 整合測試驗證
- [ ] 性能回歸測試

### **階段六: 文件更新** (1天)
- [ ] API文件更新
- [ ] 使用說明更新
- [ ] 代碼註解完善

---

## 🛠 **詳細實施步驟**

### **Step 1: 環境準備**

#### **1.1 代碼備份**
```bash
# 確保當前分支是 gui-rewrite-7
git checkout gui-rewrite-7

# 創建備份標籤
git tag backup-before-unification-$(date +%Y%m%d)

# 確認所有變更已提交
git status
```

#### **1.2 依賴關係分析**
```bash
# 檢查模組間的匯入關係
find gmat_diagnosis_app/diagnostics -name "*.py" -exec grep -l "from.*modules" {} \;

# 檢查外部調用
grep -r "di_modules\|q_modules\|v_modules" gmat_diagnosis_app/ --include="*.py"
```

### **Step 2: 檔案結構統一**

#### **2.1 DI模組檔案重新命名**

**執行順序**:
1. `chapter_logic.py` → `analysis.py`
2. `report_generation.py` → `reporting.py`
3. 移除 `translation.py` (已統一使用i18n)

```bash
# 在 di_modules 目錄下執行
cd gmat_diagnosis_app/diagnostics/di_modules

# 重新命名檔案
git mv chapter_logic.py analysis.py
git mv report_generation.py reporting.py

# 檢查 translation.py 是否還有引用
grep -r "translation" . --include="*.py"

# 如果沒有引用，移除 translation.py
git rm translation.py
```

#### **2.2 更新匯入語句**

**DI模組 main.py 更新**:
```python
# 修改前
from .chapter_logic import (
    _diagnose_root_causes, _observe_di_patterns, _check_foundation_override, _generate_di_recommendations
)
from .report_generation import _generate_di_summary_report

# 修改後  
from .analysis import (
    diagnose_root_causes, observe_di_patterns, check_foundation_override, generate_di_recommendations
)
from .reporting import generate_di_summary_report
```

#### **2.3 檢查並建立缺失檔案**

**為DI模組新增 recommendations.py**:
```python
# 創建 gmat_diagnosis_app/diagnostics/di_modules/recommendations.py
def generate_di_recommendations(diagnosis_results):
    """
    生成DI診斷建議
    
    Args:
        diagnosis_results (dict): 診斷結果
        
    Returns:
        list: 建議列表
    """
    # 從 analysis.py 中移動相關邏輯到此處
    pass
```

### **Step 3: 函數命名統一**

#### **3.1 移除DI模組底線前綴**

**utils.py 函數重新命名**:
```python
# 修改前
def _format_rate(rate_value):
def _grade_difficulty_di(difficulty):
def _analyze_dimension(df_filtered, dimension_col):

# 修改後
def format_rate(rate_value):
def grade_difficulty_di(difficulty):
def analyze_dimension(df_filtered, dimension_col):
```

#### **3.2 統一工具函數命名格式**

**各模組 utils.py 標準化**:
```python
# 統一的函數命名模式

# 基礎工具函數 (所有模組共同)
def format_rate(rate_value): pass
def analyze_dimension(df_filtered, dimension_col): pass

# 科目特定函數 (添加科目後綴)
def grade_difficulty_di(difficulty): pass    # DI模組
def grade_difficulty_q(difficulty): pass     # Q模組
def grade_difficulty_v(difficulty): pass     # V模組
```

#### **3.3 更新所有函數調用**

**批量更新策略**:
```bash
# 搜索並替換DI模組的函數調用
find gmat_diagnosis_app/diagnostics/di_modules -name "*.py" -exec sed -i 's/_format_rate/format_rate/g' {} \;
find gmat_diagnosis_app/diagnostics/di_modules -name "*.py" -exec sed -i 's/_grade_difficulty_di/grade_difficulty_di/g' {} \;
find gmat_diagnosis_app/diagnostics/di_modules -name "*.py" -exec sed -i 's/_analyze_dimension/analyze_dimension/g' {} \;
```

### **Step 4: 主入口函數標準化**

#### **4.1 統一函數簽名**

**標準化的主入口函數格式**:
```python
def run_{subject}_diagnosis(
    df_processed: pd.DataFrame,
    time_pressure_status: bool,
    avg_time_per_type: Optional[Dict[str, float]] = None,
    include_summaries: bool = False,
    include_individual_errors: bool = False,
    include_summary_report: bool = True
) -> Tuple[Dict, str, pd.DataFrame]:
    """
    {科目}診斷主入口函數
    
    Args:
        df_processed: 預處理後的DataFrame，包含is_invalid標記
        time_pressure_status: 時間壓力狀態布林值
        avg_time_per_type: 各題型平均時間字典，可選
        include_summaries: 是否包含詳細摘要數據
        include_individual_errors: 是否包含個別錯誤詳情
        include_summary_report: 是否生成文字摘要報告
        
    Returns:
        tuple: (診斷結果字典, 報告字串, 帶診斷標記的DataFrame)
    """
```

#### **4.2 各模組主函數重構**

**DI模組 main.py**:
```python
def run_di_diagnosis(
    df_processed: pd.DataFrame,
    time_pressure_status: bool,
    avg_time_per_type: Optional[Dict[str, float]] = None,
    include_summaries: bool = False,
    include_individual_errors: bool = False,
    include_summary_report: bool = True
) -> Tuple[Dict, str, pd.DataFrame]:
    """DI診斷主入口函數"""
    # 重構現有的 run_di_diagnosis_logic 邏輯
    # 統一參數處理和返回值格式
    pass
```

**Q模組 main.py**:
```python
def run_q_diagnosis(
    df_processed: pd.DataFrame,
    time_pressure_status: bool,
    avg_time_per_type: Optional[Dict[str, float]] = None,
    include_summaries: bool = False,
    include_individual_errors: bool = False,
    include_summary_report: bool = True
) -> Tuple[Dict, str, pd.DataFrame]:
    """Q診斷主入口函數"""
    # 重構現有的 diagnose_q_main 邏輯
    # 統一參數處理和返回值格式
    pass
```

**V模組 main.py**:
```python
def run_v_diagnosis(
    df_processed: pd.DataFrame,
    time_pressure_status: bool,
    avg_time_per_type: Optional[Dict[str, float]] = None,
    include_summaries: bool = False,
    include_individual_errors: bool = False,
    include_summary_report: bool = True
) -> Tuple[Dict, str, pd.DataFrame]:
    """V診斷主入口函數"""
    # 重構現有的 run_v_diagnosis_processed 邏輯
    # 統一參數處理和返回值格式
    pass
```

### **Step 5: 參數命名標準化**

#### **5.1 DataFrame參數統一**

**標準命名約定**:
```python
# 統一使用的DataFrame參數名
df_processed          # 主要輸入DataFrame (預處理後)
df_valid             # 過濾後的有效數據
df_diagnosed         # 添加診斷標記後的數據
df_analysis          # 用於分析的DataFrame子集
```

#### **5.2 診斷結果結構統一**

**標準返回值結構**:
```python
# 診斷結果字典結構
diagnosis_results = {
    'subject': 'DI/Q/V',                    # 科目標識
    'total_questions': int,                 # 總題數
    'valid_questions': int,                 # 有效題數
    'invalid_count': int,                   # 無效題數
    'time_pressure_status': bool,           # 時間壓力狀態
    'chapters': {                           # 各章節分析結果
        'chapter1': {...},
        'chapter2': {...},
        # ...
    },
    'recommendations': [...],               # 建議列表
    'summary_stats': {...},                # 統計摘要
    'diagnostic_params': [...]             # 診斷參數列表
}
```

### **Step 6: 統一常數和配置**

#### **6.1 提取共同常數**

**創建共同常數檔案**: `gmat_diagnosis_app/diagnostics/common_constants.py`
```python
"""
診斷模組共用常數定義
"""

# 時間相關常數
INVALID_TIME_THRESHOLD_MINUTES = 0.5
ABSOLUTE_FAST_THRESHOLD_MINUTES = 1.0
SUSPICIOUS_FAST_MULTIPLIER = 0.5

# 超時閾值
OVERTIME_THRESHOLDS = {
    True: 2.5,   # 有時間壓力
    False: 3.0   # 無時間壓力
}

# 診斷相關常數
DIFFICULTY_THRESHOLDS = {
    'LOW': -1.0,
    'MID_LOW': 0.0,
    'MID_HIGH': 1.0,
    'HIGH': 1.5,
    'VERY_HIGH': 1.95
}

# 報告格式常數
MAX_INDIVIDUAL_ERRORS_DISPLAY = 10
RATE_DISPLAY_PRECISION = 2
```

#### **6.2 各模組constants.py重構**

**保留科目特定常數**:
```python
# di_modules/constants.py - 僅保留DI特有常數
from ..common_constants import *  # 匯入共同常數

# DI特有常數
MAX_ALLOWED_TIME_DI = 45
TIME_PRESSURE_THRESHOLD_DI = 3
MSR_GROUP_THRESHOLDS = {...}
```

---

## 📏 **命名標準規範**

### **檔案命名標準**

| 檔案類型 | 命名格式 | 說明 |
|----------|----------|------|
| 主入口 | `main.py` | 包含主診斷函數 |
| 核心分析 | `analysis.py` | 診斷邏輯和計算 |
| 報告生成 | `reporting.py` | 報告格式化和輸出 |
| 建議生成 | `recommendations.py` | 練習建議生成 |
| 工具函數 | `utils.py` | 輔助函數 |
| 常數定義 | `constants.py` | 常數和配置 |
| AI提示 | `ai_prompts.py` | AI相關功能 |
| 行為分析 | `behavioral.py` | 行為模式分析(可選) |

### **函數命名標準**

| 函數類型 | 命名格式 | 範例 |
|----------|----------|------|
| 主入口函數 | `run_{subject}_diagnosis` | `run_di_diagnosis` |
| 分析函數 | `analyze_{feature}` | `analyze_time_patterns` |
| 計算函數 | `calculate_{metric}` | `calculate_error_rate` |
| 生成函數 | `generate_{output}` | `generate_recommendations` |
| 格式化函數 | `format_{type}` | `format_rate` |
| 工具函數 | `{verb}_{noun}` | `grade_difficulty_di` |

### **變數命名標準**

| 變數類型 | 命名格式 | 範例 |
|----------|----------|------|
| DataFrame | `df_{description}` | `df_processed`, `df_valid` |
| 時間相關 | `{type}_time` | `question_time`, `avg_time` |
| 狀態標記 | `{feature}_status` | `time_pressure_status` |
| 計數器 | `num_{item}` | `num_errors`, `num_total` |
| 比率 | `{item}_rate` | `error_rate`, `overtime_rate` |
| 字典/映射 | `{item}_mapping` | `difficulty_mapping` |

### **常數命名標準**

| 常數類型 | 命名格式 | 範例 |
|----------|----------|------|
| 閾值 | `{FEATURE}_THRESHOLD` | `INVALID_TIME_THRESHOLD` |
| 上限/下限 | `MAX_{ITEM}`, `MIN_{ITEM}` | `MAX_ALLOWED_TIME` |
| 倍數 | `{FEATURE}_MULTIPLIER` | `SUSPICIOUS_FAST_MULTIPLIER` |
| 標籤 | `{TYPE}_TAG_{SUBJECT}` | `INVALID_DATA_TAG_DI` |

---

## 🧪 **測試驗證計劃**

### **單元測試策略**

#### **測試檔案結構**
```
tests/
├── unit/
│   ├── test_di_diagnosis.py
│   ├── test_q_diagnosis.py
│   ├── test_v_diagnosis.py
│   └── test_common_utils.py
├── integration/
│   ├── test_diagnosis_pipeline.py
│   └── test_cross_module.py
└── fixtures/
    ├── sample_di_data.json
    ├── sample_q_data.json
    └── sample_v_data.json
```

#### **關鍵測試案例**

**功能測試**:
```python
def test_unified_main_function_signature():
    """測試主入口函數簽名統一性"""
    # 確保所有模組的主函數具有相同的參數格式

def test_return_value_structure():
    """測試返回值結構一致性"""
    # 確保所有模組返回相同格式的結果

def test_diagnostic_params_format():
    """測試診斷參數格式統一性"""
    # 確保診斷參數的格式和結構一致
```

**回歸測試**:
```python
def test_diagnosis_results_consistency():
    """測試診斷結果一致性"""
    # 使用相同測試數據，確保重構前後結果一致

def test_performance_regression():
    """測試性能回歸"""
    # 確保重構後性能沒有明顯下降
```

### **整合測試計劃**

#### **測試場景**
1. **完整診斷流程測試**: 從原始數據到最終報告
2. **跨模組調用測試**: 確保模組間調用正常
3. **邊界條件測試**: 空數據、異常數據處理
4. **並發測試**: 多模組同時運行的穩定性

#### **驗證檢查清單**

- [ ] 所有主入口函數具有統一簽名
- [ ] 返回值結構完全一致
- [ ] 函數命名遵循新標準
- [ ] 檔案結構符合規範
- [ ] 匯入語句正確更新
- [ ] 診斷結果與原版本一致
- [ ] 性能測試通過
- [ ] 代碼覆蓋率維持或提升

---

## ⚠️ **風險評估與回滾策略**

### **潛在風險**

| 風險類型 | 風險描述 | 影響程度 | 發生機率 |
|----------|----------|----------|----------|
| **功能回歸** | 重構導致診斷結果錯誤 | 高 | 中 |
| **性能下降** | 代碼結構變更影響性能 | 中 | 低 |
| **匯入錯誤** | 模組重新命名導致匯入失敗 | 高 | 中 |
| **數據不一致** | 參數傳遞錯誤導致結果差異 | 高 | 低 |
| **向後兼容** | 外部調用程式受影響 | 中 | 高 |

### **風險緩解措施**

#### **預防措施**
1. **充分測試**: 執行完整的單元測試和整合測試
2. **漸進式重構**: 分階段實施，每階段都進行驗證
3. **代碼審查**: 每個變更都經過詳細審查
4. **文件更新**: 及時更新相關文件和說明

#### **監控指標**
- 診斷結果準確性對比
- 函數執行時間監控
- 記憶體使用量監控
- 錯誤日誌監控

### **回滾策略**

#### **快速回滾方案**
```bash
# 如果發現嚴重問題，可快速回滾到重構前狀態
git checkout backup-before-unification-$(date +%Y%m%d)
git checkout -b emergency-rollback-$(date +%Y%m%d-%H%M)
```

#### **部分回滾方案**
```bash
# 僅回滾特定檔案或模組
git checkout HEAD~1 -- gmat_diagnosis_app/diagnostics/di_modules/
git checkout HEAD~1 -- gmat_diagnosis_app/diagnostics/q_modules/
git checkout HEAD~1 -- gmat_diagnosis_app/diagnostics/v_modules/
```

#### **數據恢復檢查**
- 確認所有診斷結果與基準版本一致
- 檢查性能指標是否符合預期
- 驗證外部調用介面是否正常

---

## 📚 **實施後文件更新**

### **需要更新的文件**

1. **API文件**: 更新主入口函數的介面說明
2. **開發指南**: 新增統一的開發標準和命名規範
3. **使用手冊**: 更新模組調用方式說明
4. **架構圖**: 更新系統架構和模組關係圖

### **代碼註解完善**

- 為所有公開函數添加詳細的docstring
- 統一註解格式和風格
- 添加類型提示 (Type Hints)
- 完善內聯註解

---

## ✅ **完成檢查清單**

### **階段一完成標準** ✅ 已完成
- [x] 新分支 `gui-rewrite-7` 創建成功
- [x] 代碼備份標籤建立
- [x] 依賴關係分析完成
- [x] 測試環境準備就緒

### **階段二完成標準** ✅ 已完成
- [x] DI模組檔案重新命名完成
- [x] 所有匯入語句更新正確
- [x] 檔案結構驗證通過
- [x] 基本功能測試通過

### **階段三完成標準** ✅ 已完成
- [x] DI模組底線前綴全部移除
- [x] 函數命名符合新標準
- [x] 所有函數調用更新完成
- [x] 命名一致性驗證通過

### **階段四完成標準** ✅ 已完成
- [x] 主入口函數簽名統一
- [x] 參數命名標準化完成
- [x] 返回值格式統一
- [x] 介面一致性測試通過

### **階段五完成標準**
- [ ] 所有單元測試通過
- [ ] 整合測試驗證成功
- [ ] 性能回歸測試通過
- [ ] 診斷結果一致性確認

### **階段六完成標準**
- [ ] API文件更新完成
- [ ] 開發指南更新
- [ ] 代碼註解完善
- [ ] 最終驗證通過

---

## 📞 **聯絡與支援**

如在實施過程中遇到問題，請參考：

1. **技術問題**: 檢查測試結果和錯誤日誌
2. **設計問題**: 重新檢視本文件的標準規範
3. **緊急情況**: 執行回滾策略

**文件維護**: 本計劃文件將隨著實施進度持續更新，確保反映最新的實施狀態和經驗總結。

---

**計劃制定者**: AI Assistant  
**最後更新**: 2025-01-30  
**文件版本**: v1.0 