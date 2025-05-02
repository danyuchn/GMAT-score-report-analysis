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

# Store the original combined input data for later use with simulated difficulty
df_combined_input_list = []
if df_q is not None: df_combined_input_list.append(df_q)
if df_v is not None: df_combined_input_list.append(df_v)
if df_di is not None: df_combined_input_list.append(df_di)

df_combined_input = None
if df_combined_input_list:
     try:
         df_combined_input = pd.concat(df_combined_input_list, ignore_index=True)
         # Ensure question_position exists for sorting, add if missing based on index
         if 'question_position' not in df_combined_input.columns:
             st.warning("輸入資料缺少 'question_position' 欄位，將使用原始順序作為位置。")
             # Assuming index corresponds to position if missing
             df_combined_input['question_position'] = df_combined_input.index + 1 
         else:
              # Convert position to numeric and handle errors
              df_combined_input['question_position'] = pd.to_numeric(df_combined_input['question_position'], errors='coerce')
              if df_combined_input['question_position'].isnull().any():
                    st.error("'question_position' 欄位包含非數值，無法排序。請檢查數據。")
                    df_combined_input = None # Stop processing if position is invalid
     except Exception as e:
         st.error(f"合併或處理輸入資料時發生錯誤: {e}")
         df_combined_input = None

all_simulation_histories = {} # Store histories per subject
final_thetas = {}           # Store final theta per subject

if df_combined_input is None and loaded_subjects: # Check if combining failed
     st.error("無法處理輸入資料，請檢查數據格式與 'question_position' 欄位。")
elif not loaded_subjects:
    st.info("請展開上方區塊，為至少一個科目上傳檔案或貼上資料以開始模擬與分析。")
