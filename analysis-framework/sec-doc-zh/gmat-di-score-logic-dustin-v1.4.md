# **第零章：核心輸入數據與設定**

<aside>

**本章目標：** 定義 DI 科目診斷分析所需的所有核心輸入數據結構。

**主要關注：** 確立基礎設定（如考試時間、題數）、題型定義、每題需記錄的詳細數據點（`question_position`、`question_time`、`is_correct`、`content_domain`、`question_type`、`question_difficulty`）、整體測驗數據以及需要預處理或計算的衍生數據（如 MSR 閱讀時間、各題型平均時間、已掌握最高難度）。

**為何重要：** 本章定義的數據是後續所有分析、計算和診斷的基石。數據的完整性、準確性和一致性直接關係到診斷結果的有效性和可靠性。

</aside>

- **基礎設定：**
    - `Max Allowed Time`: 45 分鐘
    - `Total Number of Questions`: 20 題
- **題型縮寫定義：**
    - `DS`: Data Sufficiency
    - `TPA`: Two-Part Analysis
    - `MSR`: Multi-Source Reasoning
    - `GT`: Graph & Table
- **每題數據：**
    - `question_position` (題目順序，必需，作為唯一識別符)
    - `question_time` (作答時間/分鐘)
    - `is_correct` (是否正確：`True`/`False`)
    - `content_domain` (內容領域：`Math Related`/`Non-Math Related`)
    - `question_type` (題型：`DS`, `TPA`, `MSR`, `GT`)
    - `msr_group_id` (MSR 題組 ID，若 `question_type` 為 `MSR` 則必需)
    - `Fundamental Skills` (**確認不追蹤**)
    - `question_difficulty` (難度值)
- **整體數據：**
    - `Total Test Time` (總作答時間/分鐘)
    - `Max Allowed Time` (測驗上限時間)
    - `Total Number of Questions` (總題數)
- **DI 衍生數據：**
    - **`MSR` 閱讀時間 (`msr_reading_time`)：** 針對每個 `MSR` 題組，計算 `msr_reading_time` = 該題組第一題的 `question_time` - (該題組中**除第一題外**所有其他題目的平均 `question_time`)。此計算僅在題組包含至少兩題時有效，且計算結果附加在題組的第一題上。(*此數據將用於第一章 MSR 單題超時判斷*)
    - **`MSR` 題組數據預計算:**
        - `group_total_time`: 計算每個 `MSR` 題組內所有題目的 `question_time` 總和。
        - `num_q_in_group`: 計算每個 `MSR` 題組包含的題目數量。
    - **`GT` 時間分配：** 無需特別區分看圖和作答時間。
    - **各題型平均作答時間 (`average_time_per_type`)：** 基於**有效數據（過濾後）**計算各 `question_type` (`DS`, `TPA`, `MSR`, `GT`) 的平均作答時間。(*此數據將用於第三章定義 `is_relatively_fast` 和第四章計算粗心率*)
    - **考試前三分之一各題型平均時間 (`first_third_average_time_per_type`)：** 對於每種 `question_type` (`DS`, `TPA`, `MSR`, `GT`)，計算 `question_position` <= (`Total Number of Questions` / 3) 的所有題目的平均 `question_time`。(*此數據將用於第一章無效數據判斷*)
    - **已掌握最高難度 (`max_correct_difficulty_per_combination`)：** 對於每個 `question_type` 和 `content_domain` 的組合，記錄該組合下所有 `is_correct` == `True` 的題目中的最高 `question_difficulty` 值。

<aside>

**本章總結：** 本章明確了 DI 診斷所需輸入數據的標準格式，包括基礎考試參數、各題目的詳細維度信息，以及為後續分析準備的衍生計算指標，如 `MSR` 閱讀時間、各題型平均時間和分組合的已掌握最高難度。

**結果去向：** 本章定義的所有數據點和衍生指標將作為後續章節進行時間壓力評估、表現分析、原因探究、模式觀察和練習建議生成的基礎。

</aside>

---

# **第一章：整體時間策略與數據有效性評估**

<aside>

**本章目標：** 評估學生在 DI 部分的整體時間壓力感知，設定題型超時標準，並識別可能因時間極度不足或策略性放棄而產生的無效數據。

**主要關注：** 計算總時間差，判斷時間壓力狀態 (`time_pressure`)，根據壓力狀態為不同題型 (`question_type`) 設定和標記超時 (`overtime`) 閾值和狀態，並根據作答時間識別測驗末尾的無效數據 (`is_invalid`)。

**為何重要：** 準確評估時間壓力有助於理解學生的作答環境，設定合理的超時標準。識別並排除無效數據對於確保後續分析的準確性至關重要，避免基於猜測數據做出錯誤診斷。

</aside>

1. **計算總時間差 (`time_diff`)**: 
   `time_diff` = `max_allowed_time` - `total_test_time`

2. **判斷時間壓力狀態 (`time_pressure`)**: 
   - 預設 `time_pressure` = `False`。
   - 檢查測驗末尾情況：找出測驗最後 1/3 的題目 (`last_third_questions`) 中 `question_time` < 1.0 分鐘的題目 (`fast_end_questions`)。
   - 判斷邏輯：如果 `time_diff` <= 3 分鐘 **且** `fast_end_questions` 不為空，則設定 `time_pressure` = `True`。
   - **用戶覆蓋：** 若用戶明確指出壓力不大，則強制設定 `time_pressure` = `False`。

3. **設定超時閾值與規則 (基於 `time_pressure`)**: 
   - **`TPA` 超時閾值 (`overtime_threshold_tpa`)**: 
       - 若 `time_pressure` == `True`: 3.0 分鐘。
       - 若 `time_pressure` == `False`: 3.5 分鐘。
   - **`GT` 超時閾值 (`overtime_threshold_gt`)**: 
       - 若 `time_pressure` == `True`: 3.0 分鐘。
       - 若 `time_pressure` == `False`: 3.5 分鐘。
   - **`DS` 超時閾值 (`overtime_threshold_ds`)**: 
       - 若 `time_pressure` == `True`: 2.0 分鐘。
       - 若 `time_pressure` == `False`: 2.5 分鐘。
   - **`MSR` 題組目標時間規則 (`msr_group_target_time`)**: 
       - 若 `time_pressure` == `True`: 6.0 分鐘。
       - 若 `time_pressure` == `False`: 7.0 分鐘。
   - **`MSR` 單題分析相關閾值**: 
       - `msr_reading_threshold`: 1.5 分鐘 (用於判斷閱讀時間是否過長)。
       - `msr_single_q_threshold`: 1.5 分鐘 (用於判斷單題作答時間是否過長)。
   - *說明：以上閾值和規則用於後續判斷各題型題目或題組是否超時 (`overtime`, `msr_group_overtime`)。*

