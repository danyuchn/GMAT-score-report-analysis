# **Chapter 0: Core Input Data and Configuration**

- **Per-Question Data:**
    - `question_id` (Question Identifier)
    - `question_time` (Response Time/minutes)
    - `is_correct` (Correctness/Boolean)
    - `question_type` ('Real' / 'Pure')
    - `question_difficulty` (Difficulty Value)
    - `question_fundamental_skill` (Core Skill)
    - `question_position` (Question Sequence Number)
    - **Core Skill (`question_fundamental_skill`) Classification List:**
        - `Rates/Ratio/Percent`
        - `Value/Order/Factor`
        - `Equal/Unequal/ALG` (Equations/Inequalities/Algebra)
        - `Counting/Sets/Series/Prob/Stats` (Counting/Sets/Series/Probability/Statistics)
- **Overall Test Data:**
    - `total_test_time` (Total Response Time/minutes)
    - `max_allowed_time` (Maximum Allowed Test Time, fixed at 45 minutes)
    - `total_number_of_questions` (Total Number of Questions)

---

# **Chapter 1: Overall Time Strategy and Data Validity Assessment**

1. **Calculate Total Time Difference (`time_diff`)**: 
   `time_diff` = `max_allowed_time` - `total_test_time`

2. **Determine Time Pressure Status (`time_pressure`)**: 
   - Default `time_pressure` = `False`.
   - Examine end-of-test conditions: Identify questions within the final one-third of the section (`last_third_questions`) where `question_time` < 1.0 minute (`fast_end_questions`).
   - Determination Logic: If `time_diff` <= 3 minutes **AND** `fast_end_questions` is not empty, set `time_pressure` = `True`.
   - **User Override:** If the user explicitly indicates minimal pressure, enforce `time_pressure` = `False`.

3. **Establish Overtime Threshold (`overtime_threshold`)**: 
   - If `time_pressure` == `True`, then `overtime_threshold` = 2.5 minutes.
   - If `time_pressure` == `False`, then `overtime_threshold` = 3.0 minutes.
   - *Note: This threshold will be used in subsequent analyses to flag individual questions where `question_time` exceeds the limit (`overtime` = `True`).*

4. **Identify Invalid Data (`is_invalid`)**: 
   - Initialize `invalid_question_ids` = `[]`.
   - Flagging Logic: If `time_pressure` == `True` (as determined in Step 2), add the `question_id` of `fast_end_questions` (i.e., questions in the last 1/3 with `question_time` < 1.0 minute) to the `invalid_question_ids` list and internally flag these questions with `is_invalid` = `True`.
   - *Note: Rapid responses at the end of the section are considered potentially invalid only when time pressure is confirmed.*

5. **Output and Summary**: 
   - Key outputs generated in this chapter: `time_pressure` (Boolean), `overtime_threshold` (Numeric), `invalid_question_ids` (List), and the `is_invalid` flag applied to relevant questions.

**Global Rule Application: Data Filtering and Flagging**

1.  **Flag Overtime (`overtime`):** For all questions **not flagged as `is_invalid`**, if their `question_time` > `overtime_threshold`, add an internal flag `overtime` = `True`.
2.  **Create Filtered Dataset:** Remove all questions whose `question_id` is in the `invalid_question_ids` list from the original dataset.
3.  **Scope of Subsequent Analysis:** All calculations, analyses, and recommendations from Chapter 2 through Chapter 7 will be based exclusively on this filtered dataset.

---

# **Chapter 2: Multi-Dimensional Performance Analysis**

1. **Difficulty Level Standardization (`question_difficulty`, denoted as `D`):**
    - If `D` ≤ -1: Difficulty Level = "Low / 505+"
    - If -1 < `D` ≤ 0: Difficulty Level = "Medium / 555+"
    - If 0 < `D` ≤ 1: Difficulty Level = "Medium / 605+"
    - If 1 < `D` ≤ 1.5: Difficulty Level = "Medium / 655+"
    - If 1.5 < `D` ≤ 1.95: Difficulty Level = "High / 705+"
    - If 1.95 < `D` ≤ 2: Difficulty Level = "High / 805+"
2. **Tallying (Based on Filtered Data):**
    - `num_total_real`, `num_total_pure` (Total count of `Real` and `Pure` questions)
    - `num_real_errors`, `num_pure_errors` (Count of errors in `Real` and `Pure` questions)
    - `num_real_overtime` (Count of `Real` questions where `overtime` == `True`)
    - `num_pure_overtime` (Count of `Pure` questions where `overtime` == `True`)
