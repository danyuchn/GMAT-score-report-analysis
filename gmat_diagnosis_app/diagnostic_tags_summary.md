診斷標籤與時間表現對應總表

## 通用診斷標籤

以下標籤的應用基於特定條件，可能與任何時間表現分類同時出現：

* **基礎掌握: 應用不穩定 (Special Focus Error) (`FOUNDATIONAL_MASTERY_APPLICATION_INSTABILITY_SFE`/`Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`/`DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`)**  當題目答錯，且該題的數值難度低於學生在同一考察能力（V科目：技能點。Q科目：技能點。DI科目：題型且領域）上已正確完成題目的最高難度時觸發。此檢查僅對有效數據進行。
  * 觸發條件：題目答錯，且該題難度低於學生在該考察能力上已正確完成的最高難度。
* **數據無效：用時過短（受時間壓力影響） (`DATA_INVALID_SHORT_TIME_PRESSURE_AFFECTED`)**  當題目的 `is_invalid` 標記為 `True` 時觸發。`is_invalid` 的狀態優先由 `is_manually_invalid` 列決定；若無手動標記，則可能由預處理步驟（如基於時間壓力的自動檢測）設定。此標記通常優先於其他診斷標籤。具體的標籤文本可能因科目而異（例如 V 科為 `INVALID_DATA_TAG_V`，Q 科和 DI 科為 `數據無效：用時過短（受時間壓力影響）`）。
  * 觸發條件：題目被預處理或手動標記為無效數據。

## Critical Reasoning (CR) 診斷標籤

### 時間表現: 正常時間且錯 (`Normal Time & Wrong`) OR 快且錯 (`Fast & Wrong`)
 以下 CR 標籤在以下條件下觸發：題目數據有效，題型為 Critical Reasoning，且時間表現類別為 'Fast & Wrong'（答錯且用時較平均快）或 'Normal Time & Wrong'（答錯且用時正常）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加。

* CR 題幹理解錯誤：提問要求把握 (`CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP`)
* CR 題幹理解錯誤：詞彙 (`CR_STEM_UNDERSTANDING_ERROR_VOCAB`)
* CR 題幹理解錯誤：句式 (`CR_STEM_UNDERSTANDING_ERROR_SYNTAX`)
* CR 題幹理解錯誤：邏輯 (`CR_STEM_UNDERSTANDING_ERROR_LOGIC`)
* CR 題幹理解錯誤：領域 (`CR_STEM_UNDERSTANDING_ERROR_DOMAIN`)
* CR 推理錯誤: 邏輯鏈分析 (前提與結論關係) (`CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP`)
* CR 推理錯誤: 抽象邏輯/術語理解 (`CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING`)
* CR 推理錯誤: 預判方向 (`CR_REASONING_ERROR_PREDICTION_DIRECTION`)
* CR 推理錯誤: 核心議題識別 (`CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION`)
* CR 選項理解錯誤: 選項詞彙 (`CR_CHOICE_UNDERSTANDING_ERROR_VOCAB`)
* CR 選項理解錯誤: 選項句式 (`CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX`)
* CR 選項理解錯誤: 選項邏輯 (`CR_CHOICE_UNDERSTANDING_ERROR_LOGIC`)
* CR 推理錯誤: 選項相關性判斷 (`CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT`)
* CR 推理錯誤: 強干擾選項混淆 (`CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION`)
* CR 特定題型弱點: (需註明題型) (`CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE`)  此標籤與上述條件一同觸發。代碼中不會自動註明具體題型，需分析師或報告生成階段結合題目其他信息進行補充。

### 時間表現: 慢且錯 (`Slow & Wrong`)
 以下 CR 標籤在以下條件下觸發：題目數據有效，題型為 Critical Reasoning，且時間表現類別為 'Slow & Wrong'（答錯且用時慢，即超時）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加，其中同時包含「障礙相關標籤」（Difficulty 類）和「錯誤相關標籤」（Error 類）。

