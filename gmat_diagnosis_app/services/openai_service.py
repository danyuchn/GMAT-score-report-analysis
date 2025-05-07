"""
OpenAI服務模組
提供與OpenAI API通信的功能
"""

import logging
import streamlit as st
import openai

def summarize_report_with_openai(report_markdown, api_key):
    """Attempts to summarize/reformat a report using OpenAI API."""
    if not api_key:
        logging.warning("OpenAI API key is missing. Skipping summarization.")
        return report_markdown # Return original if no key

    try:
        # Ensure openai library is accessible
        client = openai.OpenAI(api_key=api_key) # Initialize client
        system_prompt = """You are an assistant that reformats GMAT diagnostic reports. Use uniform heading levels: Level-2 headings for all major sections (## Section Title). Level-3 headings for subsections (### Subsection Title). Reformat content into clear Markdown tables where appropriate. Fix minor grammatical errors or awkward phrasing for readability. IMPORTANT: Do NOT add or remove any substantive information or conclusions. Only reformat and polish the existing text. Output strictly in Markdown format, without code blocks.  """

        response = client.chat.completions.create(
            model="gpt-4.1-nano", # Use the specified model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": report_markdown}
            ],
            # temperature=0.2 # Removed: o4-mini only supports default (1)
        )
        summarized_report = response.choices[0].message.content
        # Basic check if response seems valid (not empty)
        if summarized_report and summarized_report.strip():
             logging.info(f"OpenAI summarization successful for report starting with: {report_markdown[:50]}...")
             return summarized_report.strip()
        else:
             logging.warning("OpenAI returned empty response. Using original report.")
             st.warning("AI 整理報告時返回了空內容，將使用原始報告。", icon="⚠️")
             return report_markdown

    except openai.AuthenticationError:
        st.warning("OpenAI API Key 無效或權限不足，無法整理報告文字。請檢查側邊欄輸入或環境變數。", icon="🔑")
        logging.error("OpenAI AuthenticationError.")
        return report_markdown
    except openai.RateLimitError:
        st.warning("OpenAI API 請求頻率過高，請稍後再試。暫時使用原始報告文字。", icon="⏳")
        logging.error("OpenAI RateLimitError.")
        return report_markdown
    except openai.APIConnectionError as e:
        st.warning(f"無法連接至 OpenAI API ({e})，請檢查網路連線。暫時使用原始報告文字。", icon="🌐")
        logging.error(f"OpenAI APIConnectionError: {e}")
        return report_markdown
    except openai.APITimeoutError:
        st.warning("OpenAI API 請求超時。暫時使用原始報告文字。", icon="⏱️")
        logging.error("OpenAI APITimeoutError.")
        return report_markdown
    except openai.BadRequestError as e:
        # Often happens with context length issues or invalid requests
        st.warning(f"OpenAI API 請求無效 ({e})。可能是報告過長或格式問題。暫時使用原始報告文字。", icon="❗") # Use valid emoji
        logging.error(f"OpenAI BadRequestError: {e}")
        return report_markdown
    except Exception as e:
        st.warning(f"調用 OpenAI API 時發生未知錯誤：{e}。暫時使用原始報告文字。", icon="⚠️")
        logging.error(f"Unknown OpenAI API error: {e}", exc_info=True)
        return report_markdown

