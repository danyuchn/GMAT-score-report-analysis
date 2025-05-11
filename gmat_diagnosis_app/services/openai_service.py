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

def get_chat_context(session_state, max_rows=100):
    """Get combined report and dataframe context for chat."""
    context = {
        "report": _get_combined_report_context(session_state),
        "dataframe": _get_dataframe_context(session_state, max_rows)
    }
    return context

def _get_combined_report_context(session_state):
    """Combines markdown reports from all subjects."""
    full_report = ""
    
    # 檢查是否有重要分數/百分位資訊並添加到報告開頭
    if hasattr(session_state, 'total_score') and session_state.total_score:
        full_report += "## 總體分數與百分位\n\n"
        
        # 添加各科目分數
        scores_text = []
        if hasattr(session_state, 'q_score') and session_state.q_score:
            scores_text.append(f"Q (Quantitative): {session_state.q_score}")
        if hasattr(session_state, 'v_score') and session_state.v_score:
            scores_text.append(f"V (Verbal): {session_state.v_score}")
        if hasattr(session_state, 'di_score') and session_state.di_score:
            scores_text.append(f"DI (Data Insights): {session_state.di_score}")
        if hasattr(session_state, 'total_score') and session_state.total_score:
            scores_text.append(f"Total: {session_state.total_score}")
            
        if scores_text:
            full_report += "### 各科目分數\n\n"
            for score in scores_text:
                full_report += f"- {score}\n"
            full_report += "\n"
    
    # 添加AI總結建議（如果存在）
    if hasattr(session_state, 'consolidated_report_text') and session_state.consolidated_report_text:
        full_report += "## AI 總結建議\n\n"
        full_report += session_state.consolidated_report_text
        full_report += "\n\n---\n\n"
    
    # 添加各科目診斷報告
    if session_state.report_dict:
        for subject in ['Q', 'V', 'DI']:  # 明確定義科目順序
            report = session_state.report_dict.get(subject)
            if report:
                full_report += f"## {subject} 科診斷報告\n\n{report}\n\n---\n\n"
                
    # 如果已經存在新診斷報告（從編輯標籤生成），則添加到報告中
    if hasattr(session_state, 'editable_diagnostic_df') and session_state.editable_diagnostic_df is not None:
        try:
            # 使用內部函數生成新診斷報告，避免循環導入
            df = session_state.editable_diagnostic_df
            if 'generated_new_diagnostic_report' in session_state:
                # 使用已生成的報告
                new_report = session_state.generated_new_diagnostic_report
                full_report += "## 新標籤分類報告\n\n"
                full_report += new_report
                full_report += "\n\n"
            else:
                # 嘗試生成新報告
                logging.info("嘗試生成新診斷報告...")
                # 我們將使用動態導入來避免循環導入問題
                import importlib
                try:
                    results_display_module = importlib.import_module('gmat_diagnosis_app.ui.results_display')
                    generate_report_func = getattr(results_display_module, 'generate_new_diagnostic_report')
                    
                    new_report = generate_report_func(df)
                    if new_report:
                        # 保存到session_state以便重複使用
                        session_state.generated_new_diagnostic_report = new_report
                        full_report += "## 新標籤分類報告\n\n"
                        full_report += new_report
                        full_report += "\n\n"
                except (ImportError, AttributeError) as ie:
                    logging.error(f"無法導入或使用generate_new_diagnostic_report函數: {ie}")
        except Exception as e:
            logging.error(f"生成新診斷報告時出錯: {e}")
    
    return full_report.strip()

