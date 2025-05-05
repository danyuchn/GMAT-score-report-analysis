# **第零章：核心輸入數據與設定**

- 每題數據： `question_position` (題目位置，必需，作為唯一識別符), `question_time` (作答時間/分鐘), `is_correct` (是否正確/布林值), `question_type` ('Real' / 'Pure'), `question_difficulty` (難度值), `question_fundamental_skill` (核心技能)。
    - **核心技能 (`question_fundamental_skill`) 分類列表:**
        - `Rates/Ratio/Percent`
        - `Value/Order/Factor`
        - `Equal/Unequal/ALG` (Equations/Inequalities/Algebra)
        - `Counting/Sets/Series/Prob/Stats` (Counting/Sets/Series/Probability/Statistics)
- 整體數據： `total_test_time` (總作答時間/分鐘), `max_allowed_time` (測驗上限時間，固定為 45 分鐘), `total_number_of_questions` (總題數)。

---

# **第一章：整體時間策略與數據有效性評估**

<aside>

**本章目標：** 評估學生在整個測驗過程中的作答節奏和時間利用情況。
**主要關注：** 比較學生的總作答時間與測驗限制時間（45分鐘），並檢查測驗末尾是否有作答過快的題目。
**為何重要：** 這有助於判斷學生是否感到時間壓力過大，或者是否有充足時間。同時，找出可能因時間不足而猜測的題目，確保後續分析的準確性。

</aside>

1. **計算總時間差 (`time_diff`)**: 
   `time_diff` = `max_allowed_time` - `total_test_time`

2. **判斷時間壓力狀態 (`time_pressure`)**: 
   - 預設 `time_pressure` = `False`。
   - 檢查測驗末尾情況：找出測驗最後 1/3 的題目 (`last_third_questions`) 中 `question_time` < 1.0 分鐘的題目 (`fast_end_questions`)。
   - 判斷邏輯：如果 `time_diff` <= 3 分鐘 **且** `fast_end_questions` 不為空，則設定 `time_pressure` = `True`。
   - **用戶覆蓋：** 若用戶明確指出壓力不大，則強制設定 `time_pressure` = `False`。

3. **設定超時閾值 (`overtime_threshold`)**: 
   - 若 `time_pressure` == `True`，則 `overtime_threshold` = 2.5 分鐘。
   - 若 `time_pressure` == `False`，則 `overtime_threshold` = 3.0 分鐘。
   - *說明：此閾值用於後續分析中標識單題作答時間 (`question_time`) 是否超時 (`overtime` = `True`)。*

4. **識別無效數據 (`is_invalid`)**: 
   - 初始化 `invalid_question_positions` = `[]`。
   - 標記邏輯：如果 `time_pressure` == `True` （根據第 2 步判斷得出），則將 `fast_end_questions` （即最後 1/3 中 `question_time` < 1.0 分鐘的題目）的 `question_position` 加入 `invalid_question_positions` 列表，並為這些題目內部標記 `is_invalid` = `True`。
   - *說明：只有在確定存在時間壓力時，末尾的快速作答才被視為無效數據。*

5. **輸出與總結**: 
   - 本章產生的關鍵標記：`time_pressure` (布林值), `overtime_threshold` (數值), `invalid_question_positions` (列表), 以及題目上的 `is_invalid` 標記。

**全局規則應用：識別無效數據與過濾**

1.  **創建過濾數據集：** 從原始題目數據中，移除 所有 `question_position` 包含在 `invalid_question_positions` 列表中的題目。
2.  **後續分析範圍：** 第二章至第七章的所有計算、分析和建議，僅基於這個過濾後的數據集。**在過濾完成後，將根據 `overtime_threshold` 在剩餘的有效題目上標記 `overtime` 狀態。**

<aside>