* CR 題幹理解障礙：詞彙 (`CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB`)
* CR 題幹理解障礙：句式 (`CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX`)
* CR 題幹理解障礙：邏輯 (`CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC`)
* CR 題幹理解障礙：領域 (`CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN`)
* CR 題幹理解障礙：心態失常讀不進去 (`CR_STEM_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED`)
* CR 推理障礙: 抽象邏輯/術語理解困難 (`CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING`)
* CR 推理障礙: 預判方向 (`CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING`)
* CR 推理障礙: 核心議題識別 (`CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION`)
* CR 推理障礙: 選項相關性判斷 (`CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT`)
* CR 推理障礙: 強干擾選項辨析 (`CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS`)
* CR 選項理解障礙: 選項詞彙理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB`)
* CR 選項理解障礙: 選項句式理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX`)
* CR 選項理解障礙: 選項邏輯理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC`)
* CR 選項理解障礙: 選項領域理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN`)
* CR 題幹理解錯誤：提問要求把握 (`CR_STEM_UNDERSTANDING_ERROR_QUESTION_REQUIREMENT_GRASP`)
* CR 題幹理解錯誤：詞彙 (`CR_STEM_UNDERSTANDING_ERROR_VOCAB`)
* CR 題幹理解錯誤：句式 (`CR_STEM_UNDERSTANDING_ERROR_SYNTAX`)
* CR 題幹理解錯誤：邏輯 (`CR_STEM_UNDERSTANDING_ERROR_LOGIC`)
* CR 題幹理解錯誤：領域 (`CR_STEM_UNDERSTANDING_ERROR_DOMAIN`)
* CR 推理錯誤: 邏輯鏈分析 (前提與結論關係) (`CR_REASONING_ERROR_LOGIC_CHAIN_ANALYSIS_PREMISE_CONCLUSION_RELATIONSHIP`)
* CR 推理錯誤: 抽象邏輯/術語理解 (`CR_REASONING_ERROR_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING`)
* CR 推理錯誤: 預判方向 (`CR_REASONING_ERROR_PREDICTION_DIRECTION`)
* CR 推理錯誤: 核心議題識別 (`CR_REASONING_ERROR_CORE_ISSUE_IDENTIFICATION`)
* CR 選項理解錯誤: 選項詞彙 (`CR_CHOICE_UNDERSTANDING_ERROR_VOCAB`)
* CR 選項理解錯誤: 選項句式 (`CR_CHOICE_UNDERSTANDING_ERROR_SYNTAX`)
* CR 選項理解錯誤: 選項邏輯 (`CR_CHOICE_UNDERSTANDING_ERROR_LOGIC`)
* CR 推理錯誤: 選項相關性判斷 (`CR_REASONING_ERROR_CHOICE_RELEVANCE_JUDGEMENT`)
* CR 推理錯誤: 強干擾選項混淆 (`CR_REASONING_ERROR_STRONG_DISTRACTOR_CHOICE_CONFUSION`)
* CR 特定題型弱點: (需註明題型) (`CR_SPECIFIC_QUESTION_TYPE_WEAKNESS_NOTE_TYPE`)  此標籤與上述條件一同觸發。代碼中不會自動註明具體題型，需分析師或報告生成階段結合題目其他信息進行補充。

### 時間表現: 慢且對 (`Slow & Correct`)
 以下 CR 標籤在以下條件下觸發：題目數據有效，題型為 Critical Reasoning，且時間表現類別為 'Slow & Correct'（答對且用時慢，即超時）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加，均為「根本原因相關標籤」（Difficulty 類）。

