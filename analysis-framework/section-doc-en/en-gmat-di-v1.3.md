# **Chapter 0: Core Input Data and Configuration**

<aside>

**Objective:** To define all core input data structures required for diagnostic analysis of the Data Insights (DI) section.
**Primary Focus:** Establishing basic settings (e.g., test time, number of questions), question type definitions, detailed data points per question (`question_id`, `question_time`, `is_correct`, `content_domain`, `question_type`, `question_difficulty`, `question_position`), overall test data, and derived data points requiring pre-processing or calculation (e.g., MSR reading time, average time per question type, highest mastered difficulty).
**Rationale:** The data defined in this chapter serves as the foundation for all subsequent analyses, calculations, and diagnoses. The completeness, accuracy, and consistency of this data directly impact the validity and reliability of the diagnostic results.

</aside>

- **Basic Settings:**
    - `Max Allowed Time`: 45 minutes
    - `Total Number of Questions`: 20
- **Question Type Abbreviations:**
    - `DS`: Data Sufficiency
    - `TPA`: Two-Part Analysis
    - `MSR`: Multi-Source Reasoning
    - `GT`: Graph & Table
- **Per-Question Data:**
    - `question_position` (Question Sequence Number, required, serves as unique identifier)
    - `question_time` (Response Time/minutes)
    - `is_correct` (Correctness: `True`/`False`)
    - `content_domain` (Content Domain: `Math Related`/`Non-Math Related`)
    - `question_type` (Question Type: `DS`, `TPA`, `MSR`, `GT`)
    - `msr_group_id` (MSR Group ID, required if `question_type` is `MSR`)
    - `Fundamental Skills` (**Tracking confirmed as NO**)
    - `question_difficulty` (Difficulty Value)
- **Overall Test Data:**
    - `Total Test Time` (Total Response Time/minutes)
    - `Max Allowed Time` (Maximum Allowed Test Time)
    - `Total Number of Questions` (Total Number of Questions)
- **DI Derived Data:**
    - **`MSR` Reading Time (`msr_reading_time`):** For each `MSR` group, calculate `msr_reading_time` = `question_time` of the first question in the group - (average `question_time` of all **other** questions in the group **excluding the first one**). This calculation is only valid if the group contains at least two questions, and the result is attached to the first question of the group. (*This data will be used in Chapter 1 for MSR single question overtime determination*)
    - **`MSR` Group Data Pre-calculation:**
        - `group_total_time`: Calculate the sum of `question_time` for all questions within each `MSR` group.
        - `num_q_in_group`: Calculate the number of questions included in each `MSR` group.
    - **`GT` Time Allocation:** No special distinction needed between chart reading and response time.
    - **Average Response Time per Question Type (`average_time_per_type`):** Based on **valid data (after filtering)**, calculate the average response time for each `question_type` (`DS`, `TPA`, `MSR`, `GT`). (*This data will be used in Chapter 3 to define `is_relatively_fast` and in Chapter 4 to calculate carelessness rate*)
    - **Average Time per Type in First Third (`first_third_average_time_per_type`):** For each `question_type` (`DS`, `TPA`, `MSR`, `GT`), calculate the average `question_time` of all questions where `question_position` <= (`Total Number of Questions` / 3). (*This data will be used in Chapter 1 for invalid data determination*)
    - **Highest Mastered Difficulty (`max_correct_difficulty_per_combination`):** For each combination of `question_type` and `content_domain`, record the highest `question_difficulty` value among all questions where `is_correct` == `True`.

<aside>

**Chapter Summary:** This chapter explicitly defines the standard format for input data necessary for DI diagnostics, including basic test parameters, detailed dimensional information for each question, and derived metrics prepared for subsequent analyses, such as `MSR` reading time, average time per question type, and combination-based highest mastered difficulty.

**Results Destination:** All data points and derived metrics defined in this chapter will serve as the basis for time pressure assessment, performance analysis, root cause investigation, pattern observation, and practice recommendation generation in the subsequent chapters.

</aside>

---

# **Chapter 1: Overall Time Strategy and Data Validity Assessment**

<aside>

**Objective:** To assess the student's overall perception of time pressure in the DI section, set overtime standards for question types, and identify potentially invalid data resulting from extreme time shortage or strategic skipping.
**Primary Focus:** Calculating the total time difference, determining the time pressure status (`time_pressure`), setting and marking overtime (`overtime`) thresholds and statuses for different question types (`question_type`) based on the pressure status, and identifying invalid data (`is_invalid`) at the end of the test based on response time.
**Rationale:** Accurately assessing time pressure helps understand the student's testing environment and set reasonable overtime standards. Identifying and excluding invalid data is crucial for ensuring the accuracy of subsequent analyses, avoiding incorrect diagnoses based on guessed data.

</aside>

1. **Calculate Total Time Difference (`time_diff`)**: 
   `time_diff` = `max_allowed_time` - `total_test_time`

2. **Determine Time Pressure Status (`time_pressure`)**: 
   - If `time_diff` <= 3 minutes, then `time_pressure` = `True`.
   - Otherwise, `time_pressure` = `False`.
   - *(User override rule can be applied here if needed)*

3. **Set Overtime Thresholds and Rules (Based on `time_pressure`)**: 
   - **`TPA` Overtime Threshold (`overtime_threshold_tpa`)**: 
       - If `time_pressure` == `True`: 3.0 minutes.
       - If `time_pressure` == `False`: 3.5 minutes.
   - **`GT` Overtime Threshold (`overtime_threshold_gt`)**: 
       - If `time_pressure` == `True`: 3.0 minutes.
       - If `time_pressure` == `False`: 3.5 minutes.
   - **`DS` Overtime Threshold (`overtime_threshold_ds`)**: 
       - If `time_pressure` == `True`: 2.0 minutes.
       - If `time_pressure` == `False`: 2.5 minutes.
   - **`MSR` Group Target Time Rule (`msr_group_target_time`)**: 
       - If `time_pressure` == `True`: 6.0 minutes.
       - If `time_pressure` == `False`: 7.0 minutes.
   - **`MSR` Single Question Analysis Related Thresholds**: 
       - `msr_reading_threshold`: 1.5 minutes (to determine if reading time is excessive).
       - `msr_single_q_threshold`: 1.5 minutes (to determine if single question response time is excessive).
   - *Note: The above thresholds and rules are used subsequently to determine if individual questions or groups are overtime (`overtime`, `msr_group_overtime`).*