4. **識別無效數據 (`is_invalid`)**:
   - **觸發前提:** 僅在 `time_pressure` == `True` 時，才執行無效數據的識別與標記。若 `time_pressure` == `False`，則不標記任何題目為 `is_invalid`。
   - **檢查範圍:** 僅檢查測驗最後 1/3 的題目 (`last_third_questions`)。
   - **定義「異常快速作答 (`abnormally_fast_response`)」標準 (滿足其一即可觸發):**
       - *標準 1 (疑似放棄):* `question_time` < 0.5 分鐘。
       - *標準 2 (絕對倉促):* `question_time` < 1.0 分鐘。
       - *標準 3 (相對單題倉促 - DS):* `question_time` < (`first_third_average_time_per_type`['DS'] * 0.5)。
       - *標準 4 (相對單題倉促 - TPA):* `question_time` < (`first_third_average_time_per_type`['TPA'] * 0.5)。
       - *標準 5 (相對單題倉促 - GT):* `question_time` < (`first_third_average_time_per_type`['GT'] * 0.5)。
       - *標準 6 (相對題組倉促 - MSR):* 該題目所屬的 MSR 題組的 `group_total_time` < (`first_third_average_time_per_type`['MSR'] * `num_q_in_group` * 0.5)。
   - **標記邏輯:** 在 `last_third_questions` 範圍內，若某題目 (或其所屬的 MSR 題組針對標準 6) 滿足了**至少一項** `abnormally_fast_response` 標準，**且 `time_pressure` == `True`**，則將該題目標記為 `is_invalid` = `True`。
   - *說明:* 此多重標準邏輯旨在更精準地識別在時間壓力下，考試末期可能因放棄或過度倉促而導致的無效作答數據。

5. **輸出與總結**: 
   - 本章產生的關鍵標記：`time_pressure` (布林值), 各題型超時閾值/規則, `is_invalid` 標記 (針對特定題目，且僅在 `time_pressure` 為 True 時觸發)。

**全局規則應用：數據過濾與標記**

1.  **標記超時 (`overtime`):** 根據本章定義的各題型閾值/規則，為所有**未被標記為 `is_invalid`** 的題目添加 `overtime` = `True` 標記：
    *   若 `question_type` == `'TPA'` 且 `question_time` > `overtime_threshold_tpa`，標記 `overtime` = `True`。
    *   若 `question_type` == `'GT'` 且 `question_time` > `overtime_threshold_gt`，標記 `overtime` = `True`。
    *   若 `question_type` == `'DS'` 且 `question_time` > `overtime_threshold_ds`，標記 `overtime` = `True`。
    *   **針對 `MSR` 題目的超時標記 (雙重標準):**
        *   **a. 題組超時標記 (`msr_group_overtime`):**
            *   計算每個 MSR 題組的總時間 (`group_total_time`)。
            *   獲取該題組的目標時間 `msr_group_target_time` (基於 `time_pressure`: True 時 6.0 分鐘, False 時 7.0 分鐘)。
            *   判斷: 如果 `group_total_time > msr_group_target_time`，則該 MSR 題組內**所有**題目標記 `msr_group_overtime = True`。
        *   **b. 單題超時標記 (`msr_individual_overtime`):**
            *   設定固定單題閾值 `msr_individual_q_threshold = 1.5` 分鐘 (不隨 `time_pressure` 變化)。
            *   計算調整後時間 `adjusted_msr_time`:
                *   對於題組第一題: `adjusted_msr_time = question_time - msr_reading_time` (使用第零章計算的 `msr_reading_time`)。
                *   對於題組非第一題: `adjusted_msr_time = question_time`。
            *   判斷: 如果某 MSR 題目的 `adjusted_msr_time > msr_individual_q_threshold` (1.5 分鐘)，則該題標記 `msr_individual_overtime = True`。
        *   **c. 最終 `overtime` 標記:**
            *   一個 MSR 題目最終被標記為 `overtime = True`，當且僅當該題目滿足 `msr_group_overtime == True` **或者** `msr_individual_overtime == True`。
2.  **創建過濾數據集：** 從原始題目數據中，移除所有被標記為 `is_invalid` = `True` 的題目。
3.  **後續分析範圍：** 第二章至第六章的所有計算、分析和建議，僅基於這個過濾後的數據集。

<aside>

**本章總結：** 我們首先計算了總時間差，判斷了學生的整體時間壓力狀態 (`time_pressure`)。基於此狀態，我們為不同題型（`DS`, `TPA`, `GT`, `MSR`）設定了相應的超時閾值或目標時間規則。然後，**僅在確定存在時間壓力 (`time_pressure` == `True`) 的情況下**，針對測驗最後三分之一的題目，根據新的多重標準（包括絕對時間過短、相對時間過短——與前三分之一平均時間比較、MSR題組整體時間過短）判斷是否為「異常快速作答 (`abnormally_fast_response`)」，並將滿足條件的題目識別為可能無效的數據 (`is_invalid`)。在進行後續分析前，我們會先根據超時規則標記超時題目 (`overtime`)，然後過濾掉無效數據。

**結果去向：** `time_pressure` 狀態和各題型的超時設定將作為後續分析的重要背景信息。被標記為 `overtime` 的題目會在後續章節用於診斷慢題。被標記為 `is_invalid` 的題目將在第二章至第六章的分析以及第七章建議觸發判斷中被過濾排除，以確保分析的準確性。

</aside>

---

# **第二章：多維度表現分析**

<aside>

**本章目標：** 使用過濾後的有效數據（排除 `is_invalid` 題目），從內容領域、題型和難度三個維度全面分析學生的表現。
**主要關注：** 計算並比較 `content_domain`（`Math Related` 和 `Non-Math Related`）的錯誤率和超時率；分析學生在四種 `question_type`（`DS`, `TPA`, `MSR`, `GT`）上的錯誤率和超時率；評估學生在不同 `question_difficulty` 難度等級上的表現。
**為何重要：** 本章旨在精準定位學生的能力短板，找出在哪些內容領域、題型或難度區間存在明顯的困難點（無論是準確率低還是效率不高），為後續的根本原因探究提供方向。

</aside>

- **分析維度：** 按 `content_domain` (`Math Related`/`Non-Math Related`), `question_type` (`DS`, `TPA`, `MSR`, `GT`), `question_difficulty` 難度。
- **計算指標：** 各維度下的題目總數、錯誤數 (`is_correct`==`False`)、超時數 (`overtime`==`True`)。計算錯誤率和超時率。
- **難度分級標準 (`question_difficulty`, 記作 `D`)：**
-   - 若 `D` ≤ -1: 難度等級 = "低難度 (Low) / 505+"
-   - 若 -1 < `D` ≤ 0: 難度等級 = "中難度 (Mid) / 555+"
-   - 若 0 < `D` ≤ 1: 難度等級 = "中難度 (Mid) / 605+"
-   - 若 1 < `D` ≤ 1.5: 難度等級 = "中難度 (Mid) / 655+"
-   - 若 1.5 < `D` ≤ 1.95: 難度等級 = "高難度 (High) / 705+"
-   - 若 1.95 < `D` ≤ 2: 難度等級 = "高難度 (High) / 805+"
- **顯著差異判斷 (僅限 `content_domain`)：**
    - 計算各 `content_domain` 的錯誤數 (`num_errors`) 和超時數 (`num_overtime`)。例如 `num_math_errors`, `num_nonmath_errors`, `num_math_overtime`, `num_nonmath_overtime`。
    - 若 `abs`(`num_math_errors` - `num_nonmath_errors`) >= 2，則認為錯誤率存在顯著差異。
    - 若 `abs`(`num_math_overtime` - `num_nonmath_overtime`) >= 2，則認為超時率存在顯著差異。
    - **標記：** 根據差異方向產生標籤，如 `poor_math_related`, `slow_non_math_related` 等。

<aside>

**本章總結：** 我們基於有效數據，分析了學生在不同 `content_domain`（`Math Related`/`Non-Math Related`）、`question_type`（`DS`, `TPA`, `MSR`, `GT`）和 `question_difficulty` 等級上的錯誤率與超時率。判斷了內容領域之間是否存在顯著表現差異，並產生了相應標籤。

