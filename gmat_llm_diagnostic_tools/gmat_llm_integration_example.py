#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT LLM Integration Example
GMAT LLM 整合範例

This script demonstrates how to integrate the GMAT study planner 
with LLM models using function calling.
"""

import json
import os
from typing import Dict, List, Any
from gmat_llm_function_handler import (
    create_function_definitions, 
    generate_gmat_study_plan, 
    validate_user_input, 
    get_input_schema
)

# Try to import OpenAI with proper version handling
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("警告: OpenAI 套件未安裝。請執行 'pip install openai' 來安裝。")

# Function definitions for OpenAI function calling
FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "generate_gmat_study_plan",
            "description": """根據學生的個人情況生成完整的 GMAT 學習計劃，包括考試週期建議、學習策略、時間分配等。

必須使用以下確切的 JSON 欄位名稱：
- target_gmat_score: 目標分數 (200-805)
- target_score_system: 分數制度 ("Old" 或 "New")  
- current_highest_gmat_score: 目前最高分數 (200-805)
- application_deadline: 申請截止日期 (YYYY-MM-DD 格式)
- language_test_status: 語言考試狀態
- application_materials_progress: 申請資料完成度 (0-100)
- study_status: 備考身份 
- weekday_study_hours: 平日每日學習時數
- weekend_study_hours: 假日每日學習時數
- current_section_scores: 包含 Quantitative、Verbal、Data Insights 的物件""",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_gmat_score": {"type": "integer", "minimum": 200, "maximum": 805},
                    "target_score_system": {"type": "string", "enum": ["Old", "New"]},
                    "current_highest_gmat_score": {"type": "integer", "minimum": 200, "maximum": 805},
                    "application_deadline": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                    "language_test_status": {"type": "string"},
                    "application_materials_progress": {"type": "number", "minimum": 0, "maximum": 100},
                    "study_status": {"type": "string"},
                    "weekday_study_hours": {"type": "number", "minimum": 0},
                    "weekend_study_hours": {"type": "number", "minimum": 0},
                    "current_section_scores": {
                        "type": "object",
                        "properties": {
                            "Quantitative": {"type": "integer", "minimum": 60, "maximum": 90},
                            "Verbal": {"type": "integer", "minimum": 60, "maximum": 90},
                            "Data Insights": {"type": "integer", "minimum": 60, "maximum": 90}
                        },
                        "required": ["Quantitative", "Verbal", "Data Insights"]
                    }
                },
                "required": [
                    "target_gmat_score", "target_score_system", "current_highest_gmat_score",
                    "application_deadline", "language_test_status", "application_materials_progress",
                    "study_status", "weekday_study_hours", "weekend_study_hours", "current_section_scores"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "validate_user_input",
            "description": """驗證用戶輸入的數據格式和內容是否正確，在生成學習計劃前使用。

確保 JSON 包含以下確切欄位名稱：
target_gmat_score, target_score_system, current_highest_gmat_score, 
application_deadline, language_test_status, application_materials_progress,
study_status, weekday_study_hours, weekend_study_hours, current_section_scores""",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_gmat_score": {"type": "integer", "minimum": 200, "maximum": 805},
                    "target_score_system": {"type": "string", "enum": ["Old", "New"]},
                    "current_highest_gmat_score": {"type": "integer", "minimum": 200, "maximum": 805},
                    "application_deadline": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                    "language_test_status": {"type": "string"},
                    "application_materials_progress": {"type": "number", "minimum": 0, "maximum": 100},
                    "study_status": {"type": "string"},
                    "weekday_study_hours": {"type": "number", "minimum": 0},
                    "weekend_study_hours": {"type": "number", "minimum": 0},
                    "current_section_scores": {
                        "type": "object",
                        "properties": {
                            "Quantitative": {"type": "integer", "minimum": 60, "maximum": 90},
                            "Verbal": {"type": "integer", "minimum": 60, "maximum": 90},
                            "Data Insights": {"type": "integer", "minimum": 60, "maximum": 90}
                        },
                        "required": ["Quantitative", "Verbal", "Data Insights"]
                    }
                },
                "required": [
                    "target_gmat_score", "target_score_system", "current_highest_gmat_score",
                    "application_deadline", "language_test_status", "application_materials_progress",
                    "study_status", "weekday_study_hours", "weekend_study_hours", "current_section_scores"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_input_schema",
            "description": "獲取輸入數據的預期格式和結構資訊，幫助 LLM 了解需要收集哪些資訊以及確切的欄位名稱",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Available functions mapping with wrapper functions to handle direct object parameters
def _validate_user_input_wrapper(**kwargs):
    """Wrapper for validate_user_input to handle direct object parameters"""
    import json
    return validate_user_input(json.dumps(kwargs, ensure_ascii=False))

def _generate_gmat_study_plan_wrapper(**kwargs):
    """Wrapper for generate_gmat_study_plan to handle direct object parameters"""
    import json
    return generate_gmat_study_plan(json.dumps(kwargs, ensure_ascii=False))

AVAILABLE_FUNCTIONS = {
    "generate_gmat_study_plan": _generate_gmat_study_plan_wrapper,
    "validate_user_input": _validate_user_input_wrapper,
    "get_input_schema": get_input_schema
}

# System prompt for GMAT advisor
SYSTEM_PROMPT = """
你是一位專業的 GMAT 學習規劃顧問，擁有豐富的 GMAT 考試指導經驗。

