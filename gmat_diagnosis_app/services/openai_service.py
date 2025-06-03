"""
OpenAI服務模組
提供與OpenAI API通信的功能
"""

import logging
import streamlit as st
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential
import os
from ..utils.rate_limiter import get_client_ip, check_rate_limit # Import rate limiting functions
from ..i18n import translate as t # Import translation function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = None
api_key_env = os.environ.get("OPENAI_API_KEY")
master_key_env = os.environ.get("MASTER_KEY")

# Decorator for retrying API calls
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def chat_completion_request_with_retry(**kwargs):
    """Makes a request to the OpenAI API with retries on failure."""
    if not client:
        st.error("OpenAI 客戶端未初始化，無法處理請求。請檢查驗證狀態。")
        raise Exception("OpenAI client not initialized.") # Raise exception to stop retry
    
    # Rate Limiting Check
    ip_address = get_client_ip()
    if not check_rate_limit(ip_address):
        st.error(f"抱歉，您今天的 API 使用次數已達上限 ({check_rate_limit.__globals__['DAILY_LIMIT']}次)。請明天再試。")
        raise Exception("Rate limit exceeded") # This will stop the retry mechanism too

    try:
        response = client.chat.completions.create(**kwargs)
        return response
    except Exception as e:
        logger.error(f"OpenAI API request failed: {repr(e)}")
        st.warning(f"與 OpenAI 連線時發生暫時性錯誤，正在重試... ({repr(e)})")
        raise e # Reraise exception to trigger tenacity retry

def validate_master_key(input_key):
    """驗證提供的master key是否與環境變量中的相符"""
    if not master_key_env:
        logger.error("MASTER_KEY環境變量未設置")
        return False
    
    # 簡單的字符串比較，正式環境可能需要更複雜的驗證方法
    return input_key == master_key_env

def initialize_openai_client_with_master_key(master_key):
    """使用master key驗證並初始化OpenAI客戶端"""
    global client
    
    if not validate_master_key(master_key):
        logger.error("Invalid master key provided.")
        st.error("提供的管理金鑰無效。")
        client = None
        return False
    
    # 如果master key驗證成功，使用環境變量中的API key
    if api_key_env:
        client = OpenAI(api_key=api_key_env)
        logger.info("OpenAI client initialized successfully with environment API key.")
        return True
    else:
        logger.error("OPENAI_API_KEY environment variable not set.")
        st.error("系統錯誤：OpenAI API 金鑰未在環境變量中設置。請聯絡系統管理員。")
        client = None
        return False

# 保留原始方法以確保向後兼容，但內部改為使用新方法
def initialize_openai_client(api_key):
    """
    已棄用：直接使用API key初始化OpenAI客戶端
    現在轉為檢查此API key是否為有效的master key
    """
    global client
    logger.warning("使用舊方法initialize_openai_client進行客戶端初始化")
    return initialize_openai_client_with_master_key(api_key)

def get_openai_client():
    """Returns the initialized OpenAI client."""
    return client

