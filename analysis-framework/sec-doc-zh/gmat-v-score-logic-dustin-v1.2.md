# **第零章：核心輸入數據與設定**

- **每題數據:**
    - `question_position` (題目順序，必需，作為唯一識別符)
    - `question_time` (作答時間/分鐘)
    - `is_correct` (是否正確/布林值)
    - `question_type` ( `Critical Reasoning` 映射轉換至 `CR` ；`Reading Comprehension` 映射轉換至 `RC`)
    - `question_difficulty` (難度值 `V_b` )
    - `question_fundamental_skill` (核心技能 - 例如: `Plan/Construct`, `Identify Stated Idea`, `Identify Inferred Idea`, `Analysis/Critique`)
- **整體數據:**
    - `total_test_time` (總作答時間/分鐘)
    - `max_allowed_time` (測驗上限時間，固定為 45 分鐘)
    - `total_number_of_questions` (總題數)
- **衍生數據 (需計算或預處理):**
    - `rc_group_id` (RC 題組 ID)
    - `questions_in_group` (題組內題目列表)
    - `group_total_time` (RC 題組總作答時間)
    - `average_time_per_type` (整個考試各類型題目的平均時間)
    - `first_third_average_time_per_type` (考試前 1/3 各類型題目的平均時間)
    - `rc_reading_time` (RC 題組估算的閱讀時間)
    - `rc_group_target_time` (RC 題組的目標分析時間)
- **附錄：RC 題組定義說明**
    - 所有 RC 分析均以 題組 (`Passage Group`) 為單位。
    - 題組指連續的 RC 題目集合，通常為 3 題或 4 題。
    - 若 RC 題目間被其他類型題目 隔開，則視為不同題組。
    - 注意： 若系統檢測到連續 RC 題目超過 4 題，需人工介入檢查題組劃分是否正確。

<aside>

**本章總結：**

本章定義了後續所有分析所需的核心輸入數據結構，包括每道題目的詳細信息（`ID`、`時間`、`正誤`、`類型`、`難度`、`技能`、`順序`）、整體測驗數據（`總時間`、`總題數`）以及需要預先計算的衍生數據（如 `RC 題組信息`、`平均時間`等）。

**結果去向：**

本章定義的數據是後續所有章節進行計算、分析和判斷的基礎。數據的完整性和準確性直接影響診斷結果的有效性。

</aside>

---

# 第一章：整體時間策略與數據有效性評估

<aside>

**本章目標:** 評估學生在 Verbal 部分的整體時間策略、壓力感知、作答節奏及數據有效性。

**主要關注:** 總時間使用、結尾策略、疲勞效應、分題型時間分配（`CR` vs. `RC`）、以及因壓力或疲勞導致的無效數據 (`is_invalid`)。

**為何重要:** Verbal 部分時間緊、易疲勞，合理的策略和準確的時間分析是找出問題和提升效率的基礎。識別無效數據可避免錯誤診斷。

</aside>

- **計算總時間差 (`time_diff`)**: 
    `time_diff` = `max_allowed_time` - `total_test_time`

- **判斷時間壓力狀態 (`time_pressure`)**: 
    - 若 `time_diff` < 1.0 分鐘，則 `time_pressure` = `True`。
    - 否則 `time_pressure` = `False`。
    - *（用戶覆蓋規則可在此處應用，若需要）*

- **設定超時閾值與規則 (基於 `time_pressure`)**: 
    - **CR 超時閾值 (`overtime_threshold_cr`)**: 
        - 若 `time_pressure` == `True`: `overtime_threshold_cr` = 2.0 分鐘。
        - 若 `time_pressure` == `False`: `overtime_threshold_cr` = 2.5 分鐘。
    - **RC 題組目標時間規則 (`rc_group_target_time`)**: 
        - 若 `time_pressure` == `True`: 3 題題組目標 6 分鐘；4 題題組目標 8 分鐘。
        - 若 `time_pressure` == `False`: 3 題題組目標 7 分鐘；4 題題組目標 9 分鐘。
    - **RC 單題分析時間閾值 (`rc_individual_q_threshold`)**: 2.0 分鐘 (用於判斷排除閱讀時間後的單題解答是否過長)。
    - *說明：以上閾值和規則用於後續判斷題目或題組是否超時 (`overtime`, `group_overtime`, `individual_overtime`)。*

- **RC 閱讀時間初步評估 (`rc_reading_time`)**: (V 科目特定分析點)
    - 針對每個 RC 題組，估算閱讀時間：`rc_reading_time` = 題組第一題作答時間 - 題組內其他題平均作答時間。
    - 檢查閱讀時間是否偏長：
        - 獲取題組題目數 `num_q_in_group`。
        - 若 (`num_q_in_group` == 3 且 `rc_reading_time` > 2.0 分鐘) 或 (`num_q_in_group` == 4 且 `rc_reading_time` > 2.5 分鐘)，則觸發 `reading_comprehension_barrier_inquiry` = `True`。
    - *說明：此標記提示可能存在基礎閱讀障礙，將在後續章節建議中引用。*

- **識別無效數據 (`is_invalid`)**: 
    - 檢查測驗最後 1/3 的題目 (`last_third_questions`)。
    - 識別末尾作答異常題目：
        - 「明顯倉促 (`hasty`)」：`question_time` < 1.0 分鐘 或 (`CR` 且 `question_time` < `first_third_average_time_per_type`['CR'] * 0.5) 或 (`RC` 題組且 `group_total_time` < (`first_third_average_time_per_type`['RC'] * `num_q_in_group`) * 0.5)。
        - 「疑似放棄 (`abandoned`)」：`question_time` < 0.5 分鐘。
    - 標記邏輯：如果一個題目滿足「明顯倉促」或「疑似放棄」的標準，**且** `time_pressure` == `True` (根據第 2 步判斷得出)，則將該題目標記為 `is_invalid` = `True`。
    - 輸出診斷提示：若存在被標記為 `is_invalid` 的題目，提示「可能結尾趕時間，需評估策略合理性」。

- **其他觀察與建議**: 
    - 疲勞效應提醒：Verbal 疲勞效應明顯。
    - 考試策略建議：考慮將 Verbal 放在考試最前面，或考前進行閱讀暖身。

- **輸出與總結**: 
    - 本章產生的關鍵標記：`time_pressure` (布林值), `overtime_threshold_cr` (數值), `rc_group_target_time` (規則), `is_invalid` 標記 (針對特定題目), `reading_comprehension_barrier_inquiry` 標記 (若觸發)。

**全局規則應用：數據過濾與標記**

