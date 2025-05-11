# GMAT-score-report-analysis

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-orange.svg)
![Excel VBA](https://img.shields.io/badge/Excel-VBA-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

## Overview

This repository provides a comprehensive toolkit for GMAT test-takers and educators to analyze score reports, simulate exam performance, and optimize study strategies. It includes:

* An interactive tool to map GMAT scale scores to percentiles and estimate total scores.
* An Item Response Theory (IRT)-based simulation tool to track ability (theta) estimates and analyze question difficulty (available as a Jupyter Notebook).
* An Excel VBA macro to annotate score reports with detailed insights for educational analysis.
* A structured Standard Operating Procedure (SOP) for detailed score report analysis, outlining steps from data cleaning to personalized practice suggestions, found in `analysis-template-dustin.md`.
* The `analysis-framework/` directory contains related documentation for the analysis methodology, potentially including overall and section-specific documents in English and Chinese.
* **Additionally, this repository now features an interactive GMAT Score Diagnosis Platform (Streamlit App located in `gmat_diagnosis_app/`) for a more automated and web-based analysis experience (see dedicated section below).**

## Key Features

* **Interactive Score Percentile Mapping (`scale-percentile-simulation.ipynb`)**: Visualize scale scores and percentiles with sliders, estimate total scores using a weighted formula, and assess score efficiency via tangent slopes (steeper slopes indicate higher percentile gains per scale point).
* **IRT-Based Exam Simulation (`irt-simulation-tool.ipynb`)**: Simulate GMAT exams with user-defined subject order, wrong questions, and initial θ values, generating theta trend plots and difficulty parameters (b).
* **Excel VBA Score Annotation (`score-excel-vba.bas`)**: Automatically annotate GMAT score reports in Excel, marking overtime questions, too-fast responses, incorrect answers, and identifying "UNUSUAL" (easier incorrect questions) and "UNUSUAL SLOW" (excessively slow responses) conditions based on difficulty and response time.
* **GMAT Score Diagnosis Platform (Streamlit App)**: A web-based application offering comprehensive analysis of Q, V, and DI sections with IRT insights, error pattern identification, and AI-powered summaries. (Detailed in its own section below).

## Installation

### Prerequisites

* For Python Tools:
  * Python 3.8 or higher
  * Required libraries: numpy, pandas, matplotlib, scipy, ipywidgets, pytz, **streamlit, openai** (ensure these are in `requirements.txt` or installed manually for the Streamlit app)
* For Excel VBA Tool:
  * Microsoft Excel with VBA support enabled

### Setup for Python Tools

1. Clone the repository:
   ```bash
   git clone https://github.com/danyuchn/GMAT-score-report-analysis.git
   ```

2. Change to project directory:
   ```bash
   cd GMAT-score-report-analysis
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run Jupyter Notebook (for `.ipynb` files):
   ```bash
   jupyter notebook
   ```
   Open `scale-percentile-simulation.ipynb` or `irt-simulation-tool.ipynb` to get started.

5. To run the GMAT Score Diagnosis Platform (Streamlit App), see its dedicated section below for launch instructions.

### Setup for Excel VBA Tool

1. Open Microsoft Excel.
2. Enable the Developer tab (if not already enabled):
   * Go to File > Options > Customize Ribbon > Check Developer > OK.
3. Import `score-excel-vba.bas` into your Excel workbook:
   * Go to Developer > Visual Basic.
   * Right-click on VBAProject > Insert > File > Select `score-excel-vba.bas`.
4. Run the macro on your GMAT score report Excel file.

## Usage

### 1. Scale Percentile Simulation (`scale-percentile-simulation.ipynb`)

* **Purpose**: Assists GMAT test-takers in planning study time allocation and targeting section scores to achieve a desired total score.
* **Features**:
  * Interactive sliders to adjust Quantitative, Verbal, and Data Insights scores (range: 60-90).
  * Visualizes scale scores vs. percentiles with tangent lines; steeper tangents indicate higher score efficiency (greater percentile change per scale point), which is critical for school application reviews.
  * Estimates total score using the formula: -1005.3296 + 6.7098 * Q + 6.6404 * V + 6.7954 * DI.
* **How to Use**:
  1. Open `scale-percentile-simulation.ipynb` in Jupyter Notebook.
  2. Adjust the sliders to set scores for each section (e.g., Q=75, V=80, DI=85).
  3. Observe the percentile scatter plot, tangent lines, and estimated total score (e.g., ~714.82 for Q=75, V=80, DI=85).
* **Note**: The scale-to-percentile data is based on the latest available data (as of March 16, 2025). Check GMAT Official Score Understanding for updates and manually update the `datasets` dictionary in the notebook if needed.

#### Example Output
![Scale Percentile Plot](/images/scale-percentile-plot.png)

### 2. IRT Simulation Tool (`irt-simulation-tool.ipynb`)

* **Purpose**: Simulates the GMAT exam process to estimate ability (theta) trends and analyze question difficulty for performance optimization.
* **Features**:
  * **Inputs**: Subject order (e.g., V/Q/DI), initial θ values (e.g., 0.0 for each section), and wrong question numbers (e.g., 1, 3, 5).
  * **Outputs**: A theta estimate trend plot over questions, difficulty parameter (b) plots, and an Excel file (`Difficulty_Parameters_YYYYMMDD_HHMMSS.xlsx`) with b values for Quantitative, Verbal, and Data Insights.
  * Uses IRT to select questions based on item information and minimizes negative log-likelihood to update theta estimates.
* **How to Use**:
  1. Open `irt-simulation-tool.ipynb` in Jupyter Notebook.
  2. Enter the subject order (e.g., V/Q/DI), initial θ values for each section, and wrong question numbers when prompted.
  3. Run the simulation to generate plots and save difficulty parameters.
  4. Review the Excel file for detailed b values (rounded to 2 decimal places).

#### Example Output
![Theta Estimate Plot](/images/theta-estimate-plot.png)
![Difficulty Estimate Plot](/images/difficulty-estimate-plot.png)

### 3. Score Excel VBA Annotation (`score-excel-vba.bas`)

* **Purpose**: Enables educators to annotate GMAT score reports in Excel with detailed insights for teaching and analysis.
* **Features**:
  * Marks overtime questions (yellow background) based on section-specific thresholds (e.g., 2.5 min for Quantitative, 2 min for Critical Reasoning, adjustable per question type).
  * Marks too-fast responses (green background) below lower limits (e.g., 1 min for Quantitative, 0.5 min for Verbal/Data Insights).
  * Highlights incorrect answers with red font.
  * Identifies "UNUSUAL" conditions where an easier question (lower V_b) is answered incorrectly while a harder question in the same fundamental skill group is correct.
  * Identifies "UNUSUAL SLOW" conditions where a response exceeds 3 minutes and is slower than a correct answer with higher difficulty in the same group.
  * Generates a plain text report on a new worksheet with color and marker explanations.
* **Required Excel Columns**:
  * A: Question Number
  * B: Response Time (in minutes)
  * C: Performance ("Correct" or "Incorrect")
  * E: Question Type (e.g., "Critical Reasoning", "Data Sufficiency")
  * F: Fundamental Skill
  * G: Difficulty (V_b value)
  * H: Marker (populated with "UNUSUAL" or "UNUSUAL SLOW")
* **How to Use**:
  1. Prepare your GMAT score report in Excel with the required columns (e.g., sample data: Question 1, 2.7 min, Incorrect, Critical Reasoning, Algebra, 0.5).
  2. Import `score-excel-vba.bas` into your workbook (see Setup for Excel VBA Tool).
  3. Run the appropriate macro based on section:
     * `MarkOverTime_Incorrect_And_Unusual_Q` for Quantitative.
     * `MarkOverTime_Incorrect_And_Unusual_Slow_V` for Verbal.
     * `MarkOverTime_Incorrect_And_Unusual_Slow_DI` for Data Insights.
  4. Review annotations and run `GeneratePlainTextReport_WithColorInfo` to export a detailed report to a new worksheet.
* **Example**:
  * Input: Question 1 (2.7 min, Incorrect, Critical Reasoning, Algebra, V_b=0.5).
  * Output: Yellow background (overtime), red font (incorrect), "UNUSUAL" in column H if a harder correct question exists.

#### Example Output
![Annotated Excel Sample](/images/annotated-excel-sample.png)

### 4. Analysis Templates

This repository includes a standardized analysis template based on Dustin's Standard Operating Procedure (SOP) for dissecting GMAT score reports. The template, detailed in [analysis-template-dustin.md](./analysis-template-dustin.md), provides an 8-step framework to:

* Clean and validate score data (e.g., filtering guessed or unanswered questions).
* Analyze time management and performance by question type and difficulty.
* Diagnose specific weaknesses with detailed obstacle identification.
* Formulate tailored practice plans with progressive difficulty and timed training.

This SOP is ideal for educators and test-takers aiming to systematically improve performance. Integrate it with the Excel VBA annotations and IRT simulation outputs for a comprehensive analysis workflow.

## Interactive GMAT Score Diagnosis Platform (Streamlit App - `gmat_diagnosis_app/app.py`)

This project also includes a powerful, web-based GMAT Score Diagnosis Platform built with Streamlit. It offers a more automated and interactive way to analyze your GMAT performance across Quantitative (Q), Verbal (V), and Data Insights (DI) sections.

*   **Purpose**: Provides an interactive web application for in-depth analysis of GMAT Quantitative, Verbal, and Data Insights sections. It helps users identify weaknesses, understand performance patterns, and receive targeted practice recommendations.

*   **Key Features**:
    *   **Versatile Data Input**:
        *   Upload score data via CSV files (up to 1MB).
        *   Paste data directly from Excel or other tabular sources.
        *   Supports Quantitative (Q), Verbal (V), and Data Insights (DI) sections.
        *   Includes sample data for quick testing.
    *   **Comprehensive Performance Analysis**:
        *   IRT-based ability (Theta) estimation and trend visualization across questions.
        *   Detailed time management analysis, identifying pacing issues.
        *   Identification of error patterns, including Special Focus Errors (SFE) indicating inconsistent concept mastery.
        *   Subject-specific diagnostic logic for Q, V, and DI.
    *   **Insightful Diagnostic Reports**:
        *   Per-subject reports showing Theta trend plots.
        *   Text-based summaries detailing overall time pressure, performance across various dimensions (question type, difficulty, skills), core diagnostic findings, and special behavioral patterns.
        *   Identification of foundational knowledge areas needing reinforcement.
    *   **Personalized Practice Recommendations**:
        *   Concrete suggestions for practice, including recommended difficulty levels and initial time constraints.
    *   **Data Interaction and Export**:
        *   Interactive data tables displaying input data alongside diagnostic tags (e.g., simulated difficulty, time performance category, SFE, overtime, invalid status).
        *   Color-coded highlighting for incorrect answers, overtime, and invalid questions.
        *   Ability to manually mark questions as "invalid" (e.g., due to rushing or guessing) to refine analysis accuracy.
        *   Download detailed diagnostic data with all tags as an Excel file.
    *   **Optional AI-Powered Enhancements (requires OpenAI API Key)**:
        *   AI-generated consolidated summary of practice recommendations from all sections.
        *   Interactive chat interface to ask questions about the generated reports and data.
    *   **Data Persistence**:
        *   Uploaded GMAT performance data is appended to `gmat_diagnosis_app/gmat_performance_data.csv` for record-keeping and potential future aggregated analysis.

*   **How to Launch**:
    1.  Ensure you have installed the necessary dependencies (including `streamlit` and `openai`) from `requirements.txt`.
    2.  Navigate to the project's root directory in your terminal.
    3.  Run the command: `streamlit run gmat_diagnosis_app/app.py`.
    4.  The application should open in your web browser.

*   **How to Use**:
    1.  **Prepare Data**: Ensure your GMAT score data for Q, V, and DI sections is ready. It should include columns like `Question`, `Response Time (Minutes)`, `Performance`, and subject-specific fields like `Content Domain`, `Question Type`, and `Fundamental Skills`. **Crucially, de-identify your data by removing all personal information.** Refer to the app's built-in "快速使用指南" (Quick Start Guide) and "完整使用說明" (Complete Usage Guide) for exact column names, formats, and detailed instructions.
    2.  **Input Data**: In the "數據輸入與分析" (Data Input & Analysis) tab of the app:
        *   Navigate to the respective Q, V, and DI sub-tabs.
        *   Either upload your CSV file or paste data from Excel/tables into the provided text areas.
        *   The app provides an option to load sample data to explore its features.
    3.  **Review and Edit Data**: 
        *   Once data is loaded, a preview and editor will appear.
        *   Verify the data accuracy. 
        *   **Mark Invalid Questions**: Use the checkboxes to mark any questions that were answered under undue time pressure, guessed, or otherwise do not reflect your true ability. The system might pre-select some based on time, but manual input is prioritized.
    4.  **Configure Settings (Sidebar)**:
        *   **IRT Simulation**: Adjust initial Theta estimates for Q, V, DI if desired (default is 0.0).
        *   **OpenAI API Key (Optional)**: If you have an OpenAI API key, enter it to enable AI-powered summary and chat features.
        *   **Manual Adjustments**: Optionally, specify question numbers to be manually flipped from incorrect to correct (or vice-versa) for IRT simulation purposes.
    5.  **Run Analysis**: Once data for all three sections (Q, V, DI) is successfully loaded and validated, the "開始分析" (Start Analysis) button will become active. Click it to initiate the diagnosis.
    6.  **View Results**: After processing, navigate to the "結果查看" (View Results) tab:
        *   **Per-Subject Tabs (e.g., "Q 科結果")**: View Theta trend plots, detailed text-based diagnostic reports (covering time pressure, error patterns, SFE, practice advice), and interactive data tables with diagnostic tags.
        *   **Download Data**: Download the augmented data (including all diagnostic tags) as an Excel file.
        *   **✨ AI Consolidated Advice (if OpenAI key provided)**: A summary of practice recommendations extracted by AI.
    7.  **Interact with AI (if OpenAI key provided)**: Use the chat interface at the bottom of the results page to ask specific questions about your generated reports.

*   **Important Considerations for the Platform**:
    *   **Data Privacy and Anonymization**: 
        *   You are responsible for **manually removing all personally identifiable information (PII)** (e.g., name, candidate ID, email, test center) from your score data before uploading or pasting it into the platform.
        *   By using the tool and uploading data, you consent to the collection of this **anonymized** data by the developer for purposes such as model optimization, academic research, or other analytical uses, as stated in the app's disclaimer.
    *   **Accuracy of Analysis**:
        *   The diagnostic insights and recommendations provided by the platform are based on quantitative analysis of the data you provide and internal IRT model estimations.
        *   The accuracy of the analysis heavily depends on the completeness and correctness of your input data.
        *   The IRT-estimated question difficulties and Theta values are for relative comparison and diagnostic purposes within this tool's framework; they **do not represent official GMAT scores or official GMAT question difficulties**.
        *   The platform may automatically filter data points it deems invalid (e.g., based on extreme response times), but your manual marking of invalid questions is also crucial.
        *   All outputs (diagnostic tags, insights, suggestions) are preliminary results and should be used as a supplementary tool. **They are not a substitute for qualitative analysis with an experienced GMAT instructor or professional advisor.**
        *   **Data Storage**: Note that uploaded performance data is appended to `gmat_diagnosis_app/gmat_performance_data.csv`.

## Files

* `gmat_diagnosis_app/app.py`: The main Streamlit application file for the GMAT Score Diagnosis Platform.
* `gmat_diagnosis_app/`: Directory containing the modules for the Streamlit GMAT diagnosis application. Key subdirectories include:
    * `services/`: Modules for data handling (CSV, OpenAI), plotting, etc.
    * `ui/`: Components for the Streamlit user interface (input tabs, results display, chat).
    * `analysis_orchestrator.py`: Coordinates the analysis pipeline.
    * `diagnostics/`: Contains diagnostic logic for Q, V, and DI sections.
    * `irt/`: Modules for Item Response Theory calculations and simulation.
    * `utils/`: Utility functions for data processing, validation, etc.
    * `constants/`: Configuration files and constant definitions.
    * `gmat_performance_data.csv`: CSV file where uploaded GMAT performance records from the Streamlit app are stored.
    * `student_subjective_reports.csv`: CSV file for storing student subjective reports (primarily related to the CSV data service, less directly tied to the Streamlit app's core performance analysis input).
* `scale-percentile-simulation.ipynb`: Interactive tool for GMAT score percentile mapping and total score estimation with tangent analysis.
* `irt-simulation-tool.ipynb`: IRT-based simulation tool for theta estimation, difficulty analysis, and Excel output (manual workflow component).
* `score-excel-vba.bas`: Excel VBA macro for annotating GMAT score reports with overtime, too-fast, incorrect, unusual, and unusual slow conditions (manual workflow component).
* `analysis-template-dustin.md`: Markdown file containing the full SOP table with descriptions, purposes, and examples for score report analysis (supports manual workflow).
* `analysis-framework/`: Directory containing documentation related to the GMAT analysis methodology used in the project. It may include:
    * `overall-doc/`: General documents about the analysis framework.
    * `sec-doc-zh/`: Section-specific documents in Chinese.
    * `section-doc-en/`: Section-specific documents in English.
    * `testset/`: Potentially sample data or test cases for the analysis framework.
* `requirements.txt`: Lists the Python dependencies for the project (ensure `streamlit` and `openai` are included if using the diagnosis platform).
* `README.md`: This file.
* `LICENSE.md`: Project license information.

## Recommended Usage Workflow

For optimal results, follow this step-by-step workflow (manual approach):

1. **Analyze GMAT Total Score Target**
   * Open `scale-percentile-simulation.ipynb`
   * Use the interactive sliders to set target scores for each section
   * Identify the most efficient sections to improve (steeper tangent slopes)

2. **Import Score Report Data**
   * Take screenshots of your GMAT score report showing question performance and time management
   * In Excel, use Insert → Insert from Picture to convert the screenshot to a spreadsheet
   * Carefully verify that all text and numbers were recognized correctly
   * Ensure data is organized in the required column format (see Score Excel VBA section above)

3. **Extract Incorrect Question Numbers**
   * Import `score-excel-vba.bas` into your Excel workbook
   * Run the `OutputIncorrectList` macro
   * Find the list of incorrect question numbers in cell K25
   * Copy these question numbers for use in the IRT simulation

4. **Run IRT Simulation**
   * Open `irt-simulation-tool.ipynb`
   * Enter the subject order used in your exam (e.g., V/Q/DI)
   * Enter initial θ values for each section (recommend starting with 0.0)
   * Input the incorrect question numbers from cell K25 identified in step 3
   * Run the simulation

5. **Complete the Analysis**
   * Open the difficulty parameters Excel file generated by the IRT simulation (`Difficulty_Parameters_YYYYMMDD_HHMMSS.xlsx`)
   * Copy the difficulty values (b parameters) into column G of your score report Excel file
   * Run the section-specific analysis tools in VBA:
     * `MarkOverTime_Incorrect_And_Unusual_Q` for Quantitative
     * `MarkOverTime_Incorrect_And_Unusual_Slow_V` for Verbal
     * `MarkOverTime_Incorrect_And_Unusual_Slow_DI` for Data Insights
   * Run `GeneratePlainTextReport_WithColorInfo` to get a comprehensive analysis
   * Review the "UNUSUAL" and "UNUSUAL SLOW" markers to identify key improvement areas

This integrated workflow allows you to target your study efforts efficiently by identifying which sections will yield the highest score improvements and pinpointing specific question types where you face unusual difficulties.

## Important Notes

1. The IRT simulation tool (`irt-simulation-tool.ipynb`) uses difficulty parameters (b) within a range of -2 to +2 and a simulated question bank of 1000 randomly distributed items. These parameters can be customized but are intended only for simulation purposes. The actual difficulty range and question bank size used in the official GMAT exam are proprietary information.
2. Theta (θ) estimates from the `.ipynb` simulation tool should be interpreted cautiously. Focus on relative values and patterns of change rather than absolute numbers.
3. The plain text report generated by `GeneratePlainTextReport_WithColorInfo` (from the Excel VBA tool) can be input into a Large Language Model (LLM) for further analysis and personalized recommendations.
4. The official GMAT exam includes unscored experimental questions (with variable quantity and positions). The IRT simulation tool (`irt-simulation-tool.ipynb`) assumes all questions are scored by default.
5. For optimal analysis results when using the manual workflow tools, combine this toolset with:
   * The test-taker's specific recollections of individual questions
   * Practice test reviews with detailed error analysis
   * Recent practice data (from 2-4 weeks before the exam) if the above information is unavailable

(For important notes specific to the **Interactive GMAT Score Diagnosis Platform**, please see its dedicated section above.)

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m "Add new feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For questions or suggestions, feel free to reach out:

* GitHub: [danyuchn](https://github.com/danyuchn)
* Email: [danyuchn@gmail.com](mailto:danyuchn@example.com)

## Acknowledgments

* Thanks to the GMAT Official website for score data and insights (https://www.mba.com/).
* Gratitude to the Python community for libraries like matplotlib, ipywidgets, and scipy.
* Inspired by Item Response Theory (IRT) applications in educational testing.