4. **Identify Invalid Data (`is_invalid`)**: 
   - **Scope and Prerequisite:** Identify questions in the last 1/3 of the test (`last_third_questions`, i.e., `question_position` > `Total Number of Questions` * 2/3). **Only when `time_pressure` == `True`** proceed with the following invalid data flagging.
   - **Define "Abnormally Fast Response (`abnormally_fast_response`)" Criteria (meeting any one triggers):**
       - *Criterion 1 (Suspected Skip):* `question_time` < 0.5 minutes.
       - *Criterion 2 (Absolute Rush):* `question_time` < 1.0 minutes.
       - *Criterion 3 (Relative Rush - DS):* `question_time` < (`first_third_average_time_per_type`['DS'] * 0.5). (Uses data calculated in Chapter 0)
       - *Criterion 4 (Relative Rush - TPA):* `question_time` < (`first_third_average_time_per_type`['TPA'] * 0.5). (Uses data calculated in Chapter 0)
       - *Criterion 5 (Relative Rush - GT):* `question_time` < (`first_third_average_time_per_type`['GT'] * 0.5). (Uses data calculated in Chapter 0)
       - *Criterion 6 (Relative Rush - MSR Group):* The `group_total_time` of the MSR group the question belongs to < (`first_third_average_time_per_type`['MSR'] * `num_q_in_group` * 0.5). (This criterion applies to all questions in the group; uses pre-calculated `group_total_time`, `num_q_in_group`, and calculated `first_third_average_time_per_type`['MSR'] from Chapter 0)
   - **Flagging Logic:** Within the `last_third_questions` scope, if a question (or its MSR group for Criterion 6) meets **at least one** `abnormally_fast_response` criterion, **AND `time_pressure` == `True`**, then flag that question as `is_invalid` = `True`.
   - *Note:* This multi-criteria logic aims to more accurately identify potentially invalid response data in the latter part of the test due to skipping or excessive rushing under time pressure.

5. **Output and Summary**: 
   - Key outputs generated in this chapter: `time_pressure` (Boolean), overtime thresholds/rules per question type, `is_invalid` flag (applied to specific questions, and only when `time_pressure` is True).

**Global Rule Application: Data Filtering and Flagging**

1.  **Flag Overtime (`overtime`):** Based on the thresholds/rules defined in this chapter for each question type, add an `overtime` = `True` flag to all questions **not flagged as `is_invalid`**:
    *   If `question_type` == `'TPA'` and `question_time` > `overtime_threshold_tpa`, flag `overtime` = `True`.
    *   If `question_type` == `'GT'` and `question_time` > `overtime_threshold_gt`, flag `overtime` = `True`.
    *   If `question_type` == `'DS'` and `question_time` > `overtime_threshold_ds`, flag `overtime` = `True`.
    *   **Overtime Flagging for `MSR` Questions (Dual Criteria):**
        *   **a. Group Overtime Flag (`msr_group_overtime`):**
            *   Calculate the total time for each MSR group (`group_total_time`).
            *   Get the group's target time `msr_group_target_time` (based on `time_pressure`: 6.0 min if True, 7.0 min if False).
            *   Determine: If `group_total_time > msr_group_target_time`, then flag **all** questions within that MSR group with `msr_group_overtime = True`.
        *   **b. Individual Question Overtime Flag (`msr_individual_overtime`):**
            *   Set a fixed individual question threshold `msr_individual_q_threshold = 1.5` minutes (does not change with `time_pressure`).
            *   Calculate adjusted time `adjusted_msr_time`:
                *   For the first question in the group: `adjusted_msr_time = question_time - msr_reading_time` (uses `msr_reading_time` calculated in Chapter 0).
                *   For non-first questions in the group: `adjusted_msr_time = question_time`.
            *   Determine: If an MSR question's `adjusted_msr_time > msr_individual_q_threshold` (1.5 minutes), then flag that question with `msr_individual_overtime = True`.
        *   **c. Final `overtime` Flag:**
            *   An MSR question is finally flagged as `overtime = True` if and only if it satisfies `msr_group_overtime == True` **OR** `msr_individual_overtime == True`.
2.  **Create Filtered Dataset:** Remove all questions marked as `is_invalid` = `True` from the original dataset.
3.  **Scope of Subsequent Analysis:** All calculations, analyses, and recommendations from Chapter 2 through Chapter 6 will be based exclusively on this filtered dataset.

<aside>

**Chapter Summary:** This chapter first calculated the total time difference and determined the student's overall time pressure status (`time_pressure`). Based on this status, corresponding overtime thresholds or target time rules were established for different question types (`DS`, `TPA`, `GT`, `MSR`). Then, **only when time pressure was confirmed (`time_pressure` == `True`)**, potentially invalid data (`is_invalid`) was identified for questions in the last third of the test based on new multi-criteria standards (including absolute short time, relative short time compared to first-third averages, and MSR group overall short time) indicating "abnormally fast responses". Before subsequent analyses, overtime questions (`overtime`) are flagged according to the rules (including the updated dual criteria for MSR), and then the invalid data is filtered out.

**Results Destination:** The `time_pressure` status and the overtime settings for each question type serve as crucial context for subsequent analyses. Questions flagged as `overtime` will be used in later chapters to diagnose slow problem-solving. Questions flagged as `is_invalid` will be excluded from analyses in Chapters 2 through 6 and from trigger conditions for recommendations in Chapter 7 to ensure the accuracy and validity of the findings.

</aside>

---

# **Chapter 2: Multi-Dimensional Performance Analysis**

<aside>

**Objective:** To comprehensively analyze student performance across three dimensions—content domain, question type, and difficulty—using the filtered, valid data (excluding `is_invalid` questions).
**Primary Focus:** Calculating and comparing error rates and overtime rates for `content_domain` (`Math Related` and `Non-Math Related`); analyzing student performance on the four `question_type`s (`DS`, `TPA`, `MSR`, `GT`) in terms of error and overtime rates; evaluating performance across different `question_difficulty` levels.
**Rationale:** This chapter aims to pinpoint the student's weaknesses by identifying specific content domains, question types, or difficulty ranges where significant difficulties exist (either low accuracy or low efficiency), providing direction for subsequent root cause analysis.

</aside>

- **Analysis Dimensions:** By `content_domain` (`Math Related`/`Non-Math Related`), `question_type` (`DS`, `TPA`, `MSR`, `GT`), `question_difficulty`.
- **Calculated Metrics:** Total number of questions, number of errors (`is_correct`==`False`), number of overtime instances (`overtime`==`True`) for each dimension. Calculate error rates and overtime rates.
- **Difficulty Level Standardization (`question_difficulty`, denoted as `D`):**
    - If `D` ≤ -1: Difficulty Level = "Low / 505+"
    - If -1 < `D` ≤ 0: Difficulty Level = "Medium / 555+"
    - If 0 < `D` ≤ 1: Difficulty Level = "Medium / 605+"
    - If 1 < `D` ≤ 1.5: Difficulty Level = "Medium / 655+"
    - If 1.5 < `D` ≤ 1.95: Difficulty Level = "High / 705+"
    - If 1.95 < `D` ≤ 2: Difficulty Level = "High / 805+"
- **Determining Significant Differences (Limited to `content_domain`)**: 
    - Calculate the number of errors (`num_errors`) and overtime instances (`num_overtime`) for each `content_domain`. E.g., `num_math_errors`, `num_nonmath_errors`, `num_math_overtime`, `num_nonmath_overtime`.
    - If `abs`(`num_math_errors` - `num_nonmath_errors`) >= 2, a significant difference in error rates is considered to exist.
    - If `abs`(`num_math_overtime` - `num_nonmath_overtime`) >= 2, a significant difference in overtime rates is considered to exist.
    - **Flagging:** Apply flags based on the direction of the difference, e.g., `poor_math_related`, `slow_non_math_related`, etc.