- **應用無效標記:** 在進行後續多數分析 (如錯誤率、難度表現) 時，應排除被標記為 `is_invalid` = `True` 的題目。
- **標記超時狀態 (`overtime`) - RC 詳細說明**
    - 對 `CR` 題: 若 `question_time` > `overtime_threshold_cr`，則標記 `overtime` = `True`。
    - 對 `RC` 題組 (`group_overtime`):
        - 若 `group_total_time` > (`rc_group_target_time` + 1.0) 分鐘 (這裡的 `rc_group_target_time` 根據第一章定義的時間壓力狀態和題數決定)，則該題組內所有題目標記 `group_overtime` = `True`。
        - 解釋：這表示整個閱讀和解題過程超出了目標時間較多，影響了題組內所有題目。
    - 對單題 `RC` (`individual_overtime`):
        - 計算 `adjusted_rc_time`:
            - 若該題是題組第一題: `adjusted_rc_time` = `question_time` - `rc_reading_time`
            - 若該題不是題組第一題: `adjusted_rc_time` = `question_time`
        - 若 `adjusted_rc_time` > 2.0 分鐘 (即超過 `rc_individual_q_threshold`)，則該題標記 `individual_overtime` = `True`。
        - 解釋：這表示單獨看這道題的分析解答時間（排除第一道題的閱讀時間後）過長，即使整個題組可能並未超時。
    - `RC` 題的最終超時判斷 (用於第三章 "`Slow`" 分類): 一個 `RC` 題目被視為「慢」，如果它滿足 `group_overtime` == `True` 或者 `individual_overtime` == `True`。
- **標記過快可疑 (`suspiciously_fast`):**
    - 對任何題目: 若 `question_time` < `average_time_per_type`[該題 `type`] * 0.5，則標記 `suspiciously_fast` = `True`。
    - 輸出診斷標籤 (給使用者)：對標記 `suspiciously_fast` = `True` 的題目，提示「過快可疑做題」。

<aside>

**本章總結：** 我們首先計算了總時間差，判斷了整體時間壓力 (`time_pressure`)。基於此，我們設定了 `CR` 的單題超時閾值 (`overtime_threshold_cr`) 和 `RC` 的題組目標時間規則 (`rc_group_target_time`)。接著，我們進行了 V 科目特定的 `RC` 閱讀時間初步評估，並標記了可能的閱讀障礙 (`reading_comprehension_barrier_inquiry`)。然後，我們結合測驗末尾的作答行為和時間壓力狀態，識別了無效數據 (`is_invalid`)。最後，給出了一些關於疲勞和考試策略的通用建議。

**結果去向：** `time_pressure` 狀態、各超時閾值和規則將作為後續分析的重要背景信息。被標記為 `is_invalid` 的題目將在後續分析中被過濾。`reading_comprehension_barrier_inquiry` 標記將用於指導後續的練習建議和總結報告。

</aside>

---

# 第二章：多維度表現分析

<aside>

**本章目標:** 評估學生在不同難度、不同題型上的準確性表現 (排除 `is_invalid` 數據)。

**主要關注:** 錯誤集中在哪個難度區間？哪些核心技能/題型是弱點？

**為何重要:** 精準定位能力短板。

</aside>

- **難度分級與定義 (`question_difficulty`, 記作 `D`):**
    - 若 `D` ≤ -1: 難度等級 = "低難度 (Low) / 505+"
    - 若 -1 < `D` ≤ 0: 難度等級 = "中難度 (Mid) / 555+"
    - 若 0 < `D` ≤ 1: 難度等級 = "中難度 (Mid) / 605+"
    - 若 1 < `D` ≤ 1.5: 難度等級 = "中難度 (Mid) / 655+"
    - 若 1.5 < `D` ≤ 1.95: 難度等級 = "高難度 (High) / 705+"
    - 若 1.95 < `D` ≤ 2: 難度等級 = "高難度 (High) / 805+"
- **難度區間表現分析:**
    - 統計各難度區間 (低/中/高) 的 `CR` 和 `RC` 題目總數及錯誤數。
    - 計算各區間的錯誤率。
    - 分析錯誤主要集中在哪個難度區間。
- **核心技能/題型錯誤分析:**
    - 按 `question_fundamental_skill` (以及更細的題型，若可得) 統計錯誤率。
    - 找出錯誤率最高的技能/題型。

<aside>

**本章總結：**我們使用過濾後的有效數據，分析了學生在不同難度級別（低、中、高）和不同核心技能（`question_fundamental_skill`）上的準確性表現。通過計算錯誤率，找出了錯誤相對集中的難度區間和技能領域。

**結果去向：**本章的分析結果（錯誤集中的難度和技能）為第三章的診斷提供了背景信息（例如，判斷正常時間做錯的題目是否低於已掌握難度），並直接指導第七章練習建議中需要重點關注的技能領域和難度水平。錯誤率結果也用於第六章的技能覆蓋規則判斷。

</aside>

---

# 第三章：根本原因診斷與分析

<aside>

**本章目標:** 結合時間、準確性、難度、題型等信息，深入探究並診斷導致錯誤或低效表現的根本原因。

**主要關注:** 運用系統性分析方法，結合學生回憶、二級證據及質化分析，識別`CR`和`RC`的具體障礙點，並生成標準化**英文診斷標籤參數**。

**為何重要:** 只有找到問題的根源，才能制定最有效的改進策略。

</aside>

- **分析框架**
    - **前置計算:**
        - `average_time_per_type` (各 `question_type` 的平均時間)
        - `max_correct_difficulty_per_skill`[`skill`] (每個 `question_fundamental_skill` 下 `is_correct` == `True` 的題目中的最高 `question_difficulty`)
    - **核心概念定義:**
        - **時間表現分類 (`Time Performance`):**
            - 快 (`is_relatively_fast`): `question_time` < `average_time_per_type`[該題 `question_type`] * 0.75。
            - 慢 (`is_slow`): 
                - `CR`題: `question_time` > `overtime_threshold_cr` (第一章定義)。
                - `RC`題: 該題被標記為 `group_overtime` == `True` 或 `individual_overtime` == `True` (第一章全局規則定義)。
            - 正常時間 (`is_normal_time`): 非快也非慢。
        - **特殊關注錯誤 (`special_focus_error`)**: 
            - *定義*: 錯誤題目 (`is_correct` == `False`) 的 `question_difficulty` 低於其對應 `question_fundamental_skill` 的 `max_correct_difficulty_per_skill`[`skill`]。
            - *標記*: 若滿足條件，則標記 `special_focus_error` = `True`。
            - *優先處理方式*: 在第七章生成練習建議和第八章輸出診斷總結時，應將標記為 `special_focus_error` = `True` 的題目及其對應的診斷參數 (`FOUNDATIONAL_MASTERY_INSTABILITY_SFE`) 和建議**優先列出或特別標註**。
