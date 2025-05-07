"""
聊天界面模組
提供AI聊天對話功能
"""

import streamlit as st
import logging
from gmat_diagnosis_app.services.openai_service import get_chat_context, get_openai_response

def display_chat_interface(session_state):
    """顯示聊天界面，處理訊息交換"""
    # Check conditions to show chat
    show_chat = check_chat_conditions(session_state)
    session_state.show_chat = show_chat

    if show_chat:
        st.subheader("💬 與 AI 對話 (基於本次報告)")
        
        # 確保聊天歷史存在
        if 'chat_history' not in session_state:
            session_state.chat_history = []
        
        # Debug: 顯示現有聊天歷史中的response_id (僅在調試時打開)
        # _debug_show_response_ids(session_state)
        
        # 添加自定義CSS，創建固定高度的聊天容器
        st.markdown("""
        <style>
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            background-color: #f8f9fa;
            margin-bottom: 15px;
        }
        .chat-container::-webkit-scrollbar {
            width: 6px;
            background-color: #F5F5F5;
        }
        .chat-container::-webkit-scrollbar-thumb {
            background-color: #CCCCCC;
            border-radius: 3px;
        }
        .stChatMessage {
            margin-bottom: 10px;
        }
        .chat-message-user {
            background-color: #e1f5fe;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 5px 0;
            max-width: 80%;
            margin-left: auto;
            text-align: right;
        }
        .chat-message-assistant {
            background-color: #f1f1f1;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 5px 0;
            max-width: 80%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 在固定容器中顯示聊天歷史
        with st.container():
            with st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True):
                # 使用streamlit的聊天元素顯示歷史聊天記錄
                display_chat_history(session_state)
            
            # 在聊天歷史加載後添加滾動腳本
            st.markdown("""
            <script>
                function scrollChatToBottom() {
                    const chatContainer = document.getElementById('chat-container');
                    if (chatContainer) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                }
                // 在完整加載後執行
                window.addEventListener('load', scrollChatToBottom);
                // 延遲執行以確保聊天內容已加載
                setTimeout(scrollChatToBottom, 500);
            </script>
            """, unsafe_allow_html=True)

        # 聊天輸入在固定容器下方
        handle_chat_input(session_state)
        
def _debug_show_response_ids(session_state):
    """顯示聊天歷史中的response_id（僅用於調試）"""
    if session_state.chat_history:
        debug_info = "聊天歷史中的response_ids:\n"
        for i, msg in enumerate(session_state.chat_history):
            if msg['role'] == 'assistant' and 'response_id' in msg:
                debug_info += f"{i}: {msg['response_id'][:10]}...\n"
        st.text(debug_info)
        
def check_chat_conditions(session_state):
    """檢查是否滿足顯示聊天的條件"""
    if session_state.openai_api_key and session_state.diagnosis_complete:
        return True
    return False

def display_chat_history(session_state):
    """顯示聊天歷史"""
    # 使用HTML實現自定義樣式的聊天氣泡
    for i, message in enumerate(session_state.chat_history):
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            st.markdown(f'<div class="chat-message-user">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message-assistant">{content}</div>', unsafe_allow_html=True)

def handle_chat_input(session_state):
    """處理用戶輸入和AI回應"""
    if prompt := st.chat_input("針對報告和數據提問..."):
        # 添加用戶消息到歷史
        session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 準備上下文並呼叫OpenAI
        with st.spinner("AI思考中..."):
            try:
                # 獲取上下文
                context = get_chat_context(session_state)
                
                # 呼叫OpenAI - 確保傳遞完整聊天歷史以獲取previous_response_id
                logging.info(f"準備調用OpenAI，聊天歷史長度: {len(session_state.chat_history)}")
                ai_response_text, response_id = get_openai_response(
                    session_state.chat_history,
                    context["report"],
                    context["dataframe"],
                    session_state.openai_api_key
                )
                
                # 明確記錄response_id的獲取
                logging.info(f"已獲得OpenAI回應，response_id: {response_id[:10]}... (長度:{len(response_id) if response_id else 0})")

                # 添加AI回應到歷史，確保包含response_id
                session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response_text,
                    "response_id": response_id  # 儲存ID用於下一次對話
                })
                
                # 使用JavaScript重新加載頁面以更新聊天並滾動到底部
                st.rerun()

            except Exception as e:
                error_message = f"呼叫 AI 時出錯: {e}"
                logging.error(f"OpenAI調用錯誤: {e}", exc_info=True)
                # 添加錯誤訊息到歷史，沒有response_id
                session_state.chat_history.append({"role": "assistant", "content": error_message})
                st.error(error_message)
                st.rerun() 