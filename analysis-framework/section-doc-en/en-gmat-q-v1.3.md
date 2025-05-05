# **Chapter 0: Core Input Data and Configuration**

- **Per-Question Data:**
    - `question_position` (Question Position, required, unique identifier)
    - `question_time` (Response Time/minutes)
    - `is_correct` (Correctness/Boolean)
    - `question_type` ('Real' / 'Pure')
    - `question_difficulty` (Difficulty Value)
    - `question_fundamental_skill` (Core Skill)
    - **Core Skill (`question_fundamental_skill`) Classification List:**
        - `Rates/Ratio/Percent`
        - `Value/Order/Factor`
        - `Equal/Unequal/ALG` (Equations/Inequalities/Algebra)
        - `Counting/Sets/Series/Prob/Stats` (Counting/Sets/Series/Probability/Statistics)
- **Overall Test Data:**
    - `total_test_time` (Total Response Time/minutes)
    - `max_allowed_time` (Maximum Allowed Test Time, fixed at 45 minutes)
    - `total_number_of_questions` (Total Number of Questions)

**New Calculation: Early Average Time**

- **Calculate average time per type for the first third (`first_third_average_time_per_type`)**:
    - For questions where `question_type` is 'Real', calculate the average `question_time` for all questions where `question_position` <= (`total_number_of_questions` / 3). Store this as `first_third_average_time_per_type['Real']`.
    - For questions where `question_type` is 'Pure', calculate the average `question_time` for all questions where `question_position` <= (`total_number_of_questions` / 3). Store this as `first_third_average_time_per_type['Pure']`.
    - *Note: This data is used later to determine if responses towards the end of the test were relatively rushed.*

---

# **Chapter 1: Overall Time Strategy and Data Validity Assessment**

<aside>

**Chapter Goal:** Evaluate the student's pacing and time management throughout the entire test section.
**Primary Focus:** Compare the student's total response time against the section time limit (45 minutes) and check for excessively fast responses towards the end of the test.
**Why It Matters:** This helps determine if the student felt excessive time pressure or had ample time. It also identifies questions potentially guessed due to insufficient time, ensuring the accuracy of subsequent analyses.

</aside>

1.  **Calculate Total Time Difference (`time_diff`)**:
    `time_diff` = `max_allowed_time` - `total_test_time`

2.  **Determine Time Pressure Status (`time_pressure`)**:
    - Default `time_pressure` = `False`.
    - Examine end-of-test conditions: Identify questions within the final one-third of the section (`last_third_questions`) where `question_time` < 1.0 minute (`fast_end_questions`).
    - Determination Logic: If `time_diff` <= 3 minutes **AND** `fast_end_questions` is not empty, set `time_pressure` = `True`.
    - **User Override:** If the user explicitly indicates minimal pressure, enforce `time_pressure` = `False`.

3.  **Establish Overtime Threshold (`overtime_threshold`)**:
    - If `time_pressure` == `True`, then `overtime_threshold` = 2.5 minutes.
    - If `time_pressure` == `False`, then `overtime_threshold` = 3.0 minutes.
    - *Note: This threshold will be used in subsequent analyses to flag individual questions where `question_time` exceeds the limit (`overtime` = `True`).*

4.  **Identify Invalid Data (`is_invalid`)**:
    - Initialize `invalid_question_positions` = `[]`.
    - **Flagging Logic (Executed only if `time_pressure` == `True`)**: Examine questions in the last one-third of the test (`last_third_questions`). For each question `Q` in this group:
        - **Define Abnormally Fast Response (`abnormally_fast_response`) criteria (meeting any one triggers):**
            - Criterion 1 (Suspected Giving Up): `Q.question_time` < 0.5 minutes.
            - Criterion 2 (Absolutely Rushed): `Q.question_time` < 1.0 minutes.
            - Criterion 3 (Relatively Rushed - Real): If `Q.question_type` == 'Real', check if `Q.question_time` < (`first_third_average_time_per_type['Real']` * 0.5).
            - Criterion 4 (Relatively Rushed - Pure): If `Q.question_type` == 'Pure', check if `Q.question_time` < (`first_third_average_time_per_type['Pure']` * 0.5).
        - **Judgment and Flagging:** If `time_pressure` == `True` **AND** question `Q` meets any of the `abnormally_fast_response` criteria above, then:
            - Add `Q.question_position` to the `invalid_question_positions` list.
            - Internally flag question `Q` with `is_invalid` = `True`.
    - *Note: Response data is considered invalid only when a student is under overall time pressure AND their response at the end of the test meets any criteria for being "abnormally fast" (either based on absolute time or significantly faster compared to their average speed on similar question types earlier in the test).*

5.  **Output and Summary**:
    - Key outputs generated in this chapter: `time_pressure` (Boolean), `overtime_threshold` (Numeric), `invalid_question_positions` (List), and the `is_invalid` flag applied to relevant questions.

**Global Rule Application: Identifying Invalid Data and Filtering**

1.  **Create Filtered Dataset:** Remove all questions whose `question_position` is included in the `invalid_question_positions` list from the original question data.
2.  **Scope of Subsequent Analysis:** All calculations, analyses, and recommendations from Chapter 2 through Chapter 7 will be based exclusively on this filtered dataset. **After filtering is complete, the `overtime` status will be flagged on the remaining valid questions based on the `overtime_threshold`.**