<aside>

**Chapter Summary:** Based on valid data, this chapter analyzed the student's error and overtime rates across different `content_domain`s (`Math Related`/`Non-Math Related`), `question_type`s (`DS`, `TPA`, `MSR`, `GT`), and `question_difficulty` levels. It determined if significant performance differences exist between content domains and generated corresponding flags.

**Results Destination:** The analysis results (e.g., areas, types, difficulties with concentrated errors/overtime) provide background information for Chapter 3's diagnosis (like determining `special_focus_error`) and directly influence the generation of practice recommendations in Chapter 6 (e.g., adjusting suggestions via exemption and focus rules). Content domain difference flags will also be included in the Chapter 7 summary report.

</aside>

---

# **Chapter 3: Root Cause Diagnosis and Analysis**

<aside>

**Objective:** To delve deeper into and diagnose the root causes of errors or inefficiencies by combining time performance (fast, slow, normal), accuracy (correct, incorrect), question type, content domain, and difficulty information, outputting standardized **English diagnostic parameter tags**.
**Primary Focus:** Applying a systematic analysis method for each `question_type` and `content_domain` combination. Associating potential **English diagnostic parameters** with different time-accuracy classifications (e.g., slow and wrong, normal time but wrong) and setting corresponding diagnostic actions. Paying special attention to and flagging `special_focus_error` (i.e., `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``).
**Rationale:** Only by finding the root cause of the problem (whether it's textual understanding, mathematical concepts, logical reasoning, chart interpretation, cross-source integration, or calculation, represented by standardized **English parameters**) can the most effective improvement strategies be developed. This chapter aims to elevate the analysis from "where the error occurred" to a standardized representation of "why the error occurred."

</aside>

- **Analysis Framework**
    - **Prerequisite Calculations:**
        - `average_time_per_type` (Average time for each `question_type`)
        - `max_correct_difficulty_per_combination` (Highest `question_difficulty` among `is_correct` == `True` questions for each `question_type` + `content_domain` combination)
    - **Core Concept Definitions:**
        - **Time Performance Classification (`Time Performance`):**
            - Fast (`is_relatively_fast`): `question_time` < `average_time_per_type`[question's `question_type`] * 0.75.
            - Slow (`is_slow`): Question is flagged `overtime` = `True` (based on Chapter 1 thresholds, including the dual criteria for MSR).
            - Normal Time (`is_normal_time`): Neither fast nor slow.
        - **Special Focus Error (`special_focus_error`)**: (Definition and handling aligned with original DI logic)
            - *Definition*: An incorrect question (`is_correct`==`False`) whose `question_difficulty` < `max_correct_difficulty_per_combination`[question's `question_type`, question's `content_domain`].
            - *Flagging*: If the condition is met, flag `special_focus_error` = `True` and associate with parameter `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``.
            - *Priority Handling*: When generating individual recommendations (Chapter 6) and outputting the diagnostic summary (Chapter 7), questions flagged as `special_focus_error` = `True` (and their corresponding parameter `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) and related diagnoses/recommendations should be **listed first or specially highlighted**.
- **Diagnostic Process and Analysis Points (for valid data questions)**
    - **Analyze by `question_type` and `content_domain` combination:**

    - **(New) Math Related Topic Reference List:** `Rates`, `Ratio`, `Percent`, `Equalities`, `Inequalties`, `Algebra`, `Value`, `Order`, `Factor`, `Counting`, `Sets`, `Probabilities`, `Series`, `Statistics`.

    - **General Diagnostic Action Logic (Applicable to action suggestions under various classifications):**
        1. **Recall First:** Initially ask the student to recall the sticking point, reason for error, or efficiency bottleneck.
        2. **Trigger Secondary Evidence (If unable to recall/confirm):**
            - *Condition*: Cannot clearly recall the specific topic, barrier type, or needs objective data backup.
            - *Recommended Action*: Review recent (last 2-4 weeks) records of similar error/overtime questions for that `question_type` and `content_domain` combination. If the sample is sufficient (e.g., 5-10+ questions), try to identify common error patterns, barrier types (e.g., text comprehension, math topic, logical reasoning, chart interpretation), or specific topics/sub-types needing recognition. If the sample is insufficient, its statistical value is limited; advise the student to pay attention during future practice, accumulate enough samples, and then analyze.
        3. **Trigger Qualitative Analysis (If still confused or need deeper insight):**
            - *Condition*: Student is confused about the initial diagnosis, or existing data/recall is insufficient to pinpoint the root cause. (Especially applicable for `Non-Math Related` scenarios involving normal/fast errors, or when the efficiency bottleneck is unclear).
            - *Recommended Action*: Encourage the student to provide more detailed information, such as 2-3 examples of their problem-solving process (text/audio recording), for a more in-depth case analysis.

- **A. Data Sufficiency (`DS`)**
        - **A.1. `Math Related`**
            - **Slow & Wrong (`is_slow` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR` `` (Sub-classify: Vocabulary / Sentence Structure / Domain-Specific Terminology)
                    - `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math - Formula derivation barrier)
                    - `` `DI_CALCULATION_ERROR` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Follow general logic. If involving formula/calculation barriers and recall fails, prioritize secondary evidence. Requires student to **identify the Math related topic (refer to list at start of chapter)**.
            - **Slow & Correct (`is_slow` & `is_correct`==`True`):**
                - *Potential Efficiency Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_CONCEPT` `` (Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_CALCULATION` ``
                - *Diagnostic Actions*: Follow general logic. Student **does not** need to identify the topic.
            - **Normal Time & Wrong (`is_normal_time` & `is_correct`==`False`) / Fast & Wrong (`is_relatively_fast` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math - Unfamiliar topic or application error)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly for fast & wrong)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Follow general logic. Requires student to **identify the Math related topic (refer to list at start of chapter)**.
            - **Fast & Correct (`is_relatively_fast` & `is_correct`==`True`):** Remind to avoid carelessness/flagging; if late in section, ask if rushed.
            - **Normal Time & Correct (`is_normal_time` & `is_correct`==`True`):** N/A
        - **A.2. `Non-Math Related`**
            - **Slow & Wrong (`is_slow` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR` `` (Sub-classify: Vocabulary / Sentence Structure / Meaning)
                    - `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math - Internal logical reasoning barrier)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Follow general logic. Ask student to recall if it was a text comprehension or logical judgment issue.
            - **Slow & Correct (`is_slow` & `is_correct`==`True`):**
                - *Potential Efficiency Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Non-Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_LOGIC` `` (Non-Math)
                - *Diagnostic Actions*: Follow general logic.
            - **Normal Time & Wrong (`is_normal_time` & `is_correct`==`False`) / Fast & Wrong (`is_relatively_fast` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR` `` (Text comprehension omission/error)
                    - `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math - Internal logical application error)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly for fast & wrong)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Follow general logic, **strongly recommend triggering secondary evidence + qualitative analysis** here.
            - **Fast & Correct (`is_relatively_fast` & `is_correct`==`True`):** Same as A.1 Fast & Correct.
            - **Normal Time & Correct (`is_normal_time` & `is_correct`==`True`):** N/A

    - **B. Two-Part Analysis (`TPA`)** (Structure same as `DS`, apply general diagnostic action logic)
        - **B.1. `Math Related`**
            - **Slow&Wrong / Slow&Correct / NormalTime&Wrong / Fast&Wrong / Fast&Correct / NormalTime&Correct**
                - *Potential Causes/Bottlenecks (Diagnostic Parameters)*: Refer to ``DS Math Related`` (`` `DI_READING_COMPREHENSION_ERROR` ``, `` `DI_CONCEPT_APPLICATION_ERROR` ``, `` `DI_CALCULATION_ERROR` ``, `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``, `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Math), `` `DI_EFFICIENCY_BOTTLENECK_CONCEPT` `` (Math), `` `DI_EFFICIENCY_BOTTLENECK_CALCULATION` ``).
                - *Diagnostic Actions*: Apply general logic, require topic identification **(refer to list at start of chapter)** or bottleneck analysis as appropriate.
        - **B.2. `Non-Math Related`**
            - **Slow&Wrong / Slow&Correct / NormalTime&Wrong / Fast&Wrong / Fast&Correct / NormalTime&Correct**
                - *Potential Causes/Bottlenecks (Diagnostic Parameters)*: Refer to ``DS Non-Math Related`` (`` `DI_READING_COMPREHENSION_ERROR` ``, `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math), `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``, `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Non-Math), `` `DI_EFFICIENCY_BOTTLENECK_LOGIC` `` (Non-Math), `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (when fast & wrong)).
                - *Diagnostic Actions*: Apply general logic, emphasizing qualitative analysis for normal/fast errors.

    - **C. Graph & Table (`GT`)** (Structure same as `DS`/`TPA`, apply general diagnostic action logic)
        - **C.1. `Math Related`**
            - **Slow&Wrong / Slow&Correct / NormalTime&Wrong / Fast&Wrong / Fast&Correct / NormalTime&Correct**
                - *Potential Causes/Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_GRAPH_TABLE_INTERPRETATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR` `` (Question stem text comprehension)
                    - `` `DI_DATA_EXTRACTION_ERROR` ``
                    - `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math - Calculation-related concepts/formulas)
                    - `` `DI_CALCULATION_ERROR` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                    - `` `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE` `` (Mainly consider for slow & correct)
                    - `` `DI_EFFICIENCY_BOTTLENECK_CALCULATION` `` (Mainly consider for slow & correct)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly consider for fast & wrong)
                - *Diagnostic Actions*: Apply general logic, require Math topic **(refer to list at start of chapter)** or chart type identification.
        - **C.2. `Non-Math Related`**
            - **Slow&Wrong / Slow&Correct / NormalTime&Wrong / Fast&Wrong / Fast&Correct / NormalTime&Correct**
                - *Potential Causes/Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_GRAPH_TABLE_INTERPRETATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR` `` (Question stem text comprehension)
                    - `` `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR` `` (Information extraction/inference error)
                    - `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                    - `` `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE` `` (Mainly consider for slow & correct)
                    - `` `DI_EFFICIENCY_BOTTLENECK_LOGIC` `` (Non-Math) (Mainly consider for slow & correct)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly consider for fast & wrong)
                - *Diagnostic Actions*: Apply general logic, emphasizing qualitative analysis for normal/fast errors.

    - **D. Multi-Source Reasoning (`MSR`)** (Structure same as above, apply general diagnostic action logic)
        *Note: "Slow" for `MSR` usually refers to group overtime; diagnosis needs to consider the overall group situation and individual question performance.* 

        - **Independent `MSR` Time Checks (Priority over Slow/Fast/Normal classification):**
            - **Reading Time Check (for the first question of the group):** Calculate `msr_reading_time` (defined in Chapter 0). If `msr_reading_time` > `msr_reading_threshold` (1.5 minutes), trigger specific diagnostic parameter `` `DI_MSR_READING_COMPREHENSION_BARRIER` `` and record diagnostic action: "`MSR` group reading time is long. Ask student to recall source material absorption barrier (Vocabulary, Sentence structure, Domain, Chart, Cross-tab information integration)." Recommend secondary evidence if recall fails.
            - *Note:* This check is performed independently to capture specific `MSR` reading efficiency issues. Its triggered parameter and action are separate from the subsequent "Slow" classification but should be aggregated into the final report.

        - **D.1. `Math Related`**
            - **Slow & Wrong (`is_slow` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR` ``
                    - `` `DI_GRAPH_TABLE_INTERPRETATION_ERROR` ``
                    - `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math)
                    - `` `DI_CALCULATION_ERROR` ``
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Apply general logic, require Math topic identification **(refer to list at start of chapter)**.
            - **Slow & Correct (`is_slow` & `is_correct`==`True`):**
                - *Potential Efficiency Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_EFFICIENCY_BOTTLENECK_INTEGRATION` ``
                    - `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE` ``
                    - `` `DI_EFFICIENCY_BOTTLENECK_CONCEPT` `` (Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_CALCULATION` ``
                - *Diagnostic Actions*: Apply general logic. Student **does not** need to identify the topic.
            - **Normal Time & Wrong (`is_normal_time` & `is_correct`==`False`) / Fast & Wrong (`is_relatively_fast` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly for fast & wrong)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Apply general logic. Requires student to **identify the Math related topic (refer to list at start of chapter)**.
            - **Fast & Correct (`is_relatively_fast` & `is_correct`==`True`):** Same as A.1 Fast & Correct.
            - **Normal Time & Correct (`is_normal_time` & `is_correct`==`True`):** N/A
        - **D.2. `Non-Math Related`**
            - **Slow & Wrong (`is_slow` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` ``
                    - `` `DI_READING_COMPREHENSION_ERROR` ``
                    - `` `DI_GRAPH_TABLE_INTERPRETATION_ERROR` ``
                    - `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math)
                    - `` `DI_QUESTION_TYPE_SPECIFIC_ERROR` `` (MSR Non-Math)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Apply general logic. Ask student to recall if logical reasoning barrier relates to RC sub-type concepts like `main idea`, `supporting idea`, or `inference`, or perform qualitative analysis.
            - **Slow & Correct (`is_slow` & `is_correct`==`True`):**
                - *Potential Efficiency Bottlenecks (Diagnostic Parameters)*: 
                    - `` `DI_EFFICIENCY_BOTTLENECK_INTEGRATION` ``
                    - `` `DI_EFFICIENCY_BOTTLENECK_READING` `` (Non-Math)
                    - `` `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE` ``
                    - `` `DI_EFFICIENCY_BOTTLENECK_LOGIC` `` (Non-Math)
                - *Diagnostic Actions*: Apply general logic. Student **does not** need to identify sub-type concepts.
            - **Normal Time & Wrong (`is_normal_time` & `is_correct`==`False`) / Fast & Wrong (`is_relatively_fast` & `is_correct`==`False`):**
                - *Potential Causes (Diagnostic Parameters)*: 
                    - `` `DI_READING_COMPREHENSION_ERROR` ``
                    - `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math)
                    - `` `DI_CARELESSNESS_DETAIL_OMISSION` `` (Mainly for fast & wrong)
                    - `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered)
                - *Diagnostic Actions*: Apply general logic, **strongly recommend triggering secondary evidence + qualitative analysis** here, analyze if related to `main idea`, `supporting idea`, `inference`.
            - **Fast & Correct (`is_relatively_fast` & `is_correct`==`True`):** Same as A.1 Fast & Correct.
            - **Normal Time & Correct (`is_normal_time` & `is_correct`==`True`):** N/A

