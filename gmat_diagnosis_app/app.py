# -*- coding: utf-8 -*- # Ensure UTF-8 encoding for comments/strings
"""
GMAT診斷應用主程序
整合各個模組以提供完整的GMAT診斷功能
"""

import sys
import os
import io
import pandas as pd
import streamlit as st
import numpy as np
import logging
import openai
import plotly.graph_objects as go

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
    # from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis_processed # Moved
    # from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q # Moved
    
    # Import our modularized components
    from gmat_diagnosis_app.constants.config import (
        SUBJECTS, MAX_FILE_SIZE_MB, MAX_FILE_SIZE_BYTES, BANK_SIZE, RANDOM_SEED,
        SUBJECT_SIM_PARAMS, FINAL_DIAGNOSIS_INPUT_COLS, BASE_RENAME_MAP,
        REQUIRED_ORIGINAL_COLS, EXCEL_COLUMN_MAP
    )
    # from gmat_diagnosis_app.utils.validation import validate_dataframe
    # from gmat_diagnosis_app.utils.data_processing import process_subject_tab
    # from gmat_diagnosis_app.utils.styling import apply_styles
    # from gmat_diagnosis_app.utils.excel_utils import to_excel
    from gmat_diagnosis_app.services.openai_service import (
        summarize_report_with_openai, generate_ai_consolidated_report,
        get_chat_context, get_openai_response
    )
    # from gmat_diagnosis_app.services.plotting_service import create_theta_plot
    from gmat_diagnosis_app.ui.results_display import display_results, display_subject_results
    from gmat_diagnosis_app.ui.chat_interface import display_chat_interface
    from gmat_diagnosis_app.ui.input_tabs import setup_input_tabs, combine_input_data, display_analysis_button
    from gmat_diagnosis_app.session_manager import init_session_state, reset_session_for_new_upload # Added import
    from gmat_diagnosis_app.analysis_orchestrator import run_analysis # Added import
    
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

