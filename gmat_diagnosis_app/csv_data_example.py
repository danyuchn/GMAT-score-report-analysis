"""
CSV Data Services Example Script

This script demonstrates how to use the CSV data services module for GMAT diagnosis data management.
"""

import os
import sys
import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the CSV data services
from gmat_diagnosis_app.services.csv_data_service import (
    initialize_csv_files,
    add_gmat_performance_record,
    add_subjective_report_record,
    get_all_gmat_performance_records,
    get_student_gmat_performance_records,
    get_test_instance_gmat_performance_records,
    get_student_section_performance_records
)

# Import the CSV data analysis services
from gmat_diagnosis_app.services.csv_data_analysis import (
    calculate_student_section_stats,
    analyze_time_pressure_impact,
    identify_student_strengths_weaknesses,
    get_progress_over_time
)

# Import the CSV batch processor
from gmat_diagnosis_app.services.csv_batch_processor import (
    export_student_data,
    export_all_data,
    generate_consolidated_student_report
)


def generate_sample_data() -> None:
    """Generate sample data for demonstration purposes."""
    # Initialize CSV files
    initialize_csv_files()
    
    # Sample student IDs
    student_ids = ["student_001", "student_002", "student_003"]
    
    # Sample test dates
    test_dates = ["2025-05-01", "2025-05-15", "2025-06-01"]
    
    # Sample sections
    sections = ["Q", "DI", "V"]
    
    # Sample question types for each section
    question_types = {
        "Q": ["PS", "DS"],
        "DI": ["Real", "Inference", "Calculation"],
        "V": ["CR", "RC", "SC"]
    }
    
    # Sample fundamental skills
    fundamental_skills = {
        "Q": ["Algebra", "Arithmetic", "Geometry", "Word Problems"],
        "V": ["Grammar", "Logic", "Reading", "Argument Analysis"],
        "DI": []
    }
    
    # Sample content domains for DI
    content_domains = ["Math Related", "Business", "Science", "Social Science"]
    
    # Generate sample data for each student
    for student_id in student_ids:
        # Create multiple test instances per student
        for test_date in test_dates:
            for section in sections:
                # Create a unique test instance ID
                test_instance_id = f"{student_id}_{section}_{test_date.replace('-', '')}_test1"
                
                # Determine total questions for this section
                total_questions = 12 if section == "DI" else 15
                
                # Calculate a random total section time (within allowed limits)
                max_allowed_time = 45.0  # 45 minutes standard time
                total_section_time = min(max_allowed_time * 0.9 + 
                                         max_allowed_time * 0.2 * 
                                         (datetime.datetime.now().microsecond / 1000000), 
                                         max_allowed_time)
                
                # Generate records for each question in this test instance
                records = []
                for q_pos in range(1, total_questions + 1):
                    # Select appropriate question type for this section
                    q_type = question_types[section][q_pos % len(question_types[section])]
                    
                    # Generate question difficulty (1.0 to 5.0 scale)
                    difficulty = 1.0 + (q_pos / total_questions) * 4.0
                    
                    # Determine if the question was answered correctly
                    # More difficult questions have lower chance of being correct
                    is_correct = 1 if (q_pos + ord(student_id[-1])) % 3 != 0 and difficulty < 4.0 else 0
                    
                    # Calculate time spent on this question (in minutes)
                    question_time = total_section_time / total_questions * (0.8 + 
                                                             (difficulty / 5.0) * 0.4 *
                                                             (datetime.datetime.now().microsecond / 1000000 + 1))
                    
                    # Select appropriate skill or domain
                    skill = ""
                    domain = ""
                    
                    if section in ["Q", "V"]:
                        skill_index = (q_pos + ord(student_id[-1])) % len(fundamental_skills[section])
                        skill = fundamental_skills[section][skill_index]
                    elif section == "DI":
                        domain_index = (q_pos + ord(student_id[-1])) % len(content_domains)
                        domain = content_domains[domain_index]
                    
                    # Create the record
                    record = {
                        "student_id": student_id,
                        "test_instance_id": test_instance_id,
                        "gmat_section": section,
                        "test_date": test_date,
                        "question_id": f"{section}_{q_pos}_{test_date.replace('-', '')}",
                        "question_position": q_pos,
                        "question_time_minutes": round(question_time, 2),
                        "is_correct": is_correct,
                        "question_difficulty": round(difficulty, 1),
                        "question_type": q_type,
                        "question_fundamental_skill": skill,
                        "content_domain": domain,
                        "total_section_time_minutes": round(total_section_time, 2),
                        "max_allowed_section_time_minutes": max_allowed_time,
                        "total_questions_in_section": total_questions
                    }
                    
                    records.append(record)
                
                # Add the records to the CSV file
                add_gmat_performance_record(records)
                
                # Generate a subjective report for this test instance
                subjective_time_pressure = 1 if section == "V" or total_section_time > 0.8 * max_allowed_time else 0
                
                subjective_report = {
                    "student_id": student_id,
                    "test_instance_id": test_instance_id,
                    "gmat_section": section,
                    "subjective_time_pressure": subjective_time_pressure,
                    "report_collection_timestamp": datetime.datetime.now().isoformat()
                }
                
                # Add the subjective report to the CSV file
                add_subjective_report_record(subjective_report)
    
    print(f"Sample data generation complete. Generated data for {len(student_ids)} students.")