<aside>

**Chapter Summary:** This chapter detailed the analysis of root causes behind different time-accuracy performance combinations across various question types and content domains, mapping these causes to standardized **English diagnostic parameters**. It defined `special_focus_error` (`` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) and emphasized its priority. For each scenario, trigger actions were designed, guiding students towards recall or leveraging secondary evidence (with sample size suggestions) and qualitative analysis to confirm specific barriers. A specific time check for MSR reading bottlenecks was also included.

**Results Destination:** The **English diagnostic parameters** and `special_focus_error` flags generated in this chapter are core inputs for creating targeted practice method recommendations in Chapter 6. The triggered actions directly guide subsequent student reflection and information gathering. The diagnostic findings (represented by **English parameters**) will form the core content of the Chapter 7 summary report (**requiring presentation in natural language based on Appendix A**).

</aside>

---

# **Chapter 4: Special Pattern Observation**

<aside>

**Objective:** To identify special situations related to response behavior patterns, such as carelessness or inappropriate rapid responses early in the test (using filtered data), generating relevant **English diagnostic parameters**.
**Primary Focus:** Calculating the overall proportion of "relatively fast and wrong" responses to assess potential carelessness issues (associating with `` `BEHAVIOR_CARELESSNESS_ISSUE` ``); checking if the student responded too quickly (`question_time` < 1.0 minute) in the early stage of the test (first 1/3 of questions) (associating with `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``).
**Rationale:** Carelessness issues require different corrective methods than knowledge or skill deficiencies. Rushing early in the test might reflect poor testing strategies or psychological states.

</aside>

1. **Carelessness Rate Calculation (`carelessness_issue`):**
    - Use the `is_relatively_fast` definition from Chapter 3.
    - `num_relatively_fast_total` = Total count of questions in filtered data where `is_relatively_fast` == `True`.
    - `num_relatively_fast_incorrect` = Total count of questions in filtered data where `is_relatively_fast` == `True` and `is_correct` == `False`.
    - `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total` (if `num_relatively_fast_total` > 0).
    - If `fast_wrong_rate` > `threshold_fast_wrong_rate` (e.g., 0.25), set diagnostic parameter `` `BEHAVIOR_CARELESSNESS_ISSUE` `` to `True`, and record diagnostic action: "Remind student to pay attention to carelessness, reflect on potential issues like misreading, calculation errors, or misinterpreting options."

2. **Early-Stage Rapid Responses (`early_rushing_flag_risk`):**
    - Identify questions where `question_position` <= `total_number_of_questions` / 3 AND `question_time` < 1.0 minute (absolute standard).
    - Record the `question_id`, `question_type`, `content_domain` for these questions.
    - If any such questions are found, set diagnostic parameter `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` to `True`, and record diagnostic action: "Remind student that some responses early in the test were excessively fast, potentially impacting accuracy or missing key information; suggest adjusting the initial pace."

<aside>

**Chapter Summary:** This chapter defined two key behavioral pattern indicators: overall carelessness rate (`` `BEHAVIOR_CARELESSNESS_ISSUE` ``) and early rushing risk (`` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``). These patterns were assessed by calculating the proportion of relatively fast and wrong responses and checking response times for early-stage questions.

**Results Destination:** The **English behavioral parameters** generated in this chapter will be included in the Chapter 7 diagnostic summary to alert the student to relevant behavioral patterns and assist in generating diagnostic actions (e.g., carelessness requires specific reflection exercises).

</aside>

---

# **Chapter 5: Foundational Performance Assessment (Exemption & Override)**

## Foundational Performance Exemption Rule

<aside>
**Objective:** To identify specific areas where the student has demonstrated complete mastery and efficiency within time limits, avoiding unnecessary practice recommendations.
</aside>

- **Judgment Level:** This rule operates at the level of **`question_type` + `content_domain` combinations** (e.g., "DS - Math Related", "TPA - Non-Math Related").
- **Exemption Status Calculation:**
    - For each `question_type` + `content_domain` combination:
        - Filter all **valid questions** belonging to this combination (excluding `is_invalid` = `True` questions).
        - **Condition 1 (Accuracy):** All these valid questions must have `is_correct` == `True`.
        - **Condition 2 (Efficiency):** All these valid questions must have `overtime` == `False` (based on the definition for the corresponding `question_type` in Chapter 1, including MSR's dual criteria).
    - If **both** Condition 1 and Condition 2 are met, the exemption status `exemption_status[type, domain]` for this combination is calculated as `True`, otherwise `False`.
- **Impact of Exemption Rule:**
    - The calculated exemption status **will be used** in the Chapter 6 practice recommendation generation logic. Combinations flagged as exempted will **skip** all practice recommendations.
    - The diagnostic summary (Chapter 7) will mention these exempted combinations to highlight the student's strengths.

---

## Foundational Ability Override Rule

<aside>

**Objective:** To check if there is widespread and severe difficulty within a specific `question_type` **(regardless of whether it was exempted)**.

</aside>

- **Calculated Metrics:** Calculate the overall error rate (`error_rate_type`) and overtime rate (`overtime_rate_type`) for each `question_type` (`DS`, `TPA`, `MSR`, `GT`).
- **Trigger Condition (`override_triggered`):** If, for a specific `question_type`, `error_rate_type` > 0.5 OR `overtime_rate_type` > 0.5, then flag `override_triggered`[that `question_type`] = `True`.
- **Determine Macro Practice Difficulty (If triggered):** Find the minimum `question_difficulty` value (`min_error_or_overtime_difficulty_per_type`) among all incorrect or overtime questions within that `question_type`. Convert this `min_error_or_overtime_difficulty_per_type` to the corresponding difficulty label (`Y_agg`) using the mapping rules from Chapter 2, for use in macro recommendations.
- **Set Macro Time Limit (`Z_agg`):**
    - Identify all questions that triggered the override rule for this question type.
    - Find the maximum `question_time` among these triggering questions, denoted as `max_time_triggering`.
    - Calculate `Z_agg` = `floor(max_time_triggering * 2) / 2` (round down to the nearest 0.5 minutes).

<aside>

**Chapter Summary:** This chapter established a question-type level override rule. By examining the overall error and overtime rates for each `question_type` (`DS`, `TPA`, `MSR`, `GT`), it determines if extremely poor performance (error rate or overtime rate > 50%) exists. If so, it triggers the override flag (`override_triggered`) for that type and determines the starting practice difficulty (`Y_agg`) and time limit (`Z_agg`) for macro-level recommendations.

**Results Destination:** The `override_triggered` flag directly influences the practice recommendation generation logic in Chapter 6. If a question type triggers the override rule, Chapter 6 will generate macro-level, foundational consolidation recommendations (using `Y_agg` and `Z_agg`), instead of case-based recommendations derived from individual incorrect or overtime questions of that type.

</aside>

---

# **Chapter 6: Practice Planning and Recommendations**

<aside>

**Objective:** To generate specific, actionable practice recommendations based on the analysis results from all previous chapters (especially the diagnosis in Chapter 3 and the override rules in Chapter 5).
**Primary Focus:** Integrating results from error analysis (`is_correct`==`False`), correct-but-overtime analysis (`is_correct`==`True` and `overtime`==`True`), special focus errors (`special_focus_error`), and question type override rules (`override_triggered`) to create specific (specifying difficulty `Y`, time limit `Z`) or macro (specifying difficulty `Y_agg`, time limit `Z_agg`) practice tasks for the relevant `question_type`. Additionally, appending practice method suggestions based on Chapter 3 diagnosis and applying `content_domain` performance adjustment rules (exemption/focus) from Chapter 2.
**Rationale:** This is the crucial step of translating diagnostic results into practical improvement plans, aiming to provide the student with a personalized, layered (distinguishing foundational consolidation from case-specific breakthroughs) practice plan including content (What), difficulty (Y/Y_agg), time limit (Z/Z_agg), and method (How).

</aside>

- **Suggestion Trigger Points:** Error questions diagnosed in Chapter 3 (`is_correct` == `False`) and correct-but-overtime questions (`is_correct` == `True` and `overtime` == `True`), as well as `question_type`s that triggered `override_triggered` in Chapter 5.
- **Suggestion Generation Logic:**
    - **Pre-Calculation/Preparation:**
        - Initialize dictionary `recommendations_by_type` = `{}`.
        - Initialize set `processed_override_types` = `set()`.
        - **Calculate Exemption Combinations (`exempted_combinations`):**
            - Initialize set `exempted_combinations` = `set()`.
            - For each `question_type` (`Qt`) and `content_domain` (`Dm`) combination:
                - Check the `exemption_status[Qt, Dm]` calculated in Chapter 5.
                - If `exemption_status[Qt, Dm]` is `True`, add `(Qt, Dm)` to `exempted_combinations`.
    - **Traverse Trigger Points (Question `X` or Question Type `Qt`):**
        - **Process Macro Suggestion:** If the trigger point is question type `Qt` and `override_triggered`[`Qt`] == `True` (from Chapter 5) and `Qt` not in `processed_override_types`:
            - Generate macro suggestion `G`: "For [`Qt`] type, since overall performance has significant room for improvement, it's recommended to systematically reinforce the foundation, starting from [`Y_agg`] difficulty questions, to master the core method, and it's recommended to limit time to [`Z_agg`] minutes." (`Y_agg` and `Z_agg` from Chapter 5).
            - Add `G` to `recommendations_by_type`[`Qt`].
            - Add `Qt` to `processed_override_types`.
        - **Process Case Suggestion (for question `X` with type `Qt`, domain `Dm`, difficulty `D`, time `T`):**
            - **Check Exemption and Macro:** If `(Qt, Dm)` is in `exempted_combinations`, or `Qt` is in `processed_override_types`, skip.
            - **Practice Difficulty (Y):** Map `D` using the 6-level standard (same as Q/V files).
            - **Starting Practice Time Limit (Z):** (**Unified Calculation Rule**)
                - Determine type target time (`target_time`) (referencing Chapter 5 `Z_agg` setting logic):
                    - `DS`: 2.0, `TPA`: 3.0, `GT`: 3.0, `MSR`: 2.0 (single question target).
                - Calculate `base_time`: If question `X` is overtime (`overtime` == `True`), then `T` - 0.5, otherwise `T`.
                - Calculate `Z_raw` = `floor`(`base_time` * 2) / 2 (round down to nearest 0.5).
                - Ensure minimum value: `Z` = `max`(`Z_raw`, `target_time`).
            - **Construct Recommendation Text:**
                - Base template: "For [`Qt`] questions in the [`Dm`] domain (addressing specific issue from Chapter 3/4 diagnosis), recommend practicing [`Y`] difficulty questions, with a starting time limit of [`Z`] minutes. (Target time: DS 2min; TPA/GT 3min; MSR single Q ~2min)."
                - **Priority Annotation:** If the question triggered `special_focus_error` = `True`, prepend "*Foundational mastery unstable*" to this recommendation.
                - **Extended Time Reminder:** If `Z` - `target_time` > 2.0 minutes, add reminder "**Significant practice volume needed to ensure gradual time limit reduction is effective.**"
            - Add case suggestion `C` to `recommendations_by_type`[`Qt`].
    - **Collate and Output Recommendation List:**
        - Initialize `final_recommendations`.
        - **Process Exempted Combinations:** For each `(Qt, Dm)` in `exempted_combinations`:
            - If `Qt` did **not** trigger a macro suggestion (`Qt` not in `processed_override_types`):
                - Add an exemption note to `final_recommendations`: "Performance on [`Qt`] questions in [`Dm`] is stable; practice can be deferred."
        - **Collate Aggregated Suggestions:** Iterate through `recommendations_by_type`.
            - For each type `Qt` and its recommendation list `type_recs`:
                - If the list is not empty:
                    - **Apply `content_domain` Focus Rules (based on Chapter 2 significant difference flags):**
                        - Check for `poor_math_related`/`slow_math_related` flags from Chapter 2: If triggered AND `type_recs` contains case suggestions for `Math Related`, append: "**Recommend increasing the proportion of `Math Related` practice for [`Qt`] questions.**"
                        - Check for `poor_non_math_related`/`slow_non_math_related` flags from Chapter 2: If triggered AND `type_recs` contains case suggestions for `Non-Math Related`, append: "**Recommend increasing the proportion of `Non-Math Related` practice for [`Qt`] questions.**"
                    - Add the collated recommendations for type `Qt` to `final_recommendations`.
        - **Final Output:** Output `final_recommendations`, ensuring aggregation by type, prioritization of `special_focus_error` suggestions, inclusion of exemption notes and focus notes.

<aside>

**Chapter Summary:** This chapter generated a structured list of practice recommendations, aggregated by `question_type` (`DS`, `TPA`, `MSR`, `GT`). Based on the override rules from Chapter 5, recommendations were categorized as macro (for types needing foundational strengthening) or case-based (for specific incorrect or overtime questions). Each recommendation specified the practice difficulty (`Y` or `Y_agg`) and starting time limit (`Z` or `Z_agg`), with method suggestions potentially appended based on Chapter 3 diagnoses (though explicit appending wasn't detailed here). `special_focus_error` recommendations were prioritized. Finally, `content_domain`-based exemption (from Chapter 5) and focus rules (from Chapter 2) were applied to fine-tune the suggestions.

**Results Destination:** This detailed, type-organized list of practice recommendations forms the core action plan section of the final student diagnostic report (Chapter 7).

</aside>

---

# **Chapter 7: Diagnostic Summary and Next Steps**

<aside>

**Objective:** To synthesize the analysis results from the previous six chapters into a clear, fluent, and prioritized final diagnostic report written entirely in natural language, providing clear guidance for subsequent actions. **(Based on internal diagnostic parameters and their descriptions in Appendix A)**
**Primary Focus:** Integrating the time pressure assessment, performance comparisons across different domains, core diagnostic findings (represented by **English parameters** like `` `DI_CONCEPT_APPLICATION_ERROR` `` or `` `DI_BEHAVIOR_CARELESSNESS_ISSUE` ``), special behavioral patterns, and the personalized practice recommendations and follow-up action plan generated based on these findings.
**Rationale:** This is the final deliverable for the student. The clarity and guidance of the report directly impact the student's ability to understand their issues and improve effectively. The report needs to translate complex data analysis into easy-to-understand and actionable advice.

</aside>

**1. Opening Summary (Based on Chapter 1)**

*   (Summarize overall time usage: Was time pressure experienced? How does total response time compare to the target time? Was there a risk of invalid data at the end due to `is_invalid` trigger?)

**2. Performance Overview (Based on Chapter 2)**

*   (Summarize `Math Related` vs `Non-Math Related` performance: In which domain was the error rate lower (`poor_math_related`/`poor_non_math_related`) or time consumption longer (`slow_math_related`/`slow_non_math_related`)? Was there a significant difference?)

**3. Core Problem Analysis (Based on Chapter 3)**

*   (Based on the **English diagnostic parameters** generated in Chapter 3, distill the 2-3 main problem areas. For example, point out frequent occurrences of `` `DI_CONCEPT_APPLICATION_ERROR` `` in `Math Related` questions, or that `` `DI_LOGICAL_REASONING_ERROR` `` is the main barrier in `Non-Math Related` `DS` questions.)
*   (Specifically mention the triggering of `special_focus_error` (`` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``), emphasizing the issue of unstable foundational mastery.)

**4. Special Pattern Observation (Based on Chapter 4)**

*   (Report behavioral pattern parameters found in Chapter 4: Is there a carelessness issue `` `BEHAVIOR_CARELESSNESS_ISSUE` ``? Is there a risk of rushing early in the test `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``?)