* CR 題幹理解障礙：詞彙 (`CR_STEM_UNDERSTANDING_DIFFICULTY_VOCAB`)
* CR 題幹理解障礙：句式 (`CR_STEM_UNDERSTANDING_DIFFICULTY_SYNTAX`)
* CR 題幹理解障礙：邏輯 (`CR_STEM_UNDERSTANDING_DIFFICULTY_LOGIC`)
* CR 題幹理解障礙：領域 (`CR_STEM_UNDERSTANDING_DIFFICULTY_DOMAIN`)
* CR 題幹理解障礙：心態失常讀不進去 (`CR_STEM_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED`)
* CR 推理障礙: 抽象邏輯/術語理解困難 (`CR_REASONING_DIFFICULTY_ABSTRACT_LOGIC_TERMINOLOGY_UNDERSTANDING`)
* CR 推理障礙: 預判方向 (`CR_REASONING_DIFFICULTY_PREDICTION_DIRECTION_MISSING`)
* CR 推理障礙: 核心議題識別 (`CR_REASONING_DIFFICULTY_CORE_ISSUE_IDENTIFICATION`)
* CR 推理障礙: 選項相關性判斷 (`CR_REASONING_DIFFICULTY_CHOICE_RELEVANCE_JUDGEMENT`)
* CR 推理障礙: 強干擾選項辨析 (`CR_REASONING_DIFFICULTY_STRONG_DISTRACTOR_CHOICE_ANALYSIS`)
* CR 選項理解障礙: 選項詞彙理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_VOCAB`)
* CR 選項理解障礙: 選項句式理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_SYNTAX`)
* CR 選項理解障礙: 選項邏輯理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_LOGIC`)
* CR 選項理解障礙: 選項領域理解 (`CR_CHOICE_UNDERSTANDING_DIFFICULTY_DOMAIN`)

## Reading Comprehension (RC) 診斷標籤

### 時間表現: 正常時間且錯 (`Normal Time & Wrong`) OR 快且錯 (`Fast & Wrong`)
 以下 RC 標籤在以下條件下觸發：題目數據有效，題型為 Reading Comprehension，且時間表現類別為 'Fast & Wrong'（答錯且用時相對快）或 'Normal Time & Wrong'（答錯且用時正常，即未標記為超時）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加。**觸發條件僅為單題。**

* RC 閱讀理解錯誤: 詞彙理解 (`RC_READING_COMPREHENSION_ERROR_VOCAB`)
* RC 閱讀理解錯誤: 長難句解析 (`RC_READING_COMPREHENSION_ERROR_LONG_DIFFICULT_SENTENCE_ANALYSIS`)
* RC 閱讀理解錯誤: 篇章結構理解 (`RC_READING_COMPREHENSION_ERROR_PASSAGE_STRUCTURE`)
* RC 閱讀理解錯誤: 關鍵信息定位/理解 (`RC_READING_COMPREHENSION_ERROR_KEY_INFO_LOCATION_UNDERSTANDING`)
* RC 題目理解錯誤: 提問焦點理解 (`RC_QUESTION_UNDERSTANDING_ERROR_FOCUS_POINT`)
* RC 定位能力錯誤: 定到錯誤位置 (`RC_LOCATION_SKILL_ERROR_LOCATION`)
* RC 推理錯誤: 預想推理不符 (`RC_REASONING_ERROR_INFERENCE`)
* RC 選項辨析錯誤: 選項詞彙理解 (`RC_CHOICE_ANALYSIS_ERROR_VOCAB`)
* RC 選項辨析錯誤: 選項句式理解 (`RC_CHOICE_ANALYSIS_ERROR_SYNTAX`)
* RC 選項辨析錯誤: 選項邏輯理解 (`RC_CHOICE_ANALYSIS_ERROR_LOGIC`)
* RC 選項辨析錯誤: 選項領域理解 (`RC_CHOICE_ANALYSIS_ERROR_DOMAIN`)
* RC 選項辨析錯誤: 選項相關性判斷 (`RC_CHOICE_ANALYSIS_ERROR_RELEVANCE_JUDGEMENT`)
* RC 選項辨析錯誤: 強干擾選項混淆 (`RC_CHOICE_ANALYSIS_ERROR_STRONG_DISTRACTOR_CONFUSION`)
* RC 方法錯誤: 特定題型處理 (`RC_METHOD_ERROR_SPECIFIC_QUESTION_TYPE_HANDLING`)

### 時間表現: 慢且錯 (`Slow & Wrong`)
 以下 RC 標籤在以下條件下觸發：題目數據有效，題型為 Reading Comprehension，且時間表現類別為 'Slow & Wrong'（答錯且用時慢，即在預處理階段已被標記為超時）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加，其中同時包含「困難相關標籤」（Difficulty 類）和「錯誤原因標籤」（Error 類）。

* RC 閱讀理解障礙: 詞彙量瓶頸 (`RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 長難句解析困難 (`RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 篇章結構把握不清 (`RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 特定領域背景知識缺乏 (`RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 心態失常讀不進去 (`RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED`)  觸發條件僅為閱讀文章超時
* RC 題目理解障礙: 提問焦點把握困難 (`RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP`)  觸發條件僅為單題超時
* RC 題目理解障礙: 心態失常讀不進去 (`RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED`)  觸發條件僅為單題超時
* RC 定位能力障礙: 找尋不到定位 (`RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY`)  觸發條件僅為單題超時
* RC 推理障礙: 預想推理緩慢 (`RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項詞彙理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項句式理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項邏輯理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項領域理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項相關性判斷困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 強干擾選項辨析困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS`)  觸發條件僅為單題超時

### 時間表現: 慢且對 (`Slow & Correct`)
 以下 RC 標籤在以下條件下觸發：題目數據有效，題型為 Reading Comprehension，且時間表現類別為 'Slow & Correct'（答對且用時慢，即在預處理階段已被標記為超時）。這些標籤通過 `analysis.py` 中的 `param_assignment_map` 統一添加，均為「困難相關標籤」（Difficulty 類）。

* RC 閱讀理解障礙: 詞彙量瓶頸 (`RC_READING_COMPREHENSION_DIFFICULTY_VOCAB_BOTTLENECK`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 長難句解析困難 (`RC_READING_COMPREHENSION_DIFFICULTY_LONG_DIFFICULT_SENTENCE_ANALYSIS`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 篇章結構把握不清 (`RC_READING_COMPREHENSION_DIFFICULTY_PASSAGE_STRUCTURE_GRASP_UNCLEAR`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 特定領域背景知識缺乏 (`RC_READING_COMPREHENSION_DIFFICULTY_SPECIFIC_DOMAIN_BACKGROUND_KNOWLEDGE_LACK`)  觸發條件僅為閱讀文章超時
* RC 閱讀理解障礙: 心態失常讀不進去 (`RC_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED`)  觸發條件僅為閱讀文章超時
* RC 題目理解障礙: 提問焦點把握困難 (`RC_QUESTION_UNDERSTANDING_DIFFICULTY_FOCUS_POINT_GRASP`)  觸發條件僅為單題超時
* RC 題目理解障礙: 心態失常讀不進去 (`RC_QUESTION_UNDERSTANDING_DIFFICULTY_MINDSET_BLOCKED`)  觸發條件僅為單題超時
* RC 定位能力障礙: 找尋不到定位 (`RC_LOCATION_SKILL_DIFFICULTY_INEFFICIENCY`)  觸發條件僅為單題超時
* RC 推理障礙: 預想推理緩慢 (`RC_REASONING_DIFFICULTY_INFERENCE_SPEED_SLOW`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項詞彙理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_VOCAB`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項句式理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_SYNTAX`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項邏輯理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_LOGIC`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項領域理解困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_DOMAIN`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 選項相關性判斷困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_RELEVANCE_JUDGEMENT`)  觸發條件僅為單題超時
* RC 選項辨析障礙: 強干擾選項辨析困難 (`RC_CHOICE_ANALYSIS_DIFFICULTY_STRONG_DISTRACTOR_ANALYSIS`)  觸發條件僅為單題超時
* RC 方法障礙: 特定題型處理困難 (`RC_METHOD_DIFFICULTY_SPECIFIC_QUESTION_TYPE_HANDLING`) 觸發條件僅為單題超時

## Data Insights (DI) 診斷標籤
 DI 標籤的分配主要在 gmat_diagnosis_app/diagnostics/di_modules/chapter_logic.py 的 _diagnose_root_causes 和 _observe_di_patterns 函數中實現。觸發條件基於題型、內容領域、時間表現和正確性。以下規則適用於被標記為有效的數據 (`is_invalid` 為 False)。

 * **數據無效：用時過短（受時間壓力影響） (`INVALID_DATA_TAG_DI`)** 當題目的 `is_invalid` 標記為 `True` 時觸發。代碼中添加的標籤文本是 `數據無效：用時過短（受時間壓力影響）`。此標籤優先於其他診斷標籤。

### 時間表現: 快且錯 (`Fast & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Fast & Wrong' (答錯且用時相對快 < 0.75*平均)。
* DI 閱讀理解錯誤: 詞彙理解 (`DI_READING_COMPREHENSION_ERROR__VOCABULARY`)  根據(題型,領域)添加所有相關錯誤類標籤
* DI 閱讀理解錯誤: 句式理解 (`DI_READING_COMPREHENSION_ERROR__SYNTAX`)  同上
* DI 閱讀理解錯誤: 邏輯理解 (`DI_READING_COMPREHENSION_ERROR__LOGIC`)  同上
* DI 閱讀理解錯誤: 領域理解 (`DI_READING_COMPREHENSION_ERROR__DOMAIN`)  同上
* DI 圖表解讀錯誤: 圖形信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__GRAPH`)  若題型為 G&T/MSR，同上
* DI 圖表解讀錯誤: 表格信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__TABLE`)  若題型為 G&T/MSR，同上
* DI 概念應用 (數學) 錯誤: 數學觀念/公式應用 (`DI_CONCEPT_APPLICATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷 (`DI_LOGICAL_REASONING_ERROR__NON_MATH`)  若領域為 Non-Math Related，同上
* DI 計算錯誤 (數學): 數學計算 (`DI_CALCULATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 基礎掌握: 應用不穩定 (Special Focus Error) (`DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`)  觸發條件：答錯且難度低於已掌握。
* DI 行為: 粗心 - 細節忽略/看錯 (`DI_BEHAVIOR_CARELESSNESS_DETAIL_OMISSION`)  在 'Fast & Wrong' 條件下觸發，標記具體題目。
* DI 行為: 粗心 - 整體快錯率偏高 (`DI_BEHAVIOR_CARELESSNESS_ISSUE`)  全局標籤，當整體快錯率 > 25% 時觸發 (_observe_di_patterns)。
* DI 行為: 測驗前期作答過快風險 (`DI_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`)  全局標籤，當存在前1/3題目用時 < 1分鐘時觸發 (_observe_di_patterns)，並標記具體題目。

### 時間表現: 正常時間且錯 (`Normal Time & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Normal Time & Wrong' (答錯且用時正常)。
* DI 閱讀理解錯誤: 詞彙理解 (`DI_READING_COMPREHENSION_ERROR__VOCABULARY`)  根據(題型,領域)添加所有相關錯誤類標籤
* DI 閱讀理解錯誤: 句式理解 (`DI_READING_COMPREHENSION_ERROR__SYNTAX`)  同上
* DI 閱讀理解錯誤: 邏輯理解 (`DI_READING_COMPREHENSION_ERROR__LOGIC`)  同上
* DI 閱讀理解錯誤: 領域理解 (`DI_READING_COMPREHENSION_ERROR__DOMAIN`)  同上
* DI 圖表解讀錯誤: 圖形信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__GRAPH`)  若題型為 G&T/MSR，同上
* DI 圖表解讀錯誤: 表格信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__TABLE`)  若題型為 G&T/MSR，同上
* DI 概念應用 (數學) 錯誤: 數學觀念/公式應用 (`DI_CONCEPT_APPLICATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷 (`DI_LOGICAL_REASONING_ERROR__NON_MATH`)  若領域為 Non-Math Related，同上
* DI 計算錯誤 (數學): 數學計算 (`DI_CALCULATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 多源整合 (MSR): 跨分頁/來源信息整合障礙 (`DI_MULTI_SOURCE_INTEGRATION_ERROR`)  若題型為 MSR，同上
* DI 基礎掌握: 應用不穩定 (Special Focus Error) (`DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`)  觸發條件：答錯且難度低於已掌握。

### 時間表現: 慢且錯 (`Slow & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Slow & Wrong' (答錯且用時慢)。同時添加錯誤類和困難類標籤。
* DI 閱讀理解錯誤: 詞彙理解 (`DI_READING_COMPREHENSION_ERROR__VOCABULARY`)  根據(題型,領域)添加所有相關錯誤類標籤
* DI 閱讀理解錯誤: 句式理解 (`DI_READING_COMPREHENSION_ERROR__SYNTAX`)  同上
* DI 閱讀理解錯誤: 邏輯理解 (`DI_READING_COMPREHENSION_ERROR__LOGIC`)  同上
* DI 閱讀理解錯誤: 領域理解 (`DI_READING_COMPREHENSION_ERROR__DOMAIN`)  同上
* DI 圖表解讀錯誤: 圖形信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__GRAPH`)  若題型為 G&T/MSR，同上
* DI 圖表解讀錯誤: 表格信息解讀 (`DI_GRAPH_INTERPRETATION_ERROR__TABLE`)  若題型為 G&T/MSR，同上
* DI 概念應用 (數學) 錯誤: 數學觀念/公式應用 (`DI_CONCEPT_APPLICATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷 (`DI_LOGICAL_REASONING_ERROR__NON_MATH`)  若領域為 Non-Math Related，同上
* DI 計算錯誤 (數學): 數學計算 (`DI_CALCULATION_ERROR__MATH`)  若領域為 Math Related，同上
* DI 閱讀理解障礙: 跨分頁/來源信息整合困難 (`DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`)  若題型為 MSR 且 **MSR 閱讀文章本身超時**，則添加此標籤 (此標籤專屬於 MSR 題型)。
* DI 閱讀理解障礙: 詞彙理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY`)  根據(題型,領域)添加所有相關困難類標籤
* DI 閱讀理解障礙: 句式理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX`)  同上
* DI 閱讀理解障礙: 邏輯理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__LOGIC`)  同上
* DI 閱讀理解障礙: 領域理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN`)  根據(題型,領域)添加所有相關困難類標籤。**此標籤在 MSR 題型中，僅當 MSR 閱讀文章本身超時方觸發；在其他題型中，則基於單題超時觸發。**
* DI 閱讀理解障礙: 心態失常讀不進去 (`DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED`)  根據(題型,領域)添加所有相關困難類標籤
* DI 圖表解讀障礙: 圖形信息解讀困難 (`DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH`)  若題型為 G&T/MSR，同上
* DI 圖表解讀障礙: 表格信息解讀困難 (`DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE`)  若題型為 G&T/MSR，同上
* DI 概念應用 (數學) 障礙: 數學觀念/公式應用困難 (`DI_CONCEPT_APPLICATION_DIFFICULTY__MATH`)  若領域為 Math Related，同上
* DI 邏輯推理 (非數學) 障礙: 題目內在邏輯推理/判斷困難 (`DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH`)  若領域為 Non-Math Related，同上
* DI 計算 (數學) 障礙: 數學計算困難 (`DI_CALCULATION_DIFFICULTY__MATH`)  若領域為 Math Related，同上
* DI 基礎掌握: 應用不穩定 (Special Focus Error) (`DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`)  觸發條件：答錯且難度低於已掌握。