# --- Main Application ---
def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Set page title
    st.title('GMAT 成績診斷平台 by Dustin')

    # --- Disclaimer Expander ---
    disclaimer_markdown = """
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
"""
    with st.expander("重要聲明與使用條款（使用即代表同意）", expanded=False):
        st.markdown(disclaimer_markdown, unsafe_allow_html=True)

    # --- Tutorial Expander ---
    tutorial_markdown = """
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

分析完成後，結果會顯示在新的分頁中：

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

**6. 重要提示與免責聲明**

- **僅供參考：** 本工具提供的所有分析結果、診斷標籤和建議，都屬於輔助性質，旨在提供洞見，**不能替代**您對實際情況的判斷或專業教師的指導。
- **IRT 模擬：** 報告中的題目難度值是基於內部 IRT 模型模擬的結果，用於內部診斷比較，**不代表**官方 GMAT 考試的實際題目難度或評分機制。
- **量化分析為主：** 本工具進行的是純粹的量化數據分析。數據得出的標籤和建議，強烈建議需要由經驗豐富的 GMAT 教師進行**質化的解讀**，才能找到最根本的原因。
- **數據收集與隱私：** 使用本工具即表示您同意我們收集您上傳的（已被您去識別化的）數據，用於工具改進與分析。請務必在上傳前做好去識別化工作。詳情請見彈窗警語。
- **參數說明：** 分析中使用的閾值（如超時標準）是基於經驗設定的啟發式參數，可能需要未來根據更多數據進行優化。

**7. 常見問題 (FAQ)**

- **Q: "開始分析" 按鈕為什麼不能點？**
    - A: 請確保您已經在 Q, V, DI 三個分頁都成功上傳或貼上了數據，並且頁面上方沒有顯示紅色的驗證錯誤訊息。必須三個科目都有有效數據才能開始。
- **Q: 我上傳/貼上的數據好像讀取不對或報錯？**
    - A: 請仔細檢查您的數據格式是否符合第 2 節的要求，特別是欄位標題是否完全一致、數據類型是否正確（時間是數字、表現是'Correct'/'Incorrect'等）。常見錯誤包含：欄位標題打錯字、多了空格、CSV 逗號使用不當、貼上時格式混亂等。
- **Q: 報告裡的「難度」是怎麼來的？**
    - A: 這個難度是工具內部透過 IRT 模擬演算法，根據您的作答模式（對錯順序）估計出來的相對難度值，僅用於本次診斷分析，並非官方公佈的題目難度。
- **Q: AI 功能（匯總建議、對話）無法使用？**
    - A: 請檢查您是否在側邊欄輸入了有效的 OpenAI API Key。同時，AI 功能僅在主分析成功完成後才會啟用。如果分析失敗，AI 功能也無法使用。
- **Q: 我發現了問題或有建議，如何反饋？**
    - A: 歡迎透過專案的 GitHub Issues 頁面提交反饋。連結請見彈窗警語或聯繫開發者。

---

希望這份說明能幫助您順利使用 GMAT 成績診斷平台！祝您備考順利！
"""
    with st.expander("GMAT 成績診斷平台使用說明", expanded=False):
        st.markdown(tutorial_markdown, unsafe_allow_html=True)
        
    # --- Sidebar Settings ---
    st.sidebar.subheader("OpenAI 設定 (選用)")
    api_key_input = st.sidebar.text_input(
        "輸入您的 OpenAI API Key 啟用 AI 問答：",
        type="password",
        key="openai_api_key_input",
        value=st.session_state.get('openai_api_key', ''),
        help="輸入有效金鑰並成功完成分析後，下方將出現 AI 對話框。"
    )

    # Update session state when input changes
    if api_key_input:
        st.session_state.openai_api_key = api_key_input
    else:
        st.session_state.openai_api_key = None
        st.session_state.show_chat = False
        st.session_state.chat_history = []

    st.sidebar.divider()

    # --- IRT Simulation Settings ---
    st.sidebar.subheader("IRT 模擬設定")
    st.session_state.initial_theta_q = st.sidebar.number_input(
        "Q 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_q, 
        step=0.1,
        key="theta_q_input"
    )
    st.session_state.initial_theta_v = st.sidebar.number_input(
        "V 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_v, 
        step=0.1,
        key="theta_v_input"
    )
    st.session_state.initial_theta_di = st.sidebar.number_input(
        "DI 科目初始 Theta 估計", 
        value=st.session_state.initial_theta_di, 
        step=0.1,
        key="theta_di_input"
    )

    # --- Manual IRT Adjustment Inputs in Sidebar ---
    st.sidebar.markdown("#### 手動調整題目正確性 (僅影響IRT模擬)")
    
    # Quant
    st.sidebar.markdown("##### 計量 (Quant)")
    st.session_state.q_incorrect_to_correct_qns = st.sidebar.text_input(
        "Q 由錯改對題號", 
        value=st.session_state.q_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="q_i_to_c_input"
    )
    st.session_state.q_correct_to_incorrect_qns = st.sidebar.text_input(
        "Q 由對改錯題號", 
        value=st.session_state.q_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="q_c_to_i_input"
    )

    # Verbal
    st.sidebar.markdown("##### 語文 (Verbal)")
    st.session_state.v_incorrect_to_correct_qns = st.sidebar.text_input(
        "V 由錯改對題號", 
        value=st.session_state.v_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="v_i_to_c_input"
    )
    st.session_state.v_correct_to_incorrect_qns = st.sidebar.text_input(
        "V 由對改錯題號", 
        value=st.session_state.v_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="v_c_to_i_input"
    )

    # Data Insights (DI)
    st.sidebar.markdown("##### 資料洞察 (DI)")
    st.session_state.di_incorrect_to_correct_qns = st.sidebar.text_input(
        "DI 由錯改對題號", 
        value=st.session_state.di_incorrect_to_correct_qns,
        placeholder="例: 1,5,10",
        key="di_i_to_c_input"
    )
    st.session_state.di_correct_to_incorrect_qns = st.sidebar.text_input(
        "DI 由對改錯題號", 
        value=st.session_state.di_correct_to_incorrect_qns,
        placeholder="例: 2,7,12",
        key="di_c_to_i_input"
    )
    st.sidebar.divider() # Add a divider after these inputs
    
    # --- Data Input Section ---
    input_dfs, validation_errors, data_source_types = setup_input_tabs(preprocess_helpers)
    
    # Store in session state
    st.session_state.input_dfs = input_dfs
    st.session_state.validation_errors = validation_errors
    st.session_state.data_source_types = data_source_types
    
    # Combine Input Data
    df_combined_input, loaded_subjects, valid_input_dfs = combine_input_data(input_dfs, SUBJECTS)
    
    # Check if any validation errors occurred across all tabs
    any_validation_errors = any(bool(warnings) for warnings in validation_errors.values())
    
    # Display Analysis Button
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
            st.header("2. 執行 IRT 模擬與診斷")
            run_analysis(df_combined_input) # This will update diagnosis_complete and analysis_error
        else:
            # If there's no data, then analysis didn't really "run" in a meaningful way.
            st.session_state.analysis_run = False 
            st.warning("沒有合併的數據可以分析，無法啟動分析。")
    
    # Note: The elif block that was here for `st.session_state.analysis_run and not st.session_state.diagnosis_complete`
    # has been removed as its primary utility was with st.rerun() for iterative display on slow steps.
    # With the current synchronous call to run_analysis, this simplified structure should be sufficient.
    
    # --- Results Display ---
    # Show results if analysis_run was set to True by the button click (meaning an analysis was attempted)
    if st.session_state.analysis_run:
        display_results()
    
    # --- Chat Interface ---
    display_chat_interface(st.session_state)

if __name__ == "__main__":
    main() 