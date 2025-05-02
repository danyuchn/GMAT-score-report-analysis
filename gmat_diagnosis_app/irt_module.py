import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit # Sigmoid function

def probability_correct(theta, a, b, c):
    """Calculates the probability of a correct response using the 3PL IRT model.

    Args:
        theta (float): Examinee's ability estimate.
        a (float): Item discrimination parameter.
        b (float): Item difficulty parameter.
        c (float): Item guessing parameter (lower asymptote).

    Returns:
        float: Probability of a correct response.
    """
    # P = c + (1 - c) * sigmoid(a * (theta - b))
    if not all(isinstance(p, (int, float)) for p in [theta, a, b, c]):
        raise TypeError("All parameters (theta, a, b, c) must be numeric.")
    # Ensure c is within the valid range [0, 1]
    if not (0 <= c <= 1):
         # Using print for now, consider logging or raising specific errors in production
         print(f"Warning: Guessing parameter c={c} is outside the typical [0, 1] range. Clipping.")
         c = np.clip(c, 0, 1)

    linear_component = a * (theta - b)
    probability = c + (1 - c) * expit(linear_component)
    return probability

def item_information(theta, a, b, c):
    """Calculates the Fisher Information for an item at a given ability level (3PL model).
       Uses the formula found in the reference notebook.

    Args:
        theta (float): Examinee's ability estimate.
        a (float): Item discrimination parameter.
        b (float): Item difficulty parameter.
        c (float): Item guessing parameter.

    Returns:
        float: Item information. Returns 0 if c=1 to avoid division by zero.
    """
    if not all(isinstance(p, (int, float)) for p in [theta, a, b, c]):
        raise TypeError("All parameters (theta, a, b, c) must be numeric.")

    # Ensure c is in [0, 1) for the formula division
    if not (0 <= c < 1):
        if c >= 1.0: # If c is 1 or more, information is effectively 0
             return 0.0
        else: # If c < 0, clip it to 0 for calculation, though unusual
            print(f"Warning: Guessing parameter c={c} is below 0. Clipping to 0 for information calculation.")
            c = 0.0

    P = probability_correct(theta, a, b, c)

    # Clip P slightly away from 0 and 1 for numerical stability
    epsilon = 1e-9
    P_clipped = np.clip(P, epsilon, 1.0 - epsilon)
    Q_clipped = 1.0 - P_clipped

    # Formula from the reference notebook: (a^2 * P * Q) / (1 - c)^2
    # Note: Standard 3PL Fisher Information is typically I = a^2 * Q * (P-c)^2 / (P * (1-c)^2).
    # Using the notebook's version for consistency as requested.
    denominator = (1.0 - c) ** 2
    # Avoid division by zero if c is exactly 1 (already handled by the check above, but good practice)
    if denominator < epsilon:
        return 0.0

    information = (a ** 2) * P_clipped * Q_clipped / denominator
    return information


def neg_log_likelihood(theta, history):
    """Calculates the negative log-likelihood of a response history given a theta.

    Args:
        theta (float): The ability estimate.
        history (list[dict]): A list of dictionaries, where each dictionary represents
                               a response and must contain keys 'a', 'b', 'c'
                               (item parameters) and 'answered_correctly' (bool).

    Returns:
        float: The negative log-likelihood. Returns float('inf') if invalid inputs lead to errors.
    """
    if not isinstance(history, list):
        raise TypeError("History must be a list of response dictionaries.")
    if not history:
        return 0.0 # Log-likelihood is zero for no data

    total_neg_ll = 0.0
    epsilon = 1e-9 # To prevent log(0)

    for i, resp in enumerate(history):
        if not isinstance(resp, dict) or not all(k in resp for k in ['a', 'b', 'c', 'answered_correctly']):
            raise ValueError(f"Item at index {i} in history is missing required keys ('a', 'b', 'c', 'answered_correctly') or is not a dict.")

        try:
            a = float(resp['a'])
            b = float(resp['b'])
            c = float(resp['c'])
            correct = bool(resp['answered_correctly'])
            theta_val = float(theta) # Ensure theta is float for calculations
        except (ValueError, TypeError) as e:
             print(f"Error converting parameters to numbers for item at index {i}: {e}")
             return float('inf') # Return infinity on bad data

        P = probability_correct(theta_val, a, b, c)

        # Clamp probabilities to avoid log(0)
        P_clipped = np.clip(P, epsilon, 1.0 - epsilon)

        if correct:
            log_prob = np.log(P_clipped)
        else:
            log_prob = np.log(1.0 - P_clipped)

        # Check for NaNs or Infs resulting from log
        if np.isnan(log_prob) or np.isinf(log_prob):
            print(f"Warning: Log calculation resulted in NaN or Inf for item {i}. Theta: {theta_val}, P: {P}, P_clipped: {P_clipped}")
            # Decide handling: return large value, skip item, etc. Returning large value for minimization.
            return float('inf')

        total_neg_ll -= log_prob

    return total_neg_ll