### 時間表現: 慢且對 (`Slow & Correct`)
 觸發條件：數據有效，時間表現類別為 'Slow & Correct' (答對且用時慢)。僅添加困難類標籤。
* DI 閱讀理解障礙: 跨分頁/來源信息整合困難 (`DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`)  若題型為 MSR 且 **MSR 閱讀文章本身超時**，則添加此標籤 (此標籤專屬於 MSR 題型)。
* DI 閱讀理解障礙: 詞彙理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY`)  根據(題型,領域)添加所有相關困難類標籤
* DI 閱讀理解障礙: 句式理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX`)  同上
* DI 閱讀理解障礙: 邏輯理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__LOGIC`)  同上
* DI 閱讀理解障礙: 領域理解困難 (`DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN`)  根據(題型,領域)添加所有相關困難類標籤。**此標籤在 MSR 題型中，僅當 MSR 閱讀文章本身超時方觸發；在其他題型中，則基於單題超時觸發。**
* DI 閱讀理解障礙: 心態失常讀不進去 (`DI_READING_COMPREHENSION_DIFFICULTY__MINDSET_BLOCKED`)  根據(題型,領域)添加所有相關困難類標籤
* DI 圖表解讀障礙: 圖形信息解讀困難 (`DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH`)  若題型為 G&T/MSR，同上
* DI 圖表解讀障礙: 表格信息解讀困難 (`DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE`)  若題型為 G&T/MSR，同上
* DI 概念應用 (數學) 障礙: 數學觀念/公式應用困難 (`DI_CONCEPT_APPLICATION_DIFFICULTY__MATH`)  若領域為 Math Related，同上
* DI 邏輯推理 (非數學) 障礙: 題目內在邏輯推理/判斷困難 (`DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH`)  若領域為 Non-Math Related，同上
* DI 計算 (數學) 障礙: 數學計算困難 (`DI_CALCULATION_DIFFICULTY__MATH`)  若領域為 Math Related，同上

## Quant (Q) 診斷標籤
 Q科標籤主要基於 gmat_diagnosis_app/diagnostics/q_modules/constants.py 中的 PARAM_ASSIGNMENT_RULES 字典，結合時間表現類別（基於用時和正確性）和題目類型（Real/Pure）進行分配。此外，特定的行為模式和數據有效性也會影響標籤。以下規則適用於被標記為有效的數據 (`is_invalid` 為 False)。

 * **數據無效：用時過短（受時間壓力影響） (`INVALID_DATA_TAG_Q`)** 當題目的 `is_invalid` 標記為 `True` 時觸發。代碼中添加的標籤文本是 `數據無效：用時過短（受時間壓力影響）`。此標籤優先於其他診斷標籤。

### 時間表現: 快且錯 (`Fast & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Fast & Wrong' (答錯且用時相對快)。
 * Q 閱讀理解錯誤：題目文字理解 (`Q_READING_COMPREHENSION_ERROR`) (僅 REAL 題型)
 * Q 概念應用錯誤：數學觀念/公式應用 (`Q_CONCEPT_APPLICATION_ERROR`)
 * Q 計算錯誤：數學計算 (`Q_CALCULATION_ERROR`)
 * Q 基礎掌握：應用不穩定（Special Focus Error） (`Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`)  觸發條件同 DI/V 科：答錯且難度低於已掌握。

