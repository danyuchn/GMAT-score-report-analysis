# -*- coding: utf-8 -*-
"""Utility functions for parsing data in GMAT Diagnosis App."""
import re
import warnings

def parse_adjusted_qns(qns_string: str) -> set[int]:
    """
    Parses a comma-separated string of question numbers into a set of integers.

    Args:
        qns_string: A string containing comma-separated question numbers.
                    Example: "1, 5, 10, 23"

    Returns:
        A set of unique integer question numbers.
        Returns an empty set if the input string is empty, None, or contains no valid numbers.
        Logs a warning for non-integer values.
    """
    if not qns_string or not qns_string.strip():
        return set()

    parsed_qns = set()
    potential_qns = re.findall(r'\d+', qns_string)

    for qn_str in potential_qns:
        try:
            parsed_qns.add(int(qn_str))
        except ValueError:
            warnings.warn(f"無效的題號 '{qn_str}' 在字串 '{qns_string}' 中被忽略。", UserWarning, stacklevel=2)
    return parsed_qns 