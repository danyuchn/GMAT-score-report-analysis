# **Chapter 0: Core Input Data and Configuration**

<aside>

**Objective:** To define all core input data structures required for subsequent analyses of the Verbal Reasoning (V) section.
**Primary Focus:** Establishing per-question data points (`question_position`, `question_time`, `is_correct`, `question_type` mapping [CR/RC], `question_difficulty` `V_b`, `question_fundamental_skill`), overall test metrics (`total_test_time`, `max_allowed_time` [fixed at 45 min], `total_number_of_questions`), and derived data (e.g., `rc_group_id`, `questions_in_group`, `group_total_time`, `average_time_per_type`, `first_third_average_time_per_type`, `rc_reading_time`, `rc_group_target_time`).
**Rationale:** The data defined in this chapter serves as the foundation for all subsequent analyses, calculations, and diagnoses. The completeness and accuracy of this data directly impact the validity of the diagnostic results.

</aside>

- **Per-Question Data:**
    - `question_position` (Question Sequence Number - used as the unique identifier)
    - `question_time` (Response Time/minutes)
    - `is_correct` (Correctness: `True`/`False`)
    - `question_type` (Question Type: `Critical Reasoning` mapped to `CR`; `Reading Comprehension` mapped to `RC`)
    - `question_difficulty` (Difficulty Value `V_b`)
    - `question_fundamental_skill` (Core Skill - e.g., `Plan/Construct`, `Identify Stated Idea`, `Identify Inferred Idea`, `Analysis/Critique`)
- **Overall Test Data:**
    - `total_test_time` (Total Response Time/minutes)
    - `max_allowed_time` (Maximum Allowed Test Time, fixed at 45 minutes)
    - `total_number_of_questions` (Total Number of Questions)
- **Derived Data (Requires Calculation or Preprocessing):**
    - `rc_group_id` (RC Passage Group Identifier)
    - `questions_in_group` (List of questions within the passage group)
    - `group_total_time` (Total response time for the RC passage group)
    - `average_time_per_type` (Average time per question type across the entire test)
    - `first_third_average_time_per_type` (Average time per question type for the first 1/3 of the test)
    - `rc_reading_time` (Estimated reading time for the RC passage group)
    - `rc_group_target_time` (Target analysis time for the RC passage group)
- **Appendix: RC Passage Group Definition**
    - All RC analysis is conducted at the passage group level.
    - A passage group refers to a consecutive set of RC questions, typically 3 or 4 questions.
    - If RC questions are interrupted by other question types, they are considered different passage groups.
    - Note: If the system detects more than 4 consecutive RC questions, manual intervention is required to verify the correct grouping.

<aside>

**Chapter Summary:** This chapter defines the core input data structure needed for all subsequent analyses, including detailed information for each question (`Position`, `Time`, `Correctness`, `Type`, `Difficulty`, `Skill`), overall test data (`Total Time`, `Total Questions`), and derived data requiring preprocessing (like `RC group information`, `average times`, `RC reading time`, `RC group target time`, etc.).

**Results Destination:** The data defined in this chapter forms the basis for calculations, analyses, and judgments in all subsequent chapters. The completeness and accuracy of this data directly affect the validity of the diagnostic results.

</aside>

---

# **Chapter 1: Overall Time Strategy and Data Validity Assessment**

<aside>

**Objective:** To evaluate the student's overall time strategy, pressure perception, pacing, and data validity in the Verbal section.
**Primary Focus:** Total time usage, end-of-test strategy, fatigue effects, time allocation per question type (`CR` vs. `RC`), and identifying invalid data (`is_invalid`) caused by pressure or fatigue.
**Rationale:** The Verbal section is time-constrained and prone to fatigue. A sound strategy and accurate time analysis are fundamental for identifying issues and improving efficiency. Identifying invalid data prevents incorrect diagnoses.

</aside>

1.  **Calculate Total Time Difference (`time_diff`)**: 
    `time_diff` = `max_allowed_time` - `total_test_time`

2.  **Determine Time Pressure Status (`time_pressure`)**: 
    - Default `time_pressure` = `False`.
    - Check end-of-test situation: Identify questions in the last 1/3 of the test (`last_third_questions`) where `question_time` < 1.0 minute (`fast_end_questions`).
    - Logic: If `time_diff` <= 3 minutes **AND** `fast_end_questions` is not empty, then set `time_pressure` = `True`.
    - **User Override:** If the user explicitly states there was little pressure, forcibly set `time_pressure` = `False`.

3.  **Set Overtime Thresholds and Rules (Based on `time_pressure`)**: 
    - **CR Overtime Threshold (`overtime_threshold_cr`)**: 
        - If `time_pressure` == `True`: `overtime_threshold_cr` = 2.0 minutes.
        - If `time_pressure` == `False`: `overtime_threshold_cr` = 2.5 minutes.
    - **RC Passage Group Target Time Rule (`rc_group_target_time`)**: 
        - If `time_pressure` == `True`: Target 6 minutes for 3-question groups; 8 minutes for 4-question groups.
        - If `time_pressure` == `False`: Target 7 minutes for 3-question groups; 9 minutes for 4-question groups.
    - **RC Individual Question Analysis Time Threshold (`rc_individual_q_threshold`)**: 2.0 minutes (Used to assess if the time spent on a single question, excluding reading time, is excessive).
    - *Note: These thresholds and rules are used later to determine if questions or groups are overtime (`overtime`, `group_overtime`, `individual_overtime`).*

4.  **RC Reading Time Preliminary Assessment (`rc_reading_time`)**: (V-specific analysis point)
    - For each RC passage group, estimate reading time: `rc_reading_time` = `question_time` of the first question in the group - average `question_time` of other questions in the group.
    - Check if reading time is potentially long:
        - Get the number of questions in the group `num_q_in_group`.
        - If (`num_q_in_group` == 3 and `rc_reading_time` > 2.0 minutes) or (`num_q_in_group` == 4 and `rc_reading_time` > 2.5 minutes), then trigger `reading_comprehension_barrier_inquiry` = `True`.
        - During report generation, if `reading_comprehension_barrier_inquiry` is triggered, the system will add the `RC_READING_COMPREHENSION_BARRIER` diagnostic parameter to the diagnostic results for tool recommendations and report display.
    - *Note: This flag suggests a potential foundational reading barrier and will be referenced in later chapter recommendations.*