**5. Detailed Diagnostic Explanation (Based on Chapter 3 - Supplementary, for deeper review)**

*   (Optional: Provide a detailed list showing **each** error or overtime question (`is_correct`=False or `overtime`=True) with its specific diagnostic information for detailed tracking. The list should be **sorted by question type, content domain, and question number**. Each entry includes:)
    *   **Question Number, Type (Full Name), Domain (Full Name)**
    *   **Performance Tag:** Labeled as "Fast & Wrong", "Slow & Wrong", "Normal Time & Wrong", or "Slow & Correct" based on time and accuracy.
    *   **Diagnostic Parameters:** List the **translated descriptions (from Appendix A)** of all English diagnostic parameters triggered by this question, **grouped by pre-defined categories** (e.g., SFE, Reading/Interpretation, Concept Application, Logical Reasoning, Data Handling, MSR Specific, Efficiency, Behavior).
*   (Note: This list is intended to provide a more granular view than the core problem analysis.)

**6. Practice Recommendations (Based on Chapter 6)**

*   (Present the specific practice recommendation table or list generated in Chapter 6. Emphasize that these recommendations are based on identified **English diagnostic parameters** and have been personalized by applying macro override, **aggregation**, and perfect performance exemption rules.)

**7. Next Steps Guidance**