3. **Calculating Rates (Handling Division by Zero):**
    - `wrong_rate_real` = `num_real_errors` / `num_total_real`
    - `wrong_rate_pure` = `num_pure_errors` / `num_total_pure`
    - `over_time_rate_real` = `num_real_overtime` / `num_total_real`
    - `over_time_rate_pure` = `num_pure_overtime` / `num_total_pure`
4. **Determining Significant Differences and Flagging:**
    - If `abs`(`num_real_errors` - `num_pure_errors`) ≥ 2 OR `abs`(`num_real_overtime` - `num_pure_overtime`) ≥ 2, a significant difference in error or time consumption between `Real` and `Pure` questions is considered to exist.
    - Based on the significance and direction of the difference, apply corresponding flags:
        - If `Real` error rate is significantly higher, flag `poor_real` = `True`.
        - If `Pure` error rate is significantly higher, flag `poor_pure` = `True`.
        - If `Real` overtime rate is significantly higher, flag `slow_real` = `True`.
        - If `Pure` overtime rate is significantly higher, flag `slow_pure` = `True`.
5. **Preliminary Diagnosis (Based on Flags):**
    - If `poor_real` or `slow_real` flags are generated (especially `slow_real`), the initial diagnosis may relate to slow reading speed.
    - If the `poor_real` flag is generated, it might also indicate reading comprehension difficulties.
    - If `poor_pure` or `slow_pure` flags are generated, subsequent analyses will focus more closely on the `question_fundamental_skill` associated with the `Pure` questions.
    - (Note: The `poor_real` and `slow_pure` flags defined in this chapter will be used in Chapter 7 to adjust practice recommendations for the corresponding skills.)

---

# **Chapter 3: Root Cause Diagnosis and Analysis**

1. **Calculate Prerequisite Data (Based on Filtered Data):**
    - `average_time_per_type`['Real'], `average_time_per_type`['Pure']` (Average response time for each question type)
    - `max_correct_difficulty_per_skill`[`skill`] (Highest `question_difficulty` among correctly answered (`is_correct` == `True`) questions for each `question_fundamental_skill`)
2. **Analyze Incorrect Questions (Iterating through questions where `is_correct` == `False` in filtered data):**
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

---

# **Chapter 4: Analysis of Time Spent on Correct Questions (Using Filtered Data)**

1. **Filter Questions:** Identify questions within the filtered dataset where `is_correct` = `True` AND `overtime` = `True` (i.e., correctly answered questions that exceeded the `overtime_threshold`).
2. **Record and Hypothesize (Associate Diagnostic Parameters):**
    - Record the `question_id`, `question_type`, `question_fundamental_skill`, and `question_time` for these questions.
    - Potential Causes (Diagnostic Parameters):
        - `` `Q_EFFICIENCY_BOTTLENECK_READING` `` (if `question_type` == 'Real')
        - `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``
        - `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` ``

---

# **Chapter 5: Special Pattern Observation and Carelessness Assessment**

