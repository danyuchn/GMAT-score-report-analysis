# GMAT Diagnostic Platform User Tutorial

## Foreword: Welcome to the GMAT Diagnostic Platform!

Hello! Welcome to the GMAT Diagnostic Platform. Whether you are a student preparing for the GMAT or a GMAT instructor guiding students, this tool aims to provide you with strong support.

**The goals of this platform are to:**

*   **Go Beyond Scores:** We don't just look at how many questions you answered correctly; we strive to deeply analyze the patterns and reasons behind your performance in each GMAT section (Quantitative, Verbal, Data Insights).
*   **Gain Detailed Performance Insights:** Through data analysis, identify your strengths and weaknesses in specific question types, knowledge points, skill applications, as well as potential time management issues or unstable concept mastery (e.g., Special Focus Errors, SFE).
*   **Obtain Personalized Recommendations:** Based on scientific diagnostic results, provide specific learning directions and practice suggestions. If an OpenAI API is configured, you can also receive AI-assisted report summaries and learning strategies.
*   **Enhance Study/Teaching Efficiency:** Make learning and coaching more targeted, investing valuable time in areas most in need of improvement.

**Key Features at a Glance:**

*   **Convenient Data Input:** Supports direct pasting or uploading of CSV-formatted question-by-question response data.
*   **Comprehensive Diagnostic Analysis:** Detailed performance evaluation for the three main sections: Quantitative (Q), Verbal (V), and Data Insights (DI).
*   **IRT (Item Response Theory) Analysis:** Estimates your relative ability level (Theta score) and the relative difficulty of each question.
*   **Time Pressure Assessment:** Analyzes your answering speed and time allocation to identify potential time pressure problems.
*   **Invalid Data Identification:** Helps flag invalid response data points due to time pressure or guessing, ensuring the accuracy of the analysis.
*   **AI-Assisted Summary & Q&A (Requires OpenAI API Key):** Automatically generates easy-to-understand diagnostic report summaries, learning recommendations, and enables interactive Q&A based on your report content.
*   **Detailed Reports & Data Export:** Provides clear charts, detailed question-by-question analysis tables, and supports exporting results to Excel files.

---

## Important: Before You Begin, Prepare Your Score Report Data

**"The quality of data is the cornerstone of an accurate diagnosis!"** To enable the platform to provide the most effective analysis, please ensure you prepare data that meets the format requirements.

**1. Required Data Fields:**

You need to prepare a question-by-question record of your responses (usually exportable from your mock test platform or manually organized) containing the following information:

*   `Question` (or a similar "Question Number" field)
*   `Response Time (Minutes)` (or a similar "Response Time" field, in minutes)
*   `Performance` (or a similar "Correct/Incorrect" field, e.g., "Correct" or "Incorrect")
*   `Content Domain` (or a similar "Content Area/Knowledge Point" field, e.g., "Algebra", "Arithmetic" for Quant; "Math Related", "Non-Math Related" for DI, etc.)
*   `Question Type` (or a similar "Question Type" field, e.g., "Problem Solving", "Data Sufficiency" for Quant; "Critical Reasoning", "Reading Comprehension" for Verbal; "Data Sufficiency", "Multi-Source Reasoning" for DI, etc.)
*   `Fundamental Skills` (or a similar "Tested Skills/Sub-topic" field, e.g., "Equations/Inequalities", "Rates/Ratios/Percentages" for Quant; "Identify Stated Idea", "Analysis/Critique" for Verbal, etc. This field can be left blank for DI.)

**2. Data Format:**

*   **Tab-Separated Values (TSV) or CSV Format:** The easiest way is to organize your data in Excel or Google Sheets, then copy and paste it directly into the platform's data input box. Ensure you only copy the data itself and the header row.
*   Alternatively, you can save your data as a CSV file and upload it.

**3. Data Integrity and Accuracy:**

*   Please ensure your data is complete and the content of each field is accurate.
*   Pay special attention that the unit for "Response Time" is **minutes**.
*   For the "Performance" field, please use "Correct" and "Incorrect" (capitalized or lowercase is usually recognizable, but consistency is recommended).