*   **Diagnostic Understanding Confirmation:**
    *   *General Prompt:* "Please read the report carefully, especially the core problem analysis section. Do you agree with the main issues identified (e.g., the issue described by `` `Parameter X` ``)? Does this align with your experience during the test?"
    *   *Question regarding `special_focus_error` (`` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``):* "The report indicates errors on some relatively basic questions, suggesting foundational mastery might be unstable. Do you think this is mainly carelessness, or are there genuinely unclear areas in certain basic concepts?"
    *   *Question regarding efficiency bottlenecks (e.g., `` `DI_EFFICIENCY_BOTTLENECK_...` ``):* "The report notes longer time spent on some correctly answered questions, possibly due to.... Which situation best describes your problem-solving process at the time?"
*   **Qualitative Analysis Suggestion:**
    *   *Trigger Condition:* When the student is uncertain about an **English diagnostic parameter** generated in Chapter 3, or needs further confirmation of the root cause.
    *   *Recommended Action:* Prompt the student to provide more detailed problem-solving information, e.g.: "If you are still confused about the issue related to parameter [`Parameter X`] mentioned in the report, you could try **providing detailed solution processes and thought examples for 2-3 related incorrect questions** for a deeper case analysis by the consultant."
*   **Secondary Evidence Reference Suggestion:**
    *   *Trigger Condition:* When the student cannot accurately recall specific barrier points (especially involving specific knowledge points or barrier types corresponding to certain **English parameters**), or needs objective data to support the diagnosis.
    *   *Recommended Action:* Suggest referring to practice records. E.g.: "To more precisely locate the issue related to parameter [`Parameter X`] encountered in [`content_domain`] [`question_type`] questions, it is recommended you review recent practice records..." (Refer to specific wording in Chapter 3)