**結果去向：** 分析結果（如錯誤/超時集中的領域、題型、難度）為第三章的診斷提供了背景信息（例如判斷 `special_focus_error`），並直接影響第六章練習建議的生成（如通過豁免和側重規則調整建議）。內容領域差異標籤也將納入第七章總結報告。

</aside>

---

# **第三章：根本原因診斷與分析**

<aside>

**本章目標：** 結合時間表現（快、慢、正常）、準確性（對、錯）、題型、內容領域及難度信息，深入探究並診斷導致錯誤或低效表現的根本原因，輸出標準化**英文診斷標籤參數**。

**主要關注：** 運用系統性分析方法，對每種 `question_type` 和 `content_domain` 的組合，根據不同的時間-準確性分類（如慢而錯、正常時間做錯等），關聯可能的**英文診斷參數**，並設定相應的觸發行動。特別關注 `special_focus_error` (即 `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) 並標記。

**為何重要：** 只有找到問題的根源（是文字理解、數學概念、邏輯推理、圖表解讀、跨源整合還是計算等具體環節，並由**英文參數**標準化表示），才能制定最有效的改進策略。本章旨在將「哪裡錯」提升到「為什麼錯」的標準化表示。

</aside>

- **分析框架**
    - **前置計算:**
        - `average_time_per_type` (各 `question_type` 的平均時間)
        - `max_correct_difficulty_per_combination` (各 `question_type` + `content_domain` 組合下，`is_correct` == `True` 的題目中的最高 `question_difficulty`)
    - **核心概念定義:**
        - **時間表現分類 (`Time Performance`):**
            - 快 (`is_relatively_fast`): `question_time` < `average_time_per_type`[該題 `question_type`] * 0.75。
            - 慢 (`is_slow`): 該題被標記為 `overtime` = `True` (根據第一章的閾值判斷，對於 MSR 題目，基於 `msr_group_overtime` 或 `msr_individual_overtime` 的新定義)。
            - 正常時間 (`is_normal_time`): 非快也非慢。
        - **特殊關注錯誤 (`special_focus_error`)**:
            - *定義*: 錯誤題目 (`is_correct`==`False`) 的 `question_difficulty` < `max_correct_difficulty_per_combination`[該題 `question_type`, 該題 `content_domain`]。
            - *標記*: 若滿足條件，則標記 `special_focus_error` = `True`。
            - *優先處理方式*: 在第六章生成個案建議和第七章輸出診斷總結時，應將標記為 `special_focus_error` = `True` 的題目及其對應的診斷和建議**優先列出或特別標註**。
- **診斷流程與分析要點 (針對有效數據題目)**
    - **按 `question_type` 和 `content_domain` 組合進行分析:**

    - **數學相關考點參考列表:** `Rates`, `Ratio`, `Percent`, `Equalities`, `Inequalties`, `Algebra`, `Value`, `Order`, `Factor`, `Counting`, `Sets`, `Probabilities`, `Series`, `Statistics`。

    - **通用診斷行動邏輯 (適用於各分類下的診斷行動建議):**
        1. **回憶優先:** 首先請學生回憶卡關點、錯誤原因或效率瓶頸。
        2. **觸發二級證據 (若無法回憶/確認):**
            - *條件*: 無法清晰回憶具體考點、障礙類型，或需客觀數據佐證。
            - *建議行動*: 查看近期（考前 2-4 週）在該 `question_type` 和 `content_domain` 組合下的類似錯誤/超時題目記錄。若樣本足夠（例如 5-10 題以上），嘗試歸納常見的錯誤模式、障礙類型（如文字理解、數學考點、邏輯推理、圖表解讀）、或需識別的考點/子題型。若樣本不足，統計參考價值有限，則請同學在接下來的做題中注意收集，累積到足夠樣本後再進行分析。
        3. **觸發質化分析 (若仍困惑或需深入):**
            - *條件*: 學生對初步診斷結果感到困惑，或現有數據/回憶不足以鎖定根本原因。（特別適用於 `Non-Math Related` 相關的正常/快錯場景，或效率瓶頸不明顯時）。
            - *建議行動*: 鼓勵學生提供更詳細的信息，如 2-3 個解題思路範例（文字/口述錄音），以便進行更深入的個案分析。

- **A. Data Sufficiency (`DS`)**
        - **A.1. `Math Related`**
            - **慢而錯 (`is_slow` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` (細分：單詞 / 句構 / 領域特定術語)
                    - `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math - 公式導出障礙)
                    - `` `DI_CALCULATION_ERROR__MATH` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 遵循通用邏輯。若涉及公式/計算障礙且無法回憶，優先考慮二級證據。需學生**識別數學相關考點 (參考本章開頭列表)**。
            - **慢而對 (`is_slow` & `is_correct`==`True`):**
                - *效率瓶頸可能點 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` `` (Math)
                    - `` `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH` `` (Math)
                    - `` `DI_CALCULATION_DIFFICULTY__MATH` ``
                - *診斷行動*: 遵循通用邏輯。**不需**學生識別考點。
            - **正常時間做錯 (`is_normal_time` & `is_correct`==`False`) / 快而錯 (`is_relatively_fast` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math - 考點不熟或應用錯誤)
                    - `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (主要針對快而錯)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 遵循通用邏輯。需學生**識別數學相關考點 (參考本章開頭列表)**。
            - **快而對 (`is_relatively_fast` & `is_correct`==`True`):** 提醒避免粗心/被標記；若在後段則詢問是否倉促。
            - **正常時間做對 (`is_normal_time` & `is_correct`==`True`):** N/A
        - **A.2. `Non-Math Related**
            - **慢而錯 (`is_slow` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` (細分：單詞 / 句構 / 題意)
                    - `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math - 題目內在邏輯推理障礙)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 遵循通用邏輯。請學生回憶是文字理解問題還是邏輯判斷問題。
            - **慢而對 (`is_slow` & `is_correct`==`True`):**
                - *效率瓶頸可能點 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` `` (Non-Math)
                    - `` `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH` `` (Non-Math)
                - *診斷行動*: 遵循通用邏輯。
            - **正常時間做錯 (`is_normal_time` & `is_correct`==`False`) / 快而錯 (`is_relatively_fast` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` (文字理解疏漏/錯誤)
                    - `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math - 題目內在邏輯應用錯誤)
                    - `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (主要針對快而錯)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 遵循通用邏輯，此處**強烈建議觸發二級證據 + 質化分析**。
            - **快而對 (`is_relatively_fast` & `is_correct`==`True`):** 同 A.1 快而對。
            - **正常時間做對 (`is_normal_time` & `is_correct`==`True`):** N/A

    - **B. Two-Part Analysis (`TPA`)** (結構同 `DS`，應用通用診斷行動邏輯)
        - **B.1. `Math Related**
            - **慢而錯 / 慢而對 / 正常時間做錯 / 快而錯 / 快而對 / 正常時間做對**
                - *可能原因/效率瓶頸 (診斷參數)*: 參考 ``DS Math Related`` (`` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` ``, `` `DI_CONCEPT_APPLICATION_ERROR__MATH` ``, `` `DI_CALCULATION_ERROR__MATH` ``, `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` ``, `` `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH` ``, `` `DI_CALCULATION_DIFFICULTY__MATH` ``)。
                - *診斷行動*: 應用通用邏輯，根據情況要求識別考點 **(參考本章開頭列表)** 或分析效率瓶頸。
        - **B.2. `Non-Math Related**
            - **慢而錯 / 慢而對 / 正常時間做錯 / 快而錯 / 快而對 / 正常時間做對**
                - *可能原因/效率瓶頸 (診斷參數)*: 參考 ``DS Non-Math Related`` (`` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` ``, `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math), `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` ``, `` `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH` `` (Non-Math), `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (快錯時))。
                - *診斷行動*: 應用通用邏輯，強調在正常/快錯時進行質化分析。

    - **C. Graph & Table (`GT`)** (結構同 `DS`/`TPA`，應用通用診斷行動邏輯)
        - **C.1. `Math Related**
            - **慢而錯 / 慢而對 / 正常時間做錯 / 快而錯 / 快而對 / 正常時間做對**
                - *可能原因/效率瓶頸 (診斷參數)*: 
                    - `` `DI_GRAPH_INTERPRETATION_ERROR__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_ERROR__TABLE` ``
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` (題幹文字理解)
                    - `` `DI_DATA_EXTRACTION_ERROR` ``
                    - `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math - 計算相關概念/公式)
                    - `` `DI_CALCULATION_ERROR__MATH` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                    - `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE` `` (慢而對時主要考慮)
                    - `` `DI_CALCULATION_DIFFICULTY__MATH` `` (慢而對時主要考慮)
                    - `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (快錯時主要考慮)
                - *診斷行動*: 應用通用邏輯，要求識別數學考點 **(參考本章開頭列表)** 或圖表類型。
        - **C.2. `Non-Math Related**
            - **慢而錯 / 慢而對 / 正常時間做錯 / 快而錯 / 快而對 / 正常時間做對**
                - *可能原因/效率瓶頸 (診斷參數)*: 
                    - `` `DI_GRAPH_INTERPRETATION_ERROR__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_ERROR__TABLE` ``
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` (題幹文字理解)
                    - `` `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR` `` (信息提取/推斷錯誤)
                    - `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                    - `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE` `` (慢而對時主要考慮)
                    - `` `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH` `` (Non-Math) (慢而對時主要考慮)
                    - `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (快錯時主要考慮)
                - *診斷行動*: 應用通用邏輯，強調在正常/快錯時進行質化分析。

    - **D. Multi-Source Reasoning (`MSR`)** (結構同上，應用通用診斷行動邏輯)
        *注意：`MSR`的「慢 (`is_slow`)」指該題被標記為 `overtime` = `True` (根據第一章更新的定義，即題組超時或調整後單題超時)。診斷時需結合題組整體情況和單題表現。*

        - **獨立 `MSR` 時間檢查 (優先於慢快正常分類)：**
            - **閱讀時間檢查 (針對題組第一題):** 計算 `msr_reading_time` (定義見第零章)。若 `msr_reading_time` > `msr_reading_threshold` (1.5 分鐘)，觸發特定診斷參數 `` `DI_MSR_READING_COMPREHENSION_BARRIER` `` 並記錄診斷行動：「`MSR` 題組閱讀時間偏長。請學生回憶源資料吸收障礙是（單字、句構、領域、圖表、跨分頁整合資訊）」。若無法回憶，建議啟用二級證據。*(說明：過長的閱讀時間也可能導致第一題的 `adjusted_msr_time` 增加，從而可能使其被標記為 `msr_individual_overtime`，進而觸發 `overtime`。) *
    
            - *說明：* `DI_MSR_READING_COMPREHENSION_BARRIER` 檢查獨立進行，旨在捕捉特定的 `MSR` 閱讀效率問題。

        - **D.1. `Math Related**
            - **慢而錯 (`is_slow` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` ``
                    - `` `DI_GRAPH_INTERPRETATION_ERROR__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_ERROR__TABLE` ``
                    - `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math)
                    - `` `DI_CALCULATION_ERROR__MATH` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 應用通用邏輯，要求識別數學考點 **(參考本章開頭列表)**。
            - **慢而對 (`is_slow` & `is_correct`==`True`):**
                - *效率瓶頸可能點 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION` ``
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` `` (Math)
                    - `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE` ``
                    - `` `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH` `` (Math)
                    - `` `DI_CALCULATION_DIFFICULTY__MATH` ``
                - *診斷行動*: 應用通用邏輯，**不需**學生識別考點。
            - **正常時間做錯 (`is_normal_time` & `is_correct`==`False`) / 快而錯 (`is_relatively_fast` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (主要針對快而錯)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 應用通用邏輯，需學生**識別數學相關考點 (參考本章開頭列表)**。
            - **快而對 (`is_relatively_fast` & `is_correct`==`True`):** 同 A.1 快而對。
            - **正常時間做對 (`is_normal_time` & `is_correct`==`True`):** N/A
        - **D.2. `Non-Math Related**
            - **慢而錯 (`is_slow` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` ``
                    - `` `DI_GRAPH_INTERPRETATION_ERROR__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_ERROR__TABLE` ``
                    - `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math)
                    - `` `DI_QUESTION_TYPE_SPECIFIC_ERROR` `` (MSR Non-Math)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 應用通用邏輯，請學生回憶邏輯推斷障礙是否關聯 `main idea`, `supporting idea`, 或 `inference` 等 RC 子題型概念，或進行質化分析。
            - **慢而對 (`is_slow` & `is_correct`==`True`):**
                - *效率瓶頸可能點 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION` ``
                    - `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` `` (Non-Math)
                    - `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE` ``
                    - `` `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH` `` (Non-Math)
                - *診斷行動*: 應用通用邏輯，**不需**學生識別子題型概念。
            - **正常時間做錯 (`is_normal_time` & `is_correct`==`False`) / 快而錯 (`is_relatively_fast` & `is_correct`==`False`):**
                - *可能原因 (診斷參數)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` ``
                    - `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math)
                    - `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` (主要針對快而錯)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` (若 SFE 觸發)
                - *診斷行動*: 應用通用邏輯，此處**強烈建議觸發二級證據 + 質化分析**，分析是否與 `main idea`, `supporting idea`, `inference` 相關。
            - **快而對 (`is_relatively_fast` & `is_correct`==`True`):** 同 A.1 快而對。
            - **正常時間做對 (`is_normal_time` & `is_correct`==`True`):** N/A