5.  **Identify Invalid Data (`is_invalid`)**: 
    - **Prerequisite:** Execute invalid data identification and flagging only if `time_pressure` == `True`. If `time_pressure` == `False`, no questions are flagged as `is_invalid`.
    - **Scope:** Only examine questions in the last 1/3 of the test (`last_third_questions`).
    - **Define "Abnormally Fast Response (`abnormally_fast_response`)" Criteria (meeting any one triggers):**
        - *Criterion 1 (Suspected Skip):* `question_time` < 0.5 minutes.
        - *Criterion 2 (Absolute Rush):* `question_time` < 1.0 minutes.
        - *Criterion 3 (Relative Single Question Rush):* `question_time` < (`first_third_average_time_per_type`[question's `question_type`] * 0.5).
        - *Criterion 4 (Relative Group Rush - RC Only):* The `group_total_time` of the RC group the question belongs to < (`first_third_average_time_per_type`['RC'] * `num_q_in_group` * 0.5).
    - **Flagging Logic:** If a question within the scope (or its RC group for Criterion 4) meets **at least one** `abnormally_fast_response` criterion, **AND `time_pressure` == `True`**, then flag that question with `is_invalid` = `True`.
    - Output Diagnostic Hint: If any questions are flagged as `is_invalid`, suggest: "Possible rushing at the end; evaluate strategy appropriateness."

6.  **Other Observations and Suggestions**: 
    - Fatigue effect reminder: Fatigue is significant in Verbal.
    - Test strategy suggestion: Consider placing Verbal at the beginning of the exam or doing a reading warm-up beforehand.

7.  **Output and Summary**: 
    - Key flags generated in this chapter: `time_pressure` (Boolean), `overtime_threshold_cr` (Numeric), `rc_group_target_time` (Rule), `is_invalid` flag (for specific questions), `reading_comprehension_barrier_inquiry` flag (if triggered).

**Global Rule Application: Data Filtering and Flagging**

1.  **Apply Invalid Flag:** In subsequent analyses (e.g., error rates, difficulty performance), questions flagged as `is_invalid` = `True` should be excluded.
2.  **Flag Overtime Status (`overtime`) - RC Detailed Explanation**
    - For `CR` questions: If `question_time` > `overtime_threshold_cr`, flag `overtime` = `True`.
    - For `RC` passage groups (`group_overtime`):
        - If `group_total_time` > (`rc_group_target_time` + 1.0) minutes (where `rc_group_target_time` depends on time pressure and number of questions as defined in Chapter 1), then flag all questions within that group with `group_overtime` = `True`.
        - Explanation: This indicates the entire reading and solving process significantly exceeded the target time, affecting all questions in the group.
    - For individual `RC` questions (`individual_overtime`):
        - Calculate `adjusted_rc_time`:
            - If it's the first question in the group: `adjusted_rc_time` = `question_time` - `rc_reading_time`
            - If it's not the first question: `adjusted_rc_time` = `question_time`
        - If `adjusted_rc_time` > 2.0 minutes (i.e., exceeds `rc_individual_q_threshold`), flag the question with `individual_overtime` = `True`.
        - Explanation: This indicates that the analysis time for this specific question (excluding reading time for the first question) was too long, even if the entire group was not overtime.
    - Final `RC` Overtime Judgment (for Chapter 3 "Slow" classification): An `RC` question is considered "Slow" if it satisfies `group_overtime` == `True` OR `individual_overtime` == `True`.
3.  **Flag Suspiciously Fast (`suspiciously_fast`):**
    - For any question: If `question_time` < `average_time_per_type`[question's `type`] * 0.5, flag `suspiciously_fast` = `True`.
    - Output Diagnostic Label (to user): For questions flagged `suspiciously_fast` = `True`, suggest "Suspiciously fast response."

<aside>

**Chapter Summary:** We first calculated the total time difference and determined the overall time pressure (`time_pressure`). Based on this, we set the single-question overtime threshold for `CR` (`overtime_threshold_cr`) and the passage group target time rules for `RC` (`rc_group_target_time`). Next, we performed a V-specific preliminary assessment of `RC` reading time, flagging potential reading barriers (`reading_comprehension_barrier_inquiry`). Then, combining end-of-test answering behavior and time pressure status, we identified invalid data (`is_invalid`). Finally, general advice regarding fatigue and test strategy was provided. Global rules for flagging detailed `RC` overtime (`group_overtime`, `individual_overtime`) and `suspiciously_fast` responses were defined.

**Results Destination:** The `time_pressure` status, various overtime thresholds, and rules serve as crucial background information for subsequent analyses. Questions flagged as `is_invalid` will be filtered out in later analyses. The `reading_comprehension_barrier_inquiry` flag will guide subsequent practice recommendations and the summary report. The detailed overtime and `suspiciously_fast` flags provide input for Chapter 3 diagnostics.

</aside>

---

# **Chapter 2: Multi-Dimensional Performance Analysis**

<aside>

**Objective:** To analyze the student's accuracy performance across different difficulty levels and question types (using filtered data, excluding `is_invalid` questions).
**Primary Focus:** Evaluating accuracy based on `question_difficulty` level (Low/Mid/High) and `question_fundamental_skill` (specific skills within RC and CR).
**Rationale:** This analysis pinpoints accuracy weaknesses. Understanding whether errors concentrate in specific difficulty bands or skill areas (e.g., RC `Inference`, CR `Assumption`) is crucial for targeted diagnosis.

</aside>

1. **Difficulty Level Standardization (`question_difficulty`, denoted as `D`):**
    - If `D` ≤ -1: Difficulty Level = "Low / 505+"
    - If -1 < `D` ≤ 0: Difficulty Level = "Medium / 555+"
    - If 0 < `D` ≤ 1: Difficulty Level = "Medium / 605+"
    - If 1 < `D` ≤ 1.5: Difficulty Level = "Medium / 655+"
    - If 1.5 < `D` ≤ 1.95: Difficulty Level = "High / 705+"
    - If 1.95 < `D` ≤ 2: Difficulty Level = "High / 805+"
2. **Performance Analysis (Based on Filtered Data):**
    - **By Difficulty Level (Low, Medium, High):**
        - Calculate `num_total` and `num_errors` for `CR` and `RC` questions within each difficulty level (Low/Mid/High).
        - Calculate `error_rate` for each difficulty level (separately for CR and RC).
        - Analyze where errors are primarily concentrated across difficulty levels.
    - **By Fundamental Skill (Specific skills within RC, CR as defined in Chapter 4):**
        - Calculate `num_total` and `num_errors` for each fundamental skill.
        - Calculate `error_rate` for each skill.
        - Identify skills/question types with the highest error rates.

<aside>

**Chapter Summary:** Using the filtered valid data, we analyzed the student's accuracy performance at different difficulty levels (Low, Medium, High) and across different fundamental skills (`question_fundamental_skill` within RC and CR). By calculating error rates, we identified the difficulty bands and skill areas where errors were relatively concentrated.

**Results Destination:** The analysis results from this chapter (error concentration by difficulty and skill) provide background information for the diagnosis in Chapter 3 (e.g., assessing if a normally-timed error occurred below the mastered difficulty level) and directly guide the skill areas and difficulty levels to focus on in the practice recommendations in Chapter 7. Error rate results are also used for the skill override rule judgment in Chapter 6.

</aside>

---

# **Chapter 3: Root Cause Diagnosis and Analysis**

<aside>

**Objective:** To delve deeper and diagnose the root causes of errors or inefficiencies by integrating information on time, accuracy, difficulty, and question type, employing systematic analysis methods, incorporating student recall, secondary evidence, and qualitative analysis to generate standardized **English diagnostic parameter tags**.
**Primary Focus:** Utilizing systematic analysis methods, combined with student recall, secondary evidence, and qualitative analysis, to identify specific obstacles in `CR` and `RC`, and generating standardized **English diagnostic parameters**.
**Rationale:** Only by finding the root cause of problems can the most effective improvement strategies be formulated. Identifying specific parameters guides targeted improvement.

</aside>

1.  **Calculate Prerequisite Data (Based on Filtered Data):**
    - `average_time_per_type`[`type`] (Average response time for each `question_type`).
    - `max_correct_difficulty_per_skill`[`skill`] (Highest `question_difficulty` among correctly answered (`is_correct` == `True`) questions for each `question_fundamental_skill`).
2.  **Define Core Concepts:**
    - **Time Performance Classification (`Time Performance`):**
        - Fast (`is_relatively_fast`): `question_time` < `average_time_per_type`[question's `question_type`] * 0.75.
        - Slow (`is_slow`):
            - `CR` question: `overtime` == `True` (based on `overtime_threshold_cr` from Chapter 1).
            - `RC` question: `group_overtime` == `True` OR `individual_overtime` == `True` (based on Chapter 1 global rules).
        - Normal Time (`is_normal_time`): Neither fast nor slow.
    - **Special Focus Error (`special_focus_error`)**: 
        - *Definition*: An incorrect question (`is_correct` == `False`) whose `question_difficulty` is lower than the `max_correct_difficulty_per_skill`[`skill`] for its corresponding `question_fundamental_skill`.
        - *Flagging*: If the condition is met, flag `special_focus_error` = `True`.
        - *Priority Handling*: When generating practice recommendations in Chapter 7 and the diagnostic summary in Chapter 8, items flagged with `special_focus_error` = `True` and their corresponding diagnostic parameter (`FOUNDATIONAL_MASTERY_INSTABILITY_SFE`) and recommendations should be **listed first or specially annotated**.
3.  **Diagnostic Flow and Analysis Points (for valid data questions)**
    - Classify and diagnose based on the question's time performance (`is_relatively_fast`, `is_slow`, `is_normal_time`) and correctness (`is_correct`):
    - **1. Fast & Wrong**
        - Classification Criteria: `is_correct` == `False` AND `is_relatively_fast` == `True`.
        - Potential Causes (Diagnostic Parameters) (`CR`):
            - `` `CR_METHOD_PROCESS_DEVIATION` ``
            - `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (Specify question type)
            - `` `CR_READING_BASIC_OMISSION` ``
            - `` `BEHAVIOR_GUESSING_HASTY` `` (If time is extremely short)
        - Potential Causes (Diagnostic Parameters) (`RC`):
            - `` `RC_READING_INFO_LOCATION_ERROR` ``
            - `` `RC_READING_KEYWORD_LOGIC_OMISSION` ``
            - `` `RC_METHOD_TYPE_SPECIFIC_ERROR` `` (Specify question type)
            - `` `BEHAVIOR_GUESSING_HASTY` `` (If time is extremely short)
        - Primary Diagnostic Actions:
            - First, ask the student to recall their thought process or the specific issue encountered.
            - If the student cannot clearly recall the steps or difficulties, activate secondary evidence analysis: Review the student's recent (2 weeks to 1 month prior) records for fast-but-wrong questions under the same `question_fundamental_skill`. If the sample size is sufficient (recommend >= 10 questions), analyze the specific sub-type with the highest error rate (e.g., `CR Weaken`, `RC Inference`, refer to Chapter 4 for classification).
    - **2. Fast & Correct**
        - Classification Criteria: `is_correct` == `True` AND `suspiciously_fast` == `True` (from Chapter 1 global rules).
        - Observation and Reminder (`CR` & `RC`):
            - Usually indicates high efficiency, but may carry a risk of `` `BEHAVIOR_CARELESSNESS_ISSUE` `` (needs integration with Chapter 5 analysis).
            - Remind the student that even if answered quickly and correctly, accuracy should be ensured, especially for tricky distractors.
        - Primary Diagnostic Actions:
            - Typically no specific action needed. If Chapter 5 indicates a high overall carelessness rate, provide a reminder.
    - **3. Normal Time & Wrong** 
        - Classification Criteria: `is_correct` == `False` AND `is_normal_time` == `True`.
        - Potential Causes (Diagnostic Parameters) (`CR`):
            - `` `CR_READING_DIFFICULTY_STEM` ``
            - `` `CR_QUESTION_UNDERSTANDING_MISINTERPRETATION` ``
            - `` `CR_REASONING_CHAIN_ERROR` ``
            - `` `CR_REASONING_ABSTRACTION_DIFFICULTY` ``
            - `` `CR_REASONING_PREDICTION_ERROR` ``
            - `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` ``
            - `` `CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY` ``
            - `` `CR_AC_ANALYSIS_RELEVANCE_ERROR` ``
            - `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` ``
            - `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (Specify question type)
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered, specify the skill involved)
        - Potential Causes (Diagnostic Parameters) (`RC`):
            - `` `RC_READING_VOCAB_BOTTLENECK` ``
            - `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``
            - `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` ``
            - `` `RC_READING_DOMAIN_KNOWLEDGE_GAP` ``
            - `` `RC_READING_PRECISION_INSUFFICIENT` ``
            - `` `RC_READING_INFO_LOCATION_ERROR` ``
            - `` `RC_READING_KEYWORD_LOGIC_OMISSION` ``
            - `` `RC_LOCATION_ERROR_INEFFICIENCY` `` 
            - `` `RC_REASONING_INFERENCE_WEAKNESS` ``
            - `` `RC_AC_ANALYSIS_DIFFICULTY` ``
            - `` `RC_METHOD_TYPE_SPECIFIC_ERROR` `` (Specify question type)
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered, specify the skill involved)
        - Primary Diagnostic Actions:
            - Check the `special_focus_error` flag; if triggered, prioritize the `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` parameter.
            - Ask the student to recall the specific obstacle or reason for the error.
            - If recall is unclear or the reason is uncertain, activate secondary evidence analysis: Review recent records for normally-timed wrong questions under the same `question_fundamental_skill`. If the sample size is sufficient (recommend >= 10 questions), analyze the sub-type with the highest error rate (e.g., `CR Assumption`, `RC Main Idea`, refer to Chapter 4 for classification).
            - Trigger Qualitative Analysis: If the student cannot confirm the obstacle/error corresponding to the diagnostic parameter, and the teacher/consultant cannot narrow down to the most likely cause based on existing info, prompt the student to provide detailed solving steps, verbal walkthroughs, etc., for further analysis.
    - **4. Normal Time & Correct**
        - Classification Criteria: `is_correct` == `True` AND `is_normal_time` == `True`.
        - Observation: Usually indicates performance is as expected for this difficulty and type.
        - Primary Diagnostic Actions: No specific action needed.
    - **5. Slow & Wrong**
        - Classification Criteria: `is_correct` == `False` AND `is_slow` == `True`.
        - Potential Causes (Diagnostic Parameters) (`CR`):
            - `` `CR_READING_TIME_EXCESSIVE` ``
            - `` `CR_REASONING_TIME_EXCESSIVE` ``
            - `` `CR_AC_ANALYSIS_TIME_EXCESSIVE` ``
            - *(May also include root cause parameters from "Normal Time & Wrong", like `` `CR_REASONING_CHAIN_ERROR` ``, needs judgment based on context)*
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered, specify the skill involved)
        - Potential Causes (Diagnostic Parameters) (`RC`):
            - `` `RC_READING_SPEED_SLOW_FOUNDATIONAL` ``
            - `` `RC_METHOD_INEFFICIENT_READING` ``
            - `` `RC_LOCATION_TIME_EXCESSIVE` ``
            - `` `RC_REASONING_TIME_EXCESSIVE` ``
            - `` `RC_AC_ANALYSIS_TIME_EXCESSIVE` ``
            - *(May also include root cause parameters from "Normal Time & Wrong", like `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` ``, needs judgment based on context)*
            - `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` (If SFE triggered, specify the skill involved)
        - Primary Diagnostic Actions:
            - Check the `special_focus_error` flag; if triggered, prioritize the `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` parameter.
            - Ask the student to recall the specific obstacle: Which step took the longest?
            - If the student cannot recall the specific type or obstacle clearly, activate secondary evidence analysis: Review recent records for slow-but-wrong questions under the same `question_fundamental_skill`. If the sample size is sufficient (recommend >= 10 questions), analyze the sub-type with the highest error rate (e.g., `CR Strengthen`, `RC Detail`, refer to Chapter 4 for classification).
            - Trigger Qualitative Analysis: Same trigger conditions as for "Normal Time & Wrong".
    - **6. Slow & Correct**
        - Classification Criteria: `is_correct` == `True` AND `is_slow` == `True`.
        - Potential Causes (Diagnostic Parameters) (`CR` & `RC`):
            - `` `EFFICIENCY_BOTTLENECK_[AREA]` `` (Specify the bottleneck AREA: READING, REASONING, LOCATION, AC_ANALYSIS)
            - *(If the question's `question_difficulty` is genuinely high, being slow might be reasonable)*
        - Primary Diagnostic Actions:
            - Ask the student to recall the efficiency bottleneck: Although correct, which step took significantly longer than expected?
            - Trigger Qualitative Analysis: If the student cannot clearly identify the efficiency bottleneck, consider activating qualitative analysis to explore potential speed improvements.

4.  **Auxiliary Diagnostic Tools and Explanations**
    - **Secondary Evidence Application:**
        - Definition: Refers to the student's relevant practice records or mock test data from the two weeks to one month prior to the test.
        - Purpose: Used when the student cannot accurately recall or needs objective data for confirmation, to analyze specific weakness sub-types within a `question_fundamental_skill` for a particular performance type (fast-wrong, normal-wrong, slow-wrong). (e.g., Analyzing within CR whether `Weaken` or `Assumption` errors are more frequent; within RC, whether `Inference` or `Detail` errors dominate. Refer to Chapter 4 for classification).
        - Execution: Filter questions matching the criteria (time performance, correctness, core skill). If total count >= 10, calculate error rates for each specific sub-type to identify the highest one as a reference. If count < 10, note that its statistical significance is limited.
    - **Qualitative Analysis Trigger and Execution:**
        - Trigger Conditions: When the student cannot confirm the obstacle/error corresponding to the diagnostic parameter, and the teacher/consultant cannot narrow down the problem to one or two most likely root causes based on existing data and recall.
        - Execution: Prompt the student that they can provide more detailed problem-solving information, such as writing down or verbally explaining their thought process step-by-step, recording audio/screen capture of problem-solving, etc., for the teacher/consultant to conduct a more in-depth case analysis.

<aside>

**Chapter Summary:** This chapter combined time performance (Fast, Slow, Normal) and accuracy (Correct, Wrong) dimensions to classify each valid question. For different classifications, it listed potential standardized **English diagnostic parameters** (e.g., `` `CR_REASONING_CHAIN_ERROR` ``, `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``, `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``). Incorporating student recall, secondary evidence, and qualitative analysis trigger mechanisms, it aims to select the diagnostic conclusion from these standard parameters that best fits the student's situation. It also defined `special_focus_error` and its priority handling, and detailed the use of auxiliary diagnostic tools.

**Results Destination:** The diagnostic parameters generated in this chapter are the core basis for developing targeted practice method recommendations in Chapter 7 and are key components of the diagnostic summary report in Chapter 8 (requiring presentation in natural language based on Appendix A). The triggering of qualitative analysis provides a path for deeper investigation in ambiguous cases.

</aside>

---

# **Chapter 4: Core Skill/Question Type/Domain Reference**

<aside>

**Objective:** To provide a reference for core skills and their possible sub-question types, clarifying the specific question types within each `question_fundamental_skill` of Verbal.

**Primary Focus:** Providing detailed lists of `CR` and `RC` sub-question types, showing the correspondence between core skills and specific question types.

**Significance:** Providing a unified, clear sub-question type classification standard for error analysis (Chapter 2), cause exploration (Chapter 3), and practice suggestions (Chapter 7).

</aside>

- **Core Skills (`Fundamental Skills`)**
    - The following are the main core skills categories of Verbal:
        - `Plan/Construct`: Involves constructing, planning, or evaluating arguments/essays.
        - `Identify Stated Idea`: Identifies information explicitly stated in the text or question stem.
        - `Identify Inferred Idea`: Makes logical inferences based on existing information.
        - `Analysis/Critique`: Analyzes the structure of an argument, evaluates its effectiveness, or identifies logical errors.
- **Specific Question Type Classification**
    - The following sub-question types are categorized and their possible associations with the above core skills are noted.
    - **`CR` Question Type Classification (based on core skill reference)**
        - **`Analysis/Critique`:**
            - Weaken
            - Strengthen
            - Evaluate (`Evaluation` / `Evaluate the Argument`)
            - Logical Error (`Flaw in the Reasoning`)
            - Method of Reasoning (`Method of Reasoning` / `Argument Structure` / `Boldface`)
        - **`Plan/Construct`:**
            - Plan/Goal (`Plan` / `Goal Evaluation`)
            - Assumption
            - Explain/Resolve Paradox (`Explain` / `Resolve the Paradox`)
            - Fill in the Blank (`Complete the Passage` / `Fill in the Blank`)
            - Inference/Conclusion (`Inference` / `Conclusion`)
    - **`RC` Question Type Classification (based on core skill reference)**
        - **1. `Identify Stated Idea` / Explicit Information**
            - Main Idea (`Main Idea` / `Primary Purpose`)
            - Detail/Supporting Idea (`Supporting Idea` / `Detail` / `Specific Information`)
        - **2. `Identify Inferred Idea` / Implicit Information**
            - Inference (`Inference`)
            - Application (`Application`)
            - Tone/Attitude (`Tone` / `Attitude`)
            - Function/Purpose (`Function` / `Purpose of paragraph/sentence`)
            - Evaluation/Analogy (`Evaluation` / `Analogy`)

<aside>

**Chapter Summary:** This chapter provided a reference framework, categorizing GMAT Verbal core skills (`question_fundamental_skill`) into more specific `CR` and `RC` sub-question types.
**Outcome Destination:** This classification standard provided a unified language and structure for other chapters. It was used for summarizing error rates by skill/question type in Chapter 2, identifying specific weaknesses in Chapter 3, generating practice suggestions for specific question types in Chapter 7, and describing skill and question type performance in Chapter 8.

</aside>

---

# **Chapter 5: Special Pattern Observation and Carelessness Assessment**

<aside>

**Objective:** To observe whether response behavior relates to question position and to assess overall carelessness issues.
**Primary Focus:** Evaluating whether the student answers too quickly in the early stages of the test, and the overall proportion of "fast and wrong" responses.
**Significance:** Identifying potentially problematic pacing strategies and careless habits.

</aside>

- **Early Fast Questions:**
    - Identify questions where `question_position` <= `total_number_of_questions` / 3 AND `question_time` < 1.0 minute.
    - Output Risk Reminder: If such questions exist, trigger the parameter `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` and output the prompt: "**Note `flag for review` issue**".
- **Carelessness Rate Calculation (`carelessness_issue`):**
    - `num_relatively_fast_total` = Total number of questions in valid data meeting the "Fast" definition from Chapter 3 (`is_relatively_fast` == `True`).
    - `num_relatively_fast_incorrect` = Total number of questions in valid data where `is_relatively_fast` == `True` AND `is_correct` == `False`.
    - If `num_relatively_fast_total` > 0, calculate `fast_wrong_rate` = `num_relatively_fast_incorrect` / `num_relatively_fast_total`.
    - If `fast_wrong_rate` > 0.25, then flag `carelessness_issue` = `True`.
- **Output Diagnostic Parameter:** If `carelessness_issue` = `True`, trigger the parameter `` `BEHAVIOR_CARELESSNESS_ISSUE` ``.

<aside>

**Chapter Summary:** We checked for excessively fast responses in the initial part of the test (triggering `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` if found) and assessed potential carelessness (`carelessness_issue`, triggering `` `BEHAVIOR_CARELESSNESS_ISSUE` `` if criteria met) by calculating the proportion of "fast and wrong" questions among all "fast" questions (`fast_wrong_rate`), based on the relative time standard from Chapter 3.

**Results Destination:** The parameters triggered in this chapter (`` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` ``, `` `BEHAVIOR_CARELESSNESS_ISSUE` ``) provide additional insights into the student's test-taking strategy and habits. **After translation via Appendix A**, they will be incorporated as supplementary conclusions in the Chapter 8 summary report and may prompt the student to reflect on their pacing and attention to detail.

</aside>

---

# **Chapter 6: Foundational Ability Override Rules**

<aside>

**Objective:** To check if any **non-exempted** fundamental skill (across RC and CR) presents widespread and severe difficulty for the student (using filtered data).
**Rationale:** Similar to Q, if a student struggles significantly across an entire skill domain (e.g., all types of CR `Assumption` questions), recommendations focused on individual difficult problems within that skill may be less effective than first consolidating the foundational understanding and application of that skill. This serves as a pre-check before detailed, case-based recommendations.

</aside>

**Added: Fundamental Skill Exemption Rule**

<aside>

**Objective:** To identify fundamental skills (`fundamental_skill`) that the student has **fully mastered in this test** and can complete stably within the time limit, to avoid generating unnecessary practice recommendations in Chapter 7.

</aside>

- **Exemption Condition Calculation (Calculated independently for each `fundamental_skill` before the override rule check):**
    - For a specific core skill (`question_fundamental_skill`):
        - Filter all valid questions belonging to this skill (excluding those with `is_invalid` = `True`).
        - **Condition 1 (100% Accuracy):** All these valid questions **must have** `is_correct` == `True`.
        - **Condition 2 (100% Efficiency):**
            - For all `CR` questions under this skill: their `overtime` flag **must all be** `False`.
            - For all `RC` questions under this skill: their `group_overtime` and `individual_overtime` flags **must all be** `False`.
    - If **both** Condition 1 and Condition 2 are **fully met**, then the calculated exemption status for this core skill (`skill_exemption_status`) is `True`.
- **Impact of Exemption Rule:**
    - The calculated `skill_exemption_status` (True or False) will be passed on.
    - This exemption status **is only used** in the Chapter 7 practice recommendation generation logic: skills marked as `True` will **completely skip** the generation of any related practice recommendations.
    - This exemption status **does not affect** the calculation logic of the subsequent "Foundational Ability Override Rules Judgement" step in this chapter (i.e., the override rule check is still based on the original error rates of all skills, regardless of their exemption status).
    - The diagnostic summary (Chapter 8) will explicitly mention these exempted skills to highlight the student's strengths.

---

**Foundational Ability Override Rules Judgement (Based on all skills, calculation is unaffected by exemption status)**

1. **Calculate Performance Rates per Skill (Based on Filtered Data):**
    - **(This calculation covers all core skills for a comprehensive assessment. Exemption status only affects downstream recommendation generation, not the error rate calculation here)**
    - For each `question_fundamental_skill` (`S`) (using the skill lists from Chapter 0):
        - Calculate `num_total_skill`, `num_errors_skill`.
        - Calculate `error_rate_skill` = `num_errors_skill` / `num_total_skill` (if `num_total_skill` > 0).
    - **Trigger Condition (`skill_override_triggered`):** If for a skill `S`, `error_rate_skill` > 0.50 (i.e., > 50%):
        - Flag `skill_override_triggered`[`S`] = `True`.

**Impact:** If triggered for a skill `S`, **and** that skill is **not exempted** (`skill_exemption_status` is `False`), the practice recommendations in Chapter 7 will focus on foundational consolidation for that skill, rather than addressing individual errors within it.

<aside>

**Chapter Summary:** This chapter first defined how to calculate the exemption status for core skills (100% correct and no overtime). Then, independent of the exemption status, it established an override rule by examining the overall error rate for each `question_fundamental_skill` to identify skills with extremely poor performance (error rate > 50%), recording this in `skill_override_triggered`.

**Results Destination:** The calculated `skill_exemption_status` will be passed to Chapter 7 to skip recommendations for mastered skills. The `skill_override_triggered` flag will also be passed to Chapter 7 to guide the generation of macro-level recommendations for non-exempted weak skills.

</aside>

---

# **Chapter 7: Practice Planning and Recommendations**

<aside>

**Objective:** To generate specific, actionable practice recommendations based on the analysis results from all previous steps.
**Primary Focus:** Consolidating findings from error analysis (Chapter 3), efficiency bottlenecks (Chapter 3, slow & correct), and skill override checks (Chapter 6) to create specific (difficulty `Y`, time limit `Z`) or macro practice tasks for relevant fundamental skills. Applying exemption rules for stable skills.
**Rationale:** This chapter translates the diagnostic insights into a concrete improvement plan, providing targeted practice addressing specific weaknesses in content, difficulty, and timing.

</aside>

*Note: Recommendation generation relies on results from preceding chapters, including but not limited to: `question_fundamental_skill` (`S`), `question_difficulty` (`D`), `question_time` (`T`), `overtime`/`group_overtime`/`individual_overtime` flags, `skill_override_triggered` flag, `skill_exemption_status`, difficulty level definitions, `RC` target time rules, etc., all adhering to the current version's definitions.*

1.  **Practice Materials and Scope Recommendation**
    - Core materials: OG, OV (Official Guide & Verbal Review).
    - Supplementary practice: GMAT Club platforms (for filtering specific difficulty/type).
2.  **Recommendation Generation Logic**
    - **Helper Function Definition (Conceptual):**
        - `floor_to_nearest_0.5`(`value`): Rounds the input `value` down to the nearest multiple of 0.5.
    - **Prerequisite Calculations:**
        - Initialize a dictionary `recommendations_by_skill` = `{}`.
        - Initialize a set `processed_override_skills` = `set()`.
    - **Iterate Through Questions:** Examine all valid data questions `X` flagged for attention in preceding analyses (with skill `S`, difficulty `D`, original time `T`, type `Type`).
        - **Check Skill Exemption Status:**
            - If skill `S` has `skill_exemption_status` == `True` (calculated based on the added exemption rule), **skip** further recommendation steps for this question and proceed to the next.
        - **Check for Macro Recommendation (Only for non-exempted skills):**
            - If `skill_override_triggered`[`S`] is `True` AND skill `S` is **not** in `processed_override_skills`:
                - Generate macro recommendation `G` = "For skill [`S`], due to a high overall error rate (based on Chapter 6 analysis), recommend comprehensive foundational consolidation. Start systematic practice with medium-low difficulty questions, focusing on core methods."
                - Add `G` to `recommendations_by_skill`[`S`].
                - Add `S` to `processed_override_skills`.
        - **Generate Case Recommendation (if skill S did not trigger macro):**
            - **Determine Practice Difficulty (`Y`):**
                - **[Modified]** Identify all valid data questions flagged for attention under skill `S`.
                - **[Modified]** Determine the **minimum** difficulty value (`min_difficulty`) among these questions.
                - **[Modified]** Map `min_difficulty` to the **6-level standard** to determine the **overall practice difficulty** `Y` for this skill:
                    - If `min_difficulty` ≤ -1: `Y` = "Low / 505+"
                    - If -1 < `min_difficulty` ≤ 0: `Y` = "Medium / 555+"
                    - If 0 < `min_difficulty` ≤ 1: `Y` = "Medium / 605+"
                    - If 1 < `min_difficulty` ≤ 1.5: `Y` = "Medium / 655+"
                    - If 1.5 < `min_difficulty` ≤ 1.95: `Y` = "High / 705+"
                    - If 1.95 < `min_difficulty` ≤ 2: `Y` = "High / 805+"
            - **Determine Starting Practice Time Limit `Z` (minutes):** (**Unified Calculation Rule**)
                - **[Modified]** For **each** valid data question `X` flagged for attention under skill `S` (original time `T`, type `Type`), individually calculate its recommended time limit `Z_individual`:
                    - Set target time (`target_time`):
                        - If `Type` == 'CR': `target_time` = 2.0
                        - If `Type` == 'RC': `target_time` = 1.5 (single question analysis target)
                    - Check if slow (`is_slow`): (`CR`: `overtime` == `True`; `RC`: `group_overtime` == `True` or `individual_overtime` == `True`)
                    - Calculate `base_time`: If `is_slow` == `True`, then `T` - 0.5, else `T`.
                    - Calculate `Z_raw` = `floor_to_nearest_0.5`(`base_time`).
                    - Ensure minimum value: `Z_individual` = `max`(`Z_raw`, `target_time`).
                - **[Added]** **Aggregate Time Limit:** Determine the final starting practice time limit `Z` for skill `S` by taking the **maximum** value (`max_z_minutes`) among all calculated `Z_individual` times for that skill.
            - **Construct Recommendation Text:**
                - Base template: "For relevant topics under skill [`S`] (identified based on Chapter 3 diagnosis), recommend practicing [`Y`] difficulty questions. Suggested starting time limit is [`Z`] minutes. (Final target time: CR 2 min / RC 1.5 min)."
                - **Priority Annotation:** If any question under this skill triggered `special_focus_error` = `True`, prefix this recommendation with "*Fundamental mastery unstable*" .
                - **Excessive Time Alert:** If `Z` - `target_time` > 2.0 minutes, append the alert: "**Note: Starting time limit significantly exceeds target; substantial practice volume is needed to ensure gradual time reduction is effective.**"
            - Add case recommendation `C` to `recommendations_by_skill`[`S`].
3.  **Collate and Output Recommendation List:**
    - Initialize `final_recommendations`.
    - **Process Aggregated Recommendations:** Iterate through `recommendations_by_skill`.
        - For each skill `S` and its list `skill_recs`:
            - If list is not empty:
                - Add collated recommendations for skill `S` to `final_recommendations`.
    - **Final Output:** Output `final_recommendations`, ensuring aggregation by skill and prioritization of `special_focus_error` recommendations.

<aside>

**Chapter Summary:** This chapter utilized analysis results from all preceding chapters (diagnostic parameters, difficulty performance, time flags, skill error rates, override triggers, exemption status, reading barrier flags) to generate a personalized practice plan. It distinguishes between macro (foundational consolidation) and case-specific recommendations, specifying practice scope, difficulty (Y/Y_agg), starting time limits (Z), and final target times. Recommendations related to `special_focus_error` are prioritized. If foundational reading issues were indicated, relevant training suggestions are triggered.

**Results Destination:** The complete practice plan generated here forms the core action plan of the entire diagnostic process, presented directly to the student and constituting the most crucial "Next Steps" component of the Chapter 8 summary report.

</aside>

---

# **Chapter 8: Diagnostic Summary and Next Steps**

<aside>

**Objective:** To synthesize the analysis results and generate a comprehensive, easy-to-understand natural language diagnostic report **(using English descriptions from Appendix A for internal parameters)**.
**Primary Focus:** Integrating key findings, practice recommendations, and guiding student reflection.
**Significance:** Providing an overall perspective and guiding improvement efforts.

</aside>

**1. Opening Summary**

*   (Summarize Chapter 1 findings: Did the student experience significant time pressure during this Verbal test? How was the overall pacing? Were there signs of rushing at the end due to time pressure potentially affecting data validity? The fatigue effect in the Verbal section is notable; consider strategic adjustments like placing Verbal first or doing a pre-test reading warm-up.)

**2. Performance Overview**

*   (Summarize Chapter 2 findings: How did the student perform on `CR` and `RC` questions across different difficulty levels (Low/Medium/High)? Which difficulty levels showed concentrated errors? Which core skills (`question_fundamental_skill`) are relative weaknesses?)
*   **(Mention which core skills were exempted due to perfect performance (100% correct and no overtime), showcasing them as mastered strengths.)**
*   (Mention the preliminary `RC` reading time assessment from Chapter 1. If `reading_comprehension_barrier_inquiry` was triggered, note here or in core problem diagnosis that potential foundational reading barriers require attention.)

**3. Core Problem Diagnosis**

*   (Summarize key findings from Chapter 3 in natural language: **Based on the diagnostic parameters generated (e.g., `` `CR_REASONING_CHAIN_ERROR` ``, `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``), use their English descriptions from Appendix A.** Explain the most common error types and reasons in `CR` and `RC`.)
*   (Prioritize Mention) (If the diagnosis includes `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``, emphasize here: "*Of particular note, errors occurred on some foundational or medium-difficulty questions within mastered skill areas, indicating potential instability in applying these concepts or skills.*")

**4. Pattern Observation**

*   (Mention Chapter 5 findings) (If the parameter `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` was triggered based on Ch 5): "*Some questions at the beginning of the test were answered relatively quickly. It's advisable to maintain a steady pace to avoid potential 'flag for review' risks.*")
*   (Mention Chapter 5 findings) (If the parameter `` `BEHAVIOR_CARELESSNESS_ISSUE` `` was triggered based on Ch 5): "*Analysis shows a higher proportion of 'fast and wrong' instances, suggesting a potential need to focus on carefulness during problem-solving to reduce unforced errors.*")

**5. Foundational Consolidation Hint**

*   (Mention Chapter 6 findings) (If any `fundamental_skill` triggered `skill_override_triggered`): "*For the following core skill(s): [`List of skills triggering override`], overall performance indicates significant room for improvement. It is recommended to prioritize systematic foundational consolidation rather than focusing solely on individual missed questions within these areas.*")

