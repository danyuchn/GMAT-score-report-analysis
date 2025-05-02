import pandas as pd
import numpy as np

# --- Placeholder Helper Functions for Diagnosis ---
# These functions currently only calculate basic stats.
# Detailed logic based on markdown documents needs to be implemented here.

def _diagnose_ds(df_ds):
    """Placeholder diagnosis for Data Sufficiency (DS)."""
    if df_ds.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])
    
    total = len(df_ds)
    errors = df_ds['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_ds['overtime'].eq(True).sum() if 'overtime' in df_ds.columns else 0
    overtime_rate = overtime / total if total > 0 else 0
    
    # TODO: Implement detailed DS diagnosis based on markdown logic
    #       - Check special_focus_error (DI_FOUNDATIONAL_MASTERY_INSTABILITY_SFE)
    #       - Classify errors (Fast/Slow/Normal & Wrong)
    #       - Associate DI_... diagnostic parameters
    
    diagnosis = f"DS: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"
    
    return pd.DataFrame([{
        'Question Type': 'DS', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

def _diagnose_tpa(df_tpa):
    """Placeholder diagnosis for Two-Part Analysis (TPA)."""
    if df_tpa.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])
        
    total = len(df_tpa)
    errors = df_tpa['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_tpa['overtime'].eq(True).sum() if 'overtime' in df_tpa.columns else 0
    overtime_rate = overtime / total if total > 0 else 0

    # TODO: Implement detailed TPA diagnosis based on markdown logic
    diagnosis = f"TPA: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'TPA', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])
    
def _diagnose_msr(df_msr):
    """Placeholder diagnosis for Multi-Source Reasoning (MSR)."""
    if df_msr.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

    total = len(df_msr)
    errors = df_msr['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    # Note: Overtime for MSR is group-based in the markdown
    overtime = df_msr['overtime'].eq(True).sum() if 'overtime' in df_msr.columns else 0 
    overtime_rate = overtime / total if total > 0 else 0
    
    # TODO: Implement detailed MSR diagnosis (group analysis, reading time, etc.)
    diagnosis = f"MSR: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'MSR', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

def _diagnose_gt(df_gt):
    """Placeholder diagnosis for Graph & Table (GT)."""
    if df_gt.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

    total = len(df_gt)
    errors = df_gt['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_gt['overtime'].eq(True).sum() if 'overtime' in df_gt.columns else 0
    overtime_rate = overtime / total if total > 0 else 0
    
    # TODO: Implement detailed GT diagnosis based on markdown logic
    diagnosis = f"GT: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'GT', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])
    
def _diagnose_cr(df_cr):
    """Placeholder diagnosis for Critical Reasoning (CR)."""
    if df_cr.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])
        
    total = len(df_cr)
    errors = df_cr['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_cr['overtime'].eq(True).sum() if 'overtime' in df_cr.columns else 0
    overtime_rate = overtime / total if total > 0 else 0

    # TODO: Implement detailed CR diagnosis based on markdown logic
    #       - Check special_focus_error (FOUNDATIONAL_MASTERY_INSTABILITY_SFE)
    #       - Classify errors (Fast/Slow/Normal & Wrong)
    #       - Associate CR_... diagnostic parameters
    #       - Requires 'question_fundamental_skill' column
    
    diagnosis = f"CR: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'CR', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

def _diagnose_rc(df_rc):
    """Placeholder diagnosis for Reading Comprehension (RC)."""
    if df_rc.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

    total = len(df_rc)
    errors = df_rc['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    # Note: Overtime for RC has group and individual components
    overtime = df_rc['overtime'].eq(True).sum() if 'overtime' in df_rc.columns else 0 
    overtime_rate = overtime / total if total > 0 else 0
    
    # TODO: Implement detailed RC diagnosis (group analysis, reading time, etc.)
    #       - Requires 'question_fundamental_skill' column
    diagnosis = f"RC: Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'RC', 
        'Total': total, 
        'Errors': errors, 
        'Error Rate': error_rate, 
        'Overtime': overtime, 
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

def _diagnose_q(df_q):
     """Placeholder diagnosis for Quantitative (Q) - Real/Pure analysis."""
     if df_q.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

     # Assuming 'question_type' column exists with 'Real'/'Pure'
     if 'question_type' not in df_q.columns:
         # Handle case where Q section doesn't distinguish Real/Pure
         total = len(df_q)
         errors = df_q['Correct'].eq(False).sum()
         error_rate = errors / total if total > 0 else 0
         overtime = df_q['overtime'].eq(True).sum() if 'overtime' in df_q.columns else 0
         overtime_rate = overtime / total if total > 0 else 0
         diagnosis = f"Q (Overall): Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"
         return pd.DataFrame([{'Question Type': 'Q (Overall)', 'Total': total, 'Errors': errors, 'Error Rate': error_rate, 'Overtime': overtime, 'Overtime Rate': overtime_rate, 'Diagnosis': diagnosis}])

     results = []
     for q_type in ['Real', 'Pure']:
         df_subtype = df_q[df_q['question_type'] == q_type]
         if not df_subtype.empty:
             total = len(df_subtype)
             errors = df_subtype['Correct'].eq(False).sum()
             error_rate = errors / total if total > 0 else 0
             overtime = df_subtype['overtime'].eq(True).sum() if 'overtime' in df_subtype.columns else 0
             overtime_rate = overtime / total if total > 0 else 0
             
             # TODO: Implement detailed Q diagnosis (Real/Pure comparison, skills, SFE, parameters)
             #       Requires 'question_fundamental_skill' column
             diagnosis = f"Q ({q_type}): Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"
             results.append({
                 'Question Type': f'Q ({q_type})', 
                 'Total': total, 
                 'Errors': errors, 
                 'Error Rate': error_rate, 
                 'Overtime': overtime, 
                 'Overtime Rate': overtime_rate,
                 'Diagnosis': diagnosis
             })
             
     return pd.DataFrame(results)


# --- Main Diagnosis Function ---

def run_diagnosis(df):
    """
    Runs the diagnostic analysis based on the input DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing response data. 
                           Expected columns: 'Question ID', 'Correct', 'question_difficulty', 
                           'question_time', 'question_type' (e.g., 'DS', 'CR', 'Real', 'Pure').
                           'difficulty' (calculated by estimate_difficulty). 
                           Optional but needed for full diagnosis: 'question_fundamental_skill', 
                           'content_domain', 'question_position', 'total_test_time'.

    Returns:
        pd.DataFrame: A DataFrame containing the diagnosis results, typically summarized by 
                      question type or skill category. Returns an empty DataFrame if input is invalid.
    """
    
    # --- 1. Input Validation ---
    required_cols = ['Question ID', 'Correct', 'difficulty', 'question_time', 'question_type']
    if not isinstance(df, pd.DataFrame) or not all(col in df.columns for col in required_cols):
        print(f"Invalid input DataFrame. Missing one or more required columns: {required_cols}")
        # In Streamlit app, use st.error()
        return pd.DataFrame() # Return empty DataFrame for invalid input

    df_processed = df.copy()

    # --- 2. Data Preprocessing (Simulated/Placeholder) ---
    # TODO: Implement full logic from Chapter 1 of markdown files
    #       - Calculate time_pressure (requires total_test_time or assume based on df)
    #       - Define overtime thresholds based on time_pressure and question_type
    #       - Mark 'is_invalid' based on time_pressure and ending speed (requires question_position)
    #       - Mark 'overtime' based on thresholds
    
    # Placeholder for 'overtime' marking (using arbitrary thresholds for now)
    # This needs actual implementation using markdown logic
    def mark_overtime(row):
        q_type = row['question_type']
        time = row['question_time']
        # Example thresholds (replace with actual logic)
        thresholds = {'DS': 2.5, 'TPA': 3.5, 'MSR': 2.3, 'GT': 3.5, 'CR': 2.5, 'RC': 2.5, 'Real': 3.0, 'Pure': 3.0}
        return time > thresholds.get(q_type, 3.0) # Default 3.0 mins

    if 'question_time' in df_processed.columns:
         df_processed['overtime'] = df_processed.apply(mark_overtime, axis=1)
    else:
         # If no time data, cannot mark overtime
         df_processed['overtime'] = False 
         print("Warning: 'question_time' column not found. Overtime analysis skipped.")


    # Placeholder for 'is_invalid' filtering (assuming no invalid data for now)
    # This needs actual implementation
    df_filtered = df_processed # .loc[df_processed['is_invalid'] == False] if 'is_invalid' in df_processed else df_processed
    
    if df_filtered.empty:
        print("No valid data remaining after filtering.")
        return pd.DataFrame()

    # --- 3. Diagnose by Section/Type ---
    all_results = []
    
    # Infer sections/types present in the data
    q_types_present = df_filtered['question_type'].unique()
    
    # Map question types to diagnostic functions
    diagnosis_functions = {
        'DS': _diagnose_ds,
        'TPA': _diagnose_tpa,
        'MSR': _diagnose_msr,
        'GT': _diagnose_gt,
        'CR': _diagnose_cr,
        'RC': _diagnose_rc,
        'Real': _diagnose_q, # Use _diagnose_q for both Real and Pure
        'Pure': _diagnose_q, # _diagnose_q handles sub-types
    }

    # Group Quantitative ('Real', 'Pure') separately if present
    is_q_present = any(qt in ['Real', 'Pure'] for qt in q_types_present)
    
    processed_q = False
    for q_type in q_types_present:
        if q_type in ['Real', 'Pure']:
            if not processed_q: # Process Q section only once
                 df_section = df_filtered[df_filtered['question_type'].isin(['Real', 'Pure'])]
                 if not df_section.empty:
                     result = _diagnose_q(df_section)
                     if result is not None and not result.empty:
                         all_results.append(result)
                 processed_q = True
        elif q_type in diagnosis_functions:
            df_section = df_filtered[df_filtered['question_type'] == q_type]
            if not df_section.empty:
                 func = diagnosis_functions[q_type]
                 result = func(df_section)
                 if result is not None and not result.empty:
                     all_results.append(result)
        else:
             print(f"Warning: No diagnosis function defined for question type '{q_type}'. Skipping.")

    # --- 4. Combine and Return Results ---
    if not all_results:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis']) # Return structure if no results
        
    result_df = pd.concat(all_results, ignore_index=True)
    
    return result_df
