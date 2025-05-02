import streamlit as st
import pandas as pd
from io import StringIO # Use io.StringIO directly
from irt_module import estimate_difficulty # Import the function
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
            # --- Rename and Transform Q Columns (Revised to handle BOM) ---
            rename_map_q = {
                '\ufeffQuestion': 'Question ID', # Handle BOM in first column name
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Content Domain': 'content_domain',
                'Fundamental Skills': 'question_fundamental_skill',
                'Q_b': 'question_difficulty'
            }
            temp_df_q.rename(columns=rename_map_q, inplace=True)
            
            # --- Debug: Columns *after* rename ---
            # st.write("Q 科目重命名後欄位:", temp_df_q.columns.tolist()) # Remove this line
            # --- End Debug ---
            
            if 'Correct' in temp_df_q.columns:
                 temp_df_q['Correct'] = temp_df_q['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            if 'question_type' in temp_df_q.columns:
                 temp_df_q['question_type'] = temp_df_q['question_type'].str.capitalize() # REAL -> Real, PURE -> Pure
            # --- End Rename/Transform ---
            data_sources['Q'] = 'File Upload' if uploaded_file_q else 'Pasted Data'
            st.success(f"Q 科目資料讀取成功 ({data_sources['Q']})！")
        except Exception as e:
            st.error(f"處理 Q 科目資料時發生錯誤：{e}")
            temp_df_q = None # Ensure reset on error
            
    if temp_df_q is not None:
        df_q = temp_df_q
        st.subheader("Q 科目資料預覽")
        st.dataframe(df_q)

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
            # --- Rename and Transform V Columns (Revised to handle BOM) ---
            rename_map_v = {
                '\ufeffQuestion': 'Question ID', # Handle BOM
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Fundamental Skills': 'question_fundamental_skill',
                'V_b': 'question_difficulty'
            }
            temp_df_v.rename(columns=rename_map_v, inplace=True)
            
            # --- Debug: Columns *after* rename ---
            # st.write("V 科目重命名後欄位:", temp_df_v.columns.tolist()) # Remove this line
            # --- End Debug ---
            
            if 'Correct' in temp_df_v.columns:
                temp_df_v['Correct'] = temp_df_v['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            if 'question_type' in temp_df_v.columns:
                 type_map_v = {'Critical Reasoning': 'CR', 'Reading Comprehension': 'RC'}
                 temp_df_v['question_type'] = temp_df_v['question_type'].map(type_map_v).fillna(temp_df_v['question_type'])
            # --- End Rename/Transform ---
            data_sources['V'] = 'File Upload' if uploaded_file_v else 'Pasted Data'
            st.success(f"V 科目資料讀取成功 ({data_sources['V']})！")
        except Exception as e:
            st.error(f"處理 V 科目資料時發生錯誤：{e}")
            temp_df_v = None
            
    if temp_df_v is not None:
        df_v = temp_df_v
        st.subheader("V 科目資料預覽")
        st.dataframe(df_v)

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
            # --- Rename and Transform DI Columns (Revised to handle BOM) ---
            rename_map_di = {
                '\ufeffQuestion': 'Question ID', # Handle BOM
                'Performance': 'Correct',
                'Response Time (Minutes)': 'question_time',
                'Question Type': 'question_type',
                'Content Domain': 'content_domain',
                'DI_b': 'question_difficulty'
            }
            temp_df_di.rename(columns=rename_map_di, inplace=True)
            
            # --- Debug: Columns *after* rename ---
            # st.write("DI 科目重命名後欄位:", temp_df_di.columns.tolist()) # Remove this line
            # --- End Debug ---
            
            if 'Correct' in temp_df_di.columns:
                 temp_df_di['Correct'] = temp_df_di['Correct'].apply(lambda x: True if str(x).strip().lower() == 'correct' else False)
            # Question types for DI seem okay
            # --- End Rename/Transform ---
            data_sources['DI'] = 'File Upload' if uploaded_file_di else 'Pasted Data'
            st.success(f"DI 科目資料讀取成功 ({data_sources['DI']})！")
        except Exception as e:
            st.error(f"處理 DI 科目資料時發生錯誤：{e}")
            temp_df_di = None
            
    if temp_df_di is not None:
        df_di = temp_df_di
        st.subheader("DI 科目資料預覽")
        st.dataframe(df_di)

# --- Combine DataFrames (Moved before processing, no preview here) ---
dfs_to_combine = []
if df_q is not None:
    dfs_to_combine.append(df_q)
if df_v is not None:
    dfs_to_combine.append(df_v)
if df_di is not None:
    dfs_to_combine.append(df_di)

df_combined = None
if dfs_to_combine:
    try:
        df_combined = pd.concat(dfs_to_combine, ignore_index=True)
        # Removed combined preview from here
    except Exception as e:
        st.error(f"合併各科目資料時發生錯誤：{e}。請確保各檔案/貼上資料的欄位一致。")
        df_combined = None 
elif not data_sources: # Only show if no attempt was made to load data
    st.info("請展開上方區塊，為至少一個科目上傳檔案或貼上資料以開始分析。")

# --- Processing Section --- 
# Only proceed if combined data is available
if df_combined is not None:
    
    # --- Estimate Difficulty ---
    if not df_combined.empty:
        st.header("1. 計算題目難度")
        try:
            # --- Debugging: Show columns before check ---
            # st.write("合併後 DataFrame 的欄位:", df_combined.columns.tolist()) # Remove this line
            # --- End Debugging ---
            
            with st.spinner("計算題目難度中..."): 
                # Check for the *standardized* column names now
                if 'Question ID' in df_combined.columns and 'Correct' in df_combined.columns:
                     # Convert 'Correct' to numeric (1/0) for estimate_difficulty if it's boolean
                     if df_combined['Correct'].dtype == 'bool':
                          df_combined['Correct_numeric'] = df_combined['Correct'].astype(int)
                     else:
                          # Assume it might already be numeric or handle other types if necessary
                          df_combined['Correct_numeric'] = pd.to_numeric(df_combined['Correct'], errors='coerce').fillna(0).astype(int)
                     
                     # Pass the numeric version to the function, original df needs 'Correct' only
                     temp_difficulty_df = df_combined[['Question ID', 'Correct_numeric']].rename(columns={'Correct_numeric': 'Correct'})
                     df_combined['difficulty'] = estimate_difficulty(temp_difficulty_df)
                     df_combined = df_combined.drop(columns=['Correct_numeric']) # Drop helper column
                     
                     if df_combined['difficulty'].isnull().all():
                          st.warning("難度計算返回空值，請檢查 `irt_module.py` 和輸入資料。")
                          # Decide how to proceed: stop or continue without difficulty?
                          # For now, let's allow continuing but diagnosis might fail or be limited.
                     else:
                          st.success("難度計算完成！")
                          st.subheader("包含難度的資料預覽 (合併後)") # Re-add combined preview *with difficulty*
                          st.dataframe(df_combined.head()) 
                else:
                    st.error("標準化後的資料缺少 'Question ID' 或 'Correct' 欄位，無法計算難度。")
                    df_combined = None 
        except Exception as e:
            st.error(f"計算難度時發生錯誤：{e}")
            df_combined = None # Stop processing on error
    else:
        st.warning("載入的資料為空，無法計算難度。")
        df_combined = None # Stop processing if data is empty

    # --- Run Diagnosis --- 
    # Proceed only if difficulty calculation seemed successful (or was skipped but df exists)
    if df_combined is not None and 'difficulty' in df_combined.columns: 
        st.header("2. 執行診斷分析")
        result_df = None 
        try:
            with st.spinner("執行診斷分析中..."): 
                required_diag_cols = ['Question ID', 'Correct', 'difficulty', 'question_time', 'question_type']
                # --- Debug: Show columns before calling run_diagnosis ---
                # st.write("欄位傳遞給 run_diagnosis:", df_combined.columns.tolist()) # Remove this line
                # --- End Debug ---
                if all(col in df_combined.columns for col in required_diag_cols):
                    result_df = run_diagnosis(df_combined)
                    if result_df is not None and not result_df.empty:
                        st.success("診斷分析完成！")
                        st.subheader("診斷結果")
                        st.dataframe(result_df)
                        
                        # --- Add Download Button ---
                        try:
                            csv_data = result_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="下載診斷結果 CSV",
                                data=csv_data,
                                file_name='gmat_diagnosis_result.csv',
                                mime='text/csv',
                                key='download-csv' # Add a key
                            )
                        except Exception as e:
                            st.error(f"準備下載檔時發生錯誤：{e}")
                        # --- End Download Button ---
                    else:
                        st.warning("診斷分析未返回結果。請檢查 `diagnosis_module.py`。")
                else:
                    st.error(f"資料缺少診斷所需欄位 (如 {required_diag_cols})，無法執行診斷。")
                    result_df = None # Ensure result_df is None if diagnosis fails early
        except Exception as e:
            st.error(f"執行診斷時發生錯誤：{e}")
            result_df = None # Ensure result_df is None on error

        # --- Generate OpenAI Summary --- 
        # Proceed only if diagnosis produced results
        if result_df is not None and not result_df.empty: 
            if openai_api_key:
                st.header("3. AI 文字摘要")
                try:
                    client = openai.OpenAI(api_key=openai_api_key)
                    # Using result_df (summary of diagnosis) for the prompt now
                    prompt_data = result_df.to_string()
                    prompt = f"""請根據以下 GMAT 診斷結果摘要，產生一段簡潔的總結報告（約 100-150 字），說明主要的強項、弱項或值得注意的模式。請使用繁體中文回答。\n\n診斷摘要：\n{prompt_data}\n\n總結報告："""

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

# If df_combined never became valid, show a final message
# (Handled by the info message in the Combine DataFrames section)