def estimate_theta(history, initial_theta_guess=0.0, bounds=(-4, 4)):
    """Estimates the ability parameter (theta) using Maximum Likelihood Estimation.

    Args:
        history (list[dict]): List of response dictionaries (see neg_log_likelihood).
        initial_theta_guess (float, optional): Starting point for the optimization. Defaults to 0.0.
        bounds (tuple, optional): Bounds for the theta estimate during optimization. Defaults to (-4, 4).

    Returns:
        float: The estimated theta value. Returns initial_theta_guess if history is empty
               or optimization fails.
    """
    if not history:
        print("Warning: Cannot estimate theta with empty history. Returning initial guess.")
        return initial_theta_guess

    # Validate history format once before optimization
    try:
        test_ll = neg_log_likelihood(initial_theta_guess, history)
        if np.isinf(test_ll): # Check if initial calculation yields infinity
             print(f"Warning: Initial neg_log_likelihood is infinite for guess {initial_theta_guess}. Check history data or bounds.")
             # Maybe try a different starting point or return guess? Returning guess.
             return initial_theta_guess
    except (TypeError, ValueError) as e:
        print(f"Error validating history format for theta estimation: {e}")
        return initial_theta_guess # Return guess if format is bad

    # Minimize the negative log-likelihood function
    result = minimize(
        neg_log_likelihood,
        initial_theta_guess,
        args=(history,),
        method='L-BFGS-B', # Method supporting bounds
        bounds=[bounds]     # Pass bounds as a list containing one tuple
    )

    if result.success:
        estimated_theta = result.x[0]
        # Ensure estimate is strictly within bounds if needed, though L-BFGS-B should respect them
        estimated_theta = np.clip(estimated_theta, bounds[0], bounds[1])
        return estimated_theta
    else:
        print(f"Warning: Theta estimation optimization failed. Message: {result.message}. Returning initial guess.")
        # Consider returning result.x[0] anyway if available, or stick to initial guess
        return initial_theta_guess


def select_next_question(theta, remaining_questions_df):
    """Selects the next question to administer based on maximum item information.

    Args:
        theta (float): Current ability estimate.
        remaining_questions_df (pd.DataFrame): DataFrame of available questions.
                                               Must contain 'a', 'b', 'c' columns.
                                               The index should represent the question identifier.

    Returns:
        The index label (identifier) of the selected question. Returns None if no
        questions remain, the DataFrame is invalid, or information cannot be calculated.
    """
    if not isinstance(remaining_questions_df, pd.DataFrame) or remaining_questions_df.empty:
        print("Warning: No remaining questions available for selection.")
        return None
    if not all(col in remaining_questions_df.columns for col in ['a', 'b', 'c']):
        print("Error: remaining_questions_df must contain 'a', 'b', and 'c' columns.")
        return None

    # Ensure parameters are numeric before applying calculation
    try:
        q_df = remaining_questions_df[['a', 'b', 'c']].astype(float)
    except (ValueError, TypeError) as e:
        print(f"Error converting question parameters to float: {e}")
        return None

    # Calculate information for all remaining questions at the current theta
    try:
        information = q_df.apply(
            lambda row: item_information(theta, row['a'], row['b'], row['c']),
            axis=1
        )
        # Check for NaNs or Infs in calculated information
        if information.isnull().any() or np.isinf(information).any():
             print("Warning: NaN or Inf encountered during item information calculation. Handling these as low/zero information.")
             # Replace NaN/Inf with a very small number or zero to avoid selecting them
             information = information.fillna(0.0).replace([np.inf, -np.inf], 0.0)

    except Exception as e:
        # Catch any other exceptions during apply
        print(f"Error calculating item information across DataFrame: {e}")
        return None

    # Find the index (question ID) of the question with the maximum information
    if information.empty or information.max() <= 0: # Check if max info is non-positive
         print("Warning: Could not find a question with positive information.")
         # Handle this case: maybe return a random question, or the least difficult?
         # Returning None for now.
         return None

    selected_question_idx = information.idxmax()
    return selected_question_idx

# --- Simulation Functions (Added based on Notebook Logic) ---

