# -*- coding: utf-8 -*- # Ensure UTF-8 encoding for comments/strings
import streamlit as st

# Call set_page_config as the first Streamlit command
st.set_page_config(
    page_title="GMAT 成績診斷平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from dotenv import load_dotenv
load_dotenv()

import sys
import os
import io
import pandas as pd
import numpy as np
import logging
import openai
import plotly.graph_objects as go
import datetime

# --- Project Path Setup ---
try:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except NameError:
    # Handle cases where __file__ is not defined (e.g., interactive environments)
    st.warning("Could not automatically determine project root. Assuming modules are available.", icon="⚠️")
    project_root = os.getcwd()  # Fallback

# --- Module Imports ---
try:
    # Import custom modules for core logic
    from gmat_diagnosis_app import preprocess_helpers # Ensure the module itself is imported for setup_input_tabs
    # from gmat_diagnosis_app import irt_module as irt # Moved to analysis_orchestrator
    # from gmat_diagnosis_app.irt import probability_correct, item_information, estimate_theta, initialize_question_bank, simulate_cat_exam
    # from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q # Moved
    
    # Import our modularized components
    from gmat_diagnosis_app.constants.config import (
        SUBJECTS, # Retained: Used in main for iterating tabs and processing
        # MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, # Removed: Likely used within setup_input_tabs
        # BANK_SIZE, RANDOM_SEED, SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS, # Removed: Likely used in analysis_orchestrator or deeper
        BASE_RENAME_MAP # Retained: Used in main for sample data processing
        # REQUIRED_ORIGINAL_COLS, EXCEL_COLUMN_MAP # Removed: Likely used within setup_input_tabs or preprocess_helpers
    )
    # from gmat_diagnosis_app.constants.thresholds import THRESHOLDS # Removed: Likely used in analysis_orchestrator or deeper
    # from gmat_diagnosis_app.utils.validation import validate_dataframe
    # from gmat_diagnosis_app.utils.data_processing import process_subject_tab
    # from gmat_diagnosis_app.utils.styling import apply_styles
    # from gmat_diagnosis_app.utils.excel_utils import to_excel # Removed
    from gmat_diagnosis_app.services.openai_service import ( # Retained: get_chat_context, get_openai_response might be used by a chat interface if it were called
        # summarize_report_with_openai, generate_ai_consolidated_report, # Removed: Assumed handled by orchestrator/display
        get_chat_context, get_openai_response # Retained cautiously, though display_chat_interface is not called
    )
    # from gmat_diagnosis_app.services.plotting_service import create_theta_plot
    from gmat_diagnosis_app.ui.results_display import display_results # Removed display_subject_results
    # from gmat_diagnosis_app.ui.chat_interface import display_chat_interface # Removed: Not called
    from gmat_diagnosis_app.ui.input_tabs import setup_input_tabs, combine_input_data, display_analysis_button
    from gmat_diagnosis_app.session_manager import init_session_state, reset_session_for_new_upload, ensure_chat_history_persistence
    from gmat_diagnosis_app.analysis_orchestrator import run_analysis # Added import
    from gmat_diagnosis_app.services.csv_data_service import add_gmat_performance_record, GMAT_PERFORMANCE_HEADERS, add_subjective_report_record # Added for CSV export and new function
    
    # Import the new analysis helpers - These are likely used by analysis_orchestrator, not directly here.
    # from gmat_diagnosis_app.analysis_helpers.time_pressure_analyzer import calculate_time_pressure, calculate_and_apply_invalid_logic # Removed
    # from gmat_diagnosis_app.analysis_helpers.simulation_manager import run_simulation, prepare_dataframes_for_diagnosis # Removed
    # from gmat_diagnosis_app.analysis_helpers.diagnosis_manager import run_diagnosis, update_session_state_after_analysis # Removed
    
except ImportError as e:
    st.error(f"導入模組時出錯: {e}. 請確保環境設定正確，且 gmat_diagnosis_app 在 Python 路徑中。")
    st.stop()

# --- Initialize Column Display Configuration ---
# COLUMN_DISPLAY_CONFIG moved to ui/results_display.py

# --- Session State Functions ---
# init_session_state and reset_session_for_new_upload moved to session_manager.py

# --- Analysis Functions ---
# run_analysis moved to analysis_orchestrator.py

# --- Display Results Function ---
# display_results moved to ui.results_display.py

# Callback function for loading sample data
def load_sample_data_callback():
    """Sets session state for sample data to be pasted into text areas."""
    sample_q_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	2.3	Correct	Algebra	REAL	Equal/Unequal/ALG
2	4.8	Correct	Algebra	REAL	Rates/Ratio/Percent
3	1.3	Correct	Arithmetic	REAL	Equal/Unequal/ALG
4	2.2	Incorrect	Arithmetic	REAL	Value/Order/Factors
5	0.8	Correct	Arithmetic	REAL	Rates/Ratio/Percent
6	3.5	Correct	Algebra	REAL	Rates/Ratio/Percent
7	1.5	Correct	Algebra	REAL	Equal/Unequal/ALG
8	1.5	Correct	Arithmetic	REAL	Rates/Ratio/Percent
9	1.3	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
10	5.4	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
11	2.6	Incorrect	Algebra	PURE	Equal/Unequal/ALG
12	4.3	Correct	Arithmetic	PURE	Rates/Ratio/Percent
13	1.6	Incorrect	Arithmetic	PURE	Counting/Sets/Series/Prob/Stats
14	0.9	Correct	Arithmetic	REAL	Counting/Sets/Series/Prob/Stats
15	0.7	Correct	Algebra	PURE	Value/Order/Factors
16	4.6	Correct	Algebra	PURE	Value/Order/Factors
17	2.1	Correct	Algebra	PURE	Counting/Sets/Series/Prob/Stats
18	0.7	Correct	Arithmetic	PURE	Equal/Unequal/ALG
19	0.7	Correct	Arithmetic	PURE	Rates/Ratio/Percent
20	0.8	Incorrect	Arithmetic	PURE	Value/Order/Factors
21	0.9	Correct	Arithmetic	PURE	Value/Order/Factors"""

    sample_v_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	1.5	Correct	N/A	Critical Reasoning	Plan/Construct
2	3.6	Correct	N/A	Critical Reasoning	Plan/Construct
3	3	Correct	N/A	Reading Comprehension	Identify Stated Idea
4	1	Incorrect	N/A	Reading Comprehension	Identify Inferred Idea
5	3.7	Incorrect	N/A	Reading Comprehension	Identify Inferred Idea
6	1.7	Incorrect	N/A	Critical Reasoning	Analysis/Critique
7	2.7	Correct	N/A	Reading Comprehension	Identify Inferred Idea
8	1	Correct	N/A	Reading Comprehension	Identify Stated Idea
9	1.6	Correct	N/A	Reading Comprehension	Identify Inferred Idea
10	2.2	Correct	N/A	Critical Reasoning	Plan/Construct
11	4.4	Correct	N/A	Reading Comprehension	Identify Inferred Idea
12	0.6	Correct	N/A	Reading Comprehension	Identify Stated Idea
13	2.3	Correct	N/A	Reading Comprehension	Identify Inferred Idea
14	0.6	Correct	N/A	Reading Comprehension	Identify Stated Idea
15	2.4	Incorrect	N/A	Critical Reasoning	Analysis/Critique
16	2.3	Incorrect	N/A	Critical Reasoning	Analysis/Critique
17	2.8	Incorrect	N/A	Critical Reasoning	Plan/Construct
18	1.3	Correct	N/A	Critical Reasoning	Analysis/Critique
19	0.7	Correct	N/A	Critical Reasoning	Analysis/Critique
20	1.9	Incorrect	N/A	Critical Reasoning	Analysis/Critique
21	1.4	Incorrect	N/A	Critical Reasoning	Analysis/Critique
22	1	Correct	N/A	Critical Reasoning	Plan/Construct
23	1.2	Incorrect	N/A	Critical Reasoning	Plan/Construct"""

    sample_di_data = """Question	Response Time (Minutes)	Performance	Content Domain	Question Type	Fundamental Skills
1	1.5	Correct	Math Related	Data Sufficiency	N/A
2	1.8	Correct	Math Related	Data Sufficiency	N/A
3	3.1	Correct	Non-Math Related	Two-part analysis	N/A
4	4.2	Correct	Math Related	Multi-source reasoning	N/A
5	1.9	Incorrect	Non-Math Related	Multi-source reasoning	N/A
6	1	Incorrect	Math Related	Multi-source reasoning	N/A
7	3.7	Incorrect	Non-Math Related	Data Sufficiency	N/A
8	2.5	Incorrect	Non-Math Related	Graph and Table	N/A
9	5.9	Correct	Non-Math Related	Two-part analysis	N/A
10	2.7	Incorrect	Math Related	Graph and Table	N/A
11	2.1	Incorrect	Math Related	Data Sufficiency	N/A
12	1.7	Incorrect	Math Related	Data Sufficiency	N/A
13	2.8	Correct	Non-Math Related	Graph and Table	N/A
14	1.5	Incorrect	Math Related	Data Sufficiency	N/A
15	2	Incorrect	Non-Math Related	Graph and Table	N/A
16	1.2	Incorrect	Non-Math Related	Data Sufficiency	N/A
17	0.4	Incorrect	Math Related	Two-part analysis	N/A
18	3.5	Incorrect	Math Related	Graph and Table	N/A
19	0.1	Incorrect	Math Related	Two-part analysis	N/A
20	1.2	Incorrect	Math Related	Graph and Table	N/A"""

    st.session_state.q_paster = sample_q_data
    st.session_state.v_paster = sample_v_data
    st.session_state.di_paster = sample_di_data
    
    if 'example_data_loaded' in st.session_state:
        del st.session_state['example_data_loaded']
    if 'example_data' in st.session_state:
        del st.session_state['example_data']
    
    st.session_state.sample_data_pasted_success = True

# --- Main Application ---
def main():
    """Main application entry point"""
    # 設置頁面配置
    # st.set_page_config( # This block will be removed
    #     page_title="GMAT 成績診斷平台",
    #     page_icon="📊",
    #     layout="wide",
    #     initial_sidebar_state="expanded"
    # )
    
    # Initialize session state
    init_session_state()
    
    # 額外確保聊天歷史持久化
    ensure_chat_history_persistence()

    # Initialize the success message flag for sample data pasting if it doesn't exist
    if 'sample_data_pasted_success' not in st.session_state:
        st.session_state.sample_data_pasted_success = False
    
    # 頁面標題與簡介區
    col1, col2 = st.columns([5, 1])
    with col1:
        st.title('📊 GMAT 成績診斷平台 by Dustin')
        st.markdown('透過數據分析深入了解您的GMAT表現，找出關鍵改進點')
    
    # 建立主要導航
    main_tabs = st.tabs(["📥 數據輸入與分析", "📈 結果查看"])
    
    with main_tabs[0]:  # 數據輸入與分析標籤頁
        # 簡短使用指引（核心步驟）
        with st.expander("快速使用指南 👉", expanded=False):
            st.markdown("""
            1. **準備數據**: 確保有Quantitative、Verbal和Data Insights三科目的數據
            2. **輸入數據**: 在下方四個標籤中分別上傳或貼上數據，以及在Total頁籤中調整分數
            3. **檢查預覽**: 確認數據正確並標記無效題目（時間壓力下倉促做題或猜題）
            4. **設定參數**: 在側邊欄調整分析參數（可選）
            5. **開始分析**: 點擊紅色分析按鈕
            """)
            
        # --- Disclaimer & Tutorial Links ---
        disclaimer_warning = st.expander("重要聲明與使用條款（使用即代表同意）", expanded=False)
        with disclaimer_warning:
            st.markdown("""
            ### 請仔細閱讀以下說明：

            本分析工具提供的是基於您輸入數據的純量化分析。分析的準確性高度依賴您所輸入數據的完整性與正確性。本工具採用預設參數與標準化診斷邏輯進行運算，其中：

            1.  **題目難度值**：報告中所使用的題目難度數據是基於內部模型的 IRT 模擬估計值，其目的是為了在本分析框架內進行相對比較與診斷，並不代表 GMAT 官方考試的真實題目難度。
            2.  **數據篩選**：分析過程可能已根據規則（例如：作答時間異常等）自動篩選部分被判定為無效的數據點。

            因此，本報告產出的所有診斷標籤、分析洞見與建議行動，均為量化數據分析的初步結果，僅供參考，不能完全取代實際情況的判斷。

            我們強烈建議您將此量化報告作為輔助工具，並與經驗豐富的 GMAT 教師或專業顧問一同檢視。透過專業人士進一步的「質化分析」（例如：探討具體錯誤思路、解題習慣、心態影響等），才能更深入、準確地解讀您的表現，找出根本問題，並制定最有效的個人化學習與備考策略。

            ---

            ### 數據使用與反饋：

            *   **數據收集同意**：當您使用本工具並上傳您的 GMAT 成績單數據時，即表示您理解並同意授權開發者（我）收集這些數據，用於後續模型優化、學術研究或其他相關分析目的。
            *   **去識別化責任**：為保護您的個人隱私，請務必在上傳前，仔細檢查並手動去除您成績單數據中的所有個人身份識別資訊（例如：姓名、考生 ID、考試中心、電子郵件地址等）。確保您上傳的數據已無法追溯到您個人。請謹慎操作。
            *   **問題反饋**：歡迎您透過 GitHub Issues 提交使用反饋、發現的問題或建議。請至：https://github.com/danyuchn/GMAT-score-report-analysis/issues
            """)
            
        tutorial_help = st.expander("完整使用說明", expanded=False)
        with tutorial_help:
            st.markdown("""
            **GMAT 成績診斷平台使用說明**

            **1. 歡迎！本工具能做什麼？**

            歡迎使用 GMAT 成績診斷平台！這個工具旨在幫助 GMAT 考生和教學者：

            - **超越單純分數：** 不只看對錯，更深入分析您在 GMAT 各科目 (Quantitative, Verbal, Data Insights) 表現背後的根本原因。
            - **找出弱點模式：** 識別您在特定題型、知識點或技能上的錯誤模式、時間管理問題或不穩定的概念掌握（例如 Special Focus Errors, SFE）。
            - **獲得個人化建議：** 根據診斷結果，提供具體的練習方向，包括建議的練習難度和起始時間限制。
            - **提升備考效率：** 讓您的練習更有針對性，把時間花在最需要加強的地方。

            **2. 開始之前：準備您的成績單數據**

            **「數據品質是診斷準確的基石！」** 請務必準備符合格式要求的數據。

            - **數據來源：** 您可以使用官方增強版成績單 (ESR)、官方練習 (Official Practice Exams)、第三方模考平台，或您自己記錄的練習數據，只要符合以下格式即可。
            - **格式要求：**
                - 需要**分別**準備 Quantitative (Q), Verbal (V), Data Insights (DI) 三個科目的數據。
                - 您可以上傳 **CSV 檔案**（檔案大小限制 1MB）或直接從 **Excel/表格** 複製數據並貼上。
            - **必要欄位（欄位標題須完全符合，大小寫/空格敏感）：**
                - **通用欄位:**
                    - `Question`: 題號 (必須是從 1 開始的正整數)
                    - `Response Time (Minutes)`: 每題作答時間 (分鐘，必須是正數，例如 1.5 或 2)
                    - `Performance`: 作答表現 (必須是 'Correct' 或 'Incorrect' 這兩種字串)
                - **科目特定欄位:**
                    - `Content Domain` (Q 和 DI 科目需要):
                        - Q: 'Algebra' 或 'Arithmetic'
                        - DI: 'Math Related' 或 'Non-Math Related'
                    - `Question Type` (Q, V, DI 都需要):
                        - Q: 'REAL' 或 'PURE' (注意是大寫)
                        - V: 'Critical Reasoning' 或 'Reading Comprehension'
                        - DI: 'Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table' (或 'Graphs and Tables')
                    - `Fundamental Skills` (Q 和 V 科目需要):
                        - Q: 例如 'Rates/Ratio/Percent', 'Value/Order/Factors', 'Equal/Unequal/ALG', 'Counting/Sets/Series/Prob/Stats' (允許常見的英文同義詞或格式變體，系統會嘗試自動校正)
                        - V: 例如 'Plan/Construct', 'Identify Stated Idea', 'Identify Inferred Idea', 'Analysis/Critique'
            - **重要：去識別化 (De-identification)**
                - **在上傳或貼上數據前，請務必、務必、務必仔細檢查並手動移除所有可能識別您個人身份的資訊！** 這包括但不限於：您的姓名、考生 ID (Candidate ID)、考試中心資訊、電子郵件地址等。
                - 您對確保數據匿名負有完全責任。本工具會收集您上傳的匿名數據用於模型改進與分析。

            **3. 如何使用本工具：一步步指南**

            - **步驟一：輸入數據**
                - 點擊上方的分頁標籤，分別進入 Quantitative (Q), Verbal (V), 和 Data Insights (DI) 的輸入區。
                - 在每個分頁中，選擇「上傳 CSV 檔案」或在文字框中「貼上 Excel 資料」。
                - 成功讀取後，下方會出現數據預覽和編輯器。
            - **步驟二：預覽、編輯與標記無效數據**
                - 在數據編輯器中，檢查您的數據是否讀取正確。
                - **關鍵步驟：** 對於您確定是因時間壓力過大、倉促猜測、分心等原因而「非正常作答」的題目，請勾選該行最左側的 **"是否草率做題？ (手動標記)"** 核取方塊。系統可能會根據時間自動預先勾選部分題目，但您的手動標記會優先採用。
                - 您也可以在編輯器中直接修正明顯的數據錯誤。
            - **步驟三：設定分析參數 (側邊欄)**
                - **IRT 模擬設定：** 您可以設定 Q, V, DI 各科的初始能力估計值 (Theta)。如果您不確定，**建議保留預設值 0.0**。
                - **OpenAI 設定 (選用)：** 如果您擁有 OpenAI API Key 並希望使用 AI 問答和報告整理功能，請在此輸入。否則請留空。
            - **步驟四：開始分析**
                - **重要：** 只有當您為 **Q, V, DI 三個科目都成功載入了有效數據**（通過驗證且無錯誤訊息）後，主頁面下方的 **"開始分析"** 按鈕才會變為可用狀態。
                - 如果按鈕不可用，請檢查上方是否有紅色錯誤訊息或缺少科目的提示。
                - 點擊 "開始分析" 按鈕。頁面會顯示進度條和目前的分析步驟。請稍候片刻。

            **4. 理解您的診斷報告**

            分析完成後，結果會顯示在「結果查看」標籤頁中：

            - **各科目結果分頁 (例如 "Q 科結果")：**
                - **能力估計 (Theta) 走勢圖：** 顯示系統模擬出的您的能力值 (Theta) 在作答過程中的變化趨勢。曲線向上表示能力估計值提升。
                - **診斷報告 (文字摘要)：** 以自然語言呈現詳細的分析結果，包含：
                    - 整體時間壓力評估
                    - 各維度（如題型、難度、技能）的表現概覽
                    - 核心問題診斷（錯誤模式、SFE 不穩定點等）
                    - 特殊行為模式觀察（如開頭搶快、潛在粗心等）
                    - 需要鞏固的基礎知識領域
                    - 個人化的練習計劃與建議 (包含建議難度 Y 和起始時間 Z)
                - **詳細數據表：** 包含您輸入的數據，以及系統計算出的診斷標籤，例如：模擬難度、時間表現分類 (快/慢/正常)、是否 SFE、是否超時、是否被標記為無效等。表格有顏色標示：紅色文字表示答錯，藍色文字表示用時超時，灰色文字表示該題被標記為無效。
                - **下載按鈕：** 您可以將帶有診斷標籤的詳細數據下載為 Excel 檔案，方便離線查看或與教師討論。
            - **✨ AI 匯總建議分頁 (若您提供了 OpenAI Key 且分析成功)：**
                - 此分頁由 AI (o4-mini 模型) 自動整理生成。
                - 它會從 Q, V, DI 三份報告中，**僅提取「練習建議」和「後續行動」** 這兩個部分的內容，合併在一起，方便您快速概覽最重要的行動項目。
                - **注意：** 此為 AI 提取的摘要，請務必對照各科目的完整報告原文，以確保理解完整。

            **5. AI 問答功能 (若您提供了 OpenAI Key)**

            - 如果分析成功且您輸入了有效的 OpenAI API Key，頁面最下方會出現一個**「與 AI 對話」**的聊天框。
            - 您可以針對**本次生成的報告內容和詳細數據**向 AI 提問。例如：
                - "請解釋一下我在 Q 科的 SFE 錯誤是什麼意思？"
                - "V 科報告裡的 'Slow & Right' 具體指哪幾題？"
                - "幫我總結一下 DI 科目的練習建議。"
                - "第 10 題的診斷標籤有哪些？"
            - **請注意：** AI 的回答**完全基於**本次分析產出的報告和數據。它無法提供超出這些資訊範圍的通用 GMAT 知識或建議。

            **6. 常見問題 (FAQ)**

            - **Q: "開始分析" 按鈕為什麼不能點？**
                - A: 請確保您已經在 Q, V, DI 三個分頁都成功上傳或貼上了數據，並且頁面上方沒有顯示紅色的驗證錯誤訊息。必須三個科目都有有效數據才能開始。
            - **Q: 我上傳/貼上的數據好像讀取不對或報錯？**
                - A: 請仔細檢查您的數據格式是否符合第 2 節的要求，特別是欄位標題是否完全一致、數據類型是否正確（時間是數字、表現是'Correct'/'Incorrect'等）。常見錯誤包含：欄位標題打錯字、多了空格、CSV 逗號使用不當、貼上時格式混亂等。
            - **Q: 報告裡的「難度」是怎麼來的？**
                - A: 這個難度是工具內部透過 IRT 模擬演算法，根據您的作答模式（對錯順序）估計出來的相對難度值，僅用於本次診斷分析，並非官方公佈的題目難度。
            - **Q: AI 功能（匯總建議、對話）無法使用？**
                - A: 請檢查您是否在側邊欄輸入了有效的 OpenAI API Key。同時，AI 功能僅在主分析成功完成後才會啟用。如果分析失敗，AI 功能也無法使用。
            """)
        
        st.divider()
        
        # --- Data Input Section ---
        input_dfs, validation_errors, data_source_types = setup_input_tabs(preprocess_helpers)
        
        # 檢查是否需要顯示範例數據
        if st.session_state.get('example_data_loaded', False) and st.session_state.get('example_data'):
            # 注入範例數據到input_dfs
            for subject in SUBJECTS:
                if subject in st.session_state['example_data']:
                    if input_dfs.get(subject) is None:  # 只有在尚未輸入數據時才注入
                        example_df = st.session_state['example_data'][subject].copy()
                        # 添加必要的列
                        example_df['is_manually_invalid'] = False
                        example_df['Subject'] = subject
                        
                        # 重設索引以避免潛在的索引問題
                        example_df = example_df.reset_index(drop=True)
                        
                        # 將原始數據重命名為標準化列名
                        rename_map = BASE_RENAME_MAP.copy()
                        if 'Question' in example_df.columns:
                            rename_map['Question'] = 'question_position'
                        if 'Response Time (Minutes)' in example_df.columns:
                            rename_map['Response Time (Minutes)'] = 'question_time'
                        if 'Performance' in example_df.columns:
                            rename_map['Performance'] = 'is_correct'
                            # 轉換Performance列為is_correct
                            example_df['is_correct'] = example_df['Performance'].apply(
                                lambda x: x == 'Correct' if isinstance(x, str) else bool(x)
                            )
                        
                        example_df.rename(columns=rename_map, inplace=True)
                        
                        input_dfs[subject] = example_df
                        validation_errors[subject] = []
                        data_source_types[subject] = "範例數據"
            
            # 清除標誌，避免重複加載
            st.session_state['example_data_loaded'] = False
        
        # Store in session state
        st.session_state.input_dfs = input_dfs
        st.session_state.validation_errors = validation_errors
        st.session_state.data_source_types = data_source_types
        
        # Combine Input Data
        df_combined_input, loaded_subjects, valid_input_dfs = combine_input_data(input_dfs, SUBJECTS)
        
        # Check if any validation errors occurred across all tabs
        any_validation_errors = any(bool(warnings) for warnings in validation_errors.values())
        
        # Display Analysis Button with improved styling
        st.divider()
        st.subheader("3. 開始分析")
        button_clicked, button_disabled, button_message = display_analysis_button(
            df_combined_input, 
            any_validation_errors, 
            input_dfs,
            SUBJECTS
        )
        
        # --- Analysis Execution Block ---
        if button_clicked and not button_disabled:
            # This is a new analysis request
            reset_session_for_new_upload() # Clear previous *results* and *completion status*
            st.session_state.analysis_run = True # Mark that analysis should run *now*
                                               # This flag will persist for the current script run
                                               # to ensure results are displayed.
            st.session_state.diagnosis_complete = False # Ensure it starts as not complete

            if df_combined_input is not None:
                with st.spinner("正在執行 IRT 模擬與診斷..."):
                    # --- Add to CSV ---
                    records_to_add = []
                    # Generate a unique student_id for this upload session if not available
                    # For simplicity, using a fixed student_id for now, or derive from session
                    student_id_for_batch = st.session_state.get("student_id_for_upload", f"student_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
                    st.session_state.student_id_for_upload = student_id_for_batch # Store for potential reuse in the session
                    
                    test_date_for_batch = datetime.date.today().isoformat()

                    # Calculate per-section totals first
                    section_stats = {}
                    if 'Subject' in df_combined_input.columns and 'question_time' in df_combined_input.columns:
                        for subject_name, group in df_combined_input.groupby('Subject'):
                            if subject_name in SUBJECTS: # Process only Q, V, DI
                                # Ensure question_time is numeric before summing
                                numeric_times = pd.to_numeric(group['question_time'], errors='coerce')
                                section_stats[subject_name] = {
                                    'total_questions': len(group),
                                    'total_time': numeric_times.sum()
                                }

                    for index, row in df_combined_input.iterrows():
                        record = {}
                        gmat_section = row.get("Subject")
                        
                        # Skip if not a main GMAT section (e.g. 'Total' if it exists in df_combined_input)
                        if gmat_section not in SUBJECTS:
                            continue
                            
                        record["student_id"] = student_id_for_batch
                        # Create a unique test_instance_id for each section within the batch
                        record["test_instance_id"] = f"{student_id_for_batch}_{gmat_section}_{test_date_for_batch.replace('-', '')}_upload"
                        record["gmat_section"] = gmat_section
                        record["test_date"] = test_date_for_batch
                        
                        question_pos = row.get("question_position", index + 1)
                        record["question_id"] = f"{gmat_section}_{question_pos}_{test_date_for_batch.replace('-', '')}"
                        record["question_position"] = int(question_pos) if pd.notnull(question_pos) else index + 1
                        # Ensure question_time is numeric before converting to float
                        question_time_val = row.get("question_time", 0.0)
                        if isinstance(question_time_val, str):
                            question_time_val = pd.to_numeric(question_time_val, errors='coerce')
                        record["question_time_minutes"] = float(question_time_val) if pd.notnull(question_time_val) else 0.0
                        
                        is_correct_val = row.get("is_correct")
                        if isinstance(is_correct_val, bool):
                            record["is_correct"] = 1 if is_correct_val else 0
                        elif isinstance(is_correct_val, str):
                            record["is_correct"] = 1 if is_correct_val.lower() == 'correct' else 0
                        else:
                            record["is_correct"] = 0 # Default if unknown format
                            
                        # question_difficulty might not be present in uploaded data, default to 0 or a placeholder
                        record["question_difficulty"] = float(row.get("question_difficulty", 0.0)) 
                        record["question_type"] = str(row.get("question_type", ""))
                        record["question_fundamental_skill"] = str(row.get("question_fundamental_skill", ""))
                        record["content_domain"] = str(row.get("content_domain", ""))
                        
                        if gmat_section in section_stats:
                            record["total_questions_in_section"] = int(section_stats[gmat_section]['total_questions'])
                            # Safely convert total_time to float, handle NaN values
                            total_time_val = section_stats[gmat_section]['total_time']
                            record["total_section_time_minutes"] = float(total_time_val) if pd.notnull(total_time_val) else 0.0
                        else:
                            record["total_questions_in_section"] = 0 # Should not happen if Subject is Q,V,DI
                            record["total_section_time_minutes"] = 0.0

                        record["max_allowed_section_time_minutes"] = 45.0 # Standard or from config
                        
                        # Ensure all GMAT_PERFORMANCE_HEADERS are present, even if with None or default values, except record_timestamp
                        for header in GMAT_PERFORMANCE_HEADERS:
                            if header not in record and header != "record_timestamp":
                                record[header] = None 
                        records_to_add.append(record)
                    
                    if records_to_add:
                        if add_gmat_performance_record(records_to_add):
                            # st.toast(f"已成功將 {len(records_to_add)} 筆資料附加到 gmat_performance_data.csv", icon="✅") # This line will be commented out
                            pass # Add pass if commenting out the toast makes the block empty
                        else:
                            st.toast("附加資料到 gmat_performance_data.csv 時發生錯誤。", icon="⚠️")
                    else:
                        st.toast("沒有可附加到 gmat_performance_data.csv 的資料。", icon="ℹ️")
                    # --- End Add to CSV ---
                    
                    # --- 添加主觀時間壓力報告到 CSV ---
                    subjective_reports_added = 0
                    
                    for subject in SUBJECTS:
                        subject_key = subject.lower()
                        time_pressure_key = f"{subject_key}_time_pressure"
                        
                        if time_pressure_key in st.session_state:
                            time_pressure_value = int(st.session_state[time_pressure_key])
                            test_instance_id = f"{student_id_for_batch}_{subject}_{test_date_for_batch.replace('-', '')}_upload"
                            
                            # 創建主觀報告記錄
                            subjective_report = {
                                "student_id": student_id_for_batch,
                                "test_instance_id": test_instance_id,
                                "gmat_section": subject,
                                "subjective_time_pressure": time_pressure_value,
                                "report_collection_timestamp": datetime.datetime.now().isoformat()
                            }
                            
                            # 將報告寫入 CSV
                            if add_subjective_report_record(subjective_report):
                                subjective_reports_added += 1
                            else:
                                st.toast(f"添加 {subject} 科目的主觀時間壓力報告到 CSV 時發生錯誤。", icon="⚠️")
                    
                    if subjective_reports_added > 0:
                        pass # 成功添加報告
                    # --- 添加主觀時間壓力報告到 CSV 結束 ---

                    run_analysis(df_combined_input) # This will update diagnosis_complete and analysis_error
                
                if st.session_state.diagnosis_complete:
                    st.success("分析完成！請前往頁首的「結果查看」分頁查看診斷結果。")
            else:
                # If there's no data, then analysis didn't really "run" in a meaningful way.
                st.session_state.analysis_run = False 
                st.error("沒有合併的數據可以分析，無法啟動分析。")
    
    with main_tabs[1]:  # 結果查看標籤頁
        if st.session_state.get("diagnosis_complete", False):
            display_results()
        else:
            # 顯示尚未分析的提示
            st.info("尚未執行分析。請先在「數據輸入與分析」標籤中上傳數據並執行分析。")
            st.markdown("""
            ### 分析流程說明
            
            1. 在「數據輸入與分析」標籤中上傳三個科目的數據
            2. 確保數據格式正確並通過驗證
            3. 點擊「開始分析」按鈕
            4. 分析完成後，結果將顯示在此頁面
            """)
            
    # --- Sidebar Settings ---
    st.sidebar.subheader("分析設定")
    
    # 添加範例數據導入功能
    with st.sidebar.expander("📊 範例數據", expanded=True):
        st.markdown("### 範例數據導入")
        st.markdown("點擊下方按鈕導入範例做題數據，方便體驗系統功能")
        
        st.button("一鍵導入範例數據", 
                  key="load_sample_data_pasted", 
                  use_container_width=True,
                  on_click=load_sample_data_callback) # Use on_click callback

        if st.session_state.get('sample_data_pasted_success', False):
            st.success("範例數據已成功填入各科目的文本框！請檢查「數據輸入與分析」頁面。")
            st.session_state.sample_data_pasted_success = False # Reset flag
            
    # OpenAI設定區塊（移到上方更明顯的位置）
    with st.sidebar.expander("🤖 AI功能設定", expanded=False):
        master_key_input = st.text_input(
            "輸入管理員金鑰啟用 AI 問答功能：",
            type="password",
            key="master_key_input",
            value=st.session_state.get('master_key', ''),
            help="輸入有效管理金鑰並成功完成分析後，下方將出現 AI 對話框。管理金鑰請向系統管理員索取。"
        )

        # Update session state when input changes
        if master_key_input:
            st.session_state.master_key = master_key_input
            # 使用新的方法基於master key初始化OpenAI客戶端
            from gmat_diagnosis_app.services.openai_service import initialize_openai_client_with_master_key
            if initialize_openai_client_with_master_key(master_key_input):
                st.session_state.show_chat = True
                st.session_state.chat_history = []
                st.success("管理金鑰驗證成功，AI功能已啟用！")
            else:
                st.session_state.show_chat = False
                st.session_state.chat_history = []
                st.error("管理金鑰驗證失敗，無法啟用AI功能。")
        else:
            st.session_state.master_key = None
            st.session_state.show_chat = False
            st.session_state.chat_history = []

    # --- IRT Simulation Settings ---
    with st.sidebar.expander("📊 IRT模擬設定", expanded=False):
        st.session_state.initial_theta_q = st.number_input(
            "Q 科目初始 Theta 估計", 
            value=st.session_state.initial_theta_q, 
            step=0.1,
            key="theta_q_input"
        )
        st.session_state.initial_theta_v = st.number_input(
            "V 科目初始 Theta 估計", 
            value=st.session_state.initial_theta_v, 
            step=0.1,
            key="theta_v_input"
        )
        st.session_state.initial_theta_di = st.number_input(
            "DI 科目初始 Theta 估計", 
            value=st.session_state.initial_theta_di, 
            step=0.1,
            key="theta_di_input"
        )

    # --- Manual IRT Adjustment Inputs in Sidebar ---
    with st.sidebar.expander("🔧 手動調整題目", expanded=False):
        st.markdown("#### 手動調整題目正確性")
        st.markdown("（僅影響IRT模擬）")
        
        # 使用標籤頁節省空間
        q_tab, v_tab, di_tab = st.tabs(["Q", "V", "DI"])
        
        with q_tab:
            st.session_state.q_incorrect_to_correct_qns = st.text_input(
                "由錯改對題號", 
                value=st.session_state.q_incorrect_to_correct_qns,
                placeholder="例: 1,5,10",
                key="q_i_to_c_input"
            )
            st.session_state.q_correct_to_incorrect_qns = st.text_input(
                "由對改錯題號", 
                value=st.session_state.q_correct_to_incorrect_qns,
                placeholder="例: 2,7,12",
                key="q_c_to_i_input"
            )
        
        with v_tab:
            st.session_state.v_incorrect_to_correct_qns = st.text_input(
                "由錯改對題號", 
                value=st.session_state.v_incorrect_to_correct_qns,
                placeholder="例: 1,5,10",
                key="v_i_to_c_input"
            )
            st.session_state.v_correct_to_incorrect_qns = st.text_input(
                "由對改錯題號", 
                value=st.session_state.v_correct_to_incorrect_qns,
                placeholder="例: 2,7,12",
                key="v_c_to_i_input"
            )
        
        with di_tab:
            st.session_state.di_incorrect_to_correct_qns = st.text_input(
                "由錯改對題號", 
                value=st.session_state.di_incorrect_to_correct_qns,
                placeholder="例: 1,5,10",
                key="di_i_to_c_input"
            )
            st.session_state.di_correct_to_incorrect_qns = st.text_input(
                "由對改錯題號", 
                value=st.session_state.di_correct_to_incorrect_qns,
                placeholder="例: 2,7,12",
                key="di_c_to_i_input"
            )
    
    # 頁尾信息
    st.markdown("---")
    st.caption("有問題或建議？請前往 [GitHub Issues](https://github.com/danyuchn/GMAT-score-report-analysis/issues) 提交反饋")

if __name__ == "__main__":
    main() 