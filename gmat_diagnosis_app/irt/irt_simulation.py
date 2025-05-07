# -*- coding: utf-8 -*-
"""
IRT simulation functions.
從irt_module.py分離出來的模擬和題庫功能。
"""

import numpy as np
import pandas as pd
import logging

# Import from core
from gmat_diagnosis_app.irt.irt_core import (
    probability_correct, 
    item_information, 
    estimate_theta
)

# Configure module-level logger
logger = logging.getLogger(__name__) # Define module-level logger

def select_next_question(theta, remaining_questions_df):
    """Selects the next question based on maximum item information.

    Args:
        theta (float): Current ability estimate.
        remaining_questions_df (pd.DataFrame): DataFrame with 'a', 'b', 'c' columns and question ID index.

    Returns:
        Index label of the selected question, or None on failure.
    """
    required_cols = ['a', 'b', 'c']
    if not isinstance(remaining_questions_df, pd.DataFrame) or remaining_questions_df.empty:
        logger.warning("No remaining questions available for selection.")
        return None
    if not all(col in remaining_questions_df.columns for col in required_cols):
        logger.error(f"remaining_questions_df must contain columns: {required_cols}.")
        return None

    # Check if columns are numeric before applying calculations
    numeric_cols = True
    for col in required_cols:
        if not pd.api.types.is_numeric_dtype(remaining_questions_df[col]):
             logger.warning(f"Column '{col}' is not numeric. Attempting conversion.")
             numeric_cols = False
             # Attempt conversion here or let apply handle it (might be slower)

    q_df = remaining_questions_df[required_cols]

    # Calculate information for all remaining questions
    try:
        information = q_df.apply(
            # Ensure parameters passed to item_information are floats
            lambda row: item_information(theta, float(row['a']), float(row['b']), float(row['c'])),
            axis=1
        )
        # Handle potential NaN/Inf results robustly
        if information.isnull().any() or np.isinf(information).any():
             logger.warning("NaN or Inf encountered during item information calculation. Treating as zero information.")
             information = information.fillna(0.0).replace([np.inf, -np.inf], 0.0)

    except (TypeError, ValueError) as e:
        # Catch errors from float conversion or item_information itself
        logger.error(f"Error calculating item information across DataFrame: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calculating item information: {e}", exc_info=True)
        return None

    # Find the index (question ID) of the question with the maximum *positive* information
    if information.empty or information.max() <= 1e-9: # Use small threshold instead of zero
         logger.warning(f"Could not find a question with positive information at theta={theta:.3f}.")
         # Fallback strategy: Maybe choose the question with b closest to theta?
         # Or just return None if no informative question exists.
         return None

    selected_question_idx = information.idxmax()
    return selected_question_idx

def initialize_question_bank(num_questions=1000, seed=None):
    """Creates a simulated question bank with random IRT parameters.

    Args:
        num_questions (int): Number of questions.
        seed (int, optional): Random seed.

    Returns:
        pd.DataFrame or None: DataFrame with ['id', 'a', 'b', 'c'] or None if invalid input.
    """
    if not isinstance(num_questions, int) or num_questions <= 0:
        logger.error("num_questions must be a positive integer.")
        return None

    rng = np.random.default_rng(seed) # Modern way to handle seeding

    # Parameter ranges (adjust as needed)
    a_params = rng.uniform(0.2, 1.5, num_questions)
    b_params = rng.uniform(-2, 2, num_questions)
    c_params = rng.uniform(0.1, 0.25, num_questions) # Ensure c is within [0,1)

    question_bank = pd.DataFrame({
        'a': a_params,
        'b': b_params,
        'c': c_params,
        # Use 0-based index internally, convert to 1-based ID if needed for display/output
        'id': np.arange(num_questions) # Or 1 to num_questions+1 if preferred ID
    })
    # Set index to be the question ID for easier selection later if 'id' is unique identifier
    # question_bank.set_index('id', inplace=True)
    return question_bank