## 核心規則：必須使用 Function Calling
🚨 **重要**：你不能憑自己的知識提供 GMAT 建議。你只能通過 function calling 使用專業系統來生成計劃。
🚨 **禁止**：不可以直接給出學習建議、時間分配、科目重點等內容。
🚨 **必須**：所有分析和建議都必須來自 function calling 的結果。

## 你的任務
1. 透過友善對話收集學生的完整背景資料
2. 使用 validate_user_input() 驗證資料
3. 使用 generate_gmat_study_plan() 生成個性化的 GMAT 學習計劃
4. 將 function calling 的技術分析結果轉化為易懂的學習建議

## 需要收集的資訊
- 目標 GMAT 分數 (200-805)
- 分數制度 (舊制 Old / 新制 New)
- 目前最高 GMAT 分數 (200-805)
- 各科目積分：Quantitative、Verbal、Data Insights (60-90)
- 申請截止日期 (YYYY-MM-DD)
- 語言考試狀態 (已完成/未完成)
- 申請資料完成度 (0-100%)
- 備考身份 (全職考生/在職考生)
- 平日每日學習時數
- 假日每日學習時數

## 重要：JSON 格式要求
當調用函數時，必須使用以下確切的欄位名稱：

```json
{
  "target_gmat_score": 700,                    // 目標分數
  "target_score_system": "New",               // 分數制度，必須是 "Old" 或 "New"
  "current_highest_gmat_score": 600,          // 目前最高分數
  "application_deadline": "2025-12-01",       // 申請截止日期，格式：YYYY-MM-DD
  "language_test_status": "已完成",           // 語言考試狀態
  "application_materials_progress": 50,        // 申請資料完成度 (0-100)
  "study_status": "在職考生",                 // 備考身份
  "weekday_study_hours": 3,                   // 平日每日學習時數
  "weekend_study_hours": 8,                   // 假日每日學習時數
  "current_section_scores": {                 // 各科目積分
    "Quantitative": 75,                       // 數學積分 (60-90)
    "Verbal": 70,                            // 語文積分 (60-90)
    "Data Insights": 72                      // 數據洞察積分 (60-90)
  }
}
```

## 對話原則
- 使用溫暖、專業的語調
- 逐步收集資訊，避免一次問太多問題
- 在生成計劃前先驗證資料完整性
- 客製化解釋 function calling 的分析結果，提供具體可行的執行指導
- 收集完資料後，務必按照上述確切的 JSON 格式調用函數

## Function Calling 強制流程
1. 初次對話：調用 get_input_schema() 了解資料格式
2. 資料收集完成：調用 validate_user_input() 驗證資料
3. **驗證通過後：立即自動調用 generate_gmat_study_plan()，無例外**
4. **必須等待函數結果，然後基於結果提供解釋**

## 強制執行規則
- 當 validate_user_input() 返回 success: true 時，**立即調用 generate_gmat_study_plan()**
- 詢問用戶是否已經準備好看結果，請用戶回覆「確認」以檢視結果。
- **絕對不要**提供自己的建議，如"建議加強閱讀理解"、"平日專注於弱項"等
- **必須等待** generate_gmat_study_plan() 的結果，然後解釋其內容
- 如果 function calling 失敗，告訴用戶系統錯誤，不要提供替代建議