**本章總結：** 我們首先計算了總時間差 (`time_diff`)，然後結合時間差和測驗末尾的作答速度判斷了學生是否處於時間壓力 (`time_pressure`) 下。基於時間壓力狀態，我們設定了統一的單題超時閾值 (`overtime_threshold`)。最後，僅在確認存在時間壓力的情況下，我們將測驗末尾作答過快的題目識別為無效數據 (`is_invalid`) 並記錄其位置 (`invalid_question_positions`)。**在進行後續分析前，我們會先過濾掉這些無效數據，然後再在剩餘的有效題目上根據 `overtime_threshold` 標記超時題目 (`overtime`)。**

**結果去向：** `time_pressure` 狀態和 `overtime_threshold` 將作為後續分析的重要背景信息。過濾後的數據集是後續所有章節分析的基礎。被標記為 `overtime` 的題目會在後續章節用於診斷慢題。被標記為 `is_invalid` 的題目已在分析開始前被排除。

</aside>

---

**全局規則應用：數據過濾**

1. 創建過濾數據集： 從原始題目數據中，移除 所有 `question_position` 包含在 `invalid_question_positions` 列表中的題目。
2. 後續分析範圍： 第二章至第七章的所有計算、分析和建議，僅基於這個過濾後的數據集。（註：標識題目是否 `overtime` 的步驟應在此數據過濾後，根據第一章確定的 `overtime_threshold` 進行。）

<aside>

**重要步驟：數據清理**

**目標：**確保我們的分析基於能夠真實反映學生能力的數據。

**執行：**我們將從數據中移除在第一章中被標識為「無效」 (`is_invalid`) 的題目。

**原因：**分析無效數據無法準確評估學生的知識掌握情況或學習困難點。之後所有的分析（第二至七章）都將使用這份清理、過濾後的數據。

</aside>

---

# **第二章：多維度表現分析**

<aside>

**本章目標：**比較學生在「Real 題」（應用題、文字題）和「Pure 題」（純計算、概念題）這兩種題型上的表現。

**主要關注：**使用過濾後的數據，分析學生在哪種題型上更容易出錯（錯誤率）或花費過多時間（超時率）。

**為何重要：**這有助於初步判斷學生的困難點是偏向閱讀理解、問題轉化（影響 `Real` 題），還是偏向數學核心概念、計算能力（影響 `Pure` 題）。

</aside>

1. **難度分級標準 (`question_difficulty`, 記作 `D`)：**
    - 若 `D` ≤ -1: 難度等級 = "低難度 (Low) / 505+"
    - 若 -1 < `D` ≤ 0: 難度等級 = "中難度 (Mid) / 555+"
    - 若 0 < `D` ≤ 1: 難度等級 = "中難度 (Mid) / 605+"
    - 若 1 < `D` ≤ 1.5: 難度等級 = "中難度 (Mid) / 655+"
    - 若 1.5 < `D` ≤ 1.95: 難度等級 = "高難度 (High) / 705+"
    - 若 1.95 < `D` ≤ 2: 難度等級 = "高難度 (High) / 805+"
2. **計數 (基於過濾數據)：**
    - `num_total_real`, `num_total_pure` (`Real` 題與 `Pure` 題的總數)
    - `num_real_errors`, `num_pure_errors` (`Real` 題與 `Pure` 題的錯誤數)
    - `num_real_overtime` (`Real` 題中 `overtime` == `True` 的題目數)
    - `num_pure_overtime` (`Pure` 題中 `overtime` == `True` 的題目數)
3. **計算率值 (處理分母為零)：**
    - `wrong_rate_real` = `num_real_errors` / `num_total_real`
    - `wrong_rate_pure` = `num_pure_errors` / `num_total_pure`
    - `over_time_rate_real` = `num_real_overtime` / `num_total_real`
    - `over_time_rate_pure` = `num_pure_overtime` / `num_total_pure`