**4. 【EXTREMELY IMPORTANT】Personal Privacy and Data Anonymization:**

*   Before you upload or paste any data, **you MUST carefully review and manually remove all information that could directly or indirectly identify you personally!**
*   This information may include, but is not limited to: your name, GMAT candidate ID, test registration number, test date, test center location, email address, etc.
*   **The developers of this platform are committed to protecting user privacy, but it is your responsibility to ensure that the data you provide is anonymous.** Data collection is used solely for model optimization and academic research purposes, as detailed in the "Important Disclaimers and Terms of Use."

---

## Platform Interface Overview

This platform primarily consists of two navigation tabs:

1.  **[📥 Data Input & Analysis]**: This is where you start using the platform. It's for uploading or pasting your GMAT score data, performing initial checks, and initiating the analysis process.
2.  **[📈 View Results]**: After the analysis is complete, you can view detailed diagnostic reports, chart analyses, and AI-generated recommendations here.

Some features (like inputting the OpenAI API Key) might be located in the page's sidebar.

On the "Data Input & Analysis" page, you will find:

*   **Quick Start Guide:** Briefly explains the core operational steps.
*   **Important Disclaimers and Terms of Use:** Please read carefully before use.
*   **Subject-Specific Input Areas:** Dedicated tabs for Quantitative (Q), Verbal (V), and Data Insights (DI) for data input.
*   **Total Tab:** Allows you to input your GMAT total score and individual section scaled scores for reference information like percentiles.
*   **Analysis Button:** After data input is complete, click this button to start the analysis.

---

## 【Student Guide】GMAT Self-Diagnosis and Improvement Guide

This guide will walk you through how to use the GMAT Diagnostic Platform to analyze your performance and gain insights to improve your study efficiency.

### 1. Quick Start: My First Diagnosis

**Step 1: Navigate to the "📥 Data Input & Analysis" Page**

Upon opening the platform, this is the first page you will see.

**Step 2: Input Your Score Data for Each Section**

The platform has separate data input tabs for the three main GMAT sections: Quantitative (Q), Verbal (V), and Data Insights (DI).

*   Click on the respective section name (e.g., "Quantitative (Q)") to enter the data input area for that section.
*   **Input Methods:**
    *   **Paste Data (Recommended):**
        1.  Organize your question-by-question response data in Excel or Google Sheets (ensure it includes the required fields and correct format mentioned in the "Prepare Your Score Report Data" section).
        2.  Select the cell range containing the header row and all your data.
        3.  Copy (Ctrl+C or Cmd+C).
        4.  Return to the platform's section input area, find the text input box, and paste (Ctrl+V or Cmd+V).
    *   **Upload CSV File:**
        1.  Save your question-by-question response data as a CSV (Comma Separated Values) file.
        2.  Click the "Upload CSV File" button and select your file.
        3.  (Note the file size limit, usually a few MB. Pasting data does not have this restriction).
*   **Sample Data:** If you want to try out the platform or see the required data format, you can click the "Load Sample Data" button below each section's input area. This will automatically populate the fields with correctly formatted sample data.
*   **Repeat this process** to input data for all three sections: Q, V, and DI.

**Step 3: (Optional) Input Your Target or Actual Total Score Information in the "Total" Tab**

*   Click on the "Total" tab.
*   Use the sliders to select your GMAT Total Score (205-805) and the Scaled Scores (60-90) for Q, V, and DI sections.
*   Click "Confirm Score Settings." This information is mainly used to display corresponding percentile rankings and score distribution charts on the results page and does not directly participate in the detailed question-by-question diagnosis.

**Step 4: Review Data Preview and Adjust "Invalid Question" Markings**

