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

    # 檢查上下文內容的有效性
    report_context_valid = bool(report_context and report_context.strip())
    dataframe_context_valid = bool(dataframe_context and dataframe_context.strip())

    logging.info(f"報告上下文有效: {report_context_valid}, 長度: {len(report_context) if report_context_valid else 0}")
    logging.info(f"診斷試算表上下文有效: {dataframe_context_valid}, 長度: {len(dataframe_context) if dataframe_context_valid else 0}")

    # 如果診斷試算表內容為空，添加警告
    if not dataframe_context_valid:
        logging.warning("診斷試算表內容為空，AI回應可能不完整")
        dataframe_context = "(診斷試算表數據不可用)"

    # 構建系統指令和對話歷史
    chat_system_prompt = f"""You are a helpful GMAT diagnostic assistant.
Your primary goal is to answer questions based SOLELY on the provided GMAT diagnostic report and detailed data table.
Do NOT use any external knowledge or make assumptions beyond what is in the context.
If the answer cannot be found in the provided report or data, state that clearly.

**IMPORTANT**: You have access to both text reports and a diagnostic spreadsheet data table. Please analyze both to provide comprehensive answers.

**Provided Context:**

```markdown
### Report
{report_context}
```

```markdown
### Diagnostic Data Table (診斷試算表)
{dataframe_context}
```

Answer questions about the GMAT diagnostic results in a direct, helpful, and accurate manner. 
If answering in Chinese, use traditional Chinese characters (繁體中文).
"""

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
        # 修復：檢查previous_response_id是否為None
        log_info = "調用 OpenAI responses.create API"
        if previous_response_id:
            log_info += f"，previous_response_id: {previous_response_id[:10]}..."
        logging.info(log_info)
        
        # 設定API呼叫參數
        api_params = {
            "model": "o4-mini",  # 使用o4-mini模型
            "input": input_text,
            "store": True,  # 存儲對話歷史
            "max_output_tokens": 4000,  # 增加輸出標記的最大數量
        }
        
        # 如果存在前一個回應ID，加入previous_response_id參數
        if previous_response_id:
            api_params["previous_response_id"] = previous_response_id
            
        # 記錄完整的input_text長度，用於調試
        logging.info(f"發送至OpenAI的input_text總長度: {len(input_text)} 字符")
        
        # 記錄最後的用戶訊息與診斷試算表長度比較
        if latest_message:
            logging.info(f"用戶最新訊息長度: {len(latest_message)} 字符，診斷試算表長度: {len(dataframe_context) if dataframe_context_valid else 0} 字符")
        
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
            # 修復：安全記錄ID
            logging.info(f"成功獲取OpenAI回應，ID: {response_id[:10] if response_id else 'N/A'}...")
            
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