4. **判斷顯著差異與標記：**
    - 若 `abs`(`num_real_errors` - `num_pure_errors`) >= 2 或 `abs`(`num_real_overtime` - `num_pure_overtime`) >= 2，則認為 `Real` 題與 `Pure` 題之間在錯誤或耗時方面存在顯著差異。
    - 根據差異顯著性及方向，標記相應的標籤：
        - 若 `Real` 題錯誤率顯著較高，標記 `poor_real` = `True`。
        - 若 `Pure` 題錯誤率顯著較高，標記 `poor_pure` = `True`。
        - 若 `Real` 題超時率顯著較高，標記 `slow_real` = `True`。
        - 若 `Pure` 題超時率顯著較高，標記 `slow_pure` = `True`。
5. **初步診斷 (基於標記)：**
    - 若產生 `'poor_real'` 或 `'slow_real'` 標籤（尤其 `'slow_real'`），初步診斷可能與閱讀速度過慢有關。
    - 若產生 `'poor_real'` 標籤，也可能與閱讀理解障礙有關。
    - 若產生 `'poor_pure'` 或 `'slow_pure'` 標籤，後續分析將更關注 `Pure` 題背後關聯的 `question_fundamental_skill`。
    - (註：本章定義的 `poor_real` 和 `slow_pure` 標籤將在第七章中用於調整相應技能的練習建議。)

<aside>

**本章總結：**我們判斷了學生在 `Real` 題和 `Pure` 題的表現是否存在顯著差異，並產生了相應標籤，如 `poor_real` (Real 題錯誤多)、`slow_pure` (Pure 題常超時) 等。

**結果去向：**這些標籤提供了初步的診斷方向。例如，`poor_real` 可能提示我們在後續步驟中更關注與閱讀相關的問題。這些標籤也會在第七章中直接用於調整最終的練習建議。

</aside>

---

# **第三章：根本原因診斷與分析**

<aside>