<aside>

**Chapter Summary:** We first calculated the total time difference (`time_diff`). Then, combining the time difference and the response speed at the end of the test, we determined if the student was under time pressure (`time_pressure`). Based on the time pressure status, we set a uniform single-question overtime threshold (`overtime_threshold`). Next, we calculated the average response time for each question type (`Real`/`Pure`) in the first third of the test (`first_third_average_time_per_type`). Finally, **only when time pressure was confirmed (`time_pressure` == `True`)**, we identified questions answered **abnormally fast** at the end of the test (based on absolute time criteria <0.5 or <1.0 minutes, or relative speed being too fast <50% compared to their earlier average for the same type) as invalid data (`is_invalid`) and recorded their positions (`invalid_question_positions`). **Before proceeding with further analysis, we will filter out this invalid data, and then flag overtime questions (`overtime`) among the remaining valid questions based on the `overtime_threshold`.**

**Outcome Destination:** The `time_pressure` status and `overtime_threshold` serve as crucial context for subsequent analysis. `first_third_average_time_per_type` is used for invalid data identification. The filtered dataset forms the basis for all analyses in subsequent chapters. Questions flagged as `overtime` will be used in later chapters to diagnose slow problems. Questions flagged as `is_invalid` are excluded before analysis begins.

</aside>

---

**Global Rule Application: Data Filtering**

1. Create Filtered Dataset: Remove all questions whose `question_position` is included in the `invalid_question_positions` list from the original question data.
2. Scope of Subsequent Analysis: All calculations, analyses, and recommendations from Chapter 2 through Chapter 7 will be based exclusively on this filtered dataset. (Note: The step of flagging whether a question is `overtime` should occur *after* this data filtering, based on the `overtime_threshold` determined in Chapter 1.)

<aside>

**Important Step: Data Cleaning**

**Goal:** Ensure our analysis is based on data that truly reflects the student's abilities.

**Execution:** We will remove questions identified as "invalid" (`is_invalid`) in Chapter 1 from the dataset. (These are questions answered abnormally fast at the end of the test under time pressure, where the "fast" criteria combine absolute time and comparison to earlier performance).

**Reason:** Analyzing invalid data cannot accurately assess the student's knowledge mastery or learning difficulties. All subsequent analysis (Chapters 2-7) will use this cleaned, filtered data.

</aside>

---

# **Chapter 2: Multi-Dimensional Performance Analysis**

<aside>

**Chapter Goal:** Compare the student's performance on "Real questions" (applied problems, word problems) and "Pure questions" (pure calculation, conceptual problems).

**Primary Focus:** Using the filtered data, analyze which question type the student is more prone to errors (error rate) or spending excessive time (overtime rate).

**Why It Matters:** This helps initially determine if the student's difficulties lean towards reading comprehension and problem translation (affecting `Real` questions) or towards core mathematical concepts and calculation skills (affecting `Pure` questions).

</aside>

1.  **Difficulty Level Standardization (`question_difficulty`, denoted as `D`):**
    - If `D` ≤ -1: Difficulty Level = "Low / 505+"
    - If -1 < `D` ≤ 0: Difficulty Level = "Medium / 555+"
    - If 0 < `D` ≤ 1: Difficulty Level = "Medium / 605+"
    - If 1 < `D` ≤ 1.5: Difficulty Level = "Medium / 655+"
    - If 1.5 < `D` ≤ 1.95: Difficulty Level = "High / 705+"
    - If 1.95 < `D` ≤ 2: Difficulty Level = "High / 805+"
2.  **Tallying (Based on Filtered Data):**
    - `num_total_real`, `num_total_pure` (Total count of `Real` and `Pure` questions)
    - `num_real_errors`, `num_pure_errors` (Count of errors in `Real` and `Pure` questions)
    - `num_real_overtime` (Count of `Real` questions where `overtime` == `True`)
    - `num_pure_overtime` (Count of `Pure` questions where `overtime` == `True`)
3.  **Calculating Rates (Handling Division by Zero):**
    - `wrong_rate_real` = `num_real_errors` / `num_total_real`
    - `wrong_rate_pure` = `num_pure_errors` / `num_total_pure`
    - `over_time_rate_real` = `num_real_overtime` / `num_total_real`
    - `over_time_rate_pure` = `num_pure_overtime` / `num_total_pure`
4.  **Determining Significant Differences and Flagging:**
    - If `abs`(`num_real_errors` - `num_pure_errors`) ≥ 2 OR `abs`(`num_real_overtime` - `num_pure_overtime`) ≥ 2, a significant difference in error or time consumption between `Real` and `Pure` questions is considered to exist.
    - Based on the significance and direction of the difference, apply corresponding flags:
        - If `Real` error rate is significantly higher, flag `poor_real` = `True`.
        - If `Pure` error rate is significantly higher, flag `poor_pure` = `True`.
        - If `Real` overtime rate is significantly higher, flag `slow_real` = `True`.
        - If `Pure` overtime rate is significantly higher, flag `slow_pure` = `True`.
