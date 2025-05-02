import sys
import os

# Get the directory containing app.py
app_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(app_dir)

# Add the project root to the beginning of sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
from io import StringIO # Use io.StringIO directly
from gmat_diagnosis_app import irt_module as irt # Import using absolute path
from gmat_diagnosis_app.diagnosis_module import run_diagnosis # Import using absolute path
import os # For environment variables
import openai # Import OpenAI library

# --- Initialize Session State ---
# To track if analysis has been run and store results
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False
if 'report_string' not in st.session_state:
    st.session_state.report_string = None
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'final_thetas' not in st.session_state:
     st.session_state.final_thetas = {}


# --- Sidebar Settings (Keep as is) ---
st.sidebar.subheader("OpenAI 設定 (選用)")
api_key_input = st.sidebar.text_input(
    "輸入您的 OpenAI API Key：", 
    type="password", 
    help="或者設定 OPENAI_API_KEY 環境變數。用於生成文字摘要。"
)
openai_api_key = api_key_input if api_key_input else os.getenv("OPENAI_API_KEY")

st.sidebar.subheader("IRT 模擬設定")
initial_theta_q = st.sidebar.number_input("Q 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_v = st.sidebar.number_input("V 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_di = st.sidebar.number_input("DI 科目初始 Theta 估計", value=0.0, step=0.1)

BANK_SIZE = 1000 
TOTAL_QUESTIONS_Q = 21
TOTAL_QUESTIONS_V = 23
TOTAL_QUESTIONS_DI = 20
RANDOM_SEED = 1000 
# --- End Sidebar ---

st.title('GMAT 成績診斷平台')

# --- Data Input Section (Using Tabs) ---
st.header("1. 上傳或貼上各科成績單")

# Initialize DataFrames
df_q = None
df_v = None
df_di = None
data_sources = {}

tab_q, tab_v, tab_di = st.tabs(["Quantitative (Q)", "Verbal (V)", "Data Insights (DI)"])

with tab_q:
    st.subheader("Quantitative (Q) 資料輸入")
    uploaded_file_q = st.file_uploader("上傳 Q 科目 CSV 檔案", type="csv", key="q_uploader")
    pasted_data_q = st.text_area("或將 Q 科目 Excel 資料貼在此處：", height=150, key="q_paster")
    temp_df_q = None
    source_q = None
    if uploaded_file_q is not None:
        source_q = uploaded_file_q
    elif pasted_data_q:
        source_q = StringIO(pasted_data_q)
        
    if source_q is not None:
        try:
            temp_df_q = pd.read_csv(source_q, sep=None, engine='python')
            # Drop rows where all columns are NaN (completely empty rows)
            temp_df_q.dropna(how='all', inplace=True)

            # --- Standardize Columns (Handle potential 'Question' variations) ---
            rename_map_q = {
                # '﻿Question': 'question_position', # Old logic
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Content Domain': 'content_domain',
                'Fundamental Skills': 'question_fundamental_skill'
            }
            # Dynamically add the position mapping
            if '﻿Question' in temp_df_q.columns:
                rename_map_q['﻿Question'] = 'question_position'
            elif 'Question' in temp_df_q.columns: # Check for plain 'Question'
                rename_map_q['Question'] = 'question_position'

            # Apply only columns that exist
            cols_to_rename = {k: v for k, v in rename_map_q.items() if k in temp_df_q.columns}
            temp_df_q.rename(columns=cols_to_rename, inplace=True)
            
            # Standardize question_type AFTER renaming
            if 'question_type' in temp_df_q.columns:
                temp_df_q['question_type'] = temp_df_q['question_type'].astype(str).str.strip().str.upper()
            else:
                 st.warning("Q: 缺少 'question_type' 欄位。") # Warn but continue

            if 'Correct' in temp_df_q.columns:
                 # Convert to boolean consistently
                 temp_df_q['Correct'] = temp_df_q['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                 temp_df_q.rename(columns={'Correct': 'is_correct'}, inplace=True) # Rename to is_correct
            else:
                st.error("Q 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                temp_df_q = None

            if temp_df_q is not None:
                data_sources['Q'] = 'File Upload' if uploaded_file_q else 'Pasted Data'
                st.success(f"Q 科目資料讀取成功 ({data_sources['Q']})！")
                # Add subject identifier and rename
                temp_df_q['Subject'] = 'Q'

                # --- Ensure independent question_position for Q ---
                if 'question_position' not in temp_df_q.columns or pd.to_numeric(temp_df_q['question_position'], errors='coerce').isnull().any():
                    st.warning("Q: 正在根據原始順序重新生成 question_position。")
                    temp_df_q = temp_df_q.reset_index(drop=True)
                    temp_df_q['question_position'] = temp_df_q.index + 1
                else:
                    # Ensure it's integer type after validation
                    temp_df_q['question_position'] = pd.to_numeric(temp_df_q['question_position'], errors='coerce').astype('Int64')
                # --- End Ensure ---
                df_q = temp_df_q # Assign to df_q here
                with st.expander("顯示 Q 資料預覽"): # Optional Preview Expander
                     st.dataframe(df_q.head())
        except Exception as e:
            st.error(f"處理 Q 科目資料時發生錯誤：{e}")
            df_q = None # Ensure df_q is None on error

with tab_v:
    st.subheader("Verbal (V) 資料輸入")
    uploaded_file_v = st.file_uploader("上傳 V 科目 CSV 檔案", type="csv", key="v_uploader")
    pasted_data_v = st.text_area("或將 V 科目 Excel 資料貼在此處：", height=150, key="v_paster")
    temp_df_v = None
    source_v = None
    if uploaded_file_v is not None:
        source_v = uploaded_file_v
    elif pasted_data_v:
        source_v = StringIO(pasted_data_v)
        
    if source_v is not None:
        try:
            temp_df_v = pd.read_csv(source_v, sep=None, engine='python')
            # Drop rows where all columns are NaN (completely empty rows)
            temp_df_v.dropna(how='all', inplace=True)

            rename_map_v = {
                # '﻿Question': 'question_position',
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Fundamental Skills': 'question_fundamental_skill'
            }
            # Dynamically add the position mapping
            if '﻿Question' in temp_df_v.columns:
                rename_map_v['﻿Question'] = 'question_position'
            elif 'Question' in temp_df_v.columns:
                rename_map_v['Question'] = 'question_position'

            cols_to_rename = {k: v for k, v in rename_map_v.items() if k in temp_df_v.columns}
            temp_df_v.rename(columns=cols_to_rename, inplace=True)
            
            # Standardize question_type AFTER renaming (Remove .str.upper() for V)
            if 'question_type' in temp_df_v.columns:
                temp_df_v['question_type'] = temp_df_v['question_type'].astype(str).str.strip() # Keep original case for V
            else:
                 st.warning("V: 缺少 'question_type' 欄位。") # Warn but continue

            if 'Correct' in temp_df_v.columns:
                 temp_df_v['Correct'] = temp_df_v['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                 temp_df_v.rename(columns={'Correct': 'is_correct'}, inplace=True) # Rename to is_correct
            else:
                 st.error("V 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                 temp_df_v = None

            if temp_df_v is not None:
                data_sources['V'] = 'File Upload' if uploaded_file_v else 'Pasted Data'
                st.success(f"V 科目資料讀取成功 ({data_sources['V']})！")
                # Add subject identifier and rename
                temp_df_v['Subject'] = 'V'

                # --- Ensure independent question_position for V ---
                if 'question_position' not in temp_df_v.columns or pd.to_numeric(temp_df_v['question_position'], errors='coerce').isnull().any():
                    st.warning("V: 正在根據原始順序重新生成 question_position。")
                    temp_df_v = temp_df_v.reset_index(drop=True)
                    temp_df_v['question_position'] = temp_df_v.index + 1
                else:
                    # Ensure it's integer type after validation
                    temp_df_v['question_position'] = pd.to_numeric(temp_df_v['question_position'], errors='coerce').astype('Int64')
                # --- End Ensure ---
                df_v = temp_df_v # Assign to df_v here
                with st.expander("顯示 V 資料預覽"):
                     st.dataframe(df_v.head())
        except Exception as e:
            st.error(f"處理 V 科目資料時發生錯誤：{e}")
            df_v = None # Ensure df_v is None on error

with tab_di:
    st.subheader("Data Insights (DI) 資料輸入")
    uploaded_file_di = st.file_uploader("上傳 DI 科目 CSV 檔案", type="csv", key="di_uploader")
    pasted_data_di = st.text_area("或將 DI 科目 Excel 資料貼在此處：", height=150, key="di_paster")
    temp_df_di = None
    source_di = None
    if uploaded_file_di is not None:
        source_di = uploaded_file_di
    elif pasted_data_di:
        source_di = StringIO(pasted_data_di)

    if source_di is not None:
        try:
            temp_df_di = pd.read_csv(source_di, sep=None, engine='python')
            # Drop rows where all columns are NaN (completely empty rows)
            temp_df_di.dropna(how='all', inplace=True)

            rename_map_di = {
                # '﻿Question': 'question_position',
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Content Domain': 'content_domain'
            }
            # Dynamically add the position mapping
            if '﻿Question' in temp_df_di.columns:
                rename_map_di['﻿Question'] = 'question_position'
            elif 'Question' in temp_df_di.columns:
                rename_map_di['Question'] = 'question_position'

            cols_to_rename = {k: v for k, v in rename_map_di.items() if k in temp_df_di.columns}
            temp_df_di.rename(columns=cols_to_rename, inplace=True)
            
            # Standardize question_type AFTER renaming (Remove .str.upper() for DI)
            if 'question_type' in temp_df_di.columns:
                temp_df_di['question_type'] = temp_df_di['question_type'].astype(str).str.strip() # Keep original case for DI
            else:
                st.warning("DI: 缺少 'question_type' 欄位。") # Warn but continue
            
            if 'Correct' in temp_df_di.columns:
                 temp_df_di['Correct'] = temp_df_di['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
                 temp_df_di.rename(columns={'Correct': 'is_correct'}, inplace=True) # Rename to is_correct
            else:
                 st.error("DI 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                 temp_df_di = None

            if temp_df_di is not None:
                data_sources['DI'] = 'File Upload' if uploaded_file_di else 'Pasted Data'
                st.success(f"DI 科目資料讀取成功 ({data_sources['DI']})！")
                # Add subject identifier and rename
                temp_df_di['Subject'] = 'DI'

                # --- Ensure independent question_position for DI ---
                if 'question_position' not in temp_df_di.columns or pd.to_numeric(temp_df_di['question_position'], errors='coerce').isnull().any():
                    st.warning("DI: 正在根據原始順序重新生成 question_position。")
                    temp_df_di = temp_df_di.reset_index(drop=True)
                    temp_df_di['question_position'] = temp_df_di.index + 1
                else:
                    # Ensure it's integer type after validation
                    temp_df_di['question_position'] = pd.to_numeric(temp_df_di['question_position'], errors='coerce').astype('Int64')
                # --- End Ensure ---
                df_di = temp_df_di # Assign to df_di here
                with st.expander("顯示 DI 資料預覽"):
                     st.dataframe(df_di.head())
        except Exception as e:
            st.error(f"處理 DI 科目資料時發生錯誤：{e}")
            df_di = None # Ensure df_di is None on error

# --- Combine Input Data (After Tabs) ---
input_dfs = {'Q': df_q, 'V': df_v, 'DI': df_di}
loaded_subjects = {subj for subj, df in input_dfs.items() if df is not None}
df_combined_input = None
df_combined_input_list = [df for df in [df_q, df_v, df_di] if df is not None]

if df_combined_input_list:
     try:
         # Concatenate with ignore_index=True, but 'question_position' is already calculated per subject
         df_combined_input = pd.concat(df_combined_input_list, ignore_index=True)

         # Ensure 'question_position' column exists after concat (it should, unless all inputs failed processing)
         if 'question_position' not in df_combined_input.columns:
             st.error("合併後資料缺少 'question_position' 欄位，無法繼續。檢查各科數據處理。")
             df_combined_input = None
         elif df_combined_input['question_position'].isnull().any():
              st.error("合併後 'question_position' 欄位包含空值，無法繼續。檢查各科數據處理。")
              df_combined_input = None
         # else:
         #     # Optional: Sort for better viewing/debugging, though later logic sorts per subject
         #     df_combined_input.sort_values(by=['Subject', 'question_position'], inplace=True)

     except Exception as e:
         st.error(f"合併輸入資料時發生錯誤: {e}")
         df_combined_input = None
elif loaded_subjects: # Data was loaded but failed during processing within tabs
     st.warning("部分科目數據處理失敗，請檢查上方錯誤信息。")

# --- Analysis Trigger Button ---
st.divider() # Add a visual separator

if df_combined_input is not None:
    if st.button("🔍 開始分析", type="primary"):
        st.session_state.analysis_run = True
        # Reset previous results when starting new analysis
        st.session_state.report_string = None
        st.session_state.ai_summary = None
        st.session_state.final_thetas = {}
    else:
        # If button not clicked in this run, keep analysis_run as False unless it was already True
        # This prevents analysis from running just on widget interaction after first run
        # st.session_state.analysis_run = st.session_state.get('analysis_run', False) # Keep existing state if button not clicked
        pass # No need to explicitly set to false, just don't set to true

elif loaded_subjects: # Data loaded but failed combining
    st.error("無法合併輸入資料，請檢查各科數據格式。分析無法進行。")
else:
    st.info("請在上方分頁中為至少一個科目上傳或貼上資料。")

# --- Simulation, Processing, Diagnosis, and Output Tabs (Conditional Execution) ---
if st.session_state.analysis_run and df_combined_input is not None:

    st.header("2. 執行 IRT 模擬與診斷") # Combine headers
    all_simulation_histories = {} # Store histories per subject
    final_thetas = {}           # Store final theta per subject locally for this run
    df_final_for_diagnosis = None # Initialize

    # --- IRT Simulation ---
    simulation_success = True
    # with st.spinner("正在執行 IRT 模擬..."): # Replace with st.status
    with st.status("執行 IRT 模擬...", expanded=True) as status:
        st.write("初始化模擬題庫...")
        question_banks = {}
        try:
            # Create banks only for loaded subjects
            if 'Q' in loaded_subjects: question_banks['Q'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED)
            if 'V' in loaded_subjects: question_banks['V'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 1)
            if 'DI' in loaded_subjects: question_banks['DI'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 2)
            # Check for failure after trying to create all needed banks
            if any(subj in loaded_subjects and question_banks.get(subj) is None for subj in loaded_subjects):
                 st.error("創建模擬題庫失敗。")
                 simulation_success = False
                 status.update(label="模擬題庫創建失敗", state="error", expanded=True)
            else:
                 st.write("模擬題庫創建完成。")
        except Exception as e:
            st.error(f"創建模擬題庫時出錯: {e}")
            simulation_success = False
            status.update(label=f"模擬題庫創建出錯: {e}", state="error", expanded=True)

        if simulation_success:
            subject_params = {
                'Q': {'initial_theta': initial_theta_q, 'total_questions': TOTAL_QUESTIONS_Q},
                'V': {'initial_theta': initial_theta_v, 'total_questions': TOTAL_QUESTIONS_V},
                'DI': {'initial_theta': initial_theta_di, 'total_questions': TOTAL_QUESTIONS_DI}
            }

            for subject in loaded_subjects:
                st.write(f"執行 {subject} 科目模擬...")
                # Get parameters for simulation
                params = subject_params[subject]
                initial_theta = params['initial_theta']
                total_sim_questions = params['total_questions'] # Number of questions IN SIMULATION
                bank = question_banks[subject]
                
                # Get WRONG indices from the *original* user data for this subject
                user_df_subj = df_combined_input[df_combined_input['Subject'] == subject]
                wrong_indices = [] # Keep variable name for now, but it holds positions
                # Check for the final column name 'is_correct'
                if 'is_correct' in user_df_subj.columns:
                    # Sort by position before getting indices
                    user_df_subj_sorted = user_df_subj.sort_values(by='question_position')
                    # Filter using the final column name 'is_correct'
                    # --- CORRECTED LOGIC HERE ---
                    # Directly get the 'question_position' values of incorrect answers
                    wrong_positions = user_df_subj_sorted[user_df_subj_sorted['is_correct'] == False]['question_position'].tolist()
                    wrong_indices = wrong_positions # Assign to the variable expected by the simulation function
                    # --- END CORRECTION ---
                    st.write(f"  {subject}: 從用戶數據提取 {len(wrong_indices)} 個錯誤題目位置: {wrong_indices}")
                else:
                    # This warning should now only appear if 'Performance' was truly missing initially
                    st.warning(f"  {subject}: 用戶數據缺少 'is_correct' 欄位 (源自 'Performance')，假設全部答對進行模擬。")
                    wrong_indices = []

                # Run the simulation
                try:
                    history_df = irt.simulate_cat_exam(
                        question_bank=bank,
                        wrong_question_indices=wrong_indices, # Pass the list of actual wrong positions
                        initial_theta=initial_theta,
                        total_questions=total_sim_questions # Use the simulation total questions
                    )
                    if history_df is not None and not history_df.empty:
                        all_simulation_histories[subject] = history_df
                        # Store final theta locally first
                        final_theta_subj = history_df['theta_est_after_answer'].iloc[-1]
                        final_thetas[subject] = final_theta_subj
                        st.write(f"  {subject}: 模擬完成。最後 Theta 估計: {final_theta_subj:.3f}")
                    elif history_df is not None and history_df.empty:
                        st.warning(f"  {subject}: 模擬執行了，但未產生歷史記錄。")
                        simulation_success = False # Treat empty history as failure for next steps
                    else:
                         st.error(f"  {subject}: 模擬執行失敗，返回 None。")
                         simulation_success = False
                         break # Stop simulation for other subjects if one fails
                except Exception as e:
                    st.error(f"  {subject}: 執行模擬時發生錯誤: {e}")
                    simulation_success = False
                    break # Stop simulation

        if simulation_success and all_simulation_histories:
            status.update(label="IRT 模擬完成！", state="complete", expanded=False)
            st.session_state.final_thetas = final_thetas # Store final thetas in session state
        elif simulation_success: # Banks created, but simulation failed for some reason
             status.update(label="IRT 模擬部分失敗或未產生結果", state="error", expanded=True)
             simulation_success = False # Ensure it's false
        # Else: Bank creation failed, status already set to error

    # --- Prepare Data for Diagnosis ---
    # st.header("2. 準備診斷數據 (結合用戶數據與模擬難度)") # Combined into header 2
    if simulation_success:
        # with st.spinner("準備診斷數據中..."): # Replace with st.status
        with st.status("準備診斷數據...", expanded=True) as status_prep:
            df_final_for_diagnosis_list = []
            processing_error = False
            for subject in loaded_subjects:
                st.write(f"處理 {subject} 科目...")
                user_df_subj = df_combined_input[df_combined_input['Subject'] == subject].copy()
                sim_history_df = all_simulation_histories.get(subject)
                final_theta = final_thetas.get(subject)

                if sim_history_df is None or sim_history_df.empty:
                    st.error(f"找不到 {subject} 科目的有效模擬結果，無法繼續。")
                    processing_error = True; status_prep.update(state="error"); break

                # Extract simulated b-values
                sim_b_values = sim_history_df['b'].tolist()
                
                # Sort user data by position
                user_df_subj_sorted = user_df_subj.sort_values(by='question_position')
                num_user_questions = len(user_df_subj_sorted)
                num_sim_b = len(sim_b_values)

                # Check for length mismatch between user data and simulation results
                if num_user_questions != num_sim_b:
                     st.warning(f"{subject}: 用戶數據題目數 ({num_user_questions}) 與模擬結果數 ({num_sim_b}) 不符。" 
                               f"將僅使用前 {min(num_user_questions, num_sim_b)} 個數據進行難度賦值。診斷可能不完整。")
                     # Truncate to the minimum length
                     min_len = min(num_user_questions, num_sim_b)
                     user_df_subj_sorted = user_df_subj_sorted.iloc[:min_len]
                     sim_b_values = sim_b_values[:min_len]
                
                if not sim_b_values: # Check if list became empty after truncation
                     st.error(f"{subject}: 無可用的模擬難度值，無法繼續處理。")
                     processing_error = True; status_prep.update(state="error"); break

                # Assign simulated b-values as 'question_difficulty'
                user_df_subj_sorted['question_difficulty'] = sim_b_values
                st.write(f"  {subject}: 已將模擬難度賦值給 {len(user_df_subj_sorted)} 道題目。")

                # Add final theta as context
                if final_theta is not None:
                     user_df_subj_sorted['estimated_ability'] = final_theta

                df_final_for_diagnosis_list.append(user_df_subj_sorted)
            
            if not processing_error and df_final_for_diagnosis_list:
                df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
                
                # st.subheader("診斷用數據預覽 (含模擬難度)") # Optional: Move preview here?
                # st.dataframe(df_final_for_diagnosis.head())
                st.write("所有科目數據準備完成。")
                status_prep.update(label="診斷數據準備完成！", state="complete", expanded=False)
            elif not processing_error: # List is empty but no specific error flagged?
                 st.warning("未能準備任何診斷數據。")
                 status_prep.update(label="未能準備診斷數據", state="warning", expanded=True)
            # Else: error occurred, status already set
    
    # --- Diagnosis Section --- (Now uses df_final_for_diagnosis)
    # st.header("3. 執行診斷分析") # Combined into header 2
    if df_final_for_diagnosis is not None: # Check if data prep was successful
        report_string = None # Initialize report string for this run
        # with st.spinner("執行診斷分析中..."): # Replace with st.status
        with st.status("執行診斷分析...", expanded=True) as status_diag:
            try:
                # Ensure all required columns for the *markdown logic* are present
                # Markdown needs: 'Correct', 'question_difficulty', 'question_time', 'question_type', 
                # 'question_fundamental_skill', 'question_position'
                required_cols = ['is_correct', 'question_difficulty', 'question_time', 'question_type', 'question_position']
                # Check optional cols individually and add placeholders if missing
                if 'question_fundamental_skill' not in df_final_for_diagnosis.columns:
                     st.warning("數據缺少 'question_fundamental_skill'，部分診斷可能受影響。正在添加占位符。")
                     df_final_for_diagnosis['question_fundamental_skill'] = 'Unknown Skill' # Add placeholder
                if 'content_domain' not in df_final_for_diagnosis.columns:
                     st.warning("數據缺少 'content_domain'，部分診斷可能受影響。正在添加占位符。")
                     df_final_for_diagnosis['content_domain'] = 'Unknown Domain' # Add placeholder

                missing_cols = [col for col in required_cols if col not in df_final_for_diagnosis.columns]
                
                if not missing_cols:
                    st.write("正在調用診斷模塊...")
                    # Pass the combined data to the diagnosis module
                    # Consider passing total_test_time if collected
                    report_string = run_diagnosis(df_final_for_diagnosis) # Changed variable name
                    st.session_state.report_string = report_string # Store in session state

                    # Check if the report string is not None and not empty
                    if report_string:
                        st.write("診斷分析完成。")
                        status_diag.update(label="診斷分析完成！", state="complete", expanded=False)
                    else:
                        st.warning("診斷分析未返回結果或結果為空。請檢查 `diagnosis_module.py`。") # Updated warning
                        status_diag.update(label="診斷分析未返回結果", state="warning", expanded=True)
                else:
                    st.error(f"準備用於診斷的資料缺少必需欄位: {missing_cols}。無法執行診斷。")
                    status_diag.update(label=f"診斷所需欄位缺失: {missing_cols}", state="error", expanded=True)
                    st.session_state.report_string = None # Ensure reset on error
            except Exception as e:
                st.error(f"執行診斷時發生錯誤：{e}")
                status_diag.update(label=f"診斷執行出錯: {e}", state="error", expanded=True)
                st.session_state.report_string = None # Ensure reset on error

            # --- Generate OpenAI Summary --- (Still within button click block)
            # Check if report_string exists and is not empty
            if st.session_state.report_string: # Check session state
                if openai_api_key:
                    # with st.spinner("正在生成文字摘要..."): # Replace with st.status
                    with st.status("生成 AI 文字摘要...", expanded=False) as status_ai:
                        try:
                            client = openai.OpenAI(api_key=openai_api_key)
                            # Use the report string directly in the prompt
                            prompt = f"""請根據以下 GMAT 診斷報告（基於用戶實際表現數據，但使用了模擬難度估計），產生一段簡潔的總結報告（約 150-200 字），說明主要的強項、弱項或值得注意的模式。請使用繁體中文回答。

診斷報告：
{st.session_state.report_string}

總結報告："""
                            st.write("正在調用 OpenAI API...")
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "你是一個擅長分析 GMAT 診斷報告並產生總結的 AI 助理。"},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            summary = response.choices[0].message.content
                            st.session_state.ai_summary = summary # Store in session state
                            st.write("AI 摘要生成成功。")
                            status_ai.update(label="AI 文字摘要生成成功！", state="complete", expanded=False)
                        except Exception as e:
                            st.error(f"生成 AI 摘要時發生錯誤：{e}")
                            st.session_state.ai_summary = None # Reset on error
                            status_ai.update(label=f"AI 摘要生成失敗: {e}", state="error", expanded=True)
                else:
                     # Info message moved to output section
                     pass
            # --- End OpenAI Summary ---
        # elif not df_final_for_diagnosis_list: # Handled inside status_prep
        #      st.warning("未能成功準備任何用於診斷的數據。")
    # elif not simulation_success: # Condition checked before data prep
    #     st.error("IRT 模擬過程中斷或失敗，無法進行後續分析。")

# --- Display Results Section (Uses Session State) ---
st.divider()
if st.session_state.analysis_run: # Only show results area if analysis was attempted
    st.header("診斷結果")

    # Display Final Thetas if available
    if st.session_state.final_thetas:
         theta_items = [f"{subj}: {theta:.3f}" for subj, theta in st.session_state.final_thetas.items()]
         st.success(f"最終能力估計 (Theta): {', '.join(theta_items)}")
    # else:
    #      st.warning("無法獲取最終能力估計。") # Maybe don't show warning if analysis failed earlier

    if st.session_state.report_string:
        report_tab, summary_tab = st.tabs(["詳細診斷報告", "AI 文字摘要"])
        with report_tab:
            st.markdown(st.session_state.report_string)
        with summary_tab:
            if st.session_state.ai_summary:
                st.markdown(st.session_state.ai_summary)
            elif openai_api_key:
                 st.info("AI 摘要尚未生成或生成失敗。請檢查上方狀態。")
            else:
                st.info("請在側邊欄輸入 OpenAI API Key 並重新運行分析以生成 AI 文字摘要。")
    else: # Analysis ran but report is None/empty
        st.error("分析過程未成功生成診斷報告，請檢查上方的狀態信息和錯誤提示。")

# else: # Analysis was not run (button not clicked or no data)
#     st.info("點擊 '開始分析' 按鈕以執行模擬與診斷。") # Message now shown near button

# Final info message handled within sections
