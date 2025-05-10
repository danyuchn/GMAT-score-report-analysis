"""
驗證規則模組
包含用於數據驗證的規則和常量
"""

# Validation Rules (Case and space sensitive for allowed values)
ALLOWED_PERFORMANCE = ['Correct', 'Incorrect', 'Not Answered']

ALLOWED_CONTENT_DOMAIN = {
    'Q': ['Algebra', 'Arithmetic'],
    'V': ['N/A'],
    'DI': ['Math Related', 'Non-Math Related']
}

ALLOWED_QUESTION_TYPE = {
    'Q': ['REAL', 'PURE'],
    'V': ['Critical Reasoning', 'Reading Comprehension'],
    'DI': ['Data Sufficiency', 'Two-part analysis', 'Multi-source reasoning', 'Graph and Table', 'Graphs and Tables']
}

ALLOWED_FUNDAMENTAL_SKILLS = {
    'Q': ['Equal/Unequal/ALG', 'Rates/Ratio/Percent', 'Rates/Ratios/Percent', 'Value/Order/Factors', 'Counting/Sets/Series/Prob/Stats'],
    'V': ['Plan/Construct', 'Identify Stated Idea', 'Identify Inferred Idea', 'Analysis/Critique'],
    'DI': ['N/A']
}

# Derived from the above for convenience
ALL_CONTENT_DOMAINS = list(set(cd for subj_cds in ALLOWED_CONTENT_DOMAIN.values() for cd in subj_cds))
ALL_QUESTION_TYPES = list(set(qt for subj_qts in ALLOWED_QUESTION_TYPE.values() for qt in subj_qts))
ALL_FUNDAMENTAL_SKILLS = list(set(fs for subj_fss in ALLOWED_FUNDAMENTAL_SKILLS.values() for fs in subj_fss))

# Validation Rules Dictionary (Original Column Name : { rules })
VALIDATION_RULES = {
    'Response Time (Minutes)': {'type': 'positive_float', 'error': "必須是正數 (例如 1.5, 2)。"},
    'Performance': {'allowed': ALLOWED_PERFORMANCE, 'error': f"必須是 {ALLOWED_PERFORMANCE} 其中之一。"},
    'Content Domain': {'allowed': ALL_CONTENT_DOMAINS, 'subject_specific': ALLOWED_CONTENT_DOMAIN, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Question Type': {'allowed': ALL_QUESTION_TYPES, 'subject_specific': ALLOWED_QUESTION_TYPE, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Fundamental Skills': {'allowed': ALL_FUNDAMENTAL_SKILLS, 'subject_specific': ALLOWED_FUNDAMENTAL_SKILLS, 'error': "值無效或與科目不符 (大小寫/空格敏感)。"},
    'Question': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"},
    '\ufeffQuestion': {'type': 'positive_integer', 'error': "必須是正整數 (例如 1, 2, 3)。"}, # Handle BOM
} 