**6. Practice Plan Presentation**
*   (Clearly and completely list the **Practice Plan** generated in Chapter 7, aggregated by skill.)
*   (The plan includes: **Macroscopic Recommendations** for skills triggering the override rule, and **Case-Specific Recommendations** for other identified issues.)
*   (Case-specific recommendations specify the skill/topic, recommended **Practice Difficulty (Y)**, **Starting Practice Time Limit (Z)**, and the final target time.)
*   (In the plan, recommendations related to `special_focus_error` (corresponding to parameter `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` ``) will be **prioritized or specially annotated** (e.g., with "*Fundamental mastery unstable*").)
*   (The plan includes relevant **Excessive Time Alerts (Volume Alerts)**, indicating the need for sufficient practice volume.)
*   (If foundational reading ability training was recommended, it will be integrated here.)

**7. Next Steps Guidance**

*   **Core Constraint:** The report **must be presented entirely in natural language** to the student. Internal **English diagnostic parameters** are translated into easy-to-understand descriptions using the **English Description column in Appendix A**, never exposed directly.
*   **Guide Reflection:** (Ask questions based on the main diagnosed problem types, using natural language)
    *   `CR` Related: "*Reflecting on the CR questions you missed, was it difficulty understanding the logical relationships in the stem, or were the answer choices hard to eliminate? Which question types (Weaken, Strengthen, Assumption, etc.) seemed more challenging?*"
    *   `RC` Related: "*Thinking about the RC questions you missed, was the main issue not understanding the passage, misinterpreting the question, or locating the information but misunderstanding it? Did you encounter difficulties with specific topics or passage structures? Are there noticeable bottlenecks in foundational reading (vocabulary, complex sentences)?*"
