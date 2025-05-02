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

# Added placeholder functions for overall Verbal and DI diagnosis
def _diagnose_verbal_overall(df_v):
    """Placeholder overall diagnosis for Verbal based on simulation."""
    if df_v.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

    total = len(df_v)
    errors = df_v['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_v['overtime'].eq(True).sum() if 'overtime' in df_v.columns else 0
    overtime_rate = overtime / total if total > 0 else 0

    diagnosis = f"Verbal (Overall): Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'Verbal (Overall)',
        'Total': total,
        'Errors': errors,
        'Error Rate': error_rate,
        'Overtime': overtime,
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

def _diagnose_di_overall(df_di):
    """Placeholder overall diagnosis for Data Insights based on simulation."""
    if df_di.empty:
        return pd.DataFrame(columns=['Question Type', 'Total', 'Errors', 'Error Rate', 'Overtime', 'Overtime Rate', 'Diagnosis'])

    total = len(df_di)
    errors = df_di['Correct'].eq(False).sum()
    error_rate = errors / total if total > 0 else 0
    overtime = df_di['overtime'].eq(True).sum() if 'overtime' in df_di.columns else 0
    overtime_rate = overtime / total if total > 0 else 0

    diagnosis = f"DI (Overall): Error Rate {error_rate:.1%}, Overtime Rate {overtime_rate:.1%}. (Detailed diagnosis pending)"

    return pd.DataFrame([{
        'Question Type': 'DI (Overall)',
        'Total': total,
        'Errors': errors,
        'Error Rate': error_rate,
        'Overtime': overtime,
        'Overtime Rate': overtime_rate,
        'Diagnosis': diagnosis
    }])

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
        # Added Quant, Verbal, DI placeholders
        thresholds = {
            'DS': 2.5, 'TPA': 3.5, 'MSR': 2.3, 'GT': 3.5, 
            'CR': 2.5, 'RC': 2.5, 
            'Real': 3.0, 'Pure': 3.0,
            'Quant': 3.0, 'Verbal': 2.5, 'DI': 3.0 # Generic thresholds for overall types
        }
        return time > thresholds.get(q_type, 3.0) # Default 3.0 mins

    if 'question_time' in df_processed.columns:
        df_processed['overtime'] = df_processed.apply(mark_overtime, axis=1)
    else:
        df_processed['overtime'] = False # Assume not overtime if time is missing

    # Placeholder for 'is_invalid' filtering (assuming no invalid data for now)
    # This needs actual implementation
    df_filtered = df_processed # .loc[df_processed['is_invalid'] == False] if 'is_invalid' in df_processed else df_processed
    
    if df_filtered.empty:
        print("No valid data remaining after filtering.")
        return pd.DataFrame()

    # --- 3. Group by Question Type and Diagnose ---
    all_diagnostics = []
    grouped = df_filtered.groupby('question_type')

    # Define mapping from question type to diagnosis function
    diagnosis_map = {
        # DI Types
        'DS': _diagnose_ds,
        'TPA': _diagnose_tpa,
        'MSR': _diagnose_msr,
        'GT': _diagnose_gt,
        # Verbal Types
        'CR': _diagnose_cr,
        'RC': _diagnose_rc,
        # Quant Types (Real/Pure handled within _diagnose_q)
        'Real': _diagnose_q,
        'Pure': _diagnose_q,
        # Overall Simulation Types (Added)
        'Quant': _diagnose_q, # Use the same function, it handles overall Q case
        'Verbal': _diagnose_verbal_overall, # New placeholder for overall Verbal
        'DI': _diagnose_di_overall # New placeholder for overall DI
    }

    for name, group in grouped:
        q_type = name # question_type from groupby
        
        # Handle potential multiple types mapping to the same function (like Real/Pure -> _diagnose_q)
        # Find the appropriate function from the map
        diag_func = diagnosis_map.get(q_type)

        if diag_func:
            # Special handling for _diagnose_q which handles both Real and Pure
            if diag_func == _diagnose_q:
                 # Check if this group name ('Real' or 'Pure' or 'Quant') has already been processed by _diagnose_q
                 # We only want to call _diagnose_q once for all relevant Q types.
                 # Collect all Q-related data first.
                 q_subtypes_present = [qt for qt in ['Real', 'Pure', 'Quant'] if qt in grouped.groups]
                 if q_type == q_subtypes_present[0]: # Only process on the *first* Q subtype encountered
                      q_data = pd.concat([grouped.get_group(qt) for qt in q_subtypes_present])
                      result = _diagnose_q(q_data)
                      if result is not None and not result.empty: all_diagnostics.append(result)
            elif diag_func == _diagnose_verbal_overall:
                 # Similar logic if CR/RC also exist and we want one combined Verbal report
                 # For now, just call the overall function if 'Verbal' is the type
                 if q_type == 'Verbal': 
                     result = _diagnose_verbal_overall(group)
                     if result is not None and not result.empty: all_diagnostics.append(result)
                 # If CR/RC exist, they will be handled by their specific entries below
                 # We might want to prevent double-counting later.
            elif diag_func == _diagnose_di_overall:
                 # Similar logic if DS/TPA etc also exist
                 if q_type == 'DI':
                      result = _diagnose_di_overall(group)
                      if result is not None and not result.empty: all_diagnostics.append(result)
                 # Specific DI types handled below.
            else: # Handle specific types like DS, CR, RC etc.
                 # Avoid reprocessing if handled by an overall function (optional refinement)
                 # For now, call specific functions if they exist
                 if q_type not in ['Real', 'Pure', 'Quant', 'Verbal', 'DI']: # Avoid calling _diagnose_q, _diagnose_verbal etc. again
                      result = diag_func(group)
                      if result is not None and not result.empty: all_diagnostics.append(result)
        elif q_type == 'Unknown':
             print(f"Info: Skipping diagnosis for question type '{q_type}'.")
        else:
            # This is where the original warning was likely printed
            print(f"Warning: No diagnosis function explicitly defined or mapped for question type '{q_type}'. Skipping.")

    # --- 4. Consolidate Results ---
    if not all_diagnostics:
        print("No diagnostic results generated.")
        return pd.DataFrame()
        
    try:
        final_results = pd.concat(all_diagnostics, ignore_index=True)
    except Exception as e:
        print(f"Error consolidating diagnostic results: {e}")
        return pd.DataFrame() # Return empty on error

    # TODO: Add further analysis/summarization if needed

    return final_results