*   In each section's data input area, after you paste or upload data, a preview table of your data will usually appear below.
*   **Carefully review** the preview to ensure fields are correctly mapped and data is read without errors.
*   **Mark Invalid Questions (Very Important):**
    *   "Invalid questions" refer to those that do not accurately reflect your current ability level, such as:
        *   Questions answered hastily or guessed randomly due to extreme time pressure.
        *   Questions that were completely skipped or answered without reading.
        *   Questions answered incorrectly due to operational errors (e.g., misclicking an option).
    *   The system will **automatically suggest** some potentially invalid questions based on your response time and other factors (e.g., very quickly answered incorrect questions).
    *   In the data preview table, there is usually a column named `is_manually_invalid` (or similar "Manually Mark as Invalid") with checkboxes.
    *   **Please make sure to check the boxes for questions you believe were invalid responses based on your actual experience. Your manual markings will take precedence over the system's automatic suggestions.**
    *   Accurately marking invalid questions helps the platform assess your true abilities more precisely.

**Step 5: (Strongly Recommended) Enter Your OpenAI API Key in the Sidebar**

*   Find the "OpenAI API Key" input box in the page's sidebar (usually on the left, may need to be expanded).
*   If you have an OpenAI API Key, please enter it here.
*   **Why is this needed?** By providing an API Key, the platform can leverage powerful GPT models to:
    *   Generate a concise and easy-to-understand **AI Summary Report** for you, highlighting your main strengths, weaknesses, and core issues.
    *   Provide more specific, personalized **learning recommendations**.
    *   Enable the **AI Chat feature** on the results page, allowing you to ask questions based on your diagnostic report.
*   **What if I don't have an API Key?** No problem! You will still receive a complete and detailed quantitative analysis report and charts. The AI features are enhancements to help you understand the report more quickly.
*   *(Note: Please ensure your API Key has sufficient quota and is active. Use of the API Key may incur costs charged by OpenAI.)*

**Step 6: Click the Red "Start Analysis" Button**

*   Once you have confirmed that all data for all sections has been correctly entered and reviewed, click the "Start Analysis" button located at the bottom of the "Data Input & Analysis" page.
*   The analysis process may take some time (from a few seconds to a minute, depending on data volume and computational complexity). You will see a progress bar indicating the current analysis progress. Please wait patiently.

### 2. Interpreting Your Diagnostic Report: The "📈 View Results" Page

After the analysis is complete, the system will automatically switch to (or you can manually click on) the "📈 View Results" tab. This is where all the detailed diagnostic results of your GMAT performance are compiled.

**A. AI Summary Report (If API Key was provided)**

*   The top of the page will usually display the **"Consolidated Diagnostic Report"** generated by AI.
*   This report will use plain language to summarize your main performance characteristics in Q, V, and DI, potential weak areas, time management overview, and preliminary learning suggestions.
*   **Editable Diagnostic Tags:** The AI may assign some "diagnostic tags" to your performance. You can click the "Edit AI-Extracted Diagnostic Tags" button to modify, delete, or add tags in the pop-up text box to better reflect your actual situation or your instructor's judgment. Click "Apply Modified Tags" after editing.

**B. Overall Score & Percentiles (If scores were entered in the "Total" tab)**

*   If you set your total score and section scaled scores in the "Total" tab during data input, these scores will be displayed here.
*   It may also include official percentile ranking charts corresponding to these scores, allowing you to see where you stand.

**C. Detailed Section-Specific Diagnostic Results (Separate Tabs for Q, V, DI)**

Below the main results area, there will be separate tabs for the Q, V, and DI sections. Click on a section name (e.g., "Quantitative (Q)") to view the detailed analysis for that section. Each section typically includes:

