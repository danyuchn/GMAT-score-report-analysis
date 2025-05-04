import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit # Sigmoid function
import logging # Import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        theta (float): The ability estimate.
        history (list[dict]): List of response dictionaries with keys
                               'a', 'b', 'c', 'answered_correctly'.

    Returns:
        float: The negative log-likelihood.

    Raises:
        TypeError: If history is not a list or theta is not numeric.
        ValueError: If items in history are invalid (missing keys, non-numeric params).
    """
    if not isinstance(history, list):
        raise TypeError("History must be a list of response dictionaries.")
    if not isinstance(theta, (int, float, np.number)):
         raise TypeError("Theta must be numeric.")
    if not history:
        return 0.0

    total_neg_ll = 0.0
    epsilon = 1e-9 # To prevent log(0)

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
            P = probability_correct(theta, a, b, c)
        except (ValueError, TypeError) as e:
             # Catch errors from float(), bool(), or probability_correct()
             raise ValueError(f"Invalid data for item at index {i}: {e}") from e

        # Clamp probabilities just before log to avoid log(0)
        P_clipped = np.clip(P, epsilon, 1.0 - epsilon)

        if correct:
            log_prob = np.log(P_clipped)
        else:
            log_prob = np.log(1.0 - P_clipped)

        # Check for NaNs or Infs resulting from log (should be less likely with clipping)
        if np.isnan(log_prob) or np.isinf(log_prob):
            logging.warning(f"Log calculation resulted in NaN/Inf for item {i}. Theta: {theta}, P: {P}, P_clipped: {P_clipped}")
            # Decide handling: raise error, return large value? Raising error is cleaner.
            raise ValueError(f"Log likelihood calculation failed for item {i} (NaN/Inf).")

        total_neg_ll -= log_prob

    return total_neg_ll

def estimate_theta(history, initial_theta_guess=0.0, bounds=(-4, 4)):
    """Estimates theta using Maximum Likelihood Estimation.

    Args:
        history (list[dict]): List of response dictionaries.
        initial_theta_guess (float, optional): Starting point. Defaults to 0.0.
        bounds (tuple, optional): Bounds for theta. Defaults to (-4, 4).

    Returns:
        float: Estimated theta. Returns initial_theta_guess on failure or empty history.
    """
    if not history:
        logging.warning("Cannot estimate theta with empty history. Returning initial guess.")
        return initial_theta_guess

    # Validate history format and initial calculation feasibility *once*
    try:
        # Test with initial guess. neg_log_likelihood will raise errors on bad data.
        _ = neg_log_likelihood(initial_theta_guess, history)
    except (TypeError, ValueError) as e:
        logging.error(f"Invalid history data or initial parameters for theta estimation: {e}")
        return initial_theta_guess

    try:
        result = minimize(
            neg_log_likelihood,
            initial_theta_guess,
            args=(history,),
            method='L-BFGS-B',
            bounds=[bounds]
        )

        if result.success:
            estimated_theta = result.x[0]
            # Clip just in case optimization slightly violates bounds
            estimated_theta = np.clip(estimated_theta, bounds[0], bounds[1])
            return estimated_theta
        else:
            logging.warning(f"Theta estimation optimization failed. Message: {result.message}. Returning initial guess.")
            # Optionally return result.x[0] if available and seems reasonable despite lack of convergence
            return initial_theta_guess
    except (ValueError, TypeError) as e:
        # Catch potential errors from neg_log_likelihood if called by minimize with problematic values
        logging.error(f"Error during optimization process: {e}")
        return initial_theta_guess
    except Exception as e:
        # Catch unexpected errors during minimization
        logging.error(f"Unexpected error during theta estimation: {e}", exc_info=True)
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
        logging.warning("No remaining questions available for selection.")
        return None
    if not all(col in remaining_questions_df.columns for col in required_cols):
        logging.error(f"remaining_questions_df must contain columns: {required_cols}.")
        return None

    # Check if columns are numeric before applying calculations
    numeric_cols = True
    for col in required_cols:
        if not pd.api.types.is_numeric_dtype(remaining_questions_df[col]):
             logging.warning(f"Column '{col}' is not numeric. Attempting conversion.")
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
             logging.warning("NaN or Inf encountered during item information calculation. Treating as zero information.")
             information = information.fillna(0.0).replace([np.inf, -np.inf], 0.0)

    except (TypeError, ValueError) as e:
        # Catch errors from float conversion or item_information itself
        logging.error(f"Error calculating item information across DataFrame: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error calculating item information: {e}", exc_info=True)
        return None

    # Find the index (question ID) of the question with the maximum *positive* information
    if information.empty or information.max() <= 1e-9: # Use small threshold instead of zero
         logging.warning(f"Could not find a question with positive information at theta={theta:.3f}.")
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
        logging.error("num_questions must be a positive integer.")
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

def simulate_cat_exam(question_bank, wrong_question_positions, initial_theta, total_questions, theta_bounds=(-4, 4)):
    """Simulates a Computerized Adaptive Test (CAT) exam section.

    Args:
        question_bank (pd.DataFrame): Item bank with 'a', 'b', 'c', and index as ID.
        wrong_question_positions (list[int]): 1-based list of question *positions*
                                              (1st question, 2nd question, etc.) answered incorrectly.
        initial_theta (float): Starting ability estimate.
        total_questions (int): Number of questions to administer.
        theta_bounds (tuple, optional): Bounds for theta estimation.

    Returns:
        pd.DataFrame: Simulation history, or empty DataFrame on failure.
    """
    # --- Input Validation ---
    if not isinstance(question_bank, pd.DataFrame) or not all(col in question_bank.columns for col in ['a', 'b', 'c']):
        logging.error("Invalid question_bank DataFrame format (missing a/b/c).")
        return pd.DataFrame() # Return empty DataFrame
    # Check if index is suitable as ID (e.g., unique) - assumes index is the ID here
    if not question_bank.index.is_unique:
        logging.warning("Question bank index is not unique. Selection might be ambiguous.")
        # Or try using an 'id' column if available: question_bank.set_index('id', inplace=True) if 'id' in question_bank.columns else error...

    if not isinstance(wrong_question_positions, list):
        logging.error("wrong_question_positions must be a list.")
        return pd.DataFrame()
    if not isinstance(initial_theta, (int, float, np.number)):
        logging.error("initial_theta must be numeric.")
        return pd.DataFrame()
    if not isinstance(total_questions, int) or total_questions <= 0:
        logging.error("total_questions must be a positive integer.")
        return pd.DataFrame()
    if total_questions > len(question_bank):
         logging.warning(f"total_questions ({total_questions}) exceeds bank size ({len(question_bank)}). Adjusting.")
         total_questions = len(question_bank)
    if not question_bank.index.name: # Often useful to have a named index
        question_bank.index.name = 'question_id' # Assume index is the ID

    # --- Simulation Setup ---
    # Use the index of the bank directly, assuming it represents unique question IDs
    remaining_questions_df = question_bank.copy()
    history = [] # Stores response dicts for theta estimation
    results_log = [] # Stores more detailed info for the final output DataFrame
    theta_est = initial_theta

    logging.info(f"Starting CAT simulation: Initial Theta = {theta_est:.3f}, Total Questions = {total_questions}")

    # --- Simulation Loop ---
    for i in range(total_questions):
        question_number = i + 1 # 1-based position in the test sequence
        theta_before = theta_est

        # Select next question (returns index label/ID)
        next_q_id = select_next_question(theta_est, remaining_questions_df)
        if next_q_id is None:
            logging.error(f"Could not select next question at step {question_number}. Stopping simulation.")
            break

        # Get question parameters using the selected ID (index)
        question_params = remaining_questions_df.loc[next_q_id]

        # Determine correctness based on *position*
        answered_correctly = question_number not in wrong_question_positions

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

        logging.info(f"  Q {question_number}: ID={next_q_id}, b={question_params['b']:.2f}, "
                     f"Answer={'Correct' if answered_correctly else 'Incorrect'}, New Theta={theta_est:.3f}")

    logging.info(f"Simulation finished. Final Theta = {theta_est:.3f}")

    return pd.DataFrame(results_log)