<aside>

**本章總結：** 本章詳細分析了在不同題型和內容領域組合下，各種時間-準確性表現背後可能的根本原因，並將這些原因與標準化的**英文診斷參數**進行了映射。定義了 `special_focus_error` (`` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) 並強調其優先性。為每種情況設計了觸發行動，引導學生進行回憶或利用二級證據（含樣本量建議）、質化分析來確認具體障礙。

**結果去向：** 本章產生的**英文診斷參數**和 `special_focus_error` 標記是第六章生成針對性練習方法建議的核心依據。觸發的行動直接指導學生後續的反思和信息補充。診斷發現（由**英文參數**代表）將構成第七章總結報告的核心內容（**需通過附錄 A 轉譯為自然語言**）。

</aside>

---

# **第四章：特殊模式觀察**

<aside>

**本章目標：** 識別與答題行為模式相關的特殊情況，例如粗心大意或測驗初期不恰當的快速作答（使用過濾數據），生成相關的**英文診斷參數**。

**主要關注：** 計算整體「相對快且錯」的比例，用於評估潛在的粗心問題 (關聯 `` `BEHAVIOR_CARELESSNESS_ISSUE` ``)；檢查學生是否在測驗前期（前 1/3 題目）就出現作答過快（`question_time` < 1.0 分鐘）的情況 (關聯 `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``)。

**為何重要：** 粗心問題需要不同於知識或技能缺陷的糾正方法。測驗初期就匆忙作答則可能反映了不良的考試策略或心理狀態。

</aside>

1. **粗心率計算 (`carelessness_issue`)：**
    - 沿用第三章的 `is_relatively_fast` 定義。
    - `num_relatively_fast_total` = 過濾數據中 `is_relatively_fast` == `True` 的總數。
    - `num_relatively_fast_incorrect` = 過濾數據中 `is_relatively_fast` == `True` 且 `is_correct` == `False` 的總數。
    - `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total` (如果 `num_relatively_fast_total` > 0)。
    - 若 `fast_wrong_rate` > `threshold_fast_wrong_rate` (例如 0.25)，則設置診斷參數 `` `DI_BEHAVIOR__CARELESSNESS_ISSUE` `` 為 `True`，並記錄診斷行動：「提醒學生注意粗心問題，反思是否存在審題不清、計算馬虎、選項看錯等情況。」

2. **前期過快題目 (`early_rushing_flag_risk`)：**
    - 找出 `question_position` <= `total_number_of_questions` / 3 且 `question_time` < 1.0 分鐘的題目 (絕對標準)。
    - 記錄這些題目的 `question_position`, `question_type`, `content_domain`。
    - 若找到任何此類題目，則設置診斷參數 `` `DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK` `` 為 `True`，並記錄診斷行動：「提醒學生測驗前期存在作答過快情況，可能影響準確率或遺漏關鍵信息，建議調整開局節奏，注意 flag for review 議題。」

<aside>

**本章總結：** 本章定義了兩個關鍵的行為模式指標：整體粗心率 (`` `BEHAVIOR_CARELESSNESS_ISSUE` ``) 和前期過快風險 (`` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``)。通過計算相對快且錯的比例和檢查測驗初期題目用時，評估了這些行為模式是否存在。

**結果去向：** 本章產生的**英文行為參數**標記將被納入第七章的診斷總結中，用於提醒學生注意相關的行為模式問題，並輔助診斷行動的生成（例如，粗心問題需要特定的反思練習）。

</aside>

---

# **第五章：基礎表現評估 (豁免與覆蓋)**

## 基礎表現豁免規則 (Exemption Rule)

<aside>
**目標:** 識別學生已完全掌握且能在時間限制內高效完成的特定領域，避免生成不必要的練習建議。
</aside>

- **判斷層級:** 本規則作用於 **`question_type` + `content_domain` 的組合** 層級 (例如 "DS - Math Related", "TPA - Non-Math Related" 等)。
- **豁免條件計算 (Exemption Status Calculation):**
    - 對於每一個 `question_type` + `content_domain` 的組合：
        - 篩選出屬於該組合的所有**有效題目** (排除 `is_invalid` = `True` 的題目)。
        - **條件一 (準確性):** 所有這些有效題目的 `is_correct` 均必須為 `True`。
        - **條件二 (效率):** 所有這些有效題目的 `overtime` 標記 (根據第一章對應 `question_type` 的定義，包括 MSR 的雙重標準 - 如果已修改) 均必須為 `False`。
    - 若**同時滿足**條件一和條件二，則計算得出該 `question_type` + `content_domain` 組合的豁免狀態 `exemption_status[type, domain]` 為 `True`，否則為 `False`。
- **豁免規則的影響:**
    - 計算出的豁免狀態將**用於**第六章練習建議生成邏輯。被標記為豁免的組合將**跳過**所有練習建議。
    - 診斷總結（第七章）會提及這些被豁免的組合，以展示學生的強項。

---

## 基礎能力覆蓋規則 (Override Rule)

<aside>

**目標:** 檢查是否有某個 `question_type` **(無論是否被豁免)** 存在普遍且嚴重的困難。

</aside>

- **計算指標：** 計算每個 `question_type`（`DS`, `TPA`, `MSR`, `GT`）的整體錯誤率 (`error_rate_type`) 和超時率 (`overtime_rate_type`)。
- **觸發判斷 (`override_triggered`)：** 若某個 `question_type` 的 `error_rate_type` > 0.5 或 `overtime_rate_type` > 0.5，則標記 `override_triggered`[該 `question_type`] = `True`。
- **宏觀練習難度確定 (若觸發)：** 找出該 `question_type` 下所有 `is_correct` == `False` 或超時題目中的最低 `question_difficulty` 值 (`min_error_or_overtime_difficulty_per_type`)。根據第二章的難度映射規則，將此 `min_error_or_overtime_difficulty_per_type` 轉換為對應的難度標籤 (`Y_agg`)，用於宏觀建議。
- **設定宏觀限時 (`Z_agg`)：**
    - 找出觸發該題型覆蓋規則的所有題目。
    - 找到這些題目中最大的 `question_time`，記為 `max_time_triggering`。
    - 計算 `Z_agg` = `floor(max_time_triggering * 2) / 2` (向下取整到最近的 0.5 分鐘)。

<aside>

**本章總結：** 本章設定了一個題型層級的覆蓋規則。通過檢查每個 `question_type`（`DS`, `TPA`, `MSR`, `GT`）的整體錯誤率和超時率，判斷是否存在表現極差（錯誤率或超時率 > 50%）的情況。若存在，則觸發該題型的覆蓋標記 (`override_triggered`)，並確定用於宏觀建議的起始練習難度 (`Y_agg`) 和限時 (`Z_agg`)。

**結果去向：** `override_triggered` 標記直接影響第六章練習建議的生成邏輯。如果某題型觸發了覆蓋規則，第六章將生成針對該題型的宏觀、基礎性鞏固建議（使用 `Y_agg` 和 `Z_agg`），而不是基於該題型下個別錯題或超時題的個案建議。

</aside>

---

# **第六章：練習規劃與建議**

<aside>

**本章目標：** 基於診斷結果，生成具體、可操作的練習建議。

**主要關注：** 提供練習材料、方法、重點（難度、限時）和基礎能力訓練計劃。區分宏觀建議（針對整體表現差的題型）、聚合建議（針對特定領域下錯誤/超時的題目組），應用豁免規則（針對表現完美的題型）和領域側重規則。

**為何重要：** 將診斷轉化為行動。

</aside>

- *(註：本章的建議生成依賴於前續章節的分析結果...)*
- **練習建議生成邏輯 (`_generate_di_recommendations`)**
    - **函數定義:** ...
    - **前置計算:**
        - 初始化字典 `recommendations_by_type` ...
        - 初始化集合 `processed_override_types` ...
        - **計算豁免題型 (`exempted_types`):** ...
    - **生成宏觀建議 (來自第五章的 `override_results`):**
        - 遍歷 `override_results` 中的每個 `question_type`:\
            - 如果該 `question_type` 觸發了 `override_triggered`:\
                - ... (生成宏觀建議文本)
                - 將此宏觀建議添加到 `recommendations_by_type[question_type]`。
                - 將 `question_type` 添加到 `processed_override_types`。
    - **生成聚合建議 (來自第三章診斷出的問題題目):**
        - 選取觸發點: `df_trigger` = `df_diagnosed` 中 `is_correct` 為 `False` 或 `overtime` 為 `True` 的題目。
        - **按 `question_type` 和 `content_domain` 分組:** 將 `df_trigger` 中的題目進行分組。
        - **遍歷每個分組 (Group):** 對應一個特定的 `question_type` 和 `content_domain` 組合。
            - **檢查是否被宏觀建議覆蓋或豁免:** 
                - 如果該組的 `question_type` 在 `processed_override_types` 中，則 `continue` 跳過此組。
                - 如果 `exemption_status[question_type, content_domain]` 為 `True` (根據第五章計算)，則 `continue` 跳過此組。
            - **聚合信息:** 在該分組內聚合計算以下信息：
                - **聚合練習難度 (`Y`):** 基於組內所有觸發題目的 **最低** `question_difficulty` 分數，使用 `_grade_difficulty_di` 轉換為難度等級（統一6級標準）。
                - **聚合起始限時 (`Z`, 分鐘):** 對組內每個觸發題目，先計算其個案建議限時 `Z_individual`：
                    - 設定目標時間：根據題型設定（例如 DS 為 2.0 分鐘，TPA/GT 為 3.0 分鐘，MSR 單題為 1.5 分鐘）。
                    - 計算 `base_time`：若題目 `overtime` 為 `True`，則 `T - 0.5`，否則 `T`。
                    - 計算 `Z_raw`：將 `base_time` 向下取整到最近的 0.5 分鐘。
                    - 確保最低值：`Z_individual` = `max(Z_raw, target_time_minutes)`。
                    - 然後取這些計算結果中的 **最大值** 作為聚合建議的 `Z`。
                - **SFE 狀態 (`group_sfe`):** 如果組內 **任何** 題目觸發了 `is_sfe`（即 `special_focus_error` 為 `True`），則此聚合建議標記為 `group_sfe` = `True`。
                - **聚合診斷參數 (`aggregated_params`):** 收集組內所有觸發題目 unique 的 `diagnostic_params` 列表。
            - **構建聚合建議文本 (`rec_text`):**
                - `translated_params` = `_translate_di(aggregated_params)`。
                - `problem_desc` = "錯誤或超時"。
                - `sfe_prefix` = "**基礎掌握不穩** - " (如果 `group_sfe` 為 `True`) 或 ""。
                - `param_text` = "(問題點可能涉及: {翻譯後的參數列表})" 或 "(具體問題點需進一步分析)"。
                - `rec_text` = `"{sfe_prefix}針對 **{domain}** 領域的 **{question_type}** 題目 ({problem_desc}) {param_text}，建議練習 **{Y}** 難度題目，起始練習限時建議為 **{z_text}** (最終目標時間: {target_time_text})。"`
            - **添加超時警告:** 如果 `Z - target_time_minutes > 2.0`，追加警告。
            - 將包含 `type='case_aggregated'`, `text=rec_text` 及其他聚合元數據 (如 `is_sfe`, `domain`, `Y`, `Z`, `question_type`) 的字典添加到 `recommendations_by_type[question_type]`。
    - **最終組裝與領域側重規則應用:**
        - 初始化 `final_recommendations` = `[]`。
        - **添加豁免說明 (若存在):**
            - 遍歷所有 `question_type` + `content_domain` 組合：
                - 如果 `exemption_status[question_type, content_domain]` 為 `True`:
                    - `exempt_domain_zh` = ... (獲取 domain 中文名)
                    - `exempt_type_zh` = ... (獲取 type 中文名)
                    - `exempt_text` = f"**{exempt_domain_zh}** 領域的 **{exempt_type_zh}** 題目表現完美，已豁免練習建議。"
                    - 將包含 `type='exemption'`, `text=exempt_text`, `question_type=question_type`, `domain=content_domain` 的字典添加到 `final_recommendations`。
        - 遍歷 `recommendations_by_type` 中的每個 `question_type` 和對應的 `type_recs` 列表 (如果該 type 未被豁免):\
            - ... (排序：宏觀在前，聚合建議在後)
            - ... **應用領域側重規則:** 
                - 根據第二章的內容領域表現差異分析結果 (`poor_math_related`, `slow_non_math_related` 等標籤)。
                - 如果發現某個領域（Math Related 或 Non-Math Related）的表現明顯較差，將追加相應的 `focus_note` 到該領域相關的建議末尾。
                - 例如：「數學相關領域題目練習佔比建議增加」或「非數學相關領域題目推薦側重練習」。
            - 將處理後的 `type_recs` 添加到 `final_recommendations`。
    - **返回:** `final_recommendations` 列表 (包含豁免說明、宏觀建議、聚合建議)，確保標記為 `is_sfe` 的建議被優先排序。

<aside>

**本章總結：** 我們生成了一份結構化的練習建議列表。根據第五章的覆蓋規則，可能包含宏觀建議（針對需基礎鞏固的題型）。對於未被宏觀覆蓋且未觸發豁免規則（完美表現）的題型，我們會將錯誤或超時的題目按內容領域分組，為每個組生成一條**聚合建議**，指明該組的練習難度（基於組內最低難度）、起始限時（基於組內最高計算限時）、涉及的問題點（聚合診斷參數），並標註是否涉及基礎掌握不穩定（SFE）。對於表現完美的題型，則生成豁免說明。最後應用了基於 `content_domain` 的側重規則對建議進行了微調。

**結果去向：** 這份詳細的練習建議列表是最終學生診斷報告（第七章）的核心行動方案部分。

</aside>

---

# **第七章：診斷總結與後續行動**

<aside>

**本章目標：** ... (整合時間壓力評估、不同領域表現對比、核心診斷發現...、特殊行為模式、以及基於這些發現生成的個性化練習建議（**區分宏觀、聚合、豁免**）和後續行動方案。)

**為何重要：** ...

</aside>

... (1. 開篇總結, 2. 表現概覽, 3. 核心問題分析, 4. 特殊模式觀察)

**5. 詳細診斷說明 (基於第三、四章 - 輔助，供深入查看)**

*   (可選，提供一個詳細列表，展示**每個**錯誤或超時題目 (`is_correct`=False 或 `overtime`=True) 的具體診斷信息，方便學生/顧問追溯細節。列表將**按題型、內容領域、題號排序**。每條記錄包含：)
    *   **題號、題型 (中文)、領域 (中文)**
    *   **表現標籤:** 根據時間和正確性判斷，標註為「快錯」、「慢錯」、「正常時間 & 錯」或「慢對」。
    *   **診斷參數:** 列出該題觸發的所有英文診斷參數的**中文翻譯**，並按預定義的**類別** (如 SFE、閱讀/解讀、概念應用、邏輯推理、數據處理、MSR 特定、效率、行為) **分組**顯示。
*   (註：此列表基於 `_generate_di_summary_report` 函數的實現，旨在提供比核心問題分析更細緻的視角。)

**6. 練習建議 (基於第六章)**

*   (呈現第六章生成的具體練習建議。強調這些建議是基於識別出的問題點，並已應用宏觀覆蓋、**聚合**和完美表現豁免規則進行了個性化調整。)
*   (建議以三種形式呈現：
    * **豁免說明**：指出哪些 `question_type` + `content_domain` 組合表現完美，已豁免練習建議。
    * **宏觀建議**：針對整體表現不佳的題型 (`question_type`) 的系統性鞏固建議。
    * **聚合建議**：按 `question_type` + `content_domain` 組合聚合的具體練習建議，包含聚合練習難度 (Y) (取自該組合內所有觸發題目中的最低難度)、聚合起始限時 (Z) (取自該組合內所有觸發題目單獨計算建議限時的最大值) 及最終目標時間。)
*   (標記 `special_focus_error` (SFE) 的聚合建議會被優先顯示並特別標註為「**基礎掌握不穩** - 」)
*   (已應用領域側重規則：基於第二章發現的內容領域 (Math/Non-Math) 表現差異，對相關建議追加側重說明，如「數學相關領域題目練習佔比建議增加」)

**7. 後續行動指引**

*   ... (診斷理解確認, 質化分析建議, 二級證據參考建議)
*   **輔助工具與 AI 提示推薦建議:**
    *   *推薦邏輯：* 為了幫助您更有效地整理練習和針對性地解決問題，以下是一些可能適用的輔助工具和 AI 提示。系統會根據您觸發的診斷參數組合，推薦相關的資源。請根據您的具體診斷結果選用。
    *   *推薦列表 (基於診斷參數):*

        * **若診斷涉及閱讀理解、圖表或數據解讀錯誤:**
            * `` `DI_READING_COMPREHENSION_ERROR__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_ERROR__SYNTAX` ``, `` `DI_READING_COMPREHENSION_ERROR__LOGIC` ``, `` `DI_READING_COMPREHENSION_ERROR__DOMAIN` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Close_Reading_Coach.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` `` , `` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_GRAPH_INTERPRETATION_ERROR__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_ERROR__TABLE` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/04_problem_pattern.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_DATA_EXTRACTION_ERROR` `` (GT) →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR` `` (GT/MSR Non-Math) →
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `DI-related/03_msr_info_flow.md` `` (MSR)

        * **若診斷涉及數學概念、計算或邏輯錯誤:**
            * `` `DI_CONCEPT_APPLICATION_ERROR__MATH` `` (Math) →
                * **Tool:** `Dustin_GMAT_Textbook_Explainer.md`, `Dustin_GMAT_Q_Question_Classifier.md`
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/05_variant_questions.md` ``
            * `` `DI_LOGICAL_REASONING_ERROR__NON_MATH` `` (Non-Math) →
                * **Tool:** `Dustin_GMAT_DI_Non-math_DS_Simulator.md` (若為 DS), `Dustin_GMAT_Textbook_Explainer.md`
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/02_quick_cr_tpa_tricks.md` `` , `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``
            * `` `DI_CALCULATION_ERROR__MATH` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/02_quick_math_tricks.md` ``

        * **若診斷涉及 MSR 特定問題:**
            * `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` `` →
                * **Tool:** `Dustin_GMAT_Chunk_Reading_Coach.md` (若整合慢因閱讀慢)
                * AI Prompt: `` `Verbal-related/04_mindmap_passage.md` ``, `` `Verbal-related/01_basic_explanation.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_MSR_READING_COMPREHENSION_BARRIER` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/01_basic_explanation.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``

        * **若診斷涉及特定題型或基礎掌握問題:**
            * `` `DI_QUESTION_TYPE_SPECIFIC_ERROR` `` →
                * **Tool:** `Dustin_GMAT_DI_Non-math_DS_Simulator.md` (若為 DS-NonMath)
                * AI Prompt: 根據具體題型選擇，如 `` `DI-related/02_quick_g&t_tricks.md` `` (GT), `` `DI-related/03_msr_info_flow.md` `` (MSR)。
            * `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE` `` →
                * **Tool:** `Dustin_GMAT_Textbook_Explainer.md`
                * AI Prompt: **優先** `` `Quant-related/01_basic_explanation.md` ``；輔助 `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/05_variant_questions.md` ``。

        * **若診斷涉及效率瓶頸:**
            * `` `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC` ``, `` `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Close_Reading_Coach.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH` `` (Math) →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Quant-related/04_problem_pattern.md` ``
            * `` `DI_CALCULATION_DIFFICULTY__MATH` `` →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``
            * `` `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH` `` (Non-Math) →
                * AI Prompt: `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH` ``, `` `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE` `` →
                * **Tool:** `GMAT_Terminator_DI_Review.md` (若課程涵蓋 GT)
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION` `` (MSR) →
                * **Tool:** `GMAT_Terminator_DI_Review.md` (若課程涵蓋 MSR), `Dustin_GMAT_Chunk_Reading_Coach.md` (若因閱讀慢)
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``

        * **若診斷涉及行為模式:** 
            * `` `DI_BEHAVIOR__CARELESSNESS_ISSUE` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK` `` →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``

        * **通用 DI 複習/練習:**
            * **Tool:** `GMAT_Terminator_DI_Review.md`
            * AI Prompt: `` `Quant-related/06_similar_questions.md` `` (數學相關), `` `Quant-related/05_variant_questions.md` `` (數學相關變體)
<aside>

**本章總結：** 本章旨在將前面各章的分析結果轉化為一份面向學生的、清晰易懂、可執行的診斷報告。報告結構包括：開篇總結、表現概覽、核心問題分析、特殊模式觀察、可選的詳細診斷列表（包含性能標籤、分類診斷參數、排序）、個性化的練習建議（區分宏觀、聚合、豁免），以及包含診斷確認、質化分析建議、二級證據建議和基於 **參數組合映射** 的輔助工具/AI 提示推薦的後續行動指引。

**結果去向：** ...

</aside>

---

# **附錄 A：診斷標籤參數與中文對照表**

## Data Insights (DI) 診斷標籤

### 時間表現: 快且錯 (`Fast & Wrong`)

* `DI_READING_COMPREHENSION_ERROR__VOCABULARY`: DI 閱讀理解錯誤: 詞彙理解
* `DI_READING_COMPREHENSION_ERROR__SYNTAX`: DI 閱讀理解錯誤: 句式理解
* `DI_READING_COMPREHENSION_ERROR__LOGIC`: DI 閱讀理解錯誤: 邏輯理解
* `DI_READING_COMPREHENSION_ERROR__DOMAIN`: DI 閱讀理解錯誤: 領域理解
* `DI_GRAPH_INTERPRETATION_ERROR__GRAPH`: DI 圖表解讀錯誤: 圖形信息解讀
* `DI_GRAPH_INTERPRETATION_ERROR__TABLE`: DI 圖表解讀錯誤: 表格信息解讀
* `DI_CONCEPT_APPLICATION_ERROR__MATH`: DI 概念應用 (數學) 錯誤: 數學觀念/公式應用
* `DI_LOGICAL_REASONING_ERROR__NON_MATH`: DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷
* `DI_CALCULATION_ERROR__MATH`: DI 計算錯誤 (數學): 數學計算
* `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`: DI 基礎掌握: 應用不穩定 (Special Focus Error)
* `DI_BEHAVIOR__CARELESSNESS_DETAIL_OMISSION`: DI 行為: 粗心 - 細節忽略/看錯
* `DI_BEHAVIOR__CARELESSNESS_ISSUE`: DI 行為: 粗心 - 整體快錯率偏高
* `DI_BEHAVIOR__EARLY_RUSHING_FLAG_RISK`: DI 行為: 測驗前期作答過快風險

### 時間表現: 正常時間且錯 (`Normal Time & Wrong`)

* `DI_READING_COMPREHENSION_ERROR__VOCABULARY`: DI 閱讀理解錯誤: 詞彙理解
* `DI_READING_COMPREHENSION_ERROR__SYNTAX`: DI 閱讀理解錯誤: 句式理解
* `DI_READING_COMPREHENSION_ERROR__LOGIC`: DI 閱讀理解錯誤: 邏輯理解
* `DI_READING_COMPREHENSION_ERROR__DOMAIN`: DI 閱讀理解錯誤: 領域理解
* `DI_GRAPH_INTERPRETATION_ERROR__GRAPH`: DI 圖表解讀錯誤: 圖形信息解讀
* `DI_GRAPH_INTERPRETATION_ERROR__TABLE`: DI 圖表解讀錯誤: 表格信息解讀
* `DI_CONCEPT_APPLICATION_ERROR__MATH`: DI 概念應用 (數學) 錯誤: 數學觀念/公式應用
* `DI_LOGICAL_REASONING_ERROR__NON_MATH`: DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷
* `DI_CALCULATION_ERROR__MATH`: DI 計算錯誤 (數學): 數學計算
* `DI_MULTI_SOURCE_INTEGRATION_ERROR`: DI 多源整合 (MSR): 跨分頁/來源信息整合障礙
* `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`: DI 基礎掌握: 應用不穩定 (Special Focus Error)

### 時間表現: 慢且錯 (`Slow & Wrong`)

* `DI_READING_COMPREHENSION_ERROR__VOCABULARY`: DI 閱讀理解錯誤: 詞彙理解
* `DI_READING_COMPREHENSION_ERROR__SYNTAX`: DI 閱讀理解錯誤: 句式理解
* `DI_READING_COMPREHENSION_ERROR__LOGIC`: DI 閱讀理解錯誤: 邏輯理解
* `DI_READING_COMPREHENSION_ERROR__DOMAIN`: DI 閱讀理解錯誤: 領域理解
* `DI_GRAPH_INTERPRETATION_ERROR__GRAPH`: DI 圖表解讀錯誤: 圖形信息解讀
* `DI_GRAPH_INTERPRETATION_ERROR__TABLE`: DI 圖表解讀錯誤: 表格信息解讀
* `DI_CONCEPT_APPLICATION_ERROR__MATH`: DI 概念應用 (數學) 錯誤: 數學觀念/公式應用
* `DI_LOGICAL_REASONING_ERROR__NON_MATH`: DI 邏輯推理 (非數學) 錯誤: 題目內在邏輯推理/判斷
* `DI_CALCULATION_ERROR__MATH`: DI 計算錯誤 (數學): 數學計算
* `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`: DI 閱讀理解障礙: 跨分頁/來源信息整合困難
* `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY`: DI 閱讀理解障礙: 詞彙理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX`: DI 閱讀理解障礙: 句式理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC`: DI 閱讀理解障礙: 邏輯理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN`: DI 閱讀理解障礙: 領域理解困難
* `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH`: DI 圖表解讀障礙: 圖形信息解讀困難
* `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE`: DI 圖表解讀障礙: 表格信息解讀困難
* `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH`: DI 概念應用 (數學) 障礙: 數學觀念/公式應用困難
* `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH`: DI 邏輯推理 (非數學) 障礙: 題目內在邏輯推理/判斷困難
* `DI_CALCULATION_DIFFICULTY__MATH`: DI 計算 (數學) 障礙: 數學計算困難
* `DI_FOUNDATIONAL_MASTERY_INSTABILITY__SFE`: DI 基礎掌握: 應用不穩定 (Special Focus Error)

### 時間表現: 慢且對 (`Slow & Correct`)

* `DI_READING_COMPREHENSION_DIFFICULTY__MULTI_SOURCE_INTEGRATION`: DI 閱讀理解障礙: 跨分頁/來源信息整合困難
* `DI_READING_COMPREHENSION_DIFFICULTY__VOCABULARY`: DI 閱讀理解障礙: 詞彙理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__SYNTAX`: DI 閱讀理解障礙: 句式理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__LOGIC`: DI 閱讀理解障礙: 邏輯理解困難
* `DI_READING_COMPREHENSION_DIFFICULTY__DOMAIN`: DI 閱讀理解障礙: 領域理解困難
* `DI_GRAPH_INTERPRETATION_DIFFICULTY__GRAPH`: DI 圖表解讀障礙: 圖形信息解讀困難
* `DI_GRAPH_INTERPRETATION_DIFFICULTY__TABLE`: DI 圖表解讀障礙: 表格信息解讀困難
* `DI_CONCEPT_APPLICATION_DIFFICULTY__MATH`: DI 概念應用 (數學) 障礙: 數學觀念/公式應用困難
* `DI_LOGICAL_REASONING_DIFFICULTY__NON_MATH`: DI 邏輯推理 (非數學) 障礙: 題目內在邏輯推理/判斷困難
* `DI_CALCULATION_DIFFICULTY__MATH`: DI 計算 (數學) 障礙: 數學計算困難

---

# **附錄 A：診斷標籤參數與中文對照表**

| 英文參數 (Parameter)                       | 中文描述 (Chinese Description)                         |
|--------------------------------------------|----------------------------------------------------|
| **DI - Reading & Understanding**           |                                                    |
| `DI_READING_COMPREHENSION_ERROR`           | DI 閱讀理解: 文字/題意理解錯誤/障礙 (Math/Non-Math) |
| `DI_GRAPH_TABLE_INTERPRETATION_ERROR`      | DI 圖表解讀: 圖形/表格信息解讀錯誤/障礙            |
| **DI - Concept & Application (Math)**      |                                                    |
| `DI_CONCEPT_APPLICATION_ERROR`             | DI 概念應用 (Math): 數學觀念/公式應用錯誤/障礙       |
| **DI - Logical Reasoning (Non-Math)**      |                                                    |
| `DI_LOGICAL_REASONING_ERROR`               | DI 邏輯推理 (Non-Math): 題目內在邏輯推理/判斷錯誤  |
| **DI - Data Handling & Calculation**       |                                                    |
| `DI_DATA_EXTRACTION_ERROR`                 | DI 數據提取 (GT): 從圖表中提取數據錯誤             |
| `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR`| DI 信息提取/推斷 (GT/MSR Non-Math): 信息定位/推斷錯誤 |
| `DI_CALCULATION_ERROR`                     | DI 計算: 數學計算錯誤/障礙                         |
| **DI - MSR Specific**                      |                                                    |
| `DI_MULTI_SOURCE_INTEGRATION_ERROR`        | DI 多源整合 (MSR): 跨分頁/來源信息整合錯誤/障礙    |
| `DI_MSR_READING_COMPREHENSION_BARRIER`     | DI MSR 閱讀障礙: 題組整體閱讀時間過長              |
| **DI - Question Type Specific**            |                                                    |
| `DI_QUESTION_TYPE_SPECIFIC_ERROR`          | DI 特定題型障礙 (例如 MSR Non-Math 子題型)         |
| **DI - Foundational & Efficiency**         |                                                    |
| `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`  | DI 基礎掌握: 應用不穩定 (Special Focus Error)      |
| `DI_EFFICIENCY_BOTTLENECK_READING`         | DI 效率瓶頸: 閱讀理解耗時 (Math/Non-Math)          |
| `DI_EFFICIENCY_BOTTLENECK_CONCEPT`         | DI 效率瓶頸: 概念/公式應用耗時 (Math)              |
| `DI_EFFICIENCY_BOTTLENECK_CALCULATION`     | DI 效率瓶頸: 計算耗時                              |
| `DI_EFFICIENCY_BOTTLENECK_LOGIC`           | DI 效率瓶頸: 邏輯推理耗時 (Non-Math)             |
| `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE`     | DI 效率瓶頸: 圖表解讀耗時                          |
| `DI_EFFICIENCY_BOTTLENECK_INTEGRATION`     | DI 效率瓶頸: 多源信息整合耗時 (MSR)              |
| **DI - Behavior**                          |                                                    |
| `DI_CARELESSNESS_DETAIL_OMISSION`          | DI 行為: 粗心 - 細節忽略/看錯 (快錯時隱含)         |
| **行為模式 (Behavioral Patterns)**       |                                                    |
| `BEHAVIOR_CARELESSNESS_ISSUE`         | 行為模式: 粗心 - 整體快錯率偏高 (fast_wrong_rate > 25%) |
| `BEHAVIOR_EARLY_RUSHING_FLAG_RISK`    | 行為模式: 測驗前期作答過快風險 (< 1.0 min, 注意 flag for review) |



（本文件結束）