def _get_dataframe_context(session_state, max_rows=100):
    """Converts the processed dataframe to a string format (markdown) for context."""
    # 優先使用修剪標籤後的數據表格 (如果存在)
    if hasattr(session_state, 'editable_diagnostic_df') and session_state.editable_diagnostic_df is not None and not session_state.editable_diagnostic_df.empty:
        df_context = session_state.editable_diagnostic_df.copy()
        logging.info(f"準備轉換修剪標籤後的診斷試算表，原始列數: {len(df_context)}, 列名: {', '.join(df_context.columns)}")
    elif session_state.processed_df is not None and not session_state.processed_df.empty:
        df_context = session_state.processed_df.copy()
        logging.info(f"準備轉換原始診斷試算表，原始列數: {len(df_context)}, 列名: {', '.join(df_context.columns)}")
    else:
        logging.warning("診斷試算表為空或不存在")
        return "(無詳細數據表格)"
        
    try:
        # 選擇關鍵列以提高可讀性，排除不必要的列
        important_cols = [
            'Subject', 'question_position', 'question_type', 'question_fundamental_skill',
            'content_domain', 'is_invalid', 'is_correct', 'question_time',
            'time_performance_category', 'diagnostic_params_list'
        ]
        
        # 只保留存在於 DataFrame 中的列
        cols_to_use = [col for col in important_cols if col in df_context.columns]
        
        # 添加其他可能有用的列（但優先使用上面定義的關鍵列）
        for col in df_context.columns:
            if col not in cols_to_use and col not in ['raw_content']:
                cols_to_use.append(col)
        
        logging.info(f"選擇的列: {', '.join(cols_to_use)}")
        
        # 如果有列可用，則使用這些列；否則使用所有列
        if cols_to_use:
            df_context = df_context[cols_to_use]
        
        # Convert boolean columns to Yes/No for better readability for the LLM
        bool_cols = df_context.select_dtypes(include=bool).columns
        for col in bool_cols:
            df_context[col] = df_context[col].map({True: 'Yes', False: 'No'})
            logging.info(f"已將布爾列 '{col}' 轉換為 Yes/No 格式")

        # Convert list column to string
        if 'diagnostic_params_list' in df_context.columns:
            df_context['diagnostic_params_list'] = df_context['diagnostic_params_list'].apply(
                lambda x: ', '.join(map(str, x)) if isinstance(x, list) else str(x)
            )
            logging.info("已將 'diagnostic_params_list' 列轉換為字符串格式")

        # Limit rows to avoid excessive context length
        if len(df_context) > max_rows:
            logging.info(f"數據行數超過限制 ({len(df_context)} > {max_rows})，只取前 {max_rows} 行")
            df_context_str = df_context.head(max_rows).to_markdown(index=False)
            df_context_str += f"\n... (只顯示前 {max_rows} 行，共 {len(df_context)} 行)"
        else:
            logging.info(f"轉換全部 {len(df_context)} 行數據為 markdown 格式")
            df_context_str = df_context.to_markdown(index=False)
        
        logging.info(f"成功轉換診斷試算表，輸出長度約 {len(df_context_str)} 字符")
        return df_context_str
    except Exception as e:
        error_msg = f"Error converting dataframe to markdown context: {e}"
        logging.error(error_msg, exc_info=True)
        return f"(無法轉換詳細數據表格: {str(e)})"

