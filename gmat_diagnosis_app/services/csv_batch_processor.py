"""
CSV Batch Processor for GMAT Diagnosis App

This module provides functions for batch processing and exporting GMAT diagnosis data.
"""

import csv
import os
import datetime
import json
from typing import List, Dict, Any
from collections import defaultdict

# Import the CSV data service module
from gmat_diagnosis_app.services.csv_data_service import (
    get_all_gmat_performance_records,
    get_all_subjective_report_records,
    GMAT_PERFORMANCE_HEADERS,
    STUDENT_SUBJECTIVE_REPORTS_HEADERS,
    add_gmat_performance_record,
    add_subjective_report_record,
    get_student_gmat_performance_records,
    get_student_subjective_reports
)

# Import the CSV data analysis services
from gmat_diagnosis_app.services.csv_data_analysis import (
    calculate_student_section_stats, 
    analyze_time_pressure_impact,
    identify_student_strengths_weaknesses,
    get_progress_over_time
)


def batch_import_gmat_performance_data(import_file_path: str) -> Dict[str, Any]:
    """
    Import GMAT performance data from a CSV file.
    
    Args:
        import_file_path: Path to the CSV file to import
        
    Returns:
        Dictionary containing import statistics
    """
    if not os.path.exists(import_file_path):
        return {
            "success": False,
            "message": f"Import file not found: {import_file_path}",
            "records_imported": 0
        }
    
    try:
        # Read records from import file
        import_records = []
        with open(import_file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate the CSV has the required headers
            missing_headers = [h for h in GMAT_PERFORMANCE_HEADERS if h not in reader.fieldnames and h != "record_timestamp"]
            if missing_headers:
                return {
                    "success": False,
                    "message": f"Import file missing required headers: {', '.join(missing_headers)}",
                    "records_imported": 0
                }
            
            # Read all records
            for row in reader:
                import_records.append(row)
        
        if not import_records:
            return {
                "success": False,
                "message": "Import file contains no data records",
                "records_imported": 0
            }
        
        # Group records by test_instance_id for batch processing
        test_instances = defaultdict(list)
        for record in import_records:
            test_instances[record.get("test_instance_id", "unknown")].append(record)
        
        # Import records using the data service
        success_count = 0
        failed_count = 0
        test_instances_processed = 0
        
        for test_id, records in test_instances.items():
            success = add_gmat_performance_record(records)
            if success:
                success_count += len(records)
                test_instances_processed += 1
            else:
                failed_count += len(records)
        
        return {
            "success": failed_count == 0,
            "message": f"Import completed with {success_count} records imported successfully and {failed_count} failures",
            "records_imported": success_count,
            "records_failed": failed_count,
            "test_instances_processed": test_instances_processed
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error importing data: {str(e)}",
            "records_imported": 0
        }


def batch_import_subjective_reports(import_file_path: str) -> Dict[str, Any]:
    """
    Import subjective report data from a CSV file.
    
    Args:
        import_file_path: Path to the CSV file to import
        
    Returns:
        Dictionary containing import statistics
    """
    if not os.path.exists(import_file_path):
        return {
            "success": False,
            "message": f"Import file not found: {import_file_path}",
            "records_imported": 0
        }
    
    try:
        # Read records from import file
        import_records = []
        with open(import_file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate the CSV has the required headers
            missing_headers = [h for h in STUDENT_SUBJECTIVE_REPORTS_HEADERS if h not in reader.fieldnames]
            if missing_headers:
                return {
                    "success": False,
                    "message": f"Import file missing required headers: {', '.join(missing_headers)}",
                    "records_imported": 0
                }
            
            # Read all records
            for row in reader:
                import_records.append(row)
        
        if not import_records:
            return {
                "success": False,
                "message": "Import file contains no data records",
                "records_imported": 0
            }
        
        # Import records using the data service
        success_count = 0
        failed_count = 0
        
        for record in import_records:
            success = add_subjective_report_record(record)
            if success:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": failed_count == 0,
            "message": f"Import completed with {success_count} records imported successfully and {failed_count} failures",
            "records_imported": success_count,
            "records_failed": failed_count
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error importing data: {str(e)}",
            "records_imported": 0
        }


def export_student_data(student_id: str, export_dir: str) -> Dict[str, Any]:
    """
    Export all data for a specific student to CSV files.
    
    Args:
        student_id: The ID of the student to export data for
        export_dir: Directory to save the exported files
        
    Returns:
        Dictionary containing export statistics
    """
    # Ensure export directory exists
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating export directory: {str(e)}",
                "files_created": 0
            }
    
    # Get student data
    performance_records = get_student_gmat_performance_records(student_id)
    subjective_reports = get_student_subjective_reports(student_id)
    
    if not performance_records and not subjective_reports:
        return {
            "success": False,
            "message": f"No data found for student: {student_id}",
            "files_created": 0
        }
    
    files_created = 0
    export_results = {
        "performance_export": {
            "success": False,
            "records_exported": 0,
            "file_path": ""
        },
        "subjective_export": {
            "success": False,
            "records_exported": 0,
            "file_path": ""
        }
    }
    
    # Export performance data if available
    if performance_records:
        performance_file = os.path.join(export_dir, f"{student_id}_performance_export.csv")
        
        try:
            with open(performance_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
                writer.writeheader()
                writer.writerows(performance_records)
                
            files_created += 1
            export_results["performance_export"] = {
                "success": True,
                "records_exported": len(performance_records),
                "file_path": performance_file
            }
            
        except Exception as e:
            export_results["performance_export"] = {
                "success": False,
                "message": f"Error exporting performance data: {str(e)}",
                "records_exported": 0,
                "file_path": performance_file
            }
    
    # Export subjective reports if available
    if subjective_reports:
        subjective_file = os.path.join(export_dir, f"{student_id}_subjective_export.csv")
        
        try:
            with open(subjective_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
                writer.writeheader()
                writer.writerows(subjective_reports)
                
            files_created += 1
            export_results["subjective_export"] = {
                "success": True,
                "records_exported": len(subjective_reports),
                "file_path": subjective_file
            }
            
        except Exception as e:
            export_results["subjective_export"] = {
                "success": False,
                "message": f"Error exporting subjective reports: {str(e)}",
                "records_exported": 0,
                "file_path": subjective_file
            }
    
    # Create summary report
    summary_file = os.path.join(export_dir, f"{student_id}_summary_report.json")
    
    try:
        # Generate a summary of the student's data
        summary = {
            "student_id": student_id,
            "export_timestamp": datetime.datetime.now().isoformat(),
            "total_performance_records": len(performance_records),
            "total_subjective_reports": len(subjective_reports),
            "sections_taken": {}
        }
        
        # Count records by section
        for record in performance_records:
            section = record["gmat_section"]
            if section not in summary["sections_taken"]:
                summary["sections_taken"][section] = 0
            summary["sections_taken"][section] += 1
        
        # Write summary to file
        with open(summary_file, 'w') as jsonfile:
            json.dump(summary, jsonfile, indent=2)
            
        files_created += 1
        
    except Exception as e:
        print(f"Error creating summary report: {str(e)}")
    
    return {
        "success": files_created > 0,
        "message": f"Exported {files_created} files for student {student_id}",
        "files_created": files_created,
        "export_details": export_results
    }


def export_all_data(export_dir: str) -> Dict[str, Any]:
    """
    Export all GMAT performance and subjective report data to CSV files.
    
    Args:
        export_dir: Directory to save the exported files
        
    Returns:
        Dictionary containing export statistics
    """
    # Ensure export directory exists
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating export directory: {str(e)}",
                "files_created": 0
            }
    
    # Get all data
    performance_records = get_all_gmat_performance_records()
    subjective_reports = get_all_subjective_report_records()
    
    if not performance_records and not subjective_reports:
        return {
            "success": False,
            "message": "No data found in the system",
            "files_created": 0
        }
    
    files_created = 0
    export_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    export_results = {}
    
    # Export performance data if available
    if performance_records:
        performance_file = os.path.join(export_dir, f"gmat_performance_export_{export_timestamp}.csv")
        
        try:
            with open(performance_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
                writer.writeheader()
                writer.writerows(performance_records)
                
            files_created += 1
            export_results["performance_export"] = {
                "success": True,
                "records_exported": len(performance_records),
                "file_path": performance_file
            }
            
        except Exception as e:
            export_results["performance_export"] = {
                "success": False,
                "message": f"Error exporting performance data: {str(e)}",
                "records_exported": 0,
                "file_path": performance_file
            }
    
    # Export subjective reports if available
    if subjective_reports:
        subjective_file = os.path.join(export_dir, f"subjective_reports_export_{export_timestamp}.csv")
        
        try:
            with open(subjective_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
                writer.writeheader()
                writer.writerows(subjective_reports)
                
            files_created += 1
            export_results["subjective_export"] = {
                "success": True,
                "records_exported": len(subjective_reports),
                "file_path": subjective_file
            }
            
        except Exception as e:
            export_results["subjective_export"] = {
                "success": False,
                "message": f"Error exporting subjective reports: {str(e)}",
                "records_exported": 0,
                "file_path": subjective_file
            }
    
    # Create summary report
    summary_file = os.path.join(export_dir, f"export_summary_{export_timestamp}.json")
    
    try:
        # Extract unique student IDs
        student_ids = set()
        for record in performance_records:
            student_ids.add(record["student_id"])
        
        # Generate a summary of the export
        summary = {
            "export_timestamp": datetime.datetime.now().isoformat(),
            "total_performance_records": len(performance_records),
            "total_subjective_reports": len(subjective_reports),
            "unique_students": len(student_ids),
            "performance_sections": {
                "Q": sum(1 for r in performance_records if r["gmat_section"] == "Q"),
                "DI": sum(1 for r in performance_records if r["gmat_section"] == "DI"),
                "V": sum(1 for r in performance_records if r["gmat_section"] == "V")
            }
        }
        
        # Write summary to file
        with open(summary_file, 'w') as jsonfile:
            json.dump(summary, jsonfile, indent=2)
            
        files_created += 1
        export_results["summary"] = {
            "success": True,
            "file_path": summary_file
        }
        
    except Exception as e:
        export_results["summary"] = {
            "success": False,
            "message": f"Error creating summary report: {str(e)}"
        }
    
    return {
        "success": files_created > 0,
        "message": f"Exported {files_created} files containing all system data",
        "files_created": files_created,
        "records_exported": {
            "performance_records": len(performance_records),
            "subjective_reports": len(subjective_reports)
        },
        "export_details": export_results
    }


def generate_consolidated_student_report(student_id: str, output_file: str) -> Dict[str, Any]:
    """
    Generate a consolidated JSON report for a specific student.
    
    Args:
        student_id: The ID of the student to generate a report for
        output_file: Path to save the generated report
        
    Returns:
        Dictionary containing the report generation results
    """
    # Get student data
    performance_records = get_student_gmat_performance_records(student_id)
    subjective_reports = get_student_subjective_reports(student_id)
    
    if not performance_records:
        return {
            "success": False,
            "message": f"No performance data found for student: {student_id}",
            "report_generated": False
        }
    
    # Initialize the consolidated report
    report = {
        "student_id": student_id,
        "report_generation_timestamp": datetime.datetime.now().isoformat(),
        "data_summary": {
            "total_performance_records": len(performance_records),
            "total_subjective_reports": len(subjective_reports)
        },
        "section_stats": {},
        "time_pressure_analysis": None,
        "strengths_weaknesses": {},
        "progress_analysis": {}
    }
    
    # Calculate statistics for each section the student has taken
    sections_taken = set(record["gmat_section"] for record in performance_records)
    
    for section in sections_taken:
        report["section_stats"][section] = calculate_student_section_stats(student_id, section)
        report["strengths_weaknesses"][section] = identify_student_strengths_weaknesses(student_id, section)
        report["progress_analysis"][section] = get_progress_over_time(student_id, section)
    
    # Analyze time pressure impact if subjective reports are available
    if subjective_reports:
        report["time_pressure_analysis"] = analyze_time_pressure_impact(student_id)
    
    # Save the consolidated report to the output file
    try:
        # Create the directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, 'w') as jsonfile:
            json.dump(report, jsonfile, indent=2)
            
        return {
            "success": True,
            "message": f"Successfully generated consolidated report for student {student_id}",
            "report_generated": True,
            "report_file": output_file
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating consolidated report: {str(e)}",
            "report_generated": False
        } 