def generate_response(system_prompt, user_prompt, model="gpt-4o-mini", temperature=0.7, max_tokens=1500):
    """
    Generates a response from OpenAI using the specified prompts and parameters.

    Args:
        system_prompt (str): The system message to guide the assistant.
        user_prompt (str): The user's message.
        model (str): The model to use (default: "gpt-4o-mini").
        temperature (float): Controls randomness (default: 0.7).
        max_tokens (int): Maximum number of tokens to generate (default: 1500).

    Returns:
        str: The generated response content, or None if an error occurs or client is not initialized.
    """
    if not client:
        logger.error("OpenAI client not initialized. Cannot generate response.")
        st.error("OpenAI client 未設置，請先在側邊欄輸入有效的管理金鑰。")
        return None

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    logger.info(f"Sending request to OpenAI model {model} with max_tokens={max_tokens}")
    
    try:
        # Use the retry wrapper function for the actual API call
        response = chat_completion_request_with_retry(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response_content = response.choices[0].message.content
        logger.info("Received response from OpenAI.")
        return response_content

    except Exception as e:
        # Handle rate limit exception if Option 2 was chosen in the wrapper
        if "Rate limit exceeded" in str(e): # str(e) here is for a specific string check, less likely to cause encoding error itself on common errors.
             logger.warning(f"Rate limit exceeded for IP (retrieved internally). User message already shown.")
             # Error message is already displayed by the wrapper via st.error
        else:
            logger.error(f"An unexpected error occurred during OpenAI API call: {repr(e)}")
            st.error(f"呼叫 OpenAI API 時發生錯誤: {repr(e)}")
        return None

def summarize_report_with_openai(report_markdown, api_key):
    """Attempts to summarize/reformat a report using OpenAI API."""
    # 檢查api_key是否是有效的master key
    global client
    original_client = client
    
    # 如果已通過驗證並設置了客戶端，則直接使用
    if not client and api_key:
        if not validate_master_key(api_key):
            logging.warning("提供的管理金鑰無效。跳過摘要處理。")
            return report_markdown
        elif not api_key_env:
            logging.warning("環境變量中未設置OPENAI_API_KEY。跳過摘要處理。")
            return report_markdown
        else:
            # 臨時初始化客戶端用於此次請求
            temp_client = OpenAI(api_key=api_key_env)
    else:
        # 使用已初始化的客戶端
        temp_client = client

    if temp_client is None:
        logging.warning("無法初始化OpenAI客戶端。跳過摘要處理。")
        return report_markdown

    ip_address = get_client_ip()
    if ip_address is None:
        st.error("IP 位址無法確定。為確保服務安全，API 請求無法處理。若在本機執行此為正常現象。")
        return report_markdown # Return original

    # Proceed with rate limiting only if IP is known
    if not check_rate_limit(ip_address):
        daily_limit = check_rate_limit.__globals__.get('DAILY_LIMIT', '每日')
        st.error(f"IP: {ip_address} - 抱歉，您今天的 API 使用次數已達整理報告文字的上限 ({daily_limit}次)。請明天再試。")
        return report_markdown

    try:
        system_prompt = """You are an assistant that reformats GMAT diagnostic reports. Use uniform heading 
levels: Level-2 headings for all major sections (## Section Title). Level-3 headings for subsections (### Su
bsection Title). Reformat content into clear Markdown tables where appropriate. Fix minor grammatical errors
 or awkward phrasing for readability. IMPORTANT: Do NOT add or remove any substantive information or conclus
ions. Only reformat and polish the existing text. Output strictly in Markdown format, without code blocks.
"""

        response = temp_client.chat.completions.create(
            model="gpt-4.1-nano", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": report_markdown}
            ],
        )
        summarized_report = response.choices[0].message.content
        if summarized_report and summarized_report.strip():
             logging.info(f"OpenAI summarization successful for report starting with: {report_markdown[:50]}\n...")
             return summarized_report.strip()
        else:
             logging.warning("OpenAI returned empty response. Using original report.")
             st.warning("AI 整理報告時返回了空內容，將使用原始報告。", icon="⚠️")
             return report_markdown

    except openai.AuthenticationError:
        st.warning("OpenAI API 驗證失敗，無法整理報告文字。請檢查系統管理員設定的API金鑰。", icon="🔑")
        logging.error("OpenAI AuthenticationError.")
        return report_markdown
    except openai.RateLimitError:
        st.warning("OpenAI API 請求頻率過高 (服務端限制)，請稍後再試。暫時使用原始報告文字。", icon="⏳")
        logging.error("OpenAI RateLimitError.")
        return report_markdown
    except openai.APIConnectionError as e:
        st.warning(f"無法連接至 OpenAI API ({repr(e)})，請檢查網路連線。暫時使用原始報告文字。", icon="🌐")
        logging.error(f"OpenAI APIConnectionError: {repr(e)}")
        return report_markdown
    except openai.APITimeoutError:
        st.warning("OpenAI API 請求超時。暫時使用原始報告文字。", icon="⏱️")
        logging.error("OpenAI APITimeoutError.")
        return report_markdown
    except openai.BadRequestError as e:
        st.warning(f"OpenAI API 請求無效 ({repr(e)})。可能是報告過長或格式問題。暫時使用原始報告文字。", icon="❗") 
        logging.error(f"OpenAI BadRequestError: {repr(e)}")
        return report_markdown
    except Exception as e:
        st.warning(f"調用 OpenAI API 整理報告時發生未知錯誤：{repr(e)}。暫時使用原始報告文字。", icon="⚠️")
        logging.error(f"Unknown OpenAI API error during summarization: {repr(e)}", exc_info=True)
        return report_markdown
    finally:
        # 確保全局客戶端狀態不受影響
        client = original_client

