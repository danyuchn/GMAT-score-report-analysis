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

# Add a file uploader to the sidebar
st.sidebar.header("上傳成績單 CSV")
uploaded_file = st.sidebar.file_uploader("選擇一個 CSV 檔案", type="csv")

# Add a text area for pasting data from Excel
st.header("或直接貼上 Excel 資料")
pasted_data = st.text_area("將您的 Excel 成績資料貼在此處（包含標頭）：", height=250)

df = None # Initialize df

# Process uploaded file or pasted data
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("檔案上傳並讀取成功！")
    except Exception as e:
        st.sidebar.error(f"讀取 CSV 檔案時發生錯誤：{e}")
elif pasted_data:
    try:
        # Use StringIO for reading string data as a file
        df = pd.read_csv(StringIO(pasted_data), sep='\t')
        st.success("貼上資料讀取成功！")
    except Exception as e:
        st.error(f"處理貼上資料時發生錯誤：{e}")

# Display DataFrame preview if data is loaded
if df is not None:
    st.subheader("資料預覽 (前 5 筆)")
    st.dataframe(df.head())

    # Check if dataframe is not empty before processing
    if not df.empty:
        st.subheader("計算題目難度")
        try:
            with st.spinner("計算題目難度中..."): # Display spinner during calculation
                # Call the function and add the difficulty column
                df['difficulty'] = estimate_difficulty(df)
            st.success("難度計算完成！")
            st.subheader("包含難度的資料預覽")
            st.dataframe(df.head()) # Show preview with difficulty

            # Check if difficulty calculation was successful before proceeding
            if 'difficulty' in df.columns:
                st.subheader("執行診斷分析")
                try:
                    with st.spinner("執行診斷分析中..."): # Display spinner during diagnosis
                        result_df = run_diagnosis(df) # Call the diagnosis function
                    st.success("診斷分析完成！")
                    st.subheader("診斷結果")
                    st.dataframe(result_df) # Display the diagnosis result

                    # --- Add Download Button ---
                    csv_data = result_df.to_csv(index=False).encode('utf-8') # Convert df to csv string (utf-8 encoded)
                    st.download_button(
                        label="下載診斷結果 CSV",
                        data=csv_data,
                        file_name='gmat_diagnosis_result.csv',
                        mime='text/csv',
                    )
                    # --- End Download Button ---

                    # --- Generate OpenAI Summary ---
                    if openai_api_key: # Check if API key is available
                        if not result_df.empty:
                            st.subheader("AI 文字摘要")
                            try:
                                # Initialize OpenAI client (ensure openai package version >= 1.0)
                                client = openai.OpenAI(api_key=openai_api_key)

                                # Prepare the prompt
                                prompt_data = result_df.head(10).to_string()
                                prompt = f"""請根據以下 GMAT 診斷結果資料的前 10 筆，產生一段簡潔的摘要報告（約 100-150 字），說明主要的發現或趨勢。請使用繁體中文回答。\n\n資料：\n{prompt_data}\n\n摘要報告："""

                                with st.spinner("正在生成文字摘要..."):
                                    response = client.chat.completions.create(
                                        model="gpt-3.5-turbo", # You can change the model if needed
                                        messages=[
                                            {"role": "system", "content": "你是一個擅長分析 GMAT 診斷報告並產生摘要的 AI 助理。"},
                                            {"role": "user", "content": prompt}
                                        ]
                                    )
                                    summary = response.choices[0].message.content
                                st.markdown(summary)
                                st.success("文字摘要生成成功！")
                            except Exception as e:
                                st.error(f"生成 AI 摘要時發生錯誤：{e}")
                        else:
                             st.warning("診斷結果為空，無法生成 AI 摘要。")
                    else:
                        st.info("在側邊欄輸入您的 OpenAI API Key 以生成 AI 文字摘要。")
                    # --- End OpenAI Summary ---

                except Exception as e:
                    st.error(f"執行診斷時發生錯誤：{e}")
                # --- End Diagnosis ---
            else:
                # Error message for difficulty calculation might already be displayed
                # You could add an st.warning here if needed
                pass 

            # The rest of the error handling for difficulty calculation
            # ... existing code ...
        except Exception as e:
            st.error(f"計算難度時發生錯誤：{e}")
    else:
        st.warning("載入的資料為空，無法計算難度或執行診斷。")

# The rest of the app logic can potentially use result_df if needed elsewhere
