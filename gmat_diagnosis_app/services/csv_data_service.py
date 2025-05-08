"""
CSV Data Service for GMAT Diagnosis App

This module provides functions to manage GMAT diagnosis data and student subjective reports
stored in CSV files.
"""

import csv
import os
import datetime
from typing import List, Dict, Any, Union, Optional, Tuple


# Define constants
GMAT_PERFORMANCE_DATA_FILE = "gmat_performance_data.csv"
STUDENT_SUBJECTIVE_REPORTS_FILE = "student_subjective_reports.csv"

# Define CSV headers
GMAT_PERFORMANCE_HEADERS = [
    "student_id",
    "test_instance_id",
    "gmat_section",
    "test_date",
    "question_id",
    "question_position",
    "question_time_minutes",
    "is_correct",
    "question_difficulty",
    "question_type",
    "question_fundamental_skill",
    "content_domain",
    "total_section_time_minutes",
    "max_allowed_section_time_minutes",
    "total_questions_in_section",
    "record_timestamp"
]

STUDENT_SUBJECTIVE_REPORTS_HEADERS = [
    "student_id",
    "test_instance_id",
    "gmat_section",
    "subjective_time_pressure",
    "report_collection_timestamp"
]


def initialize_csv_files() -> None:
    """
    Initialize CSV files if they do not exist.
    Creates the files and writes headers.
    """
    # Initialize gmat_performance_data.csv
    if not os.path.exists(GMAT_PERFORMANCE_DATA_FILE):
        try:
            with open(GMAT_PERFORMANCE_DATA_FILE, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
                writer.writeheader()
                print(f"Created {GMAT_PERFORMANCE_DATA_FILE} successfully.")
        except Exception as e:
            print(f"Error creating {GMAT_PERFORMANCE_DATA_FILE}: {e}")
    
    # Initialize student_subjective_reports.csv
    if not os.path.exists(STUDENT_SUBJECTIVE_REPORTS_FILE):
        try:
            with open(STUDENT_SUBJECTIVE_REPORTS_FILE, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
                writer.writeheader()
                print(f"Created {STUDENT_SUBJECTIVE_REPORTS_FILE} successfully.")
        except Exception as e:
            print(f"Error creating {STUDENT_SUBJECTIVE_REPORTS_FILE}: {e}")


def validate_gmat_performance_record(record: Dict[str, Any]) -> bool:
    """
    Validate a GMAT performance record.
    
    Args:
        record: Dictionary containing the GMAT performance record
        
    Returns:
        bool: True if record is valid, False otherwise
    """
    # Check for required fields
    required_fields = [
        "student_id", "test_instance_id", "gmat_section", "test_date",
        "question_id", "question_position", "question_time_minutes",
        "is_correct", "question_difficulty", "question_type",
        "total_section_time_minutes", "max_allowed_section_time_minutes",
        "total_questions_in_section"
    ]
    
    for field in required_fields:
        if field not in record:
            print(f"Missing required field: {field}")
            return False
    
    # Validate data types and values
    try:
        # Check is_correct is 0 or 1
        if record["is_correct"] not in [0, 1]:
            print(f"Invalid value for is_correct: {record['is_correct']}. Must be 0 or 1.")
            return False
        
        # Ensure question_position is an integer and greater than 0
        if not isinstance(record["question_position"], int) or record["question_position"] <= 0:
            print(f"Invalid question_position: {record['question_position']}. Must be a positive integer.")
            return False
        
        # Validate time values are positive numbers
        if float(record["question_time_minutes"]) < 0:
            print(f"Invalid question_time_minutes: {record['question_time_minutes']}. Must be a non-negative number.")
            return False
        
        if float(record["total_section_time_minutes"]) < 0:
            print(f"Invalid total_section_time_minutes: {record['total_section_time_minutes']}. Must be a non-negative number.")
            return False
        
        if float(record["max_allowed_section_time_minutes"]) <= 0:
            print(f"Invalid max_allowed_section_time_minutes: {record['max_allowed_section_time_minutes']}. Must be a positive number.")
            return False
        
        # Validate gmat_section
        if record["gmat_section"] not in ["Q", "DI", "V"]:
            print(f"Invalid gmat_section: {record['gmat_section']}. Must be 'Q', 'DI', or 'V'.")
            return False
        
        # Validate test_date format (YYYY-MM-DD)
        try:
            datetime.datetime.strptime(record["test_date"], "%Y-%m-%d")
        except ValueError:
            print(f"Invalid test_date format: {record['test_date']}. Must be in YYYY-MM-DD format.")
            return False
        
    except (ValueError, TypeError) as e:
        print(f"Data validation error: {e}")
        return False
    
    return True


def add_gmat_performance_record(record_data: List[Dict[str, Any]]) -> bool:
    """
    Add GMAT performance records to the CSV file.
    
    Args:
        record_data: List of dictionaries, each containing data for a single question performance
                    All records should share the same student_id, test_instance_id, etc.
                    
    Returns:
        bool: True if records were added successfully, False otherwise
    """
    if not record_data:
        print("Error: Empty record data provided")
        return False
    
    # Initialize CSV file if it doesn't exist
    initialize_csv_files()
    
    try:
        current_timestamp = datetime.datetime.now().isoformat()
        
        with open(GMAT_PERFORMANCE_DATA_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
            
            for record in record_data:
                # Validate the record
                if not validate_gmat_performance_record(record):
                    print(f"Invalid record found, skipping: {record}")
                    continue
                
                # Add timestamp to the record
                record["record_timestamp"] = current_timestamp
                
                # Write the record to the CSV file
                writer.writerow(record)
        
        print(f"Successfully added {len(record_data)} GMAT performance records.")
        return True
    except Exception as e:
        print(f"Error adding GMAT performance records: {e}")
        return False


def validate_subjective_report_record(report: Dict[str, Any]) -> bool:
    """
    Validate a subjective report record.
    
    Args:
        report: Dictionary containing the subjective report data
        
    Returns:
        bool: True if report is valid, False otherwise
    """
    # Check for required fields
    required_fields = [
        "student_id", "test_instance_id", "gmat_section", 
        "subjective_time_pressure", "report_collection_timestamp"
    ]
    
    for field in required_fields:
        if field not in report:
            print(f"Missing required field: {field}")
            return False
    
    # Validate data types and values
    try:
        # Check subjective_time_pressure is 0 or 1
        if report["subjective_time_pressure"] not in [0, 1]:
            print(f"Invalid value for subjective_time_pressure: {report['subjective_time_pressure']}. Must be 0 or 1.")
            return False
        
        # Validate gmat_section
        if report["gmat_section"] not in ["Q", "DI", "V"]:
            print(f"Invalid gmat_section: {report['gmat_section']}. Must be 'Q', 'DI', or 'V'.")
            return False
        
        # Validate timestamp format (ISO 8601)
        try:
            datetime.datetime.fromisoformat(report["report_collection_timestamp"])
        except ValueError:
            print(f"Invalid report_collection_timestamp format: {report['report_collection_timestamp']}. Must be in ISO 8601 format.")
            return False
        
    except (ValueError, TypeError) as e:
        print(f"Data validation error: {e}")
        return False
    
    return True


def add_subjective_report_record(report_data: Dict[str, Any]) -> bool:
    """
    Add a subjective report record to the CSV file.
    
    Args:
        report_data: Dictionary containing subjective report data
                    
    Returns:
        bool: True if the record was added successfully, False otherwise
    """
    if not report_data:
        print("Error: Empty report data provided")
        return False
    
    # Initialize CSV file if it doesn't exist
    initialize_csv_files()
    
    try:
        # Validate the report data
        if not validate_subjective_report_record(report_data):
            print(f"Invalid report data, not adding to CSV: {report_data}")
            return False
        
        with open(STUDENT_SUBJECTIVE_REPORTS_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
            writer.writerow(report_data)
        
        print(f"Successfully added subjective report record for student {report_data['student_id']}")
        return True
    except Exception as e:
        print(f"Error adding subjective report record: {e}")
        return False


def get_all_gmat_performance_records() -> List[Dict[str, Any]]:
    """
    Get all GMAT performance records from the CSV file.
    
    Returns:
        List of dictionaries containing all GMAT performance records.
    """
    initialize_csv_files()
    
    try:
        with open(GMAT_PERFORMANCE_DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except Exception as e:
        print(f"Error reading GMAT performance records: {e}")
        return []


def get_all_subjective_report_records() -> List[Dict[str, Any]]:
    """
    Get all subjective report records from the CSV file.
    
    Returns:
        List of dictionaries containing all subjective report records.
    """
    initialize_csv_files()
    
    try:
        with open(STUDENT_SUBJECTIVE_REPORTS_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except Exception as e:
        print(f"Error reading subjective report records: {e}")
        return []


def get_student_gmat_performance_records(student_id: str) -> List[Dict[str, Any]]:
    """
    Get GMAT performance records for a specific student.
    
    Args:
        student_id: The ID of the student to retrieve records for
        
    Returns:
        List of dictionaries containing GMAT performance records for the specified student.
    """
    all_records = get_all_gmat_performance_records()
    return [record for record in all_records if record["student_id"] == student_id]


def get_student_subjective_reports(student_id: str) -> List[Dict[str, Any]]:
    """
    Get subjective report records for a specific student.
    
    Args:
        student_id: The ID of the student to retrieve records for
        
    Returns:
        List of dictionaries containing subjective report records for the specified student.
    """
    all_reports = get_all_subjective_report_records()
    return [report for report in all_reports if report["student_id"] == student_id]


def get_test_instance_gmat_performance_records(test_instance_id: str) -> List[Dict[str, Any]]:
    """
    Get GMAT performance records for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to retrieve records for
        
    Returns:
        List of dictionaries containing GMAT performance records for the specified test instance.
    """
    all_records = get_all_gmat_performance_records()
    return [record for record in all_records if record["test_instance_id"] == test_instance_id]


def get_test_instance_subjective_report(test_instance_id: str) -> Optional[Dict[str, Any]]:
    """
    Get subjective report record for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to retrieve the report for
        
    Returns:
        Dictionary containing the subjective report record, or None if not found.
    """
    all_reports = get_all_subjective_report_records()
    for report in all_reports:
        if report["test_instance_id"] == test_instance_id:
            return report
    return None


def get_student_section_performance_records(student_id: str, gmat_section: str) -> List[Dict[str, Any]]:
    """
    Get GMAT performance records for a specific student and section.
    
    Args:
        student_id: The ID of the student to retrieve records for
        gmat_section: The section to retrieve records for ('Q', 'DI', or 'V')
        
    Returns:
        List of dictionaries containing GMAT performance records for the specified student and section.
    """
    student_records = get_student_gmat_performance_records(student_id)
    return [record for record in student_records if record["gmat_section"] == gmat_section]


def update_gmat_performance_records(test_instance_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update GMAT performance records for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to update records for
        updates: Dictionary containing the fields to update and their new values
        
    Returns:
        bool: True if records were updated successfully, False otherwise
    """
    all_records = get_all_gmat_performance_records()
    updated_records = []
    records_updated = False
    
    for record in all_records:
        if record["test_instance_id"] == test_instance_id:
            # Apply updates to the record
            for key, value in updates.items():
                if key in GMAT_PERFORMANCE_HEADERS:
                    record[key] = value
            records_updated = True
        updated_records.append(record)
    
    if not records_updated:
        print(f"No records found for test_instance_id: {test_instance_id}")
        return False
    
    try:
        # Write all records back to the CSV file
        with open(GMAT_PERFORMANCE_DATA_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
            writer.writeheader()
            writer.writerows(updated_records)
        
        print(f"Successfully updated records for test_instance_id: {test_instance_id}")
        return True
    except Exception as e:
        print(f"Error updating GMAT performance records: {e}")
        return False


def update_subjective_report_record(test_instance_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update a subjective report record for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to update the report for
        updates: Dictionary containing the fields to update and their new values
        
    Returns:
        bool: True if the record was updated successfully, False otherwise
    """
    all_reports = get_all_subjective_report_records()
    updated_reports = []
    report_updated = False
    
    for report in all_reports:
        if report["test_instance_id"] == test_instance_id:
            # Apply updates to the report
            for key, value in updates.items():
                if key in STUDENT_SUBJECTIVE_REPORTS_HEADERS:
                    report[key] = value
            report_updated = True
        updated_reports.append(report)
    
    if not report_updated:
        print(f"No subjective report found for test_instance_id: {test_instance_id}")
        return False
    
    try:
        # Write all reports back to the CSV file
        with open(STUDENT_SUBJECTIVE_REPORTS_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
            writer.writeheader()
            writer.writerows(updated_reports)
        
        print(f"Successfully updated subjective report for test_instance_id: {test_instance_id}")
        return True
    except Exception as e:
        print(f"Error updating subjective report record: {e}")
        return False


def delete_gmat_performance_records(test_instance_id: str) -> bool:
    """
    Delete GMAT performance records for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to delete records for
        
    Returns:
        bool: True if records were deleted successfully, False otherwise
    """
    all_records = get_all_gmat_performance_records()
    filtered_records = []
    records_deleted = False
    
    for record in all_records:
        if record["test_instance_id"] != test_instance_id:
            filtered_records.append(record)
        else:
            records_deleted = True
    
    if not records_deleted:
        print(f"No records found for test_instance_id: {test_instance_id}")
        return False
    
    try:
        # Write filtered records back to the CSV file
        with open(GMAT_PERFORMANCE_DATA_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=GMAT_PERFORMANCE_HEADERS)
            writer.writeheader()
            writer.writerows(filtered_records)
        
        print(f"Successfully deleted records for test_instance_id: {test_instance_id}")
        return True
    except Exception as e:
        print(f"Error deleting GMAT performance records: {e}")
        return False


def delete_subjective_report_record(test_instance_id: str) -> bool:
    """
    Delete a subjective report record for a specific test instance.
    
    Args:
        test_instance_id: The ID of the test instance to delete the report for
        
    Returns:
        bool: True if the record was deleted successfully, False otherwise
    """
    all_reports = get_all_subjective_report_records()
    filtered_reports = []
    report_deleted = False
    
    for report in all_reports:
        if report["test_instance_id"] != test_instance_id:
            filtered_reports.append(report)
        else:
            report_deleted = True
    
    if not report_deleted:
        print(f"No subjective report found for test_instance_id: {test_instance_id}")
        return False
    
    try:
        # Write filtered reports back to the CSV file
        with open(STUDENT_SUBJECTIVE_REPORTS_FILE, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STUDENT_SUBJECTIVE_REPORTS_HEADERS)
            writer.writeheader()
            writer.writerows(filtered_reports)
        
        print(f"Successfully deleted subjective report for test_instance_id: {test_instance_id}")
        return True
    except Exception as e:
        print(f"Error deleting subjective report record: {e}")
        return False 