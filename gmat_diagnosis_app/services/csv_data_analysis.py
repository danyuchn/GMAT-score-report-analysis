"""
CSV Data Analysis for GMAT Diagnosis App

This module provides functions to analyze GMAT diagnosis data stored in CSV files.
"""

from typing import List, Dict, Any
from collections import defaultdict

# Import the CSV data service module
from gmat_diagnosis_app.services.csv_data_service import (
    get_all_gmat_performance_records,
    get_all_subjective_report_records,
    get_student_gmat_performance_records,
    get_student_section_performance_records,
    get_test_instance_gmat_performance_records,
    get_student_subjective_reports
)


def calculate_student_section_stats(student_id: str, gmat_section: str) -> Dict[str, Any]:
    """
    Calculate statistics for a specific student and GMAT section.
    
    Args:
        student_id: The ID of the student to calculate statistics for
        gmat_section: The section to calculate statistics for ('Q', 'DI', or 'V')
        
    Returns:
        Dictionary containing the calculated statistics
    """
    section_records = get_student_section_performance_records(student_id, gmat_section)
    
    if not section_records:
        return {
            "student_id": student_id,
            "gmat_section": gmat_section,
            "total_tests": 0,
            "message": "No records found for this student and section"
        }
    
    # Group records by test_instance_id
    test_instances = defaultdict(list)
    for record in section_records:
        test_instances[record["test_instance_id"]].append(record)
    
    # Calculate statistics for each test instance
    test_stats = []
    for test_id, records in test_instances.items():
        correct_count = sum(1 for r in records if r["is_correct"] == '1')
        total_questions = len(records)
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        
        # Calculate average question time
        try:
            avg_question_time = sum(float(r["question_time_minutes"]) for r in records) / total_questions
        except (ValueError, ZeroDivisionError):
            avg_question_time = 0
        
        # Calculate test date
        test_date = records[0]["test_date"] if records else "Unknown"
        
        test_stats.append({
            "test_instance_id": test_id,
            "test_date": test_date,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "avg_question_time_minutes": avg_question_time
        })
    
    # Calculate overall statistics
    total_questions = sum(stats["total_questions"] for stats in test_stats)
    total_correct = sum(stats["correct_count"] for stats in test_stats)
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
    avg_test_accuracy = sum(stats["accuracy"] for stats in test_stats) / len(test_stats)
    
    # Sort test instances by date
    test_stats.sort(key=lambda x: x["test_date"], reverse=True)
    
    return {
        "student_id": student_id,
        "gmat_section": gmat_section,
        "total_tests": len(test_stats),
        "total_questions_answered": total_questions,
        "total_correct_answers": total_correct,
        "overall_accuracy": overall_accuracy,
        "avg_test_accuracy": avg_test_accuracy,
        "test_instances": test_stats
    }