def simulate_cat_exam(question_bank, wrong_question_positions, initial_theta, total_questions, theta_bounds=(-4, 4),
                        incorrect_to_correct_qns: set[int] = None, 
                        correct_to_incorrect_qns: set[int] = None):
    """Simulates a Computerized Adaptive Test (CAT) exam section.

    Args:
        question_bank (pd.DataFrame): Item bank with 'a', 'b', 'c', and index as ID.
        wrong_question_positions (list[int]): 1-based list of question *positions*
                                              (1st question, 2nd question, etc.) answered incorrectly.
        initial_theta (float): Starting ability estimate.
        total_questions (int): Number of questions to administer.
        theta_bounds (tuple, optional): Bounds for theta estimation.
        incorrect_to_correct_qns (set[int], optional): Set of 1-based question positions to be treated as correct for IRT.
        correct_to_incorrect_qns (set[int], optional): Set of 1-based question positions to be treated as incorrect for IRT.

    Returns:
        pd.DataFrame: Simulation history, or empty DataFrame on failure.
    """
    # --- Input Validation ---
    if not isinstance(question_bank, pd.DataFrame) or not all(col in question_bank.columns for col in ['a', 'b', 'c']):
        logger.error("Invalid question_bank DataFrame format (missing a/b/c).")
        return pd.DataFrame() # Return empty DataFrame
    # Check if index is suitable as ID (e.g., unique) - assumes index is the ID here
    if not question_bank.index.is_unique:
        logger.warning("Question bank index is not unique. Selection might be ambiguous.")
        # Or try using an 'id' column if available: question_bank.set_index('id', inplace=True) if 'id' in question_bank.columns else error...

    if not isinstance(wrong_question_positions, list):
        logger.error("wrong_question_positions must be a list.")
        return pd.DataFrame()
    if not isinstance(initial_theta, (int, float, np.number)):
        logger.error("initial_theta must be numeric.")
        return pd.DataFrame()
    if not isinstance(total_questions, int) or total_questions <= 0:
        logger.error("total_questions must be a positive integer.")
        return pd.DataFrame()
    if total_questions > len(question_bank):
         logger.warning(f"total_questions ({total_questions}) exceeds bank size ({len(question_bank)}). Adjusting.")
         total_questions = len(question_bank)
    if not question_bank.index.name: # Often useful to have a named index
        question_bank.index.name = 'question_id' # Assume index is the ID

    # --- Simulation Setup ---
    # Use the index of the bank directly, assuming it represents unique question IDs
    remaining_questions_df = question_bank.copy()
    history = [] # Stores response dicts for theta estimation
    results_log = [] # Stores more detailed info for the final output DataFrame
    theta_est = initial_theta

    # Initialize adjustment sets safely
    effective_i_to_c = incorrect_to_correct_qns if incorrect_to_correct_qns is not None else set()
    effective_c_to_i = correct_to_incorrect_qns if correct_to_incorrect_qns is not None else set()

    logger.debug(f"Starting CAT simulation: Initial Theta = {theta_est:.3f}, Total Questions = {total_questions}")
    if effective_i_to_c:
        logger.debug(f"  Adjusting to CORRECT: Positions {effective_i_to_c}")
    if effective_c_to_i:
        logger.debug(f"  Adjusting to INCORRECT: Positions {effective_c_to_i}")

    # --- Simulation Loop ---
    for i in range(total_questions):
        question_number = i + 1 # 1-based position in the test sequence
        theta_before = theta_est

        # Select next question (returns index label/ID)
        next_q_id = select_next_question(theta_est, remaining_questions_df)
        if next_q_id is None:
            logger.error(f"Could not select next question at step {question_number}. Stopping simulation.")
            break

        # Get question parameters using the selected ID (index)
        question_params = remaining_questions_df.loc[next_q_id]

        # Determine correctness based on *position* and adjustments
        original_answered_correctly = question_number not in wrong_question_positions
        
        # Apply adjustments
        answered_correctly = original_answered_correctly
        if question_number in effective_i_to_c:
            answered_correctly = True
            logger.debug(f"  Q {question_number} (ID={next_q_id}): Original correct={original_answered_correctly}, Adjusted to CORRECT.")
        if question_number in effective_c_to_i: # This will override i_to_c if qn is in both
            answered_correctly = False
            logger.debug(f"  Q {question_number} (ID={next_q_id}): Original correct={original_answered_correctly}, Adjusted to INCORRECT.")

        # Prepare response info for history (used in theta estimation)
        # Ensure keys match neg_log_likelihood requirements
        response_info_for_est = {
            'a': question_params['a'],
            'b': question_params['b'],
            'c': question_params['c'],
            'answered_correctly': answered_correctly,
            # Add other info if neg_log_likelihood needs it
        }
        # Append to history *before* estimation (more efficient)
        history.append(response_info_for_est)

        # Estimate new theta using the *entire* history up to this point
        theta_est = estimate_theta(history, theta_est, bounds=theta_bounds) # Pass updated history

        # Log detailed results for this step
        step_result = {
            'question_number': question_number,
            'question_id': next_q_id, # The ID from the bank index
            'a': question_params['a'],
            'b': question_params['b'],
            'c': question_params['c'],
            'answered_correctly': answered_correctly,
            'theta_est_before_answer': theta_before,
            'theta_est_after_answer': theta_est
        }
        results_log.append(step_result)

        # Remove administered question from the *copy*
        remaining_questions_df = remaining_questions_df.drop(next_q_id)

        # No need for 'if logger:' if logger is defined at module level and always available
        b_val_formatted = format(question_params['b'], '.2f')
        logger.debug(f"  Q {question_number}: ID={next_q_id}, b={b_val_formatted}, "
                     f"Answer={'Correct' if answered_correctly else 'Incorrect'}, New Theta={theta_est:.3f}")

    logger.debug(f"Simulation finished. Final Theta = {theta_est:.3f}")

    return pd.DataFrame(results_log) 