def generate_ai_consolidated_report(report_dict, api_key):
    """Generates a consolidated report of suggestions and next steps using OpenAI o4-mini."""
    # 檢查api_key是否是有效的master key
    global client
    original_client = client
    
    # 如果沒有報告資料，直接返回
    if not report_dict:
        logging.warning("Report dictionary is empty. Skipping consolidated report generation.")
        return None
    
    # 驗證master key並獲取有效的客戶端
    if not client and api_key:
        if not validate_master_key(api_key):
            logging.warning("提供的管理金鑰無效。跳過匯總報告生成。")
            return None
        elif not api_key_env:
            logging.warning("環境變量中未設置OPENAI_API_KEY。跳過匯總報告生成。")
            return None
        else:
            # 臨時初始化客戶端用於此次請求
            temp_client = openai.OpenAI(api_key=api_key_env)
    else:
        # 使用已初始化的客戶端
        temp_client = client

    if temp_client is None:
        logging.warning("無法初始化OpenAI客戶端。跳過匯總報告生成。")
        return None

    ip_address = get_client_ip()
    if ip_address is None:
        st.error("IP 位址無法確定。為確保服務安全，AI 匯總報告生成請求無法處理。若在本機執行此為正常現象。")
        return None

    if not check_rate_limit(ip_address):
        daily_limit = check_rate_limit.__globals__.get('DAILY_LIMIT', '每日')
        st.error(f"IP: {ip_address} - 抱歉，您今天的 API 使用次數已達生成匯總報告的上限 ({daily_limit}次)。請明天再試。")
        return None

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
Your task is to identify and extract ONLY the sections related to '{t('openai_practice_suggestion')}' (Practice Suggestions) and '{t('openai_subsequent_action')}' (Next Steps, including reflection and secondary evidence gathering) for each subject (Q, V, DI) from the provided text.