def initialize_question_bank(num_questions=1000, seed=None):
    """Creates a simulated question bank with random IRT parameters.

    Args:
        num_questions (int, optional): Number of questions in the bank. Defaults to 1000.
        seed (int, optional): Random seed for reproducibility. Defaults to None.

    Returns:
        pd.DataFrame: DataFrame with columns ['id', 'a', 'b', 'c'].
                      Returns None if num_questions is invalid.
    """
    if not isinstance(num_questions, int) or num_questions <= 0:
        print("Error: num_questions must be a positive integer.")
        return None

    if seed is not None:
        np.random.seed(seed)

    # Parameter ranges similar to the notebook
    a_params = np.random.uniform(0.2, 1.5, num_questions)
    b_params = np.random.uniform(-2, 2, num_questions)
    c_params = np.random.uniform(0.1, 0.25, num_questions)

    question_bank = pd.DataFrame({
        'a': a_params,
        'b': b_params,
        'c': c_params,
        'id': np.arange(1, num_questions + 1) # Assign unique IDs
    })
    return question_bank

def simulate_cat_exam(question_bank, wrong_question_indices, initial_theta, total_questions, theta_bounds=(-4, 4)):
    """Simulates a Computerized Adaptive Test (CAT) exam section.

    Args:
        question_bank (pd.DataFrame): The item bank (from initialize_question_bank).
        wrong_question_indices (list[int]): 1-based list of question *positions* answered incorrectly.
        initial_theta (float): Starting ability estimate.
        total_questions (int): The number of questions to administer in this section.
        theta_bounds (tuple, optional): Bounds for theta estimation. Defaults to (-4, 4).

    Returns:
        pd.DataFrame: DataFrame containing the simulation history, including columns:
                      ['question_number', 'question_id', 'a', 'b', 'c',
                       'answered_correctly', 'theta_est_before_answer', 'theta_est_after_answer'].
                      Returns None if inputs are invalid.
    """
    # Input validation
    if not isinstance(question_bank, pd.DataFrame) or not all(col in question_bank.columns for col in ['a', 'b', 'c', 'id']):
        print("Error: Invalid question_bank DataFrame format.")
        return None
    if not isinstance(wrong_question_indices, list):
        print("Error: wrong_question_indices must be a list.")
        return None
    if not isinstance(initial_theta, (int, float)):
        print("Error: initial_theta must be numeric.")
        return None
    if not isinstance(total_questions, int) or total_questions <= 0:
        print("Error: total_questions must be a positive integer.")
        return None
    if total_questions > len(question_bank):
         print(f"Warning: total_questions ({total_questions}) exceeds bank size ({len(question_bank)}). Adjusting total questions.")
         total_questions = len(question_bank)

    remaining_questions = question_bank.copy()
    history = []
    theta_est = initial_theta

    print(f"Starting simulation: Initial Theta = {theta_est:.2f}, Total Questions = {total_questions}")

    for i in range(total_questions):
        question_number = i + 1
        theta_before = theta_est # Record theta before selecting/answering

        # Select the next question based on current theta estimate
        next_q_idx = select_next_question(theta_est, remaining_questions)
        if next_q_idx is None:
            print(f"Error: Could not select next question at step {question_number}. Stopping simulation.")
            break # Stop simulation if no question can be selected

        question = remaining_questions.loc[next_q_idx]

        # Determine if the answer is correct based on the provided list of wrong indices
        answered_correctly = question_number not in wrong_question_indices

        # Append response to history *before* updating theta
        response_info = {
            'question_number': question_number,
            'question_id': question['id'], # ID from the bank
            'a': question['a'],
            'b': question['b'], # This is the difficulty parameter
            'c': question['c'],
            'answered_correctly': answered_correctly,
            'theta_est_before_answer': theta_before
            # 'theta_est_after_answer' will be added after estimation
        }
        current_history_for_estimation = history + [response_info] # Use current step info for estimation

        # Estimate new theta based on the updated history
        theta_est = estimate_theta(current_history_for_estimation, theta_est, bounds=theta_bounds)

        # Add the updated theta to the history entry for this step
        response_info['theta_est_after_answer'] = theta_est
        history.append(response_info)

        # Remove the administered question from the bank
        remaining_questions = remaining_questions.drop(next_q_idx)

        print(f"  Q {question_number}: ID={question['id']}, b={question['b']:.2f}, Answer={'Correct' if answered_correctly else 'Incorrect'}, New Theta={theta_est:.2f}")

    print(f"Simulation finished. Final Theta = {theta_est:.2f}")

    if not history:
        return pd.DataFrame() # Return empty DataFrame if simulation didn't run

    return pd.DataFrame(history)