def generate_ai_consolidated_report(report_dict, api_key):
    """Generates a consolidated report of suggestions and next steps using OpenAI o4-mini.

    Args:
        report_dict (dict): Dictionary containing the diagnostic reports for each subject (Q, V, DI).
        api_key (str): OpenAI API key.

    Returns:
        str: The generated consolidated report in Markdown, or None if an error occurs.
    """
    if not api_key:
        logging.warning("OpenAI API key missing. Skipping consolidated report generation.")
        return None
    if not report_dict:
        logging.warning("Report dictionary is empty. Skipping consolidated report generation.")
        return None

    client = openai.OpenAI(api_key=api_key)

    # Construct the full input text from individual reports
    full_report_text = ""
    for subject, report in report_dict.items():
        if report:
            full_report_text += f"## {subject} Report:\n\n{report}\n\n---\n\n"

    if not full_report_text.strip():
        logging.warning("No valid reports found in the dictionary. Skipping consolidated report generation.")
        return None

    # Define the system prompt emphasizing strict extraction and formatting
    system_prompt = """You are an assistant that extracts specific sections from GMAT diagnostic reports and consolidates them into a single, structured document.
Your task is to identify and extract ONLY the sections related to '練習建議' (Practice Suggestions) and '後續行動' (Next Steps, including reflection and secondary evidence gathering) for each subject (Q, V, DI) from the provided text.

**CRITICAL INSTRUCTIONS:**
1.  **Strict Extraction:** Only extract text explicitly under '練習建議' or '後續行動' headings or clearly discussing these topics.
2.  **Subject Separation:** Keep the extracted information strictly separated under standardized headings for each subject: `## Q 科目建議與行動`, `## V 科目建議與行動`, `## DI 科目建議與行動`.
3.  **Complete Information:** Transfer ALL original text, data, details, parenthetical notes, specific question numbers, difficulty codes, time limits, percentages, scores, etc., accurately and completely. DO NOT SUMMARIZE OR OMIT ANY DETAILS.
4.  **Standardized Formatting:** Use Markdown format. Use Level-2 headings (##) for each subject as specified above. Use bullet points or numbered lists within each subject section as they appear in the original text, or to improve readability if appropriate, but maintain all original content.
5.  **No Additions:** Do not add any information, interpretation, or introductory/concluding text not present in the extracted sections.
6.  **Output Format:** Output only the consolidated Markdown report. Do not include any other text or commentary.
"""

    try:
        logging.info("Calling OpenAI responses.create with model o4-mini for consolidated report.")
        response = client.responses.create(
            model="o4-mini",
            input=f"""
System: {system_prompt}

User: 從以下 GMAT 診斷報告中提取練習建議和後續行動部分，按科目分類並整理成統一格式：

{full_report_text}
""",
            # No prompt parameter - incorporate system instructions into input instead
            # No previous_response_id needed for this one-off task
            # max_output_tokens=1000 # Optional: Set a limit if needed
        )
        logging.info(f"OpenAI consolidated report response received. Status: {response.status}")

        if response.status == 'completed' and response.output:
            response_text = ""
            message_block = None
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    message_block = item
                    break

            if message_block and hasattr(message_block, 'content') and message_block.content:
                for content_block in message_block.content:
                    if hasattr(content_block, 'type') and content_block.type == 'output_text':
                        response_text += content_block.text

            if not response_text:
                logging.error("OpenAI consolidated report response completed but no text found.")
                st.warning("AI 無法生成匯總報告（返回空內容）。", icon="⚠️")
                return None
            else:
                logging.info("Successfully generated consolidated report.")
                return response_text.strip()
        elif response.status == 'error':
            error_details = response.error if response.error else "Unknown error"
            logging.error(f"OpenAI API error (consolidated report): {error_details}")
            st.warning(f"AI 生成匯總報告時出錯：{error_details}", icon="❗")
            return None
        else:
            logging.error(f"OpenAI consolidated report status not completed or output empty. Status: {response.status}")
            st.warning(f"AI 未能成功生成匯總報告（狀態：{response.status}）。", icon="⚠️")
            return None

    except openai.AuthenticationError:
        st.warning("OpenAI API Key 無效或權限不足，無法生成匯總報告。", icon="🔑")
        logging.error("OpenAI AuthenticationError (consolidated report).")
        return None
    except openai.RateLimitError:
        st.warning("OpenAI API 請求頻率過高，無法生成匯總報告。", icon="⏳")
        logging.error("OpenAI RateLimitError (consolidated report).")
        return None
    except openai.APIConnectionError as e:
        st.warning(f"無法連接至 OpenAI API ({e})，無法生成匯總報告。", icon="🌐")
        logging.error(f"OpenAI APIConnectionError (consolidated report): {e}")
        return None
    except openai.APITimeoutError:
        st.warning("OpenAI API 請求超時，無法生成匯總報告。", icon="⏱️")
        logging.error("OpenAI APITimeoutError (consolidated report).")
        return None
    except openai.BadRequestError as e:
        st.warning(f"OpenAI API 請求無效 ({e})，無法生成匯總報告。", icon="❗")
        logging.error(f"OpenAI BadRequestError (consolidated report): {e}")
        return None
    except Exception as e:
        st.warning(f"生成 AI 匯總建議時發生未知錯誤：{e}", icon="⚠️")
        logging.error(f"Unknown error during consolidated report generation: {e}", exc_info=True)
        return None

def get_chat_context(session_state, max_rows=50):
    """Get combined report and dataframe context for chat."""
    context = {
        "report": _get_combined_report_context(session_state),
        "dataframe": _get_dataframe_context(session_state, max_rows)
    }
    return context

def _get_combined_report_context(session_state):
    """Combines markdown reports from all subjects."""
    full_report = ""
    if session_state.report_dict:
        for subject in ['Q', 'V', 'DI']:  # Explicitly define subjects order
            report = session_state.report_dict.get(subject)
            if report:
                full_report += f"\n\n## {subject} 科診斷報告\n\n{report}"
    return full_report.strip()

def _get_dataframe_context(session_state, max_rows=50):
    """Converts the processed dataframe to a string format (markdown) for context."""
    if session_state.processed_df is not None and not session_state.processed_df.empty:
        df_context = session_state.processed_df.copy()
        # Optionally select/rename columns for clarity in context
        # For now, let's convert a sample to markdown
        try:
            # Convert boolean columns to Yes/No for better readability for the LLM
            bool_cols = df_context.select_dtypes(include=bool).columns
            for col in bool_cols:
                df_context[col] = df_context[col].map({True: 'Yes', False: 'No'})

            # Convert list column to string
            if 'diagnostic_params_list' in df_context.columns:
                df_context['diagnostic_params_list'] = df_context['diagnostic_params_list'].apply(
                    lambda x: ', '.join(map(str, x)) if isinstance(x, list) else str(x)
                )

            # Limit rows to avoid excessive context length
            if len(df_context) > max_rows:
                df_context_str = df_context.head(max_rows).to_markdown(index=False)
                df_context_str += f"\n... (只顯示前 {max_rows} 行)"
            else:
                df_context_str = df_context.to_markdown(index=False)
            return df_context_str
        except Exception as e:
            logging.error(f"Error converting dataframe to markdown context: {e}")
            return "(無法轉換詳細數據表格)"
    return "(無詳細數據表格)"

