import numpy as np
import pandas as pd

def estimate_difficulty(df):
    """Estimates the difficulty parameter (b) for each question using a simple method.

    Args:
        df (pd.DataFrame): DataFrame containing response data. 
                           Must have columns like 'Question ID', 'Correct'.

    Returns:
        pd.Series: A Series containing the estimated difficulty for each unique question ID,
                   indexed by 'Question ID'. Returns None if input is invalid.
    """
    if not isinstance(df, pd.DataFrame) or 'Question ID' not in df.columns or 'Correct' not in df.columns:
        print("Invalid input: DataFrame must contain 'Question ID' and 'Correct' columns.")
        # In a Streamlit context, you might want to use st.error instead of print
        # or raise an exception to be caught in the main app
        return None # Or raise ValueError("Invalid input DataFrame")

    # Calculate the proportion of correct answers for each question
    # Assuming 'Correct' column contains 1 for correct, 0 for incorrect
    difficulty_estimates = df.groupby('Question ID')['Correct'].mean()

    # Convert proportion correct to difficulty (logit scale approximation)
    # Avoid division by zero or log(0) for proportions of 0 or 1
    epsilon = 1e-6 # Small value to prevent log(0)
    proportion_correct = difficulty_estimates.clip(epsilon, 1 - epsilon)
    
    # Simple inverse relationship: higher proportion correct -> lower difficulty
    # We can use a simple transformation, e.g., inverse or logit-like
    # Using a logit-like transformation: log(p / (1-p))
    # Difficulty is often inversely related to p, so we might take the negative logit
    # Or simply use a scale where lower values mean easier (higher p)
    # Let's use a simple inverse scaling for now, mapped to a reasonable range if needed.
    # A common IRT scale is roughly -3 to +3. Higher values = harder.
    # Higher p means easier, so difficulty should be lower.
    
    # Using negative logit of proportion correct as difficulty measure
    difficulty_b = -np.log(proportion_correct / (1 - proportion_correct))

    # Map the calculated difficulty back to the original DataFrame
    # Create a mapping dictionary
    difficulty_map = difficulty_b.to_dict()
    
    # Return a Series aligned with the original DataFrame's index
    return df['Question ID'].map(difficulty_map)