*   **C1. [Section Name] Detailed Data (with Diagnostic Tags)**
    *   This is a detailed **question-by-question analysis table** showing the specifics of your performance on each question in that section.
    *   **Key Column Explanations:**
        *   `Question No. (question_position)`: The order in which you answered the question.
        *   `Question Type (question_type)`: E.g., PS, DS, CR, RC, MSR, etc.
        *   `Skill Tested (question_fundamental_skill)`: The core skill or knowledge point tested by the question (this column might be absent or show "N/A" for the DI section).
        *   `Difficulty (Simulated) (question_difficulty)`: The system's estimated relative difficulty of the question based on the IRT model (estimated for valid questions only). **Note: This is not the official GMAC difficulty, but for internal diagnostic reference.**
        *   `Time Spent (Min) (question_time)`: The time you spent answering the question (in minutes).
        *   `Time Performance (time_performance_category)`: Categorized as "Fast," "Moderate," or "Slow" based on your time compared to average performance.
        *   `Content Domain (content_domain)`: The content area the question belongs to.
        *   `Diagnostic Tags (diagnostic_params_list)`: Preliminary diagnostic tags assigned by the system based on your performance, e.g., "Over Time," "SFE (Possible)," "Low Difficulty Error," etc.
        *   `Correct? (is_correct)`: Checked if you answered the question correctly.
        *   `SFE? (is_sfe)`: Checked if the system identified the question as a possible "Special Focus Error" (i.e., a concept you might not have fully mastered, often an error on a low-to-medium difficulty question).
        *   `Marked Invalid? (is_invalid)`: Checked if the question was ultimately treated as an invalid data point (based on your manual markings during input). Invalid questions are usually excluded from core ability assessment and some diagnostics.
    *   **Table Styling:** The table will use color-coding; for example, incorrect rows might be highlighted in red for quick identification.
    *   **Data Sorting & Filtering:** You can usually click on column headers to sort the data.
    *   **Download Data:** Below the table or within the section's report block, there will be a "Download [Section Name] Detailed Data (Excel)" button. Click it to export the detailed data table for the current section as an Excel file, convenient for offline viewing or sharing with your instructor.

*   **C2. [Section Name] Ability (Theta) Trend Chart**
    *   This is a line chart showing the **trend of your estimated relative ability (Theta) value** as you progressed through the questions in that section.
    *   The horizontal axis is the question number sequence, and the vertical axis is the Theta value.
    *   **How to interpret the Theta chart?**
        *   **Overall Level:** Higher Theta values indicate stronger performance in that section.
        *   **Trend Changes:**
            *   Stable or upward trend: Usually indicates you maintained a good state and performance throughout the test.
            *   Downward trend: May indicate fatigue, the impact of time pressure, or a drop in confidence after encountering consecutive difficult questions, leading to a decline in later performance.
            *   Significant fluctuations: May indicate inconsistent performance.
        *   **Combine with Question Difficulty:** While this chart doesn't directly show question difficulty, you can cross-reference it with the "Difficulty (Simulated)" column in the detailed data table above to get a sense of at which difficulty ranges your Theta value changed significantly.

*   **C3. [Section Name] Detailed Diagnostic Report**
    *   This is a **detailed textual analysis report** for the section, generated by the system's diagnostic modules.
    *   Content may include:
        *   **Overall Performance Summary:** Accuracy rate, average time spent, SFE percentage, etc.
        *   **Time Management Analysis:** A detailed breakdown of your time allocation across different question types and difficulties, and whether there's a general pattern of being too fast or too slow.
        *   **Error Pattern Analysis:** In-depth analysis of your common errors by question type, knowledge point, and skill dimension. For example, for Quant, it might point out higher error rates in "Algebra word problems" or "complex geometry questions." For Verbal, it might analyze specific issues with "Inference questions" in RC or "Weaken questions" in CR.
        *   **SFE Analysis:** Lists characteristics of questions identified as SFEs, highlighting knowledge points that may not be solidly mastered.
        *   **Specific Recommendations:** Preliminary study and practice suggestions based on the above analyses.

**D. AI Chat Interface (If API Key was provided)**

*   Somewhere on the results page (usually below the AI summary report or in the sidebar), you will see a **chat input box**.
*   You can ask the AI questions based on your current diagnostic report, much like conversing with a chatbot.
*   **For example, you can ask:**
    *   "Based on my report, which area of math do I need to strengthen the most?"
    *   "How should I improve my Verbal pacing?"
    *   "Can you give me some practice advice for SFEs?"
    *   "Summarize my main issues in the DI section."
