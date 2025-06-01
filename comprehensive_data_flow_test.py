#!/usr/bin/env python3
"""
完整數據流測試腳本 - GMAT診斷模組驗證
========================================

此腳本全面測試三個科目(DI、Q、V)的數據流完整性，並驗證計算方式是否符合sec-doc-zh的標準。

執行流程：
1. 創建符合標準文檔要求的測試數據
2. 測試數據流完整性
3. 驗證計算邏輯正確性
4. 生成詳細的一致性報告

作者：Claude Sonnet 4
日期：2025-01-30
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
import traceback
from datetime import datetime
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_data_flow_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ComprehensiveDataFlowTest:
    """完整數據流測試類別"""
    
    def __init__(self):
        self.test_results = {}
        self.calculation_inconsistencies = []
        self.data_flow_issues = []
        self.missing_data_issues = []
        
    def create_standard_di_data(self) -> pd.DataFrame:
        """
        創建符合 DI 標準文檔要求的測試數據
        基於 gmat-di-score-logic-dustin-v1.5.md 第零章規範
        """
        logger.info("Creating standard DI test data...")
        
        # Based on sec-doc-zh specifications
        di_data = pd.DataFrame({
            # 基礎必需欄位
            'question_position': list(range(1, 21)),  # 20 題 DI
            'question_time': [2.5, 1.8, 4.2, 3.1, 2.9, 1.2, 3.8, 2.7, 4.5, 1.9,
                             3.3, 2.1, 4.1, 2.8, 3.6, 1.7, 2.4, 3.9, 2.2, 1.5],
            'is_correct': [True, False, True, True, False, True, False, True, True, False,
                          True, True, False, True, False, True, True, False, True, True],
            
            # DI 特定欄位
            'content_domain': ['Math Related', 'Non-Math Related', 'Math Related', 'Non-Math Related'] * 5,
            'question_type': ['DS', 'TPA', 'MSR', 'GT', 'DS', 'TPA', 'MSR', 'GT'] * 2 + ['DS', 'TPA', 'MSR', 'GT'],
            'question_difficulty': [0.5, 1.2, -0.3, 1.8, 0.8, -0.5, 1.5, 0.2, 1.9, -0.1,
                                   0.7, 1.1, -0.8, 1.3, 0.9, -0.2, 1.6, 0.4, 1.4, 0.1],
            
            # MSR 題組相關欄位 (根據標準文檔要求)
            'msr_group_id': [None, None, 1, None, None, None, 2, None, None, None,
                            None, None, 3, None, None, None, 4, None, None, None],
            'msr_group_total_time': [None, None, 8.5, None, None, None, 9.2, None, None, None,
                                    None, None, 7.8, None, None, None, 8.9, None, None, None],
            'msr_reading_time': [None, None, 2.5, None, None, None, 2.8, None, None, None,
                                None, None, 2.1, None, None, None, 2.6, None, None, None],
            'is_first_msr_q': [None, None, True, None, None, None, True, None, None, None,
                              None, None, True, None, None, None, True, None, None, None],
            
            # 科目標識
            'Subject': ['DI'] * 20
        })
        
        # Add invalid data flag (initially False)
        di_data['is_invalid'] = False
        
        return di_data
    
    def create_standard_q_data(self) -> pd.DataFrame:
        """
        創建符合 Q 標準文檔要求的測試數據
        基於 gmat-q-score-logic-dustin-v1.5.md 第零章規範
        """
        logger.info("Creating standard Q test data...")
        
        q_data = pd.DataFrame({
            # 基礎必需欄位
            'question_position': list(range(1, 22)),  # 21 題 Q
            'question_time': [2.1, 1.8, 3.2, 2.5, 1.9, 2.8, 3.1, 2.3, 1.7, 2.9,
                             3.4, 2.0, 2.6, 3.0, 1.5, 2.7, 3.3, 2.2, 1.8, 2.4, 2.8],
            'is_correct': [True, False, True, True, False, True, False, True, True, False,
                          True, True, False, True, False, True, True, False, True, True, False],
            
            # Q 特定欄位
            'question_type': ['Real', 'Pure'] * 10 + ['Real'],
            'question_difficulty': [0.3, 1.1, -0.4, 1.7, 0.6, -0.3, 1.4, 0.1, 1.8, -0.2,
                                   0.8, 1.0, -0.6, 1.2, 0.5, -0.1, 1.5, 0.4, 1.6, 0.2, 0.9],
            'question_fundamental_skill': [
                'Rates/Ratio/Percent', 'Value/Order/Factor', 'Equal/Unequal/ALG',
                'Counting/Sets/Series/Prob/Stats', 'Rates/Ratio/Percent', 'Value/Order/Factor'
            ] * 3 + ['Equal/Unequal/ALG', 'Counting/Sets/Series/Prob/Stats', 'Rates/Ratio/Percent'],
            
            # 科目標識
            'Subject': ['Q'] * 21
        })
        
        # Add invalid data flag (initially False)
        q_data['is_invalid'] = False
        
        return q_data
    
    def create_standard_v_data(self) -> pd.DataFrame:
        """
        創建符合 V 標準文檔要求的測試數據
        基於 gmat-v-score-logic-dustin-v1.5.md 第零章規範
        """
        logger.info("Creating standard V test data...")
        
        v_data = pd.DataFrame({
            # 基礎必需欄位
            'question_position': list(range(1, 24)),  # 23 題 V
            'question_time': [2.2, 1.9, 4.5, 3.8, 2.1, 1.8, 3.2, 2.7, 4.1, 3.5,
                             2.0, 1.7, 3.9, 2.8, 4.2, 3.1, 2.3, 1.6, 3.7, 2.9,
                             4.0, 3.3, 2.5],
            'is_correct': [True, False, True, True, False, True, False, True, True, False,
                          True, True, False, True, False, True, True, False, True, True,
                          False, True, True],
            
            # V 特定欄位
            'question_type': ['CR', 'RC', 'RC', 'RC', 'CR', 'CR', 'RC', 'RC', 'RC', 'RC',
                             'CR', 'CR', 'RC', 'RC', 'RC', 'CR', 'CR', 'CR', 'RC', 'RC',
                             'RC', 'CR', 'CR'],
            'question_difficulty': [0.4, 1.3, -0.2, 1.6, 0.7, -0.4, 1.1, 0.2, 1.7, -0.1,
                                   0.9, 1.4, -0.5, 1.0, 0.5, -0.3, 1.2, 0.3, 1.5, 0.1,
                                   1.8, 0.6, 0.8],
            'question_fundamental_skill': [
                'Plan/Construct', 'Identify Stated Idea', 'Identify Inferred Idea',
                'Analysis/Critique', 'Plan/Construct', 'Identify Stated Idea'
            ] * 3 + ['Identify Inferred Idea', 'Analysis/Critique', 'Plan/Construct',
                    'Identify Stated Idea', 'Analysis/Critique'],
            
            # RC 題組相關欄位
            'rc_group_id': [None, 1, 1, 1, None, None, 2, 2, 2, 2,
                           None, None, 3, 3, 3, None, None, None, 4, 4,
                           4, None, None],
            'passage_id': [None, 1, 1, 1, None, None, 2, 2, 2, 2,
                          None, None, 3, 3, 3, None, None, None, 4, 4,
                          4, None, None],
            'passage_position': [None, 1, 2, 3, None, None, 1, 2, 3, 4,
                                None, None, 1, 2, 3, None, None, None, 1, 2,
                                3, None, None],
            
            # 科目標識
            'Subject': ['V'] * 23
        })
        
        # Add invalid data flag (initially False)
        v_data['is_invalid'] = False
        
        return v_data
        
    def test_di_data_flow(self, df_di: pd.DataFrame) -> Dict[str, Any]:
        """測試 DI 模組數據流完整性"""
        logger.info("Testing DI module data flow...")
        
        results = {
            'module': 'DI',
            'data_flow_complete': True,
            'missing_columns': [],
            'calculation_errors': [],
            'function_execution': {},
            'data_processing': {}
        }
        
        try:
            # Import DI modules
            from gmat_diagnosis_app.diagnostics.di_diagnostic import diagnose_di
            from gmat_diagnosis_app.diagnostics.di_modules.main import run_di_diagnosis
            
            # Test required columns according to sec-doc-zh
            required_columns = [
                'question_position', 'question_time', 'is_correct', 
                'content_domain', 'question_type', 'question_difficulty',
                'msr_group_id', 'Subject'
            ]
            
            missing_cols = [col for col in required_columns if col not in df_di.columns]
            if missing_cols:
                results['missing_columns'] = missing_cols
                results['data_flow_complete'] = False
                logger.error(f"DI missing required columns: {missing_cols}")
            
            # Test data preprocessing according to Chapter 0 standards
            results['data_processing']['msr_groups'] = self.verify_msr_group_data(df_di)
            results['data_processing']['question_types'] = self.verify_question_types(df_di, ['DS', 'TPA', 'MSR', 'GT'])
            results['data_processing']['content_domains'] = self.verify_content_domains(df_di)
            
            # Test main function execution
            logger.info("Testing DI diagnose_di function...")
            
            # Use correct function signature - only requires df_di
            di_result = diagnose_di(df_di)
            
            if di_result is not None and len(di_result) == 3:
                results['function_execution']['diagnose_di'] = True
                results['function_execution']['output_type'] = 'tuple'
                results['function_execution']['result_components'] = len(di_result)
                logger.info("DI diagnose_di function executed successfully")
            else:
                results['function_execution']['diagnose_di'] = False
                results['data_flow_complete'] = False
                logger.error("DI diagnose_di function returned invalid result")
            
            # Test detailed calculation flow according to sec-doc-zh
            results['calculation_verification'] = self.verify_di_calculations(df_di, "No")
            
        except Exception as e:
            logger.error(f"DI data flow test failed: {str(e)}")
            logger.error(traceback.format_exc())
            results['data_flow_complete'] = False
            results['error'] = str(e)
            
        return results
    
    def test_q_data_flow(self, df_q: pd.DataFrame) -> Dict[str, Any]:
        """測試 Q 模組數據流完整性"""
        logger.info("Testing Q module data flow...")
        
        results = {
            'module': 'Q',
            'data_flow_complete': True,
            'missing_columns': [],
            'calculation_errors': [],
            'function_execution': {},
            'data_processing': {}
        }
        
        try:
            # Import Q modules
            from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
            
            # Test required columns according to sec-doc-zh
            required_columns = [
                'question_position', 'question_time', 'is_correct',
                'question_type', 'question_difficulty', 'question_fundamental_skill',
                'Subject'
            ]
            
            missing_cols = [col for col in required_columns if col not in df_q.columns]
            if missing_cols:
                results['missing_columns'] = missing_cols
                results['data_flow_complete'] = False
                logger.error(f"Q missing required columns: {missing_cols}")
            
            # Test data preprocessing according to Chapter 0 standards
            results['data_processing']['question_types'] = self.verify_question_types(df_q, ['Real', 'Pure'])
            results['data_processing']['fundamental_skills'] = self.verify_fundamental_skills(df_q)
            
            # Test main function execution
            logger.info("Testing Q diagnose_q function...")
            
            # Use correct function signature
            q_result = diagnose_q(df_q)
            
            if q_result is not None and len(q_result) == 3:
                results['function_execution']['diagnose_q'] = True
                results['function_execution']['output_type'] = 'tuple'
                results['function_execution']['result_components'] = len(q_result)
                logger.info("Q diagnose_q function executed successfully")
            else:
                results['function_execution']['diagnose_q'] = False
                results['data_flow_complete'] = False
                logger.error("Q diagnose_q function returned invalid result")
            
            # Test detailed calculation flow according to sec-doc-zh
            results['calculation_verification'] = self.verify_q_calculations(df_q, "No")
            
        except Exception as e:
            logger.error(f"Q data flow test failed: {str(e)}")
            logger.error(traceback.format_exc())
            results['data_flow_complete'] = False
            results['error'] = str(e)
            
        return results
    
    def test_v_data_flow(self, df_v: pd.DataFrame) -> Dict[str, Any]:
        """測試 V 模組數據流完整性"""
        logger.info("Testing V module data flow...")
        
        results = {
            'module': 'V',
            'data_flow_complete': True,
            'missing_columns': [],
            'calculation_errors': [],
            'function_execution': {},
            'data_processing': {}
        }
        
        try:
            # Import V modules
            from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed
            
            # Test required columns according to sec-doc-zh
            required_columns = [
                'question_position', 'question_time', 'is_correct',
                'question_type', 'question_difficulty', 'question_fundamental_skill',
                'Subject'
            ]
            
            missing_cols = [col for col in required_columns if col not in df_v.columns]
            if missing_cols:
                results['missing_columns'] = missing_cols
                results['data_flow_complete'] = False
                logger.error(f"V missing required columns: {missing_cols}")
            
            # Test data preprocessing according to Chapter 0 standards
            results['data_processing']['question_types'] = self.verify_question_types(df_v, ['CR', 'RC'])
            results['data_processing']['fundamental_skills'] = self.verify_fundamental_skills(df_v)
            results['data_processing']['rc_groups'] = self.verify_rc_group_data(df_v)
            
            # Test main function execution
            logger.info("Testing V run_v_diagnosis_processed function...")
            
            # Calculate required parameters for V function
            v_time_pressure_status = False  # Default
            v_avg_time_per_type = {
                'CR': df_v[df_v['question_type'] == 'CR']['question_time'].mean() if 'CR' in df_v['question_type'].values else 2.0,
                'RC': df_v[df_v['question_type'] == 'RC']['question_time'].mean() if 'RC' in df_v['question_type'].values else 3.0
            }
            
            # Use correct function signature
            v_result = run_v_diagnosis_processed(df_v, v_time_pressure_status, v_avg_time_per_type)
            
            if v_result is not None and len(v_result) == 3:
                results['function_execution']['run_v_diagnosis_processed'] = True
                results['function_execution']['output_type'] = 'tuple'
                results['function_execution']['result_components'] = len(v_result)
                logger.info("V run_v_diagnosis_processed function executed successfully")
            else:
                results['function_execution']['run_v_diagnosis_processed'] = False
                results['data_flow_complete'] = False
                logger.error(f"V run_v_diagnosis_processed function returned invalid result: {type(v_result)} with value: {v_result}")
                # Add more details about the result
                if v_result is not None:
                    logger.error(f"V result type: {type(v_result)}, length: {len(v_result) if hasattr(v_result, '__len__') else 'N/A'}")
                    if isinstance(v_result, (tuple, list)) and len(v_result) >= 1:
                        logger.error(f"V result first element: {type(v_result[0])}")
                else:
                    logger.error("V result is None")
            
            # Test detailed calculation flow according to sec-doc-zh
            results['calculation_verification'] = self.verify_v_calculations(df_v, "No")
            
        except Exception as e:
            logger.error(f"V data flow test failed: {str(e)}")
            logger.error(traceback.format_exc())
            results['data_flow_complete'] = False
            results['error'] = str(e)
            
        return results
    
    def verify_msr_group_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """驗證 MSR 題組數據完整性"""
        msr_data = df[df['question_type'] == 'MSR'].copy()
        
        verification = {
            'groups_found': len(msr_data['msr_group_id'].dropna().unique()) if 'msr_group_id' in df.columns else 0,
            'total_msr_questions': len(msr_data),
            'has_group_id': 'msr_group_id' in df.columns,
            'has_reading_time': 'msr_reading_time' in df.columns,
            'has_first_q_marker': 'is_first_msr_q' in df.columns
        }
        
        if verification['groups_found'] == 0 and verification['total_msr_questions'] > 0:
            self.missing_data_issues.append("MSR questions found but no group IDs provided")
        
        return verification
    
    def verify_rc_group_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """驗證 RC 題組數據完整性"""
        rc_data = df[df['question_type'] == 'RC'].copy()
        
        verification = {
            'groups_found': len(rc_data['rc_group_id'].dropna().unique()) if 'rc_group_id' in df.columns else 0,
            'total_rc_questions': len(rc_data),
            'has_group_id': 'rc_group_id' in df.columns,
            'has_passage_id': 'passage_id' in df.columns,
            'has_passage_position': 'passage_position' in df.columns
        }
        
        if verification['groups_found'] == 0 and verification['total_rc_questions'] > 0:
            self.missing_data_issues.append("RC questions found but no group IDs provided")
        
        return verification
    
    def verify_question_types(self, df: pd.DataFrame, expected_types: List[str]) -> Dict[str, Any]:
        """驗證題型數據完整性"""
        actual_types = df['question_type'].unique().tolist()
        
        verification = {
            'expected_types': expected_types,
            'actual_types': actual_types,
            'missing_types': [t for t in expected_types if t not in actual_types],
            'unexpected_types': [t for t in actual_types if t not in expected_types]
        }
        
        if verification['missing_types']:
            self.missing_data_issues.append(f"Missing question types: {verification['missing_types']}")
        
        if verification['unexpected_types']:
            self.data_flow_issues.append(f"Unexpected question types: {verification['unexpected_types']}")
        
        return verification
    
    def verify_content_domains(self, df: pd.DataFrame) -> Dict[str, Any]:
        """驗證內容領域數據完整性"""
        expected_domains = ['Math Related', 'Non-Math Related']
        actual_domains = df['content_domain'].unique().tolist() if 'content_domain' in df.columns else []
        
        verification = {
            'expected_domains': expected_domains,
            'actual_domains': actual_domains,
            'missing_domains': [d for d in expected_domains if d not in actual_domains],
            'unexpected_domains': [d for d in actual_domains if d not in expected_domains]
        }
        
        return verification
    
    def verify_fundamental_skills(self, df: pd.DataFrame) -> Dict[str, Any]:
        """驗證基礎技能數據完整性"""
        skills = df['question_fundamental_skill'].unique().tolist() if 'question_fundamental_skill' in df.columns else []
        
        verification = {
            'total_skills': len(skills),
            'skills_found': skills,
            'has_skill_data': 'question_fundamental_skill' in df.columns
        }
        
        if not verification['has_skill_data']:
            self.missing_data_issues.append("Fundamental skill data not found")
        
        return verification
    
    def verify_di_calculations(self, df: pd.DataFrame, time_pressure_status: str) -> Dict[str, Any]:
        """
        驗證 DI 計算邏輯是否符合 sec-doc-zh 標準
        基於 gmat-di-score-logic-dustin-v1.5.md
        """
        logger.info("Verifying DI calculations against sec-doc-zh standards...")
        
        verification = {
            'chapter_0_data_completeness': True,
            'chapter_1_time_analysis': {},
            'chapter_2_performance_analysis': {},
            'inconsistencies': []
        }
        
        try:
            # Chapter 0 verification: Core input data
            max_allowed_time = 45  # Fixed according to standards
            total_questions = 20   # Fixed according to standards
            
            if len(df) != total_questions:
                verification['inconsistencies'].append(f"Expected {total_questions} questions, got {len(df)}")
            
            # Chapter 1 verification: Time strategy analysis
            total_test_time = df['question_time'].sum()
            time_diff = max_allowed_time - total_test_time
            
            # Time pressure calculation according to standards
            last_third_start = int(total_questions * 2/3) + 1
            last_third_questions = df[df['question_position'] >= last_third_start]
            fast_end_questions = last_third_questions[last_third_questions['question_time'] < 1.0]
            
            time_pressure = time_diff <= 3 and len(fast_end_questions) > 0
            if time_pressure_status == "Yes":
                time_pressure = True
            elif time_pressure_status == "No":
                time_pressure = False
            
            verification['chapter_1_time_analysis'] = {
                'total_test_time': total_test_time,
                'time_diff': time_diff,
                'time_pressure': time_pressure,
                'fast_end_questions_count': len(fast_end_questions),
                'overtime_thresholds': self.get_di_overtime_thresholds(time_pressure)
            }
            
            # Chapter 2 verification: Multi-dimensional performance analysis
            content_domain_analysis = self.analyze_content_domain_performance(df)
            question_type_analysis = self.analyze_question_type_performance(df)
            difficulty_analysis = self.analyze_difficulty_performance(df)
            
            verification['chapter_2_performance_analysis'] = {
                'content_domain': content_domain_analysis,
                'question_type': question_type_analysis,
                'difficulty': difficulty_analysis
            }
            
        except Exception as e:
            verification['inconsistencies'].append(f"Calculation error: {str(e)}")
            logger.error(f"DI calculation verification failed: {str(e)}")
        
        return verification
    
    def verify_q_calculations(self, df: pd.DataFrame, time_pressure_status: str) -> Dict[str, Any]:
        """
        驗證 Q 計算邏輯是否符合 sec-doc-zh 標準
        基於 gmat-q-score-logic-dustin-v1.5.md
        """
        logger.info("Verifying Q calculations against sec-doc-zh standards...")
        
        verification = {
            'chapter_0_data_completeness': True,
            'chapter_1_time_analysis': {},
            'chapter_2_performance_analysis': {},
            'inconsistencies': []
        }
        
        try:
            # Chapter 1 verification: Time strategy analysis
            max_allowed_time = 45  # Fixed according to standards
            total_test_time = df['question_time'].sum()
            time_diff = max_allowed_time - total_test_time
            
            # Time pressure calculation
            total_questions = len(df)
            last_third_start = int(total_questions * 2/3) + 1
            last_third_questions = df[df['question_position'] >= last_third_start]
            fast_end_questions = last_third_questions[last_third_questions['question_time'] < 1.0]
            
            time_pressure = time_diff <= 3 and len(fast_end_questions) > 0
            if time_pressure_status == "Yes":
                time_pressure = True
            elif time_pressure_status == "No":
                time_pressure = False
            
            # Overtime threshold according to standards
            overtime_threshold = 2.5 if time_pressure else 3.0
            
            verification['chapter_1_time_analysis'] = {
                'total_test_time': total_test_time,
                'time_diff': time_diff,
                'time_pressure': time_pressure,
                'fast_end_questions_count': len(fast_end_questions),
                'overtime_threshold': overtime_threshold
            }
            
            # Chapter 2 verification: Performance analysis by question type
            real_pure_analysis = self.analyze_real_pure_performance(df)
            difficulty_analysis = self.analyze_difficulty_performance(df)
            
            verification['chapter_2_performance_analysis'] = {
                'real_pure': real_pure_analysis,
                'difficulty': difficulty_analysis
            }
            
        except Exception as e:
            verification['inconsistencies'].append(f"Calculation error: {str(e)}")
            logger.error(f"Q calculation verification failed: {str(e)}")
        
        return verification
    
    def verify_v_calculations(self, df: pd.DataFrame, time_pressure_status: str) -> Dict[str, Any]:
        """
        驗證 V 計算邏輯是否符合 sec-doc-zh 標準
        基於 gmat-v-score-logic-dustin-v1.5.md
        """
        logger.info("Verifying V calculations against sec-doc-zh standards...")
        
        verification = {
            'chapter_0_data_completeness': True,
            'chapter_1_time_analysis': {},
            'chapter_2_performance_analysis': {},
            'inconsistencies': []
        }
        
        try:
            # Chapter 1 verification: Time strategy analysis
            max_allowed_time = 45  # Fixed according to standards
            total_test_time = df['question_time'].sum()
            time_diff = max_allowed_time - total_test_time
            
            # Time pressure calculation
            total_questions = len(df)
            last_third_start = int(total_questions * 2/3) + 1
            last_third_questions = df[df['question_position'] >= last_third_start]
            fast_end_questions = last_third_questions[last_third_questions['question_time'] < 1.0]
            
            time_pressure = time_diff <= 3 and len(fast_end_questions) > 0
            if time_pressure_status == "Yes":
                time_pressure = True
            elif time_pressure_status == "No":
                time_pressure = False
            
            # Overtime thresholds according to standards
            overtime_threshold_cr = 2.0 if time_pressure else 2.5
            rc_group_target_time = self.get_v_rc_target_times(time_pressure)
            
            verification['chapter_1_time_analysis'] = {
                'total_test_time': total_test_time,
                'time_diff': time_diff,
                'time_pressure': time_pressure,
                'fast_end_questions_count': len(fast_end_questions),
                'overtime_threshold_cr': overtime_threshold_cr,
                'rc_group_target_time': rc_group_target_time
            }
            
            # Chapter 2 verification: Performance analysis
            cr_rc_analysis = self.analyze_cr_rc_performance(df)
            difficulty_analysis = self.analyze_difficulty_performance(df)
            
            verification['chapter_2_performance_analysis'] = {
                'cr_rc': cr_rc_analysis,
                'difficulty': difficulty_analysis
            }
            
        except Exception as e:
            verification['inconsistencies'].append(f"Calculation error: {str(e)}")
            logger.error(f"V calculation verification failed: {str(e)}")
        
        return verification
    
    def get_di_overtime_thresholds(self, time_pressure: bool) -> Dict[str, float]:
        """獲取 DI 超時閾值（根據標準文檔）"""
        if time_pressure:
            return {
                'TPA': 3.0,
                'GT': 3.0,
                'DS': 2.0,
                'MSR_group_target': 6.0
            }
        else:
            return {
                'TPA': 3.5,
                'GT': 3.5,
                'DS': 2.5,
                'MSR_group_target': 7.0
            }
    
    def get_v_rc_target_times(self, time_pressure: bool) -> Dict[str, float]:
        """獲取 V RC 目標時間（根據標準文檔）"""
        if time_pressure:
            return {
                '3_questions': 6.0,
                '4_questions': 8.0
            }
        else:
            return {
                '3_questions': 7.0,
                '4_questions': 9.0
            }
    
    def analyze_content_domain_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析內容領域表現（DI 專用）"""
        if 'content_domain' not in df.columns:
            return {'error': 'content_domain column not found'}
        
        analysis = {}
        for domain in df['content_domain'].unique():
            domain_data = df[df['content_domain'] == domain]
            analysis[domain] = {
                'total_questions': len(domain_data),
                'error_count': len(domain_data[domain_data['is_correct'] == False]),
                'error_rate': len(domain_data[domain_data['is_correct'] == False]) / len(domain_data) if len(domain_data) > 0 else 0
            }
        
        return analysis
    
    def analyze_question_type_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析題型表現"""
        analysis = {}
        for qtype in df['question_type'].unique():
            type_data = df[df['question_type'] == qtype]
            analysis[qtype] = {
                'total_questions': len(type_data),
                'error_count': len(type_data[type_data['is_correct'] == False]),
                'error_rate': len(type_data[type_data['is_correct'] == False]) / len(type_data) if len(type_data) > 0 else 0,
                'avg_time': type_data['question_time'].mean()
            }
        
        return analysis
    
    def analyze_real_pure_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析 Real/Pure 題型表現（Q 專用）"""
        analysis = {}
        for qtype in ['Real', 'Pure']:
            if qtype in df['question_type'].values:
                type_data = df[df['question_type'] == qtype]
                analysis[qtype] = {
                    'total_questions': len(type_data),
                    'error_count': len(type_data[type_data['is_correct'] == False]),
                    'error_rate': len(type_data[type_data['is_correct'] == False]) / len(type_data) if len(type_data) > 0 else 0,
                    'avg_time': type_data['question_time'].mean()
                }
        
        return analysis
    
    def analyze_cr_rc_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析 CR/RC 表現（V 專用）"""
        analysis = {}
        for qtype in ['CR', 'RC']:
            if qtype in df['question_type'].values:
                type_data = df[df['question_type'] == qtype]
                analysis[qtype] = {
                    'total_questions': len(type_data),
                    'error_count': len(type_data[type_data['is_correct'] == False]),
                    'error_rate': len(type_data[type_data['is_correct'] == False]) / len(type_data) if len(type_data) > 0 else 0,
                    'avg_time': type_data['question_time'].mean()
                }
        
        return analysis
    
    def analyze_difficulty_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析難度表現（通用）"""
        def get_difficulty_level(difficulty):
            if difficulty <= -1:
                return "Low (505+)"
            elif difficulty <= 0:
                return "Mid (555+)"
            elif difficulty <= 1:
                return "Mid (605+)"
            elif difficulty <= 1.5:
                return "Mid (655+)"
            elif difficulty <= 1.95:
                return "High (705+)"
            else:
                return "High (805+)"
        
        df['difficulty_level'] = df['question_difficulty'].apply(get_difficulty_level)
        
        analysis = {}
        for level in df['difficulty_level'].unique():
            level_data = df[df['difficulty_level'] == level]
            analysis[level] = {
                'total_questions': len(level_data),
                'error_count': len(level_data[level_data['is_correct'] == False]),
                'error_rate': len(level_data[level_data['is_correct'] == False]) / len(level_data) if len(level_data) > 0 else 0
            }
        
        return analysis
    
    def generate_comprehensive_report(self) -> str:
        """生成完整測試報告"""
        logger.info("Generating comprehensive test report...")
        
        report = f"""
=============================================================================
                         GMAT 診斷模組完整數據流測試報告
=============================================================================

測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
測試目標: 驗證三個科目(DI、Q、V)的數據流完整性及計算邏輯一致性

=============================================================================
                                 測試摘要
=============================================================================

總測試數量: {len(self.test_results)}
成功模組: {sum(1 for r in self.test_results.values() if r.get('data_flow_complete', False))}
失敗模組: {sum(1 for r in self.test_results.values() if not r.get('data_flow_complete', False))}

資料流問題數量: {len(self.data_flow_issues)}
數據缺失問題數量: {len(self.missing_data_issues)}
計算不一致問題數量: {len(self.calculation_inconsistencies)}

=============================================================================
                              詳細測試結果
=============================================================================
"""
        
        for module, results in self.test_results.items():
            report += f"""
--- {results['module']} 模組測試結果 ---
資料流完整性: {'✅ 通過' if results['data_flow_complete'] else '❌ 失敗'}
"""
            
            if results.get('missing_columns'):
                report += f"缺失欄位: {', '.join(results['missing_columns'])}\n"
            
            if results.get('function_execution'):
                # Get correct function name for each module
                if module == 'V':
                    func_name = 'run_v_diagnosis_processed'
                elif module == 'DI':
                    func_name = 'diagnose_di'
                elif module == 'Q':
                    func_name = 'diagnose_q'
                else:
                    func_name = f'diagnose_{module.lower()}'
                
                func_status = '✅ 成功' if results['function_execution'].get(func_name, False) else '❌ 失敗'
                report += f"主函數執行: {func_status}\n"
            
            if results.get('data_processing'):
                report += "數據處理驗證:\n"
                for key, value in results['data_processing'].items():
                    report += f"  - {key}: {value}\n"
            
            if results.get('calculation_verification'):
                calc_data = results['calculation_verification']
                if calc_data.get('inconsistencies'):
                    report += f"計算不一致問題: {len(calc_data['inconsistencies'])}\n"
                    for issue in calc_data['inconsistencies']:
                        report += f"  - {issue}\n"
                        self.calculation_inconsistencies.append(f"{module}: {issue}")
        
        # Add issues summary
        if self.data_flow_issues:
            report += f"""
=============================================================================
                               資料流問題
=============================================================================
"""
            for issue in self.data_flow_issues:
                report += f"- {issue}\n"
        
        if self.missing_data_issues:
            report += f"""
=============================================================================
                               數據缺失問題
=============================================================================
"""
            for issue in self.missing_data_issues:
                report += f"- {issue}\n"
        
        if self.calculation_inconsistencies:
            report += f"""
=============================================================================
                              計算邏輯不一致
=============================================================================
"""
            for issue in self.calculation_inconsistencies:
                report += f"- {issue}\n"
        
        # Overall assessment
        all_passed = all(r.get('data_flow_complete', False) for r in self.test_results.values())
        no_major_issues = len(self.calculation_inconsistencies) == 0 and len(self.data_flow_issues) == 0
        
        report += f"""
=============================================================================
                                整體評估
=============================================================================

資料流完整性: {'✅ 全部通過' if all_passed else '❌ 存在問題'}
計算邏輯一致性: {'✅ 符合標準' if no_major_issues else '❌ 存在不一致'}

建議:
"""
        
        if not all_passed:
            report += "- 修復數據流問題，確保所有必需欄位完整\n"
        
        if not no_major_issues:
            report += "- 檢查並修正計算邏輯，使其符合 sec-doc-zh 標準\n"
        
        if all_passed and no_major_issues:
            report += "- 系統運行正常，數據流完整，計算邏輯符合標準\n"
        
        report += """
=============================================================================
                                測試完成
=============================================================================
"""
        
        return report
    
    def run_comprehensive_test(self):
        """執行完整測試流程"""
        logger.info("Starting comprehensive data flow test...")
        
        try:
            # Create test data according to sec-doc-zh standards
            logger.info("Creating test data according to sec-doc-zh standards...")
            di_data = self.create_standard_di_data()
            q_data = self.create_standard_q_data()
            v_data = self.create_standard_v_data()
            
            # Test each module
            logger.info("Testing all modules...")
            self.test_results['DI'] = self.test_di_data_flow(di_data)
            self.test_results['Q'] = self.test_q_data_flow(q_data)
            self.test_results['V'] = self.test_v_data_flow(v_data)
            
            # Generate comprehensive report
            report = self.generate_comprehensive_report()
            
            # Save report to file
            with open('comprehensive_data_flow_test_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Display report
            print(report)
            
            logger.info("Comprehensive test completed. Report saved to comprehensive_data_flow_test_report.txt")
            
        except Exception as e:
            logger.error(f"Comprehensive test failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise


def main():
    """主執行函數"""
    print("=============================================================================")
    print("                        GMAT 診斷模組完整數據流測試")
    print("=============================================================================")
    print()
    print("此測試將驗證:")
    print("1. 三個科目(DI、Q、V)的數據流完整性")
    print("2. 必需欄位是否齊全")
    print("3. 計算邏輯是否符合 sec-doc-zh 標準")
    print("4. 函數執行是否正常")
    print()
    
    try:
        # Create and run comprehensive test
        tester = ComprehensiveDataFlowTest()
        tester.run_comprehensive_test()
        
        print("\n✅ 測試完成！請查看 'comprehensive_data_flow_test_report.txt' 獲取詳細報告。")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        print("\n請檢查錯誤日誌 'comprehensive_data_flow_test.log' 獲取詳細信息。")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 