- **診斷流程與分析要點 (針對有效數據題目)**
    - 根據題目的時間表現 (`is_relatively_fast`, `is_slow`, `is_normal_time`) 和正確性 (`is_correct`) 進行分類診斷：
    - **1. 快而錯 (`Fast & Wrong`)**
        - 分類依據: `is_correct` == `False` 且 `is_relatively_fast` == `True`。
        - 可能原因 (診斷參數) (`CR`):
            - `` `CR_METHOD_PROCESS_DEVIATION` ``
            - `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (需註明題型)
            - `` `CR_READING_BASIC_OMISSION` ``
            - `` `BEHAVIOR_GUESSING_HASTY` `` (若時間極短)
        - 可能原因 (診斷參數) (`RC`):
            - `` `RC_READING_INFO_LOCATION_ERROR` ``
            - `` `RC_READING_KEYWORD_LOGIC_OMISSION` ``
            - `` `RC_METHOD_TYPE_SPECIFIC_ERROR` `` (需註明題型)
            - `` `BEHAVIOR_GUESSING_HASTY` `` (若時間極短)
        - 主要診斷行動:
            - 首先詢問學生能否回憶該題的思考過程或遇到的問題點。
            - 若學生無法清晰回憶具體的思考步驟或遇到的困難點，則啟用二級證據分析：查找學生近期（考前兩週至一個月）在該核心技能 (`question_fundamental_skill`) 下的快錯題目記錄，若樣本足夠（建議 >= 10題），分析其中錯誤率最高的具體子題型 (例如，是 `CR Weaken`, `RC Inference` 等，具體分類參考第四章)。
    - **2. 快而對 (`Fast & Correct`)**
        - 分類依據: `is_correct` == `True` 且 `suspiciously_fast` == `True`。
        - 觀察與提醒 (`CR` & `RC`):
            - 通常表示效率高，但也可能存在 `` `BEHAVIOR_CARELESSNESS_ISSUE` `` 的風險 (需結合第五章分析)。
            - 可提醒學生即使快速做對，也要確保準確性，尤其在選項迷惑性強的題目中。
        - 主要診斷行動:
            - 通常無需特別行動。若第五章顯示整體粗心率高，可提醒注意。
    - **3. 正常時間做錯 (`Normal Time & Wrong`)** 
        - 分類依據: `is_correct` == `False` 且 `is_normal_time` == `True`。
        - 可能原因 (診斷參數) (`CR`):
            - `` `CR_READING_DIFFICULTY_STEM` ``
            - `` `CR_QUESTION_UNDERSTANDING_MISINTERPRETATION` ``
            - `` `CR_REASONING_CHAIN_ERROR` ``
            - `` `CR_REASONING_ABSTRACTION_DIFFICULTY` ``
            - `` `CR_REASONING_PREDICTION_ERROR` ``
            - `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` ``
            - `` `CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY` ``
            - `` `CR_AC_ANALYSIS_RELEVANCE_ERROR` ``
            - `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` ``
            - `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (需註明題型)
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 SFE 觸發，需註明涉及的技能)
        - 可能原因 (診斷參數) (`RC`):
            - `` `RC_READING_VOCAB_BOTTLENECK` ``
            - `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``
            - `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` ``
            - `` `RC_READING_DOMAIN_KNOWLEDGE_GAP` ``
            - `` `RC_READING_PRECISION_INSUFFICIENT` ``
            - `` `RC_QUESTION_UNDERSTANDING_MISINTERPRETATION` ``
            - `` `RC_LOCATION_ERROR_INEFFICIENCY` `` 
            - `` `RC_REASONING_INFERENCE_WEAKNESS` ``
            - `` `RC_AC_ANALYSIS_DIFFICULTY` ``
            - `` `RC_METHOD_TYPE_SPECIFIC_ERROR` `` (需註明題型)
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 SFE 觸發，需註明涉及的技能)
        - 主要診斷行動:
            - 檢查 `special_focus_error` 標記，若觸發，優先考慮 `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 參數。
            - 請學生回憶具體障礙點或錯誤原因。
            - 若回憶不清或原因不明確，啟用二級證據分析：查找近期在該 `question_fundamental_skill` 下的正常時間做錯題目記錄，若樣本足夠（建議 >= 10題），分析錯誤率最高的子題型 (例如，是 `CR Assumption`, `RC Main Idea` 等，具體分類參考第四章)。
            - 觸發質化分析： 當學生表示無法確認診斷參數對應的「障礙」或「錯誤」，且教師/顧問無法通過現有信息排除至只剩一種最可能的原因時，提示學生可提供詳細解題步驟、口述錄音等質化信息，供進一步分析。
    - **4. 正常時間做對 (`Normal Time & Correct`)**
        - 分類依據: `is_correct` == `True` 且 `is_normal_time` == `True`。
        - 觀察: 通常表示學生在該難度和題型上表現符合預期。
        - 主要診斷行動: 無需特別行動。
    - **5. 慢而錯 (`Slow & Wrong`)**
        - 分類依據: `is_correct` == `False` 且 `is_slow` == `True`。
        - 可能原因 (診斷參數) (`CR`):
            - `` `CR_READING_TIME_EXCESSIVE` ``
            - `` `CR_REASONING_TIME_EXCESSIVE` ``
            - `` `CR_AC_ANALYSIS_TIME_EXCESSIVE` ``
            - *（同時可能包含「正常時間做錯」中列出的根本原因參數，如 `` `CR_REASONING_CHAIN_ERROR` `` 等，需結合具體情況判斷）*
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 SFE 觸發，需註明涉及的技能)
        - 可能原因 (診斷參數) (`RC`):
            - `` `RC_READING_SPEED_SLOW_FOUNDATIONAL` ``
            - `` `RC_METHOD_INEFFICIENT_READING` ``
            - `` `RC_LOCATION_TIME_EXCESSIVE` ``
            - `` `RC_REASONING_TIME_EXCESSIVE` ``
            - `` `RC_AC_ANALYSIS_TIME_EXCESSIVE` ``
            - *（同時可能包含「正常時間做錯」中列出的根本原因參數，如 `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` `` 等，需結合具體情況判斷）*
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 SFE 觸發，需註明涉及的技能)
        - 主要診斷行動:
            - 檢查 `special_focus_error` 標記，若觸發，優先考慮 `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 參數。
            - 請學生回憶具體障礙點：是哪個環節耗時最長？
            - 若學生無法回憶清楚具體題型或障礙，啟用二級證據分析：查找近期在該 `question_fundamental_skill` 下的慢錯題目記錄，若樣本足夠（建議 >= 10題），分析錯誤率最高的子題型 (例如，是 `CR Strengthen`, `RC Detail` 等，具體分類參考第四章)。
            - 觸發質化分析： 同「正常時間做錯」的觸發條件。
    - **6. 慢而對 (`Slow & Correct`)**
        - 分類依據: `is_correct` == `True` 且 `is_slow` == `True`。
        - 可能原因 (診斷參數) (`CR` & `RC`):
            - `` `EFFICIENCY_BOTTLENECK_[AREA]` `` (需指明具體環節 AREA: READING, REASONING, LOCATION, AC_ANALYSIS)
            - *（如果題目本身難度 (`question_difficulty`) 確實很高，則慢可能是合理的）*
        - 主要診斷行動:
            - 請學生回憶效率瓶頸點：雖然做對了，但在哪個環節花費了顯著多於預期的時間？
            - 觸發質化分析： 若學生無法清晰說明效率瓶頸，可考慮啟用質化分析以探究提速空間。
- **輔助診斷工具與說明**
    - **二級證據 (`Secondary Evidence`) 應用:**
        - 定義: 指學生考前兩週至一個月內的相關練習記錄或模考數據。
        - 作用: 在學生無法準確回憶或需要客觀數據佐證時，用於分析特定表現類型（快錯、正常錯、慢錯）下，某一核心技能 (`question_fundamental_skill`) 內的具體弱點子題型（例如，分析 `CR` 題型中是 `Weaken` 還是 `Assumption` 出錯更多，`RC` 中是 `Inference` 還是 `Detail` 題錯誤更頻繁，具體分類參考第四章）。
        - 執行: 篩選符合條件（時間表現、正確性、核心技能）的題目，若總數 >= 10 題，則計算其中各具體子題型的錯誤率，找出錯誤率最高的子題型作為參考。若母數 < 10 題，需註明其統計參考價值有限。
    - **質化分析 (`Qualitative Analysis`) 觸發與執行:**
        - 觸發條件: 當學生表示無法確認診斷參數對應的「障礙」或「錯誤」，且教師/顧問根據已有數據和學生回憶無法將問題範圍縮小至一兩種最可能的根本原因時。
        - 執行: 提示學生可以提供更詳細的解題信息，例如：逐步寫下或口述解題思考過程、錄製解題錄音/錄屏等，供教師/顧問進行更深入的個案分析。

<aside>

**本章總結：** 本章結合了時間表現（快、慢、正常）和準確性（對、錯）兩個維度，對每道有效題目進行了分類。針對不同的分類，直接列出了可能的標準化**英文診斷標籤參數**（如 `` `CR_REASONING_CHAIN_ERROR` ``, `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``, `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 等）。結合學生回憶、二級證據及質化分析觸發機制，旨在從這些標準參數中選擇最符合學生情況的診斷結論。
**結果去向：** 本章產生的診斷參數是第七章制定針對性練習方法建議的核心依據，也是第八章診斷總結報告（需經對照表轉譯為中文）的關鍵組成部分。質化分析的觸發為無法明確診斷的情況提供了深入探究的路徑。

</aside>

---

# 第四章：核心技能/題型/領域參考

<aside>

**本章目標:** 提供核心技能與其下可能包含的具體題型分類參考，明確 Verbal 各 `question_fundamental_skill` 下包含的具體題目類型。

**主要關注:** 提供 `CR` 和 `RC` 的詳細題型列表，展示核心技能與具體題型的對應關係。

**為何重要:** 為錯誤分析（第二章）、原因探究（第三章）、練習建議（第七章）提供統一、清晰的子題型分類標準。

</aside>

- **核心技能 (`Fundamental Skills`)**
    - 以下是Verbal部分考察的主要核心技能分類：
        - `Plan/Construct`: 涉及構建、計劃或評估方案/論證。
        - `Identify Stated Idea`: 識別文章或題幹中明確陳述的信息。
        - `Identify Inferred Idea`: 基於已有信息進行邏輯推斷。
        - `Analysis/Critique`: 分析論證結構、評估論證有效性或識別邏輯錯誤。
- **具體題型分類**
    - 以下將具體的`CR`和`RC`子題型類型歸類，並提示其與上述核心技能的可能關聯。
    - **`CR` 題型分類 (按核心技能參考)**
        - **`Analysis/Critique`:**
            - 削弱 (`Weaken`)
            - 加強 (`Strengthen`)
            - 評估 (`Evaluation` / `Evaluate the Argument`)
            - 邏輯錯誤 (`Flaw in the Reasoning`)
            - 論證方法/結構 (`Method of Reasoning` / `Argument Structure` / `Boldface`)
        - **`Plan/Construct`:**
            - 方案/目標 (`Plan` / `Goal Evaluation`)
            - 假設 (`Assumption`)
            - 解釋/調和矛盾 (`Explain` / `Resolve the Paradox`)
            - 填空/完成段落 (`Complete the Passage` / `Fill in the Blank`)
            - 推論/結論 (`Inference` / `Conclusion`)
    - **`RC` 題型分類 (按核心技能參考)**
        - **1. `Identify Stated Idea` / Explicit Information**
            - 主旨題 (`Main Idea` / `Primary Purpose`)
            - 細節題 / 支持觀點題 (`Supporting Idea` / `Detail` / `Specific Information`)
        - **2. `Identify Inferred Idea` / Implicit Information**
            - 推論題 (`Inference`)
            - 應用題 (`Application`)
            - 語氣/態度題 (`Tone` / `Attitude`)
            - 作用/功能題 (`Function` / `Purpose of paragraph/sentence`)
            - 評估/類比題 (`Evaluation` / `Analogy`)

<aside>

**本章總結：** 本章提供了一個參考框架，將 GMAT Verbal 部分考察的核心技能 (`question_fundamental_skill`) 與更具體的 `CR` 和 `RC` 子題型進行了分類和映射。
**結果去向：** 這個分類標準為其他章節提供了統一的語言和結構。它被用於第二章按技能/題型匯總錯誤率，第三章在診斷和二級證據分析中識別具體弱點題型，第七章生成針對特定題型的練習建議，以及第八章在總結報告中清晰地描述技能和題型表現。

</aside>

---

# 第五章：特殊模式觀察與粗心評估

<aside>

**本章目標:** 觀察作答行為是否與題目位置有關，評估整體粗心問題。

**主要關注:** 測驗前期作答是否過快，整體「快而錯」的比例。

**為何重要:** 識別不良答題策略和潛在的粗心習慣。

</aside>

- **前期過快題目:**
    - 找出 `question_position` <= `total_number_of_questions` / 3 且 `question_time` < 1.0 分鐘 的題目。
    - 輸出風險提醒參數: 若存在此類題目，觸發參數 `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``。