*   **Auxiliary Tools and AI Prompt Recommendation Suggestion:**
    *   *Recommendation Logic:* To help you organize practice more effectively and address problems in a targeted manner, here are some potentially applicable auxiliary tools and AI prompts. The system recommends relevant resources based on the combination of diagnostic parameters triggered for you. Please select based on your specific diagnostic results.
    *   *Recommendation List (Based on Diagnostic Parameters):*

        * **If diagnosis involves errors in reading comprehension, chart, or data interpretation:**
            * `` `DI_READING_COMPREHENSION_ERROR` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Close_Reading_Coach.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` `` , `` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_GRAPH_TABLE_INTERPRETATION_ERROR` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/04_problem_pattern.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_DATA_EXTRACTION_ERROR` `` (GT) →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR` `` (GT/MSR Non-Math) →
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `DI-related/03_msr_info_flow.md` `` (MSR)

        * **If diagnosis involves errors in math concepts, calculation, or logic:**
            * `` `DI_CONCEPT_APPLICATION_ERROR` `` (Math) →
                * **Tool:** `Dustin_GMAT_Textbook_Explainer.md`, `Dustin_GMAT_Q_Question_Classifier.md`
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/05_variant_questions.md` ``
            * `` `DI_LOGICAL_REASONING_ERROR` `` (Non-Math) →
                * **Tool:** `Dustin_GMAT_DI_Non-math_DS_Simulator.md` (if DS), `Dustin_GMAT_Textbook_Explainer.md`
                * AI Prompt: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/02_quick_cr_tpa_tricks.md` `` , `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``
            * `` `DI_CALCULATION_ERROR` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/02_quick_math_tricks.md` ``

        * **If diagnosis involves MSR specific issues:**
            * `` `DI_MULTI_SOURCE_INTEGRATION_ERROR` `` →
                * **Tool:** `Dustin_GMAT_Chunk_Reading_Coach.md` (if integration slow due to reading slow)
                * AI Prompt: `` `Verbal-related/04_mindmap_passage.md` ``, `` `Verbal-related/01_basic_explanation.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_MSR_READING_COMPREHENSION_BARRIER` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/01_basic_explanation.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``

        * **If diagnosis involves specific question type or foundational mastery issues:**
            * `` `DI_QUESTION_TYPE_SPECIFIC_ERROR` `` →
                * **Tool:** `Dustin_GMAT_DI_Non-math_DS_Simulator.md` (if DS-NonMath)
                * AI Prompt: Choose based on specific type, e.g., `` `DI-related/02_quick_g&t_tricks.md` `` (GT), `` `DI-related/03_msr_info_flow.md` `` (MSR).
            * `` `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` →
                * **Tool:** `Dustin_GMAT_Textbook_Explainer.md`
                * AI Prompt: **Prioritize** `` `Quant-related/01_basic_explanation.md` `` ; supplement with `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/05_variant_questions.md` ``.

        * **If diagnosis involves efficiency bottlenecks:**
            * `` `DI_EFFICIENCY_BOTTLENECK_READING` `` →
                * **Tool:** `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Close_Reading_Coach.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``
            * `` `DI_EFFICIENCY_BOTTLENECK_CONCEPT` `` (Math) →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Quant-related/04_problem_pattern.md` ``
            * `` `DI_EFFICIENCY_BOTTLENECK_CALCULATION` `` →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``
            * `` `DI_EFFICIENCY_BOTTLENECK_LOGIC` `` (Non-Math) →
                * AI Prompt: `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE` `` →
                * **Tool:** `GMAT_Terminator_DI_Review.md` (if course covers GT)
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `DI-related/02_quick_g&t_tricks.md` ``
            * `` `DI_EFFICIENCY_BOTTLENECK_INTEGRATION` `` (MSR) →
                * **Tool:** `GMAT_Terminator_DI_Review.md` (if course covers MSR), `Dustin_GMAT_Chunk_Reading_Coach.md` (if due to slow reading)
                * AI Prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``, `` `DI-related/03_msr_info_flow.md` ``, `` `DI-related/04_custom_SOP.md` ``

        * **If diagnosis involves behavioral patterns:** 
            * `` `BEHAVIOR_CARELESSNESS_ISSUE` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` →
                * AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
            * `` `DI_CARELESSNESS_DETAIL_OMISSION` `` →
                * AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``

        * **General DI Review/Practice:**
            * **Tool:** `GMAT_Terminator_DI_Review.md`
            * AI Prompt: `` `Quant-related/06_similar_questions.md` `` (Math related), `` `Quant-related/05_variant_questions.md` `` (Math related variants)

<aside>

**Chapter Summary:** This chapter aims to translate the analysis results from previous chapters into a student-facing, clear, understandable, and actionable diagnostic report. The report structure includes: an opening summary, performance overview, core problem analysis (based on **English diagnostic parameters**, described using **Appendix A**), special pattern observation (based on **English behavioral parameters**), an optional detailed diagnostic list (containing performance tags, categorized translated parameters, sorted), personalized practice recommendations (distinguishing macro, aggregated, exempted), and next steps guidance including diagnostic confirmation, qualitative analysis suggestions, secondary evidence suggestions, and auxiliary tool/AI prompt recommendations based on **parameter combination mapping**.

</aside>

---

# **Appendix A: Diagnostic Parameter Tags and English Descriptions**

| English Parameter                          | English Description                                                    |
|--------------------------------------------|----------------------------------------------------------------------|
| **DI - Reading & Understanding**           |                                                                      |
| `DI_READING_COMPREHENSION_ERROR`           | DI Reading Comprehension: Text/Meaning Understanding Error/Barrier   |
| `DI_GRAPH_TABLE_INTERPRETATION_ERROR`      | DI Graph/Table Interpretation: Error/Barrier in reading visual data |
| **DI - Concept & Application (Math)**      |                                                                      |
| `DI_CONCEPT_APPLICATION_ERROR`             | DI Concept Application (Math): Math Concept/Formula Application Error/Barrier |
| **DI - Logical Reasoning (Non-Math)**      |                                                                      |
| `DI_LOGICAL_REASONING_ERROR`               | DI Logical Reasoning (Non-Math): Internal Logical Reasoning/Judgment Error |
| **DI - Data Handling & Calculation**       |                                                                      |
| `DI_DATA_EXTRACTION_ERROR`                 | DI Data Extraction (GT): Error extracting data from charts/tables      |
| `DI_INFORMATION_EXTRACTION_INFERENCE_ERROR`| DI Info Extraction/Inference (GT/MSR Non-Math): Info Location/Inference Error |
| `DI_CALCULATION_ERROR`                     | DI Calculation: Mathematical Calculation Error/Barrier               |
| **DI - MSR Specific**                      |                                                                      |
| `DI_MULTI_SOURCE_INTEGRATION_ERROR`        | DI Multi-Source Integration (MSR): Error/Barrier integrating info across tabs/sources |
| `DI_MSR_READING_COMPREHENSION_BARRIER`     | DI MSR Reading Barrier: Excessive overall reading time for the group |
| **DI - Question Type Specific**            |                                                                      |
| `DI_QUESTION_TYPE_SPECIFIC_ERROR`          | DI Specific Question Type Barrier (e.g., MSR Non-Math sub-type)       |
| **DI - Foundational & Efficiency**         |                                                                      |
| `DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`  | DI Foundational Mastery: Unstable Application (Special Focus Error)  |
| `DI_EFFICIENCY_BOTTLENECK_READING`         | DI Efficiency Bottleneck: Reading Comprehension Time (Math/Non-Math)|
| `DI_EFFICIENCY_BOTTLENECK_CONCEPT`         | DI Efficiency Bottleneck: Concept/Formula Application Time (Math)    |
| `DI_EFFICIENCY_BOTTLENECK_CALCULATION`     | DI Efficiency Bottleneck: Calculation Time                           |
| `DI_EFFICIENCY_BOTTLENECK_LOGIC`           | DI Efficiency Bottleneck: Logical Reasoning Time (Non-Math)         |
| `DI_EFFICIENCY_BOTTLENECK_GRAPH_TABLE`     | DI Efficiency Bottleneck: Graph/Table Interpretation Time            |
| `DI_EFFICIENCY_BOTTLENECK_INTEGRATION`     | DI Efficiency Bottleneck: Multi-Source Info Integration Time (MSR)  |
| **DI - Behavior**                          |                                                                      |
| `DI_CARELESSNESS_DETAIL_OMISSION`          | DI Behavior: Carelessness - Detail Omission/Misread (Implied in Fast & Wrong) |
| **Behavioral Patterns**                  |                                                                      |
| `BEHAVIOR_CARELESSNESS_ISSUE`              | Behavioral Pattern: Carelessness - High Overall Fast & Wrong Rate    |
| `BEHAVIOR_EARLY_RUSHING_FLAG_RISK`         | Behavioral Pattern: Risk of Rushing Early in the Test                |

\n\n(End of document)\n\