*   **Secondary Evidence Reference Suggestion:**
    *   *Trigger*: When you cannot accurately recall specific error reasons, involved skill weaknesses, or question types, or when you need more objective data to confirm patterns.
    *   *Suggested Action*: "*To more precisely pinpoint your specific difficulties in [`Specific Skill/Type`], review your recent practice records (e.g., 2-4 weeks pre-test). Compile relevant missed questions and identify recurring issues related to specific skill points, question types, or error categories (refer to descriptions in **Appendix A**).*"
*   **Qualitative Analysis Suggestion:**
    *   *Trigger*: When you are unsure about the root causes identified in the diagnostic report, especially for complex logical reasoning or reading comprehension processes, or when the methods above still don't clarify the fundamental issue.
    *   *Suggested Action*: "*If you remain unsure about the reasons for errors in [`Type of Problem`, e.g., CR logical chain analysis or RC inference processes], try providing **detailed walkthroughs for 2-3 examples of that question type** (can be written notes or audio recording). This allows for a deeper case analysis with your consultant to identify the core issue.*"
*   **Auxiliary Tool Recommendation Suggestion:**
    *   *Recommendation Logic*: To more effectively address the issues identified in the diagnosis, the system will recommend potentially suitable auxiliary learning tools based on your specific situation. Only the tools most relevant to your diagnostic results will be listed in the final report, described in natural language.
    *   *Diagnosis-to-Tool Mapping Rules*: (This list covers all diagnostic parameters defined in Appendix A and their corresponding tool/prompt recommendations)
        *   **If diagnosis involves CR reasoning or specific type difficulty (based on Chapter 3 parameters):**
            *   If includes `` `CR_REASONING_CHAIN_ERROR` `` or `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` `` → May recommend external tools **`Dustin_GMAT_CR_Core_Issue_Identifier`** or **`Dustin_GMAT_CR_Chain_Argument_Evaluation`**; or use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` `` (for `` `CR_REASONING_CHAIN_ERROR` ``) or `` `Verbal-related/01_basic_explanation.md` `` (for `` `CR_REASONING_CORE_ISSUE_ID_DIFFICULTY` ``).
            *   If includes `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (e.g., Boldface) → May recommend external tool **`Dustin's GMAT CR: Boldface Interactive Tutor`**; or use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``.
            *   If includes `` `CR_METHOD_TYPE_SPECIFIC_ERROR` `` (e.g., Argument Construction) or involves weak argument structure analysis → May recommend external tool **`Dustin_GMAT_CR_Role_Argument_Construction`**; or use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``.
            *   If includes `` `CR_REASONING_ABSTRACTION_DIFFICULTY` `` or unclear basic logic concepts → May recommend external tool **`Dustin's GMAT Tool: Textbook Explainer`**; or use AI prompts: `` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``.
            *   If includes `` `CR_READING_BASIC_OMISSION` `` → May use AI prompt: `` `Verbal-related/01_basic_explanation.md` ``.
            *   If includes `` `CR_READING_DIFFICULTY_STEM` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/09_complex_sentence_rewrite.md` ``.
            *   If includes `` `CR_READING_TIME_EXCESSIVE` `` → May use AI prompts: `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `CR_QUESTION_UNDERSTANDING_MISINTERPRETATION` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``.
            *   If includes `` `CR_REASONING_PREDICTION_ERROR` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``.
            *   If includes `` `CR_REASONING_TIME_EXCESSIVE` `` → May use AI prompts: `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``.
            *   If includes `` `CR_AC_ANALYSIS_UNDERSTANDING_DIFFICULTY` `` → May use AI prompts: `` `Verbal-related/07_logical_term_explained.md` ``, `` `Verbal-related/01_basic_explanation.md` ``.
            *   If includes `` `CR_AC_ANALYSIS_RELEVANCE_ERROR` `` → May use AI prompts: `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``.
            *   If includes `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``.
            *   If includes `` `CR_AC_ANALYSIS_TIME_EXCESSIVE` `` → May use AI prompts: `` `Verbal-related/02_quick_cr_tpa_tricks.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``.
            *   If includes `` `CR_METHOD_PROCESS_DEVIATION` `` → May use AI prompts: `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/06_boldface_SOP.md` ``.

        *   **If diagnosis involves RC reading comprehension barriers (based on Chapter 3 parameters or Chapter 1 `reading_comprehension_barrier_inquiry` trigger):**
            *   If includes `` `RC_READING_SPEED_SLOW_FOUNDATIONAL` `` or `rc_reading_time` estimate is long → May recommend external tool **`Dustin GMAT: Chunk Reading Coach`**; or use AI prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `RC_READING_SENTENCE_STRUCTURE_DIFFICULTY` ``, `` `RC_READING_DOMAIN_KNOWLEDGE_GAP` `` or `` `RC_READING_VOCAB_BOTTLENECK` `` (and not systematic learning) → May recommend external tool **`Dustin's GMAT Terminator: Sentence Cracker`**; or use targeted AI prompts: `` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` `` (for vocab); `` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` `` (for sentence structure); `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/08_source_passage_rewrite.md` `` (for domain knowledge).
            *   If includes `` `RC_READING_VOCAB_BOTTLENECK` `` (and systematic learning needed) → May recommend external tool **`Dustin's GMAT Core: Vocab Master`**; can also use AI prompts: `` `Verbal-related/09_complex_sentence_rewrite.md` ``, `` `Verbal-related/01_basic_explanation.md` ``.
            *   If includes `` `RC_READING_PRECISION_INSUFFICIENT` `` → May recommend external tool **`Dustin GMAT Close Reading Coach`**; or use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `RC_READING_PASSAGE_STRUCTURE_DIFFICULTY` `` → May recommend external tool **`Dustin_GMAT_RC_Passage_Analyzer`**; or use AI prompts: `` `Verbal-related/04_mindmap_passage.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `RC_READING_INFO_LOCATION_ERROR` `` → May use AI prompts: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``.
            *   If includes `` `RC_READING_KEYWORD_LOGIC_OMISSION` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `RC_METHOD_INEFFICIENT_READING` `` → May use AI prompts: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``.
            *   If includes `` `RC_QUESTION_UNDERSTANDING_MISINTERPRETATION` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``.
            *   If includes `` `RC_LOCATION_ERROR_INEFFICIENCY` `` → May use AI prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``.
            *   If includes `` `RC_LOCATION_TIME_EXCESSIVE` `` → May use AI prompts: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/04_mindmap_passage.md` ``.
            *   If includes `` `RC_REASONING_INFERENCE_WEAKNESS` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``.
            *   If includes `` `RC_REASONING_TIME_EXCESSIVE` `` → May use AI prompts: `` `Verbal-related/03_quick_rc_tricks.md` ``, `` `Verbal-related/05_evaluate_explanation.md` ``.
            *   If includes `` `RC_AC_ANALYSIS_DIFFICULTY` `` → May use AI prompts: `` `Verbal-related/01_basic_explanation.md` ``, `` `Verbal-related/07_logical_term_explained.md` ``.
            *   If includes `` `RC_AC_ANALYSIS_TIME_EXCESSIVE` `` → May use AI prompt: `` `Verbal-related/03_quick_rc_tricks.md` ``.

        *   **If diagnosis involves answer choice elimination difficulty or carelessness (based on Chapter 3/5 parameters):**
            *   If includes `` `CR_AC_ANALYSIS_DISTRACTOR_CONFUSION` ``, `` `RC_AC_ANALYSIS_DIFFICULTY` `` or `` `BEHAVIOR_CARELESSNESS_ISSUE` `` → May recommend external tool **`Dustin_GMAT_Verbal_Distractor_Mocker`**; or for `` `BEHAVIOR_CARELESSNESS_ISSUE` `` use AI prompts: `` `Verbal-related/05_evaluate_explanation.md` ``, `` `Verbal-related/01_basic_explanation.md` ``.
        *   **If diagnosis includes foundational mastery issues (based on Chapter 3 parameters):**
            *   If includes `` `FOUNDATIONAL_MASTERY_INSTABILITY_SFE` `` → Prioritize using AI prompt: `` `Verbal-related/01_basic_explanation.md` `` to consolidate foundations.
        *   **If diagnosis includes efficiency issues (based on Chapter 3 parameters):**
            *   If includes `` `EFFICIENCY_BOTTLENECK_[AREA]` `` → Refer to AI prompts for the corresponding `[AREA]` and additionally use `` `Verbal-related/02_quick_cr_tpa_tricks.md` `` (CR) or `` `Verbal-related/03_quick_rc_tricks.md` `` (RC).
        *   **If diagnosis includes behavioral pattern issues (based on Chapter 5 parameters):**
            *   If includes `` `BEHAVIOR_EARLY_RUSHING_FLAG_RISK` `` → May use AI prompt: `` `Verbal-related/05_evaluate_explanation.md` `` to reflect on pacing.
            *   If includes `` `BEHAVIOR_GUESSING_HASTY` `` → May use AI prompt: `` `Verbal-related/01_basic_explanation.md` `` to learn complete steps.
        *   **If comprehensive review, categorized practice, or simulation needed (based on overall recommendations from Ch 2, 3, 6, 7):**
            *   (Trigger condition is general, based on overall practice plan) → May recommend external tools: **`GMAT - Terminator (CR Review)`**, **`GMAT - Terminator (RC Review)`**, **`Dustin's GMAT RC: Question Classifier`**, **`Dustin_GMAT_CR_Question_Classifier`**, **`Dustin_GMAT_CR_Question_Simulator`**, **`Dustin_GMAT_RC_Question_Simulator`**, **`Dustin_GMAT_Time_Analyst (CR & RC)`**, **`Dustin_GMAT_Review_Assistant (CR & RC)`**, **`Dustin_GMAT_RC_Preparatory_Answer_Trainer`**.
    *   *Final Presentation*: In the final diagnostic report provided to you, based on your specific diagnostic results, we will use the **English Description column in Appendix A** to explain the recommended tools and their use cases in natural language.

