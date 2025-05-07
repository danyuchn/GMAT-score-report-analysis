"""
聊天界面模組
提供AI聊天對話功能
"""

import streamlit as st
import logging
from gmat_diagnosis_app.services.openai_service import get_chat_context, get_openai_response
from gmat_diagnosis_app.session_manager import ensure_chat_history_persistence

def display_chat_interface(session_state):
    """顯示聊天界面，處理訊息交換"""
    # 確保聊天歷史持久化
    ensure_chat_history_persistence()
    
    # Check conditions to show chat
    show_chat = check_chat_conditions(session_state)
    session_state.show_chat = show_chat

    if show_chat:
        st.subheader("💬 與 AI 對話 (基於本次報告)")
        
        # 添加提示信息，告知用戶 AI 可以回答的內容
        st.info("""
        AI 助手可以回答有關您的診斷報告和測試數據的問題。您可以詢問：
        - 關於報告中具體內容的解釋
        - 關於診斷試算表中的數據分析
        - 特定題型或難度的表現
        - 時間分配和準確率的問題
        """)
        
        # 確保聊天歷史存在
        if 'chat_history' not in session_state:
            session_state.chat_history = []
            st.info("已初始化新的聊天歷史")
        else:
            st.info(f"當前聊天歷史包含 {len(session_state.chat_history)} 條消息")
        
        # Debug: 顯示現有聊天歷史中的response_id (用於調試)
        _debug_show_chat_history(session_state)
        
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
        
def _debug_show_chat_history(session_state):
    """顯示完整的聊天歷史信息（僅用於調試）"""
    with st.expander("顯示聊天歷史調試信息", expanded=True):
        if session_state.chat_history:
            debug_info = "聊天歷史:\n"
            for i, msg in enumerate(session_state.chat_history):
                role = msg.get('role', 'unknown')
                content_preview = msg.get('content', '')[:30] + '...' if len(msg.get('content', '')) > 30 else msg.get('content', '')
                response_id = msg.get('response_id', 'N/A')
                if response_id != 'N/A' and len(response_id) > 10:
                    response_id = response_id[:10] + '...'
                debug_info += f"{i}: [{role}] {content_preview} (response_id: {response_id})\n"
            st.text(debug_info)
            
            # 顯示當前上下文摘要
            st.markdown("##### 當前聊天上下文摘要")
            try:
                context = get_chat_context(session_state)
                
                # 顯示報告摘要
                if context["report"]:
                    report_preview = context["report"][:200] + "..." if len(context["report"]) > 200 else context["report"]
                    st.text(f"報告文字 ({len(context['report'])} 字符):\n{report_preview}")
                else:
                    st.text("沒有報告文字")
                
                # 顯示診斷試算表摘要
                if context["dataframe"] and context["dataframe"] != "(無詳細數據表格)":
                    df_preview = context["dataframe"].split("\n")[:5]
                    df_preview = "\n".join(df_preview) + "\n..."
                    st.text(f"診斷試算表 ({len(context['dataframe'])} 字符):\n{df_preview}")
                else:
                    st.text(f"診斷試算表: {context['dataframe']}")
                    
                # 新增：顯示錯題和無效題的統計信息
                if "dataframe" in context and context["dataframe"] != "(無詳細數據表格)":
                    st.markdown("##### 數據統計")
                    lines = context["dataframe"].split("\n")
                    di_lines = [line for line in lines if "| DI " in line]
                    q_lines = [line for line in lines if "| Q " in line]
                    v_lines = [line for line in lines if "| V " in line]
                    
                    # 分析 DI 部分
                    di_total = len(di_lines)
                    di_invalid = len([line for line in di_lines if "| True " in line[:20]])
                    di_valid = di_total - di_invalid
                    di_correct = len([line for line in di_lines if "| False " in line[:20] and "| True " in line[20:30]])
                    di_wrong = di_valid - di_correct
                    
                    # 分析 Q 部分
                    q_total = len(q_lines)
                    q_invalid = len([line for line in q_lines if "| True " in line[:20]])
                    q_valid = q_total - q_invalid
                    q_correct = len([line for line in q_lines if "| False " in line[:20] and "| True " in line[20:30]])
                    q_wrong = q_valid - q_correct
                    
                    # 分析 V 部分
                    v_total = len(v_lines)
                    v_invalid = len([line for line in v_lines if "| True " in line[:20]])
                    v_valid = v_total - v_invalid
                    v_correct = len([line for line in v_lines if "| False " in line[:20] and "| True " in line[20:30]])
                    v_wrong = v_valid - v_correct
                    
                    # 顯示統計
                    st.text(f"DI: 總題數={di_total}, 有效題數={di_valid}, 無效題數={di_invalid}, 答對={di_correct}, 答錯={di_wrong}")
                    st.text(f"Q:  總題數={q_total}, 有效題數={q_valid}, 無效題數={q_invalid}, 答對={q_correct}, 答錯={q_wrong}")
                    st.text(f"V:  總題數={v_total}, 有效題數={v_valid}, 無效題數={v_invalid}, 答對={v_correct}, 答錯={v_wrong}")
            except Exception as e:
                st.text(f"無法獲取上下文摘要: {e}")
        else:
            st.text("目前沒有聊天歷史記錄")
        
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
        # 添加用戶消息到歷史前先備份
        current_history = session_state.chat_history.copy()
        
        # 添加用戶消息到歷史
        session_state.chat_history.append({"role": "user", "content": prompt})
        
        # 更新備份
        if hasattr(st.session_state, 'chat_history_backup'):
            st.session_state.chat_history_backup = session_state.chat_history.copy()
        
        # 調試輸出
        st.info(f"添加用戶消息前歷史長度: {len(current_history)}")
        st.info(f"添加用戶消息後歷史長度: {len(session_state.chat_history)}")
        
        # 準備上下文並呼叫OpenAI
        with st.spinner("AI思考中..."):
            try:
                # 獲取上下文
                context = get_chat_context(session_state)
                
                # 顯示調試信息
                st.info(f"發送至API的聊天歷史長度: {len(session_state.chat_history)}")
                
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
                st.success(f"AI回應已生成，ID: {response_id[:8]}...")

                # 添加AI回應到歷史，確保包含response_id
                session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response_text,
                    "response_id": response_id  # 儲存ID用於下一次對話
                })
                
                # 再次更新備份
                if hasattr(st.session_state, 'chat_history_backup'):
                    st.session_state.chat_history_backup = session_state.chat_history.copy()
                
                # 顯示更新後的聊天歷史長度
                st.info(f"更新後的聊天歷史長度: {len(session_state.chat_history)}")
                
                # 確保聊天歷史在會話狀態中直接更新
                st.session_state.chat_history = session_state.chat_history
                
                # 使用JavaScript重新加載頁面以更新聊天並滾動到底部
                st.rerun()

            except Exception as e:
                error_message = f"呼叫 AI 時出錯: {e}"
                logging.error(f"OpenAI調用錯誤: {e}", exc_info=True)
                # 添加錯誤訊息到歷史，沒有response_id
                session_state.chat_history.append({"role": "assistant", "content": error_message})
                
                # 確保聊天歷史在會話狀態中直接更新
                st.session_state.chat_history = session_state.chat_history
                
                # 更新備份
                if hasattr(st.session_state, 'chat_history_backup'):
                    st.session_state.chat_history_backup = session_state.chat_history.copy()
                
                st.error(error_message)
                st.rerun()
                
    # 確保每次執行時都檢查並保存聊天歷史
    ensure_chat_history_persistence() 