def get_openai_response(current_chat_history, report_context, dataframe_context, api_key):
    """Gets response from OpenAI using the responses API and handles conversation history.

    Args:
        current_chat_history (list): The current chat history list.
        report_context (str): The combined markdown report context.
        dataframe_context (str): The dataframe context string.
        api_key (str): OpenAI API key.

    Returns:
        tuple: (ai_response_text, response_id) or raises an exception.
    """
    if not api_key:
        raise ValueError("OpenAI API Key is missing.")

    client = openai.OpenAI(api_key=api_key)

    chat_system_prompt = f"""You are a helpful GMAT diagnostic assistant.
Your primary goal is to answer questions based SOLELY on the provided GMAT diagnostic report and detailed data table.
Do NOT use any external knowledge or make assumptions beyond what is in the context.
If the answer cannot be found in the provided report or data, state that clearly.

**Provided Context:**

```
### Report
{report_context}

### Data Details
{dataframe_context}
```

Answer questions about the GMAT diagnostic results in a direct, helpful, and accurate manner. 
If answering in Chinese, use traditional Chinese characters (繁體中文).
"""

    # 準備用於構建對話的輸入文本
    input_text = ""
    
    # 找出最後一條 assistant 消息的 response_id（如果存在）
    previous_response_id = None
    for message in reversed(current_chat_history):
        if message["role"] == "assistant" and "response_id" in message:
            previous_response_id = message["response_id"]
            break
    
    # 顯示最新訊息記錄
    latest_message = current_chat_history[-1]["content"] if current_chat_history else None
    logging.info(f"準備發送至 OpenAI 的最新訊息: {latest_message[:30]}...")
    
    # 構建系統指令和對話歷史
    input_text = f"System: {chat_system_prompt}\n\n"
    
    # 添加對話歷史（最多取最近10條，避免過長）
    history_start_idx = max(0, len(current_chat_history) - 11)  # 保留最多10輪對話
    for i, msg in enumerate(current_chat_history[history_start_idx:], start=history_start_idx):
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            input_text += f"User: {content}\n\n"
        elif role == "assistant":
            input_text += f"Assistant: {content}\n\n"

    try:
        logging.info(f"調用 OpenAI responses.create API，previous_response_id: {previous_response_id[:10]}... 如果有的話")
        
        # 設定API呼叫參數
        api_params = {
            "model": "gpt-4.1-turbo",  # 可以根據需要調整模型
            "input": input_text,
            "temperature": 0.7,
            "store": True,  # 存儲對話歷史
        }
        
        # 如果存在前一個回應ID，加入previous_response_id參數
        if previous_response_id:
            api_params["previous_response_id"] = previous_response_id
            
        # 調用responses API
        response = client.responses.create(**api_params)
        
        # 記錄回應狀態
        logging.info(f"OpenAI API 回應狀態: {response.status}")
        
        if response.status == "completed" and response.output:
            # 提取回應文本
            response_text = ""
            for output_item in response.output:
                if hasattr(output_item, 'type') and output_item.type == 'message':
                    for content_item in output_item.content:
                        if hasattr(content_item, 'type') and content_item.type == 'output_text':
                            response_text += content_item.text

            if not response_text.strip():
                logging.error("OpenAI返回空回應")
                raise ValueError("AI未提供有效的回應")
                
            # 獲取response_id以便下次對話使用
            response_id = response.id
            logging.info(f"成功獲取OpenAI回應，ID: {response_id[:10]}...")
            
            return response_text.strip(), response_id
            
        elif response.status == "error":
            error_detail = response.error.get("message", "未知錯誤") if response.error else "未知錯誤"
            logging.error(f"OpenAI API錯誤: {error_detail}")
            raise ValueError(f"AI回應錯誤: {error_detail}")
            
        else:
            logging.error(f"無法處理的OpenAI回應狀態: {response.status}")
            raise ValueError("獲取AI回應時發生未知錯誤")
            
    except openai.AuthenticationError:
        error_msg = "OpenAI API密鑰無效"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    except openai.RateLimitError:
        error_msg = "OpenAI API請求頻率過高，請稍後再試"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    except openai.APIConnectionError as e:
        error_msg = f"連接OpenAI API時出錯: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    except openai.APITimeoutError:
        error_msg = "OpenAI API請求超時"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    except openai.BadRequestError as e:
        error_msg = f"OpenAI API請求無效: {e}"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    except Exception as e:
        error_msg = f"與OpenAI API通訊時發生未知錯誤: {e}"
        logging.error(error_msg, exc_info=True)
        raise ValueError(error_msg) 