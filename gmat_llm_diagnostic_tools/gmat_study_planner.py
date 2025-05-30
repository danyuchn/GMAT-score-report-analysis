#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAT Study Plan Automation System
GMAT 讀書計畫自動化規劃系統

This system automatically generates GMAT study plans and cycle recommendations
based on student's personal situation, target score, and available resources.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gmat_planner.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class GMATStudyPlanner:
    """
    GMAT Study Plan Automation System
    
    Main class that implements all the core functions for GMAT study planning
    according to the specifications in basic-helper.md
    """
    
    def __init__(self):
        """Initialize the GMAT Study Planner with all necessary data"""
        logger.info("初始化 GMAT 學習規劃系統")
        logger.info("Loading GMAT conversion table and reference data")
        
        self.gmat_conversion_table = self._load_gmat_conversion_table()
        logger.info(f"已載入 GMAT 分數轉換表，包含 {len(self.gmat_conversion_table)} 個對照數據")
        
        self.section_percentile_data = self._load_section_percentile_data()
        logger.info("已載入科目積分與百分位對照數據")
        
        self.strategy_recommendation_table = self._load_strategy_table()
        logger.info(f"已載入策略建議表，包含 {len(self.strategy_recommendation_table)} 種情境")
    
    def _load_gmat_conversion_table(self) -> Dict[int, int]:
        """
        Load GMAT score conversion table from 10th Edition to Focus Edition
        Returns a dictionary mapping old scores to new scores
        """
        conversion_data = [
            (800, 805), (790, 805), (790, 795), (790, 785), (780, 785), (780, 775),
            (780, 765), (780, 755), (770, 755), (770, 745), (770, 735), (760, 735),
            (760, 725), (760, 715), (750, 715), (750, 705), (750, 695), (740, 695),
            (740, 685), (730, 685), (730, 675), (720, 675), (720, 665), (710, 665),
            (710, 655), (700, 655), (700, 645), (690, 645), (690, 635), (680, 635),
            (680, 625), (680, 615), (670, 615), (660, 615), (650, 615), (650, 605),
            (640, 595), (640, 585), (630, 585), (620, 585), (610, 575), (610, 565),
            (600, 565), (600, 555), (590, 555), (580, 555), (580, 545), (570, 545),
            (570, 535), (560, 535), (560, 525), (550, 525), (550, 515), (540, 515),
            (530, 515), (530, 505), (530, 495), (520, 495), (510, 495), (500, 495),
            (500, 485), (490, 485), (490, 475), (480, 475), (470, 475), (470, 465),
            (460, 465), (460, 455), (450, 455), (450, 445), (440, 445), (440, 435),
            (430, 435), (420, 435), (410, 435), (410, 425), (400, 425), (400, 415),
            (390, 415), (380, 415), (380, 405), (370, 405), (370, 395), (360, 395),
            (350, 395), (350, 385), (350, 375), (340, 375), (330, 375), (320, 375),
            (320, 365), (310, 355), (310, 345), (300, 355), (300, 365), (290, 345),
            (280, 345), (280, 335), (270, 335), (260, 335), (250, 325), (250, 315),
            (240, 315), (240, 305), (230, 305), (230, 295), (220, 295), (220, 285),
            (210, 285), (210, 275), (210, 265), (210, 255), (200, 255), (200, 245),
            (200, 235), (200, 225), (200, 215), (200, 205)
        ]
        
        conversion_dict = {}
        for old_score, new_score in conversion_data:
            if old_score not in conversion_dict:
                conversion_dict[old_score] = new_score
                
        return conversion_dict
    
    def _load_section_percentile_data(self) -> Dict[str, Dict[str, List[int]]]:
        """
        Load GMAT section scaled score to percentile rank data
        Used for Function 2 calculations
        """
        return {
            'Quantitative': {
                'scale': [90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 
                         75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60],
                'percentile': [100, 97, 95, 94, 91, 88, 85, 81, 76, 70, 64, 57, 50, 43, 37, 
                              32, 26, 22, 19, 15, 12, 10, 8, 6, 4, 3, 2, 2, 1, 1, 1]
            },
            'Verbal': {
                'scale': [90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 
                         75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60],
                'percentile': [100, 99, 99, 98, 97, 94, 90, 84, 76, 67, 57, 48, 39, 31, 23, 
                              18, 13, 10, 7, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1]
            },
            'Data Insights': {
                'scale': [90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 
                         75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60],
                'percentile': [100, 100, 99, 99, 99, 98, 97, 96, 93, 89, 84, 77, 70, 63, 54, 
                              48, 42, 36, 31, 26, 21, 18, 15, 12, 10, 8, 7, 6, 5, 4, 4]
            }
        }
    
    def _load_strategy_table(self) -> Dict[Tuple[str, str, str], Dict[str, str]]:
        """
        Load strategy recommendation table based on study status, schedule sufficiency, and score gap
        """
        return {
            ('FullTime', 'Tight', 'Large'): {
                'strategy': '(1) 經過成績單或模考分析，確定強弱科目。\n(2) 把準備時間集中到其中一到兩個重點科目衝到80th，第三科目穩定在50th，以快速提高分數。\n(3) 密集進行多次正式考試，用多次機會衝刺相對高分。',
                'cycle': '每16天（基本方案）'
            },
            ('FullTime', 'Tight', 'Small'): {
                'strategy': '(1) 經過成績單或模考分析，確定所有科目的弱項。\n(2) 針對所有科目的弱項進行專項加強。\n(3) 每4-5天一次模考，快速適應考試狀態。\n(4) 密集進行多次正式考試，用多次機會衝刺相對高分。',
                'cycle': '每16天（基本方案）'
            },
            ('FullTime', 'Sufficient', 'Large'): {
                'strategy': '(1) 除成績單與模考分析外，加做閱讀與邏輯基礎能力檢測。\n(2) 從基礎能力開始進行系統化的知識建構，逐步填補知識缺口。\n(3) 基礎觀念全盤調整後，開始加入速度、熟練度、耐力訓練。\n(4) 每2-3週安排一次模考，並根據模考顯示的強弱項調整學習計劃。',
                'cycle': '每45天（頂級方案）'
            },
            ('FullTime', 'Sufficient', 'Small'): {
                'strategy': '(1) 經過成績單或模考分析，確定所有科目的弱項。\n(2) 針對所有科目的弱項進行專項加強。\n(3) 糾正觀念後，額外進行速度、熟練度與耐力訓練。\n(4) 每1-2週進行模考，根據模考顯示的強弱項調整學習計劃。',
                'cycle': '每30天（進階方案）'
            },
            ('PartTime', 'Tight', 'Large'): {
                'strategy': '透過與考生深度討論申請遇到的挑戰，探索拉長戰線、調整目標分數或增加每日學習時間等方式來克服挑戰。',
                'cycle': '每16-45天（待定方案）'
            },
            ('PartTime', 'Tight', 'Small'): {
                'strategy': '(1) 經過成績單或模考分析，確定所有科目的弱項。\n(2) 平日安排零碎時間，針對最弱勢的科目進行精緻補強，保持學習節奏。\n(3) 每個假日專心進行系統性複習、模考。\n(4) 密集進行多次正式考試，用多次機會衝刺相對高分。',
                'cycle': '每16天（基本方案）'
            },
            ('PartTime', 'Sufficient', 'Large'): {
                'strategy': '(1) 除成績單與模考分析外，加做閱讀與邏輯基礎能力檢測。\n(2) 平日：從基礎能力開始進行系統化的知識建構，逐步填補知識缺口。\n(3) 假日：透過大量做題鍛鍊速度、熟練度、耐力。\n(4) 每2-3週安排一次模考，並根據模考顯示的強弱項調整學習計劃。',
                'cycle': '每45天（頂級方案）'
            },
            ('PartTime', 'Sufficient', 'Small'): {
                'strategy': '(1) 經過成績單或模考分析，確定所有科目的弱項。\n(2) 平日：針對所有科目的弱項進行專項加強。\n(3) 假日：糾正觀念後，額外進行速度、熟練度與耐力訓練。\n(4) 每1-2週進行模考，根據模考顯示的強弱項調整學習計劃。',
                'cycle': '每30天（進階方案）'
            }
        }
    
    def convert_old_to_new_gmat_score(self, old_score: int, target_score_system: str) -> int:
        """
        Convert GMAT 10th Edition score to Focus Edition score
        
        Args:
            old_score: GMAT score in 10th Edition format
            target_score_system: "Old" or "New" indicating the score system
            
        Returns:
            Converted score in Focus Edition format
        """
        logger.info(f"開始分數轉換處理：輸入分數 {old_score}，分數制度 {target_score_system}")
        
        if target_score_system.lower() == "new":
            logger.info("目標分數已為新制，無需轉換")
            return old_score
            
        # Find the closest old score in conversion table
        if old_score in self.gmat_conversion_table:
            new_score = self.gmat_conversion_table[old_score]
            logger.info(f"找到精確對照：舊制 {old_score} 分 -> 新制 {new_score} 分")
            return new_score
        
        # If exact match not found, find the closest lower score
        logger.info(f"未找到精確對照，尋找最接近的較低分數")
        available_old_scores = sorted(self.gmat_conversion_table.keys(), reverse=True)
        for score in available_old_scores:
            if score <= old_score:
                new_score = self.gmat_conversion_table[score]
                logger.info(f"使用最接近對照：舊制 {score} 分 -> 新制 {new_score} 分 (原輸入 {old_score} 分)")
                return new_score
        
        # If no suitable conversion found, return minimum converted score
        min_score = min(self.gmat_conversion_table.values())
        logger.warning(f"無法找到合適對照，返回最低新制分數 {min_score}")
        return min_score
    
    def calculate_target_gap_and_improvement(self, target_gmat_score: int, 
                                           current_highest_gmat_score: int) -> Tuple[int, float]:
        """
        Function 1: Calculate Target Gap and Required Scaled Score Improvement
        計算目標差距與所需提升積分
        
        Args:
            target_gmat_score: Target GMAT score (Focus Edition)
            current_highest_gmat_score: Current highest GMAT score (Focus Edition)
            
        Returns:
            Tuple of (score_gap, required_total_scaled_score_improvement)
        """
        logger.info("===== Function 1: 計算目標差距與所需提升積分 =====")
        logger.info(f"目標分數：{target_gmat_score}")
        logger.info(f"目前最高分數：{current_highest_gmat_score}")
        
        score_gap = target_gmat_score - current_highest_gmat_score
        logger.info(f"分數差距計算：{target_gmat_score} - {current_highest_gmat_score} = {score_gap}")
        
        # 根據規格，總積分提升 = 分數差距 / 6.7
        required_total_scaled_score_improvement = score_gap / 6.7
        logger.info(f"所需積分提升計算：{score_gap} ÷ 6.7 = {required_total_scaled_score_improvement:.2f}")
        
        # 判斷差距大小（根據規格，50分為分界點）
        gap_size = "Large" if score_gap > 50 else "Small"
        logger.info(f"差距程度判定：{gap_size} (基準：50分)")
        
        logger.info("Function 1 計算完成")
        return score_gap, required_total_scaled_score_improvement
    
    def get_percentile_for_score(self, section: str, score: int) -> float:
        """
        Helper function to get percentile for a given section and score
        
        Args:
            section: Section name ('Quantitative', 'Verbal', 'Data Insights')
            score: Scaled score (60-90)
            
        Returns:
            Percentile rank for the given score
        """
        if section not in self.section_percentile_data:
            raise ValueError(f"Invalid section: {section}")
        
        section_data = self.section_percentile_data[section]
        scales = section_data['scale']
        percentiles = section_data['percentile']
        
        # Find exact match or interpolate
        if score in scales:
            index = scales.index(score)
            return percentiles[index]
        
        # If score is outside range, return boundary values
        if score >= max(scales):
            return max(percentiles)
        if score <= min(scales):
            return min(percentiles)
        
        # Linear interpolation for scores between available data points
        for i in range(len(scales) - 1):
            if scales[i+1] <= score <= scales[i]:
                # Linear interpolation
                x1, y1 = scales[i+1], percentiles[i+1]
                x2, y2 = scales[i], percentiles[i]
                
                # Calculate interpolated percentile
                percentile = y1 + (y2 - y1) * (score - x1) / (x2 - x1)
                return percentile
        
        return 0.0  # Fallback
    
    def calculate_section_slope(self, section: str, current_score: int) -> float:
        """
        Calculate slope (ROI) for a section based on current score
        計算各科目的投報率斜率
        
        Args:
            section: Section name ('Quantitative', 'Verbal', 'Data Insights')
            current_score: Current scaled score for the section
            
        Returns:
            Slope value (percentile improvement per 1 scaled score point)
        """
        if current_score >= 90:
            return 0.0  # Cannot improve beyond maximum score
        
        current_percentile = self.get_percentile_for_score(section, current_score)
        next_score_percentile = self.get_percentile_for_score(section, current_score + 1)
        
        slope = next_score_percentile - current_percentile
        return max(0.0, slope)  # Ensure non-negative slope
    
    def round_to_half_hour(self, hours: float) -> float:
        """
        Round hours to the nearest 0.5 hour
        將時數四捨五入到最接近的0.5小時
        
        Args:
            hours: Time in hours
            
        Returns:
            Rounded time to nearest 0.5 hour
        """
        return round(hours * 2) / 2
    
    def analyze_section_roi_and_time_allocation(self, current_section_scores: Dict[str, int],
                                               weekday_study_hours: float = None,
                                               weekend_study_hours: float = None) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Function 2: Analyze Subject ROI and Recommend Time Allocation Ratio
        分析科目投報率並建議時間分配比例
        
        Args:
            current_section_scores: Dictionary with current scores for each section
                                  Format: {'Quantitative': score, 'Verbal': score, 'Data Insights': score}
            weekday_study_hours: Optional weekday study hours for calculating actual time allocation
            weekend_study_hours: Optional weekend study hours for calculating actual time allocation
            
        Returns:
            Tuple of:
            - Dictionary with recommended time allocation percentages for each section
            - Dictionary with actual study time allocation (if hours provided)
        """
        logger.info("===== Function 2: 分析科目投報率並建議時間分配 =====")
        
        # Validate input
        required_sections = ['Quantitative', 'Verbal', 'Data Insights']
        logger.info("驗證輸入數據...")
        for section in required_sections:
            if section not in current_section_scores:
                error_msg = f"Missing section score for {section}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            score = current_section_scores[section]
            if not (60 <= score <= 90):
                error_msg = f"Invalid score for {section}: {score}. Must be between 60-90"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"{section} 目前積分：{score}")
        
        # Calculate slopes for each section
        logger.info("開始計算各科目投報率斜率...")
        slopes = {}
        for section in required_sections:
            current_score = current_section_scores[section]
            slope = self.calculate_section_slope(section, current_score)
            slopes[section] = slope
            
            current_percentile = self.get_percentile_for_score(section, current_score)
            if current_score < 90:
                next_percentile = self.get_percentile_for_score(section, current_score + 1)
                logger.info(f"{section}: 積分 {current_score} (百分位 {current_percentile:.1f}) -> 積分 {current_score + 1} (百分位 {next_percentile:.1f}), 斜率 {slope:.1f}")
            else:
                logger.info(f"{section}: 積分 {current_score} (百分位 {current_percentile:.1f}) 已達最高，斜率 {slope:.1f}")
        
        # Calculate total slope
        total_slope = sum(slopes.values())
        logger.info(f"總斜率計算：{' + '.join([f'{s:.1f}' for s in slopes.values()])} = {total_slope:.1f}")
        
        # Calculate time allocation percentages
        logger.info("根據投報率計算時間分配...")
        time_allocation = {}
        if total_slope > 0:
            for section in required_sections:
                percentage = (slopes[section] / total_slope) * 100
                time_allocation[section] = percentage
                logger.info(f"{section} 時間分配：{slopes[section]:.1f} ÷ {total_slope:.1f} × 100% = {percentage:.1f}%")
        else:
            # If all slopes are 0 (all sections at max score), allocate equally
            equal_allocation = 100 / len(required_sections)
            logger.info("所有科目斜率為0，採用平均分配")
            for section in required_sections:
                time_allocation[section] = equal_allocation
                logger.info(f"{section} 時間分配：{equal_allocation:.1f}% (平均分配)")
        
        # Calculate actual time allocation
        actual_time_allocation = {}
        if weekday_study_hours is not None and weekend_study_hours is not None:
            logger.info("計算各科目實際學習時間分配...")
            for section in required_sections:
                percentage = time_allocation[section] / 100
                weekday_hours = self.round_to_half_hour(percentage * weekday_study_hours)
                weekend_hours = self.round_to_half_hour(percentage * weekend_study_hours)
                
                actual_time_allocation[section] = {
                    'weekday': weekday_hours,
                    'weekend': weekend_hours
                }
                logger.info(f"{section} 實際時間分配 - 平日: {weekday_hours:.1f}小時, 假日: {weekend_hours:.1f}小時")
        
        logger.info("Function 2 計算完成")
        return time_allocation, actual_time_allocation
    
    def assess_gmat_preparation_schedule(self, application_deadline: str, 
                                       language_test_status: str, 
                                       application_materials_progress: float, 
                                       study_status: str) -> Tuple[str, int]:
        """
        Function 3: Assess GMAT Preparation Schedule Sufficiency
        評估GMAT準備時程寬裕度
        
        Args:
            application_deadline: Application deadline in YYYY-MM-DD format
            language_test_status: "已完成" (Completed) or "準備中" (In Progress)
            application_materials_progress: Application materials completion percentage (0-100)
            study_status: "全職考生" (FullTime) or "在職考生" (PartTime)
            
        Returns:
            Tuple of (is_schedule_sufficient, gmat_prep_days_available)
        """
        logger.info("===== Function 3: 評估GMAT準備時程寬裕度 =====")
        logger.info(f"申請截止日期：{application_deadline}")
        logger.info(f"語言考試狀態：{language_test_status}")
        logger.info(f"申請資料完成度：{application_materials_progress}%")
        logger.info(f"備考身份：{study_status}")
        
        # Parse application deadline
        try:
            deadline = datetime.strptime(application_deadline, "%Y-%m-%d")
            logger.info(f"申請截止日期解析成功：{deadline.strftime('%Y年%m月%d日')}")
        except ValueError:
            error_msg = f"Invalid date format: {application_deadline}. Use YYYY-MM-DD format."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Calculate application preparation time needed
        logger.info("計算申請準備時間需求...")
        app_prep_time_needed = 0
        
        language_incomplete = language_test_status.lower() in ["未完成", "not completed", "準備中", "in progress"]
        materials_incomplete = application_materials_progress < 100
        
        if language_incomplete or materials_incomplete:
            logger.info("語言考試或申請資料未完成，需要額外申請準備時間")
            
            # Calculate base preparation time
            if study_status.lower() in ["在職考生", "parttime"]:
                base_prep_time = 3  # 3 months
                logger.info("在職考生基礎申請準備時間：3個月")
            else:  # FullTime
                base_prep_time = 2.5  # 2.5 months
                logger.info("全職考生基礎申請準備時間：2.5個月")
            
            # Apply discount based on application materials progress
            if application_materials_progress == 0:
                app_prep_time_needed = base_prep_time
                logger.info(f"申請資料完成度0%，使用完整基礎時間：{app_prep_time_needed}個月")
            else:
                discount_factor = 1 - (application_materials_progress / 100)
                app_prep_time_needed = base_prep_time * discount_factor
                logger.info(f"申請資料完成度{application_materials_progress}%，折扣係數{discount_factor:.2f}，調整後時間：{app_prep_time_needed:.2f}個月")
        else:
            logger.info("語言考試和申請資料均已完成，無需額外申請準備時間")
        
        # Calculate GMAT latest finish date
        gmat_latest_finish_date = deadline - timedelta(days=app_prep_time_needed * 30)
        logger.info(f"GMAT最晚完成日期：{gmat_latest_finish_date.strftime('%Y年%m月%d日')} (申請截止前 {app_prep_time_needed} 個月)")
        
        # Get current date
        current_date = datetime.now()
        logger.info(f"當前日期：{current_date.strftime('%Y年%m月%d日')}")
        
        # Calculate GMAT preparation days available
        gmat_prep_days_available = (gmat_latest_finish_date - current_date).days
        logger.info(f"GMAT可用準備天數：{gmat_prep_days_available} 天")
        
        # Determine schedule sufficiency (根據規格，60天為分界點)
        if gmat_prep_days_available > 60:
            is_schedule_sufficient = "Sufficient"
            logger.info("時程判定：Sufficient (可用天數 > 60天)")
        else:
            is_schedule_sufficient = "Tight"
            logger.info("時程判定：Tight (可用天數 ≤ 60天)")
        
        logger.info("Function 3 計算完成")
        return is_schedule_sufficient, gmat_prep_days_available
    
    def assess_daily_study_time_sufficiency(self, study_status: str, 
                                          weekday_study_hours: float, 
                                          weekend_study_hours: float) -> Tuple[str, float]:
        """
        Function 4: Assess Daily Study Time Sufficiency
        評估每日準備時間充裕度
        
        Args:
            study_status: "全職考生" (FullTime) or "在職考生" (PartTime)
            weekday_study_hours: Daily study hours on weekdays
            weekend_study_hours: Daily study hours on weekends
            
        Returns:
            Tuple of (is_time_sufficient, weekly_study_hours)
        """
        logger.info("===== Function 4: 評估每日準備時間充裕度 =====")
        logger.info(f"備考身份：{study_status}")
        logger.info(f"平日每日學習時間：{weekday_study_hours} 小時")
        logger.info(f"假日每日學習時間：{weekend_study_hours} 小時")
        
        # Calculate weekly total study hours
        weekly_study_hours = (weekday_study_hours * 5) + (weekend_study_hours * 2)
        logger.info(f"每週總學習時數計算：({weekday_study_hours} × 5) + ({weekend_study_hours} × 2) = {weekly_study_hours} 小時")
        
        # Determine time sufficiency
        logger.info("根據備考身份判定時間充裕度...")
        if study_status.lower() in ["全職考生", "fulltime"]:
            is_time_sufficient = "Sufficient"
            logger.info("全職考生：時間充裕度判定為 Sufficient")
        elif study_status.lower() in ["在職考生", "parttime"]:
            logger.info("在職考生：檢查時間標準...")
            logger.info("標準：平日 ≥ 4小時 且 假日 ≥ 8小時")
            
            weekday_sufficient = weekday_study_hours >= 4
            weekend_sufficient = weekend_study_hours >= 8
            
            logger.info(f"平日時間檢查：{weekday_study_hours} ≥ 4 = {weekday_sufficient}")
            logger.info(f"假日時間檢查：{weekend_study_hours} ≥ 8 = {weekend_sufficient}")
            
            if weekday_sufficient and weekend_sufficient:
                is_time_sufficient = "Sufficient"
                logger.info("在職考生：兩項標準均達成，時間充裕度判定為 Sufficient")
            else:
                is_time_sufficient = "Insufficient"
                logger.info("在職考生：未達成時間標準，時間充裕度判定為 Insufficient")
        else:
            error_msg = f"Invalid study_status: {study_status}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Function 4 計算完成")
        return is_time_sufficient, weekly_study_hours
    
    def comprehensive_diagnosis_and_recommendation(self, score_gap: int, 
                                                 is_schedule_sufficient: str, 
                                                 is_time_sufficient: str, 
                                                 study_status: str,
                                                 recommended_section_time_allocation: Dict[str, float],
                                                 actual_time_allocation: Dict[str, Dict[str, float]] = None) -> Dict[str, str]:
        """
        Function 5: Comprehensive Diagnosis and Recommendation Output
        綜合診斷與建議輸出
        
        Args:
            score_gap: Score gap from Function 1
            is_schedule_sufficient: Schedule sufficiency from Function 3
            is_time_sufficient: Time sufficiency from Function 4
            study_status: Study status (FullTime/PartTime)
            recommended_section_time_allocation: Time allocation from Function 2
            actual_time_allocation: Actual time allocation in hours from Function 2
            
        Returns:
            Dictionary containing comprehensive recommendations
        """
        logger.info("===== Function 5: 綜合診斷與建議輸出 =====")
        logger.info(f"分數差距：{score_gap}")
        logger.info(f"時程寬裕度：{is_schedule_sufficient}")
        logger.info(f"時間充裕度：{is_time_sufficient}")
        logger.info(f"備考身份：{study_status}")
        
        # Determine score gap size
        score_gap_size = "Large" if score_gap > 50 else "Small"
        logger.info(f"分數差距分類：{score_gap_size} (基準：50分)")
        
        # Normalize study status
        normalized_study_status = "FullTime" if study_status.lower() in ["全職考生", "fulltime"] else "PartTime"
        logger.info(f"備考身份標準化：{study_status} -> {normalized_study_status}")
        
        # Create lookup key for strategy table
        lookup_key = (normalized_study_status, is_schedule_sufficient, score_gap_size)
        logger.info(f"策略查詢鍵值：{lookup_key}")
        
        # Get recommendation from strategy table
        if lookup_key in self.strategy_recommendation_table:
            recommendation = self.strategy_recommendation_table[lookup_key]
            recommended_study_strategy = recommendation['strategy']
            recommended_exam_cycle = recommendation['cycle']
            logger.info(f"找到匹配策略：考試週期 {recommended_exam_cycle}")
            logger.info("策略內容已取得")
        else:
            # Fallback recommendation
            logger.warning(f"未找到匹配策略鍵值 {lookup_key}，使用備用建議")
            recommended_study_strategy = "請與教學顧問進一步討論，制定個性化學習策略。"
            recommended_exam_cycle = "待定"
        
        # Format time allocation recommendation
        logger.info("格式化時間分配建議...")
        time_allocation_str = ""
        for section, percentage in recommended_section_time_allocation.items():
            time_allocation_str += f"{section}: {percentage:.1f}%\n"
            logger.info(f"時間分配 - {section}: {percentage:.1f}%")
        
        # Format actual time allocation if available
        actual_time_str = ""
        if actual_time_allocation:
            logger.info("格式化實際時間分配...")
            for section, times in actual_time_allocation.items():
                weekday_hours = times['weekday']
                weekend_hours = times['weekend']
                actual_time_str += f"{section}: 平日 {weekday_hours:.1f}小時, 假日 {weekend_hours:.1f}小時\n"
                logger.info(f"實際時間 - {section}: 平日 {weekday_hours:.1f}小時, 假日 {weekend_hours:.1f}小時")
        
        result = {
            "recommended_exam_cycle": recommended_exam_cycle,
            "recommended_study_strategy": recommended_study_strategy,
            "recommended_section_time_allocation": time_allocation_str.strip(),
            "actual_study_time_allocation": actual_time_str.strip() if actual_time_str else "未提供學習時間資訊",
            "score_gap_analysis": f"目標與現有分數差距: {score_gap}分 (差距程度: {score_gap_size})",
            "schedule_analysis": f"時程寬裕度: {is_schedule_sufficient}",
            "time_sufficiency_analysis": f"每日時間充裕度: {is_time_sufficient}"
        }
        
        logger.info("Function 5 計算完成")
        return result
    
    def validate_inputs(self, input_data: Dict) -> Dict:
        """
        Validate and normalize input parameters
        驗證和標準化輸入參數
        
        Args:
            input_data: Dictionary containing all input parameters
            
        Returns:
            Validated and normalized input data
            
        Raises:
            ValueError: If any input is invalid
        """
        required_fields = [
            'target_gmat_score', 'target_score_system', 'current_highest_gmat_score',
            'application_deadline', 'language_test_status', 'application_materials_progress',
            'study_status', 'weekday_study_hours', 'weekend_study_hours', 'current_section_scores'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        
        validated_data = input_data.copy()
        
        # Validate target_gmat_score
        if not (200 <= validated_data['target_gmat_score'] <= 805):
            raise ValueError("target_gmat_score must be between 200 and 805")
        
        # Validate and convert target_score_system
        if validated_data['target_score_system'].lower() not in ['old', 'new']:
            raise ValueError("target_score_system must be 'Old' or 'New'")
        
        # Convert old score to new if necessary
        validated_data['target_gmat_score'] = self.convert_old_to_new_gmat_score(
            validated_data['target_gmat_score'], 
            validated_data['target_score_system']
        )
        
        # Validate current_highest_gmat_score
        if not (200 <= validated_data['current_highest_gmat_score'] <= 805):
            raise ValueError("current_highest_gmat_score must be between 200 and 805")
        
        # Validate application_materials_progress
        if not (0 <= validated_data['application_materials_progress'] <= 100):
            raise ValueError("application_materials_progress must be between 0 and 100")
        
        # Validate study hours
        if validated_data['weekday_study_hours'] < 0 or validated_data['weekend_study_hours'] < 0:
            raise ValueError("Study hours cannot be negative")
        
        # Validate current_section_scores
        required_sections = ['Quantitative', 'Verbal', 'Data Insights']
        for section in required_sections:
            if section not in validated_data['current_section_scores']:
                raise ValueError(f"Missing section score for {section}")
            
            score = validated_data['current_section_scores'][section]
            if not (60 <= score <= 90):
                raise ValueError(f"Invalid {section} score: {score}. Must be between 60-90")
        
        # Validate language_test_status
        valid_language_statuses = ['已完成', '未完成', 'completed', 'not completed']
        if validated_data['language_test_status'] not in valid_language_statuses:
            raise ValueError(f"Invalid language_test_status: {validated_data['language_test_status']}")
        
        return validated_data
    
    def generate_study_plan(self, input_data: Dict) -> Dict:
        """
        Main function to generate comprehensive GMAT study plan
        主要函數：生成綜合GMAT學習計劃
        
        Args:
            input_data: Dictionary containing all required input parameters
            
        Returns:
            Dictionary containing comprehensive study plan recommendations
        """
        try:
            # Validate inputs
            validated_data = self.validate_inputs(input_data)
            
            # Function 1: Calculate target gap and improvement
            score_gap, required_improvement = self.calculate_target_gap_and_improvement(
                validated_data['target_gmat_score'],
                validated_data['current_highest_gmat_score']
            )
            
            # Function 2: Analyze section ROI and time allocation
            time_allocation, actual_time_allocation = self.analyze_section_roi_and_time_allocation(
                validated_data['current_section_scores'],
                validated_data['weekday_study_hours'],
                validated_data['weekend_study_hours']
            )
            
            # Function 3: Assess GMAT preparation schedule
            schedule_sufficient, prep_days = self.assess_gmat_preparation_schedule(
                validated_data['application_deadline'],
                validated_data['language_test_status'],
                validated_data['application_materials_progress'],
                validated_data['study_status']
            )
            
            # Function 4: Assess daily study time sufficiency
            time_sufficient, weekly_hours = self.assess_daily_study_time_sufficiency(
                validated_data['study_status'],
                validated_data['weekday_study_hours'],
                validated_data['weekend_study_hours']
            )
            
            # Function 5: Comprehensive diagnosis and recommendation
            final_recommendations = self.comprehensive_diagnosis_and_recommendation(
                score_gap,
                schedule_sufficient,
                time_sufficient,
                validated_data['study_status'],
                time_allocation,
                actual_time_allocation
            )
            
            # Add additional information to the output
            final_recommendations.update({
                "required_score_improvement": f"{required_improvement:.1f} 積分",
                "available_preparation_days": f"{prep_days} 天",
                "weekly_study_hours": f"{weekly_hours:.1f} 小時/週",
                "input_summary": {
                    "目標分數": f"{validated_data['target_gmat_score']} ({validated_data['target_score_system']})",
                    "目前分數": validated_data['current_highest_gmat_score'],
                    "分數差距": score_gap,
                    "申請截止日期": validated_data['application_deadline'],
                    "備考身份": validated_data['study_status'],
                    "語言考試狀態": validated_data['language_test_status'],
                    "申請資料完成度": f"{validated_data['application_materials_progress']}%"
                }
            })
            
            return final_recommendations
            
        except Exception as e:
            return {
                "error": f"計劃生成失敗: {str(e)}",
                "recommendations": "請檢查輸入參數並重試，或聯繫教學顧問獲得幫助。"
            }
    
    def print_study_plan(self, recommendations: Dict) -> None:
        """
        Print study plan in a formatted way
        格式化打印學習計劃
        
        Args:
            recommendations: Study plan recommendations from generate_study_plan
        """
        print("=" * 80)
        print("GMAT 讀書計畫自動化規劃系統 - 分析結果")
        print("GMAT Study Plan Automation System - Analysis Results")
        print("=" * 80)
        
        if "error" in recommendations:
            print(f"錯誤: {recommendations['error']}")
            print(f"建議: {recommendations['recommendations']}")
            logger.error(f"學習計劃生成失敗: {recommendations['error']}")
            return
        
        logger.info("開始輸出學習計劃結果")
        
        # Input Summary
        print("\n輸入參數摘要 (Input Summary):")
        print("-" * 40)
        for key, value in recommendations.get("input_summary", {}).items():
            print(f"{key}: {value}")
        
        # Analysis Results
        print(f"\n分析結果 (Analysis Results):")
        print("-" * 40)
        print(f"目標差距分析: {recommendations.get('score_gap_analysis', 'N/A')}")
        print(f"時程寬裕度: {recommendations.get('schedule_analysis', 'N/A')}")
        print(f"時間充裕度: {recommendations.get('time_sufficiency_analysis', 'N/A')}")
        print(f"所需積分提升: {recommendations.get('required_score_improvement', 'N/A')}")
        print(f"可用準備天數: {recommendations.get('available_preparation_days', 'N/A')}")
        print(f"每週學習時數: {recommendations.get('weekly_study_hours', 'N/A')}")
        
        # Recommendations
        print(f"\n建議考試週期 (Recommended Exam Cycle):")
        print("-" * 40)
        print(recommendations.get('recommended_exam_cycle', 'N/A'))
        
        print(f"\n建議學習策略 (Recommended Study Strategy):")
        print("-" * 40)
        print(recommendations.get('recommended_study_strategy', 'N/A'))
        
        print(f"\n建議科目時間分配 (Recommended Section Time Allocation):")
        print("-" * 40)
        print(recommendations.get('recommended_section_time_allocation', 'N/A'))
        
        print(f"\n實際學習時間分配 (Actual Study Time Allocation):")
        print("-" * 40)
        print(recommendations.get('actual_study_time_allocation', 'N/A'))
        
        print("=" * 80)
        logger.info("學習計劃結果輸出完成")


def get_user_input():
    """
    Interactive function to collect user input step by step
    互動式收集用戶輸入的函數
    
    Returns:
        Dictionary containing all user input data
    """
    print("\nGMAT 學習計劃生成器 - 參數輸入")
    print("GMAT Study Plan Generator - Parameter Input")
    print("=" * 60)
    print("請按照提示逐步輸入您的資訊 (Please enter your information step by step)")
    print("=" * 60)
    
    logger.info("開始互動式參數收集流程")
    input_data = {}
    
    # 1. Target GMAT Score
    while True:
        try:
            print("\n1. 目標 GMAT 分數 (Target GMAT Score)")
            print("   範圍: 200-805")
            target_score = int(input("   請輸入目標分數: "))
            if 200 <= target_score <= 805:
                input_data['target_gmat_score'] = target_score
                logger.info(f"用戶輸入目標分數: {target_score}")
                break
            else:
                print("   分數必須在 200-805 之間，請重新輸入")
                logger.warning(f"無效目標分數: {target_score} (超出範圍)")
        except ValueError:
            print("   請輸入有效的數字")
            logger.warning("目標分數輸入格式錯誤")
    
    # 2. Target Score System
    while True:
        print("\n2. 分數制度 (Score System)")
        print("   選項: Old (舊制) / New (新制)")
        system = input("   請輸入分數制度 [Old/New]: ").strip()
        if system.lower() in ['old', 'new', '舊制', '新制']:
            if system.lower() in ['old', '舊制']:
                input_data['target_score_system'] = 'Old'
                logger.info("用戶選擇分數制度: Old (舊制)")
            else:
                input_data['target_score_system'] = 'New'
                logger.info("用戶選擇分數制度: New (新制)")
            break
        else:
            print("   請輸入 Old 或 New")
            logger.warning(f"無效分數制度輸入: {system}")
    
    # 3. Current Highest GMAT Score
    while True:
        try:
            print("\n3. 目前最高 GMAT 分數 (Current Highest GMAT Score)")
            print("   範圍: 200-805")
            current_score = int(input("   請輸入目前最高分數: "))
            if 200 <= current_score <= 805:
                input_data['current_highest_gmat_score'] = current_score
                logger.info(f"用戶輸入目前分數: {current_score}")
                break
            else:
                print("   分數必須在 200-805 之間，請重新輸入")
                logger.warning(f"無效目前分數: {current_score} (超出範圍)")
        except ValueError:
            print("   請輸入有效的數字")
            logger.warning("目前分數輸入格式錯誤")
    
    # 4. Application Deadline
    while True:
        print("\n4. 申請截止日期 (Application Deadline)")
        print("   格式: YYYY-MM-DD (例如: 2025-12-01)")
        deadline = input("   請輸入申請截止日期: ").strip()
        try:
            # Validate date format
            from datetime import datetime
            datetime.strptime(deadline, "%Y-%m-%d")
            input_data['application_deadline'] = deadline
            logger.info(f"用戶輸入申請截止日期: {deadline}")
            break
        except ValueError:
            print("   日期格式錯誤，請使用 YYYY-MM-DD 格式")
            logger.warning(f"無效日期格式: {deadline}")
    
    # 5. Language Test Status
    while True:
        print("\n5. 語言考試準備狀態 (Language Test Status)")
        print("   問題: 語言考試(如托福/雅思)是否已完成？")
        status = input("   請回答 [Y/N]: ").strip().upper()
        if status in ['Y', 'YES', 'N', 'NO']:
            if status in ['Y', 'YES']:
                input_data['language_test_status'] = '已完成'
                logger.info("用戶輸入語言考試狀態: 已完成")
            else:
                input_data['language_test_status'] = '未完成'
                logger.info("用戶輸入語言考試狀態: 未完成")
            break
        else:
            print("   請輸入 Y 或 N")
            logger.warning(f"無效語言考試狀態: {status}")
    
    # 6. Application Materials Progress
    while True:
        try:
            print("\n6. 申請資料完成度 (Application Materials Progress)")
            print("   範圍: 0-100%")
            progress = float(input("   請輸入完成百分比 (0-100): "))
            if 0 <= progress <= 100:
                input_data['application_materials_progress'] = progress
                logger.info(f"用戶輸入申請資料完成度: {progress}%")
                break
            else:
                print("   百分比必須在 0-100 之間，請重新輸入")
                logger.warning(f"無效申請資料完成度: {progress} (超出範圍)")
        except ValueError:
            print("   請輸入有效的數字")
            logger.warning("申請資料完成度輸入格式錯誤")
    
    # 7. Study Status
    while True:
        print("\n7. 備考身份 (Study Status)")
        print("   選項: 全職考生 / 在職考生")
        status = input("   請輸入備考身份 [全職考生/在職考生]: ").strip()
        if status in ['全職考生', '在職考生', 'fulltime', 'parttime']:
            input_data['study_status'] = status
            logger.info(f"用戶輸入備考身份: {status}")
            break
        else:
            print("   請輸入 全職考生 或 在職考生")
            logger.warning(f"無效備考身份: {status}")
    
    # 8. Weekday Study Hours
    while True:
        try:
            print("\n8. 平日每日學習時間 (Weekday Study Hours)")
            print("   單位: 小時/天")
            hours = float(input("   請輸入平日每天可學習時數: "))
            if hours >= 0:
                input_data['weekday_study_hours'] = hours
                logger.info(f"用戶輸入平日學習時間: {hours} 小時/天")
                break
            else:
                print("   學習時間不能為負數，請重新輸入")
                logger.warning(f"無效平日學習時間: {hours} (負數)")
        except ValueError:
            print("   請輸入有效的數字")
            logger.warning("平日學習時間輸入格式錯誤")
    
    # 9. Weekend Study Hours
    while True:
        try:
            print("\n9. 假日每日學習時間 (Weekend Study Hours)")
            print("   單位: 小時/天")
            hours = float(input("   請輸入假日每天可學習時數: "))
            if hours >= 0:
                input_data['weekend_study_hours'] = hours
                logger.info(f"用戶輸入假日學習時間: {hours} 小時/天")
                break
            else:
                print("   學習時間不能為負數，請重新輸入")
                logger.warning(f"無效假日學習時間: {hours} (負數)")
        except ValueError:
            print("   請輸入有效的數字")
            logger.warning("假日學習時間輸入格式錯誤")
    
    # 10. Current Section Scores
    print("\n10. 各科目目前積分 (Current Section Scores)")
    print("    範圍: 60-90 分")
    
    sections = ['Quantitative', 'Verbal', 'Data Insights']
    section_names_zh = ['數學 (Quantitative)', '語文 (Verbal)', '數據洞察 (Data Insights)']
    current_section_scores = {}
    
    for i, (section, section_zh) in enumerate(zip(sections, section_names_zh), 1):
        while True:
            try:
                print(f"\n    10.{i} {section_zh}")
                score = int(input(f"    請輸入 {section} 目前積分 (60-90): "))
                if 60 <= score <= 90:
                    current_section_scores[section] = score
                    logger.info(f"用戶輸入 {section} 積分: {score}")
                    break
                else:
                    print("    積分必須在 60-90 之間，請重新輸入")
                    logger.warning(f"無效 {section} 積分: {score} (超出範圍)")
            except ValueError:
                print("    請輸入有效的數字")
                logger.warning(f"{section} 積分輸入格式錯誤")
    
    input_data['current_section_scores'] = current_section_scores
    
    # Summary
    print("\n" + "=" * 60)
    print("輸入摘要確認 (Input Summary)")
    print("=" * 60)
    print(f"目標分數: {input_data['target_gmat_score']} ({input_data['target_score_system']})")
    print(f"目前分數: {input_data['current_highest_gmat_score']}")
    print(f"申請截止: {input_data['application_deadline']}")
    print(f"語言考試: {input_data['language_test_status']}")
    print(f"申請資料: {input_data['application_materials_progress']}%")
    print(f"備考身份: {input_data['study_status']}")
    print(f"平日學習: {input_data['weekday_study_hours']} 小時/天")
    print(f"假日學習: {input_data['weekend_study_hours']} 小時/天")
    print("各科積分:")
    for section, score in input_data['current_section_scores'].items():
        print(f"  {section}: {score}")
    
    logger.info("顯示輸入摘要供用戶確認")
    
    while True:
        confirm = input("\n確認以上資訊正確嗎？[Y/n]: ").strip().lower()
        if confirm in ['y', 'yes', '', '是', '確認']:
            logger.info("用戶確認輸入資訊正確")
            return input_data
        elif confirm in ['n', 'no', '否', '不是']:
            print("請重新開始輸入...")
            logger.info("用戶選擇重新輸入")
            return get_user_input()  # Recursive call to start over
        else:
            print("請輸入 Y 或 N")
            logger.warning(f"無效確認輸入: {confirm}")


def main():
    """
    Interactive command line interface for GMAT Study Planner
    GMAT學習規劃器的互動式命令行接口
    """
    print("歡迎使用 GMAT 讀書計畫自動化規劃系統!")
    print("Welcome to GMAT Study Plan Automation System!")
    print("=" * 80)
    print("本系統將根據您的個人情況生成個性化的GMAT學習計劃")
    print("This system will generate personalized GMAT study plans based on your situation")
    print("=" * 80)
    
    logger.info("GMAT學習規劃系統啟動")
    
    try:
        # Get user input interactively
        logger.info("開始收集用戶輸入")
        input_data = get_user_input()
        
        # Create planner instance
        logger.info("創建規劃器實例")
        planner = GMATStudyPlanner()
        
        print("\n正在分析您的資料並生成學習計劃...")
        print("Analyzing your data and generating study plan...")
        
        logger.info("開始生成學習計劃")
        
        # Generate study plan
        recommendations = planner.generate_study_plan(input_data)
        
        logger.info("學習計劃生成完成")
        
        # Print results
        planner.print_study_plan(recommendations)
        
        # Ask if user wants to save results
        while True:
            save_choice = input("\n是否要將結果保存到文件？[Y/n]: ").strip().lower()
            if save_choice in ['y', 'yes', '', '是']:
                try:
                    import json
                    from datetime import datetime
                    
                    # Create filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"gmat_study_plan_{timestamp}.json"
                    
                    # Save to file
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(recommendations, f, ensure_ascii=False, indent=2)
                    
                    print(f"結果已保存到: {filename}")
                    logger.info(f"學習計劃結果已保存到文件: {filename}")
                    break
                except Exception as e:
                    print(f"保存失敗: {str(e)}")
                    logger.error(f"文件保存失敗: {str(e)}")
                    break
            elif save_choice in ['n', 'no', '否']:
                print("結果未保存")
                logger.info("用戶選擇不保存結果")
                break
            else:
                print("請輸入 Y 或 N")
        
        # Ask if user wants to run another analysis
        while True:
            repeat_choice = input("\n是否要為其他學生生成計劃？[Y/n]: ").strip().lower()
            if repeat_choice in ['y', 'yes', '', '是']:
                print("\n" + "="*80)
                logger.info("用戶選擇進行另一次分析")
                main()  # Recursive call for another analysis
                break
            elif repeat_choice in ['n', 'no', '否']:
                print("\n感謝使用 GMAT 學習規劃系統！")
                print("Thank you for using GMAT Study Planning System!")
                logger.info("系統正常結束")
                break
            else:
                print("請輸入 Y 或 N")
                
    except KeyboardInterrupt:
        print("\n\n程序被用戶中斷")
        print("Program interrupted by user")
        logger.info("程序被用戶中斷")
    except Exception as e:
        print(f"\n程序執行錯誤: {str(e)}")
        print("Program execution error")
        print("請檢查輸入並重試，或聯繫技術支援")
        logger.error(f"程序執行錯誤: {str(e)}")


if __name__ == "__main__":
    main() 