def get_openai_response(current_chat_history, report_context, dataframe_context, api_key):
    """Get response from OpenAI based on chat history and context, using o4-mini.

    Args:
        current_chat_history (list): The current conversation history.
        report_context (str): Markdown string of the GMAT report.
        dataframe_context (str): Markdown string of the diagnostic dataframe.
        api_key (str): OpenAI API key.

    Returns:
        tuple: (ai_response_text, response_id) or (error_message_string, None)
    """
    if not api_key:
        logging.error("OpenAI API key is missing for chat.")
        return "錯誤：OpenAI API 金鑰未設定。", None

    client = openai.OpenAI(api_key=api_key)

    # Determine if this is the first user message in the session for this specific chat.
    # A simple heuristic: if chat history has only one user message (the current one being processed)
    # or two messages (system (if we decide to add one initially), user), it's likely the first real interaction.
    # For robustness, let's count user messages.
    user_message_count = sum(1 for msg in current_chat_history if msg['role'] == 'user')

    is_first_exchange = user_message_count <= 1

    if is_first_exchange:
        # First exchange: include the full report and dataframe context
        system_prompt_content = f"""You are an expert GMAT diagnostic assistant. 
Your goal is to help the user understand their GMAT performance based on the provided diagnostic report and data.

Here is the user's GMAT diagnostic report:
--- BEGIN REPORT ---
{report_context}
--- END REPORT ---

Here is the user's detailed diagnostic data (questions, answers, time spent, etc.):
--- BEGIN DATA ---
{dataframe_context}
--- END DATA ---

Answer the user's questions based on this report and data. Be concise, helpful, and refer to specific details from the report or data when possible.
If the user asks for something not in the report or data, state that the information is unavailable.
Maintain a conversational and supportive tone.
"""
    else:
        # Subsequent exchanges: use a simpler system prompt, assuming context is maintained by conversation history.
        system_prompt_content = """You are an expert GMAT diagnostic assistant. 
Continue the conversation based on the provided history. Be concise, helpful, and refer to specific details from the report or data if they were mentioned earlier or are relevant.
If the user asks for something not in the report or data that wasn't previously established, state that the information is unavailable.
Maintain a conversational and supportive tone.
"""

    messages_for_api = [
        {"role": "system", "content": system_prompt_content}
    ]
    # Append the actual chat history (user and assistant messages)
    # We need to ensure the history format is correct for the API
    for message in current_chat_history:
        role = message.get("role")
        content = message.get("content", "") # Default to empty string if content is missing
        if not isinstance(content, str):
            content = str(content) # Ensure content is a string

        if role:
            # Only include 'role' and 'content' keys in the message sent to the API
            messages_for_api.append({"role": role, "content": content})
        # No longer need the separate case for `elif message.get("role")` with empty content,
        # as `message.get("content", "")` handles it.

    # Get previous response_id if available from the last assistant message
    previous_response_id = None
    if len(current_chat_history) > 1:
        # Iterate backwards to find the last assistant message with a response_id
        for i in range(len(current_chat_history) - 1, -1, -1):
            msg = current_chat_history[i]
            if msg.get("role") == "assistant" and msg.get("response_id"):
                previous_response_id = msg.get("response_id")
                logging.info(f"Found previous_response_id: {previous_response_id[:10]}...")
                break 

    try:
        logging.info(f"Calling OpenAI o4-mini. is_first_exchange: {is_first_exchange}. History length: {len(messages_for_api)}. Previous_id: {previous_response_id[:10] if previous_response_id else 'None'}")
        
        # Debug: Log the system prompt being used
        if is_first_exchange:
            logging.info("Sending request with full context in system prompt.")
        else:
            logging.info("Sending request with simplified system prompt.")

        response = client.responses.create(
            model="o4-mini", 
            input=messages_for_api, # Pass the constructed messages list
            # The 'o4-mini' model expects input as a list of messages, not a single prompt string.
            # `prompt` parameter is not used with this model for chat-like interactions.
            previous_response_id=previous_response_id, # Pass the ID for context
            # max_output_tokens=1000 # Optional, if needed for controlling response length
        )
        logging.info(f"OpenAI response status: {response.status}")

        if response.status == 'completed' and response.output:
            ai_response_text = ""
            message_block = None
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    message_block = item
                    break
            
            if message_block and hasattr(message_block, 'content') and message_block.content:
                for content_block in message_block.content:
                    if hasattr(content_block, 'type') and content_block.type == 'output_text':
                        ai_response_text += content_block.text

            if not ai_response_text:
                logging.error("OpenAI response completed but no text found.")
                return "AI 回應為空，請稍後再試。", None
            
            new_response_id = response.id
            logging.info(f"OpenAI response successful. New response_id: {new_response_id[:10] if new_response_id else 'N/A'}...")
            return ai_response_text.strip(), new_response_id
        
        elif response.status == 'error':
            error_details = response.error if response.error else "Unknown error"
            logging.error(f"OpenAI API error: {error_details}")
            return f"AI 服務出錯: {error_details}", None
        else:
            logging.error(f"OpenAI response status not completed or output empty. Status: {response.status}")
            return f"AI 未能成功回應 (狀態: {response.status})，請稍後再試。", None

    except openai.AuthenticationError:
        error_msg = "OpenAI API密鑰無效"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.RateLimitError:
        error_msg = "OpenAI API請求頻率過高，請稍後再試"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.APIConnectionError as e:
        error_msg = f"連接OpenAI API時出錯: {e}"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.APITimeoutError:
        error_msg = "OpenAI API請求超時"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.BadRequestError as e:
        error_msg = f"OpenAI API請求無效: {e}"
        logging.error(error_msg)
        return error_msg, None
        
    except Exception as e:
        error_msg = f"與OpenAI API通訊時發生未知錯誤: {e}"
        logging.error(error_msg, exc_info=True)
        return error_msg, None

