# This file makes the 'diagnostics' directory a Python package. 
from gmat_diagnosis_app.diagnostics.q_diagnostic import diagnose_q
from gmat_diagnosis_app.diagnostics.v_diagnostic import run_v_diagnosis_processed as diagnose_v
from gmat_diagnosis_app.diagnostics.di_diagnostic import run_di_diagnosis as diagnose_di

# 導入AI提示生成功能
from gmat_diagnosis_app.diagnostics.q_modules.ai_prompts import generate_q_ai_tool_recommendations
from gmat_diagnosis_app.diagnostics.v_modules.ai_prompts import generate_v_ai_tool_recommendations
from gmat_diagnosis_app.diagnostics.di_modules.ai_prompts import generate_di_ai_tool_recommendations

__all__ = [
    'diagnose_q', 
    'diagnose_v', 
    'diagnose_di',
    'generate_q_ai_tool_recommendations',
    'generate_v_ai_tool_recommendations',
    'generate_di_ai_tool_recommendations'
] 