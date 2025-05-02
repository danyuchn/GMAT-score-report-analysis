import streamlit as st
import pandas as pd
from io import StringIO # Use io.StringIO directly
import irt_module as irt # Import the updated module
from diagnosis_module import run_diagnosis # Import the diagnosis function
import os # For environment variables
import openai # Import OpenAI library

# --- Get OpenAI API Key ---
st.sidebar.subheader("OpenAI 設定 (選用)")
api_key_input = st.sidebar.text_input(
    "輸入您的 OpenAI API Key：", 
    type="password", 
    help="或者設定 OPENAI_API_KEY 環境變數。用於生成文字摘要。"
)

# Use input key if provided, otherwise check environment variable
openai_api_key = api_key_input if api_key_input else os.getenv("OPENAI_API_KEY")
# --- End OpenAI API Key ---

# Set the title of the app
st.title('GMAT 成績診斷平台')

# --- Data Input Section ---
st.header("上傳或貼上各科成績單")

# Initialize DataFrames
df_q = None
df_v = None
df_di = None
data_sources = {}

# Input fields for initial theta estimates
st.sidebar.subheader("IRT 模擬設定")
initial_theta_q = st.sidebar.number_input("Q 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_v = st.sidebar.number_input("V 科目初始 Theta 估計", value=0.0, step=0.1)
initial_theta_di = st.sidebar.number_input("DI 科目初始 Theta 估計", value=0.0, step=0.1)

# Simulation Parameters (can be adjusted)
BANK_SIZE = 1000 # Number of items in the simulated bank for each subject
TOTAL_QUESTIONS_Q = 21
TOTAL_QUESTIONS_V = 23
TOTAL_QUESTIONS_DI = 20
RANDOM_SEED = 1000 # For reproducible question banks

# Quantitative (Q) Input
with st.expander("Quantitative (Q) 資料輸入", expanded=False):
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
            # --- Standardize Columns (Keep original metadata, map Correct) ---
            # Use a consistent base mapping, Q_b/V_b/DI_b are no longer primary source of difficulty
            rename_map_q = {
                '\ufeffQuestion': 'Question ID', # Handle BOM
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time', # Keep for potential future use
                'Question Type': 'question_type', # Keep for potential future use
                'Content Domain': 'content_domain', # Keep for potential future use
                'Fundamental Skills': 'question_fundamental_skill' # Keep
                # Removed mapping for Q_b
            }
            # Apply only columns that exist
            cols_to_rename = {k: v for k, v in rename_map_q.items() if k in temp_df_q.columns}
            temp_df_q.rename(columns=cols_to_rename, inplace=True)
            
            if 'Correct' in temp_df_q.columns:
                 # Convert to boolean consistently
                 temp_df_q['Correct'] = temp_df_q['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            else:
                st.error("Q 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                temp_df_q = None

            if temp_df_q is not None:
                data_sources['Q'] = 'File Upload' if uploaded_file_q else 'Pasted Data'
                st.success(f"Q 科目資料讀取成功 ({data_sources['Q']})！")
                # Add section identifier
                temp_df_q['Subject'] = 'Q'

        except Exception as e:
            st.error(f"處理 Q 科目資料時發生錯誤：{e}")
            temp_df_q = None
            
    if temp_df_q is not None:
        df_q = temp_df_q
        st.subheader("Q 科目輸入資料預覽 (用於提取錯誤題目)")
        st.dataframe(df_q.head())

# Verbal (V) Input
with st.expander("Verbal (V) 資料輸入", expanded=False):
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
            rename_map_v = {
                '\ufeffQuestion': 'Question ID',
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Fundamental Skills': 'question_fundamental_skill'
                # Removed mapping for V_b
            }
            cols_to_rename = {k: v for k, v in rename_map_v.items() if k in temp_df_v.columns}
            temp_df_v.rename(columns=cols_to_rename, inplace=True)
            
            if 'Correct' in temp_df_v.columns:
                 temp_df_v['Correct'] = temp_df_v['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            else:
                 st.error("V 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                 temp_df_v = None

            if temp_df_v is not None:
                data_sources['V'] = 'File Upload' if uploaded_file_v else 'Pasted Data'
                st.success(f"V 科目資料讀取成功 ({data_sources['V']})！")
                # Add section identifier
                temp_df_v['Subject'] = 'V'

        except Exception as e:
            st.error(f"處理 V 科目資料時發生錯誤：{e}")
            temp_df_v = None
            
    if temp_df_v is not None:
        df_v = temp_df_v
        st.subheader("V 科目輸入資料預覽 (用於提取錯誤題目)")
        st.dataframe(df_v.head())

# Data Insights (DI) Input
with st.expander("Data Insights (DI) 資料輸入", expanded=False):
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
            rename_map_di = {
                '\ufeffQuestion': 'Question ID',
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Content Domain': 'content_domain'
                 # Removed mapping for DI_b
            }
            cols_to_rename = {k: v for k, v in rename_map_di.items() if k in temp_df_di.columns}
            temp_df_di.rename(columns=cols_to_rename, inplace=True)
            
            if 'Correct' in temp_df_di.columns:
                 temp_df_di['Correct'] = temp_df_di['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            else:
                 st.error("DI 資料缺少 'Performance' (Correct) 欄位，無法確定錯誤題目。")
                 temp_df_di = None

            if temp_df_di is not None:
                data_sources['DI'] = 'File Upload' if uploaded_file_di else 'Pasted Data'
                st.success(f"DI 科目資料讀取成功 ({data_sources['DI']})！")
                # Add section identifier
                temp_df_di['Subject'] = 'DI'

        except Exception as e:
            st.error(f"處理 DI 科目資料時發生錯誤：{e}")
            temp_df_di = None
            
    if temp_df_di is not None:
        df_di = temp_df_di
        st.subheader("DI 科目輸入資料預覽 (用於提取錯誤題目)")
        st.dataframe(df_di.head())

# --- Simulation and Processing Section --- 

# Combine *input* dataframes only to check which subjects were loaded
input_dfs = {'Q': df_q, 'V': df_v, 'DI': df_di}
loaded_subjects = {subj for subj, df in input_dfs.items() if df is not None}

all_simulation_histories = []

if not loaded_subjects:
    st.info("請展開上方區塊，為至少一個科目上傳檔案或貼上資料以開始模擬與分析。")
else:
    st.header("1. 執行 IRT 模擬")
    simulation_success = True
    with st.spinner("正在執行 IRT 模擬..."):
        # Initialize question banks first (using the same seed for consistency across runs if desired)
        st.write("初始化模擬題庫...")
        question_banks = {}
        try:
            if 'Q' in loaded_subjects: question_banks['Q'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED)
            if 'V' in loaded_subjects: question_banks['V'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 1) # Slightly different seed
            if 'DI' in loaded_subjects: question_banks['DI'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 2)
            if any(bank is None for bank in question_banks.values()):
                 st.error("創建模擬題庫失敗。")
                 simulation_success = False
            else:
                 st.write("模擬題庫創建完成。")
        except Exception as e:
            st.error(f"創建模擬題庫時出錯: {e}")
            simulation_success = False

        # Run simulation for each loaded subject
        if simulation_success:
            subject_params = {
                'Q': {'df': df_q, 'initial_theta': initial_theta_q, 'total_questions': TOTAL_QUESTIONS_Q},
                'V': {'df': df_v, 'initial_theta': initial_theta_v, 'total_questions': TOTAL_QUESTIONS_V},
                'DI': {'df': df_di, 'initial_theta': initial_theta_di, 'total_questions': TOTAL_QUESTIONS_DI}
            }

            for subject, params in subject_params.items():
                if subject in loaded_subjects:
                    st.write(f"執行 {subject} 科目模擬...")
                    input_df = params['df']
                    initial_theta = params['initial_theta']
                    total_questions = params['total_questions']
                    bank = question_banks[subject]

                    # Extract 1-based indices of WRONG answers from the input dataframe
                    # Assuming the input dataframe rows are in the order questions were presented
                    wrong_indices = []
                    if 'Correct' in input_df.columns:
                        wrong_indices = input_df[input_df['Correct'] == False].index + 1
                        wrong_indices = wrong_indices.tolist()
                        st.write(f"  {subject}: 偵測到 {len(wrong_indices)} 個錯誤題目，位置: {wrong_indices[:10]}...") # Show first 10
                    else:
                        st.warning(f"  {subject}: 輸入資料缺少 'Correct' 欄位，假設全部答對進行模擬。")
                        wrong_indices = []

                    # Run the simulation
                    try:
                        history_df = irt.simulate_cat_exam(
                            question_bank=bank,
                            wrong_question_indices=wrong_indices,
                            initial_theta=initial_theta,
                            total_questions=total_questions
                        )
                        if history_df is not None and not history_df.empty:
                            history_df['Subject'] = subject # Add subject identifier to history
                            all_simulation_histories.append(history_df)
                            st.write(f"  {subject}: 模擬完成。最後 Theta 估計: {history_df['theta_est_after_answer'].iloc[-1]:.3f}")
                        elif history_df is not None and history_df.empty:
                            st.warning(f"  {subject}: 模擬執行了，但未產生歷史記錄 (可能是 total_questions=0)。")
                        else:
                             st.error(f"  {subject}: 模擬執行失敗，返回 None。")
                             simulation_success = False
                             break # Stop simulating other subjects if one fails
                    except Exception as e:
                        st.error(f"  {subject}: 執行模擬時發生錯誤: {e}")
                        simulation_success = False
                        break

    if simulation_success and all_simulation_histories:
        st.success("所有科目的 IRT 模擬完成！")
        # Combine simulation results
        df_simulated_combined = pd.concat(all_simulation_histories, ignore_index=True)
        st.header("模擬結果預覽")
        st.dataframe(df_simulated_combined.head())

        # --- Prepare Data for Diagnosis ---
        # Use the output of the simulation
        df_for_diagnosis = df_simulated_combined.copy()

        # Rename 'b' to 'difficulty' as expected by diagnosis module
        if 'b' in df_for_diagnosis.columns:
            df_for_diagnosis.rename(columns={'b': 'difficulty'}, inplace=True)
        else:
            st.error("模擬結果缺少 'b' (difficulty) 欄位！")
            df_for_diagnosis = None # Cannot proceed

        # Ensure required columns for run_diagnosis exist
        # Required: ['Question ID', 'Correct', 'difficulty', 'question_time', 'question_type']
        if df_for_diagnosis is not None:
            # Rename simulated 'question_id' to 'Question ID'
            if 'question_id' in df_for_diagnosis.columns:
                 df_for_diagnosis.rename(columns={'question_id': 'Question ID'}, inplace=True)
            else:
                 st.error("模擬結果缺少 'question_id' 欄位！")
                 df_for_diagnosis = None

            # Rename 'answered_correctly' to 'Correct'
            if 'answered_correctly' in df_for_diagnosis.columns:
                 df_for_diagnosis.rename(columns={'answered_correctly': 'Correct'}, inplace=True)
            elif 'Correct' not in df_for_diagnosis.columns: # Check if already named Correct
                 st.error("模擬結果缺少 'answered_correctly' 或 'Correct' 欄位！")
                 df_for_diagnosis = None

            # Add dummy columns for 'question_time' and 'question_type' if missing
            if 'question_time' not in df_for_diagnosis.columns:
                df_for_diagnosis['question_time'] = 0.0 # Placeholder value
            
            # Add 'question_type' based on 'Subject' if missing
            if 'question_type' not in df_for_diagnosis.columns:
                if 'Subject' in df_for_diagnosis.columns:
                    # Define mapping from Subject to a generic type diagnosis module might handle
                    subject_to_type_map = {
                        'Q': 'Quant', # Or 'Quantitative' if diagnosis module uses that
                        'V': 'Verbal',
                        'DI': 'DI'    # Or 'Data Insights'
                    }
                    df_for_diagnosis['question_type'] = df_for_diagnosis['Subject'].map(subject_to_type_map).fillna('Unknown')
                    st.write("新增了基於 Subject 的 question_type 欄位 ('Quant', 'Verbal', 'DI')")
                else:
                     st.warning("模擬結果缺少 'Subject' 欄位，無法自動生成 'question_type'。將使用 'Unknown'。")
                     df_for_diagnosis['question_type'] = 'Unknown' # Fallback placeholder

        # --- Diagnosis Section --- (Now uses df_for_diagnosis)
        if df_for_diagnosis is not None:
            st.header("2. 執行診斷分析 (基於模擬結果)")
            result_df = None
            try:
                with st.spinner("執行診斷分析中..."):
                    required_diag_cols = ['Question ID', 'Correct', 'difficulty', 'question_time', 'question_type']
                    if all(col in df_for_diagnosis.columns for col in required_diag_cols):
                        result_df = run_diagnosis(df_for_diagnosis)
                        if result_df is not None and not result_df.empty:
                            st.success("診斷分析完成！")
                            st.subheader("診斷結果")
                            st.dataframe(result_df)

                            # Download Button
                            try:
                                csv_data = result_df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="下載診斷結果 CSV",
                                    data=csv_data,
                                    file_name='gmat_sim_diagnosis_result.csv',
                                    mime='text/csv',
                                    key='download-sim-csv'
                                )
                            except Exception as e:
                                st.error(f"準備下載檔時發生錯誤：{e}")
                        else:
                            st.warning("診斷分析未返回結果。請檢查 `diagnosis_module.py`。")
                    else:
                        st.error(f"準備用於診斷的資料缺少必需欄位 (需要: {required_diag_cols}，實際有: {df_for_diagnosis.columns.tolist()})，無法執行診斷。")
                        result_df = None
            except Exception as e:
                st.error(f"執行診斷時發生錯誤：{e}")
                result_df = None

            # --- Generate OpenAI Summary --- (Uses diagnosis result_df)
            if result_df is not None and not result_df.empty:
                if openai_api_key:
                    st.header("3. AI 文字摘要 (基於模擬診斷)")
                    try:
                        client = openai.OpenAI(api_key=openai_api_key)
                        prompt_data = result_df.to_string()
                        prompt = f"""請根據以下 GMAT 模擬診斷結果摘要，產生一段簡潔的總結報告（約 100-150 字），說明主要的強項、弱項或值得注意的模式。請使用繁體中文回答。\n\n診斷摘要：\n{prompt_data}\n\n總結報告："""
                        with st.spinner("正在生成文字摘要..."):
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "你是一個擅長分析 GMAT 模擬診斷報告並產生總結的 AI 助理。"},
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            summary = response.choices[0].message.content
                        st.markdown(summary)
                        st.success("文字摘要生成成功！")
                    except Exception as e:
                        st.error(f"生成 AI 摘要時發生錯誤：{e}")
                else:
                    st.info("在側邊欄輸入您的 OpenAI API Key 以生成 AI 文字摘要。")
            # --- End OpenAI Summary ---
        else:
             st.warning("準備用於診斷的資料失敗，無法執行診斷分析。")
    elif not simulation_success:
        st.error("IRT 模擬過程中斷或失敗，無法進行後續分析。")
    # If no simulation histories were generated (e.g., initial error)
    # elif not all_simulation_histories:
    #    st.warning("未能生成任何模擬結果，無法進行分析。")

# Final info message is handled within the sections now.