def trim_diagnostic_tags_with_openai(original_tags_str: str, user_description: str, api_key: str) -> str:
    """
    Uses OpenAI to suggest a trimmed list of 1-2 most relevant diagnostic tags
    based on original tags and user's description of their difficulty.

    Args:
        original_tags_str: A string containing the original diagnostic tags (e.g., comma-separated or list-like).
        user_description: User's description of their difficulty with the question.
        api_key: OpenAI API key.

    Returns:
        A string containing the AI's suggested trimmed tags, or an error message.
    """
    if not api_key:
        logging.warning("OpenAI API key is missing for tag trimming.")
        return "錯誤：OpenAI API 金鑰未提供。"
    if not original_tags_str.strip():
        return "錯誤：原始診斷標籤不能為空。"
    if not user_description.strip():
        return "錯誤：使用者描述不能為空。"

    client = openai.OpenAI(api_key=api_key)

    system_prompt = """
您是一位專業的 GMAT 診斷標籤修剪助手。
您的任務是分析使用者提供的「原始診斷標籤」（以逗號,分隔）以及他們「對題目的描述或遇到的困難」。
根據使用者的描述，從原始標籤中篩選出 1 至 2 個最能直接對應並解釋使用者所述困難的核心診斷標籤。

輸出要求：
- 直接返回修剪後建議的 1 或 2 個標籤全名，不要省略成簡名。
- 如果有多個建議標籤，請用逗號和一個空格（例如：標籤1, 標籤2）分隔。
- 如果原始標籤已經很少（例如只有1-2個）且與使用者描述相關，可以直接返回原始標籤（或相關的部分）。
- 如果根據使用者描述，原始標籤中沒有明顯直接相關的標籤，請明確指出「根據您的描述，原始標籤中未找到直接對應的項目。」
- 不要添加任何解釋、引言或額外的客套話，只需提供建議的標籤或上述明確的提示。
"""
    
    user_content = f"原始診斷標籤：\n{original_tags_str}\n\n使用者描述：\n{user_description}"

    try:
        logging.info("Calling OpenAI ChatCompletion for tag trimming with model gpt-3.5-turbo.")
        response = client.chat.completions.create(
            model="gpt-4.1-mini", # Using a cost-effective and capable model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2, # Lower temperature for more deterministic output
            max_tokens=100 # Expecting a short list of tags
        )
        
        trimmed_suggestion = response.choices[0].message.content
        
        if trimmed_suggestion and trimmed_suggestion.strip():
            logging.info(f"OpenAI tag trimming successful. Suggestion: {trimmed_suggestion}")
            return trimmed_suggestion.strip()
        else:
            logging.warning("OpenAI returned empty response for tag trimming.")
            return "AI 未能提供修剪建議（返回空內容）。"

    except openai.AuthenticationError:
        logging.error("OpenAI AuthenticationError during tag trimming.")
        return "錯誤：OpenAI API 金鑰無效或權限不足。"
    except openai.RateLimitError:
        logging.error("OpenAI RateLimitError during tag trimming.")
        return "錯誤：OpenAI API 請求頻率過高，請稍後再試。"
    except openai.APIConnectionError as e:
        logging.error(f"OpenAI APIConnectionError during tag trimming: {e}")
        return f"錯誤：無法連接至 OpenAI API ({e})。"
    except openai.APITimeoutError:
        logging.error("OpenAI APITimeoutError during tag trimming.")
        return "錯誤：OpenAI API 請求超時。"
    except openai.BadRequestError as e:
        logging.error(f"OpenAI BadRequestError during tag trimming: {e}")
        return f"錯誤：OpenAI API 請求無效 ({e})。可能是輸入內容問題。"
    except Exception as e:
        logging.error(f"Unknown OpenAI API error during tag trimming: {e}", exc_info=True)
        return f"調用 OpenAI API 時發生未知錯誤：{e}。" 