- **粗心率計算 (`carelessness_issue`):**
    - `num_relatively_fast_total` = 有效數據中滿足第三章 "快" 定義 (`is_relatively_fast` == `True`) 的題目總數。
    - `num_relatively_fast_incorrect` = 有效數據中 `is_relatively_fast` == `True` 且 `is_correct` = `False` 的題目總數。
    - 若 `num_relatively_fast_total` > 0，計算 `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total`。
    - 若 `fast_wrong_rate` > 0.25，則標記 `carelessness_issue` = `True`。
- **輸出診斷標籤參數:** 若 `carelessness_issue` = `True`，觸發參數 `` `BEHAVIOR_CARELESSNESS_ISSUE` ``。

<aside>

**本章總結：**我們檢查了學生在測驗前段是否存在作答過快的現象 (`BEHAVIOR_EARLY_RUSHING_FLAG_RISK`)，並通過計算基於相對時間標準的「快而錯」題目在所有「快」題目中的比例 (`fast_wrong_rate`)，評估了是否存在潛在的粗心問題 (`BEHAVIOR_CARELESSNESS_ISSUE`)。

**結果去向：**本章觸發的參數（`BEHAVIOR_EARLY_RUSHING_FLAG_RISK`, `BEHAVIOR_CARELESSNESS_ISSUE`）提供了關於學生答題策略和習慣的額外信息，**將通過附錄 A 對照表轉譯後**，作為輔助性結論納入第八章的總結報告中，並可能引導學生反思其答題節奏和仔細程度。