**本章目標：**深入探究學生答錯的題目（使用過濾數據）。
**主要關注：**根據學生在錯題上花費的時間長短，以及題目相對於該生能力的難易程度，對錯誤進行分類，並生成標準化**英文診斷標籤參數**。
**為何重要：**旨在理解錯誤的*性質*。是粗心大意（快而錯）？是花了時間但仍無法掌握（慢而錯）？還是在相對簡單的題目上意外失誤（觸發 `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``）？

</aside>

1. **計算前置數據 (基於過濾數據)：**
    - `average_time_per_type`['Real']`, `average_time_per_type`['Pure']` (各題型平均作答時間)
    - `max_correct_difficulty_per_skill`[`skill`] (每個 `question_fundamental_skill` 下 `is_correct` == `True` 的題目中的最高 `question_difficulty`)
2. **分析錯誤題 (遍歷過濾數據中 `is_correct` == `False` 的題目)：**
    - 對每道錯誤題：
        - **檢查是否特殊關注錯誤 (`special_focus_error`)**: 判斷該錯誤題目的 `question_difficulty` 是否低於其對應 `question_fundamental_skill` 的 `max_correct_difficulty_per_skill`[`skill`]。若是，則標記 `special_focus_error` = `True`，並關聯診斷參數 `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``。
        - **`special_focus_error` / `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 優先處理方式**: 在第七章生成練習建議和第八章輸出診斷總結時，應將標記為 `special_focus_error` = `True` 的題目及其對應的診斷參數 `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 和建議**優先列出或特別標註** (例如，在列表中置頂並加註「*基礎掌握不穩*」)。
        - **分類錯誤類型並記錄可能原因：**
            - **時間表現分類 (`Time Performance`):**
                - 快 (`is_relatively_fast`): `question_time` < `average_time_per_type`[該題 `question_type`] * 0.75。
                - 慢 (`is_slow`): 題目 `overtime` == `True` (第一章標記)。
                - 正常時間 (`is_normal_time`): 非快也非慢。
            - **診斷場景分析：**
                - **快而錯 (`Fast & Wrong`):** (`is_relatively_fast` == `True` 且 `is_correct` == `False`)
                    - *可能原因 (診斷參數)*:
                        - `` `Q_CARELESSNESS_DETAIL_OMISSION` ``
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (若 `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_PROBLEM_UNDERSTANDING_ERROR` ``
                    - *主要診斷行動*: 
                        1. *回憶*: 請學生回憶卡關點或錯誤原因。
                        2. *觸發二級證據*: 若無法清晰回憶，建議查看近期在該 `question_fundamental_skill` 及相關題型下的快錯題目記錄，歸納錯誤模式。
                - **慢而錯 (`Slow & Wrong`):** (`is_slow` == `True` 且 `is_correct` == `False`)
                    - *可能原因 (診斷參數)*:
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (若 `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_CALCULATION_ERROR` ``
                        - `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 `special_focus_error` == `True`)
                    - *主要診斷行動*: 
                        1. *回憶*: 請學生回憶卡關點，哪個環節耗時最長？
                        2. *觸發二級證據*: 若無法清晰回憶，建議查看近期在該 `question_fundamental_skill` 及相關題型下的慢錯題目記錄，歸納障礙類型。
                        3. *觸發質化分析*: 若對錯誤原因仍感困惑，建議提供 2-3 題解題流程範例。
                - **正常時間做錯 (`Normal Time & Wrong`):** (`is_normal_time` == `True` 且 `is_correct` == `False`)
                    - *可能原因 (診斷參數)*:
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (若 `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_PROBLEM_UNDERSTANDING_ERROR` ``
                        - `` `Q_CALCULATION_ERROR` `` (若涉及複雜計算)
                        - `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (若 `special_focus_error` == `True`)
                    - *主要診斷行動*: 
                        1. *回憶*: 請學生回憶錯誤原因。
                        2. *觸發二級證據*: 若無法清晰回憶，建議查看近期在該 `question_fundamental_skill` 及相關題型下的正常時間做錯題目記錄，歸納錯誤模式。
                        3. *觸發質化分析*: 若對錯誤原因仍感困惑，建議提供 2-3 題解題流程範例。

<aside>

**本章總結：** 我們分析了所有錯誤題目，根據其作答時間（快/慢/正常）進行分類。引入了診斷參數 `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 對應 `special_focus_error` 並明確了其優先處理方式。針對不同錯誤類型，列出了可能的**英文診斷參數**（如 `` `Q_CARELESSNESS_DETAIL_OMISSION` ``, `` `Q_CONCEPT_APPLICATION_ERROR` `` 等）。同時，為無法清晰回憶錯誤原因的情況，提供了二級證據和質化分析的建議路徑。

**結果去向：** 這些錯誤分類、診斷參數以及 `special_focus_error` / `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` 標記是後續生成具體練習建議（第七章）的關鍵依據。二級證據和質化分析的建議旨在幫助學生更深入地理解問題根源。第八章的總結報告將引用這些參數（並通過附錄翻譯）。

</aside>

---

# **第四章：正確題目時間分析 (使用過濾數據)**

<aside>

**本章目標：**檢查學生雖然答對了、但花費時間超過預期的題目（使用過濾數據）。

**主要關注：**找出那些被標記為 `is_correct` = `True`（答對）同時又 `overtime` = `True`（超時）的題目，並關聯可能的**英文診斷參數**。

**為何重要：**即便答對，耗時過長也可能反映問題。這可能意味著學生在解題時猶豫不決、知識點提取困難、計算反覆檢查修改，或是（對 `Real` 題而言）閱讀理解耗時，對應著不同的效率瓶頸。

</aside>

1. **篩選題目：** 找出過濾數據中 `is_correct` = `True` 且 `overtime` = `True` 的題目 (即作答正確但用時超過 `overtime_threshold` 的題目)。
2. **記錄與推測 (關聯診斷參數)：**
    - 記錄這些題目的 `question_position`, `question_type`, `question_fundamental_skill`, `question_time`。
    - 可能原因 (診斷參數):
        - `` `Q_EFFICIENCY_BOTTLENECK_READING` `` (若 `question_type` == 'Real')
        - `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``
        - `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` ``

<aside>

**本章總結：**我們識別出了學生雖然做對了、但效率可能偏低的具體題目和對應的知識技能。記錄了這些「正確但超時」題目的詳細信息，並關聯了可能的**英文效率瓶頸參數** (如 `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``)。

**結果去向：**這些情況同樣會作為觸發點，連同其關聯的效率參數，用於在第七章生成練習建議，旨在提升學生在相關技能或題型上的解題流暢度和效率。第八章報告會總結效率問題。

</aside>

---

# **第五章：特殊模式觀察與粗心評估**

<aside>

**本章目標：**觀察學生作答行為是否與題目位置有關，並評估整體的答題速度習慣（使用過濾數據），生成相關的**英文診斷參數**。
**主要關注：**檢查學生是否在測驗前期就出現作答過快（`question_time` < 1.0 分鐘）的情況 (關聯 `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``)，並計算整體「相對快且錯」的比例 (關聯 `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` ``)。
**為何重要：**測驗初期就匆忙作答可能反映了不良的答題策略。如果快而錯的比例很高，則可能表明學生普遍存在粗心問題。

</aside>

1. **前期過快題目：**
   找出 `question_position` <= `total_number_of_questions` / 3 且 `question_time` < 1.0 分鐘的題目 (絕對標準)。
   記錄這些題目的 `question_position`, `question_type`, `question_fundamental_skill`，並關聯診斷參數 `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``。輸出風險提醒：「**注意 `flag for review` 議題**」。
1. **粗心率計算 (`carelessness_issue`)：**
    `num_relatively_fast_total` = 過濾數據中滿足第三章「快」定義 (`is_relatively_fast` == `True`) 的總數。
    `num_relatively_fast_incorrect` = 過濾數據中 `is_relatively_fast` == `True` 且 `is_correct` == `False` 的總數。
    `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total` (如果 `num_relatively_fast_total` > 0)。
    若 `fast_wrong_rate` > 0.25，則標記 `carelessness_issue` = `True`，關聯診斷參數 `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` ``，並在第八章總結報告中提醒學生可能存在粗心問題。

<aside>

**本章總結：**

我們檢查了測驗前期是否存在絕對過快 (`question_time` < 1.0 min) 的題目 (關聯參數 `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``)，並計算了基於相對時間標準的整體「快而錯」比率 (`fast_wrong_rate`)。若此比率 > 25%，則標記可能存在普遍的粗心問題 (關聯參數 `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` ``)。

**結果去向：** 診斷參數 `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` 和 `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` `` 將作為背景信息，納入最終的診斷報告（第八章），提醒學生注意可能的行為模式問題。

</aside>

---

# **第六章：基礎能力覆蓋規則**

<aside>

**本章目標：**檢查是否有某個數學知識技能對該學生來說存在普遍且嚴重的困難（使用過濾數據）。

**主要關注：**計算每個核心技能（`fundamental_skill`）的整體錯誤率和超時率。如果某個技能的這兩項指標之一非常高（例如 > 50%），則觸發特殊規則。

**為何重要：**如果學生在某個完整的技能領域都表現出極大困難，那麼針對該領域內個別難題的建議可能效果不佳，不如先回頭鞏固該技能的基礎。這一步是生成詳細建議前的一個「前置檢查」。

</aside>

1. **計算各技能表現率 (基於過濾數據)：**
    - 對每個 `fundamental_skill` (`S`)：
        - 計算 `num_total_skill`, `num_errors_skill`, `num_overtime_skill`。
        - 計算 `error_rate_skill`, `overtime_rate_skill`。
    - **判斷觸發 (`skill_override_triggered`)：** 若某技能 `S` 的 `error_rate_skill` > 0.5 或 `overtime_rate_skill` > 0.5：
        - 標記 `skill_override_triggered`[`S`] = `True`。
        - 找出技能 `S` 中錯誤或超時題目的最低難度 `min_diff_skill`。
        - 根據 `min_diff_skill` 確定宏觀練習難度 `Y_agg` (映射規則同第七章個案建議中的難度 `D` 到標籤 `Y` 的規則)。
        - 設定宏觀限時 `Z_agg` = 2.5 分鐘。

<aside>

**本章總結：**本章設定了一個覆蓋規則，通過檢查每個核心技能（`question_fundamental_skill`）的整體錯誤率和超時率，判斷是否存在表現極差（錯誤率或超時率 > 50%）的情況。若存在，則觸發該技能的覆蓋標記（`skill_override_triggered`），並確定用於宏觀建議的起始練習難度 (`Y_agg`) 和限時 (`Z_agg`)。

**結果去向：**該標記直接影響第七章的練習建議生成邏輯。如果某技能觸發了覆蓋規則，第七章將生成針對該技能的宏觀、基礎性鞏固建議（使用 `Y_agg` 作為起始難度，限時 `Z_agg`），而不是基於該技能下個別錯題或超時題的微觀建議。

</aside>

---

# **第七章：練習規劃與建議**

**本章目標：**基於前面所有步驟的分析結果，生成具體、可操作的練習建議。
**主要關注：**整合錯誤分析（第三章）、正確但超時分析（第四章）以及技能覆蓋檢查（第六章）的結果，為相關的知識技能創建具體（指定難度、限時）或宏觀的練習任務。同時，考慮整體題型表現（第二章）來微調建議，並應用豁免規則。
**為何重要：**這是將診斷結果轉化為實際改進方案的關鍵一步，旨在為學生提供針對其特定弱點的練習計劃。

1. **確定建議觸發點：** 找出所有帶有以下診斷標籤的題目：第三章定義的錯誤標籤 (如 `slow_wrong`, `fast_wrong`, `special_focus_error`) 或第四章定義的正確但超時 (即 `overtime` = `True` 且 `is_correct` = `True`) 的題目。以及第六章觸發 `skill_override_triggered` 的 `fundamental_skill`。
2. **生成與初步分類建議：**
    - 初始化一個字典 `recommendations_by_skill` = `{}`，用於按技能臨時存儲建議列表。
    - 初始化一個集合 `processed_override_skills` = `set()`，用於記錄已處理宏觀建議的技能。
    - **計算豁免技能:**
        - 初始化一個集合 `exempted_skills` = `set()`。
        - 對於每個 `fundamental_skill` (`S`):
            - 計算該技能下正確 (`is_correct`==`True`) 且未超時 (`overtime`==`False`) 的題目數量 `num_correct_not_overtime`。
            - 若 `num_correct_not_overtime` > 2，則將 `S` 添加到 `exempted_skills`。
    - 遍歷所有建議觸發點對應的題目 `X` (其核心技能為 `S`，難度為 `D`，原始用時為 `T`)：
        - **檢查豁免:** 如果技能 `S` 在 `exempted_skills` 中，則跳過此題目的個案建議生成。
        - **檢查宏觀建議 (針對技能 S):** 如果 `skill_override_triggered`[`S`] 為 `True` 且技能 `S` **未**在 `processed_override_skills` 中：
            - 生成宏觀建議 `G` = “針對 [`S`] 技能，由於整體表現有較大提升空間 (根據第六章分析)，建議全面鞏固基礎，可從 [`Y_agg`] 難度題目開始系統性練習，掌握核心方法，建議限時 [`Z_agg`] 分鐘。” (`Y_agg` 和 `Z_agg` 來自第六章)。
            - 將宏觀建議 `G` 添加到 `recommendations_by_skill`[`S`]。
            - 將技能 `S` 添加到 `processed_override_skills`。
        - **生成個案建議 (若技能 S 未觸發宏觀建議且未被豁免):**
            - **練習難度 (`Y`):** 根據題目 `X` 的難度 `D` 進行映射（**統一 6 級標準**）：
                - 若 `D` ≤ -1: `Y` = “低難度 (Low) / 505+”
                - 若 -1 < `D` ≤ 0: `Y` = “中難度 (Mid) / 555+”
                - 若 0 < `D` ≤ 1: `Y` = “中難度 (Mid) / 605+”
                - 若 1 < `D` ≤ 1.5: `Y` = “中難度 (Mid) / 655+”
                - 若 1.5 < `D` ≤ 1.95: `Y` = “高難度 (High) / 705+”
                - 若 1.95 < `D` ≤ 2: `Y` = “高難度 (High) / 805+”
            - **起始練習限時 (`Z`):** (**統一計算規則**)
                - 設定目標時間: `target_time` = 2.0 分鐘。
                - 計算 `base_time`: 若 `X` 的 `overtime` == `True` (即 `is_slow` == `True`) 則 `T` - 0.5，否則 `T`。
                - 計算 `Z_raw` = `floor`(`base_time` * 2) / 2 (向下取整到最近的 0.5)。
                - 確保最低值: `Z` = `max`(`Z_raw`, `target_time`)。
            - 添加個案建議 `C` 到 `recommendations_by_skill`[`Skill`]。
3. **整理與輸出建議列表：**
    - 初始化 `final_recommendations`。
    - **處理豁免技能:** 對於在 `exempted_skills` 中的每個技能 `S`，如果它**未**觸發宏觀建議，則添加一條豁免說明到 `final_recommendations`：「技能 [`S`] 表現穩定，可暫緩練習。」
    - **整理聚合建議:** 遍歷 `recommendations_by_skill` 字典。
        - 對於每個技能 `S` 及其建議列表 `skill_recs`:
            - 如果列表非空：
                - **應用第二章診斷調整 (側重規則):**
                    - 檢查第二章的 `poor_real` 標籤：若 `poor_real` = `True` 且觸發該技能建議的題目中至少包含一道 `'Real'` 型題目，則在技能 `S` 的建議文本末尾追加「**Real題比例建議佔總練習題量2/3。**」
                    - 檢查第二章的 `slow_pure` 標籤：若 `slow_pure` = `True` 且觸發該技能建議的題目中至少包含一道 `'Pure'` 型題目，則在技能 `S` 的建議文本末尾追加「**建議此考點練習題量增加。**」
                - 將整理好的技能 `S` 的建議（可能包含一條宏觀建議和/或多條個案建議，已應用側重規則）添加到 `final_recommendations`。
    - **最終輸出:** 輸出 `final_recommendations`，確保按技能聚合，優先顯示標註 `special_focus_error` 的建議，並包含豁免說明。

---

# **第八章：診斷總結與後續行動**

**本章目標：**將前面所有的分析發現匯總成一份全面、易於理解、使用自然語言撰寫的診斷報告，供學生和老師使用。
**主要關注：**整合學生的整體時間壓力狀況、關鍵分析結果、以及量身定製的練習建議，並提供後續行動指引。
**為何重要：**提供一個整體的視角，點明學生的主要優勢和待改進之處，並通過清晰的解釋和可行的步驟指導未來的學習。

**1. 開篇總結**

- (此處總結第一章的發現：學生在本輪測驗中是否感受到明顯的時間壓力？總體作答時間與規定時間相比如何？測驗末尾是否存在因時間壓力導致作答過快、可能影響數據有效性的跡象？)

**2. 表現概覽**

- (此處總結第二章的發現：比較學生在 `'Real'` 題和 `'Pure'` 題上的表現，在哪種類型上錯誤更多或耗時更長？是否存在顯著差異 (`poor_real`, `slow_pure` 等標籤)？錯誤主要集中在哪些難度區間？哪些核心數學技能 (`fundamental_skill`) 是相對弱項？)

**3. 核心問題診斷**

- (此處使用自然語言歸納第三、四章的主要發現：描述學生最常見的錯誤類型，例如，是傾向於快速作答但出錯（可能涉及粗心或流程簡化），還是花費了較長時間但仍無法解決（可能涉及概念不清或計算障礙）？是否存在雖然做對但耗時過長的情況，反映了哪些技能的應用效率有待提升？)
- (優先提及) (如果第三章發現存在 `special_focus_error`，在此處強調：『尤其需要注意的是，在一些已掌握技能範圍內的基礎或中等難度題目上出現了失誤，這表明在這些知識點的應用上可能存在穩定性問題。』)

**4. 模式觀察**

- (提及第五章發現) (如果學生在測驗前期作答過快，提示：『測驗開始階段的部分題目作答速度較快，建議注意保持穩定的答題節奏，避免潛在的 “`flag for review`” 風險。』)
- (提及第五章發現) (如果 `carelessness_issue` 被觸發，提示：『分析顯示，“快而錯” 的情況佔比較高，提示可能需要關注答題的仔細程度，減少粗心錯誤。』)

**5. 基礎鞏固提示**

- (提及第六章發現) (如果任何 `fundamental_skill` 觸發了 `skill_override_triggered`，明確指出：『對於 [`觸發覆蓋規則的技能列表`] 這些核心技能，由於整體表現顯示出較大的提升空間，建議優先進行系統性的基礎鞏固，而非僅針對個別錯題練習。』)

**6. 練習計劃呈現**

- (此處清晰、完整地列出第七章生成的所有練習建議)
- (包含豁免說明，例如：『技能 [`被豁免的技能名`] 表現穩定，可暫緩練習。』)
- (包含側重說明，例如：『針對 [`技能名`] 的練習，建議增加 `Real`/`Pure` 題的比例…』)
- (確保 `special_focus_error` 相關建議優先顯示或突出標註)

**7. 後續行動指引**

- **核心約束：** 本章節最終產出的所有文字**必須完全使用自然語言**，避免直接引用或透露分析過程中使用的任何內部參數名稱、診斷標籤或具體的數值閾值。
- **引導反思：** (根據診斷出的主要障礙類型提出問題)
    - 若主要與數學觀念/技能相關：『回想一下，在做錯的 [`某類型`或`技能`] 題目時，具體是卡在哪個數學知識點或公式上？是完全沒思路，還是知道方法但算錯了？』
    - 若主要與閱讀理解相關 (`Real` 題)：『對於做錯的文字題，是題目本身的陳述讀不懂，還是能讀懂但無法轉化成數學問題？是否存在特定主題或長句子的閱讀困難？』
- **二級證據參考建議：**
    - *觸發時機：* 當您無法準確回憶具體的錯誤原因、涉及的知識點，或需要更客觀的數據來確認問題模式時。
    - *建議行動：* 『為了更精確地定位您在 [`某技能`/`題型`] 上的具體困難點，建議您查看近期的練習記錄（例如考前 2-4 週），整理相關錯題，歸納是哪些知識點或題型反覆出現問題。如果樣本不足，請在接下來的做題中注意收集，累積到足夠樣本後再進行分析。』
- **質化分析建議：**
    - *觸發時機：* 當您對診斷報告指出的錯誤原因感到困惑，或者上述方法仍無法幫您釐清根本問題時。
    - *建議行動：* 『如果您對 [`某類問題`] 的錯誤原因仍感困惑，可以嘗試**提供 2-3 題該類型題目的詳細解題流程跟思路範例**（可以是文字記錄或口述錄音），以便與顧問進行更深入的個案分析，共同找到癥結所在。』

**本章總結：**我們生成了一份完全使用自然語言撰寫的最終診斷報告。報告首先總結了時間使用情況和整體表現概覽，接著深入分析了核心問題所在（特別指出了基礎掌握不穩的情況），納入了特殊的作答模式觀察，並提示了需要基礎鞏固的技能領域。報告的核心部分是呈現了詳細的、按技能分類的練習計劃（已應用豁免和側重規則）。最後，報告包含了一些引導性問題和關於如何利用二級證據、質化分析來促進自我反思和針對性改進的建議。
**結果去向：**這份報告是整個診斷流程的最終產出，用於與學生溝通，並指導他們後續的學習和練習。