def demonstrate_data_retrieval() -> None:
    """Demonstrate data retrieval functions."""
    # Get all performance records
    all_records = get_all_gmat_performance_records()
    print(f"Total performance records: {len(all_records)}")
    
    if all_records:
        # Get records for a specific student
        student_id = all_records[0]["student_id"]
        student_records = get_student_gmat_performance_records(student_id)
        print(f"Records for student {student_id}: {len(student_records)}")
        
        # Get records for a specific test instance
        test_instance_id = student_records[0]["test_instance_id"]
        test_records = get_test_instance_gmat_performance_records(test_instance_id)
        print(f"Records for test instance {test_instance_id}: {len(test_records)}")
        
        # Get records for a specific section
        section = "Q"
        section_records = get_student_section_performance_records(student_id, section)
        print(f"Records for student {student_id}, section {section}: {len(section_records)}")


def demonstrate_data_analysis() -> None:
    """Demonstrate data analysis functions."""
    # Get all performance records to find a valid student ID
    all_records = get_all_gmat_performance_records()
    
    if not all_records:
        print("No data available for analysis demonstration.")
        return
    
    student_id = all_records[0]["student_id"]
    print(f"Demonstrating data analysis for student: {student_id}")
    
    # Calculate section statistics
    for section in ["Q", "DI", "V"]:
        stats = calculate_student_section_stats(student_id, section)
        print(f"\nSection stats for {section}:")
        if stats.get("total_tests", 0) > 0:
            print(f"  Total tests: {stats['total_tests']}")
            print(f"  Overall accuracy: {stats['overall_accuracy']:.2f}")
        else:
            print(f"  No data available for section {section}")
    
    # Analyze time pressure impact
    pressure_analysis = analyze_time_pressure_impact(student_id)
    print("\nTime pressure analysis:")
    if pressure_analysis.get("comparison", {}).get("analysis_complete", False):
        accuracy_diff = pressure_analysis["comparison"]["accuracy_difference"]
        time_diff = pressure_analysis["comparison"]["time_difference"]
        print(f"  Accuracy difference (no pressure - pressure): {accuracy_diff:.2f}")
        print(f"  Time difference (no pressure - pressure): {time_diff:.2f} minutes")
    else:
        print("  Insufficient data for time pressure analysis")
    
    # Identify strengths and weaknesses
    for section in ["Q", "DI", "V"]:
        strengths = identify_student_strengths_weaknesses(student_id, section)
        print(f"\nStrengths and weaknesses for section {section}:")
        
        if strengths.get("analysis_complete", False):
            if "top_strengths" in strengths and strengths["top_strengths"]:
                print("  Top strengths:")
                for strength in strengths["top_strengths"]:
                    print(f"    {strength['skill']}: {strength['accuracy']:.2f} accuracy")
            
            if "top_weaknesses" in strengths and strengths["top_weaknesses"]:
                print("  Top weaknesses:")
                for weakness in strengths["top_weaknesses"]:
                    print(f"    {weakness['skill']}: {weakness['accuracy']:.2f} accuracy")
        else:
            print(f"  Insufficient data for analysis in section {section}")
    
    # Track progress over time
    for section in ["Q", "DI", "V"]:
        progress = get_progress_over_time(student_id, section)
        print(f"\nProgress over time for section {section}:")
        
        if progress.get("analysis_complete", False) and "trend_analysis" in progress:
            trend = progress["trend_analysis"]
            if "accuracy_trend" in trend:
                print(f"  Accuracy trend: {trend['accuracy_trend']} ({trend['accuracy_change']:.2f})")
                print(f"  Time trend: {trend['time_trend']} ({trend['time_change']:.2f} minutes)")
                print(f"  Tests analyzed: {trend['num_tests_analyzed']}")
                print(f"  Date range: {trend['date_range']}")
        else:
            print(f"  Insufficient data for progress analysis in section {section}")