</aside>

---

# 第六章：基礎能力覆蓋規則

<aside>

**目標:** 檢查是否有某個**未被豁免的**核心技能存在普遍且嚴重的困難。

</aside>

**新增：基礎能力豁免規則 (Fundamental Skill Exemption Rule)**

<aside>

**目標:** 識別學生已完全掌握且能在時間限制內完成的技能，避免在第七章生成不必要的練習建議。

</aside>

- **豁免條件計算 (在覆蓋規則判斷之前進行):**
    - 對於某個核心技能 (`question_fundamental_skill`)：
        - 篩選出屬於該技能的所有有效題目（排除 `is_invalid` = `True` 的題目）。
        - **條件一 (準確性):** 所有這些有效題目的 `is_correct` 均為 `True`。
        - **條件二 (效率):**
            - 對於 `CR` 題目：所有有效題目的 `overtime` 標記均為 `False`。
            - 對於 `RC` 題目：所有有效題目的 `group_overtime` 標記和 `individual_overtime` 標記均為 `False`。
    - 若同時滿足**條件一**和**條件二**，則計算得出該核心技能的豁免狀態 `skill_exemption_status` 為 `True`。
- **豁免規則的影響:**
    - 計算出的豁免狀態 (`skill_exemption_status`) **僅用於**第七章練習建議生成邏輯。被標記為豁免的技能將**跳過**所有練習建議。
    - 豁免狀態**不影響**本章後續的基礎能力覆蓋規則判斷（覆蓋規則仍基於所有非豁免技能的錯誤率）。
    - 診斷總結（第八章）會提及這些被豁免的技能，以展示學生的強項。

---

**基礎能力覆蓋規則判斷 (基於所有技能，不考慮豁免狀態)**

- **邏輯:**
    - **(此處計算基於所有技能，以便全面評估，豁免狀態僅影響下游建議)**
    - 計算每個核心技能 (`question_fundamental_skill`) 在有效數據中的 總錯誤率 (`error_rate_skill`)。
    - 若某技能的 `error_rate_skill` > 0.50 (即 > 50%)，則觸發 `skill_override_triggered`[`Skill`] = `True`。
- **影響:** 若觸發 `skill_override_triggered`，第七章的練習建議 (如果該技能未被豁免) 將側重該技能的基礎鞏固，而非針對個別錯題。

<aside>

**本章總結：**本章首先定義瞭如何計算核心技能的豁免狀態（全對且無超時）。然後，獨立於豁免狀態，設定了一個覆蓋規則，通過檢查每個核心技能的整體錯誤率，判斷是否存在錯誤率過高（>50%）的情況，並記錄在 `skill_override_triggered` 中。

**結果去向：**計算出的 `skill_exemption_status` 將傳遞給第七章，用於跳過已掌握技能的建議。`skill_override_triggered` 標記也將傳遞給第七章，用於指導未被豁免的薄弱技能生成宏觀建議。

</aside>

---

# 第七章：練習規劃與建議

<aside>

**本章目標:** 基於診斷結果，生成具體、可操作的練習建議。

**主要關注:** 提供練習材料、方法、重點（難度、限時）和基礎能力訓練計劃。區分宏觀與個案建議。

**為何重要:** 將診斷轉化為行動。

</aside>

- *(註：本章的建議生成依賴於前續章節的分析結果，包括但不限於：`question_fundamental_skill` (`S`), `question_difficulty` (`D`), `question_time` (`T`), `overtime`/`group_overtime`/`individual_overtime` 標記, `skill_override_triggered` 標記, 難度區間定義, `RC`目標時間規則等，均遵循當前版本定義。)*
- **練習教材與範圍建議**
    - 核心材料: OG, OV (Official Guide & Verbal Review)。
    - 補充練習: GMAT Club 等平台（可篩選特定難度/題型）。
- **練習建議生成邏輯**
    - **函數定義:**
        - `floor_to_nearest_0.5`(`value`): 將輸入數值 `value` 向下取整到最接近的 0.5 的倍數。
    - **前置計算:**
        - 初始化一個字典 `recommendations_by_skill` = `{}`。
        - 初始化一個集合 `processed_override_skills` = `set()`。
    - **遍歷題目:** 檢查所有在前續章節分析中被標記需要關注的有效數據題目 `X` (其核心技能為 `S`，難度為 `D`，原始用時為 `T`，題型為 `Type`)。
        - **檢查技能豁免狀態:**
            - 若技能 `S` 的 `skill_exemption_status` == `True` (根據新增的豁免規則計算得出)，則**跳過**此題目的後續建議生成步驟，處理下一個題目。
        - **檢查技能覆蓋規則 (僅對未豁免技能):**
            - 若技能 `S` 觸發了覆蓋規則 (`skill_override_triggered`[`S`] == `True`) 且技能 `S` **未**在 `processed_override_skills` 中：
                - 生成宏觀建議 `G` = "針對 [`S`] 技能，由於整體錯誤率偏高 (根據第六章分析)，建議全面鞏固基礎，可從中低難度題目開始系統性練習，掌握核心方法。"
                - 將宏觀建議 `G` 添加到 `recommendations_by_skill`[`S`]。
                - 將技能 `S` 添加到 `processed_override_skills`。
        - **生成個案建議 (若技能 S 未觸發宏觀建議):**
            - **確定練習難度 (`Y`):** 根據題目 `X` 的難度 `D` 進行映射（**統一 6 級標準**）：
                - 若 `D` ≤ -1: `Y` = "低難度 (Low) / 505+"
                - 若 -1 < `D` ≤ 0: `Y` = "中難度 (Mid) / 555+"
                - 若 0 < `D` ≤ 1: `Y` = "中難度 (Mid) / 605+"
                - 若 1 < `D` ≤ 1.5: `Y` = "中難度 (Mid) / 655+"
                - 若 1.5 < `D` ≤ 1.95: `Y` = "高難度 (High) / 705+"
                - 若 1.95 < `D` ≤ 2: `Y` = "高難度 (High) / 805+"
            - **確定起始練習限時 `Z` (分鐘):** (**統一計算規則**)
                - 設定目標時間 (`target_time`):
                    - 若 `Type` == 'CR': `target_time` = 2.0
                    - 若 `Type` == 'RC': `target_time` = 1.5 (單題分析目標)
                - 判斷是否慢 (`is_slow`): (`CR`: `overtime` == `True`; `RC`: `group_overtime` == `True` 或 `individual_overtime` == `True`)
                - 計算 `base_time`: 若 `is_slow` == `True` 則 `T` - 0.5，否則 `T`。
                - 計算 `Z_raw` = `floor_to_nearest_0.5`(`base_time`)。
                - 確保最低值: `Z` = `max`(`Z_raw`, `target_time`)。
            - **構建建議文本:**
                - 基本模板：「針對 [`Skill`] 的相關考點 (根據第三章診斷結果確定)，建議練習 [`Y`] 難度題目，起始練習限時建議為 [`Z`] 分鐘。(最終目標時間：`CR` 2分鐘 / `RC` 1.5分鐘)。"
                - **優先級標註:** 如果該題觸發了 `special_focus_error` = `True`，則在此建議前標註「*基礎掌握不穩*」。
                - **超長提醒:** 若 `Z` - `target_time` > 2.0 分鐘，加註提醒「**需加大練習量以確保逐步限時有效**」。
            - 將個案建議 `C` 添加到 `recommendations_by_skill`[`Skill`]。
    - **整理與輸出建議列表：**
        - 初始化最終建議列表 `final_recommendations`。
    - **整理聚合建議:** 遍歷 `recommendations_by_skill` 字典。
        - 對於每個技能 `S` 及其建議列表 `skill_recs`:
            - 如果列表非空，將整理好的技能 `S` 的建議添加到 `final_recommendations`。
    - **最終輸出:** 輸出 `final_recommendations`，確保按技能聚合，優先顯示標註 `special_focus_error` 的建議。

