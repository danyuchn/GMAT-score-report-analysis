# GMAT Score Report Analysis & Diagnosis Platform

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-orange.svg)
![Excel VBA](https://img.shields.io/badge/Excel-VBA-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)
![Version](https://img.shields.io/badge/Version-3.0-blue.svg)

## 🎯 Overview

A comprehensive, production-ready toolkit for GMAT test-takers and educators featuring advanced psychometric analysis, Interactive Item Response Theory (IRT) simulation, and AI-powered diagnostic insights. The platform combines statistical rigor with practical usability to deliver personalized study recommendations.

### ✨ Key Highlights

* 🧠 **Advanced IRT-based Analysis**: Sophisticated theta estimation and adaptive difficulty modeling
* 🌐 **Bilingual Interface**: Full Traditional Chinese and English support with real-time switching
* 🤖 **AI-Powered Insights**: OpenAI integration for intelligent report synthesis and interactive chat
* 📊 **Comprehensive Diagnostics**: Detailed analysis across Q, V, and DI sections
* 🔧 **Production-Grade Code**: Fully optimized, maintainable, and documented codebase
* 🚀 **Ready for Deployment**: Docker support and containerized architecture

## 🚀 Quick Start

### Using the Streamlit Web Application (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/danyuchn/GMAT-score-report-analysis.git
   cd GMAT-score-report-analysis
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application**:
   ```bash
   streamlit run gmat_diagnosis_app/app.py
   ```

4. **Access via browser**: Open `http://localhost:8501`

### Using Docker (Production Deployment)

```bash
docker-compose up --build
```

## 🎯 Core Features

### 1. Interactive GMAT Diagnosis Platform (Web Application)

**Primary Tool**: Comprehensive web-based analysis platform built with Streamlit

#### Key Capabilities
* **Multi-format Data Input**:
  - CSV file upload (up to 1MB)
  - Direct Excel data paste
  - Built-in sample data for testing
  - Automated format validation and correction

* **Advanced Psychometric Analysis**:
  - IRT-based theta estimation with visualization
  - Adaptive difficulty modeling
  - Time management pattern analysis
  - Special Focus Error (SFE) detection
  - Behavioral pattern identification

* **Intelligent Diagnostics**:
  - Subject-specific diagnostic algorithms (Q/V/DI)
  - Multi-dimensional performance assessment
  - Automated invalid data detection
  - Comprehensive error categorization

* **Personalized Recommendations**:
  - Targeted practice suggestions
  - Difficulty-progressive study plans
  - Time management strategies
  - Skill-specific improvement paths

* **AI-Enhanced Features** (OpenAI API Required):
  - Consolidated cross-subject analysis
  - Interactive chat interface
  - Intelligent report synthesis
  - Natural language insights

#### Subject-Specific Analysis

**Quantitative (Q) Section**:
- Content domain analysis (Algebra, Arithmetic, Geometry)
- Question type performance (REAL vs PURE)
- Calculation vs conceptual error identification
- Time efficiency optimization

**Verbal (V) Section**:
- Critical Reasoning vs Reading Comprehension analysis
- Skill-based performance assessment
- Reading comprehension barrier detection
- Choice analysis efficiency evaluation

**Data Insights (DI) Section**:
- Multi-source reasoning (MSR) analysis
- Graph interpretation assessment
- Data sufficiency evaluation
- Cross-domain reasoning patterns

### 2. Scale-Percentile Simulation Tool

**Purpose**: Strategic score planning and efficiency analysis

**Features**:
- Interactive score adjustment (60-90 range per section)
- Real-time percentile mapping
- Total score estimation using validated formula
- Efficiency visualization via tangent slope analysis
- Data current as of March 2025

**Usage Example**:
```python
# Simulate scores: Q=75, V=80, DI=85
# Expected output: ~714.82 total score
# Visualizes percentile efficiency gains
```

### 3. IRT Simulation Framework

**Purpose**: Exam process simulation and ability tracking

**Advanced Features**:
- Customizable subject ordering
- Initial theta parameter setting
- Wrong answer pattern simulation
- Difficulty parameter (b-value) analysis
- Excel export for detailed review

**Technical Implementation**:
- Maximum information item selection
- Negative log-likelihood minimization
- Adaptive difficulty progression
- Comprehensive performance tracking

### 4. Excel VBA Annotation System

**Purpose**: Automated score report annotation for educators

**Annotation Categories**:
- Overtime questions (yellow highlighting)
- Fast responses (green highlighting)
- Incorrect answers (red formatting)
- Unusual patterns (difficulty-performance mismatches)
- Unusual slow responses (efficiency analysis)

## 🏗️ Technical Architecture

### System Requirements
- **Python**: 3.8+
- **Key Libraries**: streamlit, pandas, numpy, scipy, openai, plotly
- **Excel**: VBA-enabled for annotation tools
- **Browser**: Modern web browser for Streamlit interface

### Code Quality & Maintainability

#### Recent Optimizations (Version 3.0)
* **Clean Codebase**: 
  - Removed unnecessary Chinese comments
  - Standardized English documentation
  - Eliminated redundant logging statements
  - Optimized import statements

* **Debug Infrastructure**:
  - Comprehensive debugging utilities (`utils/debug_utils.py`)
  - Performance monitoring decorators
  - DataFrame analysis tools
  - Session state debugging
  - Configurable logging levels

* **Production Readiness**:
  - Error handling with context managers
  - Memory usage optimization
  - Type hints throughout codebase
  - Standardized exception handling

#### Debug Configuration
```python
# Environment variables for debugging
GMAT_DEBUG_MODE=true  # Enable debug mode
GMAT_DEBUG_LEVEL=DEBUG  # Set logging level
```

#### Debugging Tools Usage
```python
from gmat_diagnosis_app.utils.debug_utils import debug_dataframe, monitor_performance

# Quick DataFrame debugging
debug_dataframe(df, "Input Data")

# Performance monitoring
@monitor_performance()
def my_function():
    # Function implementation
    pass
```

### Internationalization (i18n)

**Bilingual Support**:
- Traditional Chinese (zh-TW) as primary
- English (en) as secondary
- Real-time language switching
- Comprehensive translation coverage
- Context-aware translations

**Technical Implementation**:
```python
from gmat_diagnosis_app.i18n import translate as t

# Usage in code
user_message = t('diagnostic_complete')
# Returns appropriate translation based on session language
```

## 📊 Data Requirements

### Input Data Format

#### Required Columns (All Sections)
- `Question`: Question number/identifier
- `Response Time (Minutes)`: Numeric response time
- `Performance`: "Correct" or "Incorrect"

#### Section-Specific Columns

**Quantitative (Q)**:
- `Content Domain`: Algebra, Arithmetic, Geometry
- `Question Type`: REAL, PURE
- `Fundamental Skills`: e.g., "Rates/Ratio/Percent"

**Verbal (V)**:
- `Question Type`: Critical Reasoning, Reading Comprehension
- `Fundamental Skills`: e.g., "Plan/Construct", "Analysis/Critique"

**Data Insights (DI)**:
- `Content Domain`: Math Related, Non-Math Related
- `Question Type`: Data Sufficiency, Two-part analysis, etc.

### Data Privacy & Security

⚠️ **Important**: Always de-identify data before upload
- Remove names, candidate IDs, test center information
- User responsible for data anonymization
- Uploaded data used for model improvement (anonymized)

## 🔬 Advanced Features

### IRT Modeling Details

**Theta Estimation**:
- Adaptive algorithm with information maximization
- Real-time ability tracking across questions
- Confidence interval calculation
- Performance trend visualization

**Difficulty Calibration**:
- Item Response Theory parameter estimation
- Difficulty-discrimination modeling
- Cross-section calibration
- Validated against official GMAT patterns

### AI Integration Capabilities

**Requirement**: Valid OpenAI API key

**Features**:
1. **Intelligent Synthesis**: Cross-subject analysis and recommendation consolidation
2. **Interactive Chat**: Natural language interface for report exploration
3. **Pattern Recognition**: Advanced error pattern identification
4. **Strategic Insights**: Personalized study strategy generation

### Performance Analytics

**Time Management**:
- Section-wise pacing analysis
- Question-level efficiency scoring
- Pressure point identification
- Optimization recommendations

**Error Pattern Analysis**:
- Systematic vs random error classification
- Skill-specific weakness identification
- Difficulty progression analysis
- Conceptual gap detection

## 📈 Validation & Accuracy

### Statistical Validation
- IRT model validated against psychometric standards
- Difficulty parameters calibrated with official data
- Cross-validation with independent test samples
- Continuous model refinement based on user data

### Diagnostic Accuracy
- Multi-dimensional analysis approach
- Conservative invalid data detection
- Manual override capabilities
- Quality assurance metrics

## 🤝 Contributing

### Development Setup
```bash
# Clone with development dependencies
git clone https://github.com/danyuchn/GMAT-score-report-analysis.git
cd GMAT-score-report-analysis

# Install development dependencies
pip install -r requirements.txt

# Enable debug mode
export GMAT_DEBUG_MODE=true
export GMAT_DEBUG_LEVEL=DEBUG

# Run with debugging
streamlit run gmat_diagnosis_app/app.py
```

### Code Standards
- English comments and documentation
- Type hints required
- Comprehensive error handling
- Debug utilities integration
- i18n translation keys for user-facing text

## 📝 License & Citation

**License**: MIT License

**Citation**: If you use this tool in research or educational contexts, please cite:
```
Yu, D. (2025). GMAT Score Report Analysis & Diagnosis Platform. 
GitHub repository: https://github.com/danyuchn/GMAT-score-report-analysis
```

## 🐛 Support & Feedback

- **Issues**: [GitHub Issues](https://github.com/danyuchn/GMAT-score-report-analysis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/danyuchn/GMAT-score-report-analysis/discussions)
- **Documentation**: Built-in tutorial and help system in the web application

## 🎉 Version History

**v3.0** (Current - Production Ready)
- ✅ Complete diagnostic module unification
- ✅ Code optimization and comment standardization
- ✅ Comprehensive debugging infrastructure
- ✅ Full bilingual support
- ✅ Production-grade error handling
- ✅ Performance monitoring and optimization

**v2.0** (Feature Complete)
- Advanced IRT implementation
- Multi-subject diagnostic algorithms
- AI integration capabilities
- Comprehensive reporting system

**v1.0** (Initial Release)
- Basic analysis tools
- Excel VBA annotation system
- IRT simulation framework
- Scale-percentile mapping

---

**Ready for Production** | **Fully Documented** | **Continuously Maintained**