def demonstrate_data_export() -> None:
    """Demonstrate data export functions."""
    # Get all performance records to find a valid student ID
    all_records = get_all_gmat_performance_records()
    
    if not all_records:
        print("No data available for export demonstration.")
        return
    
    student_id = all_records[0]["student_id"]
    print(f"Demonstrating data export for student: {student_id}")
    
    # Create an export directory
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Export student data
    student_export = export_student_data(student_id, export_dir)
    print("\nStudent data export results:")
    print(f"  Success: {student_export['success']}")
    print(f"  Files created: {student_export['files_created']}")
    print(f"  Message: {student_export['message']}")
    
    # Export all data
    all_data_export = export_all_data(export_dir)
    print("\nAll data export results:")
    print(f"  Success: {all_data_export['success']}")
    print(f"  Files created: {all_data_export['files_created']}")
    print(f"  Records exported: {all_data_export['records_exported']}")
    print(f"  Message: {all_data_export['message']}")
    
    # Generate consolidated student report
    report_file = os.path.join(export_dir, f"{student_id}_consolidated_report.json")
    report_result = generate_consolidated_student_report(student_id, report_file)
    print("\nConsolidated report generation results:")
    print(f"  Success: {report_result['success']}")
    print(f"  Report generated: {report_result['report_generated']}")
    print(f"  Message: {report_result['message']}")
    
    if report_result.get('success', False):
        print(f"  Report file: {report_result['report_file']}")


def run_all_demonstrations() -> None:
    """Run all demonstration functions."""
    print("="*80)
    print("CSV Data Services Demonstration")
    print("="*80)
    
    # Check if data exists
    all_records = get_all_gmat_performance_records()
    
    if not all_records:
        print("\nNo existing data found. Generating sample data...\n")
        generate_sample_data()
    else:
        print(f"\nFound existing data with {len(all_records)} performance records.\n")
    
    print("\n" + "="*50)
    print("Data Retrieval Demonstration")
    print("="*50)
    demonstrate_data_retrieval()
    
    print("\n" + "="*50)
    print("Data Analysis Demonstration")
    print("="*50)
    demonstrate_data_analysis()
    
    print("\n" + "="*50)
    print("Data Export Demonstration")
    print("="*50)
    demonstrate_data_export()
    
    print("\n" + "="*80)
    print("Demonstration Complete")
    print("="*80)


if __name__ == "__main__":
    run_all_demonstrations() 