*   The AI will try to understand your questions and provide answers based on the content of the already generated diagnostic report.

### 3. How to Use Diagnostic Results to Improve Your GMAT Score

Getting a detailed diagnostic report is just the first step. More importantly, how can you effectively use this information to guide your subsequent studies?

*   **Pay Close Attention to "Error Pattern Analysis" and "SFE Analysis":**
    *   These two sections are the essence of the report, directly pointing out the weak links and unstable factors in your knowledge system.
    *   For common error-prone knowledge points and question types listed in the report, conduct **targeted breakthrough practice**. Don't just do new questions; review your mistakes to understand the root cause of the error.
    *   For SFEs, be sure to find the corresponding fundamental concepts, relearn them, and ensure a thorough understanding, rather than just knowing the surface.

*   **Optimize Your Test-Taking Strategy (Pacing & Time Management):**
    *   Carefully study the "Time Management Analysis" and the "Theta Trend Chart."
    *   Reflect on which question types you spend too much or too little time on. The GMAT is a strictly timed exam, and proper pacing is crucial.
    *   Practice strategically allocating time between questions of different difficulties. Sometimes, wisely skipping a question far beyond your current level to save time for more manageable ones is a smart choice.

*   **Select Practice Materials Targetedly:**
    *   Based on the practice directions suggested in the report, choose appropriate practice questions. For example, if the report indicates weakness in RC detail-locating questions, find more of those to practice.
    *   You can refer to the "Question Difficulty (Simulated)" value in the report to consciously practice questions slightly above your current comfort zone.

*   **Diagnose Regularly, Track Progress:**
    *   GMAT preparation is a continuous improvement process. It is recommended that you use this platform for a diagnosis after each full mock exam or a significant phase of practice.
    *   Compare reports over time to observe where you've made progress and what issues persist, allowing you to dynamically adjust your study plan.

*   **【IMPORTANT】Combine with Professional Guidance:**
    *   This platform provides **quantitative analysis** based on data. It can efficiently help you identify "potential problem" areas.
    *   However, to truly understand "why these problems exist" and "how to fundamentally solve them," it often requires **qualitative analysis** from experienced GMAT instructors (e.g., in-depth discussions about your specific problem-solving approaches, thinking errors, test-taking mentality, etc.).
    *   It is strongly recommended that you share the diagnostic report generated by this platform (especially the detailed data tables and section diagnostic details) with your GMAT instructor or academic advisor for more in-depth and personalized guidance.

---

## 【GMAT Instructor Guide】Data-Driven Teaching Insights and Coaching Strategies

This guide aims to help GMAT instructors understand how to use the GMAT Diagnostic Platform to derive teaching insights from student performance data and develop more targeted coaching strategies.

### 1. Guiding Students to Use the Diagnostic Platform Effectively

Successful data analysis begins with high-quality data input. As an instructor, you can guide students to:

*   **Understand the Platform's Value:** Clearly explain to students how this tool can help them go beyond surface scores to understand the root causes of their learning difficulties.
*   **Prepare Qualified Data:**
    *   Emphasize the **completeness** and **accuracy** of the data, especially the fields and formats mentioned in the "Prepare Your Score Report Data" section.
    *   **Crucially emphasize data anonymization!** Ensure students remove all personal identifying information before uploading or pasting data.
    *   Guide students on how to export or organize the required question-by-question response data from their commonly used mock test tools.
*   **Correctly Mark "Invalid Questions":**
    *   Explain the definition of "invalid questions" (questions that do not reflect true ability due to extreme time pressure, guessing, operational errors, etc.).
    *   Guide students on how to use the `is_manually_invalid` (Manually Mark as Invalid) checkbox during the data input preview stage to accurately mark such questions. Emphasize that student manual markings will override the system's preliminary suggestions.
*   **Recommend Using an OpenAI API Key (If applicable):**
    *   Explain that providing an API Key allows students to receive more readable AI summary reports and personalized learning recommendations, and also helps instructors quickly grasp the key points of a student's report.
    *   If students are uncomfortable providing one, instructors can use relevant tools themselves to summarize after receiving the student's detailed report.