<aside>

**Chapter Summary:** This chapter served as the final output synthesis, integrating analysis findings from all preceding chapters (time pressure, invalid data, difficulty/skill performance, **English parameter-based** root cause diagnosis, special pattern observations, `RC` reading assessment, etc.) and the complete practice plan from Chapter 7 into a comprehensive, easy-to-understand natural language diagnostic report **(using English descriptions from Appendix A for internal parameters)**. The report highlights Verbal fatigue factors and potential foundational reading issues. It also includes guided reflection questions, suggestions for qualitative analysis and secondary evidence reference, and personalized tool recommendations based on diagnostic parameters.

**Results Destination:** This is the final product delivered to the student, aiming to provide deep insights into their Verbal performance and clearly outline the direction and specific action steps for improvement.

</aside>

---

# **Appendix A: Diagnostic Parameter Tags and Descriptions**

| English Parameter                          | Chinese Description (中文描述)                         |
|--------------------------------------------|----------------------------------------------------|
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
| `RC_METHOD_TYPE_SPECIFIC_ERROR`               | RC 方法應用: 特定題型方法錯誤/不熟 (需註明題型)       |
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
| `BEHAVIOR_EARLY_RUSHING_FLAG_RISK`            | 行為模式: 前期作答過快 (< 1.0 min, 注意 flag for review 風險) |
| `BEHAVIOR_CARELESSNESS_ISSUE`                 | 行為模式: 粗心問題 (快而錯比例 > 25%)                    |
| `BEHAVIOR_GUESSING_HASTY`                     | 行為模式: 過快疑似猜題/倉促                     |

(End of document)