**CRITICAL INSTRUCTIONS:**
1.  **Strict Extraction:** Only extract text explicitly under '{t('openai_practice_suggestion')}' or '{t('openai_subsequent_action')}' headings or clearly discussing these topics.
2.  **Subject Separation:** Keep the extracted information strictly separated under standardized headings for each subject: "## Q 科目建議與行動", "## V 科目建議與行動", "## DI 科目建議與行動".
3.  **Complete Information:** Transfer ALL original text, data, details, parenthetical notes, specific question numbers, difficulty codes, time limits, percentages, scores, etc., accurately and completely. DO NOT SUMMARIZE OR OMIT ANY DETAILS.
4.  **Standardized Formatting:** Use Markdown format. Use Level-2 headings (##) for each subject as specified above. Use bullet points or numbered lists within each subject section as they appear in the original text, or to improve readability if appropriate, but maintain all original content.
5.  **No Additions:** Do not add any information, interpretation, or introductory/concluding text not present in the extracted sections.
6.  **Output Format:** Output only the consolidated Markdown report. Do not include any other text or commentary.
"""

    try:
        logging.info("Calling OpenAI responses.create with model o4-mini for consolidated report.")
        # WARNING: client.responses.create might be outdated. Consider migrating to chat.completions.create.
        response = temp_client.responses.create(
            model="o4-mini",
            input=f"""
System: {system_prompt}

User: 從以下 GMAT 診斷報告中提取練習建議和後續行動部分，按科目分類並整理成統一格式：

{full_report_text}
""",
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
            logging.error(f"OpenAI API error (consolidated report): {repr(error_details)}")
            st.warning(f"AI 生成匯總報告時出錯：{repr(error_details)}", icon="❗")
            return None
        else:
            logging.error(f"OpenAI consolidated report status not completed or output empty. Status: {response.status}")
            st.warning(f"AI 未能成功生成匯總報告（狀態：{response.status}）。", icon="⚠️")
            return None

    except openai.AuthenticationError:
        st.warning("OpenAI API 驗證失敗，無法生成匯總報告。請檢查系統管理員設定的API金鑰。", icon="🔑")
        logging.error("OpenAI AuthenticationError (consolidated report).")
        return None
    except openai.RateLimitError:
        st.warning("OpenAI API 請求頻率過高，無法生成匯總報告。", icon="⏳")
        logging.error("OpenAI RateLimitError (consolidated report).")
        return None
    except openai.APIConnectionError as e:
        st.warning(f"無法連接至 OpenAI API ({repr(e)})，無法生成匯總報告。", icon="🌐")
        logging.error(f"OpenAI APIConnectionError (consolidated report): {repr(e)}")
        return None
    except openai.APITimeoutError:
        st.warning("OpenAI API 請求超時，無法生成匯總報告。", icon="⏱️")
        logging.error("OpenAI APITimeoutError (consolidated report).")
        return None
    except openai.BadRequestError as e:
        st.warning(f"OpenAI API 請求無效 ({repr(e)})，無法生成匯總報告。", icon="❗")
        logging.error(f"OpenAI BadRequestError (consolidated report): {repr(e)}")
        return None
    except Exception as e:
        st.warning(f"生成 AI 匯總建議時發生未知錯誤：{repr(e)}", icon="⚠️")
        logging.error(f"Unknown error during consolidated report generation: {repr(e)}", exc_info=True)
        return None
    finally:
        # 確保全局客戶端狀態不受影響
        client = original_client

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
                    logging.error(f"無法導入或使用generate_new_diagnostic_report函數: {repr(ie)}")
        except Exception as e:
            logging.error(f"生成新診斷報告時出錯: {repr(e)}")
    
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
            df_context_str += f"\n... ({t('openai_showing_first')} {max_rows} {t('openai_rows_total')} {len(df_context)} {t('openai_rows')})"
        else:
            logging.info(f"轉換全部 {len(df_context)} 行數據為 markdown 格式")
            df_context_str = df_context.to_markdown(index=False)
        
        logging.info(f"成功轉換診斷試算表，輸出長度約 {len(df_context_str)} 字符")
        return df_context_str
    except Exception as e:
        error_msg = f"Error converting dataframe to markdown context: {repr(e)}"
        logging.error(error_msg, exc_info=True)
        return f"(無法轉換詳細數據表格: {repr(e)})"

def get_openai_response(current_chat_history, report_context, dataframe_context, api_key):
    """Get response from OpenAI based on chat history and context, using o4-mini."""
    # 檢查api_key是否是有效的master key
    global client
    original_client = client
    
    # 驗證master key並獲取有效的客戶端
    if not client and api_key:
        if not validate_master_key(api_key):
            logging.error("提供的管理金鑰無效。無法使用聊天功能。")
            return "錯誤：提供的管理金鑰無效。", None
        elif not api_key_env:
            logging.error("環境變量中未設置OPENAI_API_KEY。無法使用聊天功能。")
            return "錯誤：系統未配置OpenAI API金鑰。請聯絡系統管理員。", None
        else:
            # 臨時初始化客戶端用於此次請求
            temp_client = openai.OpenAI(api_key=api_key_env)
    else:
        # 使用已初始化的客戶端
        temp_client = client

    if temp_client is None:
        logging.error("無法初始化OpenAI客戶端。無法使用聊天功能。")
        return "錯誤：OpenAI客戶端初始化失敗。請確認管理金鑰和系統設置。", None

    ip_address = get_client_ip()
    if ip_address is None:
        st.error("IP 位址無法確定。為確保服務安全，聊天請求無法處理。若在本機執行此為正常現象。")
        return "錯誤：IP 位址無法確定，無法處理請求。", None

    if not check_rate_limit(ip_address):
        daily_limit = check_rate_limit.__globals__.get('DAILY_LIMIT', '每日')
        error_message = f"IP: {ip_address} - 抱歉，您今天的 API 使用次數已達聊天功能的上限 ({daily_limit}次)。請明天再試。"
        st.error(error_message)
        return error_message, None

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

        # WARNING: client.responses.create might be outdated. Consider migrating to chat.completions.create.
        response = temp_client.responses.create(
            model="o4-mini", 
            input=messages_for_api, 
            previous_response_id=previous_response_id,
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
            logging.error(f"OpenAI API error: {repr(error_details)}")
            return f"AI 服務出錯: {repr(error_details)}", None
        else:
            logging.error(f"OpenAI response status not completed or output empty. Status: {response.status}")
            return f"AI 未能成功回應 (狀態: {response.status})，請稍後再試。", None

    except openai.AuthenticationError:
        error_msg = "OpenAI API驗證失敗，請檢查系統管理員設定的API金鑰。"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.RateLimitError:
        error_msg = "OpenAI API請求頻率過高，請稍後再試"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.APIConnectionError as e:
        error_msg = f"連接OpenAI API時出錯: {repr(e)}"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.APITimeoutError:
        error_msg = "OpenAI API請求超時"
        logging.error(error_msg)
        return error_msg, None
        
    except openai.BadRequestError as e:
        error_msg = f"OpenAI API請求無效: {repr(e)}"
        logging.error(error_msg)
        return error_msg, None
        
    except Exception as e:
        error_msg = f"與OpenAI API通訊時發生未知錯誤: {repr(e)}"
        logging.error(error_msg, exc_info=True)
        return error_msg, None
    finally:
        # 確保全局客戶端狀態不受影響
        client = original_client

def trim_diagnostic_tags_with_openai(original_tags_str: str, user_description: str, api_key: str) -> str:
    """
    Uses OpenAI to suggest a trimmed list of 1-2 most relevant diagnostic tags
    based on original tags and user's description of their difficulty.

    Args:
        original_tags_str: A string containing the original diagnostic tags (e.g., comma-separated or list-like).
        user_description: User's description of their difficulty with the question.
        api_key: OpenAI API key or master key for authentication.

    Returns:
        A string containing the AI's suggested trimmed tags, or an error message.
    """
    # 檢查api_key是否是有效的master key
    global client
    original_client = client
    
    # 基本檢查
    if not original_tags_str.strip():
        return "錯誤：原始診斷標籤不能為空。"
    if not user_description.strip():
        return "錯誤：使用者描述不能為空。"
    
    # 修改驗證邏輯：如果api_key為空，直接使用環境變量的API key
    if not api_key:
        # 直接使用環境變量中的API key，無需master_key驗證
        if not api_key_env:
            logging.warning("環境變量中未設置OPENAI_API_KEY。無法執行標籤修剪。")
            return "錯誤：系統未配置OpenAI API金鑰。請聯絡系統管理員。"
        # 直接初始化客戶端用於此次請求
        temp_client = openai.OpenAI(api_key=api_key_env)
    else:
        # 如果提供了api_key，進行原有的master_key驗證邏輯
        if not client and api_key:
            if not validate_master_key(api_key):
                logging.warning("提供的管理金鑰無效。無法執行標籤修剪。")
                return "錯誤：提供的管理金鑰無效。"
            elif not api_key_env:
                logging.warning("環境變量中未設置OPENAI_API_KEY。無法執行標籤修剪。")
                return "錯誤：系統未配置OpenAI API金鑰。請聯絡系統管理員。"
            else:
                # 臨時初始化客戶端用於此次請求
                temp_client = openai.OpenAI(api_key=api_key_env)
        else:
            # 使用已初始化的客戶端
            temp_client = client

    if temp_client is None:
        logging.warning("無法初始化OpenAI客戶端。無法執行標籤修剪。")
        return "錯誤：OpenAI客戶端初始化失敗。請確認管理金鑰和系統設置。"
        
    ip_address = get_client_ip()
    if ip_address is None:
        st.error("IP 位址無法確定。為確保服務安全，修剪標籤請求無法處理。若在本機執行此為正常現象。")
        return "錯誤：IP 位址無法確定，無法處理請求。"

    if not check_rate_limit(ip_address):
        daily_limit = check_rate_limit.__globals__.get('DAILY_LIMIT', '每日')
        error_message = f"IP: {ip_address} - 抱歉，您今天的 API 使用次數已達修剪標籤功能的上限 ({daily_limit}次)。請明天再試。"
        st.error(error_message)
        return error_message

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
    
    user_content = f"{t('openai_original_diagnostic_tags')}：\n{original_tags_str}\n\n{t('openai_user_description')}：\n{user_description}"

    try:
        logging.info("Calling OpenAI ChatCompletion for tag trimming with model gpt-4.1-mini.")
        response = temp_client.chat.completions.create(
            model="gpt-4.1-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2, 
            max_tokens=100 
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
        return "錯誤：OpenAI API 驗證失敗。請檢查系統管理員設定的API金鑰。"
    except openai.RateLimitError:
        logging.error("OpenAI RateLimitError during tag trimming.")
        return "錯誤：OpenAI API 請求頻率過高，請稍後再試。"
    except openai.APIConnectionError as e:
        logging.error(f"OpenAI APIConnectionError during tag trimming: {repr(e)}")
        return f"錯誤：無法連接至 OpenAI API ({repr(e)})。"
    except openai.APITimeoutError:
        logging.error("OpenAI APITimeoutError during tag trimming.")
        return "錯誤：OpenAI API 請求超時。"
    except openai.BadRequestError as e:
        logging.error(f"OpenAI BadRequestError during tag trimming: {repr(e)}")
        return f"錯誤：OpenAI API 請求無效 ({repr(e)})。可能是輸入內容問題。"
    except Exception as e:
        logging.error(f"Unknown OpenAI API error during tag trimming: {repr(e)}", exc_info=True)
        return f"調用 OpenAI API 修剪標籤時發生未知錯誤：{repr(e)}。"
    finally:
        # 確保全局客戶端狀態不受影響
        client = original_client 