1. **Early-Stage Rapid Responses:**
   Identify questions where `question_position` ≤ `total_number_of_questions` / 3 AND `question_time` < 1.0 minute (absolute standard).
   Record the `question_id`, `question_type`, and `question_fundamental_skill` for these questions, associate with diagnostic parameter `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``, and issue a risk alert: "**Note `flag for review` issue.**"
2. **Carelessness Rate Calculation (`carelessness_issue`):**
    `num_relatively_fast_total` = Total count of questions in the filtered data satisfying the "Fast" definition from Chapter 3 (`is_relatively_fast` == `True`).
    `num_relatively_fast_incorrect` = Total count of questions in the filtered data where `is_relatively_fast` == `True` and `is_correct` == `False`.
    `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total` (if `num_relatively_fast_total` > 0).
    If `fast_wrong_rate` > 0.25, flag `carelessness_issue` = `True`, associate with diagnostic parameter `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` ``, and include a reminder about potential carelessness in the Chapter 8 summary report.

---

# **Chapter 6: Foundational Ability Override Rules**

1. **Calculate Performance Rates per Skill (Based on Filtered Data):**
    - For each `fundamental_skill` (`S`):
        - Calculate `num_total_skill`, `num_errors_skill`, `num_overtime_skill`.
        - Calculate `error_rate_skill`, `overtime_rate_skill`.
    - **Trigger Condition (`skill_override_triggered`):** If for a skill `S`, `error_rate_skill` > 0.5 OR `overtime_rate_skill` > 0.5:
        - Flag `skill_override_triggered`[`S`] = `True`.
        - Find the minimum difficulty `min_diff_skill` among incorrect or overtime questions for skill `S`.
        - Determine the macro practice difficulty `Y_agg` based on `min_diff_skill` (using the same mapping rule as `D` to `Y` in Chapter 7 case recommendations).
        - Set the macro time limit `Z_agg` = 2.5 minutes.

---

# **Chapter 7: Practice Planning and Recommendations**

1.  **Identify Recommendation Triggers:** Pinpoint all questions flagged with diagnostic labels from Chapter 3 (e.g., `slow_wrong`, `fast_wrong`, `special_focus_error`) or Chapter 4 (`overtime`=True and `is_correct`=True), and skills identified by `skill_override_triggered` in Chapter 6.
2.  **Generate and Preliminarily Classify Recommendations:**
    - Initialize a dictionary `recommendations_by_skill` = `{}` to temporarily store recommendation lists by skill.
    - Initialize a set `processed_override_skills` = `set()` to track skills for which macro recommendations have been generated.
    - **Calculate Exempted Skills:**
        - Initialize a set `exempted_skills` = `set()`.
        - For each `fundamental_skill` (`S`):
            - Calculate `num_correct_not_overtime`, the count of questions for skill `S` that are correct (`is_correct`==`True`) and not overtime (`overtime`==`False`).
            - If `num_correct_not_overtime` > 2, add `S` to `exempted_skills`.
    - Iterate through all triggering questions `X` (with core skill `S`, difficulty `D`, original time `T`):
        - **Check Exemption:** If skill `S` is in `exempted_skills`, skip generating a case-based recommendation for this question.
        - **Check for Macro Recommendation (for skill S):** If `skill_override_triggered`[`S`] is `True` AND skill `S` is **not** in `processed_override_skills`:
            - Generate macro recommendation `G` = "For skill [`S`], due to significant room for improvement (based on Chapter 6 analysis), recommend comprehensive foundational consolidation. Start systematic practice with [`Y_agg`] difficulty questions, focusing on core methods, with a recommended time limit of [`Z_agg`] minutes." (`Y_agg` and `Z_agg` from Chapter 6).
            - Add macro recommendation `G` to `recommendations_by_skill`[`S`].
            - Add skill `S` to `processed_override_skills`.
        - **Generate Case Recommendation (if skill S did not trigger macro and is not exempted):**
            - **Practice Difficulty (`Y`):** Map question `X`'s difficulty `D` using the **unified 6-level standard**: 
                - If `D` ≤ -1: `Y` = "Low / 505+"
                - If -1 < `D` ≤ 0: `Y` = "Medium / 555+"
                - If 0 < `D` ≤ 1: `Y` = "Medium / 605+"
                - If 1 < `D` ≤ 1.5: `Y` = "Medium / 655+"
                - If 1.5 < `D` ≤ 1.95: `Y` = "High / 705+"
                - If 1.95 < `D` ≤ 2: `Y` = "High / 805+"
            - **Starting Practice Time Limit (`Z`):** (**Unified Calculation Rule**)
                - Set target time: `target_time` = 2.0 minutes.
                - Calculate `base_time`: If `X` was overtime (`overtime` == `True` or `is_slow` == `True`), then `T` - 0.5, else `T`.
                - Calculate `Z_raw` = `floor`(`base_time` * 2) / 2 (round down to nearest 0.5).
                - Ensure minimum value: `Z` = `max`(`Z_raw`, `target_time`).
            - Add case recommendation `C` to `recommendations_by_skill`[`Skill`].
3.  **Collate and Output Recommendation List:**
    - Initialize `final_recommendations`.
    - **Process Exempted Skills:** For each skill `S` in `exempted_skills`, if it did **not** trigger a macro recommendation, add an exemption note to `final_recommendations`: "Skill [`S`] performance is stable; practice can be deferred."
    - **Collate Aggregated Recommendations:** Iterate through the `recommendations_by_skill` dictionary.
        - For each skill `S` and its recommendation list `skill_recs`:
            - If the list is not empty:
                - **Apply Chapter 2 Diagnostic Adjustments (Focus Rules):**
                    - Check `poor_real` flag from Chapter 2: If `poor_real` = `True` AND at least one triggering question for skill `S` was 'Real', append to skill `S` recommendations: "**Recommend that Real questions constitute 2/3 of the total practice volume for this skill.**"
                    - Check `slow_pure` flag from Chapter 2: If `slow_pure` = `True` AND at least one triggering question for skill `S` was 'Pure', append to skill `S` recommendations: "**Recommend increasing the practice volume for this skill.**"
                - Add the collated recommendations for skill `S` (potentially including one macro and/or multiple case recommendations, with focus rules applied) to `final_recommendations`.
    - **Final Output:** Output `final_recommendations`, ensuring aggregation by skill, prioritization of `special_focus_error` recommendations, and inclusion of exemption notes.

---

# **Chapter 8: Diagnostic Summary and Next Steps**

**1. Opening Summary**

*   (Summarize findings from Chapter 1: Did the student experience significant time pressure during this test round? How did the total response time compare to the allotted time? Were there signs of excessively fast responses at the end due to time pressure, potentially affecting data validity (`is_invalid` triggered)?)

**2. Performance Overview**

*   (Summarize findings from Chapter 2: Compare performance on 'Real' vs. 'Pure' questions. Which type had more errors or longer response times? Was the difference significant (triggering `poor_real`, `slow_pure`, `poor_pure`, `slow_real` parameters)? In which difficulty ranges were errors concentrated? Which core mathematical skills (`fundamental_skill`) were relative weaknesses?)

**3. Core Problem Diagnosis**

*   (Summarize main findings from Chapters 3 & 4 using natural language: **Based on generated diagnostic parameters (e.g., `` `Q_CONCEPT_APPLICATION_ERROR` ``, `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` ``) described in Appendix A**, describe the student's most common error types and efficiency bottlenecks. For instance, is there a tendency for fast but incorrect answers (possibly involving `` `Q_CARELESSNESS_DETAIL_OMISSION` ``), or spending considerable time but still failing (possibly involving `` `Q_CONCEPT_APPLICATION_ERROR` `` or `` `Q_CALCULATION_ERROR` ``)? Are there instances of correct answers taking too long (`EFFICIENCY_BOTTLENECK` related parameters), indicating areas where application efficiency needs improvement?)
*   (Prioritize mentioning) (If `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` was triggered in Chapter 3, emphasize here: 'Notably, errors occurred on some foundational or medium-difficulty questions within mastered skill areas, suggesting potential instability in applying these concepts.')

**4. Pattern Observation**

*   (Mention Chapter 5 findings) (If `` `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` was triggered, suggest: 'Response speed on some questions early in the test was relatively fast. It is advisable to maintain a steady pace to avoid potential "`flag for review`" risks.')
*   (Mention Chapter 5 findings) (If `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` `` was triggered, suggest: 'Analysis indicates a relatively high proportion of "fast and wrong" instances, suggesting a need to focus on carefulness during problem-solving to reduce unforced errors.')

**5. Foundational Consolidation Alert**

*   (Mention Chapter 6 findings) (If any `fundamental_skill` triggered `skill_override_triggered`, state clearly: 'For the core skills [`List of triggered skills`], overall performance indicates significant room for improvement. It is recommended to prioritize systematic foundational consolidation rather than only practicing individual missed problems.')

**6. Practice Plan Presentation**

*   (Clearly and fully list all practice recommendations generated in Chapter 7)
*   (Include exemption notes, e.g., 'Skill [`Exempted Skill Name`] performance is stable; practice can be deferred.')
*   (Include focus notes, e.g., 'For practice on [`Skill Name`], recommend adjusting the proportion of `Real`/`Pure` questions...' (based on `poor_real`/`slow_pure` parameters))
*   (Ensure `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` related recommendations are prioritized or highlighted)

**7. Next Steps Guidance**

*   **Core Constraint:** All text produced in this section **must use only natural language**, translating internal **English diagnostic parameters** into easily understandable descriptions using the **English Description provided in Appendix A**. Never directly expose internal parameters.
*   **Guide Reflection:** (Ask questions based on the main types of diagnosed parameters, using natural language but triggered by parameters)
    *   If many `` `Q_CONCEPT_APPLICATION_ERROR` `` or `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` triggered: 'Reflecting on the incorrect [`type` or `skill`] questions, what specific math concept or formula was the sticking point? Was it a complete lack of approach, or knowing the method but applying it incorrectly?'
    *   If `` `Q_CALCULATION_ERROR` `` or `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` `` triggered: 'Are errors occurring during the calculation process, or is the calculation speed generally slow?'
    *   If many `` `Q_READING_COMPREHENSION_ERROR` `` or `poor_real` triggered: 'For the incorrect word problems, was the issue understanding the text itself, or translating the understood text into a mathematical problem? Are there specific topics or long sentences causing reading difficulty?'
    *   If `` `Q_CARELESSNESS_DETAIL_OMISSION` `` or `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` `` triggered: 'Reflecting, do you often lose points due to misreading numbers, missing conditions, or misunderstanding the question's intent?'
*   **Secondary Evidence Reference Suggestion:**
    *   *Trigger When:* You cannot accurately recall the specific reason for error, the involved knowledge point, or need more objective data to confirm a pattern.
    *   *Recommended Action:* 'To more precisely pinpoint your specific difficulties in [`Skill`/`Type`], it's recommended to review your recent practice records (e.g., 2-4 weeks pre-test), collate related incorrect questions, and identify which knowledge points or question types (referencing descriptions in **Appendix A**) repeatedly cause issues. If the sample size is insufficient, pay attention to collecting data in upcoming practice sessions for later analysis.'
*   **Qualitative Analysis Suggestion:**
    *   *Trigger When:* You are confused about the cause of errors identified in the report, or the above methods haven't clarified the root problem.
    *   *Recommended Action:* 'If you remain unclear about the reason for errors in [`Type of problem`, e.g., involving `` `Q_CONCEPT_APPLICATION_ERROR` ``], consider **providing detailed step-by-step solution processes and thought examples for 2-3 questions of that type** (text or audio recording). This allows for deeper case analysis with a consultant to identify the crux of the issue.'
*   **Auxiliary Tool Recommendation Suggestion:**
    *   *Recommendation Logic:* To help organize practice and tackle issues more effectively, here are some potentially useful tools and AI prompts:
    *   *Tool Recommendations:*
        *   If you need help classifying questions by knowledge point or type while analyzing incorrect questions or organizing practice records (as mentioned in "Secondary Evidence"), consider using **`Dustin's GMAT Q: Question Classifier`**.
        *   If the diagnosis indicates relative weakness in `Real` questions (e.g., `poor_real` or `slow_real` triggered), you can try using **`Dustin_GMAT_Q_Real-Context_Converter`** to practice converting pure math problems into application problems with real-world contexts, strengthening text comprehension and translation skills.
    *   *AI Prompt Recommendations (Based on triggered diagnostic parameters):*
        *   **If diagnosis triggers: `` `Q_FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``, `` `Q_CONCEPT_APPLICATION_ERROR` `` or `` `skill_override_triggered` ``**: 
            *   `` `Quant-related/01_basic_explanation.md` ``: Get detailed step-by-step solutions and basic logic explanations.
            *   `` `Quant-related/03_test_math_concepts.md` ``: Deepen understanding of the mathematical concepts tested and the question's angle.
        *   **If diagnosis triggers: `` `Q_EFFICIENCY_BOTTLENECK_READING` ``, `` `Q_EFFICIENCY_BOTTLENECK_CONCEPT` ``, `` `Q_EFFICIENCY_BOTTLENECK_CALCULATION` ``, `` `slow_real` ``, `` `slow_pure` `` or involves excessive calculation/thinking time**: 
            *   `` `Quant-related/02_quick_math_tricks.md` ``: Learn and practice faster calculation techniques or shortcuts.
        *   **If diagnosis triggers: `` `Q_PROBLEM_UNDERSTANDING_ERROR` ``, `` `Q_READING_COMPREHENSION_ERROR` `` (Real questions)**: 
            *   `` `Quant-related/03_test_math_concepts.md` ``: Confirm the core concept tested by the question to aid in understanding the prompt.
        *   **If diagnosis triggers: `` `Q_CARELESSNESS_DETAIL_OMISSION` ``, `` `Q_BEHAVIOR_CARELESSNESS_ISSUE` ``**: 
            *   `` `Quant-related/01_basic_explanation.md` ``: Relearn standard problem-solving steps to minimize omissions.
        *   **General Practice & Consolidation (Can supplement Chapter 7 recommendations)**: 
            *   `` `Quant-related/05_variant_questions.md` ``: Generate variations of problems to solidify specific solution methods.
            *   `` `Quant-related/06_similar_questions.md` ``: Find similar questions related to specific learning goals or incorrect problems for practice.

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
| `Q_BEHAVIOR_EARLY_RUSHING_FLAG_RISK`       | Behavioral Pattern: Early test rushing (Flag risk)                   |
| `Q_BEHAVIOR_CARELESSNESS_ISSUE`            | Behavioral Pattern: General carelessness issue (high fast-wrong rate) |
| **Comparative Performance (Real vs Pure)** |                                                                      |
| `poor_real`                                | Comparative Performance: Real question error rate significantly higher |
| `poor_pure`                                | Comparative Performance: Pure question error rate significantly higher |
| `slow_real`                                | Comparative Performance: Real question overtime rate significantly higher |
| `slow_pure`                                | Comparative Performance: Pure question overtime rate significantly higher |
| **Skill Level Override**                   |                                                                      |
| `skill_override_triggered`                 | Skill Override: A core skill requires foundational consolidation (error/overtime rate > 50%) |

(End of document)