<aside>

**本章總結：** 本章綜合運用前面所有章節的分析結果（包括診斷標籤、難度表現、時間標記、技能錯誤率、覆蓋規則、閱讀障礙標記等），為學生生成了一套個性化的練習計劃。該計劃區分宏觀與個案建議，包括推薦的練習範圍、難度 (`Y`/`Y_agg`)、起始限時 (`Z`)、最終目標時間。`special_focus_error` 的建議被優先標註。如果分析表明存在基礎閱讀問題，相應的基礎訓練建議會被觸發。

**結果去向：** 本章輸出的完整練習計劃是整個診斷流程的核心行動方案，將直接呈現給學生，並構成第八章總結報告中最重要的「後續行動」部分。

</aside>

---

# 第八章：診斷總結與後續行動

<aside>

**本章目標:** 匯總分析結果，生成全面、易懂的自然語言診斷報告。 **(基於內部診斷參數，通過對照表轉譯為中文)**

**主要關注:** 整合關鍵發現、練習建議，並引導學生反思。

**為何重要:** 提供整體視角，指導改進。

</aside>

**1. 開篇總結**

*   (總結第一章發現：學生在本輪Verbal測驗中是否感受到明顯時間壓力？總體作答時間如何？測驗末尾是否有因時間壓力導致作答過快、可能影響數據有效性的跡象？Verbal部分疲勞效應明顯，建議考慮考試策略調整，如將Verbal置於考試最前或進行考前閱讀暖身。)

**2. 表現概覽**

*   (總結第二章發現：學生在不同難度區間（低/中/高）的 `CR` 和 `RC` 題目上表現如何？錯誤主要集中在哪些難度區間？哪些核心技能 (`question_fundamental_skill`) 是相對弱項？)
*   **(提及哪些核心技能因表現完美（全對且無超時）而被豁免，展示為已掌握的強項。)**
*   (提及第一章關於 `RC` 閱讀時間的初步評估結果，如果觸發了 `reading_comprehension_barrier_inquiry`，在此處或核心問題診斷中提示可能存在基礎閱讀障礙需要關注。)

**3. 核心問題診斷**

*   (使用自然語言歸納第三章主要發現：**基於分析產生的診斷參數 (如 `` `CR_REASONING_CHAIN_ERROR` ``, `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` `` 等)，通過附錄 A 對照表轉譯為自然語言描述**，說明學生在 `CR` 和 `RC` 中最常見的錯誤類型和原因。)
*   (優先提及) (如果診斷參數包含 `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``，在此處強調：『尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤，這表明在這些知識點或技能的應用上可能存在穩定性問題。』)

**4. 模式觀察**

*   (提及第五章發現) (如果診斷參數包含 `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``，提示：『測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 "flag for review" 風險。』)
*   (提及第五章發現) (如果診斷參數包含 `` `BEHAVIOR_CARELESSNESS_ISSUE` ``，提示：『分析顯示，"快而錯" 的情況佔比較高，提示可能需要關注答題的仔細程度，減少粗心錯誤。』)

**5. 基礎鞏固提示**

*   (提及第六章發現) (如果任何 `fundamental_skill` 觸發了 `skill_override_triggered`，明確指出：『對於 [`觸發覆蓋規則的技能列表`] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。』)

