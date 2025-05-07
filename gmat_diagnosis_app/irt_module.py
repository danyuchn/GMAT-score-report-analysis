# -*- coding: utf-8 -*-
"""
GMAT 診斷應用 IRT 模組 (轉發器)
此檔案僅作為向後兼容性的轉發器，所有功能已移至 gmat_diagnosis_app.irt 子包
"""

# 引入新的 irt 子包中的所有內容，以保持與舊引入方式的兼容性
from gmat_diagnosis_app.irt import (
    probability_correct,
    item_information,
    neg_log_likelihood,
    estimate_theta,
    select_next_question,
    initialize_question_bank,
    simulate_cat_exam
)

import logging
import warnings

# 顯示棄用警告
warnings.warn(
    "直接引用 irt_module.py 已棄用，請改用 gmat_diagnosis_app.irt 子包",
    DeprecationWarning,
    stacklevel=2
)

# 設定模組 logger 作為向後兼容
logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit # Sigmoid function
from scipy.stats import norm

# Configure basic logging (this might be better in the main app entry point)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def probability_correct(theta, a, b, c):
    """Calculates the probability of a correct response using the 3PL IRT model.

    Args:
        theta (float): Examinee's ability estimate.
        a (float): Item discrimination parameter.
        b (float): Item difficulty parameter.
        c (float): Item guessing parameter (lower asymptote).

    Returns:
        float: Probability of a correct response.

    Raises:
        TypeError: If any input parameter is not numeric.
        ValueError: If 'c' is outside the valid [0, 1] range (stricter than original).
                    Alternatively, keep clipping but log a warning.
    """
    # Stricter validation: raise errors instead of just printing warnings/clipping implicitly.
    if not all(isinstance(p, (int, float, np.number)) for p in [theta, a, b, c]):
        raise TypeError("All parameters (theta, a, b, c) must be numeric.")
    if not (0 <= c <= 1):
        # Option 1: Strict - Raise error
        raise ValueError(f"Guessing parameter c={c} is outside the valid [0, 1] range.")
        # Option 2: Clip but warn loudly
        # logging.warning(f"Guessing parameter c={c} is outside [0, 1]. Clipping to range.")
        # c = np.clip(c, 0, 1)

    linear_component = a * (theta - b)
    probability = c + (1 - c) * expit(linear_component)
    # Ensure probability is within [0, 1] due to potential float inaccuracies
    return np.clip(probability, 0.0, 1.0)

def item_information(theta, a, b, c):
    """Calculates the Fisher Information for an item (3PL model, notebook formula).

    Args:
        theta (float): Examinee's ability estimate.
        a (float): Item discrimination parameter.
        b (float): Item difficulty parameter.
        c (float): Item guessing parameter.

    Returns:
        float: Item information. Returns 0 if c=1.

    Raises:
        TypeError: If any input parameter is not numeric.
        ValueError: If 'c' is outside the valid [0, 1) range for the formula.
                     (Note: probability_correct already checks [0, 1]).
    """
    # probability_correct will handle initial type/range checks for c in [0,1]
    # We only need to ensure c is not exactly 1 for the denominator.
    if not isinstance(theta, (int, float, np.number)): # Check theta separately if needed
         raise TypeError("Theta must be numeric.")
    if not (0 <= c < 1):
        if np.isclose(c, 1.0) or c > 1.0: # If c is effectively 1 or more
            return 0.0
        else: # c < 0, already handled by probability_correct raising ValueError
             # If probability_correct clips instead, this check might be needed
             raise ValueError(f"Guessing parameter c={c} cannot be negative for information calculation.")

    # This will raise errors if params are invalid based on probability_correct's rules
    P = probability_correct(theta, a, b, c)

    # Clip P slightly away from 0 and 1 for numerical stability in division/logs (if any)
    # Although the formula used here might not strictly need it, it's safer.
    epsilon = 1e-9
    P_clipped = np.clip(P, epsilon, 1.0 - epsilon)
    Q_clipped = 1.0 - P_clipped # Q based on clipped P

    # Formula from the reference notebook: (a^2 * P_clipped * Q_clipped) / (1 - c)^2
    # Denominator check implicitly handled by the c < 1 check above.
    denominator = (1.0 - c) ** 2
    # Added check for extremely small denominator just in case
    if denominator < epsilon:
        return 0.0

    information = (a ** 2) * P_clipped * Q_clipped / denominator
    return information


