"""
Services package for the GMAT Diagnosis App.
"""

# Import services
from gmat_diagnosis_app.services.csv_data_service import (
    initialize_csv_files,
    add_gmat_performance_record,
    add_subjective_report_record,
    get_all_gmat_performance_records,
    get_all_subjective_report_records,
    get_student_gmat_performance_records,
    get_student_subjective_reports,
    get_test_instance_gmat_performance_records,
    get_test_instance_subjective_report,
    get_student_section_performance_records,
    update_gmat_performance_records,
    update_subjective_report_record,
    delete_gmat_performance_records,
    delete_subjective_report_record
)

# CSV data analysis services
from gmat_diagnosis_app.services.csv_data_analysis import (
    calculate_student_section_stats,
    analyze_time_pressure_impact,
    identify_student_strengths_weaknesses,
    get_progress_over_time
)

# CSV batch processing services
from gmat_diagnosis_app.services.csv_batch_processor import (
    batch_import_gmat_performance_data,
    batch_import_subjective_reports,
    export_student_data,
    export_all_data,
    generate_consolidated_student_report
)