def analyze_time_pressure_impact(student_id: str) -> Dict[str, Any]:
    """
    Analyze the impact of subjective time pressure on student performance.
    
    Args:
        student_id: The ID of the student to analyze
        
    Returns:
        Dictionary containing the analysis results
    """
    # Get student's performance records
    performance_records = get_student_gmat_performance_records(student_id)
    
    # Get student's subjective reports
    subjective_reports = get_student_subjective_reports(student_id)
    
    if not performance_records or not subjective_reports:
        return {
            "student_id": student_id,
            "analysis_complete": False,
            "message": "Insufficient data for analysis"
        }
    
    # Create lookup dictionary for subjective reports
    report_lookup = {
        report["test_instance_id"]: report
        for report in subjective_reports
    }
    
    # Group performance records by test_instance_id
    test_instances = defaultdict(list)
    for record in performance_records:
        test_instances[record["test_instance_id"]].append(record)
    
    # Analyze performance with and without time pressure
    pressure_results = {
        "with_pressure": {
            "count": 0,
            "total_questions": 0,
            "correct_count": 0,
            "avg_question_time": 0,
            "section_counts": {"Q": 0, "DI": 0, "V": 0}
        },
        "without_pressure": {
            "count": 0,
            "total_questions": 0,
            "correct_count": 0,
            "avg_question_time": 0,
            "section_counts": {"Q": 0, "DI": 0, "V": 0}
        }
    }
    
    # Calculate statistics for each test instance
    for test_id, records in test_instances.items():
        if test_id not in report_lookup:
            continue
            
        report = report_lookup[test_id]
        category = "with_pressure" if report["subjective_time_pressure"] == '1' else "without_pressure"
        section = report["gmat_section"]
        
        # Update section counts
        pressure_results[category]["section_counts"][section] += 1
        
        # Update test counts
        pressure_results[category]["count"] += 1
        
        # Calculate and update question statistics
        correct_count = sum(1 for r in records if r["is_correct"] == '1')
        total_questions = len(records)
        
        pressure_results[category]["total_questions"] += total_questions
        pressure_results[category]["correct_count"] += correct_count
        
        # Update average question time
        try:
            total_time = sum(float(r["question_time_minutes"]) for r in records)
            pressure_results[category]["avg_question_time"] += total_time
        except ValueError:
            pass
    
    # Calculate final averages
    for category in ["with_pressure", "without_pressure"]:
        data = pressure_results[category]
        if data["count"] > 0:
            data["avg_question_time"] = data["avg_question_time"] / data["total_questions"] if data["total_questions"] > 0 else 0
            data["accuracy"] = data["correct_count"] / data["total_questions"] if data["total_questions"] > 0 else 0
        else:
            data["accuracy"] = 0
    
    # Calculate performance difference
    performance_diff = {}
    if (pressure_results["with_pressure"]["count"] > 0 and 
        pressure_results["without_pressure"]["count"] > 0):
        
        accuracy_diff = (pressure_results["without_pressure"]["accuracy"] - 
                        pressure_results["with_pressure"]["accuracy"])
        
        time_diff = (pressure_results["without_pressure"]["avg_question_time"] - 
                    pressure_results["with_pressure"]["avg_question_time"])
        
        performance_diff = {
            "accuracy_difference": accuracy_diff,
            "time_difference": time_diff,
            "analysis_complete": True
        }
    else:
        performance_diff = {
            "analysis_complete": False,
            "message": "Insufficient data for comparison (need tests both with and without time pressure)"
        }
    
    return {
        "student_id": student_id,
        "with_pressure": pressure_results["with_pressure"],
        "without_pressure": pressure_results["without_pressure"],
        "comparison": performance_diff
    }


def identify_student_strengths_weaknesses(student_id: str, gmat_section: str) -> Dict[str, Any]:
    """
    Identify a student's strengths and weaknesses based on their performance.
    
    Args:
        student_id: The ID of the student to analyze
        gmat_section: The section to analyze ('Q', 'DI', or 'V')
        
    Returns:
        Dictionary containing the analysis results
    """
    section_records = get_student_section_performance_records(student_id, gmat_section)
    
    if not section_records:
        return {
            "student_id": student_id,
            "gmat_section": gmat_section,
            "analysis_complete": False,
            "message": "No records found for this student and section"
        }
    
    # Initialize analysis structures
    analysis = {
        "student_id": student_id,
        "gmat_section": gmat_section,
        "analysis_complete": True,
        "total_questions": len(section_records),
        "skills_analysis": {},
        "question_types_analysis": {},
        "difficulty_analysis": {
            "easy": {"correct": 0, "total": 0, "accuracy": 0},
            "medium": {"correct": 0, "total": 0, "accuracy": 0},
            "hard": {"correct": 0, "total": 0, "accuracy": 0}
        }
    }
    
    # Initialize counters for different analysis aspects
    skills_counts = defaultdict(lambda: {"correct": 0, "total": 0})
    q_types_counts = defaultdict(lambda: {"correct": 0, "total": 0})
    
    # Process each record
    for record in section_records:
        is_correct = record["is_correct"] == '1'
        
        # Process fundamental skill analysis
        if gmat_section in ["Q", "V"]:
            skill = record.get("question_fundamental_skill", "Unknown")
            if skill:
                skills_counts[skill]["total"] += 1
                if is_correct:
                    skills_counts[skill]["correct"] += 1
        
        # Process content domain analysis for DI section
        if gmat_section == "DI":
            domain = record.get("content_domain", "Unknown")
            if domain:
                skills_counts[domain]["total"] += 1
                if is_correct:
                    skills_counts[domain]["correct"] += 1
        
        # Process question type analysis
        q_type = record.get("question_type", "Unknown")
        if q_type:
            q_types_counts[q_type]["total"] += 1
            if is_correct:
                q_types_counts[q_type]["correct"] += 1
        
        # Process difficulty analysis
        try:
            difficulty = float(record["question_difficulty"])
            
            # Categorize difficulty
            if difficulty < 3:
                category = "easy"
            elif difficulty < 4:
                category = "medium"
            else:
                category = "hard"
                
            analysis["difficulty_analysis"][category]["total"] += 1
            if is_correct:
                analysis["difficulty_analysis"][category]["correct"] += 1
                
        except (ValueError, KeyError):
            pass
    
    # Calculate accuracies for skills/domains
    for skill, counts in skills_counts.items():
        accuracy = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        analysis["skills_analysis"][skill] = {
            "correct": counts["correct"],
            "total": counts["total"],
            "accuracy": accuracy
        }
    
    # Calculate accuracies for question types
    for q_type, counts in q_types_counts.items():
        accuracy = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        analysis["question_types_analysis"][q_type] = {
            "correct": counts["correct"],
            "total": counts["total"],
            "accuracy": accuracy
        }
    
    # Calculate accuracies for difficulty levels
    for level in analysis["difficulty_analysis"]:
        counts = analysis["difficulty_analysis"][level]
        counts["accuracy"] = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
    
    # Identify strengths and weaknesses
    if analysis["skills_analysis"]:
        skills = list(analysis["skills_analysis"].items())
        
        # Sort by accuracy
        strengths = sorted(skills, key=lambda x: x[1]["accuracy"], reverse=True)
        weaknesses = sorted(skills, key=lambda x: x[1]["accuracy"])
        
        # Filter to include only skills with at least 2 questions
        strengths = [s for s in strengths if s[1]["total"] >= 2]
        weaknesses = [s for s in weaknesses if s[1]["total"] >= 2]
        
        analysis["top_strengths"] = [{"skill": s[0], **s[1]} for s in strengths[:3]]
        analysis["top_weaknesses"] = [{"skill": w[0], **w[1]} for w in weaknesses[:3]]
    
    return analysis


