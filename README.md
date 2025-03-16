# GMAT-score-report-analysis

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Excel VBA](https://img.shields.io/badge/Excel-VBA-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

## Overview

This repository provides a comprehensive toolkit for GMAT test-takers and educators to analyze score reports, simulate exam performance, and optimize study strategies. It includes:

* An interactive tool to map GMAT scale scores to percentiles and estimate total scores.
* An Item Response Theory (IRT)-based simulation tool to track ability (theta) estimates and analyze question difficulty.
* An Excel VBA macro to annotate score reports with detailed insights for educational analysis.

## Key Features

* **Interactive Score Percentile Mapping**: Visualize scale scores and percentiles with sliders, estimate total scores using a weighted formula, and assess score efficiency via tangent slopes (steeper slopes indicate higher percentile gains per scale point).
* **IRT-Based Exam Simulation**: Simulate GMAT exams with user-defined subject order, wrong questions, and initial θ values, generating theta trend plots and difficulty parameters (b).
* **Excel VBA Score Annotation**: Automatically annotate GMAT score reports in Excel, marking overtime questions, too-fast responses, incorrect answers, and identifying "UNUSUAL" (easier incorrect questions) and "UNUSUAL SLOW" (excessively slow responses) conditions based on difficulty and response time.

## Installation

### Prerequisites

* For Python Tools:
  * Python 3.8 or higher
  * Required libraries: numpy, pandas, matplotlib, scipy, ipywidgets, pytz
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

4. Run Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
   Open `scale-percentile-simulation.ipynb` or `irt-simulation-tool.ipynb` to get started.

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

## Files

* `scale-percentile-simulation.ipynb`: Interactive tool for GMAT score percentile mapping and total score estimation with tangent analysis.
* `irt-simulation-tool.ipynb`: IRT-based simulation tool for theta estimation, difficulty analysis, and Excel output.
* `score-excel-vba.bas`: Excel VBA macro for annotating GMAT score reports with overtime, too-fast, incorrect, unusual, and unusual slow conditions.
* `requirements.txt`: List of required Python libraries for the Jupyter Notebooks.

## Recommended Usage Workflow

For optimal results, follow this step-by-step workflow:

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

1. The IRT simulation tool uses difficulty parameters (b) within a range of -2 to +2 and a simulated question bank of 1000 randomly distributed items. These parameters can be customized but are intended only for simulation purposes. The actual difficulty range and question bank size used in the official GMAT exam are proprietary information.

2. Theta (θ) estimates should be interpreted cautiously. Focus on relative values and patterns of change rather than absolute numbers.

3. The plain text report generated by `GeneratePlainTextReport_WithColorInfo` can be input into a Large Language Model (LLM) for further analysis and personalized recommendations.

4. The official GMAT exam includes unscored experimental questions (with variable quantity and positions). The IRT simulation tool assumes all questions are scored by default.

5. For optimal analysis results, combine this toolset with:
   * The test-taker's specific recollections of individual questions
   * Practice test reviews with detailed error analysis
   * Recent practice data (from 2-4 weeks before the exam) if the above information is unavailable

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