### 時間表現: 正常時間且錯 (`Normal Time & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Normal Time & Wrong' (答錯且用時正常)。
 * Q 閱讀理解錯誤：題目文字理解 (`Q_READING_COMPREHENSION_ERROR`) (僅 REAL 題型)
 * Q 概念應用錯誤：數學觀念/公式應用 (`Q_CONCEPT_APPLICATION_ERROR`)
 * Q 計算錯誤：數學計算 (`Q_CALCULATION_ERROR`)
 * Q 基礎掌握：應用不穩定（Special Focus Error） (`Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`)  觸發條件同 DI/V 科：答錯且難度低於已掌握。

### 時間表現: 慢且錯 (`Slow & Wrong`)
 觸發條件：數據有效，時間表現類別為 'Slow & Wrong' (答錯且用時慢)。同時包含錯誤類和困難類標籤。
 * Q 閱讀理解錯誤：題目文字理解 (`Q_READING_COMPREHENSION_ERROR`) (僅 REAL 題型)
 * Q 概念應用錯誤：數學觀念/公式應用 (`Q_CONCEPT_APPLICATION_ERROR`)
 * Q 計算錯誤：數學計算 (`Q_CALCULATION_ERROR`)
 * Q 閱讀理解障礙：題目文字理解困難 (`Q_READING_COMPREHENSION_DIFFICULTY`) (僅 REAL 題型)
 * Q 閱讀理解障礙：心態失常讀不進去 (`Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED`) (僅 REAL 題型)
 * Q 概念應用障礙：數學觀念/公式應用困難 (`Q_CONCEPT_APPLICATION_DIFFICULTY`)
 * Q 計算障礙：數學計算困難 (`Q_CALCULATION_DIFFICULTY`)
 * Q 基礎掌握：應用不穩定（Special Focus Error） (`Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`)  具體觸發同 DI/V 科：答錯且難度低於已掌握。

