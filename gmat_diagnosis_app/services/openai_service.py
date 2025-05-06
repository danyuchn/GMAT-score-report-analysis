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
    """Gets response from OpenAI using the responses endpoint and handles conversation history.

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

    # Find the last user prompt
    last_user_prompt = ""
    if current_chat_history and current_chat_history[-1]["role"] == "user":
        last_user_prompt = current_chat_history[-1]["content"]
    else:
        raise ValueError("Could not find the last user prompt in history.")

    # Find the previous response ID from the last assistant message
    previous_response_id = None
    if len(current_chat_history) > 1:
        for i in range(len(current_chat_history) - 2, -1, -1):
            if current_chat_history[i]["role"] == "assistant":
                previous_response_id = current_chat_history[i].get("response_id")
                break

    # Construct the input for the API using standard multi-line string and .format()
    input_template = '''You are a GMAT diagnostic assistant. Analyze the provided report summary and detailed data table (excerpt) to answer the user's question accurately and concisely. If the information is not present in the provided context, say so.

REPORT SUMMARY:
{report}

DETAILED DATA EXCERPT:
{data}

USER QUESTION:
{prompt}
'''
    api_input = input_template.format(
        report=report_context,
        data=dataframe_context,
        prompt=last_user_prompt
    )

    try:
        logging.info(f"Calling OpenAI responses.create with model o4-mini. Previous ID: {previous_response_id}")
        response = client.responses.create(
            model="o4-mini", # Using the model from user's example
            input=api_input,
            previous_response_id=previous_response_id,
            # Add other parameters if needed, e.g., temperature, max_tokens based on API docs
            # max_output_tokens=500, # Example: limit output tokens
        )
        logging.info(f"OpenAI response received. Status: {response.status}")

        if response.status == 'completed' and response.output:
            # Extract text from the first output message content
            response_text = ""
            # Iterate through the output list to find the message block
            message_block = None
            for item in response.output:
                if hasattr(item, 'type') and item.type == 'message':
                    message_block = item
                    break # Found the message block

            if message_block and hasattr(message_block, 'content') and message_block.content:
                for content_block in message_block.content:
                    # Ensure the content_block itself has a type attribute before checking
                    if hasattr(content_block, 'type') and content_block.type == 'output_text':
                        response_text += content_block.text

            if not response_text:
                 # --- Log the output structure before raising error ---
                 logging.error(f"OpenAI response completed but no text found after iterating. Response output structure: {response.output}")
                 # --- End Log ---
                 raise ValueError("OpenAI response completed but contained no text output after iterating.")

            return response_text.strip(), response.id
        elif response.status == 'error':
             error_details = response.error if response.error else "Unknown error"
             raise Exception(f"OpenAI API error: {error_details}")
        else:
             # --- Log the output structure before raising error ---
             logging.error(f"OpenAI response status not completed or output empty. Status: {response.status}. Response output structure: {response.output}")
             # --- End Log ---
             raise Exception(f"OpenAI response status was not 'completed' or output was empty. Status: {response.status}")

    except Exception as e:
        logging.error(f"Error calling OpenAI responses API: {e}", exc_info=True)
        # Re-raise the exception to be caught by the sidebar UI
        raise e 