#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Study Plan LLM Function Handler
GMAT 讀書計畫 LLM 功能處理器

This module provides function calling interface for LLM integration
with the GMAT study planning system.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from gmat_study_planner import GMATStudyPlanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gmat_llm_handler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class GMATLLMFunctionHandler:
    """
    GMAT Study Plan Function Handler for LLM Integration
    為 LLM 整合提供的 GMAT 學習計劃功能處理器
    """
    
    def __init__(self):
        """Initialize the function handler with GMAT study planner"""
        self.planner = GMATStudyPlanner()
        logger.info("GMAT LLM 功能處理器初始化完成")
    
    def generate_gmat_study_plan(self, user_data: str) -> str:
        """
        Main function for LLM function calling to generate GMAT study plan
        LLM function calling 的主要函數，用於生成 GMAT 學習計劃
        
        Args:
            user_data: JSON string containing user input data
            
        Returns:
            JSON string containing study plan recommendations
        """
        logger.info("===== 開始處理 LLM Function Call 請求 =====")
        
        try:
            # Parse input JSON
            logger.info("解析輸入 JSON 數據")
            input_data = json.loads(user_data)
            logger.info(f"成功解析輸入數據: {list(input_data.keys())}")
            
            # Validate required fields
            required_fields = [
                'target_gmat_score', 'target_score_system', 'current_highest_gmat_score',
                'application_deadline', 'language_test_status', 'application_materials_progress',
                'study_status', 'weekday_study_hours', 'weekend_study_hours', 'current_section_scores'
            ]
            
            missing_fields = [field for field in required_fields if field not in input_data]
            if missing_fields:
                error_response = {
                    "success": False,
                    "error": f"缺少必要欄位: {', '.join(missing_fields)}",
                    "missing_fields": missing_fields,
                    "required_fields": required_fields
                }
                logger.error(f"輸入數據缺少必要欄位: {missing_fields}")
                return json.dumps(error_response, ensure_ascii=False, indent=2)
            
            # Generate study plan using the main planner
            logger.info("調用主要規劃器生成學習計劃")
            recommendations = self.planner.generate_study_plan(input_data)
            
            # Format response for LLM
            if "error" in recommendations:
                response = {
                    "success": False,
                    "error": recommendations["error"],
                    "recommendations": recommendations.get("recommendations", "請聯繫教學顧問獲得幫助")
                }
                logger.error(f"學習計劃生成失敗: {recommendations['error']}")
            else:
                response = {
                    "success": True,
                    "study_plan": {
                        "exam_cycle": recommendations.get("recommended_exam_cycle", "未定"),
                        "study_strategy": recommendations.get("recommended_study_strategy", ""),
                        "section_time_allocation": recommendations.get("recommended_section_time_allocation", ""),
                        "actual_time_allocation": recommendations.get("actual_study_time_allocation", ""),
                        "analysis": {
                            "score_gap": recommendations.get("score_gap_analysis", ""),
                            "schedule_sufficiency": recommendations.get("schedule_analysis", ""),
                            "time_sufficiency": recommendations.get("time_sufficiency_analysis", ""),
                            "required_improvement": recommendations.get("required_score_improvement", ""),
                            "available_days": recommendations.get("available_preparation_days", ""),
                            "weekly_hours": recommendations.get("weekly_study_hours", "")
                        },
                        "input_summary": recommendations.get("input_summary", {})
                    },
                    "timestamp": datetime.now().isoformat(),
                    "system_version": "1.0"
                }
                logger.info("學習計劃生成成功")
            
            # Return JSON response
            result = json.dumps(response, ensure_ascii=False, indent=2)
            logger.info("===== LLM Function Call 處理完成 =====")
            return result
            
        except json.JSONDecodeError as e:
            error_response = {
                "success": False,
                "error": f"JSON 格式錯誤: {str(e)}",
                "message": "請確認輸入的數據格式正確"
            }
            logger.error(f"JSON 解析錯誤: {str(e)}")
            return json.dumps(error_response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"系統錯誤: {str(e)}",
                "message": "請聯繫技術支援或重試"
            }
            logger.error(f"系統錯誤: {str(e)}")
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def validate_user_input(self, user_data: str) -> str:
        """
        Validate user input data format and content
        驗證用戶輸入數據格式和內容
        
        Args:
            user_data: JSON string containing user input data
            
        Returns:
            JSON string containing validation results
        """
        logger.info("開始驗證用戶輸入數據")
        
        try:
            # Parse input JSON
            input_data = json.loads(user_data)
            
            # Use planner's validation method
            try:
                validated_data = self.planner.validate_inputs(input_data)
                response = {
                    "success": True,
                    "message": "輸入數據驗證通過",
                    "validated_data": validated_data
                }
                logger.info("用戶輸入數據驗證通過")
            except ValueError as e:
                response = {
                    "success": False,
                    "error": f"數據驗證失敗: {str(e)}",
                    "message": "請檢查並修正輸入數據"
                }
                logger.warning(f"數據驗證失敗: {str(e)}")
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError as e:
            error_response = {
                "success": False,
                "error": f"JSON 格式錯誤: {str(e)}",
                "message": "請確認輸入的數據格式正確"
            }
            logger.error(f"JSON 解析錯誤: {str(e)}")
            return json.dumps(error_response, ensure_ascii=False, indent=2)
        except Exception as e:
            error_response = {
                "success": False,
                "error": f"驗證過程錯誤: {str(e)}",
                "message": "請聯繫技術支援"
            }
            logger.error(f"驗證過程錯誤: {str(e)}")
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def get_input_schema(self) -> str:
        """
        Get the expected input data schema for LLM reference
        獲取預期的輸入數據結構供 LLM 參考
        
        Returns:
            JSON string containing input schema information
        """
        schema = {
            "input_schema": {
                "target_gmat_score": {
                    "type": "integer",
                    "range": "200-805",
                    "description": "目標 GMAT 分數"
                },
                "target_score_system": {
                    "type": "string",
                    "options": ["Old", "New"],
                    "description": "分數制度 (舊制/新制)"
                },
                "current_highest_gmat_score": {
                    "type": "integer",
                    "range": "200-805",
                    "description": "目前最高 GMAT 分數"
                },
                "application_deadline": {
                    "type": "string",
                    "format": "YYYY-MM-DD",
                    "description": "申請截止日期"
                },
                "language_test_status": {
                    "type": "string",
                    "options": ["已完成", "未完成", "completed", "not completed"],
                    "description": "語言考試狀態"
                },
                "application_materials_progress": {
                    "type": "number",
                    "range": "0-100",
                    "description": "申請資料完成百分比"
                },
                "study_status": {
                    "type": "string",
                    "options": ["全職考生", "在職考生", "fulltime", "parttime"],
                    "description": "備考身份"
                },
                "weekday_study_hours": {
                    "type": "number",
                    "minimum": 0,
                    "description": "平日每日學習時數"
                },
                "weekend_study_hours": {
                    "type": "number",
                    "minimum": 0,
                    "description": "假日每日學習時數"
                },
                "current_section_scores": {
                    "type": "object",
                    "properties": {
                        "Quantitative": {
                            "type": "integer",
                            "range": "60-90",
                            "description": "數學積分"
                        },
                        "Verbal": {
                            "type": "integer",
                            "range": "60-90",
                            "description": "語文積分"
                        },
                        "Data Insights": {
                            "type": "integer",
                            "range": "60-90",
                            "description": "數據洞察積分"
                        }
                    },
                    "required": ["Quantitative", "Verbal", "Data Insights"],
                    "description": "各科目目前積分"
                }
            },
            "example_input": {
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
        }
        
        return json.dumps(schema, ensure_ascii=False, indent=2)


def create_function_definitions() -> str:
    """
    Create function definitions for LLM function calling
    為 LLM function calling 創建功能定義
    
    Returns:
        JSON string containing function definitions
    """
    functions = [
        {
            "name": "generate_gmat_study_plan",
            "description": "根據學生的個人情況生成完整的 GMAT 學習計劃，包括考試週期建議、學習策略、時間分配等",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_data": {
                        "type": "string",
                        "description": "包含學生完整資訊的 JSON 字串，必須包含目標分數、目前分數、申請截止日期、學習狀態等所有必要欄位"
                    }
                },
                "required": ["user_data"]
            }
        },
        {
            "name": "validate_user_input",
            "description": "驗證用戶輸入的數據格式和內容是否正確，在生成學習計劃前使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_data": {
                        "type": "string",
                        "description": "需要驗證的用戶輸入 JSON 字串"
                    }
                },
                "required": ["user_data"]
            }
        },
        {
            "name": "get_input_schema",
            "description": "獲取輸入數據的預期格式和結構資訊，幫助 LLM 了解需要收集哪些資訊",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]
    
    return json.dumps(functions, ensure_ascii=False, indent=2)


# Global handler instance for function calling
_handler = None

def get_handler():
    """Get or create the global handler instance"""
    global _handler
    if _handler is None:
        _handler = GMATLLMFunctionHandler()
    return _handler


# Function calling entry points
def generate_gmat_study_plan(user_data: str) -> str:
    """Function calling entry point for generating study plan"""
    return get_handler().generate_gmat_study_plan(user_data)


def validate_user_input(user_data: str) -> str:
    """Function calling entry point for validating user input"""
    return get_handler().validate_user_input(user_data)


def get_input_schema() -> str:
    """Function calling entry point for getting input schema"""
    return get_handler().get_input_schema()


if __name__ == "__main__":
    # Test the function handler
    print("GMAT LLM Function Handler Test")
    print("=" * 50)
    
    # Print function definitions
    print("\nFunction Definitions:")
    print(create_function_definitions())
    
    # Print input schema
    print("\nInput Schema:")
    print(get_input_schema())
    
    # Test with example data
    example_data = {
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
    
    print("\nTesting with example data...")
    result = generate_gmat_study_plan(json.dumps(example_data, ensure_ascii=False))
    print("Result:", result[:200] + "..." if len(result) > 200 else result) 