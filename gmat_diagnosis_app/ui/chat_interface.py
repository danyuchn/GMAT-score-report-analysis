"""
聊天界面模組
提供AI聊天對話功能
"""

import streamlit as st
from gmat_diagnosis_app.services.openai_service import get_chat_context, get_openai_response

def display_chat_interface(session_state):
    """顯示聊天界面，處理訊息交換"""
    st.divider()

    # Check conditions to show chat
    show_chat = check_chat_conditions(session_state)
    session_state.show_chat = show_chat

    if show_chat:
        st.header("💬 與 AI 對話 (基於本次報告)")

        # Display chat history
        display_chat_history(session_state)

        # Chat input at the bottom of the main page
        handle_chat_input(session_state)
        
def check_chat_conditions(session_state):
    """檢查是否滿足顯示聊天的條件"""
    if session_state.openai_api_key and session_state.diagnosis_complete:
        return True
    return False

def display_chat_history(session_state):
    """顯示聊天歷史"""
    for message in session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_chat_input(session_state):
    """處理用戶輸入和AI回應"""
    if prompt := st.chat_input("針對報告和數據提問..."):
        # Add user message to history and display
        session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare context and call OpenAI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()  # Placeholder for streaming or waiting message
            message_placeholder.markdown("思考中...")
            try:
                # Get context
                context = get_chat_context(session_state)
                
                # Call OpenAI
                ai_response_text, response_id = get_openai_response(
                    session_state.chat_history,
                    context["report"],
                    context["dataframe"],
                    session_state.openai_api_key
                )

                # Display AI response and add to history with response_id
                message_placeholder.markdown(ai_response_text)
                session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response_text,
                    "response_id": response_id  # Store the ID for the next turn
                })

            except Exception as e:
                error_message = f"呼叫 AI 時出錯: {e}"
                message_placeholder.error(error_message)
                # Add error message to history, without a response_id
                session_state.chat_history.append({"role": "assistant", "content": error_message}) 