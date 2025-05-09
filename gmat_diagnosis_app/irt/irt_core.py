# -*- coding: utf-8 -*-
"""
Core IRT calculation functions.
從irt_module.py分離出來的核心計算功能。
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit  # Sigmoid function
import logging  # Import logging

# Configure module-level logger
logger = logging.getLogger(__name__) # Define module-level logger

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