### 時間表現: 慢且對 (`Slow & Correct`)
 觸發條件：數據有效，時間表現類別為 'Slow & Correct' (答對且用時慢)。僅包含困難類標籤。
 * Q 閱讀理解障礙：題目文字理解困難 (`Q_READING_COMPREHENSION_DIFFICULTY`) (僅 REAL 題型)
 * Q 閱讀理解障礙：心態失常讀不進去 (`Q_READING_COMPREHENSION_DIFFICULTY_MINDSET_BLOCKED`) (僅 REAL 題型)
 * Q 概念應用障礙：數學觀念/公式應用困難 (`Q_CONCEPT_APPLICATION_DIFFICULTY`)
 * Q 計算障礙：數學計算困難 (`Q_CALCULATION_DIFFICULTY`)

### 行為模式標籤（獨立評估）
 以下行為標籤由 `gmat_diagnosis_app/diagnostics/q_modules/behavioral.py` 中的邏輯獨立評估，可能作為全局性標誌或影響特定題目集的標記，而不是直接添加到上述時間表現分類的參數列表中：
 * **行為模式：前期作答過快（Flag risk） (`BEHAVIOR_EARLY_RUSHING_FLAG_RISK`)**  觸發條件：存在位於測驗前三分之一且用時少於 1 分鐘的題目。
 * **行為模式：整體粗心問題（快而錯比例高） (`BEHAVIOR_CARELESSNESS_ISSUE`)**  觸發條件：快且錯 (`Fast & Wrong`) 的題目數量佔所有快 (`Fast & Wrong` + `Fast & Correct`) 題目數量的比例超過 25%。

---

*注意：此列表基於程式碼中的主要分配邏輯。實際報告中，標籤的呈現可能還會受到其他細微條件或報告生成邏輯的影響。*