5.  **Preliminary Diagnosis (Based on Flags):**
    - If `poor_real` or `slow_real` flags are generated (especially `slow_real`), the initial diagnosis may relate to slow reading speed.
    - If the `poor_real` flag is generated, it might also indicate reading comprehension difficulties.
    - If `poor_pure` or `slow_pure` flags are generated, subsequent analyses will focus more closely on the `question_fundamental_skill` associated with the `Pure` questions.
    - (Note: The `poor_real` and `slow_pure` flags defined in this chapter will be used in Chapter 7 to adjust practice recommendations for the corresponding skills.)

<aside>

**Chapter Summary:** We determined if there were significant performance differences between `Real` and `Pure` questions, generating corresponding flags like `poor_real` (more errors on Real questions) or `slow_pure` (often overtime on Pure questions).

**Outcome Destination:** These flags provide initial diagnostic directions. For example, `poor_real` might prompt us to look closer at reading-related issues in later steps. These flags will also be directly used in Chapter 7 to adjust the final practice recommendations.

</aside>

---

# **Chapter 3: Root Cause Diagnosis and Analysis**

<aside>

**Chapter Goal:** Deep dive into the questions the student answered incorrectly (using filtered data).
**Primary Focus:** Classify errors based on the time spent on the incorrect question (long or short) and the question's difficulty relative to the student's ability on that skill. Generate standardized **English diagnostic parameter tags**.
**Why It Matters:** Aims to understand the *nature* of the errors. Was it carelessness (fast and wrong)? Difficulty grasping the concept despite spending time (slow and wrong)? Or an unexpected slip-up on a relatively easier question (triggering `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``)?

</aside>

1.  **Calculate Prerequisite Data (Based on Filtered Data):**
    - `average_time_per_type`['Real'], `average_time_per_type`['Pure']` (Average response time for each question type)
    - `max_correct_difficulty_per_skill`[`skill`] (Highest `question_difficulty` among correctly answered (`is_correct` == `True`) questions for each `question_fundamental_skill`)
2.  **Analyze Incorrect Questions (Iterating through questions where `is_correct` == `False` in filtered data):**
    - For each incorrect question:
        - **Check for Special Focus Error (`special_focus_error`)**: Determine if the `question_difficulty` of the incorrect question is lower than the `max_correct_difficulty_per_skill`[`skill`] for its corresponding `question_fundamental_skill`. If so, flag `special_focus_error` = `True`, and associate with diagnostic parameter `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``.
        - **Priority Handling for `special_focus_error` / `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``**: When generating practice recommendations (Chapter 7) and outputting the diagnostic summary (Chapter 8), questions flagged as `special_focus_error` = `True`, along with their corresponding diagnostic parameter `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` and recommendations, should be **listed first or specially highlighted** (e.g., placed at the top of the list with an annotation like "*Fundamental mastery unstable*").
        - **Classify Error Type and Record Potential Causes:**
            - **Time Performance Classification (`Time Performance`):**
                - Fast (`is_relatively_fast`): `question_time` < `average_time_per_type`[question's `question_type`] * 0.75.
                - Slow (`is_slow`): Question is flagged `overtime` == `True` (from Chapter 1).
                - Normal Time (`is_normal_time`): Neither fast nor slow.
            - **Diagnostic Scenario Analysis:**
                - **Fast & Wrong:** (`is_relatively_fast` == `True` and `is_correct` == `False`)
                    - *Potential Causes (Diagnostic Parameters)*:
                        - `` `Q_CARELESSNESS_DETAIL_OMISSION` ``
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (if `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_PROBLEM_UNDERSTANDING_ERROR` ``
                    - *Primary Diagnostic Actions*:
                        1. *Recall*: Ask the student to recall the sticking point or reason for the error.
                        2. *Trigger Secondary Evidence*: If recall is unclear, recommend reviewing recent records of fast-but-wrong questions within the same `question_fundamental_skill` and related question types to identify error patterns.
                - **Slow & Wrong:** (`is_slow` == `True` and `is_correct` == `False`)
                    - *Potential Causes (Diagnostic Parameters)*:
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (if `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_CALCULATION_ERROR` ``
                        - `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (if `special_focus_error` == `True`)
                    - *Primary Diagnostic Actions*:
                        1. *Recall*: Ask the student to recall the sticking point – which step took the longest?
                        2. *Trigger Secondary Evidence*: If recall is unclear, recommend reviewing recent records of slow-but-wrong questions within the same `question_fundamental_skill` and related question types to identify types of barriers.
                        3. *Trigger Qualitative Analysis*: If still uncertain about the cause, recommend providing 2-3 examples of the problem-solving process.
                - **Normal Time & Wrong:** (`is_normal_time` == `True` and `is_correct` == `False`)
                    - *Potential Causes (Diagnostic Parameters)*:
                        - `` `Q_READING_COMPREHENSION_ERROR` `` (if `question_type` == 'Real')
                        - `` `Q_CONCEPT_APPLICATION_ERROR` ``
                        - `` `Q_PROBLEM_UNDERSTANDING_ERROR` ``
                        - `` `Q_CALCULATION_ERROR` `` (if complex calculation involved)
                        - `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (if `special_focus_error` == `True`)
                    - *Primary Diagnostic Actions*:
                        1. *Recall*: Ask the student to recall the reason for the error.
                        2. *Trigger Secondary Evidence*: If recall is unclear, recommend reviewing recent records of normal-time-but-wrong questions within the same `question_fundamental_skill` and related question types to identify error patterns.
                        3. *Trigger Qualitative Analysis*: If still uncertain about the cause, recommend providing 2-3 examples of the problem-solving process.

<aside>

**Chapter Summary:** We analyzed all incorrect questions, classifying them based on response time (fast/slow/normal). Introduced the diagnostic parameter `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` corresponding to `special_focus_error` and specified its priority handling. For different error types, we listed potential **English diagnostic parameters** (like `` `Q_CARELESSNESS_DETAIL_OMISSION` ``, `` `Q_CONCEPT_APPLICATION_ERROR` ``). We also provided suggested pathways for secondary evidence and qualitative analysis when the cause of error is unclear.

**Outcome Destination:** These error classifications, diagnostic parameters, and the `special_focus_error` / `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` flag are key inputs for generating specific practice recommendations (Chapter 7). The suggestions for secondary evidence and qualitative analysis aim to help students understand the root causes more deeply. The summary report in Chapter 8 will reference these parameters (translated via appendix).

</aside>

---

# **Chapter 4: Analysis of Time Spent on Correct Questions (Using Filtered Data)**

<aside>

**Chapter Goal:** Examine questions the student answered correctly but took longer than expected (using filtered data).

**Primary Focus:** Identify questions flagged as `is_correct` = `True` (answered correctly) and `overtime` = `True` (exceeded time threshold), and associate possible **English diagnostic parameters**.

**Why It Matters:** Even if answered correctly, excessive time spent can indicate issues. This might mean hesitation, difficulty retrieving knowledge, repeated calculations/checking, or (for `Real` questions) lengthy reading comprehension, pointing to different efficiency bottlenecks.

</aside>

1.  **Filter Questions:** Identify questions within the filtered dataset where `is_correct` = `True` AND `overtime` = `True` (i.e., correctly answered questions that exceeded the `overtime_threshold`).
2.  **Record and Hypothesize (Associate Diagnostic Parameters):**
    - Record the `question_position`, `question_type`, `question_fundamental_skill`, and `question_time` for these questions.
    - Potential Causes (Diagnostic Parameters):
        - `` `Q_EFFICIENCY_BOTTLENECK_READING` `` (if `question_type` == 'Real')
        - `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``
        - `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` ``

<aside>

**Chapter Summary:** We identified specific questions and associated skills where the student was correct but potentially inefficient. We recorded details of these "correct but overtime" questions and linked them to potential **English efficiency bottleneck parameters** (e.g., `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``).

**Outcome Destination:** These instances, along with their associated efficiency parameters, will also serve as triggers for generating practice recommendations in Chapter 7, aiming to improve the student's fluency and efficiency in related skills or question types. Chapter 8 report will summarize efficiency issues.

</aside>

---

# **Chapter 5: Special Pattern Observation and Carelessness Assessment**

<aside>

**Chapter Goal:** Observe if the student's response behavior relates to question position and assess overall response speed habits (using filtered data), generating relevant **English diagnostic parameters**.
**Primary Focus:** Check if the student exhibits rushing early in the test (`question_time` < 1.0 minute) (associated with `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``) and calculate the overall proportion of "relatively fast and wrong" responses (associated with `` `BEHAVIOR_CARELESSNESS_ISSUE` ``).
**Why It Matters:** Rushing early in the test might reflect poor test-taking strategy. A high rate of fast-and-wrong answers could indicate a general carelessness issue.

</aside>

1.  **Early-Stage Rapid Responses:**
    Identify questions where `question_position` ≤ `total_number_of_questions` / 3 AND `question_time` < 1.0 minute (absolute standard).
    Record the `question_position`, `question_type`, and `question_fundamental_skill` for these questions, associate with diagnostic parameter `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``, and issue a risk alert: "**Note `flag for review` issue.**"
2.  **Carelessness Rate Calculation (`carelessness_issue`):**
    `num_relatively_fast_total` = Total count of questions in the filtered data satisfying the "Fast" definition from Chapter 3 (`is_relatively_fast` == `True`).
    `num_relatively_fast_incorrect` = Total count of questions in the filtered data where `is_relatively_fast` == `True` and `is_correct` == `False`.
    `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total` (if `num_relatively_fast_total` > 0).
    If `fast_wrong_rate` > 0.25, flag `carelessness_issue` = `True`, associate with diagnostic parameter `` `BEHAVIOR_CARELESSNESS_ISSUE` ``, and include a reminder about potential carelessness in the Chapter 8 summary report.

<aside>

**Chapter Summary:**

We checked for questions answered absolutely too fast (`question_time` < 1.0 min) early in the test (associated parameter `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``) and calculated the overall "fast and wrong" rate (`fast_wrong_rate`) based on relative time standards. If this rate > 25%, we flagged a potential general carelessness issue (associated parameter `` `BEHAVIOR_CARELESSNESS_ISSUE` ``).

**Outcome Destination:** The diagnostic parameters `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` and `` `BEHAVIOR_CARELESSNESS_ISSUE` `` will be included as background information in the final diagnostic report (Chapter 8), alerting the student to potential behavioral pattern issues.

</aside>

---

# **Chapter 6: Foundational Ability Assessment (Exemption and Override)**

## Fundamental Skill Exemption Rule

<aside>
**Goal:** Identify core skills that the student has fully mastered and can complete efficiently within time limits, to avoid generating unnecessary practice recommendations.
</aside>

- **Level of Judgment:** This rule operates at the **`fundamental_skill`** level.
- **Exemption Status Calculation:**
    - For each `fundamental_skill` (`S`):
        - Filter all **valid questions** belonging to this skill (excluding those where `is_invalid` = `True`).
        - **Condition 1 (Accuracy):** All these valid questions must have `is_correct` = `True`.
        - **Condition 2 (Efficiency):** All these valid questions must have `overtime` = `False` (as flagged based on Chapter 1 definitions).
    - If **both** Condition 1 and Condition 2 are met, then the calculated exemption status for skill `S`, `skill_exemption_status[S]`, is `True`; otherwise, it is `False`.
- **Impact of the Exemption Rule:**
    - The calculated exemption status will be **used in** the logic for generating practice recommendations in Chapter 7. Skills flagged as exempt will **skip** all practice recommendation generation.
    - The diagnostic summary (Chapter 8) will mention these exempted skills to showcase the student's strengths.

---

## Foundational Ability Override Rule

<aside>

**Goal:** Check if any core skill **(regardless of exemption status)** shows widespread and severe difficulty (using filtered data).

**Primary Focus:** Calculate the overall error rate and overtime rate for each core skill (`fundamental_skill`). If either of these metrics is very high for a skill (e.g., > 50%), trigger a special rule.

**Why It Matters:** If a student struggles significantly across an entire skill area, recommendations targeting individual difficult problems within that area might be ineffective. It's better to first reinforce the fundamentals of that skill. This step acts as a "pre-check" before generating detailed recommendations.

</aside>

1.  **Calculate Performance Rates per Skill (Based on Filtered Data):**
    - For each `fundamental_skill` (`S`):
        - Calculate `num_total_skill`, `num_errors_skill`, `num_overtime_skill`.
        - Calculate `error_rate_skill`, `overtime_rate_skill`.
    - **Trigger Condition (`skill_override_triggered`):** If for a skill `S`, `error_rate_skill` > 0.5 OR `overtime_rate_skill` > 0.5:
        - Flag `skill_override_triggered`[`S`] = `True`.
        - Find the minimum difficulty `min_diff_skill` among incorrect or overtime questions for skill `S`.
        - Determine the macro practice difficulty `Y_agg` based on `min_diff_skill` (using the same mapping rule as `D` to `Y` in Chapter 7 case recommendations).
        - Set the macro time limit `Z_agg` = 2.5 minutes.

<aside>

**Chapter Summary:** This chapter established an override rule by checking the overall error and overtime rates for each core skill (`question_fundamental_skill`). It determines if performance is extremely poor (error or overtime rate > 50%). If so, the override flag for that skill (`skill_override_triggered`) is triggered, and a starting practice difficulty (`Y_agg`) and time limit (`Z_agg`) for macro-level recommendations are determined.

**Outcome Destination:** This flag directly influences the practice recommendation generation in Chapter 7. If a skill triggers the override rule, Chapter 7 will generate macro-level, foundational reinforcement recommendations for that skill (using `Y_agg` as starting difficulty and `Z_agg` time limit), instead of micro-level recommendations based on individual incorrect or overtime questions within that skill.

</aside>

---

# **Chapter 7: Practice Planning and Recommendations**

<aside>

**Chapter Goal:** Generate specific, actionable practice recommendations based on the analysis results from all previous steps.
**Primary Focus:** Integrate findings from error analysis (Chapter 3), correct-but-overtime analysis (Chapter 4), and skill override checks (Chapter 6) to create specific (difficulty, time limit) or macro practice tasks for relevant skills. Also, consider overall question type performance (Chapter 2) to fine-tune suggestions and apply exemption rules.
**Why It Matters:** This is the key step in translating diagnostic findings into a concrete improvement plan, aiming to provide students with a practice plan targeted at their specific weaknesses.

</aside>

1.  **Identify Recommendation Triggers:** Pinpoint all questions flagged with diagnostic labels from Chapter 3 (e.g., `slow_wrong`, `fast_wrong`, `special_focus_error`) or Chapter 4 (`overtime`=True and `is_correct`=True), and skills identified by `skill_override_triggered` in Chapter 6.
2.  **Generate and Preliminarily Classify Recommendations:**
    - Initialize a dictionary `recommendations_by_skill` = `{}` to temporarily store recommendation lists by skill.
    - Initialize a set `processed_override_skills` = `set()` to track skills for which macro recommendations have been generated.
    - Iterate through all triggering questions `X` (with core skill `S`, difficulty `D`, original time `T`):
        - **Check Exemption (Based on Chapter 6):** First, check the skill `S` exemption status `skill_exemption_status[S]`. If it is `True`, **skip** all subsequent recommendation generation steps for this skill and proceed to the next trigger point.
        - **Check for Macro Recommendation (for skill S):** If `skill_override_triggered`[`S`] is `True` AND skill `S` is **not** in `processed_override_skills`:
            - Generate macro recommendation `G` = "For skill [`S`], due to significant room for improvement (based on Chapter 6 analysis), recommend comprehensive foundational consolidation. Start systematic practice with [`Y_agg`] difficulty questions, focusing on core methods, with a recommended time limit of [`Z_agg`] minutes." (`Y_agg` and `Z_agg` from Chapter 6).
            - Add macro recommendation `G` to `recommendations_by_skill`[`S`] if the key exists, otherwise initialize the list with G.
            - Add skill `S` to `processed_override_skills`.
        - **Generate Case Recommendation (if skill S is not exempted):**
            - **Practice Difficulty (`Y`):** Map question `X`'s difficulty `D` using the **unified 6-level standard**:
                - If `D` ≤ -1: `Y` = "Low / 505+"
                - If -1 < `D` ≤ 0: `Y` = "Medium / 555+"
                - If 0 < `D` ≤ 1: `Y` = "Medium / 605+"
                - If 1 < `D` ≤ 1.5: `Y` = "Medium / 655+"
                - If 1.5 < `D` ≤ 1.95: `Y` = "High / 705+"
                - If 1.95 < `D` ≤ 2: `Y` = "High / 805+"
            - **Starting Practice Time Limit (`Z`):** (**Unified Calculation Rule**)
                - Set target time: `target_time` = 2.0 minutes.
                - Calculate `base_time`: If `X` was overtime (`overtime` == `True`), then `T` - 0.5, else `T`.
                - Calculate `Z_raw` = `floor`(`base_time` * 2) / 2 (round down to nearest 0.5).
                - Ensure minimum value: `Z` = `max`(`Z_raw`, `target_time`).
            - Construct the case recommendation `C` string (e.g., "Practice similar problems at difficulty level [`Y`] with a time limit of [`Z`] minutes.")
            - Add case recommendation `C` to `recommendations_by_skill`[`S`] if the key exists, otherwise initialize the list with C.
3.  **Collate and Output Recommendation List:**
    - Initialize `final_recommendations` = []
    - **Process Exempted Skills:** Iterate through all `fundamental_skill`s. For each skill `S`, if its `skill_exemption_status[S]` (from Chapter 6) is `True`, add an exemption note to `final_recommendations`: "Skill [`S`] performance is excellent; practice recommendations exempted."
    - **Collate Aggregated Recommendations:** Iterate through the `recommendations_by_skill` dictionary.
        - For each skill `S` and its recommendation list `skill_recs`:
            - **Re-check Exemption:** If `skill_exemption_status[S]` is `True`, skip processing this skill (ensuring exemption logic covers all cases).
            - If the list `skill_recs` is not empty:
                - **Apply Chapter 2 Diagnostic Adjustments (Focus Rules):**
                    - Check `poor_real` flag from Chapter 2: If `poor_real` = `True` AND at least one triggering question for skill `S` was 'Real', append to the skill `S` recommendation text: "**Recommend that Real questions constitute 2/3 of the total practice volume for this skill.**"
                    - Check `slow_pure` flag from Chapter 2: If `slow_pure` = `True` AND at least one triggering question for skill `S` was 'Pure', append to the skill `S` recommendation text: "**Recommend increasing the practice volume for this topic.**"
                - Add the collated and potentially adjusted recommendations for skill `S` (could include one macro and/or multiple case recommendations) to `final_recommendations`.
    - **Final Output:** Output `final_recommendations`, ensuring aggregation by skill, prioritization of `special_focus_error` related recommendations (needs logic to track/sort these), and inclusion of exemption notes.

---

# **Chapter 8: Diagnostic Summary and Next Steps**

<aside>

**Chapter Goal:** Consolidate all preceding analysis findings into a comprehensive, easy-to-understand diagnostic report written in natural language for student and teacher use.
**Primary Focus:** Integrate the student's overall time pressure situation, key analysis results, tailored practice recommendations, and provide guidance for subsequent actions.
**Why It Matters:** Offers a holistic perspective, highlighting the student's main strengths and areas for improvement, guiding future learning through clear explanations and actionable steps.

</aside>

**1. Opening Summary**

*   (Summarize findings from Chapter 1: Did the student experience significant time pressure during this test round (`time_pressure` = True)? How did the total response time compare to the allotted time (`time_diff`)? Were there signs of excessively fast responses at the end due to time pressure, potentially affecting data validity (`invalid_question_positions` list not empty)?) 

**2. Performance Overview**

*   (Summarize findings from Chapter 2: Compare performance on 'Real' vs. 'Pure' questions. Which type had more errors or longer response times? Was the difference significant (triggering `poor_real`, `slow_pure`, `poor_pure`, `slow_real` flags)? In which difficulty ranges were errors concentrated? Which core mathematical skills (`fundamental_skill`) were relative weaknesses based on error/overtime rates?)
*   **Strengths Identification:** Additionally, based on the analysis, you demonstrated complete mastery and efficient performance in the following core skills, exempting them from related practice recommendations: [`List of skills where skill_exemption_status from Chapter 6 is True`].

**3. Core Problem Diagnosis**

*   (Summarize main findings from Chapters 3 & 4 using natural language, based on the patterns of triggered diagnostic parameters: Describe the student's most common error types. For instance, is there a tendency for fast but incorrect answers (suggesting `` `Q_CARELESSNESS_DETAIL_OMISSION` `` or simplified processes), or spending considerable time but still failing (suggesting `` `Q_CONCEPT_APPLICATION_ERROR` `` or `` `Q_CALCULATION_ERROR` ``)? Are there instances of correct answers taking too long (related to `Q_EFFICIENCY_BOTTLENECK` parameters), indicating areas where application efficiency needs improvement?)
*   (Prioritize mentioning) (If `special_focus_error` was triggered in Chapter 3, emphasize here: 'Notably, errors occurred on some foundational or medium-difficulty questions within potentially mastered skill areas, suggesting potential instability in applying these concepts (`` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``).')

**4. Pattern Observation**

*   (Mention Chapter 5 findings) (If `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` was triggered, suggest: 'Response speed on some questions early in the test was relatively fast. It is advisable to maintain a steady pace to avoid potential "`flag for review`" risks.')
*   (Mention Chapter 5 findings) (If `` `BEHAVIOR_CARELESSNESS_ISSUE` `` was triggered, suggest: 'Analysis indicates a relatively high proportion of "fast and wrong" instances, suggesting a need to focus on carefulness during problem-solving to reduce unforced errors.')

**5. Foundational Consolidation Alert**

*   (Mention Chapter 6 findings) (If any `fundamental_skill` triggered `skill_override_triggered`, state clearly: 'For the core skills [`List of skills where skill_override_triggered is True`], overall performance indicates significant room for improvement. It is recommended to prioritize systematic foundational consolidation rather than only practicing individual missed problems.')

**6. Practice Plan Presentation**

*   (Clearly and fully list all practice recommendations generated in Chapter 7)
*   (Include exemption notes based on `skill_exemption_status`, e.g., 'Skill [`Exempted Skill Name`] performance is excellent; practice recommendations exempted.')
*   (Include focus notes based on Chapter 2 flags applied in Chapter 7, e.g., 'For practice on [`Skill Name`], recommend adjusting the proportion of `Real`/`Pure` questions...' or 'Recommend increasing practice volume...')
*   (Ensure `special_focus_error` / `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` related recommendations are prioritized or highlighted as determined in Chapter 7 logic)

**7. Next Steps Guidance**

*   **Core Constraint:** All text produced in this section **must use only natural language**. Avoid directly quoting or revealing any internal parameter names, diagnostic tags, or specific numerical thresholds used during the analysis.
*   **Guide Reflection:** (Ask questions based on the main diagnosed issues)
    *   If issues relate mainly to math concepts/skills (e.g., `` `Q_CONCEPT_APPLICATION_ERROR` ``, `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` triggered): 'Reflecting on the incorrect [`type` or `skill`] questions, what specific math concept or formula was the sticking point? Was it a complete lack of approach, or knowing the method but making a mistake in calculation?'
    *   If issues relate mainly to reading comprehension (`Real` questions, e.g., `` `Q_READING_COMPREHENSION_ERROR` ``, `poor_real` triggered): 'For the incorrect word problems, was the issue understanding the text itself, or translating the understood text into a mathematical problem? Are there specific topics or long sentences causing reading difficulty?'
*   **Secondary Evidence Reference Suggestion:**
    *   *Trigger When:* You cannot accurately recall the specific reason for error, the involved knowledge point, or need more objective data to confirm a pattern.
    *   *Recommended Action:* 'To more precisely pinpoint your specific difficulties in [`Skill`/`Type`], it's recommended to review your recent practice records (e.g., 2-4 weeks pre-test), collate related incorrect questions, and identify which knowledge points or question types repeatedly cause issues. If the sample size is insufficient, pay attention to collecting data in upcoming practice sessions until enough examples are gathered for analysis.'
*   **Qualitative Analysis Suggestion:**
    *   *Trigger When:* You are confused about the cause of errors identified in the report, or the above methods haven't clarified the root problem.
    *   *Recommended Action:* 'If you remain unclear about the reason for errors in [`Type of problem`], consider **providing detailed step-by-step solution processes and thought examples for 2-3 questions of that type** (text or audio recording). This allows for deeper case analysis with a consultant to identify the crux of the issue.'

#### Auxiliary Tools and AI Prompt Recommendations:

*   *Recommendation Logic:* To help you organize practice more effectively and tackle problems with targeted support, here are some potentially applicable auxiliary tools and AI prompts. The system recommends relevant resources based on the combination of diagnostic parameters triggered in your analysis. Please select based on your specific diagnostic results.
*   *Recommendation List (Based on triggered diagnostic parameters):*

    *   **If diagnosis involves Reading Comprehension, Problem Understanding, or Concept Application errors:**
        *   `` `Q_READING_COMPREHENSION_ERROR` `` (Real) →
            *   **Tool:** `Dustin_GMAT_Q_Real-Context_Converter.md`, `Dustin_GMAT_Core_Sentence_Cracker.md`, `Dustin_GMAT_Chunk_Reading_Coach.md`
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``
        *   `` `Q_PROBLEM_UNDERSTANDING_ERROR` `` →
            *   **Tool:** `Dustin_GMAT_Q_Question_Classifier.md`, `Dustin_GMAT_Textbook_Explainer.md`
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/03_test_math_concepts.md` ``, `` `Verbal-related/07_logical_term_explained.md` `` (for DS)
        *   `` `Q_CONCEPT_APPLICATION_ERROR` `` →
            *   **Tool:** `Dustin_GMAT_Q_Question_Classifier.md`, `Dustin_GMAT_Textbook_Explainer.md`
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/04_problem_pattern.md` ``, `` `Quant-related/05_variant_questions.md` ``

    *   **If diagnosis involves Calculation Errors or Foundational Mastery issues:**
        *   `` `Q_CALCULATION_ERROR` `` →
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/02_quick_math_tricks.md` ``
        *   `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` →
            *   **Tool:** `Dustin_GMAT_Textbook_Explainer.md`
            *   AI Prompt: **Priority** `` `Quant-related/01_basic_explanation.md` ``; Support `` `Quant-related/03_test_math_concepts.md` ``, `` `Quant-related/05_variant_questions.md` ``.

    *   **If diagnosis involves Efficiency Bottlenecks:**
        *   `` `Q_EFFICIENCY_BOTTLENECK_READING` `` (Real) →
            *   **Tool:** `Dustin_GMAT_Chunk_Reading_Coach.md`
            *   AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``
        *   `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` `` →
            *   AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Quant-related/04_problem_pattern.md` ``
        *   `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` `` →
            *   AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``

    *   **If diagnosis involves Behavioral Patterns:** *(Using consistent parameter names)*
        *   `` `BEHAVIOR_CARELESSNESS_ISSUE` `` →
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
        *   `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` →
            *   AI Prompt: `` `Quant-related/02_quick_math_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``
        *   `` `Q_CARELESSNESS_DETAIL_OMISSION` `` *(If this parameter is retained)* →
            *   AI Prompt: `` `Quant-related/01_basic_explanation.md` ``, `` `Quant-related/02_quick_math_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``

    *   **General Q Practice/Classification/Understanding:**
        *   **Tool:** `Dustin_GMAT_Q_Question_Classifier.md`, `Dustin_GMAT_Q_Real-Context_Converter.md`
        *   AI Prompt: `` `Quant-related/06_similar_questions.md` ``, `` `Quant-related/05_variant_questions.md` ``
Note: When presenting, only list the recommendations corresponding to parameters actually triggered by the diagnosis.

<aside>

**Chapter Summary:** We generated a final diagnostic report written entirely in natural language. The report first summarizes time usage and overall performance, then delves into core problem analysis (highlighting foundational mastery instability), incorporates observations of special response patterns, and points out skill areas needing foundational consolidation. The core part presents the detailed, skill-aggregated practice plan (with exemptions and focus rules applied). Finally, the report includes guiding questions and suggestions on using secondary evidence and qualitative analysis for self-reflection and targeted improvement.
**Outcome Destination:** This report is the final output of the entire diagnostic process, used for communication with the student and guiding their subsequent learning and practice.

</aside>

---

# Appendix A: Diagnostic Parameter Tags and English Descriptions

| English Parameter                          | English Description (for reference)                                  |
|--------------------------------------------|----------------------------------------------------------------------|
| **Quant - Reading & Understanding**        |                                                                      |
| `Q_READING_COMPREHENSION_ERROR`            | Quant Reading Comprehension: Real question text understanding error/barrier |
| `Q_PROBLEM_UNDERSTANDING_ERROR`            | Quant Problem Understanding: Misunderstanding of the math problem itself |
| **Quant - Concept & Application**          |                                                                      |
| `Q_CONCEPT_APPLICATION_ERROR`              | Quant Concept Application: Math concept/formula application error/barrier |
| `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE`   | Quant Foundational Mastery: Unstable application (Special Focus Error) |
| **Quant - Calculation**                    |                                                                      |
| `Q_CALCULATION_ERROR`                      | Quant Calculation: Calculation error/barrier                         |
| **Quant - Efficiency Bottlenecks**       |                                                                      |
| `Q_EFFICIENCY_BOTTLENECK_READING`          | Quant Efficiency Bottleneck: Real question reading time excessive      |
| `Q_EFFICIENCY_BOTTLENECK_CONCEPT`          | Quant Efficiency Bottleneck: Concept/formula thinking/derivation time excessive |
| `Q_EFFICIENCY_BOTTLENECK_CALCULATION`      | Quant Efficiency Bottleneck: Calculation process time excessive / repeated calculation |
| **Behavioral Patterns & Carelessness**   |                                                                      |
| `Q_CARELESSNESS_DETAIL_OMISSION`           | Behavioral Pattern: Carelessness - Ignoring details/conditions/traps |
| `BEHAVIOR_EARLY_RUSHING_FLAG_RISK`       | Behavioral Pattern: Early test rushing (Flag risk)                   |
| `BEHAVIOR_CARELESSNESS_ISSUE`            | Behavioral Pattern: General carelessness issue (high fast-wrong rate) |
| **Comparative Performance (Real vs Pure)** | (Flags set in Chapter 2, used in Chapter 7 & summarized in Chapter 8) |
| `poor_real`                                | Comparative Performance: Real question error rate significantly higher |
| `poor_pure`                                | Comparative Performance: Pure question error rate significantly higher |
| `slow_real`                                | Comparative Performance: Real question overtime rate significantly higher |
| `slow_pure`                                | Comparative Performance: Pure question overtime rate significantly higher |
| **Skill Level Override**                   | (Flag set in Chapter 6, used in Chapter 7 & summarized in Chapter 8) |
| `skill_override_triggered`                 | Skill Override: A core skill requires foundational consolidation (error/overtime rate > 50%) |
| **Skill Level Exemption**                  | (Status set in Chapter 6, used in Chapter 7 & summarized in Chapter 8) |
| `skill_exemption_status`                   | Skill Exemption: Skill demonstrates accuracy and efficiency (True/False status per skill) |

(End of document)