def get_progress_over_time(student_id: str, gmat_section: str) -> Dict[str, Any]:
    """
    Track a student's progress over time for a specific GMAT section.
    
    Args:
        student_id: The ID of the student to analyze
        gmat_section: The section to analyze ('Q', 'DI', or 'V')
        
    Returns:
        Dictionary containing the progress analysis
    """
    section_records = get_student_section_performance_records(student_id, gmat_section)
    
    if not section_records:
        return {
            "student_id": student_id,
            "gmat_section": gmat_section,
            "analysis_complete": False,
            "message": "No records found for this student and section"
        }
    
    # Group records by test_instance_id and test_date
    test_instances = defaultdict(lambda: {"records": [], "date": None})
    
    for record in section_records:
        test_id = record["test_instance_id"]
        test_instances[test_id]["records"].append(record)
        test_instances[test_id]["date"] = record["test_date"]
    
    # Calculate statistics for each test instance
    progress_data = []
    
    for test_id, data in test_instances.items():
        records = data["records"]
        test_date = data["date"]
        
        total_questions = len(records)
        correct_count = sum(1 for r in records if r["is_correct"] == '1')
        accuracy = correct_count / total_questions if total_questions > 0 else 0
        
        # Calculate average time per question
        try:
            avg_time = sum(float(r["question_time_minutes"]) for r in records) / total_questions
        except (ValueError, ZeroDivisionError):
            avg_time = 0
            
        # Calculate difficulty metrics
        try:
            avg_difficulty = sum(float(r["question_difficulty"]) for r in records) / total_questions
        except (ValueError, ZeroDivisionError):
            avg_difficulty = 0
        
        progress_data.append({
            "test_instance_id": test_id,
            "test_date": test_date,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "avg_question_time_minutes": avg_time,
            "avg_difficulty": avg_difficulty
        })
    
    # Sort by test date
    progress_data.sort(key=lambda x: x["test_date"])
    
    # Calculate trend metrics
    if len(progress_data) >= 2:
        first_test = progress_data[0]
        latest_test = progress_data[-1]
        
        accuracy_change = latest_test["accuracy"] - first_test["accuracy"]
        time_change = latest_test["avg_question_time_minutes"] - first_test["avg_question_time_minutes"]
        
        trend_analysis = {
            "accuracy_trend": "improving" if accuracy_change > 0 else "declining" if accuracy_change < 0 else "stable",
            "accuracy_change": accuracy_change,
            "time_trend": "improving" if time_change < 0 else "declining" if time_change > 0 else "stable",
            "time_change": time_change,
            "num_tests_analyzed": len(progress_data),
            "date_range": f"{first_test['test_date']} to {latest_test['test_date']}"
        }
    else:
        trend_analysis = {
            "message": "Need at least 2 tests to calculate trends",
            "num_tests_analyzed": len(progress_data)
        }
    
    return {
        "student_id": student_id,
        "gmat_section": gmat_section,
        "analysis_complete": True,
        "progress_data": progress_data,
        "trend_analysis": trend_analysis
    } 