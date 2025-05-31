"""
Chat interface module
Provides AI chat conversation functionality
"""

import streamlit as st
import logging
from gmat_diagnosis_app.services.openai_service import get_chat_context, get_openai_response
from gmat_diagnosis_app.session_manager import ensure_chat_history_persistence
from gmat_diagnosis_app.i18n import translate as t

def display_chat_interface(session_state):
    """Display chat interface and handle message exchange"""
    # Ensure chat history persistence (called once at the beginning)
    ensure_chat_history_persistence()
    
    # Check conditions to show chat
    show_chat = check_chat_conditions(session_state)
    # session_state.show_chat = show_chat # This seems redundant if session_state is passed around directly

    if show_chat:
        st.subheader(t('chat_with_ai_title'))
        
        # Add prompt information to tell users what AI can answer
        info_text = t('chat_ai_capabilities_info')
        
        # If trimmed data exists, inform the user
        if hasattr(session_state, 'editable_diagnostic_df') and session_state.editable_diagnostic_df is not None:
            info_text += "\n" + t('chat_trimmed_data_notice')
        
        st.info(info_text)
        
        # Ensure chat history exists
        if 'chat_history' not in session_state:
            session_state.chat_history = []
            # logging.info("已初始化新的聊天歷史") # Replaced st.info with logging
        # else:
            # logging.info(f"當前聊天歷史包含 {len(session_state.chat_history)} 條消息") # Replaced st.info with logging
        
        # Debug: 顯示現有聊天歷史中的response_id (用於調試)
        # _debug_show_chat_history(session_state) # Removed the call to the debug function
        
        # 添加自定義CSS
        # We will rely on st.container(height=...) for scrolling and its border=True parameter.
        # Custom scrollbar styling might be added later if needed, targeting Streamlit's specific elements.
        st.markdown("""
        <style>
        /* Minimal styling for now, st.container with border=True will provide the main structure */
        /* We might need to adjust margins for st.chat_message if they are too tight within the container */
        /* Example: div[data-testid='stChatMessage'] { margin-bottom: 8px !important; } */

        /* Custom scrollbar styles (might need adjustment for Streamlit's specific container) */
        /* This targets any scrollable area, which might be too broad or not specific enough */
        /* Let's keep it commented for now to ensure basic functionality first */
        /*
        ::-webkit-scrollbar {
            width: 8px;
            background-color: #F5F5F5;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #AAAAAA;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: #777777;
        }
        */
        </style>
        """, unsafe_allow_html=True)
        
        # 在固定容器中顯示聊天歷史
        # Use st.container with a fixed height to make it scrollable
        # The border=True gives a visual boundary similar to the old CSS border.
        chat_display_area = st.container(height=800, border=True) # User previously set height to 1200px

        with chat_display_area:
            display_chat_history(session_state)
            
        # JavaScript自動滾動部分暫時移除，因為 target id "chat-container" 不再存在
        # 並且 st.container(height=...) 的內部滾動元素需要新的定位方式。
        # st.markdown(""" 
        # <script>
        #     function scrollChatToBottom() { ... }
        #     scrollChatToBottom();
        #     setTimeout(scrollChatToBottom, 100);
        #     setTimeout(scrollChatToBottom, 500);
        # </script>
        # """, unsafe_allow_html=True)

        # 聊天輸入在固定容器下方
        handle_chat_input(session_state)
        