### 2. Efficiently Analyzing an Individual Student's Diagnostic Report

Once a student completes the analysis and shares the report with you (students can export detailed data for each section as Excel tables, or share screenshots/the results page directly), you can start by looking at:

*   **A. Quick Overview & AI Insights (If available):**
    *   If the student used the OpenAI feature, first review the AI-generated **"Consolidated Diagnostic Report."** This can help you quickly understand the student's main strengths, weaknesses, and core issues within minutes.
    *   Pay attention to the **"Diagnostic Tags"** extracted by the AI. You can discuss with the student whether these tags are accurate, and even guide them in editing these tags to better fit the actual situation.

*   **B. In-depth Interpretation of Detailed Section Reports:**

    *   **B1. Core Metric Data:**
        *   **Accuracy Rate:** Overall, and broken down by question type and knowledge point.
        *   **IRT Ability (Theta) & Trend Chart:**
            *   Assess the student's relative ability level in that section.
            *   Observe the Theta curve to judge the student's stability and endurance during the test, and whether pacing issues led to a late-stage collapse.
        *   **Average Time per Question:** Overall, and broken down by question type and knowledge point.
        *   **SFE (Special Focus Errors) Percentage & Details:** Pay close attention to SFEs. These are usually knowledge points or skills the student thought they mastered but didn't fully grasp, representing significant opportunities for improvement.

    *   **B2. Time Management & Pacing Analysis:**
        *   Carefully review the "Time Performance" column and the "Time Management Analysis" section in the report.
        *   On which types of questions does the student spend too much time (potentially leading to not finishing)? Which questions are answered too quickly (potentially leading to lower accuracy or invalid guesses)?
        *   Combined with the Theta trend chart, analyze whether time allocation affected the stability of their ability demonstration.

    *   **B3. Deep Dive into Error Patterns (Combined with "Diagnostic Tags" and "Skill Tested/Content Domain"):**
        *   **Quantitative (Q):**
            *   Are problems more prevalent in Algebra, Arithmetic, or Geometry? Which specific sub-topics (e.g., inequalities, percentages, properties of circles)?
            *   Is it a poor grasp of PS (Problem Solving) question types, or issues with the logical judgment in DS (Data Sufficiency)?
            *   Are there fundamental issues like calculation carelessness, misreading questions, or forgetting formulas?
        *   **Verbal (V):**
            *   RC (Reading Comprehension): Are weaknesses in specific question types like Main Idea, Detail, Inference, or Structure? Is it an issue with passage types (e.g., science, humanities)? Difficulty with complex sentences, or slow information retrieval?
            *   CR (Critical Reasoning): Are common errors in Weaken, Strengthen, Assumption, Evaluate, Explain, or Inference questions? Is it unclear logical chain analysis, or insufficient ability to discern between options?
        *   **Data Insights (DI):**
            *   DS (Data Sufficiency): Similar to Quant DS, judging A, B, C, D, E logic.
            *   MSR (Multi-Source Reasoning): How is their information integration ability, and their ability to map between charts and text?
            *   GRA (Graphics Interpretation) / TIA (Table Analysis): Accuracy and speed in reading charts and extracting data.
            *   TPA (Two-Part Analysis): Comprehensive analysis and matching ability under complex conditions.
            *   Are errors more common in math-related or non-math-related content domains?

    *   **B4. Additional Insights from "Invalid Questions":**
        *   Even if invalid questions don't directly contribute to ability assessment, they provide important information.
        *   Which questions did the student mark as invalid? During which phase of the test are they concentrated? What types or difficulties do they belong to?
        *   This can reflect the student's test-taking mentality (e.g., easily giving up on difficult questions), strategy (e.g., how they guess when short on time), or their judgment of their own state.

    *   **B5. Comparing Subjective and Objective Data (If recorded by the student):**
        *   If your teaching process includes having students record subjective feelings (e.g., subjective time pressure feedback mentioned in `student_subjective_reports.csv`), you can compare this with the platform's objective time analysis results.
        *   For example, if a student felt very pressed for time, but the data shows their timing was within a reasonable range, it might indicate high psychological stress needing adjustment. Conversely, it might mean the student's perception of time is skewed.