def neg_log_likelihood(theta, history):
    """Calculates the negative log-likelihood of a response history given theta.

    Args:
        theta (float or np.ndarray): Ability estimate(s). Typically a float or a numpy array with one element from optimizer.
        history (list[dict]): List of response dictionaries with keys
                               'a', 'b', 'c', 'answered_correctly'.

    Returns:
        float: The negative log-likelihood.

    Raises:
        TypeError: If history is not a list or theta is not numeric.
        ValueError: If items in history are invalid (missing keys, non-numeric params).
    """
    logger.debug(f"neg_log_likelihood called with theta type: {type(theta)}, value: {theta}")

    # --- More robust handling of theta from scipy.optimize.minimize ---
    # Minimize often passes a numpy array, even for a scalar objective function.
    if isinstance(theta, np.ndarray):
        if theta.size == 1:
            current_theta = float(theta[0]) # Extract scalar value
        else:
            # This case should not happen for scalar optimization like L-BFGS-B
            logger.error(f"neg_log_likelihood received unexpected numpy array theta shape: {theta.shape}")
            return np.inf # Indicate error
    elif isinstance(theta, (int, float, np.number)):
         current_theta = float(theta)
    # --- Check for list/tuple as a fallback, although less likely from minimize ---
    elif isinstance(theta, (list, tuple)):
         if len(theta) == 1 and isinstance(theta[0], (int, float, np.number)):
             current_theta = float(theta[0])
         else:
              logger.error(f"neg_log_likelihood received unsupported list/tuple theta format: {theta}")
              return np.inf
    else:
        # If none of the above, log the type and raise error
        logger.error(f"neg_log_likelihood received non-numeric theta type: {type(theta)}, value: {theta}")
        raise TypeError("Theta must be numeric or a single-element array/list.") # More specific error

    # --- Original log-likelihood calculation ---
    log_likelihood = 0.0
    tiny_val = 1e-9 # Small value to prevent log(0)

    for i, resp in enumerate(history):
        # Check format concisely
        if not isinstance(resp, dict) or not {'a', 'b', 'c', 'answered_correctly'}.issubset(resp):
            raise ValueError(f"Item at index {i} in history is invalid (not dict or missing keys).")

        try:
            # Convert and validate parameters via probability_correct
            a = float(resp['a'])
            b = float(resp['b'])
            c = float(resp['c'])
            correct = bool(resp['answered_correctly'])
            # probability_correct will raise error if a,b,c invalid or c outside [0,1]
            P = probability_correct(current_theta, a, b, c)
        except (ValueError, TypeError) as e:
             # Catch errors from float(), bool(), or probability_correct()
             raise ValueError(f"Invalid data for item at index {i}: {e}") from e

        # Clamp probabilities just before log to avoid log(0)
        P_clipped = np.clip(P, tiny_val, 1.0 - tiny_val)

        if correct:
            log_likelihood += np.log(P_clipped)
        else:
            log_likelihood += np.log(1.0 - P_clipped)

        # Check for NaNs or Infs resulting from log (should be less likely with clipping)
        if np.isnan(log_likelihood) or np.isinf(log_likelihood):
            logger.warning(f"Log calculation resulted in NaN/Inf for item {i}. Theta: {current_theta}, P: {P}, P_clipped: {P_clipped}")
            # Decide handling: raise error, return large value? Raising error is cleaner.
            raise ValueError(f"Log likelihood calculation failed for item {i} (NaN/Inf).")

    # Check for NaN or Inf likelihood which can stop optimization
    if np.isnan(log_likelihood) or np.isinf(log_likelihood):
        logger.warning(f"Log-likelihood became NaN or Inf for theta={current_theta:.4f}. History length={len(history)}. Returning Inf.")
        return np.inf

    return -log_likelihood # Return negative for minimization

def estimate_theta(history, initial_theta_guess=0.0, bounds=(-4, 4)):
    """Estimates the ability (theta) based on response history.

    Args:
        history (list[dict]): List of response dictionaries, each containing
                               'a', 'b', 'c', 'answered_correctly'.
        initial_theta_guess (float): Starting point for the optimizer.
        bounds (tuple): Lower and upper bounds for theta.

    Returns:
        float: Estimated theta, or initial_theta_guess on failure.
    """
    if not history:
        logger.info("Theta estimation: No history provided, returning initial guess.")
        return initial_theta_guess

    try:
        # Ensure bounds format is correct for minimize
        bounds_list = [bounds]

        result = minimize(
            neg_log_likelihood,
            initial_theta_guess,
            args=(history,),
            method='L-BFGS-B',
            bounds=bounds_list
        )

        if result.success:
            estimated_theta = result.x[0]
            # Clamp the result within the bounds explicitly
            final_theta = np.clip(estimated_theta, bounds[0], bounds[1])
            logger.debug(f"Theta estimation successful. Theta: {final_theta:.4f} (Optimizer status: {result.message})")
            return final_theta
        else:
            # Log detailed failure information
            logger.warning(f"Theta estimation optimization FAILED. Status: {result.status}, Message: {result.message}")
            logger.warning(f"Optimizer Result Details: {result}") # Log the full result object for debugging
            logger.warning(f"Returning previous guess: {initial_theta_guess:.4f}")
            return initial_theta_guess # Return previous guess

    except ValueError as ve:
        # This might catch the TypeError from neg_log_likelihood now, or other value issues
        logger.error(f"ValueError or TypeError during theta estimation (check history data or theta type?): {ve}")
        return initial_theta_guess
    except Exception as e:
        logger.error(f"Unexpected error during theta estimation: {e}", exc_info=True)
        return initial_theta_guess


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

# --- Simulation Functions ---

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