else:
    st.header("1. 執行 IRT 模擬 (以獲取難度序列與 Theta)")
    simulation_success = True
    with st.spinner("正在執行 IRT 模擬..."):
        st.write("初始化模擬題庫...")
        question_banks = {}
        try:
            if 'Q' in loaded_subjects: question_banks['Q'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED)
            if 'V' in loaded_subjects: question_banks['V'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 1)
            if 'DI' in loaded_subjects: question_banks['DI'] = irt.initialize_question_bank(BANK_SIZE, seed=RANDOM_SEED + 2)
            if any(bank is None for bank in question_banks.values()):
                 st.error("創建模擬題庫失敗。")
                 simulation_success = False
            else:
                 st.write("模擬題庫創建完成。")
        except Exception as e:
            st.error(f"創建模擬題庫時出錯: {e}")
            simulation_success = False

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
                wrong_indices = []
                if 'Correct' in user_df_subj.columns:
                    # Sort by position before getting indices
                    user_df_subj_sorted = user_df_subj.sort_values(by='question_position')
                    wrong_indices = user_df_subj_sorted[user_df_subj_sorted['Correct'] == False].index + 1
                    wrong_indices = wrong_indices.tolist()
                    st.write(f"  {subject}: 從用戶數據提取 {len(wrong_indices)} 個錯誤題目位置: {wrong_indices[:10]}...")
                else:
                    st.warning(f"  {subject}: 用戶數據缺少 'Correct'，假設全部答對進行模擬。")
                    wrong_indices = []

                # Run the simulation
                try:
                    history_df = irt.simulate_cat_exam(
                        question_bank=bank,
                        wrong_question_indices=wrong_indices,
                        initial_theta=initial_theta,
                        total_questions=total_sim_questions # Use the simulation total questions
                    )
                    if history_df is not None and not history_df.empty:
                        all_simulation_histories[subject] = history_df
                        final_thetas[subject] = history_df['theta_est_after_answer'].iloc[-1]
                        st.write(f"  {subject}: 模擬完成。產生 {len(history_df)} 個模擬結果。最後 Theta 估計: {final_thetas[subject]:.3f}")
                    elif history_df is not None and history_df.empty:
                        st.warning(f"  {subject}: 模擬執行了，但未產生歷史記錄。")
                        simulation_success = False # Treat empty history as failure for next steps
                    else:
                         st.error(f"  {subject}: 模擬執行失敗，返回 None。")
                         simulation_success = False
                         break
                except Exception as e:
                    st.error(f"  {subject}: 執行模擬時發生錯誤: {e}")
                    simulation_success = False
                    break

    if simulation_success and all_simulation_histories:
        st.success("所有科目的 IRT 模擬完成！")
        
        # --- Combine Input Data with Simulated Difficulty --- 
        st.header("2. 準備診斷數據 (結合用戶數據與模擬難度)")
        df_final_for_diagnosis_list = []
        processing_error = False
        for subject in loaded_subjects:
            st.write(f"處理 {subject} 科目...")
            user_df_subj = df_combined_input[df_combined_input['Subject'] == subject].copy()
            sim_history_df = all_simulation_histories.get(subject)
            final_theta = final_thetas.get(subject)

            if sim_history_df is None or sim_history_df.empty:
                st.error(f"找不到 {subject} 科目的有效模擬結果，無法繼續。")
                processing_error = True
                break

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
                 processing_error = True
                 break

            # Assign simulated b-values as 'question_difficulty'
            user_df_subj_sorted['question_difficulty'] = sim_b_values
            st.write(f"  {subject}: 已將模擬難度賦值給 {len(user_df_subj_sorted)} 道題目。")

            # Add final theta as context
            if final_theta is not None:
                 user_df_subj_sorted['estimated_ability'] = final_theta

            df_final_for_diagnosis_list.append(user_df_subj_sorted)
        
        if not processing_error and df_final_for_diagnosis_list:
            df_final_for_diagnosis = pd.concat(df_final_for_diagnosis_list, ignore_index=True)
            
            st.subheader("診斷用數據預覽 (含模擬難度)")
            st.dataframe(df_final_for_diagnosis.head())
            
            # --- Diagnosis Section --- (Now uses df_final_for_diagnosis)
            st.header("3. 執行診斷分析")
            result_df = None
            # Add input for total_test_time if needed by Chapter 1 logic
            # total_test_time = st.number_input("請輸入總測驗時間（分鐘）:", value=135.0, min_value=10.0, step=0.5) 
            try:
                with st.spinner("執行診斷分析中..."):
                    # Diagnosis module now needs the combined actual data with simulated difficulty
                    # It will need columns like: 'Question ID', 'Correct', 'question_difficulty', 'question_time', 
                    # 'question_type', 'question_fundamental_skill', 'question_position', 'estimated_ability' (optional)
                    
                    # Ensure all required columns for the *markdown logic* are present
                    # Markdown needs: 'Correct', 'question_difficulty', 'question_time', 'question_type', 
                    # 'question_fundamental_skill', 'question_position'
                    required_markdown_cols = ['Correct', 'question_difficulty', 'question_time', 'question_type', 'question_fundamental_skill', 'question_position']
                    missing_cols = [col for col in required_markdown_cols if col not in df_final_for_diagnosis.columns]
                    
                    if not missing_cols:
                        # Pass the combined data to the diagnosis module
                        # Consider passing total_test_time if collected
                        result_df = run_diagnosis(df_final_for_diagnosis)
                        
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
                                    file_name='gmat_diagnosis_result_sim_b.csv', # Indicate sim b used
                                    mime='text/csv',
                                    key='download-diag-sim-b'
                                )
                            except Exception as e:
                                st.error(f"準備下載檔時發生錯誤：{e}")
                        else:
                            st.warning("診斷分析未返回結果。請檢查 `diagnosis_module.py`。")
                    else:
                        st.error(f"準備用於診斷的資料缺少 Markdown 邏輯所需欄位: {missing_cols}。無法執行診斷。")
                        result_df = None
            except Exception as e:
                st.error(f"執行診斷時發生錯誤：{e}")
                result_df = None

            # --- Generate OpenAI Summary --- (Uses diagnosis result_df)
            if result_df is not None and not result_df.empty:
                if openai_api_key:
                    st.header("4. AI 文字摘要 (基於詳細診斷)")
                    try:
                        client = openai.OpenAI(api_key=openai_api_key)
                        prompt_data = result_df.to_string()
                        prompt = f"""請根據以下 GMAT 診斷結果摘要（基於用戶實際表現數據，但使用了模擬難度估計），產生一段簡潔的總結報告（約 150-200 字），說明主要的強項、弱項或值得注意的模式。請使用繁體中文回答。\n\n診斷摘要：\n{prompt_data}\n\n總結報告："""
                        with st.spinner("正在生成文字摘要..."):
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "你是一個擅長分析 GMAT 診斷報告並產生總結的 AI 助理。"},
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
        elif not df_final_for_diagnosis_list:
             st.warning("未能成功準備任何用於診斷的數據。")
    elif not simulation_success:
        st.error("IRT 模擬過程中斷或失敗，無法進行後續分析。")

# Final info message handled within sections