### 3. Using Diagnostic Results to Optimize Teaching Strategies

Based on the detailed analysis above, you can provide students with more precise and efficient coaching:

*   **Personalized Study Plans & Homework Assignments:**
    *   Develop personalized review plans targeting each student's unique weak points (knowledge areas, question types, skill dimensions).
    *   Assign targeted practice questions. For instance, if a student's Quant "exponent operations" in Algebra is an SFE hotspot, assign specific practice on this topic.
*   **Adjusting Classroom Teaching Focus:**
    *   If you find that a majority of students have universal problems with a certain knowledge point or question type (e.g., the class as a whole has a low score rate on DI MSR questions), consider strengthening the explanation and practice of this content in subsequent lessons.
*   **Teaching Efficient Test-Taking Skills:**
    *   For common time management issues, teach pacing strategies and time allocation methods for different test phases.
    *   Guide students on how to identify and tackle SFEs, such as creating an error log, reviewing regularly, and ensuring true understanding.
    *   Teach strategies for answering questions under pressure, such as when to persevere and when to strategically skip difficult questions.
*   **Guiding Students to Correctly Understand "Difficulty" & "Ability":**
    *   Explain to students that the "Question Difficulty (Simulated)" and "Ability (Theta)" values in the report are relative estimates based on the IRT model, primarily for internal diagnostic comparison, not absolute official standards.
    *   Encourage students to focus on identifying their knowledge gaps and skill shortcomings, rather than obsessing over a single numerical value.
*   **Establishing a Positive Learning Feedback Loop:**
    *   Encourage students to use the platform for self-diagnosis after every mock exam or significant practice phase.
    *   Regularly review diagnostic reports with students, discuss progress and areas for improvement, and form a virtuous cycle of "practice-diagnose-feedback-adjust."

### 4. (Advanced) Multi-Student Data Analysis & Class Insights

If your teaching institution or you personally have the capability to integrate anonymized data from multiple students (e.g., using Excel data exported from the platform, or by secondary processing of backend data like `gmat_performance_data.csv`), you can gain broader class-level teaching insights:

*   **Overall Class Strengths & Weaknesses Analysis:**
    *   Compile statistics on the class's average accuracy, average time spent, etc., across GMAT sections, knowledge areas, and question types.
    *   Identify common weak areas and error patterns for the class.
*   **Reference for Adjusting Teaching Content & Difficulty:**
    *   Based on overall class data, reflect on whether the current syllabus content and difficulty gradient are appropriate.
    *   Timely adjust teaching strategies to supplement explanations for common issues.
*   **Tracking High-Frequency SFE Points:**
    *   Compile statistics on SFE knowledge points that appear frequently in the class; these are often areas of fuzzy understanding that need focused clarification.
*   **(Caution Required) Data Privacy & Ethics:**
    *   When conducting any multi-student data analysis, **you MUST ensure that all data has been thoroughly anonymized**, strictly adhering to relevant data privacy regulations and ethical requirements.

### 5. Teaching Memos & Continuous Tracking

*   **Record Observations & Plans:** You can combine the analysis results from the diagnostic report with your teaching journal or student files (e.g., `memo.md` in the project if used personally) to record key observations, coaching plans, and progress tracking for each student.
*   **Encourage Transparent Communication:** Openly discuss the results of the diagnostic report with students, jointly set improvement goals and strategies, and enhance students' learning initiative and engagement.

---

Hopefully, this tutorial will help you make better use of the GMAT Diagnostic Platform to enhance your teaching effectiveness and assist more students in successfully preparing for the GMAT! If you encounter any issues or have suggestions during use, please feel free to provide feedback through the channels offered by the platform (such as GitHub Issues). 