**6. 練習計劃呈現**
*   (清晰、完整地列出第七章生成的 **練習計劃**，按技能聚合。)
*   (計劃包含：針對觸發覆蓋規則技能的 **宏觀建議 (Macroscopic Recommendations)**，以及針對其他問題的 **個案建議 (Case-Specific Recommendations)**。)
*   (個案建議明確指出練習技能/考點、建議的 **練習難度 (Y)**、**起始練習限時 (Z)** 及最終目標時間。)
*   (計劃中，與 `special_focus_error` (對應參數 `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) 相關的建議會被 **優先顯示或特別標註** (如加註 "*基礎掌握不穩*")。)
*   (計劃包含相關的 **超長提醒 (Volume Alerts)**，提示練習量需求。)
*   (若觸發了基礎閱讀能力訓練建議，相應內容也會整合在此處。)

**7. 後續行動指引**

*   **核心約束:** 報告**必須完全使用自然語言**呈現給學生，通過**附錄 A 對照表**將內部使用的**英文診斷參數**轉譯為易於理解的中文描述，絕不直接暴露內部參數。
*   **引導反思：** (根據診斷出的主要問題類型提問，問題本身使用自然語言)
    *   `CR` 相關：『回想做錯的 `CR` 題，是沒看懂題幹的邏輯關係，還是選項難以排除？是哪種題型（削弱、加強、假設等）更容易出錯？』
    *   `RC` 相關：『回想做錯的 `RC` 題，是文章沒讀懂，題目問啥沒理解，還是定位到了但理解有偏差？是否存在特定主題或文章結構的閱讀困難？基礎閱讀（詞彙、長難句）是否存在明顯瓶頸？』
*   **二級證據參考建議：**
    *   *觸發時機：* 當您無法準確回憶具體的錯誤原因、涉及的技能弱點或題型，或需要更客觀的數據來確認問題模式時。
    *   *建議行動：* 『為了更精確地定位您在 [`某技能`/`題型`] 上的具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些技能點、題型或錯誤類型（參考**附錄 A** 中的描述）反覆出現問題。』
*   **質化分析建議：**
    *   *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，特別是涉及複雜的邏輯推理或閱讀理解過程時，或者上述方法仍無法幫您釐清根本問題時。
    *   *建議行動：* 『如果您對 [`某類問題`，例如 `CR` 邏輯鏈分析或 `RC` 推理過程] 的錯誤原因仍感困惑，可以嘗試**提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。』
*   **輔助工具推薦建議：**
    *   *推薦邏輯：* 為了更有效地解決診斷中發現的問題，系統將根據您的具體情況，推薦以下可能適用的輔助學習工具。最終報告中僅會列出與您的診斷結果最相關的工具，並以自然語言描述其用途。
    *   *診斷到工具的映射規則：*
    *   （以下列表涵蓋附錄 A 中定義的所有診斷參數及其對應的工具/提示推薦）*
        *   **若診斷涉及 CR 推理或特定題型困難 (基於第三章診斷參數)：**
            *   若診斷包含 `` `CR_REASONING_CHAIN_ERROR` `` 或 `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` `` → 可能推薦外部工具 **`Dustin_GMAT_CR_Core_Issue_Identifier`** 或 **`Dustin_GMAT_CR_Chain_Argument_Evaluation`**；或使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` `` (針對 `` `CR_REASONING_CHAIN_ERROR` ``) 或 `` `Verbal-related/01_basic_explanation.md` `` (針對 `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` ``)。
            *   若診斷包含 `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (例如 Boldface) → 可能推薦外部工具 **`Dustin's GMAT CR: Boldface Interactive Tutor`**；或使用 AI 提示：`` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``。
            *   若診斷包含 `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (例如 Argument Construction) 或涉及論證結構分析弱 → 可能推薦外部工具 **`Dustin_GMAT_CR_Role_Argument_Construction`**；或使用 AI 提示：`` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``。
            *   若診斷包含 `` `CR_REASONING_ABSTRACTION_DIFFICULTY` `` 或基礎邏輯概念不清 → 可能推薦外部工具 **`Dustin's GMAT Tool: Textbook Explainer`**；或使用 AI 提示：`` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``。
            *   若診斷包含 `` `CR_READING_BASIC_OMISSION` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``。
            *   若診斷包含 `` `CR_READING_DIFFICULTY_STEM` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``。
            *   若診斷包含 `` `CR_READING_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `CR_QUESTION_UNDERSTANDING_MISINTERPRETATION` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``。
            *   若診斷包含 `` `CR_REASONING_PREDICTION_ERROR` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``。
            *   若診斷包含 `` `CR_REASONING_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``。
            *   若診斷包含 `` `CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY` `` → 可能使用 AI 提示： `` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/01_basic_explanation.md` ``。
            *   若診斷包含 `` `CR_AC_ANALYSIS_RELEVANCE_ERROR` `` → 可能使用 AI 提示： `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``。
            *   若診斷包含 `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``。
            *   若診斷包含 `` `CR_AC_ANALYSIS_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``。
            *   若診斷包含 `` `CR_METHOD_PROCESS_DEVIATION` `` → 可能使用 AI 提示： `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``。

        *   **若診斷涉及 RC 閱讀理解障礙 (基於第三章診斷參數或第一章 `reading_comprehension_barrier_inquiry` 觸發)：**
            *   若診斷包含 `` `RC_READING_SPEED_SLOW_FOUNDATIONAL` `` 或 `rc_reading_time` 估算偏長 → 可能推薦外部工具 **`Dustin GMAT: Chunk Reading Coach`**；或使用 AI 提示：`` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``, `` `RC_READING_DOMAIN_KNOWLEDGE_GAP` `` 或 `` `RC_READING_VOCAB_BOTTLENECK` `` (且非系統性學習) → 可能推薦外部工具 **`Dustin's GMAT Terminator: Sentence Cracker`**；或針對性使用 AI 提示：`` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` `` (用於詞彙)；`` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` `` (用於句式)；`` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/08_source_passage_rewrite.md` `` (用於領域)。
            *   若診斷包含 `` `RC_READING_VOCAB_BOTTLENECK` `` (且需要系統性學習) → 可能推薦外部工具 **`Dustin's GMAT Core: Vocab Master`**；也可輔助使用 AI 提示：`` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` ``。
            *   若診斷包含 `` `RC_READING_PRECISION_INSUFFICIENT` `` → 可能推薦外部工具 **`Dustin GMAT Close Reading Coach`**；或使用 AI 提示：`` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` `` → 可能推薦外部工具 **`Dustin_GMAT_RC_Passage_Analyzer`**；或使用 AI 提示：`` `Verbal-related/04_mindmap_passage.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `RC_READING_INFO_LOCATION_ERROR` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``。
            *   若診斷包含 `` `RC_READING_KEYWORD_LOGIC_OMISSION` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `RC_METHOD_INEFFICIENT_READING` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``。
            *   若診斷包含 `` `RC_QUESTION_UNDERSTANDING_MISINTERPRETATION` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``。
            *   若診斷包含 `` `RC_LOCATION_ERROR_INEFFICIENCY` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``。
            *   若診斷包含 `` `RC_LOCATION_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``。
            *   若診斷包含 `` `RC_REASONING_INFERENCE_WEAKNESS` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``。
            *   若診斷包含 `` `RC_REASONING_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``。
            *   若診斷包含 `` `RC_AC_ANALYSIS_DIFFICULTY` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``。
            *   若診斷包含 `` `RC_AC_ANALYSIS_TIME_EXCESSIVE` `` → 可能使用 AI 提示： `` `Verbal-related/03_quick_rc_tricks.md` ``。

        *   **若診斷涉及選項篩選困難或粗心問題 (基於第三章/第五章診斷參數)：**
            *   若診斷包含 `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` ``, `` `RC_AC_ANALYSIS_DIFFICULTY` `` 或 `` `BEHAVIOR_CARELESSNESS_ISSUE` `` → 可能推薦外部工具 **`Dustin_GMAT_Verbal_Distractor_Mocker`**；或針對 `` `BEHAVIOR_CARELESSNESS_ISSUE` `` 使用 AI 提示：`` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/01_basic_explanation.md` ``。
        *   **若診斷包含基礎掌握問題 (基於第三章診斷參數)：**
            *   若診斷包含 `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` → 優先使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` `` 來鞏固基礎。
        *   **若診斷包含效率問題 (基於第三章診斷參數)：**
            *   若診斷包含 `` `EFFICIENCY_BOTTLENECK_[AREA]` `` → 參考 ``[AREA]`` 對應環節的 AI 提示，並額外使用 `` `Verbal-related/02_quick_cr_tpa_tricks.md` `` (CR) 或 `` `Verbal-related/03_quick_rc_tricks.md` `` (RC)。
        *   **若診斷包含行為模式問題 (基於第五章診斷參數)：**
            *   若診斷包含 `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` → 可能使用 AI 提示： `` `Verbal-related/05_evaluate_explanation.md` `` 來反思節奏。
            *   若診斷包含 `` `BEHAVIOR_GUESSING_HASTY` `` → 可能使用 AI 提示： `` `Verbal-related/01_basic_explanation.md` `` 學習完整步驟。
        *   **若需要綜合複習、分類練習或模擬 (基於第二、三、六、七章的綜合建議)：**
            *   (此處觸發條件較通用，可基於整體練習建議) → 可能推薦外部工具： **`GMAT - Terminator (CR Review)`**, **`GMAT - Terminator (RC Review)`**, **`Dustin's GMAT RC: Question Classifier`**, **`Dustin_GMAT_CR_Question_Classifier`**, **`Dustin_GMAT_CR_Question_Simulator`**, **`Dustin_GMAT_RC_Question_Simulator`**, **`Dustin_GMAT_Time_Analyst (CR & RC)`**, **`Dustin_GMAT_Review_Assistant (CR & RC)`**, **`Dustin_GMAT_RC_Preparatory_Answer_Trainer`**。
    *   *最終呈現：* 在提供給您的最終診斷報告中，我們會根據您的具體診斷結果，使用**附錄A的對照表**將診斷參數轉譯，並用自然語言說明推薦的工具及其適用場景。

<aside>

**本章總結：**本章是最終的成果匯總，將前面所有章節的分析發現（時間壓力、無效數據、難度/技能表現、**基於英文參數的**根本原因診斷、特殊模式觀察、`RC`閱讀評估等）以及第七章生成的完整練習計劃，整合成一份全面、易於理解的自然語言診斷報告 **（通過附錄A對照表將內部參數轉譯為中文）**。報告強調了 Verbal 部分的疲勞因素和可能的基礎閱讀問題。報告還包含引導學生反思的問題和進行質化分析、參考二級證據的建議，以及基於診斷參數的個性化工具推薦。

**結果去向：**這是交付給學生的最終產品，旨在提供對其 Verbal 表現的深入洞察，並明確指出改進的方向和具體行動步驟。

</aside>

---

# 附錄 A：診斷標籤參數與中文對照表

| 英文參數 (Parameter)                          | 中文描述 (Chinese Description)                         |
|-----------------------------------------------|----------------------------------------------------|
| **CR - Reading Comprehension**                |                                                    |
| `CR_READING_BASIC_OMISSION`                   | CR 閱讀理解: 基礎理解疏漏                           |
| `CR_READING_DIFFICULTY_STEM`                  | CR 閱讀理解: 題幹理解障礙 (關鍵詞/句式/邏輯/領域)     |
| `CR_READING_TIME_EXCESSIVE`                   | CR 閱讀理解: 閱讀耗時過長                         |
| **CR - Question Understanding**               |                                                    |
| `CR_QUESTION_UNDERSTANDING_MISINTERPRETATION` | CR 題目理解: 提問要求把握錯誤                       |
| **CR - Reasoning Deficiencies**             |                                                    |
| `CR_REASONING_CHAIN_ERROR`                    | CR 推理障礙: 邏輯鏈分析錯誤 (前提/結論/關係)           |
| `CR_REASONING_ABSTRACTION_DIFFICULTY`         | CR 推理障礙: 抽象邏輯/術語理解困難                   |
| `CR_REASONING_PREDICTION_ERROR`               | CR 推理障礙: 預判方向錯誤或缺失                     |
| `CR_REASONING_TIME_EXCESSIVE`                 | CR 推理障礙: 邏輯思考耗時過長                     |
| `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY`       | CR 推理障礙: 核心議題識別困難                       |
| **CR - Answer Choice Analysis**             |                                                    |
| `CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY`     | CR 選項辨析: 選項本身理解困難                       |
| `CR_AC_ANALYSIS_RELEVANCE_ERROR`              | CR 選項辨析: 選項相關性判斷錯誤                     |
| `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION`         | CR 選項辨析: 強干擾選項混淆                         |
| `CR_AC_ANALYSIS_TIME_EXCESSIVE`               | CR 選項辨析: 選項篩選耗時過長                     |
| **CR - Method Application**                  |                                                    |
| `CR_METHOD_PROCESS_DEVIATION`                 | CR 方法應用: 未遵循標準流程                         |
| `CR_METHOD_TYPE_SPECIFIC_ERROR`               | CR 方法應用: 特定題型方法錯誤/不熟 (需註明題型)       |
| **RC - Reading Comprehension**                |                                                    |
| `RC_READING_INFO_LOCATION_ERROR`              | RC 閱讀理解: 關鍵信息定位/理解錯誤                 |
| `RC_READING_KEYWORD_LOGIC_OMISSION`           | RC 閱讀理解: 忽略關鍵詞/邏輯                       |
| `RC_READING_VOCAB_BOTTLENECK`                 | RC 閱讀理解: 詞彙量瓶頸                             |
| `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY`    | RC 閱讀理解: 長難句解析困難                         |
| `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY`     | RC 閱讀理解: 篇章結構把握不清                       |
| `RC_READING_DOMAIN_KNOWLEDGE_GAP`             | RC 閱讀理解: 特定領域背景知識缺乏                   |
| `RC_READING_SPEED_SLOW_FOUNDATIONAL`          | RC 閱讀理解: 閱讀速度慢 (基礎問題)                   |
| `RC_READING_PRECISION_INSUFFICIENT`           | RC 閱讀精度不足 (精讀/定位問題)                     |
| **RC - Reading Method**                       |                                                    |
| `RC_METHOD_INEFFICIENT_READING`               | RC 閱讀方法: 閱讀方法效率低 (過度精讀)               |
| **RC - Question Understanding**               |                                                    |
| `RC_QUESTION_UNDERSTANDING_MISINTERPRETATION` | RC 題目理解: 提問焦點把握錯誤                       |
| **RC - Location Skills**                      |                                                    |
| `RC_LOCATION_ERROR_INEFFICIENCY`              | RC 定位能力: 定位錯誤/效率低下                      |
| `RC_LOCATION_TIME_EXCESSIVE`                  | RC 定位能力: 定位效率低下 (反覆定位)                 |
| **RC - Reasoning Deficiencies**             |                                                    |
| `RC_REASONING_INFERENCE_WEAKNESS`             | RC 推理障礙: 推理能力不足 (預判/細節/語氣)             |
| `RC_REASONING_TIME_EXCESSIVE`                 | RC 推理障礙: 深度思考耗時過長                     |
| **RC - Answer Choice Analysis**             |                                                    |
| `RC_AC_ANALYSIS_DIFFICULTY`                   | RC 選項辨析: 選項理解/辨析困難 (含義/對應)             |
| `RC_AC_ANALYSIS_TIME_EXCESSIVE`               | RC 選項辨析: 選項篩選耗時過長                     |
| **Foundational Mastery (CR & RC)**            |                                                    |
| `FOUNDATIONAL_MASTERY_INSTABILITY_SFE`        | 基礎掌握: 應用不穩定 (Special Focus Error)          |
| **Efficiency Issues (CR & RC)**               |                                                    |
| `EFFICIENCY_BOTTLENECK_[AREA]`                | 效率問題: [具體障礙] 導致效率低下 (需指明 Area: READING, REASONING, LOCATION, AC_ANALYSIS)     |
| **Behavioral Patterns**                       |                                                    |
| `BEHAVIOR_EARLY_RUSHING_FLAG_RISK`            | 行為模式: 前期作答過快 (Flag risk)                 |
| `BEHAVIOR_CARELESSNESS_ISSUE`                 | 行為模式: 粗心問題 (快而錯比例高)                    |
| `BEHAVIOR_GUESSING_HASTY`                     | 行為模式: 過快疑似猜題/倉促                     |

（本文件結束）