## 注意事項
- 分數制度：只能使用 "Old" 或 "New"，不能用其他變體
- 日期格式：必須是 YYYY-MM-DD 格式
- 各科積分：必須放在 current_section_scores 物件內
- 所有欄位名稱必須完全匹配上述範例
"""


class GMATLLMAdvisor:
    """
    GMAT LLM Advisor with Function Calling Integration
    整合 Function Calling 的 GMAT LLM 顧問
    """
    
    def __init__(self, api_key: str = None, model: str = "gpt-4.1-mini", timeout: int = 30):
        """
        Initialize the GMAT LLM Advisor
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: OpenAI model to use
            timeout: Request timeout in seconds
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 套件未安裝。請執行 'pip install openai' 來安裝。")
        
        # Initialize OpenAI client with timeout
        if api_key:
            self.client = OpenAI(api_key=api_key, timeout=timeout)
        else:
            # Will use OPENAI_API_KEY environment variable
            self.client = OpenAI(timeout=timeout)
        
        self.model = model
        self.timeout = timeout
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    def chat(self, user_message: str, max_retries: int = 2) -> str:
        """
        Process user message and return response with function calling support
        
        Args:
            user_message: User's message
            max_retries: Maximum number of retries for failed requests
            
        Returns:
            Assistant's response
        """
        # Add user message to conversation
        self.conversation_history.append({"role": "user", "content": user_message})
        
        for attempt in range(max_retries + 1):
            try:
                # Call OpenAI API with function calling
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=FUNCTION_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    timeout=self.timeout
                )
                
                message = response.choices[0].message
                
                # Check if function calling is needed
                if message.tool_calls:
                    # Add assistant message with tool calls to conversation
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": message.tool_calls
                    })
                    
                    # Process each tool call
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        
                        print(f"🔧 調用函數: {function_name}")
                        
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                            print(f"📝 參數: {function_args}")
                            
                            # Execute function
                            if function_name in AVAILABLE_FUNCTIONS:
                                function_result = AVAILABLE_FUNCTIONS[function_name](**function_args)
                                
                                # Add successful function result to conversation
                                self.conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": function_result
                                })
                            else:
                                error_msg = f"未知函數: {function_name}"
                                self.conversation_history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": error_msg
                                })
                                
                        except json.JSONDecodeError as json_err:
                            error_msg = f"函數參數 JSON 解析錯誤: {str(json_err)}"
                            print(f"❌ {error_msg}")
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_msg
                            })
                            
                        except TypeError as type_err:
                            error_msg = f"函數調用參數錯誤: {str(type_err)}"
                            print(f"❌ {error_msg}")
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_msg
                            })
                            
                        except Exception as func_err:
                            error_msg = f"函數執行錯誤: {str(func_err)}"
                            print(f"❌ {error_msg}")
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_msg
                            })
                    
                    # Get final response from LLM
                    try:
                        final_response = self.client.chat.completions.create(
                            model=self.model,
                            messages=self.conversation_history,
                            temperature=0.7,
                            timeout=self.timeout
                        )
                        
                        final_message = final_response.choices[0].message.content
                        self.conversation_history.append({"role": "assistant", "content": final_message})
                        
                        return final_message
                    except Exception as final_e:
                        error_msg = f"Function calling 執行成功，但生成最終回應時發生錯誤: {str(final_e)}"
                        self.conversation_history.append({"role": "assistant", "content": error_msg})
                        return error_msg
                else:
                    # Regular response without function calling
                    assistant_message = message.content
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
                    
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Classify error types
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    if attempt < max_retries:
                        print(f"⏱️ 請求超時 (嘗試 {attempt + 1}/{max_retries + 1})，正在重試...")
                        continue
                    else:
                        final_error = "😅 抱歉，API 回應較慢。請稍後再試，或嘗試簡化您的問題。"
                elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                    if attempt < max_retries:
                        print(f"🚦 API 使用頻率限制 (嘗試 {attempt + 1}/{max_retries + 1})，等待後重試...")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        final_error = "🚦 API 使用頻率過高，請稍後再試。"
                elif "authentication" in error_msg.lower() or "api" in error_msg.lower() and "key" in error_msg.lower():
                    final_error = "🔑 API Key 錯誤，請檢查 OPENAI_API_KEY 環境變數設置。"
                    break  # No point retrying for auth errors
                elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                    if attempt < max_retries:
                        print(f"🌐 網路連接問題 (嘗試 {attempt + 1}/{max_retries + 1})，正在重試...")
                        continue
                    else:
                        final_error = "🌐 網路連接問題，請檢查網路狀態後重試。"
                else:
                    if attempt < max_retries:
                        print(f"⚠️ 未知錯誤 (嘗試 {attempt + 1}/{max_retries + 1}): {error_type}")
                        continue
                    else:
                        final_error = f"⚠️ 處理請求時發生錯誤 ({error_type}): {error_msg}"
                
                # If we've exhausted retries, return the final error
                self.conversation_history.append({"role": "assistant", "content": final_error})
                return final_error
        
        # This should never be reached, but just in case
        fallback_error = "😅 抱歉，系統暫時無法處理您的請求，請稍後再試。"
        self.conversation_history.append({"role": "assistant", "content": fallback_error})
        return fallback_error
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        print("🔄 對話已重置")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get current conversation history"""
        return self.conversation_history.copy()


def demo_conversation():
    """
    Demonstrate a complete GMAT planning conversation
    示範完整的 GMAT 規劃對話
    """
    print("=" * 60)
    print("GMAT LLM 整合示範 (Demo Mode)")
    print("=" * 60)
    print("注意：這是示範模式，使用模擬回應而非真實 API 調用")
    print()
    
    # 示範資料收集流程
    demo_messages = [
        "您好，我想制定一個 GMAT 學習計劃",
        "我的目標分數是 700 分，是新制的",
        "我目前的最高分數是 600 分",
        "各科積分：數學 75 分，語文 70 分，數據洞察 72 分",
        "申請截止日期是 2025-12-01，語言考試已完成，申請資料完成了 50%",
        "我是在職考生，平日每天可以學習 3 小時，假日 8 小時"
    ]
    
    # 模擬收集到的用戶資料
    user_data = {
        "target_gmat_score": 700,
        "target_score_system": "New",
        "current_highest_gmat_score": 600,
        "application_deadline": "2025-12-01",
        "language_test_status": "已完成",
        "application_materials_progress": 50,
        "study_status": "在職考生",
        "weekday_study_hours": 3,
        "weekend_study_hours": 8,
        "current_section_scores": {
            "Quantitative": 75,
            "Verbal": 70,
            "Data Insights": 72
        }
    }
    
    print("📋 收集到的用戶資料:")
    print(json.dumps(user_data, ensure_ascii=False, indent=2))
    print()
    
    print("🔧 調用 validate_user_input 驗證資料...")
    validation_result = validate_user_input(json.dumps(user_data, ensure_ascii=False))
    print("✅ 驗證結果:", "通過" if "success" in validation_result and "true" in validation_result.lower() else "失敗")
    print()
    
    print("🔧 調用 generate_gmat_study_plan 生成學習計劃...")
    study_plan = generate_gmat_study_plan(json.dumps(user_data, ensure_ascii=False))
    
    # 解析並格式化輸出
    try:
        plan_data = json.loads(study_plan)
        if plan_data.get("success"):
            print("📊 **您的 GMAT 學習計劃分析完成！**")
            print()
            
            analysis = plan_data["study_plan"]["analysis"]
            print("### 🎯 核心分析")
            print(f"- {analysis['score_gap']}")
            print(f"- {analysis['schedule_sufficiency']}")
            print(f"- {analysis['time_sufficiency']}")
            print(f"- 所需積分提升: {analysis['required_improvement']}")
            print(f"- 可用準備天數: {analysis['available_days']}")
            print(f"- 每週學習時數: {analysis['weekly_hours']}")
            print()
            
            print(f"### 📅 建議考試週期: {plan_data['study_plan']['exam_cycle']}")
            print()
            
            print("### 📚 學習策略重點")
            strategy_lines = plan_data['study_plan']['study_strategy'].split('\n')
            for line in strategy_lines:
                if line.strip():
                    print(f"  {line.strip()}")
            print()
            
            print("### ⏰ 時間分配建議")
            allocation_lines = plan_data['study_plan']['section_time_allocation'].split('\n')
            for line in allocation_lines:
                if line.strip():
                    print(f"  {line.strip()}")
            print()
            
            print("### ⚡ 實際學習時間分配")
            actual_lines = plan_data['study_plan']['actual_time_allocation'].split('\n')
            for line in actual_lines:
                if line.strip():
                    print(f"  {line.strip()}")
            
        else:
            print(f"❌ 計劃生成失敗: {plan_data.get('error', '未知錯誤')}")
            
    except json.JSONDecodeError:
        print("❌ 無法解析學習計劃結果")
    
    print()
    print("=" * 60)
    print("示範完成")


def interactive_mode():
    """
    Interactive mode for testing with real OpenAI API
    互動模式，用於真實 OpenAI API 測試
    """
    print("=" * 60)
    print("GMAT LLM 互動模式")
    print("=" * 60)
    print("請確保已設置 OPENAI_API_KEY 環境變數")
    print("輸入 'quit' 退出，'reset' 重置對話，'test' 測試連接")
    print()
    
    # Check if API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 錯誤: 未找到 OPENAI_API_KEY 環境變數")
        print("請設置您的 OpenAI API Key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # 初始化顧問，使用較短的超時時間避免長時間等待
        advisor = GMATLLMAdvisor(timeout=20)
        
        # 測試 API 連接
        print("🔧 正在測試 API 連接...")
        test_response = advisor.chat("Hello", max_retries=1)
        if "錯誤" in test_response or "Error" in test_response:
            print(f"⚠️ API 連接測試失敗: {test_response}")
            print("建議：")
            print("1. 檢查網路連接")
            print("2. 確認 API Key 正確")
            print("3. 稍後再試")
            return
        else:
            print("✅ API 連接測試成功")
            # 重置對話以清除測試訊息
            advisor.reset_conversation()
        
        print("🤖 GMAT 顧問: 您好！我是您的 GMAT 學習規劃顧問。我將協助您制定個性化的 GMAT 學習計劃。")
        print("首先，請告訴我您的目標 GMAT 分數是多少？(範圍：200-805)")
        print()
        
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while True:
            try:
                user_input = input("👤 您: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 再見！祝您 GMAT 準備順利！")
                    break
                elif user_input.lower() == 'reset':
                    advisor.reset_conversation()
                    consecutive_errors = 0  # Reset error count
                    print("🤖 GMAT 顧問: 對話已重置。讓我們重新開始！請告訴我您的目標 GMAT 分數。")
                    continue
                elif user_input.lower() == 'test':
                    print("🔧 測試 API 連接...")
                    test_result = advisor.chat("ping", max_retries=1)
                    if "錯誤" not in test_result and "Error" not in test_result:
                        print("✅ API 連接正常")
                        consecutive_errors = 0
                    else:
                        print(f"❌ API 連接有問題: {test_result}")
                    continue
                
                if user_input:
                    response = advisor.chat(user_input)
                    
                    # Check if response indicates an error
                    if any(keyword in response for keyword in ["錯誤", "Error", "抱歉", "無法處理"]):
                        consecutive_errors += 1
                        print(f"🤖 GMAT 顧問: {response}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            print("\n⚠️ 連續發生多次錯誤，建議：")
                            print("1. 輸入 'test' 檢查 API 連接")
                            print("2. 輸入 'reset' 重置對話")
                            print("3. 檢查網路連接後重新啟動")
                            print("4. 輸入 'quit' 退出程式")
                            print()
                    else:
                        consecutive_errors = 0  # Reset error count on successful response
                        print(f"🤖 GMAT 顧問: {response}")
                    
                    print()
                    
            except KeyboardInterrupt:
                print("\n\n👋 程式已中斷，再見！")
                break
            except Exception as e:
                consecutive_errors += 1
                print(f"❌ 輸入處理錯誤: {str(e)}")
                if consecutive_errors >= max_consecutive_errors:
                    print("⚠️ 請嘗試重新啟動程式")
                    break
            
    except Exception as e:
        print(f"❌ 系統初始化錯誤: {str(e)}")
        print("建議解決方案：")
        print("1. 確認 OpenAI 套件已安裝: pip install openai")
        print("2. 檢查 API Key 設置")
        print("3. 檢查網路連接")


if __name__ == "__main__":
    print("GMAT LLM 整合系統")
    print("1. Demo 模式 (示範功能，無需 API)")
    print("2. 互動模式 (需要 OpenAI API)")
    
    choice = input("請選擇模式 (1/2): ").strip()
    
    if choice == "1":
        demo_conversation()
    elif choice == "2":
        interactive_mode()
    else:
        print("無效選擇，執行 Demo 模式")
        demo_conversation() 