def _debug_show_chat_history(session_state):
    """Display complete chat history information (for debugging only)"""
    with st.expander(t('chat_debug_history_title'), expanded=False):
        if session_state.chat_history:
            debug_info = t('chat_debug_history_label') + "\n"
            for i, msg in enumerate(session_state.chat_history):
                role = msg.get('role', 'unknown')
                content_preview = msg.get('content', '')[:30] + '...' if len(msg.get('content', '')) > 30 else msg.get('content', '')
                
                # Safely get response_id, ensure it's a string before len()
                response_id_val = msg.get('response_id') 
                response_id_display = 'N/A'
                if response_id_val is not None:
                    response_id_display = str(response_id_val) # Ensure it's a string
                    if len(response_id_display) > 10:
                        response_id_display = response_id_display[:10] + '...'
                
                debug_info += f"{i}: [{role}] {content_preview} (response_id: {response_id_display})\n"
            st.text(debug_info)
            
            # Display current context summary
            st.markdown("##### " + t('chat_debug_current_context'))
            try:
                context = get_chat_context(session_state)
                
                # Display data source information
                if hasattr(session_state, 'editable_diagnostic_df') and session_state.editable_diagnostic_df is not None:
                    st.success(t('chat_debug_using_trimmed_data'))
                else:
                    st.info(t('chat_debug_using_original_data'))
                
                # Display report summary
                if context["report"]:
                    report_preview = context["report"][:200] + "..." if len(context["report"]) > 200 else context["report"]
                    st.text(t('chat_debug_report_text').format(len(context['report'])) + f"\n{report_preview}")
                else:
                    st.text(t('chat_debug_no_report'))
                
                # Display diagnostic table summary
                if context["dataframe"] and context["dataframe"] != t('chat_debug_no_detailed_table'):
                    df_preview = context["dataframe"].split("\n")[:5]
                    df_preview = "\n".join(df_preview) + "\n..."
                    st.text(t('chat_debug_diagnostic_table').format(len(context['dataframe'])) + f"\n{df_preview}")
                else:
                    st.text(f"{t('chat_debug_diagnostic_table').format(0)}: {context['dataframe']}")
                    
                # New: Display statistics for wrong and invalid questions
                if "dataframe" in context and context["dataframe"] != t('chat_debug_no_detailed_table'):
                    st.markdown("##### " + t('chat_debug_data_statistics'))
                    lines = context["dataframe"].split("\n")
                    
                    # Debug: Display first few lines of data format for observation
                    if len(lines) > 5:
                        st.text(t('chat_debug_data_format_example'))
                        for i in range(min(3, len(lines))):
                            st.text(lines[i])
                    
                    # Use more flexible way to identify subjects
                    di_lines = [line for line in lines if " DI " in line or "|DI|" in line or "| DI|" in line or "|DI |" in line]
                    q_lines = [line for line in lines if " Q " in line or "|Q|" in line or "| Q|" in line or "|Q |" in line]
                    v_lines = [line for line in lines if " V " in line or "|V|" in line or "| V|" in line or "|V |" in line]
                    
                    # Display identified question counts for each subject
                    st.text(t('chat_debug_identified_rows').format(len(di_lines), len(q_lines), len(v_lines)))
                    
                    # Analyze DI section
                    di_total = len(di_lines)
                    di_invalid = len([line for line in di_lines if "Yes" in line and "is_invalid" in line])
                    di_valid = di_total - di_invalid
                    di_correct = len([line for line in di_lines if "Yes" in line and "is_correct" in line])
                    di_wrong = di_valid - di_correct
                    
                    # Analyze Q section
                    q_total = len(q_lines)
                    q_invalid = len([line for line in q_lines if "Yes" in line and "is_invalid" in line])
                    q_valid = q_total - q_invalid
                    q_correct = len([line for line in q_lines if "Yes" in line and "is_correct" in line])
                    q_wrong = q_valid - q_correct
                    
                    # Analyze V section
                    v_total = len(v_lines)
                    v_invalid = len([line for line in v_lines if "Yes" in line and "is_invalid" in line])
                    v_valid = v_total - v_invalid
                    v_correct = len([line for line in v_lines if "Yes" in line and "is_correct" in line])
                    v_wrong = v_valid - v_correct
                    
                    # Display statistics
                    st.text(t('chat_debug_di_stats').format(di_total, di_valid, di_invalid, di_correct, di_wrong))
                    st.text(t('chat_debug_q_stats').format(q_total, q_valid, q_invalid, q_correct, q_wrong))
                    st.text(t('chat_debug_v_stats').format(v_total, v_valid, v_invalid, v_correct, v_wrong))
            except Exception as e:
                st.text(t('chat_debug_context_error').format(e))
        else:
            st.text(t('chat_debug_no_history'))
        
def check_chat_conditions(session_state):
    """檢查是否滿足顯示聊天的條件"""
    if session_state.master_key and session_state.diagnosis_complete:
        return True
    return False

def display_chat_history(session_state):
    """顯示聊天歷史"""
    # 使用 Streamlit 原生的 st.chat_message
    for i, message in enumerate(session_state.chat_history):
        role = message["role"]
        content = message["content"]
        
        with st.chat_message(role):
            st.markdown(content) # Use markdown for potential formatting in content

def handle_chat_input(session_state):
    """Handle user input and AI response"""
    if prompt := st.chat_input(t('chat_input_placeholder')):
        # Add user message to history
        session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Debug output
        # logging.info(f"添加用戶消息後歷史長度: {len(session_state.chat_history)}") # Replaced st.info with logging
        
        # Prepare context and call OpenAI
        with st.spinner(t('chat_ai_thinking')):
            try:
                # Get context
                context = get_chat_context(session_state)
                
                # Display debug information
                # logging.info(f"發送至API的聊天歷史長度: {len(session_state.chat_history)}") # Replaced st.info with logging
                
                # Call OpenAI - ensure passing complete chat history to get previous_response_id
                logging.info(f"準備調用OpenAI，聊天歷史長度: {len(session_state.chat_history)}")
                ai_response_text, response_id = get_openai_response(
                    session_state.chat_history, # Pass the current history directly
                    context["report"],
                    context["dataframe"],
                    session_state.master_key
                )
                
                # Explicitly record response_id acquisition
                logging.info(f"已獲得OpenAI回應，response_id: {response_id[:10] if response_id else 'N/A'}... (長度:{len(response_id) if response_id else 0})")
                st.success(t('chat_response_generated').format(response_id[:8] if response_id else 'N/A'))

                # Add AI response to history, ensure including response_id
                session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response_text,
                    "response_id": response_id  # Store ID for next conversation
                })
                
                # Display updated chat history length
                # logging.info(f"更新後的聊天歷史長度: {len(session_state.chat_history)}") # Replaced st.info with logging
                
                # st.session_state will automatically save, no need to manually assign back to st.session_state.chat_history = session_state.chat_history
                # unless session_state is not a direct reference to st.session_state
                
                # Use JavaScript to reload page to update chat and scroll to bottom
                st.rerun()

            except Exception as e:
                error_message = t('chat_api_error').format(e)
                logging.error(f"OpenAI調用錯誤: {e}", exc_info=True)
                # Add error message to history, no response_id
                session_state.chat_history.append({"role": "assistant", "content": error_message})
                                
                st.error(error_message)
                st.rerun()
                
    # No longer need to call ensure_chat_history_persistence() at the end because rerun will call it at the beginning of display_chat_interface
    # ensure_chat_history_persistence() 